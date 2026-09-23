---
type: reference
description: How long a classified row stays in Airtable, when its outcome is written to its store, and which clock governs each table. The operator's numbers.
status: current
---

# Retention

One period, fifteen days, applied twice on two different clocks. Neither clock
is the posting's publication date or its first-seen date, because neither of
those moves when a classification changes.

| Table | Clock | Value | What happens at the end |
|---|---|---|---|
| `Jobs` | `Classified at`, a `lastModifiedTime` field watching `Status` | **15 days** | The sweep writes the row to its ADR-0043 store, with its reason, or for an accepted row its `Stage`, read from the matching copy in the same run, verifies the write, then deletes the row from `Jobs` |
| `rejected-not-a-fit` | `Classified`, a `createdTime` field | **15 days** | The sweep deletes the row. Its outcome is already in the store |
| `rejected-poor-filtering` | `Classified`, a `createdTime` field | **15 days** | The sweep deletes the row. Its outcome is already in the store |
| `accepted` | none | never | Nothing. See below |

**`accepted` is deleted by no clock.** Its rows are written to the accepted
store on the same 15-day clock as the others, so ADR-0044's star can read
them, but nothing removes them from Airtable. A separate tool, run by the
operator when he chooses, deletes accepted rows from Airtable alone so the
base stays under its record cap. It never touches the store.

**Nothing deletes from a store.** The three outcome stores, the filtered layer
and the raw layer stay append-only. The accepted store is the file the
operator opens in other software, and it stays complete whether or not the
Airtable rows do.

## Why the clock in `Jobs` is a last-modified field

The operator asked for a classification to be reversible: a row he sent to
`accepted` and then reconsidered should get a fresh window, not the remainder
of the old one.

`Published` and `First seen` cannot do that. Neither moves when a status
changes, and a row left unreviewed for twenty days and then classified would
be deleted on the day it was classified.

`Classified at` watches `Status` and nothing else. It is empty until a status
is set, so an unreviewed row is never deleted by this clock. It moves when the
status changes, so the window restarts by itself. The pipeline never writes
`Status`, so the projection's own writes leave it alone.

## Why fifteen days

It is the operator's number, chosen on 2026-09-19. It has to cover two things
at once: long enough to notice a wrong classification and change it, and long
enough that a cluster of one reason is still on screen to be seen. Four rows
in `rejected-poor-filtering` all admitted by the same pool term is a work item,
and it is only visible while the rows are together.

Nothing here has ever run. No row has been classified, no sweep has executed,
and no store has been written. **A longer window is the cheaper mistake while
that is true.** Shorten it once the sweep has run cleanly for a few cycles.
That is the operator's call and it is a one-line change here.

## What the two clocks do not buy

Both start when the classification is set, so the copy in a rejection table
and the row in `Jobs` expire at about the same time. The copies do not extend
how long a row is visible. What they provide is the reason fields, which live
on the classification tables rather than in `Jobs`, and a grouped view of one
outcome.

**The reason reaches the store from the copy.** On day 15 the sweep reads
the row from `Jobs` and its reason from the matching copy, in the same run,
and writes both. A status change discards the old copy's reason, because it
belonged to the old classification. An accepted row carries its `Stage`,
shortlisted or applied, the same way. A `Stage` changed after day 15 does not
reach the store. ADR-0046, Changes rows of 2026-09-22.

## What has no clock at all

**A row that fell out, unreviewed, goes at the next sweep.** ADR-0046's step
4: a row in `Jobs` with an empty `Status` that the current chain no longer
admits is written to `outcomes/removed_unreviewed.json` with the rule that
dropped it, verified, then deleted. There is no fifteen days here, because
nothing was classified: the row is gone from the display because the rules
say it does not belong there, and the store is what keeps the fact.

A row dropped by the expiry rule is the event ADR-0014 called
`expired_before_review`: it was fresh when surfaced and closed before the
operator reached it. A row dropped by a narrowed pool term is a different
event with the same shape, and the stored rule name is what tells them apart.

**That store is not read by the projection's skip.** ADR-0040 requires a row
that fell out on a narrowed rule to reappear if the rule widens again, and
only the three classification stores make a removal final.

## The ordering invariant

Write, verify, then delete. Never the reverse. Inherited from ADR-0014 through
ADR-0045 to ADR-0046 and unchanged throughout. A row that fails verification
stays in Airtable and is reported, and no row is deleted on the strength of
another row's success.

## After the row leaves `Jobs`

A classification is final at fifteen days. The classification tables carry no
status field, so once the row has left `Jobs` there is nothing left to change.
Reversing a classification after that means editing a store by hand, which no
record provides for.

## What reads these numbers

Nothing yet. The sweep is unbuilt. **This file exists before the code so the
sweep is built to these numbers rather than having them chosen during
implementation**, which is where a number nobody decided usually comes from.

Per ADR-0031 these are configuration, not constants in a module: the sweep
loads them from here, and changing one is a documented act with a dated row
below, never a code change.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | A fourth removal added, on no clock: unreviewed rows the chain no longer admits, stored with the rule that dropped them | ADR-0046 step 4, on the operator's decision. It closes ADR-0040's unowned removal and preserves the `expired_before_review` signal, which ADR-0046 retired as a status |
| 2026-09-22 | An accepted row carries its `Stage` to the store the same way | The operator's decision; ADR-0046 extended |
| 2026-09-22 | The `Jobs` row and a new paragraph say where the stored reason comes from: the matching copy, read in the same run | ADR-0046's step 2 read only `Jobs`, where no reason lives, so no reason would have reached a store. Closed in ADR-0046 on the operator's decision |
| 2026-09-20 | Two clocks of 3 and 14 days become one period of 15 days on two clocks, and `Jobs` gains a clock of its own | ADR-0046 replaced classification-by-moving with classification-by-status, so a row now sits in `Jobs` with a status rather than leaving it. A separate early store write no longer helps: the operator can change a status after it, leaving the store holding an outcome he has reversed. One write at the moment of deletion removes that case, and the row is visible in Airtable the whole time, so nothing is at risk. The 15 is the operator's number |
| 2026-09-18 | File created. Write at 3 days, delete at 14 | The operator's decision, splitting ADR-0045's single retention period into two clocks. He chose 14 over his stated preference of 7 as a starting value, because nothing in this path has run yet and a longer window is the cheaper mistake while that is true |
