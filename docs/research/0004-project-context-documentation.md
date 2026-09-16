---
type: research
description: Pass 0004. Project context documentation for humans and AI agents. Corrects pass 0002 on CLAUDE.md length; finds the strongest source was the operator's own prior repository.
status: current
---

# Research 0004: Project context documentation

Run 2026-09-11. Findings reflect that date.

**Question asked.** What artifacts should a repository carry so that a human or a fresh AI session can understand the project without reading every file? Specifically: current state, trajectory, history, and onboarding.

**Headline.** The strongest source in this pass was not a study or a specification. It was the operator's own prior repository, which had already solved most of the problem, in several places better than the published practice.

## Corrections to earlier passes

**Pass 0002 was wrong about CLAUDE.md length.** It recorded the 200-line figure as community consensus rather than vendor guidance. Anthropic's memory documentation targets **under 200 lines per file, because longer files consume more context and reduce adherence.** Corroborated across five independent sources citing the docs. The operator identified the error.

Two corrections in the same area, both of which would have produced bad recommendations:

**`@imports` do not reduce context.** Imported files are expanded and loaded at launch. Splitting a long instruction file into imports buys readability and no budget at all.

**`.claude/rules/*.md` with a `paths` frontmatter glob is the mechanism that does.** Those rules load only when the agent touches matching files. This is what imports are widely and wrongly believed to do.

**Consequence for this project:** a 160-line instruction file is within target. The work is a content audit against the removal test, not a cut to hit a number. `/doctor` (Claude Code v2.1.206+) proposes trims, cutting what is derivable from the codebase.

## Auto Memory: shadow state, running by default

Claude Code writes its own notes to `~/.claude/projects/<dir>/memory/`, **outside the repository**. Enabled by default since v2.1.59.

Not git-tracked, not reviewable in a pull request, not versioned with the code, not portable to other agents. `MEMORY.md` caps at 200 lines or 25 KB and **silently truncates**. It cannot currently be disabled; there is an open request for a switch. Consolidation fires only after roughly 24 hours *and* at least five new sessions.

It is keyed by **working directory, not repository root**. One reported case had a session for project A receive facts about projects B, C and D in its system prompt, and use a business-legal fact from B while analysing an unrelated personal project.

**It does not replace an in-repo state artifact, and it is an argument for building one.** It is a second place where facts live, ungated, untracked, occasionally contaminated across projects. Worth knowing it is running.

## The studies: four, not one

Pass 0004's first draft rested a conclusion on a single study. There are at least four.

**Agent READMEs**, arXiv 2511.12884, MSR 2026. 2,303 context files from 1,925 repositories. Context files are **not static documentation but complex, difficult-to-read artifacts that evolve like configuration code through frequent, small additions.** Developers put test procedures in 76%, implementation details 70%, architecture 68%. Security and performance under 15%.

**ETH Zurich / LogicStar**, arXiv 2602.11988, ICLR 2026 workshop. Context files did not generally improve task success and cost over 20% more tokens. Repository overviews specifically were not helpful. Agents were "too obedient": a tool named in a context file was used ~160x more often, even when counterproductive.

Plus an efficiency study finding curated files reduced runtime and output tokens on focused work, and a fourth on context engineering in open-source software.

**The useful contradiction:** 68% of developers put architecture into context files; the ETH study says overviews do not help. Common practice and effective practice are not the same thing here, and no single study would have shown that.

## The strongest source was the operator's own repository

`fyp-career-guidance`, five months of work. Six files read in full or in part. What follows is what it already solves, and is the reason most of this pass's proposals were withdrawn.

**`SYSTEM_STATE.md`** — task-status ground truth, organised by task rather than by session, because logs are chronological and one task spans many rows. One search, one row, STATUS plus date plus log proof. Maintenance is a same-commit rule, and a session that writes a log without updating it is declared incomplete. It carries a **memory staleness rule** born from a specific incident where a session falsely claimed four completed tasks were pending: the file is ground truth, not memory, and "I remember this was pending" is explicitly not evidence.

It also carries an **evidence-method section** explaining how it was populated and why it did not read all 100 logs individually. A state document that documents its own provenance. Nothing in the published practice does this.

**`STATUS_REGISTER.md`** — in-flight diagnosis and held defects, explicitly distinguished from `SYSTEM_STATE` which holds locked and shipped work. One line per item, `STATUS (date) — description — pointer`, where the pointer is a commit hash, an audit path, or a chat. **Two artifacts split by churn rate**, which this pass's research found argued for in principle and found here already implemented.

**`[VERIFIED]` versus `[BELIEVED]`** — live-exercised versus inspected but not run, with unmarked defaulting to believed "so suspicion stays directed at the believed-but-unverified set." Stronger than the evidence-gate convention the research offered, because the default points at the weak set rather than hiding it.

**`logs/README.md`** — a navigation index with an append-only summary table, read-first enforcement, log routing by lane, a self-healing rule, a reorganisation protocol with a stated trigger of roughly 80 to 100 files at root, and this:

> when you need detail beyond what this README provides, read the most recent relevant log file first. That file references the one before it. Read backwards through the chain only as far as you need, stop when you have enough context.

That is progressive disclosure, and it is the answer to the onboarding problem this pass was convened to solve. The index is thin by rule; the logs are deep; the chain means depth costs nothing until needed.

**The log format itself.** Roughly sixty lines. Every claim carries a file and line number and is tagged verified, meaning grepped and quoted that pass. Per-item verdicts with class labels, honest size and risk estimates per option, a closing "Recommendation (not a decision)", and its own commit status. Not a narrative. An evidence package.

**`WORKING_METHODOLOGY.md`** — explicitly project-agnostic, a way of working rather than facts about a project. Its central stance: aggressive investigation, conservative mutation, with the consequence that the ratio of findings to changes should be high. The depth trigger is not complexity but "this looks fine in isolation, but its correctness depends on an assumption I have not checked." The tension technique: hold producer against consumer, document against code, test against reality, write-time against read-time. On tests: a passing result can itself be evidence of a bug, and mocked-green is the weakest form of green.

Section 1.5 is the one with no counterpart anywhere in the published practice: **verify the model can produce a distinction before designing a mechanism that depends on it.** Evidenced by a controlled probe where "firm" produced less concrete output than "light", inverted, so the graduated-strength layer was dropped before implementation. "A gradient it cannot produce is theatre."

**`CLAUDE_CODE_RULES.md`** — a numbered reading order, a role statement (the session executes and does not decide), hard rules as never-create, never-modify, never-introduce lists, scope discipline, and change discipline stated as do the minimum required.

**`docs/rationale/`** — a category this pass had no slot for. Four levels, system down to algorithm, with a formal specification standard: interface contract, operating instructions, enumerated failure modes, honest known limitations. Not decision records and not logs.

**The authority order**, in `POINT_2`. Six levels of precedence for when documents conflict: current conversation, instruction file, this document, schema contract, system state, everything else as background. **No source in any pass addresses document conflict.** Every multi-file documentation system has this problem.

**Clause-scoped supersession**, in the same file's version header: v3.1 supersedes v3.0 on one topic only, and states that all other decisions stand. The distinction this project derived from first principles for its own record standard, already in practice.

## What this pass got wrong, recorded rather than quietly fixed

**It ruled on the operator's log system without reading it.** Two turns were spent arguing from practitioner blogs that detailed logs rot. The directory listing containing `README.md` and `STATUS_REGISTER.md` had been seen turns earlier and neither was opened. The verdict was wrong: the advice applies to systems with no index and no chain rule, and this one has both.

**It presented three findings as a census.** "Three things that appear in no source" was a count of what happened to be noticed in six files out of a five-month repository, phrased as though exhaustive. The operator corrected it: five months of work will hold more than three, and some of it will only surface when it is needed.

**It proposed inventing artifacts that already existed**, in better form, in a repository it had partially read.

**It asserted a propagation path without checking it, four days after proposing a rule against exactly that.** On 2026-09-15, reviewing the endpoint spike, this chat stated that the fabricated "roughly twenty open roles per board" figure had propagated into ADR-0001, ADR-0003 **and the architecture document**. The implementing seat grepped the working tree and HEAD and found it in neither architecture document. The figure had reached two records, not three documents.

The error is recorded here rather than in a decision record because no record contains it. It was made in conversation and in a brief, neither of which persists. It belongs with the pass that produced the assumption-basis rule, because it is the same failure the rule exists to prevent: a plausible claim stated as established without the check that would have taken one command.

## Sources

| Source | Rating | Used for |
|---|---|---|
| `fyp-career-guidance`, six files read | **Primary, first-hand** | Every finding in the section above |
| Agent READMEs, arXiv 2511.12884, MSR 2026 | Empirical | Accumulation failure mode at scale; what developers actually put in context files |
| ETH Zurich / LogicStar, arXiv 2602.11988 | Empirical | Overviews do not help; cost; over-obedience |
| Anthropic Claude Code memory and skills documentation | Primary, first-party | 200-line target; imports do not reduce context; `.claude/rules` path globs; Auto Memory mechanics |
| GitHub issues on anthropics/claude-code | Primary | Auto Memory cannot be disabled; working-directory keying and cross-project contamination |
| log4brains, adr-log, sphinx-adr | Primary for the tool | Generating a decision timeline from records |
| Solo maintainer, 1,566 files across 6 locales | Practitioner | Frontmatter as source of truth, index regenerated, drift as a build failure |
| Practitioner writing on agent decision records | Practitioner | Do not document everything; the log will rot. **Applies to prose logs, not to evidence packages** |
| llms.txt adoption studies, Google statements | Mixed | Around 10% adoption; crawlers largely do not request it |
| Vendor blogs on context files and drift tooling | **Vendor** | Discovery only. Numeric claims treated as unverified |

## Conclusions

**Port, do not invent.** For a new repository the artifact set is: a task-status state file, an in-flight register if work is in flight, an indexed log directory with the chain-reading rule, and an authority order. All four exist in `fyp-career-guidance` and need adapting rather than designing.

**Reject:** llms.txt, repository-packaging tools, log4brains as a tool rather than a pattern, hand-written per-folder overviews, and reorganising documentation into Diataxis folders.

**Open:** the end-state and trajectory gap. `SPRINT_PLAN.md` was read and is a task breakdown with per-person assignments, gates and a deadline, not a statement of what the finished system is. The prior project has no artifact for this, so there is nothing to port.

**`team-updates/`, read after the conclusions above were written.** Eighteen dated interface-change notices, each carrying the payload before and after, the reason, and the incident that forced it. Posting one is a numbered step in the sprint plan, so it is workflow rather than optional. Not adopted here, because it exists to notify three collaborators and this project has one. Its payload-before-and-after shape is adopted into the log format instead, which fills a real gap: ADR-0018's contract check reports that a board changed and nothing recorded what it changed to.
