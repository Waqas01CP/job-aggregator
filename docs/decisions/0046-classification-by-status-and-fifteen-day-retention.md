---
status: accepted
topic: display
description: The operator classifies by setting one status in Jobs; the sweep copies the row out, then writes, verifies and deletes it at fifteen days. A stored outcome keeps a row out of the projection. Supersedes ADR-0045.
date: 2026-09-19
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0046: Classification by status, and the fifteen-day retention

## Context and Problem Statement

ADR-0045 decided that the operator classifies a row by moving it from `Jobs` to one of three tables. Airtable has no move operation. The route it does offer is copy, paste into the target table, then delete the original: three actions rather than one, and one that writes a row without its `Identity` if that field is hidden in the source view.

The same record left the projection free to recreate a row that had left `Jobs`. ADR-0040 re-applies the current rules to the whole filtered layer on every run and projects every row it admits. ADR-0035 upserts on `Identity` and matches only rows present in `Jobs`. Neither consults the outcome stores. A row deleted under ADR-0045's retention therefore returns on the next run. This is read from the three records, not observed, because the writer does not exist.

Two forces pull against each other. A row's location is unambiguous, but the interface cannot produce it in one action. A status field is one action, but it puts the classification in a field that can be mis-set, and a separate reason field can disagree with it. That second objection is what ADR-0045 moved away from.

## Decision Drivers

- Classification must be one action performed by hand.
- A row the operator has classified must never reappear in `Jobs`.
- The store is the durable record. Airtable is a projection.
- The `accepted` table is the record of what he applied to, and the pipeline cannot reconstruct it.
- The free base caps records across all tables, so copies are not free.
- A classification must be reversible for long enough to notice it was wrong.

## Assumptions

- The operator sets one status rather than moving a row. **Stated** by him, 2026-09-19.
- A `lastModifiedTime` field can be restricted to watch one named field. **Sourced** from the Airtable connector's field-creation schema, inspected 2026-09-19. Not exercised: no such field exists yet.
- Fifteen days is long enough to change a classification and to see a cluster by eye. **Stated** by him. Not measured, and configuration under ADR-0031 rather than a constant.
- Classified volume is on the order of tens a week. **Sourced** from the 25 display rows ADR-0037's grouping produces. Not measured.
- Airtable's delete endpoint accepts up to 10 records per call, as its create endpoint does. **Sourced** from Airtable's documentation, not exercised. Carried from ADR-0045.
- The free plan caps a base at 1,000 records across all its tables. **Sourced** from Airtable's published plan limits. Not re-verified in this session, and the accepted-prune tool is the only thing that rests on it.

## Considered Options

- ADR-0045's move, performed by hand as copy, paste and delete.
- One status field in `Jobs`, with the pipeline performing the copy and the deletion.
- One status field with three filtered views and no copies at all.
- An Airtable automation or a paid extension to perform the move.

## Decision Outcome

Chosen option: "one status field, with the pipeline performing the copy and the deletion".

**The operator classifies by setting `Status` on the row in `Jobs`.** Its values are `not fit`, `poor filtering`, `accepted` and `expired_before_review`, the last of which only the pipeline sets. Empty means not yet reviewed, and the "To review" view shows exactly those rows.

**`Jobs` carries a `Classified at` field of type `lastModifiedTime` watching `Status` alone.** It is empty until a status is set, it moves when the status changes, and nothing sets it by hand. The projection's writes leave it alone, because it watches one field the pipeline never writes.

**The clock is never the posting's dates.** `Published` and `First seen` do not move when a classification changes, and a row classified long after it was surfaced would be deleted on the day it was classified. `Classified at` in `Jobs`, and `Classified` in each classification table, are the only clocks this record recognises.

**The sweep runs daily and does three things in this order.**

1. **Copy.** Every row in `Jobs` with an operator status and no copy in the matching table is created there. A row whose status changed since its copy was made has the old copy deleted and a new one created, which resets that table's `Classified`.
2. **Store, verify, delete from `Jobs`.** For each row whose `Classified at` is more than fifteen days old: write it to its store under ADR-0043, read the store back and confirm its `Identity` is present, then delete it from `Jobs`. A row that fails verification stays and is reported, and no row is deleted on the strength of another row's success. *(Extended 2026-09-22: where the reason and `Stage` come from. See Changes.)*
3. **Delete from the rejection tables.** A row in `rejected-not-a-fit` or `rejected-poor-filtering` whose `Classified` is more than fifteen days old is deleted. Its outcome reached the store in step 2.

**Write, verify, then delete. Never the reverse.** Inherited unchanged from ADR-0045 and from ADR-0014 before it.

**A stored outcome keeps a row out of the projection.** The writer reads the three outcome stores and skips any identity present in any of them. This is what makes a deletion final, and it extends ADR-0040.

**`accepted` is deleted by no clock.** Step 2 writes accepted rows to the accepted store so ADR-0044's star can read them, and step 3 does not touch that table. A separate tool, run by the operator when he chooses, deletes accepted rows from Airtable alone so the base stays under its record cap. It never touches a store.

**Nothing deletes from a store.** The three outcome stores, the filtered layer and the raw layer stay append-only. The accepted store is the file the operator opens in other software, and it stays complete whether or not the Airtable rows do.

### The call budget, in arithmetic

| Operation | Calls | Per month |
|---|---|---|
| Projection upserts, 2 runs a day, batched 10 per call | 1 per run | 60 |
| Projection reads `Jobs` to find rows that fell out, per ADR-0040 | 1 per run | 60 |
| Sweep reads `Jobs` for statuses and clocks | 1 per day | 30 |
| Sweep creates copies, batched 10 per call | up to 1 per day | 30 |
| Sweep reads the three classification tables | 3 per day | 90 |
| Sweep deletes from `Jobs`, batched 10 per call | up to 1 per day | 30 |
| Sweep deletes from the two rejection tables, batched 10 per call | up to 2 per day | 60 |
| **Total** | | **about 360** |

**About 36% of the allowance**, against ADR-0045's 270 and ADR-0014's 130. This is arithmetic from the operations above, not a measurement, and no run has made an Airtable call. The two things holding it there are unchanged: ADR-0037's grouping keeps `Jobs` to one page, and writes and deletes batch ten to a call.

### Consequences

Classification is one action, and the operator does nothing Airtable does not support in one click.

The pipeline now deletes rows from `Jobs` on a classification, which ADR-0045 forbade in terms. The protection that rule provided is replaced by the verify step and by the stored-outcome skip: a row leaves `Jobs` only after the store is confirmed to hold it, and never comes back.

A classification is final fifteen days after it is set. Once the row has left `Jobs` there is no field to change, because the classification tables carry no status. Reversing a classification after that means editing a store by hand, which this record does not provide for.

The copies buy no extra viewing time, because both clocks start together. What the rejection tables provide is the reason fields and a grouped view of a cluster, not a longer window.

A status field can be mis-set, and a mis-set status is invisible until the sweep acts on it. Fifteen days is the whole of the protection against that.

`accepted` grows until the operator prunes it, and the prune is now a tool rather than hand deletion.

The budget moves from about 27% to about 36% of the allowance. A fourth classification table, or losing ADR-0037's grouping, moves it again.

### Confirmation

**The verify step must be seen refusing.** Point the sweep at a store missing an identity it has just claimed to write, and confirm it does not delete and reports the row. A verify nobody has seen refuse is not a verify, and this one guards an unrecoverable action. Carried from ADR-0045.

**The skip must be seen both ways.** Delete a row from `Jobs` whose outcome is in a store, run the projection, and confirm it is not recreated. Then remove that identity from the store, run the projection again, and confirm it **is** recreated. Only the second half proves the skip is reading the store rather than failing to project.

**The clock must be seen moving.** Set a status and confirm `Classified at` populates. Change the status and confirm it moves, and that the copy is deleted and recreated with a fresh `Classified`.

**`accepted` must be seen surviving.** Run the sweep against an accepted row well past fifteen days and confirm it is still in Airtable and present in the accepted store.

## Pros and Cons of the Options

### ADR-0045's move, by hand

Good, because the row's location is its classification and the two cannot disagree.
Bad, because Airtable has no move: it is three actions, and a hidden `Identity` in the source view produces a row the verify step can never clear.

### Three filtered views, no copies

Good, because it costs no records and no create calls, and the reason fields could live in `Jobs`.
Bad, because the reason fields would return to the main table, which ADR-0045 emptied deliberately, and a cluster of one reason is harder to see next to unreviewed rows.

### An automation or a paid extension

Good, because the operator's action stays one click.
Bad, because Airtable automations cannot delete records, so the pipeline would still delete; the free allowance for automation runs is disputed between sources and was not measured; and an extension is paid, which the standing cost constraint excludes.

## More Information

Supersedes ADR-0045, which carries a superseded marker pointing here. The supersession is case 2 of the Decision Record Standard: the question is the same and the answer is different.

Extends ADR-0040, which gains a note: the projection now skips identities held in the outcome stores.

ADR-0043's three stores are what this writes to. ADR-0044's star reads the accepted store. ADR-0035's field ownership still holds: the pipeline writes only its own fields, and `Status` and the reasons are the operator's.

**Carried forward from ADR-0045 unchanged**, so that superseding it retires nothing still in force: `Pipeline reason` and `Choice reason` stay on the classification table each belongs to rather than in `Jobs`, so a reason has one home; the clock in each classification table is its `Classified` field of type `createdTime`; and write, verify, then delete is inherited from ADR-0014 through ADR-0045 to here.

Unbuilt at the time of writing. The `Status` choices and the `Classified at` field do not exist yet, and `docs/reference/airtable-schema.md` predates them.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | Step 2 now says where the reason comes from. On day 15 the row is written from `Jobs` and its reason from the matching copy, read in the same run. A status change discards the old copy's reason, because it belonged to the old classification | The reason fields live only on the copies, and step 2 read only `Jobs`, so no reason would have reached a store, against ADR-0043, whose outcome records carry "the reason where one was given". Found by the architecture chat, decided by the operator. No extra calls: the sweep already reads the three classification tables daily |
| 2026-09-22 | `Stage` travels the same way. An accepted row is written with the `Stage` its `accepted` copy holds on day 15, shortlisted or applied, read in the same run | `Stage` lives only on the `accepted` copy, so without this the accepted store could not tell a shortlisted role from one applied to. The operator's decision. A `Stage` changed after day 15 does not reach the store; that is open as a separate question |
