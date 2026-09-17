"""Read the run logs and report what ADR-0028's Confirmation needs.

    python tools/run_log_report.py                  the data branch here
    python tools/run_log_report.py --test-mode      the data-test branch here
    python tools/run_log_report.py --repo PATH      another clone, or a bare repository
    python tools/run_log_report.py --dir PATH       a directory of run logs, e.g. data/logs-runs
    python tools/run_log_report.py --since 2026-10-01

The data branch is written on a GitHub runner, so this clone only has what it
last fetched. Fetch first:

    git fetch origin data:data

ADR-0028 set the per-run request ceiling at 500 as a runaway guard with no
basis, and says the real ceiling is set from the distribution the run logs
record over the first month. This prints that distribution, per run and per
source, and whether the ceiling or the circuit breaker ever stopped a run.
**It does not propose a ceiling.** The margin is a decision, and it belongs in
the record's amendment with its basis.

Two readings would mislead without help, so they are reported beside the
numbers rather than left to be noticed:

- **First contact.** A run in which every posting a source returned was new
  costs far more than steady state; Himalayas cost 36 requests on first contact
  and 12 after it. Mixed into one distribution, first-contact runs read as the
  normal load, so each source reports how many of its runs were first contact.
  A source that is first contact on every run is not persisting its state.
- **Test runs.** A test run's log is not evidence about production volume. A
  log whose `test_mode` does not match the branch or flag being read is
  excluded and counted, because before 2026-09-17 a test run committed to the
  production branch.

The run logs also exist so that a board returning nothing is visible, since a
board that is silent for a week is a broken adapter rather than a quiet market.
So the report ends with every board whose latest runs fetched nothing or
failed, and for how long. No threshold is applied: how long is too long is not
decided anywhere.

Exit 0 when a report was printed, 1 when there was nothing to read.
"""

import argparse
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import storage  # noqa: E402  the names come from the writer, never repeated

RUNLOG_DIR = storage.RUNLOG_DIR
BRANCHES = {False: storage.DATA_BRANCH, True: storage.TEST_DATA_BRANCH}


# ------------------------------------------------------------------ reading
def logs_from_branch(repo, branch):
    """Every run log on a branch, as (name, text). None when the branch is absent.

    One `git cat-file --batch` for all of them, so a year of twice-daily logs
    is one process rather than seven hundred."""
    def git(args, data=None):
        return subprocess.run(["git", "-C", str(repo)] + args, input=data,
                              capture_output=True)

    if git(["rev-parse", "--verify", "--quiet", "refs/heads/" + branch]).returncode:
        return None
    listed = git(["ls-tree", "-r", "--name-only", "refs/heads/" + branch, "--", RUNLOG_DIR + "/"])
    names = [n for n in listed.stdout.decode("utf-8").splitlines() if n.endswith(".json")]
    if not names:
        return []
    request = "".join("refs/heads/%s:%s\n" % (branch, n) for n in names).encode("utf-8")
    out = git(["cat-file", "--batch"], request).stdout
    logs, pos = [], 0
    for name in names:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        if len(header) != 3:
            raise SystemExit("git could not read %s:%s" % (branch, name))
        size = int(header[2])
        body = out[end + 1:end + 1 + size]
        logs.append((name, body.decode("utf-8")))
        pos = end + 1 + size + 1
    return logs


def logs_from_dir(directory):
    path = Path(directory)
    if not path.is_dir():
        return None
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(path.glob("*.json"))]


def parse(named_texts, test_mode, since=None):
    """(runs, problems). A run is kept only if it parses, carries the fields
    this report reads, matches the mode being read, and is not before `since`."""
    runs, problems = [], {"unreadable": [], "other mode": [], "before since": []}
    for name, text in named_texts:
        try:
            log = json.loads(text)
            when = datetime.fromisoformat(log["run_at"].replace("Z", "+00:00"))
            requests = log["requests"]
            int(requests["requests_used"]), int(requests["budget"])
            dict(requests["by_source"])
            boards = list(log["boards"])
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            problems["unreadable"].append("%s (%s: %s)" % (name, type(e).__name__, e))
            continue
        if bool(log.get("test_mode")) != test_mode:
            problems["other mode"].append(name)
            continue
        if since and when.date() < since:
            problems["before since"].append(name)
            continue
        runs.append({"name": name, "when": when, "requests": requests, "boards": boards,
                     "stopped": log.get("stopped")})
    runs.sort(key=lambda r: r["when"])
    return runs, problems


# ---------------------------------------------------------------- summarising
def nearest_rank(values, fraction):
    """The nearest-rank percentile: always an observed value, defined for any n."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(fraction * len(ordered))) - 1]


def spread(values):
    return {"n": len(values), "min": min(values), "median": statistics.median(values),
            "p90": nearest_rank(values, 0.9), "max": max(values)}


def source_of(board_id):
    return board_id.split(":", 1)[0]


def summarise(runs):
    per_run = [int(r["requests"]["requests_used"]) for r in runs]
    ceilings = sorted({int(r["requests"]["budget"]) for r in runs})

    sources = {}
    for r in runs:
        fetched, new = {}, {}
        for b in r["boards"]:
            s = source_of(b.get("board", ""))
            fetched[s] = fetched.get(s, 0) + int(b.get("fetched") or 0)
            new[s] = new.get(s, 0) + int(b.get("new") or 0)
        for s, used in r["requests"]["by_source"].items():
            entry = sources.setdefault(s, {"requests": [], "first_contact": 0})
            entry["requests"].append(int(used))
            if fetched.get(s, 0) > 0 and new.get(s, 0) == fetched[s]:
                entry["first_contact"] += 1

    stopped = {
        "ceiling": [r["name"] for r in runs
                    if int(r["requests"]["requests_used"]) >= int(r["requests"]["budget"])],
        "circuit": [r["name"] for r in runs if r["requests"].get("circuit_open")],
        "not reached": sum(1 for r in runs for b in r["boards"]
                           if b.get("status") == "not reached"),
    }

    # Walk each board's runs from the newest back while it keeps fetching
    # nothing or failing. A board that fetched something in its latest run is
    # not listed, however bad its history.
    history = {}
    for r in runs:
        for b in r["boards"]:
            history.setdefault(b.get("board"), []).append((r["when"], b))
    quiet = []
    for board, seen in history.items():
        streak = []
        for when, b in reversed(seen):
            if b.get("status") == "ok" and int(b.get("fetched") or 0) > 0:
                break
            streak.append((when, b))
        if streak:
            since = streak[-1][0]
            statuses = sorted({b.get("status") for _, b in streak})
            quiet.append({"board": board, "runs": len(streak), "since": since,
                          "days": (seen[-1][0] - since).total_seconds() / 86400,
                          "statuses": statuses})
    quiet.sort(key=lambda q: (-q["runs"], q["board"]))

    return {
        "runs": len(runs),
        "first": runs[0]["when"], "last": runs[-1]["when"],
        "span_days": (runs[-1]["when"] - runs[0]["when"]).total_seconds() / 86400,
        "ceilings": ceilings,
        "per_run": spread(per_run),
        "sources": {s: dict(spread(v["requests"]), first_contact=v["first_contact"])
                    for s, v in sorted(sources.items())},
        "retries": sum(int(r["requests"].get("retries") or 0) for r in runs),
        "failures": sum(int(r["requests"].get("failures") or 0) for r in runs),
        "stopped": stopped,
        "quiet": quiet,
    }


# ------------------------------------------------------------------ rendering
def number(x):
    return ("%d" % x) if float(x).is_integer() else ("%.1f" % x)


def render(report, where, problems):
    lines = ["Run logs from %s" % where,
             "  %d run(s), %s to %s, a span of %.1f days. ADR-0028 sets the real ceiling "
             "after the first month."
             % (report["runs"], report["first"].strftime("%Y-%m-%d %H:%M"),
                report["last"].strftime("%Y-%m-%d %H:%M"), report["span_days"]),
             "  Ceiling in force: %s. It is provisional until ADR-0028 is amended."
             % ", ".join(str(c) for c in report["ceilings"]),
             "",
             "Requests per run",
             "  %-14s %4s %6s %8s %6s %6s %s" % ("", "runs", "min", "median", "p90", "max",
                                                "first-contact runs")]
    p = report["per_run"]
    lines.append("  %-14s %4d %6s %8s %6s %6s" % ("all sources", p["n"], number(p["min"]),
                                                 number(p["median"]), number(p["p90"]),
                                                 number(p["max"])))
    for s, v in report["sources"].items():
        flag = "  every run" if v["first_contact"] == v["n"] and v["n"] > 1 else ""
        lines.append("  %-14s %4d %6s %8s %6s %6s %d%s"
                     % (s, v["n"], number(v["min"]), number(v["median"]), number(v["p90"]),
                        number(v["max"]), v["first_contact"], flag))
    st = report["stopped"]
    lines += ["",
              "Stops",
              "  runs that reached the ceiling: %d%s"
              % (len(st["ceiling"]), "  (%s)" % ", ".join(st["ceiling"]) if st["ceiling"] else ""),
              "  runs that ended with the circuit open: %d%s"
              % (len(st["circuit"]), "  (%s)" % ", ".join(st["circuit"]) if st["circuit"] else ""),
              "  board lines marked not reached: %d" % st["not reached"],
              "  retries %d, failures %d, across all runs" % (report["retries"], report["failures"]),
              "",
              "Boards whose latest runs fetched nothing or failed"]
    if report["quiet"]:
        for q in report["quiet"]:
            lines.append("  %-34s %3d run(s) since %s, %.1f days  %s"
                         % (q["board"], q["runs"], q["since"].strftime("%Y-%m-%d %H:%M"),
                            q["days"], "/".join(str(s) for s in q["statuses"])))
    else:
        lines.append("  none")
    skipped = [(k, v) for k, v in problems.items() if v]
    if skipped:
        lines += ["", "Logs not counted"]
        for k, names in skipped:
            lines.append("  %s: %d  %s" % (k, len(names), ", ".join(names[:5])
                                           + (" ..." if len(names) > 5 else "")))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-mode", action="store_true",
                        help="read the data-test branch and count only test runs")
    parser.add_argument("--repo", default=str(REPO_ROOT),
                        help="the repository whose branch is read (default: this one)")
    parser.add_argument("--dir", help="read run logs from a directory instead of a branch")
    parser.add_argument("--since", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
                        help="ignore runs before this date, YYYY-MM-DD")
    args = parser.parse_args(argv)

    if args.dir:
        where = args.dir
        texts = logs_from_dir(args.dir)
        missing = "no directory at %s" % args.dir
    else:
        branch = BRANCHES[args.test_mode]
        where = "the %s branch of %s" % (branch, args.repo)
        texts = logs_from_branch(args.repo, branch)
        missing = ("no %s branch in %s. It is written on GitHub; fetch it first:\n"
                   "  git fetch origin %s:%s" % (branch, args.repo, branch, branch))
    if texts is None:
        print(missing, file=sys.stderr)
        return 1

    runs, problems = parse(texts, args.test_mode, args.since)
    if not runs:
        print("no run logs to report from %s" % where, file=sys.stderr)
        for k, names in problems.items():
            if names:
                print("  %s: %d" % (k, len(names)), file=sys.stderr)
        return 1
    print(render(summarise(runs), where, problems))
    return 0


if __name__ == "__main__":
    sys.exit(main())
