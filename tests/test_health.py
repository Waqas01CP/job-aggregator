"""The health rows: what becomes one, and that each is sent once. The
operator's decision of 2026-10-07: one table for contract findings and run
failures, written only when something is wrong or new."""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import health

NOW = datetime(2026, 10, 7, 18, 0, tzinfo=timezone.utc)


def contract_log(run_at="2026-10-07T13:46:06Z", **platforms):
    return {"run_at": run_at, "platforms": platforms}


def run_log(run_at="2026-10-07T04:38:28Z", boards=(), **extra):
    return dict({"run_at": run_at, "boards": list(boards)}, **extra)


class TestWhatIsARow(unittest.TestCase):
    def test_a_healthy_check_and_a_healthy_run_are_no_rows(self):
        check = contract_log(lever={"status": "unchanged", "changes": []},
                             manatal={"status": "no board configured"})
        run = run_log(boards=[{"board": "greenhouse:careem", "status": "ok"},
                              {"board": "himalayas:pakistan", "status": "skipped"}],
                      airtable={"failure": None}, sweep={"failure": None})
        self.assertEqual(health.contract_events(check), [])
        self.assertEqual(health.run_events(run), [])

    def test_each_changed_field_is_a_row_and_ours_says_so(self):
        check = contract_log(lever={"status": "changed", "changes": [
            {"in": "posting", "field": "hostedUrl", "was": {"present": "all"},
             "now": {"present": "none"}},
            {"in": "posting", "field": "country", "was": "not in the stored fingerprint",
             "now": {"present": "some"}, "ours": "2026-10-02T20:36:10Z: we read it"}]})
        rows = health.contract_events(check)
        self.assertEqual([(r["Subject"], r["Status"]) for r in rows],
                         [("lever", "changed"), ("lever", "re-baselined")])
        self.assertIn("hostedUrl", rows[0]["Detail"])
        self.assertIn("ours, 2026-10-02T20:36:10Z: we read it", rows[1]["Detail"])
        self.assertEqual(rows[0]["Key"], "contract 2026-10-07T13:46:06Z lever posting.hostedUrl")
        self.assertEqual(rows[0]["When"], "2026-10-07T13:46:06.000Z")
        self.assertEqual(set(rows[0]), set(health.HEALTH_FIELDS))

    def test_a_failed_unreachable_or_new_platform_is_one_row(self):
        check = contract_log(
            greenhouse={"status": "check failed", "detail": "KeyError raised at contract.py:9 in shape"},
            lever={"status": "unreachable", "detail": "503 from the board"},
            manatal={"status": "baseline", "board": "manatal:abacus-consulting-3"})
        rows = {r["Subject"]: r for r in health.contract_events(check)}
        self.assertEqual(rows["greenhouse"]["Status"], "check failed")
        self.assertEqual(rows["lever"]["Detail"], "503 from the board")
        self.assertEqual(rows["manatal"]["Detail"], "manatal:abacus-consulting-3")

    def test_every_failing_part_of_a_run_is_a_row(self):
        run = run_log(boards=[{"board": "greenhouse:careem", "status": "failed", "detail": "500"},
                              {"board": "lever:x", "status": "not reached", "detail": "budget"}],
                      stopped="the budget of 500 was reached",
                      airtable={"failure": "PermanentError: 422"},
                      sweep={"failure": "the read failed"},
                      private_store={"failure": "could not push"},
                      clearing={"failure": "refused: no dry run"},
                      closure_failure="ValueError: bad log",
                      health={"failure": "CallBudgetExhausted"})
        subjects = [(r["Subject"], r["Status"]) for r in health.run_events(run)]
        self.assertEqual(subjects, [
            ("greenhouse:careem", "failed"), ("lever:x", "not reached"), ("fetch", "stopped"),
            ("projection", "failed"), ("sweep", "failed"), ("private store", "failed"),
            ("clearing tool", "failed"), ("closure test", "failed"), ("health", "failed")])


class TestTheWalkAndTheAgreementCheck(unittest.TestCase):
    """The fifth audit's F3: findings that were workflow warnings alone."""

    BOARD = "himalayas:pakistan"

    def _run(self, **board):
        return {"run_at": "2026-11-02T22:13:47Z",
                "boards": [dict(board=self.BOARD, status="ok", **board)]}

    def test_a_disagreement_is_a_row_with_its_count_and_nothing_of_a_posting(self):
        """Mutation: "a disagreement stays a workflow warning"."""
        [r] = health.run_events(self._run(agreement={"disagreements": 2}))
        self.assertEqual((r["Subject"], r["Status"]), (self.BOARD, "disagreement"))
        self.assertIn("2 posting(s)", r["Detail"])
        self.assertEqual(r["Key"], "run 2026-11-02T22:13:47Z %s agreement" % self.BOARD)

    def test_no_disagreement_is_no_row(self):
        """A check that agreed is the healthy case. Mutation: "every agreement
        check is a row"."""
        self.assertEqual(health.run_events(self._run(agreement={"disagreements": 0})), [])
        self.assertEqual(health.run_events(self._run()), [])

    def test_a_failed_check_is_a_row(self):
        """Mutation: "a check that failed says nothing"."""
        [r] = health.run_events(self._run(agreement={"failure": "HttpError: 500"}))
        self.assertEqual(r["Status"], "agreement check failed")
        self.assertEqual(r["Detail"], "HttpError: 500")

    def test_a_capped_walk_is_one_row_a_month_for_a_board(self):
        """A week's batch caps every morning, and one row says so. Mutations:
        "a capped walk reaches no row"; "a capped walk is a row every run"."""
        first = health.run_events(self._run(capped=True))
        later = dict(self._run(capped=True), run_at="2026-11-03T05:36:01Z")
        [a], [b] = first, health.run_events(later)
        self.assertEqual(a["Status"], "capped")
        self.assertEqual(a["Key"], b["Key"])
        self.assertEqual(a["Key"], "capped %s 2026-11" % self.BOARD)
        self.assertEqual(health.run_events(self._run(capped=False)), [])


class TestSentOnce(unittest.TestCase):
    def failing_run(self, run_at, **extra):
        return run_log(run_at=run_at, airtable={"failure": "PermanentError: 503"}, **extra)

    def test_an_event_recorded_as_sent_is_not_sent_again(self):
        first = self.failing_run("2026-10-06T05:11:15Z")
        [event] = health.pending([first], [], NOW)
        later = run_log(run_at="2026-10-06T18:50:32Z", health={"sent": [event["Key"]]})
        self.assertEqual(health.pending([first, later], [], NOW), [])

    def test_an_event_no_run_sent_is_sent_by_the_next(self):
        """Airtable down: the run that found it could not send it."""
        first = self.failing_run("2026-10-06T05:11:15Z", health={"failure": "503", "sent": []})
        keys = [r["Key"] for r in health.pending([first], [], NOW)]
        self.assertCountEqual(keys, ["run 2026-10-06T05:11:15Z projection",
                                     "run 2026-10-06T05:11:15Z health"])

    def test_an_event_older_than_the_window_is_not_sent(self):
        old = self.failing_run("2026-09-29T05:00:00Z")
        self.assertEqual(health.pending([old], [], NOW), [])

    def test_contract_findings_are_pending_too_and_each_key_once(self):
        check = contract_log(lever={"status": "unreachable", "detail": "503"})
        rows = health.pending([], [check, check], NOW)
        self.assertEqual([r["Key"] for r in rows], ["contract 2026-10-07T13:46:06Z lever"])

    def test_oldest_first(self):
        a = self.failing_run("2026-10-07T04:38:28Z")
        b = self.failing_run("2026-10-05T04:23:51Z")
        self.assertEqual([r["When"][:10] for r in health.pending([a, b], [], NOW)],
                         ["2026-10-05", "2026-10-07"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
