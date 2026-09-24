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
| D5 | Aggregator rows accumulating | Build ADR-0047's write path |
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
accent survives, and a string with no Latin accent folds exactly as before,
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
pipeline-owned on 2026-09-23. The field was created on `Jobs`
(`fld2ugC2DsHdjre5W`) and `Jobs test` (`fldlD4Bc1ZipKanZp`) through the
connector as single-line text `[VERIFIED]` from the connector's answer. The
projection sends it as the eleventh pipeline-owned field: the family of the
term shown in `Matched term`, a lookup on the term and never a reading of the
title. Both test files pin the eleven by hand. One test sends two rows from
different families; another uses a row whose raw and normalised titles name
terms in different families, so a `Family` taken from the raw title fails it.
Six mutations, all caught `[VERIFIED]`: `tools/mutations/2026-09-24-family.json`.
Rows already in `Jobs` gain their `Family` on the next projection, since every
run re-sends the whole layer.

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
