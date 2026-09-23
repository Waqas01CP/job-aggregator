"""The shared HTTP module. Every request the pipeline makes goes through here.

**Adapters parse and nothing else.** The prior codebase has `fetch_with_retry`
duplicated verbatim across three files, which is the failure this split exists
to prevent: three copies drift, and the one that matters is never the one that
was fixed.

What lives here, and why:

**Retry with backoff**, because a board that times out once is not a board that
is down.

**A per-run request budget**, counting every attempt including retries and
failures. ADR-0028 sets the ceiling at 500 and is explicit that this is a
runaway guard, not a politeness policy: its only job is to stop a loop or a
pagination bug from issuing unbounded requests. Nobody has measured what volume
is appropriate, so the number carries no claim that it is right. The run log
records requests per source and in total, and that log is what sets the real
number later.

**A circuit breaker on consecutive failures**, reset by any success, so a board
that is genuinely down stops costing the run its remaining budget.

**Error classification on status codes, never on substrings of a message.**
A body containing the word "error" is not an error, and a 404 page that says
"temporarily unavailable" is still a 404.

When the budget is exhausted the caller is told, not lied to. ADR-0028 requires
deferred work to be recorded and picked up next run, which is safe only because
ADR-0007 makes a late posting a latency cost rather than a loss.

**Retry, backoff and the breaker live in `src/resilience.py`**, since
ADR-0034 gave the Airtable writer a client of its own and both must share
them. The budget stays here, because it is per run and the writer's is per
month. The error classes are imported from there and re-exported, so a caller
of this module sees the names it always did.
"""

import time

import requests

from .resilience import (RETRYABLE_STATUS, CircuitOpen, HttpError,  # noqa: F401
                         PermanentError, ResilientClient, TransientError)

# ADR-0028. Provisional, and explicitly so: a runaway guard, not a measured
# volume. Amended once the run log has a month of per-source counts.
DEFAULT_BUDGET = 500

# Retry and pacing are method choices, not decisions from a record.
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE = 2.0
DEFAULT_TIMEOUT = 30
DEFAULT_BREAKER_THRESHOLD = 5
DEFAULT_MIN_INTERVAL = 1.0

USER_AGENT = ("job-aggregator/0.1 (scheduled job-board poller; "
              "https://github.com/Waqas01CP/job-aggregator)")


class BudgetExhausted(HttpError):
    """The run's request ceiling was reached. Not a failure of the board.

    The caller records what it did not reach and stops; the next run picks it
    up. ADR-0028."""

    def __init__(self, budget):
        super().__init__("per-run request budget of %d is exhausted" % budget)
        self.budget = budget


class HttpClient(ResilientClient):
    def __init__(self, budget=DEFAULT_BUDGET, max_attempts=DEFAULT_MAX_ATTEMPTS,
                 backoff_base=DEFAULT_BACKOFF_BASE, timeout=DEFAULT_TIMEOUT,
                 breaker_threshold=DEFAULT_BREAKER_THRESHOLD,
                 min_interval=DEFAULT_MIN_INTERVAL, session=None,
                 sleep=time.sleep, now=time.monotonic):
        super().__init__(max_attempts=max_attempts, backoff_base=backoff_base,
                         breaker_threshold=breaker_threshold,
                         min_interval=min_interval, sleep=sleep, now=now)
        self.budget = budget
        self.timeout = timeout
        self._session = session if session is not None else requests.Session()

        # Counters. These are the run log's raw material, so they count
        # attempts rather than logical fetches: a fetch that retried twice
        # cost three requests and the log must say so.
        self.requests_used = 0
        self.requests_by_source = {}

    # ---------------------------------------------------------------- state
    @property
    def budget_remaining(self):
        return self.budget - self.requests_used

    def counters(self):
        """A snapshot for the run log. ADR-0028 wants per source and total."""
        return {
            "requests_used": self.requests_used,
            "budget": self.budget,
            "budget_remaining": self.budget_remaining,
            "by_source": dict(self.requests_by_source),
            "retries": self.retries,
            "failures": self.failures,
            "refused": self.refused,
            "circuit_open": self.circuit_is_open,
        }

    # ------------------------------------------------------------ internals
    def _spend(self, source):
        if self.requests_used >= self.budget:
            self.refused += 1
            raise BudgetExhausted(self.budget)
        self.requests_used += 1
        self.requests_by_source[source] = self.requests_by_source.get(source, 0) + 1

    # ---------------------------------------------------------------- fetch
    def get_json(self, url, source, params=None):
        """GET and decode JSON, or raise. `source` names the counter bucket,
        which is the platform, because ADR-0020 stores one file per source."""
        response = self.get(url, source, params=params)
        try:
            return response.json()
        except ValueError as e:
            # A 200 carrying something that is not JSON is a contract change,
            # not a transport problem. Retrying would just fetch it again.
            self._record_failure()
            raise PermanentError(url, "200 but body is not JSON: %s" % e)

    def get(self, url, source, params=None):
        """A GET is safe to repeat, so every retryable failure is retried."""
        return self._send(
            lambda: self._session.get(
                url, params=params, timeout=self.timeout,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"}),
            url, source)
