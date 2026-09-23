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
from src.airtable import AirtableConfigError
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


class FakeAirtable:
    """Stands in for AirtableClient in the run's tests. Records what it is
    given and sends nothing, so no test reaches a live base."""

    CALLS = 3

    def __init__(self):
        self.sent = []
        self.rows_sent = 0

    def upsert(self, records):
        self.sent.extend(records)
        self.rows_sent += len(records)
        return {"created": [], "updated": []}

    def counters(self):
        return {"calls_used": self.CALLS, "rows_sent": self.rows_sent}

    def redact(self, text):
        return text


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


class TestTheBackfillInsideARun(RunHarness):
    """ADR-0030, wired into the run on 2026-09-18 so the filtered layer tracks
    the rules without anyone remembering after a pool change.

    The audit before wiring it found two ways it could do harm. Both are
    tested here, because both are silent failures."""

    def test_a_run_heals_a_gap_the_normal_write_path_cannot(self):
        """The situation the backfill exists for: the posting is in the raw
        layer and in the seen store, so no run will ever offer it again, and
        the rules now admit it."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        self.assertEqual(len(storage.read_records("data/filtered.json")), 1)

        # Delete the row from the filtered layer, leaving raw and seen intact.
        # That is exactly the shape a widened pool produces.
        storage.write_atomic("data/filtered.json", storage.dumps([]))

        log = Run([GH], client_for({"careem": payload}), now=NOW,
                  matcher=MATCHER).execute()
        self.assertEqual(len(storage.read_records("data/filtered.json")), 1,
                         "the run did not heal the gap")
        self.assertEqual(log["totals"]["backfilled"], 1)
        self.assertEqual(log["totals"]["written_filtered"], 0,
                         "the row came from the backfill, not the normal path")

    def test_the_backfill_count_is_reported_apart_from_the_run_s_own_writes(self):
        """The first audit finding. If these were one number, a broken write
        path would read as a healthy run: the backfill would quietly write the
        same rows and nothing would say so."""
        payload = gh_payload(["AI Engineer"])
        log = Run([GH], client_for({"careem": payload}), now=NOW,
                  matcher=MATCHER).execute()
        totals = log["totals"]
        for key in ("backfilled", "backfilled_public", "backfilled_local"):
            self.assertIn(key, totals)
        # A first run writes through the normal path, so the backfill finds
        # nothing. That is the healthy shape and it must be distinguishable.
        self.assertEqual(totals["written_filtered"], 1)
        self.assertEqual(totals["backfilled"], 0)
        self.assertIn("backfilled:", summarise(log))

    def test_a_test_run_backfills_test_paths_and_never_production(self):
        """The second audit finding, and the more dangerous one. The backfill
        inherits the run's paths; if it ever read the production layout while
        in test mode it would heal, or corrupt, production from a test."""
        payload = gh_payload(["AI Engineer"])
        Run([GH], client_for({"careem": payload}), now=NOW, matcher=MATCHER).execute()
        production = read_text("data/filtered.json")

        # A gap in production that only a backfill could close.
        storage.write_atomic("data/filtered.json", storage.dumps([]))

        Run([GH], client_for({"careem": gh_payload(["AI Engineer"], start=77)}),
            now=NOW, test_mode=True, matcher=MATCHER).execute()

        self.assertEqual(read_text("data/filtered.json"),
                         storage.dumps([]),
                         "a test run's backfill reached production")
        self.assertNotEqual(read_text("data/filtered.json"), production)
        self.assertTrue(os.path.exists("data/test/filtered.json"))

    def test_an_aggregator_row_is_never_backfilled_into_the_public_file(self):
        """ADR-0020 through the run's own backfill, not the tool's."""
        client = client_for({"careem": gh_payload(["AI Engineer"])})
        Run([GH], client, now=NOW, matcher=MATCHER).execute()
        storage.write_atomic("data/filtered.json", storage.dumps([]))
        storage.write_atomic("data/fetch-all-local/himalayas.json", storage.dumps(
            [dict(storage.read_records("data/fetch-all/greenhouse.json")[0],
                  identity="himalayas:1", source="himalayas",
                  board_id="himalayas:browse")]))

        log = Run([GH], client_for({"careem": gh_payload(["AI Engineer"])}),
                  now=NOW, matcher=MATCHER).execute()
        public = [r["source"] for r in storage.read_records("data/filtered.json")]
        self.assertNotIn("himalayas", public)
        self.assertEqual(log["totals"]["backfilled_local"], 1)


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
                     run_module.load_boards, run_module.HttpClient,
                     run_module.make_airtable_client, run_module.read_private_stores)
        storage.REPO_ROOT = self.dir
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.payload = gh_payload(["AI Engineer"])
        run_module.load_boards = lambda: [GH]
        run_module.HttpClient = lambda **kw: client_for({"careem": self.payload})
        # A committing run now projects. No test may reach a live base, so the
        # client is a fake that records what it is given, and the private
        # store is an empty reachable one.
        self.airtable = []
        self.airtable_asked = []

        def fake_client(test_mode, used_this_month):
            self.airtable_asked.append((test_mode, used_this_month))
            client = FakeAirtable()
            self.airtable.append(client)
            return client
        run_module.make_airtable_client = fake_client
        run_module.read_private_stores = lambda: []

    def tearDown(self):
        (storage.REPO_ROOT, storage.commit_files, storage.restore_from_branch,
         run_module.load_boards, run_module.HttpClient,
         run_module.make_airtable_client, run_module.read_private_stores) = self.real
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

    # ------------------------------------------------------------ projection
    def test_a_committing_run_projects_and_logs_what_it_sent(self):
        code, out, _ = self.main()
        self.assertEqual(code, EXIT_OK)
        sent = self.airtable[0].sent
        self.assertEqual([r["Identity"] for r in sent], ["greenhouse:1000"])
        log = self.last_run_log()
        self.assertEqual(log["airtable"]["rows_sent"], 1)
        self.assertIsNone(log["airtable"]["failure"])
        self.assertEqual(log["projection"]["groups"], 1)
        self.assertIn("projection:", out)
        on_branch = json.loads(self.on_branch("data", "logs-runs/%s"
                                              % sorted(os.listdir("data/logs-runs"))[-1]))
        self.assertIn("airtable", on_branch, "the committed log lacks the airtable block")

    def test_a_failed_projection_still_commits_and_exits_2(self):
        """The operator's decision of 2026-09-23: exit 1 would stop the push
        and lose the fetch for a display failure. ADR-0040 re-projects every
        run, so the failure is resumable."""
        def refuse(test_mode, used_this_month):
            raise AirtableConfigError("empty or unset: AIRTABLE_TOKEN")
        run_module.make_airtable_client = refuse
        code, _, err = self.main()
        self.assertEqual(code, EXIT_STOPPED_RESUMABLE)
        self.assertIn("projection to Airtable failed", err)
        self.assertEqual(self.identities("data"), ["greenhouse:1000"],
                         "the fetch was not committed")
        self.assertIn("AIRTABLE_TOKEN", self.last_run_log()["airtable"]["failure"])

    def test_an_unreachable_private_store_fails_the_projection_visibly(self):
        """ADR-0047's rule: a store the run cannot reach fails the run and
        says so, rather than projecting as though it held nothing."""
        def unreachable():
            raise storage.PrivateStoreUnreachable("the private store could not be reached")
        run_module.read_private_stores = unreachable
        code, _, _ = self.main()
        self.assertEqual(code, EXIT_STOPPED_RESUMABLE)
        self.assertEqual(self.airtable[0].sent, [], "projected without the private stores")
        self.assertIn("could not be reached", self.last_run_log()["airtable"]["failure"])

    def test_a_failure_quoting_a_secret_is_scrubbed_before_it_is_logged(self):
        """The run log is committed to a public branch. The case built to
        defeat the clients' own discipline: an exception that quotes every
        secret the run holds."""
        secrets = {name: "SECRET-VALUE-%d-xyz" % i
                   for i, name in enumerate(run_module.SECRET_ENVS)}
        saved = {name: os.environ.get(name) for name in secrets}
        os.environ.update(secrets)
        try:
            def leak(test_mode, used_this_month):
                raise RuntimeError("boom " + " ".join(secrets.values()))
            run_module.make_airtable_client = leak
            code, out, err = self.main()
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.assertEqual(code, EXIT_STOPPED_RESUMABLE)
        committed = self.on_branch("data", "logs-runs/%s"
                                   % sorted(os.listdir("data/logs-runs"))[-1])
        for value in secrets.values():
            for text, where in ((committed, "the committed run log"), (out, "stdout"),
                                (err, "stderr")):
                self.assertNotIn(value, text, "a secret reached %s" % where)

    def test_a_no_commit_run_reaches_no_base_and_no_private_store(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("a no-commit run reached for a live service")
        run_module.make_airtable_client = forbidden
        run_module.read_private_stores = forbidden
        code, _, _ = self.main("--no-commit")
        self.assertEqual(code, EXIT_OK)
        log = self.last_run_log()
        self.assertIn("dry run", log["projection"]["mode"])
        self.assertEqual(log["projection"]["rows_to_send"], 1)
        self.assertEqual(log["airtable"]["calls_used"], 0)
        self.assertIsNone(log["airtable"]["failure"])

    def test_test_mode_asks_for_the_test_table(self):
        self.main("--test-mode")
        self.assertEqual(self.airtable_asked[0][0], True)
        self.main()
        self.assertEqual(self.airtable_asked[1][0], False)

    def test_the_month_so_far_reaches_the_next_runs_client(self):
        """ADR-0034: a budget counted per month. A runner restores no run
        logs, so the count must come back from the branch."""
        self.main()
        self.fresh_machine()
        self.main()
        self.assertEqual(self.airtable_asked[0][1], 0)
        self.assertEqual(self.airtable_asked[1][1], FakeAirtable.CALLS)

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
