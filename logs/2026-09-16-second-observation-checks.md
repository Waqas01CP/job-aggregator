---
type: log
description: Second-observation checks on three date fields left open by the platform spike. Workday startDate confirmed behaviourally, the iCIMS suspicion withdrawn, Lever createdAt still unsettled.
status: current
---

# Second-observation checks, 2026-09-16

Previous log: `2026-09-16-publication-date-across-untested-platforms.md`, earlier the same day.

| Header | Value |
|---|---|
| Date | 2026-09-16. Requests between 11:47Z and 11:48Z |
| Model | claude-opus-5 |
| HEAD | `26d0073` |
| Mode | **Read-only.** GET only, no authentication |
| Requests | **7 against a self-imposed cap of 12.** Ledger `secondobs_ledger.tsv` |
| Commit status | Committed with the three earlier logs; see the commit that adds this file |

**Tags.** `[VERIFIED]` means exercised and observed this pass. `[BELIEVED]` means reasoned, not run. Unmarked means believed. **RECOMMENDATION** marks a recommendation, not a decision.

## Why these tests and not a wait

The three questions left open this morning were framed as needing a second observation separated by time. **Only 1 hour 31 minutes had passed** since the platform spike's last request at 10:16:31Z `[VERIFIED]`, so a re-observation on elapsed time would have proved nothing about Workday or iCIMS.

Two of the three have a decisive test that needs no elapsed time at all, and the third already had a five-day-old baseline on disk. Those were run instead. Waiting a day was rejected: it would have delayed an answer that the data could give immediately.

## Question 1: does Workday's `startDate` mean publication? Yes, on behaviour

Spike 3 marked Workday INVESTIGATE because its only absolute date is named `startDate`, which does not denote publication and could as easily be the role's employment start date. The test that separates them needs no waiting: **an employment start date would not track the posting's age.**

Three more details were fetched at ages spread across the range, joining the four already held. Fetch date 2026-09-16. Expected value is the fetch date minus the relative age in `postedOn` `[VERIFIED]`:

| Title | `postedOn` | `startDate` | Expected | Match |
|---|---|---|---|---|
| Product Owner | Posted Yesterday | `2026-09-15` | 2026-09-15 | yes |
| Junior/Intermediate Software Developer | Posted Yesterday | `2026-09-15` | 2026-09-15 | yes |
| Data Engineer | Posted Yesterday | `2026-09-15` | 2026-09-15 | yes |
| AP & AR Analyst | Posted 5 Days Ago | `2026-09-11` | 2026-09-11 | yes |
| SDET | Posted 8 Days Ago | `2026-09-08` | 2026-09-08 | yes |
| HR Operations Intern | Posted 12 Days Ago | `2026-09-04` | 2026-09-04 | yes |
| Front Desk Officer | Posted 13 Days Ago | `2026-09-03` | 2026-09-03 | yes |

**7 of 7, across ages 1 to 13 days, with no exceptions** `[VERIFIED]`. No `startDate` is in the future.

`[BELIEVED]`: `startDate` is the posting's publication date, expressed as a date with no time. A field tracking posting age this exactly across the whole range is not an employment start date. The name remains wrong for what it holds, so an adapter should record where the value came from rather than trusting the label.

**This removes spike 3's stated reason for Workday's INVESTIGATE.** The remaining obstacle is cost, not semantics: the date is on the detail endpoint only, so it is 1 + N requests per board, and that is the N+1 question already before the architecture chat.

## Question 2: is iCIMS's `datePosted` generated? No. The suspicion was wrong

Spike 3 found three iCIMS postings all reporting `2026-09-10T04:00:00.000Z`, identical to the millisecond, and flagged the field as probably generated rather than real. **That was the wrong conclusion, and this pass withdraws it.**

The test: fetch a posting with a much lower job id, which should be much older. Job 19891 against the three already held at 29109, 29235 and 29236 `[VERIFIED]`:

| Job | `datePosted` |
|---|---|
| 29109 Principal Software Engineer, Dev | `2026-09-10T04:00:00.000Z` |
| 29235 Senior Software Engineer, Dev | `2026-09-10T04:00:00.000Z` |
| 29236 Data Specialist, GRA | `2026-09-10T04:00:00.000Z` |
| **19891 HR Business Analyst** | **`2025-05-15T04:00:00.000Z`** |

The older posting reports a date **sixteen months earlier**. The field varies per posting and is real. The three identical values were three jobs genuinely posted on the same day, which is ordinary for a large BPO hiring in batches.

**What the shared `04:00:00.000Z` actually is.** Every value observed carries exactly that time component. 04:00Z is midnight US Eastern Daylight Time. `[BELIEVED]`: iCIMS holds a date with no time and renders it at midnight Eastern. Untested for a winter date, which would render at 05:00Z under Eastern Standard Time if that reading is right.

**Correction to the record:** the platform spike's iCIMS entry and its "treat as generated until explained" recommendation are withdrawn. iCIMS's INVESTIGATE now rests only on there being no JSON list endpoint, which is unchanged.

## Question 3: does Lever's `createdAt` mean publication? Still not settled

The method from the earlier logs: a posting that becomes visible after a known observation, carrying a `createdAt` earlier than that observation's clock, would prove `createdAt` precedes visibility and is therefore a record-creation time rather than a publication time.

Baseline is the 2026-09-11 snapshot on disk, clock `2026-09-11T21:06:10.171756+00:00`, five days old. Both Lever boards were re-fetched `[VERIFIED]`:

| Board | Baseline | Now | Appeared | Disappeared |
|---|---|---|---|---|
| smart-working-solutions | 21 | 19 | 0 | 2 |
| spreetail | 27 | 25 | 1 | 3 |

The single posting that appeared is `Warehouse Team Member, $21/hr`, `createdAt` `2026-09-14T14:08:04.161Z`, which is **after** the baseline clock `[VERIFIED]`. Newly visible postings whose `createdAt` predates the baseline: **0 of 1**.

**That is consistent with `createdAt` being a publication time, and it is one posting.** One observation cannot establish the field's meaning; it can only fail to contradict it. **What would settle it:** more appearances, which means either a longer gap or busier boards. Two boards producing one new posting in five days is too thin a signal to conclude from.

**Bonus finding, relevant to ADR-0007.** Five of 48 postings disappeared over five days, 2 of 21 and 3 of 27 `[VERIFIED]`. ADR-0007 assumes "postings remain on their board for days rather than hours, so a missed run recovers on the next". Nothing here contradicts that: roughly 10% turnover over five days means a posting survives well past a 12-hour polling gap.

## What failed

One request of the seven failed `[VERIFIED]`: `https://pktechcareers-ibex.icims.com/jobs/18543/full-stack-developer/job?in_iframe=1` returned a `URLError` at the transport layer, not an HTTP status. It was a second old-job sample for question 2.

**It was not retried,** because job 19891 had already answered the question: the value varies per posting. Spending a request to confirm a settled answer is waste. The failure is recorded here so a later session does not read the gap as an untried case.

## Checked and found already correct

- The 2026-09-11 Lever snapshot on disk still matches its recorded byte counts and parsed cleanly as the baseline `[VERIFIED]`.
- The request cap held: 7 used of a self-imposed 12, enforced in code from the ledger `[VERIFIED]`.

## Rejected alternatives

- **Waiting a day and re-observing.** Rejected for Workday and iCIMS, where a test existed that needed no elapsed time. A day's delay would have bought nothing.
- **Fetching all 20 Workday details** to prove no `startDate` is in the future. Rejected: 7 points spread across the full age range answer the question, and 20 would cost 13 more requests for the same conclusion.
- **Retrying the failed iCIMS request.** Rejected as above.
- **Re-fetching Greenhouse against its baseline.** Rejected: ADR-0006 closed the propagation question on 2026-09-11 evidence, and its Changes entry states a second run "cannot change the verdict".

## Not done, and not established

- **Lever `createdAt` semantics.** One appearance in five days is not enough. This still gates whether Lever's rows can serve Measure A, and ADR-0026 leaves Lever's place in the slice open on exactly this point.
- **Whether iCIMS renders a winter date at 05:00Z**, which would confirm the Eastern-midnight reading.
- **Whether Workday's `startDate` ever diverges from `postedOn`** on a board other than ContourSoftware-Careers.
- No decision record written or edited. Nothing in `docs/` changed by this pass except as recorded in the commit that carries it.

## Recommendations

**RECOMMENDATION**, not decisions.

1. **Treat Workday `startDate` as the publication date**, recording its provenance, since the field name does not say what the field holds. The N+1 cost stays with the architecture chat.
2. **Withdraw the iCIMS caution** from the platform spike's recommendations. The field is real and per-posting.
3. **Settle Lever by observation, not by more reasoning.** Once the slice polls Lever twice daily, the question answers itself within days from the pipeline's own data: any posting first seen in a run whose `createdAt` predates the previous run's clock is the proof. No separate spike is needed if Lever is in the slice.
