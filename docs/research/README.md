# Research

Dated snapshots of what was found and when. Numbered by the order the pass was run, so a later reader knows what was known at each point.

A research record is never edited to reflect a later finding. A new pass gets a new number and supersedes the earlier one, with links both directions, exactly as decision records do.

**Findings go stale. The record does not.** A pass reporting an endpoint as free in September 2026 stays a true record of September 2026 even after that endpoint moves behind a paywall. Check the pass date before relying on any figure in one.

## Passes

| # | Pass | Date | Output | Status |
|---|------|------|--------|--------|
| 0001 | Architecture documentation | 2026-09-09 | `0001-architecture-documentation.md`, plus the operator's cross-project standards on arc42, C4, Diataxis and the MADR 4.0.0 record format used in `docs/decisions/`. | complete |
| 0002 | Agentic implementation flow | 2026-09-10 | `0002-agentic-implementation.md`, plus the operator's cross-project standard on instruction files, skills, subagents, verification gates and briefs, plus ADR-0017 and ADR-0018. | complete, **thinly sourced, read its caveat first** |
| 0003 | Job source survey | 2026-09-10 | `0003-job-source-survey.md`, plus ADR-0019 and ADR-0020. | complete |
| 0004 | Project context documentation | 2026-09-11 | `0004-project-context-documentation.md`, plus ADR-0022, ADR-0023 and ADR-0024. Corrects pass 0002 on instruction-file length. | complete |

Passes 0001 and 0002 also produced cross-project standards, which live outside this repository because their findings apply to every project rather than this one. The records here carry the evidence and the source ratings; the standards carry the conclusions.

**Every pass records its own sources with a quality rating**, and records where a source turned out to be unreliable. Three passes contain an error found and corrected mid-pass. Those are kept deliberately: a research record that reports only what survived is not a record of the research.

**Pass 0004 found its strongest source was not published practice but the operator's own prior repository.** Where that happens, the record says so plainly rather than dressing a port up as a discovery.

## Residuals, permanent rather than pending

**No primary material exists on Antigravity.** Everything found was vendor marketing or secondhand commentary. A further pass would not create primary sources.

**No empirical study of agentic coding workflows was found.** Pass 0002 therefore rests substantially on one vendor's documentation of its own product, and says so at the top of its output.

## What a pass does not cover

Verification. Reading a robots.txt, confirming a field name against a live payload, and running a feasibility spike are requests rather than searches, and belong in the work itself.
