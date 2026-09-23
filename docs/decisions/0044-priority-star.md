---
status: accepted
topic: display
description: A posting is starred when it shares one of three named attributes with an accepted role. The deterministic answer to "show me more like this", and the line it must not cross.
date: 2026-09-18
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0044: The priority star, and the line it must not cross

## Context and Problem Statement

The operator wants an accepted role to raise the priority of later postings that resemble it. The want is reasonable and the obvious implementation is banned.

ADR-0010: "We will perform no scoring, no ranking, and no model-based classification of any posting. Every rule that admits or drops a posting will be a deterministic, readable predicate whose verdict can be explained by naming the rule."

"Resembles" is the word that does the damage. Embed the accepted roles, embed the candidate, compute a distance, sort by it: that is a relevance model, it cannot be explained by naming a rule, and it is precisely what the scope floor exists to keep out. It would also arrive looking helpful, which is why the line needs to be in a record rather than in someone's memory.

The question is whether the want survives without the model. It does, because what the operator actually means by "resembles" turns out to be nameable.

## Decision Drivers

- The want is real: a second role at an employer he applied to is worth seeing first.
- Every star must be explainable by naming the attribute that produced it, which is ADR-0010's own test.
- The next session will see the naive version and think it a small extension, unless the line is written down with the reason.
- A star must never remove a row, or it becomes a filter nobody decided on.

## Assumptions

- The three named attributes capture most of what the operator means by resemblance. **Not measured**, and cannot be until the accepted store has rows. If it turns out to be wrong, the fix is a fourth named attribute, not a model.
- The accepted store will be small. **Sourced** from the operator applying by hand; a comparison against every accepted row on every projection is cheap at tens of rows and would need revisiting at thousands.

## Considered Options

- Similarity over titles or descriptions, by embedding or by string distance.
- Shared named attributes, compared for equality.
- Nothing; leave the display ordered by date alone.

## Decision Outcome

Chosen option: "shared named attributes".

**A posting is starred when it shares any of three named attributes with a row in the accepted store:**

- **employer**, compared after the same folding titles get;
- **matched term**, the pool term that admitted it, recomputed from the title with the same matcher the chain used;
- **role family**, the heading that term sits under in the pool, per ADR-0038.

**Every star names its attribute, its value, and the accepted row it came from.** The test is that a star can be read aloud: "starred because employer matches accepted row N". A star that cannot be said that way did not come from a named attribute, and is out of scope.

**The line, stated so it can be enforced rather than remembered:**

- **No score.** No number attaches to a posting.
- **No distance**, string or vector, and **no embedding**.
- **No ranking of stars.** Two stars do not beat one. A count used as an order is a score wearing a different hat, and ADR-0038 already records that ordering by a derived number is the shape a ranking arrives in.
- **A row is starred or it is not**, and the display still orders by date within a view, per ADR-0010.

**A star never drops anything.** It is a display annotation over rows the chain already admitted. A posting resembling nothing accepted appears exactly as it does today.

**A row never stars itself**, or projecting the accepted store would star every row in it for resembling itself.

**A missing employer never matches another missing employer.** Two rows with no employer are not at the same company, and before ADR-0026's derivation runs, Lever rows have none.

### Consequences

The operator sees a marked row for a second opening at an employer he applied to, for another role admitted by the same term, and for a role in the same family. Those are the three cases he described, and they are the three the system can name.

The star depends on the accepted store, so ADR-0043 must land first and the display must exist before either does anything.

Role family required a term-to-family map, which did not exist: `load_title_pool` read the pool's four headings and discarded them. It is now built, which also delivers the label ADR-0038 needs.

A fourth attribute is a decision, not a refactor, because it widens what resemblance means. The attribute list is a single tuple and a test asserts its contents, so widening it cannot pass unnoticed.

Comparing every candidate against every accepted row is quadratic. At the sizes involved that is irrelevant, and it is recorded so that the first response to it being slow is not to reach for an index built on a distance.

### Confirmation

Every star must be explainable by naming its attribute. The check is a function that renders each reason as a sentence, and a test asserts each one names the attribute and the accepted row.

**The check that can fail, and the one that matters:** a posting that a similarity model would obviously star, sharing none of the three attributes, must not be starred. "Machine Learning Engineer at Motive" accepted, "Backend Engineer at Veeam" offered: different employer, different term, different family, no star. If that ever starts starring, something is comparing text rather than attributes.

A second: two runs over the same data must produce identical reasons in identical order, so the output is deterministic rather than dependent on store order.

## Pros and Cons of the Options

### Similarity over titles or descriptions

Good, because it would catch resemblance the three attributes miss, which certainly exists.
Bad, because it is a relevance model, ADR-0010 forbids it, and no star it produced could be explained by naming a rule. It would also be unfalsifiable in practice: a wrong star looks like a taste difference rather than a defect.

### Nothing at all

Good, because the display stays simple and ordered by date.
Bad, because the operator loses a signal the data already carries, and the three attributes are already recorded on every row.

## More Information

The boundary is the point of this record. ADR-0010 is the scope floor; ADR-0038 sets the same boundary for role families and is the precedent this follows.

ADR-0043 owns the accepted store. `src/star.py` implements it, and `src/filters.py` gained `load_term_families` for the family attribute.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | The star's home is named: a pipeline-owned `Star reason` field on `Jobs`, long text, empty meaning not starred | ADR-0035 requires a new field to be classified before the writer sends it. The star is derived from three named attributes against the accepted store and is recomputed every run. One field rather than a checkbox plus a reason, so the mark and its explanation cannot disagree. The field waits on the accepted store, which waits on the sweep. The operator's decision, 2026-09-23 |
