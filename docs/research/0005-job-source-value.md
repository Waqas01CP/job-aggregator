---
type: research
description: Pass 0005. Which job sources are worth integrating, judged by their value to the operator rather than by whether they can be polled. Every load-bearing claim checked against its primary source; employer ATS boards first, Himalayas kept, four feeds as a second wave, the rest out.
status: current
---

# Research 0005: Job source value

Run 2026-10-04 by the operator's clock: begun on 2026-10-03 UTC, after he set its criteria at 21:02Z, and finished, with its verification, before the chat's commits on 2026-10-04 UTC. Findings reflect those dates. Terms, prices and endpoints change; the implementing seat re-checks each source's claims when it integrates that source, and a claim it finds wrong, whether wrong when written or changed since, is recorded in the Corrections table at the end, marked as which, as pass 0003's were.

**Question asked.** Of the job sources a personal aggregator could read, which are worth having for this operator, and in what order should they be integrated?

Pass 0003 asked whether a source can be polled: an endpoint, a lane he can be hired in, terms permitting polling, a publication date. It did not ask whether a source is worth having. This pass asks that, and re-checks the access gate, because terms, prices and endpoints move, and one of 0003's recommended sources no longer exists in the form 0003 read.

## What "value" means here

The operator's criteria, 2026-10-04 (2026-10-03 UTC), in substance:

- **Genuineness.** Postings that are real openings: no ghost posts left up with no intent to hire, no postings that exist to collect CVs or applicant data, no scams.
- **Fairness and consideration to applicants.** Whether the application reaches the employer, what the applicant is charged or made to give up, and whether the applicant's CV is sold on.
- **Time to get hired.** How quickly, and whether at all, employers reached through a source respond.
- **Fit.** AI, ML and LLM roles at entry level, at most three years asked (ADR-0058), that he can take from Pakistan (ADR-0057). AI-specific boards may be better than general ones.

He named the evidence standard in the same message: "you do not need to prioritize influencers or other fake sources as they are of no value." His example was a ranking posted on X naming hiring.cafe, Welcome to the Jungle, Himalayas and Y Combinator in that order, which carries no weight against a legitimate source or a verified record. A person's vouching counts only when the person is identifiable and the vouch can be checked.

**The project's standing evidence rules apply.** Primary sources only: official bodies and statistics, peer-reviewed studies, established research organisations, and a platform's own documentation, which is primary for what the platform's policy is and never for claims about its own quality. Vendor figures count only with a credible publisher and a stated, sound method. Every claim is graded:

| Grade | Meaning |
|---|---|
| Strong | Read directly from the primary source |
| Moderate | A primary source that answers only part of the question, or several independent third parties that agree |
| Weak | One third party, such as a scraper listing or a GitHub issue, or a vendor figure without a sound stated method |
| Anecdotal | One person's report |

A weak claim is not discarded. It decides nothing on its own, and it becomes something to check, usually in minutes when the source is built.

## Method

1. A research run over the web, 2026-10-04 (begun 2026-10-03 UTC), against the criteria and the evidence rules above.
2. Three independent verification passes the same day, each reading the primary source behind every load-bearing claim of that run: the ATS platforms' own developer documentation; the boards' own terms, API pages and robots files, with a real browser where a page needed one; and the studies and official publications behind the ghost-job and scam figures. Where a payload was large, counts were taken in a browser rather than from a summarising fetch, which had truncated RemoteOK's array to 18 jobs.

The verification changed sixteen of the run's claims. They are listed under "What verification changed", because a record that reports only what survived is not a record of the research.

## Verdict

**Integrate employer boards on further ATS platforms first.** Ashby, Workable and SmartRecruiters each publish a keyless endpoint for a company's postings with a date on each posting, and Manatal one that filters on a creation date; on all four the application goes to the employer's own system. That is the fairest route to an applicant that exists. It is not proof of genuineness: the only measured figures for direct boards are vendors', and they put ghost and long-open postings on these platforms too. Genuineness per source has to be measured from the project's own data.

**Keep Himalayas.** It is the only aggregator read here that lists, per posting, the countries it is open to (Jobicy gives a region), which is what ADR-0057 needs, and its own documentation permits building on it.

**A second wave, each after its access claims are checked at build:** Hacker News "Who is Hiring", Jobicy, We Work Remotely and RemoteOK. Smaller, weaker on eligibility, and except for Hacker News their apply links pass through the board. Their best use is discovery: an AI employer hiring from Pakistan seen there is a candidate for the registry, whose own board then carries its postings directly.

**Not integrated:** foorilla, formerly ai-jobs.net, whose free API is gone and whose new one costs $64 a month; Remotive, whose public API delays every posting by 24 hours, so each one reaches him later than Measure A's 24-hour median target (ADR-0015); hiring.cafe, Y Combinator Work at a Startup, Welcome to the Jungle and Wellfound, which offer no permitted feed; Rozee.pk, Mustakbil and Bayt, whose terms or privacy policy forbid automated use; Adzuna, which has no Pakistan market. The three Pakistani boards remain useful by hand.

**No public evidence ranks sources by ghost-job rate.** The Congressional Research Service states there are no official statistics on how many ghost jobs exist, and a 2026 peer-reviewed scoping review names comparative data by channel as a research gap.

## The sources

### Employer ATS platforms

| Platform | Endpoint, keyless | Date on each posting | Grade | Notes |
|---|---|---|---|---|
| Greenhouse (live) | `boards-api.greenhouse.io/v1/boards/{board}/jobs` | `first_published`, the first publication | Strong | The single-job endpoint also carries `ai_disclaimer` and `ai_opt_out_request_url` where the employer uses Greenhouse's AI matching; the list endpoint does not, so reading them costs a request per posting |
| Lever (live) | `api.lever.co/v0/postings/{company}` | `createdAt`, epoch milliseconds, absent from Lever's own field table | Strong for access, its meaning undefined | Lever's README says published postings may be read by third parties. Consistent with ADR-0052, which never drops Lever for age because 6 of 22 postings appeared more than a week after their `createdAt` |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{name}`, docs updated 2026-05-26 | `publishedAt`, which Ashby defines as when the job was **last** published | Strong | A republished job reads as new. Also `isRemote`, `workplaceType`, a structured address, `secondaryLocations`, and compensation on request |
| Workable | `www.workable.com/api/accounts/{subdomain}`, no auth in its spec | `published_on`, the job's publication date, and `created_at`, its creation timestamp, both typed as dates; neither says whether a republished job keeps its first date *(corrected 2026-10-09)* | Strong | Also `telecommuting`, `workplace_type`, `experience`, `country`. The `apply.workable.com/api/v1` form is not documented by Workable |
| SmartRecruiters | `api.smartrecruiters.com/v1/companies/{id}/postings`, no auth for public postings | `releasedDate`, undefined, with a server-side `releasedAfter` filter | Strong | Also `locationType` remote, hybrid or onsite, and country. Its guide's prose speaks only of keys; its specification allows none |
| Manatal | `api.careers-page.com/open/v1/career-pages/{slug}/job-posts`, no auth | None: the job post schema has no date field, and none of 640 postings read carried one; a `created_at` filter brackets a posting's creation day *(corrected 2026-10-09)* | Strong for the endpoint | ADR-0029's spike was right: no date. The documented endpoint does not serve four of the registry's nine boards and gives no working link to a posting; the career site's undocumented endpoint serves all nine. The V1 and V2 shutdown of February 2025 applies to Manatal's authenticated Open API, not to its career pages |
| Breezy HR | No public endpoint documented by Breezy | n/a | Not verifiable | Breezy's API documentation lists only keyed endpoints. ADR-0029's spike measured `published_date` on an endpoint no Breezy page documents |

No platform states a rate limit for these public reads, except Lever's two application submissions a second, which do not apply. None was checked against the vendor's general terms of service.

Which platforms Pakistani AI employers actually use is **not established** by any survey. Manatal's prominence among Pakistani employers rests on the operator's registry, where it hosts eight or nine boards (ADR-0029), and on Manatal's own marketing. The registry is the evidence that matters, and it is measured by counting.

Hugging Face, named as a candidate board, is not one: its `/jobs` page is a compute product, and it hires through Workable, so its roles arrive through a Workable adapter if it is in the registry.

### Aggregators and boards

| Source | Access, as read on 2026-10-04 (2026-10-03 or 10-04 UTC) | Value evidence | Verdict |
|---|---|---|---|
| **Himalayas** (live) | Free, keyless browse and search endpoints; search filters by `country`, `worldwide`, `seniority`, employment type; `pubDate`, `expiryDate`, `locationRestrictions` with an empty array meaning worldwide, `timezoneRestrictions`; 20 jobs a request; 429 on abuse; data "cached and refreshed every 24 hours"; a visible link back and naming Himalayas required; building apps permitted; submitting its jobs to Jooble, Neuvoo, Google Jobs or LinkedIn Jobs forbidden. Strong | Genuineness not established; its apply link goes through a Himalayas page | Keep. The 24-hour claim does not describe the search endpoint, measured 2026-10-03 (ADR-0048) |
| **HN "Who is Hiring"** | Algolia API keyless, `created_at` per item; Hacker News' own Firebase API has `/v0/jobstories`, carrying Y Combinator companies' job posts, and states no rate limit. Strong | Posts written by people at the hiring company, usually linking to the employer's ATS. Anecdotal. The monthly Freelancer thread stopped after October 2025, read from the `whoishiring` account's posts | Second wave. Free text, so parsing is the cost, and a monthly thread is fresh for its first week or two |
| **Jobicy** | 1 to 200 jobs a request, no key, polling no more often than hourly, `geo` filter, only the last seven days returned, a **3-hour** publication delay; Jobicy named as source and its URL kept; the employer's own apply URL only with a paid key. Strong | Not established | Second wave. The apply link passes through Jobicy unless the posting names the employer's own page |
| **We Work Remotely** | Public RSS, "anyone can use the feed" with links attributed back; eleven category feeds. Strong | Not established. One third-party report of 25 items in the programming feed, newest about two weeks old. Weak | Second wave, after its volume is counted |
| **RemoteOK** | Keyless JSON; the first element is a legal notice requiring a followed link back and naming Remote OK, on pain of suspension; no non-commercial restriction on its API or legal page (updated 2026-07-20). Strong. **Measured** 2026-10-04 (2026-10-03 or 10-04 UTC) in a browser: 99 jobs, dated 2026-07-30 to 2026-10-02, with no paging | One sampled posting was an unrelated cabin-crew role. Anecdotal | Second wave. Ninety-nine postings over two months is a slow feed |
| **foorilla** (formerly ai-jobs.net, then aijobs.net) | The rename chain is confirmed: by July 2025 aijobs.net announced it would shut after 1 August and pointed to foorilla, run by foorilla LLC in Zürich. Every aijobs.net and ai-jobs.net path, the old JSON API included, now redirects to foorilla.com. foorilla's API needs a PRO+ subscription at $64 a month; its terms forbid bots and scrapers without permission. Strong | Whether the old board took only paid postings: not verifiable | Out on cost. Pass 0003's best topical fit no longer exists in the form 0003 read |
| **Remotive** | Jobs "delayed by 24 hours"; more than two requests a minute blocked; four calls a day recommended; its jobs may not be passed to Jooble, Neuvoo, Google Jobs or LinkedIn Jobs or shown to collect sign-ups; endpoint moved to `remotive.com/api/remote-jobs`. Strong | Feed size 16 and 17 jobs in September 2026, from third parties. Weak | Out: every posting reaches him at least a day late, past Measure A's 24-hour median target (ADR-0015), whatever its size. Whether its `publication_date` is the date before the delay is not established |
| **hiring.cafe** | Now `hiringcafe.com`. No official API; robots permits `/jobs` paths; terms forbid republishing or redistributing its content. Strong | Not established | Out: no endpoint. It aggregates employer ATS boards, which the ATS adapters read directly |
| **Y Combinator Work at a Startup** | No API; robots permits everything; terms silent. Strong for absence as far as checked | Not established | Out: no endpoint. Hacker News' `/v0/jobstories` is the nearest permitted route to YC companies' posts |
| **Welcome to the Jungle** (formerly Otta) | Terms effective 2026-04-27 forbid robots that scrape; its developer API is token-gated for employers. Strong | Not established | Out |
| **Wellfound** | Terms forbid automated load beyond a person browsing; robots disallows its job paths. Strong | Not established | Out |
| **Rozee.pk** | Privacy policy, "Use of Material": use "in a networked computer environment for any purpose is prohibited"; its terms page returns 404; robots permits the job and listing paths. Strong. Rozee won an interim order from the Intellectual Property Tribunal, Lahore, against RightJobs for copying its postings, reported 26 September 2016. Moderate | Rozee sells employers search access to the CVs in its database, $250 a month for 2,000 CVs. Strong, Rozee's own price page; that every applicant's CV is in that database is an inference | Out for automated use; by hand only |
| **Mustakbil** | Terms updated May 2026 forbid users to scrape, crawl or harvest by automated means, or to bypass technical protection. Strong | Not established | Out for automated use |
| **Bayt** | Terms effective 2026-04-07, clause 6.5.10, forbid spiders, robots and agents. Strong | Pakistan coverage not established | Out |
| **Adzuna** | 19 countries in its API specification; Pakistan is not one. Strong | n/a | Out: no Pakistan market |
| Arbeitnow, Working Nomads, Remote.co, JustRemote, The Muse, Findwork, Jooble | Not re-read in this pass | Not established | Unchanged from pass 0003; none is a candidate until it passes the access gate on its own documentation |

## What is known about ghost jobs and scams

**No official statistics exist.** CRS In Focus IF12977, "'Ghost' Job Postings", version 2 of 25 April 2025, by Elizabeth Weber Handwerker and Alexander H. Pepper of the Congressional Research Service. It also notes that the private estimates come from firms that sell hiring services, with varying disclosure of method. Strong.

**Every prevalence figure found is a vendor's or a preprint's, and they measure different things**, so none can be compared with another:

| Figure | What it measures | Grade |
|---|---|---|
| Greenhouse, December 2024: 18 to 22% of jobs on its platform each quarter "classified as ghost jobs" | Undefined; "internal data", no rule given | Weak, vendor without method |
| Greenhouse industry rates, construction 38%, art 34%, legal 29% | From press coverage of January 2025, not the December release | Weak |
| Hunter Ng, Baruch College, arXiv 2410.21771: 56,559 of 269,347 Glassdoor interview reviews (21%) flagged | Reviews showing a ghost-hiring signal, not job ads. Labels from GPT-4o on 2,000 reviews, then a fine-tuned BERT, with no validation accuracy reported; a keyword method gave 1.3%. Highest at firms of 1,001 to 5,000 staff and in publishing, internet and software | Weak, unreviewed preprint, highly sensitive to method |
| Revelio Labs, 2023: about 0.75 hires per posting in 2018, below 0.5 in 2023 | Postings with no matching hire within six months; the same blog names labour shortage and uncertainty as other causes | Weak, vendor with partial method |
| Unlisted.careers, September 2026: 28.0% of 668,355 postings from 15 ATSs open more than 90 days; Lever 48.4%, Workday 18.5% | Posting duration, from employer ATS feeds only | Weak, vendor with stated method |
| ResumeUp.AI 27.4% of LinkedIn; MyPerfectResume about 30 to 33% | A posting older than 30 days; JOLTS openings on one day against a month of hires | Not usable; the second method does not measure unfilled postings at all |

**The St. Louis Fed working paper "The Dual Beveridge Curve"** (2022-021) cites the over-20% figure only in its revision of 29 September 2026, from Ng and the CRS note, and measures nothing about ghost jobs itself.

**Phantom vacancies are a recognised economic object.** Albrecht, Decreuse and Vroman, "Directed search with phantom vacancies" (IZA DP 13704), calibrate already-filled advertisements living about 1.4 months; Chéron and Decreuse, "Matching with Phantoms", Review of Economic Studies 84(3), 2017, is the peer-reviewed theory. Neither compares channels. Moderate.

**Scams are counted, by complaint.** FTC Consumer Sentinel: reported losses to job and employment agency scams rose from $90 million in 2020 to $501 million in 2024, and reports nearly tripled; an FTC business blog of September 2025 gives over 105,000 reports and over $513 million for 2024. Self-reported and unverified by the FTC's own description, United States only. Strong as a count of complaints. In Pakistan, the FIA (December 2025) and the Bureau of Emigration and Overseas Employment with the FIA (May and September 2026) warned of fake IT and call-centre offers abroad, reported by Pakistani outlets; none names a job board. Moderate.

**Applying through the employer.** CareerPlug's 2025 report, an ATS vendor over about 60,000 mostly small businesses: careers pages produced 13.1% of applicants and 26.8% of hires, job boards 61.3% and 43.3%, about 2.9 times the hires per applicant for careers pages by arithmetic on its shares; source attribution unstated. Weak, vendor, small-business sample.

## Signals the project can measure itself

Genuineness per source, which no public study supplies, can be estimated from what the pipeline already stores:

1. **How long a posting stays up**, first seen to last seen or closure, per source and per employer.
2. **Reposting**: the same employer, normalised title and place reappearing under a new identity or a reset date. Ashby's `publishedAt` makes this matter most there. ADR-0052's repost research found 57 of 560 employer-and-title pairs on the employer boards carrying more than one publication date, and ADR-0050's closure measurement found twelve Greenhouse postings leaving their boards and returning after 23 to 130 hours. Not `updated_at`, which Greenhouse stamps in bulk (ADR-0018).
3. **Postings that never close** within 60 and 90 days.
4. **Cross-source date agreement**: an aggregator's date against the employer board's for the same role, which shows lag or a refreshed date.
5. **Expiry kept**: whether a Himalayas posting leaves at its `expiryDate`.
6. **Where the apply link lands**: the employer's ATS or an intermediary.
7. **His own outcomes**, deferred in `docs/deferred/response-quality.md`.

**No threshold for "too long open" is established.** The research run cited 90 and 180 days, and 25% and 10% of postings past them, to a 2025 Equitable Growth working paper; verification found none of those figures in it. Thresholds come from this project's own distributions, per source, once there is enough data to state them with a count.

## What verification changed

| Claim as the research run stated it | What the primary source shows |
|---|---|
| Manatal: V1 and V2 dead from 7 February 2025, so the V3 endpoint must be used | The notice concerns the authenticated Open API. The current career-page API is itself labelled v1, at `api.careers-page.com` |
| SmartRecruiters rests on third-party documentation | Its own specification allows unauthenticated reads of public postings |
| Greenhouse AI fields appear in the job object | Only on the single-job endpoint |
| Jobicy delays postings 6 hours (also pass 0003) | 3 hours |
| RemoteOK is non-commercial only, about 100 newest | No such restriction on its API or legal page; 99 jobs measured |
| Remotive allows no more than four calls a day | Recommended, not a cap; more than two a minute is blocked |
| aijobs.net "will be no more after August 1st" | Not the wording; the banner said it would shut after 1 August 2025. The claim's substance holds |
| foorilla's API terms unverified | Paid, $64 a month, and its terms forbid bots without permission |
| Rozee's court order was in 2017 | September 2016 |
| Rozee lists about 22 reported companies | No such page found |
| Mustakbil says it uses technical means against robots | Its terms forbid users to scrape; they say nothing of Mustakbil's own measures |
| Bayt's clause 4(j) | Clause 6.5.10, terms effective 2026-04-07 |
| Greenhouse's industry rates are in its December 2024 release | They come from coverage in January 2025 |
| Ng's paper shows up to 21% of job ads are ghosts | 21% of interview reviews carry a signal, by an unvalidated classifier |
| Equitable Growth paper: 25% of postings up past 90 days, 10% past 180, UK 17 to 18 days, Austria 30.5 | None of these figures appear in it |
| FTC: about 38,000 reports in 2020 | The FTC states "nearly tripled"; the 38,000 figure appears only in press coverage |

## Corrections to earlier passes

**Pass 0003, ai-jobs.net.** Its JSON API and RSS no longer exist; every path redirects to foorilla.com, whose API is paid. The board had announced its shutdown by July 2025, before 0003 recommended it on 2026-09-10. Whether its endpoint still answered on that date is not settled: 0003 does not say it requested it, and a third-party scraper dates the redirect to about 3 September 2026 (weak). Stale at the least, possibly wrong when written.

**Pass 0003, Jobicy's delay.** Three hours, not six, on 2026-10-04 (2026-10-03 or 10-04 UTC). Possibly changed since, possibly misread then.

**Pass 0003, Rozee's terms.** 0003 found no automated-access clause in the terms and said the privacy policy was not fully reviewed. The privacy policy prohibits use of Rozee's material in a networked computer environment. This settles the question 0003 left open, against automated use.

**Pass 0003, Adzuna** said roughly 20 markets with no Pakistan; the specification lists 19, none of them Pakistan. Consistent.

## Gaps only the project's own data can close

- Each source's genuineness: the signals above, per source, with counts.
- Response and time to first response by source, for an applicant in Pakistan: his own outcomes, deferred.
- Each feed's share of roles he can take: AI, entry level, at most three years, open to Pakistan.
- Which ATS platforms his registry's employers use, and how many postings he can take each platform yields.
- Whether each second-wave feed's weak claims hold.

## Caveats

- Several primary pages show no date: We Work Remotely, Remotive, Jobicy's GitHub page, Adzuna's terms.
- "Absent" for an API means not found on the official pages, robots files and terms read, plus a search. It is not proof that none exists.
- Most measured ghost-job evidence is from the United States and need not hold for remote roles open to Pakistan.
- No vendor's general terms of service were read for the four ATS platforms.

## Sources

| Source | Kind | Used for |
|---|---|---|
| Ashby, Workable, SmartRecruiters, Manatal, Greenhouse developer documentation; Lever's postings-api README; Breezy's developer documentation | Primary, platform | Endpoints and date fields |
| Himalayas API reference, current as of 2026-10-03; Jobicy feed page and GitHub; We Work Remotely RSS page; RemoteOK API and legal page; Remotive API page and GitHub; foorilla API schema, terms and privacy policy; aijobs.net archive of 2025-07-24 | Primary, board | Access, terms, prices |
| Algolia HN API; Hacker News Firebase API | Primary | Access |
| Rozee.pk privacy policy, robots.txt and price page; Mustakbil terms; Bayt terms; Welcome to the Jungle terms; Wellfound terms and robots; hiringcafe.com terms and robots; workatastartup.com robots; Adzuna API specification and terms | Primary, board | Access and terms |
| Express Tribune and ProPakistani, 26 September 2016 | News | Rozee's court order |
| CRS In Focus IF12977, v2, 2025-04-25 | Official | No official statistics on ghost jobs |
| FTC consumer alert of 2025-03-10 and business blog of September 2025; Consumer Sentinel | Official | Job scam complaints |
| Daily Times, 2025-12-04; Daily Pakistan, 2026-09-22; APP, 2026-05-17 | News of official warnings | Pakistan scam warnings |
| Ng, arXiv 2410.21771 | Preprint | Ghost-hiring signals in reviews |
| Cheremukhin and Restrepo-Echavarria, St. Louis Fed WP 2022-021, revised 2026-09-29 | Working paper | Citation only |
| Albrecht, Decreuse and Vroman, IZA DP 13704; Chéron and Decreuse, Review of Economic Studies 2017 | Working paper; peer-reviewed | Phantom vacancies |
| Sun, Akartuna and Manning, Trends in Organized Crime, May 2026 | Peer-reviewed review | Gap in comparative data |
| Greenhouse blog, 2024-12-10; Revelio Labs, 2023-10-31; Unlisted.careers, September 2026; CareerPlug 2025; ResumeUp.AI; MyPerfectResume | Vendor | Graded weak or unusable above |
| Apify listings, GitHub issues, metaintro and antoniocortes blogs, cited by the research run | Third party | Leads only; nothing here rests on them |

## Corrections

| Date | Correction | Source |
|---|---|---|
| 2026-10-05 (2026-10-04 UTC) | Four statements narrowed and one scope stated: Remotive's delay stated against its own postings, since Measure A is one median over all postings (ADR-0015); Manatal's date marked as filtered on, not shown on each posting; Himalayas' eligibility claim narrowed, since Jobicy gives a region; Rozee's CV sale narrowed to what its price page shows; and the opening paragraph now says this table records claims found wrong, as 0003's does | An independent audit of this pass, 2026-10-05 (2026-10-04 UTC). Each claimed more than its source shows |
| 2026-10-09 | Workable's `published_on` and `created_at` are defined, as the publication date and the creation timestamp; this pass said neither was. Manatal's postings carry no date; this pass gave `created_at` as each posting's date, a field that belongs to the employer's account. Both wrong when written, and corrected in the platforms table | The implementing seat's check of this pass on 2026-10-04 (Brief 10, item 2): Workable's reference updated 2025-06-10, Manatal's updated 2026-05-07; and its recount of 2026-10-07, 640 distinct Manatal postings read |
