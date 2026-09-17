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

- Nothing pushed. GitHub still runs pool version 2 without the seniority rule.
- No Himalayas fetch.
- No decision record written or edited.
