"""ADR-0055's tool: the operator clears a chosen table by an age threshold.

He runs it from the fetch workflow's dispatch, choosing a table, a threshold
in days (fifteen, thirty, or any number he gives) and whether to confirm. His
words, 2026-09-28: "i decided i wanted to delete the last 1 month jobs and i
selected that then it should delete the jobs which are older than 1 month".

**Deleting a row in the browser does not stick**, which is why this exists.
The projection re-applies the rules over the whole filtered layer and upserts
on `Identity`, so a row cleared by hand returns within about fourteen hours.
Only a store the skip reads keeps a row out.

**So the tool writes stores and deletes nothing.** The next daily sweep reads
what this run wrote back from origin and deletes the rows then, by ADR-0050's
write, verify, delete, a day later:

- `Jobs`, unreviewed: `outcomes/removed_unreviewed.json`, reason
  `operator-removed`, which never returns (ADR-0043).
- `Jobs`, classified, and the two rejection tables: the row's own outcome
  corpus, marked `removed_by: operator`, so it leaves before its fifteen days
  with its classification saved.
- `accepted`: `Delete` set to yes, and D12's path does the rest. One way out
  of the one table that cannot be reconstructed.

**The threshold measures the publication date on `Jobs`, and `Classified` on
the three classification tables**: those rows record decisions, and their age
is the decision's. A seven-day threshold on publication date is a trap: on
2026-09-28 it would have removed 11 of 13 legitimate rows, because ADR-0052
judges age once at first sight and a waiting row's publication date recedes.

**A dry run always comes first.** A run that is not confirmed reports, per
table, how many rows it would remove, the oldest and newest publication dates
among them, and how many are unreviewed, and writes nothing. A confirmed run
refuses unless a dry run of the same table and threshold ran on this branch
within `clearing_dry_run_valid_hours`. Every row is named in the run log by
identity, an aggregator's masked there and named in its private store.
"""

from datetime import timedelta

from . import storage
from .airtable_sweep import (CLASSIFICATION_TABLES, COPY_FIELDS, DELETE_FIELD, DELETE_YES, JOBS,
                             OPERATOR_FIELD)
from .normalise import Row
from .projection import REASON_OPERATOR, REMOVED_UNREVIEWED_STORE, removal_key
from .sweep import (JOBS_FIELDS, REMOVED_BY_OPERATOR, STORE_FOR, Stores, jobs_fields_record,
                    masked, older_than, parse_time)

# The four tables by the name the dispatch offers; `jobs` is this mode's
# `Jobs` or `Jobs test`, as the client binds it.
TABLES = (JOBS,) + CLASSIFICATION_TABLES
NONE = "none"


class ClearingError(Exception):
    pass


def request_from(table, days, confirm):
    """(table, days, confirmed) from the dispatch's inputs, or None when no
    table was chosen. A threshold that is not a whole number of at least one
    day is refused by name."""
    table = (table or NONE).strip()
    if table == NONE:
        return None
    if table not in TABLES:
        raise ClearingError("no table named %r; choose one of %s" % (table, ", ".join(TABLES)))
    try:
        value = int(str(days).strip())
    except ValueError:
        raise ClearingError("the threshold must be a whole number of days, got %r" % (days,))
    if value < 1:
        raise ClearingError("the threshold must be at least one day, got %d" % value)
    return table, value, bool(confirm)


def dry_run_on_file(logs, table, days, now, valid_hours):
    """Whether one of `logs`, this branch's recent run logs, carries an
    unconfirmed run of the same table and threshold, recent enough."""
    for log in logs:
        c = (log or {}).get("clearing") or {}
        if (c.get("table"), c.get("older_than_days"), c.get("confirmed")) != (table, days, False):
            continue
        if c.get("failure"):
            continue
        when = log.get("run_at")
        if when and parse_time(when) >= now - timedelta(hours=valid_hours):
            return True
    return False


class Clearing:
    def __init__(self, client, paths, now, private_ok):
        self.client = client
        self.now = now
        self.now_iso = now.isoformat().replace("+00:00", "Z")
        self.stores = Stores(paths, private_ok)
        rows = []
        for key in ("filtered", "local_filtered"):
            if key == "local_filtered" and not private_ok:
                continue
            rows.extend(Row(**r) for r in storage.read_records(paths[key]))
        self.rows = {r.identity: r for r in rows}

    def record(self, identity, fields, **outcome):
        row = self.rows.get(identity)
        rec = row.as_record() if row else jobs_fields_record(fields)
        rec.update(outcome)
        rec["swept_at"] = self.now_iso
        return rec

    # ------------------------------------------------------------ selecting
    def select(self, table, days):
        """The rows older than the threshold, and the rows that cannot be
        judged because the date the threshold measures is missing."""
        if table == JOBS:
            rows = self.client.list_records(JOBS, JOBS_FIELDS)
            dated = [(r, r["fields"].get("Published")) for r in rows]
        else:
            fields = COPY_FIELDS + (OPERATOR_FIELD[table],)
            if table == "accepted":
                fields += (DELETE_FIELD,)
            rows = self.client.list_records(table, fields)
            dated = [(r, r.get("createdTime")) for r in rows]
        chosen = [r for r, when in dated if when and older_than(when, days, self.now)]
        undated = [r for r, when in dated if not when]
        return chosen, undated

    # ----------------------------------------------------------------- run
    def run(self, table, days, confirmed, logs, valid_hours):
        report = {"table": table, "older_than_days": days, "confirmed": confirmed,
                  "measured_on": "publication date" if table == JOBS else "Classified",
                  "failure": None}
        if confirmed and not dry_run_on_file(logs, table, days, self.now, valid_hours):
            report["failure"] = ("refused: no dry run of %s at %d days on this branch in the last "
                                 "%d hours. Run it once without confirming, read the report, "
                                 "then confirm" % (table, days, valid_hours))
            return report
        chosen, undated = self.select(table, days)
        published = sorted(r["fields"].get("Published") for r in chosen
                           if r["fields"].get("Published"))
        report.update({
            "would_remove": len(chosen),
            "oldest_published": published[0] if published else None,
            "newest_published": published[-1] if published else None,
            "unreviewed": sum(1 for r in chosen
                              if table == JOBS and not r["fields"].get("Status")),
            "without_a_date": len(undated),
            "rows": [masked(r["fields"].get("Identity")) for r in chosen],
        })
        if not confirmed:
            report["mode"] = "dry run: nothing was written or removed"
            return report
        report.update({"written": 0, "already_leaving": 0, "marked_delete": 0,
                       "held_private_unavailable": 0, "problems": []})
        if table == JOBS:
            self.clear_jobs(chosen, report)
        elif table == "accepted":
            self.clear_accepted(chosen, report)
        else:
            self.clear_rejections(table, chosen, report)
        report["stored_written"] = dict(self.stores.written)
        report["mode"] = ("confirmed: stores written; the next daily sweep removes the rows "
                          "once origin holds them")
        return report

    def clear_jobs(self, chosen, report):
        copies = None
        for r in chosen:
            f = r["fields"]
            identity, status = f.get("Identity"), f.get("Status")
            where = self.stores.where(identity)
            if not identity:
                continue
            if where is None:
                report["held_private_unavailable"] += 1
                continue
            if not status:
                if self.stores.kept_out_reason(where, identity) is not None:
                    report["already_leaving"] += 1
                    continue
                self.stores.write(where, REMOVED_UNREVIEWED_STORE,
                                  self.record(identity, f, reason=REASON_OPERATOR,
                                              removed_by=REMOVED_BY_OPERATOR,
                                              removal=removal_key(identity, REASON_OPERATOR)),
                                  key="removal")
                report["written"] += 1
                continue
            if status not in STORE_FOR:
                continue
            if copies is None:
                copies = {t: {c["fields"].get("Identity"): c for c in self.client.list_records(
                    t, ("Identity", OPERATOR_FIELD[t]))} for t in CLASSIFICATION_TABLES}
            copy = copies[status].get(identity)
            reason = copy["fields"].get(OPERATOR_FIELD[status]) if copy else None
            self.store_outcome(where, status, identity, f, reason,
                               f.get("Classified at"), report)

    def clear_rejections(self, table, chosen, report):
        for c in chosen:
            f = c["fields"]
            identity = f.get("Identity")
            where = self.stores.where(identity)
            if not identity:
                continue
            if where is None:
                report["held_private_unavailable"] += 1
                continue
            self.store_outcome(where, table, identity, f, f.get(OPERATOR_FIELD[table]),
                               c.get("createdTime"), report)

    def store_outcome(self, where, status, identity, fields, reason, classified, report):
        """The classification saved in its corpus, marked as the operator's
        removal, so its row and copy leave before their fifteen days. An
        identity already in its corpus is already leaving; one in another
        corpus is left and reported, since routing is exclusive (ADR-0043)."""
        name = STORE_FOR[status]
        if self.stores.classified_elsewhere(where, name, identity):
            report["problems"].append("%s is already in another classification store; left"
                                      % masked(identity))
            return
        if self.stores.durable_has(where, name, identity):
            report["already_leaving"] += 1
            return
        written = self.stores.write(where, name, self.record(
            identity, fields, status=status, reason=reason, classified_at=classified,
            removed_by=REMOVED_BY_OPERATOR))
        report["written"] += written
        report["already_leaving"] += 1 - written

    def clear_accepted(self, chosen, report):
        """`Delete` set, nothing deleted, nothing stored here: D12's path in
        the sweep saves each copy and removes it."""
        ids = [c["id"] for c in chosen if c["fields"].get(DELETE_FIELD) != DELETE_YES]
        report["already_leaving"] += len(chosen) - len(ids)
        if ids:
            self.client.mark_delete(ids)
        report["marked_delete"] = len(ids)
