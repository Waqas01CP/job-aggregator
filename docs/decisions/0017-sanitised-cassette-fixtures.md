---
status: accepted
topic: practice
description: Adapter tests run against committed real responses with every description field stripped before commit.
date: 2026-09-10
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0017: Sanitised cassettes as adapter test fixtures

## Context and Problem Statement

Adapters parse third-party board responses. Testing them requires a response to parse. Hand-written mocks miss the shapes real boards actually return, which is where parsing defects live.

The VCR pattern records a real response once to a cassette file and replays it in tests, making them offline, deterministic and fast against real response shapes. Cassettes are committed so the tests run anywhere.

ADR-0011 makes the repository public and stores metadata only, specifically excluding job description text, on the grounds that republishing employer-authored text is a different act from reading an API.

A recorded board response contains description text. That is the conflict.

## Decision Drivers

- Adapters cannot be tested against real shapes without real responses.
- ADR-0011's exclusion of description text from the public repository.
- Cassettes must be committed or tests cannot run in a clean checkout.
- The cost constraint: no paid fixture hosting.

## Assumptions

- Board responses carry description text in a small number of identifiable fields per platform. Not verified for any platform; the sanitiser will need adjusting per adapter as each is written.
- A cassette with description fields removed still exercises the parsing logic that matters, because parsers read structure rather than prose. Holds while ADR-0016 keeps matching to titles; would not hold if description matching is added.

## Considered Options

- Hand-written mocks, no cassettes.
- Cassettes committed unsanitised.
- Cassettes kept outside the repository, so tests cannot run in CI.
- Cassettes committed with description fields stripped before commit.

## Decision Outcome

Chosen option: "cassettes committed with description fields stripped before commit".

We will record one real response per platform as a cassette. We will strip description fields, replacing each with a short fixed placeholder so the field's presence and type are still exercised. We will commit the sanitised cassettes.

We will enforce this with a pre-commit guard that rejects a cassette containing an unstripped description field, because an instruction is advisory and a hook is not.

We will record the capture date on each cassette and treat a cassette older than six months as stale, to be re-recorded.

### Consequences

Adapters are testable offline, deterministically, against real structure.

ADR-0011 stands unamended. No description text reaches the public repository.

The sanitiser is per-platform work: each new adapter needs its description fields identified before its cassette can be committed.

A sanitised cassette cannot test description handling. Nothing currently needs that, and adding description matching would require revisiting both this record and ADR-0011.

Cassettes go stale silently as boards change. This is not solved here; ADR-0018 covers it.

### Confirmation

Give the pre-commit guard a cassette containing an unstripped description field and confirm it rejects the commit. A guard that has never been shown to fire is not a guard.

## Pros and Cons of the Options

### Cassettes kept outside the repository

Good, because there is nothing to sanitise.
Bad, because tests cannot run in a clean checkout or in CI, which removes most of their value.

## More Information

Related to ADR-0011, which this decision is shaped to preserve, and ADR-0018, which covers the drift that cassettes cannot detect.
