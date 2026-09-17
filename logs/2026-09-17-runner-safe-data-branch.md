---
type: log
description: The first GitHub run failed at the commit; five defects behind it fixed, reproduced locally before and after, and a standing verify-do-not-trust rule recorded.
status: current
---

# A runner-safe data branch, 2026-09-17

Previous log: `2026-09-17-vertical-slice.md`.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `cd1f290` |
| Mode | **Mutating.** No job board contacted. Five unauthenticated reads of GitHub's public Actions API and one `git ls-remote`. Every pipeline run was simulated against a local bare repository with the network replaced |
| Commits | `18f3808` docs, `dcc056a` the harness, then the commit carrying this log. Nothing pushed |
| Tests | 185 at start, 225 at end, all passing |
| Verification | 39 mutations kept in `tools/mutations/`, one per guarantee. 38 caught on the first pass; the 39th survived and was fixed with the test it lacked. Every catch attributed to the test meant to make it |

**Tags.** `[VERIFIED]` exercised and observed this session. `[RUN LOG]` from the step 6 output the operator pasted, not checkable here. `[ACCOUNT]` a previous session's report of its own actions. `[BELIEVED]` reasoned, not run. Unmarked means believed. **RECOMMENDATION** marks a recommendation, not a decision.

## The first GitHub run

`[VERIFIED]` through `https://api.github.com/repos/Waqas01CP/job-aggregator/actions/runs`: one run, number 1, id 35179218050, event `schedule`, created 2026-09-17T03:43:19Z, head `cd1f290`, conclusion `failure`. Its only slot between the push (commits dated from 19:30Z on 2026-09-16) and the check (10:23Z) is 00:00 UTC, so it ran 3h43m late. Steps: checkout, setup-python, pip install and the test step `success`; Fetch `failure`; Push `skipped`. Annotations: "the run could not start", "Process completed with exit code 1", and a Node.js 20 deprecation warning for `actions/checkout@v4` and `actions/setup-python@v5`.

`[RUN LOG]` The cause, from the operator: `src.storage.StorageError: git commit-tree ... failed: Author identity unknown / fatal: empty ident name (for <runner@...cloudapp.net>) not allowed`, raised from `run.py:298` through `storage.py:255`. Before it, all 12 boards `ok`, 1239 fetched, 37 kept, 36 of 500 requests. Speechify returned 191, down from 361 on 2026-09-16 and 1086 on 2026-09-11.

`[VERIFIED]` `git ls-remote --heads origin` returned only `refs/heads/main`. Nothing was published.

## What the handoff and the brief claimed, and what checked out

| Claim | Source | Check | Result |
|---|---|---|---|
| The workflow has never run on GitHub | handoff, `STATE.md` | Actions API | **False.** Corrected in `18f3808` |
| A manual `test_mode` run would not touch production data | handoff | read `fetch.yml`, `storage.branch_path`, `files_to_commit` | **False.** No `--no-commit`; `branch_path("data/test/seen.json", True)` printed `seen.json`; both modes commit to `data`, which is pushed |
| Five questions for the architecture chat are named in `STATE.md` | handoff | read `STATE.md` | Four are named. The brief supplied the fifth, the title pool `[ACCOUNT]`, and the log's own numbering fits it: experience is question 2 at log line 158 and "Question 3" at line 256 |
| No `data` branch exists | handoff | `git branch -a`, `git ls-remote` | True, locally and on the remote |
| The suite passes on 3.11 and 3.12 | `CLAUDE.md` | ran it | 185 pass on 3.12.10 locally; the Actions API shows the test step passing on the runner |
| `filtered.json` holds himalayas 20, `seen.json` himalayas 500 | brief | counted `data/test/` by `source` | True: filtered greenhouse 17, lever 2, himalayas 20; seen greenhouse 873, lever 43, himalayas 500 |
| The existing aggregator test checks only the raw file | brief | read `tests/test_himalayas.py:172-204` | True: it asserts no offered file *name* contains `himalayas` |
| ADR-0006's propagation assumption is recorded as confirmed | brief | read ADR-0006:29 and its Changes row | True. `STATE.md:117` was stale; corrected in `18f3808` |
| CodeRoad's 29/22/6 comes from a mixed-run table | brief | read the surviving run log, counted stored rows and duplicate identities | True: fetched 28 in that log, 28 stored, 0 duplicates. **My earlier "duplicate identity" explanation was an unchecked inference and was wrong** |
| The checkout lacks the remote `data` branch | brief, `[INFERRED]` there | local simulation with `git clone --depth 1 --branch main` | True for that simulation: "local branches after checkout: main". Whether `actions/checkout@v4` behaves the same is outside knowledge `[BELIEVED]` |

## Defects, reproduced on the old code

A scratch harness cloned this repository at `cd1f290` into a bare "origin", and simulated each run as a depth-1 clone of `main` with git identity removed (empty global config, no system config, `user.useConfigOnly`). It extracted each step's `run:` body from the checkout's own `fetch.yml` and ran it under `bash -eo pipefail`, replacing only `python -m src.run` with a driver that serves fake Greenhouse (2 postings, one titled with Japanese characters and an em-dash) and Himalayas (2 pages) responses. `[VERIFIED]` all of the following.

**On this Windows machine the old code fails before the identity problem.** Every run died in `hash-object` with `UnicodeEncodeError: 'charmap' codec can't encode characters`, because `_git` used text mode and the locale is cp1252. The runner's locale is not cp1252 `[BELIEVED]`, so to reach the runner's failures the old code was rerun with `PYTHONUTF8=1`:

| Run | What happened |
|---|---|
| A1, run 1, no identity | `commit-tree ... failed: Author identity unknown`, then `::error::the run could not start`, exit 1, push skipped. The runner's failure, reproduced |
| A2, run 1, identity supplied | Pushed `data`. **`filtered.json` and `seen.json` on the pushed branch each held 2 Himalayas records.** All three record blobs inspected had CRLF endings |
| A3, run 2, fresh runner | Checkout held only `main`. The run reported `new 4` of 4. Push **rejected** as non-fast-forward, exit 1 |
| A4, `test_mode`, fresh origin | Pushed **`data`**, not a test branch, holding the test run's files at production paths. `data-test` absent |

## The five defects

1. **No git identity on a runner.** `commit-tree` refuses to guess. Fixed with a fixed, non-personal identity passed through the environment to `commit-tree` only: `job-aggregator <job-aggregator@invalid>`. `.invalid` is a reserved top-level domain, so the address can never belong to anyone.
2. **Aggregator records inside committed files.** The raw aggregator file was excluded by name, but `filtered.json` and `seen.json` were single files holding every source and were offered whole. The filtered layer and the seen store now split by source the way the raw layer does, into `data/local/filtered.json` and `data/local/seen.json`, which are never offered. `files_to_commit` also reads every record file it offers and refuses the commit if any record's source is not publishable. Publishability is a named set, `PLATFORMS - AGGREGATOR_PLATFORMS`, so a source nobody named, or a record with no source, stays local.
3. **No memory between runs on a runner.** The workflow now fetches the run's branch before the run, if origin has it (`ls-remote --exit-code` distinguishes "absent", exit 2, from a failure to ask). A committing run then replaces its working copies of the raw files, `filtered.json` and `seen.json` with the branch's before fetching.
4. **Test mode published to production.** Test mode now commits to `data-test` and the workflow pushes whichever branch the mode chose. The branch keeps production's layout, which is exactly why it cannot share production's branch. A test holds the names in the workflow and the code in step.
5. **Text mode at the git boundary.** Found by this session's own test, not by the brief. On Windows, `_git` wrote every blob in cp1252 with CRLF endings, and raised for a character outside cp1252; `read_branch_file` undid both on the way back, so the existing round-trip test passed. Content now crosses the boundary as bytes, encoded and decoded as UTF-8 here. The runner, on Linux, was not affected by the newline half `[BELIEVED]`.

Plus the label: a failure after a completed fetch now prints the stage that failed and that the fetch completed, still exits 1, and the workflow's annotation no longer claims "could not start" for every exit 1.

## The same runs on the new code

The same simulation against a bare repository seeded with this session's working tree, **without** `PYTHONUTF8`, so the Windows boundary fix is exercised too. `[VERIFIED]` all of the following.

| Run | What happened |
|---|---|
| B1, run 1, no identity | The new step printed "origin has no data branch yet". The run printed "no data branch, starting from local files", exited 0 and pushed `data`. On the branch, the raw file, `filtered.json` and `seen.json` hold Greenhouse records only, and no blob contains CRLF. The two Himalayas records exist only in the runner's `data/local/` and `data/fetch-all-local/` |
| B2, run 2, fresh runner | The checkout held only `main`. The step fetched `data`, the run printed "3 file(s) restored from the data branch", Greenhouse reported `new 0`, and the push fast-forwarded `25cab90..3ab8f18`. History is linear with a parentless root, author and committer `job-aggregator <job-aggregator@invalid>` |
| B3, run 3, fresh runner, the board dropped 1000 and added 1002 | Greenhouse `new 1`. The branch's raw file holds 1000, 1001 and 1002 |
| B4, `test_mode` | "origin has no data-test branch yet". Pushed `data-test`. `data` had the same sha before and after |
| B5, `test_mode` again | Restored 3 files from `data-test`, Greenhouse `new 0`, `data-test` fast-forwarded |

## How it was verified

**Suite.** 185 tests at the start, 225 at the end, all passing on Python 3.12.10 `[VERIFIED]`. It takes about 19 seconds rather than 3, because the new end-to-end tests of `main()` build git repositories.

**Tests were written from the brief, the run log and ADR-0003 and ADR-0020**, and several assert the precondition that makes them meaningful. The identity test first proves the host refuses `commit-tree` without an identity, using `user.useConfigOnly`, an empty global config and no system config, so it cannot pass on a machine that guesses one. The aggregator test first proves both sources kept a row. The first run of the new tests failed on the blob-bytes assertion and exposed the CRLF half of defect 5, which nobody had predicted.

**Mutations.** `tools/mutations/2026-09-17-publication-and-state.json`, one mutation per guarantee, re-runnable with `python tools/mutate.py <file> --why`.

Run 1, 38 mutations: **38 caught, 0 survived**, files restored, suite passing again, no stray ref `[VERIFIED]`. Two survivors were predicted while writing the mutations, and a test was written for each before the run. *An unreadable listed branch file being skipped*: nothing read that path, so a test now makes `read_branch_file` return nothing for one listed file. *Raw files not selected by source*: the new content guard would refuse the same file, so the two checks had identical effect; the case that separates them is a leftover Himalayas raw file under `fetch-all/`, which must be passed over rather than refuse the whole commit.

A clean sweep proves only that *some* test failed. Run 2 added `--why`, which names the failing tests for each mutation, and ran all 39: **38 caught, 1 survived** `[VERIFIED]`. The full list was read. Every catch included at least one test written for that guarantee, and no catch came from an unrelated failure. Removing the fixed identity was caught by the two identity tests and nothing else. Skipping an unreadable listed file was caught only by the test written for it. Loading only the committed half of the seen store was caught only by the stop-rule test.

**The survivor** was the mutation added for the summary line, which says how many kept rows stay local. Its test used a Greenhouse-only run, where that count is zero, so a summary that always printed zero passed. That is a test whose precondition never occurs, the same shape as the vertical slice's `rag` survivor. The assertion moved to a run with a Himalayas row, and `--only` on that mutation then reported it caught by `test_the_summary_says_how_many_kept_rows_stay_local`. The full `--why` output was not kept; the command reproduces it.

**Harness self-check** `[VERIFIED]`: a known mutation reported caught; a docstring-only edit reported survived with exit 1; an anchor occurring 23 times refused before any file was touched; `git diff` empty afterwards.

## Mistakes in this session's own work

- **An unchecked explanation, stated as fact.** I told the operator the CodeRoad arithmetic came from a duplicated identity. I had not looked. The brief corrected it and the check agrees with the brief.
- **A `STATE.md` row tagged `[VERIFIED]` for figures I could not check.** The step 6 numbers came from the operator's paste. Corrected before `18f3808` was made; the row now separates the two.
- **A scratch script named `inspect.py`** shadowed the standard library module of that name, so the first reproduction's four runs all failed on an import. None of that output was used.
- **A mutation anchor written from memory** (a `#` comment that is a docstring line). The harness refused it, which is its guard working.

## For the architecture chat

**1. Himalayas on a runner keeps nothing.** ADR-0020's Consequences say aggregator history "exists only on the operator's machine". The schedule runs on a GitHub runner, which is discarded after each run. With aggregator stores kept local, as ADR-0020 requires, every scheduled run is Himalayas' first contact: it pages to the cap, every posting is new, and its kept rows are deleted with the runner. In the local simulation `[VERIFIED]` every one of the five runs reported Himalayas `new 2` and read both of its pages, including B2, B3 and B5, which followed runs that had already fetched the same two postings. On GitHub that is 25 of 36 requests per run, the split run 35179218050 reported `[RUN LOG]`, for output nobody can see, and it will dominate the month of run logs ADR-0028's Confirmation reads. The record's premise does not hold for the machine the schedule uses. The operator's one-line stopgap is removing the Himalayas entry from `config/boards.json`.

**2. ADR-0020's promised hook guard was never added.** The record says a guard rejecting an aggregator-sourced file from a commit "is added when the first aggregator adapter exists". `.githooks/pre-commit` has five gates and none does this `[VERIFIED]`. A hook could not guard the data branch anyway: commits built with `commit-tree` run no hooks. The guard that can work is the one now in `files_to_commit`. Whether the record should say so, or a hook gate for `data/` paths on `main` is still wanted, is the chat's to shape.

**3. Seen-store entries were treated as rows.** The conservative reading of ADR-0020, as the brief suggested. A seen entry carries the posting's URL, as its identity, and its publication date. If the chat reads "rows" more narrowly, the split can be undone for the seen store alone.

**4. Exit code 1 now has two causes.** `CLAUDE.md` fixed three codes and the brief said not to add a fourth, so 1 covers both "could not start" and "fetched but could not store". `CLAUDE.md`'s convention line is updated to say so. If a fourth code is wanted, that is a change to a convention.

The five questions from the previous session stand, with the title pool routed to the operator.

## Checked and found already correct

- `branch_exists` and `read_branch_file` resolve `REPO_ROOT` at call time, and `_git` resolves it per call. No test in this session created a ref in this repository: the harness's per-mutation ref comparison reported none in either run, and `git branch` showed only `main` each time it was checked, including after both mutation runs and before each commit.
- The workflow already ran the test suite before touching a live board, and the runner's test step passed.
- The pre-existing `test_a_second_run_with_no_new_postings_writes_nothing` still passes under the restore, and in B2 the restored run wrote no Greenhouse raw record.

## Rejected alternatives

- **Filtering aggregator records out of `filtered.json` and `seen.json` at commit time, leaving the local files mixed.** The committed file would then differ from the local one, breaking one canonical serialisation per file, and a restore would silently lose the aggregator half.
- **Restoring only files missing locally.** On a machine whose copy is older than the branch, the run would append to the stale copy and the commit would delete what the branch gained: the snapshot failure ADR-0003 exists to prevent. The branch wins.
- **Restoring on `--no-commit` runs too.** A no-commit run is exploratory and chains from local files, as the previous session's two-run check did. It also never writes the branch, so its starting point cannot corrupt it.
- **Setting the git identity in the workflow with `git config`.** It would fix the runner and leave every other machine depending on its own configuration, and the operator's name would appear on data commits made locally. The identity is fixed in code instead.
- **The `github-actions[bot]` identity.** It would claim to be GitHub's bot on commits made anywhere.
- **Exit 2 for a failed commit.** 2 means stopped deliberately and resumable, and the workflow pushes after a 2. Neither is true of a failed commit.
- **Adding a fourth exit code.** The brief ruled it out.
- **A YAML parser to test the workflow.** It would be a new dependency; the checks need a few exact lines.
- **Splitting the fixes into separate commits in the brief's order.** All five live partly in `storage.py`, and the environment has no interactive staging. The brief allows one commit, and nothing is pushed until the operator asks.

## Not done, and not established

- **Nothing was pushed.** The fixes have not run on GitHub. The next scheduled run uses the code on origin, which is still `cd1f290`, and will fail at the commit as run 35179218050 did, after spending its requests `[BELIEVED]`.
- **Whether `inputs.test_mode` resolves in a job-level `env`** is outside knowledge `[BELIEVED]`. The previous workflow used it at step level.
- **Whether a push from a depth-1 fetch fast-forwards on GitHub** is established only against a local `file://` remote.
- **The Node.js 20 deprecation** annotation was noted and not acted on.
- **The previous session's mutation files are lost.** Its 79 mutations cannot be re-run; only this session's 39 can.
- **`data/test/`** still holds a `filtered.json` with 20 Himalayas rows and a mixed `seen.json`. The next local test run splits the seen store. The filtered file is append-only, so a committing test run from this machine will refuse to commit `[BELIEVED]`, from `test_a_refused_commit_set_fails_the_run_and_commits_nothing`, which builds the same case. Deleting `data/test/` clears it.
- **Why Speechify is shrinking** was not investigated.
- No decision record was written or edited.

## Assumptions from outside this repository

- A GitHub-hosted runner has no git identity configured. Consistent with the run log, not read from GitHub's documentation.
- `actions/checkout` with `fetch-depth: 1` fetches only the triggering ref.
- The runner's locale is UTF-8.
- `inputs` is available in `jobs.<id>.env`.
- `.invalid` is reserved and never resolves (RFC 2606).
