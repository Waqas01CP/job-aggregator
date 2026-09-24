---
type: instruction
description: How to work in this repository. Scope floor, conventions, commands. Read before touching anything.
status: current
---

# CLAUDE.md

A scheduled pipeline that polls employer ATS job boards, filters the results
against fixed rules, and writes what survives to a table for review.

**The vertical slice is built.** `STATE.md` says what exists, what has run,
and what is blocked.

## Reading order

Read these four, in this order, then stop and follow pointers. Do not read the
documented file set.

1. **This file.** How to work here.
2. **`STATE.md`.** What exists, what is blocked, and where the proof is. It is
   where you start, not where you stop. It outranks memory: "I remember this
   was pending" is not evidence. It does not outrank the code or the data:
   where a row disagrees with them, the row is stale. Report it and correct
   it. See "Verify, do not trust" below.
3. **`logs/README.md`.** What prior sessions did. When you need more, read the
   most recent relevant log; it references the one before it; chain backwards
   only as far as you need and stop when you have enough.
4. **`MAP.md`**. **The navigation index for every documented file in this
   repository.** It names each one, what it holds, and what kind of answer it
   gives. **Read it before searching the tree.** Grepping for a file whose
   purpose this index already states is the slowest way to find anything here,
   and it is what every session that skipped this line has done.

**Then `docs/how-to/the-seats.md`, once, before your first action of the
session.** Four seats work on this project and it says what each may and may
not do, including what this one may not. It is the only document here that no
command can verify, so it carries its own checks and the date they last ran.

Then the brief for your task.

`MAP.md` is generated. Never edit it by hand. Edit the source file's frontmatter
and regenerate.

## When documents disagree

Two questions, two orders.

**What is true**, what exists and what happened: the code and the data win
over every document. A document that disagrees is stale. Report it and
correct it. ADR-RULES.

**What should be done**: higher wins. ADR-0022, ADR-0025, ADR-RULES.

1. The operator's instruction in this conversation
2. This file
3. `docs/decisions/`, excluding anything marked superseded
4. The brief for your task. It ranks below this file and every accepted
   record: where it contradicts one, follow the record and report it. It
   overrides a record only when it names the record and clause and states
   that the operator approved the change; it then carries rank 1.
5. `docs/architecture-2.0.md`
6. `docs/reference/`
7. `docs/research/`, evidence for decisions, never a decision
8. Everything else, including `docs/architecture.md`, which is superseded
   and must never be implemented from
9. Anything from outside this repository, including your own Auto Memory

Two unsuperseded records that conflict is a defect. Raise it. Do not choose.

If your only source for a claim is something outside this repository, say so.
A claim the operator cannot check is different from one they can.

## Scope floor

These are decided. Do not propose them, do not add them as robustness
improvements, do not reintroduce them in a refactor.

- **No scoring, ranking, or model-based classification of any posting.** Every
  posting is admitted or dropped by a deterministic rule that can be named.
  ADR-0010.
- **No user interface**, dashboard or web app. Operator's standing decision;
  no record.
- **No notification system.** The operator opens a table. Operator's standing
  decision; no record.
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

**Writing to a display service is not fetch behaviour.** ADR-0034 gives
Airtable its own client: different verb, authentication, budget, rate limit
and failure semantics. Retry, backoff and circuit breaking stay shared, as
utilities both import, because that is what the rule above is protecting.
Fetching a job board has no exception and never gets one.

**Read only the fields consumed.** Ignore everything else, so a board adding a
field never breaks anything.

**Align by key, never by position.** Fall back to position only when counts
agree exactly. Refuse to store when both fail.

**Classify errors on status codes, never on substrings of a message.**

**Atomic writes.** Write to `.tmp`, then rename. When moving data between
stores, write to the destination before deleting from the source.

**One canonical serialisation per file.** Every writer of a file agrees on it,
so a run that changes nothing produces a diff containing nothing.

**Three exit codes.** 0 finished, 1 failed, 2 stopped deliberately and
resumable. The orchestrator treats 2 as non-fatal. Exit 1 has two causes, a
run that could not start and a run that fetched but could not store the
result, and the run's own output says which. Run 35179218050 was the second
kind and was reported as the first. **A failed projection to Airtable exits
2, not 1**: the fetch is committed, the run log records the failure, and the
next run re-projects the whole layer. Exit 1 would stop the push and lose the
fetch for a display failure. The operator's decision, 2026-09-23, in
ADR-0034's Changes. **So does a private store that cannot be restored or
written** (ADR-0047): the public fetch is committed, and when the restore
failed the aggregator boards are not polled, since nothing they returned
could be kept. The operator's decision, 2026-09-24, in ADR-0047's Changes.
**On the third failure of either in a row** the run still
commits and the workflow still pushes, and only then does the workflow's last
step mark the run failed, so a failure that repeats cannot look healthy and
marking it can never cost data. The operator's decision, 2026-09-24.

**Log per board every run, including zero.** A board returning nothing for a
week is a broken adapter. Without a zero logged it looks like a quiet market.

**Dates are UTC, and schedules are reasoned about in UTC.** This machine runs
at UTC+5, so for five hours of every day its local date is already tomorrow's.
A session dated its log and its handoff 2026-09-18 from the local clock while
UTC was still the 17th, and sent the next session to look for a scheduled run
that could not have fired yet. Date logs in UTC, read `cron` in UTC, and when
a local date differs from the UTC one, say which is which.

## Verification

**Verify, do not trust.** Every claim is unverified until you have checked it
in this session. That covers briefs, handoffs, logs, `STATE.md`, decision
records, anything pasted from another session, anything from outside this
repository, and your own earlier conclusions. A wrong claim accepted once gets
built on, and every later session inherits it. A handoff once stated that a
`test_mode` workflow run would not touch production data. It would have: the
workflow never passed `--no-commit`, and test-mode files mapped onto
production paths of the same branch. Reading the code caught it.

- **Check before you act.** A claim you are about to build on gets a command,
  a file read or a test first. Cheap checks happen now, not later.
- **A claim you cannot check**, because it needs the network, credentials or
  the operator, is marked unverified and is not acted on as though true.
- **A claim that fails its check is reported** with the evidence. Never
  corrected quietly, never acted on in its unchecked form.
- **Where a document's account of what exists or what happened disagrees with
  the code or the data, the code and the data win.** Report the document as
  stale. This is a different axis from the authority order above, which
  settles documents against documents.
- **Tag what you pass on**: checked this session, taken from a log, or
  inferred, so the next reader knows what to re-check.

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

**An accepted record's decision is never silently rewritten.** A change
that leaves it in force (one clause reversed, something added, a fact or
reference corrected) is annotated with its date and logged in the record's
Changes table. A change that replaces the decision, or more than half its
Decision Outcome, is a new record that supersedes it, both directions
linked. ADR-RULES says what a seat may correct without asking.

**Every unmeasured number goes in Assumptions**, with what it is based on.

## Documentation layering

System-level and overall picture go in `docs/`. Component-level detail goes in
comments inside the file it describes. Integration detail splits between them.

A comment explaining why a guard exists and what the incident cost is
documentation. A comment restating the next line is noise.

## Commands

```
python -m venv .venv                   create the environment, once per clone
.venv/Scripts/python -m pip install -r requirements.txt     Windows
.venv/bin/python -m pip install -r requirements.txt         Linux and macOS

.venv\Scripts\activate                 activate, PowerShell or cmd
source .venv/Scripts/activate          activate, git bash on Windows
source .venv/bin/activate              activate, Linux and macOS
deactivate                             leave it

.venv/Scripts/python -m unittest discover -s tests -t .     run every test
.venv/Scripts/python -m src.run --test-mode --no-commit     one run, alternate
                                                            files, no commit
.venv/Scripts/python -m src.contract --test-mode --no-commit
                                       one contract check (ADR-0018), three
                                       requests, no commit

python tools/generate_map.py           regenerate MAP.md
python tools/generate_map.py --check   report whether MAP.md is current
git config core.hooksPath .githooks    enable the hook, once per clone
```

**Changing Python version is a rebuild, not a migration.** Delete `.venv`,
make a new one on the interpreter you want, reinstall. Nothing else in the
repository is tied to a version:

```
rm -rf .venv                           or Remove-Item -Recurse -Force .venv
py -3.13 -m venv .venv                 Windows, a specific version
python3.13 -m venv .venv               Linux and macOS
.venv/Scripts/python -m pip install -r requirements.txt
```

The suite has been run on 3.11 and 3.12 and passes identically on both.
The scheduled workflow pins 3.11, so that is the version the pipeline
actually runs on; a local venv on a newer one is fine for development but
is not what ships.

**Never install this project's dependency outside a venv.** A global
`pip install requests` makes the dependency invisible to anyone cloning the
repository and leaves an unactivated shell silently using it. This happened
once and was undone.

**Activating is optional.** The commands above name the interpreter inside
`.venv` explicitly, which works from any shell without activating and cannot
pick up the system Python by accident. Activating only puts that interpreter
on `PATH` for the current shell, so `python` means the venv's one. Use whichever
you prefer; the explicit form is what this file documents because it is
unambiguous in a log or a bug report. If PowerShell refuses the activation
script, that is its execution policy, and the explicit form sidesteps it.

Everything a run writes lives under `data/`, which is gitignored: the raw
layers, the filtered layer, the seen store and the run logs. A `--test-mode`
run writes the same shapes under `data/test/`. The paths inside the orphan
data branch are ADR-0020's and are not affected by where the working copies
sit.

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
