"""Writers for the raw and filtered layers, and the orphan data branch.

**Append deltas, never snapshots.** ADR-0003. A record already present is never
rewritten and a full snapshot is never written, so repository growth is
proportional to genuinely new postings rather than to board size.

**One file per source.** ADR-0020. `fetch-all/greenhouse.json`,
`fetch-all/lever.json`. A row's provenance is its filename, so no routing bug
can misfile a row into the wrong store. Aggregator sources write to local files
that are never committed; the slice has none, and the split is by directory so
that moving a source later is a file move rather than a transformation.

**Metadata only.** ADR-0011. The row shape has nowhere to put description text,
which is the guard: there is no field to fill.

**Atomic writes.** Temp file then rename, so a run killed mid-write leaves the
previous file intact rather than a truncated one.

**The data branch is orphan and is never checked out.** Commits are built with
plumbing: hash-object, a scratch index, write-tree, commit-tree, update-ref.
The working tree is never touched, which avoids the stash-and-restore sequence
the prior project needs because its data directory is ignored on one branch and
tracked on another. A run can therefore commit data while the operator has
uncommitted work on main.
"""

import os
import shutil
import subprocess
import tempfile

from .normalise import dumps, loads

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_BRANCH = "data"
RAW_DIR = "fetch-all"
# ADR-0020: aggregator rows live here and are never committed or pushed.
LOCAL_RAW_DIR = "fetch-all-local"
FILTERED_FILE = "filtered.json"
SEEN_FILE = "seen.json"
RUNLOG_DIR = "logs-runs"

# A test run writes beside production data, never over it.
TEST_PREFIX = "test-"


class StorageError(Exception):
    pass


def layout(test_mode=False):
    """Every path the pipeline writes, in one place so a test run cannot
    accidentally inherit a production path."""
    prefix = TEST_PREFIX if test_mode else ""
    return {
        "raw_dir": prefix + RAW_DIR,
        "local_raw_dir": prefix + LOCAL_RAW_DIR,
        "filtered": prefix + FILTERED_FILE,
        "seen": prefix + SEEN_FILE,
        "runlog_dir": prefix + RUNLOG_DIR,
    }


def raw_path(source, test_mode=False, source_class="ats"):
    """One file per source. ADR-0020. An aggregator's file sits in a separate
    directory that the data-branch commit never reads, so a routing bug cannot
    push a row that must not be published."""
    key = "local_raw_dir" if source_class == "aggregator" else "raw_dir"
    return "%s/%s.json" % (layout(test_mode)[key], source)


# ------------------------------------------------------------ local files
def write_atomic(path, text):
    """Write to a temp file in the same directory, then rename.

    Same directory because rename is only atomic within a filesystem."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_records(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.strip():
        return []
    records = loads(text)
    if not isinstance(records, list):
        raise StorageError("%s does not hold a list of records" % path)
    return records


def append_delta(path, records, key="identity"):
    """Append only records whose key is absent. Returns the number appended.

    Writes nothing when there is nothing to append, so a run that changes
    nothing leaves the file byte-identical and produces no diff."""
    existing = read_records(path)
    seen = {r.get(key) for r in existing}
    fresh = [r for r in records if r.get(key) not in seen]
    if not fresh:
        return 0
    write_atomic(path, dumps(existing + fresh))
    return len(fresh)


# ------------------------------------------------------------ seen store
class SeenStore:
    """Identity to first-seen, plus the publication date once known.

    ADR-0003 keeps mutable lifecycle state out of the append-only records and
    in a structure small enough to rewrite each run. ADR-0028 makes it
    load-bearing for cost too: a posting whose publication date is already
    recorded never needs a detail request again."""

    def __init__(self, entries=None):
        self.entries = dict(entries or {})

    @classmethod
    def load(cls, path):
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return cls(loads(text) if text.strip() else {})

    def save(self, path):
        ordered = {k: self.entries[k] for k in sorted(self.entries)}
        write_atomic(path, dumps(ordered))

    @property
    def identities(self):
        return set(self.entries)

    def first_seen_map(self):
        return {k: v.get("first_seen") for k, v in self.entries.items()}

    def record(self, row):
        entry = self.entries.get(row.identity)
        if entry is None:
            self.entries[row.identity] = {
                "first_seen": row.first_seen,
                "published_at": row.published_at,
                "source": row.source,
                "last_seen": row.first_seen,
            }
        else:
            # first_seen is never rewritten: it is the moment of first
            # observation and re-dating it would reset every posting's age.
            entry["published_at"] = entry.get("published_at") or row.published_at
            entry["source"] = row.source

    def mark_seen(self, identity, when):
        entry = self.entries.get(identity)
        if entry is not None:
            entry["last_seen"] = when


# ------------------------------------------------------- the data branch
def _git(args, cwd=None, env=None, check=True, stdin=None):
    # REPO_ROOT is resolved on every call, never bound as a default. A default
    # is evaluated once at import, so a caller that repoints REPO_ROOT would
    # still have run against the original repository. A test did exactly that
    # and committed to the real one.
    cwd = cwd or REPO_ROOT
    full = dict(os.environ)
    full.update(env or {})
    p = subprocess.run(["git"] + args, cwd=cwd, env=full, input=stdin,
                       capture_output=True, text=True)
    if check and p.returncode != 0:
        raise StorageError("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
    return p.stdout.strip()


def branch_exists(branch=DATA_BRANCH):
    p = subprocess.run(["git", "rev-parse", "--verify", "--quiet", branch],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    return p.returncode == 0


def read_branch_file(path, branch=DATA_BRANCH):
    """Read one file from the branch without checking it out."""
    if not branch_exists(branch):
        return None
    p = subprocess.run(["git", "show", "%s:%s" % (branch, path)],
                       cwd=REPO_ROOT, capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def commit_files(files, message, branch=DATA_BRANCH):
    """Commit a mapping of path to text onto an orphan branch.

    Plumbing only. The working tree and the real index are never touched, so
    this is safe to run while the operator has uncommitted work on main.
    Returns the new commit sha, or None when nothing changed."""
    if not files:
        return None

    parent = _git(["rev-parse", branch]) if branch_exists(branch) else None

    # A scratch index git creates itself. NamedTemporaryFile would leave a
    # zero-byte file behind, and git refuses that with "index file smaller
    # than expected" rather than treating it as empty.
    index_dir = tempfile.mkdtemp(suffix=".gitindex")
    env = {"GIT_INDEX_FILE": os.path.join(index_dir, "index")}
    try:
        if parent:
            _git(["read-tree", branch], env=env)
        for path, text in sorted(files.items()):
            blob = _git(["hash-object", "-w", "--stdin"], env=env, stdin=text)
            _git(["update-index", "--add", "--cacheinfo",
                  "100644,%s,%s" % (blob, path)], env=env)
        tree = _git(["write-tree"], env=env)

        if parent:
            parent_tree = _git(["rev-parse", "%s^{tree}" % branch])
            if tree == parent_tree:
                return None      # nothing changed, so no empty commit
        args = ["commit-tree", tree, "-m", message]
        if parent:
            args += ["-p", parent]
        commit = _git(args, env=env)
        _git(["update-ref", "refs/heads/%s" % branch, commit])
        return commit
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)
