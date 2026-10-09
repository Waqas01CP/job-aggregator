---
status: accepted
topic: filtering
description: Everything is ingested and recency is applied when ordering the display, never when deciding what to keep. Why an old posting is still stored.
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

- A material number of registry platforms expose no reliable publication date. Asserted from the source registry's own notes; verified for no platform in this session. *(Annotated 2026-09-24, stale: checked since across 16 platforms. Manatal exposes no date field of any kind and Dover's board carries none; `logs/2026-09-16-publication-date-across-untested-platforms.md`.)*
- Postings remain on their board for days rather than hours, so a missed run recovers on the next. Stated from the operator's experience of postings aged 24 hours to three weeks.

## Considered Options

- Filter at ingest on a 24-hour publication window.
- Ingest everything and order by date at presentation.

## Decision Outcome

Chosen option: "ingest everything and order by date at presentation".

We will ingest everything a board returns without reference to publication date. We will record a first-seen timestamp on every record at ingestion. We will present recency by ordering the display on publication date descending, falling back to first-seen where publication date is absent, and we will record which of the two supplied the ordering date. *(Changed 2026-10-09: a posting with no publication date is shown after every dated posting rather than by first sight, the operator's rule of 2026-10-07 UTC. See Changes.)*

### Consequences

A missed run costs latency, not data. The next run observes everything still on the board.

Boards with no publication date remain usable, ordered by first-seen instead. *(Since 2026-10-07 UTC: shown after every dated posting.)*

Measure A is computable on the subset carrying a real publication date, and the coverage of that subset is itself measurable.

The display contains postings older than 24 hours. Ordering handles this; no filtering is required. *(Corrected 2026-09-26: **the second sentence is false.** Ordering did not handle it, and the operator said so on opening the table. ADR-0052 filters the display on age, judged once at first sight. This record's four rules are untouched, including the one that matters most here: nothing is filtered at ingest, so the rows ADR-0052 keeps out of the display are still stored. See Changes.)*

Records must distinguish the ordering date's origin, so a first-seen fallback is never mistaken for a publication date.

### Confirmation

Deliberately skip one scheduled run and confirm the following run ingests the postings published during the gap. Also report publication-date coverage per platform in the run log from the first run.

## Pros and Cons of the Options

## More Information

The ingest-filter failure mode described here is live in the operator's LinkedIn pipeline and is the reason this decision goes the other way.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-24 | The unverified date-coverage claim annotated as stale | Checked across 16 platforms on 2026-09-16. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
| 2026-09-26 | The consequence "Ordering handles this; no filtering is required" is false, and named as such. ADR-0052 filters the display on age. **No rule of this record is reversed:** ingest everything, record first seen, order on publication date descending with a first-seen fallback, and record which supplied the ordering date, are all four in force and all four verified live on 2026-09-28 over 346 stored rows | The operator opened the table and found postings he would not apply to, so the consequence was falsified by use. It is a consequence and not a rule, which is why this record keeps its status and its Decision Outcome: the decision was never to leave old postings in the display, it was to avoid filtering at ingest, and that is exactly what ADR-0052 also avoids. The corpus now holds three positions on recency, and ADR-0052's More Information sets out why they do not conflict |
| 2026-10-09 | A posting with no publication date is shown after every dated posting, not ordered by first sight: it is sent with an empty `Order date`, which a latest-first sort places last. The first-seen fallback for ordering is reversed for the display; first sight is still recorded on every row, and such a posting is kept and never dropped for age | The operator's rule, 2026-10-07 UTC, on integrating Manatal, whose postings carry no date: "if a job board does not offer dates then we can make a simple new rule that those that do not have dates are at the end because no job should be skipped". That blanks sort last is from Airtable's own support documentation, read by the implementing seat. Built with Manatal's adapter, commits `0cfcdd1` and `62d11de` |
