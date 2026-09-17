"""The run-log reader, tested from ADR-0028's Confirmation.

The record asks for requests per source and per run over the first month, the
observed distribution, and whether the ceiling is hit routinely. It sets no
ceiling of its own, so neither does the reader. The run logs also exist so a
board that has gone silent is visible (CLAUDE.md), which the reader reports
without a threshold, because none is decided.
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
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import storage
from src.config import Board
from src.filters import TitleMatcher
from src.http_client import HttpClient
from src.normalise import dumps
from src.run import Run

_spec = importlib.util.spec_from_file_location(
    "run_log_report", os.path.join(ROOT, "tools", "run_log_report.py"))
report_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report_tool)


def log(when, used, by_source, boards=(), test_mode=False, budget=500, circuit=False,
        retries=0, failures=0):
    """A run log in the shape src/run.py writes. The integration test below
    holds that shape to the real writer."""
    return {"run_at": when, "test_mode": test_mode, "stopped": None,
            "requests": {"requests_used": used, "budget": budget,
                         "budget_remaining": budget - used, "by_source": by_source,
                         "retries": retries, "failures": failures, "refused": 0,
                         "circuit_open": circuit},
            "boards": [dict({"fetched": 0, "new": 0, "status": "ok"}, board=b, **v)
                       for b, v in boards],
            "totals": {}}


def texts(*logs):
    return [("%02d.json" % i, json.dumps(l)) for i, l in enumerate(logs)]


def summary(*logs, test_mode=False, since=None):
    runs, problems = report_tool.parse(texts(*logs), test_mode, since)
    return report_tool.summarise(runs), problems


GH = ("greenhouse:careem", {"fetched": 20, "new": 0})
GH_FIRST = ("greenhouse:careem", {"fetched": 20, "new": 20})
HM_FIRST = ("himalayas:browse", {"fetched": 500, "new": 500})
HM = ("himalayas:browse", {"fetched": 20, "new": 3})


class TestDistribution(unittest.TestCase):
    def test_requests_per_run_are_spread_rather_than_averaged(self):
        """The record asks for the observed distribution. 11, 36, 12, 12 were
        the slice's measured runs; a mean alone would hide the 36."""
        s, _ = summary(log("2026-09-17T00:00:00Z", 11, {"greenhouse": 11}),
                       log("2026-09-17T13:00:00Z", 36, {"greenhouse": 11, "himalayas": 25}),
                       log("2026-09-18T00:00:00Z", 12, {"greenhouse": 11, "himalayas": 1}),
                       log("2026-09-18T13:00:00Z", 12, {"greenhouse": 11, "himalayas": 1}))
        self.assertEqual(s["per_run"], {"n": 4, "min": 11, "median": 12, "p90": 36, "max": 36})

    def test_each_source_has_its_own_spread_and_count(self):
        """The first run never reached Himalayas: its board line is there,
        marked not reached, and the source made no requests. That run says
        nothing about Himalayas' need, so it is not a zero in its spread."""
        s, _ = summary(log("2026-09-17T00:00:00Z", 11, {"greenhouse": 11},
                           [("himalayas:browse", {"status": "not reached"})]),
                       log("2026-09-17T13:00:00Z", 36, {"greenhouse": 11, "himalayas": 25}),
                       log("2026-09-18T00:00:00Z", 12, {"greenhouse": 11, "himalayas": 1}))
        self.assertEqual(s["sources"]["greenhouse"]["n"], 3)
        self.assertEqual(s["sources"]["himalayas"]["n"], 2,
                         "a run without the source is not a zero for it")
        self.assertEqual((s["sources"]["himalayas"]["min"], s["sources"]["himalayas"]["max"]),
                         (1, 25))

    def test_the_percentile_is_an_observed_value(self):
        self.assertEqual(report_tool.nearest_rank([1, 2, 3, 4, 100], 0.9), 100)
        self.assertEqual(report_tool.nearest_rank([7], 0.9), 7)
        self.assertEqual(report_tool.nearest_rank(list(range(1, 11)), 0.9), 9)

    def test_the_span_is_measured_from_the_runs_not_the_files(self):
        """Runs are ordered by their own clock. File order is not evidence."""
        s, _ = summary(log("2026-10-17T00:00:00Z", 12, {"greenhouse": 12}),
                       log("2026-09-17T00:00:00Z", 12, {"greenhouse": 12}))
        self.assertEqual(s["span_days"], 30.0)
        self.assertEqual(s["first"], datetime(2026, 9, 17, tzinfo=timezone.utc))


class TestFirstContact(unittest.TestCase):
    def test_a_run_where_every_posting_was_new_is_counted_per_source(self):
        s, _ = summary(log("2026-09-17T00:00:00Z", 26, {"greenhouse": 1, "himalayas": 25},
                           [GH_FIRST, HM_FIRST]),
                       log("2026-09-17T13:00:00Z", 2, {"greenhouse": 1, "himalayas": 1},
                           [GH, HM]))
        self.assertEqual(s["sources"]["greenhouse"]["first_contact"], 1)
        self.assertEqual(s["sources"]["himalayas"]["first_contact"], 1)

    def test_a_source_that_is_new_every_run_is_flagged(self):
        """What Himalayas does on a runner that keeps no aggregator state."""
        s, _ = summary(log("2026-09-17T00:00:00Z", 26, {"greenhouse": 1, "himalayas": 25},
                           [GH_FIRST, HM_FIRST]),
                       log("2026-09-17T13:00:00Z", 26, {"greenhouse": 1, "himalayas": 25},
                           [GH, HM_FIRST]))
        self.assertEqual(s["sources"]["himalayas"]["first_contact"], 2)
        text = report_tool.render(s, "x", {})
        himalayas_line = [l for l in text.splitlines() if l.strip().startswith("himalayas")][0]
        greenhouse_line = [l for l in text.splitlines() if l.strip().startswith("greenhouse")][0]
        self.assertIn("every run", himalayas_line)
        self.assertNotIn("every run", greenhouse_line)

    def test_a_board_that_fetched_nothing_is_not_first_contact(self):
        s, _ = summary(log("2026-09-17T00:00:00Z", 1, {"greenhouse": 1},
                           [("greenhouse:careem", {"fetched": 0, "new": 0})]))
        self.assertEqual(s["sources"]["greenhouse"]["first_contact"], 0)


class TestStops(unittest.TestCase):
    def test_a_run_that_used_the_whole_budget_is_a_ceiling_hit(self):
        """ADR-0028: a ceiling hit routinely means something is wrong."""
        s, _ = summary(log("2026-09-17T00:00:00Z", 500, {"workday": 500}),
                       log("2026-09-17T13:00:00Z", 499, {"workday": 499}))
        self.assertEqual(s["stopped"]["ceiling"], ["00.json"])

    def test_a_run_that_ended_with_the_circuit_open_is_counted(self):
        s, _ = summary(log("2026-09-17T00:00:00Z", 5, {"lever": 5}, circuit=True),
                       log("2026-09-17T13:00:00Z", 5, {"lever": 5}))
        self.assertEqual(s["stopped"]["circuit"], ["00.json"])
        self.assertEqual(s["stopped"]["ceiling"], [])

    def test_boards_not_reached_and_retries_are_totalled(self):
        s, _ = summary(log("2026-09-17T00:00:00Z", 5, {"lever": 5}, retries=2, failures=1,
                           boards=[("lever:a", {"status": "not reached"}),
                                   ("lever:b", {"status": "not reached"})]),
                       log("2026-09-17T13:00:00Z", 5, {"lever": 5}, retries=1))
        self.assertEqual(s["stopped"]["not reached"], 2)
        self.assertEqual((s["retries"], s["failures"]), (3, 1))


class TestQuietBoards(unittest.TestCase):
    def test_a_board_silent_in_its_latest_runs_is_listed_with_its_streak(self):
        s, _ = summary(
            log("2026-09-17T00:00:00Z", 2, {"greenhouse": 2},
                [("greenhouse:a", {"fetched": 5}), ("greenhouse:b", {"fetched": 5})]),
            log("2026-09-18T00:00:00Z", 2, {"greenhouse": 2},
                [("greenhouse:a", {"fetched": 0}), ("greenhouse:b", {"fetched": 5})]),
            log("2026-09-19T00:00:00Z", 2, {"greenhouse": 2},
                [("greenhouse:a", {"fetched": 0, "status": "failed"}),
                 ("greenhouse:b", {"fetched": 5})]))
        self.assertEqual([q["board"] for q in s["quiet"]], ["greenhouse:a"])
        q = s["quiet"][0]
        self.assertEqual((q["runs"], q["days"]), (2, 1.0))
        self.assertEqual(q["statuses"], ["failed", "ok"])

    def test_a_board_that_recovered_is_not_listed(self):
        s, _ = summary(
            log("2026-09-17T00:00:00Z", 1, {"greenhouse": 1}, [("greenhouse:a", {"fetched": 0})]),
            log("2026-09-18T00:00:00Z", 1, {"greenhouse": 1}, [("greenhouse:a", {"fetched": 3})]))
        self.assertEqual(s["quiet"], [])

    def test_an_ok_status_with_nothing_fetched_still_counts_as_silent(self):
        """The case the per-board zero exists for: nothing is wrong on the
        wire, and nothing arrives."""
        s, _ = summary(log("2026-09-17T00:00:00Z", 1, {"greenhouse": 1},
                           [("greenhouse:a", {"fetched": 0, "status": "ok"})]))
        self.assertEqual([q["board"] for q in s["quiet"]], ["greenhouse:a"])


class TestWhatIsCounted(unittest.TestCase):
    def test_test_runs_are_not_production_evidence(self):
        """Before 2026-09-17 a test run committed to the production branch."""
        runs, problems = report_tool.parse(texts(
            log("2026-09-17T00:00:00Z", 12, {"greenhouse": 12}),
            log("2026-09-17T13:00:00Z", 99, {"greenhouse": 99}, test_mode=True)), False)
        self.assertEqual([r["requests"]["requests_used"] for r in runs], [12])
        self.assertEqual(problems["other mode"], ["01.json"])

    def test_test_mode_reads_only_test_runs(self):
        runs, problems = report_tool.parse(texts(
            log("2026-09-17T00:00:00Z", 12, {"greenhouse": 12}),
            log("2026-09-17T13:00:00Z", 99, {"greenhouse": 99}, test_mode=True)), True)
        self.assertEqual([r["requests"]["requests_used"] for r in runs], [99])
        self.assertEqual(problems["other mode"], ["00.json"])

    def test_a_broken_log_is_reported_not_fatal(self):
        named = texts(log("2026-09-17T00:00:00Z", 12, {"greenhouse": 12}))
        named += [("bad.json", "{not json"), ("short.json", json.dumps({"run_at": "x"}))]
        runs, problems = report_tool.parse(named, False)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(problems["unreadable"]), 2)

    def test_since_drops_earlier_runs(self):
        runs, problems = report_tool.parse(texts(
            log("2026-09-17T00:00:00Z", 36, {"himalayas": 36}),
            log("2026-10-01T00:00:00Z", 12, {"greenhouse": 12})), False, date(2026, 10, 1))
        self.assertEqual([r["requests"]["requests_used"] for r in runs], [12])
        self.assertEqual(problems["before since"], ["00.json"])


class TestReadingTheBranch(unittest.TestCase):
    """Against a throwaway repository, the way the data branch is written."""

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
            code = report_tool.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_only_run_logs_are_read_from_the_branch(self):
        storage.commit_files({
            "logs-runs/20260917T000000Z.json": dumps(log("2026-09-17T00:00:00Z", 11, {"greenhouse": 11})),
            "logs-runs/20260917T130000Z.json": dumps(log("2026-09-17T13:00:00Z", 13, {"greenhouse": 13})),
            "seen.json": dumps({"greenhouse:1": {"source": "greenhouse"}}),
            "filtered.json": dumps([]),
        }, "run", branch="data")
        logs = report_tool.logs_from_branch(self.dir, "data")
        self.assertEqual([name for name, _ in logs],
                         ["logs-runs/20260917T000000Z.json", "logs-runs/20260917T130000Z.json"])
        self.assertEqual(json.loads(logs[1][1])["requests"]["requests_used"], 13)

    def test_non_ascii_log_text_survives_the_batch_read(self):
        entry = log("2026-09-17T00:00:00Z", 1, {"greenhouse": 1})
        entry["boards"] = [{"board": "greenhouse:careem", "fetched": 1, "new": 1,
                            "status": "error", "detail": "Ingénieur データ"}]
        storage.commit_files({"logs-runs/a.json": dumps(entry),
                              "logs-runs/b.json": dumps(log("2026-09-17T13:00:00Z", 2, {"greenhouse": 2}))},
                             "run", branch="data")
        logs = report_tool.logs_from_branch(self.dir, "data")
        self.assertEqual(json.loads(logs[0][1])["boards"][0]["detail"], "Ingénieur データ")
        self.assertEqual(json.loads(logs[1][1])["requests"]["requests_used"], 2,
                         "the second object was misread after a multi-byte first one")

    def test_the_default_reads_production_and_the_flag_reads_test(self):
        storage.commit_files({"logs-runs/p.json": dumps(log("2026-09-17T00:00:00Z", 12, {"greenhouse": 12}))},
                             "run", branch="data")
        storage.commit_files({"logs-runs/t.json": dumps(log("2026-09-17T00:00:00Z", 7, {"greenhouse": 7},
                                                            test_mode=True))},
                             "run", branch="data-test")
        code, out, _ = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 0)
        self.assertIn("the data branch", out)
        self.assertRegex(out, r"all sources\s+1\s+12\s")
        code, out, _ = self.run_tool("--repo", self.dir, "--test-mode")
        self.assertEqual(code, 0)
        self.assertIn("the data-test branch", out)
        self.assertRegex(out, r"all sources\s+1\s+7\s")

    def test_a_missing_branch_says_how_to_fetch_it(self):
        code, out, err = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("git fetch origin data:data", err)

    def test_nothing_countable_is_a_failure_not_an_empty_report(self):
        storage.commit_files({"logs-runs/t.json": dumps(log("2026-09-17T00:00:00Z", 7, {"greenhouse": 7},
                                                            test_mode=True))},
                             "run", branch="data")
        code, out, err = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("other mode: 1", err)


class TestAgainstTheRealWriter(unittest.TestCase):
    """The reader and src/run.py must agree on the log's shape. A reader
    tested only against hand-built logs would pass while the writer moved."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_a_log_written_by_a_run_is_read_back(self):
        page = {"jobs": [{"id": 1, "title": "AI Engineer", "absolute_url": "https://b.test/1",
                          "first_published": "2026-09-10T05:00:00+00:00",
                          "company_name": "Careem", "location": {"name": "Karachi"}}]}

        class Session:
            def get(self, url, params=None, timeout=None, headers=None):
                class R:
                    status_code = 200
                    headers = {}

                    def json(self):
                        return page
                return R()

        written = []
        for hour in (0, 13):
            client = HttpClient(session=Session(), sleep=lambda s: None, min_interval=0)
            now = datetime(2026, 9, 17, hour, tzinfo=timezone.utc)
            written.append(Run([Board(platform="greenhouse", slug="careem")], client,
                               now=now, matcher=TitleMatcher()).execute())
        runs, problems = report_tool.parse(texts(*written), False)
        self.assertEqual(problems["unreadable"], [])
        s = report_tool.summarise(runs)
        self.assertEqual(s["per_run"]["n"], 2)
        self.assertEqual(s["sources"]["greenhouse"]["first_contact"], 1,
                         "only the first run saw every posting as new")


if __name__ == "__main__":
    unittest.main(verbosity=2)
