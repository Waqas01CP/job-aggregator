---
status: accepted
topic: storage
description: Every posting is saved whole and privately, as its board returned it, verified by content hash before a posting counts as saved. Closes the conflict between ADR-0016's keep-every-field and ADR-0011's metadata-only.
date: 2026-09-25
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0051: Every field a board returns is saved, privately

## Context and Problem Statement

Two accepted records said different things about what is kept, and the code had quietly followed one of them.

ADR-0016 line 44: "We will store every field each board returns in the raw layer regardless of whether a filter uses it", which ADR-0021 line 104 restates as still standing. ADR-0011 line 42: "identifying and locating metadata yes, description text no". The raw layer holds the 19 keys of `FIELDS` in `src/normalise.py`, so the code followed ADR-0011 and nobody had noticed that ADR-0016 asked for more. The corpus audit of 2026-09-23 raised it as conflict 2 and the implementing seat handed it back on 2026-09-25, having correctly refused to choose between two live records.

The two records are not arguing about the same thing. ADR-0011 is about a public repository and what may be republished from it. ADR-0016 is about not discarding data before anyone knows what it is worth. Read that way the conflict dissolves, and what is left is a question nobody had asked: **where does everything go?**

The operator answered both halves. On what: "wherever description is present then it is to be saved and any other form of data". His reason, in his words, 2026-09-25: "there is a possibility that some of the posts might not have description fetched due to any X reason such as incorrect fetch or maybe the job description is not in the fetch so that is why i am collecting every bit of data and only using some." And the purpose he gave the chat on 2026-09-28, which is the stronger argument: he wants to know later which fields exist, which of them carry a description, and how each board gives it, because an extractor is far easier to build with the data already in hand than without it. The deferred experience rule in ADR-0016 is the first thing that will need it.

On where, his rule was "public unless the two really do not differ, private otherwise". They differ on exactly what he had named himself: public means republishing an employer's text, and whatever personal data sits inside it, permanently and irrevocably. So private.

## Decision Drivers

- A field discarded at fetch time cannot be recovered; a field kept can always be ignored.
- The rules that are still unbuilt, the experience rule above all, need description text to be designed against real data rather than guessed at.
- ADR-0011's promise about the public branch is a promise about other people's text and must not be weakened.
- A fetch can fail, or succeed with a field missing, and that is invisible unless the whole response is kept.
- Nothing may be marked saved on the strength of a write nobody has read back.

## Assumptions

- The description is the field most likely to be absent, truncated or malformed, and keeping everything costs less than deciding now which field will matter. **Stated** by the operator, 2026-09-25.
- The payload cost is affordable at this volume. **Measured** 2026-09-26: a Greenhouse description runs about 6.6 thousand characters, Lever about 11 KB a posting, Himalayas about 5.9 thousand characters, and `?content=true` made a Greenhouse response 6.7 times larger. The Greenhouse adapter's own note had said 9.5 times, which was never measured; the measured figure governs.
- A run saves only what is still pending, not everything it fetched. **Measured** 2026-09-26 and 09-27: the first save carried 824 postings in 9.8 MB because nothing had been saved before, and the evening run of 2026-09-27 wrote nothing at all, logging `pending: 0`.
- A single file stays well inside GitHub's per-file limit. **Sourced** from GitHub's published file-size limit and not verified from the container, which cannot reach GitHub's documentation. At the measured size a run file would need on the order of fifteen thousand unsaved postings to approach it. The implementing seat should confirm the figure from GitHub's own documentation when it next has reason to.
- New ATS volume is on the order of twenty postings a day. **Measured** 2026-09-26 across the eleven boards.

## Considered Options

- Keep following ADR-0011 and narrow ADR-0016 to match, saving metadata only.
- Save everything on the public `data` branch.
- Save everything on a branch of the private repository ADR-0047 already runs.
- Save everything to a local file the workflow discards.

## Decision Outcome

Chosen option: "save everything on a branch of the private repository ADR-0047 already runs".

**Every posting a run fetches is saved exactly as its board returned it**, every field, description included. Greenhouse is now asked for `?content=true`; Lever and Himalayas already returned everything they have.

**It goes to the private repository's own `data-full` branch**, one file per run, and to `data-test-full` in test mode. A branch of its own rather than a folder on an existing branch, so that a partial fetch of it can be taken without touching anything else.

**No run downloads what an earlier run saved.** The branch is fetched without file contents, which is what makes the store cheap to append to however large it grows.

**A posting is marked saved only after a read-back.** A second, fresh partial fetch must list the file with exactly the content hash that was written. Until that holds, the postings in it are not marked saved in the seen stores, and the next run tries again.

**A failed save is the private store's failure and nothing else's.** The run exits 2 and is marked failed at once under D9, after its push, so the public data and the aggregator rows of that run are still saved. An ATS posting is saved by the next run that still lists it.

**Only a posting saved in full sets its board's stop mark.** This is what makes recovery automatic rather than manual: a paginated board whose postings were fetched but not saved is read again, back to the age limit, until a save succeeds.

**The whole entry is carried and saved, never read.** `CLAUDE.md`'s rule that only the fields a filter consumes are read is untouched: the filters still read the 19 normalised keys, and nothing reads the saved entry at all today.

**ADR-0011 is untouched.** The public branch keeps metadata only, and the code still refuses to commit a file holding description text or an aggregator's rows.

### Consequences

ADR-0016's clause is built for the first time, nine days after it was written, and in a place ADR-0016 did not name. That record keeps its rule and gains a pointer here.

The private repository grows by roughly the intake rate rather than by the fetch volume: about twenty ATS postings a day at about 6.6 thousand characters each, plus a morning's eligible Himalayas postings at about 5.9 thousand, which is on the order of half a megabyte a day and under two hundred megabytes a year. That is the first figure anyone has put on this store's growth, and it is the number to re-measure before the five adapters of ADR-0029 land.

A Greenhouse fetch is now several times larger than it was, which spends bandwidth and run time rather than requests. ADR-0028's budget of 500 requests a run is untouched, because asking for content adds no request.

The deferred experience rule can now be designed against real descriptions instead of being guessed at. It is still deferred, and this record does not revive it.

The coupling between the stop mark and the save has a cost worth naming: while the private store is failing, a paginated board's walk never advances, so every morning reads back to the age limit at roughly 23 to 28 pages instead of 4 to 6. That is bounded, well inside ADR-0028's budget, and it is the right trade, because the alternative is a row stored with its text lost for good. A reader seeing a 28-page morning should look at the save before suspecting the walk.

Two stores must now both succeed for a run to be clean, so there is one more way for a run to be marked failed. D9 already required exactly this, and the run of 2026-09-27 is the proof that it behaves as intended.

### Confirmation

**The read-back must be seen refusing.** Point the save at a branch where the file is absent or its hash differs, and confirm no posting is marked saved and the run is marked failed.

**The partial fetch must be exercised against a real one.** The failure of 2026-09-27 survived the suite because the local repository standing in for GitHub honoured no partial fetch and downloaded everything. The test now runs against a real partial fetch and asserts that the earlier file is genuinely absent.

**On-demand downloads must be refused for the whole save**, not merely avoided, so that a future change cannot reintroduce the failure quietly.

**The public branch must be seen refusing description text**, which is ADR-0011's and ADR-0020's existing commit guard, re-run now that descriptions exist in the process. *(Annotated 2026-10-04, wrong when written: no such guard existed, and the row's shape was what kept descriptions out. Built 2026-10-03 in `storage.commit_files`, commit `eb0134e`, so the clause is now true. See Changes.)*

**A `pending: 0` run must write no file at all**, so that an idle day costs nothing.

## Pros and Cons of the Options

### Metadata only, narrowing ADR-0016

Good, because it is what the code already did and costs nothing.
Bad, because it decides now, on no evidence, that no unbuilt rule will ever need a description, and the operator has one such rule already deferred.

### Everything on the public branch

Good, because it is one store, already built, already verified by the commit guard.
Bad, and decisively so: it republishes an employer's text and any personal data inside it, permanently and publicly, which is the exact thing ADR-0011 exists to prevent. The operator ruled it out himself once the difference was named.

### A local file the workflow discards

Good, because it costs no storage and no branch.
Bad, because the file dies with the runner, so nothing is saved at all. It is the option that looks like saving everything while saving nothing.

## More Information

**This closes the corpus audit's conflict 2.** ADR-0016 line 44 stands and is now built; ADR-0011 line 42 stands untouched and governs the public branch alone. Neither record was wrong: they were answering different questions, and the missing decision was where.

ADR-0047 owns the private repository this branch lives in, and now holds ATS description text as well as aggregator rows. ADR-0020 owns the routing that keeps the two apart. ADR-0005 is why a run fetches complete board output in the first place, which is what makes "everything" well defined. ADR-0016's deferred experience rule is the first consumer this store has, and it remains deferred.

The operator's decision, 2026-09-25, in two halves: what to save, in his words above, and where, on the seat's recommendation once he had named the difference between public and private himself. The stop-mark coupling is the implementing seat's design of 2026-09-27, taken while fixing the failure, and it is recorded here because it changes what a save means rather than only how one is written.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | The commit guard the Confirmation names is built. `storage.commit_files`, through which every commit to the public branch passes, refuses the whole commit when a description field holds text anywhere, or when a record file holds markup or a string over 1,000 characters; the refusal names the file, field and record, never the text | The implementing seat found on 2026-10-03 that the clause described a guard that did not exist. Built the same evening on the operator's yes. The public branch passed it at `0b6bb51`, its longest string in a record file a 135-character location |
