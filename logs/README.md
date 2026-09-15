# Session logs

One log per session, newest at the top. This table is the navigation index for all session history.

**No logs yet.** Nothing has been implemented. The first row lands when the first implementing session runs.

## How to use this file

Read this table first. It tells you what prior sessions did.

**When you need detail beyond what this table gives, read the most recent relevant log. That log references the one before it. Chain backwards only as far as you need, and stop when you have enough.** Do not read the directory.

This rule is what keeps the reading cost flat as the log count grows.

## How to maintain it

**Append your row in the same commit as your work.** A session that writes a log and does not index it has left the log invisible.

**Never delete or modify an existing row.** If a later session corrects an earlier one, that is a new row saying so.

**Rows are compressed. No prose, no reasoning, no elaboration beyond what a future session needs in order to decide whether to open the log.** The reasoning lives in the log, one level down. An index that explains is an index nobody finishes reading.

**If a log file exists with no row here, read it and add the row before doing anything else.**

## Log format

ADR-0024. In short: a header with date, model, the HEAD commit, and whether the session was read-only or mutating. Every factual claim carries a file and line, or a command and its output. Every claim tagged `[VERIFIED]` or `[BELIEVED]`, with unmarked meaning believed. Rejected alternatives recorded with the reason. What was checked and found already correct, recorded. What was not done, stated explicitly. Findings separated from decisions.

Length follows the work. No cap, no floor.

## Reorganisation

When this directory passes roughly 80 to 100 files at its root, split by lane into subdirectories and leave this index at the top pointing into them. Do it before the root becomes unscannable, not after.

## Index

| Date | Session | What was done | Outcome |
|---|---|---|---|
| — | — | No sessions yet | — |
