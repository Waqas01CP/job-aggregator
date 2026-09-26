"""ADR-0030's backfill, and the Confirmation it has to be able to fail.

The gap exists because a run writes a kept row only if its identity is new to
the seen store. Every test here builds a raw layer holding rows the filtered
file never received, which is the situation the tool exists for and which a
run can no longer produce.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.filters import TitleMatcher
from src.normalise import Row
from src.backfill import BackfillError, backfill, gap, load_rows

NOW = "2026-09-18T12:00:00.000000Z"
MATCHER = TitleMatcher()


def read_bytes(path):
    """Closed after reading. A bare open().read() left the handle to the
    garbage collector, which the suite reported as ResourceWarnings."""
    with open(path, "rb") as f:
        return f.read()


def row(identity, title="AI Engineer", source="greenhouse", expires_at=None):
    return Row(identity=identity, source=source, board_id="%s:b" % source,
               external_id=identity.split(":")[-1], title=title,
               title_normalised=title, url="https://x.test/%s" % identity,
               url_provenance="given", first_seen="2026-09-15T00:00:00.000000Z",
               ordering_date="2026-09-15T00:00:00.000000Z",
               ordering_date_source="publication", employer="E",
               employer_provenance="payload", location="Karachi",
               published_at="2026-09-15T00:00:00.000000Z",
               published_field="first_published", expires_at=expires_at)
# Dated three days before NOW: the operator's D14 drops a posting more than a
# week old, and these tests are about the gap, not about age.


class BackfillCase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.paths = {
            "root": self.root,
            "raw_dir": os.path.join(self.root, "fetch-all"),
            "local_raw_dir": os.path.join(self.root, "fetch-all-local"),
            "filtered": os.path.join(self.root, "filtered.json"),
            "local_filtered": os.path.join(self.root, "local", "filtered.json"),
        }
        os.makedirs(self.paths["raw_dir"])
        os.makedirs(self.paths["local_raw_dir"])

    def write_raw(self, rows, source="greenhouse", aggregator=False):
        key = "local_raw_dir" if aggregator else "raw_dir"
        path = os.path.join(self.paths[key], "%s.json" % source)
        storage.write_atomic(path, storage.dumps([r.as_record() for r in rows]))

    def write_filtered(self, rows):
        storage.write_atomic(self.paths["filtered"],
                             storage.dumps([r.as_record() for r in rows]))

    def read(self, key):
        return storage.read_records(self.paths[key])

    def run_gap(self, **kw):
        return gap(self.paths, NOW, MATCHER, **kw)


class TestTheGap(BackfillCase):
    def test_no_gap_when_the_file_already_holds_every_admitted_row(self):
        rows = [row("greenhouse:1"), row("greenhouse:2")]
        self.write_raw(rows)
        self.write_filtered(rows)
        self.assertEqual(self.run_gap(), [])

    def test_the_gap_is_what_the_chain_admits_and_the_file_lacks(self):
        kept, missing = row("greenhouse:1"), row("greenhouse:2")
        self.write_raw([kept, missing])
        self.write_filtered([kept])
        self.assertEqual([r.identity for r in self.run_gap()], ["greenhouse:2"])

    def test_a_row_the_chain_rejects_is_not_in_the_gap(self):
        """The backfill adds what the rules admit, never everything stored."""
        self.write_raw([row("greenhouse:1", title="Accounts Officer")])
        self.write_filtered([])
        self.assertEqual(self.run_gap(), [])

    def test_an_expired_row_is_not_backfilled(self):
        """The chain runs with a clock, so a posting that has since expired is
        not added to a display the operator would then have to reject."""
        self.write_raw([row("greenhouse:1", expires_at="2026-09-10")])
        self.write_filtered([])
        self.assertEqual(self.run_gap(), [])

    def test_a_row_held_only_in_the_local_file_is_not_a_gap(self):
        """ADR-0020 splits the filtered layer, so absence from the public file
        is not absence from the layer."""
        local = row("himalayas:1", source="himalayas")
        self.write_raw([local], source="himalayas", aggregator=True)
        storage.write_atomic(self.paths["local_filtered"],
                             storage.dumps([local.as_record()]))
        self.assertEqual(self.run_gap(), [])


class TestTheAppend(BackfillCase):
    def test_it_appends_the_gap_and_closes_it(self):
        rows = [row("greenhouse:%d" % i) for i in range(1, 6)]
        self.write_raw(rows)
        self.write_filtered(rows[:2])
        result = backfill(self.paths, NOW, MATCHER)
        self.assertEqual(result["written_public"], 3)
        self.assertEqual(len(self.read("filtered")), 5)
        self.assertEqual(self.run_gap(), [])

    def test_a_second_pass_writes_nothing_and_changes_no_byte(self):
        rows = [row("greenhouse:%d" % i) for i in range(1, 4)]
        self.write_raw(rows)
        self.write_filtered([])
        backfill(self.paths, NOW, MATCHER)
        before = read_bytes(self.paths["filtered"])
        result = backfill(self.paths, NOW, MATCHER)
        self.assertEqual(result["written_public"], 0)
        self.assertEqual(read_bytes(self.paths["filtered"]), before)

    def test_rows_already_present_are_never_duplicated(self):
        rows = [row("greenhouse:1"), row("greenhouse:2")]
        self.write_raw(rows)
        self.write_filtered(rows)
        backfill(self.paths, NOW, MATCHER)
        identities = [r["identity"] for r in self.read("filtered")]
        self.assertEqual(sorted(identities), ["greenhouse:1", "greenhouse:2"])

    def test_dry_run_writes_nothing(self):
        self.write_raw([row("greenhouse:1")])
        self.write_filtered([])
        before = read_bytes(self.paths["filtered"])
        result = backfill(self.paths, NOW, MATCHER, dry_run=True)
        self.assertEqual(result["missing"], 1)
        self.assertEqual(result["written_public"], 0)
        self.assertEqual(read_bytes(self.paths["filtered"]), before)


class TestADR0020IsEnforced(BackfillCase):
    def test_an_aggregator_row_goes_local_and_never_public(self):
        """The case the guard exists for. If this ever writes the public file,
        a run would offer it to the branch and ADR-0020 would be bypassed by a
        tool rather than by the pipeline."""
        self.write_raw([row("greenhouse:1")])
        self.write_raw([row("himalayas:1", source="himalayas")],
                       source="himalayas", aggregator=True)
        self.write_filtered([])
        result = backfill(self.paths, NOW, MATCHER)
        self.assertEqual(result["written_public"], 1)
        self.assertEqual(result["written_local"], 1)
        public = [r["source"] for r in self.read("filtered")]
        self.assertEqual(public, ["greenhouse"])
        self.assertNotIn("himalayas", public)
        local = [r["source"] for r in self.read("local_filtered")]
        self.assertEqual(local, ["himalayas"])

    def test_the_split_is_by_source_not_by_which_file_it_came_from(self):
        """An aggregator row sitting in the committed raw directory, which a
        routing bug could produce, must still be routed by its own source."""
        self.write_raw([row("himalayas:1", source="himalayas")])
        self.write_filtered([])
        backfill(self.paths, NOW, MATCHER)
        self.assertEqual(self.read("filtered"), [],
                         "an aggregator row reached the public file")
        self.assertEqual(len(self.read("local_filtered")), 1)


class TestTheConfirmationCanFail(BackfillCase):
    def test_withholding_one_identity_leaves_exactly_one_row_absent(self):
        """ADR-0030's Confirmation, given the case built to defeat it. The
        backfill cannot see the withheld row, so it reports itself complete;
        the check, run without the same blindfold, finds the one it missed."""
        rows = [row("greenhouse:%d" % i) for i in range(1, 5)]
        self.write_raw(rows)
        self.write_filtered([])
        result = backfill(self.paths, NOW, MATCHER, withhold=["greenhouse:3"])
        self.assertEqual(result["written_public"], 3)
        self.assertEqual(self.run_gap(withhold=["greenhouse:3"]), [],
                         "blindfolded, the pass looks complete")
        remaining = self.run_gap()
        self.assertEqual([r.identity for r in remaining], ["greenhouse:3"],
                         "unblindfolded, the check must find the missed row")


class TestLoading(BackfillCase):
    def test_a_record_this_code_cannot_read_is_named(self):
        """A raw file written by a future row shape must fail loudly rather
        than being silently skipped, which would look like a closed gap."""
        path = os.path.join(self.paths["raw_dir"], "greenhouse.json")
        storage.write_atomic(path, json.dumps([{"identity": "x", "nonsense": 1}]))
        with self.assertRaises(BackfillError) as ctx:
            load_rows(self.paths)
        self.assertIn("greenhouse.json", str(ctx.exception))

    def test_both_raw_directories_are_read(self):
        self.write_raw([row("greenhouse:1")])
        self.write_raw([row("himalayas:1", source="himalayas")],
                       source="himalayas", aggregator=True)
        self.assertEqual(len(load_rows(self.paths)), 2)


if __name__ == "__main__":
    unittest.main()
