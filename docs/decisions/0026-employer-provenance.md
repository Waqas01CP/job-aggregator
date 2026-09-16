---
status: accepted
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0026: Employer provenance where a payload does not carry it

## Context and Problem Statement

ADR-0019 states that employer is read from the response payload in every case and never derived from the configuration entry. That rule exists so one configuration model can serve both source shapes: an ATS slug returns one employer, an aggregator endpoint returns many, and nothing downstream needs to know which.

The endpoint spike found the rule unfollowable for Lever. Every key on all 48 postings across both boards was enumerated: `additional`, `additionalPlain`, `applyUrl`, `categories`, `country`, `createdAt`, `description`, `descriptionBody`, `descriptionBodyPlain`, `descriptionPlain`, `hostedUrl`, `id`, `lists`, `opening`, `openingPlain`, `salaryRange`, `text`, `workplaceType`, and on one Spreetail posting also `salaryDescription` and `salaryDescriptionPlain`. Twenty keys in total. No key contains `compan`, `employ` or `org`. The field does not exist; it is not merely sparse.

The employer is recoverable. It is the configuration slug, and it appears in `hostedUrl` on 48 of 48 postings. So the rule fails not because the information is absent but because it arrives by derivation rather than by return.

**The real problem is not correctness of the derivation. It is form.** Derivation yields a slug, not a name. `smart-working-solutions`, where Greenhouse returns `company_name` as "Veeam Software" and Himalayas returns `companyName` as "micro1". ADR-0001's deduplication key is employer plus title plus publication date, compared as strings. A slug will never match a name.

No free source carries Lever's postings with employers attached. Research pass 0003 established that Arbeitnow aggregates Greenhouse, SmartRecruiters, Join, Team Tailor, Recruitee and Comeet. Lever is not among them.

## Decision Drivers

- Lever is a major ATS and dropping it over a missing field would be a large coverage loss for a small cause.
- Deduplication compares employer strings, so a slug and a name must never be compared as though equivalent.
- A derived value and a returned value have different reliability and must not look the same downstream.

## Assumptions

- The configuration slug is the employer for every Lever board. **Measured on 2 boards and 48 postings, where `hostedUrl` contained the slug on 48 of 48.** Untested on any other Lever board.
- Slug-to-name expansion is unambiguous for these two boards. **Operator-stated, not measured.** `smart-working-solutions` expanding to "Smart Working Solutions" is a guess about capitalisation and word boundaries, and a board slug could be an abbreviation that does not expand at all.
- No free source carries Lever postings with employer names. **Sourced**, from research pass 0003.

## Considered Options

- Drop Lever from the source list.
- Derive the employer silently, so it looks like a returned value.
- Derive with a recorded provenance, and expand to a name through the alias map.

## Decision Outcome

Chosen option: "derive with a recorded provenance, and expand through the alias map".

We will derive the employer from the configuration slug where the payload carries no employer field.

We will record **how** every employer value was obtained, on every row, as one of `payload`, `envelope`, `slug`, `url`, or `constructed`. A derived employer is never indistinguishable from a returned one.

We will record provenance on the canonical URL by the same enum, for the same reason. SmartRecruiters returns no human-facing URL: its `ref` is an absolute API address and the careers URL must be built from `id`. A constructed URL and a returned one carry different risk, and ADR-0011 stores a canonical URL with no provenance concept at all.

Provenance is recorded for these two fields and no others. Generalising it to every derived field would mean recording provenance on things nobody questions.

We will expand a derived slug to a display name through the employer alias map that ADR-0019 already requires for cross-source deduplication, and we will record when no alias entry exists rather than guessing an expansion.

**A derived employer with no alias entry does not participate in cross-source deduplication.** It deduplicates within its own source, where the slug is consistent, and is held out of comparison against returned names until an alias exists. Comparing a guessed expansion against a real name would produce silent false negatives, which is worse than a duplicate row the operator can see.

### Consequences

Lever stays in the source list. Coverage is preserved.

Every row carries the reliability of its own employer field, so a later defect in deduplication can be traced to derivation rather than guessed at.

The alias map becomes required earlier than ADR-0019 anticipated. It was needed once a second source class existed; it is now needed for the first Lever adapter.

Cross-source deduplication is incomplete for derived employers until their aliases are written. This produces duplicate rows rather than lost rows, which is the correct direction to fail.

The row shape gains a field. This touches the normaliser, which is a shared component, so it is the kind of change ADR-0019's Himalayas condition would have flagged had it arisen there.

One clause of ADR-0019 no longer holds as written.

### Confirmation

Fetch one Lever posting and one Greenhouse posting and print both employer values with their provenance. The Lever row must read `slug` and the Greenhouse row must read `payload`. A Lever row reading `payload` means the derivation is being laundered as a return, and the decision has failed in implementation.

Separately, give the deduplicator a derived slug and a returned name for the same employer with no alias entry present, and confirm it does not match them. If it matches, it matched on a guess.

## Pros and Cons of the Options

### Drop Lever

Good, because it needs no new field and no alias entries.
Bad, because it removes a major ATS over one missing key, when the information is present and recoverable on 48 of 48 postings.

### Derive silently

Good, because nothing downstream changes.
Bad, because a slug would then be compared against returned names as though equivalent, producing silent false negatives in deduplication with no way to trace them.

## More Information

Reverses one clause of ADR-0019: that employer is read from the payload in every case and never derived. The rest of ADR-0019 stands, including the reason that clause was written, which is that one configuration model must serve both source shapes. Provenance is what preserves that while allowing derivation.

Evidence is the endpoint feasibility spike of 2026-09-11, whose full key enumeration for Lever is the basis for the claim that no employer field exists.

Lever's `createdAt` semantics remain untested and are a separate open question. This record does not settle whether Lever stays in the vertical slice.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-15 | The key enumeration listed 18 keys and called them "every key." There are 20 | `salaryDescription` and `salaryDescriptionPlain` appear on one Spreetail posting and were missed by the first spike, whose report this record copied. The conclusion is unchanged: neither new key contains compan, employ or org, so no employer field exists. But an enumeration described as complete was not, and the corrected list is now here |
| 2026-09-16 | The provenance enum gains `envelope` and `constructed`, and now covers the canonical URL as well as the employer | Two shapes were uncovered. Workable returns the employer in the response envelope rather than on the posting, which is neither a per-row field nor a slug derivation and is more reliable than either. SmartRecruiters returns no human-facing URL at all, so the careers address must be constructed from `id`. Extending the enum and the field set once is better than touching the normaliser, a shared component, twice for one class of problem |
