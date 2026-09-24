"""PreToolUse guard for the one shell shape that keeps corrupting files here.

Reads a Claude Code hook payload on stdin and prints a JSON decision. It asks
for confirmation, never denies, and only when a heredoc writes to a file that
lives in this repository.

**The failure.** Content written into a file through a bash heredoc loses a
level of escaping on the way. A Python string written as a backslash-n
arrives in the file as a real newline, and the file stops parsing. It has
broken src/filters.py twice and test and scratch files three more times.

**Why this does NOT test for a backslash, which was the first design.**
Measured on 2026-09-18: the escape is converted before the hook sees the
command. A guard that looked for a backslash asked on the text as typed and
allowed the text it actually received, so it fired on surviving backslashes,
which are regex patterns and harmless, and stayed silent on converted ones,
which are the failure. It was precisely backwards, and only running it proved
that.

**So the trigger is the destination, which the conversion cannot hide.** A
heredoc writing to a path in this repository asks; a heredoc writing to the
scratchpad, a temporary directory or data/ runs untouched, and a heredoc that
only reads and prints runs untouched. That keeps every analysis command free,
which is most of them, and catches every command that can damage a tracked
file.

Exit code is always 0. A guard that failed closed on its own bug would block
work for a reason nobody could see.
"""
import json
import re
import sys

# A heredoc opener: <<EOF, <<-EOF, <<'EOF', <<"EOF".
OPENER = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

# Writing a file from inside the body. These are the shapes this repository
# actually uses; a new one joins the list the first time it corrupts a file.
WRITES = (
    re.compile(r"\bopen\s*\([^)]*['\"][wa]"),
    re.compile(r"\bio\.open\s*\([^)]*['\"][wa]"),
    re.compile(r"\.write_text\s*\("),
    re.compile(r"\.writelines\s*\("),
    re.compile(r"\bwrite_atomic\s*\("),
    re.compile(r"\bshutil\.(copy|move)\s*\("),
)

# Writing a file from the command line the heredoc is attached to.
REDIRECTS = re.compile(r"(?<![0-9<>])>>?\s*[^\s|&;]+")


def heredoc_bodies(command):
    """Every heredoc body in the command, with the delimiter that closed it.

    Scans line by line rather than with one regex, because a body may contain
    anything at all, including text that looks like another opener."""
    lines = command.split("\n")
    bodies, i = [], 0
    while i < len(lines):
        match = OPENER.search(lines[i])
        if not match:
            i += 1
            continue
        delimiter = match.group(2)
        opener_line = lines[i]
        body, i = [], i + 1
        while i < len(lines) and lines[i].strip() != delimiter:
            body.append(lines[i])
            i += 1
        i += 1  # step over the closing delimiter
        bodies.append((opener_line, "\n".join(body)))
    return bodies


# Paths a heredoc may write to freely: scratch space and the pipeline's own
# gitignored output. Nothing here is tracked, so nothing here can be corrupted
# in a way that survives.
_SEP = "[" + chr(92) + chr(92) + "/]"      # a path separator, either slash
SAFE_PATH = re.compile(
    "(temp" + _SEP + "claude|scratchpad|" + _SEP + "tmp" + _SEP +
    "|(^|" + _SEP + ")data" + _SEP + ")",
    re.IGNORECASE)


def written_paths(body, opener_line):
    """Every file path this heredoc appears to write to."""
    paths = []
    for pattern in WRITES:
        for match in pattern.finditer(body):
            quoted = re.search(r"['\"]([^'\"]+)['\"]", match.group(0))
            if quoted:
                paths.append(quoted.group(1))
            else:
                paths.append("")
    for match in REDIRECTS.finditer(opener_line):
        paths.append(match.group(0).lstrip("> ").strip())
    return paths


def verdict(command):
    """(should_ask, reason). Reason is None when nothing is suspicious."""
    for opener_line, body in heredoc_bodies(command):
        paths = written_paths(body, opener_line)
        if not paths:
            continue
        risky = [p for p in paths if not SAFE_PATH.search(p)]
        if not risky:
            continue
        return True, chr(10).join((
            "This heredoc writes to %s, which is inside the repository."
            % (risky[0] or "a file"),
            "Content written through a heredoc loses a level of escaping: a "
            "backslash-n becomes a real newline and the file stops parsing. "
            "That has happened six times here, twice to src/filters.py, and "
            "once inside the guard that was being written to prevent it.",
            "The conversion happens before this guard can see the command, so "
            "it cannot check the content, only the destination.",
            "Use the Write or Edit tool for file content, or build the text in "
            "code with chr(92) and chr(10). Continue only if this heredoc "
            "contains no escape sequences at all."))
    return False, None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # not our business to fail a tool call over a malformed payload
    if not isinstance(payload, dict):
        return 0  # valid JSON that is not an object used to raise and exit 1
    command = (payload.get("tool_input") or {}).get("command") or ""
    should_ask, reason = verdict(command)
    if should_ask:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
