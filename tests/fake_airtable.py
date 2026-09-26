"""An in-memory Airtable base for tests. No network.

It answers the calls both clients make: the projection's upsert and the
sweep's list, create, update and delete, routed by table ID. It models the
two clocks the flow depends on, as Airtable keeps them:

- `Classified at` on a `Jobs` table is a last-modified time watching `Status`
  alone: it moves when, and only when, a write changes `Status`, a clear
  included. It is empty only on a row whose `Status` was never set.
- Every record carries `createdTime`, which is what `Classified` on a
  classification table is.

Reads honour `pageSize`, `offset` and `fields[]`, and omit an empty field, as
Airtable does. Every call is recorded, so a test can count them or assert
what was never sent.

Writes refuse more than ten records a call, Airtable's documented limit, and
a delete naming a record that is not there fails whole, nothing deleted. The
audit of 2026-09-25 found the base accepting any batch and ignoring a missing
record (F5, nit 1). The status codes are the base's choice; Airtable's exact
answers to both are unverified. `fail`, when a test sets it, is asked about
each call first and may answer in the base's place.
"""

import itertools
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

T0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
MAX_RECORDS = 10


def stamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.headers = {}

    def json(self):
        return json.loads(json.dumps(self._body))


class FakeBase:
    def __init__(self, jobs_tables=(), now=None):
        """`jobs_tables` are the table IDs that are `Jobs` tables, whose
        `Classified at` watches `Status`."""
        self.tables = {}
        self.jobs_tables = set(jobs_tables)
        self.now = now or T0
        self.calls = []
        self.fail = None
        self._ids = itertools.count(1)

    # ---------------------------------------------------------- test helpers
    def table(self, table_id):
        return self.tables.setdefault(table_id, {})

    def seed(self, table_id, fields, created=None, classified_at=None):
        record_id = "rec%014d" % next(self._ids)
        record = {"createdTime": stamp(created or self.now), "fields": dict(fields)}
        if classified_at is not None:
            record["fields"]["Classified at"] = stamp(classified_at)
        self.table(table_id)[record_id] = record
        return record_id

    def rows(self, table_id):
        return [dict(r["fields"], _id=i, _created=r["createdTime"])
                for i, r in self.table(table_id).items()]

    def advance(self, **kw):
        self.now = self.now + timedelta(**kw)

    # ------------------------------------------------------------------ wire
    def request(self, method, url, params=None, json=None, headers=None, timeout=None):
        table_id = urlparse(url).path.rstrip("/").split("/")[-1]
        call = {"method": method, "table": table_id, "params": params, "json": json}
        self.calls.append(call)
        if self.fail is not None:
            answer = self.fail(call)
            if answer is not None:
                return answer
        if method in ("POST", "PATCH") and len((json or {}).get("records", [])) > MAX_RECORDS:
            return Response(422, {"error": "more than %d records" % MAX_RECORDS})
        handler = {"GET": self._list, "POST": self._create, "PATCH": self._patch,
                   "DELETE": self._delete}[method]
        return handler(table_id, params or [], json or {})

    def _write_fields(self, table_id, record, fields):
        before = record["fields"].get("Status")
        for name, value in fields.items():
            if value is None:
                record["fields"].pop(name, None)
            else:
                record["fields"][name] = value
        if table_id in self.jobs_tables and "Status" in fields \
                and record["fields"].get("Status") != before:
            record["fields"]["Classified at"] = stamp(self.now)

    def _list(self, table_id, params, body):
        params = list(params.items()) if isinstance(params, dict) else list(params)
        size = int(dict(params).get("pageSize", 100))
        offset = int(dict(params).get("offset", 0))
        wanted = [v for k, v in params if k == "fields[]"]
        items = sorted(self.table(table_id).items())
        page = items[offset:offset + size]
        records = []
        for record_id, r in page:
            fields = {k: v for k, v in r["fields"].items()
                      if (not wanted or k in wanted) and v not in (None, "")}
            records.append({"id": record_id, "createdTime": r["createdTime"], "fields": fields})
        out = {"records": records}
        if offset + size < len(items):
            out["offset"] = str(offset + size)
        return Response(200, out)

    def _create(self, table_id, params, body):
        created = []
        for r in body.get("records", []):
            record_id = "rec%014d" % next(self._ids)
            record = {"createdTime": stamp(self.now), "fields": {}}
            self._write_fields(table_id, record, r.get("fields", {}))
            self.table(table_id)[record_id] = record
            created.append({"id": record_id, "createdTime": record["createdTime"],
                            "fields": dict(record["fields"])})
        return Response(200, {"records": created})

    def _patch(self, table_id, params, body):
        out, created_ids, updated_ids = [], [], []
        merge = (body.get("performUpsert") or {}).get("fieldsToMergeOn")
        for r in body.get("records", []):
            if merge:
                key = merge[0]
                match = [i for i, rec in self.table(table_id).items()
                         if rec["fields"].get(key) == r["fields"].get(key)]
                if len(match) > 1:
                    return Response(422, {"error": "multiple matches"})
                if match:
                    record_id = match[0]
                    updated_ids.append(record_id)
                else:
                    record_id = "rec%014d" % next(self._ids)
                    self.table(table_id)[record_id] = {"createdTime": stamp(self.now),
                                                       "fields": {}}
                    created_ids.append(record_id)
            else:
                record_id = r.get("id")
                if record_id not in self.table(table_id):
                    return Response(404, {"error": "NOT_FOUND"})
            self._write_fields(table_id, self.table(table_id)[record_id], r.get("fields", {}))
            rec = self.table(table_id)[record_id]
            out.append({"id": record_id, "createdTime": rec["createdTime"],
                        "fields": dict(rec["fields"])})
        body_out = {"records": out}
        if merge:
            body_out.update(createdRecords=created_ids, updatedRecords=updated_ids)
        return Response(200, body_out)

    def _delete(self, table_id, params, body):
        ids = [v for k, v in (params.items() if isinstance(params, dict) else params)
               if k == "records[]"]
        if len(ids) > MAX_RECORDS:
            return Response(422, {"error": "more than %d records" % MAX_RECORDS})
        if any(record_id not in self.table(table_id) for record_id in ids):
            return Response(404, {"error": "NOT_FOUND"})
        out = []
        for record_id in ids:
            self.table(table_id).pop(record_id)
            out.append({"id": record_id, "deleted": True})
        return Response(200, {"records": out})
