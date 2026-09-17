---
status: accepted
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0023: Context artifact set and onboarding order

## Context and Problem Statement

A fresh session is currently told to read `CLAUDE.md`, then `MAP.md`, then, implicitly, every one of the twenty-nine documented files. That count only grows.

Four things are missing. No document states what actually exists versus what is designed. No document states what is blocked and on whom. No document carries the project's trajectory. And there is no defined reading order, so "understand the project" means "read everything."

Three research passes surveyed the published practice. The evidence cut against adding artifacts: one study across 2,303 context files found they evolve like configuration code through frequent small additions and become difficult to read; another found context files did not generally improve task success while costing over 20% more tokens, with repository overviews specifically unhelpful.

Research pass 0004 then found the operator's prior project had already solved most of it, with two state artifacts split by how often they change, an indexed log directory with a chain-reading rule, and a reading order stated in its execution contract.

Separately: Claude Code's Auto Memory is enabled by default and writes to a directory outside the repository, untracked, ungated, silently truncating at 200 lines, and keyed by working directory rather than repository root.

## Decision Drivers

- The reading cost of onboarding must stop growing with the file count.
- Every added artifact is a maintenance liability carried by one person.
- Anything derivable should be generated and gated, per the project's governing principle.
- State and history change at completely different rates.

## Assumptions

- Two state artifacts are not needed until work is in flight. This project has none yet, so the in-flight register is deferred rather than rejected.
- The chain-reading rule scales here as it did on a 250-log project. Not measured at this project's scale, which is currently zero logs.
- Auto Memory will not be relied on. It cannot be inspected or gated, so nothing is designed around it.

## Considered Options

- Add nothing. Rely on `MAP.md` and the records.
- Add a state file, a trajectory file, a history file, and per-folder overview files.
- Add a state file and an indexed log directory, and generate or defer everything else.

## Decision Outcome

Chosen option: "a state file and an indexed log directory, generate or defer the rest".

**`STATE.md` at the repository root.** Organised by task, not by session, because logs are chronological and one task spans many entries. One row per task: status, date, and a pointer to where the proof lives. Status is one of DONE, PARTIAL, PENDING. A row reads DONE only when the thing is built, never when it has merely been examined.

Every row carries `[VERIFIED]` or `[BELIEVED]`. Verified means exercised and observed. Believed means reasoned from the code but not run. **Unmarked defaults to believed**, so the weak set is always visible rather than hidden.

Pointers are commits, decision records, or log filenames. Never file paths, which move.

It is updated in the same commit as the work, never in a separate bookkeeping pass. A commit that completes a task without updating its row is incomplete.

It carries a header stating the commit it was last verified against.

**`logs/` with `logs/README.md` as its index.** One log per session. The index is a thin append-only table, one row per log: what was done, what changed, what the outcome was. No prose, no reasoning in the index; that lives in the log.

A session reading the index and needing more reads the most recent relevant log, which references its predecessor, and chains backwards only as far as needed. **This is what keeps onboarding cost flat as the log count grows.**

Log format is ADR-0024.

**Onboarding order, stated in `CLAUDE.md`:** `CLAUDE.md`, then `STATE.md`, then `logs/README.md`, then `MAP.md` on demand, then the task's own brief. A session does not read the documented file set; it reads four files and follows pointers.

**Deferred, not rejected:** an in-flight register separate from `STATE.md`, wanted once work is genuinely in flight and held defects exist.

**Confirmed open, not deferred:** an end-state document. The operator's prior project was checked for prior art and has none. `SPRINT_PLAN.md` is a task breakdown with per-person assignments, gates and a deadline, which is a plan rather than a statement of what the finished system is. No artifact in either project says what this is ultimately for. That gap is real and stays open until it is decided deliberately.

**Rejected:** hand-written per-folder overview files, which duplicate the generated map and drift. A separate history document, since history is the records plus the log index. `llms.txt`, a web-publishing convention with around 10% adoption that crawlers largely do not request. Repository-packaging tools, since the agent has filesystem access and `MAP.md` already routes. Reorganising documentation into Diataxis folders, since the frontmatter `type` field already carries that distinction.

### Consequences

Onboarding is four files and a pointer-following rule, rather than a file count that grows forever.

Two new hand-maintained artifacts exist. Both have a same-commit rule and both are cheap to check.

`STATE.md` is not generated and therefore can drift. The verified-against header makes drift visible; the same-commit rule is what prevents it; neither is a gate yet. *(Annotated 2026-09-17: out of date. The same-commit rule has been a gate since commit `7b5633e`, dated 2026-09-15; see Changes.)*

The `[VERIFIED]` and `[BELIEVED]` split means the state file is honest about its own confidence, which a plain checklist cannot be.

Auto Memory continues running outside all of this. Nothing here controls it, and any fact it holds is unreviewable.

Trajectory remains uncovered. The prior project has no artifact for it either, so there is nothing to port. That is a known gap, not an oversight.

### Confirmation

Start a session with only the four onboarding files and a task brief, and confirm it can state what exists, what is blocked, and where to find the proof, without reading the remaining twenty-five documented files.

Separately: mark a row DONE without a pointer and confirm the omission is visible on reading. If it is not, the format has failed.

## Pros and Cons of the Options

### Add nothing

Good, because it adds no maintenance and the evidence says extra context files rarely help.
Bad, because the studies measured one-shot issue resolution, not multi-session continuity, which is the entire problem here and the one thing they did not test.

### State, trajectory, history, and per-folder overviews

Bad, because history duplicates the records and the git log, per-folder overviews duplicate the generated map, and four hand-maintained artifacts on a solo project is how documentation systems die.

## More Information

Every element of the state file and the log index is adapted from the operator's prior project, `fyp-career-guidance`. Evidence, the wider survey, and the corrections this pass made to its own earlier findings are in `docs/research/0004-project-context-documentation.md`.

Reading order is authoritative per ADR-0022. Log format is ADR-0024.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-11 | The end-state document moved from deferred-pending-a-read to confirmed open | `SPRINT_PLAN.md` was read. It is a task plan, not a statement of the finished system, so there is no prior art to port and the gap is real |
| 2026-09-17 | Factual correction, not a change of decision: the Consequences sentence saying the same-commit rule is not a gate yet | Gate 4 of `.githooks/pre-commit`, added in commit `7b5633e` (author date 2026-09-15), blocks a commit that stages implementation paths without `STATE.md`. `STATE.md` records it as proven to fire. The verified-against header is still not gated |
