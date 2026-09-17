"""The fetch run. Loads config, polls every board, writes both layers.

Exit codes, because the orchestrator needs to tell three things apart:

  0  finished
  1  could not start, or fetched and could not store the result
  2  stopped deliberately and resumable

Exit 1 has two causes because CLAUDE.md fixes the codes at three, and a
completed fetch that cannot be stored is neither a clean finish nor a
deliberate stop. The printed message says which cause it was. Run 35179218050
failed at the commit after fetching 1239 postings, and was reported as "could
not start" because nothing distinguished the two.

Two runs a day, early PKT morning and early PKT evening. ADR-0006.

**A run logs every board every run, including the ones that returned zero.**
A board returning nothing for a week is a broken adapter, and without a zero
logged it is indistinguishable from a quiet market.

Stopping is not failing. When the request budget is exhausted or the circuit
breaker opens, the run records which boards it did not reach and exits 2. The
next run picks them up, which is safe because ADR-0007 makes a late posting a
latency cost rather than a loss.
"""

import argparse
import os
import sys
import traceback
from datetime import datetime, timezone

from . import storage
from .adapters import greenhouse, himalayas, lever
from .config import ConfigError, is_publishable, load_boards
from .dedupe import counts as dedupe_counts
from .dedupe import group, split_new
from .filters import FilterError, TitleMatcher, apply_chain, drop_counts
from .http_client import (BudgetExhausted, CircuitOpen, HttpClient, HttpError)
from .normalise import dumps, iso, loads, normalise

EXIT_OK = 0
EXIT_CANNOT_START = 1
EXIT_STOPPED_RESUMABLE = 2

ADAPTERS = {"greenhouse": greenhouse, "lever": lever,
            "himalayas": himalayas}

# A paginated feed is read until it reaches postings already stored. The cap is
# a runaway guard on top of the stop rule, in the same spirit as ADR-0028.
MAX_PAGES = 25


class Run:
    def __init__(self, boards, client, now=None, test_mode=False, matcher=None):
        self.boards = boards
        self.client = client
        self.now = now or datetime.now(timezone.utc)
        self.test_mode = test_mode
        self.matcher = matcher or TitleMatcher()
        self.paths = storage.layout(test_mode)
        self.board_logs = []
        self.stopped = None

    # ------------------------------------------------------------ per board
    def poll(self, board, seen_first_seen):
        """Fetch, parse and normalise one board. Raises only for stop
        conditions; a board-level failure is recorded and the run continues,
        because one dead board must not cost the other ten."""
        adapter = ADAPTERS[board.platform]
        log = {"board": board.board_id, "fetched": 0, "parse_problems": 0,
               "new": 0, "kept": 0, "drops": {}, "status": "ok", "detail": None}
        try:
            if getattr(adapter, "PAGINATED", False):
                payload = self._fetch_pages(adapter, board, log)
            else:
                payload = self.client.get_json(adapter.url_for(board), board.source)
        except (BudgetExhausted, CircuitOpen) as stop:
            log["status"] = "not reached"
            log["detail"] = str(stop)
            self.board_logs.append(log)
            raise
        except HttpError as e:
            log["status"] = "failed"
            log["detail"] = str(e)
            self.board_logs.append(log)
            return []
        except Exception as e:
            # Distinct from "failed" on purpose: a board answering 500 is the
            # board's problem, an unexpected exception here is ours, and a run
            # log that spelled them the same would hide our own bugs among
            # theirs.
            log["status"] = "error"
            log["detail"] = "%s: %s" % (type(e).__name__, e)
            self.board_logs.append(log)
            return []

        try:
            parsed = adapter.parse(payload, board)
        except Exception as e:
            log["status"] = "unparseable"
            log["detail"] = "%s: %s" % (type(e).__name__, e)
            self.board_logs.append(log)
            return []

        log["fetched"] = len(parsed.postings)
        log["parse_problems"] = len(parsed.problems)
        rows = normalise(parsed.postings, board, self.now, seen=seen_first_seen)
        self.board_logs.append(log)
        self._log_for = log
        return rows

    def _fetch_pages(self, adapter, board, log):
        """Read a paginated feed newest-first until it reaches what is already
        stored, then stop. The anchor is the newest publication date actually
        stored for this source, never the previous run's clock: this feed is
        known to trail by at least 97.7 minutes, so a clock anchor would step
        over postings that arrive late and never look again."""
        high_water = self.high_water.get(board.source)
        merged, cursor, pages = {"jobs": []}, None, 0
        while pages < MAX_PAGES:
            payload = self.client.get_json(adapter.url_for(board, cursor), board.source)
            pages += 1
            merged["jobs"].extend(payload.get("jobs", []))
            if adapter.stop_after(payload, high_water):
                break
            cursor = adapter.next_cursor(payload)
            if not cursor:
                break
        log["pages"] = pages
        return merged

    # ---------------------------------------------------------------- main
    def execute(self):
        seen = storage.SeenStore.load_many([self.paths["seen"], self.paths["local_seen"]])
        first_seen = seen.first_seen_map()
        self.high_water = {}
        for entry in seen.entries.values():
            source, published = entry.get("source"), entry.get("published_at")
            if source and published:
                self.high_water[source] = max(self.high_water.get(source, ""), published)

        all_rows, reached = [], set()
        try:
            for board in self.boards:
                rows = self.poll(board, first_seen)
                reached.add(board.board_id)
                all_rows.extend(rows)
        except (BudgetExhausted, CircuitOpen) as stop:
            self.stopped = str(stop)

        # Every board gets a line, including the ones never reached.
        for board in self.boards:
            if board.board_id not in {l["board"] for l in self.board_logs}:
                self.board_logs.append({"board": board.board_id, "fetched": 0,
                                        "parse_problems": 0, "new": 0, "kept": 0,
                                        "drops": {}, "status": "not reached",
                                        "detail": self.stopped})

        new_rows, _ = split_new(all_rows, seen.identities)

        # Raw first: everything fetched is stored before anything is judged.
        by_source, source_class = {}, {}
        for row in new_rows:
            by_source.setdefault(row.source, []).append(row)
        for board in self.boards:
            source_class[board.source] = board.source_class
        raw_written = {}
        for source, rows in sorted(by_source.items()):
            raw_written[source] = storage.append_delta(
                storage.raw_path(source, self.test_mode,
                                 source_class.get(source, "ats")),
                [r.as_record() for r in rows])
        self.source_class = source_class

        kept, drops = apply_chain(all_rows, iso(self.now), matcher=self.matcher)
        kept_rows = [row for row, _ in kept]
        new_kept, _ = split_new(kept_rows, seen.identities)
        # ADR-0020 governs every store, so the filtered layer splits the same
        # way the raw layer does: an aggregator's kept rows are rows.
        filtered_local = storage.append_delta(
            self.paths["local_filtered"],
            [r.as_record() for r in new_kept if not is_publishable(r.source)])
        filtered_written = storage.append_delta(
            self.paths["filtered"],
            [r.as_record() for r in new_kept if is_publishable(r.source)]) + filtered_local

        for row in all_rows:
            seen.record(row)
            seen.mark_seen(row.identity, iso(self.now))
        public_seen, local_seen = seen.partition(is_publishable)
        public_seen.save(self.paths["seen"])
        local_seen.save(self.paths["local_seen"])

        per_board_drops = {}
        for d in drops:
            per_board_drops.setdefault(d["board_id"], {})
            per_board_drops[d["board_id"]][d["rule"]] = \
                per_board_drops[d["board_id"]].get(d["rule"], 0) + 1
        for log in self.board_logs:
            log["drops"] = per_board_drops.get(log["board"], {})
            log["new"] = sum(1 for r in new_rows if r.board_id == log["board"])
            log["kept"] = sum(1 for r in kept_rows if r.board_id == log["board"])

        run_log = {
            "run_at": iso(self.now),
            "test_mode": self.test_mode,
            "boards": sorted(self.board_logs, key=lambda l: l["board"]),
            "totals": {
                "fetched": sum(l["fetched"] for l in self.board_logs),
                "new": len(new_rows),
                "kept": len(kept_rows),
                "written_raw": raw_written,
                "written_filtered": filtered_written,
                "written_filtered_local": filtered_local,
                "drops": drop_counts(drops),
                "dedupe": dedupe_counts(group(all_rows)),
            },
            "requests": self.client.counters(),
            "stopped": self.stopped,
            "source_class": dict(self.source_class),
        }
        return run_log

    def exit_code(self):
        return EXIT_STOPPED_RESUMABLE if self.stopped else EXIT_OK


def summarise(run_log):
    """One line per board, including zeros, then the totals."""
    lines = ["run at %s%s" % (run_log["run_at"],
                              "  TEST MODE" if run_log["test_mode"] else "")]
    for b in run_log["boards"]:
        drops = ", ".join("%s=%d" % (k, v) for k, v in sorted(b["drops"].items()))
        lines.append("  %-34s %-12s fetched %4d  new %4d  kept %3d  %s%s"
                     % (b["board"], b["status"], b["fetched"], b["new"], b["kept"],
                        drops or "no drops",
                        "  [%s]" % b["detail"] if b["detail"] else ""))
    t = run_log["totals"]
    lines.append("  totals: fetched %d, new %d, kept %d, raw %s, filtered %d (%d of them local only)"
                 % (t["fetched"], t["new"], t["kept"], t["written_raw"],
                    t["written_filtered"], t["written_filtered_local"]))
    lines.append("  drops by rule: %s" % t["drops"])
    lines.append("  dedupe: %s" % t["dedupe"])
    r = run_log["requests"]
    lines.append("  requests: %d of %d, by source %s, retries %d, failures %d"
                 % (r["requests_used"], r["budget"], r["by_source"],
                    r["retries"], r["failures"]))
    if run_log["stopped"]:
        lines.append("  STOPPED: %s. Unreached boards resume next run." % run_log["stopped"])
    return "\n".join(lines)


def files_to_commit(run_log, paths, log_path, test_mode):
    """What goes to the data branch.

    **An aggregator's raw file never does.** ADR-0020: two feeds prohibit
    redistribution and a branch inherits its repository's visibility, so those
    rows stay in a local directory. This is the last gate before a push, and
    it selects by source class rather than by filename, because a filename
    convention is one rename away from leaking.

    **Nor does any record of theirs inside a shared file.** Selecting files was
    not enough: until 2026-09-17 the filtered layer and seen store were single
    files holding every source, offered here unconditionally. The first GitHub
    run kept 18 Himalayas rows and saw 500 Himalayas postings, and only its
    failure to commit kept them off the public branch; a local simulation of
    the same workflow steps, given an identity, pushed them. So every record
    file offered is read and refused if it holds a record whose source may not
    be published. The run writes them split; this is the check that the split
    held, including for files written before it existed."""
    files = {}
    for source in sorted(run_log["totals"]["written_raw"]):
        if not is_publishable(source):
            continue
        path = storage.raw_path(source, test_mode, "ats")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                files[storage.branch_path(path, test_mode)] = f.read()
    for path in (paths["filtered"], paths["seen"], log_path):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                files[storage.branch_path(path, test_mode)] = f.read()
    for committed_path, text in sorted(files.items()):
        if committed_path.startswith(storage.RUNLOG_DIR + "/"):
            continue
        records = loads(text)
        entries = records.values() if isinstance(records, dict) else records
        refused = sorted({str(e.get("source")) for e in entries
                          if not is_publishable(e.get("source"))})
        if refused:
            raise storage.StorageError(
                "refusing to commit %s: it holds records from %s, which ADR-0020 "
                "keeps off the data branch" % (committed_path, ", ".join(refused)))
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="One fetch run.")
    parser.add_argument("--test-mode", action="store_true",
                        help="write to alternate files, leaving production data alone")
    parser.add_argument("--budget", type=int, default=None,
                        help="override the per-run request ceiling (ADR-0028)")
    parser.add_argument("--no-commit", action="store_true",
                        help="write files but do not commit to the data branch")
    args = parser.parse_args(argv)

    test_mode = args.test_mode or os.environ.get("TEST_MODE") == "1"

    try:
        boards = load_boards()
        matcher = TitleMatcher()
    except (ConfigError, FilterError) as e:
        print("could not start: %s" % e, file=sys.stderr)
        return EXIT_CANNOT_START

    # A run that commits starts from the branch, so that it appends to what is
    # stored rather than to whatever this machine happens to hold. A no-commit
    # run is exploratory and chains from the local files, as it always has.
    branch = storage.data_branch(test_mode)
    if not args.no_commit:
        try:
            restored = storage.restore_from_branch(test_mode)
        except Exception as e:
            print("could not start: reading state from the %s branch failed: %s"
                  % (branch, e), file=sys.stderr)
            return EXIT_CANNOT_START
        print("state: %s" % ("%d file(s) restored from the %s branch" % (len(restored), branch)
                             if restored else "no %s branch, starting from local files" % branch))

    client = HttpClient(**({"budget": args.budget} if args.budget else {}))
    run = Run(boards, client, test_mode=test_mode, matcher=matcher)
    try:
        run_log = run.execute()
    except Exception:
        traceback.print_exc()
        print("could not complete the run: the exception above was raised before "
              "anything was committed", file=sys.stderr)
        return EXIT_CANNOT_START

    print(summarise(run_log))

    stage = "writing the run log"
    try:
        stamp = run_log["run_at"].replace(":", "").replace("-", "")
        log_path = "%s/%s.json" % (run.paths["runlog_dir"], stamp)
        storage.write_atomic(log_path, dumps(run_log))

        if not args.no_commit:
            stage = "committing to the %s branch" % branch
            files = files_to_commit(run_log, run.paths, log_path, test_mode)
            sha = storage.commit_files(files, "run %s" % run_log["run_at"], branch=branch)
            print("  %s branch: %s" % (branch, sha or "nothing changed, no commit"))
    except Exception:
        traceback.print_exc()
        print("the fetch completed and its files are written locally, but %s "
              "failed, so nothing was committed" % stage, file=sys.stderr)
        return EXIT_CANNOT_START

    return run.exit_code()


if __name__ == "__main__":
    sys.exit(main())
