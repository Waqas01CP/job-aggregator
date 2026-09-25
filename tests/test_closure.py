"""The closure test, tested from ADR-0050 and Brief 7.

No network and no branch: run logs and seen entries are written by hand in
the shapes `src/run.py` writes them.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.closure import Closure
from src.normalise import Row

NOW = "2026-10-01T12:00:00Z"
GH, HIM = "greenhouse:acme", "himalayas:browse"


def row(identity, board=GH, published="2026-09-20T10:00:00Z", expires=None):
    return Row(identity=identity, source=board.split(":")[0], board_id=board,
               external_id=identity, title="AI Engineer", title_normalised="AI Engineer",
               url="https://x.test/" + identity, url_provenance="payload",
               first_seen="2026-09-20T10:00:00Z", ordering_date=published,
               ordering_date_source="publication", employer="Acme", location="Lahore",
               published_at=published, published_field="first_published", expires_at=expires)


def log(run_at, **boards):
    """A run log. Each board is status, fetched[, oldest_published]."""
    out = []
    for name, spec in boards.items():
        board = {"greenhouse": GH, "himalayas": HIM}[name]
        entry = {"board": board, "status": spec[0], "fetched": spec[1]}
        if len(spec) > 2:
            entry["oldest_published"] = spec[2]
        out.append(entry)
    return {"run_at": run_at, "boards": out}


def closure(logs, last_seen, runs_needed=4):
    return Closure(last_seen, logs, lambda board: board == HIM, runs_needed, NOW)


MORNINGS = ["2026-09-2%dT03:40:00Z" % d for d in range(2, 8)]
EVENINGS = ["2026-09-2%dT17:40:00Z" % d for d in range(2, 8)]


class TestAbsence(unittest.TestCase):
    def test_absent_on_four_polled_runs_closes_on_the_fourth(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS[:5]]
        c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("greenhouse:1")), ("2026-09-25", "absent"))

    def test_three_is_not_enough(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS[:3]]
        c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("greenhouse:1")), (None, None))

    def test_a_posting_seen_again_is_open(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS]
        c = closure(logs, {"greenhouse:1": MORNINGS[-1]})
        self.assertEqual(c.closed_on(row("greenhouse:1")), (None, None))

    def test_the_count_is_configuration(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS[:2]]
        c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z"}, runs_needed=2)
        self.assertEqual(c.closed_on(row("greenhouse:1")), ("2026-09-23", "absent"))

    def test_runs_that_did_not_poll_never_count(self):
        """Skipped, failed, not reached, or answering nothing: none polled."""
        for status, fetched in (("skipped", 0), ("failed", 0), ("not reached", 0),
                                ("ok", 0), ("error", 0)):
            with self.subTest(status=status, fetched=fetched):
                logs = [log(t, greenhouse=(status, fetched)) for t in MORNINGS]
                c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z"})
                self.assertEqual(c.closed_on(row("greenhouse:1")), (None, None))

    def test_four_evening_runs_with_himalayas_skipped_close_nothing(self):
        """ADR-0050's check that can fail. ADR-0048 skips Himalayas every
        evening; counting those runs would close every aggregator row in
        about two days."""
        logs = [log(t, greenhouse=("ok", 30), himalayas=("skipped", 0)) for t in EVENINGS]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), (None, None))

    def test_a_paginated_run_that_stopped_short_did_not_reach_the_posting(self):
        """Himalayas is read only to what is stored. A morning that fetched
        one page of newer postings never looked at an older one."""
        newer = "2026-09-24T00:00:00Z"
        logs = [log(t, himalayas=("ok", 20, newer)) for t in MORNINGS]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM,
                                         published="2026-09-20T10:00:00Z")), (None, None))

    def test_a_paginated_run_that_reached_back_does_count(self):
        older = "2026-09-10T00:00:00Z"
        logs = [log(t, himalayas=("ok", 500, older)) for t in MORNINGS[:4]]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), ("2026-09-25", "absent"))

    def test_a_paginated_run_without_its_reach_recorded_never_counts(self):
        """Logs written before the reach was recorded prove nothing."""
        logs = [log(t, himalayas=("ok", 500)) for t in MORNINGS]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), (None, None))

    def test_a_posting_no_run_has_seen_is_unknowable(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS]
        self.assertEqual(closure(logs, {}).closed_on(row("greenhouse:1")), (None, None))


class TestExpiry(unittest.TestCase):
    def test_a_passed_expiry_closes_on_its_own_date(self):
        c = closure([], {})
        self.assertEqual(c.closed_on(row("himalayas:9", board=HIM,
                                         expires="2026-09-28T00:00:00Z")),
                         ("2026-09-28", "expired"))

    def test_a_future_expiry_does_not(self):
        c = closure([], {})
        self.assertEqual(c.closed_on(row("himalayas:9", board=HIM,
                                         expires="2026-12-01T00:00:00Z")), (None, None))


class TestGroups(unittest.TestCase):
    def test_one_open_member_keeps_the_group_open(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS]
        c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z",
                           "greenhouse:2": MORNINGS[-1]})
        self.assertIsNone(c.group_closed_on([row("greenhouse:1"), row("greenhouse:2")]))

    def test_a_group_closes_on_the_day_its_last_member_did(self):
        logs = [log(t, greenhouse=("ok", 30)) for t in MORNINGS]
        c = closure(logs, {"greenhouse:1": "2026-09-21T03:40:00Z",
                           "greenhouse:2": MORNINGS[1]})
        self.assertEqual(c.group_closed_on([row("greenhouse:1"), row("greenhouse:2")]),
                         "2026-09-27")


if __name__ == "__main__":
    unittest.main(verbosity=2)
