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
| D3 | Closed postings | **Clarification asked and pending.** He does not want to see a closed role and mentioned the fifteen-day rule; the seat asked whether a closed row goes at the next sweep, stored with the reason, or after fifteen days |
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
