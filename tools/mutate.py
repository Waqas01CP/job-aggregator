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
- The suite must pass before any mutation is applied, or a broken suite would
  report every mutation as caught.
- Every run compiles into a fresh bytecode cache, so a stale .pyc can never
  stand in for the mutated source.
- Every file is restored in a `finally`, compared byte for byte against the
  original, and the suite is run once more at the end.
- Refs are compared before and after each mutation. The mutation that
  reinstates `_git(cwd=REPO_ROOT)` as a default argument commits a stray
  branch to this repository by design; it is reported, never deleted here.

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
SUITE = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
KEYS = {"label", "path", "find", "replace"}


def run_suite():
    """(passed, tail, failing). The tail lets a failing baseline be read
    without rerunning; `failing` names the tests that failed or errored, so
    `--why` can show that a mutation was caught by the test meant to catch it
    rather than by an unrelated crash."""
    cache = tempfile.mkdtemp(prefix="mutate-pyc-")
    env = dict(os.environ, PYTHONPYCACHEPREFIX=cache)
    try:
        p = subprocess.run(SUITE, cwd=REPO_ROOT, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    output = (p.stdout + p.stderr).strip().splitlines()
    failing = sorted({line.split(" ", 1)[1] for line in output
                      if line.startswith(("FAIL: ", "ERROR: "))})
    return p.returncode == 0, "\n".join(output[-6:]), failing


def refs():
    p = subprocess.run(["git", "for-each-ref", "--format=%(refname)"],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    return set(p.stdout.split())


def load(path, only=None):
    """Read and validate every mutation before any file is touched."""
    with open(path, encoding="utf-8") as f:
        mutations = json.load(f)
    if not isinstance(mutations, list) or not mutations:
        raise SystemExit("%s: expected a non-empty JSON list" % path)
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
        target = REPO_ROOT / m["path"]
        if not target.is_file():
            problems.append("%s: no file at %s" % (where, m["path"]))
            continue
        count = target.read_bytes().decode("utf-8").count(m["find"])
        if count != 1:
            problems.append("%s: find occurs %d times in %s, expected exactly 1"
                            % (where, count, m["path"]))
    if problems:
        raise SystemExit("refusing to run:\n  " + "\n  ".join(problems))
    if only:
        mutations = [m for m in mutations if m["label"] == only]
        if not mutations:
            raise SystemExit("no mutation labelled %r" % only)
    return mutations


def apply_one(m):
    """Mutate, run, restore. Returns (caught, failing test names)."""
    target = REPO_ROOT / m["path"]
    original = target.read_bytes()
    mutated = original.decode("utf-8").replace(m["find"], m["replace"], 1).encode("utf-8")
    try:
        target.write_bytes(mutated)
        passed, _, failing = run_suite()
    finally:
        target.write_bytes(original)
    if target.read_bytes() != original:
        raise SystemExit("RESTORE FAILED for %s. Stop and repair it by hand." % m["path"])
    return not passed, failing


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="a JSON list of mutations")
    parser.add_argument("--only", help="apply only the mutation with this label")
    parser.add_argument("--why", action="store_true",
                        help="name the tests that caught each mutation")
    args = parser.parse_args(argv)

    mutations = load(args.file, args.only)
    originals = {m["path"]: (REPO_ROOT / m["path"]).read_bytes() for m in mutations}

    passed, tail, _ = run_suite()
    if not passed:
        print("baseline suite fails, so no mutation result would mean anything:\n" + tail)
        return 1
    print("baseline: suite passes. %d mutation(s) from %s" % (len(mutations), args.file))

    before = refs()
    results = []
    for m in mutations:
        caught, failing = apply_one(m)
        stray = sorted(refs() - before)
        results.append((m["label"], caught, stray))
        print("  %-9s %s%s" % ("caught" if caught else "SURVIVED", m["label"],
                               "   STRAY REF: %s" % ", ".join(stray) if stray else ""))
        if args.why:
            for name in failing:
                print("              by %s" % name)
        before |= set(stray)

    for path, data in originals.items():
        if (REPO_ROOT / path).read_bytes() != data:
            print("RESTORE CHECK FAILED: %s differs from its original" % path)
            return 1
    passed, tail, _ = run_suite()
    if not passed:
        print("the suite fails after restoring every file:\n" + tail)
        return 1

    survivors = [r for r in results if not r[1]]
    strays = sorted({s for r in results for s in r[2]})
    print("\n%d applied, %d caught, %d survived. Files restored, suite passes again."
          % (len(results), len(results) - len(survivors), len(survivors)))
    if strays:
        print("Stray refs created in this repository: %s. Inspect and delete them."
              % ", ".join(strays))
    return 0 if not survivors and not strays else 1


if __name__ == "__main__":
    sys.exit(main())
