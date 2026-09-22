---
type: state
description: What exists right now, what is blocked and on whom, and where the proof is. Where to start, then checked against the code and data.
status: current
---

# STATE

**Revised by the architecture chat against origin, 2026-09-22 (UTC).** `main` at `da193b6` and `data` at `7bb4c76`, by `git ls-remote --heads`; the eleven production run logs on `data` read directly from a clone at that head; the decision directory listed; the Airtable schema read through the connector. **Not rechecked, carried from the seat's line below:** the test count, `MAP.md`'s currency, the pool's term count, and every row not named in this revision. *(Corrected 2026-09-22T20:56Z by the implementing seat: the two commits this line names have both moved. `main` is at `0e0419f` and `data` at `137364f`, and the working copy is clean, so the sentence about uncommitted edits is no longer true: they were committed in `807add2`, `a165d15`, `10b3273` and `0e0419f`. The run count has also moved from eleven to twelve.)* This line and the seat's line below are the only places this file names a commit.

**Last verified against `main` at `0e0419f`, 2026-09-22T20:56Z**, for the push state, the suite's test count, the board count, the pool's term count, `MAP.md`'s currency and the Actions run history. Checked by `git ls-remote --heads origin`, the public Actions API, `python -m unittest discover`, and loading the pool. Four lines that claimed work was unpushed were stale and are corrected below. Also verified this session: the Airtable schema, read back after building it; that a pool widening is not retroactive; the record count, 39 *(wrong when stamped: the corpus held 45 records at that time per the seat's own Addendum 10, and holds 48 on 2026-09-22, 47 numbered plus ADR-RULES, by directory listing)*; that ADR-0021's eight Confirmation cases all still produce their required verdict; and that pre-commit gate 6 blocks a force-added `data/` path. Dates in this file are UTC from 2026-09-17, per CLAUDE.md. Verified in the navigation and audit round: ADR-0031's Confirmation now runs as a tool and the shipped tree is clean; 325 tests; the field inventory is measured from 84 saved responses; run 35303384355 wrote 0 rows to the public filtered file; the map's topic gate, which fires on a record with no topic; the backfill, run against a copy of the branch, which appended 257 rows and closed the gap; the five Airtable tables, each schema read back after building; that both Airtable tables were empty before ten rows were seeded into `Jobs test`; and that the heredoc guard's first design was blind to the failure it was built for.

**Touched again 2026-09-22T22:10Z by the implementing seat, after the close, for `docs/how-to/the-seats.md`.** No pipeline code changed and no test was run: the change is documentation only. Verified for it: six gates in `.githooks/pre-commit`, `core.hooksPath` returning `.githooks`, 42 Python files and 8,642 lines, 49 files in `docs/decisions/`, the four reading-order files at 72,765 bytes, and `MAP.md` current at 87 files. **`main` is at `73fff5c` and `origin/main` at `0e0419f`, so two commits are now unpushed and the operator's decision to push is still open.** One claim this seat made to the operator was wrong and is corrected in the log: the seat protocol does exist in a repository file, `CHAT_STATE.md`, in six lines addressed to the architecture chat.

Verified earlier, against `main` at `085c434`, 2026-09-17, and not rechecked since: the Known unverified entries dated 2026-09-17, the README row, the title pool and seniority rows, the Himalayas and Banyan Canopy trials, and the Tooling rows added on 2026-09-17. Other Documentation and Tooling rows are carried forward from earlier verifications and were not rechecked.

This file is where to start, not where to stop. It outranks memory: if you believe a row is wrong, read the file the pointer names before claiming a conflict. It does not outrank the code or the data. Where a row disagrees with them, the row is stale; report it and correct it. On 2026-09-17 four stale lines were found here that way.

Organised by task, not by session, because logs are chronological and one task spans many of them.

## How to read a row

`STATUS` is DONE, PARTIAL or PENDING. A row reads DONE only when the thing is built, never when it has merely been examined.

Every row carries `[VERIFIED]` or `[BELIEVED]`. Verified means exercised and observed. Believed means reasoned from the code but not run. **Unmarked means believed.** The default points at the weak set on purpose.

`Proof` is a commit, a decision record, or a log filename. Never a file path; paths move.

## How to maintain it

Update the affected rows **in the same commit as the work**, never in a separate pass. A commit that completes a task without updating its row is incomplete.

**When a row becomes DONE, move it to `docs/reference/completed.md` in the same commit.** Never delete one. Supersede it with a new row there if the work is redone. This file holds what is not settled; that one holds what is.

Update the verified-against line whenever you touch this file.

## Headline

**The vertical slice runs on schedule on GitHub.** [VERIFIED] 2026-09-22T20:56Z from a clone at `data` head `137364f`: **twelve** production runs from 2026-09-17T14:52Z to 2026-09-22T17:33Z, every one spending 36 of 500 requests. `filtered.json` holds **345** rows, the seen store **923**, raw Greenhouse 876 and Lever 47. Test mode works on GitHub on `data-test`.

**ADR-0030's backfill is proven in production, and this is the single most useful thing a new seat can know about it.** [VERIFIED] from the run logs: the 2026-09-19T03:26Z run reports `backfilled: 257`, which is exactly the number measured by hand three days earlier, and **every one of the seven runs since reports 0**. It appends the gap once and nothing thereafter, which is the idempotence the design claimed and the reason it is safe inside every run.

**The display does not fill yet.** The Airtable base and its five tables exist and are verified; the writer that fills them does not, so ADR-0009's slice Confirmation cannot yet be met. The operator has asked for the writer to be held until the implementing seat is restarted with a new brief.

**Himalayas' kept rows are lost on every run.** [VERIFIED] each of the eleven runs fetched 500 and kept between 11 and 28, and every kept row was discarded with the runner. ADR-0047 gives them a private store; it is decided and unbuilt, and needs the operator's step 5.

**Committed 2026-09-22, and this paragraph is kept only to say so.** It listed the architecture chat's edits of 2026-09-19 to 2026-09-22 as uncommitted and awaiting the implementing seat. They are in `807add2`, `a165d15`, `10b3273` and `0e0419f`: ADR-0046, ADR-0047 and ADR-0048, the Changes-table move across sixteen records, the rewritten `CLAUDE.md` authority order, `docs/architecture-2.0.md`, both reference files, the how-to, and this file. [VERIFIED] `git status` clean and `origin/main` at `0e0419f`.

Four spikes have run and their findings are folded into the records. The four decisions they raised are answered by ADR-0028 and ADR-0029.

---

**The 62 completed rows live in `docs/reference/completed.md`**, read on demand rather than at the start of every session. A DONE row is finished history: it records that something was built and how it was proved, and under this file's own rule it is never deleted. Keeping them here meant every session read 18.7KB of settled work to reach the nine rows that are not settled: 60 of the 69 rows were DONE, and the file went from 42,036 bytes to 23,334. Nothing was rewritten in the move.

## Documentation

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| End-state document | PENDING | — | — | Confirmed open in ADR-0023. No prior art exists |

## Tooling

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|

## Pipeline

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Spike follow-up: board volume, Speechify age floor, Lever `createdAt`, Himalayas pagination | PARTIAL | [VERIFIED] checks 1 to 3 complete. Check 4 complete except whether browse pagination terminates, not establishable inside its 7-request cap | 2026-09-15 | `2026-09-15-spike-followup-checks.md` |
| Himalayas adapter | PARTIAL | [VERIFIED] built, tested and run live: cursor pagination, stop anchored on stored data, aggregator rows routed to a local file never committed. **It stays**, decided 2026-09-18; ADR-0039 settled that ADR-0019's three named components govern, not its narrower wording. **On trial to 2026-09-26.** [VERIFIED] every production run so far fetched 500 and kept 11 to 28, all discarded with the runner, so the trial has no stored rows to judge. **Decided, unbuilt:** a private store for every aggregator-sourced layer and the private Airtable base (ADR-0047), and one poll a day on the morning run (ADR-0048) | 2026-09-22 | `2026-09-17-vertical-slice.md`, ADR-0039, ADR-0047, ADR-0048 |
| Filter chain | PARTIAL | [VERIFIED] expiry and title built and tested, 34 tests, 10 mutations all caught. **Experience is disabled: no record names a threshold and no slice platform returns the field**, and the operator has deferred the rule until filtering reads descriptions. **The annotation-vendor list is no longer provisional in code:** it moved from a constant in `src/filters.py` to `docs/reference/annotation-vendors.md` with a loader, per ADR-0031, with the three names unchanged. Its evidence is still one census of 34 rows and it has never fired on this pipeline's boards | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0005, ADR-0021 |
| Airtable writer | **UNBLOCKED, held** | The token and seven secrets exist, created by the operator on 2026-09-18. **Held by the operator** until the implementing seat is restarted with a new brief. What it must do is settled: its own client (ADR-0034); upsert on Identity writing only pipeline-owned fields (ADR-0035); the current chain filters the projection (ADR-0040); **skip any identity already held in an outcome store, so a deleted row never returns** (ADR-0046); aggregator rows to the private base (ADR-0047). It does not need the `Status` choices; the sweep does | 2026-09-22 | ADR-0034, ADR-0035, ADR-0040, ADR-0046, ADR-0047 |
| The writer's constraints assembled in one place | DONE | [VERIFIED] every constraint traced to the record it comes from, and the built state of each dependency checked against the tree: the star, the grouping, the term-to-family map and the chain all exist; the three `Status` choices do not. Written at session close because the constraints span nine records over six days and one of them, ADR-0035's field ownership, silently destroys the operator's classifications if missed | 2026-09-22 | `docs/how-to/build-the-writer.md` |
| Daily sweep, routing to three outcome stores | PENDING, behind the writer and the `Status` choices | Design superseded 2026-09-19 by ADR-0046: the operator sets `Status` in `Jobs`; the daily sweep copies the row to its classification table, then at fifteen days on `Classified at` writes it to its store, reads the store back, and only then deletes it from `Jobs`; the two rejection tables delete at fifteen days on `Classified`; `accepted` is deleted by a tool the operator runs. **[VERIFIED] 2026-09-22 through the connector:** `Classified at` exists on `Jobs` and `Jobs test` watching `Status` alone; the three new `Status` choices do not, and the connector cannot add them, so the operator adds them by hand | 2026-09-22 | ADR-0043, ADR-0046 |
| Contract check | PENDING, cadence decided | **Daily**, chosen by the operator from the costed options: about 90 requests a month now and about 240 after ADR-0029's five adapters, against a per-run ceiling of 500 that no run has come within 90% of. ADR-0036 settled the channel. Still unbuilt | 2026-09-18 | ADR-0018, ADR-0036 |

## Blocked, and on whom

Current blockers only. Resolved paragraphs moved to `docs/reference/completed.md` verbatim on 2026-09-22.

| Item | Blocked on | Who | Since |
|---|---|---|---|
| The sweep | Three `Status` choices on `Jobs` and `Jobs test`: `not fit`, `poor filtering`, `accepted`. The connector cannot add a choice to an existing field | Operator, by hand | 2026-09-20 |
| Himalayas' rows being stored at all | The private aggregator repository, its token, and the eighth secret, `AGGREGATOR_STORE_TOKEN` (ADR-0047) | Operator | 2026-09-19 |
| The writer | The operator's go, held until the implementing seat is restarted | Operator | 2026-09-19 |
| Himalayas' trial verdict | 2026-09-26 | Operator | 2026-09-17 |
| Banyan Canopy's review | 2026-09-24 | Operator | 2026-09-17 |
| The stated-experience rule | Deferred by the operator until filtering reads descriptions | Operator | 2026-09-17 |

**Decided, not blocked:** the contract check's cadence is daily (ADR-0036), Rozee.pk is deferred with its trigger in `docs/deferred/`, and the `To review` view exists on `Jobs`.

## Known unverified

**The audit seat has never run.** `docs/how-to/the-seats.md` defines a fourth seat running Claude Code at `ultracode`, which is `xhigh` effort plus dynamic workflows across parallel subagents. Everything that file says about how it behaves is design reasoned from Anthropic's documentation, read 2026-09-22, and not one observation. Three things are unknown and each would change the design: whether the operator's plan allows `ultracode` at all, whether the `PreToolUse` heredoc guard fires on a subagent's `Bash` calls, and whether a workflow's synthesis is accurate enough to act on without re-running its checks. The first job given to it should be scoped small enough that a bad answer is cheap. `docs/how-to/the-seats.md`.

**The workflow's branch fetch and push behave on GitHub as they did in simulation.** [VERIFIED] now in full: run 35236531478 created `data`, run 35239033514 created `data-test`, and scheduled run 35253312417 fetched the existing `data` at depth 1, restored from it, appended, and fast-forwarded the push. `2026-09-17-first-scheduled-run.md`.

**Boards publish to their APIs at the moment a posting goes live.** ADR-0006's cadence rests on it. **Recorded as confirmed 2026-09-11** in ADR-0006's Assumptions, and its Changes row explains why: a posting 0.26 hours old at fetch is positive evidence, and a second run "would tighten the bound and cannot change the verdict". The record outranks this file under ADR-0022. Until 2026-09-17 this entry read "[VERIFIED] partially" and asked for a second run; it predated the record's amendment and was stale. `2026-09-11-endpoint-feasibility-spike.md`, ADR-0006.

**Many ATS platforms expose no publication date.** ADR-0007 asserts it. **Now settled across 16 platforms and it holds, narrowly.** [VERIFIED] a publication date exists on Greenhouse, Lever, Himalayas, Ashby, Workable, SmartRecruiters, Breezy, Pinpoint and BambooHR, and on JazzHR, Freshteam, Zoho and iCIMS only inside per-posting HTML. [VERIFIED] **Manatal exposes no date field of any kind**, across 2 boards and 34 postings, and it holds 8 registry boards. Dover's per-employer board carries none either. Manatal rows can never satisfy Measure A and must use ADR-0007's first-seen fallback. ADR-0007 is unrevised. `2026-09-16-publication-date-across-untested-platforms.md`.

**Workday `startDate` means publication.** [VERIFIED] behaviourally: it equals the fetch date minus the relative age in `postedOn` on 7 of 7 postings spanning ages 1 to 13 days, and none is in the future. An employment start date would not track posting age. The field name still does not say what it holds, so provenance must be recorded. `2026-09-16-second-observation-checks.md`.

**iCIMS `datePosted` is generated, not real.** [VERIFIED] false. The earlier suspicion is **withdrawn**: an older posting reports `2025-05-15T04:00:00.000Z`, sixteen months before the three that shared `2026-09-10T04:00:00.000Z`. The field varies per posting. The shared `04:00:00.000Z` is midnight US Eastern, so the value is a date with no time. `2026-09-16-second-observation-checks.md`.

**Measure A's coverage on the slice is 100%.** [VERIFIED] every one of 916 Greenhouse and Lever rows and all 500 Himalayas rows carries a real publication date; nothing falls back to first-seen. 43 Lever rows carry the date with its meaning unconfirmed. `2026-09-17-vertical-slice.md`.

**ADR-0028's ceiling of 500 is forty times the observed need.** [VERIFIED] first four observations: 11 requests for the eleven ATS boards, 36 on first contact with Himalayas, 12 in steady state for the whole slice. That is one month short of the evidence the record's Confirmation asks for, and nothing yet reads the run logs to aggregate it. `2026-09-17-vertical-slice.md`. **2026-09-22, architecture chat:** [VERIFIED] 36 requests in each of eleven production runs, read from the run logs on `data`.

**The title pool admits 2.1% of postings, and 40 of its 50 terms admitted nothing.** [VERIFIED] 19 rows from 916, seven of them Pakistan-reachable. One concrete gap found: "Forward Deployment Engineer" is dropped while "Senior Forward Deployed Engineer" is kept, because ADR-0021's plural rule cannot reach "Deployment" from `forward deployed`. Widening the pool is the operator's call. `2026-09-17-vertical-slice.md`. **Updated 2026-09-17 against production data:** 21 of 796 admitted (2.6%), 10 terms credited, 39 matching nothing. The operator decided to keep all 39, and the measurement is recorded in `docs/reference/title-pool.md`. `tools/title_pool_report.py` re-measures it and previews candidates: on these eleven boards almost every AI candidate term matched nothing, so widening the AI side depends on adding boards more than terms. `2026-09-17-operator-decisions-d1-to-d5.md`.

**Lever `createdAt` means published.** Still open. [VERIFIED] not contradicted: across five days both Lever boards produced one new posting, whose `createdAt` postdates the baseline clock, so 0 of 1 newly visible postings predate it. One appearance cannot establish the field's meaning. If Lever enters the slice, twice-daily polling answers this from the pipeline's own data within days. `2026-09-16-second-observation-checks.md`. `tools/publication_lag_report.py` now answers it from the data branch once a second production run exists: a Lever posting first seen in a later run and dated before the run that missed it is the evidence. [VERIFIED] 2026-09-17: one production run so far, so nothing to report yet. **2026-09-17, second production run:** 1 of 1 Lever posting first seen in run 2 is dated after run 1, as are 7 of 7 Greenhouse postings. Consistent, and one posting is not proof. **2026-09-18, third run:** now 2 of 2 Lever and 11 of 11 Greenhouse, with none dated at or before the run that missed it. Still consistent, still not proof; two postings is a second observation, not a demonstration of what the field means. `2026-09-17-first-scheduled-run.md`.

**Speechify's board changes by closing whole roles and rotating the cities of the rest, not by a fault.** [VERIFIED] 2026-09-11 to 2026-09-16, 1086 to 361: 723 of the 813 lost postings were four closed roles. [VERIFIED] 2026-09-16 to 2026-09-17T14:52Z, 361 to 255: four roles closed (106 postings) and 64 location copies rotated out and back in; 191 postings were in both snapshots. [INFERRED] the 191 reported at 03:43Z is that intersection, before the 64 replacements appeared; the count matches exactly, the ids were discarded. `2026-09-17-first-github-runs.md`.

**Scheduled runs keep running.** [VERIFIED] from GitHub's documentation: "In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days." Whether the pipeline's own data-branch pushes count as activity is not established. Already recorded as a risk in `docs/architecture-2.0.md`, with the operator's LinkedIn pipeline running over 100 times on bot commits alone as evidence against it. `2026-09-17-run-log-reader-and-speechify.md`.

**Postings per run are on the order of one thousand.** ADR-0001:27, inherited by ADR-0003:28. [VERIFIED] false: 11 of the 53 boards return 1646 postings. Median 27 per board, maximum 1086. The 53-board total is unmeasured. `2026-09-15-spike-followup-checks.md`.

**Lever `createdAt` means published.** Measure A on Lever rows depends on it. [VERIFIED] not established: hosted pages display no date. Page-source JSON-LD `datePosted` matches `createdAt`'s UTC date on 3 of 3, but both come from Lever, so the match is not independent. `2026-09-15-spike-followup-checks.md`.

**Greenhouse `updated_at` marks an edit to a posting.** [VERIFIED] unreliable as such: it is bulk-stamped. 16 of 21 Careem postings share one instant, and Speechify's run in four rotating batches of about 265. What writes it is unknown. `2026-09-15-spike-followup-checks.md`.

**Himalayas can be read newest-first and stopped early.** [VERIFIED] partially: the browse endpoint orders by `pubDate` and paginates by cursor without duplicates over 3 pages. The search endpoint does neither. Browse's newest posting trailed search's by 97.7 minutes. [BELIEVED] from that lag, not observed: a stopping rule keyed to a run's wall clock would skip postings that reach browse late. Termination is not established. `2026-09-15-spike-followup-checks.md`.
