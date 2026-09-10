---
status: accepted
date: 2026-09-10
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0019: Add aggregator feeds as a second source class

## Context and Problem Statement

The pipeline's sources have until now been 53 employer ATS boards from the operator's registry. Each is one employer's own careers posting, polled directly.

Research pass 0003 surveyed job aggregators, which index many employers from one endpoint. Six pass every gate the survey applied: a keyless machine-readable endpoint, coverage of a lane the operator can be hired in, terms permitting low-rate polling, and a publication date field. They are Jobicy, Himalayas, Arbeitnow, RemoteOK, We Work Remotely and ai-jobs.net. Remotive and Working Nomads pass with caveats.

The operator has stated he is open to remote work for employers in Europe, the Middle East, the United States, Canada and elsewhere, provided the role can be performed from Pakistan. The aggregators carry that lane. The ATS registry largely does not.

None of the six carry meaningful Pakistan on-site inventory. The boards that do, Rozee.pk foremost, expose no free API at all.

Two of the six attach terms that constrain what may be republished. Jobicy prohibits redistribution to other job boards. Remotive prohibits submitting its jobs to third-party websites and states it will terminate access.

Arbeitnow's own description says its source is applicant tracking systems including Greenhouse and SmartRecruiters, so part of its output covers boards the pipeline already polls directly.

## Decision Drivers

- The remote lane is where the operator's stated openness is widest and where ATS registry coverage is thinnest.
- All six are free and keyless, so adoption cost is adapter work only.
- All six carry a publication date, without which ADR-0015's Measure A is uncomputable.
- Two carry redistribution constraints that interact with ADR-0011's public repository.

## Assumptions

- The six feeds carry roles matching the target titles at usable volume. Not measured; the survey established topical fit, not counts.
- Overlap between Arbeitnow and the directly polled Greenhouse and SmartRecruiters boards is small enough not to dominate. Not measured.
- Employer name strings from an aggregator will differ from the same employer's own ATS string often enough to break naive deduplication. Expected, not measured.
- Quotas and terms recorded in research 0003 were accurate on 2026-09-10 and may change.

## Considered Options

- Registry only. No aggregators.
- Add all sources the survey assessed.
- Add the six that pass all four gates, staged, starting with one.

## Decision Outcome

Chosen option: "add the six that pass all four gates, staged".

We will treat aggregators as a second source class alongside employer ATS boards, not as a replacement for them.

We will read the employer name from the response payload in every case, never derive it from the configuration entry. This is the rule that lets one configuration model serve both shapes: an ATS slug returns one employer, an aggregator endpoint returns many, and neither the normaliser nor the config needs to know which.

We will add Himalayas first, inside the vertical slice, on condition. It is the best documented of the six, keyless, and carries `locationRestrictions` and `timezoneRestrictions`, the only structured eligibility fields found anywhere in the survey.

**The condition, stated as a criterion so it can actually trigger.** Himalayas is removed from the slice if adding it forces a change to the shared HTTP module, the normaliser's row shape, or the filter chain. Adding a configuration entry and an adapter file is not a complication; that is the model working. Changing a component every other source shares is a complication, and it means the model was wrong and should be fixed before eleven more adapters depend on it.

If it is removed, it returns after the slice is live, alongside the other five.

We will add the remaining five after the slice, in survey order.

We will record the source of every row, because ADR-0020 routes storage by source class.

We will carry attribution as each feed's terms require.

### Consequences

Coverage extends from 53 named employers to those plus whatever the six aggregators index, which is a larger change to reach than the entire Tier D of the ATS registry would have been.

The configuration model serves both shapes with no refactor, because employer comes from the payload.

Deduplication now has to work across source classes. The same posting can arrive once from a directly polled board and once from Arbeitnow. ADR-0001's employer plus title plus date key handles it only if employer strings normalise to the same value, so an alias map is now required before the second source class lands rather than after.

Redistribution clauses on Jobicy and Remotive constrain where their rows may be stored. ADR-0020 resolves that.

Rozee.pk remains uncovered, so Karachi on-site inventory stays the largest gap. No decision here changes that.

Per-source terms must be tracked, since they differ. This is new maintenance the ATS boards did not carry.

### Confirmation

The first run including an aggregator reports, per source: rows fetched, publication-date coverage as a percentage, and count of rows whose employer string matches an employer already present from a directly polled board. A high third figure means the alias map is required immediately rather than eventually.

The Himalayas condition is confirmed by inspecting the diff that adds it. A diff touching only a config entry and a new adapter file passes. A diff touching the shared HTTP module, the normaliser, or the filter chain fails, and Himalayas leaves the slice.

## Pros and Cons of the Options

### Registry only

Good, because it keeps one source shape and no per-source terms.
Bad, because it leaves the operator's widest stated lane almost entirely uncovered while six free dated feeds exist.

### Add all sources assessed

Bad, because it includes sources that failed a gate: Jooble's 500-request lifetime cap, Adzuna's aggregation clause, Findwork's overlap with sources already ingested.

## More Information

Evidence: `docs/research/0003-job-source-survey.md`, including endpoints, field names, quotas and the terms clause for each source.

Does not reverse ADR-0012, which prohibits email and search-alert ingestion. An aggregator API is a documented endpoint returning structured data. ADR-0012 carries a correction removing a sentence that had described the registry as the source list.

Storage routing by source class is ADR-0020.
