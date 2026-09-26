"""The private aggregator store, ADR-0047, against a real git repository.

A local bare repository stands in for the private GitHub repository through a
file URL, so git's own behaviour is exercised rather than a fake's: an empty
repository, a first write, a restore, an append on top, a refused
non-fast-forward, and a test branch that never touches production's. No
network and no token.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.private_store import PrivateStore, files_to_push, local_path_for
from src.storage import PrivateStoreUnreachable, private_store_basic

REPO = "someone/private-thing"
TOKEN = "github_pat_FAKE0123456789"


def file_url(path):
    return "file:///" + path.replace(os.sep, "/").lstrip("/")


class Harness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.bare = os.path.join(self.dir, "store.git")
        subprocess.run(["git", "init", "-q", "--bare", self.bare], check=True)
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.paths = storage.layout(False)
        self.opened = []

    def tearDown(self):
        for s in self.opened:
            s.close()
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def store(self, test_mode=False, run=subprocess.run):
        url = file_url(self.bare)
        s = PrivateStore(REPO, TOKEN, test_mode=test_mode, run=run, url_for=lambda repo: url)
        self.opened.append(s)
        return s.open()

    def branches(self):
        out = subprocess.run(["git", "--git-dir", self.bare, "branch",
                              "--format=%(refname:short)"],
                             capture_output=True, text=True).stdout.split()
        return sorted(out)

    def read_local(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()


class TestRoundTrip(Harness):
    def test_an_empty_repository_opens_holding_nothing(self):
        s = self.store()
        self.assertIsNone(s.tip)
        self.assertEqual(s.paths(), [])
        self.assertIsNone(s.read("seen.json"))
        self.assertEqual(s.restore(self.paths), [])

    def test_a_first_write_creates_the_branch_and_the_next_run_restores_it(self):
        self.store().commit_and_push({"seen.json": "{}\n",
                                      "fetch-all/himalayas.json": "[]\n"}, "run 1")
        self.assertEqual(self.branches(), ["data"])
        s = self.store()
        self.assertEqual(sorted(s.paths()), ["fetch-all/himalayas.json", "seen.json"])
        self.assertEqual(s.read("seen.json"), "{}\n")

    def test_a_later_write_builds_on_the_last_and_keeps_what_it_does_not_rewrite(self):
        first = self.store().commit_and_push({"seen.json": "{}\n",
                                              "filtered.json": "[1]\n"}, "run 1")
        second = self.store().commit_and_push({"filtered.json": "[1, 2]\n"}, "run 2")
        parent = subprocess.run(["git", "--git-dir", self.bare, "rev-parse", second + "^"],
                                capture_output=True, text=True).stdout.strip()
        self.assertEqual(parent, first, "the second write did not build on the first")
        s = self.store()
        self.assertEqual(s.read("seen.json"), "{}\n", "an untouched file was lost")
        self.assertEqual(s.read("filtered.json"), "[1, 2]\n")

    def test_nothing_changed_makes_no_commit(self):
        self.store().commit_and_push({"seen.json": "{}\n"}, "run 1")
        self.assertIsNone(self.store().commit_and_push({"seen.json": "{}\n"}, "run 2"))

    def test_a_store_that_moved_meanwhile_refuses_rather_than_being_overwritten(self):
        """Two runs racing: the second push is not a fast-forward and fails,
        which the run turns into exit 2. The first run's write survives."""
        self.store().commit_and_push({"seen.json": "{}\n"}, "seed")
        a, b = self.store(), self.store()
        a.commit_and_push({"filtered.json": "[\"a\"]\n"}, "a")
        with self.assertRaises(PrivateStoreUnreachable):
            b.commit_and_push({"filtered.json": "[\"b\"]\n"}, "b")
        self.assertEqual(self.store().read("filtered.json"), "[\"a\"]\n")

    def test_a_store_never_opened_refuses_to_write(self):
        """Unopened, it has no scratch repository, and git would run in
        whatever directory the process is in: this repository, on a machine."""
        s = PrivateStore(REPO, TOKEN, url_for=lambda repo: file_url(self.bare))
        with self.assertRaises(PrivateStoreUnreachable):
            s.commit_and_push({"seen.json": "{}\n"}, "run")
        self.assertEqual(self.branches(), [])


class TestRestore(Harness):
    def test_each_stored_file_lands_on_its_working_copy(self):
        self.store().commit_and_push({
            "fetch-all/himalayas.json": "[\"raw\"]\n", "filtered.json": "[\"kept\"]\n",
            "seen.json": "{\"seen\": 1}\n", "outcomes/accepted.json": "[]\n",
            "README.md": "not a store\n"}, "run 1")
        written = self.store().restore(self.paths)
        self.assertEqual(sorted(written), sorted([
            "data/fetch-all-local/himalayas.json", "data/local/filtered.json",
            "data/local/seen.json", "data/local/outcomes/accepted.json"]))
        self.assertEqual(self.read_local(self.paths["local_filtered"]), "[\"kept\"]\n")
        self.assertEqual(self.read_local("data/fetch-all-local/himalayas.json"), "[\"raw\"]\n")

    def test_the_branch_wins_over_a_local_copy(self):
        """A stale local copy appended to and pushed would delete what the
        store gained meanwhile, ADR-0003's snapshot failure."""
        self.store().commit_and_push({"seen.json": "{\"stored\": 1}\n"}, "run 1")
        storage.write_atomic(self.paths["local_seen"], "{\"stale\": 1}\n")
        self.store().restore(self.paths)
        self.assertEqual(self.read_local(self.paths["local_seen"]), "{\"stored\": 1}\n")

    def test_no_branch_leaves_local_copies_alone(self):
        storage.write_atomic(self.paths["local_seen"], "{\"local\": 1}\n")
        self.assertEqual(self.store().restore(self.paths), [])
        self.assertEqual(self.read_local(self.paths["local_seen"]), "{\"local\": 1}\n")

    def test_only_the_stores_layout_maps_to_a_working_copy(self):
        for stored in ("README.md", "fetch-all/sub/x.json", "fetch-all/x.txt",
                       "logs-runs/20260924T000000Z.json", "outcomes/x.csv"):
            with self.subTest(stored=stored):
                self.assertIsNone(local_path_for(stored, self.paths))

    def test_what_is_pushed_is_the_runs_aggregator_files_and_their_outcomes(self):
        """The raw, filtered and seen files, and from ADR-0050 the outcome
        stores the sweep writes for aggregator rows. Never a public file."""
        storage.write_atomic("data/fetch-all-local/himalayas.json", "[\"raw\"]\n")
        storage.write_atomic(self.paths["local_filtered"], "[\"kept\"]\n")
        storage.write_atomic(self.paths["local_seen"], "{}\n")
        storage.write_atomic("data/local/outcomes/accepted.json", "[]\n")
        storage.write_atomic(self.paths["filtered"], "[\"public\"]\n")
        storage.write_atomic("data/outcomes/accepted.json", "[\"public\"]\n")
        self.assertEqual(files_to_push(self.paths), {
            "fetch-all/himalayas.json": "[\"raw\"]\n", "filtered.json": "[\"kept\"]\n",
            "seen.json": "{}\n", "outcomes/accepted.json": "[]\n"})


class TestTestModeIsolation(Harness):
    def test_test_mode_writes_its_own_branch_and_never_reads_production(self):
        self.store().commit_and_push({"seen.json": "{\"production\": 1}\n"}, "prod")
        t = self.store(test_mode=True)
        self.assertIsNone(t.read("seen.json"), "a test run read production's branch")
        t.commit_and_push({"seen.json": "{\"test\": 1}\n"}, "test")
        self.assertEqual(self.branches(), ["data", "data-test"])
        self.assertEqual(self.store().read("seen.json"), "{\"production\": 1}\n")


class TestSecrets(Harness):
    def test_an_unreachable_repository_raises_and_names_nothing_it_should_not(self):
        """The case built to defeat the scrub: git's stderr quotes the URL,
        and this URL carries the repository's name, the token, and the token
        in the encoded form git sends it in. The audit of 2026-09-24 dropped
        the encoded form from the scrub and nothing failed (F11)."""
        missing = os.path.join(self.dir, "nowhere.git")
        basic = private_store_basic(TOKEN)
        s = PrivateStore(REPO, TOKEN, url_for=lambda repo: file_url(missing) + "/" + REPO
                         + "/" + TOKEN + "/" + basic)
        self.opened.append(s)
        with self.assertRaises(PrivateStoreUnreachable) as caught:
            s.open()
        for secret in (REPO, TOKEN, "private-thing", basic):
            self.assertNotIn(secret, str(caught.exception))
        self.assertIn("git exit", str(caught.exception))

    def test_every_git_call_has_a_time_limit(self):
        """One hung call to the private store, opened before the fetch and
        pushed before the commit, would hold the job until GitHub kills it,
        and the fetch would go with it. The audit of 2026-09-24 removed the
        limit and nothing failed (F2)."""
        limits = []

        def recording(args, **kw):
            limits.append(kw.get("timeout"))
            return subprocess.run(args, **kw)
        url = file_url(self.bare)
        s = PrivateStore(REPO, TOKEN, run=recording, url_for=lambda repo: url, timeout=7)
        self.opened.append(s)
        s.open().commit_and_push({"seen.json": "{}\n"}, "run 1")
        self.assertGreater(len(limits), 5)
        self.assertEqual(set(limits), {7})

        def hanging(args, **kw):
            raise subprocess.TimeoutExpired(args, kw.get("timeout"))
        hung = PrivateStore(REPO, TOKEN, run=hanging, url_for=lambda repo: url)
        self.opened.append(hung)
        with self.assertRaises(PrivateStoreUnreachable) as caught:
            hung.open()
        self.assertIn("timed out", str(caught.exception))

    def test_the_token_is_never_a_bare_argument(self):
        calls = []

        def recording(args, **kw):
            calls.append(args)
            return subprocess.run(args, **kw)

        self.store(run=recording).commit_and_push({"seen.json": "{}\n"}, "run 1")
        self.assertTrue(any("push" in args for args in calls))
        for args in calls:
            self.assertFalse(any(TOKEN in a for a in args),
                             "the token appeared in plain text on a command line")

    def test_missing_secrets_are_named_not_echoed(self):
        for repo, token in (("", TOKEN), (REPO, ""), (None, None)):
            with self.assertRaises(PrivateStoreUnreachable) as caught:
                PrivateStore(repo, token)
            self.assertIn("AGGREGATOR_STORE", str(caught.exception))
            self.assertNotIn(TOKEN, str(caught.exception))

    def test_a_url_in_the_repository_secret_is_refused(self):
        for repo in ("https://github.com/" + REPO, REPO + ".git", REPO + "/"):
            with self.assertRaises(PrivateStoreUnreachable) as caught:
                PrivateStore(repo, TOKEN)
            self.assertNotIn("private-thing", str(caught.exception))


class TestTheFullBranch(Harness):
    """D11, 2026-09-26: every field a board returns, kept on the full branch,
    one file per run, each read back after its push."""

    def show(self, branch, path):
        p = subprocess.run(["git", "--git-dir", self.bare, "show", "%s:%s" % (branch, path)],
                           capture_output=True, text=True, encoding="utf-8")
        return p.stdout if p.returncode == 0 else None

    def test_each_file_lands_on_the_full_branch_beside_the_last(self):
        s = self.store()
        first = s.save_full("full/one.json", '[{"posting": 1}]\n', "one")
        second = s.save_full("full/two.json", '[{"posting": 2}]\n', "two")
        self.assertNotEqual(first, second)
        self.assertEqual(self.show("data-full", "full/one.json"), '[{"posting": 1}]\n')
        self.assertEqual(self.show("data-full", "full/two.json"), '[{"posting": 2}]\n')
        self.assertEqual(self.branches(), ["data-full"], "the data branch was touched")

    def test_test_mode_writes_its_own_full_branch(self):
        self.store(test_mode=True).save_full("full/t.json", "[]\n", "t")
        self.assertEqual(self.branches(), ["data-test-full"])

    def test_the_read_back_refuses_a_file_the_branch_does_not_hold(self):
        """The case built to defeat the check: the push appears to succeed,
        and the branch read back lists the file under different content."""
        def lying(args, **kw):
            p = subprocess.run(args, **kw)
            if "ls-tree" in args and "refs/remotes/readback" in args:
                p.stdout = p.stdout.replace(p.stdout.split()[2], b"0" * 40)
            return p
        s = self.store(run=lying)
        with self.assertRaises(PrivateStoreUnreachable) as caught:
            s.save_full("full/x.json", '[{"posting": 3}]\n', "x")
        self.assertIn("different content", str(caught.exception))

    def test_the_read_back_refuses_a_file_missing_after_the_push(self):
        def forgetful(args, **kw):
            p = subprocess.run(args, **kw)
            if "ls-tree" in args and "refs/remotes/readback" in args:
                p.stdout = b""
            return p
        s = self.store(run=forgetful)
        with self.assertRaises(PrivateStoreUnreachable) as caught:
            s.save_full("full/y.json", "[]\n", "y")
        self.assertIn("does not list", str(caught.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
