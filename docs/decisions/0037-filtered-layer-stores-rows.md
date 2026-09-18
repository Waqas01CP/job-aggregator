---
status: accepted
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0037: The filtered layer stores rows, the projection groups them

## Context and Problem Statement

One role posted to many cities arrives as many postings with different identities. ADR-0001's dedupe key collapses them, keyed on employer, normalised title and publication date.

Pool version 4 admits `software engineer`, which admits Speechify's city copies. Measured against the `data` branch at `91f7518`, the current chain keeps 270 rows which collapse to 25 groups. Speechify accounts for 241 of those rows and exactly 2 of those groups, of 135 and 106 members, spanning 129 and 102 locations.

So the question is where the collapse happens. If the filtered layer stores one representative per group, it holds 25 rows instead of 270 and the public branch stays small. If it stores rows, the branch carries 270 and the display shows 25.

## Decision Drivers

- The filtered layer is a durable record. ADR-0003 never rewrites it, so anything discarded at write time is discarded permanently.
- A group's membership is an interpretation. The key could change, and then a stored representative was chosen under a rule that no longer exists.
- Every location a role was posted to is information the operator may want, and for a Pakistan-reachable role it is the information that decides whether to apply.
- The constraint people reach for, repository size, is not where the pressure actually is.

## Assumptions

- Airtable's free plan caps records per base, on the order of 1,000. **Sourced** from the architecture chat, not verified against Airtable's own documentation in this session, and not exercised. If it is wrong in either direction the conclusion is unchanged, because the projection is where any such cap binds.
- Group membership is stable across runs given the same data. **Measured**: the representative is the earliest by publication date then the lowest identity, and two runs over identical data produced byte-identical files.

## Considered Options

- Store group representatives in the filtered layer.
- Store rows, and group at the projection.
- Store rows plus a precomputed group key.

## Decision Outcome

Chosen option: "store rows, group at the projection".

**The filtered layer stores every kept row.** Nothing is collapsed on the way in. The file is the durable record of what the rules admitted, and collapsing it would lose the locations, the identities and the ability to regroup under a changed key.

**The projection groups.** The display shows one row per group with the locations gathered, which is where the operator benefits from the collapse and where any record ceiling actually binds. Measured today that is 25 rows in the display against 270 in the file.

**This answers question G, whose premise also needed correcting.** The question assumed those 241 rows would enter the public file on the first run after the pool change. They cannot: a row enters the filtered layer only on the run that first sees the posting, and all 255 Speechify postings were first seen before pool version 4 existed. The rows arrive instead through ADR-0030's backfill, and through future rotation at a bound of roughly 64 a day.

**No precomputed group key is stored.** Storing the key would freeze today's ADR-0001 key into the durable record, which is the same mistake as storing representatives, in a smaller form.

### Consequences

The public filtered file grows faster than the display does, and one employer can dominate it. That is visible, diffable and reversible, which a lost location is not.

The projection must group, which means the writer needs the grouping code the display side already has, and the display's row count and the file's row count will differ. Anyone comparing them without knowing this will think something is broken, which is why it is recorded here.

If a record ceiling is ever reached, the pressure lands on the projection and the fix is a display-side filter, not a change to what is stored.

ADR-0001's key can change later without invalidating the stored data.

### Confirmation

Take the filtered file, group it, and count. The display's row count must equal the group count, and every location in a group's members must appear in the projected row. Measured today that is 25 groups from 270 rows, with 129 and 102 locations on the two Speechify groups.

The check that can fail: change ADR-0001's key so that publication date is excluded, regroup, and confirm the file still supports it. Speechify's 241 rows must then collapse to 1 group rather than 2. If the file cannot produce that answer, a representative was stored somewhere.

## Pros and Cons of the Options

### Store group representatives

Good, because the public file stays small and matches the display one for one.
Bad, because the locations and identities of every non-representative posting are lost permanently, and the collapse is frozen under whatever key was current when the row was written.

### Store rows plus a precomputed key

Good, because grouping becomes cheap at projection time.
Bad, because it writes today's interpretation into an append-only file, so a key change leaves stale keys that cannot be rewritten.

## More Information

Answers question G of the 2026-09-17 architecture brief, and corrects its premise.

ADR-0001 defines the key. ADR-0030 decides the backfill that brings the existing rows in. ADR-0013 makes Airtable a projection of this file.
