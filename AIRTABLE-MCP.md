---
type: how-to
description: How the operator, and any LLM chat working for him, uses the Airtable base through Airtable's MCP connector, and how to spend as few of the workspace's 1,000 monthly API calls as possible doing it. Which fields a chat may write, what each connector tool costs, and the patterns for reading once and writing in batches.
status: current
---

# Using the Airtable base through an LLM and the MCP connector

**Who this is for:** the operator, and any chat he works with through Airtable's MCP connector, such as his resume chat while he applies. A chat given this file should follow it as written.

**Why it matters:** every call the connector makes spends from the same allowance the pipeline uses.
- **The allowance:** 1,000 API calls a month for the whole workspace, on Airtable's free plan.
- **The pipeline's share:** in October it spent 635 of them (measured from its run logs, test runs included). It will spend about 590 in November [estimate, `briefs/architecture.md`'s addendum of 2026-10-28].
- **What is left for chats:** about 400 calls a month, so every call a chat saves is one he can spend applying.

Facts about Airtable below were read on 2026-10-28 from Airtable's own pages:
- "Managing API call limits in Airtable" (support);
- "Airtable plans" (support);
- the developer pages on rate limits and list records;
- the connector's own tool descriptions.

## 1. The budget, and what happens at its end

- **The allowance:** 1,000 API calls a month per workspace. It resets on the first day of each calendar month, UTC.
- **Who counts against it:** calls made by integrations, the MCP connector included, count against the same allowance as the pipeline's.
- **Past 1,000:** a one-time thirty-day grace period, then every call answers 429 until the month resets. **The grace period is given once, ever.** Do not spend it on a busy week; keep it for an emergency.
- **Where to see the count:** Workspace settings, Summary, "Public API calls" for the current month (the workspace owner sees it).
- **The pipeline's guard:** it stops itself at 900 of its own calls (`config/sweep.json`, `monthly_call_ceiling`). It does not see the chats' calls, so the guard does not protect the chats, and the chats can still use up the workspace.
- **The records limit:** the base holds at most **1,000 records across all its tables** on the free plan. On 2026-10-28 it held about 630 by the run logs' count, test tables included. Creating rows by hand uses that up too.

## 2. The tables, and what a chat may write

The pipeline owns most fields and rewrites them every run. **A chat writes only the operator's fields.**

| Table | A chat may write | Never write |
|---|---|---|
| `Jobs` | `Status`, `Reason` | Every other field: `Title`, `Employer`, `Location`, `Link`, `Published`, `First seen`, `Order date`, `Board`, `Matched term`, `Identity`, `Family`, `Closed`, `Who reads`, `Years asked`, `Required in`, `On site`, `No description`. The pipeline owns them and overwrites any edit. `No.` and `Classified at` are Airtable's |
| `accepted` | `Stage`, `Delete` | Everything else; `Jobs No.` is the pipeline's |
| `rejected-not-a-fit` | `Choice reason` | Everything else |
| `rejected-poor-filtering` | `Pipeline reason` | Everything else |
| `Health` | Nothing. Read it; delete a row once read if space is needed (it is never sent again) | |
| `Jobs test` and the other test tables | Nothing | Leave them to test runs |

**The choices, written exactly as named.**
- **`Status`:** `rejected-not-a-fit`, `rejected-poor-filtering`, `accepted`, and, if the field offers them, `applied` and `gone`.
  - `applied` makes the `accepted` copy with `Stage` already `applied`.
  - `gone` is for a posting found dead: the pipeline records it and removes the row.
- **`Reason`:** the choices of `Choice reason` and `Pipeline reason` together.
  - `Choice reason`: employer, compensation, stack, recently applied to this employer, seniority in substance.
  - `Pipeline reason`: wrong title match, location wrong, expired at surfacing, experience level, duplicate.
- **`Stage`:** shortlisted, applied, gone.
- **`Delete`:** yes.

`docs/reference/airtable-schema.md` holds the current list; a choice added in the browser belongs there too.

**What the pipeline does with them.**
- **At the next run** (about 03:30 UTC and between about 16:30 and 19:00 UTC; 8:30 am and the evening in Pakistan) a row with a `Status` is copied to its table.
- **Fifteen days later** its outcome is stored on GitHub and the row leaves `Jobs`.
- **What the pipeline never does:** write `Status`.
- **Clearing a `Status`:** removes nothing.
- **A row deleted by hand in `Jobs`:** comes back at the next run. **Never create or delete rows in `Jobs`.**
- **`Delete` set to yes on an `accepted` row:** removes it from Airtable once it is stored; it is never removed from the store.

## 3. What each connector tool costs

Airtable's API reads one table per call, at most 100 records a page, and writes at most 10 records a call. The connector accepts more per tool call: up to 8,000 rows a read and 50 records a write. **Whether one connector call is counted as one API call, or as the pages and batches of 10 it stands for, is not stated anywhere read so far.** Section 6 says how to find out. Until then, plan on the cautious reading.

| Tool | What it does | Calls, cautious reading |
|---|---|---|
| `search_bases`, `list_tables_for_base` | Find the base and its tables' and fields' IDs | 1 each |
| `get_table_schema` | A field's choices and their IDs | 1 |
| `list_records_for_table` | Read rows, with filters, chosen fields and sort | 1 for each 100 rows returned |
| `search_records` | Free-text search | 1 or more; avoid for bulk work |
| `update_records_for_table` | Change rows by record ID | 1 for each 10 rows |
| `create_records_for_table`, `delete_records_for_table` | Create or delete rows | 1 for each 10 rows; a chat should not need them on `Jobs` |

**Every tool call costs at least one call, even when it finds nothing.**

## 4. The rules that save calls

1. **Keep the IDs, do not look them up each time.**
   - **Where:** the base's ID and the table and field IDs belong in the chat's own private instructions or notes, never in this public repository.
   - **The saving:** a chat that has them skips `search_bases` and `list_tables_for_base`, 2 calls a session.
   - **When they change:** if a call fails because an ID is wrong, look them up once and update the notes.
2. **Read once, then work from what was read.**
   - **How:** one `list_records_for_table` on `Jobs`, filtered to what the work needs, such as `Status` is empty for "to review". Name only the fields needed, and sort by `Order date` latest first.
   - **Then:** keep the result in the conversation and work through it. Do not read the same rows again to check one detail; do not read row by row; do not search for each job by name.
3. **Filter on the server, not in the chat.** A filter that returns 40 rows costs one call; reading all 300 rows to pick 40 costs three.
4. **Write in batches.**
   - **How:** decide on a group of jobs first, then send one `update_records_for_table` carrying them all.
   - **The cautious batch:** ten records a call. Ten jobs applied to is **one call** setting `Status` to `applied` (or `accepted`) on ten rows, not ten calls.
   - **The measured batch:** up to 50 once section 6 has shown the connector counts a 50-record write as one call.
5. **One write per job, not two.**
   - **Applying:** set `Status` to `applied` in `Jobs` when the field offers it. The pipeline then makes the `accepted` copy with `Stage` applied, so `accepted` needs no second write.
   - **Turning down:** set `Status` and `Reason` in the same update.
6. **Do not read back what was just written.** The update's answer already returns the fields it wrote.
7. **Do not fetch the schema to write a choice.** Write the choice's name as listed in section 2, with `typecast` off. `get_table_schema` is needed only to filter on a choice by its ID, or when a choice was added.
8. **Classify in one sitting a day, after the evening run if you can.**
   - **Why:** the pipeline's evening run copies statuses set since the morning's run, which costs it extra calls (about 5 to 11) on top of the next morning's work. Statuses set after the evening run are copied by the morning run alone.
   - **The window:** in Pakistan, the evening run lands between about 9:30 pm and midnight, the morning run at about 8:30 am.
9. **Leave the test tables alone, and do not create rows.** The base's 1,000-record limit counts every table.

## 5. Recipes

**"Show me the jobs to review"** (1 call for up to 100 rows):
- `list_records_for_table` on `Jobs`, filter `Status` is empty.
- Fields: Title, Employer, Location, Link, Order date, Who reads, Family.
- Sort: `Order date` descending.

**"I applied to these seven"** (1 call):
- One `update_records_for_table` on `Jobs` with the seven record IDs from the read.
- Each gets `Status` `applied`, or `accepted` if `applied` is not offered.

**"Turn down these twelve, not a fit, stack"** (2 calls at ten a call, 1 at fifty):
- `Status` `rejected-not-a-fit` and `Reason` `stack` on each row.

**"Which accepted jobs are still open?"** (1 call):
- `list_records_for_table` on `accepted`.
- Fields: Title, Employer, Link, Stage, Jobs No.

**"Mark these old accepted rows for removal"** (1 call per ten):
- `Delete` yes on each.
- They leave Airtable after the next morning run stores them; the store keeps them.

## 6. Measuring what the connector really costs

1. **Pick a quiet hour,** when no pipeline run is due: the pipeline runs at about 03:30 UTC and in the evening.
2. **Read the workspace's "Public API calls"** count.
3. **Have the chat make one known call:** say one `update_records_for_table` writing 20 records, on rows that are safe to change. Re-setting a `Reason` to its own value is safe.
4. **Read the count again**, after Airtable has refreshed it. It may lag; on 2026-10-22 it appeared to refresh once a day, by the morning UTC.
5. **Read the difference:** a rise of 1 means the connector counts per tool call; a rise of 2 means it counts per ten records.
6. **Then update section 3 of this file** with the result and its date.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-28 | File created | The operator's request of 2026-10-28: a guide to using the base through an LLM and the MCP connector, with the strategy for spending as few calls as possible, since his own chats share the workspace's allowance with the pipeline |
