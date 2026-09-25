---
type: log
description: The first production runs with the private store, the contract check and the workspace count verified; the stamp gate widened; the sweep's timing asked; and Brief 7 read against its records before any build.
status: current
---

# The first production mornings, and Brief 7 read cold, 2026-09-25 UTC

Previous log: `2026-09-24-operator-decisions-and-the-next-builds.md`.

| Header | Value |
|---|---|
| Date | 2026-09-25, from 14:33Z, UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `549ba8e`, level with `origin/main`: the chat's four commits, made and pushed by the operator at 14:29Z to 14:30Z |
| Mode | **Mutating** |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means
believed. `[INFERRED]` reasoned from observed data, not tested.

## Last night's runs

**The first scheduled morning run with the private store**, 36091563197 at
03:44Z on `5b63a71` `[VERIFIED]` through the public Actions API, its job
steps and its committed run log from a scratch clone of `data`:

- **The new workflow step ran.** "Fetch the other data branch, for the
  month's Airtable count" succeeded, and "Fail the run if it needs
  attention" was skipped.
- **ADR-0047, production.** `private_store` read `restored: 1, pushed: true,
  files: 3`, no failure; the one file restored was the empty `seen.json` the
  evening run had written. Himalayas fetched 500 in 25 pages, all new, and
  kept 25. The public `data` branch holds no aggregator file, and none of its
  four data files contains "himalayas". The private file counts cannot be
  read without the token, so the Confirmation's first half is met from the
  public side and the run log only.
- **ADR-0048's first check, met.** The morning run fetched Himalayas and
  spent 36 requests; the evening run of 2026-09-24 skipped it with the
  record's reason and spent 11. The fall is 25, the record's "about 25". Its
  check that can fail needs a week of morning polls compared, from about
  2026-10-01.
- **G7 in production.** `month_to_date_by_branch` read `data: 8,
  data-test: 22`, which matches the committed logs: production 5 and 3, test
  6, 6, 5 and 5.

**The contract check's first scheduled run**, 36133006135 at 12:05Z, five
and a half hours after its 06:30Z slot `[VERIFIED]`: exit 0 and a baseline
for all three platforms on `data`, Greenhouse's first board with 250
postings, Lever's with 17 and Himalayas' first page of 20.

## Measured, for ADR-0050's budget

| Production run | Calls | Groups sent | `Jobs` after |
|---|---|---|---|
| 2026-09-24T03:27Z | 5 | 44 | 44 |
| 2026-09-24T17:47Z, Himalayas skipped | 3 | 29 | 44 |
| 2026-09-25T03:44Z | 6 | 52 | 67 |

All `[VERIFIED]` from committed run logs, and `Jobs` read through the
connector on 2026-09-25. The month stood at 36 calls after the morning run,
counting both branches. `Jobs` holds 29 public rows, the 15 Himalayas rows of
2026-09-24 that no run re-sends, and 23 new Himalayas rows. At the morning's
rate it gains about 23 rows a day until the sweep empties it `[INFERRED]`.

## The stamp gate, widened

The pre-commit hook's gate 4 read only the first "Last verified" stamp in
`STATE.md`, and on 2026-09-24 a "Touched" line and a log note each carried a
future stamp past it. It now reads every minute-precision UTC stamp in a
staged `STATE.md` or log. Proved in scratch clones `[VERIFIED]`: a future
stamp on a "Touched" line and one in a log each block the commit, and past
stamps in both pass. One probe first passed when it should have failed,
because resetting the clone between cases had restored the old hook; re-run
with the new hook, it blocked.

## The sweep's timing, asked

The operator wants a classified row in its table "immediately ... as soon as
the status is set", with the stores written on their own clocks, and all the
times stated. Under ADR-0050 the copy is not tied to the fifteen days: it
runs with every fetch. Observed fetch starts are 03:27Z to 03:44Z and 17:33Z
to 17:47Z, so the wait after a status is set is up to about 14 hours, not
ADR-0050's "twelve". "Immediately" is more than ADR-0050 decides. The only
instant route is an Airtable automation, which ADR-0046 considered and
rejected: automations cannot delete, the free plan allows 100 runs a month
(ADR-0004), and the mechanism sits outside version control. Changing ADR-0050
in its first week is one of Brief 7's hand-back conditions, so this goes back
to the operator and the chat.

## Brief 7, read against its records before any build

The architecture chat's Brief 7 arrived with the operator's message.
`briefs/architecture.md` is ticked executed. Read against ADR-0050, ADR-0049
and the tree before building:

- **The chat's files were already committed.** The brief says they are "on
  disk, uncommitted"; the operator committed and pushed them as `e3971ca`,
  `20d5146`, `a71b281` and `549ba8e` before the seat read it.
- **"Within twelve hours" is about fourteen** at the observed run times.
- **The copy step's reads are not in ADR-0050's budget table.** Copying on
  every fetch needs `Status` from `Jobs` on every fetch, and an idempotent
  copy must know which copies exist. The table counts one `Jobs` read and
  three table reads a day. Reading all four on both runs adds about 120 calls
  a month, taking the total from about 600 to about 720, or 72%
  `[INFERRED]`. A copy ledger kept on the data branch would avoid the evening
  table reads; that design is the seat's to choose within the brief, and it
  is reported rather than treated as a stop.
- **A `Jobs` read costs one call per 100 records.** At 67 rows today that is
  one, but the table counts one whatever the size.
- **The operator's Y4** would change ADR-0050's step 1 if he keeps
  "immediately". That is a hand-back, not the seat's to decide.

Nothing of Brief 7 is built yet. The seat waits for the operator's answer on
Y4 and his go.
