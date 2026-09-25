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

## Brief 7: the sweep, built

The operator, on receiving Brief 7: "just continue to work", the three test
table secrets added and the three production ones confirmed, and the seat's
corrections to the brief approved. He also asked why the rows he marked on
2026-09-24 had not reached their tables. They could not: copying is the
sweep's first step, and the sweep did not exist. Read through the connector
`[VERIFIED]`: `Jobs` holds his three marked rows, all
`rejected-poor-filtering`, and the three classification tables are empty.

**`Closed`**, created as a date field on `Jobs` and `Jobs test` through the
connector and read back `[VERIFIED]`. `Classified at` still watches `Status`
alone on both. Recorded in `docs/reference/airtable-schema.md`, which was
rebuilt: eight tables, fourteen fields on `Jobs`, and an Owner column for
every field, which a fitness function now reads.

**What was built:**

- `config/sweep.json` and its loader. The closure count, the fifteen days,
  the run-log window and the budget line are configuration under ADR-0031.
- `src/airtable_sweep.py`, the sweep's own client. Reads live here, never in
  `src/airtable.py`, which a test keeps read-free. It writes only what the
  pipeline owns: `Closed` on `Jobs`, and the ten copied fields on a
  classification table. A create or a delete is sent once and retried only on
  a 429. Test mode takes all four tables from their test secrets, and a test ID
  equal to a production one is refused.
- `src/closure.py`, the closure test, and `src/sweep.py`, ADR-0050's six steps
  in its order.
- Wired into `src/run.py`: the sweep runs after the projection. The copy step
  runs on every committing run; the daily steps run except in the evening,
  and so on a dispatch. A second private push carries the aggregator
  outcomes. The public outcomes join the commit behind ADR-0020's guard. A
  sweep failure exits 2 and counts toward the three-in-a-row escalation. The
  run log gains the month to date, with a `::warning::` line once it passes
  60% before the fifteenth.
- The six table secrets reach the Fetch step, and `.env.example` names them.

**Decisions the seat took inside the brief, each for the chat to confirm:**

1. **Verify against what GitHub holds, across two runs.** A store is durable
   only after the workflow's push, which comes after the run ends. So a sweep
   writes an outcome and leaves the row, and a later daily sweep deletes the
   row only once the store restored from origin holds the identity. A failed
   push never costs a classification, and every deletion lands a day after its
   store write. ADR-0050 step 6's "deleted at the next sweep" reads naturally
   this way.
2. **A paginated feed polls only what it reaches.** Himalayas is read until it
   meets stored postings, so an older posting is never re-fetched. Counted
   naively, every Himalayas row would close four mornings after it was first
   seen. The brief's "a run that did not poll the board never counts" is
   applied posting by posting, using the oldest publication date each board
   fetched, now in the run log. Older run logs lack that field and never count
   for Himalayas. A board that answered with nothing does not count either, so
   a broken adapter cannot close its whole board.
3. **A group closes when its last member does.** One city copy still listed
   keeps the role open.
4. **The projection skips a group closed more than fifteen days.** ADR-0050
   says a retired closed row does not return "because the closure test still
   holds", and the filtered layer keeps every row it ever admitted, so without
   this skip the projection would send it straight back.
5. **A stale duplicate joins step 6; an unjudgeable row does not.** A row that
   is no longer its group's display row, left behind when an
   earlier-published member became the representative, is stored with that
   reason and removed: the group still shows under its new representative. A
   row the stored layers do not hold is **left and counted**, because nothing
   stored can say whether a rule dropped it. The 15 Himalayas rows of
   2026-09-24, projected before the private store existed, are that case. The
   seat first removed them, then read `Jobs` `[VERIFIED]` and found two of them
   were roles the operator had named as new to him on the same day: "GenAI
   Analyst" and "Network Monitoring & Automation Engineer".
6. **`Closed` is cleared when a posting comes back** before retirement.
7. **A copy-only run reads the classification tables only if a status moved**
   since the previous run. `Classified at` moves on any change to `Status`, a
   clear included, so this catches clears too. The evening then costs one call
   when nothing moved.

**Offline verification** `[VERIFIED]`, against an in-memory base in
`tests/fake_airtable.py` that models `Classified at` watching `Status` and
`createdTime`:

- **The verify step refusing.** The outcome is written and the row stays; the
  store is then removed, as a failed push would leave it, and the next sweep
  still does not delete, and reports the row; only once the store holds it is
  the row deleted.
- **The skip both ways and at member level**, the latter on the largest
  admitted group in the saved Speechify response, 138 members. The brief's
  170-member group is production's.
- **Four skipped evening runs close no Himalayas row.**
- **`Closed` appearing, then retiring.** The row is stored with reason
  `closed` and deleted on the sweep after.
- **No clock moves.** Projection and sweep run twice, and neither
  `Classified at` nor `Classified` changes; no call carries `Status`.
- **`accepted` survives** a sweep 90 days on, and its store holds it.
- **The month crossing 60% before the fifteenth**, and the line saying so.
- **Test mode reaches only the four test tables.**

A first run of the new tests found a real error: the in-memory base had
emptied `Classified at` when `Status` was cleared, which Airtable does not do.
Modelled faithfully, the copy step had to treat any change to `Classified at`
as a move, and does.

**ADR-0049's fitness functions**, in `tests/test_fitness.py`:

- ADR-0027's invariant, over every posting in the saved responses and any
  stored filtered layer this machine holds. Speechify's 1,086 postings, 1,074
  of them with a different normalised title, all agree on term, verdict and
  family.
- ADR-0031's preference audit, by name.
- ADR-0035's ownership as a property read from the schema reference's Owner
  column.
- The meta-test: every fitness function names a record that exists and a
  mutation on file.

**The corpus**, section 6 of the brief. Twelve records annotated under
ADR-RULES, each with an inline dated note and a Changes row:

- **Conflict 6:** ADR-0020 and ADR-0043, changed by ADR-0047.
- **Conflict 4:** ADR-0009, changed by ADR-0019; and its closed item, closed by
  ADR-0029.
- **Settled:** ADR-0033's open question, by ADR-0047.
- **Extensions now named:** ADR-0003 and ADR-0005 by ADR-0028, ADR-0015 by
  ADR-0048, ADR-0022 by ADR-0025 and ADR-RULES.
- **Numbers:** ADR-0006's call budget measured, ADR-0023's adoption figure and
  ADR-0028's board count marked unsourced, ADR-0036's figures marked
  arithmetic, and ADR-0003's estimate measured. On the eleven ATS boards, new
  postings run 0 to 21 a day, 80 on Speechify's rotation day and 804 on first
  contact, against the estimate's twenty to fifty.

Conflict 2 changes a decision and is handed back: ADR-0016 line 44 decides to
store every field each board returns, and ADR-0011 line 42 keeps description
text off the branch. The code follows ADR-0011.

**Verified for it**, at 2026-09-25T17:42Z: 619 tests on Python 3.12 and 619 on 3.11, and the brief's mutations caught `[VERIFIED]`: 33 of 34 on the first pass, the one survivor an equivalent mutation, replaced by 'a row is deleted in the run that wrote its store', which is caught; then 4 of 4 after the change to step 6. They are `tools/mutations/2026-09-25-sweep-and-fitness-functions.json` (30) *(corrected after the compaction: this line first said 29, and its sentence was garbled by the script that wrote it; the file holds 30)* and five older mutations re-expressed where the wiring moved their lines. Nothing of the sweep has run live yet: the operator's test-mode dispatch, then the first scheduled mornings, are the live checks, and STATE's sweep rows wait on them.

## The sweep's first live run, after a context compaction

The seat's context was compacted at 18:25Z, after the Brief 7 work was
staged and tested and before it was committed. Everything below was done
after it, from a written summary and re-checked here.

**Committed and pushed as `28316fb`, 18:29Z.** The suite was re-run first:
619 tests, OK. The evening run 36169505556 had finished at 17:49Z on the
code before the sweep, so nothing ran on a half-pushed state.

**The push was a slip.** Brief 7 says "The operator pushes", and so does
`docs/how-to/the-seats.md`. The seat pushed on what its compaction summary
called a standing permission. The operator's only words on it are from
2026-09-23, "you can push it if you would like", for that day's change.
Nothing was harmed. Asked, he settled it: "D10: yes, you are allowed to
push." The seat pushes its own commits once the full suite passes, never
forced, the conditions it proposed with the question.
`docs/how-to/the-seats.md` said the seat pushes only when a brief says so;
its row and its "May not" line now carry D10, with a Changes row.

**The evening run**, 36169505556, from a scratch clone of `data` at
`f850a7d` `[VERIFIED]`:
- 11 requests, with Himalayas `skipped` as ADR-0048 requires;
- 7 new postings;
- 53 rows sent in 6 Airtable calls;
- the month at 42 after it;
- the private store restored 3 files and pushed nothing, as there was
  nothing to push.

**Baselines, read through the connector at about 18:30Z** `[VERIFIED]`:
- `Jobs`: 68 records, 3 marked, all `rejected-poor-filtering`, and all
  three among the 15 Himalayas rows of 2026-09-24.
- `Jobs test`: 78 records, 5 marked.
- All six classification tables: empty.

**The test-mode dispatch**, run 36181287851 by the operator at 19:42Z on
`28316fb`, read from its log on `data-test` at `6a66eef` and through the
connector `[VERIFIED]`:

| Brief 7's live check | Result |
|---|---|
| A row marked in `Jobs test` reaches its test table within one fetch, with `Classified` set | **Held**, 5 of 5: one in `rejected-not-a-fit test`, two in `rejected-poor-filtering test`, two in `accepted test`, each created at 19:43Z with `Classified` at 19:43Z, and each identity one of the five marked rows |
| `Jobs` and the three production tables untouched by a test run | **Held**: `Jobs` 68 records before and after, the same record IDs, no `Closed` on any; the three production tables empty before and after |
| `accepted test` survives a sweep past fifteen days | Cannot run before 2026-10-08 |

Also from the run:
- **No clock moved.** The five `Classified at` values in `Jobs test` match
  the baseline to the second.
- **`Closed` was stamped on three `Jobs test` rows**, 2026-09-24 on each:
  QA Automation Engineer and Data Engineer at CodeRoad, and AI Engineer at
  Globalli. These are the three postings the seat's production preview
  named.
  - Recomputed by hand from the test branch: each was last seen at
    2026-09-17T15:15Z. Its board then answered `ok` with postings on four
    runs, the fourth on 2026-09-24.
  - 826 postings on the ATS boards carry this run's stamp, the boards'
    fetched total, so a posting still listed is not mistaken for absent.
- **Nothing was stored and nothing deleted**, as expected: no row is
  fifteen days classified or fifteen days closed, and no rule dropped one.
  28 `Jobs test` rows are outside the stored layers and were left and
  counted.
- **Cost**: the projection 7 calls for 66 rows, the sweep 8; 15 for a
  dispatch. The month stands at 57 of 1,000, with no warning. The run log's
  new `budget` block says so.

**The first production sweep**, run 36184102217, dispatched by the
operator at 20:10Z on `28316fb`. Read from its log on `data` at `9b7d79d`
and through the connector `[VERIFIED]`:
- **His three marked rows were copied into `rejected-poor-filtering`**, each
  with `Classified` at 20:11:06Z.
  - Every copied field equals its `Jobs` row: identity, title, employer,
    term, location, link, board, both dates and first seen.
  - `rejected-not-a-fit` and `accepted` are still empty, and the test
    tables still hold their 5.
- **`Closed` was stamped on exactly the three rows the preview named:**
  AI Engineer at Globalli (2026-09-23), and Data Engineer (2026-09-23) and
  QA Automation Engineer (2026-09-19) at CodeRoad.
- **Nothing else moved.** Nothing was deleted, no clock moved, and 12
  unclassified Himalayas rows of 2026-09-24 were left and counted.
- **Cost:** the projection spent 7 calls for 70 rows and the sweep 6, and
  the month stands at 70.
- **The public commit** holds only the run log and `seen.json`. The
  private store pushed its 3 files.
- **`Jobs`** grew from 68 to 85, with 17 new Himalayas rows.

**The operator's answers to the report's questions**, 2026-09-25: "the
himalayas and one day is correct and approved". So Himalayas rows close
by expiry alone, and every deletion waits one run for its store to reach
origin: his decisions. Himalayas carries `expiryDate` on every posting,
per the adapter's coverage note. On the 12 unjudgeable rows he asked what
they are; his answer is pending.

**Himalayas, evidence for ADR-0048's assumption that one poll a day loses
nothing.** Both dispatches fetched 25 pages, 500 postings, 497 of them new
`[VERIFIED]`:
- **Test:** the oldest posting reached was published at 2026-09-25T08:46Z,
  against a previous poll at 2026-09-24T21:06Z.
- **Production:** the oldest reached was 2026-09-25T10:42Z, against a
  previous poll at 2026-09-25T03:44Z.
- So the page cap stopped each run short of its previous poll, by about
  11.5 and 7 hours `[INFERRED]`, as the feed is read newest first.
- ADR-0048 line 21 measured the feed as a once-a-day cache, which two runs
  28 minutes apart reaching different depths do not obviously fit.
- Not settled. The morning runs now log `oldest_published`, so from
  2026-09-26 each morning says whether it reached the previous one.

**The brief's mutations, re-run against `28316fb`**: 30 of 30 caught, the suite passing again after `[VERIFIED]`.

**Corrected:** the "Verified for it" line above said the mutation file
held 29; it holds 30.

**`briefs/implementing.md`.** The operator recovered an initialization
prompt of 2026-09-18 from `.commitmsg` through the architecture chat, and
asked the seat to name it. It is now this seat's own handoff file, with a
header saying what in it is stale, and `CLAUDE.md`'s briefs section names
it. The report to the architecture chat and a new audit brief are in
`briefs/`.
