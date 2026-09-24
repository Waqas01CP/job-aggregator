---
status: accepted
topic: display
description: Three append-only outcome corpora, one per kind of outcome, and what each one is allowed to feed back into. Reverses ADR-0014's single-file clause.
date: 2026-09-18
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0043: Three outcome stores, and what each is for

## Context and Problem Statement

ADR-0014's sweep reads a row's status, writes it to an outcomes log, and deletes the row from Airtable. It treats all four statuses alike: "We will record outcomes in one file with a status discriminator, not one file per status, so a row has exactly one outcome."

That was right for its purpose, which was to capture an outcome and free the display. It is wrong for the purpose the operator now has, which is different: the outcomes are **corpora that feed back into filtering**, and the three that do so are read by different consumers for different reasons.

- **`rejected_not_a_fit`**: the role was correctly surfaced and he chose not to apply. This teaches what to stop admitting, which is a question about the title pool.
- **`rejected_poor_filtering`**: the pipeline should not have surfaced it at all. This is the filter's own defect log and the strongest feedback signal in the system.
- **`accepted`**: shortlisted or applied to. This is what ADR-0044's priority star compares against.

Reading any of those out of a mixed file means filtering it first. "Every role he turned down" should be a file, not a query, because it is going to be read by a person deciding what to change about the pool.

## Decision Drivers

- The three corpora have different readers and different lifetimes; one of them is consumed by code on every projection.
- ADR-0014's invariant, that a row has exactly one outcome, is worth keeping whatever the file layout.
- Anything on the data branch inherits ADR-0011 and ADR-0020, and a new store is a new way to leak an aggregator's rows.
- A defect log that is hard to read does not get read.

## Assumptions

- Outcome volume stays small, on the order of tens a month. **Sourced** from 24 filtered rows in three runs and the operator reviewing by hand; not measured, because no sweep has run.
- The operator will set statuses at all. **Not established.** No row has been reviewed, because the display does not yet receive rows.

## Considered Options

- One outcomes file with a status discriminator, as ADR-0014 says.
- Three files, one per outcome class.
- Three files plus a fourth for `expired_before_review`.

## Decision Outcome

Chosen option: "three files, one per outcome class".

**Three append-only stores on the data branch**, written by the sweep, in the same serialisation as every other store and through the same append-delta writer:

| Store | Fed by ADR-0014's status | Read for |
|---|---|---|
| `outcomes/rejected_not_a_fit.json` | `rejected_choice` | what to stop admitting |
| `outcomes/rejected_poor_filtering.json` | `rejected_pipeline` | the filter's defects, with the reason naming the rule |
| `outcomes/accepted.json` | `applied` | ADR-0044's priority star |

*(Annotated 2026-09-24, stale: ADR-0046 decided new names for these statuses, `not fit` and `poor filtering`, which never reached the base; on 2026-09-24 the operator named them after the tables they feed, `rejected-not-a-fit`, `rejected-poor-filtering` and `accepted`, in the base from 15:30Z. Corrected after that day's audit, F12.)*

**`expired_before_review` gets no store.** *(Amended 2026-09-23: this clause is reversed. The status is retired, and the event it named is recorded in a fourth store. See Changes.)* It is not a judgement about a role; it measures the cost of the operator's absences, which is what ADR-0014 already says it is for. It stays a counted outcome and nothing reads it as a corpus.

**This reverses ADR-0014's "not one file per status", and keeps what that clause was protecting.** The invariant was that a row has exactly one outcome. Routing is therefore exclusive: a swept row goes to exactly one store, decided by its status, and no identity may appear in two. That is now a checkable property rather than a property of the file layout, which is the better place for it.

**Metadata only, per ADR-0011.** An outcome record carries the row as the filtered layer holds it, plus the status, the reason where one was given, and the date swept. No description text, and no note the operator typed in Airtable, because a free-text note is exactly where description text would arrive by the back door.

**ADR-0020 applies to all three.** Each store splits the way the filtered layer splits: an aggregator's rows go to the local copy and never to the branch. A new store is a new path for a row that may not be published, and the content guard at the commit boundary reads every record's source, so it catches this only if the split is done. It must be done.

**What may feed back, and what may not.** These corpora inform the operator's decisions about configuration. **No rule changes itself from them.** ADR-0010 and ADR-0031 together mean a pool term is added because the operator adds it to a file, never because a corpus suggested it. A tool may report "these eleven rejected_not_a_fit rows were all admitted by `ai ops`"; only he removes the term.

### Consequences

The sweep gains routing and three writers where it had one. It is unbuilt, so this costs nothing now and must be built this way rather than retrofitted.

A reader wanting every outcome must read three files. That is the trade, and it favours the three readers who each want one.

`rejected_poor_filtering` becomes the most valuable file in the repository for improving the filter, because every row in it names the rule that admitted it wrongly.

Three more files on the data branch, each append-only, each subject to the same byte-identical-diff discipline.

The accepted store is read by the projection on every run once ADR-0044's star exists, so it moves from a log to a dependency.

### Confirmation

After the first sweep, no identity appears in more than one store. Take the three files, intersect their identities pairwise, and all three intersections must be empty.

The check that can fail: hand-write a row into two stores and confirm the check reports it. A check over three files that never overlap by construction would pass whatever the routing did.

Separately, and this is the one that matters for ADR-0020: put an aggregator-sourced row through the sweep and confirm it lands in the local copy and that the commit step refuses any store file holding it.

## Pros and Cons of the Options

### One file with a discriminator

Good, because it is what ADR-0014 decided, it guarantees one outcome per row by construction, and it is one writer.
Bad, because each of the three readers must filter it first, and the defect log, which is the one a person reads while deciding what to fix, is the hardest to extract.

### A fourth store for `expired_before_review`

Good, because it is symmetrical.
Bad, because nothing would read it. It is a measure of absence, not a corpus of judgements, and a file nobody reads is a file that goes stale without anyone noticing.

## More Information

Reverses one clause of ADR-0014, which carries a Changes row pointing here. The four statuses, their reasons and the write-before-delete rule are unchanged.

ADR-0044 consumes the accepted store. ADR-0011 governs what a record may carry. ADR-0020 governs the split. ADR-0003 governs the append.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | The "no fourth store" clause is reversed. `outcomes/removed_unreviewed.json` is written by ADR-0046's sweep step 4: an unreviewed row the current chain no longer admits, with the rule that dropped it and the date. A row dropped by the expiry rule is the event `expired_before_review` named | This record rejected a fourth store because "nothing would read it". Two things changed. The operator asked for the signal and is its reader: how many roles closed before he saw them, on which boards, and how long after they were surfaced. And ADR-0046 retired `expired_before_review` as a status, so without a store the event would have no home at all. The three outcome stores are unaffected, and this fourth one is not read by the projection's skip, so a row that fell out on a narrowed rule can still return if the rule widens |
| 2026-09-24 | The status names feeding the stores annotated as stale | ADR-0046 decided new names that never reached the base, and the operator renamed them after the tables on 2026-09-24 *(corrected after that day's audit, F12)*. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
