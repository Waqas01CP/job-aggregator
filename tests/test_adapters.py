"""Adapters, tested against sanitised cassettes of real responses.

Written from the brief's measured field list, not from the adapter code. The
brief names the fields for each platform and says not to re-derive them, so the
expected field names here are copied from the brief.
"""

import copy
import json
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import greenhouse, lever
from src.adapters.base import AdapterError, Posting
from src.config import Board

CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cassettes")

GH_BOARD = Board(platform="greenhouse", slug="careem")
SPEECHIFY = Board(platform="greenhouse", slug="speechify",
                  normalisations=("strip_location_suffix",))
LV_BOARD = Board(platform="lever", slug="smart-working-solutions",
                 employer_alias="Smart Working Solutions")
LV_NO_ALIAS = Board(platform="lever", slug="smart-working-solutions")


def cassette(name):
    with open(os.path.join(CASSETTES, name), encoding="utf-8") as f:
        return json.load(f)


class TestGreenhouse(unittest.TestCase):
    def setUp(self):
        self.payload = cassette("greenhouse-careem.json")

    def test_url_is_the_documented_endpoint(self):
        self.assertEqual(greenhouse.url_for(GH_BOARD),
                         "https://boards-api.greenhouse.io/v1/boards/careem/jobs")

    def test_url_never_requests_content(self):
        """`?content=true` adds description text at 9.5x payload, which
        ADR-0011 keeps out of this repository."""
        self.assertNotIn("content=true", greenhouse.url_for(GH_BOARD))

    def test_parses_every_posting_with_no_problems(self):
        result = greenhouse.parse(self.payload, GH_BOARD)
        self.assertEqual(len(result.postings), 21)
        self.assertEqual(result.problems, [])

    def test_reads_the_measured_fields(self):
        p = greenhouse.parse(self.payload, GH_BOARD).postings[0]
        self.assertTrue(p.title)
        self.assertEqual(p.employer, "Careem")
        self.assertEqual(p.employer_provenance, "payload")
        self.assertTrue(p.url.startswith("https://"))
        self.assertEqual(p.url_provenance, "payload")
        self.assertEqual(p.published_field, "first_published")
        self.assertEqual(p.source, "greenhouse")
        self.assertEqual(p.board_id, "greenhouse:careem")

    def test_publication_times_are_utc_aware(self):
        """Stored in UTC so rows are comparable without reading an offset."""
        for p in greenhouse.parse(self.payload, GH_BOARD).postings:
            self.assertIsNotNone(p.published_at.tzinfo)
            self.assertEqual(p.published_at.utcoffset(), timezone.utc.utcoffset(None))

    def test_offset_is_converted_not_discarded(self):
        """A -04:00 timestamp is four hours later in UTC. Dropping the offset
        would shift every US posting by four hours and still look plausible."""
        payload = {"jobs": [{"id": 1, "title": "Engineer",
                             "absolute_url": "https://x.test/1",
                             "first_published": "2026-09-09T03:36:17-04:00",
                             "company_name": "X"}]}
        p = greenhouse.parse(payload, GH_BOARD).postings[0]
        self.assertEqual(p.published_at,
                         datetime(2026, 9, 9, 7, 36, 17, tzinfo=timezone.utc))

    def test_wrong_envelope_raises(self):
        """A board that changes shape stops the board. It is not half-parsed."""
        with self.assertRaises(AdapterError):
            greenhouse.parse([], GH_BOARD)
        with self.assertRaises(AdapterError):
            greenhouse.parse({"postings": []}, GH_BOARD)

    def test_one_broken_posting_does_not_cost_the_board(self):
        payload = copy.deepcopy(self.payload)
        payload["jobs"][0]["absolute_url"] = "/relative/path"
        result = greenhouse.parse(payload, GH_BOARD)
        self.assertEqual(len(result.postings), 20)
        self.assertEqual(len(result.problems), 1)
        self.assertIn("absolute", result.problems[0]["reason"])

    def test_missing_publication_date_is_a_problem_not_a_silent_drop(self):
        payload = copy.deepcopy(self.payload)
        del payload["jobs"][0]["first_published"]
        result = greenhouse.parse(payload, GH_BOARD)
        self.assertEqual(len(result.problems), 1)
        self.assertIn("first_published", result.problems[0]["reason"])

    def test_a_naive_timestamp_is_rejected(self):
        """No offset means no way to know what instant it names."""
        payload = {"jobs": [{"id": 1, "title": "E", "absolute_url": "https://x.test/1",
                             "first_published": "2026-09-09T03:36:17"}]}
        result = greenhouse.parse(payload, SPEECHIFY)
        self.assertEqual(result.postings, [])
        self.assertEqual(len(result.problems), 1)

    def test_speechify_cassette_parses_whole(self):
        result = greenhouse.parse(cassette("greenhouse-speechify-titles.json"), SPEECHIFY)
        self.assertEqual(len(result.postings), 1086)
        self.assertEqual(result.problems, [])


class TestLever(unittest.TestCase):
    def setUp(self):
        self.payload = cassette("lever-smart-working-solutions.json")

    def test_url_is_the_documented_endpoint(self):
        self.assertEqual(
            lever.url_for(LV_BOARD),
            "https://api.lever.co/v0/postings/smart-working-solutions?mode=json")

    def test_parses_every_posting(self):
        result = lever.parse(self.payload, LV_BOARD)
        self.assertEqual(len(result.postings), 6)
        self.assertEqual(result.problems, [])

    def test_reads_the_measured_fields(self):
        p = lever.parse(self.payload, LV_BOARD).postings[0]
        self.assertTrue(p.title)
        self.assertTrue(p.url.startswith("https://jobs.lever.co/"))
        self.assertEqual(p.published_field, "createdAt")
        self.assertEqual(p.source, "lever")

    def test_employer_is_derived_from_the_slug_and_says_so(self):
        """ADR-0026: a derived employer is never indistinguishable from a
        returned one."""
        for p in lever.parse(self.payload, LV_BOARD).postings:
            self.assertEqual(p.employer, "Smart Working Solutions")
            self.assertEqual(p.employer_provenance, "slug")

    def test_absent_alias_is_recorded_not_guessed(self):
        """ADR-0026 forbids guessing an expansion. Without an alias the
        employer is unresolved, and the row must say so rather than carrying
        the raw slug as though it were a name."""
        for p in lever.parse(self.payload, LV_NO_ALIAS).postings:
            self.assertIsNone(p.employer)
            self.assertIsNone(p.employer_provenance)

    def test_epoch_milliseconds_are_converted(self):
        """1789018446882 is 2026-09-10T05:34:06.882Z, measured in the spike."""
        payload = [{"id": "a", "text": "Engineer",
                    "hostedUrl": "https://jobs.lever.co/x/a",
                    "createdAt": 1789018446882}]
        p = lever.parse(payload, LV_BOARD).postings[0]
        self.assertEqual(p.published_at,
                         datetime(2026, 9, 10, 5, 34, 6, 882000, tzinfo=timezone.utc))

    def test_seconds_mistaken_for_milliseconds_is_rejected(self):
        """The case built to defeat a naive divide: a 10-digit epoch would
        date a 2026 posting to 1970 and pass every downstream check."""
        payload = [{"id": "a", "text": "Engineer",
                    "hostedUrl": "https://jobs.lever.co/x/a",
                    "createdAt": 1789018446}]
        result = lever.parse(payload, LV_BOARD)
        self.assertEqual(result.postings, [])
        self.assertIn("epoch ms", result.problems[0]["reason"])

    def test_boolean_createdat_is_rejected(self):
        """True is an int in Python and would otherwise become 1970."""
        payload = [{"id": "a", "text": "E", "hostedUrl": "https://x.test/a",
                    "createdAt": True}]
        self.assertEqual(lever.parse(payload, LV_BOARD).postings, [])

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            lever.parse({"jobs": []}, LV_BOARD)

    def test_location_comes_from_categories(self):
        p = lever.parse(self.payload, LV_BOARD).postings[0]
        self.assertTrue(p.location)


class TestPostingInvariants(unittest.TestCase):
    def test_unknown_provenance_is_refused(self):
        with self.assertRaises(AdapterError):
            Posting(external_id="1", title="t", url="https://x.test/1",
                    published_at=datetime.now(timezone.utc), published_field="f",
                    published_raw="f", source="greenhouse", board_id="greenhouse:x",
                    employer="E", employer_provenance="vibes")

    def test_naive_publication_time_is_refused(self):
        with self.assertRaises(AdapterError):
            Posting(external_id="1", title="t", url="https://x.test/1",
                    published_at=datetime(2026, 1, 1), published_field="f",
                    published_raw="f", source="greenhouse", board_id="greenhouse:x")


if __name__ == "__main__":
    unittest.main(verbosity=2)
