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
"""

import argparse
import os
import sys
import traceback
from datetime import datetime, timezone

from . import envfile, storage
from .adapters import greenhouse, himalayas, lever
from .config import load_boards
from .http_client import HttpClient, HttpError
from .normalise import dumps, iso, loads

PLATFORMS = {"greenhouse": greenhouse, "lever": lever, "himalayas": himalayas}

FINGERPRINT_FILE = "contract/fingerprint.json"
LOG_DIR = "logs-contract"

# One request per platform, and a little room: the shared client counts every
# attempt, including retries, against this.
BUDGET = 2 * len(PLATFORMS)

TYPE_NAMES = {bool: "boolean", int: "number", float: "number", str: "string",
              list: "array", dict: "object"}


def resolve(obj, path):
    """(present, value) for a dotted path. A step through anything that is not
    an object is absent, not an error: a null `location` makes
    `location.name` absent, which is itself a shape worth recording."""
    for part in path.split("."):
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


def first_board(boards, platform):
    return next((b for b in boards if b.platform == platform), None)


def check(boards, client, stored, now):
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
        if previous is None:
            entry["status"] = "baseline"
        else:
            entry["changes"] = compare(previous, fp)
            entry["status"] = "changed" if entry["changes"] else "unchanged"
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
            lines.append("    %s field %s: was %s, now %s" % (c["in"], c["field"],
                                                           c["was"], c["now"]))
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
        updated, log = check(boards, HttpClient(budget=BUDGET), stored, now)
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
