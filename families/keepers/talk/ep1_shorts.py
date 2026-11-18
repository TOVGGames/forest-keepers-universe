"""Forest Keepers ep 1 (talk format): three upright teaser Shorts (1080x1920) cut from chapters 1, 3 and 5 of the
approved long FK0027 "How the Forest Keepers Began" (owner 2026-11-17: "we're going to publish it as is").

Each Short is the chapter's own animation and voices, re-framed for an upright screen: the world stays 1920x1080, the
camera is a view into it (zoom >= 1.78 so the scenery covers the tall page). Every framing change is a cut, made only
while nobody is moving, and every Keeper is wholly in or wholly out of each shot (checked). A hook title at the top
for the first seconds; at the end the picture fades out (owner, FK0027 notes: fade, don't watch a Keeper walk off)
and a card points to the full episode. A series Short is a teaser with its own small payoff (owner 2026-11-01).

    .venv\\Scripts\\python.exe -m families.keepers.talk.ep1_shorts --check
    .venv\\Scripts\\python.exe -m families.keepers.talk.ep1_shorts --stills a [b c]
    .venv\\Scripts\\python.exe -m families.keepers.talk.ep1_shorts --render a [b c]
"""
import os
import subprocess
import sys
import time

import numpy as np
import skia

from families.keepers.talk import anim, places
from families.keepers.talk import ep1_film as E
from families.keepers.talk.anim import FPS, HALF, TALL, rrect, text
from families.keepers.talk.mix import SR, ease

PW, PH = 1080, 1920
ZMIN = 1.78                               # just over 1920/1080: the world's full height fills the page
CARD = 3.2                                # the end card, after the picture fades
FADE = 1.0


def frame_on(ch, t, keep, zoom=None, at=1640.0, cx=None, margin=34.0):
    """An upright view on the Keepers in `keep` as they stand at chapter time t: centred on them (or at cx), as close
    as fits (or `zoom`), their feet near screen y `at`."""
    ext = []
    for w in keep:
        s = ch.actors[w].pos(t)
        h = HALF[w] * places.scale_at(s["y"])
        ext.append((s["x"] - h, s["x"] + h, s["y"]))
    lo, hi = min(e[0] for e in ext), max(e[1] for e in ext)
    Z = zoom or max(ZMIN, min(2.6, (PW - 2 * margin) / (hi - lo)))
    cx = (lo + hi) / 2 if cx is None else cx
    return view(Z, cx, sum(e[2] for e in ext) / len(ext), at)


def view(Z, cx, cy, at):
    """zoom Z about world (cx, cy), that point at page (540, at); clamped so the scenery covers the page."""
    assert Z >= ZMIN - 1e-6, Z
    cx = min(max(cx, 540.0 / Z), places.W - 540.0 / Z)
    sy = min(max(at, PH - (places.H - cy) * Z), cy * Z)
    return dict(zoom=float(Z), cx=float(cx), cy=float(cy), sx=540.0, sy=float(sy))


class Short:
    """One Short: chapter n of the episode from t0 to t1 (chapter time), framings [(t, view or callable)], a hook."""

    def __init__(self, key, name, n, t0, t1, hook, plan):
        self.key, self.name, self.n, self.t0, self.t1, self.hook = key, name, n, t0, t1, hook
        self.ch = E.CHAPTERS[n - 1](n, E.VOICES, f"ep1_ch{n}")
        self.shots = [(t, v(self.ch, t) if callable(v) else v) for t, v in plan(self.ch)]
        assert self.shots[0][0] <= t0
        self.pic = t1 - t0                                      # the picture; then the end card
        self.dur = self.pic + CARD

    def cam(self, t):
        v = self.shots[0][1]
        for t0, s in self.shots:
            if t >= t0:
                v = s
        return v

    def cuts(self):
        return [t for t, _ in self.shots if self.t0 < t < self.t1]

    def frame(self, u):
        if u >= self.pic:
            pg = anim.flat.FlatPage(PW, PH)
            pg.c.drawPaint(skia.Paint(Color=skia.Color(250, 244, 234)))
        else:
            t = self.t0 + u
            v = self.cam(t)
            self.ch.oak_light = bool(v.get("oak"))
            pg = self.ch.frame(t, camera={k: v[k] for k in ("zoom", "cx", "cy", "sx", "sy")}, page=(PW, PH))
            a = ease(u, 0.2, 0.7) * (1 - ease(u, 3.6, 4.3))
            if a > 0.01:
                self.title(pg, self.hook, 250, 70, a)
            f = ease(u, self.pic - FADE, self.pic)
            if f > 0.001:
                pg.c.drawPaint(skia.Paint(Color=skia.Color(250, 244, 234, int(255 * f))))
        a = ease(u, self.pic - 0.3, self.pic + 0.5)
        if a > 0.01:
            text(pg, "Watch the full episode", PW / 2, 860, 54, a=a, weight="Medium")
            self.title(pg, "How the Forest Keepers Began", 1010, 62, a)
        return pg.finish()

    @staticmethod
    def title(pg, s, y, size, a):
        """A cream pill with the text, held still in screen space (smaller type if it would not fit)."""
        while anim.font(size).measureText(s) > PW - 220:
            size -= 2
        w = anim.font(size).measureText(s) + 80
        x0 = PW / 2 - w / 2
        pg.flat(rrect(x0 + 6, y - size - 34, x0 + w + 6, y + 40, 32), (40, 28, 24), 0.18 * a, blur=12)
        pg.flat(rrect(x0, y - size - 42, x0 + w, y + 32, 32), anim.PAPER, 0.94 * a)
        text(pg, s, PW / 2, y, size, a=a)

    # ------------------------------------------------------------------------------------------------- sound
    def audio(self, path):
        from scipy.io import wavfile
        from scipy.signal import butter, sosfilt
        from families.curiosity.sfx import generate, load
        from families.keepers.talk import mix as MX
        from families.keepers.talk.ep1 import SFX
        n = int((self.dur + 0.5) * SR)
        i0, i1 = int(self.t0 * SR), int(self.t1 * SR)
        v = np.zeros(n, np.float32)
        seg = self.ch.voices[i0:i1]
        v[:len(seg)] = seg
        fx = np.zeros(n, np.float32)
        lib = {}
        for name, (prompt, sec) in SFX.items():
            a = load(generate(prompt, sec))                      # cached: no new ElevenLabs credits
            a = sosfilt(butter(2, [250, 6500], btype="band", fs=SR, output="sos"), a).astype(np.float32)
            fr = np.array([np.sqrt(np.mean(a[j:j + 882] ** 2)) for j in range(0, len(a) - 882, 882)])
            act = fr[fr > 0.25 * fr.max()]
            lib[name] = a / (np.sqrt(np.mean(act ** 2)) + 1e-9) * 0.085
        for t, name, g in self.ch.sfx:
            if self.t0 <= t < self.t1:
                a = lib[name] * g
                i = int((t - self.t0) * SR)
                fx[i:i + len(a)] += a[:max(0, n - i)]
        for ta, tb, name, g in self.ch.loops:
            ta, tb = max(ta, self.t0), min(tb, self.t1, self.ch.dur)
            if tb > ta:
                a = lib[name]
                ia, ib = int((ta - self.t0) * SR), int((tb - self.t0) * SR)
                s = np.tile(a, (ib - ia) // len(a) + 2)[:ib - ia] * g
                ramp = np.minimum(1, np.minimum(np.arange(len(s)), np.arange(len(s))[::-1]) / (1.2 * SR))
                fx[ia:ib] += s * ramp
        out_fade = np.clip((self.pic - np.arange(n) / SR) / FADE, 0, 1).astype(np.float32)   # with the picture
        voice = (v + fx) * out_fade
        cues = [dict(c, start=c["start"] - self.t0, end=c["end"] - self.t0) for c in self.ch.cues
                if self.t0 <= c["start"] and c["end"] <= self.t1]
        theme_path = os.path.join(E.VOICES, f"ep1_short_{self.key}_theme.wav")
        _, chords, folded = MX.theme(self.dur, theme_path)
        music = E._stereo(theme_path, n)
        end = np.clip((self.dur - np.arange(n) / SR) / 1.5, 0, 1).astype(np.float32)
        music = music * end[:, None]
        out, mask = MX.mix(np.stack([voice, voice], 1), music, cues)
        wavfile.write(path, SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
        return mask, folded, cues

    # ------------------------------------------------------------------------------------------------- checks
    def check(self, mask=None, cues=None):
        from families.keepers.talk import check as TC
        ch = self.ch
        print(f"--- Short {self.key} {self.name}: chapter {self.n} {self.t0:.1f}-{self.t1:.1f} s ({self.dur:.1f} s)")
        ts = np.arange(self.t0, self.t1, 1 / FPS)
        frames = [(t, ch.state(t)) for t in ts]
        env = ch.mouths.env

        def said(who, t):
            return any(c["who"] == who and c["start"] <= t <= c["end"] for c in ch.cues) and \
                env[min(int(t * FPS), len(env) - 1)] > 0.25
        total = TC.run(frames, [c for c in ch.cues if self.t0 <= c["start"] < self.t1], self.cuts(),
                       places.scale_at, FPS, said=said)
        moving_at_cut = []
        for c in self.cuts():                                   # cuts only while nobody moves
            for w, a in ch.actors.items():
                p, q = a.pos(c - 0.2), a.pos(c + 0.2)
                if abs(p["x"] - q["x"]) + abs(p["y"] - q["y"]) + abs(p["lift"] - q["lift"]) > 0.5:
                    moving_at_cut.append(f"{c:.1f}s {w} moving at the cut")
        print(f"cuts while moving: {len(moving_at_cut)}")
        for p in moving_at_cut:
            print("   ", p)
        ec = self.edge_crops()
        print(f"edge crops: {len(ec)}")
        for p in ec[:10]:
            print("   ", p)
        total += len(moving_at_cut) + len(ec)
        if mask is not None:
            mp = TC.music(mask, cues, SR)
            print(f"music: {len(mp)}")
            total += len(mp)
        print(f"SHORT CHECK TOTAL {total}")
        return total

    def edge_crops(self, hold=0.5, step=0.1):
        """A Keeper partly in shot while standing still (more than `hold` s), on the upright page."""
        out, run = [], {}
        t = self.t0
        while t < self.t1:
            v = self.cam(t)
            Z = v["zoom"]
            for w, a in self.ch.actors.items():
                s, s2 = a.pos(t), a.pos(min(t + step, self.t1))
                moving = abs(s2["x"] - s["x"]) + abs(s2["y"] - s["y"]) > 0.5
                X = (s["x"] - v["cx"]) * Z + v["sx"]
                Y = (s["y"] - v["cy"]) * Z + v["sy"]
                half = HALF[w] * places.scale_at(s["y"]) * Z
                below = Y - TALL[w] * half >= PH
                cut = not below and ((X - half < 0 < X + half) or (X - half < PW < X + half))
                if cut and not moving:
                    run.setdefault(w, t)
                    if t - run[w] >= hold and all((w, run[w]) != (o[0], o[1]) for o in out):
                        out.append((w, run[w], X))
                else:
                    run.pop(w, None)
            t += step
        return [f"{t0:.1f}s {w} cut by the frame edge (page x {X:.0f})" for w, t0, X in out]


# ===================================================================================================== the three
def short_a():
    """Chapter 1: the old oak, then the little acorn under the leaves as the sun reaches it and it wakes. Payoff: it
    wakes, finds the leaves on its head, asks what it is; a croak - "Somebody's down there!" - and fade."""
    def plan(ch):
        c = ch.c
        ox = places.OAK[0]
        return [(0.0, view(ZMIN, ox + 40, 600.0, 960.0)),                                  # the old oak, whole
                (c(0)["end"] - 3.6, lambda ch, t: frame_on(ch, t, ["sprout"], zoom=2.3, at=1600)),   # the acorn
                (c(5)["start"] - 0.3, lambda ch, t: frame_on(ch, t, ["sprout"], zoom=2.9, at=1520))]  # "I'm awake."
    return dict(key="a", name="acorn_wakes", n=1, hook="THE LITTLE ACORN WAKES UP",
                span=lambda ch: (ch.c(0)["start"] - 0.4, ch.c(6)["end"] + 0.5 + FADE), plan=plan)


def short_b():
    """Chapter 3: Digs, who can't see well in daylight, smells the old oak on Sprout. Payoff: "So... I'm a tree?" -
    "A very little one. With feet." Ends on Sprout's worry and Digs' "...Huh." (the episode answers it)."""
    def plan(ch):
        c = ch.c
        digs = lambda ch, t: frame_on(ch, t, ["digs"], zoom=2.3)
        pair = lambda ch, t: frame_on(ch, t, ["sprout", "springs"])
        return [(0.0, view(1.9, 1504.0, 985.0, 1640.0)),                                   # Digs, waking
                (c(1)["end"] + 0.35, lambda ch, t: frame_on(ch, t, ["sprout"], zoom=2.2)),     # "I'm Sprout."
                (c(3)["start"] - 0.3, digs),                                               # moles; "come closer"
                (c(6)["start"] - 0.3, pair),                                               # "The big one?"
                (c(7)["start"] - 0.3, digs),
                (c(8)["start"] - 0.3, pair),
                (c(9)["start"] - 0.3, digs),
                (c(10)["start"] - 0.3, lambda ch, t: frame_on(ch, t, ["sprout"], zoom=3.1, at=1580)),  # "a tree?"
                (c(11)["start"] - 0.3, digs),
                (c(12)["start"] - 0.3, pair),                                              # "A tree with feet!"
                (c(14)["start"] - 0.3, digs)]                                              # "...Huh."
    return dict(key="b", name="what_am_i", n=3, hook="WHAT AM I?",
                span=lambda ch: (0.8, ch.c(14)["end"] + 1.6 + FADE), plan=plan)


def short_c():
    """Chapter 5, night under the old oak: "Look up, Sprout. What do you see?" - who lives in the oak. Payoff: "So
    maybe... a squirrel planted me?" and Glo's secret."""
    oak = dict(view(2.1, 350.0, 550.0, 960.0), oak=True)                              # nest, squirrel, moths

    def plan(ch):
        c = ch.c
        glo = lambda ch, t: view(2.6, 852.0 - 540 / 2.6, 955.0, 1640.0)    # Glo; the squirrel's hole just out
        pair = lambda ch, t: frame_on(ch, t, ["springs", "sprout"], zoom=1.9)       # Glo and Digs just out
        digs = lambda ch, t: frame_on(ch, t, ["digs"], zoom=2.7)
        return [(0.0, glo),                                                              # "Look up, Sprout."
                (c(3)["start"] - 0.3, oak),
                (c(4)["start"] - 0.3, digs),                                             # its roots
                (c(5)["start"] - 0.3, pair),                                             # leaves in the pond
                (c(6)["start"] - 0.3, glo),                                              # "I rest on its branches"
                (c(7)["start"] - 0.3, oak),                                              # home to hundreds
                (c(8)["start"] - 0.3, pair),
                (c(9)["start"] - 0.3, glo),
                (c(11)["start"] - 0.3, oak),                                             # jays and squirrels
                (c(12)["start"] - 0.3, pair),                                            # "a squirrel planted me?"
                (c(15)["start"] - 0.3, glo)]                                             # "That's my secret."
    return dict(key="c", name="who_lives_in_the_oak", n=5, hook="WHO LIVES IN THE OAK?",
                span=lambda ch: (ch.c(2)["start"] - 0.5, min(ch.dur, ch.c(15)["end"] + 1.2 + FADE)), plan=plan)


SPECS = {s()["key"]: s for s in (short_a, short_b, short_c)}


def make(key):
    sp = SPECS[key]()
    ch = E.CHAPTERS[sp["n"] - 1](sp["n"], E.VOICES, f"ep1_ch{sp['n']}")
    t0, t1 = sp["span"](ch)
    return Short(key, sp["name"], sp["n"], t0, t1, sp["hook"], sp["plan"])


# ===================================================================================================== render
_S = None


def _work(args):
    global _S
    key, i = args
    if _S is None or _S.key != key:
        _S = make(key)
    return _S.frame(i / FPS).tobytes()


def render(key, workers=8):
    import multiprocessing as mp
    from engine import log
    from families.keepers.talk.voices import ffmpeg
    E._idle()
    s = make(key)
    vid = log.next_id("keepers", s.name)
    wav = os.path.join(E.VOICES, f"{vid}_mix.wav")
    mask, folded, cues = s.audio(wav)
    assert s.check(mask, cues) == 0, "the Short's checks must be 0 before rendering"
    out = os.path.join(E.FINAL_DIR, f"{vid}.mp4")
    n = int(round(s.dur * FPS))
    p = subprocess.Popen([ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{PW}x{PH}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{s.dur:.3f}",
                          "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    E._idle(p.pid)
    t0 = time.time()
    with mp.Pool(workers, initializer=E._init, initargs=(True,)) as pool:
        for i, buf in enumerate(pool.imap(_work, [(key, i) for i in range(n)], chunksize=8)):
            p.stdin.write(buf)
            if i % 300 == 0:
                print(f"{key}: frame {i}/{n}  {time.time() - t0:.0f} s", flush=True)
    p.stdin.close()
    p.wait()
    log.write(dict(id=vid, family="keepers", status="rendered", file=out, format="short", seed=0,
                   duration_s=round(s.dur, 2), params_file="families/keepers/talk/ep1_shorts.py",
                   title=s.hook, params=dict(short=key, chapter=s.n, span=[round(s.t0, 2), round(s.t1, 2)],
                                             shots=[(round(t, 2), {k: round(x, 2) for k, x in v.items()
                                                                   if k != "oak"}) for t, v in s.shots],
                                             teaser_for="FK0027_keepers_began", fps=FPS, size=[PW, PH]),
                   stats=dict(duration=round(s.dur, 2), audio_folded_notes=len(folded),
                              summary=f"FK talk ep 1 teaser Short {key}: chapter {s.n}, {s.dur:.1f} s")))
    print("WROTE", out, f"{s.dur:.1f} s in {time.time() - t0:.0f} s")
    return out


def stills(key, out_dir, every=None):
    from PIL import Image
    s = make(key)
    os.makedirs(out_dir, exist_ok=True)
    ts = sorted({0.1, 2.0} | {max(0.0, t - s.t0 + 0.6) for t, _ in s.shots} | {s.pic - 0.5, s.pic + 1.5})
    tiles = [Image.fromarray(s.frame(u)).resize((360, 640)) for u in ts]
    from PIL import ImageDraw
    cols = 6
    sh = Image.new("RGB", (360 * cols, 640 * ((len(tiles) + cols - 1) // cols)), "white")
    for j, (u, im) in enumerate(zip(ts, tiles)):
        sh.paste(im, ((j % cols) * 360, (j // cols) * 640))
        ImageDraw.Draw(sh).text(((j % cols) * 360 + 6, (j // cols) * 640 + 6), f"{key} {u:.1f}s", fill="black")
    p = os.path.join(out_dir, f"short_{key}_sheet.png")
    sh.save(p)
    print("wrote", p, f"({s.dur:.1f} s)")


if __name__ == "__main__":
    keys = [a for a in sys.argv[2:] if a in SPECS] or list(SPECS)
    scratch = os.environ.get("FK_SCRATCH", os.path.join(E.SHARED, "renders", "forest_keepers_talk", "ep1", "stills"))
    if sys.argv[1] == "--check":
        sys.exit(1 if sum(make(k).check() for k in keys) else 0)
    if sys.argv[1] == "--stills":
        for k in keys:
            stills(k, scratch)
    if sys.argv[1] == "--render":
        for k in keys:
            render(k)
