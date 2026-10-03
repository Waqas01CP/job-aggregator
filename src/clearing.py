"""ADR-0055's tool: the operator clears a chosen table by an age threshold.

He runs it from the fetch workflow's dispatch, choosing a table, a threshold
in days (fifteen, thirty, or any number he gives) and whether to confirm. His
words, 2026-09-28: "i decided i wanted to delete the last 1 month jobs and i
selected that then it should delete the jobs which are older than 1 month".

**Deleting a row in the browser does not stick**, which is why this exists.
The projection re-applies the rules over the whole filtered layer and upserts
on `Identity`, so a row cleared by hand returns at the next run. Only a store the skip
reads keeps a row out.

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
among them, and how many are unreviewed, and removes and stores nothing. A
confirmed run refuses unless a dry run of the same table and threshold, in
the same mode, finished on this branch within `clearing_dry_run_valid_hours`.

**A confirmed run removes only what its dry run listed.** It selects again
at its own clock and acts on the rows both selections hold. A row that
crossed the threshold after the dry run is left and counted, never removed
unseen: `operator-removed` never returns, and he said "i do not want to miss
any". The fourth audit's F1 found the first build selecting afresh, so a
confirm up to 48 hours later removed rows no dry run had shown him.

**So every row the dry run lists is named where he can read it.** A public
row by identity in the run log. An aggregator's is masked there (ADR-0020),
so the dry run lists it, with its title, employer and date, in the private
repository's `clearing/dry_runs.json`. That file is a list for him and for
the confirm, and is no store: neither the skip nor the sweep reads it, so it
keeps nothing out of the display. **It sits outside `outcomes/`**, the
architecture chat's ruling of 2026-10-03 in ADR-0055: a file there will one
day be read as a store, so the guarantee holds by where the file sits and
not only by what reads it today.

**Clearing `Jobs` takes a classified row's rejection copy with it**, since
both leave on the outcome the tool writes. An accepted copy stays until its
`Delete` (D12). The dry run counts the classified rows by status, so the
copies leaving are not a surprise (the fourth audit's F16).

**The dry run says how many of its rows are leaving without it.** The tool
runs after the sweep, and a row the sweep has just stored for removal, or
one already kept out for good, goes on a later run whatever he confirms. On
2026-10-02 his dry run listed 19 rows and the confirm removed 2: the sweep
had taken the other 17, and nothing on the line he read said so. The
operator asked for the count on 2026-10-03.
"""

from datetime import timedelta

from . import storage
from .config import is_publishable
from .airtable_sweep import (CLASSIFICATION_TABLES, COPY_FIELDS, DELETE_FIELD, DELETE_YES, JOBS,
                             OPERATOR_FIELD)
from .normalise import Row
from .projection import REASON_OPERATOR, REMOVED_UNREVIEWED_STORE, removal_key
from .storage import CLEARING_DIR
from .sweep import (JOBS_FIELDS, REMOVED_BY_OPERATOR, STORE_FOR, Stores, jobs_fields_record,
                    masked, older_than, parse_time, source_of)

# The four tables by the name the dispatch offers; `jobs` is this mode's
# `Jobs` or `Jobs test`, as the client binds it.
TABLES = (JOBS,) + CLASSIFICATION_TABLES
NONE = "none"
# The dry run's aggregator rows, in the private store's own directory for
# the tool. Read by the confirm and by no store reader.
DRY_RUN_FILE = "dry_runs.json"
DRY_RUN_PATH = "%s/%s" % (CLEARING_DIR, DRY_RUN_FILE)


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


def dry_run_on_file(logs, table, days, now, valid_hours, test_mode=False):
    """The latest of `logs`, this branch's recent run logs, carrying a dry run
    of the same table and threshold in the same mode, finished and recent
    enough; or None. None of these may stand in for one, and the fourth
    audit's F2 found the first three untested: a dry run that failed showed
    nothing; a confirmed run is not a dry run; a log of the other mode listed
    the other mode's rows; and a log with no list gives the confirm nothing
    to bind to."""
    found = None
    for log in logs:
        if not isinstance(log, dict) or bool(log.get("test_mode")) != test_mode:
            continue
        c = log.get("clearing") or {}
        if (c.get("table"), c.get("older_than_days"), c.get("confirmed")) != (table, days, False):
            continue
        if c.get("failure") or not isinstance(c.get("rows"), list):
            continue
        when = log.get("run_at")
        if not when or parse_time(when) < now - timedelta(hours=valid_hours):
            continue
        if found is None or parse_time(when) > parse_time(found["run_at"]):
            found = log
    return found


class Clearing:
    def __init__(self, client, paths, now, private_ok, test_mode=False):
        self.client = client
        self.now = now
        self.now_iso = now.isoformat().replace("+00:00", "Z")
        self.test_mode = test_mode
        self.dry_run_path = "%s/%s" % (paths["local_clearing_dir"], DRY_RUN_FILE)
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
        listed = None
        if confirmed:
            dry = dry_run_on_file(logs, table, days, self.now, valid_hours, self.test_mode)
            if dry is None:
                report["failure"] = ("refused: no dry run of %s at %d days on this branch in "
                                     "the last %d hours. Run it once without confirming, read "
                                     "the report, then confirm" % (table, days, valid_hours))
                return report
            report["dry_run_at"] = dry["run_at"]
            listed = self.listed_by(dry)
        chosen, undated = self.select(table, days)
        if listed is not None:
            # A row the private store cannot be read for stays and is counted
            # as held, below; every other row must have been shown.
            unseen = {r["id"] for r in chosen if r["fields"].get("Identity")
                      and self.stores.where(r["fields"]["Identity"]) is not None
                      and r["fields"]["Identity"] not in listed}
            report["not_in_the_dry_run"] = len(unseen)
            chosen = [r for r in chosen if r["id"] not in unseen]
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
        if table == JOBS:
            classified = {}
            for r in chosen:
                status = r["fields"].get("Status")
                if status in STORE_FOR:
                    classified[status] = classified.get(status, 0) + 1
            report["classified"] = classified
        if not confirmed:
            self.list_privately(table, days, chosen, report)
            report["leaving_without_the_tool"] = self.leaving_anyway(table, chosen)
            report["mode"] = "dry run: nothing was removed or stored"
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

    def leaving_anyway(self, table, chosen):
        """How many of the rows a dry run lists leave on a later run without
        the tool: on `accepted`, a copy whose `Delete` is already set; a
        classified row whose outcome is already in its store; an unreviewed
        row kept out for good, or one this run's sweep, which ran first,
        has just stored for removal under a rule's reason."""
        if table == "accepted":
            return sum(1 for r in chosen if r["fields"].get(DELETE_FIELD) == DELETE_YES)
        swept = set()
        for directory in self.stores.dirs.values():
            swept |= {r.get("identity") for r in storage.read_records(
                "%s/%s" % (directory, REMOVED_UNREVIEWED_STORE))
                if r.get("swept_at") == self.now_iso}
        count = 0
        for r in chosen:
            identity = r["fields"].get("Identity")
            where = self.stores.where(identity) if identity else None
            if where is None:
                continue
            status = r["fields"].get("Status") if table == JOBS else table
            if status in STORE_FOR:
                count += self.stores.durable_has(where, STORE_FOR[status], identity)
            elif self.stores.kept_out_reason(where, identity) is not None or identity in swept:
                count += 1
        return count

    def listed_by(self, dry):
        """The identities a dry run showed: a public row's from its run log,
        an aggregator's from the private list it wrote, when the private
        store can be read."""
        listed = {i for i in dry["clearing"]["rows"]
                  if isinstance(i, str) and is_publishable(source_of(i))}
        if "private" in self.stores.dirs:
            listed |= {r.get("identity") for r in storage.read_records(self.dry_run_path)
                       if r.get("dry_run_at") == dry["run_at"]}
        return listed

    def list_privately(self, table, days, chosen, report):
        """The dry run's aggregator rows, named for him to review and for the
        confirm to bind to. Without the private store they cannot be listed,
        so a confirm will leave them, and the report says so."""
        aggregator = [r for r in chosen if r["fields"].get("Identity")
                      and not is_publishable(source_of(r["fields"]["Identity"]))]
        if not aggregator:
            return
        if "private" not in self.stores.dirs:
            report["aggregator_not_listed"] = len(aggregator)
            return
        records = []
        for r in aggregator:
            f = r["fields"]
            records.append({
                "key": "%s|%s" % (self.now_iso, f["Identity"]), "dry_run_at": self.now_iso,
                "table": table, "older_than_days": days, "identity": f["Identity"],
                "title": f.get("Title"), "employer": f.get("Employer"),
                "published": f.get("Published"),
                "status": f.get("Status") if table == JOBS else table,
                "classified": f.get("Classified at") if table == JOBS else r.get("createdTime")})
        report["aggregator_listed_privately"] = storage.append_delta(self.dry_run_path, records,
                                                                     key="key")

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
