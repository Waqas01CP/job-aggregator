---
type: reference
description: Every field each ATS platform and aggregator returns, with its type, how often it is populated, and whether the pipeline reads it. The inventory that makes "use everything that is fetched" checkable.
status: current
---

# Platform fields

**The rule this enforces: use everything that is fetched.** A request already
paid for that returns a structured field the pipeline throws away is the
cheapest improvement available, and the most easily forgotten, because
nothing anywhere says the field exists.

Himalayas is the case that prompted this file. It returns `seniority` on
every posting, as a list like `["Mid-level", "Senior"]`, and the pipeline
does not read it: seniority is inferred from title words instead, by
ADR-0032's rule, on a source that states it outright.

## How this was measured

From the 84 saved responses in `raw_responses/`, captured by the spikes of
2026-09-11 to 2026-09-16 and by the follow-up checks. Counted by walking
every posting object in each file and recording, per field, its type and
whether the value was present and non-empty. Sample sizes are given per
platform and several are small.

**Population rates are of the saved corpus, not of the platform.** Nine
Greenhouse boards at 1840 postings is a fair picture; SmartRecruiters at 9
postings from one board is a hint. A rate from a single board reflects that
employer's habits as much as the platform's.

**"Read" means the adapter names the field.** Determined by matching each
observed field name against the adapter source, not by reading the docstring,
so a field the docstring mentions and the code ignores counts as unread.

## Greenhouse, adapted. 1840 postings, 9 boards

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

## Lever, adapted. 92 postings, 2 boards

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

## Himalayas, adapted, aggregator. 146 postings, 91 unique

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

## What is fetched and not used, worth deciding on

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
| 2026-09-17 | File created. Twenty-three platform inventories from the 84 saved responses, with read and unread marked for the three adapted platforms | The architecture chat asked for it, on the rule that everything fetched should be used. Himalayas' `locationRestrictions` prompted it; measuring showed the adapter does read that field, lossily, and that the more valuable unread field is `seniority`, stated on every posting while the pipeline infers it from titles |
