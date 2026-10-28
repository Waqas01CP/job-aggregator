---
type: log
description: The due items of Brief 19 caught up on 2026-10-28. EWOR's walk of Himalayas' search to the floor of 10-19 and items 146 and 149; every run since 10-22 read, all clean; October's Airtable calls accounted for by kind and the code set against Airtable's limits read at the source; the tables' fields checked before November 1; the switch commit replayed on main; the audit brief brought up to date.
status: current
---

# The walk, the month's calls and November ready, 2026-10-28 UTC

Previous log: `2026-10-21-brief-19-the-audit-brief-and-november-rehearsed.md`.

| Header | Value |
|---|---|
| Date | 2026-10-28 from about 10:30Z, the same session as Briefs 12 to 19 |
| Model | claude-opus-5-5 |
| HEAD at start | `4f133d3`, level with `origin/main` |
| HEAD at end | `4f133d3` and this commit; the local branch `nov-1-switches-v2` at `bf8fe2e` |
| Mode | **Read-only on the data.** `data`, `data-test` and the private repository's `data` branch from scratch clones; Himalayas' search walked once; Airtable's documentation read; **2 Airtable connector calls**, the tables' schema |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run. `[O]` outside this repository.

## What was asked

The operator, 2026-10-28, with the briefs still unsent and his meter at 870 of 1,000 at 10:26Z:
- do whatever dated work should be done now, and anything that can be completed or is due, checks on the tables included;
- how far the code is optimised for Airtable's calls, against Airtable's own read and write limits.

## Errors this seat made

- **Item 157's projection of 2026-10-22 was wrong:** 840 to 870 for month's end, and 870 came on 10-28. It assumed 8 calls a day; the pipeline spends about 14.
- **The walk's first try paced 1.5 seconds a page.** Himalayas answered page 4 with a 429. The partial snapshot was deleted unread, and the walk was rerun at 5 seconds a page, waiting out a 429 as asked. None came.
- **An update script for the audit brief stopped twice on its own count check,** nothing written either time.

## What was done

**EWOR's walk** [VERIFIED]: Himalayas' Pakistan search, 2026-10-28T10:38Z, to the floor of the walk of 10-19 (published 2026-10-03T10:54Z): 98 pages, 1,960 postings.
- **Item 146:** all 91 of the baseline's EWOR postings are gone, and 22 new ones appeared (10-23, 10-24, 10-28), every one templated. None of the 196 stored in the band was admitted. No exclusion is needed.
- **Item 149:** of 1,310 other Himalayas postings stored in the band, 298 left the search before their expiry, 22.7%; of the 59 admitted, 4, 6.8%; of EWOR's 196, all.

**The runs since 2026-10-22** [VERIFIED]: 13, to 10-28T04:20Z, all clean, 95 to 134 requests each.

**October's Airtable calls** [VERIFIED from every run log]:

| Kind | Calls |
|---|---|
| Production sweep | 255 |
| Production projection writes | 210 |
| Production projection reads | 85 |
| `Health` | 8 |
| Test mode | 77 |
| **All** | **635** |

His meter, less that, leaves about 235 from elsewhere [INFERRED]. The pipeline spends about 14 a day since 10-22.

**Airtable's limits** [O, read 2026-10-28]:
- **The allowance:** 1,000 calls a month on the free plan, reset on the first of each UTC calendar month. Integrations count. Over the limit, a one-time thirty-day grace, then 429s.
- **The rate:** 5 requests a second per base.
- **The batch sizes:** 10 records a write; 100 a page on a read.

The clients are at each limit: `BATCH_SIZE = 10`, `PAGE_SIZE = 100`, four a second.

**The tables' schema**, 2 connector calls [VERIFIED]: `Jobs` and `Jobs test` both hold the four description fields and `Who reads`, of the documented types.

**November 1:** `62faca8` replayed on `4f133d3` as `bf8fe2e`, branch `nov-1-switches-v2`, local; both suites pass, 1,067 tests.

**The audit brief** (`briefs/audit.md`, gitignored):
- **The range:** extended to `4f133d3`, 121 commits.
- **The date:** the report ideally by 2026-10-31.
- **The meter:** his reading of 870.

## Verification

- **`bf8fe2e`:** suites on 3.12 and 3.11, each alone in a scratch clone, 1,067 tests, the map clean.
- **This commit:** its suite before the push.

## Not done

- **Both briefs:** his to send, about 10-29.
- **The November 1 push:** after the evening run of 10-31, or on 11-01 before about 03:30Z, in a session he opens.

## Open

- **Fewer Airtable calls, three levers set out for the chat, none built:** the evening run's Airtable work; the rejection tables' reasons; an evening read of `Jobs` skipped when nothing is new.
