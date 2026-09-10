---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0006: Twice-daily fetch cadence

## Context and Problem Statement

Discovery latency is determined by polling interval once board-side propagation is accounted for.

Once daily gives a worst case of 24 hours and an average of 12. Twice daily gives 12 and 6. Three times daily gives 8 and 4.

The operator reads the table intermittently, sometimes not for several days. GitHub Actions minutes are free on public repositories, so additional runs carry no compute cost, and the Airtable call budget accommodates three runs a day.

The operator's existing LinkedIn pipeline runs once daily at 04:00 UTC and has completed over 100 consecutive runs.

## Decision Drivers

- Measure A in ADR-0015 requires median age at first appearance at or under 24 hours.
- Additional runs are free in compute and cheap in API calls.
- A failed run should not leave a long gap.

## Assumptions

- ATS boards publish to their APIs at or near the moment a posting goes live, so board-side propagation is near zero. Not measured for any platform; assumed from the nature of the endpoints.
- The operator's reading cadence, not the polling interval, dominates the total publication-to-application gap. Stated by the operator.

## Considered Options

- Once daily.
- Twice daily.
- Three times daily.

## Decision Outcome

Chosen option: "twice daily".

We will run twice a day: once in the early PKT morning, capturing postings published overnight during North American and European working hours, and once in the early PKT evening, capturing postings published by Pakistani employers during their working day.

### Consequences

Worst-case discovery latency is 12 hours, clearing Measure A's 24-hour median bar by construction.

A single failed run leaves a gap of 12 hours rather than 24. ADR-0007 makes such a gap non-destructive.

Two commits a day on the data branch, which is the growth rate ADR-0003 is sized against.

Three runs a day remain available at no cost if measurement shows discovery dominating the gap, which is not expected.

### Confirmation

Measure A itself. If median age at first appearance exceeds 12 hours, the board-side propagation assumption above is wrong and should be investigated before the cadence is changed.

## Pros and Cons of the Options

## More Information
