---
type: log
description: Brief 9 built and measured. Closure at twelve runs, re-baselines ordered by time, the clearing tool's private list moved out of the outcome stores, every Confirmation clause of ADR-0050 to ADR-0058 tied to a test or a reason, Himalayas' freshness and time zones as residence measured, and the seat's own country names found in code and removed.
status: current
---

# Brief 9: twelve runs, times, and every clause, 2026-10-03 UTC

Previous log: `2026-10-03-the-crash-the-morning-and-the-description.md`, the same day's earlier work, which this one follows.

| Header | Value |
|---|---|
| Date | 2026-10-03 UTC, from about 15:20Z. The operator relayed Brief 9 from the architecture chat |
| Model | claude-opus-5-5 |
| HEAD at start | `9aeb263`, level with `origin/main`: the chat's four record commits on top of `b2687b4` |
| Mode | **Mutating.** `data` cloned into the scratchpad at `0b6bb51`; the private repository's `data` and `data-test` branches listed, its seen store and full branch read, read-only |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What the brief asked

Eight items from the records the chat wrote on 2026-10-03, ADR-0057 and ADR-0058 new and thirteen amended. The records were read on disk first; the chat's figures this log relies on were checked: 57 records, 5 superseded, 141 Changes rows in 47 files counting ADR-RULES, and 253 location drops on the evening run of 2026-09-30, which polls no Himalayas [VERIFIED].

## 1. Closure at twelve runs [VERIFIED]

`config/sweep.json` now says 12. The loader refuses a run-log window shorter than the count, since the closure test counts runs in the logs it reads and a window of ten with a count of twelve would let nothing close, silently. Tests: the shipped count, at twelve hours a run, outlasts the longest absence measured, 130 hours; a posting closes on its twelfth polled run and not its eleventh.

**What four runs actually closed falsely: nothing, while it was in force.** Every sweep block on `data`, 2026-09-25 to 2026-10-03:
- `closed_marked` was 3 on 2026-09-25T20:10Z, the first sweep; 10 on 10-01 and 37 on 10-02; 0 on every other run.
- The 3 were Greenhouse rows last seen on 09-17 and 09-21, and none has been seen on its board since, through the run of 10-03T04:04Z: true closures. All three later left `Jobs` for a rule's drop.
- The 47 were the walk-reach defect on Himalayas, not the threshold, and cleared on 10-03 (`closed_cleared: 47`, the only non-zero clear).
- A false closure would have shown as a clear when its posting returned, and no employer-board row was ever cleared. The twelve returning postings of 2026-09-30 were measured across the boards, not in `Jobs`, and none was ever marked; whether any sat in the display is not known.

## 2. Himalayas' freshness under the morning-only poll [VERIFIED]

Publication to first seen, for postings published 2026-09-27T00:00Z to 2026-10-02T04:22Z, so every one had a full morning to appear. Public seen store from `data` at `0b6bb51`; Himalayas' from the private seen store.

| Source | Polled | Postings | Median | 90th percentile | Longest |
|---|---|---|---|---|---|
| Himalayas | each morning | 448 | 10.2 h | 22.2 h | 29.9 h |
| Greenhouse | twice a day | 32 | 4.6 h | 9.7 h | 13.6 h |
| Lever | twice a day | 16 | 8.5 h | 34.8 h | 53.2 h |

- Lever's date is `createdAt`, not proven to be publication (ADR-0052), so its figures include time before posting and are not comparable.
- **The search trails little.** 5 of the 448 were published before a morning walk that did not return them, a median of 1.5 h and at most 6.1 h before it.
- **With an evening walk** at the evening runs' actual times, 16:18Z to 20:02Z, the estimate is a median of 6.4 h, p90 12.1 h, longest 15.5 h, at the 97.7-minute trail measured earlier; 7.2 h and 12.8 h at a 4-hour trail [INFERRED: a simulation over the same postings].
- **Its cost** is the walk back to the morning's mark plus the agreement page: about 4 to 6 requests on days like 10-01 and 10-02, about 100 new postings, and up to about 17 on a day like 10-03's 559 [INFERRED from 17.7 postings a page].

## 3. Clearing a classified `Jobs` row [VERIFIED]

The code does what the operator decided. `clear_jobs` writes the row's outcome to its classification store with the reason from its copy and `removed_by: operator`, and deletes nothing. The sweep removes the row (step 2) and the rejection copy (step 3) only once origin holds that outcome. **No test held it**: the one test cleared the rejection table, not `Jobs`. One now clears a classified `Jobs` row and follows it out, with two mutations.

## 4. The dry run's list out of `outcomes/` [VERIFIED]

It is now `clearing/dry_runs.json` in the private repository, restored and pushed with the other aggregator files. Neither private branch held the old file, read on both, so nothing moves. A test runs a dry run naming an aggregator row and finds both outcome directories byte for byte unchanged, the list pushed under `clearing/` and restored to where the confirm reads it.

**Two more files sit in the private `outcomes/` and are not stores:** the agreement check's `agreement_pending.json` and `agreement_disagreements.json`. The chat's reasoning applies to them equally. Not moved, as outside the brief; neither branch holds either today.

## 5. Re-baselines carry a UTC time [VERIFIED]

An entry's `at` is the UTC time its change was committed to `main`, and a stored shape's `since` is the check's own time from its next change. The seven entries on file were re-timed from `git log`: 2026-09-26T13:35:27Z, 10-02T18:07:05Z, 10-02T20:36:10Z for two, 10-03T09:46:55Z for three. The test built to defeat dates is the gap of the morning: a shape accepted at 11:56Z and a change committed at 16:00Z the same day reads ours on the next check, and an entry committed at 09:46Z, before the acceptance, reads spent.

**The three stored shapes carry only their day, 2026-10-03,** and are read as that day's last second, which is the old rule. So the gap stays open for the rest of 2026-10-03 for them alone, and no adapter change is planned in it. Each gains its time on its next change.

**The one rule for the next entry:** push straight after committing. A check that records a change between the two leaves the entry older than the shape it must excuse.

## 6. Every Confirmation clause of ADR-0050 to ADR-0058 [VERIFIED]

`tests/confirmations.py` holds every clause by its bold lead. The meta-test in `tests/test_fitness.py` fails when:
- a record gains a clause nothing holds;
- a named test leaves the suite;
- an entry names a clause the record no longer has.

| | Clauses |
|---|---|
| Held by tests | 44, two of them only in part, below |
| Live or private data only, with the reason | 4 |
| Declared "Live only:" by the record | 2 |
| Unbuilt, ADR-0056's delta | 1 |

**Four clauses had no test, and now do:**
- ADR-0052's "No drop may be unlogged": the age reason names both dates;
- ADR-0053's "A posting browse already stored must not be new to search";
- ADR-0057's "The structured place must never keep a posting the text drops", whose closing half was tested and keeping half was not;
- ADR-0057's "ADR-0031's audit must still find no country named in code", below.

**Two clauses claim a guard that does not exist.** ADR-0051's "The public branch must be seen refusing description text, which is ADR-0011's and ADR-0020's existing commit guard", and the second sentence of ADR-0058's first clause. Nothing refuses description text in a commit to the public branch. The row's shape keeps it out, having no field for it, and the commit hook guards `main` against unsanitised cassettes only. `CAPABILITIES.md` said the code "refuses to commit a file holding either"; corrected.

**Live, with the reason, for the chat to mark in its records:**
- ADR-0053's snapshot series and pages per morning: properties of the live feed.
- ADR-0056's week: due 2026-10-05.
- ADR-0057's corpus check of 74 and 17: its 91 postings are aggregator content, which ADR-0020 keeps out of this repository, so it runs by hand against the private copy.

## A mistake of mine: country names in code [VERIFIED]

ADR-0031's audit read pool terms, seniority words, vendors, families and employers, and no place. Extended to the configured places, it found seven hits, all in `src/description.py`, written by this seat on the night of 2026-10-02:
- the citizen pattern named nine countries and nationalities;
- the step that drops the dots from initials named the United States and the United Kingdom.

ADR-0057 and ADR-0031 keep every place in configuration.
- **Fixed:** initials lose their dots generically; the citizen pattern takes the word before "citizen" and its kind, and the one before that when capitalised, and the configuration decides whether they name a place.
- **Measured over all 2,271 saved postings:** the configured places derived are identical before and after, 28 postings each, no difference. Four of the old names, British, American, Canadian and Australian, named no configured place, so they had decided nothing.
- **Found on the way and fixed:** "non-US citizens" read as a US requirement, which would drop a job open to him. In no saved description.
- **The audit now reads 366 values**, places among them, and a planted country is a test.

## 7. Time zones as residence [VERIFIED]

Over the 2,271 postings on the private full branch, 837 Greenhouse, 66 Lever and 1,368 Himalayas, each line naming a time zone was classified, and every line the classifier called residence (39) or other (59) was read.
- **211 postings name a time zone:** 50, 7 and 154.
- **14 state one as a residence requirement that excludes Pakistan,** 6 Greenhouse and 8 Himalayas, and up to 4 more among the lines the classifier missed, all Himalayas. 7 to 9 more state it as a preference, and a few include Pakistan or cannot be read either way, such as a bare "time zone" label beside a zone's name.
- **The phrasings, described:**
  - one or two named US time zones as where the candidate must live;
  - a band of UTC offsets around central Europe, within which the candidate must live or work;
  - a region's time zones, such as Europe's, the Americas' with EMEA's, or part of Africa's;
  - residence defined by a working day overlapping US Pacific hours by six.
- **Every one of them is in a posting the current rules already drop,** most on the title.
- **Of the 57 postings the rules keep,** age aside, 3 name a time zone, all about working hours, two of them located in Pakistan.

On today's corpus no posting he would see turns on it.

## Verification

Mutations ran in scratch clones identical to the tree in `src`, `tests`, `tools`, `config` and `.github`, one suite at a time at below-normal priority.
- **The first batch: 18 of 18 caught.** It held 11 new mutations for the closure count, the times, the clearing list and the classified row, and 7 re-expressed because their text moved. Two of the 7 were relabelled with the change from dates to times: "an entry timed after the check excuses a change" and "any twenty characters pass as a time". The batch ran without `--why`, so which test caught each is not recorded.
- **The second batch: 9 of 9 caught, each by the test built for it**, run with `--why` on a fresh clone of the final tree. It held 7 new mutations, for the audit's places, the non- prefix, the citizen pattern's capitalised word, the clause registry, the age reason, the structured place and the browse identity, and 2 description mutations re-expressed. The identity mutation is also caught by about 25 other tests.
- **Suite:** 811 tests pass on Python 3.12, and on 3.11 under `-W error::ResourceWarning`. A run prints no workflow command.
- **Stale finds:** 0 of 458.
- **Privacy, over the outgoing diff:** no Airtable identifier, token, email address, aggregator identity or URL, and none of the description lines read this session.

## Evening: the operator's three answers, about 17:30Z [VERIFIED]

His words: "you can do it to himalayas if justified"; "what is this morning's proposal?"; "yes, build the missing guard". And: make sure the brief to the chat is complete, with addenda for any work done since.

**Himalayas now polled on both runs.**
- **Judged justified:**
  - it halves the wait measured in item 2, to about Greenhouse's;
  - it costs about 4 to 6 fetch requests an evening on an ordinary day, against the 7 to 8 a morning walk spends on a whole day, and about 16 on a day like 10-03's;
  - it adds no Airtable call, since the evening run already sends the whole display, 84 and 92 rows on 10-01 and 10-02;
  - it is the same walk the morning runs.
- **ADR-0048's reason, a once-a-day cache, is false for the search,** item 2's postings having been seen as little as 0.3 hours after publication.
- **What changed:**
  - `config/boards.json` names both slots;
  - the agreement check's twelve-hour wait now usually settles at the next run, the search having trailed at most 6.1 hours;
  - the skip itself stays configuration, still tested with a morning-only board.
- **First live:** the evening run of 2026-10-04. The evening run of 2026-10-03 came at 17:04Z, before this push, and skipped Himalayas [VERIFIED from `data` at `40a38bf`]. That run was the description rules' first live one: of 565 postings read, none new, the experience rule dropped 9, authorisation 2 and location 12, with 11 requests and no failure.

**The description guard built.** `storage.commit_files`, the one function every commit to the public branch goes through, now refuses the whole commit, before git is touched, when a file holds:
- a description field holding text, anywhere: `content`, `description` and the other spellings the adapters meet;
- in a record file, markup or a string over 1,000 characters.

The public branch holds none of these today: the longest string in a record file is 135 characters, a location, and the longest anywhere 308, a failure message in a run log. Run logs are spared the markup and length rules, since failure text may carry either, and never the field rule. The refusal names the file, the field and the record, never the text. The contract check's fingerprint names the same fields holding only shapes, and passes. ADR-0051's and ADR-0058's clauses are now true, and the clause registry holds them by the new tests.

**The agreement check's two files moved** to the private store's `agreement/`, out of `outcomes/`, on the chat's own reasoning for the clearing list; neither branch held them.

**The morning's proposal, then built on his yes, about 17:40Z:** a dry run says how many of the rows it lists leave on a later run without the tool. The tool runs after the sweep, so such a row is:
- one this run's sweep has just stored for removal under a rule's reason, read from the removal store by this run's time;
- one kept out for good by an earlier removal;
- a classified row whose outcome is stored;
- on `accepted`, a copy whose `Delete` is set.

Its summary line reads, for his dry run of 10-02, "would remove 19 ..., 17 of them already on their way out without it". Offline only; his next dry run is the first live one.

**Verification, the evening:**
- **The third batch: 10 of 10 caught, each by the test built for it,** with `--why` on a fresh clone. It held the guard's six, the agreement files' two, the Himalayas cadence, and the clearing list's mutation re-expressed for the rewrapped directory list. The mutation refusing a description field that holds a shape is also caught by the contract check's own end-to-end tests, which shows the guard sits in that check's path too.
- **The fourth batch, first attempt: refused at its baseline, a slip of the seat's.** The dry-run count moved the text under an older mutation, "a dry run writes the stores", and the seat had run only the clearing tests before starting the batch, not the suite's stale-find check. Nothing was applied, so no result was wrong; it cost one baseline suite. Re-expressed in the same commit as the count, and rerun with it, six mutations.
- **The fourth batch, rerun: 6 of 6 caught, each by the test built for it.** Five for the count, for each way a row can be leaving anyway, and the re-expressed one, caught by the dry run's own fitness function among others.
- **Stale finds:** 0 of 472.
- **The commits:** five, at his request, each holding its own code, tests, mutations and document lines: the evening poll, the guard, the agreement files, the dry run's count, and this record. Each was checked out alone in a scratch clone and its suite run before the push. They passed with 811, 814, 814, 816 and 816 tests.
- **A second slip of the seat's, caught before the push:** the script that split the work into commits first built each commit's mutation file from the moving `HEAD`, not from the commit the evening started from. The mutation file landed in the wrong commits: the guard's commit carried a mutation whose code arrives only with the agreement move, and that commit carried the dry run's five. A count of each commit's mutations showed it before any suite ran. The five local commits were undone, the script fixed to a fixed base, every mutation's text checked against every commit's files, none stale, and the commits made again.

**His other answers:** OneDrive, VMware and Docker Desktop are done, his side. He asked for the work committed in separate commits, each with its own message.

## Open

- **The seat's:**
  - 2026-10-04 morning: the description rules' first live drops;
  - 2026-10-05: ADR-0056's clean week.
  - 2026-10-04 evening: the first evening walk's requests, pages and new postings.
- **The architecture chat's,** through the brief and its Addendum 1:
  - the live clauses to mark;
  - ADR-0048's cadence, now both runs;
  - the guard and the agreement files, recorded as built.
- **His:**
  - the dry-run proposal of this morning;
  - sending the brief.
