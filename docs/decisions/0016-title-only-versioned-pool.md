---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0016: Title-only matching against a versioned title pool

## Context and Problem Statement

ADR-0008 established three-way title classification but treated the title terms as a fixed list embedded in the filter.

Two things make that insufficient.

The operator's manual process searches the full posting text, not just the title. Typing "agentic" into a site's search box matches a description. A role titled "Software Engineer" whose description describes building agentic systems is caught by the manual process and missed by title matching. Adding description matching requires fetching descriptions, which is a separate call on some platforms, and would produce weaker matches in greater volume.

The title terms will change. They are built around the operator's capabilities and intended direction, both of which move. A term added in November changes what a re-filter over October's raw rows produces, and an undated list makes that re-filter irreproducible.

## Decision Drivers

- ADR-0011 stores metadata only on the public data branch, so storing descriptions there would require revisiting that decision.
- The raw layer already stores every field a board returns, so the data needed for description matching accumulates whether or not it is used.
- A filter whose configuration is not versioned cannot be replayed over history.

## Assumptions

- Title matching alone will miss some suitable roles. Certain in principle; the rate is unknown and is what the unmatched bucket and `rejected_pipeline` outcomes will reveal.
- Which platforms return descriptions in the list call, and which require a second call, is unknown. Not verified for any platform.

## Considered Options

- Title matching only, fixed term list.
- Title matching only, versioned term pool.
- Title and description matching from the start.

## Decision Outcome

Chosen option: "title matching only, versioned term pool".

We will match on title only. We will store every field each board returns in the raw layer regardless of whether a filter uses it, and we will report field coverage per platform in the run log so it is later known which platforms carry descriptions and by what mechanism.

We will keep the title pool in a versioned file with dated changes, so any historical filter run can be reproduced.

We will treat the unmatched bucket, retained from ADR-0008 and restated in this record, as the mechanism for extending the pool: a role appearing there that should have been applied to identifies a missing term.

Description matching is deferred, not rejected. It is revisited once field coverage per platform is known.

### Consequences

The filter stays cheap and every match is explainable by naming a term.

Some suitable roles are missed. The unmatched bucket and the `rejected_pipeline` outcome reasons are the only signals that will show this, so both must be reviewed rather than merely recorded.

Field coverage reporting costs nothing at logging time and answers the description-matching question before it is asked.

A versioned pool means re-filtering over history is reproducible, which is what ADR-0001 promised.

Adding description matching later would require revisiting ADR-0011, since descriptions cannot go on the public data branch.

### Confirmation

Review the unmatched bucket weekly for the first month. A role in it worth applying to means a missing term, and the term is added with the date. Field coverage per platform appears in the run log from the first run.

## Pros and Cons of the Options

### Title and description matching from the start

Good, because it matches the operator's manual process exactly.
Bad, because it requires a second fetch per posting on an unknown number of platforms.
Bad, because it conflicts with ADR-0011 unless descriptions are held only in the display layer.
Bad, because it produces more weak matches before any evidence exists that title matching is insufficient.

## More Information

Extends ADR-0008, whose allowlist, blocklist and unmatched-flagged classification is carried forward unchanged and is the mechanism this record depends on for extending the pool.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-10 | Said it superseded ADR-0008, now says it extends it | It reverses nothing in ADR-0008. Claiming supersession would have retired the classification this record itself depends on |
