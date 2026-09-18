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

---

# Navigation, storage, and an architecture audit

The chat's second brief: five parts and two corrections to earlier framing.

## Part 5, the ADR-0031 audit, run for the first time

**The letter of the Confirmation finds nothing.** `[VERIFIED]` 112 preference
values checked against all 19 shipped modules: 19 hits, every one in a comment
or a docstring. No pool term, seniority word, vendor name or family name is
used as a value anywhere in `src/` or `tools/`.

**The audit was extended to employer names**, which ADR-0031's own wording does
not cover and which matter more: an employer named in a module is a board the
pipeline cannot stop polling without a code change. `[VERIFIED]` **no employer
name appears in any module.** The case that could easily have gone wrong is
ADR-0027's per-source title normalisation, and it did not: `config/boards.json`
names a normaliser, `strip_location_suffix`, and the function itself is generic,
removing a trailing suffix that equals the posting's own location field. The
word "speechify" appears once in `src/`, in a comment explaining a measurement.

**Two violations were found on a stricter reading and fixed.** The method
`TitleMatcher.senior_word` is named after the list's current contents rather
than its function. Renamed to `excluded_word`; the tree is now clean.

**The Confirmation is now a tool**, `tools/preference_audit.py`, with 14 tests.
Every test that matters plants a violation the shipped tree does not have: a
pool term in a list literal, an employer in a condition, seniority words in a
tuple. Two cases prove the distinction the audit rests on. The same term in a
docstring is allowed and in a data string is not, which is why docstrings are
found with `ast` rather than by looking for triple quotes; and `llm` must not
match "llmodule", which is ADR-0021's boundary rule applied to source code.

**One defect in my own work**, found by my own test: `load_families` leaked
`FileNotFoundError` instead of raising `AuditError`, so a missing pool file
would have crashed the audit rather than reporting it. Fixed.

## Part 3, the field inventory

`docs/reference/platform-fields.md`, measured from the 84 saved responses
rather than from adapter docstrings. A field counts as read only if the adapter
names it, so a field the documentation mentions and the code ignores counts as
unread.

**The brief's premise needed correcting.** It said nothing records that
`locationRestrictions` exists "or that the pipeline ignores it". The pipeline
does not ignore it: `src/adapters/himalayas.py` reads it and joins the first
three entries into the `location` string.

**And my own first reaction to that was wrong too.** I assumed the cut at three
was lossy. `[VERIFIED]` across 91 unique postings the lists have median length
1 and 90th percentile 2, and **only 2 of 74 exceed three entries**. The
truncation costs almost nothing. The measurement was worth making precisely
because both the brief and I had guessed.

**The field that is actually ignored is a better one.** Himalayas returns
`seniority` on 100% of postings, as `["Mid-level", "Senior"]`, and nothing reads
it. ADR-0032 infers seniority from title words on the one source that states it.
`timezoneRestrictions` is also 100% and also unread.

Other unread fields worth naming: Lever's `workplaceType` and `country`, both
100%; Greenhouse's `metadata` at 37.4%, which is the weak experience lead; and,
for platforms not yet adapted, **SmartRecruiters' `experienceLevel` at 100% and
Zoho Recruit's `Work_Experience` reading "1-3 years"**. Those two are the only
measured sources of the field the stated-experience rule has never had.

## Part 2, ADR-0040, and Part 4, ADR-0041

**ADR-0040: the current rules filter the projection, never the store.**
ADR-0030 handled widening; this handles contraction. `[VERIFIED]` 11 of the 24
rows in `filtered.json` are rejected by the current chain, so projecting the
file as-is would show the operator eleven roles he has decided against.
ADR-0030's clause "the projection then copies the file as it stands" is amended
inline and in its Changes.

**One consequence the brief did not name, and it destroys data if wrong.** An
upsert-based sweep that removes rows which have fallen out would delete rows the
operator has already marked `applied`, which is the record of an application.
The record therefore removes only rows whose `Status` is empty, and its
Confirmation is the case built to defeat it: mark one of the eleven `applied`,
run the sweep, and it must still be there.

**ADR-0041: location admits unless a source excludes.** Records the deferral,
which had none, and the rule replacing it. `[VERIFIED]` on the saved Himalayas
corpus the structured half would drop 74 and admit 17, and none of the 74 lists
names Pakistan. On every ATS board in the slice it drops nothing, because none
exposes an eligibility field. The text half, "US only", waits on description
filtering and is recorded in full so it is implemented to this rule rather than
designed again.

Its Confirmation is the existing case set, which is the case built to defeat it:
"Karachi, Punjab, Pakistan" with its wrong province must stay admitted. A rule
that drops it has become the matcher this record rejects.

## Part 1, navigation: investigated, proposed, not built

`[VERIFIED]` how routing actually works today, by reading the generator and the
generated file rather than assuming.

- **Decision rows in `MAP.md` carry only the record's H1 title.**
  `tools/generate_map.py` takes a description from frontmatter for other types
  and falls back to the first heading for decision records, which have no
  `description` field. Forty-one records are therefore a flat list of forty-one
  titles, ordered by number.
- **The titles are good.** Most state the decision as a sentence. The failure is
  not identifying a record once seen; it is knowing which of forty-one to look
  at when the question arrives by topic rather than by decision.
- **Grep does not route here.** Records cross-reference each other heavily, so
  a topic word returns roughly half the corpus: "Airtable" appears in 19 of 41
  files, "title" in 18, "log" in 27.
- **The reading order's real growth risk is not `MAP.md`.** Measured:
  `CLAUDE.md` 11.5KB, `MAP.md` 13.1KB, `logs/README.md` 10.4KB, and **`STATE.md`
  36.6KB**, which is both the largest and the only hand-written one.

Proposal, and the route: this is configuration and a generator change, so it
needs the operator's approval and not the chat's. Put to him, not yet built.

## Also

**Himalayas stays.** ADR-0019 gains a Changes row and ADR-0039 an annotation.
Both halves of the old argument are withdrawn in writing: the request spend was
never a constraint, since ADR-0028's ceiling is 500 and the maximum observed is
36, and the worthlessness judgement rested on a different corpus. Its own
restriction field is measured instead.

**The 36 requests are what a run spends, not a limit.** Every place that framed
it as a cost against Himalayas is corrected.

## Part 1 built, after the operator chose

He chose both options, grouping and descriptions, and separately settled the
push question: push when the brief asks for it. This brief asks.

**All 41 records carry `topic` and `description`.** The topic vocabulary is
six words, fixed in the generator, in the order the pipeline runs: fetching,
filtering, storage, display, measurement, practice. The description says what
question the record answers, because that is how a reader arrives, rather than
restating the decision, which the title already does.

**`MAP.md`'s decision table is grouped under six headings** instead of being a
flat list of 41 titles.

**The vocabulary cannot drift, because adding a topic outside the six fails.**
`[VERIFIED]` by the case built to defeat it: one record's `topic` line was
deleted and the map check exited 1 naming the file and listing the six valid
topics, which the pre-commit hook treats as a failure other than staleness and
blocks. Restored, and the check exits 0 again.

Three descriptions were rewritten after reading the generated output, because
they restated their own titles and added nothing: ADR-0010, ADR-0011 and
ADR-0012.

**What was deliberately not done.** `CLAUDE.md` did not grow. The brief warned
that a longer instruction file is the obvious answer and probably the wrong
one, and nothing here needed it: the pointer to `MAP.md` was already
strengthened earlier in this session, and the map now does the routing.

**The adjacent finding, not acted on.** The reading order's size risk is not
`MAP.md` at 13.1KB. It is `STATE.md` at 36.6KB, the largest file a session
reads to start and the only hand-written one. Raised, not solved.

## Still not done

- Part 1 of the brief is now built; nothing else from it is outstanding.
- ADR-0040's projection filter, ADR-0041's structured half, and every unread
  field in Part 3 are decisions and measurements, not code.

---

# Outcome stores, the backfill, and the PAT

The chat's third brief. Five parts, three of them code.

## Part 1: ADR-0030's backfill, built

`tools/backfill.py`. It reads the raw layer, applies the current chain, and
appends what the filtered layer lacks, through `storage.append_delta` and
split by `is_publishable`. That is the run's own writer and the run's own
ADR-0020 split, not a second path with its own rules. The only thing it does
differently is skip the seen-store check, which is the entire point.

`[VERIFIED]` against a copy of the data branch at `90553c3`:

    backfill: 257 row(s) ... are absent from the filtered layer
    backfill: appended 257 publishable and 0 aggregator row(s).
    backfill: the gap is closed.

`filtered.json` went from 24 rows to 281. A second pass appended nothing and
left the file byte-identical. The 257 matches the number measured
independently two rounds ago, before the tool existed.

**The Confirmation was proved able to fail**, which the brief asked for
specifically. Withholding one identity, the backfill appended 256 and
reported itself complete, because it could not see the withheld row. The
check, run without the same blindfold, reported exactly one row absent and
exited 2. Both halves matter: the pass believing itself done is what makes an
independent check necessary.

14 tests, 6 mutations, all caught. The mutations include removing ADR-0020's
split so everything is written to the public file, ignoring the local
filtered file when computing the gap, never reading the aggregator raw
directory, and silently skipping a record the code cannot read, which would
look exactly like a closed gap.

**One deviation from ADR-0030's Confirmation**, recorded in its Changes: the
count is printed and logged here rather than written to a run log. A backfill
is not a run, and a foreign file in `logs-runs/` would be read by
`tools/run_log_report.py` as one.

## Part 2: ADR-0043, three outcome stores

Recorded, not built, because the sweep that writes them is blocked behind the
token (Part 4).

**It reverses a clause of ADR-0014**, which says outcomes go in "one file with
a status discriminator, not one file per status, so a row has exactly one
outcome". The three corpora have different readers: `rejected_not_a_fit` is
read by a person deciding what to stop admitting, `rejected_poor_filtering` is
the filter's defect log, and `accepted` is read by code on every projection.
"Every role he turned down" should be a file, not a query.

**The invariant that clause protected is kept.** Routing is exclusive and the
property is now checkable: no identity may appear in two stores, and the
Confirmation says to hand-write one into two and confirm the check reports it,
because three files that never overlap by construction would pass whatever the
routing did.

`expired_before_review` gets no store. It measures the cost of the operator's
absences, which ADR-0014 already says, and nothing would read it as a corpus.

**Two boundaries recorded.** ADR-0020 applies to all three stores, so each
splits public from local exactly as the filtered layer does; a new store is a
new way to publish an aggregator's rows. And no rule changes itself from these
corpora: a tool may report that eleven rejected rows were all admitted by
`ai ops`, and only the operator removes the term.

## Part 3: the priority star, and where the line went

`src/star.py`. A posting is starred when it shares **employer**, **matched
term** or **role family** with a row in the accepted store. Every star names
the attribute, the value and the accepted row, so it can be read aloud as
"starred because employer matches accepted row N", which is ADR-0010's own
test.

**The test that matters is the negative one.** A posting a similarity model
would obviously star, sharing none of the three attributes, must not be
starred: "Machine Learning Engineer at Motive" accepted, "Backend Engineer at
Veeam" offered. If that ever starts starring, something is comparing text.

14 tests, 7 mutations, all caught. The line is recorded in ADR-0044 in the
terms it has to be enforced in: no score, no distance, no embedding, and **no
ranking of stars**, because a count used as an order is a score wearing a
different hat.

**Role family needed something that did not exist.** `load_title_pool` reads
the pool's four `### N.` headings and discards them, so no family label could
reach a row. `load_term_families` now maps all 79 terms to their heading, 7
agentic, 43 LLM and applied, 12 traditional, 17 software. That also delivers
the label ADR-0038 has been waiting on.

**A regression I caused and caught.** Adding the family load to
`TitleMatcher.__init__` broke `tools/title_pool_report.py --pool CANDIDATE`,
because a candidate pool file has terms and no family headings. The fix
distinguishes two cases rather than becoming tolerant: a pool with no headings
at all has no families, which is what a candidate file legitimately is; a pool
with headings and a term above them raises, because that is a term nobody can
name a family for.

**Also my own, and the rule I keep breaking.** A `"\\n"` inside a bash heredoc
became a real newline and broke `src/filters.py`. That is the fifth time this
trap has been recorded in these logs. The repair went through the Edit tool,
which is what the rule says to do in the first place.

## Part 4: the PAT, named as a blocker

`STATE.md` now carries it as a blocker rather than as an item in a list of
things not yet built, which is what the brief asked for and what the previous
addendum got wrong.

The Airtable writer row reads BLOCKED, the sweep row reads BLOCKED behind it,
and the Blocked section names the token's three scopes and the four secret
names. It also says why the MCP authorisation does not substitute: that is a
session's OAuth, and the pipeline never touches it.

Everything else the writer needs now exists: the schema, ADR-0034's client
decision, ADR-0035's upsert key, ADR-0040's projection filter, and ADR-0043's
outcome stores behind it.

## Part 5: STATE.md, investigated

`[VERIFIED]` by measuring the file section by section rather than guessing at
a seam.

| Section | Bytes |
|---|---|
| Preamble, how-to, headline | 4,208 |
| Documentation, Tooling, Pipeline tables | 20,572 |
| Blocked, and on whom | 6,682 |
| Known unverified | 7,485 |

**The seam is status, not pipeline stage.** Of 69 table rows, **57 are DONE,
and those 57 are 17.5KB, 45% of the file.** *(That count was taken before this
round added three DONE rows of its own. At the split it was 60 of 69 and
18.7KB.)* A DONE row is finished history:
the file's own rule is that it is never deleted, so the file grows
monotonically with completed work. A session reads all of it at start and acts
on almost none of it.

What a session actually needs at start is the headline, what is blocked and on
whom, what is unverified, and the nine rows that are not DONE. Splitting by
pipeline stage would cut across all four of those; splitting generated from
hand-written yields nothing, because none of it is generable, which is
precisely why ADR-0023 calls this the artifact most able to lie.

Proposed and not built: it is the operator's call. It does not change the
reading order, since the four files stay and the history is read on demand
like `MAP.md`, and it does not change the authority order, since both halves
are the same type. It would need a Changes row on ADR-0023, whose artifact set
would gain a file.

The file is 42KB as this log is written, having grown 3KB in this round alone.

## Part 5 built, after the operator chose

He chose the status seam. `STATE.md` now holds what is unsettled and
`docs/reference/completed.md` holds what is finished.

`[VERIFIED]` nothing was lost in the move. Every table row from the file
before the split appears in exactly one of the two after it, compared as
sorted lists of whole lines: 69 rows before, 9 plus 60 after, and the sets are
equal. Rows moved verbatim, because a rule that says a DONE row is never
deleted is only honoured if the bytes survive.

    STATE.md      42,036 bytes  ->  23,560
    completed.md        0       ->  20,544

`STATE.md`'s maintenance rule now says where a row goes when it becomes DONE,
and ADR-0023 carries a Changes row: its artifact set gains a file, its reading
order does not change, since the four files a session starts with are the same
and the completed rows are read on demand like `MAP.md`. The record's own
point stands, that this is the artifact most able to lie. The split makes the
part that can lie smaller.

## Not done

- ADR-0043's three stores and ADR-0044's star have no writer, because the
  sweep and the projection are blocked behind the token.
- ADR-0038's views remain unbuilt; only the label they need now exists.
