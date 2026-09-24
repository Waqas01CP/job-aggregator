"""The heredoc guard, and the measurement that rebuilt it.

Every command here is built with chr(92) rather than typed, because a test
file for this guard is the last place a stray backslash should be ambiguous.

**The guard was rebuilt on 2026-09-18 after being proved backwards.** Its
first design asked when a heredoc carried a backslash and wrote a file. Run
against the real hook payload, it asked on the text as typed and allowed the
text it actually received: the escape is converted before the hook sees the
command, so the guard fired on surviving backslashes, which are regex
patterns and harmless, and stayed silent on converted ones, which are the
failure. TestTheOldDesignWasBackwards keeps that case, because it is the
reason the trigger is what it is.

The guard's value is that it stays quiet. Half these tests are cases it must
not fire on: a guard that fires on ordinary analysis becomes something to
click through, and a gate people click through is worse than none.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.heredoc_guard import heredoc_bodies, verdict, written_paths

BS = chr(92)
NL = chr(10)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def heredoc(*body_lines):
    return "python - <<'PY'" + NL + NL.join(body_lines) + NL + "PY"


class TestTheOldDesignWasBackwards(unittest.TestCase):
    """The measurement that forced the rebuild. Keep it: without it, the
    backslash trigger looks obviously correct and someone will restore it."""

    def test_the_command_as_received_has_no_backslash_left_to_test(self):
        """What the hook receives after the escape is converted. A trigger
        that tested for a backslash would allow this, and this is the exact
        shape that broke src/filters.py twice."""
        received = heredoc('io.open("src/filters.py", "w").write("a' + NL + 'b")')
        self.assertNotIn(BS, received, "the escape is already gone by now")
        self.assertTrue(verdict(received)[0],
                        "the guard must catch the command as it arrives")

    def test_a_surviving_backslash_alone_is_not_a_reason_to_ask(self):
        """Regex backslashes do survive, and they are the harmless case. The
        old design fired here and nowhere useful."""
        cmd = heredoc("import re", 'print(re.findall(r"' + BS + 'd{4}", "0045"))')
        self.assertIn(BS, cmd)
        self.assertFalse(verdict(cmd)[0])


class TestItAsks(unittest.TestCase):
    def test_writing_a_source_file(self):
        asks, reason = verdict(heredoc('io.open("src/filters.py", "w").write(s)'))
        self.assertTrue(asks)
        self.assertIn("src/filters.py", reason)
        self.assertIn("Write or Edit tool", reason)

    def test_writing_a_tracked_document(self):
        self.assertTrue(verdict(heredoc('io.open("docs/x.md", "w").write(s)'))[0])

    def test_a_shell_redirect_into_the_repository(self):
        cmd = "cat > src/x.py <<'EOF'" + NL + "x = 1" + NL + "EOF"
        self.assertTrue(verdict(cmd)[0])

    def test_write_atomic_the_repository_s_own_writer(self):
        self.assertTrue(verdict(heredoc('write_atomic("STATE.md", s)'))[0])

    def test_append_mode_counts(self):
        self.assertTrue(verdict(heredoc('open("logs/x.md", "a").write(s)'))[0])


class TestItStaysQuiet(unittest.TestCase):
    def test_analysis_that_only_reads_and_prints(self):
        """The common case by far, and the one that must never be blocked."""
        cmd = heredoc("import json", 'print(len(json.load(open("data/x.json"))))')
        self.assertFalse(verdict(cmd)[0])

    def test_writing_to_the_scratchpad(self):
        cmd = heredoc('io.open("/tmp/claude/scratchpad/x.txt", "w").write(s)')
        self.assertFalse(verdict(cmd)[0])

    def test_writing_to_the_gitignored_data_directory(self):
        """The pipeline's own output. Nothing there is tracked, so nothing
        there can be corrupted in a way that survives a run."""
        self.assertFalse(verdict(heredoc('io.open("data/filtered.json", "w").write(s)'))[0])

    def test_a_windows_scratchpad_path_with_backslashes(self):
        path = "C:" + BS + "Temp" + BS + "claude" + BS + "scratchpad" + BS + "x.txt"
        self.assertFalse(verdict(heredoc('io.open("' + path + '", "w").write(s)'))[0])

    def test_a_command_with_no_heredoc(self):
        self.assertFalse(verdict('grep -rn "' + BS + 'd" src/')[0])

    def test_an_empty_command(self):
        self.assertFalse(verdict("")[0])


class TestParsing(unittest.TestCase):
    def test_quoted_and_unquoted_delimiters_are_both_found(self):
        for opener in ("<<'PY'", '<<"PY"', "<<PY", "<<-PY"):
            cmd = "python - " + opener + NL + "body" + NL + "PY"
            self.assertEqual(len(heredoc_bodies(cmd)), 1, opener)

    def test_text_inside_a_body_is_not_read_as_another_opener(self):
        self.assertEqual(len(heredoc_bodies(heredoc('print("use <<EOF in docs")'))), 1)

    def test_two_heredocs_are_both_seen(self):
        self.assertEqual(len(heredoc_bodies(heredoc("one") + NL + heredoc("two"))), 2)

    def test_the_written_path_is_extracted_not_guessed(self):
        paths = written_paths('io.open("src/a.py", "w").write(x)', "")
        self.assertIn("src/a.py", paths)


class TestTheHookContract(unittest.TestCase):
    """What Claude Code actually sends on stdin and reads from stdout."""

    def run_guard(self, payload):
        return subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "heredoc_guard.py")],
            input=json.dumps(payload), capture_output=True, text=True)

    def test_it_emits_an_ask_decision_not_a_deny(self):
        """Ask, never deny. A guard that refuses outright is routed around."""
        cmd = heredoc('open("src/x.py", "w").write(s)')
        out = self.run_guard({"tool_name": "Bash", "tool_input": {"command": cmd}})
        self.assertEqual(out.returncode, 0)
        decision = json.loads(out.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "ask")
        self.assertTrue(decision["permissionDecisionReason"])

    def test_it_says_nothing_when_the_command_is_fine(self):
        out = self.run_guard({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "")

    def test_a_malformed_payload_never_blocks_a_tool_call(self):
        """A guard that failed closed on its own bug would stop work for a
        reason nobody could see."""
        out = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "heredoc_guard.py")],
            input="not json at all", capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "")

    def test_a_payload_with_no_command_is_handled(self):
        out = self.run_guard({"tool_name": "Bash", "tool_input": {}})
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def launcher():
    """The exact launcher the hook runs, read from .claude/settings.json, so a
    change there is what these tests exercise."""
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as f:
        hook = json.load(f)["hooks"]["PreToolUse"][0]["hooks"][0]
    assert hook["command"] == "python" and hook["args"][0] == "-c", hook
    return hook["args"][1]


def run_launcher(payload, cwd, project_dir=None):
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    if project_dir:
        env["CLAUDE_PROJECT_DIR"] = project_dir
    return subprocess.run([sys.executable, "-c", launcher()],
                          input=payload if isinstance(payload, str) else json.dumps(payload),
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=60)


RISKY = {"tool_input": {"command": "cat <<'EOF' > src/x.py" + chr(10) + "print(1)"
                                  + chr(10) + "EOF"}}
HARMLESS = {"tool_input": {"command": "git status --short"}}


class TestTheLauncher(unittest.TestCase):
    """The hook once ran `python tools/heredoc_guard.py`, a path relative to
    the working directory. From any subdirectory Python exited 2 on the
    missing script, a PreToolUse hook reads 2 as block, and every Bash call was
    refused. The launcher finds the guard from wherever it runs and never
    blocks. Before 2026-09-24 nothing in the repository tested it; its only
    proof was a scratchpad script, which the audit of that date reported."""

    def decision(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)

    def test_it_finds_the_guard_from_a_subdirectory(self):
        out = self.decision(run_launcher(RISKY, os.path.join(ROOT, "docs", "decisions")))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_it_stays_quiet_on_a_harmless_command_from_a_subdirectory(self):
        self.assertIsNone(self.decision(run_launcher(HARMLESS, os.path.join(ROOT, "docs"))))

    def test_a_project_dir_pointing_elsewhere_does_not_switch_it_off(self):
        """The audit's case: CLAUDE_PROJECT_DIR set to another directory used
        to find nothing and exit silently. The working directory is searched
        too."""
        elsewhere = tempfile.mkdtemp()
        try:
            out = self.decision(run_launcher(RISKY, ROOT, project_dir=elsewhere))
        finally:
            shutil.rmtree(elsewhere, ignore_errors=True)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_where_no_guard_exists_it_fails_open_and_says_so(self):
        """Failing open is the design; failing open silently made a disabled
        guard look like one with nothing to say."""
        nowhere = tempfile.mkdtemp()
        try:
            out = self.decision(run_launcher(RISKY, nowhere))
        finally:
            shutil.rmtree(nowhere, ignore_errors=True)
        self.assertNotIn("hookSpecificOutput", out)
        self.assertIn("not checked", out["systemMessage"])

    def test_a_payload_that_is_not_an_object_never_blocks(self):
        for payload in ("[1, 2]", "not json at all"):
            with self.subTest(payload=payload):
                self.assertIsNone(self.decision(run_launcher(payload, ROOT)))


if __name__ == "__main__":
    unittest.main()
