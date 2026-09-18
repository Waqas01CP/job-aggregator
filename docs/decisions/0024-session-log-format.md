---
status: accepted
topic: practice
description: What a session log must contain: tagged claims, evidence behind each one, and what was not done.
date: 2026-09-11
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0024: Session log format

## Context and Problem Statement

ADR-0023 establishes `logs/` with one log per session. This record fixes what a log contains.

The working cycle produces a written brief in an architecture chat, an implementing session executes it, and the chat verifies the result. The implementing session holds knowledge that exists nowhere else at the moment it finishes: which alternatives were rejected and why, what was checked and found already correct, what was deliberately not done, and what remains unverified.

None of that is recoverable from a diff. A diff shows what changed, not what was considered and rejected, and not what was examined and left alone.

Two failure modes bound the format. A log that is a narrative of the session rots: practitioner writing on agent decision records is blunt that documenting everything leads to burnout and a rotted log, which is worse than no log. A log that is too thin loses the only record of why a thing is the way it is: one report describes an agent deleting a working idempotency layer because nothing told it the original had been written after an incident that double-charged 4,200 customers.

Research pass 0004 initially took the first warning and ruled against detailed logs, having not read the operator's existing ones. That verdict was wrong. The prior project's logs are not narratives. A representative log runs about sixty lines, carries a file and line number on every claim, tags each as verified or believed, gives per-item verdicts, states honest size and risk for each option, and closes with a recommendation explicitly marked as not a decision.

## Decision Drivers

- The log is the only record of rejected alternatives and of things checked and found correct.
- Audits, incident investigation and security review all read logs, and all need evidence rather than assertion.
- A log nobody can audit is as useless as no log.
- Length must follow the work. A one-line change and a cross-cutting investigation do not deserve the same log.

## Assumptions

- The implementing session will write honestly about what it did not verify. Unenforceable; the format makes omission visible rather than preventing it.
- Sixty to two hundred lines is the usual range for this project's work. Taken from the prior project's logs, not measured here.

## Considered Options

- No logs. Rely on commits and decision records.
- A narrative of the session.
- An evidence package with tagged claims and per-item verdicts.

## Decision Outcome

Chosen option: "an evidence package with tagged claims and per-item verdicts".

Every log carries a header: date, model, the HEAD commit it ran against, whether it was read-only or mutating, and the commit status of its own findings.

**Every factual claim carries its evidence inline.** A file and a line number, or a command and its output. A claim with no evidence is a belief and is marked as one.

**Every claim is tagged.** `[VERIFIED]` means exercised and observed this pass: grepped, quoted, run, output seen. `[BELIEVED]` means reasoned from the code but not run. **Unmarked defaults to believed.** The default points at the weak set rather than hiding it.

**Rejected alternatives are recorded with the reason.** Why X over Y is the single most valuable thing in a log, because it is the one thing a future session cannot reconstruct and the one thing it will otherwise undo.

**What was checked and found already correct is recorded.** A future session that repeats that check has wasted the session.

**What was not done is stated explicitly.** Silence reads as completeness.

**Findings are separated from decisions.** An implementing session reports and recommends. It does not decide. A recommendation is labelled as one.

**Length follows the work.** No cap and no floor. A log that could be three lines is three lines. The test is whether an auditor could reconstruct what happened and check it.

**A log recording an external contract change carries the payload before and after.** When a third-party response shape moves, the shapes themselves are the evidence and a description of them is not. Adapted from the operator's prior project, where interface changes are broadcast with the old and new payloads quoted in full plus the incident that forced the change. ADR-0018's contract check reports that a board changed; this is what records what it changed to.

After writing a log, the session appends its row to `logs/README.md` and updates the affected rows in `STATE.md`, both in the same commit as the work.

### Consequences

Logs become auditable. Every claim can be checked against the file and line it cites.

The verified and believed split means a security or correctness review can go straight to the unverified set, which is the point of defaulting to believed.

Rejected alternatives survive, so an agent proposing to remove something can find out why it exists.

Writing costs real time at the end of each session, and that cost is accepted.

A dishonest or lazy log is still possible. Tagging makes omission visible on reading; it does not prevent it.

The index stays thin only if the discipline holds. `logs/README.md` rows are compressed by rule; reasoning belongs in the log.

### Confirmation

Take a completed log and pick three claims at random. Each must be checkable from what the log itself states, without opening anything the log does not name. A claim that cannot be checked that way was not evidence, and the format failed on that claim.

## Pros and Cons of the Options

### No logs

Good, because there is nothing to maintain.
Bad, because rejected alternatives and negative findings exist nowhere else, and both get re-derived or undone.

### A narrative of the session

Good, because it is easy to write.
Bad, because it is long, unauditable, and the specific thing practitioners report rotting.

## More Information

Format adapted from the operator's prior project. The reasoning, including this pass's wrong initial verdict and how it was corrected, is in `docs/research/0004-project-context-documentation.md`.

The prior project also maintains a separate `team-updates/` directory broadcasting interface changes to named collaborators. That artifact is not adopted here: it exists because three people needed notifying, and this project has one. Its payload-before-and-after shape is adopted into the log format instead.

The log directory and index are ADR-0023.
