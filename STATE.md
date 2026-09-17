---
type: state
description: What exists right now, what is blocked and on whom, and where the proof is. Ground truth, not memory.
status: current
---

# STATE

**Last verified against `main` at `659bbee` plus the commit that carries this line, 2026-09-17**, for the Headline, the Blocked section, the Known unverified entries dated 2026-09-17, the Pipeline rows, and the Tooling rows for the mutation harness and the run-log reader. Documentation and Tooling rows are carried forward from earlier verifications and were not rechecked.

This file is where to start, not where to stop. It outranks memory: if you believe a row is wrong, read the file the pointer names before claiming a conflict. It does not outrank the code or the data. Where a row disagrees with them, the row is stale; report it and correct it. On 2026-09-17 four stale lines were found here that way.

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

**The vertical slice runs end to end on this machine and has run once on GitHub, where it failed at the last step.** Every component is built and tested. The orchestrator polled every configured board in four logged TEST_MODE runs from this machine, all with `--no-commit`. Scheduled run 35179218050 on 2026-09-17 polled all twelve boards on GitHub, fetched 1239 postings and failed at the data-branch commit, so nothing has been written to a data branch anywhere, locally or on the remote. The Airtable display layer does not exist.

Four spikes have run and their findings are folded into the records. The four decisions they raised are answered by ADR-0028 and ADR-0029.

---

## Documentation

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Architecture document, arc42, twelve sections | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture-2.0.md` |
| Rejected architecture bannered, not deleted | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture.md` |
| Decision records, MADR 4.0.0 plus Assumptions | DONE | [VERIFIED] counted 2026-09-17 | 2026-09-17 | 29 records in `docs/decisions/` |
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
| Virtual environment and dependency pin | DONE | [VERIFIED] `.venv` created, `requirements.txt` pinned at requests 2.34.2, 185 tests run under it | 2026-09-17 | `CLAUDE.md` commands |
| Working files consolidated under `data/` | DONE | [VERIFIED] repository root holds 7 files and nothing the pipeline writes; branch paths unchanged per ADR-0020 | 2026-09-17 | `2026-09-17-vertical-slice.md` |
| Mutation harness kept in the repository | DONE | [VERIFIED] a known mutation reported caught, a docstring edit reported survived with exit 1, an anchor occurring 23 times refused before anything ran, and every file byte-identical afterwards. The previous harness and its 79 mutations lived in a scratchpad and are lost | 2026-09-17 | `tools/mutate.py`, `2026-09-17-runner-safe-data-branch.md` |
| Run-log reader for ADR-0028's Confirmation | DONE | [VERIFIED] 23 tests, 22 mutations with the one survivor fixed, and read correctly from seven real log sources, including the old code's test log on a production branch, which it refused. Has not read a production data branch, because none exists. Proposes no ceiling | 2026-09-17 | `tools/run_log_report.py`, `2026-09-17-run-log-reader-and-speechify.md` |
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
| Himalayas adapter, conditional | PARTIAL | [VERIFIED] built, tested and run live: cursor pagination, stop anchored on stored data, aggregator rows routed to a local file never committed. **Whether it stays is unresolved: ADR-0019's condition passes on its three named components and fails on its "config entry and adapter file" wording.** Removing it is a one-line config deletion | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0019 |
| Normaliser, one row shape for every source | DONE | [VERIFIED] 29 tests; 10 mutations all caught, including a first-seen fallback relabelled as publication | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0007, ADR-0026 |
| Deduplicator | DONE | [VERIFIED] Speechify's 1086 postings collapse to 8 roles across 11 keys; 6 mutations all caught | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0001, ADR-0027 |
| Filter chain | PARTIAL | [VERIFIED] expiry and title built and tested, 34 tests, 10 mutations all caught. **Experience is disabled: no record names a threshold and no slice platform returns the field. The annotation-vendor list is provisional, sourced from the title pool's prose, not from a record** | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0005, ADR-0021 |
| Raw layer writer, orphan data branch | DONE | [VERIFIED] append-delta, atomic write, and a plumbing commit that never touches the working tree; 11 mutations all caught | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0002, ADR-0003, ADR-0020 |
| Filtered layer writer | DONE | [VERIFIED] same append-delta writer, separate file, ADR-0013 | 2026-09-17 | `2026-09-17-vertical-slice.md` |
| Airtable base and schema | PENDING | — | — | Deferred until real output exists |
| Airtable writer | PENDING | — | — | ADR-0004 |
| Scheduled workflow | DONE | [VERIFIED] orchestrator run twice against all 11 live boards in TEST_MODE: 917 postings, 19 kept, second run wrote nothing and both files byte-identical. Workflow file written, not yet exercised by GitHub | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0006 |
| Scheduled workflow, first run on GitHub. Supersedes the row above's "not yet exercised by GitHub" | PARTIAL | [VERIFIED] through the public Actions API: run 35179218050, schedule event, 2026-09-17T03:43Z, head `cd1f290`; the test step passed, Fetch failed with "the run could not start", push skipped; `git ls-remote --heads origin` shows only `main`. From the step 6 log the operator supplied, not checkable here: Python 3.11.16, all 12 boards `ok`, 1239 fetched, 37 kept, 36 of 500 requests, then `commit-tree` failed with "Author identity unknown" and the run exited 1 as an uncaught exception | 2026-09-17 | Run 35179218050 and its step 6 log |
| Data branch safe on a runner: fixed commit identity, bytes at the git boundary, state restored from the branch before a committing run, test mode on its own `data-test` branch, and the workflow fetching and pushing the branch its mode chose | DONE | [VERIFIED] by tests, mutations, and simulated runs against a local bare repository with the network replaced. **Not pushed, so not yet run on GitHub** | 2026-09-17 | `2026-09-17-runner-safe-data-branch.md` |
| ADR-0020 applied to the filtered layer and the seen store, with a content guard on every file offered to the branch | DONE | [VERIFIED] the old code pushed 2 Himalayas records in each of `filtered.json` and `seen.json` in simulation; the new code pushes none, keeps them in `data/local/`, and refuses to commit a file holding a record whose source is not publishable | 2026-09-17 | `2026-09-17-runner-safe-data-branch.md` |
| A run that fails after fetching says so | DONE | [VERIFIED] exit 1 still, with the failing stage named and "the fetch completed" printed; the workflow no longer annotates every exit 1 as "could not start" | 2026-09-17 | `2026-09-17-runner-safe-data-branch.md` |
| Workflow actions on Node 24: `checkout@v5`, `setup-python@v6` | DONE | [VERIFIED] each tag's `action.yml` declares node24 and a test holds the majors. [BELIEVED] run 35179218050's Node 20 annotation is gone; only a GitHub run shows it | 2026-09-17 | `2026-09-17-run-log-reader-and-speechify.md` |
| Weekly outcome sweep | PENDING | — | — | ADR-0014 |
| Contract check | PENDING | — | — | ADR-0018 |

## Blocked, and on whom

**The record revisions from spikes 1 and 2 are done.** ADR-0001 and ADR-0003 carry the falsified volume assumptions, ADR-0006 records the propagation assumption as confirmed, ADR-0018 bars `updated_at` as a change signal, ADR-0019's employer clause is reversed by ADR-0026, ADR-0026's key list is corrected from 18 to 20, and ADR-0027 adds per-source title normalisation. The architecture document's coverage table was corrected on 2026-09-16 for spike 3.

**ADR-0007's publication-date assumption is not falsified: it holds for Manatal**, the one platform of sixteen exposing no date at all.

**The four decisions the spikes raised are answered.** ADR-0028 sets a per-run fetch budget and fetches a posting's detail once ever rather than once per run. ADR-0029 fixes adapter order after the slice at Ashby, Workable, SmartRecruiters, Breezy and Manatal, drops Dover, and declares the registry tiers obsolete. ADR-0026 gained `envelope` and `constructed` and now covers the canonical URL.

**Waiting on the operator, as of 2026-09-17.** Pushing: the scheduled run on GitHub still uses `cd1f290` and will fail at the commit, twice a day. A manual `test_mode` run is safe only on the new code, which can be pushed to a separate branch and run from there before `main` is pushed. Whether Himalayas stays in `config/boards.json` meanwhile, given the finding below. Whether `data/test/` may be moved aside. The title pool, the experience threshold's value, and the board list (Speechify, CodeRoad) are the operator's, not the chat's; the material for them is in `data/reports/title-pool-review-2026-09-17.md`, local only.

**New for the architecture chat, from `2026-09-17-runner-safe-data-branch.md`.** *Himalayas on a runner keeps nothing:* ADR-0020 assumes aggregator history lives on the operator's machine, but the schedule runs on a discarded runner, so every scheduled run is Himalayas' first contact and its kept rows are lost. *ADR-0020's promised hook guard was never added*, and a hook cannot see a `commit-tree` commit anyway. *Seen-store entries were treated as rows* under ADR-0020, the conservative reading. *Exit 1 now has two causes* within the three fixed codes.

**Five questions were open for the architecture chat before that.** The title pool was the second, and under the protocol it belongs to the operator; it is stated under Known unverified. The other four were raised by the slice build and are stated in full in `2026-09-17-vertical-slice.md`:

*Does Himalayas stay?* ADR-0019's condition passes on its three named components and fails on its "config entry and adapter file" wording.

*The stated-experience threshold and the annotation-vendor list.* Both are named in the architecture document as filter rules and defined nowhere. The experience rule also has no source field: no slice platform returns one.

*The location filter's deferral has no record.* ADR-0001's Confirmation names a filter the pipeline does not have, and `docs/architecture-2.0.md:195` still lists it in the chain.

*ADR-0011's enumeration reads as a schema and is eight fields out of date*, every one of them required by a later record.

**The blocklist is no longer needed.** ADR-0021 removed it. Previously blocked on the operator; now closed.

**The Airtable base is blocked on real output**, by the operator's decision, not by an omission.

**Rozee.pk is unblocked and undecided.** robots.txt permits the job paths, the terms carry no automated-access clause, and a sitemap index publishes job URLs daily with the title in the slug. No decision record exists yet.

## Known unverified

**The workflow's branch fetch and push behave on GitHub as they did in simulation.** [VERIFIED] only against a local bare repository reached by `file://`, with a depth-1 clone of `main` standing in for the checkout. [BELIEVED], from outside this repository: `actions/checkout` with `fetch-depth: 1` fetches only the triggering ref, `inputs.test_mode` resolves in a job-level `env`, and the runner's locale is UTF-8. The first run after the push settles all three. `2026-09-17-runner-safe-data-branch.md`.

**Boards publish to their APIs at the moment a posting goes live.** ADR-0006's cadence rests on it. **Recorded as confirmed 2026-09-11** in ADR-0006's Assumptions, and its Changes row explains why: a posting 0.26 hours old at fetch is positive evidence, and a second run "would tighten the bound and cannot change the verdict". The record outranks this file under ADR-0022. Until 2026-09-17 this entry read "[VERIFIED] partially" and asked for a second run; it predated the record's amendment and was stale. `2026-09-11-endpoint-feasibility-spike.md`, ADR-0006.

**Many ATS platforms expose no publication date.** ADR-0007 asserts it. **Now settled across 16 platforms and it holds, narrowly.** [VERIFIED] a publication date exists on Greenhouse, Lever, Himalayas, Ashby, Workable, SmartRecruiters, Breezy, Pinpoint and BambooHR, and on JazzHR, Freshteam, Zoho and iCIMS only inside per-posting HTML. [VERIFIED] **Manatal exposes no date field of any kind**, across 2 boards and 34 postings, and it holds 8 registry boards. Dover's per-employer board carries none either. Manatal rows can never satisfy Measure A and must use ADR-0007's first-seen fallback. ADR-0007 is unrevised. `2026-09-16-publication-date-across-untested-platforms.md`.

**Workday `startDate` means publication.** [VERIFIED] behaviourally: it equals the fetch date minus the relative age in `postedOn` on 7 of 7 postings spanning ages 1 to 13 days, and none is in the future. An employment start date would not track posting age. The field name still does not say what it holds, so provenance must be recorded. `2026-09-16-second-observation-checks.md`.

**iCIMS `datePosted` is generated, not real.** [VERIFIED] false. The earlier suspicion is **withdrawn**: an older posting reports `2025-05-15T04:00:00.000Z`, sixteen months before the three that shared `2026-09-10T04:00:00.000Z`. The field varies per posting. The shared `04:00:00.000Z` is midnight US Eastern, so the value is a date with no time. `2026-09-16-second-observation-checks.md`.

**Measure A's coverage on the slice is 100%.** [VERIFIED] every one of 916 Greenhouse and Lever rows and all 500 Himalayas rows carries a real publication date; nothing falls back to first-seen. 43 Lever rows carry the date with its meaning unconfirmed. `2026-09-17-vertical-slice.md`.

**ADR-0028's ceiling of 500 is forty times the observed need.** [VERIFIED] first four observations: 11 requests for the eleven ATS boards, 36 on first contact with Himalayas, 12 in steady state for the whole slice. That is one month short of the evidence the record's Confirmation asks for, and nothing yet reads the run logs to aggregate it. `2026-09-17-vertical-slice.md`.

**The title pool admits 2.1% of postings, and 40 of its 50 terms admitted nothing.** [VERIFIED] 19 rows from 916, seven of them Pakistan-reachable. One concrete gap found: "Forward Deployment Engineer" is dropped while "Senior Forward Deployed Engineer" is kept, because ADR-0021's plural rule cannot reach "Deployment" from `forward deployed`. Widening the pool is the operator's call. `2026-09-17-vertical-slice.md`.

**Lever `createdAt` means published.** Still open. [VERIFIED] not contradicted: across five days both Lever boards produced one new posting, whose `createdAt` postdates the baseline clock, so 0 of 1 newly visible postings predate it. One appearance cannot establish the field's meaning. If Lever enters the slice, twice-daily polling answers this from the pipeline's own data within days. `2026-09-16-second-observation-checks.md`.

**Speechify's shrinking board is closures, not a fault.** [VERIFIED] for 2026-09-11 to 2026-09-16, 1086 to 361: 723 of the 813 lost postings are four whole roles that closed, each posted once per location; the other 90 are location copies of open roles, nearly matched by 87 new copies. [RUN LOG] 191 on 2026-09-17, not explained, since that run's postings were discarded. The first pushed run answers it without an extra request. `2026-09-17-run-log-reader-and-speechify.md`.

**Scheduled runs keep running.** [VERIFIED] from GitHub's documentation: "In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days." Whether the pipeline's own data-branch pushes count as activity is not established. `2026-09-17-run-log-reader-and-speechify.md`.

**Postings per run are on the order of one thousand.** ADR-0001:27, inherited by ADR-0003:28. [VERIFIED] false: 11 of the 53 boards return 1646 postings. Median 27 per board, maximum 1086. The 53-board total is unmeasured. `2026-09-15-spike-followup-checks.md`.

**Lever `createdAt` means published.** Measure A on Lever rows depends on it. [VERIFIED] not established: hosted pages display no date. Page-source JSON-LD `datePosted` matches `createdAt`'s UTC date on 3 of 3, but both come from Lever, so the match is not independent. `2026-09-15-spike-followup-checks.md`.

**Greenhouse `updated_at` marks an edit to a posting.** [VERIFIED] unreliable as such: it is bulk-stamped. 16 of 21 Careem postings share one instant, and Speechify's run in four rotating batches of about 265. What writes it is unknown. `2026-09-15-spike-followup-checks.md`.

**Himalayas can be read newest-first and stopped early.** [VERIFIED] partially: the browse endpoint orders by `pubDate` and paginates by cursor without duplicates over 3 pages. The search endpoint does neither. Browse's newest posting trailed search's by 97.7 minutes. [BELIEVED] from that lag, not observed: a stopping rule keyed to a run's wall clock would skip postings that reach browse late. Termination is not established. `2026-09-15-spike-followup-checks.md`.
