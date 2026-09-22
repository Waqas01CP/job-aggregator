---
type: how-to
description: The held implementation, assembled in one place: every constraint the Airtable writer, projection and sweep must satisfy, which record each comes from, what is already built, and the order to build in.
status: current
---

# Build the writer

**This is the one implementation on hold.** Everything else in the pipeline
runs. The writer is what stands between a working fetch-and-filter pipeline
and a display the operator can read, and therefore between the project and
ADR-0009's slice Confirmation, which is its definition of done.

**Why this file exists.** The constraints are decided and correct, and they
are spread across nine records written over six days. A seat starting here
would spend its first hours assembling them and would miss at least one. This
file is that assembly and nothing more: **it decides nothing.** Where it and a
record disagree, the record wins and this file is stale.

## Before you write any code

1. **Read `docs/reference/airtable-schema.md`.** It is the built state of the
   base, read back through the connector, and it marks the one field change
   that is still pending.
2. **Read `docs/reference/retention.md`.** Two clocks, one period, and the
   reason the `Jobs` clock is a last-modified field.
3. **Confirm the operator has done step 4** of
   `docs/how-to/airtable-token-and-secrets.md`: the three `Status` choices and
   the `Classified at` field. **The sweep matches on those exact names.** The
   connector cannot add a choice to an existing single select, so this cannot
   be done from a session. If it is not done, build the client and the
   projection and stop before the sweep.

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

## The constraints, and the record each comes from

**One client of its own.** ADR-0034. Not the shared fetch module: different
verb, authentication, budget, rate limit and failure semantics. **Retry,
backoff and circuit breaking stay shared**, as utilities both import, because
that is what CLAUDE.md's one-HTTP-module rule is actually protecting. Fetching
a board has no exception and never gets one.

**Upsert on `Identity`.** ADR-0035. A retried write must not duplicate a row,
because the operator cannot tell a duplicate from a real second posting. An
upsert matches server side and reads nothing back, so ADR-0004's "we will
perform no reads" is untouched.

**Write only pipeline-owned fields.** ADR-0035, and this one destroys data if
missed. `Status`, `Classified at`, the two reason fields and `Stage` belong to
the operator. An upsert updates every field it is given, so sending `Status`
would erase a classification on the next projection.

**The projection applies the current chain.** ADR-0040. The filtered layer is
append-only and holds rows admitted under older rules, so the projection
filters rather than copies. It reads `filtered.json`, not the raw layer.

**The projection groups.** ADR-0037. The store holds every row; the display
shows one row per ADR-0001 dedupe key with the locations gathered. On the
current branch that is 345 stored rows to roughly 25 display rows, and the
mismatch is by design.

**A stored outcome keeps a row out of the projection.** ADR-0046. The writer
reads the three outcome stores and skips any identity present in any of them.
This is what makes a deletion final; without it the next run re-surfaces
everything the operator has ever retired.

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
`Jobs` to about 25 rows so one list call reads it, and deletes batch ten to a
call.

## Suggested build order

Each step is independently testable, and the first three need nothing from the
operator.

1. **The client.** Authenticated writes, the 429 and its 30-second wait, a
   monthly call budget, and the shared retry and backoff extracted so both it
   and the fetch module import them. ADR-0034's Confirmation is a mutation:
   break the backoff once and both modules' tests must fail, or it is not
   actually shared.
2. **The projection.** Read `filtered.json`, apply the chain, group, skip
   stored outcomes, upsert pipeline-owned fields only. Test that a projection
   run twice leaves the row count unchanged and every operator-owned field
   untouched, with a hand-set `Status` surviving.
3. **The star, wired in.** It exists and has no caller.
4. **The sweep**, once step 4 of the how-to is confirmed. Its Confirmation is
   the one that matters: **give the verify step a row whose store write did not
   happen and watch it refuse to delete.** A verify nobody has seen refuse is
   not a verify, and it guards the only irreversible action in the system.
5. **The private aggregator store**, ADR-0047, once the operator has made the
   repository and the eighth secret exists.

## What to prove before calling it done

ADR-0009's Confirmation: a scheduled run completes unattended and the operator
finds a role in the display he had not already seen by hand. That is the whole
project, and nothing before it counts as the slice being confirmed.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | File created at session close | The writer was held for a fresh seat, and its constraints were spread across nine records written over six days. Assembling them at close costs this seat an hour and saves the next one a day, and stops a constraint being missed: the field-ownership rule in ADR-0035 silently destroys the operator's classifications if it is, and it is one clause in the middle of a record about something else |
