"""The closure test. ADR-0050.

**A posting has closed when either holds.** Its own expiry date has passed.
Or it was absent from its board on `closed_after_polled_runs` consecutive runs
that polled that board: twelve, configuration under ADR-0031. Four until
2026-10-03, when the operator raised it: postings measured leaving their
boards and coming back were gone up to 130 hours, and four runs is about 48.

**A run that did not poll the board never counts.** ADR-0048 skips Himalayas
on the evening run, and counting those runs would close every aggregator row
in two days. A board that failed, was not reached, or answered with nothing
did not poll either: a board returning nothing is a broken adapter far more
often than an empty market, and counting it would close the whole board.

**Nor does a run that did not reach the posting.** A paginated feed is read
only until it meets what is already stored, so a run that stopped on its
first page never looked at an older posting, and its absence there says
nothing. For such a board a run counts only when its walk covered the
posting's date: stopped at its mark, the walk read every posting newer than
the mark; read to the feed's end, every posting; stopped by the page cap,
nothing is proved. The rule the brief names, "a run that did not poll the
board never counts", applied posting by posting. A board read whole on every
run, Greenhouse and Lever, needs no such test.

**The walk's oldest posting is not its reach.** That was the first build's
test, and the search pins old postings on page one, so every walk logged
2026-09-16 as its oldest whether it read one page or thirty. Every Himalayas
row was then marked closed four mornings after it was last seen: 47 open
rows on 2026-10-01 and 10-02, hidden from the operator's `To review` view
and fifteen days from being retired as closed, which never returns. A log
written before the walk's reach was recorded counts for nothing, so those
marks clear on the next sweep.

**In practice a Himalayas posting now closes by its expiry date**, which the
source gives on every posting. The mark advances with each walk, so a walk
covers a posting's date on about one run after it was last seen, never
twelve in a row. Absence on a feed read only to its newest postings is not
evidence, and the test no longer pretends it is.

**A display group has closed when every member has**, on the day the last of
them closed. One city copy still listed keeps the role open.

Nothing here reads Airtable. Everything comes from the seen store's
`last_seen`, the run logs and the rows themselves, all on the data branch.
"""

from datetime import datetime, timezone


def _when(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def covered(walk, published):
    """Whether a paginated walk, as its run log records it, read back far
    enough that a posting published at `published` would have been fetched
    had it still been listed.

    **A walk that reached the feed's end read every posting, dated or not.**
    Asked first since 2026-10-07: Manatal's postings carry no date and its
    walk always reads to the end, and asked after the date, a posting with
    none could never be closed by its absence."""
    if not isinstance(walk, dict):
        return False
    if walk.get("stopped_by") == "end":
        return True
    if not published:
        return False
    if walk.get("stopped_by") != "mark" or not walk.get("mark"):
        return False
    return _when(published) > _when(walk["mark"])


def history(run_logs):
    """[(run_at, {board_id: board_log})], oldest first."""
    out = []
    for log in run_logs:
        if not isinstance(log, dict) or not log.get("run_at"):
            continue
        boards = {b.get("board"): b for b in log.get("boards") or [] if isinstance(b, dict)}
        out.append((log["run_at"], boards))
    out.sort(key=lambda pair: pair[0])
    return out


class Closure:
    def __init__(self, last_seen, run_logs, paginated, runs_needed, now_iso):
        """`last_seen` maps identity to the last run that fetched it.
        `paginated(board_id)` says whether a board is read only to its stop."""
        self._last_seen = last_seen
        self._history = history(run_logs)
        self._paginated = paginated
        self._runs_needed = runs_needed
        self._now = now_iso

    def closed_on(self, row):
        """(ISO date, "expired" or "absent"), or (None, None) while open or
        unknowable. A posting never seen by any run is unknowable."""
        if row.expires_at and row.expires_at <= self._now:
            return row.expires_at[:10], "expired"
        seen = self._last_seen.get(row.identity)
        if not seen:
            return None, None
        paginated = self._paginated(row.board_id)
        counted = 0
        for run_at, boards in self._history:
            if run_at <= seen:
                continue
            board = boards.get(row.board_id)
            if not board or board.get("status") != "ok" or not board.get("fetched"):
                continue
            if paginated and not covered(board.get("walk"), row.published_at):
                continue
            counted += 1
            if counted >= self._runs_needed:
                return run_at[:10], "absent"
        return None, None

    def group_closed_on(self, members):
        """The day the last member closed, or None while any is open."""
        days = []
        for row in members:
            day, _ = self.closed_on(row)
            if day is None:
                return None
            days.append(day)
        return max(days) if days else None
