---
type: explanation
description: Everything the system is and does, in one file. Its purpose, how a run works end to end, the stack, its engineering qualities, measured numbers with their sources, how it was built and by whom, and its limits. Written so that reading it stands in for reading the repository. Kept current.
status: current
---

# Capabilities

**What this file is.** Everything this repository is and does, in one place, for a reader who will open nothing else. Two readers are expected:
- a person who wants to know what the system offers;
- a chat drafting a CV, which should find every usable fact here without reading the tree.

**Current as of 2026-09-30 UTC**, against `main` at `19ca94d`. Every number carries its date and its source. A number that could not be measured is not here.

**Kept current.** Updated at the close of any session that changes a capability or a measured number. Sections that restate a decision name the record that holds it, so a reader who wants the reasoning can find it.

---

## In one paragraph

A personal job-discovery pipeline that runs itself.
- **Twice a day**, on GitHub Actions, it reads the public job feeds of eleven employers' applicant-tracking-system (ATS) boards, and one aggregator narrowed to postings open to Pakistan.
- **It keeps every posting it fetches, permanently.**
- **It admits only postings the operator can use:** his target roles, his level, places he is eligible to work, and at most a week old when first seen. Each posting is admitted or dropped by a named, deterministic rule.
- **It shows what survives in an Airtable table.** The operator marks each row accepted, not a fit, or poorly filtered. The pipeline copies each mark to its own table, stores it for good, and clears the display after fifteen days. A row he never marks leaves after thirty, and he can clear any table himself, dry run first.
- **It costs nothing to run.** A new posting reaches the table a median of 5 hours after its employer publishes it.

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

## What a run does, end to end

1. **Starts on a schedule.** Two GitHub Actions workflows:
   - **Fetch.** Scheduled for 00:00 and 13:00 UTC; GitHub starts them late, measured at 03:27 to 03:59 UTC and 16:56 to 17:47 UTC. It also runs on a manual dispatch, which can be ticked as a test run that writes only to separate test branches and tables.
   - **Contract check.** Daily at 06:30 UTC.

   Each fetch runs the full test suite before touching any data.
2. **Restores state.** The run loads what the stores already hold, so it appends to the stored history rather than to whatever the last machine saw:
   - from the public `data` branch;
   - from a second, private repository, for aggregator data.
3. **Fetches.** All fetching goes through one shared HTTP module:
   - retry with backoff;
   - a request budget of 500 per run, counting every attempt including retries;
   - a circuit breaker on consecutive failures.

   **Adapters are per platform, never per employer:** one Greenhouse adapter serves nine boards. An adapter only parses; it never fetches. The aggregator, Himalayas, is paginated. It is read newest first and stops at the first page that is either wholly older than what that board has already stored in full, or wholly older than the age limit. A 40-page cap guards against a runaway.

   **The aggregator's own filter is checked every morning.** Himalayas is asked only for postings open to Pakistan, which hands part of the location rule to a third party. So one page of its whole feed is read beside the search. A posting the search never returned, but the location rule would admit, is a disagreement: counted in the log and named in the private store (ADR-0053).
4. **Normalises** every posting to one row shape. The publication date and the moment the pipeline first saw the posting are recorded as separate fields, never confused. Where the employer name or URL is derived rather than given, the row says so.
5. **Stores the raw layer.** Every posting never seen before is appended permanently, before anything is judged, and nothing is ever rewritten. So a filter mistake is recoverable: the rows it missed are still stored.
6. **Filters**, cheapest rule first. Every drop is logged with the rule that caused it. The rules (the chain is in `src/filters.py`):

   | Rule | What it drops | Source of truth |
   |---|---|---|
   | Expiry | A posting past its stated expiry | The posting |
   | Experience | Built and switched off: no board gives years of experience as a field, and the operator deferred the rule until filtering reads descriptions | `src/filters.py` |
   | Annotation vendor | Postings from data-labelling vendors | `docs/reference/annotation-vendors.md` |
   | Title | Titles matching none of 79 terms in four role families: agentic AI, LLM and applied AI, traditional AI and ML, software engineering | `docs/reference/title-pool.md` |
   | Seniority | Titles carrying a senior-level word (senior, staff, lead, principal, II, III and others) | `docs/reference/seniority-exclusions.md` |
   | Location | A posting only when *every* place it lists is closed to the operator. Examples: other countries only; a region without Pakistan; on-site in a Pakistani city other than Karachi. Anything unclear is kept | `config/eligibility.json` |
   | Age | A posting published more than 7 days before the pipeline first saw it. Judged once, at first sight, so an admitted row never ages out unseen | `config/eligibility.json` |

   Title matching normalises both sides: case, punctuation, accents and plurals. Spelling variants such as "fullstack" and "full stack" are listed as terms of their own.
7. **Groups duplicates** by employer, normalised title and publication date. One role posted 134 times, once per city, becomes one display row listing every city.
8. **Appends the filtered layer**, the rows that passed. When a rule widens, a backfill appends the rows it now admits, inside every run.
9. **Saves every posting whole, privately** (the operator's D11). This includes the description text and every field the board returned. It goes to the private repository's `data-full` branch, one file per run. The file is read back by a fresh fetch and compared by content hash, and only then is each posting marked saved. A failed save is retried on the next run.
10. **Projects to Airtable**, the only screen the operator opens:
    - an upsert matched on the posting's identity, ten rows per call;
    - only the pipeline's own fields are written, never the operator's `Status`;
    - anything he has already classified is skipped, so it never comes back.
11. **Sweeps the display**, under ADR-0050:
    - **Every run:** copies each newly marked row into its classification table.
    - **Every morning:** marks postings that have closed. It writes a row to a permanent store when its time comes:
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

**The contract check** fetches one response per platform. It fingerprints the shape of exactly the fields each adapter reads: present or absent, type, null or not. It reports any change by field name. That tells a board that changed its API apart from a board with no new jobs (ADR-0018, ADR-0036). A change we caused ourselves, such as a new endpoint, is recorded in configuration with its date and cause and reported as ours, so it never reads as the board moving.

**The clearing tool** is the operator's, run from the same workflow by hand (ADR-0055). He chooses a table and an age in days: publication date for `Jobs`, the date he classified for the other tables. The first run is a dry run: it reports what it would remove and changes nothing. A confirmed run is refused unless a dry run of the same request ran within two days. It writes the stores and deletes nothing itself, so the next sweep removes the rows only after reading those records back. On `accepted` it only sets `Delete`. A row deleted by hand in Airtable would come back; one cleared this way does not.

---

## How data is stored, and where it may go

**Three layers**, each derived from the one before (ADR-0001, ADR-0013):

| Layer | Holds | Where |
|---|---|---|
| Raw | Every posting ever fetched | Git branch |
| Filtered | Every posting the rules admitted | Git branch |
| Display | The current projection of the filtered layer | Airtable. Never authoritative: losing it costs a screen, not data |

**Git branches are the database.** There is no hosted database (ADR-0002):
- **Public `data` branch:** employer-board metadata only, never description text (ADR-0011). Nothing from the aggregator either, because aggregator terms restrict redistribution (ADR-0020). The code refuses to commit a file holding either.
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
| Safe to clear | A bulk removal runs dry first, is refused without a recent dry run of the same request, writes before anything is deleted, and never deletes from the table of roles applied to |
| Self-diagnosing | The daily contract check, per-board run logs including zeros, the month's call budget, and escalation after the push |
| Change safety | Every guarantee has a test, and every test that guards one is proved by a mutation that breaks the code and must fail it. Architectural rules are guarded by fitness functions in the ordinary suite (ADR-0049) |
| Cost | Nothing recurring: GitHub Actions is free on a public repository, and Airtable is on its free plan |

---

## Measured numbers

Each is measured, with its date and source. `data` is the public data branch.

| What | Value | Measured | Source |
|---|---|---|---|
| Production runs | 28, from 2026-09-17 to 2026-09-30, a span of 12.6 days | 2026-09-30 | Run logs on `data`, `tools/run_log_report.py` |
| Fetch reliability | 0 retries, 0 failed requests, 0 runs near the request ceiling, across all 28 runs | 2026-09-30 | Same |
| Requests per run | Median 36 against a ceiling of 500, at most 41; 11 on an evening run | 2026-09-30 | Same |
| Postings read per run | 824 from the eleven boards; 1,283 with Himalayas | 2026-09-26 and 09-27 | Those runs' logs |
| Postings fetched in total | 32,831 across 28 runs, repeats included | 2026-09-30 | Run logs |
| Distinct employer-board postings stored | 1,012 | 2026-09-30 | `seen.json` on `data` |
| **Freshness (Measure A)** | New postings first seen a **median 5.4 hours** after publication, **90th percentile 10.5 hours**, maximum 14.4, over 114 postings. The targets are 24 and 72 hours | 2026-09-30 | `seen.json` and run logs on `data`. Counts only postings published after the run before the one that saw them |
| Selectivity | Of 1,283 postings read, 36 kept: 922 dropped on title, 258 on location, 56 on seniority, 11 on age | 2026-09-27, morning run | Run log |
| Deduplication | 824 postings grouped into 527 display rows; the largest group, one role posted 134 times, once per city, became one row | 2026-09-26 | Run log |
| Himalayas before the change | 500 postings a morning, the page cap, from about 1,600 published a day (inferred from 499 new postings spanning 7.3 hours). 93 of 100 postings sampled from the feed were closed to Pakistan | 2026-09-26 | Run logs, and a live sample of 100 postings |
| Himalayas after the change | Only postings open to Pakistan requested. The first morning read back a week, 460 postings in 23 pages, stored 361 new and kept 31 | 2026-09-27 | Run log |
| Himalayas completeness | Of the 420 postings a week-long read of the search held, published before the morning walk, the pipeline had stored all 420 | 2026-09-30 | A 26-page snapshot against the private seen store |
| Location rule, its owed check | Exactly 74 of the saved 91 Himalayas postings dropped and 17 admitted, as the record predicted nine days before the rule was built | 2026-09-30 | ADR-0041's Confirmation, on `raw_responses/` |
| Full postings saved privately | 824 postings in one 9.8 MB file, read back and matched by content hash | 2026-09-26 | Run log |
| Airtable usage | 172 of the month's 1,000 calls, 17%; `Jobs` holds 89 rows; a projection costs 8 calls | 2026-09-30 | Run log |
| Display intake | About one new display row a day under the current rules, so the display settles near thirty rows and the cheaper delta projection is not yet needed | 2026-09-29 and 09-30 | Run logs, against ADR-0056's trigger of 100 |
| Recurring cost | None | 2026-09-27 | Free plans only |
| Feasibility research | 16 ATS platforms probed; 1,646 postings across the first 11 boards | 2026-09-11 to 09-16 | Spike logs |
| Code | 25 source files, 6,123 lines; 32 test files, 9,574 lines; 9 tool files, 1,817 lines | 2026-09-30 | `git ls-files`, `wc` |
| Tests | 702, passing on Python 3.11 and 3.12 | 2026-09-30 | `unittest` |
| Mutations | 354 recorded across 29 files, re-run when the code they guard changes. A survivor is closed by a new test, or, where the mutation changes nothing, replaced and recorded as such | 2026-09-30 | `tools/mutations/`, run by `tools/mutate.py`; results in the session logs |
| Decision records | 55 (four superseded), plus the rules for amending them. 124 dated Changes rows across 42 records | 2026-09-30 | `docs/decisions/` |
| History | 115 commits on `main`, the first on 2026-09-01 UTC; 22 session logs | 2026-09-30 | `git log`, `logs/` |

---

## How it was built

**Four seats, each a separate conversation with its own rules** (`docs/how-to/the-seats.md`):

| Seat | Who | Does | May not |
|---|---|---|---|
| Operator | Waqas Sharif | Drafts the skeleton of each design. Decides scope, cost, roles and anything that changes what the project is. Approves every override of a recorded decision. Relays between the seats | |
| Architecture chat | Claude, in a chat | Works the operator's designs through with him, concludes decisions, writes the records and the briefs | Write code, run the pipeline, commit |
| Implementing seat | Claude Code | Builds to briefs, tests, logs every session, keeps the state file current | Amend a decision beyond what the rules allow, push before the full suite passes, work around the scope floor |
| Audit seat | Claude Code, in a fresh chat | Audits a range of commits cold, read-only, and reports to the operator | Edit anything |

**Five independent audits so far:** two of documents (the writer's constraints, and the decision corpus) and three of code ranges. Each was run by an audit chat reading the work cold, with the operator routing its findings. The latest audited the first code that deletes anything:
- all 86 of its mutations were caught;
- it found four defects, none yet triggered, all closed within a day.

**The working method is written down and enforced:**
- **"Verify, do not trust."** Every claim, including a handoff or the seat's own memory, is checked with a command before anything is built on it. Every claim passed on is tagged verified or believed.
- **Decision records are never silently rewritten.** A change is annotated and dated in the record's Changes table. A change replacing the decision supersedes it with a new record.
- **One file says what exists and what is blocked** (`STATE.md`), and a pre-commit gate refuses implementation work that does not update it.
- **Every session writes a log**, indexed and chained backwards.
- **Every documented file is indexed** in a generated map, and a stale map blocks the commit.
- **"A check that cannot fail is worse than no check."** Each check is proved by the case built to defeat it.

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

---

## The operator's role

**The division of work.**
- **The design starts with him.** He drafts the skeleton of each design himself and works it through with the architecture chat: they discuss it, improve it, and the chat writes the decision records from the result.
- **The code and the audits are the AI seats' work:** the implementing seat writes the code and the audit seat audits it.
- **Whether it is right is his:**
  - he audited it by using it;
  - he caught mistakes in what the seats built and proposed, and corrected them;
  - he made every decision that changed what the system does.

Each dated item below has its source in the session log of that date. The design process is his own account, 2026-09-27, and is not recorded in any repository file, since the architecture conversations are not. The architecture chat is asked to check it and add what it knows.

### He defined and designed it

- **He architects it:** the skeleton of a design is his, developed with the architecture chat into the records (his account, above).
- **The problem and the measure of success are his:** the week lost to searching by hand, the three-to-six-day baseline, and freshness as the one binding measure. `docs/architecture-2.0.md` carries his name; the measure is ADR-0015.
- **The scope floor is his standing decision,** with no record behind it: no user interface, no notifications, no paid services.
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

- **The age rule was built wrong.** 2026-09-26: the seat judged a posting's age against each run's clock, so a row admitted today would vanish a week later, possibly before he had seen it. He caught it from the seat's description alone and restated the rule: age is judged once, at first sight. It was rebuilt the same day.
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

### He made the decisions that set what it does

- **His targets.** The role families and their order; the seniority rule, after asking for evidence that levels II and III expect more than his three years.
- **Retention.** The fifteen days and their two clocks; closed postings shown for fifteen days, then stored.
- **The `Status` values** named after their tables. He renamed them in the browser, so no mark was lost.
- **Failure handling.**
  - The public display always updates, even when the private store fails, and such a failure must reach him (D9).
  - Three failed display updates in a row mark the run failed (D1).
  - Runs queue rather than drop: "I do not want anything to be dropped".
- **Records.** The record standard is followed rather than bent: ADR-0046 was replaced only at its eighth amendment, by ADR-0050.
- **Permission to push.** The implementing seat may push its own commits after the full suite passes (D10).

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

**Limits as of 2026-09-27:**
- **Sources.** Eleven employer boards and one aggregator. Five more adapters are decided and unbuilt (Ashby, Workable, SmartRecruiters, Breezy and Manatal, ADR-0029), out of 53 boards in the operator's registry. On-site roles in Karachi are thin: Rozee.pk, the main Pakistani board, has no API, and it is deferred.
- **Matching reads titles only.** Descriptions are now saved but never read, so a role whose title misses the pool is missed. The years-of-experience rule waits on reading descriptions.
- **Duplicates across sources are not merged.** An employer's own posting and an aggregator's copy of it can both appear, because the aggregator stamps its own date.
- **Lever's date is not proven to mean publication**, so Lever postings are never dropped for age.
- **GitHub starts scheduled runs three to four hours late.** Freshness is measured from publication, so it includes that delay.
- **Unbuilt:** the priority star (a mark on postings sharing a named attribute with an accepted one, ADR-0044) and the contract check's Airtable row. The cheaper projection that sends only changed rows is designed and deliberately waits on its triggers (ADR-0056).
- **The clearing tool and the thirty-day clock have not run live yet**; both are proved offline.
- **"Finished" is not yet defined.** The end-state document is open by decision (ADR-0023).
- **The private store's token expires on 2027-01-01**; the operator rotates it before then.

---

## Highlights

Short, role-neutral statements a reader can take as they are. Every figure is from the table above.

- Built an unattended job-discovery pipeline on GitHub Actions and Python (standard library plus `requests`). It polls employer job boards twice a day and shows only eligible, matching postings in Airtable, at no recurring cost.
- New postings reach the display a median of 5.4 hours after publication, and 90% within 10.5 hours, against targets of 24 and 72 hours, over 114 postings.
- 28 production runs over 12.6 days with no retries and no failed requests, reading 800 to 1,300 postings a run and keeping a few dozen.
- Every posting is admitted or dropped by a named, deterministic rule, and every drop is logged. There is no model and no scoring.
- Git branches serve as the database, with privacy enforced in code: employers' description text and aggregator data never reach the public repository. Every posting is saved in full to a private repository, verified by read-back.
- A classification workflow: the operator's marks are copied to their own tables and stored permanently. Rows are deleted from the display only after the store is read back from the remote. The display is bounded by a thirty-day clock and a dry-run-first clearing tool.
- A day's worth of an aggregator's feed went from about a third read, 93% of it irrelevant, to all of the relevant postings, by moving to a filtered endpoint an earlier measurement had wrongly rejected.
- 702 tests, and 354 mutations that deliberately break the code to prove the tests notice.
- Designed by the operator and built with AI agents in separate roles: architecture, implementation, and cold, read-only audit. The work was carried out under a written verification discipline and produced 55 decision records and 22 session logs.

---

## Where the evidence lives

| For | Read |
|---|---|
| What exists now and what is blocked | `STATE.md` |
| What was finished, with proof | `docs/reference/completed.md` |
| Why the system is shaped as it is | `docs/architecture-2.0.md` and `docs/decisions/` |
| What each session did | `logs/README.md`, then the log it names |
| Every documented file | `MAP.md` |
| The live numbers | The run logs on the `data` branch, read with `tools/run_log_report.py` and `tools/publication_lag_report.py` |

## Keeping this file current

**At the close of any session that changes a capability or a measured number:**
- update the section it belongs to and the date at the top;
- re-measure a number rather than carrying it forward, and give it its new date and source;
- remove a number that can no longer be measured;
- record a limit that is removed where it was listed, with the date.
