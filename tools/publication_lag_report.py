"""How each posting's stated publication date compares with when the pipeline
first saw it.

    python tools/publication_lag_report.py                 the data branch here
    python tools/publication_lag_report.py --test-mode     the data-test branch here
    python tools/publication_lag_report.py --repo PATH     another clone, or a bare repository
    python tools/publication_lag_report.py --dir data      a local data directory

The data branch is written on GitHub, so fetch it first:

    git fetch origin data:data

Two open questions are answered from the pipeline's own data rather than by
extra requests:

- **Does Lever's `createdAt` mean publication?** STATE.md lists it as
  unverified, and every Lever row carries `published_meaning_unconfirmed`. If
  the date is publication, a posting first seen in a run is dated after the
  previous run, because it did not exist when that run looked. A posting dated
  before the previous run, which that run nevertheless did not see, either
  reached the board late or carries a date that is not its publication.
- **How late do boards publish?** ADR-0006's cadence assumes near zero.
  Greenhouse's field is named `first_published`, so late postings there
  measure the board; if Lever shows many and Greenhouse few, the difference
  points at Lever's field rather than at boards in general.

Only postings first seen after the first run count. A posting first seen on
the first run was never missed by an earlier look, so it is evidence of
nothing.

**The report gives counts and gaps and concludes nothing.** How many late
postings would settle either question is not decided anywhere.

Runs come from the run logs rather than from first-seen values, so a run that
found nothing new still counts as the run before the next one. A run log whose
`test_mode` does not match the branch or directory being read is left out and
counted, as in tools/run_log_report.py.

Exit 0 when a report was printed, 1 when there was nothing to read.
"""

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from src import storage  # noqa: E402
import run_log_report  # noqa: E402  the run-log reading is shared, not repeated

EXAMPLES = 5


def when(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ------------------------------------------------------------------ reading
def seen_from_branch(repo, branch):
    p = subprocess.run(["git", "-C", str(repo), "show",
                        "refs/heads/%s:%s" % (branch, storage.SEEN_FILE)], capture_output=True)
    return json.loads(p.stdout.decode("utf-8")) if p.returncode == 0 else None


def seen_from_dir(directory):
    """The committed seen store and its local-only half, which holds the
    aggregator entries that never reach a branch."""
    root = Path(directory)
    merged, found = {}, False
    for path in (root / storage.SEEN_FILE, root / storage.LOCAL_DIR / storage.SEEN_FILE):
        if path.is_file():
            found = True
            merged.update(json.loads(path.read_text(encoding="utf-8")))
    return merged if found else None


# ---------------------------------------------------------------- analysing
def analyse(seen, run_times):
    """Per source: postings first seen after the first run, sorted into those
    dated after the run before, those dated at or before it, those with no
    date, and those whose first sighting matches no run."""
    runs = sorted(set(run_times))
    previous = {t: runs[i - 1] for i, t in enumerate(runs) if i > 0}
    report = {}
    for identity, entry in sorted(seen.items()):
        source = entry.get("source") or "unknown"
        first_seen = entry.get("first_seen")
        r = report.setdefault(source, {"first_run": 0, "after": 0, "before": [],
                                       "no_date": 0, "unmatched": 0})
        try:
            seen_at = when(first_seen)
        except (TypeError, ValueError, AttributeError):
            r["unmatched"] += 1
            continue
        if runs and seen_at == runs[0]:
            r["first_run"] += 1
            continue
        if seen_at not in previous:
            r["unmatched"] += 1
            continue
        if not entry.get("published_at"):
            r["no_date"] += 1
            continue
        published = when(entry["published_at"])
        prior = previous[seen_at]
        if published > prior:
            r["after"] += 1
        else:
            r["before"].append({"identity": identity, "published": published,
                                "first_seen": seen_at, "previous_run": prior,
                                "hours": (prior - published).total_seconds() / 3600})
    return report


# ------------------------------------------------------------------ rendering
def render(report, runs, where, problems):
    lines = ["Publication dates against first sighting, from %s" % where,
             "  %d run(s)%s." % (len(runs), ", %s to %s" % (
                 min(runs).strftime("%Y-%m-%d %H:%M"), max(runs).strftime("%Y-%m-%d %H:%M"))
                 if runs else ""),
             "  Only postings first seen after the first run count. The report concludes nothing.",
             "",
             "  source       first run   seen later   dated after the   dated at or   no date   unmatched",
             "               (ignored)                run before        before it"]
    for source, r in sorted(report.items()):
        later = r["after"] + len(r["before"]) + r["no_date"]
        lines.append("  %-12s %9d   %10d   %15d   %11d   %7d   %9d" % (
            source, r["first_run"], later, r["after"], len(r["before"]),
            r["no_date"], r["unmatched"]))
    for source, r in sorted(report.items()):
        if not r["before"]:
            continue
        hours = [b["hours"] for b in r["before"]]
        lines += ["", "%s: %d posting(s) dated at or before the run that did not see them"
                  % (source, len(hours)),
                  "  hours before that run: min %.1f, median %.1f, max %.1f"
                  % (min(hours), statistics.median(hours), max(hours))]
        for b in sorted(r["before"], key=lambda b: -b["hours"])[:EXAMPLES]:
            lines.append("  %s  dated %s, previous run %s, first seen %s"
                         % (b["identity"], b["published"].strftime("%Y-%m-%d %H:%M"),
                            b["previous_run"].strftime("%Y-%m-%d %H:%M"),
                            b["first_seen"].strftime("%Y-%m-%d %H:%M")))
    skipped = [(k, v) for k, v in problems.items() if v]
    if skipped:
        lines += ["", "Run logs not counted"]
        for k, names in skipped:
            lines.append("  %s: %d" % (k, len(names)))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-mode", action="store_true",
                        help="read the data-test branch and count only test runs")
    parser.add_argument("--repo", default=str(REPO_ROOT),
                        help="the repository whose branch is read (default: this one)")
    parser.add_argument("--dir", help="read a local data directory instead of a branch")
    args = parser.parse_args(argv)

    if args.dir:
        where = args.dir
        seen = seen_from_dir(args.dir)
        logs = run_log_report.logs_from_dir(str(Path(args.dir) / storage.RUNLOG_DIR))
        missing = "no seen store under %s" % args.dir
    else:
        branch = run_log_report.BRANCHES[args.test_mode]
        where = "the %s branch of %s" % (branch, args.repo)
        seen = seen_from_branch(args.repo, branch)
        logs = run_log_report.logs_from_branch(args.repo, branch)
        missing = ("no %s branch with a seen store in %s. It is written on GitHub; "
                   "fetch it first:\n  git fetch origin %s:%s"
                   % (branch, args.repo, branch, branch))
    if seen is None or logs is None:
        print(missing, file=sys.stderr)
        return 1
    runs, problems = run_log_report.parse(logs, args.test_mode)
    if not runs:
        print("no run logs to compare against in %s" % where, file=sys.stderr)
        return 1
    run_times = [r["when"] for r in runs]
    print(render(analyse(seen, run_times), run_times, where, problems))
    return 0


if __name__ == "__main__":
    sys.exit(main())
