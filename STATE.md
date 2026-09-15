---
type: state
description: What exists right now, what is blocked and on whom, and where the proof is. Ground truth, not memory.
status: current
---

# STATE

**Last verified against `main` at `ed0c4f4`, 2026-09-11.**

This file is ground truth. If a row says DONE, it is done. If you believe otherwise, read the file the pointer names before claiming a conflict. Memory is not evidence.

Organised by task, not by session, because logs are chronological and one task spans many of them.

## How to read a row

`STATUS` is DONE, PARTIAL or PENDING. A row reads DONE only when the thing is built, never when it has merely been examined.

Every row carries `[VERIFIED]` or `[BELIEVED]`. Verified means exercised and observed. Believed means reasoned from the code but not run. **Unmarked means believed.** The default points at the weak set on purpose.

`Proof` is a commit, a decision record, or a log filename. Never a file path; paths move.

## How to maintain it

Update the affected rows **in the same commit as the work**, never in a separate pass. A commit that completes a task without updating its row is incomplete.

Never delete a DONE row. Supersede it with a new row if the work is redone.

Update the verified-against line whenever you touch this file.

## Headline

**Nothing is built. No pipeline code exists.** Everything below is documentation, tooling for documentation, and decisions. The first line of pipeline code has not been written.

The project is blocked on one thing that is not mine: the endpoint feasibility spike.

---

## Documentation

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Architecture document, arc42, twelve sections | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture-2.0.md` |
| Rejected architecture bannered, not deleted | DONE | [VERIFIED] | 2026-09-10 | `docs/architecture.md` |
| Decision records, MADR 4.0.0 plus Assumptions | DONE | [VERIFIED] | 2026-09-11 | 24 records in `docs/decisions/` |
| Research records with source trails | DONE | [VERIFIED] | 2026-09-11 | 4 passes in `docs/research/` |
| Title pool, 50 terms with matching rules | DONE | [VERIFIED] | 2026-09-11 | `docs/reference/title-pool.md`, ADR-0021 |
| README, licence and scope statement | DONE | [VERIFIED] | 2026-09-11 | `README.md`, `LICENSE` |
| Instruction file with reading and authority order | DONE | [VERIFIED] | 2026-09-11 | `CLAUDE.md`, ADR-0022, ADR-0023 |
| This file | DONE | [VERIFIED] | 2026-09-11 | ADR-0023 |
| Log index and directory | PENDING | — | — | ADR-0023, ADR-0024 |
| End-state document | PENDING | — | — | Confirmed open in ADR-0023. No prior art exists |

## Tooling

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Map generated from frontmatter | DONE | [VERIFIED] ran, 29 files | 2026-09-11 | `tools/generate_map.py` |
| Pre-commit hook, four gates | DONE | [VERIFIED] all four proven to fire | 2026-09-11 | `.githooks/pre-commit` |
| Map gate Python resolution fixed | DONE | [VERIFIED] fired correctly after fix | 2026-09-11 | commit `ed0c4f4` |
| Line endings forced to LF | DONE | [BELIEVED] renormalise found nothing | 2026-09-11 | `.gitattributes` |
| State file staleness gate | PENDING | — | — | Named as a gap in ADR-0023 |

## Pipeline

**Nothing in this section is started.**

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Endpoint feasibility spike, Greenhouse, Lever, Himalayas | PENDING | — | — | Brief written, not run |
| Shared HTTP module | PENDING | — | — | ADR-0009 |
| Greenhouse adapter | PENDING | — | — | ADR-0009 |
| Lever adapter | PENDING | — | — | ADR-0009 |
| Himalayas adapter, conditional | PENDING | — | — | ADR-0019 |
| Normaliser | PENDING | — | — | ADR-0019 |
| Deduplicator | PENDING | — | — | ADR-0001 |
| Filter chain | PENDING | — | — | ADR-0005, ADR-0021 |
| Raw layer writer, orphan data branch | PENDING | — | — | ADR-0002, ADR-0003, ADR-0020 |
| Filtered layer writer | PENDING | — | — | ADR-0013 |
| Airtable base and schema | PENDING | — | — | Deferred until real output exists |
| Airtable writer | PENDING | — | — | ADR-0004 |
| Scheduled workflow | PENDING | — | — | ADR-0006 |
| Weekly outcome sweep | PENDING | — | — | ADR-0014 |
| Contract check | PENDING | — | — | ADR-0018 |

## Blocked, and on whom

**The spike is blocked on the operator.** The brief is written. It has not been run. Nothing downstream of it should be built first, because it tests the two assumptions ADR-0006 and ADR-0007 rest on, and a bad result changes records before any code exists.

**The blocklist is no longer needed.** ADR-0021 removed it. Previously blocked on the operator; now closed.

**The Airtable base is blocked on real output**, by the operator's decision, not by an omission.

**Rozee.pk is unblocked and undecided.** robots.txt permits the job paths, the terms carry no automated-access clause, and a sitemap index publishes job URLs daily with the title in the slug. No decision record exists yet.

## Known unverified

Two assumptions carry accepted decisions and neither has been tested. Both are recorded as Assumptions in their records, and the spike is what settles them.

**Boards publish to their APIs at the moment a posting goes live.** ADR-0006's cadence rests on it. Not measured for any platform.

**Many ATS platforms expose no publication date.** ADR-0007 asserts it from a registry's notes. No endpoint has been requested. ADR-0015's Measure A, the project's only binding success measure, is uncomputable without one.
