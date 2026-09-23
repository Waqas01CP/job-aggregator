"""The Airtable client, tested from ADR-0034, ADR-0035, ADR-0004 and Brief 6.

No test here touches the network. The transport is injected, and every
identifier below is made up for the test.

The backoff and breaker cases here are deliberate duplicates in kind of the
fetch module's. ADR-0034's Confirmation breaks the shared backoff once and
requires both modules' tests to fail; that only means something if both
suites exercise it.
"""

import inspect
import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.airtable import (API_ROOT, PIPELINE_FIELDS, AirtableClient,
                          AirtableConfigError, CallBudgetExhausted, ResponseMismatch,
                          month_to_date)
from src.resilience import CircuitOpen, PermanentError, TransientError

SRC = Path(__file__).resolve().parent.parent / "src"
TOKEN = "patFAKEFAKEFAKE.0123456789abcdef"
BASE = "appFAKEBASE000001"
TABLE = "tblFAKETABLE00001"
TEST_TABLE = "tblFAKETESTTAB001"

# ADR-0035's ten, written out by hand so a change to PIPELINE_FIELDS has to
# change this too. The set a mutation adding Status must break.
TEN = {"Title", "Employer", "Location", "Link", "Published", "First seen",
       "Order date", "Board", "Matched term", "Identity"}


class FakeResponse:
    def __init__(self, status_code, body=None, headers=None):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.headers = headers or {}

    def json(self):
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


class FakeSession:
    """Returns queued responses in order. A queued Exception is raised, which
    is how a dropped connection is simulated. A queued callable is called with
    the request, so a response can echo what was sent. Every call it receives
    is recorded, which is how the tests see that only PATCH is ever sent."""

    def __init__(self, queue):
        self.queue = list(queue)
        self.calls = []

    def request(self, method, url, params=None, json=None, headers=None, timeout=None):
        call = {"method": method, "url": url, "params": params, "json": json,
                "headers": headers, "timeout": timeout}
        self.calls.append(call)
        item = self.queue.pop(0) if self.queue else echo
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(call)
        return item


def echo(call):
    """What a successful upsert answers: the records it was sent, each with a
    made-up record ID."""
    records = [{"id": "rec%014d" % i, "fields": r["fields"]}
               for i, r in enumerate((call["json"] or {}).get("records", []))]
    return FakeResponse(200, {"records": records,
                              "createdRecords": [r["id"] for r in records],
                              "updatedRecords": []})


def client(queue=(), **kw):
    """Pacing and sleeping disabled, so tests do not wait."""
    slept = []
    kw.setdefault("min_interval", 0)
    c = AirtableClient(TOKEN, BASE, TABLE, session=FakeSession(queue),
                       sleep=slept.append, **kw)
    c.slept = slept
    return c


def row(i):
    return {"Title": "Role %d" % i, "Employer": "Acme", "Location": "Lahore",
            "Link": "https://example.test/%d" % i, "Published": "2026-09-20T10:00:00.000Z",
            "First seen": "2026-09-21T10:00:00.000Z", "Order date": "2026-09-20T10:00:00.000Z",
            "Board": "greenhouse:acme", "Matched term": "ai engineer",
            "Identity": "greenhouse:%d" % i}


def rows(n):
    return [row(i) for i in range(n)]


def env(**overrides):
    base = {"AIRTABLE_TOKEN": TOKEN, "AIRTABLE_BASE_ID": BASE,
            "AIRTABLE_TABLE_ID": TABLE, "AIRTABLE_TEST_TABLE_ID": TEST_TABLE}
    base.update(overrides)
    return base


class TestTheTenFields(unittest.TestCase):
    def test_the_sent_set_is_exactly_adr_0035s_ten(self):
        """The guard against the worst failure available here. An upsert
        overwrites every field it sends, so an eleventh field is somebody
        else's data."""
        self.assertEqual(set(PIPELINE_FIELDS), TEN)
        c = client()
        c.upsert(rows(12))
        for call in c._session.calls:
            for record in call["json"]["records"]:
                self.assertEqual(set(record["fields"]), TEN)

    def test_status_is_refused_before_anything_is_sent(self):
        """Ruling 1, 2026-09-23: the pipeline never writes Status. A write
        would also restart the fifteen-day clock on Classified at."""
        record = row(1)
        record["Status"] = "not fit"
        c = client()
        with self.assertRaises(ValueError):
            c.upsert([record])
        self.assertEqual(c._session.calls, [])

    def test_a_record_missing_one_of_the_ten_is_refused(self):
        record = row(1)
        del record["Matched term"]
        c = client()
        with self.assertRaises(ValueError):
            c.upsert([record])
        self.assertEqual(c._session.calls, [])

    def test_an_empty_published_is_sent_as_empty(self):
        """A platform with no publication date sends an empty Published,
        which the brief expects; the field is still one of the ten."""
        record = row(1)
        record["Published"] = None
        c = client()
        c.upsert([record])
        self.assertIsNone(c._session.calls[0]["json"]["records"][0]["fields"]["Published"])


class TestRequestShape(unittest.TestCase):
    def test_upsert_is_a_patch_matching_on_identity(self):
        """Confirmed against Airtable's documentation 2026-09-23: PATCH with
        performUpsert.fieldsToMergeOn, fields wrapped per record."""
        c = client()
        c.upsert(rows(2))
        call = c._session.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(call["url"], "%s/%s/%s" % (API_ROOT, BASE, TABLE))
        self.assertEqual(call["json"]["performUpsert"], {"fieldsToMergeOn": ["Identity"]})
        self.assertEqual(call["json"]["records"][0], {"fields": row(0)})

    def test_the_token_travels_in_the_header_and_nowhere_else(self):
        c = client()
        c.upsert(rows(1))
        call = c._session.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertNotIn(TOKEN, call["url"])
        self.assertNotIn(TOKEN, json.dumps(call["json"]))

    def test_timeout_is_always_set(self):
        """A request with no timeout can hang a scheduled run forever."""
        c = client()
        c.upsert(rows(1))
        self.assertTrue(c._session.calls[0]["timeout"])

    def test_upserts_go_ten_to_a_call(self):
        """ADR-0004 and ADR-0035. 23 rows are three calls, never 23 and never
        one call Airtable would reject."""
        c = client()
        c.upsert(rows(23))
        self.assertEqual([len(call["json"]["records"]) for call in c._session.calls],
                         [10, 10, 3])
        self.assertEqual(c.calls_used, 3)
        self.assertEqual(c.rows_sent, 23)


class TestNoReadPath(unittest.TestCase):
    """Ruling 4, 2026-09-23: the projection performs no reads at all. Made
    checkable: the client has one public verb, it sends only PATCH, and its
    source names no read method."""

    def test_the_only_public_verb_is_upsert(self):
        public = {name for name, member in inspect.getmembers(AirtableClient)
                  if callable(member) and not name.startswith("_")}
        self.assertEqual(public, {"upsert", "counters", "redact", "from_env"})

    def test_only_patch_reaches_the_wire(self):
        c = client([FakeResponse(429), FakeResponse(503), echo])
        c.upsert(rows(15))
        self.assertEqual({call["method"] for call in c._session.calls}, {"PATCH"})

    def test_the_source_names_no_read_method(self):
        source = (SRC / "airtable.py").read_text(encoding="utf-8")
        self.assertEqual(READ_METHODS.findall(source), [])

    def test_the_read_check_can_fail(self):
        self.assertTrue(READ_METHODS.findall('self._session.request("GET", url)'))
        self.assertTrue(READ_METHODS.findall("self._session.get(url)"))


class TestUpsertGuards(unittest.TestCase):
    def test_a_record_with_no_identity_is_refused_before_any_call(self):
        """An upsert with nothing to match on is a create, and a retried
        create duplicates. The whole batch is refused, and nothing is sent."""
        records = rows(3)
        records[1]["Identity"] = ""
        c = client()
        with self.assertRaises(ValueError):
            c.upsert(records)
        self.assertEqual(c._session.calls, [])

    def test_two_records_sharing_an_identity_are_refused(self):
        """Airtable fails an upsert whose key matches more than one record;
        two in one call would be the pipeline's own doing."""
        c = client()
        with self.assertRaises(ValueError):
            c.upsert(rows(2) + rows(1))
        self.assertEqual(c._session.calls, [])

    def test_the_response_is_matched_by_key_not_by_position(self):
        """The case that defeats a count check: the same number of records
        comes back, one of them a different identity."""
        def wrong_one(call):
            response = echo(call)
            response._body["records"][1]["fields"]["Identity"] = "greenhouse:999"
            return response
        c = client([wrong_one])
        with self.assertRaises(ResponseMismatch) as caught:
            c.upsert(rows(3))
        self.assertEqual(caught.exception.unaccounted, ["greenhouse:1"])
        self.assertEqual(c.rows_sent, 0)

    def test_created_and_updated_ids_are_reported(self):
        c = client()
        result = c.upsert(rows(2))
        self.assertEqual(len(result["created"]), 2)
        self.assertEqual(result["updated"], [])


class TestRateLimitAndBackoff(unittest.TestCase):
    def test_a_429_waits_thirty_seconds_then_retries(self):
        """ADR-0034, and Airtable's rate-limit page: wait 30 seconds."""
        c = client([FakeResponse(429), echo])
        c.upsert(rows(1))
        self.assertEqual(c.slept, [30.0])
        self.assertEqual(c.calls_used, 2)

    def test_a_longer_retry_after_is_honoured(self):
        c = client([FakeResponse(429, headers={"Retry-After": "45"}), echo])
        c.upsert(rows(1))
        self.assertEqual(c.slept, [45.0])

    def test_a_server_error_backs_off_exponentially(self):
        """The shared backoff, seen from this client. With base 2 the waits
        are 1 then 2 seconds."""
        c = client([FakeResponse(503), FakeResponse(503), echo], backoff_base=2.0)
        c.upsert(rows(1))
        self.assertEqual(c.slept, [1.0, 2.0])
        self.assertEqual(c.retries, 2)

    def test_an_upsert_is_retried_after_an_unknown_outcome(self):
        """Safe to repeat: the retry matches what the first attempt made."""
        c = client([OSError("connection reset"), echo])
        c.upsert(rows(1))
        self.assertEqual(len(c._session.calls), 2)

    def test_the_client_paces_under_five_a_second(self):
        """ADR-0004: under five requests a second per base. Two calls with no
        time passing between them are held a quarter of a second apart."""
        clock = [100.0]
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            clock[0] += seconds

        c = AirtableClient(TOKEN, BASE, TABLE, session=FakeSession([]), sleep=sleep,
                           now=lambda: clock[0])
        c.upsert(rows(11))
        self.assertEqual(len(slept), 1)
        self.assertGreater(slept[0], 0.2)


class TestClassification(unittest.TestCase):
    def test_422_is_not_retried(self):
        c = client([FakeResponse(422), echo])
        with self.assertRaises(PermanentError) as caught:
            c.upsert(rows(1))
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(c.calls_used, 1)

    def test_401_is_not_retried(self):
        c = client([FakeResponse(401), echo])
        with self.assertRaises(PermanentError):
            c.upsert(rows(1))
        self.assertEqual(c.calls_used, 1)


class TestMonthlyBudget(unittest.TestCase):
    def test_the_month_ceiling_refuses_without_sending(self):
        """ADR-0034: a budget counted per month. Two calls left means the
        third is refused, and refused before it reaches the wire."""
        c = client(monthly_ceiling=1000, used_this_month=998)
        c.upsert(rows(20))
        with self.assertRaises(CallBudgetExhausted):
            c.upsert(rows(1))
        self.assertEqual(len(c._session.calls), 2)
        self.assertEqual(c.refused, 1)
        self.assertEqual(c.month_remaining, 0)

    def test_retries_count_against_the_month(self):
        c = client([FakeResponse(503), FakeResponse(503), echo])
        c.upsert(rows(1))
        self.assertEqual(c.calls_used, 3)

    def test_counters_report_the_month_the_run_and_the_rows(self):
        c = client(used_this_month=40)
        c.upsert(rows(11))
        counters = c.counters()
        self.assertEqual(counters["calls_used"], 2)
        self.assertEqual(counters["rows_sent"], 11)
        self.assertEqual(counters["month_to_date_before_run"], 40)
        self.assertEqual(counters["month_remaining"], 1000 - 42)


class TestMonthToDate(unittest.TestCase):
    def test_sums_only_the_current_utc_month(self):
        """The case built to defeat it: a large count from the previous month
        must not be charged to this one."""
        logs = [{"run_at": "2026-08-31T23:59:00Z", "airtable": {"calls_used": 900}},
                {"run_at": "2026-09-01T00:01:00Z", "airtable": {"calls_used": 4}},
                {"run_at": "2026-09-23T03:36:36Z", "airtable": {"calls_used": 3}}]
        self.assertEqual(month_to_date(logs, "2026-09-23T12:00:00Z"), 7)

    def test_a_log_from_before_this_client_counts_zero(self):
        logs = [{"run_at": "2026-09-22T17:33:36Z", "totals": {}}]
        self.assertEqual(month_to_date(logs, "2026-09-23T12:00:00Z"), 0)


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_consecutive_failures_and_refuses_without_spending(self):
        c = client([FakeResponse(500)] * 9, breaker_threshold=3, max_attempts=3)
        with self.assertRaises(TransientError):
            c.upsert(rows(1))
        self.assertTrue(c.circuit_is_open)
        with self.assertRaises(CircuitOpen):
            c.upsert(rows(1))
        self.assertEqual(c.calls_used, 3, "a refused call must not spend budget")

    def test_any_success_resets_it(self):
        c = client([FakeResponse(500), echo], breaker_threshold=2, max_attempts=1)
        with self.assertRaises(TransientError):
            c.upsert(rows(1))
        self.assertEqual(c.consecutive_failures, 1)
        c.upsert(rows(1))
        self.assertEqual(c.consecutive_failures, 0)


class TestTestModeNeverReachesProduction(unittest.TestCase):
    """Brief 6: test mode resolves to AIRTABLE_TEST_TABLE_ID and can never
    resolve to AIRTABLE_TABLE_ID. An earlier handoff believed a test run left
    production alone, and it would not have."""

    def test_test_mode_takes_the_test_table(self):
        c = AirtableClient.from_env(True, env(), session=FakeSession([]), min_interval=0)
        c.upsert(rows(1))
        self.assertTrue(c._session.calls[0]["url"].endswith("/" + TEST_TABLE))

    def test_production_takes_the_production_table(self):
        c = AirtableClient.from_env(False, env(), session=FakeSession([]), min_interval=0)
        c.upsert(rows(1))
        self.assertTrue(c._session.calls[0]["url"].endswith("/" + TABLE))

    def test_a_missing_test_table_is_refused_never_replaced_by_production(self):
        """The case built to defeat a fallback: the production ID is right
        there, and test mode must still refuse."""
        with self.assertRaises(AirtableConfigError) as caught:
            AirtableClient.from_env(True, env(AIRTABLE_TEST_TABLE_ID=""))
        self.assertIn("AIRTABLE_TEST_TABLE_ID", str(caught.exception))

    def test_a_test_table_equal_to_production_is_refused(self):
        with self.assertRaises(AirtableConfigError):
            AirtableClient.from_env(True, env(AIRTABLE_TEST_TABLE_ID=TABLE))

    def test_production_does_not_need_the_test_table(self):
        AirtableClient.from_env(False, env(AIRTABLE_TEST_TABLE_ID=""))


class TestNoSecretInAnError(unittest.TestCase):
    """This repository is public and an error's text can reach a run log on
    the public data branch. The token is a credential; base and table IDs are
    secrets here."""

    def assertClean(self, error):
        text = str(error)
        for secret in (TOKEN, BASE, TABLE, TEST_TABLE):
            self.assertNotIn(secret, text)

    def test_permanent_and_transient_errors(self):
        for queue in ([FakeResponse(404)], [FakeResponse(503)] * 3):
            c = client(queue)
            with self.assertRaises((PermanentError, TransientError)) as caught:
                c.upsert(rows(1))
            self.assertClean(caught.exception)

    def test_a_transport_error_quoting_the_url_loses_it(self):
        """The case built to defeat a message-level guard: requests quotes the
        URL in its connection errors, and the URL holds the base and table.
        Only the exception's class name survives."""
        leaky = ConnectionError("HTTPSConnectionPool(host='api.airtable.com'): Max retries "
                                "exceeded with url: /v0/%s/%s (Bearer %s)" % (BASE, TABLE, TOKEN))
        c = client([leaky] * 3)
        with self.assertRaises(TransientError) as caught:
            c.upsert(rows(1))
        self.assertClean(caught.exception)
        self.assertIn("ConnectionError", str(caught.exception))

    def test_redact_scrubs_every_secret(self):
        c = client()
        text = c.redact("token %s base %s table %s" % (TOKEN, BASE, TABLE))
        for secret in (TOKEN, BASE, TABLE):
            self.assertNotIn(secret, text)

    def test_config_errors_do_not_echo_values(self):
        for args in ((TOKEN, TABLE, TABLE), (TOKEN, BASE, "Jobs")):
            with self.assertRaises(AirtableConfigError) as caught:
                AirtableClient(*args)
            self.assertClean(caught.exception)
            self.assertNotIn("Jobs", str(caught.exception))

    def test_an_empty_secret_is_refused_by_name(self):
        """A mistyped secret name gives an empty value, not an error. It must
        fail here, naming which, before anything is sent."""
        with self.assertRaises(AirtableConfigError) as caught:
            AirtableClient.from_env(False, env(AIRTABLE_TOKEN="  "))
        self.assertIn("AIRTABLE_TOKEN", str(caught.exception))
        self.assertClean(caught.exception)


# ADR-0034's Confirmation, first half: "Grep the Airtable client for any import
# of the fetch module's request function, and the fetch module for any mention
# of a token or a write verb. Either is a violation."
FETCH_IMPORT = re.compile(r"^\s*(?:from\s+[.\w]*http_client\s+import|import\s+[.\w]*http_client)",
                          re.M)
WRITE_SIGNS = [re.compile(p, re.I) for p in (
    r"\btoken\b", r"\bauthorization\b", r"\.(?:post|patch|put|delete)\(",
    r"['\"](?:post|patch|put|delete)['\"]")]
MAKES_REQUESTS = re.compile(r"^\s*(?:import\s+requests|from\s+requests\s+import)", re.M)
# Ruling 4 made checkable: a read verb or a read call on the session.
READ_METHODS = re.compile(r"['\"]GET['\"]|\._session\.(?:get|head)\(")


def fetch_imports(source):
    return FETCH_IMPORT.findall(source)


def write_signs(source):
    return [m.group(0) for p in WRITE_SIGNS for m in p.finditer(source)]


class TestTheExceptionStaysScoped(unittest.TestCase):
    def read(self, name):
        return (SRC / name).read_text(encoding="utf-8")

    def test_the_airtable_client_does_not_import_the_fetch_module(self):
        self.assertEqual(fetch_imports(self.read("airtable.py")), [])

    def test_the_fetch_module_carries_no_token_and_no_write_verb(self):
        self.assertEqual(write_signs(self.read("http_client.py")), [])

    def test_the_shared_module_makes_no_request_itself(self):
        """What is shared is logic. A shared module holding a session would
        be the god-module ADR-0034 rejected, arriving by another door."""
        self.assertIsNone(MAKES_REQUESTS.search(self.read("resilience.py")))

    def test_the_checks_can_fail(self):
        """The cases built to defeat them. Without these, three empty lists
        prove only that the patterns match nothing."""
        self.assertTrue(fetch_imports("from .http_client import HttpClient\n"))
        self.assertTrue(fetch_imports("import src.http_client\n"))
        self.assertTrue(write_signs('self._session.post(url, json=body)'))
        self.assertTrue(write_signs('method = "PATCH"'))
        self.assertTrue(write_signs('headers["Authorization"] = token'))
        self.assertTrue(MAKES_REQUESTS.search("import requests\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
