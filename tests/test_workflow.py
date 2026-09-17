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

from src import storage

WORKFLOW = os.path.join(ROOT, ".github", "workflows", "fetch.yml")


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

    def test_exit_1_is_not_labelled_as_could_not_start(self):
        """Run 35179218050 failed at the commit after a full fetch and the
        workflow announced that the run could not start."""
        self.assertNotIn("::error::the run could not start", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
