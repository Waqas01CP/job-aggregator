"""The shared HTTP module, tested from the brief.

The brief requires: retry with backoff, a budget counted per run including
retries and failures, a circuit breaker on consecutive failures that resets on
any success, and error classification on status codes rather than substrings.

No test here touches the network. The transport is injected.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.http_client import (BudgetExhausted, CircuitOpen, HttpClient,
                             PermanentError, TransientError)


class FakeResponse:
    def __init__(self, status_code, body="{}", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self):
        return json.loads(self._body)


class FakeSession:
    """Returns queued responses in order. A queued Exception is raised, which
    is how a connection reset or read timeout is simulated."""

    def __init__(self, queue):
        self.queue = list(queue)
        self.calls = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout,
                           "headers": headers})
        item = self.queue.pop(0) if self.queue else FakeResponse(200)
        if isinstance(item, Exception):
            raise item
        return item


def client(queue, **kw):
    """A client with pacing and sleeping disabled, so tests do not wait."""
    slept = []
    kw.setdefault("min_interval", 0)
    c = HttpClient(session=FakeSession(queue), sleep=slept.append, **kw)
    c.slept = slept
    return c


class TestBudget(unittest.TestCase):
    def test_every_attempt_is_counted_including_retries(self):
        """The brief says the budget counts retries and failures, not logical
        fetches. A budget that counted fetches would undercount a retrying run
        by exactly the amount that matters."""
        c = client([FakeResponse(503), FakeResponse(503), FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.requests_used, 3)
        self.assertEqual(c.retries, 2)
        self.assertEqual(c.requests_by_source, {"greenhouse": 3})

    def test_failures_count_against_the_budget(self):
        c = client([FakeResponse(404)])
        with self.assertRaises(PermanentError):
            c.get("https://example.test/jobs", "lever")
        self.assertEqual(c.requests_used, 1)

    def test_the_ceiling_refuses_further_requests(self):
        """ADR-0028: enforced in code, not by intention."""
        c = client([FakeResponse(200)] * 10, budget=2)
        c.get("https://example.test/a", "greenhouse")
        c.get("https://example.test/b", "greenhouse")
        with self.assertRaises(BudgetExhausted):
            c.get("https://example.test/c", "greenhouse")
        self.assertEqual(c.requests_used, 2)
        self.assertEqual(c.budget_remaining, 0)
        self.assertEqual(c.refused, 1)

    def test_a_retry_cannot_overspend_the_ceiling(self):
        """The retry loop spends budget per attempt, so a board failing at the
        ceiling must stop rather than borrow."""
        c = client([FakeResponse(503), FakeResponse(503), FakeResponse(503)], budget=2)
        with self.assertRaises(BudgetExhausted):
            c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.requests_used, 2)

    def test_counters_are_reported_per_source_and_total(self):
        c = client([FakeResponse(200)] * 3)
        c.get("https://example.test/a", "greenhouse")
        c.get("https://example.test/b", "greenhouse")
        c.get("https://example.test/c", "lever")
        counters = c.counters()
        self.assertEqual(counters["by_source"], {"greenhouse": 2, "lever": 1})
        self.assertEqual(counters["requests_used"], 3)
        self.assertEqual(counters["budget"], 500)


class TestClassification(unittest.TestCase):
    def test_500_is_retried(self):
        c = client([FakeResponse(500), FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.requests_used, 2)

    def test_429_is_retried(self):
        c = client([FakeResponse(429), FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.requests_used, 2)

    def test_404_is_not_retried(self):
        """A dead slug fails identically on every attempt. Retrying it spends
        budget to learn nothing."""
        c = client([FakeResponse(404), FakeResponse(200)])
        with self.assertRaises(PermanentError) as caught:
            c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(c.requests_used, 1)

    def test_403_is_not_retried(self):
        c = client([FakeResponse(403)])
        with self.assertRaises(PermanentError):
            c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.requests_used, 1)

    def test_a_body_saying_error_on_a_200_is_not_an_error(self):
        """Classification is on the status code. This is the case that defeats
        substring classification: the body is full of the word error and the
        request succeeded."""
        body = json.dumps({"jobs": [{"title": "Error Handling Engineer",
                                     "note": "error error timeout 503"}]})
        c = client([FakeResponse(200, body)])
        payload = c.get_json("https://example.test/jobs", "greenhouse")
        self.assertEqual(payload["jobs"][0]["title"], "Error Handling Engineer")
        self.assertEqual(c.failures, 0)

    def test_a_404_body_promising_availability_is_still_permanent(self):
        """The mirror case: a friendly body on a hard status."""
        c = client([FakeResponse(404, '{"message": "temporarily unavailable, retry"}')])
        with self.assertRaises(PermanentError):
            c.get("https://example.test/jobs", "greenhouse")

    def test_connection_failure_is_retried_then_reported(self):
        c = client([OSError("connection reset"), OSError("connection reset"),
                    OSError("connection reset")])
        with self.assertRaises(TransientError) as caught:
            c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(caught.exception.attempts, 3)
        self.assertEqual(c.requests_used, 3)

    def test_200_with_a_non_json_body_is_permanent(self):
        """A contract change, not a transport problem. Retrying fetches the
        same HTML again."""
        c = client([FakeResponse(200, "<html>maintenance</html>")])
        with self.assertRaises(PermanentError):
            c.get_json("https://example.test/jobs", "greenhouse")


class TestBackoff(unittest.TestCase):
    def test_backoff_grows(self):
        c = client([FakeResponse(503), FakeResponse(503), FakeResponse(200)],
                   backoff_base=2.0)
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.slept, [1.0, 2.0])

    def test_retry_after_is_honoured_when_longer(self):
        """A server naming a wait has better information than our formula."""
        c = client([FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.slept, [7.0])

    def test_a_junk_retry_after_does_not_crash_the_run(self):
        c = client([FakeResponse(429, headers={"Retry-After": "soon"}), FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertEqual(c.slept, [1.0])


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_consecutive_failures_and_refuses_without_spending(self):
        c = client([FakeResponse(500)] * 9, breaker_threshold=3, max_attempts=3)
        with self.assertRaises(TransientError):
            c.get("https://example.test/a", "greenhouse")
        self.assertTrue(c.circuit_is_open)
        used = c.requests_used
        with self.assertRaises(CircuitOpen):
            c.get("https://example.test/b", "greenhouse")
        self.assertEqual(c.requests_used, used,
                         "a refused request must not spend budget")

    def test_any_success_resets_it(self):
        """The brief: resets on any success. Without the reset, one flaky
        board would end the run for every board after it."""
        c = client([FakeResponse(500), FakeResponse(200), FakeResponse(500)],
                   breaker_threshold=2, max_attempts=1)
        with self.assertRaises(TransientError):
            c.get("https://example.test/a", "greenhouse")
        self.assertEqual(c.consecutive_failures, 1)
        c.get("https://example.test/b", "greenhouse")
        self.assertEqual(c.consecutive_failures, 0)
        self.assertFalse(c.circuit_is_open)

    def test_failures_on_different_boards_accumulate(self):
        """Consecutive means consecutive across the run, not within a board.
        Five boards each failing once is an outage."""
        c = client([FakeResponse(500)] * 5, breaker_threshold=3, max_attempts=1)
        for name in "abc":
            with self.assertRaises(TransientError):
                c.get("https://example.test/%s" % name, "greenhouse")
        self.assertTrue(c.circuit_is_open)


class TestRequestShape(unittest.TestCase):
    def test_sends_a_descriptive_user_agent_and_no_credentials(self):
        c = client([FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        headers = c._session.calls[0]["headers"]
        self.assertIn("job-aggregator", headers["User-Agent"])
        self.assertNotIn("Authorization", headers)

    def test_timeout_is_always_set(self):
        """A request with no timeout can hang a scheduled run forever."""
        c = client([FakeResponse(200)])
        c.get("https://example.test/jobs", "greenhouse")
        self.assertTrue(c._session.calls[0]["timeout"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
