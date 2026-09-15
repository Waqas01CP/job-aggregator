---
type: reference
description: The 50 title terms a posting must match to be admitted, plus the normalisation and matching rules applied to both sides.
status: current
---

# Title pool

Version 1, 2026-09-11.

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

`ai platform` · `ai system` · `ai product engineer` · `ai solution` · `conversational ai` · `forward deployed` · `ai automation` · `nlp`

### Generic entry rung

`software engineer i` · `associate software engineer` · `junior software engineer` · `backend engineer` · `back end engineer` · `python developer` · `python engineer`

**50 terms.**

## Known behaviour, accepted deliberately

**`ai red team` rather than `red team`.** The bare term pulls security red teaming, which is a real field and not this one.

**`model behavior` and `model behaviour` are both listed.** Spelling variants are listed, never derived.

**`software engineer i` also matches "Software Engineer II" and "III"**, because the boundary falls after `i`. Accepted. Skimming an occasional Software Engineer II costs less than the special case needed to prevent it.

**`ai trainer` and `ai evaluator` will pull annotation gig work.** One prior census measured 17 of 34 rows as Welo Data, Welocalize and Innodata. The annotation-vendor drop rule catches those by employer, so the terms stay and a different filter does the work.

**Never used as terms: bare `junior`, `associate`, `trainee`.** In the Pakistani market these match sales, HR, bookkeeping, Amazon PPC and clinical QA far more often than engineering. One paid run spent $0.73 that way and returned six technical rows out of sixty. Seniority words are always qualified.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-11 | Version 1 created | Initial pool, restructured from full job titles into distinctive stems so a trailing noun that varies between Engineer, Developer, Specialist and Lead does not require a term each |
| 2026-09-11 | Removed `agentic workflow` and `agentic system`. 52 terms to 50 | Neither could ever fire independently. `agentic` is an exempt single token and matches alone, so any title containing either longer term was already admitted by it. Dead terms in a pool whose purpose is that every match names one term |
| 2026-09-11 | Stated that the plural suffix reaches the term's final word only | The rule was true but unwritten, so a later term like `system engineer` would have silently failed to match its plural |
