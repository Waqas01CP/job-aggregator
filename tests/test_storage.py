"""Writers and the orphan data branch, tested from the brief.

The brief's named checks live here: two runs with no new postings producing a
diff containing nothing, a serialisation round-trip, and TEST_MODE writing to
alternate files while production data is untouched.

The data-branch tests build a throwaway repository in a temp directory, so
nothing here can touch the real one.
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.adapters.base import Posting
from src.config import Board
from src.normalise import dumps, normalise
from src.storage import (SeenStore, StorageError, append_delta, layout,
                         raw_path, read_records, write_atomic)

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
BOARD = Board(platform="greenhouse", slug="careem")


def rows(n=2, start=0):
    postings = [Posting(external_id=str(i), title="AI Engineer %d" % i,
                        url="https://x.test/%d" % i,
                        published_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
                        published_field="first_published", published_raw="x",
                        source="greenhouse", board_id="greenhouse:careem",
                        employer="Careem", employer_provenance="payload",
                        location="Karachi")
                for i in range(start, start + n)]
    return normalise(postings, BOARD, NOW)


class TestAppendDelta(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "greenhouse.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_first_write_appends_everything(self):
        n = append_delta(self.path, [r.as_record() for r in rows(3)])
        self.assertEqual(n, 3)
        self.assertEqual(len(read_records(self.path)), 3)

    def test_a_second_run_with_no_new_postings_writes_nothing(self):
        """The brief's check: two runs with no new postings produce a diff
        containing nothing. Byte-identical is the strongest form of that."""
        records = [r.as_record() for r in rows(3)]
        append_delta(self.path, records)
        before = read_text(self.path)
        mtime = os.path.getmtime(self.path)

        appended = append_delta(self.path, records)
        after = read_text(self.path)

        self.assertEqual(appended, 0)
        self.assertEqual(before, after)
        self.assertEqual(mtime, os.path.getmtime(self.path),
                         "the file was rewritten when nothing changed")

    def test_only_the_new_records_are_appended(self):
        append_delta(self.path, [r.as_record() for r in rows(2)])
        n = append_delta(self.path, [r.as_record() for r in rows(3)])
        self.assertEqual(n, 1)
        self.assertEqual(len(read_records(self.path)), 3)

    def test_a_batch_missing_earlier_records_does_not_lose_them(self):
        """The case that separates appending from snapshotting. A board that
        drops an old posting sends a batch without it; a writer that wrote the
        batch instead of appending to the file would delete history, and the
        record counts would still look plausible on the run that did it."""
        append_delta(self.path, [r.as_record() for r in rows(2, start=0)])
        append_delta(self.path, [r.as_record() for r in rows(1, start=5)])
        stored = read_records(self.path)
        self.assertEqual(len(stored), 3)
        self.assertEqual([r["identity"] for r in stored],
                         ["greenhouse:0", "greenhouse:1", "greenhouse:5"],
                         "earlier records must survive a batch that omits them")

    def test_existing_records_are_never_rewritten(self):
        """ADR-0003 appends and never rewrites, so history stays readable."""
        first = [r.as_record() for r in rows(1)]
        append_delta(self.path, first)
        mutated = [dict(first[0], title="Changed Title")]
        append_delta(self.path, mutated)
        stored = read_records(self.path)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["title"], first[0]["title"])

    def test_a_corrupt_file_is_refused_rather_than_overwritten(self):
        write_atomic(self.path, '{"not": "a list"}\n')
        with self.assertRaises(StorageError):
            append_delta(self.path, [r.as_record() for r in rows(1)])


class TestAtomicWrite(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_round_trip_is_byte_identical_with_non_ascii(self):
        path = os.path.join(self.dir, "x.json")
        text = dumps([{"title": "Ingénieur IA — データ", "identity": "g:1"}])
        write_atomic(path, text)
        self.assertEqual(read_text(path), text)
        self.assertEqual(dumps(read_records(path)), text)

    def test_a_failed_write_leaves_the_previous_file_intact(self):
        """A run killed mid-write must not truncate the store."""
        path = os.path.join(self.dir, "x.json")
        write_atomic(path, dumps([{"identity": "a"}]))
        before = read_text(path)

        class Boom(Exception):
            pass

        real = os.replace
        def exploding(src, dst):
            raise Boom("interrupted")
        os.replace = exploding
        try:
            with self.assertRaises(Boom):
                write_atomic(path, dumps([{"identity": "b"}]))
        finally:
            os.replace = real
        self.assertEqual(read_text(path), before)

    def test_no_temp_files_are_left_behind(self):
        path = os.path.join(self.dir, "x.json")
        write_atomic(path, dumps([{"identity": "a"}]))
        self.assertEqual([f for f in os.listdir(self.dir) if f.endswith(".tmp")], [])


class TestTestMode(unittest.TestCase):
    def test_test_mode_writes_to_alternate_paths(self):
        """The brief: a TEST_MODE run leaves production data untouched."""
        prod, test = layout(False), layout(True)
        for key in prod:
            self.assertNotEqual(prod[key], test[key], key)
        self.assertEqual(raw_path("greenhouse", test_mode=False),
                         "fetch-all/greenhouse.json")
        self.assertEqual(raw_path("greenhouse", test_mode=True),
                         "test-fetch-all/greenhouse.json")

    def test_one_file_per_source(self):
        """ADR-0020: a row's provenance is its filename."""
        self.assertEqual(raw_path("lever"), "fetch-all/lever.json")
        self.assertNotEqual(raw_path("lever"), raw_path("greenhouse"))


class TestSeenStore(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "seen.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_first_seen_survives_a_second_observation(self):
        store = SeenStore()
        row = rows(1)[0]
        store.record(row)
        original = store.entries[row.identity]["first_seen"]

        later = rows(1)[0]
        later.first_seen = "2027-01-01T00:00:00Z"
        store.record(later)
        self.assertEqual(store.entries[row.identity]["first_seen"], original)

    def test_round_trips_through_a_file_in_stable_order(self):
        store = SeenStore()
        for row in rows(3):
            store.record(row)
        store.save(self.path)
        first = read_text(self.path)

        reloaded = SeenStore.load(self.path)
        reloaded.save(self.path)
        self.assertEqual(read_text(self.path), first)
        self.assertEqual(reloaded.identities, store.identities)

    def test_entries_are_saved_in_sorted_order_whatever_the_insert_order(self):
        """One canonical serialisation per file. Insertion order would make
        the seen store diff on every run for no reason."""
        store = SeenStore()
        for row in reversed(rows(4)):
            store.record(row)
        store.save(self.path)
        keys = list(json.loads(read_text(self.path)).keys())
        self.assertEqual(keys, sorted(keys))

    def test_missing_file_loads_empty(self):
        self.assertEqual(SeenStore.load(os.path.join(self.dir, "nope.json")).identities,
                         set())


class TestDataBranch(unittest.TestCase):
    """Built against a throwaway repository, never the real one."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.real_root = storage.REPO_ROOT
        storage.REPO_ROOT = self.dir
        run = lambda *a: subprocess.run(list(a), cwd=self.dir, capture_output=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@test")
        run("git", "config", "user.name", "t")
        run("git", "config", "commit.gpgsign", "false")
        write_text(os.path.join(self.dir, "README.md"), "main\n")
        run("git", "add", "README.md")
        run("git", "commit", "-q", "-m", "main")

    def tearDown(self):
        storage.REPO_ROOT = self.real_root
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_commit_creates_the_branch_without_touching_the_working_tree(self):
        before = sorted(os.listdir(self.dir))
        sha = storage.commit_files({"fetch-all/greenhouse.json": dumps([{"identity": "a"}])},
                                   "run", branch="data")
        self.assertTrue(sha)
        self.assertEqual(sorted(os.listdir(self.dir)), before,
                         "the working tree gained or lost a file")

    def test_the_data_branch_is_orphan(self):
        """No shared history with main, so cloning main never drags the data."""
        storage.commit_files({"fetch-all/greenhouse.json": "[]\n"}, "run", branch="data")
        parents = subprocess.run(["git", "rev-list", "--parents", "-n", "1", "data"],
                                 cwd=self.dir, capture_output=True, text=True).stdout.split()
        self.assertEqual(len(parents), 1, "the first data commit has a parent")

    def test_a_second_commit_with_no_change_writes_nothing(self):
        files = {"fetch-all/greenhouse.json": dumps([{"identity": "a"}])}
        first = storage.commit_files(files, "run 1", branch="data")
        second = storage.commit_files(files, "run 2", branch="data")
        self.assertTrue(first)
        self.assertIsNone(second, "an empty commit was created")

    def test_content_is_readable_back_from_the_branch(self):
        text = dumps([{"identity": "a", "title": "Ingénieur"}])
        storage.commit_files({"fetch-all/greenhouse.json": text}, "run", branch="data")
        self.assertEqual(storage.read_branch_file("fetch-all/greenhouse.json", "data"), text)

    def test_the_uncommitted_working_tree_is_left_alone(self):
        """A run must be able to commit data while the operator has work in
        progress on main."""
        scratch = os.path.join(self.dir, "wip.txt")
        write_text(scratch, "work in progress\n")
        storage.commit_files({"fetch-all/greenhouse.json": "[]\n"}, "run", branch="data")
        self.assertTrue(os.path.exists(scratch))
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.dir,
                                capture_output=True, text=True).stdout
        self.assertIn("wip.txt", status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
