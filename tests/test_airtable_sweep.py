"""The sweep's Airtable client, tested from ADR-0050, ADR-0035 and ADR-0033.

Against the in-memory base in `tests/fake_airtable.py`. No network.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.airtable import AirtableConfigError, CallBudgetExhausted, ResponseMismatch
from src.airtable_sweep import (CLASSIFICATION_TABLES, COPY_FIELDS, JOBS, TABLE_SECRETS,
                                SweepClient)
from src.resilience import HttpError, TransientError
from tests.fake_airtable import FakeBase, Response

TOKEN = "patFAKEFAKEFAKE.0123456789abcdef"
BASE = "appFAKEBASE000001"
PROD = {JOBS: "tblPRODJOBS000001", "rejected-not-a-fit": "tblPRODNOTFIT0001",
        "rejected-poor-filtering": "tblPRODPOORFILT01", "accepted": "tblPRODACCEPT0001"}
TEST = {JOBS: "tblTESTJOBS000001", "rejected-not-a-fit": "tblTESTNOTFIT0001",
        "rejected-poor-filtering": "tblTESTPOORFILT01", "accepted": "tblTESTACCEPT0001"}


def env(**overrides):
    e = {"AIRTABLE_TOKEN": TOKEN, "AIRTABLE_BASE_ID": BASE}
    e.update({TABLE_SECRETS[False][k]: v for k, v in PROD.items()})
    e.update({TABLE_SECRETS[True][k]: v for k, v in TEST.items()})
    e.update(overrides)
    return e


def client(base=None, tables=PROD, **kw):
    kw.setdefault("min_interval", 0)
    return SweepClient(TOKEN, BASE, tables, session=base or FakeBase({tables[JOBS]}),
                       sleep=lambda s: None, **kw)


def copy(i):
    fields = {name: None for name in COPY_FIELDS}
    fields.update(Title="Role %d" % i, Identity="greenhouse:%d" % i, Board="greenhouse:acme")
    return fields


class Flaky:
    """Answers with the given statuses first, then passes to the base."""

    def __init__(self, base, statuses):
        self.base, self.statuses, self.calls = base, list(statuses), []

    def request(self, method, url, **kw):
        self.calls.append(method)
        if self.statuses:
            return Response(self.statuses.pop(0), {})
        return self.base.request(method, url, **kw)


class TestTheTablesAMode(unittest.TestCase):
    def test_test_mode_reaches_only_the_test_tables(self):
        """ADR-0033 and Brief 7: the sweep must reach the three test tables
        and never the production three."""
        base = FakeBase({TEST[JOBS]})
        c = SweepClient.from_env(True, environ=env(), session=base, min_interval=0,
                                 sleep=lambda s: None)
        c.list_records(JOBS, ("Identity",))
        for t in CLASSIFICATION_TABLES:
            c.list_records(t, ("Identity",))
        c.create_copies("accepted", [copy(1)])
        touched = {call["table"] for call in base.calls}
        self.assertEqual(touched, set(TEST.values()))
        self.assertFalse(touched & set(PROD.values()))

    def test_production_reaches_only_the_production_tables(self):
        base = FakeBase({PROD[JOBS]})
        c = SweepClient.from_env(False, environ=env(), session=base, min_interval=0,
                                 sleep=lambda s: None)
        for t in (JOBS,) + CLASSIFICATION_TABLES:
            c.list_records(t, ("Identity",))
        self.assertEqual({call["table"] for call in base.calls}, set(PROD.values()))

    def test_a_test_table_equal_to_a_production_one_is_refused(self):
        with self.assertRaises(AirtableConfigError) as caught:
            SweepClient.from_env(True, environ=env(AIRTABLE_ACCEPTED_TEST_TABLE_ID=PROD["accepted"]))
        self.assertIn("AIRTABLE_ACCEPTED_TEST_TABLE_ID", str(caught.exception))
        self.assertNotIn(PROD["accepted"], str(caught.exception))

    def test_a_production_table_equal_to_a_test_one_is_refused(self):
        """The reverse of the case above: a production run never writes the
        test tables either."""
        with self.assertRaises(AirtableConfigError) as caught:
            SweepClient.from_env(False, environ=env(AIRTABLE_NOT_A_FIT_TABLE_ID=TEST["rejected-not-a-fit"]))
        self.assertIn("AIRTABLE_NOT_A_FIT_TABLE_ID", str(caught.exception))
        self.assertNotIn(TEST["rejected-not-a-fit"], str(caught.exception))

    def test_two_tables_of_one_mode_sharing_an_id_are_refused(self):
        """The audit of 2026-09-25, F2: `accepted` given the `Jobs` table's ID
        made every unmarked `Jobs` row look like a stale copy, and step 1
        deleted them. Any pair, either mode, refused before a request."""
        keys = (JOBS,) + CLASSIFICATION_TABLES
        for mode, tables in ((False, PROD), (True, TEST)):
            for i, a in enumerate(keys):
                for b in keys[i + 1:]:
                    with self.subTest(mode=mode, pair=(a, b)):
                        base = FakeBase({tables[JOBS]})
                        with self.assertRaises(AirtableConfigError) as caught:
                            client(base, tables=dict(tables, **{b: tables[a]}))
                        self.assertIn(a, str(caught.exception))
                        self.assertNotIn(tables[a], str(caught.exception))
                        self.assertEqual(base.calls, [])
        with self.assertRaises(AirtableConfigError):
            SweepClient.from_env(False, environ=env(AIRTABLE_ACCEPTED_TABLE_ID=PROD[JOBS]))

    def test_a_missing_table_is_refused_by_name(self):
        with self.assertRaises(AirtableConfigError) as caught:
            SweepClient.from_env(False, environ=env(AIRTABLE_NOT_A_FIT_TABLE_ID=""))
        self.assertIn("AIRTABLE_NOT_A_FIT_TABLE_ID", str(caught.exception))


class TestOnlyWhatThePipelineOwns(unittest.TestCase):
    """ADR-0035: the operator's fields are never sent. Each case is refused
    before any request."""

    def test_a_copy_carrying_status_or_a_reason_is_refused(self):
        for extra in ({"Status": "accepted"}, {"Stage": "applied"},
                      {"Pipeline reason": "duplicate"}, {"Classified": "2026-09-01"}):
            with self.subTest(field=list(extra)[0]):
                base = FakeBase({PROD[JOBS]})
                c = client(base)
                with self.assertRaises(ValueError):
                    c.create_copies("rejected-poor-filtering", [dict(copy(1), **extra)])
                self.assertEqual(base.calls, [])

    def test_a_copy_never_goes_to_jobs(self):
        c = client()
        with self.assertRaises(ValueError):
            c.create_copies(JOBS, [copy(1)])

    def test_the_only_field_written_to_jobs_is_closed(self):
        base = FakeBase({PROD[JOBS]})
        record_id = base.seed(PROD[JOBS], {"Identity": "greenhouse:1", "Status": "accepted"})
        c = client(base)
        c.set_closed([(record_id, "2026-09-20")])
        sent = base.calls[-1]["json"]["records"]
        self.assertEqual([set(r["fields"]) for r in sent], [{"Closed"}])
        self.assertEqual(base.rows(PROD[JOBS])[0]["Status"], "accepted")


class TestReadsAndWrites(unittest.TestCase):
    def test_a_read_pages_by_one_hundred(self):
        base = FakeBase({PROD[JOBS]})
        for i in range(250):
            base.seed(PROD[JOBS], {"Identity": "greenhouse:%d" % i})
        c = client(base)
        self.assertEqual(len(c.list_records(JOBS, ("Identity",))), 250)
        self.assertEqual(c.calls_used, 3)

    def test_an_unconfirmed_delete_is_a_mismatch(self):
        """A 200 that confirms fewer deletions than were asked is not
        success. The base now refuses a missing record outright, so the
        short answer is given in its place."""
        base = FakeBase({PROD[JOBS]})
        record_id = base.seed(PROD["accepted"], {"Identity": "greenhouse:1"})
        base.fail = lambda call: (Response(200, {"records": []})
                                  if call["method"] == "DELETE" else None)
        c = client(base)
        with self.assertRaises(ResponseMismatch):
            c.delete("accepted", [record_id])

    def test_a_delete_of_a_record_already_gone_fails(self):
        base = FakeBase({PROD[JOBS]})
        c = client(base)
        with self.assertRaises(HttpError):
            c.delete("accepted", ["rec00000000000404"])

    def test_every_write_goes_ten_records_a_call(self):
        """ADR-0050's Assumptions give Airtable's limit as ten records a call;
        the base refuses more. The audit of 2026-09-25, F5."""
        base = FakeBase({PROD[JOBS]})
        c = client(base)
        c.create_copies("rejected-poor-filtering", [copy(i) for i in range(25)])
        ids = [r["_id"] for r in base.rows(PROD["rejected-poor-filtering"])]
        jobs = [base.seed(PROD[JOBS], {"Identity": "greenhouse:%d" % i}) for i in range(25)]
        c.set_closed([(j, "2026-09-20") for j in jobs])
        c.delete("rejected-poor-filtering", ids)
        for method in ("POST", "PATCH", "DELETE"):
            with self.subTest(method=method):
                sizes = [len(call["json"]["records"]) if method != "DELETE" else
                         len([k for k, _ in call["params"] if k == "records[]"])
                         for call in base.calls if call["method"] == method]
                self.assertEqual(sizes, [10, 10, 5])
        self.assertEqual(base.rows(PROD["rejected-poor-filtering"]), [])

    def test_a_read_that_fails_after_its_first_page_returns_nothing(self):
        """A partial read is never acted on: a copy on the unread page would
        otherwise be taken as missing, and its reason or `Stage` lost from the
        store for good. The audit of 2026-09-25, F5."""
        base = FakeBase({PROD[JOBS]})
        for i in range(150):
            base.seed(PROD["accepted"], {"Identity": "greenhouse:%d" % i})

        def second_page(call):
            params = call["params"] or []
            if call["method"] == "GET" and any(k == "offset" for k, _ in params):
                return Response(422, {"error": "INVALID_OFFSET_VALUE"})
        base.fail = second_page
        c = client(base)
        with self.assertRaises(HttpError):
            c.list_records("accepted", ("Identity",))

    def test_a_create_is_not_retried_after_an_unknown_outcome(self):
        """A 503 after a create may mean the copy was made. Retrying could
        make a second, so the error is raised and nothing is sent again."""
        base = FakeBase({PROD[JOBS]})
        flaky = Flaky(base, [503])
        c = client(flaky)
        with self.assertRaises(TransientError):
            c.create_copies("accepted", [copy(1)])
        self.assertEqual(flaky.calls, ["POST"])

    def test_a_create_is_retried_after_a_429(self):
        base = FakeBase({PROD[JOBS]})
        flaky = Flaky(base, [429])
        c = client(flaky)
        c.create_copies("accepted", [copy(1)])
        self.assertEqual(flaky.calls, ["POST", "POST"])
        self.assertEqual(len(base.rows(PROD["accepted"])), 1)

    def test_the_month_ceiling_refuses_without_sending(self):
        base = FakeBase({PROD[JOBS]})
        c = client(base, monthly_ceiling=10, used_this_month=10)
        with self.assertRaises(CallBudgetExhausted):
            c.list_records(JOBS, ("Identity",))
        self.assertEqual(base.calls, [])

    def test_no_secret_reaches_an_error(self):
        c = client()
        text = c.redact("boom %s %s %s" % (TOKEN, BASE, " ".join(PROD.values())))
        for secret in [TOKEN, BASE] + list(PROD.values()):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
