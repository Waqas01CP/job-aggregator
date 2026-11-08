"""A walk the page cap stopped reads on from where it stopped at the next run
(the fifth audit's F1).

Before this, what the cap left was lost, not late: the next walk's mark is the
newest posting stored, so a walk stopping there never reached the rest, and a
posting first seen past seven days is dropped by the age rule. Startup.jobs'
first production walk lost about the oldest eleven hours of its window that
way. Each test here is built to fail on the behaviour it names.
"""

import json
import os
import re
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

from src import private_store, storage
from src.adapters import himalayas
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.run import Run, WALK_RESUME_FILE, walk_floor

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
NOW_EPOCH = 1789560000
HOUR = 3600
SEARCH = Board(platform="himalayas", slug="pakistan")
DEEP = Board(platform="himalayas", slug="pakistan", deep_slots=("morning",))
FLOOR = walk_floor("himalayas", NOW)
MATCHER = TitleMatcher()
RESUME = "data/local/agreement/%s" % WALK_RESUME_FILE


def page(number, epoch, total_pages):
    """One search page of one posting a title rule keeps."""
    return {"jobs": [{"guid": "https://x.test/%d" % epoch, "title": "AI Engineer",
                      "applicationLink": "https://x.test/%d" % epoch, "pubDate": epoch}],
            "offset": (number - 1) * 20, "limit": 20, "totalCount": total_pages * 20}


def feed(epochs, failing=()):
    """A client serving page N of the search by its number, newest first,
    recording which pages were asked for. A page in `failing` answers 404."""
    asked = []
    pages = {n: page(n, e, len(epochs)) for n, e in enumerate(epochs, 1)}

    class Session:
        def get(_self, url, params=None, timeout=None, headers=None):
            if url == himalayas.AGREEMENT_URL:
                body, status = {"jobs": []}, 200
            else:
                number = int(re.search(r"page=(\d+)", url).group(1))
                asked.append(number)
                status = 404 if number in failing else 200
                body = pages.get(number, {"jobs": [], "offset": 0, "limit": 20, "totalCount": 0})

            class R:
                status_code = status
                headers = {}
                text = ""

                def json(self):
                    return body
            return R()
    client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
    client.asked = asked
    return client


def held(cursor="4", mark=None, board=SEARCH.board_id):
    return {"board": board, "cursor": cursor, "mark": mark or FLOOR,
            "capped_at": "2026-09-16T00:00:00Z"}


def read_resume():
    return storage.read_records(RESUME) if os.path.exists(RESUME) else None


def write_resume(entries):
    storage.write_atomic(RESUME, json.dumps(entries))


class TestAWalkTheCapStopped(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        patcher = mock.patch("src.run.MAX_PAGES", 3)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def _saved_in_full(self):
        """What main() does after a verified save to the full branch (D11)."""
        for key in ("seen", "local_seen"):
            path = storage.layout(False)[key]
            seen = storage.SeenStore.load(path)
            for identity in seen.entries:
                seen.mark_full_saved(identity, "2026-09-16T12:00:00Z")
            seen.save(path)

    def _run(self, client, board=SEARCH, slot=None, **kw):
        log = Run([board], client, now=NOW, matcher=MATCHER, slot=slot, **kw).execute()
        return log, next(b for b in log["boards"] if b["board"] == board.board_id)

    def _epochs(self, n=5):
        """`n` pages, an hour apart, all inside the week, newest first."""
        return [NOW_EPOCH - HOUR * i for i in range(1, n + 1)]

    def test_a_capped_walk_leaves_where_it_stopped_privately(self):
        """The cursor can be a posting's own ID, Startup.jobs' is, so it goes
        to the private file and never to the public run log. Mutation: "a
        capped walk leaves nothing for the next"."""
        log, entry = self._run(feed(self._epochs()))
        self.assertIs(entry["capped"], True)
        self.assertEqual(read_resume(), [{"board": SEARCH.board_id, "cursor": "4", "mark": FLOOR,
                                          "capped_at": "2026-09-16T12:00:00Z"}])
        self.assertNotIn("cursor", json.dumps(log))
        self.assertEqual(entry["walk"], {"stopped_by": "cap", "mark": FLOOR})

    def test_the_next_walk_reads_on_and_stores_what_the_cap_left(self):
        """F1 itself: the next walk stops at its own mark on page one, and
        still reads pages four and five. Mutation: "the next walk never reads
        on"."""
        client = feed(self._epochs())
        self._run(client)
        self._saved_in_full()
        client = feed(self._epochs())
        log, entry = self._run(client)
        self.assertEqual(client.asked, [1, 4, 5])
        self.assertEqual(entry["new"], 2)
        self.assertEqual(entry["walk"]["stopped_by"], "mark")
        self.assertEqual(entry["walk"]["tail"], {"stopped_by": "end", "mark": FLOOR, "pages": 2})
        self.assertIs(entry["capped"], False)
        self.assertEqual(entry["pages"], 3)
        self.assertEqual(read_resume(), [])

    def test_the_tail_stops_at_the_held_mark(self):
        """It reads only what the capped walk owed, not the rest of the feed.
        Mutation: "the tail reads past the held mark"."""
        epochs = self._epochs(6)
        with mock.patch("src.run.MAX_PAGES", 10):
            self._run(feed(epochs))
        self._saved_in_full()
        mark = datetime.fromtimestamp(epochs[3], timezone.utc).isoformat().replace("+00:00", "Z")
        write_resume([held(cursor="3", mark=mark)])
        client = feed(epochs)
        with mock.patch("src.run.MAX_PAGES", 10):
            _, entry = self._run(client)
        # Page one is at its own mark; pages three and four are the tail, and
        # four is the page at the held mark.
        self.assertEqual(client.asked, [1, 3, 4])
        self.assertEqual(entry["walk"]["tail"]["stopped_by"], "mark")
        self.assertEqual(read_resume(), [])

    def test_the_tail_never_reads_past_the_age_limit(self):
        """A held mark older than the week owes nothing the age rule could
        admit. Mutation: "the tail ignores the age limit"."""
        client = feed(self._epochs())
        self._run(client)
        self._saved_in_full()
        write_resume([held(cursor="4", mark="2026-09-01T00:00:00Z")])
        client = feed(self._epochs())
        _, entry = self._run(client)
        self.assertEqual(entry["walk"]["tail"]["mark"], FLOOR)

    def test_a_deep_walk_reads_past_a_page_wholly_older_than_the_week(self):
        """F1's second half. Below its first pages the search is not in date
        order: page two here is wholly older than the week, and page three
        holds a posting dated this week, which the walk used to stop short
        of. It reads to the feed's end. Mutation: "the deep walk stops at the
        age limit"."""
        old = NOW_EPOCH - HOUR * 24 * 10
        epochs = [NOW_EPOCH - HOUR, old, NOW_EPOCH - HOUR * 2]
        client = feed(epochs)
        _, entry = self._run(client, board=DEEP, slot="morning")
        self.assertEqual(client.asked, [1, 2, 3])
        self.assertEqual(entry["walk"], {"stopped_by": "end", "mark": ""})
        self.assertEqual(entry["new"], 3)

    def test_a_deep_walk_the_cap_stopped_reads_on_to_the_end_next_run(self):
        """Its tail keeps its reading to the end, past a page wholly older
        than the week. Mutation: "a deep walk's tail stops at the age limit"."""
        old = NOW_EPOCH - HOUR * 24 * 10
        epochs = [NOW_EPOCH - HOUR * 3, old, old - 1, old - 2, NOW_EPOCH - HOUR * 2]
        client = feed(epochs)
        _, entry = self._run(client, board=DEEP, slot="morning")
        self.assertEqual(entry["walk"]["stopped_by"], "cap")
        self.assertEqual(read_resume()[0]["mark"], "")
        self._saved_in_full()
        client = feed(epochs)
        _, entry = self._run(client, board=DEEP, slot="evening")
        self.assertEqual(client.asked, [1, 4, 5])
        self.assertEqual(entry["walk"]["tail"], {"stopped_by": "end", "mark": "", "pages": 2})
        self.assertEqual(entry["new"], 2)
        self.assertEqual(read_resume(), [])

    def test_a_deep_walk_that_reached_the_end_owes_nothing_and_clears_it(self):
        """Mutation: "a deep walk reads the tail as well"."""
        epochs = self._epochs(2)
        write_resume([held(cursor="4", board=DEEP.board_id)])
        client = feed(epochs)
        _, entry = self._run(client, board=DEEP, slot="morning")
        self.assertEqual(client.asked, [1, 2])
        self.assertNotIn("tail", entry["walk"])
        self.assertEqual(read_resume(), [])

    def test_a_walk_that_read_to_the_feeds_end_owes_nothing(self):
        """Its own mark is newer than the held one, so only its reaching the
        end says nothing is left. Mutation: "a walk that reached the end still
        reads the tail"."""
        self._run(feed([NOW_EPOCH - HOUR * 5]))
        self._saved_in_full()
        write_resume([held(cursor="9")])
        client = feed([NOW_EPOCH - HOUR, NOW_EPOCH - HOUR * 2])
        _, entry = self._run(client)
        self.assertEqual(client.asked, [1, 2])
        self.assertEqual(entry["walk"]["stopped_by"], "end")
        self.assertEqual(read_resume(), [])

    def test_the_cap_holds_across_head_and_tail_and_the_rest_stays_owed(self):
        """Mutations: "the tail has a cap of its own"; "a tail the cap stops
        forgets what it still owes"."""
        epochs = self._epochs(8)
        client = feed(epochs)
        self._run(client)
        self._saved_in_full()
        client = feed(epochs)
        _, entry = self._run(client)
        self.assertEqual(client.asked, [1, 4, 5])
        self.assertEqual(entry["pages"], 3)
        self.assertEqual(entry["walk"]["tail"], {"stopped_by": "cap", "mark": FLOOR, "pages": 2})
        self.assertIs(entry["capped"], True)
        self.assertEqual(read_resume(), [{"board": SEARCH.board_id, "cursor": "6", "mark": FLOOR,
                                          "capped_at": "2026-09-16T12:00:00Z"}])

    def test_a_walk_capped_twice_owes_the_older_mark(self):
        """Mutation: "a second capped walk forgets the first one's mark"."""
        older = "2026-09-01T00:00:00Z"
        write_resume([held(cursor="9", mark=older)])
        _, entry = self._run(feed(self._epochs()))
        self.assertEqual(entry["walk"]["stopped_by"], "cap")
        self.assertEqual(read_resume(), [held(cursor="4", mark=older)])

    def test_a_tail_page_that_fails_costs_the_tail_alone(self):
        """A stale cursor must not cost the board its new postings, and what
        is owed stays owed. Mutation: "a failed tail fails the board"."""
        epochs = self._epochs()
        self._run(feed(epochs))
        self._saved_in_full()
        fresh = [NOW_EPOCH - 60] + epochs
        write_resume([held(cursor="4")])
        client = feed(fresh, failing=(4,))
        with mock.patch("src.run.MAX_PAGES", 5):
            _, entry = self._run(client)
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(entry["new"], 1)
        self.assertTrue(entry["walk"]["tail"]["stopped_by"].startswith("failed"))
        self.assertIs(entry["capped"], True)
        self.assertEqual(read_resume(), [held(cursor="4")])

    def test_a_file_that_cannot_be_read_costs_the_tail_alone(self):
        """Mutation: "an unreadable file fails the board"."""
        storage.write_atomic(RESUME, "not json")
        _, entry = self._run(feed(self._epochs(2)))
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(entry["fetched"], 2)
        self.assertEqual(entry["walk_resume_failure"], "JSONDecodeError")

    def test_a_malformed_entry_is_no_held_walk(self):
        """Mutation: "a malformed entry is taken as a held walk"."""
        for bad in ({"board": SEARCH.board_id}, {"board": SEARCH.board_id, "cursor": "4"},
                    {"board": SEARCH.board_id, "cursor": "4", "mark": 7}):
            with self.subTest(bad=bad):
                write_resume([bad])
                _, entry = self._run(feed(self._epochs(2)))
                self.assertEqual(entry["status"], "ok")
                self.assertNotIn("tail", entry["walk"])

    def test_another_boards_entry_is_left_alone(self):
        """Mutation: "writing one board's entry drops the others'"."""
        other = held(cursor="7", board="startupjobs:sj-workplace-remote")
        write_resume([other])
        self._run(feed(self._epochs()))
        self.assertEqual(read_resume()[0], other)
        self.assertEqual(len(read_resume()), 2)

    def test_a_run_with_nothing_capped_writes_no_file(self):
        """One serialisation, and a run that changes nothing changes nothing.
        Mutation: "every walk rewrites the file"."""
        self._run(feed(self._epochs(2)))
        self.assertIsNone(read_resume())

    def test_with_the_private_store_down_nothing_is_read_or_written(self):
        """Its file was not restored and nothing could reach origin.
        Mutation: "the held walk is read with the private store down"."""
        write_resume([held()])
        run = Run([SEARCH], feed(self._epochs()), now=NOW, matcher=MATCHER,
                  private_unavailable=True)
        log = {}
        self.assertIsNone(run._held_walk(SEARCH, log))
        run._keep_walk(SEARCH, None, held(cursor="9"))
        self.assertEqual(read_resume(), [held()])

    def test_the_file_reaches_the_private_branch(self):
        """Or the next run could not read on from it. Mutation: "the file is
        left out of the private push"."""
        write_resume([held()])
        files = private_store.files_to_push(storage.layout(False))
        self.assertIn("agreement/%s" % WALK_RESUME_FILE, files)

    def test_the_capped_warning_says_the_next_walk_reads_on(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self._run(feed(self._epochs()))
        self.assertIn("::warning::%s: the walk reached its cap" % SEARCH.board_id, out.getvalue())
        self.assertIn("the next walk reads on", out.getvalue())


class TestTheCapHoldsTheSearch(unittest.TestCase):
    def test_the_morning_walk_can_read_the_whole_search_in_one_run(self):
        """The operator's yes of 2026-11-08 UTC: the search held 102 pages that
        day, and only a walk read to the end counts for the closure test and
        the agreement check. And it leaves the run its ceiling. Mutation: "the
        cap goes back under the size of the search"."""
        from src.http_client import DEFAULT_BUDGET
        from src.run import MAX_PAGES
        self.assertEqual(MAX_PAGES, 130)
        # About 105 requests a run go to every other board (the runs of 11-08).
        self.assertLess(MAX_PAGES + 105, DEFAULT_BUDGET)


if __name__ == "__main__":
    unittest.main()
