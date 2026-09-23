---
status: accepted
topic: display
description: Airtable's free plan is the display layer, written by batched calls and never read back. What the operator actually opens.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0004: Airtable as the filtered display layer

## Context and Problem Statement

ADR-0001 requires a filtered layer presented for review. The requirement includes a status column set by hand, which rules out a file in the repository, since the pipeline would overwrite manual edits on the next run.

Airtable's free plan, verified September 2026: 1,000 records per base, 1,000 API calls per month per workspace enforced since January 2025, five requests per second, five editors, 100 automation runs per month.

The call allowance is roughly 33 a day. The create-records endpoint accepts ten records per call; list-records returns 100 per page.

## Decision Drivers

- A status column set by hand requires an editable interface.
- The free-tier call allowance is small enough to shape the design.
- Cost constraint: free by default.

## Assumptions

- Rows are removed once applied to or rejected, so the 1,000-record ceiling is not approached. Depends entirely on manual pruning happening.
- Read access to Airtable is not needed by the pipeline. This assumption was wrong; see ADR-0014.

## Considered Options

- A file in the repository, edited by hand.
- Airtable free plan.
- A hosted database with a UI.

## Decision Outcome

Chosen option: "Airtable free plan".

We will write the filtered layer to an Airtable base using batched creates of ten records per call. We will perform no reads. *(Clarified 2026-09-23: this clause was reversed by ADR-0014 for the sweep, which must read. The projection still performs no reads, and what survives for every component is that Airtable is never authoritative. See Changes.)* We will determine novelty entirely from repository-side state.

### Consequences

Manual status editing works, which is the requirement that eliminated file-based alternatives.

API usage sits at roughly five to nine percent of the free allowance.

Airtable never holds authoritative state and can be rebuilt from the data branch.

The 1,000-record ceiling requires ongoing manual pruning. Failure to prune stops writes, so the run must detect and log write rejections.

A single uncorroborated source reports an August 2026 acquisition agreement by Bending Spoons. If free-tier terms change, only the display is affected.

### Confirmation

Check the Airtable workspace API usage counter monthly against the 1,000-call allowance.

## Pros and Cons of the Options

## More Information

One clause of this record was reversed by ADR-0014: the no-read rule. The rest stands. Airtable remains the display layer, writes remain batched at ten per call, and the record ceiling is still managed as described.

The reversed clause and why: the no-read rule made ADR-0015's Measure A unmeasurable, because the operator's hand-set outcomes exist only in Airtable and would have been destroyed at deletion.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-10 | Status was `superseded by ADR-0014`, now `accepted` with the reversed clause named | ADR-0014 reverses one clause, not the decision. Marking the whole record superseded retired the Airtable choice, which is still in force and is depended on by ADR-0013 and the architecture document |
| 2026-09-17 | Batched creates become upserts matched on Identity | ADR-0035. Plain creates are not idempotent, so a retry after an unknown outcome duplicates rows the operator cannot distinguish from real second postings. 'We will perform no reads' is unaffected: an upsert matches server-side and the pipeline still learns nothing from Airtable |
| 2026-09-17 | The writer becomes a separate client rather than part of the shared fetch module | ADR-0034. Airtable's writes differ from board fetches in verb, authentication, budget, rate limit and failure semantics. Retry, backoff and circuit breaking become shared utilities both import, which is what CLAUDE.md's rule actually protects |
| 2026-09-23 | The no-read clause is stated exactly: the **projection** performs no reads, the **sweep** reads, and the rule that survives for both is that Airtable is never the source of truth | Four documents disagreed about whether "we will perform no reads" still stood. This record's Assumptions and More Information say ADR-0014 reversed it; its own 2026-09-17 row and ADR-0035 say an upsert leaves it intact; ADR-0046 budgeted a projection read. Both narrower statements are about upserts, not about the blanket rule. Resolved by giving every read to the sweep, which already reads `Jobs` daily and which now owns ADR-0046's step 4, so the projection needs no read at all and the budget loses one line. Novelty still comes from the seen store and no read changes what the pipeline stores. The operator's decision, 2026-09-23 |
