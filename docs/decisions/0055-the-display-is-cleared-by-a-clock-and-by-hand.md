---
status: accepted
topic: display
description: An unreviewed row leaves the display on a clock, and the operator can clear any table by an age threshold on demand. Both write to a store the projection reads by reason, because a row deleted in the browser comes back.
date: 2026-09-28
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0055: The display is cleared by a clock, and by hand

## Context and Problem Statement

ADR-0050 gives every classified row a way out of the display and gives an unreviewed row none. A row the operator never marks stays in `Jobs` for ever, unless a rule stops admitting it or the posting closes. Against a base capped at 1,000 records and a projection whose cost is linear in display rows, that is the one unbounded quantity in the system.

The operator raised it from the other end. He wanted to clear the table himself: "i decided i wanted to delete the last 1 month jobs and i selected that then it should delete the jobs which are older than 1 month", by table, with thresholds of a week, fifteen days and a month, and with `accepted` under his own control rather than a rule's. His purpose was a fresh start once he judged the system good enough to trust.

**A deletion in the browser does not stick, and that is the fact the whole record turns on.** The projection re-applies the current rules over the whole filtered layer on every run and upserts on `Identity`, and the only thing that keeps a row out is its identity sitting in a store the skip reads. So rows cleared by hand return within about fourteen hours. *(Corrected 2026-10-03, the fourth audit's F10: on the next run, which has been as much as 16.0 hours away.)* An hour spent tidying the table would be undone before the next morning.

## Decision Drivers

- The display must be bounded without the operator having to do anything.
- He must also be able to clear it deliberately, because a judgement about what is worth keeping is his.
- Deletion is the one irreversible act in this system, and a bulk selection is where a wrong threshold is cheapest to type.
- `accepted` holds what he applied to and cannot be reconstructed.
- Every ten rows in the display costs about sixty Airtable calls a month, so clearing the table is also a budget action.

## Assumptions

- Thirty days is long enough that nothing he would still act on is removed unseen. **Stated** by the chat and approved by him on 2026-09-28 as a starting value: it is double ADR-0050's fifteen-day retention window. It is configuration under ADR-0031, not a constant.
- He will sometimes be away for long enough that the clock matters. **Stated**: ADR-0007 records absences of one to ten days as expected, and he has since described a month as possible.
- Volume is small enough that a bulk removal is cheap in calls. **Measured**: `Jobs` held 126 rows on 2026-09-27, and deletes batch ten to a call.
- A publication-date threshold is the wrong axis for `Jobs`, and a seven-day one is dangerous. **Measured** 2026-09-28: of the 13 display groups ADR-0052 admits from the stored public layer, 11 were published more than seven days earlier, 3 more than fifteen days, and none more than thirty. A seven-day purge run that day would have removed 11 of 13 legitimate rows.

## Considered Options

- A clock only: an unreviewed row leaves after N days and nothing else changes.
- A tool only: he clears tables by threshold when he wants to, and nothing is automatic.
- Both, which is what he chose: "one is just to maintain while the other is manual meaning i can run whenever i want".
- Clearing rows in the Airtable browser, which is what a reader would try first.

## Decision Outcome

Chosen option: "both".

**The clock. An unreviewed row leaves the display thirty days after it was first seen**, written to `outcomes/removed_unreviewed.json` with the reason `unreviewed-aged-out`, verified, then deleted, on ADR-0050's write-verify-delete path and its two-run separation. Thirty days is configuration. Every removal is named in the run log with its identity, so an absence costs him a line to read rather than a row he never learns about.

**The tool. He clears a chosen table by an age threshold, on demand.** Per table, with a threshold of fifteen days, thirty days or a number he gives.

- **For `Jobs` the threshold measures the publication date**, as he asked.
- **For the three classification tables it measures `Classified`**, the date the copy arrived, because those rows are records of decisions he made and their age is the age of the decision rather than of the posting.
- **A dry run always comes first.** The first invocation reports, per table, how many rows it would remove, the oldest and newest publication dates among them, and how many are unreviewed. Nothing is removed until a second invocation carries an explicit confirmation.
- **`accepted` is never deleted by this tool.** It sets `Delete` to yes on the selected rows and D12's existing path in ADR-0050 does the saving and the removal. One deletion path on the one table that cannot be reconstructed.
- **It runs as a workflow dispatch with inputs**, so it needs no local environment and uses the secrets already in place, and its calls are counted into the month's total like any others.

**Both write the reason, and the projection reads the store by reason.** Under ADR-0043's principle, a row returns only if the reason it left was the rules. `unreviewed-aged-out` and `operator-removed` do not return; a row dropped by a narrowed rule still does.

**A tool the operator invokes is him acting, not the pipeline acting.** It writes `Delete`, which is his field. ADR-0035's field-ownership rule constrains the writer and the projection, and that scope has to be explicit or its fitness function reads this tool as a violation.

### Consequences

The display becomes bounded for the first time. Its steady size is the rate at which rows are admitted multiplied by how long they stay, so with the clock in place it is at most thirty days of intake rather than unbounded.

**Clearing the table is a budget action as much as a tidiness one.** At ten rows a call and two runs a day, every ten rows removed saves about sixty calls a month. Holding the display near forty rows costs about 240 calls a month where a hundred rows costs about 600.

**Purging resets the level and does not lower it.** The display refills at the intake rate, so a weekly purge is a recurring obligation rather than a fix. That matters for ADR-0056's triggers, which must not measure his housekeeping instead of the system.

A row he never read can now leave the display. It is not lost: it stays in the filtered layer, its removal is stored with a reason, and the run log names it. But the chance to apply to it is gone, and thirty days is the number that decides how often that happens. It is configuration for exactly that reason.

The `Delete` field now has two writers, him in the browser and his own tool, and no pipeline writer at all.

### Confirmation

**A dry run must change nothing**, proved by record counts before and after and by the absence of any store write. *(Clarified 2026-10-03: the dry run writes one private list of the aggregator rows it would remove, so that the confirm can be bound to exactly those rows. That list is not a store and lives outside `outcomes/`, so the guarantee holds by where the file sits and not only by a test.)*

**The confirmation must be required.** An invocation without it must refuse, and the mutation that removes the requirement must fail a test.

**A removed row must not come back.** Run the tool, then run a projection, and the row must not reappear. This is the check that the whole record exists for, because the behaviour it corrects is the one a reader would assume works.

**A rule-dropped row must still come back** when the rule widens, in the same suite, so the reason-based skip is proved in both directions.

**`accepted` must be seen surviving the tool.** Point it at `accepted` with a threshold that matches every row and confirm nothing is deleted and only `Delete` is set, and that the rows then leave by D12's path with their store writes verified.

**The clock must be seen firing and not firing.** A row 29 days unreviewed stays; at 31 days it is stored with `unreviewed-aged-out` and then removed on a later run.

**Every removal must be named in the run log**, by identity, so that an absence of weeks can be reconstructed from the logs alone.

## Pros and Cons of the Options

### A clock only

Good, because it needs no interface and cannot be misused.
Bad, because it gives him no way to act on a judgement of his own, and his fresh-start case is exactly such a judgement.

### A tool only

Good, because nothing happens that he did not ask for.
Bad, because the display is then unbounded whenever he is away, which is the condition the system was built to tolerate.

### Clearing rows in the Airtable browser

Good, because it needs nothing built.
Bad, because it does not work: the next projection puts the rows back, and the effort is invisible within a day. It is recorded as an option precisely because it is the one a reader would try.

## More Information

ADR-0050 owns the sweep this joins, its write-verify-delete order and the two-run separation. ADR-0043 owns the store and the reason-based skip principle. ADR-0040 is why a deleted row returns at all. ADR-0035 owns field ownership, scoped here. ADR-0052 is why a publication-date threshold on `Jobs` is a trap, since it judges age once at first sight and a legitimate row's publication date then recedes. ADR-0031 owns the thirty days and every threshold as configuration. ADR-0056 owns the projection cost these mechanisms relieve.

The operator's decisions, 2026-09-28: the tool and its per-table thresholds, the date field for each table on the chat's recommendation, and both mechanisms rather than one. His reason for both, in his words: "one is just to maintain while the other is manual meaning i can run whenever i want so keeping both should be reasonable."

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | Built and audited. The operator's three decisions recorded: a confirm must follow a dry run of the same table, days and mode within 48 hours (2026-09-30); a refused or failed clear exits 2 and shows green with a warning, and a partial clear reports how many rows it stored (2026-10-02); and clearing a classified `Jobs` row takes its rejection copy with it, only after the outcome and its reason are in the classification store (2026-10-03) | The last is the one with an edge: ADR-0050 writes a classified row's outcome to its store fifteen days after classification, by reading the `Jobs` row, so clearing that row earlier would skip the write and lose his verdict unless the tool writes it first. The chat recommended it on that condition and he accepted; the implementing seat confirms the code does it |
| 2026-10-03 | Four clarifications of how it is built: the confirm acts only on rows its dry run listed (the audit's F1); the dry run's private list sits outside `outcomes/`; an aggregator's identity is masked in the public run log and named in the private store; and the latency to the next run is corrected from about fourteen hours | F1 found the confirm selecting afresh, so it could remove rows the dry run never showed. The masking satisfies "named by identity" here and ADR-0047's "never public" together, as an implementation of both and not a conflict. The list's location is the chat's ruling: a file in `outcomes/` will one day be read as a store |
| 2026-10-03 | The dry run says how many of the rows it lists will leave without it: a row this run's sweep has just stored for removal, one kept out by an earlier removal, a classified row whose outcome is stored, and on `accepted` a copy whose `Delete` is set. What the tool removes is unchanged. The dry run's private list sits at `clearing/dry_runs.json` in the private repository, and a test now holds that clearing a classified `Jobs` row stores its outcome first | His dry run of 2026-10-02 listed 19 rows and his confirm removed 2, because the same run's sweep had already stored the other 17 for removal, and nothing he read said so. He asked for the count once it was explained. Storing the outcome first was built from the start; no test held it until Brief 9 |
