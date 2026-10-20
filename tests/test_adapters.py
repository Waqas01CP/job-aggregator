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

from src.adapters import (ashby, greenhouse, hackernews, hasjob, hnjobs, jobicy, lever, manatal,
                          pythonorg, remoteok, smartrecruiters, weworkremotely, workable)
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

    def test_url_pages_from_one_twenty_a_page(self):
        """Ten a page unless asked, twenty at most, read on 2026-10-15: ITC's
        walk was 48 requests where 24 do. Mutation: "the page size is not
        asked"."""
        self.assertEqual(manatal.url_for(MN_BOARD),
                         "https://www.careers-page.com/api/v1.0/c/premiernx/jobs/"
                         "?page=1&page_size=20")
        self.assertEqual(manatal.url_for(MN_BOARD, 2),
                         "https://www.careers-page.com/api/v1.0/c/premiernx/jobs/"
                         "?page=2&page_size=20")

    def test_the_next_page_is_found_in_a_next_link_carrying_the_page_size(self):
        """The `next` link repeats what was asked; only its page is read."""
        page = {"results": [], "next": "https://www.careers-page.com/api/v1.0/c/x/jobs/"
                                       "?page=3&page_size=20"}
        self.assertEqual(manatal.next_cursor(page), 3)

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


WK_BOARD = Board(platform="workable", slug="igate-technologies", employer_alias="iGATE Technology")


class TestWorkable(unittest.TestCase):
    """Workable's documented endpoint. Cassette: iGATE Technology's board of
    2026-10-04, sanitised, envelope included."""

    def setUp(self):
        self.payload = cassette("workable-igate-technologies.json")

    def test_url_is_the_documented_endpoint_with_descriptions(self):
        self.assertEqual(workable.url_for(WK_BOARD),
                         "https://www.workable.com/api/accounts/igate-technologies?details=true")

    def test_parses_every_posting(self):
        result = workable.parse(self.payload, WK_BOARD)
        self.assertEqual(len(result.postings), 15)
        self.assertEqual(result.problems, [])

    def test_the_date_is_the_day_published_at_its_start_in_utc(self):
        entry = dict(self.payload["jobs"][0], published_on="2026-10-03")
        p = workable.parse({"jobs": [entry]}, WK_BOARD).postings[0]
        self.assertEqual(p.published_at, datetime(2026, 10, 3, tzinfo=timezone.utc))
        self.assertEqual(p.published_field, "published_on")

    def test_a_posting_without_a_readable_date_is_a_problem(self):
        for bad in (None, "", "03-10-2026", "2026-10-03T00:00:00Z"):
            with self.subTest(bad=bad):
                entry = dict(self.payload["jobs"][0], published_on=bad)
                result = workable.parse({"jobs": [entry]}, WK_BOARD)
                self.assertEqual(result.postings, [])
                self.assertIn("published_on", result.problems[0]["reason"])

    def test_the_link_is_the_jobs_own_page_not_its_form(self):
        p = workable.parse(self.payload, WK_BOARD).postings[0]
        self.assertEqual(p.url, self.payload["jobs"][0]["url"])
        self.assertFalse(p.url.endswith("/apply"))

    def test_employer_from_the_account_else_the_alias(self):
        p = workable.parse(self.payload, WK_BOARD).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), ("iGATE Technology", "envelope"))
        nameless = dict(self.payload, name="")
        p = workable.parse(nameless, WK_BOARD).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), ("iGATE Technology", "slug"))
        p = workable.parse(nameless, Board(platform="workable", slug="x")).postings[0]
        self.assertEqual((p.employer, p.employer_provenance), (None, None))

    def test_the_place_and_its_country_codes(self):
        entry = dict(self.payload["jobs"][0], city="Lahore", state="Punjab", country="Pakistan",
                     locations=[{"countryCode": "PK"}, {"countryCode": "AE"}])
        p = workable.parse({"jobs": [entry]}, WK_BOARD).postings[0]
        self.assertEqual((p.location, p.places), ("Lahore, Punjab, Pakistan", ("PK", "AE")))

    def test_remote_comes_from_telecommuting_until_a_workplace_is_stated(self):
        entry = dict(self.payload["jobs"][0], telecommuting=True)
        entry.pop("workplace_type", None)
        self.assertEqual(workable.parse({"jobs": [entry]}, WK_BOARD).postings[0].workplace, "remote")
        entry["telecommuting"] = False
        self.assertIsNone(workable.parse({"jobs": [entry]}, WK_BOARD).postings[0].workplace)
        entry["workplace_type"] = "on_site"
        self.assertEqual(workable.parse({"jobs": [entry]}, WK_BOARD).postings[0].workplace, "on_site")

    def test_the_description_goes_to_the_reader_and_the_posting_whole_to_the_store(self):
        entry = dict(self.payload["jobs"][0], description="<p>x</p>")
        p = workable.parse({"jobs": [entry]}, WK_BOARD).postings[0]
        self.assertEqual(p.description, ("<p>x</p>",))
        self.assertEqual(p.raw, entry)

    def test_the_stated_level_is_read_from_experience(self):
        """Brief 13, the Senior change's build: `experience` is the level the
        source states, verbatim; empty or absent is no level, which the
        level rule keeps. The cassette's board states Director twice and
        Mid-Senior level three times. Mutation: "the Workable adapter reads
        no level"."""
        postings = workable.parse(self.payload, WK_BOARD).postings
        counts = {}
        for p in postings:
            counts[p.levels] = counts.get(p.levels, 0) + 1
        self.assertEqual(counts, {("Director",): 2, ("Mid-Senior level",): 3, None: 10})
        entry = dict(self.payload["jobs"][0], experience="  Entry level ")
        self.assertEqual(workable.parse({"jobs": [entry]}, WK_BOARD).postings[0].levels,
                         ("Entry level",))
        entry.pop("experience")
        self.assertIsNone(workable.parse({"jobs": [entry]}, WK_BOARD).postings[0].levels)

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            workable.parse({"results": []}, WK_BOARD)


SR_BOARD = Board(platform="smartrecruiters", slug="OneScreen", employer_alias="OneScreen")


class TestSmartRecruiters(unittest.TestCase):
    """SmartRecruiters' public Posting API. Cassettes: OneScreen's and
    SeekaTechnology's boards and one detail each, 2026-10-17, sanitised."""

    def setUp(self):
        self.payload = cassette("smartrecruiters-onescreen.json")
        self.seeka = cassette("smartrecruiters-seekatechnology.json")
        self.detail = cassette("smartrecruiters-onescreen-detail.json")

    def entry(self, **extra):
        return dict(self.payload["content"][0], **extra)

    def one(self, entry, board=SR_BOARD):
        return smartrecruiters.parse({"content": [entry]}, board).postings[0]

    def test_the_list_is_read_by_offset_to_its_end(self):
        """Mutation: "the SmartRecruiters walk stops after the first
        page"."""
        self.assertEqual(smartrecruiters.url_for(SR_BOARD),
                         "https://api.smartrecruiters.com/v1/companies/OneScreen/postings"
                         "?limit=100&offset=0")
        self.assertEqual(smartrecruiters.url_for(SR_BOARD, 100)[-10:], "offset=100")
        page = {"content": [{}] * 100, "offset": 0, "totalFound": 130}
        self.assertEqual(smartrecruiters.next_cursor(page), 100)
        self.assertIsNone(smartrecruiters.next_cursor(
            {"content": [{}] * 30, "offset": 100, "totalFound": 130}))
        self.assertIsNone(smartrecruiters.next_cursor(self.payload))
        self.assertFalse(smartrecruiters.stop_after(page, "2099-01-01"))

    def test_parses_every_posting_on_both_boards(self):
        for payload in (self.payload, self.seeka):
            result = smartrecruiters.parse(payload, SR_BOARD)
            self.assertEqual((len(result.postings), result.problems), (10, []))

    def test_the_date_is_released_date_in_utc(self):
        """The operator's decision of 2026-10-17: trusted as the
        publication date."""
        p = self.one(self.entry())
        self.assertEqual(p.published_at, datetime(2026, 10, 1, 19, 44, 1, 110000,
                                                  tzinfo=timezone.utc))
        self.assertEqual(p.published_field, "releasedDate")
        for bad in (None, "", "yesterday", "2026-10-01T19:44:01"):
            with self.subTest(bad=bad):
                result = smartrecruiters.parse({"content": [self.entry(releasedDate=bad)]},
                                               SR_BOARD)
                self.assertEqual(result.postings, [])
                self.assertIn("releasedDate", result.problems[0]["reason"])

    def test_the_link_is_the_details_page_else_one_built_from_the_list(self):
        """Read from the list alone, as every run after a posting's first
        sight reads it, the link is the page built from the company and the
        id, which answered 200 on 2026-10-17. Mutation: "the built link
        replaces the detail's"."""
        p = self.one(self.entry())
        self.assertEqual((p.url, p.url_provenance),
                         ("https://jobs.smartrecruiters.com/OneScreen/744000153018507",
                          "constructed"))
        merged = self.entry(**smartrecruiters.from_detail(self.detail))
        p = self.one(merged)
        self.assertEqual((p.url, p.url_provenance), (self.detail["postingUrl"], "payload"))

    def test_the_employer_is_the_postings_company_else_the_alias(self):
        p = self.one(self.entry())
        self.assertEqual((p.employer, p.employer_provenance), ("OneScreen", "payload"))
        p = self.one(self.entry(company={"identifier": "OneScreen", "name": ""}))
        self.assertEqual((p.employer, p.employer_provenance), ("OneScreen", "slug"))

    def test_the_place_without_its_empty_and_repeated_parts_and_its_country(self):
        p = self.one(self.entry(location={"fullLocation": "Islamabad,, Islamabad, Pakistan",
                                          "city": "Islamabad", "country": "pk"}))
        self.assertEqual((p.location, p.places), ("Islamabad, Pakistan", ("PK",)))

    def test_remote_and_hybrid_are_read_and_neither_says_nothing(self):
        """Mutation: "SmartRecruiters' remote is not read"."""
        workplaces = [p.workplace for p in smartrecruiters.parse(self.seeka, SR_BOARD).postings]
        self.assertEqual(workplaces[:3], ["hybrid", "remote", "remote"])
        p = self.one(self.entry())
        self.assertIsNone(p.workplace)

    def test_the_stated_level_is_the_experience_levels_label(self):
        """OneScreen labels one posting Executive, which the level rule
        drops. Mutation: "the SmartRecruiters adapter reads no level"."""
        levels = {p.levels for p in smartrecruiters.parse(self.payload, SR_BOARD).postings}
        self.assertEqual(levels, {("Entry Level",), ("Executive",), ("Mid-Senior Level",)})

    def test_the_description_is_the_job_ads_sections_and_none_when_unread(self):
        """Not read is not the same as none: the list alone gives None, a
        detail gives its four sections, and a job ad with no sections an
        empty tuple."""
        self.assertIsNone(self.one(self.entry()).description)
        merged = self.entry(**smartrecruiters.from_detail(self.detail))
        self.assertEqual(self.one(merged).description, ("STRIPPED",) * 4)
        self.assertEqual(self.one(self.entry(jobAd={"sections": {}})).description, ())

    def test_the_detail_gives_the_posting_its_link_and_job_ad_and_nothing_else(self):
        self.assertEqual(set(smartrecruiters.from_detail(self.detail)), {"postingUrl", "jobAd"})
        self.assertEqual(smartrecruiters.from_detail(None), {})
        self.assertEqual(smartrecruiters.detail_url(SR_BOARD, "744000153018507"),
                         "https://api.smartrecruiters.com/v1/companies/OneScreen/postings/"
                         "744000153018507")

    def test_wrong_envelope_raises(self):
        with self.assertRaises(AdapterError):
            smartrecruiters.parse({"jobs": []}, SR_BOARD)


AB_BOARD = Board(platform="ashby", slug="Overjet", employer_alias="Overjet")
AB_NO_ALIAS = Board(platform="ashby", slug="Overjet")
# Overjet's postings, by id, as the cassette of 2026-10-17 holds them.
EGYPT_AND_PAKISTAN = "50c2eb16-5800-4cbb-bd78-341c8af84c41"
NO_ADDRESS = "daca62f6-04e0-4485-b714-be3d47b11c1c"
HYBRID = "482071c4-40ac-4e53-94dc-f6c4f451b0a7"
ON_SITE = "93a5111a-8e11-4444-81d8-40e55739bf4c"


class TestAshby(unittest.TestCase):
    """Ashby's public job board API. Cassettes: Overjet's and
    deeter-analytics' boards, 2026-10-17, sanitised."""

    def setUp(self):
        self.payload = cassette("ashby-overjet.json")
        self.deeter = cassette("ashby-deeter-analytics.json")

    def entry(self, external_id=EGYPT_AND_PAKISTAN, **extra):
        [found] = [j for j in self.payload["jobs"] if j["id"] == external_id]
        return dict(found, **extra)

    def one(self, entry, board=AB_BOARD):
        return ashby.parse({"jobs": [entry]}, board).postings[0]

    def test_one_request_a_board_on_the_documented_endpoint(self):
        self.assertEqual(ashby.url_for(AB_BOARD),
                         "https://api.ashbyhq.com/posting-api/job-board/Overjet"
                         "?includeCompensation=true")
        self.assertFalse(getattr(ashby, "PAGINATED", False))
        self.assertFalse(getattr(ashby, "DETAIL", False))

    def test_parses_every_posting_on_both_boards(self):
        for payload, count in ((self.payload, 30), (self.deeter, 3)):
            result = ashby.parse(payload, AB_BOARD)
            self.assertEqual((len(result.postings), result.problems), (count, []))

    def test_the_identity_is_the_id_and_the_link_its_job_page(self):
        p = self.one(self.entry())
        self.assertEqual((p.external_id, p.url, p.url_provenance),
                         (EGYPT_AND_PAKISTAN,
                          "https://jobs.ashbyhq.com/Overjet/" + EGYPT_AND_PAKISTAN, "payload"))
        for bad in (None, "", "/Overjet/" + EGYPT_AND_PAKISTAN):
            with self.subTest(bad=bad):
                result = ashby.parse({"jobs": [self.entry(jobUrl=bad)]}, AB_BOARD)
                self.assertEqual(result.postings, [])
                self.assertIn("jobUrl", result.problems[0]["reason"])
        for field in ("id", "title"):
            with self.subTest(missing=field):
                result = ashby.parse({"jobs": [self.entry(**{field: ""})]}, AB_BOARD)
                self.assertEqual(result.postings, [])

    def test_the_date_is_published_at_in_utc(self):
        """Ashby's last publication, which a republish moves; the run keeps
        the first (tests.test_run.TestAshbyRepublish). Mutation: "Ashby's
        date keeps its own offset"."""
        p = self.one(self.entry(publishedAt="2026-09-18T22:31:20.502+05:00"))
        self.assertEqual(p.published_at, datetime(2026, 9, 18, 17, 31, 20, 502000,
                                                  tzinfo=timezone.utc))
        # Equal instants compare equal across offsets, so the offset itself.
        self.assertEqual(p.published_at.utcoffset().total_seconds(), 0)
        self.assertEqual(p.published_field, "publishedAt")
        for bad in (None, "", "yesterday", "2026-09-18T22:31:20"):
            with self.subTest(bad=bad):
                result = ashby.parse({"jobs": [self.entry(publishedAt=bad)]}, AB_BOARD)
                self.assertEqual(result.postings, [])
                self.assertIn("publishedAt", result.problems[0]["reason"])

    def test_the_employer_is_the_alias_since_no_posting_names_one(self):
        """ADR-0026, the Lever case: derived with its provenance, and its
        absence recorded rather than guessed. Mutation: "Ashby's employer is
        guessed from the slug"."""
        p = self.one(self.entry())
        self.assertEqual((p.employer, p.employer_provenance), ("Overjet", "slug"))
        p = self.one(self.entry(), board=AB_NO_ALIAS)
        self.assertEqual((p.employer, p.employer_provenance), (None, None))

    def test_every_place_is_read_the_postings_own_first(self):
        """Overjet's Egypt posting lists Pakistan second, so D13 must see
        both. Mutation: "Ashby's secondary locations are not read"."""
        p = self.one(self.entry())
        self.assertEqual((p.location, p.places), ("Egypt; Pakistan", ("Egypt", "Pakistan")))
        p = self.one(self.entry(NO_ADDRESS))
        self.assertEqual(p.location, "United States, Remote; Salt Lake City, UT; "
                                     "San Mateo, CA; NYC based (Remote)")
        self.assertEqual(p.places, ("United States",))
        bare = self.entry(NO_ADDRESS, secondaryLocations=[])
        self.assertEqual((self.one(bare).location, self.one(bare).places),
                         ("United States, Remote", None))

    def test_the_workplace_is_workplace_type_never_is_remote(self):
        """`isRemote` is true on Hybrid postings too. Mutation: "Ashby's
        workplace is read from isRemote"."""
        self.assertEqual(self.one(self.entry(HYBRID)).workplace, "Hybrid")
        self.assertEqual(self.one(self.entry(ON_SITE)).workplace, "OnSite")
        self.assertEqual(self.one(self.entry()).workplace, "Remote")
        self.assertIsNone(self.one(self.entry(workplaceType=None)).workplace)

    def test_no_level_is_stated(self):
        self.assertEqual({p.levels for p in ashby.parse(self.payload, AB_BOARD).postings},
                         {None})

    def test_the_description_is_in_the_list_and_none_is_an_empty_tuple(self):
        """Read on every sight, so a posting with no description carried
        none, never one not read. Mutation: "Ashby's missing description is
        read as not read"."""
        self.assertEqual(self.one(self.entry()).description, ("STRIPPED",))
        self.assertEqual(self.one(self.entry(descriptionHtml="")).description, ())
        missing = self.entry()
        del missing["descriptionHtml"]
        self.assertEqual(self.one(missing).description, ())

    def test_wrong_envelope_raises(self):
        for payload in ({"content": []}, [], {"jobs": None}):
            with self.subTest(payload=payload), self.assertRaises(AdapterError):
                ashby.parse(payload, AB_BOARD)


HN_BOARD = Board(platform="hackernews", slug="whoishiring")
HNJ_BOARD = Board(platform="hnjobs", slug="jobstories")


def hn_post(header, rest="<p>STRIPPED", **extra):
    """A Who is hiring post shaped as Algolia gives it."""
    return dict({"id": 49900001, "type": "comment", "story_id": 49922569,
                 "created_at": "2026-10-05T12:00:00.000Z", "text": header + rest,
                 "author": "STRIPPED", "children": []}, **extra)


class TestHackerNews(unittest.TestCase):
    """Hacker News' Who is hiring thread. Cassettes: October 2026's first 40
    posts, each its first line only, and the stories that find it, read
    2026-10-18 and sanitised."""

    def setUp(self):
        self.thread = cassette("hackernews-whoishiring.json")
        self.stories = cassette("hackernews-whoishiring-stories.json")

    def one(self, header, **extra):
        thread = dict(self.thread, children=[hn_post(header, **extra)])
        return hackernews.parse(thread, HN_BOARD).postings[0]

    def test_the_newest_who_is_hiring_thread_is_followed(self):
        """The account posts "Who wants to be hired?" beside it. Mutation:
        "the thread followed is not the newest"."""
        self.assertEqual(hackernews.url_for(HN_BOARD),
                         "https://hn.algolia.com/api/v1/search_by_date?tags=story,"
                         "author_whoishiring&hitsPerPage=10")
        self.assertEqual(hackernews.follow(HN_BOARD, self.stories),
                         "https://hn.algolia.com/api/v1/items/49922569")
        wanted = dict(self.stories, hits=[h for h in self.stories["hits"]
                                          if "hired" in h["title"]])
        self.assertIsNone(hackernews.follow(HN_BOARD, wanted))

    def test_parses_every_post_and_refuses_anything_but_the_thread(self):
        result = hackernews.parse(self.thread, HN_BOARD)
        self.assertEqual((len(result.postings), result.problems), (40, []))
        for payload in (self.stories, {"title": "Ask HN: Who wants to be hired?", "children": []},
                        []):
            with self.subTest(payload=type(payload).__name__), self.assertRaises(AdapterError):
                hackernews.parse(payload, HN_BOARD)

    def test_a_saved_post_is_read_again(self):
        """The re-read wraps a saved post with no thread around it (ADR-0040's
        and ADR-0058's re-read). Mutation: "a saved Hacker News post cannot
        be re-read"."""
        from src import facts
        post = hn_post("Acme | AI Engineer | Lahore | ONSITE", id=49900002)
        post.pop("children")
        texts = [json.dumps([{"identity": "hackernews:49900002", "board_id": HN_BOARD.board_id,
                              "fetched_at": "2026-10-18T03:19:48.000000Z", "posting": post}])]
        records, counts = facts.reread(texts, [HN_BOARD], {}, {"hackernews": hackernews})
        self.assertEqual((counts["read"], counts["unparseable"]), (1, 0))
        self.assertEqual(records["hackernews:49900002"]["workplace"], "on site")

    def test_the_first_line_is_the_title_and_ends_at_a_break(self):
        """Fastly's post ran its header into its description with a bare
        newline. Mutation: "the first line runs on past a line break"."""
        p = self.one("Acme | AI Engineer | Remote", rest="\nWe build things.<p>More")
        self.assertEqual(p.title, "Acme | AI Engineer | Remote")
        p = self.one("<i>Acme | AI Engineer</i>", rest="<br>We build.")
        self.assertEqual(p.title, "Acme | AI Engineer")
        long = self.one("Acme | " + "x" * 300)
        self.assertEqual(len(long.title), hackernews.TITLE_LIMIT)

    def test_the_employer_is_the_first_part_without_its_address(self):
        p = self.one('Smarkets (<a href="https:&#x2F;&#x2F;www.smarkets.com">'
                     'https:&#x2F;&#x2F;www.smarkets.com</a>) | Engineer | London, UK')
        self.assertEqual((p.employer, p.employer_provenance), ("Smarkets", "payload"))
        p = self.one("Ambito (ambito.io) – Founding AI Engineer")
        self.assertEqual(p.employer, "Ambito (ambito.io)")

    def test_the_place_is_the_line_after_the_company(self):
        p = self.one("Acme | AI Engineer | San Francisco, CA | ONSITE | $200k")
        self.assertEqual(p.location, "AI Engineer | San Francisco, CA | ONSITE | $200k")
        self.assertIsNone(p.places)

    def test_the_workplace_is_read_from_the_line_and_remote_wins(self):
        """A remote option makes it remote; "no remote" is not one.
        Mutation: "a post saying both on site and remote reads on site"."""
        for header, want in (("Acme | Engineer | ONSITE", "on site"),
                             ("Acme | Engineer | In-person, NYC", "on site"),
                             ("Acme | Engineer | NYC (Hybrid)", "hybrid"),
                             ("Acme | Engineer | ONSITE or REMOTE", "remote"),
                             ("Acme | Engineer | Onsite, no remote", "on site"),
                             ("Acme | Engineer | NYC", None)):
            with self.subTest(header=header):
                self.assertEqual(self.one(header).workplace, want)

    def test_the_link_is_the_posts_own_page_on_hacker_news(self):
        """ADR-0063: a second-wave posting links to its source's own page.
        Mutation: "a Hacker News post links nowhere of its own"."""
        p = self.one("Acme | Engineer | Remote", id=49912345)
        self.assertEqual((p.url, p.url_provenance, p.source),
                         ("https://news.ycombinator.com/item?id=49912345", "constructed",
                          "hackernews"))

    def test_a_deleted_post_is_passed_over_and_replies_are_not_kept(self):
        thread = dict(self.thread, children=[
            hn_post("", rest="", text=None, author=None),
            hn_post("Acme | Engineer | Remote", children=[{"id": 2, "text": "a reply"}])])
        result = hackernews.parse(thread, HN_BOARD)
        self.assertEqual((len(result.postings), result.problems), (1, []))
        self.assertNotIn("children", result.postings[0].raw)
        self.assertEqual(result.postings[0].published_at,
                         datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc))


class TestHnJobs(unittest.TestCase):
    """Hacker News' job stories. Cassette: the 13 of the 30 days to
    2026-10-17, read 2026-10-18 and sanitised."""

    def setUp(self):
        self.payload = cassette("hnjobs-job.json")

    def test_parses_every_story(self):
        self.assertEqual(hnjobs.url_for(HNJ_BOARD),
                         "https://hn.algolia.com/api/v1/search_by_date?tags=job&hitsPerPage=100")
        result = hnjobs.parse(self.payload, HNJ_BOARD)
        self.assertEqual((len(result.postings), result.problems), (13, []))
        with self.assertRaises(AdapterError):
            hnjobs.parse({"children": []}, HNJ_BOARD)

    def test_the_employer_is_the_title_before_its_batch(self):
        for title, want in (("Coris (YC S22) Is Hiring Back End Engineer", "Coris"),
                            ("Flexport Is Hiring a Biz Ops Leader in Office of CEO", "Flexport"),
                            ("Launch HN: a product, not a job", None)):
            with self.subTest(title=title):
                self.assertEqual(hnjobs.employer_of(title), want)

    def test_the_link_is_the_storys_own_page_and_no_text_is_none(self):
        """ADR-0063. Mutation: "a job story links to the employer's page"."""
        [p] = [p for p in hnjobs.parse(self.payload, HNJ_BOARD).postings
               if p.title.startswith("Coris")]
        self.assertEqual(p.url, "https://news.ycombinator.com/item?id=%s" % p.external_id)
        self.assertEqual((p.source, p.description, p.employer), ("hnjobs", (), "Coris"))


JB_BOARD = Board(platform="jobicy", slug="jobicy-remote")


class TestJobicy(unittest.TestCase):
    """Jobicy's public Jobs API. Cassette: the first 30 of its first page of
    2026-10-18, sanitised."""

    def setUp(self):
        self.payload = cassette("jobicy-remote.json")

    def entry(self, **extra):
        return dict(self.payload["jobs"][0], **extra)

    def one(self, entry):
        return jobicy.parse({"jobs": [entry]}, JB_BOARD).postings[0]

    def test_parses_every_posting(self):
        result = jobicy.parse(self.payload, JB_BOARD)
        self.assertEqual((len(result.postings), result.problems), (30, []))
        with self.assertRaises(AdapterError):
            jobicy.parse({"hits": []}, JB_BOARD)

    def test_the_feed_is_read_page_by_page_by_its_cursor(self):
        """Mutation: "the Jobicy walk stops after the first page"."""
        self.assertEqual(jobicy.url_for(JB_BOARD),
                         "https://jobicy.com/api/v2/remote-jobs?count=200")
        self.assertEqual(jobicy.url_for(JB_BOARD, "a/b+c"),
                         "https://jobicy.com/api/v2/remote-jobs?count=200&cursor=a%2Fb%2Bc")
        self.assertEqual(jobicy.next_cursor(self.payload), self.payload["nextCursor"])
        self.assertIsNone(jobicy.next_cursor(dict(self.payload, hasMore=False)))

    def test_the_walk_stops_on_a_page_wholly_at_or_before_the_mark(self):
        """The whole page, never one posting. Mutation: "Jobicy's walk stops
        on one old posting"."""
        newest = max(j["pubDate"] for j in self.payload["jobs"])
        oldest = min(j["pubDate"] for j in self.payload["jobs"])
        as_z = lambda value: value.replace("+00:00", "Z")  # noqa: E731
        self.assertTrue(jobicy.stop_after(self.payload, as_z(newest)))
        self.assertFalse(jobicy.stop_after(self.payload, as_z(oldest)))
        self.assertFalse(jobicy.stop_after(self.payload, None))

    def test_any_states_no_level_and_every_posting_is_remote(self):
        """Mutation: "Jobicy's Any is read as a level"."""
        self.assertIsNone(self.one(self.entry(jobLevel="Any")).levels)
        self.assertEqual(self.one(self.entry(jobLevel="Senior")).levels, ("Senior",))
        p = self.one(self.entry(jobGeo="Germany,  Netherlands", jobTitle="A &amp; B"))
        self.assertEqual((p.location, p.workplace, p.title), ("Germany, Netherlands", "remote", "A & B"))

    def test_the_link_is_jobicys_own_page_and_jobicy_the_source(self):
        """ADR-0063 and Jobicy's terms: no listing shown as one's own or
        stripped of its attribution. Mutation: "a Jobicy posting is shown
        without its source"."""
        p = self.one(self.entry())
        self.assertTrue(p.url.startswith("https://jobicy.com/jobs/"))
        self.assertEqual((p.source, p.board_id, p.url_provenance),
                         ("jobicy", "jobicy:jobicy-remote", "payload"))


RO_BOARD = Board(platform="remoteok", slug="remoteok-feed")


class TestRemoteOK(unittest.TestCase):
    """Remote OK's API. Cassette: its legal notice and 29 postings of
    2026-10-18, sanitised."""

    def setUp(self):
        self.payload = cassette("remoteok-feed.json")

    def one(self, **extra):
        return remoteok.parse([dict(self.payload[1], **extra)], RO_BOARD).postings[0]

    def test_the_notice_is_passed_over_and_every_posting_parsed(self):
        """Its first element is its terms. Mutation: "the legal notice is
        read as a posting"."""
        self.assertIn("legal", self.payload[0])
        result = remoteok.parse(self.payload, RO_BOARD)
        self.assertEqual((len(result.postings), result.problems), (29, []))
        self.assertEqual(remoteok.url_for(RO_BOARD), "https://remoteok.com/api")
        with self.assertRaises(AdapterError):
            remoteok.parse({"jobs": []}, RO_BOARD)

    def test_an_empty_place_says_nothing_and_every_posting_is_remote(self):
        """Mutation: "an empty RemoteOK location is read as a place"."""
        self.assertEqual((self.one(location="").location, self.one(location="").workplace),
                         (None, "remote"))
        self.assertEqual(self.one(location="Brazil").location, "Brazil")

    def test_the_link_is_its_remote_ok_page_and_remote_ok_the_source(self):
        """ADR-0063 and Remote OK's terms: its link and its name with every
        row. Mutation: "a RemoteOK posting is shown without its source"."""
        p = self.one()
        self.assertTrue(p.url.lower().startswith("https://remoteok.com/remote-jobs/"))
        self.assertEqual((p.source, p.board_id, p.url_provenance),
                         ("remoteok", "remoteok:remoteok-feed", "payload"))


WWR_BOARD = Board(platform="weworkremotely", slug="wwr-feed")
WWR_RSS = ("<rss><channel><item><guid>https://weworkremotely.com/remote-jobs/acme-ai-engineer</guid>"
               "<title>Acme: AI Engineer</title>"
               "<link>https://weworkremotely.com/remote-jobs/acme-ai-engineer</link>"
               "<pubDate>Sun, 18 Oct 2026 07:31:05 +0000</pubDate>"
               "<region>Anywhere in the World</region><country></country>"
               "<description>&lt;p&gt;Text&lt;/p&gt;</description></item></channel></rss>")


class TestWeWorkRemotely(unittest.TestCase):
    """We Work Remotely's RSS. Cassette: the first 30 of its feed of
    2026-10-18, as its adapter decodes it, sanitised."""

    def setUp(self):
        self.payload = cassette("weworkremotely-feed.json")

    def item(self, **extra):
        return dict(self.payload["items"][0], **extra)

    def one(self, item):
        return weworkremotely.parse({"items": [item]}, WWR_BOARD).postings[0]

    def test_the_feed_is_decoded_into_items(self):
        doc = weworkremotely.decode(WWR_RSS)
        self.assertEqual([i["title"] for i in doc["items"]], ["Acme: AI Engineer"])
        for bad in ("not xml", "<rss></rss>"):
            with self.subTest(bad=bad), self.assertRaises(AdapterError):
                weworkremotely.decode(bad)

    def test_parses_every_item_and_splits_the_employer_from_the_role(self):
        result = weworkremotely.parse(self.payload, WWR_BOARD)
        self.assertEqual((len(result.postings), result.problems), (30, []))
        p = self.one(self.item(title="Airbnb: Engineering Manager, Payments"))
        self.assertEqual((p.employer, p.title, p.workplace),
                         ("Airbnb", "Engineering Manager, Payments", "remote"))

    def test_the_countries_named_are_the_place_and_else_the_region(self):
        """The region says "Anywhere in the World" beside a country that
        narrows it, on 17 of 88. Mutation: "We Work Remotely's countries are
        not read"."""
        us = [i for i in self.payload["items"] if "United States" in (i["country"] or "")][0]
        self.assertEqual(self.one(us).location, "United States of America")
        many = self.item(country="\U0001F1E6\U0001F1FA Australia, \U0001F1E8\U0001F1E6 Canada, "
                               "and \U0001F1FA\U0001F1F8 United States of America")
        self.assertEqual(self.one(many).location, "Australia; Canada; United States of America")
        uk = self.item(country="\U0001F1E8\U0001F1E6 Canada, and \U0001F1EC\U0001F1E7 United Kingdom of "
                               "Great Britain and Northern Ireland")
        self.assertEqual(self.one(uk).location,
                         "Canada; United Kingdom of Great Britain and Northern Ireland")
        self.assertEqual(self.one(self.item(country="")).location, "Anywhere in the World")

    def test_the_link_is_its_page_on_we_work_remotely_and_it_the_source(self):
        """ADR-0063 and its terms: links attributed back. Mutation: "a We
        Work Remotely posting is shown without its source"."""
        p = self.one(self.item())
        self.assertTrue(p.url.startswith("https://weworkremotely.com/remote-jobs/"))
        self.assertEqual((p.source, p.board_id, p.external_id),
                         ("weworkremotely", "weworkremotely:wwr-feed", p.url.rsplit("/", 1)[-1]))


PYTHONORG_BOARD = Board(platform="pythonorg", slug="pythonorg-feed")
PYTHONORG_RSS = ("<rss><channel><item><title>AI Engineer, Acme, Inc.</title>"
                 "<link>https://www.python.org/jobs/9001/</link>"
                 "<description>Remote, Worldwide\n&lt;p&gt;Text&lt;/p&gt;</description>"
                 "<guid>https://www.python.org/jobs/9001/</guid></item></channel></rss>")


class TestPythonOrg(unittest.TestCase):
    """Python.org's job board, its RSS. Cassette: its feed of 2026-10-20, all
    20 items, as its adapter decodes it, sanitised."""

    def setUp(self):
        self.payload = cassette("pythonorg-feed.json")

    def one(self, **extra):
        return pythonorg.parse({"items": [dict(self.payload["items"][0], **extra)]},
                               PYTHONORG_BOARD).postings[0]

    def test_the_feed_is_decoded_its_first_line_the_place(self):
        """The description's first line is the place: a field of its own, so
        a sanitised description leaves it. Mutation: "Python.org's place is
        read from the description"."""
        [item] = pythonorg.decode(PYTHONORG_RSS)["items"]
        self.assertEqual((item["title"], item["place"]),
                         ("AI Engineer, Acme, Inc.", "Remote, Worldwide"))
        self.assertNotIn("Remote", item["description"])
        for bad in ("not xml", "<rss></rss>"):
            with self.subTest(bad=bad), self.assertRaises(AdapterError):
                pythonorg.decode(bad)

    def test_parses_every_item_with_no_date_the_role_and_the_employer(self):
        """No date of any kind: a dateless posting, ordered after every dated
        one, as Manatal's. The employer is after the title's last comma, its
        legal form kept with it. Mutation: "a legal form is read as the
        employer"."""
        result = pythonorg.parse(self.payload, PYTHONORG_BOARD)
        self.assertEqual((len(result.postings), result.problems), (20, []))
        self.assertTrue(all(p.published_at is None for p in result.postings))
        p = self.one(title="SENIOR Back-End Python Engineer - FULLY REMOTE, ActivePrime, Inc.")
        self.assertEqual((p.title, p.employer),
                         ("SENIOR Back-End Python Engineer - FULLY REMOTE", "ActivePrime, Inc."))
        p = self.one(title="Software Engineer, Full Stack (Python, Rust), Gridnaut Recruiting")
        self.assertEqual((p.title, p.employer),
                         ("Software Engineer, Full Stack (Python, Rust)", "Gridnaut Recruiting"))
        self.assertEqual(self.one(title="Engineer").employer, None)
        self.assertEqual(self.one().location, "Remote, Worldwide")

    def test_the_link_is_its_page_on_python_org_and_it_the_source(self):
        """ADR-0063's Confirmation, annotated 2026-10-20: each row links to
        the source's own page and names it. Mutation: "a Python.org posting
        is shown without its source"."""
        p = self.one()
        self.assertTrue(p.url.startswith("https://www.python.org/jobs/"))
        self.assertEqual((p.source, p.board_id, p.external_id),
                         ("pythonorg", "pythonorg:pythonorg-feed",
                          p.url.rstrip("/").rsplit("/", 1)[-1]))
        self.assertEqual(pythonorg.parse({"items": [dict(self.payload["items"][0],
                                                         link="https://x.test/")]},
                                         PYTHONORG_BOARD).postings, [])


HASJOB_BOARD = Board(platform="hasjob", slug="hasjob-feed")
HASJOB_ATOM = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
               '<title type="text">AI Engineer</title>'
               "<id>https://hasjob.co/acme.test/abc12</id>"
               '<link href="https://hasjob.co/acme.test/abc12"/>'
               "<published>2026-10-19T11:55:35.484215+00:00</published>"
               "<location>Anywhere</location>"
               '<content type="html">&lt;p&gt;&lt;strong&gt;&lt;a href="https://acme.test/"&gt;'
               "Acme Labs&lt;/a&gt;&lt;/strong&gt;&lt;/p&gt;&lt;p&gt;Text&lt;/p&gt;</content>"
               "</entry></feed>")


class TestHasjob(unittest.TestCase):
    """Hasjob's Atom feed. Cassette: its feed of 2026-10-20, all 17 entries,
    as its adapter decodes it, sanitised."""

    def setUp(self):
        self.payload = cassette("hasjob-feed.json")

    def test_the_feed_is_decoded_and_the_byline_is_the_employer(self):
        """Mutation: "Hasjob's byline is not read as the employer"."""
        [p] = hasjob.parse(hasjob.decode(HASJOB_ATOM), HASJOB_BOARD).postings
        self.assertEqual((p.title, p.employer, p.location, p.external_id),
                         ("AI Engineer", "Acme Labs", "Anywhere", "abc12"))
        self.assertEqual(p.published_at.isoformat(), "2026-10-19T11:55:35.484215+00:00")
        for bad in ("not xml", "<rss></rss>"):
            with self.subTest(bad=bad), self.assertRaises(AdapterError):
                hasjob.decode(bad)

    def test_parses_every_entry_and_refuses_one_without_a_date(self):
        """Mutation: "a Hasjob posting with no date is kept"."""
        result = hasjob.parse(self.payload, HASJOB_BOARD)
        self.assertEqual((len(result.postings), result.problems), (17, []))
        undated = dict(self.payload["entries"][0], published="")
        result = hasjob.parse({"entries": [undated]}, HASJOB_BOARD)
        self.assertEqual((result.postings, len(result.problems)), ([], 1))

    def test_the_link_is_its_page_on_hasjob_and_it_the_source(self):
        """ADR-0063's Confirmation, annotated 2026-10-20: each row links to
        the source's own page and names it. Mutation: "a Hasjob posting is
        shown without its source"."""
        p = hasjob.parse({"entries": [self.payload["entries"][0]]}, HASJOB_BOARD).postings[0]
        self.assertTrue(p.url.startswith("https://hasjob.co/"))
        self.assertEqual((p.source, p.board_id, p.external_id),
                         ("hasjob", "hasjob:hasjob-feed", p.url.rsplit("/", 1)[-1]))


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
