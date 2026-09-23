"""The .env reader. Brief 6: standard library only, a no-op when the file is
absent, and what is already set in the environment wins."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import envfile


class TestEnvFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, ".env")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_a_missing_file_does_nothing(self):
        environ = {}
        self.assertEqual(envfile.load(self.path, environ), [])
        self.assertEqual(environ, {})

    def test_what_is_already_set_wins(self):
        """A runner sets every secret. A stray .env must not replace one."""
        self.write("AIRTABLE_TOKEN=from-file\nAIRTABLE_BASE_ID=appFROMFILE00001\n")
        environ = {"AIRTABLE_TOKEN": "from-runner"}
        loaded = envfile.load(self.path, environ)
        self.assertEqual(environ["AIRTABLE_TOKEN"], "from-runner")
        self.assertEqual(environ["AIRTABLE_BASE_ID"], "appFROMFILE00001")
        self.assertEqual(loaded, ["AIRTABLE_BASE_ID"])

    def test_an_empty_value_already_set_still_wins(self):
        """Present counts, not truthy: an empty secret on a runner is a fault
        to be reported by name, not quietly patched from a file."""
        self.write("AIRTABLE_TOKEN=from-file\n")
        environ = {"AIRTABLE_TOKEN": ""}
        envfile.load(self.path, environ)
        self.assertEqual(environ["AIRTABLE_TOKEN"], "")

    def test_comments_quotes_export_and_junk(self):
        text = "# a comment\n\nexport A=1\nB=\"two words\"\nC='3'\nnot a pair\n=orphan\nD=\n"
        self.assertEqual(envfile.parse(text),
                         {"A": "1", "B": "two words", "C": "3", "D": ""})

    def test_the_example_file_names_every_secret_the_run_reads(self):
        """.env.example is the list a new machine copies. It must hold every
        secret the run reads and no values."""
        from src import run as run_module
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, ".env.example"), encoding="utf-8") as f:
            example = envfile.parse(f.read())
        self.assertEqual(sorted(example), sorted(run_module.SECRET_ENVS))
        self.assertEqual(set(example.values()), {""})


if __name__ == "__main__":
    unittest.main(verbosity=2)
