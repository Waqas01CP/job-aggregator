"""Retry, backoff and circuit breaking, shared by every client that makes a
request. ADR-0034.

CLAUDE.md's rule is that this logic exists once. It was written when the
fetch module was the only client, so "one module" and "once" meant the same
thing. The Airtable writer is a second client with a different verb,
authentication, budget, rate limit and failure semantics, and ADR-0034 gives
it a module of its own. What must not be duplicated moves here, and both
clients import it. A third client copying this loop instead of importing it
is the failure the rule exists to prevent.

What stays in each client: the budget, because the fetch budget is per run
and the Airtable budget is per month, and each client's own request shape.

**Proved by mutation, not assumed.** ADR-0034's Confirmation: break the
backoff calculation once and both the fetch module's tests and the Airtable
client's tests must fail. If only one does, the logic is not actually shared.
"""

# Status codes worth trying again. Everything else in 4xx is the caller's
# fault and will fail identically on a retry.
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})

# Statuses where the server says it did not act on the request. Only these
# are retried for a request that is unsafe to repeat. A 500 or a dropped
# connection leaves the outcome unknown, and repeating a create after an
# unknown outcome is how ADR-0035's duplicate rows happen.
NOT_ACTED_ON = frozenset({429})


class HttpError(Exception):
    """Base for every failure a client reports."""


class PermanentError(HttpError):
    """A status that will not change on retry. 404, 403, 400.

    `url` is whatever the client names the request by. The Airtable client
    passes a label carrying no base or table ID, because this message can
    reach a run log on the public data branch."""

    def __init__(self, url, status):
        super().__init__("%s returned %s, which is not retryable" % (url, status))
        self.url = url
        self.status = status


class TransientError(HttpError):
    """Retryable, and every attempt allowed was used."""

    def __init__(self, url, detail, attempts):
        super().__init__("%s failed after %d attempts: %s" % (url, attempts, detail))
        self.url = url
        self.detail = detail
        self.attempts = attempts


class CircuitOpen(HttpError):
    """Consecutive failures crossed the threshold. Further requests are
    refused without spending budget, until a success resets it."""

    def __init__(self, failures):
        super().__init__("circuit open after %d consecutive failures" % failures)
        self.failures = failures


def retry_after_seconds(response):
    """The server's Retry-After in seconds, or None. A junk value is ignored
    rather than allowed to crash a run."""
    if response is None:
        return None
    try:
        header = response.headers.get("Retry-After")
    except Exception:
        return None
    if not header:
        return None
    try:
        return float(header)
    except (TypeError, ValueError):
        return None


def backoff_delay(attempt, base, retry_after=None, floor=0.0):
    """Exponential in the attempt number, never shorter than a wait the server
    named, because a server that names a wait has better information than we
    do, and never shorter than a floor the service requires."""
    delay = base ** (attempt - 1)
    if retry_after is not None:
        delay = max(delay, retry_after)
    return max(delay, floor)


class CircuitBreaker:
    """Opens on consecutive failures and is reset by any success.

    Consecutive across the client's whole life, not per target: five boards
    each failing once is an outage."""

    def __init__(self, threshold):
        self.threshold = threshold
        self.consecutive = 0

    @property
    def is_open(self):
        return self.consecutive >= self.threshold

    def record_success(self):
        self.consecutive = 0

    def record_failure(self):
        self.consecutive += 1


class Pacer:
    """A minimum interval between requests. The fetch module paces for
    politeness; Airtable enforces five requests a second per base."""

    def __init__(self, min_interval, sleep, now):
        self.min_interval = min_interval
        self._sleep = sleep
        self._now = now
        self._last = None

    def wait(self):
        if self.min_interval <= 0:
            return
        if self._last is not None:
            gap = self.min_interval - (self._now() - self._last)
            if gap > 0:
                self._sleep(gap)
        self._last = self._now()


class ResilientClient:
    """The retry loop, the breaker and the counters both clients report.

    A subclass supplies `_spend(label)`, which charges one attempt to its own
    budget and raises when the budget is gone. Every attempt is charged,
    including retries and failures, because a run that retried twice spent
    three requests and its log must say so."""

    def __init__(self, max_attempts, backoff_base, breaker_threshold,
                 min_interval, sleep, now, wait_floors=None):
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.min_interval = min_interval
        self.breaker = CircuitBreaker(breaker_threshold)
        self.pacer = Pacer(min_interval, sleep, now)
        self._sleep = sleep
        self.wait_floors = dict(wait_floors or {})
        self.retries = 0
        self.failures = 0
        self.refused = 0

    @property
    def breaker_threshold(self):
        return self.breaker.threshold

    @property
    def consecutive_failures(self):
        return self.breaker.consecutive

    @property
    def circuit_is_open(self):
        return self.breaker.is_open

    def _spend(self, label):
        raise NotImplementedError

    def _record_success(self):
        self.breaker.record_success()

    def _record_failure(self):
        self.failures += 1
        self.breaker.record_failure()

    def _may_retry(self, attempt):
        return attempt < self.max_attempts and not self.breaker.is_open

    def _backoff(self, attempt, response=None, status=None):
        self._sleep(backoff_delay(attempt, self.backoff_base,
                                  retry_after=retry_after_seconds(response),
                                  floor=self.wait_floors.get(status, 0.0)))

    def _send(self, send, target, label, repeatable=True):
        """Call `send()` until it returns a 2xx response, and return it.

        `send` takes no arguments and returns a response or raises a
        transport error. `target` names the request in error messages.
        `label` is the budget bucket. `repeatable=False` marks a request
        that must not be sent twice after an unknown outcome: it is retried
        only on a status in NOT_ACTED_ON."""
        if self.breaker.is_open:
            self.refused += 1
            raise CircuitOpen(self.breaker.consecutive)

        last_detail = None
        for attempt in range(1, self.max_attempts + 1):
            self._spend(label)
            if attempt > 1:
                self.retries += 1
            self.pacer.wait()
            try:
                response = send()
                status = response.status_code
            except Exception as e:
                # Transport-level: DNS, connection reset, read timeout.
                last_detail = "%s: %s" % (type(e).__name__, e)
                self._record_failure()
                if repeatable and self._may_retry(attempt):
                    self._backoff(attempt)
                    continue
                raise TransientError(target, last_detail, attempt)

            if 200 <= status < 300:
                self._record_success()
                return response

            if status not in RETRYABLE_STATUS:
                self._record_failure()
                raise PermanentError(target, status)

            last_detail = "HTTP %s" % status
            self._record_failure()
            if (repeatable or status in NOT_ACTED_ON) and self._may_retry(attempt):
                self._backoff(attempt, response, status)
                continue
            raise TransientError(target, last_detail, attempt)

        raise TransientError(target, last_detail or "no attempt made", self.max_attempts)
