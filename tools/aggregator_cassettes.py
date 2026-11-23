"""ADR-0020's guard: no aggregator's real response in a committed cassette.

ADR-0020 says no aggregator content reaches the public repository, and
promised "a guard rejecting an aggregator-sourced file from a commit"; ADR-0017
records a real response per platform. The fifth audit's F2 found ten
aggregator cassettes holding real postings, and the operator decided on
2026-11-23 (Brief 20, decision 2) that ADR-0020 wins: an aggregator's cassette
is made-up postings of the real shape, an employer board's stays a real
response.

**What "made up" means here, so a check can fail.** The cassette is parsed by
its own platform's adapter, and every posting must name its employer as
`Example Employer N`, which no real employer is called. Hasjob's feed names no
employer, so there every posting's link must be an example link. Hacker News'
stories cassette holds the `whoishiring` account's own monthly threads, not
postings, so there every entry must be one of its "Ask HN:" threads. A real
recording fails at its first real employer.

The platform is the file name's first part, as every cassette here is named.
Usage: python tools/aggregator_cassettes.py <cassette> [<cassette> ...]; exits 1
naming each problem. The pre-commit hook runs it on staged cassettes, and the
suite on every committed one.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.config import AGGREGATOR_PLATFORMS, Board  # noqa: E402

MADE_UP_EMPLOYER = "Example Employer "


def platform_of(path):
    return os.path.basename(path).split("-", 1)[0]


def problems_in(path):
    """What makes this cassette a real aggregator response, or []. A cassette
    of an employer-board platform is not this guard's."""
    platform = platform_of(path)
    if platform not in AGGREGATOR_PLATFORMS:
        return []
    from src.run import ADAPTERS
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    name = os.path.basename(path)
    if platform == "hackernews" and isinstance(payload, dict) and "hits" in payload:
        return ["%s: an entry that is not one of the account's own threads: %r"
                % (name, str(h.get("title"))[:60])
                for h in payload["hits"] if not str(h.get("title") or "").startswith("Ask HN:")]
    try:
        result = ADAPTERS[platform].parse(payload, Board(platform=platform, slug="guard"))
    except Exception as e:
        return ["%s: its adapter cannot read it (%s), so it cannot be shown made up"
                % (name, type(e).__name__)]
    if not result.postings:
        return ["%s: no posting in it, so it cannot be shown made up" % name]
    found = []
    for p in result.postings:
        if platform == "hasjob":
            if "/example" not in (p.url or ""):
                found.append("%s: a real link: %s" % (name, p.external_id))
        elif not (p.employer or "").startswith(MADE_UP_EMPLOYER):
            found.append("%s: a real employer on posting %s" % (name, p.external_id))
    return found


def main(argv):
    found = [line for path in argv for line in problems_in(path)]
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
