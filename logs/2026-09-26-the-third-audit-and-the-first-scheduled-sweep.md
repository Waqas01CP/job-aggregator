---
type: log
description: The first scheduled sweep verified; the third audit's findings closed except F1, which is the operator's to decide; the projection's cost found to grow with the display; descriptions measured for the operator's choice on conflict 2.
status: current
---

# The third audit, and the first scheduled sweep, 2026-09-26 UTC

Previous log: `2026-09-25-first-production-mornings-and-brief-7.md`.

| Header | Value |
|---|---|
| Date | 2026-09-26, from 07:55Z, UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `783ba3e`, level with `origin/main` |
| Mode | **Mutating** |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means
believed. `[INFERRED]` reasoned from observed data, not tested.

## The first scheduled sweep

Run 36216026882, 03:50Z, on `783ba3e`, from its log on `data` at `063f75d`
and through the connector `[VERIFIED]`:

- **The operator's 12 marks copied.** Ten went to `rejected-not-a-fit` and
  two to `rejected-poor-filtering`. They are the 12 Himalayas rows no stored
  layer holds; he marked them on 2026-09-25, 21:10Z to 21:24Z, per the audit.
  Each copy's identity and title were read back in its table. All 15 of
  those rows are now classified, and `not_in_the_stored_layers` is 0.
- **Nothing else moved.** No new `Closed` (the three are already marked),
  nothing deleted, no problems.
- **Cost:** the projection spent 9 calls for 86 groups and the sweep 7. The
  month stands at 86.
- **Himalayas hit its page cap for the third run in a row:** 500 fetched and
  499 new. The oldest posting reached was published at 2026-09-25T20:32:58Z,
  against the previous production poll at 20:10Z the evening before. The gap
  is short only because the operator's dispatch had polled then.

This is the one path the two dispatches of 2026-09-25 did not take: a
scheduled slot, running the daily steps because it is the morning. STATE's
sweep rows move to DONE on it. Two items stay open:
- `accepted test` surviving past fifteen days cannot be seen before
  2026-10-08;
- F1 below.

## The third audit, `06c3749..783ba3e`

A fresh audit chat, 2026-09-25 21:26Z to 22:45Z, read-only, relayed by the
operator. It found no deletion that happened was wrong, and ADR-0050's
ordering holding in code and live. All 86 mutations in the six files the brief
named were caught. Its findings, and what was done `[VERIFIED]`:

| # | Finding | Done |
|---|---|---|
| F1 | Clearing or changing a status deletes the old copy, `accepted` included, with its `Stage`, against the `accepted` table's own description and `retention.md` | **Not changed.** The code follows ADR-0050 line 71 as written, and resolving it changes a record: the operator's decision, asked as D12 |
| F2 | Nothing checked that a mode's four tables are distinct; `accepted` given `Jobs`'s ID made step 1 delete every unmarked `Jobs` row | `SweepClient` refuses any two of its four tables sharing an ID, by key and never by value. `from_env` now refuses a table ID of the other mode both ways |
| F3 | The second count of the month's calls in `main()` had no guard; a failure exited 1 and lost the fetch | `main()` reuses the projection's count, and counts again only when that is missing, guarded. When the count cannot be read the sweep is skipped and says why, and the run exits 2 with the fetch committed. The new test found a second fault in the first repair: `summarise()` read the missing count and would have crashed the run. Fixed |
| F4 | Step 3 deleted a copy step 1 had already removed, failing the daily sweep | Step 1 takes the copies it deleted out of the run's read |
| F5 | Four guarantees with no test | Four tests, one for each: the mask on an aggregator identity in a problem line; the second private push, through a real bare repository; ten records a call on every write; a read failing after its first page. The in-memory base now refuses more than ten records and a delete of a missing record, and a test can make any call fail |
| F6 | The three fitness functions quoted clauses their records do not contain, and the meta-test could not see it | Each docstring now quotes its record verbatim. The meta-test checks that the quoted clause is in the record, and its can-fail test puts five defeating docstrings through that same check |
| F7 | `CLAUDE.md` and the workflow's messages never mentioned the sweep | The exit-code paragraph, the workflow's exit-2 comment, its warning and its escalation error now name a sweep failure |
| F8 | The Airtable descriptions predate ADR-0050 | **Waiting on D12**, since the `accepted` table's description states the promise F1 is about. All of them are rewritten in one pass once he decides |
| F9.1 | The base had no ten-record limit and ignored a missing delete | Done with F5. The claim that `Classified at` moves on a cleared `Status` stays unconfirmed against Airtable |
| F9.2 | The stamp gate missed a stamp with seconds | It reads seconds and fractions, cut to the minute. Proved in a scratch clone: a future stamp to the minute, with seconds, and with a fraction each block (exit 1), and a past stamp with a fraction passes. A time with no date cannot be judged and is not read |
| F9.3 | "Durable" means origin only on a runner | Said so in `src/sweep.py`'s docstring |
| F9.4 | A closure test that could not be built skipped the copy too | The copy runs, the daily steps do not, and the run reports it as a sweep failure |
| F9.5 | ADR-0006's annotation counted three runs where four had run | Corrected, with a Changes row. The corrected figure is also stale: see the next section |
| F9.6 | The seats file's operator section still gave him pushing alone | It now says the seat pushes its own commits under D10 |
| F9.7 | "A manual dispatch copies at once" | It copies within minutes, and it also runs the daily steps and polls Himalayas. Said so in the report to the architecture chat |

## Found by the seat: the projection's cost grows with the display

The projection re-sends every display group on every run, at ten a call. From
the production run logs on `data` `[VERIFIED]`:

| Run | Groups sent | Projection calls |
|---|---|---|
| 2026-09-24 03:27Z | 44 | 5 |
| 2026-09-25 03:44Z | 52 | 6 |
| 2026-09-25 20:10Z, dispatch | 70 | 7 |
| 2026-09-26 03:50Z | 86 | 9 |

**The growth.** Each Himalayas poll adds 15 to 25 kept rows. A row leaves
`Jobs` only a day after its fifteen days, classified or closed, and a
Himalayas row closes by expiry alone.

**The arithmetic, not measured `[INFERRED]`:**
- The display holds about 250 rows by early October, on the current growth
  with nothing yet old enough to leave. That is 25 calls a projection and
  about 50 a day.
- The month's 1,000 is then reached in the second half of October.
- The budget line warns once 600 are passed before the fifteenth. The client
  refuses at 1,000, so the allowance is never overspent, but the display
  stops updating until the month turns.

**The obvious remedy** is to send only the groups that are new or changed
since the last successful projection. It touches ADR-0034, ADR-0035 and
ADR-0040's re-projection of the whole layer, so it is the architecture
chat's.

## Conflict 2, measured for the operator's decision

He decided on 2026-09-25 that descriptions, and every field, are to be saved.
He asked for the private and public choices compared before he says where.

**Measured on 2026-09-26, one request each** `[VERIFIED]`:

| Board | Postings | Description per posting |
|---|---|---|
| Greenhouse, Careem | 18 | median 6,613 characters, max 11,641. `?content=true` made the response 6.7 times larger: 27,437 bytes to 183,450. The adapter's docstring says 9.5, from another board |
| Lever, Spreetail | 30 | median 11,243 bytes across its description fields. Already in every response |
| Himalayas, one page | 20 | median 5,892 characters, max 10,979. Already in every response |

**Himalayas' descriptions go private whichever he chooses**, since ADR-0047
keeps aggregator data there.
- At about 500 new postings a morning, that is about 3 MB a day and about 1
  GB a year before compression `[INFERRED]`.
- So the choice covers the ATS boards alone: about 20 new postings a day,
  about 70 MB a year `[INFERRED]`.
- The comparison itself is in the reply to him and in the report to the
  architecture chat.

## Pre-existing: 11 stale mutations in the older files

A check of every mutation file's finds, run for this round `[VERIFIED]`,
found 11 that no longer match their code. All are in files of 2026-09-17 and
2026-09-18, against code this session did not touch:
- three in `2026-09-17-publication-and-state.json`;
- one in `2026-09-17-run-log-report.json`;
- one in `2026-09-17-seniority-and-families.json`;
- six in `2026-09-18-backfill.json`.

The harness refuses such a file before running anything, so those
guarantees are unproven until the mutations are re-expressed. The seat's to
do.

## Verification

- **630 tests** on Python 3.12 and on 3.11 `[VERIFIED]`.
- **This round's mutations**, `tools/mutations/2026-09-26-third-audit.json`,
  in a scratch clone: 13 of 13 caught `[VERIFIED]`.
- **Brief 7's 30**, re-run in three scratch clones, because the base and the
  sweep changed under them: 30 of 30 caught `[VERIFIED]`.
- **The widened stamp gate**, run directly in a scratch clone, as above
  `[VERIFIED]`.
