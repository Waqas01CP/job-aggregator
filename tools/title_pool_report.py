"""Measure the title pool against stored postings, and preview a new term
before it is added.

    python tools/title_pool_report.py                          the data branch here
    python tools/title_pool_report.py --try "forward deployment" --try "ml engineer"
    python tools/title_pool_report.py --dropped                also list every dropped title
    python tools/title_pool_report.py --repo PATH | --dir data | --test-mode
    python tools/title_pool_report.py --pool path/to/candidate-pool.md

The data branch is written on GitHub, so fetch it first:

    git fetch origin data:data

ADR-0021 makes the drop log "the sole feedback signal for a missing term" and
the pool a versioned file whose every change is a documented act. This is the
measurement behind such a change:

- **Per term**, how many postings it is *credited* with (the first matching
  term in pool order, which is what the filter records) and how many it
  *matches* on its own.
- **Terms that match nothing.** On 2026-09-17, 39 of 50 matched nothing in 796
  postings. The operator chose to keep them; re-running this after the board
  list grows is how that choice gets revisited with evidence.
- **`--try TERM`** compiles a candidate exactly as the pool would, refuses it
  if ADR-0021 would, and reports how many postings it matches and how many of
  those the current pool drops, with their titles. Adding a term without this
  preview is guessing.

Reads the employer-board raw files on the branch, or a local data directory,
where aggregator raw files are included too. Nothing is written.

Exit 0 when a report was printed, 1 when there was nothing to read or a
candidate term was refused.
"""

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import storage  # noqa: E402
from src.filters import FilterError, TitleMatcher, compile_terms, fold  # noqa: E402

EXAMPLES = 12


# ------------------------------------------------------------------ reading
def postings_from_branch(repo, branch):
    def git(*args):
        return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True)

    if git("rev-parse", "--verify", "--quiet", "refs/heads/" + branch).returncode:
        return None
    names = [n for n in git("ls-tree", "-r", "--name-only", "refs/heads/" + branch, "--",
                            storage.RAW_DIR + "/").stdout.decode("utf-8").splitlines()
             if n.endswith(".json")]
    rows = []
    for name in names:
        rows += json.loads(git("show", "refs/heads/%s:%s" % (branch, name)).stdout.decode("utf-8"))
    return rows


def postings_from_dir(directory):
    root = Path(directory)
    files = sorted((root / storage.RAW_DIR).glob("*.json")) + \
        sorted((root / storage.LOCAL_RAW_DIR).glob("*.json"))
    if not files:
        return None
    rows = []
    for path in files:
        rows += json.loads(path.read_text(encoding="utf-8"))
    return rows


# ---------------------------------------------------------------- measuring
def measure(rows, matcher):
    credited, matches = collections.Counter(), collections.Counter()
    admitted, dropped = [], []
    for row in rows:
        title = row.get("title_normalised") or row.get("title") or ""
        folded = fold(title)
        for term, pattern in matcher.patterns:
            if pattern.search(folded):
                matches[term] += 1
        term = matcher.match(title)
        if term:
            credited[term] += 1
            admitted.append(row)
        else:
            dropped.append(row)
    return {"credited": credited, "matches": matches, "admitted": admitted,
            "dropped": dropped, "zero": [t for t in matcher.terms if not matches[t]]}


def try_term(candidate, rows, matcher):
    """What a candidate would add. Compiled and validated as the pool would."""
    term = fold(candidate)
    if not term:
        raise FilterError("the candidate %r is empty after normalisation" % candidate)
    if " " not in term and term not in matcher.exempt:
        raise FilterError("%r is a single token and is not on the exempt list; ADR-0021 "
                          "requires two words unless exempted" % term)
    [(_, pattern)] = compile_terms([term])
    hits = [r for r in rows if pattern.search(fold(r.get("title_normalised") or r.get("title") or ""))]
    new = [r for r in hits if not matcher.match(r.get("title_normalised") or r.get("title") or "")]
    return {"term": term, "matches": len(hits), "new": new,
            "already": [t for t in matcher.terms if t == term]}


# ------------------------------------------------------------------ rendering
def titles_table(rows, limit=None):
    groups = collections.defaultdict(collections.Counter)
    for r in rows:
        groups[r.get("title_normalised") or r.get("title")][r.get("board_id", "?")] += 1
    ordered = sorted(groups.items(), key=lambda kv: (-sum(kv[1].values()), kv[0].lower()))
    lines = []
    for title, boards in (ordered[:limit] if limit else ordered):
        lines.append("    %4d  %s  [%s]" % (sum(boards.values()), title,
                                            ", ".join("%s %d" % kv for kv in sorted(boards.items()))))
    if limit and len(ordered) > limit:
        lines.append("    ... %d more distinct titles" % (len(ordered) - limit))
    return lines


def render(where, rows, m, report, tries, show_dropped):
    lines = ["Title pool against %d postings from %s" % (len(rows), where),
             "  %d admitted, %d dropped, %d of %d terms match nothing"
             % (len(report["admitted"]), len(report["dropped"]), len(report["zero"]), len(m.terms)),
             "",
             "  %-28s %9s %8s" % ("term", "credited", "matches")]
    for term in m.terms:
        lines.append("  %-28s %9d %8d" % (term, report["credited"][term], report["matches"][term]))
    lines += ["", "Terms that match nothing (%d):" % len(report["zero"]),
              "  " + ", ".join(report["zero"]) if report["zero"] else "  none"]
    for t in tries:
        lines += ["", "Candidate `%s`: matches %d, of which %d are dropped today"
                  % (t["term"], t["matches"], len(t["new"]))]
        if t["already"]:
            lines.append("  already in the pool")
        lines += titles_table(t["new"], EXAMPLES)
    if show_dropped:
        lines += ["", "Every dropped title:"] + titles_table(report["dropped"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-mode", action="store_true", help="read the data-test branch")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="the repository whose branch is read")
    parser.add_argument("--dir", help="read a local data directory instead of a branch")
    parser.add_argument("--pool", help="a pool file other than docs/reference/title-pool.md")
    parser.add_argument("--try", dest="tries", action="append", default=[],
                        metavar="TERM", help="preview a candidate term; repeatable")
    parser.add_argument("--dropped", action="store_true", help="list every dropped title")
    args = parser.parse_args(argv)

    if args.dir:
        where, rows = args.dir, postings_from_dir(args.dir)
        missing = "no raw files under %s" % args.dir
    else:
        branch = storage.data_branch(args.test_mode)
        where = "the %s branch of %s" % (branch, args.repo)
        rows = postings_from_branch(args.repo, branch)
        missing = ("no %s branch in %s. It is written on GitHub; fetch it first:\n"
                   "  git fetch origin %s:%s" % (branch, args.repo, branch, branch))
    if rows is None:
        print(missing, file=sys.stderr)
        return 1

    m = TitleMatcher(args.pool)
    try:
        tries = [try_term(t, rows, m) for t in args.tries]
    except FilterError as e:
        print("refused: %s" % e, file=sys.stderr)
        return 1
    print(render(where, rows, m, measure(rows, m), tries, args.dropped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
