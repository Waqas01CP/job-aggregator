---
status: accepted
topic: display
description: The projection reads `Jobs` back and sends only the rows that differ from what the repository says they should be. The operator's choice over ADR-0056's recorded delta design, which this supersedes. Airtable is still never the source of truth.
date: 2026-10-07
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0060: The projection sends only what differs from `Jobs`

## Context and Problem Statement

ADR-0056 kept the whole-layer projection, recorded a delta design to replace it, set three triggers, and pre-authorised the build on one week's measurement of the display's intake. The design: keep a per-group record of what was confirmed sent, split between the public and private stores; send only new or changed groups; send everything whenever the rules' fingerprint changes.

The week came in high. The implementing seat's report on Brief 10, from the run logs on `data` at `b4f9f03`: six mornings, 2026-09-29 to 2026-10-04, in which the display grew from 74 to 113 groups and reached 115 on the evening of 10-04. About 7.5 new rows a day, which ADR-0055's thirty days make a steady display of about 220 to 230 rows (arithmetic on measured counts). At about 200 rows the whole-layer projection costs 20 calls each, 40 a day, and the month's 1,000 would be reached around 2026-10-22 to 10-24 (arithmetic). The trigger of 100 rows was passed, so the build was authorised.

The seat proposed a different design from the recorded one: read `Jobs` back and send only the rows that differ from it. Put to the operator with both costs at about 230 rows, read-back about 250 calls a month and the recorded design about 100, he chose the read-back on 2026-10-07 UTC. His instruction with it: "recommendation accepted but you should check if this raises new problems."

The tension is between calls and moving parts. The recorded design is cheaper, and it needs a stored record of what was sent, kept in two stores, and a fingerprint of the rules. The read-back costs more calls, and it needs no stored state at all, because `Jobs` itself says what was sent.

## Decision Drivers

- Airtable's free plan allows 1,000 calls a month per workspace, with a grace period available once ever (ADR-0004).
- The display must converge on the current rules (ADR-0040).
- Airtable is never the source of truth (ADR-0004).
- Fewer moving parts fail in fewer ways; a record of what was sent can disagree with what was sent.
- Every new source raises the display permanently (ADR-0056, carried forward).

## Assumptions

- The display's steady size is about 220 to 230 rows. **Measured** intake over six mornings, with the steady state as arithmetic, by the implementing seat on 2026-10-04.
- Read-back costs about 250 calls a month at that size, the recorded design about 100. **Arithmetic** by the implementing seat, put to the operator on 2026-10-07. The read itself costs 2 to 3 calls a run even when nothing changed.
- A value Airtable returns in a format other than the one sent would be re-sent every run without ever being wrong. **Not observed**; the run log's counts make it visible at once.

## Considered Options

- Keep the whole-layer projection.
- ADR-0056's recorded delta design: a stored per-group record of what was confirmed sent, and a rules fingerprint.
- Read `Jobs` back and send only what differs from it.
- Pay for Airtable.

## Decision Outcome

Chosen option: "read `Jobs` back and send only what differs from it".

**We will read `Jobs` on each projection and send only the rows that are new or whose pipeline-owned fields differ from what the repository says they should be.** Every value sent comes from the repository; the read decides only which rows need sending.

**We will make the read through the sweep's client.** `src/airtable.py` still only writes (ADR-0034).

**We will fail the projection on a failed read**, exactly as on a failed write, with the same escalation (ADR-0034's Changes).

**We will report in the run log how many rows were unchanged, new and changed**, so that a format mismatch, or any other row re-sent run after run, is seen at once.

**We will leave removal to the sweep** (ADR-0050). The projection adds and updates; the sweep subtracts. Carried forward unchanged from ADR-0056.

### Consequences

The invariant stays one sentence: each run makes the display match the repository, sending only what differs. No record of what was sent exists to drift from what was sent.

**ADR-0004's ruling of 2026-09-23, that the projection performs no reads, is reversed.** The principle it protected stands: Airtable is never the source of truth, and losing it costs a screen, not data.

Convergence on the rules needs no fingerprint. A field a rule changes differs from what `Jobs` shows, so it is sent, which satisfies ADR-0040 by construction.

The cost is higher than the recorded design's, about 250 calls a month against 100 at 230 rows, accepted by the operator for the simpler mechanism. ADR-0055's clock, removing rows from about 2026-10-17, and his clearing tool are the levers on the display's size.

The four places ADR-0056 named for the day of the build read as follows with the read-back. ADR-0034 and `CLAUDE.md`, "the next run re-projects the whole layer": still true in effect, since the next run compares the whole layer and sends what is missing. ADR-0035: its upsert is still what makes a resend harmless. ADR-0040: satisfied without a fingerprint, as above.

### Confirmation

**A run in which nothing changed sends no upsert call.**

**A row whose pipeline-owned field changed is sent, and one whose fields did not is not.**

**A rule change reaches the display**: rows the change affects differ from `Jobs` and are sent on the next run.

**A failed read fails the projection.**

**A row the current rules no longer admit still leaves the display through the sweep**, not through the projection.

**Live only:** the month's call count under the read-back, against the arithmetic above, from the run logs.

## Pros and Cons of the Options

### Keep the whole-layer projection

Good, because it is the simplest invariant and needs no read.
Bad, because at the measured intake the allowance runs out around 2026-10-22.

### ADR-0056's recorded delta design

Good, because it is the cheapest in calls, about 100 a month at 230 rows.
Bad, because it keeps a record of what was sent in two stores and a fingerprint of the rules, each a way for the record and the display to disagree.

### Read `Jobs` back

Good, because the display itself is the record of what was sent, so there is nothing to keep in step.
Bad, because it costs more calls than the recorded design, and it reverses ADR-0004's no-read ruling for the projection.

### Pay for Airtable

Bad, because the scope floor forbids paid services (ADR-0056, carried forward).

## More Information

**Supersedes ADR-0056.** Carried forward unchanged: removal is the sweep's job and never the projection's; every new source raises the display permanently; paying is excluded by the scope floor. ADR-0056's three triggers and its pre-authorisation are spent: the build they called for is this record.

Built by the implementing seat as commit `a3e387a`. ADR-0004 owns the allowance and carries the reversal in its Changes. ADR-0034 owns the clients and the escalation, ADR-0035 the upsert, ADR-0040 the convergence, ADR-0050 the sweep, ADR-0055 the clock and the clearing tool.

The operator's decision, 2026-10-07 UTC, on the seat's proposal and after both designs' costs were put to him.

## Changes
