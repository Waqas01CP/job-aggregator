"""Startup.jobs' rows closed by its own answer (Brief 21, item 3).

Its walk reads newest first and never whole, so its absence can never close a
posting, and the resume chat found ten of its rows dead on 2026-11-22 that
nothing had marked. Its API answers 404 for a posting it no longer lists and
200 for a live one, tested that day on the 55 rows `Jobs` held. Each test here
is built to fail on the behaviour it names.
"""

import json
import os
import re
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

from src import storage
from src.closure import Closure
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.run import GONE_FILE, JOBS_VIEW_FILE, Run, closure_for
from tests.test_adapters import cassette

NOW = datetime(2026, 11, 24, 4, 0, tzinfo=timezone.utc)
MATCHER = TitleMatcher()
SJ = Board(platform="startupjobs", slug="sj-workplace-remote")
VIEW = "data/local/agreement/%s" % JOBS_VIEW_FILE
GONE = "data/local/agreement/%s" % GONE_FILE
KEY = {"STARTUP_JOBS_API_KEY": "sk_FAKEKEY"}


def client(statuses):
    """The listing from its cassette; each per-posting read answers the status
    `statuses` gives its ID, 200 by default. Records the IDs asked about."""
    listing = cassette("startupjobs-remote.json")
    asked = []

    class Session:
        def get(_self, url, params=None, timeout=None, headers=None):
            m = re.search(r"/v1/jobs/(\d+)$", url)
            if m:
                asked.append(m.group(1))
                status, body = statuses.get(m.group(1), 200), {"data": {"id": m.group(1)}}
            else:
                status, body = 200, listing

            class R:
                status_code = status
                headers = {}
                text = ""

                def json(self):
                    return body
            return R()
    c = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
    c.asked = asked
    return c


def view(*ids, board=SJ.board_id):
    rows = [{"Board": board, "Identity": "startupjobs:%s" % i,
             "First seen": "2026-11-%02dT00:00:00Z" % (1 + n)} for n, i in enumerate(ids)]
    storage.write_atomic(VIEW, json.dumps({"at": "2026-11-23T20:00:00Z", "described": True,
                                           "rows": rows}))


def gone():
    if not os.path.exists(GONE):
        return {}
    with open(GONE, encoding="utf-8") as f:
        return json.load(f)


class GoneHarness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        patcher = mock.patch.dict(os.environ, KEY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_with(self, c, slot="morning", **kw):
        return Run([SJ], c, now=NOW, matcher=MATCHER, slot=slot, **kw).execute()


class TestTheGoneCheck(GoneHarness):
    def test_a_404_is_recorded_with_its_day_and_a_200_is_not(self):
        """The source's own answer, and the public log carries counts alone.
        Mutation: "a 404 is not recorded"."""
        view("11", "12")
        log = self.run_with(client({"11": 404}))
        self.assertEqual(gone(), {"startupjobs:11": "2026-11-24"})
        self.assertEqual(log["gone_check"], {"checked": 2, "gone": 1, "open": 1,
                                             "unanswered": 0, "waiting": 0})
        self.assertNotIn("startupjobs:11", json.dumps(log))

    def test_any_other_answer_proves_nothing(self):
        """A 403 or a 500 is no answer: counted, never recorded. Mutation: "any
        error reads as gone"."""
        view("11", "12")
        log = self.run_with(client({"11": 403, "12": 500}))
        self.assertEqual(gone(), {})
        self.assertEqual(log["gone_check"]["unanswered"], 2)

    def test_a_morning_of_closed_postings_never_opens_the_breaker(self):
        """Seven 404s in a row, past the breaker's five: each is an answer, so
        each is asked and recorded. Mutation: "an answer counts as a failure"."""
        ids = [str(10 + n) for n in range(7)]
        view(*ids)
        log = self.run_with(client({i: 404 for i in ids}))
        self.assertEqual(len(gone()), 7)
        self.assertNotIn("stopped", log["gone_check"])

    def test_the_evening_asks_nothing(self):
        """The sweep that marks Closed runs on mornings (A1). Mutation: "the
        evening asks too"."""
        view("11")
        c = client({"11": 404})
        log = self.run_with(c, slot="evening")
        self.assertEqual(c.asked, [])
        self.assertIn("mornings only", log["gone_check"]["skipped"])

    def test_a_posting_already_recorded_is_not_asked_again(self):
        """Mutation: "a recorded posting is asked every morning"."""
        view("11", "12")
        storage.write_atomic(GONE, json.dumps({"startupjobs:11": "2026-11-20"}))
        c = client({"12": 404})
        self.run_with(c)
        self.assertEqual(c.asked, ["12"])
        self.assertEqual(gone(), {"startupjobs:11": "2026-11-20", "startupjobs:12": "2026-11-24"})

    def test_the_oldest_are_asked_first_and_the_rest_wait(self):
        """Mutation: "the cap asks every row"."""
        view("11", "12", "13")
        c = client({})
        with mock.patch("src.run.GONE_CHECK_CAP", 2):
            log = self.run_with(c)
        self.assertEqual(c.asked, ["11", "12"])
        self.assertEqual(log["gone_check"]["waiting"], 1)

    def test_a_board_not_polled_cleanly_is_not_asked_about(self):
        """Without its key the board is not polled, so 55 requests would each
        fail. Mutation: "a board not polled is asked about"."""
        view("11")
        c = client({"11": 404})
        with mock.patch.dict(os.environ, {"STARTUP_JOBS_API_KEY": ""}):
            log = self.run_with(c)
        self.assertEqual(c.asked, [])
        self.assertEqual(log["gone_check"]["checked"], 0)

    def test_no_check_with_the_private_store_down_or_no_view(self):
        view("11")
        c = client({"11": 404})
        log = self.run_with(c, private_unavailable="restore failed")
        self.assertIn("private store", log["gone_check"]["skipped"])
        os.remove(VIEW)
        log = self.run_with(c)
        self.assertIn("no view of Jobs", log["gone_check"]["skipped"])
        self.assertEqual(c.asked, [])


class TestTheClosureReadsIt(GoneHarness):
    def test_a_posting_its_source_said_is_gone_closes_on_that_day(self):
        """Mutation: "the closure test ignores the source's answer"."""
        row = SimpleNamespace(identity="startupjobs:11", expires_at=None, board_id=SJ.board_id,
                              published_at="2026-11-01T00:00:00Z")
        closure = Closure({}, [], lambda b: True, 12, "2026-11-24T04:00:00Z",
                          gone={"startupjobs:11": "2026-11-23"})
        self.assertEqual(closure.closed_on(row), ("2026-11-23", "gone at source"))

    def test_the_run_hands_the_record_to_the_closure_test(self):
        """Mutation: "the run never reads the record"."""
        storage.write_atomic(GONE, json.dumps({"startupjobs:11": "2026-11-23"}))
        run = Run([SJ], client({}), now=NOW, matcher=MATCHER)
        config = SimpleNamespace(closed_after_polled_runs=12, run_log_window=10)
        closure = closure_for(run, [SJ], False, True, {"run_at": "2026-11-24T04:00:00Z"}, config)
        row = SimpleNamespace(identity="startupjobs:11", expires_at=None, board_id=SJ.board_id,
                              published_at="2026-11-01T00:00:00Z")
        self.assertEqual(closure.closed_on(row)[0], "2026-11-23")


if __name__ == "__main__":
    unittest.main()
