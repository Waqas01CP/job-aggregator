"""ADR-0020's guard over the cassettes (Brief 20, decision 2): every committed
aggregator cassette is made up, and the guard refuses a real one."""

import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import aggregator_cassettes  # noqa: E402

CASSETTES = os.path.join(ROOT, "tests", "cassettes")


class TestAggregatorCassettes(unittest.TestCase):
    def test_every_committed_aggregator_cassette_is_made_up(self):
        """So a real response cannot come back by a path the hook does not
        see. Mutation: "the guard passes every cassette"."""
        paths = [os.path.join(CASSETTES, n) for n in sorted(os.listdir(CASSETTES))]
        aggregators = [p for p in paths if aggregator_cassettes.platform_of(p)
                       in aggregator_cassettes.AGGREGATOR_PLATFORMS]
        self.assertEqual(len(aggregators), 10)
        self.assertEqual([line for p in aggregators
                          for line in aggregator_cassettes.problems_in(p)], [])

    def test_a_real_employer_is_refused_and_a_board_cassette_is_not_its_to_judge(self):
        """The case built to defeat it: one posting given a real-looking
        employer. Mutation: "a real employer passes the guard"."""
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        with open(os.path.join(CASSETTES, "jobicy-remote.json"), encoding="utf-8") as f:
            doc = json.load(f)
        doc["jobs"][0]["companyName"] = "Welo Global"
        path = os.path.join(folder, "jobicy-remote.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        self.assertEqual(len(aggregator_cassettes.problems_in(path)), 1)
        self.assertEqual(aggregator_cassettes.main([path]), 1)
        board = os.path.join(CASSETTES, "greenhouse-careem.json")
        self.assertEqual(aggregator_cassettes.problems_in(board), [])

    def test_hasjob_names_no_employer_so_its_links_are_read(self):
        """Mutation: "a real Hasjob link passes the guard"."""
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        with open(os.path.join(CASSETTES, "hasjob-feed.json"), encoding="utf-8") as f:
            doc = json.load(f)
        doc["entries"][0]["link"] = "https://hasjob.co/jobs/1/real-posting"
        path = os.path.join(folder, "hasjob-feed.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        self.assertTrue(aggregator_cassettes.problems_in(path))


if __name__ == "__main__":
    unittest.main()
