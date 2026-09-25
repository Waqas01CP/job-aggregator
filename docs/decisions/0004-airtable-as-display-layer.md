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

API usage sits at roughly five to nine percent of the free allowance. *(Annotated 2026-09-24, stale: ADR-0046 budgets about 45%, and the first production projection, 2026-09-24T03:27Z, made 5 calls where ADR-0046 assumed 3.)*

Airtable never holds authoritative state and can be rebuilt from the data branch.

The 1,000-record ceiling requires ongoing manual pruning. Failure to prune stops writes, so the run must detect and log write rejections.

A single uncorroborated source reports an August 2026 acquisition agreement by Bending Spoons. If free-tier terms change, only the display is affected.

### Confirmation

Check the Airtable workspace API usage counter monthly against the 1,000-call allowance. *(Extended 2026-09-25: where to look, what exceeding costs, and who else spends it. See Changes.)*

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
| 2026-09-24 | The API usage figure annotated as stale | ADR-0046's budget and the first production run's measured calls. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
| 2026-09-25 | The allowance is stated exactly, with where to read it and what exceeding it costs. Workspace settings, Usage tab, "Public API calls" for the current month, per base: Airtable's documentation says detailed usage analytics are available on Free plans, which this is. Exceeding the 1,000 calls starts a **30-day grace period, available once ever**, after which calls are blocked until the month resets. There is no warning before the limit. **Every client on the workspace spends it**, including the Airtable connector the architecture chat reads the schema with, so the pipeline's own count in its run logs is a floor and not the total | Read from Airtable's help centre, "Managing API call limits in Airtable", 2026-09-25. This record sized the allowance and set a monthly check without saying where the counter is, what happens at the limit or that a second client exists. The grace period changes what exceeding means: it is survivable once and then not, so the guard has to be a trajectory rather than a breach. The projection's measured cost and the growth that moves it are in ADR-0046's Changes row of 2026-09-25 |
