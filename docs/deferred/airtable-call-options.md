---
type: deferred
description: The ways to spend fewer Airtable API calls, or fewer records, that were weighed on 2026-10-28 and not approved then: what each would do, what it would save, why it waited, and when to look again. The approved ones are being built; these are kept so none has to be rediscovered.
status: current
---

# Airtable call and record options, deferred

**What happened on 2026-10-28:** every way to spend fewer of the workspace's 1,000 monthly Airtable calls, and fewer of the base's 1,000 records, was weighed for the operator. That covered the code against Airtable's own documentation, read that day:
- "Managing API call limits in Airtable" and "Airtable plans" (support);
- the developer pages on rate limits, list records and webhooks.

The full list, with each option's pros and cons, is in the implementing seat's report of that day (`briefs/architecture.md`, Addendum 2, gitignored).

**What he approved, 2026-10-29 (Pakistan time):**
- A1, the evening run using the morning's view of `Jobs`;
- A3, a webhook reporting his edits;
- B1, the copies' record IDs remembered;
- C1, the unreviewed clock at 21 days;
- D2, stopping at once when the month's calls are spent;
- D3, the base's record count reported each morning;
- D4, `Jobs test` emptied;
- E, `AIRTABLE-MCP.md`.

His words on the rest: "you should note them down somewhere in case if i want to implement them later on as some of them were quite good proposals". These are they.

**Figures:** savings are estimates for a month like November 2026, when the pipeline was projected at about 590 calls with no option built.

## A2. Read only the rows changed since the last full read

- **What:** a run that does not read `Jobs` in full reads only the rows modified since, through `filterByFormula` on `LAST_MODIFIED_TIME()`. It lays them over the view the last full read stored.
- **Saves:** about 75 calls a month.
- **Why it waited:** A1 does the same job, removing the evening's full read, and removes the read altogether. A run cannot both skip its read and make a smaller one, so the two are alternatives. He chose A1.
- **Look again if:** the evening run must see his edits made since the morning, for example if the copy step has to run in the evening again.

## B2. Retire the two rejection tables; use views of `Jobs`

- **What:** no copies made in `rejected-not-a-fit` and `rejected-poor-filtering`. His `Reason` already sits on `Jobs` beside `Status` (ADR-0062), so a view of `Jobs` filtered on a rejection status shows the same rows for the same fifteen days, and the GitHub stores keep every outcome as now. `accepted` would stay.
- **Saves:** about 100 to 150 calls a month, and about 105 records.
- **Why it waited:** he chose B1, which keeps the tables and removes most of their reads. B2 changes ADR-0043, ADR-0050 and ADR-0062 and the clearing tool, and takes away two tables he may use.
- **Look again if:** the record limit presses, or he finds he works from views of `Jobs` rather than from the copy tables.

## B3. Read `accepted` every other day

- **What:** the morning sweep reads `accepted` for his `Delete` and `Stage` marks every other morning, not every morning.
- **Saves:** about 15 calls a month. His marks act up to a day later.
- **Why it waited:** small, and A3, approved, makes it unnecessary: the webhook reports his marks as they happen.
- **Look again if:** A3 is not built or is turned off.

## C2. The classified clock at 7 days, not 15

- **What:** a row he has classified leaves `Jobs` 7 days after `Classified at` rather than 15 (`retire_after_days` in `config/sweep.json`; ADR-0050, ADR-0062). The store keeps it either way.
- **Saves:** about 60 calls a month for each 100 rows fewer in `Jobs`, and the same records.
- **Why it waited:** less time to change his mind in the table; his to decide.
- **Look again if:** `Jobs` keeps growing as sources are added.

## C3. Hold a low-yield source from the display

- **What:** list a source in `sources_held_from_display` (`config/sweep.json`, built). It is still fetched, judged and stored, but its rows are not sent to `Jobs`.
- **Saves:** depends on the source: its rows' share of each read and write.
- **Why it waited:** a source should be judged by its measured yield first, his rule since 2026-10-19 (Breezy).
- **Look again if:** a source sends many rows he never takes.

## D1. The test tables in a second, free workspace

- **What:** `Jobs test`, its three classification tables and `Health test` move to a base in another free workspace. Airtable's free plan allows 1,000 calls a month per workspace and 1,000 records per base, so test runs would stop spending his production allowance and stop filling his production base.
- **Saves:** every test run's calls, 77 in October 2026, and up to about 250 records.
- **Needs:**
  - a second base and a token that reaches it;
  - a base secret of its own for test mode (`src/airtable.py` assumes one base today);
  - the workflow's secrets;
  - the schema mirrored by hand and kept in step;
  - a reading of Airtable's terms, though production's capacity does not change.
- **Why it waited:** setup and upkeep. He chose instead to keep the test tables and empty them after each use.
- **Look again if:** test runs become frequent, or emptying the tables after each becomes a chore.

## Weighed and set aside

- **Skipping the evening run's Airtable work:** about 100 calls a month. His last resort; it would delay an evening's postings by about ten hours, which Measure A would see.
- **Reading several tables in one call:** not possible. Airtable's API reads one table per call.
- **Reading fewer fields:** answers are smaller; the number of calls is the same.
- **Airtable's Sync API:** 10,000 rows a request, but a synced table is read-only in Airtable, so he could not classify in it. Its plan availability was not confirmed.
- **Airtable automations to make the copies:** no API calls, but the free plan allows 100 automation runs a month across the workspace, fewer than his classifications. The logic would also sit outside the repository and its tests.
- **A paid plan:** 100,000 calls and 50,000 records a month on Team, but `CLAUDE.md`'s scope floor is no paid services.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-28 | File created | The operator's request of 2026-10-29, Pakistan time, to keep the options he did not approve |
