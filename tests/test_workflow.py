"""The scheduled workflow and the code must agree.

The workflow is shell inside YAML and nothing here runs it. These checks hold
the two to the same branch names and the same order of steps, which is where
they drifted apart before: the run committed test files to `data` and the
workflow pushed `data`, and neither file alone looked wrong.

Read as text, because the standard library has no YAML parser and the checks
need only a few exact lines.
"""

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import run as run_module
from src import storage

WORKFLOW = os.path.join(ROOT, ".github", "workflows", "fetch.yml")
SECRET_NAMES = ("AIRTABLE_TOKEN", "AIRTABLE_BASE_ID", "AIRTABLE_TABLE_ID",
                "AIRTABLE_TEST_TABLE_ID", "AGGREGATOR_STORE_TOKEN", "AGGREGATOR_STORE_REPO")


def workflow():
    with open(WORKFLOW, encoding="utf-8") as f:
        return f.read()


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.text = workflow()

    def test_the_workflow_names_the_same_branches_as_the_code(self):
        m = re.search(r"DATA_BRANCH:\s*\$\{\{\s*inputs\.test_mode\s*&&\s*'([^']+)'"
                      r"\s*\|\|\s*'([^']+)'\s*\}\}", self.text)
        self.assertIsNotNone(m, "no DATA_BRANCH chosen from test_mode")
        self.assertEqual(m.group(1), storage.data_branch(True))
        self.assertEqual(m.group(2), storage.data_branch(False))

    def test_test_mode_reaches_the_run(self):
        self.assertRegex(self.text, r"TEST_MODE:\s*\$\{\{\s*inputs\.test_mode\s*&&\s*'1'"
                                    r"\s*\|\|\s*'0'\s*\}\}")

    def test_test_mode_is_scoped_to_the_fetch_step_only(self):
        """Set at job level, TEST_MODE also reached the test step, and run
        35236457737 failed seven of its own tests. It must be defined exactly
        once, inside the Fetch step, after the test step."""
        lines = self.text.splitlines()
        defined = [i for i, l in enumerate(lines) if l.strip().startswith("TEST_MODE:")]
        self.assertEqual(len(defined), 1, "TEST_MODE is defined more than once")
        fetch_step = next(i for i, l in enumerate(lines) if l.strip() == "- name: Fetch")
        next_step = next(i for i, l in enumerate(lines)
                         if i > fetch_step and l.strip().startswith("- name:"))
        self.assertTrue(fetch_step < defined[0] < next_step,
                        "TEST_MODE is not set inside the Fetch step")

    def test_git_steps_use_the_chosen_branch_and_never_a_literal_one(self):
        self.assertIn('git fetch --no-tags --depth=1 origin '
                      '"refs/heads/$DATA_BRANCH:refs/heads/$DATA_BRANCH"', self.text)
        self.assertIn('git push origin "refs/heads/$DATA_BRANCH:refs/heads/$DATA_BRANCH"',
                      self.text)
        self.assertNotRegex(self.text, r"git (push|fetch)[^\n]*\bdata(:|\s|$)")

    def test_the_branch_is_fetched_before_the_run_and_pushed_after(self):
        fetch = self.text.index("git fetch --no-tags")
        run = self.text.index("python -m src.run")
        push = self.text.index("git push origin")
        self.assertLess(fetch, run)
        self.assertLess(run, push)

    def test_tests_gate_the_fetch(self):
        self.assertLess(self.text.index("python -m unittest discover"),
                        self.text.index("python -m src.run"))

    def test_no_action_targets_node_20(self):
        """Run 35179218050 warned that checkout@v4 and setup-python@v5 target
        Node 20. Each tag's action.yml was read on 2026-09-17: checkout v5 and
        setup-python v6 are the first majors declaring node24."""
        first_node24 = {"actions/checkout": 5, "actions/setup-python": 6}
        used = re.findall(r"uses:\s*(actions/[\w-]+)@v(\d+)", self.text)
        self.assertEqual(sorted(name for name, _ in used), sorted(first_node24))
        for name, major in used:
            self.assertGreaterEqual(int(major), first_node24[name], name)

    def test_every_secret_reaches_the_fetch_step_and_nothing_else(self):
        """Brief 6: the six secrets go to the Fetch step only. Each must be
        defined exactly once, inside that step, and never at job level or in
        the test step, where a job-level variable once broke run 35236457737."""
        lines = self.text.splitlines()
        fetch_step = next(i for i, l in enumerate(lines) if l.strip() == "- name: Fetch")
        next_step = next(i for i, l in enumerate(lines)
                         if i > fetch_step and l.strip().startswith("- name:"))
        for name in SECRET_NAMES:
            defined = [i for i, l in enumerate(lines)
                       if l.strip() == "%s: ${{ secrets.%s }}" % (name, name)]
            self.assertEqual(len(defined), 1, "%s is not defined exactly once" % name)
            self.assertTrue(fetch_step < defined[0] < next_step,
                            "%s is not set inside the Fetch step" % name)
            mentions = [i for i, l in enumerate(lines) if name in l]
            self.assertEqual(mentions, defined, "%s appears outside its definition" % name)

    def test_the_secret_list_matches_the_code(self):
        """The names the workflow passes are the names the run reads."""
        self.assertEqual(sorted(SECRET_NAMES), sorted(run_module.SECRET_ENVS))

    def test_the_exit_2_warning_names_the_projection(self):
        warning = next(l for l in self.text.splitlines() if "::warning::" in l)
        self.assertIn("projection", warning)
        self.assertIn("budget", warning)
        self.assertIn("breaker", warning)

    def test_exit_1_is_not_labelled_as_could_not_start(self):
        """Run 35179218050 failed at the commit after a full fetch and the
        workflow announced that the run could not start."""
        self.assertNotIn("::error::the run could not start", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
