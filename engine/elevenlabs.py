"""ElevenLabs API access (ported from science-animations; Space Explained narration, docs/engines/space_explained.md).

The key lives in the git-ignored secrets/elevenlabs_key.txt of the main checkout (C:\\Projects\\dissociate-state),
also when the code runs from a git worktree. Credits are shared with the biology channel - estimate before a batch.

    .venv\\Scripts\\python.exe -m engine.elevenlabs --check   # key works? plan + credits left (never prints the key)
"""
import argparse
import os
import subprocess
import sys

import requests

from .log import ROOT

API = "https://api.elevenlabs.io/v1"


def shared_root():
    """The main checkout: secrets and the narration cache live there once, whichever worktree runs the code."""
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip()
        if common and os.path.basename(common) == ".git":
            return os.path.dirname(common)
    except OSError:
        pass
    return ROOT


KEY_FILE = os.path.join(shared_root(), "secrets", "elevenlabs_key.txt")


def api_key():
    try:
        with open(KEY_FILE, encoding="utf-8") as f:
            key = f.read().strip()
    except FileNotFoundError:
        key = ""
    if not key:
        sys.exit(f"No ElevenLabs key in {KEY_FILE} - paste it there (one line) and save.")
    return key


def get(path, **params):
    r = requests.get(f"{API}{path}", headers={"xi-api-key": api_key()}, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def credits():
    """-> (used, limit) this billing period."""
    sub = get("/user/subscription")
    return sub.get("character_count"), sub.get("character_limit")


def check():
    try:
        sub = get("/user/subscription")
    except requests.HTTPError as e:
        sys.exit(f"Key rejected: HTTP {e.response.status_code} {e.response.text[:200]}")
    used, limit = sub.get("character_count"), sub.get("character_limit")
    print(f"key OK - plan: {sub.get('tier')}, credits used {used:,} of {limit:,} this period, "
          f"status: {sub.get('status')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    if ap.parse_args().check:
        check()
