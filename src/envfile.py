"""Load `.env` for a local run. Standard library only.

A runner receives its secrets from the workflow; a laptop has none, so a local
committing run would fail its projection for want of a token. `.env` holds
them locally. It is gitignored, and `.env.example` lists the names with empty
values.

**What is already set wins.** A variable present in the environment is never
replaced by the file, so a runner, which sets every secret, behaves the same
whether or not a `.env` exists. Nothing here prints a value.
"""

import os


def parse(text):
    """NAME=value lines. Blank lines and # comments are skipped, an `export `
    prefix is allowed, and one pair of matching quotes around a value is
    removed. A line with no = is ignored rather than guessed at."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or not name:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[name] = value
    return values


def load(path=".env", environ=None):
    """Set every name the file holds that the environment does not. Returns
    the names set, never their values. A missing file does nothing."""
    environ = os.environ if environ is None else environ
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return []
    loaded = []
    for name, value in parse(text).items():
        if name not in environ:
            environ[name] = value
            loaded.append(name)
    return loaded
