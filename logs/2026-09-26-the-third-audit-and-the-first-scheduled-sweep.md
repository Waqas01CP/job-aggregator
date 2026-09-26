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

## The operator's answers, and D12 and D11 built

**D12, the audit's F1: `accepted` copies.**
- **His words:** "the not fit and poor filtering has different meaning being
  deleted but after saving them and then deleting, correct? now this takes us
  back to the main question that the accepted is ever deleted and the answer
  is yes. you can say that it is option A but improvised meaning that there
  will be an additional row which says delete and there will be a single
  option of yes and null will be considered no so when i deem that this job
  should be deleted then i will just select yes but that does not mean it will
  be permanently deleted but rather from the airtable. i still expect that the
  local copy or the storage to have all the 5 storage meaning raw, jobs, not
  fit, poor filtering and accepted."
- **His premise was half right, and the seat said so.** A rejection copy was
  deleted at fifteen days only after its outcome was stored. But one
  superseded by a status change was deleted with its reason unsaved, as
  ADR-0050 line 71 reads. The build makes the rest match what he expected.

**Built, in `src/sweep.py`** `[VERIFIED]` by tests, and each rule by a
mutation:
- **A cleared `Status` removes nothing**, from any table.
- **An `accepted` copy stays whatever its row's status becomes**, reported
  in the run log.
- **A superseded rejection copy is saved first.** Its reason goes to a new
  store, `removed_copies.json`, keyed by the copy's record ID. The copy is
  deleted on a later run once origin holds the record, the same write,
  verify, delete as everywhere else.
- **An `accepted` copy leaves Airtable only when he sets `Delete` to yes.**
  - The next daily sweep saves it, `Stage` as it stands then, to
    `removed_copies.json`, and to the accepted store if its row is still in
    `Jobs`.
  - A later sweep removes it once both are read back, with its `Jobs` row if
    there is one; left there, step 1 would copy the row straight back.
  - Nothing leaves a store.
- **Not a classification store.** `removed_copies.json` is not one, so the
  projection never reads it and nothing in it hides a row.

**In Airtable, through the connector `[VERIFIED]`:**
- `Delete`, a single select whose one choice is yes, created on `accepted`
  and `accepted test` and read back.
- The stale descriptions the audit named (F8) rewritten for ADR-0050 and
  D12: the `Jobs` table, `Status` and `Classified at` on both `Jobs` tables,
  the three classification tables, and all six `Classified` fields.

**Recorded:** `docs/reference/airtable-schema.md` and
`docs/reference/retention.md`, with Changes rows.

**Not recorded:** ADR-0050 line 71 is now contradicted by his decision, and
recording that is the architecture chat's. Brief 7 said the seat must add no
Changes row there in the record's first week.

**D11, conflict 2: where descriptions go.**
- **His words:** "the only reason i would save the description and other data
  on private repo is because of their terms and conditions otherwise i see no
  reason to save it on the public and make the work easier but if there
  really is not a difference in either saving on private vs public and there
  is no hassle then i will choose public otherwise private is reasonable and
  you can proceed automatically if that the data there is stored properly.
  you should store something of description if you go the private repo way
  and fetch back to recheck that the saving is done properly."
- **The two differ on the concern he named**, republishing employers' text
  and the personal data inside it, publicly and for good. So by his own rule
  it is private.

**Built** `[VERIFIED]` by tests and each guarantee by a mutation:
- **What is saved.** Every posting a run fetches, as its board returned it,
  description and all:
  - Greenhouse is now asked for `?content=true`;
  - Lever and Himalayas already sent everything.
- **Where.** On the private repository's own `data-full` branch (test mode
  `data-test-full`), one file per run.
- **No run downloads what earlier runs saved.** A partial fetch brings
  commits and trees only; a probe on a local bare repository took 1.4 KB for
  a branch holding 270 KB.
- **The read-back.** After the push, a second fresh partial fetch must list
  the file with exactly the content hash written, or the save fails. Two
  tests give it the cases built to defeat it: a branch listing different
  content, and a branch missing the file.
- **Only then are the postings marked saved**, in both seen stores.
  - A failed save is the private store's failure: exit 2, the fetch
    committed, the run marked failed at once (D9).
  - An ATS posting is saved by the next run that still sees it listed.
  - A Himalayas posting is not fetched again, so a failed run loses its
    full record, reported.
- **The first production run saves everything currently listed**, about
  800 ATS postings and one morning's Himalayas, about 10 MB `[INFERRED]` from
  today's sizes.
- **Nothing of it reaches the public branch:** a test greps the public
  branch for the description it planted and finds nothing.
- **The contract check is unaffected.** It fingerprints only consumed
  fields, and `content` is not one.

**Answered without a build:**
- **`Published` against `First seen`.** Read through the connector: all 101
  `Jobs` rows. Every date field in all five tables displays in UTC.
  - `First seen` is never before `Published`.
  - `Order date` equals `Published` on every row, as ADR-0007 intends when a
    board gives a date. Each is the board's own date, never the fetch time.
  - The 346 stored public rows agree.
  - Old postings appear because ADR-0007 ingests everything still listed
    and orders by date. "At most a week old" is therefore a view, not a rule.
- **Himalayas' location restrictions.** Its feed carries
  `locationRestrictions`, which `Location` already shows, and
  `timezoneRestrictions`. On one page of 20, 17 were restricted to countries
  without Pakistan and 3 were unrestricted. A rule is his to set (D13).

**Verified for it**, at 2026-09-26T10:58Z: 643 tests on Python 3.12 and 3.11, and the mutation files for D12 and D11, and every older file their code touches, still running at this commit; the results follow in the next `[VERIFIED]`. Nothing of D11 has run on GitHub yet: the first run after the push is the live check, and the first thing it proves is that the private store's token may create the new branch.

**The 11 stale mutations re-expressed.** In the 2026-09-17 and 2026-09-18 files, edited in place so each file keeps its own formatting:
- six backfill mutations follow their code from `tools/backfill.py` to `src/backfill.py`;
- three restore mutations get enough context to be unique, or the tuple as it now reads;
- one run-log-report mutation matches the call as it now reads;
- the pool-order mutation swaps sections 3 and 4 of today's pool.

Every find in every mutation file now matches exactly once `[VERIFIED]`. Whether the suite still catches them follows in the next commit.
