---
status: accepted
topic: filtering
description: The deduplication key normalises the title first, configured per source against measured evidence.
date: 2026-09-15
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0027: Deduplication key normalisation, configured per source

## Context and Problem Statement

ADR-0001 deduplicates on employer plus title plus publication date, chosen because the source registry recorded that 20 to 30 percent of harvested rows were one job posted to several cities.

The spike follow-up measured a case the registry's warning does not describe. Speechify returns 1086 postings, 68 percent of all Greenhouse volume across nine boards. Those 1086 postings are **8 job titles across 329 locations**. On all 1074 titles containing " - ", the text after the separator equals the posting's own `location` field.

The key fails on this shape. Employer matches and publication date matches, but the titles differ, because the location is inside the title. "Staff Engineer - Austin, TX" and "Staff Engineer - Berlin" are two distinct strings. One employer contributes 1086 rows where 8 are wanted.

The convention is Speechify's, not Greenhouse's. It is a choice that employer made about how to name postings, and nothing guarantees another board on the same platform does the same thing, or uses the same separator, or puts the location last.

Separately, `updated_at` cannot be used to detect that a posting changed. It was rewritten in four batches of roughly 265 postings on 24 August, 28 August, 2 September and 9 September, each drawing evenly from every publication month. Sixteen of twenty-one Careem postings share one exact second. It is stamped in bulk, not on edit.

## Decision Drivers

- One employer producing 1086 near-duplicate rows would dominate the display and defeat the pipeline's purpose.
- Fetch and parsing logic already differ per source; the sources are not uniform and pretending otherwise is what produced this defect.
- A normalisation rule that is wrong for a board is worse than none, because it merges postings that are genuinely distinct.

## Assumptions

- The " - location" convention is Speechify's alone among the boards measured. **Measured** on 11 boards: 1074 of 1086 Speechify titles match, and the pattern was not reported on any other board. Not measured on the 42 unmeasured boards.
- Two postings sharing employer, normalised title and publication date are the same job. **Stated** by the operator, consistent with the registry's multi-city finding. Not measured.
- `location` is populated wherever the convention is used. **Measured**, 100 percent on Greenhouse.

## Considered Options

- Leave the key as it is and accept the duplicates.
- Strip a trailing location from every title on every source, globally.
- Configure normalisation per source, driven by measured evidence for that source.

## Decision Outcome

Chosen option: "configure normalisation per source, driven by measured evidence".

We will normalise the title before it enters the deduplication key, and **the normalisation applied is a property of the source, not a global rule.** A board's configuration entry names which normalisations apply to it.

For Speechify, and for any board later measured to share the convention: strip a trailing separator and the text after it **only when that text equals the posting's own location field**. Never strip on the separator alone. A title genuinely containing " - " and not naming a location is left intact.

We will not apply a normalisation to a board until it has been measured on that board. An unmeasured normalisation is a guess that silently merges distinct postings.

We will record the normalised title alongside the original, never replacing it. The display shows what the employer wrote; the key uses what we derived.

**We will not use `updated_at` to detect change on any source.** It is stamped in bulk.

### Consequences

Speechify contributes 8 rows rather than 1086, which is the difference between a usable display and an unusable one. *(Annotated 2026-09-24, measured: on 2026-09-17 Speechify's postings made 11 keys, not 8, per the vertical-slice row of `logs/README.md`; the 318 Speechify postings stored on `data` at `a5abc3b` make 5.)*

Deduplication normalisation and title matching are now two separate rules on the same field. ADR-0021 governs what is admitted; this governs what is considered the same posting. They must not be merged, because admitting and deduplicating are different questions.

A per-source configuration is more work than a global rule and will grow as boards are added. That cost is accepted: the sources genuinely differ, and the alternative merges postings that are not the same.

Any board added without measurement gets no normalisation, so it fails toward duplicates rather than toward silent merges. Duplicates are visible; merges are not.

The row shape gains a field for the normalised title. This touches the normaliser, a shared component.

Change detection now has no field on Greenhouse. ADR-0018's contract check must not rely on `updated_at`, and any future need to detect an edited posting requires a different mechanism.

### Confirmation

Run the Speechify payload already in `raw_responses/` through the key and confirm it yields 8 distinct groups, not 1086 and not fewer than 8. Fewer than 8 means the normalisation is over-stripping.

Separately, give the normaliser a title containing " - " whose trailing text does **not** match the location field, and confirm it is left intact. If it is stripped, the rule is matching on the separator rather than on the location, which is the failure mode this record exists to prevent.

## Pros and Cons of the Options

### Leave the key as it is

Good, because no new field and no configuration.
Bad, because one board contributes 1086 rows of 8 jobs, and the display becomes the problem it was built to solve.

### Strip globally

Good, because it is one rule with no configuration.
Bad, because it assumes every source names postings the same way, which is the assumption that produced this defect. A board using " - " for something else would have distinct postings silently merged, and a silent merge cannot be seen in the output.

## More Information

Extends ADR-0001, whose deduplication key stands. This adds normalisation before the key is computed; it does not change what the key is made of.

Evidence is the spike follow-up of 2026-09-15, checks 1 and 2.

The `updated_at` finding bears on ADR-0018, which carries its own Changes row.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-24 | Speechify's row count annotated with its measurements | 11 keys on 2026-09-17 and 5 on 2026-09-24, where the record estimated 8. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
