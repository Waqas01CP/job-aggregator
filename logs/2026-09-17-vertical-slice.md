---
type: log
description: The vertical slice built end to end. Config, HTTP module, Greenhouse and Lever adapters, normaliser, deduplicator, filter chain, writers, orchestrator and schedule, plus Himalayas on condition.
status: current
---

# The vertical slice, 2026-09-17

Previous log: `2026-09-16-second-observation-checks.md`.

| Header | Value |
|---|---|
| Date | 2026-09-16 into 2026-09-17 |
| Model | claude-opus-5 |
| HEAD at start | `3552b35` |
| Mode | **Mutating.** First pipeline code. Four live runs against real boards, all in TEST_MODE, read-only against every endpoint |
| Tests | 183, all passing |
| Verification | 79 mutations applied across nine steps, one per guarantee. 8 survived and all 8 were resolved |

**Tags.** `[VERIFIED]` means exercised and observed this pass. `[BELIEVED]` means reasoned, not run. Unmarked means believed. **RECOMMENDATION** marks a recommendation, not a decision.

## What now exists

The slice runs end to end. Eleven employer boards, both layers written, a schedule, and Himalayas behind its condition.

`[VERIFIED]` by four runs against live boards:

| Run | Boards | Fetched | New | Kept | Requests |
|---|---|---|---|---|---|
| 1 | 11 ATS | 917 | 917 | 19 | 11 |
| 2 | 11 ATS | 917 | **0** | 19 | 11 |
| 3 | 11 ATS + Himalayas | 1417 | 500 | 39 | 36 |
| 4 | 11 ATS + Himalayas | 937 | **0** | 19 | 12 |

Run 2 is the brief's check met against real boards rather than a fixture: nothing new, nothing written, and both files byte-identical by sha256. Run 4 shows the Himalayas stop rule working, 25 requests falling to 1 once a high-water mark exists.

Per board on run 1 `[VERIFIED]`: speechify 361, veeamsoftware 243, gomotive 150, joblogic 33, coderoad 29, spreetail 24, careem 21, brkz 19, smart-working-solutions 19, globalli 12, banyancanopygroup 6.

**Speechify has shrunk from 1086 postings on 2026-09-11 to 361.** Not investigated; noted because the earlier logs rest on the larger figure.

19 rows survive the filter out of 917, and one of them is a Karachi and Lahore role: Careem, "Senior Software Engineer I", published 2026-08-19. That is the pipeline doing the job it exists for.

## How each step was verified

Every step got a check shown to fail before the next began, by mutating the thing the check guards and confirming the suite caught it. A suite that passes under mutation is not testing what it claims to test.

| Step | Mutations | Survivors |
|---|---|---|
| 1 Board configuration | 4 | 0 |
| 2 Shared HTTP module | 8 | 0 |
| 3 Adapters | 11 | 0 |
| 4 Normaliser | 10 | 0 |
| 5 Deduplicator | 6 | 1, fixed |
| 6 Filter chain | 10 | 2, fixed |
| 7 Writers and data branch | 11 | 2, fixed |
| 8 The run | 10 | 2, fixed |
| 9 Himalayas | 9 | 1, fixed |

The survivors are the useful part, because each was a test that looked adequate and was not.

**The dedupe representative.** Tests asserted the choice was deterministic, which any stable rule satisfies, so a mutation reversing the documented rule passed. Determinism was not the guarantee; the documented rule was.

**"Storage Engineer must not match rag" passed trivially.** The pool contains no bare `rag` term, because ADR-0021 forbids it, so substring matching could not fail that case. The mechanism is now tested directly by compiling `rag` as the pool would if anyone added it.

**A dead default.** `rule_experience(row, max_years=None)` had a default no caller read, since `apply_chain` always passes the value. It was deleted rather than tested, because a test for an unreachable path is theatre.

**Appending versus snapshotting.** No test distinguished them. The case that does is a batch that omits an earlier record, which is what a board sends when it drops an old posting: a writer that wrote the batch would delete history and the counts would still look plausible.

**The seen store's sorted save** was never exercised, because the fixture inserted in sorted order already.

**TEST_MODE isolation was partial.** The raw path was isolated; the filtered layer and seen store were not. A test run would have re-dated `first_seen` for every posting and put test rows in front of the operator.

**One dead board aborting the run** survived because two exception handlers were identical. They now differ: a board answering 500 is "failed", an unexpected exception in our own code is "error". A run log spelling them the same hides our bugs among theirs.

**The aggregator's exclusion from the data-branch commit** lived in `main()`, which no test exercised. It is now a function, `files_to_commit`, with a test.

## Two defects found in my own code, by its own tests

**A scratch git index created with `NamedTemporaryFile` left a zero-byte file**, and git refuses that with "index file smaller than expected" rather than treating it as empty `[VERIFIED]`.

**`_git` took `cwd=REPO_ROOT` as a default argument**, which Python evaluates once at import. A test repointing `REPO_ROOT` at a throwaway repository was therefore ignored, and **the test committed a `data` branch to this repository** `[VERIFIED]`. It was deleted, nothing was pushed, and the working tree was untouched, which is the one thing the plumbing design got right. The default is gone and a mutation reintroducing it is caught by three tests.

That second one is worth keeping in mind: the isolation that failed was the test's, not the code's.

## Findings that change what the records say

### Speechify collapses to 11 keys, not the 8 the brief predicts

`[VERIFIED]`. 1086 postings, 8 distinct normalised titles, **11 deduplication keys**. Three titles were published on two dates each:

| Title | Dates | Postings |
|---|---|---|
| Go-to-Market | 2026-05-06, 2026-05-22 | 95, 12 |
| Software Engineer, Data Infrastructure & Acquisition | 2023-12-04, 2025-12-05 | 105, 136 |
| Software Engineer, Platform | 2024-01-24, 2025-05-07 | 138, 103 |

8 + 3 = 11. This is the brief's own key definition rather than a defect: ADR-0001 keys on employer plus title plus publication date. Collapsing across dates would merge a 2023 posting with a 2025 one, which is a repost and not a duplicate, and would make Measure A meaningless for the merged row. **Dropping the date from the key to reach 8 would contradict ADR-0001**, so the number is reported rather than engineered away.

### Two filter rules have no definition anywhere

The architecture document names five rules in the chain. Two of them exist nowhere else `[VERIFIED]` by grep across `docs/`:

**Stated experience.** No record names a threshold. Neither Greenhouse nor Lever returns a structured experience field, so nothing reads one. The rule is implemented and **disabled**: it activates only when a maximum is supplied, and is tested both ways so that supplying one is a one-line change.

**Annotation vendors.** No record carries the list. Three employers are named in `docs/reference/title-pool.md`, which records that one census measured 17 of 34 rows as Welo Data, Welocalize and Innodata, and states that the rule catches them by employer. Those three are used, sourced from that line, and marked **provisional**.

Inventing a threshold or a vendor list would be policy invented by an implementing session.

### The location filter is in the records and not in the code

The brief says there is no location filter and defers it to MVP 2 by decision. **No record carries that decision** `[VERIFIED]`. Two records still describe the filter as present:

- `docs/architecture-2.0.md:195` lists location in the chain, between expiry and stated experience.
- `docs/decisions/0001-two-layer-store.md:55` makes its Confirmation "re-run the location filter over the raw layer with a deliberately broken match rule", which cannot be run against a pipeline that has no location filter.

The brief outranks both under ADR-0022, so the code follows the brief. The records are left alone, because changing a decision record is not an implementing session's job.

### `expires_at` exceeds ADR-0011's enumeration, and so does most of the row

ADR-0011 lists what the data branch stores: employer, title, location, ATS platform, publication date, first-seen date, stated experience, canonical URL, and the filter verdict with its reason.

The row shape carries eight fields beyond that list, each required by a later record: `identity`, `source`, `board_id`, `external_id`, `employer_provenance` and `url_provenance` (ADR-0026), `title_normalised` (ADR-0027), `published_field`, `ordering_date` and `ordering_date_source` (ADR-0007), plus `published_meaning_unconfirmed` and `expires_at`.

None is description text, so the spirit holds. The enumeration is materially out of date as a schema.

## Himalayas: read the diff and state which it was

ADR-0019: "Himalayas leaves the slice if adding it forces a change to the shared HTTP module, the normaliser's row shape, or the filter chain. A diff touching only a config entry and an adapter file passes."

**The two halves of that criterion disagree for this diff** `[VERIFIED]`.

By the three named components, it passes. None changed:

| Component | Status |
|---|---|
| `src/http_client.py`, the shared HTTP module | **unchanged** |
| `src/normalise.py`, the row shape | **unchanged** |
| `src/filters.py`, the filter chain | **unchanged** |

By the "only a config entry and an adapter file" test, it fails. The diff is:

| File | Lines | What |
|---|---|---|
| `src/adapters/himalayas.py` | +146 | new adapter |
| `config/boards.json` | +9 | the board entry |
| `src/config.py` | +12 | registers the platform and its source class |
| `src/run.py` | +50 | the pagination loop and the high-water stop |
| `src/storage.py` | +11 | routes aggregator raw files to a local directory |

The substantive one is `run.py`. Himalayas is the first source that needs more than one request per board, so the orchestrator gained a pagination loop. Putting that loop in the adapter would have broken the rule that adapters parse and nothing else; putting it in the HTTP module would have failed ADR-0019's condition outright. The `storage.py` change is ADR-0020's routing, which any aggregator needs.

**This is not mine to decide.** It is a scope question about what the slice contains, and the criterion is ambiguous exactly where it matters. It is raised for the architecture chat below. The work is committed and tested either way, and **removing Himalayas is a one-line deletion from `config/boards.json` with no code change**, so the decision is cheap in both directions.

## For the architecture chat

**1. Does Himalayas stay?** ADR-0019's condition passes on its three named components and fails on its "config entry and adapter file" wording. Which formulation governs, and if the answer is "stays", ADR-0019 should be amended to say that an orchestrator change for pagination is permitted.

**2. The stated-experience threshold and the annotation-vendor list.** Both are named in the architecture document as filter rules and defined nowhere. The first also needs a source field: no slice platform returns one, so a threshold alone would not make it work.

**3. The location filter's deferral has no record.** ADR-0001's Confirmation currently names a filter the pipeline does not have.

**4. ADR-0011's enumeration.** It reads as a schema and is eight fields out of date, every one of them required by a later record.

## Checked and found already correct

- The registry's slugs resolve: all nine Greenhouse boards and both Lever boards answered 200 on every live run `[VERIFIED]`.
- The title pool parses to exactly 50 terms and its exempt single-token list matches ADR-0021 `[VERIFIED]`.
- ADR-0028's budget was never approached: the largest run used 36 of 500 `[VERIFIED]`.
- The pre-commit hook's five gates all fired as expected across six commits, including gate 2 refusing nothing because the cassettes were sanitised before staging `[VERIFIED]`.

## Rejected alternatives

- **Installing `requests` was accepted, not assumed.** The brief permits it and session reuse across eleven boards is a real gain, but the spikes proved `urllib` sufficient, so it is recorded as a choice rather than a necessity.
- **Dropping the publication date from the dedupe key** to reach the brief's 8 groups. Rejected: it contradicts ADR-0001 and merges reposts years apart.
- **Inventing an experience threshold or a vendor list.** Rejected: policy invented by an implementing session is policy nobody decided.
- **A location filter**, because two records still describe one. Rejected: the brief outranks them under ADR-0022.
- **Putting the pagination loop in the adapter or the HTTP module.** Rejected: the first breaks the parse-only rule, the second fails ADR-0019's condition outright.
- **Reading Himalayas' empty `locationRestrictions` as worldwide.** Rejected: what an empty array means was never established, and reading it as worldwide would widen the display on a guess.
- **Committing the aggregator's rows.** Rejected by ADR-0020, and enforced by source class rather than by filename, because a filename convention is one rename from leaking.

## Not done, and not established

- **The workflow has never run on GitHub.** The file is written and its logic is readable, but no scheduled run has fired, and the data-branch push has never been exercised against the remote.
- **Nothing has been written to the data branch in anger.** Every live run used `--no-commit`.
- **Airtable does not exist**, so the slice's Confirmation in ADR-0009, the operator finding a role in the display they had not already seen, cannot yet be met.
- **Lever's `createdAt` remains unproven.** Rows carry `published_meaning_unconfirmed` so the pipeline can settle it from its own data within days.
- **Speechify's drop from 1086 to 361 postings** was noticed, not investigated.
- **The weekly outcome sweep and the contract check** are untouched; they were not in this brief.
- No decision record was written or edited.

---

# Added at session close

Everything above was written during the work. This section is what existed only in the session's context and would otherwise die with it. None of it is in the diff.

## Why each of the eight mutation survivors survived

The brief named the `rag` one. The other seven are the useful part, because the *shape* of each failure recurs.

1. **The dedupe representative, "latest instead of earliest".** The tests asserted the choice was *order-independent*, which every stable rule satisfies. Determinism was tested; the documented rule was not. **Shape: testing a property weaker than the guarantee.**
2. **`rag` matching "storage".** The pool contains no bare `rag` term, because ADR-0021 forbids single tokens, so substring matching had nothing to collide with: "storage engineer" does not contain "rag engineer". The brief's own case could not fail. **Shape: a test whose precondition never occurs.**
3. **`rule_experience`'s default threshold.** `apply_chain` passes `max_years` explicitly on every path, so the function's own default was unreachable. Mutating it changed nothing because nothing read it. **Shape: dead code, which no test can guard and none should try to.**
4. **Snapshot instead of append.** Every test passed a batch that was a superset of what was stored, so `dumps(records)` and `dumps(existing + fresh)` produced identical files. The distinguishing case is a batch that *omits* an earlier record. **Shape: fixtures that only ever grow.**
5. **The seen store's sorted save.** The fixture inserted identities 0, 1, 2 in already-sorted order, so `dict(entries)` and `sorted(entries)` were the same bytes. **Shape: a fixture accidentally satisfying the invariant under test.**
6. **One dead board aborting the run.** `except HttpError` and `except Exception` both set status `"failed"`, so narrowing the first changed nothing: the second caught it identically. The specific handler was dead weight. **Shape: two branches with identical effect, so neither is load-bearing.**
7. **TEST_MODE ignored by the run's paths.** `self.paths` covered the filtered layer, seen store and run log, but `raw_path()` took `test_mode` as its own argument, so the raw file stayed isolated even with `self.paths` pointed at production. The test only checked the raw file. **Shape: partial isolation, sampled by the test on its working half.**
8. **The aggregator file reaching the data-branch commit.** The exclusion lived inside `main()`, which no test called. **Shape: a guarantee implemented in an entry point rather than a unit.**

## The `_git` default-argument defect, in full

    def _git(args, cwd=REPO_ROOT, env=None, check=True, stdin=None):   # wrong

Python evaluates a default argument **once, at import**. `REPO_ROOT` was bound into the signature when the module loaded. `TestDataBranch.setUp` did `storage.REPO_ROOT = self.dir` to point the code at a throwaway repository, which rebinds the module global and does nothing at all to the already-bound default. Every `_git` call therefore ran in the real repository, and `commit_files` created `refs/heads/data` here with a commit named "run".

**What made it invisible.** Three things compounding.

- **The other two functions were correct.** `branch_exists()` and `read_branch_file()` referenced `REPO_ROOT` *inside their bodies*, so they resolved at call time and honoured the patch. The harness looked like it was isolating properly, because two thirds of it was.
- **The plumbing design never touches the working tree.** That is the feature that kept the blast radius small, and also the reason nothing looked wrong: `git status` stayed clean throughout.
- **An orphan branch is invisible in normal use.** Never checked out, absent from `git log` on main, visible only in `git branch`.

**What caught it.** `test_the_data_branch_is_orphan` failed with `0 != 1`: it ran `git rev-list --parents -n 1 data` inside the temp repo and got nothing, because no `data` branch existed *there*. The assertion was about orphanhood and the failure was about location, which is why it took a moment to read.

**What would have caught it earlier.** Asserting on *where the ref landed* rather than on the returned sha. One line, `git -C self.dir rev-parse data`, fails instantly. More generally: never take a mutable module global as a default argument. The fix resolves it per call, and a mutation reintroducing the default is now caught by three tests.

**It recurs during mutation testing**, by design: the mutation that reinstates the default recreates the stray branch every time it runs. Both occurrences were deleted, neither was pushed. A future session running `mutations_step7.json` should expect it and check `git branch` afterwards.

## What was tried and did not work

- **Heredocs for content containing backslashes.** `<<'PY'` mangled escapes at least five times, including while writing this very section: `\n` became a literal newline inside a string literal, and `\a` in `.venv\Scripts\activate` became a bell character that reached `CLAUDE.md` and had to be repaired. Anything with a backslash goes through the Write tool, or is built with `chr(92)`.
- **The first mutation harness** embedded mutations as Python literals inside `mutate.py` and rewrote that list with a regex. It broke on the same escaping problem. Restructured to read mutations from a JSON file, which is what made the remaining eight steps cheap.
- **`tempfile.NamedTemporaryFile(delete=False)` for the scratch git index.** It leaves a zero-byte file, and git refuses that with "index file smaller than expected" rather than treating it as empty. A path inside `mkdtemp()` that git creates itself works.
- **`unittest discover` without `tests/__init__.py`** fails with "Start directory is not importable" rather than simply finding nothing, which is an opaque error for a missing file.
- **Writing working files to the repository root.** `filtered.json`, `seen.json`, `fetch-all/`, `logs-runs/` and a `test-` copy of each went to the root for most of the build, then had to move under `data/` with a `branch_path()` mapping so the data branch's own layout did not move with them. `.gitignore` had said `data/` since before any of this code existed.
- **In-place text replacement without asserting the anchor.** A `write_text` substitution silently matched nothing because the file had been rewritten between edits. Every later replacement asserts the anchor first, and `mutate.py` refuses a mutation whose anchor does not appear exactly once.
- **`Edit` on the operator's registry file** failed because the tool requires the file to have been read in-session. A script with an explicit uniqueness check did the job and left a backup.

## Where the close alternative was wrong

Each of these had a defensible-looking other answer.

- **Speechify's 11 dedupe keys.** The alternative was to drop the publication date from the key so the brief's predicted 8 came true. It would have merged a 2023 posting with a 2025 one and contradicted ADR-0001. The number was reported instead.
- **The two undefined filter rules.** The alternative was to invent a threshold and a vendor list. The chain would have looked complete while enforcing policy nobody decided.
- **The location filter.** The alternative was to build it, since two records still describe it. It would have dropped the Careem Karachi role, because the geocoder writes "Karachi, Punjab, Pakistan" and Karachi is in Sindh.
  - **Correction, 2026-09-17, by a later session: that reason is wrong for this pipeline.** "Karachi, Punjab, Pakistan" comes from `docs/architecture-2.0.md:408`, which describes a geocoder in *harvested* data and says "Direct board polling gives raw location text instead". This pipeline stores the board's raw text. `[VERIFIED]` the Careem role's stored location is "Karachi, Pakistan; Lahore, Pakistan", and no stored row contains "Karachi, Punjab". Stored Karachi locations do vary: "Karachi, Pakistan", "Karachi, Sindh, Pakistan", "Pakistan - Karachi", "Karachi" alone, and semicolon lists. That variety is the real fragility a location matcher would face. The decision not to build the filter stands; it came from the build brief, not from this reason.
- **The Himalayas verdict.** The alternatives were to declare it passing and move on, or to delete it. Either would have been an implementing session deciding scope.
- **Pagination placement.** The alternative was the shared HTTP module, which is the cleaner API. It would have failed ADR-0019's condition outright and pre-decided the question above.
- **`requests` over `urllib`.** The brief permits it, but the spikes had proved `urllib` sufficient and CLAUDE.md requires a dependency to survive "the standard library can do this". Taken as a choice and recorded as one, not as a necessity.
- **`charset-normalizer`.** The alternative was to uninstall it alongside the other four for tidiness. Its mtime is two months older and it sits in user site-packages, so it was never mine.

## Noticed and not investigated

Beyond Speechify falling from 1086 postings to 361.

- **Speechify is 39% of volume and has produced zero kept rows on every run.** Whether it belongs in the board list at all is a question nobody has asked.
- **CodeRoad keeps 6 of 29, a 21% yield, far above every other board.** The registry records it as Latin America only, so its high yield may be worth nothing to this operator.
- **Greenhouse's `metadata` array is parsed away, and it may answer Question 3.** On veeamsoftware it carries `Workday P Level` on all 242 postings, plus `Job Family`, `Worker Type` and `Work Type`. A seniority signal in a structured field is exactly what the stated-experience rule lacks. **This is the most promising unexplored lead in the repository.**
- **Lever's `country` and `workplaceType` are also discarded.** The adapter reads `categories.location` only; `country` gives "IN" and "PK", `workplaceType` gives "remote", both cleaner than the free-text location.
- **Board counts drift between runs and nobody has characterised the churn:** gomotive 148 to 150, brkz 23 to 19, joblogic 31 to 33, smart-working-solutions 21 to 19, spreetail 27 to 24. That rate bears directly on ADR-0003's unmeasured "20 to 50 new postings a day".
- **Careem returned exactly 21 postings on 2026-09-11 and 21 today**, and nobody checked whether they are the same 21.
- **Himalayas' first contact stops at the page cap, not at the end of the feed.** 25 pages, 500 postings, out of 100,000-plus. The first run captures an arbitrary depth of the newest, and whether 500 is the right first-contact depth was never considered.
- **Nothing reads the run log.** ADR-0028's Confirmation requires aggregating per-source request counts over a month, and no tooling exists to do it. Logs accumulate one file per run under `data/logs-runs/` with no rotation.

## Records believed stale, not raised because nothing was blocked

- **`STATE.md`'s Documentation table says "24 records in `docs/decisions/`".** There are 29.
- **`README.md` predates the code.** It documents what the repository stores and names `tools/generate_map.py`, but says nothing about the virtual environment, how to run the tests, or how to run a fetch. It is the first thing a stranger reads and it now describes half the repository.
- **`docs/architecture-2.0.md` runtime view, step 8**, says "Batch-write to Airtable, ten per call" as a step of a normal run. There is no Airtable writer and, by the operator's own decision, no base. It reads as description rather than intent.
- **ADR-0009 says the slice is eleven boards**; `config/boards.json` holds twelve entries. The twelfth is the ADR-0019 conditional and a test says so explicitly, but the arithmetic will confuse someone.
- **`CHAT_STATE.md`** at the repository root is gitignored local scratch and still describes the spike as the one open item. It is not an implementing session's to edit, and the map deliberately skips it.

## Measurements taken after the body of this log was written

These were computed while preparing the architecture-chat brief, after the
sections above were finished. They exist nowhere else and several bear directly
on open Confirmations.

### Measure A is computable on every row in the slice

| Source | Rows carrying a real publication date |
|---|---|
| Greenhouse and Lever | 916 of 916, **100%** |
| Himalayas | 500 of 500, **100%** |

Nothing in the slice falls back to first-seen. 43 Lever rows carry
`published_meaning_unconfirmed`, because `createdAt`'s meaning is still
unproven, but they do carry a date.

### First data toward ADR-0028's Confirmation

ADR-0028 sets the ceiling at 500, says explicitly that it is a runaway guard
rather than a measured volume, and says the real number comes from the run log
after a month. The first four observations:

| Run | Requests | Of 500 |
|---|---|---|
| 11 ATS boards only | 11 | 2.2% |
| 11 ATS + Himalayas, first contact | 36 | 7.2% |
| 11 ATS + Himalayas, steady state | 12 | 2.4% |

**Steady state for the whole slice is 12 requests per run, 24 a day.** The
ceiling is roughly forty times the observed need. That is one month short of
the evidence the record asks for, but it is the first real data and it points
at a much smaller number.

### What survived the filter, and whether it is reachable

Nineteen rows from 916 ATS postings. **Seven are Pakistan-reachable:**

| Title | Employer | Location |
|---|---|---|
| Senior Software Engineer I | Careem | Karachi, Lahore |
| Software Engineer I | Careem | Karachi, Lahore |
| Senior AI Engineer, twice | BRKZ | Cairo, Islamabad, Karachi, Lahore |
| AI Engineer | Globalli | India, Pakistan |
| AI/ML Engineer | Joblogic | Lahore |
| Senior Backend Engineer, PHP/Symfony | Smart Working Solutions | Pakistan |

The other twelve are US, Australia, India, Latin America and Vietnam.

### The title pool admits 2.1%, and ADR-0021's feedback loop has now fired

ADR-0021 says the drop log is the sole feedback signal for a missing term and
that reading it is load-bearing rather than optional. This is the first run that
produced one, so this is the first time anyone has read it.

**916 ATS postings, 19 admitted, a 2.1% survival rate.** Himalayas admits 4.0%.

Ten terms did all the admitting. `ai engineer` 7, `ai ml` 2,
`software engineer i` 2, `backend engineer` 2, then one each for
`forward deployed`, `ai platform`, `agentic`, `ai solution`,
`machine learning`, `ai automation`. **Forty of the fifty terms admitted
nothing.**

**One concrete gap, three postings.** "Forward Deployment Engineer" was dropped
while "Senior Forward Deployed Engineer" was kept. The term is
`forward deployed`, and ADR-0021's plural rule appends `(?:e?s)?` to the
term's final word, which cannot reach "Deployment". That is the pool's own
machinery working exactly as specified and still missing a real variant. Adding
`forward deployment` as its own term is the fix; the existing machinery cannot
produce it.

**What the other 897 drops are**, by inspection: Java and C# developers, QA and
SDET roles, Customer Success Engineers, Solutions Architects, sales. The
allowlist is doing its job. 476 of the 897 contain an engineering word, and
almost all of those are genuinely out of domain. The open question is not
whether 2.1% is too low in general but whether any of those specific families
should be admitted, and that is the operator's call, not an implementing
session's.

### Per board, from the first live run

**Correction, 2026-09-17, by the following session.** This table mixes two runs, so its rows need not sum. The Postings column is from run 1 (ATS total 917, CodeRoad 29). The Dropped and Kept columns are from the run recorded in `data/test/logs-runs/20260916T200345.122061Z.json`, the only run log that survives (ATS total 916, CodeRoad 28, `test_mode` true). CodeRoad lost a posting between those runs. `[VERIFIED]` that run log shows `greenhouse:coderoad` fetched 28, dropped 22 by title, kept 6; the stored `data/test/fetch-all/greenhouse.json` holds 28 CodeRoad rows; and no identity is duplicated across the three stored raw files. The same mix explains why this log says 917 in some places and 916 in others.

| Board | Postings | Dropped | Kept |
|---|---|---|---|
| greenhouse:speechify | 361 | 361 | **0** |
| greenhouse:veeamsoftware | 243 | 241 | 2 |
| greenhouse:gomotive | 150 | 148 | 2 |
| greenhouse:joblogic | 33 | 31 | 2 |
| greenhouse:coderoad | 29 | 22 | 6 |
| lever:spreetail | 24 | 23 | 1 |
| greenhouse:careem | 21 | 19 | 2 |
| greenhouse:brkz | 19 | 17 | 2 |
| lever:smart-working-solutions | 19 | 18 | 1 |
| greenhouse:globalli | 12 | 11 | 1 |
| greenhouse:banyancanopygroup | 6 | 6 | 0 |

### A note on leftover state

`data/test/` holds the artefacts of this session's four TEST_MODE runs,
including a seen store with 1416 identities. It is gitignored and it is not
production state. A first production run starts from an empty store and will
therefore treat every posting as new, which is correct. Delete `data/test/` if
a clean test run is wanted.
