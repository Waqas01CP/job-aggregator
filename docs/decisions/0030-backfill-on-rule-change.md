---
status: accepted
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0030: A rule change backfills the filtered layer

## Context and Problem Statement

The filtered layer is append-delta and a run writes only postings it is seeing for the first time. `src/run.py` splits kept rows against the seen store before writing, so a posting reaches `filtered.json` only on the run that first records its identity.

That has a consequence nobody stated until it was measured. When the filter rules widen, rows the new rules would admit never arrive, because the postings were already seen under the old rules. The converse was known and raised: rows kept under older rules stay in the file, since nothing is ever rewritten.

Measured on the `data` branch at `91f7518`, with the chain and the seen store the runner itself loads:

| | Count |
|---|---|
| Postings stored | 804 |
| Kept by pool version 4 with the seniority rule | 270, collapsing to 25 groups |
| `filtered.json` rows | 24, collapsing to 23 groups |
| Of those 24, rows the current chain would drop | 11 |
| **Kept but absent from the file, and unwritable** | **257** |

Among the 257 is the Veeam AI internship that pool version 4 was widened to catch, and 241 Speechify city copies of one role. So the public file currently under-represents the rules in force, in both directions at once.

This is not specific to pool version 4. Every future pool change, seniority change or family change inherits it.

## Decision Drivers

- The display exists so the operator sees roles that match his rules. A role the rules admit and the file omits is the failure the project exists to prevent.
- ADR-0013 calls Airtable a projection of the filtered file. A projection is only as accurate as what it projects.
- ADR-0003's append-only guarantee is what keeps the branch diffable, and it must survive whatever is chosen.
- A pool change that quietly does nothing to existing data teaches the operator that widening the pool does not work.

## Assumptions

- Rule changes are infrequent, on the order of a few a month. **Sourced** from four pool versions in seven days during active development, which is an upper bound rather than a steady state. A backfill's cost scales with rule changes, not with runs.
- Re-running the chain over the stored raw layer is cheap. **Measured**: 804 postings through the full chain is sub-second, and the raw layer is read from the branch a run already fetches.

## Considered Options

- Re-apply the current chain at projection time.
- Copy the filtered file as it stands and accept the drift.
- Backfill the filtered file when the rules change, then copy it.

## Decision Outcome

Chosen option: "backfill on rule change".

**When the filter rules change, a backfill pass re-runs the current chain over the raw layer and appends to `filtered.json` every row the rules now admit that the file does not already hold.** The projection then copies the file as it stands, per ADR-0013, and is accurate.

**This does not violate ADR-0003.** That record says "We will append only records absent from the raw layer. We will never rewrite an existing record and never write a full snapshot." A backfill appends records absent from the file and rewrites nothing. It is the same operation a run performs, differing only in what triggered it.

**Rows admitted under older rules stay.** Nothing is removed, because removal would be a rewrite. The file is the durable record of what was kept and when, and a row the current rules would reject remains in it with its original verdict. The display's own filters, and the operator's `rejected_pipeline` status, are where a stale row is dealt with.

This answers questions I and J together, which were the two halves of one question.

### Consequences

The filtered file tracks the rules in force, so widening the pool has a visible effect on the next projection rather than only on postings not yet published.

A backfill is a second writer of `filtered.json` and must use the same append-delta path and the same content guard as a run, or ADR-0020's routing can be bypassed.

The file will contain rows whose `first_seen` long predates their appearance in the display. Measure A already excludes postings published before the pipeline's first successful run against their board, under ADR-0015, so backfilled rows must be excluded from Measure A the same way. Without that, a backfill would make freshness look catastrophic.

Running the chain over the raw layer means the chain must be pure with respect to run state. It is today: `apply_chain` takes rows and a clock.

The alternative of re-applying rules at projection time is rejected, and with it the idea that the filtered file is merely a log.

### Confirmation

After the next rule change, the backfill runs and the count it appends is reported in the run log. Take the raw layer, apply the current chain, and subtract the file: the remainder must be empty. If it is not, the backfill missed rows and the file still under-represents the rules.

Give the check the case built to defeat it: a posting that the old rules admitted and the new rules reject must still be in the file afterwards, untouched, with its original matched term.

## Pros and Cons of the Options

### Re-apply the current chain at projection time

Good, because the display is always exactly the current rules with no second writer.
Bad, because `filtered.json` stops being the thing the display reads and becomes a historical log, which contradicts ADR-0013's "projection of that file", and because the projection would then need the raw layer, not the filtered one.

### Copy the file as it stands, no backfill

Good, because it is what exists today and needs no code.
Bad, because measured today it shows 24 rows of which 11 are wrong under the current rules, and omits 257 that are right.

## More Information

Supersedes nothing. Answers the questions raised in `2026-09-17-first-scheduled-run.md` (rows kept under older rules) and in `2026-09-17-corrections-and-airtable-schema.md` (rows never admitted).

ADR-0037 decides separately that the filtered layer stores rows rather than group representatives, which is what makes the 257 a row count rather than a group count.
