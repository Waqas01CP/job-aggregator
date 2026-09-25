# Architecture Decision Records

Every architecture decision made on this project, one file per decision, with the reasoning that produced it and the conditions that would show it was wrong.

Format: MADR 4.0.0 with two documented deviations. Numbered in the order concluded.

The deviations: an added **Assumptions** section, taken from Tyree and Akerman, holding every belief the decision rests on that is not established, so unmeasured numbers are visible and re-checkable rather than buried in prose. And three authoring rules carried forward from Nygard, which MADR does not specify: Context is written value-neutral with the tensions named, Decision Outcome is written in active voice as a rule, and Consequences are always filled including the negative ones.

Records are written at the moment a decision concludes. A record's factual error may be corrected in place with a dated annotation; a change that leaves the decision in force is logged in its Changes table; a change that replaces it is a new record. The criteria for which is which are in `ADR-RULES.md` and in the operator's cross-project decision record standard.

**`ADR-RULES.md` governs this corpus** and is read through rather than in sequence. It adds two ranks to the authority order, distinguishes stale from wrong, and states what a seat may correct without asking. **ADR-0042 was reserved for it and is deliberately unused**; the gap between 0041 and 0043 is not a missing file.

| ID | Title | Status |
|----|-------|--------|
| 0001 | Two-layer store, raw and filtered | Accepted, extended by 0027 |
| 0002 | Raw layer on a git data branch, not a hosted database | Accepted |
| 0003 | Append deltas, not snapshots | Accepted |
| 0004 | Airtable as the filtered display layer | Accepted, clauses reversed by 0014, 0034, 0035 |
| 0005 | Fetch complete board output, filter locally | Accepted |
| 0006 | Twice-daily fetch cadence | Accepted, extended by 0048 |
| 0007 | Recency is a view, not an ingest filter | Accepted |
| 0008 | Title matching by allowlist, blocklist, and unmatched flag | Superseded by 0021 |
| 0009 | Vertical slice first, adapters incremental | Accepted |
| 0010 | No relevance scoring, ranking, or model-based screening | Accepted |
| 0011 | Public repository, metadata only on the data branch | Accepted |
| 0012 | No email or search-alert ingestion path | Accepted |
| 0013 | Three layers, filtered set persisted independently of the display | Accepted, clause reversed by 0030 |
| 0014 | Weekly status sweep, with a four-status outcome taxonomy | Superseded by 0045 |
| 0015 | Two measures, and the archive protocol | Accepted |
| 0016 | Title-only matching against a versioned title pool | Accepted, one clause reversed by 0021 |
| 0017 | Sanitised cassettes as adapter test fixtures | Accepted |
| 0018 | Scheduled contract check against live boards | Accepted, clause reversed by 0036 |
| 0019 | Add aggregator feeds as a second source class | Accepted, clauses reversed by 0026 and 0039 |
| 0020 | Route raw storage by source class | Accepted, one clause reversed by 0047 |
| 0021 | Allowlist-only title matching, with normalisation | Accepted, clause reversed by 0032 |
| 0022 | Document authority order | Accepted |
| 0023 | Context artifact set and onboarding order | Accepted, artifact set extended |
| 0024 | Session log format | Accepted |
| 0025 | Auto Memory is not authoritative | Accepted |
| 0026 | Employer provenance where a payload does not carry it | Accepted |
| 0027 | Deduplication key normalisation, configured per source | Accepted |
| 0028 | Per-run fetch budget, and detail fetched once per posting | Accepted |
| 0029 | Adapter order after the slice, and Dover dropped | Accepted |
| 0030 | A rule change backfills the filtered layer | Accepted |
| 0031 | Personal preferences are configuration, not code | Accepted |
| 0032 | The seniority rule | Accepted |
| 0033 | The data branch is the store, local files are working copies | Accepted |
| 0034 | Airtable gets its own client | Accepted |
| 0035 | The projection upserts on Identity | Accepted |
| 0036 | The contract check reports through the run log | Accepted |
| 0037 | The filtered layer stores rows, the projection groups them | Accepted |
| 0038 | Role families are views, not a ranking | Accepted |
| 0039 | The aggregator condition is the three components | Accepted |
| 0040 | The current rules filter the projection, never the store | Accepted, extended by 0046, one clause narrowed by 0046 |
| 0041 | Location admits unless a source excludes | Accepted |
| 0042 | *reserved for ADR-RULES, deliberately unused* | n/a |
| 0043 | Three outcome stores | Accepted |
| 0044 | The priority star, on named attributes only | Accepted |
| 0045 | The classification flow | Superseded by 0046 |
| 0046 | Classification by status, and the fifteen-day retention | Superseded by 0050 |
| 0047 | Aggregator data lives in private destinations | Accepted, reverses one clause of 0020 |
| 0048 | A source is polled no faster than its feed refreshes | Accepted, extends 0006 |
| 0049 | Architectural rules are guarded by fitness functions, not by prose | Accepted |
| 0050 | The classification flow, consolidated | Accepted, supersedes 0046 |
| RULES | How records are resolved, amended and retired | Accepted |

## Pending

Decisions identified but not concluded.

- Reuse boundary against the LinkedIn pipeline in fyp-career-guidance: which components are adopted, which are deliberately not.
- Description matching, deferred by ADR-0016 until field coverage per platform is known.
- Deduplication across source classes, and the employer alias map ADR-0019 makes necessary.
- Whether Rozee.pk is added as a source. robots.txt permits the job paths and the terms carry no automated-access clause; a sitemap index publishes job URLs daily with the title in the slug.
- An end-state document stating what the finished system is. Confirmed genuinely open by ADR-0023: no prior art exists in either project.
- An in-flight register separate from `STATE.md`, wanted once work is in flight.
- Which skills the project needs, and whether the session log becomes a skill with dynamic context injection.
- Whether an AGENTS.md symlink is added for Antigravity. Claude Code reads CLAUDE.md only, with no fallback, so CLAUDE.md is the real file either way.
- Every unread field in `docs/reference/platform-fields.md`, each needing its own decision about what it means and what its absence means.

## Reading these records

Several records cite files from the operator's LinkedIn collection pipeline, which lives in a private repository. Those citations record where a pattern came from and are not links a reader can follow. They are kept because the provenance is what makes the reasoning checkable.

A record's factual error may be corrected in place, marked as a correction with its date, as in ADR-0005. A change that leaves the decision in force, one clause reversed or something added, is logged in the record's Changes table. A change that replaces the decision, or more than half its Decision Outcome, is a new record superseding the old one.

**Supersession is the last resort, not the default.** Full criteria, with the seven cases and the operational test, are in the operator's cross-project decision record standard. The short version: before stamping a record superseded, ask whether any decision in it is still in force **and not carried into the later record**. If yes, it is not a supersession. A rule that survives but is restated in the later record does not block supersession; it obliges that record to name it as carried forward unchanged. A record whose clause was reversed stays accepted and names the clause; a record that was merely built upon stays accepted and is marked extended.

Records 0004 and 0008 were wrongly stamped superseded on 2026-09-09 and corrected on 2026-09-10. Both remained fully in force, and one held a decision the architecture still depends on.

ADR-0008 was then genuinely superseded by ADR-0021 on 2026-09-11, this time by the criteria: more than half its Decision Outcome was replaced. Its Changes table records both events, which is the point of keeping one.

**Changes that are not supersessions are logged in a `## Changes` table at the bottom of the record.** As of 2026-09-25, 92 Changes rows sit across 40 records, ADR-RULES included, and every table is the last section of its record. Sixteen records had it above More Information until 2026-09-22 and were moved; the move changed no text.

A record stays under 200 lines, and its Changes table stays under eight rows. Reaching eight rows is itself a supersession trigger: a decision amended eight times is no longer the decision that was made.

## Review

Records 0001 to 0012 were written in Nygard format before the architecture-documentation research pass, then retrofitted to the current format. Their reasoning was not changed in the retrofit; Assumptions and Confirmation sections were added, since neither existed in the original format.

**This index fell fifteen records behind.** It listed through 0029 while the corpus ran to 0044, and eight statuses were reconstructed from session reports rather than from the records. Restored 2026-09-18, then audited by the implementing seat against every record.

Three defects the audit found, all introduced by the reconstruction and all corrected 2026-09-18:

**ADR-0010 was marked "clause reversed by 0038". It is not.** ADR-0038 keeps date ordering and adds views; it reverses nothing. ADR-0010 is the scope floor, so an index suggesting part of it had been overturned was the most consequential wrong cell in the table.

**The preamble contradicted this file's own conventions**, stating that an accepted record is never edited while the sections below describe in-place correction and a Changes table. Corrected to match.

**The Changes-table count was stale**, reading six records dated 2026-09-10 when fifteen rows sit across eleven records.
