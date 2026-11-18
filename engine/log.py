"""video_log/: one JSON record per render + a CSV index for quick browsing."""
import csv
import datetime
import glob
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(ROOT, "video_log")
INDEX = os.path.join(LOG_DIR, "index.csv")
INDEX_FIELDS = ["id", "date", "family", "format", "seed", "duration_s", "params_file", "git_commit",
                "summary", "published_url", "views", "ctr", "avg_view_pct", "notes"]


# Each engine numbers its renders separately: BL = Bright Lights (ring_bounce, pendulum_wave,
# lava_lamp, races), FE = Foundry Engine, SG = Sandglass, CR = Chain Reaction, FK = Forest Keepers (the
# monster series, its own engine from episode 4; episodes 1-3 are FE0008-FE0014), TW = Tiny World
# (docs/engines/tiny_world.md), SK = Deep Sky (sleep loops; not DS, see below), SX = Space Explained
# (docs/engines/space_explained.md), PR = Photoreal (Blender Cycles, experiments/photoreal/), KS = Kaleidoscope
# (psychedelic long-form, docs/engines/kaleidoscope.md), SN = Snow Globe (cozy Christmas spot-the-change ambience,
# docs/engines/cozy_christmas.md), FL = faithlocket "Reformed Readings" (its own channel, docs/engines/faithlocket.md). Keeps parallel sessions on
# different engines from colliding. (Bright Lights renders before 2026-10-25 were DS####; records keep `former_id`.)
PREFIXES = {"foundry": "FE", "sandglass": "SG", "chain_reaction": "CR", "keepers": "FK", "tiny_world": "TW",
            "deep_sky": "SK", "space_explained": "SX", "photoreal": "PR", "kaleidoscope": "KS",
            "curiosity": "CU", "snow_globe": "SN", "faithlocket": "FL"}


def prefix(family):
    return PREFIXES.get(family, "BL")


def id_block():
    """This machine's ID block (docs/RENDER_MACHINES.md): 0 on the main PC (numbers 1-9999), or 10000, 20000, ...
    on a helper PC (numbers block..block+9999). Set by DS_ID_BLOCK or a git-ignored `.id_block` file in the repo
    root, so machines rendering at the same time never pick the same number."""
    v = os.environ.get("DS_ID_BLOCK")
    if not v and os.path.exists(os.path.join(ROOT, ".id_block")):
        v = open(os.path.join(ROOT, ".id_block")).read().strip()
    return int(v) if v else 0


def taken_elsewhere(pre):
    """Record names (without .json) with this prefix in the other checkouts of the repo: every git worktree's
    video_log and origin/main's (Local Ops 2026-11-06: in a worktree next_id only saw its own video_log, so two
    sessions could pick the same number). Best effort: no git, no extra names."""
    names = set()
    try:
        out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=ROOT, capture_output=True, text=True,
                             timeout=20).stdout
        for line in out.splitlines():
            if line.startswith("worktree "):
                d = os.path.join(line[9:].strip(), "video_log")
                names.update(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(d, f"{pre}*.json")))
        out = subprocess.run(["git", "ls-tree", "--name-only", "origin/main", "video_log/"], cwd=ROOT,
                             capture_output=True, text=True, timeout=20).stdout
        names.update(os.path.basename(f)[:-5] for f in out.split() if os.path.basename(f).startswith(pre)
                     and f.endswith(".json"))
    except (OSError, subprocess.SubprocessError):
        pass
    return names


def next_id(family, name=None):
    """Reserve the next ID by creating its record file exclusively (safe for parallel renders).
    The ID is `<prefix><number>_<name>`; `name` (params `name:`, e.g. "monsters", "gokarts") defaults to
    the family. Numbers are per engine and per machine block (see id_block), and the name keeps file
    names distinct as well."""
    os.makedirs(LOG_DIR, exist_ok=True)
    pre = prefix(family)
    block = id_block()
    lo, hi = (block, block + 9999) if block else (1, 9999)
    elsewhere = taken_elsewhere(pre)
    while True:
        here = [os.path.basename(f)[:-5] for f in glob.glob(os.path.join(LOG_DIR, f"{pre}*.json"))]
        nums = [n for f in set(here) | elsewhere
                if (m := re.match(rf"{pre}(\d+)", f)) and lo <= (n := int(m.group(1))) <= hi]
        vid = f"{pre}{(max(nums) + 1 if nums else lo):04d}_{name or family}"
        try:
            fd = os.open(os.path.join(LOG_DIR, f"{vid}.json"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w") as f:
            json.dump({"id": vid, "family": family, "status": "rendering"}, f)
        return vid


def git_state():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "engine", "families", "audio"],
                               cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return h + ("-dirty" if dirty else "")
    except OSError:
        return "unknown"


def write(record):
    record = dict(record)
    record["date"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    record.setdefault("git_commit", git_state())
    record.setdefault("metrics", {"published_url": None, "views": None, "ctr": None, "avg_view_pct": None})
    with open(os.path.join(LOG_DIR, f"{record['id']}.json"), "w") as f:
        json.dump(record, f, indent=2, default=str)
    new = not os.path.exists(INDEX)
    with open(INDEX, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS, extrasaction="ignore", lineterminator="\n")
        if new:
            w.writeheader()
        row = {k: record.get(k) for k in INDEX_FIELDS}
        row["summary"] = record.get("stats", {}).get("summary", "")
        w.writerow(row)
    return record


def repair_index():
    """Fix index.csv after a git merge: drop conflict markers, keep one row per ID, sort by ID.

    Both sessions append to this file, so merges often conflict on its last lines.
        python -m engine.log --repair-index
    """
    import io
    with open(INDEX, newline="", encoding="utf-8") as f:
        raw = f.read().replace("\r\n", "\n")
    lines = [l for l in raw.split("\n") if l and not l.startswith(("<<<<<<<", "=======", ">>>>>>>"))]
    rows = {}
    for r in csv.DictReader(io.StringIO("\n".join(lines))):
        if r.get("id") and r["id"] != "id":
            # keep the most informative copy of a row (e.g. the one with a published URL)
            old = rows.get(r["id"])
            if old is None or sum(bool(v) for v in r.values()) >= sum(bool(v) for v in old.values()):
                rows[r["id"]] = r
    key = lambda i: (i[:2], int(re.match(r"[A-Z]+(\d+)", i).group(1)))
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for i in sorted(rows, key=key):
            w.writerow(rows[i])
    return sorted(rows, key=key)


if __name__ == "__main__":
    import sys
    if "--repair-index" in sys.argv:
        print(" ".join(repair_index()))
