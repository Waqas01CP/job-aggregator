---
type: deferred
description: Adding Rozee.pk as a source. Deferred until the display works and until more ATS sources are added, either of which may remove the need for it.
status: current
---

# Rozee.pk

**Deferred 2026-09-18.** Not rejected. Not scheduled.

## What it is

Pakistan's dominant job board, and the largest remaining gap in coverage for
Karachi on-site roles. That lane is the one the current eleven boards serve
worst: the ATS registry is thin on Pakistani employers, and the aggregators
carry remote roles rather than local ones.

## What is known, and it is more than usual for a deferred item

Checked in an earlier session and unchanged since:

- **robots.txt permits the job paths.**
- **The terms carry no automated-access clause.**
- **A sitemap index publishes job URLs daily, with the title in the slug.**

So it is not blocked by permission or by access. It is deferred on priority.

## Why it is deferred

**The display does not work yet.** Adding a source increases the input to a
pipeline whose output nobody has read. The operator's reasoning, and it is
correct: coverage is worth nothing until the thing that shows him the coverage
exists.

**It is a different shape of adapter.** Every current source returns JSON from
an API. Rozee would be read from a sitemap and per-posting pages, which means
a parsing path nothing else shares. ADR-0019's condition for a new source asks
whether it forces a change to the shared HTTP module, the normaliser's row
shape, or the filter chain; a sitemap source plausibly touches the first, and
that question deserves to be asked when it is actually being built.

**It may turn out to be unnecessary.** This is the operator's own point and it
is the strongest of the three. More ATS sources are coming: ADR-0029 names
Ashby, Workable, SmartRecruiters, Breezy and Manatal as the next five, and
Manatal alone holds eight or nine registry boards and is one of the two
dominant Pakistani platforms. **Manatal may cover the same employers Rozee
lists**, through an API, at one request per board, with no new parsing path.

Building Rozee first would be paying the highest cost for coverage that the
cheapest adapter might deliver anyway.

## The trigger

Revisit when **all three** hold:

1. The display works and the operator has used it for long enough to know
   what is missing from it.
2. ADR-0029's five adapters are built, Manatal among them.
3. The Karachi gap is still visible in the display after those five.

The third is the real test. If Manatal and the others fill the lane, this file
is closed rather than actioned, and that is a good outcome.

## What revisiting would have to produce

A decision record, because it would be the first non-API source and the first
to read a sitemap. ADR-0019's three-component condition would have to be
evaluated against the diff, per ADR-0039.

Also a measurement, not an impression: how many roles the display is missing
that Rozee carries, after the five adapters. "Karachi coverage is thin" has
been true for the whole project and has never been a number.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | File created | The operator deferred it explicitly and named the condition that may remove the need for it entirely: more sources first, after which Rozee may not be required. Recording only "deferred" would have lost that reasoning and left the next session to rediscover that the access questions are already answered |
