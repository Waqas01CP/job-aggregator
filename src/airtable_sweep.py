"""The sweep's Airtable client. ADR-0050.

The projection's client, `src/airtable.py`, writes and never reads: ADR-0004,
clarified 2026-09-23, puts every read with the sweep. So the sweep's reads and
its three writes live here, in their own module, and `src/airtable.py` stays
read-free, which a test holds. Retry, backoff and the breaker are the shared
ones in `src/resilience.py`; the budget, the pacing and the secret discipline
are Airtable's own and repeat what the projection's client does.

**It writes only what the pipeline owns.** ADR-0035's rule, which an upsert
makes dangerous and a create or an update makes no safer:

- on `Jobs`, the one field `Closed`, never `Status`, whose every write would
  restart the fifteen-day clock on `Classified at`;
- on a classification table, the ten identifying fields of the copy, never
  the operator's reason or `Stage`, and never `Classified`, which Airtable
  sets.

Anything else is refused before a request is made.

**A test run reaches only the test tables.** Each of the four tables comes
from its own secret, the test ones in test mode, with no fallback; a test ID
equal to a production one is refused.

**Two of its writes cannot be repeated safely.** A create retried after an
unknown outcome may make a second copy, and a delete retried after one may
fail on a record already gone. Both are sent once and retried only on a 429,
which Airtable guarantees was not acted on. A read and an update of `Closed`
are safe to repeat.
"""

import os
import time

import requests

from .airtable import (API_ROOT, BASE_ENV, BATCH_SIZE, DEFAULT_BACKOFF_BASE, SWEEP_LOG_KEY,
                       DEFAULT_BREAKER_THRESHOLD, DEFAULT_MAX_ATTEMPTS, DEFAULT_MONTHLY_CALLS,
                       DEFAULT_TIMEOUT, MIN_INTERVAL, RATE_LIMIT_WAIT, TABLE_ENV,
                       TEST_TABLE_ENV, TOKEN_ENV, AirtableConfigError, CallBudgetExhausted,
                       ResponseMismatch, TransportFailure)
from .resilience import PermanentError, ResilientClient

JOBS = "jobs"
# The three classification tables, keyed by the `Status` value that feeds
# each: the operator named the values after the tables, 2026-09-24.
CLASSIFICATION_TABLES = ("rejected-not-a-fit", "rejected-poor-filtering", "accepted")

# The ten identifying fields a copy carries: ADR-0035's ten, the ones the
# three classification tables share with `Jobs`.
COPY_FIELDS = ("Title", "Employer", "Location", "Link", "Published", "First seen",
               "Order date", "Board", "Matched term", "Identity")
# Each classification table's operator field: the reason, or the stage.
OPERATOR_FIELD = {"rejected-not-a-fit": "Choice reason",
                  "rejected-poor-filtering": "Pipeline reason",
                  "accepted": "Stage"}
# What the sweep may write, per table. Nothing else leaves this module.
WRITES = {JOBS: ("Closed",)}
WRITES.update({table: COPY_FIELDS for table in CLASSIFICATION_TABLES})

# The secret each table's ID comes from, per mode. The production names are
# the ones the operator created on 2026-09-18; the test ones on 2026-09-25,
# for the tables of his decision D7.
TABLE_SECRETS = {
    False: {JOBS: TABLE_ENV,
            "rejected-not-a-fit": "AIRTABLE_NOT_A_FIT_TABLE_ID",
            "rejected-poor-filtering": "AIRTABLE_POOR_FILTERING_TABLE_ID",
            "accepted": "AIRTABLE_ACCEPTED_TABLE_ID"},
    True: {JOBS: TEST_TABLE_ENV,
           "rejected-not-a-fit": "AIRTABLE_NOT_A_FIT_TEST_TABLE_ID",
           "rejected-poor-filtering": "AIRTABLE_POOR_FILTERING_TEST_TABLE_ID",
           "accepted": "AIRTABLE_ACCEPTED_TEST_TABLE_ID"},
}
PAGE_SIZE = 100
RUN_LOG_KEY = SWEEP_LOG_KEY


class SweepClient(ResilientClient):
    def __init__(self, token, base_id, tables, monthly_ceiling=DEFAULT_MONTHLY_CALLS,
                 used_this_month=0, max_attempts=DEFAULT_MAX_ATTEMPTS,
                 backoff_base=DEFAULT_BACKOFF_BASE, timeout=DEFAULT_TIMEOUT,
                 breaker_threshold=DEFAULT_BREAKER_THRESHOLD, min_interval=MIN_INTERVAL,
                 session=None, sleep=time.sleep, now=time.monotonic):
        if not token:
            raise AirtableConfigError("no Airtable token")
        if not (base_id or "").startswith("app"):
            raise AirtableConfigError("the base ID must begin 'app'")
        if set(tables) != {JOBS, *CLASSIFICATION_TABLES}:
            raise AirtableConfigError("the sweep needs exactly its four tables")
        for key, table_id in tables.items():
            if not (table_id or "").startswith("tbl"):
                raise AirtableConfigError("the %s table ID must begin 'tbl'" % key)
        super().__init__(max_attempts=max_attempts, backoff_base=backoff_base,
                         breaker_threshold=breaker_threshold, min_interval=min_interval,
                         sleep=sleep, now=now, wait_floors={429: RATE_LIMIT_WAIT})
        self._token = token
        self._base_id = base_id
        self._tables = dict(tables)
        self.timeout = timeout
        self._session = session if session is not None else requests.Session()
        self.monthly_ceiling = monthly_ceiling
        self.used_before = used_this_month
        self.calls_used = 0

    @classmethod
    def from_env(cls, test_mode, environ=None, **kw):
        """The token, the base and this mode's four tables. An empty secret is
        refused by name and no value is ever echoed. In test mode a table ID
        equal to any production table's is refused, so a test run cannot
        reach production."""
        environ = os.environ if environ is None else environ

        def value(name):
            return (environ.get(name) or "").strip()

        names = TABLE_SECRETS[bool(test_mode)]
        missing = [n for n in [TOKEN_ENV, BASE_ENV] + list(names.values()) if not value(n)]
        if missing:
            raise AirtableConfigError("empty or unset: %s" % ", ".join(missing))
        if test_mode:
            production = {value(n) for n in TABLE_SECRETS[False].values()} - {""}
            clash = [n for n in names.values() if value(n) in production]
            if clash:
                raise AirtableConfigError(
                    "%s equals a production table ID, so a test run would write "
                    "production" % ", ".join(clash))
        return cls(value(TOKEN_ENV), value(BASE_ENV),
                   {key: value(n) for key, n in names.items()}, **kw)

    # ---------------------------------------------------------------- state
    @property
    def month_remaining(self):
        return self.monthly_ceiling - self.used_before - self.calls_used

    def counters(self):
        return {"calls_used": self.calls_used, "retries": self.retries,
                "failures": self.failures, "refused": self.refused,
                "circuit_open": self.circuit_is_open}

    def redact(self, text):
        text = str(text)
        secrets = [(self._token, "<token>"), (self._base_id, "<base>")]
        secrets += [(table_id, "<%s table>" % key) for key, table_id in self._tables.items()]
        for secret, label in secrets:
            if secret:
                text = text.replace(secret, label)
        return text

    # ------------------------------------------------------------ internals
    def _spend(self, operation):
        if self.used_before + self.calls_used >= self.monthly_ceiling:
            self.refused += 1
            raise CallBudgetExhausted(self.monthly_ceiling, self.used_before + self.calls_used)
        self.calls_used += 1

    def _call(self, method, table, target, repeatable, params=None, body=None):
        url = "%s/%s/%s" % (API_ROOT, self._base_id, self._tables[table])
        headers = {"Authorization": "Bearer %s" % self._token}
        if body is not None:
            headers["Content-Type"] = "application/json"

        def send():
            try:
                return self._session.request(method, url, params=params, json=body,
                                             headers=headers, timeout=self.timeout)
            except Exception as e:
                raise TransportFailure(type(e).__name__) from None

        response = self._send(send, target, "sweep", repeatable=repeatable)
        try:
            return response.json()
        except ValueError:
            self._record_failure()
            raise PermanentError(target, "2xx but the body is not JSON")

    @staticmethod
    def _batches(items):
        for start in range(0, len(items), BATCH_SIZE):
            yield items[start:start + BATCH_SIZE]

    def _refuse_foreign_fields(self, table, fields, index):
        extra = sorted(set(fields) - set(WRITES[table]))
        if extra:
            raise ValueError("record %d for %s carries fields the pipeline does not own: %s"
                             % (index, table, extra))

    # ----------------------------------------------------------------- read
    def list_records(self, table, fields):
        """Every record in a table, with the named fields. One call per
        hundred records. Airtable omits a field that is empty."""
        records, offset, page = [], None, 0
        while True:
            page += 1
            params = [("pageSize", PAGE_SIZE)] + [("fields[]", name) for name in fields]
            if offset:
                params.append(("offset", offset))
            payload = self._call("GET", table, "airtable read %s, page %d" % (table, page),
                                 repeatable=True, params=params)
            for r in payload.get("records") or []:
                records.append({"id": r.get("id"), "createdTime": r.get("createdTime"),
                                "fields": r.get("fields") or {}})
            offset = payload.get("offset")
            if not offset:
                return records

    # ---------------------------------------------------------------- write
    def create_copies(self, table, records):
        """Create copies in a classification table. Returns their IDs, matched
        to what was sent by Identity, never by position."""
        if table not in CLASSIFICATION_TABLES:
            raise ValueError("copies go to a classification table, not %s" % table)
        for index, fields in enumerate(records):
            self._refuse_foreign_fields(table, fields, index)
            if not fields.get("Identity"):
                raise ValueError("record %d has no Identity" % index)
        created = []
        batches = list(self._batches(list(records)))
        for number, batch in enumerate(batches, 1):
            target = "airtable create in %s, batch %d of %d" % (table, number, len(batches))
            payload = self._call("POST", table, target, repeatable=False,
                                 body={"records": [{"fields": dict(f)} for f in batch]})
            got = {(r.get("fields") or {}).get("Identity"): r.get("id")
                   for r in payload.get("records") or []}
            missing = [f["Identity"] for f in batch if not got.get(f["Identity"])]
            if missing:
                raise ResponseMismatch(target, "%d of %d copies are not in the response"
                                       % (len(missing), len(batch)), missing)
            created.extend(got[f["Identity"]] for f in batch)
        return created

    def set_closed(self, updates):
        """Set or clear `Closed` on `Jobs` rows. `updates` is a list of
        (record ID, ISO date or None). The only field sent is `Closed`."""
        done = []
        batches = list(self._batches(list(updates)))
        for number, batch in enumerate(batches, 1):
            target = "airtable update of Closed, batch %d of %d" % (number, len(batches))
            records = [{"id": record_id, "fields": {"Closed": day}} for record_id, day in batch]
            for index, r in enumerate(records):
                self._refuse_foreign_fields(JOBS, r["fields"], index)
            payload = self._call("PATCH", JOBS, target, repeatable=True, body={"records": records})
            got = {r.get("id") for r in payload.get("records") or []}
            missing = [record_id for record_id, _ in batch if record_id not in got]
            if missing:
                raise ResponseMismatch(target, "%d of %d updates are not in the response"
                                       % (len(missing), len(batch)), missing)
            done.extend(record_id for record_id, _ in batch)
        return done

    def delete(self, table, record_ids):
        """Delete records by ID, ten a call. Returns the IDs Airtable reports
        deleted; one it does not report is a mismatch, never assumed gone."""
        deleted = []
        batches = list(self._batches(list(record_ids)))
        for number, batch in enumerate(batches, 1):
            target = "airtable delete from %s, batch %d of %d" % (table, number, len(batches))
            payload = self._call("DELETE", table, target, repeatable=False,
                                 params=[("records[]", record_id) for record_id in batch])
            got = {r.get("id") for r in payload.get("records") or [] if r.get("deleted")}
            missing = [record_id for record_id in batch if record_id not in got]
            if missing:
                raise ResponseMismatch(target, "%d of %d deletions are not confirmed"
                                       % (len(missing), len(batch)), missing)
            deleted.extend(batch)
        return deleted
