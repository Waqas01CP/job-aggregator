"""Writers for the raw and filtered layers, and the orphan data branch.

**Append deltas, never snapshots.** ADR-0003. A record already present is never
rewritten and a full snapshot is never written, so repository growth is
proportional to genuinely new postings rather than to board size.

**One file per source.** ADR-0020. `fetch-all/greenhouse.json`,
`fetch-all/lever.json`. A row's provenance is its filename, so no routing bug
can misfile a row into the wrong store. Aggregator sources write to local files
that are never committed to this repository, and the split is by directory so
that moving a source later is a file move rather than a transformation.
*(2026-09-24: ADR-0047 gives those files a private repository, which
`src/private_store.py` restores them from and pushes them to.)* That covers every store, not
only the raw one: an aggregator's filtered rows and seen-store entries are local
too, because a filtered row is a row and a seen entry carries the posting's URL
and publication date.

**The data branch is the store; `data/` is a working copy.** A GitHub runner
starts from an empty checkout, so a committing run first replaces its working
copies with the branch's. Without that, every run on a runner is first
contact: every posting new, first_seen re-dated, the history on the branch
replaced by one run's snapshot.

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

import base64
import os
import re
import shutil
import subprocess
import tempfile

from .normalise import dumps, loads

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_BRANCH = "data"
# A test run keeps production's layout inside its branch, which is exactly why
# it needs a branch of its own: on the same branch, test files land on
# production paths. `.github/workflows/fetch.yml` names both branches and a
# test holds them in step.
TEST_DATA_BRANCH = "data-test"

# The data branch is written by a machine, so its commits carry a fixed,
# non-personal identity rather than whatever the host has configured. A GitHub
# runner has none and commit-tree refuses to guess: run 35179218050 fetched
# 1239 postings and then died here with "Author identity unknown".
COMMIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "job-aggregator",
    "GIT_AUTHOR_EMAIL": "job-aggregator@invalid",
    "GIT_COMMITTER_NAME": "job-aggregator",
    "GIT_COMMITTER_EMAIL": "job-aggregator@invalid",
}

# Where the working copies live. One ignored directory rather than a scatter of
# files at the repository root, so `git status` shows the operator's work and
# not the pipeline's. The paths *inside* the data branch are unaffected: those
# are fixed by ADR-0020 and are produced by branch_path() below.
DATA_ROOT = "data"
TEST_SUBDIR = "test"          # a test run writes beside production, never over it

RAW_DIR = "fetch-all"
# ADR-0020: aggregator rows live here and never reach this repository.
# ADR-0047 pushes them to a private one, `src/private_store.py`.
LOCAL_RAW_DIR = "fetch-all-local"
# The same rule for the filtered layer and the seen store. A separate directory
# from LOCAL_RAW_DIR because that one is the raw layer's local twin and already
# holds data on the operator's machine.
LOCAL_DIR = "local"
FILTERED_FILE = "filtered.json"
SEEN_FILE = "seen.json"
RUNLOG_DIR = "logs-runs"
# ADR-0043's outcome stores. Written by the sweep, read by the projection's
# skip, so they are state and are restored with the rest.
OUTCOMES_DIR = "outcomes"

# What a committing run reads back from the branch before it starts. Run logs
# are history rather than state, so they are not restored.
RESTORED_FILES = (FILTERED_FILE, SEEN_FILE)
RESTORED_DIRS = (RAW_DIR, OUTCOMES_DIR)

# ADR-0047: aggregator-sourced stores live in a private repository, reached
# with a token. The run treats the repository's name as a secret: it comes from
# a repository secret and is scrubbed from every error. Documents may name it,
# by the operator's decision of 2026-09-23; run output never does.
PRIVATE_STORE_REPO_ENV = "AGGREGATOR_STORE_REPO"
PRIVATE_STORE_TOKEN_ENV = "AGGREGATOR_STORE_TOKEN"
PRIVATE_STORE_TIMEOUT = 120


class StorageError(Exception):
    pass


def data_root(test_mode=False):
    return "%s/%s" % (DATA_ROOT, TEST_SUBDIR) if test_mode else DATA_ROOT


def data_branch(test_mode=False):
    return TEST_DATA_BRANCH if test_mode else DATA_BRANCH


# The operator's D11, 2026-09-26: every field a board returns, descriptions
# included, is kept in the private repository, on a branch of its own so no
# run ever downloads what earlier runs saved. One file per run under FULL_DIR.
FULL_DIR = "full"


def full_branch(test_mode=False):
    return data_branch(test_mode) + "-full"


def layout(test_mode=False):
    """Every path the pipeline writes, in one place so a test run cannot
    accidentally inherit a production path."""
    root = data_root(test_mode)
    return {
        "root": root,
        "raw_dir": "%s/%s" % (root, RAW_DIR),
        "local_raw_dir": "%s/%s" % (root, LOCAL_RAW_DIR),
        "filtered": "%s/%s" % (root, FILTERED_FILE),
        "seen": "%s/%s" % (root, SEEN_FILE),
        "local_filtered": "%s/%s/%s" % (root, LOCAL_DIR, FILTERED_FILE),
        "local_seen": "%s/%s/%s" % (root, LOCAL_DIR, SEEN_FILE),
        "runlog_dir": "%s/%s" % (root, RUNLOG_DIR),
        "outcomes_dir": "%s/%s" % (root, OUTCOMES_DIR),
        # ADR-0047: the private repository's copies of the outcome stores,
        # restored beside the other aggregator working copies.
        "local_outcomes_dir": "%s/%s/%s" % (root, LOCAL_DIR, OUTCOMES_DIR),
    }


def branch_path(local_path, test_mode=False):
    """The path a local file takes inside the data branch.

    The branch layout is ADR-0020's and does not move just because the working
    copies were tidied into one directory: `fetch-all/greenhouse.json` on the
    branch, whatever the local tree looks like."""
    root = data_root(test_mode) + "/"
    return local_path[len(root):] if local_path.startswith(root) else local_path


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

    @classmethod
    def load_many(cls, paths):
        """One store from several files, for the committed and local halves."""
        store = cls()
        for path in paths:
            store.entries.update(cls.load(path).entries)
        return store

    def partition(self, publishable):
        """Two stores: entries whose source may be published, and the rest.

        The run partitions before it saves, so a seen file written before the
        split, which holds both classes, is corrected by the next run rather
        than carried."""
        public, local = SeenStore(), SeenStore()
        for identity, entry in self.entries.items():
            side = public if publishable(entry.get("source")) else local
            side.entries[identity] = entry
        return public, local

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
            # The board that first stored it, which sets that board's stop
            # mark. Only on a new entry: entries stored before 2026-09-26
            # carry none, and rewriting every one would change the whole file.
            self.entries[row.identity] = {
                "first_seen": row.first_seen,
                "published_at": row.published_at,
                "source": row.source,
                "board_id": row.board_id,
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

    def full_saved(self, identity):
        """Whether the posting's full record reached the private full branch
        and was read back (D11). Unset until then, so a posting whose save
        failed is saved again by the next run that still sees it listed."""
        return bool((self.entries.get(identity) or {}).get("full_saved_at"))

    def mark_full_saved(self, identity, when):
        entry = self.entries.get(identity)
        if entry is not None:
            entry["full_saved_at"] = when


# ------------------------------------------------------- the data branch
def _git(args, cwd=None, env=None, check=True, stdin=None):
    # REPO_ROOT is resolved on every call, never bound as a default. A default
    # is evaluated once at import, so a caller that repoints REPO_ROOT would
    # still have run against the original repository. A test did exactly that
    # and committed to the real one.
    cwd = cwd or REPO_ROOT
    full = dict(os.environ)
    full.update(env or {})
    # Bytes across the boundary, encoded and decoded here as UTF-8. Text mode
    # uses the locale's encoding and, on Windows, turns "\n" into "\r\n" on the
    # way in. On a cp1252 host a title outside cp1252 raised, and every blob
    # was written with CRLF endings in cp1252, while reading it back through
    # text mode undid both and the round-trip test passed.
    p = subprocess.run(["git"] + args, cwd=cwd, env=full,
                       input=None if stdin is None else stdin.encode("utf-8"),
                       capture_output=True)
    if check and p.returncode != 0:
        raise StorageError("git %s failed: %s"
                           % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout.decode("utf-8").strip()


def branch_exists(branch=DATA_BRANCH):
    p = subprocess.run(["git", "rev-parse", "--verify", "--quiet", branch],
                       cwd=REPO_ROOT, capture_output=True)
    return p.returncode == 0


def read_branch_file(path, branch=DATA_BRANCH):
    """Read one file from the branch without checking it out."""
    if not branch_exists(branch):
        return None
    # Bytes, for the reason given in _git: text mode would silently turn a
    # blob's "\r\n" into "\n" and hide a wrongly written blob.
    p = subprocess.run(["git", "show", "%s:%s" % (branch, path)],
                       cwd=REPO_ROOT, capture_output=True)
    return p.stdout.decode("utf-8") if p.returncode == 0 else None


def restore_from_branch(test_mode=False):
    """Replace the local working copies of the committed stores with the
    branch's. Returns the local paths written.

    The branch wins over a local file that exists, not only over a missing one.
    A local copy older than the branch, on a machine that has not run for a
    while, would otherwise be appended to and committed, deleting every record
    the branch gained in between. That is the snapshot failure ADR-0003 exists
    to prevent. With no branch there is nothing to restore and local files are
    left as they are."""
    branch = data_branch(test_mode)
    if not branch_exists(branch):
        return []
    listed = _git(["ls-tree", "-r", "--name-only", branch]).splitlines()
    wanted = [p for p in listed
              if p in RESTORED_FILES
              or any(p.startswith(d + "/") and p.endswith(".json") for d in RESTORED_DIRS)]
    root = data_root(test_mode)
    written = []
    for path in wanted:
        text = read_branch_file(path, branch)
        if text is None:
            raise StorageError("%s:%s is listed but could not be read" % (branch, path))
        local = "%s/%s" % (root, path)
        write_atomic(local, text)
        written.append(local)
    return written


def read_recent_run_logs(count, test_mode=False):
    """The last `count` run logs on the branch, oldest first, whatever month
    they fall in. For counting failures in a row across a month boundary."""
    branch = data_branch(test_mode)
    if count <= 0 or not branch_exists(branch):
        return []
    listed = sorted(p for p in _git(["ls-tree", "--name-only", branch, RUNLOG_DIR + "/"]).splitlines()
                    if p.endswith(".json"))
    logs = []
    for path in listed[-count:]:
        text = read_branch_file(path, branch)
        if text is None:
            raise StorageError("%s:%s is listed but could not be read" % (branch, path))
        logs.append(loads(text))
    return logs


def read_month_run_logs(yyyymm, test_mode=False):
    """This month's run logs from the branch, as dicts.

    Run logs are not restored, because they are history rather than state; a
    runner therefore holds none. The Airtable client's monthly budget needs
    the month so far, so it reads just these from the branch."""
    branch = data_branch(test_mode)
    if not branch_exists(branch):
        return []
    listed = _git(["ls-tree", "--name-only", branch, RUNLOG_DIR + "/"]).splitlines()
    logs = []
    for path in sorted(listed):
        if os.path.basename(path).startswith(yyyymm) and path.endswith(".json"):
            text = read_branch_file(path, branch)
            if text is None:
                raise StorageError("%s:%s is listed but could not be read" % (branch, path))
            logs.append(loads(text))
    return logs


# ------------------------------------------------- the private store
class PrivateStoreUnreachable(StorageError):
    """ADR-0047: the private store could not be reached at all, and a run that
    cannot reach it must fail visibly rather than proceed as though it held
    nothing. The message never names the repository or carries the token."""


def private_store_basic(token):
    """The Basic credential git sends for the private store. It decodes to the
    token, so anything that scrubs the token must scrub this too."""
    return base64.b64encode(("x-access-token:%s" % token).encode("utf-8")).decode("ascii")


def _scrub(text, secrets):
    for secret in secrets:
        if secret:
            text = re.sub(re.escape(secret), "<private>", text, flags=re.IGNORECASE)
    return text


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
        commit = _git(args, env=dict(env, **COMMIT_IDENTITY))
        _git(["update-ref", "refs/heads/%s" % branch, commit])
        return commit
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)
