"""The filter chain, tested from the brief.

The brief's minimum case set is here in full: "Karachi, Sindh", "Karachi,
Punjab, Pakistan", a worldwide-remote posting, "Storage Engineer" which must
not match `rag`, and "Agentic Systems Engineer" which must match.
"""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters.base import Posting
from src.config import Board
from src.filters import (ANNOTATION_VENDORS, FilterError, TitleMatcher,
                         apply_chain, compile_terms, drop_counts,
                         load_title_pool, rule_annotation_vendor,
                         rule_experience, rule_expiry)
from src.normalise import normalise

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
NOW_ISO = "2026-09-16T12:00:00Z"
BOARD = Board(platform="greenhouse", slug="careem")
MATCHER = TitleMatcher()


def row(title="AI Engineer", employer="Careem", location="Karachi",
        expires_at=None, stated_experience=None):
    p = Posting(external_id="1", title=title, url="https://x.test/1",
                published_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
                published_field="first_published", published_raw="x",
                source="greenhouse", board_id="greenhouse:careem",
                employer=employer, employer_provenance="payload",
                location=location, expires_at=expires_at)
    r = normalise([p], BOARD, NOW)[0]
    r.stated_experience = stated_experience
    return r


def keep(**kw):
    kept, drops = apply_chain([row(**kw)], NOW_ISO, matcher=MATCHER)
    return bool(kept), (drops[0] if drops else None)


class TestTitlePool(unittest.TestCase):
    def test_pool_has_fifty_terms(self):
        terms, exempt = load_title_pool()
        self.assertEqual(len(terms), 50, "the pool file says 50 terms")

    def test_exempt_single_tokens_are_read_from_the_file(self):
        _, exempt = load_title_pool()
        self.assertIn("agentic", exempt)
        self.assertIn("llm", exempt)
        self.assertNotIn("ai", exempt, "ADR-0021: `ai` never stands alone")
        self.assertNotIn("rag", exempt, "ADR-0021: `rag` never stands alone")

    def test_a_bare_single_token_term_is_refused(self):
        """A pool edit adding a bare token would silently widen the filter."""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("## Terms\n\n`rag`\n\n## Known behaviour\n")
        try:
            with self.assertRaises(FilterError):
                load_title_pool(path)
        finally:
            os.unlink(path)


class TestTitleMatching(unittest.TestCase):
    def test_storage_engineer_does_not_match_rag(self):
        """The brief's case, and the reason ADR-0021 forbids raw substring
        matching: `rag` inside 'sto-rag-e'."""
        self.assertIsNone(MATCHER.match("Storage Engineer"))
        kept, drop = keep(title="Storage Engineer")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "title")

    def test_word_boundaries_are_what_stop_rag_matching_storage(self):
        """The pool has no bare `rag`, so the case above passes even under
        substring matching. This tests the mechanism the brief is protecting:
        compile the term `rag` as the pool would if anyone added it, and
        confirm the boundary is what refuses "Storage Engineer"."""
        [(term, pattern)] = compile_terms(["rag"])
        self.assertIsNone(pattern.search("storage engineer"),
                          "substring matching would turn a Storage Engineer "
                          "into a RAG role")
        self.assertIsNotNone(pattern.search("rag engineer"))
        self.assertIsNotNone(pattern.search("rags engineer"))

    def test_boundaries_hold_for_every_term_in_the_real_pool(self):
        """No term may match inside a longer word."""
        for term, pattern in TitleMatcher().patterns:
            self.assertIsNone(pattern.search("x%sx" % term.replace(" ", "x")),
                              "term %r matched inside a word" % term)

    def test_agentic_systems_engineer_matches(self):
        """The brief's case. `agentic` is an exempt single token."""
        self.assertEqual(MATCHER.match("Agentic Systems Engineer"), "agentic")
        self.assertTrue(keep(title="Agentic Systems Engineer")[0])

    def test_plural_suffix_reaches_the_final_word(self):
        self.assertIsNotNone(MATCHER.match("Multi Agents Engineer"))

    def test_hyphens_and_slashes_normalise_before_matching(self):
        self.assertIsNotNone(MATCHER.match("AI-Agent Developer"))
        self.assertIsNotNone(MATCHER.match("AI/ML Specialist"))

    def test_an_unmatched_title_is_dropped_with_its_title_recorded(self):
        """The drop log is the only feedback signal for a missing term, so the
        title has to be in it."""
        kept, drop = keep(title="Chief Happiness Officer")
        self.assertFalse(kept)
        self.assertIn("Chief Happiness Officer", drop["title"])

    def test_a_match_names_the_term_that_admitted_it(self):
        kept, _ = apply_chain([row(title="Machine Learning Engineer")],
                              NOW_ISO, matcher=MATCHER)
        self.assertIn("machine learning", kept[0][1])


class TestNoLocationFilter(unittest.TestCase):
    """The brief defers location to MVP 2. These are its named cases."""

    def test_karachi_sindh_is_not_dropped(self):
        self.assertTrue(keep(location="Karachi, Sindh")[0])

    def test_karachi_punjab_pakistan_is_not_dropped(self):
        """The geocoder's known bad spelling. Karachi is in Sindh, and a
        location filter would have dropped this row for being wrong."""
        self.assertTrue(keep(location="Karachi, Punjab, Pakistan")[0])

    def test_a_worldwide_remote_posting_is_not_dropped(self):
        self.assertTrue(keep(location="Worldwide")[0])
        self.assertTrue(keep(location="Remote")[0])

    def test_an_absent_location_is_not_dropped(self):
        self.assertTrue(keep(location=None)[0])

    def test_no_rule_in_the_chain_is_named_location(self):
        from src.filters import CHAIN
        self.assertNotIn("location", [name for name, _ in CHAIN])


class TestExpiry(unittest.TestCase):
    def test_a_past_expiry_drops(self):
        kept, drop = keep(expires_at="2026-09-01")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "expiry")

    def test_a_future_expiry_keeps(self):
        self.assertTrue(keep(expires_at="2027-01-01")[0])

    def test_no_expiry_keeps(self):
        """Every Greenhouse posting measured had application_deadline null.
        A rule that dropped on absence would empty the display."""
        self.assertTrue(keep(expires_at=None)[0])


class TestExperienceRuleIsDisabled(unittest.TestCase):
    def test_disabled_without_a_threshold(self):
        """No record names one, so the rule keeps everything."""
        r = row(stated_experience="12")
        self.assertTrue(rule_experience(r, max_years=None).keep)

    def test_the_chain_leaves_it_disabled_by_default(self):
        """Through apply_chain, not by calling the rule directly: it is the
        chain's default that decides whether an invented threshold is in
        force, and a row claiming twelve years must survive."""
        kept, drops = apply_chain([row(stated_experience="12")], NOW_ISO,
                                  matcher=MATCHER)
        self.assertEqual(len(kept), 1)
        self.assertEqual(drop_counts(drops)["experience"], 0)

    def test_it_works_once_a_threshold_is_supplied(self):
        """Implemented and tested so that supplying a threshold is a
        one-line change, not a rewrite."""
        r = row(stated_experience="12")
        verdict = rule_experience(r, max_years=5)
        self.assertFalse(verdict.keep)
        self.assertEqual(verdict.rule, "experience")

    def test_absent_experience_is_kept_even_with_a_threshold(self):
        """Neither slice platform returns the field. Dropping on absence
        would drop every row."""
        self.assertTrue(rule_experience(row(stated_experience=None), max_years=5).keep)


class TestAnnotationVendors(unittest.TestCase):
    def test_named_vendors_are_dropped(self):
        for vendor in ("Welo Data", "Welocalize", "Innodata"):
            kept, drop = keep(employer=vendor, title="AI Trainer")
            self.assertFalse(kept, vendor)
            self.assertEqual(drop["rule"], "annotation_vendor")

    def test_the_match_is_case_and_spacing_insensitive(self):
        self.assertFalse(rule_annotation_vendor(row(employer="WELO  DATA"), ANNOTATION_VENDORS).keep)

    def test_an_ordinary_employer_is_kept(self):
        self.assertTrue(rule_annotation_vendor(row(employer="Careem"), ANNOTATION_VENDORS).keep)

    def test_an_unresolved_employer_is_not_dropped(self):
        """A Lever board with no alias has no employer. Dropping those would
        remove a whole board on a rule about three vendors."""
        self.assertTrue(rule_annotation_vendor(row(employer=None), ANNOTATION_VENDORS).keep)


class TestChainOrder(unittest.TestCase):
    def test_the_cheapest_disqualifier_runs_first(self):
        """An expired annotation-vendor posting is dropped by expiry, not by
        the later rule, so the drop log attributes it correctly."""
        kept, drop = keep(employer="Welo Data", expires_at="2026-01-01",
                          title="Chief Happiness Officer")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "expiry")

    def test_each_drop_names_exactly_one_rule(self):
        rows = [row(title="Storage Engineer"), row(employer="Innodata"),
                row(expires_at="2020-01-01"), row(title="AI Engineer")]
        kept, drops = apply_chain(rows, NOW_ISO, matcher=MATCHER)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(drops), 3)
        self.assertEqual({d["rule"] for d in drops},
                         {"title", "annotation_vendor", "expiry"})

    def test_drop_counts_cover_every_rule_including_zeros(self):
        """ADR-0005. A rule reporting nothing must be visibly zero, not
        missing, or a rule that stopped firing looks the same as one that
        never fires."""
        _, drops = apply_chain([row(title="Storage Engineer")], NOW_ISO, matcher=MATCHER)
        counts = drop_counts(drops)
        self.assertEqual(counts["title"], 1)
        self.assertEqual(counts["expiry"], 0)
        self.assertEqual(counts["annotation_vendor"], 0)
        self.assertEqual(counts["experience"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
