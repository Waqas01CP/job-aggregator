---
type: state
description: The architecture chat's ledger. What was raised, what is waiting and on what, and the errors this chat made. Read at the start of a new architecture chat.
status: current
---

# CHAT_STATE

The architecture chat's ledger. **`STATE.md` is the project's state; this is the conversation's.**

It exists because items raised in a chat and not written down are forgotten the moment the chat moves on. Four such items nearly vanished before this file existed.

**Read this at the start of a new architecture chat**, alongside the behavioural prompt that chat is initialised with. This file carries what was decided and what is waiting. The prompt carries how the chat works, which cannot live in a repository file because it is about the conversation rather than the project.

Brought to final form 2026-09-18, at the close of the first architecture chat, after verifying against `logs/README.md` rather than against session reports.

**Revised 2026-09-20**, in the second architecture chat, against the repository and the live Airtable base rather than against the handoff prompt. That prompt was stale in three places and is listed under the errors below.

**Brought current 2026-10-09 UTC**, after recording nothing from 2026-09-25 to 2026-10-09: every old item was checked against `STATE.md`, `logs/README.md`, the records, Briefs 7 to 10 and their reports, the implementing seat's handoff of 2026-10-08 and the `Health` table read through the connector, then moved or kept; items 121 on are the fortnight's. The lapse is the first of the new entries in the errors below, and the rule it broke is under "Rules for this file".

---

## What this project is, in one paragraph

A scheduled pipeline that polls employer ATS job boards and one aggregator, deduplicates, filters against a versioned title pool and the operator's eligibility, and writes what survives to Airtable for the operator to review. Its purpose is hours returned, not roles found: job discovery was consuming the majority of a working week, and the reachable pool is roughly one qualifying role per six months, which the pipeline cannot change and is not built to. Its only binding success measure is Measure A, in ADR-0015: the median gap between a posting's publication date and its first appearance in the display, at or under 24 hours. *(2026-10-09: what it is working toward is version 1.0.0, the system working for the operator himself, ADR-0059 and `docs/versions/v1.0.0.md`. It reads twenty-six employer boards on four platforms and Himalayas.)*

## The seats, and what each does

**The operator** decides scope, cost, and anything about roles, titles or what he is reachable for. He relays between the other seats and is not a relay for questions either could answer directly.

**The architecture chat**, this one, concludes decisions, writes records, writes briefs, and checks what comes back. It does not implement.

**The implementing seat**, Claude Code, executes briefs, writes code and tests, writes session logs, and audits. It decides method, structure and tooling. It stops and hands back when an answer would change what the project is. It pushes its own commits once the full suite passes (D10).

**The audit seat** audits finished work cold and read-only, and reports to the operator, who routes its findings. `docs/how-to/the-seats.md` is the fuller account of all four, with its own recheck table.

A brief ranks below any accepted record. When they conflict, the record wins and the seat reports it. That is ADR-RULES.

---

## Where to look

| Question | File |
|---|---|
| What exists, what is blocked and on whom | `STATE.md` |
| What was finished, with proof | `docs/reference/completed.md` |
| Why the system is shaped this way | `docs/architecture-2.0.md` |
| Why one choice was made | `docs/decisions/`, indexed in its README |
| How records are amended and retired | `docs/decisions/ADR-RULES.md` |
| What each documented file holds | `MAP.md`, generated |
| What prior sessions did | `logs/README.md`, then chain backwards |
| What the audits found | `logs/audit/` |
| What was found and when | `docs/research/` |
| What was deliberately not done, and its trigger | `docs/deferred/` |
| Where the project is going, and what is left | `docs/versions/v1.0.0.md` |
| Everything the system is and does, for an outside reader | `CAPABILITIES.md` |
| The latest brief or report to each seat | `briefs/`, one file per receiving seat, gitignored |

---

## Status meanings

**DONE** with a pointer. **GATED** with the gate named in checkable words. **OPEN** with nothing blocking it.

Items keep their number forever and move rows rather than being renumbered. **Numbers 15 to 18, 25, 29, 44, 103, 109 and 112 appear in no table of this file**, checked 2026-10-09. Whatever they named was not written down here, and the repository does not say.

---

## Open

| # | Item | Notes |
|---|---|---|
| 81 | Banyan Canopy | Deferred by the operator 2026-09-23 with Himalayas, until he had seen rows in `Jobs`; review no earlier than 2026-10-07. Evidence by 2026-09-25: the same six finance postings on all thirteen runs, none admitted. ADR-0059 keeps Himalayas in version 1, the operator's decision of 2026-10-03 UTC, but on 2026-10-08 he told the seat his trial verdicts come later, and the seat's log lists both as waiting on him. Whether ADR-0059 is his Himalayas verdict is put to him, 2026-10-09; Banyan Canopy's verdict is his |
| 107 | Measure A's assessment | **Overdue, the chat's.** ADR-0015: "We will assess against Measure A two weeks after go-live"; go-live was 2026-09-24T03:27Z, so it fell due about 2026-10-08. Measured so far: publication to first seen, Greenhouse median 4.6 h and 90th percentile 9.7 h over 32 postings, Himalayas 10.2 h and 22.2 h over 448 under the morning-only poll (the seat, 2026-10-03, Brief 9); Himalayas is polled on both runs since 2026-10-04. The chat cannot read the data branch from here, so Brief 11 asks the seat for the two weeks' figures and the chat writes the assessment from them. Separate from the window the version file's test leaves to the operator, item 121 |
| 133 | Brief 11 to the implementing seat | To carry: item 132's registry entries; item 107's two weeks of Measure A; item 137's level rule, once he has answered for the unnamed levels; SmartRecruiters next, then Ashby (item 134); a dateless posting counts as passing (item 135); `docs/how-to/the-seats.md`'s recheck row that reads this file's "Three seats" section, renamed "The seats" on 2026-10-09 when the audit seat was added; and the records of 2026-10-09 to read. The chat writes it when the operator asks |
| 121 | The operator's open choices for version 1.0.0 | In `docs/versions/v1.0.0.md`: the window over which Measure A must hold; the period he uses the tables; whether a dropped posting's own reason must be stored, or its rule in the run log and the raw layer are enough; and Breezy, waiting on a documented endpoint or his acceptance of an undocumented one. Each his |
| 139 | Whether "add or update, never remove" binds the implementing seat in `CAPABILITIES.md` | The operator's rule for the file reached the chat as add or update, never remove; the template and the file's own upkeep section tell the seat to remove a number that can no longer be measured. Explained to him 2026-10-09 with each reading's consequence. His decision |
| 140 | The Decision Record Standard's line rule | It still says "A record stays under 200 lines" (checked 2026-10-09); ADR-RULES and Working Method 1.2 carry his rule of 2026-09-28. His reading of 2026-10-09, that 200 stays the aim and a record running a little over it never forces a new one, checked against ADR-RULES and answered. Whether to amend the standard, his file, is his |
| 141 | `CLAUDE.md`'s exit-code paragraph | It names the fetch run's exit 2 and not the contract check's, which ADR-0061 adds. `CLAUDE.md` is the operator's file, so the change is an update block for him (Working Method 8.8), the chat's to draft |

## Gated

| # | Item | Gated on |
|---|---|---|
| 56 | Set the real fetch ceiling from measurement | A month of run logs, from about 2026-10-17. Since 2026-10-07 and 10-08 Manatal and Workable add requests. By `STATE.md`'s contract-check row, no run had come within 90% of the ceiling of 500 |
| 66 | ADR-0044's star has no caller | A version after 1.0.0 (ADR-0059): it compares against accepted rows, which come only from his using the tables |
| 68 | ADR-0038's family views | The operator asking for one. The `Family` label is sent on every row since 2026-09-24; no view is built |
| 70 | Every unread field in `platform-fields.md` | Each needs a decision. Every field of the three live sources was re-measured over the saved postings on 2026-10-02, and Himalayas' `seniority` is read since then (ADR-0032). Still on the index's Pending list |
| 22 | Deduplication across source classes, employer alias map | A version after 1.0.0 (ADR-0059); `docs/deferred/employer-alias-map.md` holds its triggers |
| 24 | In-flight register separate from `STATE.md` | Work being in flight |
| 26 | Reuse boundary against the LinkedIn pipeline | One session, component by component |
| 27 | Which skills the project gets | Nothing technical |
| 28 | AGENTS.md symlink for Antigravity | Only matters if Antigravity is used here |
| 132 | Pushing the operator's two commits of 2026-10-09 | Entries in `tests/confirmations.py` for ADR-0060's five Confirmation leads and ADR-0061's four. ADR-0049's scan reads every record from ADR-0050 on, so the suite fails until they exist. Committed, not pushed, the operator's report of 2026-10-09 |
| 137 | The levels Workable and SmartRecruiters state | Decided 2026-10-09: read like Himalayas', Entry level and Mid-Senior level kept, the second for now (ADR-0032's Changes). Waits on his answer for the values he did not name, Internship among them (6 of SmartRecruiters' 20 postings), then Brief 11 and the seat's build |
| 142 | ADR-0055's live checks | The thirty-day clock's first removal, about 2026-10-17, and `accepted test` past fifteen days. The seat reads them; the chat records what they show |
| 143 | `AGGREGATOR_STORE_TOKEN` | Its expiry on 2027-01-01, the operator's to rotate before then (`STATE.md`, Blocked) |

## Done

| # | Item | Landed in |
|---|---|---|
| 1 | Read the Rahzaan reference files | Seven files, plus SPRINT_PLAN |
| 2 | Research 0004, project context documentation | `docs/research/` |
| 3 | Context artifact set | ADR-0023 |
| 4 | Log-verdict correction | Research 0004, ADR-0024 |
| 5 | First backlog committed and pushed | Four commits |
| 6 | Title pool | Version 4, 79 terms, family-ordered |
| 7 | MIT licence and scope statement | `LICENSE`, `README.md` |
| 8 | Supersession criteria, five cases plus the operational test | Decision Record Standard, vault |
| 9 | Change-history convention, eight-row supersession trigger | Decision Record Standard, vault |
| 10 | Document authority order | ADR-0022 |
| 11 | Session log format | ADR-0024 |
| 12 | STATE.md created, later split | `STATE.md` plus `docs/reference/completed.md` |
| 13 | Log index with the chain-reading rule | `logs/README.md` |
| 14 | Three endpoint spikes reviewed | Sixteen platforms measured |
| 19 | Adapter order after the slice | ADR-0029 |
| 30 | Auto Memory ranked and excluded from design | ADR-0025, authority level 8 |
| 31 | STATE.md staleness gate | Pre-commit gate 4, proven to fire |
| 32 | Rahzaan patterns into the vault standards | Three standards plus the index |
| 33 | This file | `CHAT_STATE.md` |
| 34 | Prove gate 4 fires | Blocked a real commit |
| 35 | Speechify floor | 8 titles across 329 locations. `updated_at` bulk-stamped |
| 36 | Postings per board | 11 boards, 1646 postings. Median 27, max 1086 |
| 37 | Lever `createdAt` semantics | Pages show no date. Answering itself through run data |
| 38 | Himalayas pagination | Browse works, search does not |
| 39 | Thirteen untested platforms probed | ADR-0007 holds, Manatal the material case |
| 40 | ADR-0007 confirmed | Manatal: clean JSON API, no date field of any kind |
| 41 | ADR-0006 Confirmation met | Youngest Greenhouse posting 16 minutes old at fetch |
| 42 | ADR-0001, ADR-0003 volume assumptions falsified | Changes rows on both |
| 43 | Employer provenance | ADR-0026, later extended to canonical URL |
| 45 | Assumption-basis rule | Decision Record Standard |
| 47 | First spike log backfilled | Marked as written after the fact |
| 48 | Briefs carry a logging section | From brief 2 onward |
| 49 | Dedupe key breaks on location-in-title | ADR-0027 |
| 50 | `updated_at` cannot detect change | ADR-0018 Changes row |
| 51 | ADR-0026 key count corrected | 18 to 20 |
| 52 | Research 0003 corrections | `pubDate`, `sort`, `updatedAt` |
| 53 | My propagation claim was false | Research 0004, error section |
| 54 | Log frontmatter type | Seat |
| 55 | The vertical slice built | Eleven ATS boards plus Himalayas, live on GitHub |
| 57 | Per-run fetch budget and detail-once | ADR-0028 |
| 58 | Provenance enum generalised | ADR-0026 Changes row |
| 59 | Brief 4 sent and implemented | ADR-RULES audited, index audited, ADR-0045 written, `docs/deferred/` created, five Airtable tables built and read back, heredoc guard built |
| 60 | Airtable tables built | **Five**, not four, in the base the MCP reaches |
| 62 | This file committed | Out of `.gitignore` and out of the generator's skip list |
| 63 | Record index audited against every record | Three defects found, all mine, all corrected: ADR-0010 wrongly marked as having a reversed clause, a preamble contradicting the file's own conventions, and a stale Changes-table count |
| 71 | ADR-RULES written and audited | `docs/decisions/ADR-RULES.md` |
| 72 | Record index restored | Fell fifteen records behind; repaired 2026-09-18 |
| 73 | Brief 4 response read and verified | Against `logs/README.md`, not against the report of it |
| 76 | Similarity matching decided against, for now | ADR-0044's deterministic star instead, with its trigger in `docs/deferred/` |
| 77 | Deletion flow decided | ADR-0045. Manual classification, timestamped deletion from the two rejection tables, accepted deleted by hand only. **Superseded 2026-09-19 by ADR-0046; see item 83** |
| 82 | The heredoc trap given a mechanism | `tools/heredoc_guard.py` and a PreToolUse hook. It asks, never denies, and fails open. Half its 16 tests are cases it must not fire on |
| 61 | The Airtable PAT and seven repository secrets created | Done by the operator 2026-09-18. An eighth is now needed for ADR-0047; that is item 89 |
| 74 | Question C answered | ADR-0047. Aggregator rows may go to private destinations, including the private Airtable base. They never reach the public branch |
| 78 | The stranded 2026-09-17 Airtable base | Operator's decision 2026-09-19: left as it is unless it causes a problem. The connector lists exactly one base, and it is the right one |
| 80 | `STATE.md`'s two commit references | Did disagree; both repaired by the seat, which also removed the commit hash from the headline so only the verified-against line names one. Local `main` and `origin/main` both at `da193b6`, checked 2026-09-19 |
| 83 | Classification flow redesigned | ADR-0046, superseding ADR-0045. Airtable has no move operation, so classification is a status the operator sets, the pipeline copies and deletes, and a stored outcome keeps a row out of the projection for good. One fifteen-day period on two clocks, in `docs/reference/retention.md` |
| 84 | Aggregator data destination decided | ADR-0047, reversing one clause of ADR-0020. A private repository for every aggregator-sourced store, plus the private Airtable base. Deletion becomes a complete purge because nothing was ever public |
| 85 | Poll cadence rule | ADR-0048, extending ADR-0006. A source is polled no faster than its documented refresh interval. Himalayas moves to the morning run only. The offset stays unset until a spike measures when its cache refreshes |
| 86 | The vault's operational test corrected | It pointed at cases 2 and 3, which are supersessions, and asked a question too broad to be true for case 3. Now asks whether a decision is still in force **and not carried into the later record**, and states the obligation that makes supersession safe. The short version in the record index was a second copy and was corrected with it |
| 90 | `STATE.md` reconciled against origin, the data branch and the base | 2026-09-22. Headline and Blocked rewritten to current state; Himalayas, writer and sweep rows brought to ADR-0039, 0046, 0047 and 0048; two workflow rows moved to DONE; every replaced paragraph and row kept verbatim in `docs/reference/completed.md`, checked line by line. New facts: eleven production runs, 36 requests each; the backfill ran live on 2026-09-19 and appended 257; Himalayas kept 11 to 28 per run and lost every one |
| 87 | `Classified at` created on `Jobs` and `Jobs test` | 2026-09-20, watching `Status` alone, verified by reading the schema back. A fifth connector limit found and recorded in `docs/reference/airtable-schema.md` |
| 91 | Record corrections, first part | 2026-09-22. ADR-0036's pointer to ADR-0014 annotated in place with a Changes row: ADR-0004 is the record that makes Airtable what the operator opens. `logs/README.md` gained two rows: one saying eight rows live in `logs/2026-09-17-corrections-and-airtable-schema.md` rather than files of their own, and one for that log's section at line 277, which had no row. Both files read back byte for byte. ADR-0035 needed nothing |
| 92 | `## Changes` moved to the bottom of sixteen records | 2026-09-22, operator's option A. Moved by script with three checks per file: the same non-blank lines before and after, frontmatter and title unchanged, and the table last. No Changes row, formatting only. `MAP.md` regenerated on a full copy of the 85 documented files, `--check` exit 0; the only rows that moved were three stale descriptions from this chat's 2026-09-20 edits. Index count updated: 51 rows across 27 records |
| 93 | ADR-0046: how a reason reaches the store | 2026-09-22, operator's decision. Changes row plus an in-place pointer at step 2: on day 15 the row is written from `Jobs` and its reason from the matching copy in the same run; a status change discards the old copy's reason. `retention.md` and `airtable-schema.md` say the same |
| 79 | `CLAUDE.md`'s authority order and two more defects | 2026-09-22, operator-approved. Nine ranks in two orders, with the brief at rank 4 and its one override; the amendment rule stated as the standard has it; the UI and notification lines cite no record, because none holds them. ADR-RULES gained a Changes row, ADR-0022 an Extended-by line, `architecture-2.0.md` the same two citation corrections, and the record index the amendment rule and the seven cases |
| 94 | `Stage` carried to the accepted store | 2026-09-22, operator's decision. Second Changes row on ADR-0046, and `retention.md` and `airtable-schema.md` updated. ADR-RULES' two em dashes removed on his approval the same day, formatting only |
| 98 | Ruling 1 and 4: the pipeline never writes `Status` | 2026-09-23, operator-approved. `expired_before_review` retired; the sweep gains step 4, which stores an unreviewed row the chain no longer admits, with the rule that dropped it, then deletes it. Closes ADR-0040's unowned removal. ADR-0046 and ADR-0043 carry the Changes rows; `retention.md` and `airtable-schema.md` follow |
| 99 | Ruling 2: the skip tests every member of a group | 2026-09-23, operator-approved. A projected row carries its representative's identity, and a group is skipped when any member is in a store. Storing every member was rejected: 170 records for one judgement would wreck ADR-0043's corpora. ADR-0046 carries the Changes row |
| 100 | Ruling 3: the projection performs no reads | 2026-09-23, operator-approved. Every read belongs to the sweep, which already reads `Jobs` daily and now owns step 4, so the projection's read line is removed. ADR-0004's clause is annotated and carries the Changes row: what survives is that Airtable is never authoritative. The four-document disagreement the seat raised is closed |
| 101 | Ruling 5: `Family` and `Star reason` classified | 2026-09-23, operator-approved. Both pipeline-owned, both text rather than single select because the connector cannot add a choice. ADR-0035's sent set becomes twelve when they exist; ADR-0038 and ADR-0044 carry the matching rows. `Star reason` empty means not starred |
| 96 | ADR-0046's call budget corrected | 2026-09-23. About 450 calls a month, 45%, from the seat's measured 39 groups over 345 rows and 29 after the chain. The old 360 counted the projection at one upsert call a run, true only below eleven groups, and included the read now removed. Recorded as arithmetic over a measured group count, with its date |
| 102 | ADR-0046's seventh and eighth Changes rows | 2026-09-25, on the operator's instruction to follow the rule rather than supersede early. Row 7 records his rename of the `Status` values to the table names, verified through the connector; row 8 records the measured budget. The record is now at its limit and says so in row 8 |
| 105 | ADR-0027 against the display | Closed 2026-09-25, measured, no change needed. Over all 345 rows of `filtered.json`, 299 differ between raw and normalised title and the matched term, the admission verdict and ADR-0038's family are identical for every one, both ways. The two rules stay separate; one `fold` serves both, as `fold`'s docstring records. Annotated in ADR-0027 with a Changes row, and the check is named for the next board added |
| 106 | Himalayas' contract fingerprint | Closed by the operator 2026-09-25: it stays on the public branch. It carries field names, type names and presence words, never a value, and those names are already public in the adapter's source |
| 110 | The accent step recorded | 2026-09-25. ADR-0021's normalisation list gains it, with the operator's D4 measurement: 1,458 distinct titles folded both ways, 21 folds changed, one verdict changed, no dedupe keys merged. ADR-0047's superseded first Changes row is annotated as such |
| 114 | ADR-0049 written, fitness functions | 2026-09-25, operator-approved. Every architectural rule that code can break silently gets a test that names the record it guards and is proved by a mutation, in the ordinary suite, never a separate one. The first three are ADR-0027's normalisation invariant, ADR-0031's existing preference audit and ADR-0035's field ownership; ADR-0020's commit guard is named as one already. Sourced from Building Evolutionary Architectures and Thoughtworks, read 2026-09-25 |
| 120 | ADR-0050 written, the flow consolidated | 2026-09-25. Supersedes ADR-0046 at its eighth amendment, on the operator's rule to follow the standard rather than supersede early. It carries every clause still in force and names them, adds the copy on every fetch, his D3 rule for closed postings with a `Closed` field and a fifteen-day clock, the closure test that ignores a skipped board, and the call-trajectory guard. ADR-0046 marked superseded with its ninth row, the index and both reference files updated, `MAP.md` regenerated at 93 files |
| 111 | ADR-0041's ordering clause narrowed | 2026-09-25, operator-approved: "the main ordering will always be date and the families and others can be views or something else." A reachability tag may filter or group a view and never order one. Changes row written; nothing was built on the old wording |
| 113 | The call-trajectory guard approved | 2026-09-25. The run log reports the month to date from both branches and says so loudly past 60% before the fifteenth. In ADR-0050's budget section, and the sweep brief builds it |
| 115 | ADR-0004 carries the allowance in full | 2026-09-25. Where to read the counter, the once-ever 30-day grace period, that no warning precedes the limit, and that every client on the workspace spends it, this chat's connector included. Read from Airtable's help centre the same day |
| 116 | The record index is current | 2026-09-25. ADR-0049 added, and the Changes count corrected from 52 rows across 27 records to 90 across 38, counted across the corpus. `MAP.md` regenerated twice and its own check passes, at 92 files |
| 117 | ADR-0021's EY example corrected | 2026-09-25. Its Context named EY as a large board; ADR-0029 records EY as a careers site that was never probed and is out. Annotated in place, reasoning unaffected, no Changes row: a corrected example is not an amendment |
| 88 | `Status` carries three choices | Done by the operator 2026-09-24, renamed rather than recreated, keeping the eight marked rows and their `Classified at` times. **Verified through the connector 2026-09-25**: both tables hold exactly `accepted`, `rejected-poor-filtering`, `rejected-not-a-fit`, and `expired_before_review` is gone. The names are the table names, not ADR-0046's `not fit` and `poor filtering`; that rename is item 102 |
| 89 | The private aggregator store | Done. Repository, fine-grained token and both secrets exist, and the store is proved on a runner: test-mode run 36016481510 pushed three files to the private `data-test` branch, and production run 36036717095 created the private `data` branch. **Verified 2026-09-25 from the public branch**: 963 seen entries, all Greenhouse and Lever, and no `fetch-all/himalayas.json`. The token expires 2027-01-01 |
| 97 | Brief 5, superseded by Brief 6 | Brief 6 sent, built, pushed and live. `Jobs` filled at 2026-09-24T03:27Z. **Verified through the connector 2026-09-25**: 44 rows, 29 ATS rows carrying `Family` and 15 Himalayas rows without it, which is the report's own correction confirmed |
| 95 | A `Stage` changed after day 15 | Closed 2026-09-23: accepted as it stands. The store keeps the value the copy held on day 15 and nothing reads the difference. Revisit when the accepted-prune tool is built. Both values live in the `accepted` table; two views by hand separate them |
| 104 | Cross-source duplicates | Moved 2026-10-09. Accepted for now on the operator's decision of 2026-09-25 and deferred with three triggers, `docs/deferred/employer-alias-map.md`; outside version 1 by ADR-0059. Item 22 is the deferral |
| 108 | The employer alias map, triggerable | Moved 2026-10-09. The deferred entry was written 2026-09-25, the duplicate accepted for now |
| 118 | The sweep brief, and the corpus work | Moved 2026-10-09. Brief 7, built 2026-09-25 and live; the first scheduled sweep 2026-09-26, its row in `completed.md`. The corpus audit's conflict 2 handed back and closed by ADR-0051 |
| 119 | ADR-0050's closure test needs the operator's number | Moved 2026-10-09. Twelve polled runs, his decision of 2026-10-03 on the seat's repost measurement: twelve Greenhouse postings left their boards and returned after 23 to 130 hours (ADR-0050) |
| 64 | The Airtable writer and the daily sweep | Moved 2026-10-09. The projection live from 2026-09-24T03:27Z; the sweep from 2026-09-25 and on schedule from 2026-09-26 (`completed.md`) |
| 65 | ADR-0043's outcome stores | Moved 2026-10-09. Built with the sweep; five stores since 2026-09-28, three of them outcome corpora |
| 67 | ADR-0040's projection filter, with the stored-outcome skip | Moved 2026-10-09. Built in Brief 6, 2026-09-23; the skip reads the removal store by reason since Brief 8, 2026-09-30 |
| 69 | ADR-0041's structured location half | Moved 2026-10-09. D13 on 2026-09-26, the structured place and stated workplace on 2026-10-02; ADR-0057 superseded ADR-0041 on 2026-10-03 |
| 20 | Rozee.pk as a source | Moved 2026-10-09. Out of automated use by ADR-0059: its privacy policy forbids use of its material in a networked computer environment (research 0005). His to use by hand |
| 21 | Description matching | Moved 2026-10-09. Built for three facts, years asked, a right to work and on-site work, by ADR-0058 on 2026-10-02 and 10-03; any further use is a new decision |
| 23 | End-state document | Moved 2026-10-09. ADR-0059 and `docs/versions/v1.0.0.md`, item 127 |
| 46 | Lever in or out of the slice | Moved 2026-10-09. In the slice since 2026-09-17. `createdAt`'s meaning stays undefined, and ADR-0052 never drops Lever for age on it |
| 75 | Adapter order execution | Moved 2026-10-09. ADR-0029's order replaced by ADR-0059's, measured yield first: Manatal built 2026-10-07, Workable 2026-10-08, then SmartRecruiters and Ashby |
| 122 | The records of 2026-09-28 | ADR-0051 every field saved privately, ADR-0052 age judged once at first sight, ADR-0053 Himalayas through its search, ADR-0054 a scheduled run happens, ADR-0055 the clock and the clearing tool, ADR-0056 the whole layer with a delta design; ADR-RULES' three rules, the line rule among them, the operator's decision of 2026-09-28 |
| 123 | Brief 8 | Built 2026-09-30: the reason-based skip, ADR-0055's clock and tool, ADR-0053's agreement check, ADR-0036's re-baseline, ADR-0041's 74 and 17 met exactly. Report with the fourth audit |
| 124 | Audit reports kept | The operator's decision of 2026-09-30; the fourth audit's report committed unchanged in `logs/audit/` on 2026-10-01 |
| 125 | The records of Brief 8's report | 2026-10-03: ADR-0057 supersedes ADR-0041, eligibility in one record; ADR-0058, the description read once at fetch; amendments to thirteen more |
| 126 | Brief 9 | Built 2026-10-03: closure at twelve, re-baselines timed, every Confirmation clause of ADR-0050 to ADR-0058 held by a test or marked live only, time zones as residence measured |
| 127 | Version 1 | ADR-0059, research 0005 and `docs/deferred/response-quality.md`, 2026-10-03 and 10-04 UTC; `docs/versions/v1.0.0.md` and the test for done, accepted by the operator on 2026-10-04 UTC. Audited cold the same day, three rounds |
| 128 | `CAPABILITIES.md`, the chat's lane | `dfe9caf`, 2026-10-04; rechecked 2026-10-09 against the seat's five changes, all deliberate, and brought current in the chat's lane |
| 129 | Brief 10 and its two addenda | Sent 2026-10-04; the report and Addenda 1 (2026-10-07) and 2 (2026-10-08) read end to end on 2026-10-09, 298 lines |
| 130 | The records of Brief 10 | 2026-10-09: ADR-0060 supersedes ADR-0056 (the projection reads `Jobs` back), ADR-0061 supersedes ADR-0036 (the contract check per source, and `Health`), amendments to thirteen more, research 0005 corrected, the version file's statuses, UTC dates. Audited cold twice. Committed by the operator, not pushed: item 132 |
| 131 | The Working Method, the chat's parts | Version 1.2, 2026-10-09, outside the repository: the audit seat and the seats file, evidence grading, the line rule, the threshold rule, the version file, whole context in a brief, the ledger rule below |
| 134 | SmartRecruiters or Ashby next | 2026-10-09: SmartRecruiters, then Ashby. The operator: the order between two sources both to be built does not matter to him (ADR-0059) |
| 135 | Does a posting with no date count as passing | 2026-10-09: yes, "if the post is genuine then i would like to see it" (ADR-0059) |
| 136 | A guard against Himalayas' listing date | 2026-10-09: none in version 1, "yes, it is acceptable" (ADR-0052) |
| 138 | The `Health` table's two secrets | Set by the operator on 2026-10-08. The evening fetch wrote 17 rows at 19:13Z, read through the connector on 2026-10-09: 15 re-baselines of 2026-10-03 and the first baselines of Manatal and Workable |

---

## Errors this chat made, kept deliberately

A record that reports only what survived is not a record.

**The twenty-per-board figure**, invented rather than estimated, written into two records as though measured, and falsified when eleven boards returned 1646 postings. It produced the assumption-basis rule.

**The claim that it also reached the architecture document**, asserted four days after proposing a rule against unchecked assertions. The seat grepped and found it in neither.

**The MADR recommendation**, made from vendor content marketing and reversed on reading the primary specification. It produced the source-quality rating.

**The skills verdict**, reversed twice, the second time on an analogy rather than evidence.

**Ruling against detailed logs without opening the operator's**, having listed the directory containing them two turns earlier. The verdict was wrong: the advice applied to systems with no index and no chain rule, and his had both.

**A verification case handed to the seat that passed trivially** and tested nothing, in a project whose standard is that a check which cannot fail is worse than none.

**"Measured dead" applied to Himalayas** from an Apify corpus that was never Himalayas data. Withdrawn, and Apify is no longer cited as a baseline for anything.

**Sharing an Airtable base asserted as a working route** without testing whether the connector surfaces shared bases.

**Letting the record index fall fifteen records behind** while maintaining the rule that a second copy of a fact is a defect. Rebuilding it from session reports rather than the records then introduced three further defects, the worst of which marked the scope floor as partly overturned.

**Writing four secrets and four tables into the handoff** from a brief rather than from the repository, after the seat had already recorded seven and five.

**Asserting the `To review` view's filter and sort were set**, in `docs/reference/airtable-schema.md`, when the connector cannot read a view's filter and nothing had been checked. Caught in the same session and corrected to say what is actually known: the view exists, and its filter is specified in the how-to but not verified from here.

**Placing `## Changes` above `## More Information`** in ADR-0040, ADR-0047 and ADR-0048, against the Decision Record Standard, which puts the table at the bottom. Found while writing the decision-record template, 2026-09-22. No functional cost; three files that later records get copied from carried the wrong order. Fix queued with the record corrections. **The audit of all 48 records then found the same order in 13 more, most of them the seat's**, so it is a corpus pattern rather than this chat's alone, and it is item 92.

**Reporting that ADR-0035 names the reason fields as `Jobs` fields.** It does not, and needed no change. Found on reopening it, 2026-09-22.

**Calling ADR-0036's pointer to ADR-0014 stale.** It was wrong from the day it was written: ADR-0014 decided the outcome sweep and says nothing about the operator opening a table as a report channel. The fix was the same annotation; the Changes row names it as a wrong cross-reference.

**Leaving `MAP.md` stale on 2026-09-20.** Three descriptions changed in `retention.md`, `airtable-schema.md` and the how-to, and the map was not regenerated, which the pre-commit hook would have refused. One of them also still said four connector limits after the body said five. Found 2026-09-22 by running the generator on a full copy; corrected.

**ADR-0046's budget line for the projection**, 1 upsert call a run where 25 groups at ten a call is 3. Written 2026-09-19, found 2026-09-22 while writing Brief 5. Item 96.

**Recording nothing in this ledger from 2026-09-25 to 2026-10-09.** Two weeks of items lived only in briefs, each overwritten by the next, and in the chat's own context. The cost: on 2026-10-09 the chat told the operator to set two secrets he had set the day before, and old items stayed open here long after they were done, the writer among them. Found by the chat on 2026-10-09; the rule it produced is under "Rules for this file".

**Telling the operator on 2026-10-09 to set the `Health` table's secrets**, and writing that they were unset into ADR-0061, ADR-0059's Confirmation, the version file and `CAPABILITIES.md`. He had set them on 2026-10-08, the implementing seat's handoff said so, and 17 rows were already in the table. The chat had not read the handoff. Corrected the same day.

**Dating records by the operator's clock in Karachi**, a day ahead of UTC for part of every day: rows of 2026-10-04 UTC written as 2026-10-05, and decisions of 2026-10-03 UTC written as 2026-10-04. `CLAUDE.md` says dates are UTC. Found by the implementing seat on 2026-10-04 for the first kind and by the chat for the second; restated with markers on 2026-10-09.

**Reading D13 as an extension of ADR-0041**, 2026-09-28. It replaced ADR-0041's central rule, that location keywords never reject, which is a supersession. ADR-0057 superseded it on 2026-10-03.

**Five of 2026-09-28, three with one cause: adding something without rechecking what depended on it.** The index's Changes count read 123 because an ADR-RULES row was added after counting. ADR-0043's line 111 contradicted the principle written above it in the same edit. ADR-0050's "nothing else removes a row" went false when ADR-0055 was written an hour later. ADR-0050's "about fourteen hours" was corrected from start times taken from a report, not the runs. And ADR-0041 put the seat's summary in quotation marks as the operator's words; his logged words were "time zone is not an issue".

**ADR-0050's assumption that a closed row would not return**, 2026-09-25. The filtered layer keeps every row it admitted, so the projection re-sent a closed row at once. Found while writing Brief 8; the skip now reads the removal store by reason.

**ADR-0056's intake of five to ten display groups a day**, 2026-09-28, written as the reason the measurement was urgent. Part of it divided a live search total by a guessed month. Brief 8's week measured about one a day; Brief 10's week measured about 7.5. The figure had no measured basis either way.

**The research round of 2026-10-03 and 10-04 UTC.** The pass was announced as 0004, a number already taken. Remotive was first called out on a weak third-party size count. A batch script failed half way and was rerun from the originals. The cold audit then found statements claiming more than their sources showed, eight in ADR-0059 and four in research 0005 among them, and stale or wrong lines in ADR-0023, ADR-0048, ADR-0050, ADR-0051, `rozee-pk.md`, the alias map's third trigger and the brief itself, all corrected the same day.

**The round of 2026-10-09, before its cold audit.** A paragraph inserted inside the version file's Sources table broke it; "779 postings" was left in the chat's own lane of `CAPABILITIES.md` after the seat had corrected it to 640; SmartRecruiters before Ashby was written as the measured rule's outcome when the rule ties them; ADR-0050 took a seventh Changes row without the re-read its own guard asks for; and the Working Method's first draft misstated how the Confirmation registry treats a "Live only:" clause. All found by two independent audits and corrected before writing.

**The record index's Changes count**, 92 rows across 40 records as of 2026-09-25, when the corpus held 106 across 41. Found 2026-09-28 by counting every table, which is how the count was derived from then on; done item 116 above, kept as written, claimed the index current on that count.

**The first round of corrections after the audit of 2026-10-04 UTC** rewrote four committed rows and one annotation without a date, which ADR-RULES forbids. Caught and reworked before anything was written: committed text stays, and each correction is a dated note beside it.

---

## One incident worth carrying, not this chat's

A seat reverted two deliberate changes made by the architecture chat rather than flagging them. A later session restored them and recorded the lesson: **reverting another seat's deliberate change is the error, not the caution.** A flag costs a message. An unexplained revert costs the decision, because nobody knows it was ever made.

---

## Rules for this file

Update it in the same message that changes an item's status, never in a catch-up pass. That rule was broken once, between items 58 and 71, and the repair is why this section exists. It was broken again from 2026-09-25 to 2026-10-09, for two weeks, which is why the next rule exists.

**What a brief or report raised is an item here until it is closed.** The file in `briefs/` is overwritten by the next one; this file is not. An item moves to DONE when the report that closes it has been verified, not when it has been read.

When an item moves, it moves rows. It does not get a new number.

A GATED item names its gate in words a later reader can check. "Blocked" is not a gate.

If an item has sat OPEN across three sessions without movement, say so out loud rather than letting it drift into permanent background.

Dates are UTC.
