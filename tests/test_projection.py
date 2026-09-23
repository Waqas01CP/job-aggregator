"""The projection, tested from ADR-0035, ADR-0037, ADR-0040, ADR-0043, ADR-0046
and Brief 6.

Everything here runs in a temporary directory with a fake Airtable client.
No test reaches a live base: the client below records what it is given and
sends nothing.
"""

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import projection, storage
from src.airtable import PIPELINE_FIELDS
from src.filters import TitleMatcher
from src.normalise import Row, dumps

MATCHER = TitleMatcher()
NOW = "2026-09-23T12:00:00.000000Z"


class FakeClient:
    """Stands in for AirtableClient. Records every upsert and sends nothing."""

    def __init__(self):
        self.sent = []
        self.rows_sent = 0

    def upsert(self, records):
        self.sent.extend(records)
        self.rows_sent += len(records)
        return {"created": [], "updated": []}


def make_row(i, title="AI Engineer", employer="Acme", location="Lahore",
             published="2026-09-20T10:00:00Z", source="greenhouse", title_normalised=None):
    return Row(identity="%s:%d" % (source, i), source=source,
               board_id="%s:acme" % source, external_id=str(i), title=title,
               title_normalised=title_normalised or title,
               url="https://example.test/%d" % i, url_provenance="payload",
               first_seen="2026-09-21T10:00:00.123456Z", ordering_date=published,
               ordering_date_source="publication", employer=employer, location=location,
               published_at=published, published_field="first_published")


class Harness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.paths = storage.layout(False)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def write_filtered(self, rows, local=()):
        storage.write_atomic(self.paths["filtered"], dumps([r.as_record() for r in rows]))
        if local:
            storage.write_atomic(self.paths["local_filtered"],
                                 dumps([r.as_record() for r in local]))

    def write_store(self, name, identities):
        storage.write_atomic("%s/%s" % (self.paths["outcomes_dir"], name),
                             dumps([{"identity": i} for i in identities]))

    def project(self, private=()):
        client, stages = FakeClient(), {}
        projection.project(self.paths, NOW, MATCHER, client, list(private), stages)
        return client, stages


class TestStages(Harness):
    def test_each_stage_is_counted(self):
        """The display, the chain and the store differ in count by design, so
        every stage is reported and a difference can be traced."""
        rows = [make_row(1, location="Lahore"), make_row(2, location="Karachi"),
                make_row(3, title="Account Executive"), make_row(4, title="Data Engineer")]
        self.write_filtered(rows)
        client, stages = self.project()
        self.assertEqual(stages["rows_read"], 4)
        self.assertEqual(stages["rows_admitted"], 3)
        self.assertEqual(stages["groups"], 2)
        self.assertEqual(stages["groups_skipped_by_store"], 0)
        self.assertEqual(stages["rows_to_send"], 2)
        self.assertEqual(stages["rows_sent"], 2)

    def test_the_local_aggregator_copy_is_read_too(self):
        self.write_filtered([make_row(1)],
                            local=[make_row(7, source="himalayas", employer="Globex")])
        client, stages = self.project()
        self.assertEqual(stages["rows_read"], 2)
        self.assertIn("himalayas:7", {r["Identity"] for r in client.sent})

    def test_the_current_chain_filters_the_projection_not_the_store(self):
        """ADR-0040. A senior row kept under older rules stays in the file
        and stays out of the display."""
        self.write_filtered([make_row(1), make_row(2, title="Senior AI Engineer")])
        client, _ = self.project()
        self.assertEqual([r["Identity"] for r in client.sent], ["greenhouse:1"])

    def test_the_filtered_layer_is_byte_identical_afterwards(self):
        """ADR-0040's second check: the projection is a reader."""
        self.write_filtered([make_row(1), make_row(2, title="Senior AI Engineer")],
                            local=[make_row(7, source="himalayas")])
        def digests():
            out = {}
            for key in ("filtered", "local_filtered"):
                with open(self.paths[key], "rb") as f:
                    out[key] = hashlib.sha256(f.read()).hexdigest()
            return out

        before = digests()
        self.project()
        self.assertEqual(digests(), before)


class TestTheRowSent(Harness):
    def test_a_group_is_one_row_carrying_every_location_and_the_representatives_identity(self):
        """ADR-0037's Confirmation: every member's location in the displayed
        row. The representative is the earliest published, then the lowest
        identity."""
        self.write_filtered([make_row(5, location="Lahore"), make_row(3, location="Karachi"),
                             make_row(4, location="Karachi")])
        client, _ = self.project()
        self.assertEqual(len(client.sent), 1)
        record = client.sent[0]
        self.assertEqual(record["Identity"], "greenhouse:3")
        self.assertEqual(record["Location"].split("\n"), ["Karachi", "Lahore"])

    def test_the_fields_are_exactly_the_ten(self):
        self.write_filtered([make_row(1)])
        client, _ = self.project()
        self.assertEqual(list(client.sent[0]), list(PIPELINE_FIELDS))

    def test_matched_term_comes_from_the_title_the_chain_matched(self):
        """The chain's title rule matches title_normalised. The raw title of
        this row, with its city suffix, names a different term, and the
        display must show the term that admitted the row."""
        raw, normalised = "Data Engineer - AI Engineer Plaza, Karachi", "Data Engineer"
        self.assertNotEqual(MATCHER.match(raw), MATCHER.match(normalised),
                            "the case no longer tells the two inputs apart")
        self.write_filtered([make_row(1, title=raw, title_normalised=normalised)])
        client, _ = self.project()
        self.assertEqual(client.sent[0]["Matched term"], MATCHER.match(normalised))

    def test_title_is_the_normalised_one_and_the_raw_one_stays_in_the_store(self):
        """The operator's choice, 2026-09-23: the display reads the normalised
        title, because the group's Location already names every city. The
        raw title must never be lost, so the stored record still carries it."""
        raw, normalised = "Software Engineer, Platform - Lahore, Pakistan", \
            "Software Engineer, Platform"
        self.write_filtered([make_row(1, title=raw, title_normalised=normalised,
                                      location="Lahore, Pakistan")])
        client, _ = self.project()
        self.assertEqual(client.sent[0]["Title"], normalised)
        stored = storage.read_records(self.paths["filtered"])[0]
        self.assertEqual(stored["title"], raw)
        self.assertEqual(stored["title_normalised"], normalised)

    def test_times_go_to_the_millisecond_in_utc(self):
        self.assertEqual(projection.airtable_datetime("2026-09-17T14:52:57.903143Z"),
                         "2026-09-17T14:52:57.903Z")
        self.assertEqual(projection.airtable_datetime("2026-09-17T19:52:57+05:00"),
                         "2026-09-17T14:52:57.000Z")
        self.assertIsNone(projection.airtable_datetime(None))


class TestTheSkip(Harness):
    def test_both_ways_against_a_hand_written_store(self):
        """ADR-0046's Confirmation, offline: an identity in a store is not
        projected; removed from the store, it is. Only the second half proves
        the skip reads the store rather than failing to project."""
        self.write_filtered([make_row(1), make_row(2, title="Data Engineer")])
        self.write_store("accepted.json", ["greenhouse:1"])
        client, stages = self.project()
        self.assertEqual([r["Identity"] for r in client.sent], ["greenhouse:2"])
        self.assertEqual(stages["groups_skipped_by_store"], 1)

        self.write_store("accepted.json", [])
        client, stages = self.project()
        self.assertEqual(sorted(r["Identity"] for r in client.sent),
                         ["greenhouse:1", "greenhouse:2"])

    def test_any_member_in_a_store_skips_the_whole_group(self):
        """Ruling 3, 2026-09-23. The case built to defeat a representative-only
        skip: the stored identity is a member that is not the representative.
        Testing the representative alone would project the group again."""
        self.write_filtered([make_row(3, location="Karachi"), make_row(4, location="Lahore"),
                             make_row(5, location="Quetta")])
        self.write_store("rejected_not_a_fit.json", ["greenhouse:5"])
        client, stages = self.project()
        self.assertEqual(client.sent, [])
        self.assertEqual(stages["groups_skipped_by_store"], 1)

    def test_each_classification_store_is_read(self):
        for name in projection.CLASSIFICATION_STORES:
            with self.subTest(store=name):
                shutil.rmtree(self.paths["outcomes_dir"], ignore_errors=True)
                self.write_filtered([make_row(1)])
                self.write_store(name, ["greenhouse:1"])
                client, _ = self.project()
                self.assertEqual(client.sent, [])

    def test_the_fourth_store_is_not_read(self):
        """ADR-0043's 2026-09-23 row: removed_unreviewed.json exists so a row
        that fell out on a narrowed rule can return. The skip must not read it."""
        self.write_filtered([make_row(1)])
        self.write_store(projection.REMOVED_UNREVIEWED_STORE, ["greenhouse:1"])
        client, _ = self.project()
        self.assertEqual([r["Identity"] for r in client.sent], ["greenhouse:1"])

    def test_the_private_stores_are_read(self):
        """ADR-0047: aggregator outcomes live in the private repository."""
        self.write_filtered([], local=[make_row(7, source="himalayas")])
        private = [("private outcomes/accepted.json", dumps([{"identity": "himalayas:7"}]))]
        client, _ = self.project(private)
        self.assertEqual(client.sent, [])

    def test_absent_stores_read_as_empty(self):
        """No sweep has written a store yet. Absent from the branch or from a
        reachable private repository counts as empty."""
        self.write_filtered([make_row(1)])
        client, stages = self.project([("private outcomes/accepted.json", None)])
        self.assertEqual(len(client.sent), 1)
        self.assertEqual(stages["stored_identities"], 0)

    def test_an_unreadable_store_stops_the_projection(self):
        """Skipping nothing because a store was unreadable would re-surface
        everything the operator retired."""
        self.write_filtered([make_row(1)])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps({"not": "a list"}))
        with self.assertRaises(projection.ProjectionError):
            self.project()
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"no_identity": True}]))
        with self.assertRaises(projection.ProjectionError):
            self.project()


if __name__ == "__main__":
    unittest.main(verbosity=2)
