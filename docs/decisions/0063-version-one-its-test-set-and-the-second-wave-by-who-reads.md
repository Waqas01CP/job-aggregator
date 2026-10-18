---
status: accepted
topic: practice
description: Version 1 in one record, consolidating ADR-0059 at its eighth amendment. The system working for the operator himself, on sources chosen for their value to him, each with its own isolated contract check; the test for done now set, four weeks from November 1; all four second-wave feeds built now, Hacker News first, the rest ordered by who reads the application; four employer boards found through it added; Breezy read once; every run log naming its commit. Supersedes ADR-0059.
date: 2026-10-18
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0063: Version 1, its test for done set, and the second wave by who reads the application

## Context and Problem Statement

ADR-0059 decided on 2026-10-03 UTC what version 1 is: the system working for the operator himself, fed by sources chosen for their value to him, employer boards first and a second wave of four feeds after, each source with its own isolated contract check. It holds seven Changes rows. By 2026-10-18 UTC the first wave was built (Manatal, Workable, SmartRecruiters and Ashby), and the operator made two sets of decisions on what remained:

- **The test for done.** The window over which Measure A must hold and the period he uses the tables were his to choose; so were whether a dropped posting's own reason must be stored, and Breezy.
- **The second wave.** The implementing seat measured the four feeds on 2026-10-18, in its report on Brief 15. Before it did, he set out what he had concluded from his applications: "there have been rejections and all this tells me and i conclude is that the places i am applying is HR meaning screened by these people. now these people are screening then no matter how good i am in something unless until i do not have the experience and years, i will continue to be rejected. the solution for this is targeting those platforms and sites that are just my stack specific and where response is fair and good. or the best possible option are those sites where founders, engineers and people who are of my stack or who understand these technical aspects are looking for skills and technical and not experience or years."

A row on ADR-0059 for either would be its eighth, the Decision Record Standard's supersession trigger (ADR-RULES). He chose on 2026-10-18 to supersede it once, with both: "option b is good". This record consolidates ADR-0059 and adds them.

The tensions: yield against who reads the application, since the source with the most founders and engineers writing is free text the rules were not built for; building now against October's Airtable allowance, which every client spends (ADR-0004, ADR-0062); and ADR-0057's rule that a place it cannot name is kept, against a source that gives no structured country.

## Decision Drivers

- Version 1 serves one person, so value to him is the only measure of a source.
- The application should reach the employer, and his CV should go nowhere else.
- What cannot be established from public evidence is measured from the project's own data, per source, with its count.
- A source must be readable under its own terms, free (the operator's standing cost constraint), with a date where it gives one. A source without one orders its postings after every dated posting (ADR-0007's Changes of 2026-10-07).
- Nothing about a source may reorder the display, which is ordered by date alone (ADR-0010, ADR-0057).
- A failure in one source must not reach any other.
- Where the application is read by a founder or an engineer rather than a recruiter, the source is worth more to him (his conclusion of 2026-10-18, stated, not tested).

## Assumptions

Carried from ADR-0059, with its corrections:
- No public study ranks job sources by ghost-posting or CV-harvesting rate. **Sourced**: CRS In Focus IF12977 (2025) states there are no official statistics on ghost jobs, and a 2026 peer-reviewed scoping review names comparative data by channel as a gap; research 0005 found none ranking sources by CV harvesting either.
- Direct employer boards are not proof of genuineness. **Sourced, weakly**: Greenhouse's own unexplained 18 to 22% a quarter, and a September 2026 vendor report finding 28% of ATS postings open over 90 days. Research 0005.
- The four first-wave platforms' dates differ in meaning. **Sourced** from each vendor's documentation, 2026-10-03 or 10-04 UTC, and **measured**: Ashby's date is the last publication, kept at its first value seen (ADR-0052); Workable defines `published_on` as the publication date; SmartRecruiters' `releasedDate` is undefined and trusted on the operator's decision of 2026-10-17; Manatal's postings carry no date, none of 640 read. Breezy documents no public endpoint. Research 0005 and its Corrections.
- A recommendation without evidence carries no weight. **Stated**: "you do not need to prioritize influencers or other fake sources as they are of no value", 2026-10-03 UTC.

New:
- What the second wave yields. **Measured** by the implementing seat on 2026-10-18 through the real normaliser and chain, each posting dated at its reading as a daily poller would see it. Hacker News' "Who is Hiring" thread keeps 27 of October's 266 posts; 16 of them are on site in cities the location rule cannot place and 1 is hybrid, and about 7 a month are remote with no region limit or say nothing of place, 10 on November's rules. Its job stories keep 2 in 30 days, Jobicy 2 a week, RemoteOK about 3 a month, We Work Remotely 1 in its feed.
- Who reads the application. **Measured, and mostly unstated**: on Hacker News' thread 77 of 266 posts give an address to write to, 9 are written by a founder, CEO or CTO in the first person and 7 by an engineer or hiring manager; on Jobicy and We Work Remotely, where a posting describes its process, it names the employer's recruiter, 216 of 833 and 31 of 88. Most posts on every source do not say. Whether an application is answered is **not measured**; only his own applications can show it.
- Each feed's terms allow the use. **Sourced**, read by the implementing seat on 2026-10-18: Jobicy, polling "must not exceed once per hour" and no listing presented as one's own; We Work Remotely, links attributed back; RemoteOK, a followed link back and the source named; Hacker News' Algolia and Firebase APIs, keyless, with no limit stated, as research 0005 found; not re-read that day.
- The new sources' rows fit what is left of October's allowance. **Not established.** The implementing seat projects it before the build reaches Airtable; if they do not fit, the operator's rule below applies.

## Considered Options

For the test, the options were his choices, each put to him with the chat's recommendation. For the second wave:

- By yield alone, as ADR-0059 ordered it.
- Hacker News now, the other three after its first month.
- All four now, Hacker News first, the other three ordered by who reads the application.
- Nothing until November, when the allowance resets.

## Decision Outcome

Chosen option for the second wave: "all four now, Hacker News first, the other three ordered by who reads the application".

**We will call version 1 the system working for him, as he intends.** Working for anyone else is a later version and a decision of its own.

**We will choose sources by their value to him**: genuine postings, fairness to the applicant, time to get hired, fit, meaning roles he can take under ADR-0057 and ADR-0058, and, where it can be read, who reads the application. A source's size or reputation counts for nothing, and a claim about a source counts only under the project's evidence standard, graded as research 0005 grades it.

**We will integrate in this order.**
1. **Employer boards on further ATS platforms**, ordered by measurement. Built: Manatal on 2026-10-07, on its career site's undocumented endpoint for all nine boards, his acceptance; Workable on 2026-10-08; SmartRecruiters on 2026-10-17; Ashby on 2026-10-17. When sources are measured against each other, a posting with no date counts as passing the current rules (his decision of 2026-10-09).
2. **Himalayas stays.**
3. **The second wave, all four built now, Hacker News first**: its monthly "Who is Hiring" thread and its job stories, the source whose posts are written by the hiring company and where a person can be written to. Its posts are free text, so title and place come from each post's first line, held by tests of their own.
4. **Then Jobicy, RemoteOK and We Work Remotely**, one at a time, those whose postings are read by founders and engineers rather than recruiters first where the counts show it. Each was measured on 2026-10-18 before this decision, as ADR-0059 required, and his call on the numbers is to build all four. All four are to be in place before Measure A's window opens on November 1, so the system it measures is the one that will be judged.

**We will build without spending October's allowance when it cannot carry the new rows.** In his words: "if quota is an issue then just do not do api call and only build." Asked whether that meant holding the rows from Airtable while the sources are still read, or reading nothing until November, he chose the first: each source is built and read, its postings are judged at first sight and stored, and its rows reach `Jobs` when the allowance has room, at the latest when November's resets. A request to the source itself spends no Airtable call.

**We will add to the registry the four employer boards the second wave led to** whose postings today's rules keep if read fresh: LiveKit, ClickHouse, Mastra and PostEra, one request a board a run.

**We will read Breezy once**, on its undocumented endpoint, which he accepts for that read, and judge it on the measured number. A Breezy that yields nearly nothing is marked out of version 1. Otherwise it waits, as before, for a documented endpoint or his acceptance of the undocumented one for use.

**Not integrated**: foorilla, formerly ai-jobs.net, whose API costs $64 a month; Remotive, whose 24-hour delay means each of its postings reaches him later than Measure A's 24-hour median target however often it is polled; hiring.cafe; Y Combinator Work at a Startup; Welcome to the Jungle; Wellfound; Adzuna; and Rozee.pk, Mustakbil and Bayt, whose terms or privacy policy forbid automated use and which stay his to use by hand. Each reason is in research 0005.

**Not candidates until each passes the access gate on its own documentation**: Arbeitnow, Working Nomads, and every other source research 0005 did not re-read.

**We will treat "preferred" as integrated first, and as nothing else.** A source never moves its postings up the display. A mark naming a source as better, a star or a note, is added only if he asks for one, and never orders a view.

**We will let the implementing seat research each source as it integrates it**, and report whether each claim research 0005 makes about that source was confirmed or contradicted. Only a claim found wrong goes into 0005's Corrections table, marked as wrong when written or changed since; a confirmation stays in the seat's report and log; and a contradiction that changes a source's place is brought back here.

**We will measure each source's genuineness from the project's own data**, per source and with its count: how long postings stay up, reposting under a new identity or a reset date, postings that never close, the source's date against the employer board's for the same role, and where the apply link lands. No threshold is set in advance; thresholds come from this project's own distributions.

**We will give every source its own contract check, isolated from the rest.** A change in one source's response, or a crash in checking it, is reported for that source and stops neither another source's check nor the run. Every finding reaches Airtable as a row. Built: the isolation on 2026-10-04, and the `Health` table on 2026-10-07 (ADR-0061).

**We will record in every run log the commit that ran it**, so that a dropped posting's reason can be recomputed under the rules of its day as well as today's. A dropped posting's own reason is not stored: its rule in the run log, its posting in the raw layer and that commit are enough.

**We will keep three things out of version 1**: the priority star (ADR-0044), for version 2; deduplication across sources (`docs/deferred/employer-alias-map.md`); and response quality (`docs/deferred/response-quality.md`).

**We will declare version 1 done only when he says so**, on this test:
- Measure A (ADR-0015) holds over four weeks from November 1, 2026-11-01T00:00Z to 2026-11-29T00:00Z, every production run inside it, the window the implementing seat took, and reported on 2026-11-29 as the two-week assessment was (ADR-0015). It starts on November 1 because the Senior switch (ADR-0032) and the description fields (ADR-0035, ADR-0058) change what reaches the display that day.
- Nothing is lost silently: every drop and every closure names its rule.
- The system runs unattended: every scheduled run happens (ADR-0054) and every failure reaches Airtable.
- Every integrated source has its isolated contract check.
- He uses the tables over the same four weeks.

### Consequences

Coverage grows mainly through the registry. An employer he wants to see is added by its own board, and the second wave serves as discovery for it. Its first reading found 49 boards on built platforms, none in the registry, which kept 5 postings if read fresh, on the four added here: an employer board yields little to his rules, as the registry's own boards had shown.

Postings reach him from the employer's own system wherever possible. Hacker News adds a second route, a person at the company to write to, which is the nearest the sources come to what he asked for.

Hacker News brings free text into a pipeline built for structured payloads. Its title and place are read from a first line, a reading that can fail in ways the platforms' fields do not, so its tests carry more weight. Its on-site posts in cities the location rule cannot place are closed by ADR-0057's row of 2026-10-18; without that row, about 17 roles a month he cannot take would reach his table, 16 on site and 1 hybrid.

A source built now may wait for the display. If October cannot carry its rows, they reach `Jobs` with November's allowance, and their age is still judged at first sight (ADR-0052), so nothing is lost; the wait shows in Measure A for those postings.

His conclusion about who screens is a criterion here, not a finding. If his own applications show otherwise, the criterion is his to drop.

The Karachi on-site lane stays thin. Rozee.pk, which carries it, forbids automated use. No AI-only board passed research 0005, so the AI lane is served by employer boards and the title pool.

### Confirmation

**A source's place must never change the display's order.** Two postings from sources of different standing are ordered by date alone, whatever either source is.

**One source's check must not touch another's.** Make one source's check raise and change another's response: the first is reported as a failed check for that source, the second's change is still found, and the run's other sources are fetched.

**A contract finding must be seen as a row in Airtable**, in test mode first.

**No source is built without its contract check**, from its first production run.

**Every run log must name the commit that ran it.**

**A source built while the allowance cannot carry its rows must be seen fetching and storing, and sending nothing to Airtable.**

**Every second-wave posting must be seen linking to its source's own page and naming its source.**

**Live only:** the yield measured before each feed is built; each source's genuineness signals, reported with their counts once there is data; the seat's confirmed or contradicted claims, per source; Hacker News' yield, apply route and who is asking, recounted after its first month; Breezy's one read; and Measure A over its four weeks.

## Pros and Cons of the Options

### By yield alone

Good, because it is ADR-0059's rule and needs no new criterion.
Bad, because Jobicy's 2 a week rival Hacker News' count while going through the board, and a recruiter is named in a quarter of its postings: yield alone ignores the one thing he said decides his rejections.

### Hacker News now, the other three after its first month

Good, because the free-text reading is proven on one source before three more depend on the lessons, and Hacker News, the source closest to what he asks for, comes first; on November's rules it also yields the most, about 10 a month, while on today's Jobicy's 2 a week are about as many.
Bad, because the other three would join in mid-November, inside Measure A's window, changing what that window measures.

### All four now, Hacker News first

Good, because coverage is widest soonest and the system is complete when Measure A's window opens. Each source is still built one at a time with its own contract check and tests, and its yield is counted on its own in the run log, so which source brings value stays visible.
Bad, because four mappings and four checks are built in two weeks, with less learned between them; and who reads is stated in a minority of posts on every source, so the order of the other three is read from what posts choose to say.

### Nothing until November

Good, because October's allowance is untouched.
Bad, because a source built and fetched now spends none of it either, and waiting delays the build by two weeks for no saving.

## More Information

**Supersedes ADR-0059**, which carries the pointer back. ADR-0059 closed the end-state gap ADR-0023 kept open, replaced ADR-0029's adapter order and ADR-0019's survey order for the remaining aggregators, and extended ADR-0036, now superseded by ADR-0061; each of those records keeps its Changes row pointing at ADR-0059, which now means this record.

**Carried forward from ADR-0059 unchanged:** version 1 as the system working for him; the value criteria; employer boards first by measured yield, then Himalayas, then the second wave by measured yield, a feed's worth his call on the number; the list not integrated, with its reasons; the access gate; "preferred" as integrated first and nothing else; the seat's research per source and how its findings are recorded; genuineness measured from the project's own data; the isolated contract check and its Airtable row; the three things kept out, the star for version 2; a posting with no date passing when sources are compared; done only when he says so; and its four Confirmation clauses, word for word, with its "Live only:" items. ADR-0059's annotated corrections and its Changes rows on the order are folded into the text above as they stand. **Changed:** who reads the application added to the value criteria; the second wave built now, all four, Hacker News first; the build held from Airtable when the allowance cannot carry it; four boards added; Breezy read once; the test's window and period set; a dropped posting's reason recomputed from the run log, the raw layer and the commit each run log now names.

ADR-0057 owns eligibility, and its row of 2026-10-18 closes Hacker News' unplaceable on-site posts. ADR-0015 owns Measure A. ADR-0062 owns the pipeline's monthly ceiling of 900 and ADR-0004 the allowance. ADR-0047 keeps aggregator rows in private destinations; which source class each second-wave source belongs to is the implementing seat's to state as it builds it. ADR-0048 sets the cadence, and Jobicy's terms allow no more than one poll an hour. ADR-0061 owns the contract check. ADR-0049 requires the checks above to be held by tests.

Where version 1 stands is tracked in `docs/versions/v1.0.0.md`; this record keeps the decisions.

Evidence: `docs/research/0005-job-source-value.md`, and the implementing seat's report on Brief 15, 2026-10-18, its counts and patterns.

The operator's decisions this record carries: version 1 as the system working for him; his four answers then: sources beyond the first five chosen by their value to him, with a research pass to "properly curate a list of best sources" and a better source integrated first and never moved up the display; the star waiting for version 2; a contract check always present for each source on its own; and duplicates across sources outside version 1; the integration order and the seat's leave to research each source, 2026-10-03 UTC; the test for done, 2026-10-04 UTC; the version file, 2026-10-04 UTC; Manatal's undocumented endpoint, 2026-10-07; on 2026-10-09 UTC, the order between SmartRecruiters and Ashby, "if both are inevitable to be implemented then next is futile as one is done then next will be done", and a posting with no date as passing, "if the post is genuine then i would like to see it"; SmartRecruiters' `releasedDate` trusted, 2026-10-17, and the go for Ashby, "yes do your work and proceed so that the seat may start its work."; and on 2026-10-18 UTC: the four choices of the test, on the chat's recommendations, "1. yes. 2. yes 3. accepted. 4. yes."; one supersession with both, "option b is good"; his conclusion, quoted in the Context; the second wave, "1. yes, but the rest are also to be done especially where the technical people are like the founder or ceo or others instead of hrs. 2. it is fine. keep it. 3. yes, this is good enough 4. add them 5. ok."; and, asked to settle his point 2 and the order, "1. a. 2. the points 1 and 3 is right but building should be done right now and not in november and if quota is an issue then just do not do api call and only build. 3. yes, build the run log."; and, asked whether "right now" meant Hacker News alone or all four, and whether "api call" meant Airtable's only or the sources' too: "1. option b. 2. option a.", all four now, and the sources still read while their rows are held from Airtable.

## Changes

| Date | Change | Reason |
|---|---|---|
