"""ADR-0055's clearing tool, against the in-memory base the sweep's tests use.

The tool writes stores and sets `Delete`; it deletes nothing. A later daily
sweep removes the rows once origin holds what the tool wrote, so each test
that follows a row out of the display runs the sweep after it.
"""

import os
import sys
import unittest
from datetime import timedelta
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import projection, storage
from src import run as run_module
from src.airtable_sweep import JOBS
from src.clearing import DRY_RUN_FILE, Clearing, ClearingError, request_from
from tests.test_sweep import CONFIG, MATCHER, NOW, TABLES, Harness, make_row

WINDOW = 48


def ago(days):
    return (NOW - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def at(when):
    return when.isoformat().replace("+00:00", "Z")


def dry_run_log(table, days, hours_ago=1, rows=(), test_mode=False, **clearing):
    """A run log carrying a dry run, as the run commits one."""
    block = {"table": table, "older_than_days": days, "confirmed": False, "failure": None,
             "rows": list(rows)}
    block.update(clearing)
    return {"run_at": at(NOW - timedelta(hours=hours_ago)), "test_mode": test_mode,
            "clearing": block}


def logged(report, when, test_mode=False):
    return {"run_at": at(when), "test_mode": test_mode, "clearing": report}


# The least a run log holds for its summary to be printed.
EMPTY_RUN_LOG = {"run_at": at(NOW), "test_mode": False, "boards": [], "stopped": None,
                 "totals": {"fetched": 0, "new": 0, "kept": 0, "written_raw": {},
                            "written_filtered": 0, "written_filtered_local": 0, "drops": {},
                            "dedupe": {}},
                 "requests": {"requests_used": 0, "budget": 500, "by_source": {}, "retries": 0,
                              "failures": 0}}


class ClearingHarness(Harness):
    def clear(self, table, days, confirmed=False, logs=None, private_ok=True, now=NOW,
              test_mode=False):
        client = self.client()
        report = Clearing(client, self.paths, now, private_ok, test_mode).run(
            table, days, confirmed, logs or [], WINDOW)
        report["calls_used"] = client.calls_used
        return report

    def confirmed(self, table, days, hours_after=1, private_ok=True):
        """A dry run, then its confirm `hours_after` later, bound to its log
        as the run binds them."""
        dry_at = NOW - timedelta(hours=hours_after)
        dry = self.clear(table, days, now=dry_at, private_ok=private_ok)
        return self.clear(table, days, confirmed=True, logs=[logged(dry, dry_at)],
                          private_ok=private_ok)

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

    def test_it_counts_the_classified_rows_whose_copies_leave_with_them(self):
        """Clearing `Jobs` takes a rejection copy with its row, early, and
        leaves an accepted copy to its `Delete`. The dry run counted `Jobs`
        rows only, so the copies leaving were a surprise (the fourth audit's
        F16, its probe F). Mutation: "the dry run does not count the
        classified rows"."""
        rows = [make_row(i, published=ago(40)) for i in (1, 2, 3)]
        self.store_rows(rows)
        self.in_jobs(rows[0])
        self.in_jobs(rows[1], status="rejected-not-a-fit", classified_days_ago=3)
        self.in_jobs(rows[2], status="accepted", classified_days_ago=3)
        report = self.clear(JOBS, 30)
        self.assertEqual(report["classified"], {"rejected-not-a-fit": 1, "accepted": 1})
        line = run_module.summarise(dict(EMPTY_RUN_LOG, clearing=report))
        self.assertIn("a rejection copy leaving with its row", line)


class TestTheConfirmation(ClearingHarness):
    def setUp(self):
        super().setUp()
        r = make_row(1, published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)

    def test_a_confirmed_run_needs_a_recent_dry_run_of_the_same_request(self):
        """Fitness function for ADR-0055, "The confirmation must be required.":
        confirming without a dry run on file refuses and writes nothing, as
        does one for another table, another threshold or too long ago, and,
        since the fourth audit's F2, a dry run that failed, a run that was
        itself confirmed, a dry run with no list of rows, and a dry run of the
        other mode in either direction. Mutation: "the confirmation is not
        required"."""
        listed = ["greenhouse:1"]
        no_list = dry_run_log(JOBS, 30, rows=listed)
        del no_list["clearing"]["rows"]
        for name, logs, test_mode in (
                ("none", [], False),
                ("another table", [dry_run_log("accepted", 30, rows=listed)], False),
                ("another threshold", [dry_run_log(JOBS, 15, rows=listed)], False),
                ("too long ago", [dry_run_log(JOBS, 30, hours_ago=WINDOW + 1, rows=listed)],
                 False),
                ("failed", [dry_run_log(JOBS, 30, rows=listed, failure="HttpError: 503")],
                 False),
                ("confirmed", [dry_run_log(JOBS, 30, rows=listed, confirmed=True)], False),
                ("no list", [no_list], False),
                ("production, for a test-mode confirm", [dry_run_log(JOBS, 30, rows=listed)],
                 True),
                ("test mode, for a production confirm",
                 [dry_run_log(JOBS, 30, rows=listed, test_mode=True)], False)):
            with self.subTest(name):
                report = self.clear(JOBS, 30, confirmed=True, logs=logs, test_mode=test_mode)
                self.assertTrue(report["failure"].startswith("refused"))
                self.assertEqual(self.store_files(), [])
                self.assertEqual(self.writes(), [])
        report = self.clear(JOBS, 30, confirmed=True, logs=[dry_run_log(JOBS, 30, rows=listed)])
        self.assertIsNone(report["failure"])
        self.assertEqual(report["written"], 1)

    def test_the_latest_dry_run_on_file_is_the_one_bound(self):
        """Two dry runs of the same request: the confirm follows the later
        one's list, which is what he read last."""
        r2 = make_row(2, published=ago(40))
        self.store_rows([make_row(1, published=ago(40)), r2])
        self.in_jobs(r2)
        logs = [dry_run_log(JOBS, 30, hours_ago=3, rows=["greenhouse:1"]),
                dry_run_log(JOBS, 30, hours_ago=1, rows=["greenhouse:1", "greenhouse:2"])]
        self.assertEqual(self.clear(JOBS, 30, confirmed=True, logs=logs)["written"], 2)
        self.assertEqual(self.clear(JOBS, 30, confirmed=True,
                                    logs=list(reversed(logs)))["already_leaving"], 2)


class TestTheConfirmIsBoundToItsDryRun(ClearingHarness):
    """The fourth audit's F1. A confirm selected again at its own clock, so a
    row that crossed the threshold in the 48 hours since the dry run was
    removed unseen, and `operator-removed` never returns."""

    def test_a_row_that_crossed_the_threshold_since_the_dry_run_is_left(self):
        """The audit's probe E: 40 and 31 days old at the confirm, the
        second 29 days old at the dry run 47 hours before. Only the first
        was shown, so only the first goes. Mutation: "a confirm removes rows
        its dry run never listed"."""
        old, crossed = make_row(1, published=ago(40)), make_row(2, published=ago(31))
        self.store_rows([old, crossed])
        self.in_jobs(old)
        self.in_jobs(crossed)
        report = self.confirmed(JOBS, 30, hours_after=47)
        self.assertEqual((report["written"], report["not_in_the_dry_run"]), (1, 1))
        self.assertEqual(report["rows"], ["greenhouse:1"])
        self.assertEqual([r["identity"] for r in self.store("removed_unreviewed.json")],
                         ["greenhouse:1"])
        self.sweep()
        self.assertEqual([j["Identity"] for j in self.jobs()], ["greenhouse:2"])

    def test_the_dry_run_names_aggregator_rows_privately_and_the_confirm_binds_to_them(self):
        """The public log masks an aggregator's row, so the dry run lists it,
        with what he needs to recognise it, in the private store; the
        confirm then removes it. The list is no store: the skip reads
        nothing from it. Mutations: "the dry run lists no aggregator row",
        "the dry run's list is written as a store"."""
        agg, pub = make_row(1, source="himalayas", published=ago(40)), make_row(2, published=ago(40))
        self.store_rows([agg, pub])
        self.in_jobs(agg)
        self.in_jobs(pub)
        dry_at = NOW - timedelta(hours=1)
        dry = self.clear(JOBS, 30, now=dry_at)
        self.assertEqual(sorted(dry["rows"]), ["<aggregator row>", "greenhouse:2"])
        self.assertEqual(dry["aggregator_listed_privately"], 1)
        [entry] = self.store(DRY_RUN_FILE, private=True)
        self.assertEqual((entry["identity"], entry["title"], entry["employer"], entry["dry_run_at"]),
                         ("himalayas:1", "AI Engineer", "Acme 1", at(dry_at)))
        self.assertEqual(projection.identities_in(projection.private_store_texts(self.paths)
                                                  + projection.public_store_texts(self.paths)),
                         set())
        self.assertNotIn(DRY_RUN_FILE, os.listdir(self.paths["outcomes_dir"])
                         if os.path.isdir(self.paths["outcomes_dir"]) else [])
        report = self.clear(JOBS, 30, confirmed=True, logs=[logged(dry, dry_at)])
        self.assertEqual((report["written"], report["not_in_the_dry_run"]), (2, 0))

    def test_a_dry_run_without_the_private_store_leaves_aggregator_rows_to_a_confirm(self):
        """Nowhere to list them, so nothing to bind to: the dry run says so,
        and the confirm leaves them rather than removing rows never shown."""
        agg = make_row(1, source="himalayas", published=ago(40))
        self.store_rows([agg])
        self.in_jobs(agg)
        dry_at = NOW - timedelta(hours=1)
        dry = self.clear(JOBS, 30, now=dry_at, private_ok=False)
        self.assertEqual(dry["aggregator_not_listed"], 1)
        report = self.clear(JOBS, 30, confirmed=True, logs=[logged(dry, dry_at)])
        self.assertEqual((report["written"], report["not_in_the_dry_run"]), (0, 1))
        self.assertEqual(self.store("removed_unreviewed.json", private=True), [])

    def test_the_summary_line_says_what_was_left_and_where_the_list_is(self):
        pub, agg = make_row(1, published=ago(40)), make_row(2, source="himalayas",
                                                            published=ago(40))
        crossed = make_row(3, published=ago(31))
        self.store_rows([pub, agg, crossed])
        for r in (pub, agg, crossed):
            self.in_jobs(r)
        dry_at = NOW - timedelta(hours=47)
        dry = self.clear(JOBS, 30, now=dry_at)
        line = run_module.summarise(dict(EMPTY_RUN_LOG, clearing=dry))
        self.assertIn("1 aggregator row(s) listed in the private store's %s" % DRY_RUN_FILE,
                      line)
        confirm = self.clear(JOBS, 30, confirmed=True, logs=[logged(dry, dry_at)])
        line += run_module.summarise(dict(EMPTY_RUN_LOG, clearing=confirm))
        self.assertIn("1 past the threshold since the dry run, left", line)
        self.assertNotIn("himalayas:", line)


class TestTheModeReachesTheTool(ClearingHarness):
    """The fourth audit's F2: in test mode the tool's client, the logs it
    reads and the tool itself all take the test mode. A production client
    in a test-mode dispatch would set `Delete` on production copies."""

    def setUp(self):
        super().setUp()
        self.real = (run_module.make_sweep_client, storage.read_recent_run_logs)
        self.asked = []

        def client(test_mode, used_this_month):
            self.asked.append(("client", test_mode))
            return self.client()

        def logs(count, test_mode=False):
            self.asked.append(("logs", test_mode))
            return [dry_run_log(JOBS, 30, rows=["greenhouse:1"], test_mode=True)]
        run_module.make_sweep_client, storage.read_recent_run_logs = client, logs

    def tearDown(self):
        run_module.make_sweep_client, storage.read_recent_run_logs = self.real
        super().tearDown()

    def test_a_test_mode_confirm_uses_the_test_mode_throughout(self):
        """Mutations: "the clearing tool in test mode reaches production",
        "a test-mode confirm reads production's logs", "the tool is told it
        is production"."""
        r = make_row(1, published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)
        run = SimpleNamespace(paths=self.paths, now=NOW)
        report = run_module.clear_display(run, False, True, (JOBS, 30, True), True, 0, CONFIG)
        self.assertEqual(self.asked, [("client", True), ("logs", True)])
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
