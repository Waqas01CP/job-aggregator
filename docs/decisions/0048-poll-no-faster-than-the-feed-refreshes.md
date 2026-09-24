---
status: accepted
topic: fetching
description: A source is polled no faster than its feed refreshes. Himalayas moves to the morning run only. The offset against its refresh stays unset until the refresh moment is measured.
date: 2026-09-19
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0048: A source is polled no faster than its feed refreshes

## Context and Problem Statement

ADR-0006 runs the pipeline twice a day and rests on a measured assumption: ATS boards publish to their APIs at or near the moment a posting goes live. That assumption was confirmed on 2026-09-11 for Greenhouse, whose youngest posting was about 16 minutes old at fetch.

The same record recorded that Himalayas did not behave that way. Its youngest posting was 5.27 hours old, and that was attributed to its own feed staleness rather than to board-side lag.

Himalayas' API reference states the reason: the data is cached and refreshed every 24 hours, and there is no benefit to polling more often. It returns 429 if abused. Read 2026-09-19.

So the second Himalayas poll of each day returns the same cache the first one did. Measured from the four production run logs on the `data` branch at `d883b82`: every run fetched 500 postings, which at the documented maximum of 20 per request is 25 requests, so about 50 requests a day of which about 25 can return nothing new.

There is a second question underneath, and it does not have an answer yet. If the cache refreshes once a day, the best moment to poll is shortly after it refreshes. Nobody knows when that is. The project measured on 2026-09-15 that the response envelope's `updatedAt` is not a cache timestamp but the newest publication date on the page returned, on 8 of 8 observations. The refresh moment is therefore not discoverable from a response.

## Decision Drivers

- A request that cannot return new data is waste against ADR-0028's fetch budget and against a documented rate limit.
- ADR-0006's cadence is sound for sources that publish live, and nothing here disputes it.
- An offset chosen without knowing the refresh moment is a guess wearing a number.

## Assumptions

- Himalayas' cache refreshes every 24 hours. **Sourced** from its API reference, read 2026-09-19. Not measured.
- Twenty-five requests per Himalayas run. **Measured** as 500 postings per run from the four run logs, divided by the documented maximum page size of 20. The 500 is ADR-0028's cap rather than the feed's size, so this is what the cap costs, not what a full walk would cost. *(Annotated 2026-09-24, wrong when written: the 500 postings are the adapter's page cap, `MAX_PAGES = 25` in `src/run.py` times `PAGE_SIZE = 20` in `src/adapters/himalayas.py`. ADR-0028's 500 caps requests, not postings (`DEFAULT_BUDGET` in `src/http_client.py`). The conclusion stands: this is what a cap costs, not a full walk.)*
- One poll a day does not lose postings. Anything published between polls is still in the feed at the next one, and ADR-0007 makes a gap non-destructive. **Not measured**, and it is the assumption this record is most exposed on.

## Considered Options

- Leave Himalayas on both runs.
- Poll Himalayas on one run a day, at the existing morning slot.
- Poll Himalayas once a day at a fixed offset after its refresh.

## Decision Outcome

Chosen option: "poll Himalayas on one run a day, at the existing morning slot".

**We will poll a source no faster than its own documented refresh interval.** Where a source states one, that interval is the ceiling on how often the pipeline asks it. This is a property of the source, configured per source under ADR-0031, not a property of the run.

**We will poll Himalayas on the morning run only.** The evening run skips it and says so in the run log, so a skipped source is visible rather than absent.

**We will not set an offset against the refresh until the refresh moment is measured.** A spike polls the browse endpoint hourly for two days and records when the returned set changes. Only then is an offset chosen, and it is chosen to poll shortly **after** a refresh. Polling shortly before one returns the most stale data the cache ever holds, which is the opposite of the intent.

**ADR-0006's cadence is unchanged.** The pipeline still runs twice a day. This record governs which sources a given run asks, not how often the run happens.

### Consequences

Himalayas' request cost halves, from about 50 requests a day to about 25, against both ADR-0028's budget and a documented rate limit.

Worst-case discovery latency for Himalayas rises from 12 hours to 24, and its feed is already up to 24 hours stale at the source, so the poll interval was never the binding constraint there. Measure A is defined over the pipeline as a whole and will now mix a 12-hour source class with a 24-hour one, which anyone reading that figure needs to know.

A source can be skipped on a run, which is a new state in the run log and a new thing a reader must not mistake for a failure.

The best polling moment stays unknown until the spike runs. Until then the morning slot is chosen for continuity, not for fit.

### Confirmation

After one day: the morning run log shows Himalayas fetched, the evening run log shows it skipped with a reason, and the evening run's request count falls by about 25.

**The check that can fail:** compare the identities Himalayas returns on the morning poll against those it returned the previous morning, for a week. If postings appear that are older than the previous poll and were absent from it, the one-poll-a-day assumption is losing rows and this record is wrong.

## Pros and Cons of the Options

### Leave Himalayas on both runs

Good, because it is the current behaviour and needs no change.
Bad, because the documentation states the second poll cannot return new data, and it spends a quarter of the day's requests to confirm that.

### Once a day at a measured offset

Good, because it is the arrangement that actually minimises staleness.
Bad, because the offset cannot be chosen today: the refresh moment is not in the response, measured 2026-09-15. It becomes available once the spike runs, and this record names the spike.

## More Information

Extends ADR-0006, which carries a Changes row pointing here. ADR-0028 owns the fetch budget this reduces. ADR-0031 owns the per-source configuration the interval lives in. ADR-0015 owns Measure A, whose interpretation this changes.

The `updatedAt` finding is in `docs/research/0003-job-source-survey.md`, in its corrections table dated 2026-09-15.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-09-24 | The attribution of the 500 postings annotated as wrong | They are the adapter's page cap, 25 pages of 20, not ADR-0028's request cap. Annotated by the implementing seat under ADR-RULES, which allows a stale or wrong fact to be annotated unasked; the Decision Outcome is untouched. Found by the corpus audit of 2026-09-23 |
