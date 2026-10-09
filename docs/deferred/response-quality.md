---
type: deferred
description: Recording what happened after he applied (a reply, an interview, a rejection, an offer), so that sources can one day be judged by how employers respond. Deferred until the operator has used the classification tables for long enough and decides to start.
status: current
---

# What happened after he applied, and which sources answer

**Deferred 2026-10-04 (2026-10-03 UTC)**, on the operator's decision. Not rejected. Not
scheduled.

## What it is

A way to record, for a role he applied to, what came back: a reply, an
interview, a rejection, an offer, or nothing. Over time that answers a question
no count of postings can: which sources lead to employers who respond. It is
one of the things the operator named when he described what makes a source
worth having, alongside how genuine its postings are and how fairly it treats
applicants.

The natural home is the `Stage` field on the `accepted` table, which today has
two choices, shortlisted and applied (`docs/reference/airtable-schema.md`).
Extending it with further choices is his to do in the browser; the choices are
his own distinction and nothing automated reads them.

## Why it is deferred

**He has not used the tables enough yet for the measure to mean anything.** In
his words, 2026-10-04 (2026-10-03 UTC): "i have yet to use the tables properly". A response rate
over a handful of applications is noise, and building the recording before the
habit of classifying exists would add fields nobody fills.

## What is already known, so revisiting does not rediscover it

**A `Stage` changed after day 15 does not reach the store.** The sweep writes
an accepted row to its store with the `Stage` its copy holds on day 15
(ADR-0046's Changes of 2026-09-22, carried forward by ADR-0050). Accepted as it
stands on 2026-09-23, `CHAT_STATE.md` item 95, with the note to revisit when
the accepted-prune tool is built. Replies to an application usually come later
than fifteen days after he classified the row, so under today's design the
response would live only in the `accepted` table.

**The `accepted` copy can leave Airtable.** The operator's `Delete` mark
removes an accepted row once it is saved (D12, ADR-0050). A response recorded
only on that copy would go with it.

So recording the response is cheap, but keeping it is not free: it needs either
the store updated after day 15, or the copy kept until the response is final.
That is the design question revisiting has to answer.

## The trigger

**The operator decides.** The likely moment is when he has applied through the
table to enough roles, across more than one source, that a difference between
sources could show, and wants to know which sources answer.

## What revisiting would have to produce

**The choices, his.** Which outcomes he wants to record, added to `Stage` or to
a field of their own.

**A path to the store that survives the copy leaving.** Either a later `Stage`
reaches the accepted store, which reopens item 95, or the copy is kept until he
marks the outcome final.

**A measure per source, with its count beside it.** Responses over
applications, per source, never stated without how many applications it rests
on.

**And a display that does not change because of it.** A source shown to answer
better may be marked with a star or a note, if and when he asks for one. The
display stays ordered by date alone, latest first (ADR-0057, carrying ADR-0041
as narrowed on 2026-09-25).

## Changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-04 | File created | The operator raised response quality as a measure of a source's value while deciding the end state, and deferred it the same day because he has not yet used the tables enough. Recording it with the item 95 constraint keeps the next session from building a field whose values the sweep would drop |
