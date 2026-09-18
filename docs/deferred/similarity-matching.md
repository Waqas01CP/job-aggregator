---
type: deferred
description: Ranking postings by similarity to accepted roles. Deferred because ADR-0010 forbids it and the deterministic star was built instead; revisit when the accepted store holds fifty rows or when the operator stops reading every row.
status: current
---

# Similarity matching

**Deferred 2026-09-18.** Not rejected. Not scheduled.

## What was proposed

That an accepted role should raise the priority of later postings resembling
it, with resemblance computed rather than named: embed the accepted roles,
embed the candidate, compute a distance, order by it. Any of the usual
shapes, from cosine similarity over embeddings down to a string distance over
titles, is the same proposal at a different cost.

## Why it was not built

**ADR-0010 forbids it.** "We will perform no scoring, no ranking, and no
model-based classification of any posting. Every rule that admits or drops a
posting will be a deterministic, readable predicate whose verdict can be
explained by naming the rule." A distance cannot be explained by naming a
rule. A wrong star from a model looks like a difference of taste rather than
a defect, which is the property that makes it unfalsifiable in practice.

**ADR-0044 was built instead**, and it satisfies the want it was aimed at. A
posting is starred when it shares employer, matched pool term or role family
with an accepted row, and every star names the attribute and the accepted row
it came from.

## Why no comparison was possible

This is the honest part, and it is the reason this file exists rather than a
paragraph saying the idea was rejected.

**No accuracy comparison between the two approaches was made, because none
could be.** There is no labelled data: no set of postings marked as ones the
operator would have wanted. The accepted store is empty, so there is nothing
to compare against in either direction. A claim that the deterministic star is
as good as, or worse than, a similarity model would be invention.

What can be said is narrower and true: the deterministic version is
explainable and the model version is not, and that difference alone decided
it under ADR-0010. Whether the model would surface roles the three attributes
miss is **unknown and currently unknowable**.

## The trigger

Revisit when **either** holds.

**Fifty or more rows in the accepted store.** At that size there is enough
signal to ask whether the three named attributes are catching what the
operator actually accepts, and enough data to measure a proposed alternative
against something rather than against intuition.

**Or, and this is the real one: when the operator notices himself scrolling
past rows rather than reading them.** A star is a convenience while he reads
everything. It stops being one the moment he does not, because then the
question changes from "which of these should I look at first" to "which of
these will I never look at", and that second question is a ranking whether or
not anything is scored.

The second trigger is the one to watch. The first is a number and will arrive
on its own; the second is a change in how he uses the display, and only he
can notice it.

## What revisiting would have to produce

Not a model. A reason why the named-attribute approach is insufficient, with
the cases it missed, and then a decision in the architecture chat about
whether ADR-0010's scope floor moves. **ADR-0010 is a scope floor, not a
preference**, and this file does not weaken it. It records that a specific
proposal was measured against it, lost, and would need the floor itself
revisited rather than worked around.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | File created, the first entry in `docs/deferred/` | The proposal was live enough to need a written answer, and the answer was not "no" but "not this, not yet, and here is what would change it". Recording only ADR-0044's decision would have lost why the alternative was set aside and what would bring it back |
