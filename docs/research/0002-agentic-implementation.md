---
type: research
description: Pass 0002. Agentic implementation flow. Thinnest of the three passes; read the sourcing caveat before relying on it.
status: current
---

# Research 0002: Agentic implementation flow

Run 2026-09-10. Findings reflect that date.

**Question asked.** How should implementation work be run through an AI execution seat? Instruction files, skills, subagents, verification gates, briefs, and testing against external services.

## Read this before the findings

**This is the weakest of the three passes and was presented at higher confidence than it deserved.** It rests substantially on one first-party source: Anthropic's own documentation for its own product. That is the right source for how Claude Code behaves. It is not sufficient to establish how agentic implementation should work generally, and the pass generalised from it anyway.

Named gaps, so a later reader does not have to rediscover them:

**Two community handbooks were cited having read only their search snippets, not the handbooks.** That violates the operator's rule against writing about a source that has not been opened, and it happened in the same session that rule was written down. Any claim in this pass attributed to a "community handbook" should be treated as unverified.

**No empirical work exists.** Pass 0001 had a study with a stated method. This pass has none, and none was found.

**Antigravity is uncovered.** Every source located was vendor marketing or secondhand commentary. A further pass would not create primary sources.

**Testing-level taxonomy was never searched.** The operator raised component, integration and system; the contract-drift finding settled the actual question before the taxonomy was checked.

## Findings

**Context is the governing constraint, not capability.** The documentation states it directly: the window fills fast and performance degrades as it fills. Almost every named failure pattern is a context failure. The prescribed fixes are blunt: clear between unrelated tasks, and after two failed corrections clear and rewrite rather than correcting a third time.

**Verification is the first-listed practice.** The named failure is the trust-then-verify gap: a plausible implementation that does not handle edge cases. Four gate strengths, increasing in setup cost: in the prompt, as a goal condition, as a stop hook, as a review subagent. One discipline: show the evidence, do not assert success.

**A reviewer asked to find gaps will report some even when the work is sound**, producing extra abstraction and tests for cases that cannot happen. Reviewers must be told to flag only gaps affecting correctness or stated requirements. On a project with a scope floor this matters: a reviewer will otherwise propose the banned feature as a robustness improvement.

**Claude Code reads CLAUDE.md, not AGENTS.md. There is no automatic fallback.** Where a repository already uses AGENTS.md, the documented pattern is a CLAUDE.md that imports it.

**Memory files are context, not enforcement.** To block an action regardless of what the model decides, use a hook. Any rule that must hold every time belongs in a hook, not in prose.

**Skills are a context mechanism, not a routing table.** Progressive disclosure: only the description sits in context, capped at 1,536 characters; the body loads on invocation. The trigger for creating one: when the same procedure keeps being pasted into chat, or when a section of the instruction file has grown into a procedure rather than a fact.

**Dynamic context injection is the most valuable feature found.** A command line runs before the skill content reaches the model and its output is inlined, which makes a skill's content derived from reality rather than transcribed from memory. Applied to session logs, it attacks log accuracy at the mechanism rather than by trying harder.

**`context: fork` runs a skill in a subagent.** This is the mechanised form of a dedicated review or test session: a fresh context is not biased toward code it just wrote.

**Skill context cost is measurable** via a diagnostic that reports each skill's cost and invocation count, so whether skills bloat context is a number rather than an opinion.

**Recorded fixtures (the VCR pattern) for testing adapters.** Capture a live response once, replay it in tests. Offline, deterministic, real response shapes. Censor credentials before commit; set an expiry so stale recordings are flagged.

**Consumer-driven contract testing cannot help with a third-party API.** Pact and its relatives require the provider to adopt the framework. For a consumed API the applicable pattern is observed contract verification: infer the shape from real responses, fingerprint it, compare on a schedule. The failure modes it catches all fail silently: a field returning null rather than disappearing, a silent type change, a new enum value.

**Every drift-monitoring product found was paid SaaS**, from roughly $50 to $2,500 a month, and most operate on published OpenAPI specifications, which ATS boards do not provide.

## An error corrected inside this pass

The skills verdict was reversed twice. First conclusion: standards belong in skills rather than the instruction file, which was right. Second conclusion, on the operator's existing routing document: no skills needed, because that document already routes by task. That was an analogy rather than evidence, and the wrong analogy. A routing document is instructions an agent must choose to follow; a skill is loaded by the runtime. Different layers.

The operator pushed back on the reasoning rather than the conclusion, which is what surfaced it.

## What the operator's own system contributed, which the research did not

Three verification rules stronger than anything in the sources, taken from his existing working system and carried into the standard:

A check that cannot fail is worse than no check; prove a check by giving it the case built to defeat it; self-report is not a check.

Name the read that would falsify the conclusion, then do that read.

Agreement between sources is not verification. A decision, the document recording it, and the code implementing it can all agree on something structurally impossible.

The research contributed one thing those lacked: mechanism. Hooks are deterministic where instructions are advisory, and the first-party documentation says so outright.

## Sources

| Source | Rating | Used for |
|---|---|---|
| Claude Code best practices documentation, code.claude.com | Primary, first-party, fetched in full | Context constraint, verification gates, planning, instruction-file contents |
| Claude Code skills documentation, code.claude.com | Primary, first-party, fetched in full | Progressive disclosure, invocation control, dynamic context injection, `context: fork`, lifecycle |
| Claude Code memory documentation, code.claude.com | Primary, first-party, via search | That CLAUDE.md is read and AGENTS.md is not, with no fallback; that memory is context and hooks are enforcement |
| agents.md and Agentic AI Foundation material | Secondary, corroborated across several sources | AGENTS.md as a cross-tool convention |
| VCR, pytest-recording documentation | Primary for the tool | The cassette pattern, credential censoring |
| Pact and contract-testing sources | Mixed, corroborated across three | That consumer-driven contract testing requires provider participation |
| EasyPost cassette guide | **Vendor** | Cassette expiry. Corroborated elsewhere |
| Drift-monitoring product pages | **Vendor** | Pricing only |
| Community handbooks on Claude Code | **Unverified, snippets only** | Should not have been cited. See the caveat above |
| Antigravity material | **Vendor marketing only** | Nothing was taken |

## Outputs

ADR-0017, sanitised cassettes as adapter test fixtures. ADR-0018, scheduled contract check against live boards. The operator's cross-project standard on agentic implementation, which opens by stating it is thinly sourced.
