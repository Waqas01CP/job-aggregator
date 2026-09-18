"""ADR-0030's backfill: append the rows the current rules admit and the
filtered layer never received.

    python tools/backfill.py --check        report the gap, write nothing
    python tools/backfill.py                append the gap, then re-check
    python tools/backfill.py --test-mode    the same against data/test/

**Why a gap exists at all.** A run writes a kept row only if its identity is
new to the seen store, because `split_new` runs before the write. So when the
rules widen, rows the new rules admit never arrive: the postings were already
seen under the old rules and no later run will offer them again. On
2026-09-18 that was 257 rows, including the Veeam AI internship pool version 4
was widened to catch and 241 Speechify city copies.

**This is not a second writer with its own rules.** It reads the raw layer,
applies the same chain a run applies, and appends through
`storage.append_delta`, which is the same function and the same file. The one
thing it does differently is skip the seen-store check, which is the whole
point.

**ADR-0020 is enforced exactly as a run enforces it.** Aggregator rows go to
the local filtered file and publishable rows to the committed one, split by
`is_publishable` on the row's own source, never by filename. A run that
offered the public file to the branch would then find nothing to refuse.

Exit codes: 0 nothing to do or the append succeeded, 2 a gap remains.
"""
import argparse
import glob
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src import storage  # noqa: E402
from src.config import is_publishable  # noqa: E402
from src.filters import TitleMatcher, apply_chain  # noqa: E402
from src.normalise import Row, iso  # noqa: E402


class BackfillError(Exception):
    pass


def raw_files(paths):
    """Every raw file, committed and local. Sorted so two runs agree."""
    out = []
    for key in ("raw_dir", "local_raw_dir"):
        out.extend(sorted(glob.glob(os.path.join(paths[key], "*.json"))))
    return out


def load_rows(paths, withhold=()):
    """Rebuild rows from the raw layer.

    `withhold` drops identities before anything is judged. It exists so the
    Confirmation can be given the case built to defeat it: hold one identity
    back, and the check must report exactly one row still missing."""
    withheld = set(withhold)
    rows = []
    for path in raw_files(paths):
        for record in storage.read_records(path):
            if record.get("identity") in withheld:
                continue
            try:
                rows.append(Row(**record))
            except TypeError as exc:
                raise BackfillError("%s holds a record this code cannot read: %s"
                                    % (path, exc))
    return rows


def admitted(rows, now_iso, matcher=None):
    kept, _ = apply_chain(rows, now_iso, matcher=matcher or TitleMatcher())
    return [row for row, _ in kept]


def gap(paths, now_iso, matcher=None, withhold=()):
    """Rows the current chain admits that the filtered layer does not hold.

    Both halves are checked, because a row absent from the public file may be
    correctly present in the local one."""
    rows = load_rows(paths, withhold=withhold)
    held = set()
    for key in ("filtered", "local_filtered"):
        held.update(r.get("identity") for r in storage.read_records(paths[key]))
    return [r for r in admitted(rows, now_iso, matcher) if r.identity not in held]


def backfill(paths, now_iso, matcher=None, withhold=(), dry_run=False):
    missing = gap(paths, now_iso, matcher, withhold)
    public = [r for r in missing if is_publishable(r.source)]
    local = [r for r in missing if not is_publishable(r.source)]
    result = {"missing": len(missing), "public": len(public), "local": len(local),
              "written_public": 0, "written_local": 0}
    if dry_run:
        return result
    result["written_local"] = storage.append_delta(
        paths["local_filtered"], [r.as_record() for r in local])
    result["written_public"] = storage.append_delta(
        paths["filtered"], [r.as_record() for r in public])
    return result


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
