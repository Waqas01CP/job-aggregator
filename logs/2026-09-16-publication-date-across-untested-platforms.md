---
type: log
description: Discovery spike across the thirteen untested ATS platforms. Whether each exposes a machine-readable endpoint and a publication date, with field names, formats and coverage.
status: current
---

# Publication-date presence across the untested platforms, 2026-09-16

Previous log: `2026-09-15-spike-followup-checks.md`.

| Header | Value |
|---|---|
| Date | 2026-09-16. Requests between 09:58:39Z and 10:16:31Z |
| Model | claude-opus-5 |
| HEAD | `26d0073` |
| Mode | **Read-only** against every endpoint. GET everywhere except one POST to Workday's search API, which is a query, not a write. No authentication sent anywhere. Wrote only `raw_responses/` (gitignored), the session scratchpad, this log, `logs/README.md`, `STATE.md`, and the frontmatter of the two earlier logs plus the regenerated `MAP.md` (item 54) |
| Commit status | **Uncommitted.** The brief forbids writes to any git branch and does not ask for a commit |
| Requests | **53 of the 60 permitted.** 7 unspent |

**Tags.** `[VERIFIED]` means exercised and observed this pass. `[BELIEVED]` means reasoned, not run. Unmarked means believed. **RECOMMENDATION** marks a recommendation, not a decision.

## Headline

**No platform returned nothing. There are zero NO ENDPOINT verdicts.** Every one of the thirteen exposes something machine-readable, though for six of them it is JSON embedded in an HTML page rather than an API.

**ADR-0007's assumption survives, narrowly and specifically.** It says "a material number of registry platforms expose no reliable publication date". One platform, **Manatal**, exposes a clean public JSON API and **no date field of any kind**, verified across two boards and 34 postings. Manatal is one of the two dominant platforms among Pakistani employers and holds 8 registry boards. That is the material case, and it is exactly where it hurts most.

| Platform | Verdict | Publication field | Format | Coverage | Board used |
|---|---|---|---|---|---|
| Ashby | **PROCEED** | `publishedAt` | ISO-8601 with offset | 21/21 = 100% | Overjet |
| Workable | **PROCEED** | `published_on` | ISO date, no time | 12/12 = 100% | igate-technologies |
| SmartRecruiters | **PROCEED** | `releasedDate` | ISO-8601 with offset | 9/9 = 100% | OneScreen |
| Breezy | **PROCEED** | `published_date` | ISO-8601 Z | 191/191 = 100% | comprehensive-rehab-consultants |
| Pinpoint | **PROCEED** via RSS | `pubDate` | RFC-2822 | 4/4 = 100% | emumba |
| BambooHR | **PROCEED** on detail | `datePosted` | ISO date, no time | 3/3 = 100% | abyss |
| Workday | INVESTIGATE | `startDate` on detail; `postedOn` is relative text | ISO date / English phrase | 4/4 detail | ContourSoftware-Careers |
| JazzHR | INVESTIGATE | `datePosted` in per-posting JSON-LD | ISO date, no time | 3/3 sampled | northbay |
| Freshteam | INVESTIGATE | `datePosted` in per-posting JSON-LD | `YYYY-MM-DD HH:MM:SS UTC` | 3/3 sampled | xgrid |
| Zoho Recruit | INVESTIGATE | `Date_Opened` in page-embedded JSON | ISO date, no time | 1/1 sampled | thephygital |
| iCIMS | INVESTIGATE | `datePosted` in per-posting JSON-LD, **suspect** | ISO-8601 Z | 3/3, all identical | pktechcareers-ibex |
| Dover | INVESTIGATE | none on the employer board; `date_posted` on the cross-client board | ISO-8601 Z | 0/103 employer, 100/100 cross-client | careerflow |
| Manatal | INVESTIGATE | **none found anywhere** | n/a | 0/34 | spursol, ahdus-technology-2 |

Requests per platform `[VERIFIED]`, from `probe_ledger.tsv`: ashby 1, breezy 1, smartrecruiters 1, workable 2, pinpoint 3, bamboohr 4, freshteam 5, icims 5, manatal 5, dover 6, jazzhr 6, zohorecruit 6, workday 8. Statuses across all 53: 200 x47, 406 x2, 404 x2, 401 x1, 410 x1.

## Method

`probe.py` in the scratchpad. The 60-request cap is enforced in code, read off `probe_ledger.tsv`, which is appended to before each response is used, so the count survives separate invocations `[VERIFIED]`. At least 2.5 s between requests. User-Agent `job-aggregator-spike/0.3 (one-off ATS endpoint discovery; read-only)`, no personal data.

Analysis reuses the date-scanning and field-population functions written for the 2026-09-11 spike and proven by `defeat_the_checks.py`, with two changes: the date-name regex was widened (spike 1 missed Greenhouse's `application_deadline` because "deadline" did not match), and the field-candidate lists were extended per platform. Value-based date detection runs alongside name-based detection, so a date-valued field is caught whatever it is called.

**Endpoints were derived, not guessed, wherever possible.** Manatal's API came from its own page's JavaScript (`apiBaseURL: ${baseUrl}/api/v1.0/c/${clientSlug}/`, then `+'jobs/?page_size='`). Dover's came from its published OpenAPI bundle. Workday's site name came from its own `robots.txt`. That is why 47 of 53 requests returned 200.

## Per platform

### Ashby: PROCEED

`https://api.ashbyhq.com/posting-api/job-board/Overjet?includeCompensation=true`, HTTP 200, no key, 364558 bytes `[VERIFIED]`. Shape: object with `apiVersion` and `jobs`; 21 postings.

- **`publishedAt`**, sample `'2025-09-08T21:06:38.959+00:00'`, parses to `2025-09-08T21:06:38.959+00:00`. Present and parseable 21/21 `[VERIFIED]`.
- **No other date field.** The scan flagged `shouldDisplayCompensationOnJobPostings` on the word "posting"; it is a boolean, 0/21 parseable. Named-but-not-a-date, reported so the absence is visible.
- title 100% (`title`), **employer 0%, no field exists**, URL 100% absolute (`jobUrl`), location 100%, description 100% (`descriptionPlain`).
- Sample: `title='Talent Pool at Overjet'`, `jobUrl='https://jobs.ashbyhq.com/Overjet/daca62f6-04e0-4485-b714-be3d47b11c1c'`.

Ashby is the Lever case again: no employer field on the posting. ADR-0026's provenance rule would apply unchanged.

### Workable: PROCEED

`https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true`, no key `[VERIFIED]`.

**First board was empty.** `creative-chaos` returned HTTP 200 and `{"name":"Creative chaos","description":null,"jobs":[]}`, 54 bytes. That is the board's state, not the platform's, so a second board was used, per the brief.

`igate-technologies`, 12 postings:

- **`published_on`**, sample `'2025-03-19'`, date only, no time. 12/12 `[VERIFIED]`.
- **`created_at`** also present 12/12, sample `'2025-03-19'`, the same value on the sampled posting. Reported, not treated as publication.
- title 100%, URL 100% absolute (`url`, e.g. `https://apply.workable.com/j/AB52417BEE`), location 100%, description 100%.
- **Employer 0% per posting**, but the response envelope carries `"name": "iGATE Technology"`. Employer is knowable from the response without derivation from the slug, which is a weaker version of the Lever problem.

### SmartRecruiters: PROCEED

`https://api.smartrecruiters.com/v1/companies/OneScreen/postings?limit=100`, HTTP 200, no key `[VERIFIED]`. Envelope `{offset, limit, totalFound: 9}`, postings under `content`, 9 returned.

- **`releasedDate`**, sample `'2026-08-13T05:07:11.914Z'`, 9/9 `[VERIFIED]`. No other date field of any kind.
- title 100% (`name`), **employer 100% (`company.name` = 'OneScreen')**, location 100%.
- **URL: no careers-page link field.** `ref` is present 9/9 and is absolute, but it points at the API: `'https://api.smartrecruiters.com/v1/companies/OneScreen/postings/744000143229669'` `[VERIFIED]`. A human-facing URL is constructible from `id`, which is derivation, not return.

### Breezy: PROCEED

`https://comprehensive-rehab-consultants.breezy.hr/json`, HTTP 200, no key, top-level array, **191 postings** `[VERIFIED]`.

- **`published_date`**, sample `'2026-07-28T20:48:09.357Z'`, 191/191 `[VERIFIED]`.
- title 100% (`name`), **employer 100% (`company.name`)**, URL 100% absolute, location 100% (`location.name`).
- Two fields matched the date-name regex on "friendly_id" containing "id"; both are strings like `'6d7b946dd06e-collaborating-physician'` and parse 0/191. Reported as scanner noise.

191 postings from a single board is worth noting against the volume picture from the last log, where the median board returned 27.

### Pinpoint: PROCEED, but not from the JSON list

Three surfaces, and they disagree `[VERIFIED]`:

| Surface | Publication date |
|---|---|
| `https://emumba.pinpointhq.com/postings.json` | **none.** 4 postings, keys include `deadline_at`, which is `null` on 0/4 |
| `https://emumba.pinpointhq.com/en/jobs.rss` | **`pubDate` on 4/4**, sample `'Tue, 28 Jul 2026 19:27:23 +0100'` |
| posting page JSON-LD | **`datePosted`**, `'2026-07-28T19:27:24+01:00'` |

The RSS link was discovered in the posting page's `<link rel="alternate">`. Had the spike stopped at `postings.json`, Pinpoint would read as "no publication date", which is exactly the failure the brief warned about.

The RSS `pubDate` and the JSON-LD `datePosted` for the same posting differ by one second, 19:27:23 against 19:27:24. Not investigated.

`postings.json` gives title 100%, URL 100% absolute, location 100%, description 100%, employer 0%.

### BambooHR: PROCEED, at one request per posting

- **List**: `https://abyss.bamboohr.com/careers/list`, HTTP 200, no key. 3 postings, keys `jobOpeningName`, `departmentLabel`, `location`, `employmentStatusLabel`, `isRemote`, `id`, `atsLocation`, `locationType`. **No date field. No URL field.** `[VERIFIED]`
- **Detail**: `https://abyss.bamboohr.com/careers/{id}/detail`, HTTP 200, no key. Carries **`datePosted`** and `jobOpeningShareUrl` `[VERIFIED]`:

| id | `datePosted` | Name |
|---|---|---|
| 266 | `'2026-06-19'` | Chief Product Officer |
| 274 | `'2026-09-04'` | Project Based Engineer |
| 275 | `'2026-09-04'` | Project Based Engineer (Isometrics) |

3/3, and the values differ, so they are per-posting data rather than a constant. Cost is 1 + N requests per board.

### Workday: INVESTIGATE

Hardest to reach, and it worked. The root URL returns **HTTP 406** with an empty body under two different `Accept` headers `[VERIFIED]`. The site name came from `https://talentmanagementsolution.wd3.myworkdayjobs.com/robots.txt`, which lists **163 sitemaps**, one per tenant site, including `ContourSoftware-Careers` `[VERIFIED]`.

- **List**: `POST /wday/cxs/talentmanagementsolution/ContourSoftware-Careers/jobs` with `{"appliedFacets":{},"limit":20,"offset":0,"searchText":""}`, HTTP 200. `total: 90`, 20 returned. Keys: `title`, `externalPath`, `locationsText`, `postedOn`, `timeType`, `bulletFields`.
- **`postedOn` is not a date.** It is English relative text, 20/20 non-empty, 8 distinct values: `'Posted Yesterday'`, `'Posted 2 Days Ago'`, `'Posted 5 Days Ago'`, `'Posted 6 Days Ago'`, `'Posted 7 Days Ago'`, `'Posted 8 Days Ago'`, `'Posted 12 Days Ago'`, `'Posted 13 Days Ago'`, `'Posted 14 Days Ago'` `[VERIFIED]`.
- **Detail**: `GET /wday/cxs/{tenant}/{site}{externalPath}`, HTTP 200, carries **`startDate`**, an absolute date `[VERIFIED]`:

| Posting | `postedOn` | `startDate` |
|---|---|---|
| Product Owner R54307 | Posted Yesterday | `'2026-09-15'` |
| Junior/Intermediate Software Developer R54206 | Posted Yesterday | `'2026-09-15'` |
| Data Engineer R54253 | Posted Yesterday | `'2026-09-15'` |
| HR Operations Intern R54144 | Posted 12 Days Ago | `'2026-09-04'` |

`startDate` tracks `postedOn` exactly: today is 2026-09-16, and 12 days back is 2026-09-04 `[VERIFIED]`.

**Why INVESTIGATE and not PROCEED.** The only absolute date is named `startDate`, which does not denote publication. It could as easily be the role's start date, and the brief forbids guessing which field means published. The arithmetic agreement above is strong evidence that it behaves as a posting date `[BELIEVED]`, but it is not proof. **What would settle it:** a second run. A posting that appears between two runs, whose `startDate` equals its first-observed date, settles it. The same two-run pass that ADR-0006 still needs would answer this at no extra cost.

Detail also carries `externalUrl` and a top-level `hiringOrganization`. The list carries neither a URL nor an employer, only `externalPath`.

### JazzHR: INVESTIGATE

**No list endpoint found.** What was tried `[VERIFIED]`:

| Attempt | Result |
|---|---|
| `https://northbay.applytojob.com/` | HTTP 200 HTML. 90 unique `/apply/{code}/{slug}` links. No `<link rel=alternate>` feed, no JSON-LD `JobPosting`, only an `Organization` block |
| `https://northbay.applytojob.com/apply/jobs/feed` | HTTP 200 but the body is a "404 Page Not Found" page |
| `https://northbay.applytojob.com/apply/jobs.rss` | **HTTP 410 Gone** |

The 410 is interesting: it implies the path once existed `[BELIEVED]`. The documented JazzHR API is `api.resumatorapi.com/v1/jobs?apikey=` and needs a key; it was not requested, because the brief bars authentication.

**Each job page carries JSON-LD `JobPosting`** with keys `datePosted`, `validThrough`, `hiringOrganization`, `jobLocation`, `title`, `url`, `employmentType`, `experienceRequirements`, `uniqueJobCode` `[VERIFIED]`:

| Posting | `datePosted` | `validThrough` |
|---|---|---|
| Senior AI Engineer | `'2026-07-20'` | `'2026-10-18'` |
| Lead Data Engineer (AWS Data Platform) | `'2026-07-09'` | `'2026-10-07'` |
| Principal Software Engineer (Data Platform) | `'2026-08-29'` | `'2026-11-27'` |

3/3, distinct, real. `validThrough` is exactly `datePosted` plus 90 days in all three cases, so it is derived, not independent `[VERIFIED]`. `hiringOrganization` is 'NorthBay Solutions' on all three, so JazzHR returns an employer where Ashby and Lever do not.

### Manatal: INVESTIGATE. The one platform with no date at all

**A machine-readable JSON API exists**, contradicting the architecture document's Tier C note that Manatal has "No verified JSON". It was not guessed: the career page is a Vue app, and its own inline script defines `apiBaseURL: ${baseUrl}/api/v1.0/c/${clientSlug}/` with `baseUrl = "https://www.careers-page.com"`, then requests `apiBaseURL+'jobs/?page_size='+pageSize+'&page='+currentPage` `[VERIFIED]`.

`https://www.careers-page.com/api/v1.0/c/{slug}/jobs/?page_size=50&page=1`, HTTP 200, no key, Django-style envelope `{count, next, previous, results}` `[VERIFIED]`:

| Board | `count` | Returned |
|---|---|---|
| spursol | 7 | 7 |
| ahdus-technology-2 | 27 | 20, with a `next` page URL |

**Every posting on both boards has exactly these 12 keys:** `address`, `city`, `country`, `description`, `hash`, `id`, `is_pinned_in_career_page`, `is_salary_visible`, `location_display`, `position_name`, `state`, `zipcode`. **No date field by name or by value, on 34 postings across 2 boards** `[VERIFIED]`.

Three further attempts to find a date `[VERIFIED]`:

- Per-job API `https://www.careers-page.com/api/v1.0/c/spursol/jobs/QY9YR6XV/` returns **HTTP 404** `{"detail":"Not found."}`.
- The job page `https://www.careers-page.com/spursol/job/QY9YR6XV` has **no JSON-LD, no ISO date, no "posted" text, no date-ish key**.
- The board page itself has no dates.

title 100% via `position_name`, description 100%, location 100% via `city`. **Employer 0%, URL 0%**, though a job URL is constructible as `careers-page.com/{slug}/job/{hash}`.

**This is ADR-0007's material case.** Manatal holds 8 registry boards and is one of the two dominant Pakistani platforms. Its rows can never satisfy Measure A and must fall back to first-seen ordering, which is what ADR-0007 already specifies.

### Freshteam: INVESTIGATE

- Documented API `https://xgrid.freshteam.com/api/job_postings` returns **HTTP 401** `{"errors":[{"code":"invalid_credentials",...}]}`. It needs a key `[VERIFIED]`. Whether a free key exists was not established; no account was created.
- The public list page `https://xgrid.freshteam.com/jobs` has no JSON-LD and no dates. 6 job links `[VERIFIED]`.
- **Each job page carries JSON-LD `JobPosting` with `datePosted`** `[VERIFIED]`, in an unusual format:

| Posting | `datePosted` |
|---|---|
| Full Stack Developer | `'2026-07-24 10:33:44 UTC'` |
| System Design Architect | `'2026-07-06 11:45:55 UTC'` |
| HR Specialist | `'2026-07-24 10:34:04 UTC'` |

3/3, distinct. **The format is not ISO-8601**: a space instead of `T` and a trailing ` UTC`. The spike-1 parser, which handles ISO, epoch and RFC-2822, rejects it. Any adapter needs a bespoke parse for this one `[VERIFIED]`.

### Zoho Recruit: INVESTIGATE

**No way to enumerate jobs was found.** What was tried `[VERIFIED]`:

| Attempt | Result |
|---|---|
| `https://thephygital.zohorecruit.com/jobs/Careers` | HTTP 200, 1.73 MB. A Lyte SPA shell: no JSON-LD, no job links, no dates, no API paths |
| Same for `hybridmediaworks` | HTTP 200, 1.72 MB, same, and no embedded job blob |
| `https://thephygital.zohorecruit.com/recruit/rss/jobs` | HTTP 200 but an HTML page, not a feed |
| `https://thephygital.zohorecruit.com/jobs/Careers/rss` | HTTP 200, `Content-Type: application/rss+xml`, body is 49 bytes: `Oops! It seems that the joblist has been removed.` |
| Same RSS path on `hybridmediaworks` | Identical response |

The RSS path returns the RSS media type on both boards, so the feature exists on the platform and is unpublished for these two portals `[BELIEVED]`.

**The job detail page does carry the data.** It embeds `var jobs = JSON.parse('[{...}]')` as a JavaScript string literal. Decoded `[VERIFIED]`, one job object with 18 keys: `City`, `Country`, `Currency`, **`Date_Opened`**, `Industry`, `Is_Locked`, `Job_Description`, `Job_Opening_Name`, `Job_Type`, `Keep_on_Career_Site`, `Posting_Title`, `Publish`, `Remote_Job`, `Salary`, `State`, `Work_Experience`, `Zip_Code`, `id`.

`Date_Opened = '2026-06-08'`, `Posting_Title = 'Agentic AI Engineer'`, `City = 'Karachi'`, `Publish = True`.

**Independent corroboration:** the registry's Part 11 records this exact posting as "Posted 8 June 2026" `[VERIFIED]`, which matches `Date_Opened` exactly. That is the only cross-check in this spike where an outside record confirms a field's meaning. `Date_Opened` is still not named "published", so it is reported, not assumed.

Coverage is 1/1, which is one posting. The blocking problem is enumeration, not the date.

### iCIMS: INVESTIGATE, and the date looks generated

> **Annotation, 2026-09-16, later the same day.** The "looks generated" reading below is **withdrawn**. An older posting on the same board reports `2025-05-15T04:00:00.000Z`, so the field varies per posting and is real. The three identical values were three jobs posted on the same day. See `2026-09-16-second-observation-checks.md`. The rest of this section, including the absence of a JSON list endpoint, stands.

- `https://pktechcareers-ibex.icims.com/jobs/search?ss=1`, HTTP 200 HTML, 15 unique job links on the first page. No feed link, no JSON-LD, no API path `[VERIFIED]`.
- The job page at `/jobs/{id}/{slug}/job` is a 4 KB **iframe wrapper**. The content is at the same URL with `?in_iframe=1`, which does carry JSON-LD `JobPosting` `[VERIFIED]`.

| Posting | `datePosted` | `validThrough` |
|---|---|---|
| Principal Software Engineer, Dev | `'2026-09-10T04:00:00.000Z'` | `'2027-09-10T04:00:00.000Z'` |
| Senior Software Engineer, Dev | `'2026-09-10T04:00:00.000Z'` | `'2027-09-10T04:00:00.000Z'` |
| Data Specialist, GRA | `'2026-09-10T04:00:00.000Z'` | `'2027-09-10T04:00:00.000Z'` |

**All three postings report the same instant to the millisecond**, with `validThrough` exactly one year later and a time component of exactly 04:00:00.000Z `[VERIFIED]`. Three unrelated roles are unlikely to have been published at the same millisecond `[BELIEVED]`. This looks like a generated or bulk-stamped value rather than each posting's publication time, which is the same class of defect as Greenhouse's bulk-written `updated_at` in the last log.

**Do not treat iCIMS `datePosted` as a publication date without more evidence.** What would settle it: sample postings known to be months apart, or a second run to see whether the value moves for unchanged postings. `hiringOrganization` is 'ibex' and `url` is present on all three.

### Dover: INVESTIGATE, and the dated feed is not the employer's board

Dover's own OpenAPI bundle, served publicly at `/static/search-builder2/static/js/openapi-CSMdCegl.js`, lists the API surface. Two public paths matter `[VERIFIED]`:

- `GET /api/v1/careers-page-slug/careerflow` → HTTP 200, gives the client id `c9a9b77b-6a08-408d-a99a-251c1444c1b0` and `name: 'Careerflow.ai'`.
- `GET /api/v1/careers-page/{client_id}/jobs` → HTTP 200, `count: 103`. **Six keys per posting**: `id`, `is_published`, `is_sample`, `locations`, `title`, `workplace_type`. **No date. No URL. No employer.** `[VERIFIED]`
- `GET /api/v1/job-board/jobs/{id}/` with a careers-page job id → **HTTP 404**.
- `GET /api/v1/job-board/jobs/?client={client_id}` → HTTP 200, `count: 482`, with **`date_posted`** present on 100/100 returned rows, 100 distinct values spanning `2026-08-11T17:36:17.958689Z` to `2026-09-16T07:10:36.212525Z` `[VERIFIED]`.

**But the `client` parameter was ignored.** The first 100 rows carry **45 distinct `client` objects** `[VERIFIED]`. This endpoint is Dover's cross-client job board, not Careerflow's careers page. It carries the employer name per row in `client.name`.

So Dover exposes a publication date, on a feed that spans many employers, and exposes none on the per-employer board the registry points at. That is an aggregator-shaped source in the sense of ADR-0019, not an ATS board.

## Registry findings

The brief asked for slugs from the registry only, and for registry problems to be reported `[VERIFIED]` against `Operating Plan\Reference\Jobs\Apify Run Log and ATS Registry.md`:

- **Workable has no slug recorded for five employers.** Part 3 lists "Hire with Reef", "CodeNinja, Thingtrax, Trickle Up, Staunch, Petra Brands" and "Inbox Business Technologies" with the board written only as `jobs.workable.com`. The two usable Workable slugs, `creative-chaos` and `igate-technologies`, appear in Part 11, not in the Part 3 registry table.
- **The `creative-chaos` board is now empty.** Part 11 records an "AI Platform Engineering Manager" posting there; the API returns `"jobs":[]`. The posting has closed since the census.
- **Part 3's claim that "Greenhouse, Lever, Ashby, Workable, Recruitee and SmartRecruiters expose public JSON over plain HTTP GET" is confirmed** for Ashby, Workable and SmartRecruiters. Recruitee was not in this spike's thirteen and remains untested.
- **The architecture document's Tier C entry, "JazzHR, Manatal: No verified JSON", is now wrong for Manatal**, which has a clean public JSON API, and remains right for JazzHR, which has no list endpoint.
- Every other slug in Parts 3 and 11 that this spike used resolved correctly: `Overjet`, `OneScreen`, `comprehensive-rehab-consultants`, `abyss`, `emumba`, `northbay`, `spursol`, `ahdus-technology-2`, `xgrid`, `thephygital`, `hybridmediaworks`, `careerflow`, `pktechcareers-ibex`, `talentmanagementsolution` `[VERIFIED]`.

## Volume, so the picture stops resting on 11 boards

Postings returned per board probed `[VERIFIED]`, one board per platform except Manatal and Workable:

| Board | Platform | Postings |
|---|---|---|
| comprehensive-rehab-consultants | Breezy | 191 |
| careerflow | Dover | 103 (employer board) |
| ContourSoftware-Careers | Workday | 90 total |
| northbay | JazzHR | 90 job links on the board page |
| ahdus-technology-2 | Manatal | 27 |
| Overjet | Ashby | 21 |
| pktechcareers-ibex | iCIMS | 15 on the first search page, paginated |
| igate-technologies | Workable | 12 |
| OneScreen | SmartRecruiters | 9 |
| spursol | Manatal | 7 |
| xgrid | Freshteam | 6 |
| emumba | Pinpoint | 4 |
| abyss | BambooHR | 3 |
| creative-chaos | Workable | 0 |

The spread seen on Greenhouse and Lever repeats here: 3 to 191 on a single board, with no useful central tendency. Breezy alone returns more postings than the 10 smallest boards in this table combined.

## For the architecture chat

Two items. Both change what the project does, so neither is mine to decide, and neither is a question for the operator to adjudicate alone.

**1. Policy for platforms whose list endpoint omits the publication date.** BambooHR and Workday carry a usable date only on a per-posting detail fetch. JazzHR, Freshteam, iCIMS and Zoho carry it only inside per-posting HTML. For Contour's Workday board that is 90 extra requests per run, per board, and ADR-0006 runs twice daily. This collides with ADR-0005's complete-board fetch, with the request budget the shared HTTP module in ADR-0009 is supposed to count, and with the cost assumptions in ADR-0003. **What needs deciding:** whether N+1 fetching is acceptable and under what per-run ceiling; or whether these platforms take ADR-0007's first-seen fallback instead and forgo Measure A on their rows; or whether they are deferred entirely. I have no basis to choose, because the answer depends on how much Measure A coverage the project is willing to buy with request budget.

**2. Whether Dover's cross-client job board is a source at all.** The only dated Dover feed spans 45 employers and 482 postings and is not the employer's board. ADR-0019 defines the aggregator source class and ADR-0020 routes raw storage by it. **What needs deciding:** whether Dover is polled as an aggregator source under those records, polled as a dateless employer board, or dropped. This is a scope question about what the pipeline ingests, not an implementation detail.

## Recommendations

**RECOMMENDATION**, not decisions.

1. **Adapter order, on this evidence:** Ashby, Workable, SmartRecruiters and Breezy next, after Greenhouse and Lever. All four are one unauthenticated GET per board, with a publication date at 100% and an unambiguous field name. Pinpoint follows, with the caveat that the date comes from its RSS and not its JSON.
2. **Manatal and JazzHR are the two dominant Pakistani platforms and both fail differently.** Manatal is cheap to poll and carries no date; JazzHR carries a real date but needs a page fetch per posting. If Pakistani coverage is the goal, Manatal is the cheaper adapter and its rows are first-seen-only.
3. ~~**Treat iCIMS `datePosted` as unverified** until the identical-timestamp anomaly is explained.~~ **Withdrawn 2026-09-16**, see the annotation above and `2026-09-16-second-observation-checks.md`. The field is real and per-posting.
4. **Freshteam's `datePosted` format needs its own parser.** `'2026-07-24 10:33:44 UTC'` is not ISO-8601 and the existing parser rejects it.
5. **The architecture document's Tier C line on Manatal should be corrected**, and the Workable slug gap in the registry Part 3 filled from Part 11.

## Checked and found already correct

- The 60-request cap fired as designed at every call; 53 used, 7 unspent `[VERIFIED]`.
- `raw_responses/` remains gitignored; `git check-ignore -v` returns `.gitignore:18:raw_responses/` for the new probe files `[VERIFIED]`.
- The spike-1 date scanner and field-population code needed no correction beyond a wider name regex and more field-name candidates.
- `tools/generate_map.py` now has the `log` type at line 59 and in the render order at line 204, as the brief said `[VERIFIED]`.

## Rejected alternatives

- **Guessing endpoint patterns.** Endpoints were read out of each platform's own page, bundle or robots.txt instead. That is why only 6 of 53 requests were non-200.
- **Using a web search engine to find documented endpoints.** Considered for the unknown platforms; rejected because the pages themselves are authoritative and searching adds an outside-repo source for a claim I can observe directly.
- **Writing an HTML parser for JazzHR or Manatal.** Barred by the brief. JSON-LD blocks were read to answer the date question, which is reporting what a page carries, not building a parser.
- **Authenticating anywhere.** Freshteam's 401 is reported as the finding, as instructed.
- **Spending the 7 remaining requests.** Nothing left was worth a request that would not also need a second run to interpret.

## Not done, and not established

- **Coverage percentages for the six JSON-LD and embedded-JSON platforms rest on 3 postings each, and Zoho on 1.** They are samples, not censuses.
- **Whether Zoho Recruit can be enumerated at all.** Without a list endpoint there is no adapter, whatever the date situation.
- **Whether a free Freshteam API key exists.** No account was created.
- **Whether iCIMS `datePosted` is real.**
- **Whether Workday `startDate` means publication.**
- **Whether any of these platforms' second boards behave differently**, except Manatal (2 boards) and Workable (2 boards).
- **Recruitee**, named in the registry as exposing public JSON, was not in the thirteen and was not tested.
- No decision record written or edited. `docs/reference/endpoint-shapes.md` not created. Nothing committed.
