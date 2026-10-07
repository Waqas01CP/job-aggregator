"""What a description is read for: the years asked, a place a requirement
names, and on-site work. Each guard is tested on a sentence shaped like the
one, among the 1,708 descriptions saved by 2026-10-02, that made it
necessary, and each pattern on the kind of sentence it must not read.

**Every sentence here is written for the test, never copied.** ADR-0011
keeps description text, snippets included, out of this public repository;
the measured sentences stay on the private full branch, and only their shape
is reproduced."""

import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import description
from src.adapters import greenhouse, himalayas, lever
from src.config import Board
from src.normalise import FIELDS, normalise

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def years(*parts):
    return description.years_asked(description.lines_of(*parts))


def required(*parts):
    return description.requirements_named(description.lines_of(*parts))


def on_site(*parts):
    return description.says_on_site(description.lines_of(*parts))


class TestLines(unittest.TestCase):
    def test_greenhouse_html_escaped_twice_is_read(self):
        lines = description.lines_of("&lt;p&gt;5+ years of experience&lt;/p&gt;&lt;ul&gt;"
                                     "&lt;li&gt;Python&amp;nbsp;and Go&lt;/li&gt;&lt;/ul&gt;")
        self.assertEqual(lines, ("5+ years of experience", "Python and Go"))

    def test_block_tags_end_a_line(self):
        """Two bullets never read as one sentence: merged, a company's "12
        years" would sit beside the next bullet's "experience". Mutation:
        "block tags do not end a line"."""
        parts = ("<ul><li>Our story: we have grown for 12 years</li>"
                 "<li>Experience with Go is a plus</li></ul>",)
        self.assertEqual(years(*parts), ())

    def test_nothing_to_read(self):
        self.assertIsNone(description.read(None))
        self.assertIsNone(description.read((None, "", "  ")))


class TestYears(unittest.TestCase):
    def test_a_line_that_opens_with_its_figure(self):
        """30 of 30 sampled from 89 such lines were requirements."""
        self.assertEqual(years("<li>6+ years in fintech platforms</li>"), (6,))
        self.assertEqual(years("Minimum of 7 years leading data teams"), (7,))
        self.assertEqual(years("• 3+ years operating Kubernetes clusters"), (3,))
        self.assertEqual(years("Qualifications: 4+ years building APIs"), (4,))
        self.assertEqual(years("Experience: ﻿5+ years"), (5,))

    def test_experience_beside_a_figure_mid_sentence(self):
        self.assertEqual(years("We are looking for a developer with 5+ years of experience."), (5,))
        self.assertEqual(years("The right person brings at least five (5) years of experience "
                               "with Rust."), (5,))

    def test_a_range_counts_by_its_low_end(self):
        """"3 to 5 years" asks at least 3, which he takes."""
        self.assertEqual(years("3 to 5 years of experience in backend development"), (3,))
        self.assertEqual(years("2–4 years of experience shipping mobile apps"), (2,))
        self.assertEqual(years("6 months to 1 year of experience in analytics"), (1,))
        self.assertEqual(years("You are a recent hire or have 0-2 years of professional "
                               "experience."), (0,))

    def test_every_figure_is_kept(self):
        self.assertEqual(years("Experience: 3 years in ops, including 2+ years in Python."),
                         (3, 2))

    def test_a_figure_glued_to_a_word_is_read(self):
        """One board's markup leaves a digit glued to the word before it
        once its tags are gone. Mutation: "a figure after a letter is
        missed"."""
        self.assertEqual(years("Experience5 – 7 years preferred"), (5,))

    def test_a_line_opened_to_fresh_graduates_is_not_a_minimum(self):
        """Shaped like a measured remote role in Pakistan. Mutation: "a line
        opened to fresh graduates is read as a minimum"."""
        self.assertEqual(years("Experience5 – 7 years preferred; strong new graduates "
                               "considered"), ())

    def test_a_figure_that_is_not_experience_is_not_read(self):
        for text in ("Help us triple our revenue over the next 5 years.",
                     "Our studio has been profitable for over 10 years and keeps growing.",
                     "Systems built at scale; most of the team has 7+ years.",
                     "List two similar products launched in the past five years.",
                     "Optional relocation support within 2+ years.",
                     "The market has had no new competitor in more than 30 years."):
            with self.subTest(text=text):
                self.assertEqual(years(text), ())

    def test_a_figure_that_is_not_a_minimum_is_not_read(self):
        """Experience stands beside each, so only the word before the figure
        says it is no minimum. Mutation: "a figure that is not a minimum is
        read"."""
        for text in ("Up to 5 years of experience in a similar role is welcome.",
                     "We value what you learned over the past 6 years of experience."):
            with self.subTest(text=text):
                self.assertEqual(years(text), ())

    def test_a_sentence_about_the_company_is_not_a_requirement(self):
        """Five of 50 mid-sentence figures measured were a company's own
        boast. Mutation: "a sentence about the company is read as a
        requirement"."""
        for text in ("As a family-owned company with over 18 years of experience in retail, "
                     "our team is proud.",
                     "At Northwind, we build logistics software, bringing nearly 30 years of "
                     "experience to our clients.",
                     "Contoso is using its global reach and 40+ years of experience to help."):
            with self.subTest(text=text):
                self.assertEqual(years(text), ())

    def test_a_sentence_that_also_addresses_the_candidate_is_one(self):
        self.assertEqual(years("Join our company if you have 5+ years of experience."), (5,))


class TestRequirements(unittest.TestCase):
    def test_a_requirement_names_its_place(self):
        cases = (("Applicants must be authorized to work in the United States (no sponsorship "
                  "offered)", ("the United States",)),
                 ("EU citizens only, please.", ("EU",)),
                 ("This team can hire US citizens only.", ("US",)),
                 ("You need the right to work in Portugal.", ("Portugal",)),
                 ("Remote, and open to candidates in East Africa.", ("East Africa",)),
                 ("The hire must be based in Africa.", ("Africa",)),
                 ("Canada-based candidates only", ("Canada",)))
        for text, place in cases:
            with self.subTest(text=text):
                self.assertEqual(required(text), place)

    def test_us_with_dots_is_one_place(self):
        """Measured: with its dots, the place ended at "the U". The phrase
        runs on to the next stop, and the row keeps only the place names in
        it. Mutation: "U.S. keeps its dots"."""
        self.assertEqual(required("You must be authorized to work in the U.S. without "
                                  "sponsorship."), ("the US without sponsorship",))

    def test_a_requirement_said_not_to_apply_names_nothing(self):
        """Shaped like a measured remote role saying the candidate need not
        be in the US. Mutation: "a negated requirement is read"."""
        self.assertEqual(required("You do not need to be located in the U.S. to join us."), ())
        self.assertEqual(required("US citizenship is not required."), ())

    def test_citizens_of_anywhere_but_a_place_are_no_requirement(self):
        """Found on 2026-10-03 while taking the countries out of the citizen
        pattern: "non-US citizens" read as a US requirement, which drops a
        job open to him. In no saved description that day. Mutation: "a
        non- prefix is read as the place"."""
        for text in ("Non-US citizens are welcome to apply.", "We hire non US nationals too."):
            with self.subTest(text=text):
                self.assertEqual(required(text), ())
        self.assertEqual(required("US citizens only."), ("US",))

    def test_a_negation_elsewhere_in_the_sentence_cancels_nothing(self):
        """Mutation: "a negation anywhere before cancels"."""
        self.assertEqual(required("We don't sponsor visas, so you must be authorized to work "
                                  "in the U.S."), ("the US",))

    def test_no_visa_sponsorship_is_never_a_requirement(self):
        """The operator: on a role open worldwide it says only that no one
        will be moved, and he wants those roles in his table."""
        for text in ("We cannot sponsor a visa for this position.",
                     "We are unable to offer visa sponsorship.", "No visa sponsorship."):
            with self.subTest(text=text):
                self.assertEqual(required(text), ())


class TestOnSite(unittest.TestCase):
    def test_on_site_statements(self):
        for text in ("Location: Onsite, at our Gulshan office",
                     "This is an in-office role, four days a week.",
                     "In this hybrid role you will own the data platform.",
                     "Work mode: Onsite | Permanent",
                     "The job needs full-time onsite work on the night shift. This post does not "
                     "offer any remote or hybrid work."):
            with self.subTest(text=text):
                self.assertTrue(on_site(text))

    def test_the_place_then_the_mode_as_pakistani_postings_write_it(self):
        """Shaped like the lines Manatal's postings use, measured 2026-10-07
        over 640 of them: the patterns above read 8 and these shapes another
        31, with nothing newly read that does not say how the role is
        worked. Mutation: "a location line's mode after the place is not
        read"."""
        for text in ("Location: Lahore (Onsite)",
                     "Location: Karachi, Lahore, Islamabad (On-site)",
                     "Location: Lahore - OnSite",
                     "Location: Lahore / Onsite",
                     "Location: Gulberg, Lahore, Pakistan (Onsite)",
                     "Join the team in Karachi (onsite) as its first analyst.",
                     "Riyadh (Onsite)"):
            with self.subTest(text=text):
                self.assertTrue(on_site(text))

    def test_labels_and_a_comma_the_first_patterns_missed(self):
        """Mutation: "a label it does not know hides the mode"."""
        for text in ("Work Module: Onsite",
                     "Job Conditions: Onsite, full time, evening shift",
                     "Employment Type: Full-time,Onsite (10AM - 7PM)",
                     "The role is based in the city and requires full-time, on-site presence."):
            with self.subTest(text=text):
                self.assertTrue(on_site(text))

    def test_a_named_product_or_a_cloud_in_brackets_is_not_a_place(self):
        """Hybrid in brackets after a product is no workplace; only on-site in
        brackets after a named place is read."""
        for text in ("Experience with the Platform (Hybrid) edition",
                     "Hands-on with Cloud Run, Cloud Build (hybrid)",
                     "Willingness to travel for on-site training engagements."):
            with self.subTest(text=text):
                self.assertFalse(on_site(text))

    def test_a_remote_option_anywhere_outweighs_it(self):
        """Shaped like a measured fully remote role with an office for those
        who want one. Mutation: "a remote option is ignored"."""
        self.assertFalse(on_site("This is a hybrid role.",
                                 "Work fully remote, or from our office if you prefer."))

    def test_remote_said_not_to_be_offered_is_no_option(self):
        """Mutation: "remote said not to be offered is an option"."""
        self.assertTrue(on_site("This is an on-site role.", "This is not a remote role."))

    def test_other_senses_of_the_words_are_not_read(self):
        for text in ("Familiar with hybrid search over embeddings",
                     "Comfortable with hybrid cloud setups",
                     "keeping in touch with the onsite team",
                     "Shortlisted people join an on-site round at the end."):
            with self.subTest(text=text):
                self.assertFalse(on_site(text))


class TestTheRowKeepsNoWords(unittest.TestCase):
    """Only derived values reach a row, and Greenhouse and Lever rows are on
    the public branch (ADR-0011)."""

    BOARDS = {"greenhouse": Board(platform="greenhouse", slug="careem"),
              "lever": Board(platform="lever", slug="smart-working-solutions"),
              "himalayas": Board(platform="himalayas", slug="pakistan")}

    def row_from(self, source, entry):
        adapter = {"greenhouse": greenhouse, "lever": lever, "himalayas": himalayas}[source]
        payload = [entry] if source == "lever" else {"jobs": [entry]}
        [posting] = adapter.parse(payload, self.BOARDS[source]).postings
        [row] = normalise([posting], self.BOARDS[source], NOW)
        return row

    TEXT = ("<p>Must be legally authorized to work in the United States or Canada.</p>"
            "<ul><li>5+ years of Thokar experience</li></ul>"
            "<p>Location: Onsite at the Thokar campus</p>")

    def assert_derived_only(self, row):
        self.assertEqual(row.stated_experience, [5])
        self.assertEqual(row.required_places, ["united states, canada"])
        self.assertEqual(row.described_workplace, "on site")
        record = str(row.as_record())
        for word in ("Thokar", "authorized", "legally"):
            self.assertNotIn(word, record)

    def test_greenhouse_reads_its_content(self):
        """Mutation: "Greenhouse hands over no description"."""
        entry = {"id": 1, "title": "AI Engineer", "absolute_url": "https://x.test/1",
                 "first_published": "2026-09-10T00:00:00-04:00", "location": {"name": "Lahore"},
                 "content": self.TEXT.replace("<", "&lt;").replace(">", "&gt;")}
        self.assert_derived_only(self.row_from("greenhouse", entry))

    def test_lever_reads_its_sections(self):
        """Lever puts the requirements in `lists`. Mutation: "Lever's
        sections are not read"."""
        entry = {"id": "a", "text": "AI Engineer", "hostedUrl": "https://x.test/a",
                 "createdAt": 1789141813000, "categories": {"location": "Lahore"},
                 "description": "<p>Must be legally authorized to work in the United States or "
                                "Canada.</p>",
                 "lists": [{"text": "Requirements",
                            "content": "<li>5+ years of Thokar experience</li>"}],
                 "additional": "<p>Location: Onsite at the Thokar campus</p>"}
        self.assert_derived_only(self.row_from("lever", entry))

    def test_himalayas_reads_its_description(self):
        entry = {"guid": "https://x.test/h", "title": "AI Engineer",
                 "applicationLink": "https://x.test/h", "pubDate": 1789141813,
                 "description": self.TEXT}
        self.assert_derived_only(self.row_from("himalayas", entry))

    def test_a_requirement_naming_no_known_place_is_left_out(self):
        """A US state, a time zone, "except": none can close a posting, and
        "anywhere except the US" must never be kept as the US."""
        entry = {"guid": "https://x.test/h", "title": "AI Engineer",
                 "applicationLink": "https://x.test/h", "pubDate": 1789141813,
                 "description": "<p>Must be located in a US time zone.</p>"
                                "<p>Must reside in one of the following states.</p>"
                                "<p>Must be eligible to work in any country except the US.</p>"}
        row = self.row_from("himalayas", entry)
        self.assertIsNone(row.required_places)

    def test_the_fields_are_part_of_the_canonical_record(self):
        for name in ("stated_experience", "required_places", "described_workplace"):
            self.assertIn(name, FIELDS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
