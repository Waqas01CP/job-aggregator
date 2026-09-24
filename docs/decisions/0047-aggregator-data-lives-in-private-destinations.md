---
status: accepted
topic: storage
description: Aggregator data lives in private destinations: a second private repository for every aggregator-sourced store, and the private Airtable base. Reverses ADR-0020's deferral. Nothing aggregator-sourced ever reaches the public branch.
date: 2026-09-19
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0047: Aggregator data lives in private destinations

## Context and Problem Statement

ADR-0020 routed aggregator rows to local files only, never committed and never pushed, and deferred a second private repository until there was a reason to spend the effort. It named the cost it was accepting: aggregator rows have no offsite copy, and if the machine fails that data is gone.

On a GitHub runner there is no machine. The local file is created inside the job and destroyed when the job ends. Measured from the four production run logs on the `data` branch at `d883b82`, read 2026-09-19: each run fetched 500 Himalayas postings and kept between 21 and 26. Every kept row was discarded at the end of the run. Himalayas has been polled since 2026-09-17 and has produced nothing the operator has ever seen.

That is the reason ADR-0020 was waiting for. The deferral was not wrong when written; it was written before the pipeline moved to a runner.

Himalayas' own two documents disagree about what is permitted. Its API reference invites developers, researchers, job board operators and AI tools to consume the feed, states the API is free and unauthenticated, and asks only for a visible link back when the data is displayed on your own website or application. Its terms page, current as of 2026-09-17, prohibits automated data gathering without prior written approval, and separately prohibits copying, reproducing, republishing or distributing material from the site. Both were read on 2026-09-19.

The pending question of whether aggregator rows may reach the private Airtable base is the same question in a second place, and is answered here rather than separately.

## Decision Drivers

- An aggregator source that stores nothing produces nothing. Himalayas' trial cannot be judged on data that no longer exists.
- ADR-0011's public artefact is deliberate and stays.
- ADR-0020's routing principle works and needs no replacement, only a destination.
- The operator wants the option to delete an aggregator's data completely, at any time.
- Anything committed to a public repository survives deletion, in that history and in every clone already made.

## Assumptions

- Private storage and a private Airtable base are not publication under Himalayas' terms. **Stated** by the operator, 2026-09-19, who read the conflict above and declined to seek the written approval the terms describe. Not legally verified and not legal advice.
- A private repository that receives only git pushes consumes no Actions minutes. **Sourced** from GitHub's Actions billing documentation, checked 2026-09-19: Actions usage is free for public repositories, the per-plan minute allowance applies to private repositories, and minutes are charged to the owner of the repository where the workflow runs. No workflow runs in this repository, so no minutes are charged. Not exercised.
- The free plan allows unlimited private repositories. **Sourced** from GitHub's pricing page, checked 2026-09-19.
- Himalayas yields 21 to 26 kept rows per run. **Measured** from the four run logs named above.

## Considered Options

- Keep ADR-0020's local-only routing and accept that aggregator rows are discarded.
- Make the whole repository private.
- A second private repository holding every aggregator-sourced store.
- A second private repository holding every store of both classes.

## Decision Outcome

Chosen option: "a second private repository holding every aggregator-sourced store".

**We will create one private repository to hold aggregator-sourced data**, hosted on the operator's existing account. Which account owns it changes nothing in this design except which token is issued.

**We will apply ADR-0020's routing at every layer, not only the raw one.** Whatever an ATS-sourced row gets on the public `data` branch, an aggregator-sourced row gets in the private repository: its per-source raw file, its seen entries, its filtered rows, and its rows in ADR-0043's three outcome stores. ADR-0020 chose one file per source precisely so that this is a copy rather than a transformation.

**We will never write an aggregator-sourced row to the public data branch.** Unchanged from ADR-0020, including its 2026-09-17 clarification that a seen-store entry is a row for this purpose, because it carries a publication date.

**We will write aggregator rows to the private Airtable base.** The base is private and is not a website the operator publishes. This closes the pending question and makes an aggregator source ordinary: it is filtered, projected, classified and retired exactly like an ATS source, under ADR-0046.

**We will reach the private repository with a personal access token held as a repository secret.** A workflow's built-in token reaches only the repository it runs in, so a token is required whichever account owns the store. This is the eighth secret.

**We will fail a run visibly when the private store cannot be written.** An unreachable private store must not degrade into a run that reports success having silently dropped its aggregator rows, which is the failure this record exists to end. *(2026-09-24: the operator decided that such a run exits 2, not 1, with the public fetch committed. "Visibly" is the run log's `private_store` block, the workflow's exit-2 warning, and a failed run on the third in a row. This changes what the clause commits to. Recorded by the implementing seat for the architecture chat to confirm or supersede; see Changes. Annotated inline after the audit of 2026-09-24, F7, which found the change only in the Changes table.)*

**We will treat deletion as a documented purge**, in `docs/how-to/`: remove the source from the board configuration, delete its rows from the Airtable tables, then delete the private repository. Because nothing aggregator-sourced was ever public, that purge is complete.

### Consequences

Himalayas' kept rows become durable and reach the operator for the first time, and its trial becomes judgeable.

ADR-0020's strongest accepted cost is paid off. Aggregator rows gain history and an offsite copy.

Every store now exists twice, once per class. Anyone comparing a count on the public branch against a count in the pipeline's own log will see a difference by design, which is the third such difference after ADR-0037's grouping and ADR-0040's projection filter.

A second repository to create, a token to issue and rotate, and one more secret. The token grants write access to that repository and lives in the public repository's secrets, where secrets are not public but are readable by anything the workflow runs.

ADR-0046's skip rule now reads six outcome stores rather than three.

The deletion option is real and complete, which it could never be for anything committed publicly.

Deduplication already reads across files, per ADR-0020, so the split adds no new case there.

### Confirmation

After the first run with the private store in place: the public `data` branch holds no file under `fetch-all/` sourced from an aggregator, and no aggregator identity in its seen store. The private repository holds the Himalayas raw file with the count the run log states, and its filtered store holds the kept count the run log states. A matching count in the private store and an absent file on the public branch is the passing case, which is ADR-0020's own Confirmation extended to the new destination.

**The check that can fail:** revoke or corrupt the token and run. The run must fail and say so. *(2026-09-24: under the operator's decision annotated above, "fail" is exit 2 with the failure named, never a clean exit 0. See Changes.)* If it completes and reports a successful fetch with no aggregator rows stored, the visible-failure rule is not implemented and the original defect has been rebuilt in a new place.

The existing commit-step guard, which reads every record's source and refuses any file holding an unpublishable row, must still refuse. It is not replaced by this record.

## Pros and Cons of the Options

### Keep local-only routing

Good, because it is decided, built, and guarded.
Bad, because on a runner it stores nothing, which is measured above rather than argued.

### Whole repository private

Good, because it removes the routing question entirely.
Bad, because it destroys the public artefact, which ADR-0011 makes a stated goal, and it would start charging Actions minutes against a 2,000-minute allowance for runs that are currently free.

### Second private repository for every store of both classes

Good, because one set of stores is simpler than two, and the outcome stores hold the operator's own classifications, which are private in nature.
Bad, because it empties the public data branch of the audit trail ADR-0002 exists to create, and it makes the public repository code only. That is a larger change than the problem requires.

## More Information

Reverses one clause of ADR-0020, "we will not build the second private repository now", which carries a Changes row pointing here. The rest of ADR-0020 stands, including its routing rule, its one-file-per-source layout and its seen-store clarification.

Answers the pending question on aggregator rows and the private Airtable base, and retires the pending item on a second private repository.

Terms evidence per source: `docs/research/0003-job-source-survey.md`. The two Himalayas documents named in Context were read directly on 2026-09-19 and are not in that survey.

ADR-0011 and ADR-0002 are unaffected and hold for the data they govern. ADR-0043 owns the outcome stores this splits. ADR-0046 owns the skip rule that now reads them all.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-24 | A private store that cannot be restored or written exits 2, not 1. The public fetch is committed and the run log's `private_store` block names the failure. When the restore failed, the aggregator boards are not polled and the projection fails, since the private outcome stores are unknown. Three such runs in a row mark the run failed after the push, the rule ADR-0034's Changes records for the projection | Exit 1 stops the workflow's push, so it would lose the public fetch for a failure of the private store alone. **Exit 2 with the public fetch committed is the operator's decision, 2026-09-24, D6**; it changes what the Decision Outcome's "fail a run visibly" and the Confirmation's "the run must fail" commit to, and both clauses now carry an inline note. **Skipping the aggregator boards and failing the projection when the restore failed is the implementing seat's design**, not his decision: nothing fetched could be kept, and the private outcome stores are unknown. *(Attribution corrected 2026-09-24 after that day's audit, F7: this row first credited both to him, and read the change as an interpretation.)* All of it is for the architecture chat to record, confirm or supersede. He also set the token's expiry, 2027-01-01, which `STATE.md` carries as a rotation due |
| 2026-09-24 | Built. The private repository holds one branch per mode, `data` and `data-test`, at ADR-0020's public paths: `fetch-all/<source>.json`, `filtered.json`, `seen.json`, `outcomes/`. A committing run restores the aggregator working copies from its branch before any fetch and pushes them as a fast-forward after it; a run whose restore failed never pushes. Nothing reads the repository's default branch | Implementation facts, recorded by the implementing seat. GitHub makes the first branch pushed to an empty repository its default, so which one that would be depends on whether a test run or a scheduled one gets there first. Brief 6's projection read the default branch and is replaced by the restored working copies |
