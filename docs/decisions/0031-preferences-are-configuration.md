---
status: accepted
topic: filtering
description: The title pool, seniority list, role families and location targets are versioned configuration, and no module hard-codes a preference.
date: 2026-09-17
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0031: Personal preferences are configuration, not code

## Context and Problem Statement

The pipeline encodes one person's preferences in several places: which job titles interest him, which seniority words rule a role out, which role families he cares about in which order, and in future which locations he can take.

None of these is a fact about job boards. All of them are facts about one operator at one moment. His seniority preference inverts the day he has more experience. His title pool widens when he learns a new term is in use. A location rule appears the day he is willing to relocate.

Two failure modes follow if they live in code. The preference becomes invisible, so nobody can see what the system believes without reading a module. And the system becomes personal in a way that cannot be undone, so the same pipeline cannot be pointed at anyone else without editing source.

The title pool is already a versioned file with a change log and a measurement section. The seniority list followed it. This record states the rule the two of them are instances of.

## Decision Drivers

- A preference that changes must be changeable without touching code or tests.
- What the system believes about the operator should be readable in one place by the operator.
- The difference between a preference and a rule is what separates this project from relevance scoring, and it needs to be structural rather than remembered.
- The pipeline should be convertible to a general aggregator by swapping configuration.

## Assumptions

- Preferences change more often than mechanism. **Measured** during development: four title-pool versions in seven days, against no change to the matching mechanism after ADR-0021.
- Every current preference is expressible as a list of terms or words. **Measured** for the title pool, the seniority list and the family order. **Not established** for location, which ADR-0001's Confirmation names and which no code implements; the stored location text varies in form between boards.

## Considered Options

- Preferences in code, changed by editing modules.
- Preferences in configuration files, loaded at run time.
- Preferences in configuration, with the loader validating shape.

## Decision Outcome

Chosen option: "preferences in configuration, with the loader validating shape".

**No module hard-codes a preference.** The title pool, the seniority word list, the role families and any future location targets are versioned files under `docs/reference/` or `config/`, each with a dated change log, and each loaded at run time by a function that fails loudly rather than falling back to a default.

**A preference file carries its own audit trail**: what changed, when, why, and what it measured against real postings when that was checked. The title pool is the shape to copy.

**This is why the seniority rule is not a blocklist in ADR-0021's sense.** ADR-0021 rejected a blocklist because it was "the only place where a machine would delete a row on a judgement rather than on a named match". The seniority list is not a machine judgement about role categories. It is the operator's own declaration about his own level, in a file he owns, applied by a rule that names the word it matched. ADR-0032 records that decision; this record supplies the frame that makes it consistent rather than an exception.

**The test of the rule:** point the pipeline at a different person by replacing configuration files and changing no source.

### Consequences

Every preference is visible in one place and diffable in history, so "why did this row appear" is answerable from the file rather than from a module.

Adding a preference means adding a file and a loader, which is more work than adding a constant, and that friction is deliberate.

Tests must construct preference data rather than relying on the shipped files, or a pool change breaks unrelated tests. This is already true of the filter tests, which build their own pools.

The general-aggregator claim is not free: it holds only while no module reads a preference directly. A single hard-coded term would quietly end it, which is what the Confirmation checks.

### Confirmation

Grep the source tree for any term from the title pool, any word from the seniority list, and any family name. Every hit must be in a loader, a test fixture, or a comment naming the file. A hit inside a rule is a violation of this record.

The check is proved by giving it the case built to defeat it: temporarily hard-code one pool term inside `src/filters.py` and confirm the grep finds it.

## Pros and Cons of the Options

### Preferences in code

Good, because it is the least machinery and the values are typed.
Bad, because changing what the operator wants becomes a code change with tests, and the system's beliefs about him are spread across modules.

### Configuration without shape validation

Good, because it is simpler.
Bad, because a malformed preference file then degrades silently into a pool that matches nothing, which looks exactly like a quiet market.

## More Information

The title pool (ADR-0016, ADR-0021) and the seniority list are the two existing instances. ADR-0032 records the seniority rule itself.

This record does not decide any preference's contents. Every value in these files is the operator's, per the project's protocol.
