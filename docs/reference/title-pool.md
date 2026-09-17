---
type: reference
description: The 51 title terms a posting must match to be admitted, plus the normalisation and matching rules applied to both sides.
status: current
---

# Title pool

Version 2, 2026-09-17.

A posting is admitted to the display only if its normalised title contains one of these terms. Nothing else is shown. Reasoning and consequences are in ADR-0021.

**This file is versioned.** Every change appends a row to Changes at the bottom, with its date, because a filter run is only reproducible against the pool as it stood at the time.

## Normalisation

Applied to the title and to every term, identically, before matching.

1. Lowercase.
2. Replace hyphen, en-dash, em-dash, underscore and forward slash with a single space. This is what makes `AI-Agent` match `ai agent`, and turns `AI/ML` into `ai ml`.
3. Delete commas, parentheses, periods and colons.
4. Collapse repeated whitespace, then trim.

URL-encoded characters are decoded before step 1, where the title arrives from a URL slug.

## Matching

**Word-boundary matching, never raw substring.** Raw substring matching on `rag` matches "sto**rag**e", turning a Storage Engineer into a RAG role. Word boundaries remove that entire class of error.

**An optional plural suffix is appended to the end of the term** when the pattern is built. The term `agentic system` compiles to `\bagentic system(?:e?s)?\b`, which matches both "Agentic System Engineer" and "Agentic Systems Engineer".

**The suffix reaches the term's final word only.** A term like `system engineer` would pluralise `engineer`, not `system`, so "Systems Engineer" would not match. No current term hits that case. Anyone adding a term where the pluralising word is not last must add both forms explicitly.

Nothing is ever stripped from a word, at either end. Terms are stored singular and the pattern handles the plural.

**No stemming algorithm.** Where a spelling or plural variant is the idiomatic form, it is listed explicitly. A stemmer is a small model with surprises in it, and every match here must be explainable by naming the term that produced it.

**Minimum two words per term**, except the single tokens listed below, which are distinctive enough not to collide. `ai` and `rag` are not on that list and never stand alone.

Exempt single tokens: `agentic`, `genai`, `llm`, `nlp`, `mlops`, `llmops`, `agentops`, `aiops`.

## Terms

### Core AI

`ai engineer` · `ai developer` · `ai software` · `applied ai` · `generative ai` · `genai` · `machine learning` · `deep learning` · `data scientist` · `ai ml`

### Agentic

`agentic` · `ai agent` · `agent engineer` · `multi agent`

### LLM and prompting

`llm` · `large language model` · `prompt engineer` · `context engineer` · `rag engineer` · `retrieval augmented`

### Evaluation

`evals engineer` · `eval engineer` · `evaluation engineer` · `ai evaluator` · `ai quality` · `ai red team` · `model behavior` · `model behaviour` · `ai trainer` · `ai reliability`

### Ops

`mlops` · `llmops` · `agentops` · `aiops` · `ai ops`

### Platform and systems

`ai platform` · `ai system` · `ai product engineer` · `ai solution` · `conversational ai` · `forward deployed` · `forward deployment` · `ai automation` · `nlp`

### Generic entry rung

`software engineer i` · `associate software engineer` · `junior software engineer` · `backend engineer` · `back end engineer` · `python developer` · `python engineer`

**51 terms.**

## Known behaviour, accepted deliberately

**`ai red team` rather than `red team`.** The bare term pulls security red teaming, which is a real field and not this one.

**`model behavior` and `model behaviour` are both listed.** Spelling variants are listed, never derived.

**`software engineer i` also matches "Software Engineer II" and "III"**, because the boundary falls after `i`. Accepted. Skimming an occasional Software Engineer II costs less than the special case needed to prevent it.

**`ai trainer` and `ai evaluator` will pull annotation gig work.** One prior census measured 17 of 34 rows as Welo Data, Welocalize and Innodata. The annotation-vendor drop rule catches those by employer, so the terms stay and a different filter does the work.

**Never used as terms: bare `junior`, `associate`, `trainee`.** In the Pakistani market these match sales, HR, bookkeeping, Amazon PPC and clinical QA far more often than engineering. One paid run spent $0.73 that way and returned six technical rows out of sixty. Seniority words are always qualified.

## Measured against real postings

Recorded so that the choice to keep these terms is revisited with evidence rather than forgotten. Reproduce with `tools/title_pool_report.py`.

**2026-09-17, version 1 against 796 employer-board postings** from the public `data` branch, run 35236531478, eleven boards.

- 21 admitted, 775 dropped.
- 10 terms were credited: `ai engineer` 7, `forward deployed` 3, `ai ml` 2, `software engineer i` 2, `backend engineer` 2, and one each for `ai platform`, `agentic`, `ai solution`, `machine learning` and `ai automation`.
- 39 terms matched no posting at all: `ai developer`, `ai software`, `applied ai`, `generative ai`, `genai`, `deep learning`, `data scientist`, `ai agent`, `agent engineer`, `multi agent`, `llm`, `large language model`, `prompt engineer`, `context engineer`, `rag engineer`, `retrieval augmented`, `evals engineer`, `eval engineer`, `evaluation engineer`, `ai evaluator`, `ai quality`, `ai red team`, `model behavior`, `model behaviour`, `ai trainer`, `ai reliability`, `llmops`, `agentops`, `aiops`, `ai ops`, `ai system`, `ai product engineer`, `conversational ai`, `nlp`, `associate software engineer`, `junior software engineer`, `back end engineer`, `python developer`, `python engineer`.
- `mlops` matched one posting, which `machine learning` is credited with because it comes first.
- An earlier local run, 2026-09-16, gave the same shape: 19 admitted from 916, 40 terms credited with nothing.

**The operator's decision, 2026-09-17: keep all 39.** Eleven boards, most of them not AI employers, are too few to condemn a term. The same census on the local Himalayas sample matched `ai trainer`, `data scientist` and `llm`, none of which fired on the employer boards. Revisit once the board list has grown under ADR-0029.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-11 | Version 1 created | Initial pool, restructured from full job titles into distinctive stems so a trailing noun that varies between Engineer, Developer, Specialist and Lead does not require a term each |
| 2026-09-11 | Removed `agentic workflow` and `agentic system`. 52 terms to 50 | Neither could ever fire independently. `agentic` is an exempt single token and matches alone, so any title containing either longer term was already admitted by it. Dead terms in a pool whose purpose is that every match names one term |
| 2026-09-11 | Stated that the plural suffix reaches the term's final word only | The rule was true but unwritten, so a later term like `system engineer` would have silently failed to match its plural |
| 2026-09-17 | Version 2. Added `forward deployment`. 50 terms to 51 | Decided by the operator. On 2026-09-16 three "Forward Deployment Engineer" postings were dropped while "Senior Forward Deployed Engineer" was kept: the plural rule reaches only a term's final word, so `forward deployed` cannot produce "deployment". None of those postings was open on 2026-09-17, so the term admits nothing today |
| 2026-09-17 | Recorded the first measurement against real postings, and the decision to keep the 39 terms that matched nothing | Decided by the operator, so the finding is kept with its evidence rather than lost in a session log |
