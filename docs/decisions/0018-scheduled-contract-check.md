---
status: accepted
date: 2026-09-10
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0018: Scheduled contract check against live boards

## Context and Problem Statement

Every input to this pipeline is a third-party API nobody here controls. ADR-0017's cassette tests are closed-world: they replay a recorded response and keep passing after the live board has changed.

The failure modes that follow do not raise errors. A field starts returning null rather than disappearing. A type changes silently, so a cast produces a wrong value instead of an exception. A new enum value appears that no branch handles. In each case the run completes, the tests pass, and the output is quietly wrong or empty.

Consumer-driven contract testing, meaning Pact and its relatives, requires the provider to adopt the framework. Confirmed across several independent sources that it cannot help with an API you do not control.

The applicable pattern for a consumed third-party API is observed contract verification: infer the response's structural shape from real responses, fingerprint it, and compare on a schedule.

Existing tooling for this is paid SaaS, surveyed at roughly $50 to $2,500 a month.

## Decision Drivers

- Cassette tests cannot detect a change in the live board.
- Per-source row counts, already logged, show that something broke but not what.
- Cost constraint: free by default. Build rather than subscribe where the build is small.
- A silent zero from a board is indistinguishable from a quiet market without this.

## Assumptions

- Board responses are stable enough that a key-set fingerprint changes rarely, so an alert means something real. Not measured; if fingerprints churn the check becomes noise and the fingerprint must be narrowed to consumed fields only.
- The fields each adapter consumes are a small subset of what a board returns. True by construction under the Tolerant Reader rule below.

## Considered Options

- Nothing beyond per-source row counts.
- A paid drift-monitoring service.
- Consumer-driven contract testing.
- A self-built scheduled fingerprint comparison.

## Decision Outcome

Chosen option: "a self-built scheduled fingerprint comparison".

We will fetch one real response per platform on a schedule, separate from the pipeline run. We will compute a fingerprint over the fields each adapter actually consumes, recording for each its presence, its type, and whether it was null. We will store the fingerprint on the data branch and compare it against the previous one on every check.

We will report a change loudly, naming the field and how it changed, rather than emitting a pass or fail.

We will apply the Tolerant Reader rule in every adapter: read only the fields consumed, ignore everything else, so additive changes on a board's side never break anything.

This check runs on a schedule, not on commit. It fails when the world changes, not when the code changes, so it is not part of the test suite.

### Consequences

The three silent failure modes above become visible, each naming its field.

A dead adapter is distinguishable from a quiet market, which per-source counts alone could not do.

The check costs one request per platform per run and nothing else. No vendor, no subscription.

A fingerprint over consumed fields only means a board can add or change fields the pipeline ignores without raising anything, which is intended.

The first run of any platform produces a baseline and no verdict. Only the second run onward can detect change.

False alarms are possible if a board's optional fields populate inconsistently across postings. Mitigation is to fingerprint across several postings per platform rather than one, which has not been sized.

### Confirmation

Hand-edit a stored fingerprint to remove a field, run the check, and confirm it reports that field by name. A check that has never been shown to fire is not a check.

## Pros and Cons of the Options

### A paid drift-monitoring service

Good, because it is maintained by someone else.
Bad, because the cheapest surveyed option costs more per month than the entire project has ever spent.
Bad, because most operate on published OpenAPI specifications, which these boards do not provide.

### Consumer-driven contract testing

Bad, because it requires the provider to participate. Not applicable.

## More Information

Complements ADR-0017: cassettes verify the parser against a known shape, this verifies the shape against reality. Neither substitutes for the other.
