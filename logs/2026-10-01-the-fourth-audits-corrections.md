---
type: log
description: The fourth audit's twenty-one findings, each checked and acted on. A confirmed clear removes only what its dry run listed; the agreement check judges each browse posting on a later walk; the location rule keeps the places the operator can take; the contract re-baseline excuses nothing on an undated shape; the suite now fails when a mutation goes stale; three untested guarantees tested; the documents and the Airtable descriptions corrected.
status: current
---

# The fourth audit's corrections, 2026-10-01 UTC

Previous log: `2026-09-30-brief-8-the-displays-clock-and-four-checks.md`. The audit: `logs/audit/2026-09-30-fourth-audit.md`.

| Header | Value |
|---|---|
| Date | 2026-10-01 UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `1418042`; `8857d0b` made and pushed at 11:20Z in this session |
| Mode | **Mutating.** Airtable: 10 connector calls, six of them description writes. GitHub's public API: 3 reads. `data` read from a scratch clone, never fetched into this repository. The private repository not read |
| Tests | 702 at start, 723 at end |
| Verification | See "Verification", at the end |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What the operator asked

He relayed the audit chat's completion message and asked for the report read end to end, the findings corrected, and then "a proper report on what the issues were and how were they resolved ... it should be me who should check how sound was your logic", with questions where the decision is his.

## The report, kept

Read end to end and checked for what the public branch must not carry: no Himalayas identity, title, URL or employer, no token, no Airtable ID, no wikilink. Its F3 evidence was already restated as durations by the audit seat. Committed unchanged in `8857d0b`, with its index row.

## Each finding

### F1. A confirmed clear removed rows its dry run never listed

**Checked** `[VERIFIED]`: `dry_run_on_file` compared the table and the days and nothing else, and the confirm selected afresh at its own clock. The audit's probe E reproduced as a test before the fix: a row 29 days old at the dry run and 31 at the confirm was removed.

**Done.** The confirm acts on the rows both selections hold: past the threshold now, and listed by the dry run it follows, the latest on file. A row that crossed the threshold since is left and counted as `not_in_the_dry_run`. Public rows are bound by the identities in the dry run's run log. An aggregator row is masked there, so the dry run writes it, with its title, employer and dates, to `outcomes/clearing_dry_runs.json` in the private store, keyed by the dry run's `run_at`; the confirm reads that file. Without the private store at the dry run the aggregator rows are counted as not listed, and a confirm leaves them.

**Why this design.** `operator-removed` never returns, so the safe direction is to leave anything not shown: a row left costs him one more dry run, a row removed unseen is lost to the display for good. Binding by identity rather than by a date cutoff, because a row first seen after the dry run can carry an old date (a Lever row, or one a widened rule backfills) and a cutoff would remove it unseen.

**Flagged for the chat.** ADR-0055's Confirmation says a dry run is proved by "the absence of any store write". The new file is no store in that record's sense: neither the skip nor the sweep reads it, and a test proves the skip reads nothing from it. If the chat reads "store" as any file, the alternative is a separate private folder; the behaviour would not change.

### F2. Four guards of the clearing tool had no test

**Checked** `[VERIFIED]`: each guard was present and correct in the code, and no test failed without it.

**Done.** The confirmation test, ADR-0055's fitness function, now also refuses a failed dry run, a confirmed run, a dry run with no list, and a dry run of the other mode in both directions. `Clearing` takes the mode and refuses a log of the other one. A run-level test drives `clear_display` in test mode and asserts that the client, the logs read, and the tool all get the test mode. Mutations: "a failed dry run validates a confirm", "a confirmed run counts as the dry run", "a test-mode confirm accepts a production dry run", "the clearing tool in test mode reaches production", "a test-mode confirm reads production's logs", "the tool is told it is production", "a dry run with no list validates a confirm", "the earliest dry run on file is bound".

### F3. The agreement check compared nothing live

**Checked** `[VERIFIED]` against the code: only browse postings no newer than the search's newest were compared. Browse's first page covers about twenty minutes; the search trails it by hours, so on the audit's live sample none qualified. The audit's 0 of 20 is consistent with that `[INFERRED]`: I made no live request.

**Done.** Every posting on the page is compared, now or later:
- returned by the search, now or on any earlier walk: agrees;
- one the location rule would drop: agrees, whatever the search does;
- one the rule would admit and the search has not returned: waits, privately, in `outcomes/agreement_pending.json`.

A later walk settles each waiting posting. Returned, it agrees. Still absent after `AGREEMENT_WAIT_HOURS` (12), on a walk that read back past its publication date, it is a disagreement: counted publicly, named privately, and warned. The search board is walked on mornings only, so in practice the next morning decides.

**Why.** ADR-0053 checks the pushed-down filter only "while its agreement with that rule is checked", and line 58 compares "every posting on it". Waiting keeps both: nothing on the page is skipped, and a posting the search has not yet taken in is not counted as excluded. The walk-reached condition stops a short walk from declaring a posting absent from pages it never read. The 12 hours is a constant with its basis in a comment, not a measured lag: the audit's one sample put the search 6.3 hours behind.

**Not yet seen live.** The next morning's run is the first. Its line reads "of 20 browse postings, n returned by the search, n the location rule excludes too, n newly waiting".

### F4. `rule_location` dropped places the operator can take

**Checked** `[VERIFIED]`: all seven of the audit's strings were dropped by the rule as built, and "Remote - EST hours" kept.

**Done.** `classify_place` now reads, in this order:
1. time zones, preferences and an optional office are removed first, since "time zone is not an issue";
2. "except" and its kind make a part unclear, kept;
3. a home place admits, unless it is on site in a named home city other than Karachi with no remote option, so "Pakistan (On-site)" (no city) and "Remote/Hybrid - Lahore" (remote offered) are kept;
4. a closed place beside "only" is closed;
5. worldwide, or a region that can include Pakistan, admits even beside closed countries, so "US, Canada, Asia" is kept;
6. a closed place is closed, so "Remote, Germany" is Germany's remote;
7. remote with nothing closed beside it admits;
8. anything else is unclear, kept.

"Anywhere in the US" scopes the open word to the US, so it stays closed. `remote` is split out of `open` in `config/eligibility.json`, and `home_country` names which home place is the country.

**Proved not to over-correct** `[VERIFIED]`: the old and new code compared on every location this machine holds. No verdict changed across 413 distinct public locations (59 kept, 354 dropped), 118 Himalayas locations (15, 103) and the 146-entry corpus (25, 121). "Global (US only)", "Remote (Anywhere in the US)", "Remote, Germany", "Hybrid - Lahore" and "Canada - remote, Eastern time zones" stay dropped, each a test.

**Also done.** A drop's reason names the field and the home country, quoted from the configuration: "the location field names only places closed to the operator, none of them pakistan or a remote role open to it". ADR-0041's Confirmation asks for the field and what was absent, and ADR-0031 forbids a module naming a preference; quoting the configuration satisfies both. The Brief 8 report called these two records in conflict. The audit read it as not forced, and the code now follows that reading. For the chat to confirm.

### F5. The re-baseline could excuse a later change

**Checked** `[VERIFIED]`: the fingerprint on `data` carries no `since`, and the code read a missing date as older than every entry.

**Done in `8857d0b`, pushed 11:20Z, before the day's contract check**, whose last five runs started at 11:42Z to 14:21Z `[VERIFIED]` (Actions API). An undated shape is never excused and gains its date on the check that reads it. An entry dated after today excuses nothing. A date must parse as a calendar date. The 10-01 check had not run when this log was written, so the window was never open on the new code.

**My error in that commit.** A line of `real_date` reached the file with its backslash continuation collapsed into spaces: valid Python, malformed text. Rewritten without a continuation here. The same commit left two of Brief 8's mutations stale, the defect F6 names; see F6.

### F6. Stale mutations, and nothing to notice them

**Checked** `[VERIFIED]` with a script counting every find in the working tree: the audit's 8, and 10 of this session's own. 2 were committed in `8857d0b` (F5). The other 8 were caught in the working tree before any commit: 2 each by the edits for F4, F1, F3 and F13, the last pair by the new test below.

**Done.**
- All 18 re-expressed in place, as `6ef16eb` did for the files of 09-17 and 09-18. Each keeps its label and its guarantee, against the code as it now reads. Two more were changed for meaning, not staleness, below; 20 entries in all.
- The audit's equivalent survivor, "the skip reads the fourth store", is replaced by "the skip ignores the accepted store". Brief 8 reversed the rule it guarded, so it read the same file twice to the same effect.
- Brief 8's "the agreement check compares postings newer than the search" guarded the cut F3 removes. It is relabelled "a posting the search has not returned is judged on the walk that found it" and guards the wait that replaced the cut.
- **The suite now fails on a stale find.** `tools/mutate.py` exposes `problems_in`, and a test runs it over every file on record. While the harness applies a mutation it names the file in `MUTATION_APPLIED`, and only that file's finds are exempt, since otherwise every mutation would be "caught" by this test alone. The test proves it can fail: a find matching nothing, a find matching twice, the exemption honoured.

**Why the suite and not the hook.** The suite runs on every workflow run and every machine; the hook only where it is enabled.

### F7. Three guarantees with no test

All three `[VERIFIED]` correct in the code and untested.
- **The clock measures first sight.** A row published 34 days ago and first seen 28 days ago stays. Mutation: "the clock measures the publication date".
- **The run passes the private removal store to the skip.** A run-level test keeps a Himalayas row out for each of `closed`, `unreviewed-aged-out` and `operator-removed`, and sends it once the record is removed, so the case is shown to be built. Mutation: "the skip ignores the private removal store".
- **A tie in `swept_at` goes to the record written last.** Mutation: "a tie in swept_at goes to the first record written".

### F8. Four wrong numbers in `CAPABILITIES.md`

Each re-measured, not taken from the audit `[VERIFIED]`:
- start times, from the Actions API over the 29 scheduled runs to 2026-10-01: 03:26 to 04:33 and 16:18 to 20:02 UTC, 3.3 to 7.0 hours late, the longest gap 16.0 hours. The audit's 04:34 is the same run, rounded;
- postings read per run, over all 30 production runs: 803 to 1,420. The audit's 811 predates the run of 09-30T18:19Z, which read 803;
- freshness is first sight, now said so, with 8 of the 114 ever admitted, from the audit;
- the session logs, counted at the close.

Also re-measured: 30 runs over 13.6 days, 0 retries and 0 failures, median 36 requests and at most 41, 34,557 fetched, 1,018 distinct public postings stored. Found stale besides: "Contract check. Daily at 06:30 UTC" while GitHub started its last five at 11:42 to 14:21 UTC. Corrected.

### F9. The unsent Brief 8 report

Corrected in `briefs/architecture.md` before it goes, with a part 2 carrying this audit:
- item 7's "a spent entry cannot excuse a later change" was untrue until `8857d0b`;
- "a quiet evening's sweep 2" held only while `Jobs` passed 100 rows; the last two evenings spent 1 call each;
- "28 of 28" said nothing of the four older files it broke;
- the ADR-0041 and ADR-0031 conflict withdrawn as forced (F4);
- "as deep as page 19" stated as unsettled: refreshed publication dates are the likely cause, and only the private seen store can settle it.

### F10. Wrong records

The chat's, in part 2 of the brief: ADR-0050's start times and "nothing else removes a row"; ADR-0041's "keywords never reject" and its misquote; ADR-0043's "closed rows alone"; and the index's count of Changes rows, 123 against the 124 the audit and I count. No record was edited here.

### F11. The Airtable descriptions predated ADR-0055

**Done** `[VERIFIED]` through the connector, each read back:
- `Jobs`: the thirty-day clock, the tool, the binding, and that a hand deletion does not stick;
- the two rejection tables: early removal by the tool, outcome saved first;
- `accepted`: `Delete` set by him or by his tool;
- `Delete` on `accepted` and `accepted test`: the tool sets it for him.

The last three were beyond the audit's list and said the same stale thing.

### F12. `retention.md` contradicted itself

All four corrected:
- the clocks paragraph now names the first-seen clock;
- "nothing has run" now says what has run;
- the reason a status change "discards" now reads as D12 left it;
- "the sweep is unbuilt and loads them from here" now names `config/sweep.json`.

**Checked** `[VERIFIED]`, the deletions it now cites: 25 public rows on 09-28, 18 on location and 7 on age, in the public removal store. The 44 aggregator rows of 09-29 are labelled inferred, as the Brief 8 log has them.

### F13. Stale `README.md`, `CLAUDE.md`, workflow and configuration

- README's start times re-measured. Its clearing steps say what the output shows and that a confirm removes only what the dry run listed.
- **The fetch the seats file forbids.** README, three tool docstrings and three error messages told readers to run `git fetch origin data:data`. They now say to clone `data` apart from the repository and pass `--repo`. The three tests assert the clone advice and the absence of `git fetch`.
- The workflow's exit-2 comment and warning name the sweep and the clearing tool; its test asserts both.
- `run.py`'s docstring names both.
- `CLAUDE.md`'s exit-code paragraph names the tool. Its exit 2 was my choice in Brief 8's build and was never put to the operator, so the paragraph says exactly that. It is a question for him.
- `config/eligibility.json`'s age note now describes first sight, with Lever never dropped for age.

### F14. The secrets how-to names the private repository

**Checked** `[VERIFIED]`: line 164 names it, line 166 says the name is kept out. Not changed: whether to keep the name is the operator's. The audit's view, which I share: correcting the sentence is cheaper than removing the name, which has been public in history since `fe07242`.

### F15. A retired member hides a live one of its group

Left as it is, and explained. It needs two Lever postings sharing employer, normalised title and creation date, one retired before the other appears. That reaches only Lever, since D14 drops any other source's late arrival with an old date. Fixing it means skipping by member instead of by display row, which is ADR-0043's design and the chat's.

### F16. Clearing `Jobs` took rejection copies too, uncounted

**Done:** reported, behaviour unchanged. The dry run counts the classified rows by status, and the summary line says a rejection copy leaves with its row. The classification is saved either way, so nothing is lost. The question of whether it should leave is his, below.

### F17. Hitting the page cap was silent

**Done.** A walk that reaches 40 pages without its stop logs `capped: true` and prints a warning naming the board.

### F18. ADR-0052's widening clause had no test

**Done.** Now a fitness function. A posting ten days old at first sight is dropped at seven. With the number raised to fourteen in a copy of the configuration, the backfill admits it with its stored `first_seen`.

### F19. A DONE row in `STATE.md`, and a missing Changes row

- The sweep's row moved verbatim to `completed.md`. Its two open items now have their own PARTIAL row: the tool's first dispatch, the clock's first removal about 2026-10-17 `[INFERRED]`, and `accepted test` past fifteen days from 2026-10-08.
- The schema reference gained the Changes row its 09-30 annotation lacked.

### F20. A local `data` branch

**Checked** `[VERIFIED]`: the reflog prints "fetch origin +data:data" at 2026-09-28 21:18:42 +0500, which is 16:18:42Z, and the branch sits level with `origin/data`. No code here issues that refspec, and the workflow fetches by full ref names. This session's transcript has no tool call between 15:50 and 16:40Z that day. So it is not this seat's, and it is flagged, not deleted. A question for the operator.

### F21. The audit brief misquoted him

Acknowledged. The misquote is only in `briefs/audit.md`, which is gitignored. The next audit brief quotes the log: "i do not want a job post more than a week old".

## Verification

All `[VERIFIED]`, run on this commit's code. The clones' `src`, `tests`, `tools`, `config` and `.github` were compared with the tree and found identical.

- **Suite:** 723 tests pass on Python 3.12, and on 3.11.9 under `-W error::ResourceWarning`.
- **Mutations**, in three scratch clones run side by side, 12:04Z to 13:05Z, with `--why`:

  | File | Result |
  |---|---|
  | `2026-10-01-fourth-audit.json`, new | 32 of 32 |
  | `2026-09-30-brief-8.json`, whole, since its tests and seven of its finds changed | 28 of 28 |
  | The 13 re-expressed outside Brief 8's file, with the search and catch-up files whose walk F17 touched | 26 of 26 |

  Each was caught by the test built for it; where `--why` listed another first, the intended one was confirmed among the catchers. Every run restored its files and passed the suite again. No stray ref, and no Python process left afterwards.
- **Stale finds:** 0 of 386, by the new test and by a separate count.
- **Privacy:** the outgoing diff, this log and the new mutation file hold no Airtable base, table or field ID, no token, no `himalayas.app`, no Himalayas identity but the test fixtures on `x.test`, no wikilink, and not the private repository's name.
- **Not run:** the other 300 of the 386. Every find still matches. The tests this round rewrote rather than added to are the agreement and clearing tests, which Brief 8's file covers, and three assertions on the report tools' missing-branch message, which clone C covers. Elsewhere tests were only added, and an added test cannot let a caught mutation survive `[INFERRED]`.

## Questions for the operator

1. **F13.** A refused or failed clear exits 2: the run shows green with a warning, and is never marked failed. That was my choice, never put to you. Approve, or should a refused confirm mark the run failed?
2. **F16.** When you clear `Jobs`, should a classified row's rejection copy leave with it, as now, or stay its fifteen days?
3. **F14.** The secrets how-to names the private repository and then says the name is kept out. Correct the sentence, or remove the name?
4. **F20.** A local `data` branch was made on 2026-09-28 at 21:18 your time, not by this seat. Was it you, and may it be deleted?
