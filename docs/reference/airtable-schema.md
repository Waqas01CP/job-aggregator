---
type: reference
description: The Airtable display's tables and fields as actually built, the ADR-0014 choices they carry, and the two things the Airtable MCP cannot do.
status: current
---

# Airtable schema, as built

Built 2026-09-18 through the Airtable MCP against the base "Job aggregator".
Verified by reading the schema back, not from the create call's own reply.

**No identifier appears in this file.** The base ID is a repository secret and
this repository is public. Base, table and field IDs live in the operator's
secrets and in the session that built them, never here.

## The two tables

| Table | Receives |
|---|---|
| `Jobs` | Production rows, from a run that commits to `data` |
| `Jobs test` | Rows from a `--test-mode` run only, mirroring the `data-test` branch |

They are identical in structure. A test run must never write to the table the
operator reviews, which is the same separation ADR-0020 gives the branches.

## The fields, in order

`Title` is the primary field. Airtable requires one and it cannot be removed,
only renamed.

| Field | Type | Holds |
|---|---|---|
| Title | single line text | The posting's title as the board states it |
| Employer | single line text | ADR-0026 records how it is derived per source |
| Location | long text | The board's raw location text, which varies in form and may be a list |
| Link | URL | The canonical URL, constructed or given, per ADR-0026 |
| Published | date with time | The board's stated publication date. Empty where the platform exposes none, which today means Manatal |
| First seen | date with time | When the pipeline first recorded the posting |
| Order date | date with time | Publication date where one exists, else first seen. ADR-0007's fallback. The field to sort on |
| Board | single line text | Source and board, for example `greenhouse:careem` |
| Matched term | single line text | The title-pool term that admitted the row, per ADR-0021 |
| Identity | single line text | The pipeline's identity. Unique, and what a retried write matches on |
| Status | single select | ADR-0014. Empty means not yet reviewed |
| Pipeline reason | single select | ADR-0014, why the row should not have been surfaced |
| Choice reason | single select | ADR-0014, why the operator passed on a correct row |

**Every date field is stored with time, ISO date format, 24 hour clock, and
the `utc` time zone.** The pipeline reasons in UTC throughout, and a display
in local time would reintroduce exactly the confusion that made one session
look for a scheduled run that had not fired.

## The choices, all three from ADR-0014

Checked against ADR-0014 lines 49 to 52 before the fields were created.

- **Status:** `applied`, `rejected_pipeline`, `rejected_choice`,
  `expired_before_review`.
- **Pipeline reason:** wrong title match, location wrong, expired at
  surfacing, experience level, duplicate. Each names a filter, which is what
  makes a cluster of one reason a work item.
- **Choice reason:** employer, compensation, stack, recently applied to this
  employer, seniority in substance.

## What the Airtable MCP cannot do

Both were found by trying, and both matter to whoever builds the writer.

**It cannot delete a field.** There is `create_field` and `update_field` and
no delete. This is why the base's default table was replaced rather than
edited: its default `Status` field would have collided with ADR-0014's
`Status`, field names being unique case-insensitively, and four other default
fields would have stayed forever. `create_table` sets the primary field and
every other field in one call, which avoids the problem entirely.

**It cannot create a view.** `list_views_for_table` reads; nothing creates a
grid view. The "To review" view, filtered to an empty Status and sorted by
Order date newest first, is made by hand in the browser, or becomes an
interface page instead.

**One schema error worth knowing.** The MCP's own field schema documents the
`dateTime` time zone as an IANA identifier and gives `"UTC"` as its example.
Airtable's API rejects `"UTC"` with a 422 and accepts `"utc"`.

## What this file does not settle

The writer itself is unbuilt and blocked on the architecture chat: the shared
HTTP module does budgeted GETs only, while the writer needs authenticated
writes and Airtable's own back-off, and CLAUDE.md keeps all HTTP in one
module. ADR-0004 says batched creates; whether an upsert keyed on Identity
replaces them is the chat's, and the Identity field exists either way.
