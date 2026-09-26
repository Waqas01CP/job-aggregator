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

## D13 and D14: eligibility and age, built

**The operator's words, 2026-09-26.**
- **D14:** "i do not want a job post more than a week old because after a week
  the chances of getting a job form that is drastically less ... the main
  intention for creating this entire system were two: 1. i appear first and
  apply within the few hour when the posting goes live ... 2. that i get the
  most recent of posts and not more than week old".
- **D13:** "any onsite post besides karachi, pakistan are automatically out.
  the for the remote work it is worldwide but ... you are either a resident
  of a specific country or have working permission to that so those are out
  as well automatically besides pakistan ... time zone is not an issue ... if
  they say that they are hiring from anywhere like worldwide or lets say no
  mention of a country i.e. null or the said restrictions then they should be
  filtered in. the goal is simple, i do not want any jobs shown in the table
  which i am not eligible to while at the same time i do not want to miss any
  to which i am eligible to."

**Measured before building** `[VERIFIED]`:
- **Himalayas, 100 postings from five pages of its feed:**
  - 93 restricted to named countries, none of them Pakistan;
  - 7 with no restriction;
  - every value a plain country name, no regions;
  - lists of one country on 98, two on one, three on one;
  - the adapter kept only the first three countries, so a list naming
    Pakistan fourth would have read as closed.
- **The ATS boards' locations are free text.** On the 346 stored public
  rows they take a few shapes:
  - "city, country", sometimes with a US state, sometimes a list;
  - a bare "Remote";
  - "United States - Remote";
  - regions such as "Latin America".
- **Lever's `createdAt`**, against when the pipeline first saw each posting
  after its board's first contact:
  - 22 postings, median lag 7.1 hours;
  - but 6 first seen more than a week after their `createdAt`.
- **Greenhouse:** 161 such postings, median lag 632 hours. These are old
  requisitions reposted under new IDs with their original
  `first_published`: what D14 is meant to remove.

**Built** `[VERIFIED]` by tests, and each guarantee by a mutation:
- **`rule_location`, D13.** A posting is dropped only when every place it
  lists is closed:
  - a country other than Pakistan;
  - a region without it;
  - a Pakistan city other than Karachi that says it is on site or hybrid.

  Kept:
  - no location, which is how Himalayas' empty restriction reads;
  - "Remote" naming no country;
  - a region that can include Pakistan;
  - anything saying "except";
  - any place the list cannot name.

  An unrecognised spelling can only let a posting through, never lose one.
- **`rule_age`, D14.** A posting whose publication date is more than 7 days
  before the run is dropped. Two exceptions:
  - A Lever posting first seen within the week is kept, since its date is
    unproven.
  - A posting with no date is kept.
- **Both come last in the chain**, after title and seniority, so each count in
  the run log is relevant roles lost to place or to age, and the title rule's
  drop log stays the pool's feedback.
- **The places and the week** live in `config/eligibility.json` under
  ADR-0031.
- **The Himalayas adapter now keeps every country.**
- **Tests of other mechanisms**, on saved responses weeks old or fixtures
  from before any clock, now hold the two rules aside explicitly through
  `tests/eligibility.py`. The fixtures of the fetch, backfill and sweep tests
  were re-dated within the week instead.

**The effect on `Jobs`**, the 101 rows read through the connector at about
12:10Z with both rules applied offline `[VERIFIED]`:
- **The 15 classified rows are untouched.**
- **Of the 86 unclassified rows, 13 stay:**
  - 12 Himalayas roles with no restriction;
  - one Lever role in "Kingswinford", a place the list cannot name, so kept.
- **73 go:** 45 for location, 17 for both, 11 for age alone.
- **The 11 age-only rows include four Pakistan roles:** MLOps Engineer and AI
  Evaluation Engineer at Joblogic (9 days old), and AI/ML Engineer and QC
  Automation Engineer, older.
- **Nothing goes before it is saved.** The projection stops sending them at
  the next run. The next daily sweep, 2026-09-27's morning, saves them to
  the removed-unreviewed store. The one after removes them from `Jobs`. A row
  the operator marks before then is untouched.

**The call budget.** `Jobs` falls from 101 rows to about 28, so a projection
costs about 3 calls again `[INFERRED]`. The Blocked row on the month's
calls is mostly answered.

**Himalayas' page cap does not go down with this**, and the operator asked
to be told if it would not.
- The cap limits what is fetched; the rules act on what was fetched.
- On 2026-09-26's morning run, 499 new postings covered about 7.3 hours of
  publications. That is about 1,600 a day against a cap of 500 a morning
  `[INFERRED]`.
- At the 7% unrestricted share measured above, and the 3% the title and
  seniority rules keep, about two eligible, matching Himalayas roles a day go
  unfetched `[INFERRED]`.
- The options are his, and ADR-0048's; its assumption that one poll a day
  loses nothing has now failed on three runs.

**Records.** Neither decision has one.
- D14 departs from ADR-0007's recency-as-a-view for the display. The raw
  layer still keeps everything fetched.
- D13 is the location filter ADR-0001's Confirmation always described.
- Both are the architecture chat's to write.

**Verified for it**, at 2026-09-26T12:24Z: 652 tests on Python 3.12 and 3.11; the mutation runs for D13, D14, D11, the private store and the files the chain change touched still going at this commit, results in the next `[VERIFIED]`. The mutation runs that were still going at `6ef16eb` are among them.

## D14 corrected: age is judged once, at first sight

**The operator's correction, the same day:**
> "at the fetch or after the fetch it is checked that whether the posting is
> more than a week old meaning 7th day old post is also valid ... the logic is
> simple, the fetch will happen daily and i might not see the table for a few
> days then it would mean some posts will be out without my knowledge which i
> do not want."

**The seat had built it wrong.** `rule_age` measured the run's clock against
the publication date. Every projection and sweep re-applies the chain, so a
row admitted fresh would have aged out of `Jobs` a week later, unseen.

**Rebuilt:**
- the age is first seen minus published, at most 7 days, and a row once
  admitted gets the same answer however often it is re-judged;
- a posting first seen already older never enters, reposts carrying their
  original date included;
- a Lever posting is never dropped for age, since its date is unproven.

Tests pin the case he described: admitted fresh, then re-judged months
later, and kept.

**On today's `Jobs`**, re-applied `[VERIFIED]`:
- 17 of 86 unclassified rows stay, not 13.
- The two Joblogic roles MLOps Engineer and AI Evaluation Engineer, both
  published and first seen on 2026-09-17, now stay.
- 7 rows go for age alone. Each was already old at first contact: for
  example Joblogic's AI/ML Engineer, published 2026-07-15 and first seen
  2026-09-17.

**His question on reposts, measured on `data`** `[VERIFIED]`:
- 161 Greenhouse postings appeared after their board's first contact; 83 of
  them were already more than a week old at first sight.
- 60 of the 83 are one Speechify role, "Software Engineer, Platform",
  first published in 2024 and reposted city by city.
- Keeping the original date, which drops them, is what he suspected was
  right. Nothing changed.

**The other finding of the mutation run, closed.** "one closed place drops
a posting that lists an eligible one" survived: no test listed a closed
place and an eligible one on separate lines. One does now.

**Himalayas' search endpoint, re-measured for his question "is it not
possible that we trim it beforehand"** `[VERIFIED]`:
- With `country=Pakistan&sort=recent&page=N` it returned 59 distinct
  postings over three pages, all eligible under D13, 2,965 in total.
- The order is newest first after four pinned items at the top.
- Paging works through `page`. The 2026-09-16 measurement that rejected
  search passed it a `cursor`, which the API documents only for browse.
- About 92 eligible postings a day, about five pages a morning, against
  25 pages of everything today, which reach about a third of the feed.
- Switching reverses a measured decision and is his to approve.

## Himalayas moves to its search endpoint, filtered to Pakistan

**The operator's go:** "himalays search: go. also do provide the results with
explanation and your understanding."

**Built:**
- The adapter now asks `himalayas.app/jobs/api/search?country=<slug>&sort=recent&page=<n>`.
- The board's slug is the country, so the board reads `himalayas:pakistan`,
  still on the morning run only. Rows stored earlier keep
  `himalayas:browse`; they close by their expiry date, as he approved.
- Paging goes by page number, from the envelope's `offset`, `limit` and
  `totalCount`.
- **The stop rule reads the whole page.** Search pins old postings at the
  top of page one, one of them ten days old, and the browse rule of
  stopping at the first stored posting would have ended the walk there.
  A page stops it only when none of its postings is newer than the stored
  mark. A test gives it that pinned page.
- D13's location rule still runs on every row, as a second guard.
- **ADR-0031's fitness function caught the seat.** A drop reason naming
  the country in code was flagged by `tools/preference_audit.py`; the
  reason no longer names it.

**Live, a test-mode run with `--no-commit`, 13:31Z** `[VERIFIED]`:
- `himalayas:pakistan` fetched 497 postings and dropped none for
  location. The title and seniority rules kept 38.
- Browse, unfiltered, kept about 16 a morning, most of them then closed
  to Pakistan.
- It read to the 25-page cap only because this machine's test store holds
  no Himalayas history, so every posting was new. With production's
  history it stops after about two or three pages `[INFERRED]`, from
  about 92 eligible postings a day.

**The contract check will report one change.** The fingerprint now reads
`offset`, `limit` and `totalCount` where it read `nextCursor`. That is
expected, not a fault.

**Mutations** `[VERIFIED]`, every file whose code this round touched:
- D13 and D14, re-run against the first-sight age rule: 15 of 15, the one
  that survived the first pass among them;
- D11: 9 of 9;
- the private store: 12 of 12;
- the filter chain's older files (seniority and families, star and
  families, vendor file): 13, 7 and 4 of the same;
- the 10 older mutations re-expressed earlier: 10 of 10;
- D9 and G7: 6 of 6;
- the search change: 6 of 6, recorded at 2026-09-26T13:49Z after `da6fe0b`: the country filter, the whole-page stop against a pinned page, the last page, the page numbers and the board's configuration.

**Verified for it**, at 2026-09-26T13:35Z: 658 tests on Python 3.12 and 3.11.
