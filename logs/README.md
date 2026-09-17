# Session logs

One log per session, newest at the top. This table is the navigation index for all session history.

The first rows are diagnostic sessions. Implementation began with the vertical slice on 2026-09-17.

## How to use this file

Read this table first. It tells you what prior sessions did.

**When you need detail beyond what this table gives, read the most recent relevant log. That log references the one before it. Chain backwards only as far as you need, and stop when you have enough.** Do not read the directory.

This rule is what keeps the reading cost flat as the log count grows.

## How to maintain it

**Append your row in the same commit as your work.** A session that writes a log and does not index it has left the log invisible.

**Never delete or modify an existing row.** If a later session corrects an earlier one, that is a new row saying so.

**Rows are compressed. No prose, no reasoning, no elaboration beyond what a future session needs in order to decide whether to open the log.** The reasoning lives in the log, one level down. An index that explains is an index nobody finishes reading.

**If a log file exists with no row here, read it and add the row before doing anything else.**

## Log format

ADR-0024. In short: a header with date, model, the HEAD commit, and whether the session was read-only or mutating. Every factual claim carries a file and line, or a command and its output. Every claim tagged `[VERIFIED]` or `[BELIEVED]`, with unmarked meaning believed. Rejected alternatives recorded with the reason. What was checked and found already correct, recorded. What was not done, stated explicitly. Findings separated from decisions.

Length follows the work. No cap, no floor.

## Reorganisation

When this directory passes roughly 80 to 100 files at its root, split by lane into subdirectories and leave this index at the top pointing into them. Do it before the root becomes unscannable, not after.

## Index

| Date | Session | What was done | Outcome |
|---|---|---|---|
| 2026-09-17 | Role families, seniority, and two trials | Pool version 3 in the operator's family order with ten software terms. Seniority rule decided by the operator, II and III checked against Veeam descriptions, architect kept. ADR-0021's case set tested for the first time. Himalayas and Banyan Canopy on trial until 2026-09-24. 303 tests, 13 mutations | On production data: 267 kept, 241 of them Speechify city copies, 32 dropped for seniority, 6 mentioning Pakistan. The rule departs from ADR-0021's no-blocklist and its "Software Engineer II" case; raised. A false note about `software engineer i` corrected. Not pushed |
| 2026-09-17 | The operator's decisions D1 to D5 | Moved `data/test` to `data/archive/2026-09-16-test`, verified. Pool version 2 with `forward deployment`; the 39 unmatched terms kept and recorded. `tools/title_pool_report.py` built and 32 candidates previewed. Experience rule deferred. Himalayas evidence gathered from saved responses. Airtable plugin examined. 285 tests, 16 mutations | Himalayas: 74 of 91 saved postings exclude Pakistan, one of 8 pool matches fits the operator's levels. A senior-word title rule would drop 10 of 21 kept. Found and removed a stray `data/seen.json` written by my own earlier test |
| 2026-09-17 | Test run verified, and the work that needed no input | Ticked run 35239033514 succeeded: `data-test` pushed, `data` untouched. Built `tools/publication_lag_report.py` for Lever `createdAt`. README brought up to date. ADR-0023 annotated. Decision pack written for the operator, local only. Greenhouse metadata checked for the experience rule. 268 tests, 14 mutations | Test mode works on GitHub; the restore path is still unexercised there. Airtable writer and sweep wait on the chat: the shared HTTP module must change. Gate 4's date is 2026-09-15, not 09-11. The metadata lead is weak: one board, a grade code, no years |
| 2026-09-17 | The first manual GitHub runs | Operator pushed `6476573` and ran the workflow twice. Ticked run failed its tests: job-level `TEST_MODE=1` reached the test step. Fixed in the tests and the workflow, reproduced by an extended simulation that now runs the test step. Production `data` branch checked. 252 tests, 5 mutations | Unticked run succeeded and created public `data`: Greenhouse and Lever only, 36 requests, Himalayas' 21 kept rows lost with the runner. Speechify's 191 is the 09-16/09-17 intersection. Fix not pushed |
| 2026-09-17 | Run-log reader, Node 24 actions, Speechify | The four no-input follow-ups. Actions moved to checkout v5 and setup-python v6. Em-dash count corrected to 54 in 7 files, one prose instance fixed. `tools/run_log_report.py` built for ADR-0028. Speechify's loss explained from saved data. Local title-pool review file written for the operator. 249 tests, 22 more mutations, one survivor fixed | Speechify lost four whole roles, 723 postings; the rest is location rotation. 361 to 191 unexplained. GitHub disables scheduled workflows after 60 days without repository activity, raised. Nothing pushed |
| 2026-09-17 | A runner-safe data branch | Found the first GitHub run: scheduled, fetched 1239, failed at `commit-tree`. Fixed five defects: no git identity, aggregator records inside the committed filtered and seen files, no state restored on a runner, test mode pushing production's branch, a text-mode git boundary on Windows. Mutation harness rebuilt in `tools/`. Verify-do-not-trust rule added to `CLAUDE.md`. 225 tests, 39 mutations, one survivor fixed | Old and new code both run through a local simulation of the workflow's steps. Nothing pushed, so the fixes have not run on GitHub. Himalayas keeps nothing on a runner, against ADR-0020's premise; raised for the architecture chat |
| 2026-09-17 | The vertical slice, built | Config, HTTP module, both adapters, normaliser, deduplicator, filter chain, writers, orchestrator, schedule, plus Himalayas on condition. 183 tests, 79 mutations, 8 survivors all resolved | Four live runs: 917 postings, 19 kept, second run byte-identical. Speechify collapses to 11 keys not 8, which is ADR-0001's key doing its job. Two filter rules have no definition anywhere and are not invented. Himalayas passes ADR-0019 on its three named components and fails its "config and adapter only" wording. Log carries a session-close section: why 8 mutations survived, the `_git` default-argument defect, what was tried and failed, 9 things noticed and not investigated |
| 2026-09-16 | Second-observation checks on three date fields | 7 GETs of a self-imposed 12. Tests chosen to need no elapsed time, since only 1h31m had passed | Workday `startDate` confirmed behaviourally, 7 of 7 across ages 1 to 13 days. The iCIMS "generated timestamp" suspicion is **withdrawn**: an older posting reads 2025-05-15. Lever `createdAt` still unsettled on one appearance in five days |
| 2026-09-16 | Publication date across the 13 untested platforms | 53 GETs of a 60 cap, one board per platform. Item 54: both earlier logs retyped `research` to `log`, map regenerated | Zero NO ENDPOINT. PROCEED: Ashby, Workable, SmartRecruiters, Breezy, Pinpoint, BambooHR. INVESTIGATE: the other 7. Manatal exposes no date field on 34 postings across 2 boards, which is ADR-0007's material case. Workday and BambooHR need 1 request per posting for a date |
| 2026-09-15 | Spike follow-up checks | 4 checks: 2 on disk, 10 GETs (Lever pages, Himalayas). Backfilled the 2026-09-11 log. STATE rows updated | 1646 postings on 11 boards falsifies ADR-0001:27 and ADR-0003:28. Speechify floor real: 8 titles across 329 locations. Lever pages show no date. Himalayas browse paginates newest-first; search does not |
| 2026-09-11 | Endpoint feasibility spike, log written 2026-09-15 | 13 GETs: Greenhouse 9 boards, Lever 2, Himalayas 1 | Greenhouse PROCEED, Lever INVESTIGATE (no employer field), Himalayas PROCEED. Publication date on 100% of postings on all three |
