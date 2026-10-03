"""What a posting's description says that stops the operator applying, even
when every other rule passes it: the years of experience it asks, a right to
work, citizenship or residence it requires in a named place, and whether it
says the role is worked on site. The operator, 2026-10-02: "it is high time
that we use the description", for "something which was not mentioned like
work permit of us required or 5+ years of experience".

**Phrases, never judgement** (ADR-0010). Each pattern below was measured over
every description saved privately by 2026-10-02, 1,708 postings, before it
was switched on, and each guard exists because a measured sentence needed
it. The log of 2026-10-02, its night section, has the counts.

**Only derived values leave this module.** The text is read and forgotten: a
row carries the years, the places a requirement names, and an on-site flag,
never a phrase of the description, so nothing an employer wrote reaches the
public branch beyond its metadata (ADR-0011; the text itself is kept only on
the private full branch, ADR-0051).

The thresholds, and which places are closed to him, are not here. They are
the operator's configuration (ADR-0031), applied by the filter chain.
"""

import html
import re
from dataclasses import dataclass

# Block-level tags end a line, so two bullets never read as one sentence:
# "<li>5+ years</li><li>experience with Go</li>" is two lines.
_BLOCK = re.compile(r"<\s*/?\s*(?:br|p|li|ul|ol|h[1-6]|div|tr|td|th|section|blockquote|article)"
                    r"\b[^>]*>", re.I)
_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Facts:
    """What one description says. `years` holds each figure's lower bound, a
    range by its low end ("3 to 5 years" is 3); `requirements` the place each
    requirement names, as written; `on_site` whether it says the role is
    worked on site with no remote option."""
    years: tuple = ()
    requirements: tuple = ()
    on_site: bool = False


def lines_of(*parts):
    """Each part HTML or plain text, as the lines a reader sees: block tags
    and line breaks end a line, other tags vanish, entities are decoded.
    Unescaped once before the tags are read, since Greenhouse escapes its
    HTML a second time."""
    lines = []
    for part in parts:
        if not isinstance(part, str) or not part.strip():
            continue
        text = _BLOCK.sub("\n", html.unescape(part))
        text = html.unescape(_TAG.sub(" ", text))
        for line in text.split("\n"):
            line = " ".join(line.split())
            if line:
                lines.append(line)
    return tuple(lines)


# ------------------------------------------------------------------ years
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
                 "twenty": 20}
_WORD = "|".join(_NUMBER_WORDS)
# A digit may follow a letter: one board's markup leaves a figure glued to
# the word before it, "Experience5 – 7 years", once its tags are gone.
_FIGURE = re.compile(
    r"(?:(?<![\d.,])(?P<digits>\d{1,2})|\b(?P<word>" + _WORD + r"))"
    r"(?:\s*\(\d{1,2}\))?(?:\s*(?:\+|plus))?"
    r"(?:\s*(?:-|–|—|to|or)\s*(?:\d{1,2}|" + _WORD + r")(?:\s*\(\d{1,2}\))?)?"
    r"(?:\s*(?:\+|plus))?(?:\s*or more)?\s*(?:years?|yrs?)\b", re.I)
# A figure that is not a minimum: "up to 5 years", "over the next 5 years",
# "within 2+ years", "the past 5 years".
_NOT_A_MINIMUM_BEFORE = re.compile(
    r"\b(?:up to|less than|fewer than|under|no more than|within|last|past|next|first|every|per)"
    r"\s*$", re.I)
# A line that opens with its figure is a requirement on every one of 30
# sampled from 89, bullets like "6+ years in fintech platforms" and "Minimum
# of 7 years leading teams". Bullets, numbering and labels may come first.
# (Every example in this module is written to the measured shape, never
# copied: ADR-0011 keeps description text out of this repository.)
_LINE_START = re.compile(
    r"^[\W\d_]*(?:(?:(?:a\s+)?minimum(?:\s+of)?|at\s+least|min\.?|requirements?|qualifications?"
    r"|must[- ]haves?|(?:required\s+|relevant\s+|work\s+|professional\s+|total\s+)?experienced?"
    r"(?:\s+required)?|years\s+of\s+experience)[\W_]*)*$", re.I)
_EXPERIENCE_AFTER = re.compile(r"^[^.;]{0,70}?\b(?:experience|exp)\b", re.I)
_EXPERIENCE_BEFORE = re.compile(r"\bexperience\b[^.;]{0,30}$", re.I)
# A sentence about the company, not the candidate: a firm citing its own
# decades of experience. Five of the 50 mid-sentence figures measured, and
# all five said so in one of these words; a sentence that also addresses the
# candidate is still a requirement: "We are looking for a developer with 5+
# years of experience".
_COMPANY_VOICE = re.compile(
    r"\b(?:compan(?:y|ies)|organi[sz]ations?|firm|agency|founded|spin-?off|bringing|brings|its"
    r"|in business|our\s+(?:company|firm|founders|history|clients))\b", re.I)
_CANDIDATE_VOICE = re.compile(
    r"\b(?:you|your|candidates?|applicants?|ideal|looking for|seeking|hiring|requir\w*|must"
    r"|minimum|at least|need\w*|suit\w*|should)\b", re.I)
# A line that opens the role to less experience than its figure, a
# preferred range of years beside "fresh graduates considered", is a role he
# can apply for (D13: "i do not want to miss any to which i am eligible to").
_OPENED = re.compile(r"\b(?:fresh|recent|new)\s+grad(?:uate)?s?\b|\bno\s+(?:prior\s+)?experience"
                     r"\s+(?:is\s+)?(?:required|necessary|needed)\b", re.I)
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")


def _sentence_around(line, start, end):
    before = _SENTENCE_END.split(line[:start])[-1]
    after = _SENTENCE_END.split(line[end:])[0]
    return before + line[start:end] + after


def years_asked(lines):
    """Each number of years of experience the description asks, by its low
    end, in the order found, without repeats. A figure counts when its line
    opens with it, or when "experience" stands beside it outside a sentence
    about the company.

    **A figure mid-sentence with no "experience" beside it is not read.** Of
    30 sampled from the 99 measured over three years, about half were not
    requirements (a growth target over the next few years, the company's
    age), and most of the rest sat beside a figure that is read. A posting
    this misses stays in the table, which costs him a look; one it wrongly
    drops he never sees."""
    found = []
    for line in lines:
        if _OPENED.search(line):
            continue
        for m in _FIGURE.finditer(line):
            before, after = line[:m.start()], line[m.end():]
            if _NOT_A_MINIMUM_BEFORE.search(before):
                continue
            if not _LINE_START.match(before):
                beside = _EXPERIENCE_AFTER.search(after) or _EXPERIENCE_BEFORE.search(before)
                sentence = _sentence_around(line, m.start(), m.end())
                if not beside or (_COMPANY_VOICE.search(sentence)
                                  and not _CANDIDATE_VOICE.search(sentence)):
                    continue
            digits, word = m.group("digits"), m.group("word")
            low = int(digits) if digits else _NUMBER_WORDS[word.lower()]
            if low not in found:
                found.append(low)
    return tuple(found)


# ----------------------------------------------------------- requirements
# Initials written with dots lose them first, or a place would end at the
# first one, as a measured place ended at "the U". Any two or three capitals,
# so that no module names a country (ADR-0031, ADR-0057): which initials name
# a closed place is the configuration's to say.
_DOTTED = re.compile(r"\b(?:[A-Z]\.\s?){1,2}[A-Z]\b\.?")
_PLACE = r"(?P<place>[^.;:\n()!?]{1,70})"
# Each a requirement on the candidate, naming a place. A match the place rule
# cannot read as closed decides nothing: being able to work in fast-moving
# environments, or authorised to work in whichever country one applies from,
# were both measured, and both stay unclear.
_REQUIREMENTS = (
    re.compile(r"\b(?:authori[sz]ed|eligible|permitted|entitled|able)\s+to\s+(?:legally\s+)?work"
               r"\s+(?:in|within|for)\s+" + _PLACE, re.I),
    re.compile(r"\b(?:work|employment)\s+(?:authori[sz]ation|eligibility|permit|rights?)"
               r"\s+(?:in|within|for)\s+" + _PLACE, re.I),
    re.compile(r"\bright\s+to\s+work\s+(?:in|within)\s+" + _PLACE, re.I),
    # The word before "citizen" and its kind, and the one before that when it
    # is capitalised, as in a two-word country; the configuration decides
    # whether they name a place, so "valid" or "dual" name nothing.
    re.compile(r"(?P<place>\b(?:(?-i:[A-Z])[\w.]*\s)?[\w.]+)\s+(?:citizen(?:ship|s)?"
               r"|work\s+authori[sz]ation|work\s+permit|persons?|nationals?|nationality)\b",
               re.I),
    re.compile(r"\b(?:must|should|need\s+to|needs\s+to|required\s+to|have\s+to|will\s+need\s+to)"
               r"\s+(?:be\s+)?(?:currently\s+)?(?:physically\s+)?(?:based|located|living|residing"
               r"|reside|live|resident)\s+(?:in|within)\s+" + _PLACE, re.I),
    re.compile(r"\b(?:open|available|restricted|limited)\s+(?:only\s+)?to\s+"
               r"(?:candidates|applicants|residents|people|individuals|those|talent)\s+"
               r"(?:who\s+(?:are|live|reside)\s+)?(?:currently\s+)?"
               r"(?:based\s+|located\s+|living\s+|residing\s+)?(?:in|within|of|from)\s+"
               + _PLACE, re.I),
    re.compile(r"(?P<place>\b[\w.]+(?:\s[\w.]+)?)[\s-]based\s+(?:candidates|applicants)\s+only\b",
               re.I),
)
# A remote role saying the candidate need not be in the US was measured. A
# requirement said not to apply decides nothing. The negation
# must stand against it: in "we don't sponsor visas, so you must be
# authorized to work in the US" the requirement holds.
_NEGATED_BEFORE = re.compile(r"(?:\bnot\b|n['’]t\b|\bno\s+need\b|\bnever\b|\bwithout\b)"
                             r"[^.;,]{0,15}$|\bnon[-\s]?$", re.I)
_NEGATED_PLACE = re.compile(r"\b(?:not|optional|no longer)\b", re.I)
_NEGATED_AFTER = re.compile(r"^[^.;]{0,25}?\b(?:not\s+(?:required|necessary|needed|a\s+requirement)"
                            r"|optional)\b", re.I)


def requirements_named(lines):
    """The place each requirement names, as the description writes it, in
    order, without repeats. Whether a place is closed is the filter chain's
    question, under the operator's configuration."""
    found = []
    for line in lines:
        line = _DOTTED.sub(lambda m: re.sub(r"[.\s]", "", m.group(0)), line)
        for pattern in _REQUIREMENTS:
            for m in pattern.finditer(line):
                place = " ".join(m.group("place").split())
                if (_NEGATED_BEFORE.search(line[:m.start()]) or _NEGATED_PLACE.search(place)
                        or _NEGATED_AFTER.search(line[m.end():]) or place in found):
                    continue
                found.append(place)
    return tuple(found)


# ---------------------------------------------------------------- on site
_WORKED = r"(?:on[- ]?site|in[- ]office|office[- ]based|in[- ]person|hybrid)"
# Each says how this role is worked. "Hybrid" and "on-site" alone are not
# read: hybrid said of search and of cloud, and on-site said of a team, were
# measured.
_ON_SITE = (
    re.compile(r"\b(?:this|the)\s+(?:role|position|job|opportunity)\s+is\s+(?:an?\s+)?"
               r"(?:fully\s+|100%\s+|strictly\s+|entirely\s+)?" + _WORKED + r"\b", re.I),
    re.compile(r"\b" + _WORKED + r"\s+(?:role|position|job|opportunity|employment|basis"
               r"|work(?:ing)?\s+(?:model|arrangement|setup|policy|schedule))\b", re.I),
    re.compile(r"\b(?:\d|one|two|three|four|five)\s+days?\s+(?:a|per|each|every)\s+week\s+"
               r"(?:in|at|from)\s+(?:the|our)\s+(?:[\w-]+\s+){0,2}office\b", re.I),
    re.compile(r"\b(?:location|work(?:place)?(?:\s+(?:type|mode|model|arrangement|setup))?"
               r"|job\s+type|employment\s+type)\s*:\s*" + _WORKED + r"\b", re.I),
    # Full-time on-site work on a night shift, measured on a Lahore posting.
    # An on-site interview round is not the role.
    re.compile(r"\b(?:full[- ]time|fully|100%|strictly|entirely)\s+" + _WORKED
               + r"\b(?!\s+(?:interview|round|visit|meeting|event)s?\b)", re.I),
)
# A remote option anywhere in the description outweighs an on-site phrase,
# as on a measured fully remote role with an office for those who want one.
# Remote said not to be offered is not an option, as on the same Lahore
# posting, which said it required no remote or hybrid work.
_REMOTE_OPTION = re.compile(r"\b(?:remote|remotely|work\s+from\s+home|from\s+home|wfh)\b", re.I)
_NOT_REMOTE = re.compile(r"\b(?:not|no|non)\b(?:[- ]\w+){0,4}?[- ]remote\b"
                         r"|\bremote\s+(?:work\s+)?is\s+not\b", re.I)


def says_on_site(lines):
    """Whether the description says the role is worked on site or hybrid,
    and offers no remote option anywhere."""
    if not any(p.search(line) for line in lines for p in _ON_SITE):
        return False
    return not any(_REMOTE_OPTION.search(_NOT_REMOTE.sub(" ", line)) for line in lines)


def read(parts):
    """The facts one description states, from its parts as the platform
    returned them, HTML or text. None when there is no text to read."""
    lines = lines_of(*(parts or ()))
    if not lines:
        return None
    return Facts(years=years_asked(lines), requirements=requirements_named(lines),
                 on_site=says_on_site(lines))
