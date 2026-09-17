"""The title pool report, tested from ADR-0021.

The record makes the pool a versioned file whose changes are documented acts,
forbids bare single tokens outside the exempt list, and credits every
admission to one named term. The report must measure exactly that, and its
preview must refuse any candidate the pool itself would refuse.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import storage
from src.filters import FilterError, TitleMatcher
from src.normalise import dumps

_spec = importlib.util.spec_from_file_location(
    "title_pool_report", os.path.join(ROOT, "tools", "title_pool_report.py"))
pool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pool)

MATCHER = TitleMatcher()


def posting(title, board="greenhouse:careem", n=0):
    return {"identity": "%s:%d:%s" % (board, n, title), "title": title,
            "title_normalised": title, "board_id": board, "source": board.split(":")[0]}


ROWS = [posting("AI Engineer"), posting("Senior AI Engineer", n=1),
        posting("AI Platform Engineer", n=2),
        posting("Software Engineer, Platform", "greenhouse:speechify", 3),
        posting("Software Engineer, Platform", "greenhouse:speechify", 4),
        posting("Storage Engineer", n=5)]


class TestMeasure(unittest.TestCase):
    def test_credit_goes_to_the_first_matching_term_and_matches_count_every_term(self):
        """"AI Platform Engineer" does not contain `ai engineer` as
        consecutive words, so the first term it matches is `ai platform`."""
        r = pool.measure(ROWS, MATCHER)
        self.assertEqual(r["credited"]["ai engineer"], 2)
        self.assertEqual(r["credited"]["ai platform"], 1)
        self.assertEqual(r["matches"]["ai platform"], 1)
        self.assertEqual(r["credited"]["software engineer"], 2, "pool version 3")
        self.assertEqual(len(r["admitted"]), 5)
        self.assertEqual([x["title"] for x in r["dropped"]], ["Storage Engineer"])

    def test_a_term_matched_but_never_credited_is_not_a_zero(self):
        """`mlops` on 2026-09-17: it matched a posting that `machine learning`
        was credited with. It is not dead, and must not be listed as such."""
        rows = [posting("Machine Learning Engineer (MLOps)")]
        r = pool.measure(rows, MATCHER)
        self.assertEqual(r["credited"]["machine learning"], 1)
        self.assertEqual(r["credited"]["mlops"], 0)
        self.assertEqual(r["matches"]["mlops"], 1)
        self.assertNotIn("mlops", r["zero"])
        self.assertIn("nlp", r["zero"])

    def test_zero_lists_follow_pool_order(self):
        r = pool.measure(ROWS, MATCHER)
        self.assertEqual(r["zero"], [t for t in MATCHER.terms if t in r["zero"]])
        self.assertNotIn("ai engineer", r["zero"])


class TestTry(unittest.TestCase):
    def test_a_candidate_reports_only_what_the_pool_drops_today(self):
        t = pool.try_term("platform engineer", ROWS, MATCHER)
        self.assertEqual(t["matches"], 1, "AI Platform Engineer")
        self.assertEqual(t["new"], [], "it is already admitted by `ai platform`")

    def test_a_candidate_is_normalised_exactly_as_the_pool_is(self):
        t = pool.try_term("Storage-Engineer", ROWS, MATCHER)
        self.assertEqual(t["term"], "storage engineer")
        self.assertEqual(len(t["new"]), 1)

    def test_a_candidate_matches_on_word_boundaries(self):
        t = pool.try_term("storage engineer", ROWS, MATCHER)
        self.assertEqual(len(t["new"]), 1)
        self.assertEqual(pool.try_term("age engineer", ROWS, MATCHER)["matches"], 0,
                         "substring matching would find 'age engineer' inside 'Storage Engineer'")

    def test_a_bare_token_is_refused_as_the_pool_would(self):
        """ADR-0021: `ai` and `rag` never stand alone."""
        for token in ("rag", "ai", "python"):
            with self.assertRaises(FilterError):
                pool.try_term(token, ROWS, MATCHER)

    def test_an_exempt_token_is_allowed(self):
        self.assertEqual(pool.try_term("llm", ROWS, MATCHER)["term"], "llm")

    def test_an_existing_term_is_flagged(self):
        self.assertEqual(pool.try_term("AI Engineer", ROWS, MATCHER)["already"], ["ai engineer"])

    def test_the_preview_groups_titles_with_their_boards(self):
        lines = pool.titles_table(ROWS[3:5], 5)
        self.assertEqual(lines, ["       2  Software Engineer, Platform  [greenhouse:speechify 2]"])


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
            code = pool.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_only_raw_files_on_the_branch_are_read(self):
        storage.commit_files({"fetch-all/greenhouse.json": dumps(ROWS[:3]),
                              "fetch-all/lever.json": dumps([posting("AI Engineer", "lever:x", 9)]),
                              "filtered.json": dumps([posting("Must Not Be Read", n=99)])},
                             "run", branch="data")
        rows = pool.postings_from_branch(self.dir, "data")
        self.assertEqual(len(rows), 4)
        self.assertNotIn("Must Not Be Read", [r["title"] for r in rows])

    def test_the_cli_reports_and_previews(self):
        storage.commit_files({"fetch-all/greenhouse.json": dumps(ROWS)}, "run", branch="data")
        code, out, _ = self.run_tool("--repo", self.dir, "--try", "storage engineer",
                                     "--try", "software engineer", "--dropped")
        self.assertEqual(code, 0)
        self.assertIn("Title pool against 6 postings", out)
        self.assertIn("Candidate `storage engineer`: matches 1, of which 1 are dropped today", out)
        self.assertIn("Candidate `software engineer`: matches 2, of which 0 are dropped today", out)
        self.assertIn("already in the pool", out)
        self.assertIn("Every dropped title:", out)
        self.assertIn("Storage Engineer", out)

    def test_a_refused_candidate_fails_the_command(self):
        storage.commit_files({"fetch-all/greenhouse.json": dumps(ROWS)}, "run", branch="data")
        code, out, err = self.run_tool("--repo", self.dir, "--try", "rag")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("ADR-0021", err)

    def test_a_missing_branch_says_how_to_fetch_it(self):
        code, _, err = self.run_tool("--repo", self.dir)
        self.assertEqual(code, 1)
        self.assertIn("git fetch origin data:data", err)

    def test_a_local_directory_includes_aggregator_raw_files(self):
        root = os.path.join(self.dir, "d")
        storage.write_atomic(os.path.join(root, "fetch-all", "greenhouse.json"), dumps(ROWS[:1]))
        storage.write_atomic(os.path.join(root, "fetch-all-local", "himalayas.json"),
                             dumps([posting("Data Scientist", "himalayas:browse", 7)]))
        code, out, _ = self.run_tool("--dir", root)
        self.assertEqual(code, 0)
        self.assertIn("Title pool against 2 postings", out)
        self.assertRegex(out, r"data scientist\s+1\s+1")

    def test_another_pool_file_can_be_measured(self):
        """How a candidate version is judged before it replaces the pool."""
        storage.commit_files({"fetch-all/greenhouse.json": dumps(ROWS)}, "run", branch="data")
        candidate = os.path.join(self.dir, "candidate.md")
        with open(candidate, "w", encoding="utf-8") as f:
            f.write("Exempt single tokens: `llm`\n\n## Terms\n\n`software engineer`\n\n## Known behaviour\n")
        code, out, _ = self.run_tool("--repo", self.dir, "--pool", candidate)
        self.assertEqual(code, 0)
        self.assertIn("2 admitted, 4 dropped, 0 of 1 terms match nothing", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
