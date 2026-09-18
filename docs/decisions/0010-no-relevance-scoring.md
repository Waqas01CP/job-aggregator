---
status: accepted
topic: filtering
description: Every verdict names a deterministic rule a person can read. The scope floor the whole project rests on, and the boundary any ranking proposal has to cross.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0010: No relevance scoring, ranking, or model-based screening

## Context and Problem Statement

The conventional extension to a job pipeline is a relevance score that ranks postings so the best appear first. The superseded architecture document in this repository specifies exactly that: a weighted 0 to 100 score combining keyword match, seniority fit, company tier and recency, with a shortlist threshold and a precision acceptance gate.

Screening is already performed by a separate falsification-based process the operator runs by hand.

Prior harvested data contains a measured instance of an AI-derived experience-level field classifying a role paying 150,000 to 200,000 USD as entry level.

## Decision Drivers

- The operator's existing screening process is more discriminating on their criteria than a keyword score.
- A scorer requires weight tuning, a labelled evaluation set, a precision measurement, and ongoing maintenance.
- Every admit or drop should be explainable by naming a rule.

## Assumptions

- The reachable pool is small enough that reading every admitted row is tractable. Based on four exhausted census queries putting the pool at roughly one qualifying role per six months; the display will carry more than qualifying roles.

## Considered Options

- Weighted keyword scoring with a shortlist threshold.
- Language-model relevance classification.
- No scoring; deterministic rules only.

## Decision Outcome

Chosen option: "no scoring; deterministic rules only".

We will perform no scoring, no ranking, and no model-based classification of any posting. Every rule that admits or drops a posting will be a deterministic, readable predicate whose verdict can be explained by naming the rule. We will order the display by date only.

### Consequences

Every row in the display is there for a reason statable in one sentence, and every dropped row likewise.

The pipeline has no accuracy metric to maintain, no evaluation set to build, and no drift to monitor.

The operator reads more rows than a ranked list would surface first.

Deterministic rules cannot capture nuance. This is intentional: nuance is the operator's job, and ADR-0016 routes ambiguity to a human.

### Confirmation

Any admitted or dropped row can be explained by naming one rule. If a row's presence requires explaining a combination of weights, this decision has been violated.

## Pros and Cons of the Options

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | Role families are permitted, as separate date-ordered views | ADR-0038. The pipeline assigns a family label derived from the term that matched, which is a lookup rather than a judgement, and every view remains ordered by date alone. Numeric weights per family, a single ordered list mixing families, and any label assigned by anything other than the matched term stay forbidden |

## More Information

If revisited, ADR-0001 guarantees the raw layer needed to evaluate any proposed scorer against real history.
