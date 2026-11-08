"""Board configuration, tested against the brief rather than the loader.

The brief: one entry per board, eleven boards, nine Greenhouse and two Lever,
slugs from the registry, per-source normalisation with only Speechify carrying
one. Every defeat case below is a config a careless edit could produce.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (Board, ConfigError, boards_missing_employer_alias,
                        is_publishable, load_boards)

# The eleven, as the registry records them. Part 3 for all but coderoad,
# which is Part 12. Written here so the test fails if the config drifts.
REGISTRY_GREENHOUSE = {"veeamsoftware", "careem", "speechify", "brkz", "globalli",
                       "gomotive", "joblogic", "banyancanopygroup", "coderoad"}
REGISTRY_LEVER = {"smart-working-solutions", "spreetail"}
# The operator's registry, Parts 3 and 11, read 2026-10-04: ADR-0059's first
# platform by measured yield, built 2026-10-07.
REGISTRY_MANATAL = {"abacus-consulting-3", "ahdus-technology-2", "spursol", "premiernx",
                    "itc-worldwide-info", "hazen-technologies", "codedistrict", "wadic-2",
                    "gigalabs-private-ltd"}
# Parts 3 and 11; four slugs found 2026-10-04 and added on the operator's yes,
# marked unproven. Built 2026-10-08.
REGISTRY_WORKABLE = {"igate-technologies", "creative-chaos", "thingtrax", "staunch",
                     "petra-brands", "inbox-business-technologies"}
# Parts 3 and 13, each board's company identifier as its job pages spell it.
# Built 2026-10-17.
REGISTRY_SMARTRECRUITERS = {"OneScreen", "SeekaTechnology"}
# Parts 3 and 12, each job board's name as its job pages spell it. Built
# 2026-10-17.
REGISTRY_ASHBY = {"Overjet", "deeter-analytics"}
# Not in the registry: found through the second wave and added on the
# operator's word of 2026-10-18 (ADR-0063, Brief 16 item 3).
DISCOVERED = {("ashby", "livekit"), ("ashby", "clickhouse"), ("ashby", "mastra"),
              ("lever", "postera")}
# Found through the a16z Speedrun talent network's feed, read once for
# discovery on 2026-10-20 (Brief 18, item 5): each keeps a posting read fresh.
DISCOVERED |= {("ashby", "cursor"), ("ashby", "elevenlabs"), ("ashby", "vesta"),
               ("ashby", "quora"), ("ashby", "realmalliance"), ("ashby", "espa"),
               ("ashby", "fal-ai"), ("ashby", "intangible.ai"), ("ashby", "protege"),
               ("ashby", "socket"), ("ashby", "sola"), ("greenhouse", "sourcegraph91"),
               ("greenhouse", "cresta"), ("lever", "pingwind")}


def write_config(boards):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"source": "test", "boards": boards}, f)
    return path


VALID = {"platform": "greenhouse", "slug": "careem", "normalisations": []}


class TestRealConfig(unittest.TestCase):
    def setUp(self):
        self.boards = load_boards()

    def test_thirty_four_ats_boards_plus_the_conditional_aggregator(self):
        """ADR-0009 fixed the slice at eleven employer boards; ADR-0059's
        Manatal adds nine, on 2026-10-07, Workable six, on 2026-10-08,
        SmartRecruiters two, on 2026-10-17, and Ashby two, on 2026-10-17; and
        four found through the second wave, on 2026-10-18; and fourteen
        through the a16z Speedrun network's feed, on 2026-10-20.
        Himalayas is the conditional
        aggregator from ADR-0019, not an employer board, so it is counted
        separately."""
        ats = [b for b in self.boards if b.source_class == "ats"]
        aggregators = [b for b in self.boards if b.source_class == "aggregator"]
        self.assertEqual(len(ats), 48)
        # The search endpoint filtered to the operator's country, since
        # 2026-09-26: the slug is the country.
        self.assertEqual([b.slug for b in aggregators],
                         ["pakistan", "whoishiring", "jobstories", "jobicy-remote",
                          "remoteok-feed", "wwr-feed", "pythonorg-feed",
                          "sj-workplace-remote", "sj-country-pk"])
        # Hasjob's board is out since 2026-10-21, the operator's decision on
        # its read: an Indian board, none of its postings one he can take.
        # Its adapter and contract check stay, so it returns by one line.
        # Hacker News, ADR-0063's second wave, is an aggregator too: its rows
        # keep to the private store (src/config.py, AGGREGATOR_PLATFORMS).
        self.assertEqual([b.platform for b in aggregators],
                         ["himalayas", "hackernews", "hnjobs", "jobicy", "remoteok",
                          "weworkremotely", "pythonorg", "startupjobs",
                          "startupjobs"])

    def test_slugs_match_the_registry(self):
        gh = {b.slug for b in self.boards if b.platform == "greenhouse"}
        lv = {b.slug for b in self.boards if b.platform == "lever"}
        self.assertEqual(gh, REGISTRY_GREENHOUSE | {s for p, s in DISCOVERED if p == "greenhouse"})
        self.assertEqual(lv, REGISTRY_LEVER | {s for p, s in DISCOVERED if p == "lever"})
        self.assertEqual({b.slug for b in self.boards if b.platform == "manatal"},
                         REGISTRY_MANATAL)
        self.assertEqual({b.slug for b in self.boards if b.platform == "workable"},
                         REGISTRY_WORKABLE)
        self.assertEqual({b.slug for b in self.boards if b.platform == "smartrecruiters"},
                         REGISTRY_SMARTRECRUITERS)
        self.assertEqual({b.slug for b in self.boards if b.platform == "ashby"},
                         REGISTRY_ASHBY | {s for p, s in DISCOVERED if p == "ashby"})

    def test_only_speechify_is_normalised(self):
        """ADR-0027: a normalisation is applied only where it was measured."""
        normalised = {b.slug for b in self.boards if b.normalisations}
        self.assertEqual(normalised, {"speechify"})
        speechify = next(b for b in self.boards if b.slug == "speechify")
        self.assertEqual(speechify.normalisations, ("strip_location_suffix",))

    def test_lever_boards_carry_an_employer_alias(self):
        """Lever returns no employer field, so without an alias the employer
        is unresolvable. ADR-0026."""
        self.assertEqual(boards_missing_employer_alias(self.boards), [])

    def test_greenhouse_boards_need_no_alias(self):
        """Greenhouse returns company_name, so an alias there would be a second
        copy of a fact the payload already carries."""
        for b in self.boards:
            if b.platform == "greenhouse":
                self.assertIsNone(b.employer_alias, b.slug)

    def test_source_is_the_platform(self):
        """ADR-0020 stores one file per source, so source names the file."""
        self.assertEqual({b.source for b in self.boards},
                         {"greenhouse", "lever", "himalayas", "manatal", "workable",
                          "smartrecruiters", "ashby", "hackernews", "hnjobs", "jobicy",
                          "remoteok", "weworkremotely", "pythonorg",
                          "startupjobs"})

    def test_source_class_separates_employer_boards_from_aggregators(self):
        """ADR-0020 routes raw storage by source class: employer rows to the
        public data branch, aggregator rows to local files never committed."""
        by_platform = {b.platform: b.source_class for b in self.boards}
        self.assertEqual(by_platform["greenhouse"], "ats")
        self.assertEqual(by_platform["lever"], "ats")
        self.assertEqual(by_platform["himalayas"], "aggregator")
        self.assertEqual(by_platform["manatal"], "ats")
        self.assertEqual(by_platform["workable"], "ats")

    def test_only_named_ats_sources_may_be_published(self):
        """ADR-0020, failing closed: a source nobody named stays local. Jobicy
        and Remotive are the two feeds that threaten termination for
        redistribution, and neither has an adapter, so both are unknown here."""
        self.assertTrue(is_publishable("greenhouse"))
        self.assertTrue(is_publishable("lever"))
        for source in ("himalayas", "jobicy", "remotive", "", None):
            self.assertFalse(is_publishable(source), source)


class TestDefeatCases(unittest.TestCase):
    """Each case is built to defeat the loader. A loader that accepts any of
    them is worse than none, because the run would look complete."""

    def assert_rejected(self, boards, fragment):
        path = write_config(boards)
        try:
            with self.assertRaises(ConfigError) as caught:
                load_boards(path)
            self.assertIn(fragment, str(caught.exception).lower())
        finally:
            os.unlink(path)

    def test_duplicate_board_is_rejected(self):
        self.assert_rejected([VALID, dict(VALID)], "duplicate")

    def test_unknown_platform_is_rejected(self):
        self.assert_rejected([{"platform": "breezy", "slug": "overjet"}], "not one of")

    def test_misspelled_normalisation_is_rejected(self):
        """A typo that silently did nothing would stop a board's location
        variants collapsing, invisibly."""
        self.assert_rejected(
            [{"platform": "greenhouse", "slug": "speechify",
              "normalisations": ["strip_location_sufix"]}], "not one of")

    def test_a_misspelled_poll_slot_is_rejected(self):
        """ADR-0048. A typo would never match the run's slot, and the source
        would be skipped on every scheduled run, silently."""
        self.assert_rejected(
            [{"platform": "himalayas", "slug": "browse", "poll_slots": ["mornign"]}],
            "not one of")

    def test_poll_slots_must_be_a_list(self):
        self.assert_rejected(
            [{"platform": "himalayas", "slug": "browse", "poll_slots": "morning"}],
            "expected a list")

    def test_url_in_the_slug_field_is_rejected(self):
        """A URL here builds a nonsense endpoint that 404s, which reads like a
        dead board rather than a config error."""
        self.assert_rejected(
            [{"platform": "greenhouse",
              "slug": "https://boards.greenhouse.io/careem"}], "url")

    def test_slug_with_whitespace_is_rejected(self):
        self.assert_rejected([{"platform": "greenhouse", "slug": "care em"}], "whitespace")

    def test_empty_slug_is_rejected(self):
        self.assert_rejected([{"platform": "greenhouse", "slug": ""}], "empty")

    def test_empty_board_list_is_rejected(self):
        self.assert_rejected([], "empty")

    def test_missing_file_is_rejected(self):
        with self.assertRaises(ConfigError):
            load_boards(os.path.join(tempfile.gettempdir(), "no-such-boards.json"))

    def test_malformed_json_is_rejected(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("{not json")
        try:
            with self.assertRaises(ConfigError) as caught:
                load_boards(path)
            self.assertIn("not valid json", str(caught.exception).lower())
        finally:
            os.unlink(path)

    def test_a_valid_config_still_loads(self):
        """The control. If this fails, the cases above prove nothing."""
        path = write_config([VALID])
        try:
            boards = load_boards(path)
        finally:
            os.unlink(path)
        self.assertEqual(len(boards), 1)
        self.assertIsInstance(boards[0], Board)
        self.assertEqual(boards[0].board_id, "greenhouse:careem")


class TestPublicDetail(unittest.TestCase):
    """The fifth audit's F21: two public logs could carry an aggregator's URL."""

    URL = "https://himalayas.app/jobs/api/search?country=pakistan&page=1"

    def test_an_aggregators_failure_names_no_url(self):
        """Mutation: "an aggregator's failure keeps its whole message"."""
        from src.config import public_detail
        from src.resilience import PermanentError, TransientError
        self.assertEqual(public_detail(PermanentError(self.URL, 404), "himalayas"),
                         "PermanentError 404")
        self.assertEqual(public_detail(TransientError(self.URL, "timed out", 3), "startupjobs"),
                         "TransientError")
        self.assertEqual(public_detail(ValueError(self.URL), "jobicy"), "ValueError")

    def test_a_source_nobody_named_stays_quiet(self):
        """Mutation: "an unknown source is treated as publishable"."""
        from src.config import public_detail
        self.assertEqual(public_detail(ValueError(self.URL), "nothing-known"), "ValueError")

    def test_a_publishable_sources_message_is_kept(self):
        """It helps to find the fault, and the board is public."""
        from src.config import public_detail
        self.assertEqual(public_detail(ValueError("no such key"), "greenhouse"),
                         "ValueError: no such key")

    def test_the_contract_logs_no_aggregators_url(self):
        """Mutation: "the contract log keeps an aggregator's URL"."""
        from src import contract
        from src.adapters import himalayas
        from src.config import Board
        from src.resilience import PermanentError

        class Client:
            def get_json(self, url, source, **kw):
                raise PermanentError(url, 404)
        entry = {}
        self.assertIsNone(contract.check_one("himalayas", himalayas,
                                             Board(platform="himalayas", slug="pakistan"),
                                             Client(), {}, entry, None, {}))
        self.assertEqual(entry, {"status": "unreachable", "detail": "PermanentError 404"})

    def test_the_run_log_keeps_no_aggregators_url(self):
        """Mutation: "the run log keeps an aggregator's URL"."""
        import os
        import shutil
        import tempfile
        from datetime import datetime, timezone
        from src.config import Board
        from src.filters import TitleMatcher
        from src.http_client import HttpClient
        from src.run import Run

        class Session:
            def get(_self, url, params=None, timeout=None, headers=None):
                class R:
                    status_code = 404
                    headers = {}
                    text = ""
                return R()
        folder, cwd = tempfile.mkdtemp(), os.getcwd()
        os.chdir(folder)
        self.addCleanup(shutil.rmtree, folder, True)
        self.addCleanup(os.chdir, cwd)
        client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
        log = Run([Board(platform="himalayas", slug="pakistan")], client,
                  now=datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
                  matcher=TitleMatcher()).execute()
        self.assertEqual(log["boards"][0]["status"], "failed")
        self.assertEqual(log["boards"][0]["detail"], "PermanentError 404")


if __name__ == "__main__":
    unittest.main(verbosity=2)
