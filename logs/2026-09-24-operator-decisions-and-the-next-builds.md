---
type: log
description: The operator's decisions of 2026-09-24 while the architecture chat was unavailable, the implementing seat's own backlog cleared, and the builds those decisions released, with the evidence gathered for the next brief.
status: current
---

# The operator's decisions, and the builds they released, 2026-09-24 UTC

Previous log: `2026-09-23-the-projection.md`, whose fourth section covers the
audit and production's first projection.

| Header | Value |
|---|---|
| Date | 2026-09-24, from 10:40Z, UTC |
| Model | claude-opus-5-5 |
| HEAD at start | `df7204e`, level with `origin/main` |
| Mode | **Mutating** |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means
believed. `[INFERRED]` reasoned from observed data, not tested.

## Why this session decided without the architecture chat

The chat could not be reached for some hours. The operator asked what could
move without it. The seat split the pending work into what is its own, what is
already settled by accepted records and needs only a go, what is the
operator's to decide, and what only the chat can do. The operator decided
everything in his column. Under `CLAUDE.md`'s authority order his instruction
in conversation ranks first, so each decision below takes effect now, and the
chat records them afterwards from an addendum to the pending brief.

## The operator's decisions, as given

| # | Question | Decision |
|---|---|---|
| Y1 | `Status` wording | `applied` becomes `accepted`, with shortlisted or applied held by `Stage` in the `accepted` table. The two rejections are named after their tables. **The three values are the table names: `rejected-not-a-fit`, `rejected-poor-filtering`, `accepted`.** This departs from ADR-0046's `not fit` and `poor filtering`; the chat records it |
| Y1 | ADR-0009's slice Confirmation | He has opened `Jobs` and sees roles he wants and roles that should not be there, which he is marking. Having searched by hand before, he had seen most of the roles; the Confirmation waits on one he had not |
| Y2 | Changing the choices | The connector cannot: `update_field` accepts only a formula in its options `[VERIFIED]` from its schema. He renames them in the browser, which keeps the rows he has already marked |
| D1 | A projection failing run after run | After three consecutive failed projections the run still commits and pushes, then the workflow marks the run failed. Approved, after the seat confirmed his understanding: marking a run failed only changes its status in GitHub and happens after the data is saved, so nothing is lost or altered |
| D2 | GitHub's failed-run email | Does not breach "no notification system". His standing rule, his ruling |
| D3 | Closed postings | *(Answered 2026-09-24T15:10Z, below: stored with the reason "closed", visible for fifteen days after it closed, then deleted under the same rule.)* **Clarification asked and pending.** He does not want to see a closed role and mentioned the fifteen-day rule; the seat asked whether a closed row goes at the next sweep, stored with the reason, or after fifteen days |
| D4 | "Sênior" escaping the seniority rule | Strip accents before matching, **with extra care**: every title's verdict before and after is compared, and any change is shown before it ships |
| D5 | Aggregator rows accumulating | Build ADR-0047's write path. *(Corrected 2026-09-24T15:12Z, stamped 15:15Z when written, ahead of the clock: not answered on its own. His reply skipped D5; this is taken from his go on G1 to G6, which includes G2, the write path, and was the recommended option)* |
| D6 | The private store cannot be written | Exit 2, not 1, keeping the public fetch. Test that the repository saves before relying on it. **`AGGREGATOR_STORE_TOKEN` expires on 2027-01-01**, to be recorded |
| D7 | Test copies of the three classification tables | Yes. The real tables may be used meanwhile |
| D8 | Banyan Canopy | The deferral to 2026-10-07 stands |
| Go | G1 to G6 | Go on all six |

## The seat's own backlog, cleared

**The map generator's status gate.** It tested only that a record had a
status, so `status: acepted` passed, which the corpus audit proved. It now
accepts MADR 4.0.0's `proposed`, `rejected`, `accepted`, `deprecated`, and
`superseded by ADR-NNNN` naming a record that exists. `tests/test_generate_map.py`
gives it the audit's misspelling, a supersession naming ADR-0999, and four
malformed supersessions, each refused `[VERIFIED]`; the real corpus passes.

**ResourceWarnings.** Four bare `open().read()` calls in `tests/test_backfill.py`
now close their files; the full suite reports none `[VERIFIED]`.

**Fourteen records annotated under ADR-RULES**, each with a dated inline note
and a Changes row, every cited line re-read first `[VERIFIED]`:

| Record | Annotation |
|---|---|
| ADR-0048 | Wrong: the 500 postings are 25 pages of 20, the adapter's page cap, not ADR-0028's request cap |
| ADR-0005 | Falsified: five to fifty roles per board, against ADR-0001's median 27 and maximum 1086; and aggregators' "out of scope" made stale by ADR-0019 |
| ADR-0012 | Stale: a third credential, the private store's token |
| ADR-0013 | Stale: four outcome stores, each with a private copy |
| ADR-0023 | Stale: `MAP.md` and the seats file are now required reads |
| ADR-0007 | Stale: date coverage checked across 16 platforms since |
| ADR-0027 | Measured: 11 Speechify keys on 2026-09-17 and 5 now, against an estimated 8 |
| ADR-0004 | Stale: API usage is ADR-0046's 45% and a measured 5 calls a run, not 5% to 9% |
| ADR-0043, ADR-0030, ADR-0032 | Status names now the table names |
| ADR-0032, ADR-0035, ADR-0038, ADR-0039 | Eight line references two lines early since `dc02b0f` added two frontmatter lines to every record; every target confirmed at the cited line plus two |

Left for the chat, as ADR-RULES requires: conflicts between live records, the
form an unmarked amendment should take, the EY contradiction between ADR-0021
and ADR-0029, and numbers the audit found outside Assumptions.

## Evidence for the next brief

**The duplicated Motive role** `[VERIFIED]` through the connector: both rows
in `Jobs` read employer "Motive" and the same title, one from Motive's
Greenhouse board published 2026-09-19T03:03Z and one through Himalayas dated
2026-09-23T23:07Z. ADR-0001's key includes the publication date, and
Himalayas stamps its own, so an aggregator's copy of an ATS posting never
shares a key with the original. The employer names agree; the date defeats
the match.

**GitHub's 60-day shutoff** `[VERIFIED]` read on GitHub's documentation page
for disabling workflows: "In a public repository, scheduled workflows are
automatically disabled when no repository activity has occurred in 60 days."
The page does not define activity. Whether the pipeline's own pushes to
`data` count stays unknown.

## Built: the Title description, accents, one Himalayas poll a day, and escalation

**G3, the `Title` field's description** on `Jobs` and `Jobs test`, through
the connector `[VERIFIED]` `success: true` on both: it now says the title is
normalised, why, and that the raw title is kept in the stored layers.

**D4, accents.** Before any code changed, every title and employer the seat
could reach was folded both ways `[VERIFIED]`: 3,308 records from the `data`
and `data-test` raw layers, the local archive holding 500 Himalayas rows, the
Himalayas cassette, and the production title that started it. 1,458 distinct
titles, 56 with any non-ASCII character. **21 titles fold differently and one
verdict changes**, "Fullstack Developer | Sênior (13593)", now dropped by the
seniority rule; the other twenty are city names or titles no term matched
either way. **No employer folds differently, and no two of the 1,001 stored
normalised titles merge into one dedupe key.** The strip touches only a mark
that follows a plain Latin letter, so a Japanese voicing mark or a Greek
accent survives *(narrower than the code, found by the audit of 2026-09-24,
F13: any mark after any ASCII character goes, a stray one after a digit or
space included, and a mark on a non-ASCII Latin letter such as `ǿ` stays)*, and a string with no Latin accent folds exactly as before,
since NFC after NFKD is NFKC; tests pin all three. `docs/reference/title-pool.md`
gains the rule as normalisation step 1. ADR-0021 specifies the fold, so this
is for the chat to record.

**G1, ADR-0048.** A board may carry `poll_slots`; Himalayas carries
`["morning"]`. The workflow names the slot from the cron that fired the run,
`0 0` morning and `0 13` evening, and a dispatch or a local run is neither and
polls every board, so test runs still see Himalayas. On an evening run the
board is logged `skipped` with its reason, never absent. Tests prove the
evening run never asks for it, the morning run does, a misspelt slot is
refused by the config loader, and the workflow's mapping names exactly the
two crons it schedules. The record's Confirmation needs the first evening
run after the push; its check that can fail needs Himalayas' identities
stored, which waits on G2.

**D1, escalation.** The run log gains an `attention` block: how many runs in
a row, this one included, have had a failed projection. On the third the run
commits as usual, writes `escalate=true` to the workflow's step outputs, and a
new last step, after the push, fails the run. A success resets the count, a
no-commit run never escalates, and failing to read the previous logs never
costs the run its commit. Tests prove the third failure escalates and the
first two do not, that all three committed, that a success in between resets
it, and that the escalation step is the workflow's last, after the push.
`CLAUDE.md`'s exit-code line and ADR-0034's Changes carry it; exit codes are
unchanged.

## Built: Family in the display

**G4, `Family`.** ADR-0038's label, which ADR-0035's Changes classified
pipeline-owned on 2026-09-23. The field was created on `Jobs` and
`Jobs test` through the connector as single-line text *(the two field IDs
first written here were removed on 2026-09-24 after that day's audit, F1:
`docs/how-to/the-seats.md` holds field IDs secret. `101371d` still carries
them in history)* `[VERIFIED]` from the connector's answer. The
projection sends it as the eleventh pipeline-owned field: the family of the
term shown in `Matched term`, a lookup on the term and never a reading of the
title. Both test files pin the eleven by hand. One test sends two rows from
different families; another uses a row whose raw and normalised titles name
terms in different families, so a `Family` taken from the raw title fails it.
Six mutations, all caught `[VERIFIED]`: `tools/mutations/2026-09-24-family.json`.
Rows already in `Jobs` gain their `Family` on the next projection, since every
run re-sends the whole layer. *(Wrong for aggregator rows, found by the audit
of 2026-09-24, F6: the 15 Himalayas rows projected into `Jobs` at 03:27Z, and
30 in `Jobs test`, sit in no store, so no run re-sends them unless a morning
run fetches them again. The 29 public rows in `Jobs` carry `Family` since the
evening run.)*

The D1 escalation tests had two survivors, both closed before this commit:
the reset test now checks the count after fail, fail, success, fail, and the
no-commit test fails the plan itself, since a failing Airtable client is
never reached by a run that only plans. `tools/mutations/2026-09-24-accents-slots-escalation.json`,
ten mutations, all caught.

## Built: the private store, and the test classification tables

**G2, ADR-0047's write path.** `src/private_store.py` holds one run's session
with the private repository. The repository gets one branch per mode, `data`
and `data-test`, with ADR-0020's public layout: `fetch-all/<source>.json`,
`filtered.json`, `seen.json`, `outcomes/`. A committing run opens it after
the public restore and before any fetch, and replaces the aggregator working
copies with the branch's. It pushes them back as a fast-forward once the
fetch is written, before the projection. Nothing reads the repository's
default branch any more. GitHub makes the first branch pushed to an empty
repository its default. Brief 6's reader read that branch, so once the write
path existed, a test run pushing first would have given production the test
branch's stores. The projection now reads the private outcome stores from the
restored working copies, and `storage.read_private_files` is removed.

Three rules, each with a test and a mutation:

- **A run that could not restore never writes.** It holds no store object
  after a failed restore. The test replaces the restore with one that fails
  and the push with a recorder, and the recorder stays empty.
- **A failed restore skips the aggregator boards and fails the projection.**
  Nothing they returned could be kept, and the private outcome stores are
  unknown, so projecting could bring back a role the operator retired. A
  failed push fails neither: the stores were read, so the display is sent.
- **D6: exit 2, the public fetch committed.** The run log's `private_store`
  block names the failure, and it counts toward the three-in-a-row
  escalation. `CLAUDE.md`'s exit-code line and ADR-0047's Changes carry it.

Offline, against a local bare repository through a file URL, so git itself
runs: a first write creates the branch and a fresh machine continues from it;
the public branch holds no Himalayas identity; test mode writes `data-test`
only; a push racing another is refused, not forced; and a stored
`accepted.json` keeps its role out of the display. Thirteen mutations, all
caught `[VERIFIED]`: `tools/mutations/2026-09-24-private-store.json`. The run
tests that do not look at the store use an in-memory stand-in, because real
git on every run took this machine's `test_run.py` from about 30 to 84
seconds.

**Not yet shown live:** that the token can write. Every run so far has only
read the repository. The operator's test-mode dispatch proves it. Then the
first scheduled morning run is ADR-0047's Confirmation: the public branch
holds no aggregator file or identity, and the run log's `private_store` block
reads `pushed`.

**D7, the test classification tables.** `rejected-not-a-fit test`,
`rejected-poor-filtering test` and `accepted test` were created through the
connector with the originals' fields, descriptions and choices `[VERIFIED]`
from the connector's answers. `Classified` is created time, which
`create_table` cannot make, so it was added afterwards with `create_field`.
The sweep needs a secret for each table ID, which its brief names.

## Built: the contract check

**G6, ADR-0018 and ADR-0036.** `src/contract.py` asks the first configured
board of each platform for one response and fingerprints the fields the
adapter consumes. Each field's shape is recorded as words across every
posting in the response: present in all, some or none; null never, in some
or always; and its type names. It compares that with the fingerprint on the
data branch, names every field whose shape changed with both shapes, and
exits 0. A crash exits 1 and commits no log. Its logs live in
`logs-contract/`, never `logs-runs/`: the escalation counts failures in a row
from `logs-runs/`, and a contract log there would read as a success. A board
that cannot be answered is logged and keeps its last fingerprint.
`.github/workflows/contract.yml` runs it daily at 06:30 UTC in the fetch's
concurrency group, with no secrets. `tools/run_log_report.py` closes its
report with the check.

Each adapter now declares `CONSUMED`, and a test reads the adapter's source
and holds the list to every key `parse()` reads, both ways. A second test
gives that reader a key through a literal, a module constant and a
subscript, so it cannot be blind. Eleven mutations, all caught `[VERIFIED]`:
`tools/mutations/2026-09-24-contract-check.json`. ADR-0036's two
Confirmations run as tests.

**Against the live boards** `[VERIFIED]`, `--test-mode --no-commit`, three
requests a check: Greenhouse's first board, `veeamsoftware`, with 259
postings; Lever's `smart-working-solutions` with 16; Himalayas' first page
of 20. The first check recorded a baseline and the second found nothing
changed. Then `absolute_url` was removed by hand from the stored Greenhouse
fingerprint, and the third check named it: "was not in the stored
fingerprint, now present in all, null never, string". Exit 0 each time. That
is ADR-0018's Confirmation, on this machine rather than on the branch.

Two judgments for the architecture chat. Himalayas' fingerprint sits on the
public branch: it holds field names, type names and the three-way words,
never a value, and a test proves no posting value reaches it. And ADR-0036's
Airtable row is not built, since it needs a table.

## The first live write to the private store, D3 answered, and `Status` as it stands

**The token writes** `[VERIFIED]`. The operator's test-mode dispatch,
run 36016481510 at `e2a481d`, committed `fe8f56f` to `data-test`. Its run log
reads `private_store: {branch: data-test, restored: 0, pushed: true,
files: 3, failure: null}`. Himalayas fetched 500 in 25 pages, all new, and
kept 32. The projection sent 48 groups to `Jobs test` in 5 calls with no
failure. The public `data-test` branch holds `fetch-all/greenhouse.json`,
`fetch-all/lever.json`, `filtered.json`, `seen.json` and run logs, and none
of those four data files contains the string "himalayas". So both halves of
ADR-0047's Confirmation hold on the test branch, except the private file
counts, which this seat cannot read without the token. A second run showing
`restored: 3` and a Himalayas `new` well under 500 proves the round trip.
`Family` is filled on the `Jobs test` rows this run re-sent `[VERIFIED]`, so
G4 is live.

**D3, the operator's answer**, 2026-09-24: "it should be stored with reason
as you recommended but later should be deleted meaning visible for 15 days
then the delete rules apply on this as well." So a closed posting is stored
with the reason "closed", stays in `Jobs` for fifteen days after it closed,
then goes. The pipeline never writes `Status` (ADR-0046, 2026-09-23), and
`Classified at` moves only when `Status` does. So the closure needs its own
clock and, for the operator to tell a closed row from an open one in those
fifteen days, probably a visible mark. Both are the sweep brief's to design.

**`Status` as it stands** `[VERIFIED]` through the connector. Both tables
still hold the original four choices, `applied`, `rejected_pipeline`,
`rejected_choice` and `expired_before_review`; ADR-0046's `not fit` and
`poor filtering` never reached the base. `Jobs` has 3 marked rows, all
`rejected_pipeline`. `Jobs test` has 5: 2 `applied`, 1 `rejected_choice`,
2 `rejected_pipeline`. No row in either holds `expired_before_review`, so
deleting it clears nothing. Renaming the other three in the browser, as the
operator was told, keeps every marked row's meaning. When he tried it,
Airtable warned that the change "will impact 2 dependencies": `Classified at`,
which watches `Status`, and the `To review` view, which filters on it. The
seat's answer: proceed. Whether Airtable counts a rename as a change to each
marked row's `Status`, restarting `Classified at`, is unknown. If it does,
the only effect is that those rows' fifteen-day clocks start later, since
nothing deletes on that clock yet. The seat checks `Classified at` after the
rename.

## The `Status` rename, done

The operator renamed the choices in the browser. Read back through the
connector at 15:30Z `[VERIFIED]`:

- Both tables hold exactly `accepted`, `rejected-poor-filtering` and
  `rejected-not-a-fit`, and `expired_before_review` is gone.
- Each choice kept its ID: `applied` is `accepted`, `rejected_pipeline` is
  `rejected-poor-filtering`, `rejected_choice` is `rejected-not-a-fit`.
- All 8 marked rows keep their meaning: 3 in `Jobs`, all
  `rejected-poor-filtering`; in `Jobs test`, 2 `accepted`, 1
  `rejected-not-a-fit` and 2 `rejected-poor-filtering`.
- **Not one `Classified at` moved.** Each matches its value read at 15:08Z,
  so a rename does not restart a row's fifteen-day clock. That answers the
  question the dependency warning raised.
- The `To review` view still exists. Its filter cannot be read through the
  connector.

The sweep now waits only on its brief.

## Where briefs now live

The operator's decision: the latest brief to each other seat is kept in the
repository, gitignored, one file per seat, overwritten by the next, with a
box on its first line that is ticked with the date once he says it has been
executed. `briefs/architecture.md` holds the unexecuted brief of 10:12Z,
recovered word for word from the session transcript, followed by the
addendum. Its own line says 10:15Z, about three minutes ahead of the message
that carried it; kept as he copied it and noted in the file's header.
`briefs/audit.md` holds the audit brief. The map generator walks every `.md`
file, ignored or not, so `briefs/` joined its skip list beside `data/`;
without that, a local `MAP.md` would name files no clean clone has.

## The second audit, and what was done

The audit seat, started fresh, audited `f864053..06c3749` from 16:47Z to
18:14Z. It found no path that loses or corrupts data, reproduced the D4 check
to the number, and caught 40 of 40 of this range's mutations. It made fourteen
findings. Each is closed below or left with the owner named.

| # | Finding | Done |
|---|---|---|
| F1 | Two live Airtable field IDs in this log, pushed in `101371d` | Removed from the log. History still holds them; rewriting a public branch's history is the operator's call |
| F2 | The guards around the previous-logs read in `attention()` and the private store's git time limit had no test | A run test where the read raises still commits and exits 2; a store test checks every git call carries the limit and a hang raises "timed out". `needs_attention` now refuses a log that is not an object, so `attention()` cannot raise on one |
| F3 | A third run arriving could cancel a waiting fetch, since the contract check shares the group | `queue: max` on both workflows, from GitHub's concurrency documentation `[VERIFIED]`; a workflow test holds it |
| F4 | Swapping the slot labels, or `main` ignoring `RUN_SLOT`, failed no test | The workflow test pins which cron is which; a run test sets `RUN_SLOT` and checks Himalayas is asked in the morning and skipped in the evening |
| F5 | `CONSUMED` was compared on last names only | A test holds every undotted path to a key the saved response has, and every dotted one to a declared parent |
| F6 | "Rows already in `Jobs` gain their `Family`" was wrong for aggregator rows | Annotated above: 15 Himalayas rows in `Jobs` and 30 in `Jobs test` sit in no store and are never re-sent |
| F7 | ADR-0047's D6 row changed a clause without an inline note, and credited the operator with the seat's design | Inline notes at the clause and the Confirmation. Exit 2 is his; skipping aggregators and failing the projection on a failed restore is the seat's, for the chat to confirm. `CLAUDE.md` says the same |
| F8 | ADR-0034's row said "once ADR-0047 is built" | Annotated: built, and tested |
| F9 | Stale descriptions in the base | 14 rewritten through the connector and read back: `Jobs`, `Status` and `Title` on both tables, the three classification tables, and `Classified` on all six |
| F10 | Two STATE rows stale | Corrected |
| F11 | The private store's scrub of the encoded token had no test | The unreachable-repository test now puts the encoded token in the URL too |
| F12 | The Y1 notes said "renamed by ADR-0046", whose names never reached the base | Corrected in ADR-0030, ADR-0032 and ADR-0043 |
| F13 | The accent rule was described as narrower than the code | `src/normalise.py`, `docs/reference/title-pool.md` and this log corrected: any mark after any ASCII character goes, and a mark on a non-ASCII Latin letter stays |
| F14 | The first audit's mutation file no longer ran | Re-expressed. The same check found five stale entries in `2026-09-23-projection.json` the audit did not name, now re-expressed too |

Fifteen changed or new mutations, all caught `[VERIFIED]`:
`tools/mutations/2026-09-24-second-audit.json` (9), the re-expressed entry in
`2026-09-24-audit-fixes.json`, and the five in `2026-09-23-projection.json`.
549 tests on Python 3.12 and 3.11.

**The first production evening run**, 36036717095 at 17:47Z `[VERIFIED]` from
its committed log. Himalayas was logged `skipped` with ADR-0048's reason, so
the record's evening half holds. The private store's `data` branch was created,
`pushed: true`, with one file, an empty `seen.json`. 29 rows went to `Jobs` in
3 calls with no failure. The next morning run is Himalayas' first contact with
the private store.

**Two things the audit noticed outside its range**, for the architecture chat.
The monthly Airtable count reads only the run's own branch, while the
allowance is per workspace: production counted 5 before tonight, while the
workspace had spent 22 counting the three test runs. And a failed private
restore fails the whole projection, public rows included. That is the seat's
design, so an expired token freezes the display until someone acts; the run
turns red on the third.

## F1 decided, and both workflows proven after the concurrency change

**F1**, the operator, 2026-09-24: "leave the field ids, it is not that much
of an issue." They stay in `101371d`'s history; the log no longer carries them.

**Test-mode dispatches at `056e21a`** `[VERIFIED]` through the public Actions
API and a scratch clone of `data-test`. Both succeeded, so GitHub accepted
`queue: max`.

- **Fetch, 36059310671.** `private_store` reads `restored: 3, pushed: true`,
  no failure: the private store's round trip holds on the test branch.
  Himalayas stopped after one page, 20 fetched and 14 new, because its stop
  rule now anchors on stored data. First contact took 25 pages and all 500
  were new. The run's requests fell from 36 to 13. 48 groups were sent in 5
  calls. No stored file on the public `data-test` branch contains
  "himalayas".
- **Contract check, 36059946826.** Exit 0, and a baseline for all three
  platforms committed to `data-test` under `logs-contract/`, with
  `contract/fingerprint.json` beside it: Greenhouse 258 postings, Lever 16,
  Himalayas 20.
