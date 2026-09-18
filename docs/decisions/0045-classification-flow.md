---
status: accepted
topic: display
description: The operator classifies by moving a row to one of three tables; the sweep writes it to its store, verifies the write, then deletes. Supersedes ADR-0014's sweep. Accepted is never deleted automatically.
date: 2026-09-18
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0045: The classification flow

## Context and Problem Statement

ADR-0014 decided a weekly sweep that reads a row's status, writes it to an outcomes log, and deletes it from Airtable. ADR-0043 then split that one log into three stores, because the three outcome classes have different readers.

The mechanism ADR-0014 chose no longer fits what it feeds. Setting a status on a row and having a sweep interpret it puts the classification in a field, where the operator must remember which of four values means what, and where a mis-set status is invisible until something reads it. Moving a row to a table named for the outcome puts the classification in the row's location, which is unambiguous and which Airtable's interface makes a drag rather than a form.

That changes enough of ADR-0014's Decision Outcome that this is a supersession rather than another clause reversal: the trigger changes, the cadence changes, the deletion rule changes, and one of the three outcomes stops being deleted at all.

**One thing in ADR-0014 must not change, and this record inherits it: write before deleting, never the reverse.** ADR-0014 got that right, and the failure it prevents is unrecoverable.

## Decision Drivers

- A classification the operator performs by hand should be one action, not a field edit plus a reason edit.
- The store is the durable record; Airtable is a projection. Rows may leave Airtable, but only once the store has them.
- The `accepted` table is the record of what he applied to. Losing it is not recoverable from the pipeline, because the pipeline never knew he applied.
- Airtable's call allowance is finite and this flow adds daily reads and deletes to a budget that previously carried writes only.

## Assumptions

- The operator will move rows rather than set statuses. **Not established.** No row has been classified, because the display has never received one.
- Classified volume is small, on the order of tens a week. **Sourced** from 25 display rows after grouping; not measured.
- A retention period is long enough to notice a cluster by eye. **Assumed, not measured**, and it is the operator's number: it lives in configuration under ADR-0031, not in code. *(Annotated 2026-09-18: this read "30 days". The operator set two periods instead, 3 days to write to the store and 14 to delete from Airtable, and they are in `docs/reference/retention.md`. See Changes.)*
- Airtable's delete endpoint accepts up to 10 records per call, as its create endpoint does. **Sourced** from Airtable's documentation, not exercised.

## Considered Options

- Keep ADR-0014's status-and-sweep, with the sweep routing to three stores.
- Classification by moving a row to a table named for the outcome.
- Three Airtable views over one table, filtered by status.

## Decision Outcome

Chosen option: "classification by moving a row".

**The operator classifies by hand.** He moves a row from `Jobs` to one of `rejected-not-a-fit`, `rejected-poor-filtering` or `accepted`. **The pipeline never deletes a row from `Jobs` because of a classification**; a row leaves `Jobs` because he moved it.

**The clock starts when the row arrives in the classification table.** Each classification table carries a `Classified` field of type `createdTime`, set by Airtable when the record is created there. It is not the posting's publication date, not its first-seen date, and not when it was surfaced. It cannot be forgotten or mis-set, because nothing sets it by hand.

**The two rejection tables auto-delete after the retention period**, measured from `Classified`. `accepted` does not. *(Annotated 2026-09-18: one period became two. The store write happens at 3 days and the delete at 14, so a row is durable long before it stops being visible. The ordering invariant below is unchanged and the gap it guards is now eleven days wide rather than seconds. See Changes.)*

**Write, verify, then delete. Never the reverse.** For each row past its retention:

1. Write the row to its store under ADR-0043, through the same append-delta writer and the same ADR-0020 split as every other store.
2. **Verify** by reading the store back and confirming the row's `Identity` is present in it.
3. Delete from Airtable only for rows that passed step 2.

A row that fails verification is left in Airtable and reported. The next sweep picks it up. An unverified row is never deleted, and no batch deletes on the strength of another row's success.

**`accepted` is deleted by hand only.** The sweep writes its rows to the accepted store, so ADR-0044's star can read them, and stops. Nothing automated removes a row from that table, because it is the record of what the operator applied to and an automated deletion there destroys something the pipeline cannot reconstruct.

**The main table loses its two reason fields.** `Pipeline reason` and `Choice reason` now live on the classification table each belongs to, so a reason has one home rather than two. `Status` stays, and of its four values only `expired_before_review` is still set in `Jobs`: the other three are expressed by moving the row.

### The call budget, in arithmetic

ADR-0004 sized the allowance at roughly 33 calls a day, about 1,000 a month, and assumed no reads at all. ADR-0014 added the sweep's reads and estimated about 130 a month. This flow adds three daily reads and deletes, so the figure is recomputed here rather than assumed to fit.

| Operation | Calls | Per month |
|---|---|---|
| Projection upserts, 2 runs a day, batched 10 per call | 1 per run | 60 |
| Projection reads `Jobs` to find rows that fell out (ADR-0040) | 1 per run | 60 |
| Sweep reads the three classification tables, daily | 3 per day | 90 |
| Deletes from the two rejection tables, batched 10 per call | up to 2 per day | 60 |
| **Total** | | **about 270** |

**About 27% of the allowance**, against ADR-0014's 130. It fits, with room, and it is no longer negligible.

Two things keep it there, and both are worth stating because losing either changes the answer. `Jobs` holds display rows, which ADR-0037 groups: 281 filtered rows collapse to about 25, so one list call reads the whole table and pagination never starts. And deletes batch: one call per ten rows, not one per row.

**Do not build this yet.** Everything here needs the Airtable token, which does not exist. This record specifies the build so that it is not designed again when the token arrives.

### Consequences

Classification becomes one action, and the row's location is its classification, which cannot disagree with itself the way a status field and a reason field can.

The sweep becomes daily rather than weekly, because retention is measured per row rather than per sweep. It reads three tables whether or not anything was classified.

A failed verify leaves a row in Airtable indefinitely until the store write succeeds. That is the intended failure: a row stuck in a table is visible, and a row deleted before it was stored is gone.

`accepted` grows without bound until the operator prunes it. That is the trade for never losing an application record, and it is the table least likely to grow fast.

ADR-0014's four-status taxonomy survives only as `expired_before_review` plus the three table names. The statuses themselves are no longer how the operator expresses an outcome.

The budget moves from about 13% to about 27% of the allowance. A third classification table, or losing the grouping that keeps `Jobs` to one page, would move it again.

### Confirmation

**The verify step must be seen refusing.** Give the sweep a row whose store write did not happen, by pointing it at a store missing that identity, and confirm it does not delete and reports the row. A verify nobody has seen refuse is not a verify, and this one guards an unrecoverable action.

Then the ordinary case: classify a row, run the sweep past its retention, and confirm the store holds it before Airtable stops holding it. Reverse the order in a test double and the test must fail.

For `accepted`: run the sweep against a row past any retention period and confirm the row is still in Airtable afterwards. If it is gone, the table that must never be auto-deleted is being auto-deleted.

## Pros and Cons of the Options

### Keep the status-and-sweep

Good, because it is decided, and because a status field is one API write rather than a record move.
Bad, because the operator must remember which of four statuses means what, a mis-set status is invisible, and the reason lives in a second field that can disagree with the first.

### Three views over one table

Good, because it needs no new tables and no moves.
Bad, because a view is a filter over a status, so it keeps every problem of the status field and adds a layer that looks like structure but is not. Deleting from a view deletes from the table.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | One retention period becomes two clocks: write to the store at 3 days, delete from Airtable at 14 | The operator's decision, which outranks this record under ADR-0022. The ordering invariant is untouched and is strengthened: write, verify, then delete, with the gap between write and delete widened from seconds to eleven days. A row is durable from day 3 and visible until day 14, so a sweep that fails for a week loses nothing and a cluster of one reason is still on screen to be noticed. He prefers 7 days for the delete and chose 14 as a starting value, because nothing in this path has run yet. Both numbers are configuration in `docs/reference/retention.md`, not constants |

## More Information

Supersedes ADR-0014, which carries a Changes row and a superseded marker pointing here. ADR-0043's three stores are what this writes to. ADR-0044's star reads the accepted store.

ADR-0035's field ownership still holds: the pipeline writes only its own fields, and `Status`, the reasons and `Stage` are the operator's.

The tables exist and are verified: `docs/reference/airtable-schema.md`.
