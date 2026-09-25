"""The Airtable client. ADR-0034. Writing to a display service is not fetching
a job board, so this is not the shared fetch module and never imports it.

It owns what differs from fetching: the token, the write verb, the 429 and its
required 30-second wait, a pace under five requests a second per base, and a
call budget counted per month rather than per run. Retry, backoff and the
circuit breaker are the ones in `src/resilience.py`, imported, not copied.

**It writes and never reads.** ADR-0004, clarified 2026-09-23: the projection
performs no reads, and every read belongs to the sweep. This module has one
verb, an upsert, and a test asserts it exposes no other. The sweep is a later
build and gets its reads where that brief puts them, not here.

**It sends exactly the pipeline-owned fields**: ADR-0035's ten, and `Family`,
classified pipeline-owned on 2026-09-23 and built 2026-09-24. An upsert
updates every field it is given, so a field outside the set would overwrite
something that is not the pipeline's: `Status` above all, whose every write
also restarts the fifteen-day clock on `Classified at`. A record carrying any
other key, or missing one of the set, is refused before anything is sent.
Adding `Star reason` later is a change to PIPELINE_FIELDS and to the tests
that pin it, and the field must exist in the base first.

**A test run cannot reach production's table.** In test mode the table comes
from AIRTABLE_TEST_TABLE_ID only; there is no fallback, and a test ID equal to
the production ID is refused.

**No secret reaches an error message.** The token is a credential, and base
and table IDs are secrets in this public repository. An error's text can end
up in a run log on the public data branch, so errors name the operation and
the batch, a transport failure is reduced to its class name before it can
carry a URL, and `redact` scrubs any text that escapes another way.

Upsert is confirmed against Airtable's own documentation, 2026-09-23:
`PATCH` with `performUpsert.fieldsToMergeOn`, on all plans, updating only the
fields sent, and failing when more than one record matches. It has not been
exercised against the base yet.
"""

import os
import time

import requests

from .resilience import (HttpError, PermanentError, ResilientClient,
                         TransientError, CircuitOpen)  # noqa: F401

API_ROOT = "https://api.airtable.com/v0"

# ADR-0035: the only fields the pipeline may send, in the base's own order.
# Status, Classified at and the classification tables' reason fields are the
# operator's or Airtable's, and are never among them. Family is ADR-0038's
# label, classified pipeline-owned in ADR-0035's 2026-09-23 Changes row.
PIPELINE_FIELDS = ("Title", "Employer", "Location", "Link", "Published",
                   "First seen", "Order date", "Board", "Matched term",
                   "Identity", "Family")
IDENTITY_FIELD = "Identity"

# ADR-0004 and ADR-0035: ten records a call.
BATCH_SIZE = 10
# ADR-0004: stay under five requests a second per base. Airtable answers a
# sixth with a 429 and a 30-second wait, so the pace sits below the limit.
MIN_INTERVAL = 0.25
# ADR-0034, and Airtable's rate-limit page: a 429 means wait 30 seconds.
RATE_LIMIT_WAIT = 30.0
# ADR-0004's free-plan allowance per workspace, sourced not exercised. Calls
# made outside the pipeline, through a session's connector for instance, may
# count against the same allowance and are not seen here.
DEFAULT_MONTHLY_CALLS = 1000

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE = 2.0
DEFAULT_TIMEOUT = 30
DEFAULT_BREAKER_THRESHOLD = 5

TOKEN_ENV = "AIRTABLE_TOKEN"
BASE_ENV = "AIRTABLE_BASE_ID"
TABLE_ENV = "AIRTABLE_TABLE_ID"
TEST_TABLE_ENV = "AIRTABLE_TEST_TABLE_ID"
# Where a run log carries this client's counters, and where month_to_date
# reads them back. ADR-0034: the run log reports both budgets.
RUN_LOG_KEY = "airtable"
# Where a run log carries the sweep's client's counters (ADR-0050). The month's
# count sums both, since the allowance is one per workspace.
SWEEP_LOG_KEY = "sweep"


class AirtableConfigError(Exception):
    """A secret is missing or malformed. Raised before any request, and never
    carrying the value it objects to."""


class CallBudgetExhausted(HttpError):
    """The month's call allowance is spent. Not a failure of Airtable."""

    def __init__(self, ceiling, used):
        super().__init__("monthly Airtable call budget of %d is exhausted, "
                         "%d used" % (ceiling, used))
        self.ceiling = ceiling
        self.used = used


class ResponseMismatch(HttpError):
    """Airtable answered 2xx and the answer does not account for what was
    sent. Matched by key, never by position."""

    def __init__(self, target, detail, unaccounted=()):
        super().__init__("%s: %s" % (target, detail))
        self.target = target
        self.unaccounted = list(unaccounted)


class TransportFailure(Exception):
    """A dropped connection or a timeout, named by its class alone. The
    exceptions `requests` raises quote the URL, and the URL carries the base
    and table IDs."""


def table_env(test_mode):
    """The one secret a mode may take its table from. Never both."""
    return TEST_TABLE_ENV if test_mode else TABLE_ENV


def month_to_date(run_logs, now_iso):
    """Calls already spent this UTC month, summed from run logs.

    A log written before this client existed has no counters and contributes
    0. The allowance is per workspace, so a caller that can read both
    branches' logs should pass both."""
    month = now_iso[:7]
    total = 0
    for log in run_logs:
        if str(log.get("run_at", ""))[:7] != month:
            continue
        for key in (RUN_LOG_KEY, SWEEP_LOG_KEY):
            section = log.get(key) or {}
            total += int(section.get("calls_used") or 0)
    return total


def _batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


class AirtableClient(ResilientClient):
    def __init__(self, token, base_id, table_id,
                 monthly_ceiling=DEFAULT_MONTHLY_CALLS, used_this_month=0,
                 max_attempts=DEFAULT_MAX_ATTEMPTS,
                 backoff_base=DEFAULT_BACKOFF_BASE, timeout=DEFAULT_TIMEOUT,
                 breaker_threshold=DEFAULT_BREAKER_THRESHOLD,
                 min_interval=MIN_INTERVAL, session=None, sleep=time.sleep,
                 now=time.monotonic):
        if not token:
            raise AirtableConfigError("no Airtable token")
        if not (base_id or "").startswith("app"):
            raise AirtableConfigError(
                "the base ID must begin 'app'. A table ID in the base secret "
                "is the likely cause")
        if not (table_id or "").startswith("tbl"):
            raise AirtableConfigError(
                "the table ID must begin 'tbl'. A table name, or the base ID, "
                "in the table secret is the likely cause")
        super().__init__(max_attempts=max_attempts, backoff_base=backoff_base,
                         breaker_threshold=breaker_threshold,
                         min_interval=min_interval, sleep=sleep, now=now,
                         wait_floors={429: RATE_LIMIT_WAIT})
        self._token = token
        self._base_id = base_id
        self._table_id = table_id
        self.timeout = timeout
        self._session = session if session is not None else requests.Session()
        self.monthly_ceiling = monthly_ceiling
        self.used_before = used_this_month
        self.calls_used = 0
        self.rows_sent = 0

    @classmethod
    def from_env(cls, test_mode, environ=None, **kw):
        """Read the token, the base and this mode's table from the secrets.

        A mistyped secret name gives an empty value at run time, not an
        error, which looks exactly like a bug in the writer. So an empty value
        is refused here, by name, and no value is ever echoed."""
        environ = os.environ if environ is None else environ

        def value(name):
            return (environ.get(name) or "").strip()

        wanted = (TOKEN_ENV, BASE_ENV, table_env(test_mode))
        missing = [name for name in wanted if not value(name)]
        if missing:
            raise AirtableConfigError("empty or unset: %s" % ", ".join(missing))
        if test_mode and value(TEST_TABLE_ENV) == value(TABLE_ENV):
            raise AirtableConfigError(
                "%s equals %s, so a test run would write the production "
                "table" % (TEST_TABLE_ENV, TABLE_ENV))
        return cls(value(TOKEN_ENV), value(BASE_ENV),
                   value(table_env(test_mode)), **kw)

    # ---------------------------------------------------------------- state
    @property
    def month_remaining(self):
        return self.monthly_ceiling - self.used_before - self.calls_used

    def counters(self):
        """For the run log, under RUN_LOG_KEY. `calls_used` is what
        month_to_date sums on the next run."""
        return {
            "calls_used": self.calls_used,
            "rows_sent": self.rows_sent,
            "monthly_ceiling": self.monthly_ceiling,
            "month_to_date_before_run": self.used_before,
            "month_remaining": self.month_remaining,
            "retries": self.retries,
            "failures": self.failures,
            "refused": self.refused,
            "circuit_open": self.circuit_is_open,
        }

    def redact(self, text):
        """Any text with the token, the base ID and the table ID removed. The
        last line of defence for a message on its way to a run log."""
        text = str(text)
        for secret, label in ((self._token, "<token>"), (self._base_id, "<base>"),
                              (self._table_id, "<table>")):
            if secret:
                text = text.replace(secret, label)
        return text

    # ------------------------------------------------------------ internals
    def _spend(self, operation):
        if self.used_before + self.calls_used >= self.monthly_ceiling:
            self.refused += 1
            raise CallBudgetExhausted(self.monthly_ceiling,
                                      self.used_before + self.calls_used)
        self.calls_used += 1

    def _patch(self, body, target):
        url = "%s/%s/%s" % (API_ROOT, self._base_id, self._table_id)
        headers = {"Authorization": "Bearer %s" % self._token,
                   "Content-Type": "application/json"}

        def send():
            try:
                return self._session.request("PATCH", url, json=body,
                                             headers=headers, timeout=self.timeout)
            except Exception as e:
                raise TransportFailure(type(e).__name__) from None

        # Repeatable: a retry after an unknown outcome matches the rows the
        # first attempt made and updates them in place, which is the reason
        # ADR-0035 chose upsert over create.
        response = self._send(send, target, "upsert")
        try:
            return response.json()
        except ValueError:
            self._record_failure()
            raise PermanentError(target, "2xx but the body is not JSON")

    # ----------------------------------------------------------------- verb
    def upsert(self, records):
        """Create or update, matched server side on Identity. ADR-0035.

        Every record must carry exactly PIPELINE_FIELDS, a non-empty Identity,
        and an Identity no other record in the call shares. Anything else is
        refused before a request is made. Returns the IDs Airtable reports
        created and updated."""
        expected = set(PIPELINE_FIELDS)
        identities = []
        for index, fields in enumerate(records):
            extra = sorted(set(fields) - expected)
            missing = sorted(expected - set(fields))
            if extra or missing:
                raise ValueError(
                    "record %d is not the pipeline-owned fields: extra %s, missing %s"
                    % (index, extra or "none", missing or "none"))
            if not fields[IDENTITY_FIELD]:
                raise ValueError("record %d has no Identity, so the upsert "
                                 "could not match it" % index)
            identities.append(fields[IDENTITY_FIELD])
        if len(set(identities)) != len(identities):
            raise ValueError("two records share an Identity; one would "
                             "silently overwrite the other")

        result = {"created": [], "updated": []}
        batches = list(_batches(list(records), BATCH_SIZE))
        for number, batch in enumerate(batches, 1):
            target = "airtable upsert, batch %d of %d" % (number, len(batches))
            body = {"performUpsert": {"fieldsToMergeOn": [IDENTITY_FIELD]},
                    "records": [{"fields": {name: fields[name] for name in PIPELINE_FIELDS}}
                                for fields in batch]}
            payload = self._patch(body, target)
            got = {(r.get("fields") or {}).get(IDENTITY_FIELD)
                   for r in payload.get("records") or []}
            sent = [fields[IDENTITY_FIELD] for fields in batch]
            unaccounted = [identity for identity in sent if identity not in got]
            if unaccounted:
                raise ResponseMismatch(
                    target, "%d of %d records sent are not in the response"
                    % (len(unaccounted), len(sent)), unaccounted)
            self.rows_sent += len(batch)
            result["created"].extend(payload.get("createdRecords") or [])
            result["updated"].extend(payload.get("updatedRecords") or [])
        return result
