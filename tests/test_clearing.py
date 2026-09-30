"""ADR-0055's clearing tool, against the in-memory base the sweep's tests use.

The tool writes stores and sets `Delete`; it deletes nothing. A later daily
sweep removes the rows once origin holds what the tool wrote, so each test
that follows a row out of the display runs the sweep after it.
"""

import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import projection
from src.airtable_sweep import JOBS
from src.clearing import Clearing, ClearingError, request_from
from tests.test_sweep import MATCHER, NOW, TABLES, Harness, make_row

WINDOW = 48


def ago(days):
    return (NOW - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def dry_run_log(table, days, hours_ago=1):
    return {"run_at": (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z"),
            "clearing": {"table": table, "older_than_days": days, "confirmed": False,
                         "failure": None}}


class ClearingHarness(Harness):
    def clear(self, table, days, confirmed=False, logs=None, private_ok=True):
        client = self.client()
        report = Clearing(client, self.paths, NOW, private_ok).run(
            table, days, confirmed, logs or [], WINDOW)
        report["calls_used"] = client.calls_used
        return report

    def confirmed(self, table, days):
        return self.clear(table, days, confirmed=True, logs=[dry_run_log(table, days)])

    def writes(self):
        return [c for c in self.base.calls if c["method"] != "GET"]

    def store_files(self):
        found = []
        for key in ("outcomes_dir", "local_outcomes_dir"):
            directory = self.paths[key]
            if os.path.isdir(directory):
                found += sorted(os.listdir(directory))
        return found


class TestTheRequest(unittest.TestCase):
    def test_no_table_is_no_request(self):
        self.assertIsNone(request_from(None, "30", False))
        self.assertIsNone(request_from("none", "30", True))

    def test_a_table_and_a_whole_number_of_days(self):
        self.assertEqual(request_from("jobs", " 15 ", True), ("jobs", 15, True))
        self.assertEqual(request_from("accepted", "30", False), ("accepted", 30, False))

    def test_anything_else_is_refused_by_name(self):
        for table, days in (("Jobs table", "30"), ("jobs", "a month"), ("jobs", "0"),
                            ("jobs", "-5"), ("jobs", "")):
            with self.subTest(table=table, days=days):
                with self.assertRaises(ClearingError):
                    request_from(table, days, False)


class TestTheDryRun(ClearingHarness):
    def test_a_dry_run_changes_nothing(self):
        """Fitness function for ADR-0055, "A dry run must change nothing":
        record counts before and after, no write to the base and no store
        written, while it reports what it would remove. Mutation: "a dry run
        writes the stores"."""
        rows = [make_row(1, published=ago(40)), make_row(2, published=ago(35))]
        self.store_rows(rows)
        for r in rows:
            self.in_jobs(r)
        self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:9", "Stage": "applied",
                                            "Published": ago(60)}, created=NOW - timedelta(days=40))
        before = (len(self.jobs()), len(self.copies("accepted")), self.store_files())
        for table in (JOBS, "accepted"):
            report = self.clear(table, 30)
            self.assertIn("dry run", report["mode"])
        self.assertEqual((len(self.jobs()), len(self.copies("accepted")), self.store_files()),
                         before)
        self.assertEqual(self.writes(), [])

    def test_it_reports_what_it_would_remove(self):
        """Per table: how many, the oldest and newest publication dates among
        them, and how many are unreviewed."""
        rows = [make_row(1, published=ago(40)), make_row(2, published=ago(35)),
                make_row(3, published=ago(5))]
        self.store_rows(rows)
        self.in_jobs(rows[0])
        self.in_jobs(rows[1], status="rejected-not-a-fit", classified_days_ago=3)
        self.in_jobs(rows[2])
        report = self.clear(JOBS, 30)
        self.assertEqual((report["would_remove"], report["unreviewed"]), (2, 1))
        self.assertEqual(report["oldest_published"][:10], ago(40)[:10])
        self.assertEqual(report["newest_published"][:10], ago(35)[:10])
        self.assertEqual(sorted(report["rows"]), ["greenhouse:1", "greenhouse:2"])


class TestTheConfirmation(ClearingHarness):
    def setUp(self):
        super().setUp()
        r = make_row(1, published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)

    def test_a_confirmed_run_needs_a_recent_dry_run_of_the_same_request(self):
        """Fitness function for ADR-0055, "The confirmation must be required.":
        confirming without a dry run on file refuses and writes nothing, as
        does one for another table, another threshold or too long ago.
        Mutation: "the confirmation is not required"."""
        for logs in ([], [dry_run_log("accepted", 30)], [dry_run_log(JOBS, 15)],
                     [dry_run_log(JOBS, 30, hours_ago=WINDOW + 1)]):
            with self.subTest(logs=logs):
                report = self.clear(JOBS, 30, confirmed=True, logs=logs)
                self.assertTrue(report["failure"].startswith("refused"))
                self.assertEqual(self.store_files(), [])
                self.assertEqual(self.writes(), [])
        report = self.clear(JOBS, 30, confirmed=True, logs=[dry_run_log(JOBS, 30)])
        self.assertIsNone(report["failure"])
        self.assertEqual(report["written"], 1)


class TestWhatEachTableMeasures(ClearingHarness):
    def test_jobs_measures_the_publication_date(self):
        """A row published two days ago and first classified long ago is not
        old for `Jobs`. Mutation: "jobs is measured on Classified"."""
        r = make_row(1, published=ago(2))
        self.store_rows([r])
        self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=40)
        self.assertEqual(self.clear(JOBS, 15)["would_remove"], 0)

    def test_the_classification_tables_measure_classified(self):
        """A copy that arrived twenty days ago is old whatever its posting's
        date. Mutation: "the tables are measured on the publication date"."""
        self.base.seed(TABLES["rejected-not-a-fit"],
                       {"Identity": "greenhouse:1", "Published": ago(2)},
                       created=NOW - timedelta(days=20))
        self.assertEqual(self.clear("rejected-not-a-fit", 15)["would_remove"], 1)


class TestRowsLeave(ClearingHarness):
    def test_a_removed_row_does_not_come_back(self):
        """Fitness function for ADR-0055, "A removed row must not come back.":
        clear it, project, and it is not sent; then the sweep takes it out of
        `Jobs`. Deleting it in the browser instead would see it re-sent within
        a day, which is the whole reason for the record. Mutation: "the tool
        removes a Jobs row without storing it"."""
        r = make_row(1, published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)
        self.confirmed(JOBS, 30)
        stored = projection.identities_in(projection.public_store_texts(self.paths))
        self.assertEqual(projection.plan([r], NOW.isoformat().replace("+00:00", "Z"), MATCHER,
                                         stored), [])
        report = self.sweep()
        self.assertEqual(self.jobs(), [])
        self.assertIn({"identity": "greenhouse:1", "table": JOBS, "reason": "operator-removed",
                       "action": "deleted"}, report["removals"])

    def test_the_tool_never_deletes_from_accepted(self):
        """Fitness function for ADR-0055, "`accepted` must be seen surviving
        the tool.": pointed at `accepted` with a threshold every row meets,
        it deletes nothing and sets only `Delete`; D12's path then saves and
        removes the copies. Mutation: "the tool deletes from accepted"."""
        for i in (1, 2):
            self.base.seed(TABLES["accepted"], {"Identity": "greenhouse:%d" % i,
                                                "Stage": "applied", "Published": ago(50)},
                           created=NOW - timedelta(days=45))
        report = self.confirmed("accepted", 15)
        self.assertEqual(report["marked_delete"], 2)
        self.assertEqual([c for c in self.base.calls if c["method"] == "DELETE"], [])
        for call in self.writes():
            for rec in (call["json"] or {}).get("records", []):
                self.assertEqual(set(rec["fields"]), {"Delete"})
        self.assertEqual([c["Delete"] for c in self.copies("accepted")], ["yes", "yes"])
        self.sweep()
        self.assertEqual(len(self.copies("accepted")), 2, "deleted before origin held it")
        self.sweep()
        self.assertEqual(self.copies("accepted"), [])
        self.assertEqual(len(self.store("removed_copies.json")), 2)

    def test_a_rejection_copy_leaves_early_with_its_classification_saved(self):
        """Seven days on `rejected-not-a-fit`: the copy and its `Jobs` row
        leave before their fifteen days, and the reason he gave is in the
        corpus first."""
        r = make_row(1, published=ago(12))
        self.store_rows([r])
        self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=10)
        self.base.seed(TABLES["rejected-not-a-fit"],
                       {"Identity": "greenhouse:1", "Choice reason": "salary",
                        "Published": ago(12)}, created=NOW - timedelta(days=10))
        report = self.confirmed("rejected-not-a-fit", 7)
        self.assertEqual(report["written"], 1)
        [record] = self.store("rejected_not_a_fit.json")
        self.assertEqual((record["reason"], record["removed_by"]), ("salary", "operator"))
        self.sweep()
        self.assertEqual((self.jobs(), self.copies("rejected-not-a-fit")), ([], []))

    def test_an_aggregator_row_is_masked_in_the_report_and_named_privately(self):
        r = make_row(1, source="himalayas", published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)
        report = self.confirmed(JOBS, 30)
        self.assertEqual(report["rows"], ["<aggregator row>"])
        [record] = self.store("removed_unreviewed.json", private=True)
        self.assertEqual(record["identity"], "himalayas:1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
