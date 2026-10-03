---
type: log
description: The laptop's crash at 21:49Z on 2026-10-02 traced to Windows running out of virtual memory while three mutation runs went in parallel; the run resumed one suite at a time; the morning run's checks, the 47 wrong Closed marks cleared; the description rules' contract entries dated for the day they reach main; and a diagnostic of the Claude Code setup.
status: current
---

# The crash, the morning checks, and the description committed, 2026-10-03 UTC

Previous log: `2026-10-02-the-closure-test-and-every-field.md`, its night section, which built what this one commits.

| Header | Value |
|---|---|
| Date | 2026-10-03 UTC. The operator wrote at about 07:25Z, 12:25 his time, after a forced restart |
| Model | claude-opus-5-5 |
| HEAD at start | `d515b3b`, level with `origin/main`; the night's work uncommitted |
| Mode | **Mutating.** Windows' event logs and the VS Code extension's log read. npm's registry: 2 version lookups. `data` cloned into the scratchpad |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run.

## What the operator asked

The laptop heated, Claude raised "a very lengthy" error, and he force-restarted. Was it the mutation run in the background or something else; resume the work; and run a diagnostic on Claude itself.

## The crash [VERIFIED]

UTC throughout; his clock is five hours ahead.
- **21:25Z:** three mutation batches started in three scratch clones, each running the whole suite once per mutation, in parallel, at normal priority.
- **21:34Z:** the seat's turn ended; Claude sat idle, waiting on them.
- **21:49:21Z:** Windows' Resource-Exhaustion-Detector, event 2004, "a low virtual memory condition". The largest consumers it names: OneDrive.Sync.Service.exe 10.6 GB, vmmem 3.2 GB, MsMpEng.exe.
- **21:49:29Z:** batch 1's closing suite failed, "lost sys.stderr", after all 11 of its mutations had been caught. Batches 2 and 3 never wrote their results.
- **21:49:34Z:** the extension's log, "Claude Code process exited with code 3221226505": `0xC0000409`, Windows' fail-fast exit. The error he saw.
- **07:17Z:** the next boot, event 41, a restart without a clean shutdown: his.

The laptop has 7.7 GB of RAM. **The Claude process died because Windows ran out of virtual memory.** The largest consumer was OneDrive's sync service, which is not the seat's and is not among the ten largest processes after the restart. The three parallel suites were the seat's part: three cores busy for 25 minutes, most of the heat, plus their memory and the files they write for Defender to scan. The session's transcript, 54.5 MB, adds to Claude's own footprint.

**Changed:** mutation runs go one suite at a time, at below-normal priority, with their output written as it is produced. The wrapper's first version passed a 64-bit handle as a 32-bit integer and failed without a word; the processes were lowered by hand and the wrapper fixed.

## The morning run, 04:04Z [VERIFIED from its committed log]

- **The 47 Closed marks cleared:** `closed_cleared: 47`, and `closed_marked: 0`. The closure test's fix of 10-02 held on its first live morning.
- **The level and location rules ran:** 20 drops each, over 1,162 postings read. The agreement check compared 20 of 20, no disagreement. Sweep and projection without failure; 86 of the month's 1,000 Airtable calls.
- **The Himalayas walk read 30 pages and 559 new postings**, stopping at its mark 24 hours back. On 10-01 and 10-02 it found 96 and 104. Within the new cap of 80; under the old 40 it would have had 10 pages to spare. Flagged.
- **The night's rules were not in it**: uncommitted.

## The contract entries' date [VERIFIED from the code and `data`]

`explain` excuses a change when an entry is dated after the stored shape's acceptance and not after today. Every stored shape was accepted on 2026-10-01, and today's check had not run at 07:40Z; yesterday's ran at 13:02Z.
- **The description's entries are dated 2026-10-03**, the day the change reaches `main`. Pushed before today's check, they apply on it, beside 10-02's.
- **A gap, not hit:** had today's check run first, it would have accepted 10-02's fields and moved the acceptance date to 10-03. No entry dated 10-03 could then excuse anything, and the next check would report the description's fields as changed. A change reaching `main` on the day a shape was accepted, after that day's check, has no date that is true and excuses it. For the architecture chat, against ADR-0036 and the fourth audit's F5.

## A diagnostic of the Claude Code setup, at his request [VERIFIED]

Read-only; any change waits on his answer. Over the 12 transcripts on this machine, 2026-09-11 to 2026-10-03:
- **Installation:** one install, npm global 2.1.280, as `~/.claude.json` records. No leftovers. Every settings file parses. No agents or skills of his own defined.
- **Behind:** the terminal CLI is 2.1.280 against 2.1.288 on npm's `latest`. The VS Code extension, which crashed, bundles its own, 2.1.287.
- **Unused:**
  - the Figma plugin: enabled, no use in the window, its connection not signed in, about 3.2k tokens of skill descriptions in every session (est.);
  - three claude.ai connectors, Gmail, Calendar and Drive: not signed in, never called.
- **Used and kept:** the Airtable plugin, 196 calls in the window.
- **The project's hook,** the guard on Bash: 196 runs, median 0.15 s, worst 0.67 s.
- **Denied calls:** five, none a read-only command worth pre-approving. Four were compound shell commands this project's guard stopped by design; one was an Airtable write.
- **Auto mode** is not his saved default; this session runs in it.
- **Beside the checks:** this session's transcript is 54.5 MB, and a fresh session after this commit lightens Claude's footprint. OneDrive's 10.6 GB at the crash is his to look at.

## A mistake of mine: description text in the repository [VERIFIED]

Found by the outgoing diff's privacy check, before the commit. ADR-0011: "We will write job description text, including snippets, only to the Airtable display layer." The night's work quoted measured sentences verbatim in the new tests, in `src/description.py`'s comments, in one docstring each in `src/filters.py` and `tests/test_filters.py`, in `CAPABILITIES.md` and in the night section of the 10-02 log. Some came from Himalayas postings, whose terms ADR-0020 keeps out of this repository altogether.
- **Before this commit:** every one replaced by a sentence written to the same shape, so each guard keeps its test. The tests say so in their module docstring, and the 10-02 log describes the sentences instead of quoting them.
- **Already pushed, yesterday:** five snippets from employer boards, none from Himalayas. Two in `docs/reference/platform-fields.md` from `d5dda62`, and three in the 10-02 log's evening section from `d515b3b`. Removed from the tree, with a note where they stood. They remain in history, and removing them needs a forced push, which D10 forbids without the operator: **put to him**, beside his choice of 10-02 to leave the addresses in history.
- **The rule the check now applies:** a sentence from a description is described, never quoted, in anything committed here.

## Verification of the description and the cap [VERIFIED]

On this commit's code. The mutation clone's `src`, `tests`, `tools`, `config` and `.github` were compared with the tree and found identical, and its baseline suite passed; since the suite checks every recorded mutation's text, that also proves no mutation of the night was left applied anywhere.
- **Suite:** 794 tests pass on Python 3.12, and on 3.11 under `-W error::ResourceWarning`. A run prints no workflow command.
- **Mutations:** 33 of 33 caught, each by the test built for it. 11 in the night's first batch, before the crash; the other 22 this morning, one suite at a time. 30 new in `2026-10-02-description.json` and 3 re-expressed: "an adapter declares a field it never reads", "a posting's entry is not carried", and "the cap stays at 25".
- **After the tests' sentences were rewritten** (the section above): the 20 mutations those tests catch, in the description module, the normaliser, the adapters and the place names, re-run in a fresh clone: 20 of 20 caught, each by the same test as before.
- **Stale finds:** 0 of 440.
- **The effect:** measured the night before with the code, unchanged since: of the 50 postings kept apart from age, 7 drop and none is newly kept.

## Open

- **His,** on the night's reading of his answers:
  - the hard stops: a right to work, citizenship or residence required elsewhere; security clearance not read;
  - the fresh-graduates line kept;
  - the 4 public stored rows, and the Himalayas ones, left to the clock.
- **His:** the confirm of the clearing test, in test mode with table `jobs` and 30 days, before 18:54Z on 10-04; then one more test-mode run.
- **His:** the diagnostic's two questions.
- **His:** whether the five snippets pushed on 10-02 stay in history, as the addresses do, or go by a forced push.
- **The seat's, tomorrow morning:** the first run with the description rules, its drops per rule, and today's contract check reading the new fields as re-baselined.
- **The architecture chat's,** through Addendum 4: the three rules, the cap, the re-baseline gap, and stored rows keeping their verdict.
