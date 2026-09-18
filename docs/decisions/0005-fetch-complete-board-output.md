---
status: accepted
topic: fetching
description: A board's complete output is fetched and filtered in code rather than queried at the source. Why nothing is asked of the board but its list.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0005: Fetch complete board output, filter locally

## Context and Problem Statement

Postings can be requested selectively, where the source supports it, or fetched whole and filtered afterwards.

The ATS board endpoints in the source registry offer no meaningful server-side filtering. The Greenhouse boards API returns an employer's complete job list. The Lever postings API returns the complete posting set for a slug. There is no predicate to push down.

Server-side filtering, where it exists, discards non-matching results before they can be observed.

## Decision Drivers

- Filter defects must be observable, per ADR-0001.
- Employer boards are small, so bandwidth is not a consideration.
- Adapters should have one responsibility.

## Assumptions

- Employer boards carry between five and fifty open roles. Stated from registry inspection; the distribution is not measured.
- No board in the registry offers a filter parameter that would materially reduce the fetch. Verified for Greenhouse and Lever only.

## Considered Options

- Request only matching postings where the source supports it.
- Request complete board output and filter in code.

## Decision Outcome

Chosen option: "request complete board output and filter in code".

We will request the complete output of every board. We will filter in code as a separate pass, and we will record the rule that caused every drop.

### Consequences

The drop log becomes the primary diagnostic artefact. A location rule rejecting everything appears as a thousand location drops rather than as an empty table.

Filters can be changed without refetching, because the raw layer already holds everything.

Non-technical postings from large employers are fetched and stored. ADR-0016 governs keeping them out of the display.

Adapters carry no filtering logic, so filter rules exist in one place rather than once per platform.

### Confirmation

The run log records, per board, postings fetched and postings dropped by each rule. Confirmed working when a deliberately narrowed rule shows a corresponding rise in that rule's drop count.

## Pros and Cons of the Options

## More Information

Does not apply to search APIs or aggregators, which are out of scope as sources per ADR-0012.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-10 | Consequences said "ADR-0008 and ADR-0016 govern", now names ADR-0016 only | ADR-0008 was already extended by ADR-0016 when this was written, so naming both implied a retired record still governed |
