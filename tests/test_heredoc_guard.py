"""The heredoc guard, and the line it draws.

Every command here is built with chr(92) rather than typed, because a test
file for this guard is the last place a stray backslash should be ambiguous.

The guard's whole value is that it stays quiet. Half these tests are cases it
must NOT fire on: if it starts asking about ordinary analysis commands, it
becomes something to click through, and a gate people click through is worse
than none.
"""

import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.heredoc_guard import heredoc_bodies, verdict

BS = chr(92)
NL = chr(10)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def heredoc(*body_lines):
    return "python - <<'PY'" + NL + NL.join(body_lines) + NL + "PY"


class TestItAsks(unittest.TestCase):
    def test_the_real_failure_that_broke_filters_twice(self):
        cmd = heredoc('s = s.replace("a", "' + BS + BS + 'n")',
                      'io.open("src/filters.py", "w").write(s)')
        asks, reason = verdict(cmd)
        self.assertTrue(asks)
        self.assertIn("five times", reason)
        self.assertIn("Write and Edit tools", reason)

    def test_a_shell_redirect_counts_as_a_write(self):
        cmd = "cat > out.py <<'EOF'" + NL + 'x = "' + BS + 'n"' + NL + "EOF"
        self.assertTrue(verdict(cmd)[0])

    def test_write_atomic_is_recognised(self):
        """The em-dash case: a backslash escape headed for prose on disk."""
        cmd = heredoc('write_atomic("f.md", "' + BS + 'u2014")')
        self.assertTrue(verdict(cmd)[0])

    def test_append_mode_counts(self):
        cmd = heredoc('open("log.txt", "a").write("' + BS + 'n")')
        self.assertTrue(verdict(cmd)[0])


class TestItStaysQuiet(unittest.TestCase):
    def test_analysis_with_regex_backslashes_is_allowed(self):
        """The common case by far, and the one that must never be blocked."""
        cmd = heredoc("import re",
                      'print(re.findall(r"' + BS + 'd{4}", "adr 0042"))')
        self.assertFalse(verdict(cmd)[0])

    def test_a_write_without_a_backslash_is_allowed(self):
        cmd = heredoc('open("notes.txt", "w").write("plain text")')
        self.assertFalse(verdict(cmd)[0])

    def test_a_command_with_no_heredoc_is_allowed(self):
        self.assertFalse(verdict('grep -rn "' + BS + 'd" src/')[0])

    def test_an_empty_command_is_allowed(self):
        self.assertFalse(verdict("")[0])

    def test_a_comparison_operator_is_not_read_as_a_redirect(self):
        """`if x > 3` inside an opener line must not look like `> file`."""
        cmd = "python - <<'PY'" + NL + 'print("' + BS + 'n")' + NL + "PY"
        self.assertFalse(verdict(cmd)[0])


class TestParsing(unittest.TestCase):
    def test_quoted_and_unquoted_delimiters_are_both_found(self):
        for opener in ("<<'PY'", '<<"PY"', "<<PY", "<<-PY"):
            cmd = "python - " + opener + NL + "body" + NL + "PY"
            self.assertEqual(len(heredoc_bodies(cmd)), 1, opener)

    def test_text_inside_a_body_is_not_read_as_another_opener(self):
        cmd = heredoc('print("use <<EOF in docs")')
        self.assertEqual(len(heredoc_bodies(cmd)), 1)

    def test_two_heredocs_are_both_seen(self):
        cmd = heredoc("one") + NL + heredoc("two")
        self.assertEqual(len(heredoc_bodies(cmd)), 2)


class TestTheHookContract(unittest.TestCase):
    """What Claude Code actually receives on stdin and reads from stdout."""

    def run_guard(self, payload):
        return subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "heredoc_guard.py")],
            input=json.dumps(payload), capture_output=True, text=True)

    def test_it_emits_an_ask_decision_not_a_deny(self):
        """Ask, never deny. A guard that refuses outright would be routed
        around within a session."""
        cmd = heredoc('open("x.py", "w").write("' + BS + 'n")')
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
        """A guard that fails closed on its own bug would stop work for a
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


if __name__ == "__main__":
    unittest.main()
