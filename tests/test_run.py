"""The fetch run, tested from the brief.

The brief requires three exit codes, a run log carrying every board every run
including zeros, and a TEST_MODE run that leaves production data alone.

No test here touches the network or the real repository.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import run as run_module
from src import storage
from src.config import Board, ConfigError
from src.normalise import dumps
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.run import EXIT_OK, EXIT_STOPPED_RESUMABLE, Run, summarise

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
MATCHER = TitleMatcher()

GH = Board(platform="greenhouse", slug="careem")
GH2 = Board(platform="greenhouse", slug="globalli")
LV = Board(platform="lever", slug="spreetail", employer_alias="Spreetail")


def gh_payload(titles, start=0):
    return {"jobs": [{"id": 1000 + start + i, "title": t,
                      "absolute_url": "https://boards.test/%d" % (1000 + start + i),
                      "first_published": "2026-09-10T05:00:00+00:00",
                      "company_name": "Careem",
                      "location": {"name": "Karachi"}}
                     for i, t in enumerate(titles)]}


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status_code = status
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


class FakeSession:
    """Maps a URL fragment to a payload, or to an Exception to raise."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append(url)
        for fragment, value in self.routes.items():
            if fragment in url:
                if isinstance(value, Exception):
                    raise value
                return FakeResponse(value)
        return FakeResponse({"jobs": []})


def client_for(routes, **kw):
    kw.setdefault("min_interval", 0)
    return HttpClient(session=FakeSession(routes), sleep=lambda s: None, **kw)


class RunHarness(unittest.TestCase):
    """Each test runs in its own directory, so nothing shares state."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)


class TestNormalRun(RunHarness):
    def test_writes_both_layers_and_logs_every_board(self):
        client = client_for({"careem": gh_payload(["AI Engineer", "Chief Happiness Officer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()

        self.assertEqual(log["totals"]["fetched"], 3)
        self.assertEqual(log["totals"]["new"], 3)
        self.assertEqual(log["totals"]["kept"], 2, "the happiness officer is dropped")
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 3})
        self.assertEqual(log["totals"]["written_filtered"], 2)
        self.assertEqual(len(storage.read_records("data/fetch-all/greenhouse.json")), 3)
        self.assertEqual(len(storage.read_records("data/filtered.json")), 2)

    def test_a_board_returning_zero_still_gets_a_line(self):
        """A board returning nothing for a week is a broken adapter, and
        without a zero logged it looks like a quiet market."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": {"jobs": []}})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(set(lines), {"greenhouse:careem", "greenhouse:globalli"})
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 0)
        self.assertEqual(lines["greenhouse:globalli"]["status"], "ok")

    def test_drops_are_attributed_per_board_and_per_rule(self):
        client = client_for({"careem": gh_payload(["Chief Happiness Officer"]),
                             "globalli": gh_payload(["AI Engineer"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["drops"], {"title": 1})
        self.assertEqual(lines["greenhouse:globalli"]["drops"], {})
        self.assertEqual(log["totals"]["drops"]["title"], 1)

    def test_request_counts_are_reported_per_source(self):
        """ADR-0028: this log is what sets the real ceiling later."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "spreetail": []})
        log = Run([GH, LV], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["requests"]["by_source"], {"greenhouse": 1, "lever": 1})
        self.assertEqual(log["requests"]["budget"], 500)

    def test_a_second_run_with_no_changes_writes_nothing_new(self):
        """The brief's check, end to end."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        before = read_text("data/fetch-all/greenhouse.json")

        log = Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        after = read_text("data/fetch-all/greenhouse.json")

        self.assertEqual(log["totals"]["new"], 0)
        self.assertEqual(before, after)

    def test_first_seen_survives_the_second_run(self):
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        seen_first = json.loads(read_text("data/seen.json"))
        later = datetime(2026, 10, 1, tzinfo=timezone.utc)
        Run([GH], client_for({"careem": payload}), now=later, matcher=MATCHER).execute()
        seen_second = json.loads(read_text("data/seen.json"))
        key = list(seen_first)[0]
        self.assertEqual(seen_first[key]["first_seen"], seen_second[key]["first_seen"])
        self.assertNotEqual(seen_second[key]["last_seen"], seen_second[key]["first_seen"])


class TestFailureHandling(RunHarness):
    def test_one_dead_board_does_not_cost_the_others(self):
        client = client_for({"careem": OSError("connection reset"),
                             "globalli": gh_payload(["AI Engineer"], start=50)},
                            max_attempts=1)
        run = Run([GH, GH2], client, now=NOW, matcher=MATCHER)
        log = run.execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["status"], "failed",
                         "a transport failure is the board's, not ours")
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 1)
        self.assertEqual(run.exit_code(), EXIT_OK)

    def test_an_unparseable_payload_stops_that_board_only(self):
        client = client_for({"careem": {"postings": []},
                             "globalli": gh_payload(["AI Engineer"], start=50)})
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:careem"]["status"], "unparseable")
        self.assertEqual(lines["greenhouse:globalli"]["fetched"], 1)

    def test_budget_exhaustion_stops_the_run_and_names_what_was_missed(self):
        """Exit 2: stopped deliberately and resumable, not a failure."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)},
                            budget=1)
        run = Run([GH, GH2], client, now=NOW, matcher=MATCHER)
        log = run.execute()
        self.assertEqual(run.exit_code(), EXIT_STOPPED_RESUMABLE)
        self.assertIsNotNone(log["stopped"])
        lines = {b["board"]: b for b in log["boards"]}
        self.assertEqual(lines["greenhouse:globalli"]["status"], "not reached")

    def test_work_reached_before_the_stop_is_still_written(self):
        """Stopping must not discard what the run already has."""
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": gh_payload(["Data Scientist"], start=50)},
                            budget=1)
        log = Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 1})
        self.assertEqual(len(storage.read_records("data/fetch-all/greenhouse.json")), 1)


class TestSourceRouting(RunHarness):
    def test_each_source_writes_its_own_file(self):
        """ADR-0020: a row's provenance is its filename."""
        client = client_for({
            "careem": gh_payload(["AI Engineer"]),
            "spreetail": [{"id": "lv1", "text": "Machine Learning Engineer",
                           "hostedUrl": "https://jobs.lever.co/spreetail/lv1",
                           "createdAt": 1789018446882,
                           "categories": {"location": "Karachi"}}]})
        log = Run([GH, LV], client, now=NOW, matcher=MATCHER).execute()
        self.assertEqual(log["totals"]["written_raw"], {"greenhouse": 1, "lever": 1})
        gh_rows = storage.read_records("data/fetch-all/greenhouse.json")
        lv_rows = storage.read_records("data/fetch-all/lever.json")
        self.assertEqual({r["source"] for r in gh_rows}, {"greenhouse"})
        self.assertEqual({r["source"] for r in lv_rows}, {"lever"})

    def test_lever_rows_carry_their_derived_employer_and_provenance(self):
        client = client_for({"spreetail": [
            {"id": "lv1", "text": "AI Engineer",
             "hostedUrl": "https://jobs.lever.co/spreetail/lv1",
             "createdAt": 1789018446882, "categories": {"location": "Karachi"}}]})
        Run([LV], client, now=NOW, matcher=MATCHER).execute()
        row = storage.read_records("data/fetch-all/lever.json")[0]
        self.assertEqual(row["employer"], "Spreetail")
        self.assertEqual(row["employer_provenance"], "slug")
        self.assertTrue(row["published_meaning_unconfirmed"])


class TestTestMode(RunHarness):
    def test_test_mode_leaves_production_files_untouched(self):
        """The brief's check."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        production = read_text("data/fetch-all/greenhouse.json")

        client = client_for({"careem": gh_payload(["Data Scientist"], start=99)})
        Run([GH], client, now=NOW, test_mode=True, matcher=MATCHER).execute()

        self.assertEqual(read_text("data/fetch-all/greenhouse.json"),
                         production)
        self.assertTrue(os.path.exists("data/test/fetch-all/greenhouse.json"))
        self.assertEqual(len(storage.read_records("data/test/fetch-all/greenhouse.json")), 1)

    def test_test_mode_isolates_the_filtered_layer_and_the_seen_store(self):
        """Isolating only the raw file is not isolation: a test run that
        rewrote the production seen store would re-date first_seen for every
        posting, and one that appended to production filtered.json would put
        test rows in front of the operator."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        filtered_before = read_text("data/filtered.json")
        seen_before = read_text("data/seen.json")

        client = client_for({"careem": gh_payload(["Machine Learning Engineer"], start=99)})
        Run([GH], client, now=NOW, test_mode=True, matcher=MATCHER).execute()

        self.assertEqual(read_text("data/filtered.json"), filtered_before)
        self.assertEqual(read_text("data/seen.json"), seen_before)
        self.assertTrue(os.path.exists("data/test/filtered.json"))
        self.assertTrue(os.path.exists("data/test/seen.json"))


class TestMain(unittest.TestCase):
    """The entry point the workflow calls, end to end against a throwaway
    repository and a fake network. Never the real repository, never a board.

    `fresh_machine` is what a GitHub runner starts with: the repository and
    its branches, and no working copies under data/."""

    def setUp(self):
        # main() reads TEST_MODE from the environment. These tests must not
        # inherit it: run 35236457737 set it for the whole job, so the test
        # step saw TEST_MODE=1 and seven of these tests failed on GitHub while
        # passing on every machine without it.
        self.env_test_mode = os.environ.pop("TEST_MODE", None)
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.real = (storage.REPO_ROOT, storage.commit_files, storage.restore_from_branch,
                     run_module.load_boards, run_module.HttpClient)
        storage.REPO_ROOT = self.dir
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.payload = gh_payload(["AI Engineer"])
        run_module.load_boards = lambda: [GH]
        run_module.HttpClient = lambda **kw: client_for({"careem": self.payload})

    def tearDown(self):
        (storage.REPO_ROOT, storage.commit_files, storage.restore_from_branch,
         run_module.load_boards, run_module.HttpClient) = self.real
        os.environ.pop("TEST_MODE", None)
        if self.env_test_mode is not None:
            os.environ["TEST_MODE"] = self.env_test_mode
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = run_module.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def git(self, *args):
        p = subprocess.run(["git"] + list(args), cwd=self.dir, capture_output=True,
                           text=True, encoding="utf-8")
        return p.returncode, p.stdout.strip()

    def on_branch(self, branch, path):
        code, text = self.git("show", "%s:%s" % (branch, path))
        self.assertEqual(code, 0, "%s:%s is missing" % (branch, path))
        return text

    def identities(self, branch):
        return [r["identity"] for r in json.loads(self.on_branch(branch, "fetch-all/greenhouse.json"))]

    def last_run_log(self, test_mode=False):
        d = storage.layout(test_mode)["runlog_dir"]
        with open(os.path.join(d, sorted(os.listdir(d))[-1]), encoding="utf-8") as f:
            return json.load(f)

    def fresh_machine(self):
        shutil.rmtree("data", ignore_errors=True)

    # ------------------------------------------------ state across machines
    def test_a_fresh_machine_continues_from_the_branch(self):
        self.assertEqual(self.main()[0], EXIT_OK)
        _, first = self.git("rev-parse", "data")
        raw_before = self.on_branch("data", "fetch-all/greenhouse.json")
        seen_before = json.loads(self.on_branch("data", "seen.json"))

        self.fresh_machine()
        code, out, _ = self.main()
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(self.last_run_log()["totals"]["new"], 0,
                         "the second run did not know what the first stored")
        self.assertEqual(self.on_branch("data", "fetch-all/greenhouse.json"), raw_before)
        seen_after = json.loads(self.on_branch("data", "seen.json"))
        for identity, entry in seen_before.items():
            self.assertEqual(seen_after[identity]["first_seen"], entry["first_seen"],
                             "first_seen was re-dated")
        self.assertEqual(self.git("rev-parse", "data^")[1], first,
                         "the second commit does not continue the first")
        self.assertIn("restored from the data branch", out)

    def test_a_posting_a_board_stops_sending_stays_on_the_branch(self):
        """ADR-0003 on a machine with no working copies. Without the restore
        the second commit is a snapshot of one run, and history is deleted."""
        self.payload = gh_payload(["AI Engineer", "ML Engineer"])
        self.main()
        self.fresh_machine()
        self.payload = gh_payload(["ML Engineer", "Data Engineer"], start=1)
        self.assertEqual(self.main()[0], EXIT_OK)
        self.assertEqual(self.identities("data"),
                         ["greenhouse:1000", "greenhouse:1001", "greenhouse:1002"])

    def test_a_no_commit_run_neither_reads_nor_writes_the_branch(self):
        self.main()
        _, before = self.git("rev-parse", "data")
        self.fresh_machine()
        code, out, _ = self.main("--no-commit")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(self.git("rev-parse", "data")[1], before)
        self.assertEqual(self.last_run_log()["totals"]["new"], 1,
                         "a no-commit run read the branch")
        self.assertNotIn("restored", out)

    # ------------------------------------------------------------ test mode
    def test_test_mode_commits_to_its_own_branch_and_never_to_production(self):
        """The handoff believed a test_mode dispatch left production alone. It
        did not: test files were committed to production paths on `data`."""
        self.main()
        _, production = self.git("rev-parse", "data")
        self.payload = gh_payload(["Data Scientist"], start=99)
        self.assertEqual(self.main("--test-mode")[0], EXIT_OK)
        self.assertEqual(self.git("rev-parse", "data")[1], production)
        self.assertIn("greenhouse:1099", self.identities("data-test"))
        self.assertNotIn("greenhouse:1099", self.identities("data"))

    def test_the_environment_variable_selects_test_mode(self):
        """The workflow selects test mode with TEST_MODE=1, not the flag, and
        nothing tested that route until run 35236457737."""
        self.main()
        _, production = self.git("rev-parse", "data")
        os.environ["TEST_MODE"] = "1"
        self.payload = gh_payload(["Data Scientist"], start=99)
        self.assertEqual(self.main()[0], EXIT_OK)
        self.assertEqual(self.git("rev-parse", "data")[1], production)
        self.assertIn("greenhouse:1099", self.identities("data-test"))

    def test_any_other_value_leaves_production_mode(self):
        os.environ["TEST_MODE"] = "0"
        self.assertEqual(self.main()[0], EXIT_OK)
        self.assertEqual(self.git("rev-parse", "--verify", "--quiet", "data")[0], 0)
        self.assertNotEqual(self.git("rev-parse", "--verify", "--quiet", "data-test")[0], 0)

    def test_test_mode_with_no_production_branch_creates_none(self):
        self.assertEqual(self.main("--test-mode")[0], EXIT_OK)
        self.assertEqual(self.git("rev-parse", "--verify", "--quiet", "data-test")[0], 0)
        self.assertNotEqual(self.git("rev-parse", "--verify", "--quiet", "data")[0], 0)

    def test_test_mode_starts_from_the_test_branch_not_production(self):
        self.main()
        self.fresh_machine()
        self.main("--test-mode")
        self.assertEqual(self.last_run_log(True)["totals"]["new"], 1,
                         "a test run started from production's state")

    # ------------------------------------------------- failures and labels
    def test_a_commit_failure_after_a_fetch_is_not_reported_as_could_not_start(self):
        """Run 35179218050 fetched 1239 postings, failed at commit-tree, and
        the workflow reported that the run could not start."""
        def refuse(*args, **kwargs):
            raise storage.StorageError("git commit-tree failed: Author identity unknown")
        storage.commit_files = refuse
        code, _, err = self.main()
        self.assertEqual(code, 1)
        self.assertNotIn("could not start", err)
        self.assertIn("the fetch completed", err)
        self.assertIn("committing to the data branch", err)
        self.assertIn("Author identity unknown", err)
        self.assertEqual(len(storage.read_records("data/fetch-all/greenhouse.json")), 1,
                         "the fetched work is not on disk")

    def test_a_refused_commit_set_fails_the_run_and_commits_nothing(self):
        """ADR-0020's last gate raising is a failure, never a quiet success."""
        storage.write_atomic("data/filtered.json",
                             dumps([{"identity": "himalayas:x", "source": "himalayas"}]))
        code, _, err = self.main()
        self.assertEqual(code, 1)
        self.assertIn("refusing to commit filtered.json", err)
        self.assertNotEqual(self.git("rev-parse", "--verify", "--quiet", "data")[0], 0)

    def test_a_config_error_is_reported_as_could_not_start(self):
        def broken():
            raise ConfigError("board config not found")
        run_module.load_boards = broken
        code, _, err = self.main()
        self.assertEqual(code, 1)
        self.assertIn("could not start", err)

    def test_an_unreadable_branch_stops_the_run_before_any_fetch(self):
        def unreadable(test_mode=False):
            raise storage.StorageError("data:seen.json is listed but could not be read")
        storage.restore_from_branch = unreadable
        code, _, err = self.main()
        self.assertEqual(code, 1)
        self.assertIn("could not start", err)
        self.assertFalse(os.path.exists("data/fetch-all/greenhouse.json"),
                         "the run fetched without its state")


class TestSummary(RunHarness):
    def test_summary_names_every_board_and_the_request_count(self):
        client = client_for({"careem": gh_payload(["AI Engineer"]),
                             "globalli": {"jobs": []}})
        text = summarise(Run([GH, GH2], client, now=NOW, matcher=MATCHER).execute())
        self.assertIn("greenhouse:careem", text)
        self.assertIn("greenhouse:globalli", text)
        self.assertIn("requests:", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
