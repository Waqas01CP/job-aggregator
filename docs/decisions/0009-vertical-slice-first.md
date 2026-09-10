---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0009: Vertical slice first, adapters incremental

## Context and Problem Statement

The source registry holds 53 employer boards with resolvable handles across roughly sixteen ATS platforms. The build can complete all adapters before going live, or deploy a narrow end-to-end path and add adapters afterwards.

The structural components carry the design risk: fetch, normalise, deduplicate, filter, write, schedule, and the operator's review loop. The adapters are repetitive and additive.

Greenhouse and Lever are the only platforms whose endpoints are documented and verified. The remainder require a feasibility spike before an adapter can be specified.

## Decision Drivers

- Filters meet real data for the first time at go-live and will be wrong.
- Adapters are additive, so nothing is rewritten when they are added later.
- Value accrues from the first live board, not from the last.

## Assumptions

- Filters will require correction on first contact with real board data. Stated from experience; the specific defects are unknown.
- Greenhouse and Lever endpoints behave as documented. Documented but not tested in this session.

## Considered Options

- Complete all adapters, then deploy.
- Deploy a vertical slice, then add adapters against the running system.

## Decision Outcome

Chosen option: "deploy a vertical slice, then add adapters".

We will build and deploy a slice covering Greenhouse and Lever only, eleven boards, with all hard filters, the title classification of ADR-0016, the schedule of ADR-0006, and real writes to every storage layer. We will add remaining platform adapters incrementally against the running system, in an order fixed after the feasibility spikes.

### Consequences

Structural defects surface once, early, against a small dataset.

The eleven boards in the slice stop being searched by hand as soon as it is live.

Measure A begins collecting on real data sooner.

Coverage is partial for a period, so manual searching continues for boards not yet adapted.

The project is done when the slice is live and manual searching has stopped for those boards. Subsequent adapters are maintenance, not project scope.

### Confirmation

The slice is confirmed when a scheduled run completes unattended, writes rows to all three layers, and the operator finds a role in the display that they had not already seen by hand.

## Pros and Cons of the Options

## More Information

Adapter order after the slice is pending, blocked on feasibility spikes for Ashby, Workable, SmartRecruiters, JazzHR and Manatal. Spike form follows `test_linkedin_scraper.py`: thresholds fixed in advance, machine verdict of PROCEED or INVESTIGATE.
