---
type: instruction
description: How to work in this repository. Scope floor, conventions, commands. Read before touching anything.
status: current
---

# CLAUDE.md

A scheduled pipeline that polls employer ATS job boards, filters the results
against fixed rules, and writes what survives to a table for review.

**Nothing is built yet.** Documentation only.

## Reading order

Read these four, in this order, then stop and follow pointers. Do not read the
documented file set.

1. **This file.** How to work here.
2. **`STATE.md`.** What exists, what is blocked, and where the proof is. It is
   ground truth, not memory. If it says done, it is done. "I remember this was
   pending" is not evidence.
3. **`logs/README.md`.** What prior sessions did. When you need more, read the
   most recent relevant log; it references the one before it; chain backwards
   only as far as you need and stop when you have enough.
4. **`MAP.md`**, on demand. Every documented file, what it holds, what kind of
   answer it gives.

Then the brief for your task.

`MAP.md` is generated. Never edit it by hand. Edit the source file's frontmatter
and regenerate.

## When documents disagree

Higher wins, without exception. ADR-0022.

1. The operator's instruction in this conversation
2. This file
3. `docs/decisions/`, excluding anything marked superseded
4. `docs/architecture-2.0.md`
5. `docs/reference/`
6. `docs/research/` — evidence for decisions, never a decision
7. Everything else, including `docs/architecture.md`, which is superseded and
   must never be implemented from
8. Anything from outside this repository, including your own Auto Memory

Two unsuperseded records that conflict is a defect. Raise it. Do not choose.

If your only source for a claim is something outside this repository, say so.
A claim the operator cannot check is different from one they can.

## Scope floor

These are decided. Do not propose them, do not add them as robustness
improvements, do not reintroduce them in a refactor.

- **No scoring, ranking, or model-based classification of any posting.** Every
  posting is admitted or dropped by a deterministic rule that can be named.
  ADR-0010.
- **No user interface**, dashboard or web app. ADR-0010.
- **No notification system.** The operator opens a table. ADR-0014.
- **No email or search-alert ingestion.** ADR-0012.
- **No paid services.** Free by default. Any spend is discussed first.

If a task appears to require one of these, stop and say so. Do not work around
it.

## Runtime

Python 3.11 or later. Standard library plus `requests`. No framework.

Dependencies are added by discussion, not by import. A new dependency needs a
reason that survives "the standard library can do this".

## Conventions

**Adapters are per ATS platform, never per employer.** Greenhouse is one
adapter serving nine boards.

**All fetch behaviour lives in one shared HTTP module.** Retry, backoff, budget
counting, circuit breaking. An adapter parses and nothing else. Copying retry
logic into an adapter is the specific failure this rule prevents.

**Read only the fields consumed.** Ignore everything else, so a board adding a
field never breaks anything.

**Align by key, never by position.** Fall back to position only when counts
agree exactly. Refuse to store when both fail.

**Classify errors on status codes, never on substrings of a message.**

**Atomic writes.** Write to `.tmp`, then rename. When moving data between
stores, write to the destination before deleting from the source.

**One canonical serialisation per file.** Every writer of a file agrees on it,
so a run that changes nothing produces a diff containing nothing.

**Three exit codes.** 0 finished, 1 could not start, 2 stopped deliberately and
resumable. The orchestrator treats 2 as non-fatal.

**Log per board every run, including zero.** A board returning nothing for a
week is a broken adapter. Without a zero logged it looks like a quiet market.

## Verification

**A check that cannot fail is worse than no check.** Prove a check by giving it
the case built to defeat it, and say what that case was.

**Self-report is not evidence.** Show the command and its output, not a claim
that it passed.

**Do not state a cause that has not been tested.** "The filter is dropping rows
because the location format differs" is a hypothesis until you have looked.

**Do not write about a file you have not opened.**

## Decision records

`docs/decisions/`, MADR 4.0.0 with an added Assumptions section.

**Write the record when the decision concludes, not afterwards.** A record
written later reconstructs its reasoning instead of committing to it.

**Never edit an accepted record to change a decision.** Write a new record that
supersedes it, and link both directions. A factual error may be corrected in
place with a dated annotation.

**Every unmeasured number goes in Assumptions**, with what it is based on.

## Documentation layering

System-level and overall picture go in `docs/`. Component-level detail goes in
comments inside the file it describes. Integration detail splits between them.

A comment explaining why a guard exists and what the incident cost is
documentation. A comment restating the next line is noise.

## Commands

```
python tools/generate_map.py           regenerate MAP.md
python tools/generate_map.py --check   report whether MAP.md is current
git config core.hooksPath .githooks    enable the hook, once per clone
```

## The hook blocks

Raw payloads (`.html`, `.eml`, `.har`), unsanitised test cassettes, Obsidian
double-bracket wikilinks, and a stale `MAP.md`. All four have been proven to
fire.

The wikilink pattern is deliberately not written out here. The hook greps for
it literally and has no notion of code fences, so this file would block its own
commit. That is the gate being stricter than the rule it enforces, which is the
right trade: teaching it to ignore backticks would create a documented bypass.

If the hook blocks you, read the reason. Do not bypass it with `--no-verify`.

## Writing

No em-dashes. Lead with the verdict. Active voice. Numbers carry their
provenance or they do not appear.
