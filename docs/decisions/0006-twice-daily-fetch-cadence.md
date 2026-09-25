---
status: accepted
topic: fetching
description: The pipeline fetches twice a day, and the propagation assumption that cadence rests on.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0006: Twice-daily fetch cadence

## Context and Problem Statement

Discovery latency is determined by polling interval once board-side propagation is accounted for.

Once daily gives a worst case of 24 hours and an average of 12. Twice daily gives 12 and 6. Three times daily gives 8 and 4.

The operator reads the table intermittently, sometimes not for several days. GitHub Actions minutes are free on public repositories, so additional runs carry no compute cost, and the Airtable call budget accommodates three runs a day. *(Unmeasured when written. Measured from 2026-09-24: the projection spends 3 to 6 Airtable calls a run, and ADR-0050 budgets the whole flow at about 600 of the 1,000 a month at two runs a day, so a third run a day is no longer clearly accommodated.)*

The operator's existing LinkedIn pipeline runs once daily at 04:00 UTC and has completed over 100 consecutive runs.

## Decision Drivers

- Measure A in ADR-0015 requires median age at first appearance at or under 24 hours.
- Additional runs are free in compute and cheap in API calls.
- A failed run should not leave a long gap.

## Assumptions

- ATS boards publish to their APIs at or near the moment a posting goes live, so board-side propagation is near zero. **Confirmed 2026-09-11.** See Changes.
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

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-19 | Extended by ADR-0048: a source is polled no faster than its own documented refresh interval, and Himalayas moves to the morning run only. The twice-daily run cadence decided here is unchanged | This record's propagation assumption was confirmed for ATS boards and explicitly not for Himalayas, whose 5.27-hour floor was attributed to feed staleness. Himalayas' API reference states the cache refreshes every 24 hours, so the second poll of each day cannot return new data. ADR-0048 governs which sources a run asks, not how often the run happens |
| 2026-09-11 | The near-zero propagation assumption is confirmed, and the Confirmation is met | Greenhouse's youngest posting was 0.26 hours old at fetch, about 16 minutes, against a 2-hour bar. A quiet market would mean nothing recent existed; something published 16 minutes earlier was already in the feed, which is positive evidence rather than an absence of evidence for lag. A second run would tighten the bound and cannot change the verdict. Himalayas' 5.27-hour floor is its own feed staleness, and Lever's 35 hours is a volume artefact from 48 postings |
| 2026-09-25 | An unmeasured budget claim annotated with the measured cost | The corpus audit found this number outside Assumptions with no basis. Three production runs spent 5, 3 and 6 calls. Annotated by the implementing seat under ADR-RULES, on Brief 7's corpus work; the Decision Outcome is untouched. |
