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
committed, and exits 2. `make_airtable_client` and `read_private_stores` are
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
