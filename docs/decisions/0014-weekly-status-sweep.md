---
status: accepted
topic: display
description: A weekly sweep reads outcomes, persists them, then deletes the rows, and the four-status taxonomy the operator marks rows with.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0014: Weekly status sweep, with a four-status outcome taxonomy

## Context and Problem Statement

ADR-0004 specified that the pipeline performs no reads against Airtable, to protect the free-tier call allowance. That decision made the operator's hand-set outcomes unreachable: they exist only in Airtable and were never read back. Any measurement or learning that depends on them was therefore impossible.

The operator sets an outcome on each row and then deletes it. Without a read, those judgements are destroyed at deletion.

Two kinds of rejection are distinguishable and carry different meaning. A row rejected because the pipeline should not have surfaced it is a defect signal. A row rejected because the operator chose not to apply, for reasons of their own, is not. Merged, they either make the filters look broken when they were fine, or hide real defects behind ordinary preference.

Airtable's create endpoint takes ten records per call; list returns 100 per page; the allowance is 1,000 calls per month.

## Decision Drivers

- Operator judgements are the only feedback the pipeline gets and are currently discarded.
- The 1,000-record ceiling requires rows to leave the base.
- Pipeline defects must be distinguishable from operator preference.
- The call budget must accommodate reads without threatening writes.

## Assumptions

- A weekly sweep reading a full base costs about ten list calls, so about forty a month against writes at about ninety. Calculated from Airtable's documented page size and allowance; not measured in operation.
- Outcome reasons drawn from a fixed list will cover most cases. Not measured; the list will need revision once real rejections accumulate.

## Considered Options

- No reads, outcomes lost at deletion.
- Airtable automations pushing outcomes outward.
- A scheduled sweep that reads outcomes, persists them, then deletes the rows.

## Decision Outcome

Chosen option: "a scheduled sweep that reads outcomes, persists them, then deletes the rows".

We will run a weekly sweep that reads rows whose status is set, writes them to an outcomes log on the data branch, and only then deletes them from Airtable. We will write before deleting, never the reverse.

We will record outcomes in one file with a status discriminator, not one file per status, so a row has exactly one outcome.

We will use four statuses:

- `applied`. A marker that clears the row. The application record itself stays with the resume workflow.
- `rejected_pipeline`, with a reason from a fixed list: wrong title match, location wrong, expired at surfacing, experience level, duplicate. Each reason names a filter.
- `rejected_choice`, with an optional reason: employer, compensation, stack, recently applied to this employer, seniority in substance.
- `expired_before_review`. Fresh when surfaced, closed before the operator reached it.

We will hide reviewed rows from the working view with an Airtable view filtered to rows where status is empty, which requires no API calls at all.

### Consequences

Operator judgements become permanent and queryable.

A cluster of one `rejected_pipeline` reason is a work item naming its own filter, rather than a vague sense that filtering is off.

`expired_before_review` measures the cost of the operator's absences without conflating it with pipeline performance.

The base stays under the 1,000-record ceiling without manual pruning.

The pipeline now reads Airtable, so the call budget carries reads as well as writes. At roughly 130 calls a month against 1,000 this is comfortable, but it is no longer negligible.

The sweep is safe during absences because it touches only rows with a status set.

A failed sweep leaves rows in Airtable with statuses set. This is recoverable: the next sweep picks them up.

### Confirmation

After the first sweep, confirm every deleted row appears in the outcomes log with its status and date. Monthly, check the Airtable usage counter stays under 200 calls.

## Pros and Cons of the Options

### Airtable automations

Good, because no pipeline code is needed.
Bad, because the free plan allows 100 automation runs a month and the mechanism is outside version control.

## More Information

Reverses one clause of ADR-0004, its no-read rule. ADR-0004 otherwise stands and remains the record of why Airtable is the display layer.

That clause was an error: it made ADR-0015's Measure A unmeasurable, because the operator's hand-set outcomes exist only in Airtable and would have been destroyed at deletion without ever being read.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-10 | Said it superseded ADR-0004, now says it reverses one clause of it | ADR-0004's other decisions still hold. Claiming supersession would have sent a reader away from a live record |
