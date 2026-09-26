"""Holding the operator's D13 and D14 aside, for a test of another mechanism.

Grouping, the skip, backfill and the sweep are tested on saved responses and
fixtures dated weeks before any clock the suite runs on, and on real boards
whose cities are mostly outside Pakistan. With the location and age rules on,
those tests would test the rules instead. A test that wants them off says so
by using `rules_aside()`; the rules themselves are tested in test_filters.py.
"""

import contextlib
import dataclasses

from src import filters


@contextlib.contextmanager
def rules_aside():
    real = filters.ELIGIBILITY
    filters.ELIGIBILITY = dataclasses.replace(real, max_age_days=365 * 100, closed=())
    try:
        yield
    finally:
        filters.ELIGIBILITY = real
