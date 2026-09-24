---
type: reference
description: The 79 title terms a posting must match, grouped into the operator's four role families in order of precedence to be admitted, plus the normalisation and matching rules applied to both sides.
status: current
---

# Title pool

Version 4, 2026-09-18.

A posting is admitted to the display only if its normalised title contains one of these terms. Nothing else is shown. Reasoning and consequences are in ADR-0021.

**This file is versioned.** Every change appends a row to Changes at the bottom, with its date, because a filter run is only reproducible against the pool as it stood at the time.

## Normalisation

Applied to the title and to every term, identically, before matching.

1. Remove accents from Latin letters, so `Sênior` becomes `senior` and `São Paulo` becomes `sao paulo`. The rule is exact: a combining mark goes when it follows an ASCII character, which covers every accent on a plain Latin letter and also a stray mark after a digit or a space. A mark on any other base stays: another script's marks, and a mark on a Latin letter outside ASCII, so `ǿ` keeps its accent. Added 2026-09-24 on the operator's decision. *(This sentence first said "only a mark on a plain Latin letter", narrower than the code; corrected after that day's audit, F13. No stored title is affected.)*
2. Lowercase.
3. Replace hyphen, en-dash, em-dash, underscore and forward slash with a single space. This is what makes `AI-Agent` match `ai agent`, and turns `AI/ML` into `ai ml`.
4. Delete commas, parentheses, periods and colons.
5. Collapse repeated whitespace, then trim.

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

The terms are grouped into the operator's four role families, in the operator's order of precedence, decided on 2026-09-17: agentic AI first, then the broad LLM and applied AI field, then traditional AI and ML, then software engineering the operator can do. AI takes precedence over software engineering.

Order matters in one way only. A title is credited to the first term it matches, reading top to bottom, so a title matching terms in two families is credited to the higher family. Admission does not depend on order, and ADR-0010 still orders the display by date alone. Within the software family, the entry-level terms come before the generic one so that they keep the credit.

### 1. Agentic AI

`agentic` · `ai agent` · `agent engineer` · `multi agent` · `agentops` · `agent developer` · `autonomous agent`

### 2. LLM and applied AI

`ai engineer` · `ai developer` · `ai software` · `applied ai` · `generative ai` · `genai` · `llm` · `large language model` · `prompt engineer` · `context engineer` · `rag engineer` · `retrieval augmented` · `evals engineer` · `eval engineer` · `evaluation engineer` · `ai evaluator` · `ai quality` · `ai red team` · `model behavior` · `model behaviour` · `ai trainer` · `ai reliability` · `llmops` · `ai platform` · `ai system` · `ai product engineer` · `ai solution` · `conversational ai` · `forward deployed` · `forward deployment` · `ai automation` · `gen ai` · `ai engineering` · `prompt engineering` · `context engineering` · `ai research` · `ai researcher` · `applied scientist` · `ai specialist` · `ai architect` · `ai integration` · `ai consultant` · `ai infrastructure`

### 3. Traditional AI and ML

`machine learning` · `deep learning` · `data scientist` · `ai ml` · `mlops` · `aiops` · `ai ops` · `nlp` · `ml engineer` · `ml ops` · `computer vision` · `data science`

### 4. Software engineering

`software engineer i` · `associate software engineer` · `junior software engineer` · `backend engineer` · `back end engineer` · `backend developer` · `back end developer` · `python developer` · `python engineer` · `full stack` · `fullstack developer` · `fullstack engineer` · `mobile developer` · `data engineer` · `automation engineer` · `software developer` · `software engineer`

**79 terms.**

## Known behaviour, accepted deliberately

**`ai red team` rather than `red team`.** The bare term pulls security red teaming, which is a real field and not this one.

**`model behavior` and `model behaviour` are both listed.** Spelling variants are listed, never derived.

**`software engineer i` does not match "Software Engineer II" or "III".** Corrected 2026-09-17: this note used to say it did, because the boundary falls after `i`; the plural suffix cannot consume a second `i`, so the pattern fails there. Since version 3, the generic `software engineer` admits both, and the seniority rule in `docs/reference/seniority-exclusions.md` drops them.

**`ai trainer` and `ai evaluator` will pull annotation gig work.** One prior census measured 17 of 34 rows as Welo Data, Welocalize and Innodata. The annotation-vendor drop rule catches those by employer, so the terms stay and a different filter does the work.

**`ai research` and `ai researcher` rather than bare `research engineer`.** The same reasoning as `ai red team`: the bare term pulls research engineering of every other kind. `applied scientist` is listed despite the same risk, because in this market it is an ML title in practice; if it starts admitting chemistry and materials roles, it is the first term to drop.

**The pool's plural rule cannot produce an "-ing" form**, since the suffix it appends is `(?:e?s)?` on the term's last word. So `ai engineering`, `prompt engineering` and `context engineering` are listed beside `ai engineer`, `prompt engineer` and `context engineer`, as `forward deployment` is beside `forward deployed`. Any later term whose gerund is idiomatic needs the same treatment.

**Never used as terms: bare `junior`, `associate`, `trainee`.** In the Pakistani market these match sales, HR, bookkeeping, Amazon PPC and clinical QA far more often than engineering. One paid run spent $0.73 that way and returned six technical rows out of sixty. Seniority words are always qualified.

## Measured against real postings

Recorded so that the choice to keep these terms is revisited with evidence rather than forgotten. Reproduce with `tools/title_pool_report.py`.

**2026-09-17, version 1 against 796 employer-board postings** from the public `data` branch, run 35236531478, eleven boards.

- 21 admitted, 775 dropped.
- 10 terms were credited: `ai engineer` 7, `forward deployed` 3, `ai ml` 2, `software engineer i` 2, `backend engineer` 2, and one each for `ai platform`, `agentic`, `ai solution`, `machine learning` and `ai automation`.
- 39 terms matched no posting at all: `ai developer`, `ai software`, `applied ai`, `generative ai`, `genai`, `deep learning`, `data scientist`, `ai agent`, `agent engineer`, `multi agent`, `llm`, `large language model`, `prompt engineer`, `context engineer`, `rag engineer`, `retrieval augmented`, `evals engineer`, `eval engineer`, `evaluation engineer`, `ai evaluator`, `ai quality`, `ai red team`, `model behavior`, `model behaviour`, `ai trainer`, `ai reliability`, `llmops`, `agentops`, `aiops`, `ai ops`, `ai system`, `ai product engineer`, `conversational ai`, `nlp`, `associate software engineer`, `junior software engineer`, `back end engineer`, `python developer`, `python engineer`.
- `mlops` matched one posting, which `machine learning` is credited with because it comes first.
- An earlier local run, 2026-09-16, gave the same shape: 19 admitted from 916, 40 terms credited with nothing.

**Planned by the operator, 2026-09-17:** once enough postings have accumulated, a pass over the dropped titles alone, harvesting the AI ones into the pool. That pass happens before the filter runs against them, and `tools/title_pool_report.py --dropped` lists exactly that set.

**The operator's decision, 2026-09-17: keep all 39.** Eleven boards, most of them not AI employers, are too few to condemn a term. The same census on the local Himalayas sample matched `ai trainer`, `data scientist` and `llm`, none of which fired on the employer boards. Revisit once the board list has grown under ADR-0029.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-11 | Version 1 created | Initial pool, restructured from full job titles into distinctive stems so a trailing noun that varies between Engineer, Developer, Specialist and Lead does not require a term each |
| 2026-09-11 | Removed `agentic workflow` and `agentic system`. 52 terms to 50 | Neither could ever fire independently. `agentic` is an exempt single token and matches alone, so any title containing either longer term was already admitted by it. Dead terms in a pool whose purpose is that every match names one term |
| 2026-09-11 | Stated that the plural suffix reaches the term's final word only | The rule was true but unwritten, so a later term like `system engineer` would have silently failed to match its plural |
| 2026-09-17 | Version 2. Added `forward deployment`. 50 terms to 51 | Decided by the operator. On 2026-09-16 three "Forward Deployment Engineer" postings were dropped while "Senior Forward Deployed Engineer" was kept: the plural rule reaches only a term's final word, so `forward deployed` cannot produce "deployment". None of those postings was open on 2026-09-17, so the term admits nothing today |
| 2026-09-17 | Recorded the first measurement against real postings, and the decision to keep the 39 terms that matched nothing | Decided by the operator, so the finding is kept with its evidence rather than lost in a session log |
| 2026-09-17 | Version 3. Terms regrouped into the operator's four role families, in order of precedence. Added `backend developer`, `back end developer`, `full stack`, `fullstack developer`, `fullstack engineer`, `mobile developer`, `data engineer`, `automation engineer`, `software developer`, `software engineer`. 51 terms to 61 | Decided by the operator, who is open to software engineering roles with AI taking precedence. Each added term was previewed against 796 production postings with `tools/title_pool_report.py`. `back end developer`, `fullstack developer` and `fullstack engineer` are the spelling variants ADR-0021 requires to be listed explicitly. Senior titles these terms admit are dropped by the seniority rule, version 1 |
| 2026-09-17 | Corrected the note claiming `software engineer i` matches "Software Engineer II" and "III" | It never did; checked against the compiled pattern |
| 2026-09-18 | Version 4. Added eighteen AI terms: `agent developer`, `autonomous agent`, `gen ai`, `ai engineering`, `prompt engineering`, `context engineering`, `ai research`, `ai researcher`, `applied scientist`, `ai specialist`, `ai architect`, `ai integration`, `ai consultant`, `ai infrastructure`, `ml engineer`, `ml ops`, `computer vision`, `data science`. 61 terms to 79 | Decided by the operator, who is moving toward AI roles first and wants the terms in place before the boards that carry them are added. Every one was previewed against the 796 production postings; none matches anything there yet, which is the point. Bare `research engineer` was rejected under ADR-0021's `ai red team` precedent |
| 2026-09-24 | Normalisation step 1 added: Latin accents removed before matching. No term changed | A Himalayas title reading "Sênior" reached Jobs because "sênior" is not "senior". The operator decided accents are stripped, with care. Over 1,458 distinct stored titles the change altered one verdict, that title, merged no two dedupe keys, and left every employer name as it was; logs/2026-09-24-operator-decisions-and-the-next-builds.md |
