---
status: accepted
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0039: The aggregator condition is the three components

## Context and Problem Statement

ADR-0019 admitted Himalayas to the vertical slice on a condition, and states that condition twice in incompatible words.

Line 55, the criterion: "Himalayas is removed from the slice if adding it forces a change to the shared HTTP module, the normaliser's row shape, or the filter chain. Adding a configuration entry and an adapter file is not a complication; that is the model working."

Line 83, the Confirmation: "A diff touching only a config entry and a new adapter file passes. A diff touching the shared HTTP module, the normaliser, or the filter chain fails, and Himalayas leaves the slice."

The first sentence names three components and says what a complication is. The second sentence adds a narrower test: only two kinds of file may change at all. The real diff satisfied the first and failed the second. It touched none of the three named components, and it did touch `src/config.py`, to register the platform and its source class, `src/run.py`, to add a pagination loop, and `src/storage.py`, for ADR-0020's local routing.

So a record intended to trigger cleanly instead produced a contradiction, and the question of whether Himalayas stays has been open since the slice was built because of a sentence rather than because of anything measured.

## Decision Drivers

- A condition that cannot be evaluated is not a condition.
- The criterion's own sentence explains what it is protecting: a component every other source shares must not change for one source.
- The narrower sentence protects nothing additional. It forbids changes to files that necessarily change when a source needs a capability no previous source needed.
- The next aggregator will hit this again if the wording is not settled.

## Assumptions

- Pagination and source-class routing had nowhere else to live. **Measured** by reading the diff: Himalayas is the first source needing more than one request, and the loop sits in the orchestrator beside every other source's single call; the routing sits in storage because that is where paths are chosen.
- No other source was affected by those changes. **Measured**: the eleven ATS boards' behaviour is unchanged, and the suite passes.

## Considered Options

- The narrow sentence governs, so Himalayas leaves the slice.
- The three components govern, and the narrow sentence is an error.
- Re-run the condition against a redrawn diff.

## Decision Outcome

Chosen option: "the three components govern".

**The condition is, and always was: does adding a source force a change to the shared HTTP module, the normaliser's row shape, or the filter chain?** If yes, the model is wrong and the source leaves. If no, the source stays, whatever else the diff touches.

**ADR-0019's Confirmation sentence is an error**, not a second condition. It was written as shorthand for the criterion and is narrower than it in a way that makes the criterion unusable. ADR-0019 carries a dated annotation and a Changes row saying so and pointing here.

**Evaluated against the real diff, Himalayas passes.** It touched none of the three components. Changes to `src/config.py`, `src/run.py` and `src/storage.py` are the model absorbing a new capability, which is the outcome the criterion calls "the model working".

**This settles the condition and not the source.** Whether Himalayas stays on the schedule is a separate question, on entirely different grounds: on a discarded runner its rows persist nowhere. That decision is the operator's and is not made here.

*(Annotated 2026-09-17, the same day: **Himalayas stays.** This paragraph originally added "and it costs 25 of every run's 36 requests while showing the operator nothing". Both halves are withdrawn. The request count is what a run spends, not a limit: ADR-0028's ceiling is 500 and no run has exceeded 36, which is 7.2% of it, so nothing is constrained and the spend was never an argument. And the judgement that its worldwide-remote rows were worthless rested on a different corpus. Its own `locationRestrictions` field is the measurement that settles reachability, and on the saved corpus it excludes Pakistan on 74 of 91 postings and leaves 17 unstated. See ADR-0041 and `docs/reference/platform-fields.md`.)*

**The rule for the next aggregator:** a new source may add configuration, an adapter, an orchestrator capability it is the first to need, and a storage path. It may not change how every other source fetches, what shape a row has, or how a row is judged.

### Consequences

The condition can now be evaluated by reading a diff, which is what it was written for.

A source can add an orchestrator capability, which is a real loosening: pagination now sits in the orchestrator for every future source to use, and it arrived for one source.

Distinguishing "the model absorbed it" from "the model bent" is a judgement about three named files rather than a file count, which is harder to game and harder to apply carelessly.

The five remaining aggregators in ADR-0019's survey face a stated criterion.

### Confirmation

Read the diff that adds a source. If `src/http_client.py`, the normaliser's row shape, or the filter chain changed, the source fails.

The check that can fail: Himalayas' own diff must pass this test and fail the narrow one. It does, which is the case that made the contradiction visible in the first place.

## Pros and Cons of the Options

### The narrow sentence governs

Good, because it is the stricter reading and strictness is usually right in a condition.
Bad, because it removes a working source over files that must change whenever a source needs a new capability, and it contradicts the criterion the record itself wrote to explain what it was protecting.

### Re-run against a redrawn diff

Good, because it avoids ruling on the record's wording.
Bad, because it is the same evaluation with a redrawn boundary, which decides by drawing rather than by criterion.

## More Information

Resolves the contradiction in ADR-0019 lines 55 and 83, which carries a Changes row pointing here.

Whether Himalayas stays on the schedule was open when this record was written and was closed the same day: it stays. See the annotation above and ADR-0019's Changes.
