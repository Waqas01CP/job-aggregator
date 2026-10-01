---
type: log
description: The fourth audit, of 783ba3e..015bead. No deletion was wrong and the deletion paths hold; five defects, none yet triggered (the clearing tool's confirmation, the agreement check, location strings the operator can take, the contract re-baseline, and eight stale mutations), and several wrong documents, CAPABILITIES.md among them.
status: current
---

# The fourth audit, 2026-09-30 UTC

| Header | Value |
|---|---|
| Date | 2026-09-30 UTC. The audit ran from 18:20Z to 20:46Z; the machine's local date was already 10-01 |
| Model | claude-opus-5-5 |
| Range | `783ba3e..015bead`, seventeen commits, 2026-09-26 to 09-30 |
| Mode | **Read-only.** This file and its index row were written afterwards, on the operator's brief |
| Brief | "Audit brief: every new way out of the display, and five days of building", `briefs/audit.md`, written by the implementing seat and relayed by the operator |
| Previous report | None in this folder. The seat's account of the third audit: `logs/2026-09-26-the-third-audit-and-the-first-scheduled-sweep.md` |
| Data read | `data` at `c5b29a6` (the basis of `CAPABILITIES.md`) and `8617ef8` (adds the 18:19Z run), `data-test` at `6a66eef`, cloned into the scratchpad |
| Subagents | None |
| Spent | **Airtable: 3 connector calls**, all reads (the schema, and `Delete`'s choices). GitHub's public API: 2 reads. Himalayas: 1 browse page. One `--test-mode --no-commit` run: 33 board requests |
| Not read | **The private repository.** The brief asked that the operator be asked first; he was not asked, so nothing here rests on it |

**Tags.** [C] checked in the audit, with the command shown. [I] inferred. [O] outside this repository.

**Footprint.** The repository's tree and refs were as found. All mutation runs were in scratch clones of the repository, and every background run was stopped before the report was delivered.

## 1. The verdict

**No deletion was wrong, and the paths that delete are sound.**
- The 25 public rows removed on 09-28 each meet D13 or D14 as written [C]. The 44 private rows cannot be checked without the private repository.
- `accepted` is deleted in one place only, `src/sweep.py:471`: on `Delete = yes`, once both records are read back from origin.
- Every deletion from `Jobs` checks the store restored from origin.
- D14 is judged at first sight everywhere, the sweep's step 6 included.
- D11's read-back refuses what the branch does not hold, and no command in a save can download on demand.
- Nothing aggregator-sourced is on either public branch, in any commit.
- All 90 mutations dated 09-26 to 09-30 are caught once 2 stale ones are re-expressed.
- 702 tests pass on 3.12 and 3.11.

**Five defects, none yet triggered. Three of them live in the new mechanisms that are supposed to protect the operator:**
1. **The clearing tool's confirmation is not tied to what the dry run showed.** A confirm can remove rows the dry run never listed, and those rows never come back. Four of its guards also have no test.
2. **The agreement check compared 0 of 20 postings live.** In practice it checks nothing, so the location filter handed to Himalayas goes unchecked.
3. **`rule_location` drops some postings the operator could take.** Examples: "Remote (US time zones)", "US, Canada, Asia", "Pakistan (On-site)" with no city. No stored public posting hits these patterns yet.
4. **The contract check's re-baseline can excuse a real change on the next check** (10-01). A malformed date can excuse changes indefinitely.
5. **Brief 8's build left 4 mutation files unable to run** (8 stale mutations). Three more guarantees have no test.

**Several documents are wrong, `CAPABILITIES.md` included:** four of its numbers are wrong; see its list in section 2.

## 2. A verdict for each item the brief listed

### The operator's decisions

| Decision | Verdict | Evidence |
|---|---|---|
| D12 | Correct | See "Is D12 closed?" below |
| D11 | Correct | See "Does D11 hold?" below |
| D13 | Incorrect in part | F4. The live drops are all correct [C] |
| D14, with his correction | Correct | See "Is D14 judged at first sight?" below |
| Search, and the catch-up | Correct | 6 of 6, then 7 of 7 caught. The first search morning read 23 pages, 460 postings, 361 new, 31 kept. The recovery walk read 30 pages and saved 599 [C] |
| Brief 8, and the order | Done | The report is held in `briefs/architecture.md` until this audit is in [C] |
| The `To review` filter | Cannot verify | No call was spent on it. His confirmation stands [O] |

**Is D12 closed?** Yes:
- `accepted` is deleted only at `src/sweep.py:471`, only on `Delete = yes`, and only once `removed_copies.json` and, while the row is still accepted, the accepted store are both read back from origin;
- step 1 never deletes `accepted`, and a clear removes nothing;
- `mark_delete` writes `Delete` only, and only to `accepted`;
- D12's file, re-expressed, is 9 of 9 caught.

**Does D11 hold?** Yes:
- the read-back compares the hash the re-fetched branch lists, and refuses a file that is missing or different;
- `GIT_NO_LAZY_FETCH=1` is set on every command, and `write-tree --missing-ok` never needs an earlier file;
- the test really runs on a partial fetch, and checks that the earlier file is absent;
- every live save since 09-28 has verified: 599, 13, 3, 9, 18 and 8 postings.

**If saving failed for good,** every morning's walk would read back to the age floor. The 09-28 recovery measured that at 30 pages and 41 requests, against 12 to 16 on a normal morning. Each such morning would escalate at once, and the sweep would hold every aggregator row. A week longer than 40 pages would be cut silently (F17).

**Is D14 judged at first sight everywhere?** Yes. Every path goes through `apply_chain` to `rule_age`, which reads `first_seen`: the run, the backfill, the projection, and the sweep's step 6. Each of the 7 public age removals was 35 to 967 days old at first sight. The walk's floor, one second past the limit, can only read further.

### The seat's five decisions inside Brief 8

| # | Verdict | Why |
|---|---|---|
| 1 | Correct | Without it, a regrouped row would hide its live group under the new representative. Its mutation is caught |
| 2 | Correct | Old records without the key are read by identity and reason, and a test holds one. `swept_at` compared as text is safe: an instant has one spelling, and no two runs share a second. The same-run tie is untested (F7) |
| 3 | Correct | Masked in the public log, named in the private store. But the dry run names aggregator rows nowhere (F1) |
| 4 | Right idea, emptied in practice | F3 |
| 5 | Mechanism incomplete | F1 and F2 |

### The numbered checks

1. **Deletion.** Correct for the sweep.
   - No path deletes without a durable record, or in the run that wrote it. The operator's early path and the clock check the store restored from origin.
   - Pairs keyed on identity and reason hold. Partial reads raise; the third audit's mutation for that is caught.
   - The tool deletes nothing and cannot reach production in test mode today. It can confirm on rows its dry run never showed (F1), and its guards are untested (F2).
2. **The skip by reason.** Correct, apart from the Lever-only nit (F15).
3. **D11 and the stop mark.** Correct.
4. **Filters.** Incorrect in part (F4).
5. **The Himalayas walk.** The whole-page stop, the pinned postings, the per-board mark, the floor and the cap are all correct, and their mutations caught. The cap is silent (F17). The agreement check is incorrect in effect (F3).
6. **Privacy.** Correct, across every file and every commit of both public branches:
   ```
   HEAD files naming himalayas.app: 0 | 'himalayas:' tokens: only "himalayas:browse", "himalayas:pakistan" | history adding himalayas.app or a himalayas source record: 0
   ```
   The sweep's removals, the clearing report and the agreement counts are masked or counts-only. The disagreements file goes to `local_outcomes_dir`. D11's full branch is private. On the how-to naming the repository, see F14.
7. **The re-baseline.** Incorrect (F5).
8. **Tests that cannot fail.** F6 and F7. The fitness meta-test now checks the quoted clause, and its can-fail test runs `problems()`, which closes the third audit's F6. Mutations, all run at `015bead` in scratch clones:

   | File | Result |
   |---|---|
   | Brief 8 | 28 of 28 |
   | D11 | 9 of 9 |
   | D12 | Refused; re-expressed, 9 of 9 |
   | D13 and D14 | 15 of 15 |
   | Search | 6 of 6 |
   | Catch-up | 7 of 7 |
   | Third audit | 13 of 13 |
   | Full-branch fix | 3 of 3 |
   | Brief 7's sweep file | Refused; re-expressed, 30 of 30 |
   | Projection | Refused; re-expressed, 20 of 21 (the survivor is equivalent) |
   | Private store | Refused; its re-expressed mutation caught (the other 11 were not re-run) |
   | Publication and state | 39 of 39 |
   | Run-log report | 22 of 22 |
   | Backfill | 6 of 6 |
   | This audit's own | 11 applied, 4 caught (F2, F7) |

   The seniority file was stopped, unfinished: it is out of scope, and its finds were never stale.
9. **Documents.**
   - Every `STATE.md` stamp is at or before its commit, across all 17 commits.
   - The three logs are right wherever measured.
   - The rest: F8 to F14 and F19.

### `CAPABILITIES.md`, every number checked

Measured against `data` at `c5b29a6` and the tree at `19ca94d` or `fcdc8d6`. ✓ means right, ✗ wrong, and ~ imprecise.

| Claim | | Evidence |
|---|---|---|
| 28 runs, 12.6 days; 0 retries, 0 failures; median 36 requests, max 41; 11 on an evening | ✓ | `run_log_report.py` |
| 824 read on 09-26, 1,283 on 09-27 | ✓ | Run logs |
| 32,831 fetched in total | ✓ | Run logs |
| 1,012 distinct stored | ✓ | `seen.json` |
| Freshness: 114 postings, median 5.4 h, 90th percentile 10.5, max 14.4 | ✓ | Recomputed |
| "Reaches the table / the display" | ✗ | 8 of the 114 were ever admitted |
| Selectivity: 1,283 read, 36 kept; 922 title, 258 location, 56 seniority, 11 age | ✓ | 09-27 morning log |
| 824 into 527 rows; largest group 134 | ✓ | 09-26 evening log |
| Himalayas before the change: 500 a morning, ~1,600 a day, 499 new over 7.3 h | ✓ | 1,642 a day computed |
| 93 of 100 closed to Pakistan | Not measured | Taken from the log |
| Himalayas after the change: 460, 23 pages, 361 new, 31 kept | ✓ | Run log |
| 420 of 420 | Not measured | Private data |
| 74 dropped and 17 admitted of 91; cutting lists at three changes nothing | ✓ | Reproduced from `raw_responses/` |
| 824 full postings in 9.8 MB | ✓ | 9,769,591 bytes |
| 172 calls, 17%; 89 rows; 8 calls a projection | ✓ | 09-30 morning log |
| About one display row a day | ✓ | Groups went 73 → 74 → 75 |
| "Settles near thirty" | ~ | Arithmetic, not a measurement |
| 25 / 6,123; 32 / 9,574; 9 / 1,817 | ✓ | `git ls-tree`, `wc` |
| 702 tests on 3.11 and 3.12 | ✓ | Both run |
| 354 mutations across 29 files | ✓ | Counted |
| "Re-run when the code they guard changes" | ✗ | F6 |
| 55 records, 4 superseded; 124 Changes rows across 42 | ✓ | Counted |
| 115 commits, the first on 09-01 UTC | ✓ | 115 at `fcdc8d6`; first at 2026-09-01T19:59:39Z |
| 22 session logs | ✗ | 21 |
| Start times 03:27 to 03:59 and 16:56 to 17:47 | ✗ | 03:26 to 04:34 and 16:18 to 20:02 |
| "Three to four hours late" | ✗ | 3.3 to 7.0 hours |
| "800 to 1,300 a run" | ✗ | 811 to 1,420 |
| "Keeping a few dozen" | ~ | 5 to 56 since 09-26; 222 to 303 before |
| 11 boards (9 Greenhouse), 79 terms in 4 families, 500 budget, 40-page cap, 10 a call, 15, 30 and 60% | ✓ | Configuration and code |
| 8 tables; `Jobs` 14 fields; 6 hook gates; Python 3.11 in production | ✓ | Connector, hook, workflows |
| 16 platforms probed; 1,646 postings | ✓ | Logs and `STATE.md` |
| Five audits; 86 of 86; four defects closed within a day | ✓ | Commits `5b82b5a`, `6ef16eb` |

### The slips the seat reported, re-checked

- **The second full save's failure** is fixed, and every save since has verified. The new test really runs on a partial fetch [C].
- **The age rule against the run's clock** is corrected everywhere, and its mutation is caught [C].
- **The two wrong estimates** are corrected in the logs. The start-time ranges are a third one the seat did not find (F8).
- **The double-counted mutation file:** 354 across 29 is now right [C].
- **The push before the suite (`aade660`):** GitHub's events show every commit in the range pushed 4 to 9 seconds after it was made. That fits a suite run before the commit, and neither proves nor disproves one.
- **The heredoc:** no damage. All 83 changed files are LF in the index and the tree, and every Python and JSON file parses [C].
- **The refuted Himalayas loss:** cannot verify; private data.
- **The repost research:** reproduced.
  - (a) 57 of 560 pairs, 459 postings, median 48 days, buckets 23/22/11/1, with folded keys.
  - (c) 12 postings, all Greenhouse, gone 23 to 130 hours. The audit's median is 54 hours to the seat's 59, likely a difference in where the gap is measured from.
  - (b) needs the private full postings.

## 3. Findings, most severe first

No finding reaches "data lost or corrupted". Probes live in `$SP/a4/p/tests/test_audit4_probes.py`, a scratch clone; `$SP` is the scratchpad.

### F1. Defect: a confirmed clear removes rows its dry run never listed (`src/clearing.py:77-89, 134-139`)

`dry_run_on_file` matches only the table and the days. The confirmed run then selects the rows again at its own clock, up to 48 hours later.

Probe E: two `Jobs` rows, 40 and 31 days old at the confirm. The dry run ran 47 hours earlier, when the second was 29 days old.
```
PROBE E: dry run rows: ['greenhouse:1'] | confirmed rows: ['greenhouse:1', 'greenhouse:2'] | written: 2 | kept out of the display now: ['greenhouse:1', 'greenhouse:2']
```
- **Why it matters:** `operator-removed` never returns. With a short threshold on `Jobs`, every row that crosses it during the 48 hours goes unseen, against the operator's "i do not want to miss any".
- **The dry run cannot show aggregator rows either.** It lists them as `<aggregator row>` (`clearing.py:149`) and writes nothing, so they are named nowhere he could review.
- **Seat decision 5, judged:** the mechanism checks the request, not the rows. Binding the confirm to the identities the dry run listed would close both gaps. The fix is the seat's to choose.

### F2. Defect (test gap): four of the clearing tool's guarantees survive their mutation

The audit's own mutations, run with `tools/mutate.py --why` in a scratch clone:
```
SURVIVED  a failed dry run validates a confirm
SURVIVED  a confirmed run counts as the dry run
SURVIVED  a test-mode confirm accepts a production dry run
SURVIVED  the clearing tool in test mode reaches production
```
All four guards are correct today, and nothing proves them.
- **The worst case, if it ever regressed:** a test-mode dispatch would build its client for production (`run.py:387`). That would set `Delete` on production `accepted` copies, and D12's path would then remove them from Airtable. They would stay in the stores.
- **The confirmation test** covers four cases: no dry run, another table, another threshold, and a dry run too long ago. It never covers a failed dry run or a confirmed one.

### F3. Defect: the agreement check compares nothing in practice (`src/run.py:468`)

It compares only browse postings no newer than the search's newest. Browse's first page is about 20 minutes of a feed of roughly 1,640 postings a day. The Pakistan search's newest posting is usually hours old.

The live test-mode run, 20:17Z:
```
himalayas:pakistan  ok  fetched 412 ... [agreement (ADR-0053): 0 of 20 browse postings compared, 0 excluded by the search, 0 the location rule would admit]
```
Then one browse request, set against what that walk stored. The publication times are given here as durations, since a public report carries nothing from a Himalayas posting:
```
search walk stored 412; its newest posting was published 6.3 hours before the run
browse page 1, read a minute after the run: 20 postings spanning 21 minutes, the oldest of them 3.9 hours newer than the search's newest | no newer than the search newest: 0
```
- **Against the record:** ADR-0053 (line 56) allows pushing the filter down only "while its agreement with that rule is checked". Line 58 compares "every posting on it".
- **Seat decision 4, judged:** testing identity against the seen store is right; a window of dates would misfire on the search's inversions. The added newest-date cut is what empties the check.
- **Evidence:** one live sample [C]. That it is usual follows from the two volumes [I].
- **The fitness test** proves the check can disagree on a built input. It says nothing about live data.

### F4. Defect (latent): `rule_location` drops places the operator can take (`src/filters.py:220, 261-283`)

`_PARTS` does not split on commas, and `classify_place` tests closed names before open ones. So one part naming both is closed. Any on-site word beside "pakistan" without Karachi is closed too.

Probe G, on constructed strings:
```
'US, Canada, Asia'                    -> DROPPED
'Europe, Middle East'                 -> DROPPED
'Remote (US time zones)'              -> DROPPED
'Anywhere (US preferred)'             -> DROPPED
'Remote/Hybrid - Lahore'              -> DROPPED
'Pakistan (On-site)'                  -> DROPPED
'Remote, Pakistan (office optional)'  -> DROPPED
'Remote - EST hours'                  -> kept
```
- **Against the record:** ADR-0041's 09-26 amendment says "one reachable place admits the posting" and "Time zones never exclude". Its on-site class is "a Pakistani city other than Karachi".
- **Against his words:** "time zone is not an issue".
- **Exposure today: none on public data** [C]. Of 413 distinct public locations, the rule drops 354. Every one is a country-restricted remote posting or a hybrid role in Islamabad or Lahore. Private data not checked.

### F5. Defect: the contract check's re-baseline can excuse a later change (`src/contract.py:157, 170, 205, 216`)

**No stored shape carries `since` yet.** The fingerprint on `data`, last written by `fc1da63` on 09-27, was checked:
```
$ git show HEAD:contract/fingerprint.json | grep -c '"since"'
0
```
So the first check on the new code, 2026-10-01, compares against `""`, and the 09-26 entry excuses any change to its four fields.

**A malformed date passes validation**, because it only needs ten characters. Probes H and H2:
```
PROBE H: no since -> 2026-09-26: ADR-0053: Himalayas is polle | since 2026-10-01 -> not excused
PROBE H2: entry dated '2026-19-26' loads; a change against a shape accepted 2026-12-01 is EXCUSED
PROBE H2: entry dated '9999-99-99' loads; a change against a shape accepted 2099-12-31 is EXCUSED
```
- **Against the unsent report:** its "a spent entry cannot excuse a later change" is untrue for the next check.
- **The window is one check,** and needs Himalayas to change one of the four fields that day.

### F6. Defect (tests that cannot fail): `19ca94d` broke 8 mutations, and 4 files refuse to run at HEAD

Every find in every mutation file, checked against HEAD:
```
2026-09-23-projection.json       REFUSED: [9] a failed projection exits 1 (0)
2026-09-24-private-store.json    REFUSED: [3] a private store failure exits 0 (0)
2026-09-25-sweep-and-fitness...  REFUSED: [4], [17], [18], [25] (0)
2026-09-26-d12.json              REFUSED: [5] Delete leaves the Jobs row behind; [7] a row due twice is named twice (0)
total 354 stale 8
```
- **When:** every one of the 8 matches at `aade660` and fails at `19ca94d`.
- **The seat's claim:** the log reports 28 of 28 for Brief 8's own file. It does not re-run the older files that commit touched, as it did for `368c641`. `CAPABILITIES.md` still says mutations are "re-run when the code they guard changes".
- **The guarantees hold.** The audit re-expressed the 8 against HEAD, in scratch only, and all 8 are caught:
  - D12: 9 of 9;
  - Brief 7's sweep file: 30 of 30;
  - the projection file: 20 of 21;
  - the private-store mutation: caught.
- **The one survivor** is "the skip reads the fourth store". Brief 8 reversed the rule it guarded, so it now reads the same file twice to the same effect. It should be replaced and recorded as equivalent.

### F7. Defect (test gap): three more guarantees survive their mutation

```
SURVIVED  the clock measures the publication date              src/sweep.py:538
SURVIVED  the skip ignores the private removal store           src/run.py:339-340
SURVIVED  a tie in swept_at goes to the first record written   src/projection.py:85
```
1. **The clock:** `make_row` gives every test row the same publication and first-seen date. So no test can tell the thirty days from `First seen` (ADR-0055) apart from `Published`. D14 admits rows up to 7 days old at first sight, so the wrong date would age rows out up to a week early.
2. **The private removal store:** nothing tests that a Himalayas row stored as `closed`, aged out or removed by the operator stays out.
3. **The tie:** it happens when the sweep and the tool write in the same run, and the tool's reason must win. The code is right today.

**Four of the audit's mutations were caught, each by a relevant test:** an invented reason returns; the disagreements file goes public; the clearing report names an aggregator; a deletion is not named in the log.

### F8. Wrong document: four numbers in `CAPABILITIES.md` are wrong, and two are stated too strongly

The full list is in section 2. The ones that change what a CV reader would believe:
- **Fetch start times.** The file says 03:27 to 03:59 and 16:56 to 17:47 UTC, "three to four hours late". The Actions API gives 03:26 to 04:34 and 16:18 to 20:02 for scheduled runs, 3.3 to 7.0 hours late.
- **Postings read per run.** It says "800 to 1,300"; the runs read 811 to 1,420.
- **Freshness.** "New postings reach the display a median of 5.4 hours" is first sight, not arrival in the display. Only 8 of the 114 postings were ever admitted. The numbers themselves are right.
- **Session logs.** It says 22; there are 21.

### F9. Wrong document: the unsent Brief 8 report (`briefs/architecture.md`) would pass these errors to the chat

- **Item 7:** "a spent entry cannot excuse a later change" is untrue for the next check (F5).
- **"A quiet evening's sweep 2":** that held while `Jobs` had more than 100 rows. The last two evenings spent 1 call each [C].
- **"28 of 28 mutations are caught":** true for Brief 8's own file, silent about the 4 files it broke (F6).
- **"ADR-0041's Confirmation against ADR-0031: two live records conflict":** not forced, in the audit's reading. A drop reason can name the field and quote the home list from `config/eligibility.json` at run time. That puts no country in code, which is all ADR-0031's audit reads. For the chat to judge.
- **"Search's order ... postings published after the 09-29 walk sat as deep as page 19"** sits uneasily with a 5-page walk storing them. The likely explanation is refreshed publication dates on postings already stored. Only the private seen store can settle it.

### F10. Wrong records, for the architecture chat

- **ADR-0050, 09-28 annotation.** It carries the wrong start-time ranges, so its "about fourteen hours" longest wait for a copy is wrong. Scheduled runs have been 16.0 hours apart (09-28T04:00Z to 20:02Z). "Nothing else removes a row" is now untrue, given ADR-0055's clock and tool.
- **ADR-0041.**
  - "Keywords never reject" (line 94) and "On every ATS board in the slice, nothing is dropped" are untrue: the 18:19Z run dropped 253 ATS postings on keywords in free text.
  - The quotation "time zones do not matter" is in no log. The 09-26 log records "time zone is not an issue".
- **ADR-0043.** "By the skip for its `closed` rows alone" contradicts its own principle and ADR-0055.
- **The index.** It says 123 Changes rows. The audit counts 124 across 42 records, ADR-RULES included, and nothing in `docs/decisions/` changed after `fe33d93` [C]. The seat's count is right.

### F11. Stale document: the Airtable descriptions predate ADR-0055

The schema, read through the connector:
- **`Jobs`:** "An unclassified row stays until its posting has been closed fifteen days (see Closed) or a rule drops it". That leaves out the thirty-day clock and the operator's tool.
- **The rejection tables** mention no early removal by the tool.

These are the descriptions the operator reads in the browser.

The base itself is right: 8 tables, `Jobs` with 14 fields, and `Delete` on both `accepted` tables as a single select whose one choice is `yes` [C].

### F12. Stale document: `docs/reference/retention.md` contradicts itself

- **Line 14:** "Neither clock is ... first-seen", yet line 24 adds one.
- **Lines 69-71:** "No row has been classified, no sweep has executed".
- **Lines 84-86:** "A status change discards the old copy's reason", which D12 reversed, as lines 36-38 of the same file say.
- **Lines 146-154:** "The sweep is unbuilt ... the sweep loads them from here". It loads them from `config/sweep.json`.

### F13. Stale documents: `README.md`, `CLAUDE.md`, the workflow, the configuration

- **`README.md`**
  - It repeats the wrong start-time ranges.
  - Line 121 says "Fetch it first with `git fetch origin data:data`". So do three tool docstrings. That is the fetch the seats file forbids (see F20).
- **`CLAUDE.md`, the workflow and `src/run.py`.** A refused or failed clear exits 2. The `CLAUDE.md` exit-code paragraph and `fetch.yml`'s exit-2 comment and warning do not name it, so a refused confirm shows green with a warning that names other causes. `run.py`'s module docstring does not name the sweep either. This is the class of the third audit's F7.
- **`config/eligibility.json:4`.** The note describes the rule as first built: "older than this at the run is dropped", and Lever "first seen within this many days is kept". The code judges at first sight and never drops Lever for age.

### F14. Stale document: the secrets how-to contradicts itself

Line 164 names the private repository. Line 166 says "The repository's name is kept out of this public repository".

**The operator's call; the audit's view is that the name is harmless as a credential.** A private repository answers 404 without the token. It has also been public in history since `fe07242`. But the code scrubs the name from run logs as a secret (`src/run.py:92`), so one of the two should change. Correcting the sentence is the cheaper fix.

### Nits

**F15. A retired member hides a live posting of the same group.** Probe I:
```
PROBE I: kept out: ['lever:1'] | groups sent: [] (lever:2 is open and admitted, but not shown)
```
Under D14 only a Lever row can reach this, since Lever is never dropped for age.

**F16. Clearing `Jobs` also takes classified rows' rejection copies early,** and the dry run counts `Jobs` rows only. Probe F:
```
PROBE F: dry run would_remove 1 (Jobs rows only) | after the next sweep: Jobs 0 , not-a-fit copies 0
```

**F17. Hitting the 40-page cap is silent.** Only `pages: 40` shows it (`run.py:627-636`). A recovery walk after several failed saves, in a busy week, would cut the oldest days unannounced.

**F18. ADR-0052's widening case has no test.** Its Confirmation asks that raising the limit and backfilling brings rows back with their `first_seen` intact. By construction it would [I].

**F19. `STATE.md` keeps a DONE row.** The "Daily sweep" row reads DONE since 09-26, against its own rule that DONE rows move to `completed.md`. Separately, the schema reference's 09-30 annotation on `Delete` has no Changes row.

**F20. This repository has a local `data` branch.** It was created 2026-09-28T16:18:42Z by `fetch origin +data:data` (the reflog prints 21:18 in local time). No log records who ran it. See F13 for the documentation that tells readers to do exactly this.

**F21. The brief misquotes the operator once.** It gives "no job post more than a week old"; the log has "i do not want a job post more than a week old".

## 4. What was checked and found correct

The verdicts in section 2 carry most of it. Beyond them:
- **The live removals.** The 25 public rows removed on 09-28 (18 on location, 7 on age) each follow D13 or D14 as written. Every age drop was 35 to 967 days old at first sight, and every location drop lists only places outside Pakistan [C].
- **The run logs since the third audit.** The deletions of 25 on 09-28 and 44 on 09-29 match the brief. The 09-27 full save failed and escalated at once, as D9 requires. The recovery walk of 09-28 read 30 pages [C].
- **The new skip, live.** The first run on the new code, 18:19Z, read `stored_identities: 0`. Every removal so far was a rule's drop, which returns, and the public removal store holds exactly those reasons [C].
- **The third audit's repairs.**
  - F2: the four tables must be distinct.
  - F3: the month count is guarded.
  - F4: step 3 no longer deletes a copy step 1 removed.
  - F5: its four survivors are now caught (13 of 13).
  - F6: the meta-test checks the clause.
  - F7: `CLAUDE.md` and the workflow name the sweep.
  - Nits: the fake base enforces ten records a call and refuses a missing delete; the stamp gate reads seconds; ADR-0006's count is corrected; the seats file's push line is corrected.
- **Test mode.** `TEST_MODE` is set on the fetch step itself (`fetch.yml:141`), and `from_env` binds the tool to the four test tables [C].
- **The suite.** 702 tests pass on 3.12, and 702 on 3.11 under `-W error::ResourceWarning` [C].
- **Every `STATE.md` stamp** is at or before its commit [C].
- **The logs' figures** that can be measured from public data all reproduce [C], apart from the repost median noted in section 2.

## 5. What was not checked, and why

- **Anything in the private repository:** the 44 private removals, 420 of 420, the full branch's contents, and the disagreements file. The brief asked that the operator be asked first, and he was not.
- **The clearing tool live, and the clock's first removal** (about 2026-10-17 [I]). Neither has run.
- **Whether F5's window is hit** on the 10-01 contract check. It had not run when the audit closed.
- **Airtable's `Classified at` on a cleared `Status`:** still unverified. D12 makes it harmless for deletion.
- **The `To review` view's filter.** It would have cost a call, and the operator confirmed it himself.

## 6. Subagent claims not re-checked

None. No subagent was used.

## Added while writing the report

*Not part of the audit as delivered. Written 2026-09-30T21:10Z.*

- **F3's evidence is redacted here.** As delivered to the operator, it quoted the publication times of the search's newest posting and of browse's first page, and the oldest stored posting of the walk. Those come from Himalayas postings, which this folder must never carry, so the output is restated as durations computed from the same values. The finding and its verdict are unchanged.
- **F10 cites ADR-0041's "Keywords never reject" at line 94.** It is at line 92: `grep -n "Keywords never reject" docs/decisions/0041-location-admits-unless-excluded.md` prints `92:`. The wording quoted is right.
- **Commit `1418042`, made after the audit closed, approves the dry run's 48 hours** as the operator's own number. F1 judged the mechanism, not the number, so it stands as written.
