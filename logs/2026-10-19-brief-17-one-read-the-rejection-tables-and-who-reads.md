---
type: log
description: Brief 17. Brief 16's 35 mutations proven; CLAUDE.md's third block; Jobs read once a run for the projection and the sweep; the rejection tables read only when a step needs them, its design corrected before the build and its saving measured; who reads the application measured over every saved description, tightened, and built to show in Jobs once its field is made; the chat's records read against the code.
status: current
---

# Brief 17: one read of Jobs, the rejection tables when needed, and who reads, 2026-10-19 UTC

Previous log: `2026-10-18-briefs-15-and-16-the-second-wave-built.md`.

| Header | Value |
|---|---|
| Date | 2026-10-19 from about 08:30Z to 2026-10-20 about 09:00Z, the same session as Briefs 12 to 16, paused between about 22:15Z and 08:00Z |
| Model | claude-opus-5-5 |
| HEAD at start | `19500ef`, level with `origin/main` |
| HEAD at end | the harness's `6799bdf` and this commit, on the operator's records commit `3ec48f4` |
| Mode | **Mutating.** `data` and the private repository's `data` and full branches from scratch clones, read-only; no live source read; no Airtable connector call |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What was asked

2026-10-19, relayed from the architecture chat: Brief 16's 35 mutations in two batches, one heavy job at a time, reported by what each caught; the chat writes nothing to the working copy until they are done.

2026-10-19, **Brief 17**, the operator's decisions on the report on Brief 16: Breezy out of version 1; one read of `Jobs` a run; the rejection tables read only when needed, with the chat's question whether the design reads them on every morning a step needs them; `Who reads` shown in `Jobs` now, measured over every saved description first, a label only, its precedence and its field; EWOR confirmed after the next walk; no rule for the one-city post; `CLAUDE.md` block 3; the chat's records to review. Items 2 to 4 and 8 only once the mutations were done.

The operator the same day: his daily reading time, 4 pm his time, 11:00Z.

## Errors this seat made

- **A `STATE.md` stamp written ahead of the clock**, 14:40Z at 14:17Z, caught before the commit; the hook would have refused it.
- **A backslash sent through a bash heredoc**, against the seat's own rule: once it failed on its own assert and wrote nothing; once it worked. Scripts written as files since.
- **Two estimates in the report on Brief 16 were wrong**, both found by measuring before building: the rejection tables' saving, 60 a month estimated, about 35 measured; and the re-send for `Who reads`, 16 calls estimated, one needed, since an empty label reads back as unchanged.
- **Brief 15's phrase patterns over-counted**, found by reading samples before the build: the recruiter pattern read any mention, the address pattern any mailbox. Tightened; Hacker News' thread speaks on 70 of 266, not 99.
- **The privacy scan's planted ID was first a character too long**, so the scan's proof failed; the proof did its job, and the plant was corrected.

## What was done

**Brief 16's mutations: 35 ran, 35 caught** [VERIFIED], at `19500ef` in a scratch clone, 18 then 17, 2026-10-19 10:04Z to 13:38Z; none survived or timed out.

**`CLAUDE.md` block 3** applied exactly, its find once, the suite and the map check clean (`bfdc59e`).

**One read of `Jobs` a run** (`e9bf796`): the projection's read names the sweep's fields too; the client keeps each record its upsert wrote with its ID, and `projection.as_written` merges them in before the sweep acts. A projection that failed, or a merge that cannot be trusted, leaves the sweep to read `Jobs` itself; the sweep block names which read it used. About 120 calls a month. A run started from the Actions page is `RUN_SLOT` manual (`fetch.yml` line 158) and sweeps as a morning does [VERIFIED].

**The rejection tables read only when needed** (`cb4dc12`). Measured first over the 25 morning sweeps since 2026-09-25, from the run logs and stores of both data branches: the proposal as written would have missed step 2's morning and the copy left when its row is gone. Built with five reasons, each named in the run log: a run started by hand; no copy step that finished known; a status moved since; a rejected row at its fifteen days by `Classified at` in `Jobs`; a rejection or superseded rejection copy stored in the last three days. `accepted` every morning. 14 of the 25 mornings would have skipped both tables, about 35 calls a month [VERIFIED]. The last copy step is now the last that finished: the previous run, whatever it did, let the evening take a failed copy step as done.

**`Who reads`** (`011fd16`, local until the operator makes the field). Brief 15's patterns measured over every saved posting on the private full branch, 5,853, 5,750 with text, and each pattern's matches read by sample before building; tightened where they read wrongly. Built as ADR-0058's fourth derived value, re-read for every saved posting, one label of five in a fixed order, the first-person roles in `config/who_reads.json` since ADR-0031's audit reads "chief", "head" and "lead" as seniority words. A label on 281 of 5,750: recruiter 128, agency 86, a named person 48, founder 12, engineer 7; the built module agrees with the measured draft on every posting [VERIFIED]. Of the 124 rows the projection plans today, 7 get a label: the re-send is one call. `docs/reference/airtable-schema.md` gives `Jobs` twenty-one fields.

**Seven older mutations re-expressed** on the lines this round changed, each keeping its label: two on the projection's read, one on the moved check, four on the field lists.

**The chat's records** read against the code: none contradicts a decision; six statements describe items 2 to 4 as proposed, for the chat to annotate (the report on Brief 17 lists them).

**`CAPABILITIES.md`**: the seat's lines brought current on the operator's commit of the chat's records.

**The first runs on `cb4dc12`**, 2026-10-19T19:08Z and 10-20T03:41Z [VERIFIED from their logs]: the sweep read no `Jobs` of its own (`jobs_read_by` "the projection"); the morning read `accepted` alone, both rejection tables skipped with no reason to read them, the sweep 1 call where a morning cost about 7; the projection 3 calls each. October's pipeline count 493. Jobicy, RemoteOK and We Work Remotely ran live for the first time, all ok, 877, 99 and 91 postings first seen.

**The mutation harness's targeted runs** (`6799bdf`), on the operator's question whether the batches could be faster without heating the laptop. Measured first: one suite at a time, its Python about 40% of one core of twelve, while the laptop had about 0.3 GB of 7.7 GB free and paged at about 11,500 pages a second; so running suites side by side would have added to the paging, and the time went on whole suites run after a test had already failed. `--targeted` runs first, alone, the tests whose docstrings name the mutation, or the modules importing its file when none names it, and the whole suite only when they pass. The operator approved it on 2026-10-19. The memory's holders, read for him: the Claude desktop app's Cowork VM (about 3 GB, started 2026-10-19T09:50:56Z, its log naming his other sessions' folders) and the app's own processes (about 4.4 GB); not WSL, not Docker, nothing left of VMware; the VM's programs signed by Microsoft, the app by Anthropic, Defender on with no threat on record.

## Verification

- **Suites**, each commit alone in a scratch clone on Python 3.12 and 3.11: `bfdc59e` 1013; `e9bf796` 1020; `cb4dc12` 1030; `011fd16` 1039; the operator's `3ec48f4` 1039; `6799bdf` and `5a5a83d` 1044; the map check clean at each.
- **Mutations of this round**, 33 new and 7 re-expressed: **40 ran, 40 caught**, none survived or timed out, one whole suite at a time, 20 at `011fd16` (2026-10-19 17:53Z to 19:55Z) and 20 at `3ec48f4` (19:58Z to 22:10Z), 254 minutes. Run again with the targeted harness with its own 7, at `6799bdf`: **47 ran, 47 caught**, 29.4 minutes (2026-10-20 08:21Z to 08:51Z).
- **Who reads**: 30 built cases first, then the module against the draft posting by posting, 0 differences; the preference audit clean.
- **Privacy**: the outgoing diff scanned for Airtable IDs, tokens, the private repository's name and the account's path, proven on a planted ID first; the only hits the test harness's own made-up table IDs.
- **Processes**: none of this seat's left running after each job, checked by listing.

## Not done

- Nothing of Brief 17. `011fd16` waited for the operator to make `Who reads` in `Jobs` and `Jobs test`, which he did on 2026-10-20; it was pushed at 08:21Z with his records commit, `cb4dc12..3ec48f4`, both passing the suite alone on 3.12 and 3.11 and the privacy scan clean.

## Open

- The first run with `Who reads`: its re-read of every saved posting, and the labelled rows sent, about one call.
- About 2026-10-23: EWOR's third walk, with items 146, 149 and 157; about 2026-11-18, Hacker News' month recounted.
- 2026-11-01: the Senior switch and `description_fields_shown` on; Measure A's four weeks begin.
