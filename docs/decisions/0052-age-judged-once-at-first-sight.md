---
status: accepted
topic: filtering
description: A posting is admitted only if it was published no more than seven days before the pipeline first saw it, judged once at first sight and never again, so an admitted row never ages out unseen.
date: 2026-09-26
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0052: Age is judged once, at first sight

## Context and Problem Statement

The operator opened his table on 2026-09-26 and found postings he would not apply to because they were too old. ADR-0007 had decided that recency is expressed by ordering rather than by filtering, and on that reading the old rows were correct behaviour: everything still listed on a board is ingested, and the display puts the newest at the top. He rejected that, and rejected the filtered view the implementing seat offered him instead, as effort spent on hiding a problem rather than fixing it.

His reason names the purpose of the whole system: "after a week the chances of getting a job form that is drastically less ... the main intention for creating this entire system were two: 1. i appear first and apply within the few hour when the posting goes live ... 2. that i get the most recent of posts and not more than week old".

**Then the harder half, which is his correction rather than his request.** The seat built the rule against each run's clock, so a posting admitted today would have vanished a week later whether or not he had read it. He caught that from the seat's description alone, before it ran, and restated the rule: "i might not see the table for a few days then it would mean some posts will be out without my knowledge which i do not want". The date is absolute at the moment of the fetch, and relative afterwards. A posting published on the first and fetched on the second was found within a day, and the system did its job; two weeks later that is still true, and nothing about the row has changed except the calendar.

This record exists because those are two different decisions and only the first was asked for.

## Decision Drivers

- The system's own purpose is to be early, so a week-old posting is not what it was built to deliver.
- A row the operator has not read must never disappear because time passed.
- Absences of one to ten days are expected, which is ADR-0007's premise and is unchanged.
- A repost under a years-old date is not a new opportunity, which is the operator's judgement of 2026-09-26.
- Nothing may be dropped on a date whose meaning is unproven.

## Assumptions

- A posting more than a week old at first sight is materially less likely to be worth applying to. **Stated** by the operator, 2026-09-26. Not measured, and not measurable from this side: it would need application outcomes.
- Seven days is the right threshold. **Stated** by him. It is configuration in `config/eligibility.json` under ADR-0031, not a constant, so it can be widened without a code change.
- A board's publication date means publication. **Measured** for Greenhouse on 2026-09-28: the live board's `first_published` for posting 5058944004 read 2024-01-24T18:33:29-05:00, which is exactly the stored `published_at` of 2024-01-24T23:33:29Z, and every row records which field supplied it in `published_field`. **Not established** for Lever, which is why Lever is exempt below. *(Annotated 2026-10-09: **not** true of Himalayas, whose date is its own listing date. Measured on the 7 of its postings still open on an employer board this pipeline reads: later than the employer's `first_published` by 1, 2, 2, 3, 14, 23 and 293 days. A small sample.)*
- A repost carries its original publication date rather than a new one. **Measured** 2026-09-26: of the 83 Greenhouse postings already old at first sight, 60 are a single Speechify role reposted city by city since 2024.

## Considered Options

- Keep ADR-0007 as it stands: ingest everything and let ordering handle age.
- A filtered view in Airtable that hides old rows without dropping them.
- Judge age against each run's clock.
- Judge age once, at first sight.
- Judge age on the board's `updated_at` rather than its publication date.

## Decision Outcome

Chosen option: "judge age once, at first sight".

**A posting is admitted only if it was published no more than seven days before the pipeline first saw it.** The rule is `rule_age` in the chain, and it names itself in every drop it logs, per ADR-0010.

**The judgement is made once and never revisited.** The comparison is between the posting's publication date and its own `first_seen`, both of which are stored and neither of which moves. *(Annotated 2026-10-09: true of what the pipeline stores, not of every source's field. Ashby's `publishedAt` moves on a republish, so its adapter, not yet built, must keep the first value it saw for a posting. See Changes.)* So an admitted row stays admitted however long it waits in the display, and a dropped row stays dropped however long the board keeps listing it.

**Exactly seven days is admitted.** The boundary is inclusive, and the paginated walk's own age limit is set one second beyond it precisely so that a posting sitting exactly on the limit can never end a walk before it is fetched.

**A repost never enters.** A posting first seen already older than a week is dropped whatever its history, including a posting that is being relisted under its original date. The operator judged such relisting to be harvesting rather than hiring, and his ruling is that the original date stands. *(Annotated 2026-10-09: this holds on employer boards. Himalayas' date is its own listing date, so an opening months old on the employer's board can enter through Himalayas as new. See Changes.)*

**Lever is never dropped for age.** Its `createdAt` is not proven to be a publication date: 6 of 22 Lever postings appeared on the board more than a week after it. Dropping on an unproven date would silently lose roles, which is the failure this project spends most of its effort avoiding.

**The raw layer is untouched.** Everything a board returns is still ingested and kept, which is ADR-0007's rule and its reason: a missed run costs latency, not data. This rule lives in the chain that feeds the display, and nothing else.

### Consequences

The display becomes much smaller and much younger. Measured over the 346 stored public rows on 2026-09-28: 13 rows survive the rule and 333 do not, the excluded set collapsing into 27 display groups, among them one Speechify role of 170 rows published 2024-01-24 and the same role again as 131 rows published 2025-05-07. The median gap between publication and first sight across the whole stored layer is 503 days, which is the measure of how much of a job board is not news.

That shrinkage is also the main relief on the Airtable call budget, because the projection's cost is linear in display rows. It was not the reason for the rule and it is the largest side effect of it.

**A row's publication date recedes while it sits in the display, and that matters for anything that deletes by date.** Measured on 2026-09-28: of the 13 groups this rule admits, 11 were published more than seven days earlier. So a purge keyed on publication date with a seven-day threshold would delete almost every legitimate row, and the honest axis for clearing the display is how long a row has been in it, not how old the posting is. This is recorded here because the rule is what creates the trap.

Rows dropped for age are recoverable. They stay in the raw layer, the drop is logged with the rule's name, and widening the limit brings them in through ADR-0030's backfill, since the judgement uses stored dates that do not move.

Lever's exemption means the display can hold a Lever posting of any age. Three of the 346 stored public rows are Lever's, so the exposure is small, and it closes the day Lever's date is proven either way.

ADR-0007's consequence that "no filtering is required" is now false. Its four rules are all still in force and untouched; the record gains a row saying which sentence this one falsified.

### Confirmation

**A posting exactly seven days old at first sight must be admitted, and one a second older must be dropped.** The boundary is the whole rule, so it is the case to build against.

**An admitted row must still be admitted a week later.** Advance the clock a week over a stored row and re-run the chain: nothing changes. The mutation that must fail this is the seat's own first build, judging against the run's clock, which is why it is worth keeping as a mutation rather than only as a fixed bug.

**A Lever posting older than a week must be admitted**, and the drop log must never name `rule_age` for a Lever row.

**Widening the limit must admit what it previously dropped.** Raise the number in configuration, run ADR-0030's backfill, and the previously dropped rows must appear with their original `first_seen` intact.

**No drop may be unlogged.** Every age drop names the rule, the publication date and the first-seen date, so the judgement can be re-derived from the log alone.

## Pros and Cons of the Options

### Keep ADR-0007 as it stands

Good, because it changes nothing and keeps one rule for recency.
Bad, because the operator opened the table and found it full of roles he would not apply to. Ordering puts the newest first; it does not stop the oldest being there.

### A filtered view in Airtable

Good, because it needs no code and no record, and nothing is ever dropped.
Bad, because it hides the rows rather than not surfacing them: they still spend Airtable records against a 1,000-record cap and still spend calls on every projection. The operator rejected it himself as effort spent on the wrong thing.

### Judge age against each run's clock

Good, because it is the obvious reading of "nothing more than a week old", and the display then contains only postings under a week old at all times.
Bad, and this is the whole point of the record: a row he has not read disappears because time passed, which breaks the guarantee that nothing is lost without his knowledge. He caught this from a description before it ever ran.

### Judge age on `updated_at`

Good, because it answers "is this posting active" rather than "when did it first appear", and a maintained posting would stay eligible.
Bad, because it would lift every years-old relisting to the top of the display. The Speechify role measured on 2026-09-28 was first published in January 2024 and updated three weeks before the measurement. The operator's ruling that a relisting under an old date is harvesting settles it, and `updated_at` is recorded here as rejected rather than left for a later reader to discover as an improvement.

## More Information

**ADR-0007 is not superseded and none of its rules is reversed.** It decided four things: ingest everything without reference to publication date, record a first-seen timestamp on every record, order the display on publication date descending with a first-seen fallback, and record which of the two supplied the ordering date. All four are in force and all four are live, verified on 2026-09-28: every one of the 346 stored public rows carries a publication date, `ordering_date` equals `published_at` on all 346, and `ordering_date_source` reads `publication` on all 346, so the fallback has never fired. What this record falsifies is ADR-0007's consequence that ordering handles age and no filtering is required. *(Changed 2026-10-09: since the operator's rule of 2026-10-07, the first-seen fallback no longer orders the display. A posting with no date is shown after every dated posting, the operator's rule in ADR-0007's Changes; the other three still hold.)*

**The corpus now holds three positions on recency and they do not conflict.** No filter at ingest, which is ADR-0007 and is why a missed run loses nothing. A filter at the display, judged once at first sight, which is this record. And ordering by publication date descending, which is ADR-0007 again and is what the operator sees.

ADR-0031 owns the seven-day limit as configuration. ADR-0010 requires the rule to be named and deterministic, which it is. ADR-0030 is how a widened limit reaches rows already stored. ADR-0016's deferred experience rule is the other half of what he means by a role worth applying to, and it stays deferred.

The operator's decision, 2026-09-26, and his correction of the same day, which is the part that made it right. The seat's first build is `4ff46dc`.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | Evidence that the rule handles reposts correctly, from the operator's repost research: 57 of 560 employer-and-title pairs carry more than one publication date; 303 postings published over 180 days ago were updated within the last 30; Speechify's role sits under two requisitions, one per date. A relisting under an old date stays out and a new requisition's new date is admitted, so no repost rule is needed | The operator asked whether reposting is harvesting or genuine demand. The data cannot separate the two, but it shows evergreen postings are common, and this rule already does the right thing with both. Measured by the implementing seat, 2026-09-30, the requisitions from the full postings ADR-0051 keeps; no rule follows, by his decision of 2026-10-03 |
| 2026-10-09 | Himalayas' date is its own listing date, not the employer's. Measured by the implementing seat on 2026-10-04: of 1,525 saved Himalayas postings, 10 come from employers this pipeline reads directly, and on the 7 still open on the employer's board Himalayas' date is later by 1 to 293 days. So "a repost never enters" holds on employer boards and not through Himalayas. The rule is unchanged; whether to guard against this is put to the operator | The cheapest guard, preferring the employer board's date where the employer is read directly, is deduplication across sources by another name, which ADR-0059 keeps out of version 1. A decision for him, not one to make in this record |
| 2026-10-09 | No guard against Himalayas' listing date in version 1: an old opening that enters through Himalayas as new is accepted, and the guard waits with deduplication across sources | The operator's answer of 2026-10-09 UTC to the question of the row above: "yes, it is acceptable." Measured scale: 10 of 1,525 saved Himalayas postings come from employers read directly. `docs/deferred/employer-alias-map.md` holds the deduplication it would need |
| 2026-10-09 | Two dates that move or are missing. Ashby's `publishedAt` is when a posting was last published and moves on a republish of the same posting, so its adapter must keep the first value it saw for an identity, or a republished row would jump up a display ordered by date; a new posting for an old job enters as new, and the adapter's runs will count both. A posting with no date at all is kept and never dropped for age, by the operator's rule of 2026-10-07 UTC | Ashby's own reference, read by the implementing seat on 2026-10-04: unpublishing and republishing act on the same posting. Keeping the first value is what "neither of which moves" already requires of a stored date; it is recorded here for the adapter, not as a new rule |
