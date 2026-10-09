---
status: accepted
topic: filtering
description: The description is read once, at fetch, for three derived facts: the years of experience asked, the places a right to work is required in, and whether the role is on site. Only the derived values are kept on the row; the text stays private. Builds the experience rule ADR-0016 deferred.
date: 2026-10-03
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0058: The description is read once, at fetch, and only what is derived is kept

## Context and Problem Statement

Every filter until now read the title and the location. The description was deferred by ADR-0016 until its coverage was known, and ADR-0011 kept it off the public branch. ADR-0051 then began saving every posting whole on a private branch, for exactly the day the description would be needed.

That day came on 2026-10-02. The operator, in his words: "high time that we use the description", for three things that stop him applying even when a posting passes every other rule: the years of experience asked, a requirement to hold a right to work somewhere he cannot, and a role that is on site although its location field does not say so.

Measured over the postings saved whole: no source gives years of experience as a field. A number of years appears in the description on 53% of Greenhouse postings, 67% of Lever's and 50% of Himalayas'. On Lever, 50 of 63 postings state their years in `lists` and only 4 in `description`, so "the description" means every text field a source gives, not one.

Three tensions. The text is the employer's, and some of it is personal, so it cannot be republished. A pattern that misreads a sentence drops a job silently. And a rule that reads text invites the next rule to store the text it read.

## Decision Drivers

- Each requirement named is one the operator has said stops him, so leaving them unread shows him jobs he cannot take.
- Nothing he can take may be lost to a misreading, so every pattern fails toward keeping.
- The employer's words never reach the public branch, in any form.
- Every rule is named and deterministic (ADR-0010).

## Assumptions

- Phrase patterns read these three facts well enough to act on. **Measured** before the rules were switched on, over the 1,708 postings on the private full branch: of the 50 that pass every rule but age, 7 now drop, 6 for asking five or more years and 1 Lahore role whose description says it is on site, and none is newly kept.
- Three years is the most he will consider. **Stated** by the operator: "the most it can say is 3+ and not 4+ years like 3 or 3+ is the max accepted years".
- A preferred figure counts like a required one. **Stated**: "5+ years preferred is already out since the max is 3 or 3+ years".
- A line welcoming fresh graduates sets no minimum, and a posting asking 0 to 1 years with 3 preferred passes. **Stated** on 2026-10-03: "must be 0-1 years experience or a bachelors required and in preferred says 3+ or 3 years ... then this is a pass already".

## Considered Options

- Keep deferring, and read titles and locations only.
- Store the description on the row and match against it at projection.
- Read the description once at fetch, keep only derived values, and leave the text on the private branch.
- A model that reads the description.

## Decision Outcome

Chosen option: "read the description once at fetch, keep only derived values, and leave the text on the private branch".

**We will read every text field a source gives, once, when the posting is fetched**, with deterministic phrase patterns.

**We will keep three derived values on the row and nothing else from the text**: the years figures it states; the configured names of the places it requires a right to work, citizenship or residence in; and a flag that it says the role is on site. The text stays on the private full branch under ADR-0051.

**We will drop a posting that asks for more than three years**, required or preferred. A range counts by its low end. A line welcoming fresh graduates sets no minimum. `max_years_experience` is configuration. This rule runs after the level rule, so its count is of relevant roles.

**We will hand the other two values to ADR-0057**, which decides eligibility from them: the required places by its authorisation rule, and the on-site flag as a stated workplace.

**We will measure each pattern over every saved description before switching it on**, and report what it would drop and what it would newly keep.

**We will describe a description's sentence, never quote it, in anything committed.** Tests, comments, logs and records carry sentences written to the same shape instead. The implementing seat set this on 2026-10-03 after finding employer sentences in its own committed work, and it binds every seat.

### Consequences

ADR-0016's deferred experience rule is built, nine days after ADR-0051 kept the data for it.

The derived values sit on the public branch for Greenhouse and Lever rows. ADR-0011 is clarified rather than changed: a value from a closed vocabulary, a number, a configured place name or a flag, is metadata, and cannot carry an employer's words.

A posting whose description is missing, truncated or unreadable yields no derived values, and is kept.

A pattern that misses a phrasing keeps a job he cannot take. A pattern that misreads drops one he can, which is why each is measured before it is switched on and why "no visa sponsorship" is excluded by name.

Rows stored before these rules carry none of the derived values, so they keep their verdict and leave by the thirty-day clock (ADR-0040).

### Confirmation

**No derived value may be anything but a number, a configured place name or a flag.** A test asserts the type and vocabulary of each, and the commit guard refuses description text on the public branch. *(Annotated 2026-10-04, wrong when written: the guard did not exist; built 2026-10-03, commit `eb0134e`. See Changes.)*

**The experience rule's edges**: a range by its low end; preferred counted like required; a fresh-graduate line setting no minimum; 0 to 1 required with 3 preferred passing; 4 or more dropping.

**"No visa sponsorship" must never set a required place.**

**A posting with no description must be kept.**

**Live only:** each new pattern's measurement over the saved descriptions, reported before it is switched on.

## Pros and Cons of the Options

### Keep deferring

Good, because nothing can be misread.
Bad, because he named three requirements that stop him and the table would keep showing them.

### Store the description on the row

Good, because any later rule could read it without a fetch.
Bad, because Greenhouse and Lever rows are public, so it would republish employers' text, which ADR-0011 exists to prevent.

### A model reading the description

Good, because it would follow phrasing no pattern anticipates.
Bad, because ADR-0010 excludes model-based screening, and a drop he cannot trace to a named phrase is one he cannot check.

## More Information

ADR-0016 deferred this and carries a pointer here. ADR-0051 keeps the text this reads. ADR-0011 governs what may be public, clarified in its Changes. ADR-0057 decides eligibility from two of these values. ADR-0032 answers level, which is a different question from years.

The operator's decisions: reading the description, 2026-10-02; the three-year limit and preferred counting, 2026-10-02; fresh graduates, citizenship and security clearance, 2026-10-03.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | The commit guard this record's Confirmation names is built, in `storage.commit_files` | Written as though it existed; it did not. Found and built by the implementing seat the same evening on the operator's yes. ADR-0051's Changes carry the detail |
| 2026-10-04 | The Confirmation's first clause annotated as wrong when written: it named a commit guard that did not exist until 2026-10-03 | From the implementing seat's report on Brief 9. The row of 2026-10-03 records the build; this one records the annotation |
| 2026-10-09 | The on-site patterns widened for the shapes Manatal's postings use, measured over every saved description before switching on: 34 postings newly read as on site, none lost, none in the display at the time | ADR-0057's on-site rule depends on them. Built as commit `ae170fa` on 2026-10-07 UTC |
