"""The talking format's animation: Keepers who stand, look, talk, take short walks and hops, in one place per shot
(owner 2026-11-17; rules in docs/engines/forest_keepers_talk_handoff.md, checked by talkcheck).

A chapter is a place, a light, its voiced lines (cues) and its actors. Each actor has:
- where it is: it stands still unless a move says otherwise. Moves are short walks on planted feet (flat_motion
  biped, the owner's pace), Springs' hops (his feet stay put while he crouches, the hop carries him), Glo's float,
  and a little bounce on the spot. A move only ever goes across the frame or toward us.
- where it looks: at whoever is talking (a speaker looks at whoever it is answering), unless a key says where else
  (up at a tree, down at the ground, at a point). The head turns a little toward what it looks at; Digs' hat
  turns with it.
- its mouth: from its own lines only (mix.Mouths). Glo has no mouth; her lantern brightens as she talks.
- eased tracks: sleep (eyes shut), Sprout's leaves (fold), Glo's lamp, Springs' yawn, a point of the arm.
Everything a frame shows is a function of time, so any frame can be drawn on its own (parallel render, stills).
"""
import json
import math
import os

import numpy as np
import skia

from families.keepers import flat, flat_motion as FM
from families.keepers.doorway import HALF_W
from families.keepers.storybook import C, oval, rrect
from families.keepers.talk import cast, places
from families.keepers.talk.mix import Mouths, blink, ease

W, H, FPS = places.W, places.H, 30
LIFT_DB = {"digs": 3.0, "springs": -1.0}   # Digs measured 3 dB under (FK0026 review). Springs: owner on FK0027 (+2 dB),
                                          # "his voice is so cutting that he sounds louder", so he sits 3 dB under that

HALF = {"sprout": HALF_W["sprout"] * 0.8, "digs": HALF_W["digger"], "springs": HALF_W["springs"],
        "glo": HALF_W["lantern"]}
HEAD = {"sprout": 125.0, "digs": 120.0, "springs": 150.0, "glo": 300.0}    # eye height above the feet, at k = 1
LEG = {"sprout": 70.0, "digs": 78.0}
HIP = {"sprout": 38.0, "digs": 62.0}
KIND = {"sprout": "sprout", "digs": "digger"}
PHASE = {"sprout": 0.0, "springs": 2.1, "digs": 1.1, "glo": 1.7}
INK, PAPER = (70, 52, 44), (252, 246, 234)
FONTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "engine", "assets", "fonts")
_FONT = {}


def font(size, weight="Bold"):
    if (size, weight) not in _FONT:
        _FONT[size, weight] = skia.Font(skia.Typeface.MakeFromFile(os.path.join(FONTS, f"Inter-{weight}.otf")), size)
    return _FONT[size, weight]


def text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold"):
    f = font(size, weight)
    pg.c.drawString(s, x - f.measureText(s) / 2, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def card(pg, s, x, y, size, a):
    """A name card: paper, soft shadow, centred on x with its text's baseline at y."""
    w = font(size).measureText(s) + 36
    pg.flat(rrect(x - w / 2 + 4, y - size - 8, x + w / 2 + 4, y + 16, 18), (40, 28, 24), 0.18 * a, blur=8)
    pg.flat(rrect(x - w / 2, y - size - 14, x + w / 2, y + 12, 18), PAPER, 0.94 * a)
    text(pg, s, x, y, size, a=a)


class Track:
    """An eased value through keys [(t, value)]: it holds before the first and after the last key and eases
    (smoothstep) from each key to the next over `dur` s starting at the next key's time."""

    def __init__(self, v0, dur=0.6):
        self.keys, self.v0, self.dur = [], v0, dur

    def to(self, t, v, dur=None):
        self.keys.append((t, v, self.dur if dur is None else dur))
        self.keys.sort(key=lambda q: q[0])
        return self

    def __call__(self, t):
        v = self.v0
        for t0, v1, d in self.keys:
            if t < t0:
                break
            v = v + (v1 - v) * ease(t, t0, t0 + d)
        return v


class Actor:
    def __init__(self, who, x, y):
        self.who, self.x0, self.y0 = who, float(x), float(y)
        self.moves = []                     # (t0, t1, fn(t) -> partial state)
        self.end = (self.x0, self.y0, 0.0)  # where the last move ends: (x, y, time)
        self.looks = []                     # (t0, t1, target): (lx, ly), a world point ("pt", x, y), or a name
        self.fold = Track(0.0, 1.2)         # Sprout's leaves
        self.sleep = Track(0.0, 0.6)        # eyes shut
        self.lamp = Track(1.0, 1.5)         # Glo
        self.yawn = Track(0.0, 0.7)         # Springs
        self.point = Track(0.0, 0.5)        # Springs' left arm toward Sprout
        self.squint = 0.0                   # Digs in daylight
        self.bounces = []                   # (t0, n): Sprout's little bounces on the spot

    @property
    def k(self):
        return places.scale_at(self.y0)

    # ------------------------------------------------------------------ moves
    def walk(self, t0, x1):
        """A short walk along the ground to x1 at the owner's pace (150 px/s at full size). -> its end time."""
        x0, y, _ = self.end
        k = places.scale_at(y)
        t1 = t0 + abs(x1 - x0) / (150.0 * k / 0.92)
        path = FM.walk_path([(t0, x0), (t1, x1)])
        turn = FM.heading(path)
        spread = lambda t: 1 - 0.6 * min(abs(turn(t)), 1.0)
        gait = FM.biped(KIND[self.who], path, y, k, spread=spread)

        def at(t, path=path, turn=turn, gait=gait, y=y, k=k, spread=spread):
            x = path(t)
            hips = lambda tt: [x - HIP[self.who] * k * spread(tt), x + HIP[self.who] * k * spread(tt)]
            return dict(x=x, y=y, turn=turn(t), feet=gait.feet(t), swing=FM.arm_swing(gait, t),
                        drop=FM.stance_drop(gait, hips, LEG[self.who] * k, t), walking=True)
        self.moves.append((t0 - 0.45, t1 + 0.45, at))
        self.end = (x1, y, t1)
        return t1

    def hop(self, t0, x1, y1=None, n=1, ground=0.42, air=0.58):
        """Springs hops n times to (x1, y1): crouch with his feet put, then the hop carries him. -> end time."""
        x0, y0, _ = self.end
        y1 = y0 if y1 is None else y1
        T = ground + air
        pts = [(x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n) for j in range(n + 1)]

        def at(t, t0=t0, pts=pts):
            i = min(n - 1, int((t - t0) / T))
            f = (t - t0) - i * T
            if t >= t0 + n * T:
                land = ease(t, t0 + n * T, t0 + n * T + 0.25) * (1 - ease(t, t0 + n * T + 0.25, t0 + n * T + 0.6))
                return dict(x=pts[-1][0], y=pts[-1][1], squash=0.35 * land)
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            if f < ground:
                return dict(x=xa, y=ya, squash=0.55 * math.sin(math.pi * f / ground))
            a = (f - ground) / air
            x, y = xa + (xb - xa) * a, ya + (yb - ya) * a
            return dict(x=x, y=y, lift=80 * places.scale_at(y) * 4 * a * (1 - a))
        self.moves.append((t0, t0 + n * T + 0.6, at))
        self.end = (x1, y1, t0 + n * T)
        return t0 + n * T

    def float_to(self, t0, t1, x1, y1):
        """Glo floats to (x1, y1) (the ground spot under her), easing out and in."""
        x0, y0, _ = self.end

        def at(t):
            u = ease(t, t0, t1)
            return dict(x=x0 + (x1 - x0) * u, y=y0 + (y1 - y0) * u, floating=True)
        self.moves.append((t0, t1, at))
        self.end = (x1, y1, t1)
        return t1

    def bounce(self, t0, n=2, period=0.45):
        self.bounces.append((t0, n, period))

    def look(self, t0, t1, target):
        self.looks.append((t0, t1, target))
        return self

    # ------------------------------------------------------------------ state
    def pos(self, t):
        """-> dict: x, y (feet on the ground), lift, squash, turn, feet, swing, drop, walking."""
        st = dict(x=self.x0, y=self.y0, lift=0.0, squash=0.0, turn=0.0, feet=None, swing=0.0, drop=0.0,
                  walking=False)
        last = None
        for t0, t1, fn in self.moves:
            if t0 <= t <= t1:
                st.update(fn(t))
                return st
            if t > t1:
                last = fn(t1)
        if last:
            st.update(x=last["x"], y=last["y"])
        for t0, n, p in self.bounces:
            if t0 <= t < t0 + n * p:
                f = ((t - t0) % p) / p
                st["lift"] = 7.0 * self.k * math.sin(math.pi * f)
        return st


class Chapter:
    """One chapter: place, light, voice (cues), actors and their keys. Subclasses fill in plan()."""
    place, light, close, title = "oak", "morning", None, ""
    sky_sun = True                     # False: the sunset backdrop has no sun (the chapter draws it setting)
    lead, tail = 1.5, 1.2
    extra = {}                              # cue index -> seconds of extra pause after it (actions need room)

    def __init__(self, n, voices_dir, voices_name):
        self.n = n
        with open(os.path.join(voices_dir, f"{voices_name}_cues.json"), encoding="utf-8") as f:
            raw = json.load(f)
        from families.keepers.talk.voices import decode
        src = decode(os.path.join(voices_dir, f"{voices_name}_voices.wav"))
        from families.keepers.talk.mix import SR
        shift, cues, parts = 0.0, [], []
        for c in raw:                       # the extra pauses: every later line moves on, with its sound
            a = src[int(c["start"] * SR):int(c["end"] * SR)] * np.float32(10 ** (LIFT_DB.get(c["who"], 0.0) / 20))
            c = dict(c, start=round(c["start"] + shift, 3), end=round(c["end"] + shift, 3))
            cues.append(c)
            parts.append((c["start"], a))
            shift += self.extra.get(c["i"], 0.0)
        self.cues = cues
        self.actors = {}
        self.sfx = []                       # (time, name, gain)
        self.loops = []                     # (t0, t1, name, gain)
        self.cuts = []                      # times inside the chapter where the framing changes
        self.cards = []                     # (t0, t1, who, name)
        self.until = None                   # a chapter that cuts away mid-move ends here
        self.shots = []                     # (t0, view): framing changes (cuts) inside the chapter
        self.plan()
        self.cuts = sorted(set(self.cuts) | {t0 for t0, _ in self.shots if t0 > 0})
        self.dur = self.until or max(cues[-1]["end"] + self.tail, max([a.end[2] + 0.5 for a in self.actors.values()] + [0]))
        self.voices = np.zeros(int((self.dur + 1) * SR), np.float32)
        for t0, a in parts:
            i = int(t0 * SR)
            self.voices[i:i + len(a)] += a[:len(self.voices) - i]
        self.mouths = Mouths(self.voices, cues, FPS)
        self._bg = {}

    def c(self, i):
        return self.cues[i]

    def add(self, who, x, y):
        self.actors[who] = Actor(who, x, y)
        return self.actors[who]

    # ------------------------------------------------------------------ looking
    def _target(self, who, t):
        """What `who` looks at at time t: a key if one covers t, else whoever is talking (or last talked)."""
        a = self.actors[who]
        for t0, t1, tg in a.looks:
            if t0 <= t <= t1:
                return tg
        said = [c for c in self.cues if c["who"] not in ("narrator",) and c["start"] - 0.2 <= t]
        if not said:
            return None
        cur = said[-1]
        if cur["who"] != who:
            return cur["who"] if cur["who"] in self.actors else None
        for c in reversed(self.cues[:cur["i"]]):                    # answering: the one who spoke before
            if c["who"] not in ("narrator", who) and c["who"] in self.actors:
                return c["who"]
        for c in self.cues[cur["i"] + 1:]:                          # or the one who answers it
            if c["who"] not in ("narrator", who) and c["who"] in self.actors:
                return c["who"]
        return None

    def _vec(self, who, tg, t):
        if tg is None:
            return (0.0, 0.0)
        if callable(tg):
            return tg(t)
        if isinstance(tg, tuple) and len(tg) == 2:
            return tg
        s = self.actors[who].pos(t)
        k = places.scale_at(s["y"])
        ex, ey = s["x"], s["y"] - HEAD[who] * k - s["lift"]
        if isinstance(tg, tuple):                                   # ("pt", x, y): a point in the world
            tx, ty = tg[1], tg[2]
        else:
            o = self.actors[tg].pos(t)
            tx, ty = o["x"], o["y"] - HEAD[tg] * places.scale_at(o["y"]) - o["lift"]
        dx, dy = tx - ex, ty - ey
        d = math.hypot(dx, dy) + 180.0
        return (max(-0.9, min(0.9, 1.1 * dx / d)), max(-0.8, min(0.8, 1.1 * dy / d)))

    def look(self, who, t):
        """Eyes ease to a new target over about a fifth of a second (three samples)."""
        v = [self._vec(who, self._target(who, t - d), t) for d in (0.0, 0.09, 0.18)]
        return (sum(q[0] for q in v) / 3, sum(q[1] for q in v) / 3)

    # ------------------------------------------------------------------ state for talkcheck
    def state(self, t):
        out = {}
        for who, a in self.actors.items():
            s = a.pos(t)
            out[who] = dict(x=s["x"], y=s["y"], k=places.scale_at(s["y"]), lift=s["lift"],
                            talk=0.0 if who == "glo" else self.mouths.open(who, t), holding=None)
        return out

    def gone(self, who, t0, margin=0.3):
        """The first time after t0 that `who` is wholly off the right or left edge of the shot (+ margin s)."""
        a = self.actors[who]
        t = t0
        while t < t0 + 60:
            s = a.pos(t)
            v = self.shot(t)
            Z = v["zoom"] if v else 1.0
            X = (s["x"] - v["cx"]) * Z + v["sx"] if v else s["x"]
            half = HALF[who] * places.scale_at(s["y"]) * Z
            if X - half > W or X + half < 0:
                return t + margin
            t += 1 / FPS
        raise ValueError(f"{who} never leaves the shot after {t0}")

    def shot(self, t):
        """The framing at t: None (wide) or a closer one {zoom, cx, cy, sx, sy}, from self.shots [(t0, view)]."""
        v = self.close
        for t0, view in self.shots:
            if t >= t0:
                v = view
        return v

    # ------------------------------------------------------------------ drawing
    def backdrop(self, place, light, close, page=(W, H)):
        key = (place, light, None if close is None else tuple(sorted(close.items())), page)
        if key not in self._bg:
            self._bg[key], self.marks = places.backdrop(place, light, view=close, sun=self.sky_sun, page=page)
        return self._bg[key]

    def lights(self, t):
        """[(light, weight)] for the scenery at t (a chapter whose light changes gives two)."""
        return [(self.light, 1.0)]

    def scenery_over(self, pg, t, S, Z):
        """Anything drawn over the backdrop and under the Keepers (subclasses)."""

    def light_extra(self, pg, t, S, Z):
        """Light effects over everything (subclasses): sun on the ground, a lantern's glow."""

    def draw_actor(self, pg, who, t, S, Z):
        a = self.actors[who]
        s = a.pos(t)
        k = places.scale_at(s["y"])
        X, Y = S(s["x"], s["y"])
        lk = self.look(who, t)
        bl = max(blink(t, PHASE[who]), a.sleep(t), a.squint)
        if who == "springs":
            rest_l = math.atan2(18, -44)
            p = a.point(t)
            cast.frog_springs(pg, X, Y, k * Z, look=lk, blink=bl, talk=max(self.mouths.open("springs", t), a.yawn(t)),
                              lift=s["lift"] * Z, squash=s["squash"],
                              arms=(rest_l + (math.atan2(-40, -34) - rest_l) * p, None))
            return
        if who == "glo":
            bob = 7.0 * k * math.sin(t * 1.1)
            talk = self.mouths.open("glo", t)
            cast.figure(pg, "glo", X, Y + bob * Z, k * Z, t=0.0, shadow=False, lamp=a.lamp(t) * (1 + 0.3 * talk),
                        talk=0.0, turn=0.25 * lk[0], _look=lambda _t: lk, _blink=lambda _t: bl)
            pg.shadow(X, Y + 6 * Z, 95 * k * Z, (13 * k + 3) * Z, 0.12)
            return
        talk = self.mouths.open(who, t) * (0.62 if who == "sprout" else 1.0)
        attrs = dict(t=0.0, talk=talk, _look=lambda _t: lk, _blink=lambda _t: bl)
        if s["walking"]:
            attrs.update(turn=s["turn"], legs_turn=s["turn"], arm_swing=s["swing"],
                         feet=[S(fx, fy) for fx, fy in s["feet"]])
        else:
            attrs.update(turn=0.3 * lk[0], legs_turn=0.0)
            if who == "sprout":
                attrs.update(arm_ang=math.atan2(55, -12), arm_ang_r=math.atan2(55, 12))
        if who == "sprout":
            attrs["leaf_fold"] = a.fold(t)
        if who == "digs":
            attrs["lamp"] = 0.0
        cast.figure(pg, who, X, Y + (s["drop"] - s["lift"]) * Z, k * Z, **attrs)

    def frame(self, t, camera=None, page=(W, H)):
        """camera: a view that replaces the chapter's own framing (an upright Short's), on a page of that size; the
        chapter's screen overlays (title, end sign) are left out then."""
        close = camera or self.shot(t)
        Z = close["zoom"] if close else 1.0
        S = (lambda x, y: ((x - close["cx"]) * Z + close["sx"], (y - close["cy"]) * Z + close["sy"])) if close else \
            (lambda x, y: (x, y))
        pg = flat.FlatPage(*page)
        lights = self.lights(t)
        for i, (light, w) in enumerate(lights):
            img = self.backdrop(self.place, light, close, page)
            if i == 0:
                pg.c.drawImage(img, 0, 0)
            elif w > 0.001:
                pg.c.drawImage(img, 0, 0, paint=skia.Paint(Alphaf=w))
        self.wash(pg, lights, 0.6)
        self.scenery_over(pg, t, S, Z)
        order = sorted(self.actors, key=lambda w: self.actors[w].pos(t)["y"])
        for who in order:
            x = S(self.actors[who].pos(t)["x"], 0)[0]
            if -400 < x < page[0] + 400:
                self.draw_actor(pg, who, t, S, Z)
        self.wash(pg, lights, 0.45)
        self.light_extra(pg, t, S, Z)
        if "glo" in self.actors:                                # Glo has no mouth: the lantern's light pulses as it talks
            talk = self.mouths.open("glo", t)
            if talk > 0.02:
                s = self.actors["glo"].pos(t)
                k = places.scale_at(s["y"])
                X, Y = S(s["x"], s["y"] - 190 * k)
                glow(pg, X, Y + 7.0 * k * math.sin(t * 1.1) * Z, 150 * k * Z, 0.42 * talk)
        for t0, t1, who, name in self.cards:                    # name cards, over the Keeper's head, held still
            a = ease(t, t0, t0 + 0.5) * (1 - ease(t, t1 - 0.6, t1))
            if a > 0.01:
                s = self.actors[who].pos(t0)
                X, Y = S(s["x"], s["y"] - (HEAD[who] + 120) * places.scale_at(s["y"]))
                card(pg, name, X, Y, 40, a)
        if camera is None:
            self.overlay(pg, t)
        return pg

    def overlay(self, pg, t):
        """Screen-space extras (title, end sign): subclasses."""

    @staticmethod
    def wash(pg, lights, part):
        for light, w in lights:
            wash = places.LIGHT[light][1]
            if wash and w > 0.001:
                pg.c.drawPaint(skia.Paint(Color=C(wash[0], wash[1] * part * w), BlendMode=skia.BlendMode.kMultiply))


def view(zoom, cx, feet, at=1000.0):
    """A closer framing: zoom about (cx, feet) with that ground line at screen y `at`, cx clamped so the scenery covers
    the frame (sx 960)."""
    cx = min(max(cx, 960.0 / zoom), W - 960.0 / zoom)
    v = dict(zoom=zoom, cx=float(cx), cy=float(feet), sx=960.0, sy=float(at))
    assert at - feet * zoom <= 0 and (H - feet) * zoom + at >= H, v
    return v


TALL = {"sprout": 2.0, "springs": 1.4, "digs": 1.2, "glo": 2.5}   # height / half width, a little generous


def edge_crops(ch, hold=1.0, step=0.25):
    """Keepers held cut in half by the frame edge (standing still, partly in shot for more than `hold` s): a held shot
    should have each Keeper wholly in or wholly out. Walking or hopping in and out is fine."""
    out, run = [], {}
    t = 0.0
    while t < ch.dur:
        v = ch.shot(t)
        Z = v["zoom"] if v else 1.0
        for who, a in ch.actors.items():
            s, s2 = a.pos(t), a.pos(min(t + step, ch.dur))
            moving = abs(s2["x"] - s["x"]) + abs(s2["y"] - s["y"]) > 0.5
            X = (s["x"] - v["cx"]) * Z + v["sx"] if v else s["x"]
            half = HALF[who] * places.scale_at(s["y"]) * Z
            Y = (s["y"] - v["cy"]) * Z + v["sy"] if v else s["y"]
            below = Y - TALL[who] * half >= H                          # wholly under the bottom edge: not in shot
            cut = not below and ((X - half < 0 < X + half) or (X - half < W < X + half))
            if cut and not moving:
                run.setdefault(who, t)
                if t - run[who] >= hold and (who, run[who]) not in [(w, t0) for w, t0, _ in out]:
                    out.append((who, run[who], X))
            else:
                run.pop(who, None)
        t += step
    return [f"{t0:.1f}s {w} cut by the frame edge (screen x {X:.0f})" for w, t0, X in out]


def overlap(state):
    """Keepers on screen whose widths overlap (no front/behind choices in the talking format)."""
    vis = [(w, s) for w, s in state.items() if s["x"] + HALF[w] * s["k"] > 0 and s["x"] - HALF[w] * s["k"] < W]
    out, items = [], sorted(vis, key=lambda q: q[1]["x"])
    for (a, sa), (b, sb) in zip(items, items[1:]):
        gap = (sb["x"] - HALF[b] * sb["k"]) - (sa["x"] + HALF[a] * sa["k"])
        if gap < 0:
            out.append(f"{a} and {b} overlap by {-gap:.0f} px")
    return out


def sun_pool(pg, x, y, rx, ry, a):
    """Warm light lying on the ground (screen blend, soft edge)."""
    p = skia.Paint(Color=C("#ffe2a8", a), BlendMode=skia.BlendMode.kScreen, AntiAlias=True)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, ry * 0.8))
    pg.c.drawPath(oval(x, y, rx, ry), p)


def glow(pg, x, y, r, a, col="#ffd68c"):
    p = skia.Paint(Color=C(col, a), BlendMode=skia.BlendMode.kScreen, AntiAlias=True)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.45))
    pg.c.drawCircle(x, y, r, p)
