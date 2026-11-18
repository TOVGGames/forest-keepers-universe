"""talkcheck: the talking format's rules, checked frame by frame before a chapter is rendered (handoff 2026-11-17).

A chapter's plan gives, for every frame, each Keeper's state in WORLD units (before any close-up zoom):
    {"who": {"x": .., "y": feet on the ground, "k": size, "lift": px off the ground (a hop or Glo floating),
             "talk": mouth 0..1, "holding": None or what is in its hand}}
plus the cues (each line's who/start/end), the cuts (times where the shot or place changes), the place's scale_at(y)
and the music mask (1 = music down). Every check returns a list of problems; all must be empty.

1. nothing is picked up or put down: `holding` never changes within a chapter
2. no one travels away from the camera: a Keeper's feet never move up the frame (y decreasing) while it travels
3. size comes from where the feet are: k == scale_at(y) (within 2 %)
4. no warping: no jump between frames except at a cut, and a cut keeps everyone where they were
5. mouths: only open inside the speaker's own lines (+ the slow close), and still moving until the line's sound ends
6. music: fully down for the whole of every conversation (no rise between lines)
"""
from .mix import conversations, LEAD

FLOAT = {"glo"}                 # Glo floats: her lift is her height above the ground, not a hop


def _pairs(frames):
    return zip(frames, frames[1:])


def holding(frames):
    out = []
    for (t0, a), (t1, b) in _pairs(frames):
        for who in a.keys() & b.keys():
            if a[who].get("holding") != b[who].get("holding"):
                out.append(f"{t1:.2f}s {who}: holding {a[who].get('holding')} -> {b[who].get('holding')}")
    return out


def direction(frames, cuts, tol=0.25):
    out = []
    for (t0, a), (t1, b) in _pairs(frames):
        if any(t0 < c <= t1 for c in cuts):
            continue
        for who in a.keys() & b.keys():
            dy = b[who]["y"] - a[who]["y"]
            if dy < -tol:
                out.append(f"{t1:.2f}s {who}: feet moved {-dy:.1f} px up the frame (away from the camera)")
    return out


def size(frames, scale_at, tol=0.02):
    out = []
    for t, st in frames:
        for who, s in st.items():
            want = scale_at(s["y"])
            if abs(s["k"] - want) > tol * want:
                out.append(f"{t:.2f}s {who}: size {s['k']:.3f}, its feet at y {s['y']:.0f} say {want:.3f}")
    return out


def warping(frames, cuts, fps, max_speed=900.0):
    """max_speed: px/s in world units (a hop's flight included)."""
    out = []
    for (t0, a), (t1, b) in _pairs(frames):
        for who in a.keys() & b.keys():
            d = ((b[who]["x"] - a[who]["x"]) ** 2 + (b[who]["y"] - a[who]["y"]) ** 2) ** 0.5
            if any(t0 < c <= t1 for c in cuts):
                if d > 0.5:
                    out.append(f"cut at {t1:.2f}s: {who} moved {d:.1f} px across it")
            elif d > max_speed / fps:
                out.append(f"{t1:.2f}s {who}: jumped {d:.1f} px in one frame")
        if a.keys() != b.keys() and not any(t0 < c <= t1 for c in cuts):
            out.append(f"{t1:.2f}s: {sorted(a.keys() ^ b.keys())} appeared or vanished without a cut")
    return out


def mouths(frames, cues, said=None):
    """said(who, t) -> True while that speaker's line is actually sounding (from the voice track), if known."""
    out = []
    for t, st in frames:
        for who, s in st.items():
            if who == "glo":
                continue                                # no mouth: she talks with her lantern
            own = [c for c in cues if c["who"] == who and c["start"] - LEAD.get(who, 0.04) - 0.03 <= t <= c["end"] + 0.4]
            if s.get("talk", 0.0) > 0.05 and not own:
                out.append(f"{t:.2f}s {who}: mouth open ({s['talk']:.2f}) outside its own lines")
            if said is not None and said(who, t) and s.get("talk", 0.0) <= 0.02:
                inside = [c for c in cues if c["who"] == who and c["start"] + 0.15 <= t <= c["end"] - 0.15]
                if inside:
                    out.append(f"{t:.2f}s {who}: its line is sounding but its mouth is shut")
    return out


def music(mask, cues, sr):
    out = []
    for a, b in conversations(cues):
        seg = mask[int(a * sr):int(b * sr)]
        if len(seg) and seg.min() < 0.999:
            out.append(f"music rises inside the conversation {a:.1f}-{b:.1f}s (mask down to {seg.min():.2f})")
    return out


def run(frames, cues, cuts, scale_at, fps, mask=None, sr=44100, said=None):
    """All checks; prints a summary and returns the number of problems (0 = pass)."""
    groups = {"holding": holding(frames), "direction": direction(frames, cuts), "size": size(frames, scale_at),
              "warping": warping(frames, cuts, fps), "mouths": mouths(frames, cues, said)}
    if mask is not None:
        groups["music"] = music(mask, cues, sr)
    total = 0
    for name, probs in groups.items():
        total += len(probs)
        print(f"talkcheck {name}: {len(probs)}")
        for p in probs[:12]:
            print("   ", p)
    print(f"talkcheck TOTAL {total}")
    return total
