"""The re-read of stored rows' derived facts (src/facts.py): ADR-0040's and
ADR-0058's Changes, the operator's yes of 2026-10-16.

Every posting here is written for the test, shaped like the measured case it
stands for, never copied: ADR-0011 keeps description text out of this
repository."""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import facts, storage
from src.adapters import lever
from src.backfill import gap
from src.config import Board
from src.filters import TitleMatcher, apply_chain
from src.normalise import Row, dumps
from src.run import ADAPTERS, files_to_commit, reread_facts

MATCHER = TitleMatcher()
SPREETAIL = Board(platform="lever", slug="spreetail", employer_alias="Spreetail")
FIRST_SEEN = "2026-09-17T14:52:57.903143Z"


def lever_posting(**extra):
    posting = {"id": "f9f0", "text": "RPA & AI Automation Engineer",
               "hostedUrl": "https://jobs.lever.co/spreetail/f9f0",
               "createdAt": int(datetime(2026, 9, 16, tzinfo=timezone.utc).timestamp() * 1000),
               "categories": {"location": "Manila"}}
    posting.update(extra)
    return posting


def saved(posting, board=SPREETAIL):
    """One full-branch file holding one saved posting, as D11 writes it."""
    return dumps([{"identity": "lever:%s" % posting["id"], "source": "lever",
                   "board_id": board.board_id, "fetched_at": FIRST_SEEN, "posting": posting}])


def stored_row(posting=None, board=SPREETAIL, **kw):
    """The row as the run stored it at first sight, before the source's own
    country was read: no places."""
    posting = posting or lever_posting()
    parsed = lever.parse([posting], board).postings
    from src.normalise import normalise
    [row] = normalise(parsed, board, datetime(2026, 9, 17, 14, 52, tzinfo=timezone.utc),
                      seen={"lever:%s" % posting["id"]: FIRST_SEEN})
    from dataclasses import replace
    return replace(row, **dict({"places": None, "workplace": None}, **kw))


class Harness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.paths = storage.layout(False)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)


class TestTheFingerprint(Harness):
    def write(self, name, body):
        path = os.path.join(self.dir, "root", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(body)

    def test_it_moves_with_the_files_that_derive_the_facts_and_nothing_else(self):
        """A change to the reader re-reads; a change elsewhere does not; a
        checkout with other line endings reads the same. Mutation: "line
        endings change the fingerprint"."""
        root = os.path.join(self.dir, "root")
        sources = ("src/description.py", "src/adapters/*.py")
        self.write("src/description.py", b"A = 1\n")
        self.write("src/adapters/lever.py", b"B = 2\n")
        self.write("src/other.py", b"C = 3\n")
        first = facts.fingerprint(root, sources)
        self.write("src/other.py", b"C = 4\n")
        self.assertEqual(facts.fingerprint(root, sources), first)
        self.write("src/description.py", b"A = 1\r\n")
        self.assertEqual(facts.fingerprint(root, sources), first)
        self.write("src/adapters/lever.py", b"B = 3\n")
        self.assertNotEqual(facts.fingerprint(root, sources), first)

    def test_the_shipped_sources_are_the_reader_the_adapters_and_the_eligibility(self):
        self.assertEqual(facts.SOURCES, ("src/description.py", "src/normalise.py",
                                         "src/adapters/*.py", "config/eligibility.json"))


class TestTheReread(Harness):
    def test_spreetails_row_reread_carries_its_country_and_drops(self):
        """The resume chat's C2: first seen 2026-09-17 with only "Manila",
        which names no configured place, so it stayed; the source's own
        country, read since 2026-10-02, closes it. Read again from its saved
        posting, today's rules drop it on location. Mutation: "the loaders
        judge the stored facts"."""
        posting = lever_posting(country="PH", workplaceType="remote")
        records, counts = facts.reread([saved(posting)], [SPREETAIL],
                                       {"lever:f9f0": FIRST_SEEN}, ADAPTERS)
        self.assertEqual(counts["read"], 1)
        self.assertEqual(list(records["lever:f9f0"]["places"]), ["PH"])
        row = stored_row()
        kept, _ = apply_chain([row], row.first_seen, matcher=MATCHER)
        self.assertTrue(kept, "the case no longer stands for the stored row")
        [reread] = facts.apply([row], records)
        kept, drops = apply_chain([reread], reread.first_seen, matcher=MATCHER)
        self.assertEqual(kept, [])
        self.assertEqual(drops[0]["rule"], "location")
        self.assertIn("PH", drops[0]["reason"])

    def test_whether_a_posting_carried_a_description_is_a_derived_fact(self):
        """Brief 13: set at first sight and carried by the re-read, so a
        stored row learns it too. Mutations: "a posting with no description
        is not flagged", "the re-read leaves out whether there was a
        description"."""
        described = lever_posting(description="<p>Build agents with our team.</p>")
        self.assertIs(stored_row().described, False)
        self.assertIs(stored_row(described).described, True)
        before = stored_row(described=None)
        records, _ = facts.reread([saved(lever_posting())], [SPREETAIL],
                                  {"lever:f9f0": FIRST_SEEN}, ADAPTERS)
        self.assertIs(records["lever:f9f0"]["described"], False)
        [row] = facts.apply([before], records)
        self.assertIs(row.described, False)
        records, _ = facts.reread([saved(described)], [SPREETAIL],
                                  {"lever:f9f0": FIRST_SEEN}, ADAPTERS)
        self.assertIs(records["lever:f9f0"]["described"], True)

    def test_a_posting_whose_board_is_gone_or_unparseable_keeps_its_stored_facts(self):
        gone = Board(platform="lever", slug="closed-board")
        records, counts = facts.reread([saved(lever_posting(), board=gone),
                                        saved({"id": "x"})], [SPREETAIL], {}, ADAPTERS)
        self.assertEqual(records, {})
        self.assertEqual((counts["unknown_board"], counts["unparseable"]), (1, 1))
        row = stored_row()
        self.assertEqual(facts.apply([row], records), [row])

    def test_an_aggregators_facts_never_reach_the_public_overlay(self):
        """ADR-0020, as for every layer. Mutation: "the overlay is not split
        by source class"."""
        records = {"lever:1": {"identity": "lever:1", "source": "lever", "places": ["PH"]},
                   "himalayas:x": {"identity": "himalayas:x", "source": "himalayas",
                                   "stated_levels": ["Senior"]}}
        facts.write(self.paths, records, "fp1")
        with open(self.paths["facts"], encoding="utf-8") as f:
            public = f.read()
        self.assertNotIn("himalayas", public)
        loaded, fps = facts.load(self.paths)
        self.assertEqual((set(loaded), fps), ({"lever:1", "himalayas:x"}, {"fp1"}))

    def test_the_commit_refuses_an_aggregators_facts_on_the_public_branch(self):
        """The last gate reads the overlay's records by source, as it reads
        every committed file's. Mutation: "the gate cannot read the
        overlay"."""
        storage.write_atomic(self.paths["facts"], dumps({"fingerprint": "fp1", "records": [
            {"identity": "himalayas:x", "source": "himalayas"}]}))
        with self.assertRaises(storage.StorageError):
            files_to_commit({"totals": {"written_raw": {}}}, self.paths,
                            os.path.join(self.dir, "none.json"), False)


class TestTheLoadersReadTheOverlay(Harness):
    def test_the_projection_and_the_sweep_judge_spreetail_on_its_reread_facts(self):
        """Stored in the filtered layer as it was first seen, Spreetail's row
        is planned for the display on its stored facts; with the overlay, the
        projection plans nothing for it and the sweep names the rule that now
        drops it. Mutations: "the projection judges the stored facts", "the
        sweep judges the stored facts"."""
        from src import projection
        from src.config import SweepConfig
        from src.sweep import Sweep
        row = stored_row()
        storage.write_atomic(self.paths["filtered"], dumps([row.as_record()]))
        now = "2026-10-16T12:00:00.000000Z"
        planned = projection.plan(projection.load_rows(self.paths), now, MATCHER, set())
        self.assertEqual(len(planned), 1, "the case no longer stands for the stored row")
        facts.write(self.paths, {row.identity: {"identity": row.identity, "source": "lever",
                                                "places": ["PH"], "workplace": "remote"}}, "fp1")
        self.assertEqual(projection.plan(projection.load_rows(self.paths), now, MATCHER, set()), [])
        config = SweepConfig(closed_after_polled_runs=12, retire_after_days=15, run_log_window=60,
                             unreviewed_after_days=30, clearing_dry_run_valid_hours=48,
                             budget_warning_share=0.6, budget_warning_before_day=15)
        sweep = Sweep(None, self.paths, datetime(2026, 10, 16, 12, tzinfo=timezone.utc), MATCHER,
                      None, config, True)
        self.assertEqual(sweep.dropped_by.get(row.identity), "location")


class TestTheBackfillJudgesTheRereadFacts(Harness):
    def test_a_row_its_reread_description_drops_is_not_added(self):
        """The Senior change's case: a stored row with no years read at first
        sight passes on its stored facts, and its saved description asks
        five. With the overlay the backfill adds nothing; without it, the row.
        Mutation: "the backfill judges the stored facts"."""
        now = "2026-10-16T12:00:00Z"
        row = Row(identity="greenhouse:9", source="greenhouse", board_id="greenhouse:acme",
                  external_id="9", title="AI Engineer", title_normalised="AI Engineer",
                  url="https://x.test/9", url_provenance="payload",
                  first_seen="2026-10-10T04:00:00Z", ordering_date="2026-10-09T10:00:00Z",
                  ordering_date_source="publication", employer="Acme", location="Lahore",
                  published_at="2026-10-09T10:00:00Z", published_field="first_published")
        storage.write_atomic(storage.raw_path("greenhouse", False, "ats"), dumps([row.as_record()]))
        self.assertEqual([r.identity for r in gap(self.paths, now, MATCHER)], ["greenhouse:9"])
        facts.write(self.paths, {"greenhouse:9": {"identity": "greenhouse:9",
                                                  "source": "greenhouse",
                                                  "stated_experience": [5]}}, "fp1")
        self.assertEqual(gap(self.paths, now, MATCHER), [])


class FakeStore:
    def __init__(self, texts):
        self.texts = texts
        self.reads = 0

    def read_full(self):
        self.reads += 1
        return self.texts


class TestTheRunRereadsOnlyAtAChange(Harness):
    def test_a_changed_fingerprint_rereads_and_the_same_one_does_not(self):
        """Mutation: "the run never re-reads"."""
        store = FakeStore([saved(lever_posting(country="PH"))])
        first = reread_facts(store, self.paths, [SPREETAIL])
        self.assertEqual((first["reread"], first["read"], store.reads), (True, 1, 1))
        _, fps = facts.load(self.paths)
        self.assertEqual(fps, {facts.fingerprint()})
        again = reread_facts(store, self.paths, [SPREETAIL])
        self.assertEqual((again["reread"], store.reads), (False, 1))

    def test_a_failed_read_is_recorded_and_the_old_overlay_stands(self):
        class Broken:
            def read_full(self):
                raise OSError("the full branch could not be fetched")
        facts.write(self.paths, {"lever:1": {"identity": "lever:1", "source": "lever"}}, "old")
        block = reread_facts(Broken(), self.paths, [SPREETAIL])
        self.assertIn("could not be fetched", block["failure"])
        self.assertEqual(facts.load(self.paths)[1], {"old"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
