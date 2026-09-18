---
status: accepted
topic: fetching
description: A per-run request ceiling, and a posting's detail fetched once ever rather than once per run.
date: 2026-09-16
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0028: Per-run fetch budget, and detail fetched once per posting

## Context and Problem Statement

Six platforms carry a publication date only per posting, never on the list endpoint. BambooHR and Workday expose it on a detail endpoint; JazzHR, Freshteam, iCIMS and Zoho Recruit carry it inside per-posting HTML.

Reaching it costs one request per posting. Contour's Workday board returns 90 postings, so 90 extra requests per run, 180 a day at ADR-0006's cadence, for one board. JazzHR's NorthBay board shows the same arithmetic. Six platforms behave this way.

**No accepted record fixes a per-run fetch budget.** ADR-0006 governs how often the pipeline runs. ADR-0014 governs Airtable API calls. Nothing governs HTTP volume against third-party endpoints, and until now nothing needed to, because every adapted platform answered in one request per board.

One fact changes the sizing entirely: **a posting's publication date does not change once published.** So a detail fetch is needed once per posting ever, not once per posting per run. ADR-0003's seen-identifier structure already records what has been observed.

## Decision Drivers

- These are free endpoints belonging to other people, polled twice daily indefinitely.
- Six platforms, roughly 20 registry boards, are unreachable without a policy.
- A runaway loop must not be able to issue unbounded requests.
- Per the standard, a number stated without a basis is a guess and does not belong in a decision.

## Assumptions

- A posting's publication date is immutable once published. **Stated**, from the meaning of the field. Not measured, and falsifiable: a platform that re-stamps on edit would break the once-only rule. `updated_at` on Greenhouse is already known to be bulk-written, which is a related but different failure.
- Steady-state new postings per run are a small fraction of total postings. **Not measured.** This is the assumption the whole sizing rests on and it has no basis yet. Measuring it is this record's Confirmation.
- Detail endpoints tolerate sequential polling at the spacing used. Not measured for any of the six.

**No figure in this record is offered as a measured per-run volume.** The number below is a safety stop, not a policy, and the distinction is the point.

## Considered Options

- Accept N+1 every run under a fixed ceiling.
- Take ADR-0007's first-seen fallback for these six and forgo Measure A on their rows.
- Defer all six until the slice shows whether Measure A coverage matters.
- Fetch detail once per posting, ever, driven by the seen-identifier structure.

## Decision Outcome

Chosen option: "fetch detail once per posting, ever", with a measured budget to follow.

**A posting's detail is fetched once.** If its identifier is already in the seen structure with a recorded publication date, no detail request is made. First contact with a board costs one request per posting; steady state costs one per genuinely new posting.

**A per-run request ceiling is enforced in the shared HTTP module**, counting every attempt including retries and failures, refusing further requests once reached. Enforced in code, not by intention.

**The initial ceiling is 500, and it is a runaway guard rather than a politeness policy.** Its only job is to stop a loop or a pagination bug from issuing unbounded requests. It is not a claim about what volume is appropriate, because nobody has measured what volume is needed.

**The real ceiling is set from measurement.** The run log records requests issued per source and in total, every run. After the first month of live running, the ceiling is set from the observed distribution and this record amended with the figure and its basis.

**Work deferred by the ceiling is recorded, never dropped.** The run log names what was skipped, and it is picked up next run. This is safe because ADR-0007 means a late posting is a latency cost, not a loss.

### Consequences

Six platforms and roughly 20 registry boards become reachable, and Measure A becomes computable on their rows.

Steady-state cost becomes proportional to new postings rather than to board size, which is the difference between 180 requests a day for one board and a handful.

First contact with a large board is expensive, once. A 90-posting board costs 90 requests on the run that first adapts it.

The seen structure becomes load-bearing for cost, not only for deduplication. A bug that loses it triggers a full re-fetch of every board.

The immutability assumption is doing real work. A platform that re-stamps publication dates on edit would silently carry stale dates, because the detail would never be re-fetched.

A ceiling that is hit routinely means the cadence, the board set or the ceiling is wrong. The run log makes that visible rather than leaving it as slow degradation.

Until the measurement lands, the project is running on a number with no basis, and this record says so rather than implying otherwise.

### Confirmation

**The measurement that sets the real ceiling.** Over the first month, the run log records requests per source and per run. The ceiling is then set from the observed distribution, with a stated margin, and this record amended with both the figure and how it was obtained. Until that amendment, the ceiling in force is explicitly provisional.

**That the once-only rule works:** run twice against a board with no new postings and confirm the second run issues no detail requests. If it issues any, the seen structure is not being consulted.

**That the ceiling can fire:** set it to a number below a board's posting count and confirm the run stops, logs what was skipped, and completes rather than failing.

## Pros and Cons of the Options

### Accept N+1 every run

Bad, because it spends the same requests forever to re-learn a value that never changes.

### First-seen fallback for all six

Good, because it costs nothing.
Bad, because it discards a publication date that is available, on roughly 20 boards, permanently. ADR-0007's fallback exists for platforms that have no date, not for platforms whose date is merely inconvenient.

### Defer all six

Good, because it is free and reversible.
Bad, because two of the six are among the dominant Pakistani platforms, which is where Karachi-reachable roles are.

## More Information

Extends ADR-0005, whose complete-board-output rule governs the list endpoint. A detail fetch is not a filter; it retrieves a field the list endpoint omits.

Extends ADR-0003, whose seen-identifier structure is what makes once-only fetching possible.

Evidence is the platform spikes of 2026-09-11, 15 and 16.
