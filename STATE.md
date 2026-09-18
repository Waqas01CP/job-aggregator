---
type: state
description: What exists right now, what is blocked and on whom, and where the proof is. Where to start, then checked against the code and data.
status: current
---

# STATE

**Last verified against `main` at `ff83385` plus the commit that carries this line, 2026-09-18 UTC**, for the push state, the suite's test count, the board count, the pool's term count, `MAP.md`'s currency and the Actions run history. Checked by `git ls-remote --heads origin`, the public Actions API, `python -m unittest discover`, and loading the pool. Four lines that claimed work was unpushed were stale and are corrected below. Also verified this session: the Airtable schema, read back after building it; that a pool widening is not retroactive; the record count, 39; that ADR-0021's eight Confirmation cases all still produce their required verdict; and that pre-commit gate 6 blocks a force-added `data/` path. Dates in this file are UTC from 2026-09-17, per CLAUDE.md. Verified in the navigation and audit round: ADR-0031's Confirmation now runs as a tool and the shipped tree is clean; 325 tests; the field inventory is measured from 84 saved responses; run 35303384355 wrote 0 rows to the public filtered file; the map's topic gate, which fires on a record with no topic; the backfill, run against a copy of the branch, which appended 257 rows and closed the gap; the five Airtable tables, each schema read back after building; that both Airtable tables were empty before ten rows were seeded into `Jobs test`; and that the heredoc guard's first design was blind to the failure it was built for.

Verified earlier, against `main` at `085c434`, 2026-09-17, and not rechecked since: the Known unverified entries dated 2026-09-17, the README row, the title pool and seniority rows, the Himalayas and Banyan Canopy trials, and the Tooling rows added on 2026-09-17. Other Documentation and Tooling rows are carried forward from earlier verifications and were not rechecked.

This file is where to start, not where to stop. It outranks memory: if you believe a row is wrong, read the file the pointer names before claiming a conflict. It does not outrank the code or the data. Where a row disagrees with them, the row is stale; report it and correct it. On 2026-09-17 four stale lines were found here that way.

Organised by task, not by session, because logs are chronological and one task spans many of them.

## How to read a row

`STATUS` is DONE, PARTIAL or PENDING. A row reads DONE only when the thing is built, never when it has merely been examined.

Every row carries `[VERIFIED]` or `[BELIEVED]`. Verified means exercised and observed. Believed means reasoned from the code but not run. **Unmarked means believed.** The default points at the weak set on purpose.

`Proof` is a commit, a decision record, or a log filename. Never a file path; paths move.

## How to maintain it

Update the affected rows **in the same commit as the work**, never in a separate pass. A commit that completes a task without updating its row is incomplete.

**When a row becomes DONE, move it to `docs/reference/completed.md` in the same commit.** Never delete one. Supersede it with a new row there if the work is redone. This file holds what is not settled; that one holds what is.

Update the verified-against line whenever you touch this file.

## Headline

**The vertical slice runs on schedule on GitHub, and the public `data` branch is growing.** Scheduled run 35253312417 on 2026-09-17 at `bac377c` restored the branch, appended 7 Greenhouse and 1 Lever posting and 3 kept rows, and pushed on top of the first manual run's commit. Test mode also works on GitHub, on `data-test`. The Airtable display layer does not exist, so ADR-0009's slice Confirmation cannot yet be met.

**Everything local is pushed.** [VERIFIED] 2026-09-18 by `git ls-remote --heads origin`: `main` is at `2bfb393`, the same commit as this working copy, so pool version 4 and the seniority rule are both on GitHub. `data` is at `91f7518` and `data-test` at `6c7425d`. **Superseded 2026-09-18:** run 35303384355 fired at 03:29Z on `bceb3d9`, 3h29m after its 00:00 slot, and is the first run on pool version 4 with the seniority rule. `data` moved to `90553c3`. [VERIFIED] **it wrote nothing to the public filtered file**, which is the prediction ADR-0030 rests on: the chain kept 294 rows, 241 of them Speechify's, and every one already had its identity in the seen store. The handoff's expectation of roughly 241 new rows was wrong, and the measured answer is zero.

Four spikes have run and their findings are folded into the records. The four decisions they raised are answered by ADR-0028 and ADR-0029.

---

**The 60 completed rows live in `docs/reference/completed.md`**, read on demand rather than at the start of every session. A DONE row is finished history: it records that something was built and how it was proved, and under this file's own rule it is never deleted. Keeping them here meant every session read 18.7KB of settled work to reach the nine rows that are not settled: 60 of the 69 rows were DONE, and the file went from 42,036 bytes to 23,334. Nothing was rewritten in the move.

## Documentation

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| End-state document | PENDING | — | — | Confirmed open in ADR-0023. No prior art exists |

## Tooling

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|

## Pipeline

| Task | Status | Evidence | Date | Proof |
|---|---|---|---|---|
| Spike follow-up: board volume, Speechify age floor, Lever `createdAt`, Himalayas pagination | PARTIAL | [VERIFIED] checks 1 to 3 complete. Check 4 complete except whether browse pagination terminates, not establishable inside its 7-request cap | 2026-09-15 | `2026-09-15-spike-followup-checks.md` |
| Himalayas adapter, conditional | PARTIAL | [VERIFIED] built, tested and run live: cursor pagination, stop anchored on stored data, aggregator rows routed to a local file never committed. **Whether it stays is unresolved: ADR-0019's condition passes on its three named components and fails on its "config entry and adapter file" wording.** Removing it is a one-line config deletion | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0019 |
| Filter chain | PARTIAL | [VERIFIED] expiry and title built and tested, 34 tests, 10 mutations all caught. **Experience is disabled: no record names a threshold and no slice platform returns the field**, and the operator has deferred the rule until filtering reads descriptions. **The annotation-vendor list is no longer provisional in code:** it moved from a constant in `src/filters.py` to `docs/reference/annotation-vendors.md` with a loader, per ADR-0031, with the three names unchanged. Its evidence is still one census of 34 rows and it has never fired on this pipeline's boards | 2026-09-17 | `2026-09-17-vertical-slice.md`, ADR-0005, ADR-0021 |
| Airtable writer | **UNBLOCKED, next** | **The operator created the token and the seven secrets on 2026-09-18, so this is now ordinary work rather than a blocker.** It is the only thing between the pipeline and a display the operator can read. The former blocker read: ADR-0004 and ADR-0035 both assume a token in a GitHub secret; the MCP authorisation that built the schema is a session's OAuth and the pipeline never uses it. Everything else the writer needs exists: the schema, ADR-0034's client decision, ADR-0035's upsert key, and ADR-0040's projection filter | 2026-09-18 | ADR-0004, ADR-0035, `docs/reference/airtable-schema.md` |
| Scheduled workflow, first run on GitHub. Supersedes the row above's "not yet exercised by GitHub" | PARTIAL | [VERIFIED] through the public Actions API: run 35179218050, schedule event, 2026-09-17T03:43Z, head `cd1f290`; the test step passed, Fetch failed with "the run could not start", push skipped; `git ls-remote --heads origin` shows only `main`. From the step 6 log the operator supplied, not checkable here: Python 3.11.16, all 12 boards `ok`, 1239 fetched, 37 kept, 36 of 500 requests, then `commit-tree` failed with "Author identity unknown" and the run exited 1 as an uncaught exception | 2026-09-17 | Run 35179218050 and its step 6 log |
| Scheduled workflow, first successful run on GitHub | PARTIAL | [VERIFIED] run 35236531478, manual, production: every step succeeded with no annotations; `data` pushed at `272cfdb` by `job-aggregator <job-aggregator@invalid>`; raw greenhouse 759 and lever 37, filtered 21, seen 796, no Himalayas record anywhere; 36 of 500 requests. **Not yet exercised on GitHub:** fetching an existing branch, the restore, a fast-forward push, and the `data-test` path. No scheduled run has succeeded yet | 2026-09-17 | `2026-09-17-first-github-runs.md` |
| Daily sweep, routing to three outcome stores | PENDING, behind the writer | No longer blocked on the token, only on the writer it reads through. **Retention is two clocks now, the operator's numbers:** write to the store at 3 days, delete from Airtable at 14, both in `docs/reference/retention.md`. The former blocker read: The sweep reads Airtable, which needs the token. Its design is now settled: ADR-0043 routes each swept row to exactly one of three append-only stores, and `expired_before_review` to none | 2026-09-18 | ADR-0014, ADR-0043 |
| Contract check | PENDING, cadence decided | **Daily**, chosen by the operator from the costed options: about 90 requests a month now and about 240 after ADR-0029's five adapters, against a per-run ceiling of 500 that no run has come within 90% of. ADR-0036 settled the channel. Still unbuilt | 2026-09-18 | ADR-0018, ADR-0036 |

## Blocked, and on whom

**The record revisions from spikes 1 and 2 are done.** ADR-0001 and ADR-0003 carry the falsified volume assumptions, ADR-0006 records the propagation assumption as confirmed, ADR-0018 bars `updated_at` as a change signal, ADR-0019's employer clause is reversed by ADR-0026, ADR-0026's key list is corrected from 18 to 20, and ADR-0027 adds per-source title normalisation. The architecture document's coverage table was corrected on 2026-09-16 for spike 3.

**ADR-0007's publication-date assumption is not falsified: it holds for Manatal**, the one platform of sixteen exposing no date at all.

**The four decisions the spikes raised are answered.** ADR-0028 sets a per-run fetch budget and fetches a posting's detail once ever rather than once per run. ADR-0029 fixes adapter order after the slice at Ashby, Workable, SmartRecruiters, Breezy and Manatal, drops Dover, and declares the registry tiers obsolete. ADR-0026 gained `envelope` and `constructed` and now covers the canonical URL.

**Superseded 2026-09-18.** This paragraph said pushing was outstanding and that Himalayas' visibility was the operator's open call. Both are closed: `origin/main` is current, Himalayas stays, and its reachability is now measured from its own `locationRestrictions` field rather than from a local fetch. What remains for the operator is below. **Airtable:** [VERIFIED] 2026-09-18 on this machine, `airtable@claude-plugins-official` is installed and `~/.claude/mcp-needs-auth-cache.json` lists `plugin:airtable:airtable` as needing authentication, which is why a tool search finds nothing. **Correction: a new session alone does not fix it**, as this line previously said. The operator must authorize the server through `/mcp`, or `/plugin`, installed, Airtable MCP, Authenticate, in an interactive session, and approve it in the browser, granting only the "Job aggregator" base if asked. A session's first check afterwards is to list the bases. **Done 2026-09-17T22:00Z or thereabouts:** the operator authorized it, and the schema is built and verified. What remains with him is the token and the four GitHub secrets, and the "To review" view, which the MCP cannot create. That token is what the pipeline uses on GitHub; it is separate from this MCP authorization and the pipeline never uses the MCP connection. **The contract check:** whether, how often, how it reports. The architecture chat's answers. Banyan Canopy's review on 2026-09-24. Done on the operator's instruction: pool version 4's AI terms; the family order; the seniority rule; Speechify and CodeRoad kept. The material behind three of these, the Airtable build task, the contract check's options and costs, and the Himalayas options, is in the session-close section of `2026-09-18-pool-version-4.md`, along with what only that session's context held.

**The architecture chat's brief of 2026-09-17 is worked through, and most of what stood here is now answered.** Ten records, ADR-0030 to ADR-0039, plus fifteen Changes rows and four in-place annotations across eleven records. Answered and closed: *rows kept under older rules and rows a widened pool never admits* (ADR-0030, one question, not two); *the seniority rule's departure from ADR-0021* (ADR-0032, with ADR-0031 supplying the frame that preferences are configuration); *question 5's three unrecorded invariants* (ADR-0033); *the Airtable writer needing the shared HTTP module to change* (ADR-0034, its own client as a scoped exception, with CLAUDE.md amended); *retry safety* (ADR-0035, upsert on Identity); *question D, the failed-run email* (ADR-0036, no); *question F, role families* (ADR-0038, views not a ranking); *question G, Speechify's city copies* (ADR-0037, rows stored and grouped at the projection, and its premise corrected); *ADR-0019's contradictory condition* (ADR-0039, the three components govern); *ADR-0020's missing guard* (it lives in the run's commit step, because `commit-tree` runs no hooks, and pre-commit gate 6 now covers `data/` paths on a code branch, proven to fire); *seen-store entries are rows* (confirmed); *ADR-0011's enumeration* (illustrative, not a schema); *when go-live starts ADR-0015's window* (the first row in Airtable); *exit 1's two causes* and *the filter chain's phantom location filter* (both corrected in `docs/architecture-2.0.md`); *the annotation-vendor list* (`docs/reference/annotation-vendors.md`, and the list moved out of code into it).

**Two items in that brief needed correcting rather than doing.** ADR-0021's Confirmation is **not** invalidated: [VERIFIED] its eight-case set was run through the current chain and every case produces the verdict the record requires, so the case set is re-run and kept rather than replaced. "Software Engineer II" is still not admitted; the pool matches it and the seniority rule drops it, so only the mechanism changed. And ADR-0023's "neither is a gate yet" correction was already made on 2026-09-17, annotated at line 76 with a Changes row.

**Still with the architecture chat.** *Whether aggregator rows may reach the private Airtable base*, question C. It is the one remaining route by which Himalayas' kept rows could reach the operator, since on a runner they persist nowhere: every scheduled run is its first contact and its kept rows die with the job. **Closed since:** the location deferral now has a record and a replacing rule, ADR-0041. **Himalayas stays**, decided 2026-09-18: the request spend was never a constraint, ADR-0028's ceiling being 500 against a maximum observed 36, and the judgement that its worldwide-remote rows were worthless rested on a different corpus and is withdrawn.

**`CHAT_STATE.md` is committed**, as the architecture chat and the operator intended. A seat had restored its `.gitignore` line and its map skip rather than flagging the change; that was wrong, and the correction is recorded in this session's log. The file was never modified, only left uncommitted for one round.

**A defect in `docs/decisions/README.md`, reported not fixed**, per the brief. Its status column says ADR-0010 has a "clause reversed by 0038". ADR-0038 reverses nothing: it states that role families are within ADR-0010 and that every view stays ordered by date. ADR-0010 is the scope floor, so an index claiming a clause of it has been reversed is the most consequential thing in that table to have wrong. Also: ADR-0013's row names 0030 but not ADR-0040, which is what actually changed the meaning of "a projection of that file", and ADR-0013's own Changes table is missing that pointer too, which is my omission from the prior round. Seven record titles in the index differ from the records' own H1s.

**The operator has created the token and the seven secrets.** The writer is therefore unblocked and is the next work. Nothing writes to Airtable yet: no code in this repository does, so both tables stayed empty until ten rows were seeded by hand into `Jobs test` on 2026-09-18 as a canary. `Jobs` is deliberately still empty, because the writer fills it and ADR-0009's Confirmation needs the pipeline rather than a hand-filled snapshot.

**Superseded, kept for the record.** **The Airtable personal access token and the four repository secrets.** The writer cannot be built without them, and the sweep, the three outcome stores and the priority star all sit behind the writer. **The steps are written out in `docs/how-to/airtable-token-and-secrets.md`**, which the operator follows. **Seven secrets, not four:** ADR-0045's sweep reads three classification tables that did not exist when the four were specified, and looking them up by name costs a call per run and breaks on a rename. The MCP authorisation that built the schema is a session's OAuth and the pipeline never uses it, so it does not substitute.

**Also with the operator.** The "To review" view, which the MCP cannot create. Whether to build the contract check and how often, ADR-0036 having settled only the channel. The stated-experience threshold, deferred by him until filtering reads descriptions. Banyan Canopy's review on 2026-09-24.

**The blocklist is no longer needed.** ADR-0021 removed it. Previously blocked on the operator; now closed.

**The Airtable base is blocked on real output**, by the operator's decision, not by an omission.

**Rozee.pk is unblocked and undecided.** robots.txt permits the job paths, the terms carry no automated-access clause, and a sitemap index publishes job URLs daily with the title in the slug. No decision record exists yet.

## Known unverified

**The workflow's branch fetch and push behave on GitHub as they did in simulation.** [VERIFIED] now in full: run 35236531478 created `data`, run 35239033514 created `data-test`, and scheduled run 35253312417 fetched the existing `data` at depth 1, restored from it, appended, and fast-forwarded the push. `2026-09-17-first-scheduled-run.md`.

**Boards publish to their APIs at the moment a posting goes live.** ADR-0006's cadence rests on it. **Recorded as confirmed 2026-09-11** in ADR-0006's Assumptions, and its Changes row explains why: a posting 0.26 hours old at fetch is positive evidence, and a second run "would tighten the bound and cannot change the verdict". The record outranks this file under ADR-0022. Until 2026-09-17 this entry read "[VERIFIED] partially" and asked for a second run; it predated the record's amendment and was stale. `2026-09-11-endpoint-feasibility-spike.md`, ADR-0006.

**Many ATS platforms expose no publication date.** ADR-0007 asserts it. **Now settled across 16 platforms and it holds, narrowly.** [VERIFIED] a publication date exists on Greenhouse, Lever, Himalayas, Ashby, Workable, SmartRecruiters, Breezy, Pinpoint and BambooHR, and on JazzHR, Freshteam, Zoho and iCIMS only inside per-posting HTML. [VERIFIED] **Manatal exposes no date field of any kind**, across 2 boards and 34 postings, and it holds 8 registry boards. Dover's per-employer board carries none either. Manatal rows can never satisfy Measure A and must use ADR-0007's first-seen fallback. ADR-0007 is unrevised. `2026-09-16-publication-date-across-untested-platforms.md`.

**Workday `startDate` means publication.** [VERIFIED] behaviourally: it equals the fetch date minus the relative age in `postedOn` on 7 of 7 postings spanning ages 1 to 13 days, and none is in the future. An employment start date would not track posting age. The field name still does not say what it holds, so provenance must be recorded. `2026-09-16-second-observation-checks.md`.

**iCIMS `datePosted` is generated, not real.** [VERIFIED] false. The earlier suspicion is **withdrawn**: an older posting reports `2025-05-15T04:00:00.000Z`, sixteen months before the three that shared `2026-09-10T04:00:00.000Z`. The field varies per posting. The shared `04:00:00.000Z` is midnight US Eastern, so the value is a date with no time. `2026-09-16-second-observation-checks.md`.

**Measure A's coverage on the slice is 100%.** [VERIFIED] every one of 916 Greenhouse and Lever rows and all 500 Himalayas rows carries a real publication date; nothing falls back to first-seen. 43 Lever rows carry the date with its meaning unconfirmed. `2026-09-17-vertical-slice.md`.

**ADR-0028's ceiling of 500 is forty times the observed need.** [VERIFIED] first four observations: 11 requests for the eleven ATS boards, 36 on first contact with Himalayas, 12 in steady state for the whole slice. That is one month short of the evidence the record's Confirmation asks for, and nothing yet reads the run logs to aggregate it. `2026-09-17-vertical-slice.md`.

**The title pool admits 2.1% of postings, and 40 of its 50 terms admitted nothing.** [VERIFIED] 19 rows from 916, seven of them Pakistan-reachable. One concrete gap found: "Forward Deployment Engineer" is dropped while "Senior Forward Deployed Engineer" is kept, because ADR-0021's plural rule cannot reach "Deployment" from `forward deployed`. Widening the pool is the operator's call. `2026-09-17-vertical-slice.md`. **Updated 2026-09-17 against production data:** 21 of 796 admitted (2.6%), 10 terms credited, 39 matching nothing. The operator decided to keep all 39, and the measurement is recorded in `docs/reference/title-pool.md`. `tools/title_pool_report.py` re-measures it and previews candidates: on these eleven boards almost every AI candidate term matched nothing, so widening the AI side depends on adding boards more than terms. `2026-09-17-operator-decisions-d1-to-d5.md`.

**Lever `createdAt` means published.** Still open. [VERIFIED] not contradicted: across five days both Lever boards produced one new posting, whose `createdAt` postdates the baseline clock, so 0 of 1 newly visible postings predate it. One appearance cannot establish the field's meaning. If Lever enters the slice, twice-daily polling answers this from the pipeline's own data within days. `2026-09-16-second-observation-checks.md`. `tools/publication_lag_report.py` now answers it from the data branch once a second production run exists: a Lever posting first seen in a later run and dated before the run that missed it is the evidence. [VERIFIED] 2026-09-17: one production run so far, so nothing to report yet. **2026-09-17, second production run:** 1 of 1 Lever posting first seen in run 2 is dated after run 1, as are 7 of 7 Greenhouse postings. Consistent, and one posting is not proof. **2026-09-18, third run:** now 2 of 2 Lever and 11 of 11 Greenhouse, with none dated at or before the run that missed it. Still consistent, still not proof; two postings is a second observation, not a demonstration of what the field means. `2026-09-17-first-scheduled-run.md`.

**Speechify's board changes by closing whole roles and rotating the cities of the rest, not by a fault.** [VERIFIED] 2026-09-11 to 2026-09-16, 1086 to 361: 723 of the 813 lost postings were four closed roles. [VERIFIED] 2026-09-16 to 2026-09-17T14:52Z, 361 to 255: four roles closed (106 postings) and 64 location copies rotated out and back in; 191 postings were in both snapshots. [INFERRED] the 191 reported at 03:43Z is that intersection, before the 64 replacements appeared; the count matches exactly, the ids were discarded. `2026-09-17-first-github-runs.md`.

**Scheduled runs keep running.** [VERIFIED] from GitHub's documentation: "In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days." Whether the pipeline's own data-branch pushes count as activity is not established. Already recorded as a risk in `docs/architecture-2.0.md`, with the operator's LinkedIn pipeline running over 100 times on bot commits alone as evidence against it. `2026-09-17-run-log-reader-and-speechify.md`.

**Postings per run are on the order of one thousand.** ADR-0001:27, inherited by ADR-0003:28. [VERIFIED] false: 11 of the 53 boards return 1646 postings. Median 27 per board, maximum 1086. The 53-board total is unmeasured. `2026-09-15-spike-followup-checks.md`.

**Lever `createdAt` means published.** Measure A on Lever rows depends on it. [VERIFIED] not established: hosted pages display no date. Page-source JSON-LD `datePosted` matches `createdAt`'s UTC date on 3 of 3, but both come from Lever, so the match is not independent. `2026-09-15-spike-followup-checks.md`.

**Greenhouse `updated_at` marks an edit to a posting.** [VERIFIED] unreliable as such: it is bulk-stamped. 16 of 21 Careem postings share one instant, and Speechify's run in four rotating batches of about 265. What writes it is unknown. `2026-09-15-spike-followup-checks.md`.

**Himalayas can be read newest-first and stopped early.** [VERIFIED] partially: the browse endpoint orders by `pubDate` and paginates by cursor without duplicates over 3 pages. The search endpoint does neither. Browse's newest posting trailed search's by 97.7 minutes. [BELIEVED] from that lag, not observed: a stopping rule keyed to a run's wall clock would skip postings that reach browse late. Termination is not established. `2026-09-15-spike-followup-checks.md`.
