---
status: accepted
topic: filtering
description: The seniority word list, running after the title rule, and the clause of ADR-0021 it reverses.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0032: The seniority rule, and the clause of ADR-0021 it reverses

## Context and Problem Statement

The title pool admits a role by name. It cannot tell a role the operator can get from the same role three levels above him. On 2026-09-17, 10 of the 21 rows the pool kept were senior-level titles, four of them reachable from Pakistan, which is where the operator was looking.

The operator decided on 2026-09-17 to exclude senior-level title words, and the rule was implemented on his instruction, which outranks the records under ADR-0022. It has run since without a record carrying it. This is that record.

**It reverses one clause of ADR-0021**, which says at line 50 *(line 52 since `dc02b0f` added two frontmatter lines on 2026-09-18)*: "We will maintain no blocklist. It is unnecessary once unmatched rows are dropped." That sentence was written about a different problem. ADR-0008 had an unmatched bucket that a blocklist existed to clean up; ADR-0021 removed the bucket, so the blocklist had nothing to do. A seniority rule was not wanted then and is not what that clause was about.

The word list is fourteen words: `senior`, `sr`, `staff`, `lead`, `principal`, `head`, `manager`, `director`, `vp`, `vice president`, `chief`, `ii`, `iii`, `iv`. `architect` and level I are deliberately kept. *(2026-10-16: `senior` leaves the list by the operator's decision, and `sr` with it on the chat's reading of the same word, so twelve words remain. See Changes.)*

## Decision Drivers

- The operator is looking for roles a fresh graduate can realistically get: intern, junior, associate, mid-level and untitled.
- A drop must name the word that caused it, so the operator can see why a row vanished and change the file.
- The rule must sit where it does not destroy the drop log's meaning as the record of titles the pool is missing.
- Nothing about this is a judgement the machine makes.

## Assumptions

- Numbered levels II and III sit above the operator's reach. **Measured**, thinly: against saved Veeam descriptions, level III asks for 5 to 8 or more years, and the single level II posting that states a number asks for 5 or more. That is one posting for II, recorded as such in `docs/reference/seniority-exclusions.md`.
- `iv` behaves like `ii` and `iii`. **Not measured.** Included as the next level up by the operator's decision.
- Title words track actual seniority. **Contradicted in one direction** and accepted: Careem's "Senior Software Engineer I" is a senior word on an entry-level rung, and is dropped. *(Since 2026-10-16 it is not: `senior` is off the list and the description decides it. See Changes.)* The Veeam board separately carries five P1 postings titled "Senior".

## Considered Options

- No seniority rule, and the operator skims senior rows in the display.
- A seniority rule before the title rule.
- A seniority rule after the title rule.
- Wait for a record before implementing.

## Decision Outcome

Chosen option: "a seniority rule after the title rule".

**A rule running immediately after the title rule drops a posting whose title contains any word in the operator's seniority list.** The drop names the word. The list lives in `docs/reference/seniority-exclusions.md` with its own change log, which is ADR-0031's shape. *(Extended 2026-10-02: where a source states a posting's level, that statement is a second signal for the same question. See Changes.)* *(Narrowed 2026-10-16: neither the word Senior (or `sr`) in a title nor a stated level of Senior drops a posting any longer, and ADR-0058's description rules decide it. See Changes.)*

**ADR-0021's line 50 *(line 52 since `dc02b0f` added two frontmatter lines on 2026-09-18)* is reversed in this respect only.** A blocklist that deletes rows on a machine's judgement of category is still rejected, and nothing here reinstates one. What this record permits is narrower and different in kind: a list of words about the operator's own level, owned by him, in a file he edits, applied by a rule that names its match. ADR-0031 records why that is configuration rather than judgement.

**Order matters and is part of the decision.** Placing it before the title rule would make the `seniority` count mean "every senior posting on every board" rather than "relevant roles excluded for level", and would empty the title drop log of its meaning as the record of titles the pool is missing.

**ADR-0021's Confirmation is not invalidated.** That was expected and is wrong. The case set was run against the current chain on 2026-09-17 and all eight cases produce the verdict the record requires:

| Case | Required | Actual |
|---|---|---|
| AI-Agent Engineer | match | admitted, `ai agent` |
| Agentic Systems Engineer | match | admitted, `agentic` |
| Storage Engineer | no | dropped, title, no term matched |
| Senior Red Team Operator | no | dropped, title, no term matched |
| Accounts Officer | no | dropped, title, no term matched |
| Sales Executive, Healthcare IT | no | dropped, title, no term matched |
| **Software Engineer II** | **no** | **dropped, seniority** |
| Non-AI Systems Analyst | the one to watch | admitted, `ai system` |

What changed for "Software Engineer II" is the mechanism, not the verdict: the pool now matches it and the seniority rule drops it, where before no term matched. The record's Confirmation asks for a verdict and gets it. ADR-0021 carries a Changes row saying so, and the case set stays as written because it still discriminates.

**"Non-AI Systems Analyst" is admitted**, which ADR-0021 named as the one to watch. It is a live false positive, caused by normalisation folding the title to "non ai systems". It is recorded, not fixed here.

### Consequences

Roles the operator cannot get stop reaching the display, at the cost of dropping any senior-titled role he could in fact get. On 2026-09-17 data that trade cost 10 of 21 rows. *(Since 2026-10-16 a title with Senior is no longer dropped for it, and the description's years decide; the other words still carry this cost. See Changes.)*

The rule inverts when the operator's experience does. Because the list is configuration with a change log, that is a file edit and a dated row, not a code change.

A row dropped for seniority never enters the filtered layer, so widening the list later is subject to ADR-0030's backfill, and narrowing it is not. *(Questioned 2026-10-16 by the architecture chat, which reads this as reversed: narrowing admits postings dropped before, which is what ADR-0030's backfill adds. Put to the implementing seat in Brief 12; not corrected until it answers.)* *(Wrong when written, confirmed 2026-10-16 by the seat from `src/backfill.py`: narrowing the list admits postings dropped before, and the backfill adds them, 130 for the Senior change; widening it adds nothing, and ADR-0040 hides the stored rows a wider list drops.)*

`filtered.json` holds rows kept before this rule existed. They stay, per ADR-0030.

Careem's "Senior Software Engineer I" is dropped although it is an entry-level rung. The operator accepted this when he chose the words. *(Stale since 2026-10-16: with `senior` off the list, such a title reaches the description rules. See Changes.)*

### Confirmation

The case set above runs before any change to the seniority list, and every case must produce its stated verdict with the deciding rule named.

The rule is proved by the case built to defeat it: a title containing a seniority word that the pool does not match must be dropped by the **title** rule, not the seniority rule, or the order has been reversed. "Senior Red Team Operator" is that case and is dropped by title. *(Stale since 2026-10-16: with `senior` off the list, this title carries no word the rule reads, so it no longer tests the order. It is replaced by a title carrying a word still on the list that the pool does not match, chosen and proved by the implementing seat, Brief 12.)* *(2026-10-16: "Principal Red Team Operator", `4316e06`, which carries `principal` and matches no pool term, caught by the recorded mutation that runs seniority before the title rule.)*

Within two weeks of the display existing, count `rejected_pipeline` *(now `rejected-poor-filtering`: the operator's rename of 2026-09-24, in the base from 15:30Z; ADR-0046's `poor filtering` never reached it. Corrected after that day's audit, F12, which found this note saying "renamed by ADR-0046 and again by the operator")* rows with reason `experience level`. A cluster means the list is wrong in one direction; the operator finding senior roles he wanted and never saw means it is wrong in the other, and only the display can show that.

## Pros and Cons of the Options

### No rule, skim in the display

Good, because it keeps ADR-0021 untouched and loses nothing.
Bad, because half the display was roles the operator cannot get, which is the cost the display exists to remove.

### Wait for a record before implementing

Good, because the record would have preceded the behaviour, as this project requires.
Bad, because it makes the operator wait on an architecture discussion for a decision that is entirely his, which the project's protocol explicitly places with him.

## More Information

Reverses ADR-0021 line 50 *(line 52 since `dc02b0f` added two frontmatter lines on 2026-09-18)* in this respect only, and is linked from ADR-0021's Changes.

ADR-0031 supplies the frame: preferences are configuration.

The evidence for the numbered levels, the words, and the reasons `architect` and level I stay are in `docs/reference/seniority-exclusions.md`.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-24 | Three references to ADR-0021's line 50 annotated as line 52, and the status name annotated | `dc02b0f` added two frontmatter lines to every record on 2026-09-18, moving every cited line down by two. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
| 2026-10-02 | *(Since 2026-10-16 a stated Senior is kept too; see that row.)* A source's stated level is read beside the title. A posting is kept when any level it states is entry-level or mid-level, and dropped when every stated level is above; a posting stating none is kept. The title rule still runs, so a stated level never rescues a title this rule drops. The levels are configuration. Only Himalayas states one | The operator's decision, "keep till mid", option A, so a posting labelled both mid and senior is kept. The same question this record answers from the title, answered from a field: Himalayas labels every posting, and 35 of the 67 it kept were Senior or above. Measured over the 809 saved Himalayas postings, 67 kept before and 34 after. Rows stored before the rule keep their verdict and leave on the thirty-day clock (ADR-0040) |
| 2026-10-09 | *(Its last sentence is replaced by the 2026-10-10 row below.)* The levels Workable and SmartRecruiters state are read the same way: Workable's `experience` where a posting carries it, and SmartRecruiters' `experienceLevel`, which every posting carries. Entry level is kept, and so is Mid-Senior level, for now. A stated value this row does not name, Internship among them, is reported with its count and put to the operator before it is configured | The operator's answer of 2026-10-09 UTC, asked by the implementing seat after both platforms were found to state levels (its report on Brief 10): "yes, the levels are good enough i.e. mid-senior should be accepted for now." A single label spanning mid and senior is kept, as option A keeps a posting labelled both. Measured by the seat on 2026-10-04: SmartRecruiters' two boards stated entry 9, internship 6, mid-senior 4 and executive 1; Workable stated `experience` on some postings. "For now" makes it revisable on his word, with no trigger set |
| 2026-10-10 | *(Its "up to mid" reads "up to Senior", and its "above mid" "above Senior", for a stated level since 2026-10-16; see the row below.)* One rule for every source's stated level, so no source's wording is put to the operator again: every level from the start of a career up to mid is kept, whatever a source calls it (internship, entry, junior, associate, mid, mid-senior and the like); a posting whose every stated level is above mid is dropped; a posting stating none is kept, and so, on the architecture chat's reading of his purpose, is one stating a value that names no level. Each source's values are mapped by this rule when its adapter is built, and the mapping is logged. The previous row's clause putting unnamed values to him is replaced | The operator's answer of 2026-10-10 UTC: "yes, internship is included for every platform/source. it should not be like that you or the seat asks again and again for every source as till the mid level or mid position meaning this might constitute to the 3 or 3+ years then everything till this position from start position is to be kept, no matter what the wording is like entry or associate and so on. this rule is just here so that no job skips my sight that i am eligible for." Option A of 2026-10-02 already kept anything up to mid; this states it for every source and every wording, and the years asked stay ADR-0058's to judge |
| 2026-10-16 | Senior no longer drops a posting by itself. The word `senior`, and `sr` with it, leaves the title list, and a stated level of Senior, on any source, is kept like every level up to mid. Every other word on the list still drops, so "Senior Manager" still goes on `manager`, and every stated level above Senior (manager, director, executive and the like) still drops. A Senior posting then meets ADR-0058's description rules: more than three years asked drops it, and a line opening it to graduates sets no minimum. One with no description is kept, by ADR-0058's Consequences, and each such case is made visible to him, the chat's reading of his "we will check later when it arises". Before it is switched on, the implementing seat counts over the saved postings how many more rows it admits, including any the backfill would add at once. The Confirmation's order case used a Senior title and is replaced by one carrying a word still on the list | The operator, 2026-10-16 UTC, on the stated level (the chat's ledger, item 145): "do not drop but rather take away senior meaning let in up to senior but the manager and director or executive are still filtered and remove and the description will check and do the filtering as the given rules meaning what we have decided." Asked whether the word in a title should still drop: "no, if there is senior written in title then it should not drop until the description is read and if description is unavailable then that is one thing that we will check later when it arises." His note, pasted 2026-10-10, gave the reason: a posting labelled Senior may ask for no years, and the description's years are the better evidence. `sr` is read as the same word, the chat's reading, put to him without objection. The resume-tailoring chat argued against the change on 2026-10-16 from the 8 senior-labelled rows it had reviewed, none viable after reading and 6 stating no years (its count; n = 8), and proposed a measure: Senior rows kept, and how many he accepts, over two weeks. *(Adopted by the operator the same day: "it is correct to check for 2 weeks." The two weeks run from the day the change is switched on, the chat's reading.)* *(Counted 2026-10-16 by the seat over 4,840 saved postings: about 15 more rows a week, all Himalayas, since every Senior posting on the employer boards asks more than three years; a backfill of 130 at once. Switch-on: of three options put to him that day he chose (b), "b", once stored rows' facts are re-read from their saved postings, ADR-0040's Changes, so the backfill adds only what today's reader passes; the date, November 1 or sooner if the allowance shows room, is the chat's recommendation that came with it. The level rule's configuration becomes a list of the levels that drop.)* *(Built 2026-10-17 and switched off: the level rule names the levels that drop, `stated_levels_dropped` in `config/eligibility.json`, Senior among them until the switch-on, so a value it does not name is kept (`40a54b2`); Workable's `experience` read; the description's four fields and the no-description count built (`a363ed5`). The switch-on is one commit from November 1: `senior` and `sr` leave `docs/reference/seniority-exclusions.md` with a change-log row, Senior leaves `stated_levels_dropped`, and the description fields are turned on; the next run re-reads, backfills what today's reader passes and re-sends every `Jobs` row once, about 30 calls by the seat's estimate. The implementing seat's report on Brief 13.)* A narrowing, not a supersession: the rule stands for twelve words and for every level above Senior |
