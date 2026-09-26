"""The private aggregator store. ADR-0047.

An aggregator's rows may never reach the public data branch, and on a runner
the local files ADR-0020 kept them in die with the job: every production run
to 2026-09-24 fetched Himalayas as first contact and lost everything it kept.
ADR-0047 gives them a private repository holding exactly what an ATS row gets
on the public branch: the raw file, the seen entries, the filtered rows and
the outcome stores, at the same paths.

**The same discipline as the public branch.** ADR-0033: a committing run
restores its working copies from the store before it fetches, and appends to
what is stored rather than to whatever this machine holds. One branch per
mode, `data` and `data-test`, so a test run can never touch production's
private state, which is ADR-0033's own reason, in the private repository.
Nothing reads the repository's default branch: GitHub makes the first branch
pushed to an empty repository its default, so which one that is depends on
whether a test run or a scheduled one got there first.

**A run that could not restore never writes.** Writing after a failed restore
would replace the stored history with one run's snapshot, which is the failure
ADR-0003 exists to prevent. The run holds no store object after a failed
restore, so there is nothing to write with; `src/run.py` is where that is
tested.

**A push never overwrites.** It is a fast-forward from the commit read at
open, so a store that moved meanwhile refuses the push rather than losing
what moved it.

**The token never reaches an error.** It travels in an HTTP header on each
git call, errors carry git's exit code and a scrubbed stderr, and the
repository's name is scrubbed too, because this text can reach a run log on
the public branch.
"""

import os
import re
import shutil
import subprocess
import tempfile

from .storage import (COMMIT_IDENTITY, FILTERED_FILE, OUTCOMES_DIR, PRIVATE_STORE_REPO_ENV,
                      PRIVATE_STORE_TIMEOUT, PRIVATE_STORE_TOKEN_ENV, RAW_DIR, SEEN_FILE,
                      PrivateStoreUnreachable, _scrub, data_branch, full_branch,
                      private_store_basic, write_atomic)


def github_url(repo):
    return "https://github.com/%s.git" % repo


# ------------------------------------------------------------ the layout
def local_path_for(stored, paths):
    """Where a file on the private branch lives as a working copy, or None
    for a file the run does not restore. The branch uses ADR-0020's public
    layout; the working copies sit in the aggregator directories the run
    already reads and writes."""
    if stored == FILTERED_FILE:
        return paths["local_filtered"]
    if stored == SEEN_FILE:
        return paths["local_seen"]
    for directory, key in ((RAW_DIR, "local_raw_dir"), (OUTCOMES_DIR, "local_outcomes_dir")):
        prefix = directory + "/"
        if stored.startswith(prefix) and stored.endswith(".json") \
                and "/" not in stored[len(prefix):]:
            return "%s/%s" % (paths[key], stored[len(prefix):])
    return None


def files_to_push(paths):
    """The run's aggregator files, keyed by their path on the private branch:
    every raw file, the filtered rows, the seen entries, and the outcome
    stores the sweep writes for aggregator rows (ADR-0050)."""
    files = {}
    raw_dir = paths["local_raw_dir"]
    if os.path.isdir(raw_dir):
        for name in sorted(os.listdir(raw_dir)):
            if name.endswith(".json"):
                files["%s/%s" % (RAW_DIR, name)] = os.path.join(raw_dir, name)
    for stored, key in ((FILTERED_FILE, "local_filtered"), (SEEN_FILE, "local_seen")):
        if os.path.exists(paths[key]):
            files[stored] = paths[key]
    outcomes = paths["local_outcomes_dir"]
    if os.path.isdir(outcomes):
        for name in sorted(os.listdir(outcomes)):
            if name.endswith(".json"):
                files["%s/%s" % (OUTCOMES_DIR, name)] = os.path.join(outcomes, name)
    out = {}
    for stored, local in files.items():
        with open(local, encoding="utf-8") as f:
            out[stored] = f.read()
    return out


class PrivateStore:
    """One run's session with the private repository: open, restore, commit
    and push, close. Holds a scratch repository for the run's duration."""

    def __init__(self, repo, token, test_mode=False, run=subprocess.run, url_for=github_url,
                 timeout=PRIVATE_STORE_TIMEOUT):
        repo, token = (repo or "").strip(), (token or "").strip()
        if not repo or not token:
            raise PrivateStoreUnreachable(
                "%s or %s is empty or unset" % (PRIVATE_STORE_REPO_ENV, PRIVATE_STORE_TOKEN_ENV))
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) or repo.endswith(".git"):
            raise PrivateStoreUnreachable(
                "%s must be owner/name only: no scheme, no .git, no trailing slash"
                % PRIVATE_STORE_REPO_ENV)
        self.branch = data_branch(test_mode)
        self.full_branch = full_branch(test_mode)
        self._url = url_for(repo)
        basic = private_store_basic(token)
        self._secrets = (token, basic, repo)
        self._auth = ["-c", "credential.helper=",
                      "-c", "http.extraHeader=Authorization: Basic %s" % basic]
        self._run = run
        self._timeout = timeout
        self._env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        self._work = None
        # The branch's commit when opened, or None when it has none yet.
        self.tip = None

    # ------------------------------------------------------------ internals
    def _git(self, args, what, auth=False, stdin=None, env=None, check=True, cwd=None):
        full = dict(self._env, **(env or {}))
        try:
            p = self._run(["git"] + (self._auth if auth else []) + args, cwd=cwd or self._work,
                          env=full, capture_output=True, timeout=self._timeout,
                          input=None if stdin is None else stdin.encode("utf-8"))
        except subprocess.TimeoutExpired:
            raise PrivateStoreUnreachable("the private store timed out while %s" % what)
        if check and p.returncode != 0:
            detail = _scrub(p.stderr.decode("utf-8", "replace").strip(), self._secrets)
            raise PrivateStoreUnreachable("the private store failed while %s (git exit %d): %s"
                                          % (what, p.returncode, detail))
        return p

    def _out(self, *args, **kw):
        return self._git(*args, **kw).stdout.decode("utf-8").strip()

    # ----------------------------------------------------------------- read
    def open(self):
        """Reach the repository and fetch this mode's branch if it has one.
        Raises PrivateStoreUnreachable when it cannot be reached. A reachable
        repository without the branch holds nothing yet, which is not a
        failure: the first run's push creates it."""
        self._work = tempfile.mkdtemp(prefix="private-store-")
        self._git(["init", "-q"], "preparing a scratch repository")
        listing = self._out(["ls-remote", "--heads", self._url], "listing it", auth=True)
        ref = "refs/heads/%s" % self.branch
        if any(line.split("\t")[-1] == ref for line in listing.splitlines()):
            self._git(["fetch", "-q", "--depth", "1", "--no-tags", self._url,
                       "%s:%s" % (ref, ref)], "fetching its %s branch" % self.branch, auth=True)
            self.tip = self._out(["rev-parse", ref], "reading its tip")
        return self

    def paths(self):
        """Every file on this mode's branch; nothing when the branch is new."""
        if self.tip is None:
            return []
        return self._out(["ls-tree", "-r", "--name-only", self.tip],
                         "listing its files").splitlines()

    def read(self, path):
        if self.tip is None:
            return None
        p = self._git(["show", "%s:%s" % (self.tip, path)], "reading a file", check=False)
        return p.stdout.decode("utf-8") if p.returncode == 0 else None

    def restore(self, paths):
        """Replace the aggregator working copies with the branch's. Returns
        the local paths written. The branch wins over a local file that
        exists, for restore_from_branch's reason: a stale local copy appended
        to and pushed would delete what the store gained meanwhile. With no
        branch yet, local files are left as they are."""
        written = []
        for stored in self.paths():
            local = local_path_for(stored, paths)
            if local is None:
                continue
            text = self.read(stored)
            if text is None:
                raise PrivateStoreUnreachable(
                    "the private store lists %s but it could not be read" % stored)
            write_atomic(local, text)
            written.append(local)
        return written

    # ---------------------------------------------------------------- write
    def commit_and_push(self, files, message):
        """Commit `files` ({path: text}) on top of the fetched tip and push.
        Returns the new commit, or None when nothing changed."""
        # Unopened, there is no scratch repository, and git would write its
        # objects wherever the process stands: this repository, on a machine.
        if self._work is None:
            raise PrivateStoreUnreachable("the private store was written before it was opened")
        env = {"GIT_INDEX_FILE": os.path.join(self._work, ".private-index")}
        if self.tip:
            self._git(["read-tree", self.tip], "reading its tree", env=env)
        for path, text in sorted(files.items()):
            blob = self._out(["hash-object", "-w", "--stdin"], "storing a file", stdin=text)
            self._git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)],
                      "staging a file", env=env)
        tree = self._out(["write-tree"], "writing its tree", env=env)
        if self.tip and tree == self._out(["rev-parse", "%s^{tree}" % self.tip],
                                          "reading its tree"):
            return None
        args = ["commit-tree", tree, "-m", message] + (["-p", self.tip] if self.tip else [])
        commit = self._out(args, "committing", env=COMMIT_IDENTITY)
        self._git(["push", "-q", self._url, "%s:refs/heads/%s" % (commit, self.branch)],
                  "pushing", auth=True)
        self.tip = commit
        return commit

    def save_full(self, path, text, message):
        """Add one file to this mode's full branch and read it back. The
        operator's D11, 2026-09-26: every field a board returns is kept here,
        and "fetch back to recheck that the saving is done properly".

        **Nothing earlier runs saved is downloaded.** The branch is fetched
        without file contents (a partial fetch: commits and trees only), the
        new file is added on top of its tree, and the commit is pushed as a
        fast-forward. Measured on a local bare repository on 2026-09-26: a
        branch holding 270 KB came down as 1.4 KB.

        **The read-back is a second, fresh partial fetch** of the branch after
        the push. The branch must list `path` with exactly the hash of the
        bytes written, which git computes from the content, so a file the
        remote does not hold, or holds differently, is refused. Returns that
        hash. Uses its own scratch repository, so the data branch's is never
        made partial."""
        work = tempfile.mkdtemp(prefix="private-full-")
        try:
            def git(args, what, **kw):
                return self._git(args, what, cwd=work, **kw)

            def out(args, what, **kw):
                return git(args, what, **kw).stdout.decode("utf-8").strip()

            git(["init", "-q"], "preparing a scratch repository for the full branch")
            git(["remote", "add", "store", self._url], "naming the store")
            ref = "refs/heads/%s" % self.full_branch
            listing = out(["ls-remote", "--heads", "store"], "listing it", auth=True)
            tip = None
            if any(line.split("\t")[-1] == ref for line in listing.splitlines()):
                git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "--no-tags", "store",
                     "%s:%s" % (ref, ref)], "fetching the full branch's tree", auth=True)
                tip = out(["rev-parse", ref], "reading the full branch's tip")
            env = {"GIT_INDEX_FILE": os.path.join(work, ".full-index")}
            if tip:
                git(["read-tree", tip], "reading the full branch's tree", env=env)
            blob = out(["hash-object", "-w", "--stdin"], "storing the full file", stdin=text)
            git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)],
                "staging the full file", env=env)
            tree = out(["write-tree"], "writing the full branch's tree", env=env)
            args = ["commit-tree", tree, "-m", message] + (["-p", tip] if tip else [])
            commit = out(args, "committing the full file", env=COMMIT_IDENTITY)
            git(["push", "-q", "store", "%s:%s" % (commit, ref)], "pushing the full file",
                auth=True)
            git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "--no-tags", "store",
                 "%s:refs/remotes/readback" % ref], "reading the full branch back", auth=True)
            listed = out(["ls-tree", "refs/remotes/readback", "--", path],
                         "listing the file read back")
            held = listed.split()[2] if len(listed.split()) >= 3 else None
            if held is None:
                raise PrivateStoreUnreachable(
                    "the full branch, read back after the push, does not list %s" % path)
            if held != blob:
                raise PrivateStoreUnreachable(
                    "the full branch, read back after the push, holds different content "
                    "for %s than was written" % path)
            return blob
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def close(self):
        if self._work:
            shutil.rmtree(self._work, ignore_errors=True)
            self._work = None
