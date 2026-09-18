---
status: accepted
topic: practice
description: Auto Memory ranks below every document in this repository and nothing is designed around it.
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0025: Auto Memory is not authoritative

## Context and Problem Statement

Claude Code writes notes to itself across sessions. Enabled by default since v2.1.59. They live at `~/.claude/projects/<working-directory>/memory/`, **outside any repository**, and are injected into the session's system prompt.

Research pass 0004 established the properties that matter here.

Not git-tracked, not reviewable in a pull request, not versioned with the code, not portable to another agent. `MEMORY.md` caps at 200 lines or 25 KB and **silently truncates** past that. It cannot currently be disabled; there is an open request for a switch. Consolidation fires only after roughly 24 hours *and* at least five new sessions, so a fact learned today may not be reconciled for a week.

It is keyed by **working directory, not repository root.** One reported case had a session for one project receive facts about three unrelated projects in its system prompt, and act on a fact belonging to a different one.

ADR-0022 lists seven levels of document authority and does not mention it. So the one input a session cannot inspect currently has no stated rank.

## Decision Drivers

- The project's governing principle is that no fact should live in two places and that anything load-bearing must be gated. This is a second place, and it is ungated.
- A session cannot show the operator what Auto Memory told it, so a claim sourced from it cannot be checked.
- It cannot be turned off, so a decision to "not use it" is unenforceable.

## Assumptions

- The cross-project contamination behaviour still exists as reported. Based on a GitHub issue, not reproduced here.
- Launching from the repository root keeps its scope to this project. Follows from directory keying; not tested.
- Anthropic will eventually ship a switch. Speculation, and nothing here depends on it.

## Considered Options

- Ignore it. Say nothing.
- Attempt to neutralise it by writing over its store.
- Rank it explicitly and design nothing around it.

## Decision Outcome

Chosen option: "rank it explicitly and design nothing around it".

**Auto Memory ranks below everything in the repository.** It sits beneath level 7 of ADR-0022's authority order, below even the superseded architecture document. Where it disagrees with any repository file, the repository file wins, without exception.

**Nothing in this project is designed around it.** No artifact assumes it holds a fact and none delegates to it. `STATE.md` and the log index exist partly because it cannot serve as either.

**A session that acts on something it did not read from a repository file says so.** If a claim's only source is Auto Memory, that is stated as its source, so the operator can tell an unverifiable claim from a checkable one.

**Claude Code is launched from the repository root**, not from a subdirectory or a parent. Directory keying is what causes cross-project contamination, so a consistent working directory is the only mitigation available.

We will not attempt to neutralise or overwrite its store. Fighting a tool over a directory it owns produces undefined behaviour, and the cost of ignoring it is already bounded by ranking it last.

### Consequences

The unreviewable input has a stated rank, so a conflict has an answer rather than an arbitrary outcome.

A claim with no repository source becomes visible as such, which is the only defence available against a store that cannot be inspected.

Auto Memory keeps consuming context in every session, unmeasured. Nothing here changes that.

Its 200-line silent truncation means facts it holds may vanish without notice. Since nothing depends on it, that costs nothing here. For a project that did depend on it, it would be severe.

Launch discipline is a habit, not a gate. It cannot be enforced by a hook, because the hook runs inside the repository and cannot know how the session was started.

If a switch to disable it ships, this record is revisited. Disabling would be simpler than ranking.

### Confirmation

Ask a session a question about this project whose answer exists only in a repository file, and confirm it names the file. A session that answers from memory without naming a source has produced an unverifiable claim, and this record has failed in practice even though it holds on paper.

## Pros and Cons of the Options

### Ignore it

Good, because it needs no writing.
Bad, because the ungated input still feeds every session, and a conflict would be resolved arbitrarily and invisibly.

### Neutralise it

Bad, because there is no supported way to do it, and writing into a directory the tool owns risks undefined behaviour for no gain over ranking it last.

## More Information

Extends ADR-0022, which stated seven levels of authority without addressing inputs from outside the repository.

Evidence, including the truncation limit, the consolidation gate and the contamination report, is in `docs/research/0004-project-context-documentation.md`.
