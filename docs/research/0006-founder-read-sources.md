---
type: research
description: Pass 0006. Sources where a founder or an engineer reads the application, for an agentic AI graduate in Karachi. Three outside research reports, two by Gemini and one by Claude's research tool, each decisive claim tested against the source's own pages on 2026-10-20 by trying to falsify it. Python.org, Hasjob, CryptoJobsList and Startup.jobs' API stand; most others fall.
status: current
---

# Research 0006: Founder-read sources

Run 2026-10-20 UTC. The operator's question, from his conclusion of 2026-10-18 that recruiters screen him out on years where founders and engineers would read for skill (ADR-0063's Context): which further sources reach the people who read for skill, and can be integrated?

**Method, his.** An outside research run produces a report; the architecture chat checks each claim by trying to falsify it, against evidence no staler than the claim's own. In his words: "in checking, i think the falsifying approach of checking would be better as this might give better yield than you just affirming that what the report says is correct or not." Three reports were read end to end:
1. Gemini, on the chat's first prompt: "Unmediated Remote Job Sources for Junior Agentic AI and LLM Engineers in Pakistan", 406 lines as text.
2. Claude's research tool, on a revised prompt carrying his filters, the integration rules and the measured bar: "Founder-read job sources for a Karachi AI/LLM graduate", 116 lines.
3. Gemini, on the same revised prompt: "Programmatic Job Source Evaluation for Direct-to-Founder AI and Python Engineering Roles", 529 lines as text.

Every verdict below rests on the source's own page read by the chat on 2026-10-20, not on a report, but one: Arbeitnow, JoinRise, FindWork and Dover, out on the reports' own accounts. A report's claim that the chat did not test is marked as untested.

## Verdict

| Source | Verdict | Why |
|---|---|---|
| Python.org job board | Measure, then build | 21 dated postings on its pages, 2026-07-23 to 10-14, about 1.75 a week; RSS at `/jobs/feed/rss/`, whose 20 items, read 2026-10-20, carry no date of any kind, only a title, link, description and identifier; robots leave `/jobs/` open; Legal Statements (2024-12-10) silent on automated reading. Of its 8 worldwide postings, one is an agency, one routes through an AI interview, one asks senior years, and one employer's three listings are one role; about two founder- or engineer-read roles near his level in twelve weeks |
| Hasjob | Measure, then build | An Atom feed of 17 entries, 2026-09-21 to 10-19; its terms say nothing on automated reading. Founders' bylines on its postings and about one fit a month, India-centred, by reports 2 and 3, untested by the chat |
| CryptoJobsList | Build once he holds a key | A documented API, keys by application, free for "Most integrations that link back to CryptoJobsList job pages", with "High-volume or commercial use" priced individually; its terms page as read has no scraping clause. By report 1's own sample, 14 of 25 AI roles at larger crypto firms |
| Startup.jobs | Build through its API | Its terms forbid copying its content "(including RSS feeds), whether for commercial or non-commercial purposes", except through the API. The API terms (effective 2026-07-10) permit "Personal automations, bots, newsletters, and job-search tools that link back", need a free account key, and require fetched content "refreshed or deleted within seven days". Read again 2026-10-20, they also say that on termination "you will promptly destroy copies of any documentation and any other Startup Jobs" information, which "includes, but is not limited to, any job listings and company data accessed through the APIs", that the agreement may be ended "with or without cause, and without notice to you", and that "Our APIs and documentation are intended for use by businesses and organizations and not for consumer purposes", beside their permission for personal automations. Its Pakistan engineering page: 20 postings, 2026-09-21 to 10-09, mostly larger employers, two already in the registry. Its API, read 2026-10-20: live jobs from the last 14 days, newest first, 20 requests a minute, a key from any account. Built keeping postings beyond seven days, his decision (ADR-0063's Changes) |
| a16z Speedrun talent network | One read, for discovery | A public JSON feed of about 22,600 jobs at a16z portfolio companies; a source of employer boards for the registry, not of founder-read postings; its terms not found |
| Recruitee, Personio | Later, with employers | Proposed by reports 2 and 3 as further platforms. Whether Recruitee's offers endpoint needs a token is contradicted between its own pages; untested. Yield depends on employers found on them |
| Investor boards on Getro (Techstars and others) | By hand, with email alerts | Getro's API is a paid product, and the project reads no email (ADR-0012). The richest founder-heavy channel any report found; the roles checked state no country |
| Wellfound, Y Combinator Work at a Startup, Algora | By hand | Y Combinator's terms bar "any data mining, robots, scraping"; Wellfound's bar copying its content by "automated or non-automated harvesting"; Algora's bar any robot and any manual monitoring without consent. Each allows written permission or specific authorisation; his to pursue |
| FOSS Jobs | Out | 50 worldwide postings over 2024-08-12 to 2026-09-16, none an AI, ML or LLM role |
| Get on Board | Out | Its public API's Python search, read 2026-10-20: mostly hybrid roles in Santiago, one strictly fully remote, none fitting him. Report 3 ranked it second on 8 postings, 3 from one staffing firm |
| Lobste.rs | Out | Its hiring threads rest on one Ask MetaFilter comment; replies need an invited account; its robots rules refuse the chat's fetcher |
| Arbeitnow, JoinRise, FindWork, Dover | Out, on the reports alone | Near zero for Pakistan by report 1's own account; large-company inventory; a login for the key; no public feed. Untested by the chat: the one verdict here that rests on the reports |

## Where the reports diverged, and which was right

- **Startup.jobs.** Report 2 sampled its Pakistan engineering page and recommended it first; report 3 sampled its general home page, full of NGO tenders and Korean roles, and found nothing. Report 2 sampled the right slice. Both called the keyless RSS usable; its terms forbid it, a clause neither report quoted. Report 3 quoted the terms as allowing non-commercial republishing; that sentence is not on the page as read on 2026-10-20.
- **Get on Board.** Report 2 dropped it as Latin American; report 3 ranked it second. Report 2 was right.
- **Hasjob.** Reports 2 and 3 give the same counts. Report 3 went further, finding that one posting tagged "Anywhere" is for Indian citizens on site.
- **Method.** Report 2 says plainly what it could not read. Reports 1 and 3 read more postings in full but write inferences as proof ("proves", "guarantees"); report 3 counts two example records in Recruitee's documentation as a yield of 0 of 2; report 1's counts render empty. Reports 1 and 3 rest some "primary" claims on scraper vendors and forums.
- **All three missed** Startup.jobs' RSS ban and its seven-day clause.

## Caveats

- A research pass samples; the implementing seat's measurement over the project's own rules decides yield, as it did for the second wave (the seat's report on Brief 15).
- Whether employers on Hasjob, in India, can contract with someone in Pakistan is not settled by any source read.
- Openness to Pakistan of the investor-board roles checked is unverified: they say "Remote" and name no country.
- Startup.jobs' own API page, read 2026-10-20, lists a keyless RSS feed of its 50 newest jobs beside the API, while its terms, read again that day, forbid copying its feeds "(including RSS feeds)" and except only "content accessed through our API in accordance with the Startup Jobs API Terms of Service". The build uses the keyed API, which the exception names; the API terms do not mention RSS.

## Sources

All read by the chat on 2026-10-20 unless dated otherwise.

| Source | Kind | Used for |
|---|---|---|
| python.org/jobs, /jobs/8133/, /jobs/8176/, /robots.txt; policies.python.org Legal Statements (2024-12-10); /jobs/feed/rss/ read 2026-10-20 | Primary | Postings, access, terms, feed |
| fossjobs.net/jobs-worldwide/ | Primary | Postings |
| cryptojobslist.com/api-access, /terms; /api-access read again 2026-10-20 | Primary | Access, terms |
| startup.jobs/terms, /terms/api (effective 2026-07-10), /api, /locations/pakistan/engineering; /terms, /terms/api and /api read again 2026-10-20 | Primary | Terms, access, postings |
| hasjob.co/feed, /tos | Primary | Feed, terms |
| getonbrd.com/api/v0/search/jobs?query=python | Primary | Postings |
| speedrun-talent-network.com/api/v1/jobs | Primary | Feed |
| jobs.techstars.com, two postings | Primary | Postings |
| wellfound.com/terms (updated 2020-06-05); ycombinator.com/legal; workatastartup.com/terms; algora.io/legal/terms (2021-08-17) | Primary | Terms |
| lobste.rs/t/job, /robots.txt | Primary, refused | Access |
| Reports 1 to 3 above, relayed by the operator | Outside research | Leads, and the one verdict marked as resting on them |

## Corrections

| Date | Correction | Source |
|---|---|---|
| 2026-10-21 | Hasjob's "about one fit a month", the reports' figure and marked untested here, is wrong for him: the implementing seat read all 17 postings, every one India's, the 4 "Anywhere" among them, and found none he can take; out on his decision (ADR-0063's Changes). Contradicted by that read of its feed, 17 postings of 2026-09-21 to 10-19; whether the reports' figure was wrong when written or the board changed is not settled by one read | The implementing seat's report on Brief 18 |
