---
status: accepted
topic: fetching
description: Which adapters are built after the slice and in what order, ranked by the cost of obtaining a publication date.
date: 2026-09-16
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0029: Adapter order after the slice, and Dover dropped

## Context and Problem Statement

ADR-0009 deferred adapter order, blocked on feasibility spikes for Ashby, Workable, SmartRecruiters, JazzHR and Manatal. All five are done, alongside eleven other platforms. Sixteen have now been probed.

The measured picture separates them by cost of obtaining a publication date, not by the tier assignments made before any endpoint was tested.

**One unauthenticated GET per board, publication date at 100% under an unambiguous name:** Ashby (`publishedAt`), Workable (`published_on`), SmartRecruiters (`releasedDate`), Breezy (`published_date`). Pinpoint is equally cheap but its date is in RSS rather than the JSON.

**One GET per board, no date at all:** Manatal, across 34 postings on two boards. It holds eight or nine registry boards and is one of the two dominant Pakistani platforms.

**One request per posting:** JazzHR, Freshteam, iCIMS, Zoho Recruit. BambooHR and Workday need a detail endpoint per posting. ADR-0028 governs these.

**Unusable:** Dover. Its per-employer careers endpoint returns 103 postings with no date, no URL and no employer. Its other endpoint returns 482 postings with `date_posted` at 100% and an employer per row, but **its `client` filter is accepted and silently ignored**: the first 100 rows span 45 different employers.

The apparent tension is between cost and coverage, and it dissolves on inspection. Manatal is simultaneously the cheapest platform available and among the highest-coverage. Its only defect is datelessness, which ADR-0007 already handles by design: those rows order by first-seen and do not contribute to Measure A.

## Decision Drivers

- Karachi-reachable roles are concentrated on the Pakistani platforms, which is the coverage the operator most lacks.
- Cheap adapters ship sooner and prove the model against more source shapes.
- ADR-0007 means a dateless source degrades the measure's coverage, not the pipeline.

## Assumptions

- Manatal's two probed boards represent its other boards. **Measured** on 2 of 9; not measured on the rest.
- Board counts per platform are as the registry records them. **Sourced** from the registry, which was harvested rather than re-verified.

## Considered Options

- Cost-first: the four one-GET dated platforms, then reassess.
- Coverage-first: Manatal and JazzHR early despite their costs.
- Cost-first including Manatal, since it is both cheapest and high-coverage.

## Decision Outcome

Chosen option: "cost-first including Manatal".

**After the slice, in this order: Ashby, Workable, SmartRecruiters, Breezy, Manatal.** Five adapters, one GET each, roughly fifteen registry boards.

Manatal is included despite having no date field. Its rows order by first-seen under ADR-0007 and are excluded from Measure A, with their share reported alongside the measure so the coverage cost is visible rather than hidden.

**Then reassess against real data**, rather than fixing the rest of the order now. JazzHR is the first candidate after that, at ten boards, and it depends on ADR-0028's budget measurement landing first.

**Pinpoint is deferred**, not rejected. Its date is in RSS while its JSON has none, so it needs a second parsing path for one board.

**Dover is dropped from the registry as a source.** The per-employer endpoint is unusable. The dated endpoint is a different product: an aggregator carrying 45 unregistered employers behind a filter that pretends to work. Adopting it would mean taking on a source research pass 0003 never surveyed, whose terms were never examined, which ADR-0020 would route to separate storage on exactly those grounds, for one registry board.

**The tier assignments in the source registry are obsolete.** Tiers A through D were constructed for an eight-hour scope that no longer exists, and rested on assumptions about endpoints that have since been measured directly. The measured platform table supersedes them. Re-tiering would maintain a fiction.

**EY and Recruitee are out.** EY is a corporate careers site rather than an ATS and was never probed. Recruitee is named in the registry as exposing public JSON but has no board recorded anywhere, so there is nothing to poll. Recorded here so neither is re-proposed.

### Consequences

ADR-0009's parked decision is closed.

Five adapters after the slice reach roughly fifteen boards at one request each, which is the cheapest coverage available anywhere in the registry.

Manatal's rows never contribute to Measure A. On eight or nine boards that is a real dent in the measure's coverage, accepted deliberately and reported rather than absorbed.

Karachi coverage remains thin until JazzHR is adapted, and JazzHR waits on ADR-0028's measurement.

Dropping Dover loses one registry board and avoids an unsurveyed aggregator.

Declaring the tiers obsolete removes a structure that several earlier documents reference. Those references now point at nothing, and the architecture document carries the measured table instead.

### Confirmation

After the five adapters are live, the run log reports rows per platform and the share of rows carrying a publication date. If Manatal's share of dateless rows exceeds what the operator finds tolerable in Measure A's coverage line, this order was wrong and Manatal should have waited.

If any of the four "one GET, 100% coverage" platforms turns out to need a second request or a second parsing path in practice, the spike measured something that does not hold at adapter scale, and the cost-first premise needs re-examining.

## Pros and Cons of the Options

### Coverage-first

Good, because it reaches Karachi roles sooner.
Bad, because JazzHR is one request per posting and blocked on ADR-0028, so coverage-first means starting with the most expensive platform before its budget policy is measured.

## More Information

Closes the adapter-order item ADR-0009 deferred.

Manatal's datelessness is the material case ADR-0007 was written for, and the first one found. Before the spikes it rested on a registry note with no endpoint tested.

ADR-0028 governs the platforms that need a request per posting.
