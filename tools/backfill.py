"""Run ADR-0030's backfill by hand, against this tree or a clone.

    python tools/backfill.py --check        report the gap, write nothing
    python tools/backfill.py                append the gap, then re-check
    python tools/backfill.py --test-mode    the same against data/test/
    python tools/backfill.py --root PATH    against a clone of the data branch

**A run does this for itself.** Since 2026-09-18 every committing run calls
the same code at the end of its write, so the filtered layer tracks the rules
without anyone remembering. This wrapper exists for the cases a run cannot
serve: inspecting a clone, checking the gap without writing, and proving the
Confirmation can fail by withholding an identity.

The logic is in `src/backfill.py`, because the run calls it and `src` must not
import from `tools`.

Exit codes: 0 nothing to do or the append succeeded, 1 it could not run,
2 a gap remains.
"""
import argparse
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src import storage  # noqa: E402
from src.backfill import BackfillError, backfill, gap  # noqa: E402
from src.filters import TitleMatcher  # noqa: E402
from src.normalise import iso  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="report the gap and write nothing")
    ap.add_argument("--test-mode", action="store_true",
                    help="operate on data/test/ instead of data/")
    ap.add_argument("--withhold", action="append", default=[], metavar="IDENTITY",
                    help="ignore this identity, to prove the check can fail")
    ap.add_argument("--root", metavar="PATH",
                    help="treat PATH as the data root instead of data/. For a "
                         "clone of the data branch, or a test fixture.")
    args = ap.parse_args(argv)

    if args.root:
        storage.DATA_ROOT = args.root
    paths = storage.layout(args.test_mode)
    now_iso = iso(datetime.now(timezone.utc))
    matcher = TitleMatcher()

    try:
        result = backfill(paths, now_iso, matcher, withhold=args.withhold,
                          dry_run=args.check)
    except (BackfillError, storage.StorageError) as exc:
        print("backfill: %s" % exc)
        return 1

    if args.check:
        print("backfill: %d row(s) the current rules admit are absent from the "
              "filtered layer (%d publishable, %d aggregator)."
              % (result["missing"], result["public"], result["local"]))
        return 2 if result["missing"] else 0

    print("backfill: appended %d publishable and %d aggregator row(s)."
          % (result["written_public"], result["written_local"]))

    # ADR-0030's Confirmation, run immediately, against the files just written.
    remaining = gap(paths, now_iso, matcher, withhold=args.withhold)
    if remaining:
        print("backfill: %d row(s) STILL absent. The pass did not close the gap."
              % len(remaining))
        for row in remaining[:5]:
            print("    %s  %s" % (row.identity, row.title[:60]))
        return 2
    print("backfill: the gap is closed. Every row the current chain admits is "
          "in the filtered layer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
