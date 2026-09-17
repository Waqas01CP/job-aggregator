"""The publication-lag report, tested from the question it answers.

STATE.md: Lever's createdAt meaning "settles from the pipeline's own data
once it runs twice: a posting first seen in a run whose createdAt predates
the previous run's clock is the proof." So a posting counts only if it was
first seen after the first run, and it is compared with the run immediately
before the one that first saw it.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import storage
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.normalise import dumps
from src.run import Run

_spec = importlib.util.spec_from_file_location(
    "publication_lag_report", os.path.join(ROOT, "tools", "publication_lag_report.py"))
lag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lag)

R1, R2, R3 = "2026-09-17T00:00:00Z", "2026-09-17T13:00:00Z", "2026-09-18T00:00:00Z"
RUNS = [lag.when(t) for t in (R1, R2, R3)]


def entry(first_seen, published, source="lever"):
    return {"first_seen": first_seen, "published_at": published, "source": source,
            "last_seen": first_seen}


def run_log(at, test_mode=False):
    return {"run_at": at, "test_mode": test_mode, "stopped": None, "boards": [],
            "requests": {"requests_used": 1, "budget": 500, "by_source": {}}}


class TestAnalysis(unittest.TestCase):
    def test_postings_from_the_first_run_are_not_evidence(self):
        r = lag.analyse({"lever:a": entry(R1, "2020-01-01T00:00:00Z")}, RUNS)
        self.assertEqual(r["lever"]["first_run"], 1)
        self.assertEqual(r["lever"]["before"], [])
        self.assertEqual(r["lever"]["after"], 0)

    def test_a_posting_dated_after_the_run_before_is_consistent(self):
        r = lag.analyse({"lever:a": entry(R2, "2026-09-17T05:00:00Z")}, RUNS)
        self.assertEqual(r["lever"]["after"], 1)
        self.assertEqual(r["lever"]["before"], [])

    def test_a_posting_dated_before_the_run_that_missed_it_is_reported_with_its_gap(self):
        r = lag.analyse({"lever:a": entry(R2, "2026-09-16T22:00:00Z")}, RUNS)
        self.assertEqual(r["lever"]["after"], 0)
        [b] = r["lever"]["before"]
        self.assertEqual(b["hours"], 2.0)
        self.assertEqual(b["previous_run"], lag.when(R1))

    def test_a_date_exactly_at_the_previous_run_counts_as_before(self):
        """That run looked at that instant and did not see it."""
        r = lag.analyse({"lever:a": entry(R2, R1)}, RUNS)
        self.assertEqual(len(r["lever"]["before"]), 1)

    def test_the_comparison_is_with_the_run_immediately_before(self):
        """Dated between run 1 and run 2, first seen in run 3: run 2 missed it."""
        r = lag.analyse({"lever:a": entry(R3, "2026-09-17T06:00:00Z")}, RUNS)
        [b] = r["lever"]["before"]
        self.assertEqual(b["previous_run"], lag.when(R2))
        self.assertEqual(b["hours"], 7.0)

    def test_a_run_that_found_nothing_is_still_the_run_before(self):
        """Run 2 added no posting, so no first-seen value names it. It still
        looked, so a posting dated before it and first seen in run 3 was
        missed by run 2, not by run 1."""
        seen = {"lever:old": entry(R1, "2026-09-10T00:00:00Z"),
                "lever:new": entry(R3, "2026-09-17T06:00:00Z")}
        r = lag.analyse(seen, RUNS)
        self.assertEqual(r["lever"]["before"][0]["previous_run"], lag.when(R2))

    def test_a_posting_without_a_date_is_counted_apart(self):
        r = lag.analyse({"manatal:a": entry(R2, None, "manatal")}, RUNS)
        self.assertEqual(r["manatal"]["no_date"], 1)
        self.assertEqual(r["manatal"]["after"], 0)

    def test_a_first_sighting_that_matches_no_run_is_unmatched(self):
        r = lag.analyse({"lever:a": entry("2026-09-17T06:00:00Z", "2026-09-17T05:00:00Z"),
                         "lever:b": entry(None, "2026-09-17T05:00:00Z")}, RUNS)
        self.assertEqual(r["lever"]["unmatched"], 2)

    def test_sources_are_reported_separately(self):
        r = lag.analyse({"lever:a": entry(R2, "2026-09-16T00:00:00Z"),
                         "greenhouse:b": entry(R2, "2026-09-17T05:00:00Z", "greenhouse")}, RUNS)
        self.assertEqual((len(r["lever"]["before"]), r["lever"]["after"]), (1, 0))
        self.assertEqual((len(r["greenhouse"]["before"]), r["greenhouse"]["after"]), (0, 1))

    def test_the_rendered_report_names_the_late_posting_and_its_gap(self):
        r = lag.analyse({"lever:late": entry(R2, "2026-09-16T22:00:00Z")}, RUNS)
        text = lag.render(r, RUNS, "x", {})
        self.assertIn("lever:late", text)
        self.assertIn("min 2.0, median 2.0, max 2.0", text)
        self.assertRegex(text, r"lever\s+0\s+1\s+0\s+1\s+0\s+0")


class TestReading(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.real_root = storage.REPO_ROOT
        storage.REPO_ROOT = self.dir
        subprocess.run(["git", "init", "-q"], cwd=self.dir)

    def tearDown(self):
        storage.REPO_ROOT = self.real_root
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = lag.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_the_branch_seen_store_and_run_logs_are_read(self):
        storage.commit_files({
            "seen.json": dumps({"lever:a": entry(R2, "2026-09-16T22:00:00Z")}),
            "logs-runs/1.json": dumps(run_log(R1)),
            "logs-runs/2.json": dumps(run_log(R2)),
        }, "run", branch="data")
        code, out, _ = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 0)
        self.assertIn("lever:a", out)

    def test_test_mode_reads_the_test_branch_and_its_test_runs(self):
        storage.commit_files({"seen.json": dumps({"lever:a": entry(R2, "2026-09-16T22:00:00Z")}),
                              "logs-runs/1.json": dumps(run_log(R1, test_mode=True)),
                              "logs-runs/2.json": dumps(run_log(R2, test_mode=True))},
                             "run", branch="data-test")
        code, out, _ = self.run_tool("--repo", self.dir, "--test-mode")
        self.assertEqual(code, 0)
        self.assertIn("the data-test branch", out)
        self.assertIn("lever:a", out)

    def test_runs_of_the_other_mode_are_not_counted(self):
        """With the test run left out, run 2 is the first run, so the
        posting it first saw is not evidence."""
        storage.commit_files({"seen.json": dumps({"lever:a": entry(R2, "2026-09-16T22:00:00Z")}),
                              "logs-runs/1.json": dumps(run_log(R1, test_mode=True)),
                              "logs-runs/2.json": dumps(run_log(R2))},
                             "run", branch="data")
        code, out, _ = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 0)
        self.assertNotIn("lever:a", out)
        self.assertIn("other mode: 1", out)

    def test_a_missing_branch_says_how_to_fetch_it(self):
        code, out, err = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("git fetch origin data:data", err)

    def test_a_local_directory_includes_the_local_only_seen_store(self):
        """Aggregator entries never reach a branch, so a local reading is the
        only place their lag can be measured."""
        root = os.path.join(self.dir, "d")
        storage.write_atomic(os.path.join(root, "seen.json"),
                             dumps({"lever:a": entry(R1, "2026-09-16T00:00:00Z")}))
        storage.write_atomic(os.path.join(root, "local", "seen.json"),
                             dumps({"himalayas:h": entry(R2, "2026-09-16T23:00:00Z", "himalayas")}))
        storage.write_atomic(os.path.join(root, "logs-runs", "1.json"), dumps(run_log(R1)))
        storage.write_atomic(os.path.join(root, "logs-runs", "2.json"), dumps(run_log(R2)))
        code, out, _ = self.run_tool("--dir", root)
        self.assertEqual(code, 0)
        self.assertIn("himalayas:h", out)


class TestAgainstTheRealWriter(unittest.TestCase):
    """Two real runs: the second sees a Lever posting dated before the first
    ran. The report must find it, which holds the tool to the writer's
    first_seen and run_at formats."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_posting_the_first_run_missed_is_found(self):
        created_ms = int(datetime(2026, 9, 16, 22, tzinfo=timezone.utc).timestamp() * 1000)
        pages = [[], [{"id": "lv1", "text": "AI Engineer",
                       "hostedUrl": "https://jobs.lever.co/spreetail/lv1",
                       "createdAt": created_ms, "categories": {"location": "Karachi"}}]]
        logs = []
        for i, now in enumerate((datetime(2026, 9, 17, 0, tzinfo=timezone.utc),
                                 datetime(2026, 9, 17, 13, tzinfo=timezone.utc))):
            body = pages[i]

            class Session:
                def get(self, url, params=None, timeout=None, headers=None):
                    class R:
                        status_code = 200
                        headers = {}

                        def json(self):
                            return body
                    return R()

            client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
            board = Board(platform="lever", slug="spreetail", employer_alias="Spreetail")
            logs.append(Run([board], client, now=now, matcher=TitleMatcher()).execute())

        with open("data/seen.json", encoding="utf-8") as f:
            seen = json.load(f)
        runs = [lag.when(l["run_at"]) for l in logs]
        r = lag.analyse(seen, runs)
        [b] = r["lever"]["before"]
        self.assertEqual(b["identity"], "lever:lv1")
        self.assertEqual(b["hours"], 2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
