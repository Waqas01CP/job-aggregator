---
type: reference
description: The Airtable display's five tables and their fields as actually built, the choices they carry, the one field change ADR-0046 still requires, and the five things the Airtable MCP cannot do.
status: current
---

# Airtable schema, as built

Rebuilt 2026-09-18 in the base the MCP now reaches, and verified by reading
every schema back rather than trusting the create calls' replies.

**No identifier appears in this file.** Base, table and field IDs are the
operator's secrets and this repository is public. They live in his secrets and
in the session that built them.

**An earlier base was built on 2026-09-17 and is stranded.** It held `Jobs` and
`Jobs test` with thirteen fields. The MCP was later authorised on a different
account, so that base is not reachable from a session and its tables are not
the ones the pipeline will use. Whichever base `AIRTABLE_BASE_ID` names is the
one that counts, and it must be this one.

**One change ADR-0046 requires is not built.** `Status` needs three more
choices, and the connector cannot add them, so it is the operator's to make by
hand as step 4 of `docs/how-to/airtable-token-and-secrets.md`. It is marked
**pending** below. Everything else in this file was read back from the base.

## The five tables

| Table | Holds | Deletion |
|---|---|---|
| `Jobs` | Production rows projected from the filtered layer | Rows that fell out of the current rules, per ADR-0040, and classified rows fifteen days after classification, per ADR-0046 |
| `Jobs test` | Rows from a `--test-mode` run only | Same, against its own table |
| `rejected-not-a-fit` | Correctly surfaced, operator passed | Auto, fifteen days after `Classified`. The outcome reached its store when the row left `Jobs` |
| `rejected-poor-filtering` | Should not have been surfaced. The defect log | Auto, fifteen days after `Classified`. The outcome reached its store when the row left `Jobs` |
| `accepted` | Shortlisted or applied to | **By no clock. A tool the operator runs deletes from Airtable alone, never from the store** |

`Jobs test` is not one of the four the brief named. It is built because
`AIRTABLE_TEST_TABLE_ID` is one of the repository secrets and ADR-0033
requires a test run to be incapable of touching production state. Without it
that secret points at nothing and test mode has nowhere to write.

## `Jobs` and `Jobs test`, twelve fields

`Title` is the primary field. Airtable requires one and it cannot be removed,
only renamed.

| Field | Type | Holds |
|---|---|---|
| Title | single line text | The posting's title as the board states it |
| Employer | single line text | ADR-0026 records how it is derived per source |
| Location | long text | The board's raw location text, which varies in form |
| Link | URL | Canonical URL, given or constructed, per ADR-0026 |
| Published | date with time | The board's stated publication date. Empty where the platform exposes none |
| First seen | date with time | When the pipeline first recorded the posting |
| Order date | date with time | Publication date where one exists, else first seen. ADR-0007. Sort on this |
| Board | single line text | Source and board, for example `greenhouse:careem` |
| Matched term | single line text | The pool term that admitted the row, per ADR-0021 |
| Identity | single line text | The pipeline's identity. What ADR-0035's upsert matches on |
| Status | single select | The operator's classification. See the choices below |
| Classified at | last modified time, watching `Status` alone | When the classification was last set. The clock `Jobs` retires rows on. Empty until a status is set, and it moves when the status changes |

`Classified at` was created on 2026-09-20 on both tables and verified by
reading the schema back: its `referencedFieldIds` holds the `Status` field and
nothing else.

Watching `Status` alone is not a detail. A last-modified field watching every
field would move on every projection write, restarting the retention clock
twice a day, and nothing in `Jobs` would ever be deleted.

Like the three `Classified` fields, it displays in the viewer's local zone on
a 12 hour clock and the connector offers no way to change that. The stored
value is a real timestamp returned in ISO, so the sweep's arithmetic is
unaffected.

**Two fields were dropped from the earlier thirteen.** `Pipeline reason` and
`Choice reason` live on the classification table each belongs to, so a reason
has one home. ADR-0046 carries that forward unchanged from ADR-0045. On day
15 the sweep reads the reason from the copy and writes it to the store with
the row; a status change discards the old copy's reason. `Stage` on the
`accepted` copy travels the same way. ADR-0046, Changes rows of 2026-09-22.

## The three classification tables

All three carry the same ten identifying fields as `Jobs`, minus `Status`,
because the table a row is copied into is named for the status it carries.
Each then carries the one reason field that applies to it, and a `Classified`
field.

| Table | Its reason field | Choices |
|---|---|---|
| `rejected-not-a-fit` | Choice reason | employer, compensation, stack, recently applied to this employer, seniority in substance |
| `rejected-poor-filtering` | Pipeline reason | wrong title match, location wrong, expired at surfacing, experience level, duplicate |
| `accepted` | Stage | shortlisted, applied |

**`Classified` is a `createdTime` field**, set by Airtable when the record is
created in that table. Under ADR-0046 the sweep creates it, at the first run
after the operator sets a status, so `Classified` is when the classification
reached this table: not when the posting was published and not when it was
surfaced. It was chosen over a hand-set date field because nothing sets it by
hand, so it cannot be forgotten or backdated. A status the operator changes
deletes the old copy and creates a new one, which resets it.

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

- **Status**, on `Jobs` and `Jobs test`. As built it carries ADR-0014's four
  values, checked against ADR-0014 lines 49 to 52 before the field was
  created: `applied`, `rejected_pipeline`, `rejected_choice`,
  `expired_before_review`. **Pending, per ADR-0046:** the field carries
  exactly three choices, `not fit`, `poor filtering` and `accepted`, all set
  by the operator. **`expired_before_review` is retired**, 2026-09-23: the
  pipeline never writes `Status`, and the event that value named is recorded
  by the sweep in `outcomes/removed_unreviewed.json`. The four values as built
  can all be deleted, because no row carries one. These three names are what
  the sweep matches on, so they are exact. Empty means not yet reviewed, and
  that is what the `To review` view filters on.
  **Checked 2026-09-23 through the connector: still the four old values on
  both tables.** Step 4 of `docs/how-to/airtable-token-and-secrets.md`.
- **Pipeline reason** and **Choice reason**: as the table above lists, each on
  its own classification table.

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

## What this file does not settle

The writer is unbuilt. The token and the seven Airtable secrets exist; the
eighth, ADR-0047's token for the private aggregator store, does not, and
neither do ADR-0046's three `Status` choices. ADR-0034 decides the writer
gets its own client, ADR-0035 that it upserts on `Identity` and writes only
pipeline-owned fields, ADR-0040 that the current rules filter the projection,
and ADR-0046 the classification flow the three tables serve.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | The `Status` choices become three, and `expired_before_review` is retired | ADR-0046, on the operator's decision. The pipeline never writes `Status`, so no value on this field is the pipeline's. Field re-read through the connector the same day: the four ADR-0014 values are still what exists |
| 2026-09-22 | `Stage` carried to the accepted store on day 15, like the reason | ADR-0046 extended on the operator's decision |
| 2026-09-22 | Says how a reason reaches the store: read from the copy on day 15, in the same run | ADR-0046 extended on the operator's decision; before it, step 2 read only `Jobs` and no reason would have been stored |
| 2026-09-20 | `Classified at` created on `Jobs` and `Jobs test`, watching `Status` alone, and verified by reading the schema back. A fifth connector limit recorded: it cannot add a choice to an existing single select field | ADR-0046 needs a clock in `Jobs` that moves when a classification changes, which no date field already present does. The three `Status` choices could not be added the same way, so they stay with the operator |
| 2026-09-20 | Deletion column rewritten for ADR-0046's fifteen-day clocks; two pending field changes recorded; the `To review` view recorded as existing; the ADR-0045 and four-secret references brought current | ADR-0046 superseded ADR-0045: classification is a status the operator sets rather than a row he moves, so `Jobs` now deletes classified rows and needs a clock of its own. The pending marks exist because this file describes what was read back from the base, and neither change has been made yet |
| 2026-09-17 | File created. Two tables, `Jobs` and `Jobs test`, thirteen fields each | The schema was built through the MCP and verified by reading it back |
| 2026-09-18 | Rebuilt in a different base, now five tables, and the main table drops two fields | The MCP was authorised on another account, so the 2026-09-17 base is unreachable and stranded; the new base is the one the pipeline will use. The three classification tables are ADR-0043's stores given a surface, and ADR-0045 makes classification a move rather than a status edit, which is why `Pipeline reason` and `Choice reason` moved out of the main table to the table each belongs to. A fourth MCP limit was found: a `createdTime` field's display format cannot be set |
