"""The map generator's status gate.

The corpus audit of 2026-09-23 gave a record `status: acepted`, regenerated
the map, and watched `--check` exit 0: the gate tested only that a status was
present. These are the cases built to defeat the new one.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import generate_map
from tools.generate_map import MapError, check_status, record_numbers


class TestStatusGate(unittest.TestCase):
    NUMBERS = {"0014", "0045", "0046"}

    def test_every_madr_status_passes(self):
        for status in ("proposed", "rejected", "accepted", "deprecated",
                       "superseded by ADR-0046"):
            with self.subTest(status=status):
                check_status("x.md", status, self.NUMBERS)

    def test_a_misspelt_status_is_refused(self):
        """The audit's case."""
        with self.assertRaises(MapError):
            check_status("x.md", "acepted", self.NUMBERS)

    def test_a_supersession_naming_a_missing_record_is_refused(self):
        with self.assertRaises(MapError) as caught:
            check_status("x.md", "superseded by ADR-0999", self.NUMBERS)
        self.assertIn("does not exist", str(caught.exception))

    def test_a_malformed_supersession_is_refused(self):
        for status in ("superseded by 0046", "Superseded by ADR-0046",
                       "superseded by ADR-46", "accepted, extended by 0040"):
            with self.subTest(status=status), self.assertRaises(MapError):
                check_status("x.md", status, self.NUMBERS)

    def test_the_real_corpus_passes_and_knows_its_records(self):
        numbers = record_numbers()
        self.assertIn("0046", numbers)
        self.assertNotIn("ADR-", "".join(numbers))


class TestWhatIsMapped(unittest.TestCase):
    def test_gitignored_working_directories_are_never_mapped(self):
        """A file only this machine has would put a line in MAP.md that no
        clean clone reproduces, and the committed map would be stale there.
        data/ halted the hook on 2026-09-17; briefs/ was added 2026-09-24."""
        root = Path(tempfile.mkdtemp())
        real = generate_map.REPO_ROOT
        try:
            for rel in ("docs/kept.md", "data/report.md", "raw_responses/x.md",
                        "briefs/audit.md", "briefs/architecture.md"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("# x" + chr(10), encoding="utf-8")
            generate_map.REPO_ROOT = root
            mapped = [p.relative_to(root).as_posix() for p in generate_map.markdown_files()]
        finally:
            generate_map.REPO_ROOT = real
            shutil.rmtree(root, ignore_errors=True)
        self.assertEqual(mapped, ["docs/kept.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
