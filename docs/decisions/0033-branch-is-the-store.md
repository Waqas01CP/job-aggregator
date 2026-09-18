---
status: accepted
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0033: The data branch is the store, local files are working copies

## Context and Problem Statement

The schedule runs on a GitHub runner that is created and destroyed for each run. Nothing on its filesystem survives. The pipeline's state, which is the raw layer, the filtered layer and the seen store, therefore cannot live on the machine that produces it.

The first scheduled run, 35179218050, demonstrated the consequence. It fetched 1239 postings against an empty seen store, judged every one of them new, and then failed before committing. A run that starts from nothing cannot tell a new posting from one it recorded yesterday.

Three implementation choices resolved this and none of them is recorded. They are load-bearing: a later session that reverses any of them reintroduces the failure.

## Decision Drivers

- The seen store decides what is new. If it is empty at the start of a run, every posting is new and both the raw layer and Measure A become meaningless.
- A run must not depend on anything left behind by a previous run on the same machine, because there is no same machine.
- A test run must be incapable of corrupting production state, and "incapable" must not rest on remembering to pass a flag.
- Local exploration should not require the network.

## Assumptions

- A depth-1 fetch of the data branch is enough to restore state. **Measured**: scheduled run 35253312417 fetched the existing branch at depth 1, restored, appended and fast-forwarded, and run 1's records and first-seen dates were unchanged.
- The branch stays small enough to fetch every run. **Measured** at 804 postings and two run logs; ADR-0003's append-delta rule is what keeps this true.

## Considered Options

- Local files as the store, with the branch as a backup.
- The branch as the store, restored at the start of every run.
- The branch as the store, restored only when a run intends to commit.

## Decision Outcome

Chosen option: "the branch as the store, restored only when a run intends to commit". Three invariants, all currently implemented:

**1. The data branch is the store. Local files are working copies.** A committing run replaces its local copies with the branch's contents before it fetches anything. A `--no-commit` run does not, so local exploration chains from local files and needs no network. This is the invariant that makes a discarded runner safe, and reversing it reproduces run 35179218050's behaviour exactly.

**2. Aggregator data never reaches the branch, and has its own paths.** Raw aggregator rows go to `fetch-all-local/`, their filtered rows and seen-store entries to `local/`, beside the committed `fetch-all/`, `filtered.json` and `seen.json`. ADR-0020 decides that aggregator rows are not published; this records where they go instead. The separate directory names exist so that a routing bug misfiles nothing: a row's provenance is its filename.

**3. A test run commits to `data-test`, which carries the production layout inside it.** Test mode selects the branch, and the paths inside that branch are unchanged. So a test run exercises the real layout, and no test run can write production's branch. The alternative, test files sharing a branch under different names, was what made an earlier handoff's claim that test mode "would not touch production data" false.

### Consequences

Every committing run pays one branch fetch. Measured at depth 1 it is negligible against the 36 requests a run spends on boards.

A run that cannot reach the branch must fail rather than proceed, because proceeding means treating every posting as new. Exit 1 covers this, with the run naming which of its two causes applies.

`--no-commit` runs can diverge from the branch, which is the point, and their output is not evidence about production state.

Aggregator history exists only where a run was executed. On a runner that means it does not persist at all, which is a live question for the architecture chat and is not settled here.

Two branches exist publicly, `data` and `data-test`, and `data-test` accumulates whatever tests have been run.

### Confirmation

Simulate a run against a local bare repository with the network replaced: a committing run must read the branch's seen store before its first fetch, and a `--no-commit` run must not. Both have been exercised this way.

The check that can fail: run the committing path twice over identical board output. The second run must write nothing and leave every file byte-identical. If it writes, the restore did not happen or the seen store did not survive it.

For invariant 3, run in test mode and confirm `data` is untouched at the commit that preceded the run. Run 35239033514 did this on GitHub: `data-test` was created and `data` stayed at `272cfdb`.

## Pros and Cons of the Options

### Local files as the store

Good, because it needs no fetch and is what a developer expects.
Bad, because on a runner there are no local files, which is not an edge case but every scheduled run.

### Restore on every run, including `--no-commit`

Good, because there is one code path and no mode to reason about.
Bad, because local exploration then depends on the network and on whatever production last wrote, which makes two consecutive local runs impossible to reason about.

## More Information

Answers question 5 of the 2026-09-17 architecture brief in full.

ADR-0020 decides the routing these paths implement. ADR-0003 is why the branch stays fetchable. ADR-0006 sets the cadence that makes a discarded runner the normal case.

The five defects that produced these invariants are recorded in `2026-09-17-runner-safe-data-branch.md`.
