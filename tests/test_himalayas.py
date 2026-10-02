"""Himalayas, the conditional aggregator. ADR-0019.

Since 2026-09-26 the search endpoint filtered to one country. The stop is
anchored on the newest pubDate the board actually stored, or on the age limit,
rather than on clock time.
"""

import contextlib
import io
import json
import os
import sys
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.adapters import himalayas
from src.adapters.base import AdapterError
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.normalise import normalise
from src.run import Run, files_to_commit, summarise

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
BOARD = Board(platform="himalayas", slug="browse")
SEARCH = Board(platform="himalayas", slug="pakistan")
CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cassettes")
MATCHER = TitleMatcher()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cassette():
    with open(os.path.join(CASSETTES, "himalayas-browse.json"), encoding="utf-8") as f:
        return json.load(f)


class TestAdapter(unittest.TestCase):
    def test_searches_the_boards_country_newest_first(self):
        """Since 2026-09-26, the operator's go: only postings open to the
        board's country, worldwide ones included. The slug is the country."""
        url = himalayas.url_for(Board(platform="himalayas", slug="pakistan"))
        self.assertTrue(url.startswith("https://himalayas.app/jobs/api/search?"), url)
        self.assertIn("country=pakistan", url)
        self.assertIn("sort=recent", url)
        self.assertIn("page=1", url)

    def test_the_real_board_is_pakistan_on_the_morning_run(self):
        from src.config import load_boards
        [him] = [b for b in load_boards() if b.platform == "himalayas"]
        self.assertEqual((him.board_id, him.poll_slots), ("himalayas:pakistan", ("morning",)))

    def test_later_pages_go_by_number(self):
        self.assertIn("page=3", himalayas.url_for(BOARD, "3"))
        self.assertEqual(himalayas.next_cursor({"offset": 0, "limit": 20, "totalCount": 2965}),
                         "2")
        self.assertEqual(himalayas.next_cursor({"offset": 20, "limit": 20, "totalCount": 2965}),
                         "3")

    def test_the_last_page_has_no_next(self):
        self.assertIsNone(himalayas.next_cursor({"offset": 2960, "limit": 20,
                                                 "totalCount": 2965}))
        self.assertIsNone(himalayas.next_cursor({"jobs": []}))
        self.assertIsNone(himalayas.next_cursor({"offset": 0, "limit": 0, "totalCount": 5}))

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

    def test_every_country_is_kept_so_pakistan_fourth_still_counts(self):
        """D13 keeps a posting that names Pakistan anywhere in its list. The
        adapter once kept the first three countries only, which would have
        dropped this one."""
        payload = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                             "applicationLink": "https://x.test/1", "pubDate": 1789141813,
                             "locationRestrictions": ["United States", "Canada",
                                                      "United Kingdom", "Pakistan"]}]}
        self.assertIn("Pakistan", himalayas.parse(payload, BOARD).postings[0].location)

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            himalayas.parse([], BOARD)


def page_of(*epochs):
    return {"jobs": [{"guid": "https://x.test/%d" % i, "pubDate": e}
                     for i, e in enumerate(epochs)]}


class TestStopRule(unittest.TestCase):
    def test_stops_when_every_posting_on_the_page_is_already_stored(self):
        payload = cassette()
        newest_on_page = max(j["pubDate"] for j in payload["jobs"])
        mark = datetime.fromtimestamp(newest_on_page, timezone.utc).isoformat().replace(
            "+00:00", "Z")
        self.assertTrue(himalayas.stop_after(payload, mark))

    def test_a_pinned_old_posting_does_not_stop_the_walk(self):
        """The case built to defeat the old rule: search pins old postings at
        the top of page one, one of them ten days old on 2026-09-26. One old
        posting among new ones must not end the walk."""
        pinned_old, new_1, new_2 = 1789539315, 1790389282, 1790385000
        mark = "2026-09-25T00:00:00Z"
        self.assertFalse(himalayas.stop_after(page_of(pinned_old, new_1, new_2), mark))
        self.assertTrue(himalayas.stop_after(page_of(pinned_old, pinned_old), mark))

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

    def _client(self, pages, browse=None):
        """Serves the given search pages in order, whatever the page number,
        and `browse` for ADR-0053's agreement request, which takes no search
        page. `client.searches` counts the search requests alone, which is
        the walk's length."""
        served = {"n": 0}
        browse = browse if browse is not None else {"jobs": []}

        class Session:
            def get(_self, url, params=None, timeout=None, headers=None):
                if url == himalayas.AGREEMENT_URL:
                    page = browse
                else:
                    page = pages[min(served["n"], len(pages) - 1)]
                    served["n"] += 1

                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return page
                return R()
        client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
        client.served = served
        return client

    def test_pagination_follows_the_pages_until_they_run_out(self):
        page1 = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                           "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                 "offset": 0, "limit": 20, "totalCount": 40}
        page2 = {"jobs": [{"guid": "https://x.test/2", "title": "Machine Learning Engineer",
                           "applicationLink": "https://x.test/2", "pubDate": 1789141800}],
                 "offset": 20, "limit": 20, "totalCount": 40}
        client = self._client([page1, page2])
        log = Run([BOARD], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["fetched"], 2)
        self.assertEqual(client.served["n"], 2)

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

    def _mixed_run(self):
        """One ATS board and Himalayas, each with one posting the pool keeps."""
        page = {"jobs": [{"guid": "https://x.test/h1", "title": "AI Engineer",
                          "applicationLink": "https://x.test/h1", "pubDate": 1789141813}],
                "nextCursor": None}
        ats = {"jobs": [{"id": 1, "title": "AI Engineer",
                         "absolute_url": "https://boards.test/1",
                         "first_published": "2026-09-10T05:00:00+00:00",
                         "company_name": "Careem", "location": {"name": "Karachi"}}]}

        class Session:
            def get(_s, url, params=None, timeout=None, headers=None):
                body = page if "himalayas" in url else ats

                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return body
                return R()

        client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
        run = Run([Board(platform="greenhouse", slug="careem"), BOARD], client,
                  now=NOW, matcher=MATCHER)
        return run, run.execute()

    def test_no_aggregator_record_is_inside_any_file_offered_to_the_branch(self):
        """ADR-0020: aggregator rows are never committed. The file-name check
        above passed while filtered.json and seen.json, offered whole, held
        Himalayas rows and identities. This reads what is inside each file."""
        run, log = self._mixed_run()
        files = files_to_commit(log, run.paths, "logs-runs/x.json", False)
        self.assertEqual(log["totals"]["kept"], 2, "precondition: both sources kept a row")

        filtered = json.loads(files["filtered.json"])
        seen = json.loads(files["seen.json"])
        self.assertEqual([r["source"] for r in filtered], ["greenhouse"])
        self.assertEqual(sorted(e["source"] for e in seen.values()), ["greenhouse"])
        for path, text in files.items():
            self.assertNotIn("himalayas", text.lower(), path)

    def test_the_aggregator_rows_are_kept_locally_rather_than_lost(self):
        run, log = self._mixed_run()
        local_filtered = storage.read_records("data/local/filtered.json")
        local_seen = load_json("data/local/seen.json")
        self.assertEqual([r["source"] for r in local_filtered], ["himalayas"])
        self.assertEqual([e["source"] for e in local_seen.values()], ["himalayas"])
        self.assertEqual(log["totals"]["written_filtered"], 2)
        self.assertEqual(log["totals"]["written_filtered_local"], 1)

    def test_the_summary_says_how_many_kept_rows_stay_local(self):
        """The Actions log is what the operator reads. "filtered 2" alone, when
        one of the two never reaches the branch, misstates what was published.
        Needs a run with an aggregator row: with none, the local count is zero
        and a summary that always printed zero would pass."""
        run, log = self._mixed_run()
        self.assertIn("filtered 2 (1 of them local only)", summarise(log))

    def test_a_record_file_holding_aggregator_rows_is_refused(self):
        """The last gate, for files written before the split existed.
        data/test/filtered.json held 20 Himalayas rows on 2026-09-17."""
        run, log = self._mixed_run()
        mixed = storage.read_records("data/filtered.json") + \
            storage.read_records("data/local/filtered.json")
        storage.write_atomic("data/filtered.json", json.dumps(mixed))
        with self.assertRaises(storage.StorageError) as caught:
            files_to_commit(log, run.paths, "logs-runs/x.json", False)
        self.assertIn("filtered.json", str(caught.exception))
        self.assertIn("himalayas", str(caught.exception))

    def test_a_stray_aggregator_file_in_the_committed_directory_is_passed_over(self):
        """A Himalayas raw file left under fetch-all/ by an older build is not
        offered at all: the commit selects raw files by source, and the run
        goes on rather than failing on a file it was never going to send."""
        run, log = self._mixed_run()
        storage.write_atomic("data/fetch-all/himalayas.json",
                             json.dumps([{"identity": "himalayas:old", "source": "himalayas"}]))
        files = files_to_commit(log, run.paths, "logs-runs/x.json", False)
        self.assertNotIn("fetch-all/himalayas.json", files)

    def test_a_seen_store_holding_aggregator_entries_is_refused(self):
        run, log = self._mixed_run()
        seen = load_json("data/seen.json")
        seen["himalayas:planted"] = {"source": "himalayas"}
        storage.write_atomic("data/seen.json", json.dumps(seen))
        with self.assertRaises(storage.StorageError) as caught:
            files_to_commit(log, run.paths, "logs-runs/x.json", False)
        self.assertIn("seen.json", str(caught.exception))

    def test_an_entry_with_no_source_is_refused(self):
        """Unknown provenance is not publishable provenance."""
        run, log = self._mixed_run()
        seen = load_json("data/seen.json")
        seen["mystery:1"] = {"first_seen": "2026-09-10T00:00:00Z"}
        storage.write_atomic("data/seen.json", json.dumps(seen))
        with self.assertRaises(storage.StorageError):
            files_to_commit(log, run.paths, "logs-runs/x.json", False)

    def _saved_in_full(self):
        """What main() does after a verified save to the full branch (D11)."""
        for key in ("seen", "local_seen"):
            path = storage.layout(False)[key]
            seen = storage.SeenStore.load(path)
            for identity in seen.entries:
                seen.mark_full_saved(identity, "2026-09-16T12:00:00Z")
            seen.save(path)

    def test_the_stop_rule_still_reads_the_local_half_of_the_seen_store(self):
        """The high-water mark comes from stored Himalayas entries, which now
        live only in the local seen file. A run that loaded only the committed
        half would page to the cap on every run."""
        page1 = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                           "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                 "offset": 0, "limit": 20, "totalCount": 40}
        page2 = {"jobs": [{"guid": "https://x.test/2", "title": "Data Scientist",
                           "applicationLink": "https://x.test/2", "pubDate": 1789141800}],
                 "offset": 20, "limit": 20, "totalCount": 40}
        first = self._client([page1, page2])
        Run([BOARD], first, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(first.served["n"], 2)
        self._saved_in_full()

        second = self._client([page1, page2])
        log = Run([BOARD], second, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(second.served["n"], 1)
        self.assertEqual(log["totals"]["new"], 0)

    def test_paging_is_capped_even_with_endless_pages(self):
        """A feed of 100k postings, pages that never end, must not run until
        the request budget is gone."""
        endless = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                             "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                   "offset": 0, "limit": 20, "totalCount": 100000}
        client = self._client([endless])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            log = Run([BOARD], client, now=NOW, matcher=MATCHER).execute()
        from src.run import MAX_PAGES
        self.assertEqual(client.served["n"], MAX_PAGES)
        # And it says so: the cap cuts the oldest days unannounced otherwise
        # (the fourth audit's F17). Mutation: "hitting the page cap is silent".
        self.assertIs(log["boards"][0]["capped"], True)
        self.assertIn("::warning::himalayas:browse: the walk reached its cap", out.getvalue())
        self.assertEqual(log["boards"][0]["walk"]["stopped_by"], "cap")

    def test_a_walk_that_ends_on_its_own_is_not_capped(self):
        """And it records what it covered, for the closure test: stopped at
        its mark, here the age floor, it read every posting newer than the
        mark. Mutation: "the walk records no reach"."""
        client = self._client(self._two_pages(1788220800))
        log = Run([SEARCH], client, now=NOW, matcher=MATCHER).execute()
        self.assertIs(log["boards"][0]["capped"], False)
        self.assertEqual(log["boards"][0]["walk"],
                         {"stopped_by": "mark", "mark": "2026-09-09T11:59:59Z"})

    def test_a_walk_that_reads_to_the_end_of_the_feed_says_so(self):
        page = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                          "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                "offset": 0, "limit": 20, "totalCount": 1}
        log = Run([SEARCH], self._client([page]), now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["boards"][0]["walk"]["stopped_by"], "end")

    # The catch-up, the operator's yes of 2026-09-26: the search board reads
    # back a week on its first walk instead of stopping at browse's mark.
    def _two_pages(self, older):
        page1 = {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                           "applicationLink": "https://x.test/1", "pubDate": 1789141813}],
                 "offset": 0, "limit": 20, "totalCount": 60}
        page2 = {"jobs": [{"guid": "https://x.test/2", "title": "Data Scientist",
                           "applicationLink": "https://x.test/2", "pubDate": older}],
                 "offset": 20, "limit": 20, "totalCount": 60}
        page3 = {"jobs": [{"guid": "https://x.test/3", "title": "Machine Learning Engineer",
                           "applicationLink": "https://x.test/3", "pubDate": 1789141700}],
                 "offset": 40, "limit": 20, "totalCount": 60}
        return [page1, page2, page3]

    def test_a_board_is_not_stopped_by_another_boards_mark(self):
        """The case built to defeat a mark kept per source: browse stored the
        newest posting, and search, a different board of the same source,
        must still read past it."""
        pages = self._two_pages(1789141800)
        Run([BOARD], self._client(pages), now=NOW, matcher=MATCHER).execute()
        self._saved_in_full()
        client = self._client(pages)
        Run([SEARCH], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(client.served["n"], 3)

    def test_a_posting_not_saved_in_full_is_walked_to_again(self):
        """D11 on a paginated feed: the run of 2026-09-27T03:59Z stored its
        postings and could not save them in full. They set no mark, so the
        next walk reaches them and saves them; once saved, the walk stops."""
        pages = self._two_pages(1789141800)
        Run([SEARCH], self._client(pages), now=NOW, matcher=MATCHER).execute()
        again = self._client(pages)
        run = Run([SEARCH], again, now=NOW, matcher=MATCHER)
        log = run.execute()
        self.assertEqual(again.served["n"], 3)
        self.assertEqual(log["totals"]["new"], 0, "a posting walked to again is not new")
        self.assertEqual(len(run.full_pending), 3, "reached again but not offered for saving")
        self._saved_in_full()
        stopped = self._client(pages)
        Run([SEARCH], stopped, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(stopped.served["n"], 1)

    def test_with_no_mark_the_walk_stops_at_the_age_limit(self):
        """A page wholly older than a week before now holds nothing D14 could
        admit, so it ends a first walk; without that, the walk reads on."""
        client = self._client(self._two_pages(1788220800))      # 2026-09-01
        Run([SEARCH], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(client.served["n"], 2)

    def test_a_posting_exactly_at_the_age_limit_does_not_end_the_walk(self):
        """2026-09-09T12:00:00Z is exactly a week before NOW; the age rule
        keeps it, so the page it is on is not past the week."""
        client = self._client(self._two_pages(1788955200))
        log = Run([SEARCH], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(client.served["n"], 3)
        self.assertEqual(log["totals"]["fetched"], 3)

    def test_a_date_not_proven_to_mean_publication_sets_no_floor(self):
        from src.run import walk_floor
        self.assertIsNone(walk_floor("lever", NOW))
        self.assertEqual(walk_floor("himalayas", NOW), "2026-09-09T11:59:59Z")

    # ADR-0053's agreement check: one browse page against what the search
    # has returned, so a pushed-down predicate that drifts is seen.
    def _search_page(self):
        return {"jobs": [{"guid": "https://x.test/1", "title": "AI Engineer",
                          "applicationLink": "https://x.test/1", "pubDate": 1789141813,
                          "locationRestrictions": ["Pakistan"]}],
                "offset": 0, "limit": 20, "totalCount": 1}

    def _browse(self, *postings):
        return {"jobs": [dict({"title": "Data Scientist", "applicationLink": p["guid"]}, **p)
                         for p in postings]}

    # Browse's first page is minutes old and the search trails it by hours,
    # as live, so the posting below is an hour newer than the search's.
    NEWER = 1789141813 + 3600

    def _walk(self, browse, search=None, days_later=0):
        page = search or self._search_page()
        return Run([SEARCH], self._client([page], browse),
                   now=NOW + timedelta(days=days_later), matcher=MATCHER).execute()

    def test_the_agreement_check_is_seen_disagreeing(self):
        """Fitness function for ADR-0053, "The agreement check must be seen
        disagreeing.": a browse posting open to anyone, which the location
        rule admits, waits; the next morning's walk, a day later and reaching
        back past its date, has still not returned it, so the search has
        dropped something the operator could apply to. Counted in the public
        log and named only in the private store. Mutation: "the agreement
        check never disagrees"."""
        first = self._walk(self._browse({"guid": "https://x.test/9", "pubDate": self.NEWER}))
        self.assertEqual(first["boards"][0]["agreement"]["disagreements"], 0)
        log = self._walk(self._browse(), days_later=1)
        [board] = log["boards"]
        self.assertEqual(board["agreement"], {"browse_read": 0, "returned_by_search": 0,
                                              "rule_excludes": 0, "newly_waiting": 0,
                                              "returned_since": 0, "disagreements": 1,
                                              "still_waiting": 0})
        self.assertNotIn("x.test/9", json.dumps(first) + json.dumps(log))
        [record] = load_json("data/local/outcomes/agreement_disagreements.json")
        self.assertEqual(record["identity"], "himalayas:https://x.test/9")
        self.assertEqual(load_json("data/local/outcomes/agreement_pending.json"), [])

    def test_a_posting_the_search_has_not_taken_in_waits_and_agrees_once_returned(self):
        """The live case. The first build compared only postings no newer
        than the search's newest, which on the live feed was none: 0 of 20,
        the fourth audit's F3. Now such a posting waits, privately, and the
        walk that returns it settles it. Mutations: "a posting the search has
        not returned is judged on the walk that found it", "a waiting posting
        the search returned later is a disagreement"."""
        first = self._walk(self._browse({"guid": "https://x.test/9", "pubDate": self.NEWER}))
        agree = first["boards"][0]["agreement"]
        self.assertEqual((agree["browse_read"], agree["newly_waiting"], agree["disagreements"],
                          agree["still_waiting"]), (1, 1, 0, 1))
        [waiting] = load_json("data/local/outcomes/agreement_pending.json")
        self.assertEqual(waiting["identity"], "himalayas:https://x.test/9")
        returned = self._search_page()
        returned["jobs"].insert(0, {"guid": "https://x.test/9", "title": "Data Scientist",
                                    "applicationLink": "https://x.test/9",
                                    "pubDate": self.NEWER})
        agree = self._walk(self._browse(), search=returned,
                           days_later=1)["boards"][0]["agreement"]
        self.assertEqual((agree["returned_since"], agree["disagreements"],
                          agree["still_waiting"]), (1, 0, 0))

    def test_a_walk_that_did_not_reach_back_to_it_leaves_it_waiting(self):
        """An absence from pages that end before a posting's date says
        nothing about it. Mutation: "a walk that never reached a waiting
        posting's date judges it"."""
        self._walk(self._browse({"guid": "https://x.test/9", "pubDate": 1789141700}))
        agree = self._walk(self._browse(), days_later=1)["boards"][0]["agreement"]
        self.assertEqual((agree["disagreements"], agree["still_waiting"]), (0, 1))

    def test_a_posting_the_search_excluded_and_the_rule_would_too_is_agreement(self):
        """Mutation: "the agreement check ignores the location rule"."""
        log = self._walk(self._browse({"guid": "https://x.test/9", "pubDate": self.NEWER,
                                       "locationRestrictions": ["United States"]}))
        agree = log["boards"][0]["agreement"]
        self.assertEqual((agree["rule_excludes"], agree["newly_waiting"],
                          agree["disagreements"]), (1, 0, 0))

    def test_what_the_search_returned_on_an_earlier_walk_was_not_excluded(self):
        """The search pins old postings and its order inverts in places, so a
        posting on a page this walk did not read is not an exclusion. The
        seen store knows what the search ever returned. Mutation: "the
        agreement check forgets earlier walks"."""
        older = {"guid": "https://x.test/5", "title": "ML Engineer",
                 "applicationLink": "https://x.test/5", "pubDate": 1789141700}
        Run([SEARCH], self._client([{"jobs": [older], "offset": 0, "limit": 20,
                                     "totalCount": 1}]), now=NOW, matcher=MATCHER).execute()
        log = self._walk(self._browse({"guid": "https://x.test/5", "pubDate": 1789141700}))
        agree = log["boards"][0]["agreement"]
        self.assertEqual((agree["returned_by_search"], agree["newly_waiting"]), (1, 0))

    def test_a_failed_agreement_check_costs_the_board_nothing(self):
        log = Run([SEARCH], self._client([self._search_page()], {"no jobs": True}), now=NOW,
                  matcher=MATCHER).execute()
        [board] = log["boards"]
        self.assertIn("failure", board["agreement"])
        self.assertEqual((board["status"], board["fetched"]), ("ok", 1))

    def test_the_cap_reaches_back_a_week(self):
        """A first walk must reach the age limit before the cap. 92 eligible
        postings a day is the higher of the two estimates of 2026-09-26, and
        25 pages held only 6.4 days that day."""
        from src.run import MAX_PAGES
        self.assertGreaterEqual(MAX_PAGES * himalayas.PAGE_SIZE,
                                7 * 92 + himalayas.PAGE_SIZE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
