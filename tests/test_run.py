"""The fetch run, tested from the brief.

The brief requires three exit codes, a run log carrying every board every run
including zeros, and a TEST_MODE run that leaves production data alone.

No test here touches the network or the real repository.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import run as run_module
from src import storage
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.run import EXIT_OK, EXIT_STOPPED_RESUMABLE, Run, summarise

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
MATCHER = TitleMatcher()

GH = Board(platform="greenhouse", slug="careem")
GH2 = Board(platform="greenhouse", slug="globalli")
LV = Board(platform="lever", slug="spreetail", employer_alias="Spreetail")


def gh_payload(titles, start=0):
    return {"jobs": [{"id": 1000 + start + i, "title": t,
                      "absolute_url": "https://boards.test/%d" % (1000 + start + i),
                      "first_published": "2026-09-10T05:00:00+00:00",
                      "company_name": "Careem",
                      "location": {"name": "Karachi"}}
                     for i, t in enumerate(titles)]}


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status_code = status
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


class FakeSession:
    """Maps a URL fragment to a payload, or to an Exception to raise."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append(url)
        for fragment, value in self.routes.items():
            if fragment in url:
                if isinstance(value, Exception):
                    raise value
                return FakeResponse(value)
        return FakeResponse({"jobs": []})


def client_for(routes, **kw):
    kw.setdefault("min_interval", 0)
    return HttpClient(session=FakeSession(routes), sleep=lambda s: None, **kw)


class RunHarness(unittest.TestCase):
    """Each test runs in its own directory, so nothing shares state."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)


class TestNormalRun(RunHarness):
    def test_writes_both_layers_and_logs_every_board(self):
        client = client_for({"careem": gh_payload(["AI Engineer", "Chief Happiness Officer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()

        self.assertEqual(log["totals"]["fetched"], 3)
        self.assertEqual(log["totals"]["new"], 3)
        self.assertEqual(log["totals"]["kept"], 2, "the happiness officer is dropped")
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 3})
        self.assertEqual(log["totals"]["written_filtered"], 2)
        self.assertEqual(len(storage.read_records("fetch-all/greenhouse.json")), 3)
        self.assertEqual(len(storage.read_records("filtered.json")), 2)

    def test_a_board_returning_zero_still_gets_a_line(self):
        """A board returning nothing for a week is a broken adapter, and
        without a zero logged it looks like a quiet market."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": {"jobs": []}})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(set(lines), {"greenhouse:careem", "greenhouse:globalli"})
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 0)
        self.assertEqual(lines["greenhouse:globalli"]["status"], "ok")

    def test_drops_are_attributed_per_board_and_per_rule(self):
        client = client_for({"careem": gh_payload(["Chief Happiness Officer"]),
                             "globalli": gh_payload(["AI Engineer"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["drops"], {"title": 1})
        self.assertEqual(lines["greenhouse:globalli"]["drops"], {})
        self.assertEqual(log["totals"]["drops"]["title"], 1)

    def test_request_counts_are_reported_per_source(self):
        """ADR-0028: this log is what sets the real ceiling later."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "spreetail": []})
        log = Run([GH, LV], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["requests"]["by_source"], {"greenhouse": 1, "lever": 1})
        self.assertEqual(log["requests"]["budget"], 500)

    def test_a_second_run_with_no_changes_writes_nothing_new(self):
        """The brief's check, end to end."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        before = read_text("fetch-all/greenhouse.json")

        log = Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        after = read_text("fetch-all/greenhouse.json")

        self.assertEqual(log["totals"]["new"], 0)
        self.assertEqual(before, after)

    def test_first_seen_survives_the_second_run(self):
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        seen_first = json.loads(read_text("seen.json"))
        later = datetime(2026, 10, 1, tzinfo=timezone.utc)
        Run([GH], client_for({"careem": payload}), now=later, matcher=MATCHER).execute()
        seen_second = json.loads(read_text("seen.json"))
        key = list(seen_first)[0]
        self.assertEqual(seen_first[key]["first_seen"], seen_second[key]["first_seen"])
        self.assertNotEqual(seen_second[key]["last_seen"], seen_second[key]["first_seen"])


class TestFailureHandling(RunHarness):
    def test_one_dead_board_does_not_cost_the_others(self):
        client = client_for({"careem": OSError("connection reset"),
                             "globalli": gh_payload(["AI Engineer"], start=50)},
                            max_attempts=1)
        run = Run([GH, GH2], client, now=NOW, matcher=MATCHER)
        log = run.execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["status"], "failed",
                         "a transport failure is the board's, not ours")
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 1)
        self.assertEqual(run.exit_code(), EXIT_OK)

    def test_an_unparseable_payload_stops_that_board_only(self):
        client = client_for({"careem": {"postings": []},
                             "globalli": gh_payload(["AI Engineer"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["status"], "unparseable")
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 1)

    def test_budget_exhaustion_stops_the_run_and_names_what_was_missed(self):
        """Exit 2: stopped deliberately and resumable, not a failure."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)},
                            budget=1)
        run = Run([GH, GH2], client, now=NOW, matcher=MATCHER)
        log = run.execute()
        self.assertEqual(run.exit_code(), EXIT_STOPPED_RESUMABLE)
        self.assertIsNotNone(log["stopped"])
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:globalli"]["status"], "not reached")

    def test_work_reached_before_the_stop_is_still_written(self):
        """Stopping must not discard what the run already has."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)},
                            budget=1)
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 1})
        self.assertEqual(len(storage.read_records("fetch-all/greenhouse.json")), 1)


class TestSourceRouting(RunHarness):
    def test_each_source_writes_its_own_file(self):
        """ADR-0020: a row's provenance is its filename."""
        client = client_for({
            "careem": gh_payload(["AI Engineer"]),
            "spreetail": [{"id": "lv1", "text": "Machine Learning Engineer",
                           "hostedUrl": "https://jobs.lever.co/spreetail/lv1",
                           "createdAt": 1789018446882,
                           "categories": {"location": "Karachi"}}]})
        log = Run([GH, LV], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 1, "lever": 1})
        gh_rows = storage.read_records("fetch-all/greenhouse.json")
        lv_rows = storage.read_records("fetch-all/lever.json")
        self.assertEqual({r["source"] for r in gh_rows}, {"greenhouse"})
        self.assertEqual({r["source"] for r in lv_rows}, {"lever"})

    def test_lever_rows_carry_their_derived_employer_and_provenance(self):
        client = client_for({"spreetail": [
            {"id": "lv1", "text": "AI Engineer",
             "hostedUrl": "https://jobs.lever.co/spreetail/lv1",
             "createdAt": 1789018446882, "categories": {"location": "Karachi"}}]})
        Run([LV], client, now=NOW, matcher=MATCHER).execute()
        row = storage.read_records("fetch-all/lever.json")[0]
        self.assertEqual(row["employer"], "Spreetail")
        self.assertEqual(row["employer_provenance"], "slug")
        self.assertTrue(row["published_meaning_unconfirmed"])


class TestTestMode(RunHarness):
    def test_test_mode_leaves_production_files_untouched(self):
        """The brief's check."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        production = read_text("fetch-all/greenhouse.json")

        client = client_for({"careem": gh_payload(["Data Scientist"], start=99)})
        Run([GH], client, now=NOW, test_mode=True, matcher=MATCHER).execute()

        self.assertEqual(read_text("fetch-all/greenhouse.json"),
                         production)
        self.assertTrue(os.path.exists("test-fetch-all/greenhouse.json"))
        self.assertEqual(len(storage.read_records("test-fetch-all/greenhouse.json")), 1)

    def test_test_mode_isolates_the_filtered_layer_and_the_seen_store(self):
        """Isolating only the raw file is not isolation: a test run that
        rewrote the production seen store would re-date first_seen for every
        posting, and one that appended to production filtered.json would put
        test rows in front of the operator."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        filtered_before = read_text("filtered.json")
        seen_before = read_text("seen.json")

        client = client_for({"careem": gh_payload(["Machine Learning Engineer"], start=99)})
        Run([GH], client, now=NOW, test_mode=True, matcher=MATCHER).execute()

        self.assertEqual(read_text("filtered.json"), filtered_before)
        self.assertEqual(read_text("seen.json"), seen_before)
        self.assertTrue(os.path.exists("test-filtered.json"))
        self.assertTrue(os.path.exists("test-seen.json"))


class TestSummary(RunHarness):
    def test_summary_names_every_board_and_the_request_count(self):
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": {"jobs": []}})
        text = summarise(Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute())
        self.assertIn("greenhouse:careem", text)
        self.assertIn("greenhouse:globalli", text)
        self.assertIn("requests:", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
