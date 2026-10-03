---
status: accepted
topic: display
description: Five append-only stores written by the sweep: three outcome corpora, one per kind of outcome, plus the removal store and the removed-copies store. What each one is allowed to feed back into, and which of them the projection reads. Reverses ADR-0014's single-file clause.
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

**This reverses ADR-0014's "not one file per status", and keeps what that clause was protecting.** The invariant was that a row has exactly one outcome. Routing is therefore exclusive: a swept row goes to exactly one store, decided by its status, and no identity may appear in two. That is now a checkable property rather than a property of the file layout, which is the better place for it. *(Annotated 2026-09-28: **the exclusivity invariant covers the three classification stores above and no others.** This record has since grown two more stores, and neither is an outcome corpus. An identity may legitimately appear in a classification store and in `removed_copies.json` at the same time, because D12 writes an `accepted` copy to both. A check that intersected all five would fail on correct behaviour.)*

**This record now owns five stores.** The three above are the outcome corpora. `outcomes/removed_unreviewed.json` holds a row removed from the display without a judgement, with the reason it went. `removed_copies.json` holds a classification-table copy removed other than by the fifteen-day clock. Only the three corpora are read as feedback, and only they are read by the projection's skip for their own sake; what the projection does with the removal store is set out below.

**Metadata only, per ADR-0011.** An outcome record carries the row as the filtered layer holds it, plus the status, the reason where one was given, and the date swept. No description text, and no note the operator typed in Airtable, because a free-text note is exactly where description text would arrive by the back door. *(Extended 2026-09-28: the same limit binds the two later stores. A removed copy carries the ten identifying fields the sweep copied, its reason or its `Stage`, and the dates, and nothing else.)*

**A row returns to the display only if the reason it left was the rules, because only the rules can change their mind.** *(Added 2026-09-28; see Changes.)* The projection's skip therefore reads `outcomes/removed_unreviewed.json` by reason and not as a whole: a row stored with reason `closed` stays out, and a row stored with the name of a rule that dropped it returns when that rule widens, which is what ADR-0040 requires. The principle, rather than a list of reasons, is what binds, so a reason added later is covered without amending this record.

**ADR-0020 applies to all three.** Each store splits the way the filtered layer splits: an aggregator's rows go to the local copy and never to the branch. *(Changed by ADR-0047: an aggregator's rows in these stores go to the private repository's copy, not a local file alone, and still never to the public branch. The sweep writes them there from 2026-09-25, ADR-0050. The corpus audit's conflict 6.)* A new store is a new path for a row that may not be published, and the content guard at the commit boundary reads every record's source, so it catches this only if the split is done. It must be done.

**What may feed back, and what may not.** These corpora inform the operator's decisions about configuration. **No rule changes itself from them.** ADR-0010 and ADR-0031 together mean a pool term is added because the operator adds it to a file, never because a corpus suggested it. A tool may report "these eleven rejected_not_a_fit rows were all admitted by `ai ops`"; only he removes the term.

### Consequences

The sweep gains routing and three writers where it had one. It is unbuilt, so this costs nothing now and must be built this way rather than retrofitted.

A reader wanting every outcome must read three files. That is the trade, and it favours the three readers who each want one.

`rejected_poor_filtering` becomes the most valuable file in the repository for improving the filter, because every row in it names the rule that admitted it wrongly.

Three more files on the data branch, each append-only, each subject to the same byte-identical-diff discipline.

The accepted store is read by the projection on every run once ADR-0044's star exists, so it moves from a log to a dependency.

### Confirmation

After the first sweep, no identity appears in more than one store. Take the three files, intersect their identities pairwise, and all three intersections must be empty. *(Scoped 2026-09-28: the three classification stores only, for the reason annotated above.)*

**The skip must be seen reading the removal store by reason**, which is ADR-0050's check and is named here because this record owns the store: a row stored with reason `closed` is not projected, and a row stored with a rule's name is projected once the rule admits it again. A test that passes for both reasons is asserting something other than the principle.

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

**The five stores, and who reads each.** `outcomes/rejected_not_a_fit.json`, `outcomes/rejected_poor_filtering.json` and `outcomes/accepted.json` are the corpora: the operator reads all three, the projection's skip reads all three, and ADR-0044's star reads the last. `outcomes/removed_unreviewed.json` is read by the operator as a measure of what he missed, and by the skip for its `closed` rows alone. *(Corrected 2026-10-03, the fourth audit's F10: this contradicted the principle stated above it in the same edit. The skip keeps out every row whose reason was not a rule's drop, which includes `unreviewed-aged-out` and `operator-removed` from ADR-0055; only a rule's drop can return.)* `removed_copies.json` is read by nobody automatically; it exists so that no copy is ever deleted unsaved, which is D12's rule and the operator's own understanding of how the tables had always behaved.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | The "no fourth store" clause is reversed. `outcomes/removed_unreviewed.json` is written by ADR-0046's sweep step 4: an unreviewed row the current chain no longer admits, with the rule that dropped it and the date. A row dropped by the expiry rule is the event `expired_before_review` named | This record rejected a fourth store because "nothing would read it". Two things changed. The operator asked for the signal and is its reader: how many roles closed before he saw them, on which boards, and how long after they were surfaced. And ADR-0046 retired `expired_before_review` as a status, so without a store the event would have no home at all. The three outcome stores are unaffected, and this fourth one is not read by the projection's skip, so a row that fell out on a narrowed rule can still return if the rule widens |
| 2026-09-24 | The status names feeding the stores annotated as stale | ADR-0046 decided new names that never reached the base, and the operator renamed them after the tables on 2026-09-24 *(corrected after that day's audit, F12)*. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
| 2026-09-25 | ADR-0047 named where it changed where aggregator outcomes are stored | The corpus audit's conflict 6: ADR-0047 moved "its rows in ADR-0043's three outcome stores" to the private repository without naming this record. Annotated by the implementing seat under ADR-RULES, on Brief 7's corpus work; the Decision Outcome is untouched. |
| 2026-09-26 | A fifth store, `removed_copies.json`, keyed by the copy's Airtable record ID. It holds every classification-table copy that leaves for any reason other than the fifteen-day clock: a rejection copy superseded by a status change, and an `accepted` copy the operator marks `Delete`. The exclusivity invariant is scoped to the three corpora, because an `accepted` copy is written here and to the accepted store in the same run | The operator's D12, answering the third audit's F1. ADR-0050 line 71 deleted a superseded copy unsaved, losing the reason it carried, and line 73 had no field for him to mark. A store that nothing reads automatically is the right shape here: its purpose is that a deletion is never the only record of a row, which is this project's oldest rule |
| 2026-09-28 | The removal store is read by the projection's skip **by reason**, not ignored wholesale as the 2026-09-23 row said. One principle replaces the enumeration: a row returns only if the reason it left was the rules | The architecture chat's error, found by the implementing seat. ADR-0050 assumed a closed row would not return because the closure test still held. It does return, at once, because the filtered layer keeps every row it admitted and ADR-0040 re-projects it; the four-run absence count would then restart from nothing. Rule-dropped rows must still return, so the store cannot simply be read in full either. Stated as a principle so that the reasons the operator's removal tool and the unreviewed clock will add need no further amendment here |
| 2026-10-03 | Line 111's "for its `closed` rows alone" corrected to the principle. Three facts of the store recorded as built: it is keyed on identity and reason, and a row's latest record decides; a member that stopped being its group's display row returns, because the grouping follows the rules; and an accepted edge, the audit's F15, where a retired Lever posting can keep out a later Lever posting with the same employer, title and creation date | The first is the chat's inconsistency, found by the fourth audit. The three facts are the implementing seat's method within this record, read correctly: one record per row would let a row that returned and left again be judged against its old reason, and grouping is a consequence of the rules, not a judgement. F15 needs two Lever postings identical on all three and one retired before the other appears; ADR-0052 keeps every other source's late arrival out, so it is left as built |
