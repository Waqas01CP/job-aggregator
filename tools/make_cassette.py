#!/usr/bin/env python3
"""Build a sanitised test cassette from a real board response.

ADR-0017: a committed cassette carries a real board response with every
description field stripped and replaced by a fixed placeholder. ADR-0011 keeps
employer-authored description text out of this repository entirely, and the
pre-commit hook rejects a cassette that still contains one.

Stripping is by field name against a list, not by guessing at content, and the
list errs wide: a field this tool does not know about is left alone, so the
operator reviews the diff. Anything long and prose-shaped that survives should
be added to DESCRIPTION_FIELDS rather than hand-edited out of the cassette.

usage:
  make_cassette.py --source raw_responses/greenhouse-careem.json \\
                   --out tests/cassettes/greenhouse-careem.json [--limit N] [--keep-only-read-fields]
"""

import argparse
import json
import os
import re
import sys

PLACEHOLDER = "STRIPPED"

# Every field known to carry employer-authored prose on the platforms adapted
# so far. Measured from the 2026-09-11 spike's key enumerations.
DESCRIPTION_FIELDS = frozenset({
    "content", "description", "descriptionPlain", "descriptionBody",
    "descriptionBodyPlain", "additional", "additionalPlain", "opening",
    "openingPlain", "job_description", "jobDescription", "excerpt",
    "salaryDescription", "salaryDescriptionPlain", "benefits",
    "key_responsibilities", "skills_knowledge_expertise", "publicDescription",
    "Job_Description", "descriptionHtml", "companyLogo", "hybridDescription",
    "story_text", "comment_text", "_highlightResult", "jobExcerpt", "friendlyNotice",
})

# SmartRecruiters' job ad, 2026-10-17: four named sections under
# `jobAd.sections`, each `{title, text}`. `text` cannot join the list above,
# since it is Lever's title, so a section's text is stripped by where it sits.
SECTIONS = "sections"
# Fields that name a person, stripped whole: SmartRecruiters' `creator`, and
# Hacker News' `author`, the account that posted.
PEOPLE_FIELDS = frozenset({"creator", "author"})

# Hacker News, 2026-10-18: a post is one `text` of HTML, its first line a
# header, company, role and place, read as a title is read, and the rest the
# description. The first line is kept, any address in it replaced, and the
# rest stripped; its replies are other people's comments and go whole. `text`
# cannot join the field list, since it is Lever's title, so a post is known
# by its `type`.
HN_POST = "comment"
# The first line ends at a paragraph or a line break, as the adapter reads it.
PARAGRAPH = re.compile(r"(?i)<p>|<br\s*/?>|\n")
# Algolia's search highlights, and its tags, one of which names the poster.
HIGHLIGHTS = "_highlightResult"
TAGS = "_tags"


def first_line_only(text):
    first = PARAGRAPH.split(text or "", maxsplit=1)[0]
    return EMAIL.sub(PLACEHOLDER, first) + "<p>" + PLACEHOLDER

# The fields the adapters actually read. --keep-only-read-fields trims to these,
# for the one cassette that needs every posting rather than every field.
READ_FIELDS = frozenset({
    "id", "title", "absolute_url", "first_published", "company_name", "location",
    "text", "hostedUrl", "createdAt", "categories",
    "name",  # location.name on Greenhouse, nested under location
})


# An address anywhere in a value, and a Greenhouse custom field whose value
# is a person. Greenhouse boards name hiring managers, approvers and
# recruiters in `metadata`, by name or by email: public in the employer's
# API, and never committed here (2026-10-02, the first cassette fetched with
# `?content=true`).
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Custom fields are kept only where the adapter reads them, the country and
# the workplace (src/adapters/greenhouse.py, a test holds the two lists
# equal); every other value is stripped, so a person named as plain text in a
# field this tool has never seen is stripped too.
KEPT_METADATA = ("country", "work type", "job type")


def sanitise(node):
    """Replace description values, people and addresses wherever they
    appear, at any depth."""
    if isinstance(node, str):
        return PLACEHOLDER if EMAIL.search(node) else node
    if isinstance(node, dict):
        if ("value_type" in node and node.get("value") not in (None, True, False)
                and str(node.get("name") or "").strip().lower() not in KEPT_METADATA):
            node = dict(node, value=PLACEHOLDER)
        if node.get("type") in (HN_POST, "story") and "story_id" in node:
            # A Hacker News post or its thread: the post keeps its first
            # line, the thread its title only, and neither its replies.
            node = dict(node, text=(first_line_only(node["text"]) if node.get("type") == HN_POST
                                    and isinstance(node.get("text"), str) else
                                    PLACEHOLDER if node.get("text") else node.get("text")))
            if node.get("type") == HN_POST:
                node["children"] = []
        out = {}
        for key, value in node.items():
            if key in DESCRIPTION_FIELDS and isinstance(value, str):
                out[key] = PLACEHOLDER
            elif key in PEOPLE_FIELDS or key == HIGHLIGHTS:
                # Algolia's highlights repeat every field, the text and the
                # author included, as an object, which the field list above
                # never meets, so they go whole.
                out[key] = PLACEHOLDER
            elif key == TAGS and isinstance(value, list):
                out[key] = [PLACEHOLDER if str(t).startswith("author_") else t for t in value]
            elif key == SECTIONS and isinstance(value, dict):
                out[key] = {name: dict(section, text=PLACEHOLDER)
                            if isinstance(section, dict) and "text" in section
                            else sanitise(section) for name, section in value.items()}
            elif key == "lists" and isinstance(value, list):
                # Lever's `lists` is prose in {text, content} pairs.
                out[key] = [{"text": item.get("text", ""), "content": PLACEHOLDER}
                            if isinstance(item, dict) else PLACEHOLDER
                            for item in value]
            else:
                out[key] = sanitise(value)
        return out
    if isinstance(node, list):
        return [sanitise(item) for item in node]
    return node


def trim(node):
    if isinstance(node, dict):
        return {k: trim(v) for k, v in node.items() if k in READ_FIELDS}
    if isinstance(node, list):
        return [trim(item) for item in node]
    return node


def postings_of(doc):
    if isinstance(doc, list):
        return doc, None
    if isinstance(doc, dict) and isinstance(doc.get("jobs"), list):
        return doc["jobs"], "jobs"
    # Hacker News, through Algolia: a thread's posts under `children`, a
    # search's stories under `hits`.
    if isinstance(doc, dict) and isinstance(doc.get("children"), list):
        return doc["children"], "children"
    if isinstance(doc, dict) and isinstance(doc.get("hits"), list):
        return doc["hits"], "hits"
    # Manatal's career site pages twenty postings under `results`, beside
    # `count`, `next` and `previous`, which the envelope keeps.
    if isinstance(doc, dict) and isinstance(doc.get("results"), list):
        return doc["results"], "results"
    # SmartRecruiters' list pages postings under `content`, beside
    # `totalFound`, `offset` and `limit`.
    if isinstance(doc, dict) and isinstance(doc.get("content"), list):
        return doc["content"], "content"
    # SmartRecruiters' detail is one posting, its job ad included.
    if isinstance(doc, dict) and "jobAd" in doc:
        return [doc], "single"
    raise SystemExit("unrecognised payload shape: %s" % type(doc).__name__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--keep-only-read-fields", action="store_true")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        doc = json.load(f)

    postings, key = postings_of(doc)
    if args.limit is not None:
        postings = postings[:args.limit]
    postings = sanitise(postings)
    if args.keep_only_read_fields:
        postings = trim(postings)

    if key == "single":
        out_doc = postings[0]
    elif key:
        doc = dict(doc)
        doc[key] = postings
        if "meta" in doc:
            doc["meta"] = {"total": len(postings)}
        # The envelope too: Workable's carries the account's own description,
        # employer prose that ADR-0011 keeps out of this repository. Until
        # 2026-10-08 only the postings were sanitised, and the hook's check
        # passes a file holding STRIPPED anywhere.
        out_doc = sanitise(doc)
    else:
        out_doc = postings

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out_doc, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    text = open(args.out, encoding="utf-8").read()
    leaked = sorted(f for f in DESCRIPTION_FIELDS if '"%s": "' % f in text
                    and '"%s": "%s"' % (f, PLACEHOLDER) not in text)
    print("wrote %s: %d postings, %d bytes" % (args.out, len(postings), len(text)))
    if leaked:
        print("REFUSING: these description fields still carry text: %s" % leaked)
        return 1
    if EMAIL.search(text):
        print("REFUSING: an email address survived sanitising")
        return 1
    if sections_with_text(out_doc):
        print("REFUSING: a job ad section still carries text")
        return 1
    if posts_with_text(out_doc):
        print("REFUSING: a Hacker News post still carries more than its first line")
        return 1
    return 0


def posts_with_text(node):
    """Every Hacker News post that carries more than its first line, or
    replies."""
    found = []
    if isinstance(node, dict):
        if node.get("type") == HN_POST and "story_id" in node:
            text = node.get("text")
            rest = PARAGRAPH.split(text, maxsplit=1)[1:] if isinstance(text, str) else []
            if (rest and rest[0] != PLACEHOLDER) or node.get("children"):
                found.append(node.get("id"))
        for value in node.values():
            found += posts_with_text(value)
    elif isinstance(node, list):
        for item in node:
            found += posts_with_text(item)
    return found


def sections_with_text(node):
    """Every SmartRecruiters section whose text is not the placeholder."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == SECTIONS and isinstance(value, dict):
                found += [name for name, section in value.items()
                          if isinstance(section, dict)
                          and section.get("text") not in (None, "", PLACEHOLDER)]
            else:
                found += sections_with_text(value)
    elif isinstance(node, list):
        for item in node:
            found += sections_with_text(item)
    return found


if __name__ == "__main__":
    sys.exit(main())
