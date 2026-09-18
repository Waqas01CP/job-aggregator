---
type: reference
description: The Airtable display's five tables and their fields as actually built, the ADR-0014 choices they carry, and the four things the Airtable MCP cannot do.
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

## The five tables

| Table | Holds | Deletion |
|---|---|---|
| `Jobs` | Production rows projected from the filtered layer | Only rows that fell out of the current rules, per ADR-0040 |
| `Jobs test` | Rows from a `--test-mode` run only | Same, against its own table |
| `rejected-not-a-fit` | Correctly surfaced, operator passed | Auto, after retention, write-verify-delete |
| `rejected-poor-filtering` | Should not have been surfaced. The defect log | Auto, after retention, write-verify-delete |
| `accepted` | Shortlisted or applied to | **By hand only. Nothing automated deletes here** |

`Jobs test` is not one of the four the brief named. It is built because
`AIRTABLE_TEST_TABLE_ID` is one of the four repository secrets and ADR-0033
requires a test run to be incapable of touching production state. Without it
that secret points at nothing and test mode has nowhere to write.

## `Jobs` and `Jobs test`, eleven fields

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
| Status | single select | ADR-0014's four values. Only `expired_before_review` is still set here |

**Two fields were dropped from the earlier thirteen.** `Pipeline reason` and
`Choice reason` now live on the classification table each belongs to, so a
reason has one home. Under ADR-0045 the operator classifies by moving a row,
not by setting a status, so the reason is recorded where the row lands.

## The three classification tables

All three carry the same ten identifying fields as `Jobs`, minus `Status`,
because the table is the status. Each then carries the one reason field that
applies to it, and a `Classified` field.

| Table | Its reason field | Choices |
|---|---|---|
| `rejected-not-a-fit` | Choice reason | employer, compensation, stack, recently applied to this employer, seniority in substance |
| `rejected-poor-filtering` | Pipeline reason | wrong title match, location wrong, expired at surfacing, experience level, duplicate |
| `accepted` | Stage | shortlisted, applied |

**`Classified` is a `createdTime` field**, set by Airtable when the record is
created in that table. It is the clock ADR-0045's retention runs on: when the
row arrived here, not when the posting was published and not when it was
surfaced. It was chosen over a hand-set date field because nothing sets it by
hand, so it cannot be forgotten or backdated.

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

## The choices, from ADR-0014

Checked against ADR-0014 lines 49 to 52 before the fields were created.

- **Status**, on `Jobs` and `Jobs test`: `applied`, `rejected_pipeline`,
  `rejected_choice`, `expired_before_review`. Under ADR-0045 only the last is
  still set; the other three are expressed by moving the row.
- **Pipeline reason** and **Choice reason**: as the table above lists, each
  now on its own classification table.

## What the Airtable MCP cannot do

All four found by trying.

**It cannot delete a field.** There is `create_field` and `update_field` and no
delete. This is why a base's default table is replaced rather than edited: its
default `Status` field collides with ADR-0014's `Status`, field names being
unique case-insensitively, and four other default fields would stay forever.
`create_table` sets the primary field and every other field in one call.

**It cannot create a view.** `list_views_for_table` reads; nothing creates a
grid view. A "To review" view, filtered to an empty Status and sorted by Order
date newest first, is made by hand in the browser or becomes an interface page.

**It cannot set a `createdTime` field's display format**, as above.

**Its own schema documents the `dateTime` time zone wrongly.** It gives `"UTC"`
as the example for an IANA identifier; Airtable's API rejects `"UTC"` with a
422 and accepts `"utc"`.

## What this file does not settle

The writer is unbuilt and blocked on the operator creating the personal access
token and the four repository secrets. ADR-0034 decides it gets its own
client, ADR-0035 that it upserts on `Identity` and writes only pipeline-owned
fields, ADR-0040 that the current rules filter the projection, and ADR-0045
the classification flow the three tables serve.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | File created. Two tables, `Jobs` and `Jobs test`, thirteen fields each | The schema was built through the MCP and verified by reading it back |
| 2026-09-18 | Rebuilt in a different base, now five tables, and the main table drops two fields | The MCP was authorised on another account, so the 2026-09-17 base is unreachable and stranded; the new base is the one the pipeline will use. The three classification tables are ADR-0043's stores given a surface, and ADR-0045 makes classification a move rather than a status edit, which is why `Pipeline reason` and `Choice reason` moved out of the main table to the table each belongs to. A fourth MCP limit was found: a `createdTime` field's display format cannot be set |
