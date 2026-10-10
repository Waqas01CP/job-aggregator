---
status: accepted
topic: measurement
description: The contract check reports through its run log, platform by platform, so one source's failure cannot cost another's findings; and every finding and every run failure reaches Airtable as a row in the Health table. Consolidates ADR-0036 at its eighth amendment.
date: 2026-10-07
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0061: The contract check reports per source, in its log and in Airtable

## Context and Problem Statement

ADR-0036 decided on 2026-09-17 that the contract check (ADR-0018) reports a changed field through its run log and never by failing, so that a board changing its API and the check itself crashing never share a signal. It deferred the Airtable row, the second reader of those logs, until the writer existed. It was amended seven times in three weeks: the cadence, a wrong cross-reference, the build, its arithmetic, the deliberate re-baseline, UTC times, and the version-1 requirements of ADR-0059.

The eighth change is two things built in October. Recording it in ADR-0036 would make an eighth row, which is the Decision Record Standard's supersession trigger. This record consolidates ADR-0036 and adds them.

**What was wrong.** ADR-0059 required on 2026-10-03 UTC that each source's check stand alone, because one source's trigger must not affect the rest. The implementing seat found on 2026-10-04 that one source could end the whole check three ways: an exception other than an HTTP error in one platform's check reached `main`, which exited 1 and committed no log, losing every platform's findings for that run; one budget of six requests served all three platforms, so two failing boards could starve the third; and one circuit breaker, opened by two platforms' failures, refused the third.

**What was missing.** No failure reached Airtable, from either workflow. ADR-0059's test for done requires that every failure does.

## Decision Drivers

- A changed field and a crashed check must never share a channel (ADR-0036, carried forward).
- One source's failure must not cost another source's findings (ADR-0059).
- The operator opens a table, not a log (ADR-0004).
- Aggregator text never reaches the public branch (ADR-0020), and an exception's message can carry it.
- Calls are scarce (ADR-0004), and a row should mean something is wrong or new.

## Assumptions

- Contract changes are rare. **Not measured** as a rate. The changes ADR-0036's Changes record from the check's first ten days, 2026-09-25 to 2026-10-04, were this project's own, re-baselined.
- The Health table costs a few calls a month. **Inferred** by the implementing seat: a row is sent only when something is wrong or new, once.

## Considered Options

- Keep ADR-0036 and add an eighth row.
- One record per change: the isolation in ADR-0018, the Health table in a record of its own.
- Consolidate ADR-0036 with both changes.

## Decision Outcome

Chosen option: "consolidate ADR-0036 with both changes".

**We will write each check's findings to its run log on the data branch**, naming each changed field, its previous shape and its current shape. A finding never fails the run. `tools/run_log_report.py` shows each platform's latest status, every change, and every failed or unreachable check with its detail.

**We will check each platform on its own.** Each has its own client, with its own budget of 2 requests and its own circuit breaker, so the check costs what it did, and each runs inside its own exception boundary. A platform whose check fails is reported as `check failed`, with the exception's class, file, line and function and **never its message**; its last fingerprint stands, and the other platforms are checked.

**We will keep three exit codes, and keep them meaning three things.**
- **0:** the check ran; findings, if any, are in the log.
- **2:** a platform's check failed. The log is committed, the workflow pushes it, and a last step marks the run failed, as the fetch workflow does, so a failure never looks healthy and marking it never costs the other findings.
- **1:** the check itself crashed, before any platform or at the commit. No log is written.

**We will send every event that needs the operator to Airtable as a row in the `Health` table**, with a `Health test` table for test mode, both pipeline-owned. A row is an event, never an `unchanged`: a contract finding (a changed field, a re-baseline, an unreachable board, a failed check, a platform's first baseline), and a fetch run's failure. Each event is sent once. The fetch run sends both kinds, reading the contract check's events from its logs on the data branch, so the contract workflow holds no Airtable secret.

**We will run the check daily** (ADR-0036's cadence of 2026-09-18, carried forward).

**We will record a contract change we caused as ours.** A difference that follows a change of endpoint or of the fields an adapter reads is matched to an entry in `config/contract_rebaselines.json` naming its cause and its UTC time `at`; each stored shape carries the UTC time `since` it was accepted, so an entry older than the shape excuses nothing (ADR-0036's rows of 2026-09-28 and 2026-10-03, carried forward).

### Consequences

A board that changes its API is named in a table the operator opens, not only in a log he must think to read. That closes the gap ADR-0036 accepted on 2026-09-17.

A failing platform costs only its own findings for that run, and the run says so in red.

The Health table also carries the fetch run's failures, which no Airtable row carried before. It was named for health rather than for the contract on the operator's choice, so other failures can join it later.

**Nothing reaches the table until the operator sets two secrets**, the two table IDs. Until then the events wait in the run logs and nothing fails, so the version file's "every failure reaches Airtable" stays unmet until he does. *(Wrong when written, 2026-10-09: the operator had set both secrets on 2026-10-08, and the evening fetch of that day wrote 17 rows to `Health` at 19:13Z, read through the connector on 2026-10-09. The architecture chat had not read the seat's handoff, which said so.)*

A failed check's detail names where it failed and never why in words. Reading why takes the private log or a local run.

`CLAUDE.md`'s paragraph on exit codes names the fetch run's 2s and not the contract check's. That file is the operator's.

### Confirmation

**A finding must not fail the run, and a crash must not produce a finding.** Run the check against a saved response with one field renamed: it exits 0 and names the field, its old shape and its new. Make the check itself raise: it exits 1 and the log carries no finding.

**One platform's failure must not touch another's check.** Make one platform's check raise and change another's response: the first reads `check failed` with its location, the second's change is still found, and the run exits 2 with its log committed.

**A failed check's detail must never carry the exception's message.**

**An event must become one `Health` row, and only once**; an `unchanged` check must make none.

**Live only:** the first production `Health` row, after the operator sets the secrets. *(Seen 2026-10-08T19:13Z: 17 rows, 15 re-baselines of 2026-10-03 and the first baselines of Manatal and Workable, read through the connector on 2026-10-09. No failure row yet: none was among the events that first write carried.)*

## Pros and Cons of the Options

### Keep ADR-0036 and add an eighth row

Good, because nothing is rewritten.
Bad, because the standard makes an eighth amendment a supersession trigger: a decision read as an original plus a pile of rows is no longer one anyone can hold in mind.

### One record per change

Good, because each change sits beside its nearest record.
Bad, because ADR-0036 would still need its eighth row for the Health table it deferred, and the reporting decision would be spread over three records.

### Consolidate

Good, because one record states how the check reports, today, in full.
Bad, because ADR-0036's history moves to a superseded record and its Changes table.

## More Information

**Supersedes ADR-0036.** Carried forward unchanged: the run log as the channel and the reason a failed run is not one (ADR-0036's answer to question D); the report tool; the daily cadence; the deliberate re-baseline with its UTC times. Changed: the Airtable row is built, as `Health`, and carries the fetch run's failures too; a platform's failure exits 2 with its log.

ADR-0018 owns the check itself and carries the per-platform isolation in its Changes. ADR-0059 required both changes for version 1. ADR-0020 is why a message is never written.

Built by the implementing seat: the isolation as commit `2c38f6f` on 2026-10-04, the Health table as commit `9a23387` on 2026-10-07. The operator's decision of 2026-10-07 UTC on the table: "yes, you can create and just provide the ids. i think general health is good but only if the cost is not a lot."

## Changes
