---
type: log
description: Brief 8. The projection's skip reads the removal store by reason; ADR-0055's thirty-day clock and the operator's clearing tool; ADR-0053's agreement check and ADR-0036's re-baseline; ADR-0041's owed check met; a week of intake measured against ADR-0056's trigger; the repost research; and the Himalayas walk checked complete against the private store.
status: current
---

# Brief 8: the display's clock, the clearing tool, and four checks, 2026-09-30 UTC

Previous log: `2026-09-27-the-full-branch-fix-and-capabilities.md`.

| Header | Value |
|---|---|
| Date | 2026-09-30 UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `aade660`, level with `origin/main`; the architecture chat's records committed by the operator as `fecbf7b` to `fe33d93` |
| Mode | **Mutating.** Himalayas read for one probe of five pages and one week-long snapshot of 26 pages; the private repository read through its token, read-only; nothing written to Airtable |
| Tests | 666 at start, 702 at end, on Python 3.12 and 3.11 |
| Verification | 28 of 28 mutations caught, in a scratch clone at `19ca94d` |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## Before building

**The operator's words:** "if there are things to be build and it is also said in brief 8 then do them", and the audit after the building, briefed by this seat as always.

**Brief 8 read against its records.** All twelve are on disk and committed `[VERIFIED]`. ADR-0050 carries four Changes rows, under its own threshold of six, and nothing built here adds a fifth. The architecture brief of 2026-09-25 to 09-27 was read end to end and ticked executed, 2026-09-28: every question and record request in its parts 1 to 7 is answered by Brief 8 and the records. Part 8, the review of `CAPABILITIES.md`, waits on the chat by the operator's arrangement.

## Item 10: two answers

**The morning save of 2026-09-28 succeeded** `[VERIFIED]` from its run log on `data`. All 599 postings it fetched were saved in full, read back and verified. That includes the 460 the morning of 09-27 could not save, reached again by the recovery walk. Every save since has verified too: 13, 3, 9 and 18.

**"First-contact runs" counts runs in which every posting a source returned was new** (`tools/run_log_report.py`, line 209). Himalayas' 16 are the runs of 2026-09-17 to the morning of 2026-09-25 `[VERIFIED]`. Before the private store existed, every Himalayas row was discarded with the runner, so each run met the feed as if for the first time. None has happened since, so the per-board mark is advancing and the walk lengths have no second explanation.

**The 81 held rows of 2026-09-27 and the 44 stored on 09-28.** `held_private_unavailable` counts every unclassified Himalayas row in `Jobs` the sweep could not judge that morning, one each, in steps 4 to 6 `[VERIFIED]` from `src/sweep.py`. It does not count rows due for removal. The next morning judged them and stored the 44 the rules drop `[INFERRED]`, since the count per step is not logged. The other 37 were rows the rules keep.

## Item 1: the reason-based skip

The projection's skip now reads `outcomes/removed_unreviewed.json` by reason, public and private, and a row's latest record decides.

**Returns:**
- a rule's drop, `dropped by the <rule> rule`, once the rule admits the row again;
- `no longer its group's display row`.

**Stays out:**
- `closed`;
- `unreviewed-aged-out`;
- `operator-removed`;
- any reason added later.

**Two decisions of the seat's, inside the brief:**
- **The regrouped reason returns.** Step 6 stores a member that stopped being its group's display row. The group is live under its new representative, so reading that record as a judgement would hide an unreviewed role. ADR-0043's principle is "the reason it left was the rules", and the grouping follows the rules.
- **The store keeps one record per row and reason, not one per row.** Otherwise a row a rule dropped, which returned when the rule widened and later closed or aged out, would be deleted against its old record without its new reason being written. The projection, reading the old rule reason, would then send it back every run. The sweep now writes the new reason first and deletes only once origin holds it. Records written before today, which lack the new key, are read by identity and reason alike.

**Until today the store was not read at all** `[VERIFIED]`: `tests/test_projection.py` pinned "the fourth store is not read". That test is replaced by the six that prove the principle both ways.

## Item 2: the exclusivity invariant

**Nothing asserted it** `[VERIFIED]`, by a search of `src/`, `tests/` and `tools/` for any intersection of stores. The only guard was the sweep's routing, `classified_elsewhere`, which already consults the three corpora alone. So nothing had been passing only because `removed_copies.json` was empty.

ADR-0043's Confirmation, the pairwise intersection, is now built as `Stores.exclusivity_violations`. It covers the three corpora only, and every daily sweep runs it and reports a violation as a problem. The test holds an `accepted` copy in `accepted.json` and in `removed_copies.json` beside a `closed` removal, which is correct, then puts one identity in two corpora, which is not.

## Item 3: ADR-0055, the clock and the tool

**The clock:**
- **When:** an unreviewed row leaves thirty days after `First seen`, the display row's own or the stored row's. The number is `unreviewed_after_days` in `config/sweep.json`.
- **How:** it is stored with `unreviewed-aged-out` and deleted on a later run, on ADR-0050's path.
- **What it never touches:** a classified row.

**The tool:**
- **Where it runs:** `src/clearing.py`, from the fetch workflow's dispatch. Three new inputs: a table, a number of days, and a box to confirm. The inputs reach the run as environment values, never into the step's script.
- **What it measures:** `jobs` measures `Published`; the three classification tables measure `Classified`, the copy's created time.
- **An unconfirmed run is the dry run.** It reports how many rows, the oldest and newest publication dates, and how many are unreviewed. It lists every row, and writes nothing.
- **A confirmed run needs a recent dry run.** It is refused unless a dry run of the same table and days is in this branch's run logs within `clearing_dry_run_valid_hours`, 48. That is the seat's number, in configuration, and makes "a dry run always comes first" a property rather than an instruction.
- **What a confirmed run writes:**
  - an unreviewed row: stored `operator-removed`;
  - a classified row or a rejection copy: its classification saved in its corpus, marked `removed_by: operator`, which lets the sweep delete it before fifteen days;
  - `accepted`: `Delete` set, and nothing else.
- **What it never does:** delete. The next daily sweep deletes once origin holds the record. The sweep's snapshot of origin is taken before the tool runs, so nothing is deleted in the run that wrote it.
- **Removals are named in the run log** by identity, an aggregator's masked there since the log is public. The private removal store names it.
- **What `accepted` gains:** a narrow `mark_delete`, under its own `TOOL_WRITES`. ADR-0035's fitness function is scoped to the pipeline's writers and says so; it now also holds the tool to writing only the operator's fields.

**Live, not yet:** the tool in test mode and the clock's first removal wait on the push and a dispatch.

## Item 4: ADR-0056's week, and the build it does not authorise

From the run logs on `data` at `c5b29a6` `[VERIFIED]`:

| Morning | New public rows | New aggregator rows | Display groups | Projection calls | Month to date |
|---|---|---|---|---|---|
| 2026-09-24 | 0 | 15 | 44 | 5 | not yet logged |
| 2026-09-25 | 0 | 25 | 52 | 6 | not yet logged |
| 2026-09-26 | 0 | 16 | 86 | 9 | 86 |
| 2026-09-27 | 0 | 26 | 43 | 5 | 100 |
| 2026-09-28 | 0 | 30 | 73 | 8 | 123 |
| 2026-09-29 | 1 | 0 | 74 | 8 | 151 |
| 2026-09-30 | 0 | 1 | 75 | 8 | 172 |

The evening runs of the week added one public row, on 2026-09-25. Before 2026-09-27 Himalayas was read through browse and the location and age rules did not exist; 09-27 was the first search morning and 09-28 its recovery walk.

**Steady intake is about one new display group a day** under the current rules:
- 1 public row on 2026-09-29 and 1 aggregator row on 09-30;
- the 30 of 09-28 were the one-off recovery walk.

At ADR-0055's thirty days that settles near 30 rows, against the trigger of 100 `[INFERRED]` as arithmetic. **So the delta projection is not built.** A projection costs 8 calls, and the month stood at 172 on 09-30.

**This cannot be reconciled with the brief's five to ten groups a day, and the brief makes that disagreement the finding.** The feed itself is thin now. The week-long snapshot of 16:32Z held 14 postings published in the preceding day and 10 in the day before, against 191 published on 09-27 and 95 on 09-25. So the volume is bursty, and a week containing a burst would read differently.

A clean week under the current rules completes on 2026-10-05, and the seat reports it then.

## The Himalayas walk is complete, checked against the private store

On 2026-09-30 at 16:32Z the seat read the Pakistan search back past a week, 26 pages and 512 postings. It compared them with the private seen store, read through its token `[VERIFIED]`:
- **Nothing is missing.** Of the 420 snapshot postings published in the week before the 04:17Z walk, the pipeline had stored all 420.
- **The search is not a daily snapshot.** It held a posting from 14:00Z at 16:32Z, so ADR-0053's assumption, measured once, is false.
- **Its order is by date with inversions**, 16 in 512. Postings published after the 09-29 walk sat as deep as page 19.
- **Why the walk still misses nothing:** the walk stops only on a page wholly at or before the stored mark, and the mark is set only by postings saved in full.

**The seat had raised a possible loss from the 09-28 walk's 234 new postings.** This check answers it for the week the snapshot covered. Whether the 234 were postings dated inside the week but added to the search late, or old postings whose date was refreshed, is not settled. A second snapshot would tell them apart; it is not needed for the question of loss.

## Item 5: ADR-0053's agreement check

One browse page each morning, one request, read in the Himalayas poll.

**How it decides:**
- **Excluded by the search:** a browse posting is counted as excluded only when neither this walk nor any earlier one returned it. The seen store records what the search board stored.
- **Why not a window over the pages read:** the search pins four old postings and inverts its order in places, so such a window would call a posting on an unread page excluded.
- **What is compared:** only postings no newer than the search's newest, since the two endpoints need not refresh together.
- **A disagreement:** an excluded posting ADR-0041's rule would admit.

**Where it reports:**
- counts in the board's line of the public run log;
- postings in disagreement to `agreement_disagreements.json` in the private store, with a workflow warning.

**Seen disagreeing** in its fitness test: an open posting the search never returned.

## Item 6: ADR-0041's owed check

On the saved corpus, the eight Himalayas responses in `raw_responses/`, 91 unique postings `[VERIFIED]`:
- **The prediction holds exactly:** 74 drop and 17 are admitted, as predicted on 2026-09-17.
- **The truncation changes nothing here:** with every list cut at three, as the adapter used to, the counts are the same and no verdict changes. None of the 91 lists names Pakistan, and 17 are empty.
- **What each drop names:** the rule and every place listed. It names neither the field nor the country. The Confirmation asks for both, and the second is kept out of code by ADR-0031's preference audit. For the chat.

## Item 7: ADR-0036's deliberate re-baseline

**The file:** `config/contract_rebaselines.json` records each change we cause: platform, date, cause, and the fingerprint fields it moves. Its first entry is ADR-0053's move to search, dated 2026-09-26, naming the four fields the check of 2026-09-27 reported `[VERIFIED]` from that log.

**How a difference reads:**
- matching an entry newer than the shape it replaces: marked ours with the date and cause, and the platform reads `re-baselined`;
- anything else: still `changed`.

**No old entry can excuse a later change:** each stored shape now carries the date it was accepted.

## Item 8: the repost research, three measurements, no rule

**(a) One employer and title under more than one publication date**, over the public raw layer `[VERIFIED]`:
- 57 of 560 pairs, holding 459 postings.
- **Span from first to last date:** 1 to 469 days, median 48.
- **By span:** 23 under 30 days, 22 from 30 to 180, 11 from 180 to 365, and 1 over a year.
- **Largest:** Speechify's "Software Engineer, Platform", 301 postings under 2024-01-24 and 2025-05-07.

**(b) Requisitions against `updated_at`, from the full postings of ADR-0051**, the first use of D11's data `[VERIFIED]`:
- 799 Greenhouse postings; 3 have no `requisition_id`, and 476 requisitions remain.
- **Shared:** 53 requisitions are carried by more than one posting, 373 postings in all, and 27 of those carry more than one `first_published` date.
- **Kept warm:** from `first_published` to `updated_at` the median is 70 days and the 90th percentile 964. 303 postings published more than 180 days ago were updated within the last 30.
- **The brief's example:** Speechify's role sits under two requisitions, one per publication date. By the brief's own test that is two hiring events, each kept warm for a long time, not one posting relisted.

**(c) Postings that disappeared from a board and returned**, from 28 commits of `seen.json` on `data` `[VERIFIED]`:
- 12 identities, all Greenhouse;
- absent 23 to 130 hours, median 59.

## Item 9: fitness functions

Each names its record and clause, and each is proved by a mutation in `tools/mutations/2026-09-30-brief-8.json`:
- the reason-based skip, both ways (ADR-0043);
- the exclusivity check scoped to three stores (ADR-0043);
- the age boundary to the second, and a week later (ADR-0052). Its mutation is the seat's own first build, judging against the run's clock;
- a dry run changes nothing, the confirmation is required, a removed row does not come back, and `accepted` survives the tool (ADR-0055);
- `queue: max` on both workflows (ADR-0054), each workflow proved by its own mutation;
- the agreement check seen disagreeing (ADR-0053);
- the re-baseline (ADR-0036).

## Stale documents brought current

- **`docs/reference/retention.md`** gains the clock, the tool, and the skip by reason. It had said the removal store is not read.
- **`README.md`** says how to clear a table.
- **`docs/reference/airtable-schema.md`** names the tool as the second writer of `Delete`.
- **`STATE.md`** moves two finished Blocked rows to `completed.md` verbatim: the private store storing Himalayas' rows, done since 09-25, and saving every field, done since 09-28.

## Not done

**Live, after the push:**
- the tool in test mode, with the production tables' counts equal before and after;
- the clock's first removal, read back from its store before the row leaves.

**Not in Brief 8:** ADR-0053's other Confirmation items, a week of the snapshot read on both runs and of pages per morning. The first needs an evening read of the search, which ADR-0048's morning-only rule does not make, so it is for the chat.

## After the report: the operator's answers, 2026-09-30T18:06Z

- **The `To review` view.** He added `Closed is empty` to its filter, and confirms it
  shows the most recent posting first: the two tasks Brief 8 gave him, done.
- **The order changes.** "after the brief 8 execution, what comes is the audit ...
  unless there is a reason to not do the audit then i propose, the audit is done
  first". There is no reason not to, and one for it: the report to the chat would
  otherwise carry any error the audit finds. So the fourth audit runs next, and the
  Brief 8 report waits in `briefs/architecture.md` for its findings.
- **Each seat decides what belongs to its perspective.** Sorted on that rule:
  - **the chat's:** the two records that conflict (ADR-0041 against ADR-0031), and
    the record corrections for ADR-0053, ADR-0056 and the index;
  - **the seat's, for information:** the regrouped reason, the removal store's key,
    masking in the public log, and the agreement check's test by identity;
  - **the operator's:** how long a dry run of the clearing tool stays valid, since
    it is a preference about his own working pattern.
