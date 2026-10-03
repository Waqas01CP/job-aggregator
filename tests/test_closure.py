"""The closure test, tested from ADR-0050 and Brief 7.

No network and no branch: run logs and seen entries are written by hand in
the shapes `src/run.py` writes them.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.closure import Closure
from src.config import SWEEP_PATH, ConfigError, load_sweep_config
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
    """A run log. Each board is status, fetched[, walk[, oldest_published]],
    where walk is the paginated walk's record: (stopped_by, mark)."""
    out = []
    for name, spec in boards.items():
        board = {"greenhouse": GH, "himalayas": HIM}[name]
        entry = {"board": board, "status": spec[0], "fetched": spec[1]}
        if len(spec) > 2 and spec[2]:
            entry["walk"] = {"stopped_by": spec[2][0], "mark": spec[2][1]}
        if len(spec) > 3:
            entry["oldest_published"] = spec[3]
        out.append(entry)
    return {"run_at": run_at, "boards": out}


# The search pins old postings on page one, so a walk's oldest posting is
# this old whatever it read: every live walk from 2026-09-27 to 10-02 logged it.
PINNED = "2026-09-16T06:15:55Z"


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
        """Himalayas is read only to what is stored. A morning that stopped
        at a mark newer than the posting never looked at it, though a pinned
        posting makes its oldest fetched date older still. The first build
        read that date as the walk's reach and marked 47 open rows closed on
        2026-10-01 and 10-02. Mutation: "a paginated walk's reach is its
        oldest posting"."""
        walk = ("mark", "2026-09-24T00:00:00Z")
        logs = [log(t, himalayas=("ok", 20, walk, PINNED)) for t in MORNINGS]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM,
                                         published="2026-09-20T10:00:00Z")), (None, None))

    def test_a_paginated_run_that_reached_back_does_count(self):
        """A mark older than the posting: every posting newer than the mark
        was read, so this one's absence is evidence."""
        walk = ("mark", "2026-09-10T00:00:00Z")
        logs = [log(t, himalayas=("ok", 500, walk, PINNED)) for t in MORNINGS[:4]]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), ("2026-09-25", "absent"))

    def test_a_walk_that_read_the_whole_feed_counts(self):
        logs = [log(t, himalayas=("ok", 60, ("end", "2026-09-24T00:00:00Z"))) for t in MORNINGS[:4]]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), ("2026-09-25", "absent"))

    def test_a_capped_walk_never_counts(self):
        """Stopped by the page cap, the walk proved nothing about what lies
        beyond it. Mutation: "a capped walk counts as reaching back"."""
        logs = [log(t, himalayas=("ok", 800, ("cap", "2026-09-10T00:00:00Z"))) for t in MORNINGS]
        c = closure(logs, {"himalayas:1": "2026-09-21T03:40:00Z"})
        self.assertEqual(c.closed_on(row("himalayas:1", board=HIM)), (None, None))

    def test_a_paginated_run_without_its_reach_recorded_never_counts(self):
        """Logs written before 2026-10-02 record only the oldest posting,
        which the pins make meaningless, so they prove nothing: the 47 marks
        clear on the next sweep. Mutation: "a log with no walk record counts"."""
        logs = [log(t, himalayas=("ok", 500, None, PINNED)) for t in MORNINGS]
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


class TestTheConfiguredCount(unittest.TestCase):
    """ADR-0050, the operator's decision of 2026-10-03: twelve runs, not four.
    Twelve Greenhouse postings left their boards and returned after 23 to 130
    hours, median 59, measured over the run logs on 2026-09-30. Since
    2026-09-30 a closed row is hidden from his `To review` view, so a false
    closure hides a live job."""

    LONGEST_ABSENCE_HOURS = 130
    HOURS_BETWEEN_RUNS = 12

    def test_the_shipped_count_outlasts_every_measured_absence(self):
        """Mutation: "the closure count goes back to four"."""
        runs = load_sweep_config().closed_after_polled_runs
        self.assertGreaterEqual(runs * self.HOURS_BETWEEN_RUNS, self.LONGEST_ABSENCE_HOURS)

    def test_it_closes_on_the_twelfth_polled_run_and_not_the_eleventh(self):
        """A posting gone as long as the longest return measured, 130 hours,
        about eleven runs, is still open; the twelfth run closes it."""
        runs = load_sweep_config().closed_after_polled_runs
        first = datetime(2026, 9, 22, 3, 40, tzinfo=timezone.utc)
        timeline = [(first + timedelta(hours=self.HOURS_BETWEEN_RUNS * i))
                    .isoformat().replace("+00:00", "Z") for i in range(runs)]
        last_seen = {"greenhouse:1": "2026-09-21T17:40:00Z"}
        for count, closed in ((runs - 1, None), (runs, timeline[runs - 1][:10])):
            with self.subTest(runs=count):
                logs = [log(t, greenhouse=("ok", 30)) for t in timeline[:count]]
                c = Closure(last_seen, logs, lambda board: False, runs, NOW)
                self.assertEqual(c.closed_on(row("greenhouse:1"))[0], closed)

    def test_a_log_window_shorter_than_the_count_is_refused(self):
        """The closure test counts runs in the logs it reads, so a window of
        ten logs and a count of twelve would let nothing close, silently.
        Mutation: "a window shorter than the count is accepted"."""
        with open(SWEEP_PATH, encoding="utf-8") as f:
            doc = json.load(f)
        doc.update(closed_after_polled_runs=12, run_log_window=10)
        path = os.path.join(tempfile.mkdtemp(), "sweep.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        with self.assertRaises(ConfigError):
            load_sweep_config(path)
        doc.update(run_log_window=12)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        self.assertEqual(load_sweep_config(path).run_log_window, 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
