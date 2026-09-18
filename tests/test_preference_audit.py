"""ADR-0031's Confirmation, made runnable and proved able to fail.

A gate nobody has seen fire is indistinguishable from an absent one. The
audit reports the shipped tree clean, so every test here that matters plants
a violation first and checks the audit finds it.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.preference_audit import (AuditError, exempt_lines, load_employers,
                                    load_families, main, needles, scan)


def write(text):
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


class TestWhatIsAudited(unittest.TestCase):
    def test_the_four_preference_kinds_and_employers_are_all_loaded(self):
        found = needles()
        kinds = set(found.values())
        self.assertEqual(kinds, {"pool term", "seniority word", "annotation vendor",
                                 "role family", "employer"})

    def test_families_come_from_the_pool_headings(self):
        fams = load_families()
        self.assertEqual(fams, ["agentic ai", "llm and applied ai",
                                "traditional ai and ml", "software engineering"])

    def test_employers_come_from_the_board_config_and_exclude_the_endpoint_name(self):
        """Himalayas' slug is "browse", which is an ordinary English word. Auditing
        it would flag every module that mentions browsing."""
        employers = load_employers()
        self.assertIn("speechify", employers)
        self.assertIn("careem", employers)
        self.assertNotIn("browse", employers)

    def test_a_pool_file_that_will_not_load_stops_the_audit(self):
        with self.assertRaises(AuditError):
            load_families(os.path.join(tempfile.gettempdir(), "no-such-pool.md"))


class TestTheAuditCanFail(unittest.TestCase):
    """Each case plants exactly one violation the shipped tree does not have."""

    def _scan(self, text):
        path = write(text)
        try:
            return scan(files=[path])
        finally:
            os.unlink(path)

    def test_a_pool_term_in_a_list_literal_is_a_violation(self):
        violations, _, _ = self._scan('TERMS = ["agentic", "llm"]\n')
        self.assertTrue(violations)
        self.assertEqual(violations[0]["kind"], "pool term")
        self.assertEqual(violations[0]["value"], "agentic")

    def test_an_employer_name_in_a_condition_is_a_violation(self):
        violations, _, _ = self._scan('def f(b):\n    return b == "speechify"\n')
        self.assertEqual([v["kind"] for v in violations], ["employer"])

    def test_a_seniority_word_in_code_is_a_violation(self):
        violations, _, _ = self._scan('WORDS = ("senior", "staff")\n')
        self.assertEqual({v["value"] for v in violations}, {"senior", "staff"})

    def test_the_same_term_in_a_docstring_is_allowed(self):
        """The distinction the whole audit rests on. Identical text, and only
        its position decides."""
        violations, allowed, _ = self._scan('"""Explains why `agentic` is exempt."""\n')
        self.assertEqual(violations, [])
        self.assertTrue(allowed)

    def test_the_same_term_in_a_comment_is_allowed(self):
        violations, allowed, _ = self._scan("x = 1  # agentic is an exempt token\n")
        self.assertEqual(violations, [])
        self.assertTrue(allowed)

    def test_a_multiline_data_string_is_not_mistaken_for_a_docstring(self):
        """Docstrings are found with ast, not by looking for triple quotes. A
        data string holding a term is a second copy of the pool, and gets no
        exemption for spanning lines."""
        text = 'X = """\nagentic\n"""\n'
        violations, _, _ = self._scan(text)
        self.assertTrue(violations, "a data string was treated as a docstring")

    def test_a_term_inside_a_longer_word_is_not_a_hit(self):
        """`llm` must not match "llmodule". The boundary rule is the same one
        ADR-0021 uses on titles."""
        violations, allowed, _ = self._scan("llmodule = 1\nsenioritis = 2\n")
        self.assertEqual(violations, [])
        self.assertEqual(allowed, [])


class TestTheShippedTree(unittest.TestCase):
    def test_no_module_hard_codes_a_preference(self):
        """ADR-0031's Confirmation itself. If this fails, read the names: a
        preference has hardened into code and the general-aggregator
        conversion just became a rewrite by that much."""
        violations, _, count = scan()
        self.assertEqual(violations, [], "ADR-0031 violated: %s"
                         % [(v["file"], v["line"], v["value"]) for v in violations])
        self.assertGreater(count, 90, "far fewer values than the pool holds")

    def test_the_exit_code_is_zero_when_clean(self):
        self.assertEqual(main([]), 0)


class TestExemptLines(unittest.TestCase):
    def test_module_class_and_function_docstrings_are_all_exempt(self):
        path = write('"""mod."""\n\n\nclass A:\n    """cls."""\n\n    def m(self):\n'
                     '        """fn."""\n        return 1  # trailing\n')
        try:
            lines = exempt_lines(path)
        finally:
            os.unlink(path)
        self.assertEqual(lines, {1, 5, 8, 9})


if __name__ == "__main__":
    unittest.main()
