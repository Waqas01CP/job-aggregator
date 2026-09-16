---
type: log
description: Spike follow-up. Board volume measured, Speechify age floor examined, Lever createdAt checked against hosted pages, Himalayas newest-first pagination tested.
status: current
---

# Spike follow-up checks, 2026-09-15

Previous log: `2026-09-11-endpoint-feasibility-spike.md`, written retroactively in this same session.

| Header | Value |
|---|---|
| Date | 2026-09-15. Requests between 18:58:24Z and 19:14:07Z |
| Model | claude-opus-5 |
| HEAD | `26d0073` |
| Mode | **Read-only** against every endpoint (GET only, no authentication) and against every existing repository file, except the ones this brief instructs: this log, the backfill log, `logs/README.md`, `STATE.md`. `MAP.md` regenerated, because two frontmatter-bearing files were added |
| Commit status | **Uncommitted.** The brief forbids writes to any git branch and does not ask for a commit. The pre-commit hook was exercised against a temporary index instead; see the section on the gates |

**Tags.** `[VERIFIED]` means exercised and observed in this pass. `[BELIEVED]` means reasoned, not run. Unmarked means believed. **RECOMMENDATION** marks a recommendation, which is not a decision.

Every age in checks 1 and 2 is measured from the 2026-09-11 fetch clock, `2026-09-11T21:06:10.171756+00:00`, not from today. Measuring from today would add about four days to every age.

## Findings

1. **Speechify's 112-day floor is real in the data, and by the brief's test the board is live.** 274 of 1086 postings have `updated_at` within 7 days of fetch against a `first_published` older than 30 days. But the updates arrive as four rotating batches of about 265 postings, drawn evenly from every publication cohort. The 1086 postings are 8 base titles repeated across 329 locations `[VERIFIED]`.
2. **Eleven boards return 1646 postings.** Median 27, mean 149.6, maximum 1086. ADR-0001:27 estimates "on the order of one thousand" per run for all 53 boards, and 11 boards already exceed it. The per-board role figure the estimate was built from is close as a median, 21 distinct base titles, but postings are not roles `[VERIFIED]`.
3. **Lever hosted pages display no date**, on 3 of 3 pages. Per the brief, that is the finding and the check stops there `[VERIFIED]`. Separately, and not displayed: page-source JSON-LD `datePosted` equals `createdAt`'s UTC calendar date on 3 of 3 `[VERIFIED]`.
4. **Himalayas browse can be read newest-first with a cursor; search cannot.** The browse endpoint is ordered by `pubDate` descending, with no duplicates and no inversions over 3 cursor pages. Search with `sort=recent` is not recency-ordered and silently ignores `cursor`. Termination was not established. Envelope `updatedAt` is the newest `pubDate` on the returned page, not a cache time. Browse's newest posting trailed search's by 97.7 minutes `[VERIFIED]`.

## Evidence base

**Checks 1 and 2 used no network.** `raw_responses/` held every file; none was missing, none re-fetched.

Integrity of that evidence `[VERIFIED]`:

- Byte counts of the 11 board files equal the counts the 2026-09-11 run printed, 11 of 11. For example `greenhouse-speechify.json` is 684204 on disk and `speechify HTTP 200 684204 bytes` in `spike_output.txt`.
- The fetch clock line `run clock (UTC): 2026-09-11T21:06:10.171756+00:00` is line 2 of `spike_output.txt`. File mtimes run from 02:06:12 to 02:06:55 local time, UTC+5.
- sha256 prefixes recorded for future comparison: speechify `c2580f0e1edd7f12`, veeamsoftware `a8f756cffb43afc3`, gomotive `ef74c541aecb3dd6`, lever smart-working-solutions `e56bf2a6ef13c43f`, lever spreetail `775713837f7b9e24`, himalayas `fdfc8c45b116bed7`.

**Checks 3 and 4 made 10 GET requests**, each appended to a ledger file before its result was used, so the count is read off a file `[VERIFIED]`. User-Agent `job-aggregator-spike/0.2 (one-off follow-up diagnostic; read-only)`, no personal data, at least 2.5 s apart.

| # | UTC | Check | Status | Bytes | URL |
|---|---|---|---|---|---|
| 1 | 18:58:24 | 3 | 200 | 729169 | `https://jobs.lever.co/smart-working-solutions/0c605546-9908-4d2e-9f44-197273172f82` |
| 2 | 18:58:26 | 3 | 200 | 735195 | `https://jobs.lever.co/smart-working-solutions/e3e9506e-8fe9-45fd-b703-bd4b3d85dbbc` |
| 3 | 18:58:29 | 3 | 200 | 738892 | `https://jobs.lever.co/spreetail/34c6437e-2541-4814-9910-19e12e354c7b` |
| 4 | 18:59:40 | 4, r1 | 200 | 76692 | `https://himalayas.app/jobs/api/search?sort=recent&limit=20` |
| 5 | 19:00:34 | 4, r2 | 200 | 128224 | `https://himalayas.app/jobs/api?limit=20` |
| 6 | 19:00:49 | 4, r3 | 200 | 137648 | `https://himalayas.app/jobs/api?limit=20&cursor=MjAyNi0wOS0xNVQxNjo1ODo0NS40MjE0OTdafDIyMjExNjU` |
| 7 | 19:01:02 | 4, r4 | 200 | 128120 | `https://himalayas.app/jobs/api?limit=20&cursor=MjAyNi0wOS0xNVQxNjo0NTowMy4xNzc0NjJafDIyMjI0NzE` |
| 8 | 19:02:11 | 4, r5 | 200 | 76692 | `https://himalayas.app/jobs/api/search?sort=recent&limit=20&cursor=MjAyNi0wOS0xNVQxNTo1MToyNS43MTEwMTdafDIyMjIyNTU` |
| 9 | 19:08:05 | 4, r6 | 200 | 128224 | `https://himalayas.app/jobs/api?limit=20` |
| 10 | 19:14:07 | 4, r7 | 200 | 128224 | `https://himalayas.app/jobs/api?limit=20` |

Check 4 used 7 of its 7 permitted requests. The cap was enforced in code, and proven: an eighth invocation printed `REFUSED: 7 check4 requests already made; cap is 7.`, exited 2, and wrote no ledger line `[VERIFIED]`.

Bodies saved under `raw_responses/`: `lever-page-{id}.html` and `himalayas-followup-{label}.json`. `git check-ignore -v` returns `.gitignore:18:raw_responses/` for both kinds `[VERIFIED]`.

## Check 1: is Speechify's 112-day floor real?

### Per Greenhouse board

`[VERIFIED]`, generated from the saved files by script rather than retyped.

| Board | Postings | `first_published` min / median / max, days | `updated_at` min / median / max, days | `first_published` equals `updated_at` |
|---|---|---|---|---|
| veeamsoftware | 242 | 0.06 / 37.52 / 604.15 | 0.06 / 2.42 / 2.42 | 20 of 242, 8.3% |
| careem | 21 | 0.48 / 51.36 / 1044.20 | 0.48 / 7.56 / 7.56 | 4 of 21, 19.0% |
| speechify | 1086 | 112.21 / 381.13 / 1012.04 | 2.79 / 14.22 / 112.01 | 0 of 1086, 0.0% |
| brkz | 23 | 23.21 / 378.39 / 515.17 | 1.36 / 169.38 / 169.38 | 2 of 23, 8.7% |
| globalli | 12 | 2.97 / 36.91 / 119.19 | 2.97 / 36.34 / 64.07 | 6 of 12, 50.0% |
| gomotive | 148 | 0.01 / 32.17 / 1855.97 | 0.01 / 7.16 / 7.16 | 15 of 148, 10.1% |
| joblogic | 31 | 1.05 / 57.19 / 77.43 | 0.21 / 7.47 / 57.52 | 11 of 31, 35.5% |
| banyancanopygroup | 7 | 32.98 / 88.20 / 155.45 | 3.45 / 3.45 / 3.45 | 0 of 7, 0.0% |
| coderoad | 28 | 21.92 / 51.52 / 228.84 | 1.02 / 38.00 / 157.11 | 5 of 28, 17.9% |

Equality was counted twice, once as strings and once as parsed instants, so an offset written differently could not mislead. The counts agree on every board `[VERIFIED]`. `updated_at` is earlier than `first_published` on 0 of 1598 postings `[VERIFIED]`. `meta.total` equals the length of `jobs` on 9 of 9 boards, so no response was truncated `[VERIFIED]`.

### Speechify: live board with old postings, or dead board

**By the brief's test, live.** `[VERIFIED]`:

| Window before fetch | `updated_at` within | `first_published` within |
|---|---|---|
| 24 hours | 0 of 1086 | 0 of 1086 |
| 7 days | 274 of 1086 | 0 of 1086 |
| 30 days | 1075 of 1086 | 0 of 1086 |
| 90 days | 1076 of 1086 | 0 of 1086 |

`updated_at` within 7 days **and** `first_published` older than 30 days: **274 of 1086**. Youngest `updated_at` `2026-09-08T22:05:04-04:00`, 2.79 days before fetch. Youngest `first_published` `2026-05-22T12:00:51-04:00`, 112.21 days before fetch.

**What "live" means here is narrower than the brief's framing assumes.** The updates are batched, not scattered `[VERIFIED]`:

| `updated_at` UTC date | Postings | Time span that day |
|---|---|---|
| 2026-08-24 | 267 | 05:44:32 to 07:08:15 |
| 2026-08-28 | 267 | 00:01:06 to 15:53:22 |
| 2026-09-02 | 265 | 00:00:27 to 07:45:53 |
| 2026-09-09 | 264 | 00:56:09 to 02:05:04 |
| six other dates | 23 | 3, 7, 1, 1, 1, 10 |

Each batch draws evenly from every publication cohort. Rows are `updated_at` date, columns are `first_published` month, main batches only `[VERIFIED]`:

| | 2023-12 | 2024-01 | 2025-05 | 2025-08 | 2025-12 | 2026-05 |
|---|---|---|---|---|---|---|
| 2026-08-24 | 27 | 35 | 25 | 60 | 93 | 27 |
| 2026-08-28 | 27 | 34 | 26 | 60 | 93 | 27 |
| 2026-09-02 | 24 | 36 | 24 | 60 | 96 | 25 |
| 2026-09-09 | 26 | 32 | 27 | 59 | 92 | 28 |

`[BELIEVED]`: a process rotates through the whole board and rewrites about a quarter of it each pass. An employer editing individual postings would not produce a partition this even. What runs that process, and whether it touches anything a candidate sees, is not established.

**The postings themselves** `[VERIFIED]`:

- `first_published` falls on only 10 distinct UTC dates. The largest are 2025-08-26 with 241, 2025-12-02 with 241, 2024-01-24 with 138, 2025-12-05 with 136, 2023-12-04 with 105, 2025-05-07 with 103, 2026-05-06 with 95, and 2026-05-22 with 13.
- 1074 of 1086 titles contain `" - "`. On all 1074, the text after the final `" - "` equals that posting's `location.name` exactly.
- With that suffix removed, 1086 postings are **8 base titles**, across 329 distinct `location.name` values. The four largest are `Senior Software Engineer, Core Experiences`, `Senior Software Engineer, Windows/Desktop Applications`, `Software Engineer, Data Infrastructure & Acquisition` and `Software Engineer, Platform`, 241 each. Then `Go-to-Market` 107, `Manual Quality Assurance Engineer, SIMBA Team` 13, and `Go-to-Market Engineer` and `Head of Agent Relations`, 1 each. Titles are metadata ADR-0011 permits; no description text is quoted.
- Consistency of `first_published` with posting order: sorted by Greenhouse `id`, 98 of 1085 adjacent pairs have `first_published` going backwards. The lowest id, `5032760004`, has `2023-12-04T15:09:34-05:00`; the highest, `6165110004`, has `2026-05-21T02:28:28-04:00`. `[BELIEVED]`: `first_published` broadly tracks creation order. This is weak evidence and cannot establish what the field means.

**Answer.** The 112-day floor is real in what the API returns: nothing on the board has a `first_published` newer than 112.21 days `[VERIFIED]`. The board is not dead by the brief's test, since 274 postings carry a recent `updated_at` `[VERIFIED]`. But the recency comes from a batch rewrite, and the volume comes from 8 roles multiplied by location `[VERIFIED]`. Whether `first_published` means publication on this board could not be settled offline.

### `updated_at` is bulk-stamped on other boards too

Share of each board's postings on its most common `updated_at` UTC date, and the time span within that date `[VERIFIED]`:

| Board | Postings on modal date | Span |
|---|---|---|
| banyancanopygroup | 7 of 7 on 2026-09-08 | 0.0 min, all at 10:15:34 |
| veeamsoftware | 199 of 242 on 2026-09-09 | 501.8 min |
| careem | 16 of 21 on 2026-09-04 | 0.0 min, all at 07:33:10 |
| brkz | 15 of 23 on 2026-03-26 | 0.1 min, 11:58:54 to 11:58:57 |
| gomotive | 95 of 148 on 2026-09-04 | 267.6 min |
| globalli | 4 of 12 on 2026-07-09 | 36.4 min |
| coderoad | 6 of 28 on 2026-06-15 | 16.3 min |
| joblogic | 6 of 31 on 2026-07-16 | 504.4 min |

Several postings sharing one second of `updated_at` is a bulk write, not an edit. `[BELIEVED]`: `updated_at` is not usable as a per-posting "changed" signal on these boards.

## Check 2: postings per board, measured

`[VERIFIED]`. A base title is the title with a trailing `" - <location>"` removed only where that suffix equals the posting's own location field exactly (`location.name` on Greenhouse, `categories.location` on Lever). It only changed Speechify.

| Platform | Board | Postings | Share | Cumulative | Distinct titles | Distinct base titles |
|---|---|---|---|---|---|---|
| greenhouse | speechify | 1086 | 66.0% | 66.0% | 1041 | 8 |
| greenhouse | veeamsoftware | 242 | 14.7% | 80.7% | 182 | 182 |
| greenhouse | gomotive | 148 | 9.0% | 89.7% | 125 | 125 |
| greenhouse | joblogic | 31 | 1.9% | 91.6% | 31 | 31 |
| greenhouse | coderoad | 28 | 1.7% | 93.3% | 24 | 24 |
| lever | spreetail | 27 | 1.6% | 94.9% | 24 | 24 |
| greenhouse | brkz | 23 | 1.4% | 96.3% | 19 | 19 |
| greenhouse | careem | 21 | 1.3% | 97.6% | 21 | 21 |
| lever | smart-working-solutions | 21 | 1.3% | 98.8% | 21 | 21 |
| greenhouse | globalli | 12 | 0.7% | 99.6% | 11 | 11 |
| greenhouse | banyancanopygroup | 7 | 0.4% | 100.0% | 7 | 7 |

| Across 11 boards | Total | Min | Median | Mean | Max |
|---|---|---|---|---|---|
| Postings | 1646 | 7 | 27 | 149.6 | 1086 |
| Distinct titles | 1506 | 7 | 24 | 136.9 | 1041 |
| Distinct base titles | 473 | 7 | 21 | 43.0 | 182 |

Postings quartiles, inclusive method: Q1 21.0, Q2 27.0, Q3 89.5. Excluding Speechify: 10 boards, total 560, min 7, median 25.0, mean 56.0, max 242. Greenhouse alone: total 1598, median 28. Lever alone: total 48, median 24.0.

**The mean describes nothing.** Three boards hold 89.7% of postings. The median board returns 27, and the mean is pulled to 149.6 by one board whose 1086 postings are 8 roles.

### Figures this falsifies

- **ADR-0001:27**: "Postings fetched per run across the full board set are on the order of one thousand. Estimated from 53 boards at roughly twenty open roles each; not measured." Falsified `[VERIFIED]`: 11 of 53 boards return **1646 postings**, 1.65 times the estimate for all 53. The measured replacement is 1646 postings per run on the 11 Tier A boards. The "twenty open roles" input is close as a median, 21 distinct base titles per board, but it fails as a volume estimate for two reasons: postings are not roles, and the distribution is not uniform.
- **ADR-0003:28**: "Roughly one thousand postings are fetched per run. Estimated as in ADR-0001; not measured." Falsified by the same measurement `[VERIFIED]`. ADR-0003 carries the figure by reference, not verbatim.
- **ADR-0003:31**, the growth projection. Recomputed at ADR-0003's own 2 KB per record and two runs a day `[VERIFIED]` arithmetic: snapshots cost 1.46 GB/year at 1000 per run, 2.40 GB/year at the measured 1646, and 4.06 GB/year at extrapolation A below. Deltas cost 14.6 to 36.5 MB/year at 20 to 50 new postings a day, and **the delta figure does not depend on per-run count**. `[BELIEVED]`: the measured volume makes the rejected snapshot option worse and leaves the chosen delta option's cost unchanged, so ADR-0003's decision is not weakened. Its stated figures are wrong.

**Not touched by this check:** ADR-0003:27, 2 KB per record, which describes the stored metadata record under ADR-0011, not the raw payload. And ADR-0003:29, 20 to 50 genuinely new postings a day. Check 1 gives a partial handle on the second `[VERIFIED]`: across the 9 Greenhouse boards, still-open postings first published in the 7 days before fetch number 69, 9.9 a day. In the final 24 hours there were 29: veeamsoftware 19, gomotive 9, careem 1. That is a lower bound on 9 boards only, because anything published and closed inside the window is absent. It neither confirms nor falsifies a 53-board rate.

### Extrapolation to the 53-board registry. Not a measurement

`[BELIEVED]`. Assumptions: the 11 measured boards contribute their measured 1646, and each of the other 42 contributes a fixed figure taken from the 11. The 42 are Tiers B to D (`docs/architecture-2.0.md` coverage table): Ashby, Workable, SmartRecruiters, JazzHR, Manatal and others, 19 of them "Pakistani-dominant". **Tier A is not a random sample of the registry**, so none of these figures is more than a range marker.

| | Assumption for the 42 unmeasured boards | Total |
|---|---|---|
| A | measured median, 27 each | 2780 |
| B | measured mean excluding Speechify, 56.0 each | 3998 |
| C | measured mean including Speechify, 149.6 each | 7931 |

### A citation in the brief that did not check out

The brief says "roughly twenty open roles per board" appears in ADR-0001, ADR-0003 and the architecture document. `[VERIFIED]`:

- ADR-0001:27 contains it verbatim.
- ADR-0003:28 carries it by reference, "Estimated as in ADR-0001".
- **Neither architecture document contains it.** `grep -n -i -E "thousand|1,000|1000|53 boards|twenty|fifty a day|volume" docs/architecture-2.0.md` matched only the Airtable limits at lines 74 and 75 and the board count at line 203. The same grep on `git show HEAD:docs/architecture-2.0.md` matched lines 74, 75 and 203. `grep -n -i -E "twenty|roles each|per board|thousand" docs/architecture.md` matched nothing.

## Check 3: what does Lever's `createdAt` mean?

### The detector was proven before any request

A page detector that silently finds nothing would falsely report "no date". It was fed a planted page `[VERIFIED]`. The page had a date meta tag, a JSON-LD `datePosted`, "Posted 5 days ago", "September 10, 2026", "10 Sep 2026", "9/10/2026" and a 13-digit epoch. The detector found 4 visible hits and 8 source hits. A date-free control page returned 0 and 0.

### Result

| Posting | `createdAt` raw | `createdAt` UTC | Date the page displays | Agree |
|---|---|---|---|---|
| smart-working-solutions `0c605546-9908-4d2e-9f44-197273172f82` | `1789033384439` | 2026-09-10T09:43:04.439Z | **none** | not comparable |
| smart-working-solutions `e3e9506e-8fe9-45fd-b703-bd4b3d85dbbc` | `1788500179387` | 2026-09-04T05:36:19.387Z | **none** | not comparable |
| spreetail `34c6437e-2541-4814-9910-19e12e354c7b` | `1786664492702` | 2026-08-13T23:41:32.702Z | **none** | not comparable |

The three were chosen from the saved Lever files to differ by several days: 6 days, then 21 days, spanning both boards.

**The pages show no date** `[VERIFIED]`. There is no page date text to quote, because none exists:

- **Visible text:** no date pattern of any tested form on the first two pages. On the third, the only match was `listed.` inside the description, a false positive on the word "listed". No date.
- **`<time>` elements:** none on any page.
- **Meta tags:** 17 per page, with names `X-UA-Compatible`, `viewport`, `twitter:card`, `twitter:title`, `twitter:description`, `twitter:label1`, `twitter:data1`, `twitter:label2`, `twitter:data2`, `twitter:image`, `og:title`, `og:description`, `og:url`, `og:image`, `og:image:height`, `og:image:width` and one unnamed. None is date-named. The label/data pairs are `Location` and `Team`, with values `India`/`Engineering`, `Pakistan`/`Engineering` and `Texas`/`Marketplace Fulfillment`.
- **Response header:** `Last-Modified` absent on all three.
- The headline block's visible text holds the title, the location list, the team and the commitment, and no date.

Per the brief, the check stops there. **Whether `createdAt` means published or record-created is not established.**

**Observed separately, not displayed.** Each page source carries one schema.org `JobPosting` JSON-LD block with keys `@context`, `@type`, `datePosted`, `description`, `employmentType`, `hiringOrganization`, `jobLocation`, `title`. The raw fragments `[VERIFIED]`:

- `"datePosted" : "2026-09-10"` against `createdAt` 2026-09-10T09:43Z
- `"datePosted" : "2026-09-04"` against `createdAt` 2026-09-04T05:36Z
- `"datePosted" : "2026-08-13"` against `createdAt` 2026-08-13T23:41Z

`datePosted` equals `createdAt`'s UTC calendar date on 3 of 3. The string `2026-` occurs exactly once in each page's source, in that field. The third case is informative about timezone: 23:41Z is 2026-08-14 in Pakistan time, and the field says 08-13.

`[BELIEVED]`: this is not independent evidence. Both values come from Lever's own record, and Lever likely derives one from the other. Lever's page labelling the date "posted" is Lever's own claim about `createdAt`, not an observation of when the posting went public. The operator decides whether that claim is enough for Measure A.

**What would settle it:** a posting that appears between two runs carrying a `createdAt` earlier than the previous run's clock would show `createdAt` preceding publication. That is the same two-run test ADR-0006 still needs. Lever's API documentation was not consulted; it is outside this repository.

## Check 4: can Himalayas be paginated newest-first and stopped early?

Research 0003:51 was read first to avoid spending requests on guesses. It records browse as "cursor pagination" and search as taking `page`. The envelope's own `comments` field then named the parameter, verbatim `[VERIFIED]`: "21/08/2026: Cursor pagination is now available and is the preferred way to page through the feed. Pass the nextCursor value from each response back as ?cursor=. It is faster than offset and will never return the same job twice. The offset parameter is deprecated and will be removed in a future release."

### Does `sort=recent` order by recency? No

`https://himalayas.app/jobs/api/search?sort=recent&limit=20` returned HTTP 200 with **13 jobs, not 20**, and `pubDate` is not monotonic `[VERIFIED]`:

| Position | `pubDate` raw | UTC 2026 | Versus previous |
|---|---|---|---|
| 0 | 1789487079 | 09-15 15:44:39 | |
| 1 | 1789127040 | 09-11 11:44:00 | descends |
| 2 | 1788901271 | 09-08 21:01:11 | descends |
| 3 | 1789487416 | 09-15 15:50:16 | **increase** |
| 4 | 1788048343 | 08-30 00:05:43 | descends |
| 5 | 1789487416 | 09-15 15:50:16 | **increase** |
| 6 | 1789487416 | 09-15 15:50:16 | tie |
| 7 | 1788048341 | 08-30 00:05:41 | descends |
| 8 | 1789498713 | 09-15 18:58:33 | **increase** |
| 9 | 1789498648 | 09-15 18:57:28 | descends |
| 10 | 1789498606 | 09-15 18:56:46 | descends |
| 11 | 1789498598 | 09-15 18:56:38 | descends |
| 12 | 1789498530 | 09-15 18:55:30 | descends |

**Order breaks at positions 3, 5 and 8.** The search envelope carries no `nextCursor`; its keys are `comments`, `limit`, `offset`, `totalCount`, `updatedAt`. Whether some other `sort` value orders by recency is not established.

### The browse endpoint is newest-first

`https://himalayas.app/jobs/api?limit=20`, then `nextCursor` followed twice, for three pages and two page boundaries. Every `pubDate`, in order, all on 2026-09-15 UTC `[VERIFIED]`:

Page 1: 17:22:51 17:22:48 17:21:02 17:16:24 17:16:23 17:09:27 17:09:10 17:08:26 17:08:14 17:07:01 17:06:18 17:05:22 17:05:21 17:04:01 17:02:41 17:01:12 17:00:21 17:00:10 16:59:46 16:58:45

Page 2: 16:58:45 16:58:11 16:57:52 16:55:41 16:54:52 16:54:25 16:53:59 16:53:48 16:53:47 16:53:42 16:53:23 16:52:36 16:50:32 16:48:25 16:48:15 16:47:48 16:46:38 16:46:38 16:46:25 16:45:03

Page 3: 16:44:43 16:42:47 16:42:46 16:41:48 16:40:55 16:38:59 16:38:52 16:37:44 16:37:20 16:37:08 16:36:35 16:36:29 16:34:18 16:34:12 16:33:16 16:28:48 16:28:48 16:14:57 16:00:33 15:51:25

Raw first and last per page: `1789492971`...`1789491525`, `1789491525`...`1789490703`, `1789490683`...`1789487485`.

- Increases anywhere in the 60 values: **none**. Ties within a page at page 2 position 17 and page 3 position 16.
- Boundary 1 to 2: 16:58:45 then 16:58:45, a tie in whole seconds, with different guids. Boundary 2 to 3: 16:45:03 then 16:44:43, descending.
- Distinct `guid` values: **60 of 60**, no duplicate across pages. Jobs carry no `id` key, so `guid` is the identifier.
- The 2026-09-11 browse page on disk agrees: 20 values, no increases, ties at positions 1, 3, 4 and 5.

Each cursor decodes from base64 to the last job's `pubDate` at microsecond precision, plus an integer `[VERIFIED]`:

| Page | `nextCursor` | Decodes to |
|---|---|---|
| 1 | `MjAyNi0wOS0xNVQxNjo1ODo0NS40MjE0OTdafDIyMjExNjU` | `2026-09-15T16:58:45.421497Z|2221165` |
| 2 | `MjAyNi0wOS0xNVQxNjo0NTowMy4xNzc0NjJafDIyMjI0NzE` | `2026-09-15T16:45:03.177462Z|2222471` |
| 3 | `MjAyNi0wOS0xNVQxNTo1MToyNS43MTEwMTdafDIyMjIyNTU` | `2026-09-15T15:51:25.711017Z|2222255` |
| 2026-09-11 on disk | `MjAyNi0wOS0xMVQwMjo1Mzo0OS4wODc2NTBafDIxOTM0OTE` | `2026-09-11T02:53:49.087650Z|2193491` |

`[BELIEVED]` from that structure: this is a keyset cursor on a sub-second publication timestamp, with the integer breaking ties. The integers are not monotonic, 2222471 then 2222255, so the integer is only a tie-breaker. A keyset cursor means postings arriving at the top during paging cannot shift later pages. That property is inferred, not observed.

### Is the cursor usable on both endpoints? Browse only

| Endpoint | Accepts `cursor` | Evidence |
|---|---|---|
| `/jobs/api` browse | **Yes** | Pages 2 and 3 continue strictly below the cursor, with no guid repeated `[VERIFIED]` |
| `/jobs/api/search` | **No, silently ignored** | The acceptance test was fixed before the request: accepted only if no job is newer than the cursor's 15:51:25 and the result differs from r1. r5 returned HTTP 200 with the same 13 guids in the same order as r1, 5 of them newer than the cursor, and no `nextCursor`. r1 and r5 are byte-identical, sha256 prefix `08eb8d3ffb2f15de` `[VERIFIED]` |

### Does pagination terminate? Not established

`totalCount` was 103947 on browse, about 5,198 pages at 20 each, and not followable inside a 7-request cap. End-of-feed behaviour, a null or absent `nextCursor` on the last page, is untested. **What would settle it:** follow the cursor to the end, or find a filtered browse query small enough to exhaust in a few pages. Research 0003 lists filters for search, not for browse. The proposed stopping rule stops on age and never needs the feed to end. A rule that pages past a quiet period, however, does need end-of-feed behaviour defined.

### Envelope `updatedAt` and the cache-age question

`updatedAt` equals the newest `pubDate` **on the page returned**, on every observation, cursor pages included `[VERIFIED]`:

| Observation | Request UTC | Envelope `updatedAt` | Newest `pubDate` on that page | Equal | Newest posting's age at request |
|---|---|---|---|---|---|
| 2026-09-11 browse p1 | 21:06:55 on 09-11 | 15:50:13 on 09-11 | 15:50:13 | yes | 5.28 h |
| r1 search | 18:59:40 | 18:58:33 | 18:58:33 | yes | 67 s |
| r2 browse p1 | 19:00:34 | 17:22:51 | 17:22:51 | yes | 97.7 min |
| r3 browse p2 | 19:00:49 | 16:58:45 | 16:58:45 | yes | n/a, cursor page |
| r4 browse p3 | 19:01:02 | 16:44:43 | 16:44:43 | yes | n/a, cursor page |
| r5 search | 19:02:11 | 18:58:33 | 18:58:33 | yes | 3.6 min |
| r6 browse p1 | 19:08:05 | 17:22:51 | 17:22:51 | yes | 105.2 min |
| r7 browse p1 | 19:14:07 | 17:22:51 | 17:22:51 | yes | 111.3 min |

**`updatedAt` is not a cache timestamp.** On cursor pages it moves to that page's own newest posting. The 2026-09-11 log's "5.27 hours stale" is therefore the age of the newest posting on browse page 1, not a measured cache age. The 2026-09-11 figure above, 5.28 h, uses that file's mtime as request time; the original run's 5.27 h used its start clock.

**Browse lags search** `[VERIFIED]`. At r1, 18:59:40Z, search's newest posting was 67 seconds old. At r2, 54 seconds later, browse's newest was 97.7 minutes old. Five postings on search with `pubDate` between 18:55:30 and 18:58:33 were absent from browse pages 1 to 3:

- `routeware-inc/jobs/director-of-ux-2818613251`, 18:58:33
- `remote/jobs/senior-product-manager-remote-build-9121090433`, 18:57:28
- `mercor/jobs/bengali-document-specialist-fully-remote-upto-12-hr-1530477794`, 18:56:46
- `assist-world/jobs/internal-billing-revenue-cycle-specialist`, 18:56:38
- `veles-productions-sp-z-o-o/jobs/3d-senior-animator-freelancer-4301003517`, 18:55:30

r6 repeated browse page 1 seven and a half minutes after r2 and got byte-identical content, sha256 prefix `da447c4c7f309eef`. Same 20 guids, and still none of the five. Search was byte-identical between r1 and r5 as well. `[BELIEVED]`: both endpoints serve from caches, and browse's is older. Whether browse lags because of caching or because it filters those postings out is not established.

**The last request went to the late-insertion test, and the test could not run.** The question was fixed beforehand: do the five search-only postings reach browse, and carrying which `pubDate`? If one arrived carrying its 18:5x `pubDate`, that would be a posting entering the newest-first feed below a later wall-clock time, which is the failure point 2 of the recommendation below guards against. r7, at 19:14:07Z, 13.5 minutes after r2, was byte-identical to r2 and r6: sha256 prefix `da447c4c7f309eef`, the same 20 guids, newest `pubDate` 17:22:51, now 111.3 minutes old, and none of the five `[VERIFIED]`. Browse did not refresh inside a 13.5-minute window, so there was no refresh to observe. **Late insertion is neither confirmed nor ruled out.**

Other observations `[VERIFIED]`, causes not established:

- `totalCount` differs between endpoints at the same minute: search 107816, browse 103947. On 2026-09-11 browse reported 100509.
- Search returned 13 jobs against `limit=20`.
- Research 0003:51 says `pubDate` is "ISO 8601". It is an integer, epoch seconds, on every job observed, 2026-09-11 and today.

### What this means for the proposed stopping rule

**RECOMMENDATION**, not a decision:

1. Read from browse, `/jobs/api`, with `cursor`. Not from search, which is neither ordered by recency nor paginated by cursor.
2. Do not key the stop to the previous run's wall-clock time. With browse trailing search by at least 97.7 minutes (observed), a posting can reach browse after a run with a `pubDate` earlier than that run's clock. A wall-clock cutoff would never read it again `[BELIEVED]`.
3. Key the stop to the newest `pubDate` actually stored by the last successful run, minus an overlap window at least as long as the largest lag observed, and deduplicate on `guid`.
4. Decide what the rule does when a run pages past a quiet period without meeting an old posting, since end-of-feed behaviour is untested.

## Discrepancies found in records and in the brief

None of these was edited. A human writes record changes.

- **The architecture document does not contain the twenty-per-board figure**, contrary to the brief. See check 2.
- **ADR-0026:15 lists 18 Lever keys as every key on all 48 postings.** The union is 20; it omits `salaryDescription` and `salaryDescriptionPlain`, which appear on one `spreetail` posting. The error originated in the 2026-09-11 report's summary, and the backfill log records the correction. ADR-0026's conclusion stands `[VERIFIED]`. ADR-0026 is **untracked** in git, dated 2026-09-11, status accepted.
- **Research 0003:51** says Himalayas `pubDate` is ISO 8601 (observed: epoch seconds), and says search pages by `page` (untested; search returned no cursor and ignored one).
- **STATE.md was stale** before this session. Its verified-against line named `ed0c4f4` while HEAD was `26d0073`, and the spike row read PENDING, "not run", four days after the spike ran.
- **MAP.md was stale before this session.** `python tools/generate_map.py --check` exited 2 before any file was written. The only difference was one added row for the untracked `docs/decisions/0026-employer-provenance.md`, taking the count from 38 to 39.
- **`logs/README.md`** said "No logs yet ... The first row lands when the first implementing session runs." These two sessions are diagnostic, not implementing. The sentence was reworded so it does not contradict the new rows.

## Checked and found already correct

`[VERIFIED]` unless marked.

- The 11 board files on disk are byte-identical in size to the 2026-09-11 run's printed counts.
- `raw_responses/` is ignored by `.gitignore:18`, including the new `.html` pages.
- Greenhouse `meta.total` equals the returned posting count on 9 of 9 boards.
- `updated_at` is never earlier than `first_published`, 0 of 1598.
- String and instant equality of `first_published` and `updated_at` agree on every board.
- ADR-0026's claim that no Lever key contains `compan`, `employ` or `org` holds on the full 20-key union.
- The 2026-09-11 verdict harness still produces 11 of 11 expected verdicts and rejects every parser trap.

## Rejected alternatives

- **Re-fetching Greenhouse or Lever JSON for checks 1 and 2.** The brief forbids it, and the disk held everything.
- **Measuring ages from today.** That would have added about 3.9 days to every age.
- **Stripping base titles with a regex.** The first attempt removed the last `" - "` segment with `\s+-\s+[^-]+$` and reported 12 base titles. It was wrong: four titles ending in `Winston-Salem, NC, USA` survived, because that city name contains a hyphen. Replaced by exact equality with the posting's own location field, which gives 8.
- **Fetching `https://himalayas.app/docs/openapi.json` to learn parameter names.** The response envelope named the cursor parameter for free, and behaviour, not documentation, was the question. It would have cost 1 of 7 requests.
- **Reusing the 2026-09-11 browse cursor.** A four-day-old cursor could fail for staleness and confound the test.
- **Paging search by `page` or `offset`.** Not the brief's question, and the API marks `offset` deprecated.
- **Treating JSON-LD `datePosted` as "the date the page shows".** It is not displayed. It is reported separately, and the check stopped as briefed.
- **A new frontmatter type for logs.** `tools/generate_map.py` requires `type` and `description` and has no `log` type; adding one is a tooling change outside this brief. Logs use `research`, defined in `MAP.md` as "a dated snapshot of what was found, valid as a record of that moment". Flagged for the operator.
- **Committing.** Not requested, and a commit is a write to a branch.

## Incidents

- **Description text reached the terminal.** The first pass of check 3 filtered meta tags on the substring `time`, which matched `Full-Time` inside `og:description` and `twitter:description`. It printed employer description excerpts for two postings to this session's terminal output. Nothing reached a repository file, and none is quoted here. The meta check was re-run filtering on attribute names only.
- **The base-title regex overcounted**, as described under rejected alternatives. It was caught by printing the 12 titles before relying on the count.

## Not done, and not established

- Whether browse pagination terminates, and what the last page looks like.
- Whether any `sort` value makes search recency-ordered.
- Why browse trails search, and whether late postings enter browse with their original `pubDate`. Browse page 1 stayed byte-identical from 19:00:34 to 19:14:07, so no refresh occurred to test against. **What would settle it:** request browse page 1 until its `updatedAt` advances, then check whether `routeware-inc/jobs/director-of-ux-2818613251` appears with `pubDate` `1789498713`.
- What `createdAt` means on Lever. What `first_published` means on Speechify.
- What rewrites Greenhouse `updated_at` in batches.
- Postings per run for the 53-board registry, 42 boards unmeasured.
- The genuinely-new-per-day rate for ADR-0003:29, and the 2 KB record size for ADR-0003:27.
- The second spike run for ADR-0006. The EU Greenhouse API host. Both still not done.
- No decision record written or edited. `docs/reference/endpoint-shapes.md` not created. Nothing committed.

## Recommendations

**RECOMMENDATION**, not decisions:

1. Supersede or annotate the volume assumptions at ADR-0001:27 and ADR-0003:28 with the measured 1646 postings on 11 boards. The new assumption should distinguish postings from roles, since one board turns 8 roles into 1086 postings.
2. Annotate ADR-0026:15 in place with the two missing keys. CLAUDE.md permits a factual correction in place with a dated annotation.
3. Do not treat Greenhouse `updated_at` as an edit or liveness signal in any lifecycle logic.
4. Run the second spike pass. One two-run comparison settles ADR-0006's propagation question and gives the only external test of Lever `createdAt` available without Lever's cooperation.
5. For Himalayas, apply the four points under check 4.
6. When committing: `MAP.md` as regenerated lists the untracked ADR-0026. Commit ADR-0026 in the same commit, or regenerate the map without it.

## The gates, exercised without committing

The pre-commit hook reads `git diff --cached`, so it was run with `GIT_INDEX_FILE` pointing at a throwaway index built from `git read-tree HEAD` in the scratchpad. That touches no branch and not the real index. `git config core.hooksPath` returned `.githooks` `[VERIFIED]`.

| Case | Staged | Built to | Result |
|---|---|---|---|
| A | `logs/2026-09-15-spike-followup-checks.md` only | Defeat gate 4: a log without `STATE.md` | `COMMIT BLOCKED: implementation work is staged but STATE.md is not.`, exit 1 `[VERIFIED]` |
| B | both logs, `logs/README.md`, `STATE.md`, `MAP.md` | Pass all five gates | exit 0 `[VERIFIED]` |

`git diff --cached --name-only` on the real index was empty before and after `[VERIFIED]`. Before regenerating, `python tools/generate_map.py --check` exited 2. After, `map: wrote MAP.md with 41 files` and `--check` exited 0 `[VERIFIED]`.

**Case B passes gate 5 only because ADR-0026 is on disk.** Gate 5 checks the working tree, not the staged set, and the regenerated map lists ADR-0026, which case B did not stage. A commit of exactly case B's files would carry a `MAP.md` naming a file absent from that commit `[BELIEVED]`. That is recommendation 6.

## Files written

- `logs/2026-09-15-spike-followup-checks.md`, this file.
- `logs/2026-09-11-endpoint-feasibility-spike.md`, retroactive.
- `logs/README.md`: two index rows replace the placeholder row; one sentence reworded.
- `STATE.md`: verified-against line, headline, two Pipeline rows updated and one added, Blocked paragraph, Known unverified section.
- `MAP.md`: regenerated.
- `raw_responses/`: 3 Lever pages and 7 Himalayas bodies, gitignored.
- Scripts and ledger in the session scratchpad only, outside the repository.
