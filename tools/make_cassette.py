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
    "Job_Description", "descriptionHtml", "companyLogo",
})

# The fields the adapters actually read. --keep-only-read-fields trims to these,
# for the one cassette that needs every posting rather than every field.
READ_FIELDS = frozenset({
    "id", "title", "absolute_url", "first_published", "company_name", "location",
    "text", "hostedUrl", "createdAt", "categories",
    "name",  # location.name on Greenhouse, nested under location
})


def sanitise(node):
    """Replace description values wherever they appear, at any depth."""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            if key in DESCRIPTION_FIELDS and isinstance(value, str):
                out[key] = PLACEHOLDER
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

    if key:
        doc = dict(doc)
        doc[key] = postings
        if "meta" in doc:
            doc["meta"] = {"total": len(postings)}
        out_doc = doc
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
