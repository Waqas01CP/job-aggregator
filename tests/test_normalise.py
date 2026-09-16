"""The normaliser, tested from the brief.

The brief requires: one row shape for every source; employer read from the
payload where present and from the slug where not, recording which; the field
that supplied the ordering date recorded so a first-seen fallback is never
mistaken for a publication date; and the source recorded because ADR-0020
routes storage by it.
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import greenhouse
from src.adapters.base import Posting
from src.config import Board
from src.normalise import (FIELDS, NormaliseError, Row, dedupe_key, dumps,
                           fold, iso, loads, normalise, strip_location_suffix)

NOW = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
GH_BOARD = Board(platform="greenhouse", slug="careem")
SPEECHIFY = Board(platform="greenhouse", slug="speechify",
                  normalisations=("strip_location_suffix",))
LEVER_BOARD = Board(platform="lever", slug="spreetail", employer_alias="Spreetail")

CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cassettes")


def posting(**kw):
    base = dict(external_id="1", title="AI Engineer", url="https://x.test/1",
                published_at=datetime(2026, 9, 10, 5, 0, tzinfo=timezone.utc),
                published_field="first_published", published_raw="2026-09-10T05:00:00Z",
                source="greenhouse", board_id="greenhouse:careem",
                employer="Careem", employer_provenance="payload",
                url_provenance="payload", location="Karachi")
    base.update(kw)
    return Posting(**base)


class TestRowShape(unittest.TestCase):
    def test_record_carries_exactly_the_agreed_fields_in_order(self):
        """Adding a platform must add an adapter, never a column."""
        row = normalise([posting()], GH_BOARD, NOW)[0]
        self.assertEqual(list(row.as_record().keys()), list(FIELDS))

    def test_source_is_recorded(self):
        row = normalise([posting()], GH_BOARD, NOW)[0]
        self.assertEqual(row.source, "greenhouse")

    def test_no_description_field_exists_on_a_row(self):
        """ADR-0011. The shape itself is the guard: there is nowhere to put it."""
        record = normalise([posting()], GH_BOARD, NOW)[0].as_record()
        for key in record:
            self.assertNotIn("description", key.lower())
            self.assertNotIn("content", key.lower())


class TestOrderingDate(unittest.TestCase):
    def test_publication_date_supplies_the_ordering_date_when_present(self):
        row = normalise([posting()], GH_BOARD, NOW)[0]
        self.assertEqual(row.ordering_date_source, "publication")
        self.assertEqual(row.ordering_date, row.published_at)

    def test_first_seen_supplies_it_when_there_is_no_publication_date(self):
        """ADR-0007's fallback. The case that matters is Manatal, which
        returns no date field at all."""
        row = normalise([posting(published_at=None, published_field=None)],
                        GH_BOARD, NOW)[0]
        self.assertEqual(row.ordering_date_source, "first_seen")
        self.assertEqual(row.ordering_date, row.first_seen)
        self.assertIsNone(row.published_at)

    def test_a_fallback_is_never_labelled_as_a_publication_date(self):
        """The defeat case: if these two were conflated, Measure A would
        measure the pipeline's own observation time and look excellent."""
        row = normalise([posting(published_at=None, published_field=None)],
                        GH_BOARD, NOW)[0]
        self.assertNotEqual(row.ordering_date_source, "publication")

    def test_first_seen_is_preserved_across_runs(self):
        """Re-dating a posting on every run would reset its age and make
        everything look fresh."""
        earlier = "2026-09-01T00:00:00Z"
        rows = normalise([posting()], GH_BOARD, NOW,
                         seen={"greenhouse:1": earlier})
        self.assertEqual(rows[0].first_seen, earlier)

    def test_lever_rows_flag_that_the_date_meaning_is_unconfirmed(self):
        row = normalise([posting(source="lever", board_id="lever:spreetail",
                                 published_field="createdAt")], LEVER_BOARD, NOW)[0]
        self.assertTrue(row.published_meaning_unconfirmed)

    def test_greenhouse_rows_do_not(self):
        self.assertFalse(normalise([posting()], GH_BOARD, NOW)[0].published_meaning_unconfirmed)


class TestProvenance(unittest.TestCase):
    def test_payload_employer_is_carried_with_its_provenance(self):
        row = normalise([posting()], GH_BOARD, NOW)[0]
        self.assertEqual(row.employer, "Careem")
        self.assertEqual(row.employer_provenance, "payload")

    def test_derived_employer_keeps_its_provenance(self):
        row = normalise([posting(employer="Spreetail", employer_provenance="slug",
                                 source="lever", board_id="lever:spreetail")],
                        LEVER_BOARD, NOW)[0]
        self.assertEqual(row.employer_provenance, "slug")

    def test_unresolved_employer_stays_unresolved(self):
        row = normalise([posting(employer=None, employer_provenance=None)],
                        GH_BOARD, NOW)[0]
        self.assertIsNone(row.employer)
        self.assertIsNone(row.employer_provenance)


class TestTitleNormalisation(unittest.TestCase):
    def test_strips_a_suffix_that_equals_the_location(self):
        self.assertEqual(
            strip_location_suffix("Go-to-Market - Alexandria, VA, USA", "Alexandria, VA, USA"),
            "Go-to-Market")

    def test_leaves_a_hyphenated_title_that_names_no_location(self):
        """The rule is the equality, never the separator. Stripping on the
        separator alone would turn this into 'Engineer'."""
        self.assertEqual(
            strip_location_suffix("Engineer - Platform Team", "Karachi"),
            "Engineer - Platform Team")

    def test_leaves_a_title_whose_suffix_is_a_different_location(self):
        self.assertEqual(
            strip_location_suffix("Go-to-Market - Anaheim, CA, USA", "Remote"),
            "Go-to-Market - Anaheim, CA, USA")

    def test_original_title_is_never_replaced(self):
        """ADR-0027: the display shows what the employer wrote."""
        p = posting(title="Go-to-Market - Anaheim, CA, USA", location="Anaheim, CA, USA")
        row = normalise([p], SPEECHIFY, NOW)[0]
        self.assertEqual(row.title, "Go-to-Market - Anaheim, CA, USA")
        self.assertEqual(row.title_normalised, "Go-to-Market")

    def test_a_board_without_the_normalisation_keeps_the_whole_title(self):
        """ADR-0027: applied only where measured."""
        p = posting(title="Go-to-Market - Anaheim, CA, USA", location="Anaheim, CA, USA")
        row = normalise([p], GH_BOARD, NOW)[0]
        self.assertEqual(row.title_normalised, row.title)

    def test_unimplemented_normaliser_fails_loudly(self):
        board = Board(platform="greenhouse", slug="x", normalisations=("nonexistent",))
        with self.assertRaises(NormaliseError):
            normalise([posting()], board, NOW)


class TestFold(unittest.TestCase):
    def test_separators_become_spaces(self):
        self.assertEqual(fold("AI/ML Engineer"), "ai ml engineer")
        self.assertEqual(fold("AI-Agent Developer"), "ai agent developer")
        self.assertEqual(fold("Full–Stack"), "full stack")

    def test_punctuation_is_deleted_and_space_collapsed(self):
        self.assertEqual(fold("Engineer, Core (Remote).  Sr.:"), "engineer core remote sr")


class TestDedupeKey(unittest.TestCase):
    def test_same_role_in_two_cities_shares_a_key(self):
        a = normalise([posting(external_id="1", title="Go-to-Market - Anaheim, CA, USA",
                               location="Anaheim, CA, USA")], SPEECHIFY, NOW)[0]
        b = normalise([posting(external_id="2", title="Go-to-Market - Dallas, TX, USA",
                               location="Dallas, TX, USA")], SPEECHIFY, NOW)[0]
        self.assertEqual(dedupe_key(a), dedupe_key(b))

    def test_different_roles_do_not(self):
        a = normalise([posting(external_id="1", title="AI Engineer")], GH_BOARD, NOW)[0]
        b = normalise([posting(external_id="2", title="Data Engineer")], GH_BOARD, NOW)[0]
        self.assertNotEqual(dedupe_key(a), dedupe_key(b))

    def test_same_title_different_publication_date_does_not_collapse(self):
        """A reposted role is a new posting, not a duplicate."""
        a = normalise([posting(external_id="1")], GH_BOARD, NOW)[0]
        b = normalise([posting(external_id="2",
                               published_at=datetime(2026, 8, 1, tzinfo=timezone.utc))],
                      GH_BOARD, NOW)[0]
        self.assertNotEqual(dedupe_key(a), dedupe_key(b))

    def test_a_row_with_no_employer_is_scoped_to_its_board(self):
        """ADR-0026: a derived employer with no alias does not participate in
        cross-source deduplication. Two unrelated boards must not merge just
        because both left the employer unresolved."""
        a = normalise([posting(external_id="1", employer=None, employer_provenance=None,
                               board_id="lever:alpha")], GH_BOARD, NOW)[0]
        b = normalise([posting(external_id="2", employer=None, employer_provenance=None,
                               board_id="lever:beta")], GH_BOARD, NOW)[0]
        self.assertNotEqual(dedupe_key(a), dedupe_key(b))

    def test_speechify_collapses_to_eight_groups(self):
        """The brief's number. 1086 postings, 8 real roles. Not 1086, and not
        fewer than 8, which would mean the normalisation over-stripped."""
        with open(os.path.join(CASSETTES, "greenhouse-speechify-titles.json"),
                  encoding="utf-8") as f:
            payload = json.load(f)
        postings = greenhouse.parse(payload, SPEECHIFY).postings
        rows = normalise(postings, SPEECHIFY, NOW)
        self.assertEqual(len(rows), 1086)
        self.assertEqual(len({r.title_normalised for r in rows}), 8)


class TestSerialisation(unittest.TestCase):
    def test_round_trip_is_byte_identical_with_non_ascii(self):
        """One canonical serialisation per file, so a run that changes nothing
        produces a diff containing nothing."""
        row = normalise([posting(title="Ingénieur IA – Montréal (H/F) — データ")],
                        GH_BOARD, NOW)[0]
        first = dumps([row.as_record()])
        second = dumps(loads(first))
        self.assertEqual(first, second)
        self.assertIn("Ingénieur", first)

    def test_round_trip_survives_a_file(self):
        row = normalise([posting(title="Señor Engineer")], GH_BOARD, NOW)[0]
        text = dumps([row.as_record()])
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_rt.json")
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            with open(path, encoding="utf-8") as f:
                back = f.read()
            self.assertEqual(text, back)
            self.assertEqual(dumps(loads(back)), text)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_iso_refuses_a_naive_datetime(self):
        with self.assertRaises(NormaliseError):
            iso(datetime(2026, 1, 1))

    def test_iso_is_utc_with_a_z(self):
        self.assertEqual(iso(datetime(2026, 9, 10, 5, 0, tzinfo=timezone(timedelta(hours=5)))),
                         "2026-09-10T00:00:00Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)
