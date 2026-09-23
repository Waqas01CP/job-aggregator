"""The Airtable client. ADR-0034. Writing to a display service is not fetching
a job board, so this is not the shared fetch module and never imports it.

It owns what differs from fetching: the token, the write verbs, the 429 and
its required 30-second wait, five requests a second per base, and a call
budget counted per month rather than per run. Retry, backoff and the circuit
breaker are the ones in `src/resilience.py`, imported, not copied.

It writes what it is given. **Which fields the writer may send is the
projection's job, not this module's.** ADR-0035 lists ten pipeline-owned
fields, and whether `Status` is ever written is an open conflict between
ADR-0035 and ADR-0046, so this module does not decide it by refusing a field.

**No identifier reaches an error message.** Base and table IDs are secrets in
a public repository, and an error's text can end up in a run log on the
public data branch. Errors name the operation and the batch, never the base,
the table, a record or the token.

Airtable's behaviour here is sourced from its API documentation and has not
been exercised: nothing has written to the base through this code yet.
"""

import os
import time

import requests

from .resilience import (HttpError, PermanentError, ResilientClient,
                         TransientError, CircuitOpen)  # noqa: F401

API_ROOT = "https://api.airtable.com/v0"

# ADR-0004 and ADR-0035: create, update and delete take ten records a call.
BATCH_SIZE = 10
# ADR-0004: list returns at most 100 records a page.
PAGE_SIZE = 100
# ADR-0034 and ADR-0004: five requests a second per base, enforced by the
# service. Pacing at the limit, not under it, because the budget is calls
# per month and a run makes a handful.
MIN_INTERVAL = 0.2
# ADR-0034: a 429 is followed by a required 30-second wait.
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
IDENTITY_FIELD = "Identity"
# Where a run log carries this client's counters, and where month_to_date
# reads them back. ADR-0034: the run log reports both budgets.
RUN_LOG_KEY = "airtable"


class AirtableConfigError(Exception):
    """A secret is missing or malformed. Raised before any request."""


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


def month_to_date(run_logs, now_iso):
    """Calls already spent this UTC month, summed from run logs.

    The allowance is per workspace, so a test run's calls count against the
    same month as a production run's: pass the logs of both branches. A log
    written before this client existed has no counters and contributes 0."""
    month = now_iso[:7]
    total = 0
    for log in run_logs:
        if str(log.get("run_at", ""))[:7] != month:
            continue
        section = log.get(RUN_LOG_KEY) or {}
        total += int(section.get("calls_used") or 0)
    return total


def _batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


class AirtableClient(ResilientClient):
    def __init__(self, token, base_id, monthly_ceiling=DEFAULT_MONTHLY_CALLS,
                 used_this_month=0, max_attempts=DEFAULT_MAX_ATTEMPTS,
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
        super().__init__(max_attempts=max_attempts, backoff_base=backoff_base,
                         breaker_threshold=breaker_threshold,
                         min_interval=min_interval, sleep=sleep, now=now,
                         wait_floors={429: RATE_LIMIT_WAIT})
        self._token = token
        self._base_id = base_id
        self.timeout = timeout
        self._session = session if session is not None else requests.Session()
        self.monthly_ceiling = monthly_ceiling
        self.used_before = used_this_month
        self.calls_used = 0
        self.calls_by_operation = {}

    @classmethod
    def from_env(cls, environ=None, **kw):
        """Read the token and base from the repository secrets.

        A mistyped secret name gives an empty value at run time, not an
        error, which looks exactly like a bug in the writer. So an empty
        value is refused here, by name, and the value is never echoed."""
        environ = os.environ if environ is None else environ
        values = {name: (environ.get(name) or "").strip()
                  for name in (TOKEN_ENV, BASE_ENV)}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise AirtableConfigError("empty or unset: %s" % ", ".join(missing))
        return cls(values[TOKEN_ENV], values[BASE_ENV], **kw)

    # ---------------------------------------------------------------- state
    @property
    def month_remaining(self):
        return self.monthly_ceiling - self.used_before - self.calls_used

    def counters(self):
        """For the run log, under RUN_LOG_KEY. `calls_used` is what
        month_to_date sums on the next run."""
        return {
            "calls_used": self.calls_used,
            "by_operation": dict(self.calls_by_operation),
            "monthly_ceiling": self.monthly_ceiling,
            "month_to_date_before_run": self.used_before,
            "month_remaining": self.month_remaining,
            "retries": self.retries,
            "failures": self.failures,
            "refused": self.refused,
            "circuit_open": self.circuit_is_open,
        }

    # ------------------------------------------------------------ internals
    def _spend(self, operation):
        if self.used_before + self.calls_used >= self.monthly_ceiling:
            self.refused += 1
            raise CallBudgetExhausted(self.monthly_ceiling,
                                      self.used_before + self.calls_used)
        self.calls_used += 1
        spent = self.calls_by_operation.get(operation, 0)
        self.calls_by_operation[operation] = spent + 1

    @staticmethod
    def _check_table(table):
        # IDs only. A table looked up by name costs a call and breaks
        # silently on a rename; docs/how-to/airtable-token-and-secrets.md.
        if not (table or "").startswith("tbl"):
            raise ValueError("a table ID beginning 'tbl' is required, not a name")

    def _call(self, method, table, operation, target, params=None, body=None,
              repeatable=True):
        url = "%s/%s/%s" % (API_ROOT, self._base_id, table)
        headers = {"Authorization": "Bearer %s" % self._token}
        if body is not None:
            headers["Content-Type"] = "application/json"
        response = self._send(
            lambda: self._session.request(method, url, params=params, json=body,
                                          headers=headers, timeout=self.timeout),
            target, operation, repeatable=repeatable)
        try:
            return response.json()
        except ValueError:
            self._record_failure()
            raise PermanentError(target, "2xx but the body is not JSON")

    # ---------------------------------------------------------------- verbs
    def upsert_records(self, table, records, merge_on=(IDENTITY_FIELD,)):
        """Create or update, matched server side on `merge_on`. ADR-0035.

        Repeatable: a retry after an unknown outcome matches the rows the
        first attempt made and updates them, which is the reason ADR-0035
        chose upsert over create. Every record must carry every merge field,
        because an upsert with nothing to match on is a create, and a retried
        create duplicates. Returns the records Airtable sent back and the
        IDs it reports created and updated."""
        self._check_table(table)
        merge_on = list(merge_on)
        keys = []
        for index, fields in enumerate(records):
            missing = [name for name in merge_on if fields.get(name) in (None, "")]
            if missing:
                raise ValueError("record %d has no value for %s, so the upsert "
                                 "could not match it" % (index, ", ".join(missing)))
            keys.append(tuple(fields[name] for name in merge_on))
        if len(set(keys)) != len(keys):
            raise ValueError("two records share a merge key; one would "
                             "silently overwrite the other")

        result = {"records": [], "created": [], "updated": []}
        batches = list(_batches(list(records), BATCH_SIZE))
        for number, batch in enumerate(batches, 1):
            target = "airtable upsert, batch %d of %d" % (number, len(batches))
            body = {"performUpsert": {"fieldsToMergeOn": merge_on},
                    "records": [{"fields": dict(fields)} for fields in batch]}
            payload = self._call("PATCH", table, "upsert", target, body=body)
            returned = payload.get("records") or []
            got = {tuple((r.get("fields") or {}).get(name) for name in merge_on)
                   for r in returned}
            sent = [tuple(fields[name] for name in merge_on) for fields in batch]
            unaccounted = [key for key in sent if key not in got]
            if unaccounted:
                raise ResponseMismatch(
                    target, "%d of %d records sent are not in the response"
                    % (len(unaccounted), len(sent)), unaccounted)
            result["records"].extend(returned)
            result["created"].extend(payload.get("createdRecords") or [])
            result["updated"].extend(payload.get("updatedRecords") or [])
        return result

    def create_records(self, table, records):
        """Plain creates. **Not repeatable.** A create whose outcome is
        unknown is not sent again, because the first may have landed and the
        second would duplicate it. It is retried only on a 429, where Airtable
        says it did not act. With no key to align on, the response must
        return exactly as many records as were sent."""
        self._check_table(table)
        created = []
        batches = list(_batches(list(records), BATCH_SIZE))
        for number, batch in enumerate(batches, 1):
            target = "airtable create, batch %d of %d" % (number, len(batches))
            body = {"records": [{"fields": dict(fields)} for fields in batch]}
            payload = self._call("POST", table, "create", target, body=body,
                                 repeatable=False)
            returned = payload.get("records") or []
            if len(returned) != len(batch):
                raise ResponseMismatch(target, "sent %d records, %d came back"
                                       % (len(batch), len(returned)))
            created.extend(returned)
        return created

    def delete_records(self, table, record_ids):
        """Delete by Airtable record ID. **Not repeatable**: deletion is the
        one irreversible act here, and one whose outcome is unknown is
        reported rather than sent again. The caller re-derives on its next
        run. Every requested ID must come back marked deleted."""
        self._check_table(table)
        record_ids = list(record_ids)
        for rid in record_ids:
            if not str(rid).startswith("rec"):
                raise ValueError("an Airtable record ID beginning 'rec' is "
                                 "required; a pipeline identity is not one")
        deleted = []
        batches = list(_batches(record_ids, BATCH_SIZE))
        for number, batch in enumerate(batches, 1):
            target = "airtable delete, batch %d of %d" % (number, len(batches))
            params = [("records[]", rid) for rid in batch]
            payload = self._call("DELETE", table, "delete", target,
                                 params=params, repeatable=False)
            confirmed = {r.get("id") for r in payload.get("records") or []
                         if r.get("deleted") is True}
            unaccounted = [rid for rid in batch if rid not in confirmed]
            if unaccounted:
                raise ResponseMismatch(
                    target, "%d of %d records not confirmed deleted"
                    % (len(unaccounted), len(batch)), unaccounted)
            deleted.extend(batch)
        return deleted

    def list_records(self, table, fields=None, formula=None):
        """Every record in a table, following Airtable's offset. Each page is
        one call against the month's budget, which is also what stops a
        paging loop that never ends."""
        self._check_table(table)
        params = [("pageSize", PAGE_SIZE)]
        params += [("fields[]", name) for name in (fields or ())]
        if formula:
            params.append(("filterByFormula", formula))
        records, offset, page = [], None, 0
        while True:
            page += 1
            target = "airtable list, page %d" % page
            payload = self._call("GET", table, "list", target,
                                 params=params + ([("offset", offset)] if offset else []))
            records.extend(payload.get("records") or [])
            offset = payload.get("offset")
            if not offset:
                return records
