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
"""

import time

import requests

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

# Status codes worth trying again. Everything else in 4xx is the caller's
# fault and will fail identically on a retry.
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class HttpError(Exception):
    """Base for every failure this module reports."""


class PermanentError(HttpError):
    """A status that will not change on retry. 404, 403, 400."""

    def __init__(self, url, status):
        super().__init__("%s returned %s, which is not retryable" % (url, status))
        self.url = url
        self.status = status


class TransientError(HttpError):
    """Retryable, and every attempt was used."""

    def __init__(self, url, detail, attempts):
        super().__init__("%s failed after %d attempts: %s" % (url, attempts, detail))
        self.url = url
        self.detail = detail
        self.attempts = attempts


class BudgetExhausted(HttpError):
    """The run's request ceiling was reached. Not a failure of the board.

    The caller records what it did not reach and stops; the next run picks it
    up. ADR-0028."""

    def __init__(self, budget):
        super().__init__("per-run request budget of %d is exhausted" % budget)
        self.budget = budget


class CircuitOpen(HttpError):
    """Consecutive failures crossed the threshold. Further requests are
    refused without spending budget, until a success resets it."""

    def __init__(self, failures):
        super().__init__("circuit open after %d consecutive failures" % failures)
        self.failures = failures


class HttpClient:
    def __init__(self, budget=DEFAULT_BUDGET, max_attempts=DEFAULT_MAX_ATTEMPTS,
                 backoff_base=DEFAULT_BACKOFF_BASE, timeout=DEFAULT_TIMEOUT,
                 breaker_threshold=DEFAULT_BREAKER_THRESHOLD,
                 min_interval=DEFAULT_MIN_INTERVAL, session=None,
                 sleep=time.sleep, now=time.monotonic):
        self.budget = budget
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.timeout = timeout
        self.breaker_threshold = breaker_threshold
        self.min_interval = min_interval
        self._session = session if session is not None else requests.Session()
        self._sleep = sleep
        self._now = now
        self._last_request_at = None

        # Counters. These are the run log's raw material, so they count
        # attempts rather than logical fetches: a fetch that retried twice
        # cost three requests and the log must say so.
        self.requests_used = 0
        self.requests_by_source = {}
        self.retries = 0
        self.failures = 0
        self.consecutive_failures = 0
        self.refused = 0

    # ---------------------------------------------------------------- state
    @property
    def budget_remaining(self):
        return self.budget - self.requests_used

    @property
    def circuit_is_open(self):
        return self.consecutive_failures >= self.breaker_threshold

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

    def _pace(self):
        if self.min_interval <= 0:
            return
        if self._last_request_at is not None:
            wait = self.min_interval - (self._now() - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._now()

    def _record_success(self):
        self.consecutive_failures = 0

    def _record_failure(self):
        self.failures += 1
        self.consecutive_failures += 1

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
        if self.circuit_is_open:
            self.refused += 1
            raise CircuitOpen(self.consecutive_failures)

        last_detail = None
        for attempt in range(1, self.max_attempts + 1):
            self._spend(source)
            if attempt > 1:
                self.retries += 1
            self._pace()
            try:
                response = self._session.get(
                    url, params=params, timeout=self.timeout,
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
                status = response.status_code
            except Exception as e:
                # Transport-level: DNS, connection reset, read timeout.
                last_detail = "%s: %s" % (type(e).__name__, e)
                self._record_failure()
                if attempt < self.max_attempts and not self.circuit_is_open:
                    self._backoff(attempt)
                    continue
                raise TransientError(url, last_detail, attempt)

            if 200 <= status < 300:
                self._record_success()
                return response

            if status not in RETRYABLE_STATUS:
                self._record_failure()
                raise PermanentError(url, status)

            last_detail = "HTTP %s" % status
            self._record_failure()
            if attempt < self.max_attempts and not self.circuit_is_open:
                self._backoff(attempt, response)
                continue
            raise TransientError(url, last_detail, attempt)

        raise TransientError(url, last_detail or "no attempt made", self.max_attempts)

    def _backoff(self, attempt, response=None):
        """Exponential, and honours Retry-After when the server sends one,
        because a server that names a wait has better information than we do."""
        delay = self.backoff_base ** (attempt - 1)
        if response is not None:
            header = None
            try:
                header = response.headers.get("Retry-After")
            except Exception:
                header = None
            if header:
                try:
                    delay = max(delay, float(header))
                except (TypeError, ValueError):
                    pass
        self._sleep(delay)
