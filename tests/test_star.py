"""The priority star, and the line ADR-0010 draws around it.

Half of these tests exist to prove the star is not a similarity model: a
posting that obviously resembles an accepted role, and shares none of the
three named attributes, must not be starred.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.filters import TitleMatcher
from src.normalise import Row
from src.star import ATTRIBUTES, attributes_of, explain, is_starred, star_reasons

MATCHER = TitleMatcher()


def row(identity, title="AI Engineer", employer="Careem"):
    return Row(identity=identity, source="greenhouse", board_id="greenhouse:b",
               external_id=identity, title=title, title_normalised=title,
               url="https://x.test/%s" % identity, url_provenance="given",
               first_seen="2026-09-01T00:00:00.000000Z",
               ordering_date="2026-09-01T00:00:00.000000Z",
               ordering_date_source="publication", employer=employer,
               employer_provenance="payload", location="Karachi",
               published_at="2026-09-01T00:00:00.000000Z",
               published_field="first_published")


class TestTheThreeAttributes(unittest.TestCase):
    def test_same_employer_stars(self):
        """Titles from different families, so employer is the only match and
        the reason list cannot be padded by an accidental second hit."""
        accepted = [row("a1", title="Data Engineer", employer="Careem")]
        reasons = star_reasons(row("n1", title="AI Engineer"), accepted, MATCHER)
        self.assertEqual([r["attribute"] for r in reasons], ["employer"])
        self.assertEqual(reasons[0]["accepted_identity"], "a1")

    def test_same_matched_term_stars_across_employers(self):
        accepted = [row("a1", title="AI Engineer", employer="Motive")]
        reasons = star_reasons(row("n1", title="AI Engineer", employer="Veeam"),
                               accepted, MATCHER)
        self.assertEqual([r["attribute"] for r in reasons],
                         ["matched term", "role family"])

    def test_same_family_stars_on_different_terms(self):
        """`agentic` and `multi agent` are different terms under one heading."""
        accepted = [row("a1", title="Agentic Systems Engineer", employer="Motive")]
        reasons = star_reasons(row("n1", title="Multi Agent Developer",
                                   employer="Veeam"), accepted, MATCHER)
        self.assertEqual([r["attribute"] for r in reasons], ["role family"])
        self.assertEqual(reasons[0]["value"], "Agentic AI")

    def test_employer_comparison_is_folded(self):
        accepted = [row("a1", employer="CAREEM")]
        self.assertTrue(is_starred(row("n1", employer="careem"), accepted, MATCHER))

    def test_the_attribute_list_is_the_whole_surface(self):
        """If this grows, something widened what 'resembles' means, which is a
        decision and not a refactor."""
        self.assertEqual(ATTRIBUTES, ("employer", "matched term", "role family"))


class TestItIsNotASimilarityModel(unittest.TestCase):
    def test_an_obviously_similar_role_sharing_no_named_attribute_is_not_starred(self):
        """A model would star this: different employer, different family, and
        titles a human reads as adjacent. No named attribute matches, so no
        star. This is the line, and this test is where it is enforced."""
        accepted = [row("a1", title="Machine Learning Engineer", employer="Motive")]
        candidate = row("n1", title="Backend Engineer", employer="Veeam")
        self.assertEqual(star_reasons(candidate, accepted, MATCHER), [])

    def test_a_row_with_no_pool_term_is_never_starred_by_term_or_family(self):
        accepted = [row("a1", title="AI Engineer", employer="Motive")]
        candidate = row("n1", title="Accounts Officer", employer="Veeam")
        self.assertEqual(star_reasons(candidate, accepted, MATCHER), [])

    def test_no_star_is_ranked_above_another(self):
        """Reasons are ordered by attribute and identity, which is stable and
        carries no weight. Nothing here returns a number."""
        accepted = [row("a2", title="AI Engineer"), row("a1", title="AI Engineer")]
        reasons = star_reasons(row("n1", title="AI Engineer"), accepted, MATCHER)
        for r in reasons:
            self.assertEqual(set(r), {"attribute", "value", "accepted_identity"})
            for value in r.values():
                self.assertNotIsInstance(value, (int, float))

    def test_the_order_is_deterministic(self):
        accepted = [row("a3"), row("a1"), row("a2")]
        candidate = row("n1")
        first = star_reasons(candidate, accepted, MATCHER)
        second = star_reasons(candidate, list(reversed(accepted)), MATCHER)
        self.assertEqual(first, second)

    def test_every_star_can_be_read_aloud(self):
        """ADR-0010's own test. A star that cannot be explained by naming the
        attribute is a model."""
        accepted = [row("a1", title="AI Engineer", employer="Careem")]
        reasons = star_reasons(row("n1", title="AI Developer"), accepted, MATCHER)
        self.assertTrue(reasons)
        for line in explain(reasons):
            self.assertTrue(line.startswith("starred because "))
            self.assertIn("accepted row a1", line)


class TestEdges(unittest.TestCase):
    def test_a_row_does_not_star_itself(self):
        """Re-projecting the accepted store would otherwise star every row in
        it for resembling itself."""
        r = row("a1")
        self.assertEqual(star_reasons(r, [r], MATCHER), [])

    def test_an_empty_accepted_store_stars_nothing(self):
        self.assertFalse(is_starred(row("n1"), [], MATCHER))

    def test_a_missing_employer_never_matches_another_missing_employer(self):
        """Two rows with no employer are not the same employer. A None that
        compares equal would star every Lever row against every other before
        ADR-0026's derivation runs."""
        accepted = [row("a1", employer=None)]
        reasons = star_reasons(row("n1", title="Accounts Officer", employer=None),
                               accepted, MATCHER)
        self.assertEqual(reasons, [])

    def test_attributes_of_reports_all_three(self):
        attrs = attributes_of(row("n1", title="AI Engineer", employer="Careem"), MATCHER)
        self.assertEqual(attrs["employer"], "careem")
        self.assertEqual(attrs["matched term"], "ai engineer")
        self.assertEqual(attrs["role family"], "LLM and applied AI")


if __name__ == "__main__":
    unittest.main()
