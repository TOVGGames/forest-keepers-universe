"""Forest Keepers episode 3: Halloween (docs/engines/foundry_keepers_halloween.md).

  RETURN    - the finished treehouse from episode 2; the Keepers climb down and walk through the forest to
              the factory's cliff door, which rolls up; in they go.
  WORKSHOP  - the night shift: forge (Digs stokes, Hans pours), press (Springs stamps), lathe (Wheels), cloth
              cutting (Twigs), glass bulbs (Glo), sanding + paint (Hans). Only anonymous parts until the
              middle, then the assembly table: carved faces + a candle = the first jack-o'-lantern, the
              board lights up HAPPY HALLOWEEN, then bats, ghosts and the light string.
  HAUL      - out of the cliff door with everything, back through the forest.
  DECORATE  - pumpkins on the ground and the platform, bats on the high branches, ghosts, the light
              string under the platform; Glo lights every jack-o'-lantern; the forest animals come to look.
Each Keeper's own body is the tool. Hans always works with his own tentacles (Monster.work_tentacle).
"""
import math

import numpy as np

from ..products import decor as D
from ..products.monster import Xform, ellipse
from ..style import CABLE, FAR, FLOOR, IRON, MID, STEEL, molten
from ..tree_monsters import (BARK, EARTH, EARTH_DARK, GRASS, HAZARD, INTERIOR, LAMP, LEAF, LEAF_FAR, SAWDUST,
                             SIGN_GREEN, SIGN_WARM, TRUNK, machine_block, saw_blade)
from .common import (GRAVITY, Jump, PLANK, bunny, hedgehog, lerp, lighten, rect, seg, settle, smoothstep, smootherstep, tree,
                     wood_sign)
from .forest import FIREFLY, ROOF, ForestAct, _firefly

TUNE_MAJOR = [72, 74, 76, 79, 81, 84]                 # the episode 2 tune (C major pentatonic)
TUNE_HALLOWEEN = [69, 71, 72, 74, 76, 77, 80, 81]     # A harmonic minor: a little spooky, still sweet (MIDI 69-81)
ROCK = np.array([46, 40, 38], np.float64)
ROCK_DARK = np.array([34, 30, 30], np.float64)


def path(keys, t):
    """Keyframed move: keys [(t, x, y), ...]; eased between keys, holds outside. -> (x, y, moving)."""
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2], False
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t < t1:
            u = smoothstep((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return lerp(x0, x1, u), lerp(y0, y1, u), (x0 != x1 or y0 != y1)
    return keys[-1][1], keys[-1][2], False


def hops(x0, x1, t0, t1, t, apex=70.0, step=190.0):
    """Springs walks by bouncing: n real-gravity hops from x0 to x1 between t0 and t1 -> (x, lift, squash)."""
    n = max(1, int(round(abs(x1 - x0) / step)))
    if t <= t0 or t >= t1:
        return (x0 if t <= t0 else x1), 0.0, 0.0
    u = (t - t0) / (t1 - t0) * n
    k, ph = int(u), u - int(u)
    x = lerp(x0, x1, (k + ph) / n)
    lift = 4 * apex * ph * (1 - ph)                   # a parabola in time = constant gravity
    squash = 0.7 * max(0.0, 1 - min(ph, 1 - ph) / 0.1)
    return x, lift, squash


# ====================================================================== the treehouse (episode 2, finished)

class House:
    """The finished treehouse from episode 2, plus the spots where the Halloween decorations go.
    Same geometry as TreehouseAct so the episodes match, except the door (now centred, see door_x)."""

    def __init__(self, G):
        self.G = G
        self.tx = 1400.0
        self.py = G - 560
        self.p0, self.p1 = 1000.0, 1800.0
        self.h0, self.h1 = 1080.0, 1640.0
        self.wall_top = self.py - 270
        self.ladder_x = 1880.0
        self.n_rungs = 9
        self.windows = [(1190, self.py - 150), (1530, self.py - 150), (1360, self.wall_top - 70)]
        # the door stands centred between the two round windows, under the gable window (owner, FK0001 review
        # 2026-10-27: it used to sit at h1 - 70, half over the right-hand window; episodes 2-4 were rendered that way)
        self.door_x = (self.windows[0][0] + self.windows[1][0]) / 2
        tx = self.tx
        self.branches = [((tx - 60, G - 760), (tx - 640, G - 980)), ((tx + 60, G - 800), (tx + 620, G - 1010)),
                         ((tx, G - 980), (tx - 300, G - 1250)), ((tx, G - 980), (tx + 320, G - 1260))]
        # Halloween spots (evenly spaced, symmetric about the trunk where the tree allows)
        self.ground_pumpkins = [self.tx - 320 + 160 * i for i in range(5)]     # a row in front of the trunk
        self.deck_pumpkins = [1120.0, 1280.0, 1440.0]
        self.bat_spots = [self.branch_at(2, u) for u in (0.4, 0.68, 0.95)] + [self.branch_at(3, u) for u in (0.4, 0.68, 0.95)]
        self.ghost_spots = [self.branch_at(0, 0.62), self.branch_at(1, 0.62), self.branch_at(0, 0.97), self.branch_at(1, 0.97)]
        self.hooks = [(self.p0 + 20 + i * (self.p1 - self.p0 - 40) / 5, self.py + 34) for i in range(6)]

    def branch_at(self, i, u):
        (x0, y0), (x1, y1) = self.branches[i]
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + 14       # underside of the branch

    def rung_y(self, k):
        return self.G - (k + 1) * (self.G - self.py) / (self.n_rungs + 1)

    def lantern_pos(self, i):
        x = 820 + i * 170
        y = self.py - 330 - 60 * math.sin(i * 0.9 + 0.4) - 0.00012 * (x - self.tx) ** 2
        return x, y

    def draw_tree(self, c, s):
        G, tx = self.G, self.tx
        c.polygon([(tx - 130, G), (tx + 130, G), (tx + 90, G - 1050), (tx - 90, G - 1050)], TRUNK)
        for k in (-1, 1):
            c.polygon([(tx + k * 120, G), (tx + k * 220, G + 4), (tx + k * 100, G - 80)], TRUNK * 0.9)
        c.line(tx - 30, G, tx - 20, G - 1000, BARK, 6)
        c.line(tx + 40, G - 100, tx + 30, G - 900, BARK, 4)
        for (bx, by), (ex, ey) in self.branches:
            c.line(bx, by, ex, ey, TRUNK, 34)
        rs = np.random.default_rng(42)
        for k in range(16):
            cx = tx + rs.uniform(-750, 750)
            cy = G - 1150 - rs.uniform(-120, 260) - 200 * math.cos((cx - tx) / 1500 * math.pi)
            c.circle(cx, cy, rs.uniform(170, 260), LEAF[k % 3] * 0.85)
        # the branch tips poke out of the leaves so the hanging things have something to hang from
        for (bx, by), (ex, ey) in self.branches:
            c.line(lerp(bx, ex, 0.55), lerp(by, ey, 0.55), ex, ey, TRUNK * 0.95, 26)
            c.line(lerp(bx, ex, 0.55), lerp(by, ey, 0.55), ex, ey, BARK, 3)

    def draw_house(self, c, s, t, windows=0.0, lanterns=1.0, door_glow=None):
        G, py = self.G, self.py
        tx = self.tx
        for xk in (self.p0 + 60, self.p1 - 60):
            c.line(tx + (60 if xk > tx else -60), py + 120, xk, py + 14, TRUNK * 0.9, 16)
        c.line(self.p0 + 20, py + 18, self.p1 - 20, py + 18, TRUNK * 0.85, 12)
        pw = (self.p1 - self.p0) / 10
        for k in range(10):
            x0 = self.p0 + k * pw
            rect(c, x0 + 2, py, x0 + pw - 2, py + 16, PLANK)
        lx = self.ladder_x
        c.line(lx - 34, G, lx - 34, py, PLANK * 0.8, 8)
        c.line(lx + 34, G, lx + 34, py, PLANK * 0.8, 8)
        for k in range(self.n_rungs):
            c.line(lx - 34, self.rung_y(k), lx + 34, self.rung_y(k), PLANK, 7)
        bw = (self.h1 - self.h0) / 10
        for k in range(10):
            x0 = self.h0 + k * bw
            rect(c, x0 + 1, self.wall_top, x0 + bw - 1, py, PLANK * (0.78 + 0.07 * (k % 2)))
            c.line(x0 + 1, self.wall_top, x0 + 1, py, PLANK * 0.6, 2)
        for k, (wx, wy) in enumerate(self.windows[:2]):
            lit = windows
            c.circle(wx, wy, 46, np.array([20, 18, 20]) + LAMP * 0.85 * lit)
            c.circle(wx, wy, 46, PLANK * 0.55, False, 6)
            c.line(wx - 46, wy, wx + 46, wy, PLANK * 0.55, 4)
            c.line(wx, wy - 46, wx, wy + 46, PLANK * 0.55, 4)
            if lit > 0:
                s.glow_draw(lambda g, wx=wx, wy=wy, lit=lit: g.circle(wx, wy, 70, LAMP * 0.55 * lit))
        dg = windows if door_glow is None else door_glow
        rect(c, self.door_x - 40, py - 170, self.door_x + 40, py, np.array([50, 36, 28]) + LAMP * 0.4 * dg)
        ridge = ((self.h0 + self.h1) / 2, self.wall_top - 190)
        c.polygon([(self.h0 + 10, self.wall_top), (self.h1 - 10, self.wall_top), (ridge[0], self.wall_top - 170)],
                  PLANK * 0.7)
        wx, wy = self.windows[2]
        c.circle(wx, wy, 30, np.array([20, 18, 20]) + LAMP * 0.85 * windows)
        c.circle(wx, wy, 30, PLANK * 0.5, False, 5)
        for sgn in (-1, 1):
            eave = (self.h0 - 70 if sgn < 0 else self.h1 + 70, self.wall_top + 10)
            pts = [ridge, eave, (eave[0], eave[1] + 24), (ridge[0], ridge[1] + 24)]
            c.polygon(pts, ROOF)
            c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], ROOF * 1.4, 3)
        for k in range(8):
            lx_, ly_ = self.lantern_pos(k)
            if k > 0:
                px, py_ = self.lantern_pos(k - 1)
                c.line(px, py_ - 40, lx_, ly_ - 40, np.array([60, 52, 40]), 2)
            sway = 0.08 * math.sin(t * 1.4 + k)
            lc = Xform(c, ang=sway, px=lx_, py=ly_ - 40)
            lc.line(lx_, ly_ - 40, lx_, ly_ - 20, np.array([60, 52, 40]), 2)
            lc.polygon([(lx_ - 14, ly_ - 20), (lx_ + 14, ly_ - 20), (lx_ + 17, ly_ + 14), (lx_ - 17, ly_ + 14)],
                       np.array([50, 50, 46]) + LAMP * 0.85 * lanterns)
            if lanterns > 0:
                s.glow_draw(lambda g, lx_=lx_, ly_=ly_: g.circle(lx_, ly_ - 2, 36, LAMP * 0.6 * lanterns))


class Hill:
    """The hill the factory is built into, seen from the front, with a roll-up steel door in its rock
    face. Drawn in two passes around the monsters: back() = hill + dark tunnel, front() = the rock
    around the opening, which hides anyone who has walked further in."""

    def __init__(self, X, G, door_w=300, door_h=520, walk_in=False):
        # walk_in (Forest Keepers from episode 9, families/keepers/doorway.py): the rock face stands behind the
        # path, front() draws only the door frame, and whoever goes in walks into the opening's depth
        self.X, self.G, self.walk_in = X, G, walk_in
        self.door_w, self.door_h = door_w, door_h
        self.d0, self.d1 = X + 120, X + 120 + door_w
        rs = np.random.default_rng(77)
        # skyline: a steep rocky face rising from the forest floor, then a rounded grassy top
        xs = np.linspace(X, X + 3200, 70)
        top = []
        for x in xs:
            u = (x - X) / 3200
            h = 600 + 260 * math.sin(min(1.0, u * 3.2) * math.pi / 2) + 40 * math.sin(u * 9 + 1) + 18 * math.sin(u * 23)
            top.append((x, G - h))
        top[0] = (X - 40, G)
        top[1] = (X - 10, G - 380)
        self.top = top
        self.stones = [(rs.uniform(X + 20, X + 3000), rs.uniform(0.0, 1.0), rs.uniform(26, 70), rs.uniform(0.85, 1.25))
                       for _ in range(60)]
        self.lines = [rs.uniform(0, 6.3) for _ in range(10)]

    def top_y(self, x):
        xs = [p[0] for p in self.top]
        return float(np.interp(x, xs, [p[1] for p in self.top]))

    def _body(self, c, x0, x1, shade=1.0):
        pts = [p for p in self.top if x0 <= p[0] <= x1]
        pts = [(x0, self.top_y(x0))] + pts + [(x1, self.top_y(x1))]
        c.polygon(pts + [(x1, self.G), (x0, self.G)], ROCK * shade)
        for k, ph in enumerate(self.lines):                     # strata
            yy0 = self.G - 60 - k * 70
            seg_pts = [(x, yy0 + 10 * math.sin(x * 0.004 + ph)) for x in np.linspace(x0, x1, 12)
                       if yy0 + 10 * math.sin(x * 0.004 + ph) > self.top_y(x) + 30]
            if len(seg_pts) > 1:
                c.polyline(seg_pts, ROCK_DARK, 3)
        for sx, v, r, sh in self.stones:                        # boulders in the face
            if not (x0 + r < sx < x1 - r):
                continue
            sy = lerp(self.top_y(sx) + r + 30, self.G - r * 0.6, v)
            c.polygon(ellipse(sx, sy, r * 1.25, r * 0.8, 14), ROCK * sh * shade)
            c.polyline(ellipse(sx, sy, r * 1.25, r * 0.8, 14, 3.6, 5.6), lighten(ROCK, 1.35) * shade, 2)
        grass = [(x, self.top_y(x)) for x in np.linspace(x0, x1, 40)]
        c.polyline(grass, GRASS, 12)

    def back(self, c, s, t, door_open):
        X, G = self.X, self.G
        for j, x in enumerate(np.arange(X + 420, X + 3100, 330)):    # trees on top of the hill
            if s.visible(x - 250, x + 250):
                tree(c, x, self.top_y(x) + 30, 520 + 70 * (j % 3), 700 + j)
        vx0, vx1 = s.view()[:2]
        self._body(c, max(X - 40, vx0 - 100), min(X + 3200, vx1 + 100))
        self._opening(c, s, t, door_open)

    def _opening(self, c, s, t, door_open):
        G, d0, d1, dh = self.G, self.d0, self.d1, self.door_h
        light = smoothstep(door_open)
        rect(c, d0, G - dh, d1, G, INTERIOR * 0.55 + LAMP * 0.10 * light)
        for k in range(3):                                          # tunnel ribs, the far end is lit
            yy = G - dh + 80 + k * 140
            c.line(d0 + 8, yy, d1 - 8, yy, INTERIOR * 0.8 + LAMP * 0.06 * light, 3)
        rect(c, d0 + 90, G - dh + 70, d1 - 90, G - 30, INTERIOR * 0.45 + LAMP * 0.3 * light)
        rect(c, d0, G - 10, d1, G, FLOOR)
        if light > 0:
            s.glow_draw(lambda g: g.polygon([(d0 + 60, G - dh + 60), (d1 - 60, G - dh + 60), (d1 + 120, G + 6),
                                             (d0 - 120, G + 6)], LAMP * 0.06 * light))

    def front(self, c, s, t, door_open):
        """Rock around the opening (hides whoever walked in), steel frame, door, sign and lamp."""
        G, X, d0, d1, dh = self.G, self.X, self.d0, self.d1, self.door_h
        vx0, vx1 = s.view()[:2]
        if vx1 < X - 100:
            return
        if self.walk_in:
            self._frame(c, s, door_open)
            return
        self._body(c, d1, min(X + 3200, vx1 + 100))
        c.polygon([(X - 40, G), (X - 10, G - 380)] + [p for p in self.top[2:] if p[0] <= d0]
                  + [(d0, self.top_y(d0)), (d0, G)], ROCK)
        top_d = self.top_y(d0)
        c.polygon([(d0, G - dh), (d1, G - dh), (d1, self.top_y(d1)), (d0, top_d)], ROCK)
        c.polyline([(x, self.top_y(x)) for x in np.linspace(X - 10, d1 + 10, 12)], GRASS, 12)
        # glow (moon halo, eyes, Glo's lamp) must not shine through the rock: clear the glow layer there
        def piece(xa, xb, ybot):
            pts = [(xa, self.top_y(xa))] + [p for p in self.top if xa < p[0] < xb] + [(xb, self.top_y(xb))]
            return pts + [(xb, ybot), (xa, ybot)]
        s.glow_draw(lambda g: (g.polygon(piece(X - 10, d0, G + 20), np.zeros(3)),
                               g.polygon(piece(d0, d1, G - dh), np.zeros(3)),
                               g.polygon(piece(d1, min(X + 3200, vx1 + 200), G + 20), np.zeros(3))))
        self._frame(c, s, door_open)

    def _frame(self, c, s, door_open):
        """Steel frame, sign, the roll-up door and the lamp."""
        G, d0, d1, dh = self.G, self.d0, self.d1, self.door_h
        machine_block(c, d0 - 22, G - dh - 46, d1 + 22, G - dh, STEEL)
        c.text("NIGHT SHIFT", (d0 + d1) / 2, G - dh - 23, 30, SIGN_WARM * 0.85)
        rect(c, d0 - 22, G - dh, d0, G, STEEL * 0.8)
        rect(c, d1, G - dh, d1 + 22, G, STEEL * 0.8)
        bot = lerp(G, G - dh + 6, smootherstep(door_open))
        if bot > G - dh + 8:
            rect(c, d0, G - dh, d1, bot, IRON)
            for y in np.arange(G - dh + 30, bot, 34):
                c.line(d0, y, d1, y, IRON * 0.7, 2)
            rect(c, d0, bot - 14, d1, bot, HAZARD * 0.7)
        lamp = SIGN_GREEN if door_open > 0.02 else LAMP
        c.circle(d1 + 60, G - dh - 30, 10, lamp)
        s.glow_draw(lambda g: g.circle(d1 + 60, G - dh - 30, 18, lamp * 0.6))


# ====================================================================== shared act base

class KeeperAct(ForestAct):
    """Forest act with Hans' working tentacles, carried things and per-act nameplates."""
    names = (1.0, 8.0)                     # nameplates float over everyone in this window

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.reach = {}                    # kind -> [(x, y), ...] what its tentacles hold this frame
        self.lift = {}                     # kind -> extra dy (hops, squats) applied in place()
        self.house = House(self.G)

    def name_amount(self, kind, t):
        a, b = self.names
        return smoothstep(seg(t, a, a + 0.6)) * (1 - smoothstep(seg(t, b - 1.0, b)))

    def draw_monsters(self, c, t, kinds=None, before=None):
        """before(kind): draws what that monster carries, just before its tentacles / body."""
        for m in self.s.monsters:
            if kinds is not None and m.kind not in kinds:
                continue
            if m.kind not in self.poses or not self.s.visible(m.x - 600, m.x + 600):
                continue
            dy, ang = self.poses[m.kind]
            if before is not None:
                before(m.kind)
            if m.kind == "tentacles":
                for i, (tx_, ty_) in enumerate(self.reach.get("tentacles", [])):
                    m.work_tentacle(c, tx_, ty_, t, slot=(i % 2) * 2 - 1 if len(self.reach["tentacles"]) <= 2 else i - 1.5,
                                    dy=dy)
            bc = m.body_center()
            mc = Xform(c, 0, dy, ang, 1.0, bc[0], bc[1]) if (dy or ang) else c
            m.draw(mc, t, self.s.glow)
            m.draw_name(Xform(c, 0, dy) if dy else c, self.name_amount(m.kind, t), 30)


# ====================================================================== RETURN

class ReturnAct(KeeperAct):
    """The treehouse at night; down they come and off to the factory."""
    name = "return"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        H, G = self.house, self.G
        self.door_X = 4700.0
        self.hill = Hill(self.door_X, G)
        self.d = d = dict(hold=4.0, down=9.0, walk=13.0, door=3.0, enter=6.5)
        d.update(P.get("durations", {}))
        T, t = {}, 0.0
        for k in ("hold", "down", "walk", "door", "enter"):
            T[k] = t
            t += d[k]
        self.T, self.dur = T, t + 1.0
        # line order walking to the door (front first) and where each waits outside it
        self.order = ["lantern", "wheels", "digger", "springs", "teeth", "tentacles"]
        self.wait_x = {k: self.door_X - 120 - 190 * q for q, k in enumerate(self.order)}
        self.start = {"tentacles": (1700.0, H.py), "teeth": (1210.0, H.py), "springs": (1460.0, H.py),
                      "lantern": (1360.0, H.py - 230), "wheels": (2300.0, G), "digger": (2470.0, G)}

    def melodies(self):
        return [(3.0, self.dur - 2.5, "music_box", 1.0, 0.55, TUNE_MAJOR)]

    def target(self, t):
        T, H = self.T, self.house
        if t < T["walk"] + 1.0:
            return H.tx + 350, H.py + 120, 0.8
        if t < T["door"]:
            xs = [self.s.by_kind[k].x for k in self.order if k in self.s.by_kind]
            u = smootherstep(seg(t, T["walk"] + 1.0, T["walk"] + 4.0))
            return lerp(H.tx + 350, float(np.mean(xs)) + 150, u), lerp(H.py + 120, self.G - 330, u), lerp(0.8, 1.0, u)
        return self.door_X - 300, self.G - 330, 1.0

    def enter_t(self, q):
        return self.T["enter"] + 0.2 + q * 0.95

    def update(self, t, dt):
        T, H, G = self.T, self.house, self.G
        s = self.s
        self.reach = {}
        for q, kind in enumerate(self.order):
            m = self.m(kind)
            if m is None:
                continue
            x0, y0 = self.start[kind]
            wx = self.wait_x[kind]
            gx = 2120.0 + 175 * (5 - q)                         # where each gathers at the foot of the tree (front of the line rightmost)
            dy, ang, walk = 0.0, 0.0, None
            # 1) down from the treehouse
            if kind == "springs":
                j0 = T["down"] + 0.6
                jump = Jump(x0, y0, gx + 60, G, apex=90)
                if t < j0:
                    x, y = x0, y0
                elif t < j0 + jump.dur:
                    x, y = jump.at(t - j0)
                else:
                    x, y = gx + 60, G
                m.spring = 0.8 * max(0.0, 1 - min(abs(t - j0), abs(t - j0 - jump.dur)) / 0.12)
            elif kind == "lantern":
                x, y, _ = path([(T["down"] + 0.3, x0, y0), (T["down"] + 4.0, gx, G - 60)], t)
            elif kind in ("tentacles", "teeth"):
                k0 = T["down"] + (0.4 if kind == "tentacles" else 3.6)
                x, y, mv = path([(k0, x0, y0), (k0 + 1.0, H.ladder_x, y0), (k0 + 4.2, H.ladder_x, G), (k0 + 4.8, gx, G)], t)
                if kind == "tentacles" and k0 + 0.8 <= t < k0 + 4.3:
                    # lowers himself hand over hand: two tentacles hold the rungs just above his head
                    hy = y - 305 * m.k
                    grips = [(H.ladder_x + (26 if k % 2 else -26), H.rung_y(k)) for k in range(H.n_rungs)]
                    grips += [(H.ladder_x - 70, H.py + 4), (H.ladder_x + 34, H.py - 2)]     # platform edge, rail top
                    above = sorted((g for g in grips if g[1] < hy - 60), key=lambda g: -g[1])
                    self.reach["tentacles"] = above[:2]
                walk = 1.0 if mv else 0.0
            else:
                x, y = x0, y0
            # 2) along the path to the door, then in
            if t >= T["walk"]:
                lead = T["walk"] + 0.35 * q
                arrive = T["door"] - 0.2 + 0.25 * q
                if kind == "springs":
                    x, lift, sq = hops(gx + 60, wx, lead, arrive, t)
                    dy -= lift
                    m.spring = max(m.spring, sq) if t < arrive else 0.0
                elif kind == "lantern":
                    x, y, _ = path([(lead, gx, G - 60), (arrive, wx, G - 60)], t)
                else:
                    x, y, mv = path([(lead, gx, G), (arrive, wx, G)], t)
                    walk = 1.0 if mv else 0.0
                e0 = self.enter_t(q)
                if t >= e0:
                    xin = self.hill.d1 + 260
                    if kind == "springs":
                        x, lift, sq = hops(wx, xin, e0, e0 + 2.2, t, apex=55, step=150)
                        dy = -lift
                        m.spring = sq
                    else:
                        x, _, mv = path([(e0, wx, 0), (e0 + 2.4, xin, 0)], t)
                        walk = 1.0 if mv else 0.0
            if kind == "lantern":
                y = G - 60 if t >= T["walk"] else y
            self.place(m, x, t, dt, y=y, dy=dy, ang=ang, walk=walk)
        self._sounds(t)
        if s.particles.rng.uniform() < 0.25 and t < T["walk"] + 2:
            s.particles.items.append(_firefly(s.particles.rng, H.tx, H.py, G))

    def _sounds(self, t):
        T, s, H = self.T, self.s, self.house
        if self.crossed(T["hold"] + 1.2):
            for q, kind in enumerate(self.order):
                self.say(t + q * 0.22, kind, "hum", H.tx, H.py, 0.4)
        if self.crossed(T["down"] + 0.6):
            self.hit(t, "boing", s.note(2, -1), 0.5, 1460, H.py)
        sp = self.m("springs")
        if sp is not None:
            j = Jump(self.start["springs"][0], H.py, 2120 + 175 * 2 + 60, self.G, apex=90)
            if self.crossed(T["down"] + 0.6 + j.dur):
                self.hit(t, "thud", 44, 0.4, sp.x, self.G)
        for k in range(H.n_rungs):
            for kind, k0 in (("tentacles", T["down"] + 1.4), ("teeth", T["down"] + 4.4)):
                if self.crossed(k0 + (H.n_rungs - 1 - k) * 3.2 / H.n_rungs):
                    self.hit(t, "clack", s.note(H.n_rungs - k, -1), 0.22, H.ladder_x, H.rung_y(k))
        if self.crossed(T["walk"] + 0.5):
            self.say(t, "lantern", "up", 2200, self.G - 200, 0.45)
            self.fx(t, "rustle", T["door"] - T["walk"], 0.18, 3000, self.G)
        if self.crossed(T["door"]):
            self.fx(t, "motor", self.d["door"], 0.55, self.hill.d0, self.G - 300)
            self.fx(t, "hiss", 0.6, 0.25, self.hill.d0, self.G - 300)
        if self.crossed(T["door"] + self.d["door"] - 0.1):
            self.hit(t, "clunk", 45, 0.5, self.hill.d0, self.G - 500)
        for q, kind in enumerate(self.order):
            if self.crossed(self.enter_t(q) + 0.3):
                self.say(t, kind, "up", self.hill.d0, self.G - 200, 0.35)
        # footsteps along the path (soft, varied)
        if T["walk"] <= t < T["door"] + 0.5:
            for k in range(int((T["door"] - T["walk"]) / 0.42)):
                if self.crossed(T["walk"] + 0.3 + k * 0.42):
                    self.hit(t, "pluck", s.note((k * 3) % 5, -1), 0.12, 3000, self.G)

    def draw(self, c, t):
        s, T, H, G = self.s, self.T, self.house, self.G
        self.backdrop(c, t)
        door = seg(t, T["door"], T["door"] + self.d["door"])
        for j, x in enumerate((-400, 120, 2700, 3150, 3600, 4100)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        self.hill.back(c, s, t, door)
        H.draw_tree(c, s)
        H.draw_house(c, s, t, windows=1.0 - smoothstep(seg(t, T["down"] + 3.0, T["down"] + 5.0)), lanterns=1.0)
        if "lantern" in self.poses:
            ln = self.m("lantern")
            self.lantern_light(c, ln.x, ln.y - 140, k=0.8)
        self.draw_monsters(c, t)
        self.hill.front(c, s, t, door)


# ====================================================================== shared Halloween pieces

POLE = np.array([116, 86, 58], np.float64)
POLE_ITEMS = ["bat", "ghost", "bat", "ghost", "bat", "bat", "ghost", "bat", "ghost", "bat"]
GHOST_GLOW = np.array([200, 220, 255], np.float64)


def swing(t, t0, L, amp=0.35, tau=2.5):
    """Damped pendulum angle for something hung at t0 on a thread of length L (real g)."""
    if t < t0:
        return 0.0
    w = math.sqrt(GRAVITY / max(20.0, L))
    tt = t - t0
    return amp * math.exp(-tt / tau) * math.cos(w * tt)


def wagon_spot(wx, G, k):
    """Where jack-o'-lantern k sits in the wagon: four on the bed, three nestled on top, one on the very top."""
    if k < 4:
        return wx - 75 + 50 * k, G - 66
    if k < 7:
        return wx - 50 + 50 * (k - 4), G - 66 - 64
    return wx, G - 66 - 128


def draw_wagon(c, s, wx, G, pumpkins, t, r=40.0):
    """Wagon with jack-o'-lanterns: `pumpkins` = list of (slot, lit) still in it."""
    for k, lit in pumpkins:
        px, py = wagon_spot(wx, G, k)
        D.pumpkin(c, px, py, r, paint=1.0, ribs=1.0, stem=1.0, carve=1.0, lit=lit, t=t, glow=s.glow, seed=k * 1.3,
                  face=k % 2)
    rect(c, wx - 110, G - 96, wx + 110, G - 34, PLANK * 0.75)
    c.line(wx - 110, G - 96, wx + 110, G - 96, PLANK, 3)
    for wxx in (wx - 70, wx + 70):
        c.circle(wxx, G - 24, 24, np.array([30, 30, 34]))
        c.circle(wxx, G - 24, 9, STEEL * 1.8)


def pole_spot(x0, y0, x1, y1, i):
    u = (i + 0.5) / len(POLE_ITEMS)
    return lerp(x0, x1, u), lerp(y0, y1, u)


def draw_pole(c, s, x0, y0, x1, y1, items, t, sway=0.0):
    """The carrying pole with the bats and ghosts hanging from it (items: list of kind or None)."""
    c.line(x0, y0, x1, y1, POLE, 10)
    c.line(x0, y0 - 3, x1, y1 - 3, lighten(POLE, 1.3), 2)
    for i, kind in enumerate(items):
        if kind is None:
            continue
        hx, hy = pole_spot(x0, y0, x1, y1, i)
        a = sway * math.sin(t * 3.1 + i * 0.7)
        L = 46 if kind == "bat" else 30
        ex, ey = hx + math.sin(a) * L, hy + math.cos(a) * L
        c.line(hx, hy, ex, ey, CABLE, 2)
        if kind == "bat":
            D.bat(c, ex, ey + 30, 0.55, flap=0.15 * math.sin(t * 2 + i), t=t, glow=s.glow)
        else:
            D.ghost(c, ex, ey, 0.62, drape=1.0, eyes=1.0, t=t, seed=i, sway=a * 2, ball=False)
            s.glow_draw(lambda g, ex=ex, ey=ey: g.circle(ex, ey + 40, 50, GHOST_GLOW * 0.14))


def draw_string_coil(c, x, y, lit, t, s):
    """The light string carried as a loose loop."""
    D.light_string(c, [(x - 50, y), (x, y + 6), (x + 50, y)], 6, 9, glow=s.glow, t=t, sag=0.35, bulbs_on=[lit] * 6)


# ====================================================================== HAUL

class HaulAct(KeeperAct):
    """Out of the cliff door with everything: a glowing procession back through the forest."""
    name = "haul"

    # where each one stops at the tree (decorate starts from exactly here)
    END = {"lantern": 1500.0, "wheels": 1860.0, "teeth": 2300.0, "tentacles": 3160.0, "springs": 3420.0,
           "digger": 3620.0}

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.door_X = 4700.0
        self.hill = Hill(self.door_X, self.G)
        self.d = d = dict(door=2.5, walk=19.0, settle=3.5)
        d.update(P.get("durations", {}))
        self.dur = 0.6 + d["door"] + d["walk"] + d["settle"]
        self.out = {"lantern": 2.6, "wheels": 3.4, "teeth": 4.6, "tentacles": 4.6, "springs": 6.2, "digger": 7.0}
        self.arrive = {k: 0.6 + d["door"] + d["walk"] - 1.0 + 0.25 * q
                       for q, k in enumerate(["lantern", "wheels", "teeth", "tentacles", "springs", "digger"])}

    def melodies(self):
        return [(3.0, self.dur - 1.5, "music_box", 1.0, 0.6, TUNE_HALLOWEEN)]

    def target(self, t):
        G = self.G
        if t < 6.0:
            return self.hill.d0 - 150, G - 330, 1.0
        xs = [m.x for k, m in self.s.by_kind.items() if k in self.poses]
        mid = float(np.mean(xs)) if xs else 3000.0
        u = smootherstep(seg(t, 6.0, 9.0))
        return lerp(self.hill.d0 - 150, mid, u), lerp(G - 330, G - 380, u), lerp(1.0, 0.8, u)

    def pole_ends(self, t):
        tw, hn = self.m("teeth"), self.m("tentacles")
        y = self.G - 300
        bob = 6 * math.sin(t * 6)
        return (tw.x + 30, y + bob), (hn.x - 70, y - bob)

    def update(self, t, dt):
        G = self.G
        self.reach = {}
        start = self.hill.d1 + 220
        for kind, m in self.s.by_kind.items():
            o, a = self.out[kind], self.arrive[kind]
            x1 = self.END[kind]
            x0 = start + (860 if kind == "tentacles" else 0)
            if kind == "springs":
                x, lift, sq = hops(x0, x1, o, a, t, apex=60, step=170)
                m.spring = sq
                self.place(m, x, t, dt, dy=-lift, walk=0.0)
                continue
            x, _, mv = path([(o, x0, 0), (a, x1, 0)], t)
            self.place(m, x, t, dt, y=G - 60 if kind == "lantern" else None, walk=1.0 if mv else 0.0)
        if self.m("tentacles") is not None and self.m("teeth") is not None:
            (px0, py0), (px1, py1) = self.pole_ends(t)
            self.reach["tentacles"] = [(px1, py1)]
        self._sounds(t)

    def _sounds(self, t):
        s, G = self.s, self.G
        if self.crossed(0.6):
            self.fx(t, "motor", self.d["door"], 0.5, self.hill.d0, G - 300)
        if self.crossed(0.6 + self.d["door"]):
            self.hit(t, "clunk", 45, 0.45, self.hill.d0, G - 500)
        for q, kind in enumerate(["lantern", "wheels", "teeth", "springs", "digger"]):
            if self.crossed(self.out[kind] + 0.6):
                self.say(t, kind, "cheer" if q % 2 == 0 else "hum", self.hill.d0, G - 200, 0.35)
        if self.crossed(4.0):
            self.fx(t, "rustle", self.d["walk"], 0.15, 3200, G)
        sp = self.m("springs")
        if sp is not None:
            o, a = self.out["springs"], self.arrive["springs"]
            n = max(1, int(round(abs(self.END["springs"] - (self.hill.d1 + 220)) / 170)))
            for k in range(n):
                if self.crossed(o + (k + 1) * (a - o) / n):
                    self.hit(t, "boing", s.note(k % 5, -1), 0.22, sp.x, G)

    def draw(self, c, t):
        s, G = self.s, self.G
        self.backdrop(c, t)
        door = seg(t, 0.6, 0.6 + self.d["door"])
        for j, x in enumerate((-400, 120, 2700, 3150, 3600, 4100)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        self.hill.back(c, s, t, door)
        self.house.draw_tree(c, s)
        self.house.draw_house(c, s, t, windows=0.0, lanterns=1.0)
        if "lantern" in self.poses:
            ln = self.m("lantern")
            self.lantern_light(c, ln.x, ln.y - 140, k=0.8)
        wh = self.m("wheels")
        if wh is not None and "wheels" in self.poses:
            wx = wh.x + 200
            c.line(wh.x + 60, G - 40, wx - 110, G - 40, CABLE * 1.5, 5)
            draw_wagon(c, s, wx, G, [(k, 1.0) for k in range(8)], t)
        if "teeth" in self.poses and "tentacles" in self.poses:
            (x0, y0), (x1, y1) = self.pole_ends(t)
            draw_pole(c, s, x0, y0, x1, y1, POLE_ITEMS, t, sway=0.25)
        self.draw_monsters(c, t)
        ln = self.m("lantern")
        if ln is not None and "lantern" in self.poses:
            draw_string_coil(c, ln.x, ln.y - (260 - 82) * ln.k + 70, 1.0, t, s)
        dg = self.m("digger")
        if dg is not None and "digger" in self.poses:                  # two stakes over Digs' shoulder
            for q in range(2):
                c.line(dg.x - 90 + q * 14, dg.y - 150, dg.x + 70 + q * 14, dg.y - 200, POLE * 0.9, 8)
        self.hill.front(c, s, t, door)


# ====================================================================== DECORATE

class DecorateAct(KeeperAct):
    """Back at the treehouse: every decoration goes up, carried and placed by the Keeper whose body suits the job.
    Wheels + Digs set five jack-o'-lanterns along the front of the tree; Springs jumps three up onto the deck and
    hangs the bats on the high branches (real-gravity jumps); Glo floats the ghosts up to the branch tips; Hans
    climbs up and hangs the light string under the deck. Then the lights come on and the forest animals visit."""
    name = "decorate"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        H, G = self.house, self.G
        self.wagon_x = HaulAct.END["wheels"] + 200
        self.pole_x = (HaulAct.END["teeth"] + 30, HaulAct.END["tentacles"] - 70)
        self.pole_y = G - 300
        d = dict(hold=3.0, finale=30.0)
        d.update(P.get("durations", {}))
        self.d = d
        T = {"start": 0.0}
        # Digs drives the two stakes in under the pole ends; the pole goes down onto them
        T["stake1"], T["stake2"] = 2.4, 5.6
        T["pole_down"] = 7.0
        # ground row: Wheels takes the odd ones, Digs the even ones, alternating, from the wagon
        self.ground = []                                  # (who, wagon slot, spot x, t pick, t set)
        tw, tdg = 7.6, 9.6
        plan = [("wheels", 7, 4), ("digger", 6, 3), ("wheels", 5, 2), ("digger", 4, 1), ("wheels", 3, 0)]
        for who, slot, i in plan:
            sx = H.ground_pumpkins[i]
            wx, _ = wagon_spot(self.wagon_x, G, slot)
            speed = 480.0 if who == "wheels" else 300.0
            drive = abs(wx - sx) / speed + 0.3
            t0_ = tw if who == "wheels" else tdg
            self.ground.append(dict(who=who, slot=slot, x=sx, pick=t0_, set=t0_ + 0.5 + drive, back=t0_ + 0.9 + 2 * drive))
            if who == "wheels":
                tw = t0_ + 1.0 + 2 * drive
            else:
                tdg = t0_ + 1.0 + 2 * drive
        T["ground_end"] = max(g["set"] for g in self.ground) + 0.6
        # Springs: deck pumpkins (two trips), then six bats in two batches
        launch = self.wagon_x + 170
        t = max(T["ground_end"] - 2.0, 10.0)
        self.springs_plan = []                            # list of segments: (kind, t0, t1, data)
        t_hop = t
        t += 2.6                                          # hop from where he stood over to the wagon
        self.springs_plan.append(("hop", t_hop, t, (HaulAct.END["springs"], launch)))
        self.deck = []
        for slots, land in (([2, 1], (H.deck_pumpkins[0] + H.deck_pumpkins[1]) / 2), ([0], H.deck_pumpkins[2])):
            t_pick = t
            t += 0.6
            up = Jump(launch, G, land, H.py, apex=90)
            self.springs_plan.append(("pick", t_pick, t, slots))
            self.springs_plan.append(("jump", t, t + up.dur, up))
            t_land = t + up.dur
            t = t_land + 0.6
            self.springs_plan.append(("stand", t_land, t, (land, H.py)))
            for q, sl in enumerate(slots):
                spot = [H.deck_pumpkins[0], H.deck_pumpkins[1]][q] if len(slots) == 2 else H.deck_pumpkins[2]
                self.deck.append(dict(slot=sl, x=spot, pick=t_pick, land=t_land, set=t_land + 0.4))
            down = Jump(land, H.py, launch, G, apex=50)
            self.springs_plan.append(("jump", t, t + down.dur, down))
            t += down.dur
        T["deck_end"] = t
        self.bats = []                                    # (spot, pole item, t take, t hang)
        bat_items = [i for i, k in enumerate(POLE_ITEMS) if k == "bat"]
        for batch in (range(0, 3), range(3, 6)):
            take_x = pole_spot(self.pole_x[0], self.pole_y, self.pole_x[1], self.pole_y, bat_items[batch[0]])[0]
            x_prev = self._springs_x_end()
            t_hop = t
            t += abs(take_x - x_prev) / 420 + 0.4
            self.springs_plan.append(("hop", t_hop, t, (x_prev, take_x)))
            t_take = t
            t += 0.7
            self.springs_plan.append(("take", t_take, t, take_x))
            x_prev = take_x
            for b in batch:
                bx, by = H.bat_spots[b]
                t_hop = t
                t += abs((bx - 130) - x_prev) / 420 + 0.3
                self.springs_plan.append(("hop", t_hop, t, (x_prev, bx - 130)))
                ya = by + 180                               # at the top of the jump his head is at the branch
                h = G - ya
                tu = math.sqrt(2 * h / GRAVITY)
                self.springs_plan.append(("big", t, t + 2 * tu, (bx - 130, bx + 130, ya)))
                self.bats.append(dict(b=b, item=bat_items[b], take=t_take, hang=t + tu))
                t += 2 * tu
                x_prev = bx + 130
        T["bats_end"] = t
        # Glo: ghosts, from the pole to the branch tips (while Springs works)
        self.ghosts = []
        ghost_items = [i for i, k in enumerate(POLE_ITEMS) if k == "ghost"]
        tg = T["deck_end"] - 2.0
        gx_prev, gy_prev = HaulAct.END["lantern"], G - 60
        self.glo_keys = [(0.0, gx_prev, gy_prev)]
        # first she hands the coiled light string to Hans
        hx = HaulAct.END["tentacles"]
        self.glo_keys += [(T["pole_down"] + 0.2, hx - 60, G - 330), (T["pole_down"] + 1.4, hx - 60, G - 330)]
        self.hand_over = T["pole_down"] + 0.8
        self.glo_keys += [(tg - 1.0, 2000, H.py - 200)]
        for q, it in enumerate(ghost_items):
            px, py_ = pole_spot(self.pole_x[0], self.pole_y, self.pole_x[1], self.pole_y, it)
            sx, sy = H.ghost_spots[q]
            t_take = tg + 1.6
            t_hang = t_take + 0.4 + math.hypot(sx - px, sy - py_) / 520 + 0.3
            self.glo_keys += [(t_take - 0.3, px, py_ + 160), (t_take + 0.3, px, py_ + 160),
                              (t_hang - 0.2, sx, sy + 150), (t_hang + 0.4, sx, sy + 150)]
            self.ghosts.append(dict(q=q, item=it, take=t_take, hang=t_hang))
            tg = t_hang + 0.4
        T["ghosts_end"] = tg
        # Hans: light string under the deck, right to left, after the jumping is done
        T["lights"] = max(T["bats_end"], T["ghosts_end"]) - 6.0
        T["climb"] = T["lights"] + 6.0
        T["hook0"] = T["climb"] + 3.4
        self.hook_t = [T["hook0"] + q * 1.5 for q in range(len(H.hooks))]
        T["lights_on"] = self.hook_t[-1] + 1.4
        T["finale"] = T["lights_on"]
        T["animals"] = T["finale"] + 5.0
        T["pull"] = T["finale"] + 14.0
        T["end"] = T["finale"] + d["finale"]
        self.T, self.dur = T, T["end"]
        self.glo_keys += [(T["ghosts_end"] + 1.0, H.tx + 200, H.py - 330), (T["lights_on"], H.tx + 200, H.py - 330),
                          (T["lights_on"] + 4.0, H.tx - 40, H.wall_top - 330)]
        self.stats = {"decorate_s": round(self.dur, 1), "alignment_ok": self._check_alignment()}

    def _springs_x_end(self):
        k, t0, t1, data = self.springs_plan[-1]
        if k == "jump":
            return data.x1
        if k in ("hop",):
            return data[1]
        if k == "big":
            return data[1]
        if k == "stand":
            return data[0]
        return self.wagon_x + 170

    def _check_alignment(self):
        """Owner rule: things line up. Pumpkins, hooks and bats must be evenly spaced / symmetric."""
        H = self.house
        g = np.diff(H.ground_pumpkins)
        d = np.diff(H.deck_pumpkins)
        hk = np.diff([h[0] for h in H.hooks])
        ok = bool(np.ptp(g) < 1e-6 and np.ptp(d) < 1e-6 and np.ptp(hk) < 1e-6)
        bl = [b[0] for b in H.bat_spots[:3]]
        br = [b[0] for b in H.bat_spots[3:]]
        ok = ok and all(abs((H.tx - a) - (b - H.tx)) < 40 for a, b in zip(bl, br))
        return ok

    def melodies(self):
        T = self.T
        return [(2.0, T["finale"] - 1.0, "music_box", 0.9, 0.6, TUNE_HALLOWEEN),
                (T["finale"] + 1.0, self.dur - 3.0, "music_box", 1.1, 0.5, TUNE_HALLOWEEN)]

    # ------------------------------------------------------------------ camera

    def target(self, t):
        T, H, G = self.T, self.house, self.G
        keys = [(0.0, 2350, G - 380, 0.8), (T["pole_down"], 2150, G - 360, 0.85),
                (T["pole_down"] + 2.0, 1650, G - 330, 0.95), (T["ground_end"] - 0.5, 1600, G - 330, 0.95),
                (T["ground_end"] + 1.5, 1650, H.py + 110, 0.85), (T["deck_end"], 1650, H.py + 110, 0.85),
                (T["deck_end"] + 2.5, H.tx + 60, H.py - 60, 0.7), (T["lights"] + 3.0, H.tx + 60, H.py - 60, 0.7),
                (T["climb"] + 1.0, 1650, H.py + 80, 0.95), (T["lights_on"] - 0.5, 1350, H.py + 80, 0.95),
                (T["lights_on"] + 2.5, H.tx + 120, H.py + 60, 0.72), (T["pull"], H.tx + 120, H.py + 60, 0.72),
                (self.dur, H.tx + 140, H.py, 0.62)]
        return _ease_keys(keys, t)

    # ------------------------------------------------------------------ update

    def update(self, t, dt):
        T, H, G = self.T, self.house, self.G
        self.reach = {}
        s = self.s
        # Digs: stakes first, then pumpkins, then joins the others in front of the tree
        dg = self.m("digger")
        if dg is not None:
            dg.dig = 0.0
            sx1, sx2 = self.pole_x[1], self.pole_x[0]
            if t < T["pole_down"] + 0.5:
                x, _, mv = path([(0.0, HaulAct.END["digger"], 0), (T["stake1"] - 0.4, sx1 + 110, 0),
                                 (T["stake1"] + 1.0, sx1 + 110, 0), (T["stake2"] - 0.4, sx2 + 110, 0)], t)
                for st in (T["stake1"], T["stake2"]):
                    if st - 0.3 <= t < st + 0.9:
                        dg.dig = 0.5 + 0.5 * math.sin((t - st) * 14)
                self.place(dg, x, t, dt, walk=1.0 if mv else 0.0)
            else:
                self._carrier(dg, "digger", t, dt, rest=(H.ladder_x + 330, G))
        wh = self.m("wheels")
        if wh is not None:
            self._carrier(wh, "wheels", t, dt, rest=(self.wagon_x + 120, G))
        # Twigs + Hans hold the pole until it's on the stakes; then Twigs waits by it, Hans does the lights
        tw = self.m("teeth")
        if tw is not None:
            x = HaulAct.END["teeth"]
            if t >= T["finale"] - 3.0:
                x = lerp(x, H.ladder_x + 560, smootherstep(seg(t, T["finale"] - 3.0, T["finale"] + 1.0)))
            dy = -abs(math.sin(t * 6)) * 24 if T["lights_on"] <= t < T["lights_on"] + 2 else 0.0
            self.place(tw, x, t, dt, dy=dy, walk=1.0 if abs(x - tw.x) > 1 else 0.0)
        hn = self.m("tentacles")
        if hn is not None:
            self._hans(hn, t, dt)
        sp = self.m("springs")
        if sp is not None:
            self._springs(sp, t, dt)
        gl = self.m("lantern")
        if gl is not None:
            x, y, _ = path(self.glo_keys, t)
            self.place(gl, x, t, dt, y=y)
        self._animals_update(t)
        self._sounds(t)
        if s.particles.rng.uniform() < 0.3:
            s.particles.items.append(_firefly(s.particles.rng, H.tx, H.py, G))

    def _carrier(self, m, kind, t, dt, rest):
        """Wheels / Digs: wagon -> spot -> back, one jack-o'-lantern at a time."""
        G = self.G
        reach = 135 if kind == "wheels" else 120
        trips = [g for g in self.ground if g["who"] == kind]
        x = m.x if m.x else rest[0]
        for g in trips:
            wx, _ = wagon_spot(self.wagon_x, G, g["slot"])
            if t < g["pick"]:
                break
            if t < g["set"]:
                x = lerp(wx - reach, g["x"] - reach, smootherstep(seg(t, g["pick"] + 0.5, g["set"])))
                break
            if t < g["back"]:
                x = g["x"] - reach
                if g is not trips[-1]:
                    nxt = trips[trips.index(g) + 1]
                    nwx, _ = wagon_spot(self.wagon_x, G, nxt["slot"])
                    x = lerp(g["x"] - reach, nwx - reach, smootherstep(seg(t, g["set"] + 0.4, g["back"])))
                break
        else:
            g = trips[-1]
            x = lerp(g["x"] - reach, rest[0], smootherstep(seg(t, self.T["finale"] - 3.0, self.T["finale"] + 1.0)))
        if trips and t < trips[0]["pick"]:
            wx, _ = wagon_spot(self.wagon_x, G, trips[0]["slot"])
            x0 = HaulAct.END[kind] if kind == "wheels" else self.pole_x[0] + 110
            x = lerp(x0, wx - reach, smootherstep(seg(t, trips[0]["pick"] - 1.6, trips[0]["pick"])))
        dy = -abs(math.sin(t * 6)) * 16 if self.T["lights_on"] <= t < self.T["lights_on"] + 2 else 0.0
        self.place(m, x, t, dt, dy=dy)

    def ground_state(self, g, t):
        """(x, y bottom) of a ground jack-o'-lantern: in the wagon, carried, or set down."""
        G = self.G
        wx, wy = wagon_spot(self.wagon_x, G, g["slot"])
        if t < g["pick"] + 0.4:
            return None
        m = self.m(g["who"])
        if t < g["set"]:
            hold = 135 if g["who"] == "wheels" else 120
            return m.x + hold, G - (150 if g["who"] == "wheels" else 120)
        drop = smoothstep(seg(t, g["set"], g["set"] + 0.3))
        return g["x"], lerp(G - (150 if g["who"] == "wheels" else 120), G, drop)

    def _hans(self, m, t, dt):
        T, H, G = self.T, self.house, self.G
        reach = []
        start = HaulAct.END["tentacles"]
        if t < T["pole_down"]:
            reach.append((self.pole_x[1], self.pole_y))      # still holding up its end of the pole
            self.place(m, start, t, dt)
        elif t < T["climb"]:
            x, _, mv = path([(T["lights"], start, 0), (T["climb"], H.ladder_x + 120, 0)], t)
            self.place(m, x, t, dt, walk=1.0 if mv else 0.0)
            if t >= self.hand_over:
                reach.append((m.x + 110, m.y - 210))           # holding the coiled string
        elif t < T["hook0"] - 0.6:
            # up the ladder hand over hand
            x, y, mv = path([(T["climb"], H.ladder_x + 120, G), (T["climb"] + 0.5, H.ladder_x, G),
                             (T["hook0"] - 1.3, H.ladder_x, H.py), (T["hook0"] - 0.6, H.hooks[-1][0] + 60, H.py)], t)
            self.place(m, x, t, dt, y=y, walk=1.0 if mv else 0.0)
            hy = y - 305 * m.k
            grips = [(H.ladder_x + (26 if k % 2 else -26), H.rung_y(k)) for k in range(H.n_rungs)]
            grips += [(H.ladder_x - 70, H.py + 4), (H.ladder_x + 34, H.py - 2)]
            above = sorted((g for g in grips if g[1] < hy - 60), key=lambda g: -g[1])
            reach += above[:2]
        else:
            # along the deck, right to left, hooking the string on under the edge
            q = min(len(H.hooks) - 1, max(0, int((t - T["hook0"] + 0.75) / 1.5)))
            hx, hy = H.hooks[-1 - q]
            x0 = H.hooks[-q][0] + 60 if q else H.hooks[-1][0] + 60
            x = lerp(x0, hx + 60, smootherstep(seg(t, self.hook_t[q] - 0.75, self.hook_t[q] - 0.2)))
            if t > self.hook_t[-1] + 0.5:
                x = hx + 60
            self.place(m, x, t, dt, y=H.py, walk=1.0 if abs(x - m.x) > 1 else 0.0)
            if t < T["lights_on"] + 0.2:
                reach.append((hx, hy + 6))
        self.reach["tentacles"] = reach

    def _springs(self, m, t, dt):
        G, H = self.G, self.house
        m.spring = 0.0
        x, y, dy = HaulAct.END["springs"], G, 0.0
        self.springs_carry = None
        for k, t0, t1, data in self.springs_plan:
            if t < t0:
                break
            if t >= t1:
                continue
            if k == "hop":
                x, lift, sq = hops(data[0], data[1], t0, t1, t, apex=55, step=150)
                dy, m.spring = -lift, sq
            elif k in ("pick", "take", "stand"):
                if k == "stand":
                    x, y = data
                else:
                    x = self.wagon_x + 170 if k == "pick" else data
                m.spring = 0.5 * max(0.0, 1 - (t - t0) / 0.2)
            elif k == "jump":
                x, y = data.at(t - t0)
                m.spring = 0.8 * max(0.0, 1 - min(t - t0, t1 - t) / 0.1)
            elif k == "big":
                xa, xb, ya = data
                tu = (t1 - t0) / 2
                tau = t - t0
                x = lerp(xa, xb, tau / (t1 - t0))
                v = GRAVITY * tu
                y = G - (v * tau - 0.5 * GRAVITY * tau * tau)
                m.spring = 0.9 * max(0.0, 1 - min(tau, t1 - t) / 0.1)
            break
        else:
            pass
        if t >= self.T["bats_end"]:
            # hops up onto the deck for the finale
            j = Jump(self._springs_x_end(), G, H.p1 - 60, H.py, apex=90)
            t0 = self.T["finale"] - 2.0
            if t < t0:
                x, y = self._springs_x_end(), G
            elif t < t0 + j.dur:
                x, y = j.at(t - t0)
            else:
                x, y = H.p1 - 60, H.py
                if self.T["lights_on"] <= t < self.T["lights_on"] + 2.4:
                    ph = ((t - self.T["lights_on"]) % 0.8) / 0.8
                    dy = -4 * 110 * ph * (1 - ph)
        self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)

    def carrying_springs(self, t):
        """What Springs holds overhead right now: ('pumpkins', slots) / ('bats', [b...]) / None."""
        for d in self.deck:
            if d["pick"] + 0.3 <= t < d["set"]:
                return "pumpkins", [dd["slot"] for dd in self.deck if dd["pick"] == d["pick"] and t < dd["set"]]
        held = [b["b"] for b in self.bats if b["take"] + 0.4 <= t < b["hang"]]
        return ("bats", held) if held else None

    # ------------------------------------------------------------------ animals

    def _animals_update(self, t):
        pass

    def animal_pos(self, i, t):
        """Two bunnies and a hedgehog come out of the dark to look at the jack-o'-lanterns."""
        T, H, G = self.T, self.house, self.G
        a0 = T["animals"] + i * 1.6
        end = [H.ground_pumpkins[0] - 200, H.ground_pumpkins[0] - 330, H.ground_pumpkins[0] - 100][i]
        u = seg(t, a0, a0 + 6.0)
        x = lerp(200 - i * 120, end, smootherstep(u))
        hop = 0.0
        if i < 2 and 0 < u < 1:
            ph = (u * 9) % 1.0
            hop = 4 * 34 * ph * (1 - ph)
        if i < 2 and u >= 1:
            ph = ((t - a0 - 6.0) % 3.0)
            hop = 4 * 30 * min(1.0, ph / 0.4) * (1 - min(1.0, ph / 0.4)) if ph < 0.4 else 0.0
        return x, hop

    # ------------------------------------------------------------------ sound

    def _sounds(self, t):
        T, s, H, G = self.T, self.s, self.house, self.G
        for st in (T["stake1"], T["stake2"]):
            if self.crossed(st):
                for q in range(3):
                    self.hit(t + q * 0.25, "thud", 43, 0.4, self.pole_x[0], G)
        if self.crossed(T["pole_down"]):
            self.hit(t, "clunk", 45, 0.45, (self.pole_x[0] + self.pole_x[1]) / 2, self.pole_y)
            self.say(t + 0.3, "teeth", "hum", self.pole_x[0], G - 300, 0.35)
        if self.crossed(self.hand_over):
            self.say(t, "lantern", "up", self.pole_x[1], G - 300, 0.35)
            self.hit(t, "chime", s.note(4, 0), 0.25, self.pole_x[1], G - 300)
        for q, g in enumerate(self.ground):
            if self.crossed(g["pick"] + 0.3):
                self.hit(t, "clack", s.note(q, 0), 0.25, self.wagon_x, G - 100)
            if self.crossed(g["set"] + 0.3):
                self.hit(t, "thud", 46, 0.4, g["x"], G)
                self.hit(t + 0.05, "chime", s.note(q + 2, 0), 0.3, g["x"], G - 60)
        for k, t0, t1, data in self.springs_plan:
            if k in ("jump", "big") and self.crossed(t0):
                self.hit(t, "boing", s.note(2 if k == "big" else 0, -1), 0.5, self.m("springs").x, G)
            if k in ("jump", "big") and self.crossed(t1):
                self.hit(t, "thud", 44, 0.35, self.m("springs").x, G)
            if k == "hop":
                n = max(1, int(round(abs(data[1] - data[0]) / 150)))
                for q in range(n):
                    if self.crossed(t0 + (q + 1) * (t1 - t0) / n):
                        self.hit(t, "boing", s.note(q % 5, -1), 0.18, data[1], G)
        for d in self.deck:
            if self.crossed(d["set"]):
                self.hit(t, "clunk", s.note(d["slot"], -1), 0.4, d["x"], H.py)
        for b in self.bats:
            if self.crossed(b["hang"]):
                bx, by = H.bat_spots[b["b"]]
                self.hit(t, "clack", s.note(b["b"] + 2, 1), 0.3, bx, by)
                self.fx(t + 0.05, "whoosh", 0.35, 0.2, bx, by)
        for g in self.ghosts:
            if self.crossed(g["take"]):
                self.fx(t, "rustle", 0.5, 0.25, g["take"] * 0 + self.pole_x[0], self.pole_y)
            if self.crossed(g["hang"]):
                sx, sy = H.ghost_spots[g["q"]]
                self.hit(t, "bloop", s.note(g["q"] + 1, 0), 0.35, sx, sy)
                self.say(t + 0.3, "lantern", "hum", sx, sy, 0.3)
        for q, ht in enumerate(self.hook_t):
            if self.crossed(ht):
                hx, hy = H.hooks[-1 - q]
                self.hit(t, "clack", s.note(q, 1), 0.3, hx, hy)
        if self.crossed(T["lights_on"]):
            for q in range(12):
                self.hit(t + 0.2 + q * 0.11, "chime", TUNE_HALLOWEEN[q % 8], 0.28, H.p0 + q * 66, H.py + 60)
            for q, kind in enumerate(("springs", "wheels", "teeth", "digger", "tentacles", "lantern")):
                self.say(t + 1.6 + q * 0.2, kind, "cheer", H.tx, H.py, 0.45)
        for i in range(3):
            if self.crossed(T["animals"] + i * 1.6 + 0.5):
                self.fx(t, "rustle", 1.2, 0.2, 400, G)
        if self.crossed(T["pull"] + 2.0):
            for q, n in enumerate((57, 64, 69, 72)):
                self.hit(t + q * 0.5, "soft_bell", n, 0.35, H.tx, H.py)

    # ------------------------------------------------------------------ drawing

    def draw(self, c, t):
        s, T, H, G = self.s, self.T, self.house, self.G
        self.backdrop(c, t)
        for j, x in enumerate((-400, 120, 2700, 3150, 3600, 4100)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        H.draw_tree(c, s)
        on = smoothstep(seg(t, T["lights_on"], T["lights_on"] + 1.5))
        H.draw_house(c, s, t, windows=on, lanterns=1.0)
        self._hanging(c, t, on)
        self._string(c, t)
        # the pole on its stakes, with whatever is still hanging on it
        self._pole(c, t)
        # wagon + the jack-o'-lanterns still in it
        inwagon = [g["slot"] for g in self.ground if t < g["pick"] + 0.4] + \
                  [d["slot"] for d in self.deck if t < d["pick"] + 0.3]
        draw_wagon(c, s, self.wagon_x, G, [(k, 1.0) for k in sorted(inwagon)], t)
        # deck pumpkins (sit on the planks in front of the house)
        for d in self.deck:
            if t >= d["set"]:
                drop = smoothstep(seg(t, d["set"], d["set"] + 0.25))
                D.pumpkin(c, d["x"], lerp(H.py - 30, H.py, drop), 38, paint=1.0, ribs=1.0, stem=1.0, carve=1.0, lit=1.0,
                          t=t, glow=s.glow, seed=d["slot"], face=d["slot"] % 2)
        self.draw_monsters(c, t, before=self._carried)
        # ground row in front of the tree
        for g in self.ground:
            p = self.ground_state(g, t)
            if p is not None:
                D.pumpkin(c, p[0], p[1], 40, paint=1.0, ribs=1.0, stem=1.0, carve=1.0, lit=1.0, t=t, glow=s.glow,
                          seed=g["slot"] * 1.3, face=g["slot"] % 2)
        self._animals(c, t)

    def _pole(self, c, t):
        T, G = self.T, self.G
        (x0, x1), y = self.pole_x, self.pole_y
        lower = smoothstep(seg(t, T["pole_down"] - 0.8, T["pole_down"]))
        yy = lerp(G - 300 + 6 * math.sin(t * 6), y, lower)
        for k, (st, sx) in enumerate(((T["stake1"], x1), (T["stake2"], x0))):
            h = smoothstep(seg(t, st - 0.2, st + 0.9))
            if t >= st - 0.4:                                # forked stake, driven in by Digs
                c.line(sx, G + 10 - 30 * (1 - h), sx, y + 4, POLE * 0.9, 9)
                c.line(sx, y + 4, sx - 16, y - 18, POLE * 0.9, 7)
                c.line(sx, y + 4, sx + 16, y - 18, POLE * 0.9, 7)
        items = list(POLE_ITEMS)
        for b in self.bats:
            if t >= b["take"] + 0.4:
                items[b["item"]] = None
        for g in self.ghosts:
            if t >= g["take"]:
                items[g["item"]] = None
        draw_pole(c, self.s, x0, yy, x1, yy, items, t, sway=0.25 * (1 - lower) + 0.04)

    def _hanging(self, c, t, on):
        """Bats on the high branches, ghosts at the branch tips: hung on threads, swinging under real gravity."""
        s, H = self.s, self.house
        for b in self.bats:
            if t < b["hang"]:
                continue
            bx, by = H.bat_spots[b["b"]]
            L = 70.0
            a = swing(t, b["hang"], L, 0.45, 3.0) + 0.04 * math.sin(t * 1.1 + b["b"])
            ex, ey = bx + math.sin(a) * L, by + math.cos(a) * L
            c.line(bx, by, ex, ey, CABLE, 2)
            flap = 0.6 * math.exp(-(t - b["hang"]) * 0.8) * math.sin((t - b["hang"]) * 12) + 0.12 * math.sin(t * 2 + b["b"])
            D.bat(c, ex, ey + 28, 0.8, flap=flap, t=t, glow=s.glow)
        for g in self.ghosts:
            if t < g["hang"]:
                continue
            sx, sy = H.ghost_spots[g["q"]]
            L = 60.0
            a = swing(t, g["hang"], L, 0.3, 3.5) + 0.06 * math.sin(t * 0.9 + g["q"])
            ex, ey = sx + math.sin(a) * L, sy + math.cos(a) * L
            c.line(sx, sy, ex, ey, CABLE, 2)
            D.ghost(c, ex, ey, 0.66, drape=1.0, eyes=1.0, t=t, seed=g["q"], sway=a * 2, ball=False)
            k = 0.14 + 0.2 * on
            s.glow_draw(lambda gg, ex=ex, ey=ey, k=k: gg.circle(ex, ey + 45, 55, GHOST_GLOW * k))

    def _string(self, c, t):
        """The light string under the deck: hooked on right to left, then switched on."""
        T, H = self.T, self.house
        n = sum(1 for ht in self.hook_t if t >= ht)
        if n == 0:
            return
        hooks = list(reversed(H.hooks))[:n]
        hooks = list(reversed(hooks))
        hn = self.m("tentacles")
        if n < len(H.hooks) and hn is not None and self.reach.get("tentacles"):
            hooks = [self.reach["tentacles"][0]] + hooks
        if len(hooks) < 2:
            return
        nb = max(1, round(12 * (len(hooks) - 1) / (len(H.hooks) - 1)))
        on = [smoothstep(seg(t, T["lights_on"] + 0.2 + q * 0.11, T["lights_on"] + 0.4 + q * 0.11)) for q in range(nb)]
        D.light_string(c, hooks, nb, 12, glow=self.s.glow, t=t, sag=0.12, bulbs_on=on)

    def _carried(self, kind):
        c, t, s = self.wcv_, self.t_, self.s
        m = self.m(kind)
        if m is None:
            return
        dy = self.poses.get(kind, (0.0, 0.0))[0]
        if kind == "springs":
            what = self.carrying_springs(t)
            if what is None:
                return
            top = m.y + dy - 330 * m.k
            if what[0] == "pumpkins":
                for q, sl in enumerate(what[1]):
                    D.pumpkin(c, m.x - 40 + 80 * q if len(what[1]) > 1 else m.x, top, 36, paint=1.0, ribs=1.0, stem=1.0,
                              carve=1.0, lit=1.0, t=t, glow=s.glow, seed=sl, face=sl % 2)
            else:
                for q, b in enumerate(what[1]):
                    D.bat(c, m.x - 50 + 50 * q, top - 30, 0.42, flap=0.3 * math.sin(t * 8 + q), t=t, glow=s.glow)
            for sxp in (-1, 1):
                c.line(m.x + sxp * 50 * m.k, m.y + dy - 190 * m.k, m.x + sxp * 40, top + 4, m.color * 0.8, 10 * m.k)
        elif kind == "lantern":
            if t < self.hand_over:
                draw_string_coil(c, m.x, m.y - (260 - 82) * m.k + 70, 1.0, t, s)
            for g in self.ghosts:
                if g["take"] <= t < g["hang"]:
                    D.ghost(c, m.x, m.y - (260 - 82) * m.k + 50, 0.62, drape=1.0, eyes=1.0, t=t, seed=g["q"], ball=False)
        elif kind == "tentacles":
            if self.hand_over <= t < self.T["hook0"] - 0.6 and self.reach.get("tentacles"):
                if t < self.T["climb"]:
                    hx, hy = self.reach["tentacles"][0]
                    draw_string_coil(c, hx, hy - 10, 0.0, t, s)

    def _animals(self, c, t):
        T = self.T
        if t < T["animals"]:
            return
        for i in range(3):
            x, hop = self.animal_pos(i, t)
            if i < 2:
                bunny(c, x, self.G, 1.0 - 0.15 * i, hop=hop, face=1)
            else:
                hedgehog(c, x, self.G, 1.0, face=1, t=t)

    def draw_monsters(self, c, t, kinds=None, before=None):
        self.wcv_, self.t_ = c, t
        super().draw_monsters(c, t, kinds, before)


def _ease_keys(keys, t):
    """Camera keyframes [(t, x, y, zoom)], eased between them."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t < t1:
            u = smootherstep((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return tuple(lerp(p, q, u) for p, q in zip(a, b))
    return keys[-1][1:]
