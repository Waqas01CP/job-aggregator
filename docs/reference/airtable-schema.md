---
type: reference
description: The Airtable display's eight tables and their fields as actually built, who owns each field, the choices they carry, and the five things the Airtable MCP cannot do.
status: current
---

# Airtable schema, as built

Rebuilt 2026-09-18 in the base the MCP now reaches, and verified by reading
every schema back rather than trusting the create calls' replies. Brought
current 2026-09-25T16:12Z for ADR-0050, which supersedes ADR-0046.

**No identifier appears in this file.** Base, table and field IDs are the
operator's secrets and this repository is public. They live in his secrets and
in the session that built them.

**An earlier base was built on 2026-09-17 and is stranded.** It held `Jobs` and
`Jobs test` with thirteen fields. The MCP was later authorised on a different
account, so that base is not reachable from a session and its tables are not
the ones the pipeline uses. Whichever base `AIRTABLE_BASE_ID` names is the
one that counts, and it must be this one.

**Every field has an owner, and the Owner column below is read by a test.**
ADR-0035: the pipeline writes only what it owns, because an upsert or an
update overwrites every field it sends. `tests/test_fitness.py` holds each
writer's field set to this column (ADR-0049), so a field added to the base
must be added here with its owner before the suite passes.

- **pipeline**: written by the projection or the sweep, and recomputed, so a
  wrong value costs a wrong value and nothing else.
- **operator**: set by hand, read by the sweep, never written by the
  pipeline. Losing one loses a judgement that cannot be reconstructed.
- **Airtable**: set by Airtable itself, a clock.

## The eight tables

| Table | Holds | Deletion |
|---|---|---|
| `Jobs` | Production rows projected from the filtered layer | Per ADR-0050: a classified row fifteen days after `Classified at`, a closed row fifteen days after `Closed`, a row the current rules drop at the next sweep, each only once its store holds it |
| `Jobs test` | Rows from a `--test-mode` run only | Same, against its own table |
| `rejected-not-a-fit` | Correctly surfaced, operator passed | Fifteen days after `Classified`, once the store holds the outcome |
| `rejected-poor-filtering` | Should not have been surfaced. The defect log | Fifteen days after `Classified`, once the store holds the outcome |
| `accepted` | Shortlisted or applied to | **By no clock. A tool the operator runs deletes from Airtable alone, never from the store** |
| `rejected-not-a-fit test`, `rejected-poor-filtering test`, `accepted test` | The sweep's test-mode copies, created 2026-09-24 on the operator's decision D7 | As their production twins |

`Jobs test` and the three test tables exist because ADR-0033 requires a test
run to be incapable of touching production state. Each has its own secret,
and a test ID equal to a production one is refused.

## `Jobs` and `Jobs test`, fourteen fields

`Title` is the primary field. Airtable requires one and it cannot be removed,
only renamed.

| Field | Type | Owner | Holds |
|---|---|---|---|
| Title | single line text | pipeline | The normalised title, on the operator's decision of 2026-09-23: a trailing " - <city>" equal to the row's own location is removed, because Location lists every city in the group. The raw title stays in the stored layers as `title` |
| Employer | single line text | pipeline | ADR-0026 records how it is derived per source |
| Location | long text | pipeline | Every member's location, one per line. ADR-0037 |
| Link | URL | pipeline | Canonical URL, given or constructed, per ADR-0026 |
| Published | date with time | pipeline | The board's stated publication date. Empty where the platform exposes none |
| First seen | date with time | pipeline | When the pipeline first recorded the posting |
| Order date | date with time | pipeline | Publication date where one exists, else first seen. ADR-0007. Sort on this |
| Board | single line text | pipeline | Source and board, for example `greenhouse:careem` |
| Matched term | single line text | pipeline | The pool term that admitted the row, per ADR-0021 |
| Identity | single line text | pipeline | The pipeline's identity. What ADR-0035's upsert matches on |
| Family | single line text | pipeline | The role family of the matched term, ADR-0038. Created 2026-09-24 |
| Closed | date | pipeline | The date the pipeline first saw the posting closed, ADR-0050; empty while open. The sweep writes it and nothing else touches it. Created 2026-09-25 |
| Status | single select | operator | The operator's classification. See the choices below |
| Classified at | last modified time, watching `Status` alone | Airtable | When the classification was last set or changed, a clear included. The clock `Jobs` retires classified rows on |

`Classified at` was created on 2026-09-20 on both tables and verified by
reading the schema back: its `referencedFieldIds` holds the `Status` field and
nothing else. Read again on 2026-09-25 after `Closed` was created: still
`Status` alone.

Watching `Status` alone is not a detail. A last-modified field watching every
field would move on every projection write, restarting the retention clock
twice a day, and nothing in `Jobs` would ever be deleted. `Closed` is a field
of its own for the same reason.

Like the three `Classified` fields, it displays in the viewer's local zone on
a 12 hour clock and the connector offers no way to change that. The stored
value is a real timestamp returned in ISO, so the sweep's arithmetic is
unaffected.

## The three classification tables

All three, and their test copies, carry the ten identifying fields the sweep
copies from `Jobs`, then the one operator field that applies, then
`Classified`. A reason has one home: on day 15 the sweep reads it from the
copy and writes it to the store with the row, and a status change discards
the old copy with its reason. ADR-0050.

| Field | Owner | Holds |
|---|---|---|
| Title | pipeline | Copied from `Jobs` |
| Employer | pipeline | Copied from `Jobs` |
| Location | pipeline | Copied from `Jobs` |
| Link | pipeline | Copied from `Jobs` |
| Published | pipeline | Copied from `Jobs` |
| First seen | pipeline | Copied from `Jobs` |
| Order date | pipeline | Copied from `Jobs` |
| Board | pipeline | Copied from `Jobs` |
| Matched term | pipeline | Copied from `Jobs` |
| Identity | pipeline | Copied from `Jobs`; what the store is keyed on and the verify checks |
| Choice reason, Pipeline reason or Stage | operator | The one that applies to the table, below |
| Classified | Airtable | Created time: when the copy arrived. The fifteen-day clock of the two rejection tables |

| Table | Its operator field | Choices |
|---|---|---|
| `rejected-not-a-fit` | Choice reason | employer, compensation, stack, recently applied to this employer, seniority in substance |
| `rejected-poor-filtering` | Pipeline reason | wrong title match, location wrong, expired at surfacing, experience level, duplicate |
| `accepted` | Stage | shortlisted, applied |

`Stage` on `accepted` is the operator's own distinction. Both values feed
ADR-0044's star and nothing automated reads the difference.

## Dates

**Every `dateTime` field is stored with time, ISO date format, 24 hour clock,
and the `utc` time zone.** The pipeline reasons in UTC throughout.

**The three `Classified` fields are the exception, and not by choice.** A
`createdTime` field displays in the viewer's local zone on a 12 hour clock and
the MCP offers no way to change it: `create_field` accepts no options for that
type, and `update_field`'s options accept only a formula. The stored value is
a real timestamp and the API returns it in ISO, so the sweep's arithmetic is
unaffected. Only the display differs, and it is recorded here so nobody reads
it later as an inconsistency somebody chose.

## The choices

- **Status**, on `Jobs` and `Jobs test`: `rejected-not-a-fit`,
  `rejected-poor-filtering` and `accepted`, the names of the tables they
  feed, set by the operator only. Renamed from ADR-0014's `rejected_choice`,
  `rejected_pipeline` and `applied` by the operator in the browser on
  2026-09-24, and `expired_before_review` deleted; read back that day: each
  choice kept its ID, every marked row its meaning, and no `Classified at`
  moved. ADR-0046's `not fit` and `poor filtering` never reached the base.
  Empty means not yet reviewed, and that is what the `To review` view filters
  on.
- **Choice reason**, **Pipeline reason** and **Stage**: as the table above
  lists, each on its own classification table.

## What the Airtable MCP cannot do

Five limits. The first four were found by trying.

**It cannot add a choice to an existing single select field.** `update_field`
accepts a name, a description and `options`, and `options` accepts only a
formula. There is no path to a `choices` array on an existing field. This is
read from the connector's own schema, not from an attempt, because the schema
rejects the argument before a call is made. It is why ADR-0046's three `Status`
choices are the operator's to add in the browser.

**It cannot delete a field.** There is `create_field` and `update_field` and no
delete. This is why a base's default table is replaced rather than edited: its
default `Status` field collides with ADR-0014's `Status`, field names being
unique case-insensitively, and four other default fields would stay forever.
`create_table` sets the primary field and every other field in one call.

**It cannot create a view.** `list_views_for_table` reads; nothing creates a
grid view. The `To review` view was made by hand in the browser by the
operator and exists as of 2026-09-19, confirmed through the MCP, which lists
it on `Jobs`. Its filter and sort are not readable through the MCP and have
not been verified here; they are specified in step 3 of
`docs/how-to/airtable-token-and-secrets.md` as an empty Status and Order date
newest first. The filter needed no data to set, because "is empty" is an
operator rather than a value in the choice list.

**It cannot set a `createdTime` field's display format**, as above.

**Its own schema documents the `dateTime` time zone wrongly.** It gives `"UTC"`
as the example for an IANA identifier; Airtable's API rejects `"UTC"` with a
422 and accepts `"utc"`.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | `Title` carries the normalised title | The operator's decision, answering the implementing seat's question after the first test-mode projection. A display row is a group whose Location lists every city, so a raw title naming one city misled; the raw title is kept in the store. Annotated in the table above rather than rewritten |
| 2026-09-23 | The `Status` choices become three, and `expired_before_review` is retired | ADR-0046, on the operator's decision. The pipeline never writes `Status`, so no value on this field is the pipeline's. Field re-read through the connector the same day: the four ADR-0014 values are still what exists |
| 2026-09-22 | `Stage` carried to the accepted store on day 15, like the reason | ADR-0046 extended on the operator's decision |
| 2026-09-22 | Says how a reason reaches the store: read from the copy on day 15, in the same run | ADR-0046 extended on the operator's decision; before it, step 2 read only `Jobs` and no reason would have been stored |
| 2026-09-20 | `Classified at` created on `Jobs` and `Jobs test`, watching `Status` alone, and verified by reading the schema back. A fifth connector limit recorded: it cannot add a choice to an existing single select field | ADR-0046 needs a clock in `Jobs` that moves when a classification changes, which no date field already present does. The three `Status` choices could not be added the same way, so they stay with the operator |
| 2026-09-20 | Deletion column rewritten for ADR-0046's fifteen-day clocks; two pending field changes recorded; the `To review` view recorded as existing; the ADR-0045 and four-secret references brought current | ADR-0046 superseded ADR-0045: classification is a status the operator sets rather than a row he moves, so `Jobs` now deletes classified rows and needs a clock of its own. The pending marks exist because this file describes what was read back from the base, and neither change has been made yet |
| 2026-09-17 | File created. Two tables, `Jobs` and `Jobs test`, thirteen fields each | The schema was built through the MCP and verified by reading it back |
| 2026-09-18 | Rebuilt in a different base, now five tables, and the main table drops two fields | The MCP was authorised on another account, so the 2026-09-17 base is unreachable and stranded; the new base is the one the pipeline will use. The three classification tables are ADR-0043's stores given a surface, and ADR-0045 makes classification a move rather than a status edit, which is why `Pipeline reason` and `Choice reason` moved out of the main table to the table each belongs to. A fourth MCP limit was found: a `createdTime` field's display format cannot be set |
| 2026-09-25 | Rebuilt for ADR-0050: eight tables, fourteen fields on `Jobs`, `Family` and `Closed` added, an Owner column for every field, the `Status` choices as renamed, and the stale "not yet built" passages removed | ADR-0050 superseded ADR-0046 and adds `Closed`; Brief 7 asked for `Closed` to be recorded here. The Owner column makes ADR-0035's ownership a property a test reads (ADR-0049), so a field added later must declare its owner. `Closed` was created on both tables through the connector and read back |
