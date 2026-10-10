---
status: accepted
topic: practice
description: The end state ADR-0023 left open. Version 1 is the system working for the operator himself, fed by sources chosen for their value to him rather than for their reach, integrated employer boards first, each source with its own isolated contract check that reaches Airtable. The priority star, cross-source duplicates and response quality wait.
date: 2026-10-03
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0059: Version 1 is the system working for him, on the sources worth having

## Context and Problem Statement

ADR-0023 confirmed on 2026-09-11 that no artifact says what this system is ultimately for, and kept that gap open until it was decided deliberately. Three weeks of building later, the question had become practical: which of the remaining pieces are part of finishing, and which are a later version.

The operator settled it on 2026-10-04 (2026-10-03 UTC). Version 1 is the aggregator working for him, as he intends it. Making it work for anyone else is a later version, and a separate decision.

Four questions followed, and he answered each.

- **Sources.** Version 1 includes sources beyond the five ADR-0029 adapters, chosen by their value to him: whether postings are genuine rather than ghost posts or CV harvesting, how long hiring takes, how fairly applicants are treated, and whether AI-specific boards serve him better. He asked for a research pass, and that it "properly curate a list of best sources". He also asked that a better source mean one integrated first, and never one whose jobs are moved up the display.
- **The priority star** (ADR-0044) waits for version 2, because it compares against accepted rows, and those come only from his using the tables.
- **The contract check** must always be present, for each source on its own, so that one source's change cannot affect the rest.
- **Duplicates across sources** stay an open issue outside version 1. Judging whether a source is worth having is inside it.

Research pass 0005 assessed the candidates on those criteria. Its central finding is uncomfortable: no public evidence ranks sources by how genuine their postings are. The only measured figures are vendors', or a preprint's, and they put ghost and long-open postings on direct employer boards too. What can be established from primary sources is narrower: which sources can be read under their own terms, which send the applicant to the employer, and which say who may apply.

The tension is between reach and value. A large aggregator brings many postings, many of them carried by an employer board already read directly, with an apply link that passes through the aggregator and eligibility that is often unstated. *(Corrected 2026-10-05 (2026-10-04 UTC): "many of them" is not measured; one duplicate was seen in 44 rows on 2026-09-25.)* An employer board brings fewer postings, each from the employer's own system. And the pending cross-source duplicates grow with every aggregator added.

## Decision Drivers

- Version 1 serves one person, so value to him is the only measure of a source.
- The application should reach the employer, and his CV should go nowhere else.
- What cannot be established from public evidence is measured from the project's own data, per source, with its count.
- A source must be readable under its own terms, free (the operator's standing cost constraint), with a date on each posting. *(Corrected 2026-10-05 (2026-10-04 UTC): with a date where it gives one; a source without one orders by first seen, as ADR-0007 allows and ADR-0029 accepted for Manatal.)* *(Changed 2026-10-09: since the operator's rule of 2026-10-07, a posting with no date is shown after every dated posting, not by first seen; ADR-0007's Changes.)*
- Nothing about a source may reorder the display, which is ordered by date alone (ADR-0010, ADR-0057).
- A failure in one source must not reach any other.

## Assumptions

- No public study ranks job sources by ghost-posting or CV-harvesting rate. **Sourced**: CRS In Focus IF12977 (2025) states there are no official statistics on ghost jobs, and a 2026 peer-reviewed scoping review names comparative data by channel as a gap. Research 0005. *(Corrected 2026-10-05 (2026-10-04 UTC): these sources cover ghost postings only. Research 0005 found none ranking sources by CV harvesting either.)*
- Direct employer boards are not proof of genuineness. **Sourced, weakly**: Greenhouse's own unexplained 18 to 22% a quarter, and a September 2026 vendor report finding 28% of ATS postings open over 90 days. Research 0005.
- Ashby, Workable, SmartRecruiters and Manatal each publish a keyless endpoint with a date on each posting. **Sourced** from each vendor's own documentation, 2026-10-04 (2026-10-03 or 10-04 UTC), with differing meanings: Ashby's date is the last publication, Workable's and SmartRecruiters' are undefined, and Manatal's endpoint filters on a creation date. Breezy documents no public endpoint. Research 0005. *(Corrected 2026-10-05 (2026-10-04 UTC): Manatal's endpoint filters on a creation date, but whether its postings carry that date is **not measured**; ADR-0029's spike found none on two boards.)* *(Corrected 2026-10-09: two statements here were wrong when written. Workable defines both its dates, `published_on` as the publication date and `created_at` as the creation timestamp. Manatal's postings carry no date: none of 640 distinct postings read carried one, and its creation filter brackets a posting's creation day without stating it. Research 0005's Corrections.)*
- Which platforms yield the most postings he can take. **Not measured.** The implementing seat measures it before the order is fixed.
- A recommendation without evidence carries no weight. **Stated**: "you do not need to prioritize influencers or other fake sources as they are of no value", 2026-10-04 (2026-10-03 UTC).

## Considered Options

- Order by reach or by recommendation: the largest feeds, or a published ranking.
- Keep the orders already recorded: ADR-0029's cost-first list for employer platforms, and ADR-0019's survey order for aggregators.
- Order by value to him: employer boards first, each group ordered by the postings he can take, aggregators as a second wave.
- Integrate every candidate that passes the access gate at once.

## Decision Outcome

Chosen option: "order by value to him".

**We will call version 1 the system working for him, as he intends.** Working for anyone else is a later version and a decision of its own.

**We will choose sources by their value to him**: genuine postings, fairness to the applicant, time to get hired, and fit, meaning roles he can take under ADR-0057 and ADR-0058. A source's size or reputation counts for nothing, and a claim about a source counts only under the project's evidence standard, graded as research 0005 grades it.

**We will integrate in this order.**
1. **Employer boards on further ATS platforms**: Ashby, Workable, SmartRecruiters and Manatal. Their order among themselves is set by measurement: one request to each registry board the platform hosts, and the platform whose boards carry the most postings passing the current rules goes first, the number of registry boards breaking a tie. **Breezy waits** until its public endpoint is documented by Breezy, or the operator accepts an undocumented one. *(Measured 2026-10-04: Manatal first, with 10 postings passing on the five boards its documented endpoint served, and none on the other three platforms. Workable second by the tie-break once the operator added four of its slugs to his registry on 2026-10-07: six registry boards against two. Manatal was integrated on 2026-10-07 and Workable on 2026-10-08. SmartRecruiters and Ashby tie on both counts, two boards each; the seat proposes SmartRecruiters next, by its one posting that failed on age alone, a tie-break this rule does not contain, so the order between them is the operator's. See Changes.)* *(Settled 2026-10-09: SmartRecruiters next, then Ashby, on the operator's answer that the order between two sources both to be built does not matter to him. See Changes.)*
2. **Himalayas stays.**
3. **A second wave**: Hacker News "Who is Hiring", Jobicy, We Work Remotely and RemoteOK, ordered the same way, by the postings each yields that he can take, measured before it is built. A feed whose yield is negligible is not built. *(Changed 2026-10-05 (2026-10-04 UTC): whether a feed's yield is worth its upkeep is the operator's call on the measured number. See Changes.)*

**Not integrated**: foorilla, formerly ai-jobs.net, whose API now costs $64 a month; Remotive, whose 24-hour delay alone breaks Measure A's median (ADR-0015); hiring.cafe; Y Combinator Work at a Startup; Welcome to the Jungle; Wellfound; Adzuna; and Rozee.pk, Mustakbil and Bayt, whose terms or privacy policy forbid automated use and which stay his to use by hand. Each reason is in research 0005. *(Corrected 2026-10-05 (2026-10-04 UTC): Remotive's delay does not break Measure A, which is one median over all postings (ADR-0015). It means each Remotive posting reaches him later than that median's 24-hour target, however often it is polled.)*

**Not candidates until each passes the access gate on its own documentation**: Arbeitnow, Working Nomads, and every other source research 0005 did not re-read.

**We will treat "preferred" as integrated first, and as nothing else.** A source never moves its postings up the display. A mark naming a source as better, a star or a note, is added only if he asks for one, and never orders a view.

**We will let the implementing seat research each source as it integrates it**, and report for every claim research 0005 makes about that source whether it was confirmed or contradicted. The result is recorded in 0005's Corrections table, and a contradiction that changes a source's place is brought back here. *(Clarified 2026-10-05 (2026-10-04 UTC): only a claim found wrong goes into 0005's Corrections table, whether it was wrong when written or has changed since, marked as which, as pass 0003's corrections were; a confirmation stays in the seat's report and log.)*

**We will measure each source's genuineness from the project's own data**, per source and with its count: how long postings stay up, reposting under a new identity or a reset date, postings that never close, the source's date against the employer board's for the same role, and where the apply link lands. No threshold is set in advance; thresholds come from this project's own distributions.

**We will give every source its own contract check, isolated from the rest.** A change in one source's response, or a crash in checking it, is reported for that source and stops neither another source's check nor the run. Every finding reaches Airtable as a row, which ADR-0036 deferred until the writer existed. Both are required before version 1 is done. *(Both built: the isolation on 2026-10-04 and the Airtable row, as the `Health` table, on 2026-10-07; ADR-0061, which supersedes ADR-0036.)*

**We will keep three things out of version 1**: the priority star (ADR-0044), for version 2; deduplication across sources (`docs/deferred/employer-alias-map.md`); and response quality (`docs/deferred/response-quality.md`).

**We will declare version 1 done only when he says so**, on a test he sets. The chat's proposal is in Consequences. *(Test accepted by the operator on 2026-10-05 (2026-10-04 UTC). See Changes.)*

### Consequences

Coverage grows mainly through the registry. An employer he wants to see is added by its own board, and the second-wave feeds serve as discovery for it: an AI employer hiring from Pakistan seen there is a candidate for the registry.

Postings reach him from the employer's own system wherever possible, which is the fairest route research 0005 found and the one that keeps his CV with the employer he chose.

Fewer aggregators means fewer duplicates while deduplication waits, and fewer apply links passing through a third party.

The Karachi on-site lane stays thin. Rozee.pk, which carries it, forbids automated use in its privacy policy. Manatal, on which eight or nine registry boards sit (ADR-0029), is the nearest substitute, and how far it closes the gap is measured rather than assumed.

Pass 0003's best AI-specific source no longer exists in the form 0003 read. No AI-only board passed in this pass, so the AI lane is served by employer boards and the title pool.

The contract findings table is a new Airtable table, small, against the base's 1,000 records (ADR-0004). *(Built 2026-10-07 as `Health` and `Health test`, which carry the fetch run's failures as well as the contract findings: ADR-0061.)*

**The chat's proposed test for "done"**, for him to confirm or change: Measure A (ADR-0015) holds over a window he chooses; nothing is lost silently, every drop and every closure naming its rule; the system runs unattended, every scheduled run happening (ADR-0054) and every failure reaching Airtable; every integrated source has its isolated contract check; and he then uses the tables for a period he chooses. *(Accepted by the operator on 2026-10-05 (2026-10-04 UTC). See Changes.)*

### Confirmation

**A source's place must never change the display's order.** Two postings from sources of different standing are ordered by date alone, whatever either source is.

**One source's check must not touch another's.** Make one source's check raise and change another's response: the first is reported as a failed check for that source, the second's change is still found, and the run's other sources are fetched.

**A contract finding must be seen as a row in Airtable**, in test mode first. *(Built 2026-10-07 as the `Health` table, ADR-0061; held by tests, and live only until the operator sets its two secrets.)* *(Wrong when written, 2026-10-09: the operator had set both secrets on 2026-10-08, and the evening fetch wrote 17 rows to `Health`, all contract findings; ADR-0061.)*

**No source is built without its contract check**, from its first production run.

**Live only:** the yield measured before each platform and feed is built; each source's genuineness signals, reported with their counts once there is data; and the seat's confirmed or contradicted claims, per source.

## Pros and Cons of the Options

### Order by reach or recommendation

Good, because the largest feeds bring the most postings soonest.
Bad, because reach is not value: most large feeds state eligibility weakly and carry postings already read from employer boards, and a recommendation without evidence is the thing he ruled out. *(Corrected 2026-10-05 (2026-10-04 UTC): they may carry such postings; the overlap is not measured.)*

### Keep the recorded orders

Good, because nothing is re-decided.
Bad, because ADR-0029 ranked platforms by the cost of a date, on which four now tie, and ADR-0019's survey order includes a board that no longer exists in that form. *(Corrected 2026-10-05 (2026-10-04 UTC): four of ADR-0029's five already tied there, and Manatal was not one of them.)*

### Order by value to him

Good, because each source earns its place by what it measurably gives him, and the fairest route to the employer comes first.
Bad, because it is slower: every platform and feed waits for a measurement, and employers seen only on aggregators arrive later.

### Every passing source at once

Good, because coverage is widest soonest.
Bad, because nobody could tell which source brought value, the duplicates arrive all together, and the contract checks are built in one batch with nothing learned between them.

## More Information

Closes the end-state gap ADR-0023 kept open, which carries a Changes row pointing here. Replaces ADR-0029's adapter order and ADR-0019's survey order for the remaining aggregators; both records stay accepted for their other decisions and carry Changes rows. Extends ADR-0036 by requiring the isolation and the Airtable row for version 1. ADR-0044's star is unchanged and waits.

Evidence: `docs/research/0005-job-source-value.md`, which corrects pass 0003 on ai-jobs.net, Jobicy and Rozee.pk.

**Where version 1 is tracked: `docs/versions/v1.0.0.md`.** What 1.0.0 includes, its sources, its test for done and what waits, each with its current status. This record keeps the decisions; that file says where each stands. Added 2026-10-05 (2026-10-04 UTC).

The operator's decisions of 2026-10-04 (2026-10-03 UTC): version 1 as the system working for him; the four answers above; the integration order, approved that day; and the seat's leave to research each source as it integrates it.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-05 (2026-10-04 UTC) | The operator accepted the proposed test for "done". The window over which Measure A must hold and the period of use stay his to choose | His decision, 2026-10-05 (2026-10-04 UTC), given after he asked for the round's work to be checked. The rule that version 1 is declared done only by him is unchanged |
| 2026-10-05 (2026-10-04 UTC) | Eight statements annotated as corrected or clarified, the original text kept: the aggregators' overlap with employer boards and the ghost-job evidence's reach, both overstated; the driver's date requirement, which now admits a source without a date as ADR-0007 already did; Manatal's date, unmeasured; Remotive's delay, stated against its own postings rather than against the pipeline's median; where the seat's findings are recorded; and the tie on the cost of a date. One clause changed: a feed's yield is the operator's call rather than an unstated threshold. The chosen option gains the pros and cons it lacked | An independent audit of the round, run on the operator's request. Each statement claimed more than its source shows. The chat's errors |
| 2026-10-05 (2026-10-04 UTC) | Version 1's definition and status are kept in `docs/versions/v1.0.0.md`, a file of its own; this record keeps the decisions | The operator's decision, 2026-10-05 (2026-10-04 UTC): the end state should be distinct from the decision records in its name and convention. He chose a separate version file over renaming this record, since a version's status changes as the work does while a record is concluded once |
| 2026-10-09 | Dates restated in UTC across the records the chat wrote on 2026-10-03 and 2026-10-04 UTC, the originals kept. A date the chat wrote as 2026-10-05 is marked "(2026-10-04 UTC)"; a decision or research event it dated 2026-10-04 that happened that evening is marked "(2026-10-03 UTC)"; the research, begun that evening and finished the next UTC day, is marked "(begun 2026-10-03 UTC)", and a reading within it whose UTC day is not known "(2026-10-03 or 10-04 UTC)". This record's frontmatter date, where no mark can sit, is corrected to 2026-10-03 | `CLAUDE.md`'s rule, "Dates are UTC": the chat dated by the operator's clock in Karachi, UTC+5. His messages that night carry Karachi times up to 02:23 on 2026-10-04, which is 21:23Z on 2026-10-03, and he committed the chat's 2026-10-05 rows at 21:19Z on 2026-10-04. The implementing seat found the 2026-10-05 rows; the chat found the 2026-10-04 events while correcting them |
| 2026-10-09 | The order measured and followed. Manatal first: 10 postings passed on the five boards its documented endpoint served, none on the other three platforms (2026-10-04). Workable second by the tie-break, six registry boards against two once the operator added four slugs on 2026-10-07. SmartRecruiters and Ashby tie; the order between them is put to the operator. Manatal integrated on 2026-10-07 on its career site's undocumented endpoint for all nine boards, the operator's acceptance; Workable on 2026-10-08. Breezy still waits. The Assumption on the four platforms' dates corrected: Workable's are defined and Manatal's postings carry none, both wrong when written. The chat reads a posting with no date as passing the current rules, since the chain keeps it and the operator's rule of 2026-10-07 never drops it for age; that reading is put to him | The implementing seat's report on Brief 10 and its addenda. The order's rule did not say whether a posting the age rule cannot judge "passes". He chose the undocumented endpoint for all nine boards after the finding that the documented one gives no working link to a posting was put to him; it also serves the four boards the documented one does not. The isolation and the Airtable row this record required are built, in ADR-0061 |
| 2026-10-09 | SmartRecruiters next, then Ashby, as the implementing seat proposed. A posting with no date counts as passing the current rules when platforms are measured against each other | The operator's answers of 2026-10-09 UTC. On the order: "if both are inevitable to be implemented then next is futile as one is done then next will be done"; the chat's reading is that, at 0 passing on each, the order decides mainly which boards wait longer for a first sight; SmartRecruiters also costs a request per posting for its description and states the levels that ADR-0032's row of the same day reads. On the dateless reading: "if the post is genuine then i would like to see it", and a posting that is not recent he notes and removes himself |
