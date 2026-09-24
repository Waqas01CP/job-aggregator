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


def write_config(boards):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"source": "test", "boards": boards}, f)
    return path


VALID = {"platform": "greenhouse", "slug": "careem", "normalisations": []}


class TestRealConfig(unittest.TestCase):
    def setUp(self):
        self.boards = load_boards()

    def test_eleven_ats_boards_plus_the_conditional_aggregator(self):
        """ADR-0009 fixes the slice at eleven employer boards. Himalayas is
        the conditional twelfth from ADR-0019 and is an aggregator, not an
        employer board, so it is counted separately."""
        ats = [b for b in self.boards if b.source_class == "ats"]
        aggregators = [b for b in self.boards if b.source_class == "aggregator"]
        self.assertEqual(len(ats), 11)
        self.assertEqual([b.slug for b in aggregators], ["browse"])
        self.assertEqual([b.platform for b in aggregators], ["himalayas"])

    def test_slugs_match_the_registry(self):
        gh = {b.slug for b in self.boards if b.platform == "greenhouse"}
        lv = {b.slug for b in self.boards if b.platform == "lever"}
        self.assertEqual(gh, REGISTRY_GREENHOUSE)
        self.assertEqual(lv, REGISTRY_LEVER)

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
                         {"greenhouse", "lever", "himalayas"})

    def test_source_class_separates_employer_boards_from_aggregators(self):
        """ADR-0020 routes raw storage by source class: employer rows to the
        public data branch, aggregator rows to local files never committed."""
        by_platform = {b.platform: b.source_class for b in self.boards}
        self.assertEqual(by_platform["greenhouse"], "ats")
        self.assertEqual(by_platform["lever"], "ats")
        self.assertEqual(by_platform["himalayas"], "aggregator")

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
        self.assert_rejected([{"platform": "ashby", "slug": "overjet"}], "not one of")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
