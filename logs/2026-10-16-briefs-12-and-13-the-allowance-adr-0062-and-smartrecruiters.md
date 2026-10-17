---
type: log
description: Briefs 12 and 13. The Airtable allowance measured and given a ceiling of 900; ADR-0062's flow built (applied, gone, Reason, Jobs No.); stored facts re-read when the code that derives them changes; Himalayas' morning walk to the age limit; the Senior change built and switched off for November 1, the level rule as a list of the levels that drop, Workable's level read, the description fields and No description; SmartRecruiters built; the mutation harness given a time limit after it stalled.
status: current
---

# Briefs 12 and 13: the allowance, ADR-0062 and SmartRecruiters, 2026-10-16 to 2026-10-17 UTC

Previous log: `2026-10-15-brief-11-the-suite-measure-a-and-the-share-audit.md`.

| Header | Value |
|---|---|
| Date | 2026-10-16 from about 03:30Z to 2026-10-17 about 20:30Z, the same session as Brief 11's |
| Model | claude-opus-5-5 |
| HEAD at start | `0792441` on 2026-10-16, level with `origin/main` |
| HEAD at end | `65061c9` pushed, and this commit |
| Mode | **Mutating.** Read-only reads of the private repository's `data` and full branches from scratch clones, deleted after; `data` from scratch clones; the Airtable base through the connector, fourteen field creations on the operator's word; live requests to Himalayas' search, SmartRecruiters' two boards and one SmartRecruiters job page |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What was asked

2026-10-16, Brief 12 and its Addendum 1: the Airtable allowance first; the Senior change counted and held; a design for `gone`, `applied` and a reason field; a week of EWOR; the resume chat's questions C1 to C5; stale lines.

2026-10-16, Brief 13, with the operator's word: "what you will do next must be done with the brief"; Senior first if it is to be done now, then SmartRecruiters. Item 0, ADR-0062's registry entries and a push; item 1, build ADR-0062; item 2, re-read stored facts; item 3, Senior, switched on 2026-11-01; item 4, the morning walk to the age limit; item 5, the allowance and a connector test; item 6, EWOR's walks; item 7, SmartRecruiters.

2026-10-16 night and 2026-10-17, the operator: make the Airtable fields of Step A and test the connector; what the deliberate code breakages are; "you can do the next work if it is not gatekept"; trust SmartRecruiters' `releasedDate` (his answer to the seat's question); stop the mutation batch rather than keep the laptop on for hours; make the four description fields now; run the rest of the mutations in batches he can follow.

## Errors this seat made

- **A push did not wait on its privacy scan.** `ba4195f`'s scan and push were chained with `;`. The scan's 9 hits, read straight after, were the tests' FAKE placeholders. Every push since read its scan first.
- **Four mutation files named by the local date,** 2026-10-17 where UTC was 10-16. Renamed in `55247be`.
- **A commit swept in a file that was not its own,** through a folder pathspec. Undone locally at once and redone; nothing was pushed in between.
- **A heredoc carried backslashes,** against the operator's standing rule; an assertion stopped it before any file was written. **An Edit wrote backslashes before docstring quotes;** compiling caught it before any test ran.
- **"The harness hung" was first called sleep alone.** The first stall began two minutes before the laptop slept (22:09Z to 07:22Z); the seat stopped it after the wake and, the harness holding its output to the end, lost 18 finished results. The second stall came with the laptop awake. See "Verification".
- **The milestone report of 2026-10-16 went stale in six places before it was sent;** it was replaced whole.
- **Two figures in the report's first draft were wrong:** October's end "near 890" (near 915 by the same arithmetic) and Workable as the fifth platform with a re-baseline entry (the fourth). Corrected before the operator saw them.

## What was done

**Brief 12, the allowance** [VERIFIED from the run logs]. The pipeline spent 442 calls in October to 2026-10-16T03:25Z, 399 production and 43 test; a production day costs mean 19.1, median 17, at most 28, the sweep now the largest share. The operator's 563 on 10-15 left 131 to 142 calls that were not the pipeline's: this seat's connector calls (at least 27 requests in October), the resume chat's (at least about 45 from 10-13), and unknowns. Airtable's help centre, read 10-16: third-party tools connecting through his account count; the limit resets on the first of each month; one 30-day grace, then 429s.

**Brief 12, the rest.** Senior counted: about 15 more rows a week, all Himalayas; the backfill would add 130 at once, 41 of them only on stale facts, so held. The statuses and fields designed. EWOR walked: it relists rather than removes, 64 of its 87 "gone" back under the same identity; 35 postings reached the search after their walk had passed, none passing the rules. The resume chat's C1 to C5 answered, C2 (Spreetail) kept by the rule that stored rows keep their verdict. ADR-0032's order case replaced by one that survives `senior` leaving the list (`4316e06`); Banyan Canopy's STATE row moved to `completed.md` (`b2fe987`).

**Item 0** (`6c94c72`): ADR-0062's registry entries, eleven carried leads and six new ones, pushed with the operator's record commit `fbc5ac2`.

**Item 1, ADR-0062.** The ceiling, 900, `monthly_call_ceiling` in `config/sweep.json`, in every client the run builds (`ba4195f`). The flow (`44e7113`): `applied` makes or raises the `accepted` copy with `Stage` applied, never lowering one; `gone` is written to `gone.json`, the projection's skip reads it whole, and its `Jobs` row leaves the morning after origin holds the record; `Reason` reaches a new rejection copy when the field offers it and fills an empty one, never overwriting; an accepted copy carries `Jobs No.`. The seat made `Reason`, `No.` and `Jobs No.` through the connector on the operator's word; he added the `Status` and `Stage` options. The first morning under it, 2026-10-17T03:15Z, swept with no failure, 5 calls [VERIFIED].

**Item 2, the re-read** (`5cb797d`). `facts.json`, an overlay of re-read derived facts by identity, split by source class; a fingerprint over the files that derive them decides when; the backfill, the projection and the sweep judge stored rows on it. First run 2026-10-17T16:12Z: 4,945 saved postings read, none unknown or unparseable [VERIFIED].

**Item 4, the morning walk** (`6cbf5e6`): `deep_slots` in `config/boards.json`; the morning run walks Himalayas' search to the age limit.

**Item 3, Senior, built and off.** The level rule names the levels that drop, Senior, Manager, Director, Executive; Workable's `experience` read, re-baselined at 2026-10-17T08:04:49Z, changing no verdict over its 47 stored postings (`40a54b2`). A row records whether its posting carried description text, `described` (the ADR-0011 shape guard refused the first name, `no_description`); the run log counts `kept_without_description`; the four description fields built behind `description_fields_shown`, off, the read-back reading a false checkbox as empty (`a363ed5`). Of 4,902 saved postings, 3 carry no description, all Manatal [VERIFIED]. The four fields were made in `Jobs` and `Jobs test` on 2026-10-17 at about 19:55Z, on the operator's word.

**Item 7, SmartRecruiters** (`effb049`). OneScreen and SeekaTechnology. A detail phase in the run, ADR-0028's once-ever detail, its Confirmation now a test; a posting read from the list after its first sight has a link built from company and id and its description recorded as not read. `releasedDate` trusted as the publication date, the operator's decision of 2026-10-17, after it did not move on nine postings read on 09-16 and 10-17. The contract check fingerprints the detail; its per-platform budget is 3. First run 2026-10-17T16:12Z: 20 postings, 20 details, none failed, none kept [VERIFIED].

**The harness** (`65061c9`): each suite twenty minutes; a stopped one reported timed out, never caught, naming the test that was running; the whole process tree killed, since the venv's interpreter is a launcher.

**The connector and the meter.** The seat's six creations on 2026-10-16 at 20:32:55 to 20:33:04Z did not move the operator's 617 over 33 minutes; he read 647 on 10-17 at about 10:00Z, 22 more than the pipeline's 8 between, and 647 again at 19:50Z, after the evening run's 6. The meter is not live; the operator reads it as refreshing about once a day.

## Not done

- **62 of the round's 73 mutations not yet run.** 11 are proven, all caught; the rest run in four batches from 2026-10-17T19:53Z, the operator's request.
- **Item 5's connector test:** whether a connector call counts is still open; the meter's lag hides it.
- **Item 6, EWOR's walks,** about 2026-10-19 and 10-23.
- **Ashby,** next on ADR-0059's order.

## Verification

- **Suites,** each commit alone in a scratch clone on Python 3.12 and 3.11: `ba4195f` 897, `44e7113` 912, `6cbf5e6` 914, `5cb797d` and `55247be` 926, `40a54b2` 928, `a363ed5` 938, `effb049` 955, `65061c9` 957.
- **Mutations:** 11 of 73 caught. Four at `a363ed5` by the harness, and "a gone row is deleted before origin holds its record" in a run of its own after the harness stalled on it (163 seconds, caught by four `TestGone` tests); six at `65061c9`. The rest in "Not done".
- **The stalls.** 2026-10-16 from 22:07Z: the suite under "clearing Jobs passes over a classified row" was idle when the seat looked at 07:23Z; the laptop had slept 22:09Z to 07:22Z (Kernel-Power 42, Power-Troubleshooter 1); the same mutation's suite run in-process finished in 214 seconds, caught. 2026-10-17 from 09:53Z: the suite under the gone mutation sat idle over twenty minutes, no CPU and no child, with no sleep event. Cause untested.
- **Live reads:** Himalayas' Pakistan search walked once on 2026-10-16, 51 pages; SmartRecruiters' two lists and two details, and one job page, on 2026-10-17.
- **Privacy:** every push's diff scanned for Airtable IDs, tokens and aggregator URLs, the scan proven on a planted ID first; cassettes read whole before commit; the private full-branch clone deleted after measuring.
- **Processes:** none of this seat's left running at each stop, checked by process listing.

## Open

- The morning run of 2026-10-18 at about 03:15Z: the first walk to the age limit, and the daily sweep's removal of the rows the re-read now drops, about 18 [INFERRED from the measurement of 2026-10-16].
- The operator: the meter, read once a day at a set time; relaying the report on Brief 13 once he judges the work done.
- The architecture chat: the operator's `releasedDate` decision in ADR-0059's Changes; ADR-0053's Confirmation clause; ADR-0032's switch-on steps.
- 2026-11-01: the Senior switch and `description_fields_shown` on, in one commit.
