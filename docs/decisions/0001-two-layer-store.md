---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0001: Two-layer store, raw and filtered

## Context and Problem Statement

The pipeline fetches complete job listings from employer ATS boards and applies hard filters before presenting anything for review.

A design storing only rows that pass the filters leaves filter defects unobservable. If the location filter rejects every row because a board writes "Karachi, Sindh" where the matcher expects "Karachi, Pakistan", the symptom is an empty table, which looks identical to a quiet market. There is no artefact to inspect and no way to establish which postings were dropped or why.

The filters will meet real board data for the first time at go-live, and will need adjustment as platforms are added.

## Decision Drivers

- Filter defects must be detectable after the fact, not only at the moment they occur.
- Filters will change over the life of the project.
- Storage of text records at this volume is cheap.

## Assumptions

- Postings fetched per run across the full board set are on the order of one thousand. Estimated from 53 boards at roughly twenty open roles each; not measured.
- No filter will ever require data beyond what the board returns at fetch time.

## Considered Options

- Store only postings that pass the filters.
- Store every fetched posting raw, filter as a separate pass, store the result separately.

## Decision Outcome

Chosen option: "store every fetched posting raw, filter as a separate pass".

We will store every fetched posting in a raw layer, unfiltered and permanent. We will apply filters as a separate pass whose output is written to a distinct layer. We will record the filter verdict and drop reason against every posting.

### Consequences

Filters become falsifiable: any filter can be re-run over full history and the set it would drop can be enumerated.

Filter errors become recoverable rather than permanent. A filter that was too aggressive can be loosened and its rows recovered without refetching.

The raw layer accumulates indefinitely and needs a medium that tolerates unbounded growth. Addressed in ADR-0002 and ADR-0003.

Storage is paid for postings that will never be reviewed. At text-only volumes this is negligible.

Two write paths exist instead of one.

### Confirmation

Within the first week of live running, re-run the location filter over the raw layer with a deliberately broken match rule and confirm the drop set is enumerable and matches the count in the run log.

## Pros and Cons of the Options

## More Information

Extended by ADR-0013, which persists the filtered layer independently of the display.
