---
type: how-to
description: The four seats that work on this project, what each may and may not do, how work moves between them, and the procedure for re-checking that this file is still true. Nothing in the repository can prove it, which is why it carries its own checks.
status: current
verified: 2026-09-22
---

# The four seats

**Four seats work on this project.** The operator, the architecture chat, the
implementing seat, and the audit seat. This file names them, says what each
may and may not do, and says how work moves between them.

It exists because that arrangement governs every session and lived almost
entirely in handoff prompts. `CHAT_STATE.md` carries a six-line version of the
first three, addressed to the architecture chat. The seat those rules bind
hardest, the implementing seat, was never told them by any file it is
instructed to read.

## Recheck before you rely on this

**This file cannot be verified by the repository.** Every other document here
can be checked against the code or the data, and where it disagrees the code
and the data win. A working arrangement between people and sessions leaves no
trace in the tree, so nothing in a commit can prove or disprove a word of
this. That is precisely why it can rot without anyone noticing, and why the
checks below are part of the file rather than advice about it.

**Where this file and what the operator actually does disagree, the operator
wins and this file is stale.** Report it and correct it.

| What this file claims | How to check it | Who can check it |
|---|---|---|
| The four seats exist and divide work this way | Ask | Operator only |
| The implementing seat pushes its own commits once the full suite passes, and never forces a push | Ask | Operator only |
| The audit seat runs at `ultracode` | `/effort` in Claude Code offers it. It needs a model supporting `xhigh` and workflows enabled | Operator only |
| `CLAUDE.md` ranks nine authorities and puts a brief at rank 4 | Read "When documents disagree" in `CLAUDE.md` | Any seat |
| Records live in `docs/decisions/` and `ADR-RULES.md` governs amending them | `ls docs/decisions/` | Any seat |
| The pre-commit hook runs six gates | `grep -n "Six checks" .githooks/pre-commit` | Any seat |
| The hook is enabled in this clone | `git config core.hooksPath` returns `.githooks` | Any seat |
| `MAP.md` is generated, never hand-edited | `python tools/generate_map.py --check` | Any seat |
| `CHAT_STATE.md` carries a shorter seat list | Read its "Three seats" section | Any seat |

**Update `verified:` in the frontmatter only after re-checking every row**,
and add a Changes row saying so. A partial check updates nothing. A date
bumped on a file half-checked is worse than a stale date, because a stale date
at least tells the truth about itself.

**`CHAT_STATE.md` is the architecture chat's file.** Its seat section is not
wrong; this file is the fuller one and adds the fourth seat. If the two ever
disagree, that is a defect to raise with the operator, not to settle by
editing the other file. Same rule as two unsuperseded records that conflict.

## The operator

**Decides.** Scope, cost, anything about roles, titles or what he is reachable
for, and anything that changes what the project is.

**Relays** between the other three seats, and pushes. He is not a relay for a
question either chat could answer from the repository itself.

**Approves** any brief clause that overrides an accepted record. Without that
approval the record wins.

## The architecture chat

**Concludes decisions, writes records, writes briefs, and checks what comes
back.** It does not implement.

**Keeps `CHAT_STATE.md`**, its own ledger of what was raised and what waits.
`STATE.md` is the project's state; `CHAT_STATE.md` is the conversation's.

**May not** write code, run the pipeline, or commit.

## The implementing seat

Claude Code, at `xhigh`. This is the seat most sessions are.

**Executes briefs.** Writes code and tests, writes the session log, updates
`STATE.md` in the same commit as the work, and audits its own output.

**Decides** method, structure and tooling. Those are not brief material.

**Stops and hands back** when an answer would change what the project is, and
when a brief contradicts an accepted record. It reports the conflict rather
than choosing.

**May not** write or amend a decision record beyond what `ADR-RULES.md` allows
a seat to correct without asking, edit `MAP.md` by hand, push before the full
suite passes or force a push, or work around the scope floor in `CLAUDE.md`.
It pushes its own commits otherwise: the operator's D10, 2026-09-25.

## The audit seat

Claude Code at `ultracode`, which runs the model at `xhigh` and lets it
orchestrate dynamic workflows across parallel subagents.

**It continues across jobs like any other seat, with one exception.** When the
work is critical enough that being cold to it is worth the re-reading, the
operator starts a fresh chat for it. Cold is this seat's method, not its
housekeeping, so that call is made on the importance of the audit and not on
how long the chat has run.

**Cold is the point.** A seat that wrote the work reads its own intent into
it, not the text. The implementing seat tested a permission hook against what
it meant rather than against what the hook would receive, and built the guard
backwards. A seat that has never seen the reasoning can only read what is
written, which is all the next seat will get.

**May** read anything, run the test suite, run `tools/mutate.py`,
`tools/generate_map.py --check`, `tools/preference_audit.py`, run the pipeline
with `--test-mode --no-commit`, and clone the `data` branch into its
scratchpad.

**May not** edit any file, commit, push, write or amend a record, touch
`MAP.md`, or write to Airtable. That prohibition is what makes fanning work
out safe: an agent that cannot write cannot break the arrangement in this
file.

**Delivers findings to the operator**, with the command and its output for
each, never straight to the implementing seat. The operator routes them, the
same way he routes briefs.

**Carry the authority order and the scope floor into every task it fans out.**
Subagents start cold and inherit neither. The scope floor exists because those
items get reintroduced by someone improving robustness, which is exactly what
a parallel agent is told to do.

**Its own synthesis is a set of claims, not findings.** A workflow's answer
aggregates subagent summaries, and a summary is self-report with the evidence
stripped. Re-check anything acted on, and tag it as coming from a workflow.

**Suits**: audits spanning many files, Confirmations, and any check where
missing something is expensive. The three queued jobs are the pre-flight audit
of `docs/how-to/build-the-writer.md` against the nine records it assembles, an
`ADR-RULES` audit across `docs/decisions/`, and the writer's Confirmations
once written.

**Does not suit**: building anything, single-file edits, mechanical work, or a
question a `grep` answers. This repository holds 42 Python files and 8,642
lines, measured 2026-09-22. Fanning that out buys orchestration overhead and
nothing else.

## How work moves

1. The operator raises something, or a seat raises it to the operator.
2. The architecture chat concludes it and writes the record.
3. The architecture chat writes a brief. The operator relays it.
4. The implementing seat executes, commits, logs, and reports back through the
   operator.
5. The audit seat checks the result when the cost of a miss justifies it, and
   reports findings to the operator.

**A brief ranks below every accepted record.** It overrides one only when it
names the record and the clause and states that the operator approved the
change, and it then carries rank 1. `ADR-RULES.md`.

## Rules that bind every seat

**When another seat's file has changed under you, flag it. Do not revert it.**
If you did not touch the file and its content differs from what you expected,
someone else changed it deliberately. On 2026-09-22 the implementing seat
reverted the architecture chat's edits to `CHAT_STATE.md` on the reasoning
that they looked unintended. They were intended and approved. The cost of
flagging a correct change is one message. The cost of reverting a correct one
is silent loss.

**This repository is public.** Base, table and field IDs are secrets and never
appear in a committed file. Never ask for or accept a token in conversation; a
pasted token has to be rotated.

**Never fetch the `data` branch into this repository's refs.** Clone into the
scratchpad.

**Never bypass the pre-commit hook.** Six gates, and the reason each exists is
written above it in `.githooks/pre-commit`. Read the refusal instead.

**A chat ends when the operator says "close this chat", and at no other
time.** He watches the context with `/context` and decides when it is full
enough. Those three words are the trigger. A seat does not close itself, does
not ration its own work against a context budget, and does not suggest
wrapping up because it feels near the end. Until he says it, the chat
continues.

**When he says it, the next chat starts fresh rather than compacting.** That
is the whole point of the keyword: compaction is the thing it exists to
replace. A compaction summary is self-report with the commands and outputs
stripped, which is the one input class `CLAUDE.md` refuses to trust, and a
summary of a summary is how a wrong number becomes permanent. Reading the
files in the reading order costs about 73,000 bytes, measured 2026-09-22, and
buys a seat whose every claim traces to a file.

**One implementing seat at a time.** When a new one is initialised the old one
is closed, because two seats committing to the same working copy is how a
correct change gets reverted. On 2026-09-23 two ran in parallel for one round
and only the clean tree between their commits kept it harmless.

## What this file does not hold

`STATE.md` holds what exists and what is blocked. `CHAT_STATE.md` holds what
the architecture chat raised and what waits. `logs/README.md` holds what prior
sessions did. `CLAUDE.md` holds how to work in this repository, and outranks
this file. This one holds only who does what.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-25 | The push rule replaced with the operator's D10 | The file said the implementing seat pushes only when a brief says push. The seat had pushed its own commits since the operator's "you can push it if you would like" of 2026-09-23, and read that as standing; a compaction summary then called it so, and the seat pushed against Brief 7's "The operator pushes". Asked, he answered: "D10: yes, you are allowed to push." The conditions, the full suite first and never a forced push, are those the seat proposed with the question. The file's `verified:` date is unchanged: only these two lines were re-checked |
| 2026-09-23 | The session-boundary rule replaced with the operator's, and the audit seat's fresh-chat rule relaxed to its reason | The file said to start a new chat at a task boundary and said the audit seat takes a fresh chat every time. Both were the seat's inference, not the operator's practice, and the audit one was already producing a wrong answer within a day. He decides closure by watching `/context` and saying "close this chat"; a seat does not decide it. The audit seat goes cold when the importance of the audit justifies it, not on a schedule. The one-seat-at-a-time rule was added after two implementing seats ran in parallel for a round |
| 2026-09-22 | File created | The arrangement governed every session and lived in handoff prompts. `CHAT_STATE.md` carried six lines of it addressed to the architecture chat, so the implementing seat was never told the rules it is bound by. A fourth seat made the omission worse, since an `ultracode` seat fans work out to agents that inherit no context at all |
