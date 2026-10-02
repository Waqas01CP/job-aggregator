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

## Later the same day: his decisions, the level rule, and the two employer platforms

**His answers** [VERIFIED as recorded]:
- **The clearing tool's exit code: green.** Recorded in `CLAUDE.md`.
- **Mixed levels:** his option A.
- **Job types:** keep interns, contract, part-time, temporary and volunteer roles, on every source: volunteering "might be a good opportunity and can become a stepping stone".
- **The level rule:** build it.
- **Closure:** he confirmed that his apply-before idea and the fix already pushed are the same. On 99 of 100 current Himalayas postings, apply-before is exactly 60 days after posting [VERIFIED], so in practice the 15-day and 30-day clocks act first.
- **Rejection copies:** stay as built. A rejection copy and its row leave together on the normal sweep, so only `accepted` copies outlive their row, and the clearing tool matches that.
- **Time zones:** not filtered; he works US hours.

### The level rule, built

- **Read from the response, never asked of the search.** Himalayas' `seniority` is read into a new row field, `stated_levels`.
- **Option A:** `rule_level` keeps a posting when any level it states is in `stated_levels_admitted`, which is Entry-level and Mid-level in `config/eligibility.json`.
- **No level is kept.** A posting stating none is kept: every employer board, and every row stored before today.
- **The title rule still runs.** The new rule sits after it in the chain.
- **The contract check** now watches `seniority`, and the re-baseline entry of 2026-10-02 records that as our change.
- **Measured** [VERIFIED], the real adapter and chain over the 809 saved Himalayas postings: 67 kept before, 34 after; the level rule takes 33.
- **What it does not reach** [INFERRED from the code]: rows stored before today carry no level, so the senior-labelled Himalayas rows already in `Jobs` stay until he classifies them or the thirty-day clock takes them. Giving them their levels would mean rewriting stored rows, which the append-only layers forbid; it was not done.
- **Tests:** the rule's cases, read from configuration rather than literals; the adapter and the row; the configuration refusing an empty list; the re-baseline entry.
- **Mutations:** `tools/mutations/2026-10-02-level-rule.json`, 6 of 6 caught in a scratch clone of this code, each by the test built for it [VERIFIED].
- **Suite:** 737 tests on Python 3.12, and on 3.11 under `-W error::ResourceWarning` [VERIFIED]. 0 of 398 finds stale.

### Greenhouse and Lever, field by field

Answered in `docs/reference/platform-fields.md`, measured over the 823 Greenhouse and 63 Lever postings saved whole [VERIFIED].

**Greenhouse:**
- `application_deadline` is already used, as the expiry, and is empty on all 823.
- `internal_job_id` is the employer's job behind several city postings: 499 distinct, 380 shared. `requisition_id` is the employer's code: 484 distinct, 407 shared.
- `updated_at` is bulk-stamped, not a freshness signal.
- `metadata` is each employer's custom fields. Three of them carry meaning: one board's `Work Type`, another's `Job Type`, and Careem's `Country`. A fourth is one board's own grade code. Five fields name people, and no file here records them.

**Lever:**
- `lists` holds the requirements, and with them the years: 50 of 63 postings state years there, against 4 in `description`.
- `opening` is the introduction, and `additional` the closing text.

**Missed jobs: none found.**
- **Greenhouse:** of the location-dropped postings whose description mentions Pakistan, "anywhere" or "worldwide remote", 3 pass every other rule, all correct drops.
- **Lever:** no dropped posting lists Pakistan among its locations.

**Jobs that should not be there: 59.**
- **Where the location text is a city the rule cannot place,** the posting is kept as unclear. Lever's `country` places 40 of them outside Pakistan: 19 on-site United States jobs, 3 on-site European ones, and 18 remote ones in the United States, the Philippines, India, Colombia and Britain.
- **Greenhouse's `offices` places 19 more** outside Pakistan, mostly Saudi cities.
- **Not one of the 59** names a Pakistani place anywhere, or has a description mentioning Pakistan, "anywhere" or "worldwide".

**Proposed, not built**, since it changes what reaches his table: where every part of the location text is unclear, let the source's structured place decide, and only ever to close.

**Also found, for him:** one board's "Lahore, Punjab, Pakistan" postings say "onsite" in the description on 6 of 11, which the location field does not say. D13 drops on-site roles outside Karachi. Reading description text for location is a further proposal, and a riskier one.

## The evening: his test dry run, two false alarms, and the structured place built

**His words, 2026-10-02 evening:**
- the job types stay, on every source;
- the custom fields should be used where useful;
- "if the job is remote but is us only then it should not be shown";
- both proposals accepted;
- "high time that we use the description", for experience, on-site work, and any requirement that stops him applying even when a posting passes every other check.

### His test-mode dry run, run 37050567807 at 18:54Z [VERIFIED]

From its log on `data-test`: on `Jobs test` at 30 days it would remove 19 rows, 18 unreviewed, with one poor-filtering copy leaving with its row. It wrote nothing.

### The warning "the search has not returned 1 posting" was false [VERIFIED]

- **It appeared on all three of the day's runs:** the morning run, whose log reads 0 disagreements, and the evening run, which never polls Himalayas.
- **Cause:** the workflow runs the test suite before fetching, and GitHub turns any warning command a step prints into an annotation. The agreement check's fitness test printed one. No disagreement has happened.
- **Fixed twice over:**
  - that test now captures and asserts its output;
  - both workflows stop workflow commands for the length of the test step, with a one-off token, and resume after, exiting with the suite's own status.
- **Tests:** a workflow test holds both. Mutation: "the tests run with workflow commands live".

### The cap warning was real, and a week no longer fits in 40 pages [VERIFIED]

- **His test-mode walk** read 40 pages, 707 postings, and stopped at the cap before the age limit. The test branch had no recent mark, so it read back toward a week.
- **The scheduled walks** read 6 and 7 pages on 10-01 and 10-02, about 100 new postings a day.
- **What this means:** a week of the Pakistan search is more than 40 pages now. ADR-0053's "a full week is about 28 pages, so a normal walk never reaches it" no longer holds. Only a walk that must read back a week meets the cap: a first walk, or recovery after failed saves.
- **Proposed to him:** raise the cap to 80, about two weeks at today's rate and 80 requests against the run's 500. Not changed, since ADR-0053's number is his.

### The agreement check measured reach by the pinned posting too [VERIFIED from the code]

`agreement()` judged whether a walk reached a waiting posting by the walk's oldest posting, the same mistake as the closure test.
- **Exposure:** latent on daily walks, whose browse postings are newer than the mark.
- **Now:** it uses the walk's record, through `closure.covered`.
- **The waiting list is bounded:** a posting older than the age limit leaves the list, counted as given up.
- **Tests:** the case of a walk stopped at a newer mark, built with a saved mark this time, and the give-up.
- **Mutations:** "a walk that never reached a waiting posting's date judges it", re-expressed, and "a waiting posting never gives up".

### The runner image pinned

GitHub's notice on every run: `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19. The workflows pin Python 3.11, untested on the new image.
- **Both workflows now run on `ubuntu-24.04`.** A move is a decision, made after a test run on the new image.
- **Test:** the image is pinned. Mutation: "the runner follows ubuntu-latest".

### The dispatch form says what it means

His questions were whether the days are hours, and whether test mode is the `Jobs test` table. The four inputs now say:
- days, not hours, counted from the publication date or from Classified;
- test mode is the test tables;
- a confirm repeats the dry run's table, days and mode within 48 hours;
- the rows leave at the next run's sweep.

### The structured place and the stated workplace, built

**Rows and adapters.** Two new row fields, `places` and `workplace`, filled by the adapters:
- **Lever:** `country` and `workplaceType`;
- **Greenhouse:** each office's `location`, a `Country` custom field, and a `Work Type` or `Job Type` custom field.

**`rule_location`.** Where every part of the text is unclear, the structured places decide, and only to close:
- an ISO code is the home country's (`home_country_codes`, `PK`) or another's;
- any other place is read like text.

**A stated on-site or hybrid workplace** marks a Pakistani city other than Karachi as on site, under D13.

**My error in the first build:** a stated remote workplace was placed beside the city, "Manila (remote)", and read as open. 19 remote Lever postings in other countries stayed kept. Caught by the measurement, not by a test; fixed, and now a test and a mutation.

**Measured with the code** over the saved postings [VERIFIED]:
- **67 kept postings now dropped,** none newly kept: Lever 42, all by country; Greenhouse 25, 19 by office or country and 6 by a stated hybrid workplace;
- **the only ones naming Pakistan** are those 6, a board's "Islamabad, Pakistan" roles whose field says Hybrid, which D13 drops;
- **no newly dropped posting's description** mentions "anywhere" or "worldwide".

**The contract check:**
- **it now steps into lists,** so `offices.location`, `metadata.name` and `metadata.value` are fingerprinted, where they would always have read absent;
- **re-baseline entries** record the new Greenhouse and Lever fields as ours;
- **a new fixture,** `greenhouse-careem-content.json`, fetched with `?content=true` as the run requests;
- **the path test** runs against it.

### People's addresses in a committed fixture

- **Found:** `tests/cassettes/greenhouse-careem.json`, committed in `9d8f9c1`, carried 19 hiring managers' addresses in Careem's custom fields. They are public in Careem's API.
- **The cassette tool** now keeps custom-field values only where the adapter reads them, the country and the workplace, and strips any address anywhere. A test holds its kept list equal to the adapter's.
- **Both fixtures are clean now.**
- **The addresses remain in git history.** Removing them needs a rewritten, force-pushed history, which D10 forbids without him. Flagged to him, not done.

### The description: measured, designed, waiting on his numbers

Over the saved postings that pass every rule but age [VERIFIED]:
- **Years** are stated on about a third. Greenhouse: of 15, 3 ask 5 or more and 1 asks 3. Himalayas: of 35, 1 asks 5 or more, 6 ask 3, and 4 ask 2 or fewer. The sampled matches read right.
- **Work authorisation** is rare here. The one match, "visa sponsorship is not available", sat on a fully remote role: no stop for him.
- **On-site wording** on postings in Pakistani cities other than Karachi: 2 of 6. One is real, "Onsite job with offices in our Thokar office"; one is false, "hybrid/vector search".

**Proposed design:**
- **Read the description once, at fetch,** where it is in hand. Store only what is derived, as row fields: the least years asked, a stated authorisation or residence requirement and where, and a stated on-site arrangement. The text never leaves the private full branch.
- **Name each rule:**
  - experience, the rule built and switched off, with his threshold;
  - authorisation;
  - on site, fed into D13 as the stated workplace is.
- **Phrase-based and deterministic,** within ADR-0010. Each pattern is measured over every saved description before it is switched on.

**His to answer:**
1. The most years a posting may ask and still be shown.
2. Whether "preferred" counts like "required".
3. Which requirements stop him: work authorisation, citizenship, clearance, residence.

**The architecture chat's:** recording it, against ADR-0011, ADR-0016 and ADR-0051.

### Verification of the evening's work

All `[VERIFIED]` on this commit's code; each clone's `src`, `tests`, `tools`, `config` and `.github` were compared with the tree and found identical.

- **Suite:** 754 tests pass on Python 3.12, and on 3.11 under `-W error::ResourceWarning`. A run of the whole suite prints no workflow command.
- **Mutations, first run:** 18 of 19 caught, each by the test built for it. The run covered the new structured-place, agreement and workflow files, and the seven re-expressed.
- **The survivor, "the home country's code reads as closed":** its test used "Lahore", which the text admits before the source's place is asked, so the test could not fail. Rebuilt on text the rule cannot place, and re-run in a fresh clone: caught, by that test. 19 of 19.
- **Stale finds:** 0 of 410.
- **Privacy:** both Greenhouse fixtures carry no address, and the outgoing diff holds no Himalayas URL, no Airtable ID and no token.
