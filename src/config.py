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

# Platforms this build adapts. ADR-0009 fixes the slice at these two.
PLATFORMS = frozenset({"greenhouse", "lever", "himalayas"})

# Every normalisation that may be named by a board entry. A name outside this
# set is a typo, and a typo that silently did nothing would be invisible: the
# dedupe key would quietly stop collapsing a board's location variants.
NORMALISATIONS = frozenset({"strip_location_suffix"})

# ADR-0019 source classes. ADR-0020 routes raw storage by this: employer ATS
# rows go to the public data branch, aggregator rows stay local and are never
# committed, because two feeds prohibit redistribution and a branch inherits
# its repository's visibility.
AGGREGATOR_PLATFORMS = frozenset({"himalayas"})

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
NO_EMPLOYER_IN_PAYLOAD = frozenset({"lever"})


class ConfigError(Exception):
    """Raised when a board entry cannot be trusted. Never repaired silently."""


@dataclass(frozen=True)
class Board:
    platform: str
    slug: str
    normalisations: tuple = ()
    employer_alias: str = None
    note: str = ""

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

    return Board(platform=platform, slug=slug, normalisations=tuple(norms),
                 employer_alias=alias, note=entry.get("note", ""))


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


def boards_missing_employer_alias(boards):
    """Boards whose platform returns no employer and which carry no alias.
    ADR-0026: such a row records its employer as unresolved rather than
    guessing an expansion of the slug."""
    return [b for b in boards
            if b.platform in NO_EMPLOYER_IN_PAYLOAD and not b.employer_alias]
