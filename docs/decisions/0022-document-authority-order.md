---
status: accepted
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0022: Document authority order

## Context and Problem Statement

This repository holds an instruction file, an architecture document, twenty-one decision records, four research records, reference material, and a generated map. More artifacts are coming.

Any multi-document system eventually contains two documents that disagree. One is stale, or one was written before a decision that changed it, or two authors reached different conclusions on the same question. Nothing currently says which wins.

The cost lands on an agent rather than a human. A human reading two conflicting documents notices the conflict and asks. A session reads whichever it found first and proceeds, and the failure is silent.

Research pass 0004 found no source addressing document conflict, in any study, specification or practitioner writing surveyed across three passes. It found one working example: a precedence list in the operator's prior project, stating six levels from current conversation down to background material.

## Decision Drivers

- A session that finds a conflict must be able to resolve it without asking.
- The rule must be readable in one place and short enough to be remembered.
- Stale documents are inevitable; the order is what makes them survivable.

## Assumptions

- Conflicts will arise faster than they are noticed. Not measured; based on the operator's prior project finding two stale register lines that had been superseded without being rewritten.
- A fixed order is better than case-by-case judgement for an agent. This is the whole premise and it is untested here.

## Considered Options

- No stated order. Resolve conflicts by asking.
- Timestamp wins: the most recently edited document is authoritative.
- A fixed precedence order by document type.

## Decision Outcome

Chosen option: "a fixed precedence order by document type".

We will treat these as authoritative in descending order. Where two disagree, the higher one wins without exception.

1. **The operator's instruction in the current conversation.**
2. **`CLAUDE.md`.** The standing rules for working here.
3. **Decision records in `docs/decisions/`**, excluding any marked superseded. Where two records conflict and neither is superseded, that is a defect: raise it rather than choosing.
4. **`docs/architecture-2.0.md`.** The design as a whole.
5. **`docs/reference/`.** Registries, schemas, the title pool.
6. **`docs/research/`.** Dated snapshots. Evidence for decisions, never a decision.
7. **Everything else**, including `docs/architecture.md`, which is superseded and must never be implemented from.

We will state this order in `CLAUDE.md` so a session reads it before anything else, and we will not restate it in the architecture document.

### Consequences

A conflict has an answer that requires no judgement, which is what an agent needs.

Research records are explicitly demoted below decisions. A research finding does not change what the project does until a decision record says so. That is intended: three passes have produced findings that were partly wrong, and one contained a claim the operator had to correct.

Reference material sits below the architecture, so a stale registry cannot silently override the design.

The order says nothing about which document is *right*. A higher document can be wrong. What it prevents is a session picking arbitrarily and proceeding in silence.

Two unsuperseded records that conflict are a defect with no resolution rule, deliberately. Inventing one would let a real contradiction pass unreported.

### Confirmation

Give a session two documents that conflict, where the lower one is more recently edited, and confirm it follows the higher one and says which rule it applied. A session that resolves the conflict silently, or by recency, has not read the order.

## Pros and Cons of the Options

### Timestamp wins

Good, because it needs no maintenance.
Bad, because a typo fix on a reference file would outrank a decision record. Recency is not authority.

### Resolve by asking

Good, because a human sees every conflict.
Bad, because it stops an unattended scheduled run, and because most conflicts are not noticed as conflicts in the first place.

## More Information

The pattern is taken from the operator's prior project, which states a six-level order at the top of its principal design document. Evidence and the wider survey are in `docs/research/0004-project-context-documentation.md`.
