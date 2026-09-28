---
status: accepted
topic: practice
description: How records are resolved, amended and retired. Two ranks the authority order lacks, the difference between stale and wrong, and what a seat may correct without asking. Read through, not in sequence.
date: 2026-09-18
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-RULES: how records are resolved, amended and retired

Named rather than numbered. Numbers record the order a decision was concluded and are read in sequence; this record is read **through**, when another record is in question.

**ADR-0042 was reserved for this record and is deliberately unused.** The gap between 0041 and 0043 is not a missing file. It is recorded here so nobody spends a session looking for one.

## Scope

This governs the other records. It decides nothing about the pipeline.

## Two ranks the authority order lacks

ADR-0022 sets seven ranks and ADR-0025 adds an eighth. They are not restated here; duplicating them would create the second copy of a fact this project exists to avoid. Two ranks are missing from that order.

**A brief ranks below CLAUDE.md and below any accepted record.**

A brief from the architecture chat is not a decision. It is an instruction to implement decisions, and an instruction that contradicts the thing it implements is an error in the instruction. The implementing seat follows the record and reports the contradiction. *(Extended 2026-09-22: one exception, and the brief's place against the lower ranks. See Changes.)*

This is not hypothetical. A brief dated 2026-09-17 said "amend" for nine records where CLAUDE.md forbids editing an accepted record to change a decision. The seat split the changes by kind, followed the standing rule, and said plainly which instruction it had not followed as written. It resolved correctly without a rule to resolve it by, and this record is that rule.

**Reality outranks every document.**

Where a document's account of what exists disagrees with the code or the data, the code and the data win, and the document is reported as stale.

CLAUDE.md carries this as a working rule. It belongs in the authority order as well, because a stale record and a live one are indistinguishable until something is checked, and the order is what a session consults when it notices the difference.

## Stale is not wrong

The Decision Record Standard distinguishes reversal, extension, correction and supersession. It does not distinguish these two, and their handling differs.

**Stale:** the record was true and the world moved. Annotate with a date and what changed. The original text stays, because it was correct when written, and the change is itself the finding.

**Wrong:** the record was never true. Annotate with a date, name the error, and state what the evidence now shows. The original text stays, because a record that quietly becomes right teaches nobody why it was wrong, and the error is usually more instructive than the correction.

Neither is a supersession. Neither requires a new record. Both require a date and evidence.

## What a seat may correct unasked

**May:** annotate a factual error with a date and the evidence. Correct a reference pointing at the wrong record. Correct a number that was never measured. Report a record as stale.

**May not:** change a decision. Retire a record. Resolve a conflict between two live records. Add a rank to the authority order.

The line is whether the record's Decision Outcome changes. Everything above it is correction; everything at or below it is a decision, and decisions are concluded in the architecture chat.

## Which form marks an extension

A record that is built upon rather than changed is **marked extended in two places, and they do different jobs.**

**The binding act is a `## Changes` row in the extended record**, naming the record that extends it and what was added. `CLAUDE.md` says so and outranks this file, so that is the form.

**The index's Status cell says "extended by NNNN" as a pointer**, so a reader scanning the table sees it without opening the record. It is a signpost and never the record of the change.

Neither is optional and neither substitutes for the other. The ambiguity was real: `CLAUDE.md` said a Changes row, `docs/decisions/README.md` said "marked extended", and the implementing seat had to choose between them on 2026-09-25. It chose `CLAUDE.md`'s, which was correct on rank.

## The eight-row trigger, and the one row that does not count

A `## Changes` table stays under eight rows, and reaching eight is itself a supersession trigger.

**A row recording that the record has been superseded does not count toward the eight.** It is written after the trigger has already fired and it describes the outcome rather than another amendment. ADR-0046 carries nine rows for exactly this reason: eight amendments triggered its supersession and the ninth says ADR-0050 replaced it. A guard counting rows must exclude that row, or it reports the corpus's most correct supersession as a violation.

**A guard may also count fewer than eight.** ADR-0050 sets its own threshold at six, because the flow is the most-amended area of this corpus and a record rewritten at the trigger is a record rewritten under pressure. A record may bind itself tighter than this file; none may bind itself looser.

## The line limit is soft; the row limit is not

**Two hundred lines is a target, not a cap.** A record may run to about 250 lines without anything being owed, provided no other trigger has fired. Beyond roughly 350 to 400 lines it is a hard flag and the record is read as a supersession candidate on length alone, because at that size nobody holds it in mind whatever its row count says.

The row limit is different in kind: eight rows is a trigger and it fires.

**A threshold that has not been reached is not a finding.** The operator's instruction, 2026-09-28: "when the conditions are met only then the consequence will trigger and there is no near so just do it." Reporting that a record is approaching a limit spends attention on nothing, and it invites a rewrite in advance of a reason. Nothing is said until a condition is met.

This rule belongs to the operator's cross-project Decision Record Standard, and the copy of it in his vault is the authority. It is restated here because this corpus is where it binds.

## When two live records conflict

This is a defect. Raise it. Do not choose.

Naming a tie-break would let a real contradiction pass as a resolved one. A contradiction that blocks is recoverable; one that resolves silently is not, because nobody learns it existed.

ADR-0019 carried exactly this shape internally: its criterion named three components and its Confirmation named a narrower rule that contradicted them. It was found by a seat reading both, not by either being wrong on its own.

## When a record and the code disagree

The code wins for what is true. The record wins for what should be.

Record both, and state which one is being changed. "The code does X and the record says Y" is an observation, not a finding, until someone says which is wrong. A record corrected to match code that was itself wrong is worse than the disagreement.

## Consequences

A seat has an answer for the case where its instructions contradict its standing rules, without needing to ask.

Stale and wrong stop being handled identically, so a record that aged honestly is no longer annotated as though it had been mistaken.

The boundary between correction and decision is stated once rather than inferred per case.

Two live records in conflict now have a defined outcome, which is to stop. That will occasionally block work that could have proceeded on a guess. That is the intent.

This record can itself go stale, and nothing here exempts it. It is subject to its own rules.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | The brief gains one exception: a brief that names the record and clause it overrides, and states that the operator approved the change, carries the operator's authority, rank 1. Otherwise it sits at rank 4, below accepted records and above the architecture document. `CLAUDE.md` now states the full nine-rank order | The operator's decision, 2026-09-22. The chat writes the brief, so where it ranks against a record is his call, and the declaration in the brief is how that call reaches the seat without the seat judging it at runtime. This record said where the brief sits against records but not against the lower ranks |
| 2026-09-28 | Which form marks an extension is settled: a Changes row in the extended record binds, and the index's Status cell is a pointer. Both, doing different jobs | `CLAUDE.md` said a Changes row and `docs/decisions/README.md` said "marked extended", and the implementing seat had to choose between them while doing Brief 7's corpus work. It chose `CLAUDE.md`'s, correctly on rank, and then asked for the ambiguity to be closed rather than re-decided by the next seat that meets it. Neither form was wrong; each was half the answer |
| 2026-09-28 | A row recording a supersession does not count toward the eight-row trigger, and a record may set itself a lower threshold | ADR-0046 carries nine rows: eight amendments fired its trigger and the ninth records that ADR-0050 replaced it. A guard counting rows naively would report the corpus's most correct supersession as a violation, which is exactly the false rule ADR-0049 warns a guard can teach. ADR-0050 then set itself six, because the classification flow is where amendments concentrate and a rewrite forced by the trigger is a rewrite under pressure |
| 2026-09-28 | The two-hundred-line rule is soft: about 250 lines is acceptable while no other trigger has fired, and roughly 350 to 400 is a hard flag. The eight-row trigger is unchanged. A threshold not yet reached is not reported at all | The operator's decision, 2026-09-28, after the architecture chat reported two records as near the line limit: "the 200 lines is a soft rule meaning not a hard cap and even if it goes to 250 then it is fine as long as the other conditions are not met. but this lines when reached lets say 350 or 400 then it can be a hard flag", and "when the conditions are met only then the consequence will trigger and there is no near so just do it". Length is a proxy for readability and a poor one on its own; the row count measures how often a decision was reopened, which is what the trigger is for. The second half is the more useful half: a guard that reports proximity turns every limit into a running commentary |
