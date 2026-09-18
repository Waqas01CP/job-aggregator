---
status: accepted
topic: filtering
description: Admission is allowlist-only with normalisation, and everything unmatched is dropped and logged. The matching rules themselves.
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0021: Allowlist-only title matching, with normalisation

## Context and Problem Statement

ADR-0008 classified every posting title three ways: allowlist terms admitted and marked matched, blocklist terms dropped, and titles matching neither admitted, marked unmatched, and shown separately. The unmatched bucket existed so that a role with an unusual title would never be silently lost.

Two things about that have since become clear.

The unmatched bucket duplicates a safety net that already exists elsewhere. ADR-0001 stores every fetched posting raw and permanently. A role missed by a narrow allowlist is still on disk, and widening the allowlist and re-running recovers it. The bucket was providing that same protection a second time, in the display, which is the one place where volume is the problem the project exists to solve.

Polling large employers returns their entire boards. Careem, S&P Global and EY carry hundreds of finance, sales and operations roles. Under three-way classification every one of those lands in the display as unmatched.

The blocklist existed only to clean up that bucket. With the bucket gone it has nothing to do: an Accountant title simply never matches an allowlist term.

Separately, matching raw title strings misses obvious variants. "AI-Agent Engineer" and "AI Agent Engineer" are the same role. So are "Agentic Systems Engineer" and "Agentic System Engineer". Adding a term per variant does not scale and obscures which term did the matching.

## Decision Drivers

- The display must be shorter than the raw fetch or it serves no purpose.
- Nothing may be permanently lost, which ADR-0001 already guarantees.
- Every admitted row must be explainable by naming one term, per ADR-0010.
- Variants differing only in punctuation or plurality must not require separate terms.

## Assumptions

- The drop log is read often enough to catch a term that should have been in the pool. Not established; it is a habit, not a mechanism, and this is the weakest point in the decision.
- Employers name target roles closely enough to the 52 stems that a two-word minimum does not miss whole categories. Not measured.
- Word-boundary matching with an optional plural suffix covers the real variant space. Verified against constructed cases only, not against live board data.

## Considered Options

- Keep the three-way classification from ADR-0008.
- Allowlist and blocklist, drop everything matching neither.
- Allowlist only, drop everything else, with normalisation.

## Decision Outcome

Chosen option: "allowlist only, drop everything else, with normalisation".

We will admit a posting only if its normalised title matches a term in the title pool. Everything else is dropped, with the title recorded in the drop log.

We will maintain no blocklist. It is unnecessary once unmatched rows are dropped. *(Annotated 2026-09-17: **reversed in one respect by ADR-0032**, which adds a seniority rule the operator owns. This sentence was written about ADR-0008's unmatched bucket, which this record removed, and not about seniority. What it still forbids stands: a list that deletes rows on a machine's judgement of category. ADR-0031 records why an operator-owned word list in a versioned file is configuration rather than that. See Changes.)*

We will normalise the title and every term identically before matching: lowercase, replace hyphens, dashes, underscores and slashes with spaces, delete commas, parentheses, periods and colons, collapse whitespace.

We will match on word boundaries, never raw substring, because substring matching turns "storage" into a RAG match.

We will append an optional plural suffix to the end of a term when compiling its pattern, so a singular term matches its plural. Nothing is stripped from a word at either end.

We will require terms to be at least two words, excepting eight distinctive single tokens named in the title pool. `ai` and `rag` never stand alone.

We will use no stemming algorithm. Spelling and plural variants that are idiomatic are listed explicitly.

We will keep the pool in `docs/reference/title-pool.md`, versioned, with every change dated, so a historical filter run is reproducible.

### Consequences

The display carries only postings matching a named term, which is the reduction the project exists to produce.

The drop log becomes the sole feedback signal for a missing term. ADR-0005 already requires every drop to record its rule, so titles dropped on this rule are recorded with their titles. Reading that log is now load-bearing rather than optional.

A role with a genuinely unusual title is not seen until the pool is widened. It is not lost: it is in the raw layer, and re-running recovers it.

One term now covers a family. `agentic system` catches System and Systems, Engineer and Architect, hyphenated or not.

Word-boundary matching removes the substring collision class entirely.

The pool is a versioned file rather than a constant in code, so changing it is a documented act.

Normalisation runs on every title on every run. At these volumes the cost is negligible.

### Confirmation

Before the filter runs against live data, run the pool against a constructed case set that must include: `AI-Agent Engineer`, `Agentic Systems Engineer`, `Storage Engineer`, `Senior Red Team Operator`, `Accounts Officer`, `Sales Executive – Healthcare IT`, `Software Engineer II`, and `Non-AI Systems Analyst`. The first two must match, the next five must not, and the last is the one to watch.

A pool that matches everything, or matches nothing, has not been tested. Each case must be shown to produce the expected verdict, with the matching term named.

## Pros and Cons of the Options

### Keep the three-way classification

Good, because an unusual title is seen rather than dropped.
Bad, because the unmatched bucket fills with the finance and operations roles of every large employer polled, reproducing the problem the project exists to solve.
Bad, because it duplicates a safety net ADR-0001 already provides more completely.

### Allowlist and blocklist, drop the rest

Bad, because the blocklist has nothing left to do once unmatched rows are dropped, and it is the only place where a machine would delete a row on a judgement rather than on a named match.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | The no-blocklist clause is reversed in one respect | ADR-0032 adds a seniority rule the operator owns, and ADR-0031 records why a versioned preference file is configuration rather than the machine judgement this clause forbids. The clause was written about ADR-0008's unmatched bucket, which this record removed, not about seniority |
| 2026-09-17 | The Confirmation case set is re-run, not replaced | Run against the current chain on 2026-09-17: all eight cases produce the verdict this record requires. 'Software Engineer II' is still not admitted, but the mechanism changed, since the pool now matches it and the seniority rule drops it. 'Non-AI Systems Analyst' is admitted by 'ai system', which this record named as the one to watch, and it is a live false positive |

## More Information

Supersedes ADR-0008. The three-way classification is replaced by a different approach to the same question, and more than half of ADR-0008's Decision Outcome no longer holds.

Reverses one clause of ADR-0016, which named the unmatched bucket as the mechanism for extending the pool. That mechanism is now the drop log. The rest of ADR-0016 stands: title-only matching, storing every field a board returns, a versioned pool, and the deferral of description matching.

The pool itself: `docs/reference/title-pool.md`.
