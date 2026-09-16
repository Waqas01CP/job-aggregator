---
type: research
description: Pass 0003. Survey of free, pollable job board and aggregator APIs. Six keyless feeds recommended; Rozee.pk has no API path.
status: current
---

# Research 0003: Job source survey

Run 2026-09-10. Findings reflect that date and nothing later. Quotas, terms and endpoints change; reconfirm before relying on any figure here.

**Question asked.** Which job aggregators and job boards expose a free, pollable endpoint that would extend coverage beyond the 53 employer ATS boards already in the registry?

**Four gates each candidate was assessed against.** A machine-readable endpoint pollable on a schedule. Coverage of a lane the operator can be hired in. Terms permitting automated polling at a low rate. A publication date field, without which Measure A is uncomputable for those rows.

## Verdict

Six aggregators pass all four gates: Jobicy, Himalayas, Arbeitnow, RemoteOK, We Work Remotely, ai-jobs.net. All keyless, all dated, all carrying AI and software roles. Remotive and Working Nomads are a viable second wave.

Rozee.pk, the dominant Pakistani board and the largest known coverage gap, has no API path at all.

## Summary table

| Source | Endpoint | Free quota | PK on-site | Remote usable from PK | ToS permits polling | Publication date | Overlaps existing ATS |
|---|---|---|---|---|---|---|---|
| Jobicy | open JSON + RSS | unlimited, no key, max 1/hr, 6h delay | No | Yes, geo filter | Yes, attribution, no redistribution | `pubDate` | Minimal |
| Himalayas | open JSON + RSS | unlimited, no key, 24h cache, 429 if abused | No | Yes, restriction fields | Yes, attribution | `pubDate` epoch seconds | Minimal |
| Arbeitnow | open JSON | unlimited, no key | No | Yes, `remote` flag | Yes, public API | creation timestamp, verify name | **Yes** |
| RemoteOK | open JSON + RSS | unlimited, no key | No | Yes, parse `location` | Yes, attribution | `date` + `epoch` | Minimal |
| We Work Remotely | RSS | unlimited, no key | No | Yes, body text only | Yes, attribution | RSS `pubDate` | Minimal |
| ai-jobs.net | open JSON + RSS | unlimited, no key, 200 items, ~2h refresh | No | Yes | Yes, redistribution allowed | `pubDate` in RSS | Minimal |
| Remotive | open JSON | unlimited, no key, 24h delay | No | Yes | Yes, but no redistribution | `publication_date` | Minimal |
| Working Nomads | undocumented JSON | unlimited, needs UA header | No | Yes | **Unclear** | `pub_date` | Minimal |
| Adzuna | free-key JSON | ~1,000 calls/month | No PK market | Partial | **Caveat, see below** | `created` | Some |
| Reed.co.uk | free-key JSON | free key, UK only | No | Partial, UK | Yes | `date` | Some |
| The Muse | open JSON, key optional | 500/hr keyless, 3,600/hr keyed | No | Some | Yes | `publication_date` | Minimal |
| Findwork.dev | free-key JSON | 60 req/min | No | Yes | Yes | `date_posted` | **Yes** |
| USAJobs | free-key JSON | fair use | No | No, US federal only | Yes | `PublicationStartDate` | No |
| Jooble | free-key JSON | **500 requests lifetime per key** | via PK domain | Yes | quota kills polling | Weak | Some |
| HN Who is Hiring | open JSON via Algolia | unlimited, no key | No | Yes, free text | Yes | `created_at` | No |
| Rozee.pk | **none** | n/a | **Yes, only source** | Some | **Unverified** | listing pages only | No, net-new |
| Indeed / Indeed PK | none, retired 2023 | n/a | Yes | n/a | Partner-gated | n/a | n/a |
| Bayt / Naukrigulf | none free | n/a | Yes | Some | Unclear | n/a | n/a |
| Mustakbil / BrightSpyre | none found | n/a | Yes | No | Unclear | n/a | n/a |
| Glassdoor / LinkedIn / Wellfound / Otta / Dice / YC WaaS | none public | n/a | varies | varies | **ToS prohibits** | n/a | n/a |
| FlexJobs | none, paid | subscription | No | Yes | n/a | n/a | n/a |

## Recommended tier

**Jobicy.** `https://jobicy.com/api/v2/remote-jobs`, params `count` (default 200), `geo`, `industry`, `tag`, `search`. Taxonomy at `?get=industries` and `?get=locations`. Publication date is `pubDate`. First-party guidance says a few times daily suffices and must not exceed once per hour; postings are delayed 6 hours so Jobicy is credited as source. Attribution and canonical URL required, redistribution to other job boards prohibited. A Hugging Face dataset `jobicy/remote-jobs` mirrors the feed as daily JSONL, a free alternate path.

**Himalayas.** Best documented of the set. Browse `https://himalayas.app/jobs/api`, cursor pagination, limit 20. Search `https://himalayas.app/jobs/api/search` with `q`, `country`, `worldwide`, `seniority`, `employment_type`, `company`, `timezone`, `sort`, `page`. OpenAPI spec at `https://himalayas.app/docs/openapi.json`. Carries `pubDate` as **epoch seconds**, plus `expiryDate`, `guid`, `locationRestrictions[]`, `timezoneRestrictions[]`, salary fields. Documentation states data is cached and refreshed every 24 hours so there is no benefit to polling more often, and returns 429 if abused. Attribution required; building apps and databases explicitly permitted. `locationRestrictions`, empty array meaning worldwide, is the closest thing available to an eligibility field.

**Arbeitnow.** `https://www.arbeitnow.com/api/job-board-api`, params include `visa_sponsorship=true`. UK variant at `arbeitnow.co.uk`. Documented via Postman at `documenter.getpostman.com/view/18545278/UVJbJdKh`. Carries a creation timestamp plus `slug`, `remote` boolean, `job_types`, `tags`, `location`, `url`. Feed updates hourly. **Overlap flag: its source is ATS-fed, naming Greenhouse, SmartRecruiters, Join.com, Team Tailor, Recruitee and Comeet, so part of this feed duplicates boards already polled directly.**

**RemoteOK.** `https://remoteok.com/api`, RSS at `https://remoteok.com/remote-jobs.rss`, tag filter `?tag=dev`. Carries `date` ISO 8601 and `epoch`, plus `position`, `company`, `tags`, salary range, `location`. **The first element of the JSON array is a legal notice object, not a job. Skip index 0.** First-party help confirms the feeds are free and require no authentication. No published numeric rate limit.

**We Work Remotely.** RSS only. All jobs at `https://weworkremotely.com/remote-jobs.rss`; category feeds at `/categories/remote-programming-jobs.rss`, `remote-back-end-programming-jobs.rss`, `remote-full-stack-programming-jobs.rss`, `remote-devops-sysadmin-jobs.rss`. Standard RSS `pubDate`. First-party terms: anyone can use the feed, attribution back required. No AI category, so filter on title. Region restrictions appear in body text rather than a structured field, which is a weaker eligibility signal than Himalayas or Jobicy.

**ai-jobs.net.** Best topical fit for the target titles. JSON at `https://ai-jobs.net/api/list-jobs/`, most recent 200, refreshed roughly every 2 hours. RSS at `https://ai-jobs.net/feed/`, most recent 100. RSS carries `pubDate`; the JSON carries more fields including company and salary. Terms are unusually permissive and explicitly allow republishing on another job board. Exclusively AI, ML, data science, NLP, computer vision and data engineering. Paid-posting board so volume is moderate.

**Second wave.** Remotive at `https://remotive.com/api/remote-jobs`, no key, `category`, `search`, `limit`, carries `publication_date`, 24h delay. Its terms prohibit submitting its jobs to third-party websites and threaten termination; private ingestion is within intent, republication is not. Working Nomads at `https://www.workingnomads.co/api/exposed_jobs/`, undocumented but public, requires a browser User-Agent header, carries `pub_date`. No published terms grant, so treat as unclear.

## Free-key tier

**Adzuna.** `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}` with `app_id` and `app_key`. Roughly 20 markets including UK, US, Germany, India, Australia, Canada. **No Pakistan market.** Free quota approximately 1,000 calls a month. Publication date present as `created`.

**Terms caveat, and it is a real one.** Adzuna's terms state that use by a commercial, government or academic organisation is permitted subject to a 14 day trial period, and that the data may not be used in original format or in aggregation to deliver ongoing work or research without written consent, after which a licence may be required. A personal non-commercial pipeline is defensible; ongoing aggregation arguably triggers the clause. Read the terms before depending on it.

**Reed.co.uk.** `https://www.reed.co.uk/api/1.0/search`, free key at reed.co.uk/developers, HTTP Basic with key as username. UK only. Carries `date` and `expirationDate`.

**The Muse.** `https://www.themuse.com/api/public/jobs?page=N` plus `category`, `location`, `level`. Documentation states 500 requests per hour without a key, up to 3,600 with a free one, with rate headers returned. Carries `publication_date`. Mostly US and curated employers, no AI category.

**Findwork.dev.** `https://findwork.dev/api/jobs/`, header `Authorization: Token`, free key, 60 requests per minute, sorted by `date_posted`. **Aggregates HN, RemoteOK and We Work Remotely, so it overlaps sources already ingested.**

**USAJobs.** `https://data.usajobs.gov/api/search`, free key by email, requires `User-Agent` set to the registered email plus `Authorization-Key`. Carries `PublicationStartDate`. US federal only, so almost never eligible from Pakistan. Low relevance.

## Hacker News Who Is Hiring

`http://hn.algolia.com/api/v1/search_by_date?tags=comment&query=...` plus item fetch at `/api/v1/items/{id}` to pull the monthly thread's comment tree. No key, free. Every comment carries `created_at` and `created_at_i`. High-quality startup and AI roles, many remote, but each posting is free text in a comment, so title, company and location must be parsed. Parsing overhead is the cost.

## Rejected, with the gate that failed

**Indeed and Indeed PK.** Endpoint. Publisher API discontinued 2023. The only current official surface is an employer-side GraphQL Job Sync API for ATS partners, which publishes and expires jobs rather than reading them, with no self-serve key. Organic single-source XML feeds being retired 31 March 2026.

**Glassdoor.** Endpoint. Public API discontinued, partner-only.

**LinkedIn Jobs.** Endpoint and terms. No free public jobs API; Jobs API partner-gated; scraping violates terms.

**Wellfound.** Endpoint. No free public jobs API; GraphQL behind auth and anti-bot.

**Y Combinator Work at a Startup.** Endpoint. No documented public API, login-gated.

**Otta, Dice.** Endpoint. No free public API.

**FlexJobs.** Cost. Subscription product.

**Jooble.** Quota. First-party help states the free REST API plan includes a total lifetime limit of 500 requests per key, an absolute lifetime quota rather than monthly, and each country domain needs its own key. That makes it single-use, not a recurring poll source.

**Bayt, Naukrigulf, Mustakbil, BrightSpyre.** Endpoint. No free machine-readable feed found; only paid third-party scrapers.

**Apify and RapidAPI listings for RemoteOK, Rozee, Bayt, Reed, The Muse.** Cost. These are paid pay-per-result scrapers, not the underlying sources. Go to the source directly where one exists.

## Unclear, and what would settle it

Arbeitnow's exact date field name and format: verify against the live Postman documentation on first ingest.

Working Nomads terms: the endpoint works and is dated, but no explicit permission for automated access is published. Read their terms page.

Mustakbil, BrightSpyre, Naukrigulf, JustRemote, Remote.co, NoDesk, DailyRemote, Jobspresso: presence or absence of a free feed could not be confirmed. Fetch each site's `/feed`, `/rss` and `/api` directly.

ai-jobs.net JSON date field name: RSS has `pubDate`; confirm the JSON equivalent on first pull.

Rozee.pk robots.txt: could not be retrieved. Must be checked with a direct request.

## Rozee.pk

The dominant Pakistani board. Self-described as carrying more than 100,000 jobs in Pakistan from more than 52,000 companies, with roughly 9.5 to 10 million registered professionals per its own and Workable partner copy. It is the single largest Karachi on-site gap in the current source list, and the finding is negative on every automated-ingestion gate.

**Endpoint: fail.** No RSS, no Atom, no public JSON API, no XML export, no developer or partner API programme found. Searches for a Rozee RSS feed return ordinary HTML search pages, not a feed. The employer side sells manual job-posting packages, not a data API. The only machine access anyone uses is scraping, evidenced by a public Puppeteer and Cheerio scraper on GitHub and a paid Apify actor. Rozee appears in Workable's partner directory only as a distribution channel for Workable ATS customers, not as a queryable API.

**Terms: partially established, and not enough to act on.** Rozee's Terms and Conditions page contains no clause mentioning scraping, crawling, robots, automated access or data harvesting; the only third-party clause is a liability disclaimer. Page-level meta on job and search pages is permissive, and search paths are indexed by Google in practice, indicating they are crawlable. **However the literal robots.txt could not be retrieved and verified, and a fuller login-gated terms document and the privacy policy were not fully reviewed. Do not assume permission until robots.txt is read directly.**

**Publication date.** Listing pages display posting dates, so a scraper could capture them, but with no structured feed there is no guaranteed machine-readable field.

**Overlap: none.** This is net-new Pakistan inventory, which is exactly why it matters.

**Verdict.** There is no free, terms-clean, pollable API path to Rozee. The options are a low-rate robots-respecting scraper built and maintained by the operator, accepting the maintenance cost and requiring robots.txt verification first, or accepting the Pakistan on-site gap and relying on aggregators for the remote half of the profile. No aggregator with a free API is confirmed to carry Rozee's listings.

## Thresholds that would change the recommendation

A source returning 429, or Adzuna calls approaching the monthly cap: back off to weekly or drop.

Rozee's robots.txt disallowing the job or search paths: do not build the scraper, and the on-site gap stays open.

Publishing the table publicly at any point: revisit Remotive and Jobicy compliance, since both explicitly threaten termination for redistribution.

## Caveats

Publication date fields exist for every recommended source, but exact JSON keys for Arbeitnow and ai-jobs.net must be validated against the live payload on first ingest.

Remote does not mean eligible from Pakistan. Himalayas carries `locationRestrictions` and `timezoneRestrictions`, Jobicy carries a geo field, RemoteOK often carries "USA Only" inside `location`. These are the only structured eligibility signals available anywhere in the survey.

Listicle sources were treated as unverified and cross-checked against first-party documentation wherever possible. Where only third-party evidence exists, including the Working Nomads endpoint and some quota figures, it is flagged above.

All quotas and counts are current as found on 2026-09-10 and should be reconfirmed at integration time.

## Corrections

| Date | Correction | Source |
|---|---|---|
| 2026-09-15 | Himalayas `pubDate` was recorded as ISO 8601. It is epoch seconds | Measured directly against the live endpoint during the endpoint feasibility spike. The original came from documentation reading rather than from a request |
| 2026-09-15 | Himalayas `sort=recent` on the search endpoint does not order by date and silently ignores the cursor, returning byte-identical responses | Measured. Ordering broke at positions 3, 5 and 8. The browse endpoint does order newest-first and pages cleanly, 60 of 60 guids distinct across three pages |
| 2026-09-15 | The envelope's `updatedAt` is not a cache timestamp | It equals the newest `pubDate` on whatever page is returned, on 8 of 8 observations. The first spike inferred it was cache age and that inference was repeated in discussion |
