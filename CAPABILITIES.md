---
type: explanation
description: Everything the system is and does, in one file. Its purpose, how a run works end to end, the stack, its engineering qualities, measured numbers with their sources, how it was built and by whom, and its limits. Written so that reading it stands in for reading the repository. Kept current.
status: current
---

# Capabilities

**What this file is.** Everything this repository is and does, in one place, for a reader who will open nothing else. The operator set two purposes for it, in his account to the architecture chat:
- **any chat** that needs to know the project, a chat drafting his CV among them, should learn everything from this file without exploring the repository;
- **a person** reads `README.md` to set the system up and run it, and this file for the nuance: the measured numbers, how it was built and by whom, its decisions and where it is going.

**Current as of 2026-10-19 UTC**, against `main` with the work of Brief 17 built, all of it pushed but `Who reads`, which waits for its field in the base *(until 2026-10-19, 2026-10-18 and Brief 14; until 2026-10-18, 2026-10-15 and Brief 11)*, and every source run live but Jobicy, RemoteOK and We Work Remotely, built on 2026-10-19 and first run at the next scheduled run. Every number carries its date and its source; one that can no longer be measured stays, marked. *(Until 2026-10-15 this said a number that could not be measured is not here.)* **The end state, the sources' order, the timeline's last rows and the operator's role are current as of 2026-10-09 UTC**, updated by the architecture chat from the decision records, the commit history and, where marked, the operator's own account to the chat. *(The operator's role brought to 2026-10-17 UTC, and the end state's sources the same day.)* *(The operator's role brought to 2026-10-20 UTC.)*

**Kept current.** Updated at the close of any session that changes a capability or a measured number. Sections that restate a decision name the record that holds it, so a reader who wants the reasoning can find it.

---

## In one paragraph

A personal job-discovery pipeline that runs itself.
- **Twice a day**, on GitHub Actions, it reads the public job feeds of thirty-four employers' boards on six applicant-tracking-system (ATS) platforms, Greenhouse, Lever, Manatal, Workable, SmartRecruiters and Ashby, four of the boards found through the second wave on 2026-10-18; one aggregator narrowed to postings open to Pakistan; and, since 2026-10-18, Hacker News' monthly "Who is hiring?" thread and its job stories, posts written by people at the hiring companies, read from each post's first line; and Jobicy's, Remote OK's and We Work Remotely's remote-jobs feeds, each row linking to its source's page and naming it. A SmartRecruiters posting's description is a request of its own, asked once, when the posting is first seen.
- **It keeps every posting it fetches, permanently.**
- **It admits only postings the operator can use:** his target roles, his level and years of experience, places he is eligible to work, and at most a week old when first seen. Each posting is admitted or dropped by a named, deterministic rule.
- **It shows what survives in an Airtable table.** The operator marks each row accepted, not a fit, or poorly filtered. The pipeline copies each mark to its own table, stores it for good, and clears the display after fifteen days. A row he never marks leaves after thirty, and he can clear any table himself, dry run first.
- **It costs nothing to run.** Over its first two weeks in use, a posting it admitted reached the display a median of 7.3 hours after its employer published it, 22.0 hours at the 90th percentile, against targets of 24 and 72 (2026-10-15).

---

## The problem it solves

**The operator's situation.** Waqas Sharif is a software engineering graduate of 2026, based in Karachi, Pakistan, looking for AI engineering and software roles. Before this pipeline, he found work by hand:
- visiting one employer's careers site after another;
- signing up where a site demanded it;
- running a few searches on each.

By his estimate, that took most of a working week. He usually found a posting three to six days after it went up, ranging from a day to three weeks, and by then the first review window had often passed (`docs/architecture-2.0.md`, section 1).

**Four goals, in priority order:**

| # | Goal | How it is judged |
|---|---|---|
| 1 | Freshness at discovery | **Measure A**, binding: the median time from publication to first appearance at or under 24 hours, the 90th percentile at or under 72. ADR-0015 |
| 2 | Nothing is silently lost | Every posting either appears or carries a recorded reason it was dropped |
| 3 | Search overhead falls | Hours a week spent on job discovery. Reported, not binding |
| 4 | Runs unattended | An absence of days costs latency, never data |

**One user.** The operator is the only user, reviewer and decision maker.

---

## Where it is going: version 1.0.0

**Version 1.0.0 is the system working for the operator himself, as he intends it** (ADR-0059, 2026-10-04 (2026-10-03 UTC); ADR-0063, which superseded it on 2026-10-18). Making it work for anyone else is a later version, and a separate decision. What 1.0.0 includes, each part's status and the test for done are kept in `docs/versions/v1.0.0.md`, a file of its own because a version's status changes as the work does while a decision record is concluded once.

**Sources are chosen by their value to him, not by their size or reputation:** whether postings are genuine rather than ghost posts or CV harvesting, how fairly applicants are treated, how long hiring takes, and whether he can take the role. Claims about a source count only from primary sources; a recommendation by an influencer counts for nothing. Research pass 0005 assessed the candidates on 2026-10-04 (begun 2026-10-03 UTC) and found that no public study ranks job sources by how genuine their postings are, so each source's genuineness is measured from the project's own data.

**The order.**
1. Employer boards on four more ATS platforms, Ashby, Workable, SmartRecruiters and Manatal, because the application goes straight to the employer, and a date, where the platform gives one, comes from the employer's own system. What each date means differs by platform, and Manatal's postings carry none: no date on any of 640 distinct postings across its 9 registry boards, measured 2026-10-04 and recounted 2026-10-07, though its documented creation filter brackets the day a posting was created. Their order is set by measuring how many postings he can take their registry boards carry. Measured 2026-10-04 through the real filter chain: Manatal 10, none under a week old, and the other three none (`2026-10-04-brief-10-yields-isolation-and-genuineness.md`). Manatal, first by that measure, was built on 2026-10-07, on its career site's own endpoint for every posting's link; Workable, second by the tie-break of registry boards, on 2026-10-08. *(2026-10-17: Manatal, Workable and SmartRecruiters built; Ashby next, with the operator's go.)* *(Ashby built the same day, so all four are.)*
2. Himalayas stays, the only aggregator of those read that lists per posting the countries a role is open to.
3. A second wave, Hacker News "Who is Hiring", Jobicy, We Work Remotely and RemoteOK, each only if its measured yield is worth its upkeep, his call. *(2026-10-18: all four built now, Hacker News first, on his decision, ADR-0063; measured first for who reads the application as well as yield.)*

**"Preferred" means integrated first, and nothing else.** A source never moves its postings up the display, which stays ordered by date, newest first.

**The test for done**, accepted by him on 2026-10-05 (2026-10-04 UTC): freshness (Measure A) holds over four weeks from 2026-11-01 UTC, the window he set on 2026-10-18 *(until then, a window he chooses)*; nothing is lost silently, every drop and every closure naming its rule; the system runs unattended, every scheduled run happening and every failure reaching Airtable; every integrated source has its own contract check, isolated from the rest; and then he uses the tables over the same four weeks *(until 2026-10-18, a period he chooses)*. Only he declares 1.0.0 done.

**Waiting for later:** the priority star (ADR-0044), deduplication across sources, and a record of what happened after he applied, which waits until he has used the tables.

---

## What a run does, end to end

1. **Starts on a schedule.** Two GitHub Actions workflows:
   - **Fetch.** Scheduled for 00:00 and 13:00 UTC; GitHub starts them late, measured at 03:26 to 04:33 UTC and 16:18 to 20:02 UTC, 3.3 to 7.0 hours after the slot, over the 29 scheduled runs to 2026-10-01. It also runs on a manual dispatch, which can be ticked as a test run that writes only to separate test branches and tables.
   - **Contract check.** Scheduled daily for 06:30 UTC; GitHub started its last five at 11:42 to 14:21 UTC.

   Each fetch runs the full test suite before touching any data.
2. **Restores state.** The run loads what the stores already hold, so it appends to the stored history rather than to whatever the last machine saw:
   - from the public `data` branch;
   - from a second, private repository, for aggregator data.
3. **Fetches.** All fetching goes through one shared HTTP module:
   - retry with backoff;
   - a request budget of 500 per run, counting every attempt including retries;
   - a circuit breaker on consecutive failures.

   **Adapters are per platform, never per employer:** one Greenhouse adapter serves nine boards. An adapter only parses; it never fetches. Manatal's nine boards, the first platform added by measured yield (2026-10-07), are paged too and read to the end, since their postings carry no date to stop at, and a posting its shifting pages repeat is kept once. The aggregator, Himalayas, is paginated. It is read newest first and stops at the first page that is either wholly older than what that board has already stored in full, or wholly older than the age limit. An 80-page cap guards against a runaway; it was 40 until 2026-10-02, when a week of the search outgrew it.

   **The aggregator's own filter is checked on every walk.** Himalayas is asked only for postings open to Pakistan, which hands part of the location rule to a third party. So one page of its whole feed is read beside the search. That page is minutes old and the search trails it by hours, so a posting there that the location rule would admit, and the search has not returned, waits privately for a walk at least twelve hours later. Still not returned by then, it is a disagreement: counted in the log and named in the private store (ADR-0053).
4. **Normalises** every posting to one row shape. The publication date and the moment the pipeline first saw the posting are recorded as separate fields, never confused. Where the employer name or URL is derived rather than given, the row says so.
5. **Stores the raw layer.** Every posting never seen before is appended permanently, before anything is judged, and nothing is ever rewritten. So a filter mistake is recoverable: the rows it missed are still stored.
6. **Filters**, cheapest rule first. Every drop is logged with the rule that caused it. The rules (the chain is in `src/filters.py`):

   | Rule | What it drops | Source of truth |
   |---|---|---|
   | Expiry | A posting past its stated expiry | The posting |
   | Annotation vendor | Postings from data-labelling vendors | `docs/reference/annotation-vendors.md` |
   | Title | Titles matching none of 79 terms in four role families: agentic AI, LLM and applied AI, traditional AI and ML, software engineering | `docs/reference/title-pool.md` |
   | Seniority | Titles carrying a senior-level word (senior, staff, lead, principal, II, III and others) | `docs/reference/seniority-exclusions.md` |
   | Level | Where the source states a level, a posting every level of which is above mid: Senior, Manager, Director or Executive. Himalayas and SmartRecruiters state one on every posting and Workable on some; a posting that states none, or a level the list does not name, is kept. Senior leaves the list on 2026-11-01 | `config/eligibility.json` |
   | Experience | A posting whose description asks for more than 3 years of experience, required or preferred. A range counts by its low end, so "3 to 5 years" is kept; a description stating no figure keeps the posting | `config/eligibility.json`, `src/description.py` |
   | Authorisation | A posting whose description requires the right to work, citizenship or residence only in places closed to the operator, such as authorisation to work in the United States. "No visa sponsorship" is never read as one: on a role open worldwide it only says no one is relocated | `config/eligibility.json`, `src/description.py` |
   | Location | A posting only when *every* place it lists is closed to the operator. Examples: other countries only; a region without Pakistan; on-site in a Pakistani city other than Karachi. Where the text names only a city the rule does not know, the source's own country or office decides, and only to close. A workplace the source states as on site or hybrid counts as on site, and so does a description saying so where the source states none. Anything still unclear is kept | `config/eligibility.json` |
   | Age | A posting published more than 7 days before the pipeline first saw it. Judged once, at first sight, so an admitted row never ages out unseen | `config/eligibility.json` |

   Title matching normalises both sides: case, punctuation, accents and plurals. Spelling variants such as "fullstack" and "full stack" are listed as terms of their own.

   **The description is read once, for what stops him applying.** Fixed phrase patterns, each measured over every saved description before it was switched on, find the years asked, a place a right to work or residence is required in, and on-site work. The row keeps only those derived values: a number, configured place names, a flag. The description's words never reach the public branch.

   **And who reads the application** (since 2026-10-19, the operator's decision, so he can find the postings a founder reads): one label, founder, engineer, agency, recruiter or a named person, the first in that order the description gives grounds for, empty when it says none. It drops nothing and is shown in `Jobs` as `Who reads`, never a name or a word of the posting. Measured over all 5,750 saved descriptions before it was built: a label on 281, a founder on 12, 11 of them on Hacker News' thread. *(Built 2026-10-19; shown once the operator makes its field in the base.)*
7. **Groups duplicates** by employer, normalised title and publication date. One role posted 134 times, once per city, becomes one display row listing every city.
8. **Appends the filtered layer**, the rows that passed. When a rule widens, a backfill appends the rows it now admits, inside every run.
9. **Saves every posting whole, privately** (the operator's D11). This includes the description text and every field the board returned. It goes to the private repository's `data-full` branch, one file per run. The file is read back by a fresh fetch and compared by content hash, and only then is each posting marked saved. A failed save is retried on the next run.
10. **Projects to Airtable**, the only screen the operator opens:
    - `Jobs` read back first, one call per hundred rows, and only the rows it does not already show as they would be sent are written: a run that changes nothing writes nothing (since 2026-10-07; until then every display row was sent on every run, one call per ten rows). The same read, with what was just written merged in, serves the sweep, so `Jobs` is read once a run (since 2026-10-19; until then twice, about 120 calls a month more);
    - an upsert matched on the posting's identity, ten rows per call;
    - only the pipeline's own fields are written, never the operator's `Status`;
    - a posting with no publication date is shown after every dated one, never skipped and never as newer than it may be (since 2026-10-07);
    - anything he has already classified is skipped, so it never comes back.
11. **Sweeps the display**, under ADR-0050:
    - **Every run:** copies each newly marked row into its classification table.
    - **The classification tables are read only when needed** (since 2026-10-19): `accepted` every morning, and the two rejection tables when a status moved, a rejected row reaches its fifteen days, a rejection was stored in the last three days, or he starts a run by hand, each reason named in the run log. Measured over the 25 mornings since 2026-09-25, 14 needed neither, about 35 calls a month.
    - **Every morning:** marks postings that have closed: an employer board's posting absent on twelve consecutive runs, about six days, and any posting past its own expiry date, which is how a Himalayas posting closes, since each walk reads only its newest postings and an absence there proves nothing. It writes a row to a permanent store when its time comes:
      - fifteen days after it was classified or closed;
      - at once, if the current rules no longer admit it.

      On a later run it reads the store back from the remote, and only then deletes the row from the display.
    - **The `accepted` table** keeps a row until he sets its `Delete` to yes, and every store is kept forever.
    - **A row nobody marks** leaves thirty days after it was first seen, stored first as `unreviewed-aged-out` (ADR-0055).
    - **What keeps a removed row out is its reason.** A row stored as closed, aged out or removed by the operator never returns. One a rule dropped returns if the rule is widened, because only the rules can change their mind (ADR-0043).
    - **Every removal is named in the run log** by identity. An aggregator's identity is masked there and named in its private store.
12. **Writes a run log**:
    - per board, every run, including zeros, since a board that silently returns nothing is a broken adapter, not a quiet market;
    - requests, drops per rule, what was stored and what failed;
    - Airtable calls this month, with a warning if 60% of the allowance is used before the fifteenth.
13. **Commits and pushes** the public branch, then **marks the run failed if it needs attention**:
    - at once when the private store fails;
    - on the third failure in a row for the display or the sweep.

    The data is always saved before the run is marked, so a failure is visible and never costs data.

**The contract check** fetches one response per platform. It fingerprints the shape of exactly the fields each adapter reads: present or absent, type, null or not. It reports any change by field name. That tells a board that changed its API apart from a board with no new jobs (ADR-0018, ADR-0061, which supersedes ADR-0036). A change we caused ourselves, such as a new endpoint, is recorded in configuration with its date and cause and reported as ours, so it never reads as the board moving. **Each platform is checked on its own** (ADR-0059, ADR-0061): with its own request allowance and its own exception boundary, so one platform that fails is reported as a failed check for that platform alone, the others' findings are still written, and the run is marked failed after they are saved.

**The clearing tool** is the operator's, run from the same workflow by hand (ADR-0055). He chooses a table and an age in days: publication date for `Jobs`, the date he classified for the other tables. The first run is a dry run: it reports what it would remove, and how many of those are already on their way out without it, and changes nothing. A confirmed run is refused unless a dry run of the same request ran within two days, and it removes only the rows that dry run listed: a row that crossed the threshold since is left. The dry run names public rows in the run log and aggregator rows, with title and employer, in the private repository, in a directory of its own outside the stores, so the list can never be read as one. It writes the stores and deletes nothing itself, so the next sweep removes the rows only after reading those records back. On `accepted` it only sets `Delete`. A row deleted by hand in Airtable would come back; one cleared this way does not.

---

## How data is stored, and where it may go

**Three layers**, each derived from the one before (ADR-0001, ADR-0013):

| Layer | Holds | Where |
|---|---|---|
| Raw | Every posting ever fetched | Git branch |
| Filtered | Every posting the rules admitted | Git branch |
| Display | The current projection of the filtered layer | Airtable. Never authoritative: losing it costs a screen, not data |

**Git branches are the database.** There is no hosted database (ADR-0002):
- **Public `data` branch:** employer-board metadata only, never description text (ADR-0011). Nothing from the aggregator either, because aggregator terms restrict redistribution (ADR-0020). The code refuses to commit a file holding aggregator rows, or anything that may be description text: a description field holding text, markup, or a passage longer than any record field holds. A row has no field for the text in any case; only numbers, configured place names and a flag derived from it are kept.
- **A private repository:**
  - the aggregator's rows;
  - the outcome stores for aggregator rows;
  - every posting in full (ADR-0047, D11).
- **Test mode** has its own branches (`data-test`, `data-test-full`) and its own four Airtable tables, so a test never touches production.

**The display**, eight Airtable tables (`docs/reference/airtable-schema.md`):
- **`Jobs`:** fourteen fields; `Status` is the operator's.
- **Three classification tables:**
  - `accepted`, with `Stage` (shortlisted or applied) and `Delete`;
  - `rejected-not-a-fit`, with his reason;
  - `rejected-poor-filtering`, with the pipeline's fault, so the table is a defect log.
- **Test copies** of all four.

**Permanent stores:** three append-only outcome stores, one per classification, plus stores for rows retired as closed or dropped by a later rule (ADR-0043). A stored outcome keeps its row out of the display for good.

---

## Tech stack

| Area | What is used |
|---|---|
| Language | Python 3.11 and later; the standard library plus `requests`, and nothing else. The suite passes identically on 3.11 and 3.12; production runs on 3.11 |
| Scheduling and compute | GitHub Actions: two workflows, cron plus manual dispatch, a concurrency group queueing runs rather than dropping them |
| Storage | Git itself: orphan data branches, a second private repository reached with a fine-grained token, and partial fetches so no run downloads earlier full-posting files. Atomic writes, one canonical serialisation per file |
| Display | Airtable REST API on the free plan: batched upserts, deletes, rate limits and a monthly call budget |
| Sources | Greenhouse and Lever job-board APIs, Himalayas' search API. Sixteen ATS platforms were probed for feasibility |
| Testing | `unittest`; a mutation-testing harness written for this project; fitness functions; recorded real responses with descriptions stripped as fixtures; an in-memory fake of the Airtable base that refuses what Airtable refuses |
| Guard rails | A pre-commit hook with six gates; a hook in the AI coding tool that stops a known shell hazard |
| Tools | Map generator, run-log report, publication-lag report, title-pool report, preference audit, backfill, fixture maker |
| Documentation | Decision records in MADR 4.0.0 with an Assumptions section; arc42 architecture with C4 diagrams in Mermaid; a generated index of every documented file |
| AI tooling | Claude Code for implementation and independent audits, a Claude chat for architecture, and the Airtable connector for building and reading the base |

---

## Engineering qualities, and what enforces each

| Quality | Mechanism |
|---|---|
| Every verdict explainable | No scoring, ranking or model anywhere (ADR-0010). Every admit or drop names one rule, and every drop is logged |
| Nothing silently lost | Raw layer permanent and append-only; write before delete; every store read back from the remote before its source row is deleted; a missed run costs latency, not data |
| Runs unattended | Retries, a request budget and a circuit breaker; three exit codes (0 done, 1 failed, 2 stopped and resumable); a display or sweep failure never loses the fetch; failures surface as a failed run, after the data is saved |
| Privacy and licensing boundaries | Enforced in code and in the hook, not by care. Descriptions never public, aggregator data never public, and secrets and Airtable IDs never in the repository |
| Preferences are configuration | The title pool, seniority words, role families, eligible places, age limit and vendor list are files. A test fails if any module hard-codes one (ADR-0031) |
| Idempotent | A run that finds nothing new commits only its log; a retried upsert creates no duplicate; the sweep's copy step is safe to repeat |
| Safe to clear | A bulk removal runs dry first, is refused without a recent dry run of the same request, removes only what that dry run listed, writes before anything is deleted, and never deletes from the table of roles applied to |
| Self-diagnosing | The daily contract check, per-board run logs including zeros, the month's call budget, escalation after the push, and since 2026-10-07 a `Health` table in Airtable with a row for every contract finding and every run failure, each sent once |
| Change safety | Every guarantee has a test, and every test that guards one is proved by a mutation that breaks the code and must fail it. The suite fails when a code change leaves a recorded mutation unable to run. Architectural rules are guarded by fitness functions in the ordinary suite (ADR-0049) |
| Cost | Nothing recurring: GitHub Actions is free on a public repository, and Airtable is on its free plan |

---

## Measured numbers

Each is measured, with its date and source. `data` is the public data branch.

| What | Value | Measured | Source |
|---|---|---|---|
| Production runs | 66, from 2026-09-17 to 2026-10-19, a span of 31.5 days; every scheduled run since has happened, the last twelve each a success by the public Actions API on 2026-10-19 | 2026-10-19 | Run logs on `data`; the public Actions API |
| Fetch reliability | 0 retries and no run near the request ceiling across all 63 runs, to 2026-10-17. 5 failed requests, all in one run, 2026-10-14T03:47Z: Manatal answered 403 five times in a row, and the run's one circuit breaker left six Workable boards unread; since 2026-10-15 each platform has its own breaker | 2026-10-17 | Same |
| Requests per run | 63 or 64 against a ceiling of 500 in the four runs from 2026-10-15 evening, 42 of them Manatal's at twenty postings a page; 87 on 2026-10-17 evening, SmartRecruiters' first, with a detail for each of its 20 postings; 93 on 2026-10-18 morning, the first walk of Himalayas to the age limit, 30 of them Himalayas', and Ashby's first, 2; 102 on 2026-10-19 morning, Hacker News' first, 3 of them its. Median 98, at most 102, from 2026-10-08 evening to 10-15, when Manatal cost 77 at ten a page. Before Manatal, over the first 30 runs: median 36 (2026-10-01) | 2026-10-17 | Same |
| Postings read per run | 2,940 on 2026-10-19 morning, the first with Hacker News' 266 and 100 and the four new boards' 229. 2,307 on 2026-10-18 morning, the first deep walk's 580 and Ashby's 33 among them. 1,724 to 1,793 in the five runs from 2026-10-15 evening, SmartRecruiters' 20 in the last. 1,330 to 1,841 from 2026-10-08 evening, with Manatal and Workable. 803 to 1,420 over the first 30 runs, to 2026-10-01 | 2026-10-18 | Run logs |
| Postings fetched in total | 87,521 across 66 runs, repeats included | 2026-10-19 | Run logs |
| Distinct employer-board postings stored | 2,736 | 2026-10-19 | `seen.json` on `data` |
| **Freshness (Measure A)** | ADR-0015's two weeks after go-live, 2026-09-24T03:27Z to 10-08T03:27Z: 140 admitted postings reached the display a **median 7.3 hours** after publication, **90th percentile 22.0 hours**, maximum 53.2. The targets are 24 and 72 hours. Himalayas 137 of the 140, on its morning poll until 2026-10-04; Greenhouse 1, Lever 2. Over every posting seen in the window, admitted or not, 1,725: median 9.8 hours, 90th percentile 21.4. First appearance is taken as first sight: no run in the window failed to write the display. Postings published before their board's first run are excluded, 26 admitted ones; none was dateless. Earlier, to 2026-09-30, first sight only: median 5.4, 90th percentile 10.5, over 114 postings | 2026-10-15 | The filtered and seen layers on `data` and in the private repository, and the run logs |
| Selectivity | Of 1,720 postings read, 16 kept: 1,612 dropped on title, 59 on seniority, 16 on location, 12 on experience, 4 on age, 1 on a right to work. Of everything first seen in the week from 2026-10-08 evening, 1,416 postings, 36 were admitted, 92% dropped on title | 2026-10-15, morning run, and the week before it | Run log; the raw layers through the current rules |
| Deduplication | 1,720 postings grouped into 1,128; the largest group, one role posted 180 times, once per city, became one row | 2026-10-15 | Run log |
| Himalayas before the change | 500 postings a morning, the page cap, from about 1,600 published a day (inferred from 499 new postings spanning 7.3 hours). 93 of 100 postings sampled from the feed were closed to Pakistan | 2026-09-26 | Run logs, and a live sample of 100 postings |
| Himalayas after the change | Only postings open to Pakistan requested. The first morning read back a week, 460 postings in 23 pages, stored 361 new and kept 31 | 2026-09-27 | Run log |
| Himalayas' stated level | Himalayas labels every posting with a level. Of the 67 postings the filter chain kept from the 809 saved since 2026-09-26, it labels 35 Senior or above; the title rule, which reads only titles, dropped 45 others it labels Senior or above. Since 2026-10-02 the label is read, and the chain keeps 34 of the 809, not 67 | 2026-10-02 | The private full postings, through the real adapter and chain; `docs/reference/platform-fields.md` |
| Experience in the description | No source gives years of experience as a field. A number of years appears in the description text of 53% of Greenhouse postings, 67% of Lever's and 50% of Himalayas', an upper bound | 2026-10-02 | Same |
| The description rules | Over the 1,708 postings saved by 2026-10-02, the rules read years asked in 883, a required place in 17 and on-site work in 34. Of the 50 the chain kept apart from age, 7 now drop: 6 asking 5 or more years, and 1 on site in Lahore. None is newly kept | 2026-10-02 | The private full postings, through the real adapters and chain |
| Himalayas completeness | Of the 420 postings a week-long read of the search held, published before the morning walk, the pipeline had stored all 420 | 2026-09-30 | A 26-page snapshot against the private seen store |
| Location rule, its owed check | Exactly 74 of the saved 91 Himalayas postings dropped and 17 admitted, as the record predicted nine days before the rule was built | 2026-09-30 | ADR-0041's Confirmation, on `raw_responses/` |
| Full postings saved privately | 824 postings in one 9.8 MB file, read back and matched by content hash | 2026-09-26 | Run log |
| Airtable usage | The pipeline's own: 485 of October's calls by the run of 2026-10-19T03:32Z, 442 production and 43 test, of which the sweep 196, the projection's sends 190 and its reads 42, Health 6 and the clearing tool 6 (to 10-18 evening); against its own ceiling of 900 since 2026-10-16 and the workspace's 1,000, which the chats' connector calls share; the workspace's meter read 647 on 2026-10-17 and is not live. `Jobs` holds 160 rows after that run; since the read-back of 2026-10-07 a projection costs 3 calls, two to read `Jobs` and one to send what differs. From the first run on `cb4dc12` the sweep reads `Jobs` no more, and a morning needing neither rejection table reads `accepted` alone, so a morning costs about 6 calls and an evening about 3 `[INFERRED from the run logs, not yet run]` | 2026-10-17; 2026-10-19 | Run log; the run logs and stores of both data branches |
| Display intake | About one new display row a day under the current rules, so by arithmetic, not measurement, the display settles near thirty rows, and the cheaper delta projection is not yet needed. *(Overtaken 2026-10-04: the week to then measured about 7.5 new rows a day, and `Jobs` held 149 rows on 2026-10-14; the read-back projection was built on 2026-10-07 instead, ADR-0060)* | 2026-09-29 and 09-30 | Run logs, against ADR-0056's trigger of 100 |
| Recurring cost | None | 2026-09-27 | Free plans only |
| Feasibility research | 16 ATS platforms probed; 1,646 postings across the first 11 boards | 2026-09-11 to 09-16 | Spike logs |
| Code | 37 source files, 9,869 lines; 36 test files, 14,565 lines; 9 tool files, 2,073 lines | 2026-10-19 | `git ls-files`, `wc` |
| Tests | 1044, passing on Python 3.11 and 3.12 | 2026-10-20 | `unittest` |
| Mutations | 665 recorded across 68 files. Since 2026-10-01 the suite fails when a code change leaves any of them unable to run, which two commits had done to 10, unnoticed. A survivor is closed by a new test, or, where the mutation changes nothing, replaced and recorded as such. Since 2026-10-17 each suite under the harness has twenty minutes, and one stopped there is reported timed out, never caught. Since 2026-10-20 the harness can try first the tests that name a mutation, the whole suite deciding only when they pass: Brief 17's 40 took 254 minutes one whole suite at a time, and 29 with its own 7 added | 2026-10-20 | `tools/mutations/`, run by `tools/mutate.py`; results in the session logs |
| Decision records | 61 (eight superseded), plus the rules for amending them. 188 dated Changes rows across 52 records, counted as rows under each record's Changes heading | 2026-10-17 | `docs/decisions/` |
| History | 212 commits on `main` with this session's record, the first on 2026-09-01 UTC; 32 session logs; one audit report in `logs/audit/` | 2026-10-19 | `git log`, `logs/` |

---

## How it was built

**Four seats, each a separate conversation with its own rules** (`docs/how-to/the-seats.md`):

| Seat | Who | Does | May not |
|---|---|---|---|
| Operator | Waqas Sharif | Drafts the skeleton of each design. Looks at the system from outside, as its user, and raises issues with simple solutions that the seats work into designs (his account; see the operator's role). Decides scope, cost, roles and anything that changes what the project is. Approves every override of a recorded decision. Relays between the seats | |
| Architecture chat | Claude, in a chat | Works the operator's designs through with him, concludes decisions, writes the records and the briefs | Write code, run the pipeline, commit |
| Implementing seat | Claude Code | Builds to briefs, tests, logs every session, keeps the state file current | Amend a decision beyond what the rules allow, push before the full suite passes, work around the scope floor |
| Audit seat | Claude Code, in a fresh chat | Audits a range of commits cold, read-only, and reports to the operator | Edit anything |

**Six independent audits by the audit seat so far:** two of documents (the writer's constraints, and the decision corpus) and four of code ranges. Each was run by an audit chat reading the work cold, with the operator routing its findings. Since 2026-09-30 each report is kept in `logs/audit/`, in the auditor's own words. The latest, on 2026-09-30, audited every new way out of the display:
- no deletion was wrong, and the paths that delete held;
- it found five defects, none yet triggered, and wrong documents; the seat corrected them on 2026-10-01, the defects first.

**The architecture chat's records are audited too.** On 2026-10-05 (2026-10-04 UTC), at the operator's request after a long session had been interrupted at a usage limit and resumed, an independent agent that had not seen the work audited that round's records and brief cold, over three rounds. Every figure taken from the seat's report matched it. The defects were overstatements and unmarked stale lines; each round's findings were corrected before the next, and the third round's few were corrected the same day (ADR-0059's Changes; the commit message of 2026-10-05 (2026-10-04 UTC)).

**The working method is written down and enforced:**
- **"Verify, do not trust."** Every claim, including a handoff or the seat's own memory, is checked with a command before anything is built on it. Every claim passed on is tagged verified or believed.
- **Decision records are never silently rewritten.** A change is annotated and dated in the record's Changes table. A change replacing the decision supersedes it with a new record.
- **One file says what exists and what is blocked** (`STATE.md`), and a pre-commit gate refuses implementation work that does not update it.
- **Every session writes a log**, indexed and chained backwards.
- **Every documented file is indexed** in a generated map, and a stale map blocks the commit.
- **"A check that cannot fail is worse than no check."** Each check is proved by the case built to defeat it.
- **A claim about the world is checked at its primary source.** The source research of 2026-10-04 (begun 2026-10-03 UTC) was followed by three independent passes reading the primary source behind every load-bearing claim, and the corrections they made are listed in the research record itself (`docs/research/0005-job-source-value.md`).

**Timeline, UTC.**

| Date | Milestone |
|---|---|
| 2026-09-01 | First commit |
| 2026-09-10 | Architecture 2.0, after a first design was rejected |
| 2026-09-11 to 09-16 | Feasibility: 16 platforms probed for a machine-readable feed and a publication date |
| 2026-09-17 | The first slice live on GitHub, and the first scheduled run |
| 2026-09-23 and 09-24 | The Airtable display filled, first in test, then in production |
| 2026-09-25 | The sweep live, in test and in production |
| 2026-09-26 | Full postings saved privately; the location and age rules; Himalayas moved to search |
| 2026-09-27 | A production failure: the second save of full postings failed on GitHub. Found in the morning's run log, reproduced, fixed and pushed the same morning, before the next run, with the postings it missed recovered by the next walk |
| 2026-09-28 | The architecture chat recorded the operator's decisions of the week in six new records, ADR-0051 to ADR-0056 |
| 2026-09-30 | The display bounded: an unreviewed row leaves after thirty days, the operator can clear any table himself, and a removed row stays removed for the reason it left. The aggregator's pushed-down filter and the contract check's own changes are now checked |
| 2026-10-01 | The fourth code audit's corrections: a confirmed clear removes only what its dry run listed, the aggregator check judges each posting on a later walk, places the operator can take are kept, and the suite fails when a mutation goes stale |
| 2026-10-02 | The level rule and the source's own place; the closure test's false marks on 47 open rows found and fixed |
| 2026-10-03 | The description read for years asked, a right to work required and on-site work. Closure raised to twelve runs after reposts were measured; the contract check ordered by time rather than date; every Confirmation clause of the nine newest records held by a test or marked live; Himalayas polled on both runs, its wait from publication measured; a guard refusing description text on the public branch; the clearing tool's dry run saying what is leaving anyway |
| 2026-10-04 | The end state decided (2026-10-03 UTC): version 1.0.0 is the system working for the operator himself, its sources chosen by their value to him (ADR-0059), on a research pass whose every load-bearing claim was checked at its primary source (research 0005). Each source's contract check isolated, so one source's failure reaches no other; the four employer platforms' yield measured on the registry's boards; Himalayas' date found to be its own listing date |
| 2026-10-05 (2026-10-04 UTC) | The round's records audited cold and corrected; version 1.0.0 given a file of its own, with the test for done the operator accepted (`docs/versions/v1.0.0.md`) |
| 2026-10-07 | The operator's answers built: the display read back so only what differs is sent; a posting with no date shown last; Manatal's nine boards polled, the first platform added by measured yield; on-site work read as Pakistani postings write it; a `Health` table for every contract finding and run failure; the clearing tool's calls counted |
| 2026-10-08 | Workable's six boards added, the first wave's second platform; the cassette tool made to sanitise a response's envelope |
| 2026-10-15 | Brief 11: Measure A met over its first two weeks; each platform given its own circuit breaker after Manatal's refusals stopped Workable's boards for a run; Manatal read twenty postings a page; a description opening the role to graduates anywhere asks no minimum |
| 2026-10-16 | Brief 12: the Airtable allowance measured, the pipeline's own ceiling set at 900 of the workspace's 1,000; ADR-0062's flow built, `applied`, `gone`, `Reason` and a row number; Himalayas' morning walk reads to the age limit; stored rows' facts re-read when the code that derives them changes |
| 2026-10-17 | Brief 13: the Senior change built and switched off for 2026-11-01, the level rule as a list of the levels that drop, Workable's level read, the description's four fields and a flag for a posting with none; SmartRecruiters' two boards added, each description asked once; the mutation harness given a time limit after two stalls |
| 2026-10-17 | Brief 14: Ashby's two boards added, the last of the first wave's four platforms, a republished posting keeping its first date through the stores; the morning walk of Himalayas read to the age limit from 2026-10-18 |
| 2026-10-18 | Briefs 15 and 16: the second wave measured for who reads the application, then built, Hacker News first, then Jobicy, RemoteOK and We Work Remotely; an on-site post on Hacker News in a place the rule cannot name dropped; every run log naming its commit; four employer boards found through the second wave |
| 2026-10-19 | Brief 17: `Jobs` read once a run for the projection and the sweep; the rejection tables read only when a step needs them; who reads the application read from every description, measured over all 5,750 saved, and built to show in `Jobs` |

---

## The operator's role

**The division of work.**
- **He is both its builder and its user.** As its user he views it, in his phrase, "from outside the box": he raises an issue and a simple solution, works it with the architecture chat into a decision record, and the implementing seat builds it into code. *(Reworded 2026-10-19; that he is its builder as well as its user is his account of that day.)* *(His account to the architecture chat; no record holds the phrase.)* The age rule is the clearest case below. In his account, a date is absolute only at the moment of the fetch and relative afterwards, which became the rule that a posting is judged once, when first seen. ADR-0052 holds the rule, the record's own phrasing of that point, and his words on why it matters.
- **The design starts with him.** He drafts the skeleton of each design himself and works it through with the architecture chat: they discuss it, improve it, and the chat writes the decision records from the result.
- **He architects it:** each design he drafts carries its algorithms, flow, integrations, logic, edge cases and contingencies, and he reviews the work at that level, through the logic, the flow, the tests and the algorithms. Implementation is delegated, for speed, to Claude Code, the implementing seat, which builds to briefs he approves under a working method he designed; review of the code itself is delegated to the audit seat, which audits ranges of it cold. *(Reworded 2026-10-19. What a design carries, the reason for delegating and where code review sits are his account, 2026-10-19. Recorded examples of rules he set: the age rule, ADR-0052; the location rule, D13; the Delete field, D12; the three-year limit, ADR-0058.)*
- **Whether it is right is his:**
  - he audited it by using it;
  - he caught mistakes in what the seats built and proposed, and corrected them;
  - he made every decision that changed what the system does.

Each dated item below has its source in the session log of that date. The design process is his own account, 2026-09-27, and is not recorded in any repository file, since the architecture conversations are not. The architecture chat was asked to check it and add what it knows. It did so on 2026-10-05 (2026-10-04 UTC): each item it added names its source, a decision record or the commit history, or is marked as his account to the chat where no record holds it.

### He defined and designed it

- **He architects it:** the skeleton of a design is his, developed with the architecture chat into the records (his account, above).
- **The problem and the measure of success are his:** the week lost to searching by hand, the three-to-six-day baseline, and freshness as the one binding measure. `docs/architecture-2.0.md` carries his name; the measure is ADR-0015.
- **The scope floor is his standing decision,** with no record behind it: no user interface, no notifications, no paid services.
- **What version 1.0.0 is.** 2026-10-04 (2026-10-03 UTC): the system working for him, as he intends; working for others is a later version. He set what makes a source worth having, genuine postings, fairness to applicants and time to get hired, ruled that a recommendation without evidence counts for nothing, and ruled that a better source is integrated first and never moved up the display. 2026-10-05 (2026-10-04 UTC): he accepted the test for done (ADR-0059).
- **When the description should be read.** 2026-10-02: "high time that we use the description", for the three things that stop him applying even when a posting passes every other rule: the years of experience asked, a right to work somewhere he cannot, and on-site work the location field does not state. He set three years as the most he will consider and preferred counting like required, and on 2026-10-03 a line welcoming fresh graduates as setting no minimum (ADR-0058).
- **The design drew on his earlier projects.** A LinkedIn job pipeline of his had run over 100 times on scheduled commits, and his Rahzaan project's patterns were read into this one. A research pass found his own earlier repository the strongest source for how to document a project like this (`docs/research/0004-project-context-documentation.md`).
- **The working method is his:**
  - the four seats, with every brief and audit relayed through him;
  - a fresh, cold audit chat when an audit matters;
  - a session ending only when he says "close this chat".

  Where a seat had written down its own guess at these rules, he replaced it with his (`docs/how-to/the-seats.md`, Changes).

### He audited it by using it, and found what the seats had not

- **2026-09-24, the first day rows appeared.** He marked postings that should not have been there. He named three roles he had not found searching by hand, one of which he may have seen once. That met the slice's acceptance test (ADR-0009).
- **2026-09-24.** He asked why rows he had marked had not reached their tables. That question, and his wish to see a mark land "immediately", is why marks are now copied on every run rather than once a day.
- **2026-09-26.** He saw postings restricted to the US or Canada in his table. That became the location rule (D13), with its measurement: 93 of 100 Himalayas postings were closed to him.
- **2026-09-26.** He saw postings older than he would apply to. He refused the filtered view the seat offered as wasted effort, and set the one-week rule (D14).
- **2026-09-26.** He judged that postings reappearing under years-old dates were harvesting CVs, so the original date stands. Measured afterwards: 60 of the 83 Greenhouse postings already a week old at first sight were one role, reposted city by city since 2024.
- **2026-09-26.** His laptop running hot during a session led him to require that seats check for, and close, any background work of their own before finishing.

### He caught errors in what the seats built or proposed

- **The age rule was built wrong.** 2026-09-26: the seat judged a posting's age against each run's clock, so a row admitted today would vanish a week later, possibly before he had seen it. He caught it from the seat's description alone and restated the rule: age is judged once, at first sight. His words: "i might not see the table for a few days then it would mean some posts will be out without my knowledge which i do not want" (ADR-0052). It was rebuilt the same day.
- **An aggregator was fetched mostly as waste.** 2026-09-26: he asked why the feed could not be trimmed before fetching. Answering that, the seat re-measured the search endpoint it had rejected on 2026-09-16, and found the rejection had tested the wrong parameter. The move to search took the feed from a third read, 93% of it irrelevant, to every relevant posting.
- **A deletion flaw.** 2026-09-26: the latest audit found that clearing or changing a `Status` would delete his record of a role he had applied to. He did not take the proposed fix as given. He designed his own: a `Delete` field whose only choice is yes, empty meaning keep, and every store kept forever (D12).
- **What is stored.** 2026-09-25: two records disagreed, one keeping every field and one keeping metadata only, and the code had followed the second. He settled it for keeping everything, because a fetch can fail or come back without its description (D11). Where to keep it was settled on the seat's recommendation: privately, checked by reading it back.
- **How the seats work together.** 2026-09-18:
  - A seat reverted another seat's deliberate change instead of flagging it. He corrected that, and "flag, never revert" now binds every seat.
  - He had the seat build a guard against a shell hazard that kept recurring, rather than write another rule about it.
  - He had it write down the steps for the tokens, which it had left him to work out.
- **The order of work.** 2026-09-18: he had test rows put into the display before the code that writes it was built. That way a display that could never fill would show at once, not after the build.
- **Care before a risky change.** 2026-09-24: a "Sênior" title had slipped past the seniority rule. He approved stripping accents from titles only if every title's verdict was compared before and after. Of 1,458 titles, exactly one changed: that one.
- **Where the guard tests run.** 2026-09-25: he questioned putting the tests that guard the architecture in a separate suite. They went into the ordinary one, which always runs (ADR-0049).
- **Whether interrupted work was right.** 2026-10-05 (2026-10-04 UTC): a long session had stopped at a usage limit and been resumed, and he asked for its output to be checked rather than trusted. The files matched what was written, but an independent audit then found overstatements and stale lines in the records, corrected the same day (ADR-0059's Changes; the commit message of 2026-10-05 (2026-10-04 UTC)).

### He made the decisions that set what it does

- **His targets.** The role families and their order; the seniority rule, after asking for evidence that levels II and III expect more than his three years.
- **Retention.** The fifteen days and their two clocks; closed postings shown for fifteen days, then stored.
- **Clearing the display himself.** 2026-09-28: he asked to clear any table by age, a week, fifteen days or a month, for a fresh start once he judged the system right. The seats worked it into the clearing tool, dry run first, and he kept it beside the thirty-day clock: "one is just to maintain while the other is manual meaning i can run whenever i want so keeping both should be reasonable" (ADR-0055).
- **Who the system keeps.** Job type never filters: internships, contracts, part-time and volunteer roles all stay, since volunteering "might be a good opportunity and can become a stepping stone". A time zone about working hours never excludes, since he is open to working any hours; a time zone used as a residence requirement is a location restriction in substance, and when measured, 14 to 18 of the 2,271 saved postings used one, depending on how a phrase is read, and every one was already dropped by another rule, so no rule was needed (ADR-0057).
- **Closure and cadence.** 2026-10-03: a posting closes after twelve runs absent, about six days, once postings that leave a board and return were measured, after 23 to 130 hours (ADR-0050); Himalayas is polled on both runs, his yes "if justified" on the measured wait (ADR-0048).
- **The `Status` values** named after their tables. He renamed them in the browser, so no mark was lost.
- **Failure handling.**
  - The public display always updates, even when the private store fails, and such a failure must reach him (D9).
  - Three failed display updates in a row mark the run failed (D1).
  - Runs queue rather than drop: "I do not want anything to be dropped".
- **Records.** The record standard is followed rather than bent: ADR-0046 was replaced only at its eighth amendment, by ADR-0050. *(And ADR-0050 by ADR-0062 at its eighth, 2026-10-16.)* 2026-09-28: a record's two-hundred-line limit is soft, and a threshold not yet reached is not reported at all: "when the conditions are met only then the consequence will trigger and there is no near so just do it" (ADR-RULES). *(2026-10-10: the hard flag on length is at 300 lines, and his cross-project Decision Record Standard now says the same.)*
- **Permission to push.** The implementing seat may push its own commits after the full suite passes (D10).
- **The operator's answers of 2026-10-07**, each built that day or the next:
  - **A posting with no date is shown last, never skipped:** "if a job board does not offer dates then we can make a simple new rule that those that do not have dates are at the end because no job should be skipped" (ADR-0007's Changes).
  - **The display sends only what differs.** He accepted the seat's read-back with "recommendation accepted but you should check if this raises new problems". The check found that it reversed a recorded ruling and cost more calls than the recorded design, about 250 a month against 100; put back to him with both, he kept the read-back (ADR-0060).
  - **A table for the system's health:** "i think general health is good but only if the cost is not a lot". Every contract finding and every failed fetch run becomes a row, at a few calls a month. He set its two secrets on 2026-10-08, and the evening fetch that day wrote its first 17 rows (ADR-0061).
  - **Manatal's career-site endpoint for all nine of its boards**, chosen once the documented endpoint was found to give no working link to a posting, and **Workable's four new slugs**, added marked unproven: "add them as long as they are good and are useful" (ADR-0059's and ADR-0029's Changes).
- **His answers of 2026-10-09:** a posting with no date counts as passing when platforms are compared, "if the post is genuine then i would like to see it"; the levels Workable and SmartRecruiters state are to be read, Mid-Senior level kept for now (ADR-0032; built 2026-10-17, Workable's and SmartRecruiters' levels read); Himalayas' own listing date accepted for 1.0.0 (ADR-0052); SmartRecruiters before Ashby (ADR-0059).
- **His answers of 2026-10-10:** every level from the start of a career up to mid is kept on every source, whatever it is called, internship included, "so that no job skips my sight that i am eligible for" (ADR-0032; built 2026-10-17); Himalayas kept, its trial over, "it has proven itself to be worth keeping".
- **His answers of 2026-10-16:** Senior no longer drops a posting, neither the word in a title nor a source's stated level, while every other seniority word in a title and every stated level above Senior still do, and the description decides the rest: "if there is senior written in title then it should not drop until the description is read" (ADR-0032; built 2026-10-17 and switched off until November 1). A `Status` value of his own for a posting he finds gone, which also lets the system count how many die before he applies (built 2026-10-17, ADR-0062). Banyan Canopy kept. EWOR GmbH's postings and the "(100 % remote) (m/f/d)" title template are watched for a week before he decides which, if either, to exclude, and a daily check for Himalayas postings removed early waits the same week. In this file, when in doubt whether a change is the point, the old value stays. Later the same day, on the resume-tailoring chat's proposals, he agreed to: the values the description yields shown in `Jobs`; a `Status` meaning applied and a reason field in `Jobs`, "yes, do it now", to be designed and built with the gone status; a fixed row number in `accepted` and `Jobs`; the new names left to the implementing seat, so long as they are as easy to understand as `gone` and `applied`; and two weeks of counting the Senior rows kept and how many he accepts, "it is correct to check for 2 weeks." The larger proposals wait for the numbers. *(2026-10-17: the flow, the reason field and the row numbers built and live; the description fields and the Senior change built and switched off until November 1.)*
- **His answers of 2026-10-16 on the allowance and the Senior switch-on** (ADR-0062, ADR-0040, ADR-0053, ADR-0032): the pipeline's own monthly ceiling at 900 calls, the rest of Airtable's 1,000 left to the chats, "900 for now and subjective to the condition that if jobs are missed then will think about it unless i am misunderstanding the number.", confirmed once told that reaching it delays the display and loses nothing, with his Usage count as what he watches; the Senior change switched on after stored rows' facts are re-read from their saved postings whenever a rule changes, on November 1 or sooner by the chat's recommendation; the morning Himalayas walk read to the age limit; and the evening run's Airtable work kept unless a projection a week on shows October short. *(2026-10-17: the ceiling, the re-read and the deeper walk built; the Senior switch-on waits for November 1.)*
- **His decisions of 2026-10-17:** SmartRecruiters' `releasedDate`, which SmartRecruiters does not define, trusted as the publication date on the seat's measurement, as the seat's report on Brief 13 records (ADR-0059); and the go for Ashby, in his words to the chat, "yes do your work and proceed so that the seat may start its work."
- **His decisions of 2026-10-18** (ADR-0063, which supersedes ADR-0059, and ADR-0057): version 1.0.0's test set, Measure A over four weeks from November 1 and the tables used over the same weeks; a dropped posting's reason recomputed rather than stored, with every run log to name the commit that ran it; and the second wave chosen by who reads the application as well as by yield. That came from his own conclusion about his rejections, untested, that recruiters screen on years where "founders, engineers and people who are of my stack or who understand these technical aspects are looking for skills and technical and not experience or years." Hacker News, where the measurement found an address to write to in 77 of 266 posts and 16 written in the first person by a founder, CEO, CTO, engineer or hiring manager, is built first and at once, with Jobicy, RemoteOK and We Work Remotely after it: "building should be done right now and not in november and if quota is an issue then just do not do api call and only build." Its on-site posts in cities the rule cannot place are closed; the four employer boards it led to are added; Breezy is read once on its undocumented endpoint. *(As of 2026-10-18 none is built.)* *(2026-10-19: all built, the four feeds before November 1; Breezy read and out.)*
- **His decisions of 2026-10-19** (ADR-0063, ADR-0058, ADR-0035, ADR-0060, ADR-0062, ADR-0057): Breezy out of 1.0.0, "as long as that result was conclusive", on one read that kept none of 193 postings; who reads the application shown in `Jobs` at once rather than from November 1, "this needs switching now as i should know  the founder ones separate as targeting those might yield much better results and people claim that as well."; one read of `Jobs` serving both the projection and the sweep, and the rejection tables read only when needed, about 180 of a month's calls saved between them by the seat's estimate *(2026-10-20: about 155, 120 estimated and 35 measured, both built 2026-10-19; `Who reads` built 2026-10-20, a label on 281 of 5,750 saved descriptions, a founder on 12)*; no exclusion for EWOR's templated postings, which today's rules already keep out, to be confirmed after the walk of about 2026-10-23; and no rule for a single post remote but based in one US city, "have to be careful as to not drop even a single post as that might be a legitimate job that i might be eligible to apply for."
- **His decisions of 2026-10-20** (ADR-0063, research 0006): every source with a posting he can take is to be built, "the end goal is the same that from wherever i can get a job post of my meaning, i will get it." The sources came by a research method of his: an outside research run, each of whose decisive claims the architecture chat tries to falsify against evidence no staler than the claim's own. Over three reports it kept Python.org's job board, Hasjob, Startup.jobs and CryptoJobsList, and dropped seven others. Wellfound, Y Combinator's Work at a Startup and Algora, whose terms bar automated reading, stay his to use by hand until he finds a way "without repurcussions". From then on his own search turns to the postings a founder or an engineer reads, which `Who reads` labels: "i will shift my focus to the founder/technical people ones from now on". *(As of 2026-10-20 none is built.)*

### And he did what only he could

- Created the tokens and secrets, and added the Airtable fields and choices the connector cannot.
- Ran every live check: each test-mode and production dispatch.
- Relayed every brief, report and audit between the seats, and decided what each seat's findings meant.

---

## What it does not do, and its limits

**Excluded by decision, the scope floor (`CLAUDE.md`):**
- no scoring, ranking or machine-learning classification;
- no user interface;
- no notifications beyond GitHub's own failed-run email;
- no reading of email job alerts;
- no paid service.

**Limits as of 2026-10-02; the sources and the end state as of 2026-10-09 UTC:**
- **Sources.** Thirty-four employer boards, nine of them Manatal's since 2026-10-07, six Workable's since 2026-10-08, two SmartRecruiters' since 2026-10-17 and two Ashby's since 2026-10-17, and four found through the second wave since 2026-10-18 (LiveKit, ClickHouse and Mastra on Ashby, PostEra on Lever); one aggregator; and, since 2026-10-18, Jobicy, RemoteOK and Hacker News' thread and job stories, and We Work Remotely since 2026-10-19, ADR-0063's second wave, Hacker News first, whose free-text posts give their place only in their first line: an on-site post there in a place the rule cannot name is dropped, an exception for that source (ADR-0057). Since 2026-10-20, from research 0006, Python.org's job board, whose feed carries no date, so its postings sort after every dated one, and Hasjob, India-centred, its postings signed by their employers; and Startup.jobs through its keyed API, about 585 remote jobs a day, of which today's rules keep about 3, its postings kept past the seven days its API terms set, the operator's decision (ADR-0063's Changes). *(Until 2026-10-18 this said thirty boards and one aggregator.)* *(2026-10-17: Ashby built. Of its 33 postings that day, today's rules kept none, as of SmartRecruiters' 20 the same day.)* SmartRecruiters and then Ashby, which tied under the measured rule, were built in the operator's order, given on 2026-10-09 *(until 2026-10-17 this said twenty-eight boards and named the two as coming next)*; Breezy waits for a documented public endpoint (ADR-0059, which replaced ADR-0029's order on 2026-10-04 (2026-10-03 UTC)). The registry holds 53 boards. On-site roles in Karachi are thin: Rozee.pk, the main Pakistani board, has no API and its privacy policy forbids automated use, so it stays his to use by hand (research 0005, `docs/deferred/rozee-pk.md`).
- **Matching reads titles only**, so a role whose title misses the pool is missed. Descriptions are read since 2026-10-02, but only for what stops him applying. They are read by fixed phrases, so a requirement worded in a way not yet measured is missed, and the posting stays in his table. Himalayas' own level label is read since the same day. Since 2026-10-16 a stored row's levels and description facts are read again from its saved posting whenever the reader or a rule that reads them changes, so rows stored before then are judged by today's rules too; the first re-read, on 2026-10-17, read 4,945 saved postings (ADR-0040). *(Until 2026-10-17 this said rows stored before then carry neither, and keep their verdict.)*
- **Duplicates across sources are not merged.** An employer's own posting and an aggregator's copy of it can both appear, because the aggregator stamps its own date.
- **Lever's date is not proven to mean publication**, so Lever postings are never dropped for age.
- **GitHub starts scheduled runs 3.3 to 7.0 hours late**, over the 29 scheduled runs to 2026-10-01. Freshness is measured from publication, so it includes that delay.
- **Unbuilt:** the priority star (a mark on postings sharing a named attribute with an accepted one, ADR-0044), which waits for a version after 1.0.0. The contract check's Airtable row, which 1.0.0 requires, was built on 2026-10-07 as a `Health` table for contract findings and run failures alike, and has reached Airtable since the operator set its two secrets: its first rows were written on 2026-10-08 (ADR-0061, which supersedes ADR-0036). The cheaper projection, sending only what `Jobs` does not already show, was built on 2026-10-07, when a week's measured intake put the display past what the month's calls could carry (ADR-0060, which supersedes ADR-0056).
- **The clearing tool and the thirty-day clock have not run live yet**; both are proved offline.
- **"Finished" is defined** since 2026-10-04 (2026-10-03 UTC) as version 1.0.0 (ADR-0059, superseded by ADR-0063 on 2026-10-18), and since 2026-10-05 (2026-10-04 UTC) it has a file of its own, `docs/versions/v1.0.0.md`, with the test for done he accepted that day. Until then it was open by decision (ADR-0023).
- **The private store's token expires on 2027-01-01**; the operator rotates it before then.

---

## Highlights

Short, role-neutral statements a reader can take as they are. Every figure is from the table above.

- Built an unattended job-discovery pipeline on GitHub Actions and Python (standard library plus `requests`). It polls employer job boards twice a day and shows only eligible, matching postings in Airtable, at no recurring cost.
- New postings are first seen a median of 5.4 hours after publication, and 90% within 10.5 hours, against targets of 24 and 72 hours, over 114 postings.
- 30 production runs over 13.6 days with no retries and no failed requests, reading 803 to 1,420 postings a run and, under the location and age rules, keeping 5 to 56.
- Every posting is admitted or dropped by a named, deterministic rule, and every drop is logged. There is no model and no scoring.
- Git branches serve as the database, with privacy enforced in code: employers' description text and aggregator data never reach the public repository. Every posting is saved in full to a private repository, verified by read-back.
- A classification workflow: the operator's marks are copied to their own tables and stored permanently. Rows are deleted from the display only after the store is read back from the remote. The display is bounded by a thirty-day clock and a dry-run-first clearing tool.
- A day's worth of an aggregator's feed went from about a third read, 93% of it irrelevant, to all of the relevant postings, by moving to a filtered endpoint an earlier measurement had wrongly rejected.
- 893 tests, and 533 mutations that deliberately break the code to prove the tests notice.
- Assessed candidate data sources by evidence of their value to the user, genuine postings and a fair route to the employer, rather than by their reach, with every load-bearing claim checked at its primary source, and set the integration order from that.
- Designed by the operator and built with AI agents in separate roles: architecture, implementation, and cold, read-only audit. The work was carried out under a written verification discipline and produced 55 decision records and 24 session logs.

---

## Where the evidence lives

| For | Read |
|---|---|
| How to set it up and run it | `README.md` |
| Where it is going, and what is left for version 1.0.0 | `docs/versions/v1.0.0.md` |
| Which sources, and why | `docs/research/0005-job-source-value.md` |
| What exists now and what is blocked | `STATE.md` |
| What was finished, with proof | `docs/reference/completed.md` |
| Why the system is shaped as it is | `docs/architecture-2.0.md` and `docs/decisions/` |
| What each session did | `logs/README.md`, then the log it names |
| Every documented file | `MAP.md` |
| The live numbers | The run logs on the `data` branch, read with `tools/run_log_report.py` and `tools/publication_lag_report.py` |

## Keeping this file current

**Add or update, never remove, both seats.** The operator's rule, accepted by both seats on 2026-10-10 and 2026-10-15: a line no longer true is updated in place with its date, so a reader sees how a figure changed and nothing here becomes false. *(Until 2026-10-15 this section said to remove a number that could no longer be measured.)* *(2026-10-16, the operator: when in doubt whether a change is the point, the old value stays.)*

**At the close of any session that changes a capability or a measured number:**
- update the section it belongs to and the date at the top;
- re-measure a number rather than carrying it forward, and replace it in place with its new date and source; keep the old value beside it only where the change is itself the point, a before and after or a correction, never as a running trail of counts that grow every session, and when in doubt, keep it;
- mark a number that can no longer be measured, or a claim overtaken, in place with the date and why;
- record a limit that is removed where it was listed, with the date.
