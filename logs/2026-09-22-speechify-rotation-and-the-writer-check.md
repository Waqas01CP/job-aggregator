---
type: log
description: The two anomalous runs of 2026-09-22 explained as Speechify rotating its city copies, not a board fault; the handoff checked and four of its statements found wrong; the corrected writer how-to checked cold against its records; and the heredoc guard seen running for the first time, with a working-directory defect.
status: current
---

# Speechify's rotation, and the writer how-to checked cold, 2026-09-22 to 2026-09-23 UTC

Previous log: `2026-09-17-corrections-and-airtable-schema.md`, its last two
sections.

| Header | Value |
|---|---|
| Date | 2026-09-22T22:22Z to 2026-09-23, UTC. The local clock read 2026-09-23 throughout |
| Model | claude-opus-5-5 |
| HEAD at start | `24cd5ba`, two ahead of `origin/main` at `73fff5c`. At the operator's second brief, `8f4c251`, level with `origin/main` |
| Mode | **Mutating**, documentation only in this commit. No job board contacted. `data` read from a scratch clone. The Airtable schema read through the connector; nothing written to Airtable |
| Tests | 383 at start, all passing, Python 3.12.10 in the venv |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means
believed. `[INFERRED]` means reasoned from observed data, not tested.

## The handoff checked, and four statements in it wrong

Each was checked before it was relied on.

| Handoff said | Found | Evidence |
|---|---|---|
| HEAD `73fff5c`, one ahead of `origin/main` at `0e0419f` | HEAD `24cd5ba`; the operator had pushed `73fff5c`; `15b00b9` and `24cd5ba` were unpushed, both made after the handoff was written | `[VERIFIED]` `git ls-remote --heads origin` and `git status -sb`, 2026-09-22T22:22Z |
| The pipeline "has succeeded fifteen times" | Fifteen Actions runs: thirteen succeeded, two failed, both on 2026-09-17 before the runner fixes (35179218050 scheduled, 35236457737 dispatched). Twelve production runs had written to `data` and one test run to `data-test` | `[VERIFIED]` public Actions API, `total_count 15` |
| The operator's step 4 includes creating `Classified at` | It exists on `Jobs` and `Jobs test`, `lastModifiedTime` referencing `Status` alone. Only the three `Status` choices are outstanding | `[VERIFIED]` connector `get_table_schema`, 2026-09-22T22:30Z |
| The list of what waits on the operator | Omitted Banyan Canopy's review, due 2026-09-24, which `STATE.md` carries | `STATE.md` Blocked table |

**The operator's second brief, 2026-09-23, was also stale on one point.** It
said `origin/main` was still `73fff5c` with three commits unpushed.
`[VERIFIED]` `git ls-remote --heads origin` at 2026-09-23T12:04Z returned
`8f4c251` for `main`, and `git status -sb` showed nothing ahead: all three
were pushed.

The `Status` field on both tables still carries `applied`,
`rejected_pipeline`, `rejected_choice` and `expired_before_review`
`[VERIFIED]`. `not fit`, `poor filtering` and `accepted` do not exist.

## The two anomalous runs: Speechify rotated its city copies

**Finding: no board broke.** Both anomalies noticed at the last close are one
event on one board, and it is the rotation `STATE.md` already records from
2026-09-16 to 2026-09-17.

Per run, from the thirteen run logs on `data` at `def4f93` `[VERIFIED]`:

| Run (UTC) | Speechify fetched | new | kept | Run `kept` | `written_filtered` | of which local |
|---|---|---|---|---|---|---|
| 2026-09-21T18:32Z | 256 | 1 | 241 | 284 | 12 | 12 |
| 2026-09-22T03:36Z | **192** | 0 | **181** | **222** | 11 | 11 |
| 2026-09-22T17:33Z | 254 | **62** | 241 | 298 | **87** | 26 |
| 2026-09-23T03:36Z | 254 | 0 | 241 | 303 | 31 | 31 |

- **What left.** `seen.json` `last_seen` puts 64 Speechify identities at
  2026-09-21T18:32:55Z and none later: they were absent from both runs of the
  22nd `[VERIFIED]`. Sixty are `Software Engineer, Platform - <city>`, four
  are `Manual Quality Assurance Engineer, SIMBA Team - <city>`.
- **What arrived.** 62 identities first seen at 2026-09-22T17:33Z: 60 of the
  platform role, 2 of the QA role `[VERIFIED]`. **None is a returning
  copy:** 0 of the 62 share a title and location with any of the 64 that
  left. 10 of the 62 share a title and location with an identity already
  stored, so Speechify carries more than one posting for some cities.
  Their `published_at` values are old: 35 at 2024-01-24T23:33:29Z, 25 at
  2025-05-07T15:13:36Z, 2 at 2026-05-21T06:28:28Z. These are existing
  postings made live again under new identities, not new roles.
- **What was stored.** 61 rows entered the public `filtered.json` at
  17:33Z: 60 Speechify platform copies and 1 Coderoad posting `[VERIFIED]`.
  The chain kept the 60 and dropped the 2 QA copies on title.
  **`Software Engineer, Platform` city copies are now 301 of the 345 filtered
  rows.** ADR-0037 foresaw this at line 47, "future rotation at a bound of
  roughly 64 a day"; the grouping is what collapses them for display.
- **No adapter fault.** Every board reports `parse_problems 0` and
  `status ok` in all thirteen runs; every run spent 36 of 500 requests with 0
  retries and 0 failures `[VERIFIED]`. ADR-0018's contract check fingerprints
  the fields an adapter reads, and a board that parsed cleanly on every run
  has not moved those fields `[BELIEVED]`: the field sets were not diffed.
- **The prediction held.** Reported to the operator at 2026-09-22T22:30Z that
  the next run would write 0 public rows. The 2026-09-23T03:36Z run did:
  Speechify 254 fetched, 0 new, and `filtered.json` still 345 `[VERIFIED]`.
- `[INFERRED]` Runs landing near 03:40Z caught the board mid-swap, as the
  2026-09-17T03:43Z run reporting 191 did. Two observations, and the cadence
  of the swap is unknown. Not tested.

**How to read `written_filtered`, since it misled the close.** It counts
public and local rows together; `written_filtered_local` is the local share.
From 2026-09-19T16:18Z the two are equal in six consecutive runs, so **the
public file received nothing in six of the seven runs before 17:33Z**
`[VERIFIED]`. The "usual 11 to 28" the close compared against was Himalayas'
local count, all of it discarded. Likewise `totals.new` carries Himalayas'
500 on every run, because its rows never reach a seen store that survives
the runner.

## The corrected writer how-to, checked cold

The operator asked for `docs/how-to/build-the-writer.md` at `8f4c251` to be
checked against its records by a seat that did not write the corrections.
Every clause was re-located in its record by reading, not by the audit's
line anchors.

**Checked and correct** `[VERIFIED]`:

| Claim | Where it holds |
|---|---|
| ADR-0035 says `Status` is never written; ADR-0046 says `expired_before_review` is set only by the pipeline | ADR-0035:50, ADR-0046:50 |
| Skip-then-group re-projects a stored group under another identity | Reproduced with `src/dedupe.py` over `filtered.json` at `def4f93`: the 170-member group `speechify\|software engineer platform\|2024-01-24`, representative `greenhouse:5058944004`, re-projects as `greenhouse:5974247004` with 169 members once that identity is skipped |
| 345 rows make 39 groups with no chain; the chain admits 334, making 29 groups | Same probe: 39, 334 admitted and 11 dropped, 29 |
| The ten pipeline-owned fields and three operator-owned fields | ADR-0035:50 |
| `Jobs` has twelve fields and the operator owns one | Connector: ten pipeline fields, `Status`, and `Classified at` |
| `Classified at` is computed, nothing sets it by hand | ADR-0046:52, and the connector |
| Six outcome stores, not three | ADR-0047:75 |
| Routing is exclusive; its Confirmation and the check that can fail; metadata only | ADR-0043:57, :79 to :81, :59 |
| `filtered.json` byte-identical after a projection | ADR-0040:118 to :119 |
| Fifteen days is configuration | ADR-0046:34 |
| Only empty-`Status` rows are removed by rule | ADR-0040:80 to :85, narrowed by its 2026-09-19 Changes row |
| Who removes fallen-out rows is unsettled | ADR-0040:77 gives it to ADR-0014's sweep; ADR-0046's sweep has no such step; ADR-0046:75 has the projection read `Jobs` "to find rows that fell out" |
| The old "roughly 25" came from 270 rows | ADR-0037:17 |
| A test run must not be able to touch production | ADR-0033:25 |
| The classification tables have no test copies | Connector: five tables, one test table |
| No record classifies the family label or the star as pipeline- or operator-owned | ADR-0038:60 needs "a family field"; ADR-0044:60 calls the star "a display annotation"; neither says who owns it |
| The anchor ADR-0035:58 | Correct: line 58 carries the classification rule |
| All 79 terms map to a family; the star has 14 tests | `load_term_families()` returns 79; 14 `def test` in `tests/test_star.py` |
| Twelve source records | The file cites sixteen; twelve impose a constraint (0004, 0031, 0033, 0034, 0035, 0037, 0038, 0040, 0043, 0044, 0046, 0047), the rest are the dedupe key, the definition of done and superseded history |

**Gaps found**, none of which blocks step 1:

1. **The no-read question is framed on half the evidence.** The file says
   ADR-0004 performs no reads and later records assume one. ADR-0004 itself
   records that clause as reversed by ADR-0014, at :30 and :64, while its own
   2026-09-17 Changes row and ADR-0035:48 treat it as standing, and ADR-0046:75
   budgets a projection read of `Jobs`. The records disagree about whether
   the clause is in force. For the architecture chat, as evidence on the
   question it already holds.
2. **The `Status` conflict is also inside ADR-0046.** Line 50 has the
   pipeline setting `expired_before_review`; line 134 says `Status` is the
   operator's. Same question, a second place it lives.
3. **The budget range is 48% to 54%, not "nearer 48%".** Three to four
   upsert calls a run is 180 to 240 a month against the record's 60, which
   puts the total at 480 to 540 of 1,000.
4. **Step 1 omits two requirements of ADR-0034.** Its grep Confirmation at
   :74, that the client imports no fetch function and the fetch module
   mentions no token or write verb; and :68, that the run log reports both
   budgets. The five-requests-a-second limit, ADR-0034:26 and ADR-0004:17,
   is also absent. Step 1 builds all three.
5. **ADR-0009's Confirmation is paraphrased short.** ADR-0009:57 also
   requires the run to write rows to all three layers.
6. **ADR-0035's fallback is omitted**: :60, creates plus the same field
   discipline if upsert is unavailable on the plan. Its Assumption at :31 is
   sourced, not exercised. Matters for step 2.

Minor: the exit-code sentence under "Fail visibly" is `CLAUDE.md`'s
convention, not ADR-0047's.

## The heredoc guard runs, and a defect in how it is wired

**First observation that the harness invokes it** `[VERIFIED]`. A `cd` in an
earlier command left the shell in `docs/decisions`. The next Bash call was
refused before it ran:

```
PreToolUse:Bash hook error: [python tools/heredoc_guard.py]: python: can't
open file '...\job-aggregator\docs\decisions\tools\heredoc_guard.py':
[Errno 2] No such file or directory
```

**The defect.** `.claude/settings.json` runs `python` with the argument
`tools/heredoc_guard.py`, a path relative to the working directory. Python
exits 2 when it cannot open a script, and exit 2 from a PreToolUse hook means
block. So a guard designed to fail open fails closed on every Bash call as
soon as the shell leaves the repository root. Moving back with PowerShell,
which the hook does not match, cleared it `[VERIFIED]`.

**Not fixed.** The fix is to anchor the path on `CLAUDE_PROJECT_DIR`, which
the harness sets for hooks. It changes how every session's Bash calls are
gated, it is outside the operator's brief, and it is his to approve.
**Recommendation**, labelled as one.

Also still unobserved: the guard firing on the failure it was built for, a
heredoc carrying a backslash into a file. Nothing in this session wrote one.

## Noticed and not investigated

- Scheduled runs start 3.5 to 5.5 hours after their cron times, 00:00Z and
  13:00Z. Runs landed at 03:26Z to 03:43Z and 16:18Z to 18:32Z. GitHub
  documents scheduling as best-effort and the workflow's comment says so.
- The Airtable descriptions of `Jobs` and the two rejection tables still
  describe ADR-0045's move-a-row flow. They live in the base, not the
  repository.
- Banyan Canopy has kept 0 rows in all thirteen runs from 5 or 6 postings,
  every drop on title. Evidence for the operator's review on 2026-09-24, not
  a recommendation.

## Not done

- The heredoc guard's path is not fixed. See above.
- `build-the-writer.md` is not edited in this commit. Gaps 3 to 6 are
  factual and are corrected in the commit that lands step 1. Gaps 1 and 2
  are record conflicts for the architecture chat, routed through the
  operator.
- The field sets of the Speechify payloads were not diffed across the swap.
