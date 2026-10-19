---
type: log
description: Briefs 15 and 16. CLAUDE.md's exit codes brought current in two blocks; the second wave measured for who reads the application, then built, Hacker News first, then Jobicy, RemoteOK and We Work Remotely; ADR-0057's exception for Hacker News' on-site posts; a switch to hold a source from Jobs; every run log naming its commit; four employer boards from the second wave; Breezy read once; the Airtable calls by kind, with proposals; EWOR's second walk.
status: current
---

# Briefs 15 and 16: the second wave measured, then built, 2026-10-18 to 2026-10-19 UTC

Previous log: `2026-10-17-brief-14-ashby-and-the-first-deep-morning.md`.

| Header | Value |
|---|---|
| Date | 2026-10-18 from about 15:55Z to 2026-10-19 about 08:30Z, the same session as Briefs 12 to 14, paused between about 22:05Z and 07:35Z |
| Model | claude-opus-5-5 |
| HEAD at start | `ff2b76e` and the architecture chat's three CHAT_STATE commits, level with `origin/main` |
| HEAD at end | `8e1a5e3` and this commit |
| Mode | **Mutating.** Live reads of the four second-wave sources, their terms pages and the employer boards they linked to; Breezy's one board; Himalayas' Pakistan search for EWOR; `data` and the private repository's `data` branch from scratch clones; no Airtable connector call |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What was asked

2026-10-18, **Brief 15**: `CLAUDE.md`'s exit codes, a block to apply exactly; the second wave measured, Hacker News "Who is hiring", Jobicy, We Work Remotely and RemoteOK, for yield and for **who reads the application**, the operator's own conclusion from his applications put as a question to measure; version 1.0.0's four choices recorded; EWOR and the daily reading.

The operator the same day: the meter refreshes between 2 pm and 7 pm his time, local and not UTC; `briefs/implementing.md` to hold the seat's initialization above a line and the chat's latest brief below it.

2026-10-18, **Brief 16**: ADR-0063's and ADR-0057's registry entries and the push first; `CLAUDE.md` block 2; Hacker News built now and first, ADR-0057's exception for its on-site posts; the four employer boards; Breezy read once; the run log naming its commit; Jobicy, RemoteOK and We Work Remotely after Hacker News, before Measure A's window opens on 2026-11-01; fewer Airtable calls, measured and proposed.

## Errors this seat made

- **"Kept if read fresh" first read 0 on Hacker News**: the measurement re-dated `published_at`, while the age rule reads `ordering_date`. Caught from the counts before reporting.
- **The phrase patterns first over-counted**: "team at Acme.io" in prose read as an address, privacy and accommodation addresses as apply routes, the employer's own recruiter lumped with agencies, and a posting with no route labelled "the board". Each caught by reading contexts, and every pattern proven on 18 built cases, before a number was reported.
- **The Hacker News board's first slug, `job`**, made the preference audit read every literal "job" as an employer's name. Renamed `jobstories` before any commit.
- **The first Hacker News cassette leaked three ways**: Algolia's highlight objects, which the field list never met; tags naming posters' accounts; and Fastly's post, its header run into its description by a bare line break, which kept a sentence of prose. Each found by reading every value before commit; the tool and, for the last, the adapter fixed.
- **The re-read would have refused every saved Hacker News post**, the parse demanding the thread's title around it. Found by checking how the re-read wraps a posting before the commit; fixed and held by a test.
- **Test modules ran beside a full suite** for about twenty minutes, against the operator's rule of one heavy job at a time. The suites passed; none ran beside a suite afterwards.
- **We Work Remotely's countries were first split on " and " as well as commas**, which would have broken "United Kingdom of Great Britain and Northern Ireland" in two. Found in the built adapter's own reading before the commit.
- **We Work Remotely's build was first dated 2026-10-18 in its texts**; it was committed on 2026-10-19 UTC. Corrected before the commit.

## What was done

**Brief 15, item 1** (`e4f17c2`, pushed): the block applied exactly. Two sentences said more than the code; offered back, they became block 2.

**Brief 15, item 2, the measurement** [VERIFIED], 61 requests, read once each on 2026-10-18 within each source's terms: Hacker News' October thread 266 posts and 13 job stories; Jobicy's whole week, 833, by its cursor; RemoteOK's 99; We Work Remotely's 88. Read fresh through the real chain: the thread 27 (17 of them on site or hybrid in places the rule could not then name), job stories 2, Jobicy 2, RemoteOK 6, We Work Remotely 1. Who reads, by fixed phrases: Hacker News is where a person can be written to (77 of 266 give an address), while where the aggregators' postings describe their process they name the employer's recruiter (Jobicy 216 of 833, We Work Remotely 31 of 88); most posts on every source do not say. 49 employer boards they linked to, read once each: 2,521 postings, 5 kept read fresh.

**Brief 16, item 0** (`5574eac`) and **item 1** (`d183903`), pushed with the operator's records `6765b38` and `8607641` before any build.

**Item 5** (`1941da2`): every fetch run log and contract check log carries `commit`. **Item 3** (`0d3d046`): LiveKit, ClickHouse, Mastra and PostEra.

**Item 2, Hacker News** (`51fc43b`): the thread, found among the `whoishiring` account's stories and read whole (a `follow` step in the run and the contract check), and the job stories. A post's first line, to its first paragraph or line break, gives the title, employer, place and workplace. ADR-0057's exception built, configured by `header_place_sources`. A switch, `sources_held_from_display`, holds a source from `Jobs` while it is fetched and stored; empty, since October holds. Read fresh over the October reads: 8 of 266 and 2 of 13.

**Item 6**: Jobicy (`5c51114`), its cursor walked back to what is stored; RemoteOK (`512d9b6`), its notice passed over; We Work Remotely (`8e1a5e3`), its RSS fetched as text through the shared client's new `get_text` and decoded by its adapter, the countries it names taken as the place ahead of its region. In that order: by yield, then by fewest postings naming a recruiter in their process. All aggregators, their rows in the private store, each linking to its source's page and naming it. The registries and the aggregator set now name one platform a line, so a platform added moves no other's line.

**Item 4, Breezy**: its one registry board, 193 postings, none kept on any rules.

**Item 7**: every row he marked poor filtering or not a fit (15, all Himalayas, all 2026-09-24 or 25) is already kept out by today's rules. October's calls by kind: production 434 to 10-18 evening (sweep 196, projection sending 190, reading back 42, Health 6), test 43. Proposed, not built: one read of `Jobs` for both the projection and the sweep, about 120 a month; the rejection tables read only when needed, about 60.

## The first live run of the second wave

The run of 2026-10-19T03:32Z, read from its log on `data` [VERIFIED]: its `commit` is `51fc43b…`. Hacker News' thread 266 read, none kept, its 8 kept-read-fresh posts older than seven days at this first sight; job stories 100 read, 2 kept; PostEra 1 kept; LiveKit 27, ClickHouse 198, Mastra 2, none kept. The re-read read 5,239 saved postings, none unknown or unparseable. 102 requests, 8 Airtable calls, 3 rows new in `Jobs`, which holds 160. October's pipeline count 485.

## EWOR's second walk

2026-10-19 at 07:43Z, Himalayas' Pakistan search walked to the baseline's floor, 63 pages [VERIFIED]. None of EWOR GmbH's 88 postings of 2026-10-16 is still listed; 91 new ones, published 10-17 and 10-18, all carrying the "(100 % remote) (m/f/d)" template, which no other employer uses. The week before, 64 of its 87 had come back under the same identity; this time the batch was replaced. Of the 293 EWOR postings stored since 09-25, 24 were admitted, every one first seen on 09-25 or 09-28; none since 10-06. Today's 91: title 83, level 7, seniority 1.

## Not done

- **The round's new mutations, about 35, not yet run.** In batches when the operator can leave the laptop on.
- **The two proposals of item 7, the derived "who reads" field and Breezy's fate:** his.

## Verification

- **Suites**, each commit alone in a scratch clone on Python 3.12 and 3.11: `e4f17c2` 969; `5574eac`, `d183903` 969; `1941da2`, `0d3d046` 972; `51fc43b` 997; `5c51114`, `512d9b6` and `8e1a5e3` 1003, 1007 and 1013.
- **Phrase rules** proven on 18 built cases, each answered as built.
- **Cassettes** read value by value before each commit; three leaks found and fixed that way.
- **Privacy**: every push's diff scanned for Airtable IDs, tokens and aggregator links, the scan proven on a planted ID first, 0 hits.
- **Processes**: none of this seat's left running after each suite, checked by listing.

## Open

- The operator: his daily reading time; Breezy; the two call savings; the "who reads" field.
- About 2026-10-23: EWOR's third walk and the evening run's figures; about 2026-11-18, Hacker News' first month recounted (ADR-0063).
- 2026-11-01: the Senior switch and `description_fields_shown` on; Measure A's four weeks begin.
