"""The Keepers talk (owner, 2026-10-27: "the little cute noises the monsters make ... a little bit more often, so
they're doing some kind of communicating with the audience").

Every voice is a moment: the Keeper turns its eyes to the camera, does a little bounce, its mouth moves (Glo's
lantern flickers instead, Hans' beard wiggles) and a small speech bubble pops up with a picture in it, never
words. On top of the voices the acts ask for at story beats, `Chatter.update` fills quiet stretches with asides:
a Keeper on screen turns to us and reacts, about one voice every 4-6 s overall.

Moods (what the act asks for) -> voice contour (audio/synth.voice), pitch step on the Keeper's own note, picture:
"""
import math

import numpy as np

from families.foundry.keepers.common import ellipse, lerp, seg, smoothstep
from families.foundry.products.monster import NAMES, TOPS

# each Keeper's voice: its note (same as episodes 1-4) and its vowel colour (formant scale)
VOICE = {"wheels": 67, "tentacles": 55, "teeth": 50, "springs": 74, "lantern": 71, "digger": 60, "sprout": 72}
VOWEL = {"wheels": 1.0, "tentacles": 0.82, "teeth": 0.9, "springs": 1.15, "lantern": 1.08, "digger": 0.94,
         "sprout": 1.12}

MOODS = {  # mood: (contour, pitch step, default picture)
    "ooh": ("ooh", 0, "sparkle"),      # wonder
    "yay": ("cheer", 0, "star"),       # happy, done
    "hm": ("hum", -2, "dots"),         # thinking
    "q": ("up", 0, "?"),               # a question
    "mm": ("down", 0, "heart"),        # content
    "hehe": ("hehe", 2, "note"),       # a giggle
    "brr": ("brr", 0, "snow"),         # cold
    "uhoh": ("uhoh", 0, "!"),          # oops
    "wee": ("wee", 0, "note"),         # whee!
    "huff": ("huff", -3, None),        # effort (no bubble)
    "hey": ("hey", 0, "!"),            # calling to us
    "aww": ("aww", 0, "heart"),        # fond
    "idea": ("up", 2, "!"),
}
# the old four contours the acts used before the engine talked (Act.say) -> moods
CONTOUR_MOOD = {"up": "q", "down": "mm", "hum": "hm", "cheer": "yay"}

PAPER = np.array([212, 208, 198], np.float64)     # soft, so the bloom doesn't blow it out at night
INK = np.array([40, 36, 48], np.float64)
HEART = np.array([226, 92, 120], np.float64)
GOLD = np.array([246, 196, 70], np.float64)
ICE = np.array([120, 180, 236], np.float64)
SLED_RED = np.array([200, 70, 60], np.float64)


class Talk:
    __slots__ = ("t", "dur", "kind", "mood", "icon", "look")

    def __init__(self, t, dur, kind, mood, icon, look):
        self.t, self.dur, self.kind, self.mood, self.icon, self.look = t, dur, kind, mood, icon, look


class Chatter:
    """Owned by the FK scene: schedules voices, drives the faces, draws the bubbles, adds asides."""

    def __init__(self, scene, seed, gap=(3.6, 6.0), vel=0.34):
        self.s = scene
        self.rng = np.random.default_rng(seed + 404)
        self.talks = []
        self.gap = gap
        self.vel = vel
        self.last = 0.0                    # when a Keeper last spoke (story beats and asides alike)
        self.next_gap = float(self.rng.uniform(*gap))
        self.turn = 0
        self.count = {"beats": 0, "asides": 0}

    # ----- scheduling -----

    def say(self, t, kind, mood, icon="auto", vel=None, look=True, x=None, y=None, step=0):
        """Keeper `kind` says something at scene time t. icon "auto" = the mood's picture, None = no bubble."""
        from audio.synth import VOICE_DUR
        if kind not in VOICE:
            return
        contour, st, pic = MOODS[mood]
        m = self.s.by_kind.get(kind)
        if x is None:
            x, y = (m.x, m.y - 150) if m is not None else (self.s.cam_x + self.s.w / 2, 0.0)
        note = VOICE[kind] + st + step
        inst = f"voice_{contour}@{int(round(VOWEL[kind] * 100))}"
        self.s.hit(t, inst, note, (self.vel if vel is None else vel), x, y)
        dur = VOICE_DUR.get(contour, 0.34)
        self.talks.append(Talk(t, dur, kind, mood, pic if icon == "auto" else icon, look))
        self.last = max(self.last, t + dur)
        self.count["beats"] += 1

    def chorus(self, t, kinds, mood, gap=0.18, icon="auto", vel=None):
        """Several Keepers one after the other (a little wave of voices)."""
        for q, kind in enumerate(kinds):
            self.say(t + q * gap, kind, mood, icon=icon if q == 0 or icon in ("3", "2", "1") else
                     (icon if q % 2 == 0 else None), vel=vel)

    # ----- per frame -----

    def update(self, t, act):
        """Faces of everyone talking now; an aside when it has been quiet for a while."""
        s = self.s
        active = {}
        for tk in self.talks:
            if tk.t - 0.35 <= t < tk.t + tk.dur + 0.9:
                active.setdefault(tk.kind, []).append(tk)
        for m in s.monsters:
            talk, att, dy = 0.0, 0.0, 0.0
            for tk in active.get(m.kind, []):
                u = t - tk.t
                if 0 <= u < tk.dur:
                    env = smoothstep(min(1.0, u / 0.05)) * smoothstep(min(1.0, (tk.dur - u) / 0.08))
                    talk = max(talk, env * (0.55 + 0.45 * abs(math.sin(2 * math.pi * 5.5 * u))))
                if tk.look:
                    att = max(att, smoothstep(seg(u, -0.35, 0.0)) * (1 - smoothstep(seg(u, tk.dur + 0.4, tk.dur + 0.9))))
                if 0 <= u < 0.34:
                    dy = min(dy, -11 * m.k / 0.55 * math.sin(math.pi * u / 0.34))
            m.talk, m.attend, m.talk_dy = talk, att, dy
        # asides: fill quiet stretches
        if not getattr(act, "asides", True) or s.done:
            return
        lt = t - act.t0
        if lt < 2.0 or lt > act.dur - 2.5:
            return
        if t - self.last < self.next_gap:
            return
        cands = [m for m in s.monsters if m.kind in getattr(act, "poses", {}) and
                 s.visible(m.x - 60, m.x + 60) and m.kind not in getattr(act, "quiet", ())]
        if not cands:
            return
        moods = act.aside_moods(lt) if hasattr(act, "aside_moods") else ["mm", "hehe", "ooh", "aww", "hm"]
        if not moods:
            return
        # the one who spoke least lately goes next, so everyone gets a turn
        spoke = {m.kind: max([tk.t for tk in self.talks if tk.kind == m.kind], default=-99.0) for m in cands}
        m = min(cands, key=lambda m: (spoke[m.kind], (s.monsters.index(m) + self.turn) % 6))
        self.turn += 1
        mood = moods[int(self.rng.integers(len(moods)))]
        self.say(t + 0.05, m.kind, mood)
        self.count["beats"] -= 1
        self.count["asides"] += 1
        self.next_gap = float(self.rng.uniform(*self.gap))

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        for tk in self.talks:
            if tk.icon is None:
                continue
            life = max(1.3, tk.dur + 0.75)
            u = t - tk.t
            if not (0 <= u < life):
                continue
            m = s.by_kind.get(tk.kind)
            if m is None or not s.visible(m.x - 200, m.x + 200):
                continue
            pop = _back(min(1.0, u / 0.24))
            fade = 1 - smoothstep(seg(u, life - 0.3, life))
            k = m.k / 0.55
            hx = m.x + 76 * k
            hy = m.y - TOPS[m.kind] * m.k - 62 * k + m.talk_dy - 10 * smoothstep(min(1.0, u / 0.5))
            bubble(c, hx, hy, 54 * k * pop, tk.icon, m.full, fade, (m.x + 22 * k, m.y - TOPS[m.kind] * m.k + 6 * k))


def _back(u):
    """Ease out with a little overshoot (a pop)."""
    c1 = 1.9
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


def bubble(c, x, y, r, icon, edge, a=1.0, tail=None):
    """Round speech bubble of radius r at (x, y) with a picture; `a` fades it (towards the night sky)."""
    if r < 2 or a <= 0.01:
        return
    bg = np.array([14, 16, 24], np.float64)
    paper = bg + (PAPER - bg) * a
    ink = bg + (INK - bg) * a
    if tail is not None:
        tx, ty = tail
        c.polygon([(x - r * 0.42, y + r * 0.62), (x - r * 0.05, y + r * 0.8), (lerp(x, tx, 0.75), lerp(y, ty, 0.75))],
                  paper)
    c.polygon(ellipse(x, y, r * 1.12, r, 36), paper)
    c.polyline(ellipse(x, y, r * 1.12, r, 36), bg + (np.asarray(edge, np.float64) * 0.85 - bg) * a,
               max(2.0, r * 0.08), closed=True)
    icon_draw(c, x, y, r * 0.62, icon, a, ink, bg)


def icon_draw(c, x, y, r, icon, a, ink, bg):
    def col(v):
        return bg + (np.asarray(v, np.float64) - bg) * a
    if icon in ("!", "?", "1", "2", "3"):
        c.text(icon, x, y + r * 0.06, r * 1.7, col(INK if icon in "!?" else SLED_RED))
    elif icon == "heart":
        h = col(HEART)
        c.circle(x - r * 0.42, y - r * 0.2, r * 0.48, h)
        c.circle(x + r * 0.42, y - r * 0.2, r * 0.48, h)
        c.polygon([(x - r * 0.86, y - r * 0.05), (x + r * 0.86, y - r * 0.05), (x, y + r * 0.85)], h)
    elif icon == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r * (0.95 if i % 2 == 0 else 0.42)
            pts.append((x + math.cos(ang) * rr, y + 0.06 * r + math.sin(ang) * rr))
        c.polygon(pts, col(GOLD))
    elif icon == "sparkle":
        for sc, dx, dy in ((1.0, -0.15, 0.08), (0.45, 0.55, -0.45)):
            rr = r * sc
            cx, cy = x + dx * r, y + dy * r
            c.polygon([(cx, cy - rr), (cx + rr * 0.22, cy - rr * 0.22), (cx + rr, cy), (cx + rr * 0.22, cy + rr * 0.22),
                       (cx, cy + rr), (cx - rr * 0.22, cy + rr * 0.22), (cx - rr, cy), (cx - rr * 0.22, cy - rr * 0.22)],
                      col(GOLD))
    elif icon == "note":
        n = col(INK)
        c.polygon(ellipse(x - r * 0.3, y + r * 0.5, r * 0.32, r * 0.24, 20), n)
        c.line(x - r * 0.0, y + r * 0.5, x - r * 0.0, y - r * 0.75, n, max(2.0, r * 0.13))
        c.polygon([(x, y - r * 0.8), (x + r * 0.55, y - r * 0.45), (x + r * 0.55, y - r * 0.2), (x, y - r * 0.45)], n)
    elif icon == "snow":
        sn = col(ICE)
        w = max(2.0, r * 0.12)
        for i in range(3):
            ang = i * math.pi / 3
            ca, sa = math.cos(ang), math.sin(ang)
            c.line(x - ca * r * 0.9, y - sa * r * 0.9, x + ca * r * 0.9, y + sa * r * 0.9, sn, w)
            for e in (-1, 1):
                ex, ey = x + e * ca * r * 0.55, y + e * sa * r * 0.55
                for f in (-1, 1):
                    b = ang + f * 0.6
                    c.line(ex, ey, ex + e * math.cos(b) * r * 0.3, ey + e * math.sin(b) * r * 0.3, sn, w * 0.8)
    elif icon == "dots":
        for i in (-1, 0, 1):
            c.circle(x + i * r * 0.55, y + r * 0.1, r * 0.17, col(INK))
    elif icon == "run":                                  # a little marble run: three zigzag ramps and a ball
        wood, ball = col(np.array([150, 112, 72])), col(SLED_RED)
        w = max(2.0, r * 0.13)
        for k in range(3):
            yy = y - r * 0.55 + k * r * 0.5
            a, b = (x - r * 0.85, x + r * 0.7) if k % 2 == 0 else (x - r * 0.7, x + r * 0.85)
            dy = r * 0.16
            c.line(a, yy + (dy if k % 2 == 0 else 0), b, yy + (0 if k % 2 == 0 else dy), wood, w)
        c.circle(x + r * 0.45, y - r * 0.78, r * 0.2, ball)
    elif icon == "ball":                                 # a wooden ball with its band
        c.circle(x, y, r * 0.62, col(np.array([196, 164, 120])))
        c.arc(x, y, r * 0.5, 200, 340, col(np.array([236, 230, 214])), max(2.0, r * 0.14))
    elif icon == "raft":                                 # a little log raft with a leaf sail on a wave
        wood, sail, water = col(np.array([150, 112, 72])), col(SLED_RED), col(ICE)
        w = max(2.0, r * 0.12)
        yy = y + r * 0.4
        for k in range(3):
            c.line(x - r * 0.7, yy - k * r * 0.09, x + r * 0.7, yy - k * r * 0.09, wood, w)
        c.line(x - r * 0.05, yy - r * 0.2, x - r * 0.05, yy - r * 1.0, wood, max(1.5, r * 0.09))
        c.polygon([(x, yy - r * 0.98), (x + r * 0.62, yy - r * 0.6), (x, yy - r * 0.28)], sail)
        c.polyline([(x - r * 0.9 + i * r * 0.15, yy + r * 0.22 + r * 0.07 * math.sin(i * 1.6)) for i in range(13)],
                   water, max(1.5, r * 0.1))
    elif icon == "acorn":                                # an acorn with its cap
        nut, cap = col(np.array([152, 104, 56])), col(np.array([104, 78, 50]))
        c.polygon(ellipse(x, y + r * 0.2, r * 0.5, r * 0.62, 20), nut)
        c.polygon(ellipse(x, y - r * 0.22, r * 0.62, r * 0.36, 20, math.pi, 2 * math.pi), cap)
        c.line(x - r * 0.62, y - r * 0.22, x + r * 0.62, y - r * 0.22, cap, max(2.0, r * 0.14))
        c.line(x, y - r * 0.55, x + r * 0.15, y - r * 0.85, cap, max(1.5, r * 0.1))
    elif icon == "pie":                                  # a round pie with a lattice crust
        crust, fill = col(np.array([196, 132, 70])), col(np.array([120, 72, 42]))
        c.polygon([(x - r * 0.85, y), (x + r * 0.85, y), (x + r * 0.7, y + r * 0.45), (x - r * 0.7, y + r * 0.45)], crust)
        c.polygon(ellipse(x, y, r * 0.85, r * 0.3, 24), crust)
        c.polygon(ellipse(x, y - r * 0.02, r * 0.66, r * 0.2, 24), fill)
        for k in (-1, 0, 1):
            c.line(x + k * r * 0.33 - r * 0.12, y - r * 0.2, x + k * r * 0.33 + r * 0.12, y + r * 0.18, crust,
                   max(1.5, r * 0.1))
    elif icon == "bread":                                # a round loaf with a scored top
        crust = col(np.array([186, 118, 58]))
        c.polygon(ellipse(x, y + r * 0.1, r * 0.82, r * 0.55, 28, math.pi, 2 * math.pi) +
                  [(x + r * 0.82, y + r * 0.45), (x - r * 0.82, y + r * 0.45)], crust)
        c.line(x - r * 0.3, y - r * 0.15, x + r * 0.3, y - r * 0.05, col(np.array([130, 78, 40])), max(1.5, r * 0.1))
    elif icon == "orb":                                  # a glowing blue orb (the Keepers' orbs, the factory)
        c.circle(x, y, r * 0.66, col(np.array([110, 190, 255])))
        c.circle(x - r * 0.2, y - r * 0.2, r * 0.18, col(np.array([220, 240, 255])))
    elif icon == "book":                                 # the Field Guide, open
        g, p = col(np.array([92, 120, 70])), col(np.array([236, 226, 198]))
        c.polygon([(x - r * 0.9, y - r * 0.5), (x + r * 0.9, y - r * 0.5), (x + r * 0.95, y + r * 0.6),
                   (x - r * 0.95, y + r * 0.6)], g)
        c.polygon([(x - r * 0.82, y - r * 0.44), (x - r * 0.04, y - r * 0.36), (x - r * 0.04, y + r * 0.5),
                   (x - r * 0.82, y + r * 0.5)], p)
        c.polygon([(x + r * 0.04, y - r * 0.36), (x + r * 0.82, y - r * 0.44), (x + r * 0.82, y + r * 0.5),
                   (x + r * 0.04, y + r * 0.5)], p)
        for q in range(3):
            yy = y - r * 0.15 + q * r * 0.2
            c.line(x - r * 0.65, yy, x - r * 0.2, yy, col(INK), max(1.5, r * 0.06))
            c.line(x + r * 0.2, yy, x + r * 0.65, yy, col(INK), max(1.5, r * 0.06))
    elif icon == "bug":                                  # a little ladybug
        c.circle(x, y + r * 0.08, r * 0.62, col(np.array([206, 40, 30])))
        c.circle(x, y - r * 0.58, r * 0.28, col(INK))
        c.line(x, y - r * 0.5, x, y + r * 0.7, col(INK), max(1.5, r * 0.07))
        for dx, dy in ((-0.3, -0.1), (0.3, -0.1), (-0.28, 0.32), (0.28, 0.32)):
            c.circle(x + dx * r, y + dy * r, r * 0.12, col(INK))
    elif icon == "smile":                                # a smiling face
        c.circle(x, y, r * 0.78, col(GOLD))
        for e in (-1, 1):
            c.circle(x + e * r * 0.28, y - r * 0.18, r * 0.1, col(INK))
        c.arc(x, y - r * 0.05, r * 0.45, 25, 155, col(INK), max(2.0, r * 0.12))
    elif icon == "sled":
        red, wood = col(SLED_RED), col(np.array([150, 112, 72]))
        L = r * 1.6
        x0, x1, yy = x - L / 2, x + L / 2, y + r * 0.35
        c.line(x0, yy, x1 - r * 0.25, yy, wood, max(2.0, r * 0.12))
        c.arc(x1 - r * 0.25, yy - r * 0.25, r * 0.25, -90, 90, wood, max(2.0, r * 0.12))
        c.polygon([(x0 + r * 0.1, yy - r * 0.62), (x1 - r * 0.2, yy - r * 0.62), (x1 - r * 0.3, yy - r * 0.32),
                   (x0 + r * 0.15, yy - r * 0.32)], red)
        for f in (0.25, 0.75):
            xx = lerp(x0 + r * 0.1, x1 - r * 0.3, f)
            c.line(xx, yy - r * 0.32, xx, yy, wood, max(1.5, r * 0.09))
