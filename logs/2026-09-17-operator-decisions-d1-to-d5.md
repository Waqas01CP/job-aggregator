---
type: log
description: The operator's answers on Himalayas, local test data, the title pool, the experience rule and the board list, what was done with each, the evidence gathered for the ones still open, and the Airtable plugin examined.
status: current
---

# The operator's decisions D1 to D5, 2026-09-17

Previous log: `2026-09-17-test-run-verified-and-no-input-work.md`. Same conversation, fifth brief.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `be99ff8`, one commit ahead of `origin/main` |
| Mode | **Mutating.** No job board contacted. Read-only use of the operator's CV at `Operating Plan\Waqas_Sharif_Master.md`, as permitted; nothing written outside this repository. Unauthenticated reads of GitHub for the Airtable plugin's source |
| Tests | 268 at start, 285 at end, all passing |
| Verification | 16 new mutations, all caught |

**Tags.** `[VERIFIED]` exercised and observed this session. `[BELIEVED]` reasoned, not run. Unmarked means believed.

## D2. Local test data moved

The operator's instruction: move `data/test/` to the recommended place, without causing issues.

`[VERIFIED]`:

- sha256 of all 6 files was taken before the move, the directory was moved to `data/archive/2026-09-16-test/`, and the hashes after the move were identical;
- `data/test` no longer exists;
- git still ignores the new path, through `.gitignore:22` (`data/`).

Nothing reads `data/test` except a local test-mode run, which recreates it empty; `CLAUDE.md` and `README.md` describe that path correctly and are unchanged.

**A defect of mine found on the way.** `data/` also held a `seen.json` of 3 bytes, `{}`, created at 16:06:46 local time. My first version of `test_no_git_call_runs_in_text_mode` called `restore_from_branch()` without changing into its temporary directory, so the restore wrote the throwaway branch's `seen.json` into this repository's `data/`. The test had already been fixed to change directory, for other reasons. `[VERIFIED]` the file held only `{}`, it was deleted, and a fresh run of `tests.test_storage` left `data/` holding only `archive` and `reports`. It was gitignored and never committed. A local production run would have loaded it as an empty seen store, which is harmless.

## D3. The title pool

**Done on the operator's instruction:**

- **`forward deployment` added; the pool is version 2, with 51 terms.** `[VERIFIED]` "Forward Deployment Engineer" matches it, "Senior Forward Deployed Engineer" still matches `forward deployed`, and "Deployment Engineer" matches nothing. None of the three postings that exposed the gap on 2026-09-16 was open on 2026-09-17, so the term admits nothing today.
- **The 39 terms that matched nothing are kept**, and the finding is recorded with its evidence in a new section of `docs/reference/title-pool.md`, "Measured against real postings", with a dated row in its Changes table. The section sits after "Known behaviour", because the loader reads terms only up to that heading. Its own backticked terms must never be read as pool terms, and a test holds the count at 51.

**Built: `tools/title_pool_report.py`.** It measures the pool against stored postings (credited per term, matches per term, terms matching nothing) and previews a candidate with `--try`. The candidate is compiled and validated exactly as the pool would be, so `rag` is refused.

- 16 tests.
- 16 mutations in `tools/mutations/2026-09-17-title-pool.json`, which also covers the pool file itself, all caught.
- **One catch took a different path from the one intended:** renaming the "Known behaviour" heading made every test module fail to import, rather than tripping the term-count assertion, because the measurement section then contains a backticked single token (`data`) that the loader refuses. Same guarantee, reported through a different path.

**Previewed against the production branch (796 postings)** `[VERIFIED]`. 32 candidates were tried.

- **AI candidates:** every one matched nothing on these eleven boards except `ml engineer`, whose one match is already admitted. The terms were `agent developer`, `autonomous agent`, `gen ai`, `ai research`, `ai researcher`, `research engineer`, `applied scientist`, `ai specialist`, `ai architect`, `ai integration`, `ai consultant`, `ai infrastructure`, `ml ops`, `data science`, `computer vision` and `ai scientist`. The boards carry few AI roles, so widening the AI side depends on more boards more than on more terms.
- **Software candidates** add postings dropped today:

| Candidate | Postings added |
|---|---|
| `software engineer` | 248, of which 241 are Speechify's "Software Engineer, Platform" city copies |
| `automation engineer` | 10 |
| `software developer` | 7 |
| `data engineer` | 5 |
| `full stack` | 4 |
| `backend developer` | 2 |
| `fullstack developer` | 1 |
| `mobile developer` | 1 |

Most of these are senior titles.

**The operator's CV, read to understand the families.** It presents an "AI Engineer | LLM Reliability | Agentic Systems in Production", a 2026 software engineering graduate, with:

- LangGraph, Google ADK, evaluation harness and red-teaming work;
- FastAPI and PostgreSQL backends;
- ML coursework (scikit-learn, TensorFlow, Keras, YOLO, CNNs);
- QA automation coursework (Selenium, Playwright);
- an AI automation internship.

The operator's stated order, confirmed against that: agentic AI and agentic systems first, then the broad LLM and applied AI field including RAG, then traditional AI and ML, then software engineering. The order is put back to the operator for confirmation, not implemented.

**ADR-0010 constrains any order.** "We will order the display by date only." A family label per term, used to give each family its own date-ordered view, is proposed instead. It is raised for the architecture chat rather than assumed to comply.

**Duplicates in the display.** `src/dedupe.py`: "Only the display side sees groups." `[VERIFIED]` by reading. Speechify's 241 city copies would therefore reach Airtable as 2 rows, while all 241 would still be appended to the public filtered file.

## D4. Experience and seniority

**Recorded on the operator's instruction:** the stated-experience rule is deferred until filtering reads descriptions as well as titles, with a reference maximum of three years. The note is in `src/filters.py`'s docstring and STATE.md.

**Proposed, not implemented: a title seniority rule.** The operator is open to intern, junior, associate, mid and untitled roles. Excluding titles containing senior-level words (senior, sr, staff, lead, principal, head, manager, director, vp, vice president, chief) would, on 2026-09-17's data `[VERIFIED]`:

- **drop 10 of the 21 kept rows:** both BRKZ "Senior AI Engineer" roles, Motive's "Senior AI Platform Engineer", both CodeRoad "Senior Agentic AI Engineer" roles, Smart Working's "Senior Backend Engineer", the three Veeam "Senior Forward Deployed Engineer" roles, and Careem's "Senior Software Engineer I";
- **drop 4 of the 7 reachable from Pakistan**, including Careem's "Senior Software Engineer I", whose level name is ambiguous;
- **leave these software additions:** `software engineer` 248 to 244, `automation engineer` 10 to 7, `data engineer` 5 to 1, `full stack` 4 to 1.

Two choices are for the operator: whether numbered levels ("II", "III") count as senior, and whether "architect" does.

No record names such a rule. It is raised for the architecture chat, because a new rule in the filter chain needs a record.

## D1. What Himalayas surfaces

The operator will remove Himalayas if its roles are ones they cannot apply for.

The pipeline keeps only the fields it uses, so the 20 Himalayas rows kept on 2026-09-16 have no seniority. Himalayas' own saved responses do carry `seniority`, `employmentType`, `locationRestrictions` and `timezoneRestrictions`. `[VERIFIED]` from `raw_responses/himalayas-*.json`, 91 unique postings saved between 2026-09-11 and 2026-09-16:

- **Location:** 74 of 91 restrict location to countries that exclude Pakistan, and 17 state no restriction.
- **Seniority:** Senior 29 and Mid-level 28 are the largest groups; Entry-level appears on 13 when combined labels are counted.
- **The pool keeps 8.** Five of those do not exclude Pakistan:
  - micro1 "AI Engineer", Mid-level, contractor;
  - Dura Digital "AI Engineer", Senior, contractor;
  - Janea Systems "Lead Machine Learning Engineer", Senior;
  - DistantJob "Principal AI Solutions Consultant", Director;
  - micro1 "Senior AI Trainer", Senior.

  Only the first fits the operator's levels.
- **The 20 kept on 2026-09-16:** 19 carry a country restriction that excludes Pakistan; the one without is micro1's "Data Scientist".

A fresh look would need about 25 requests to Himalayas, the same as one GitHub run, and is the operator's call.

## D5. The board list

The operator did not understand the question. It is re-asked plainly, and nothing changed.

## Airtable: the Claude Code plugin examined

The operator asked whether Airtable's AI or the Claude Code Airtable plugin could build the table. `[VERIFIED]` from GitHub:

- **What it is:** `airtable@claude-plugins-official` is listed in the official marketplace's `marketplace.json`, authored by Airtable, sourced from `github.com/Airtable/skills`.
- **What it connects to:** its `.mcp.json` points at `https://mcp.airtable.com/mcp`.
- **Schema:** its product-ops skill says to "build the schema via MCP: base, typed fields, … `singleSelect`s".
- **Views:** the same skill hands views, interfaces and automations back to the UI "for surfaces it doesn't yet author".

On this machine, the Claude Code CLI 2.1.272 is installed, the official marketplace is known, and Airtable is not installed.

Not established:

- the server's current tool list, which the skill says to query live;
- whether its sign-in can be limited to one base;
- whether its calls count against the free plan's 1,000 a month.

## Not done

- D1, D3's family order and terms, D3 and D4's seniority rule, D5, the Airtable route, and the contract check all wait on the operator.
- No change to `config/boards.json`.
- Nothing pushed.
- No decision record written or edited.
