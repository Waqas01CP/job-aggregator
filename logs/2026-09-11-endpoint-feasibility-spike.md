---
type: log
description: Endpoint feasibility spike against Greenhouse, Lever and Himalayas, run 2026-09-11. Written retroactively on 2026-09-15 from the run's own report.
status: current
---

# Endpoint feasibility spike, 2026-09-11

**Retroactive log.** The spike ran on 2026-09-11. This log was written on 2026-09-15 by the spike follow-up session, because the run itself wrote no log. It is transcribed from the run's printed report and from the output files that survive in that session's scratchpad (`spike_output.txt`, `replay_output.txt`). It is not a reconstruction. Where something was re-checked on 2026-09-15, the claim says so.

| Header | Value |
|---|---|
| Ran | 2026-09-11. Requests between 21:06:12Z and 21:06:55Z |
| Written | 2026-09-15, after the fact |
| Model | claude-opus-5, in the same conversation that later wrote this log |
| HEAD at run time | `ed0c4f4` |
| Mode | Read-only against every endpoint and every repository file. Wrote only to `raw_responses/` (gitignored) and the session scratchpad |
| Commit status of findings | Nothing committed by the run. This log is uncommitted at time of writing |

HEAD evidence `[VERIFIED 2026-09-15]`: `git log --date=iso` shows `ed0c4f4 2026-09-10 19:26:14 +0500` followed directly by `6839dba 2026-09-15 15:54:45 +0500`. The session-start git status of the run listed `LICENSE` and ADR-0021 as untracked; `git log --diff-filter=A` shows them added in `a219380` and `6839dba`, both after the run.

**Tags.** `[VERIFIED]` means exercised and observed in the 2026-09-11 pass. `[VERIFIED 2026-09-15]` means re-exercised while writing this log. `[BELIEVED]` means reasoned, not run. Unmarked means believed.

## Outcome

| Platform | Verdict | Failed criterion |
|---|---|---|
| Greenhouse | PROCEED | none |
| Lever | INVESTIGATE | Employer present on 0.0% of postings (threshold 100%). End-to-end check could not print an employer for a named posting |
| Himalayas | PROCEED | none |
| ADR-0006 propagation | PROCEED | Minimum posting age under 2 hours on Greenhouse (0.26 h) |

`[VERIFIED]`, from the replayed report's verdict block.

Limitation, as printed by the run: a single run cannot separate "boards publish instantly, but nothing happened to be posted recently" from "there is real propagation lag". Only a second run at least 3 hours later settles it. In that run, any posting that appears carrying a publication timestamp earlier than `2026-09-11T21:06:10.171756+00:00` is evidence of lag. **The second run has not been done.**

The ADR-0007 assumption that many platforms expose no publication date is false for all three platforms tested: publication timestamp parseable on 100% of postings on each `[VERIFIED]`.

## What ran

One throwaway script, `spike_endpoints.py`, kept in the session scratchpad and never in the repository.

- Standard library `urllib`, not `requests`. `python -c "import requests"` failed with `ModuleNotFoundError: No module named 'requests'` `[VERIFIED]`. Installing it was rejected: CLAUDE.md requires a new dependency to survive "the standard library can do this", and here it does not.
- 13 GET requests, 2.5 s apart, no authentication, User-Agent `job-aggregator-spike/0.1 (one-off endpoint feasibility diagnostic; read-only)` `[VERIFIED]`. No email or personal data in any request.
- 9 Greenhouse boards on the standard host, 2 Lever boards, 1 Himalayas browse request, and **1 deliberate extra request**: `veeamsoftware` with `?content=true`, the only way to answer the brief's content question. That is the single exception to one request per board.
- Every body saved to `raw_responses/{platform}-{slug}.json`. `git check-ignore -v` returned `.gitignore:18:raw_responses/` `[VERIFIED]`.
- Fetch clock `2026-09-11T21:06:10.171756+00:00`, printed by the run `[VERIFIED]`. File mtimes run from 02:06:12 to 02:06:55 local, UTC+5 `[VERIFIED 2026-09-15]`.

Raw files and sizes, re-checked against the run's printed byte counts, 11 of 11 board files matching exactly `[VERIFIED 2026-09-15]`:

| File | Bytes |
|---|---|
| greenhouse-veeamsoftware.json | 490052 |
| greenhouse-careem.json | 31861 |
| greenhouse-speechify.json | 684204 |
| greenhouse-brkz.json | 15779 |
| greenhouse-globalli.json | 8362 |
| greenhouse-gomotive.json | 121629 |
| greenhouse-joblogic.json | 18847 |
| greenhouse-banyancanopygroup.json | 4383 |
| greenhouse-coderoad.json | 16465 |
| greenhouse-content-veeamsoftware.json | 4677158 |
| lever-smart-working-solutions.json | 198208 |
| lever-spreetail.json | 323792 |
| himalayas-jobs-api.json | 123414 |

## The checks were proven able to fail before the run

`defeat_the_checks.py` fed the verdict logic fabricated payloads with no network `[VERIFIED]`. Re-run on 2026-09-15 with identical results `[VERIFIED 2026-09-15]`.

| Case | Built to defeat | Result |
|---|---|---|
| 0 | Control: every field, every date, all 200. Must reach PROCEED or the other cases prove nothing | PROCEED |
| 1 | HTTP 200 on 3 of 6 boards, 50% | INVESTIGATE, names the HTTP criterion |
| 1b | Boundary: exactly 80% | PROCEED, as required |
| 2 | Employer absent on 1 of 10 | INVESTIGATE, "Employer present and non-empty on 90.0%" |
| 3 | URL relative on 1 of 10 | INVESTIGATE, "Absolute URL present on 90.0%" |
| 4 | Title absent on 1 of 10 | INVESTIGATE |
| 5 | Publication timestamp on 80% | INVESTIGATE |
| 5b | Boundary: exactly 90% | PROCEED, as required |
| 6 | Only `updated_at`, no publication-named field | INVESTIGATE, no field selected |
| 7 | HTTP 200 with zero postings | INVESTIGATE |
| 8 | `first_published` present but `"not a date"` on every posting | INVESTIGATE |

The date parser rejected `True`, `0`, `4567890` (a Greenhouse-sized job id), `99999999999999`, `""`, `None` and `"not a date"`. It parsed ISO with `Z`, with offset, naive ISO, epoch seconds, epoch milliseconds as int and as string, and RFC-2822 `[VERIFIED]`.

## Incident: report truncated, replayed from disk

The run was invoked as `python spike_endpoints.py | tee spike_output.txt | head -100`. `head` exited after 100 lines, SIGPIPE killed the process, and `spike_output.txt` holds 155 lines, ending mid-Lever section `[VERIFIED]`.

Every network request had already completed. `grep -l "_spike_error" *.json` matched nothing, so all 13 saved files are real bodies `[VERIFIED]`. The full report was regenerated by `replay.py`, which calls the identical analysis functions on the saved bodies with the clock pinned to `2026-09-11T21:06:10.171756+00:00`. No endpoint was requested twice. Re-running live was rejected because it would have doubled every request.

## Greenhouse

All 9 boards HTTP 200 on `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`. Shape: object with keys `jobs` and `meta`, postings under `jobs` `[VERIFIED]`.

| Board | Postings | Youngest `first_published`, hours before fetch |
|---|---|---|
| veeamsoftware | 242 | 1.48 |
| careem | 21 | 11.52 |
| speechify | 1086 | 2693.09 |
| brkz | 23 | 557.00 |
| globalli | 12 | 71.39 |
| gomotive | 148 | 0.26 |
| joblogic | 31 | 25.18 |
| banyancanopygroup | 7 | 791.51 |
| coderoad | 28 | 526.15 |
| **Total** | **1598** | minimum 0.26 |

`[VERIFIED]`. Speechify is 1086 of 1598, 68.0% of Greenhouse volume.

**Publication field.** `first_published`, ISO-8601 with offset, sample `'2026-09-09T03:36:17-04:00'` parsing to `2026-09-09T07:36:17+00:00`. Present and parseable on 1598 of 1598 `[VERIFIED]`. Selected because its name unambiguously denotes publication.

**Other date fields, all reported, none treated as publication:**

- `updated_at`, ISO-8601 with offset, sample `'2026-09-09T06:54:23-04:00'`, 1598 of 1598 `[VERIFIED]`. Differs from `first_published` on 1535 of 1598, 96.1%, so the two are not aliases `[VERIFIED]`.
- `application_deadline`, key present on every posting and null on 1598 of 1598 `[VERIFIED]`. **The automated scanner missed this field**: its name regex did not match `deadline`. It was found by direct inspection.

Keys on `careem`'s first posting without `content=true`, 13: `absolute_url`, `application_deadline`, `company_name`, `data_compliance`, `first_published`, `id`, `internal_job_id`, `language`, `location`, `metadata`, `requisition_id`, `title`, `updated_at` `[VERIFIED]`. `veeamsoftware`'s first posting carries those plus `education`, 14, which is the baseline in the `content=true` table below `[VERIFIED 2026-09-15]`. Key sets are not identical across boards.

**Field population**: title 100% via `title`; employer 100% via `company_name`; URL 100% via `absolute_url`, all absolute; location 100% via `location.name`; description 0%, no field without `content=true` `[VERIFIED]`. Distinct `company_name` per board: `Banyan Canopy Group ` (trailing space as returned), `BRKZ`, `Careem`, `CodeRoad`, `Globalli`, `Motive`, `Joblogic`, `Speechify`, `Veeam Software` `[VERIFIED]`.

**EU-hosted boards.** `veeamsoftware`, `brkz` and `joblogic` all returned HTTP 200 from the standard host `[VERIFIED]`. **The EU API host `boards-api.eu.greenhouse.io` was never requested**, because the retry condition, a non-200 from the standard host, never fired. Its behaviour is unknown. EU hosting shows in the board URL instead: `"absolute_url": "https://job-boards.eu.greenhouse.io/veeamsoftware/jobs/4954045101"` `[VERIFIED]`.

**`?content=true`**, probed on `veeamsoftware` only `[VERIFIED]`:

| | Bytes | Keys per posting | Postings |
|---|---|---|---|
| Without | 490052 | 14 | 242 |
| With | 4677158 | 20 | 242 |

Keys added: `ai_disclaimer`, `ai_opt_out_request_url`, `content`, `departments`, `include_ai_disclaimer`, `offices`. Keys removed: none. Payload 9.5 times larger. `content` is a string of 6901 characters on the first posting, the employer description, not quoted here under ADR-0011. Date fields unchanged: `first_published`, `updated_at`.

**End-to-end, one named posting** `[VERIFIED]`:

```json
{
    "title": "Account Executive, Commercial Accounts (Public)",
    "company_name": "Veeam Software",
    "absolute_url": "https://job-boards.eu.greenhouse.io/veeamsoftware/jobs/4954045101",
    "first_published": "2026-09-09T03:36:17-04:00"
}
```

Youngest posting, which sets the 0.26 h minimum `[VERIFIED]`:

```json
{
  "title": "Staff Product Manager - Connected Devices",
  "company_name": "Motive",
  "absolute_url": "https://job-boards.greenhouse.io/gomotive/jobs/8782064002",
  "first_published": "2026-09-11T16:50:36-04:00",
  "updated_at": "2026-09-11T16:50:36-04:00"
}
```

## Lever

Both boards HTTP 200 on `https://api.lever.co/v0/postings/{slug}?mode=json`. Shape: top-level array. `smart-working-solutions` 21 postings, `spreetail` 27, total 48 `[VERIFIED]`.

**Publication field.** None named for publication. `createdAt`, epoch milliseconds as int, sample `1789018446882` parsing to `2026-09-10T05:34:06.882000+00:00`, parseable on 48 of 48 `[VERIFIED]`. Selected, and flagged in the output as `AMBIGUOUS: creation time; no field is named for publication`. Whether it means published or record-created was not tested.

Other date-named fields: `opening` and `openingPlain` matched the scanner's regex on the substring "open". Sample value `''`, parseable on 0 of 48. Scanner noise, not date fields `[VERIFIED]`.

**Employer: no field exists.** The full key enumeration across all 48 postings, **corrected**, 20 keys `[VERIFIED 2026-09-15]`:

`additional`, `additionalPlain`, `applyUrl`, `categories`, `country`, `createdAt`, `description`, `descriptionBody`, `descriptionBodyPlain`, `descriptionPlain`, `hostedUrl`, `id`, `lists`, `opening`, `openingPlain`, `salaryDescription`, `salaryDescriptionPlain`, `salaryRange`, `text`, `workplaceType`.

Per board, from the run's tool output `[VERIFIED]`: `smart-working-solutions` carries 18 of these, with `salaryRange` on 3 postings; `spreetail` carries all 20, with `salaryRange` on 8, and `salaryDescription` and `salaryDescriptionPlain` on 1 posting each. `categories` sub-keys: `allLocations`, `commitment`, `location`, `team`, plus `department` on `spreetail`. No key contains `compan`, `employ` or `org` on either board.

The employer is recoverable from the request: `hostedUrl` contains the requested slug on 21 of 21 and 27 of 27 postings, for example `https://jobs.lever.co/smart-working-solutions/904069e0-7632-4b2a-9fad-d1534a681649` `[VERIFIED]`. The verdict counts only returned fields. Counting derivation as presence was rejected, because it would have softened the verdict.

**Field population**: title 100% via `text`; employer 0%; URL 100% via `hostedUrl`, all absolute; location 100% via `categories.location`; description 100%, via `descriptionPlain` on 45 postings and `description` on 3 `[VERIFIED]`.

`createdAt` ages in hours `[VERIFIED]`: `smart-working-solutions` youngest 35.38, median 277.80, oldest 1690.56; `spreetail` youngest 53.35, median 1056.17, oldest 8471.96.

**End-to-end, failed on employer** `[VERIFIED]`:

```json
{
    "text": "Business Development Representative (Remote, Full-Time)",
    "hostedUrl": "https://jobs.lever.co/smart-working-solutions/904069e0-7632-4b2a-9fad-d1534a681649",
    "createdAt": 1789018446882
}
```

`employer [None] = None`. `ALL FOUR PRESENT (and URL absolute): NO`.

## Himalayas

`https://himalayas.app/jobs/api?limit=20`, HTTP 200, 123414 bytes. Shape: object with keys `comments`, `jobs`, `limit`, `nextCursor`, `offset`, `totalCount`, `updatedAt`. 20 postings. `totalCount` 100509, `nextCursor` `'MjAyNi0wOS0xMVQwMjo1Mzo0OS4wODc2NTBafDIxOTM0OTE'` `[VERIFIED]`.

**Publication field.** `pubDate`, epoch seconds as int, sample `1789141813` parsing to `2026-09-11T15:50:13+00:00`, on 20 of 20 `[VERIFIED]`. Other date field: `expiryDate`, epoch seconds, sample `1794148087` parsing to `2026-11-08T14:28:07+00:00`, on 20 of 20 `[VERIFIED]`.

Keys per posting: `applicationLink`, `categories`, `companyLogo`, `companyName`, `companySlug`, `currency`, `description`, `employmentType`, `excerpt`, `expiryDate`, `guid`, `locationRestrictions`, `maxSalary`, `minSalary`, `parentCategories`, `pubDate`, `salaryPeriod`, `seniority`, `timezoneRestrictions`, `title` `[VERIFIED]`. There is no `id` key.

**Field population**: title 100%, employer 100% via `companyName`, URL 100% via `applicationLink`, all absolute; location 55% via `locationRestrictions`, meaning 11 of 20 non-empty; description 100% `[VERIFIED]`.

**`locationRestrictions`**: key present on 20 of 20, an empty array on 9, non-empty on 11. Samples range from a single-country list, `"Bangladesh"`, to a 73-country list `[VERIFIED]`. What an empty array means was not tested. Research 0003:51 states it means worldwide; that is sourced from documentation, not observed.

**Employers**, 11 distinct: CapsLock, Databricks, Dura Digital, GXO Logistics, Heartbeat Health, Nexii Building Solutions Inc., SkyGrid, Upstream USA, lemon.io, mercor, micro1. None matches any Greenhouse or Lever slug or returned employer name, by exact-normalised or substring-normalised comparison against 20 slugs and names `[VERIFIED]`.

Envelope `updatedAt` `1789141813` equals the newest `pubDate` exactly; 5.27 h before the fetch clock `[VERIFIED]`. The coverage percentages above rest on 20 of 100509 postings.

**End-to-end** `[VERIFIED]`:

```json
{
    "title": "Financial Systems Expert",
    "companyName": "micro1",
    "applicationLink": "https://himalayas.app/companies/micro1/jobs/financial-systems-expert",
    "pubDate": 1789141813
}
```

## ADR-0006 propagation

Minimum posting age: Greenhouse 0.26 h, Lever 35.38 h, Himalayas 5.27 h `[VERIFIED]`. Verdict PROCEED on Greenhouse. The single-run limitation above applies in full.

## Corrections found after the run

Recorded here rather than silently fixed above, so the original report's error stays visible.

1. **The Lever key enumeration in the printed report was incomplete.** It listed 18 keys under "Every key on all 48 postings". The union is 20: `salaryDescription` and `salaryDescriptionPlain` appear only on `spreetail`, on one posting each. The per-board tool output had them; the summary dropped them `[VERIFIED 2026-09-15]`. **ADR-0026:15 reproduces the 18-key list** and calls it every key. Its conclusion, that no employer key exists, holds on all 20.
2. **Himalayas `updatedAt` is not a cache timestamp.** The report called the feed "5.27 hours stale" and suggested the 5.27 h floor "may be cache age". The follow-up found `updatedAt` equal to the newest `pubDate` on whatever page is returned, cursor pages included. The 5.27 h figure is the age of the newest posting on browse page 1, not a measured cache age. See `2026-09-15-spike-followup-checks.md`.
3. **Research 0003:51 records Himalayas `pubDate` as ISO 8601.** This run observed an integer epoch seconds value on 20 of 20 postings `[VERIFIED]`.

## Rejected alternatives

- Install `requests`: rejected, the standard library does the job.
- Treat Lever `createdAt` as a publication date without comment: rejected. Flagged ambiguous in output.
- Count a slug-derived employer as present for the Lever verdict: rejected. It would soften a verdict the brief says must not be softened.
- Re-run live after the truncated output: rejected. Replayed from disk.
- Keep the script in the repository: rejected. The brief says nothing is kept.

## Not done, and not established

- The EU Greenhouse API host was never requested.
- No second run at least 3 hours later, so propagation lag and a quiet market remain inseparable.
- Lever `createdAt` semantics untested.
- Himalayas findings rest on 20 postings.
- `locationRestrictions` empty-array semantics untested.
- `docs/reference/endpoint-shapes.md` not created, per the brief.
- No log was written by the run. This file fills that gap four days late.

## Recommendations offered at the time

Not decisions. The run's report offered a second pass at least 3 hours later, and a probe of the EU API host despite the standard host working. Neither was carried out. The follow-up session that wrote this log was briefed on different checks.
