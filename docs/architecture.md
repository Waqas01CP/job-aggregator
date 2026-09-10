---
type: explanation
description: SUPERSEDED. A rejected design, kept as the record of what was turned down and why. Never implement from this file.
status: superseded
---

> **SUPERSEDED 2026-09-10 by [architecture-2.0.md](architecture-2.0.md).**
>
> This document is kept as the record of a rejected design. It is not the architecture of this project and must not be implemented.
>
> It was written against a different premise: that sources must be discovered, that postings need relevance scoring, and that a Postgres canonical store with a monitoring stack was warranted. Each of those was subsequently rejected on evidence. Specifically, it specifies a weighted 0-to-100 scoring engine with a shortlist threshold, which ADR-0010 prohibits; a Postgres store plus an Airtable mirror, superseded by the three-layer design in ADR-0013; Telegram alerting and a Prometheus and Grafana monitoring stack, which exceed the notification scope floor; an optional web UI, which ADR-0010 prohibits; and a Phase 0 source-discovery exercise targeting LinkedIn, Indeed, Glassdoor and AngelList, which duplicates an already-completed and already-paid-for ATS registry and targets sources that registry retired.
>
> It also carries none of the four hard filters this project requires and treats publication date as optional, which would make the project's binding measure uncomputable.
>
> Two things in it survived into the current design and are credited there: GitHub Actions as the scheduler, and the prohibition on committing raw payloads.

---

# Architecture Blueprint — Job Aggregator & Triage Pipeline (Final, Implementation-Ready)

> Purpose: complete, production-grade architecture & blueprint that an experienced engineer — or an automated code generator like OpenAI Codex — can use to implement the system end-to-end.
> Scope: scheduled Python aggregator (GitHub Actions) → per-source adapters → normalize → dedupe/merge → deterministic scoring → Postgres canonical store → actionable mirror to Airtable (or small web UI) → manual apply workflow. Includes CI, tests, monitoring, security, incident & legal guidance.

---

## Table of Contents

1. Goals & constraints
2. System overview (data flow & components)
3. Tech stack & rationale (final)
4. Repo layout (exact)
5. Runtime configuration & environment variables
6. Adapters — contract & template (detailed)
7. Normalization & canonicalization rules
8. Dedupe & merge algorithm (definitive)
9. Scoring engine (definitive)
10. Persistence: data model (DDL + indexes)
11. Transactions, idempotency & concurrency rules
12. CI / GitHub Actions workflows (YAML)
13. Tests & fixtures (what to include)
14. Logging format, metrics & monitoring (names, thresholds)
15. Alerts & incident response playbook
16. Security & secrets handling (concrete)
17. Storage, retention & archival policy (concrete)
18. Extensibility & plugin model (domains, new adapters)
19. Operational runbook (daily/weekly tasks)
20. Troubleshooting guide (common errors & fixes)
21. Legal / takedown / ToS guidance (practical)
22. Deliverables to include in repo (files & examples)
23. Acceptance criteria checklist (copyable)
24. Implementation timeline & effort estimate
25. Change log & versioning guidance

---

# 1. Goals & constraints

**Primary goal:** produce a system that reliably aggregates AI/LLM-adjacent job postings (Karachi onsite, Pakistan remote, global remote), deduplicates and scores them, and surfaces a curated `Actionable` list for manual application.

**Non-functional constraints**

* Manual application only (no auto-send).
* Preserve high recall for niche agentic / LLM roles while controlling noise.
* Keep operations low-maintenance (GitHub Actions runner vs self-host).
* Everything must be auditable, testable, idempotent, and extensible for other domains (ML, .NET).
* Do not include raw scraped payloads in the public repo.

---

# 2. System overview (data flow & components)

```
[SOURCES]
  RSS / IMAP (saved-search emails) / Company career pages / Aggregators
      ↓
[ADAPTERS LAYER] (adapters/<source>.py)  -- per-source fetch + parse + validate
      ↓
[NORMALIZER] (normalize company/location/URL)
      ↓
[DEDUPER] (merge multi-source postings into logical job entity)
      ↓
[SCORER] (deterministic, explainable)
      ↓
[POSTGRES] (canonical jobs table + job_sources provenance)
      ↓
[MIRROR] (Airtable or triage UI)  <-- only actionable subset
      ↓
[MANUAL APPLY] (user opens, tailors resume & email, sends) → mark status
      ↓
[FEEDBACK STORE] (applied/interview/offer) → used to tune scoring
```

Key runtime: `aggregator.run_pipeline()` executed by GitHub Actions scheduled cron (default every 6 hours). Each run must be idempotent and transactional.

---

# 3. Tech stack & rationale (final)

* **Language:** Python 3.11 — mature scraping/processing ecosystem.
* **Orchestration:** GitHub Actions (cron) — minimal ops, secure secrets, CI integration.
* **Database:** Postgres (managed: Supabase / Railway). Optionally PGVector later for semantic search.
* **Triage UI:** Airtable (MVP) or a small React/Streamlit app for richer workflows.
* **Monitoring:** Prometheus + Grafana or push metrics to a SaaS (Datadog) or lightweight alerts via Telegram webhook.
* **Version control:** GitHub (private repo during development).
* **Testing:** Pytest, unit tests for adapters, dedupe, scoring; fixtures stored in `tests/fixtures`.
* **Dependency management:** `requirements.txt` (pip) and optional `poetry`.
* **Secrets:** GitHub Secrets (DATABASE_URL, AIRTABLE_API_KEY, TELEGRAM_TOKEN, GMAIL_*).
* **Logging:** Structured JSON logs; retention in S3/Logs table for 90 days.

---

# 4. Repo layout (exact - copy to disk)

```
job-aggregator/
├─ adapters/
│  ├─ __init__.py
│  ├─ adapter_template.py
│  ├─ linkedin_email.py
│  ├─ angel.py
│  ├─ contour_careers.py
│  └─ ... (one per source)
├─ aggregator/
│  ├─ __init__.py
│  ├─ run_pipeline.py
│  ├─ ingest.py
│  ├─ normalize.py
│  ├─ dedupe.py
│  ├─ scoring.py
│  ├─ persistence.py
│  └─ utils.py
├─ domains/
│  ├─ agentic_ai.json
│  └─ ... (other domains)
├─ infra/
│  ├─ gh-actions-job-aggregator.yml
│  └─ prometheus.yml (optional)
├─ sql/
│  └─ schema.sql
├─ tests/
│  ├─ fixtures/
│  │  ├─ linkedin_sample.eml
│  │  ├─ contour_sample.html
│  │  └─ angel_sample.rss
│  ├─ test_adapters.py
│  ├─ test_dedupe.py
│  └─ test_scoring.py
├─ docs/
│  └─ architecture.md  # keep copy here
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

# 5. Runtime configuration & environment variables

**Environment variables (required)**

* `DATABASE_URL` — Postgres connection (postgres://user:pass@host:port/db)
* `AIRTABLE_API_KEY` — (optional) Airtable key for triage mirror
* `AIRTABLE_BASE_ID` — (optional) Airtable base id
* `TELEGRAM_TOKEN` — (optional) Telegram bot token for alerts
* `TELEGRAM_CHAT_ID` — chat id for alerts
* `SENTRY_DSN` — (optional) for error monitoring
* `RUNNER_ENV` — `dev|staging|prod`
* `LOG_LEVEL` — `INFO|DEBUG|WARN|ERROR`
* `MAX_FETCH_PER_MINUTE` or per-adapter config (throttling)
* `ADMIN_EMAIL` — contact for takedown requests

**Config files**

* `domains/*.json` — domain-specific keywords.
* `adapters/config.yaml` — per-adapter settings (rate limit, allowed hosts, known tracking params).

---

# 6. Adapters — contract & template

**Adapter responsibilities**

* Fetch raw items (RSS, HTTP, IMAP message) — `fetch()` returns `List[RawEntry]`.
* Parse raw item(s) to canonical `JobRecord` — `parse(raw)` returns `JobRecord` or `None`.
* Validate required fields.
* Obey per-host throttling/backoff.
* Emit run log (JSON) every run, even if no items parsed.

**Interface (Python)**

```python
# adapters/adapter_template.py
from typing import List, Dict, Optional
import datetime

RawEntry = Dict  # {source_id, payload (str/json), fetched_at (ISO), meta}
JobRecord = Dict
# Required JobRecord keys:
# title, company, location, apply_url, canonical_url, description,
# posted_date (ISO|None), source_name, source_id, raw_payload

def fetch() -> List[RawEntry]:
    """
    Fetch recent raw items from the source.
    Return list of RawEntry dicts.
    """
    raise NotImplementedError

def parse(raw: RawEntry) -> Optional[JobRecord]:
    """
    Parse a raw entry into JobRecord or return None.
    Must fill required fields (or empty string for description).
    """
    raise NotImplementedError
```

**Adapter run summary log (JSON)**

```json
{
  "adapter": "contour_careers",
  "run_id": "2026-09-01T04:00:00Z-uuid",
  "started_at": "2026-09-01T04:00:00Z",
  "ended_at": "2026-09-01T04:00:02Z",
  "items_fetched": 12,
  "items_parsed": 11,
  "items_new": 2,
  "items_updated": 1,
  "error_count": 0,
  "errors": []
}
```

**Adapter must:**

* Write above log to `logs/adapter_runs` table or S3.
* Always write the log even if `items_new == 0`.
* Rate limit itself (configurable per adapter).

---

# 7. Normalization & canonicalization rules

**URL canonicalization**

1. Prefer `<link rel="canonical">` from the HTML if available.
2. Else parse URL and:

   * remove query parameters in a configured blacklist (`utm_*`, `fbclid`, `gclid`, etc.)
   * remove fragment (`#...`)
   * remove trailing slashes (normalize `/job` and `/job/`)
3. Store original URL in `job_sources.raw_payload`.

**Company canonicalization**

* `company_registry` maps `canonical_company` to `aliases[]`.
* Use fuzzy matcher (RapidFuzz `token_sort_ratio` and token_set) to suggest alias matches.
* If fuzzy match > 92% with a verified canonical company, use that canonical value.
* Otherwise set `company_canonical = company_raw` and add to `proposed_aliases` for manual curation.

**Location normalization**

* Normalize to controlled set: `Karachi`, `Lahore`, `Pakistan`, `Remote`, `Pakistan Remote`, `Anywhere`.
* Heuristics:

  * If `Remote` or `Work from home` in title/location → `is_remote = True`.
  * If location contains `Karachi` or `Karachi, Pakistan` → `location_tag = Karachi`.
* Store original location string in provenance.

---

# 8. Dedupe & merge algorithm (definitive)

**High-level flow**

1. Compute candidate keys:

   * `canonical_url` if present.
   * `title_norm = normalize_text(title)` (lowercase, remove punctuation).
   * `company_norm = normalize_text(company)`.
2. Stage 1 — exact URL match:

   * If `canonical_url` matches an existing job → merge.
3. Stage 2 — fuzzy title+company:

   * Compute `token_set_ratio(f"{title_norm} {company_norm}", existing.title_company_concat)`.
   * If >= **85** → merge.
4. Stage 3 — semantic / TF-IDF fallback:

   * If both descriptions present: TF-IDF vectorize (vectorizer fit on corpus or use cached) and compute cosine similarity. If >= **0.90** → merge.
5. If none matched → create new `job_id` = `sha1(title_norm + '|' + company_norm + '|' + canonical_url_or_empty)`.

**Merging policy**

* Append entry into `job_sources`.
* Choose canonical fields deterministically:

  * `company_canonical`: prefer existing canonical (if any) else use `company_registry` mapping; if multiple, prefer one with `manual_verified = True`.
  * `title`: prefer the longest non-empty title string.
  * `description`: prefer the longest non-empty description.
  * `posted_date`: earliest posted_date if multiple; store all in `job_sources`.
* Recompute `score` after merging and update `jobs` row.

**Edge cases**

* Multiple companies with similar names: lower fuzzy threshold to avoid over-merging; rely on manual review.
* Partials: if only title + link available, create a job row marked `description_missing = True`. These appear in Actionable but flagged.

---

# 9. Scoring engine (definitive & explainable)

**Inputs**

* Job text (title + description)
* Domain config: `main_keywords[]` (broad), `specific_keywords[]` (high-signal)
* Company tier (0,1,2)
* Posted_date (for recency)

**Algorithm**

1. `main_matches = count_kws(job_text, main_keywords)`
   `main_score = min(1.0, main_matches / main_norm)` where `main_norm` defaults to 3 (tuneable).
2. `specific_matches = min(3, count_kws(job_text, specific_keywords))`
   `specific_boost = specific_matches * 10` (0,10,20,30).
3. `company_tier_boost = {0:0,1:10,2:5}.get(tier, 0)`
4. `recency_penalty = max(0, days_since_posted - 30) * 1`
5. `ease_of_apply_bonus = +5` if `apply_url` contains `easy-apply` or `LinkedIn apply` heuristics.

**Final score**

```
score = clamp(round(100 * (0.7 * main_score) + specific_boost + company_tier_boost - recency_penalty + ease_of_apply_bonus), 0, 100)
```

**Explainability**

* Store `matched_main_keywords`, `matched_specific_keywords`, `score_breakdown` as JSON:

```json
{
  "main_score": 0.67,
  "specific_boost": 10,
  "company_tier_boost": 10,
  "recency_penalty": 0,
  "final_score": 77,
  "matched_main": ["ai","llm"],
  "matched_specific": ["agentic"]
}
```

**Tuning**

* Provide a small CLI `aggregator/tune_scoring.py` to evaluate scoring on seed datasets and suggest adjustments.

---

# 10. Persistence: data model (DDL + recommended indexes)

**sql/schema.sql**

```sql
-- jobs table (canonical)
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  title TEXT,
  company_raw TEXT,
  company_canonical TEXT,
  company_tier INT DEFAULT 0,
  location_tag TEXT,
  is_remote BOOLEAN DEFAULT FALSE,
  description TEXT,
  description_missing BOOLEAN DEFAULT FALSE,
  apply_url TEXT,
  canonical_url TEXT,
  score INT DEFAULT 0,
  matched_main_keywords TEXT[],
  matched_specific_keywords TEXT[],
  score_breakdown JSONB,
  status TEXT DEFAULT 'new',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- provenance / sources
CREATE TABLE IF NOT EXISTS job_sources (
  id SERIAL PRIMARY KEY,
  job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
  source_name TEXT,
  source_id TEXT,
  source_url TEXT,
  fetched_at TIMESTAMPTZ,
  raw_payload JSONB,
  UNIQUE(job_id, source_name, source_id)
);

-- company registry
CREATE TABLE IF NOT EXISTS company_registry (
  canonical_company TEXT PRIMARY KEY,
  aliases TEXT[],
  tier INT DEFAULT 0,
  manual_verified BOOLEAN DEFAULT FALSE,
  proposed_aliases JSONB
);

-- adapter run logs
CREATE TABLE IF NOT EXISTS adapter_run_logs (
  id SERIAL PRIMARY KEY,
  adapter TEXT,
  run_id TEXT,
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  items_fetched INT,
  items_parsed INT,
  items_new INT,
  items_updated INT,
  error_count INT,
  errors JSONB
);

-- indexes
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_canonical_url ON jobs(canonical_url);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_canonical);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
-- full text index on description
CREATE INDEX IF NOT EXISTS idx_jobs_description_tsv ON jobs USING GIN (to_tsvector('english', coalesce(description,'')));
```

**Notes**

* Use `UNIQUE(job_id, source_name, source_id)` in `job_sources` to avoid duplicate provenance rows on repeat runs.
* Consider `pg_trgm` extension for fuzzy string indexing on `title`/`company`.

---

# 11. Transactions, idempotency & concurrency rules

* **Per job upsert pattern**

  1. Compute candidate job_id (or merge id after matching).
  2. Start DB transaction.
  3. `SELECT FOR UPDATE` the existing `jobs` row by `job_id` or `canonical_url`.
  4. Merge and update fields; `INSERT` if not exist (UPSERT).
  5. Insert a `job_sources` row with `ON CONFLICT DO NOTHING`.
  6. Commit.

* **Idempotency**

  * Use stable keys (hash of normalized fields) to avoid duplicate creations on repeated runs.
  * `adapter_run_logs` written at end of adapter invocation; if the run crashes, reconcile or replay based on `run_id`.

* **Concurrency**

  * Single pipeline runner per repository recommended for MVP (GitHub Actions cron ensures sequential runs), or serialize adapters that target same hosts to avoid race conditions.

---

# 12. CI / GitHub Actions workflows

**infra/gh-actions-job-aggregator.yml**

```yaml
name: Job Aggregator CI & Cron

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # every 6 hours

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
  run_pipeline:
    if: github.event_name == 'schedule' || github.event_name == 'push'
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run pipeline
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          AIRTABLE_API_KEY: ${{ secrets.AIRTABLE_API_KEY }}
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          RUNNER_ENV: prod
        run: |
          python -m aggregator.run_pipeline --env prod
```

**Notes**

* CI runs tests on push/PR. Scheduler (cron) runs pipeline only if tests passed.
* Use `secrets` set in repository settings.

---

# 13. Tests & fixtures

**Test types and files**

* `tests/fixtures/` — save canonical example pages/emails (sanitized).

  * `linkedin_sample.eml` (saved-search email)
  * `contour_sample.html` (company job page)
  * `angel_sample.rss`
* Unit tests:

  * `test_adapters.py` — for each adapter ensure `parse()` yields `title`, `company`, `apply_url`.
  * `test_dedupe.py` — fixtures representing duplicates; assert merge.
  * `test_scoring.py` — seed jobs and assert scores in expected ranges.
* Integration test:

  * `test_pipeline_dryrun.py` — run pipeline against fixtures, assert transactions, check `adapter_run_logs` created, ensure no unhandled exceptions.

**CI rules**

* PR cannot be merged without passing tests.
* Any adapter change must include updated fixtures if source changed.

---

# 14. Logging format, metrics & monitoring

**Logging (structured JSON)** — send to stdout and optionally push to file/S3.

```json
{
  "timestamp": "2026-09-01T04:00:00Z",
  "component": "adapters.contour_careers",
  "level": "INFO",
  "message": "adapter_run_completed",
  "run_id": "2026-09-01T04:00:00Z-uuid",
  "items_fetched": 12,
  "items_parsed": 11,
  "items_new": 2
}
```

**Metrics (names & description)**

* `adapter_fetch_count{name=adapter}` — count fetched items.
* `adapter_parse_errors{name=adapter}` — parse errors.
* `pipeline_items_new` — new jobs per run.
* `pipeline_actionable_count` — current actionable rows.
* `jobs_avg_score` — average score of new jobs.
* `dedupe_rate` — fraction of incoming items merged.

**Monitoring thresholds (suggested)**

* Adapter failure alert: `adapter_parse_errors > 0` for 2 consecutive runs or `adapter_fetch_count` drops > 50% vs baseline.
* Actionable drop alert: `pipeline_actionable_count < baseline_threshold` (baseline computed from historical mean minus X%).
* GH Actions failure — immediate alert.

**Alert channels**

* Telegram bot message to `TELEGRAM_CHAT_ID`.
* Email to `ADMIN_EMAIL`.
* Open GitHub issue automatically for serious failures.

---

# 15. Alerts & incident response playbook

**1. Adapter parse failures**

* Alert triggered → check `adapter_run_logs` for error stack → run adapter locally against `tests/fixtures` → if parse logic broken, patch adapter & run tests → open PR. If external site changed, update adapter parse rules and update fixtures.

**2. Massive drop in actionable items**

* Check `adapter_fetch_count` across sources → check network / GitHub Actions logs → if external site down, mark source as degraded in `adapters/config.yaml` and notify.

**3. Duplicate flood**

* If `dedupe_rate` spikes > 80% → inspect fuzzy thresholds, adjust token_set_ratio or TF-IDF threshold and re-run dedupe on last N items.

**4. Legal takedown**

* See section 21 below (Legal & Takedown plan).

---

# 16. Security & secrets handling (concrete)

**Do**

* Keep repo private during development.
* Store secrets in GitHub Secrets. Use least-privilege tokens.
* Do not commit `tests/fixtures` that contain third-party copyrighted content beyond minimal synthetic examples. Avoid raw scrapes in repo.
* Use GCM on Windows for PAT caching if using HTTPS.

**Don’t**

* Don’t print secrets in logs or `print()` statements.
* Don’t push raw payloads to repo.

**Key rotation**

* Rotate keys every 90 days.
* Revoke old tokens and re-run pipeline with new secrets.

**Audit**

* Keep `access.log` for credential usage; review monthly.

---

# 17. Storage, retention & archival policy

* Raw payloads (HTML/EML) stored in S3 or database JSONB for **90 days** then archived compressed to S3 Glacier (or deleted if not required).
* Canonical `jobs` kept for **365 days** (business logic). After 365 days, summarize into analytics table and delete archival raw.
* Logs kept for **90 days** in Postgres / log store; older logs archived to S3.

---

# 18. Extensibility & plugin model (how to add domains / adapters)

**Add a domain**

1. Add `domains/<name>.json` with `main_keywords`, `specific_keywords`, `resume_version`, `actionable_threshold`.
2. Add `resume_<name>.pdf` into `docs/resumes/`.
3. Optionally add domain-specific detection rules in `scoring.py` plugin registry.

**Add an adapter**

1. Create `adapters/<source>.py` implementing `fetch()` and `parse()`.
2. Add test fixture to `tests/fixtures/`.
3. Add adapter config to `adapters/config.yaml` (rate limit).
4. Add to `aggregator/ingest.py` adapter list.
5. Run `pytest` and ensure CI passes.

**Plugin points**

* `scoring` function can accept plugin strategy: deterministic vs semantic vs supervised (future).
* `dedupe` can be extended to use PGVector embeddings.

---

# 19. Operational runbook (daily/weekly tasks)

**Daily**

* Check pipeline run logs (or get Telegram summary).
* Open Airtable Actionable view and process top N jobs.

**Weekly**

* Inspect adapter health dashboard.
* Review `proposed_aliases` in `company_registry` and verify new canonical mappings.
* Recompute baseline metrics.

**Monthly**

* Rotate keys; test backup restore; run DB vacuum; audit logs.

---

# 20. Troubleshooting guide (common errors & fixes)

* `git push -u origin main` fails (permission denied): ensure SSH key added to GitHub or use HTTPS + PAT. (See earlier interactive steps.)
* `adapter_run_logs` show `items_parsed == 0` but `items_fetched > 0`: parse broken — check HTML change, update parse selectors.
* `pipeline_actionable_count` sudden drop: check adapter fetch rates; external source may have changed or returned different schema.
* Duplicate entries persist: adjust fuzzy threshold and re-run dedupe job on recent window.

---

# 21. Legal / takedown / ToS guidance (practical)

**Keep code public-safe**

* Do not store third-party raw content in public repo.
* Prefer APIs or email/RSS where possible.

**Takedown response**

* Add `TAKEDOWN.md` with contact info and quick removal policy.
* On complaint: remove offending data, make repo private if necessary, respond to complainant promptly.

**Automated pre-commit**

* Add `pre-commit` hook (or GitHub Action) that fails commits containing large files (e.g., over 1MB) or file extensions `.html`, `.eml`, `.jsonl` to stop accidental data commits.

---

# 22. Deliverables to include in repo (exact files & templates)

* `docs/architecture.md` (this file)
* `sql/schema.sql` (create tables & indexes)
* `infra/gh-actions-job-aggregator.yml` (CI & cron)
* `adapters/adapter_template.py` (complete skeleton)
* `aggregator/run_pipeline.py` (orchestrator skeleton)
* `aggregator/ingest.py`, `aggregator/normalize.py`, `aggregator/dedupe.py`, `aggregator/scoring.py`, `aggregator/persistence.py`
* `tests/fixtures/*` (sanitized)
* `tests/test_adapters.py`, `tests/test_dedupe.py`, `tests/test_scoring.py`
* `README.md` with run instructions
* `TAKEDOWN.md`
* `.gitignore` and `requirements.txt`
* `docs/resumes/resume_agentic_ai.pdf` (resume variants mapping)

---

# 23. Acceptance criteria checklist (copy/paste)

* [ ] Repo contains `docs/architecture.md` (this file).
* [ ] GH Actions configured and tests pass on PR.
* [ ] One adapter implemented + unit tests and fixtures.
* [ ] Pipeline runs in dry-run locally and writes `adapter_run_logs`.
* [ ] New items are inserted into Postgres `jobs` and `job_sources`.
* [ ] Dedupe recall >= 95% on prepared test set.
* [ ] Precision@50 >= 70% on seeded relevant jobs.
* [ ] Airtable actionable mirror accessible and shows `Onsite` & `Remote` views.
* [ ] Alerts configured (adapter failure, actionable drop).
* [ ] Secrets are in GitHub Secrets; no secrets in repo.

---

# 24. Implementation timeline & effort estimate

**Single experienced engineer**

* MVP core (1 adapter + pipeline + DB + triage mirror): **~6–7 working days**.
* Additional adapters (per 2–3 adapters): **+1 day** per 2 adapters (varies by complexity).
* Monitoring/alerts/production hardening: **+1–2 days**.

**Parallel team**: can be faster if adapter owners work in parallel.

---

# 25. Change log & versioning guidance

* Maintain `CHANGELOG.md` with semantic versioning (v0.1.0 MVP).
* Tag releases in Git with `v0.1.0`, `v0.2.0` for major feature sets.
* Use branch naming `feature/<adapter-name>` and PR reviews.

---

## Appendix — Useful code snippets (copy & paste)

**Simple scoring function (aggregator/scoring.py)**

```python
# aggregator/scoring.py (simplified)
from typing import Dict, List
from datetime import datetime

def count_matches(text: str, keywords: List[str]) -> int:
    t = text.lower()
    return sum(1 for kw in keywords if kw.lower() in t)

def compute_score(job: Dict, domain_cfg: Dict, company_tier: int = 0) -> Dict:
    text = " ".join(filter(None, [job.get('title',''), job.get('description','')]))
    main_matches = count_matches(text, domain_cfg['main_keywords'])
    main_norm = domain_cfg.get('main_norm', 3)
    main_score = min(1.0, main_matches / main_norm)
    specific_matches = min(3, count_matches(text, domain_cfg['specific_keywords']))
    specific_boost = specific_matches * 10
    company_tier_boost = 10 if company_tier == 1 else 5 if company_tier == 2 else 0
    # recency
    posted = job.get('posted_date')
    recency_penalty = 0
    if posted:
        days = (datetime.utcnow() - posted).days
        recency_penalty = max(0, days - 30) * 1
    ease_of_apply = 5 if 'easy apply' in (job.get('description','') + job.get('title','')).lower() else 0
    raw_score = round(100 * (0.7 * main_score) + specific_boost + company_tier_boost - recency_penalty + ease_of_apply)
    final_score = max(0, min(100, raw_score))
    breakdown = {
        "main_score": main_score,
        "specific_boost": specific_boost,
        "company_tier_boost": company_tier_boost,
        "recency_penalty": recency_penalty,
        "ease_of_apply": ease_of_apply,
        "final_score": final_score
    }
    return {"score": final_score, "breakdown": breakdown}
```

**Adapter template (adapters/adapter_template.py)**

```python
# adapters/adapter_template.py
import requests, uuid, datetime, logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def fetch() -> List[Dict]:
    """Example: return list of RawEntry dicts"""
    return []

def parse(raw: Dict) -> Optional[Dict]:
    """Return JobRecord or None"""
    # fill required fields
    job = {
      "title": "",
      "company": "",
      "location": "",
      "apply_url": "",
      "canonical_url": "",
      "description": "",
      "posted_date": None,
      "source_name": "adapter_template",
      "source_id": raw.get('source_id'),
      "raw_payload": raw.get('payload')
    }
    return job

def run_adapter():
    run_id = f"{datetime.datetime.utcnow().isoformat()}-{uuid.uuid4()}"
    started = datetime.datetime.utcnow()
    items = fetch()
    parsed = 0
    new_items = 0
    updated_items = 0
    errors = []
    for r in items:
        try:
            job = parse(r)
            if job:
                parsed += 1
                # persistence handled by pipeline
        except Exception as e:
            errors.append(str(e))
    ended = datetime.datetime.utcnow()
    log = {
        "adapter": "adapter_template",
        "run_id": run_id,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "items_fetched": len(items),
        "items_parsed": parsed,
        "items_new": new_items,
        "items_updated": updated_items,
        "error_count": len(errors),
        "errors": errors
    }
    logger.info(log)
    return log
```

---

## Final note

This `architecture.md` is intended as the single source of truth for implementation. It is exhaustive and designed for direct consumption by an engineer or an automated code generation agent (Codex) to build the system. If you want, I can now generate the concrete starter artifacts (component wiring README, `sql/schema.sql`, `infra/gh-actions-job-aggregator.yml` file, `adapter_template.py`, and the `aggregator/run_pipeline.py` skeleton) ready to paste into your repo. Say **“generate artifacts”** and I will produce those files in sequence.
