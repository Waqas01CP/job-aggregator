---
status: accepted
topic: display
description: The current rules filter the projection and never the store. The half of the append-only problem that removes rows.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0040: The current rules filter the projection, never the store

## Context and Problem Statement

ADR-0030 handled one direction. When the rules widen, a backfill appends the
rows they now admit, so the file catches up.

It did not handle the other. When the rules contract, rows admitted under the
old rules stay in `filtered.json`, correctly, because removing them would be
a rewrite and ADR-0003 forbids that. ADR-0030 then says the projection copies
the file as it stands, which puts those rows in the display.

Measured on the `data` branch at `90553c3`: `filtered.json` holds 24 rows and
**the current chain rejects 11 of them**. Ten are senior-level roles kept
before ADR-0032's seniority rule existed; one is Motive's "Senior Program
Manager, AI Ops (GTM)", admitted by `ai ops` and dropped by seniority.

So the display would show the operator eleven roles he has already decided he
does not want, and would go on showing them. The file is right and the
display is wrong, which means the fix belongs at the projection.

## Decision Drivers

- The filtered file is the durable record of what was admitted and when.
  Editing it to match today's opinion destroys that.
- ADR-0003's append-only guarantee is what keeps the branch diffable and must
  not be weakened at any layer.
- The display exists to show the operator roles he might take. A role his own
  rules reject is noise, and noise is the problem the project exists to fix.
- Rules will contract again. The seniority list inverts when his experience
  does, per ADR-0032.

## Assumptions

- The chain is pure with respect to run state. **Measured**: `apply_chain`
  takes rows and a clock and nothing else, which is what makes it runnable at
  projection time over stored rows.
- Contraction is rarer than widening. **Not measured.** One contraction has
  happened, the seniority rule, against four pool widenings.

## Considered Options

- Remove superseded rows from the filtered file.
- Mark superseded rows in the file with a verdict field.
- Apply the current chain at projection time, as a display filter.

## Decision Outcome

Chosen option: "apply the current chain at projection time".

**The projection runs the current filter chain over `filtered.json` and
projects only the rows it admits.** The file is never filtered, never
rewritten and never pruned. It stays append-only and complete.

**This is still a projection in ADR-0013's sense.** That record says Airtable
is "a projection of that file", and a projection that shows a subset of its
source is still a projection of it. What ADR-0030 rejected, and still
rejects, is projecting from the **raw layer** instead, which would make the
filtered file a log that nothing reads. The source stays the filtered file.

**ADR-0030 is amended in one clause**: "the projection then copies the file as
it stands" becomes "the projection reads the file and applies the current
chain". Its backfill is unaffected and both halves now work together. A rule
change widens, the backfill adds the new rows, and the projection hides the
rows the change removed.

**The weekly sweep removes rows that have since fallen out**, per ADR-0014,
so the display converges rather than accumulating.

**One exception to removal, which this record adds.** A row the operator has
already actioned is not removed. `Status`, `Pipeline reason` and `Choice
reason` are his, per ADR-0035, and deleting a row he marked `applied`
destroys the record of an application. **The sweep removes only rows whose
`Status` is empty.** A row he has marked stays, whatever the rules now say
about it.

### Consequences

The display shows exactly what the current rules admit, and changing the
rules changes the display on the next projection in both directions.

The projection now needs the chain, which means the writer imports the
filter module. That is a real coupling and it is the point: one definition of
what is admitted, used in both places.

A row can leave the display and return, if a rule contracts and later widens.
Its `first_seen` is unchanged, so its position in a date-ordered view is
unchanged, and it will not look new.

The file and the display now differ in row count by design, on top of the
grouping difference ADR-0037 introduces. Anyone comparing the two numbers
without reading these three records will think something is broken.

Projection cost rises from a copy to a chain run over the whole file. At 24
rows this is nothing, and at the scale the backfill implies it is still one
pass over a file the projection already reads.

### Confirmation

Project the current file. The display's row count must equal the number of
rows the chain admits, grouped per ADR-0037, and the eleven senior rows must
not appear.

The check that can fail: mark one of those eleven `applied` in Airtable, then
run the sweep. It must still be there afterwards. If it is gone, the sweep is
removing rows by rule alone and has destroyed an application record.

A second check for the store: after any projection, `filtered.json` must be
byte-identical to what it was before. The projection is a reader.

## Pros and Cons of the Options

### Remove superseded rows from the file

Good, because the file and the display then agree exactly.
Bad, because it is a rewrite of an append-only store, it destroys the record
of what was admitted when, and it cannot be undone if the rule change is
reversed.

### Mark rows in the file with a verdict field

Good, because the history is kept and the display can filter on a stored
flag.
Bad, because the flag is written once and the rules change again, so the file
accumulates stale verdicts, which is ADR-0037's stored-representative mistake
in another form.

## More Information

Amends ADR-0030, which carries a Changes row pointing here. Completes the
answer to questions I and J.

ADR-0003 is why the file is not edited. ADR-0013 is what a projection is.
ADR-0014 owns the sweep. ADR-0035 owns the field ownership the removal
exception rests on. ADR-0037 owns the grouping the projection also applies.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-19 | Extended by ADR-0046, and one clause narrowed. The projection now also skips any identity present in one of ADR-0043's three outcome stores. "The sweep removes only rows whose `Status` is empty" now governs removal **by rule** alone: ADR-0046's sweep deletes rows whose status is not empty, but only after their outcome is written to a store and read back | Without the skip, a row deleted under the retention flow is projected again on the next run, because this record re-applies the chain to the whole filtered layer and ADR-0035's upsert matches only rows present in `Jobs`. The protection the empty-status clause gave an actioned row is now given by the store: a row leaves `Jobs` only once its outcome is durable |

The sweep this record hands removal to was ADR-0014's when this was written. ADR-0014 was superseded by ADR-0045 and ADR-0045 by ADR-0046. The reference is left as written and the chain is followable from ADR-0014's own marker.
