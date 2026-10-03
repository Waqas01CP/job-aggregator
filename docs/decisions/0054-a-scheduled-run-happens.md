---
status: accepted
topic: fetching
description: A run that should happen, happens. Runs queue rather than cancel each other, up to GitHub's hundred, and the sixty-day shutoff of scheduled workflows is disregarded on the operator's evidence from another project.
date: 2026-09-25
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0054: A scheduled run happens, or it is not silently gone

## Context and Problem Statement

Two different mechanisms can stop a scheduled run from happening at all, and neither reports anything when it does. They are unrelated in cause and identical in effect, which is why they are decided together.

**The first is concurrency.** Both workflows share a concurrency group. GitHub's default behaviour in a group is that a newly queued run cancels the run already waiting, so a third run arriving while a second waits leaves only the third. The implementing seat found this and set `queue: max` on both workflows, and the fix was unrecorded until now.

**The second is inactivity.** GitHub disables a repository's scheduled workflows after sixty days without repository activity. Its documentation does not define what counts as activity, so whether the pipeline's own twice-daily commits to the `data` branch reset the clock is not knowable from the documentation.

The operator's requirement covers both in one sentence: "i do not want anything to be dropped and properly handled even if a fourth or a fifth arrives."

## Decision Drivers

- A dropped run costs latency under ADR-0007, and that is acceptable only if the run actually happens later.
- A cancelled run and a disabled schedule both produce silence rather than a failure, and silence is the failure mode this project spends most of its effort on.
- Neither mechanism can be tested by waiting for it: concurrency needs three runs at once, and inactivity needs sixty idle days.

## Assumptions

- `queue: max` allows up to 100 pending runs in a group and cancels beyond that; the default cancels the waiting run; and `queue: max` cannot be combined with `cancel-in-progress: true`. **Sourced** from GitHub's workflow-syntax documentation, read by the implementing seat on 2026-09-25 and verified by it.
- More than 100 runs will never be pending. **Stated**, and safe by construction: the schedule produces two a day and a dispatch is manual.
- Repository activity, whatever GitHub counts, will not lapse for sixty days. **Stated** by the operator, 2026-09-25: "the 60 day rule can be disregarded as my rahzaan project pipeline is running for the past 3 months or more." **The evidence is outside this repository**, as was the earlier evidence from his LinkedIn pipeline recorded in `STATE.md`. It is not measurable here until sixty days have passed, and it is recorded as his decision rather than as a fact this project has established.

## Considered Options

- Leave the default concurrency behaviour and accept that a third run displaces a waiting second.
- Set `queue: max` on both workflows.
- Give each workflow its own concurrency group.
- For inactivity: disregard it; or add a scheduled commit whose only purpose is to be activity; or move the schedule to an external trigger.

## Decision Outcome

Chosen: **`queue: max` on both workflows, and the sixty-day shutoff disregarded.**

**Runs queue, up to GitHub's hundred.** A fourth or fifth run arriving while others wait takes its place in the queue instead of displacing the one ahead of it. Both workflows set `cancel-in-progress: false`, which `queue: max` requires, so a run in progress is never killed by a newcomer either.

**`tests/test_workflow.py` pins both settings on both workflows.** This is the only way either can be checked, since the behaviour itself needs three simultaneous runs to observe.

**The sixty-day shutoff is disregarded on the operator's evidence**, and the record says plainly that the evidence is from another of his projects rather than from this one. Nothing is built to defend against it: no keep-alive commit, no external trigger, no reminder.

**What would show it wrong.** The run log report states the number of runs and the span they cover, so a schedule that stopped firing appears as a run count that no longer grows against elapsed days. On 2026-09-28 it read 24 runs over 10.5 days. That is the detector, it already exists, and it costs nothing.

### Consequences

A queued backlog means a run can start well after its slot, so its postings carry a later first-seen time and Measure A records the delay. That is the standing trade of this project stated once more: latency is acceptable, loss is not.

Both workflows sharing one group means the contract check can queue behind a fetch and vice versa. With queueing that is a delay rather than a cancellation, so the shared group is now harmless where before it was the thing that dropped runs.

A keep-alive commit was considered and rejected, and the reason is worth keeping: a commit whose only purpose is to be activity would put a meaningless entry in the history of a repository whose history is one of the project's deliverables.

If the shutoff does happen, the cost is bounded and visible: scheduled runs stop, the run count stops growing, and re-enabling them is a click. Nothing is lost, because ADR-0007 makes a gap non-destructive and the boards still list what was published during it.

### Confirmation

**The pinned settings must be seen failing.** Remove `queue: max` from either workflow, or set `cancel-in-progress: true`, and `tests/test_workflow.py` must fail. A test that passes for both configurations pins nothing.

**The run count against elapsed time must be readable in one command**, which `tools/run_log_report.py` already gives. A count that stops growing is the only signal either failure produces.

## Pros and Cons of the Options

### Leave the default concurrency behaviour

Good, because it needs no change and runs never pile up.
Bad, because it silently discards a waiting run, which is exactly the operator's stated objection.

### A concurrency group per workflow

Good, because the contract check and the fetch stop waiting for each other.
Bad, because it solves a delay nobody has complained about and leaves the dropping problem untouched within each group. It stays available if queue depth ever becomes visible.

### A keep-alive commit against inactivity

Good, because it removes the uncertainty entirely for the cost of one commit a month.
Bad, because it writes noise into a history that is part of what this repository is for, and it defends against a risk the operator has evidence against.

## More Information

ADR-0007 is why a missed or delayed run costs latency rather than data, and it is the reason queueing is a sufficient answer rather than a partial one. ADR-0015 owns Measure A, which absorbs the delay a queued run adds. ADR-0024's session logs and the run log report are where either failure becomes visible.

Both halves are the operator's decisions of 2026-09-25, relayed by the implementing seat, which had found the concurrency gap and read GitHub's documentation for the numbers.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | Both workflows pin the runner image to `ubuntu-24.04` | GitHub announced on every run that `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19, and Python 3.11 is untested there; a run that fails on a new image is a run that does not happen. Sourced from that notice by the implementing seat, not verified by the chat. A test holds the pin. The pin is lifted deliberately, after a test run on the new image, and no later than GitHub's announcement that 24.04 is retiring |
