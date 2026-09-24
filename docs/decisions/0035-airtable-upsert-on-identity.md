---
status: accepted
topic: display
description: The projection upserts on Identity so a retried write creates no duplicates, and writes only pipeline-owned fields.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0035: The projection upserts on Identity

## Context and Problem Statement

ADR-0004 decides at line 40 *(line 42 since `dc02b0f` added two frontmatter lines on 2026-09-18)*: "We will write the filtered layer to an Airtable base using batched creates of ten records per call. We will perform no reads. We will determine novelty entirely from repository-side state."

Plain creates are not idempotent. A projection that writes ten rows, receives a network error after the service has accepted them, and retries, creates twenty rows. The operator then reviews the same posting twice, and the duplicate carries no marker distinguishing it from a genuine second posting.

Determining novelty from repository-side state is sound and is not in question. The gap is what happens when a write whose outcome is unknown is retried.

Airtable offers an upsert: a write that matches on up to three fields and updates when it finds a match, creates when it does not. The schema built on 2026-09-17 carries an `Identity` field in both `Jobs` and `Jobs test`, holding the pipeline's own identity for a posting, which is unique by construction and is what the seen store keys on.

## Decision Drivers

- A retried write must not produce a duplicate row, because the operator cannot tell a duplicate from a real second posting.
- Novelty must stay a repository-side decision, so the display cannot become authoritative.
- The display is a projection and must be reconstructible.

## Assumptions

- Airtable's upsert matches on a field the caller names and is available on the records endpoint. **Sourced** from Airtable's API documentation, not exercised: nothing has written to the base yet.
- `Identity` is unique across the filtered layer. **Measured**: it is the seen store's key, and the store holds 804 entries with no collision. The dedupe key, which deliberately collapses city copies, is a different value and is not used here.

## Considered Options

- Batched creates, as ADR-0004 says, and tolerate duplicates after a failed retry.
- Batched creates, with the writer reading back to check before retrying.
- Upsert matched on `Identity`.

## Decision Outcome

Chosen option: "upsert matched on `Identity`".

**The projection upserts, matching on the `Identity` field, in batches of ten.** A retry after an unknown outcome is then safe: the second attempt matches the rows the first attempt created and updates them in place.

**This amends ADR-0004's "batched creates" and leaves the rest of it standing.** Batching, the batch size, and the direction of authority are unchanged.

**It does not strain "We will perform no reads."** An upsert is a write that matches server-side. The pipeline still learns nothing from Airtable, still decides novelty from the seen store and the filtered file, and still never treats the base as authoritative. The clause exists so that repository state is the source of truth, and it remains so.

**A consequence worth naming: the operator's own edits are at risk.** An upsert updates every field it is given. If the projection sends `Status`, a re-projection overwrites the operator's review. **The projection therefore writes only pipeline-owned fields**: Title, Employer, Location, Link, Published, First seen, Order date, Board, Matched term, Identity. `Status`, `Pipeline reason` and `Choice reason` are the operator's and are never written by the pipeline.

### Consequences

The projection becomes safely repeatable, which also makes ADR-0030's backfill safe to project.

The writer must be able to name the fields it sends, rather than sending a whole row, which is a small constraint on how the projection is built.

Any field added to the schema later must be classified as pipeline-owned or operator-owned before the writer touches it. Getting that wrong silently destroys review data, which is the worst failure available in this system.

If Airtable's upsert turns out not to be available on the plan in use, the fallback is creates plus the same field discipline, and duplicates after a failed retry become a known defect rather than a surprise.

### Confirmation

Project the same batch twice against `Jobs test`. The row count must be identical after the second run, and every pipeline-owned field unchanged.

The check that can fail: before the second projection, set `Status` on one test row by hand. After the projection, that value must still be there. If it is empty, the writer is sending operator-owned fields and the discipline above is not implemented.

## Pros and Cons of the Options

### Batched creates, tolerate duplicates

Good, because it is exactly what ADR-0004 already says and needs no change.
Bad, because the duplicate is indistinguishable from a real posting, and the operator pays for it by reviewing the same role twice.

### Creates with a read-back check

Good, because it detects the duplicate before creating it.
Bad, because it reads from Airtable, which is the clause ADR-0004 wrote to prevent the display becoming authoritative, and it doubles the call cost against a small allowance.

## More Information

Amends ADR-0004, which carries a Changes row pointing here. Answers question B of the 2026-09-17 architecture brief.

ADR-0034 decides that the writer is a separate client. The schema, including `Identity`, is recorded in `docs/reference/airtable-schema.md`.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | Two fields are classified pipeline-owned ahead of being built, so the sent set becomes twelve when they exist: `Family`, ADR-0038's label, and `Star reason`, ADR-0044's explanation. Both single line or long text, never a single select | This record requires a field added later to be classified before the writer touches it, because an upsert overwrites what it sends. Both are derived and recomputed every run, from the matched term and from the accepted store, so neither can carry a judgement of the operator's that an overwrite could destroy. A select is refused because the Airtable connector cannot add a choice to an existing field, which would make every new family a manual step. `Star reason` empty means not starred, so no checkbox can disagree with its own reason. The operator's decision, 2026-09-23 |
| 2026-09-24 | The reference to ADR-0004's line 40 annotated as line 42 | `dc02b0f` moved every record's lines down by two on 2026-09-18. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
