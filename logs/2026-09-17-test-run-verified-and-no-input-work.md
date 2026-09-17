---
type: log
description: The ticked test run verified on GitHub, a publication-lag report built, the README brought up to date, ADR-0023 annotated, a decision pack prepared for the operator, and the Airtable writer found to need the architecture chat first.
status: current
---

# Test run verified, and the work that needed no input, 2026-09-17

Previous log: `2026-09-17-first-github-runs.md`. Same conversation, fourth brief. The operator pushed `3ef83ba`, ran the workflow with the test box ticked, and asked for every pending item that needs no decision to be done.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `3ef83ba`, also `origin/main` |
| Mode | **Mutating.** No job board contacted. Unauthenticated reads of GitHub's public API and a fetch of `data` and `data-test` into a scratch clone. Reads of Airtable's and GitHub's documentation |
| Tests | 252 at start, 268 at end, all passing |
| Verification | 14 new mutations, all caught, each by a test written for it |

**Tags.** `[VERIFIED]` exercised and observed this session. `[BELIEVED]` reasoned, not run. `[INFERRED]` concluded from verified facts. Unmarked means believed.

## 1. The ticked run on GitHub

`[VERIFIED]` run 35239033514, `workflow_dispatch`, `3ef83ba`, created 15:15:26Z. Every step succeeded, including the tests, and there were no annotations.

- **`data-test` was pushed** at `6c7425d` by `job-aggregator <job-aggregator@invalid>`, parentless. It holds Greenhouse 759 and Lever 37 raw records, 21 kept, 796 seen entries, and no Himalayas record. Its run log reports 36 requests, first contact on every source.
- **`data` was untouched**: still one commit, `272cfdb`.

Test mode now works on GitHub, and `DATA_BRANCH` has resolved both ways there.

**Not yet exercised on GitHub:** a run that finds an existing branch, restores from it and pushes on top. The next scheduled run does that against `data`.

## 2. What this session can see of a GitHub run

The operator asked whether the run's console output is available here. It is not.

- **The public Actions API, unauthenticated, 60 requests an hour**, gives a run's event, status, conclusion, commit, and timing; each step's name and result; and the annotations.
- **The step logs**, the text each step prints, need a signed-in request even for a public repository.
- **What a successful run wrote to the branch** can be read by fetching it, and it includes the run log, which carries the summary the run printed.

So for a successful run nothing is missing. For a failed run the cause has to be reproduced, as it was for 35236457737, and the result is `[INFERRED]` until the operator pastes the step's text or this machine is signed in to the GitHub CLI.

**The "automatic trigger" was a watcher this session started**, polling that API every 75 seconds for up to an hour. It is not permanent, and it has ended.

## 3. Publication-lag report

`tools/publication_lag_report.py` answers STATE.md's open question about Lever's `createdAt` from the pipeline's own data. STATE.md: "a posting first seen in a run whose `createdAt` predates the previous run's clock is the proof."

It reads the seen store and the run logs from a branch, or from a local directory including the local-only seen store. It counts, per source, postings first seen after the first run, sorted by whether each is dated after the run immediately before, or at or before it, and gives the gaps for the second group. It concludes nothing, because no record says how many would settle the question.

Choices and reasons:

- **Runs come from the run logs, not from first-seen values**, so a run that found nothing still counts as the run before the next.
- **A date exactly at the previous run counts as before**, because that run looked at that instant.
- **Postings first seen on the first run are ignored**, because nothing looked before them.

`[VERIFIED]`:

- 16 tests, one of which runs two real `Run.execute()` calls and finds the Lever posting the first run missed.
- 14 mutations in `tools/mutations/2026-09-17-publication-lag-report.json`, all caught.
- Read correctly from the production branch (one run, so nothing counted yet), a three-run simulation (posting 1002, dated 174.4 hours before the run that missed it), and `data/test`.
- With this repository's missing branch, it exits 1 and says how to fetch it.

## 4. README and ADR-0023

**README.md** said "Status: design, not built... No code has been written." It now describes what runs: the `data` and `data-test` branches, setup with `.venv`, the test and run commands, the workflow and its test box, and the tools. The licence, scope and contact sections are unchanged.

`[VERIFIED]` every command it names exists. One row first described `tools/make_cassette.py` as recording from a live board; its docstring says it builds from a saved response, and the row was corrected before commit.

**ADR-0023** is a factual correction with a dated annotation, as CLAUDE.md allows for accepted records. Its Consequences said the same-commit rule for STATE.md was "not a gate yet"; gate 4 of the pre-commit hook enforces it. `[VERIFIED]` `git log -1 7b5633e` shows the gate was added on **2026-09-15**. STATE.md's Tooling row says 2026-09-11, and I had repeated that date in the previous log and in the architecture-chat brief. The row now carries a note, the previous log a dated correction, and the operator is told the brief's line is wrong.

## 5. Decision pack for the operator

`data/reports/decision-pack-2026-09-17.md`, local and gitignored, 568 lines, generated from the production `data` branch. It holds:

- every board's fetched and kept counts, and every kept posting with its location and admitting term;
- the 20 rows Himalayas kept in the 2026-09-16 test run, none of which mentions Pakistan and one of which states no location restriction;
- the 50 pool terms against the 796 postings: 10 credited, 39 matching nothing, and `mlops` matching only postings credited to an earlier term;
- all 431 distinct dropped titles.

`[VERIFIED]` from the same data:

- **seniority words among the 775 dropped titles:** senior 122, manager 110, director 31, lead 27, intern 18, staff 17, sr 16, associate 13, principal 7, mid 5, head 4, vice president 3, junior 1;
- **among the 21 kept:** senior 10, intern 1.

## 6. Evidence for the architecture chat's experience question

The slice log called Greenhouse's `metadata` "the most promising unexplored lead" for the stated-experience rule. `[VERIFIED]` from the saved 2026-09-11 payloads, it is weak:

- **Only one of the nine boards has a level field.** Five boards carry some metadata: Veeam (14 fields), Careem (10), Motive (2), BRKZ, Globalli (1 each). Banyan Canopy, CodeRoad, Joblogic and Speechify carry none.
- **Veeam's field is a grade, not years.** Its "Workday P Level" values: P1 8, P2 23, P3 37, P4 75, P5 26, P6 10, M2 2, M3 2, M4 4, M5 11, M6 1, S3 5, and null 38, of which 18 are internships.
- **The grade tracks titles loosely:** five P1 postings say "Senior".
- **No board carries years of experience.**

## 7. Gated, not built

**The Airtable writer and the weekly sweep wait on the architecture chat.** CLAUDE.md: "All fetch behaviour lives in one shared HTTP module. Retry, backoff, budget counting, circuit breaking." The module does budgeted GETs only. The writer needs authenticated PATCH or POST with a JSON body, and Airtable's own limits:

- `[VERIFIED]` from airtable.com/developers: 5 requests per second per base, then 429 and a 30-second wait;
- 1,000 calls a month per ADR-0004, which is a different budget from ADR-0028's per-run ceiling.

The protocol sends a change to a shared component to the architecture chat.

Two more questions belong there:

- **Aggregator rows in Airtable.** Whether the private Airtable base may receive aggregator rows, which would make Himalayas useful, is ADR-0020's to answer, since its terms concern redistribution.
- **Upsert.** Airtable's update endpoint can upsert on up to three fields `[VERIFIED]`, which would make a retried projection create no duplicates. ADR-0004 says "batched creates", so the method is noted for the chat rather than chosen here.

**ADR-0018's contract check waits on the operator**: whether to build it, how often, and how a change is reported, given CLAUDE.md's "No notification system".

**The operator's Airtable setup** was written from airtable.com/developers pages and GitHub's secrets documentation, both read this session. The free-plan limits come from ADR-0004, because support.airtable.com did not resolve from this machine. Airtable's screen labels were not verifiable, and the instructions say so.

## Mistakes in this session's own work

- **The gate-4 date.** I repeated STATE.md's 2026-09-11 without checking the commit. It is 2026-09-15.
- **The same editing-tool decoding as before.** A `\u2014` I wrote into the previous log became a literal em-dash, which misstated the sentence and broke the house rule. Repaired by writing the backslash with `chr(92)`.
- **A first draft of the ADR-0023 annotation said the gate "fired repeatedly" today.** Nothing this session saw it fire. Removed before commit.

## Not done

- No scheduled run has succeeded yet; the restore path on GitHub is unexercised.
- The Airtable writer, the weekly sweep and the contract check are not built, for the reasons above.
- Nothing pushed.
- No decision record changed except ADR-0023's dated annotation.
