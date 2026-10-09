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
- A posting absent from its board on four consecutive runs that polled that board has closed. **Chosen by the chat** from the two-a-day cadence, so four runs is about two days, and not measured. It needs the operator's approval before the sweep is built, and the number is configuration under ADR-0031 rather than a constant. *(Annotated 2026-09-28: **approved** by the operator on 2026-09-25 as a starting value, and it lives in `config/sweep.json`. The counting rule was then refined by the implementing seat and approved: see the closure test below. The number has still never been measured against a board that hid a posting and restored it.)* *(Annotated 2026-10-03: **measured, and raised to twelve.** Twelve Greenhouse postings left their boards and returned after 23 to 130 hours, median 59, measured by the implementing seat over the run logs; four runs is about 48 hours, so more than half of them would have been marked closed while open, and the operator's `To review` view hides a closed row. The operator set twelve, about six days, on 2026-10-03: a closed role shown for four more days costs a click, a live one hidden costs the freshness the system exists for. See Changes.)* *(Annotated 2026-10-04: what four runs actually cost while in force was **none**. The implementing seat read every sweep block from 2026-09-25 to 10-03: the 3 marks of 09-25 were true closures, and the 47 of 10-01 and 10-02 came from the Himalayas walk-reach defect, not the threshold. Twelve is prevention, not repair.)*
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

**The copy step runs with every fetch, twice a day. Every other step runs once a day.** A classification then appears in its table within twelve hours rather than twenty-four, which is what the operator asked for, and the step is idempotent: it creates a copy only for a row that has none. *(Corrected 2026-09-28: **about fourteen hours, not twelve.** The chat took the smaller of the two nominal gaps between a 00:00Z and a 13:00Z schedule. Measured run starts are 03:27Z to 04:00Z and 16:56Z to 17:47Z, so the longest wait after a status is set is about fourteen hours and the shortest about ten. A manual dispatch copies within minutes of its test step, at a measured 13 to 15 calls. The cadence is unchanged; only the figure was wrong.)* *(Corrected again 2026-10-03, the fourth audit's F10: the start times above were themselves stale. Over 2026-09-29 to 2026-10-01 scheduled runs began between 03:26Z and 04:33Z and between 16:18Z and 20:02Z, and the longest gap between two was 16.0 hours, read from GitHub's Actions API by the audit. The honest statement is "by the next run", whose start GitHub moves by hours.)*

1. **Copy.** Every row in `Jobs` with a status and no copy in the matching table is created there. A row whose status changed since its copy was made has the old copy deleted and a new one created, which resets that table's `Classified` and discards the old copy's reason, because that reason belonged to the old classification. *(Amended 2026-09-28 for the operator's D12 of 2026-09-26, which the third audit's F1 produced. A copy is never deleted unsaved. **A cleared `Status` removes nothing, from any table.** **An `accepted` copy is never deleted by the pipeline**: it stays whatever its row's status becomes, and the run log says so. **A rejection copy superseded by a status change is written to `removed_copies.json` first, its reason included, verified, and deleted on a later run.** Line 71 as originally written deleted that copy unsaved, which the audit found and which the operator's own understanding had never allowed.)*
2. **Store, verify, delete from `Jobs`.** For each row whose `Classified at` is more than fifteen days old: write it to its ADR-0043 store, with its reason, or for an accepted row its `Stage`, read from the matching copy in the same run; read the store back and confirm its `Identity` is present; then delete it from `Jobs`. A row that fails verification stays and is reported, and no row is deleted on the strength of another row's success. *(Amended 2026-09-28: **the write and the delete fall in different runs.** A store is durable only once the workflow has pushed it, which happens after the run, so a verify inside the writing run would be reading back the file that run just wrote, which is a check that cannot fail. The sweep therefore writes and leaves the row, and a later daily sweep deletes it only once the store restored from origin holds the identity. Every deletion lands about a day after its store write. The implementing seat took this decision inside Brief 7 and the operator approved it on 2026-09-25.)*
3. **Delete from the rejection tables.** A row in `rejected-not-a-fit` or `rejected-poor-filtering` whose `Classified` is more than fifteen days old is deleted; its outcome reached the store in step 2. **`accepted` is deleted by no clock**, because it is the record of what he applied to; a tool he runs clears it from Airtable alone, never from the store. *(Amended 2026-09-28 for D12: the tool is his `Delete` field. `Delete` is a single select on `accepted` and `accepted test` whose one choice is yes, empty meaning keep; the pipeline reads it and never writes it. The next daily sweep saves the copy, `Stage` as it then stands, to `removed_copies.json`, and to the accepted store if its row is still in `Jobs`; a later sweep removes the copy once both records are read back from origin, with its `Jobs` row if there is one.)*
4. **Mark what has closed.** A row in `Jobs` with an empty `Status` whose posting has closed gets `Closed` set to the date the pipeline first saw it closed. It stays in the display, marked, so he can see it closed rather than finding it gone. **`Closed` is cleared if the posting returns before it is retired, and clearing it resets the absence count**, since a retained count would re-close the row on its next absent run.
5. **Retire what closed, fifteen days on.** A row whose `Closed` is more than fifteen days old is written to `outcomes/removed_unreviewed.json` with the reason `closed`, verified, then deleted from `Jobs`. This is the event ADR-0014 called `expired_before_review`, now recorded rather than inferred.
6. **Remove what a rule dropped, at once.** A row with an empty `Status` that the current chain no longer admits, for any reason other than closure, is written to the same store with the rule that dropped it and deleted at the next sweep, with no clock: the rules say it does not belong in the display, and ADR-0040 requires the display to converge on the current rules. **Two cases sit inside this step.** A row that stopped being its group's display row, because an earlier member became the representative, is removed with that reason and the group still shows under its new representative. And **a row the stored layers do not hold is left in place and counted, never removed**, because nothing can re-judge a row there is no stored posting for; the fifteen Himalayas rows projected on 2026-09-24, before the private store existed, are the only instance, and the operator classified all fifteen by hand on 2026-09-26.

**A posting has closed when either holds.** Its own expiry date has passed, which is the expiry rule the chain already applies. Or it was absent from its board on **four consecutive runs that polled that board** *(twelve since 2026-10-03; the number is configuration, see the Assumptions)*. **A run that did not poll the board never counts**, which matters because ADR-0048 skips Himalayas on the evening run, and counting those would close every aggregator row in two days. *(Annotated 2026-10-05 (2026-10-04 UTC): stale since 2026-10-03, when ADR-0048 put Himalayas back on both runs. The rule stands for any source a run skips.)*

**Absence is counted posting by posting, not board by board.** *(Amended 2026-09-28. The implementing seat found the rule above too coarse and the operator approved the refinement on 2026-09-25.)* A paginated board is read newest first and stops when it meets what is already stored, so a run can poll the board without ever reaching the posting in question. **A run counts for a posting only if that run's read reached back to the posting's publication date**, which every board now logs as `oldest_published`; runs logged before 2026-09-26 carry no such field and never count. *(Extended 2026-10-09: a run whose walk reached the feed's end counts for every posting, including one with no date. See Changes.)* A board that answered with nothing does not count either. **A group closes when its last member does.**

**So each class of source has exactly one closure mechanism, and neither is redundant.** The eleven ATS boards are read in full on every run, so absence is the mechanism there, and expiry is not: `expires_at` is empty on all 346 stored public rows, measured 2026-09-28, and Greenhouse's `application_deadline` was null on the posting sampled live that day. Himalayas is read only back to its mark, so absence can never be counted for it, and expiry is the mechanism: its feed carries `expiryDate` on every posting, per the adapter's coverage note.

**Write, verify, then delete. Never the reverse.** Inherited from ADR-0014 through ADR-0045 and ADR-0046.

### What keeps a classified row out of the display

**A stored outcome keeps a row out for good.** The projection skips a display group when **any member's** identity is present in one of ADR-0043's three classification stores.

**`outcomes/removed_unreviewed.json` is not read by the skip.** A row removed because a rule narrowed must be able to return if the rule widens again, per ADR-0040, and a closed row will not return because the closure test still holds. *(Corrected 2026-09-28. The second half of that sentence was wrong and the implementing seat found it. A closed row does return, at once: the filtered layer keeps every row it ever admitted, so ADR-0040's re-projection re-sends it, and the four-run absence count then has to start again. The skip is therefore read by reason, under one principle: **a row returns only if the reason it left was the rules, because only the rules can change their mind.** The projection skips a row stored with reason `closed`, and it does not skip a row stored with a rule's name.)*

**A projected row carries its group representative's identity**, as `src/dedupe.py` chooses it.

### The cost, and the guard

**Measured 2026-09-24**: the projection spent 5 calls for 44 groups, and two test runs 6 each at 54 and 56 groups. **Reproduced by the chat 2026-09-25** from `filtered.json` at `data` head `def4f935`: 39 groups over 345 rows, 334 admitted, 29 groups, 3 calls for the public rows alone.

*(Corrected 2026-09-28. The table that stood here was arithmetic over one early projection and it left out the copy step's own reads, which the implementing seat identified on 2026-09-25: an idempotent copy on every fetch must read `Jobs`, at one call per 100 records however few rows it holds, and must read the classification tables when anything moved. The seat reads the tables on a copy-only run only if `Classified at` has moved since the previous run, which catches a cleared status too. Every figure below is measured, with its date, and replaces the projection.)*

| What | Measured | When |
|---|---|---|
| Projection upsert, 44 display groups | 5 calls | 2026-09-24 morning |
| Projection upsert, 52 groups | 6 calls | 2026-09-25 morning |
| Projection upsert, 70 groups | 7 calls | 2026-09-25 dispatch |
| Projection upsert, 86 groups | 9 calls | 2026-09-26 morning |
| Sweep, a morning running every step | 6 to 8 calls | 2026-09-25 and 2026-09-26 |
| Sweep, a quiet evening, copy step only | 2 calls | 2026-09-27 evening |
| A manual dispatch, every step and every board | 13 to 15 calls | 2026-09-26 |
| The month to date at 126 rows in `Jobs` | 100 calls, 10% | 2026-09-27 |

**What the table shows is a law, not a total.** The projection re-sends every display group on every run at ten groups a call, so **the cost is linear in the display: about one call per ten groups per run, and about 60 calls a month for every ten groups the display holds.** Fifty groups is about 300 calls a month, a hundred about 600, and at about 150 the projection alone would consume the allowance. The figure therefore moves with anything that adds display rows, a new source included, and not with the size of the store behind it.

**The run log reports the month to date from both branches' logs, and says so loudly once the month's total passes 60% before the fifteenth.** That is the guard the operator asked for on 2026-09-25: the trajectory is raised, not the breach, because the grace period is available once ever.

### Consequences

A classification lands in its table within about fourteen hours, and a closed role is visible as closed for fifteen days before it goes. *(Corrected 2026-10-03: by the next run, which has been as much as 16.0 hours away; see the sweep section.)*

`Jobs` now empties. Every row leaves by one of four routes: classified and retired at fifteen days, closed and retired at fifteen days, dropped by a rule and removed at once, or, for an `accepted` copy, on the operator's `Delete`. Nothing else removes a row, and nothing removes one silently. *(Corrected 2026-10-03, the fourth audit's F10: untrue since ADR-0055, written an hour after this, which adds two routes, the thirty-day clock for an unreviewed row and the operator's clearing tool. Both store first and name every row in the run log, so the second half of the sentence still holds.)*

The pipeline writes one more field, `Closed`, which is one more field an upsert could overwrite wrongly. It is pipeline-owned, so the cost of a mistake is a wrong date rather than lost review data.

The budget rises from about 450 to about 600 a month, because the copy step doubles and marking costs calls. At about 100 aggregator groups the allowance binds, and the guard above is what gives warning.

A closed row sits in the display for fifteen days, so the display holds roles he cannot apply to. That is the trade he chose: seeing that a role closed is worth more than a shorter list.

The four-run closure test will close a role that a board hides temporarily and then restores. The row returns on the next projection if the chain still admits it, because the removal store is not read by the skip. *(Corrected 2026-09-28: a row stored with reason `closed` is now skipped, so it does not return on the next projection. A board that hides a posting and restores it is instead handled at step 4, where a returning posting clears `Closed` and resets its absence count before retirement.)*

Every deletion in this flow lands about a day after the store write that permits it, which is the cost of verifying against the remote rather than against the file the run just wrote.

### Confirmation

**The verify step must be seen refusing.** Point the sweep at a store missing an identity it has just claimed to write, and confirm it does not delete and reports the row.

**The skip must be seen both ways, and at the member level.** An identity in a classification store is not projected; removed from the store, it is. Then put a non-representative member of a group in a store and confirm the whole group is skipped.

**The skip must be seen reading by reason.** A row stored with reason `closed` is not projected; a row stored with a rule's name is, once the rule widens again. A test that passes for both reasons is asserting something other than the principle.

**The closure test must not fire on a skipped board.** Run four evening runs with Himalayas skipped and confirm no Himalayas row gains a `Closed` date. This is the check that can fail, and it is the one that matters, because the aggregator rows are the ones the test would wrongly close.

**The closure test must not fire on a board that was polled but not read back far enough.** Four runs that each stopped at their mark, none of them reaching the posting's publication date, must leave `Closed` empty.

**`Closed` must be seen appearing and then retiring.** Set a posting absent on four consecutive polling runs, confirm `Closed` is stamped and the row stays, then advance fifteen days and confirm it reaches the store with reason `closed` and leaves `Jobs`.

**A cleared `Status` must be seen removing nothing**, and an `accepted` copy must be seen surviving a status change and a clear.

**A superseded rejection copy must be seen saved before it goes**, with its reason, and the delete must be seen refusing when the save cannot be read back.

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

ADR-0040 owns the projection that re-applies the current rules and the convergence this record's steps 5 and 6 deliver. ADR-0043 owns the stores, including `removed_unreviewed.json` and `removed_copies.json`. ADR-0035 owns field ownership, which `Closed` is classified under. ADR-0048 owns the poll cadence that makes a skipped board possible, which step 4's counting rule exists for. ADR-0049 requires the checks above to be fitness functions where they guard a rule rather than a feature. ADR-0004 owns the allowance and its grace period.

The operator's decisions this record carries: the status names, 2026-09-24; the reason and `Stage` reaching the store, 2026-09-22; the group-wide skip, 2026-09-23; D3, closed postings visible for fifteen days then retired, 2026-09-24; the copy on every fetch, 2026-09-25; the call-trajectory guard, 2026-09-25; the six sweep behaviours of 2026-09-25; and D12, 2026-09-26.

**On this record's own amendment count.** Brief 7 told the implementing seat that a Changes row here in the record's first week would mean the consolidation was premature, and the seat wrote none, leaving the judgement to the architecture chat. The chat's ruling, 2026-09-28: the consolidation stands. The eight-row trigger exists to catch a decision that keeps being reopened, not a record meeting reality for the first time. Two of the four rows below are the chat's own wrong figures, which say nothing about the decision; one is a set of refinements the operator approved in a single exchange, which Brief 7 itself asked the seat to take and hand back; one is a genuine amendment, D12. The chat has set its own guard below the standard's: **at six rows this record is re-read as a supersession candidate**, because a record rewritten at the trigger is a record rewritten under pressure. *(Met 2026-10-03, and done. Of the six rows only D12 changed a decision; three correct the chat's own figures and sentences, one records a batch of approvals, and one changes a configured number. A record that keeps being corrected is not a decision that keeps being reopened, and the guard exists to catch the second. The record stands.)* *(Re-read again 2026-10-09, at its seventh row, which changes a rule: a posting with no date can now close by its absence. It extends step 4's counting to a case the record did not foresee, Manatal's dateless postings, and leaves closure by absence, the twelve runs and the rest of the flow as decided. The record stands.)*

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-25 | The sweep's six behaviours settled: the store write and the delete fall in different runs; absence is counted posting by posting; a group closes when its last member does; step 6 also removes a stale duplicate and leaves a row the stored layers cannot judge; `Closed` is cleared when a posting returns; a sweep failure exits 2 and counts toward the three-in-a-row escalation | The implementing seat took all six inside Brief 7, which asked it to decide and hand back, and the operator approved all six the same day in his own words. One approval on one date, so one row: six rows for one exchange would spend three quarters of this record's life on a single conversation. Built before the record caught up, and none of the six changes the flow's shape |
| 2026-09-26 | D12: step 1 and step 3. A cleared `Status` removes nothing; an `accepted` copy is never deleted by the pipeline and leaves only on the operator's new `Delete` field; a superseded rejection copy is saved to `removed_copies.json` before it goes | The third audit's F1. Line 71 as written deleted a superseded copy unsaved, and neither line 71 nor line 73 foresaw a cleared status or `accepted`, whose reason is `Stage`. The operator designed the fix himself rather than taking the one offered, and it makes true what he had always understood to be true |
| 2026-09-28 | "Within twelve hours" corrected to about fourteen, in the sweep section and in Consequences | The chat's error: it took the smaller of the two nominal gaps between a 00:00Z and a 13:00Z schedule instead of the larger, and the measured starts are later still. Found by the implementing seat. The cadence was always right; only the figure was wrong |
| 2026-09-28 | The cost table replaced by measured per-run figures, and the copy step's reads added. The linear law stated: about one call per ten display groups per run | The chat's error: the original table was arithmetic over one early projection and omitted the reads an idempotent copy step must make. Found by the implementing seat on 2026-09-25 and measured by it over eight runs |
| 2026-10-03 | The audit's F10, two of the chat's sentences: the copy's latency, stated as about fourteen hours on start times that were stale, is now "by the next run", measured at up to 16.0 hours; and "Nothing else removes a row" is annotated untrue since ADR-0055 added the clock and the clearing tool | Both are the chat's. The first correction of 2026-09-28 replaced one stale figure with another, because it took the start times from a report rather than from the runs. The second sentence went stale an hour after it was written, when the chat wrote ADR-0055 and did not come back to this one. The flow is unchanged |
| 2026-10-03 | The closure test's run count goes from four to twelve | The first measurement of the number, which this record had marked as chosen and unmeasured: twelve Greenhouse postings were absent 23 to 130 hours and came back, so four runs would have closed more than half of them while open. Since 2026-09-30 a closed row is hidden from the operator's review view, so a false closure now hides a live job rather than only mislabelling it. The operator's decision, 2026-10-03. Himalayas is unaffected, because in practice it closes by its own expiry date (ADR-0053) |
| 2026-10-09 | A posting with no date can close by its absence: a run whose walk reached the feed's end counts toward closure for it, since the closure test now asks whether the walk reached the end before it asks for the posting's date | Manatal's postings carry no date. The test asked for a posting's date first, to judge whether a paginated walk had reached back to it, so a posting with no date could never close by absence. Found and fixed by the implementing seat when integrating Manatal on 2026-10-07 UTC; some of its boards repeat postings across pages, so the walk reads to the end and keeps a repeated posting once |
