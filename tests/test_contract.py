"""The contract check, tested from ADR-0018 and ADR-0036.

Against the saved cassettes of real responses and a fake network, in a
throwaway repository. No test reaches a board.
"""

import ast
import contextlib
import copy
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import contract, storage
from src.adapters import greenhouse, himalayas, lever
from src.config import Board
from src.http_client import HttpClient
from tests.test_adapters import cassette

NOW = datetime(2026, 9, 24, 6, 30, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 25, 6, 30, tzinfo=timezone.utc)
GH = Board(platform="greenhouse", slug="careem")
LV = Board(platform="lever", slug="smart-working-solutions")
HIM = Board(platform="himalayas", slug="browse")
BOARDS = [GH, LV, HIM]


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status_code = status
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


class FakeSession:
    """Maps a URL fragment to a payload, or to a status code to answer."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append(url)
        for fragment, value in self.routes.items():
            if fragment in url:
                if isinstance(value, int):
                    return FakeResponse({}, status=value)
                return FakeResponse(copy.deepcopy(value))
        return FakeResponse({}, status=404)


def responses():
    return {"careem": cassette("greenhouse-careem.json"),
            "smart-working": cassette("lever-smart-working-solutions.json"),
            "himalayas": cassette("himalayas-browse.json")}


def client(routes):
    return HttpClient(session=FakeSession(routes), sleep=lambda s: None, min_interval=0,
                      max_attempts=1)


def reads_of(module):
    return reads_in(inspect.getsource(module))


def reads_in(source):
    """Every key the source reads from a response: the string given to a
    `.get()` or a subscript, with a module constant resolved to its value."""
    tree = ast.parse(source)
    names = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = node.value.value

    def key(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        return None

    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get" and node.args:
            k = key(node.args[0])
        elif isinstance(node, ast.Subscript):
            k = key(node.slice)
        else:
            continue
        if k is not None:
            found.add(k)
    return found


class TestConsumedFields(unittest.TestCase):
    """ADR-0018 fingerprints the fields each adapter consumes. A list that
    drifted from the code would fingerprint fields nobody reads, or miss one
    that is read, and the check would watch the wrong thing."""

    def test_each_adapter_declares_exactly_what_it_reads(self):
        for module in (greenhouse, lever, himalayas):
            with self.subTest(adapter=module.PLATFORM):
                declared = {path.split(".")[-1]
                            for path in module.CONSUMED + module.CONSUMED_RESPONSE}
                self.assertEqual(reads_of(module), declared)

    def test_each_declared_path_is_a_real_path_in_a_saved_response(self):
        """Compared on its last name alone, `location.name` could become a
        top-level `name` no posting has, and the fingerprint would watch
        nothing (the audit of 2026-09-24, F5). So every undotted path must be
        a key the saved response really has, and every dotted one must hang
        off a declared parent."""
        # Greenhouse's as the run requests it since 2026-09-26, with
        # `?content=true`, which adds `offices`.
        saved = {"greenhouse": "greenhouse-careem-content.json",
                 "lever": "lever-smart-working-solutions.json",
                 "himalayas": "himalayas-browse.json"}
        for module in (greenhouse, lever, himalayas):
            with self.subTest(adapter=module.PLATFORM):
                payload = cassette(saved[module.PLATFORM])
                keys = set()
                for posting in contract.postings_in(module, payload):
                    keys |= set(posting)
                for path in module.CONSUMED:
                    parent = path.rpartition(".")[0]
                    if parent:
                        self.assertIn(parent, module.CONSUMED, path)
                    else:
                        self.assertIn(path, keys, path)
                for path in module.CONSUMED_RESPONSE:
                    self.assertIn(path, payload, path)

    def test_the_reader_is_not_blind(self):
        """The case built to defeat the test above: a key read through a
        literal, through a module constant and through a subscript must all
        show, and a non-string key must not."""
        source = "\n".join(["KEY = 'b'",
                            "def parse(p):",
                            "    return p.get('a'), p.get(KEY), p['c'], p[0]"])
        self.assertEqual(reads_in(source), {"a", "b", "c"})

    def test_every_platform_the_run_polls_is_checked(self):
        from src.run import ADAPTERS
        self.assertEqual(set(contract.PLATFORMS), set(ADAPTERS))


class TestShape(unittest.TestCase):
    def test_presence_nulls_and_types_are_words_not_counts(self):
        self.assertEqual(contract.shape([(True, "a"), (True, "b")]),
                         {"present": "all", "null": "never", "types": ["string"]})
        self.assertEqual(contract.shape([(True, None), (False, None)]),
                         {"present": "some", "null": "always", "types": []})
        self.assertEqual(contract.shape([(True, 1), (True, None), (True, "x")]),
                         {"present": "all", "null": "some", "types": ["number", "string"]})
        self.assertEqual(contract.shape([(False, None)]),
                         {"present": "none", "null": "never", "types": []})

    def test_a_boolean_is_not_a_number(self):
        self.assertEqual(contract.type_name(True), "boolean")

    def test_a_path_through_a_null_is_absent(self):
        self.assertEqual(contract.resolve({"location": None}, "location.name"), (False, None))
        self.assertEqual(contract.resolve({"location": {"name": "X"}}, "location.name"),
                         (True, "X"))

    def test_a_path_into_a_list_reads_its_items(self):
        """Greenhouse's `offices.location`: present when any item has it.
        Read as absent, it would fingerprint nothing and a rename inside
        would never show. Mutation: "a path through a list is absent"."""
        posting = {"offices": [{"id": 1}, {"location": "Lahore, Pakistan"}]}
        self.assertEqual(contract.resolve(posting, "offices.location"),
                         (True, "Lahore, Pakistan"))
        self.assertEqual(contract.resolve({"offices": []}, "offices.location"), (False, None))
        self.assertEqual(contract.resolve({"offices": [{"id": 1}]}, "offices.location"),
                         (False, None))

    def test_the_cassette_tool_strips_people(self):
        """A board's custom fields name hiring managers and recruiters, by
        email or by name; no cassette may carry one. Mutation: "the cassette
        tool keeps people's addresses"."""
        from src.adapters import greenhouse
        from tools.make_cassette import KEPT_METADATA, PLACEHOLDER, sanitise
        self.assertEqual(set(KEPT_METADATA),
                         set(greenhouse.COUNTRY_FIELDS + greenhouse.WORKPLACE_FIELDS))
        out = sanitise([{"metadata": [
            {"name": "Hiring Lead", "value": "A Person", "value_type": "short_text"},
            {"name": "Job Approver", "value": {"name": "B"}, "value_type": "user"},
            {"name": "Country", "value": "Pakistan", "value_type": "single_select"}],
            "note": "write to someone@example.com"}])
        self.assertEqual([m["value"] for m in out[0]["metadata"]],
                         [PLACEHOLDER, PLACEHOLDER, "Pakistan"])
        self.assertEqual(out[0]["note"], PLACEHOLDER)

    def test_the_fingerprint_holds_no_value_from_any_posting(self):
        """Structure only: Himalayas' fingerprint sits on the public branch."""
        payload = cassette("himalayas-browse.json")
        fp, count = contract.fingerprint(himalayas, payload)
        self.assertGreater(count, 0)
        text = json.dumps(fp)
        for job in payload["jobs"]:
            for field in ("title", "companyName", "guid", "applicationLink"):
                if job.get(field):
                    self.assertNotIn(str(job[field]), text)


class TestCheck(unittest.TestCase):
    def test_the_first_check_is_a_baseline_and_the_second_unchanged(self):
        fp, log = contract.check(BOARDS, client(responses()), {}, NOW)
        self.assertEqual({p: e["status"] for p, e in log["platforms"].items()},
                         dict.fromkeys(contract.PLATFORMS, "baseline"))
        _, log = contract.check(BOARDS, client(responses()), fp, LATER)
        self.assertEqual({p: e["status"] for p, e in log["platforms"].items()},
                         dict.fromkeys(contract.PLATFORMS, "unchanged"))

    def test_a_field_removed_from_the_stored_fingerprint_is_named(self):
        """ADR-0018's Confirmation, offline: hand-edit a stored fingerprint to
        remove a field and the check must name it."""
        fp, _ = contract.check(BOARDS, client(responses()), {}, NOW)
        del fp["lever"]["posting"]["hostedUrl"]
        _, log = contract.check(BOARDS, client(responses()), fp, LATER)
        entry = log["platforms"]["lever"]
        self.assertEqual(entry["status"], "changed")
        self.assertEqual([c["field"] for c in entry["changes"]], ["hostedUrl"])
        self.assertEqual(entry["changes"][0]["was"], "not in the stored fingerprint")
        self.assertEqual(log["platforms"]["greenhouse"]["status"], "unchanged")

    def test_a_field_turning_null_or_changing_type_is_named_with_both_shapes(self):
        fp, _ = contract.check(BOARDS, client(responses()), {}, NOW)
        routes = responses()
        for job in routes["careem"]["jobs"]:
            job["absolute_url"] = None
            job["id"] = str(job["id"])
        _, log = contract.check(BOARDS, client(routes), fp, LATER)
        changes = {c["field"]: c for c in log["platforms"]["greenhouse"]["changes"]}
        self.assertEqual(sorted(changes), ["absolute_url", "id"])
        self.assertEqual(changes["absolute_url"]["now"]["null"], "always")
        self.assertEqual(changes["id"]["was"]["types"], ["number"])
        self.assertEqual(changes["id"]["now"]["types"], ["string"])

    def test_an_unreachable_board_is_logged_and_keeps_its_last_fingerprint(self):
        fp, _ = contract.check(BOARDS, client(responses()), {}, NOW)
        routes = responses()
        routes["smart-working"] = 404
        after, log = contract.check(BOARDS, client(routes), fp, LATER)
        self.assertEqual(log["platforms"]["lever"]["status"], "unreachable")
        self.assertEqual(after["lever"], fp["lever"])

    def test_a_renamed_list_of_postings_is_a_change_not_a_crash(self):
        fp, _ = contract.check(BOARDS, client(responses()), {}, NOW)
        routes = responses()
        routes["careem"] = {"postings": routes["careem"]["jobs"]}
        _, log = contract.check(BOARDS, client(routes), fp, LATER)
        entry = log["platforms"]["greenhouse"]
        self.assertEqual(entry["postings"], 0)
        self.assertEqual([c["field"] for c in entry["changes"]], ["jobs"])

    def test_one_request_per_platform(self):
        c = client(responses())
        contract.check(BOARDS, c, {}, NOW)
        self.assertEqual(len(c._session.calls), len(contract.PLATFORMS))


class TestTheDeliberateRebaseline(unittest.TestCase):
    """ADR-0036, 2026-09-28: a difference we caused is ours and says so."""

    def entry(self, date, fields, platform="lever"):
        return [{"platform": platform, "date": date, "cause": "we moved it", "fields": fields}]

    def changed_lever(self):
        fp, _ = contract.check(BOARDS, client(responses()), {}, NOW)
        del fp["lever"]["posting"]["hostedUrl"]
        return fp

    def test_a_recorded_change_is_ours(self):
        """Fitness function for ADR-0036, "A contract change we caused
        ourselves is re-baselined deliberately, and the re-baseline is
        recorded.": the difference is named, marked ours with the date and
        cause on file, and the platform reads re-baselined, not changed.
        Mutation: "a recorded re-baseline is ignored"."""
        _, log = contract.check(BOARDS, client(responses()), self.changed_lever(), LATER,
                                self.entry("2026-09-25", ["posting.hostedUrl"]))
        entry = log["platforms"]["lever"]
        self.assertEqual(entry["status"], "re-baselined")
        self.assertEqual(entry["changes"][0]["ours"], "2026-09-25: we moved it")
        self.assertIn("[ours, 2026-09-25: we moved it]", contract.summarise(log))

    def test_an_unrecorded_change_is_still_a_change(self):
        _, log = contract.check(BOARDS, client(responses()), self.changed_lever(), LATER,
                                self.entry("2026-09-25", ["posting.text"]))
        self.assertEqual(log["platforms"]["lever"]["status"], "changed")
        self.assertNotIn("ours", log["platforms"]["lever"]["changes"][0])

    def test_an_old_entry_never_excuses_a_later_change(self):
        """The case built to defeat a re-baseline file: once a shape is
        accepted, the entry that explained it is spent. The same field moving
        again, later, is the board, and must read changed. Mutation: "an old
        re-baseline excuses a later change"."""
        rebaselines = self.entry("2026-09-25", ["posting.hostedUrl"])
        accepted, _ = contract.check(BOARDS, client(responses()), self.changed_lever(), LATER,
                                     rebaselines)
        self.assertEqual(accepted["lever"]["since"], "2026-09-25")
        del accepted["lever"]["posting"]["hostedUrl"]
        _, log = contract.check(BOARDS, client(responses()), accepted,
                                datetime(2026, 9, 30, 6, 30, tzinfo=timezone.utc), rebaselines)
        self.assertEqual(log["platforms"]["lever"]["status"], "changed")

    def test_a_shape_with_no_acceptance_date_is_never_excused(self):
        """The fourth audit's F5, the case built to defeat the first build:
        every shape stored before 2026-09-30 lacks `since`, and reading the
        gap as older than everything let a spent entry excuse the next
        check's changes. Mutation: "a shape with no acceptance date reads as
        older than every entry"."""
        fp = self.changed_lever()
        del fp["lever"]["since"]
        updated, log = contract.check(BOARDS, client(responses()), fp, LATER,
                                      self.entry("2026-09-25", ["posting.hostedUrl"]))
        self.assertEqual(log["platforms"]["lever"]["status"], "changed")
        self.assertEqual(updated["lever"]["since"], "2026-09-25", "it gains its date now")

    def test_an_entry_dated_after_today_excuses_nothing_yet(self):
        """Mutation: "an entry dated in the future excuses a change today"."""
        _, log = contract.check(BOARDS, client(responses()), self.changed_lever(), LATER,
                                self.entry("2026-12-31", ["posting.hostedUrl"]))
        self.assertEqual(log["platforms"]["lever"]["status"], "changed")

    def test_a_date_that_is_not_a_calendar_date_is_refused(self):
        """The fourth audit's probe H2 loaded both of these. Mutation: "any ten
        characters pass as a date"."""
        path = os.path.join(tempfile.mkdtemp(), "r.json")
        for date in ("2026-19-26", "9999-99-99", "2026-02-30"):
            with self.subTest(date=date):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"rebaselines": [{"platform": "lever", "date": date, "cause": "x",
                                                "fields": ["posting.text"]}]}, f)
                with self.assertRaises(contract.ConfigError):
                    contract.load_rebaselines(path)

    def test_one_unexplained_field_among_ours_is_a_change(self):
        fp = self.changed_lever()
        del fp["lever"]["posting"]["text"]
        _, log = contract.check(BOARDS, client(responses()), fp, LATER,
                                self.entry("2026-09-25", ["posting.hostedUrl"]))
        entry = log["platforms"]["lever"]
        self.assertEqual(entry["status"], "changed")
        self.assertEqual(sorted(c["field"] for c in entry["changes"] if c.get("ours")),
                         ["hostedUrl"])

    def test_a_malformed_entry_stops_the_check(self):
        path = os.path.join(tempfile.mkdtemp(), "r.json")
        for bad in ({"rebaselines": [{"platform": "lever", "date": "2026-9-1",
                                      "cause": "x", "fields": ["a"]}]},
                    {"rebaselines": [{"platform": "nowhere", "date": "2026-09-01",
                                      "cause": "x", "fields": ["a"]}]},
                    {"rebaselines": [{"platform": "lever", "date": "2026-09-01",
                                      "fields": ["a"]}]}):
            with self.subTest(bad=bad):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(bad, f)
                with self.assertRaises(contract.ConfigError):
                    contract.load_rebaselines(path)

    def test_the_search_move_is_on_file_with_the_fields_it_moved(self):
        """The check of 2026-09-27 reported exactly these four Himalayas
        fields; the entry that explains them must name exactly these."""
        [entry] = [e for e in contract.load_rebaselines()
                   if e["platform"] == "himalayas" and e["date"] == "2026-09-26"]
        self.assertEqual(sorted(entry["fields"]), ["response.limit", "response.nextCursor",
                                                   "response.offset", "response.totalCount"])

    def test_reading_seniority_is_on_file_with_the_field_it_adds(self):
        """2026-10-02: the adapter reads one more field, so the check would
        report it as changed; the entry says it was ours."""
        from src.adapters import himalayas
        self.assertIn("seniority", himalayas.CONSUMED)
        [entry] = [e for e in contract.load_rebaselines()
                   if e["platform"] == "himalayas" and e["date"] == "2026-10-02"]
        self.assertEqual(entry["fields"], ["posting.seniority"])


class TestMain(unittest.TestCase):
    """End to end against a throwaway repository, as the workflow runs it."""

    def setUp(self):
        self.env_test_mode = os.environ.pop("TEST_MODE", None)
        self.dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.real = (storage.REPO_ROOT, contract.load_boards, contract.HttpClient)
        storage.REPO_ROOT = self.dir
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.routes = responses()
        contract.load_boards = lambda: BOARDS
        contract.HttpClient = lambda **kw: client(self.routes)

    def tearDown(self):
        storage.REPO_ROOT, contract.load_boards, contract.HttpClient = self.real
        os.environ.pop("TEST_MODE", None)
        if self.env_test_mode is not None:
            os.environ["TEST_MODE"] = self.env_test_mode
        os.chdir(self.cwd)
        shutil.rmtree(self.dir, ignore_errors=True)

    def main(self, *argv, now=NOW):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = contract.main(list(argv), now=now)
        return code, out.getvalue(), err.getvalue()

    def on_branch(self, branch, path):
        p = subprocess.run(["git", "show", "%s:%s" % (branch, path)], cwd=self.dir,
                           capture_output=True, text=True, encoding="utf-8")
        return p.stdout if p.returncode == 0 else None

    def logs(self, branch="data"):
        p = subprocess.run(["git", "ls-tree", "--name-only", branch, contract.LOG_DIR + "/"],
                           cwd=self.dir, capture_output=True, text=True)
        return sorted(p.stdout.split())

    def test_a_renamed_field_exits_0_both_times_and_is_named_with_both_shapes(self):
        """ADR-0036's Confirmation: run twice against a saved response with one
        field renamed in the second."""
        self.assertEqual(self.main()[0], 0)
        for job in self.routes["smart-working"]:
            job["url"] = job.pop("hostedUrl")
        code, out, _ = self.main(now=LATER)
        self.assertEqual(code, 0)
        log = json.loads(self.on_branch("data", self.logs()[-1]))
        [change] = log["platforms"]["lever"]["changes"]
        self.assertEqual(change["field"], "hostedUrl")
        self.assertEqual(change["was"]["present"], "all")
        self.assertEqual(change["now"]["present"], "none")
        self.assertIn("hostedUrl", out)

    def test_a_crash_exits_1_and_commits_no_log(self):
        """ADR-0036's check that can fail: a crash and a finding never share
        a channel."""
        def broken(**kw):
            raise RuntimeError("the check itself is broken")
        contract.HttpClient = broken
        code, _, err = self.main()
        self.assertEqual(code, 1)
        self.assertIn("the contract check itself failed", err)
        self.assertEqual(self.logs(), [])

    def test_its_logs_never_land_among_the_fetch_run_logs(self):
        """The fetch counts failed projections in a row from logs-runs/. A
        contract log there would read as a success and reset the count."""
        self.main()
        self.assertEqual(len(self.logs()), 1)
        self.assertEqual(storage.read_recent_run_logs(5, False), [])

    def test_test_mode_writes_the_test_branch_only(self):
        self.main("--test-mode")
        self.assertIsNotNone(self.on_branch("data-test", contract.FINGERPRINT_FILE))
        self.assertIsNone(self.on_branch("data", contract.FINGERPRINT_FILE))

    def test_a_no_commit_check_commits_nothing(self):
        self.assertEqual(self.main("--no-commit")[0], 0)
        self.assertEqual(self.logs(), [])
        self.assertTrue(os.path.exists("data/%s" % contract.FINGERPRINT_FILE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
