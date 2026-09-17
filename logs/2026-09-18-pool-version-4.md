---
type: log
description: Pool version 4 with eighteen AI terms added ahead of the boards that carry them, one of which immediately admitted a missed AI internship; why Himalayas cannot be seen from GitHub; and why Airtable could not be built in this session.
status: current
---

# Pool version 4, and two things that cannot be done from here, 2026-09-18

Previous log: `2026-09-17-first-scheduled-run.md`.

| Header | Value |
|---|---|
| Date | 2026-09-18 |
| Model | claude-opus-5 |
| HEAD at start | `57f9382`, two commits ahead of `origin/main` at `bac377c` |
| Mode | **Mutating.** No job board contacted. The production branch in a scratch clone was read |
| Tests | 303 at start, 311 at end, all passing, also with `TEST_MODE=1` |
| Verification | 4 new mutations, all caught; one was caught only by a count test at first and its test was strengthened |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means believed.

## Pool version 4: eighteen AI terms

The operator asked for the AI terms to be added now, ahead of the boards that carry such roles, and stated the intent behind it: once enough postings have accumulated, a pass over the dropped titles alone, harvesting the AI ones into the pool before the filter runs against them. That intent is recorded in the pool's measurement section, and `tools/title_pool_report.py --dropped` produces exactly that list.

Added, by family:

- **Agentic:** `agent developer`, `autonomous agent`.
- **LLM and applied AI:** `gen ai`, `ai engineering`, `prompt engineering`, `context engineering`, `ai research`, `ai researcher`, `applied scientist`, `ai specialist`, `ai architect`, `ai integration`, `ai consultant`, `ai infrastructure`.
- **Traditional AI and ML:** `ml engineer`, `ml ops`, `computer vision`, `data science`.

**Bare `research engineer` was rejected**, under ADR-0021's own precedent for `ai red team`: the bare term pulls research engineering of every other kind. `ai research` covers "AI Research Engineer" and "AI Research Scientist". `applied scientist` carries the same risk and is listed anyway, because in this market it is an ML title; the pool now records that it is the first term to drop if it starts admitting chemistry.

**A gap class, now named in the pool.** The plural rule appends `(?:e?s)?` to a term's last word, so it can never produce an "-ing" form. `ai engineer` cannot match "AI Engineering", exactly as `forward deployed` could not match "Forward Deployment". Hence `ai engineering`, `prompt engineering` and `context engineering` beside their existing forms.

**What they admit today** `[VERIFIED]` against the 804 postings on the `data` branch at `91f7518`: one posting, and it is the gap class proving itself.

- **Veeam, "Platform, Security & AI Engineering Intern - Summer 2027", San Jose**, admitted by `ai engineering`. Version 3 dropped it. It is an AI internship, which is the level the operator is looking for.

Everything else matched nothing, which is the point of adding them early. The chain now keeps 270 of 804, drops 501 by title and 33 by seniority.

**A weak check, found and fixed.** The mutation that removes `gen ai` was caught only by the term-count test, because my test used "Gen AI Engineer", which `ai engineer` also matches. The test now uses "Gen AI Specialist", which only `gen ai` admits, and the mutation is caught by it.

## Himalayas cannot be seen from GitHub

The operator asked whether a week's trial is meaningful if the roles are never visible. It is not, as things stand, and the reason is ADR-0020: aggregator rows are never committed, so on a runner they exist only while the job runs. A scheduled run leaves behind its counts in the run log and nothing else.

What is available:

- **Counts only, free:** `tools/run_log_report.py` shows Himalayas' fetched and kept counts per run. With the seniority rule pushed, the kept count becomes "roles at the operator's level", which is a better signal than the raw count but still a number.
- **The roles themselves, locally:** a run on the operator's machine keeps them in `data/.../fetch-all-local/himalayas.json` and `data/.../local/filtered.json`. About 25 requests for Himalayas alone, or 36 for every board. Level and location restrictions are not stored by the pipeline, which reads only the fields it uses, so a fuller picture needs the raw responses saved as the spikes did.
- **The display, not yet:** whether Himalayas' kept rows may be written to the private Airtable base is question C for the architecture chat, and the writer does not exist.

Recorded for the operator's decision rather than acted on. Nothing was fetched.

## Airtable could not be built in this session

`[VERIFIED]` the operator ran `/reload-plugins`, whose output says "Plugin MCP server changes take effect in your next session". The Airtable skills are loaded, but no Airtable tool is available here: a tool search returns nothing. The schema build belongs to the next session, with the task text already given to the operator.

## Not done

- Nothing pushed at the time of writing. **Corrected at session close:** the operator pushed `ffccf8f` and `57f9382` while this was being written, so GitHub now runs pool version 3 with the seniority rule; only `085c434`, pool version 4, was still local.
- No Himalayas fetch.
- No decision record written or edited.

---

# Added at session close

Everything above, and in the seven logs before it, was written during the work. This section is what existed only in the session's context. The session ran from `cd1f290` to `085c434` across eight briefs from the operator.

## Why each mutation survived, and the two that were predicted

Three survivors in 108 mutations, and one catch weaker than it looked.

1. **The summary line's local-only count.** The test used a run with no aggregator rows, so the count it checked was zero and a mutation that always printed zero passed. **Shape: a test whose precondition never occurs**, the same shape as the vertical slice's `rag` survivor. Fixed by asserting on a run that has a Himalayas row.
2. **A source absent from a run's request counts, treated as zero.** No test had a board line for a source that made no requests, which happens when the budget runs out before a source is reached. **Shape: the fixture lacks the case entirely.** Fixed with a board marked "not reached".
3. **`gen ai` removed from the pool** was caught only by the term-count test, because the title I chose, "Gen AI Engineer", is also matched by `ai engineer`. **Shape: a test that cannot isolate the thing it names.** Fixed with "Gen AI Specialist", which only `gen ai` admits.
4. **Two survivors were predicted before running** and given tests first: a listed branch file that cannot be read being skipped silently, and the raw-file source check, whose effect the new content guard duplicated. The case separating that pair is a stray aggregator raw file under `fetch-all/`, which must be passed over rather than refuse the whole commit.

One mutation was caught by an unintended path: renaming the pool's "Known behaviour" heading made every test module fail to import, because the measurement section then contains a backticked single token (`data`) that the loader refuses. Same guarantee, louder failure.

## Defects in my own work, and what made each invisible

- **`TEST_MODE` at job level.** Moving it from the Fetch step to the job's `env` let the test step see it, and seven of my own `main()` tests failed on GitHub while passing everywhere else. Invisible because the local simulation ran only three steps and skipped the tests, and because nothing tested the environment-variable route into test mode, which is the only route the workflow uses. The simulation now runs the test step.
- **A stray `data/seen.json`.** An early version of the text-mode spy test called `restore_from_branch()` without changing into its temporary directory, so it wrote into this repository's `data/`. Three bytes, gitignored, never committed. Invisible because `data/` is ignored and nothing lists it.
- **A scratch script named `inspect.py`** shadowed the standard library module and made four simulated runs fail on an import, which I first misread as a pipeline failure. Scratch scripts must not take standard-library names.
- **An unchecked cause stated as fact.** I told the operator CodeRoad's arithmetic came from a duplicated identity. No identity is duplicated anywhere; the real cause was a table mixing two runs.
- **A date repeated from `STATE.md` without checking.** Gate 4's commit is dated 2026-09-15, not 2026-09-11. It reached a log and the architecture-chat brief before being caught.
- **A commit message saying "five" for four items**, amended before the push.

## What did not work

- **Backslashes through a bash heredoc, four more times.** A `\n` inside a Python string became a real newline and broke `src/filters.py`, and again inside a test's expected string; a third attempt mangled a scratch edit; and this very section could not be appended by heredoc at all. The rule from the previous session holds and needs restating: anything containing a backslash goes through the Write or Edit tool, or is built in code with `chr(92)` and `chr(10)`.
- **`\uXXXX` escapes through the Write and Edit tools.** They are decoded on the way in, so a `\u2014` written into prose became a literal em-dash twice, once breaking the house style in a log and once in a commit message. Only `\u` escapes are decoded; a literal `\n` in prose survives.
- **`grep -c` at the head of an `&&` chain.** It exits non-zero when the count is zero, which silently skipped the rest of the chain and produced an empty commit message.
- **Watching GitHub for longer than an hour.** The unauthenticated Actions API allows 60 requests an hour, and a monitor lives only while the session is working, so runs that fire between messages are checked afterwards rather than watched.
- **Reading a failed run's step output.** It needs an authenticated request even on a public repository, so a failure's cause has to be reproduced locally instead.

## Where the close alternative was wrong

- **Implementing the seniority rule despite ADR-0021's "no blocklist".** The alternative was to wait for the architecture chat. The operator's instruction in the conversation outranks a record under ADR-0022, so it was built, marked as carrying no record, and raised. Treating it as a design question would have made the operator wait on a chat for their own call.
- **Ordering the seniority rule after the title rule.** Before it, the drop log would have lost its meaning as the record of titles the pool is missing, and the `seniority` count would have become "every senior posting on every board" rather than "relevant roles excluded for level".
- **Excluding level II on one posting's evidence.** The alternative was to keep II, since the operator is open to mid-level. The check found 5+ years on the only II posting stating a number, and the file records that the evidence is one posting.
- **Airtable upserts.** Idempotent retries argue for them; ADR-0004 says "batched creates". Left for the chat rather than chosen while building nothing.
- **Restoring branch state on every run.** Restoring only when a run commits keeps the operator's `--no-commit` exploration chaining from local files, which is how the previous session's two-run check worked.
- **Adding AI terms before the operator asked.** They match nothing on the current boards, so adding them looked free; it would still have been a pool change nobody decided. Asked, then added when approved.
- **Deleting `data/test/` outright.** Moving it preserved the only surviving run log and the snapshot both Speechify comparisons rest on.

## Noticed, not investigated

- **`ai ops` admits go-to-market titles.** Run 2 kept Motive's "Senior Program Manager, AI Ops (GTM)". The seniority rule drops that one, but the term's shape is a false-positive source.
- **`ai system` admits "Non-AI Systems Analyst"**, because normalisation turns it into "non ai systems". Recorded in a test as current behaviour; ADR-0021 named it the one to watch.
- **Speechify's city copies will now be admitted** by `software engineer`, so roughly 241 rows enter the filtered file on the first run after the push, and its daily rotation adds more. The display collapses them to two roles; the public file does not.
- **Careem's "Senior Software Engineer I"** is ambiguous: a senior word on an entry-level rung. Dropped, by the operator's decision.
- **GitHub's schedule is very late.** The two scheduled runs fired 3h43m and 4h31m after their slots. ADR-0006 absorbs it, but Measure A's freshness numbers will carry it.
- **`data-test` is still on the remote** from the manual test run, and nothing deletes it.
- **A local `origin/HEAD` ref appeared** on the first fetch. Harmless.
- **`filtered.json` keeps rows admitted under older rules.** Raised for the chat as question I.
- **A `--boards PATH` option** would let GitHub run one board list and this machine another, which is the cheapest route to keeping Himalayas local-only. Not built, because it presumes the answer to the Himalayas question.

## Records believed stale or wrong

Raised with the architecture chat unless marked otherwise.

- **ADR-0021's "We will maintain no blocklist"**, and its Confirmation case "Software Engineer II", both contradicted by the seniority rule.
- **ADR-0011's field enumeration**, eight fields out of date.
- **ADR-0013's "projection of that file"**, which does not say whether a projection re-applies current rules.
- **`docs/architecture-2.0.md:195`** still lists a location filter; **line 302** still gives exit 1 a single cause.
- **ADR-0009 says eleven boards**; `config/boards.json` holds twelve entries.
- **Corrected in place:** ADR-0023's "neither is a gate yet", annotated; the pool's false claim that `software engineer i` matches "Software Engineer II"; `STATE.md`'s gate-4 date; and the vertical-slice log's "Karachi, Punjab" reason for having no location filter, which describes harvested data rather than this pipeline.

## Material the operator asked for, kept here so it survives

### Airtable, the task for a session that has the plugin

The operator has created the account, the base "Job aggregator" and its table "Jobs". The plugin's tools reach only a new session, which should be given this:

> Build the Airtable schema for job-aggregator with the Airtable MCP. Read `STATE.md` and this log first. Do not write outside the repository. Do not create records. In table "Jobs": the primary field must be "Title", single line text; remove the other default fields, and if the MCP cannot delete a field, say which. Then create Employer (single line text), Location (long text), Link (URL), Published, First seen and Order date (date with time, GMT if offered), Board, Matched term and Identity (single line text), Status (single select: applied, rejected_pipeline, rejected_choice, expired_before_review), Pipeline reason (single select: wrong title match, location wrong, expired at surfacing, experience level, duplicate), Choice reason (single select: employer, compensation, stack, recently applied to this employer, seniority in substance). Duplicate it as "Jobs test". If the MCP can create a grid view "To review", filtered to Status is empty and sorted by Order date newest first, create it on both; otherwise say so. Verify by listing both tables' fields and comparing with this list. Report the base ID, both table IDs, and roughly how many API calls were used. Never ask for the token.

The statuses and reasons are ADR-0014's. The token, with scopes `data.records:read`, `data.records:write` and `schema.bases:read` limited to that base, and the four repository secrets `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_ID` and `AIRTABLE_TEST_TABLE_ID`, remain the operator's to create.

### The contract check, the options put to the operator

ADR-0018's check fetches one response per platform, fingerprints the fields the adapters read, and names any that change. Three platforms today, eight after ADR-0029's adapters. For scale, the fetch runs spend about 2,160 requests a month.

| Option | Requests a month now | After five more adapters | A change is noticed within |
|---|---|---|---|
| Daily | about 90 | about 240 | a day |
| Twice weekly | about 26 | about 70 | 3 to 4 days |
| Weekly | about 13 | about 35 | a week |
| Before every fetch run | about 180 | about 480 | the same run |
| Inside the fetch run, reusing its responses | none | none | every run, but it contradicts ADR-0018's "separate from the pipeline run" |

How it reports, given CLAUDE.md's "No notification system": the check's run fails and GitHub sends its own failed-run email; or a report file on the data branch; or a row in Airtable once the writer exists. Recommended: daily, failing the run, adding the Airtable row later.

### Himalayas, the options put to the operator

Its roles cannot be seen from a GitHub run at all. Either fetch it from the operator's machine (about 25 requests for Himalayas alone, 36 for every board), or get the chat's answer on whether its rows may reach the private Airtable base, or drop it from the schedule and keep it for local runs. Until then it costs 50 requests a day and shows nothing.

### One clarification the operator asked for

The "reply template" in my messages was a fill-in format for convenience. It is not a file, nothing reads it, and answers need not follow it.
