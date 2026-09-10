---
type: research
description: Pass 0001. Architecture documentation formats. Produced the arc42 structure, C4 in Mermaid, and the MADR 4.0.0 record format with two deviations.
status: current
---

# Research 0001: Architecture documentation

Run 2026-09-09. Findings reflect that date.

**Question asked.** What structure should a project's architecture documentation take, what record format should decisions use, and how do the candidate conventions compose?

**Why it exists as a record.** The findings became `docs/architecture-2.0.md`, the format used across `docs/decisions/`, and the operator's cross-project standards. Without this file, none of those carry their evidence, and nobody can later ask whether a conclusion rested on something weak.

## Findings

**arc42 for the architecture document.** Twelve sections, technology agnostic, free, in use since 2005. Every section optional and tailorable. Explicitly targets docs-as-code: plain text in git, next to the code, reviewed through pull requests. Its own practitioners warn that filling all twelve sections on a project that does not need them produces content duplication.

**C4 for diagrams, mapped into arc42.** The C4 FAQ confirms the mapping directly: context into arc42 section 3, container into section 5 level 1, component into section 5 level 2. Level 4, code diagrams, is not worth maintaining by hand.

**Mermaid rather than PlantUML**, contradicting the AsciiDoc and docToolchain route arc42 itself promotes. Rationale: GitHub renders Mermaid inline with no toolchain. Correct for a repository where the diagram should render where someone is already reading; wrong for a team publishing a documentation site.

**Diataxis for splitting documents by function.** Four types, split by what the reader is doing rather than by topic. The failure it names is cramming several intentions into one file. Extended the operator's existing layering rule with a cut he did not have: within documents, explanation and reference must not share a file.

**MADR 4.0.0 as the record format**, released 17 September 2024. It adds four things Nygard lacks: Decision Drivers, Considered Options as a required list, Pros and Cons of the Options, and Confirmation. Confirmation is the one that earned the switch: Nygard has no field for how you would know a decision was wrong.

**Three Nygard authoring rules carried forward**, none of which MADR specifies. Context written value-neutral with tensions named. Decision Outcome in active voice as a rule. Consequences always filled, including negative ones.

**One added section from Tyree and Akerman: Assumptions.** Defined there as the underlying assumptions in the environment in which the decision is made. Neither MADR nor Nygard has it. MADR's Decision Drivers is the nearest thing, but drivers are forces you respond to, not beliefs you rely on.

**Retroactive records lose most of their value**, because context, alternatives and consequences get reconstructed rather than committed to. This supports the operator's existing standing rule rather than introducing one.

## Sources

| Source | Rating | Used for |
|---|---|---|
| MADR 4.0.0 specification, adr.github.io/madr | Primary, fetched in full | The template verbatim, which sections are mandatory, the 4.0.0 changes including Confirmation |
| Nygard, "Documenting Architecture Decisions", cognitect.com, 2011 | Primary, fetched | Value-neutral context, active voice, all consequences mandatory, the never-edit rule |
| arc42.org overview and documentation pages | Primary, fetched | The twelve sections, tailorability, docs-as-code stance |
| c4model.com FAQ | Primary, via search | The arc42 mapping |
| Kopp, Armbruster, Zimmermann, "Markdown Architectural Decision Records", ZEUS 2018 | Primary, via search | That MADR has peer-reviewed backing |
| Tyree and Akerman, "Architecture Decisions: Demystifying Architecture", IEEE Software, 2005 | Primary paper, **accessed via a summary rather than the paper itself** | The Assumptions field and its definition |
| diataxis.fr | Primary, via search | The four documentation types and the split-by-function rule |
| Empirical comparison of five ADR templates, DESMET feature analysis, arXiv, April 2026 | Empirical | That Nygard supports concise documentation and MADR supports structural detail |
| ozimmer.ch ADR primer | Practitioner, academic author | Corroboration on MADR; Zimmermann co-authored both MADR and Y-statements |

### Sources used and later found unreliable

| Source | Rating | What went wrong |
|---|---|---|
| catio.tech | **Vendor** | Sells an architecture-decision product, so has a commercial interest in claiming static records strain |
| docsio.co | **Vendor** | Sells documentation tooling |
| scribelet.app | **Vendor** | Sells an AI notebook |
| hidekazu-konishi.com, prompt-architects.com | Unattributable blogs | No verifiable provenance |

**An error was made and corrected inside this pass.** The initial recommendation was to stay on Nygard rather than adopt MADR, on the grounds that MADR imposes bureaucratic overhead. That claim traced entirely to the vendor sources above. Reading the MADR specification directly showed the opposite: nearly every element is marked optional with an inline instruction to remove what is not needed, and MADR ships a minimal template variant containing only mandatory sections.

The recommendation was reversed. This is the reason the source-quality rating in the standards index exists, and the reason a claim resting only on vendor content is marked unverified.

## Residual

Y-statements, arc42's own decision template, and OpenEdX OEP-19 were assessed and rejected. Nothing from any of them was taken; each was either covered by MADR already or too heavy for the scale.
