---
type: how-to
description: The held implementation, assembled in one place: every constraint the Airtable writer, projection and sweep must satisfy, which record each comes from, what is already built, and the order to build in. Audited 2026-09-23 and corrected; two constraints are undecided and named at the top.
status: current
---

# Build the writer

**This is the one implementation on hold.** Everything else in the pipeline
runs. The writer is what stands between a working fetch-and-filter pipeline
and a display the operator can read, and therefore between the project and
ADR-0009's slice Confirmation, which is its definition of done.

**Why this file exists.** The constraints are decided and correct, and they
are spread across twelve records written over six days. A seat starting here
would spend its first hours assembling them and would miss at least one. This
file is that assembly and nothing more: **it decides nothing.** Where it and a
record disagree, the record wins and this file is stale.

## This file was audited on 2026-09-23 and found defective

An audit seat checked every constraint below against its record and found six
errors and eight omissions. The errors are corrected and the omissions folded
in, each verified against the record by the seat that made the correction.
**The corrections have not been checked by a second seat. Verify them before
you build on them**, which you are told to do anyway.

*(Decided 2026-09-23, with the operator's approval, and the projection is now
built on the answers: the pipeline never writes `Status` and
`expired_before_review` is retired; the skip tests every member of a group and
the row carries the representative's identity; the projection performs no
reads; ADR-0040's removal belongs to the sweep's new step 4; `Family` and
`Star reason` are pipeline-owned text. Read the 2026-09-23 Changes rows of
ADR-0004, ADR-0035, ADR-0043 and ADR-0046, not this note.)*

**Two constraints are missing because nobody has decided them yet**, and both
change what the writer does. Do not start the projection until they come back:

1. **Whether the writer ever writes `Status`.** ADR-0035 says the pipeline
   never writes it. ADR-0046 says `expired_before_review` is a `Status` value
   only the pipeline sets. Both are accepted and in force.
2. **Which identity a grouped display row carries.** Skipping a stored
   identity and then grouping lets a classified role return under the next
   member's identity. Demonstrated on live data: a 170-member group whose
   representative was stored re-projected under a different identity.

Also open, raised by the same audit and not settled here: whether the
projection may read `Jobs` at all, given ADR-0004's "we will perform no
reads"; who performs the removal in ADR-0040; and how ADR-0038's family label
and ADR-0044's star reason are classified under ADR-0035:58 before the writer
touches them.

**Checked cold by a second seat on 2026-09-23.** Every clause was re-located
in its record and the group counts were reproduced from the code: 39, 334
admitted, 29, and the 170-member group re-projecting as
`greenhouse:5974247004`. The corrections hold. Two facts the open questions
above were missing, both for the architecture chat:

- **ADR-0004 records its own no-read clause as reversed by ADR-0014**, at its
  lines 30 and 64. Its own 2026-09-17 Changes row and ADR-0035:48 treat the
  clause as standing, and ADR-0046:75 budgets a projection read of `Jobs`. The
  records disagree about whether the clause is in force at all.
- **The `Status` conflict is also inside ADR-0046**: line 50 has the pipeline
  setting `expired_before_review`, and line 134 says `Status` is the
  operator's.

`logs/2026-09-22-speechify-rotation-and-the-writer-check.md` has the table.

## Before you write any code

1. **Read `docs/reference/airtable-schema.md`.** It is the built state of the
   base, read back through the connector, and it marks the one field change
   that is still pending.
2. **Read `docs/reference/retention.md`.** Two clocks, one period, and the
   reason the `Jobs` clock is a last-modified field.
3. **Confirm the three `Status` choices exist**: `not fit`, `poor filtering`,
   `accepted`. **The sweep matches on those exact names.** The connector
   cannot add a choice to an existing single select, so this cannot be done
   from a session. If it is not done, build the client and the projection and
   stop before the sweep. **`Classified at` already exists** on `Jobs` and
   `Jobs test`, created 2026-09-20 and watching `Status` alone
   (`docs/reference/airtable-schema.md`). Step 4 of
   `docs/how-to/airtable-token-and-secrets.md` still lists it as outstanding
   and is stale on that point.

## What already exists

| Thing | Where | State |
|---|---|---|
| The five tables | The Airtable base | Built, schemas read back |
| The token and seven secrets | GitHub repository secrets | Created by the operator 2026-09-18 |
| Grouping | `src/dedupe.py`, `group()` | Built and used by the run log |
| The star | `src/star.py` | Built, 14 tests, 7 mutations. No caller |
| Term to family map | `src/filters.py`, `load_term_families` | Built, all 79 terms |
| The chain | `src/filters.py`, `apply_chain` | Built. Pure: takes rows and a clock |
| The backfill | `src/backfill.py`, called by every run | Built and proven in production |
| Shared retry, backoff, breaker | `src/resilience.py`, imported by the fetch module and the Airtable client | Built 2026-09-23. ADR-0034's mutation Confirmation passes: breaking the backoff fails both modules' tests |
| The Airtable client | `src/airtable.py` | Built 2026-09-23, renamed from `src/airtable_client.py` for Brief 6. One verb, an upsert of exactly ADR-0035's ten fields; no read path; test mode can only reach `Jobs test`. No call yet made to Airtable |
| The projection | `src/projection.py`, called by every committing run | Built 2026-09-23. Over `data` at `bab0acf`: 345 rows read, 334 admitted, 29 groups, 29 to send, `filtered.json` byte-identical afterwards. Not yet run against the base |
| The outcome stores' reader | `src/storage.py`: restored from the branch, and read from the private repository | Built 2026-09-23. Absent reads as empty; an unreachable private repository fails the projection |

## The constraints, and the record each comes from

**One client of its own.** ADR-0034. Not the shared fetch module: different
verb, authentication, budget, rate limit and failure semantics. **Retry,
backoff and circuit breaking stay shared**, as utilities both import, because
that is what CLAUDE.md's one-HTTP-module rule is actually protecting. Fetching
a board has no exception and never gets one.

**Upsert on `Identity`, in batches of ten.** ADR-0035. A retried write must
not duplicate a row, because the operator cannot tell a duplicate from a real
second posting. An upsert matches server side and reads nothing back. ADR-0035
amends ADR-0004's "batched creates" and leaves the rest of that record
standing. **Whether the projection may read `Jobs` is open**: ADR-0004 says
the pipeline performs no reads, and later records assume a read. Raised, not
settled here. **Upsert itself is sourced, not exercised** (ADR-0035:31), and
the record names the fallback if the plan lacks it: creates plus the same
field discipline, with a duplicate after a failed retry a known defect
(ADR-0035:60).

**Write only pipeline-owned fields.** ADR-0035, and this one destroys data if
missed. The record names the ten the writer may send: Title, Employer,
Location, Link, Published, First seen, Order date, Board, Matched term,
Identity. **Three fields are the operator's and are never written:** `Status`,
`Pipeline reason` and `Choice reason`. An upsert updates every field it is
given, so sending `Status` would erase a classification on the next
projection.

Two things this file previously got wrong here. **`Classified at` is not the
operator's**: it is a `lastModifiedTime` field Airtable computes from
`Status`, and nothing sets it by hand (ADR-0046). **`Stage` and the reason
fields are not on `Jobs`**: they live on the classification tables. `Jobs`
carries twelve fields and the operator owns one of them.

**A field added later must be classified before the writer touches it**,
pipeline-owned or operator-owned. ADR-0035 says getting that wrong silently
destroys review data, which is the worst failure available here. This bites
now: ADR-0038's family label and ADR-0044's star reason both need new display
fields and no record classifies either.

**The projection applies the current chain.** ADR-0040. The filtered layer is
append-only and holds rows admitted under older rules, so the projection
filters rather than copies. It reads `filtered.json`, not the raw layer.

**The projection groups.** ADR-0037. The store holds every row; the display
shows one row per ADR-0001 dedupe key with the locations gathered. **On the
current branch 345 stored rows collapse to 39 groups**, measured 2026-09-23
over `filtered.json` at `def4f935` with no chain applied; the audit seat
measured 29 after the chain admits 334. The mismatch with the store is by
design. **The "roughly 25" this file previously carried was ADR-0037's
measurement over 270 rows, copied rather than measured again**, and it is what
made the call budget below look smaller than it is.

**Every member's location must appear in the displayed row.** ADR-0037's
Confirmation, and grouping is worthless without it.

**A stored outcome keeps a row out of the projection.** ADR-0046. The writer
reads the outcome stores and skips any identity present in any of them. This
is what makes a deletion final; without it the next run re-surfaces everything
the operator has ever retired. **There are six stores, not three**: ADR-0047
splits each of ADR-0043's three so aggregator rows land privately.

**Routing between the stores is exclusive.** ADR-0043. A swept row goes to
exactly one store and no identity may appear in two. Its Confirmation is a
pairwise intersection of the store files, all three empty, and the check that
can fail is a hand-written row in two stores. A store holds metadata only and
never a note the operator typed.

**The projection is a reader.** ADR-0040: `filtered.json` must be
byte-identical after any projection run.

**Fifteen days is configuration, not a constant.** ADR-0046 puts it under
ADR-0031. Do not write the number into code.

**Rows that fall out of the chain are removed from the display.** ADR-0040,
and this file previously omitted it entirely. The display converges rather
than accumulating. **One exception: only rows whose `Status` is empty are
removed.** A row the operator marked stays, whatever the rules now say,
because deleting one he marked `applied` destroys the record of an
application. **Who performs this removal is unsettled** across ADR-0014,
ADR-0040 and ADR-0046. Raised, not settled here.

**Aggregator rows go to the private base and the private store.** ADR-0047.
They may now reach Airtable, which closed the long-open question C. They must
never reach the public `data` branch, at any layer, including seen entries.

**Fail visibly.** ADR-0047. A run that cannot write its aggregator rows fails
rather than reporting success having dropped them. Exit 1 carries two causes
and the run says which.

## The sweep, in the order ADR-0046 fixes

Daily. Do not reorder these.

1. **Copy.** Every row in `Jobs` with an operator status and no copy in the
   matching table is created there. A row whose status changed since its copy
   was made has the old copy deleted and a new one created, which resets that
   table's `Classified`.
2. **Store, verify, delete from `Jobs`.** For each row whose `Classified at`
   is more than fifteen days old: write it to its store under ADR-0043, **read
   the store back and confirm its `Identity` is present**, then delete from
   `Jobs`. The reason, or `Stage` for an accepted row, is read from the
   matching copy in the same run. A row that fails verification stays and is
   reported, and no row is deleted on the strength of another row's success.
3. **Delete from the rejection tables** where `Classified` is more than
   fifteen days old. The outcome reached the store in step 2.

**`accepted` is deleted by no clock.** Step 2 writes its rows to the accepted
store so the star can read them; step 3 does not touch that table. A separate
tool the operator runs deletes accepted rows from Airtable alone, never from a
store.

**Write, verify, then delete. Never the reverse.** Unchanged from ADR-0014
through ADR-0045 to ADR-0046.

## The budget

ADR-0046 sizes the whole flow at about 36% of roughly 1,000 calls a month.
Two things hold it there and losing either changes the answer: grouping keeps
`Jobs` small enough for one list call to read it, and writes and deletes batch
ten to a call.

*(Closed 2026-09-23: ADR-0046's budget is corrected to about 450 calls a month,
45%, with the projection at three upsert calls a run. The paragraph below is
kept as the reasoning that led there.)*

**The record's arithmetic is probably low and this is open.** It counts one
upsert call per run. At 29 to 39 groups batched ten to a call that is three or
four calls a run, so 180 to 240 a month rather than 60, and a total of 48% to
54% rather than 36%. It holds only if the writer sends new rows alone, which no
record decides. Do not treat 36% as measured.

## Suggested build order

Each step is independently testable, and the first three need nothing from the
operator.

1. **The client. Built 2026-09-23.** Authenticated writes, the 429 and its
   30-second wait, five requests a second per base (ADR-0034:26), a monthly
   call budget, and the shared retry and backoff extracted so both it and the
   fetch module import them. ADR-0034's Confirmation has two halves, both now
   tests: the grep at :74, that the client imports nothing from the fetch
   module and the fetch module carries no token or write verb; and the
   mutation at :76, break the backoff once and both modules' tests must fail.
   **Left for step 2, the first caller:** the run log must report the
   client's counters beside the fetch budget (ADR-0034:68), and the monthly
   count must be read from the month's run logs on **both** branches, since
   the allowance is per workspace and a runner does not restore run logs.
   Until then each run starts the month at zero. *(2026-09-23: the run log
   carries an `airtable` block, and the month is read back from the run's
   own branch. Reading the other branch is not built: a runner fetches only
   its own, so a test run's calls are not counted against production's month
   or the reverse. Test runs are dispatched by hand and rare.)*
2. **The projection. Built 2026-09-23, offline-verified; the live checks
   below are outstanding.** Read `filtered.json`, apply the chain, group, skip
   stored outcomes, upsert pipeline-owned fields only. ~~Blocked on the two
   open decisions above~~, decided 2026-09-23. ADR-0035's
   Confirmation runs **against `Jobs test`**: project the same batch twice,
   the row count identical after the second run, every pipeline-owned field
   unchanged and a hand-set `Status` surviving. **A test run must be incapable
   of touching production** (ADR-0033), and note that the three classification
   tables have no test copies, so a sweep in test mode has nowhere safe to
   copy into.
3. **The star, wired in.** It exists and has no caller.
4. **The sweep**, once step 4 of the how-to is confirmed. Its Confirmation is
   the one that matters: **give the verify step a row whose store write did not
   happen and watch it refuse to delete.** A verify nobody has seen refuse is
   not a verify, and it guards the only irreversible action in the system.
5. **The private aggregator store**, ADR-0047, once the operator has made the
   repository and the eighth secret exists.

## What to prove before calling it done

ADR-0009's Confirmation: a scheduled run completes unattended, writes rows to
all three layers, and the operator finds a role in the display he had not
already seen by hand. That is the whole
project, and nothing before it counts as the slice being confirmed.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-23 | Step 2 marked built, with the client's new name and the outcome stores' reader added to what exists. The two undecided constraints and the three open questions noted as decided, pointing at the records' Changes rows | Brief 6 built the projection on the architecture chat's five rulings of the same day. The notes are annotations so the questions stay readable beside their answers |
| 2026-09-23 | Checked cold by a second seat. Step 1 built and marked so. Four gaps closed: the budget range at three to four calls a run is 48% to 54%, not "nearer 48%"; step 1 gained ADR-0034's grep Confirmation, its run-log requirement and the five-a-second limit; ADR-0009's Confirmation gained "writes rows to all three layers"; ADR-0035's upsert assumption and fallback added. Two facts added to the open questions | The corrections had been verified only by the seat that made them. Every clause was re-located in its record rather than by the audit's anchors, and the counts reproduced from the code. The four gaps are factual and closed here; the two record conflicts are the architecture chat's and are stated, not settled |
| 2026-09-23 | Six errors corrected and eight omissions folded in, after an audit seat checked every constraint against its record | The file claimed nine source records and cites twelve; invented two of the five operator-owned fields it listed and misattributed a computed field to the operator; said three outcome stores where ADR-0047 says six; carried a group count copied from a measurement over 270 rows, which made the call budget look smaller than it is; treated `Classified at` as outstanding when it was built on 2026-09-20; and omitted ADR-0040's removal path entirely. Two constraints are still missing because no record settles them, and both are now named at the top rather than silently absent. Corrections verified against the records by the correcting seat and **not yet checked by a second** |
| 2026-09-22 | File created at session close | The writer was held for a fresh seat, and its constraints were spread across nine records written over six days. Assembling them at close costs this seat an hour and saves the next one a day, and stops a constraint being missed: the field-ownership rule in ADR-0035 silently destroys the operator's classifications if it is, and it is one clause in the middle of a record about something else |
