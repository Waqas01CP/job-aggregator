---
type: state
description: The architecture chat's ledger. What was raised, what is waiting and on what, and the errors this chat made. Read at the start of a new architecture chat.
status: current
---

# CHAT_STATE

The architecture chat's ledger. **`STATE.md` is the project's state; this is the conversation's.**

It exists because items raised in a chat and not written down are forgotten the moment the chat moves on. Four such items nearly vanished before this file existed.

**Read this at the start of a new architecture chat**, alongside the behavioural prompt that chat is initialised with. This file carries what was decided and what is waiting. The prompt carries how the chat works, which cannot live in a repository file because it is about the conversation rather than the project.

Brought to final form 2026-09-18, at the close of the first architecture chat.

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
| 61 | Create the Airtable PAT and four repository secrets | **The single largest blocker. Six decided things sit behind it.** Scopes and secret names are in `STATE.md`'s Blocked section |
| 73 | Read the seat's brief 4 response | The only outstanding input. Covers ADR-RULES' audit, the record index verification, the four Airtable tables, the classification flow, the deferred register and the heredoc mechanism |
| 63 | Verify the record index against the records themselves | Eight statuses were reconstructed from session reports. Assigned to the seat in brief 4 |
| 74 | Decide question C | Whether aggregator rows may be written to the private Airtable base. The only route by which Himalayas' kept rows reach the operator, since on a runner they persist nowhere |

## Gated

| # | Item | Gated on |
|---|---|---|
| 64 | The Airtable writer and the weekly sweep | Item 61 |
| 65 | ADR-0043's three outcome stores | Item 61. Recorded, not built |
| 66 | ADR-0044's star has no caller | Item 61. The projection does not exist |
| 67 | ADR-0040's projection filter | Item 61 |
| 68 | ADR-0038's family views | Item 61. The label exists; the views do not |
| 69 | ADR-0041's structured location half | A reachability field on the row and in the Airtable schema, neither of which exists |
| 56 | Set the real fetch ceiling from measurement | A month of run logs. Every run so far has spent 36 requests against a provisional ceiling of 500 |
| 70 | Every unread field in `platform-fields.md` | Each needs a decision about what it means and what its absence means. Himalayas returns `seniority` on 100% of postings while ADR-0032 infers it from title words |
| 20 | Rozee.pk as a source | Needs a record. robots.txt permits the job paths, the terms carry no automated-access clause, and a sitemap publishes job URLs daily with the title in the slug |
| 21 | Description matching | Deferred by ADR-0016. Field coverage is now measured |
| 22 | Deduplication across source classes, employer alias map | A second source class in production |
| 23 | End-state document | Operator's decision. No prior art in either project |
| 24 | In-flight register separate from `STATE.md` | Work being in flight |
| 25 | Second private repository for aggregator data | A reason to spend the effort |
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
| 59 | Brief 4 sent | Classification flow, deferred register, ADR-RULES audit |
| 60 | Airtable base moved to the connected account | Seat rebuilds four tables |
| 62 | This file committed | Removed from `.gitignore` and from the generator's skip list |
| 71 | ADR-RULES written | Awaiting the seat's audit |
| 72 | Record index restored | Fell fifteen records behind; repaired 2026-09-18 |
| 76 | Similarity matching decided against, for now | ADR-0044's deterministic star instead, with its trigger in `docs/deferred/` |
| 77 | Deletion flow decided | Manual classification, timestamped deletion from the two rejection tables, accepted deleted by hand only |

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

**Letting the record index fall fifteen records behind** while maintaining the rule that a second copy of a fact is a defect.

---

## Rules for this file

Update it in the same message that changes an item's status, never in a catch-up pass. That rule was broken once, between items 58 and 71, and the repair is why this section exists.

When an item moves, it moves rows. It does not get a new number.

A GATED item names its gate in words a later reader can check. "Blocked" is not a gate.

If an item has sat OPEN across three sessions without movement, say so out loud rather than letting it drift into permanent background.
