---
type: how-to
description: The operator's steps to create the Airtable personal access token and the repository secrets that unblock the writer, the sweep and everything behind them.
status: current
---

# Create the Airtable token and the repository secrets

**This is the only thing blocking the rest of the project.** The writer, the
weekly sweep, ADR-0043's three outcome stores, ADR-0044's star and ADR-0045's
classification flow are all designed, recorded and tested as far as they can
be without a token. None can be built until these steps are done.

**No identifier appears in this file.** The repository is public. The base and
table IDs are given to the operator in the session that built the tables, and
they go into GitHub's secret store, never here.

## Before you start

The tables already exist and are verified: `Jobs`, `Jobs test`,
`rejected-not-a-fit`, `rejected-poor-filtering` and `accepted`, in the base
named "Job aggregator". Their schema is in `docs/reference/airtable-schema.md`.

**The MCP authorisation is not a substitute for the token.** That is a
session's OAuth access, used to build the schema. The pipeline runs on a
GitHub runner with no browser and no session, and reads a token from a secret.

## Step 1: create the token

1. Go to **airtable.com/create/tokens** and click **Create new token**.
2. Name it something that says where it is used, for example
   `job-aggregator pipeline`.
3. Add exactly these three scopes, and no others:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
4. Under **Access**, add **only** the base named "Job aggregator". Do not
   grant workspace-wide or all-bases access.
5. Create it, and **copy the token immediately**. Airtable shows it once. It
   begins with `pat`.

**Why these three and no more.** The writer needs to write records and the
sweep needs to read them. `schema.bases:read` lets the writer confirm a field
exists before writing to it, which turns a silent no-op into a clear failure.
Nothing the pipeline does needs to create or delete a table, so no schema
write scope is granted: a token that cannot restructure the base cannot
destroy it either.

## Step 2: add the repository secrets

In GitHub: **Settings → Secrets and variables → Actions → New repository
secret**, once per row.

| Secret name | Value |
|---|---|
| `AIRTABLE_TOKEN` | The `pat...` token from step 1 |
| `AIRTABLE_BASE_ID` | The base ID, beginning `app` |
| `AIRTABLE_TABLE_ID` | The `Jobs` table ID, beginning `tbl` |
| `AIRTABLE_TEST_TABLE_ID` | The `Jobs test` table ID |

**Three more are needed than the four originally planned**, because ADR-0045's
sweep reads three classification tables that did not exist when the four were
specified:

| Secret name | Value |
|---|---|
| `AIRTABLE_NOT_A_FIT_TABLE_ID` | The `rejected-not-a-fit` table ID |
| `AIRTABLE_POOR_FILTERING_TABLE_ID` | The `rejected-poor-filtering` table ID |
| `AIRTABLE_ACCEPTED_TABLE_ID` | The `accepted` table ID |

Seven in total. The alternative was for the writer to look tables up by name
on every run, which costs an API call against a budget ADR-0045 already sizes
at about 27% of the allowance, and which breaks silently if a table is
renamed. An ID is stable and free.

**Secret names are exact and case-sensitive.** A typo produces an empty value
at run time, not an error, which is the failure that looks like a bug in the
writer.

## Step 3: the "To review" view, by hand

The Airtable MCP cannot create views, so this one is yours:

1. Open the `Jobs` table.
2. Create a new **Grid view** named `To review`.
3. Filter: **Status is empty**.
4. Sort: **Order date**, newest first.

That view is what you actually open. Rows you have classified have been moved
out of the table entirely, so the view holds exactly what you have not yet
looked at.

## Step 4: tell the session

Once the secrets exist, a session can build the writer. It will not ask for
the token and must never be given it: the pipeline reads it from the secret,
and a token pasted into a conversation is a token that has to be rotated.

## What happens next, in order

1. The Airtable client (ADR-0034) and the projection that upserts on Identity
   (ADR-0035), writing only pipeline-owned fields.
2. The projection filter (ADR-0040), so the display shows only what the
   current rules admit.
3. The backfill's output reaching the display: 257 rows are waiting.
4. The sweep (ADR-0045), with its write-verify-delete order.
5. ADR-0009's slice confirmation, which is the definition of this project
   being finished: a scheduled run completes unattended and the operator finds
   a role in the display he had not already seen by hand.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | File created, with seven secrets rather than the four originally planned | The token had been named as a blocker in `STATE.md` without steps to clear it. ADR-0045's sweep reads three classification tables that did not exist when the four secrets were specified, and looking them up by name each run costs a call and breaks on a rename |
