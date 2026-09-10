---
status: superseded by ADR-0016
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0008: Title matching by allowlist, blocklist, and unmatched flag

## Context and Problem Statement

ADR-0005 means every posting on every board is ingested, including the finance, sales, operations and clinical roles carried by large employers in the registry. Without a title rule the display reproduces the sifting problem it exists to remove.

A pure allowlist over the target title terms produces the cleanest display but excludes any role whose title does not match a listed term. A pure blocklist misses nothing but leaves the display noisy.

The operator's governing rule is that ambiguous cases enter the display for human decision rather than being dropped by machine judgement.

## Decision Drivers

- The display must be shorter than the raw fetch or it serves no purpose.
- Ambiguity is resolved by the operator, not by the pipeline.
- ADR-0001 makes a wrong title rule recoverable, since it can be re-run over history.

## Assumptions

- Employers name equivalent roles inconsistently enough that an allowlist alone would miss real matches. Stated from the operator's experience; not measured.

## Considered Options

- Allowlist only.
- Blocklist only.
- Allowlist, blocklist, and an unmatched bucket that is still shown.

## Decision Outcome

Chosen option: "allowlist, blocklist, and an unmatched bucket that is still shown".

We will classify every posting title three ways. A title matching an allowlist term is admitted and marked matched. A title matching a blocklist term for a clearly non-engineering function is dropped with the rule recorded. A title matching neither is admitted, marked unmatched, and presented separately from matched rows.

### Consequences

Nothing is silently lost. Every posting either appears in the display or carries a recorded drop reason.

The unmatched set is visible, which is the feedback signal for extending the allowlist.

The display carries more rows than a pure allowlist would, consuming the record ceiling faster.

The blocklist is the only place machine judgement drops a row on title, so it must stay narrow.

### Confirmation

Review the unmatched bucket weekly for the first month. A role in it that should have been applied to means the allowlist needs the corresponding term.

## Pros and Cons of the Options

## More Information

Superseded by ADR-0016, which retains this classification and adds versioning of the title pool.
