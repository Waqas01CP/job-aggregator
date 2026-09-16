---
type: state
description: What exists right now, what is blocked and on whom, and where the proof is. Ground truth, not memory.
status: current
---

# STATE

**Last verified against `main` at `9d8f9c1`, 2026-09-17**, for the Pipeline rows the slice build touched. Documentation and Tooling rows are carried forward from earlier verifications and were not rechecked.

This file is ground truth. If a row says DONE, it is done. If you believe otherwise, read the file the pointer names before claiming a conflict. Memory is not evidence.

Organised by task, not by session, because logs are chronological and one task spans many of them.

## How to read a row

`STATUS` is DONE, PARTIAL or PENDING. A row reads DONE only when the thing is built, never when it has merely been examined.

Every row carries `[VERIFIED]` or `[BELIEVED]`. Verified means exercised and observed. Believed means reasoned from the code but not run. **Unmarked means believed.** The default points at the weak set on purpose.

`Proof` is a commit, a decision record, or a log filename. Never a file path; paths move.

## How to maintain it

Update the affected rows **in the same commit as the work**, never in a separate pass. A commit that completes a task without updating its row is incomplete.

Never delete a DONE row. Supersede it with a new row if the work is redone.

Update the verified-against line whenever you touch this file.

## Headline

**The vertical slice is under construction.** Board configuration, the shared HTTP module, both adapters, the normaliser, the deduplicator, the filter chain and both writers are built and tested. The orchestrator and the schedule are not. Nothing has run against a live board from pipeline code yet.

Four spikes have run and their findings are folded into the records. The four decisions they raised are answered by ADR-0028 and ADR-0029.

---

## Documentation

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Architecture document, arc42, twelve sections | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture-2.0.md` |
| Rejected architecture bannered, not deleted | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture.md` |
| Decision records, MADR 4.0.0 plus Assumptions | DONE | [VERIFIED] | 2026-09-11 | 24 records in `docs/decisions/` |
| Research records with source trails | DONE | [VERIFIED] | 2026-09-11 | 4 passes in `docs/research/` |
| Title pool, 50 terms with matching rules | DONE | [VERIFIED] | 2026-09-11 | `docs/reference/title-pool.md`, ADR-0021 |
| README, licence and scope statement | DONE | [VERIFIED] | 2026-09-11 | `README.md`, `LICENSE` |
| Instruction file with reading and authority order | DONE | [VERIFIED] | 2026-09-11 | `CLAUDE.md`, ADR-0022, ADR-0023, ADR-0025 |
| Auto Memory ranked and excluded from design | DONE | [VERIFIED] | 2026-09-11 | ADR-0025 |
| This file | DONE | [VERIFIED] | 2026-09-11 | ADR-0023 |
| Log index and directory | DONE | [VERIFIED] | 2026-09-11 | `logs/README.md`, ADR-0023, ADR-0024 |
| End-state document | PENDING | — | — | Confirmed open in ADR-0023. No prior art exists |

## Tooling

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Map generated from frontmatter | DONE | [VERIFIED] ran, 38 files | 2026-09-11 | `tools/generate_map.py` |
| Pre-commit hook, five gates | DONE | [VERIFIED] all five proven to fire | 2026-09-11 | `.githooks/pre-commit` |
| Map gate Python resolution fixed | DONE | [VERIFIED] fired correctly after fix | 2026-09-11 | commit `ed0c4f4` |
| Line endings forced to LF | DONE | [BELIEVED] renormalise found nothing | 2026-09-11 | `.gitattributes` |
| State file staleness gate | DONE | [VERIFIED] blocked a commit staging `tools/` without `STATE.md` | 2026-09-11 | `.githooks/pre-commit` gate 4, ADR-0023 |

## Pipeline

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Endpoint feasibility spike, Greenhouse, Lever, Himalayas | DONE | [VERIFIED] ran; 11 of 11 board files re-checked against printed byte counts on 2026-09-15 | 2026-09-11 | `2026-09-11-endpoint-feasibility-spike.md`, written retroactively |
| Spike follow-up: board volume, Speechify age floor, Lever `createdAt`, Himalayas pagination | PARTIAL | [VERIFIED] checks 1 to 3 complete. Check 4 complete except whether browse pagination terminates, not establishable inside its 7-request cap | 2026-09-15 | `2026-09-15-spike-followup-checks.md` |
| Publication-date discovery across the 13 untested ATS platforms | DONE | [VERIFIED] 53 of 60 permitted requests, one board per platform, two boards for Manatal and Workable | 2026-09-16 | `2026-09-16-publication-date-across-untested-platforms.md` |
| Second-observation checks on Lever `createdAt`, Workday `startDate`, iCIMS `datePosted` | DONE | [VERIFIED] 7 requests against a self-imposed cap of 12 | 2026-09-16 | `2026-09-16-second-observation-checks.md` |
| Board configuration, eleven boards from the registry | DONE | [VERIFIED] 16 tests; 4 mutations applied and all caught | 2026-09-16 | `2026-09-16-vertical-slice.md` |
| Shared HTTP module | DONE | [VERIFIED] 21 tests; 8 mutations applied and all caught, including budget, breaker and status classification | 2026-09-16 | `2026-09-16-vertical-slice.md`, ADR-0028 |
| Greenhouse adapter, nine boards | DONE | [VERIFIED] parses a sanitised cassette of 21 real postings and one of 1086; 11 adapter mutations all caught | 2026-09-16 | `2026-09-16-vertical-slice.md` |
| Lever adapter, two boards | DONE | [VERIFIED] employer derived from slug with provenance recorded, epoch-ms range checked | 2026-09-16 | `2026-09-16-vertical-slice.md`, ADR-0026 |
| Himalayas adapter, conditional | PENDING | — | — | ADR-0019 |
| Normaliser, one row shape for every source | DONE | [VERIFIED] 29 tests; 10 mutations all caught, including a first-seen fallback relabelled as publication | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0007, ADR-0026 |
| Deduplicator | DONE | [VERIFIED] Speechify's 1086 postings collapse to 8 roles across 11 keys; 6 mutations all caught | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0001, ADR-0027 |
| Filter chain | PARTIAL | [VERIFIED] expiry and title built and tested, 34 tests, 10 mutations all caught. **Experience is disabled: no record names a threshold and no slice platform returns the field. The annotation-vendor list is provisional, sourced from the title pool's prose, not from a record** | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0005, ADR-0021 |
| Raw layer writer, orphan data branch | DONE | [VERIFIED] append-delta, atomic write, and a plumbing commit that never touches the working tree; 11 mutations all caught | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0002, ADR-0003, ADR-0020 |
| Filtered layer writer | DONE | [VERIFIED] same append-delta writer, separate file, ADR-0013 | 2026-09-17 | `2026-09-17-vertical-slice.md` |
| Airtable base and schema | PENDING | — | — | Deferred until real output exists |
| Airtable writer | PENDING | — | — | ADR-0004 |
| Scheduled workflow | PENDING | — | — | ADR-0006 |
| Weekly outcome sweep | PENDING | — | — | ADR-0014 |
| Contract check | PENDING | — | — | ADR-0018 |

## Blocked, and on whom

**The record revisions from spikes 1 and 2 are done.** ADR-0001 and ADR-0003 carry the falsified volume assumptions, ADR-0006 records the propagation assumption as confirmed, ADR-0018 bars `updated_at` as a change signal, ADR-0019's employer clause is reversed by ADR-0026, ADR-0026's key list is corrected from 18 to 20, and ADR-0027 adds per-source title normalisation. The architecture document's coverage table was corrected on 2026-09-16 for spike 3.

**ADR-0007's publication-date assumption is not falsified: it holds for Manatal**, the one platform of sixteen exposing no date at all.

**The four decisions the spikes raised are answered.** ADR-0028 sets a per-run fetch budget and fetches a posting's detail once ever rather than once per run. ADR-0029 fixes adapter order after the slice at Ashby, Workable, SmartRecruiters, Breezy and Manatal, drops Dover, and declares the registry tiers obsolete. ADR-0026 gained `envelope` and `constructed` and now covers the canonical URL.

**Two filter rules have no definition anywhere and are not built.** The architecture document names a stated-experience rule and an annotation-vendor rule in the filter chain; no record defines a threshold for the first or a list for the second. Neither Greenhouse nor Lever returns a structured experience field, so the first has nothing to read. See the open question in `2026-09-16-vertical-slice.md`.

**The blocklist is no longer needed.** ADR-0021 removed it. Previously blocked on the operator; now closed.

**The Airtable base is blocked on real output**, by the operator's decision, not by an omission.

**Rozee.pk is unblocked and undecided.** robots.txt permits the job paths, the terms carry no automated-access clause, and a sitemap index publishes job URLs daily with the title in the slug. No decision record exists yet.

## Known unverified

**Boards publish to their APIs at the moment a posting goes live.** ADR-0006's cadence rests on it. [VERIFIED] partially: one run found a Greenhouse posting 0.26 hours old. That cannot separate instant publication from a quiet window. The second run that settles it has not been done. `2026-09-11-endpoint-feasibility-spike.md`.

**Many ATS platforms expose no publication date.** ADR-0007 asserts it. **Now settled across 16 platforms and it holds, narrowly.** [VERIFIED] a publication date exists on Greenhouse, Lever, Himalayas, Ashby, Workable, SmartRecruiters, Breezy, Pinpoint and BambooHR, and on JazzHR, Freshteam, Zoho and iCIMS only inside per-posting HTML. [VERIFIED] **Manatal exposes no date field of any kind**, across 2 boards and 34 postings, and it holds 8 registry boards. Dover's per-employer board carries none either. Manatal rows can never satisfy Measure A and must use ADR-0007's first-seen fallback. ADR-0007 is unrevised. `2026-09-16-publication-date-across-untested-platforms.md`.

**Workday `startDate` means publication.** [VERIFIED] behaviourally: it equals the fetch date minus the relative age in `postedOn` on 7 of 7 postings spanning ages 1 to 13 days, and none is in the future. An employment start date would not track posting age. The field name still does not say what it holds, so provenance must be recorded. `2026-09-16-second-observation-checks.md`.

**iCIMS `datePosted` is generated, not real.** [VERIFIED] false. The earlier suspicion is **withdrawn**: an older posting reports `2025-05-15T04:00:00.000Z`, sixteen months before the three that shared `2026-09-10T04:00:00.000Z`. The field varies per posting. The shared `04:00:00.000Z` is midnight US Eastern, so the value is a date with no time. `2026-09-16-second-observation-checks.md`.

**Lever `createdAt` means published.** Still open. [VERIFIED] not contradicted: across five days both Lever boards produced one new posting, whose `createdAt` postdates the baseline clock, so 0 of 1 newly visible postings predate it. One appearance cannot establish the field's meaning. If Lever enters the slice, twice-daily polling answers this from the pipeline's own data within days. `2026-09-16-second-observation-checks.md`.

**Postings per run are on the order of one thousand.** ADR-0001:27, inherited by ADR-0003:28. [VERIFIED] false: 11 of the 53 boards return 1646 postings. Median 27 per board, maximum 1086. The 53-board total is unmeasured. `2026-09-15-spike-followup-checks.md`.

**Lever `createdAt` means published.** Measure A on Lever rows depends on it. [VERIFIED] not established: hosted pages display no date. Page-source JSON-LD `datePosted` matches `createdAt`'s UTC date on 3 of 3, but both come from Lever, so the match is not independent. `2026-09-15-spike-followup-checks.md`.

**Greenhouse `updated_at` marks an edit to a posting.** [VERIFIED] unreliable as such: it is bulk-stamped. 16 of 21 Careem postings share one instant, and Speechify's run in four rotating batches of about 265. What writes it is unknown. `2026-09-15-spike-followup-checks.md`.

**Himalayas can be read newest-first and stopped early.** [VERIFIED] partially: the browse endpoint orders by `pubDate` and paginates by cursor without duplicates over 3 pages. The search endpoint does neither. Browse's newest posting trailed search's by 97.7 minutes. [BELIEVED] from that lag, not observed: a stopping rule keyed to a run's wall clock would skip postings that reach browse late. Termination is not established. `2026-09-15-spike-followup-checks.md`.
