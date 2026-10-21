---
type: reference
description: The annotation and data-labelling vendors whose postings are dropped, why the list exists, what it is sourced from, and how thin that evidence is.
status: current
---

# Annotation vendors

Employers whose postings are dropped before the title rule runs, because their
roles are data annotation and labelling work rather than engineering.

The rule matches the **employer** name, not the title, because these vendors
post engineering-sounding titles for annotation work. It runs before the title
rule, so a dropped row is counted as a vendor drop and not as a title miss.

## How the names match

On the employer string, normalised exactly as titles are: lowercase, hyphens,
dashes, underscores and slashes to spaces, commas, parentheses, periods and
colons deleted, whitespace collapsed. A name matches if it appears in the
normalised employer string.

## Vendors

`welo data` · `welocalize` · `innodata` · `aptura`

## The evidence, and how thin it is

One census, quoted in `docs/reference/title-pool.md`: 17 of 34 rows in a prior
harvest were Welo Data, Welocalize and Innodata. That is a real measurement of
a real problem, half of one sample, and it is the only measurement there is.

**Nothing has been measured on this pipeline's own boards.** No row fetched by
this pipeline has been dropped by this rule, because none of the eleven
configured boards is one of these vendors. The rule is carried forward against
future boards and against the aggregators, where these employers actually
appear.

Until then, treat this file as a hypothesis that has never fired, rather than
as a filter with a track record.

*(2026-10-21: it has fired. Startup.jobs' measurement of 2026-10-20 dropped
12 postings by these names; and Aptura, the fourth name, met the test below
on a board this pipeline polls: 14 of the 44 postings kept at reading.)*

## What would justify a fourth name

A vendor earns a place when its postings have been seen on a board this
pipeline polls, and the roles are annotation work under an engineering title.
A name added on reputation alone drops an employer that may be hiring
engineers, and a dropped row never reaches the display to be argued with.

The safer direction is the drop log: `tools/title_pool_report.py --dropped`
lists titles the pool rejected, and a vendor posting engineering titles will
show up there first.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | File created from the constant `ANNOTATION_VENDORS` in `src/filters.py`, with no change to the three names | The list was a tuple in code with a comment saying it was provisional and carried by no record. ADR-0031 requires that a preference live in a versioned file with an audit trail, like the title pool and the seniority list, so this is that file. The names are unchanged, so no filtering behaviour changes with this move |
| 2026-10-21 | `aptura` added, the operator's decision of 2026-10-21 | Seen on Startup.jobs, a board this pipeline polls: 14 postings, one text in fourteen fields ("Accounting AI Research Contributor", "Legal AI Research Contributor" and so on), each an independent contract of about 4 to 6 weeks, paid by the task, writing Excel tasks and yes-or-no marking criteria to test frontier AI models, asking 3 or more years in that field and no engineering. Kept by the title pool's `ai research`. The operator: "the aptura 14 roles can be left behind as they are of not my domain and simple repetetive work". The name matches inside any employer name; no stored employer but Aptura contains it, checked over every stored layer the same day |
