---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0015: Two measures, and the archive protocol

## Context and Problem Statement

The project's original falsifier was a single number: the median gap between a posting's publication date and the operator's application date, required to be under 48 hours, failing which the build would be archived without iteration.

That metric spans two segments with different owners. Publication to first appearance in the display is the pipeline's. First appearance to application is the operator's. The operator states that applying two to five days after finding a posting is normal and is not the problem being solved. A single metric therefore fails the pipeline for latency the pipeline does not control and the operator does not care about.

The operator states two problems: the overhead of searching many sites by hand, and encountering postings already two to four days old, sometimes a week or more.

Archiving without iteration was written to prevent sunk-cost tinkering. Against a larger build it discards a sound architecture over one number.

## Decision Drivers

- The measure must isolate what the pipeline controls.
- The bar must be capable of failing, or it is not a falsifier.
- The protection against sunk-cost tinkering must survive whatever replaces the archive rule.

## Assumptions

- Postings currently reach the operator at a median age of three to six days, ranging from 24 hours to three weeks. Stated by the operator; not measured, and no retrospective measurement is possible because the Application Log records application dates, not discovery dates.
- The gap between that stated baseline and the pipeline's expected performance is large enough that baseline imprecision does not affect the verdict.

## Considered Options

- Keep the single publication-to-application metric.
- Split into two measures, both binding.
- Split into two measures, with only the pipeline-controlled one binding.

## Decision Outcome

Chosen option: "two measures, with only the pipeline-controlled one binding".

**Measure A, freshness at discovery, binding.** Publication date to first appearance in the display. Median at or under 24 hours, 90th percentile at or under 72 hours. Postings whose publication date precedes the pipeline's first successful run against their board are excluded as backfill.

**Measure B, search overhead, reported not binding.** Hours per week spent on job discovery, including time spent reading the display. A poor result here means the display needs a better view, not that the build was wrong.

We will assess against Measure A two weeks after go-live. When Measure A fails, three things happen in order:

The schedule is disabled. Not informally paused.

A written assessment is produced against the architecture: which segment failed, which record's Assumptions turned out false, and whether the fault lies in a decision or in an implementation of a sound decision.

One of three outcomes is chosen: archive; a targeted change to a named component with a new falsifier and a fresh two-week window; or rebuild from the architecture, retaining decisions that survived assessment.

Only one such reassessment is permitted. If Measure A fails a second time, the project is archived.

### Consequences

The pipeline is judged on what it controls. Operator latency no longer fires the protocol.

The 90th percentile does the real work. With twice-daily polling the median cannot exceed 12 hours unless something is broken, so the percentile is what catches a late-publishing board or a silently stopped adapter.

Backfill exclusion means Measure A produces no verdict until postings published after go-live accumulate, which is why the two-week window exists.

The one-reassessment limit preserves the original rule's protection. Without it, "assess whether to change it" becomes indefinite tinkering.

Measure A depends on publication dates, which some platforms do not expose. Coverage of the measure is itself reported, per ADR-0007.

Measure B has no precise baseline and will not get one. Its value is directional.

### Confirmation

Measure A is computable from the filtered layer alone: publication date and first-seen timestamp are both recorded there. Confirm at the end of week one that the measure computes and that its coverage, the share of rows carrying a real publication date, is reported alongside it.

## Pros and Cons of the Options

## More Information

Replaces the original falsifier from the project brief. The retrospective baseline exercise over the fifteen-row Application Log is abandoned: that log records application dates and was built to prevent reapplication and track follow-ups, so it never held discovery dates and cannot be made to yield them.
