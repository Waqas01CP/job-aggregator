---
status: accepted
topic: storage
description: Only records never seen before are appended, and nothing is ever rewritten. Why a run that changes nothing produces an empty diff.
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0003: Append deltas, not snapshots

## Context and Problem Statement

ADR-0002 places the raw layer in git. Git stores a new object for every changed file, so the write strategy determines whether the repository stays usable over time.

A snapshot strategy writes the complete current state on every run, producing a fresh copy of the whole dataset each time. A delta strategy writes only records not previously seen.

Some fields change over time. A posting's last-seen date and closure status are properties of the posting's life, not of the moment it was first observed, and cannot be updated in place on an append-only record.

## Decision Drivers

- Repository size must stay small enough that cloning and diffing remain practical indefinitely.
- A diff must mean a change, or history is unreadable.
- Lifecycle fields need somewhere to live that tolerates rewriting.

## Assumptions

- A posting record serialises to roughly 2 KB. Estimated from field count; not measured.
- Roughly one thousand postings are fetched per run. **Falsified 2026-09-15.** Eleven boards returned 1646. See Changes.
- Genuinely new postings arrive at twenty to fifty a day. Estimated; not measured, and the figure most likely to be wrong. *(Measured 2026-09-25 from the run logs on `data`: on the eleven ATS boards, 0 to 21 a day across seven days with two runs, 80 on the day Speechify rotated its city copies, and 804 on first contact. The estimate was high.)*

On those assumptions, snapshots cost roughly 1.4 GB of repository growth a year and deltas roughly 36 MB. The ratio, not the absolute figures, is what carries the decision.

## Considered Options

- Snapshot the full raw layer on every run.
- Append only records not previously seen.

## Decision Outcome

Chosen option: "append only records not previously seen".

We will append only records absent from the raw layer. We will never rewrite an existing record and never write a full snapshot. We will keep mutable lifecycle state in a separate seen-identifier structure small enough to rewrite each run, following the split between `linkedin_raw_jobs.json` and `linkedin_seen_jobs.json` already in production.

### Consequences

Repository growth falls by roughly forty times against snapshots, from unusable to negligible.

The raw layer is reconstructed by reading all appended records, not by reading one current-state file.

Lifecycle fields cannot live on the raw record. They live in the seen structure, which is a second file with different write semantics.

A run that fails partway appends a partial set. Individual records are complete, so a partial append is not corrupting, but the run log must record what was written.

### Confirmation

Measure data-branch size monthly for the first three months and compare against the 36 MB per year projection. Also confirm that a run adding no new postings produces a commit whose only change is the run log, per the serialisation discipline in section 8 of the architecture document.

## Pros and Cons of the Options

## More Information

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-15 | The postings-per-run assumption is falsified and the snapshot cost projection rises | Eleven boards returned 1646 postings, so the snapshot cost at measured volume is 2.40 GB a year rather than 1.4 GB. **The decision is unaffected.** The argument was the ratio between snapshots and deltas, and the delta cost does not depend on postings per run at all. A higher fetch volume makes snapshots worse, not deltas |
| 2026-09-17 | Confirmed compatible with ADR-0030's backfill | A backfill appends records absent from the filtered file and rewrites nothing, which is exactly what this record permits. 'We will never rewrite an existing record and never write a full snapshot' is unaffected |
| 2026-09-25 | The estimate of new postings a day measured, and ADR-0028 named as extending this record | The corpus audit found the figure with no basis. ADR-0028 extends this record and was not named here. Annotated by the implementing seat under ADR-RULES, on Brief 7's corpus work; the Decision Outcome is untouched. |
