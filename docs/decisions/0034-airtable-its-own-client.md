---
status: accepted
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0034: Airtable gets its own client, as a scoped exception

## Context and Problem Statement

CLAUDE.md says: "All fetch behaviour lives in one shared HTTP module. Retry, backoff, budget counting, circuit breaking. An adapter parses and nothing else. Copying retry logic into an adapter is the specific failure this rule prevents."

That rule was written about fetching job boards, and it has held. Eleven boards across three platforms share one module, and no adapter carries retry logic.

The Airtable writer does not fit it. Every dimension differs:

| | Board fetching | Airtable writing |
|---|---|---|
| Verb | GET | POST and PATCH with a JSON body |
| Authentication | none | bearer token, a repository secret |
| Budget | ADR-0028's per-run request ceiling | roughly 33 calls a day, a separate monthly allowance |
| Rate limit | politeness, self-imposed | 5 requests per second per base, enforced |
| On limit | back off and retry | HTTP 429 then a required 30-second wait |
| On failure | drop the board, log a zero, continue | the row is not displayed, and the run's output is wrong |

Forcing both through one module means that module grows two auth paths, two budget counters, two rate-limit policies and two failure semantics, while the thing it was built to prevent, an adapter carrying its own retry logic, is not at issue here at all.

## Decision Drivers

- The rule's purpose is that retry, backoff and breaker logic exist once. That purpose can be served without one module owning every HTTP verb.
- A module that serves two callers with nothing in common becomes the place every change lands.
- The writer and the weekly sweep are blocked until this is settled.
- An exception that is not written down becomes a precedent nobody can bound.

## Assumptions

- Airtable's documented limits are as stated: 5 requests per second per base, HTTP 429 then 30 seconds, and a monthly call allowance. **Sourced** from Airtable's API documentation, not exercised, because nothing has written to the base yet.
- The pipeline's write volume stays far under the allowance. **Measured** indirectly: 24 filtered rows in two runs, batched ten per call, against roughly 33 calls a day.

## Considered Options

- Extend the shared module with authenticated writes and a second budget.
- Give Airtable its own client, sharing nothing.
- Give Airtable its own client, with retry, backoff and breaking as shared utilities both import.

## Decision Outcome

Chosen option: "its own client, with retry, backoff and breaking as shared utilities".

**Airtable gets its own client module.** It owns the token, the write verbs, the 429 and its 30-second wait, and its own call budget, which is counted per month rather than per run.

**Retry, backoff and circuit breaking become shared utilities that both the fetch module and the Airtable client import.** That is what CLAUDE.md's rule is actually protecting, and it is preserved exactly. What is not preserved is the incidental claim that one module owns all HTTP.

**This is a scoped exception, and the scope is the verb.** Fetching a job board goes through the shared fetch module, always, with no exceptions. Writing to a display service goes through that service's own client. A second display service, if one ever existed, would follow this record rather than extend the fetch module.

**CLAUDE.md is amended to say so**, because a rule with an undocumented exception is worse than either the rule or the exception.

### Consequences

The writer and the weekly outcome sweep are unblocked.

Retry and backoff move out of the fetch module into a shared utility, which is a refactor of a component eleven boards depend on. It is behaviour-preserving and covered by the existing HTTP tests, and it must be proved by mutation rather than assumed.

Two budgets exist with different units: requests per run for fetching, calls per month for Airtable. The run log must report both, or one of them goes unmeasured, which is how ADR-0028's ceiling came to be a guess.

A failure to write to Airtable is not a failure to fetch. The run must distinguish them, and exit 1's two causes already carry that distinction.

### Confirmation

Grep the Airtable client for any import of the fetch module's request function, and the fetch module for any mention of a token or a write verb. Either is a violation.

The shared utilities are proved by mutation: break the backoff calculation once, and both the fetch module's tests and the Airtable client's tests must fail. If only one fails, the utility is not actually shared and the duplication this record was written to prevent has already happened.

## Pros and Cons of the Options

### Extend the shared module

Good, because CLAUDE.md's sentence stays literally true.
Bad, because it produces one module with two auth schemes, two budgets, two rate limits and two failure semantics, which is the god-module the original rule was itself written against.

### Its own client sharing nothing

Good, because it is the smallest change and the two are genuinely different.
Bad, because retry and backoff would then exist twice, which is exactly the failure CLAUDE.md names.

## More Information

Answers question A of the 2026-09-17 architecture brief.

ADR-0035 decides how the writer avoids duplicates. ADR-0004 remains the record of what the display layer is for.

CLAUDE.md carries the amended rule and points here.
