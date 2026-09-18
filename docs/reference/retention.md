---
type: reference
description: How long a classified row stays in Airtable and when it is written to its outcome store. Two separate clocks, both the operator's numbers.
status: current
---

# Retention

Two periods, both measured from `Classified`, the `createdTime` field Airtable
sets when a row arrives in a classification table. Neither is measured from
when the posting was published or when it was surfaced.

| Period | Value | What happens |
|---|---|---|
| **Write to store** | **3 days** | The sweep writes the row to its ADR-0043 store and verifies the write |
| **Delete from Airtable** | **14 days** | The sweep deletes the row from the classification table |

**Only the two rejection tables are deleted from.** `accepted` is written to
its store on the same 3-day clock and is **never deleted automatically**, per
ADR-0045. That table is the record of what the operator applied to.

## Why two clocks and not one

ADR-0045 originally wrote, verified and deleted as one operation at a single
retention period. The operator separated them on 2026-09-18, and the
separation is worth more than it looks.

**The row is safe from day 3 and visible until day 14.** Writing early means
an outcome is durable long before anything is deleted, so a sweep that fails
for a week loses nothing. Deleting late means the operator can still see what
he classified, and can still spot a cluster by eye: four rows in
`rejected-poor-filtering` all admitted by the same pool term is a work item,
and it is only visible while the rows are together on a screen.

**The ordering invariant is untouched and is what matters.** Write, verify,
then delete, never the reverse. Separating the clocks widens the gap between
write and delete from seconds to eleven days, which makes the invariant harder
to violate rather than easier.

## Why 14 and not 7

The operator's stated preference is 7 days and his starting value is 14. The
reason is that nothing here has ever run: no row has been classified, no sweep
has executed, and no store has been written. **A longer window is the cheaper
mistake while that is true.** If the sweep has a defect, 14 days of rows are
still on screen to notice it with; at 7 days half of them would be gone before
anyone looked.

Shorten it to 7 once the sweep has run cleanly for a few cycles. That is the
operator's call and it is a one-line change here.

## What reads these numbers

Nothing yet. The sweep is unbuilt and blocked behind the Airtable writer.
**This file exists before the code so the sweep is built to these numbers
rather than having them chosen during implementation**, which is where a
number nobody decided usually comes from.

Per ADR-0031 these are configuration, not constants in a module: the sweep
loads them from here, and changing one is a documented act with a dated row
below, never a code change.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | File created. Write at 3 days, delete at 14 | The operator's decision, splitting ADR-0045's single retention period into two clocks. He chose 14 over his stated preference of 7 as a starting value, because nothing in this path has run yet and a longer window is the cheaper mistake while that is true |
