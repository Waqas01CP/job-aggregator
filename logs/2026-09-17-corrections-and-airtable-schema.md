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

## Not done, as of 22:20Z

- Nothing pushed. The operator pushed `1bcea92` himself mid-session.
- The scheduled run had not fired by 22:20Z. Expected between about 03:00 and
  04:30Z from the two previous runs' lateness.
- No Himalayas fetch, no decision record written or edited, no "To review"
  view, which the MCP cannot create.

---

# The architecture chat's brief, worked through

The operator relayed a twelve-part brief from the architecture chat, stating
that none of it required his input. Everything below is that work.

## Ten records written

| Record | Decides |
|---|---|
| ADR-0030 | A rule change backfills the filtered layer. Answers questions I and J together |
| ADR-0031 | Personal preferences are configuration, not code |
| ADR-0032 | The seniority rule, and the clause of ADR-0021 it reverses |
| ADR-0033 | The data branch is the store, local files are working copies. Answers question 5 |
| ADR-0034 | Airtable gets its own client, as a scoped exception. Answers question A |
| ADR-0035 | The projection upserts on Identity. Answers question B |
| ADR-0036 | The contract check reports through the run log. Answers question D with a no |
| ADR-0037 | The filtered layer stores rows, the projection groups them. Answers question G |
| ADR-0038 | Role families are views, not a ranking. Answers question F |
| ADR-0039 | The aggregator condition is the three components. Resolves ADR-0019 |

## Fifteen Changes rows, and four in-place annotations

**A structural decision, made and worth stating.** The brief said "amend" for
nine records. CLAUDE.md says: "Never edit an accepted record to change a
decision. Write a new record that supersedes it, and link both directions. A
factual error may be corrected in place with a dated annotation." Those two
cannot both be followed literally.

They were split by kind. Where the change is a **decision**, a new record
carries it and the old one gains a Changes row pointing forward: ADR-0004 to
ADR-0034 and ADR-0035, ADR-0010 to ADR-0038, ADR-0013 to ADR-0030, ADR-0018 to
ADR-0036, ADR-0019 to ADR-0039, ADR-0021 to ADR-0032. Where the change is a
**factual error in the record**, it is annotated in place with the date, as
the rule allows: ADR-0001's unrunnable Confirmation, ADR-0011's enumeration,
ADR-0019's contradictory Confirmation sentence, ADR-0021's no-blocklist
clause. ADR-0015 took two Changes rows, go-live and the backfill exclusion, as
the brief specified.

Fifteen rows across eleven records, applied by a script so the table structure
stayed uniform rather than being retyped eleven times.

## Corrections to the brief itself

**ADR-0021's Confirmation is not invalidated.** `[VERIFIED]` by running its
eight-case set through the current chain. Every case produces the verdict the
record requires. "Software Engineer II" is still not admitted: the pool now
matches it and the seniority rule drops it, so the **verdict** holds and only
the **mechanism** changed. The case set is therefore re-run and kept, not
replaced, and ADR-0032 records the table. The run also confirms
"Non-AI Systems Analyst" is admitted by `ai system`, which ADR-0021 itself
named as the one to watch, so it is a live false positive rather than a
theoretical one.

**ADR-0023 was already done.** The brief asked for the "neither is a gate yet"
correction. It is at line 76 with a dated annotation and a Changes row, both
added on 2026-09-17 by an earlier session. Nothing to do.

## The annotation-vendor list became configuration, not just a file

The brief asked for `docs/reference/annotation-vendors.md`. Writing only the
file would have left `ANNOTATION_VENDORS = ("welo data", "welocalize",
"innodata")` in `src/filters.py`, contradicting ADR-0031 the moment it was
written. So the list moved: a `load_annotation_vendors()` loader reading the
file's Vendors section only, and the constant now loads at import.

The three names are unchanged, so no filtering behaviour changed.

`[VERIFIED]` 311 tests pass, 3 new. **Four mutations, all caught**: the loader
reading the whole file instead of its section, a missing file returning empty
instead of raising, an empty list accepted, and a vendor removed from the
file. The section-scoping mutation matters because the file quotes
`src/filters.py` and a tool path in backticks outside that section, and a
whole-file loader would have turned them into vendor names.

**The test count is now genuinely 311**, which is what the previous session's
log claimed before this session corrected it to 308. Coincidence, and recorded
so nobody later reads the correction as wrong.

## Gate 6 in the pre-commit hook, proven to fire

ADR-0020 promised "a guard rejecting an aggregator-sourced file from a commit"
and none existed. The guard that matters lives in the run's commit step,
because the data branch's commits use `git commit-tree`, which runs no hooks.
Gate 6 covers the other failure mode, which a hook can see: a `data/` path
staged onto a code branch by hand.

`[VERIFIED]` by the case built to defeat it. `.gitignore` excludes `data/`, so
the gate is only reachable through `git add -f`, which is exactly what was
done:

    git add -f data/gate6-proof.json
    git commit -m "this must never be created"
    COMMIT BLOCKED: a pipeline working file is staged: data/gate6-proof.json

HEAD was unchanged afterwards and the file was removed. A gate nobody has seen
fire is indistinguishable from an absent one.

## Also

`CLAUDE.md`'s pointer to `MAP.md` now states that it is the navigation index
for every documented file and is read before searching the tree. Its shared
HTTP module rule now names ADR-0034's exception, because a rule with an
undocumented exception is worse than either.

`docs/architecture-2.0.md` line 302 gave exit 1 one cause; it now gives two
and says the run names which. Its filter-chain listing named a location filter
that has never existed; it now lists the chain the code runs, with the
location gap and its real difficulty recorded.

## Still not done

- **Nothing is pushed.** The brief's last line says "commit, push". The
  standing protocol in this project is that the operator pushes. Stopped at
  the commit and asked.
- Himalayas storage, the location tag and the aggregator question are held for
  the chat's second brief.

---

# The run landed, and the prediction held

`[VERIFIED]` run 35303384355, `schedule`, created 2026-09-18T03:29:18Z at
`bceb3d9`, every step succeeded. Three hours and twenty-nine minutes after its
00:00 slot, the least late of the three scheduled runs. `data` moved from
`91f7518` to `90553c3`.

**It is the first run on pool version 4 with the seniority rule, and it wrote
nothing to the public filtered file.**

| | Run 2 | Run 3 |
|---|---|---|
| `fetch-all/greenhouse.json` | 766 | 770 |
| `fetch-all/lever.json` | 38 | 39 |
| `seen.json` | 804 | 809 |
| **`filtered.json`** | **24** | **24** |

The run log says why, and it is exactly the mechanism this session recorded:

- fetched 1297, new 505, **chain kept 294**, dropped 938 by title and **65 by
  seniority**;
- `written_filtered` 24, of which `written_filtered_local` 24, so **0 rows
  reached the public file** and all 24 were Himalayas rows written locally;
- Speechify: fetched 255, **kept 241, new 0**.

So the chain admits 294 rows and the public file holds 24 of an older
vintage. The handoff expected roughly 241 new rows on this run. The measured
answer is zero, the reason is that every kept row's identity was already in
the seen store, and ADR-0030's backfill is the thing that closes the gap.
This is the prediction being tested by the run rather than argued about.

**The seniority rule's first production run** dropped 65 rows, across Careem,
CodeRoad, Globalli, Motive, Veeam, Spreetail and Himalayas.

**Himalayas kept 24 roles and lost all of them.** Third run, third first
contact, 25 of 36 requests again. The run-log report flags it as "every run".
That is now three observations of ADR-0020's premise failing on a runner, and
it is the clearest evidence the operator has for that decision.

**Publication lag, three runs:** 11 of 11 Greenhouse and **2 of 2 Lever**
postings first seen after run 1 are dated after the run that missed them, none
at or before. Lever's `createdAt` now has a second observation. Still
consistent, still not proof.

**Requests:** 36 in every run, 9 Greenhouse, 2 Lever, 25 Himalayas. No run
near the 500 ceiling, 0 retries, 0 failures across all three.
