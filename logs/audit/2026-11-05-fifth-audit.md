---
type: log
description: The fifth audit, of 015bead..b811455. No deletion was wrong and every delete waits for its record on origin; 1,080 tests pass on both Pythons and all 351 mutations of the range are caught; but capped walks lose postings for good, aggregator postings sit on main in ten cassettes, the agreement check's twelve disagreements went unread, and a cleared classification is stored as unreviewed.
status: current
---

# The fifth audit, 2026-11-05 UTC

| Header | Value |
|---|---|
| Date | 2026-11-05 UTC. The audit ran from 16:14Z to 22:11Z, stopped from 16:57Z to 20:47Z by the operator's usage limit; the machine's local date was 11-06 from 19:00Z |
| Model | claude-opus-5-5 |
| Range | `015bead..b811455`, 130 commits, 2026-10-01 to 11-05 |
| Mode | **Read-only.** This file and its index row are the only files written in the repository |
| Brief | "The fifth audit, `015bead..b811455`, in Measure A's window", `briefs/audit.md`, written by the implementing seat and relayed by the operator |
| Previous report | `2026-09-30-fourth-audit.md` |
| Data read | `data` from a fresh clone, at `c61b483` and then `3d0154c` (the run of 11-05T20:33Z, the first on `b811455`); `data-test` at `44d5e4c`; the private repository's `data`, `data-test`, `data-full` and `data-test-full`, each cloned depth 1 into the scratchpad, remote dropped |
| Subagents | Sixteen read-only reviewers were started at 16:30Z. All sixteen stopped at the operator's usage limit by 16:57Z and none returned a result. Nothing below rests on them; see section 6 |
| Spent | **Airtable: no call.** **The private repository: 4 read-only clones**, one per branch, the token in git's environment config and never on a command line. **Network otherwise:** 2 clones and 1 pull of this repository's public data branches; 2 installs of `requests` from PyPI into scratch environments. No job board was asked anything |
| Heavy work | One job at a time, below normal priority, idle sleep held off: the suite on 3.12 then 3.11; 231 target lists run alone; 351 mutations in 239 minutes; then the audit's 2 |

**Tags.** [C] checked in this audit, with the command or probe shown or named. [I] inferred. [O] outside this repository.

**What this report cannot carry.** Every count below that comes from an aggregator is a count. No identity, title, URL or employer of an aggregator's posting appears, nor any secret or Airtable ID.

## 1. The verdict

**No deletion was wrong, and every path that deletes waits for its record on origin.** [C]
- Each delete in `src/sweep.py` follows a durable record read from the store restored at the run's start, written in an earlier run.
- The six rows the 21-day clock took on 11-04 and 11-05 are in the private `removed_unreviewed.json`, written first; the one deleted on 11-05 was stored on 11-04.
- The merged view of `Jobs` the projection hands the sweep cannot show a row as it was not, for any of the three cases the brief names.

**The tests hold.** [C]
- 1,080 tests pass on 3.12.10 (319.5 s) and on 3.11.9 under `-W error::ResourceWarning` (290.5 s).
- All 351 mutations of the 47 files dated after 2026-09-30 are caught, each by a named failing test, under `--targeted`.
- Every one of the 231 target lists passes when run alone with no mutation, so no catch was a test failing for another reason.
- No mutation on record is stale: 0 problems over 76 files and 705 mutations.

**Four defects lose or hide postings or classifications. None is yet known to have cost the operator a role he could take:**
1. **A walk that reaches its page cap loses what it did not read, for good** (F1). The next walk stops at a mark set by the newest posting stored. Age is judged once, at first sight. Startup.jobs' first production walk, 10-21T17:57Z, read 80 pages and missed about the oldest eleven hours of its seven-day window. Nothing has read them since. Himalayas' capped walks since 11-01 run on the same mechanism.
2. **Aggregator postings are committed on `main`** (F2). Ten cassettes from nine aggregator platforms hold real postings' titles, employers and URLs; 229 of their URLs are also in the private store. ADR-0020 says no aggregator content reaches the public repository. ADR-0017 says to commit one real response per platform. For aggregators the two accepted records conflict, and no gate stands between them.
3. **The agreement check found what it exists to find, and nobody read it** (F3). Twelve times since 10-21 the Pakistan search failed to return a Himalayas posting the location rule would admit, the condition ADR-0053 makes the price of its pushed-down filter. Each was a workflow warning only, with no Health row, and the session logs called every one of those runs clean.
4. **A rejected row whose `Status` is cleared is stored as never reviewed** (F4). Its rejection copy then stays in its table for good, and its rejection store never gets his classification. A probe shows it on the in-memory base. With C1's 21 days, the clock reaches such a row on the first morning after the clear.

**Five more defects are latent:**
- the facts fingerprint misses the filter module's place reading (F5);
- Hacker News' job stories never have their title's place read (F6);
- `Who reads` calls an agency's founder a founder (F7);
- the targeted harness has no unmutated baseline (F8);
- the no-token guard misses one import form (F9).

**Several documents are stale**, `CAPABILITIES.md` and `STATE.md` among them, and the brief itself has six small errors. Section 3 lists them.

## 2. A verdict for each item the brief listed

| # | Item | Verdict | In short |
|---|---|---|---|
| 1 | The fourth audit's findings | Closed, with two closed in name only | F1 to F8, F12 to F14, F17, F18 and F21 closed; F19 and F20 closed in name only (F19 and F20 below); F15 and F16 open by the seat's choice, routed; F9, F10 and F11 cannot be verified |
| 2 | The classification flow | Incorrect in part | Every delete waits for its record on origin; the shared read is sound; a cleared classification is stored as unreviewed (F4) |
| 3 | The stored-facts overlay | Incorrect in part | A failed re-read leaves the old overlay; the fingerprint misses `src/filters.py` (F5) |
| 4 | The private stores and the public branches | Incorrect | Both public data branches are clean in every commit; `main` carries aggregator postings in its cassettes (F2) |
| 5 | The first keyed source | Correct, one guard gap | No path takes the key to a log, a commit, a branch or Airtable; the guard misses `import src.airtable` (F9) |
| 6 | The request ceiling of 400 | Correct basis; incorrect for capped walks | 69 runs, median 36, at most 104, reproduced; a capped walk loses its tail for good (F1) |
| 7 | Contract checks per source | Correct | Isolated per platform; exit codes and the workflow match `CLAUDE.md`; F5 of the fourth audit closed; all 15 platforms covered |
| 8 | `Who reads` | Correct on the saved data, one latent misreading | One label, never a word; an agency's founder or engineer would read as founder or engineer (F7), which none of 27,510 saved descriptions does |
| 9 | The November 1 switches | Correct | Off on every run before `285d228`; `285d228` is `62faca8` with five lines re-dated; the first run on it re-read, backfilled 229 and spent 32 calls |
| 10 | Dateless sources last | Correct in code; one document silent | Never dropped for age, sent with no `Order date`; `docs/versions/v1.0.0.md:58` states Measure A without them (F19) |
| 11 | Hacker News' free-text reading | Incorrect in part | The thread and the first line are read as documented; job stories' places are never read (F6) |
| 12 | Tests that cannot fail | Correct, one latent harness gap | Both suites pass, 351 of 351 caught, 0 stale; the harness can call a crash a catch (F8) |
| 13 | The records against the code | Incorrect in part | No two unsuperseded records found to conflict except ADR-0017 and ADR-0020 for aggregators (F2); stale numbers in `CAPABILITIES.md`, `STATE.md`, ADR-0062, `retention.md` and `v1.0.0.md` (F10 to F19) |
| 14 | Exit codes and failure paths | Correct | Every documented path exits as documented; D9 holds |
| 15 | The display's budget | Correct, one wording off by one | Every attempt counted; the 900th call is made and the 901st refused, where ADR-0062 says the 900th is refused (F12) |
| 16 | D2, D3, C1 and `AIRTABLE-MCP.md` | Correct in part | D2 reads the type exactly; D3 omits the other mode's tables without naming them (F13); C1 stores before it deletes, live; the guide is sourced and names his fields only |

### Item 1: the fourth audit's findings at `b811455`

| Finding | Verdict | Evidence |
|---|---|---|
| F1, the confirm and its dry run | Closed | Its mutations, in `2026-10-01-fourth-audit.json`, all caught in this audit's batch |
| F2, four clearing guards | Closed | Same file, all caught |
| F3, the agreement check compared nothing | Closed | 68 live runs since 10-02 read 1,360 browse postings: 1,296 the rule excludes, 34 returned by the search, 30 waited, 12 disagreements. It works; its output is F3 below |
| F4, place strings dropped | Closed | The seven strings kept and the five dropped, through today's `rule_location` [C]: 13 of 13 as required |
| F5, the re-baseline | Closed | `src/contract.py:227-279`: a time must parse as `YYYY-MM-DDTHH:MM:SSZ`, an undated shape is never excused, an entry timed after the check excuses nothing, and any change moves the shape's `since` forward (`:379`) |
| F6, stale mutations | Closed | `problems_in` over every file: 0 of 705; the suite's test for it ran in both suites |
| F7, three untested guarantees | Closed | Their mutations caught |
| F8, `CAPABILITIES.md`'s four numbers | Closed for those four | New stale numbers are F10 |
| F9, the unsent Brief 8 report | Cannot verify | Gitignored, and no longer the file it was |
| F10, the chat's records | Cannot verify in full | ADR-0050 and ADR-0041, two of the three it named, are superseded since by ADR-0062 and ADR-0057; not re-read line by line |
| F11, Airtable's descriptions | Cannot verify | Needs a call |
| F12, `retention.md` | Closed | 0 of its four stale phrases remain; a new stale line is F17 |
| F13, the fetch advice and exit codes | Closed | No `fetch origin data:data` advice left in `README.md`, `tools/`, `src/` or `docs/how-to/` [C]; `CLAUDE.md` names the clearing tool's exit |
| F14, the secrets how-to | Closed | The contradictory sentence is gone; the name stays, the cheaper fix |
| F15, a retired member hides a live one | Open, routed | Left as ADR-0043's design, the chat's |
| F16, clearing takes rejection copies | Open, routed | Reported, behaviour unchanged, a question for him |
| F17, the cap was silent | Closed | Every capped walk since logs `capped: true` and warns; what the cap costs is F1 below |
| F18, ADR-0052's widening | Closed | `tests/test_backfill.py:153` |
| F19, a DONE row in `STATE.md` | **Closed in name only** | Two DONE rows remain (F18 below) |
| F20, a local `data` branch | **Closed in name only** | The local branch is gone; the data branches still enter this repository's refs (F20 below) |
| F21, the misquote | Closed | Not repeated |

### Item 2: the classification flow

- **Every delete has a durable record first, read back, never in the run that wrote it** [C]. These paths delete:
  - step 2's `Jobs` rows (`src/sweep.py:557-560`);
  - step 3's rejection copies (`:593-596`, then `:602-604`);
  - `accepted` on `Delete` (`:627-634`);
  - superseded copies (`:462-475`);
  - `gone` (`:666-667`);
  - steps 4 to 7 (`:687-722`).

  Each tests `durable_has`, `durable_removal`, `copy_saved` or `kept_out_reason`. All four read the store restored from origin at the sweep's start, and every write goes to a store a later run reads.
- **The one shared read** (`src/projection.py:324-356`, `src/run.py:436-437`):
  - **(a) a stale field.** The operator's fields come from the read, and the pipeline's from what the upsert sent. A `Status` he sets after the read waits a run, as documented.
  - **(b) a row created this run.** It is added with the ID Airtable returned; a record without one gives `None`, and the sweep reads `Jobs` itself.
  - **(c) two records for one identity.** If the identity was written, the view is `None`. If it was not, the sweep sees both, as its own read would.
  - **Any upsert failure** gives no view at all (`:439-448`).
- **The rejection tables read only when needed.** No morning was found when a step needs them and none of the five reasons fires, except F4's orphaned copy. The live record: on 11-01 and 11-02 two rejection copies were "past 15 days but its outcome is not in the store; kept", and from 11-03 the tables were not read.
  - The same two rows most likely sat with a cleared status on every run that read the tables from 10-15 to 10-27 (`kept_after_a_clear: 2`). They were most likely re-classified on 10-27, so they wait for their rows' fifteen days, about 11-11 [I].
  - To settle it, read the two rejection tables and `Jobs`: 3 calls.
- **The anchor**, `last_copy_step_at` (`src/run.py:523`): it takes the last run whose sweep read every table and did not fail. Read; no case found where it moves wrongly.
- **The clocks, live** [C]:
  - `accepted test`'s copies, classified 09-23, were still there at the test runs of 10-21; only rejection copies were deleted.
  - In `Jobs`, the 21-day clock has removed 6 rows since C1, 1 on 11-04 and 5 on 11-05, each stored first. The brief's "removed nothing so far" was true when it was written.
- **The pipeline never writes `Status`.** The projection's upsert refuses any field outside its pipeline-owned set (`src/airtable.py:396-404`).

### Item 3: the stored-facts overlay

- **The fingerprint**, `src/facts.py:53-54`, covers `src/description.py`, `src/normalise.py`, `src/adapters/*.py`, `config/eligibility.json` and `config/who_reads.json`.
  - It misses `src/filters.py`, whose `place_names` derives `required_places` (`src/normalise.py:287-292`). That is F5.
  - The adapters import only `src/adapters/base.py`, which the glob covers.
  - `src/description.py` reads only `config/who_reads.json` at runtime (`:292-317`).
- **A failed re-read leaves the old overlay** [C]: the overlay is written only after the whole re-read succeeds (`src/run.py:263-270`). The overlay is rewritten whole from today's reader, so no stale key survives a re-read.
- **The live re-read of 11-05T20:33Z:** 76 files, 27,622 postings read, 0 unknown boards, 0 unparseable, fingerprint `3709f937dcda9241`. The audit's probe computes the same fingerprint from `b811455`'s tree.

### Item 4: what may reach a public branch

- **Both public data branches are clean in every commit** [C], `agents/lead/leakscan.py`. Every line added in every commit of `data` (143) and `data-test` (12) was searched for:
  - the 26,531 aggregator identities and 26,975 URLs the private stores hold;
  - every aggregator host;
  - any token of the form `<aggregator platform>:<id>`.

  It found 0 identities, 0 URLs and 0 hosts. 535 and 28 registry board IDs, and one Hasjob board ID in the test run of 10-21, are boards, not postings. No commit message on either branch carries a host or token.
- **`main`'s range outside the cassettes** carries no identity or URL from the private sets [C]. Its one 8-digit Hacker News identity, in `tests/test_adapters.py:704`, is in no store, no cassette and no public data.
- **`main`'s cassettes** are F2.
- **The publishable set is an allowlist** (`src/config.py:65-73`), so a source the build does not know stays private.
- **D9:** with the private store unrestored, aggregator boards are skipped with a reason (`src/run.py:1082-1089`), the projection runs public-only, and the run exits 2 and is marked failed at once (`:143-176`, `:1636`).

### Item 5: the first keyed source

**No path takes the key's value to a log, a commit, a branch or Airtable** [C]:
- It reaches only the Fetch step (`fetch.yml:172`) and the Check step (`contract.yml:90`), never a test step. No step echoes the environment.
- It travels only as a bearer header (`src/http_client.py:173-175`), never in a URL. `tests/test_http_client.py:249-258` holds that, including the error text.
- `requests` 2.34.2 strips Authorization on a redirect to another host (`sessions.py:154-159`, read in the scratch environment).
- `SECRET_ENVS` names it (`src/run.py:127-130`) for the run's scrub.
- `src/contract.py` has no scrub, and needs none: a check failure records the exception's class and location only (`:326-330`), and an HTTP error's text names a URL (`:351-352`).
- No cassette or fixture holds `Bearer` or a key-like value.
- **A run without the key** marks that one board failed, makes no request, and touches no other (`src/run.py:848-855`).
- **An ended key** returns 401, which is not retryable (`src/resilience.py:22`), so that board alone fails. Breakers are per platform.
- **The guard's test** (`tests/test_airtable.py:597-647`) is narrowed to what was approved and can fail, but misses two forms (F9).

### Item 6: the request ceiling

- **The basis reproduces exactly** [C], `tools/runs.py`: 69 production runs of 09-17 to 10-20, median 36 requests, at most 104. The one run that stopped early, 10-14T03:47Z, stopped on the circuit breaker.
- **Since 10-20:** 32 runs, at most 184 requests of 400.
- **The test-mode run of 10-21T09:42Z:** 222 requests, its Startup.jobs remote walk capped at 80 pages and 4,000 postings, as the brief says.
- **What a capped walk records:** `pages`, `capped: true`, `stopped_by: cap` and a warning (`src/run.py:1023-1042`).
- **What the next run reads:** down to the mark, the newest posting stored (`:1004-1006`, `:1061-1068`).
- **Lost, not late:** F1.

### Item 7: contract checks

- **Each platform has its own client, budget, breaker and exception boundary** (`src/contract.py:310-383`).
- **The workflow matches `CLAUDE.md`** (`contract.yml:85-124`): exit 1 pushes nothing and fails; exit 2 pushes, then a last step fails the run.
- **42 contract logs on `data`:** 326 unchanged, 14 baselines, 1 changed, 4 re-baselined, and 16 "no board configured" (Hasjob).
- **All 15 platforms are checked**; Hacker News' thread takes its follow step.
- **The fingerprint and the logs carry field names and statuses only.** F21 below is the one way a URL could reach them.

### Item 8: `Who reads`

- **The label is one of five**, chosen by the order in `src/description.py:287`.
- **Its roles come from `config/who_reads.json`.** No posting word reaches the row: the row keeps the label alone (`src/normalise.py:273`).
- **The order lets an agency's founder or engineer outrank the agency** (F7).

### Item 9: the November 1 switches

- **Both were off before `285d228`** [C]:
  - at `28bfaad`, `description_fields_shown` was false and Senior, `senior` and `sr` were in the lists;
  - the nine production runs of 11-01T04:42Z to 11-05T05:26Z all name `0a6e5f5`.
- **`285d228` does what the records say and nothing else** [C].
  - It changes the two configuration files, the seniority list, two tests and `STATE.md`.
  - Against `62faca8`, still an unreachable object in the working copy and read there read-only, it differs in exactly five lines, each re-dating 2026-11-01 to 2026-11-05, apart from `STATE.md`, which `62faca8` did not touch.
- **The rehearsal of 10-21T21:46Z on `62faca8`:** 14 projection and 7 sweep calls, 21, as `STATE.md` says.
- **The first production run on it, 11-05T20:33Z:**
  - re-read every saved posting;
  - backfilled 229 rows (227 private, 2 public) and sent 289;
  - spent 32 calls, taking November from 57 to 89 of 900.
  - D3 now counts 648 of 1,000 records, with `Jobs` at 499. The warning comes at 850.

### Item 10: dateless sources

- **Never dropped for age** [C]: `rule_age` takes `ordering_date`, which is first sight for a dateless posting, so the age is 0 (`src/filters.py:707-713`).
- **Sent with an empty `Order date`** (`src/projection.py:212`).
- **Not checked:** whether the `To review` view sorts empty dates last needs a call.
- **Measure A's exclusion of them** is stated in ADR-0015, ADR-0063, `CAPABILITIES.md` and `STATE.md`, but not in the version's own test for done (F19).

### Item 11: Hacker News

- **The thread chosen:** the newest of the `whoishiring` account's stories titled `^ask hn: who is hiring?` (`src/adapters/hackernews.py:56`, `:83-91`). "Who wants to be hired?" and the freelancer threads are excluded.
- **The first line** ends at the first `<p>`, `<br>` or newline (`:69`, `:95-98`), so a header that runs past a line break loses its second line, and with it any place written there [I].
- **The job stories:** F6.

### Item 12: tests that cannot fail

- **Both suites pass**, 1,080 tests each [C], `out/suite-312.txt` and `out/suite-311.txt` in the scratchpad.
- **351 of 351 caught** [C], `out/mutations.txt`: 342 by the tests tried first, 9 by the whole suite, each by at least one named failing test.
- **All 231 target lists pass when run alone with no mutation** [C], `out/targets-unmutated.txt`.
- **The Confirmation registry**, `tests/confirmations.py`:
  - every record from 0050 on has an entry;
  - 83 clauses are held by tests, 6 are live-only and 1 is unbuilt (0056's, superseded);
  - every named test exists [C];
  - `tests/test_fitness.py` checks it against the records, and the registry's own mutations were caught.
- **The harness itself:** F8.

### Item 13: the records against the code

- **Checked:**
  - ADR-0028's 400 against `src/http_client.py:57`;
  - ADR-0034's narrowing against its test (F9);
  - ADR-0053's agreement condition against the live counts (F3);
  - ADR-0062's ceiling against the code (F12);
  - ADR-0017 against ADR-0020 (F2);
  - every `STATE.md` stamp against its commit: 71 stamps in the 73 commits that touched it, none later than its commit [C];
  - `CAPABILITIES.md`'s countable numbers (F10).
- **Not checked line by line:** every Changes row of the 36 record files the range touched (section 5).

### Items 14 to 16

- **Exit codes** [C]:
  - 1 for a start-up failure (`src/run.py:1449`, `:1461`, `:1496`) and for a failed commit (`:1612`), whose messages say which;
  - 2 for a private-store, projection, sweep or clearing failure (`:1636`), or a stopped fetch (`:1217`);
  - the ceiling and D2 exit 2 through the projection's failure;
  - `needs_attention` counts projection, private-store and sweep failures, three in a row escalating and a private-store failure at once (`:142-187`);
  - the message "raised before anything was committed" is true: the guarded block holds only the local fetch (`:1486-1496`), and the private store's first push comes after it;
  - a failed Health write never raises and changes no exit code, by design (`:466-495`).
- **The budget** [C]:
  - every attempt is charged before it is sent (`src/resilience.py:235`), so retries count;
  - the month is summed from both branches' logs over `airtable`, `sweep`, `clearing` and `health` (`src/airtable.py:214-228`);
  - October came to 673 pipeline calls, 596 production and 77 test;
  - the test run of 10-21T09:42Z began at 501 and spent 13, as the brief says.
- **D2** [C]: the type is compared whole, from the JSON `error.type` or a string `error`, only on a 429 (`src/airtable.py:145-185`). A message naming the code, a type containing it, or the code on a 422 cannot trigger it. The run exits 2 with the fetch stored (`tests/test_run.py:1834-1873`).
- **D3:** F13.
- **C1:** live, stored before every removal (item 2).
- **`AIRTABLE-MCP.md`:**
  - no Airtable ID;
  - "A chat writes only the operator's fields", with the table of them;
  - its limits sourced to Airtable's support and developer pages, read 2026-10-28.

  Two stale figures are F11.

## 3. Findings, most severe first

No finding reaches "data lost or corrupted" in the sense of a store or a row the pipeline held being lost or changed. F1 is the nearest: postings the pipeline should have read and never did. Probes are in the scratchpad's `agents/lead/`.

### F1. Defect: a capped walk loses its unread tail for good (`src/run.py:1004-1023`, `:1061-1068`)

**The claim.** A walk that reaches `MAX_PAGES`, 80 (`src/run.py:111`), before its mark or its age floor reads the newest postings and leaves the rest of the window unread. The next walk's mark is the newest publication date among postings saved in full, so any walk that stops at the mark never reaches the unread tail. A deep morning walk reaches it only when it is no longer capped. By then a posting first seen more than seven days after publication is dropped by D14, judged once, at first sight. So what the cap leaves is lost, not late, which is not what ADR-0007 means by recency.

**The evidence** [C], from the private seen store and the run logs:
```
startupjobs:sj-workplace-remote  first seen on the walk of 10-21T17:57Z: 4000 | published from 2026-10-15T04:53 to 2026-10-20T17:54
   first seen after 10-22: 9397 | of them published before the first walk's oldest: 0
data 20261021T175743 startupjobs:sj-workplace-remote pages 80 capped True stopped_by cap fetched 4000 new 4000
```
- **The size of the loss:** the walk's age floor was about 10-14T17:57Z, so about the window's oldest eleven hours were never read. At the board's measured keep rate, 44 of 8,225, that is perhaps 1 to 3 kept postings [I].
- **It was foreseeable.** `STATE.md`'s line of 2026-10-20 predicted "a walk of about 82 pages" against a cap of 80.
- **The session log saw the cap and not the loss.** `logs/2026-10-21-brief-19-...md:62` records "its first walk at the 80-page cap" under "no failure".
- **Himalayas since 11-01:** the evening walk of 11-01 and every morning walk since are capped at 80 pages. A late-arriving posting dated in the window's oldest days that sits below page 80 meets the same end. The cap since 11-02 is known and routed; that it can lose, not only delay, is this finding.

**Why it matters.** D13: "i do not want to miss any to which i am eligible to". The fix is the seat's to choose: a capped walk could leave the mark where it was, so the next walk reads on into the tail.

### F2. Defect, and two records in conflict: aggregator postings are committed on `main` (`tests/cassettes/`)

**The claim.** Ten cassettes from nine aggregator platforms are committed on `main`, each a real response with its descriptions stripped and its postings' titles, employers and URLs kept:
- `himalayas-browse`;
- `hackernews-whoishiring` and `-stories`;
- `hnjobs-job`;
- `hasjob-feed`;
- `jobicy-remote`;
- `pythonorg-feed`;
- `remoteok-feed`;
- `startupjobs-remote`;
- `weworkremotely-feed`.

`himalayas-browse` arrived in `387ac8c` on 2026-09-17. The other nine arrived in the range, 2026-10-19 to 10-21.

**The evidence** [C], `agents/lead/leakscan.py` over `015bead..b811455`, cassettes only:
```
URL from the private set           229
aggregator host named              312
```
Per cassette, against the private seen and filtered stores [C]: stored titles appear in eight of the ten, and stored employers as values in three.

**Against the records:**
- ADR-0020:61: "No aggregator content reaches the public repository".
- ADR-0020:21: "Committing a fetched dataset to a public repository is a harder case, and the operator does not want to test it".
- ADR-0047:31: "Anything committed to a public repository survives deletion".
- ADR-0017:46 says to record "one real response per platform" with only descriptions stripped. It predates the aggregators and makes no exception for them.

Two accepted records conflict here, which is a defect to raise, not to resolve.

**No gate stands in the way.** The hook's gate 6 covers staged `data/` paths only (`.githooks/pre-commit:200-230`). The cassette gate checks only that descriptions are stripped. ADR-0020:57 promised "a guard rejecting an aggregator-sourced file from a commit".

**A source's terms bear on it.** Startup.jobs' API terms, as `docs/research/0006-founder-read-sources.md:25` records them, require fetched content "refreshed or deleted within seven days", and copies destroyed on termination [O, as recorded there].

**Not caught before.** The fourth audit's privacy check read the data branches only.

### F3. Defect: twelve agreement-check disagreements went unread (`src/run.py:986`, `src/health.py`)

**The claim.** ADR-0053:58 allows the Pakistan search to stand in for the location rule only while "every posting on it that the search endpoint would exclude must be a posting ADR-0041 would also exclude". That condition failed twelve times. Each was printed as a workflow warning (`src/run.py:986`). `src/health.py` has no case for it, so none reached the `Health` table he reads.

**The evidence** [C]:
```
20261021T033406 disagreements 1 | 20261024T033232 5 | 20261027T183624 1 | 20261029T044016 2
20261030T044005 1 | 20261101T044239 1 | 20261102T221347 1        (12 in all, from the run logs)
private disagreements file: 12 records | of them in the private seen store: 0 | in the filtered layer: 0
```
- Run through the title pool and the seniority words, 2 of the 12 pass the pool and 1 passes both, on folded titles [I, the full normaliser not run].
- `STATE.md`'s lines of 10-28 and 11-05 call every run of the period clean: "every production run since 2026-10-22, 13, clean"; "fifteen production runs, every one clean".

**Why it matters.** The check is ADR-0053's only stand-in for ADR-0005's observability, and its findings reach no one who acts on them.

### F4. Defect: a cleared classification is stored as unreviewed, its copy orphaned (`src/sweep.py:437-442`, `:579-600`, `:676-722`)

**The claim.** A rejected row whose `Status` is cleared is "no new classification" (D12), so its copy is kept: correct. But the row is now unclassified:
1. Steps 4 to 7 store it as `unreviewed-aged-out` once it is 21 days past first sight, and delete it.
2. Step 3 never deletes the copy, because its outcome is not in the rejection store.
3. Step 2 never stores that outcome, because no `Jobs` row holds the status any more.
4. After that morning no reason reads the rejection tables, so not even the problem line recurs.

**The evidence** [C], `agents/lead/probe_orphan.py`, on the in-memory base with C1's 21 days. A row first seen 25 days ago, rejected 20 days ago with a copy, its status then cleared:
```
morning 0: read=True for=['a status moved since the last copy step'] kept_after_a_clear=1 aged_out=1 deleted=0 problems=['the rejected-not-a-fit copy of greenhouse:2 is past 15 days but its outcome is not in the store; kept']
morning 1: read=False for=[] kept_after_a_clear=0 aged_out=0 deleted=1 problems=[]
morning 2: read=False for=[] kept_after_a_clear=0 aged_out=0 deleted=0 problems=[]
morning 3: read=False for=[] kept_after_a_clear=0 aged_out=0 deleted=0 problems=[]
Jobs rows left: 0
rejected-not-a-fit copies left: ['salary']
rejected_not_a_fit store: []
removed_unreviewed store: [('greenhouse:2', 'unreviewed-aged-out')]
```
Morning 3 is thirty days on.

**Exposure.** No data is lost: the copy stays in Airtable with his reason. But the stores say he never reviewed a posting he rejected, and the copy holds a record of the base's 1,000 for good. Two production rows sat in this state from 10-15 to 10-27, before C1 made it fast, and left it by being re-classified, not by the clock [I].

### F5. Defect (latent): the facts fingerprint misses the filter module's place reading (`src/facts.py:53-54`)

**The claim.** `required_places`, a stored fact the authorisation rule judges, comes from `src/filters.py`'s `place_names`, `_qualifiers_removed` and `_NEGATIONS`, through `src/normalise.py:279-292`. `src/filters.py` is not in `SOURCES`. A change there alters the fact for new postings while every stored row keeps the old one.

**The evidence** [C], `agents/lead/probe_fingerprint.py`. `src/filters.py` was changed in a copy of the tree so that qualifiers are not removed, and the requirement "must be located in a us time zone" read in each tree:
```
before fingerprint 3709f937dcda9241 | required_places None
after fingerprint 3709f937dcda9241 | required_places ['us']
```

**Exposure today: none** [C]. Every one of the six range commits that touched `src/filters.py` also changed a fingerprinted file, at least `config/eligibility.json`, so each forced a re-read.

### F6. Defect (latent): Hacker News' job stories never have their place read (`src/adapters/hnjobs.py`)

**The claim.** The brief left this as an open question. Job stories carry no location field and the header rule never runs on them, so a title naming a place closed to the operator keeps its posting.

**The evidence** [C], under `b811455`'s rules with age held aside:
```
hnjobs raw rows: 109 | kept at any age on b811455 rules: 13 | drops: 96
13 kept, by the places their titles name: {'none named': 11, 'closed': 2}
closed-in-title kept at any age: 2 | of them stored in the filtered layer: 0
```
The brief's 13 reproduces. Two of them name a place the configuration lists as closed. Neither reached the store, since both failed the age rule at first sight. Whether each title states a restriction needs reading the titles, which this report cannot quote.

### F7. Defect (latent): an agency's founder reads as a founder (`src/description.py:287`, `:377-414`)

**The claim.** The first label in the order wins. An agency's founder, chief executive or engineer writing in the first person on behalf of a client is labelled `founder` or `engineer`, the labels the operator uses to find a posting a founder or an engineer reads. This is the brief's own question: "Does a recruiter's posting read as a founder's?"

**The evidence** [C], constructed strings, none a posting's:
```
founder   ['agency', 'founder']    I'm the founder of Brightpath Talent, a recruitment agency. On behalf of our client, ...
founder   ['agency', 'founder']    I am the CEO of a staffing firm. Our client is a Series A startup ...
engineer  ['agency', 'engineer']   I'm a senior engineer at Acme Recruiting. We place engineers with our client, ...
founder   ['founder', 'recruiter'] I'm the CTO. Our recruiter will review applications first.   (correct, by design)
```
The comment at `:283` says an agency writing for a client "stands between him and the employer, whoever else it names", which the order does not do when the writer is the agency's own founder or engineer.

**How often: never yet** [C], `agents/lead/whoreads_measure.py`. It runs the production re-read over every file on the private full branch, with `who_reads` wrapped to record every label each description gives grounds for:
```
descriptions read: 27510 (re-read count 27622), files 76
labels as shown: {None: 26118, 'recruiter': 688, 'agency': 181, 'engineer': 14, 'founder': 44, 'a named person': 465}
shown as founder: 44; of them the description also gives grounds for agency 0, recruiter 17
shown as engineer: 14; of them the description also gives grounds for agency 0, recruiter 5
```
- So the misreading is latent.
- The 17 and 5 that also name a recruiter are resolved to the writer by design: "a founder writing that a recruiter screens first is still a founder's posting".

### F8. Defect (latent): the targeted harness can call a crash a catch (`tools/mutate.py:270-288`)

**The claim.**
- `apply_one` decides a mutation caught when the targeted run "did not pass and did not time out". Any non-zero exit counts: a named test that fails when run alone, a name unittest cannot load, or a module that ran no tests, which exits 5 on 3.12.
- The target lists are never run without the mutation first.
- `--why` would then print no failing test, but the line still reads "caught".
- The other half of the brief's question holds: a survivor is always decided on the whole suite.

**Exposure at `b811455`: none** [C]. All 231 target lists pass alone unmutated, and every one of the 351 catches named at least one failing test:
```
mutations 351 | caught with no failing test named: 0
decided by the whole suite: 9 | by the tests tried first: 342
DONE: 0 target lists fail when run alone without a mutation
```

### F9. Defect (test gap): the narrowed no-token guard misses one import form (`tests/test_airtable.py:590-597`)

**The claim.** The guard's patterns flag `from src.airtable import AirtableClient` only because "import airtable" matches "import AirtableClient" case-insensitively. They do not flag `import src.airtable`, nor a write verb sent through `request(method, url)` with the method in a variable. The narrowing of 2026-10-20 forbids "an import of the Airtable client".

**The evidence** [C]: the guard's own `write_signs` on each string:
```
flag  imports the Airtable client, absolute            from src.airtable import AirtableClient
PASS  imports the Airtable client, absolute module     import src.airtable
PASS  write verb, method in a variable                 self._session.request(method, url)
```
Run as a mutation [C], `tools/mutate.py --targeted --why` in a scratch clone at `b811455`, adding `import src.airtable  # noqa: F401` after `import requests` in `src/http_client.py`:
```
  SURVIVED  audit5: the fetch module imports the Airtable client by its absolute module name
              591 s, by the whole suite
```

**No harm today:** `src/http_client.py` imports only `os`, `time`, `requests` and `.resilience`.

### F10. Stale document: `CAPABILITIES.md`'s numbers lag the tree

`CLAUDE.md` asks for each number to be re-measured at the close of any session that changes it. Measured at `b811455` [C]:

| Line | It says | Measured |
|---|---|---|
| 242, dated 2026-10-20 | 665 mutations across 68 files | 705 across 76; five files added since, and the 11-05 session updated the tests line beside it |
| 243, dated 2026-10-17 | 61 records, eight superseded | 62 numbered records plus ADR-RULES, nine superseded; ADR-0042 reserved |
| 244, dated 2026-10-19 | 212 commits, 32 session logs | 246 commits, 37 session logs |
| 427, undated | 893 tests, 533 mutations | 1,080 and 705 |
| 429, undated | 55 decision records and 24 session logs | as above |
| 425, undated | 30 production runs over 13.6 days, 803 to 1,420 a run | the figures of 2026-10-01, presented as current |

### F11. Stale document: October's calls counted two ways (`STATE.md:11`, `AIRTABLE-MCP.md:13`)

- `STATE.md`'s line of 11-05 says "the pipeline's calls 596 in October".
- `AIRTABLE-MCP.md` says "in October it spent 635 of them (measured from its run logs, test runs included)".

Summed from both branches' logs over the four counted blocks [C]:
```
2026-10 data 596 {'airtable': 315, 'sweep': 273, 'clearing': 0, 'health': 8}
2026-10 datatest 77 {'airtable': 39, 'sweep': 32, 'clearing': 6, 'health': 0}
```
- October came to 673.
- 596 leaves out the test runs, which the ceiling counts.
- 635 was the month to 10-28.
- `AIRTABLE-MCP.md:13` cites its November estimate to `briefs/architecture.md`, a gitignored file no reader of the repository can open.

### F12. Wrong document, off by one: the ceiling refuses the 901st call, not the 900th (ADR-0062:110, `config/sweep.json:23`)

Both say the pipeline "refuses any Airtable call that would take its own month's count to 900". The code refuses only once 900 are spent (`src/airtable.py:359`, `src/airtable_sweep.py:203`). The evidence [C], a `SweepClient` on the fake base:
```
used before 899, one call made: month now 900
second call refused: monthly Airtable call budget of 900 is exhausted, 900 used
```
The code's reading is deliberate and tested. Changing `>=` to `>` in `src/airtable.py` is caught [C]:
```
  caught    audit5: the ceiling refuses only past the ceiling, not at it
              by test_the_month_ceiling_refuses_without_sending (tests.test_airtable.TestMonthlyBudget...)
```
So the wording in the record and the configuration note is off by one call, not the code.

### F13. Defect (small): D3's count leaves out the other mode's tables without naming them (`src/run.py:734-790`)

- The docstring says a table "never yet read is named in `unknown`". When the other mode has never counted, its tables add 0 and are not named: `unknown` lists only this mode's tables (`:777-779`).
- Every production log since D3 carries `other_mode: null` with `unknown: []`, because no test run has happened since 10-28 [C].
- The test tables hold few records now: about 5 copies made in test mode, 3 deleted, and `Jobs test` emptied on 10-28 by `STATE.md` [I].
- A test run would correct it. Until one does, the warning at 850 compares a count that omits them.

### F14. Wrong document: D2's "every later call that run is refused without a request" (`STATE.md:19`)

`allowance_spent` is per client and `src/run.py` never shares it. After the workspace's month is spent, a run still sends one request from each later client: the projection's reader, the sweep, `Health`, and the clearing tool when asked. Each is answered 429 and stops at once. The test's own docstring is right, "each client stops at its first answer", and asserts at most two calls between its two clients (`tests/test_run.py:1834-1873`). The brief repeats `STATE.md`'s wording.

### F15. Nit: `STATE.md`'s formatting

- Three lines read "15:29Zby", "15:19Zby" and, before `285d228` fixed it, "21:33Zby". `285d228` fixed one and introduced another.
- `STATE.md:11` says the switch branches are not yet deleted. That is known and routed; their objects survive unreachable in the working copy, which is how item 9 was checked.

### F16. Stale document: `STATE.md` C1's "At once it takes about 3 rows" (`STATE.md:15`)

Marked inferred when written. The first C1 morning, 10-30, took 0. The clock's first removals were 1 on 11-04 and 5 on 11-05 [C].

### F17. Stale document: `docs/reference/retention.md:169-170`

It says the sweep reads `unreviewed_after_days` as 30. It is 21 since C1, which the same file's table at line 26 says. C1's `STATE.md` line says the file was annotated; this line was missed.

### F18. Nit, the fourth audit's F19 again: two DONE rows in `STATE.md`

"End-state document" (`STATE.md:257`) and "The writer's constraints assembled in one place" (`:272`) read DONE, against the file's own rule that a DONE row moves to `docs/reference/completed.md` in the same commit.

### F19. Nit: the version's test for done does not say dateless postings are outside Measure A (`docs/versions/v1.0.0.md:58`)

ADR-0015 and ADR-0063 state it once each, and `CAPABILITIES.md` and `STATE.md` twice each. The line that states the test for done states Measure A without it.

### F20. Nit, the fourth audit's F20 again: the data branches enter this repository's refs on every fetch

- There is no local `data` branch now.
- The working copy's remote still fetches with git's default refspec, `+refs/heads/*:refs/remotes/origin/*`. So `refs/remotes/origin/data` and `refs/remotes/origin/data-test` exist and are refreshed by every plain `git fetch`: the reflog shows fetches from 2026-09-26 to 2026-11-05.
- `docs/how-to/the-seats.md` says "Never fetch the `data` branch into this repository's refs".
- The implementing seat's own practice is to fetch before every commit.
- Either the refspec narrows to `main`, or the rule says what it means.

### F21. Nit (latent): two public logs can carry an exception's or a URL's text

- The contract check writes an HTTP error's text, which names its URL, into an `unreachable` detail (`src/contract.py:351-360`). A failed follow request would publish Hacker News' thread URL in the public contract log.
- The fetch run keeps an unexpected exception's message in a board's detail on the public run log (`src/run.py:887-900`), where the contract check keeps only the class and location.
- The aggregator adapters' own errors quote only a board ID and a type name.
- No aggregator board has ever failed. The only failures on either branch are Manatal's five 403s and Workable's six boards not reached on 10-14 [C].

### F22. Nit: the brief

- **A stamp ahead of the clock.** It was "brought up to date 2026-11-05 at about 16:30Z". It was first read at 16:14Z, and `b811455` was committed at 15:35:20Z.
- **The wrong reason for forbidding a local run.** It says a local `python -m src.run` "would project to the Airtable test tables, spending calls". With `--no-commit`, the form `CLAUDE.md` and the seats file give, a run "reaches no base and no private store" (`src/run.py:403-415`, `:473`, `:558`, `:600`). Its other reason stands: `.env` is loaded at `src/run.py:1426`, not `:1339`, so the run would poll Startup.jobs on his key.
- **A line reference one off.** `MAX_PAGES` is at `src/run.py:111`, not `:110`.
- **Two commits for one run.** Item 1 says to run the mutation files at `0a6e5f5`, and item 12 at `b811455`; this audit used `b811455`.
- **The report's name.** It is given as `2026-10-DD-...`; the audit ran on 11-05.
- **Stale since written:** "Jobs: the clock has removed nothing so far" (item 2).

## 4. What was checked and found correct

The verdicts in section 2 carry most of it. Beyond them [C]:
- **Every scheduled run since the fourth audit.** 72 production runs and 36 contract checks on `data` since 09-30T18:00Z, every commit by the pipeline's own identity, every message `run <time>` or `contract check <time>`.
- **The first switch run's facts block.** Its fingerprint, `3709f937dcda9241`, equals the one the audit computed from `b811455`'s tree.
- **The sweep's one read of `Jobs` since `cb4dc12`.** Every production sweep since names "the projection" as its read.
- **The private store on every run since 10-17.** No failure in its block on any run.
- **`last_copy_step_at`** (`src/run.py:524-538`) takes the start of the last run whose sweep read every table without failing. A status set while that run was going is caught by the next, the safe side.
- **No cassette holds `Bearer`, `Authorization` or an API key**, and no adapter imports from outside `src/adapters/`.
- **`MAP.md` is current.** `tools/generate_map.py --check` exits 0, and the hook has its six gates.
- **The seats file's checkable rows hold.** Its row on the code's size, "42 Python files and 8,642 lines", is dated 2026-09-22 and was not re-measured.
- **`--targeted`'s survivor half.** A survivor is always decided on the whole suite (`tools/mutate.py:270-288`).

## 5. What was not checked, and why

- **Anything needing an Airtable call:**
  - which two copies were "past 15 days" on 11-01 and 11-02 (3 calls);
  - the `To review` view's sort of empty dates (1);
  - the Airtable descriptions of the fourth audit's F11 (1);
  - the test tables' record counts for F13 (4).
- **A local run of `src.run` or `src.contract`:** not without his go.
- **Every Changes row of the 36 record files the range touched**, line by line. ADR-0017, 0020, 0028, 0034, 0047, 0053, 0055 and 0062 were read where the findings needed them. `CHAT_STATE.md` was read only for the seats section.
- **The session logs of the range, claim by claim.** Read where a finding touched them: the logs of 10-01, 10-20, 10-21 and 11-05.
- **`docs/reference/platform-fields.md` and `airtable-schema.md`, field by field.**
- **Which Startup.jobs postings F1 lost.** They were never fetched, so nothing holds them.
- **Measure A's 121 rows over 11-01 to 11-05**, as `STATE.md` gives them.

## 6. Subagent claims not re-checked

**None is relied on.**
- Sixteen read-only reviewers were started at 16:30Z through a workflow.
- Each stopped at the operator's five-hour usage limit between 16:50Z and 16:57Z, before returning anything.
- Their transcripts held four leads, each re-checked here before use: the six 21-day removals stored first (item 2); the problem lines of 11-01 and 11-02 (item 2); the contract check's `unreachable` detail (F21); and the test tree's shape, which the 231 target lists confirmed.
- None asked Airtable anything; their transcripts show no connector call.
