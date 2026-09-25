"""The sweep, tested from ADR-0050's six steps and Brief 7's verification list.

End to end against the in-memory base in `tests/fake_airtable.py`, with real
store files in a temporary directory. No network.

**How "durable" is simulated.** A sweep verifies a deletion against the store
as it stood when the run began, which on a runner is the store restored from
origin. Here that is simply the file on disk when a `Sweep` is made: a file
left in place is one that was pushed, and a file removed is a push that
failed.
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import storage
from src.airtable import AirtableClient
from src.airtable_sweep import CLASSIFICATION_TABLES, COPY_FIELDS, JOBS, SweepClient
from src.closure import Closure
from src.config import SweepConfig
from src.filters import TitleMatcher
from src.normalise import Row, dumps
from src.projection import fields_for
from src.dedupe import group
from src.sweep import Sweep
from tests.fake_airtable import FakeBase, stamp

MATCHER = TitleMatcher()
NOW = datetime(2026, 10, 10, 4, 0, tzinfo=timezone.utc)
CONFIG = SweepConfig(closed_after_polled_runs=4, retire_after_days=15, run_log_window=60,
                     budget_warning_share=0.6, budget_warning_before_day=15)
TABLES = {JOBS: "tblPRODJOBS000001", "rejected-not-a-fit": "tblPRODNOTFIT0001",
          "rejected-poor-filtering": "tblPRODPOORFILT01", "accepted": "tblPRODACCEPT0001"}


def make_row(i, title="AI Engineer", source="greenhouse", published="2026-09-20T10:00:00Z",
             employer=None, expires=None, location="Lahore"):
    return Row(identity="%s:%d" % (source, i), source=source, board_id="%s:acme" % source,
               external_id=str(i), title=title, title_normalised=title,
               url="https://x.test/%d" % i, url_provenance="payload",
               first_seen="2026-09-20T10:00:00Z", ordering_date=published,
               ordering_date_source="publication", employer=employer or "Acme %d" % i,
               location=location, published_at=published, published_field="first_published",
               expires_at=expires)


class Harness(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.paths = storage.layout(False)
        self.base = FakeBase({TABLES[JOBS]}, now=NOW)
        self.last_seen = {}
        self.logs = []

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    # ------------------------------------------------------------- helpers
    def store_rows(self, rows):
        public = [r.as_record() for r in rows if r.source != "himalayas"]
        private = [r.as_record() for r in rows if r.source == "himalayas"]
        storage.write_atomic(self.paths["filtered"], dumps(public))
        storage.write_atomic(self.paths["local_filtered"], dumps(private))
        for r in rows:
            self.last_seen.setdefault(r.identity, "2026-10-10T03:40:00Z")

    def in_jobs(self, row, status=None, classified_days_ago=None, closed=None):
        fields = fields_for(group([row])[0], MATCHER)
        fields = {k: fields[k] for k in COPY_FIELDS}
        if status:
            fields["Status"] = status
        if closed:
            fields["Closed"] = closed
        classified = NOW - timedelta(days=classified_days_ago) if status else None
        return self.base.seed(TABLES[JOBS], fields, classified_at=classified)

    def client(self):
        return SweepClient("patFAKE.0000", "appFAKEBASE000001", TABLES, session=self.base,
                           min_interval=0, sleep=lambda s: None)

    def sweep(self, daily=True, private_ok=True, since=None, now=NOW):
        closure = Closure(self.last_seen, self.logs, lambda b: b.startswith("himalayas"),
                          CONFIG.closed_after_polled_runs, now.isoformat().replace("+00:00", "Z"))
        client = self.client()
        report = Sweep(client, self.paths, now, MATCHER, closure, CONFIG,
                       private_ok).run(daily, since=since)
        report["calls_used"] = client.calls_used
        return report

    def store(self, name, private=False):
        directory = self.paths["local_outcomes_dir" if private else "outcomes_dir"]
        return storage.read_records("%s/%s" % (directory, name))

    def jobs(self):
        return self.base.rows(TABLES[JOBS])

    def copies(self, table):
        return self.base.rows(TABLES[table])


class TestStep1Copy(Harness):
    def test_a_marked_row_is_copied_with_its_ten_fields_and_nothing_else(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=1)
        report = self.sweep(daily=False)
        [c] = self.copies("rejected-poor-filtering")
        self.assertEqual(c["Identity"], "greenhouse:1")
        self.assertNotIn("Status", c)
        self.assertNotIn("Pipeline reason", c)
        self.assertEqual(report["copied"], {"rejected-poor-filtering": 1})
        self.assertEqual(self.copies("accepted"), [])

    def test_the_copy_is_idempotent(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=1)
        self.sweep(daily=False)
        self.sweep(daily=False)
        self.assertEqual(len(self.copies("accepted")), 1)

    def test_a_status_change_moves_the_copy_and_resets_its_clock(self):
        """ADR-0050 step 1: the old copy goes, with its reason, and the new
        one's `Classified` starts now."""
        r = make_row(1)
        self.store_rows([r])
        record_id = self.in_jobs(r, status="accepted", classified_days_ago=5)
        old = self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "applied"},
                             created=NOW - timedelta(days=5))
        self.base.table(TABLES[JOBS])[record_id]["fields"]["Status"] = "rejected-not-a-fit"
        self.sweep(daily=False)
        self.assertNotIn(old, {c["_id"] for c in self.copies("accepted")})
        self.assertEqual(self.copies("accepted"), [])
        [new] = self.copies("rejected-not-a-fit")
        self.assertEqual(new["_created"], stamp(NOW))

    def test_a_cleared_status_removes_the_copy_on_the_next_fetch(self):
        """The operator clears `Status` in the browser. `Classified at`
        records the change, so even an evening run sees it."""
        r = make_row(1)
        self.store_rows([r])
        record_id = self.in_jobs(r, status="accepted", classified_days_ago=5)
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1"},
                       created=NOW - timedelta(days=5))
        fields = self.base.table(TABLES[JOBS])[record_id]["fields"]
        fields.pop("Status")
        fields["Classified at"] = stamp(NOW - timedelta(hours=1))
        report = self.sweep(daily=False, since=stamp(NOW - timedelta(hours=12)))
        self.assertTrue(report["tables_read"])
        self.assertEqual(self.copies("accepted"), [])

    def test_with_no_previous_run_the_tables_are_always_read(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=5)
        self.assertTrue(self.sweep(daily=False, since=None)["tables_read"])

    def test_a_copy_only_run_reads_one_table_when_nothing_moved(self):
        """The evening run: the copy step reads the classification tables
        only when a status moved since the previous run."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=3)
        report = self.sweep(daily=False, since=stamp(NOW - timedelta(hours=12)))
        self.assertFalse(report["tables_read"])
        self.assertEqual(report["calls_used"], 1)


class TestStep2StoreVerifyDelete(Harness):
    def test_the_verify_refuses_until_the_store_holds_the_row(self):
        """Brief 7's first check. Day 15: the outcome is written and the row
        stays. The push fails, so the next run's store lacks it: the row is
        still not deleted, and is reported. Only once the store holds it is
        the row deleted."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=16)

        report = self.sweep()
        self.assertEqual(len(self.jobs()), 1, "deleted on a write nobody read back")
        self.assertEqual(report["waiting_for_the_store"], 1)
        self.assertEqual([s["identity"] for s in self.store("rejected_poor_filtering.json")],
                         ["greenhouse:1"])

        os.remove("%s/rejected_poor_filtering.json" % self.paths["outcomes_dir"])
        report = self.sweep()
        self.assertEqual(len(self.jobs()), 1, "deleted although the store lacks the row")
        self.assertEqual(report["deleted_from_jobs"], 0)
        self.assertEqual(report["waiting_for_the_store"], 1)

        report = self.sweep()
        self.assertEqual(self.jobs(), [])
        self.assertEqual(report["deleted_from_jobs"], 1)

    def test_nothing_happens_before_fifteen_days(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=14)
        self.sweep()
        self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(self.store("rejected_poor_filtering.json"), [])

    def test_the_reason_travels_with_the_row(self):
        """ADR-0050: on day 15 the store record carries the reason from the
        matching copy, or for an accepted row its `Stage`."""
        for status, field, value, name in (
                ("rejected-poor-filtering", "Pipeline reason", "duplicate",
                 "rejected_poor_filtering.json"),
                ("accepted", "Stage", "applied", "accepted.json")):
            with self.subTest(status=status):
                self.setUp()
                r = make_row(1)
                self.store_rows([r])
                self.in_jobs(r, status=status, classified_days_ago=16)
                self.base.seed(TABLES[status], {"Identity": "greenhouse:1", field: value},
                               created=NOW - timedelta(days=16))
                self.sweep()
                [record] = self.store(name)
                self.assertEqual((record["status"], record["reason"]), (status, value))
                self.assertEqual(record["title"], "AI Engineer")
                self.tearDown()

    def test_an_identity_already_in_another_store_is_left_and_reported(self):
        """ADR-0043: routing is exclusive."""
        r = make_row(1)
        self.store_rows([r])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=20)
        report = self.sweep()
        self.assertEqual(self.store("rejected_not_a_fit.json"), [])
        self.assertEqual(len(self.jobs()), 1)
        self.assertTrue(report["problems"])


class TestStep3RejectionTables(Harness):
    def test_accepted_is_deleted_by_no_clock(self):
        """Brief 7: `accepted` survives a sweep against a row well past
        fifteen days, and the accepted store holds it."""
        r = make_row(1)
        self.store_rows([r])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "applied"},
                       created=NOW - timedelta(days=90))
        self.sweep()
        self.assertEqual(len(self.copies("accepted")), 1)
        self.assertEqual(len(self.store("accepted.json")), 1)

    def test_a_rejection_copy_goes_at_fifteen_days_only_once_stored(self):
        r = make_row(1)
        self.store_rows([r])
        self.base.seed(TABLES["rejected-not-a-fit"], {"Identity": "greenhouse:1"},
                       created=NOW - timedelta(days=16))
        report = self.sweep()
        self.assertEqual(len(self.copies("rejected-not-a-fit")), 1, "deleted before stored")
        self.assertTrue(report["problems"])
        storage.write_atomic("%s/rejected_not_a_fit.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        self.sweep()
        self.assertEqual(self.copies("rejected-not-a-fit"), [])


class TestSteps4And5Closed(Harness):
    def polled(self, days, board="greenhouse:acme"):
        for d in days:
            self.logs.append({"run_at": "2026-10-%02dT03:40:00Z" % d,
                              "boards": [{"board": board, "status": "ok", "fetched": 30}]})

    def test_closed_appears_then_retires(self):
        """Brief 7: absent on four polling runs, `Closed` is stamped and the
        row stays; fifteen days on it reaches the store with reason `closed`
        and leaves `Jobs`."""
        r = make_row(1)
        self.store_rows([r])
        self.last_seen["greenhouse:1"] = "2026-10-01T03:40:00Z"
        self.polled([2, 3, 4, 5])
        self.in_jobs(r)
        report = self.sweep()
        [row] = self.jobs()
        self.assertEqual(row["Closed"], "2026-10-05")
        self.assertEqual(report["closed_marked"], 1)

        later = NOW + timedelta(days=15)
        self.sweep(now=later)
        [record] = self.store("removed_unreviewed.json")
        self.assertEqual((record["reason"], record["closed"]), ("closed", "2026-10-05"))
        self.assertEqual(len(self.jobs()), 1, "deleted in the run that wrote the store")
        self.sweep(now=later)
        self.assertEqual(self.jobs(), [])

    def test_four_skipped_evenings_mark_no_himalayas_row(self):
        """Brief 7's closure check, through the sweep."""
        r = make_row(7, source="himalayas")
        self.store_rows([r])
        self.last_seen["himalayas:7"] = "2026-10-01T03:40:00Z"
        for d in range(2, 9):
            self.logs.append({"run_at": "2026-10-%02dT17:40:00Z" % d,
                              "boards": [{"board": "himalayas:acme", "status": "skipped",
                                          "fetched": 0}]})
        self.in_jobs(r)
        self.sweep()
        self.assertNotIn("Closed", self.jobs()[0])

    def test_a_posting_that_returns_loses_its_mark(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, closed="2026-10-05")
        report = self.sweep()
        self.assertNotIn("Closed", self.jobs()[0])
        self.assertEqual(report["closed_cleared"], 1)

    def test_an_expired_posting_is_marked_with_its_expiry(self):
        r = make_row(1, expires="2026-10-08T00:00:00Z")
        self.store_rows([r])
        self.in_jobs(r)
        self.sweep()
        self.assertEqual(self.jobs()[0]["Closed"], "2026-10-08")

    def test_a_classified_row_is_never_marked(self):
        """Step 4 reads rows with an empty status only: a classified row
        runs on its own clock."""
        r = make_row(1)
        self.store_rows([r])
        self.last_seen["greenhouse:1"] = "2026-10-01T03:40:00Z"
        self.polled([2, 3, 4, 5])
        self.in_jobs(r, status="accepted", classified_days_ago=2)
        self.sweep()
        self.assertNotIn("Closed", self.jobs()[0])


class TestStep6Removed(Harness):
    def test_a_row_a_rule_now_drops_is_stored_with_the_rule_then_removed(self):
        r = make_row(1, title="Account Executive")
        self.store_rows([r])
        self.in_jobs(r)
        self.sweep()
        [record] = self.store("removed_unreviewed.json")
        self.assertEqual(record["reason"], "dropped by the title rule")
        self.assertEqual(len(self.jobs()), 1)
        self.sweep()
        self.assertEqual(self.jobs(), [])

    def test_a_row_no_longer_its_groups_display_row_is_removed(self):
        """A new member published earlier becomes the representative, the
        projection sends the group under it, and the old row is a duplicate."""
        old = make_row(5, employer="Acme", published="2026-09-20T10:00:00Z")
        earlier = make_row(3, employer="Acme", published="2026-09-20T10:00:00Z")
        self.store_rows([old, earlier])
        self.in_jobs(old)
        self.sweep()
        [record] = self.store("removed_unreviewed.json")
        self.assertEqual(record["reason"], "no longer its group's display row")

    def test_a_row_the_stored_layers_do_not_hold_is_left_and_counted(self):
        """Nothing stored can say whether a rule dropped it, so it is not
        judged. The 15 Himalayas rows of 2026-09-24 are the case, two of them
        roles the operator named as new to him."""
        r = make_row(1)
        self.store_rows([])
        self.in_jobs(r)
        report = self.sweep()
        self.sweep()
        self.assertEqual(self.store("removed_unreviewed.json"), [])
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(report["not_in_the_stored_layers"], 1)

    def test_a_classified_row_the_layers_do_not_hold_is_stored_from_the_display_row(self):
        """Step 2 still stores it, from the fields `Jobs` holds, marked so."""
        r = make_row(1)
        self.store_rows([])
        self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=16)
        self.sweep()
        [record] = self.store("rejected_not_a_fit.json")
        self.assertEqual((record["identity"], record["from"]), ("greenhouse:1", "display"))

    def test_an_open_admitted_row_is_left_alone(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r)
        report = self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(self.store("removed_unreviewed.json"), [])
        self.assertEqual(report["waiting_for_the_store"], 0)


class TestPrivateRows(Harness):
    def test_an_aggregator_outcome_goes_to_the_private_store(self):
        r = make_row(7, source="himalayas")
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=16)
        self.sweep()
        self.assertEqual([s["identity"] for s in self.store("rejected_poor_filtering.json",
                                                             private=True)], ["himalayas:7"])
        self.assertEqual(self.store("rejected_poor_filtering.json"), [])

    def test_without_the_private_store_aggregator_rows_are_copied_and_held(self):
        r = make_row(7, source="himalayas")
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=16)
        report = self.sweep(private_ok=False)
        self.assertEqual(len(self.copies("rejected-poor-filtering")), 1)
        self.assertEqual(self.store("rejected_poor_filtering.json", private=True), [])
        self.assertEqual(len(self.jobs()), 1)
        self.assertGreater(report["held_private_unavailable"], 0)


class TestNoClockMoves(Harness):
    def test_neither_the_projection_nor_the_sweep_moves_a_clock(self):
        """Brief 7: project twice and confirm no `Classified at` and no
        `Classified` changed. Status is the only thing that moves the first,
        and no pipeline writer sends it."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=3)
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1"},
                       created=NOW - timedelta(days=3))
        before = ({x["Identity"]: x["Classified at"] for x in self.jobs()},
                  {x["Identity"]: x["_created"] for x in self.copies("accepted")})
        projector = AirtableClient("patFAKE.0000", "appFAKEBASE000001", TABLES[JOBS],
                                   session=self.base, min_interval=0, sleep=lambda s: None)
        for _ in range(2):
            projector.upsert([fields_for(group([r])[0], MATCHER)])
            self.base.advance(hours=12)
            self.sweep()
        after = ({x["Identity"]: x["Classified at"] for x in self.jobs()},
                 {x["Identity"]: x["_created"] for x in self.copies("accepted")})
        self.assertEqual(after, before)
        for call in self.base.calls:
            for rec in (call["json"] or {}).get("records", []):
                self.assertNotIn("Status", rec.get("fields", {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
