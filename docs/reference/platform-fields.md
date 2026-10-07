---
type: reference
description: Every field each source returns and every query parameter its API accepts, measured over the full postings saved since 2026-09-26, with whether the pipeline reads each and where a posting states experience. The inventory that makes "use everything that is fetched" checkable, and the procedure for each new source.
status: current
---

# Platform fields

**The rule this enforces: use everything that is fetched.** A request already
paid for that returns a structured field the pipeline throws away is the
cheapest improvement available, and the most easily forgotten, because
nothing anywhere says the field exists.

**Re-measured 2026-10-02**, on what the pipeline fetches now. The first
measurement, 2026-09-17, read Himalayas' browse feed and Greenhouse without
descriptions; both changed on 2026-09-26. Its tables are kept at the end as
history.

## How this was measured

**The corpus is every posting the pipeline has saved whole**, the operator's
D11 (ADR-0051): the private repository's full branch, one file per run since
2026-09-26, each posting exactly as its board returned it. The first copy of
each posting was counted:

| Source | Postings | Boards | Request |
|---|---|---|---|
| Greenhouse | 823 | 9 | `boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true` |
| Lever | 63 | 2 | `api.lever.co/v0/postings/<board>?mode=json` |
| Himalayas | 809 | 1 | `himalayas.app/jobs/api/search?country=Pakistan&sort=recent&page=<n>` |

For each field: its JSON type, and the share of postings where it is present
and not empty. One level of nesting is shown, as `object.field`. **"Read"
means the adapter's source names the field**, matched as a quoted string, so
a field the docstring mentions and the code ignores counts as unread. Rates
are of this corpus: Lever's 63 postings from two boards say more about two
employers than about Lever.

Nothing here identifies a posting: field names, types, rates, and the
category names a provider defines. The measurement script is in
`logs/2026-10-02-the-closure-test-and-every-field.md`.

## Where a posting states experience

**No source gives years of experience as a field.** A number of years
appears only inside the description text, which the pipeline reads for it
since 2026-10-02 (below, "Decided"). **One source states a level:
Himalayas, on every posting**, which the level rule reads since the same day.

| Source | A stated level | Years as a field | Description states a number of years |
|---|---|---|---|
| Greenhouse | None standard. One board's custom `metadata` carries "Workday P Level", a grade code, on 269 postings | No | 435 of 823, 53% |
| Lever | `categories.level` exists in Lever's schema and filters, and neither board sets it: 0 of 63 | No | 42 of 63, 67% |
| Himalayas | `seniority`, 100%: Entry-level, Mid-level, Senior, Manager, Director, Executive, one or more | No | 406 of 809, 50% |

"States a number of years" counts descriptions with a phrase like "3 years",
"3+ years" or "3-5 yrs". It also matches "10 years in business", so it is an
upper bound on postings that ask for experience in years, not a count of
them. The rule's own reading is stricter (`src/description.py`): over the
1,708 postings saved by the evening of 2026-10-02 it finds years asked in
447 of 834 Greenhouse postings, 50 of 65 Lever and 386 of 809 Himalayas.

**What Himalayas' level would change, measured** over the 809 postings, each
put through the real adapter and filter chain at the moment it was saved:
- the chain keeps 67;
- **Himalayas labels 35 of those 67 Senior or above**: 32 Senior alone, 3
  with Senior among other levels;
- the title rule's seniority words dropped 45 postings Himalayas labels
  Senior or above (42 Senior alone), the ones whose title says so.

So about half of the Himalayas rows reaching the display were, by the
source's own label, senior roles. Reading the label was a rule change, and
the operator's (ADR-0032 is the title-word rule): he made it on 2026-10-02.

## Greenhouse

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `id` | number | 100% | yes | identity |
| `title` | string | 100% | yes | |
| `absolute_url` | string | 100% | yes | canonical URL, given |
| `company_name` | string | 100% | yes | |
| `first_published` | string | 100% | yes | ISO-8601. Measure A's field |
| `location`, `location.name` | object, string | 100% | yes | one free-text string |
| `content` | string | 100% | **yes**, since 2026-10-02 | the description, HTML-escaped, since `?content=true`. Read for the years asked, a required place and on-site work; the row keeps only those. Saved whole privately (D11) |
| `departments` | list | 100% | no | since `?content=true` |
| `offices` | list | 99.6% | **yes**, since 2026-10-02 | each office's `location`, "City, Region, Country": the posting's structured place, read by the location rule only where the free text names nothing it knows |
| `updated_at` | string | 100% | no | deliberately: bulk-stamped, ADR-0018 |
| `data_compliance` | list | 100% | no | GDPR flags |
| `language` | string | 100% | no | |
| `internal_job_id`, `requisition_id` | number, string | 99.6% | no | |
| `metadata` | list | 61.0% | **in part**, since 2026-10-02 | a `Country` field as a structured place, and a `Work Type` or `Job Type` field as the stated workplace; the rest unread. Each board's custom fields. One board accounts for most: "Workday P Level", "Job Family", "Worker Type", "Time Type", "Pay Rate Type" and nine more on 269 postings; "Employment Type" on 196 |
| `education` | string | 30.4% | no | a requirement flag, not a value |
| `include_ai_disclaimer`, `ai_opt_out_request_url`, `ai_disclaimer` | bool, string | 2.6 to 10.3% | no | |
| `employment` | string | 0.9% | no | |
| `application_deadline` | null | 0% | yes | read, never populated |

### What the unread Greenhouse fields hold

Measured 2026-10-02 over the same 823 postings `[VERIFIED]`.

- **`application_deadline` is already used.** The adapter reads it as the
  posting's expiry. A deadline already passed drops the posting at fetch
  (the expiry rule), and one that passes while it is shown marks it
  `Closed`. It is empty on all 823, on every board configured.
- **`internal_job_id` is the employer's job behind the posting; one job can
  have several postings**, one per city: 499 distinct over 823, and 380
  postings share theirs. **`requisition_id` is the employer's own requisition
  code**: 484 distinct, 407 shared. Either would group city copies exactly,
  where the pipeline groups by employer, normalised title and publication
  date (ADR-0001). Both bear on the repost question of 2026-09-30.
- **`updated_at` is not a freshness signal.** Boards bulk-stamp it: 16 of 21
  Careem postings share one instant, and on 2026-09-30, 303 postings first
  published over 180 days earlier had been updated in the previous 30.
  ADR-0018 bars it as a publication date.
- **`metadata` is each employer's own custom fields**, on 5 of 9 boards. What
  carries meaning for the operator:
  - **`Work Type`**, one board, 269 postings: Hybrid 140, Remote 80, Office
    Based 47. A structured workplace flag;
  - **`Job Type`**, one board: Remote, 16;
  - **`Country`**, one board, 21 postings: United Arab Emirates 12, Pakistan 7;
  - **`Workday P Level`**, one board: P1 12, P2 31, P3 33, P4 84, P5 31. That
    employer's internal grade; what each grade means is not published;
  - **`Employment Type`**, `Time Type`, `Worker Type`: Regular, Full-time,
    Fixed-Term, Contractor.

  Five fields name people: `Hiring Manager`, `Job Approver`, `Job HRBP`,
  `SOURCER (TA)`. They are public in the employer's API and are saved only
  in the private full branch. **No file in this repository records them.**
- **`content`, the description,** states a number of years on 53%. On the
  location question: of the location-dropped postings whose description
  mentions Pakistan, "anywhere" or "worldwide remote", 3 pass every other
  rule, and all 3 are correct drops. One is open to anywhere in Latin
  America only; two are Vietnam roles whose company has a Pakistan office. **No
  missed posting found.** Of 13 postings passing every rule but age, no
  description restricts the role to a country.
- **`offices` names a structured place,** "City, Region, Country", on 352 of
  831 office entries. It is not authoritative: a "Remote - India, Pakistan"
  posting lists offices in India and Mexico only.

## Lever

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `id` | string | 100% | yes | identity |
| `text` | string | 100% | yes | the title |
| `hostedUrl` | string | 100% | yes | canonical URL |
| `createdAt` | number | 100% | yes | epoch ms. Meaning unconfirmed, so never dropped for age (D14) |
| `categories.location` | string | 100% | yes | |
| `categories.allLocations` | list | 100% | no | every location, where `location` is one |
| `categories.team` | string | 100% | no | |
| `categories.commitment` | string | 96.8% | no | full time, part time and the like |
| `categories.department` | string | 63.5% | no | |
| `workplaceType` | string | 100% | **yes**, since 2026-10-02 | remote 41, on-site 22. The stated workplace: on site or hybrid feeds D13's on-site rule; remote adds nothing |
| `country` | string | 100% | **yes**, since 2026-10-02 | ISO-2. The posting's structured place, read where the free text names nothing the rule knows |
| `applyUrl` | string | 100% | no | |
| `description`, `descriptionBody` | string | 100% | **`description`**, since 2026-10-02 | HTML. Read with `lists` and `additional` for the description rules; the row keeps only what they derive. `descriptionBody`, the same without the opening, is not read |
| `descriptionPlain`, `descriptionBodyPlain` | string | 95.2%, 81.0% | no | the same as plain text |
| `lists` | list | 100% | **yes**, since 2026-10-02 | named sections: responsibilities, requirements. Where Lever's years are stated |
| `additional`, `additionalPlain` | string | 65.1% | **`additional`**, since 2026-10-02 | the closing text |
| `opening`, `openingPlain` | string | 61.9% | no | |
| `salaryRange` (`min`, `max`, `currency`, `interval`) | object | 12.7% | no | |
| `salaryDescription`, `salaryDescriptionPlain` | string | 1.6% | no | |

**No employer field**, which is why ADR-0026 derives it from the board.

### What the unread Lever fields hold

Measured 2026-10-02 over the 63 postings `[VERIFIED]`.

- **`lists` is the description's structured half:** headed sections, each
  `{text, content}`. The headings seen include "Responsibilities",
  "Requirements", "Nice to Have", "Benefits", and one board's heading on the
  experience that helps. **The years of experience live here: 50 of 63
  postings state a number of years inside `lists`, and 4 inside
  `description`.** A rule on experience over Lever must read `lists`.
- **`opening` is the introduction**, median 31 words. `description` is the
  opening plus the role's summary, median 128 words. `descriptionBody` is
  the summary without the opening. Each has a `Plain` twin without HTML.
- **`additional` is the closing text**, median 135 words: the company,
  benefits, the equal-opportunity statement.
- **`categories.location` is often a city:** "Dallas, TX", "Manila",
  "Kochi", "Bucharest". The location rule recognises countries, regions
  and Pakistani cities. A foreign city is unclear to it, so the posting is
  kept.
- **`country` and `workplaceType` say where the role is**, on 100%. On the 63:
  - remote in Pakistan 9, kept;
  - remote in India 15: 12 dropped on their "India" location, 3 kept as
    unclear cities;
  - remote in Romania 2, dropped;
  - **kept, though Lever places them in another country:** 19 on site in
    the United States, 3 on site in Germany, Britain and Romania, 7 remote
    in the United States, 6 in the Philippines, 3 in India, 1 each in
    Colombia and Britain.
- **`categories.allLocations` lists every place a posting is open in,**
  longer than one on 40 postings. None of the dropped postings lists
  Pakistan there: no posting was missed.

## Himalayas, the Pakistan search

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `guid` | string | 100% | yes | identity, a URL |
| `title` | string | 100% | yes | |
| `companyName` | string | 100% | yes | |
| `applicationLink` | string | 100% | yes | |
| `pubDate` | number | 100% | yes | epoch seconds |
| `expiryDate` | number | 100% | yes | epoch seconds. Closes a posting on its date (ADR-0050), and since 2026-10-02 the only way a Himalayas posting closes |
| `locationRestrictions` | list of country names | 10.8% | yes | empty on 722 of 809: open to every country, which the search returns with those listing Pakistan |
| `seniority` | list | 100% | **yes**, since 2026-10-02 | **the stated level**, read by the level rule. Counts by label below |
| `timezoneRestrictions` | list of numbers | 100% | no | UTC offsets the employer hires in. Never empty in this corpus. The operator: "time zone is not an issue" |
| `employmentType` | string | 100% | no | Full Time 581, Contractor 178, Part Time 22, Intern 9, Temporary 8, Volunteer 8, Other 3 |
| `categories` | list | 100% | no | role tags |
| `parentCategories` | list | 79.5% | no | |
| `excerpt` | string | 100% | no | the description's first sentences |
| `description` | string | 100% | **yes**, since 2026-10-02 | HTML. Read for the description rules; the row keeps only what they derive. Saved whole privately |
| `companySlug` | string | 100% | no | |
| `companyLogo` | string | 80.3% | no | |
| `salaryPeriod` | string | 100% | no | |
| `currency` | string | 30.3% | no | |
| `minSalary`, `maxSalary` | number | 15.9% | no | |

**`seniority` by label**, counting a posting under each level it lists:
Mid-level 344, Senior 285, Entry-level 84, Manager 84, Director 44,
Executive 28. 751 of 809 list one level.

### The Himalayas job page, field by field

What the operator reads on a posting's page, and where it is in what the
pipeline receives:

| On the page | In the API | Read |
|---|---|---|
| Apply before | `expiryDate` | yes: a passed date closes the posting |
| Posted on | `pubDate` | yes: the publication date, judged at first sight (D14) |
| Job type | `employmentType` | no |
| Experience level | `seniority` | yes: the level rule |
| Location requirements | `locationRestrictions`. Empty shows as "open to candidates from all countries" | yes: the location rule (D13) |
| Hiring timezones | `timezoneRestrictions` | no, by the operator's ruling |
| Job categories | `categories`, `parentCategories` | no |
| Skills | **not in the API response.** None of the 20 fields carries them, so the site shows something the API does not give |  |
| Browse similar jobs | the site's navigation, not data |  |
| The description | `description`, `excerpt` | `description` read for the description rules; `excerpt` not |

## Manatal, the career site's endpoint

`www.careers-page.com/api/v1.0/c/{slug}/jobs/?page={n}`, which Manatal does not document, accepted by the operator on 2026-10-07 for all nine registry boards: its documented endpoint served five of the nine and gave no working link to a posting. Measured 2026-10-07 over 393 postings on five boards, saved on 2026-10-04 and 10-07 `[VERIFIED]`:

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `id` | number | 100% | yes | identity |
| `hash` | string | 100% | yes | the posting's own page, `careers-page.com/{slug}/job/{hash}`; the documented endpoint's `id` opens a 404 |
| `position_name` | string | 100% | yes | the title |
| `description` | string | 100% | yes | HTML, for the description rules; the row keeps only what they derive |
| `location_display` | string | 98.2% | yes | the place as shown, read before `city`, `state` and `country` |
| `city`, `country` | string | 98.2% | yes | `country` is the posting's structured place |
| `state` | string | 50.4% | yes | |
| `organization_name` | string | 87.3% | yes | the employer; absent on some boards, which take the board's configured name |
| `address` | string | 39.9% | no | an office's street address |
| `salary_min`, `salary_max`, `currency_code` | string | 12.0% | no | |
| `is_pinned_in_career_page`, `is_salary_visible` | boolean | 100% | no | |
| `zipcode` | string | 0% | no | |

**No date of any kind, and no workplace field**, on any of the 640 distinct postings read across the nine boards and both endpoints on 2026-10-04. The documented endpoint's `created_at__gte` filter works and brackets the day a posting was created; nothing reads it, since whether creation means publication is unmeasured.

**Twenty postings a page**, whatever `page_size` asks, under `results` beside `count` and `next`. **The pages are not stable on every board:** ITC Worldwide's 24 pages on 2026-10-04 gave 477 reads of 338 distinct postings, where Abacus Consulting's nine on 2026-10-07 gave its 168 once each. The adapter keeps a repeated posting once, and a later walk reads one this walk missed.

**The two endpoints list different numbers:** Abacus Consulting showed 217 on the documented endpoint on 2026-10-04 and 168 on this one on 2026-10-07.

## What each API accepts

From each provider's own documentation, read 2026-10-02 `[outside this
repository]`. Rate limits are as documented.

**Greenhouse Job Board API**, public, no authentication, no documented rate
limit:

| Endpoint | Parameters | Used |
|---|---|---|
| `/v1/boards/<board>/jobs` | `content=true`: adds the description, departments and offices | **yes, with `content=true`** |
| `/v1/boards/<board>/jobs/<id>` | `questions=true`: the application form's `questions`, `location_questions`, `compliance`, `demographic_questions`. `pay_transparency=true`: `pay_input_ranges`, each with `min_cents`, `max_cents`, `currency_type`, `title`, `blurb` | no. One request per posting; whether these boards publish pay ranges is unmeasured |
| `/v1/boards/<board>/offices`, `/departments` | `render_as=list` or `tree` | no |
| `/v1/boards/<board>/sections`, `/education/degrees`, `/disciplines`, `/schools` | `term`, `page` | no |
| `/v1/boards/<board>` | none | no |

**Lever Postings API**, public. Rate limit documented only for applying, 2 a
second:

| Endpoint | Parameters | Used |
|---|---|---|
| `/v0/postings/<site>` | `mode` (json, iframe, html), `skip`, `limit`, and filters `location`, `commitment`, `team`, `department`, `level`, plus `group` | **yes, `mode=json`, unfiltered** |
| `/v0/postings/<site>/<id>` | none | no |

**Himalayas**, public. Rate-limited, 429 past the limit. Its terms ask that a
user link back to the posting and name Himalayas as the source, and not
submit its jobs to third-party aggregators (ADR-0020 keeps its rows private
regardless).

| Endpoint | Parameters | Used |
|---|---|---|
| `/jobs/api` (browse) | `cursor`, `limit` (at most 20), `offset` (deprecated) | **yes: one page on each walk for ADR-0053's agreement check** |
| `/jobs/api/search` | `q`, `country`, `worldwide`, `exclude_worldwide`, `seniority`, `employment_type`, `company`, `timezone`, `sort` (relevant, recent, salaryAsc, salaryDesc, nameAToZ, nameZToA, jobs), `page` | **yes: `country=Pakistan`, `sort=recent`, `page`** |

**Its documentation says the data "is cached every 24 hours".** Observed
otherwise on 2026-09-30: the search held a posting less than three hours old
(the Brief 8 log). Its job object documents `timezoneRestriction` and
`category`; the response carries `timezoneRestrictions` and `categories`,
and `seniority`, which the documentation does not list.

**Pushing a filter down is a decision, not a parameter.** `seniority` and
`employment_type` on the search would drop postings before they are seen.
ADR-0053 allows that only for a predicate duplicating one of the pipeline's
own recorded rules, and only while its agreement with that rule is checked.
Reading the field from the response keeps every posting observable
(ADR-0005), at no extra request.

## What is fetched and not used, worth deciding on

Ordered by what each would change. Reading a field means deciding what it
means and what happens when it is absent.

**Decided 2026-10-02:**
- **Himalayas `seniority` is read.** The level rule keeps a posting when any
  level it states is Entry-level or Mid-level, the operator's option A
  (`config/eligibility.json`). Over the 809 saved postings it takes the kept
  count from 67 to 34.
- **Job type is not filtered, on any source.** Interns, contract, part-time,
  temporary and volunteer roles are all kept: the operator, "volunteer might
  be a good opportunity and can become a stepping stone".
- **Time zones are not filtered.** He works US hours remotely.
- **Each source's structured place, and its stated workplace, are read**, the
  operator's go. Where every part of the location text is a place the rule
  cannot name, Lever's `country` and Greenhouse's `offices` and `Country`
  field decide, and only ever to close. A stated on-site or hybrid workplace,
  Lever's `workplaceType` or a Greenhouse `Work Type` field, makes a Pakistani
  city other than Karachi on site under D13; a stated remote workplace adds
  nothing. Measured with the code over the saved postings: 67 kept postings
  now dropped, 42 Lever and 25 Greenhouse, and none newly kept. The only ones
  naming Pakistan are six Islamabad roles whose field says hybrid, which D13
  drops.

- **The description is read**, on all three sources, for what stops him
  applying even when every other rule passes a posting: the operator, "high
  time that we use the description". Greenhouse's `content`, Lever's
  `description`, `lists` and `additional`, Himalayas' `description`.
  `src/description.py` reads each once, at normalisation, and the row keeps
  only what it derives: the years asked, the place names a requirement
  names, and an on-site flag. His answers the same evening:
  - **Experience:** "3 or 3+ is the max accepted years"; a preferred figure
    over it is out like a required one, "5+ years preferred is already
    out". A range counts by its low end.
  - **Authorisation:** a right to work, citizenship or residence required
    only in places closed to him drops the posting, his "work permit of us
    required". "No visa sponsorship" is never read as a requirement: on a
    role open worldwide it says only that no one is relocated, and he wants
    those roles.
  - **On site:** a description saying the role is on site counts as a
    stated workplace where the source states none, so D13 drops it outside
    Karachi.

  Each phrase was measured over the 1,708 postings saved by then before it
  was switched on; the log of 2026-10-02, its night section, has every count
  and the sentences behind each guard. Over those postings the rules read
  years in 883, a required place in 17 and on-site work in 34. Of the 50 the
  chain kept apart from age, 7 now drop: 6 asking 5 or more years, and 1
  Lahore role whose description says it is on site. None is newly kept.

**Open:**
1. **Salary**, on Himalayas 15.9% and Lever 12.7%. Greenhouse's
   `pay_transparency` costs a request per posting, rate unmeasured.
2. **Greenhouse `internal_job_id`**, to group one job's city copies exactly.
3. **Security clearance in the description.** Not read: 6 mentions in the
   1,708, two of them saying it is not required and one in a legal sense. A
   US citizenship requirement, which a US clearance implies, is read.

## Inventorying a new source

So a new source is measured the same way, before its adapter decides what to
read:
1. **Save its responses whole.** For an adapted source D11 already does this,
   privately. For a probe, keep the saved response out of the repository
   (`raw_responses/` is gitignored).
2. **Count every field** over every posting: JSON type, share present and not
   empty, one level of nesting, and whether the adapter names it. The script
   in the log of 2026-10-02 does this for the full branch's format.
3. **Read the provider's documentation** for every endpoint and parameter,
   and tag it as outside this repository. Compare it with the response: on
   Himalayas the two disagree on three field names.
4. **Look for the operator's questions first:** a publication date (Measure
   A), a stated level or years, location and remote flags, salary.
5. **Add its section here**, with the counts, and a Changes row.

## The thirteen probed platforms

Not adapted. Fields measured once, to decide adapter order (ADR-0029). Small
samples: treat as a guide to what exists, not as population rates.

| Platform | Postings | Publication date | Structured fields worth having |
|---|---|---|---|
| Ashby | 21 | `publishedAt` 100% | `isRemote` 100%, `workplaceType` 100%, `employmentType` 100%, `secondaryLocations` 47.6%, `address` 81% |
| Workable | 12 | `published_on` 100% | **`experience` 41.7%**, `education` 50%, `telecommuting` 100%, `country` 100%, `locations` 100% |
| SmartRecruiters | 9 | `releasedDate` 100% | **`experienceLevel` 100%**, as `{id: entry_level, label: Entry Level}`. Also `typeOfEmployment`, `industry`, `function`, `customField` |
| Breezy | 191 | `published_date` 100% | `location` and `locations` 100%, `type` 100%, `salary` 99.5% |
| Pinpoint | 4 | in RSS, not JSON | `workplace_type` 100%, `employment_type` 100%, `location` 100%, structured `skills_knowledge_expertise` |
| BambooHR | 771 | detail request per posting | `atsLocation`, `locationType`, `employmentStatusLabel`, all on the 0.4% that are detail responses |
| Manatal | 27 | **none, any field** | `city`, `country`, `location_display` 100%; `state` 7.4%. ADR-0007's material case |
| Workday | 28 | `startDate` 28.6%, `postedOn` 100% as "Posted 5 Days Ago" | `timeType` 100%, `locationsText` 100% |
| Zoho Recruit | 1 | `Date_Opened` 100% | **`Work_Experience` 100%, as "1-3 years"**, `Remote_Job` bool, `City`, `State`, `Country`, `Job_Type` |
| Dover | 200 | `date_posted` 50% | `workplace_type` 100%, `locations` 100% with `location_type: REMOTE`. Dropped by ADR-0029 |
| JazzHR, Freshteam, iCIMS | see logs | per-posting HTML only | not inventoried here; the saved probes are HTML, not JSON |

## History: the measurement of 2026-09-17

From the 84 responses saved by the spikes of 2026-09-11 to 09-16, before
`?content=true` and before Himalayas moved to search. Kept as measured.

### Greenhouse, adapted. 1840 postings, 9 boards

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `id` | int | 100% | yes | identity |
| `title` | string | 100% | yes | |
| `absolute_url` | string | 100% | yes | canonical URL, given not constructed |
| `location` | object | 100% | yes | `.name`, one free-text string |
| `company_name` | string | 100% | yes | ADR-0026 provenance `payload` |
| `first_published` | string | 100% | yes | ISO-8601 with offset. Measure A's field |
| `updated_at` | string | 100% | **no** | deliberately. ADR-0018 bars it: bulk-stamped, 16 of 21 Careem postings share one instant |
| `data_compliance` | list[object] | 100% | no | GDPR flags |
| `language` | string | 100% | no | |
| `internal_job_id` | int | 99.8% | no | |
| `requisition_id` | string | 99.8% | no | |
| `metadata` | list[object] | 37.4% | **no** | **the experience lead.** Carries "Workday P Level" on the Veeam board, a grade code, on 242 postings |
| `education` | string | 20.0% | no | a requirement flag, not a value |
| `content` | string | 13.2% | no | description HTML. ADR-0011 keeps it off the branch |
| `departments` | list[object] | 13.2% | no | |
| `offices` | list[object] | 13.1% | **no** | structured office locations, richer than `location.name` |
| `employment` | string | 0.3% | no | |
| `application_deadline` | null | 0% | yes | read, never populated in this corpus |
| `ai_disclaimer`, `ai_opt_out_request_url`, `include_ai_disclaimer` | null | 0% | no | present in the schema, empty everywhere |

### Lever, adapted. 92 postings, 2 boards

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `id` | string | 100% | yes | identity |
| `text` | string | 100% | yes | the title |
| `hostedUrl` | string | 100% | yes | canonical URL |
| `categories` | object | 100% | yes | `.location` only |
| `createdAt` | int | 100% | yes | epoch ms. Meaning still unconfirmed, ADR-0026 |
| `workplaceType` | string | 100% | **no** | `"remote"`. A structured remote flag, unused |
| `country` | string | 100% | **no** | ISO-2. Unused |
| `applyUrl` | string | 100% | no | |
| `description`, `descriptionBody`, `descriptionPlain`, `descriptionBodyPlain` | string | 90 to 100% | no | ADR-0011 |
| `lists` | list[object] | 100% | no | responsibilities and requirements, structured |
| `additional`, `additionalPlain` | string | 60.9% | no | |
| `opening`, `openingPlain` | string | 56.5% | no | |
| `salaryRange` | object | 22.8% | no | min, max, currency, interval |
| `salaryDescription`, `salaryDescriptionPlain` | string | 2.2% | no | the two keys ADR-0026's first enumeration missed |

**No employer field**, which is why ADR-0026 derives it from the slug with
provenance recorded.

### Himalayas, adapted, aggregator. 146 postings, 91 unique

| Field | Type | Populated | Read | Note |
|---|---|---|---|---|
| `guid` | string | 100% | yes | identity, a URL |
| `title` | string | 100% | yes | |
| `companyName` | string | 100% | yes | |
| `applicationLink` | string | 100% | yes | |
| `pubDate` | int | 100% | yes | epoch seconds |
| `expiryDate` | int | 100% | yes | epoch seconds. The only source with a real expiry |
| `locationRestrictions` | list[string] | 82.9% | yes, lossily | country allowlist. The adapter joins the first three into the `location` string |
| `seniority` | list[string] | 100% | **no** | **`["Mid-level", "Senior"]`. Stated seniority, on the one source that gives it** |
| `timezoneRestrictions` | list[number] | 100% | **no** | UTC offsets the role accepts. A second eligibility axis |
| `employmentType` | string | 100% | no | `"Full Time"` |
| `excerpt` | string | 100% | no | |
| `salaryPeriod` | string | 100% | no | |
| `categories` | list[string] | 98.6% | no | role tags |
| `companyLogo` | string | 91.8% | no | |
| `parentCategories` | list[string] | 62.3% | no | `["Developer"]` |
| `currency` | string | 58.2% | no | |
| `minSalary`, `maxSalary` | int | 43.8% | no | |
| `companySlug` | string | 100% | no | |
| `description` | string | 100% | no | ADR-0011, and ADR-0020 keeps aggregator rows local anyway |

**The restriction lists are shorter than they look.** Across 91 unique
postings: 74 carry a non-empty list, 17 carry an empty list, none is absent.
Median length 1, 90th percentile 2, maximum 73. **Only 2 of 74 lists exceed
three entries**, so the adapter's cut at three loses information on two
postings, not on most of them.

**None of the 74 lists names Pakistan.** On this corpus, the reachability
answer for the operator is 74 excluded, 17 unstated.

### What it ranked, 2026-09-17

Ordered by what each would change, not by effort.

1. **Himalayas `seniority`.** Stated seniority on 100% of its postings, while
   ADR-0032 infers it from title words. A source that states the thing the
   rule guesses should not be guessed at. It is also the only place the
   seniority rule could be checked against an independent signal.
2. **Himalayas `timezoneRestrictions`.** 100% populated, an eligibility axis
   no ATS board offers, and directly relevant to whether a role is workable
   from Pakistan.
3. **Lever `workplaceType` and `country`.** Both 100%. A remote flag and a
   country, where today the pipeline reads only a free-text location.
4. **Greenhouse `metadata`.** 37.4% overall, and the only structured level
   information any employer board gives. Weak, per the 2026-09-17 check: one
   board of nine, a grade code, no years.
5. **Greenhouse `offices`.** 13.1%, structured locations beside the free-text
   one.
6. **SmartRecruiters `experienceLevel` and Zoho `Work_Experience`**, when
   those adapters exist. These are the only measured sources of the field the
   stated-experience rule needs, which today has no source at all.

Nothing here is a decision. Reading a field means deciding what it means and
what happens when it is absent, and each of these deserves that separately.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-07 | Manatal's section added: the career site's endpoint, every field counted over 393 postings, no date and no workplace field, unstable pages | Its adapter is built, ADR-0059's first platform by measured yield, on the endpoint the operator accepted that day |
| 2026-10-02, night | The description is read, on the operator's answers: the fields each adapter now reads are marked, the "Open" description item moved to "Decided" with its measured effect, and security clearance added as open. Himalayas `seniority`, read since the evening's level rule, was still marked unread in two tables and in the experience section: corrected | His thresholds arrived; the seniority rows were stale since `d5dda62`, the implementing seat's miss |
| 2026-10-02 | Re-measured over the 1,695 postings saved whole since 2026-09-26, on what the pipeline fetches now: Greenhouse with descriptions, Himalayas' Pakistan search. Added: where each source states experience, the Himalayas job page mapped to its API fields, every endpoint and parameter each API documents, the unused fields re-ranked, and the procedure for a new source. The 2026-09-17 tables kept as history | The operator asked for every field each source gives, experience above all, after seeing senior Himalayas roles in his table, and for it to be repeatable as sources are added. Two of the 09-17 tables no longer described the requests made |
| 2026-09-17 | File created. Twenty-three platform inventories from the 84 saved responses, with read and unread marked for the three adapted platforms | The architecture chat asked for it, on the rule that everything fetched should be used. Himalayas' `locationRestrictions` prompted it; measuring showed the adapter does read that field, lossily, and that the more valuable unread field is `seniority`, stated on every posting while the pipeline infers it from titles |
