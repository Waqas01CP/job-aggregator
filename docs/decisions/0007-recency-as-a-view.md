---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0007: Recency is a view, not an ingest filter

## Context and Problem Statement

The operator wants to see postings that went live recently. This can be implemented at ingest, by requesting or retaining only postings inside a time window, or at presentation, by ordering.

The operator's existing LinkedIn pipeline filters at ingest, passing `f_TPR=r86400` to request only the last 24 hours.

That approach has two properties in this context. A failed or skipped run permanently loses its window, because the next run looks only at the last 24 hours and postings published during the gap are never observed. And a source that exposes no publication date returns nothing under a strict recency filter.

The operator states that periods of one to ten days without reading the table are expected.

## Decision Drivers

- GitHub documents that scheduled runs may be delayed or dropped under load, producing no error.
- An unknown number of ATS platforms in the registry expose no publication date.
- Absences of up to ten days are expected and must not cause loss.

## Assumptions

- A material number of registry platforms expose no reliable publication date. Asserted from the source registry's own notes; verified for no platform in this session.
- Postings remain on their board for days rather than hours, so a missed run recovers on the next. Stated from the operator's experience of postings aged 24 hours to three weeks.

## Considered Options

- Filter at ingest on a 24-hour publication window.
- Ingest everything and order by date at presentation.

## Decision Outcome

Chosen option: "ingest everything and order by date at presentation".

We will ingest everything a board returns without reference to publication date. We will record a first-seen timestamp on every record at ingestion. We will present recency by ordering the display on publication date descending, falling back to first-seen where publication date is absent, and we will record which of the two supplied the ordering date.

### Consequences

A missed run costs latency, not data. The next run observes everything still on the board.

Boards with no publication date remain usable, ordered by first-seen instead.

Measure A is computable on the subset carrying a real publication date, and the coverage of that subset is itself measurable.

The display contains postings older than 24 hours. Ordering handles this; no filtering is required.

Records must distinguish the ordering date's origin, so a first-seen fallback is never mistaken for a publication date.

### Confirmation

Deliberately skip one scheduled run and confirm the following run ingests the postings published during the gap. Also report publication-date coverage per platform in the run log from the first run.

## Pros and Cons of the Options

## More Information

The ingest-filter failure mode described here is live in the operator's LinkedIn pipeline and is the reason this decision goes the other way.
