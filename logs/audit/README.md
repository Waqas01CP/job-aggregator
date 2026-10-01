# Audit reports

One report per audit, newest at the top, written by the audit seat in its own words. This table is the navigation index for every audit of this repository.

## Why this folder exists

Until 2026-09-30 an audit's report lived only in the audit chat. What survived was the implementing seat's summary of it, in that seat's session log, so the audit's own words, including what it checked and found correct, were lost. And the audited work, not the audit, was the only thing anyone could check later.

The operator's decision, 2026-09-30: the audit seat saves its report here, chained like the session logs. His reasons:
- **A trail.** Each audit names the one before it, so the order of the work is recorded.
- **Credibility.** An audit is not exempt from being checked.
- **Better audits.** A later audit reads this index, as a session reads `logs/README.md`, and knows which earlier report to open.

## How to use this file

**Read the table first.** When you need more, read the most recent relevant report. It names the one before it, so chain backwards only as far as you need.

**An auditor starting a new audit reads the previous report** and checks whether each of its findings was closed. A finding closed in name only is a finding again.

## How the audit seat writes a report

- **The file:** `logs/audit/YYYY-MM-DD-<which>-audit.md`, dated in UTC by the day the audit ran.
- **Frontmatter:**
  - `type: log`;
  - `description`: one sentence naming the range and the verdict;
  - `status: current`.
- **A header table:**
  - the date, in UTC;
  - the model;
  - the range audited;
  - "read-only";
  - the brief it answered;
  - **the previous report**, by file name.
- **The body, in this order:**
  1. **The verdict.**
  2. **A verdict for each item the brief listed:** correct, incorrect, or cannot verify, with the evidence.
  3. **Findings, most severe first.** Each gets a severity (data lost or corrupted / defect / stale or wrong document / nit), its file and line, the claim, the evidence, and the command with its output.
  4. **What was checked and found correct.**
  5. **What was not checked, and why.**
  6. **Anything a subagent reported that was not re-checked**, tagged as such.
- **One row in the index below**, added at the top.

**What a report may never contain.** The repository is public:
- **Nothing aggregator-sourced:** no identity, title, URL or employer name from a Himalayas posting, since ADR-0020 and ADR-0047 keep it off the public branch. Counts only.
- **No secret:** no token, and no Airtable base, table or field ID.
- **No double-bracket wikilink.** The pre-commit hook refuses one.
- **No time ahead of the clock.** The hook refuses that too.

**The audit seat writes the report and its index row, and nothing else.** It never commits or pushes.

**The implementing seat then:**
- reads the report, and checks it for anything the public branch must not carry;
- commits it unchanged, with `STATE.md`;
- records what it did with each finding in its own session log, which names the report.

**A committed report is never modified.** A correction is a note in the next report, or a new report saying so.

## Before this folder

These audits ran before 2026-09-30. Only the implementing seat's account of each survives:

| Date | Audit | Where its findings are recorded |
|---|---|---|
| 2026-09-25 | The third audit, `06c3749..783ba3e`: four defects and five document findings | `logs/2026-09-26-the-third-audit-and-the-first-scheduled-sweep.md` |
| 2026-09-24 | The second audit: fourteen findings | `logs/2026-09-24-operator-decisions-and-the-next-builds.md`, "The second audit, and what was done" |
| 2026-09-24 | The first audit of code, `d8f3658..f864053`: nine findings | `logs/2026-09-23-the-projection.md`, its fourth section |
| 2026-09-23 | `docs/how-to/build-the-writer.md` against its records | `logs/2026-09-17-corrections-and-airtable-schema.md`, its last section |
| 2026-09-23 | The decision corpus at `b242d9a` | No account in one place. Its findings are cited in the Changes rows of the records it touched |

## Index

| Date | Audit | Range | Verdict | Report |
|---|---|---|---|---|
| 2026-09-30 | The fourth audit | `783ba3e..015bead` | No deletion wrong and the deletion paths hold; five defects, none yet triggered (the clearing tool's confirmation, the agreement check, location strings the operator can take, the contract re-baseline, eight stale mutations), and wrong documents, `CAPABILITIES.md` among them | `2026-09-30-fourth-audit.md` |
