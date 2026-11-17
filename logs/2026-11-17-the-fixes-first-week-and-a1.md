---
type: log
description: The session of 2026-11-17. The checks due on 11-10 and 11-11 made late: every run from 11-09 to 11-17 none failed or stopped, the whole search read, the vendors' rows gone, the agreement check seen again, October's classifications retired; Measure A to 11-17; Hacker News' first month recounted; A1 built on a branch for his rehearsal; B1 measured at about 20 calls a month and held for his word.
status: current
---

# The fixes' first week, and A1, 2026-11-17 UTC

Previous log: `2026-11-08-the-fifth-audit-acted-on.md`.

| Header | Value |
|---|---|
| Date | 2026-11-17 from about 14:00Z, the same session as Briefs 12 to 19 |
| Model | claude-opus-5-5 |
| HEAD at start | `70d5494`, level with `origin/main` |
| HEAD at end | This commit on `main`; A1 on the branch `a1-evening-view`, `a02ae3a` and `7aa417c` |
| Mode | **Read-only on the data.** `data` and the private repository's `data` from scratch clones; Hacker News' public API, one request a second, for 22 posts; **no Airtable call** |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run. `[O]` outside this repository.

## What was asked

The operator, 2026-11-17 (Pakistan time): do the overdue work on this project, the checks of 11-10 and 11-11 among it, before anything else. His meter: 362 of 1,000 on 11-17.

## Errors this seat made

- **The checks due on 11-10 and 11-11 were not made on the day:** no session was opened between 11-09 and 11-17.
- **A stale mutation find, the second in two weeks.** A1 rewrote lines five older mutations name, and the seat committed without running the find check, as it had said on 11-09 it would. The suite caught it on the branch before any push; the five are re-pointed and folded into A1's commit, which had not left this machine. The seat proposes a pre-commit gate for it, waiting on the chat since it changes `docs/how-to/the-seats.md`'s count of gates.
- **Two of A1's run tests first failed on the seat's own test errors,** the harness's identity and its clock, and one of its mutations survived a test that counted reads rather than asking where they came from. Each corrected before any commit left this machine.

## What was done

### The runs of 11-09 to 11-17

Eighteen production runs, none failed or stopped [VERIFIED from `data`'s run logs]:
- **The tail of 11-09:** the evening read the 23 pages the morning's cap had left and stored 330 new Himalayas postings; every morning since read 103 or 104 pages to the end, uncapped, at 200 to 217 requests.
- **The vendor rule:** 112 rows stored on 11-10, deleted on 11-11.
- **The agreement check:** 3 disagreements on 11-10 and 1 on 11-12 reached `Health`; the waiting postings settled.
- **October's classifications:** 66 rejections stored on 11-12, their copies deleted on 11-13. Both rejection tables are empty since: he has classified nothing since about 11-01.
- **Airtable:** the pipeline's 292 calls in November by 11-17's morning, about 17 a day; his meter's 362, so his chats about 70. The base: 313 records of 1,000.

### Measure A, 11-01 to 11-17

290 rows, median 6.1 hours, 90th percentile 28.1, against 24 and 72; 2 dateless rows excluded [VERIFIED, `b19/measure_a.py`].

### Hacker News' first month, ADR-0063's Live only

2026-10-19 to 11-17, counts only [VERIFIED]: 636 posts read, 521 from the threads and 115 job stories; 22 kept, 17 and 5, 19 of them in November against a projected 10 a month. Who reads: 1 founder, 2 engineers, 1 a named person, 18 unsaid. 11 remote, 11 unsaid. The apply route, from each kept post's text on the public API: 8 a careers page or ATS, 4 an email to a person, 3 both, 6 another link, 1 none. He rejected 3, 2 "location wrong" and 1 duplicate.

### A1, on a branch

Measured first: November's evenings spent 59 calls in 16 runs re-reading `Jobs` and 3 sweeping. Built: every run that reads `Jobs` keeps its view, fields only, in the private `agreement/jobs_view.json`; a scheduled evening with a view of the last 22 hours sends against it, reads nothing and runs no sweep. The dispatch gains a `slot` choice for the rehearsal. **On `a1-evening-view`** until he rehearses it.

### B1, measured and held

The rejection tables were read on 6 mornings of 17 in November, 2 calls each: B1 would save about 20 calls a month at his present pace. The seat recommends not building it; his to decide.

## Verification

- **A1's commits alone, on 3.12 and 3.11,** 1,132 tests, and its 16 mutations caught once its weak test was strengthened [VERIFIED].
- **This commit:** its suites before the push.

## Not done

- **A1's rehearsal and merge:** his two test-mode dispatches first.
- **A3:** waits on the webhook scope on his token.

## Open

- **B1:** his word.
- **The pre-commit gate for mutation finds:** the chat's word.
