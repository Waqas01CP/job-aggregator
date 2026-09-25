---
status: accepted
topic: display
description: The whole classification flow in one record: one status in Jobs, the copy on every fetch, fifteen days on two clocks, closed postings marked and retired, and what keeps a classified row out of the display. Supersedes ADR-0046.
date: 2026-09-25
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0050: The classification flow, consolidated

## Context and Problem Statement

ADR-0046 decided this flow on 2026-09-19 and was amended eight times in six days: the reason's source, `Stage`, the status vocabulary, the retirement of a status the pipeline set, the sweep's fourth step, the group-wide skip and the measured budget. The Decision Record Standard makes eight amendments a supersession trigger, because a decision read as an original plus a pile of rows is no longer one decision anyone can hold in mind.

Two changes now due would be the ninth and tenth. The operator asked that a classification appear in its table without waiting a day, which changes the sweep's cadence. And his decision D3 of 2026-09-24 adds a rule the old record has no place for: a posting that has closed should stay visible for fifteen days and then be retired like any classified row.

Separately, the display has a growth problem that the old record did not face. `Jobs` fills and nothing empties it: 44 rows at the first projection, no removal path until this sweep exists, against a base capped at 1,000 records. Measured on 2026-09-24 over `filtered.json`: `expires_at` is empty on all 345 stored rows, so the expiry rule never fires, and 65 rows were absent from their boards at the latest run. Closed roles therefore accumulate silently, and the event ADR-0046 named as `expired_before_review` could never be recorded.

## Decision Drivers

- Classification must stay one action the operator performs by hand.
- A row he has classified must never reappear in `Jobs`.
- A closed role must leave the display, and he must be able to see that it closed before it goes.
- The store is the durable record; Airtable is a projection.
- The free plan allows 1,000 API calls a month per workspace, and exceeding it starts a grace period available once ever.
- The base is capped at 1,000 records across all tables, and only this flow can empty it.

## Assumptions

- Fifteen days is long enough to change a classification and to see a cluster by eye. **Stated** by the operator. Carried from ADR-0046.
- A posting absent from its board on four consecutive runs that polled that board has closed. **Chosen by the chat** from the two-a-day cadence, so four runs is about two days, and not measured. It needs the operator's approval before the sweep is built, and the number is configuration under ADR-0031 rather than a constant.
- Airtable's delete endpoint accepts ten records a call, as its create endpoint does. **Sourced** from Airtable's documentation, not exercised. Carried from ADR-0046.
- The free plan caps a base at 1,000 records across its tables, and a workspace at 1,000 API calls a month with a once-only 30-day grace period. **Sourced** from Airtable's help centre, read 2026-09-25, and recorded in ADR-0004's Changes.
- Classified volume is on the order of tens a week. **Sourced** from the 29 public display groups measured 2026-09-25. Not measured as a rate.

## Considered Options

- Keep ADR-0046 and amend it twice more.
- Consolidate, with the copy on every fetch and closed postings retired on their own clock.
- Consolidate, and delete a closed row as soon as it is detected.
- Consolidate, and let closed rows accumulate until the operator prunes them by hand.

## Decision Outcome

Chosen option: "consolidate, with the copy on every fetch and closed postings retired on their own clock".

**Everything below is in force. Where it repeats ADR-0046, that is deliberate, so this record can be read alone.**

### What the operator does

**He classifies by setting `Status` on the row in `Jobs`.** Its three values are the names of the tables they feed: `rejected-not-a-fit`, `rejected-poor-filtering` and `accepted`. Empty means not yet reviewed, and the "To review" view shows exactly those rows.

**The pipeline never writes `Status`, without exception.** It is the one field whose loss cannot be reconstructed, and the client has no way to send it.

### The clocks

**`Jobs` carries `Classified at`**, a `lastModifiedTime` field watching `Status` alone. It is empty until a status is set and it moves when the status changes. Watching one field is what keeps a projection write from restarting the clock.

**Each classification table carries `Classified`**, a `createdTime` field set when the sweep creates the copy.

**`Jobs` gains `Closed`**, a pipeline-owned date field, empty until the pipeline decides a posting has closed. It is not `Status`, so writing it disturbs no other clock, and it is classified pipeline-owned under ADR-0035.

**No clock is ever the posting's own dates.** `Published` and `First seen` do not move.

### The sweep

**The copy step runs with every fetch, twice a day. Every other step runs once a day.** A classification then appears in its table within twelve hours rather than twenty-four, which is what the operator asked for, and the step is idempotent: it creates a copy only for a row that has none.

1. **Copy.** Every row in `Jobs` with a status and no copy in the matching table is created there. A row whose status changed since its copy was made has the old copy deleted and a new one created, which resets that table's `Classified` and discards the old copy's reason, because that reason belonged to the old classification.
2. **Store, verify, delete from `Jobs`.** For each row whose `Classified at` is more than fifteen days old: write it to its ADR-0043 store, with its reason, or for an accepted row its `Stage`, read from the matching copy in the same run; read the store back and confirm its `Identity` is present; then delete it from `Jobs`. A row that fails verification stays and is reported, and no row is deleted on the strength of another row's success.
3. **Delete from the rejection tables.** A row in `rejected-not-a-fit` or `rejected-poor-filtering` whose `Classified` is more than fifteen days old is deleted; its outcome reached the store in step 2. **`accepted` is deleted by no clock**, because it is the record of what he applied to; a tool he runs clears it from Airtable alone, never from the store.
4. **Mark what has closed.** A row in `Jobs` with an empty `Status` whose posting has closed gets `Closed` set to the date the pipeline first saw it closed. It stays in the display, marked, so he can see it closed rather than finding it gone.
5. **Retire what closed, fifteen days on.** A row whose `Closed` is more than fifteen days old is written to `outcomes/removed_unreviewed.json` with the reason `closed`, verified, then deleted from `Jobs`. This is the event ADR-0014 called `expired_before_review`, now recorded rather than inferred.
6. **Remove what a rule dropped, at once.** A row with an empty `Status` that the current chain no longer admits, for any reason other than closure, is written to the same store with the rule that dropped it and deleted at the next sweep, with no clock: the rules say it does not belong in the display, and ADR-0040 requires the display to converge on the current rules.

**A posting has closed when either holds.** Its own expiry date has passed, which is the expiry rule the chain already applies. Or it was absent from its board on **four consecutive runs that polled that board**. **A run that did not poll the board never counts**, which matters because ADR-0048 skips Himalayas on the evening run, and counting those would close every aggregator row in two days.

**Write, verify, then delete. Never the reverse.** Inherited from ADR-0014 through ADR-0045 and ADR-0046.

### What keeps a classified row out of the display

**A stored outcome keeps a row out for good.** The projection skips a display group when **any member's** identity is present in one of ADR-0043's three classification stores.

**`outcomes/removed_unreviewed.json` is not read by the skip.** A row removed because a rule narrowed must be able to return if the rule widens again, per ADR-0040, and a closed row will not return because the closure test still holds.

**A projected row carries its group representative's identity**, as `src/dedupe.py` chooses it.

### The cost, and the guard

**Measured 2026-09-24**: the projection spent 5 calls for 44 groups, and two test runs 6 each at 54 and 56 groups. **Reproduced by the chat 2026-09-25** from `filtered.json` at `data` head `def4f935`: 39 groups over 345 rows, 334 admitted, 29 groups, 3 calls for the public rows alone.

| Operation | Calls | Per month |
|---|---|---|
| Projection upserts, 2 runs a day, at 44 groups | 5 per run | 300 |
| Sweep copy step, with every fetch, batched 10 per call | up to 1 per run | 60 |
| Sweep reads `Jobs` | 1 per day | 30 |
| Sweep reads the three classification tables | 3 per day | 90 |
| Sweep deletes from `Jobs`, batched 10 per call | up to 1 per day | 30 |
| Sweep deletes from the two rejection tables | up to 2 per day | 60 |
| Sweep marks `Closed`, batched 10 per call | up to 1 per day | 30 |
| **Total** | | **about 600** |

**About 60% of the allowance**, and the figure moves with the aggregator count rather than the row count. **The run log reports the month to date from both branches' logs, and says so loudly once the month's total passes 60% before the fifteenth.** That is the guard the operator asked for on 2026-09-25: the trajectory is raised, not the breach, because the grace period is available once ever.

### Consequences

A classification lands in its table within twelve hours, and a closed role is visible as closed for fifteen days before it goes.

`Jobs` now empties. Every row leaves by one of four routes: classified and retired at fifteen days, closed and retired at fifteen days, dropped by a rule and removed at once, or deleted by hand from `accepted`. Nothing else removes a row, and nothing removes one silently.

The pipeline writes one more field, `Closed`, which is one more field an upsert could overwrite wrongly. It is pipeline-owned, so the cost of a mistake is a wrong date rather than lost review data.

The budget rises from about 450 to about 600 a month, because the copy step doubles and marking costs calls. At about 100 aggregator groups the allowance binds, and the guard above is what gives warning.

A closed row sits in the display for fifteen days, so the display holds roles he cannot apply to. That is the trade he chose: seeing that a role closed is worth more than a shorter list.

The four-run closure test will close a role that a board hides temporarily and then restores. The row returns on the next projection if the chain still admits it, because the removal store is not read by the skip.

### Confirmation

**The verify step must be seen refusing.** Point the sweep at a store missing an identity it has just claimed to write, and confirm it does not delete and reports the row.

**The skip must be seen both ways, and at the member level.** An identity in a classification store is not projected; removed from the store, it is. Then put a non-representative member of a group in a store and confirm the whole group is skipped.

**The closure test must not fire on a skipped board.** Run four evening runs with Himalayas skipped and confirm no Himalayas row gains a `Closed` date. This is the check that can fail, and it is the one that matters, because the aggregator rows are the ones the test would wrongly close.

**`Closed` must be seen appearing and then retiring.** Set a posting absent on four consecutive polling runs, confirm `Closed` is stamped and the row stays, then advance fifteen days and confirm it reaches the store with reason `closed` and leaves `Jobs`.

**The clock must not move on a projection write.** Project twice and confirm no `Classified at` and no `Classified` changes.

**`accepted` must be seen surviving.** Run the sweep against an accepted row well past fifteen days and confirm it is still in Airtable and in the accepted store.

**The month's count must be seen crossing the line.** Feed the report a month of logs summing past 60% before the fifteenth and confirm it says so.

## Pros and Cons of the Options

### Keep ADR-0046 and amend it twice more

Good, because it writes no new record.
Bad, because it takes that record to ten amendments, which the standard treats as a decision eroded past recognition, and a reader would have to assemble the flow from eight rows.

### Delete a closed row as soon as it is detected

Good, because the display holds only live roles and the base stays small.
Bad, because a role disappears with no trace for the operator, and a board that hides a posting for a day would remove a row he was about to read.

### Let closed rows accumulate until pruned by hand

Good, because it needs no closure test and no new field.
Bad, because it is the behaviour measured on 2026-09-24, where 4 of 29 display groups had no member left on its board, and it walks into the 1,000-record cap with no warning.

## More Information

**Supersedes ADR-0046**, which carries the pointer back. ADR-0046 in turn superseded ADR-0045, and ADR-0045 superseded ADR-0014, so the chain is followable from any of them.

**Carried forward unchanged from ADR-0046**, so that superseding it retires nothing still in force: write, verify, then delete; `Pipeline reason` and `Choice reason` on the classification table each belongs to, so a reason has one home; `Stage` on `accepted` and its trip to the store on day 15; `accepted` deleted by no clock; nothing ever deleted from a store; the three stores and their contents per ADR-0043; and the reason the `Classified at` field watches one field.

ADR-0040 owns the projection that re-applies the current rules and the convergence this record's steps 5 and 6 deliver. ADR-0043 owns the stores, including the fourth, `removed_unreviewed.json`. ADR-0035 owns field ownership, which `Closed` is classified under. ADR-0048 owns the poll cadence that makes a skipped board possible, which step 4's counting rule exists for. ADR-0049 requires the checks above to be fitness functions where they guard a rule rather than a feature. ADR-0004 owns the allowance and its grace period.

The operator's decisions this record carries: the status names, 2026-09-24; the reason and `Stage` reaching the store, 2026-09-22; the group-wide skip, 2026-09-23; D3, closed postings visible for fifteen days then retired, 2026-09-24; the copy on every fetch, 2026-09-25; and the call-trajectory guard, 2026-09-25.

## Changes
