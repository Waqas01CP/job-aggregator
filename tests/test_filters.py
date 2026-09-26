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
                         load_annotation_vendors, load_seniority_words,
                         load_title_pool, rule_annotation_vendor,
                         rule_experience, rule_expiry, rule_seniority)
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
    def test_pool_has_seventy_nine_terms(self):
        """Version 4, 2026-09-18: the 61 of version 3 plus eighteen AI terms.
        The measurement section after Known behaviour quotes 39 terms in
        backticks, and none may be read as pool terms."""
        terms, exempt = load_title_pool()
        self.assertEqual(len(terms), 79, "the pool file says 79 terms")
        self.assertEqual(len(set(terms)), 79, "a term is listed twice")

    def test_forward_deployment_closes_the_gap_the_plural_rule_leaves(self):
        """On 2026-09-16 "Forward Deployment Engineer" was dropped while
        "Senior Forward Deployed Engineer" was kept: the plural suffix reaches
        only a term's final word, so `forward deployed` cannot produce it."""
        self.assertEqual(MATCHER.match("Forward Deployment Engineer"), "forward deployment")
        self.assertEqual(MATCHER.match("Senior Forward Deployed Engineer"), "forward deployed")
        self.assertIsNone(MATCHER.match("Deployment Engineer"))

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


class TestTheLocationRule(unittest.TestCase):
    """D13, the operator's decision of 2026-09-26: no posting he is not
    eligible for, and none missed that he is. The brief's named cases of the
    days before any location rule still hold."""

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

    def test_a_posting_only_for_another_country_is_dropped(self):
        """"if there is an ai engineer post from usa and it says only us
        people then i am out"."""
        for location in ("United States", "Remote, United States", "United States - Remote",
                         "San Jose, CA, USA", "Bangalore, India", "Latin America",
                         "Remote (Europe)", "Lisbon, Portugal\nPrague, Czechia\nWarsaw, Poland"):
            with self.subTest(location=location):
                kept, drop = keep(location=location)
                self.assertFalse(kept)
                self.assertEqual(drop["rule"], "location")

    def test_pakistan_anywhere_in_the_list_keeps_it(self):
        for location in ("Pakistan", "Lahore, Punjab, Pakistan", "India, Pakistan",
                         "United States, Pakistan", "Cairo; Islamabad; Karachi; Lahore"):
            with self.subTest(location=location):
                self.assertTrue(keep(location=location)[0])

    def test_on_site_in_pakistan_is_only_karachi(self):
        """"any onsite post besides karachi, pakistan are automatically out".
        A Pakistan location that does not say on site is kept: that it is on
        site cannot be read from it."""
        self.assertFalse(keep(location="Hybrid - Lahore, Pakistan")[0])
        self.assertFalse(keep(location="On-site, Islamabad, Pakistan")[0])
        self.assertTrue(keep(location="On-site, Karachi, Pakistan")[0])
        self.assertTrue(keep(location="Lahore, Pakistan")[0])

    def test_anything_unclear_is_kept(self):
        """An unrecognised place, or one saying "except", can only let a
        posting through, never lose one."""
        for location in ("Manila", "Kingswinford", "Hybrid - Vancouver",
                         "Remote, anywhere except US", "EMEA", "Asia Pacific"):
            with self.subTest(location=location):
                self.assertTrue(keep(location=location)[0])

    def test_a_word_is_never_matched_inside_another(self):
        """"India" must not close "Indiana", nor "Oman" close "Romania"'s
        neighbour: whole words only. Indiana is not listed, so it is unclear
        and kept."""
        self.assertTrue(keep(location="Indianapolis, Indiana")[0])


class TestTheAgeRule(unittest.TestCase):
    """D14, the operator's decision of 2026-09-26: "i do not want a job post
    more than a week old". NOW is 2026-09-16."""

    def row_dated(self, published, source="greenhouse", first_seen=None):
        r = row()
        r.published_at = r.ordering_date = published
        r.published_meaning_unconfirmed = source == "lever"
        if first_seen:
            r.first_seen = first_seen
        return r

    def test_a_week_old_is_kept_and_a_day_more_is_dropped(self):
        kept, drops = apply_chain([self.row_dated("2026-09-09T12:00:00Z"),
                                   self.row_dated("2026-09-09T11:59:00Z")],
                                  NOW_ISO, matcher=MATCHER)
        self.assertEqual(len(kept), 1)
        self.assertEqual(drops[0]["rule"], "age")

    def test_a_lever_posting_first_seen_this_week_is_kept(self):
        """Lever's createdAt is not proven to mean publication; a fresh
        posting must not be lost to it. A Greenhouse date is trusted."""
        lever = self.row_dated("2026-08-01T00:00:00Z", source="lever",
                               first_seen="2026-09-15T00:00:00Z")
        greenhouse = self.row_dated("2026-08-01T00:00:00Z", first_seen="2026-09-15T00:00:00Z")
        kept, drops = apply_chain([lever, greenhouse], NOW_ISO, matcher=MATCHER)
        self.assertEqual([r.published_meaning_unconfirmed for r, _ in kept], [True])
        self.assertEqual([d["rule"] for d in drops], ["age"])

    def test_a_posting_with_no_date_is_kept(self):
        r = self.row_dated(None)
        self.assertEqual(len(apply_chain([r], NOW_ISO, matcher=MATCHER)[0]), 1)

    def test_the_limit_is_configuration(self):
        from src.filters import ELIGIBILITY
        self.assertEqual(ELIGIBILITY.max_age_days, 7)


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


class TestRoleFamilies(unittest.TestCase):
    """The operator's order, 2026-09-17: agentic AI, then LLM and applied AI,
    then traditional AI and ML, then software engineering. Order decides only
    which term a title is credited to; ADR-0010 still orders the display by
    date."""

    def test_the_families_come_in_the_operators_order(self):
        terms = MATCHER.terms
        first = {name: terms.index(name) for name in
                 ("agentic", "ai engineer", "machine learning", "software engineer i")}
        self.assertLess(first["agentic"], first["ai engineer"])
        self.assertLess(first["ai engineer"], first["machine learning"])
        self.assertLess(first["machine learning"], first["software engineer i"])
        self.assertEqual(terms[:5], ["agentic", "ai agent", "agent engineer",
                                     "multi agent", "agentops"])

    def test_a_title_in_two_families_is_credited_to_the_higher(self):
        self.assertEqual(MATCHER.match("Senior Agentic AI Engineer"), "agentic")
        self.assertEqual(MATCHER.match("Software Engineer, Machine Learning"), "machine learning")
        self.assertEqual(MATCHER.match("Backend Engineer, AI Platform"), "ai platform")

    def test_entry_level_software_terms_keep_their_credit(self):
        self.assertEqual(MATCHER.match("Software Engineer I"), "software engineer i")
        self.assertEqual(MATCHER.match("Junior Software Engineer"), "junior software engineer")
        self.assertEqual(MATCHER.match("Software Engineer"), "software engineer")

    def test_the_software_terms_the_operator_chose_admit_their_titles(self):
        for title, term in (("Python Backend Engineer", "backend engineer"),
                            ("Backend Developer", "backend developer"),
                            ("Back-End Developer", "back end developer"),
                            ("Full Stack Python and React Engineer", "full stack"),
                            ("FullStack Developer", "fullstack developer"),
                            ("Fullstack Engineer", "fullstack engineer"),
                            ("Mobile Developer (Flutter)", "mobile developer"),
                            ("Data Engineer", "data engineer"),
                            ("QA Automation Engineer", "automation engineer"),
                            ("Software Developer in Test (Python)", "software developer"),
                            ("Software Engineer, Platform", "software engineer")):
            self.assertEqual(MATCHER.match(title), term, title)


class TestAITermsVersionFour(unittest.TestCase):
    """The eighteen terms the operator added on 2026-09-18, before the boards
    that carry such roles exist. Only one matched anything on the 804 postings
    stored then, which is why they are in place early."""

    def test_the_gerund_forms_the_plural_rule_cannot_produce(self):
        """`ai engineer` cannot produce "AI Engineering": the suffix is
        "(?:e?s)?" on the last word. The same gap as `forward deployment`."""
        self.assertEqual(MATCHER.match("AI Engineering Intern"), "ai engineering")
        self.assertEqual(MATCHER.match("Prompt Engineering Specialist"), "prompt engineering")
        self.assertEqual(MATCHER.match("Context Engineering Analyst"), "context engineering")

    def test_the_real_posting_that_proved_the_gap(self):
        """Veeam's "Platform, Security & AI Engineering Intern - Summer 2027",
        on the data branch at 91f7518, was dropped by version 3 and is the
        only posting version 4 admits."""
        kept, drop = keep(title="Platform, Security & AI Engineering Intern - Summer 2027")
        self.assertTrue(kept, drop and drop["rule"])

    def test_the_other_new_terms_admit_their_titles(self):
        for title, term in (("Agent Developer", "agent developer"),
                            ("Autonomous Agents Engineer", "autonomous agent"),
                            ("ML Engineer", "ml engineer"),
                            ("ML Ops Engineer", "ml ops"),
                            ("Computer Vision Engineer", "computer vision"),
                            ("Data Science Intern", "data science"),
                            ("AI Researcher", "ai researcher"),
                            ("AI Research Scientist", "ai research"),
                            ("Applied Scientist", "applied scientist"),
                            ("AI Specialist", "ai specialist"),
                            ("AI Architect", "ai architect"),
                            ("AI Integration Engineer", "ai integration"),
                            ("AI Consultant", "ai consultant"),
                            ("AI Infrastructure Engineer", "ai infrastructure")):
            self.assertEqual(MATCHER.match(title), term, title)

    def test_bare_research_engineer_is_not_a_term(self):
        """Rejected under ADR-0021's `ai red team` precedent: the bare term
        pulls research engineering of every other kind."""
        self.assertIsNone(MATCHER.match("Research Engineer"))
        self.assertIsNone(MATCHER.match("Senior Research Engineer, Materials"))
        self.assertEqual(MATCHER.match("AI Research Engineer"), "ai research")

    def test_gen_ai_spelled_apart_is_admitted(self):
        """`genai` is an exempt single token and cannot match "Gen AI". The
        title has to be one no earlier term also matches, or the test passes
        with `gen ai` gone: "Gen AI Engineer" is credited to `ai engineer`."""
        self.assertEqual(MATCHER.match("Gen AI Specialist"), "gen ai")
        self.assertEqual(MATCHER.match("GenAI Engineer"), "genai")


class TestSeniority(unittest.TestCase):
    """docs/reference/seniority-exclusions.md, version 1, decided by the
    operator on 2026-09-17: open to intern, junior, associate, mid-level and
    untitled roles; II and III excluded after checking; architect kept."""

    def test_senior_level_titles_are_dropped_by_the_seniority_rule(self):
        for title in ("Senior AI Engineer", "Sr. AI Engineer", "Staff AI Engineer",
                      "Lead AI Engineer", "Machine Learning Team Lead", "Principal AI Engineer",
                      "Head of Machine Learning", "Machine Learning Manager",
                      "Director, Machine Learning", "VP, AI Platform",
                      "Vice President, Applied AI", "Chief Machine Learning Scientist",
                      "AI Engineer II", "Software Engineer III - Backend",
                      "Machine Learning Engineer IV", "AI Engineer - Mid/Senior"):
            kept, drop = keep(title=title)
            self.assertFalse(kept, title)
            self.assertEqual(drop["rule"], "seniority", title)

    def test_the_levels_the_operator_can_reach_are_kept(self):
        for title in ("AI Engineer", "AI/ML Intern Summer 2027", "Junior AI Engineer",
                      "Associate Machine Learning Engineer", "AI Engineer (Mid-Level)",
                      "Graduate AI Engineer", "Software Engineer I",
                      "AI Solutions Architect", "AI Automation Engineer, Management Trainee"):
            kept, drop = keep(title=title)
            self.assertTrue(kept, "%s dropped by %s" % (title, drop and drop["rule"]))

    def test_an_accented_senior_word_is_dropped_too(self):
        """Production's first projection put "Fullstack Developer | Sênior
        (13593)" in Jobs on 2026-09-24. The operator decided accents are
        stripped before matching; this is that title."""
        kept, drop = keep(title="Fullstack Developer | Sênior (13593)")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "seniority")

    def test_senior_with_level_one_is_still_dropped(self):
        """Careem's "Senior Software Engineer I": the operator accepted that a
        senior word drops it whatever level follows."""
        kept, drop = keep(title="Senior Software Engineer I")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "seniority")

    def test_words_match_whole_never_inside_another_word(self):
        for title in ("Staffing AI Engineer", "Headless AI Engineer",
                      "AI Engineer, Leadership Programme", "AI Engineer, Directory Services",
                      "AI Engineer, Seniority Models", "AI Engineer, Chiefly Remote"):
            self.assertIsNone(MATCHER.excluded_word(title), title)
        self.assertEqual(MATCHER.excluded_word("AI Team Leads"), "lead")

    def test_uk_and_i_is_not_a_level(self):
        """A naive level match read "UK&I" as level I in the evidence check."""
        self.assertIsNone(MATCHER.excluded_word("AI Engineer, UK&I"))

    def test_an_unadmitted_senior_title_is_a_title_drop(self):
        """Seniority runs after the title rule, so the drop log keeps recording
        every title the pool is missing, senior or not."""
        kept, drop = keep(title="Senior Account Executive")
        self.assertFalse(kept)
        self.assertEqual(drop["rule"], "title")

    def test_a_kept_row_still_names_the_term_that_admitted_it(self):
        kept, _ = apply_chain([row(title="Junior Data Engineer")], NOW_ISO, matcher=MATCHER)
        self.assertEqual(kept[0][1], "matched 'data engineer'")

    def test_the_run_log_counts_seniority_drops_separately(self):
        _, drops = apply_chain([row(title="Senior AI Engineer"),
                                row(title="Chief Happiness Officer")],
                               NOW_ISO, matcher=MATCHER)
        counts = drop_counts(drops)
        self.assertEqual((counts["seniority"], counts["title"]), (1, 1))

    def test_the_rule_names_the_word(self):
        verdict = rule_seniority(row(title="Principal AI Engineer"), matcher=MATCHER)
        self.assertEqual(verdict.reason, "senior-level word 'principal' in title")

    def test_the_word_list_is_read_from_its_section_only(self):
        """The file quotes the words it deliberately keeps elsewhere; reading
        them would exclude architects and interns."""
        words = load_seniority_words()
        self.assertEqual(words, ["senior", "sr", "staff", "lead", "principal", "head",
                                 "manager", "director", "vp", "vice president", "chief",
                                 "ii", "iii", "iv"])
        for kept_word in ("architect", "intern", "junior", "associate", "i"):
            self.assertNotIn(kept_word, words)

    def test_a_missing_or_empty_word_list_stops_the_run_starting(self):
        import tempfile
        with self.assertRaises(FilterError):
            load_seniority_words(os.path.join(tempfile.gettempdir(), "no-such-file.md"))
        for text in ("# nothing here\n", "## Excluded words\n\nnone listed\n\n## Next\n`senior`\n"):
            fd, path = tempfile.mkstemp(suffix=".md")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            try:
                with self.assertRaises(FilterError):
                    load_seniority_words(path)
            finally:
                os.unlink(path)


class TestTermFamilies(unittest.TestCase):
    """ADR-0038's label. The pool's four headings were read and discarded by
    load_title_pool, so no family reached a row until 2026-09-18."""

    def test_every_shipped_term_belongs_to_exactly_one_family(self):
        """The check that protects the real pool. A term added outside a
        heading, or a heading renamed, shows up here."""
        from src.filters import load_term_families
        terms, _ = load_title_pool()
        families = load_term_families()
        self.assertEqual(len(families), len(terms))
        self.assertEqual(sorted(families), sorted(set(terms)))
        self.assertEqual(sorted(set(families.values())),
                         ["Agentic AI", "LLM and applied AI",
                          "Software engineering", "Traditional AI and ML"])

    def test_the_family_is_the_heading_the_term_sits_under(self):
        from src.filters import load_term_families
        families = load_term_families()
        self.assertEqual(families["agentic"], "Agentic AI")
        self.assertEqual(families["software engineer"], "Software engineering")
        self.assertEqual(families["mlops"], "Traditional AI and ML")

    def test_a_pool_without_headings_has_no_families_rather_than_failing(self):
        """A candidate pool previewed against real postings is a smaller
        document with no headings. That is not a defect."""
        from src.filters import load_term_families
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("## Terms\n\n`ai engineer`\n\n## Known behaviour\n")
        try:
            self.assertEqual(load_term_families(path), {})
        finally:
            os.unlink(path)

    def test_a_term_outside_a_heading_is_a_defect_and_raises(self):
        """Headings present and a term above them means a term nobody can
        name a family for, which is different from a pool with no families."""
        from src.filters import load_term_families
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("## Terms\n\n`orphan term`\n\n### 1. Agentic AI\n\n"
                    "`ai agent`\n\n## Known behaviour\n")
        try:
            with self.assertRaises(FilterError):
                load_term_families(path)
        finally:
            os.unlink(path)

    def test_the_matcher_reports_a_family_for_a_matched_title(self):
        self.assertEqual(MATCHER.family_of(MATCHER.match("Agentic Systems Engineer")),
                         "Agentic AI")
        self.assertIsNone(MATCHER.family_of(None))
        self.assertIsNone(MATCHER.family_of("not a pool term"))


class TestAnnotationVendorFile(unittest.TestCase):
    """ADR-0031: the vendor list is configuration, not a constant. It was a
    tuple in src/filters.py until 2026-09-17."""

    def test_the_names_are_read_from_their_section_only(self):
        """The file quotes `src/filters.py`, `ANNOTATION_VENDORS` and a tool
        path in backticks outside the Vendors section. Reading the whole
        document would turn each of those into a vendor name."""
        names = load_annotation_vendors()
        self.assertEqual(names, ["welo data", "welocalize", "innodata"])
        for not_a_vendor in ("src filters py", "annotation vendors",
                             "tools title pool report py dropped"):
            self.assertNotIn(not_a_vendor, names)

    def test_the_loaded_list_is_what_the_chain_uses(self):
        self.assertEqual(tuple(load_annotation_vendors()), ANNOTATION_VENDORS)
        self.assertFalse(rule_annotation_vendor(row(employer="Welocalize"),
                                                ANNOTATION_VENDORS).keep)

    def test_a_missing_or_empty_vendor_list_stops_the_run_starting(self):
        import tempfile
        with self.assertRaises(FilterError):
            load_annotation_vendors(os.path.join(tempfile.gettempdir(), "no-such-file.md"))
        for text in ("# nothing here\n", "## Vendors\n\nnone listed\n\n## Next\n`innodata`\n"):
            fd, path = tempfile.mkstemp(suffix=".md")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            try:
                with self.assertRaises(FilterError):
                    load_annotation_vendors(path)
            finally:
                os.unlink(path)


class TestADR0021CaseSet(unittest.TestCase):
    """ADR-0021's Confirmation, through the whole chain. The first two must be
    admitted, the next five must not, and the last is the one to watch.

    Pool version 3 adds `software engineer`, so "Software Engineer II" now
    matches the pool; the seniority rule is what keeps it out. That departs
    from the record's wording and is raised with the architecture chat."""

    def test_the_two_that_must_be_admitted(self):
        for title in ("AI-Agent Engineer", "Agentic Systems Engineer"):
            self.assertTrue(keep(title=title)[0], title)

    def test_the_five_that_must_not(self):
        for title, rule in (("Storage Engineer", "title"),
                            ("Senior Red Team Operator", "title"),
                            ("Accounts Officer", "title"),
                            ("Sales Executive – Healthcare IT", "title"),
                            ("Software Engineer II", "seniority")):
            kept, drop = keep(title=title)
            self.assertFalse(kept, title)
            self.assertEqual(drop["rule"], rule, title)
        self.assertEqual(MATCHER.match("Software Engineer II"), "software engineer")

    def test_the_one_to_watch(self):
        """"Non-AI Systems Analyst" normalises to contain "ai systems", so
        `ai system` admits it. A false admission, recorded as current
        behaviour so that any change to it is noticed."""
        self.assertEqual(MATCHER.match("Non-AI Systems Analyst"), "ai system")
        self.assertTrue(keep(title="Non-AI Systems Analyst")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
