---
status: accepted
topic: measurement
description: Two measures, freshness at discovery and outcome, with only the pipeline-controlled one binding. When the assessment window opens.
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

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | Go-live, for Measure A's two-week window, is the first row in Airtable | This record measures publication date to first appearance in the display. The data branch is not the display: a row on it is invisible to the operator. The window starts when a row is visible to him, which also makes ADR-0009's slice Confirmation and this window start together |
| 2026-09-17 | Rows appended by a backfill are excluded from Measure A | ADR-0030 appends rows for postings first seen long before the rules that now admit them. This record already excludes postings published before the pipeline's first successful run against their board, for the same reason. Without the exclusion a backfill would make freshness look catastrophic while nothing had got worse |
| 2026-09-25 | ADR-0048 named as changing how Measure A is read | ADR-0048 says "ADR-0015 owns Measure A, whose interpretation this changes"; the corpus audit found this record did not name it. Annotated by the implementing seat under ADR-RULES, on Brief 7's corpus work; the Decision Outcome is untouched. |
| 2026-10-16 | Measure A assessed at two weeks: **met**, so the protocol's three steps do not fire and the schedule stays on. Over 2026-09-24T03:27Z to 2026-10-08T03:27Z, 140 admitted postings: median 7.3 hours and 90th percentile 22.0, against 24 and 72. Himalayas 137 at 7.3 and 21.8, Lever 2 at 34.8 and 49.5, Greenhouse 1 at 6.6. First appearance is taken as the row's first-seen time, the start of the run that admitted it, a minute or two before that run's projection writes the row. The 26 admitted postings published before their board's first successful run are excluded as backfill, and no run in the window backfilled a row. Coverage was every admitted row in the window. After the window it falls: from 2026-10-08 evening Manatal's rows carry no date, 9 of the 36 admitted to 2026-10-15, and each later reading reports its coverage | Measured by the implementing seat from the run logs on `data` and the private repository, its report on Brief 11, item 5, checked by the chat on 2026-10-16. Due about 2026-10-08 and missed by the chat (its ledger, item 107). Read with two limits the seat named: Himalayas was polled on the morning run only until 2026-10-04, most of the window, and the meaning of Lever's `createdAt` is unconfirmed, its two rows being the window's slowest. The window over which Measure A must keep holding for version 1.0.0 is the operator's to set (the version file) |
