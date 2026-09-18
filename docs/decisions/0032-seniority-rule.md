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

**It reverses one clause of ADR-0021**, which says at line 50: "We will maintain no blocklist. It is unnecessary once unmatched rows are dropped." That sentence was written about a different problem. ADR-0008 had an unmatched bucket that a blocklist existed to clean up; ADR-0021 removed the bucket, so the blocklist had nothing to do. A seniority rule was not wanted then and is not what that clause was about.

The word list is fourteen words: `senior`, `sr`, `staff`, `lead`, `principal`, `head`, `manager`, `director`, `vp`, `vice president`, `chief`, `ii`, `iii`, `iv`. `architect` and level I are deliberately kept.

## Decision Drivers

- The operator is looking for roles a fresh graduate can realistically get: intern, junior, associate, mid-level and untitled.
- A drop must name the word that caused it, so the operator can see why a row vanished and change the file.
- The rule must sit where it does not destroy the drop log's meaning as the record of titles the pool is missing.
- Nothing about this is a judgement the machine makes.

## Assumptions

- Numbered levels II and III sit above the operator's reach. **Measured**, thinly: against saved Veeam descriptions, level III asks for 5 to 8 or more years, and the single level II posting that states a number asks for 5 or more. That is one posting for II, recorded as such in `docs/reference/seniority-exclusions.md`.
- `iv` behaves like `ii` and `iii`. **Not measured.** Included as the next level up by the operator's decision.
- Title words track actual seniority. **Contradicted in one direction** and accepted: Careem's "Senior Software Engineer I" is a senior word on an entry-level rung, and is dropped. The Veeam board separately carries five P1 postings titled "Senior".

## Considered Options

- No seniority rule, and the operator skims senior rows in the display.
- A seniority rule before the title rule.
- A seniority rule after the title rule.
- Wait for a record before implementing.

## Decision Outcome

Chosen option: "a seniority rule after the title rule".

**A rule running immediately after the title rule drops a posting whose title contains any word in the operator's seniority list.** The drop names the word. The list lives in `docs/reference/seniority-exclusions.md` with its own change log, which is ADR-0031's shape.

**ADR-0021's line 50 is reversed in this respect only.** A blocklist that deletes rows on a machine's judgement of category is still rejected, and nothing here reinstates one. What this record permits is narrower and different in kind: a list of words about the operator's own level, owned by him, in a file he edits, applied by a rule that names its match. ADR-0031 records why that is configuration rather than judgement.

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

Roles the operator cannot get stop reaching the display, at the cost of dropping any senior-titled role he could in fact get. On 2026-09-17 data that trade cost 10 of 21 rows.

The rule inverts when the operator's experience does. Because the list is configuration with a change log, that is a file edit and a dated row, not a code change.

A row dropped for seniority never enters the filtered layer, so widening the list later is subject to ADR-0030's backfill, and narrowing it is not.

`filtered.json` holds rows kept before this rule existed. They stay, per ADR-0030.

Careem's "Senior Software Engineer I" is dropped although it is an entry-level rung. The operator accepted this when he chose the words.

### Confirmation

The case set above runs before any change to the seniority list, and every case must produce its stated verdict with the deciding rule named.

The rule is proved by the case built to defeat it: a title containing a seniority word that the pool does not match must be dropped by the **title** rule, not the seniority rule, or the order has been reversed. "Senior Red Team Operator" is that case and is dropped by title.

Within two weeks of the display existing, count `rejected_pipeline` rows with reason `experience level`. A cluster means the list is wrong in one direction; the operator finding senior roles he wanted and never saw means it is wrong in the other, and only the display can show that.

## Pros and Cons of the Options

### No rule, skim in the display

Good, because it keeps ADR-0021 untouched and loses nothing.
Bad, because half the display was roles the operator cannot get, which is the cost the display exists to remove.

### Wait for a record before implementing

Good, because the record would have preceded the behaviour, as this project requires.
Bad, because it makes the operator wait on an architecture discussion for a decision that is entirely his, which the project's protocol explicitly places with him.

## More Information

Reverses ADR-0021 line 50 in this respect only, and is linked from ADR-0021's Changes.

ADR-0031 supplies the frame: preferences are configuration.

The evidence for the numbered levels, the words, and the reasons `architect` and level I stay are in `docs/reference/seniority-exclusions.md`.
