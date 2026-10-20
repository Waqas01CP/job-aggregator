"""Board configuration: one entry per board, loaded and validated.

A board entry names its platform, its slug, and the normalisations that apply
to it. Nothing else. The employer comes from the payload where the platform
returns one, and from `employer_alias` where it does not (ADR-0026).

Slugs come from the operator's registry, never from memory or a spike log.
The file records which part of the registry each came from.

Per-source normalisation is ADR-0027. A normalisation is applied to a board
only once it has been measured on that board, because an unmeasured
normalisation silently merges distinct postings. Only Speechify has one.
"""

import json
import os
from dataclasses import dataclass, field

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(REPO_ROOT, "config", "boards.json")

# Platforms this build adapts. ADR-0009 fixed the slice at the first two;
# Manatal is ADR-0059's first, by measured yield, on 2026-10-07; Workable
# second, on 2026-10-08; SmartRecruiters third, on 2026-10-17; Ashby fourth,
# on 2026-10-17. Hacker News' thread and job stories, ADR-0063's second wave,
# on 2026-10-18; Jobicy, RemoteOK and We Work Remotely the same day.
# Python.org's job board from research 0006, on 2026-10-20.
PLATFORMS = frozenset({"greenhouse", "lever", "himalayas", "manatal", "workable",
                       "smartrecruiters", "ashby", "hackernews", "hnjobs", "jobicy",
                       "remoteok", "weworkremotely", "pythonorg"})

# Every normalisation that may be named by a board entry. A name outside this
# set is a typo, and a typo that silently did nothing would be invisible: the
# dedupe key would quietly stop collapsing a board's location variants.
NORMALISATIONS = frozenset({"strip_location_suffix"})

# ADR-0019 source classes. ADR-0020 routes raw storage by this: employer ATS
# rows go to the public data branch, aggregator rows stay local and are never
# committed, because two feeds prohibit redistribution and a branch inherits
# its repository's visibility. Hacker News is one too, the seat's statement
# under ADR-0063 (Brief 16, item 2): its posts are written by many employers'
# people on a site that is not theirs, and nothing in its terms grants
# republishing them, so its rows keep to the private store with Himalayas'.
# Jobicy's terms forbid redistributing its listings (ADR-0019), so its too;
# and RemoteOK's and We Work Remotely's, whose terms ask for their link and
# name with every row. Python.org's job board too, ADR-0063's Changes of
# 2026-10-20: many employers' postings on a site that is not theirs, whose
# Legal Statements grant no republishing.
# One platform a line, so adding one moves no other's line.
AGGREGATOR_PLATFORMS = frozenset({
    "himalayas",
    "hackernews",
    "hnjobs",
    "jobicy",
    "remoteok",
    "weworkremotely",
    "pythonorg",
})

# Sources whose rows may reach the public data branch. Named rather than
# derived as "not an aggregator", so a source this build does not know, such
# as one whose platform has since been removed, stays local. Defaulting an
# unknown source to public is the direction that leaks.
PUBLISHABLE_SOURCES = PLATFORMS - AGGREGATOR_PLATFORMS


def is_publishable(source):
    return source in PUBLISHABLE_SOURCES

# Platforms whose payload carries no employer field. A board on one of these
# needs an alias or its employer is unresolvable. ADR-0026 requires the absence
# to be recorded rather than guessed, so this is not a hard error here.
NO_EMPLOYER_IN_PAYLOAD = frozenset({"lever", "ashby"})


class ConfigError(Exception):
    """Raised when a board entry cannot be trusted. Never repaired silently."""


# ADR-0048: a source is polled no faster than its feed refreshes, configured
# per source. The workflow names the run's slot from the cron that fired it;
# a manual dispatch or a local run is neither slot and polls every source.
SLOTS = ("morning", "evening")


@dataclass(frozen=True)
class Board:
    platform: str
    slug: str
    normalisations: tuple = ()
    employer_alias: str = None
    note: str = ""
    poll_slots: tuple = ()      # empty means every slot
    # ADR-0053's Changes, 2026-10-16: the slots on which a paginated walk
    # reads to the age limit instead of stopping at the board's stored mark.
    # Postings reach Himalayas' search late, dated before the mark, and a walk
    # that stops at the mark never reads them: 35 on 2026-10-16.
    deep_slots: tuple = ()

    def polled_on(self, slot):
        """Whether a run in this slot asks this board. A run that is not a
        scheduled slot, a dispatch or a local run, asks every board."""
        return slot not in SLOTS or not self.poll_slots or slot in self.poll_slots

    @property
    def source_class(self):
        return "aggregator" if self.platform in AGGREGATOR_PLATFORMS else "ats"

    @property
    def source(self):
        """The source name, which is the raw-layer filename. ADR-0020."""
        return self.platform

    @property
    def board_id(self):
        return "%s:%s" % (self.platform, self.slug)


def _validate(entry, index, seen):
    where = "boards[%d]" % index
    if not isinstance(entry, dict):
        raise ConfigError("%s: entry is %s, expected an object" % (where, type(entry).__name__))

    platform = entry.get("platform")
    if platform not in PLATFORMS:
        raise ConfigError("%s: platform %r is not one of %s"
                          % (where, platform, sorted(PLATFORMS)))

    slug = entry.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise ConfigError("%s: slug %r is empty or not a string" % (where, slug))
    if slug != slug.strip():
        raise ConfigError("%s: slug %r has leading or trailing whitespace" % (where, slug))
    if any(c.isspace() for c in slug):
        raise ConfigError("%s: slug %r contains whitespace" % (where, slug))
    # A URL pasted where a slug belongs would build a nonsense endpoint and
    # 404 in a way that reads like a dead board rather than a config error.
    if "/" in slug or ":" in slug or slug.startswith("http"):
        raise ConfigError("%s: slug %r looks like a URL, not a slug" % (where, slug))

    key = (platform, slug)
    if key in seen:
        raise ConfigError("%s: duplicate board %s:%s, already at boards[%d]"
                          % (where, platform, slug, seen[key]))
    seen[key] = index

    norms = entry.get("normalisations", [])
    if not isinstance(norms, list):
        raise ConfigError("%s: normalisations is %s, expected a list"
                          % (where, type(norms).__name__))
    for n in norms:
        if n not in NORMALISATIONS:
            raise ConfigError("%s: normalisation %r is not one of %s"
                              % (where, n, sorted(NORMALISATIONS)))

    alias = entry.get("employer_alias")
    if alias is not None and (not isinstance(alias, str) or not alias.strip()):
        raise ConfigError("%s: employer_alias %r is empty or not a string" % (where, alias))

    slots = entry.get("poll_slots", [])
    if not isinstance(slots, list):
        raise ConfigError("%s: poll_slots is %s, expected a list" % (where, type(slots).__name__))
    for s in slots:
        if s not in SLOTS:
            raise ConfigError("%s: poll_slot %r is not one of %s" % (where, s, list(SLOTS)))

    deep = entry.get("deep_slots", [])
    if not isinstance(deep, list):
        raise ConfigError("%s: deep_slots is %s, expected a list" % (where, type(deep).__name__))
    for s in deep:
        if s not in SLOTS:
            raise ConfigError("%s: deep_slot %r is not one of %s" % (where, s, list(SLOTS)))

    return Board(platform=platform, slug=slug, normalisations=tuple(norms),
                 employer_alias=alias, note=entry.get("note", ""), poll_slots=tuple(slots),
                 deep_slots=tuple(deep))


def load_boards(path=None):
    """Read and validate the board list. Raises ConfigError rather than
    returning a partial list, because a half-loaded board set would poll an
    unpredictable subset and log it as a complete run."""
    path = path or DEFAULT_PATH
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except FileNotFoundError:
        raise ConfigError("board config not found at %s" % path)
    except json.JSONDecodeError as e:
        raise ConfigError("board config at %s is not valid JSON: %s" % (path, e))

    if not isinstance(doc, dict) or "boards" not in doc:
        raise ConfigError("board config at %s has no 'boards' key" % path)
    entries = doc["boards"]
    if not isinstance(entries, list) or not entries:
        raise ConfigError("board config at %s has an empty or non-list 'boards'" % path)

    seen = {}
    return [_validate(e, i, seen) for i, e in enumerate(entries)]


SWEEP_PATH = os.path.join(REPO_ROOT, "config", "sweep.json")


@dataclass(frozen=True)
class SweepConfig:
    """ADR-0050's numbers. Configuration under ADR-0031, never constants."""
    closed_after_polled_runs: int
    retire_after_days: int
    run_log_window: int
    unreviewed_after_days: int
    clearing_dry_run_valid_hours: int
    budget_warning_share: float
    budget_warning_before_day: int
    # ADR-0062's guard on the pipeline's own calls. The default is Airtable's
    # whole allowance, for tests that build a config by hand; the shipped
    # figure is the file's.
    monthly_call_ceiling: int = 1000
    # ADR-0062: each rejection table's reason choices, mirroring the base, so
    # `Reason` is written into a copy only when the field offers it.
    reason_choices: dict = field(default_factory=dict)
    # Brief 13: whether the projection sends the description's values to
    # `Jobs` (airtable.DESCRIPTION_FIELDS). Off until the operator has made
    # the fields and the month has room for the one re-send of every row.
    description_fields_shown: bool = False
    # ADR-0063: sources fetched and stored but not sent to `Jobs` while the
    # month's allowance cannot carry their rows.
    held_from_display: tuple = ()


# The tables whose reason field the sweep may fill from `Reason`.
REASON_TABLES = ("rejected-not-a-fit", "rejected-poor-filtering")


# Airtable's free plan: 1,000 calls a month per workspace. A ceiling above it
# would guard nothing.
AIRTABLE_MONTHLY_ALLOWANCE = 1000


def load_sweep_config(path=None):
    """Read and validate the sweep's numbers. Raises ConfigError naming the
    field: a closure count of zero would close every posting on the next run,
    and a retirement of zero days would delete a classification the moment
    it was made."""
    path = path or SWEEP_PATH
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except FileNotFoundError:
        raise ConfigError("sweep config not found at %s" % path)
    except json.JSONDecodeError as e:
        raise ConfigError("sweep config at %s is not valid JSON: %s" % (path, e))
    if not isinstance(doc, dict):
        raise ConfigError("sweep config at %s is not an object" % path)

    def whole(name, low):
        value = doc.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < low:
            raise ConfigError("sweep config: %s must be a whole number of at least %d, "
                              "got %r" % (name, low, value))
        return value

    share = doc.get("budget_warning_share")
    if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0 < share < 1:
        raise ConfigError("sweep config: budget_warning_share must be between 0 and 1, "
                          "got %r" % (share,))
    day = whole("budget_warning_before_day", 1)
    if day > 31:
        raise ConfigError("sweep config: budget_warning_before_day must be a day of the "
                          "month, got %r" % day)
    runs, window = whole("closed_after_polled_runs", 1), whole("run_log_window", 1)
    # The closure test counts runs in the logs it reads, so a window shorter
    # than the count would let no posting close, silently. The count went
    # from four to twelve on 2026-10-03.
    if window < runs:
        raise ConfigError("sweep config: run_log_window (%d) must hold at least "
                          "closed_after_polled_runs (%d) runs, or no posting can close"
                          % (window, runs))
    ceiling = whole("monthly_call_ceiling", 1)
    if ceiling > AIRTABLE_MONTHLY_ALLOWANCE:
        raise ConfigError("sweep config: monthly_call_ceiling (%d) is above Airtable's "
                          "allowance of %d, so it guards nothing"
                          % (ceiling, AIRTABLE_MONTHLY_ALLOWANCE))
    choices = doc.get("reason_choices")
    if not isinstance(choices, dict) or set(choices) != set(REASON_TABLES) or not all(
            isinstance(v, list) and v and all(isinstance(c, str) and c.strip() for c in v)
            for v in choices.values()):
        raise ConfigError("sweep config: reason_choices must give each of %s a non-empty list "
                          "of choices" % ", ".join(REASON_TABLES))
    shown = doc.get("description_fields_shown")
    if not isinstance(shown, bool):
        raise ConfigError("sweep config: description_fields_shown must be true or false, "
                          "got %r" % (shown,))
    held = doc.get("sources_held_from_display", [])
    if not isinstance(held, list) or not all(isinstance(s, str) and s in PLATFORMS for s in held):
        raise ConfigError("sweep config: sources_held_from_display must be a list of sources "
                          "this build adapts, got %r" % (held,))
    return SweepConfig(monthly_call_ceiling=ceiling, description_fields_shown=shown,
                       held_from_display=tuple(held),
                       reason_choices={t: tuple(v) for t, v in choices.items()},
                       closed_after_polled_runs=runs,
                       retire_after_days=whole("retire_after_days", 1),
                       run_log_window=window,
                       unreviewed_after_days=whole("unreviewed_after_days", 1),
                       clearing_dry_run_valid_hours=whole("clearing_dry_run_valid_hours", 1),
                       budget_warning_share=float(share),
                       budget_warning_before_day=day)


def boards_missing_employer_alias(boards):
    """Boards whose platform returns no employer and which carry no alias.
    ADR-0026: such a row records its employer as unresolved rather than
    guessing an expansion of the slug."""
    return [b for b in boards
            if b.platform in NO_EMPLOYER_IN_PAYLOAD and not b.employer_alias]
