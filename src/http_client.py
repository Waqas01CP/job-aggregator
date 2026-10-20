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

**A circuit breaker on consecutive failures, one per platform**, reset by any
success, so a platform that is genuinely down stops costing the run its
remaining budget. One per platform since 2026-10-15: with one for the run,
five Manatal boards refused in a row on 2026-10-14T03:47Z left all six
Workable boards after them unread.

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

import os
import time

import requests

from .resilience import (RETRYABLE_STATUS, CircuitOpen, HttpError,  # noqa: F401
                         Pacer, PermanentError, ResilientClient, TransientError)

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


def source_options(adapter, environ=None):
    """What a source's own terms ask of every request to it, as `get` takes
    them: its key, from the environment variable its adapter names
    (`AUTH_ENV`), and its pace (`MIN_INTERVAL`). Empty for every source that
    asks neither. The run and the contract check both take them from here,
    so the adapter declares and this module fetches."""
    environ = os.environ if environ is None else environ
    options = {}
    auth_env = getattr(adapter, "AUTH_ENV", None)
    if auth_env:
        options["bearer"] = (environ.get(auth_env) or "").strip() or None
    if getattr(adapter, "MIN_INTERVAL", None):
        options["min_interval"] = adapter.MIN_INTERVAL
    return options


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
                         min_interval=min_interval, sleep=sleep, now=now,
                         breaker_per_label=True)
        self.budget = budget
        self.timeout = timeout
        self._session = session if session is not None else requests.Session()
        self._clock = (sleep, now)
        # A source with a rate limit of its own paces itself beside the run's
        # pace: Startup.jobs' 20 requests a minute (src/adapters/startupjobs.py).
        self._source_pacers = {}

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
            "circuits_open": self.circuits_open,
        }

    # ------------------------------------------------------------ internals
    def _spend(self, source):
        if self.requests_used >= self.budget:
            self.refused += 1
            raise BudgetExhausted(self.budget)
        self.requests_used += 1
        self.requests_by_source[source] = self.requests_by_source.get(source, 0) + 1

    # ---------------------------------------------------------------- fetch
    def get_json(self, url, source, params=None, bearer=None, min_interval=None):
        """GET and decode JSON, or raise. `source` names the counter bucket,
        which is the platform, because ADR-0020 stores one file per source.
        `bearer` and `min_interval`: a keyed source's key and its own rate
        limit, as `get` takes them."""
        response = self.get(url, source, params=params, bearer=bearer,
                            min_interval=min_interval)
        try:
            return response.json()
        except ValueError as e:
            # A 200 carrying something that is not JSON is a contract change,
            # not a transport problem. Retrying would just fetch it again.
            self._record_failure(source)
            raise PermanentError(url, "200 but body is not JSON: %s" % e)

    def get(self, url, source, params=None, accept="application/json", bearer=None,
            min_interval=None):
        """A GET is safe to repeat, so every retryable failure is retried.

        **A keyed source's key travels in its header and nowhere else**
        (`bearer`): never in the URL, so no error, which names the URL, can
        carry it. **A source's own rate limit** (`min_interval`, seconds
        between its requests) is kept by a pacer of its own, every attempt
        and retry included, beside the run's pace for every source."""
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        if bearer:
            headers["Authorization"] = "Bearer %s" % bearer
        pacer = None
        if min_interval:
            pacer = self._source_pacers.get(source)
            if pacer is None or pacer.min_interval != min_interval:
                pacer = self._source_pacers[source] = Pacer(min_interval, *self._clock)

        def send():
            if pacer is not None:
                pacer.wait()
            return self._session.get(url, params=params, timeout=self.timeout, headers=headers)
        return self._send(send, url, source)

    def get_text(self, url, source, params=None):
        """GET a body that is not JSON, We Work Remotely's RSS, whole: the same
        retries, budget and breaker as get_json, since fetch behaviour lives
        here and nowhere else. The adapter decodes it."""
        return self.get(url, source, params=params,
                        accept="application/rss+xml, application/xml;q=0.9, */*;q=0.8").text
