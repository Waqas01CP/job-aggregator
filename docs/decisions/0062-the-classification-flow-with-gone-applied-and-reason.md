---
status: accepted
topic: display
description: The whole classification flow in one record, consolidating ADR-0050 at its eighth amendment. One status in Jobs, now with gone and applied; a Reason set beside it; the copy on every fetch; fifteen days on two clocks; closed postings marked and retired; what keeps a row out of the display; and the pipeline's own monthly ceiling of 900 calls.
date: 2026-10-16
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0062: The classification flow, with gone, applied and a reason in `Jobs`

## Context and Problem Statement

ADR-0050 consolidated this flow on 2026-09-25 and holds seven Changes rows against its own guard of six. On 2026-10-16 UTC the operator decided three changes to it, from three days of using the tables for real (13 to 15 Oct), reported by the resume-tailoring chat:

- **Postings dead when he came to apply.** About 10 of roughly 40 he tried were gone, five tailored CVs were built for dead ones, and no rule reads the sign he sees, a link that redirects to a job list. Himalayas' job pages answer 403 to the pipeline's client (the implementing seat, 2026-10-15), so it cannot see the redirect itself.
- **Applying takes two steps a day apart.** A set `Status` hides a row from his `To review` view, so he sets it only after applying; the `accepted` copy then arrives at the next sweep and `Stage` needs a second write. Nine rows were waiting for `Stage` when the resume chat counted.
- **A reason waits a sweep.** `Choice reason` and `Pipeline reason` live only on the rejected tables' copies, so a reason can be given only after a sweep has made the copy; 74 reasons took two passes on two days.

A row on ADR-0050 for any of them would be its eighth, the Decision Record Standard's supersession trigger. This record consolidates ADR-0050 and adds them, from the implementing seat's design of 2026-10-16. It also carries the operator's decision of the same day on the pipeline's own monthly ceiling, since this record owns the guard on the allowance.

The tensions: the operator owns `Status`, `Stage` and the reasons (ADR-0035), and two of the changes have the pipeline write two of them on his instruction; and every call these changes cost comes out of an allowance that the chats' connector calls also spend and the pipeline cannot see.

## Decision Drivers

- Classification stays one action he performs by hand, and a row he has classified never reappears in `Jobs`.
- A field he owns is never written from the pipeline's own judgement.
- The store is the durable record; Airtable is a projection.
- The free plan allows 1,000 API calls a month per workspace, every client spends them, and exceeding them starts a grace period available once ever.
- A closed role leaves the display, and he can see that it closed before it goes.

## Assumptions

- Fifteen days is long enough to change a classification and to see a cluster by eye. **Stated** by the operator. Carried from ADR-0046 through ADR-0050.
- A posting absent from its board on twelve consecutive runs that polled and reached it has closed. **Measured** by the implementing seat over the run logs on 2026-10-03: twelve Greenhouse postings left their boards and returned after 23 to 130 hours, median 59; the operator set twelve. Configuration under ADR-0031.
- Airtable's delete endpoint accepts ten records a call. **Sourced** from Airtable's documentation. Carried from ADR-0046 through ADR-0050.
- The free plan's limits: 1,000 records a base, 1,000 API calls a workspace each calendar month, a once-only 30-day grace period after which every request returns 429 until the month resets, and requests by integrations connected through his account spend the same quota. **Sourced** from Airtable's help centre, "Managing API call limits in Airtable", read 2026-09-25 and again by the implementing seat on 2026-10-16. Whether the chats' connector counts is inferred from that sentence, not shown.
- The chats' connector calls fit in 100 a month. **Not established, and false for October:** the operator read 617 calls at about 2026-10-16T19:02Z, when the pipeline's own count was about 445 to 455 (the chat's arithmetic: 442 by the run logs to that morning, plus the evening run), so about 160 to 175 were not the pipeline's. He accepted the ceiling knowing this; see the guard below.
- A `Status` value the sweep does not know makes no copy and moves no clock. **Read** in `src/sweep.py` by the implementing seat on 2026-10-16: no copy is made, no clock touches the row, and nothing fails; a rejection copy the row already had is saved and then deleted as superseded, and an `accepted` copy stays, with a problem line in the log.
- Airtable's free plan offers a number field Airtable assigns (autonumber). **Not checked**: the implementing seat believes it does and has not read it; he sees it when he creates the field. *(Checked 2026-10-16: the seat created `No.` as an autonumber in `Jobs` and `Jobs test`.)*

## Considered Options

- Keep ADR-0050 and give it an eighth row.
- One new record per change, each extending ADR-0050.
- Consolidate ADR-0050 with the three changes and the ceiling.

## Decision Outcome

Chosen option: "consolidate ADR-0050 with the three changes and the ceiling".

**Everything below is in force. Where it repeats ADR-0050, that is deliberate, so this record can be read alone.**

### What the operator does

**He classifies by setting `Status` on the row in `Jobs`.** Five values: `rejected-not-a-fit`, `rejected-poor-filtering` and `accepted`, named after the tables they feed; `applied`, for a posting he has applied to; and `gone`, for a posting he finds dead, its link redirecting to a job list or failing. Empty means not yet reviewed, and the `To review` view shows exactly those rows.

**He may set `Reason` beside it**, a single select in `Jobs` whose choices are those of `Choice reason` and `Pipeline reason` together, so a reason no longer waits for a copy.

**On a row already in `accepted`, he marks a dead posting by setting its `Stage` to `gone`**, since its row may have left `Jobs`. `Stage` holds shortlisted, applied and gone.

**The pipeline never writes `Status`, without exception.** It is the one field whose loss cannot be reconstructed, and the client has no way to send it.

### Whose fields the pipeline writes, and when

**`Stage`, `Choice reason` and `Pipeline reason` stay his** (ADR-0035). **The pipeline writes them only as a transcription of a value he set in `Jobs`**, `Status` `applied` or `Reason`, and only on the copy of that same posting. It never writes them from its own judgement, never lowers or clears a `Stage`, never writes `gone` into one, and never overwrites a reason he set on a copy.

### The clocks and the fields

**`Jobs` carries `Classified at`**, a `lastModifiedTime` field watching `Status` alone, so a projection write never restarts the clock. **Each classification table carries `Classified`**, a `createdTime` field set when the sweep makes the copy. **`Jobs` carries `Closed`**, a pipeline-owned date, empty until the pipeline decides a posting has closed. **No clock is ever the posting's own dates.**

**`Jobs` carries `No.`**, a number Airtable assigns and no client writes, and **`accepted` carries `Jobs No.`**, written by the sweep from the row's `No.` when it makes the copy, so one number follows the posting. Classified in ADR-0035's Changes.

### The sweep

**The copy step runs with every fetch, twice a day; every other step runs once a day, in the morning.** A classification reaches its table by the next run.

1. **Copy.** Every row in `Jobs` whose status feeds a table (`rejected-not-a-fit`, `rejected-poor-filtering`, `accepted`, or `applied`, which feeds `accepted`) and has no copy there gets one; an `accepted` copy carries `Jobs No.`. A `gone` row gets no copy; step 7 handles it.
   - **`applied`** is treated as `accepted`: the copy is made with `Stage` applied in the same create. If an `accepted` copy exists, its `Stage` is raised to applied, never lowered.
   - **`Reason`** is written into the new copy's reason field when it is one of that field's choices, listed in `config/sweep.json` to mirror his Airtable (ADR-0031), so one value outside them cannot fail a batch; a value outside them is kept in the store record and named in the run log. An empty reason on an existing copy is filled from `Reason`.
   - A row whose status changed since its copy was made gets a new copy, and the old one is handled as D12 set it: **a cleared `Status` removes nothing; an `accepted` copy is never deleted by the pipeline; a superseded rejection copy is written to `removed_copies.json` first, its reason included, verified, and deleted on a later run.**
2. **Store, verify, delete from `Jobs`.** For each row whose `Classified at` is more than fifteen days old: write it to its ADR-0043 store with its reason, or for an accepted row its `Stage`, read from the matching copy, and `Reason` beside it; a row marked `applied` is stored as accepted, with `applied` in the record. **The write and the delete fall in different runs:** the row is deleted only once the store restored from origin holds its identity. A row that fails verification stays and is reported, and no row is deleted on the strength of another row's success.
3. **Delete from the rejection tables.** A rejection copy whose `Classified` is more than fifteen days old is deleted; its outcome reached the store in step 2. **`accepted` is deleted by no clock.** It leaves Airtable only on his `Delete` mark (D12), a single select on `accepted` and `accepted test` whose one choice is yes, empty meaning keep, which the pipeline reads and never writes: the next sweep saves the copy to `removed_copies.json`, and to the accepted store if its row is still in `Jobs`, and a later sweep removes it once both records are read back from origin, with its `Jobs` row if there is one.
4. **Mark what has closed.** A row with an empty `Status` whose posting has closed gets `Closed` set to the date the pipeline first saw it closed, and stays in the display, marked. **`Closed` is cleared if the posting returns before it is retired, and the absence count resets with it.**
5. **Retire what closed, fifteen days on**, to `outcomes/removed_unreviewed.json` with the reason `closed`, verified, then deleted from `Jobs`.
6. **Remove what a rule dropped, at once.** A row with an empty `Status` that the current chain no longer admits, for any reason but closure, is stored with the rule that dropped it and deleted at the next sweep (ADR-0040). A row that stopped being its group's display row is removed with that reason. **A row the stored layers do not hold is left in place and counted, never removed.**
7. **Record what he found gone.** At the morning sweep, a posting marked `gone`, by `Status` in `Jobs` or by `Stage` in `accepted`, is written to `gone.json` (ADR-0043), public or private by source, with `Classified at`, `Reason` and whether it was accepted. At the morning sweep after origin holds it, its `Jobs` row is deleted, without the fifteen days. An `accepted` copy stays; `Delete` remains its only removal. A rejection copy is superseded as in step 1.

**Write, verify, then delete. Never the reverse.**

### When a posting has closed

**Either its own expiry date has passed, or it was absent from its board on twelve consecutive runs that polled the board and reached it.** A run that did not poll the board never counts. **Absence is counted posting by posting:** a run counts for a posting only if its read reached back to the posting's publication date, or reached the feed's end, which is how a posting with no date can close. A board that answered with nothing does not count. **A group closes when its last member does.** In practice the employer boards close by absence and Himalayas by its expiry date: even the morning walk that reads to the age limit (ADR-0053) covers a posting on mornings only and only in its first week, fewer than the twelve covering runs closure needs.

**A sweep failure exits 2 and counts toward the three-in-a-row escalation**, as a projection failure does (ADR-0034's Changes).

### What keeps a row out of the display

**A stored outcome keeps a row out for good.** The projection skips a display group when any member's identity is in one of ADR-0043's three classification stores, or in `gone.json`. **A projected row carries its group representative's identity.**

**A row returns only if the reason it left was the rules, because only the rules can change their mind.** The skip reads `outcomes/removed_unreviewed.json` by reason: a row stored as `closed`, aged out or removed by him stays out, and a row stored with a rule's name returns when the rule admits it again.

### The cost, and the guard

**Measured by the implementing seat from the run logs, October to 2026-10-16T03:25Z: 442 calls, 399 production and 43 test.** A production day, 2026-10-09 to 10-15: the read-back of `Jobs` 4, the projection's writes 0 to 2, the morning sweep 5 to 14, the evening copy step 2, `Health` 0 or 2; mean 19.1, median 17, maximum 28. The sweep is now the largest share.

The three changes add nothing recurring: no new read, since `Jobs` and `accepted` are read every morning already; one delete call per ten gone rows; one update per ten `Stage` raises or reasons filled. `Jobs No.` rides the copy's create.

**The pipeline refuses any Airtable call that would take its own month's count to 900.** Airtable's limit is the workspace's 1,000, which the chats' connector calls also spend and the pipeline cannot see, so the hundred between is theirs. The figure is configuration (ADR-0031). When the pipeline reaches it, the fetch still runs and every posting is still stored; the projection and the sweep fail, each run exits 2 and the third such run in a row is marked failed, and the display stops updating until the month resets, when the next run sends everything it holds. **What he watches is the workspace's Usage count.** His condition for revisiting the figure: "if jobs are missed then will think about it"; the chat adds a count nearing 1,000 as the earlier sign, since reaching the ceiling delays postings rather than missing them.

**The run log reports the month to date from both branches' logs, and says so loudly once the month's total passes 60% before the fifteenth.** The trajectory is raised, not the breach, because the grace period is available once ever.

### The order of introduction

This record reaches origin together with its registry entries (ADR-0049), its new clauses marked unbuilt until tests hold them. He then creates the fields (`Reason`, `No.`, `Jobs No.`, and ADR-0035's derived fields), since a read that names a field fails until it exists, and the implementing seat pushes the handling. **Only then does he add `gone` and `applied` to `Status` and `gone` to `Stage`**: until the handling is pushed, a row marked `applied` would get no copy.

### Consequences

He applies in one step: `applied` makes the `accepted` copy with its `Stage`, and the row leaves `To review` as any set `Status` does.

A reason lands with its classification, in the copy and in the store, without waiting a sweep.

For the first time the system counts postings dead before he applied, by source and by age at death, from `gone.json`. That count is what the deferred early-removal check (the chat's ledger, item 149) is judged against.

The pipeline now writes three fields he owns, though only as his own instruction carried to the copy of the same posting; a defect there would write his value onto the wrong posting, which is the failure the tests below exist for.

`Jobs` empties by six routes: classified and retired at fifteen days; closed and retired at fifteen days; dropped by a rule and removed at once; marked gone and removed the next day; aged out by ADR-0055's thirty-day clock; or cleared by his tool (ADR-0055). An `accepted` copy leaves only on his `Delete`. Each route stores first and names its rows in the run log.

The ceiling can stop the display updating before the month ends, which delays postings and loses none. With connector use at October's rate it would not protect the grace period, which is why his Usage count is what he watches.

A closed row still sits in the display for fifteen days, marked: the trade he chose, seeing that a role closed over a shorter list.

### Confirmation

**The verify step must be seen refusing.** Point the sweep at a store missing an identity it has just claimed to write, and confirm it does not delete and reports the row.

**The skip must be seen both ways, and at the member level.** An identity in a classification store is not projected; removed from the store, it is. Then put a non-representative member of a group in a store and confirm the whole group is skipped.

**The skip must be seen reading by reason.** A row stored with reason `closed` is not projected; a row stored with a rule's name is, once the rule widens again. A test that passes for both reasons is asserting something other than the principle.

**The closure test must not fire on a skipped board.** Runs that did not poll a board must leave its rows' `Closed` empty.

**The closure test must not fire on a board that was polled but not read back far enough.** Runs that each stopped at their mark, none reaching the posting's publication date, must leave `Closed` empty.

**`Closed` must be seen appearing and then retiring.** Twelve consecutive covering absences stamp `Closed` and the row stays; fifteen days on it reaches the store with reason `closed` and leaves `Jobs`.

**A cleared `Status` must be seen removing nothing**, and an `accepted` copy must be seen surviving a status change and a clear.

**A superseded rejection copy must be seen saved before it goes**, with its reason, and the delete must be seen refusing when the save cannot be read back.

**The clock must not move on a projection write.** Project twice and confirm no `Classified at` and no `Classified` changes.

**`accepted` must be seen surviving.** Run the sweep against an accepted row well past fifteen days and confirm it is still in Airtable and in the accepted store.

**The month's count must be seen crossing the line.** Feed the report a month of logs summing past 60% before the fifteenth and confirm it says so.

**`gone` must be seen keeping a posting out for good**, from `Jobs` and from `accepted`'s `Stage`, with its `Jobs` row deleted only once origin holds its record and its `accepted` copy kept.

**`applied` must be seen making the copy with its `Stage` in one sweep**, and raising an existing copy's `Stage` without ever lowering one.

**A `Reason` must be seen reaching the copy and the store**, a value outside the field's choices kept in the store and named in the log, and a reason he set on a copy never overwritten.

**A `Status` the sweep does not know must make no copy and move no clock.**

**`Jobs No.` must be seen following the posting into `accepted`.**

**The ceiling must be seen refusing at the configured figure**, with the fetch and its stores unaffected.

**Live only:** the count of postings he marks gone, by source and age at death, once he uses the value.

## Pros and Cons of the Options

### An eighth row on ADR-0050

Good, because nothing is rewritten.
Bad, because the eighth row is the supersession trigger, and a flow changed three ways in one row is the erosion the trigger exists to catch.

### One record per change

Good, because each change sits in a record of its own.
Bad, because each would extend ADR-0050 by a Changes row there, the binding act ADR-RULES requires, which fires the same trigger, and the flow would be read across four records.

### Consolidate

Good, because one record states the flow in full, today.
Bad, because ADR-0050's history moves to a superseded record and its Changes table.

## More Information

**Supersedes ADR-0050**, which carries the pointer back; ADR-0050 superseded ADR-0046, ADR-0046 superseded ADR-0045, and ADR-0045 superseded ADR-0014.

**Carried forward from ADR-0050 unchanged:** the one status set by hand and never by the pipeline; the copy on every fetch; the three clocks; steps 1 to 6 with D12 and its `Delete` field, and the six sweep behaviours of 2026-09-25, a sweep failure's exit 2 among them; the twelve-run closure test, counted posting by posting, with the run that reached the feed's end counting for a dateless posting; the skip by any member and by reason; the 60% trajectory guard; write, verify, then delete. ADR-0050's annotated corrections (the copy's latency, "by the next run"; the cost table; the routes ADR-0055 added) are folded into the text above as they stand. **Changed:** two `Status` values and a `Stage` value added; `Reason` in `Jobs`; the `No.` carried as `Jobs No.`; step 7 and `gone.json`; the ceiling of 900; the cost figures re-measured.

ADR-0035 owns field ownership and classifies the new fields. ADR-0043 owns the stores, `gone.json` among them. ADR-0040 owns the convergence steps 5 and 6 deliver. ADR-0055 owns the thirty-day clock and the clearing tool. ADR-0048 owns the cadence that makes a skipped board possible. ADR-0004 owns the allowance. ADR-0049 requires the checks above to be held by tests.

The operator's decisions this record carries: the status names, 2026-09-24; the reason and `Stage` reaching the store, 2026-09-22; the group-wide skip, 2026-09-23; D3, closed postings visible for fifteen days then retired, 2026-09-24; the copy on every fetch and the trajectory guard, 2026-09-25; the six sweep behaviours, 2026-09-25; D12, 2026-09-26; twelve runs, 2026-10-03; and on 2026-10-16 UTC: the gone status, "i do need the one more status i gave as this is reasonable"; the applied status and a reason in `Jobs`, "yes, do it now."; the row number in `Jobs`, "yes, the row number should be in jobs as well."; the names left to the implementing seat, "let the seat propose and it does not need to ask me for approval as long as those names are easy to understand like the ones you proposed."; and the ceiling: first "4. yes but 900 is very conservative and should be 950 or 975 something.", then, once told the ceiling counts only the pipeline's calls, "900 for now and subjective to the condition that if jobs are missed then will think about it unless i am misunderstanding the number.", confirmed with "yes." once told that reaching it delays the display and loses nothing, and that his Usage count is what to watch.

Designed by the implementing seat in its report on Brief 12 and Addendum 1, 2026-10-16, which chose the names `gone`, `applied`, `Reason`, `No.` and `Jobs No.`.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-17 | Built on 2026-10-16 by the commits' UTC times, and live from the run of 2026-10-17T03:15Z. The ceiling as `monthly_call_ceiling: 900` in `config/sweep.json`, which refuses a figure above 1,000, across the run's three Airtable clients (`ba4195f`); the flow (`44e7113`), its seventeen clauses that tests can hold each held by named tests, the eighteenth live only; the fields made by the seat on 2026-10-16, and the options added by the operator after the push. Two choices within the design: `applied` raises an existing copy's `Stage` from empty or shortlisted and never otherwise; and the store keeps the copy's reason and `Reason` side by side, neither winning, since they differ only when he edited one after the other. The first run under it, 2026-10-17T03:15Z, swept cleanly in 5 calls | The implementing seat's report on Brief 13, its run log on `data` read by the seat. The registry entries were pushed with this record (`fbc5ac2`, `6c94c72`) after 894 tests passed on Python 3.12 and 3.11 |
