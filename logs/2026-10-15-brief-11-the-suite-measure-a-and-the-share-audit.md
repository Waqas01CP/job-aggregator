---
type: log
description: Brief 11 and its Addendum 1, with the urgent fix of 2026-10-10 that preceded it. The registry entries for ADR-0060 and ADR-0061, no run lost; Measure A met over its two weeks; Banyan Canopy's verdict, keep, back to the operator; why Jobs is mostly Himalayas, structural, with one starvation found and fixed by a breaker per platform; Manatal asked twenty a page; a graduate line opening the whole description; no source states years as a field; Himalayas' early removals measured; CAPABILITIES' rule, add or update, never remove, accepted.
status: current
---

# Brief 11: the suite, Measure A and the share audit, 2026-10-10 and 2026-10-15 UTC

Previous log: `2026-10-08-working-method-the-cassette-envelope-and-workable.md`.

| Header | Value |
|---|---|
| Date | 2026-10-10 from about 16:40Z, and 2026-10-15 from about 11:55Z, the same session |
| Model | claude-opus-5-5 |
| HEAD at start | `4f15464` on 2026-10-10, level with `origin/main`; `085a230` on 2026-10-15 |
| Mode | **Mutating.** Read-only reads of the private repository, the Airtable base through the connector, and live requests to every employer board, Manatal's ITC walked once, Himalayas' search walked once |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What was asked

2026-10-10, an urgent paste from the architecture chat: the operator had pushed ADR-0060 and ADR-0061 before `tests/confirmations.py` had entries for them, so the suite failed and both workflows' test step with it. Add the entries, push, and count the runs lost.

2026-10-14, the operator: is the earlier work complete, where is its summary, what is next; and how the aggregator has been doing, from the tables the resume chat had been working in.

2026-10-15, the operator: Brief 11 and its Addendum 1; whether they address the seat's flags of 2026-10-14; whether an earlier architecture brief waits to be sent; and whether any other brief for the seat sits in `briefs/`, anything stale said to him and the chat.

## Errors this seat made

- **A guessed stamp.** The first STATE line of 2026-10-15 carried 13:00Z at 12:13Z; the hook refused the commit and the stamp was corrected from `date -u`.
- **"Wrong when written" where it was stale.** `47f0b15` annotated Manatal's "twenty a page whatever `page_size` asks" as wrong when written on 2026-10-07. It was true when measured on 2026-10-04 and 10-07, and stale from the first run on 2026-10-08. Corrected in `a085eff` before anything was pushed.
- **A completeness check that read its own gap as the runs'.** The first live comparison took each board's read from seen entries carrying a `board_id`; 979 entries older than that field carry none, so Greenhouse and Lever looked short by up to 145 postings a board. Caught by Speechify matching while its neighbours did not, and redone through the raw layer before anything was reported.

## What was done

**2026-10-10, the suite** (`3961d4d`, `73d6a12`). ADR-0061's four Confirmation leads were already held by the tests of `2c38f6f` and `9a23387`. ADR-0060's five were held in part, and four tests close the rest: an empty upsert makes no request; a rule change, the family map, re-sends only the rows it moves; a row the rules now drop is not sent by the projection; a failed read of `Jobs` fails the projection. Each new test caught the mutation built for it, alone, through the harness. **No run was lost** [VERIFIED]: the records reached GitHub at 16:16:19Z and the fix at 16:50:16Z, from GitHub's push events, and no run was created in between; every run since has passed its test step.

**Brief 11, item 4: add or update, never remove, accepted.** Reasons in the report. `CAPABILITIES.md`'s upkeep section and the Working Method's template changed, with a Changes row in the template; one precision added: a re-measured number replaces its value in place, the old value kept only where the change is the point.

**Item 5: Measure A met** [VERIFIED]. 2026-09-24T03:27Z to 10-08T03:27Z: 140 admitted postings, median 7.3 hours from publication to first appearance, 90th percentile 22.0, against 24 and 72. Himalayas 137 of them, Greenhouse 1, Lever 2. Every posting seen in the window: 1,725, median 9.8, 90th percentile 21.4. First appearance is first sight, the run that wrote the row to the display; the one run in the window with a failure, 2026-09-27T03:59Z, failed only to save full postings and still wrote the display. 26 admitted postings published before their board's first run are excluded as backfill. None was dateless: Manatal's first run was 2026-10-08T19:11Z, after the window.

**Item 6 and the Addendum: Banyan Canopy, keep.** 56 runs from 2026-09-17 to 2026-10-15, 11 postings, none admitted, every one on the title rule [VERIFIED]. Its one AI-and-data role of 2026-09-11 would not pass the title pool, nor would a NetSuite or ERP developer [VERIFIED through `TitleMatcher`]. The verdict, keep, goes back to the operator; the board is still polled.

**Item 7: stale lines.** `STATE.md`'s Himalayas trial row moved to `completed.md`, settled 2026-10-10; Banyan Canopy's row carries the verdict. `docs/how-to/the-seats.md`'s recheck row names "The seats", and no longer says the chat's list lacks the fourth seat (`5d7295a`).

**The Addendum's audit: why `Jobs` is mostly Himalayas.** Structural [VERIFIED]. Of 1,416 postings first seen from 2026-10-08 evening to 2026-10-15 morning, today's rules admit 36: Himalayas 27 of 594, Manatal 9 of 696, Greenhouse 0 of 58, Lever 0 of 8, Workable 0 of 60; the title rule drops 92% of all. Workable's boards post marketing, design, support and warehouse roles. Every employer board's live postings were read once against the last run: Greenhouse, Lever, Workable and eight Manatal boards complete, give or take the hours between; ITC Worldwide's shifting pages leave about a quarter unread on any one walk, a delay rather than a loss, since the runs between them have read 438 of its 477. The backfill reports 0 every run, so no posting the rules admit today is missing from the stores. **One starvation found**: the run's one circuit breaker, which on 2026-10-14T03:47Z left six Workable boards unread after five Manatal 403s. Fixed in `82f131b`: one breaker per platform. The budget and the page cap cannot starve a source at today's volume.

**Manatal, twenty a page** (`47f0b15`, `a085eff`). The endpoint now serves ten unless asked and twenty at most; the default fell between 2026-10-07 and 10-08. Manatal cost 77 of each run's 98 requests; asking twenty halves it.

**The two description checks.** A fresh-graduate line on a different line from the years did not open the posting: the reader set aside only its own line. Over 4,748 saved descriptions no posting had that shape. Fixed in `fb4fdb7`: a description opening the role to graduates anywhere asks no minimum, and "freshers" and graduates welcomed open it too, 3 of 13 such postings missed until then; no saved verdict changes. **No source states years as a field** [VERIFIED over every saved payload]: Himalayas' `seniority` and Workable's `experience` are levels, Greenhouse has an education flag, Lever and Manatal nothing. Himalayas' own pages answer 403 to a non-browser client, so what a page shows beyond the API was not read.

**Himalayas postings removed before expiry** [VERIFIED, one live walk of the Pakistan search, 47 pages]. Of 381 stored postings published 2026-10-05 to 10-07, 123 had left the search eight to ten days later, every one before its expiry: all 87 of EWOR GmbH's, and 36 of the other 294, 12.2%. None of the 8 admitted from that band had left. Seeing it costs a walk as deep as the display's oldest row, about 4.7 search pages per day of depth.

## Not done

- **SmartRecruiters and Ashby.** SmartRecruiters needs a detail request per new posting for its description, a new phase in the run rather than an adapter alone; its two registry boards yielded 0 of 20 on 2026-10-04. Next, on the operator's word.
- **Item 3, the level rule:** held by Addendum 1 until the operator answers whether a stated level should drop a posting at all.
- **EWOR:** waiting on the operator; the counts above are what a decision would start from.

## Verification

- **Suite, 2026-10-10:** `3961d4d` alone in a scratch clone, 887 tests on Python 3.12 and 3.11.
- **Suite, 2026-10-15:** each commit alone in a scratch clone, `fb4fdb7` 890, `82f131b` 892, `47f0b15` 893 on Python 3.12, and 893 on 3.11 at `47f0b15`; the final tree on both before the push.
- **Mutations, 2026-10-10:** 4 of 4 caught in a scratch clone at `3961d4d`, with `--why`, each by its own test alone (`73d6a12`).
- **Mutations, 2026-10-15:** 9 of 9 caught in a scratch clone at `47f0b15`, with `--why`: the graduate opening's 2, the breaker's 3, Manatal's 1, and 3 re-expressed (the fresh-graduate mutation of 2026-10-02 and two of 2026-09-23 for the breaker's label argument). Run time about 80 minutes, below normal priority, announced before it started.
- **Live reads:** 26 employer boards one request each; ITC Worldwide walked once at twenty a page, 24 requests; Himalayas' Pakistan search walked once, 47 pages; SmartRecruiters' two boards and one detail for the next build; one Himalayas page, refused with 403. All with the pipeline's user agent, a second or more apart.
- **Privacy:** each staged diff scanned; no Airtable ID, token or aggregator URL, and no description text, the tests' sentences written to the measured shape.
- **Processes:** none of this seat's left running.

## Open

- The next fetch runs: Manatal at twenty a page, about 40 requests [INFERRED]; a breaker per platform.
- The operator: Banyan Canopy's verdict, item 145, EWOR, relaying the report.
- The architecture chat: the records the report lists.
