---
status: accepted
topic: filtering
description: Role families are a label derived from the matched term, with one date-ordered view each, and the boundary that keeps it from becoming a ranking.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0038: Role families are views, not a ranking

## Context and Problem Statement

The operator ranks the kinds of role he wants: agentic AI first, then LLM and applied AI, then traditional AI and ML, then software engineering. The title pool already lists its 79 terms under those four headings, in that order, and the order decides which term a title is credited to when it matches more than one.

ADR-0010 says at line 39: "We will perform no scoring, no ranking, and no model-based classification of any posting. Every rule that admits or drops a posting will be a deterministic, readable predicate whose verdict can be explained by naming the rule. We will order the display by date only."

A preference ordering over kinds of role sounds like exactly what that record forbids. It is worth being precise about why it is not, because this is the shape scoring would arrive in: a label, then an order over labels, then a number derived from the order, then a model that assigns the number.

## Decision Drivers

- The operator wants to look at agentic AI roles before software engineering roles. That is a real need and predates any record.
- ADR-0010 exists because a scored list is unauditable and hides why a role appeared where it did.
- Whatever is built must keep every row explainable by naming a rule.
- The boundary has to be written down, or the next step along this path looks like a small extension of an accepted decision.

## Assumptions

- Every admitted row has exactly one matched term. **Measured**: the title rule records the term that admitted the row, and the pool's family order decides the credit when several match.
- Four families are enough. **Sourced** from the operator, who named them. They are configuration under ADR-0031 and change by editing the pool.

## Considered Options

- Order the display by family, then by date.
- Score rows by family and sort on the score.
- One date-ordered view per family, with the operator choosing which to open.

## Decision Outcome

Chosen option: "one date-ordered view per family".

**The pipeline assigns each row a family label, derived deterministically from which pool term matched it.** The label is a lookup, not a judgement: the term is already recorded on the row, and the pool already states which family each term belongs to.

**Every view is ordered by date and nothing else**, exactly as ADR-0010 requires. No row is ranked against another, and no row carries a number.

**Precedence is which view the operator opens first.** The ordering lives in his head and in the order the views are listed, not in the data.

**This is within ADR-0010, and the boundary is stated so it can be enforced:**

- Allowed: a label derived from a named term, and separate views over that label.
- **Not allowed**: any numeric weight per family, any sort that mixes families in one ordered list, and any assignment of a family by anything other than the matched term. A model that reads a description and decides a row is "really" agentic is the thing ADR-0010 forbids, and it would arrive looking like an improvement to this record.

**Not yet built.** The pool's four headings are read as one flat list today; `load_title_pool` takes the whole Terms section and discards the headings, so no family label reaches a row. Carrying the label is work that follows the Airtable writer, since views are where it becomes visible.

### Consequences

The operator sees his preferred kind of role first without anything having been ranked.

The loader must parse the pool's headings rather than flattening them, and a row gains a family field that the schema does not currently have. Both are small, and both must land before the writer projects families.

A term's family can change when the pool is reordered, which changes a row's label on a later projection. Because the label is derived rather than stored at admission time, that is a re-derivation and not a rewrite.

Four views mean four places to look, which is worse than one if the operator would rather see everything by date. One view holding every family, ordered by date, remains available and is what exists today.

### Confirmation

For every admitted row, the family label must be recomputable from the matched term alone. Take the filtered file, recompute, and compare against what the display holds: any disagreement means something other than the term decided a label.

The check that can fail: construct a title matching terms in two families, for example one that matches both `agentic` and `software engineer`. It must be credited to the higher family by the pool's order, deterministically, on every run. If the label depends on anything else, the derivation is not a lookup.

## Pros and Cons of the Options

### Order by family, then date, in one list

Good, because the operator sees his preference in a single place.
Bad, because a single ordered list where position encodes preference is a ranking, whatever it is called, and ADR-0010 forbids it.

### Score by family

Good, because it generalises to more dimensions later.
Bad, because it is precisely what ADR-0010 exists to prevent, and a score cannot be explained by naming a rule.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | The term-to-family map is built | `load_title_pool` read the pool's four headings and discarded them, so no family label could reach a row. `load_term_families` in `src/filters.py` now maps all 79 terms to their heading, and `TitleMatcher.family_of` exposes it. Built for ADR-0044's third star attribute; the views this record describes are still unbuilt, and still wait on the writer |
## More Information

Answers question F of the 2026-09-17 architecture brief. ADR-0010 carries a Changes row pointing here.

ADR-0031 covers why the family list is configuration. The pool's headings and their order are in `docs/reference/title-pool.md`.
