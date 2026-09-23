"""The Airtable client, tested from ADR-0034, ADR-0035 and ADR-0004.

No test here touches the network. The transport is injected, and every
identifier below is made up for the test.

The backoff and breaker cases here are deliberate duplicates in kind of the
fetch module's. ADR-0034's Confirmation breaks the shared backoff once and
requires both modules' tests to fail; that only means something if both
suites exercise it.
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.airtable_client import (API_ROOT, AirtableClient, AirtableConfigError,
                                 CallBudgetExhausted, ResponseMismatch,
                                 month_to_date)
from src.resilience import CircuitOpen, PermanentError, TransientError

SRC = Path(__file__).resolve().parent.parent / "src"
TOKEN = "patFAKEFAKEFAKE.0123456789abcdef"
BASE = "appFAKEBASE000001"
TABLE = "tblFAKETABLE00001"


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
    the request, so a response can echo what was sent."""

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
    """What a successful upsert or create answers: the records it was sent,
    each with a made-up record ID."""
    records = [{"id": "rec%014d" % i, "fields": r["fields"]}
               for i, r in enumerate((call["json"] or {}).get("records", []))]
    return FakeResponse(200, {"records": records,
                              "createdRecords": [r["id"] for r in records],
                              "updatedRecords": []})


def deleted_all(call):
    return FakeResponse(200, {"records": [{"id": v, "deleted": True}
                                          for k, v in call["params"] if k == "records[]"]})


def client(queue=(), **kw):
    """Pacing and sleeping disabled, so tests do not wait."""
    slept = []
    kw.setdefault("min_interval", 0)
    c = AirtableClient(TOKEN, BASE, session=FakeSession(queue), sleep=slept.append, **kw)
    c.slept = slept
    return c


def rows(n):
    return [{"Identity": "greenhouse:%d" % i, "Title": "Role %d" % i} for i in range(n)]


class TestRequestShape(unittest.TestCase):
    def test_upsert_is_a_patch_matching_on_identity(self):
        """ADR-0035: upsert, matched on Identity, fields wrapped per record."""
        c = client()
        c.upsert_records(TABLE, rows(2))
        call = c._session.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(call["url"], "%s/%s/%s" % (API_ROOT, BASE, TABLE))
        self.assertEqual(call["json"]["performUpsert"], {"fieldsToMergeOn": ["Identity"]})
        self.assertEqual(call["json"]["records"][0],
                         {"fields": {"Identity": "greenhouse:0", "Title": "Role 0"}})

    def test_the_token_travels_in_the_header_and_nowhere_else(self):
        c = client()
        c.upsert_records(TABLE, rows(1))
        call = c._session.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertNotIn(TOKEN, call["url"])
        self.assertNotIn(TOKEN, json.dumps(call["json"]))

    def test_timeout_is_always_set(self):
        """A request with no timeout can hang a scheduled run forever."""
        c = client()
        c.upsert_records(TABLE, rows(1))
        self.assertTrue(c._session.calls[0]["timeout"])

    def test_the_client_sends_only_the_fields_it_is_given(self):
        """Field ownership is the projection's job (ADR-0035). The client adds
        nothing: a Status it was not given must not appear."""
        c = client()
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(set(c._session.calls[0]["json"]["records"][0]["fields"]),
                         {"Identity", "Title"})


class TestBatching(unittest.TestCase):
    def test_upserts_go_ten_to_a_call(self):
        """ADR-0004 and ADR-0035. 23 rows are three calls, never 23 and never
        one call Airtable would reject."""
        c = client()
        c.upsert_records(TABLE, rows(23))
        sizes = [len(call["json"]["records"]) for call in c._session.calls]
        self.assertEqual(sizes, [10, 10, 3])
        self.assertEqual(c.calls_used, 3)

    def test_deletes_go_ten_to_a_call(self):
        ids = ["rec%014d" % i for i in range(12)]
        c = client([deleted_all, deleted_all])
        self.assertEqual(c.delete_records(TABLE, ids), ids)
        self.assertEqual([len(call["params"]) for call in c._session.calls], [10, 2])


class TestUpsertGuards(unittest.TestCase):
    def test_a_record_with_no_identity_is_refused_before_any_call(self):
        """An upsert with nothing to match on is a create, and a retried
        create duplicates. The whole batch is refused, and nothing is sent."""
        records = rows(3)
        records[1]["Identity"] = ""
        c = client()
        with self.assertRaises(ValueError):
            c.upsert_records(TABLE, records)
        self.assertEqual(c._session.calls, [])

    def test_two_records_sharing_an_identity_are_refused(self):
        c = client()
        with self.assertRaises(ValueError):
            c.upsert_records(TABLE, rows(2) + rows(1))
        self.assertEqual(c._session.calls, [])

    def test_the_response_is_matched_by_key_not_by_position(self):
        """The case that defeats a count check: the same number of records
        comes back, one of them a different identity. Aligned by key, one sent
        record is unaccounted for."""
        def wrong_one(call):
            response = echo(call)
            response._body["records"][1]["fields"]["Identity"] = "greenhouse:999"
            return response
        c = client([wrong_one])
        with self.assertRaises(ResponseMismatch) as caught:
            c.upsert_records(TABLE, rows(3))
        self.assertEqual(caught.exception.unaccounted, [("greenhouse:1",)])

    def test_created_and_updated_ids_are_reported(self):
        c = client()
        result = c.upsert_records(TABLE, rows(2))
        self.assertEqual(len(result["created"]), 2)
        self.assertEqual(result["updated"], [])


class TestRateLimitAndBackoff(unittest.TestCase):
    def test_a_429_waits_thirty_seconds_then_retries(self):
        """ADR-0034: HTTP 429 then a required 30-second wait."""
        c = client([FakeResponse(429), echo])
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.slept, [30.0])
        self.assertEqual(c.calls_used, 2)

    def test_a_longer_retry_after_is_honoured(self):
        c = client([FakeResponse(429, headers={"Retry-After": "45"}), echo])
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.slept, [45.0])

    def test_a_server_error_backs_off_exponentially(self):
        """The shared backoff, seen from this client. With base 2 the waits
        are 1 then 2 seconds."""
        c = client([FakeResponse(503), FakeResponse(503), echo], backoff_base=2.0)
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.slept, [1.0, 2.0])
        self.assertEqual(c.retries, 2)

    def test_the_client_paces_itself_at_five_a_second(self):
        """ADR-0034: five requests per second per base. Two calls with no
        time passing between them must be held apart by 0.2 seconds."""
        clock = [100.0]
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            clock[0] += seconds

        c = AirtableClient(TOKEN, BASE, session=FakeSession([]), sleep=sleep,
                           now=lambda: clock[0])
        c.upsert_records(TABLE, rows(11))
        self.assertEqual(len(slept), 1)
        self.assertAlmostEqual(slept[0], 0.2)


class TestUnknownOutcomes(unittest.TestCase):
    def test_a_create_is_not_sent_again_after_a_server_error(self):
        """The first create may have landed. Sending it again is how ADR-0035's
        duplicate rows happen, so the failure is reported instead."""
        c = client([FakeResponse(503), echo])
        with self.assertRaises(TransientError):
            c.create_records(TABLE, rows(1))
        self.assertEqual(len(c._session.calls), 1)

    def test_a_create_is_not_sent_again_after_a_dropped_connection(self):
        c = client([OSError("connection reset"), echo])
        with self.assertRaises(TransientError):
            c.create_records(TABLE, rows(1))
        self.assertEqual(len(c._session.calls), 1)

    def test_a_create_is_retried_after_a_429(self):
        """Airtable says it did not act on a 429, so a retry cannot
        duplicate."""
        c = client([FakeResponse(429), echo])
        self.assertEqual(len(c.create_records(TABLE, rows(1))), 1)
        self.assertEqual(len(c._session.calls), 2)

    def test_a_create_response_short_of_what_was_sent_is_refused(self):
        def short(call):
            response = echo(call)
            response._body["records"].pop()
            return response
        c = client([short])
        with self.assertRaises(ResponseMismatch):
            c.create_records(TABLE, rows(2))

    def test_a_delete_is_not_sent_again_after_a_server_error(self):
        c = client([FakeResponse(500), deleted_all])
        with self.assertRaises(TransientError):
            c.delete_records(TABLE, ["rec00000000000001"])
        self.assertEqual(len(c._session.calls), 1)

    def test_an_upsert_is_retried_after_a_server_error(self):
        """The mirror: an upsert is safe to repeat, which is why it was
        chosen."""
        c = client([FakeResponse(502), echo])
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(len(c._session.calls), 2)

    def test_a_delete_not_confirmed_for_every_id_is_refused(self):
        def one_missing(call):
            ids = [v for k, v in call["params"] if k == "records[]"]
            return FakeResponse(200, {"records": [{"id": ids[0], "deleted": True}]})
        c = client([one_missing])
        with self.assertRaises(ResponseMismatch) as caught:
            c.delete_records(TABLE, ["rec00000000000001", "rec00000000000002"])
        self.assertEqual(caught.exception.unaccounted, ["rec00000000000002"])

    def test_an_id_returned_but_not_marked_deleted_is_refused(self):
        """The case the check above does not reach: every ID comes back, one
        of them with `deleted` false. Presence is not deletion. Added after
        the mutation that drops the `deleted` check survived without it."""
        def one_refused(call):
            ids = [v for k, v in call["params"] if k == "records[]"]
            return FakeResponse(200, {"records": [{"id": ids[0], "deleted": True},
                                                  {"id": ids[1], "deleted": False}]})
        c = client([one_refused])
        with self.assertRaises(ResponseMismatch) as caught:
            c.delete_records(TABLE, ["rec00000000000001", "rec00000000000002"])
        self.assertEqual(caught.exception.unaccounted, ["rec00000000000002"])

    def test_a_pipeline_identity_is_not_accepted_as_a_record_id(self):
        c = client()
        with self.assertRaises(ValueError):
            c.delete_records(TABLE, ["greenhouse:4975862101"])
        self.assertEqual(c._session.calls, [])


class TestClassification(unittest.TestCase):
    def test_422_is_not_retried(self):
        c = client([FakeResponse(422), echo])
        with self.assertRaises(PermanentError) as caught:
            c.upsert_records(TABLE, rows(1))
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(c.calls_used, 1)

    def test_401_is_not_retried(self):
        c = client([FakeResponse(401), echo])
        with self.assertRaises(PermanentError):
            c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.calls_used, 1)


class TestMonthlyBudget(unittest.TestCase):
    def test_the_month_ceiling_refuses_without_sending(self):
        """ADR-0034: a budget counted per month. Two calls left means the
        third is refused, and refused before it reaches the wire."""
        c = client(monthly_ceiling=1000, used_this_month=998)
        c.upsert_records(TABLE, rows(20))
        with self.assertRaises(CallBudgetExhausted):
            c.upsert_records(TABLE, rows(1))
        self.assertEqual(len(c._session.calls), 2)
        self.assertEqual(c.refused, 1)
        self.assertEqual(c.month_remaining, 0)

    def test_retries_count_against_the_month(self):
        c = client([FakeResponse(503), FakeResponse(503), echo])
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.calls_used, 3)

    def test_counters_report_the_month_and_the_run(self):
        c = client(used_this_month=40)
        c.upsert_records(TABLE, rows(11))
        counters = c.counters()
        self.assertEqual(counters["calls_used"], 2)
        self.assertEqual(counters["by_operation"], {"upsert": 2})
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
            c.upsert_records(TABLE, rows(1))
        self.assertTrue(c.circuit_is_open)
        with self.assertRaises(CircuitOpen):
            c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.calls_used, 3, "a refused call must not spend budget")

    def test_any_success_resets_it(self):
        c = client([FakeResponse(500), echo], breaker_threshold=2, max_attempts=1)
        with self.assertRaises(TransientError):
            c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.consecutive_failures, 1)
        c.upsert_records(TABLE, rows(1))
        self.assertEqual(c.consecutive_failures, 0)


class TestNoIdentifierInAnError(unittest.TestCase):
    """This repository is public and an error's text can reach a run log on
    the public data branch. Base, table and record IDs are secrets here, and
    the token is a credential."""

    def assertClean(self, error):
        text = str(error)
        for secret in (TOKEN, BASE, TABLE, "rec00000000000002"):
            self.assertNotIn(secret, text)

    def test_permanent_and_transient_errors(self):
        for queue in ([FakeResponse(404)], [FakeResponse(503)] * 3,
                      [OSError("reset")] * 3):
            c = client(queue)
            with self.assertRaises((PermanentError, TransientError)) as caught:
                c.upsert_records(TABLE, rows(1))
            self.assertClean(caught.exception)

    def test_a_mismatch_names_counts_not_ids(self):
        def none_deleted(call):
            return FakeResponse(200, {"records": []})
        c = client([none_deleted])
        with self.assertRaises(ResponseMismatch) as caught:
            c.delete_records(TABLE, ["rec00000000000002"])
        self.assertClean(caught.exception)

    def test_config_errors_do_not_echo_values(self):
        with self.assertRaises(AirtableConfigError) as caught:
            AirtableClient(TOKEN, TABLE)
        self.assertClean(caught.exception)


class TestFromEnvironment(unittest.TestCase):
    def test_an_empty_secret_is_refused_by_name(self):
        """A mistyped secret name gives an empty value, not an error. It must
        fail here, naming which, before anything is sent."""
        with self.assertRaises(AirtableConfigError) as caught:
            AirtableClient.from_env({"AIRTABLE_TOKEN": "  ", "AIRTABLE_BASE_ID": BASE})
        self.assertIn("AIRTABLE_TOKEN", str(caught.exception))
        self.assertNotIn(BASE, str(caught.exception))

    def test_a_table_id_in_the_base_secret_is_refused(self):
        with self.assertRaises(AirtableConfigError):
            AirtableClient.from_env({"AIRTABLE_TOKEN": TOKEN, "AIRTABLE_BASE_ID": TABLE})

    def test_valid_secrets_build_a_client(self):
        c = AirtableClient.from_env({"AIRTABLE_TOKEN": TOKEN, "AIRTABLE_BASE_ID": BASE})
        self.assertEqual(c.calls_used, 0)

    def test_a_table_name_is_refused(self):
        """IDs only: a name costs a lookup and breaks silently on a rename."""
        c = client()
        with self.assertRaises(ValueError):
            c.upsert_records("Jobs", rows(1))


class TestListRecords(unittest.TestCase):
    def test_follows_the_offset_and_counts_every_page(self):
        pages = [FakeResponse(200, {"records": [{"id": "rec1"}], "offset": "page2"}),
                 FakeResponse(200, {"records": [{"id": "rec2"}]})]
        c = client(pages)
        records = c.list_records(TABLE, fields=["Status", "Identity"],
                                 formula="NOT({Status} = '')")
        self.assertEqual([r["id"] for r in records], ["rec1", "rec2"])
        self.assertEqual(c.calls_used, 2)
        first, second = c._session.calls
        self.assertEqual(first["method"], "GET")
        self.assertIn(("fields[]", "Status"), first["params"])
        self.assertIn(("pageSize", 100), first["params"])
        self.assertIn(("offset", "page2"), second["params"])
        self.assertNotIn("offset", [k for k, _ in first["params"]])


# ADR-0034's Confirmation, first half: "Grep the Airtable client for any import
# of the fetch module's request function, and the fetch module for any mention
# of a token or a write verb. Either is a violation."
FETCH_IMPORT = re.compile(r"^\s*(?:from\s+[.\w]*http_client\s+import|import\s+[.\w]*http_client)",
                          re.M)
WRITE_SIGNS = [re.compile(p, re.I) for p in (
    r"\btoken\b", r"\bauthorization\b", r"\.(?:post|patch|put|delete)\(",
    r"['\"](?:post|patch|put|delete)['\"]")]
MAKES_REQUESTS = re.compile(r"^\s*(?:import\s+requests|from\s+requests\s+import)", re.M)


def fetch_imports(source):
    return FETCH_IMPORT.findall(source)


def write_signs(source):
    return [m.group(0) for p in WRITE_SIGNS for m in p.finditer(source)]


class TestTheExceptionStaysScoped(unittest.TestCase):
    def read(self, name):
        return (SRC / name).read_text(encoding="utf-8")

    def test_the_airtable_client_does_not_import_the_fetch_module(self):
        self.assertEqual(fetch_imports(self.read("airtable_client.py")), [])

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
