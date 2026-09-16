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
