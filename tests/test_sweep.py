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
from dataclasses import replace
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
                     unreviewed_after_days=30, clearing_dry_run_valid_hours=48,
                     budget_warning_share=0.6, budget_warning_before_day=15)
TABLES = {JOBS: "tblPRODJOBS000001", "rejected-not-a-fit": "tblPRODNOTFIT0001",
          "rejected-poor-filtering": "tblPRODPOORFILT01", "accepted": "tblPRODACCEPT0001"}


def make_row(i, title="AI Engineer", source="greenhouse", published="2026-10-08T10:00:00Z",
             employer=None, expires=None, location="Lahore"):
    return Row(identity="%s:%d" % (source, i), source=source, board_id="%s:acme" % source,
               external_id=str(i), title=title, title_normalised=title,
               url="https://x.test/%d" % i, url_provenance="payload",
               first_seen=published, ordering_date=published,
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

    def in_jobs(self, row, status=None, classified_days_ago=None, closed=None, extra=None):
        fields = fields_for(group([row])[0], MATCHER)
        fields = {k: fields[k] for k in COPY_FIELDS}
        if status:
            fields["Status"] = status
        if closed:
            fields["Closed"] = closed
        fields.update(extra or {})
        classified = NOW - timedelta(days=classified_days_ago) if status else None
        return self.base.seed(TABLES[JOBS], fields, classified_at=classified)

    def client(self):
        return SweepClient("patFAKE.0000", "appFAKEBASE000001", TABLES, session=self.base,
                           min_interval=0, sleep=lambda s: None)

    def sweep(self, daily=True, private_ok=True, since=None, now=NOW, config=CONFIG):
        closure = Closure(self.last_seen, self.logs, lambda b: b.startswith("himalayas"),
                          config.closed_after_polled_runs, now.isoformat().replace("+00:00", "Z"))
        client = self.client()
        report = Sweep(client, self.paths, now, MATCHER, closure, config,
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

    def test_a_status_changed_away_from_accepted_keeps_its_copy(self):
        """D12: an `accepted` copy is never removed by a status change. The
        new copy is made, its `Classified` starting now, and the old one is
        reported for the operator to remove with `Delete`."""
        r = make_row(1)
        self.store_rows([r])
        record_id = self.in_jobs(r, status="accepted", classified_days_ago=5)
        old = self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "applied"},
                             created=NOW - timedelta(days=5))
        self.base.table(TABLES[JOBS])[record_id]["fields"]["Status"] = "rejected-not-a-fit"
        report = self.sweep(daily=False)
        self.sweep()
        [kept] = self.copies("accepted")
        self.assertEqual((kept["_id"], kept["Stage"]), (old, "applied"))
        [new] = self.copies("rejected-not-a-fit")
        self.assertEqual(new["_created"], stamp(NOW))
        self.assertTrue([p for p in report["problems"] if "set Delete" in p])

    def test_a_cleared_status_removes_no_copy(self):
        """D12: the operator clears `Status`, perhaps by a stray keystroke.
        `Classified at` records it, so even an evening run reads the tables,
        and nothing is removed from any of them, daily steps included."""
        r1, r2 = make_row(1), make_row(2)
        self.store_rows([r1, r2])
        ids = [self.in_jobs(r1, status="accepted", classified_days_ago=5),
               self.in_jobs(r2, status="rejected-not-a-fit", classified_days_ago=5)]
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "applied"},
                       created=NOW - timedelta(days=5))
        self.base.seed(TABLES["rejected-not-a-fit"], {"Identity": "greenhouse:2",
                                                      "Choice reason": "salary"},
                       created=NOW - timedelta(days=5))
        for record_id in ids:
            fields = self.base.table(TABLES[JOBS])[record_id]["fields"]
            fields.pop("Status")
            fields["Classified at"] = stamp(NOW - timedelta(hours=1))
        report = self.sweep(daily=False, since=stamp(NOW - timedelta(hours=12)))
        self.sweep()
        self.assertTrue(report["tables_read"])
        self.assertEqual(report["kept_after_a_clear"], 2)
        self.assertEqual([c["Stage"] for c in self.copies("accepted")], ["applied"])
        self.assertEqual([c["Choice reason"] for c in self.copies("rejected-not-a-fit")],
                         ["salary"])
        self.assertEqual([c for c in self.base.calls if c["method"] == "DELETE"], [])

    def test_a_superseded_rejection_copy_is_saved_before_it_goes(self):
        """D12: a rejection copy whose row was reclassified keeps its reason
        in `removed_copies.json`, and is deleted only on a later run, once
        that store holds it. Until then both copies stand."""
        r = make_row(1)
        self.store_rows([r])
        record_id = self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=5)
        old = self.base.seed(TABLES["rejected-not-a-fit"],
                             {"Identity": "greenhouse:1", "Choice reason": "salary"},
                             created=NOW - timedelta(days=5))
        self.base.table(TABLES[JOBS])[record_id]["fields"]["Status"] = "rejected-poor-filtering"
        first = self.sweep(daily=False)
        self.assertEqual([c["_id"] for c in self.copies("rejected-not-a-fit")], [old])
        self.assertEqual(len(self.copies("rejected-poor-filtering")), 1)
        [saved] = self.store("removed_copies.json")
        self.assertEqual((saved["copy_id"], saved["table"], saved["reason"], saved["identity"]),
                         (old, "rejected-not-a-fit", "salary", "greenhouse:1"))
        self.assertIn("rejected-poor-filtering", saved["why"])
        self.assertEqual(first["stale_copies_deleted"], {})
        second = self.sweep(daily=False)
        self.assertEqual(self.copies("rejected-not-a-fit"), [])
        self.assertEqual(second["stale_copies_deleted"], {"rejected-not-a-fit": 1})

    def test_a_superseded_copy_waits_while_its_record_is_not_on_origin(self):
        """The push that should have carried the record failed: the file
        is gone at the next run, so the copy stays and the record is
        written again."""
        r = make_row(1)
        self.store_rows([r])
        record_id = self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=5)
        self.base.seed(TABLES["rejected-not-a-fit"], {"Identity": "greenhouse:1"},
                       created=NOW - timedelta(days=5))
        self.base.table(TABLES[JOBS])[record_id]["fields"]["Status"] = "accepted"
        self.sweep(daily=False)
        os.remove("%s/removed_copies.json" % self.paths["outcomes_dir"])
        self.sweep(daily=False)
        self.assertEqual(len(self.copies("rejected-not-a-fit")), 1)
        self.assertEqual(len(self.store("removed_copies.json")), 1)

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

    def test_an_accepted_copy_marked_delete_is_stored_then_removed(self):
        """D12: the operator sets `Delete` to yes on a copy whose row has
        already left `Jobs`. The first sweep writes its record, `Stage` as it
        stands now; the copy leaves Airtable on the next, once origin holds
        it. The accepted store is never touched."""
        r = make_row(1)
        self.store_rows([r])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1", "reason": "shortlisted"}]))
        copy_id = self.base.seed(TABLES["accepted"], dict(
            {k: v for k, v in fields_for(group([r])[0], MATCHER).items() if k in COPY_FIELDS},
            Stage="applied", Delete="yes"), created=NOW - timedelta(days=40))
        first = self.sweep()
        self.assertEqual(len(self.copies("accepted")), 1, "removed before its record was stored")
        [saved] = self.store("removed_copies.json")
        self.assertEqual((saved["copy_id"], saved["reason"], saved["table"]),
                         (copy_id, "applied", "accepted"))
        self.assertEqual(first["waiting_for_the_store"], 1)
        second = self.sweep()
        self.assertEqual(self.copies("accepted"), [])
        self.assertEqual(second["copies_deleted"], {"accepted": 1})
        self.assertEqual(len(self.store("accepted.json")), 1)

    def test_delete_on_a_row_still_in_jobs_stores_it_and_removes_both(self):
        """Marked before its fifteen days: the accepted store gets the row
        with its `Stage`, and once origin holds both records the copy and its
        `Jobs` row go together, or step 1 would copy the row straight back."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=3)
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "shortlisted",
                                            "Delete": "yes"}, created=NOW - timedelta(days=3))
        self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(len(self.copies("accepted")), 1)
        [stored] = self.store("accepted.json")
        self.assertEqual((stored["identity"], stored["reason"]), ("greenhouse:1", "shortlisted"))
        report = self.sweep()
        self.assertEqual(self.jobs(), [])
        self.assertEqual(self.copies("accepted"), [])
        self.assertEqual(report["deleted_from_jobs"], 1)

    def test_a_row_due_twice_is_deleted_once(self):
        """Past its fifteen days and its copy marked `Delete`, both records
        on origin: steps 2 and 3 each qualify the `Jobs` row, and it is named
        once in the one delete."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=20)
        copy_id = self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Delete": "yes"},
                                 created=NOW - timedelta(days=20))
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        storage.write_atomic("%s/removed_copies.json" % self.paths["outcomes_dir"],
                             dumps([{"copy_id": copy_id, "identity": "greenhouse:1"}]))
        report = self.sweep()
        self.assertEqual((self.jobs(), self.copies("accepted")), ([], []))
        self.assertEqual(report["deleted_from_jobs"], 1)
        [jobs_delete] = [c for c in self.base.calls
                         if c["method"] == "DELETE" and c["table"] == TABLES[JOBS]]
        self.assertEqual(len([k for k, _ in jobs_delete["params"] if k == "records[]"]), 1)

    def test_delete_waits_while_its_record_is_not_on_origin(self):
        r = make_row(1)
        self.store_rows([r])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Delete": "yes"},
                       created=NOW - timedelta(days=40))
        self.sweep()
        os.remove("%s/removed_copies.json" % self.paths["outcomes_dir"])
        self.sweep()
        self.assertEqual(len(self.copies("accepted")), 1)

    def test_an_accepted_copy_without_delete_is_never_removed(self):
        r = make_row(1)
        self.store_rows([r])
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:1", "Stage": "applied"},
                       created=NOW - timedelta(days=400))
        self.sweep()
        self.sweep()
        self.assertEqual(len(self.copies("accepted")), 1)
        self.assertEqual(self.store("removed_copies.json"), [])

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

    def test_the_marks_the_pinned_posting_caused_clear_on_the_next_sweep(self):
        """The live case of 2026-10-01 and 10-02: a Himalayas row marked
        closed because every walk logged a pinned 2026-09-16 posting as its
        oldest. Logs of that shape prove nothing now, so the sweep clears the
        mark, and walks that stopped at marks newer than the row add none."""
        r = make_row(7, source="himalayas", published="2026-10-01T10:00:00Z")
        self.store_rows([r])
        self.last_seen["himalayas:7"] = "2026-10-03T03:40:00Z"
        for d in range(4, 9):
            self.logs.append({"run_at": "2026-10-%02dT03:40:00Z" % d, "boards": [
                {"board": "himalayas:acme", "status": "ok", "fetched": 120,
                 "oldest_published": "2026-09-16T06:15:55Z"}]})
        self.in_jobs(r, closed="2026-10-08")
        report = self.sweep()
        self.assertNotIn("Closed", self.jobs()[0])
        self.assertEqual(report["closed_cleared"], 1)
        for log in self.logs:
            log["boards"][0]["walk"] = {"stopped_by": "mark",
                                        "mark": log["run_at"][:10] + "T00:00:00Z"}
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
        old = make_row(5, employer="Acme", published="2026-10-08T10:00:00Z")
        earlier = make_row(3, employer="Acme", published="2026-10-08T10:00:00Z")
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

    def test_an_aggregator_identity_never_reaches_a_problem_line(self):
        """The run log is public; an aggregator's identity is not (ADR-0020).
        Its copy is past fifteen days with no stored outcome, so the sweep
        reports it, masked. The audit of 2026-09-25, F5."""
        r = make_row(7, source="himalayas")
        self.store_rows([r])
        self.base.seed(TABLES["rejected-not-a-fit"], {"Identity": "himalayas:7"},
                       created=NOW - timedelta(days=16))
        report = self.sweep()
        self.assertTrue(report["problems"])
        self.assertFalse([p for p in report["problems"] if "himalayas" in p], report["problems"])
        self.assertTrue(all("<aggregator row>" in p for p in report["problems"]))


class TestTheAuditOf20260925(Harness):
    def test_a_copy_step_1_removed_is_not_deleted_again_by_step_3(self):
        """F4: a row now `accepted` whose old `rejected-not-a-fit` copy is
        past fifteen days and already stored. Step 1 deletes the stale copy;
        step 3 read the table before that and must not delete it again, or
        the unconfirmed delete fails the whole daily sweep."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=1)
        copy_id = self.base.seed(TABLES["rejected-not-a-fit"], {"Identity": "greenhouse:1"},
                                 created=NOW - timedelta(days=20))
        storage.write_atomic("%s/rejected_not_a_fit.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        # Under D12 step 1 deletes a superseded copy only once its record is
        # on origin; here it is, so step 1 deletes it and step 3, which read
        # the table first, would reach for it too.
        storage.write_atomic("%s/removed_copies.json" % self.paths["outcomes_dir"],
                             dumps([{"copy_id": copy_id, "identity": "greenhouse:1"}]))
        report = self.sweep()
        self.assertEqual(report["stale_copies_deleted"], {"rejected-not-a-fit": 1})
        self.assertEqual(report["copies_deleted"], {})
        self.assertEqual(self.copies("rejected-not-a-fit"), [])
        self.assertEqual(len([c for c in self.base.calls if c["method"] == "DELETE"]), 1)

    def test_twenty_five_copies_go_ten_at_a_time(self):
        """Airtable takes ten records a call (ADR-0050's Assumptions); the
        in-memory base now refuses more, and every write here is counted."""
        rows = [make_row(i) for i in range(1, 26)]
        self.store_rows(rows)
        for r in rows:
            self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=1)
        self.sweep(daily=False)
        self.assertEqual(len(self.copies("rejected-poor-filtering")), 25)
        posts = [len(c["json"]["records"]) for c in self.base.calls if c["method"] == "POST"]
        self.assertEqual(posts, [10, 10, 5])


CHOICES = replace(CONFIG, reason_choices={
    "rejected-not-a-fit": ("employer", "stack"),
    "rejected-poor-filtering": ("wrong title match", "duplicate")})


class ADR0062Harness(Harness):
    def in_table(self, table, row, extra=None):
        fields = fields_for(group([row])[0], MATCHER)
        fields = {k: fields[k] for k in COPY_FIELDS}
        fields.update(extra or {})
        return self.base.seed(TABLES[table], fields)


class TestGone(ADR0062Harness):
    """ADR-0062's step 7: a posting he found gone is recorded and its row
    leaves `Jobs` the morning after origin holds the record."""

    def test_gone_keeps_a_posting_out_for_good(self):
        """Stored at the first morning sweep, its row deleted only at the
        next one, once the store is on origin; then the projection's skip
        holds it out whatever the rules say. Mutation: "the gone store is
        not read by the skip"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="gone", classified_days_ago=0, extra={"Reason": "duplicate"})
        first = self.sweep()
        [rec] = self.store("gone.json")
        self.assertEqual((rec["identity"], rec["status"], rec["reason"], rec["accepted"],
                          rec["marked_in"]), ("greenhouse:1", "gone", "duplicate", False, "Jobs"))
        self.assertEqual(len(self.jobs()), 1, "deleted before origin held its record")
        self.assertEqual(first["gone_recorded"], 1)
        self.sweep()
        self.assertEqual(self.jobs(), [])
        from src.projection import identities_in, public_store_texts
        self.assertIn("greenhouse:1", identities_in(public_store_texts(self.paths)))

    def test_a_gone_row_waits_while_its_record_is_not_on_origin(self):
        """A push that failed: the record is written again and the row stays."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="gone", classified_days_ago=0)
        self.sweep()
        os.remove("%s/gone.json" % self.paths["outcomes_dir"])
        self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(len(self.store("gone.json")), 1)

    def test_gone_on_an_accepted_posting_keeps_its_copy(self):
        """Marked in `Jobs`, or by `Stage` on the copy once the row has left:
        both reach the store, the copy stays, and neither is a problem."""
        r1, r2 = make_row(1), make_row(2)
        self.store_rows([r1, r2])
        self.in_jobs(r1, status="gone", classified_days_ago=0)
        self.in_table("accepted", r1)
        self.in_table("accepted", r2, {"Stage": "gone"})
        report = self.sweep()
        self.sweep()
        stored = {rec["identity"]: rec for rec in self.store("gone.json")}
        self.assertEqual((stored["greenhouse:1"]["accepted"], stored["greenhouse:1"]["marked_in"]),
                         (True, "Jobs"))
        self.assertEqual((stored["greenhouse:2"]["accepted"], stored["greenhouse:2"]["marked_in"]),
                         (True, "accepted"))
        self.assertEqual(len(self.copies("accepted")), 2, "an accepted copy was removed")
        self.assertEqual([p for p in report["problems"] if "accepted copy" in p], [])
        self.assertEqual(self.jobs(), [])

    def test_a_gone_mark_supersedes_a_rejection_copy_as_any_status_change(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="gone", classified_days_ago=0)
        self.in_table("rejected-poor-filtering", r, {"Pipeline reason": "duplicate"})
        self.sweep()
        [saved] = self.store("removed_copies.json")
        self.assertEqual(saved["reason"], "duplicate")
        self.sweep()
        self.assertEqual(self.copies("rejected-poor-filtering"), [])


class TestApplied(ADR0062Harness):
    def test_applied_makes_the_copy_with_its_stage_in_one_sweep(self):
        """One sweep, the evening's copy step included: the copy arrives with
        `Stage` applied. Mutation: "applied makes a copy without its
        Stage"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="applied", classified_days_ago=0)
        self.sweep(daily=False)
        [c] = self.copies("accepted")
        self.assertEqual((c["Identity"], c["Stage"]), ("greenhouse:1", "applied"))

    def test_applied_raises_a_stage_and_never_lowers_or_overwrites_one(self):
        """Empty and shortlisted are raised to applied; gone, which he set,
        is left; and `accepted` never writes `Stage` at all. Mutation: "a
        Stage is written over"."""
        rows = [make_row(i) for i in range(1, 5)]
        self.store_rows(rows)
        for r, status, stage in ((rows[0], "applied", None), (rows[1], "applied", "shortlisted"),
                                 (rows[2], "applied", "gone"), (rows[3], "accepted", None)):
            self.in_jobs(r, status=status, classified_days_ago=0)
            self.in_table("accepted", r, {"Stage": stage} if stage else None)
        report = self.sweep(daily=False)
        stages = {c["Identity"]: c.get("Stage") for c in self.copies("accepted")}
        self.assertEqual(stages, {"greenhouse:1": "applied", "greenhouse:2": "applied",
                                  "greenhouse:3": "gone", "greenhouse:4": None})
        self.assertEqual(report["transcribed"], {"accepted": 2})

    def test_an_applied_row_is_stored_as_accepted_with_applied_in_its_record(self):
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="applied", classified_days_ago=16)
        self.sweep()
        [rec] = self.store("accepted.json")
        self.assertEqual((rec["identity"], rec["status"], rec["reason"]),
                         ("greenhouse:1", "applied", "applied"))


class TestReason(ADR0062Harness):
    def test_a_reason_reaches_the_copy_and_the_store(self):
        """Mutation: "Reason never reaches the copy"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=16,
                     extra={"Reason": "duplicate"})
        self.sweep(config=CHOICES, daily=False)
        [c] = self.copies("rejected-poor-filtering")
        self.assertEqual(c["Pipeline reason"], "duplicate")
        self.sweep(config=CHOICES)
        [rec] = self.store("rejected_poor_filtering.json")
        self.assertEqual((rec["reason"], rec["reason_in_jobs"]), ("duplicate", "duplicate"))

    def test_a_reason_outside_the_fields_choices_is_kept_and_named(self):
        """One value the field lacks would fail a whole batch at Airtable;
        it is kept in the store record and named in the run log instead.
        Mutation: "a Reason outside the choices is sent"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=16,
                     extra={"Reason": "seniority in substance"})
        report = self.sweep(config=CHOICES, daily=False)
        [c] = self.copies("rejected-poor-filtering")
        self.assertNotIn("Pipeline reason", c)
        self.assertTrue([p for p in report["problems"] if "seniority in substance" in p])
        self.sweep(config=CHOICES)
        [rec] = self.store("rejected_poor_filtering.json")
        self.assertEqual((rec["reason"], rec["reason_in_jobs"]), (None, "seniority in substance"))

    def test_a_reason_he_set_on_a_copy_is_never_overwritten_and_an_empty_one_is_filled(self):
        """Mutation: "a reason on a copy is written over"."""
        r1, r2 = make_row(1), make_row(2)
        self.store_rows([r1, r2])
        for r in (r1, r2):
            self.in_jobs(r, status="rejected-poor-filtering", classified_days_ago=1,
                         extra={"Reason": "duplicate"})
        self.in_table("rejected-poor-filtering", r1, {"Pipeline reason": "wrong title match"})
        self.in_table("rejected-poor-filtering", r2)
        report = self.sweep(config=CHOICES, daily=False)
        reasons = {c["Identity"]: c.get("Pipeline reason")
                   for c in self.copies("rejected-poor-filtering")}
        self.assertEqual(reasons, {"greenhouse:1": "wrong title match",
                                   "greenhouse:2": "duplicate"})
        self.assertEqual(report["transcribed"], {"rejected-poor-filtering": 1})


class TestUnknownStatusAndTheNumber(ADR0062Harness):
    def test_a_status_the_sweep_does_not_know_makes_no_copy_and_moves_no_clock(self):
        """Past the fifteen and the thirty days, nothing happens to it.
        Mutation: "an unknown status is stored as accepted"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="later", classified_days_ago=40)
        report = self.sweep()
        for table in CLASSIFICATION_TABLES:
            self.assertEqual(self.copies(table), [], table)
        self.assertEqual(len(self.jobs()), 1)
        for name in ("rejected_not_a_fit.json", "rejected_poor_filtering.json", "accepted.json",
                     "removed_unreviewed.json", "gone.json"):
            self.assertEqual(self.store(name), [], name)
        self.assertEqual(report["deleted_from_jobs"], 0)

    def test_the_jobs_number_follows_the_posting_into_accepted(self):
        """Mutation: "an accepted copy is made without its Jobs No."."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=0, extra={"No.": 42})
        self.sweep(daily=False)
        [c] = self.copies("accepted")
        self.assertEqual(c["Jobs No."], 42)


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


class TestTheClock(Harness):
    """ADR-0055's clock: an unreviewed row leaves thirty days after it was
    first seen, stored with `unreviewed-aged-out` first, deleted on a later
    run once origin holds it."""

    def aged(self, days):
        first = (NOW - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        r = make_row(1, published=first)
        self.store_rows([r])
        self.in_jobs(r)
        return r

    def test_a_row_29_days_unreviewed_stays(self):
        """Mutation: "the clock fires at the retention window"."""
        self.aged(29)
        report = self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual(self.store("removed_unreviewed.json"), [])
        self.assertEqual(report["aged_out"], 0)

    def test_at_31_days_it_is_stored_then_removed_on_a_later_run(self):
        """Mutation: "the clock never fires"."""
        self.aged(31)
        first = self.sweep()
        [record] = self.store("removed_unreviewed.json")
        self.assertEqual((record["identity"], record["reason"]),
                         ("greenhouse:1", "unreviewed-aged-out"))
        self.assertEqual(len(self.jobs()), 1, "deleted in the run that wrote its store")
        self.assertIn({"identity": "greenhouse:1", "table": JOBS,
                       "reason": "unreviewed-aged-out", "action": "stored"}, first["removals"])
        second = self.sweep()
        self.assertEqual(self.jobs(), [])
        self.assertIn({"identity": "greenhouse:1", "table": JOBS,
                       "reason": "unreviewed-aged-out", "action": "deleted"}, second["removals"])

    def test_the_clock_measures_first_seen_not_the_publication_date(self):
        """ADR-0055: thirty days after it was first seen. A row published 34
        days ago and first seen 28 days ago, six days old then and so
        admitted (D14), has been in the display 28 days and stays. Every
        other test gave a row one date for both, so measuring publication
        would have aged rows out up to a week early unnoticed: the fourth
        audit's F7. Mutation: "the clock measures the publication date"."""
        r = replace(make_row(1, published=(NOW - timedelta(days=34)).isoformat()
                             .replace("+00:00", "Z")),
                    first_seen=(NOW - timedelta(days=28)).isoformat().replace("+00:00", "Z"))
        self.store_rows([r])
        self.in_jobs(r)
        self.assertNotEqual(self.jobs()[0]["First seen"], self.jobs()[0]["Published"])
        report = self.sweep()
        self.assertEqual((report["aged_out"], self.store("removed_unreviewed.json")), (0, []))
        self.assertEqual(report.get("removals", []), [])

    def test_a_classified_row_is_never_aged_out(self):
        first = (NOW - timedelta(days=40)).isoformat().replace("+00:00", "Z")
        r = make_row(1, published=first)
        self.store_rows([r])
        self.in_jobs(r, status="accepted", classified_days_ago=2)
        self.sweep()
        self.assertEqual(self.store("removed_unreviewed.json"), [])

    def test_an_aggregator_rows_identity_is_masked_in_the_log(self):
        first = (NOW - timedelta(days=31)).isoformat().replace("+00:00", "Z")
        r = make_row(1, source="himalayas", published=first)
        self.store_rows([r])
        self.in_jobs(r)
        report = self.sweep()
        self.assertEqual([x["identity"] for x in report["removals"]], ["<aggregator row>"])
        [record] = self.store("removed_unreviewed.json", private=True)
        self.assertEqual(record["identity"], "himalayas:1")


class TestRemovalsByReason(Harness):
    def write_removals(self, records, private=False):
        directory = self.paths["local_outcomes_dir" if private else "outcomes_dir"]
        storage.write_atomic("%s/removed_unreviewed.json" % directory, dumps(records))

    def test_a_row_that_returned_and_aged_out_is_stored_again_before_it_goes(self):
        """A rule dropped it, a widened rule let it back, and it has now aged
        out. Origin holds the first removal, not this one, so this one is
        written and the row stays until origin holds it. Deleting against the
        old record would let the projection, reading its rule reason, send the
        row back on every run. Mutation: "a returned row is deleted against
        its old record"."""
        first = (NOW - timedelta(days=31)).isoformat().replace("+00:00", "Z")
        r = make_row(1, published=first)
        self.store_rows([r])
        self.in_jobs(r)
        self.write_removals([{"identity": "greenhouse:1", "reason": "dropped by the age rule",
                              "swept_at": "2026-09-01T04:00:00Z"}])
        report = self.sweep()
        self.assertEqual(len(self.jobs()), 1)
        self.assertEqual([x["reason"] for x in self.store("removed_unreviewed.json")],
                         ["dropped by the age rule", "unreviewed-aged-out"])
        self.assertEqual(report["deleted_from_jobs"], 0)
        self.sweep()
        self.assertEqual(self.jobs(), [])

    def test_a_removal_the_operators_tool_wrote_takes_the_row_once_origin_holds_it(self):
        """ADR-0055: the tool writes `operator-removed` and nothing else; the
        sweep deletes the row on its next daily run. The rules would keep the
        row, so the stored removal is the only reason it goes. Mutation: "a
        kept-out row is judged again"."""
        r = make_row(1)
        self.store_rows([r])
        self.in_jobs(r)
        self.write_removals([{"identity": "greenhouse:1", "reason": "operator-removed",
                              "swept_at": "2026-10-09T04:00:00Z"}])
        report = self.sweep()
        self.assertEqual(self.jobs(), [])
        self.assertIn({"identity": "greenhouse:1", "table": JOBS,
                       "reason": "operator-removed", "action": "deleted"}, report["removals"])
        self.assertEqual(len(self.store("removed_unreviewed.json")), 1, "a second record")


class TestExclusivity(Harness):
    def test_an_accepted_copy_saved_twice_is_correct_and_two_corpora_are_not(self):
        """Fitness function for ADR-0043, "the exclusivity invariant covers the
        three classification stores above and no others.": D12 writes an
        `accepted` copy to `removed_copies.json` and to the accepted store in
        the same run, which is correct; one identity in two outcome corpora is
        not. Before 2026-09-30 nothing checked either. Mutation: "the
        exclusivity check covers every store"."""
        storage.write_atomic("%s/accepted.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        storage.write_atomic("%s/removed_copies.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1", "copy_id": "recA"}]))
        storage.write_atomic("%s/removed_unreviewed.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1", "reason": "closed"}]))
        report = self.sweep()
        self.assertEqual([p for p in report["problems"] if "ADR-0043" in p], [])
        storage.write_atomic("%s/rejected_not_a_fit.json" % self.paths["outcomes_dir"],
                             dumps([{"identity": "greenhouse:1"}]))
        report = self.sweep()
        self.assertEqual(len([p for p in report["problems"] if "ADR-0043" in p]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
