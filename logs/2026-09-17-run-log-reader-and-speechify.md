---
type: log
description: The four follow-ups done without operator input. Workflow actions moved to Node 24, the em-dash count corrected, a run-log reader for ADR-0028 built, and Speechify's shrinkage explained from saved data.
status: current
---

# Run-log reader, Node 24 actions, and Speechify, 2026-09-17

Previous log: `2026-09-17-runner-safe-data-branch.md`. Same conversation, second brief from the operator: do the four items the first report listed as needing no input.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `659bbee` |
| Mode | **Mutating.** No job board contacted. Unauthenticated reads of GitHub's public API and raw files for two actions' tags and release notes, and two GitHub documentation pages |
| Tests | 225 at start, 249 at end, all passing |
| Verification | 22 new mutations; 21 caught on the first pass, the survivor fixed with the case its test lacked. Nothing pushed |

**Tags.** `[VERIFIED]` exercised and observed this session. `[RUN LOG]` from the step 6 output the operator pasted. `[BELIEVED]` reasoned, not run. Unmarked means believed.

## 1. Workflow actions on Node 24

Run 35179218050 annotated: "Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5."

`[VERIFIED]` the `runs.using` line of each tag's `action.yml`, read from `raw.githubusercontent.com`:

| Tag | Runtime |
|---|---|
| checkout v4 | node20 |
| checkout v5, v6, v7 | node24 |
| setup-python v5 | node20 |
| setup-python v6, v7 | node24 |

`[VERIFIED]` release notes through the GitHub API. checkout v5.0.0: the Node 24 update and a minimum runner of v2.327.1, nothing else. checkout v6.0.0: "Persist creds to a separate file". checkout v7.0.0: blocks fork checkouts for `pull_request_target` and `workflow_run`, and an ESM migration. setup-python v6.0.0: Node 24 as its breaking change, plus unused enhancements. setup-python v7.0.0: removes the `pip-install` input, which the workflow does not use.

**Chosen: `checkout@v5` and `setup-python@v6`**, the lowest majors on Node 24. A test holds each action at or above those majors, and two mutations reverting them are caught.

**Rejected: the latest majors.** checkout v6 changed how the credentials the push step uses are persisted, and the push path has never run on GitHub. Changing it in the same push as its first test would leave a failure with two candidate causes. It is a one-line change once the push has worked.

**Not established:** that the annotation is gone. Only a GitHub run shows that. That GitHub-hosted runners meet v2.327.1 is `[BELIEVED]`; run 35179218050 already forced Node 24 onto both actions and succeeded in those steps.

## 2. The em-dash

The first report said "the one em-dash, which was already in `CLAUDE.md:46`". **That was true only of the three files I had searched.** `[VERIFIED]` `git grep -c` across tracked files: 54 in 7 files.

| File | Count | What they are | Action |
|---|---|---|---|
| `CLAUDE.md` | 1 | prose, line 46 | replaced with ", which is" |
| `STATE.md` | 5 | empty-cell placeholders in PENDING rows | left; not prose |
| `src/normalise.py` | 1 | inside the separator regex at line 123, matching em-dashes in titles | left; removing it breaks normalisation |
| `tests/test_normalise.py`, `tests/test_storage.py` | 1, 2 | deliberate non-ASCII test data | left |
| `docs/research/0004-project-context-documentation.md` | 7 | prose in a research record | left; not an implementing session's to restyle |
| `docs/architecture.md` | 37 | prose in the superseded architecture | left |

**Noticed:** the two `—` escapes I wrote into `tests/test_storage.py` in the previous brief reached the file as literal characters, and so did the Japanese test strings. The editing tool decodes `\u` escapes in its input. Python reads both forms identically, so nothing broke `[VERIFIED]` by the suite, but a later session writing escapes on purpose should check the bytes with `cat -A`.

## 3. The run-log reader

`tools/run_log_report.py`. ADR-0028's Confirmation: "Over the first month, the run log records requests per source and per run. The ceiling is then set from the observed distribution, with a stated margin, and this record amended." Its Consequences add that "a ceiling that is hit routinely means the cadence, the board set or the ceiling is wrong."

It reads the `data` branch by default, `data-test` with `--test-mode`, another repository with `--repo`, or a directory with `--dir`, and `--since` trims the start. It prints:

- the span of runs, against the first month the record asks for;
- requests per run and per source as n, min, median, nearest-rank p90 and max;
- per source, how many runs were first contact, flagged "every run" when all were;
- runs that reached the ceiling (`requests_used >= budget`), runs that ended with the circuit open, board lines marked not reached, retries and failures;
- boards whose latest runs fetched nothing or failed, with the streak length and span, because CLAUDE.md says a board silent for a week is a broken adapter.

**It proposes no ceiling and applies no silence threshold.** Both are decisions no record has made.

Design choices, each with its reason:

- **Stops are classified on structured fields**, never on the `stopped` message, because CLAUDE.md forbids classifying errors on message substrings. `refused` counts both budget and circuit refusals, so it is not used.
- **A source absent from a run's `by_source` is absent, not zero.** A run that never reached a source says nothing about its need.
- **Test-mode logs are excluded from a production report and counted**, because before 2026-09-17 a test run committed to the production branch.
- **Branch names come from `src/storage.py`**, not repeated.
- **One `git cat-file --batch`** reads every log, so a year of twice-daily runs is one process.

`[VERIFIED]` against every real log source available:

| Source | Result |
|---|---|
| this repository | exit 1: "no data branch ... git fetch origin data:data" |
| `data/test/logs-runs`, as production | exit 1: "other mode: 1" |
| `data/test/logs-runs`, `--test-mode` | 1 run, 36 requests: greenhouse 9, himalayas 25, lever 2 |
| the simulated origin's `data` | 3 runs of 3 requests; **himalayas first contact on 3 of 3, flagged "every run"** |
| the simulated origin's `data-test` | 2 runs; himalayas flagged "every run" |
| the old-code origin A's `data` | 1 run read |
| the old-code origin B's `data`, written by a test run | exit 1: "other mode: 1", the contamination the old code produced |

**Tests:** 23 in `tests/test_run_log_report.py`, written from the Confirmation; the 24th new test this session is the Node 24 check in `tests/test_workflow.py`. One builds two logs with `src/run.py` itself, so a change to the writer's shape breaks the reader's tests.

**Mutations:** 22 in `tools/mutations/2026-09-17-run-log-report.json`, 21 caught on the first pass, each by a test written for that guarantee. **The survivor** counted a source absent from `by_source` as a zero. Its test had no board line for such a source, so the mutation had nothing to act on: the fixture lacked the case again, the same shape as the summary-line survivor earlier today. The test now includes a Himalayas board marked not reached, and the mutation is caught.

## 4. Why Speechify keeps shrinking

**Mostly, four roles closed.** Each had been posted once per location, 105 to 241 times.

`[VERIFIED]` by comparing, posting by posting, `raw_responses/greenhouse-speechify.json` (1086 postings, saved 2026-09-11 21:06Z by file time) with the 361 Speechify rows stored by the TEST_MODE run of 2026-09-16T20:03Z. The raw snapshot went through the pipeline's own adapter and normaliser with Speechify's `strip_location_suffix`. The span is 4.96 days. 273 ids were in both, 813 were gone, and 88 were new.

| Role | Published | 09-11 | Gone | Kept | New | 09-16 |
|---|---|---|---|---|---|---|
| Software Engineer, Data Infrastructure & Acquisition | 2023-12-04 | 105 | 105 | 0 | 0 | 0 |
| Software Engineer, Platform | 2024-01-24 | 138 | 35 | 103 | 32 | 135 |
| Software Engineer, Platform | 2025-05-07 | 103 | 25 | 78 | 27 | 105 |
| Senior Software Engineer, Core Experiences | 2025-08-26 | 241 | 241 | 0 | 0 | 0 |
| Senior Software Engineer, Windows/Desktop Applications | 2025-12-02 | 241 | 241 | 0 | 0 | 0 |
| Software Engineer, Data Infrastructure & Acquisition | 2025-12-05 | 136 | 136 | 0 | 0 | 0 |
| Go-to-Market | 2026-05-06 | 95 | 25 | 70 | 23 | 93 |
| Head of Agent Relations | 2026-05-19 | 1 | 0 | 1 | 0 | 1 |
| Manual Quality Assurance Engineer, SIMBA Team | 2026-05-21 | 13 | 2 | 11 | 3 | 14 |
| Go-to-Market | 2026-05-22 | 12 | 3 | 9 | 2 | 11 |
| Go-to-Market Engineer | 2026-05-22 | 1 | 0 | 1 | 0 | 1 |
| Team Lead, Android Core Product | 2026-09-15 | 0 | 0 | 0 | 1 | 1 |

- **723 of the 813 losses are four whole roles**, closed with every location copy.
- **The other 90 losses are location copies of roles still open**, almost matched by 87 new copies of the same roles. The roles rotate which cities they list, and their totals barely move.
- **One new role** makes the 88th new posting.
- **`updated_at` does not mark the closures.** Gone and kept postings share the same bulk-stamp dates (2026-08-28, 2026-09-02, 2026-09-08), consistent with the 2026-09-15 finding that the field is bulk-written.

**Not established: the drop from 361 to 191** on 2026-09-17 `[RUN LOG]`. That run's postings were discarded with the runner. No combination of whole roles open on 2026-09-16 sums to the 170 lost, so rotation or new roles must be part of it `[BELIEVED]`. After the push, the first production run's raw file answers it at no extra request.

**What this means for the board list**, which is the operator's decision:

- Speechify costs one request per run.
- It has produced zero kept rows in every run.
- Its location rotation adds new raw rows at about 18 a day on this measurement (88 in 4.96 days), each appended to the public raw layer for good. That also bears on ADR-0003's unmeasured "20 to 50 new postings a day": this one board supplies about 18 of them with rows nobody will see.

## 5. Material prepared for the operator's decisions

`data/reports/title-pool-review-2026-09-17.md`. It is local and gitignored `[VERIFIED]` by `git check-ignore`, 559 lines. It holds:

1. each of the 50 pool terms with credited and total matches;
2. the 19 kept postings with employer, location and term;
3. all 444 distinct dropped titles, from 897 postings, with counts and boards;
4. CodeRoad's kept rows and Speechify's roles.

`[VERIFIED]` it reproduces the vertical-slice log's figures: 19 kept, 10 terms credited, 40 not. **New detail:** 39 terms match nothing at all. `mlops` matches one posting that the earlier term `machine learning` is credited with.

**New detail on CodeRoad:** one of its six kept rows, "AI Solutions Architect", is located in the United States, so the registry's "Latin America only" is not exact.

## 6. A defect my own report file exposed

**Writing that review file as markdown under `data/` halted `tools/generate_map.py`**, and with it the pre-commit hook's map gate. The generator walks every `*.md` in the tree and skipped only a fixed set of directories; `data/` was not among them, although git ignores it. `[VERIFIED]` the failure message: "map: data/reports/title-pool-review-2026-09-17.md: needs 'type' and 'description' in frontmatter". `data` and `raw_responses`, both gitignored working data, are now in `SKIP_DIRS`. The fix was proven by reverting it in memory and rerunning `--check`, which failed with the same message, then restoring it: the map regenerated at 49 files and the check passed. Any markdown the pipeline or a session writes under `data/` would have done the same.

## 7. Noticed, not acted on

- **GitHub disables scheduled workflows in a public repository after 60 days without repository activity.** `[VERIFIED]` quoted from docs.github.com, "Disable and enable workflows". Whether the pipeline's own data-branch pushes count as activity is unknown. **This is not new:** `docs/architecture-2.0.md:406` already lists it as a risk, noting that the operator's LinkedIn pipeline "has run over 100 consecutive times on bot commits alone". This log's index row calls it raised; it was already known, and the quote only confirms the mechanism. Found after the row was committed; the row is left as written, per the index's rules.
- **The handoff's and the slice log's reason for having no location filter is wrong for this pipeline.** Both say the geocoder writes "Karachi, Punjab, Pakistan". That comes from `docs/architecture-2.0.md:408`, about harvested data. `[VERIFIED]` no stored row contains it, and the Careem role reads "Karachi, Pakistan; Lahore, Pakistan". The slice log carries a dated correction.
- **GitHub's documentation on manual runs** `[VERIFIED]`: "To trigger the `workflow_dispatch` event, your workflow must be in the default branch", and the run's branch is chosen from a Branch dropdown. The disabling page says a disabled workflow is stopped "from being triggered" and does not say whether that includes manual runs.
- **`docs/architecture-2.0.md:302`** still reads "1 could not start". CLAUDE.md now gives exit 1 two causes. CLAUDE.md outranks it, so this is a stale line, not a conflict.
- **ADR-0023:76** says of STATE.md's staleness controls that "neither is a gate yet". Gate 4 of the pre-commit hook has been one since 2026-09-11. A factual correction for a dated annotation.
- **ADR-0023 never calls STATE.md "ground truth"** `[VERIFIED]` by grep, so the verify-do-not-trust rule conflicts with no record.

## Rejected alternatives

- **Restyling every em-dash in the repository.** Five are placeholders, four are functional or test data, and 44 are in records an implementing session does not restyle.
- **A live Speechify request** to see the 191. The protocol puts request spend with the operator, and the first pushed run answers it for nothing.
- **A suggested ceiling in the reader's output.** ADR-0028 says the margin is decided and recorded with its basis.
- **Treating `refused > 0` as a ceiling hit.** It also counts circuit refusals.

## Not done

- Nothing pushed; nothing run on GitHub.
- The Node 20 annotation is not shown to be gone.
- The reader has not read a production data branch, because none exists.
- Speechify's 361 to 191 is not explained.
- No decision record written or edited.
