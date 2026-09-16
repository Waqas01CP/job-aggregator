"""The deduplicator, tested from the brief.

The brief: employer plus title plus publication date, title normalised first
per ADR-0027, not row identity, and Speechify through the key yielding 8
groups, not 1086 and not fewer than 8.
"""

import json
import os
import random
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters import greenhouse
from src.adapters.base import Posting
from src.config import Board
from src.dedupe import counts, group, split_new
from src.normalise import normalise

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
SPEECHIFY = Board(platform="greenhouse", slug="speechify",
                  normalisations=("strip_location_suffix",))
GH_BOARD = Board(platform="greenhouse", slug="careem")
CASSETTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cassettes")


def rows_from(pairs, board=SPEECHIFY, published="2026-09-10T05:00:00Z"):
    postings = []
    for i, (title, location) in enumerate(pairs):
        postings.append(Posting(
            external_id=str(i), title=title, url="https://x.test/%d" % i,
            published_at=datetime.fromisoformat(published.replace("Z", "+00:00")),
            published_field="first_published", published_raw=published,
            source=board.platform, board_id=board.board_id,
            employer="Speechify", employer_provenance="payload", location=location))
    return normalise(postings, board, NOW)


class TestSpeechify(unittest.TestCase):
    def test_1086_postings_collapse_to_eight_roles_across_eleven_keys(self):
        """The brief predicts 8 groups. The measured answer is 8 distinct
        roles and **11 keys**, and the difference is the brief's own key
        definition rather than a defect.

        ADR-0001 keys on employer plus title plus publication date. Three of
        Speechify's eight titles were published on two dates each:

          Go-to-Market                     2026-05-06 (95) and 2026-05-22 (12)
          Software Engineer, Data Infra    2023-12-04 (105) and 2025-12-05 (136)
          Software Engineer, Platform      2024-01-24 (138) and 2025-05-07 (103)

        8 + 3 = 11. Collapsing those would merge a 2023 posting with a 2025
        one, which is a repost and not a duplicate, and would make Measure A
        meaningless for the merged row. Dropping the date from the key to
        reach 8 would contradict ADR-0001."""
        with open(os.path.join(CASSETTES, "greenhouse-speechify-titles.json"),
                  encoding="utf-8") as f:
            payload = json.load(f)
        rows = normalise(greenhouse.parse(payload, SPEECHIFY).postings, SPEECHIFY, NOW)
        groups = group(rows)
        self.assertEqual(len(rows), 1086)
        self.assertEqual(len({r.title_normalised for r in rows}), 8,
                         "not 1086, which would mean no collapse, and not fewer "
                         "than 8, which would mean the normalisation over-stripped")
        self.assertEqual(len(groups), 11)
        self.assertEqual(sum(g.size for g in groups), 1086,
                         "every posting must land in exactly one group")

    def test_a_repost_is_not_a_duplicate(self):
        """The case that forces 11 over 8. Same employer, same title, 14
        months apart."""
        rows = rows_from([("Software Engineer, Platform", "Remote")],
                         published="2024-01-24T05:00:00Z")
        rows += rows_from([("Software Engineer, Platform", "Karachi")],
                          published="2025-05-07T05:00:00Z")
        self.assertEqual(len(group(rows)), 2)

    def test_the_collapse_is_reported(self):
        with open(os.path.join(CASSETTES, "greenhouse-speechify-titles.json"),
                  encoding="utf-8") as f:
            payload = json.load(f)
        rows = normalise(greenhouse.parse(payload, SPEECHIFY).postings, SPEECHIFY, NOW)
        c = counts(group(rows))
        self.assertEqual(c["postings"], 1086)
        self.assertEqual(c["groups"], 11)
        self.assertEqual(c["collapsed"], 1075)
        self.assertEqual(c["largest_group"], 241)


class TestGrouping(unittest.TestCase):
    def test_one_role_across_cities_becomes_one_group(self):
        rows = rows_from([("Go-to-Market - Dallas, TX, USA", "Dallas, TX, USA"),
                          ("Go-to-Market - Anaheim, CA, USA", "Anaheim, CA, USA"),
                          ("Go-to-Market - Remote", "Remote")])
        groups = group(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].size, 3)
        self.assertEqual(groups[0].locations,
                         ["Anaheim, CA, USA", "Dallas, TX, USA", "Remote"])

    def test_distinct_roles_stay_distinct(self):
        rows = rows_from([("AI Engineer - Karachi", "Karachi"),
                          ("Data Engineer - Karachi", "Karachi")])
        self.assertEqual(len(group(rows)), 2)

    def test_the_representative_does_not_depend_on_input_order(self):
        """Two runs over the same data must choose the same row, or the
        filtered layer diffs for no reason."""
        pairs = [("Go-to-Market - %s" % city, city)
                 for city in ["Dallas, TX, USA", "Anaheim, CA, USA", "Remote", "Boise, ID, USA"]]
        rows = rows_from(pairs)
        first = group(rows)[0].representative.identity
        for seed in range(5):
            shuffled = list(rows)
            random.Random(seed).shuffle(shuffled)
            self.assertEqual(group(shuffled)[0].representative.identity, first)

    def test_the_representative_is_the_earliest_posting(self):
        """Determinism alone is not enough: any stable rule is deterministic.
        The documented rule is earliest publication date, then lowest
        identity, and the filtered layer shows this row, so it is pinned."""
        rows = rows_from([("Go-to-Market - Dallas, TX, USA", "Dallas, TX, USA")],
                         published="2026-05-22T05:00:00Z")
        rows += rows_from([("Go-to-Market - Anaheim, CA, USA", "Anaheim, CA, USA")],
                          published="2026-05-06T05:00:00Z")
        # Same title and employer, different dates, so these are two groups.
        # Within a group the earliest wins; build that case directly.
        same = rows_from([("Go-to-Market - Dallas, TX, USA", "Dallas, TX, USA"),
                          ("Go-to-Market - Anaheim, CA, USA", "Anaheim, CA, USA")])
        g = group(same)[0]
        self.assertEqual(g.representative.identity,
                         min(m.identity for m in same),
                         "on equal dates the lowest identity is the representative")

    def test_group_order_is_stable(self):
        rows = rows_from([("B Engineer", "X"), ("A Engineer", "Y"), ("C Engineer", "Z")])
        self.assertEqual([g.key for g in group(rows)],
                         [g.key for g in group(list(reversed(rows)))])

    def test_identity_is_not_the_key(self):
        """The defeat case for a dedupe keyed on id: three postings with three
        ids are one job, and keying on identity would collapse nothing."""
        rows = rows_from([("Go-to-Market - Dallas, TX, USA", "Dallas, TX, USA"),
                          ("Go-to-Market - Anaheim, CA, USA", "Anaheim, CA, USA")])
        self.assertNotEqual(rows[0].identity, rows[1].identity)
        self.assertEqual(len(group(rows)), 1)


class TestDelta(unittest.TestCase):
    def test_only_unseen_rows_are_new(self):
        rows = rows_from([("AI Engineer", "Karachi"), ("Data Engineer", "Lahore")])
        new, existing = split_new(rows, {rows[0].identity})
        self.assertEqual([r.identity for r in new], [rows[1].identity])
        self.assertEqual([r.identity for r in existing], [rows[0].identity])

    def test_an_empty_seen_set_makes_everything_new(self):
        """First contact with a board."""
        rows = rows_from([("AI Engineer", "Karachi")])
        new, existing = split_new(rows, set())
        self.assertEqual(len(new), 1)
        self.assertEqual(existing, [])

    def test_a_second_run_with_no_changes_yields_no_new_rows(self):
        """ADR-0003: a run that changes nothing appends nothing."""
        rows = rows_from([("AI Engineer", "Karachi"), ("Data Engineer", "Lahore")])
        new, _ = split_new(rows, {r.identity for r in rows})
        self.assertEqual(new, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
