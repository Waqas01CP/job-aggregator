"""Fitness functions: ADR-0049.

Each one guards an architectural rule that code can break silently. Its
docstring opens with the record and clause it guards and names the mutation
that proves it can fail, and the meta-test at the bottom holds every such
docstring to a record that exists and a mutation that is on file. They run in
the ordinary suite and are never skipped or marked slow.

Where a property can be checked over data, it is checked over all the data
the suite has: every posting in the saved responses in `tests/cassettes/`,
and the stored filtered layer when this machine holds one. The saved
responses are always there, so nothing here is ever skipped.
"""

import ast
import glob
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import storage
from src.adapters import greenhouse, himalayas, lever
from src.airtable import PIPELINE_FIELDS
from src.airtable_sweep import CLASSIFICATION_TABLES, COPY_FIELDS, JOBS, WRITES
from src.config import Board
from src.filters import TitleMatcher
from src.normalise import Row, normalise
from tests.test_adapters import cassette
from tests.test_normalise import NOW as NORMALISE_NOW
from tests.test_normalise import SPEECHIFY

MATCHER = TitleMatcher()
SCHEMA = os.path.join(ROOT, "docs", "reference", "airtable-schema.md")
FITNESS = re.compile(r"^Fitness function for (ADR-(\d{4})), ")
MUTATION = re.compile(r'Mutation: "([^"]+)"')


def cassette_rows():
    """Every posting in the saved responses, normalised through the real
    normaliser with each board's own configuration."""
    boards = [
        (greenhouse, "greenhouse-speechify-titles.json", SPEECHIFY),
        (greenhouse, "greenhouse-careem.json", Board(platform="greenhouse", slug="careem")),
        (lever, "lever-smart-working-solutions.json",
         Board(platform="lever", slug="smart-working-solutions", employer_alias="Smart Working")),
        (himalayas, "himalayas-browse.json", Board(platform="himalayas", slug="browse")),
    ]
    rows = []
    for adapter, name, board in boards:
        rows.extend(normalise(adapter.parse(cassette(name), board).postings, board,
                              NORMALISE_NOW))
    return rows


def stored_rows():
    """The stored filtered layers this machine holds, if any."""
    rows = []
    for mode in (False, True):
        paths = storage.layout(mode)
        for key in ("filtered", "local_filtered"):
            path = os.path.join(ROOT, paths[key])
            if os.path.exists(path):
                rows.extend(Row(**r) for r in storage.read_records(path))
    return rows


def verdict(title):
    term = MATCHER.match(title)
    return term, term is not None and MATCHER.excluded_word(title) is None, MATCHER.family_of(term)


def owners(heading, columns):
    """{field: owner} from the table under `heading` in the schema reference,
    whose header row is `columns`."""
    with open(SCHEMA, encoding="utf-8") as f:
        text = f.read()
    start = text.index(heading)
    lines = text[start:].splitlines()
    header = "| " + " | ".join(columns) + " |"
    begin = lines.index(header) + 2
    out = {}
    for line in lines[begin:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        out[cells[0]] = cells[columns.index("Owner")]
    return out


class TestFitnessFunctions(unittest.TestCase):
    def test_raw_and_normalised_titles_admit_alike(self):
        """Fitness function for ADR-0027, "The key itself is unchanged": the
        title normalisation a board is configured with may strip a location
        suffix and nothing a rule reads. For every posting in the saved
        responses, and every stored row this machine holds, matching the raw
        title and matching the normalised title give the same term, the same
        verdict and the same family. Measured true over 345 stored rows by the
        architecture chat, 2026-09-25. Mutation: "a per-source normalisation
        strips a word a pool term needs"."""
        rows = cassette_rows() + stored_rows()
        changed = [r for r in rows if r.title != r.title_normalised]
        self.assertGreater(len(changed), 1000, "the Speechify case is missing")
        disagree = [(r.title, r.title_normalised) for r in rows
                    if verdict(r.title) != verdict(r.title_normalised)]
        self.assertEqual(disagree, [])

    def test_no_module_hard_codes_a_preference(self):
        """Fitness function for ADR-0031, "no module hard-codes any of them":
        the title pool, the seniority list, the role families, the annotation
        vendors and the employers live in configuration, never in a shipped
        module's code. Runs `tools/preference_audit.py` over the tree.
        Mutation: "a shipped module hard-codes a pool term"."""
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import preference_audit
        violations, _, _ = preference_audit.scan()
        self.assertEqual(violations, [])

    def test_every_writer_sends_only_what_the_pipeline_owns(self):
        """Fitness function for ADR-0035, "fields the operator owns are never
        written by the pipeline": stated as a property over the schema, not a
        list. Every field in the base has an owner in the schema reference;
        the fields any pipeline writer sends to a table are exactly the ones
        owned by the pipeline there, whatever the base gains later. Mutation:
        "the sweep may write Status"."""
        jobs = owners("## `Jobs` and `Jobs test`", ("Field", "Type", "Owner", "Holds"))
        self.assertTrue(set(jobs.values()) <= {"pipeline", "operator", "Airtable"}, jobs)
        written = set(PIPELINE_FIELDS) | set(WRITES[JOBS])
        self.assertEqual(written, {f for f, o in jobs.items() if o == "pipeline"})
        self.assertIn("Status", jobs)
        self.assertEqual(jobs["Status"], "operator")

        copies = owners("## The three classification tables", ("Field", "Owner", "Holds"))
        self.assertTrue(set(copies.values()) <= {"pipeline", "operator", "Airtable"}, copies)
        for table in CLASSIFICATION_TABLES:
            self.assertEqual(set(WRITES[table]), {f for f, o in copies.items()
                                                  if o == "pipeline"}, table)
        self.assertEqual(set(COPY_FIELDS), {f for f, o in copies.items() if o == "pipeline"})


class TestTheFitnessFunctionsThemselves(unittest.TestCase):
    """ADR-0049's Confirmation: each fitness function names a record that
    exists and a mutation that is on file, or it is guarding nothing."""

    def fitness_functions(self):
        found = []
        for path in glob.glob(os.path.join(ROOT, "tests", "test_*.py")):
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node) or ""
                    if FITNESS.match(doc):
                        found.append((os.path.basename(path), node.name, doc))
        return found

    def test_the_first_three_are_present(self):
        records = {FITNESS.match(doc).group(1) for _, _, doc in self.fitness_functions()}
        self.assertTrue({"ADR-0027", "ADR-0031", "ADR-0035"} <= records, records)

    def test_each_names_a_record_that_exists_and_a_mutation_on_file(self):
        labels = set()
        for path in glob.glob(os.path.join(ROOT, "tools", "mutations", "*.json")):
            with open(path, encoding="utf-8") as f:
                labels |= {m["label"] for m in json.load(f)}
        for filename, name, doc in self.fitness_functions():
            with self.subTest(test=name):
                number = FITNESS.match(doc).group(2)
                self.assertTrue(glob.glob(os.path.join(ROOT, "docs", "decisions",
                                                       "%s-*.md" % number)),
                                "%s in %s names ADR-%s, which does not exist"
                                % (name, filename, number))
                mutation = MUTATION.search(" ".join(doc.split()))
                self.assertIsNotNone(mutation, "%s names no mutation" % name)
                self.assertIn(mutation.group(1), labels,
                              "%s names a mutation not on file" % name)

    def test_the_meta_test_can_fail(self):
        """The case built to defeat it: a docstring naming a record that
        does not exist is caught by the same pattern."""
        doc = 'Fitness function for ADR-0999, "x". Mutation: "nothing".'
        self.assertEqual(FITNESS.match(doc).group(2), "0999")
        self.assertFalse(glob.glob(os.path.join(ROOT, "docs", "decisions", "0999-*.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
