---
status: accepted
topic: storage
description: Raw storage is routed by source class, so an aggregator's rows are written locally and never published.
date: 2026-09-10
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0020: Route raw storage by source class

## Context and Problem Statement

ADR-0002 places the raw layer on a data branch in this repository. ADR-0011 makes the repository public.

ADR-0019 adds aggregator feeds, two of which attach redistribution constraints. Jobicy prohibits redistribution to other job boards. Remotive prohibits submitting its jobs to third-party websites and states it will terminate access.

A branch inherits its repository's visibility. There is no private branch in a public repository. Any row Actions commits to the data branch is published on the public internet at that moment, whatever the intent behind the fetch.

Fetching is not redistribution and neither is holding a private copy. Committing a fetched dataset to a public repository is a harder case, and the operator does not want to test it.

Employer ATS boards do not carry equivalent clauses. A Greenhouse or Lever board is the employer's own public careers listing, published to be read.

## Decision Drivers

- Two aggregator feeds explicitly threaten termination for redistribution.
- ADR-0002's audit trail, and the offsite copy that comes free with it, are worth keeping for as much data as possible.
- ADR-0011's public repository is a deliberate artefact, not an accident.
- Whatever split is chosen must make a later move to a private store cheap rather than a migration.

## Assumptions

- Employer ATS board postings carry no redistribution restriction comparable to Jobicy's or Remotive's. Based on the nature of those endpoints, not on reading each employer's terms. Not legally verified, and this is not legal advice.
- The four aggregators without an explicit redistribution clause are still safer treated as one class than assessed individually as their terms change.

## Considered Options

- Whole repository private.
- A second private repository holding all data.
- Split by source class: ATS-sourced rows public on the data branch, aggregator-sourced rows local only.

## Decision Outcome

Chosen option: "split by source class".

We will write rows sourced from employer ATS boards to the data branch, as ADR-0002 specifies, unchanged.

We will write rows sourced from aggregators to local files only. They are never committed and never pushed.

We will store the raw layer as **one file per source**, not one file per class. `fetch-all/himalayas.json`, `fetch-all/jobicy.json`, `fetch-all/greenhouse.json`. A row's provenance is then its filename, and no row can be misfiled by a bug in a routing condition.

We will keep the local aggregator files in the same append-only shape as the committed ones, so that moving a source between stores is a file move rather than a transformation.

We will not build the second private repository now. The per-source file split makes it a later copy operation rather than a migration, and it is deferred until there is a reason to spend the effort.

The pre-commit hook already blocks raw payloads. A guard rejecting an aggregator-sourced file from a commit is added when the first aggregator adapter exists, not before, since a guard for a file shape that does not yet exist cannot be given the case built to defeat it.

### Consequences

ADR-0011 holds. No aggregator content reaches the public repository.

ADR-0002's audit trail is preserved for ATS rows and lost for aggregator rows. Their history exists only on the operator's machine.

**Aggregator rows have no offsite copy.** If the machine fails, that data is gone and cannot be reconstructed, because a board only returns what is currently open. This is a real cost accepted deliberately, and it is the strongest argument for the private second repository later.

One file per source means more files and a slightly more complex writer than one file per class.

Provenance becomes structural rather than a field, so a routing bug misfiles nothing.

Deduplication reads across files rather than one, since the same posting may exist in both stores.

Adding a source later requires deciding its class, which is a per-source terms question rather than a technical one.

### Confirmation

After the first run including an aggregator, inspect the data branch and confirm no file under `fetch-all/` sourced from an aggregator is present, and that the local aggregator file contains the rows the run log says it fetched. A count that matches the log but a file that is absent from the branch is the passing case.

## Pros and Cons of the Options

### Whole repository private

Good, because it removes the question entirely.
Bad, because it destroys the public artefact, which is a stated goal.

### Second private repository for all data

Good, because every row keeps an audit trail and an offsite copy.
Bad, because it is a second repository to maintain before there is evidence it is needed.
Deferred rather than rejected. The per-source file split is chosen partly to make this cheap later.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-17 | The aggregator guard lives in the run's commit step, and a hook gate is added for data paths on main | This record promised a guard when the first aggregator adapter existed. A hook cannot serve that purpose: data-branch commits are built with git commit-tree, which runs no hooks. The working guard reads every record's source in the commit step and refuses any file holding an unpublishable row. The hook gate covers a different failure mode, a data path staged on main by hand, and is cheap |
| 2026-09-17 | Seen-store entries are rows for the purposes of this record | Confirms the conservative reading already implemented. An entry carries a posting's identity, its first-seen and last-seen dates and its publication date, and publication date is the field an aggregator's terms restrict. Aggregator entries therefore stay in the local seen store and never reach the branch |

## More Information

Terms evidence per source: `docs/research/0003-job-source-survey.md`.

Constrains ADR-0019. Does not reverse ADR-0002 or ADR-0011; both hold for the data they govern.
