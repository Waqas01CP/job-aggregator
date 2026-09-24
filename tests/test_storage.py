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
from src.storage import (SeenStore, StorageError, append_delta, branch_path,
                         layout, raw_path, read_records, write_atomic)

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
                         "data/fetch-all/greenhouse.json")
        self.assertEqual(raw_path("greenhouse", test_mode=True),
                         "data/test/fetch-all/greenhouse.json")

    def test_one_file_per_source(self):
        """ADR-0020: a row's provenance is its filename."""
        self.assertEqual(raw_path("lever"), "data/fetch-all/lever.json")
        self.assertNotEqual(raw_path("lever"), raw_path("greenhouse"))

    def test_working_files_live_under_one_ignored_directory(self):
        """Not scattered across the repository root, so `git status` shows the
        operator's work rather than the pipeline's."""
        for key, path in layout(False).items():
            self.assertTrue(path == "data" or path.startswith("data/"), path)
        for key, path in layout(True).items():
            self.assertTrue(path.startswith("data/test"), path)

    def test_the_branch_layout_is_unchanged_by_the_local_tidying(self):
        """ADR-0020 fixes the paths inside the data branch. Moving the working
        copies into data/ must not move them on the branch, or every historical
        path breaks."""
        self.assertEqual(branch_path(raw_path("greenhouse")), "fetch-all/greenhouse.json")
        self.assertEqual(branch_path(layout()["filtered"]), "filtered.json")
        self.assertEqual(branch_path(layout()["seen"]), "seen.json")
        self.assertEqual(
            branch_path(raw_path("greenhouse", test_mode=True), test_mode=True),
            "fetch-all/greenhouse.json")


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

    def test_the_commit_lands_in_the_repository_it_was_pointed_at(self):
        """Asserted on where the ref landed, not on the returned sha. The
        `_git(cwd=REPO_ROOT)` default once sent this commit to the real
        repository while every sha-based assertion passed."""
        sha = storage.commit_files({"seen.json": "{}\n"}, "run", branch="data")
        here = subprocess.run(["git", "rev-parse", "data"], cwd=self.dir,
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(here, sha)

    def test_text_reaches_the_branch_as_the_exact_bytes_written_locally(self):
        """The blob must be the UTF-8 bytes of the text with LF endings,
        whatever the host. On Windows the text-mode writer raised for the
        second title, and stored every blob in cp1252 with CRLF endings while
        reading it back unchanged, so the read-back assertion alone could not
        fail there. On a Linux host this test cannot fail for either reason;
        the next one can, anywhere."""
        text = dumps([{"identity": "a", "title": "Ingénieur"},
                      {"identity": "b", "title": "データ — AI"}])
        storage.commit_files({"filtered.json": text}, "run", branch="data")
        blob = subprocess.run(["git", "cat-file", "blob", "data:filtered.json"],
                              cwd=self.dir, capture_output=True).stdout
        self.assertEqual(blob, text.encode("utf-8"))
        self.assertEqual(storage.read_branch_file("filtered.json", "data"), text)

    def test_no_git_call_runs_in_text_mode(self):
        """The host-independent form of the check above. Text mode is where
        both the locale's encoding and the newline translation come from, so
        content must cross the git boundary as bytes in both directions."""
        calls = []
        real = subprocess.run

        def spy(*args, **kwargs):
            calls.append((args[0], kwargs))
            return real(*args, **kwargs)

        cwd = os.getcwd()
        os.chdir(self.dir)
        storage.subprocess.run = spy
        try:
            storage.commit_files({"seen.json": "{}\n"}, "run", branch="data")
            storage.read_branch_file("seen.json", "data")
            storage.restore_from_branch()
        finally:
            storage.subprocess.run = real
            os.chdir(cwd)
        self.assertIn("hash-object", [c[0][1] for c in calls])
        self.assertIn("show", [c[0][1] for c in calls])
        for argv, kwargs in calls:
            self.assertFalse(kwargs.get("text") or kwargs.get("universal_newlines")
                             or kwargs.get("encoding"), " ".join(argv))
            if kwargs.get("input") is not None:
                self.assertIsInstance(kwargs["input"], bytes, " ".join(argv))


class TestCommitIdentity(unittest.TestCase):
    """Run 35179218050 fetched 1239 postings on a GitHub runner, then failed
    at commit-tree with "Author identity unknown": a runner has no git
    identity and git refuses to guess one."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.empty = tempfile.mkdtemp()
        empty_config = os.path.join(self.empty, "gitconfig")
        write_text(empty_config, "")
        self.real_root = storage.REPO_ROOT
        storage.REPO_ROOT = self.dir
        self.real_env = dict(os.environ)
        for key in list(os.environ):
            if key.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_")) or key in ("EMAIL",):
                del os.environ[key]
        os.environ["GIT_CONFIG_GLOBAL"] = empty_config
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        # Never guess a name or address from the host: the runner's condition,
        # made the same on every machine.
        subprocess.run(["git", "config", "user.useConfigOnly", "true"], cwd=self.dir)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.real_env)
        storage.REPO_ROOT = self.real_root
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.empty, ignore_errors=True)

    def test_a_host_with_no_git_identity_can_still_commit(self):
        tree = subprocess.run(["git", "mktree"], cwd=self.dir, input="",
                              capture_output=True, text=True).stdout.strip()
        bare = subprocess.run(["git", "commit-tree", tree, "-m", "x"], cwd=self.dir,
                              capture_output=True, text=True)
        self.assertNotEqual(bare.returncode, 0,
                            "precondition: this host must refuse to commit "
                            "without an identity, or the test proves nothing")

        sha = storage.commit_files({"seen.json": "{}\n"}, "run", branch="data")
        here = subprocess.run(["git", "rev-parse", "data"], cwd=self.dir,
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(here, sha)

    def test_the_identity_is_fixed_and_carries_no_personal_data(self):
        storage.commit_files({"seen.json": "{}\n"}, "run", branch="data")
        who = subprocess.run(["git", "log", "-1", "--format=%an <%ae>|%cn <%ce>", "data"],
                             cwd=self.dir, capture_output=True, text=True).stdout.strip()
        self.assertEqual(who, "job-aggregator <job-aggregator@invalid>|"
                              "job-aggregator <job-aggregator@invalid>")


class TestBranchPerMode(unittest.TestCase):
    def test_test_mode_has_a_branch_of_its_own(self):
        """Test mode keeps production's layout inside its branch, so on a
        shared branch its files would land on production paths."""
        self.assertEqual(storage.data_branch(False), "data")
        self.assertNotEqual(storage.data_branch(True), storage.data_branch(False))


class TestRestoreFromBranch(unittest.TestCase):
    """A GitHub runner starts with no working copies. The branch is the store."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.real_root = storage.REPO_ROOT
        storage.REPO_ROOT = self.dir
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.state = {
            "fetch-all/greenhouse.json": dumps([{"identity": "greenhouse:1", "source": "greenhouse"}]),
            "filtered.json": dumps([{"identity": "greenhouse:1", "source": "greenhouse"}]),
            "seen.json": dumps({"greenhouse:1": {"first_seen": "2026-09-10T00:00:00Z",
                                                 "source": "greenhouse"}}),
            "logs-runs/20260910T000000Z.json": dumps({"run_at": "x"}),
        }

    def tearDown(self):
        os.chdir(self.cwd)
        storage.REPO_ROOT = self.real_root
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_fresh_checkout_gets_every_committed_store(self):
        storage.commit_files(self.state, "run", branch="data")
        written = storage.restore_from_branch(False)
        self.assertEqual(sorted(written), ["data/fetch-all/greenhouse.json",
                                           "data/filtered.json", "data/seen.json"])
        for path in ("fetch-all/greenhouse.json", "filtered.json", "seen.json"):
            self.assertEqual(read_text("data/" + path), self.state[path], path)

    def test_run_logs_are_history_and_are_not_restored(self):
        storage.commit_files(self.state, "run", branch="data")
        storage.restore_from_branch(False)
        self.assertFalse(os.path.exists("data/logs-runs"))

    def test_the_branch_replaces_a_stale_local_copy(self):
        """A machine that has not run for a while holds an older copy.
        Appending to it and committing would delete what the branch gained."""
        storage.commit_files(self.state, "run", branch="data")
        write_atomic("data/fetch-all/greenhouse.json", dumps([]))
        storage.restore_from_branch(False)
        self.assertEqual(read_text("data/fetch-all/greenhouse.json"),
                         self.state["fetch-all/greenhouse.json"])

    def test_with_no_branch_local_files_are_left_alone(self):
        write_atomic("data/seen.json", "{}\n")
        self.assertEqual(storage.restore_from_branch(False), [])
        self.assertEqual(read_text("data/seen.json"), "{}\n")

    def test_local_only_stores_are_never_touched(self):
        """ADR-0020: aggregator stores exist only locally. The branch has no
        version of them, so a restore must not clear them."""
        storage.commit_files(self.state, "run", branch="data")
        write_atomic("data/local/seen.json", '{"himalayas:x": {}}\n')
        write_atomic("data/fetch-all-local/himalayas.json", "[]\n")
        storage.restore_from_branch(False)
        self.assertEqual(read_text("data/local/seen.json"), '{"himalayas:x": {}}\n')
        self.assertEqual(read_text("data/fetch-all-local/himalayas.json"), "[]\n")

    def test_a_listed_file_that_cannot_be_read_stops_the_restore(self):
        """Skipping it would start the run from an empty store for that file,
        and the next commit would replace the branch's copy with one run's."""
        storage.commit_files(self.state, "run", branch="data")
        real = storage.read_branch_file
        storage.read_branch_file = lambda path, branch: None if path == "seen.json" else real(path, branch)
        try:
            with self.assertRaises(StorageError):
                storage.restore_from_branch(False)
        finally:
            storage.read_branch_file = real

    def test_test_mode_restores_its_own_branch_into_its_own_directory(self):
        storage.commit_files(self.state, "run", branch="data")
        test_state = {"seen.json": dumps({"greenhouse:9": {"source": "greenhouse"}})}
        storage.commit_files(test_state, "run", branch="data-test")
        storage.restore_from_branch(True)
        self.assertEqual(read_text("data/test/seen.json"), test_state["seen.json"])
        self.assertFalse(os.path.exists("data/seen.json"),
                         "a test restore wrote a production path")
        self.assertFalse(os.path.exists("data/test/filtered.json"),
                         "a test restore read the production branch")


class TestOutcomesAndRunLogsFromTheBranch(unittest.TestCase):
    """Brief 6: ADR-0043's stores are state, so they are restored; run logs
    are history, and only this month's are read back, for the Airtable
    client's monthly budget. Borrows the restore tests' throwaway repository
    rather than subclassing, which would run those tests twice."""

    setUp = TestRestoreFromBranch.setUp
    tearDown = TestRestoreFromBranch.tearDown

    def test_outcome_stores_are_restored_with_the_rest(self):
        self.state["outcomes/accepted.json"] = dumps([{"identity": "greenhouse:1"}])
        storage.commit_files(self.state, "run", branch="data")
        written = storage.restore_from_branch(False)
        self.assertIn("data/outcomes/accepted.json", written)
        self.assertEqual(read_text("data/outcomes/accepted.json"),
                         self.state["outcomes/accepted.json"])

    def test_a_branch_without_outcome_stores_restores_none(self):
        """No sweep has written one yet. Absent reads as empty downstream."""
        storage.commit_files(self.state, "run", branch="data")
        storage.restore_from_branch(False)
        self.assertFalse(os.path.exists("data/outcomes"))

    def test_only_this_months_run_logs_are_read(self):
        self.state["logs-runs/20260831T235900Z.json"] = dumps({"run_at": "2026-08-31",
                                                               "airtable": {"calls_used": 900}})
        self.state["logs-runs/20260923T033636Z.json"] = dumps({"run_at": "2026-09-23",
                                                               "airtable": {"calls_used": 3}})
        storage.commit_files(self.state, "run", branch="data")
        logs = storage.read_month_run_logs("202609", False)
        self.assertEqual(sorted(log["run_at"] for log in logs), ["2026-09-23", "x"])
        self.assertEqual(storage.read_month_run_logs("202609", True), [],
                         "test mode read the production branch's logs")


class FakeGit:
    """Stands in for subprocess.run under read_private_files. No network."""

    def __init__(self, listing=b"abc123\tHEAD\n", fails=None, files=None, stderr=b""):
        self.listing = listing
        self.fails = fails or set()
        self.files = files or {}
        self.stderr = stderr
        self.calls = []

    def __call__(self, args, cwd=None, env=None, capture_output=None, timeout=None):
        self.calls.append(args)
        verb = next(a for a in args[1:] if not a.startswith("-") and "=" not in a
                    and not a.startswith("http.") and a != "credential.helper=")
        result = type("P", (), {})()
        result.returncode, result.stdout, result.stderr = 0, b"", b""
        if verb in self.fails:
            result.returncode, result.stderr = 128, self.stderr
        elif verb == "ls-remote":
            result.stdout = self.listing
        elif verb == "show":
            path = args[-1].split(":", 1)[1]
            if path in self.files:
                result.stdout = self.files[path].encode("utf-8")
            else:
                result.returncode = 128
        return result


class TestPrivateStore(unittest.TestCase):
    """ADR-0047 and the operator's decision of 2026-09-23: absent is empty,
    unreachable is a failure, and neither the token nor the repository's name
    reaches an error."""

    REPO = "someone/private-thing"
    TOKEN = "github_pat_FAKE0123456789"
    PATHS = ["outcomes/accepted.json", "outcomes/rejected_not_a_fit.json"]

    def read(self, git, repo=REPO, token=TOKEN):
        return storage.read_private_files(repo, token, self.PATHS, run=git)

    def assertClean(self, error):
        text = str(error)
        self.assertNotIn(self.TOKEN, text)
        self.assertNotIn(self.REPO, text)
        self.assertNotIn("private-thing", text)

    def test_a_file_the_repository_holds_is_returned_and_an_absent_one_is_none(self):
        git = FakeGit(files={"outcomes/accepted.json": "[]\n"})
        self.assertEqual(self.read(git), {"outcomes/accepted.json": "[]\n",
                                          "outcomes/rejected_not_a_fit.json": None})

    def test_an_empty_repository_holds_nothing_yet(self):
        git = FakeGit(listing=b"")
        self.assertEqual(self.read(git), dict.fromkeys(self.PATHS))
        self.assertFalse(any("fetch" in c for c in git.calls), "fetched an empty repository")

    def test_an_unreachable_repository_fails_and_says_nothing_it_should_not(self):
        """The case built to defeat a message guard: git's own stderr quotes
        the repository, and the token is set in the header."""
        git = FakeGit(fails={"ls-remote"},
                      stderr=("remote: Repository not found.\nfatal: repository "
                              "'https://github.com/%s.git/' not found (%s)"
                              % (self.REPO, self.TOKEN)).encode("utf-8"))
        with self.assertRaises(storage.PrivateStoreUnreachable) as caught:
            self.read(git)
        self.assertClean(caught.exception)
        self.assertIn("git exit 128", str(caught.exception))

    def test_a_failed_fetch_is_unreachable_too(self):
        """Listed but not fetchable fails the same way and says which: the
        audit of 2026-09-24 found an unborn default branch reported as a
        repository that could not be reached."""
        git = FakeGit(fails={"fetch"},
                      stderr=("fatal: couldn't find remote ref (%s %s)"
                              % (self.REPO, self.TOKEN)).encode("utf-8"))
        with self.assertRaises(storage.PrivateStoreUnreachable) as caught:
            self.read(git)
        self.assertIn("reached and listed", str(caught.exception))
        self.assertIn("default branch", str(caught.exception))
        self.assertClean(caught.exception)

    def test_missing_secrets_are_named_not_echoed(self):
        for repo, token in (("", self.TOKEN), (self.REPO, ""), (None, None)):
            with self.assertRaises(storage.PrivateStoreUnreachable) as caught:
                self.read(FakeGit(), repo=repo, token=token)
            self.assertIn("AGGREGATOR_STORE", str(caught.exception))
            self.assertClean(caught.exception)

    def test_a_url_in_the_repository_secret_is_refused(self):
        for repo in ("https://github.com/%s" % self.REPO, self.REPO + ".git",
                     self.REPO + "/"):
            with self.assertRaises(storage.PrivateStoreUnreachable) as caught:
                self.read(FakeGit(), repo=repo)
            self.assertClean(caught.exception)

    def test_the_token_is_never_a_bare_argument(self):
        git = FakeGit(files={})
        self.read(git)
        for args in git.calls:
            self.assertFalse(any(self.TOKEN in a for a in args),
                             "the token appeared in plain text on a command line")


class TestSeenStorePartition(unittest.TestCase):
    def test_a_mixed_store_splits_by_whether_its_source_may_be_published(self):
        """A seen file written before the split holds both classes, as
        data/test/seen.json did on 2026-09-17 with 500 Himalayas entries."""
        store = SeenStore({"greenhouse:1": {"source": "greenhouse"},
                           "himalayas:2": {"source": "himalayas"},
                           "unknown:3": {}})
        public, local = store.partition(lambda s: s == "greenhouse")
        self.assertEqual(public.identities, {"greenhouse:1"})
        self.assertEqual(local.identities, {"himalayas:2", "unknown:3"})

    def test_load_many_merges_the_two_halves(self):
        d = tempfile.mkdtemp()
        try:
            a, b = os.path.join(d, "a.json"), os.path.join(d, "b.json")
            write_atomic(a, dumps({"greenhouse:1": {"source": "greenhouse"}}))
            write_atomic(b, dumps({"himalayas:2": {"source": "himalayas"}}))
            merged = SeenStore.load_many([a, b, os.path.join(d, "missing.json")])
            self.assertEqual(merged.identities, {"greenhouse:1", "himalayas:2"})
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
