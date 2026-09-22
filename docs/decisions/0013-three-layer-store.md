---
status: accepted
topic: storage
description: The filtered set is persisted in its own file on the data branch and Airtable is a projection of that file. Why the display is never authoritative.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0013: Three layers, with the filtered set persisted independently of the display

## Context and Problem Statement

ADR-0001 established a raw layer and a filtered layer. ADR-0004 placed the filtered layer in Airtable, which made Airtable both the filtered store and the display.

That conflation has three consequences. Airtable's 1,000-record ceiling limits the filtered set, not just what is on screen. Deleting a row to keep the base under that ceiling destroys the record. And a change in Airtable's free-tier terms, or loss of the base, loses the filtered history.

The raw layer is already persisted independently under ADR-0002.

## Decision Drivers

- The operator removes rows from the display once they are applied to or rejected, so the display cannot be the durable record.
- Measure A in ADR-0015 needs first-appearance timestamps to survive row deletion.
- Exit cost: a free hosted service should hold a projection, not an authority.

## Assumptions

- The filtered set is a small fraction of the raw set, so its storage cost is a small fraction again of ADR-0003's estimate. Not measured; depends on filter selectivity, which is unknown until the first run.

## Considered Options

- Keep the filtered layer in Airtable only.
- Persist the filtered layer on the data branch and treat Airtable as a projection of it.

## Decision Outcome

Chosen option: "persist the filtered layer on the data branch, Airtable as a projection".

We will write the filtered set to its own file on the data branch, alongside the raw layer, under the same append-delta rule as ADR-0003. We will treat Airtable as a projection of that file. We will never treat Airtable as authoritative for anything the pipeline writes.

### Consequences

Losing the Airtable base, exhausting its ceiling, or a terms change costs a display tool, not data.

Rows can be deleted from Airtable freely, which is what makes the sweep in ADR-0014 safe.

Switching display tool later costs one small writer rather than a redesign.

A third write path exists. Three files on the data branch now carry pipeline state: raw, filtered, and the outcomes log from ADR-0014.

The filtered file and the Airtable base can drift if a write to one succeeds and the other fails. The run log must record both write results.

### Confirmation

Delete a row from Airtable by hand and confirm it is still present in the filtered file on the data branch with its first-seen timestamp intact.

## Pros and Cons of the Options

## More Information

Extends ADR-0001. Related to ADR-0014, which defines how outcomes set in the display return to the data branch.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | The projection copies the filtered file, and a rule change backfills the file first | ADR-0030. Copying the file as it stands is what 'a projection of that file' means, and it is accurate only if the file tracks the rules in force. Re-applying the chain at projection time was rejected because it would make the filtered file a log rather than the thing the display reads |
| 2026-09-18 | The projection applies the current chain rather than copying the file as it stands | ADR-0040. "A projection of that file" was read as a straight copy, which would show rows the current rules reject: measured, 11 of the 24 rows in `filtered.json`. Added late: this pointer was missing when ADR-0040 was written, which left this record's own Changes table silent about the record that changed it |
