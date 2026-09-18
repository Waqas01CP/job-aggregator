"""Run ADR-0031's Confirmation: no module hard-codes a preference.

    python tools/preference_audit.py            report violations, exit 2 if any
    python tools/preference_audit.py --all      also list the allowed hits
    python tools/preference_audit.py --json     machine-readable

ADR-0031 says the title pool, the seniority list, the role families and the
annotation vendors are configuration, and that no module hard-codes any of
them. Its Confirmation is a grep, and a grep nobody runs is a rule nobody
keeps. This is that grep, runnable.

**What counts as a violation.** A preference value appearing anywhere in
shipped code except a comment or a docstring. A comment quoting `agentic` to
explain why the plural rule exists documents the rule; a list literal holding
"agentic" reimplements the pool. The second is what makes converting this to
a general aggregator a rewrite instead of a configuration swap.

**Employer names are audited too**, though ADR-0031's own Confirmation does
not name them. The same reasoning applies with more force: an employer named
in a module is a board this pipeline cannot stop polling without a code
change. ADR-0027's per-source title normalisation is the case that could
easily have gone wrong and did not, because the board configuration names a
normaliser and the normaliser itself is generic.

Exit codes follow tools/generate_map.py: 0 clean, 1 the audit could not run,
2 violations found.
"""
import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.filters import (load_annotation_vendors, load_seniority_words,  # noqa: E402
                         load_title_pool)

POOL_PATH = os.path.join(REPO_ROOT, "docs", "reference", "title-pool.md")
BOARDS_PATH = os.path.join(REPO_ROOT, "config", "boards.json")

# Everything the pipeline ships. Tests are excluded on purpose: a test that
# names a pool term is a fixture, which ADR-0031 explicitly allows.
SCAN = ("src", "tools")


class AuditError(Exception):
    pass


def load_families(path=POOL_PATH):
    """The family names, from the pool's own headings, as '### 1. Agentic AI'."""
    try:
        with io.open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        raise AuditError("title pool not found at %s" % path)
    names = re.findall(r"^###\s*\d+\.\s*(.+?)\s*$", text, re.MULTILINE)
    if not names:
        raise AuditError("no family headings found in %s" % path)
    return [n.lower() for n in names]


def load_employers(path=BOARDS_PATH):
    try:
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise AuditError("board config not found at %s" % path)
    boards = data["boards"] if isinstance(data, dict) else data
    out = set()
    for b in boards:
        for key in ("slug", "employer_alias"):
            v = b.get(key)
            # "browse" is Himalayas' endpoint name, not an employer, and it is
            # an ordinary English word that would match prose everywhere.
            if v and v != "browse":
                out.add(v.lower())
    return sorted(out)


def needles():
    terms, _ = load_title_pool()
    out = {}
    for t in terms:
        out.setdefault(t.lower(), "pool term")
    for w in load_seniority_words():
        out.setdefault(w.lower(), "seniority word")
    for v in load_annotation_vendors():
        out.setdefault(v.lower(), "annotation vendor")
    for f in load_families():
        out.setdefault(f, "role family")
    for e in load_employers():
        out.setdefault(e, "employer")
    return out


def exempt_lines(path):
    """Line numbers that are comment or docstring, which ADR-0031 allows.

    Docstrings are found with ast rather than by looking for triple quotes,
    so a data string that merely spans lines is never mistaken for one. That
    distinction is the whole point: a term in a docstring is documentation, a
    term in a string literal is a second copy of the pool."""
    with io.open(path, encoding="utf-8") as f:
        text = f.read()
    lines = set()
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise AuditError("%s does not parse: %s" % (path, exc))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        end = getattr(first, "end_lineno", first.lineno)
        lines.update(range(first.lineno, end + 1))
    with io.open(path, "rb") as f:
        for tok in tokenize.tokenize(f.readline):
            if tok.type == tokenize.COMMENT:
                lines.add(tok.start[0])
    return lines


def python_files():
    for root in SCAN:
        base = os.path.join(REPO_ROOT, root)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def scan(files=None):
    """`files` overrides the shipped tree, so a test can plant a violation in a
    temporary file and prove this audit can actually fail."""
    found = needles()
    patterns = [(n, kind, re.compile(r"(?<![a-z0-9_-])%s(?![a-z0-9-])" % re.escape(n)))
                for n, kind in found.items()]
    violations, allowed = [], []
    for path in (python_files() if files is None else files):
        rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        exempt = exempt_lines(path)
        with io.open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                low = line.lower()
                for needle, kind, pat in patterns:
                    if pat.search(low):
                        hit = {"file": rel, "line": i, "kind": kind,
                               "value": needle, "text": line.strip()[:100]}
                        (allowed if i in exempt else violations).append(hit)
    return violations, allowed, len(found)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true",
                    help="also list hits in comments and docstrings")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        violations, allowed, count = scan()
    except (AuditError, Exception) as exc:  # a preference file that will not load
        if args.json:
            print(json.dumps({"error": str(exc)}))
        else:
            print("the audit could not run: %s" % exc)
        return 1

    if args.json:
        print(json.dumps({"violations": violations, "allowed": allowed,
                          "values_checked": count}, indent=1))
        return 2 if violations else 0

    print("ADR-0031: %d preference values checked against every shipped module."
          % count)
    if violations:
        print("\n%d VIOLATION(S). A preference value in code is a piece of the"
              " general-aggregator\nconversion that becomes a rewrite.\n" % len(violations))
        for v in violations:
            print("  %s:%d  %s %r" % (v["file"], v["line"], v["kind"], v["value"]))
            print("      %s" % v["text"])
    else:
        print("\nNo violation. Every hit is a comment or a docstring.")
    print("\n%d hit(s) in comments and docstrings, which ADR-0031 allows."
          % len(allowed))
    if args.all:
        for a in allowed:
            print("  %s:%d  %s %r" % (a["file"], a["line"], a["kind"], a["value"]))
            print("      %s" % a["text"])
    return 2 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
