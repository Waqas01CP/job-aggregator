#!/usr/bin/env python3
"""Generate MAP.md from the repository's own files.

Read-only against the repository. Walks the tree, reads each markdown
file's frontmatter, and writes MAP.md. It transcribes nothing: every row
is derived from a file that exists on disk right now, so the map cannot
claim a file the repository does not have, and cannot omit one it does.

Two modes.

  generate_map.py            writes MAP.md
  generate_map.py --check    writes nothing, reports whether MAP.md is current

Exit codes, so a caller can tell the causes apart:

  0  map is current (or was written successfully)
  1  structural error: a file is missing frontmatter, or has a bad type.
     Fix the file.
  2  map is stale or missing. Regenerate it.

The distinction matters because a hook that reads any non-zero exit as
"stale" will report a cause it has not tested. That happened once, on
Windows, where a Python alias stub exited non-zero without running
anything and the hook announced a stale map that was in fact current.

--check is what the pre-commit hook runs. It is the reason this map
cannot go stale: the same-operation rule stops being a discipline
someone has to remember and becomes a gate that fails the commit.

Decision records are handled differently from other documents. Their
one-line description is their H1 title, which is already maintained and
already accurate, so no description field is added to their frontmatter.
Adding one would create a second copy to keep in sync, which is the
failure this whole design exists to prevent.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = REPO_ROOT / "MAP.md"

# data/ and raw_responses/ are gitignored working data, never part of the
# record. A markdown report written under data/ on 2026-09-17 halted this
# generator, and with it the pre-commit hook, until data/ was listed here.
# briefs/ is gitignored too, added 2026-09-24: mapped, its files would land in
# a MAP.md that no clean clone could reproduce.
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", ".commitmsg",
             "data", "raw_responses", "briefs"}

# Files this generator walks past. MAP.md is its own output.
# CHAT_STATE.md was skipped here while it was gitignored; it is now
# committed and carries frontmatter like any other documented file.
SKIP_FILES = {"MAP.md", "MAP.generated.md"}

DECISIONS_DIR = REPO_ROOT / "docs" / "decisions"

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

VALID_TYPES = {"instruction", "state", "explanation", "reference", "how-to", "decision", "research", "log", "entry", "deferred"}


class MapError(Exception):
    pass


def parse_frontmatter(text):
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def first_h1(text):
    body = FRONTMATTER_RE.sub("", text, count=1)
    match = H1_RE.search(body)
    return match.group(1).strip() if match else None


def first_paragraph_after_h1(text):
    """The first prose paragraph following the H1.

    A README's H1 is usually the repository or section name, which says
    nothing. Its first paragraph is the description someone actually
    wrote. Falls back to the H1 when there is no paragraph.
    """
    body = FRONTMATTER_RE.sub("", text, count=1)
    match = H1_RE.search(body)
    if not match:
        return None
    rest = body[match.end():]
    for block in rest.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith(("#", ">", "|", "-", "*", "```", "<!--")):
            continue
        return " ".join(block.split())
    return match.group(1).strip()


def markdown_files():
    for path in sorted(REPO_ROOT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.name in SKIP_FILES:
            continue
        yield path


# Decision topics, in the order the pipeline runs, so the map reads as a
# path through the system rather than as an alphabet. Adding one here is the
# only way to add one: a record naming a topic that is not here fails the
# gate, which is what stops the vocabulary drifting into forty topics.
TOPICS = {
    "fetching": "Fetching, sources and adapters",
    "filtering": "Filtering, matching and preferences",
    "storage": "Storage and the data branch",
    "display": "The display and the projection",
    "measurement": "Measurement and evidence",
    "practice": "How this repository is worked",
}


# MADR 4.0.0's statuses. Until 2026-09-24 the check tested presence only, so a
# record reading `status: acepted` rendered in the map as a status nobody
# would read; the corpus audit of 2026-09-23 proved it. A supersession must
# also name a record that exists.
STATUSES = {"proposed", "rejected", "accepted", "deprecated"}
SUPERSEDED_RE = re.compile(r"^superseded by ADR-(\d{4})$")


def record_numbers():
    return {p.name[:4] for p in DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")}


def check_status(rel, status, numbers):
    if status in STATUSES:
        return
    match = SUPERSEDED_RE.match(status)
    if match is None:
        raise MapError(f"{rel}: status '{status}' is not one of {sorted(STATUSES)} "
                       f"or 'superseded by ADR-NNNN'")
    if match.group(1) not in numbers:
        raise MapError(f"{rel}: status names ADR-{match.group(1)}, which does not exist")


def describe(path):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(REPO_ROOT).as_posix()
    fm = parse_frontmatter(text)

    if DECISIONS_DIR in path.parents and path.name != "README.md":
        title = first_h1(text)
        if not title:
            raise MapError(f"{rel}: decision record has no H1 title")
        status = fm.get("status")
        if not status:
            raise MapError(f"{rel}: decision record has no status in frontmatter")
        check_status(rel, status, record_numbers())
        # A record's title says what was decided. Its description says what
        # question it answers, which is how a reader arrives: by topic, not
        # by decision. Both are required, so a new record cannot be added
        # without saying where it belongs and what it settles.
        topic = fm.get("topic")
        if not topic:
            raise MapError(
                f"{rel}: decision record has no topic in frontmatter. "
                f"One of {sorted(TOPICS)}."
            )
        if topic not in TOPICS:
            raise MapError(
                f"{rel}: topic '{topic}' is not one of {sorted(TOPICS)}"
            )
        description = fm.get("description")
        if not description:
            raise MapError(
                f"{rel}: decision record has no description in frontmatter. "
                f"One sentence: what question does this record answer?"
            )
        return {
            "path": rel,
            "type": "decision",
            "topic": topic,
            "description": f"**{title}.** {description}",
            "status": status,
        }

    # README files carry no frontmatter. The root README is public-facing
    # and GitHub renders frontmatter as a table, which would be noise on
    # the first thing anyone sees. Their row is derived from the H1 and
    # their location instead.
    if path.name == "README.md":
        title = first_paragraph_after_h1(text)
        if not title:
            raise MapError(f"{rel}: README has no H1 title")
        return {
            "path": rel,
            "type": "entry" if path.parent == REPO_ROOT else "reference",
            "description": title,
            "status": "current",
        }

    description = fm.get("description")
    file_type = fm.get("type")
    if not description or not file_type:
        raise MapError(
            f"{rel}: needs 'type' and 'description' in frontmatter. "
            f"Every documented file states what it holds, next to what it holds."
        )
    if file_type not in VALID_TYPES:
        raise MapError(
            f"{rel}: type '{file_type}' is not one of {sorted(VALID_TYPES)}"
        )
    return {
        "path": rel,
        "type": file_type,
        "description": description,
        "status": fm.get("status", "current"),
    }


def render(entries):
    by_type = {}
    for entry in entries:
        by_type.setdefault(entry["type"], []).append(entry)

    lines = [
        "<!-- GENERATED BY tools/generate_map.py. DO NOT EDIT BY HAND. -->",
        "<!-- To change a row, edit that file's frontmatter, then regenerate. -->",
        "",
        "# Map",
        "",
        "Every documented file in this repository, what it holds, and what kind",
        "of answer it gives. Read this before opening anything else.",
        "",
        "This file is generated from the frontmatter of the files it lists.",
        "It cannot describe a file that does not exist and cannot omit one that",
        "does. The pre-commit hook fails the commit when it is stale.",
        "",
        "**Types.** `entry` is where to start. `instruction` is how an agent",
        "should work in this repository. `state` is what is true right now.",
        "`explanation` is why the system is",
        "as it is. `reference` is what things are, opened while working.",
        "`how-to` is how to accomplish a task. `decision` is one recorded choice.",
        "`research` is a dated snapshot of what was found, valid as a record",
        "of that moment even once its findings go stale. `log` is what one",
        "session did, append-only, chained backwards through the index.",
        "`deferred` is a decision not to do something yet, carrying the",
        "trigger that would make it worth revisiting. It is not a decision",
        "record: it decides nothing, and it is the one type that states what",
        "would change its own mind.",
        "",
        "Relations between decision records live inside those records as",
        "supersedes and superseded-by links, deliberately not duplicated here.",
        "",
    ]

    order = ["entry", "instruction", "state", "explanation", "how-to", "reference", "research", "log", "decision", "deferred"]
    for file_type in order:
        rows = by_type.pop(file_type, [])
        if not rows:
            continue
        lines.append(f"## {file_type}")
        lines.append("")
        if file_type == "decision":
            # Grouped by topic. A flat list of forty-one titles is scanned by
            # whoever already knows which record they want, which is not the
            # reader who needs it.
            lines.append(
                "Grouped by topic, in the order the pipeline runs. A record "
                "appears under exactly one topic."
            )
            lines.append("")
            for topic, heading in TOPICS.items():
                in_topic = [r for r in rows if r.get("topic") == topic]
                if not in_topic:
                    continue
                lines.append(f"### {heading}")
                lines.append("")
                lines.append("| File | Holds | Status |")
                lines.append("| --- | --- | --- |")
                for row in in_topic:
                    lines.append(
                        f"| `{row['path']}` | {row['description']} | {row['status']} |"
                    )
                lines.append("")
            continue
        lines.append("| File | Holds | Status |")
        lines.append("| --- | --- | --- |")
        for row in rows:
            lines.append(
                f"| `{row['path']}` | {row['description']} | {row['status']} |"
            )
        lines.append("")

    for file_type in sorted(by_type):
        lines.append(f"## {file_type}")
        lines.append("")
        lines.append("| File | Holds | Status |")
        lines.append("| --- | --- | --- |")
        for row in by_type[file_type]:
            lines.append(
                f"| `{row['path']}` | {row['description']} | {row['status']} |"
            )
        lines.append("")

    lines.append(f"Files listed: {len(entries)}")
    lines.append("")
    return "\n".join(lines)


def main():
    check_only = "--check" in sys.argv

    try:
        entries = [describe(path) for path in markdown_files()]
    except MapError as exc:
        print(f"map: {exc}", file=sys.stderr)
        return 1

    rendered = render(entries)

    if check_only:
        if not MAP_PATH.exists():
            print("map: MAP.md does not exist. Run tools/generate_map.py", file=sys.stderr)
            return 2
        current = MAP_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print(
                "map: MAP.md is stale. A file was added, removed, or its "
                "frontmatter changed, and the map was not regenerated in the "
                "same operation.\n"
                "     Run: python tools/generate_map.py",
                file=sys.stderr,
            )
            return 2
        return 0

    MAP_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"map: wrote MAP.md with {len(entries)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
