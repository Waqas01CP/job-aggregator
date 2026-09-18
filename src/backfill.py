"""ADR-0030's backfill: the rows the current rules admit that the filtered
layer never received.

**Why a gap exists.** A run writes a kept row only if its identity is new to
the seen store, because `split_new` runs before the write. When the rules
widen, rows the new rules admit never arrive: those postings were already
seen under the old rules, and no later run will offer them again.

**This is not a second writer with its own rules.** It reads the raw layer,
applies the same chain a run applies, and appends through
`storage.append_delta`, the same function into the same files. The one thing
it does differently is skip the seen-store check, which is the entire point.

**It lives in `src/` because the run calls it.** ADR-0030 wants the filtered
layer to track the rules in force, and the only place that can be guaranteed
is inside the run that writes the layer. `tools/backfill.py` is a thin
command-line wrapper over this module, for running it against a clone.

**ADR-0020 is enforced exactly as a run enforces it.** Aggregator rows go to
the local filtered file and publishable rows to the committed one, split by
`is_publishable` on the row's own source, never by filename.
"""
import glob
import os

from .config import is_publishable
from .filters import TitleMatcher, apply_chain
from .normalise import Row
from . import storage


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
    back, and the check must report exactly one row still missing.

    A record this code cannot read raises rather than being skipped. A skipped
    record would look exactly like a closed gap, which is the one outcome this
    pass must never fake."""
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
    """Append the gap. Returns counts, never raises on an empty gap.

    The counts are reported separately from a run's own writes, and that
    separation is deliberate. If the run's normal write path broke, the
    backfill would quietly write the same rows and the run would look healthy.
    A run whose own `written_filtered` is 0 while `backfilled` is 8 is a
    defect wearing a working run's clothes, and the two numbers are what make
    it visible."""
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
