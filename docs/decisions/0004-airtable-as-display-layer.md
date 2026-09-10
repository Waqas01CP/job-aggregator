---
status: superseded by ADR-0014
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

We will write the filtered layer to an Airtable base using batched creates of ten records per call. We will perform no reads. We will determine novelty entirely from repository-side state.

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

Superseded by ADR-0014. The no-read rule made the falsifier unmeasurable, because the operator's hand-set outcomes exist only in Airtable and were never read back.
