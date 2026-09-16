"""Himalayas, the conditional aggregator. ADR-0019.

The brief: browse endpoint only, and the stop anchored on the newest pubDate
actually stored rather than on clock time.
"""

import json
import os
import sys
import shutil
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.adapters import himalayas
from src.adapters.base import AdapterError
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.normalise import normalise
from src.run import Run, files_to_commit

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
BOARD = Board(platform="himalayas", slug="browse")
CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cassettes")
MATCHER = TitleMatcher()


def cassette():
    with open(os.path.join(CASSETTES, "himalayas-browse.json"), encoding="utf-8") as f:
        return json.load(f)


class TestAdapter(unittest.TestCase):
    def test_uses_the_browse_endpoint_and_never_search(self):
        """Measured 2026-09-16: search is not recency-ordered and silently
        ignores the cursor, returning a byte-identical page."""
        url = himalayas.url_for(BOARD)
        self.assertIn("himalayas.app/jobs/api", url)
        self.assertNotIn("/search", url)
        self.assertNotIn("sort=recent", url)

    def test_cursor_is_appended_for_later_pages(self):
        self.assertIn("cursor=abc123", himalayas.url_for(BOARD, "abc123"))

    def test_parses_the_measured_fields(self):
        result = himalayas.parse(cassette(), BOARD)
        self.assertEqual(len(result.postings), 8)
        self.assertEqual(result.problems, [])
        p = result.postings[0]
        self.assertEqual(p.title, "Financial Systems Expert")
        self.assertEqual(p.employer, "micro1")
        self.assertEqual(p.employer_provenance, "payload")
        self.assertEqual(p.published_field, "pubDate")
        self.assertEqual(p.source, "himalayas")
        self.assertTrue(p.url.startswith("https://"))

    def test_guid_is_the_identifier_because_there_is_no_id(self):
        p = himalayas.parse(cassette(), BOARD).postings[0]
        self.assertTrue(p.external_id.startswith("https://himalayas.app/"))

    def test_epoch_seconds_are_converted(self):
        """1789141813 is 2026-09-11T15:50:13Z, measured in the spike."""
        p = himalayas.parse(cassette(), BOARD).postings[0]
        self.assertEqual(p.published_at,
                         datetime(2026, 9, 11, 15, 50, 13, tzinfo=timezone.utc))

    def test_milliseconds_mistaken_for_seconds_are_rejected(self):
        payload = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                             "applicationLink": "https://x.test/1",
                             "pubDate": 1789141813000}]}
        result = himalayas.parse(payload, BOARD)
        self.assertEqual(result.postings, [])
        self.assertIn("epoch seconds", result.problems[0]["reason"])

    def test_an_empty_location_restriction_is_recorded_as_unstated(self):
        """An empty array is not the same as an absent field, and what it
        means was never established. Reading it as worldwide would be a
        guess that widens the display."""
        payload = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                             "applicationLink": "https://x.test/1",
                             "pubDate": 1789141813, "locationRestrictions": []}]}
        self.assertIsNone(himalayas.parse(payload, BOARD).postings[0].location)

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            himalayas.parse([], BOARD)


class TestStopRule(unittest.TestCase):
    def test_stops_when_a_page_reaches_what_is_already_stored(self):
        payload = cassette()
        newest = "2026-09-11T15:50:13Z"
        self.assertTrue(himalayas.stop_after(payload, newest))

    def test_does_not_stop_on_first_contact(self):
        """No high-water mark means nothing is stored yet."""
        self.assertFalse(himalayas.stop_after(cassette(), None))

    def test_does_not_stop_when_every_posting_is_newer_than_the_mark(self):
        self.assertFalse(himalayas.stop_after(cassette(), "2020-01-01T00:00:00Z"))

    def test_the_anchor_is_stored_data_not_the_clock(self):
        """The failure this prevents: browse trails the search endpoint by at
        least 97.7 minutes, so a posting can arrive with a pubDate earlier
        than the previous run's clock. A clock anchor steps over it and never
        looks again; a stored-data anchor does not."""
        payload = cassette()
        run_clock = "2026-09-16T12:00:00Z"        # long after every posting
        stored_high_water = "2026-09-01T00:00:00Z"
        self.assertTrue(himalayas.stop_after(payload, run_clock),
                        "a clock anchor would stop immediately")
        self.assertFalse(himalayas.stop_after(payload, stored_high_water),
                         "a stored anchor keeps reading until it meets known data")


class TestRunIntegration(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def _client(self, pages):
        """Serves the given pages in order, whatever the cursor."""
        served = {"n": 0}

        class Session:
            def get(_self, url, params=None, timeout=None, headers=None):
                page = pages[min(served["n"], len(pages) - 1)]
                served["n"] += 1

                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return page
                return R()
        return HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)

    def test_pagination_follows_the_cursor_until_it_runs_out(self):
        page1 = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                           "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                 "nextCursor": "c1"}
        page2 = {"jobs": [{"guid": "https://x.test/2", "title": "Machine Learning Engineer",
                           "applicationLink": "https://x.test/2", "pubDate": 1789141800}],
                 "nextCursor": None}
        client = self._client([page1, page2])
        log = Run([BOARD], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["fetched"], 2)
        self.assertEqual(client.counters()["by_source"]["himalayas"], 2)

    def test_aggregator_rows_go_to_a_local_file_never_the_committed_one(self):
        """ADR-0020: two feeds prohibit redistribution and a branch inherits
        its repository's visibility."""
        page = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                          "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                "nextCursor": None}
        log = Run([BOARD], self._client([page]), now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["source_class"], {"himalayas": "aggregator"})
        self.assertTrue(os.path.exists("data/fetch-all-local/himalayas.json"))
        self.assertFalse(os.path.exists("data/fetch-all/himalayas.json"),
                         "an aggregator row reached the committed directory")

    def test_the_aggregator_file_is_never_offered_to_the_data_branch(self):
        """The last gate before a push. ADR-0020: these rows are never
        committed and never pushed, so the commit set must not contain the
        aggregator's file even though the run wrote it."""
        page = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                          "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                "nextCursor": None}
        gh = Board(platform="greenhouse", slug="careem")

        class GHSession:
            def get(_s, url, params=None, timeout=None, headers=None):
                body = page if "himalayas" in url else {"jobs": [
                    {"id": 1, "title": "AI Engineer",
                     "absolute_url": "https://boards.test/1",
                     "first_published": "2026-09-10T05:00:00+00:00",
                     "company_name": "Careem", "location": {"name": "Karachi"}}]}

                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return body
                return R()

        client = HttpClient(session=GHSession(), sleep=lambda s: None, min_interval=0)
        run = Run([gh, BOARD], client, now=NOW, matcher=MATCHER)
        log = run.execute()
        files = files_to_commit(log, run.paths, "logs-runs/x.json", False)
        self.assertIn("fetch-all/greenhouse.json", files)   # branch path, ADR-0020
        self.assertNotIn("data/fetch-all-local/himalayas.json", files)
        self.assertFalse([p for p in files if "himalayas" in p],
                         "an aggregator file reached the data-branch commit set")

    def test_paging_is_capped_even_with_an_endless_cursor(self):
        """A feed of 100k postings behind a cursor that never ends must not
        run until the request budget is gone."""
        endless = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                             "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                   "nextCursor": "always"}
        client = self._client([endless])
        Run([BOARD], client, now=NOW, matcher=MATCHER).execute()
        from src.run import MAX_PAGES
        self.assertEqual(client.counters()["by_source"]["himalayas"], MAX_PAGES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
