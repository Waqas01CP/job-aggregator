"""The shared retry loop, tested directly. ADR-0034.

Both clients exercise it, but neither sends a request that is unsafe to
repeat: the fetch module sends GETs and the Airtable client sends upserts. The
`repeatable=False` path exists for the sweep's deletes, the next build, and a
path no caller uses is tested here or it is not tested at all.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.resilience import (NOT_ACTED_ON, PermanentError, ResilientClient,
                            TransientError, backoff_delay)


class Response:
    def __init__(self, status, headers=None):
        self.status_code = status
        self.headers = headers or {}


class Minimal(ResilientClient):
    """The smallest client: an unlimited budget, a queue for a network."""

    def __init__(self, queue, **kw):
        self.slept = []
        super().__init__(max_attempts=kw.get("max_attempts", 3), backoff_base=2.0,
                         breaker_threshold=5, min_interval=0, sleep=self.slept.append,
                         now=lambda: 0.0, wait_floors=kw.get("wait_floors"))
        self.queue = list(queue)
        self.sent = 0

    def _spend(self, label):
        pass

    def send(self):
        self.sent += 1
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class TestUnrepeatableRequests(unittest.TestCase):
    def test_not_sent_again_after_a_server_error(self):
        """The outcome is unknown: the first attempt may have landed."""
        c = Minimal([Response(500), Response(200)])
        with self.assertRaises(TransientError):
            c._send(c.send, "a delete", "delete", repeatable=False)
        self.assertEqual(c.sent, 1)

    def test_not_sent_again_after_a_dropped_connection(self):
        c = Minimal([OSError("reset"), Response(200)])
        with self.assertRaises(TransientError):
            c._send(c.send, "a delete", "delete", repeatable=False)
        self.assertEqual(c.sent, 1)

    def test_sent_again_after_a_429_which_says_nothing_was_done(self):
        self.assertIn(429, NOT_ACTED_ON)
        c = Minimal([Response(429), Response(200)])
        c._send(c.send, "a delete", "delete", repeatable=False)
        self.assertEqual(c.sent, 2)

    def test_a_repeatable_request_is_sent_again_after_either(self):
        c = Minimal([Response(500), OSError("reset"), Response(200)])
        c._send(c.send, "a read", "read")
        self.assertEqual(c.sent, 3)

    def test_a_permanent_status_is_never_repeated(self):
        c = Minimal([Response(404), Response(200)])
        with self.assertRaises(PermanentError):
            c._send(c.send, "a read", "read")
        self.assertEqual(c.sent, 1)


class TestWaits(unittest.TestCase):
    def test_a_floor_for_a_status_is_applied(self):
        c = Minimal([Response(429), Response(200)], wait_floors={429: 30.0})
        c._send(c.send, "a write", "write")
        self.assertEqual(c.slept, [30.0])

    def test_the_formula(self):
        self.assertEqual(backoff_delay(1, 2.0), 1.0)
        self.assertEqual(backoff_delay(3, 2.0), 4.0)
        self.assertEqual(backoff_delay(1, 2.0, retry_after=7.0), 7.0)
        self.assertEqual(backoff_delay(1, 2.0, floor=30.0), 30.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
