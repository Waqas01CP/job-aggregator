"""Mutation harness: break the code that provides a guarantee, and confirm the
suite notices.

    python tools/mutate.py tools/mutations/<file>.json
    python tools/mutate.py tools/mutations/<file>.json --only <label>
    python tools/mutate.py tools/mutations/<file>.json --why

A mutation file is a JSON list of {"label", "path", "find", "replace"}. Each
mutation replaces one exact, unique piece of source text, runs the whole suite,
and restores the file from the bytes held in memory. A mutation the suite still
passes under is a survivor: a test that looks adequate and is not, dead code,
or two branches with the same effect.

Why this lives in the repository. The first version was kept in a session
scratchpad and died with the session, along with every mutation file, so the
79 mutations behind the vertical slice cannot be re-run.

Guards, each against a failure that has already happened once:

- A `find` that does not occur exactly once is refused before anything runs.
  An in-place replacement that silently matched nothing cost real time twice.
  The suite applies the same check to every file on record, so a commit
  that changes the code under a mutation fails until the mutation is
  re-expressed. A file is refused whole, and the fourth audit found four
  that had been unable to run since `19ca94d` without anyone knowing.
- The suite must pass before any mutation is applied, or a broken suite would
  report every mutation as caught.
- Every run compiles into a fresh bytecode cache, so a stale .pyc can never
  stand in for the mutated source.
- Every file is restored in a `finally`, compared byte for byte against the
  original, and the suite is run once more at the end.
- Refs are compared before and after each mutation. The mutation that
  reinstates `_git(cwd=REPO_ROOT)` as a default argument commits a stray
  branch to this repository by design; it is reported, never deleted here.
- Each suite has a time limit, and a suite that reaches it is stopped with
  everything it started and reported as timed out, never as caught. On
  2026-10-17 a suite under one mutation sat idle for over twenty minutes, no
  CPU and no child process, and the harness, which waited without limit,
  held a 57-mutation batch with it; the same suite run again finished in
  163 seconds. The suite runs verbose, so the tail of a timed-out run names
  the test that was running, and with its input closed, so no test can wait
  on one.

Exit 0 when every mutation was caught, 1 otherwise.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITE = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]
KEYS = {"label", "path", "find", "replace"}
# The whole suite takes three to five minutes on the operator's laptop at
# below-normal priority; four times that has stopped, not slowed.
SUITE_TIMEOUT = 20 * 60


# Names the file a mutation is applied to, for the suite's run. The suite
# checks that every find on file still occurs exactly once, and an applied
# mutation's file is the one place that must not hold: without this every
# mutation would be "caught" by that check alone.
APPLIED_ENV = "MUTATION_APPLIED"


def kill_tree(process):
    """The suite and everything it started. On Windows the interpreter a
    venv names is a launcher that starts the real one as its child, so
    killing the launcher alone would leave the suite running, holding the
    output pipes open."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                       capture_output=True)
    else:
        process.kill()


def run_suite(applied=None, timeout=SUITE_TIMEOUT):
    """(passed, tail, failing, timed_out). The tail lets a failing baseline
    be read without rerunning, and names the running test when the suite
    timed out; `failing` names the tests that failed or errored, so `--why`
    can show that a mutation was caught by the test meant to catch it rather
    than by an unrelated crash. `applied` is the path of the file a mutation
    has changed, or None for the baseline and the final run."""
    cache = tempfile.mkdtemp(prefix="mutate-pyc-")
    env = dict(os.environ, PYTHONPYCACHEPREFIX=cache)
    env.pop(APPLIED_ENV, None)
    if applied:
        env[APPLIED_ENV] = applied
    timed_out = False
    try:
        p = subprocess.Popen(SUITE, cwd=REPO_ROOT, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace")
        try:
            stdout, stderr = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(p)
            stdout, stderr = p.communicate()
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    output = ((stdout or "") + (stderr or "")).strip().splitlines()
    failing = sorted({line.split(" ", 1)[1] for line in output
                      if line.startswith(("FAIL: ", "ERROR: "))})
    return (p.returncode == 0 and not timed_out, "\n".join(output[-6:]), failing,
            timed_out)


def refs():
    p = subprocess.run(["git", "for-each-ref", "--format=%(refname)"],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    return set(p.stdout.split())


def problems_in(mutations, root=REPO_ROOT, exempt=()):
    """What stops a list of mutations from running against the tree at
    `root`: wrong keys, a duplicate label, a find equal to its replace, a
    missing file, or a find that does not occur exactly once. A path in
    `exempt` is not counted, which is how the suite reads the tree while the
    harness holds one file mutated. The suite runs this over every file on
    record: the fourth audit's F6 found a commit that left 8 finds matching
    nothing and 4 files unable to run, which nothing noticed."""
    problems, labels = [], set()
    for i, m in enumerate(mutations):
        where = "[%d] %s" % (i, m.get("label") if isinstance(m, dict) else "?")
        if not isinstance(m, dict) or set(m) != KEYS:
            problems.append("%s: keys must be exactly %s" % (where, sorted(KEYS)))
            continue
        if m["label"] in labels:
            problems.append("%s: duplicate label" % where)
        labels.add(m["label"])
        if m["find"] == m["replace"]:
            problems.append("%s: find and replace are identical" % where)
        target = Path(root) / m["path"]
        if not target.is_file():
            problems.append("%s: no file at %s" % (where, m["path"]))
            continue
        if m["path"] in exempt:
            continue
        count = target.read_bytes().decode("utf-8").count(m["find"])
        if count != 1:
            problems.append("%s: find occurs %d times in %s, expected exactly 1"
                            % (where, count, m["path"]))
    return problems


def load(path, only=None):
    """Read and validate every mutation before any file is touched."""
    with open(path, encoding="utf-8") as f:
        mutations = json.load(f)
    if not isinstance(mutations, list) or not mutations:
        raise SystemExit("%s: expected a non-empty JSON list" % path)
    problems = problems_in(mutations)
    if problems:
        raise SystemExit("refusing to run:\n  " + "\n  ".join(problems))
    if only:
        mutations = [m for m in mutations if m["label"] == only]
        if not mutations:
            raise SystemExit("no mutation labelled %r" % only)
    return mutations


def apply_one(m):
    """Mutate, run, restore. Returns (caught, failing test names, the
    tail when the suite timed out or None). A suite that timed out caught
    nothing anyone can name."""
    target = REPO_ROOT / m["path"]
    original = target.read_bytes()
    mutated = original.decode("utf-8").replace(m["find"], m["replace"], 1).encode("utf-8")
    try:
        target.write_bytes(mutated)
        passed, tail, failing, timed_out = run_suite(applied=m["path"])
    finally:
        target.write_bytes(original)
    if target.read_bytes() != original:
        raise SystemExit("RESTORE FAILED for %s. Stop and repair it by hand." % m["path"])
    return not passed and not timed_out, failing, tail if timed_out else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="a JSON list of mutations")
    parser.add_argument("--only", help="apply only the mutation with this label")
    parser.add_argument("--why", action="store_true",
                        help="name the tests that caught each mutation")
    args = parser.parse_args(argv)

    mutations = load(args.file, args.only)
    originals = {m["path"]: (REPO_ROOT / m["path"]).read_bytes() for m in mutations}

    passed, tail, _, timed_out = run_suite()
    if not passed:
        print("baseline suite %s, so no mutation result would mean anything:\n%s"
              % ("timed out" if timed_out else "fails", tail))
        return 1
    print("baseline: suite passes. %d mutation(s) from %s" % (len(mutations), args.file))

    before = refs()
    results = []
    for m in mutations:
        caught, failing, hung = apply_one(m)
        stray = sorted(refs() - before)
        results.append((m["label"], caught, stray, hung is not None))
        print("  %-9s %s%s" % ("caught" if caught else "TIMED OUT" if hung is not None
                               else "SURVIVED", m["label"],
                               "   STRAY REF: %s" % ", ".join(stray) if stray else ""),
              flush=True)
        if hung is not None:
            print("              the suite ran past %d seconds and was stopped; its last "
                  "lines:\n%s" % (SUITE_TIMEOUT, hung), flush=True)
        if args.why:
            for name in failing:
                print("              by %s" % name, flush=True)
        before |= set(stray)

    for path, data in originals.items():
        if (REPO_ROOT / path).read_bytes() != data:
            print("RESTORE CHECK FAILED: %s differs from its original" % path)
            return 1
    passed, tail, _, timed_out = run_suite()
    if not passed:
        print("the suite %s after restoring every file:\n%s"
              % ("timed out" if timed_out else "fails", tail))
        return 1

    survivors = [r for r in results if not r[1]]
    hung = [r for r in survivors if r[3]]
    strays = sorted({s for r in results for s in r[2]})
    print("\n%d applied, %d caught, %d survived, %d timed out. Files restored, suite "
          "passes again." % (len(results), len(results) - len(survivors),
                             len(survivors) - len(hung), len(hung)))
    if strays:
        print("Stray refs created in this repository: %s. Inspect and delete them."
              % ", ".join(strays))
    return 0 if not survivors and not strays else 1


if __name__ == "__main__":
    sys.exit(main())
