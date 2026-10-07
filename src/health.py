"""The pipeline's health, as rows the operator opens in Airtable's `Health`.

ADR-0036 deferred a contract finding's Airtable row until a writer existed,
and ADR-0059 requires it before version 1 is done, with every failure
reaching Airtable. The operator chose on 2026-10-07 one table for both,
"general health", "only if the cost is not a lot". So a row is written only
when something is wrong or new, never for a healthy run:

- **from the contract check:** each changed field, each change of ours it
  re-baselined, a board it could not reach, a platform whose check failed,
  and a platform's first baseline;
- **from a fetch run:** a board that failed, errored, could not be parsed or
  was not reached, a run stopped early, and a projection, sweep, private
  store, clearing tool, closure test or health write that failed.

**The fetch run writes them all**, the contract check's included, from the
logs on the data branch. The contract workflow so holds no Airtable secret,
and every call is counted where the month's count already looks: a finding
reaches `Health` at the next fetch run, a few hours after its check.

**Each event is sent once.** Its key goes into the run log as sent, and a
later run sends only the events of the last week that no run has recorded:
one that failed to send, Airtable being the thing that failed, is sent by
the next run that reaches it. A row the operator deletes is not sent again.

**Nothing from a posting.** A row carries a platform, a board, a field name,
shapes and the failure text the run log already holds, which is public.
"""

from datetime import datetime, timedelta, timezone

from .projection import airtable_datetime

HEALTH_FIELDS = ("Key", "When", "Source", "Subject", "Status", "Detail")
KEY_FIELD = "Key"
# Where a run log keeps this step's counters and what it sent. The month's
# Airtable count sums its calls with the projection's and the sweep's.
LOG_KEY = "health"
# How far back an unsent event is still sent. A week of scheduled runs is
# fourteen chances.
WINDOW_DAYS = 7

CONTRACT = "contract check"
FETCH = "fetch run"
# A contract status that is a row. "unchanged" is the healthy case, and "no
# board configured" says nothing has gone wrong.
CONTRACT_ROWS = ("changed", "re-baselined", "unreachable", "check failed", "baseline")
# A board status that is a row; "ok" and "skipped" are not.
BOARD_ROWS = ("failed", "error", "unparseable", "not reached")
# The parts of a run whose failure is a row, as each run log names it.
RUN_PARTS = (("projection", lambda log: (log.get("airtable") or {}).get("failure")),
             ("sweep", lambda log: (log.get("sweep") or {}).get("failure")),
             ("private store", lambda log: (log.get("private_store") or {}).get("failure")),
             ("clearing tool", lambda log: (log.get("clearing") or {}).get("failure")),
             ("closure test", lambda log: log.get("closure_failure")),
             ("health", lambda log: (log.get(LOG_KEY) or {}).get("failure")))


def row(when, source, subject, status, detail, key):
    return {"Key": key, "When": airtable_datetime(when), "Source": source,
            "Subject": subject, "Status": status, "Detail": detail or None}


def shape(value):
    if isinstance(value, dict):
        return ", ".join("%s %s" % (k, value[k]) for k in sorted(value))
    return str(value)


def contract_events(log):
    """The rows one contract check's log holds."""
    when = log.get("run_at")
    out = []
    for platform, entry in sorted((log.get("platforms") or {}).items()):
        status = entry.get("status")
        if status not in CONTRACT_ROWS:
            continue
        changes = entry.get("changes") or []
        if status in ("changed", "re-baselined") and changes:
            for c in changes:
                field = "%s.%s" % (c.get("in"), c.get("field"))
                detail = "%s field %s: was %s; now %s" % (c.get("in"), c.get("field"),
                                                          shape(c.get("was")), shape(c.get("now")))
                if c.get("ours"):
                    detail += "; ours, %s" % c["ours"]
                out.append(row(when, CONTRACT, platform,
                               "re-baselined" if c.get("ours") else "changed", detail,
                               "contract %s %s %s" % (when, platform, field)))
        else:
            out.append(row(when, CONTRACT, platform, status,
                           entry.get("detail") or entry.get("board"),
                           "contract %s %s" % (when, platform)))
    return out


def run_events(log):
    """The rows one fetch run's log holds."""
    when = log.get("run_at")
    out = []
    for board in log.get("boards") or []:
        if board.get("status") in BOARD_ROWS:
            out.append(row(when, FETCH, board.get("board"), board["status"], board.get("detail"),
                           "run %s %s" % (when, board.get("board"))))
    if log.get("stopped"):
        out.append(row(when, FETCH, "fetch", "stopped", log["stopped"], "run %s fetch" % when))
    for part, failure in RUN_PARTS:
        text = failure(log)
        if text:
            out.append(row(when, FETCH, part, "failed", text, "run %s %s" % (when, part)))
    return out


def sent_keys(run_logs):
    sent = set()
    for log in run_logs:
        sent.update((log.get(LOG_KEY) or {}).get("sent") or [])
    return sent


def pending(run_logs, contract_logs, now):
    """The rows of the last week that no run has recorded as sent, oldest
    first. `run_logs` include the current run's own."""
    since = now - timedelta(days=WINDOW_DAYS)
    sent = sent_keys(run_logs)
    rows, seen = [], set()
    for log, events in ([(log, run_events) for log in run_logs]
                        + [(log, contract_events) for log in contract_logs]):
        if not isinstance(log, dict) or not recent(log.get("run_at"), since):
            continue
        for r in events(log):
            if r[KEY_FIELD] not in sent and r[KEY_FIELD] not in seen:
                seen.add(r[KEY_FIELD])
                rows.append(r)
    rows.sort(key=lambda r: (r["When"] or "", r[KEY_FIELD]))
    return rows


def recent(when, since):
    try:
        at = datetime.fromisoformat(str(when).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return False
    return at >= since
