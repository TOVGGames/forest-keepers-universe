"""Tree monsters (Toby's design, docs/engines/foundry_monsters.md): three wooden monsters grown
in the green vat, parts stuck on, brought to life by a blue orb.

These are recurring characters, so each one's look lives here and nowhere else: shape, colour
and parts. Front view, local origin = ground under the monster's middle, y down, scale `k`.
Before the orb lands a monster is asleep: eyes shut, still, and almost no colour (a faint tint
over bare wood). `alive` 0..1 brings in full colour, opens the eyes and starts the idle motion;
`t` drives the idle motion. `tint` overrides the colour amount (0 = bare wood, used in the vat).

Parts can be stuck on one at a time: `attach` maps part name -> 0..1 (0 = not there yet, 1 = on);
a part in between is drawn shifted along its approach direction (PARTS), so a robot arm can
carry it in. `attach = None` means fully built.

The new look (`newlook = True`, Forest Keepers from episode 9, docs/engines/forest_keepers_tune_up.md): no pinned
badge (the orb flashes the job badge instead: `flash` 0..1, `job`), asleep = pale grey wood, Hans without the
face-tentacle beard and with a smiling mouth, Twigs with a softer eye (lid + brow) and a rounded-tooth grin.
Expressions: `smile` (-1 "ooh" .. 1 big grin), `lid_top` (0..1 upper lid down: happy / sleepy), `brow` (-1 worried ..
1 raised); `talk` opens the mouth as before.
"""
import math

import numpy as np

from engine.core import hex_rgb
from ..style import STEEL, lighten, smoothstep

COLORS = {"wheels": "#2f6fd6", "tentacles": "#e0701e", "teeth": "#8a3fd0",
          "springs": "#d4a21c", "lantern": "#1fb3a5", "digger": "#c4452f", "sprout": "#4c9f48"}
# names (owner + Toby, 2026-10-25). Code keys stay the body-type names; these are what viewers see.
NAMES = {"wheels": "Wheels", "tentacles": "Hans", "teeth": "Twigs", "springs": "Springs", "lantern": "Glo",
         "digger": "Digs", "sprout": "Sprout"}
# top of the head above the feet at k = 1 (antlers, wings, hat included), for the nameplate
TOPS = {"wheels": 380, "tentacles": 470, "teeth": 650, "springs": 320, "lantern": 380, "digger": 300, "sprout": 360}
ORB = np.array([110, 190, 255], np.float64)
WOOD = np.array([132, 96, 62], np.float64)
EYE_WHITE = np.array([232, 226, 210], np.float64)
PUPIL = np.array([16, 18, 26], np.float64)
GLINT = np.array([255, 250, 235], np.float64)
TOOTH = np.array([236, 230, 214], np.float64)
MOUTH = np.array([30, 14, 26], np.float64)
RUBBER = np.array([27, 27, 31], np.float64)
CLAW = np.array([150, 158, 172], np.float64)      # bright steel: claws, hubs
LAMP_C = np.array([255, 196, 110], np.float64)    # warm lamp light (lantern belly, digger's hat lamp)
HAT = np.array([214, 172, 40], np.float64)
LEAF = np.array([70, 170, 90], np.float64)
PALE = np.array([156, 151, 143], np.float64)       # new look, orb out: pale grey wood
TONGUE = np.array([214, 96, 110], np.float64)
BLADE = np.array([206, 212, 220], np.float64)      # Twigs' slide-out pruning blades: bright, clean silver


def lerp_(a, b, u):
    return a + (b - a) * u


# part name -> approach direction (unit-ish vector, scaled by `reach`) per kind, in build order
PARTS = {
    "wheels": {"wheels": (-1, 0), "arms": (0, -1), "eyes": (0, -1)},
    "tentacles": {"legs": (-1, 0), "wings": (0, -1), "beard": (1, 0), "eyes": (0, -1)},
    "teeth": {"legs": (-1, 0), "arms": (1, 0), "antlers": (0, -1), "eye": (0, -1), "mouth": (1, 0)},
    # episode 2 (docs/engines/foundry_keepers.md)
    "springs": {"legs": (-1, 0), "arms": (1, 0), "eyes": (0, -1), "mouth": (1, 0)},
    "lantern": {"tendrils": (-1, 0), "lamp": (1, 0), "eyes": (0, -1)},
    "digger": {"legs": (-1, 0), "arms": (1, 0), "hat": (0, -1), "face": (0, -1)},
    # the seventh Keeper (owner + Toby, 2026-11-03), built at the night-shift factory (forest_keepers_factory_trip.md)
    "sprout": {"legs": (-1, 0), "arm": (-1, 0), "hand": (1, 0), "face": (0, -1), "seed": (0, -1)},
}
# a Keeper turning to walk (Turned): its face parts, its head's radius (monster units), and the most it turns
FACE_PARTS = {"wheels": ("eyes",), "tentacles": ("eyes", "beard"), "teeth": ("eye", "mouth"),
              "springs": ("eyes", "mouth"), "lantern": ("eyes",), "digger": ("face", "hat"), "sprout": ("face", "seed")}
HEAD_R = {"wheels": 112.0, "tentacles": 118.0, "teeth": 92.0, "springs": 110.0, "lantern": 105.0, "digger": 135.0,
          "sprout": 110.0}
TURN_MAX = 0.55               # rad (about 30 degrees: a three-quarter view)
TURN_OF = {"wheels": 0.6, "springs": 0.8}   # wide-set eyes turn less, so the near one stays on the face
TURN_NARROW = 0.6             # how much closer the hips come in that view (the legs pass each other, like a walk
                              # seen from the side, instead of stepping sideways)
ACORN = np.array([176, 120, 58], np.float64)       # Sprout's acorn nut and cap
CAP = np.array([128, 92, 56], np.float64)
SPROUT_ORB_DY = 84   # Sprout's orb socket below his body centre: low on the belly, well clear of his mouth (was 72:
                     # the empty socket sat just under his sleeping face and read as an open mouth; FK0024, 2026-11-07)
BARK_C = np.array([92, 70, 52], np.float64)        # the oak log Sprout is turned from
SEED_STEM = np.array([96, 150, 70], np.float64)
WATER = np.array([150, 200, 240], np.float64)


def clip_half(pts, axis, v, below):
    """Sutherland-Hodgman: the part of polygon pts with coordinate `axis` (0 = x, 1 = y) <= v (below) or >= v."""
    keep = (lambda p: p[axis] <= v) if below else (lambda p: p[axis] >= v)
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ka, kb = keep(a), keep(b)
        if ka:
            out.append(a)
        if ka != kb:
            u = (v - a[axis]) / (b[axis] - a[axis])
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def seedling(c, x, y, k, t=0.0, ang=0.0, grow=1.0, fold=0.0):
    """Sprout's seedling (and the little tree it plants): a stem with two leaves, root end at (x, y), leaning by
    `ang`; `grow` 0..1 how far it has come up; `fold` 0..1 how far its two leaves fold down (they bend where they
    meet the stem and keep their length: talking format, 2026-11-17)."""
    if grow <= 0.01:
        return
    sway = 0.08 * math.sin(t * 1.3) + ang
    ca, sa = math.cos(sway), math.sin(sway)
    g = grow
    q = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    top = q(6 * k * g, -56 * k * g)
    c.polyline([q(0, 0), q(2 * k * g, -26 * k * g), top], SEED_STEM, max(1.5, 6 * k * min(1.0, 0.4 + g)))
    lg = max(0.0, (g - 0.25) / 0.75)
    if lg <= 0.01:
        return
    for sx in (-1, 1):
        a = -math.pi / 2 + sx * (1.0 * (0.3 + 0.7 * lg) + 1.75 * fold) + sway
        L = 46 * k * lg
        lf = [(top[0], top[1]), (top[0] + math.cos(a - 0.35) * L * 0.57, top[1] + math.sin(a - 0.35) * L * 0.57),
              (top[0] + math.cos(a) * L, top[1] + math.sin(a) * L),
              (top[0] + math.cos(a + 0.35) * L * 0.57, top[1] + math.sin(a + 0.35) * L * 0.57)]
        c.polygon(lf, LEAF * 1.08)
        c.line(top[0], top[1], top[0] + math.cos(a) * L * 0.87, top[1] + math.sin(a) * L * 0.87, LEAF * 0.7, 2 * k)


def acorn_nut(c, x, y, r):
    """A loose acorn, its middle at (x, y)."""
    c.circle(x, y + r * 0.1, r, ACORN)
    c.polygon(ellipse(x, y - r * 0.45, r * 1.08, r * 0.62, 20, math.pi, 2 * math.pi), CAP)
    c.line(x, y - r * 1.05, x + r * 0.25, y - r * 1.4, CAP * 0.8, max(1.5, r * 0.22))
WOOD_BODY = np.array([118, 92, 66], np.float64)    # bare grown wood (before any colour)


class Xform:
    """Canvas wrapper: rotate by `ang` (rad) and scale by `s` about pivot (px, py), then move by
    (dx, dy). Used for parts flying in and for whole-body moves (flips, hops, leans)."""

    def __init__(self, cv, dx=0.0, dy=0.0, ang=0.0, s=1.0, px=0.0, py=0.0, fx=1.0):
        # fx scales x before rotating (fx = -1 mirrors: a vehicle turning around)
        self.__dict__.update(_cv=cv, _m=(dx, dy, math.cos(ang) * s, math.sin(ang) * s, px, py, s, ang), _fx=fx)

    def __getattr__(self, k):
        return getattr(self._cv, k)

    def __setattr__(self, k, v):
        setattr(self._cv, k, v)

    def _p(self, x, y):
        dx, dy, c, si, px, py, _, _ = self._m
        x, y = (x - px) * self._fx, y - py
        return (px + c * x - si * y + dx, py + si * x + c * y + dy)

    def _pts(self, pts):
        return [self._p(*q) for q in np.asarray(pts, np.float64).reshape(-1, 2)]

    def polygon(self, pts, col):
        self._cv.polygon(self._pts(pts), col)

    def polyline(self, pts, col, width=2.0, closed=False):
        self._cv.polyline(self._pts(pts), col, width * self._m[6], closed)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self._cv.line(*self._p(x0, y0), *self._p(x1, y1), col, width * self._m[6])

    def circle(self, x, y, r, col, fill=True, width=2.0):
        self._cv.circle(*self._p(x, y), r * self._m[6], col, fill, width * self._m[6])

    def text(self, text, x, y, size, col, anchor="mm", weight="Bold"):
        self._cv.text(text, *self._p(x, y), size * self._m[6], col, anchor, weight)

    def arc(self, x, y, r, a0, a1, col, width=2.0):
        d = math.degrees(self._m[7])
        self._cv.arc(*self._p(x, y), r * self._m[6], a0 + d, a1 + d, col, width * self._m[6])



class Turned(Xform):
    """Canvas wrapper for a Keeper turning to walk (owner 2026-11-05: no crab walking - they turn to face where they
    go): the face is drawn on a round head of radius r about x = cx, turned by `th` rad (+ = to the screen's right).
    Each point keeps its height and moves round the head (x = cx + r sin(asin(u) + th)), so the features slide
    towards the side it faces and the far ones crowd together, the way a real round head turns. Never mirrored,
    never thin."""

    def __init__(self, cv, cx, r, th):
        super().__init__(cv)
        self.__dict__.update(_cx=cx, _r=r, _th=th)

    def _p(self, x, y):
        x, y = Xform._p(self, x, y)
        u = max(-1.0, min(1.0, (x - self._cx) / self._r))
        a = max(-math.pi / 2, min(math.pi / 2, math.asin(u) + self._th))
        return self._cx + self._r * math.sin(a), y

    def circle(self, x, y, r, col, fill=True, width=2.0):
        # (advisor FK0023 r7: a circle kept its full width at its moved centre, so the near eye's socket disc stuck out
        # past the head's edge) mapped point by point round the head like every other shape: it never leaves the head
        pts = ellipse(x, y, r, r, 40)
        if fill:
            self.polygon(pts, col)
        else:
            self.polyline(pts, col, width, closed=True)

def ellipse(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in np.linspace(a0, a1, n, endpoint=a1 - a0 < 2 * math.pi - 1e-6)]


def blob(cv, pts, col, edge=1.35, shade=0.74):
    """Flat body: face, darker lower third, thin highlight along the top."""
    pts = np.asarray(pts, np.float64)
    cv.polygon(pts, col)
    if getattr(cv, "flat_look", False):                # flat picture-book look: the canvas does its own soft shade
        return
    y0, y1 = pts[:, 1].min(), pts[:, 1].max()
    yb = y1 - (y1 - y0) * 0.3
    low = [p for p in pts if p[1] >= yb]
    if len(low) > 2:
        cv.polygon(low, np.asarray(col) * shade)
    top = [p for p in pts if p[1] <= y0 + (y1 - y0) * 0.18]
    if len(top) > 1:
        cv.polyline(sorted(top, key=lambda p: p[0]), lighten(col, edge), 2.5)
    cv.polyline(pts, np.asarray(col) * 0.55, 2.5, closed=True)


def grain(cv, cx, cy, rx, ry, col):
    """A few faint tree-ring arcs: these monsters were trees."""
    if getattr(cv, "flat_look", False):
        return
    for f in (0.35, 0.6, 0.85):
        cv.polyline(ellipse(cx, cy, rx * f, ry * f, 40, 3.5, 5.9), np.asarray(col) * 0.86, 1.6)


def eye(cv, x, y, r, look, blink, glow=None, alive=1.0, lid=None, top=0.0, iris=0.5, cheek=0.0):
    """Round eye; `look` = (dx, dy) in -1..1, `blink` 0 open .. 1 shut (an eyelid in `lid`
    colour with a sleepy curved lash line). `top` 0..1 lowers a flat upper lid over the eye (happy, sleepy);
    `iris` = iris radius / eye radius; `cheek` 0..1 pushes a lower lid up in an arch (a smiling, squinting eye).
    On a flat canvas (`cv.flat_look`, the flat picture-book look) the eye has no dark rim and a bigger coloured iris
    ring round a black pupil (no lash: the owner scrapped it, 2026-11-04)."""
    flat = getattr(cv, "flat_look", False)
    lid = WOOD_BODY if lid is None else np.asarray(lid)
    if flat:
        r *= getattr(cv, "eye_scale", 1.0)
        iris = max(iris, 0.6)
        cv.circle(x, y, r * 1.08, lid * 0.86)
    else:
        cv.circle(x, y, r * 1.12, PUPIL)
        cv.circle(x, y, r, lid * 0.92)
    h = r * (1 - blink)
    if h < 1:
        cv.arc(x, y - r * 0.25, r * 0.75, 25, 155, PUPIL, max(2.0, r * 0.12))
        return
    cv.polygon(ellipse(x, y, r, h, 36), EYE_WHITE)
    px, py = x + look[0] * r * 0.38, y + look[1] * h * 0.38
    pr = r * iris
    col = (getattr(cv, "iris_col", ORB) if flat else ORB) * (0.35 + 0.65 * alive)
    cv.polygon(ellipse(px, py, pr, min(pr, h * 0.9), 28), col)
    cv.circle(px, py, pr * (0.58 if flat else 0.5), PUPIL)
    cv.circle(px - pr * 0.35, py - pr * 0.35, pr * (0.14 if flat else 0.2), GLINT)
    if glow is not None and alive > 0:
        glow.begin(cv)
        cv.circle(px, py, pr * 0.9, ORB * 0.55 * alive * max(0.0, 1 - 2 * top) * max(0.0, 1 - 2.5 * cheek))
        glow.end(cv)
    if cheek > 0.01:                                   # lower lid: below an upward arch
        hgt = 2 * r * min(cheek, 0.8)
        edge, bottom = [], []
        for u in np.linspace(-1, 1, 49):
            half = math.sqrt(max(0.0, 1 - u * u)) * r
            ye = y + r - hgt * (1 - u * u)                          # the arch, highest in the middle
            if ye < y + half:                                       # only where it is inside the eye
                edge.append((x + u * r, max(ye, y - half)))
                bottom.append((x + u * r, y + half))
        if len(edge) > 2:
            cv.polygon(edge + bottom[::-1], lid * 0.92)
            cv.polyline(edge, PUPIL, max(2.0, r * 0.1))
    if top > 0.01:                                     # upper lid: the part of the eye above a slightly curved line
        yc = y - r + 2 * r * min(top, 0.95)
        arc = [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 36)]
        pts = [(px_, min(py_, yc + 0.12 * r * (1 - ((px_ - x) / r) ** 2))) for px_, py_ in arc]
        edge = [(x + r * u, yc + 0.12 * r * (1 - u * u)) for u in np.linspace(1, -1, 24)
                if y - math.sqrt(max(0.0, r * r - (r * u) ** 2)) < yc + 0.12 * r * (1 - u * u)]
        cv.polygon(pts + edge, lid * 0.92)
        if len(edge) > 1:
            cv.polyline(edge, PUPIL, max(2.0, r * 0.1))


def orb(cv, x, y, r, glow=None, alive=1.0, t=0.0, orb_in=1.0, flash=0.0, job="keeper"):
    """Orb socket; the orb itself only once it has landed (`orb_in` > 0). `flash` 0..1: the orb swells a little,
    lights up and shows the job badge (`job`: keeper = the Forest Keeper leaf, loaf, snow)."""
    pulse = 0.85 + 0.15 * math.sin(t * 3.0)
    cv.circle(x, y, r * 1.18, STEEL)                      # socket ring
    cv.circle(x, y, r * 0.95, PUPIL)                      # empty socket
    r *= orb_in
    if r < 0.5:
        return
    f = smoothstep(flash) if flash > 0 else 0.0
    r *= 1 + 0.45 * f
    body = ORB * (0.3 + 0.7 * alive)
    cv.circle(x, y, r, body)
    if f > 0.01:
        badge(cv, x, y, r, job, f, body)
    cv.circle(x - r * 0.3, y - r * 0.3, r * 0.28 * (1 - 0.5 * f), lighten(ORB, 1.6))
    if glow is not None and (alive > 0 or f > 0):
        glow.begin(cv)
        cv.circle(x, y, r * (1.1 + 0.4 * f), ORB * alive * pulse * (1 - f) + BADGE_GLOW[job] * f * 0.45)
        glow.end(cv)


BADGE_GLOW = {"keeper": np.array([200, 230, 120], np.float64), "loaf": np.array([255, 200, 120], np.float64),
              "snow": np.array([200, 230, 255], np.float64)}


def badge(cv, x, y, r, job, f, under):
    """Job badge shown in an orb, faded in over the orb colour `under` by `f`."""
    mix = lambda c: under * (1 - f) + np.asarray(c, np.float64) * f
    if job == "keeper":                                   # the Forest Keeper badge: yellow disc, green leaf
        cv.circle(x, y, r * 0.98, mix(HAT))
        leaf = [(x, y - r * 0.78), (x + r * 0.46, y - r * 0.1), (x, y + r * 0.68), (x - r * 0.46, y - r * 0.1)]
        cv.polygon(leaf, mix(LEAF))
        cv.line(x, y - r * 0.62, x, y + r * 0.56, mix(LEAF * 0.6), max(1.5, r * 0.09))
    elif job == "loaf":                                   # baking: a round loaf on a warm disc
        cv.circle(x, y, r * 0.98, mix((250, 214, 150)))
        cv.polygon(ellipse(x, y + r * 0.08, r * 0.62, r * 0.42, 28), mix((176, 104, 46)))
        for u in (-0.3, 0.0, 0.3):
            cv.line(x + (u - 0.1) * r, y - r * 0.12, x + (u + 0.1) * r, y + r * 0.12, mix((236, 186, 120)),
                    max(1.5, r * 0.08))
    elif job == "snow":                                   # winter jobs: a snowflake on ice blue
        cv.circle(x, y, r * 0.98, mix((150, 196, 236)))
        for i in range(3):
            a = i * math.pi / 3 + math.pi / 2
            dx, dy = math.cos(a) * r * 0.7, math.sin(a) * r * 0.7
            cv.line(x - dx, y - dy, x + dx, y + dy, mix((250, 252, 255)), max(1.5, r * 0.1))


def blush(cv, x, y, k, col, alive):
    """Soft rosy cheek (new look)."""
    cv.polygon(ellipse(x, y, 17 * k, 9 * k, 20), np.asarray(col) * (1 - 0.3 * alive) + np.array([250, 120, 140]) * 0.3 * alive)


def smile_mouth(cv, mx, my, w, smile, talk, col, k, teeth=0, depth=1.0, awake=1.0):
    """New-look mouth (Hans, Twigs): `smile` 0..1 a D-shaped grin, corners up, opening wider with `talk`; below 0
    a little round "ooh". `teeth` rounded teeth along the top edge. Asleep (`awake` < 0.5): a closed, relaxed line."""
    if awake < 0.5:
        cv.arc(mx, my - w * 0.9, w * 1.05, 62, 118, np.asarray(col) * 0.45, 3.5 * k)
        return
    if smile < 0:
        o = -smile
        cv.polygon(ellipse(mx, my + 4 * k, (10 + 7 * o) * k, (11 + 9 * o + 10 * talk) * k, 28), MOUTH)
        cv.polyline(ellipse(mx, my + 4 * k, (10 + 7 * o) * k, (11 + 9 * o + 10 * talk) * k, 28),
                    np.asarray(col) * 0.5, 3 * k, closed=True)
        return
    hw = w * (0.75 + 0.25 * smile)
    c = (4 + 10 * smile) * k
    d = ((5 + 16 * smile) * depth + 26 * talk) * k
    us = np.linspace(-1, 1, 33)
    top = [(mx + u * hw, my - c * u * u) for u in us]
    bot = [(mx + u * hw, my - c * u * u + d * math.sqrt(max(0.0, 1 - u * u))) for u in us[::-1]]
    cv.polygon(top + bot, MOUTH)
    if d > 12 * k:                                    # tongue
        cv.polygon(ellipse(mx + 0.12 * hw, my + d * 0.66, hw * 0.36, d * 0.26, 24), TONGUE)
    if teeth:
        slot = 1.2 * hw / teeth
        th = min(0.36 * d, 15 * k)
        tw = slot * 0.84
        for i in range(teeth):
            u = -0.6 + (i + 0.5) * 1.2 / teeth
            cx = mx + u * hw
            y0 = my - c * u * u - 1
            r = tw / 2
            yb = y0 + max(th - r, 0.0)
            cv.polygon([(cx - r, y0), (cx + r, y0), (cx + r, yb), (cx - r, yb)], TOOTH)
            cv.polygon(ellipse(cx, yb, r, min(r, th), 20, 0, math.pi), TOOTH)
    cv.polyline(top + bot, np.asarray(col) * 0.5, 3 * k, closed=True)


def beard(c, x, hy, k, col, tt, t, talk=0.0):
    """Hans' old face-tentacle beard (episodes 1-8), hanging from the head centred at (x, hy): 9 face tentacles,
    longest in the middle, angled inward, so together they make an upside-down triangle that comes to a point under
    the chin. A function so the factory arm can carry it away (episode 9)."""
    n = 9
    for i in sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2)):   # sides first, middle on top
        u = (i - (n - 1) / 2) / ((n - 1) / 2)
        bx = x + u * 78 * k
        by = hy + 52 * k + 30 * k * (1 - u * u) ** 0.5     # below the eyes, following the chin
        ln = (190 - 130 * abs(u)) * k
        wig = talk * 0.22 * math.sin(t * 13 + i * 1.7)        # talking: the beard wiggles
        tentacle(c, bx, by, ln * (1 - 0.1 * talk), math.pi / 2 + u * 0.35 + wig, (30 - 8 * abs(u)) * k,
                 lighten(col, 1.16 - 0.1 * abs(u)), tt + talk * t * 3, 2 + i * 0.9,
                 curl=0.35 * (1 if u > 0 else -1) if abs(u) > 0.01 else 0.15)


def fang_mouth(c, mx, my, k, col, a, t, talk=0.0):
    """Twigs' old mouth (episodes 1-8): every tooth sharp, top and bottom rows interlocking."""
    mw, mh = 70 * k, 30 * k
    chomp = a * 0.25 * (0.5 + 0.5 * math.sin(t * 1.9))
    mh *= 0.8 + chomp + 0.55 * talk
    mouth = ellipse(mx, my, mw, mh, 40)
    c.polygon(mouth, MOUTH)
    n = 9
    for row, sgn in ((my - mh * 0.92, 1), (my + mh * 0.92, -1)):
        off = 0.0 if sgn > 0 else 0.5
        for i in range(n):
            u0, u1 = (i + off) / n, (i + 1 + off) / n
            if u1 > 1.0:
                continue
            x0, x1 = mx - mw + u0 * 2 * mw, mx - mw + u1 * 2 * mw
            edge = math.sqrt(max(0.0, 1 - ((x0 + x1) / 2 - mx) ** 2 / mw ** 2))
            hgt = mh * 0.85 * edge
            b = my + (row - my) * edge
            c.polygon([(x0, b), (x1, b), ((x0 + x1) / 2, b + sgn * hgt)], TOOTH)
    c.polyline(mouth, np.asarray(col) * 0.5, 3, closed=True)


def tentacle(cv, x, y, length, ang, width, col, t, phase, curl=1.0, segs=14, sucker=None):
    """Tapered tentacle from (x, y) heading `ang` (rad, 0 = +x, y down), gently waving. On a flat canvas (no outline
    to thicken it) it is a little plumper, with a blunter tip."""
    flat = getattr(cv, "flat_look", False)
    taper = 0.7 if flat else 0.85
    if flat:
        width *= 1.35
    pts_l, pts_r, spine = [], [], []
    a = ang
    px, py = x, y
    for i in range(segs + 1):
        u = i / segs
        spine.append((px, py))
        w = width * (1 - taper * u)
        nx, ny = -math.sin(a), math.cos(a)
        pts_l.append((px + nx * w / 2, py + ny * w / 2))
        pts_r.append((px - nx * w / 2, py - ny * w / 2))
        a += curl * (0.09 + 0.07 * math.sin(t * 1.7 + phase + u * 3.0)) * (0.4 + u)
        px += math.cos(a) * length / segs
        py += math.sin(a) * length / segs
    poly = pts_l + pts_r[::-1]
    cv.polygon(poly, col)
    if flat:                                           # a round tip, not a cut-off end
        tip = np.mean([pts_l[-1], pts_r[-1]], axis=0)
        cv.circle(tip[0], tip[1], width * (1 - taper) / 2, col)
    cv.polyline(poly, np.asarray(col) * 0.55, 2, closed=True)
    # suckers on the underside
    for i in range(3, segs - 2, 3):
        sx, sy = pts_r[i]
        cv.circle(sx, sy, width * (1 - 0.85 * i / segs) * 0.16, lighten(col, 1.35) if sucker is None else sucker)


TWIGS_THIGH = math.hypot(30.0, 110.0)      # Twigs' leg bones (monster units), as drawn standing
TWIGS_SHIN = math.hypot(20.0, 112.0)
TWIGS_UPPER, TWIGS_FORE = math.hypot(46.0, 80.0), math.hypot(10.0, 80.0)      # his arm bones, standing
WHEELS_UPPER, WHEELS_FORE = math.hypot(70.0, 30.0), math.hypot(30.0, 60.0)    # Wheels' arm bones


def bent_knee(hip, foot, a, b, side):
    """Like two_bone, but `side` may be anywhere in -1..1: the knee bends out to the right by `side` of its full
    bend. In between it is pointing towards / away from us (the leg turning round), so it only looks shorter."""
    H, F_ = np.asarray(hip, np.float64), np.asarray(foot, np.float64)
    d = F_ - H
    L = float(np.linalg.norm(d)) or 1e-6
    L2 = min(L, (a + b) * 0.9995)
    u = d / L
    ca = (a * a + L2 * L2 - b * b) / (2 * a * L2)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    n = np.array([-u[1], u[0]])
    if n[0] < 0:
        n = -n
    kn = H + u * a * ca + n * a * sa * side
    return float(kn[0]), float(kn[1])


TWO_BONE_BAND = 0.15   # two_bone: |cos| between the bend normal and `prefer` under which the joint swings smoothly


def two_bone(hip, foot, a, b, side, prefer=None):
    """The knee of a leg with bones a (hip-knee) and b (knee-foot) reaching from hip to foot, bent out to `side`
    (-1/1), or towards the direction `prefer` (an elbow: down and out); the bones never change length (a foot out
    of reach is met as far as the leg goes)."""
    H, F_ = np.asarray(hip, np.float64), np.asarray(foot, np.float64)
    d = F_ - H
    L = float(np.linalg.norm(d)) or 1e-6
    L2 = min(L, (a + b) * 0.9995)
    u = d / L
    ca = (a * a + L2 * L2 - b * b) / (2 * a * L2)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    n = np.array([-u[1], u[0]])
    pref = np.array(prefer if prefer is not None else (side, 0.0), np.float64)
    # which side of the hip-foot line the knee goes: where the limb points almost along `prefer` the two sides are
    # nearly equal and a hard switch threw the joint across the limb in one frame (FK0024 0:32, Wheels' reaching
    # elbows 10 px as he turned to walk). Within a narrow band the joint swings through the limb's own line instead
    # (the projection of an elbow rotating round), outside it nothing changes.
    s = float(n @ pref) / (float(np.linalg.norm(pref)) or 1.0)
    w = 1.0 if s >= TWO_BONE_BAND else -1.0 if s <= -TWO_BONE_BAND else \
        2.0 * smoothstep((s + TWO_BONE_BAND) / (2 * TWO_BONE_BAND)) - 1.0
    kn = H + u * a * ca + n * a * sa * w
    return float(kn[0]), float(kn[1])


def planted_tentacle(cv, root, foot, L, width, col, side, sucker=None):
    """A leg tentacle that walks (flat look, owner 2026-11-03: Hans walks on his legs, less floaty), always exactly
    `L` long: from its root it comes down to the ground, and its end lies along the ground out to the tip at `foot`
    (`side` -1/1: which way it points), the way an octopus's arm puts its last part flat on the ground. The nearer
    the foot is to under the root, the more of the leg lies on the ground. Returns its drawn length (storycheck)."""
    flat = getattr(cv, "flat_look", False)
    taper = 0.7 if flat else 0.85
    if flat:
        width *= 1.35
    p0, ft = np.asarray(root, np.float64), np.asarray(foot, np.float64)
    o = np.array([side, 0.0])
    u = np.linspace(0, 1, 41)[:, None]

    def chord(g):
        return float(np.linalg.norm(ft - o * g - p0))

    lo, hi = 0.0, 0.6 * L                              # g: how much lies on the ground (the upper part keeps a
    if 0.96 * L - chord(0.0) < 0:                      # gentle 4 % curve)
        hi = 0.0
    for _ in range(40):
        g = (lo + hi) / 2
        if 0.96 * (L - g) - chord(g) > 0:
            lo = g
        else:
            hi = g
    g = (lo + hi) / 2
    p3 = ft - o * g                                    # where it meets the ground
    Lu = L - g
    d = p3 - p0
    c = float(np.linalg.norm(d))
    if c > Lu * 0.999:                                 # out of reach: never longer than itself, the tip stops short
        p3 = p0 + d / c * Lu * 0.999
        d, c = p3 - p0, Lu * 0.999

    def curve(b):
        p1 = p0 + d * 0.3 + o * b
        p2 = p3 + np.array([-side * 0.12 * c, -0.35 * c])
        return ((1 - u) ** 3) * p0 + 3 * ((1 - u) ** 2) * u * p1 + 3 * (1 - u) * u * u * p2 + (u ** 3) * p3

    def length(pts):
        return float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))

    lo, hi = -0.5 * Lu, 1.0 * Lu                       # bow out until the upper part is exactly Lu long
    for _ in range(40):
        mid = (lo + hi) / 2
        if length(curve(mid)) < Lu:
            lo = mid
        else:
            hi = mid
    spine = curve((lo + hi) / 2)
    if g > 1.0:                                        # the part on the ground, its very tip lifting a little
        v = np.linspace(0, 1, max(3, int(g / 6)))[1:, None]
        low = p3 + o * g * v
        low[:, 1] -= 0.12 * g * v[:, 0] ** 3
        spine = np.vstack([spine, low])
    n = len(spine)
    dd = np.gradient(spine, axis=0)
    dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-9
    nn = np.stack([-dd[:, 1], dd[:, 0]], axis=1)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(spine, axis=0), axis=1))])
    w = width * (1 - taper * arc / max(arc[-1], 1e-9))
    poly = np.vstack([spine + nn * (w / 2)[:, None], (spine - nn * (w / 2)[:, None])[::-1]])
    col = np.asarray(col)
    cv.polygon(poly, col)
    if flat:
        cv.circle(spine[-1][0], spine[-1][1], w[-1] / 2, col)
    cv.polyline(poly, col * 0.55, 2, closed=True)
    for q in np.linspace(0.18, 0.8, 5):                # suckers on the inner side
        i = int(np.searchsorted(arc, q * arc[-1]))
        sx, sy = spine[i] - nn[i] * (side * w[i] * 0.32)
        cv.circle(sx, sy, w[i] * 0.13, lighten(col, 1.35) if sucker is None else sucker)
    return float(arc[-1])


def reach_tentacle(cv, x0, y0, tx, ty, width, col, t, phase=0.0, side=1, grip=1.0, segs=28, sucker=None):
    """A working tentacle: from its root (x0, y0) along a soft S-curve to (tx, ty), then the tip wraps
    about 3/4 of a turn around the held point. Same look as the leg tentacles (taper, dark outline,
    suckers on the underside), slowly undulating along its length. `grip` 0..1 tightens the wrap."""
    L = math.hypot(tx - x0, ty - y0) + 1e-6
    # control points: leave the body sideways and a little down, arrive at the target from below
    # (reaching up) or from above (reaching down), like a real arm of an octopus
    up = ty < y0
    p0 = np.array([x0, y0])
    p1 = p0 + np.array([side * 0.45 * L, 0.18 * L])
    p3 = np.array([tx, ty])
    p2 = p3 + np.array([-side * 0.12 * L, (0.32 if up else -0.28) * L])
    u = np.linspace(0, 1, segs + 1)[:, None]
    spine = ((1 - u) ** 3) * p0 + 3 * ((1 - u) ** 2) * u * p1 + 3 * (1 - u) * u * u * p2 + (u ** 3) * p3
    d = np.gradient(spine, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], axis=1)
    uu = u[:, 0]
    wave = 0.05 * L * np.sin(np.pi * uu) * np.sin(t * 1.7 + phase + uu * 4.0)
    spine = spine + nrm * wave[:, None]
    # tip wrap: a shrinking spiral around the held point
    r0 = width * 0.55
    a0 = math.atan2(spine[-1][1] - spine[-2][1], spine[-1][0] - spine[-2][0]) - side * math.pi / 2
    turn = (0.55 + 0.25 * grip) * 2 * math.pi
    wrap = []
    for i in range(1, 11):
        f = i / 10
        a = a0 + side * turn * f
        r = r0 * (1 - 0.35 * f)
        wrap.append((tx + math.cos(a) * r - math.cos(a0) * r0, ty + math.sin(a) * r - math.sin(a0) * r0))
    pts = np.vstack([spine, np.array(wrap)])
    n = len(pts)
    dd = np.gradient(pts, axis=0)
    dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-9
    nn = np.stack([-dd[:, 1], dd[:, 0]], axis=1)
    w = width * (1 - 0.62 * np.linspace(0, 1, n) ** 0.8)
    left = pts + nn * (w / 2)[:, None]
    right = pts - nn * (w / 2)[:, None]
    poly = np.vstack([left, right[::-1]])
    col = np.asarray(col)
    cv.polygon(poly, col)
    cv.polyline(poly, col * 0.55, 2, closed=True)
    # a lighter stripe along the top side reads as a round limb
    cv.polyline(pts[2:-4] + nn[2:-4] * (w[2:-4] * 0.22)[:, None], lighten(col, 1.18), max(2.0, width * 0.12))
    under = -side if not up else side
    for i in range(4, n - 3, 3):
        sx, sy = pts[i] + nn[i] * (under * w[i] * 0.36)
        cv.circle(sx, sy, w[i] * 0.15, lighten(col, 1.35) if sucker is None else sucker)
    return float(np.sum(np.linalg.norm(np.diff(spine, axis=0), axis=1)))


class Monster:
    KINDS = ("wheels", "tentacles", "teeth", "springs", "lantern", "digger", "sprout")

    def __init__(self, kind, k=1.0):
        assert kind in self.KINDS
        self.kind, self.k = kind, k
        self.full = hex_rgb(COLORS[kind])
        self.x = self.y = 0.0
        self.alive = 1.0          # 0 = asleep (faint, eyes shut, still), 1 = awake
        self.orb_in = 1.0         # 0..1 orb pushed into its socket
        self.tint = None          # colour amount override (0 = bare wood)
        self.attach = None        # part -> 0..1 while being built; None = complete
        self.reach = 520.0        # how far away a part starts its approach
        self.wheel_rot = 0.0
        self.punch = 0.0          # 0..1 right arm thrown forward (punching bag)
        self.walk = 0.0           # 0..1 walking gait amount
        self.spring = 0.0         # springs: coil squash (-0.5 stretched .. 1 squashed)
        self.dig = 0.0            # digger: shovels down 0..1
        self.lamp = None          # lantern/digger lamp brightness override (default = alive)
        self.rough = 0.0          # 0 = carved smooth body, 1 = rough grown lump (before the carving station)
        self.badge = 0.0          # 0..1 Forest Keeper badge pinned on (episode 2)
        self.gait = 0.0           # gait phase (rad), advanced by the scene while moving
        self.saws = False         # Twigs (from Forest Keepers episode 4): a little circular saw on each wrist
        self.saw_spin = 0.0       # blade angle (rad), advanced by the scene while the saws run
        self.saw_run = 0.0        # 0..1 how fast they spin (blur + sound)
        self.punch_l = 0.0        # 0..1 left arm lifted forward (Twigs with saws)
        self.hands = False        # Twigs (owner 2026-11-03, the factory-trip episode on): wooden hands instead of
        self.blades = 0.0         # the wrist saws, and a pruning blade on each forearm that slides out 0..1
        self.blades_l = None      # the left blade on its own (None = same as `blades`): only the cutting one comes out
        self.grip = 0.0           # 0 open hand .. 1 fingers curled (holding something)
        self.bare = set()         # Twigs' wrists with nothing on yet (-1 left, 1 right): a socket, at the factory
        self.turn = 0.0           # -1..1: turned to walk left / right (0 = facing us; Turned)
        self.legs_turn = None     # its legs' turn, if not the face's (it looks round at us, still walking)
        self.arm_swing = None     # ep 14 on (owner, FK0016: "nobody walks with their arms out like they're pretending
        #                           they're an airplane"): -1..1 the right arm swung forward (the left the other way);
        #                           set, the arms hang down at their own length and swing along the way it walks
        self.clamp_reach = False  # ep 14 on: an arm reaching for a point out of reach stops at its own length
        self.knee_fwd = False     # ep 14 on (owner, FK0016: Twigs "looks like he's walking backwards"): Twigs' knees
        #                           bend forward, the way he walks, like a person's
        self.feet = None          # walking (flat look): where each foot is planted, (x, y) - Hans' six tentacle tips
                                  # (planted_tentacle), Twigs', Digs' and Sprout's two feet (left, right); the legs
                                  # keep their length. None = the old drawing
        self.float = 1.0          # Hans: how much his head bobs (1 = the old floaty bob)
        self.paw_ang = None       # Digs digging (flat look): {-1: rad, 1: rad} each arm's angle at a fixed length
        self.leg_len = []         # filled while drawing: Hans' legs' drawn lengths (storycheck)
        self.legs_up = ()         # Hans (planted feet): legs lifted off the ground to work as tentacles (not drawn as legs;
                                  # owner 2026-11-06: 8 tentacles in all, a 3rd arm is a leg that lifts)
        self.hat_orb = False      # Digs (flat look, owner + Toby 2026-11-04): his orb in his hard hat, not his tummy
        self.orbless = False          # the talking format (owner 2026-11-17: "Remove the orb, remove the orb from all of
                                  # them"): no orb, no socket and no rim anywhere; Digs wears his plain hard hat, which
                                  # turns with his head (docs/engines/forest_keepers_talk_handoff.md)
        self.leaf_fold = 0.0      # Sprout's seedling leaves: 0 open, 1 folded down (asleep)
        self.parts_col = {}       # Hans (flat look): "legs", "wings", "suckers" colours (awake)
        self.wing_amp = None      # Hans' wings with his mood (owner 2026-11-04): flap size (default 0.15), speed
        self.wing_speed = None    # (rad/s, default 2.0), phase, and wing_up 0..1 pricked straight up (surprised)
        self.wing_phase = 0.0
        self.wing_up = 0.0
        self.mole_claws = False   # Digs (storybook episodes, owner 2026-11-04): a real mole's broad paws with five
                                  # long claws instead of the steel shovels
        self.talk = 0.0           # 0..1 how far its mouth is open while it talks (Forest Keepers engine)
        self.attend = 0.0         # 0..1 looking straight out at the audience instead of looking around
        self.talk_dy = 0.0        # little bounce while talking (up is negative)
        self.newlook = False      # Forest Keepers from episode 9 (see the module docstring)
        self.flash = 0.0          # 0..1 orb flashing the job badge (new look)
        self.job = "keeper"       # which badge: keeper, loaf, snow
        self.smile = 0.6          # new-look mouths: -1 "ooh" .. 1 big grin
        self.lid_top = 0.0        # 0..1 upper lids lowered (happy / sleepy)
        self.brow = 0.0           # Twigs' brow: -1 worried .. 1 raised
        self.cheek = 0.0          # 0..1 smiling eyes (lower lids pushed up)
        # the Tune-Up episode (9): the new look comes on piece by piece at the factory
        self.pin = 0.0            # new look: the old leaf badge still pinned on (0..1), until the factory unclips it
        self.old = set()          # new look: old face parts still on ("beard" Hans; "mouth", "eye" Twigs)
        self.brow_on = 1.0        # Twigs' new brow: 0..1 clipped on (slides down into place)
        self.hide = set()         # face slots left empty for a moment ("beard" Hans' chin, "mouth" Twigs)
        # Sprout, the seventh Keeper (factory-trip episode): the build stages, from an oak log to a Keeper
        self.part_dxy = {}        # part -> (dx, dy): where a machine arm has a part right now (while 0 < attach < 1)
        self.log_top = None       # Sprout still a log: extra log length above the finished top (CUT takes it off)
        self.turned = 1.0         # TURN: 0..1 how far down the cutter has shaped the log into the acorn body
        self.spin = 0.0           # the log's turn on the lathe (rad): its bark ridges move round
        self.carved = 1.0         # CARVE: 0..1 how far across the chisel has cut the cap's scales
        self.stained = 1.0        # CARVE: 0..1 how far across the brush has stained the cap brown
        self.acorn = True         # Sprout carries an acorn in its little hand
        self.acorn_r = 11.0       # its radius (x k): an episode can make it bigger so the viewer sees it (FK0024: 16)
        self.water_floor = None   # where the watering can's drops land (None: its own feet line, self.y)
        self.can_tip = None       # how far it tips the can to pour (None: CAN_TIP); held high, less (FK0017 r2)
        self.can = False          # Sprout carries a little watering can in its right hand
        self.water = 0.0          # 0..1 Sprout tips the watering can and it sprinkles
        self.wave = 0.0           # 0..1 Sprout's hand lifted up beside the head, waving
        self.hold_out = 0.0       # 0..1 Sprout's hand held out level (to drop the acorn)
        self.arm_to = {}          # Twigs / Wheels: {side: (x, y)} a hand reaching for a point (fixed-length bones)
        self.arm_w = {}           # {side: 0..1} how far that hand has gone from where it would be to arm_to (1 = there)
        self.arm_len = {}         # filled while drawing: {side: (shoulder, elbow, hand)} (storycheck)
        self.arm_ang = None       # Sprout's left arm angle (rad, fixed length), set by a scene; None = the poses above
        self.arm_ang_r = None     # ... and its right arm
        self.socket = 1.0         # CARVE: 0..1 the orb socket being cut (a dark hole growing in)

    @property
    def color(self):
        if self.newlook:                              # orb out: pale grey wood, no colour at all
            f = self.tint if self.tint is not None else self.alive
            return PALE * (1 - f) + self.full * f
        f = self.tint if self.tint is not None else 0.16 + 0.84 * self.alive
        return WOOD_BODY * (1 - f) + self.full * f

    def face(self, cv):
        """cv, or the turned head canvas while it turns to walk (Turned)."""
        if abs(self.turn) < 1e-4:
            return cv
        return Turned(cv, self.x, HEAD_R[self.kind] * self.k, self.turn * TURN_MAX * TURN_OF.get(self.kind, 1.0))

    def swing_dir(self):
        """Which way 'forward' is on screen for a swinging arm (-1..1: 0 facing us, where a swing is towards us)."""
        return smoothstep(min(abs(self._legs_turn()), 1.0)) * (1.0 if self._legs_turn() >= 0 else -1.0)

    def hang_arm(self, sh, sx, reach, out=0.18, amp=0.5, upper=None, fore=None):
        """-> (elbow, hand) of an arm hanging from shoulder `sh` on side sx, swung by arm_swing (fixed lengths)."""
        h = self.swing_dir()
        sw = (self.arm_swing or 0.0) * (1.0 if sx > 0 else -1.0)
        ang = sx * out * (1 - 0.6 * abs(h)) + h * sw * amp                  # from straight down, + = to the right
        hd = (sh[0] + math.sin(ang) * reach, sh[1] + math.cos(ang) * reach)
        if upper is None:
            return None, hd
        # facing us the elbow bends out to its side; turned to walk it bends back. Where those two are on opposite
        # sides the elbow swings round through the arm's own axis while the walker turns (blended over |h| 0.15-0.45,
        # the projection of that swing), never flipping sides in one frame (Raft Race report 2026-11-06: a ~40 px
        # elbow pop at every walk start and stop when it switched at |h| = 0.3)
        side = two_bone(sh, hd, upper, fore, sx, (sx * 0.6, 0.15))
        w = smoothstep(min(1.0, max(0.0, (abs(h) - 0.15) / 0.3)))
        if w <= 0.0:
            return side, hd
        fwd = two_bone(sh, hd, upper, fore, sx, (-math.copysign(max(abs(h), 0.3), h), 0.15))
        el = (side[0] + (fwd[0] - side[0]) * w, side[1] + (fwd[1] - side[1]) * w)
        return el, hd

    def _legs_turn(self):
        return self.turn if self.legs_turn is None else self.legs_turn

    def narrow(self):
        """How far apart its hips are now (1 facing us; closer while it is turned to walk)."""
        return 1.0 - TURN_NARROW * min(abs(self._legs_turn()), 1.0)

    def leg_order(self):
        """The two legs (-1 left, 1 right), the far one first (drawn behind the near one)."""
        return (-1, 1) if self._legs_turn() >= 0 else (1, -1)

    def _orb(self, c, *a):
        if not self.orbless:
            orb(c, *a)

    def part(self, cv, name):
        """Canvas to draw part `name` on, or None if it isn't attached yet (a face part turns with the head)."""
        c = self._part(cv, name)
        if c is not None and name in FACE_PARTS.get(self.kind, ()):
            return self.face(c)
        return c

    def _part(self, cv, name):
        if self.attach is None:
            return cv
        u = self.attach.get(name, 0.0)
        if u <= 0:
            return None
        if u >= 1:
            return cv
        if name in self.part_dxy:                     # carried by a machine arm: drawn where the arm has it
            return Xform(cv, *self.part_dxy[name])
        d = PARTS[self.kind][name]
        e = (1 - u) ** 2 * self.reach
        return Xform(cv, d[0] * e, d[1] * e)

    def part_offset(self, name):
        """Where a part currently is relative to its attached spot (for the carrier arm)."""
        u = 1.0 if self.attach is None else self.attach.get(name, 0.0)
        d = PARTS[self.kind][name]
        e = (1 - u) ** 2 * self.reach
        return d[0] * e, d[1] * e

    # idle motion shared by all three: slow look-around + occasional blink
    def _look(self, t):
        a = self.alive
        lx, ly = a * math.sin(t * 0.7 + self.KINDS.index(self.kind) * 2.3), a * 0.4 * math.sin(t * 0.45)
        w = smoothstep(self.attend)                # eyes come round to the camera, a touch low (at the viewer)
        return lx * (1 - w), ly * (1 - w) + 0.12 * w

    def _blink(self, t):
        if self.alive < 1.0:      # asleep: shut; waking: lids open slowly
            return 1.0 - smoothstep((self.alive - 0.25) / 0.6)
        if self.talk > 0.05:      # eyes wide open while it talks to you
            return 0.0
        p = (t + self.KINDS.index(self.kind) * 1.4) % 4.2
        return max(0.0, 1 - abs(p - 0.1) / 0.1) if p < 0.2 else 0.0

    def draw(self, cv, t=0.0, glow=None):
        if self.talk_dy:
            cv = Xform(cv, 0, self.talk_dy)
        getattr(self, "_draw_" + self.kind)(cv, t, glow)
        if self.newlook and self.pin > 0:
            self._draw_badge(cv, glow, self.pin)
        elif self.badge > 0 and not self.newlook:
            self._draw_badge(cv, glow)

    @property
    def name(self):
        return NAMES[self.kind]

    def draw_name(self, cv, amount=1.0, size=34.0, dy=0.0):
        """Nameplate floating above the head; `amount` 0..1 pops it in (and fades it)."""
        if amount <= 0.01:
            return
        x, y = self.x, self.y - TOPS[self.kind] * self.k - 46 + dy
        pop = min(1.0, amount * 1.25) if amount < 1 else 1.0
        sz = size * (0.6 + 0.4 * pop)
        w = (len(self.name) * 0.62 + 1.1) * sz
        h = sz * 1.45
        k = min(1.0, amount)
        cv.polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)],
                   np.array([16, 18, 26]) * k + np.array([8, 8, 10]) * (1 - k))
        cv.polyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)],
                    self.full * 0.9 * k, 3, closed=True)
        cv.polygon([(x - 8, y + h / 2), (x + 8, y + h / 2), (x, y + h / 2 + 10)], self.full * 0.9 * k)
        cv.text(self.name, x, y + 1, sz, lighten(self.full, 1.35) * k)

    def _body(self, cv, pts, col):
        """Body blob; while `rough` > 0 the outline is a lumpy, uncarved version of itself."""
        if self.rough > 0:
            p = np.asarray(pts, np.float64)
            c0 = p.mean(axis=0)
            n = len(p)
            ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
            seed = self.KINDS.index(self.kind) * 1.7
            bump = (0.10 * np.sin(ang * 5 + seed) + 0.07 * np.sin(ang * 9 + seed * 2.3)
                    + 0.05 * np.sin(ang * 14 + seed * 0.7)) * self.rough
            pts = c0 + (p - c0) * (1 + bump)[:, None]
        blob(cv, pts, col)

    def badge_pos(self):
        """Where the pinned leaf badge sits (episodes 2-8)."""
        (x, y), (rx, ry) = self.body_center(), self.body_size()
        return x + rx * 0.6, y + ry * 0.32

    def _draw_badge(self, cv, glow, amount=None):
        """Small glowing leaf badge: they passed training and became Forest Keepers."""
        k = self.k
        bx, by = self.badge_pos()
        s = (self.badge if amount is None else amount) * k
        leaf = [(bx, by - 22 * s), (bx + 13 * s, by - 4 * s), (bx, by + 18 * s), (bx - 13 * s, by - 4 * s)]
        cv.circle(bx, by, 24 * s, np.array([40, 34, 20]))
        cv.circle(bx, by, 21 * s, HAT)
        cv.polygon(leaf, np.array([70, 170, 90]))
        cv.line(bx, by - 18 * s, bx, by + 14 * s, np.array([40, 110, 60]), 2.5 * s)
        if glow is not None:
            glow.begin(cv)
            cv.circle(bx, by, 26 * s, np.array([120, 220, 140]) * 0.35 * self.badge)
            glow.end(cv)

    # ----- 1. Toby's: blue, three eyes, claws, wheels -----

    def _draw_wheels(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        bob = a * 3 * math.sin(t * 2.2) * k
        wr = 46 * k
        by = y - 210 * k + bob
        c = self.part(cv, "wheels")
        if c is not None:
            # axle + wheels, centre strut up into the body (drawn behind it), bolted at the axle
            c.polygon([(x - 120 * k, y - wr - 8 * k), (x + 120 * k, y - wr - 8 * k),
                       (x + 120 * k, y - wr + 8 * k), (x - 120 * k, y - wr + 8 * k)], STEEL * 0.8)
            for sx in (-1, 1):
                wx = x + sx * 112 * k
                c.circle(wx, y - wr, wr, RUBBER)
                c.circle(wx, y - wr, wr * 0.55, CLAW * 0.75)
                for i in range(5):
                    ang = self.wheel_rot + i * 2 * math.pi / 5
                    c.line(wx, y - wr, wx + math.cos(ang) * wr * 0.5, y - wr + math.sin(ang) * wr * 0.5,
                           STEEL * 0.6, 3 * k)
                c.circle(wx, y - wr, wr * 0.16, lighten(STEEL, 1.4))
            c.polygon([(x - 16 * k, by), (x + 16 * k, by), (x + 22 * k, y - wr), (x - 22 * k, y - wr)],
                      CLAW * 0.72)
            c.line(x - 16 * k, by, x - 22 * k, y - wr, CLAW, 2.5 * k)
            c.polygon([(x - 44 * k, y - wr - 10 * k), (x + 44 * k, y - wr - 10 * k),
                       (x + 44 * k, y - wr + 12 * k), (x - 44 * k, y - wr + 12 * k)], CLAW * 0.8)
            for bx in (-28, 0, 28):
                c.circle(x + bx * k, y - wr + 1 * k, 5 * k, lighten(STEEL, 1.5))
        c = self.part(cv, "arms")
        if c is not None:
            for sx in (-1, 1):
                wave = a * 0.25 * math.sin(t * 1.6 + sx) + self.punch * (sx > 0)
                sh = (x + sx * 100 * k, by + 10 * k)
                el = (sh[0] + sx * 70 * k, sh[1] + 30 * k - wave * 40 * k)
                hd = (el[0] + sx * (30 + 60 * self.punch * (sx > 0)) * k, el[1] - 60 * k - wave * 30 * k)
                reaching = bool(self.arm_to) and sx in self.arm_to
                w_ = self.arm_w.get(sx, 1.0) if reaching else 1.0
                if self.arm_swing is not None and (not reaching or w_ < 1.0):   # hanging, swinging
                    el, hd = self.hang_arm(sh, sx, (WHEELS_UPPER + WHEELS_FORE) * k * 0.9, 0.6, 0.4,
                                           WHEELS_UPPER * k, WHEELS_FORE * k)
                    self.arm_len[sx] = (sh, el, hd)
                if reaching:                            # reaching for a point: fixed-length bones, elbow down
                    tx_, ty_ = self.arm_to[sx]
                    hd = (hd[0] + (tx_ - hd[0]) * w_, hd[1] + (ty_ - hd[1]) * w_)   # part-way from where it was
                    pref = (getattr(self, "elbow_pref", None) or {}).get(sx, (sx * 0.5, 1.0))   # (a scene may keep the
                    el = two_bone(sh, hd, WHEELS_UPPER * k, WHEELS_FORE * k, sx, pref)          # elbow on one side)
                    if self.clamp_reach and math.hypot(hd[0] - sh[0], hd[1] - sh[1]) > (WHEELS_UPPER + WHEELS_FORE) * k * 0.999:
                        # out of reach: the hand stops where the arm ends (only then: in two_bone's swing band the
                        # bones are foreshortened together and the hand is right on the point, FK0017)
                        d_ = math.hypot(hd[0] - el[0], hd[1] - el[1]) or 1.0
                        hd = (el[0] + (hd[0] - el[0]) / d_ * WHEELS_FORE * k, el[1] + (hd[1] - el[1]) / d_ * WHEELS_FORE * k)
                    self.arm_len[sx] = (sh, el, hd)
                c.line(*sh, *el, CLAW * 0.8, 18 * k)
                c.line(*el, *hd, CLAW * 0.8, 16 * k)
                c.circle(*el, 12 * k, CLAW)
                snap = 0.35 + a * 0.25 * (0.5 + 0.5 * math.sin(t * 2.4 + sx))
                if self.grip > 0.01:                     # holding something: the pincers close on it
                    snap += (0.08 - snap) * self.grip
                for side in (-1, 1):   # two pincer jaws
                    base = math.atan2(hd[1] - el[1], hd[0] - el[0]) + side * snap
                    tip = (hd[0] + math.cos(base) * 70 * k, hd[1] + math.sin(base) * 70 * k)
                    mid = (hd[0] + math.cos(base - side * 0.45) * 42 * k, hd[1] + math.sin(base - side * 0.45) * 42 * k)
                    jaw = [hd, mid, tip, (hd[0] + math.cos(base + side * 0.25) * 34 * k,
                                          hd[1] + math.sin(base + side * 0.25) * 34 * k)]
                    c.polygon(jaw, CLAW)
                    c.polyline(jaw, CLAW * 0.55, 2, closed=True)
                c.circle(*hd, 14 * k, CLAW * 0.9)
        # body: a short, wide stump
        self._body(cv, ellipse(x, by, 112 * k, 118 * k, 56), col)
        grain(cv, x, by + 60 * k, 70 * k, 30 * k, col)
        c = self.part(cv, "eyes")
        if c is not None:
            lk, bl = self._look(t), self._blink(t)
            for i, ex in enumerate((-56, 0, 56)):
                ey = by - 52 * k - (14 * k if i == 1 else 0)
                eye(c, x + ex * k, ey, 25 * k, lk, bl, glow, a, col, self.lid_top, 0.5, self.cheek)
            if self.talk > 0.02:     # talking: the smile opens into a little round mouth
                c.polygon(ellipse(x, by + 22 * k, 24 * k, (6 + 16 * self.talk) * k, 24), MOUTH)
            c.arc(x, by + 4 * k, 34 * k, 20, 160, PUPIL, 4 * k)        # smile
        self._orb(self.face(cv), x, by + 58 * k, 18 * k, glow, a, t, self.orb_in, self.flash, self.job)

    # ----- 2. Orange: friendly Cthulhu, many tentacles -----

    def _draw_tentacles(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        tt = t * a + self.gait * 0.5
        bob = a * 5 * math.sin(t * 1.4) * k * self.float
        hy = y - 305 * k + bob
        c = self.part(cv, "wings")
        if c is not None:
            amp = 0.15 if self.wing_amp is None else self.wing_amp
            spd = 2.0 if self.wing_speed is None else self.wing_speed
            for sx in (-1, 1):
                flap = a * amp * math.sin(t * spd + self.wing_phase)
                wing = [(x + sx * 80 * k, hy - 10 * k),
                        (x + sx * 190 * k, hy - (110 + flap * 80) * k),
                        (x + sx * 170 * k, hy - 40 * k),
                        (x + sx * 200 * k, hy - (20 + flap * 40) * k),
                        (x + sx * 150 * k, hy + 20 * k),
                        (x + sx * 90 * k, hy + 30 * k)]
                if self.wing_up:                 # pricked up (surprised): the whole wing turns up about its root
                    th = -sx * 0.55 * self.wing_up
                    rx, ry = wing[0]
                    wing = [(rx + (px - rx) * math.cos(th) - (py - ry) * math.sin(th),
                             ry + (px - rx) * math.sin(th) + (py - ry) * math.cos(th)) for px, py in wing]
                c.polygon(wing, self.parts_col.get("wings", np.asarray(col) * 0.6))
                c.polyline(wing, np.asarray(col) * 0.4, 2, closed=True)
        c = self.part(cv, "legs")
        if c is not None and self.feet is not None:     # walking: six legs planted, each one fixed length
            self.leg_len = []
            for i, ft in enumerate(self.feet):
                if i in self.legs_up:
                    continue
                u = (i - 2.5) / 2.5
                self.leg_len.append(planted_tentacle(c, self.leg_root(i, t), ft, 275 * k, 44 * k,
                                                     self.parts_col.get("legs", np.asarray(col) * 0.82),
                                                     1 if u > 0 else -1, self.parts_col.get("suckers")))
        elif c is not None:         # six leg tentacles, splayed on the ground
            for i in range(6):
                u = (i - 2.5) / 2.5
                ang = math.pi / 2 - u * 1.05
                tentacle(c, x + u * 80 * k, hy + 70 * k, 275 * k, ang, 44 * k,
                         self.parts_col.get("legs", np.asarray(col) * 0.82), tt, i * 1.3,
                         curl=-0.45 if u > 0 else 0.45, sucker=self.parts_col.get("suckers"))
        self._body(cv, ellipse(x, hy, 118 * k, 128 * k, 56), col)      # head: a tall dome
        grain(cv, x, hy - 70 * k, 60 * k, 26 * k, col)
        c = None if "beard" in self.hide else self.part(cv, "beard")
        if self.newlook and "beard" not in self.old and c is not None:     # no beard: a smiling mouth
            for sx in (-1, 1):
                blush(c, x + sx * 74 * k, hy + 26 * k, k, col, a)
            smile_mouth(c, x, hy + 56 * k, 56 * k, self.smile, self.talk, col, k, depth=1.2, awake=a)
        elif c is not None:
            beard(c, x, hy, k, col, tt, t, self.talk)
        c = self.part(cv, "eyes")
        if c is not None:
            lk, bl = self._look(t), self._blink(t)
            for sx in (-1, 1):
                eye(c, x + sx * 48 * k, hy - 20 * k, 32 * k, lk, bl, glow, a, col, self.lid_top, 0.5, self.cheek)
        self._orb(self.face(cv), x, hy - 92 * k, 17 * k, glow, a, t, self.orb_in, self.flash, self.job)

    # ----- 3. Purple: tall, long legs, branch antlers, one big eye, all sharp teeth -----

    def _draw_teeth(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        sway = a * 4 * math.sin(t * 1.1) * k
        hip = y - 230 * k
        c = self.part(cv, "legs")
        if c is not None and self.feet is not None:    # walking (flat look): planted feet, two fixed-length bones
            self.leg_len = []
            f = smoothstep(min(abs(self._legs_turn()), 1.0))
            back = -1.0 if self._legs_turn() >= 0 else 1.0    # a bird's knee points back, away from where he goes
            if self.knee_fwd:                                 # ep 14 on: a person's knee, forward, the way he goes
                back = -back
            for sx in self.leg_order():
                ft = self.feet[(sx + 1) // 2]
                hx = x + sx * 40 * k * self.narrow()
                fy = ft[1] - 8 * k
                kn = bent_knee((hx, hip), (ft[0], fy), TWIGS_THIGH * k, TWIGS_SHIN * k, sx * (1 - f) + back * f)
                c.line(hx, hip, *kn, np.asarray(col) * 0.78, 22 * k)
                c.line(*kn, ft[0], fy, np.asarray(col) * 0.78, 18 * k)
                c.circle(*kn, 12 * k, np.asarray(col) * 0.9)
                for toe in (-1, 0, 1):
                    c.line(ft[0], fy, ft[0] + toe * 22 * k + sx * 6 * k, fy + 8 * k, np.asarray(col) * 0.6, 8 * k)
                self.leg_len.append(((hx, hip), kn, (ft[0], fy)))
        elif c is not None:         # long legs with backward knees and three-toed feet
            for sx in (-1, 1):
                hx = x + sx * 40 * k
                lift = self.walk * 34 * k * max(0.0, math.sin(self.gait + (sx > 0) * math.pi))
                kn = (hx + sx * 30 * k + sway + lift * 0.6, hip + 110 * k - lift * 0.5)
                ft = (hx + sx * 10 * k + lift * 0.4, y - 8 * k - lift)
                c.line(hx, hip, *kn, np.asarray(col) * 0.78, 22 * k)
                c.line(*kn, *ft, np.asarray(col) * 0.78, 18 * k)
                c.circle(*kn, 12 * k, np.asarray(col) * 0.9)
                for toe in (-1, 0, 1):
                    c.line(*ft, ft[0] + toe * 22 * k + sx * 6 * k, ft[1] + 8 * k, np.asarray(col) * 0.6, 8 * k)
        cy = hip - 120 * k + sway * 0.3
        c = self.part(cv, "arms")
        if c is not None:           # thin long arms
            for sx in (-1, 1):
                sh, el, hd = self._teeth_arm(sx, t, x + sway, cy)
                reaching = bool(self.arm_to) and sx in self.arm_to
                w_ = self.arm_w.get(sx, 1.0) if reaching else 1.0
                if self.arm_swing is not None and (not reaching or w_ < 1.0):   # hanging, swinging
                    el, hd = self.hang_arm(sh, sx, (TWIGS_UPPER + TWIGS_FORE) * k * 0.93, 0.16, 0.42,
                                           TWIGS_UPPER * k, TWIGS_FORE * k)
                    self.arm_len[sx] = (sh, el, hd)
                if reaching:                            # reaching for a point: fixed-length bones, elbow down
                    tx_, ty_ = self.arm_to[sx]
                    hd = (hd[0] + (tx_ - hd[0]) * w_, hd[1] + (ty_ - hd[1]) * w_)   # part-way from where it was
                    el = two_bone(sh, hd, TWIGS_UPPER * k, TWIGS_FORE * k, sx, (sx * 0.4, 1.0))
                    if self.clamp_reach and math.hypot(hd[0] - sh[0], hd[1] - sh[1]) > (TWIGS_UPPER + TWIGS_FORE) * k * 0.999:
                        # out of reach: the hand stops where the arm ends (only then, as for Wheels)
                        d_ = math.hypot(hd[0] - el[0], hd[1] - el[1]) or 1.0
                        hd = (el[0] + (hd[0] - el[0]) / d_ * TWIGS_FORE * k, el[1] + (hd[1] - el[1]) / d_ * TWIGS_FORE * k)
                    self.arm_len[sx] = (sh, el, hd)
                c.line(*sh, *el, np.asarray(col) * 0.8, 13 * k)
                c.line(*el, *hd, np.asarray(col) * 0.8, 11 * k)
                if sx in self.bare:                # the empty wrist socket the new hand fits into
                    c.circle(*hd, 9 * k, CLAW * 0.72)
                    c.circle(*hd, 4.5 * k, CLAW * 0.4)
                elif self.hands:
                    self._twigs_hand(c, hd, el, sx)
                elif self.saws:
                    self._wrist_saw(c, hd, el, sx)
                else:
                    for f in (-1, 0, 1):
                        c.line(*hd, hd[0] + f * 14 * k, hd[1] + 22 * k, np.asarray(col) * 0.62, 6 * k)
        self._body(cv, ellipse(x + sway, cy, 92 * k, 150 * k, 60), col)    # body: tall egg
        grain(cv, x + sway, cy + 90 * k, 50 * k, 22 * k, col)
        c = self.part(cv, "antlers")
        if c is not None:
            # branch antlers: they grow out of the head, so the colour fades into wood along them
            top = cy - 146 * k
            base = np.asarray(col) * 0.92

            def branch(p0, p1, u0, u1, w0, w1, n=8):
                for m in range(n):
                    a0, a1 = m / n, (m + 1) / n
                    q0 = (p0[0] + (p1[0] - p0[0]) * a0, p0[1] + (p1[1] - p0[1]) * a0)
                    q1 = (p0[0] + (p1[0] - p0[0]) * a1, p0[1] + (p1[1] - p0[1]) * a1)
                    f = smoothstep(u0 + (u1 - u0) * (a0 + a1) / 2)
                    c.line(*q0, *q1, base * (1 - f) + WOOD * f, w0 + (w1 - w0) * (a0 + a1) / 2)

            for sx in (-1, 1):
                b0 = (x + sway + sx * 30 * k, top + 40 * k)          # rooted inside the head
                b1 = (b0[0] + sx * 46 * k, b0[1] - 98 * k)
                b2 = (b1[0] + sx * 34 * k, b1[1] - 56 * k)
                branch(b0, b1, 0.0, 0.55, 20 * k, 12 * k)
                branch(b1, b2, 0.55, 0.9, 11 * k, 9 * k)
                branch(b1, (b1[0] - sx * 26 * k, b1[1] - 46 * k), 0.55, 1.0, 8 * k, 6 * k, 5)
                branch(b2, (b2[0] + sx * 30 * k, b2[1] - 10 * k), 0.9, 1.0, 6 * k, 5 * k, 4)
                branch(b2, (b2[0] - sx * 6 * k, b2[1] - 36 * k), 0.9, 1.0, 6 * k, 5 * k, 4)
        c = self.part(cv, "eye")
        if c is not None and self.newlook and "eye" not in self.old:   # softer: big iris, a lid, a brow
            ex, ey = x + sway, cy - 58 * k
            eye(c, ex, ey, 44 * k, self._look(t), self._blink(t), glow, a, col, self.lid_top, 0.62, self.cheek)
            if self.brow_on > 0:
                b = self.brow
                off = -(1 - self.brow_on) ** 2 * self.reach
                arch = [(ex + u * 24 * k, ey + off - (58 + 8 * b) * k - (7 + 6 * b) * k * (1 - u * u))
                        for u in np.linspace(-1, 1, 15)]
                c.polyline(arch, np.asarray(col) * 0.5 if self.brow_on >= 1 else lighten(WOOD, 0.9), 6 * k)
                for q in (arch[0], arch[-1]):
                    c.circle(*q, 3 * k, np.asarray(col) * 0.5 if self.brow_on >= 1 else lighten(WOOD, 0.9))
        elif c is not None:         # one big eye
            eye(c, x + sway, cy - 62 * k, 44 * k, self._look(t), self._blink(t), glow, a, col)
        c = None if "mouth" in self.hide else self.part(cv, "mouth")
        if c is not None and self.newlook and "mouth" not in self.old:     # a wide grin, rounded teeth
            for sx in (-1, 1):
                blush(c, x + sway + sx * 58 * k, cy + 8 * k, k, col, a)
            # no teeth once the factory has given him hands (owner 2026-11-03: same mouth, no teeth), nor in the flat
            # look (owner 2026-11-04: "they should not have teeth")
            nt = self.hands or getattr(c, "flat_look", False)
            smile_mouth(c, x + sway, cy + 28 * k, 58 * k, self.smile, self.talk, col, k, teeth=0 if nt else 4,
                        depth=1.5, awake=a)
        elif c is not None:         # wide mouth: every tooth sharp, top and bottom rows interlocking
            fang_mouth(c, x + sway, cy + 30 * k, k, col, a, t, self.talk)
        self._orb(self.face(cv), x + sway, cy + 104 * k, 16 * k, glow, a, t, self.orb_in, self.flash, self.job)

    # ----- 4. Gold: springs (episode 2) - coil-spring legs, big bulging eyes, wide grin -----

    def _draw_springs(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        sq = self.spring + a * 0.06 * math.sin(t * 3.0)
        by = y - (170 - 46 * sq) * k
        c = self.part(cv, "legs")
        if c is not None:           # two coil springs, flat feet
            for sx in (-1, 1):
                top, bot = by + 70 * k, y - 18 * k
                n = 7
                pts = [(x + sx * 50 * k, top)]
                for i in range(1, n * 2):
                    u = i / (n * 2)
                    pts.append((x + sx * (50 + (14 if i % 2 else -14)) * k + sx * 8 * k * u, lerp_(top, bot, u)))
                pts.append((x + sx * 58 * k, bot))
                c.polyline(pts, CLAW * 0.85, 9 * k)
                c.polyline(pts, lighten(CLAW, 1.2), 2.5 * k)
                c.polygon(ellipse(x + sx * 62 * k, y - 9 * k, 38 * k, 11 * k, 24), np.asarray(col) * 0.7)
        c = self.part(cv, "arms")
        if c is not None:           # short stubby arms, three fingers
            for sx in (-1, 1):
                wv = a * 0.3 * math.sin(t * 2.0 + sx)
                sh = (x + sx * 100 * k, by + 10 * k)
                hd = (sh[0] + sx * 46 * k, sh[1] - (10 + wv * 40) * k)
                if self.arm_swing is not None:
                    _, hd = self.hang_arm(sh, sx, 47 * k, 0.75 - 0.5 * max(0.0, -self.spring), 0.35)
                if self.arm_to and sx in self.arm_to:   # reaching for a point: the arm keeps its length
                    tx, ty = self.arm_to[sx]
                    d = math.hypot(tx - sh[0], ty - sh[1]) or 1.0
                    hd = (sh[0] + (tx - sh[0]) / d * 47 * k, sh[1] + (ty - sh[1]) / d * 47 * k)
                c.line(*sh, *hd, np.asarray(col) * 0.82, 16 * k)
                for f in (-1, 0, 1):
                    c.line(*hd, hd[0] + sx * 14 * k, hd[1] + f * 12 * k - 6 * k, np.asarray(col) * 0.65, 6 * k)
        c = self.part(cv, "eyes")
        if c is not None:           # bumps on top of the head carry two big eyes
            for sx in (-1, 1):
                c.circle(x + sx * 46 * k, by - 72 * k, 40 * k, col)
        self._body(cv, ellipse(x, by, 110 * k, 88 * k, 56), col)
        grain(cv, x, by + 50 * k, 66 * k, 24 * k, col)
        if c is not None:
            lk, bl = self._look(t), self._blink(t)
            for sx in (-1, 1):
                eye(c, x + sx * 46 * k, by - 76 * k, 30 * k, lk, bl, glow, a, col, self.lid_top, 0.5, self.cheek)
        c = self.part(cv, "mouth")
        if c is not None and self.newlook and a < 0.5:     # asleep: a closed, relaxed smile
            c.arc(x, by - 60 * k, 66 * k, 62, 118, np.asarray(col) * 0.45, 3.5 * k)
        elif c is not None:         # wide grin with a tongue
            mo = 1 + 0.8 * self.talk
            c.polygon(ellipse(x, by - 4 * k, 70 * k, 30 * mo * k, 30, 0.15, math.pi - 0.15), MOUTH)
            c.polygon(ellipse(x + 12 * k, by + (16 + 18 * self.talk) * k, 24 * k, 12 * k, 20), np.array([214, 96, 110]))
            c.arc(x, by - 4 * k, 70 * k, 9, 171, np.asarray(col) * 0.5, 3 * k)
        self._orb(self.face(cv), x, by + 62 * k, 15 * k, glow, a, t, self.orb_in, self.flash, self.job)

    # ----- 5. Teal: lantern (episode 2) - floats, dome head, glowing lantern belly, tendrils -----

    def _draw_lantern(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        bob = (4 + 10 * a) * math.sin(t * 1.3) * k
        by = y - 260 * k + bob
        c = self.part(cv, "tendrils")
        if c is not None:
            short = 0.72 if getattr(cv, "flat_look", False) else 1.0    # flat look: short, plump tendrils
            for i in range(7):
                u = (i - 3) / 3
                tentacle(c, x + u * 78 * k, by + 40 * k, (150 - 30 * abs(u)) * k * short, math.pi / 2 - u * 0.25,
                         13 * k / short, np.asarray(col) * 0.8, t * (0.3 + 0.7 * a) + self.gait * 0.3, i * 0.9,
                         curl=0.5 if u < 0 else -0.5)
        lamp = self.alive if self.lamp is None else self.lamp
        lamp *= 1 + self.talk * (0.35 + 0.25 * math.sin(t * 31))      # she talks with her light
        c = self.part(cv, "lamp")
        if c is not None:           # glass lantern hanging under the dome
            lx, ly = x, by + 82 * k
            c.line(lx, by + 30 * k, lx, ly - 34 * k, CLAW * 0.7, 4 * k)
            c.polygon([(lx - 30 * k, ly - 34 * k), (lx + 30 * k, ly - 34 * k), (lx + 36 * k, ly + 30 * k),
                       (lx - 36 * k, ly + 30 * k)], np.array([60, 70, 70]) + LAMP_C * 0.8 * lamp)
            c.polyline([(lx - 30 * k, ly - 34 * k), (lx + 30 * k, ly - 34 * k), (lx + 36 * k, ly + 30 * k),
                        (lx - 36 * k, ly + 30 * k)], CLAW * 0.6, 3 * k, closed=True)
            c.line(lx - 40 * k, ly - 38 * k, lx + 40 * k, ly - 38 * k, CLAW * 0.7, 6 * k)
            c.line(lx - 42 * k, ly + 33 * k, lx + 42 * k, ly + 33 * k, CLAW * 0.7, 6 * k)
            if glow is not None and lamp > 0:
                glow.begin(c)
                c.circle(lx, ly, 46 * k, LAMP_C * 0.75 * lamp)
                glow.end(c)
        # dome: half ellipse with a scalloped skirt
        dome = ellipse(x, by, 105 * k, 95 * k, 40, math.pi, 2 * math.pi)
        skirt = []
        for i in range(9):
            u = i / 8
            sxp = x + 105 * k - u * 210 * k
            skirt.append((sxp, by + (18 + 12 * (i % 2)) * k))
        self._body(cv, dome + skirt, col)
        grain(cv, x, by - 30 * k, 60 * k, 22 * k, col)
        c = self.part(cv, "eyes")
        if c is not None:
            lk, bl = self._look(t), self._blink(t)
            for sx in (-1, 1):
                eye(c, x + sx * 40 * k, by - 18 * k, 24 * k, lk, bl, glow, a, col, self.lid_top, 0.5, self.cheek)
        self._orb(self.face(cv), x, by - 66 * k, 15 * k, glow, a, t, self.orb_in, self.flash, self.job)

    # ----- 6. Red: digger (episode 2) - low and wide, shovel hands, hard hat with a lamp -----

    def _draw_digger(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, self.color
        bob = a * 2 * math.sin(t * 2.6) * k
        by = y - 150 * k + bob
        c = self.part(cv, "legs")
        if c is not None and self.feet is not None:    # walking (flat look): planted feet, one leg length
            self.leg_len = []
            for sx in self.leg_order():
                fx, fy = self.feet[(sx + 1) // 2]
                lx = x + sx * 62 * k * self.narrow()
                c.polygon([(lx - 24 * k, by + 60 * k), (lx + 24 * k, by + 60 * k), (fx + 26 * k, fy - 12 * k),
                           (fx - 26 * k, fy - 12 * k)], np.asarray(col) * 0.75)
                for f in (-1, 0, 1):
                    c.line(fx + f * 14 * k, fy - 14 * k, fx + f * 18 * k + sx * 4 * k, fy, TOOTH * 0.85, 6 * k)
                self.leg_len.append(((lx, by + 60 * k), (fx, fy - 12 * k)))
        elif c is not None:         # stubby legs with claws
            for sx in (-1, 1):
                lift = self.walk * 18 * k * max(0.0, math.sin(self.gait + (sx > 0) * math.pi))
                lx = x + sx * 62 * k
                c.polygon([(lx - 24 * k, by + 60 * k), (lx + 24 * k, by + 60 * k), (lx + 26 * k, y - 12 * k - lift),
                           (lx - 26 * k, y - 12 * k - lift)], np.asarray(col) * 0.75)
                for f in (-1, 0, 1):
                    c.line(lx + f * 14 * k, y - 14 * k - lift, lx + f * 18 * k + sx * 4 * k, y - lift,
                           TOOTH * 0.85, 6 * k)
        c = self.part(cv, "arms")
        if c is not None:           # short thick arms, big steel shovels
            for sx in (-1, 1):
                d = self.dig * (1.0 if sx > 0 else 0.7) + a * 0.12 * math.sin(t * 1.7 + sx)
                sh = (x + sx * 118 * k, by + 4 * k)
                hd = (sh[0] + sx * 56 * k, sh[1] + (30 + 70 * d) * k)
                ang = math.pi / 2 - sx * (0.5 - 0.6 * d)
                if self.paw_ang is not None and sx in self.paw_ang:   # digging: the arm swings at its own fixed length
                    ang = self.paw_ang[sx]
                    hd = (sh[0] + math.cos(ang) * 95 * k, sh[1] + math.sin(ang) * 95 * k)
                elif self.arm_swing is not None:         # walking: hanging at his sides, swinging (same length)
                    _, hd = self.hang_arm(sh, sx, 95 * k, 0.42, 0.4)
                    ang = math.atan2(hd[1] - sh[1], hd[0] - sh[0])
                c.line(*sh, *hd, np.asarray(col) * 0.8, 26 * k)
                if self.mole_claws:
                    self._mole_paw(c, hd, ang, sx, k)
                    continue
                c.circle(*hd, 14 * k, CLAW * 0.8)
                ca, sa = math.cos(ang), math.sin(ang)
                w0, w1, L = 26 * k, 40 * k, 70 * k
                pts = [(hd[0] - sa * w0, hd[1] + ca * w0), (hd[0] + sa * w0, hd[1] - ca * w0),
                       (hd[0] + ca * L + sa * w1, hd[1] + sa * L - ca * w1),
                       (hd[0] + ca * L - sa * w1, hd[1] + sa * L + ca * w1)]
                c.polygon(pts, CLAW)
                c.polyline(pts, CLAW * 0.55, 2.5, closed=True)
        self._body(cv, ellipse(x, by, 135 * k, 100 * k, 60), col)
        grain(cv, x, by + 55 * k, 80 * k, 28 * k, col)
        if self.orbless:
            c = self._part(cv, "hat")
            if c is not None:
                self._turning_hat(c, x, by - 82 * k, k)
            c = None
        else:
            c = self.part(cv, "hat")
        if c is not None and self.hat_orb:   # (owner + Toby, 2026-11-04) his orb is in the front of his hard hat:
            hy = by - 82 * k                 # his orb, his Forest Keeper badge, and his headlamp when he needs one
            c.polygon(ellipse(x, hy, 78 * k, 46 * k, 30, math.pi, 2 * math.pi), HAT)
            c.polygon([(x - 96 * k, hy), (x + 96 * k, hy), (x + 90 * k, hy + 12 * k), (x - 90 * k, hy + 12 * k)],
                      HAT * 0.85)
            ox, oy = x, hy - 21 * k
            c.circle(ox, oy, 27 * k, np.array([118, 82, 52]))         # a dark wooden mount, so it shows on the hat
            orb(c, ox, oy, 17 * k, glow, a, t, self.orb_in, self.flash, self.job)
            if self.flash > 0.01:                                    # the badge swells over the mount: a rim keeps
                rr = 17 * k * (1 + 0.45 * smoothstep(self.flash)) + 3 * k   # it from melting into the yellow hat
                c.circle(ox, oy, rr, np.array([118, 82, 52]), fill=False, width=6 * k)
            lamp = 0.0 if self.lamp is None else self.lamp           # lamp 0..1: the orb shines as a headlamp
            if lamp > 0:
                c.circle(ox, oy, 15 * k, np.asarray(ORB) * (1 - lamp) + np.array([255, 244, 214]) * lamp)
                if glow is not None:
                    glow.begin(c)
                    c.circle(ox, oy, (26 + 30 * lamp) * k, LAMP_C * 0.95 * lamp)
                    glow.end(c)
        elif c is not None:         # yellow hard hat with a small lamp
            hy = by - 82 * k
            c.polygon(ellipse(x, hy, 78 * k, 46 * k, 30, math.pi, 2 * math.pi), HAT)
            c.polygon([(x - 96 * k, hy), (x + 96 * k, hy), (x + 90 * k, hy + 12 * k), (x - 90 * k, hy + 12 * k)],
                      HAT * 0.85)
            c.line(x, hy - 46 * k, x, hy, HAT * 0.8, 6 * k)
            lamp = self.alive if self.lamp is None else self.lamp
            c.circle(x, hy - 18 * k, 13 * k, np.array([70, 70, 60]) + LAMP_C * 0.75 * lamp)
            if glow is not None and lamp > 0:
                glow.begin(c)
                c.circle(x, hy - 18 * k, 22 * k, LAMP_C * 0.7 * lamp)
                glow.end(c)
        c = self.part(cv, "face")
        if c is not None:           # small eyes, round pink snout, whiskers
            lk, bl = self._look(t), self._blink(t)
            for sx in (-1, 1):
                eye(c, x + sx * 44 * k, by - 30 * k, 18 * k, lk, bl, glow, a, col, self.lid_top, 0.5, self.cheek)
                for w in (-1, 1):
                    c.line(x + sx * 26 * k, by + 10 * k + w * 6 * k, x + sx * 70 * k, by + 4 * k + w * 14 * k,
                           np.asarray(col) * 0.45, 2 * k)
            if self.talk > 0.02 and getattr(c, "flat_look", False):   # flat look: a rounded open mouth and a
                tk = min(self.talk, 1.0)                                # pink tongue (no teeth: owner 2026-11-04)
                mw, mh, top = (14 + 14 * tk) * k, (4 + 24 * tk) * k, by + 29 * k
                c.polygon(ellipse(x, top, mw, mh, 32, 0.0, math.pi), MOUTH)
                if tk > 0.3:
                    c.polygon(ellipse(x, top + mh * 0.66, mw * 0.58, mh * 0.34, 24), np.array([226, 122, 132]))
            elif self.talk > 0.02:   # talking: a little mouth opens under the snout, the snout wiggles
                c.polygon(ellipse(x, by + 38 * k, 14 * k, (3 + 11 * self.talk) * k, 20), MOUTH)
            c.circle(x, by + 8 * k - 3 * k * self.talk * math.sin(t * 17), 24 * k, np.array([222, 130, 140]))
            c.circle(x - 8 * k, by + 6 * k, 5 * k, MOUTH)
            c.circle(x + 8 * k, by + 6 * k, 5 * k, MOUTH)
        if not self.hat_orb:        # (on his tummy it looked like a mouth: owner + Toby, 2026-11-04)
            self._orb(self.face(cv), x, by + 58 * k, 16 * k, glow, a, t, self.orb_in, self.flash, self.job)

    def _turning_hat(self, c, x, hy, k):
        """Digs' plain hard hat in the talking format, turning with his head (owner on Proof C, 2026-11-17: the hat
        turned with the face "doesn't really turn well", and one left facing forward "is not going to look natural").
        The dome keeps its shape (a round hat looks much the same from any side) and slides a little the way he
        turns; the ridge and the lamp on its front move round toward that side and narrow, as a real hat's front does.
        Drawn on the unturned canvas: the turn is in the geometry."""
        th = max(-1.0, min(1.0, self.turn)) * TURN_MAX * TURN_OF.get(self.kind, 1.0)   # the angle the face turns by
        dome, front, w = 8 * k * math.sin(th), 62 * k * math.sin(th), math.cos(th)
        hx = x + dome
        c.polygon(ellipse(hx, hy, 78 * k, 46 * k, 30, math.pi, 2 * math.pi), HAT)
        c.polygon([(hx - 96 * k, hy), (hx + 96 * k, hy), (hx + 90 * k, hy + 12 * k), (hx - 90 * k, hy + 12 * k)],
                  HAT * 0.85)
        rise = 46 * k * math.sqrt(max(0.0, 1 - (front / (78 * k)) ** 2))   # the dome's height where the ridge is
        c.line(hx + front, hy - rise, hx + front, hy, HAT * 0.8, max(2.0, 6 * k * w))
        lamp = self.alive if self.lamp is None else self.lamp
        c.ellipse(hx + front, hy - 0.4 * rise, 13 * k * w, 13 * k, np.array([70, 70, 60.0]) + LAMP_C * 0.75 * lamp)

    def _mole_paw(self, c, hd, ang, sx, k):
        """A mole's digging hand: a broad pink palm turned outward, furred at the wrist, and five long pale claws
        fanned along its edge (the way a real mole's spade-shaped forepaw looks)."""
        ca, sa = math.cos(ang), math.sin(ang)
        palm = np.array([236, 168, 160], np.float64)
        px, py = hd[0] + ca * 22 * k, hd[1] + sa * 22 * k
        pts = []
        for i in range(24):                                    # the palm: a rounded spade, wide across the fingers
            a = 2 * math.pi * i / 24
            u, v = 30 * k * math.cos(a), 40 * k * math.sin(a) * (1.0 if math.cos(a) > 0 else 0.8)
            pts.append((px + ca * u - sa * v, py + sa * u + ca * v))
        c.polygon(pts, palm)
        c.polyline(pts, palm * 0.62, 2.2 * k + 1, closed=True)
        c.circle(hd[0], hd[1], 17 * k, np.asarray(self.color) * 0.8)       # the furry wrist
        for f in range(5):                                     # the claws, along the far edge of the palm
            b = (f - 2) * 0.34
            ex, ey = math.cos(b), math.sin(b)
            bx, by_ = px + (ca * ex - sa * ey) * 26 * k, py + (sa * ex + ca * ey) * 26 * k
            L = (34 - 5 * abs(f - 2)) * k
            dx, dy = ca * math.cos(b * 0.6) - sa * math.sin(b * 0.6), sa * math.cos(b * 0.6) + ca * math.sin(b * 0.6)
            nx, ny = -dy, dx
            tip = (bx + dx * L + nx * 5 * k * sx, by_ + dy * L + ny * 5 * k * sx)
            c.polygon([(bx + nx * 7 * k, by_ + ny * 7 * k), tip, (bx - nx * 7 * k, by_ - ny * 7 * k)], TOOTH)
            c.polyline([(bx + nx * 7 * k, by_ + ny * 7 * k), tip, (bx - nx * 7 * k, by_ - ny * 7 * k)],
                       TOOTH * 0.62, 1.6 * k + 0.8, closed=True)

    # ----- 7. Sprout, the gardener (owner + Toby, 2026-11-03): an acorn with a seedling, two little hands -----

    def sprout_arm(self, t, dy=0.0, side=-1):
        """Sprout's arm (side -1 left, 1 right): (shoulder, hand) in world units; on the left, `wave` lifts the hand
        up beside the head (waving), `hold_out` holds it out level; dy = the body's current vertical offset."""
        k, a = self.k, self.alive
        by = self.y - 150 * k + a * 2 * math.sin(t * 2.0) * k + dy
        L = 57 * k
        if self.arm_swing is not None and (self.arm_ang if side < 0 else self.arm_ang_r) is None \
                and not (side < 0 and (self.wave > 0.01 or self.hold_out > 0.01)):
            sh = (self.x + side * 78 * k, by + 4 * k)
            return sh, self.hang_arm(sh, side, L, 0.5, 0.45)[1]
        if side > 0:
            sh = (self.x + 78 * k, by + 4 * k)
            ang = math.atan2(34, 46) if self.arm_ang_r is None else self.arm_ang_r
            return sh, (sh[0] + math.cos(ang) * L, sh[1] + math.sin(ang) * L)
        sh = (self.x - 78 * k, by + 4 * k)
        if self.arm_ang is not None:                 # the scene points the arm (reaching, carrying, setting down)
            return sh, (sh[0] + math.cos(self.arm_ang) * L, sh[1] + math.sin(self.arm_ang) * L)
        ang = math.atan2(34, -46)
        w = smoothstep(self.wave)
        ang = ang + (math.atan2(-56, -26) - ang) * w + w * 0.28 * math.sin(t * 9.0)
        ang = ang + (math.pi - ang) * smoothstep(self.hold_out) * (1 - w)
        return sh, (sh[0] + math.cos(ang) * L, sh[1] + math.sin(ang) * L)

    def acorn_xy(self, t, dy=0.0):
        """Where the acorn in Sprout's hand is."""
        sh, hd = self.sprout_arm(t, dy)
        return hd[0] - 6 * self.k, hd[1] - (3 + self.acorn_r) * self.k

    CAN_TIP = 0.5                 # how far (rad) Sprout tips its watering can to water
    CAN_S = 1.25                  # the watering can's size

    def _can_frame(self, t, dy=0.0):
        """The watering can in Sprout's right hand: (grip, tip angle); the hand holds its top handle."""
        sh, hd = self.sprout_arm(t, dy, 1)
        return hd, (self.CAN_TIP if getattr(self, "can_tip", None) is None else self.can_tip) * smoothstep(self.water)

    def _can_pt(self, hd, th, u, v):
        k, c_, s_ = self.k * self.CAN_S, math.cos(th), math.sin(th)
        return hd[0] + (u * c_ - v * s_) * k, hd[1] + (u * s_ + v * c_) * k

    def can_rose(self, t, dy=0.0):
        """Where the sprinkler rose of Sprout's watering can is (the drops fall from here)."""
        hd, th = self._can_frame(t, dy)
        return self._can_pt(hd, th, 70, 6)

    def can_bottom(self, hd):
        """How far below its grip the upright watering can's bottom is (to stand it on something)."""
        return self._can_pt(hd, 0.0, 0, 54)[1] - hd[1]

    def _draw_can(self, c, t, hd=None, th=None):
        """A little tin watering can hanging from Sprout's right hand by its top handle, its spout to the right;
        tipped (spout down) while it waters, then a soft shower of drops falls from the rose. hd/th: draw it
        standing somewhere else, by its grip (before Sprout picks it up)."""
        k = self.k * self.CAN_S
        if hd is None:
            hd, th = self._can_frame(t)
        P = lambda u, v: self._can_pt(hd, th, u, v)                         # noqa: E731
        tin, dark, lite = CLAW * 0.95, CLAW * 0.6, lighten(CLAW, 1.25)
        c.polyline([P(-14, 14), P(-12, 0), P(0, -6), P(14, 0), P(16, 14)], dark, 5 * k)     # the handle
        sp = [P(18, 34), P(62, 4), P(66, 9), P(22, 44)]                                     # the spout
        c.polygon(sp, tin)
        c.polyline(sp, dark, 2, closed=True)
        body = [P(-22, 12), P(24, 12), P(26, 54), P(-24, 54)]
        c.polygon(body, tin)
        c.polyline(body, dark, 2, closed=True)
        c.line(*P(-12, 18), *P(-13, 48), lite, 3 * k)                                        # a shine on the tin
        c.polygon([P(-22, 12), P(24, 12), P(24, 17), P(-22, 17)], lite)                      # the rim
        rose = [P(62, -2), P(74, 2), P(76, 14), P(64, 14)]                                  # the sprinkler rose
        c.polygon(rose, tin)
        c.polyline(rose, dark, 2, closed=True)
        for q in (0.3, 0.6, 0.9):
            hx, hy = P(75, 2 + 12 * q)
            c.circle(hx, hy, 1.5 * k, CLAW * 0.5)
        if self.water > 0.5:        # a soft shower of drops falling from the rose to the ground, once the can is
            rx, ry = P(76, 8)       # tipped past half; it starts and stops by fewer drops, always water-coloured
            fall_ = max(30 * k, (self.water_floor if self.water_floor is not None else self.y) - ry)   # (FK0024: the
            n_ = max(1, int(round(9 * min(1.0, (self.water - 0.5) / 0.4))))          # ramp was near-black drops)
            for i in range(n_):
                ph = (t * 0.9 + i * 0.37) % 1.0
                dx = rx + 4 * k + (i % 3) * 7 * k + ph * 16 * k
                dy = ry + (i % 3 - 1) * 5 * k + ph * ph * fall_
                c.polygon(ellipse(dx, dy, 2.6 * k, 4.2 * k, 12), WATER * (0.6 + 0.4 * (1 - ph)))

    def _sprout_shape(self, x, by, k):
        """The finished outline: the acorn nut (a little point at the bottom) and the cap dome on top."""
        body = ellipse(x, by, 88 * k, 96 * k, 60)
        body = [(px, py + max(0.0, py - by - 70 * k) * 0.55) for px, py in body]
        cy = by - 74 * k
        cap = ellipse(x, cy + 6 * k, 98 * k, 46 * k, 40, math.pi, 2 * math.pi) + \
            [(x + 96 * k, cy + 14 * k), (x - 96 * k, cy + 14 * k)]
        return body, cap, cy

    def _draw_sprout(self, cv, t, glow):
        k, x, y, a, col = self.k, self.x, self.y, self.alive, np.asarray(self.color)
        bob = a * 2 * math.sin(t * 2.0) * k
        by = y - 150 * k + bob
        c = self.part(cv, "legs")
        if c is not None and self.feet is not None:    # walking (flat look): planted feet, one leg length
            self.leg_len = []
            for sx in self.leg_order():
                fx, fy = self.feet[(sx + 1) // 2]
                lx = x + sx * 38 * k * self.narrow()
                c.line(lx, by + 70 * k, fx, fy - 10 * k, col * 0.74, 20 * k)
                for toe in (-1, 0, 1):
                    c.line(fx, fy - 10 * k, fx + toe * 17 * k, fy - 2 * k, col * 0.6, 7 * k)
                self.leg_len.append(((lx, by + 70 * k), (fx, fy - 10 * k)))
        elif c is not None:         # two short legs with root toes
            for sx in (-1, 1):
                lift = self.walk * 14 * k * max(0.0, math.sin(self.gait + (sx > 0) * math.pi))
                lx = x + sx * 38 * k
                c.line(lx, by + 70 * k, lx + sx * 4 * k, y - 10 * k - lift, col * 0.74, 20 * k)
                for toe in (-1, 0, 1):
                    c.line(lx + sx * 4 * k, y - 10 * k - lift, lx + sx * 4 * k + toe * 17 * k, y - 2 * k - lift,
                           col * 0.6, 7 * k)
        c = self.part(cv, "arm")
        if c is not None:           # the left arm, a little three-fingered hand (holding an acorn)
            sh, hd = self.sprout_arm(t)
            c.line(*sh, *hd, col * 0.8, 14 * k)
            if self.acorn:
                acorn_nut(c, hd[0] - 6 * k, hd[1] - (3 + self.acorn_r) * k, self.acorn_r * k)
            ang = math.atan2(hd[1] - sh[1], hd[0] - sh[0])
            g = 0.7 if self.acorn else 0.2
            for f in (-1, 0, 1):
                fa = ang + f * 0.36 * (1 - 0.5 * g)
                L = (17 - 3 * abs(f)) * k * (1 - 0.4 * g)
                c.line(*hd, hd[0] + math.cos(fa) * L, hd[1] + math.sin(fa) * L, col * 0.8, 7 * k)
                c.circle(hd[0] + math.cos(fa) * L, hd[1] + math.sin(fa) * L, 4 * k, col * 0.86)
            c.circle(*hd, 10 * k, col * 0.84)
        c = self.part(cv, "hand")
        if c is not None:           # the right arm, the same little three-fingered hand (it can carry a watering can)
            sh, hd = self.sprout_arm(t, 0.0, 1)
            c.line(*sh, *hd, col * 0.8, 14 * k)
            if self.can:
                self._draw_can(c, t)
            ang = math.atan2(hd[1] - sh[1], hd[0] - sh[0])
            g = 0.7 if self.can or self.grip > 0.5 else 0.2
            for f in (-1, 0, 1):
                fa = ang + f * 0.36 * (1 - 0.5 * g)
                L = (17 - 3 * abs(f)) * k * (1 - 0.4 * g)
                c.line(*hd, hd[0] + math.cos(fa) * L, hd[1] + math.sin(fa) * L, col * 0.8, 7 * k)
                c.circle(hd[0] + math.cos(fa) * L, hd[1] + math.sin(fa) * L, 4 * k, col * 0.86)
            c.circle(*hd, 10 * k, col * 0.84)
        body, cap, cy = self._sprout_shape(x, by, k)
        top, bot = by - 120 * k, y - 40 * k                  # the log's ends (it stands on the jig's peg)
        lt = (self.log_top or 0.0) * k
        yr = top - lt if self.turned <= 0 else top + (bot - top) * self.turned
        if self.turned < 1:         # still (partly) the oak log: bark below the cutter, turning on the lathe
            log = [(x - 100 * k, top - lt), (x + 100 * k, top - lt), (x + 100 * k, bot), (x - 100 * k, bot)]
            lp = clip_half(log, 1, yr, False)
            if len(lp) > 2:
                cv.polygon(lp, BARK_C)
                y0 = max(top - lt, yr)
                for q in range(9):  # bark ridges, moving round as it turns
                    u = ((q / 9.0) + self.spin / (2 * math.pi)) % 1.0
                    bx = x - 100 * k * math.cos(math.pi * u)
                    if 0.06 < u < 0.94:
                        cv.line(bx, y0 + 4 * k, bx, bot - 4 * k, BARK_C * (0.7 + 0.25 * math.sin(math.pi * u)),
                                max(1.5, 5 * k))
                cv.polyline(lp, BARK_C * 0.6, 2.5, closed=True)
            if yr <= top - lt + 1:  # the cut end on top: fresh wood with its rings
                cv.polygon(ellipse(x, top - lt, 100 * k, 16 * k, 32), lighten(WOOD, 1.25))
                for f in (0.35, 0.65):
                    cv.polyline(ellipse(x, top - lt, 100 * k * f, 16 * k * f, 28), WOOD, 1.5, closed=True)
            else:                   # where the cutter is: a pale ring where the bark comes off
                cv.polygon(ellipse(x, yr, 100 * k, 12 * k, 28, 0, math.pi), lighten(WOOD, 1.3))
        if yr > top:                # the turned shape above the cutter
            bp = clip_half(body, 1, yr, True)
            if len(bp) > 2:
                blob(cv, bp, col)
                if self.turned >= 1:
                    grain(cv, x, by + 54 * k, 54 * k, 24 * k, col)
            cp = clip_half(cap, 1, yr, True)
            if len(cp) > 2:
                cv.polygon(cp, col)
                if self.turned >= 1:
                    xs = x - 98 * k + 196 * k * self.stained
                    st = clip_half(cp, 0, xs, True) if self.stained < 1 else cp
                    if self.stained > 0 and len(st) > 2:
                        cv.polygon(st, CAP)
                    xc = x - 100 * k + 200 * k * self.carved
                    for row in range(3):
                        for j in range(-4 + row, 5 - row):
                            sx_, sy_ = x + j * 21 * k, cy + 4 * k - row * 14 * k
                            if sx_ < xc and self.carved > 0:
                                sc = CAP if sx_ < xs else col
                                cv.arc(sx_, sy_, 10 * k, 20, 160, np.asarray(sc) * 0.72, 2.5 * k)
                cv.polyline(cp, (CAP if self.stained >= 1 else col) * 0.6, 2.5, closed=True)
        if self.turned >= 1:
            c = self.part(cv, "seed")
            if self._part(cv, "seed") is not cv and self.carved >= 1:    # the little hole in the cap where the seedling goes
                cv.polygon(ellipse(x, cy - 37 * k, 9 * k, 4 * k, 16), CAP * 0.45)
            if c is not None:
                seedling(c, x, cy - 36 * k, k, t * a, fold=self.leaf_fold)
            c = self.part(cv, "face")
            if c is not None:
                lk, bl = self._look(t), self._blink(t)
                for sx in (-1, 1):
                    eye(c, x + sx * 36 * k, by - 14 * k, 26 * k, lk, bl, glow, a, col, self.lid_top, 0.52, self.cheek)
                    blush(c, x + sx * 54 * k, by + 24 * k, k, col, a)
                smile_mouth(c, x, by + 36 * k, 30 * k, self.smile, self.talk, col, k, depth=1.0, awake=a)
            oy = by + SPROUT_ORB_DY * k
            if self.orbless:                 # talking format: no socket, no rim (owner 2026-11-17)
                return
            if self.socket > 0:          # a carved rim round the socket, so the hole reads as a socket, never a mouth
                fc = self.face(cv)
                rs = min(1.0, self.socket)
                fc.circle(x, oy, 14 * k * 1.5 * rs, col * 0.62)                       # the rim's dark outer edge
                fc.circle(x, oy, 14 * k * 1.36 * rs, lighten(CAP, 1.3))               # the carved wooden rim
                fc.arc(x, oy, 14 * k * 1.27 * rs, 200, 340, lighten(CAP, 1.65), 2.4 * k)  # light on its top edge
            if self.socket >= 1:
                self._orb(self.face(cv), x, oy, 14 * k, glow, a, t, self.orb_in, self.flash, self.job)
                if self.orb_in <= 0.02:      # empty: the hole's inner shadow under the top edge (no light curve at
                    fc.arc(x, oy, 14 * k * 0.8, 200, 340, PUPIL * 0.4, 3.0 * k)   # the bottom: it read as a smile)
            elif self.socket > 0:
                cv.circle(x, oy, 14 * k * 0.95 * self.socket, np.array([16, 18, 26]))

    def saw_center(self, sx, t, dy=0.0):
        """World centre of Twigs' wrist saw on side sx (-1 left, 1 right) at time t, same arm maths as
        _draw_teeth (`punch` lifts the right one forward); dy = the body's current vertical offset."""
        k, a = self.k, self.alive
        sway = a * 4 * math.sin(t * 1.1) * k
        cy = self.y - 350 * k + sway * 0.3 + dy
        sh, el, hd = self._teeth_arm(sx, t, self.x + sway, cy)
        ax, ay = hd[0] - el[0], hd[1] - el[1]
        L = math.hypot(ax, ay) + 1e-9
        return hd[0] + ax / L * 26 * k, hd[1] + ay / L * 26 * k

    def _teeth_arm(self, sx, t, bx, cy):
        """Twigs' arm on side sx: (shoulder, elbow, hand). `punch` lifts the right one forward; with the wrist
        saws, `punch_l` lifts the left one the same way."""
        k, a = self.k, self.alive
        lift = self.punch if sx > 0 else (self.punch_l if self.saws or self.hands else 0.0)
        moves = sx > 0 or self.saws or self.hands
        sw = a * 0.3 * math.sin(t * 1.3 + sx * 1.7) - lift * 1.6
        sh = (bx + sx * 82 * k, cy + 10 * k)
        el = (sh[0] + sx * 46 * k, sh[1] + 80 * k + sw * 40 * k * moves)
        hd = (el[0] + sx * (10 + abs(sw) * 40) * k, el[1] + 80 * k + sw * 50 * k * moves)
        return sh, el, hd

    def _wrist_saw(self, c, hd, el, sx):
        """Twigs' wrist saw: a small toothed blade on a steel cuff where the hand was, the back half behind a
        guard. It spins with saw_spin; when running fast the teeth blur into a pale ring."""
        k = self.k
        ax, ay = hd[0] - el[0], hd[1] - el[1]
        L = math.hypot(ax, ay) + 1e-9
        ux, uy = ax / L, ay / L
        bx, by = hd[0] + ux * 26 * k, hd[1] + uy * 26 * k          # blade centre, just past the wrist
        r = 30 * k
        cuff = [(hd[0] - uy * 10 * k - ux * 14 * k, hd[1] + ux * 10 * k - uy * 14 * k),
                (hd[0] + uy * 10 * k - ux * 14 * k, hd[1] - ux * 10 * k - uy * 14 * k),
                (hd[0] + uy * 12 * k + ux * 12 * k, hd[1] - ux * 12 * k + uy * 12 * k),
                (hd[0] - uy * 12 * k + ux * 12 * k, hd[1] + ux * 12 * k + uy * 12 * k)]
        c.polygon(cuff, CLAW * 0.7)
        c.polyline(cuff, CLAW * 0.45, 2, closed=True)
        run = self.saw_run
        rot = self.saw_spin * sx
        teeth = 16
        pts = []
        for i in range(teeth * 2):
            a = rot + i * math.pi / teeth
            rr = r if i % 2 == 0 else r * 0.84
            pts.append((bx + math.cos(a) * rr, by + math.sin(a) * rr))
        c.polygon(pts, lighten(STEEL, 1.55) * (1 - 0.25 * run) + np.array([200, 204, 212]) * 0.25 * run)
        if run > 0.3:                                               # spinning: the teeth blur into a ring
            c.circle(bx, by, r * 0.96, lighten(STEEL, 1.7), False, max(1.5, r * 0.16 * run))
        c.circle(bx, by, r * 0.74, lighten(STEEL, 1.2))
        for i in range(3):
            a = rot + i * 2 * math.pi / 3
            c.line(bx, by, bx + math.cos(a) * r * 0.6, by + math.sin(a) * r * 0.6, STEEL * 0.8, max(1.5, 3 * k))
        # guard over the half of the blade nearest the arm
        a0 = math.atan2(-uy, -ux)
        guard = [(bx + math.cos(a0 + d) * r * 1.12, by + math.sin(a0 + d) * r * 1.12)
                 for d in np.linspace(-math.pi / 2, math.pi / 2, 12)]
        guard += [(bx + math.cos(a0 + d) * r * 0.5, by + math.sin(a0 + d) * r * 0.5)
                  for d in np.linspace(math.pi / 2, -math.pi / 2, 8)]
        c.polygon(guard, np.asarray(self.color) * 0.62)
        c.polyline(guard, np.asarray(self.color) * 0.4, 2, closed=True)
        c.circle(bx, by, r * 0.2, CLAW)
        c.circle(bx, by, r * 0.08, CLAW * 0.5)

    def _blade_frame(self, hd, el, sx):
        """Twigs' forearm: unit vector along it (elbow -> hand) and the outward normal (away from the body)."""
        ax, ay = hd[0] - el[0], hd[1] - el[1]
        L = math.hypot(ax, ay) + 1e-9
        ux, uy = ax / L, ay / L
        nx, ny = -uy, ux
        if nx * sx < 0:
            nx, ny = -nx, -ny
        return ux, uy, nx, ny

    def _blade(self, sx):
        return self.blades if sx > 0 or self.blades_l is None else self.blades_l

    def blade_tip(self, sx, t, dy=0.0):
        """World position of the tip of Twigs' pruning blade on side sx at time t (at the sheath mouth when
        retracted); dy = the body's current vertical offset."""
        k, a = self.k, self.alive
        sway = a * 4 * math.sin(t * 1.1) * k
        cy = self.y - 350 * k + sway * 0.3 + dy
        sh, el, hd = self._teeth_arm(sx, t, self.x + sway, cy)
        ux, uy, nx, ny = self._blade_frame(hd, el, sx)
        out = (6 + 74 * smoothstep(self._blade(sx))) * k
        return hd[0] + nx * 13 * k + ux * out, hd[1] + ny * 13 * k + uy * out

    def _twigs_hand(self, c, hd, el, sx):
        """Twigs' hand: a round wooden palm, three fingers and a thumb (curled by `grip`). Along the outside of the
        forearm a steel sheath; the pruning blade slides out of it past the hand with `blades` (gently curved,
        small teeth on its outer edge, a rounded tip), so the hand stays free to hold things."""
        k, col = self.k, np.asarray(self.color)
        ux, uy, nx, ny = self._blade_frame(hd, el, sx)
        off = 13 * k                                           # the sheath runs along the outer side
        s0 = (el[0] + ux * 22 * k + nx * off, el[1] + uy * 22 * k + ny * off)
        s1 = (hd[0] + ux * 6 * k + nx * off, hd[1] + uy * 6 * k + ny * off)
        out = 74 * k * smoothstep(self._blade(sx))
        if out > 1:                                            # the blade, drawn first so it comes out of the sheath
            n = 24
            back, edge = [], []
            for i in range(n + 1):
                u = i / n
                bend = 8 * k * u * u                           # curves a little outward toward the tip
                w = 13 * k
                px, py = s1[0] + ux * (out * u - 10 * k) + nx * bend, s1[1] + uy * (out * u - 10 * k) + ny * bend
                back.append((px - nx * w * 0.4, py - ny * w * 0.4))
                tooth = (1.8 * k if i % 2 else 0.0) if 0 < i < n - 2 else 0.0      # fine pruning-saw teeth
                edge.append((px + nx * (w * 0.6 + tooth), py + ny * (w * 0.6 + tooth)))
            ex, ey = (back[-1][0] + edge[-1][0]) / 2, (back[-1][1] + edge[-1][1]) / 2
            tip = [(ex + (ux * math.cos(a) + nx * math.sin(a)) * w * 0.5, ey + (uy * math.cos(a) + ny * math.sin(a)) * w * 0.5)
                   for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]                  # a rounded end
            pts = back + tip + edge[::-1]
            c.polygon(pts, BLADE)
            c.polyline(back, lighten(BLADE, 1.12), max(1.5, 2.5 * k))       # a bright line along the back
            c.polyline(pts, BLADE * 0.62, max(1.5, 1.8 * k), closed=True)
        sh = [(s0[0] - nx * 6 * k, s0[1] - ny * 6 * k), (s0[0] + nx * 7 * k, s0[1] + ny * 7 * k),
              (s1[0] + nx * 8 * k, s1[1] + ny * 8 * k), (s1[0] - nx * 6 * k, s1[1] - ny * 6 * k)]
        c.polygon(sh, CLAW * 0.72)
        c.polyline(sh, CLAW * 0.45, 2, closed=True)
        for q in (0.25, 0.75):                                 # two rivets
            c.circle(s0[0] + (s1[0] - s0[0]) * q, s0[1] + (s1[1] - s0[1]) * q, 2.6 * k, lighten(STEEL, 1.5))
        # the hand, a little lighter than the arm so it reads
        hx, hy = hd[0] + ux * 12 * k, hd[1] + uy * 12 * k
        g = self.grip
        hc = col * 0.92
        for f in (-1, 0, 1):                                   # three fingers fanned a little
            ang = math.atan2(uy, ux) + f * 0.36 * (1 - 0.5 * g)
            L = (27 - 4 * abs(f)) * k * (1 - 0.45 * g)
            fx, fy = hx + math.cos(ang) * L, hy + math.sin(ang) * L
            c.line(hx, hy, fx, fy, hc * 0.9, 10 * k)
            c.circle(fx, fy, 5.5 * k, hc)
        b = 1.0 - 0.5 * g                                      # the thumb, on the inner side (away from the blade)
        tx = hx + (ux * math.cos(b) - nx * math.sin(b)) * 20 * k
        ty = hy + (uy * math.cos(b) - ny * math.sin(b)) * 20 * k
        c.line(hx, hy, tx, ty, hc * 0.9, 9 * k)
        c.circle(tx, ty, 5 * k, hc)
        c.circle(hx, hy, 15 * k, hc)                           # palm
        c.circle(hx - ux * 4 * k - nx * 4 * k, hy - uy * 4 * k - ny * 4 * k, 6 * k, lighten(hc, 1.12))

    def leg_root(self, i, t):
        """Where Hans' leg i (0..5, left to right) leaves his head."""
        k = self.k
        hy = self.y - 305 * k + self.alive * 5 * math.sin(t * 1.4) * k * self.float
        return self.x + (i - 2.5) / 2.5 * 80 * k * (1 + self.narrow()) / 2, hy + 70 * k

    def work_tentacle(self, cv, tx, ty, t, slot=0, grip=1.0, dy=0.0, root=None):
        """Hans works with his own tentacles: one more arm of the same tentacle, from the root ring
        under his head out to (tx, ty) and wrapped around it. `slot` picks the root (several can
        work at once: -2..2), `dy` is the body's current vertical offset (hops, climbing). Returns its root and its
        drawn length."""
        assert self.kind == "tentacles"
        k = self.k
        hy = self.y - 305 * k + dy + self.alive * 5 * math.sin(t * 1.4) * k * self.float
        side = 1 if tx >= self.x else -1
        rx = self.x + side * (40 + 22 * abs(slot)) * k
        ry = hy + (64 + 8 * abs(slot)) * k
        if root is not None:                       # a lifted leg working: from that leg's own root (leg_root)
            rx, ry = root
        L = reach_tentacle(cv, rx, ry, tx, ty, 50 * k, self.parts_col.get("legs", np.asarray(self.color) * 0.82), t,
                           1.3 * slot + 0.7, side, grip, sucker=self.parts_col.get("suckers"))
        return (rx, ry), L

    # ----- geometry the scene needs -----

    def body_center(self):
        """World position of the body's middle (where the grown wood lump sits)."""
        k = self.k
        dy = {"wheels": 210, "tentacles": 305, "teeth": 350, "springs": 170, "lantern": 260,
              "digger": 150, "sprout": 150}[self.kind]
        return self.x, self.y - dy * k

    def body_size(self):
        k = self.k
        rx, ry = {"wheels": (112, 118), "tentacles": (118, 128), "teeth": (92, 150), "springs": (110, 88),
                  "lantern": (105, 95), "digger": (135, 100), "sprout": (88, 96)}[self.kind]
        return rx * k, ry * k

    def orb_now(self, t):
        """Where the orb is drawn right now (idle bob, sway, squash and talking bounce included), unlike orb_pos."""
        k, x, y, a = self.k, self.x, self.y, self.alive
        if self.kind == "wheels":
            ox, oy = x, y - 210 * k + a * 3 * math.sin(t * 2.2) * k + 58 * k
        elif self.kind == "tentacles":
            ox, oy = x, y - 305 * k + a * 5 * math.sin(t * 1.4) * k - 92 * k
        elif self.kind == "teeth":
            sway = a * 4 * math.sin(t * 1.1) * k
            ox, oy = x + sway, y - 350 * k + sway * 0.3 + 104 * k
        elif self.kind == "springs":
            sq = self.spring + a * 0.06 * math.sin(t * 3.0)
            ox, oy = x, y - (170 - 46 * sq) * k + 62 * k
        elif self.kind == "lantern":
            ox, oy = x, y - 260 * k + (4 + 10 * a) * math.sin(t * 1.3) * k - 66 * k
        elif self.kind == "sprout":
            ox, oy = x, y - 150 * k + a * 2 * math.sin(t * 2.0) * k + SPROUT_ORB_DY * k
        else:
            ox, oy = x, y - 150 * k + a * 2 * math.sin(t * 2.6) * k + 58 * k
        return ox, oy + self.talk_dy

    def orb_pos(self):
        k, (x, y) = self.k, self.body_center()
        return x, y + {"wheels": 58, "tentacles": -92, "teeth": 104, "springs": 62, "lantern": -66,
                       "digger": 58, "sprout": SPROUT_ORB_DY}[self.kind] * k

    def part_anchor(self, name):
        """Attached position of a part's grip point (world), for the arm that carries it in."""
        k, (x, y) = self.k, self.body_center()
        off = {"wheels": {"wheels": (0, 164), "arms": (0, -110), "eyes": (0, -60)},
               "tentacles": {"legs": (0, 150), "wings": (0, -120), "beard": (0, 110), "eyes": (0, -20)},
               "teeth": {"legs": (0, 230), "arms": (0, 60), "antlers": (0, -230), "eye": (0, -62),
                         "mouth": (0, 30)},
               "springs": {"legs": (0, 120), "arms": (0, 10), "eyes": (0, -90), "mouth": (0, 10)},
               "lantern": {"tendrils": (0, 150), "lamp": (0, 90), "eyes": (0, -10)},
               "digger": {"legs": (0, 110), "arms": (0, 30), "hat": (0, -110), "face": (0, -10)},
               "sprout": {"legs": (0, 120), "arm": (-124, 38), "hand": (124, 38), "face": (0, -14),
                          "seed": (0, -110)}}[self.kind][name]
        return x + off[0] * k, y + off[1] * k
