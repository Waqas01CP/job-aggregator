---
type: log
description: The first successful scheduled run, which proved on GitHub that a run restores from the data branch, appends, and pushes on top; the first publication-lag evidence; and a question for the display about rows kept under older rules.
status: current
---

# The first scheduled run, 2026-09-17

Previous log: `2026-09-17-families-seniority-and-trials.md`. Found while committing that work: the operator had pushed `be99ff8` and `bac377c` (`git reflog` on `origin/main` shows "update by push"), and the production `data` branch had moved from `272cfdb` to `91f7518`.

| Header | Value |
|---|---|
| Date | 2026-09-17 |
| Model | claude-opus-5 |
| HEAD | `ffccf8f`, one commit ahead of `origin/main` at `bac377c` |
| Mode | **Read-only against GitHub.** Public Actions API and a fetch of `data` into a scratch clone |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means believed.

## The run

`[VERIFIED]` run 35253312417, event `schedule`, created 2026-09-17T17:31:57Z, head `bac377c`. That is the 13:00 UTC slot, 4.5 hours late. Every step succeeded, including "Fetch the data branch"; no annotations. It is the first successful scheduled run, and the first run of any kind to find an existing branch.

## What it proves

`[VERIFIED]` by comparing the branch's two commits in a scratch clone:

- **History continues.** `91f7518`'s parent is `272cfdb`, both by `job-aggregator <job-aggregator@invalid>`. So the depth-1 fetch of an existing branch works on GitHub, the run committed on top of it, and the push fast-forwarded.
- **The state was restored and appended to, not replaced.**

  | File | Run 1 | Run 2 | Run 1's records unchanged and first in run 2 |
  |---|---|---|---|
  | `fetch-all/greenhouse.json` | 759 | 766 | yes |
  | `fetch-all/lever.json` | 37 | 38 | yes |
  | `filtered.json` | 21 | 24 | yes |

  Every run-1 identity kept its `first_seen` in `seen.json`, which grew from 796 to 804.
- **Only new postings were written.** 508 of 1303 fetched were new: 7 Greenhouse, 1 Lever, and Himalayas' 500.

These close the last GitHub-side unknowns listed in STATE.md: fetching an existing branch, the restore, and a fast-forward push after a depth-1 fetch. `DATA_BRANCH` had already resolved both ways.

## Requests

`[VERIFIED]` `tools/run_log_report.py` on the branch: 2 runs, 36 requests each (Greenhouse 9, Lever 2, Himalayas 25). Greenhouse and Lever were first contact on run 1 only. **Himalayas was first contact on both runs and is flagged "every run"**, as predicted: a runner keeps none of its state, so it pages to the cap each time. Steady state for the employer boards is 11 requests per run.

## First publication-lag evidence

`[VERIFIED]` `tools/publication_lag_report.py` on the branch: of postings first seen in run 2, Greenhouse 7 of 7 and Lever 1 of 1 are dated after run 1; none is dated at or before it.

It is consistent with ADR-0006's near-zero propagation, and with Lever's `createdAt` meaning publication. One Lever posting is not proof, and the report concludes nothing.

## New kept rows

`[VERIFIED]` the three rows run 2 added to `filtered.json`, under pool version 2:

- Joblogic, "AI Evaluation Engineer", Pakistan;
- Joblogic, "MLOps Engineer", Pakistan;
- Motive, "Senior Program Manager, AI Ops (GTM)", United States, remote.

The two Joblogic roles are the pipeline doing its job. The Motive role is a go-to-market program manager admitted by `ai ops`, which the seniority rule would drop.

## A question this raises for the display

`filtered.json` is append-only (ADR-0003). Rows kept before the seniority rule existed stay in it once that rule is pushed: 11 so far, the ten senior rows of run 1 and this Motive row. The rule applies only to postings new from then on.

The Airtable writer is not built. It will have to decide whether its projection re-applies the current rules to the filtered file or copies it as it stands. ADR-0013 calls Airtable "a projection of that file", which reads as the latter. This is raised for the architecture chat rather than decided here.

## Not done

- Nothing written to GitHub from this session.
- `ffccf8f` is not pushed, so GitHub still runs pool version 2 without the seniority rule.
