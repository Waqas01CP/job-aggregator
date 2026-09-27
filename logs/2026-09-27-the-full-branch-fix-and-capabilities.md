---
type: log
description: The first two runs with full postings and Himalayas' search endpoint read back; the second full save's failure on GitHub reproduced and fixed the same morning, with the unsaved postings recovered by the next walk; and CAPABILITIES.md drafted for the operator's approval.
status: current
---

# The full branch fixed, the first search morning, and CAPABILITIES.md, 2026-09-27 UTC

Previous log: `2026-09-26-the-third-audit-and-the-first-scheduled-sweep.md`.

| Header | Value |
|---|---|
| Date | 2026-09-27 UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `65c70e3`, level with `origin/main` |
| Mode | **Mutating.** No job board contacted; nothing written to Airtable. The `data` branch read from a scratch clone |
| Tests | 663 at start, 666 at end, on Python 3.12 and 3.11 |
| Verification | 3 of 3 mutations caught |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## The two runs since the last log

Read from their committed logs in a scratch clone of `data` at `5add66a` `[VERIFIED]`.

**The evening run of 2026-09-26, 16:56Z**, on `2710cb2`, before the catch-up was pushed:
- **D11's first save on GitHub held.** 824 postings in `full/20260926T165604.546134Z.json`, 9,769,591 bytes, read back and matched: `verified: true`. The token may create the branch.
- Himalayas was skipped, as on every evening run: 11 requests.
- **The first quiet evening's copy-only sweep cost 2 calls.** Part 2 of the architecture brief listed it as unmeasured. The projection sent 17 groups.

**The morning run of 2026-09-27, 03:59Z**, on `65c70e3`, the first search morning:
- **The catch-up held.** `himalayas:pakistan` read 23 pages, 460 postings, and stopped on the page past the age limit, well inside the cap of 40. 361 were new and 31 kept. Drops: 404 title, 23 seniority, 2 age, 0 location.
- **What browse had stored was not new.** 99 of the 460 were already stored, as the guid check of 2026-09-26 predicted, so none was admitted twice.
- **The sweep's step 6 stored 25 public rows the rules no longer admit**, in `removed_unreviewed.json`. The next daily sweep deletes them once the store reads them back.
- `Jobs` holds 126 rows; the month stands at 100 calls, 10%. The run spent 34 requests.
- **The full save failed, and the run was marked failed at once** (D9), after its push. The public data and the aggregator files were pushed; only the full postings were not. The failure, verbatim, scrubbed by the run:

  > PrivateStoreUnreachable: the private store failed while writing the full branch's tree (git exit 128): fatal: could not read Username for 'https://github.com': terminal prompts disabled / fatal: could not fetch f55779cd... from promisor remote

- Because the private store counted as failed, the sweep held 81 private rows (`held_private_unavailable`). They wait for the next morning whose save succeeds.

## The failure: cause, reproduction, fix

**Cause** `[VERIFIED]`, reproduced below. The full branch is fetched without file contents, a partial fetch, so the earlier run's file is absent by design. `git write-tree` checks that every file in the tree exists. Finding last night's file missing, git tried to download it on demand. That download carries no token, because only the fetch and push commands are given one, so GitHub refused it. The first save worked because the branch was empty.

**Why the tests passed.**
- `[VERIFIED]` The local repository standing in for GitHub never honoured a partial fetch: `uploadpack.allowFilter` was unset, so git quietly fetched every file. The two-save test then passed on a full fetch.
- `[INFERRED]` The seat's probe of 2026-09-26 did see a partial fetch (270 KB as 1.4 KB). But over a local file URL the on-demand download needs no token, so it would have succeeded silently.

**Reproduced** `[VERIFIED]`. The full-branch tests now use a stand-in that honours partial fetches, and every command of a save runs with on-demand downloads refused (`GIT_NO_LAZY_FETCH=1`). With `write-tree` as it was, the new test fails "while writing the full branch's tree (git exit 128)": the runner's step and exit code. The test also checks that the earlier file really is absent, so it cannot pass on a full fetch as its predecessor did.

**Fixed:**
- `write-tree --missing-ok`. The tree names earlier files by hash alone, which the partial fetch brings.
- On-demand downloads refused for the whole save, so any command that needs one fails in the tests, not on a runner.

**Recovery of what was not saved.** The 460 Himalayas postings of this morning's run are stored as rows but not in full. An ATS posting is saved by the next run that still lists it, but a Himalayas walk would stop before reaching them. **So only a posting saved in full now sets a board's stop mark.** None of this morning's is saved, so the next morning's walk reads back to the age limit again, about 23 pages, and saves them all. After that the mark is set and walks are short. ATS postings still pending are saved by tonight's run.

**Tests**, each built to fail without its part:
- a later save never needs an earlier file's contents, on a real partial fetch;
- no command of a save may download on demand;
- a posting not saved in full is walked to again, is offered for saving, and is not new; once saved, the walk stops.

Two Himalayas tests now mark their postings saved between runs, as `main()` does after a verified save.

## CAPABILITIES.md, drafted and held

The operator asked for one file that stands in for the whole repository, for any reader and for a chat drafting his CV. His answers: at the root, committed, role-neutral, kept current, personal details included. The section on his role is held for his approval, and nothing is committed until he gives it. Its numbers were measured this session from the scratch clone of `data`:
- **Freshness:** 89 new ATS postings first seen a median of 5.0 hours after publication; the 90th percentile 10.0 hours, the maximum 13.4.
- **Reliability:** 22 production runs with 0 retries and 0 failed requests.

## Found and not fixed

- **`README.md` is stale.** It says the review table is not built and gives the schedule as 00:00 and 13:00 UTC; runs start three to four hours after those times. For the operator.

## Not done

- The older mutation files whose code this fix touches (D11, the private store, the catch-up, search) are re-run after the push, in a scratch clone; their results follow in the next commit.
- Tonight's run, about 17:00Z, is the fix's first live proof. The next morning's walk is the recovery's.
