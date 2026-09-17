---
type: log
description: The first manual GitHub runs. The ticked test-mode run failed its own tests because TEST_MODE reached the test step; the unticked run succeeded and created the public data branch. Fix, reproduction, and the Speechify 191 explained.
status: current
---

# The first manual GitHub runs, 2026-09-17

Previous log: `2026-09-17-run-log-reader-and-speechify.md`. Same conversation, third brief. The operator pushed `6476573` to `main` and ran the workflow by hand.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `6476573`, also `origin/main` |
| Mode | **Mutating.** No job board contacted from this machine. Unauthenticated reads of GitHub's public Actions API, `git ls-remote`, and a fetch of the new `data` branch into a scratch clone, never into this repository's refs |
| Tests | 249 at start, 252 at end, all passing with `TEST_MODE` unset, `1` and `0` |
| Verification | 5 new mutations, all caught, run with `TEST_MODE=1` set. The simulation, extended to run the test step, reproduced GitHub's failure on `6476573` and passed on the fix |

**Tags.** `[VERIFIED]` exercised and observed this session. `[BELIEVED]` reasoned, not run. `[INFERRED]` concluded from verified facts that were not themselves observed. Unmarked means believed.

## What ran

`[VERIFIED]` through the Actions API. Both runs were `workflow_dispatch` on `main` at `6476573`.

| Run | Created | Result |
|---|---|---|
| 35236457737 | 14:52:11Z | **failure** at "Run the tests before touching a live board"; fetch, branch fetch and push skipped |
| 35236531478 | 14:52:49Z | **success**, every step. No annotations, so the Node 20 warning is gone |

`[VERIFIED]` 35236531478's run log on the branch has `"test_mode": false`, so it was a production run, and `git ls-remote` shows a new `refs/heads/data` at `272cfdb`. Which run had the box ticked is `[INFERRED]`: the failure below reproduces only with `TEST_MODE=1`, and the successful run was not in test mode. The API does not expose dispatch inputs.

## The defect: TEST_MODE reached the test step

The previous brief moved `TEST_MODE` from the Fetch step to the job's `env`, next to `DATA_BRANCH`, so every step saw it, including the tests. The new `main()` tests call `run.main()`, which reads `TEST_MODE` from the environment, and they expect production behaviour.

`[VERIFIED]` locally, `TEST_MODE=1` and the full suite on `6476573`: 6 failures and 1 error, all in `TestMain`:

- `test_a_no_commit_run_neither_reads_nor_writes_the_branch` (error)
- `test_a_commit_failure_after_a_fetch_is_not_reported_as_could_not_start`
- `test_a_fresh_machine_continues_from_the_branch`
- `test_a_posting_a_board_stops_sending_stays_on_the_branch`
- `test_a_refused_commit_set_fails_the_run_and_commits_nothing`
- `test_test_mode_commits_to_its_own_branch_and_never_to_production`
- `test_test_mode_starts_from_the_test_branch_not_production`

With `TEST_MODE=0` all 249 passed. The runner's own test output needs a signed-in read, so that it failed on these same seven tests is `[INFERRED]`.

**What made it invisible.** The local simulation of the workflow skipped the pip and test steps and ran only the three steps it was written to prove. It exported `TEST_MODE` to every step, exactly as the job-level `env` did, but no test step ran to be affected. Nothing tested the environment-variable route into test mode either, although that is the only route the workflow uses.

**The fix, in two layers.**

- `TestMain` removes `TEST_MODE` from the environment in `setUp` and restores it in `tearDown`, so the tests do not depend on where they run.
- `TEST_MODE` is set on the Fetch step only; `DATA_BRANCH` stays job-level, because the fetch and push steps need it.

Three tests were added:

- `TEST_MODE=1` with no flag commits to `data-test` and leaves `data` alone;
- `TEST_MODE=0` stays in production mode;
- the workflow defines `TEST_MODE` exactly once, inside the Fetch step.

**Verified.**

- The suite passes with `TEST_MODE` unset, `1` and `0` `[VERIFIED]`.
- `tools/mutations/2026-09-17-test-mode-env.json`, run with `TEST_MODE=1` set, caught 5 of 5 `[VERIFIED]`: the environment route removed; any value selecting test mode; the tests inheriting `TEST_MODE`, which reproduced exactly the seven failures above; `TEST_MODE` added at job level; and `TEST_MODE` missing from the Fetch step.
- The scratch simulation now runs the workflow's test step as well, with `TEST_MODE` exported to every step, which is harsher than the fixed workflow `[VERIFIED]`:
  - on `6476573`, a ticked run failed at the test step with the same seven, and no `data-test` was pushed;
  - on the fixed tree, 252 tests passed, `data-test` was created, and `data` stayed absent.

## The production data branch, checked

`[VERIFIED]` by fetching `data` from GitHub into a scratch bare clone.

| File | Records by source | CRLF |
|---|---|---|
| `fetch-all/greenhouse.json` | greenhouse 759 | no |
| `fetch-all/lever.json` | lever 37 | no |
| `filtered.json` | greenhouse 19, lever 2 | no |
| `seen.json` | greenhouse 759, lever 37 | no |
| `logs-runs/20260917T145257.903143Z.json` | the run log | no |

- **No Himalayas record in any file.** ADR-0020's Confirmation, first half, holds on GitHub: "confirm no file under `fetch-all/` sourced from an aggregator is present". Its second half, "that the local aggregator file contains the rows the run log says it fetched", **cannot be checked on a runner**: the run log says 500 Himalayas rows were written locally and 21 kept, and the runner that held them is gone. This is the architecture-chat question about Himalayas, now observed rather than simulated.
- **The commit identity** is `job-aggregator <job-aggregator@invalid>`, a parentless root, one commit.
- **The run log:** 12 boards `ok`, 1296 fetched, all new, 42 kept of which 21 were local only, and 36 of 500 requests: greenhouse 9, lever 2, himalayas 25 over 25 pages.
- **Per board:**

| Board | Fetched |
|---|---|
| speechify | 255 |
| veeamsoftware | 241 |
| gomotive | 145 |
| joblogic | 33 |
| coderoad | 27 |
| spreetail | 24 |
| careem | 21 |
| brkz | 19 |
| smart-working-solutions | 13 |
| globalli | 12 |
| banyancanopygroup | 6 |

- **The 21 kept employer-board rows** include the same seven reachable from Pakistan as on 2026-09-16: Careem twice, BRKZ twice, Globalli, Joblogic and Smart Working Solutions. Veeam's Senior Forward Deployed Engineer now appears three times, once each for Brisbane, Melbourne and North Sydney.
- **The run-log reader** read the branch and reported every source as first contact on its first run, as expected.

**Not yet exercised on GitHub:**

- fetching an existing branch;
- the restore;
- a fast-forward push from a depth-1 fetch;
- the `data-test` path of `DATA_BRANCH`.

The next run of either kind exercises the first three against `data` or `data-test`.

## Speechify's 191, explained

`[VERIFIED]` by comparing, posting by posting, the 361 Speechify rows of 2026-09-16T20:03Z with the 255 on the new `data` branch at 2026-09-17T14:52Z: 191 were in both, 170 were gone, 64 were new.

| Role | Published | 09-16 | Gone | New | 09-17 |
|---|---|---|---|---|---|
| Software Engineer, Platform | 2024-01-24 | 135 | 34 | 34 | 135 |
| Software Engineer, Platform | 2025-05-07 | 105 | 26 | 27 | 106 |
| Go-to-Market | 2026-05-06 | 93 | 93 | 0 | 0 |
| Head of Agent Relations | 2026-05-19 | 1 | 1 | 0 | 0 |
| Manual Quality Assurance Engineer, SIMBA Team | 2026-05-21 | 14 | 4 | 3 | 13 |
| Go-to-Market | 2026-05-22 | 11 | 11 | 0 | 0 |
| Go-to-Market Engineer | 2026-05-22 | 1 | 1 | 0 | 0 |
| Team Lead, Android Core Product | 2026-09-15 | 1 | 0 | 0 | 1 |

Four roles closed, 106 postings in all, and 64 location copies rotated out and back in. **361 minus 170 is 191**, the count run 35179218050 reported at 03:43Z. `[INFERRED]` that run saw the closures and the removed copies but not yet the 64 replacements, which appeared by 14:52Z. That run's ids were discarded, so the match is on the count alone. Speechify's board is not shrinking steadily: it closes whole roles and rotates the city list of the rest.

## Rejected alternatives

- **Only scoping `TEST_MODE` to the step.** It fixes the workflow and leaves tests that fail on any machine with `TEST_MODE` set. Both layers were changed.
- **Only isolating the tests.** It leaves the test step running under a variable it has no business seeing. Both layers were changed.
- **Fetching `data` into this repository's refs to inspect it.** A local `data` branch would change what a local committing run restores from. A scratch clone was used instead.

## Not done

- The fix is committed locally and **not pushed**. `main` on GitHub is `6476573`, whose production path works and whose ticked path fails at its own tests, before touching anything.
- The `data-test` path has not run on GitHub.
- No decision record written or edited.
