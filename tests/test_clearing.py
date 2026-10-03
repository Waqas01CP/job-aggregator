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
from src.clearing import DRY_RUN_FILE, DRY_RUN_PATH, Clearing, ClearingError, request_from
from src.normalise import dumps
from src.private_store import files_to_push, local_path_for
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

    def outcome_bytes(self):
        """Every file under both outcome directories, with its contents."""
        found = {}
        for key in ("outcomes_dir", "local_outcomes_dir"):
            directory = self.paths[key]
            if os.path.isdir(directory):
                for name in sorted(os.listdir(directory)):
                    with open(os.path.join(directory, name), "rb") as f:
                        found["%s/%s" % (key, name)] = f.read()
        return found

    def dry_run_list(self):
        return storage.read_records("%s/%s" % (self.paths["local_clearing_dir"], DRY_RUN_FILE))


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


class TestWhatIsLeavingAnyway(ClearingHarness):
    """The operator's request of 2026-10-03. His dry run of 10-02 listed 19
    rows and his confirm removed 2: the same run's sweep, which runs first,
    had stored the other 17 for removal, and nothing on the line he read
    said so."""

    def test_a_row_the_sweep_just_stored_for_removal_is_counted(self):
        """A row a rule now drops is stored by the sweep and deleted on a later
        run; the dry run counts it, and not the row nothing removes. Twenty
        days old, so the thirty-day clock takes neither. Mutations: "the dry
        run counts nothing as leaving anyway", "a row this run's sweep stored
        is not counted"."""
        dropped = make_row(1, published=ago(20), location="New York, United States")
        kept = make_row(2, published=ago(20))
        self.store_rows([dropped, kept])
        self.in_jobs(dropped)
        self.in_jobs(kept)
        self.assertEqual(self.sweep()["waiting_for_the_store"], 1)
        dry = self.clear(JOBS, 15)
        self.assertEqual((dry["would_remove"], dry["leaving_without_the_tool"]), (2, 1))
        line = run_module.summarise(dict(EMPTY_RUN_LOG, clearing=dry))
        self.assertIn("would remove 2", line)
        self.assertIn("1 of them already on their way out without it", line)

    def test_rows_held_out_classified_or_marked_are_counted(self):
        """A row kept out for good by an earlier removal, a classified row
        whose outcome is stored, and an accepted copy whose Delete is set
        all leave without the tool. A row nothing holds is not counted.
        Mutation: "a row kept out for good is not counted"."""
        held, classified, open_row = (make_row(i, published=ago(40)) for i in (1, 2, 3))
        self.store_rows([held, classified, open_row])
        self.in_jobs(held)
        self.in_jobs(classified, status="rejected-not-a-fit", classified_days_ago=3)
        self.in_jobs(open_row)
        storage.write_atomic("%s/removed_unreviewed.json" % self.paths["outcomes_dir"], dumps([
            dict(held.as_record(), reason="operator-removed", removal="greenhouse:1|operator-removed",
                 swept_at=ago(2))]))
        storage.write_atomic("%s/rejected_not_a_fit.json" % self.paths["outcomes_dir"], dumps([
            dict(classified.as_record(), status="rejected-not-a-fit", swept_at=ago(2))]))
        self.assertEqual(self.clear(JOBS, 30)["leaving_without_the_tool"], 2)
        for i, delete in ((4, "yes"), (5, None)):
            fields = {"Identity": "greenhouse:%d" % i, "Stage": "applied", "Published": ago(50)}
            if delete:
                fields["Delete"] = delete
            self.base.seed(TABLES["accepted"], fields, created=NOW - timedelta(days=45))
        self.assertEqual(self.clear("accepted", 15)["leaving_without_the_tool"], 1)


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
        [entry] = self.dry_run_list()
        self.assertEqual((entry["identity"], entry["title"], entry["employer"], entry["dry_run_at"]),
                         ("himalayas:1", "AI Engineer", "Acme 1", at(dry_at)))
        self.assertEqual(projection.identities_in(projection.private_store_texts(self.paths)
                                                  + projection.public_store_texts(self.paths)),
                         set())
        report = self.clear(JOBS, 30, confirmed=True, logs=[logged(dry, dry_at)])
        self.assertEqual((report["written"], report["not_in_the_dry_run"]), (2, 0))

    def test_the_dry_runs_list_sits_outside_every_outcome_directory(self):
        """ADR-0055, clarified 2026-10-03: "That list is not a store and lives
        outside `outcomes/`, so the guarantee holds by where the file sits
        and not only by a test." A dry run naming an aggregator row leaves
        both outcome directories byte for byte as they were; its list goes
        to the private store under `clearing/` and comes back to where the
        confirm reads it. Mutation: "the dry run's list is kept among the
        outcome stores"."""
        agg = make_row(1, source="himalayas", published=ago(40))
        self.store_rows([agg])
        self.in_jobs(agg)
        storage.write_atomic("%s/removed_unreviewed.json" % self.paths["local_outcomes_dir"],
                             dumps([]))
        before = self.outcome_bytes()
        self.assertEqual(self.clear(JOBS, 30)["aggregator_listed_privately"], 1)
        self.assertEqual(self.outcome_bytes(), before)
        pushed = files_to_push(self.paths)
        self.assertIn(DRY_RUN_PATH, pushed)
        self.assertEqual([p for p in pushed if p.startswith("outcomes/")],
                         ["outcomes/removed_unreviewed.json"])
        self.assertEqual(local_path_for(DRY_RUN_PATH, self.paths),
                         "%s/%s" % (self.paths["local_clearing_dir"], DRY_RUN_FILE))

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
        self.assertIn("1 aggregator row(s) listed in the private store's clearing/dry_runs.json",
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

    def test_clearing_a_classified_jobs_row_stores_its_verdict_before_anything_leaves(self):
        """ADR-0055, the operator's decision of 2026-10-03: clearing a
        classified `Jobs` row takes its rejection copy with it, only after
        the outcome and its reason are in the classification store. ADR-0050
        writes that outcome fifteen days after classification, by reading
        the row, so a row cleared sooner would otherwise take his verdict
        with it. The confirm stores the status and the reason from the copy
        and deletes nothing; the sweep then removes the row and the copy
        together. Mutations: "clearing Jobs passes over a classified row",
        "clearing Jobs stores a classified row without its reason"."""
        r = make_row(1, published=ago(40))
        self.store_rows([r])
        self.in_jobs(r, status="rejected-not-a-fit", classified_days_ago=3)
        self.base.seed(TABLES["rejected-not-a-fit"],
                       {"Identity": "greenhouse:1", "Choice reason": "salary",
                        "Published": ago(40)}, created=NOW - timedelta(days=3))
        report = self.confirmed(JOBS, 30)
        self.assertEqual(report["written"], 1)
        [record] = self.store("rejected_not_a_fit.json")
        self.assertEqual((record["identity"], record["status"], record["reason"],
                          record["removed_by"]),
                         ("greenhouse:1", "rejected-not-a-fit", "salary", "operator"))
        self.assertEqual((len(self.jobs()), len(self.copies("rejected-not-a-fit"))), (1, 1),
                         "the tool deletes nothing")
        self.sweep()
        self.assertEqual((self.jobs(), self.copies("rejected-not-a-fit")), ([], []))
        self.assertEqual(self.store("removed_unreviewed.json"), [])

    def test_an_aggregator_row_is_masked_in_the_report_and_named_privately(self):
        r = make_row(1, source="himalayas", published=ago(40))
        self.store_rows([r])
        self.in_jobs(r)
        report = self.confirmed(JOBS, 30)
        self.assertEqual(report["rows"], ["<aggregator row>"])
        [record] = self.store("removed_unreviewed.json", private=True)
        self.assertEqual(record["identity"], "himalayas:1")


class TestAPartialClearSaysSo(ClearingHarness):
    """A clear that fails part-way has stored some rows, which the next sweep
    removes as asked. The run is green with a warning, so the line he reads
    must say how many, or a partial clear looks like nothing happened."""

    def setUp(self):
        super().setUp()
        self.real = (run_module.make_sweep_client, storage.read_recent_run_logs)
        harness = self

        def client(test_mode, used_this_month):
            c = harness.client()
            listing = c.list_records

            def list_records(table, fields):
                if table != JOBS:
                    raise RuntimeError("the base stopped answering")
                return listing(table, fields)
            c.list_records = list_records
            return c
        run_module.make_sweep_client = client
        storage.read_recent_run_logs = lambda count, test_mode=False: [
            dry_run_log(JOBS, 30, rows=["greenhouse:1", "greenhouse:2"])]

    def tearDown(self):
        run_module.make_sweep_client, storage.read_recent_run_logs = self.real
        super().tearDown()

    def test_rows_stored_before_a_failure_are_counted_on_the_summary_line(self):
        """Mutation: "a failed clear forgets what it stored"."""
        unreviewed, classified = make_row(1, published=ago(40)), make_row(2, published=ago(40))
        self.store_rows([unreviewed, classified])
        self.in_jobs(unreviewed)
        self.in_jobs(classified, status="rejected-not-a-fit", classified_days_ago=3)
        run = SimpleNamespace(paths=self.paths, now=NOW)
        report = run_module.clear_display(run, False, False, (JOBS, 30, True), True, 0, CONFIG)
        self.assertIn("RuntimeError", report["failure"])
        self.assertEqual(sum(report["stored_written"].values()), 1)
        line = run_module.summarise(dict(EMPTY_RUN_LOG, clearing=report))
        self.assertIn("1 row(s) stored before it failed", line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
