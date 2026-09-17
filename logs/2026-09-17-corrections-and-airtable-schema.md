---
type: log
description: Four stale STATE.md lines and a test count corrected; the discovery that a pool widening is not retroactive, so 257 kept rows can never reach the filtered file; the UTC dating rule; and the Airtable schema built and verified through the MCP.
status: current
---

# Corrections, a non-retroactive pool, and the Airtable schema, 2026-09-17 UTC

Previous log: `2026-09-18-pool-version-4.md`.

**On the filename.** This log is dated by its UTC start, 2026-09-17T21:08Z.
The previous log is named for a local date while UTC was still the 17th, so
for this one pair the filenames sort in the opposite order to the sessions.
That mistake is what this session's UTC rule now prevents, and renaming a
committed log would break the index's rule against changing rows.

| Header | Value |
|---|---|
| Date | 2026-09-17T21:08Z to 2026-09-17T22:20Z and continuing |
| Model | claude-opus-5 |
| HEAD at start | `2bfb393`, equal to `origin/main` |
| Mode | **Mutating.** No job board contacted. The public Actions API and a scratch clone of `data` were read. The operator's Airtable base was written |
| Tests | 308 at start, 308 at end, passing with `TEST_MODE` unset and with `TEST_MODE=1` |

**Tags.** `[VERIFIED]` exercised and observed this session. Unmarked means believed.

## The handoff was checked, and two things in it were wrong

`[VERIFIED]` by `git ls-remote --heads origin`: `main` was already at
`2bfb393`, so nothing was waiting to be pushed. Four lines in `STATE.md` said
otherwise and are corrected in place with annotations: the Headline, the
Blocked section's list, the seniority row, and the data-branch row. The
seniority row was stale twice over, because the pool GitHub ran before the
push was version 2 and the row said version 1.

`[VERIFIED]` the suite reports 308 tests, not the 311 in the previous log's
header. `tests/` holds 308 `def test_` methods, `085c434` added 5 to a base of
303 at `57f9382`, and no test file has changed since. The previous session
reports having produced 311 by arithmetic after running the suite with
`tail -1`, which prints only "OK". Corrected in that log. Its row in
`logs/README.md` still says 311 and was deliberately left alone, because that
file forbids editing a row; this log's own row carries the correction.

## Nothing had run, and the reason is the reason the handoff existed

`[VERIFIED]` the public Actions API listed five runs with the newest still
35253312417 at 2026-09-17T17:31Z, and `data` was still at `91f7518`. The
handoff expected a run to check. It could not have fired: the handoff and this
machine both read 2026-09-18, while UTC was 2026-09-17T21:08Z.

`CLAUDE.md` now carries the rule. Dates are UTC, schedules are read in UTC,
and where a local date differs the text says which is which.

## A pool widening is not retroactive, and that is the larger finding

The handoff said to expect roughly 241 Speechify city copies to enter
`filtered.json` on the first run after the push. `[VERIFIED]` they never can.

`src/run.py:178` runs `split_new(kept_rows, seen.identities)` before writing,
so a posting enters the filtered layer only on the run that first sees it. All
241 were first seen at 2026-09-17T14:52:57Z.

Measured against `data` at `91f7518`, using the chain and the seen store the
runner itself loads:

| | Count |
|---|---|
| Stored postings | 804 |
| Kept by pool version 4 with the seniority rule | 270 |
| of which Speechify's `Software Engineer, Platform` | 241 |
| Dropped by title, and by seniority | 501, and 33 |
| **Kept but absent from `filtered.json`, and unwritable** | **257** |
| Rows in `filtered.json` today's chain would drop | 11 |

The 270 matches the previous session's own measurement, which is a useful
cross-check on the chain; what is new is the 257.

**The check was proved against the case built to defeat it.** With
`greenhouse:5058944004` in the real seen store the row is unwritable; with
that one identity removed from the set, the same row is writable. A check
that could not fail would not have distinguished them.

**Also measured, and it bounds the expectation.** `[VERIFIED]` the two runs'
first-seen cohorts are 796 and 8. **No Speechify identity appeared in the
second**, over a 2h40m gap. So the next run's filtered growth comes from
rotation alone. An upper bound of roughly 64 a day is available from the
09-16 to 09-17 snapshot difference, but the identities behind that comparison
were discarded, so it is a bound and not a measurement.

Raised for the architecture chat in `STATE.md` rather than recorded, and the
expectation is corrected in the log that set it. Rows kept under older rules
staying is the half already raised as question I; rows a wider pool newly
admits never arriving is the half nobody had stated, and every future pool
change inherits it.

## Baseline before the next run

`[VERIFIED]` from a scratch clone of `data`, which was never fetched into this
repository's refs. `tools/run_log_report.py`: 2 runs, 36 requests each,
Greenhouse 9, Lever 2, Himalayas 25, no run near the 500 ceiling, 0 retries,
0 failures, Himalayas flagged "every run". `tools/publication_lag_report.py`:
of postings first seen in run 2, Greenhouse 7 of 7 and Lever 1 of 1 are dated
after run 1, none at or before. Both reproduce the previous session's numbers,
which is what makes the next run's delta measurable.

## Airtable

`[VERIFIED]` the previous log's claim that the plugin's tools "reach only a
new session" is incomplete. The server is installed and was unauthorized;
`~/.claude/mcp-needs-auth-cache.json` listed it as needing authentication,
which is why a tool search found nothing. The operator authorized it through
`/mcp`, and `list_bases` then returned the base. `ping` alone would not have
shown this: it answers `pong` from the server process regardless.

**Built and verified:** two tables, `Jobs` and `Jobs test`, 13 identical
fields each, primary field `Title`. The three single-select lists were checked
against ADR-0014 lines 49 to 52 before creation and match. Every date field is
stored with time, ISO format, 24 hour, `utc`. Verified by reading the schema
back with `get_table_schema`, not from the create call's own reply.

The base's default table was deleted after both new tables were verified, on
the operator's explicit choice between three options. Its three records were
listed first and were Airtable's empty defaults, created with the base.

**Two MCP limits, both found by trying**, and both recorded in
`docs/reference/airtable-schema.md`: there is no tool to delete a field, and
none to create a view. A third detail: the MCP's own schema documents the
`dateTime` time zone as an IANA identifier with `"UTC"` as its example, and
Airtable's API rejects `"UTC"` with a 422 while accepting `"utc"`.

**No identifier was written to the repository.** The base ID is a repository
secret and this repository is public.

About 11 MCP calls were used, one of which was the rejected 422.

## Where a close alternative was wrong

- **Building on the existing default table.** It would have left four
  undeletable default fields in the operator's display forever, and its
  default `Status` field collides with ADR-0014's `Status`, since field names
  are unique case-insensitively. `create_table` sets every field at once.
- **Writing the superseding record for the seniority rule.** The architecture
  chat's, not an implementing session's. Raised, not written.
- **Tidying `architecture-2.0.md:195` and ADR-0009's "eleven boards".** Both
  look like stale text and are open questions with the chat.
- **Trusting `ping`.** It proves the server runs, not that it is authorized.

## Not done

- Nothing pushed. The operator pushed `1bcea92` himself mid-session.
- The scheduled run had not fired by 22:20Z. Expected between about 03:00 and
  04:30Z from the two previous runs' lateness.
- No Himalayas fetch, no decision record written or edited, no "To review"
  view, which the MCP cannot create.
