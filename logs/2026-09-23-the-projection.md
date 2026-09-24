---
type: log
description: Brief 6. The Airtable client reshaped to one upsert of exactly ten fields with no read path, the projection built and wired into every committing run, the outcome stores restored and read from the private repository, a failed projection exiting 2, and a .env reader. Offline-verified over real data; the live checks wait on a push and a test-mode dispatch.
status: current
---

# The projection, and the Airtable client reshaped, 2026-09-23 UTC

Previous log: `2026-09-22-speechify-rotation-and-the-writer-check.md`. Same
session, a new brief.

| Header | Value |
|---|---|
| Date | 2026-09-23, 17:50Z onward, UTC. The local clock read 2026-09-23 too |
| Model | claude-opus-5-5 |
| HEAD at start | `b242d9a`, level with `origin/main`, with ten files of the architecture chat's uncommitted edits in the tree |
| Mode | **Mutating.** No job board contacted. No write to Airtable: `Jobs` and `Jobs test` read through the connector only. `data` and `data-test` read from scratch clones |
| Tests | 427 at start, 474 at end, all passing on Python 3.12.10, on 3.11.9 in a scratch venv, and on 3.11 with `TEST_MODE=1` `[VERIFIED]` |
| Verification | 37 mutations in two files, all caught `[VERIFIED]`. One was aimed at the wrong line by my own generator, found by reading its attribution, retargeted, and re-run caught by the tests meant for it |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means
believed. `[INFERRED]` reasoned from observed data, not tested.

## Before the brief: the tree, and two files held back

`origin/main` was `b242d9a` at 17:50Z, one commit past my `c3e5a4f`, so both
of the previous round's commits were already pushed `[VERIFIED]`
`git ls-remote`. Ten files carried the architecture chat's uncommitted edits.
The operator said `CHAT_STATE.md` is not mine to change, that the docs were
the chat's, and that I could push.

**Eight were committed unmodified as `ee0fc79`**: ADR-0004, 0035, 0038, 0043,
0044, 0046, `airtable-schema.md` and `retention.md`, which carry the five
rulings Brief 6 builds on. Read in full and scanned for identifiers first.

**Two were held back, uncommitted and untouched**: `CHAT_STATE.md` and
`docs/how-to/airtable-token-and-secrets.md`. Both write the private
repository's full name into this public repository, and both say in the same
passage that the name "is kept out of the public repository deliberately, per
ADR-0011" `[VERIFIED]` by reading the diff. Committing them would publish the
name in history for good, against their own stated intent. Raised with the
operator; not edited, since neither file is this seat's.

## Airtable's documentation, read before relying on it

The brief asked for the upsert shape to be confirmed against Airtable's own
documentation. `[VERIFIED]` 2026-09-23, `airtable.com/developers/web/api/update-multiple-records`:

- `PATCH` (or `PUT`) to `/v0/{baseId}/{tableIdOrName}`, with
  `performUpsert.fieldsToMergeOn`, "at least one and at most three field
  names", of text, number, date or select types. `Identity` is single line
  text.
- "If zero matches are found, a new record will be created. If one match is
  found, that record will be updated. **If multiple matches are found, the
  request will fail.**"
- "Billing plans: All plans". **Upsert is available; ADR-0035's fallback is
  not needed.**
- "A PATCH request will only update the fields included in the request.
  Fields not included in the request will be unchanged." So a `Status` the
  operator sets survives any projection that does not send it.
- The response carries `createdRecords` and `updatedRecords`.
- The page does not state a per-request record limit. Ten comes from
  ADR-0004, not re-confirmed.

`airtable.com/developers/web/api/rate-limits`: "5 requests per second per
base", a 429, and "wait 30 seconds before subsequent requests will succeed".
Nothing there on monthly limits.

## What was built

**`src/airtable.py`**, renamed from `src/airtable_client.py` to the brief's
name and cut down to what the brief allows:

- **One verb, `upsert`.** `list_records`, `create_records` and
  `delete_records` removed. Ruling 4 made checkable: the class's public
  callables are `upsert`, `counters`, `redact` and `from_env`, only `PATCH`
  reaches the fake wire, and the source names no read method, each a test.
- **Exactly ADR-0035's ten fields.** A record with any other key, `Status`
  above all, or missing one, is refused before anything is sent. The test
  pins the set against a literal written out by hand.
- **Test mode binds to `AIRTABLE_TEST_TABLE_ID` only.** No fallback: with
  the test ID empty and the production ID present, test mode refuses. A test
  ID equal to the production ID is refused too.
- **Pace 0.25 seconds**, under five a second, where the step-1 client sat at
  the limit. The brief says under.
- **Counters** for the run log's `airtable` block: calls, rows sent, the month
  so far, retries, failures, refusals.
- **A defect in my own step-1 client, closed here.** Its transport errors
  carried the exception's text, and `requests` quotes the URL, which holds
  the base and table IDs. A real connection error would have written both
  into a run log on the public branch. The step-1 test used `OSError("reset")`,
  which quotes nothing, so it could not see it. Now a transport failure is
  reduced to its class name before the retry loop sees it, and the test
  feeds a `ConnectionError` quoting the URL and the token.

**`src/projection.py`.** Read the public and local filtered files; apply the
current chain; group; skip a group when any member is in one of the three
classification stores; send the ten fields with the representative's
identity and every member's location, newline-joined. Each stage counted.
`removed_unreviewed.json` is named and never read.

**`src/storage.py`.** `outcomes/` restored with the rest of the branch.
`read_month_run_logs` reads this month's run logs back from the branch for the
monthly budget, because a runner restores none. `read_private_files` reads
the private repository through git with the token in an HTTP header, returns
`None` for an absent file and nothing for an empty repository, raises
`PrivateStoreUnreachable` when it cannot reach the repository, and scrubs the
token, its encoded header and the repository's name from every error.

**`src/run.py`.** `project_display` runs after the files are written and
before the run log is, and never raises. A committing run projects through
the client; a no-commit run plans from local files and reaches no base and no
private store; a failure is scrubbed of every secret the run holds, recorded,
committed, and exits 2. *(Overstated when written, found by the audit of
2026-09-24: the run-level scrub missed the private token's base64 form, which
git sends. Fixed that day.)* `make_airtable_client` and `read_private_stores` are
the two seams the tests replace, as they already replace `HttpClient`.

**`src/envfile.py` and `.env.example`.** Standard library only. Loaded at
the start of `main`; a name already in the environment wins, including an
empty one, so a runner is unaffected.

**`.github/workflows/fetch.yml`.** The six secrets on the Fetch step only;
the exit-2 warning names the projection beside the budget and the breaker.

**Records and rules.** `CLAUDE.md`'s exit-code line and ADR-0034's Changes
carry the exit-2 decision, as the brief instructs, with ADR-0034's
Consequences sentence annotated in place.

## Decided here, and why

- **Matched term from `title_normalised`, not the raw title.** The brief says
  "what the current matcher returns for the representative's title". The
  chain's title rule matches `title_normalised` (`src/filters.py`,
  `rule_title`). On a board with a city in its titles the two differ:
  "Data Engineer - AI Engineer Plaza, Karachi" matches `ai engineer` raw and
  `data engineer` normalised `[VERIFIED]` against the live pool. The display
  must name the term that admitted the row, per ADR-0021. Reported as a
  correction to the brief.
- **`Title` is the representative's raw title**, as `airtable-schema.md`
  describes the field: "as the board states it". For Speechify that shows one
  city in `Title` and 158 in `Location`. Whether the operator would rather see
  the normalised title is his question, not this seat's.
- **Dates to the millisecond, UTC.** Stored times carry microseconds; the
  canary rows already in `Jobs test` carry milliseconds, which is what is
  known to be accepted.
- **An unreachable private store fails the projection and exits 2**, not 1.
  The brief says such a run "fails visibly"; exit 2 after a commit is
  visible in the log, the output and the workflow warning, and exit 1 would
  lose the fetch, the brief's own reason for exit 2. Reported as an
  interpretation to confirm.
- **The monthly count reads the run's own branch only.** A runner fetches
  one branch, so a test run's calls are not counted against production's
  month or the reverse. Test runs are hand-dispatched and rare.
- **No `HEAD` literal in the private-store reader.** ADR-0031's preference
  audit matched git's `HEAD` as the seniority word "head", and it has no
  allow mechanism beyond comments and docstrings. `ls-remote` with no ref and
  `fetch` with no refspec do the same job `[VERIFIED]` against a real local
  repository: refs listed, blank for an empty repository, the default branch
  in `FETCH_HEAD`, and 128 for a missing path. The audit is untouched.
- **The shared loop's non-repeatable path is kept and now tested directly**,
  in `tests/test_resilience.py`. Removing the create and delete verbs left it
  with no caller; the sweep's deletes will need it. Rejected: deleting it now
  and rebuilding it next brief.

## Offline verification, over real data

`[VERIFIED]` with the repository's own modules and a recording client, over
`filtered.json` from a scratch clone of `data` at `bab0acf`, 14 run logs:

| Check | Result |
|---|---|
| Rows read, admitted, groups, to send | 345, 334, 29, 29 |
| Projected groups equal the groups the chain admits | Yes, 29 and 29 |
| `filtered.json` byte-identical afterwards | Yes, `d0f73c93b60423f7` before and after |
| Every record exactly the ten fields, in order | Yes |
| Every identity sent is a group representative | Yes |
| Largest group | `speechify\|software engineer platform\|2024-01-24`, 170 members, 158 distinct locations, all 158 in its `Location` |
| Representative `greenhouse:5058944004` in `accepted.json` | Group skipped; removed from the store, projected again |
| Non-representative member `greenhouse:5974247004` in `rejected_not_a_fit.json` | The whole group skipped, no member of it sent |
| Both only in `removed_unreviewed.json` | Group projected: the fourth store is not read |

At 29 groups the projection costs three upsert calls a run, 10, 10 and 9,
which is ADR-0046's corrected figure.

## Checked and found correct

- The five rulings, in the committed Changes rows of ADR-0004, 0035, 0043
  and 0046, match the brief's summary of them.
- `.gitignore` ignores `.env` and `.env.*` and allows `.env.example`.
- `Jobs` is empty; `Jobs test` holds ten canary rows, each with a unique
  `Identity`, so an upsert can match at most one per key.

## The live checks, and what the canaries do to them

Not run: they need the operator's push and a test-mode dispatch.

**`Jobs test` will not equal the sent count while the canaries are there.**
Planned over `data-test` at `6c7425d`, the test projection sends 11 groups
and only 4 of the 10 canary identities are among them `[VERIFIED]`. The live
run fetches and backfills into `data-test` first, so the exact figures will
move, but up to 6 canaries will stay untouched and the count will read sent
plus those `[INFERRED]`. Either the operator deletes the ten canaries before
the first test run, or the check subtracts the unmatched ones. His decision;
deleting Airtable rows is not this brief's.

## Mutations

`tools/mutations/2026-09-23-projection.json`, 20, run with `tools/mutate.py
--why` `[VERIFIED]`. The four the brief names, and what caught each:

| Mutation | Caught by |
|---|---|
| `Status` added to the sent set | `test_the_sent_set_is_exactly_adr_0035s_ten`, `test_status_is_refused_before_anything_is_sent`, and 43 others, since every record the tests build is then short a field |
| Test mode resolves to the production table | `test_test_mode_takes_the_test_table`, `test_a_missing_test_table_is_refused_never_replaced_by_production` |
| The skip tests the group's identity, not every member | `test_any_member_in_a_store_skips_the_whole_group` alone |
| The skip reads the fourth store | `test_the_fourth_store_is_not_read` alone |

The other sixteen, each caught by the test written for it: a test table equal
to production allowed; a `GET` reaching the wire; a transport failure keeping
its URL; the client's `redact` doing nothing; a no-commit run projecting for
real; a failed projection exiting 1; the run's secret scrub doing nothing; the
month so far not read; Matched term from the raw title; the representative's
location only; outcome stores not restored; an unreachable private store read
as empty; the private store's errors unscrubbed; its token in plain text on a
command line; `.env` replacing what is set; a secret reaching the test step.

**An error of mine, caught by reading the attribution.** "A failed
projection exits 1" was first reported caught by
`test_budget_exhaustion_stops_the_run_and_names_what_was_missed`, a budget
test. The generator had taken the first line containing
`return EXIT_STOPPED_RESUMABLE`, which is in `Run.exit_code()`, so the
mutation broke the budget path and never touched the projection's. A count of
"caught" would have hidden it. Anchored on the projection branch's own
message and re-run: caught by `test_a_failed_projection_still_commits_and_exits_2`,
`test_an_unreachable_private_store_fails_the_projection_visibly` and
`test_a_failure_quoting_a_secret_is_scrubbed_before_it_is_logged`.

`tools/mutations/2026-09-23-shared-resilience-and-airtable-client.json`,
regenerated against the reshaped client: 17, all caught. The four entries
for the removed create and delete verbs are gone, and the finds that moved
are retargeted. **ADR-0034's Confirmation still holds**: breaking the shared
backoff fails tests in `test_http_client`, `test_airtable` and
`test_resilience`. The non-repeatable path's three mutations are now caught
by `tests/test_resilience.py`, where before this round they were caught
through the create and delete verbs.

## Not done

- The live checks, above.
- `CHAT_STATE.md` and the Airtable how-to, held back uncommitted.
- The heredoc hook's relative path. The audit report hit the same failure.
- The audit report's findings about the decision corpus. They are for the
  architecture chat; the operator noted some may already be resolved.
- Measured Airtable calls per run: none exist until the first live run.

---

# The first live run, the operator's answers, and the hook fixed, 2026-09-23 UTC

The operator pushed `ee0fc79`, `5ea1e8c` and `5768cf0` and dispatched the
workflow from `main` with the test-mode box ticked, which is the intended
dispatch: the workflow always runs from `main`, and that box is `test_mode`.

## Live run 1: the projection reached `Jobs test`

`[VERIFIED]` run 35912554579, `workflow_dispatch`, head `5768cf0`, created
2026-09-23T19:55:43Z, conclusion success (public Actions API). `data-test`
moved from `6c7425d` to `105d10a`; `data` stayed at `bab0acf`. Its committed
run log, read from a scratch clone of `data-test`:

| Block | Values |
|---|---|
| `projection` | 371 rows read (344 public, 27 Himalayas), 361 admitted, 56 groups, 0 skipped by a store, 56 to send, 56 sent |
| `airtable` | 6 calls, 56 rows sent, 0 retries, 0 failures, 0 refused, breaker closed, `failure` null, 994 of 1,000 left this month |
| Fetch | 36 requests; backfill appended 257, the test branch's first backfill |

Read back through the connector at 20:07Z `[VERIFIED]`: **`Jobs test` holds
56 records, equal to the sent count, and `Jobs` holds 0.** Every `Status` is
empty. Dates at millisecond precision were accepted. **No failure also means
the private repository was reached**: with either store secret empty the read
refuses by name, and with the repository unreachable it raises, so both
secrets exist and a fine-grained token in a Basic header reaches it through
git on a runner. Whether the repository holds any file yet is not visible
from here.

**My canary prediction was wrong.** I said up to six of the ten canary rows
would be left over, from a plan over `data-test` as it stood. The run's
backfill added 257 rows to `data-test` first, and all ten canary identities
were among the 56 sent. Each canary was matched and overwritten, its `First
seen` and `Published` now the pipeline's, so no duplicate and no leftover:
the count check holds exactly.

**The measured calls, against ADR-0046's corrected budget.** Six calls for 56
groups. ADR-0046 budgets the projection at three calls a run from 29 groups,
but that count is the public filtered file alone. Since ADR-0047, aggregator
rows reach the private base, and this run projected 27 Himalayas rows beside
the public ones. A production run will do the same, so the projection is five
or six calls a run rather than three, about 300 to 360 a month for that line
alone, and the total nearer 60% than 45% `[INFERRED]` from one test run. A
second consequence: until ADR-0047's write path is built, Himalayas rows live
only for the run that fetched them, so no run re-projects or removes an
earlier run's, and they accumulate in `Jobs` until the sweep's step 4 exists.
Against the free plan's 1,000-record cap across the base, which ADR-0046
sources and has not re-verified, that is the number to watch. Both are for
the architecture chat.

## The operator's answers

1. **Delete the ten canaries.** Not done, and why: after run 1 they are no
   longer canaries. Each was matched on `Identity` and every one of its ten
   pipeline-owned fields overwritten by the projection; only its
   `createdTime` remembers the seeding. Deleting them would remove ten live
   projection rows that the next run recreates, which is exactly the count
   change the second run's check must not see. Offered to delete if he still
   wants it.
2. **Naming the private repository is fine.** `CHAT_STATE.md` and the
   Airtable how-to are committed as the chat wrote them, in a commit of their
   own. Their sentence saying the name is kept out of this repository is now
   untrue; the wording is the chat's to fix.
3. **Exit 2 is reasonable; suggest better if there is one.** A
   recommendation, labelled as one, below.
4. **Normalised title, raw title kept.** Built: `Title` is `title_normalised`.
   Normalisation only removes a trailing " - <city>" equal to the row's own
   location field (`src/normalise.py`, `strip_location_suffix`); it changes
   299 of 345 stored rows, all Speechify city copies `[VERIFIED]`. The raw
   `title` is stored beside it in the raw layer and the filtered layer on the
   branch, which a test now pins. **The exception:** Himalayas rows are not
   durably stored anywhere until ADR-0047's write path exists.
5. **Fix the hook path.** Done; below.

## Recommendation for question 3: persistent failure turns the run red

The operator wants not to have to check whether the store works. Exit 2 is
right for one failure, since the next run repairs it, but the workflow shows
exit 2 as a green run with a warning, so a projection failing every run for a
week would look healthy from the Actions list. **Recommended:** count
consecutive projection failures from the month's run logs, which the run
already reads for the budget, and on the third in a row still commit and
push, then fail the job after the push step. Data is never lost, a single
failure stays quiet, and a persistent one shows as a failed run. Two things
make it the chat's rather than this seat's: it changes the exit contract
`CLAUDE.md` states, and a failed scheduled run makes GitHub email the
repository owner by default, which sits close to the scope floor's "no
notification system" even though nothing new is built. That GitHub behaviour
is from outside this repository and was not checked this session. ADR-0018's contract
check, still unbuilt, is the other home for store health.

## The hook, fixed and proved

`.claude/settings.json` now runs the guard through a Python launcher rather
than a relative path. It looks for `tools/heredoc_guard.py` from
`CLAUDE_PROJECT_DIR` if the harness sets it, else from the working directory,
walking up the parents, and exits 0 when it finds nothing, so the guard fails
open as it was designed to and never blocks every call again.

Proved offline `[VERIFIED]`, `scratchpad/hookprobe.py`, the exact launcher
string run with a payload built to trigger the guard and one built not to:

| From | Env var | Risky heredoc | Harmless command |
|---|---|---|---|
| `docs/decisions` | set | ask | nothing |
| `docs/decisions` | unset | ask | nothing |
| outside the repository | unset | nothing, fail-open | nothing |

Proved live `[VERIFIED]`: with the new settings in place, the shell was moved
into `docs/decisions` and left there, and the next Bash call ran. Before the
fix that exact sequence refused every call with "can't open file".

## Not done

- **Live run 2**: the operator sets `Status` by hand on one `Jobs test` row
  and dispatches a second test run; then the value must survive, no
  `Identity` may appear twice, and `Jobs` must still hold 0.
- The canaries, per answer 1.
- The `Title` field's own description in the base still says "as the board
  states it". Changing it is an Airtable schema write, offered rather than
  done.
- **Production goes live on the next scheduled run.** The code is on `main`;
  the next cron is 00:00Z, landing about 03:30Z on 2026-09-24 by recent runs,
  and it will project into `Jobs`.

---

# Live run 2: the operator's `Status` survives, 2026-09-23 UTC

**Both live checks pass.** `[VERIFIED]` run 35917058573, `workflow_dispatch`
on `af899c1`, created 20:36:13Z, success; `data-test` `105d10a` to `d71e4ea`,
`data` still `bab0acf`. It ran the normalised-title code.

| | Run 1, 19:55Z | Run 2, 20:36Z |
|---|---|---|
| Rows read (public + Himalayas) | 371 (344 + 27) | 369 (344 + 25) |
| Admitted | 361 | 359 |
| Groups (public + Himalayas) | 56 (29 + 27) | 54 (29 + 25) |
| Sent | 56 | 54 |
| Calls | 6 | 6 |
| Month so far before the run | 0 | **6** |
| Backfilled | 257 | **0** |
| Failure | none | none |

**The operator's hand-set values.** Before run 2 he set `Status` on four
`Jobs test` rows through the browser, the old choices being all that exist:
`greenhouse:4977137101` `applied` at 20:31:49Z, `greenhouse:4406476009`
`applied` at 20:32:35Z, a Himalayas row `rejected_choice` at 20:33:22Z and
another `rejected_pipeline` at 20:34:57Z, the times being their `Classified
at` values. After run 2, read through the connector at 20:43Z `[VERIFIED]`:
**all four values are still there, and all four `Classified at` values are
unchanged.** `Classified at` watches `Status` alone, so an unchanged value is
direct evidence the run never wrote `Status`.

**The survival proof rests on rows the run actually re-sent.** Himalayas rows
live only for the run that fetched them, so a Himalayas row marked by hand
may simply not have been sent again. Both ATS rows were: planned over
`data-test` at `d71e4ea` with run 2's clock, `greenhouse:4406476009` and
`greenhouse:4977137101` are in the 29 public groups `[VERIFIED]`. The upsert
matched each and updated its pipeline-owned fields, and the operator's field
survived. That is ADR-0035's check that can fail, passed live.

**No duplicate, and the count moves only by new postings.** `Jobs test` went
from 56 to 59 `[VERIFIED]`. The three created at 20:37Z are Himalayas
postings whose identities were not in run 1's list. Run 2 sent 54, so 51 were
matched and updated in place. The strict form of ADR-0035's Confirmation, the
same batch twice with the count identical, cannot occur against live boards;
it holds in the form they allow.

**Accumulation, observed rather than inferred.** 56 plus 3 less 54 sent means
**five of run 1's Himalayas rows were not sent again and remain in `Jobs
test`**, untouched, after one run. Nothing will remove them until the sweep's
step 4 exists, and nothing re-sends them because ADR-0047's store is unbuilt.
Two runs a day at this rate is the accumulation the previous section
inferred.

**The budget carries across runs.** Run 2's `month_to_date_before_run` is 6,
run 1's `calls_used` read back from `data-test`'s run logs by
`storage.read_month_run_logs`: the monthly count works on a runner that
restores no run logs. And the backfill appended 0 after run 1's 257, the
idempotence ADR-0030 claims, now on the test branch too.

`Jobs` holds 0 `[VERIFIED]`: two test runs, no production write.

## Still not done

- Production's first projection, at the next scheduled run.
- The `Title` field's description in the base.
- `null` for an empty field: no row sent had one.

---

# The audit, its nine findings fixed, and production's first projection, 2026-09-24 UTC

The operator ran the audit brief. The audit seat read `d8f3658` to `f864053`
at `f864053`, wrote nothing to the repository, and found nine things. Its
verdict: the work does what the operator and Brief 6 asked, every safety
property held against the case built to break it, and no finding is a live
pipeline defect. Each finding was checked at its line before it was fixed.

## Production's first projection

`[VERIFIED]` scheduled run 35951490496, created 2026-09-24T03:27:00Z, on
`f864053`, success; `data` moved from `bab0acf` to `a5abc3b`. Its run log:
360 rows read (345 public, 15 Himalayas), 349 admitted, 44 groups (29 plus
15), 44 sent in 5 calls, no failure, no retry; `month_to_date_before_run` 0,
because the two test runs' calls sit on `data-test`, as designed. `Jobs`,
read through the connector at about 09:50Z, holds 44 records, every `Status`
empty, Speechify's rows showing the normalised title.

Two things seen in `Jobs` and not investigated. A Himalayas row titled
"Fullstack Developer | Sênior (13593)" was admitted. `fold` normalises with
NFKC, which keeps the circumflex, so "sênior" never matches the seniority word
"senior". That is a filter gap, and a rule change is the operator's. And
"GTM AI Engineer -Deal Desk" appears twice: once from Motive's Greenhouse board
and once through Himalayas under the company slug `thinkmotive`. Cross-source
deduplication depends on the employer names agreeing (ADR-0026). Both go to
the architecture brief.

## The findings, and what was done

| # | Finding | Done |
|---|---|---|
| 1 | STATE.md's headline and its "audit seat has never run", and four sentences in `build-the-writer.md`, still said the writer was unbuilt or unrun | Annotated with dates in all six places; the headline now states what the production run did |
| 2 | Two more future timestamps, in `af899c1` and `f864053`, after `5768cf0` had fixed the first | Both corrected to their commit times, with notes. **A mechanical guard instead of a third promise:** gate 4 of the pre-commit hook now refuses a staged STATE.md whose first "Last verified" time is later than the moment of committing. Kept inside gate 4 so the documented count of six gates stays true |
| 3 | STATE.md claimed a hook mutation that did not exist, and nothing in the repository tested the launcher | The claim is annotated. `TestTheLauncher` in `tests/test_heredoc_guard.py` runs the exact launcher read out of `.claude/settings.json`, and three mutations of the settings file are caught |
| 4 | Two tests that could not fail for what their names say | The title test now builds its row through the real normaliser, and the audit's own mutation, a normaliser storing the normalised title as `title`, is caught by it. The ten-field test now compares against the ten names written out by hand, and the audit's mutation, `Status` added to both the constant and `fields_for`, is caught by it |
| 5 | The run-level scrub missed the private token's base64 form | `storage.private_store_basic` builds the encoding in one place; `redact_secrets` scrubs it too; the run test raises an exception quoting it and asserts it reaches neither the committed log nor the output. The log's sentence that overstated the scrub is annotated |
| 6 | `storage.py` said the private repository's name "never appears in a file here", made false by `fe07242` | The comment now says what is true: the run treats the name as a secret and scrubs it from all output; documents may name it, by the operator's decision |
| 7 | The guard switched off silently when `CLAUDE_PROJECT_DIR` pointed elsewhere | The launcher searches from the variable and from the working directory. When it finds nothing it still fails open, but now prints a `systemMessage` saying the command was not checked. The guard itself now returns 0 on a payload that is valid JSON but not an object, where it used to exit 1 |
| 8 | A remote with an unborn default branch beside other branches was reported as unreachable | A listed-but-unfetchable store now says "was reached and listed, but its default branch could not be fetched", still failing visibly |
| 9 | `d8f3658` combined the small commit with the cold check, unreported | Reported here. The cold check's findings were logged in the same commit as the small change the operator approved; the two were not separated |

Also from the audit, corrected: `src/projection.py`'s docstring said "every
layer stores `title`", which is true of the branch and not of `Jobs` or of
aggregator rows. It now says which is which.

For the architecture chat, from the audit: ADR-0027:61 says dedupe
normalisation and title matching "must not be merged", and the chain has
matched on `title_normalised` since before this work; and the treatment of the
private repository's name as a secret in code no longer matches the tree's
documents.

## Proving the timestamp gate

`[VERIFIED]` with the case built to defeat it: with every file of this commit
staged and STATE.md stamped 2026-09-24T10:15Z while `date -u` read 10:10Z,
`git commit` was refused with "COMMIT BLOCKED: STATE.md says it was last
verified at 2026-09-24T10:15Z, but it is now 2026-09-24T10:10Z UTC", and no
commit was made. The stamp was then set from `date -u` and the commit passed.

## Mutations

`tools/mutations/2026-09-24-audit-fixes.json`, 9, run with `--why`
`[VERIFIED]`, all caught, each by a test built for it:

| Mutation | Caught by |
|---|---|
| The launcher searches the project directory only | `test_a_project_dir_pointing_elsewhere_does_not_switch_it_off` |
| The launcher does not walk up to the parents | the two subdirectory tests of `TestTheLauncher` |
| The launcher fails open silently | `test_where_no_guard_exists_it_fails_open_and_says_so` |
| The guard exits 1 on a payload that is not an object | `test_a_payload_that_is_not_an_object_never_blocks` |
| The normaliser stores the normalised title as the title, the audit's own | `test_original_title_is_never_replaced`, and now `test_title_is_the_normalised_one_and_the_raw_one_stays_in_the_store` |
| `fields_for` emits `Status` | `test_the_fields_are_exactly_the_ten` |
| `Status` added to the constant | 46 tests, including `test_the_sent_set_is_exactly_adr_0035s_ten` |
| The run's scrub misses the encoded token | `test_a_failure_quoting_a_secret_is_scrubbed_before_it_is_logged` |
| A listed but unfetchable store is called unreachable | `test_a_failed_fetch_is_unreachable_too` |

The audit's combined case, `Status` in both the constant and `fields_for` at
once, spans two files and so cannot be one mutation for the harness. It was
applied by hand to a scratch copy of the tree `[VERIFIED]`:
`test_the_fields_are_exactly_the_ten` failed, where before the fix it passed.
Every find in the two 2026-09-23 mutation files still occurs exactly once.
