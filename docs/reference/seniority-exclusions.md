---
type: reference
description: The senior-level title words that drop a posting the title pool admitted, the levels deliberately left in, and the evidence behind the numbered levels.
status: current
---

# Seniority exclusions

Version 1, 2026-09-17.

A posting the title pool admits is still dropped if its title carries one of the words below. The run log counts these drops under the rule name `seniority`, apart from postings the pool never admitted.

**Decided by the operator on 2026-09-17**, who is open to intern, junior, associate, mid-level and untitled roles, the roles a fresh graduate has a realistic chance at. **No decision record carries this rule yet.** It also runs against ADR-0021's "We will maintain no blocklist", which was written about unmatched titles before a seniority rule was wanted. Both are raised with the architecture chat. The operator's instruction outranks the record under ADR-0022.

**This file is versioned.** Every change appends a row to Changes, with its date, so a filter run is reproducible against the list as it stood.

## How the words match

Exactly as title-pool terms do, and with the same normalisation. See `docs/reference/title-pool.md`: lowercase, hyphens and slashes to spaces, commas, parentheses, periods and colons deleted. Words match whole, never inside a longer word, with an optional plural on the last word. So "Sr." matches `sr`, "Team Leads" matches `lead`, and "Staffing", "Headless", "Management" and "Directory" match nothing.

The rule reads the same normalised title the pool reads, and runs after the pool, so a title the pool never admitted is counted as a title drop, not a seniority drop.

## Excluded words

`senior` · `sr` · `staff` · `lead` · `principal` · `head` · `manager` · `director` · `vp` · `vice president` · `chief` · `ii` · `iii` · `iv`

## Deliberately not excluded

**Intern, junior, associate, trainee, graduate, mid-level, and titles with no level word.** These are what the rule exists to keep.

**Level I.** "Software Engineer I" is an entry level and stays.

**Architect.** The operator's decision: architect roles such as AI solutions architects are wanted, and the word names a role more than a level.

## Known behaviour, accepted deliberately

**A senior word anywhere drops the posting**, including where the title also names an entry level. Careem's "Senior Software Engineer I" is dropped; the operator accepted that. So is a title like "AI Engineer, Mid/Senior", which is open to mid-level applicants.

**`lead` drops non-leadership uses too**, such as a lead-generation role. Those are outside the pool's families anyway.

**Level V and "L3"-style levels are not listed.** Neither appeared in the saved postings. Add them when one does.

## Evidence for the numbered levels

The operator asked that `ii` and `iii` be checked before being excluded. From Veeam's saved response of 2026-09-11, which carries descriptions and Workday grades, counting only phrases of the form "N years … experience":

- **Level III.** Five postings, all Workday grade P3. Every one that states a number asks for five years or more: two Software Engineer III roles at eight or more, a software testing role and a security role at five or more.
- **Level II.** Three postings, all grade P2. One states a number, and it is five years or more.
- **Level I.** Two titles matched, and both were "UK&I" in a sales title, not a level. Nothing to learn, and a reminder that a naive match reads "UK&I" as a level.

Both levels ask for more than the operator's reference maximum of three years. The evidence for `ii` is thin: one posting.

Description text is not stored in this repository (ADR-0011). Only the numbers are recorded here.

## Effect when introduced

On the 21 postings kept by production run 35236531478, this list drops 10: both BRKZ "Senior AI Engineer" roles, Motive's "Senior AI Platform Engineer", both CodeRoad "Senior Agentic AI Engineer" roles, Smart Working's "Senior Backend Engineer", the three Veeam "Senior Forward Deployed Engineer" roles, and Careem's "Senior Software Engineer I". Four of the ten were reachable from Pakistan.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | Version 1 created | Decided by the operator: keep roles a fresh graduate can reach, drop senior-level titles. `ii` and `iii` excluded after the evidence check above; `architect` deliberately kept; `iv` added as the next level up |
