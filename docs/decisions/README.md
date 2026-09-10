# Architecture Decision Records

Every architecture decision made on this project, one file per decision, with the reasoning that produced it and the conditions that would show it was wrong.

Format: MADR 4.0.0 with two documented deviations. Numbered in the order concluded.

The deviations: an added **Assumptions** section, taken from Tyree and Akerman, holding every belief the decision rests on that is not established, so unmeasured numbers are visible and re-checkable rather than buried in prose. And three authoring rules carried forward from Nygard, which MADR does not specify: Context is written value-neutral with the tensions named, Decision Outcome is written in active voice as a rule, and Consequences are always filled including the negative ones.

Records are written at the moment a decision concludes. An accepted record is never edited; a change is a new record that supersedes it, with links in both directions.

| ID | Title | Status |
|----|-------|--------|
| 0001 | Two-layer store, raw and filtered | Accepted |
| 0002 | Raw layer on a git data branch, not a hosted database | Accepted |
| 0003 | Append deltas, not snapshots | Accepted |
| 0004 | Airtable as the filtered display layer | Superseded by 0014 |
| 0005 | Fetch complete board output, filter locally | Accepted |
| 0006 | Twice-daily fetch cadence | Accepted |
| 0007 | Recency is a view, not an ingest filter | Accepted |
| 0008 | Title matching by allowlist, blocklist, and unmatched flag | Superseded by 0016 |
| 0009 | Vertical slice first, adapters incremental | Accepted |
| 0010 | No relevance scoring, ranking, or model-based screening | Accepted |
| 0011 | Public repository, metadata only on the data branch | Accepted |
| 0012 | No email or search-alert ingestion path | Accepted |
| 0013 | Three layers, filtered set persisted independently of the display | Accepted |
| 0014 | Weekly status sweep, with a four-status outcome taxonomy | Accepted |
| 0015 | Two measures, and the archive protocol | Accepted |
| 0016 | Title-only matching against a versioned title pool | Accepted |
| 0017 | Sanitised cassettes as adapter test fixtures | Accepted |
| 0018 | Scheduled contract check against live boards | Accepted |

## Pending

Decisions identified but not concluded.

- Platform adapter order after the vertical slice. Blocked on feasibility spikes for Ashby, Workable, SmartRecruiters, JazzHR and Manatal.
- Reuse boundary against the LinkedIn pipeline in fyp-career-guidance: which components are adopted, which are deliberately not.
- Description matching, deferred by ADR-0016 until field coverage per platform is known.
- Which skills the project needs, and whether the session log becomes a skill with dynamic context injection.
- Whether an AGENTS.md symlink is added for Antigravity. Claude Code reads CLAUDE.md only, with no fallback, so CLAUDE.md is the real file either way.

## Reading these records

Several records cite files from the operator's LinkedIn collection pipeline, which lives in a private repository. Those citations record where a pattern came from and are not links a reader can follow. They are kept because the provenance is what makes the reasoning checkable.

A record's factual error may be corrected in place, marked as a correction with its date, as in ADR-0005. A change of decision may not: that is a new record superseding the old one.

## Review

Records 0001 to 0012 were written in Nygard format before the architecture-documentation research pass, then retrofitted to the current format. Their reasoning was not changed in the retrofit; Assumptions and Confirmation sections were added, since neither existed in the original format.

To be re-examined once the implementation-flow research pass is complete.
