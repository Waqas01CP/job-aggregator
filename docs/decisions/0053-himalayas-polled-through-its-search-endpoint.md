---
status: accepted
topic: fetching
description: Himalayas is polled through its Pakistan search endpoint instead of the browse feed, so a morning reads every eligible posting rather than a third of all postings. The walk's two stop rules, the runaway cap, and the check that keeps a pushed-down predicate honest.
date: 2026-09-26
decision-makers: Waqas Sharif
# consulted:
# informed:
---

# ADR-0053: Himalayas is polled through its search endpoint

## Context and Problem Statement

Himalayas was polled through its browse feed, newest first, stopping when it met a posting already stored. ADR-0048 set that to one poll a day and named its own weakest point: "One poll a day does not lose postings ... **Not measured**, and it is the assumption this record is most exposed on."

It broke exactly there. Measured 2026-09-26: the 500-posting page cap held on three consecutive runs without ever reaching the previous poll, so each run saw about a third of a day. The feed publishes on the order of 1,600 postings a day, inferred from 499 new postings spanning 7.3 hours of publications. At the measured 7% that are open to Pakistan and the 3% the title and seniority rules then keep, roughly two eligible matching roles a day were never fetched, which is about as many as were caught. The operator's expectation was that the location rule would fix this by itself: "the himalayas cap, i think after looking at the above then it will automatically go down but do tell me if it does not". It does not, because a rule acts on what was fetched.

**The endpoint that solves it had been measured and rejected ten days earlier, and the rejection was wrong.** On 2026-09-16 the search endpoint was tested with a `cursor` parameter, which the API documents only for browse. It pages by `page`. That one wrong parameter stood as a recorded rejection for ten days, and re-measuring it on 2026-09-26 is what produced this record.

## Decision Drivers

- The system's binding measure is freshness, and a posting never fetched has no freshness.
- Roughly half the eligible aggregator inventory was being missed, silently.
- ADR-0005 fetches complete board output so that filter defects stay observable, and a server-side predicate hides what it removes.
- Requests are cheap against ADR-0028's budget of 500 a run; the constraint is the page cap, not the ceiling.
- A rule delegated to a third party can drift without anyone noticing.

## Assumptions

- The search endpoint is a snapshot refreshed about once a day, so one morning poll misses nothing. **Measured once**, 2026-09-26 at 16:20Z: its newest posting was still 02:21Z and its total still the morning's 2,965. One reading, not a series, and it is the assumption that replaces the one that just failed, so it is watched the same way and reported weekly rather than asserted. *(Annotated 2026-10-03: **false.** At 16:32Z on 2026-09-30 the search held a posting published at 14:00Z, and its total moves within a day, 2,965 on 09-26 and 2,917 on 09-30. Nothing is lost by the morning-only poll all the same: a week-long read compared with the private seen store found all 420 postings of that week stored, because each walk reads back to its stop mark. What falls is the reason a second poll would be pointless; see ADR-0048.)*
- Every search result is eligible under ADR-0041. **Measured**: 59 of 59 sampled on 2026-09-26, and the first production morning of 2026-09-27 dropped none of its 460 postings for location.
- Eligible volume is on the order of 45 to 92 postings a day. **Measured**, and the two figures disagree: 2,965 results over about a month gives 92 a day, while the 19 dated postings on page one spanned 10.5 hours, which gives about 45. Both are recorded because the disagreement is unexplained.
- A week of eligible postings is about 28 pages. **Measured** 2026-09-26: 25 pages held 6.4 days, 2026-09-19 17:25Z to 2026-09-26 02:21Z.
- A posting's identity is the same on both endpoints. **Measured**: three postings appeared on both first pages on 2026-09-26 with the same `guid` and the same `pubDate`.

## Considered Options

- Keep browse and raise the page cap: about 80 requests for a full day.
- Keep browse and poll on both runs, reversing ADR-0048's morning-only rule.
- Keep browse and accept the loss.
- Poll the search endpoint, filtered to Pakistan, on the morning run.

## Decision Outcome

Chosen option: "poll the search endpoint, filtered to Pakistan, on the morning run". The operator's decision, 2026-09-26: "himalays search: go."

**The board is `himalayas:pakistan`** and it is polled with `country=Pakistan&sort=recent&page=N`, on the morning run only. ADR-0048's cadence is kept, with a new reason: the endpoint behaves as a daily snapshot, so a second poll would read the same data. *(Annotated 2026-10-04: polled on both runs since 2026-10-03; see ADR-0048's Changes.)*

**The walk pages by number and reads every page whole.** The endpoint pins four items at the top, so order is not strictly monotonic and a stop rule that trusted the first old posting it saw would end the walk on page one. The rule reads the page and then decides.

**A walk ends on either of two conditions, and the cap is not one of them.** It stops at the board's own stop mark, which is about four to six pages on an ordinary morning. It stops at a page wholly older than the age limit, which is one second beyond ADR-0052's seven days so that a posting sitting exactly on the limit can never end a walk before it is fetched. **The runaway cap is 40 pages**, raised from 25, and it exists only to bound a walk that has lost its way: a full week is about 28 pages, so a normal walk never reaches it. *(Annotated 2026-10-03: no longer true, and the cap is 80. The feed thickened: 96 and 104 new postings on the mornings of 10-01 and 10-02 and 559 on 10-03, at about 17.7 a page, so a week is about 41 pages, and a test-mode walk on 10-02 stopped at 40 before the age limit. Raised to 80 by the operator on 2026-10-02.)*

**The stop mark is kept per board, not per source.** Every seen entry now records which board first stored it. Entries written before 2026-09-26 carry no board, so the search board's first walk had no mark and read back to the age limit, which is what recovered the eligible postings browse had never reached. This was the operator's decision of 2026-09-26: "the postings browse missed, as you recommended should be fetch so the answer is yes."

**A predicate is pushed down to the source, and that narrows ADR-0005 for this source.** ADR-0005 fetches complete board output precisely so that filter defects stay observable, and `country=Pakistan` removes postings before we can see them. The narrowing is deliberate and bounded: **a predicate may be pushed down to an aggregator only when it duplicates one of our own recorded rules, and only while its agreement with that rule is checked.** Here the predicate duplicates ADR-0041's location rule.

**The agreement check.** One page of the browse feed is read periodically, and every posting on it that the search endpoint would exclude must be a posting ADR-0041 would also exclude. It costs one request. Without it, the location rule has been handed to a third party with no way to learn that it changed its mind, because the contract check fingerprints the shape of fields and not the meaning of a query.

### Consequences

The eligible feed is read in full each morning instead of a third of the whole feed, at four to six requests instead of twenty-five. The first production morning, 2026-09-27, read 23 pages and 460 postings, stopped on the first page past the age limit, stored 361 new postings and kept 31, and treated the 99 that browse had already stored as seen rather than new.

**ADR-0041's location rule now drops nothing from Himalayas, and that is not the rule failing.** Its measured effect of 93 drops in 100 postings was measured on browse. On search the drop count is zero by construction, and a reader comparing the two numbers without this record would conclude the rule had stopped working.

**The contract check reported four field changes on 2026-09-27 that we caused.** Browse returns `nextCursor`; search returns `limit`, `offset` and `totalCount`. The check did its job and the diff is ours, but it has no notion of a contract changed on purpose, so an endpoint change will always surface as an unexplained change until it is re-baselined deliberately. ADR-0036 gains that rule.

The raw layer for this source is no longer complete, and the ineligible postings are not merely unstored but unseen. That is the price of the pushed-down predicate, and the agreement check is the only thing standing in for the observability ADR-0005 bought.

Recovery has a shape now: because only a posting saved in full sets a board's mark under ADR-0051, a failing private store makes each morning re-read to the age limit, about 23 to 28 pages instead of 4 to 6. Measured on 2026-09-28, the Himalayas walk spent 30 requests, which is that recovery and not a fault.

ADR-0028's budget of 500 requests a run is untouched. The morning run's total was 36 with Himalayas and the evening's 11 without, a difference of exactly 25 under browse.

**ADR-0019's removal condition was tested against this change and does not fire.** That record removes Himalayas from the slice if adding it forces a change to the shared HTTP module, the normaliser's row shape, or the filter chain. What changed is the seen store's stop mark, now per board, and the walk's stop rules. Neither is one of the three named components, and it is recorded here so a later reader knows the criterion was checked rather than forgotten.

### Confirmation

**The walk must not stop on a pinned posting.** Feed it a first page whose top four items are older than the mark and confirm the walk continues.

**A posting browse already stored must not be new to search.** Same `guid`, same identity, no second row and no second publication date.

**The age limit must stop a walk, and must not stop it one posting early.** A page wholly older than the limit ends the walk; a posting sitting exactly on seven days does not.

**The snapshot assumption must be measured as a series, not once.** Log the newest posting and the reported total on both runs for a week, and report whether the evening ever differs from the morning. This is the check that failed last time, and it failed because one reading was treated as a property. *(Live only, marked 2026-10-04 under ADR-0049: a property of the live endpoint across days. Answered 2026-10-03: not a snapshot.)*

**The agreement check must be seen disagreeing.** Hand it a browse posting that the search filter excludes and that ADR-0041 would admit, and confirm it reports. A check that only ever sees agreement is asserting nothing.

**Pages per morning must be reported for a week**, so that four to six is measured rather than projected, and so the cap is shown to be unreachable in normal operation. *(Live only, marked 2026-10-04 under ADR-0049: a count over production mornings.)*

## Pros and Cons of the Options

### Raise the browse page cap to a full day

Good, because it changes no endpoint and no record's assumption.
Bad, because it spends about 80 requests to fetch a day of which 93% is ineligible, and it leaves the whole feed's growth as an open-ended cost.

### Poll browse on both runs

Good, because it halves the window each poll must cover.
Bad, because it reverses ADR-0048's cadence, and Himalayas' own reference warns against polling faster than the feed refreshes. It also does not solve the cap: two runs at a third of a day each still miss a third.

### Accept the loss

Good, because it costs nothing and keeps every record as it stands.
Bad, because the loss is about two eligible roles a day against about two caught, and freshness is the system's one binding measure.

## More Information

**No record ever chose browse.** The browse-only choice lived in the adapter's own note and in the spike log of 2026-09-16, and the corpus has no clause reversing it: ADR-0019's Decision Outcome makes no choice of endpoint, and the only mention of browse anywhere in `docs/decisions/` is ADR-0048's instruction for a spike. So this record reverses nothing. What it corrects is a measurement that was never a decision, and the lesson is worth more than the correction: a rejection recorded in a log, on one measurement, with the wrong parameter, stood unchallenged for ten days because nothing in the corpus was answerable for it.

**ADR-0005 is narrowed, not reversed.** Its rule holds for every employer board, where no predicate exists to push down anyway. Its own More Information excluded search APIs and aggregators, and that clause was annotated stale on 2026-09-24 when ADR-0019 brought aggregators into scope, leaving the question open. This record closes it with the bounded exception above.

ADR-0048 owns the cadence, and its failed assumption and the new one are recorded in its Changes. ADR-0041 owns the location rule the predicate duplicates. ADR-0052 owns the seven-day limit the walk's second stop rule is derived from. ADR-0051 owns the save that sets the mark. ADR-0036 owns the contract check that must learn to be re-baselined. ADR-0028 owns the request budget, which this change does not approach.

The operator's decisions: the move to search, 2026-09-26, and the catch-up walk for the postings browse had missed, the same day. The implementing seat measured the endpoint, built both, and proved the first production morning.

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | The runaway cap goes from 40 pages to 80 | A week of the eligible feed no longer fits in 40 pages: about 41 at the rate of 10-01 and 10-02. Only a walk that must read back a week meets the cap, a first walk or recovery after failed saves, and such a walk was stopping short of the age limit. 80 is about two weeks at that rate and 80 requests against the run's 500. The operator's decision |
| 2026-10-03 | Two facts corrected and one recorded. The daily-snapshot assumption is false; the week arithmetic behind the cap is out of date; and in practice a Himalayas posting closes by its own expiry date, which is 60 days after posting on 99 of 100 current postings, so the 15-day and 30-day clocks act first | The snapshot reading was one reading, and the Confirmation's weekly report is what showed it wrong. The closure fact follows from the fix of 2026-10-02: a walk's mark advances daily, so a Himalayas posting's absence is never observed across twelve covering runs. That is ADR-0050's rule working as written, since a run counts only when its read reached the posting's date; the defect before the fix was the code taking a pinned old posting as the walk's reach, which marked 47 open rows closed for a day *(corrected 2026-10-04: 10 were marked on 10-01 and 37 on 10-02, all cleared on 10-03, so the first 10 were closed for two days)* |
| 2026-10-03 | Polled on both runs, by ADR-0048's amendment. The agreement check's twelve-hour wait now usually settles at the next run, the search having trailed at most 6.1 hours; and the agreement check's two private files moved from `outcomes/` to the private store's `agreement/` | The freshness measurement and the operator's yes are in ADR-0048. The two files are not stores, and the reasoning ADR-0055 applies to the clearing list holds for them: a file in `outcomes/` will one day be read as a store |
