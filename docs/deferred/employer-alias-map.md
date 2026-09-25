---
type: deferred
description: Deduplicating one role that arrives from two source classes, which needs an employer alias map. Deferred while one instance exists; revisit at the second or third, or when an accepted row turns out to have a twin.
status: current
---

# The employer alias map, and deduplication across source classes

**Deferred 2026-09-25**, on the operator's decision. Not rejected. Not
scheduled. It was already deferred as item 22 of `CHAT_STATE.md`, whose
trigger was a second source class in production; that trigger is now met, and
this file replaces it with a sharper one.

## What happens today

One role reaches the display twice when Himalayas carries a posting from a
board the pipeline already polls directly.

**Measured 2026-09-25 through the Airtable connector.** `Jobs` holds "GTM AI
Engineer -Deal Desk" twice: once as `greenhouse:8693228002` from Motive's
Greenhouse board, and once as a Himalayas row under the company slug
`thinkmotive`. One instance, out of 44 rows.

## Why the two cannot collapse

**ADR-0001's key is employer, title and publication date.** Himalayas stamps
its own publication date rather than passing the board's through, so the dates
differ for the same role.

**The employers do not match either.** The ATS row reads `Motive`; the
Himalayas row carries the slug `thinkmotive`. ADR-0027's fold reconciles case,
separators, punctuation and Latin accents, and none of those is the
difference. ADR-0026 already records that a derived employer with no alias
does not take part in cross-source deduplication, which is exactly this case.

So the collapse needs a name-to-name map, maintained by the operator as
configuration under ADR-0031, before any rule can use it.

## Why it was not built

**One instance is not a pattern**, and the cost of guessing is asymmetric.
Dropping the date from the key, or matching on title alone, merges roles that
are not the same: two different "AI Engineer" postings at two employers are in
today's display, and one employer posting two different "Software Engineer"
roles is ordinary. ADR-0001 put the date in the key for that reason, and
ADR-0027 records that the design fails toward duplicates rather than toward
silent merges, because a duplicate is visible and a merge is not.

**What it costs to leave it.** The operator reads one role twice. The
aggregator copy links to himalayas.app rather than to the employer's board, so
the two rows are not interchangeable when applying. If he accepts both, the
accepted store holds two identities for one application, and ADR-0044's star
will later mark each as sharing an employer with an accepted row, which is
noise rather than error.

## The trigger

Revisit when **any** holds.

**A second and third duplicate appear.** Two more instances make it a pattern
rather than a coincidence of one employer being on both sources.

**Or an accepted row turns out to have a twin.** That is the case where the
cost stops being cosmetic: the accepted store is the record of what was
applied to, and two identities for one application corrupt ADR-0044's
comparisons and the operator's own history.

**Or a third source class arrives.** Two aggregators multiply the pairs rather
than adding to them.

## What revisiting would have to produce

**The map first, as configuration.** A file the operator edits, one line per
alias, with its provenance: which source produced the name and where it was
seen. It starts with one line, `thinkmotive` for Motive.

**Then a rule that names what it did.** A cross-class collapse must be
explainable in one sentence, per ADR-0010, and reversible: the stores keep
both rows whatever the display shows. Suppressing the aggregator copy at the
projection is the cheapest shape, because it changes no key and no stored
record, and ADR-0037 already puts the grouping at the projection.

**And a check that can fail.** Two different roles sharing a title at one
employer must stay two rows after the change, and the observed pair must
become one. Neither half is worth anything without the other.

## Where the evidence is

`CHAT_STATE.md` items 104 and 108. The duplicate itself is in `Jobs`, read
through the connector on 2026-09-25, and named in the implementing seat's
brief of 2026-09-24, part 1, item E2.
