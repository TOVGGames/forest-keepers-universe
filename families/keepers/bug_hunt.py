"""Forest Keepers episode 10: Bug Hunt (docs/engines/forest_keepers_bug_hunt.md), 16:9, ~6:30.

Owner idea (2026-11-01): the Keepers turn over logs and rocks and find the bugs of the forest. Every bug gets a
close-up and looks like the real bug (families/keepers/bugs.py, drawn in code to field-guide accuracy); a Keeper
identifies it in a field guide book; its name and a kid-friendly line about it show on screen (no narrator).

One act, one walk along a forest path at night, no cuts:
  HOOK   Digs is digging; an earthworm wiggles out. Glo has an idea; Wheels pushes the Keeper Field Guide over on
         its little reading cart, Glo's light opens it on the checklist: six empty frames. "Bug hunt: find six!"
  FINDS  six stops, one per Keeper, each its own way of looking: Digs digs (earthworm), Hans rolls a log over with
         his tentacles (pill bugs: one rolls up), Twigs peels back loose bark on a stump (millipede), Wheels lifts a
         flat rock with his claws (ground beetle), Springs bounces up to a tall plant (ladybug and its aphids), Glo
         dims his lantern by the ferns (fireflies). At each: Glo floats his big magnifying lens over the bug and the
         camera slowly closes in (the lens shows the bug big, from above, moving like the real one); Glo's light
         flare turns the guide's pages to the match and ticks it; the name card shows; the bug goes home and the
         hiding place is put back gently.
  END    fireflies rise all around; the checklist is full; everyone cheers; the camera pulls back. End sign.
"""
import math

import numpy as np

from families.foundry.keepers.common import Night, ellipse, lerp, rect, seg, smoothstep, smootherstep, tree
from families.foundry.products.monster import Xform, lighten
from families.foundry.tree_monsters import LAMP, LEAF as TREE_LEAF

from .animal_houses import G
from .bugs import BUGS, Frame, draw_bug
from .doorway import fade_clip, half_width
from .harvest_feast import cam_keys
from .tune_up import ORDER, Route, TuneAct, bump, work_flash
from families.foundry.keepers.forest import _firefly

# ----------------------------------------------------------------------------------------------- the props

LENS_R = 120.0
LENS_Y = G - 150.0                    # lens centre while it looks at a bug
GLO_Y = LENS_Y - 145.0                # Glo floats this high holding the lens by its handle
CART_W = 300.0                        # the open book's width on the reading cart
BOOK_Y = G - 238.0                    # the open book's middle
PAPER = np.array([236, 226, 198], np.float64)
PAPER_DARK = np.array([200, 186, 154], np.float64)
COVER = np.array([92, 120, 70], np.float64)
INK = np.array([62, 46, 34], np.float64)
BRASS = np.array([196, 160, 90], np.float64)
WOOD = np.array([142, 104, 66], np.float64)
BARK_C = np.array([86, 62, 44], np.float64)
ROCK_C = np.array([118, 116, 110], np.float64)
SOIL_C = np.array([70, 52, 38], np.float64)
FERN_C = np.array([58, 112, 58], np.float64)
TICK = np.array([70, 150, 70], np.float64)
CARD = np.array([240, 230, 204], np.float64)

FINDS = [  # in the order they are found; x = where the bug is
    dict(kind="earthworm", finder="digger", x=1700.0, place="soil"),
    dict(kind="pillbug", finder="tentacles", x=3300.0, place="log"),
    dict(kind="millipede", finder="teeth", x=4900.0, place="bark"),
    dict(kind="groundbeetle", finder="wheels", x=6500.0, place="rock", book=-540.0),   # room for Wheels
    dict(kind="ladybug", finder="springs", x=8100.0, place="plant"),
    dict(kind="firefly", finder="lantern", x=9700.0, place="ferns"),
]
WORK = {"digger": 140.0, "tentacles": 300.0, "teeth": 150.0, "wheels": -230.0, "springs": 150.0, "lantern": 0.0}
BOOK_DX = -340.0                       # the cart parks this far left of the bug
PUSH = 185.0                           # Wheels pushes the cart from this far behind it


def draw_cart(c, x, wheel_rot=0.0):
    """The Field Guide's reading cart: a slanted desk on a post, two little wheels, a push handle at the back."""
    wy = G - 22
    for wx in (x - 90, x + 90):
        c.circle(wx, wy, 22, WOOD * 0.55)
        c.circle(wx, wy, 15, WOOD * 0.8)
        for i in range(4):
            a = wheel_rot + i * math.pi / 2
            c.line(wx, wy, wx + 14 * math.cos(a), wy + 14 * math.sin(a), WOOD * 0.5, 3)
    rect(c, x - 110, G - 52, x + 110, G - 36, WOOD * 0.75)
    rect(c, x - 12, G - 150, x + 12, G - 44, WOOD * 0.7)
    c.polygon([(x - 170, BOOK_Y + 88), (x + 170, BOOK_Y + 88), (x + 160, BOOK_Y + 104), (x - 160, BOOK_Y + 104)],
              WOOD * 0.85)
    c.line(x - 110, G - 44, x - 190, G - 170, WOOD * 0.6, 8)                      # push handle
    c.line(x - 200, G - 172, x - 180, G - 168, WOOD * 0.7, 10)


def closed_book(c, x):
    """The Field Guide closed on its cart: a green cover with a leaf and the title."""
    y0, y1 = BOOK_Y - 86, BOOK_Y + 86
    c.polygon([(x - 4, y0 - 4), (x + 160, y0 - 4), (x + 164, y1 + 8), (x - 4, y1 + 8)], COVER * 0.8)
    c.polygon([(x, y0), (x + 152, y0), (x + 152, y1), (x, y1)], COVER)
    c.text("FIELD GUIDE", x + 76, y0 + 34, 15, PAPER)
    c.polygon(ellipse(x + 76, BOOK_Y + 20, 18, 32, 20), np.array([200, 190, 100]))
    c.line(x + 76, BOOK_Y - 8, x + 76, BOOK_Y + 50, np.array([150, 140, 70]), 3)


def draw_book(c, x, spread, flip=None, left=True, cover_flip=False):
    """The open Keeper Field Guide. spread(c, side, x0, x1, y0, y1) fills one page; flip = u 0..1 a page turning
    from the right page over to the left (the cover, the first time)."""
    y0, y1 = BOOK_Y - 86, BOOK_Y + 86
    c.polygon([(x - (160 if left else 4), y0 - 4), (x + 160, y0 - 4), (x + 164, y1 + 8),
               (x - (164 if left else 4), y1 + 8)], COVER * 0.8)
    for side in ((-1, 1) if left else (1,)):
        xa, xb = (x - 150, x - 4) if side < 0 else (x + 4, x + 150)
        pts = [(xa, y0 + (6 if side < 0 else 0)), (xb, y0 + (0 if side < 0 else 6)), (xb, y1), (xa, y1)]
        c.polygon(pts, PAPER)
        c.line(x + side * 6, y0 + 4, x + side * 6, y1, PAPER_DARK, 4)
        spread(c, side, xa, xb, y0, y1)
    c.line(x, y0, x, y1 + 4, COVER * 0.6, 3)
    if flip is not None:
        u = flip
        w = 146 * math.cos(math.pi * u)
        lift = 26 * math.sin(math.pi * u)
        tip = x + w
        col = COVER if cover_flip else PAPER
        c.polygon([(x, y0), (tip, y0 - lift), (tip, y1 - lift * 0.4), (x, y1)],
                  col * (0.82 + 0.18 * abs(math.cos(math.pi * u))))
        c.line(tip, y0 - lift, tip, y1 - lift * 0.4, PAPER_DARK, 2)


def page_lines(c, xa, xb, y, n, w=0.8):
    for i in range(n):
        L = (xb - xa - 30) * (w if i < n - 1 else 0.55)
        c.line(xa + 15, y + i * 14, xa + 15 + L, y + i * 14, PAPER_DARK * 0.9, 3)


def draw_lens(c, x, y, glass=1.0):
    """Glo's big magnifying lens: brass ring, wooden handle up into his tendrils, a soft sheen on the glass."""
    c.line(x, y - LENS_R - 70, x, y - LENS_R, WOOD * 0.8, 16)
    c.line(x - 5, y - LENS_R - 70, x - 5, y - LENS_R, lighten(WOOD, 1.2), 4)
    c.circle(x, y, LENS_R + 10, BRASS * 0.7, False, 14)
    c.circle(x, y, LENS_R + 10, BRASS, False, 8)
    if glass > 0:
        c.polyline(ellipse(x - 30, y - 34, LENS_R * 0.62, LENS_R * 0.5, 24, 3.6, 4.6), np.array([230, 236, 240]) * 0.7,
                   5)


def lens_ground(c, x, y, R, place, seed):
    """What the lens looks down at, magnified: soil, a stump's wood, a rock's damp underside, a leaf, a fern."""
    rs = np.random.default_rng(seed)
    if place in ("soil", "log", "rock"):
        base = SOIL_C * (0.85 if place == "rock" else 1.0)
        c.circle(x, y, R, base)
        for _ in range(70):                                       # crumbs, grains, little pebbles
            a, d = rs.uniform(0, 2 * math.pi), R * math.sqrt(rs.uniform())
            r = rs.uniform(2, 7)
            c.circle(x + d * math.cos(a), y + d * math.sin(a), r, base * rs.uniform(0.6, 1.4))
        for _ in range(4 if place != "rock" else 1):              # bits of dead leaf
            a, d = rs.uniform(0, 2 * math.pi), R * 0.8 * math.sqrt(rs.uniform())
            px, py, ang = x + d * math.cos(a), y + d * math.sin(a), rs.uniform(0, math.pi)
            f = Frame(px, py, rs.uniform(30, 55), ang)
            c.polygon(f.oval(0, 0, 0.5, 0.22, 16), np.array([132, 88, 44]) * rs.uniform(0.7, 1.0))
            c.polyline(f.pts([(-0.45, 0), (0.45, 0)]), np.array([90, 60, 30]), 1.5)
        for _ in range(3 if place == "rock" else 1):              # a few pebbles
            a, d = rs.uniform(0, 2 * math.pi), R * 0.85 * math.sqrt(rs.uniform())
            px, py, r = x + d * math.cos(a), y + d * math.sin(a), rs.uniform(10, 22)
            c.polygon(ellipse(px, py, r * 1.2, r, 18), ROCK_C * rs.uniform(0.7, 1.0))
            c.polygon(ellipse(px - r * 0.3, py - r * 0.3, r * 0.4, r * 0.25, 12), ROCK_C * 1.2)
    elif place == "bark":
        c.circle(x, y, R, np.array([176, 138, 96]))
        for i in range(-12, 13):                                   # the wood's grain under the bark
            yy = y + i * 10 + 3 * math.sin(i)
            c.polyline([(x - R + j * 12, yy + 3 * math.sin(j * 0.6 + i)) for j in range(21)],
                       np.array([150, 110, 74]), 2)
        for _ in range(5):
            a, d = rs.uniform(0, 2 * math.pi), R * 0.8 * math.sqrt(rs.uniform())
            c.polygon(ellipse(x + d * math.cos(a), y + d * math.sin(a), rs.uniform(6, 14), rs.uniform(3, 5), 10),
                      np.array([120, 86, 56]))
    elif place == "plant":
        c.circle(x, y, R, np.array([70, 140, 64]))
        c.line(x - R, y + 20, x + R, y - 10, np.array([150, 196, 120]), 6)          # the midrib
        for i in range(-5, 6):
            bx = x + i * 22
            by = y + 20 - (bx - x + R) / (2 * R) * 30
            c.line(bx, by, bx + 40, by - 60, np.array([110, 170, 96]), 3)
            c.line(bx, by, bx + 40, by + 60, np.array([110, 170, 96]), 3)
        c.circle(x - 30, y - 30, 40, np.array([86, 156, 76]))
    elif place == "ferns":
        c.circle(x, y, R, np.array([24, 40, 30]))
        for j in (-1, 0, 1):                                       # fern fronds, pinnae either side
            y0 = y + j * 70
            c.line(x - R, y0 + 10, x + R, y0 - 10, FERN_C * 0.8, 5)
            for i in range(-9, 10):
                px = x + i * 13
                py = y0 - i * 0.8
                for s in (-1, 1):
                    c.polygon([(px - 5, py), (px + 5, py), (px + 2, py + s * 30), (px - 2, py + s * 28)],
                              FERN_C * (0.8 + 0.08 * (i % 3)))


def aphid(c, x, y, L, t):
    """A green aphid (what the ladybug eats): pear-shaped, long legs, two little tubes at the back."""
    f = Frame(x, y, L, -0.4)
    for s in (-1, 1):
        for u in (0.2, 0.0, -0.2):
            c.polyline(f.pts([(u, s * 0.2), (u + 0.1, s * 0.5), (u + 0.05, s * 0.62)]), np.array([96, 140, 70]),
                       0.04 * L)
        c.polyline(f.pts([(-0.32, s * 0.12), (-0.55, s * 0.2)]), np.array([60, 100, 50]), 0.06 * L)
        c.polyline(f.pts([(0.4, s * 0.06), (0.7, s * 0.25), (0.95, s * 0.3)]), np.array([96, 140, 70]), 0.03 * L)
    c.polygon(f.oval(-0.05, 0.0, 0.42, 0.28, 24), np.array([150, 200, 96]))
    c.polygon(f.oval(0.38, 0.0, 0.12, 0.12, 12), np.array([140, 190, 90]))
    c.polygon(f.oval(0.0, -0.1, 0.2, 0.07, 12), np.array([200, 236, 150]))


def moth(c, x, y, t, s=1.0):
    """A little pale moth fluttering round Glo's lantern (moths come to the light)."""
    fl = abs(math.sin(t * 22))
    for sx in (-1, 1):
        c.polygon([(x, y), (x + sx * 14 * s * fl, y - 9 * s), (x + sx * 16 * s * fl, y + 3 * s), (x + sx * 4 * s, y + 6 * s)],
                  np.array([210, 198, 170]))
    c.line(x, y - 4 * s, x, y + 7 * s, np.array([150, 134, 110]), 3 * s)


# ----------------------------------------------------------------------------------------------- the act

class HuntAct(TuneAct):
    """The whole hunt: one walk along the forest path, six finds."""
    name = "hunt"
    LEAD = 8.0                                     # the name tags first
    names = (0.8 - LEAD, 7.0 - LEAD)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + 91), G, -1500, 12500)
        for m in scene.monsters:
            m.job = "keeper"
        self._plan()
        self.stats = {"bugs": [f["kind"] for f in FINDS]}

    # ----- the timeline -----

    def _slots(self, f):
        """Where everyone stands at find f: {kind: x}."""
        x = f["x"]
        pos = {"wheels": x + f.get("book", BOOK_DX) - PUSH, "lantern": x - 70.0}
        if f["finder"] not in ("wheels", "lantern"):
            pos[f["finder"]] = x + WORK[f["finder"]]
        if f["finder"] == "lantern":
            pos["lantern"] = x
        fx = x + WORK[f["finder"]]
        edge = max(x + 135.0, fx + (self._hw(f["finder"]) if f["finder"] not in ("wheels", "lantern") else 0.0)) + 40
        for k in ["springs", "teeth", "digger", "wheels", "tentacles", "lantern"]:
            if k in pos:
                continue
            pos[k] = edge + self._hw(k)
            edge = pos[k] + self._hw(k) + 30
        return pos

    def _hw(self, kind):
        m = self.m(kind)
        return half_width(m) if m is not None else 150.0

    def _plan(self):
        self.F = []                                    # per find: a dict of its times
        f0 = FINDS[0]
        s0 = self._slots(f0)
        self.start = dict(s0, wheels=f0["x"] + BOOK_DX - PUSH - 420.0)
        R = {k: Route(self.start[k], -self.LEAD) for k in ORDER}
        self.cart = {}                                 # cart x keys: [(t, x)] while parked / pushed
        t = 0.0
        for i, f in enumerate(FINDS):
            S = self._slots(f)
            T = {}
            if i == 0:
                T["hook"] = 0.0
                R["wheels"].wait(7.0).go(S["wheels"], v=150)
                T["book_in"] = R["wheels"].t
                T["open"] = T["book_in"] + 0.8
                T["title"] = (T["open"] + 3.0, T["open"] + 11.5)
                T["reveal"] = -2.0                                    # (the worm comes out at 0..2.5)
                T0 = T["title"][1] - 4.0
            else:
                order = sorted(ORDER, key=lambda k: -R[k].x)          # front of the line leaves first
                for j, k in enumerate(order):
                    R[k].wait(t + 0.3 * j).go(S[k], v=175 if k != "lantern" else 180)
                T0 = max(R[k].t for k in ORDER) + 0.6
                T["reveal"] = T0
            T["walk"] = t
            T["lens"] = T0 + 5.0
            T["close"] = T0 + 10.0
            T["book"] = T0 + 19.0
            T["flips"] = [T0 + 19.4, T0 + 20.4, T0 + 21.4]
            T["match"] = T0 + 22.3
            T["tick"] = T0 + 23.0
            T["card"] = (T0 + 23.5, T0 + 33.0)
            T["out"] = T0 + 33.0
            T["home"] = (T0 + 33.5, T0 + 38.0)
            T["end"] = T0 + 44.0                                    # the camera pulls back slowly first
            T["x"] = f["x"]
            T["slots"] = S
            if f["finder"] == "wheels":                               # Wheels leaves the cart to lift the rock
                rx = f["x"] + WORK["wheels"]
                park = R["wheels"].x
                R["wheels"].wait(T0 + 0.2).go(rx, v=150)
                T["lift"] = R["wheels"].t
                R["wheels"].wait(T["home"][1] + 0.3).go(park, v=150)
                T["back"] = R["wheels"].t
                T["end"] = max(T["end"], T["back"] + 0.5)
            self._extra_moves(i, f, T, R)
            t = T["end"]
            self.F.append(T)
        # the finale
        last = self.F[-1]
        self.FIN = dict(rise=last["out"] - 1.0, flip=last["end"] + 0.5, card=(last["end"] + 5.5, last["end"] + 13.5),
                        cheer=last["end"] + 6.5, back=last["end"] + 13.5)
        self.dur = last["end"] + 25.0
        self.R = R

    WALK_ICON = "bug"                              # the bubble as they set off for the next find

    def _extra_moves(self, i, f, T, R):
        """A subclass may add a short move to a Keeper's route here (after find i's own work)."""

    def find_at(self, t):
        """(index, times) of the find running at act time t (the next one while walking)."""
        for i, T in enumerate(self.F):
            if t < T["end"]:
                return i, T
        return len(self.F) - 1, self.F[-1]

    def found(self, t):
        return sum(1 for T in self.F if t >= T["tick"])

    # ----- the cart -----

    def cart_x(self, t):
        i, T = self.find_at(t)
        if FINDS[i]["finder"] == "wheels" and T["reveal"] <= t < T.get("back", -1):
            return T["x"] + FINDS[i].get("book", BOOK_DX)
        return self.R["wheels"].at(t) + PUSH

    # ----- bugs in the world (small) and the hiding places -----

    def reveal_u(self, i, t):
        T = self.F[i]
        if i == 0:
            return smoothstep(seg(t, 0.2, 2.6))
        return smoothstep(seg(t, T["reveal"] + 0.8, T["reveal"] + 4.2))

    def restore_u(self, i, t):
        a, b = self.F[i]["home"]
        return smoothstep(seg(t, a + 1.5, b))

    # ----- camera -----

    def target(self, t):
        keys = [(-self.LEAD, *self._wide(0))]
        for i, (T, f) in enumerate(zip(self.F, FINDS)):
            x, bd = f["x"], f.get("book", BOOK_DX)
            close = (x + bd / 2, G - 150.0, 2.0)
            wide = self._wide(i)
            if i == 0:
                book = (x + BOOK_DX + 40, G - 190.0, 1.75)
                keys += [(1.0, *wide), (T["book_in"] - 2.0, *wide),
                         (T["open"] + 5.0, *book), (T["title"][1] - 1.0, *book)]
            else:
                keys += [(T["walk"] + 1.5, *self._wide_prev(i)), (T["reveal"] - 1.0, *wide),
                         (T["reveal"] + 0.5, *wide)]
            mid = (x + bd / 4, None, 1.3)
            keys += [(T["lens"] + 2.0, *mid), (T["close"] + 2.5, *close), (T["out"], *close),
                     (T["out"] + 5.0, *mid), (T["out"] + 10.5, *wide)]
        Fn = self.FIN
        xl = FINDS[-1]["x"]
        keys += [(Fn["flip"] - 1.5, *self._wide(len(FINDS) - 1)), (Fn["flip"] + 5.5, xl + BOOK_DX + 40, G - 190.0, 1.75),
                 (Fn["back"], xl + BOOK_DX + 40, G - 190.0, 1.75), (self._dur_base, xl - 200.0, G - 330.0, 0.72)]
        keys.sort(key=lambda e: e[0])
        for i in range(1, len(self.F)):                  # the walks: a steady pan with the Keepers, eased ends
            T = self.F[i]
            a, b = T["walk"] + 1.5, T["reveal"] - 1.0
            if a <= t < b:
                pa, pb = self._wide(i - 1), self._wide(i)
                u = Route(0.0, a).go(1.0, v=1.0 / max(0.1, b - a - 2.0), ramp=2.0).at(t)
                z = lerp(pa[2], pb[2], u)
                return lerp(pa[0], pb[0], u), G - 0.36 * 1080.0 / z, z
        return cam_keys(keys, t)

    def _wide_prev(self, i):
        return self._wide(i - 1)

    def _wide(self, i):
        """A wide shot of find i that fits everyone (the cart and the finder included)."""
        S = self.F[i]["slots"]
        x = FINDS[i]["x"]
        lo = min(x + FINDS[i].get("book", BOOK_DX) - PUSH - 140, min(S.values()) - 160)
        hi = max(x + 300, max(S.values()) + 180)
        z = min(0.95, 1920.0 / (hi - lo + 160))
        return (lo + hi) / 2, None, z

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        i, T = self.find_at(t)
        f = FINDS[i]
        for kind in ORDER:
            m = self.m(kind)
            if m is None:
                continue
            x = self.R[kind].at(t)
            y, dy = G, 0.0
            if kind == "lantern":
                y = GLO_Y + 6 * math.sin(t * 1.3)
                lx = self._lens_x(t)
                x = lx
            if kind == "springs":
                dy -= self._hop(t)
            self.place(m, x, t, dt, y=y, dy=dy)
            self.new_look(m, work_flash(kind, t, 2.0), smile=0.6)
            m.dig, m.punch, m.punch_l = 0.0, 0.0, 0.0
            if kind == "lantern":
                m.lamp = 1.0
        self._work(i, T, f, t)
        self._particles(i, T, f, t)
        self._sounds(t)

    def _lens_x(self, t):
        """Glo (and the lens under him): beside the find, over the bug for the close-up, then back."""
        i, T = self.find_at(t)
        x = FINDS[i]["x"]
        base = self.R["lantern"].at(t)
        over = smoothstep(seg(t, T["lens"], T["lens"] + 3.0)) * (1 - smoothstep(seg(t, T["out"], T["out"] + 3.0)))
        return lerp(base, x, over)

    def _hop(self, t):
        """Springs bounces wherever he goes: real-gravity hops over each leg of his route."""
        for ts, T, a, b, r in self.R["springs"].legs:
            if ts <= t < ts + T:
                n = max(1, int(round(abs(b - a) / 170.0)))
                ph = ((t - ts) / T * n) % 1.0
                return 4 * 48 * ph * (1 - ph)
        i, Tf = self.find_at(t)
        if FINDS[i]["finder"] == "springs":                    # a little hop up to look at the leaves
            return 4 * 60 * bump(t, Tf["reveal"] + 0.6, 0.9) ** 2
        return 0.0

    def _work(self, i, T, f, t):
        m = self.m(f["finder"])
        if m is None:
            return
        u = self.reveal_u(i, t)
        r = self.restore_u(i, t)
        kind = f["finder"]
        if kind == "digger":
            digging = (-1.6 <= t < 1.6) or (T["home"][0] + 1.5 <= t < T["home"][1])
            m.dig = 0.5 + 0.5 * math.sin(t * 5.0) if digging else 0.0
        elif kind == "tentacles":
            lx, ly, rr = self.log_xy(i, t)
            grip = smoothstep(seg(t, T["reveal"], T["reveal"] + 0.8)) * (1 - smoothstep(seg(t, T["reveal"] + 4.4,
                                                                                            T["reveal"] + 5.2)))
            if grip > 0:
                hx, hy = m.x - 60, G - 300 * m.k
                self.reach["tentacles"] = [(lerp(hx, lx + rr * 0.3, grip), lerp(hy, ly - rr * 0.92, grip)),
                                           (lerp(hx, lx + rr * 0.75, grip), lerp(hy, ly - rr * 0.6, grip))]
        elif kind == "teeth":
            m.punch_l = 0.9 * (bump(t, T["reveal"], 5.0) ** 0.5 if t < T["reveal"] + 5.0 else 0.0) + \
                0.9 * (bump(t, T["home"][0] + 1.0, 4.0) ** 0.5 if t > T["home"][0] else 0.0)
        elif kind == "wheels":
            if "lift" in T:
                up = smoothstep(seg(t, T["lift"], T["lift"] + 2.0)) * (1 - smoothstep(seg(t, T["home"][0] + 1.5,
                                                                                      T["home"][1])))
                m.punch = 0.55 * up
        elif kind == "lantern":
            m.lamp = 1.0 - 0.7 * smoothstep(seg(t, T["reveal"], T["reveal"] + 2.5))
            if t > T["out"]:
                m.lamp = lerp(m.lamp, 1.0, smoothstep(seg(t, T["out"] + 6.0, T["out"] + 10.0)))
        if i > 0 and FINDS[i - 1]["finder"] == "lantern":
            pass

    def log_xy(self, i, t):
        """The log (seen end-on) of find i: rolled right off the pill bugs by Hans, and left there."""
        T = self.F[i]
        x0 = FINDS[i]["x"]
        u = smootherstep(seg(t, T["reveal"] + 0.8, T["reveal"] + 4.4))
        r = 64.0
        return x0 + 150.0 * u, G - r, r

    def rock_ang(self, i, t):
        T = self.F[i]
        if "lift" not in T:
            return 0.0
        up = smoothstep(seg(t, T["lift"] + 0.3, T["lift"] + 2.2)) * (1 - smoothstep(seg(t, T["home"][0] + 1.8,
                                                                                    T["home"][1] - 0.2)))
        return 0.42 * up

    def bark_open(self, i, t):
        T = self.F[i]
        return smoothstep(seg(t, T["reveal"] + 1.0, T["reveal"] + 4.0)) * (1 - smoothstep(seg(t, T["home"][0] + 2.0,
                                                                                         T["home"][1])))

    # ----- particles: soil from Digs' shovels, fireflies -----

    def _particles(self, i, T, f, t):
        s = self.s
        if f["place"] == "soil" and self.m("digger") is not None and self.m("digger").dig > 0.85:
            if s.particles.rng.uniform() < 0.35:
                s.particles.burst(f["x"] - 10, G - 6, 2, SOIL_C * 1.2, 260, 0.7, 5, g=1800, spread=0.7,
                                  direction=-math.pi / 2 - 0.5)
        fire = FINDS[-1]
        Tl = self.F[-1]
        if t > Tl["reveal"] + 1.0:
            rate = 0.08 if t < self.FIN["rise"] else 0.5
            if s.particles.rng.uniform() < rate:
                p = _firefly(s.particles.rng, fire["x"] + s.particles.rng.uniform(-120, 160), G - 150, G)
                if t >= self.FIN["rise"]:
                    p.x += s.particles.rng.uniform(-900, 500)
                    p.vy -= 40
                s.particles.items.append(p)

    # ----- talking and sounds -----

    def aside_moods(self, t):
        i, T = self.find_at(t)
        if T["card"][0] - 0.5 < t < T["card"][1] or (self.FIN["card"][0] - 0.5 < t < self.FIN["card"][1]):
            return []                                     # quiet while the card is up: time to read
        return ["mm", "ooh", "hehe", "hm"]

    def _sounds(self, t):
        for i, (T, f) in enumerate(zip(self.F, FINDS)):
            x, fk = f["x"], f["finder"]
            others = [k for k in ORDER if k not in (fk, "lantern")]
            if i == 0:
                for q in range(4):
                    if self.crossed(-1.4 + 0.8 * q):
                        self.fx(-1.4 + 0.8 * q, "rustle", 0.35, 0.16, x, G)
                if self.crossed(2.7):
                    self.chat(2.7, "digger", "ooh")
                if self.crossed(3.5):
                    self.chorus(3.5, ["springs", "teeth", "tentacles"], "ooh", gap=0.3)
                if self.crossed(5.2):
                    self.chat(5.2, "lantern", "idea", icon="book")
                if self.crossed(7.0):
                    self.chat(7.0, "wheels", "hey", icon="book")
                if self.crossed(T["open"]):
                    self.fx(T["open"], "rustle", 0.6, 0.22, x + BOOK_DX, BOOK_Y)
                if self.crossed(T["title"][0] + 0.5):
                    self.chorus(T["title"][0] + 0.5, ["springs", "digger", "teeth"], "yay", gap=0.3)
            else:
                if self.crossed(T["walk"] + 0.5):
                    self.chat(T["walk"] + 0.5, fk if fk != "lantern" else "wheels", "hey", icon=self.WALK_ICON)
                if self.crossed(T["reveal"] + 0.6):
                    self.chat(T["reveal"] + 0.6, fk, "huff" if fk in ("tentacles", "wheels", "teeth") else "hm")
                if self.crossed(T["reveal"] + 1.0):
                    snd = {"log": ("creak", 3.0), "bark": ("creak", 2.0), "rock": ("sand_scrape", 1.6),
                           "plant": ("rustle", 1.0), "ferns": ("rustle", 1.2)}[f["place"]]
                    self.fx(T["reveal"] + 1.0, snd[0], snd[1], 0.22, x, G)
                if self.crossed(T["reveal"] + 3.6):
                    self.chorus(T["reveal"] + 3.6, others[:3], "ooh", gap=0.3)
            if self.crossed(T["lens"] + 2.6):
                self.hit(T["lens"] + 2.6, "warm_bell", 67, 0.12, x, LENS_Y)
            if self.crossed(T["close"] + 2.0):
                self.chat(T["close"] + 2.0, fk, "ooh", icon="sparkle")
            if self.crossed(T["close"] + 6.0):
                self.chat(T["close"] + 6.0, "lantern" if fk != "lantern" else "springs", "q", icon="?")
            for q, ft in enumerate(T["flips"]):
                if self.crossed(ft):
                    self.fx(ft, "rustle", 0.35, 0.16, x + BOOK_DX, BOOK_Y)
            if self.crossed(T["tick"]):
                self.hit(T["tick"], "warm_bell", 72, 0.16, x + BOOK_DX, BOOK_Y)
                self.hit(T["tick"] + 0.22, "warm_bell", 79, 0.14, x + BOOK_DX, BOOK_Y)
            if self.crossed(T["tick"] + 0.2):
                self.chorus(T["tick"] + 0.2, [fk, "lantern" if fk != "lantern" else "wheels"], "yay", gap=0.3)
            if self.crossed(T["home"][0] + 0.8):
                self.chat(T["home"][0] + 0.8, fk, "aww", icon="heart")
            if f["place"] == "log" and self.crossed(T["reveal"] + 4.4):
                self.hit(T["reveal"] + 4.4, "wood_thud", 45, 0.14, x + 150, G)
            if f["place"] == "rock" and self.crossed(T["home"][1] - 0.2):
                self.hit(T["home"][1] - 0.2, "thud", 43, 0.12, x, G)
        Fn = self.FIN
        if self.crossed(Fn["flip"]):
            self.fx(Fn["flip"], "rustle", 0.6, 0.2, FINDS[-1]["x"] + BOOK_DX, BOOK_Y)
        if self.crossed(Fn["cheer"]):
            self.chorus(Fn["cheer"], ORDER, "yay", gap=0.3)
            for q in range(4):
                self.hit(Fn["cheer"] + 0.3 * q, "warm_bell", [67, 72, 76, 79][q], 0.12, FINDS[-1]["x"], G - 200)
        if self.crossed(Fn["back"] + 3.0):
            self.chorus(Fn["back"] + 3.0, ["springs", "teeth", "digger"], "aww", gap=0.4)

    # ----- what moves (for the warp check) -----

    def props(self, t):
        out = {"cart": (self.cart_x(t), G), "lens": (self._lens_x(t), LENS_Y)}
        i, T = self.find_at(t)
        if FINDS[i]["place"] == "log":
            lx, ly, _ = self.log_xy(i, t)
            out["log"] = (lx, ly)
        return out

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.night.draw(s, c, t)
        self.night.ground_slab(s, c)
        self._forest(c)
        i, T = self.find_at(t)
        for j, f in enumerate(FINDS):                 # every hiding place stays where it is
            if s.visible(f["x"] - 500, f["x"] + 500):
                self._place(c, j, t)
        self.glo_light(c, k=0.8 * (self.m("lantern").lamp if self.m("lantern") is not None else 1.0))
        self.draw_monsters(c, t)
        cx = self.cart_x(t)
        if s.visible(cx - 300, cx + 300):
            draw_cart(c, cx, -cx / 22.0)
            op = self.F[0]["open"]
            if t < op:
                closed_book(c, cx)
            else:
                draw_book(c, cx, lambda c_, side, xa, xb, y0, y1: self._page(c_, t, side, xa, xb, y0, y1),
                          self._flip(t), left=t >= op + 0.4, cover_flip=t < op + 0.8)
        lx = self._lens_x(t)
        gl = self.m("lantern")
        if gl is not None:
            self._lens(c, i, T, t, lx)
            mx = gl.x + 70 * math.cos(t * 2.1) + 20 * math.sin(t * 5.3)       # the moth by the lantern
            my = gl.y - 120 + 40 * math.sin(t * 2.9)
            if gl.lamp is not None and gl.lamp > 0.6 and s.visible(mx - 20, mx + 20):
                moth(c, mx, my, t)
        self._flare(c, i, T, t)

    def _forest(self, c):
        s = self.s
        vx0, vx1 = s.view()[:2]
        for j, x in enumerate(np.arange(-600, 12000, 520)):
            if vx0 - 400 < x < vx1 + 400:
                tree(c, x + 90 * math.sin(j * 1.7), G, 700 + 140 * ((j * 7) % 3), 300 + j)
        for j, x in enumerate(np.arange(-300, 12000, 380)):                    # low bushes along the path
            if vx0 - 200 < x < vx1 + 200 and all(abs(x - f["x"]) > 260 for f in FINDS):
                r = 70 + 20 * ((j * 3) % 3)
                c.circle(x, G - r * 0.5, r, TREE_LEAF[1] * 0.6)
                c.circle(x + r * 0.7, G - r * 0.4, r * 0.7, TREE_LEAF[1] * 0.68)

    # ----- the hiding places -----

    def _place(self, c, j, t):
        f = FINDS[j]
        x, kind = f["x"], f["kind"]
        T = self.F[j]
        u = self.reveal_u(j, t) if t > T["walk"] - 1 else 0.0
        if t < T["walk"] - 1 and j > 0:
            u = 0.0
        if f["place"] == "soil":
            out = u * (1 - self.restore_u(j, t))
            c.polygon(ellipse(x - 40, G, 70, 22, 20, math.pi, 2 * math.pi), SOIL_C * 1.1)
            c.polygon(ellipse(x + 50, G, 60, 18, 20, math.pi, 2 * math.pi), SOIL_C * 1.05)
            c.polygon(ellipse(x, G - 2, 20, 7, 16), SOIL_C * 0.5)
            if out > 0.02:
                L = 60.0
                wx = x + L / 2 - (1 - out) * L
                draw_bug(c, "earthworm", wx, G - 6, L, -0.05, t, t * 0.8)
            c.polygon(ellipse(x - 14, G + 2, 26, 8, 16, 0, math.pi), SOIL_C * 1.1)      # the hole's front lip
        elif f["place"] == "log":
            lx, ly, r = self.log_xy(j, t)
            home = smoothstep(seg(t, T["home"][0], T["home"][1]))
            for q, (bx, ph) in enumerate(((x - 22, 0.0), (x + 4, 1.3), (x + 30, 2.1))):
                if u > 0.5:
                    hx = lerp(bx, x + 120 + 12 * q, home)
                    draw_bug(c, "pillbug", hx, G - 4, 13, 0.0, t, t * 1.5 + ph)
            c.polygon(ellipse(lx, ly, r, r, 40), BARK_C)
            c.polygon(ellipse(lx, ly, r * 0.84, r * 0.84, 40), np.array([196, 160, 112]))
            for q in (0.3, 0.52, 0.72):
                c.polyline(ellipse(lx + 3, ly + 2, r * q, r * q * 0.95, 30), np.array([160, 122, 80]), 2)
            rot = (lx - x) / r                                  # rolling right turns it clockwise (y down)
            for q in range(3):
                a = rot + q * 2.1
                c.line(lx + math.cos(a) * r * 0.2, ly + math.sin(a) * r * 0.2, lx + math.cos(a) * r * 0.8,
                       ly + math.sin(a) * r * 0.8, np.array([140, 100, 66]), 3)
        elif f["place"] == "bark":
            sx, top = x, G - 170
            rect(c, sx - 105, top, sx + 105, G, BARK_C)
            c.polygon(ellipse(sx, top, 105, 26, 36), np.array([186, 150, 104]))
            for q in (0.35, 0.65, 0.9):
                c.polyline(ellipse(sx, top, 105 * q, 26 * q, 30), np.array([150, 112, 76]), 2)
            for q in range(6):
                bx = sx - 90 + q * 36
                c.line(bx, top + 30, bx + 6, G - 10, BARK_C * 0.7, 4)
            c.polygon([(sx - 46, G - 150), (sx + 50, G - 150), (sx + 50, G - 12), (sx - 46, G - 12)],
                      np.array([176, 138, 96]))                                    # the wood under the bark
            op = self.bark_open(j, t) if t > T["walk"] else 0.0
            if u > 0.3 and t < T["home"][1]:
                mu = smoothstep(seg(t, T["home"][0], T["home"][1] - 0.5))
                draw_bug(c, "millipede", sx - 10 + 40 * mu, G - 84 + 50 * mu, 70, 0.25, t, t * 0.6)
            hgt = 138 * math.cos(op * 1.35)
            col = lerp(BARK_C * 1.15, np.array([150, 108, 70]), smoothstep(op * 1.5))
            c.polygon([(sx - 48, G - 12 - hgt), (sx + 52, G - 12 - hgt), (sx + 52, G - 12), (sx - 48, G - 12)], col)
            if op < 0.4:
                for q in range(3):
                    c.line(sx - 36 + q * 34, G - 12 - hgt + 8, sx - 34 + q * 34, G - 18, BARK_C * 0.75, 3)
        elif f["place"] == "rock":
            ang = self.rock_ang(j, t)
            if ang > 0.05 or (T["reveal"] <= t < T["home"][1]):
                c.polygon(ellipse(x, G - 2, 100, 10, 24), SOIL_C * 0.55)             # the damp patch under it
                if t < T["home"][1] - 0.6:
                    run = smoothstep(seg(t, T["home"][0], T["home"][0] + 1.5))
                    draw_bug(c, "groundbeetle", x - 20 + 30 * math.sin(t * 0.7) * (1 - run) + 20 * run, G - 6, 20,
                             0.0, t, t * 2.5)
            piv = (x + 110.0, G)
            rc = Xform(c, 0, 0, ang, 1.0, *piv)                                  # the left edge lifts
            rc.polygon(ellipse(x, G - 28, 110, 30, 32), ROCK_C)
            rc.polygon(ellipse(x - 20, G - 40, 70, 14, 24), ROCK_C * 1.15)
            rc.polyline(ellipse(x, G - 28, 110, 30, 32), ROCK_C * 0.6, 3, closed=True)
        elif f["place"] == "plant":
            px = x + 15
            sway = 0.04 * math.sin(t * 1.1) + 0.12 * bump(t, T["reveal"] + 1.0, 1.5)
            c.line(px, G, px + 200 * sway, G - 250, np.array([70, 120, 60]), 6)
            for q in range(6):
                h = 50 + q * 34
                bx = px + 200 * sway * h / 250
                sgn = 1 if q % 2 else -1
                c.polygon(ellipse(bx + sgn * 34, G - h - 6, 40, 13, 20), np.array([74, 140, 66]) * (0.85 + 0.03 * q))
                c.line(bx, G - h, bx + sgn * 70, G - h - 10, np.array([110, 170, 96]), 2)
            if u > 0.2:
                draw_bug(c, "ladybug", px + 200 * sway * 160 / 250 + 30, G - 172, 9, 0.0, t, t)
            for q in range(3):
                aphid(c, px + 200 * sway * 0.8 - 4 + 8 * q, G - 200 - 6 * q, 5, t)
        elif f["place"] == "ferns":
            for q in range(7):
                a = -math.pi / 2 + (q - 3) * 0.32
                L = 150 + 25 * (q % 3)
                pts = [(x + math.cos(a) * L * w + 30 * w * w * (q - 3) / 3, G + math.sin(a) * L * w + 40 * w * w)
                       for w in np.linspace(0, 1, 10)]
                c.polyline(pts, FERN_C * 0.75, 4)
                for (ax, ay), (bx, by) in zip(pts[1:-1], pts[2:]):
                    for sgn in (-1, 1):
                        c.line(ax, ay, ax + sgn * 18 - (bx - ax) * 0.3, ay + 8, FERN_C * (0.9 + 0.05 * sgn), 5)
            if u > 0.3:
                lit = 0.5 + 0.5 * math.sin(t * 2.4)
                draw_bug(c, "firefly", x + 40, G - 96, 9, 0.3, t, 0.0, glow=self.s.glow, light=lit ** 3)

    # ----- the lens and what it shows -----

    def _lens(self, c, i, T, t, lx):
        s = self.s
        if not s.visible(lx - 200, lx + 200):
            return
        f = FINDS[i]
        view = smoothstep(seg(t, T["lens"] + 2.0, T["lens"] + 4.0)) * (1 - smoothstep(seg(t, T["out"], T["out"] + 2.0)))
        if view > 0.0:
            R = LENS_R
            pts = ellipse(lx, LENS_Y, R, R, 64)
            fade_clip(c, s.glow, pts, lambda: self._close_view(c, i, T, t, lx), 1.0, view)
        draw_lens(c, lx, LENS_Y)

    def _close_view(self, c, i, T, t, lx):
        f = FINDS[i]
        kind, R, y = f["kind"], LENS_R, LENS_Y
        lens_ground(c, lx, y, R, f["place"], 300 + i)
        tt = t - T["lens"]
        if kind == "earthworm":
            draw_bug(c, kind, lx - 18 + 1.2 * tt, y + 10, 205, -0.18, t, tt * 0.7)
        elif kind == "pillbug":
            roll = 1.0 - smoothstep(seg(tt, 4.0, 7.0))
            draw_bug(c, kind, lx + 30, y + 40, 90, 2.6, t, 0.0)                   # a second one, further off
            hd = -0.3 + 0.2 * math.sin(tt * 0.3)
            gait = max(0.0, tt - 7.0) * 1.4
            draw_bug(c, kind, lx - 20 + max(0.0, tt - 7.0) * 9, y - 20, 120, hd, t, gait, roll=roll)
        elif kind == "millipede":
            draw_bug(c, kind, lx - 14 + 1.1 * tt, y + 14 - 0.4 * tt, 205, -0.3, t, tt * 0.8)
        elif kind == "groundbeetle":
            k, run = int(tt // 6.0), tt % 6.0                    # dashes across and back, stops, feels about
            go = smoothstep(seg(run, 0.0, 0.4)) * (1 - smoothstep(seg(run, 2.0, 2.4)))
            d = 1.0 if k % 2 == 0 else -1.0
            x0 = lx - d * 30 + d * 30 * smoothstep(seg(run, 0.0, 2.4))
            hd = (0.0 if d > 0 else math.pi) + 0.15 * math.sin(tt * 0.5)
            draw_bug(c, kind, x0, y + 10, 150, hd, t, tt * 2.2 * go + 0.25)
        elif kind == "ladybug":
            for q, (ax, ay) in enumerate(((45, -40), (70, -10), (60, 30))):
                aphid(c, lx + ax, y + ay, 30, t)
            draw_bug(c, kind, lx - 40 + 2.5 * tt, y + 5 - 0.6 * tt, 110, -0.2, t, tt * 1.1)
        elif kind == "firefly":
            lit = 0.5 + 0.5 * math.sin(tt * 2.2 - 1.0)
            draw_bug(c, kind, lx - 10, y + 10, 150, -0.5, t, 0.0, glow=self.s.glow, light=lit ** 2, glow_r=0.16)

    # ----- the book -----

    def _flips(self):
        """[(t, from page, to page)]: page 0 is the checklist, 1..6 the six bugs, 7.. other bugs in the guide."""
        out = [(self.F[0]["open"], -1, 0)]
        cur = 0
        for i, T in enumerate(self.F):
            tgt = i + 1
            mids = [7 + (i % 3), 8 + (i % 2)]
            seq = [mids[0], mids[1], tgt] if i > 0 else [mids[0], mids[1], tgt]
            for ft, to in zip(T["flips"], seq):
                out.append((ft, cur, to))
                cur = to
        out.append((self.FIN["flip"], cur, 0))
        return out

    def _book_page(self, t):
        """(page shown, flip u or None)."""
        page = -1
        for ft, a, b in self._flips_cache():
            if t < ft:
                return page, None
            if t < ft + 0.8:
                return (a, b), (t - ft) / 0.8
            page = b
        return page, None

    def _flips_cache(self):
        if not hasattr(self, "_fl"):
            self._fl = self._flips()
        return self._fl

    def _flip(self, t):
        return self._book_page(t)[1]

    def _page(self, c, t, side, xa, xb, y0, y1):
        p, u = self._book_page(t)
        if isinstance(p, tuple):                       # mid-flip: the left page is the old one until the half-way
            a, b = p
            p = b if side > 0 else (a if u < 0.5 else b)
        if p == -1:
            return self._cover(c, side, xa, xb, y0, y1)
        if p == 0:
            return self._checklist(c, t, side, xa, xb, y0, y1)
        if p >= 7:
            other = ["millipede", "ladybug", "earthworm"][p % 3]
            if side < 0:
                c.polygon(ellipse((xa + xb) / 2, (y0 + y1) / 2, 46, 30, 20), PAPER_DARK)
            else:
                page_lines(c, xa, xb, y0 + 30, 7)
            return
        kind = FINDS[p - 1]["kind"]
        i = p - 1
        if side < 0:
            L = 120 if kind in ("earthworm", "millipede") else 84
            draw_bug(c, kind, (xa + xb) / 2, (y0 + y1) / 2 + 6, L, -0.5 if L > 100 else -1.57 + 0.0, 0.0, 0.25)
        else:
            name = BUGS[kind]["name"].split(" (")[0]
            c.text(name.upper(), (xa + xb) / 2, y0 + 26, 15 if len(name) > 10 else 18, INK)
            page_lines(c, xa, xb, y0 + 52, 5)
            bx, by = xb - 32, y1 - 30                                                 # the tick box
            c.polyline([(bx - 14, by - 14), (bx + 14, by - 14), (bx + 14, by + 14), (bx - 14, by + 14)], INK * 1.4, 2,
                       closed=True)
            tk = smoothstep(seg(t, self.F[i]["tick"], self.F[i]["tick"] + 0.5))
            if tk > 0:
                p1, p2, p3 = (bx - 10, by), (bx - 3, by + 9), (bx + 14, by - 14)
                if tk < 0.4:
                    c.line(*p1, lerp(p1[0], p2[0], tk / 0.4), lerp(p1[1], p2[1], tk / 0.4), TICK, 5)
                else:
                    v = (tk - 0.4) / 0.6
                    c.line(*p1, *p2, TICK, 5)
                    c.line(*p2, lerp(p2[0], p3[0], v), lerp(p2[1], p3[1], v), TICK, 5)

    def _cover(self, c, side, xa, xb, y0, y1):
        c.polygon([(xa, y0), (xb, y0), (xb, y1), (xa, y1)], COVER)
        if side > 0:
            c.text("FIELD GUIDE", (xa + xb) / 2, y0 + 40, 15, PAPER)
            c.polygon(ellipse((xa + xb) / 2, (y0 + y1) / 2 + 20, 18, 30, 20), np.array([200, 190, 100]))

    def _checklist(self, c, t, side, xa, xb, y0, y1):
        if side < 0:
            c.text("BUG HUNT", (xa + xb) / 2, y0 + 34, 22, INK)
            c.text("find all six!", (xa + xb) / 2, y0 + 64, 13, INK * 1.3)
            draw_bug(c, "ladybug", (xa + xb) / 2, y1 - 52, 46, -1.57, 0.0, 0.25)
            return
        n = self.found(t)
        for q in range(6):
            cx = xa + 30 + (q % 3) * 45
            cy = y0 + 46 + (q // 3) * 78
            c.polyline([(cx - 20, cy - 30), (cx + 20, cy - 30), (cx + 20, cy + 30), (cx - 20, cy + 30)], INK * 1.4, 2,
                       closed=True)
            if q < n:
                kind = FINDS[q]["kind"]
                L = 52 if kind in ("earthworm", "millipede") else 30
                draw_bug(c, kind, cx, cy, L, -1.57, 0.0, 0.25)
            else:
                c.text("?", cx, cy, 24, INK * 1.6)

    # ----- Glo's light turns the pages and ticks the box -----

    def _flare(self, c, i, T, t):
        cx = self.cart_x(t)
        g = 0.0
        for ft, a, b in self._flips_cache():
            g = max(g, bump(t, ft - 0.3, 1.4))
        g = max(g, bump(t, T["tick"] - 0.3, 1.2), bump(t, self.F[0]["open"] - 0.3, 1.3))
        if g > 0.01:
            self.flare(c, cx + 60, BOOK_Y - 40, g)

    # ----- on screen: the name card and the count -----

    def screen(self, cv, ts):
        """On-screen text, drawn straight onto the frame in fixed screen units (owner + Toby, FK0007 review: the
        count and the name cards jittered the whole time when they were drawn in the world and mapped back through
        the always-drifting camera). Called by the scene after the act; ts = scene time - t0."""
        t = ts / self.STRETCH - self.LEAD
        i, T = self.find_at(t)
        F0 = self.F[0]
        if F0["title"][0] <= t < F0["title"][1] + 1.0:
            a = smoothstep(seg(t, F0["title"][0], F0["title"][0] + 0.7)) * (1 - smoothstep(seg(t, F0["title"][1],
                                                                                         F0["title"][1] + 0.7)))
            self._card(cv, a, "BUG HUNT", ["Can the Keepers find six", "different bugs in the forest?"], None)
        a0, a1 = T["card"]
        if a0 <= t < a1 + 0.8:
            a = smoothstep(seg(t, a0, a0 + 0.7)) * (1 - smoothstep(seg(t, a1, a1 + 0.7)))
            kind = FINDS[i]["kind"]
            self._card(cv, a, BUGS[kind]["name"], BUGS[kind]["line"], kind)
        Fc = self.FIN["card"]
        if Fc[0] <= t < Fc[1] + 0.8:
            a = smoothstep(seg(t, Fc[0], Fc[0] + 0.7)) * (1 - smoothstep(seg(t, Fc[1], Fc[1] + 0.7)))
            self._card(cv, a, "All six found!", ["Every one of them helps", "keep the forest healthy."], None)
        if F0["title"][1] - 0.5 < t:                                   # the count, top left, fixed size
            n = self.found(t)
            hi = max((bump(t, Tq["tick"], 0.8) for Tq in self.F), default=0.0)
            self._unglow(cv, 40, 36, 400, 104)
            cv.polygon([(40, 36), (400, 36), (400, 104), (40, 104)], WOOD * 0.8)
            cv.polyline([(40, 36), (400, 36), (400, 104), (40, 104)], WOOD * 0.5, 4, closed=True)
            cv.text(f"BUGS FOUND  {n} / 6", 220, 70, 30, PAPER * (1 - 0.25 * hi) + np.array([255, 220, 120]) * 0.25 * hi)

    def _unglow(self, cv, x0, y0, x1, y1):
        """No bloom over on-screen panels (lanterns behind them would shine through)."""
        g = self.s.glow.layer
        k = cv.s
        g[max(0, int(y0 * k)):int(y1 * k) + 1, max(0, int(x0 * k)):int(x1 * k) + 1] = 0

    def _card(self, cv, a, title, lines, kind):
        """The name card at the bottom of the screen: paper on wood, big friendly letters, the bug's picture. It
        fades in and out where it stands; nothing on it moves."""
        if a <= 0.01:
            return
        W, H = 1240, 210
        x0, y0 = 960 - W // 2, 1080 - 30 - H
        x1, y1 = x0 + W, y0 + H
        bg = cv.target.copy() if a < 0.999 else None
        self._unglow(cv, x0, y0, x1, y1)
        cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], WOOD * 0.75)
        cv.polygon([(x0 + 8, y0 + 8), (x1 - 8, y0 + 8), (x1 - 8, y1 - 8), (x0 + 8, y1 - 8)], CARD)
        tx0 = x0 + (230 if kind else 60)
        if kind:
            L = 190 if kind in ("earthworm", "millipede") else 130
            draw_bug(cv, kind, x0 + 120, y0 + H // 2, L, -0.6 if L > 150 else -1.2, 0.0, 0.25)
        cx = (tx0 + x1 - 40) // 2
        cv.text(title, cx, y0 + H // 2 - 52, 62, INK)
        for q, ln in enumerate(lines):
            cv.text(ln, cx, y0 + H // 2 + 14 + q * 42, 34, INK * 1.25)
        if bg is not None:
            cv.target[:] = (bg * (1 - a) + cv.target * a).astype(np.uint8)
