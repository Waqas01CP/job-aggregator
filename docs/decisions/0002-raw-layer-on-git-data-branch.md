---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0002: Raw layer on a git data branch, not a hosted database

## Context and Problem Statement

ADR-0001 requires a raw layer holding every fetched posting permanently. Three storage media were available, each with different limits, failure behaviour and operational surface.

Airtable's free plan caps a base at 1,000 records and refuses new records at the ceiling. Supabase's free tier gives 500 MB per project with no backups, and pauses projects after seven days of inactivity under a policy tightened in February 2026. A git data branch has no ceiling and no vendor, but no query language.

A working implementation of the data-branch pattern already exists in the operator's LinkedIn pipeline, where a scheduled workflow checks out a data branch, runs collection, and commits the result back under the Actions bot identity.

## Decision Drivers

- Cost constraint: free by default; paid only where free is impossible, at the minimum that does the job.
- The raw layer grows without bound, so a hard record ceiling disqualifies a candidate outright.
- Audit is the purpose of the layer, so history matters more than query ergonomics.
- Operational risk is lowest where a pattern is already proven in the operator's hands.

## Assumptions

- The audit will be run rarely, so the absence of SQL costs little. Not measured; based on the layer's stated purpose.
- Repository size stays manageable under the delta strategy of ADR-0003.

## Considered Options

- Airtable as the raw store.
- Supabase Postgres as the raw store.
- A dedicated git data branch in the project repository.

## Decision Outcome

Chosen option: "a dedicated git data branch in the project repository".

We will write the raw layer to a data branch in the job-aggregator repository from the scheduled run. We will not hold raw postings in any hosted service.

### Consequences

No vendor, no credentials beyond the repository token, no free-tier ceiling, and no inactivity pause to defend against.

Audit is git history. The state of the raw layer at any past date is recoverable without a separate backup mechanism.

There is no query language. Auditing requires a script over the data files. `verify_linkedin_data.py` in fyp-career-guidance establishes that this is workable and produces better output than ad-hoc queries.

Repository size grows monotonically, bounded by ADR-0003.

Airtable's 1,000-record ceiling no longer threatens the raw layer, only the display.

### Confirmation

After the first month of live running, measure actual repository growth on the data branch and compare against the estimate in ADR-0003. A figure materially above estimate falsifies the sizing, not the medium.

## Pros and Cons of the Options

### Airtable

Good, because the display layer is there already.
Bad, because 1,000 records per base is reached on roughly the first full run.

### Supabase

Good, because it offers SQL for the audit.
Bad, because it adds credentials, a vendor, and a seven-day inactivity pause that fires during any deliberate stop.
Bad, because the free tier has no backups, so a backup mechanism would be needed anyway.

### Git data branch

Good, because it is free without limit, versioned by construction, and already proven by the operator.
Bad, because auditing requires a script rather than a query.

## More Information

If SQL ergonomics later prove necessary, a database can be added as a downstream consumer of the data branch without changing the write path.
