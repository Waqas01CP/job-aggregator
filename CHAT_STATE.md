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

---

## What this project is, in one paragraph

A scheduled pipeline that polls employer ATS job boards and one aggregator, deduplicates, filters against a versioned title pool, and writes what survives to Airtable for the operator to review. Its purpose is hours returned, not roles found: job discovery was consuming the majority of a working week, and the reachable pool is roughly one qualifying role per six months, which the pipeline cannot change and is not built to. Its only binding success measure is Measure A, in ADR-0015: the median gap between a posting's publication date and its first appearance in the display, at or under 24 hours.

## Three seats, and what each does

**The operator** decides scope, cost, and anything about roles, titles or what he is reachable for. He relays between the other two and is not a relay for questions either could answer directly.

**The architecture chat**, this one, concludes decisions, writes records, writes briefs, and checks what comes back. It does not implement.

**The implementing seat**, Claude Code, executes briefs, writes code and tests, writes session logs, and audits. It decides method, structure and tooling. It stops and hands back when an answer would change what the project is.

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
| What was found and when | `docs/research/` |
| What was deliberately not done, and its trigger | `docs/deferred/` |

---

## Status meanings

**DONE** with a pointer. **GATED** with the gate named in checkable words. **OPEN** with nothing blocking it.

Items keep their number forever and move rows rather than being renumbered.

---

## Open

| # | Item | Notes |
|---|---|---|
| 97 | Brief 5, the projection | Written 2026-09-22 in the architecture chat, not sent. It carries the corrections notice for the seat as its first section. Waits on the operator's approval of its four decisions: A, a failed projection exits 2 so the push still happens; B, aggregator rows are projected before the private stores exist; C, a group's identity is its representative's and the skip tests every member; D, family labels and the star are part 2 |
| 88 | `Status` carries three choices, by hand | `not fit`, `poor filtering`, `accepted`. **`expired_before_review` is retired**, 2026-09-23, so all four values as built can be deleted: no row carries one. The connector cannot add a choice to an existing field, so this is the operator's, in the browser. Step 4 of `docs/how-to/airtable-token-and-secrets.md`. Checked through the connector 2026-09-23: still the four old values on both tables. **The sweep cannot be built until they exist** |
| 89 | The private aggregator store | `Waqas01CP/job-aggregator-store` created 2026-09-23 with a fine-grained token, and `AGGREGATOR_STORE_TOKEN` is in the repository secrets. **Outstanding: `AGGREGATOR_STORE_REPO` as a second secret**, value `Waqas01CP/job-aggregator-store`. The name is kept out of the public repository deliberately, per ADR-0011 |
| 81 | Himalayas and Banyan Canopy | Both deferred by the operator 2026-09-23 until the writer runs and he has seen rows in `Jobs`. Review no earlier than **2026-10-07**. Himalayas additionally needs item 89's repository name, because ADR-0047 fails a run that cannot write the private store. Evidence so far: Himalayas keeps 11 to 31 rows a run and loses every one; Banyan Canopy has returned the same six finance postings on all thirteen runs, admitted none, and the one AI-adjacent posting of 2026-09-11 is gone |

## Gated

| # | Item | Gated on |
|---|---|---|
| 64 | The Airtable writer and the **daily** sweep | The writer is unblocked and deliberately not started. The sweep additionally needs item 88 |
| 65 | ADR-0043's three outcome stores | The writer. Recorded, not built |
| 66 | ADR-0044's star has no caller | The writer. The projection does not exist |
| 67 | ADR-0040's projection filter, including ADR-0046's stored-outcome skip | The writer |
| 68 | ADR-0038's family views | The writer. The label exists; the views do not |
| 69 | ADR-0041's structured location half | A reachability field on the row and in the Airtable schema, neither of which exists |
| 56 | Set the real fetch ceiling from measurement | A month of run logs. Every run so far has spent 36 requests against a provisional ceiling of 500 |
| 70 | Every unread field in `platform-fields.md` | Each needs a decision about what it means and what its absence means. Himalayas returns `seniority` on 100% of postings while ADR-0032 infers it from title words |
| 20 | Rozee.pk as a source | Deferred, `docs/deferred/rozee-pk.md`. The trigger is three conditions, the real one being whether the Karachi gap is still visible after ADR-0029's five adapters. Access questions already answered there so nobody re-investigates them |
| 21 | Description matching | Deferred by ADR-0016. Field coverage is now measured |
| 22 | Deduplication across source classes, employer alias map | A second source class in production |
| 23 | End-state document | Operator's decision. No prior art in either project |
| 24 | In-flight register separate from `STATE.md` | Work being in flight |
| 26 | Reuse boundary against the LinkedIn pipeline | One session, component by component |
| 27 | Which skills the project gets | Nothing technical |
| 28 | AGENTS.md symlink for Antigravity | Only matters if Antigravity is used here |
| 46 | Lever in or out of the slice | **Answering itself.** 11 of 11 Greenhouse and 2 of 2 Lever postings were dated after the run that missed them |
| 75 | Adapter order execution | ADR-0029 fixes it: Ashby, Workable, SmartRecruiters, Breezy, Manatal. Waiting on the slice proving itself |

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
| 95 | A `Stage` changed after day 15 | Closed 2026-09-23: accepted as it stands. The store keeps the value the copy held on day 15 and nothing reads the difference. Revisit when the accepted-prune tool is built. Both values live in the `accepted` table; two views by hand separate them |

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

---

## One incident worth carrying, not this chat's

A seat reverted two deliberate changes made by the architecture chat rather than flagging them. A later session restored them and recorded the lesson: **reverting another seat's deliberate change is the error, not the caution.** A flag costs a message. An unexplained revert costs the decision, because nobody knows it was ever made.

---

## Rules for this file

Update it in the same message that changes an item's status, never in a catch-up pass. That rule was broken once, between items 58 and 71, and the repair is why this section exists.

When an item moves, it moves rows. It does not get a new number.

A GATED item names its gate in words a later reader can check. "Blocked" is not a gate.

If an item has sat OPEN across three sessions without movement, say so out loud rather than letting it drift into permanent background.
