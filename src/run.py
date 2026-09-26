"""The fetch run. Loads config, polls every board, writes both layers.

Exit codes, because the orchestrator needs to tell three things apart:

  0  finished
  1  could not start, or fetched and could not store the result
  2  stopped deliberately and resumable, the projection to Airtable failed,
     or the private store could not be restored or written

Exit 1 has two causes because CLAUDE.md fixes the codes at three, and a
completed fetch that cannot be stored is neither a clean finish nor a
deliberate stop. The printed message says which cause it was. Run 35179218050
failed at the commit after fetching 1239 postings, and was reported as "could
not start" because nothing distinguished the two.

**A failed projection exits 2, not 1.** The operator's decision of
2026-09-23, recorded in ADR-0034's Changes. Exit 1 stops the workflow's push,
which would lose the run's fetched data for a display failure, while ADR-0040
re-projects the whole layer every run, so the next run repairs the display by
construction. The run records the failure in its log, commits, and exits 2.

**So does a private store that cannot be restored or written.** The
operator's decision of 2026-09-24, D6: the public fetch is kept, the run log's
`private_store` block names the failure, and the aggregator boards are not
polled, because nothing they returned could be kept. ADR-0047's "fail
visibly" is the run log, the workflow's warning, and after three runs in a row
a failed run.

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

from . import envfile, private_store, projection, storage
from .airtable_sweep import SweepClient, TABLE_SECRETS
from .closure import Closure
from .sweep import Sweep, older_than
from .adapters import greenhouse, himalayas, lever
from .airtable import (BASE_ENV, RUN_LOG_KEY, TABLE_ENV, TEST_TABLE_ENV, TOKEN_ENV,
                       AirtableClient, month_to_date)
from .backfill import backfill
from .config import ConfigError, is_publishable, load_boards, load_sweep_config
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

# Every value that must never reach a run log or the console: the run log is
# committed to the public data branch. Scrubbed from any projection failure
# before it is recorded, as a last line behind the clients' own discipline.
SECRET_ENVS = (TOKEN_ENV, BASE_ENV, TABLE_ENV, TEST_TABLE_ENV,
               storage.PRIVATE_STORE_TOKEN_ENV, storage.PRIVATE_STORE_REPO_ENV) + tuple(
    name for mode in (False, True) for key, name in sorted(TABLE_SECRETS[mode].items())
    if key != "jobs")


# The operator's decision of 2026-09-24: a failure that is resumable exits 2
# and shows as a green run, so one that repeats would look healthy for a week.
# On the third run in a row the run still commits and pushes, then the
# workflow's last step marks it failed. A single failure stays quiet.
ESCALATE_AFTER = 3


def needs_attention(run_log):
    """A run whose display, sweep or private store failed, which exit 2
    hides. A log that is not an object needs none, so attention() can never
    raise on one: it runs before the commit. The sweep counts because a
    sweep that silently does nothing lets `Jobs` fill to the record cap."""
    if not isinstance(run_log, dict):
        return False
    for block in (run_log.get(RUN_LOG_KEY), run_log.get("private_store"),
                  run_log.get("sweep")):
        if isinstance(block, dict) and block.get("failure"):
            return True
    return False


def private_store_failed(run_log):
    block = run_log.get("private_store") if isinstance(run_log, dict) else None
    return isinstance(block, dict) and bool(block.get("failure"))


def attention(run_log, test_mode, no_commit):
    """How many runs in a row, this one included, have needed attention, and
    whether the workflow should mark this one failed. Reads the previous logs
    from the branch; a no-commit run neither reads the branch nor escalates.
    Never raises: failing to count must not cost the run its commit.

    **A private-store failure escalates at once.** The operator's decision of
    2026-09-24, D9: he wants to hear so it can be fixed, and its causes, an
    expired or revoked token or a moved repository, do not clear on their
    own. A projection failure still waits for ESCALATE_AFTER runs, because
    Airtable's own errors often do."""
    if not needs_attention(run_log):
        return {"failed_in_a_row": 0, "escalate": False}
    at_once = private_store_failed(run_log)
    if no_commit:
        return {"failed_in_a_row": 1, "escalate": False}
    try:
        previous = storage.read_recent_run_logs(ESCALATE_AFTER - 1, test_mode)
    except Exception as e:
        return {"failed_in_a_row": 1, "escalate": at_once,
                "note": "previous run logs unreadable: %s" % type(e).__name__}
    streak = 1
    for log in reversed(previous):
        if not needs_attention(log):
            break
        streak += 1
    return {"failed_in_a_row": streak, "escalate": streak >= ESCALATE_AFTER or at_once}


def tell_the_workflow(name, value):
    """A step output for the workflow, when running inside one."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("%s=%s\n" % (name, value))


def make_airtable_client(test_mode, used_this_month):
    """The one place the run builds its Airtable client. Tests replace it with
    a fake transport, so no unit test can reach a live base."""
    return AirtableClient.from_env(test_mode, used_this_month=used_this_month)


def make_private_store(test_mode):
    """The one place the run builds its private store. Tests replace it with
    a local bare repository, so no unit test can reach GitHub."""
    return private_store.PrivateStore(os.environ.get(storage.PRIVATE_STORE_REPO_ENV),
                                      os.environ.get(storage.PRIVATE_STORE_TOKEN_ENV),
                                      test_mode=test_mode)


def open_private_store(paths, test_mode):
    """Open the private store and restore the aggregator working copies from
    it. ADR-0047. Returns (the store or None, the run log's block).

    Never raises. On any failure it returns no store, so the run has nothing
    to write with: **a run that could not restore never writes**, since
    pushing after a failed restore would replace the stored history with one
    run's snapshot, ADR-0003's failure."""
    block = {"branch": storage.data_branch(test_mode), "restored": 0, "pushed": None,
             "failure": None}
    store = None
    try:
        store = make_private_store(test_mode)
        store.open()
        block["restored"] = len(store.restore(paths))
        return store, block
    except Exception as e:
        if store is not None:
            store.close()
        block["failure"] = redact_secrets("%s: %s" % (type(e).__name__, e))
        return None, block


def save_private_store(store, block, paths, run_at, key="pushed"):
    """Commit and push the run's aggregator files. Never raises; a failure is
    recorded in the block and the run exits 2. Called twice: once after the
    fetch, so the data goes first, and once after the sweep, for the
    aggregator outcomes it wrote, recorded under `key`. The caller closes
    the store."""
    if store is None:
        return
    try:
        files = private_store.files_to_push(paths)
        if key == "pushed":
            block["files"] = len(files)
        block[key] = bool(files and store.commit_and_push(files, "run %s" % run_at))
    except Exception as e:
        block["failure"] = redact_secrets("%s: %s" % (type(e).__name__, e))


def save_full_postings(run, store, block, run_at):
    """D11: every posting this run fetched that the private full branch does
    not hold yet, saved whole, descriptions included, as one file, and read
    back. Only then are the postings marked saved in both seen stores, so
    a failed save is retried by the next run that sees them listed. Never
    raises: a failure is the private store's failure, recorded in its block,
    so the run exits 2 and is marked failed at once (D9)."""
    pending = run.full_pending
    out = {"pending": len(pending), "saved": 0, "file": None, "verified": False,
           "failure": None}
    block["full"] = out
    if store is None:
        out["held"] = "the private store could not be restored; the next run saves them"
        return
    if not pending:
        return
    path = "%s/%s.json" % (storage.FULL_DIR,
                           run_at.replace(":", "").replace("-", ""))
    text = dumps(pending)
    try:
        store.save_full(path, text, "full postings %s" % run_at)
    except Exception as e:
        out["failure"] = redact_secrets("%s: %s" % (type(e).__name__, e))
        block["failure"] = block["failure"] or (
            "the full postings could not be saved: %s" % out["failure"])
        return
    saved = {r["identity"] for r in pending}
    for key in ("seen", "local_seen"):
        seen = storage.SeenStore.load(run.paths[key])
        for identity in saved & set(seen.entries):
            seen.mark_full_saved(identity, run_at)
        seen.save(run.paths[key])
    out.update(saved=len(pending), file=path, verified=True, bytes=len(text.encode("utf-8")))


def redact_secrets(text, environ=None):
    """Every secret the run holds, scrubbed, including the private store's
    token in the encoded form git sends it in. The audit of 2026-09-24 put an
    exception quoting that encoded header through the run, and it reached the
    run log intact while the raw token was scrubbed."""
    environ = os.environ if environ is None else environ
    for name in SECRET_ENVS:
        value = (environ.get(name) or "").strip()
        if value:
            text = text.replace(value, "<%s>" % name)
    token = (environ.get(storage.PRIVATE_STORE_TOKEN_ENV) or "").strip()
    if token:
        text = text.replace(storage.private_store_basic(token),
                            "<%s, encoded>" % storage.PRIVATE_STORE_TOKEN_ENV)
    return text


def month_so_far(now_iso, test_mode):
    """The month's Airtable calls per branch, projection and sweep together.
    The allowance is per workspace, so both modes' branches count (G7)."""
    month = now_iso[:7].replace("-", "")
    return {storage.data_branch(mode): month_to_date(
        storage.read_month_run_logs(month, mode), now_iso)
        for mode in (test_mode, not test_mode)}


def closure_for(run, boards, test_mode, no_commit, run_log, config):
    """ADR-0050's closure test over this run's state: last seen from both
    seen stores, and the recent run logs with this run's own appended. A
    no-commit run reads no branch and judges from this run alone."""
    seen = storage.SeenStore.load_many([run.paths["seen"], run.paths["local_seen"]])
    last_seen = {k: v.get("last_seen") for k, v in seen.entries.items()}
    logs = [] if no_commit else storage.read_recent_run_logs(config.run_log_window, test_mode)
    paginated = {b.board_id: bool(getattr(ADAPTERS[b.platform], "PAGINATED", False))
                 for b in boards}
    return Closure(last_seen, logs + [run_log], lambda board_id: paginated.get(board_id, False),
                   config.closed_after_polled_runs, iso(run.now))


def retired_by(closure, config, now):
    """Whether a display group closed more than the retirement span ago."""
    def retired(g):
        day = closure.group_closed_on(g.members)
        return day is not None and older_than(day + "T00:00:00Z", config.retire_after_days, now)
    return retired


def project_display(run, no_commit, test_mode, restore_failure=None, retired=None):
    """Project the filtered layer to `Jobs`, or to `Jobs test` in test mode.

    Returns (projection stages, the airtable block, failure or None). Never
    raises: a failed projection is recorded, the run still commits, and the
    caller exits 2.

    **A private store that could not be restored withholds only the
    aggregator rows.** The operator's decision of 2026-09-24, D9: the public
    rows always update. Until then the whole projection failed, the seat's
    first design, so one expired token froze the display. The private
    outcome stores are unknown, so the aggregator rows are held back rather
    than projected against stores that might retire them. A group mixing a
    public row with an aggregator one retired only in the private store would
    come back. ADR-0001's key includes the publication date and an
    aggregator stamps its own, which is why the Motive role sits in `Jobs`
    twice rather than merged, so such a group is not expected; none has been
    looked for.

    **The month's Airtable calls are counted from both branches.** The
    allowance is per workspace and both modes spend it. The operator's go of
    2026-09-24, G7: before it, production counted 5 calls while the workspace
    had spent 22.

    **A no-commit run reaches no base and no private store.** It plans the
    projection from the local files and sends nothing, so the counts can be
    checked offline."""
    now_iso = iso(run.now)
    stages = {}
    client = None
    try:
        if no_commit:
            stages["mode"] = "dry run: a no-commit run reaches no base and no private store"
            records = projection.plan(projection.load_rows(run.paths), now_iso, run.matcher,
                                      projection.identities_in(
                                          projection.public_store_texts(run.paths)
                                          + projection.private_store_texts(run.paths)), stages,
                                      retired=retired)
            return stages, {"calls_used": 0, "rows_sent": 0, "failure": None,
                            "would_send": len(records)}, None

        by_branch = month_so_far(now_iso, test_mode)
        client = make_airtable_client(test_mode, sum(by_branch.values()))
        projection.project(run.paths, now_iso, run.matcher, client,
                           projection.private_store_texts(run.paths), stages,
                           public_only=bool(restore_failure), retired=retired)
        return stages, dict(client.counters(), failure=None,
                            month_to_date_by_branch=by_branch), None
    except Exception as e:
        failure = "%s: %s" % (type(e).__name__, e)
        if client is not None:
            failure = client.redact(failure)
        failure = redact_secrets(failure)
        block = dict(client.counters()) if client is not None else {"calls_used": 0,
                                                                    "rows_sent": 0}
        block["failure"] = failure
        return stages, block, failure


def make_sweep_client(test_mode, used_this_month):
    """The one place the run builds the sweep's client. Tests replace it."""
    return SweepClient.from_env(test_mode, used_this_month=used_this_month)


def previous_run_at(test_mode):
    """When the previous run on this branch ran, or None. A copy-only sweep
    reads the classification tables only if a status moved since."""
    try:
        logs = storage.read_recent_run_logs(1, test_mode)
    except Exception:
        return None
    return logs[-1].get("run_at") if logs and isinstance(logs[-1], dict) else None


def sweep_display(run, no_commit, test_mode, slot, private_ok, closure, config, used_before,
                  closure_failure=None):
    """ADR-0050's sweep. The copy step runs on every committing run; the
    daily steps run except on the evening slot. Never raises: a failure is
    recorded, the run still commits, and the caller exits 2.

    **The copy needs no closure test.** When it could not be built the copy
    still runs and the daily steps do not, and the run fails as a sweep
    failure so it is seen (the audit of 2026-09-25, nit 4).

    **A no-commit run reaches no base.** It sweeps nothing."""
    if no_commit:
        return {"mode": "dry run: a no-commit run reaches no base", "calls_used": 0,
                "failure": None}
    daily = slot != "evening" and closure_failure is None
    client = None
    try:
        client = make_sweep_client(test_mode, used_before)
        report = Sweep(client, run.paths, run.now, run.matcher, closure, config,
                       private_ok).run(daily, since=None if daily else previous_run_at(test_mode))
        report.update(client.counters())
        report["failure"] = None if closure_failure is None else (
            "the closure test could not be built, so only the copy ran: %s" % closure_failure)
        return report
    except Exception as e:
        failure = "%s: %s" % (type(e).__name__, e)
        if client is not None:
            failure = client.redact(failure)
        block = dict(client.counters()) if client is not None else {"calls_used": 0}
        block.update(daily=daily, failure=redact_secrets(failure))
        return block


def budget_line(run_log, by_branch, config, now):
    """ADR-0050's guard: the month to date, and a loud line once it passes
    the configured share of the allowance before the configured day. Airtable
    warns of nothing, and its grace period is available once ever (ADR-0004).
    """
    spent = sum(by_branch.values())
    for key in (RUN_LOG_KEY, "sweep"):
        spent += int((run_log.get(key) or {}).get("calls_used") or 0)
    allowance = int((run_log.get(RUN_LOG_KEY) or {}).get("monthly_ceiling") or 1000)
    block = {"month_to_date": spent, "allowance": allowance,
             "share": round(spent / allowance, 3), "warning": None}
    if spent > config.budget_warning_share * allowance and now.day < config.budget_warning_before_day:
        block["warning"] = ("the month's Airtable calls are at %d of %d, past %d%% before day %d"
                            % (spent, allowance, round(config.budget_warning_share * 100),
                               config.budget_warning_before_day))
    return block


class Run:
    def __init__(self, boards, client, now=None, test_mode=False, matcher=None, slot=None,
                 private_unavailable=None):
        self.boards = boards
        self.client = client
        self.now = now or datetime.now(timezone.utc)
        self.test_mode = test_mode
        self.matcher = matcher or TitleMatcher()
        self.paths = storage.layout(test_mode)
        self.board_logs = []
        self.stopped = None
        # D11: each posting as the board returned it, by identity, and the ones
        # the private full branch does not hold yet.
        self.full = {}
        self.full_pending = []
        # ADR-0048: which scheduled slot this run is, from the workflow. None
        # for a dispatch or a local run, which polls every board.
        self.slot = slot
        # ADR-0047: why the private store is unavailable, or None. An
        # aggregator polled without it would keep nothing and be first
        # contact next time too, so it is not polled.
        self.private_unavailable = private_unavailable

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
        # D11: the posting whole, for the private full branch. Keyed the way
        # the normaliser keys a row, so only what became a row is kept.
        raw = {"%s:%s" % (p.source, p.external_id): p.raw
               for p in parsed.postings if p.raw is not None}
        for row in rows:
            if row.identity in raw:
                self.full[row.identity] = {"identity": row.identity, "source": row.source,
                                           "board_id": row.board_id,
                                           "fetched_at": iso(self.now),
                                           "posting": raw[row.identity]}
        # ADR-0050's closure test: a paginated feed read only to its stop did
        # not look at anything older than this, so an absence there is not
        # evidence of closure.
        published = [r.published_at for r in rows if r.published_at]
        log["oldest_published"] = min(published) if published else None
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
                if not board.polled_on(self.slot):
                    # ADR-0048: skipped, and said so, so a skipped source is
                    # visible rather than absent and never reads as broken.
                    self.board_logs.append({
                        "board": board.board_id, "fetched": 0, "parse_problems": 0,
                        "new": 0, "kept": 0, "drops": {}, "status": "skipped",
                        "detail": "polled on the %s run only (ADR-0048); this is the %s run"
                                  % (" and ".join(board.poll_slots), self.slot)})
                    continue
                if self.private_unavailable and not is_publishable(board.source):
                    self.board_logs.append({
                        "board": board.board_id, "fetched": 0, "parse_problems": 0,
                        "new": 0, "kept": 0, "drops": {}, "status": "skipped",
                        "detail": "the private store could not be restored, so nothing "
                                  "fetched here could be kept (ADR-0047); the run log's "
                                  "private_store block says why"})
                    continue
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

        # ADR-0030: the filtered layer must track the rules in force, and the
        # only place that can be guaranteed is inside the run that writes it.
        # A rule change otherwise needs someone to remember, and forgetting is
        # invisible: no later run offers those postings again.
        #
        # It runs after the normal write, so at the end of every run the
        # layer matches the rules. It appends nothing when there is no gap,
        # which is the usual case, and costs one pass over the raw layer.
        #
        # **Counted separately, and that separation is the point.** If the
        # normal write path broke, this would quietly write the same rows and
        # the run would look healthy. A run whose `written_filtered` is 0
        # while `backfilled` is 8 is a defect wearing a working run's clothes,
        # and only two numbers make it visible.
        #
        # `self.paths` already carries the run's mode, so a test run backfills
        # data/test/ and can never heal production. That is asserted by a test,
        # because inheriting it silently is exactly how it would stop being true.
        backfilled = backfill(self.paths, iso(self.now), matcher=self.matcher)

        for row in all_rows:
            seen.record(row)
            seen.mark_seen(row.identity, iso(self.now))
        # D11: every posting fetched whose full record the private branch does
        # not hold yet. An ATS board returns every listed posting each run, so
        # one whose save failed is saved by the next run that still sees it.
        self.full_pending = [self.full[i] for i in sorted(self.full)
                             if not seen.full_saved(i)]
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
                "backfilled": backfilled["written_public"] + backfilled["written_local"],
                "backfilled_public": backfilled["written_public"],
                "backfilled_local": backfilled["written_local"],
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
    # Its own line, never folded into the filtered count. A run writing 0 of
    # its own while the backfill writes 8 is a broken write path, and one
    # combined number would read as a healthy run.
    lines.append("  backfilled: %d (%d publishable, %d local only). ADR-0030"
                 % (t.get("backfilled", 0), t.get("backfilled_public", 0),
                    t.get("backfilled_local", 0)))
    lines.append("  drops by rule: %s" % t["drops"])
    lines.append("  dedupe: %s" % t["dedupe"])
    r = run_log["requests"]
    lines.append("  requests: %d of %d, by source %s, retries %d, failures %d"
                 % (r["requests_used"], r["budget"], r["by_source"],
                    r["retries"], r["failures"]))
    if run_log["stopped"]:
        lines.append("  STOPPED: %s. Unreached boards resume next run." % run_log["stopped"])
    p = run_log.get("projection")
    if p is not None:
        # Each stage on the line, because the display, the chain and the store
        # differ in count by design and only the stages show where.
        lines.append("  projection: read %s, admitted %s, groups %s, skipped by a store %s, "
                     "to send %s%s"
                     % (p.get("rows_read", "-"), p.get("rows_admitted", "-"),
                        p.get("groups", "-"), p.get("groups_skipped_by_store", "-"),
                        p.get("rows_to_send", "-"),
                        "  [%s]" % p["mode"] if p.get("mode") else ""))
    sw = run_log.get("sweep")
    if sw is not None:
        lines.append("  sweep: %s%s" % (
            sw.get("mode") or "%s, %d call(s), copied %s, deleted from Jobs %s, Closed marked %s, "
            "waiting for the store %s" % ("daily" if sw.get("daily") else "copy only",
                                          sw.get("calls_used", 0), sw.get("copied", {}),
                                          sw.get("deleted_from_jobs", 0),
                                          sw.get("closed_marked", 0),
                                          sw.get("waiting_for_the_store", 0)),
            "  FAILED: %s" % sw["failure"] if sw.get("failure") else ""))
    b = run_log.get("budget")
    if b is not None and b.get("failure"):
        lines.append("  airtable month to date: could not be counted: %s" % b["failure"])
    elif b is not None:
        lines.append("  airtable month to date: %d of %d%s" % (
            b["month_to_date"], b["allowance"],
            "  WARNING: %s" % b["warning"] if b.get("warning") else ""))
    a = run_log.get(RUN_LOG_KEY)
    if a is not None:
        lines.append("  airtable: %d call(s), %d row(s) sent%s"
                     % (a.get("calls_used", 0), a.get("rows_sent", 0),
                        "  FAILED: %s" % a["failure"] if a.get("failure") else ""))
    ps = run_log.get("private_store")
    if ps is not None:
        lines.append("  private store (%s): %d file(s) restored, %s%s"
                     % (ps.get("branch"), ps.get("restored", 0),
                        {True: "pushed", False: "nothing changed"}.get(ps.get("pushed"),
                                                                       "not pushed"),
                        "  FAILED: %s" % ps["failure"] if ps.get("failure") else ""))
    at = run_log.get("attention") or {}
    if at.get("failed_in_a_row"):
        lines.append("  attention: failed %d run(s) in a row%s"
                     % (at["failed_in_a_row"], ", the run will be marked failed"
                        if at.get("escalate") else ""))
    return "\n".join(lines)


def files_to_commit(run_log, paths, log_path, test_mode):
    """What goes to the data branch.

    **An aggregator's raw file never does.** ADR-0020: two feeds prohibit
    redistribution and a branch inherits its repository's visibility, so those
    rows stay in a local directory, which ADR-0047 pushes to a private
    repository instead. This is the last gate before a push, and
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
    # ADR-0050: the sweep's public outcome stores. The guard below reads each
    # record's source, so an aggregator's outcome can no more reach the
    # branch than its row can.
    if os.path.isdir(paths["outcomes_dir"]):
        for name in sorted(os.listdir(paths["outcomes_dir"])):
            if name.endswith(".json"):
                path = "%s/%s" % (paths["outcomes_dir"], name)
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

    # Local runs read their secrets from .env; anything already set wins, so
    # a runner is unaffected. Names are counted, never printed with values.
    loaded = envfile.load()
    if loaded:
        print("environment: %d name(s) loaded from .env" % len(loaded))

    test_mode = args.test_mode or os.environ.get("TEST_MODE") == "1"

    try:
        boards = load_boards()
        matcher = TitleMatcher()
        sweep_config = load_sweep_config()
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

    # ADR-0047. After the public restore, which can stop the run, and before
    # any fetch. A failure here does not stop the run: D6 keeps the public
    # fetch and exits 2.
    store, private_block = (None, None)
    if not args.no_commit:
        store, private_block = open_private_store(storage.layout(test_mode), test_mode)

    client = HttpClient(**({"budget": args.budget} if args.budget else {}))
    # The workflow names the slot from the cron that fired it. Anything else,
    # a dispatch or a local run, is not a slot and polls every board.
    slot = os.environ.get("RUN_SLOT") or None
    # A failed restore and a failed push differ: only the first leaves the
    # private outcome stores unknown, so only the first stops the projection.
    restore_failure = private_block and private_block["failure"]
    run = Run(boards, client, test_mode=test_mode, matcher=matcher, slot=slot,
              private_unavailable=restore_failure)
    try:
        run_log = run.execute()
    except Exception:
        if store is not None:
            store.close()
        traceback.print_exc()
        print("could not complete the run: the exception above was raised before "
              "anything was committed", file=sys.stderr)
        return EXIT_CANNOT_START

    # The data first: the aggregator files go to the private store before
    # anything is sent to the display. Never raises. The full postings (D11)
    # go before them, so both seen stores record what was saved.
    if private_block is not None:
        save_full_postings(run, store, private_block, run_log["run_at"])
        save_private_store(store, private_block, run.paths, run_log["run_at"])
        run_log["private_store"] = private_block
    private_failure = private_block and private_block["failure"]

    # After the files are written, before the run log is: the log records the
    # outcome. Never raises; a failure is recorded and the run still commits.
    try:
        closure = closure_for(run, boards, test_mode, args.no_commit, run_log, sweep_config)
        retired = retired_by(closure, sweep_config, run.now)
    except Exception as e:
        closure, retired = None, None
        run_log["closure_failure"] = redact_secrets("%s: %s" % (type(e).__name__, e))
    run_log["projection"], run_log[RUN_LOG_KEY], projection_failure = \
        project_display(run, args.no_commit, test_mode, restore_failure, retired=retired)

    # ADR-0050's sweep, after the projection so a row it just sent is read
    # back with the rest. Its aggregator outcomes need the private store to
    # have been restored and written this run.
    #
    # The month's calls: the projection's count when it reached the base,
    # read again otherwise. A count that cannot be read must never cost the
    # fetch, so it is caught here like every other display failure (the
    # audit of 2026-09-25, F3); the sweep is then skipped, since its budget
    # guard would be blind, and the run says why.
    by_branch, count_failure = {}, None
    if not args.no_commit:
        by_branch = (run_log[RUN_LOG_KEY] or {}).get("month_to_date_by_branch")
        if by_branch is None:
            try:
                by_branch = month_so_far(iso(run.now), test_mode)
            except Exception as e:
                by_branch = {}
                count_failure = redact_secrets("%s: %s" % (type(e).__name__, e))
    if count_failure is not None:
        run_log["sweep"] = {"calls_used": 0, "failure": "the month's Airtable calls could not "
                            "be counted, so the sweep did not run: %s" % count_failure}
    else:
        run_log["sweep"] = sweep_display(
            run, args.no_commit, test_mode, slot,
            private_ok=bool(store is not None and not (private_block and private_block["failure"])),
            closure=closure, config=sweep_config,
            used_before=sum(by_branch.values())
            + int((run_log[RUN_LOG_KEY] or {}).get("calls_used") or 0),
            closure_failure=run_log.get("closure_failure") if closure is None else None)
    sweep_failure = run_log["sweep"].get("failure")
    if private_block is not None and store is not None and not private_block["failure"]:
        # The second push: the aggregator outcomes the sweep just wrote.
        save_private_store(store, private_block, run.paths, run_log["run_at"],
                           key="outcomes_pushed")
        private_failure = private_block["failure"]
    if store is not None:
        store.close()
    if not args.no_commit and count_failure is not None:
        run_log["budget"] = {"month_to_date": None, "warning": None, "failure": count_failure}
    elif not args.no_commit:
        run_log["budget"] = budget_line(run_log, by_branch, sweep_config, run.now)
        if run_log["budget"]["warning"]:
            # A workflow annotation, and it stays in the committed log.
            print("::warning::%s" % run_log["budget"]["warning"])
    run_log["attention"] = attention(run_log, test_mode, args.no_commit)

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

    if run_log["attention"]["escalate"]:
        # Only after the commit: the workflow pushes, then fails the run.
        tell_the_workflow("escalate", "true")
        why = ("the private store failed" if private_store_failed(run_log) else
               "the display has failed on %d runs in a row"
               % run_log["attention"]["failed_in_a_row"])
        print("%s; this run is committed and the workflow will mark it failed after "
              "pushing, so it can be fixed" % why, file=sys.stderr)
    if private_failure:
        print("the private store could not be restored or written, or the full postings "
              "could not be saved; the public fetch is stored and the next run tries "
              "again: %s" % private_failure,
              file=sys.stderr)
    if projection_failure:
        print("the projection to Airtable failed; the fetch is stored and the next run "
              "re-projects: %s" % projection_failure, file=sys.stderr)
    if sweep_failure:
        print("the sweep failed; nothing it had not verified was deleted, and the next "
              "run sweeps again: %s" % sweep_failure, file=sys.stderr)
    if private_failure or projection_failure or sweep_failure:
        return EXIT_STOPPED_RESUMABLE
    return run.exit_code()


if __name__ == "__main__":
    sys.exit(main())
