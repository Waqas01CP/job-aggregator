---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0012: No email or search-alert ingestion path

## Context and Problem Statement

A prior design proposed a second ingestion path: search-engine alerts delivered to dedicated mailboxes, polled over IMAP, with job links extracted and fed into the pipeline. It included thirty query templates and recommended polling every 30 to 120 seconds.

Search alerts index the open web, so they reach employers outside the source registry. That is the capability the path adds.

Against that, it is a second architecture with its own credentials, failure modes and parsing surface. Alert emails are HTML documents whose structure is outside anyone's control.

Most of the proposed query templates target worldwide-remote postings. Prior measurement found 54 entry-level worldwide-remote AI postings with zero open to Pakistan.

## Decision Drivers

- The source registry is the stated source list.
- Every additional credential is an additional failure mode and an additional secret to manage.
- Measure A's 24-hour bar does not require sub-minute polling.

## Assumptions

- The registry's 53 boards cover enough of the reachable market that open-web reach is not urgent. Based on four exhausted census queries; the residual outside the registry is not quantified.

## Considered Options

- Build the alert and IMAP path into the pipeline.
- No open-web reach at all.
- Alerts delivered to an ordinary inbox and read by hand, outside the pipeline.

## Decision Outcome

Chosen option: "alerts read by hand, outside the pipeline, if wanted at all".

We will not build email ingestion, IMAP polling, or a search-alert path into the pipeline. The source registry is the source list. If reach beyond the registry is wanted later, it will be satisfied by alerts read by hand, outside the codebase.

### Consequences

Employers not in the registry are not covered by the pipeline. Extending coverage means adding boards to the registry, which is the intended mechanism.

No mailbox credentials exist in the system. The secret surface stays at the repository token and the Airtable token.

No email parsing code exists, so no maintenance burden from changes to alert email structure.

The registry becomes the single point at which coverage is defined, making coverage auditable by counting boards.

### Confirmation

If the operator finds a suitable role through a channel outside the registry, the employer's board is added to the registry. A pattern of such finds would falsify the coverage assumption above.

## Pros and Cons of the Options

## More Information
