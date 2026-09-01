# Architecture Blueprint — Job Discovery & Triage Pipeline

**Final (audited + hardened) design** — GitHub Actions + Python runner, adapterized ingestion → Postgres canonical store → deterministic scoring → actionable mirror (Airtable/UI) → manual apply. This document updates the previous blueprint to **compensate for identified weaknesses**, applies software-engineering principles, defines contracts, tests, and acceptance criteria, and is ready to hand to an engineer for implementation.

---

## Table of contents

1. Goals & constraints (reminder)
2. High-level architecture (final) — diagram + explanation
3. Core components & contracts (details + interfaces)
4. Data model & canonicalization rules
5. Dedupe, canonicalization & merge algorithm (definitive)
6. Scoring engine (deterministic rules + explainability)
7. Adapter pattern, tests & CI rules (must-have)
8. Operational rules: idempotency, transactions, logging, monitoring, alerts
9. Security & secrets handling (concrete)
10. Storage, retention & archival policy
11. Performance, scaling & cost considerations
12. Extensibility: domain config & plugin model
13. Acceptance criteria & test matrix (executable)
14. MVP roadmap & responsibilities
15. Deliverables / artifacts provided

---

# 1 — Goals & constraints (reminder)

* **Primary goal:** Surface a curated set of high-quality AI/LLM-adjacent jobs (Karachi onsite, Pakistan remote, global remote) so the user can manually apply with tailored resumes.
* **Hard requirements:** manual apply, preserve high recall for niche AI/agentic roles, modular/extensible architecture to support other domains later, minimal ops overhead.
* **Tech choices confirmed:** GitHub Actions + Python 3.11 + Postgres primary store + Airtable (or small UI) for triage. LLMs out of core path (drafts on demand only). User will provide source list and tier1 company seeds.

---

# 2 — High-level architecture (final)

```
[Sources: RSS / IMAP email alerts / company pages / aggregators / user-provided feeds]
       ↓
[Adapters Layer (one adapter per source)  -- adapter tests & fixtures]
       ↓
[Normalizer & Canonicalizer (company_registry, location_map)]
       ↓
[Dedupe & Merge (multi-stage: canonical_url → fuzzy → semantic) ]
       ↓
[Scoring Engine (deterministic primary + specific boosts) -> explainability]
       ↓
[Postgres (canonical jobs + job_sources provenance + metrics)]
       ↓
[Mirror actionable subset -> Airtable or triage UI]
       ↓
[Manual apply flow (user inspects, tailor, send) -> mark status]
       ↓
[Analytics + Feedback loop -> scoring reweighting suggestion]
```

**Key runtime:** scheduled GitHub Actions cron (e.g., every 6 hours) triggers `aggregator.run_pipeline`. Each run is idempotent, transactional, and logged.

---

# 3 — Core components & precise contracts

### 3.1 Adapters (source modules)

* Location: `adapters/<source>.py`

* Required functions:

  ```python
  def fetch() -> List[RawEntry]:
      # returns list[ {source_id, payload, fetched_at, meta} ]
  def parse(raw: RawEntry) -> Optional[JobRecord]:
      # returns dict with required fields or None
  ```

* **JobRecord (required fields):**

  * `title` (str), `company` (str), `location` (str or None),
  * `apply_url` (str or None), `canonical_url` (str or None),
  * `description` (str or ""), `posted_date` (ISO or None),
  * `source_name`, `source_id`, `raw_payload` (JSON/HTML for audit).

* **Adapter non-functional contract:**

  * Must log a JSON run summary each invocation: `{adapter, run_id, started_at, ended_at, items_fetched, items_parsed, items_new, items_updated, error_count}`. **Always** write this log (even if 0 new).
  * Must not print secrets.
  * Must implement per-host rate limiting & exponential backoff on 429/5xx.

### 3.2 Orchestrator

* `aggregator/run_pipeline.py` orchestrates:

  * load domain config,
  * run each enabled adapter (parallel or sequential with per-host throttle),
  * parse, normalize, dedupe, score,
  * persist via transactional upsert,
  * send daily digest/notification,
  * emit metrics & logs.

### 3.3 Normalizer

* responsibilities:

  * canonicalize URLs (prefer `<link rel="canonical">`), remove tracking params (configurable list),
  * normalize company names via `company_registry`,
  * normalize location strings to controlled vocab (`Karachi`, `Remote`, `Pakistan Remote`, etc.),
  * detect `is_remote` boolean heuristics.

### 3.4 Dedupe & Merge

* deterministically groups multiple source rows into one logical `job_id`. See section 5 for the exact algorithm.

### 3.5 Scoring Engine

* deterministic function: returns numeric score 0..100 + `explainability` dict (`matched_main`, `matched_specific`, `score_breakdown`).

### 3.6 Persistence

* Use Postgres with schema in `sql/schema.sql`. All writes must be transactional and idempotent (UPSERT or SELECT FOR UPDATE pattern).

---

# 4 — Data model & canonicalization rules

### 4.1 Canonical Job Table (`jobs`)

* `job_id TEXT PK`
* `title TEXT`
* `company_raw TEXT`
* `company_canonical TEXT`
* `company_tier INT` (0..n)
* `location_tag TEXT`
* `is_remote BOOLEAN`
* `description TEXT`
* `description_missing BOOLEAN DEFAULT FALSE`
* `apply_url TEXT`
* `canonical_url TEXT`
* `score INT`
* `matched_main_keywords TEXT[]`
* `matched_specific_keywords TEXT[]`
* `score_breakdown JSONB`
* `status TEXT` (`new`/`shortlisted`/`applied`/...)
* `created_at`, `updated_at`

### 4.2 Job provenance (`job_sources`)

* `id SERIAL`
* `job_id FK`
* `source_name, source_id, source_url, fetched_at, raw_payload JSONB`

### 4.3 Company registry (`company_registry`)

* `canonical_company TEXT PK`, `aliases TEXT[]`, `tier INT`, `manual_verified BOOL`, `proposed_aliases JSONB`

---

# 5 — Dedupe & merge algorithm (definitive)

**Stage 0 — compute candidate_key**

* Compute `canonical_url` via canonical tag or normalized URL (strip known tracking params).
* Compute `title_norm = normalize_text(title)`, `company_norm = normalize_text(company)`.

**Stage 1 — exact canonical_url match**

* If canonical_url present and job exists with canonical_url → merge.

**Stage 2 — fuzzy title+company**

* Compute `token_set_ratio(title_norm + company_norm)` using RapidFuzz. If score ≥ **85**, merge.

**Stage 3 — semantic / TF-IDF fallback**

* If both descriptions exist, compute TF-IDF cosine similarity (or embeddings when PGVector added). If similarity ≥ **0.90**, merge.

**Merging policy**

* Append source to `job_sources`.
* Choose canonical fields deterministically:

  * `company_canonical`: prefer `company_registry` match > manual > fuzzy highest confidence.
  * `title`: prefer longest non-empty title or earliest source with full description.
  * `description`: choose most complete (longest) non-empty description.
* Preserve original values in `job_sources`.

**Why this order:** exact URL is authoritative; fuzzy protects against small textual variants; semantic catches near-synonym duplicates.

---

# 6 — Scoring engine (final rules, interpretable)

**Inputs:** `job_record` + `domain_config` (main_keywords[], specific_keywords[], company_tier).

**Steps:**

1. `main_matches = count main_keywords present in title+description` → `main_score = min(1.0, main_matches / 3)`. (Tuneable denominator). Weight = **0.70**.
2. `specific_matches = count specific_keywords present in full text` → `specific_boost = min(3, specific_matches) * 10` (i.e., 0,10,20,30).
3. `company_tier_boost = 10 if Tier1 else 5 if Tier2 else 0`.
4. `recency_penalty = max(0, days_since_posted - 30) * 1` (subtract 1 point/day beyond 30).
5. Optional `ease_of_apply_bonus = +5` if easy apply detected.

**Final:** `score = clamp(round(100 * (0.7 * main_score) + specific_boost + company_tier_boost - recency_penalty + ease_of_apply_bonus), 0, 100)`

**Explainability:** store `matched_main_keywords`, `matched_specific_keywords`, `score_breakdown`.

**Design rationale:** majority weight on broad keywords to preserve recall; agentic keywords are additive, not gatekeepers.

---

# 7 — Adapter testing & CI rules (enforceable)

* **Unit tests for adapters**: every adapter must include a `tests/fixtures/<adapter>_sample.*` and a test asserting parsed `JobRecord` fields exist and match expected values. CI blocks PR if adapter tests fail.
* **Integration dry-run**: `run_pipeline.py --dryrun` uses fixtures and asserts no unhandled exceptions, correct dedupe, and sample writes to a test DB.
* **Pre-merge checks**:

  * `pytest` passes,
  * static analysis (`mypy`, `flake8`, `bandit`),
  * pre-commit hooks.
* **Scheduled smoke tests**: daily GH Action that fetches a small set of canonical pages and runs adapters; if parse completeness drops >20% vs baseline → alert.

---

# 8 — Operational rules: idempotency, transactions, logging & monitoring

### Idempotency & transactions

* Each pipeline run computes candidate job grouping deterministically and performs upserts inside DB transactions:

  * Acquire `SELECT FOR UPDATE` on candidate key (job_id or generated merge ID), then insert/update + append provenance.
* Be defensive to avoid partial updates:

  * Use two-phase commit pattern within a single DB transaction per job if multiple tables updated.

### Logs (structured JSON)

* `logs/adapter_runs` entry per adapter run. Keep 90 days in Postgres or S3.
* `logs/pipeline_runs` for each pipeline invocation: `run_id, started_at, ended_at, total_fetched, total_new, total_updated, errors`.

### Monitoring & alerts

* Emit metrics: `adapter_fetch_count`, `adapter_parse_errors`, `items_new`, `items_updated`, `actionable_count`, `avg_score`, `dedupe_rate`.
* Alerting rules:

  * Adapter failure rate > 20% for 2 successive runs → Telegram/Email.
  * Actionable_count_today < baseline_threshold → alert.
  * GH Actions run fails → open GitHub issue + slack/telegram alert.

---

# 9 — Security & secrets handling

* **Secrets:** store in GitHub Secrets (DATABASE_URL, AIRTABLE_KEY, GMAIL_SERVICE_TOKEN, TELEGRAM_TOKEN). No secrets in logs. Use least-privilege tokens.
* **Repo:** private repo for code & CI. Protect main branch with PR reviews & passing CI requirement.
* **Access control:** Airtable keys limited to base access. Gmail drafts via minimal scope service account (OAuth limited to draft compose only).
* **Rotation:** rotate tokens every 90 days (or earlier on personnel change). Keep audit logs of token use.
* **Self-hosted runners:** if used later, run inside private VPC and restrict inbound.

---

# 10 — Storage, retention & archival policy

* **Raw payloads:** keep for **90 days** in Postgres JSONB or S3 as compressed JSONL (recommend S3).
* **Canonical jobs:** keep for **365 days**; archived older than 365 days to cold storage and summarized rows kept.
* **Logs:** last 90 days in Postgres/ELK; older logs in S3.
* **Backups:** daily DB backups with 30-day restore window; periodic test restores.

---

# 11 — Performance & scaling guidance

* MVP scale: 100–2,000 items/day — Postgres handles easily.
* Indexes to add:

  * `idx_jobs_score (score DESC)`, `idx_jobs_canonical_url`, GIN full-text on `description` (`to_tsvector(description)`), index on `company_canonical`.
* If ingestion > 10k/day: consider:

  * Batch writes, queueing parsing using Redis/RQ or Celery, move heavy similarity checks (TF-IDF) to async worker.
* If many semantic queries needed later: add PGVector.

---

# 12 — Extensibility: domain config & plugin model

* `domains/<domain>.json` defines `main_keywords`, `specific_keywords`, `resume_version`, `actionable_threshold`. Add domain config to `domains/` and register in pipeline config.
* Adding a new domain: add JSON + resume file + optional domain-specific adapter enhancements (rare).
* Plugin points:

  * scoring: pluggable weighting functions,
  * dedupe: pluggable similarity function (TF-IDF vs embedding),
  * adapter: standard interface.

---

# 13 — Acceptance criteria & test matrix (concrete)

**Functional**

* [ ] GH Actions cron triggers `aggregator.run_pipeline` every 6 hours and writes a run log.
* [ ] For each adapter, `test_adapters.py` exists and passes on CI.
* [ ] Postgres rows created with `job_sources` provenance aggregated.
* [ ] Actionable mirror shows `Onsite` and `Remote` views with `sites` aggregated in one logical row.

**Quality**

* [ ] Dedupe recall ≥ 95% on provided duplicates test set.
* [ ] Precision@50 on seeded positive test ≥ 70%.
* [ ] Adapter parse completeness (title + apply_url) ≥ 90% for sample 7-day ingest.

**Ops**

* [ ] Alerts configured: adapter failure, actionable_count drop, GH Action run failure.
* [ ] Secrets not printed in logs & stored in GitHub Secrets.

---

# 14 — MVP roadmap & responsibilities (concrete steps, estimated time)

**Day 0 (setup)** — Repo + GH Actions + sample Postgres (Supabase/Railway) — *0.5 day*
**Days 1–3 (adapters & tests)** — adapter template + 3 adapters + fixtures & CI — *2.5 days*
**Day 4 (persistence & dedupe)** — schema + transactional upsert + dedupe tests — *1 day*
**Day 5 (scoring & mirror)** — scoring module + Airtable mirror + digest — *0.5 day*
**Day 6 (monitoring & alerts)** — metrics & alerts + run tune — *0.5–1 day*
**Day 7 (tuning & acceptance)** — run live, tune thresholds, finalize documentation — *0.5–1 day*

**Total MVP:** ~6–7 engineering days (single experienced engineer). Add 0.5–1 day per additional adapter complexity.

**Team roles** (suggested):

* Lead engineer (design + critical code)
* Adapter owner(s) for each complex source (1 per 2–4 adapters)
* QA/Tester (fixtures + CI) — can be same engineer for MVP

---

# 15 — Deliverables / artifacts I will produce now

Per your instruction: I will produce the **updated architecture file** (implementation-ready) that incorporates all compensations and fixes above. Below is the architecture file content; you can copy/save it as `docs/architecture.md` in the repo. It already includes all contracts, algorithm specifics, test matrix and acceptance criteria.
