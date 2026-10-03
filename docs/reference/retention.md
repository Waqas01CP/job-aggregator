---
type: reference
description: How long a classified row stays in Airtable, when its outcome is written to its store, and which clock governs each table. The operator's numbers.
status: current
---

# Retention

**The flow is ADR-0050 as of 2026-09-25.** It supersedes ADR-0046, which the
citations below name because it decided each item at the time. ADR-0050 adds a
third fifteen-day period, for a posting that has closed, and moves the copy
step to every fetch.

A classified row has one period, fifteen days, applied twice on two different
clocks. Neither is the posting's publication date or its first-seen date,
because neither moves when a classification changes. A row nobody classified
has a clock of its own, the table's last row, and that one is first-seen:
with no classification there is nothing else to measure from.

| Table | Clock | Value | What happens at the end |
|---|---|---|---|
| `Jobs` | `Classified at`, a `lastModifiedTime` field watching `Status` | **15 days** | The sweep writes the row to its ADR-0043 store, with its reason, or for an accepted row its `Stage`, read from the matching copy in the same run, verifies the write, then deletes the row from `Jobs` |
| `rejected-not-a-fit` | `Classified`, a `createdTime` field | **15 days** | The sweep deletes the row. Its outcome is already in the store |
| `rejected-poor-filtering` | `Classified`, a `createdTime` field | **15 days** | The sweep deletes the row. Its outcome is already in the store |
| `accepted` | none | never | Nothing, unless the operator sets `Delete`. See below |
| `Jobs`, unreviewed | `First seen` | **30 days** | ADR-0055's clock, added 2026-09-30: the sweep writes the row to `outcomes/removed_unreviewed.json` with the reason `unreviewed-aged-out`, verifies the write on a later run, then deletes it. It never comes back. `unreviewed_after_days` in `config/sweep.json` |

**`accepted` is deleted by no clock.** Its rows are written to the accepted
store on the same 15-day clock as the others, so ADR-0044's star can read
them. No clock, no status change and no clear removes one from Airtable.
**The operator removes one by setting its `Delete` to yes** (D12,
2026-09-26). The next morning sweep saves the row, `Stage` as it stands
then, to `removed_copies.json`, and to the accepted store if it is not
there yet. A later sweep removes it from Airtable once both are read back
from GitHub, with its `Jobs` row if that is still there. That is the
tool the base's record cap needs. It never touches the store.

**A copy removed any other way is saved first, and a clear removes
nothing** (D12). A rejection copy whose row the operator reclassified goes
to `removed_copies.json` with its reason, then is deleted on a later run.
A cleared `Status` leaves every copy where it is.

**Nothing deletes from a store.** The three outcome stores, the removed-unreviewed and removed-copies stores, the filtered layer
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

The sweep has run since 2026-09-25 and has deleted rows since 2026-09-28:
25 public rows that day, each dropped by a rule (18 on location, 7 on age, in
the public removal store), and 44 aggregator rows on 09-29, inferred to be
rule drops since the count per step was not logged then. No
classification has reached its fifteen days: the first were marked on
2026-09-24, so the first come due about 2026-10-09 [inferred]. **A longer
window is the cheaper mistake until that clock has run cleanly for a few
cycles.** Shortening it is the operator's call and a one-line change in
`config/sweep.json`.

## What the two clocks do not buy

Both start when the classification is set, so the copy in a rejection table
and the row in `Jobs` expire at about the same time. The copies do not extend
how long a row is visible. What they provide is the reason fields, which live
on the classification tables rather than in `Jobs`, and a grouped view of one
outcome.

**The reason reaches the store from the copy.** On day 15 the sweep reads
the row from `Jobs` and its reason from the matching copy, in the same run,
and writes both. A status change discards nothing (D12, 2026-09-26): the old
rejection copy is saved with its reason to `removed_copies.json` before it is
deleted, and an old accepted copy stays. An accepted row carries its `Stage`,
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

**That store is read by the projection's skip by reason** *(since 2026-09-30,
ADR-0043's row of 2026-09-28; until then it was not read at all, and a
retired closed row came straight back)*. ADR-0040 requires a row that fell
out on a narrowed rule to reappear if the rule widens again, so a row stored
with a rule's name returns when the rule admits it, and so does one stored
because another member became its group's display row. Every other reason
keeps the row out: `closed`, `unreviewed-aged-out` and `operator-removed`,
and any reason added later. The latest record for a row decides, and a row
that returns and later leaves again for another reason gets a second record
before it is deleted.

## The operator's clearing tool

ADR-0055. He clears one table by an age threshold, on demand, from the fetch
workflow's dispatch: a table, a number of days (15, 30 or any he gives), and
a confirmation box. `Jobs` is measured on the publication date; the three
classification tables on `Classified`, when the copy arrived. A run without
the box ticked is a dry run: it reports what it would remove and changes
nothing. A ticked run is refused unless a dry run of the same table and days
ran within `clearing_dry_run_valid_hours` of `config/sweep.json`, 48, and it
removes only the rows that dry run listed: one that crossed the threshold
since is left and counted (the fourth audit's F1, 2026-10-01). The dry run
names a public row in the run log, and an aggregator's, with its title and
employer, in the private repository's `clearing/dry_runs.json`, outside the
outcome stores so that it can never be read as one (ADR-0055, 2026-10-03).
Clearing `Jobs` takes a classified row's rejection copy with it, and the dry
run counts those rows by status.

**The tool writes stores and deletes nothing.** An unreviewed `Jobs` row is
stored with `operator-removed`; a classified row or a rejection copy has its
classification saved in its corpus, marked as his removal, so it leaves
before its fifteen days; an `accepted` copy gets `Delete` set, and D12's path
does the rest. The next daily sweep deletes once origin holds the record.
Deleting in the browser instead does not stick: the next projection sends
the row back.

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

The sweep and the clearing tool, from `config/sweep.json`: `retire_after_days`
(15), `unreviewed_after_days` (30) and `clearing_dry_run_valid_hours` (48).
This file was written before the sweep, so the sweep was built to the
operator's numbers rather than ones chosen during implementation; it now
says what each number is and why, and the configuration is what the code
reads. Per ADR-0031 they are configuration, not constants in a module, and
changing one is a dated row there and here, never a code change.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-01 | Four statements the file contradicted corrected: the clocks paragraph now names the first-seen clock, the sweep has run, a status change discards nothing (D12), and the numbers are read from `config/sweep.json`. The clearing tool removes only what its dry run listed | The fourth audit's F12 and F1 |
| 2026-09-30 | ADR-0055's thirty-day clock for unreviewed rows and the operator's clearing tool added; the removal store is now read by reason | Brief 8. `Jobs` had no clock for a row nobody marked, the one unbounded quantity in the system, and rows deleted in the browser came back within about fourteen hours |
| 2026-09-26 | `accepted` rows leave Airtable on the operator's `Delete`, saved first; a superseded rejection copy is saved before it goes; a clear removes nothing | The operator's D12, answering the audit of 2026-09-25's F1, which found a clear or a status change deleting an `accepted` copy and its `Stage`. The separate tool this file named is the `Delete` field |
| 2026-09-23 | A fourth removal added, on no clock: unreviewed rows the chain no longer admits, stored with the rule that dropped them | ADR-0046 step 4, on the operator's decision. It closes ADR-0040's unowned removal and preserves the `expired_before_review` signal, which ADR-0046 retired as a status |
| 2026-09-22 | An accepted row carries its `Stage` to the store the same way | The operator's decision; ADR-0046 extended |
| 2026-09-22 | The `Jobs` row and a new paragraph say where the stored reason comes from: the matching copy, read in the same run | ADR-0046's step 2 read only `Jobs`, where no reason lives, so no reason would have reached a store. Closed in ADR-0046 on the operator's decision |
| 2026-09-20 | Two clocks of 3 and 14 days become one period of 15 days on two clocks, and `Jobs` gains a clock of its own | ADR-0046 replaced classification-by-moving with classification-by-status, so a row now sits in `Jobs` with a status rather than leaving it. A separate early store write no longer helps: the operator can change a status after it, leaving the store holding an outcome he has reversed. One write at the moment of deletion removes that case, and the row is visible in Airtable the whole time, so nothing is at risk. The 15 is the operator's number |
| 2026-09-18 | File created. Write at 3 days, delete at 14 | The operator's decision, splitting ADR-0045's single retention period into two clocks. He chose 14 over his stated preference of 7 as a starting value, because nothing in this path has run yet and a longer window is the cheaper mistake while that is true |
