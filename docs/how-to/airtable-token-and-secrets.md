---
type: how-to
description: The operator's steps for the Airtable token, the repository secrets, and the base changes ADR-0046 and ADR-0047 require. Twelve secrets are set; two more, for the health tables created 2026-10-07, are the operator's to add. The file stays as the procedure for replacing a token.
status: current
---

# Create the Airtable token and the repository secrets

**Steps 1 to 3 are done.** The token exists, the seven Airtable secrets are
set, and the `To review` view is created. Steps 4 and 5 are outstanding and
come from ADR-0046 and ADR-0047, both written after this file.

*(Annotated 2026-09-27: every step is done. Step 4 on 2026-09-24, step 5 on
2026-09-24, and the three test tables' secrets on 2026-09-25, so twelve
secrets are set: the ten Airtable ones below and the private repository's
two. What this file still serves is replacing a token: the private store's
expires on 2027-01-01, and step 5.2 is how to make its successor.)*

**No identifier appears in this file.** The repository is public. The base and
table IDs are given to the operator in the session that built the tables, and
they go into GitHub's secret store, never here.

## Before you start

The tables already exist and are verified: `Jobs`, `Jobs test`,
`rejected-not-a-fit`, `rejected-poor-filtering` and `accepted`, in the base
named "Job aggregator". Their schema is in `docs/reference/airtable-schema.md`,
which predates step 4 below.

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

**Three more are needed than the four originally planned**, because ADR-0046's
sweep reads three classification tables that did not exist when the four were
specified:

| Secret name | Value |
|---|---|
| `AIRTABLE_NOT_A_FIT_TABLE_ID` | The `rejected-not-a-fit` table ID |
| `AIRTABLE_POOR_FILTERING_TABLE_ID` | The `rejected-poor-filtering` table ID |
| `AIRTABLE_ACCEPTED_TABLE_ID` | The `accepted` table ID |

Seven in total. The alternative was for the writer to look tables up by name
on every run, which costs an API call against a budget ADR-0046 sizes at about
36% of the allowance, and which breaks silently if a table is renamed. An ID
is stable and free.

*(Annotated 2026-09-27: three more, for the test copies of the classification
tables the operator created on 2026-09-24, D7. Added by him on 2026-09-25:
`AIRTABLE_NOT_A_FIT_TEST_TABLE_ID`, `AIRTABLE_POOR_FILTERING_TEST_TABLE_ID`
and `AIRTABLE_ACCEPTED_TEST_TABLE_ID`, each the ID of the matching `test`
table. Ten Airtable secrets in total; `.github/workflows/fetch.yml` names
every one.)*

*(Annotated 2026-10-07: two more, for the health tables the seat created
through the connector that day, on the operator's yes: `AIRTABLE_HEALTH_TABLE_ID`,
the ID of `Health`, and `AIRTABLE_HEALTH_TEST_TABLE_ID`, the ID of `Health test`.
Added the same way, under **Settings → Secrets and variables → Actions → New
repository secret**, one each. The seat gives the two IDs in its report and
never writes them into the repository. The token needs nothing new: it is
scoped to the base, not to tables. Until they are set, the health rows wait
in the run logs and no run fails for them. Twelve Airtable secrets then.)*

**Secret names are exact and case-sensitive.** A typo produces an empty value
at run time, not an error, which is the failure that looks like a bug in the
writer.

## Step 3: the "To review" view, by hand

The Airtable MCP cannot create views, so this one is yours. **Done.**

1. Open the `Jobs` table.
2. Create a new **Grid view** named `To review`.
3. Filter: **Status is empty**. Note that "is empty" is an operator rather
   than a value in the choice list, which is why the filter needs no data to
   be set.
4. Sort: **Order date**, newest first.

That view is what you actually open. Under ADR-0046 a classified row keeps its
place in `Jobs` for fifteen days, so the filter is what hides it: the view
holds exactly the rows whose `Status` you have not yet set.

## Step 4: the base changes ADR-0046 needs, by hand

Not done. The sweep cannot be built until these exist.

*(Annotated 2026-09-27: done 2026-09-24. The operator renamed the old
choices rather than adding new ones, so every marked row kept its meaning:
`applied` became `accepted`, `rejected_pipeline` became
`rejected-poor-filtering`, `rejected_choice` became `rejected-not-a-fit`,
and `expired_before_review` was removed. The names are the table names, not
the `not fit` and `poor filtering` below. `docs/reference/airtable-schema.md`
has the field as it stands.)*

*(Annotated 2026-09-23: half done. Items 2 and 3 were done on 2026-09-20,
when `Classified at` was created on `Jobs` and `Jobs test` watching `Status`
alone, per `docs/reference/airtable-schema.md`. Read back through the
connector 2026-09-22T22:30Z: type `lastModifiedTime`, referencing the
`Status` field only, on both tables. **Only item 1, the three `Status`
choices, is outstanding.** The same read found the field still carrying
`applied`, `rejected_pipeline`, `rejected_choice` and
`expired_before_review`.)*

1. In `Jobs`, open the `Status` field and add three choices:
   `not fit`, `poor filtering`, `accepted`. Leave `expired_before_review`,
   which only the pipeline sets.
2. In `Jobs`, create a field named `Classified at`, of type
   **Last modified time**. Set it to watch **only** the `Status` field.
   Watching every field would make it move on every projection write, which
   would restart the retention clock twice a day and delete nothing, ever.
3. Confirm it stays empty on a row whose status has never been set.

The three choice names are what the sweep matches on, so they are exact. The
mapping to tables is in ADR-0046 and the clocks are in
`docs/reference/retention.md`.

## Step 5: the private aggregator repository, ADR-0047

Not done. Himalayas rows are currently fetched and discarded.

*(Annotated 2026-09-27: done 2026-09-24. The repository, the token and both
secrets exist, and production runs have pushed to the private repository since
2026-09-24. The token expires on 2027-01-01: make a new one as in 5.2 and
replace `AGGREGATOR_STORE_TOKEN` before then. A run that cannot reach the
store is marked failed at once, so an expired token shows on its first run.)*

1. Create a **private** repository to hold aggregator-sourced data. No
   workflow runs in it, so it consumes no Actions minutes: GitHub charges
   minutes to the owner of the repository where the workflow runs, and this
   repository only receives pushes.
2. Create a GitHub personal access token with write access to that repository
   and nothing else. A workflow's built-in token reaches only its own
   repository, which is why this is needed.
3. Add it here as the eighth secret:

| Secret name | Value |
|---|---|
| `AGGREGATOR_STORE_TOKEN` | The GitHub token from step 5.2 |
| `AGGREGATOR_STORE_REPO` | `Waqas01CP/job-aggregator-store`. The path only: no `https://`, no `.git`, no trailing slash |

**Two secrets, not one, and the second holds nothing secret.** The repository's name appears above and has been public in this repository's history since `fe07242`. That is harmless: the repository is private and answers 404 to anyone without the token. It is a secret rather than a line of configuration so that no code needs it written into a committed file, and the run log scrubs it like any secret all the same. *(2026-10-02: until now this paragraph said the name was kept out of this repository, two lines below where it is named. The fourth audit's F14; the operator chose to correct the sentence rather than remove the name.)*

**Do not make this repository public later.** Anything committed to a public
repository stays in that history and in every clone already made, which is
exactly what ADR-0047's deletion option depends on avoiding.

## Step 6: tell the session

Once the secrets exist, a session can build the writer. It will not ask for
the token and must never be given it: the pipeline reads it from the secret,
and a token pasted into a conversation is a token that has to be rotated.

## What happens next, in order

*(Annotated 2026-09-27: all six are built and running, the last on
2026-09-25. ADR-0009's confirmation was met on 2026-09-24, when the operator
named roles in `Jobs` he had not found by hand. `STATE.md` has what is open
now.)*

1. The Airtable client (ADR-0034) and the projection that upserts on Identity
   (ADR-0035), writing only pipeline-owned fields.
2. The projection filter (ADR-0040), so the display shows only what the
   current rules admit, including ADR-0046's skip of any identity that already
   has a stored outcome.
3. The backfill's output reaching the display: 257 rows are waiting.
4. The daily sweep (ADR-0046), with its copy, its write-verify-delete order
   and its two fifteen-day clocks.
5. The private aggregator store (ADR-0047) and Himalayas on one poll a day
   (ADR-0048).
6. ADR-0009's slice confirmation, which is the definition of this project
   being finished: a scheduled run completes unattended and the operator finds
   a role in the display he had not already seen by hand.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-07 | Step 2 annotated with the health tables' two secrets, and the description made current | The seat created `Health` and `Health test` through the connector on the operator's yes; their IDs reach him in the seat's report, never this repository |
| 2026-10-02 | The paragraph on `AGGREGATOR_STORE_REPO` corrected: it said the private repository's name was kept out of this repository, two lines below the line naming it | The fourth audit's F14. The operator's choice, 2026-10-02: correct the sentence, since the name is harmless and already in the history |
| 2026-09-27 | Steps 4 and 5 and the list of what happens next annotated as done; the three test-table secrets added beside step 2; the description made current | The file still said steps 4 and 5 were not done, three days after both were, and counted seven secrets where twelve are set. Found while updating `README.md`, which points here. Annotated rather than rewritten, as the row below did, so each original instruction survives beside what is true |
| 2026-09-23 | Step 4 annotated as half done: `Classified at` exists, only the three `Status` choices remain | The step said "Not done" as a whole and still instructed creating `Classified at`, which was built on 2026-09-20. `STATE.md` and `airtable-schema.md` already said so, so the operator was being sent to do work that existed. Annotated rather than rewritten, so the original instruction survives beside what is true |
| 2026-09-20 | Steps 1 to 3 marked done. Step 4 added for the `Status` choices and the `Classified at` field, step 5 for the private aggregator repository and an eighth secret. The `To review` explanation corrected, and the budget figure updated from 27% to 36% | ADR-0046 replaced classification-by-moving with classification-by-status, so a classified row now stays in `Jobs` for fifteen days and the view's filter is what hides it, not the row's absence. ADR-0047 added the private aggregator store and its token. The opening framing of this file as the only blocker was true when written and stopped being true when the operator completed steps 1 and 2 |
| 2026-09-18 | File created, with seven secrets rather than the four originally planned | The token had been named as a blocker in `STATE.md` without steps to clear it. ADR-0045's sweep reads three classification tables that did not exist when the four secrets were specified, and looking them up by name each run costs a call and breaks on a rename |
