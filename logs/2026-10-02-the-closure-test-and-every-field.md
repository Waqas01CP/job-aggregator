---
type: log
description: The first live checks of the fourth audit's fixes; a defect found in the closure test that had marked 47 open Himalayas rows closed, fixed before the next morning; the Himalayas logic checked against the live search; every field and parameter of the three sources measured over the saved full postings; and the operator's answers on the audit's questions.
status: current
---

# The closure test, and every field, 2026-10-02 UTC

Previous log: `2026-10-01-the-fourth-audits-corrections.md`.

| Header | Value |
|---|---|
| Date | 2026-10-02 UTC. The operator wrote at 15:48 his time, 10:48Z |
| Model | claude-opus-5-5 |
| HEAD at start | `8bd84a0`, level with `origin/main` |
| Mode | **Mutating.** Airtable: 1 connector read. GitHub's public API: 2 reads. Himalayas: about 25 requests, the search, browse, and six job pages that answered 403. The private repository's full branch cloned read-only into the scratchpad. Provider documentation read for Himalayas, Greenhouse and Lever |

**Tags.** `[VERIFIED]` exercised and observed this session. `[INFERRED]` reasoned, not run. `[outside]` from outside this repository.

## What the operator asked

1. His answers to the four questions of 2026-10-01:
   - on the clearing tool's exit code: green only if the drawback is small or none;
   - on rejection copies: what a kept copy would be for, and where it lives;
   - on the how-to: correct the sentence;
   - on the local `data` branch: he made it, and it may go.
2. Before he sends the architecture brief, check the day's contract check and this morning's run.
3. Recheck the Himalayas logic: that it keeps every posting he can apply to, the gray zone of postings with no location included.
4. Every field each source gives, experience above all, with each API's parameters, logged so it can be repeated as sources are added.

## His answers, acted on

- **The how-to** `[VERIFIED]`: the paragraph now says the name is in the history since `fe07242` and harmless, with a Changes row.
- **The local `data` branch** `[VERIFIED]`: deleted. It was identical to `origin/data`, `92d2103`, so nothing was lost.
- **The exit code and the rejection copies**: their consequences are set out for him below. Neither record nor configuration changed; he decides.

### The clearing tool's exit code, consequences

**No case loses data.** The tool writes stores and deletes nothing; deletion is the sweep's, after read-back.

| Case | What happens | Green, as now | Red |
|---|---|---|---|
| Refused confirm, no dry run on file | nothing written | a warning names the refusal on the run page | the run turns red and GitHub emails him |
| Fails before writing | nothing written | the same | the same |
| Fails part-way | the rows stored so far are removed by the next sweep, as asked; the rest stay | **until today the line said only "FAILED"**: a partial clear could look like nothing happened | red, with the same gap |

**The one real drawback of green is closed now.** A failed clear reports how many rows it stored before failing, on the line he reads: "n row(s) stored before it failed, which the next sweep removes; confirm again to finish the rest". Confirming again finishes it, the stored rows counted as already leaving. Test and mutation: "a failed clear forgets what it stored".

**What red would cost:** nothing in data, since the push comes first. It costs a failed-run email for what is usually his own forgotten dry run, sent through the same channel as a real failure. By his rule, small or none means green. I read the remaining drawback as none, since he dispatched the run and is reading it. The record stays "not yet put to the operator" until he says.

### A rejection copy when `Jobs` is cleared

**The copy** is the row in `rejected-not-a-fit` or `rejected-poor-filtering` in Airtable, carrying his reason. Before anything is deleted, its classification and reason are written to the outcome store:
- `outcomes/rejected_*.json` on `data` for an employer row;
- the same files in the private repository for a Himalayas row.

So a kept copy adds nothing to what is saved. It only keeps the row visible in that table until its own fifteen days end.

- **Its one use:** seeing several rows with one reason together in `rejected-poor-filtering`, the filter's defect log, while they are on screen. The store keeps that cluster readable for good.
- **Keeping it** means the tool marks a `Jobs` clear differently from a table clear, and the sweep reads the difference. A small change.
- **The seat's view:** leave it as it is. The dry run already counts these rows before he confirms.

## The live checks he asked for

**The contract check of 2026-10-01** `[VERIFIED]`, run 36871204857 at 13:46Z on `8bd84a0`, from its log on `data`:
- Greenhouse, Lever and Himalayas all read unchanged;
- each stored shape now carries `since: 2026-10-01`.

That is the fourth audit's F5 fix live: a shape with no acceptance date was dated on its first read, and nothing was excused. The check of 2026-10-02 had not run at 11:10Z; its runs have started between 11:42Z and 14:21Z.

**The fetch of 2026-10-01T18:44Z** `[VERIFIED]`: healthy.
- 808 fetched, 7 kept;
- 84 rows sent in 9 calls;
- no failure; Himalayas skipped, as every evening.

**The fetch of 2026-10-02T04:22Z** `[VERIFIED]`, run 36964231534 on `8bd84a0`:
- 948 fetched, 18 kept, no failure, 19 requests;
- Himalayas walked 7 pages to its mark, not capped;
- **the agreement check compared all 20 browse postings:** the location rule excludes all 20 and the search returned none of them, so they agree on every one. Before the fix it compared 0 of 20. No posting waited, so the waiting path has not yet fired live.

**And the sweep marked 37 rows Closed.** It had marked 10 the morning before, and none on any earlier morning. That led to the next section.

## A defect: the closure test marked open Himalayas rows closed

**Found** `[VERIFIED]`, one read of `Jobs` through the connector: 47 rows carry `Closed`, 10 dated 10-01 and 37 dated 10-02.
- **All 47 are Himalayas rows** first seen on 09-27 or 09-28, by the catch-up and recovery walks.
- **None is an employer-board row.**

**Cause** `[VERIFIED]`. For a paginated board, `src/closure.py` counted a run's absence only when "the oldest posting it fetched is no newer than this one". The run log records that oldest posting as `oldest_published`. On every Himalayas walk from 09-27 to 10-02 it read `2026-09-16T06:15:55Z`, including the walk of 09-29, which read one page. That is a pinned posting: ADR-0053 records that the search pins old postings on page one. So the test believed every walk reached back to 09-16. Every Himalayas row not seen on four consecutive mornings was marked closed, though the daily walks read only the newest 1 to 7 pages.

**The rows were open** `[VERIFIED]`: six of eight looked up through the search API, `q` with the title and `country=Pakistan`, are listed today. The other two were not found by those words, which proves nothing either way. Their job pages answered 403 to a script, so they could not be read directly.

**What it cost, and would have:**
- **since 10-01 and 10-02,** the 47 rows were hidden from his `To review` view, which filters out closed rows;
- **from about 10-16,** fifteen days after marking, the sweep would have retired them as `closed`, which never returns;
- **every Himalayas row from now on** would have been marked about four mornings after it was last seen.

**Why no check caught it.**
- **The unit tests modelled a walk's reach as its oldest posting**, with no pinned posting in the data. The check could not fail on the live shape.
- **The fourth audit closed before the first mark appeared on 10-01.** For the next audit.

**Fixed.**
- **`_fetch_pages` now records what the walk covered**: `walk: {stopped_by, mark}`, where `stopped_by` is `mark`, `end` or `cap`.
- **`closure.covered()` counts a paginated run only when the walk covered the posting's date:**
  - stopped at its mark: the posting is newer than the mark;
  - read to the feed's end: any posting;
  - capped: none.
- **A log without the record counts for nothing.** So the 47 marks clear on the next daily sweep through the existing "a mark whose posting came back" path, before any is retired `[INFERRED]` from the code. The next morning's run is the check.

**The consequence, stated in `src/closure.py`:** a Himalayas posting now closes in practice by its `expiryDate`, given on every posting. The mark advances each morning, so a walk covers a posting's date on about one morning after it was last seen, never four in a row. Absence on a feed read only to its newest postings is not evidence. The thirty-day clock still bounds an unreviewed row.

**Tests.**
- The regression case carries the pinned 2026-09-16 posting as the live logs do.
- New cases: a capped walk never counts, a whole-feed walk counts, and a log without the record never counts.
- The run's walk record is asserted for all three endings.

**Mutations,** in `tools/mutations/2026-10-02-closure-and-clearing.json`:
- "a paginated walk's reach is its oldest posting", which is the old behaviour;
- "a capped walk counts as reaching back";
- "a log with no walk record counts";
- "a whole-feed walk proves nothing";
- "the walk records no reach";
- with the exit-code change, "a failed clear forgets what it stored".

Brief 7's "a paginated run counts without reaching the posting" was stale against the new line and is re-expressed in place. Results under Verification.

## The Himalayas logic, checked

**His understanding is right, and so is the gray zone.**
- The search asks Himalayas only for postings open to someone in Pakistan, so "USA only" and "Remote, Germany" are never fetched.
- The pipeline's own location rule (D13) runs again on what comes back.

**What the search returns** `[VERIFIED]`, two live pages, 40 postings:
- 35 restrict no location at all, which the site shows as "open to candidates from all countries";
- 5 list Pakistan among their countries;
- none is restricted to other countries only.

Over the 809 postings saved since 09-26 `[VERIFIED]`, 722 carry no restriction.

**What the search leaves out** `[VERIFIED]`, three browse pages, 60 postings: 59 restrict to places other than Pakistan. The one with no restriction was returned by the Pakistan search.

**No location is in, at both layers** `[VERIFIED]`:
- the search returns unrestricted postings;
- the adapter turns an empty or missing list into no location;
- the rule keeps a posting with no location, since nothing says it is closed to him.

Probed with the real code:
- **kept:** `None`, empty, "Pakistan", "Pakistan, United States", "Asia";
- **dropped:** "United States", "Germany".

**On-site Karachi on Himalayas:** the site lists remote roles; its restrictions say where a remote worker may live. A Karachi office role is not expected there.

**Gaps and loopholes, as they stand:**
1. **The closure defect above**: the one that was hiding jobs. Fixed.
2. **The search's country filter is Himalayas'.** If it ever drops a posting he can take, the agreement check catches it: today it compared 20 of 20, where it had compared 0.
3. **Seniority comes from the title only.** Himalayas labels 35 of the 67 postings the chain keeps Senior or above (below). These are senior roles let in, not jobs missed; whether to use the label is his decision.
4. **The title pool is the largest filter:** 121 of the 139 Himalayas postings this morning were dropped on title. A role named outside the pool is missed by design, and the drop log is how the pool grows.
5. **Time zones are not filtered**, by his ruling. Every Himalayas posting carries a hiring-time-zone list.
6. **A posting first seen more than a week after its publication date is dropped** (D14), as he set.

## Every field, every parameter

Recorded in full in `docs/reference/platform-fields.md`, re-measured over the 1,695 postings saved whole since 2026-09-26: 823 Greenhouse, 63 Lever, 809 Himalayas `[VERIFIED]`.
- **No source gives years of experience as a field.** A number of years appears in the description text on 53% of Greenhouse postings, 67% of Lever's and 50% of Himalayas'. That counts phrases like "3+ years", so it is an upper bound.
- **Himalayas states a level on every posting**, `seniority`, which the pipeline does not read: Mid-level 344, Senior 285, Entry-level 84, Manager 84, Director 44, Executive 28.
- **Put through the real adapter and chain at the moment each was saved,** 67 of the 809 are kept, and 35 of those are labelled Senior or above.
- **Lever has a `level` category, and neither board sets it.** Greenhouse has none, beyond one board's custom grade code.
- **The Himalayas page he described, mapped to the API:**
  - apply before is `expiryDate`, posted on `pubDate`, job type `employmentType`;
  - experience level is `seniority`, location requirements `locationRestrictions`;
  - hiring timezones are `timezoneRestrictions`, job categories `categories` and `parentCategories`;
  - **skills are not in the API response at all.**
- **Each API's parameters** `[outside]`, from the providers' documentation:
  - **Greenhouse:** `content`, `questions` and `pay_transparency`; the last two need one request per posting;
  - **Lever:** `mode`, `skip`, `limit`, and filters `location`, `commitment`, `team`, `department`, `level`, plus `group`;
  - **Himalayas search:** `q`, `country`, `worldwide`, `exclude_worldwide`, `seniority`, `employment_type`, `company`, `timezone`, `sort`, `page`.
- **Himalayas' documentation disagrees with its response:**
  - it says data is cached every 24 hours, contradicted on 2026-09-30;
  - it names three fields differently from the response;
  - it omits `seniority`.

**The script that measured it**, run against a read-only clone of the private full branch. It prints field names, types, rates and category names, nothing that identifies a posting:

```python
"""Every field each source returns, measured over the private full postings.
Arguments: repo root, full clone directory."""
import collections, glob, json, os, re, sys

root, full = sys.argv[1], sys.argv[2]
ADAPTERS = {s: open(os.path.join(root, "src", "adapters", s + ".py"), encoding="utf-8").read()
            for s in ("greenhouse", "lever", "himalayas")}
postings = {}
for path in sorted(glob.glob(os.path.join(full, "full", "*.json"))):
    for rec in json.load(open(path, encoding="utf-8")):
        postings.setdefault(rec["identity"], rec)
by_source = collections.defaultdict(list)
for rec in postings.values():
    by_source[rec["source"]].append(rec["posting"])

def kind(v):
    if v is None: return "null"
    if isinstance(v, bool): return "bool"
    if isinstance(v, (int, float)): return "number"
    if isinstance(v, str): return "string"
    return "list" if isinstance(v, list) else "object"

def filled(v):
    return v not in (None, "", [], {})

# Whitespace is collapsed first, so each optional space is bounded. A first
# version with adjacent unbounded runs backtracked for minutes on long HTML.
YEARS = re.compile(r"\b\d{1,2}\+?(?:\s?(?:-|to|–)\s?\d{1,2})?\+?\s?(?:years?|yrs?)\b", re.I)
TAGS = re.compile(r"<[^>]+>")
TEXT = {"greenhouse": ("content",), "lever": ("descriptionPlain", "description", "additionalPlain", "lists"),
        "himalayas": ("description", "excerpt")}

for source, rows in sorted(by_source.items()):
    stats = collections.defaultdict(lambda: [collections.Counter(), 0])
    for p in rows:
        for k, v in p.items():
            stats[k][0][kind(v)] += 1; stats[k][1] += filled(v)
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    stats[k + "." + k2][0][kind(v2)] += 1; stats[k + "." + k2][1] += filled(v2)
    print(source, len(rows))
    for k in sorted(stats, key=lambda k: (-stats[k][1], k)):
        leaf = k.split(".")[-1]
        read = ('"%s"' % leaf) in ADAPTERS[source] or ("'%s'" % leaf) in ADAPTERS[source]
        print("  %-34s %-22s %5.1f%%  %s" % (k, "/".join(sorted(stats[k][0])),
                                            100.0 * stats[k][1] / len(rows), "read" if read else "-"))
    years = 0
    for p in rows:
        text = " ".join(p[f] if isinstance(p[f], str) else json.dumps(p[f]) for f in TEXT[source] if p.get(f))
        years += bool(YEARS.search(" ".join(TAGS.sub(" ", text.replace("&lt;", "<").replace("&gt;", ">")).split())))
    print("  description states a number of years:", years)
```

**For a new source,** `docs/reference/platform-fields.md` has the procedure: save the responses whole, run this count, read the provider's documentation, and add a section.

## Verification

All `[VERIFIED]` on this commit's code; each clone's `src`, `tests` and `tools` were compared with the tree and found identical.

- **Suite:** 728 tests pass on Python 3.12, and on 3.11 under `-W error::ResourceWarning`.
- **Mutations:** 7 of 7 caught in two scratch clones, each by the test built for it:
  - the five closure mutations and Brief 7's re-expressed one, 10:59Z to about 11:15Z;
  - "a failed clear forgets what it stored", in a second clone holding the current code.
  Both restored their files and passed the suite again, and no Python process was left.
- **Stale finds:** 0 of 392.
- **Privacy:** the outgoing diff, this log and the new mutation file hold no Himalayas URL or company, no Airtable ID, no token and no wikilink. The private repository's name appears only as unchanged context beside the how-to's edit.
- **The sweep test of the live case** models the 47: a Himalayas row marked closed, with logs of the old shape whose oldest posting is the pinned 2026-09-16 one. The mark clears.

## Open

- **For the operator:**
  - whether a refused clear stays green, now that a partial clear reports itself;
  - whether a `Jobs` clear keeps rejection copies;
  - whether Himalayas' `seniority` label should be read.
- **For the next morning's run:**
  - the 47 marks clear;
  - no Himalayas row is newly marked closed except by expiry.
- **For the next audit:** the closure defect, which no audit had a chance to see.
