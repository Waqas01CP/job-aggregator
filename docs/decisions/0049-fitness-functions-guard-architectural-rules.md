---
status: accepted
topic: practice
description: Every architectural rule that code can break silently gets a test that fails when it is broken, named for the record it guards and proved by a mutation.
date: 2026-09-25
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0049: Architectural rules are guarded by fitness functions, not by prose

## Context and Problem Statement

This corpus states rules that code can violate without any test failing. ADR-0035 forbids the pipeline from sending `Status`, and the cost of breaking it is the operator's review data. ADR-0010 forbids scoring, and a violation would arrive looking like an improvement. ADR-0027 requires deduplication normalisation and title matching to stay two rules, and an implementation audit on 2026-09-24 could not tell from the code whether they had been merged; the architecture chat had to measure 345 rows by hand on 2026-09-25 to answer it.

Three things follow from a rule that lives only in prose. A seat that has not read the record cannot obey it. A violation is invisible until it destroys something. And the check, when someone finally runs it, is run once by hand and never again.

Two guards of this kind already exist here and were built one at a time without a name: `tools/preference_audit.py`, which proves that no module hard-codes a preference for ADR-0031, and the test asserting the ten fields the writer sends for ADR-0035.

The practice has a name in published work. An **architectural fitness function** is an objective test of an architectural characteristic, run continuously with the rest of the suite rather than at review time.

## Decision Drivers

- A rule outlives the session that wrote it, and the next seat may never open the record.
- The most expensive rules here are the ones whose violation is silent.
- The project already rejects a check that cannot fail, so a guard must be provable.
- The operator asked for tests that sit in the suite and warn when a worry becomes real.

## Assumptions

- The practice is established rather than invented here. **Sourced** from *Building Evolutionary Architectures* by Ford, Parsons and Kua, chapter 2, and Thoughtworks' "Fitness function-driven development", both read 2026-09-25. Not adapted from any single vendor's tooling.
- Suite runtime is not a constraint at this size. **Measured**: 542 tests run in CI on 2026-09-24 without a timeout concern.
- A guard in the ordinary suite is run; one in a separate suite is not. **Stated** by the operator, 2026-09-25, and the reason he asked whether a separate category was wise.

## Considered Options

- Prose rules only, audited by a seat when someone remembers.
- A separate "future tests" suite, run when convenient.
- Fitness functions in the ordinary suite, each naming the record it guards.
- A periodic audit seat instead of tests.

## Decision Outcome

Chosen option: "fitness functions in the ordinary suite, each naming the record it guards".

**Every architectural rule that code can break silently gets a fitness function.** The test asserts the property, not an example of it: over the whole stored corpus where that is possible, rather than over one hand-made case.

**Each one names its record and clause in its docstring**, so a later seat reading the test knows what it protects, and a seat retiring a rule can find the guard.

**Each one is proved by a mutation that makes it fail**, recorded with the others in `tools/mutations/`. An unproved fitness function is a check that cannot fail, which this project already treats as worse than none.

**They live in the ordinary suite and are never skipped, marked slow, or moved to a separate run.** A separate category is the failure mode this decision exists to avoid.

**A property that can only be checked against live data is enforced at the boundary that touches it**, not in the suite. ADR-0020's rule that no aggregator row reaches the public branch is enforced by the commit guard in `src/run.py`, and that guard is a fitness function by this record's definition.

**When a rule is retired, its fitness function is deleted in the same change.** A guard for a rule nobody holds any more teaches a false rule.

**The first three, in order:**

1. **ADR-0027's normalisation invariant.** For every row in the stored filtered layer, matching the raw title and matching the normalised title must produce the same verdict, the same term and the same family. Measured true over 345 rows on 2026-09-25; the test makes that permanent, and it fails the day a per-source normalisation strips text a pool term needs.
2. **ADR-0031's preference rule.** `tools/preference_audit.py` already does this and becomes a fitness function by name, run in the suite rather than by hand.
3. **ADR-0035's field ownership.** The existing ten-field assertion, restated as a property: the writer sends only pipeline-owned fields, whatever the schema gains later.

### Consequences

The suite grows by one test per rule worth guarding, and each is cheap because the data is already loaded.

A failing fitness function blocks a commit. That is the point, and it will one day block a change the seat believes is correct; the record it names is then the thing to read, and the architecture chat decides.

The corpus gains a second way to be read: from a test back to the rule. A reader who finds a fitness function knows the rule is live, which prose alone cannot tell them.

Some rules cannot be guarded this way, because they are about judgement rather than mechanism. ADR-0010's ban on scoring can be partly guarded by asserting that no row carries a number, but not wholly, and this record does not pretend otherwise.

A guard for a rule that later changes becomes a false guard unless it is deleted with the rule, which is one more thing to remember at retirement.

### Confirmation

**Each fitness function has a mutation that makes it fail**, in `tools/mutations/`, and the mutation is named in the test's docstring.

**A meta-test asserts that every fitness function names a record that exists** in `docs/decisions/`. It fails when a record is renumbered or retired and its guard is left behind.

**The check that can fail for the first one:** add a per-source normalisation that strips a word a pool term needs, and ADR-0027's fitness function must fail. If it passes, it is asserting something other than the property.

## Pros and Cons of the Options

### Prose rules only

Good, because it costs nothing to write.
Bad, because it has already failed here: an audit had to ask whether two rules had been merged, and only a hand measurement could answer.

### A separate "future tests" suite

Good, because it keeps a slow or speculative check out of the fast loop.
Bad, because a suite nobody runs rots, and its failures are discovered long after the change that caused them. The operator raised this shape himself and the objection is his to own.

### A periodic audit seat

Good, because a reader can judge intent, which a test cannot.
Bad, because it is expensive, irregular, and finds a violation after it has been built on. It stays valuable for what tests cannot check, which is why it is not replaced by this record.

## More Information

ADR-0031's audit tool and ADR-0035's field test are the two that existed before this record named the practice. ADR-0027 is the rule whose ambiguity produced it. ADR-0020's commit guard is named here as one, to stop it being read as a one-off.

Sources: *Building Evolutionary Architectures*, Ford, Parsons and Kua, O'Reilly, chapter 2, "Fitness Functions"; Thoughtworks, "Fitness function-driven development". Read 2026-09-25. The project's own rule that a check must be provable comes from `CLAUDE.md` and predates both.

The operator asked for this practice on 2026-09-25 after the ADR-0027 measurement, and asked whether it was an established principle. It is, and his instinct to keep the guards permanent rather than to re-measure by hand is what this record makes standing practice.

## Changes
