---
status: accepted
topic: filtering
description: Eligibility in one record. A posting is kept unless every place it can be taken from is closed to the operator, judged from its location text, the source's own structured place, its stated workplace, and what its description requires; time zones and job type never exclude. Supersedes ADR-0041.
date: 2026-10-03
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0057: A posting is shown only if he can take it, and none he can take is lost

## Context and Problem Statement

ADR-0041 decided on 2026-09-17 how location should work: a posting is admitted on any location signal or on none, it is dropped only on an explicit exclusion by the source, and **location keywords never reject**. Its reason was sound. A rule that reads place names will one day drop "Karachi, Punjab, Pakistan" for having the wrong province.

What was built took a different approach. On 2026-09-26 the operator saw postings in his table restricted to the United States or Canada and asked for them out, stating the constraint in his own words: "i do not want any jobs shown in the table which i am not eligible to while at the same time i do not want to miss any to which i am eligible to". The rule built on that, D13, reads the location text and drops a posting when every place it names is closed to him. The run of 2026-09-30 dropped 253 ATS postings on location alone, where ADR-0041 had said nothing on an ATS board would ever be dropped.

The architecture chat recorded D13 on 2026-09-28 as an extension of ADR-0041 and wrote that its rule was unchanged. That was wrong. Reading place names and dropping on them is the matcher ADR-0041 rejected, and a different approach to the same question is a supersession.

Since then the rule has grown by four more decisions: the fourth audit's refinements of 2026-10-01, the source's structured place and stated workplace on 2026-10-02, and the description's requirements the same night. They were each recorded only in session logs. This record holds them together, so that "can he take this job" is answered in one place.

## Decision Drivers

- Both halves of his sentence bind: nothing he cannot take, and nothing he can take lost. When they pull apart, a posting is kept.
- A text matcher fails on spelling, unfamiliar places and ambiguous phrasing, so whatever reads text must fail toward keeping.
- The sources give more than text: a country code, office locations, a stated workplace, and a description.
- Every rule is named and deterministic (ADR-0010), and every place and threshold is configuration (ADR-0031).

## Assumptions

- A place the rule cannot name is more likely one he can take than one he cannot. **Stated** by the operator: unclear is kept. Confirmed by him on 2026-09-26 for "Kingswinford", on site in England, which the lists cannot name.
- When the text names nothing the rule knows, the source's structured place is where the role is open. **Measured**: over the saved postings it newly drops 67 that were kept, Lever 42 by country and Greenhouse 25, 19 by office or country and 6 by a stated hybrid workplace, and keeps none newly; the only ones naming Pakistan are 6 hybrid Islamabad roles, which this record drops on purpose. The implementing seat found no newly dropped description mentioning "anywhere" or "worldwide". The architecture chat checked independently on 2026-10-03, over the current listings of all eleven employer boards, every posting naming no Pakistani place and not plainly remote, against about twenty-five phrases of global or open hiring: every match was company boilerplate or a restriction to another region, and none was a job he could take.
- Time zones about working hours do not affect him. **Stated**: "time zone is not an issue", 2026-09-26, and "i am open to working at any time", 2026-10-03.
- How often a time zone is used as a residence requirement rather than as working hours. **Not established.** It is measured before any rule is built.
- The configured place lists name the closed cases well enough. **Not established**, and safe either way: what they cannot name is kept.

## Considered Options

- Keep ADR-0041: explicit exclusions only, keywords never reject.
- D13 as first built: the location text alone.
- The location text, then the source's structured place, the stated workplace, and the description's requirements, each only able to close.
- A model that classifies eligibility from the whole posting.

## Decision Outcome

Chosen option: "the location text, then the source's structured place, the stated workplace, and the description's requirements, each only able to close".

**We will keep a posting unless every place it can be taken from is closed to him.** One reachable place keeps it. Anything the rule cannot read is kept.

**We will treat a place as closed when it is** a country other than Pakistan; a region that does not include Pakistan; or a Pakistani city other than Karachi where the role is on site or hybrid with no remote option. An open region outranks a closed country unless the posting says "only".

**We will read in this order.**
1. **The location text**, with time-zone wording and stated preferences removed first.
2. **Where every part of the text is unclear, the source's structured place**: Lever's `country`, Greenhouse's office locations, a `Country` custom field. It decides only to close, never to keep a posting the text would drop.
3. **The workplace**, as the source states it or as ADR-0058 reads it from the description. On site or hybrid makes a Pakistani city other than Karachi closed. A stated remote workplace adds nothing.
4. **The description's requirements**, as ADR-0058 reads them: a posting is dropped when every place it requires a right to work, citizenship or residence in is closed. "No visa sponsorship" is never read as a requirement, because on a worldwide remote role it only says nobody is relocated. Citizenship of a specific other country drops a posting. A security clearance is not read until it becomes common.

**We will never exclude on a time zone that is about working hours.** A time zone used as a residence requirement, "only applicants located in these time zones", is a location restriction in substance. It is built only after the implementing seat measures how often it occurs; until then such a posting is kept.

**We will never filter on job type.** Internships, contracts, part-time, temporary and volunteer roles all stay. In his words, volunteering "might be a good opportunity and can become a stepping stone".

**We will keep every place, region and the home country in `config/eligibility.json`.** A drop names the field it read and quotes the home country from configuration at run time, so no module names a country (ADR-0031).

**We will let a reachability tag filter or group a view and never order one**, as ADR-0041 was narrowed on 2026-09-25. The display is ordered by date alone.

### Consequences

The table holds fewer postings he cannot take. Over the saved corpus the structured place newly drops 67 kept postings, and the description 7 of the 50 kept apart from age; neither newly keeps one.

ADR-0041's warning stands and is answered rather than ignored: a text matcher drops on spelling, so this one drops only when every place is closed, keeps what it cannot read, and carries ADR-0041's own case set as its guard.

On Himalayas this rule drops nothing by construction, because ADR-0053 asks the source for Pakistan-eligible postings only. A drop count of zero there is the endpoint working, not the rule failing.

A residence requirement phrased as a time zone is kept until it is measured. That shows him a job he cannot take, which is the lesser of the two errors and still breaks the first half of his sentence.

Rules that need a field a stored row lacks judge postings first seen after them, and older rows leave by the thirty-day clock (ADR-0040).

### Confirmation

**ADR-0041's case set must all be kept**: "Karachi, Sindh", "Karachi, Punjab, Pakistan" with its wrong province, "Worldwide", "Remote", and a posting with no location at all. A rule that drops any of them has become the matcher ADR-0041 warned of.

**A posting naming one open place among closed ones must be kept.**

**The structured place must never keep a posting the text drops**, and must close a posting whose text names nothing known and whose place is closed.

**"No visa sponsorship" must never drop a posting, and a working-hours time zone must never drop one.**

**ADR-0041's corpus check stands as a regression check**: on the saved 91-posting Himalayas corpus, exactly 74 drop and 17 are kept. It held exactly on 2026-09-30.

**Every drop must name its field and quote the home country from configuration**, and ADR-0031's audit must still find no country named in code.

**Live only:** the residence-by-time-zone measurement, before any rule.

## Pros and Cons of the Options

### Keep ADR-0041

Good, because it cannot drop a posting on a misreading.
Bad, because it showed him postings restricted to other countries, and he asked for them out.

### The location text alone

Good, because it is one rule over one field.
Bad, because it keeps every posting whose text is a city it cannot place, and 59 such postings were measured as ones he cannot take.

### A model that classifies eligibility

Good, because it would read phrasing no list anticipates.
Bad, because ADR-0010 excludes model-based screening, and a verdict nobody can trace to a named rule is one he cannot check.

## More Information

**Supersedes ADR-0041.** Carried forward unchanged: its case set, its principle that a structured field is used wherever a source provides one, its corpus check of 74 and 17, and its tag rule as narrowed on 2026-09-25.

ADR-0058 reads the description that items 3 and 4 depend on. ADR-0053 is why Himalayas arrives pre-filtered. ADR-0032 answers the separate question of level. ADR-0031 owns the configuration, ADR-0010 the requirement that every rule be named, and ADR-0040 the limit on judging rows stored before a rule existed.

The operator's decisions this record carries: D13, 2026-09-26, and his two judgements of that day; job types and time zones, 2026-10-02; the structured place and stated workplace, 2026-10-02; the description's requirements, 2026-10-02, with "if the job is remote but is us only then it should not be shown"; citizenship and security clearance, 2026-10-03; and his clarification of time zones, 2026-10-03. The fourth audit's F4 refinements of 2026-10-01 were measured over 413 public locations, 118 Himalayas and the 146-entry corpus with no verdict changed.

## Changes
