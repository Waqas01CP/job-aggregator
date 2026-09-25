---
status: accepted
topic: filtering
description: Location admits on any signal or on none and drops only on an explicit exclusion; keywords tag reachability and never reject.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0041: Location admits unless a source excludes, and keywords only tag

## Context and Problem Statement

Location filtering was deferred when the pipeline was built. **No record says
so.** The consequences of that gap have been found one at a time: the
architecture document listed a location filter in the chain that the code has
never had, ADR-0001's Confirmation named that filter and so could not be run,
and a session justified the deferral with a reason that turned out to describe
harvested data from another project rather than this pipeline.

The deferral itself was right. The reason it was right is visible in the data.
Stored location text for one city reads "Karachi, Pakistan", "Karachi, Sindh,
Pakistan", "Pakistan - Karachi", "Karachi", and semicolon-separated lists.
Greenhouse returns one free-text string. A matcher built on that text would
drop real roles on spelling, and a dropped row never reaches the display to be
argued with.

Meanwhile the operator's actual constraint is not a place. It is whether he
can be hired for the role from Pakistan, which most postings never state, and
which one source states outright: Himalayas returns `locationRestrictions`, a
country allowlist, on 82.9% of its postings.

## Decision Drivers

- A false drop is invisible and permanent in the display; a false admit costs
  one line of the operator's attention. The costs are not symmetrical and the
  rule should not pretend they are.
- The operator is open to remote work worldwide provided it can be done from
  Pakistan, so "not in Pakistan" is not a reason to drop anything.
- Free text varies by board. Structured fields do not.
- The deferral needs a record whether or not a rule replaces it.

## Assumptions

- Most postings state no eligibility restriction at all. **Measured** on
  Himalayas: 17 of 91 carry an empty restriction list. **Not measured** on the
  ATS boards, which expose no eligibility field, so absence there is the
  normal case by construction rather than by observation.
- Explicit exclusions are mostly in description text. **Believed, not
  measured.** No description text has been searched for exclusion phrasing,
  because ADR-0016 defers description matching and ADR-0011 keeps descriptions
  off the branch.

## Considered Options

- Keep deferring, and record only the deferral.
- Match a location allowlist and drop everything else.
- Admit unless a source explicitly excludes, and tag reachability.

## Decision Outcome

Chosen option: "admit unless a source explicitly excludes, and tag
reachability".

**The deferral is recorded and now closed.** Location filtering was deferred
at the build with no record; this record supersedes that silence.

**The rule. A posting is admitted on any location signal, or on none.** A
location string, a remote flag, a country, an empty field, a missing field:
all admit. **A posting is dropped only on an explicit exclusion**, meaning a
statement by the source that the operator is not eligible:

- a structured country allowlist that does not include Pakistan, which is
  Himalayas' `locationRestrictions`;
- an explicit statement such as "US only", or "must be authorised to work in
  X" for an X that is not Pakistan.

**Keywords never reject.** Normalised location keywords tag a row's
reachability and nothing more. A tag orders and groups the display; it never
removes a row. *(Narrowed 2026-09-25: a tag may filter or group a view and
never order one. Ordering is by date alone. See Changes.)* This is the part of the rule that must not drift: the moment a
keyword drops a row, the rule has become the location matcher this record
rejected, and it will drop "Karachi, Punjab, Pakistan" for being misspelled.

**Use the structured field wherever a source provides one**, per
`docs/reference/platform-fields.md`. Himalayas' `locationRestrictions` today;
Lever's `workplaceType` and `country`, both 100% populated and both currently
unread; Ashby's `isRemote`; Workable's `telecommuting`.

**What is buildable now, and what is not.** The structured half is buildable
today. The text half is not: "US only" lives in description text, which
ADR-0016 defers and ADR-0011 keeps off the public branch. **The rule is
recorded in full so that the text half is implemented to this rule when
description filtering arrives, rather than being designed again from
scratch.**

**What it would do today.** On the 91 saved Himalayas postings, 74 carry a
list that does not name Pakistan and would be dropped; 17 carry an empty list
and would be admitted. On every ATS board in the slice, nothing is dropped,
because none exposes an eligibility field.

### Consequences

The display keeps every posting whose eligibility is unstated, which is most
of them, and the operator judges those himself. That is deliberate: the
alternative silently loses roles.

Himalayas becomes considerably more useful, since 74 of 91 of its postings
are ones the operator cannot take, and the pipeline can now say so from the
source's own field rather than from a guess about text.

A reachability tag needs somewhere to live: a field on the row, and a field
in the Airtable schema, which currently has neither. That is a schema change
and a normaliser change, and it is not made by this record.

The rule's text half is unimplementable until descriptions are read, so a
posting saying "US only" in its description is admitted until then. Recorded
rather than hidden.

`docs/architecture-2.0.md` no longer lists a location filter in the chain.
When the structured half is built, the chain gains a rule named for what it
does, which is eligibility, not location.

### Confirmation

The existing case set must keep passing, and it is the case built to defeat
this rule: "Karachi, Sindh", "Karachi, Punjab, Pakistan" with its wrong
province, "Worldwide", "Remote", and a posting with no location at all must
every one be admitted. A rule that drops any of them has become a matcher.

For the structured half, once built: of the saved Himalayas corpus, exactly
74 postings must drop and 17 must be admitted, and every drop must name the
field and the absence of Pakistan from its list.

The tag is checked separately: turn the tagger off entirely and the kept set
must be byte-identical. If it is not, a keyword is rejecting.

## Pros and Cons of the Options

### Keep deferring, record only the deferral

Good, because it commits to nothing while descriptions are unreadable.
Bad, because the only source that already answers the question, Himalayas,
would go on being read as free text, and its structured field would stay
unused for no reason.

### Location allowlist, drop everything else

Good, because the display would be short and every row plausibly reachable.
Bad, because the text it would match varies by board for the same city, so it
drops real roles on spelling, invisibly and permanently.

## More Information

Closes the gap that ADR-0001's Confirmation and the architecture document's
filter-chain listing both exposed; both were corrected on 2026-09-17.

`docs/reference/platform-fields.md` is the inventory of which sources expose
an eligibility field.

ADR-0016 defers description matching, which the text half waits on. ADR-0010
forbids scoring, and a reachability tag is a label, not a score, on the same
reasoning ADR-0038 sets out for role families.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-25 | "A tag orders and groups the display" is narrowed: a reachability tag may **filter or group a view, and never order one**. Ordering stays by date alone | ADR-0010 orders the display by date and nothing else, and ADR-0038 forbids a sort that mixes families in one ordered list, so ordering rows by a derived label is the ranking the scope floor excludes, whatever the label is called. This record's own More Information already argues the tag is a label and not a score; the word "orders" contradicted that. The operator's decision, 2026-09-25: "the main ordering will always be date and the families and others can be views or something else." Nothing is built on the old wording: the tag itself is unbuilt, and the field it needs does not exist |
