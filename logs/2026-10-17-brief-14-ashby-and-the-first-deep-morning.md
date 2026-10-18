---
type: log
description: Brief 14. ADR-0053's new clause held by its tests and pushed with the operator's records; Ashby built from a live read of its two boards, a republished posting keeping its first date through the stores; a stale CAPABILITIES line fixed; the first morning that walked Himalayas to the age limit and Ashby's first run read; the claim that the re-read's drops would leave Jobs found wrong; mutation batches 1 and 2, 34 caught of 34.
status: current
---

# Brief 14: Ashby and the first deep morning, 2026-10-17 to 2026-10-18 UTC

Previous log: `2026-10-16-briefs-12-and-13-the-allowance-adr-0062-and-smartrecruiters.md`.

| Header | Value |
|---|---|
| Date | 2026-10-17 from about 20:55Z to 2026-10-18 about 09:45Z, the same session as Briefs 12 and 13, paused between about 22:10Z and 07:50Z |
| Model | claude-opus-5-5 |
| HEAD at start | `4427538`, the operator's records commit, unpushed, over `35db38b` on `origin/main` |
| HEAD at end | `4d1d04a` and this commit, over `b67452d` |
| Mode | **Mutating.** Live reads of Ashby's two boards, 2 requests; `data` and the private repository's `data` branch from scratch clones, the private one read-only with its remote dropped; no Airtable connector call |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What was asked

2026-10-17, Brief 14 from the architecture chat: item 0, ADR-0053's new Confirmation clause given its registry entry and pushed with the operator's records commit; item 1, Ashby, the operator's go; item 2, no connector call in October unless essential, and his daily reading of the meter at a time he chooses; item 3, the November 1 switch as set; item 4, EWOR's walks and the unrun mutations; item 5, two stale lines.

The operator, the same night: stop what is not needed and say what belongs to other repositories (nothing closed, all his in use); stop the mutations after batch 1; the daily reading at noon his time, 07:00Z; EWOR's first walk on 2026-10-19. On 2026-10-18: "if there is work pending, do it", and start batch 2 of 4.

## Errors this seat made

- **A heredoc carried backslashes again,** against the operator's standing rule, in an edit of `tests/test_config.py`. It wrote what was meant because the heredoc was quoted; the rule has no exception. Every script since went through the Write tool.
- **Ashby's build was first dated 2026-10-18 from the local clock** while UTC was 2026-10-17: nine times across five files and in the mutation file's name. Caught before the commit.
- **The report on Brief 13 dated the operator's word on Ashby 2026-10-18,** the same slip.
- **The adapter's first docstring said 9 of 33 postings had no country;** a count gave 8 before the commit.
- **The report on Brief 13 said "its per-platform budget went from 2 to 3"** for the contract check, and the chat annotated ADR-0061 with 3 for SmartRecruiters alone. The constant is every platform's. Reported; the chat corrected the annotation in `b67452d`.
- **"About 18 rows leave `Jobs` at the next daily sweep" was wrong** (see "The first deep morning").

## What was done

**Item 0** (`00451b7`): `tests/confirmations.py` names two tests for "The morning walk must be seen reading past the stored mark to the age limit, and the evening walk stopping at its mark.": the walk test, and the shipped board walking deep on the morning only. Without the entry, `TestEveryConfirmationIsHeld` failed naming the clause; with it, it passed [VERIFIED].

**Item 5:** `CAPABILITIES.md`'s limits line on rows stored before the description rules (`a3d03ab`). The schema reference's four fields had already been marked made in `35db38b`, before the brief was written.

**Item 1, Ashby** (`4e1fab2`). Read live first, 2026-10-17T21:00Z, two requests [VERIFIED]:
- **Overjet 30 postings, deeter-analytics 3,** each with its description in the list, so one request a board and no detail phase.
- **No company field and no stated level** on any of the 33: the employer is the alias, provenance `slug`, as on Lever (ADR-0026).
- **`workplaceType`** Remote 16, Hybrid 15, OnSite 2; `isRemote` is true on Hybrid too, so it is not read.
- **Places:** the posting's own `location` and each secondary location, 13 of 33 having one or more, joined by semicolons so D13 judges each. Countries are names, read as text by the location rule; the primary address is null on 8.
- **Through the real chain:** none kept, title 32, seniority 1. Five list Pakistan among their places.

**ADR-0052's first `publishedAt` is kept by the store, not the adapter,** read in the code before building: the run appends only identities it has not seen (`split_new`), the seen store keeps the first date (`entry.get("published_at") or row.published_at`), and the full branch holds a posting's first sight. Two run tests hold it: a republished posting keeps its first date in the raw layer, the filtered layer and the seen store; and one too old at first sight stays dropped when republished.

The contract check reads Ashby's declared paths, one request a check. Two cassettes, every value they hold read before commit. Eight mutations; four older ones re-expressed because the registration changed the lines they target.

**The push:** `35db38b..4e1fab2` at 2026-10-17T22:04Z, with the operator's `4427538`, which alone fails the confirmation test by design.

**The process check** the operator asked for, 2026-10-17T20:50Z: nothing of this seat's idle or orphaned, the batch's own processes only; everything else his and in use, left as he asked. Free memory, 0.5 of 7.7 GB, was the likelier cause of the heat than CPU, about 32% in all.

## The first deep morning

The run of 2026-10-18T03:19Z, read from its log on `data` [VERIFIED]:
- **Ashby's first run:** Overjet 30 read and new, none kept (title 29, seniority 1); deeter-analytics 3, none kept; no parse problem.
- **The Himalayas walk read to the age limit:** 29 pages and 30 requests, against 3 to 5 pages on the six runs before. Its stop, logged as "mark" on either slot, was 2026-10-11T03:19:47Z, the run time less seven days, which only the morning slot uses (`_fetch_pages`). It read 580 postings, 109 new; today's rules kept 2, and `Jobs` gained 2 rows.
- **The sweep** deleted the five `accepted` copies he marked Delete and their five `Jobs` rows. 10 Airtable calls in the run, 3 for the projection and 7 for the sweep; the pipeline's October count is 471, 428 production and 43 test.
- **SmartRecruiters' second run asked for no detail** on either board: ADR-0028's once-ever detail, seen live.
- **The re-read's drops did not leave `Jobs`, and should not have.** The seat had claimed about 18 would `[INFERRED]`. Judged offline over both stores' filtered layers at the run's time, the overlay turns 42 rows from kept to dropped and none the other way; 21 have no outcome stored and were first seen under 30 days ago (19 Himalayas on the level rule, first seen about 2026-09-29, before Himalayas' level was read; 1 Himalayas on experience; 1 Lever on location). The sweep judges `Jobs` rows on the overlay through the same chain, held by a test whose mutation batch 1 caught, and it found no unclassified row to remove. So the 21 are classified rows on their fifteen days, or rows no longer in `Jobs`; "under 30 days with no outcome stored" is not "unclassified in `Jobs`". No connector call was spent to tell which.

## Not done

- **36 of the round's 81 mutations not yet run,** in two batches of 18, when the operator can leave the laptop on.
- **EWOR's first walk,** 2026-10-19, on his word.
- **His first daily reading,** asked for on 2026-10-18.

## Verification

- **Suites,** each commit alone in a scratch clone on Python 3.12 and 3.11: `00451b7` and `a3d03ab` 957, `4e1fab2` 969 [VERIFIED]. `4d1d04a` and this commit before their push.
- **Mutations: 45 of the round's 81 proven, every one caught.** Batch 1, 16 at `65061c9`, 2026-10-17T20:07Z to 21:39Z; batch 2, 18 at `4e1fab2`, 2026-10-18T07:51Z to 09:39Z: the level rule as levels that drop, Workable's level, the description fields and their switch, the run log's count of admissions without a description, and SmartRecruiters' walk, link and remote. None survived, none timed out [VERIFIED].
- **Privacy:** the push's diff scanned for Airtable IDs, tokens and aggregator links, the scan proven on a planted ID first, 0 hits; the private clone's remote dropped on cloning.
- **Processes:** none of this seat's left running after each batch and suite, checked by process listing.

## Open

- The operator: the daily reading at 07:00Z; the reports on Brief 14 and its Addendum 1 relayed.
- 2026-10-19: EWOR's first walk, against `walk_20261016.json` in the session's scratchpad. About 2026-10-23: the second, and the evening run's figures.
- 2026-11-01: the Senior switch and `description_fields_shown` on, in one commit.
