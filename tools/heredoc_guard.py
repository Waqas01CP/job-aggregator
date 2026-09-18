"""PreToolUse guard for the one shell shape that keeps corrupting files here.

Reads a Claude Code hook payload on stdin and prints a JSON decision. It asks
for confirmation, never denies, and only for the narrow case that has actually
failed five times in this repository's logs.

**The failure.** Content written into a file through a bash heredoc loses a
level of backslash escaping on the way. A Python string written as "\\n"
arrives in the file as a real newline, and the file stops parsing. It has
happened to src/filters.py twice and to test and scratch files three more
times, each caught by the test suite a minute later.

**Why not block every heredoc.** Most heredocs here are analysis that prints a
number and exits: they carry regexes full of backslashes, run correctly, and
are the normal way to ask a question of the data. Blocking those would make
the guard something to work around, which is how a gate stops being a gate.

**Why not leave it to the rule.** A rule restated after each of five failures
is a rule that does not work.

**So the discriminator is the file write, not the backslash.** Both together
ask; either alone runs untouched:

    backslash + writes a file   ->  ask, and suggest the Edit or Write tool
    backslash, reads only       ->  allow
    writes a file, no backslash ->  allow

Exit code is always 0. A guard that fails closed on its own bug would block
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


def verdict(command):
    """(should_ask, reason). Reason is None when nothing is suspicious."""
    for opener_line, body in heredoc_bodies(command):
        if "\\" not in body:
            continue
        writes = [p.pattern for p in WRITES if p.search(body)]
        redirected = bool(REDIRECTS.search(opener_line))
        if not writes and not redirected:
            continue
        how = "a shell redirect" if redirected and not writes else "a file write"
        return True, (
            "This heredoc contains a backslash and performs %s.\n"
            "That exact shape has corrupted a file five times in this "
            "repository: a backslash escape loses a level on the way through "
            "the heredoc, so \\n arrives as a real newline and the file stops "
            "parsing.\n"
            "The Write and Edit tools do not have this problem. Use one of "
            "them for file content, or build the text in code with chr(92) "
            "and chr(10).\n"
            "Continue only if the backslashes here are genuinely intended to "
            "survive as written." % how
        )
    return False, None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # not our business to fail a tool call over a malformed payload
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
