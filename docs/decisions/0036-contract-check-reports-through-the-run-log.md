---
status: accepted
topic: measurement
description: The contract check reports through the run log rather than by failing, so a contract change and a crashed check stay distinguishable.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0036: The contract check reports through the run log, not a failed run

## Context and Problem Statement

ADR-0018 says the contract check will "report a change loudly, naming the field and how it changed, rather than emitting a pass or fail". CLAUDE.md forbids a notification system. The question was whether GitHub's own failed-run email could serve as the loud report, by having the check exit non-zero when a fingerprint changes.

It cannot, and the reason is that it reports the wrong event.

A failed workflow run means the run failed. If the check exits 1 on a contract change, then a changed field and a crashed check produce the same signal, and the operator cannot tell "Greenhouse renamed a field" from "the check itself is broken". ADR-0018's whole purpose is to distinguish a dead adapter from a quiet market; a channel that collapses two causes into one notification reintroduces exactly that ambiguity one level up.

The failure mode is also silent in the direction that matters. An email that arrives on every crash becomes an email the operator stops opening, and the one that carries a real contract change arrives looking identical.

## Decision Drivers

- ADR-0018's report must name the field and how it changed. An email subject line saying a run failed names nothing.
- A crash and a finding must never share a channel.
- CLAUDE.md forbids a notification system, and nothing here should become one by another route.
- The pipeline already has a channel the operator reads, and a second one is a cost.

## Assumptions

- The operator reads run logs when something looks wrong, rather than continuously. **Sourced** from the protocol: he opens a table, and the tooling reads logs for him.
- Contract changes are rare, on the order of a few a year per platform. **Not measured.** No contract change has been observed yet, because the check does not exist.

## Considered Options

- Exit non-zero on a change, and rely on GitHub's failed-run email.
- Write the finding to a report file on the data branch, read by a tool.
- Write the finding to the run log, and later mirror it into Airtable.

## Decision Outcome

Chosen option: "the run log, mirrored into Airtable later".

**The contract check writes its findings to its run log on the data branch, naming each changed field, its previous shape and its current shape.** The run succeeds. A run that exits non-zero means the check itself failed, which is a different event and keeps its own meaning.

**`tools/run_log_report.py` is where the operator, or a session, sees it.** That tool already reads run logs from the branch and is the existing channel.

**Once the Airtable writer exists, a contract change also becomes a row**, which is the operator opening a table, exactly as ADR-0014 intends. This is deferred behind the writer rather than built twice. *(Corrected 2026-09-22: the record that makes an Airtable table what the operator opens is ADR-0004. ADR-0014 decided the outcome sweep, says nothing about a report channel, and is superseded, by ADR-0045 and then ADR-0046.)*

**This answers question D with a no.** GitHub's failed-run email is not an acceptable report for ADR-0018.

**How often the check runs, and whether to build it at all, remains the operator's.** The costed options are on record: daily is about 90 requests a month now and about 240 after five more adapters; weekly is about 13 and about 35. *(Arithmetic, not measurement: one request per platform per check, three platforms today. The check built on 2026-09-24 makes exactly that, but does not yet log its request count.)* This record decides the channel, not the cadence.

### Consequences

A contract change is visible only when someone reads the logs, which is slower than an email and is the price of not collapsing two signals into one.

The check's own failures stay loud, because exit 1 keeps meaning the run failed.

A second reader of run logs is needed eventually, or a change sits in a file nobody opens. The Airtable row is that reader, and until it exists the gap is real and is accepted.

Nothing here constitutes a notification system: no message is pushed anywhere, and the operator pulls.

### Confirmation

Run the check twice against a saved response, with one field renamed in the second. The run must exit 0 both times, and the second run's log must name the field, its old shape and its new shape.

The check that can fail: make the check itself raise, and confirm the run exits 1 and the log carries no fingerprint finding. If a crash produces a finding, or a finding produces a crash, the two channels have merged.

## Pros and Cons of the Options

### Failed-run email

Good, because it needs no new mechanism and reaches the operator without him looking.
Bad, because it cannot name the field, and it makes a contract change indistinguishable from a broken check.

### A report file on the branch

Good, because it is durable and diffable.
Bad, because it is a second artifact with its own format when the run log already exists and is already read by a tool.

## More Information

Answers question D of the 2026-09-17 architecture brief. ADR-0018 carries a Changes row pointing here.

The check itself is unbuilt and its cadence is the operator's decision.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | Cadence decided: daily | The operator's choice from the costed options. About 90 requests a month now and about 240 after ADR-0029's five adapters, against a per-run ceiling of 500 that no run has come within 90% of. A contract change is noticed within a day. This record decided the channel and left the cadence open; it is now closed. The check itself is still unbuilt |
| 2026-09-22 | The Decision Outcome said a contract-change row is the operator opening a table "exactly as ADR-0014 intends". It now carries an in-place note naming ADR-0004, the record that makes Airtable what the operator opens | A cross-reference that pointed at the wrong record: ADR-0014 decided the outcome sweep and is superseded. Found by the architecture chat in an audit. The decision is unchanged |
| 2026-09-24 | Built. The check writes its findings to its own log in `logs-contract/` on the data branch and exits 0; a crash exits 1 and commits no log. `tools/run_log_report.py` closes with the check's latest status per platform and every change found. The Airtable row is not built | Implementation facts, recorded by the implementing seat. Its own directory, not `logs-runs/`: the fetch counts failed projections in a row from `logs-runs/`, and a contract log there would read as a success and reset the count. The row needs a table and a client that writes a second table, which is a brief. Both Confirmations run as tests |
| 2026-09-25 | The cadence's request figures marked as arithmetic | The corpus audit found them outside Assumptions with no basis. They are the check's own design, one request per platform, times the days in a month. Annotated by the implementing seat under ADR-RULES, on Brief 7's corpus work; the Decision Outcome is untouched. |
