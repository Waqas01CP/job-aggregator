"""The contract check. ADR-0018 and ADR-0036.

Every input here is a third-party API nobody here controls, and the cassette
tests replay a recorded response, so they keep passing after a board has
changed. The changes that matter raise nothing: a field starts arriving null,
a type changes, a field disappears. The run completes and its output is
quietly wrong or empty.

So once a day, apart from the fetch, this asks one board per platform for one
response and fingerprints the fields the adapter consumes: for each, whether
it is present in every posting, some or none, whether it is null never, in
some or always, and the types it arrives as. The fingerprint is compared with
the last one stored on the data branch and every difference is named.

**Only the consumed fields.** Each adapter declares them in `CONSUMED`, and a
test holds that list to what `parse()` actually reads, so a board adding or
changing a field the pipeline ignores never raises anything (ADR-0018's
Tolerant Reader).

**A finding is not a failure.** ADR-0036: the check writes what changed to
its own run log on the data branch and exits 0. Exit 1 means the check itself
crashed, and then it writes no log at all, so a crash can never be read as a
finding or a finding as a crash. A board that cannot be reached is neither:
it is logged, its last fingerprint is kept, and the next check compares
against that.

**Its logs have their own directory**, `logs-contract/`, never `logs-runs/`.
The fetch run counts failed projections in a row from the logs in
`logs-runs/`, and a contract log there would read as a run that succeeded and
reset the count.

**Structure only, never content.** A fingerprint holds field names, type
names and three-way presence words. No value from any posting is stored, so
Himalayas' fingerprint can sit on the public branch beside the others: its
field names are already public in `src/adapters/himalayas.py`.

The first check of a platform records a baseline and gives no verdict; only
the second onward can detect a change.

**A change we caused is ours, and says so.** ADR-0036, 2026-09-28: when an
endpoint or the fields an adapter reads change, the diff the next check
reports is not the board moving. `config/contract_rebaselines.json` records
each such change, with the UTC time it was committed to `main`, its cause and
the fields it moves, in the same commit as the change. A difference matching
an entry newer than the shape it replaces is marked ours and the platform
reads `re-baselined`; any other difference still reads `changed`. Each stored
shape carries the time it was accepted, so an old entry can never excuse a
later change to the same field. On 2026-09-27 the check reported four
Himalayas fields changed that ADR-0053's move to the search endpoint had
caused, with nothing to say so.

**Times, not dates.** ADR-0036, 2026-10-03. With calendar dates, a change
reaching `main` on the day a shape was accepted, after that day's check, had
no date both true and later than the acceptance, so the next check would
have called our own change the board's. A time orders the two within the day.
"""

import argparse
import os
import sys
import traceback
from datetime import datetime, timezone

from . import envfile, storage
from .adapters import greenhouse, himalayas, lever
from .config import REPO_ROOT, ConfigError, load_boards
from .http_client import HttpClient, HttpError
from .normalise import dumps, iso, loads

PLATFORMS = {"greenhouse": greenhouse, "lever": lever, "himalayas": himalayas}

FINGERPRINT_FILE = "contract/fingerprint.json"
REBASELINES_PATH = os.path.join(REPO_ROOT, "config", "contract_rebaselines.json")
LOG_DIR = "logs-contract"

# One request per platform, and a little room: the shared client counts every
# attempt, including retries, against this.
BUDGET = 2 * len(PLATFORMS)

TYPE_NAMES = {bool: "boolean", int: "number", float: "number", str: "string",
              list: "array", dict: "object"}


def resolve(obj, path):
    """(present, value) for a dotted path. A step through anything that is not
    an object is absent, not an error: a null `location` makes
    `location.name` absent, which is itself a shape worth recording.

    **A step into a list reads its items**: the rest of the path in each,
    present when any item has it, with the first value found. Greenhouse's
    `offices.location` and `metadata.value` are read that way since
    2026-10-02; resolved as absent, they would fingerprint nothing, and a
    renamed field inside them would never show."""
    parts = path.split(".")
    for i, part in enumerate(parts):
        if isinstance(obj, list):
            for item in obj:
                present, value = resolve(item, ".".join(parts[i:]))
                if present:
                    return True, value
            return False, None
        if not isinstance(obj, dict) or part not in obj:
            return False, None
        obj = obj[part]
    return True, obj


def type_name(value):
    return "null" if value is None else TYPE_NAMES.get(type(value), type(value).__name__)


def shape(observed):
    """One field's shape across `observed`, a list of (present, value).
    Words rather than counts, because counts move every day with the
    postings and a fingerprint that moves daily is noise."""
    n = len(observed)
    present = [v for p, v in observed if p]
    nulls = sum(1 for v in present if v is None)

    def word(k, whole, none_word, all_word):
        return none_word if k == 0 else all_word if k == whole else "some"

    return {"present": word(len(present), n, "none", "all"),
            "null": word(nulls, len(present), "never", "always") if present else "never",
            "types": sorted({type_name(v) for v in present if v is not None})}


def postings_in(adapter, payload):
    """The postings a response carries: under the adapter's POSTINGS_AT, or
    the response itself when that is None. Anything else is a change of
    contract, and returns None."""
    found = payload if adapter.POSTINGS_AT is None else (
        payload.get(adapter.POSTINGS_AT) if isinstance(payload, dict) else None)
    return found if isinstance(found, list) else None


def fingerprint(adapter, payload):
    """{"response": {path: shape}, "posting": {path: shape}}, and the number
    of postings it was taken over. The count goes to the log, never into the
    fingerprint."""
    postings = postings_in(adapter, payload)
    response = {path: shape([resolve(payload, path)]) for path in adapter.CONSUMED_RESPONSE}
    entries = [p for p in (postings or []) if isinstance(p, dict)]
    posting = {path: shape([resolve(p, path) for p in entries])
               for path in adapter.CONSUMED} if entries else {}
    return {"response": response, "posting": posting}, len(entries)


def compare(before, after):
    """Every field whose shape differs, named, with both shapes. A field in
    one fingerprint and not the other is a change too: that is the case
    ADR-0018's Confirmation builds by hand-editing a stored fingerprint."""
    changes = []
    for section in ("response", "posting"):
        old, new = before.get(section) or {}, after.get(section) or {}
        for path in sorted(set(old) | set(new)):
            if old.get(path) != new.get(path):
                changes.append({"field": path, "in": section,
                                "was": old.get(path, "not in the stored fingerprint"),
                                "now": new.get(path, "not in this fingerprint")})
    return changes


def load_rebaselines(path=None):
    """The recorded re-baselines, each checked for what explaining a
    difference needs. A malformed entry stops the check rather than excusing
    a change it was never meant to."""
    import json
    with open(path or REBASELINES_PATH, encoding="utf-8") as f:
        doc = json.load(f)
    entries = doc.get("rebaselines") if isinstance(doc, dict) else None
    if not isinstance(entries, list):
        raise ConfigError("contract re-baselines: expected a 'rebaselines' list")
    for i, e in enumerate(entries):
        if not (isinstance(e, dict) and e.get("platform") in PLATFORMS
                and real_time(e.get("at"))
                and e.get("cause") and isinstance(e.get("fields"), list) and e["fields"]):
            raise ConfigError("contract re-baseline %d needs a platform, a UTC time written "
                              "YYYY-MM-DDTHH:MM:SSZ, a cause and the fields it moves" % i)
    return entries


def real_time(value):
    """A UTC time written YYYY-MM-DDTHH:MM:SSZ, or None. Twenty characters
    are not enough: the fourth audit loaded "2026-19-26" and "9999-99-99" as
    dates, each able to excuse changes it was never written for."""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if len(value) == 20 else None


def accepted_at(since):
    """When a stored shape was accepted, or None when that is unknown.

    **A shape accepted before times were kept carries only its day**, and is
    read as that day's last second, which is what the date rule meant: an
    entry of the same day excuses nothing. It gains its time on its next
    change."""
    if not isinstance(since, str):
        return None
    try:
        if len(since) == 10:
            day = datetime.strptime(since, "%Y-%m-%d")
            return day.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        return datetime.fromisoformat(since.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def explain(platform, changes, rebaselines, since, now):
    """Mark each change a recorded re-baseline accounts for: same platform,
    the field named, committed after the stored shape was accepted and not
    after this check.

    **A shape whose acceptance is unknown is never excused.** Shapes stored
    before 2026-09-30 carry none, and reading the gap as "older than
    everything" let the entry of 2026-09-26, already spent on the check of
    09-27, excuse any change to its four fields on the next check: the fourth
    audit's F5. Such a shape gains its time on the first check that reads it.
    **An entry timed after this check excuses nothing yet**, so a mistyped
    future time cannot hold a field open."""
    accepted = accepted_at(since)
    if accepted is None:
        return changes
    for c in changes:
        name = "%s.%s" % (c["in"], c["field"])
        for e in rebaselines:
            if e["platform"] == platform and name in e["fields"] \
                    and accepted < real_time(e["at"]) <= now:
                c["ours"] = "%s: %s" % (e["at"], e["cause"])
                break
    return changes


def first_board(boards, platform):
    return next((b for b in boards if b.platform == platform), None)


def check(boards, client, stored, now, rebaselines=()):
    """One check. Returns (the new fingerprint file, the log). Never reaches
    the branch; main does. A board that cannot be answered keeps its old
    fingerprint and is logged as such."""
    updated = dict(stored)
    log = {"run_at": iso(now), "platforms": {}}
    for platform, adapter in PLATFORMS.items():
        board = first_board(boards, platform)
        if board is None:
            log["platforms"][platform] = {"status": "no board configured"}
            continue
        entry = {"board": board.board_id}
        log["platforms"][platform] = entry
        try:
            payload = client.get_json(adapter.url_for(board), board.source)
        except HttpError as e:
            entry.update(status="unreachable", detail=str(e))
            continue
        fp, count = fingerprint(adapter, payload)
        entry["postings"] = count
        if not count:
            # Nothing to fingerprint the postings over. The response's own
            # fields are still compared, since a renamed list lands here.
            fp["posting"] = (stored.get(platform) or {}).get("posting", {})
        previous = stored.get(platform)
        since = (previous or {}).get("since")
        if previous is None:
            entry["status"] = "baseline"
        else:
            entry["changes"] = explain(platform, compare(previous, fp), rebaselines, since, now)
            entry["status"] = ("unchanged" if not entry["changes"] else
                               "re-baselined" if all(c.get("ours") for c in entry["changes"])
                               else "changed")
        # When this shape was accepted: now for a new or changed one, and for
        # a stored one written before the acceptance was kept, so no entry
        # older than the shape in force can explain a later change.
        fp["since"] = iso(now) if previous is None or entry.get("changes") or not since \
            else since
        updated[platform] = fp
    return updated, log


def summarise(log):
    lines = ["contract check at %s%s" % (log["run_at"], "  TEST MODE" if log.get("test_mode")
                                        else "")]
    for platform, entry in log["platforms"].items():
        lines.append("  %-11s %-12s %s%s" % (
            platform, entry["status"], entry.get("board", ""),
            "  %d posting(s)" % entry["postings"] if "postings" in entry else ""))
        for c in entry.get("changes") or []:
            lines.append("    %s field %s: was %s, now %s%s" % (
                c["in"], c["field"], c["was"], c["now"],
                "  [ours, %s]" % c["ours"] if c.get("ours") else ""))
        if entry.get("detail"):
            lines.append("    %s" % entry["detail"])
    return "\n".join(lines)


def read_stored(test_mode, no_commit):
    """The last fingerprint: from the branch for a committing check, from the
    local copy for a no-commit one, as the fetch run does."""
    if no_commit:
        path = "%s/%s" % (storage.data_root(test_mode), FINGERPRINT_FILE)
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as f:
            text = f.read()
    else:
        text = storage.read_branch_file(FINGERPRINT_FILE, storage.data_branch(test_mode))
    return loads(text) if text else {}


def main(argv=None, now=None):
    parser = argparse.ArgumentParser(description="The daily contract check.")
    parser.add_argument("--test-mode", action="store_true",
                        help="read and write the data-test branch")
    parser.add_argument("--no-commit", action="store_true",
                        help="write the files locally and commit nothing")
    args = parser.parse_args(argv)
    envfile.load()
    test_mode = args.test_mode or os.environ.get("TEST_MODE") == "1"

    try:
        boards = load_boards()
        stored = read_stored(test_mode, args.no_commit)
        now = now or datetime.now(timezone.utc)
        updated, log = check(boards, HttpClient(budget=BUDGET), stored, now,
                             load_rebaselines())
        log["test_mode"] = test_mode
        print(summarise(log))

        root = storage.data_root(test_mode)
        stamp = log["run_at"].replace(":", "").replace("-", "")
        files = {FINGERPRINT_FILE: dumps(updated),
                 "%s/%s.json" % (LOG_DIR, stamp): dumps(log)}
        for path, text in files.items():
            storage.write_atomic("%s/%s" % (root, path), text)
        if not args.no_commit:
            branch = storage.data_branch(test_mode)
            sha = storage.commit_files(files, "contract check %s" % log["run_at"], branch=branch)
            print("  %s branch: %s" % (branch, sha or "nothing changed, no commit"))
    except Exception:
        traceback.print_exc()
        print("the contract check itself failed; this is not a finding about any board",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
