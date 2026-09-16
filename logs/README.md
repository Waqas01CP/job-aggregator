# Session logs

One log per session, newest at the top. This table is the navigation index for all session history.

Nothing has been implemented. The first rows are diagnostic sessions, not implementing ones.

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
| 2026-09-16 | Second-observation checks on three date fields | 7 GETs of a self-imposed 12. Tests chosen to need no elapsed time, since only 1h31m had passed | Workday `startDate` confirmed behaviourally, 7 of 7 across ages 1 to 13 days. The iCIMS "generated timestamp" suspicion is **withdrawn**: an older posting reads 2025-05-15. Lever `createdAt` still unsettled on one appearance in five days |
| 2026-09-16 | Publication date across the 13 untested platforms | 53 GETs of a 60 cap, one board per platform. Item 54: both earlier logs retyped `research` to `log`, map regenerated | Zero NO ENDPOINT. PROCEED: Ashby, Workable, SmartRecruiters, Breezy, Pinpoint, BambooHR. INVESTIGATE: the other 7. Manatal exposes no date field on 34 postings across 2 boards, which is ADR-0007's material case. Workday and BambooHR need 1 request per posting for a date |
| 2026-09-15 | Spike follow-up checks | 4 checks: 2 on disk, 10 GETs (Lever pages, Himalayas). Backfilled the 2026-09-11 log. STATE rows updated | 1646 postings on 11 boards falsifies ADR-0001:27 and ADR-0003:28. Speechify floor real: 8 titles across 329 locations. Lever pages show no date. Himalayas browse paginates newest-first; search does not |
| 2026-09-11 | Endpoint feasibility spike, log written 2026-09-15 | 13 GETs: Greenhouse 9 boards, Lever 2, Himalayas 1 | Greenhouse PROCEED, Lever INVESTIGATE (no employer field), Himalayas PROCEED. Publication date on 100% of postings on all three |
