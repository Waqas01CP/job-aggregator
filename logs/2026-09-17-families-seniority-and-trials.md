---
type: log
description: Pool version 3 in the operator's role-family order with ten software terms, a seniority rule decided by the operator and checked against evidence, and one-week trials for Himalayas and Banyan Canopy.
status: current
---

# Role families, seniority, and two trials, 2026-09-17

Previous log: `2026-09-17-operator-decisions-d1-to-d5.md`. Same conversation, sixth brief.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `bac377c`, two commits ahead of `origin/main` |
| Mode | **Mutating.** No job board contacted. Saved payloads and the production branch fetched into a scratch clone were read |
| Tests | 285 at start, 303 at end, all passing, also with `TEST_MODE=1` |
| Verification | 13 new mutations, all caught; all six mutation files still validate against the changed files |

**Tags.** `[VERIFIED]` exercised and observed this session. `[BELIEVED]` reasoned, not run. Unmarked means believed.

## The operator's answers

1. **Himalayas:** keep it for a week, then decide.
2. **Title pool:** the stated understanding is correct; add the software candidates; record the order of role families.
3. **Seniority:** exclude "II" and "III", after checking they count as senior; keep "architect"; Careem's "Senior Software Engineer I" is out because of its senior word.
4. **Boards:** keep Speechify and CodeRoad; remove Banyan Canopy only if certain it is finance, otherwise leave it for a week.
5. **The reply template:** what it is. It was a reply format written into my previous message for convenience. It exists nowhere in the repository, nothing reads it, and answers need not follow it.

## Role families, recorded in the pool

`docs/reference/title-pool.md` is version 3. Its terms are grouped under four headings, in the operator's order:

1. agentic AI;
2. LLM and applied AI;
3. traditional AI and ML;
4. software engineering.

A sentence above the lists records that order and the date it was decided.

**What order does.** The pool credits a title to the first term it matches, so a title matching two families is now credited to the higher one. `[VERIFIED]` "Senior Agentic AI Engineer" is credited to `agentic`, and "Software Engineer, Machine Learning" to `machine learning`. Admission does not depend on order, and ADR-0010's date-only display order is untouched. Within the software family, `software engineer i`, `associate software engineer` and `junior software engineer` come before the generic `software engineer`, so they keep their credit rather than becoming dead terms.

**Ten terms added:**

- `backend developer`, `full stack`, `mobile developer`, `data engineer`, `automation engineer`, `software developer` and `software engineer`, each previewed against production;
- `back end developer`, `fullstack developer` and `fullstack engineer`, the spelling variants ADR-0021 requires to be listed explicitly.

**A false claim in the pool corrected.** Its Known behaviour said `software engineer i` "also matches Software Engineer II and III". `[VERIFIED]` it never did: the compiled pattern returned no match for either, because the plural suffix cannot consume a second `i`.

## The seniority rule

`docs/reference/seniority-exclusions.md`, version 1, lists: `senior`, `sr`, `staff`, `lead`, `principal`, `head`, `manager`, `director`, `vp`, `vice president`, `chief`, `ii`, `iii`, `iv`. Words are matched like pool terms: normalised, whole-word, with an optional plural. `architect`, level I, intern, junior, associate, trainee, graduate and mid-level are deliberately not excluded.

**The check the operator asked for.** From Veeam's saved response of 2026-09-11, which carries descriptions and Workday grades, counting only phrases of the form "N years … experience":

- **Level III:** five postings, grade P3. Every one stating a number asks for five years or more (8+, 8+, 5+, 5+).
- **Level II:** three postings, grade P2. One states a number: 5+.

Both exceed the operator's reference maximum of three years. The evidence for II rests on a single posting. No description text was written anywhere.

**The same check exposed a trap.** A naive level match read "UK&I" in two sales titles as level I. The rule does not exclude level I, and a test holds "UK&I" as no level.

**Placement: after the title rule.** Two reasons:

- a title the pool never admitted stays a title drop, so the drop log keeps its value as the record of missing terms;
- the `seniority` count in the run log means relevant roles excluded for level.

A kept row still records "matched <term>": `apply_chain` now keeps the last reason any rule gave, where it used to keep only the final rule's.

**Loading.** The words load inside `TitleMatcher`, from their own section only, so a missing, section-less or empty list is a `FilterError` and the run does not start. The file quotes the words it keeps under other headings, and a test proves those are never read.

**Where it departs from the records.** Raised with the architecture chat:

- ADR-0021: "We will maintain no blocklist."
- ADR-0021's Confirmation lists "Software Engineer II" among titles that must not be admitted. The pool now matches it and the seniority rule drops it. The case set, which no test covered before, is now tested through the whole chain, with that difference stated.

The rule is implemented because the operator's instruction outranks the records (ADR-0022).

**The watched case, recorded.** ADR-0021 names "Non-AI Systems Analyst" as the one to watch. `[VERIFIED]` `ai system` admits it: normalisation turns "Non-AI Systems" into "non ai systems". It is recorded as current behaviour, so any change is noticed.

## Effect on production data

`[VERIFIED]` the chain run over the 796 postings of the production `data` branch:

- **Kept: 267.** 241 are Speechify's "Software Engineer, Platform" city copies of two roles. The display groups those, but the public filtered file will store every copy.
- **Dropped:** 32 for seniority, 497 for title.
- **The other kept roles, 25:**
  - agentic: 2, CodeRoad's "EG - Agentic AI Engineer" and Joblogic's full-stack agentic role;
  - LLM and applied AI: 4, including Globalli's "AI Engineer";
  - traditional ML: 3, including Joblogic's "AI/ML Engineer" in Lahore;
  - software: 16, among them Careem's "Software Engineer I", Joblogic's two automation roles in Lahore, and Veeam's QA and test roles in Europe.
- **Six kept rows mention Pakistan.**

**The pool change reaches GitHub only when pushed.** Until then the runs use version 1.

## Two trials, until 2026-09-24

**Himalayas.** Kept for a week at the operator's request. On a runner its rows are discarded, so the week produces only run-log counts, visible with `tools/run_log_report.py`. Seeing the actual roles needs a local run of about 36 requests, which is the operator's call. The seniority rule will now remove its senior roles, so its kept count should fall.

**Banyan Canopy.** Not removed. `[VERIFIED]` its 2026-09-11 response held seven postings. Six were finance and business roles; one was "Product Analyst / BI (AI & Data)" in Karachi. That is not certainly finance, so under the operator's rule it stays for the week.

## Speechify and CodeRoad

Kept on the operator's instruction. `config/boards.json` is unchanged.

## Airtable

The operator ran `/reload-plugins`. No Airtable tool is visible in this session. A plugin reload does not reach a conversation already running, so the schema build belongs to a new session.

## Mistakes in this session's own work

- **Backslashes through a heredoc, twice more.** A `\n` became a real line break in `src/filters.py`, breaking its syntax, and again in a test string. Both were caught at once by the next command and repaired with code that never writes a backslash through the heredoc. The mutation files were built with `json.dumps` and `chr(10)` for the same reason.
- **Test titles the pool never admitted.** Four of my seniority test titles ("AI Team Lead", "Head of AI Engineering", "AI Engineering Manager", "Chief AI Officer") match no pool term, so they were title drops, not seniority drops. They were replaced with titles the pool admits, since the test is about the seniority rule.

## Not done

- Nothing pushed.
- AI terms that match nothing on today's boards were not added. The operator's approval covered the software candidates, and the AI list is asked once more.
- No decision record written or edited.
