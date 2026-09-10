---
status: accepted
date: 2026-09-09
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0011: Public repository, metadata only on the data branch

## Context and Problem Statement

The repository is public. GitHub Actions minutes are free on public repositories, and the operator intends to share the project.

Two components have different exposure profiles. Code that polls public ATS board endpoints is unremarkable; those endpoints exist to be read by third parties and many public repositories consume them. Republishing employer-authored job descriptions verbatim in a public repository is a different act, and it is what the superseded architecture document in this repository already prohibited when it barred committing raw payloads.

The realistic risk is not litigation but a hosting provider honouring a notice and removing the repository, which would destroy the artefact the public visibility exists to create.

## Decision Drivers

- Free Actions minutes require a public repository.
- The audit purpose of ADR-0001 must survive whatever restriction is applied.
- Exit cost: a free hosted service should hold a projection, never an authority.

## Assumptions

- No filter depends on description text, so metadata alone preserves the audit. True as of ADR-0016; would change if description matching is added.
- Job posting metadata as factual record-keeping carries materially less exposure than verbatim description text. This is a judgement, not legal advice.

## Considered Options

- Private repository, everything stored.
- Public repository with a takedown policy document, everything stored.
- Public repository, metadata only on the data branch, descriptions in the private display layer.

## Decision Outcome

Chosen option: "public repository, metadata only on the data branch".

We will make the repository public. We will store on the data branch only employer, title, location, ATS platform, publication date, first-seen date, stated experience, canonical URL, and the filter verdict with its reason. We will write job description text, including snippets, only to the Airtable display layer. We will state in the README what the repository stores, what it does not, and a contact address, rather than adding a separate takedown document.

### Consequences

The audit purpose of ADR-0001 is fully preserved, because no filter depends on description text.

There is nothing in the public repository to take down, so the artefact is durable.

Description snippets exist only in Airtable. If that base is lost, snippets must be refetched rather than restored.

A pre-commit guard rejecting raw payload files and oversized files is required if any adapter later parses HTML, because that is how description text could reach the repository accidentally.

Adding description matching later would require revisiting this decision.

### Confirmation

Inspect the data branch after the first month and confirm no file contains description text. The pre-commit guard, once present, is the standing check.

## Pros and Cons of the Options

## More Information
