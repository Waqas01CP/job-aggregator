---
type: log
description: Brief 10 measured and built. The four employer platforms' yield on the registry's boards, 0005's claims about them checked, the contract check isolated per source, ADR-0049's scan widened to every record from ADR-0050 on, genuineness signals for the live sources, Ashby's republish against ADR-0052, and six mornings of ADR-0056's week.
status: current
---

# Brief 10: yields, isolation and genuineness, 2026-10-04 UTC

Previous log: `2026-10-03-brief-9-twelve-runs-times-and-every-clause.md`.

| Header | Value |
|---|---|
| Date | 2026-10-04 UTC, from about 21:25Z. The machine's local date was already 10-05. The operator relayed Brief 10 from the architecture chat |
| Model | claude-opus-5-5 |
| HEAD at start | `fbbc77d`, level with `origin/main`: the chat's five record commits on top of `23966ca` |
| Mode | **Mutating.** `data` read from a scratch clone at `b4f9f03`; the private repository's `data` and `data-full` branches cloned read-only at the run of 10-04T17:21Z; 73 requests to four ATS platforms' public endpoints |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## The runs since the last log [VERIFIED]

Read from `data` at `b4f9f03`:
- **2026-10-04T04:38Z, morning:** 705 postings read, 113 new, all Himalayas; 8 kept, 5 stored. The first run to store under the description rules: none of the 113 was dropped by them (Himalayas' drops were title, level and seniority); their 9, 2 and 12 drops are over every posting read, the same each run. 19 requests. Projection 113 groups, 12 calls; the daily sweep 5 calls, nothing closed, nothing removed. The first under twelve-run closure: nothing closed.
- **2026-10-04T12:46Z, contract check:** all three platforms unchanged.
- **2026-10-04T17:21Z, evening, the first evening Himalayas walk:** 4 pages and the agreement check's browse, 5 requests, as estimated; 44 new Himalayas postings, 3 kept, the walk stopped by its mark. 643 read, 45 new, 6 kept, 2 stored. 115 groups, 12 calls; month 157, the test branch's 37 among them.

**Every scheduled run since 2026-09-17 happened**, from the public Actions API: 36 of 36 fetch slots and 10 of 10 contract slots. Each started 3.3 to 7.9 hours after its cron. Two fetch runs failed, on 09-17 and 09-27, both already logged.

## The chat's records, read first [VERIFIED]

ADR-0059, research 0005 and `docs/versions/v1.0.0.md` read in full; the amendments by their Changes rows. The suite passed at 816 on the chat's tree, so every `tests/confirmations.py` key still matched.

**The chat's review of `CAPABILITIES.md` arrived during this session**, as `dfe9caf` at 21:44Z, committed in this same working copy and pushed. Its message leaves the measured numbers to this seat. Accepted, with two figures changed in the record commit: time zones as residence were 14 to 18 of 2,271 postings, not 14; and Manatal's date, which it called still to be measured, was measured here. Had it landed during a mutation batch, which mutates this working copy's files in place, it could have committed a mutated file; it landed twenty minutes before the first.

**The records are dated a day ahead.** The chat's five commits were made at 20:24Z and 21:19Z on 2026-10-04 UTC, and the rows of the last two are dated 2026-10-05, this machine's local date. Reported to the chat, not corrected: its rows.

## 1. Yield of Ashby, Workable, SmartRecruiters and Manatal [VERIFIED]

**The registry** is the operator's file outside the repository, `Operating Plan\Reference\Jobs\Apify Run Log and ATS Registry.md`, read only: 15 boards with a handle on the four platforms (2 Ashby, 2 Workable, 2 SmartRecruiters, 9 Manatal) and 7 Workable employers without one.

**Requests, 2026-10-04 21:38Z to 21:46Z:**

| Purpose | Requests |
|---|---|
| One per registry board, each vendor's documented endpoint | 15 |
| The 4 Manatal boards answering 404 there, on the endpoint ADR-0029's spike used, every page | 28 |
| SmartRecruiters' detail for the 2 postings passing every rule but age | 2 |
| Workable slugs guessed for the 7 unslugged employers | 13 |
| Manatal's creation filter: a week ago, a future date and an invalid one on Abacus, then Abacus again, then Ahdus and Gigalabs since 09-27 and since 09-04 | 8 |
| Hugging Face's Workable account, for 0005's claim, with the redirect | 7 |

**Method.** No adapter exists, so each platform's postings were mapped onto `Posting` provisionally and run through the real `normalise` and `apply_chain` at the time of the read:
- **Ashby:** `id`, `title`, `jobUrl`, `publishedAt`, `location` and the secondary locations as the location, their countries as places, `workplaceType`, `descriptionHtml`.
- **Workable:** `shortcode`, `title`, `url`, `published_on`, city, state and country as the location, `locations[].countryCode` as places, `workplace_type` or `telecommuting`, `description` (one request with `details=true`).
- **SmartRecruiters:** `id`, `name`, a constructed `jobs.smartrecruiters.com` URL, `releasedDate`, `fullLocation`, the country code, `remote` or `hybrid`; the description from the detail's job ad sections.
- **Manatal:** `id`, the first translation's `name` and `description`, city, state and country; no date, no workplace, a constructed URL.

| Platform | Boards answering | Postings | Pass every rule | Every rule but age |
|---|---|---|---|---|
| Manatal, documented | 5 of 9 | 257 | 10 | 10 |
| Manatal, undocumented, the other 4 | 4 | 522 | 3 | 3 |
| SmartRecruiters | 2 | 20 | 0 | 1 |
| Ashby | 2 | 25 | 0 | 0 |
| Workable, registry slugs | 2, one empty | 15 | 0 | 0 |
| Workable, slugs found | 4 | 63 | 0 | 0 |

Drops: title took 24 of 25 on Ashby, 16 of 20 on SmartRecruiters, 228 of 257 and 513 of 522 on Manatal, 14 of 15 and 62 of 63 on Workable.

**Manatal's dates.** No posting carries a date field: 257 on the documented endpoint, 522 on the old one. The documented `created_at__gte` filter works: on Abacus' 217, a week ago returned 2, a future date 0, an invalid date an error. Neither of the 2 is among the 7 Abacus postings kept; Ahdus and Gigalabs have none created since 09-04. So all 10 kept were created more than a week before the read.

**The description reader on Manatal's text.** Of the 13 kept on either endpoint, three say on-site or hybrid in shapes `src/description.py` does not read: Ahdus' (Rawalpindi) and Gigalabs' (Lahore) in a sentence, Premier NX's (Lahore) under a label the reader does not know. D13 would drop all three. Counted by word class only; no text was printed.

**Workable's guesses** accepted only where the account's name is the registry's employer exactly: `thingtrax`, `staunch`, `petra-brands`, `inbox-business-technologies`. Set aside: "Reef" (empty, a different name), two empty CodeNinja accounts. Trickle Up not found. **The documented `www.workable.com/api/accounts/{x}` answers 302** to the undocumented `apply.workable.com/api/v1/widget/accounts/{x}`.

## 2. 0005's claims [VERIFIED]

Read from each vendor's own reference, raw where a summarising fetch could mislead:
- **Confirmed, Strong:** Ashby's endpoint and `publishedAt` "when the job was last published" (page updated 2026-05-26); Workable's endpoint without auth (updated 2025-06-10); SmartRecruiters' endpoint, auth optional for public postings, `releasedDate` undefined, `releasedAfter`, 100 a page (updated 2026-04-23); Manatal's endpoint without auth (updated 2026-05-07); Breezy documents no public endpoint; no platform states a rate limit; Hugging Face hires through Workable (8 jobs, remote, France and the United States).
- **Contradicted, wrong when written:** Workable's `published_on` and `created_at` are defined, "The publication date of the job" and "The timestamp the job created"; Manatal's job post schema carries no `created_at`, which belongs to the client, and no posting of 779 carries a date.
- **Not re-checked:** Manatal's 2025 shutdown notice.

## 3. The contract check, isolated per source [VERIFIED]

Built in `2c38f6f`. Before it, one platform could end the check three ways: an exception other than an HTTP error reached `main`, which exited 1 and committed nothing; the three shared a budget of six, so two boards failing three attempts each starved the third; and they shared a breaker that five failures opened. Now each platform has its own client, budget of 2 and breaker, and its own exception boundary: a failure reads `check failed` with the exception's class and where it was raised, never its message, since the log is public and a message could carry an aggregator's text. Its fingerprint stands, the others are checked, the log is committed, and `main` exits 2; `contract.yml` pushes on 0 and 2 and then marks a 2 failed as its last step. `tools/run_log_report.py` names each failed or unreachable check with its detail.

Tests: one platform's check raising while another's response changes, the first failed, the second's change found, all three asked; a failure's message kept out of the log; two failing boards unable to spend the third's budget or open its breaker; `main` committing the others and exiting 2; the workflow's push before its last step; the report naming a failure after a later check overwrote it. The check that stays exit 1, a crash of the check itself, is now made at loading the boards.

**The Airtable row is not built.** It needs a table and two secrets; the design and the operator's question are in the report.

## 4. ADR-0059 held, and ADR-0049's scan widened [VERIFIED]

Built in `ca349a5`. The scan reads every record from ADR-0050 on, so a new record is held the day it lands; a test holds that the glob found every number from 0050 to the last. ADR-0059's clauses: a projection test that rows from all three sources with the same dates carry the same `Order date`, the field the view sorts on; the isolation tests; the Airtable row marked unbuilt; and a fitness function that every platform with an adapter or a configured board has its contract check through the same adapter. An older test, `test_every_platform_the_run_polls_is_checked`, already held the narrower half, the same set of platforms; both are on file for the clause.

## 6. Genuineness signals [VERIFIED]

Stores as of the run of 10-04T17:21Z, observed since 09-17T14:52Z. Counts only.
- **Greenhouse:** 976 identities; 504 open at the latest run, 472 gone (316 Speechify, 78 Veeam, 51 Motive). Open now by age from `first_published`: 186 at 30 days or less, 113 at 31 to 60, 62 at 61 to 90, 59 at 91 to 180, 43 at 181 to 365, 41 over a year; past 60 days 205, past 90 143. Of 932 employer, title and place keys, 42 under more than one identity, 22 with different dates, a median 79 days apart.
- **Lever:** 79 identities, 59 open; past 60 days 11, past 90 6; 7 of 69 keys under more than one identity, all dated differently, a median 78 days apart.
- **Himalayas:** `expiryDate` is `pubDate` plus 60 days on 1,467 of 1,525 saved postings; every `applicationLink` is its own job page on `himalayas.app`, 1,525 of 1,525; of 10 postings from employers read directly, the 7 still open on the board carry a date 1, 2, 2, 3, 14, 23 and 293 days after Greenhouse's `first_published`; 5 of 3,012 keys under more than one identity.

## 7. Ashby's republish [VERIFIED] from documentation

Ashby's `jobPosting.setStatus` (updated 2026-07-28) unpublishes a posting to `Draft` and publishes the same posting back; `jobPosting.create` makes a new posting for a job, and its applications reference speaks of "multiple job postings for the same job". The public feed's `id` is undocumented and equals the id in each posting's `jobUrl`, 25 of 25 `[INFERRED]` as the posting's id. No title and place repeated in 25.

## 8. ADR-0056's week [VERIFIED] for six mornings

Display groups each morning, 09-29 to 10-04: 74, 75, 83, 92, 108, 113; 115 the evening of 10-04. 41 new groups and 42 new rows stored (2 public, 40 aggregator) from the 09-29 morning to the 10-04 evening. The 10-05 morning had not run. Arithmetic in the report.

## Mistakes of mine

- **Two comments dated 2026-10-05 while UTC was the 4th.** Caught before any commit.
- **One suite run at normal priority**, outside the wrapper. Two minutes, nothing else running.
- **One response saved to the system temp folder.** Moved to the scratchpad.

## Verification

- **Suite:** 816 on the chat's tree before any change; 826 after, on Python 3.12, and on 3.11.9 at the record commit's tree. Each commit alone, in a scratch clone: `2c38f6f` 823, `ca349a5` 826.
- **Mutations,** each a full suite run at below-normal priority with `--why`: the 9 new, now in `2026-10-04-each-source-on-its-own.json` (7) and `2026-10-04-adr-0059-held.json` (2), 9 caught; the 3 re-expressed, run from a scratch file, 3 caught. No find on file stale: the suite's own check passes.
- **Privacy:** each staged diff scanned for Airtable IDs, tokens and aggregator URLs before its commit; none. Nothing aggregator-sourced is in any committed file but counts.
- **Processes:** none of this seat's left running.

## Open

- The operator's four answers in the report: the findings table, the delta projection's design, Manatal's undocumented endpoint, the four Workable slugs.
- The 10-05 morning, for ADR-0056's seventh row.
- From 10-07, his trial verdicts on Himalayas and Banyan Canopy.
