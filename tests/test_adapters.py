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

from src.adapters import greenhouse, lever, manatal
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

    def test_url_is_the_documented_endpoint_with_descriptions(self):
        """The operator's D11, 2026-09-26: every field a board returns is
        kept, so the description is asked for. It goes to the private full
        branch only."""
        self.assertEqual(greenhouse.url_for(GH_BOARD),
                         "https://boards-api.greenhouse.io/v1/boards/careem/jobs?content=true")

    def test_each_posting_carries_its_entry_whole_and_uncompared(self):
        result = greenhouse.parse(self.payload, GH_BOARD)
        first = result.postings[0]
        self.assertIs(first.raw, self.payload["jobs"][0])
        other = greenhouse.parse(self.payload, GH_BOARD).postings[0]
        other.raw = {"changed": True}
        self.assertEqual(first, other, "the raw entry must not change equality")
        self.assertNotIn(", raw=", repr(first))

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


class TestTheSourcesOwnPlace(unittest.TestCase):
    """2026-10-02: where each source structures a posting's place, and how
    it is worked, read verbatim for the location rule. Mutations: "the
    adapter reads no office", "the adapter reads no country"."""

    def test_greenhouse_reads_each_office_and_a_country_field(self):
        result = greenhouse.parse(cassette("greenhouse-careem-content.json"), GH_BOARD)
        self.assertEqual(result.postings[1].places, ("Karachi, Pakistan", "Pakistan"))
        self.assertEqual(result.postings[0].places,
                         ("Dubai, United Arab Emirates", "United Arab Emirates"))

    def test_greenhouse_reads_a_work_type_field(self):
        entry = {"id": 1, "title": "AI Engineer", "absolute_url": "https://x.test/1",
                 "first_published": "2026-09-10T00:00:00-04:00", "location": {"name": "Lahore"},
                 "offices": [], "metadata": [
                     {"name": "Work Type", "value": "Office Based", "value_type": "single_select"},
                     {"name": "Country", "value": None, "value_type": "single_select"}]}
        [p] = greenhouse.parse({"jobs": [entry]}, GH_BOARD).postings
        self.assertEqual((p.workplace, p.places), ("Office Based", None))

    def test_lever_reads_the_country_code_and_the_workplace(self):
        postings = lever.parse(cassette("lever-smart-working-solutions.json"), LV_BOARD).postings
        self.assertEqual([(p.places, p.workplace) for p in postings[:2]],
                         [(("IN",), "remote"), (("PK",), "remote")])


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


MN_BOARD = Board(platform="manatal", slug="premiernx", employer_alias="Premier NX")
MN_NO_ALIAS = Board(platform="manatal", slug="premiernx")


class TestManatal(unittest.TestCase):
    """The career site's endpoint, which the operator accepted for all nine
    registry boards on 2026-10-07. Cassettes: Premier NX's two pages of
    2026-10-04, sanitised."""

    def setUp(self):
        self.page1 = cassette("manatal-premiernx-page1.json")
        self.page2 = cassette("manatal-premiernx-page2.json")

    def test_url_pages_from_one(self):
        self.assertEqual(manatal.url_for(MN_BOARD),
                         "https://www.careers-page.com/api/v1.0/c/premiernx/jobs/?page=1")
        self.assertEqual(manatal.url_for(MN_BOARD, 2),
                         "https://www.careers-page.com/api/v1.0/c/premiernx/jobs/?page=2")

    def test_the_next_page_is_read_from_next_and_the_last_has_none(self):
        self.assertEqual(manatal.next_cursor(self.page1), 2)
        self.assertIsNone(manatal.next_cursor(self.page2))
        self.assertIsNone(manatal.next_cursor({"next": "https://x.test/?page=two"}))

    def test_a_walk_never_stops_on_a_mark(self):
        """No dates, so nothing says where to stop: every page is read."""
        self.assertFalse(manatal.stop_after(self.page1, "2099-01-01T00:00:00Z"))

    def test_parses_every_posting_on_both_pages(self):
        for page, n in ((self.page1, 20), (self.page2, 12)):
            result = manatal.parse(page, MN_BOARD)
            self.assertEqual(len(result.postings), n)
            self.assertEqual(result.problems, [])

    def test_no_posting_carries_a_date(self):
        """Measured over 779 postings on 2026-10-04: none. A date guessed
        here would be one Manatal never gave."""
        for p in manatal.parse(self.page1, MN_BOARD).postings:
            self.assertIsNone(p.published_at)
            self.assertIsNone(p.published_field)

    def test_the_link_opens_the_postings_own_page(self):
        """By its `hash`, which opened the posting on 2026-10-07; its `id`
        does not."""
        entry = self.page1["results"][0]
        p = manatal.parse(self.page1, MN_BOARD).postings[0]
        self.assertEqual(p.url, "https://www.careers-page.com/premiernx/job/%s" % entry["hash"])
        self.assertEqual(p.url_provenance, "constructed")
        self.assertEqual(p.external_id, str(entry["id"]))

    def test_employer_from_the_payload_else_the_alias_else_unresolved(self):
        """ADR-0026: a posting naming its organisation keeps it; one naming
        none takes the configured alias and says so; without an alias it is
        recorded as unresolved, never guessed from the slug."""
        named = {"results": [{"id": 1, "hash": "H1", "position_name": "AI Engineer",
                              "organization_name": "Acme"}]}
        bare = {"results": [{"id": 2, "hash": "H2", "position_name": "AI Engineer"}]}
        p = manatal.parse(named, MN_BOARD).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), ("Acme", "payload"))
        p = manatal.parse(bare, MN_BOARD).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), ("Premier NX", "slug"))
        p = manatal.parse(bare, MN_NO_ALIAS).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), (None, None))

    def test_the_place_is_the_shown_location_else_its_parts(self):
        shown = {"results": [{"id": 1, "hash": "H", "position_name": "E",
                              "location_display": "Lahore, Punjab, Pakistan", "country": "Pakistan"}]}
        parts = {"results": [{"id": 1, "hash": "H", "position_name": "E", "city": "Karachi",
                              "state": "", "country": "Pakistan"}]}
        p = manatal.parse(shown, MN_BOARD).postings[0]
        self.assertEqual((p.location, p.places), ("Lahore, Punjab, Pakistan", ("Pakistan",)))
        p = manatal.parse(parts, MN_BOARD).postings[0]
        self.assertEqual(p.location, "Karachi, Pakistan")

    def test_a_posting_without_id_title_or_hash_is_a_problem_not_a_row(self):
        payload = {"results": [{"hash": "H", "position_name": "E"},
                               {"id": 2, "hash": "H"},
                               {"id": 3, "position_name": "E"}]}
        result = manatal.parse(payload, MN_BOARD)
        self.assertEqual(result.postings, [])
        self.assertEqual([p["reason"] for p in result.problems],
                         ["no id", "no position_name", "no hash, so no link to the posting"])

    def test_the_description_goes_to_the_reader_and_the_posting_whole_to_the_store(self):
        entry = {"id": 1, "hash": "H", "position_name": "E", "description": "<p>x</p>"}
        p = manatal.parse({"results": [entry]}, MN_BOARD).postings[0]
        self.assertEqual(p.description, ("<p>x</p>",))
        self.assertEqual(p.raw, entry)

    def test_a_posting_repeated_on_another_page_of_the_walk_is_kept_once(self):
        """ITC Worldwide's 24 pages of 2026-10-04 gave 477 reads of 338
        distinct postings: the pages shift between requests."""
        entry = {"id": 7, "hash": "H", "position_name": "AI Engineer"}
        result = manatal.parse({"results": [entry, dict(entry), {"id": 8, "hash": "J",
                                                                  "position_name": "E"}]}, MN_BOARD)
        self.assertEqual([p.external_id for p in result.postings], ["7", "8"])
        self.assertEqual(result.problems, [])

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            manatal.parse({"items": []}, MN_BOARD)


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
