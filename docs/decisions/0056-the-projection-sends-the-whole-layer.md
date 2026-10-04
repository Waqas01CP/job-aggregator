---
status: accepted
topic: display
description: The projection sends every display group on every run, which costs about one call per ten rows per run, and the delta design that replaces it. Decided and unbuilt, with the triggers that call for it and the measurement that authorises the build.
date: 2026-09-28
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0056: The projection sends the whole layer, and the delta design that will replace it

## Context and Problem Statement

The projection re-sends every display group on every run, ten groups to an Airtable call. That is what keeps the table from drifting: whatever happened to the base between runs, the next run states the whole truth again. It also means the cost of the display is the size of the display, twice a day, for ever.

Measured across four runs: 44 groups cost 5 calls, 52 cost 6, 70 cost 7, 86 cost 9. From those the implementing seat projected about 250 rows by early October, roughly 25 calls a projection and 50 a day, and the month's thousand-call allowance reached in the second half of October. Those figures were measured on 2026-09-26, before the operator's location rule and age rule, which removed most of the growth they extrapolated.

**What replaced that projection is worse in one respect and better in another.** It is no longer a runaway curve, but the steady state it settles at is not comfortably inside the allowance either. Roughly five to ten new display groups arrive a day, and under ADR-0055 a row stays at most thirty days, which puts the display somewhere between 150 and 300 rows. At about sixty calls a month for every ten rows, that is 900 to 1,800 calls against an allowance of 1,000. The operator also made the point that settles the shape of this record: he will add more boards, sites and platforms, so any number measured now is a floor.

## Decision Drivers

- Airtable's free plan allows 1,000 API calls a month per workspace, and the grace period for exceeding it is available once ever (ADR-0004).
- The whole-layer projection is a one-sentence invariant that anyone can hold in mind, and that is worth real money.
- ADR-0040 requires the display to converge on the current rules, and a projection that sends only changes is the obvious way to break that.
- A guard that measures the operator's housekeeping instead of the system is not a guard.
- Every new source raises the display's size permanently.

## Assumptions

- The cost is linear in display groups at one call per ten. **Measured** over four runs, 2026-09-24 to 2026-09-26, and arithmetic thereafter: two runs a day for thirty days is about sixty calls a month for every ten rows.
- Intake is five to ten new display groups a day. **Derived, not directly measured.** The morning of 2026-09-27 kept 31 of 361 new Himalayas postings, which is 8.6%, against an eligible volume of 45 to 92 a day, plus one or two from the eleven ATS boards. The eligible volume is itself two disputed figures, 2,965 results over a month against 19 dated postings on page one spanning 10.5 hours. This is the number the build is conditional on.
- The steady display size is the intake rate multiplied by how long a row stays. **Stated** as arithmetic. ADR-0055's clock is what makes the second term finite at all.
- Clearing the table by hand resets the level and does not lower it. **Stated**, and it follows from the line above.

## Considered Options

- Keep the whole-layer projection and accept that the display must stay under about 100 rows.
- Build the delta projection now, on the figures above.
- Keep the whole-layer projection, record the delta design with triggers, and build when a measurement confirms the rate.
- Raise the allowance by paying for Airtable.

## Decision Outcome

Chosen option: "keep the whole-layer projection, record the delta design with triggers, and build when a measurement confirms the rate".

**What is in force today is unchanged: the projection sends every display group on every run.** Nothing about the current behaviour is being amended, and `CLAUDE.md`'s statement that the next run re-projects the whole layer stands.

**The delta design, recorded now so that it is argued before it is needed.**

- **Send only the groups that are new or changed since the last projection that was confirmed.** Confirmed matters: a projection that failed part way through has sent an unknown amount, so anything not positively acknowledged is re-sent. The record of what was sent is per group, not per run.
- **Fall back to the whole layer whenever the rule set changes.** The rules carry a fingerprint; when it differs from the one the last projection ran under, that projection sends everything. This is the clause the design exists to protect, because ADR-0040 requires the display to converge on the current rules and a row whose fields changed under a new rule would otherwise never be re-sent.
- **Removal is not the projection's job and does not become it.** ADR-0050's sweep removes what the rules no longer admit, so the delta never has to reason about disappearance. The delta adds and updates; the sweep subtracts.

**Three triggers, any one of which calls for the build.**

1. A single projection spends more than 15 calls.
2. The month-to-date total passes 60% of the allowance before the fifteenth, which is ADR-0050's existing warning.
3. **The purge-proof one:** new groups admitted per day, multiplied by the retention window, exceeds about 100 rows. The first two triggers can be held off indefinitely by clearing the table under ADR-0055, which would mean the guard was measuring the operator's housekeeping rather than the system's growth. This one cannot be masked that way.

The run log already carries everything all three need.

**The build is pre-authorised on a measurement.** The operator's decision, 2026-09-28: the implementing seat reports one week of morning group counts and groups kept per day, and if that week confirms an intake consistent with a steady state above about 100 rows, it builds the delta projection without a further round trip. If the week comes in lower, the design waits on the triggers. His reason for taking it this way rather than building at once: "option 2 is more reasonable as we will have more data."

### Consequences

Nothing changes today, and the thing most likely to go wrong is that nothing changes for too long. The triggers exist because this record's own arithmetic says the answer is probably yes, and the week of measurement is what turns probably into a number.

When the delta is built, the invariant that anyone can state in one sentence is gone, replaced by one that needs three: send what changed, re-send what was not confirmed, send everything when the rules move. That is a real loss and it is the price of the allowance.

Four places will need amending on the day it is built, and they are named now so nobody has to find them: ADR-0034 and `CLAUDE.md`, which both say the next run re-projects the whole layer; ADR-0035, whose upsert is what makes a resend harmless and therefore what a delta relies on; and ADR-0040, which keeps its rule and gains the fingerprint fallback as the mechanism that satisfies it.

Until then, the failure mode is known and cheap: the client refuses at the ceiling, the warning fires first, and the display stops updating until the month turns. Nothing is lost, because Airtable is a projection and never authoritative.

ADR-0055's two mechanisms are the other lever on the same number, and they are the one the operator holds himself. Every ten rows cleared saves about sixty calls a month.

### Confirmation

**The week's measurement is the first check, and it is the one that decides the build.** Morning group counts and groups kept per day, reported from the run logs, with the implied steady state stated as a number rather than as a direction. *(Live only, marked 2026-10-04 under ADR-0049: counts over a clean week of production mornings, due 2026-10-05.)*

**When the delta is built, these must hold, each with a mutation that breaks it.**

- A run in which nothing changed sends no upsert call at all, and the table is still correct afterwards.
- A group whose fields changed is sent, and one whose fields did not is not.
- A projection interrupted part way is followed by a run that re-sends everything it did not confirm. The mutation: acknowledge on send rather than on response, and the test must fail.
- A change to any rule forces a whole-layer projection on the next run, proved by changing a rule and counting the groups sent.
- A row the current rules no longer admit still leaves the display, which is the sweep's job and must be shown not to have been quietly moved into the projection's.

**The trigger arithmetic must be checkable from the run log alone**, so that whoever reads the log can compute the implied steady state without access to this record.

## Pros and Cons of the Options

### Keep the whole-layer projection and hold the display under 100 rows

Good, because it changes no code and keeps the simplest invariant in the system.
Bad, because holding the display down means the operator clearing it by hand on a schedule, which makes a recurring manual obligation out of a cost the code could absorb.

### Build the delta projection now

Good, because this record's own arithmetic says it will be needed within weeks, and building it before the allowance binds is cheaper than building it during a month when the display has stopped updating.
Bad, because the arithmetic rests on a derived intake figure and a disputed volume, and this project's rule is that a number decides a build only when it has been measured. A week costs little and the guard already warns.

### Pay for Airtable

Good, because it removes the constraint entirely and needs no design.
Bad, because the scope floor forbids paid services, and the constraint has been productive: it is what forced the display to have a removal path at all.

## More Information

ADR-0004 owns the allowance, its once-ever grace period and where the counter is read. ADR-0050 owns the sweep, the 60% warning and the measured per-run costs. ADR-0055 owns the two mechanisms that lower the display's size. ADR-0040 owns the convergence the fingerprint fallback protects. ADR-0034 owns the Airtable client and ADR-0035 the upsert that makes a resend idempotent.

The operator's decisions, 2026-09-28: the design recorded now rather than built now, the build pre-authorised on a week's measurement, and the observation that makes the guard permanent rather than a one-off, which is that adding boards and platforms will raise the display again whatever it settles at today.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-04 | The week's measurement marked live only | ADR-0049, as amended 2026-10-03, asks every Confirmation clause to be a test or to say it can be seen only on live runs; this one is counts over production mornings |
