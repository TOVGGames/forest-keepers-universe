"""Forest Keepers episode 9: The Big Tune-Up (docs/engines/forest_keepers_tune_up.md). The new look comes on.

  TRIP  - a calm night in the village, the name tags first. Hans says hello to a bunny, and his face-tentacle beard
          wiggles: the bunny hops away behind a bush. Twigs grins at the hedgehog with all his sharp teeth: it curls
          up into a ball. Glo has an idea (an orb in his bubble): back to the factory. They walk to the hill door
          and go in, Hans last.
  HALL  - the factory hall from episodes 1-2. They walk in, Glo lighting the way, and each steps up onto a pallet of
          the old assembly line. The orb trolley on the ceiling rail lifts the orbs out one by one (Hans first, Glo
          last): each Keeper drains to pale grey wood and falls asleep; the others wave goodbye. The orbs ride along
          the rail in the trolley's rack while the line carries the sleepers through four stations, one step at a
          time: UNCLIP (the arm takes off every pinned badge, Hans' beard and Twigs' sharp mouth, into the bin),
          FIT (new pieces from the tray: Hans' smile, Twigs' grin and brow; the others get their bolts checked),
          SAND and POLISH. At the end the trolley drops the orbs back in, Glo first: each orb flashes the Forest
          Keeper badge and the colour floods back. Hans wakes last and smiles for the first time. A polished steel
          mirror on the way out: Hans sees his smile, Twigs his grin. Out through the door.
  HOME  - back in the village: the hedgehog uncurls for Twigs' new grin, the bunny comes out from behind the bush to
          Hans, the orbs flash the badge as they get back to work.
Nothing about a Keeper changes while it's awake, and nothing changes by itself: a machine visibly does every step,
carried pieces stay in their layer the whole way (owner after FK0005: the right layer in motion).
"""
import math

import numpy as np

from families.foundry.keepers.common import Jump, ellipse, lerp, rect, seg, smoothstep, smootherstep, tree, \
    bunny, hedgehog, machine_block, saw_blade
from families.foundry.keepers.forest import _firefly
from families.foundry.keepers.halloween import Hill, hops, path
from families.foundry.products.monster import (HAT, LEAF, ORB, PUPIL, TOOTH, Xform, beard, fang_mouth, lighten,
                                               smile_mouth)
from families.foundry.style import CABLE, FAR, FLOOR, IRON, MID, STEEL
from families.foundry.tree_monsters import HAZARD, INTERIOR, LAMP, SAWDUST, SIGN_GREEN, SIGN_WARM, LEAF as TREE_LEAF

from . import props as PR
from .animal_houses import G
from .doorway import DEPTH_T, DOOR_W, Doorway, depth_in, depth_out, half_width
from .harvest_feast import FeastAct, cam_keys, px

ORDER = ["lantern", "wheels", "springs", "digger", "teeth", "tentacles"]   # front of the line first
GLO_UP = 60.0                                   # Glo floats this high when awake
WALK = 175.0                                    # walking speed (px/s)
BUSH = (4010.0, 125.0)                          # the bush right of the bunny's house (the bunny hides behind it)
BUNNY0 = 3790.0                                 # where the bunny sits nibbling
HOG = 3300.0                                    # the hedgehog, right of its house
HILL_X = 4300.0                                 # the hill the factory is built into (door at HILL_X + 120..420)
FLASH_EVERY = 20.0                              # the orbs flash the job badge about this often while they work
STEEL_GLASS = np.array([132, 146, 166], np.float64)
BIN = np.array([64, 70, 66], np.float64)
PAD = np.array([214, 196, 160], np.float64)    # sanding pads
FLEECE = np.array([236, 228, 210], np.float64)  # the buffing wheel
STAR = np.array([255, 244, 214], np.float64)


def bump(t, t0, d):
    """0 -> 1 -> 0 over d seconds from t0."""
    u = (t - t0) / d
    return math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0


def work_flash(kind, t, since):
    """The orb's badge flash while a Keeper works: about every FLASH_EVERY s, each on its own timer."""
    if t < since:
        return 0.0
    ph = (t - since + 3.3 * (ORDER.index(kind) if kind in ORDER else 6)) % FLASH_EVERY
    return bump(ph, 0.0, 1.1)


class Route:
    """A Keeper's walk as legs at a steady pace: speeds up over `ramp` s, walks at v, slows down over `ramp` s
    (eased keys would rush the middle of a long walk; owner: slow on purpose)."""

    def __init__(self, x0, t0=0.0):
        self.legs, self.x, self.t, self.x0 = [], x0, t0, x0

    def wait(self, t):
        self.t = max(self.t, t)
        return self

    def go(self, x1, v=WALK, ramp=0.7):
        L = abs(x1 - self.x)
        if L >= 1.0:
            T = L / v + ramp
            self.legs.append((self.t, T, self.x, x1, min(ramp / T, 0.5)))
            self.t += T
        self.x = x1
        return self

    def at(self, t):
        x = self.x0
        for ts, T, a, b, r in self.legs:
            if t < ts:
                return a
            u = (t - ts) / T
            if u >= 1.0:
                x = b
                continue
            if u < r:
                f = u * u / (2 * r)
            elif u < 1 - r:
                f = r / 2 + (u - r)
            else:
                f = (1 - r) - (1 - u) ** 2 / (2 * r)
            return lerp(a, b, f / (1 - r))
        return x


def draw_pin(c, bx, by, k):
    """The old pinned leaf badge (episodes 2-8), anywhere (the arm carries it to the bin)."""
    s = k
    leaf = [(bx, by - 22 * s), (bx + 13 * s, by - 4 * s), (bx, by + 18 * s), (bx - 13 * s, by - 4 * s)]
    c.circle(bx, by, 24 * s, np.array([40, 34, 20]))
    c.circle(bx, by, 21 * s, HAT)
    c.polygon(leaf, LEAF)
    c.line(bx, by - 18 * s, bx, by + 14 * s, np.array([40, 110, 60]), 2.5 * s)


def orb_r(m):
    return {"wheels": 18, "tentacles": 17, "teeth": 16, "springs": 15, "lantern": 15, "digger": 16}[m.kind] * m.k


def loose_orb(c, s, x, y, r, glow=1.0):
    """An orb out of its socket (in the gripper or the rack): blue, a glint, a soft glow."""
    c.circle(x, y, r, ORB)
    c.circle(x - r * 0.3, y - r * 0.3, r * 0.28, lighten(ORB, 1.6))
    if glow > 0:
        s.glow_draw(lambda g: g.circle(x, y, r * 1.5, ORB * 0.7 * glow))


def keep_inside(c, pts, draw, tint=None, mix=0.0):
    """draw(), then put back what was there before OUTSIDE the polygon pts (world units): the drawing only shows
    inside it (the mirror's glass). `tint` is blended over the inside at `mix`."""
    import cv2
    img = c.target
    before = img.copy()
    draw()
    mask = np.zeros(img.shape[:2], np.uint8)
    c.target = mask
    try:
        c.polygon(pts, (255, 255, 255))
    finally:
        c.target = img
    a = mask[..., None].astype(np.float32) / 255.0
    if tint is not None and mix > 0:
        img[:] = (img * (1 - a * mix) + np.asarray(tint, np.float32)[None, None, :] * a * mix + 0.5).astype(np.uint8)
    img[:] = (img * a + before * (1 - a) + 0.5).astype(np.uint8)
    del cv2


def curled_hog(c, x, y, s, face, u, t):
    """The hedgehog, curled into a spiky ball by `u` (0 = walking about, 1 = a ball)."""
    if u < 0.5:
        sq = 1 - 0.5 * u
        hedgehog(Xform(c, 0, 0, 0.0, 1.0, x, y) if sq == 1 else _squash(c, x, y, sq), x, y, s, face, t)
        return
    v = (u - 0.5) / 0.5
    r = 24 * s * (0.85 + 0.15 * v)
    cy = y - r
    pts = []
    for i in range(36):                                   # a ball of spines, the nose tucked in at the bottom
        a = i * 2 * math.pi / 36
        rr = r * (1.32 if i % 2 else 1.02)
        pts.append((x + math.cos(a) * rr, cy + math.sin(a) * rr))
    c.polygon(pts, np.array([74, 56, 44]))
    c.polygon(ellipse(x, cy, r * 1.0, r * 0.96, 28), np.array([104, 82, 62]))
    for i in range(14):
        a = i * 2 * math.pi / 14 + 0.2
        c.circle(x + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.58, 2.2 * s, np.array([80, 62, 48]))
    c.polygon(ellipse(x + face * r * 0.55, y - r * 0.32, r * 0.32, r * 0.22, 14), np.array([170, 140, 110]))
    c.circle(x + face * r * 0.8, y - r * 0.32, 3.0 * s, np.array([60, 40, 40]))


class _squash:
    """Canvas wrapper that squashes y towards the ground line (the hedgehog tucking in)."""

    def __init__(self, cv, x, y, sy):
        self.__dict__.update(_cv=cv, _y=y, _sy=sy)

    def __getattr__(self, k):
        return getattr(self._cv, k)

    def _p(self, x, y):
        return x, self._y + (y - self._y) * self._sy

    def polygon(self, pts, col):
        self._cv.polygon([self._p(*p) for p in pts], col)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        self._cv.circle(*self._p(x, y), r, col, fill, width)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self._cv.line(*self._p(x0, y0), *self._p(x1, y1), col, width)


# ====================================================================== shared

class TuneAct(FeastAct):
    """An act of the Tune-Up. All six Keepers use the new look's drawing (Monster.newlook); before the factory the
    old pieces are still on (pin = the badge, old = Hans' beard / Twigs' sharp mouth and old eye)."""

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        for m in scene.monsters:
            m.newlook = True

    @property
    def quiet(self):
        """Sleeping Keepers don't talk, nor do the ones out of sight (in the tunnel, behind a wall)."""
        return [m.kind for m in self.s.monsters if m.alive < 0.99 or self.hidden(m)]

    def hidden(self, m):
        return self.door_depth.get(m.kind, 0.0) > 0.85

    @property
    def door_depth(self):
        return self.__dict__.setdefault("_depth", {})

    def outside(self):
        """The Keepers not in a doorway (drawn in front of the walls)."""
        return [m.kind for m in self.s.monsters if self.door_depth.get(m.kind, 0.0) <= 0.0]

    def walls(self, t):
        """x-ranges of solid things drawn in FRONT of the walkway (no Keeper may overlap one: scene check)."""
        return []

    def old_look(self, m):
        m.pin, m.flash = 1.0, 0.0
        m.old = {"tentacles": {"beard"}, "teeth": {"mouth", "eye"}}.get(m.kind, set())
        m.hide, m.brow_on = set(), (0.0 if m.kind == "teeth" else 1.0)
        m.smile, m.lid_top, m.cheek, m.brow = 0.6, 0.0, 0.0, 0.0

    def new_look(self, m, flash=0.0, smile=0.6):
        m.pin, m.flash, m.old, m.hide, m.brow_on = 0.0, flash, set(), set(), 1.0
        m.smile = smile

    def aside_moods(self, t):
        return ["mm", "hehe", "ooh", "aww"]


class VillageAct(TuneAct):
    """The village from episodes 4-8 and the hill door to the factory."""

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.hill = Hill(HILL_X, G, door_w=DOOR_W, walk_in=True)
        self.doorway = Doorway(self.hill.d0, self.hill.d1, G, self.hill.door_h)
        self.x_in = self.doorway.xc

    def bush(self, c):
        x, r = BUSH
        c.circle(x - 40, G - r * 0.45, r * 0.8, TREE_LEAF[1] * 0.7)
        c.circle(x + 50, G - r * 0.5, r * 0.75, TREE_LEAF[1] * 0.78)
        c.circle(x, G - r * 0.62, r, TREE_LEAF[1] * 0.75)

    def scene_draw(self, c, t, door, bunny_st, hog_st):
        s = self.s
        self.backdrop(c, t)
        for j, x in enumerate((-300, 300, 3900)):
            if s.visible(x - 260, x + 260):
                tree(c, x, G, 640 + 60 * (j % 3), 950 + j)
        self.hill.back(c, s, t, door)
        bx, hop, face = bunny_st
        if s.visible(bx - 80, bx + 80):
            bunny(c, bx, G, 1.5, hop, face)
        self.bush(c)
        self.draw_village(c, t, peek=1.0)
        hx, face, curl = hog_st
        if s.visible(hx - 80, hx + 80):
            curled_hog(c, hx, G, 1.45, face, curl, t)
        self.glo_light(c, k=0.8)
        self.doorway.draw_inside(self, c, t, self.door_depth)
        self.hill.front(c, s, t, door)
        self.draw_monsters(c, t, kinds=self.outside())

    def fireflies(self):
        s = self.s
        if s.particles.rng.uniform() < 0.2:
            s.particles.items.append(_firefly(s.particles.rng, 2900, G - 560, G))


# ====================================================================== TRIP: the village -> the factory door

class TripAct(VillageAct):
    name = "trip"
    LEAD = 8.0                                     # (owner) the name tags first, then the bunny
    names = (0.8 - LEAD, 7.0 - LEAD)
    START = {"lantern": 2150.0, "digger": 2350.0, "wheels": 2550.0, "springs": 2750.0, "teeth": 2950.0,
             "tentacles": 3150.0}
    IN_ORDER = ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"]   # front first: nobody passes

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.hans_to, self.twigs_to, self.glo_to = 3570.0, 3170.0, 3000.0
        self.go = 20.5
        self.wait = {k: 4440.0 - 170 * q for q, k in enumerate(self.IN_ORDER)}
        here = dict(self.START, tentacles=self.hans_to, teeth=self.twigs_to, lantern=self.glo_to)
        self.leave = {k: self.go + 0.3 * q for q, k in enumerate(self.IN_ORDER)}
        self.here = here
        self.route = {}
        for k in self.IN_ORDER:
            r = Route(self.START[k], -self.LEAD)
            if k == "tentacles":
                r.wait(0.0).go(self.hans_to, v=120)
            elif k == "teeth":
                r.wait(8.0).go(self.twigs_to, v=110)
            elif k == "lantern":
                r.wait(14.0).go(self.glo_to, v=210)
            r.wait(self.leave[k]).go(self.wait[k], v=WALK)
            self.route[k] = r
        self.arrive = {k: self.route[k].t for k in self.IN_ORDER}
        self.door = (self.arrive["lantern"] - 2.5, self.arrive["lantern"] + 0.5)
        self.enter, self.at_door, last, last_door = {}, {}, self.door[1], -1e9
        for k in self.IN_ORDER:
            walk = Route(self.wait[k]).go(self.x_in, v=170).t        # time from the queue to the doorstep
            last = self.enter[k] = max(last + 1.0, self.arrive[k] + 0.5, last_door + 2.4 - walk)
            self.route[k].wait(self.enter[k]).go(self.x_in, v=170)
            last_door = self.at_door[k] = self.route[k].t
        self.inside = {k: self.at_door[k] + DEPTH_T for k in self.IN_ORDER}
        self.dur = max(self.inside.values()) + 1.5

    # ----- the animals -----

    def bunny_st(self, t):
        h0, n, d = 5.2, 3, 0.48
        if t < h0:
            return BUNNY0, 3 * max(0.0, math.sin(t * 2.3)) ** 8, -1             # nibbling, a little twitch
        u = (t - h0) / (n * d)
        if u >= 1:
            return BUSH[0] + 10, 0.0, 1
        k_, ph = int(u * n), u * n - int(u * n)
        return lerp(BUNNY0, BUSH[0] + 10, (k_ + ph) / n), 4 * 34 * ph * (1 - ph), 1

    def hog_st(self, t):
        return HOG, -1, smoothstep(seg(t, 11.4, 12.0))

    def props(self, t):
        bx, hop, _ = self.bunny_st(t)
        return {"bunny": (bx, G - hop)}

    # ----- camera -----

    def target(self, t):
        g, a = self.go, self.arrive
        keys = [(-self.LEAD, 2700.0, None, 0.85), (-3.0, 2700.0, None, 0.85), (5.0, 3610.0, None, 1.35),
                (7.6, 3610.0, None, 1.35), (10.6, 3300.0, None, 1.35), (13.6, 3300.0, None, 1.35),
                (17.5, 3150.0, None, 1.0), (g, 3200.0, None, 0.95), (a["wheels"], 3900.0, None, 0.95),
                (self.enter["springs"], 4250.0, None, 1.0), (self.dur, 4400.0, None, 1.0)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        for q, kind in enumerate(self.IN_ORDER):
            m = self.m(kind)
            if m is None:
                continue
            here = self.here[kind]
            dy, y = 0.0, (G - GLO_UP if kind == "lantern" else G)
            u = depth_in(t, self.at_door[kind]) if t > self.at_door[kind] else 0.0
            self.door_depth[kind] = u
            if u > 0.0:                                   # in through the door, away from the camera
                if kind == "springs":
                    ph = ((t - self.at_door[kind]) / 0.55) % 1.0
                    dy, m.spring = -4 * 40 * ph * (1 - ph), 0.0
                self.doorway.walking(self, m, t, dt, u, y, dy)
                self.old_look(m)
                continue
            if kind == "springs":
                x, lift, sq = hops(here, self.wait[kind], self.leave[kind], self.arrive[kind], t, apex=55, step=170)
                if t >= self.enter[kind]:
                    x, lift, sq = hops(self.wait[kind], self.x_in, self.enter[kind], self.at_door[kind], t, apex=50,
                                       step=170)
                if t < self.leave[kind]:
                    x = here
                dy, m.spring = -lift, sq
            else:
                x = self.route[kind].at(t)
            if kind == "tentacles":
                dy += 5.0 * smoothstep(seg(t, 6.8, 7.6)) * (1 - smoothstep(seg(t, 18.0, 19.0)))   # a little slump
                if 3.6 <= t < 6.7 and x > self.hans_to - 5:     # waves hello to the bunny with one tentacle
                    hx, hy = x + 40, G - 300 * m.k
                    tx, ty = BUNNY0 - 70 + 14 * math.sin(t * 6), G - 90 + 10 * math.cos(t * 6)
                    u = smoothstep(seg(t, 3.6, 4.5)) * (1 - smoothstep(seg(t, 5.9, 6.7)))
                    self.reach["tentacles"] = [(lerp(hx, tx, u), lerp(hy, ty, u))]
            self.place(m, x, t, dt, y=y, dy=dy)
            self.old_look(m)
        self.fireflies()
        self._sounds(t)

    def aside_moods(self, t):
        return [] if t < self.go + 1.0 else ["mm", "ooh", "hm"]

    def _sounds(self, t):
        if self.crossed(3.7):
            self.chat(3.7, "tentacles", "hey")
        if self.crossed(5.2):
            self.hit(5.2, "pluck", 72, 0.12, BUNNY0, G)
            for q in range(3):
                self.hit(5.2 + 0.48 * (q + 1), "thud", 50, 0.08, BUNNY0, G)
        if self.crossed(6.9):
            self.chat(6.9, "tentacles", "uhoh", icon=None)
        if self.crossed(10.9):
            self.chat(10.9, "teeth", "hehe")
        if self.crossed(11.45):
            self.hit(11.45, "pluck", 67, 0.12, HOG, G)
        if self.crossed(12.6):
            self.chat(12.6, "teeth", "uhoh", icon=None)
        if self.crossed(15.0):
            self.chat(15.0, "tentacles", "hm")
        if self.crossed(18.6):
            self.chat(18.6, "lantern", "idea", icon="orb")
        if self.crossed(19.5):
            self.chorus(19.5, ["wheels", "springs", "digger"], "yay", gap=0.25)
        if self.crossed(self.door[0]):
            self.fx(self.door[0], "motor", self.door[1] - self.door[0], 0.4, self.hill.d0, G - 300)
        if self.crossed(self.door[1]):
            self.hit(self.door[1], "clunk", 45, 0.35, self.hill.d0, G - 500)
        for kind in self.IN_ORDER:
            if self.crossed(self.enter[kind] + 0.3):
                self.chat(self.enter[kind] + 0.3, kind, "wee" if kind == "springs" else "mm", icon=None)

    def draw(self, c, t):
        door = seg(t, *self.door)
        self.scene_draw(c, t, door, self.bunny_st(t), self.hog_st(t))


# ====================================================================== HALL: orbs out, the line, orbs in

PY = G - 40.0                                   # pallet top: feet on the line
FY = G + 60.0                                   # the walkway in front of the line
X0, D = 900.0, 420.0                            # the line: slot p sits at X0 + p * D
STATIONS = ["UNCLIP", "FIT", "SAND", "POLISH"]  # slots 6..9; the queue is 0..5, the end dock 10..15
RAIL_Y = G - 780.0                              # the orb trolley's rail
BEAM_Y = G - 640.0                              # the stations' crossbeams (their tools hang from them)
MIRROR = (7900.0, 8480.0)                       # the polished steel mirror (stands on the walkway)
EXIT = (9600.0 - DOOR_W, 9600.0)                # the way out (a roll-up door in the back wall)
ENTRY = (100.0, 100.0 + DOOR_W)                 # the way in from the tunnel (an opening in the back wall)
HALL = (-400.0, 10200.0)


def slot_x(p):
    return X0 + p * D


class HallAct(TuneAct):
    name = "hall"
    indoor = True
    names = (-9.0, -8.0)
    M, W = 3.4, 9.0                              # line: move one slot, then every station works
    OUT, IN = 8.0, 7.5                           # one orb out / in

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.slot0 = {k: 5 - j for j, k in enumerate(ORDER)}
        self.way_in = Doorway(ENTRY[0], ENTRY[1], FY, FY - (G - 520), rise=130.0)
        self.way_out = Doorway(EXIT[0], EXIT[1], FY, FY - (G - 520), rise=130.0)
        self.in_door = {k: 1.0 + 1.8 * j for j, k in enumerate(ORDER)}           # starts coming out of the tunnel
        self.in_route = {k: Route(self.way_in.xc, self.in_door[k] + DEPTH_T).go(slot_x(self.slot0[k]), v=160)
                         for k in ORDER}
        self.on_slot = {k: self.in_route[k].t for k in ORDER}
        self.hop_up = {k: self.on_slot[k] + 0.4 for k in ORDER}
        self.settle = max(self.hop_up.values()) + 0.8
        self.O0 = self.settle + 8.5
        self.out_order = list(reversed(ORDER))                 # Hans first ... Glo last
        self.out_t = {k: self.O0 + i * self.OUT for i, k in enumerate(self.out_order)}
        self.L0 = self.O0 + 6 * self.OUT + 1.0
        self.LE = self.L0 + 10 * self.M + 9 * self.W
        self.I0 = self.LE + 1.0
        self.in_t = {k: self.I0 + q * self.IN for q, k in enumerate(ORDER)}   # Glo first ... Hans last
        self.HANS = 6.0                                        # Hans' wake-up gets longer
        self.down_t = {k: self.in_t[k] + 6.6 for k in ORDER}
        self.down_t["tentacles"] += self.HANS - 1.0
        self.ME = self.in_t["tentacles"] + self.IN + self.HANS + 1.0      # everyone heads for the way out
        self.mirror_spot = MIRROR[0] - 200.0
        self.queue_x = {"lantern": 9150.0, "wheels": 8990.0, "springs": 8830.0, "digger": 8670.0,
                        "teeth": 8510.0, "tentacles": 8350.0}
        self.exit_order = ["lantern", "wheels", "springs", "digger", "teeth", "tentacles"]
        x0 = {k: slot_x(15 - ORDER.index(k)) + 30 for k in ORDER}
        R = {k: Route(x0[k], 0.0).wait(self.ME + 0.25 * ORDER.index(k)) for k in ORDER}
        R["tentacles"].go(self.mirror_spot, v=115)
        self.hans_at_mirror = hm = R["tentacles"].t
        R["teeth"].go(self.mirror_spot - 250, v=110)
        R["tentacles"].wait(hm + 5.0).go(self.queue_x["tentacles"], v=130)
        R["teeth"].wait(hm + 6.0).go(self.mirror_spot, v=110)
        self.twigs_at_mirror = tm = R["teeth"].t
        R["teeth"].wait(tm + 3.4).go(self.queue_x["teeth"], v=130)
        for k in ("lantern", "wheels", "springs", "digger"):
            R[k].go(self.queue_x[k], v=130)
        self.door = (tm + 1.0, tm + 4.0)
        self.exit_t, self.at_exit, last, last_door = {}, {}, self.door[1], -1e9
        for k in self.exit_order:
            walk = Route(self.queue_x[k]).go(self.way_out.xc, v=170).t
            last = self.exit_t[k] = max(last + 1.1, R[k].t + 0.5, last_door + 2.4 - walk)
            R[k].wait(last).go(self.way_out.xc, v=170)
            last_door = self.at_exit[k] = R[k].t
        self.out_route = R
        self.gone = {k: self.at_exit[k] + DEPTH_T for k in ORDER}
        self.dur = max(self.gone.values()) + 1.5
        self._trolley_keys()
        self._orb_at = {}
        self.lamps = list(np.arange(HALL[0] + 350, HALL[1], 700))
        self.stats = {"orbs_out": 6, "orbs_in": 6, "stations": STATIONS}

    # ----- timing -----

    def moves(self, t):
        """How many slots the line has moved (fractional during a move)."""
        if t < self.L0:
            return 0.0
        k = (t - self.L0) / (self.M + self.W)
        c = int(k)
        ph = (t - self.L0) - c * (self.M + self.W)
        if c >= 10:
            return 10.0
        return c + smootherstep(min(1.0, ph / self.M))

    def unit_x(self, kind, t):
        return slot_x(self.slot0[kind] + self.moves(t))

    def work(self, kind, st):
        """Start of `kind`'s work at station st (0..3)."""
        c = ORDER.index(kind) + 1 + st
        return self.L0 + (c - 1) * (self.M + self.W) + self.M

    def station_unit(self, st, t):
        """Who works at station st right now, with the local work time (or None)."""
        if t < self.L0:
            return None
        k = int((t - self.L0) // (self.M + self.W))
        ph = (t - self.L0) - k * (self.M + self.W) - self.M
        j = k - st
        if 0 <= ph < self.W and 0 <= j < 6 and k < 9:
            return ORDER[j], ph
        return None

    def alive(self, kind, t):
        o = self.out_t[kind]
        if t < o + 3.7:
            return 1.0
        i0 = self.in_t[kind]
        if t < i0 + 4.2:
            return 1.0 - smoothstep(seg(t, o + 3.7, o + 5.2))
        return smoothstep(seg(t, i0 + 4.2, i0 + 5.9))

    # ----- the face pieces (what the stations change) -----

    UNCLIP = dict(pin_grab=1.2, pin_drop=3.6, part_grab=5.6, part_drop=7.8)
    FIT = dict(grin_grab=2.2, grin_on=4.6, brow_grab=5.8, brow_on=7.8)

    def look(self, m, t):
        """Set m's pieces for time t: badge pin, old parts, empty slots, Twigs' brow."""
        self.old_look(m)
        u0 = self.work(m.kind, 0)
        if t >= u0 + self.UNCLIP["pin_grab"]:
            m.pin = 0.0
        if m.kind in ("tentacles", "teeth"):
            slot = "beard" if m.kind == "tentacles" else "mouth"
            f0 = self.work(m.kind, 1)
            if t >= u0 + self.UNCLIP["part_grab"]:
                m.old.discard(slot)
                m.hide.add(slot)
            if t >= f0 + self.FIT["grin_on"]:
                m.hide.discard(slot)
            if m.kind == "teeth" and t >= f0 + self.FIT["brow_on"]:
                m.old.discard("eye")
                m.brow_on = 1.0
        i0 = self.in_t[m.kind]
        m.flash = bump(t, i0 + 3.9, 1.4) + work_flash(m.kind, t, i0 + 12.0)
        if m.kind == "tentacles":
            m.smile = 0.6 if t < i0 + 8.5 else lerp(0.6, 0.9, smoothstep(seg(t, i0 + 8.5, i0 + 9.7)))
            m.smile = min(m.smile, 0.25 + 0.65 * smoothstep(seg(t, i0 + 6.6, i0 + 8.3)))
            if t >= self.hans_at_mirror + 1.0:
                m.smile = lerp(0.9, 1.0, smoothstep(seg(t, self.hans_at_mirror + 1.0, self.hans_at_mirror + 2.0)))
                m.cheek = 0.3 * smoothstep(seg(t, self.hans_at_mirror + 1.0, self.hans_at_mirror + 2.0)) * \
                    (1 - smoothstep(seg(t, self.hans_at_mirror + 5.0, self.hans_at_mirror + 6.0)))
        if m.kind == "teeth" and self.twigs_at_mirror + 0.8 <= t:
            m.smile = lerp(0.6, 0.95, smoothstep(seg(t, self.twigs_at_mirror + 0.8, self.twigs_at_mirror + 1.6)))

    # ----- the orb trolley -----

    def _trolley_keys(self):
        keys = [(0.0, slot_x(-0.6)), (self.O0, slot_x(-0.6))]
        for i, k in enumerate(self.out_order):
            o = self.out_t[k]
            keys += [(o, keys[-1][1]), (o + 1.8, slot_x(i))]
        keys += [(self.L0 + 5.0, slot_x(5)), (self.L0 + 105.0, slot_x(15))]
        for q, k in enumerate(ORDER):
            i0 = self.in_t[k]
            keys += [(i0, keys[-1][1]), (i0 + 1.6, slot_x(15 - q))]
        self.tkeys = keys

    def trolley_x(self, t):
        return px(self.tkeys, t)

    def cup(self, q):
        return (q - 2.5) * 36.0

    def gripper(self, t):
        """(x, y, holding kind or None) of the trolley's gripper; the cups hold the other orbs (rack())."""
        tx = self.trolley_x(t)
        top = RAIL_Y + 66
        for k in self.out_order:
            o = self.out_t[k]
            if o + 1.8 <= t < o + 7.0:
                ox, oy = self.grab_xy(k, t)
                if t < o + 3.3:
                    u = smootherstep(seg(t, o + 1.8, o + 3.3))
                    return tx, lerp(top, oy, u), None
                if t < o + 3.7:
                    return tx, oy, None
                if t < o + 5.5:
                    return tx, lerp(oy, top, smootherstep(seg(t, o + 3.7, o + 5.5))), k
                cx = tx + self.cup(ORDER.index(k))
                if t < o + 6.3:
                    return lerp(tx, cx, smootherstep(seg(t, o + 5.5, o + 6.3))), top, k
                return lerp(cx, tx, smootherstep(seg(t, o + 6.3, o + 7.0))), top, None
        for k in ORDER:
            i0 = self.in_t[k]
            if i0 + 1.6 <= t < i0 + 5.0:
                cx = tx + self.cup(ORDER.index(k))
                if t < i0 + 2.0:
                    return lerp(tx, cx, smootherstep(seg(t, i0 + 1.6, i0 + 2.0))), top, None
                if t < i0 + 2.6:
                    return lerp(cx, tx, smootherstep(seg(t, i0 + 2.1, i0 + 2.6))), top, k
                ox, oy = self.sock_xy(k, t)
                if t < i0 + 3.9:
                    return tx, lerp(top, oy, smootherstep(seg(t, i0 + 2.6, i0 + 3.9))), k
                if t < i0 + 4.1:
                    return tx, oy, None
                return tx, lerp(oy, top, smootherstep(seg(t, i0 + 4.1, i0 + 5.0))), None
        return tx, top, None

    def grab_xy(self, k, t):
        """Where the gripper takes k's orb: the orb in its socket (it bobs while awake) until the grip at o + 3.7,
        then where it was at the grip (act time, the clock the Keepers are drawn with)."""
        if t >= self.out_t[k] + 3.7 and k in self._orb_at:
            return self._orb_at[k]
        return self.m(k).orb_now(t)

    def sock_xy(self, k, t):
        return self.m(k).orb_now(t)

    def in_rack(self, k, t):
        return self.out_t[k] + 6.3 <= t < self.in_t[k] + 2.0

    # ----- camera -----

    def target(self, t):
        k = []
        k.append((0.0, 650.0, None, 0.8))
        k.append((self.on_slot["lantern"], 1950.0, None, 0.8))
        k.append((self.settle, 1950.0, None, 0.8))
        for i, kind in enumerate(self.out_order):
            o = self.out_t[kind]
            k.append((o + 1.0, slot_x(i) + 60, None, 1.02))
            k.append((o + 6.8, slot_x(i) + 60, None, 1.02))
        k.append((self.L0 + 4.0, 3700.0, None, 0.9))
        # the line: the stations; close in on Twigs' and Hans' new faces (UNCLIP and FIT, cycles 5-7)
        w5 = self.work("teeth", 0)
        k.append((w5 - 3.0, 3800.0, None, 0.9))
        k.append((w5 + 1.0, slot_x(6.5), None, 1.42))
        hf = self.work("tentacles", 1)
        k.append((hf + 6.5, slot_x(6.5), None, 1.42))
        k.append((self.LE - 25.0, 4300.0, None, 0.9))
        for q, kind in enumerate(ORDER):
            i0 = self.in_t[kind]
            z = 1.25 if kind == "tentacles" else 1.02
            k.append((i0 + 1.2, slot_x(15 - q) - 40, None, z))
            k.append((i0 + (self.IN + self.HANS if kind == "tentacles" else 6.8), slot_x(15 - q) - 40, None, z))
        k.append((self.hans_at_mirror + 3.0, self.mirror_spot + 300, None, 1.1))
        k.append((self.twigs_at_mirror + 3.0, self.mirror_spot + 300, None, 1.1))
        k.append((self.exit_t["teeth"] + 1.0, 8900.0, None, 0.95))
        k.append((self.dur, 9100.0, None, 0.95))
        k.sort(key=lambda e: e[0])
        x, y, z = cam_keys(k, t)
        # the walk to the mirror: the camera follows Hans at his own pace
        w = smoothstep(seg(t, self.ME, self.ME + 7.0)) * (1 - smoothstep(seg(t, self.hans_at_mirror - 3.0,
                                                                                 self.hans_at_mirror + 1.0)))
        if w > 0:
            fx = self.out_route["tentacles"].at(t) + 300
            x = lerp(x, fx, w)
        return x, y, z

    # ----- the Keepers -----

    def walls(self, t):
        return [(ENTRY[0] - 900, ENTRY[0]), (EXIT[1], EXIT[1] + 900)]

    def name_amount(self, kind, t):
        w = self.in_t[kind] + 4.6
        return smoothstep(seg(t, w, w + 0.6)) * (1 - smoothstep(seg(t, w + 4.0, w + 4.8)))

    def update(self, t, dt):
        self.reach = {}
        for kind in ORDER:
            m = self.m(kind)
            if m is None:
                continue
            a = self.alive(kind, t)
            up = GLO_UP if kind == "lantern" else 0.0
            dy, walk, y = 0.0, None, FY - up
            sx = slot_x(self.slot0[kind])
            u = 0.0
            if t < self.in_door[kind] + DEPTH_T:
                u = depth_out(t, self.in_door[kind]) if t > self.in_door[kind] else 1.0
            elif t > self.at_exit[kind]:
                u = depth_in(t, self.at_exit[kind])
            self.door_depth[kind] = u
            if u > 0.0:                                        # in the tunnel / out into the night
                (self.way_in if t < self.ME else self.way_out).walking(self, m, t, dt, u, FY - up)
                m.alive, m.orb_in = a, 1.0
                if kind == "lantern":
                    m.lamp = a
                self.look(m, t)
                continue
            if t < self.hop_up[kind]:                          # out of the tunnel, along the walkway
                x = self.in_route[kind].at(t)
            elif t < self.down_t[kind]:                         # on the line
                hj = Jump(sx, FY - up, sx, PY - up, apex=40)
                if t < self.hop_up[kind] + hj.dur:
                    x, y = hj.at(t - self.hop_up[kind])
                else:
                    x, y = self.unit_x(kind, t), PY - up
                    if kind == "lantern":                       # asleep, Glo rests on his tendrils on the pallet
                        y = lerp(PY + 39.0, PY - up, a)
            else:
                ex = slot_x(15 - ORDER.index(kind))
                hj = Jump(ex, PY - up, ex + 30, FY - up, apex=30)
                if t < self.down_t[kind] + hj.dur:
                    x, y = hj.at(t - self.down_t[kind])
                else:
                    x = self.out_route[kind].at(t)
            if kind == "springs" and t >= self.ME and t < self.gone[kind]:
                pass
            self.place(m, x, t, dt, y=y, dy=dy, walk=walk)
            m.alive, m.orb_in = a, (0.0 if self.out_t[kind] + 3.7 <= t < self.in_t[kind] + 3.9 else 1.0)
            if kind == "lantern":
                m.lamp = a
            self.look(m, t)
            if a < 1.0:
                m.walk, m.spring = 0.0, 0.0
            if t >= self.out_t[kind] + 3.7 and kind not in self._orb_at:
                self._orb_at[kind] = m.orb_now(t)
        self._particles(t)
        self._sounds(t)

    def aside_moods(self, t):
        if self.O0 - 1 < t < self.L0 or self.I0 - 1 < t < self.ME + 3:
            return []
        return ["mm", "hehe", "ooh", "aww"]

    # ----- what moves (for the warp check) -----

    def props(self, t):
        out = {"trolley": (self.trolley_x(t), RAIL_Y)}
        gx, gy, held = self.gripper(t)
        out["gripper"] = (gx, gy)
        for kind in ORDER:
            if t >= self.L0 - 1:
                out["pallet_" + kind] = (self.unit_x(kind, t), PY)
        for st in range(4):
            su = self.station_unit(st, t)
            if su is not None:
                tool = self.tool_point(st, su[0], su[1])
                if tool is not None:
                    out["tool%d" % st] = tool[:2]
        return out

    # ----- the stations' tools -----

    def bin_xy(self, st):
        return slot_x(6 + st) - 150.0, G + 18.0

    def tray_xy(self, st):
        return slot_x(6 + st) - 165.0, G + 6.0

    def idle_xy(self, st):
        return slot_x(6 + st), BEAM_Y + 90.0

    def tool_point(self, st, kind, u):
        """Where station st's gripper / pad / wheel is at local work time u, and what it carries:
        (x, y, item). item: ("pin"|"part"|"new"|"brow", kind) or None."""
        m = self.m(kind)
        ix, iy = self.idle_xy(st)
        if st == 0:                                            # UNCLIP
            bx, by = m.badge_pos()
            bnx, bny = self.bin_xy(0)
            keys = [(0.0, ix, iy), (1.0, bx, by), (self.UNCLIP["pin_grab"], bx, by), (3.2, bnx, bny - 40),
                    (self.UNCLIP["pin_drop"], bnx, bny - 40)]
            item = ("pin", kind) if self.UNCLIP["pin_grab"] <= u < self.UNCLIP["pin_drop"] else None
            if kind in ("tentacles", "teeth"):
                ax, ay = self.part_xy(m)
                keys += [(5.0, ax, ay), (self.UNCLIP["part_grab"], ax, ay), (7.4, bnx, bny - 40),
                         (self.UNCLIP["part_drop"], bnx, bny - 40), (8.9, ix, iy)]
                if self.UNCLIP["part_grab"] <= u < self.UNCLIP["part_drop"]:
                    item = ("part", kind)
            else:
                keys += [(4.8, ix, iy)]
            x, y, _ = path(keys, u)
            return x, y, item
        if st == 1:                                            # FIT
            if kind in ("tentacles", "teeth"):
                tx, ty = self.tray_xy(1)
                ax, ay = self.part_xy(m, new=True)
                keys = [(0.0, ix, iy), (1.8, tx - 20, ty - 30), (self.FIT["grin_grab"], tx - 20, ty - 30),
                        (4.2, ax, ay), (self.FIT["grin_on"], ax, ay)]
                item = ("new", kind) if self.FIT["grin_grab"] <= u < self.FIT["grin_on"] else None
                if kind == "teeth":
                    rx, ry = self.brow_xy(m)
                    keys += [(5.4, tx + 30, ty - 30), (self.FIT["brow_grab"], tx + 30, ty - 30), (7.4, rx, ry),
                             (self.FIT["brow_on"], rx, ry), (8.9, ix, iy)]
                    if self.FIT["brow_grab"] <= u < self.FIT["brow_on"]:
                        item = ("brow", kind)
                else:
                    keys += [(6.0, ix, iy)]
                x, y, _ = path(keys, u)
                return x, y, item
            names = self.bolt_points(m)
            keys = [(0.0, ix, iy), (1.4, *names[0]), (4.0, *names[0]), (5.2, *names[1]), (7.6, *names[1]),
                    (8.9, ix, iy)]
            x, y, _ = path(keys, u)
            return x, y, None
        bx, by = m.body_center()
        rx, ry = m.body_size()
        e = smoothstep(seg(u, 0.0, 1.0)) * (1 - smoothstep(seg(u, self.W - 1.0, self.W)))
        if st == 2:                                            # SAND: one pad each side, up and down the body
            py_ = by + ry * 0.55 * math.sin(u * 2 * math.pi / 3.0)
            return lerp(ix, bx - rx - 16, e), lerp(iy, py_, e), None
        ang = u * 2 * math.pi / 4.5                            # POLISH: the wheel goes round the front
        return lerp(ix, bx + rx * 0.4 * math.cos(ang), e), lerp(iy, by + ry * 0.4 * math.sin(ang), e), None

    def part_xy(self, m, new=False):
        """Grip point of the old part (Hans' beard, Twigs' sharp mouth) or where the new piece goes."""
        bx, by = m.body_center()
        k = m.k
        if m.kind == "tentacles":
            return bx, by + (56 if new else 110) * k
        return bx, by + (28 if new else 30) * k

    def brow_xy(self, m):
        bx, by = m.body_center()
        return bx, by - 58 * m.k - 58 * m.k

    def bolt_points(self, m):
        bx, by = m.body_center()
        rx, ry = m.body_size()
        return [(bx - rx * 0.85, by + ry * 0.2), (bx + rx * 0.85, by + ry * 0.2)]

    # ----- particles and sounds -----

    def _particles(self, t):
        p = self.s.particles
        for st in (2, 3):
            su = self.station_unit(st, t)
            if su is None:
                continue
            kind, u = su
            if not (1.0 < u < self.W - 1.0):
                continue
            x, y, _ = self.tool_point(st, kind, u)
            if st == 2 and p.rng.uniform() < 0.6:
                p.burst(x, y, 2, SAWDUST * 1.05, 150, 1.0, 4.5, g=500, spread=1.2, direction=math.pi)
            if st == 3 and p.rng.uniform() < 0.25:
                p.burst(x + p.rng.uniform(-30, 30), y + p.rng.uniform(-30, 30), 1, STAR, 40, 0.6, 3.5, g=-20,
                        glow=True)

    def _sounds(self, t):
        s = self.s
        for j, kind in enumerate(ORDER):
            if self.crossed(self.in_door[kind] + 0.2):
                self.chat(self.in_door[kind] + 0.2, kind, "ooh" if j % 2 == 0 else "mm", icon=None if j else "auto")
            if self.crossed(self.hop_up[kind]):
                self.hit(self.hop_up[kind], "boing" if kind == "springs" else "thud", 50, 0.12,
                         slot_x(self.slot0[kind]), PY)
        if self.crossed(self.O0 - 2.0):
            self.chat(self.O0 - 2.0, "lantern", "hm")
        for i, kind in enumerate(self.out_order):
            o = self.out_t[kind]
            x = slot_x(i)
            if self.crossed(o):
                self.fx(o, "servo", 1.8, 0.18, x, RAIL_Y)
            if self.crossed(o + 1.0):
                self.chat(o + 1.0, kind, "mm")
            if self.crossed(o + 3.4):
                self.hit(o + 3.4, "clack", 60, 0.18, x, G - 300)
            if self.crossed(o + 3.8):
                self.hit(o + 3.8, "soft_bell", 72 - 2 * i, 0.16, x, G - 300)
            if self.crossed(o + 6.3):
                self.hit(o + 6.3, "clack", 67, 0.12, x, RAIL_Y)
            nxt = self.out_order[i + 1] if i + 1 < 6 else None
            if nxt is not None and self.crossed(o + 6.6):
                self.chat(o + 6.6, nxt, "aww")
        for c in range(10):
            mt = self.L0 + c * (self.M + self.W)
            if self.crossed(mt):
                self.fx(mt, "motor", self.M, 0.22, 4050, G - 100)
            if c < 9 and self.crossed(mt + self.M):
                ws = mt + self.M
                for st in range(4):
                    su = self.station_unit(st, ws + 0.01)
                    if su is None:
                        continue
                    sx = slot_x(6 + st)
                    if st == 0:
                        self.hit(ws + self.UNCLIP["pin_grab"], "clack", 64, 0.16, sx, G - 300)
                        self.hit(ws + self.UNCLIP["pin_drop"] + 0.3, "thud", 55, 0.12, sx + 150, G)
                        if su[0] in ("tentacles", "teeth"):
                            self.hit(ws + self.UNCLIP["part_grab"], "clack", 62, 0.16, sx, G - 300)
                            self.hit(ws + self.UNCLIP["part_drop"] + 0.3, "thud", 52, 0.14, sx + 150, G)
                    elif st == 1:
                        if su[0] in ("tentacles", "teeth"):
                            self.hit(ws + self.FIT["grin_on"], "clunk", 55, 0.18, sx, G - 300)
                            self.hit(ws + self.FIT["grin_on"] + 0.1, "chime", 76, 0.1, sx, G - 300)
                            if su[0] == "teeth":
                                self.hit(ws + self.FIT["brow_on"], "clunk", 57, 0.16, sx, G - 300)
                        else:
                            for b in (2.0, 5.6):
                                self.fx(ws + b, "servo", 1.6, 0.1, sx, G - 300)
                    elif st == 2:
                        self.fx(ws + 1.0, "sand_scrape", self.W - 2.0, 0.12, sx, G - 300)
                    else:
                        self.fx(ws + 1.0, "rustle", self.W - 2.0, 0.1, sx, G - 300)
        if self.crossed(self.L0 + 5.0):
            self.fx(self.L0 + 5.0, "servo", 3.0, 0.1, 3000, RAIL_Y)
        for q, kind in enumerate(ORDER):
            i0 = self.in_t[kind]
            x = slot_x(15 - q)
            if self.crossed(i0):
                self.fx(i0, "servo", 1.6, 0.16, x, RAIL_Y)
            if self.crossed(i0 + 3.95):
                self.hit(i0 + 3.95, "clack", 67, 0.14, x, G - 300)
                self.hit(i0 + 4.0, "chime", 72 + 2 * q, 0.16, x, G - 300)
                self.hit(i0 + 4.3, "soft_bell", 79, 0.12, x, G - 300)
            wake = i0 + 6.0 + (self.HANS - 1.0 if kind == "tentacles" else 0.0)
            if self.crossed(wake):
                self.chat(wake, kind, "ooh" if kind != "tentacles" else "mm", icon=None if kind != "tentacles" else "auto")
            if kind != "tentacles" and self.crossed(i0 + 6.6):
                self.hit(i0 + 6.6, "boing" if kind == "springs" else "thud", 48, 0.1, x, FY)
        h0 = self.in_t["tentacles"]
        if self.crossed(h0 + 9.9):
            self.chat(h0 + 9.9, "tentacles", "hehe", icon="smile")
        if self.crossed(h0 + 11.0):
            self.chorus(h0 + 11.0, ["lantern", "wheels", "springs", "digger", "teeth"], "yay", gap=0.22)
        hm = self.hans_at_mirror
        if self.crossed(hm + 0.4):
            self.chat(hm + 0.4, "tentacles", "ooh")
        if self.crossed(hm + 2.2):
            self.chat(hm + 2.2, "tentacles", "hehe", icon="smile")
        if self.crossed(hm + 2.0):
            self.hit(hm + 2.0, "chime", 84, 0.1, MIRROR[0], G - 300)
        tm = self.twigs_at_mirror
        if self.crossed(tm + 1.0):
            self.chat(tm + 1.0, "teeth", "hehe", icon="smile")
        if self.crossed(self.door[0]):
            self.fx(self.door[0], "motor", self.door[1] - self.door[0], 0.35, EXIT[0], G - 300)
        if self.crossed(self.door[1]):
            self.hit(self.door[1], "clunk", 45, 0.3, EXIT[0], G - 500)
        for kind in self.exit_order:
            if self.crossed(self.exit_t[kind] + 0.2):
                self.chat(self.exit_t[kind] + 0.2, kind, "wee" if kind == "springs" else "mm", icon=None)

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self._hall(c, t)
        self.way_in.draw_inside(self, c, t, self.door_depth)
        self.way_out.draw_inside(self, c, t, self.door_depth)
        self._exit_door(c, t)
        self._rail(c, t)
        self._stations_back(c, t)
        self._line(c, t)
        self._mirror(c, t)
        self.glo_light(c, k=0.6 * self.m("lantern").alive)
        self.draw_monsters(c, t, kinds=self.outside())
        if s.visible(slot_x(7) - 300, slot_x(7)):
            self._tray(c, t)                            # in front of the line: the pieces stay in front all the way
        self._tools(c, t)
        self._gripper(c, t)
        self._front(c, t)

    def _hall(self, c, t):
        s = self.s
        vx0, vx1, vy0, vy1 = s.view()
        L, R = max(HALL[0], vx0 - 200), min(HALL[1], vx1 + 200)
        top = G - 1300
        rect(c, L, top - 400, R, G, INTERIOR)
        off = s.cam_x * 0.25
        for gx in np.arange(math.floor((L - off) / 340) * 340 + off, R, 340):
            rect(c, gx, top, gx + 26, G, FAR)
        for gy in (G - 1000, G - 430):
            c.line(L, gy, R, gy, FAR, 9)
        rect(c, L, top, R, G - 1180, MID)
        glo_x = self.m("lantern").x
        for lx in self.lamps:
            if not (L - 300 < lx < R + 300):
                continue
            on = smoothstep(seg(glo_x if t < self.O0 else 1e9, lx - 260, lx - 60))
            c.line(lx, G - 1180, lx, G - 900, CABLE, 3)
            c.polygon([(lx - 42, G - 868), (lx + 42, G - 868), (lx + 22, G - 900), (lx - 22, G - 900)], STEEL)
            c.circle(lx, G - 864, 12, IRON * 1.2 + LAMP * 0.6 * on)
            if on > 0:
                s.glow_draw(lambda g, lx=lx, on=on: (g.circle(lx, G - 862, 22, LAMP * 0.7 * on),
                                                     g.polygon([(lx - 42, G - 862), (lx + 42, G - 862), (lx + 260, G),
                                                                (lx - 260, G)], LAMP * 0.035 * on)))
        rect(c, L, G, R, G + 700, FLOOR)
        c.line(L, G, R, G, lighten(FLOOR, 1.9), 2)
        c.line(L, FY + 40, R, FY + 40, lighten(FLOOR, 1.3), 2)
        # the way in (from the tunnel) and the way out
        for (d0, d1), outside in ((ENTRY, False), (EXIT, True)):
            if not (L < d1 + 100 and d0 - 100 < R):
                continue
            rect(c, d0, G - 520, d1, G, INTERIOR * 0.45)
            if outside:
                u = smoothstep(seg(t, *self.door))
                rect(c, d0, G - 520, d1, G, np.array([16, 22, 40]) * (0.4 + 0.6 * u))
                for q in range(5):
                    sx_ = d0 + 30 + q * 57
                    c.circle(sx_, G - 470 + 37 * ((q * 7) % 5), 2.5, SIGN_WARM * 0.6 * u)
                rect(c, d0, G - 30, d1, G, np.array([30, 44, 30]) * u + INTERIOR * 0.45 * (1 - u))
            else:
                for k in range(3):
                    c.line(d0 + 8, G - 440 + k * 140, d1 - 8, G - 440 + k * 140, INTERIOR * 0.8, 3)
            machine_block(c, d0 - 22, G - 566, d1 + 22, G - 520, STEEL)

    def _rail(self, c, t):
        """The orb trolley's rail along the back wall, the trolley and its rack of six cups."""
        s = self.s
        vx0, vx1 = s.view()[:2]
        c.line(max(HALL[0], vx0 - 100), RAIL_Y - 20, min(HALL[1], vx1 + 100), RAIL_Y - 20, CABLE, 10)
        for hx in np.arange(math.floor(vx0 / 600) * 600, vx1 + 600, 600):
            c.line(hx, G - 1180, hx, RAIL_Y - 20, CABLE * 0.8, 4)
        tx = self.trolley_x(t)
        if not s.visible(tx - 200, tx + 200):
            return
        machine_block(c, tx - 120, RAIL_Y - 40, tx + 120, RAIL_Y + 30, STEEL)
        for wx in (-80, 80):
            c.circle(tx + wx, RAIL_Y - 20, 12, IRON)
        c.text("ORBS", tx, RAIL_Y - 6, 26, SIGN_WARM * 0.75)
        top = RAIL_Y + 66
        for q, kind in enumerate(ORDER):
            cx = tx + self.cup(q)
            c.line(cx, RAIL_Y + 30, cx, top + 6, CABLE, 3)
            c.polygon(ellipse(cx, top + 6, 17, 10, 16, 0, math.pi), IRON * 1.3)
            if self.in_rack(kind, t):
                loose_orb(c, s, cx, top, orb_r(self.m(kind)), 0.8)
        # the gripper's carriage and cable top (the cable itself comes down in front, in _gripper)
        gx, gy, _ = self.gripper(t)
        rect(c, gx - 14, RAIL_Y + 24, gx + 14, RAIL_Y + 40, IRON * 1.3)

    def _gripper(self, c, t):
        s = self.s
        gx, gy, held = self.gripper(t)
        if not s.visible(gx - 100, gx + 100):
            return
        if held is not None:
            loose_orb(c, s, gx, gy, orb_r(self.m(held)))
        c.line(gx, RAIL_Y + 40, gx, gy - 26, CABLE, 3)
        rect(c, gx - 12, gy - 34, gx + 12, gy - 22, STEEL * 1.2)
        open_ = 0.0 if held is not None else 1.0
        for sd in (-1, 1):
            c.line(gx + sd * 8, gy - 24, gx + sd * (14 + 8 * open_), gy - 6, STEEL * 1.4, 4)
            c.line(gx + sd * (14 + 8 * open_), gy - 6, gx + sd * (8 + 6 * open_), gy + 8, STEEL * 1.4, 4)

    def _stations_back(self, c, t):
        s = self.s
        for st, name in enumerate(STATIONS):
            sx = slot_x(6 + st)
            if not s.visible(sx - 260, sx + 260):
                continue
            for px_ in (sx - 200, sx + 200):
                rect(c, px_ - 10, BEAM_Y, px_ + 10, PY + 10, STEEL * 0.55)
            rect(c, sx - 210, BEAM_Y - 20, sx + 210, BEAM_Y + 4, STEEL * 0.7)
            machine_block(c, sx - 120, BEAM_Y - 86, sx + 120, BEAM_Y - 30, IRON)
            busy = self.station_unit(st, t) is not None
            col = HAZARD if busy else STEEL * 0.6
            c.text(name, sx - 12, BEAM_Y - 58, 30, SIGN_WARM * 0.8)
            c.circle(sx + 98, BEAM_Y - 58, 8, col)
            if busy:
                s.glow_draw(lambda g, sx=sx, col=col: g.circle(sx + 98, BEAM_Y - 58, 15, col * 0.6))
            # the bin (UNCLIP) and the tray of new pieces (FIT): their backs
            if st == 0:
                bx, by = self.bin_xy(0)
                rect(c, bx - 60, by, bx + 60, by + 70, BIN * 0.7)

    def _tray(self, c, t):
        tx, ty = self.tray_xy(1)
        rect(c, tx - 80, ty, tx + 80, ty + 12, PLANK_C)
        for lx in (tx - 66, tx + 66):
            c.line(lx, ty + 12, lx, G + 90, PLANK_C * 0.7, 6)
        c.text("NEW", tx, ty + 34, 20, SIGN_WARM * 0.5)
        # pieces still waiting on the tray (Hans' smile, Twigs' grin and brow)
        for kind, dx, what in (("tentacles", -20, "new"), ("teeth", -20, "new"), ("teeth", 30, "brow")):
            f0 = self.work(kind, 1)
            grab = self.FIT["grin_grab"] if what == "new" else self.FIT["brow_grab"]
            if t >= f0 + grab:
                continue
            if kind == "teeth" and t < self.work("tentacles", 1) + self.FIT["grin_grab"] and what == "new":
                dx = 40 if what == "new" else dx
            self._piece(c, self.m(kind), what, tx + dx, ty - 6, flat=True)

    def _piece(self, c, m, what, x, y, flat=False):
        """A new face piece (wood, still unpainted: the colour comes with the orb) or an old one, its grip point at
        (x, y)."""
        k = m.k
        wood = m.color
        if what == "new" and m.kind == "tentacles":
            smile_mouth(c, x, y, 56 * k, 0.6, 0.0, wood, k, depth=1.2, awake=0.0)
        elif what == "new":
            smile_mouth(c, x, y, 58 * k, 0.6, 0.0, wood, k, teeth=4, depth=1.5, awake=0.0)
        elif what == "brow":
            arch = [(x + u * 24 * k, y - 7 * k * (1 - u * u)) for u in np.linspace(-1, 1, 15)]
            c.polyline(arch, np.asarray(wood) * 0.5, 6 * k)
        elif what == "part" and m.kind == "tentacles":
            beard(c, x, y - 110 * k, k, wood, m.gait * 0.5, self.s._t)
        elif what == "part":
            fang_mouth(c, x, y, k, wood, 0.0, self.s._t)
        elif what == "pin":
            draw_pin(c, x, y, k)

    def _line(self, c, t):
        s = self.s
        x0, x1 = slot_x(0) - 260, slot_x(15) + 260
        vx0, vx1 = s.view()[:2]
        a, b = max(x0, vx0 - 100), min(x1, vx1 + 100)
        if a < b:
            rect(c, a, PY + 14, b, G + 24, IRON)
            c.line(a, PY + 14, b, PY + 14, lighten(IRON, 1.5), 2)
            roll = self.moves(t) * D / 9.0
            for rx_ in np.arange(math.floor(a / 48) * 48, b, 48):
                c.circle(rx_, PY + 30, 8, STEEL)
                c.line(rx_, PY + 30, rx_ + 7 * math.cos(roll), PY + 30 + 7 * math.sin(roll), STEEL * 0.6, 2)
        for kind in ORDER:
            ux = self.unit_x(kind, t)
            if s.visible(ux - 140, ux + 140):
                rect(c, ux - 120, PY, ux + 120, PY + 14, HAZARD * 0.55)

    def _mirror(self, c, t):
        """A tall polished steel mirror standing on the walkway: whoever stands left of it sees themself in it."""
        s = self.s
        m0, m1 = MIRROR
        if not s.visible(m0 - 600, m1 + 100):
            return
        top, bot = G - 470, FY + 6
        glass = [(m0, top), (m1, top), (m1, bot), (m0, bot)]
        c.polygon(glass, STEEL_GLASS * 0.42)
        for q in range(4):
            xx = m0 + 60 + q * 140
            c.line(xx, top + 20, xx + 80, top + 120, STEEL_GLASS * 0.55, 6)

        def refl():
            for m in self.s.monsters:
                if m.kind not in self.poses or not (m0 - 520 < m.x < m0):
                    continue
                dy, ang = self.poses[m.kind]
                mc = Xform(c, 0, dy, 0.0, 1.0, m0, 0.0, -1.0)
                if m.kind == "tentacles":
                    for i, (tx_, ty_) in enumerate(self.reach.get("tentacles", [])):
                        m.work_tentacle(mc, tx_, ty_, t, slot=i - 0.5, dy=dy)
                m.draw(mc, t, None)
        keep_inside(c, glass, refl, tint=STEEL_GLASS, mix=0.22)
        rect(c, m0 - 16, top - 16, m1 + 16, top, STEEL * 1.3)
        rect(c, m0 - 16, top, m0, bot, STEEL * 1.3)
        rect(c, m1, top, m1 + 16, bot, STEEL * 1.3)
        for fx_ in (m0 + 40, m1 - 40):
            c.line(fx_, bot, fx_ - 20, bot + 30, STEEL, 6)
            c.line(fx_, bot, fx_ + 20, bot + 30, STEEL, 6)

    def _tools(self, c, t):
        s = self.s
        for st in range(4):
            sx = slot_x(6 + st)
            if not s.visible(sx - 300, sx + 300):
                continue
            ix, iy = self.idle_xy(st)
            su = self.station_unit(st, t)
            if su is None:
                c.line(ix, BEAM_Y, ix, iy - 20, STEEL * 0.8, 9)
                rect(c, ix - 20, iy - 24, ix + 20, iy, IRON * 1.2)
                continue
            kind, u = su
            x, y, item = self.tool_point(st, kind, u)
            m = self.m(kind)
            elbow = (lerp(ix, x, 0.5) + (40 if st != 2 else -40), lerp(BEAM_Y, y, 0.5) - 60)
            c.line(ix, BEAM_Y, *elbow, STEEL * 0.85, 10)
            c.line(*elbow, x, y - 12, STEEL, 8)
            c.circle(*elbow, 9, IRON * 1.4)
            if st == 0 or (st == 1 and kind in ("tentacles", "teeth")):
                if item is not None:
                    self._piece(c, self.m(item[1]), item[0], x, y)
                closed = item is not None
                for sd in (-1, 1):
                    c.line(x + sd * 6, y - 14, x + sd * (10 if closed else 18), y + 4, STEEL * 1.4, 4)
                rect(c, x - 10, y - 22, x + 10, y - 12, HAZARD * 0.8)
                # what drops into the bin falls in behind its front (drawn in _front)
            elif st == 1:                                     # bolt check: a little driver spinning
                rect(c, x - 9, y - 9, x + 9, y + 9, IRON)
                spin = (t * 30) % (2 * math.pi)
                c.line(x, y, x + 9 * math.cos(spin), y + 9 * math.sin(spin), STAR * 0.8, 3)
                if 1.6 < u < 4.0 or 5.6 < u < 7.6:
                    s.glow_draw(lambda g, x=x, y=y: g.circle(x, y, 14, LAMP * 0.4))
            elif st == 2:                                     # sanding pads both sides
                bx, by = m.body_center()
                rx, _ = m.body_size()
                e = x - bx
                for sd in (-1, 1):
                    px_ = bx + sd * abs(e) + 3 * math.sin(t * 60) * (1 if 1 < u < 8 else 0)
                    rect(c, px_ - 8 + sd * 4, y - 30, px_ + 8 + sd * 4, y + 30, PAD)
                    rect(c, px_ - 3 - sd * 6, y - 26, px_ + 3 - sd * 6, y + 26, HAZARD * 0.75)
                    if sd == 1:
                        c.line(sx + 120, BEAM_Y, px_ + 14, y, STEEL, 7)
            else:                                             # the soft buffing wheel
                spin = t * 14
                c.circle(x, y, 30, FLEECE * 0.92)
                for q in range(6):
                    a_ = spin + q * math.pi / 3
                    c.line(x, y, x + 26 * math.cos(a_), y + 26 * math.sin(a_), FLEECE * 0.78, 2)
                c.circle(x, y, 8, STEEL)

    def _front(self, c, t):
        s = self.s
        # the bin's front: anything dropped falls behind it
        bx, by = self.bin_xy(0)
        if s.visible(bx - 80, bx + 80):
            su = self.station_unit(0, t)
            if su is not None:
                kind, u = su
                for what, d0 in (("pin", self.UNCLIP["pin_drop"]), ("part", self.UNCLIP["part_drop"])):
                    if what == "part" and kind not in ("tentacles", "teeth"):
                        continue
                    if d0 <= u < d0 + 0.5:
                        yy = by - 40 + 1300 * (u - d0) ** 2
                        self._piece(c, self.m(kind), what, bx, yy)
            rect(c, bx - 64, by + 6, bx + 64, by + 74, BIN)
            c.line(bx - 64, by + 6, bx + 64, by + 6, lighten(BIN, 1.4), 3)
            c.text("OLD", bx, by + 42, 22, SIGN_WARM * 0.55)
        # the hall's end walls, in front: whoever comes in from the tunnel / goes out walks behind them
        for x0, x1, edge in ((ENTRY[0] - 900, ENTRY[0], ENTRY[0]), (EXIT[1], EXIT[1] + 900, EXIT[1])):
            if not s.visible(x0, x1):
                continue
            rect(c, x0, G - 1400, x1, FY + 120, MID * 1.05)
            for yy in np.arange(G - 1300, FY + 100, 160):
                c.line(x0, yy, x1, yy, MID * 0.85, 3)
            rect(c, edge - 14, G - 1400, edge + 14, FY + 120, STEEL * 0.9)
            c.line(edge - 14, G - 1400, edge - 14, FY + 120, lighten(STEEL, 1.4), 2)
            s.glow_draw(lambda g, x0=x0, x1=x1: g.polygon([(x0, G - 1400), (x1, G - 1400), (x1, FY + 120),
                                                           (x0, FY + 120)], np.zeros(3)))

    def _exit_door(self, c, t):
        """The roll-up door of the way out (in the back wall, in front of whoever is in the doorway)."""
        if not self.s.visible(EXIT[0] - 50, EXIT[1] + 50):
            return
        u = smootherstep(seg(t, *self.door))
        bot = lerp(G, G - 514, u)
        if bot > G - 512:
            rect(c, EXIT[0], G - 520, EXIT[1], bot, IRON)
            for y in np.arange(G - 490, bot, 34):
                c.line(EXIT[0], y, EXIT[1], y, IRON * 0.7, 2)
            rect(c, EXIT[0], bot - 14, EXIT[1], bot, HAZARD * 0.7)


PLANK_C = np.array([150, 112, 72], np.float64)


# ====================================================================== HOME: back in the village

class HomeAct(VillageAct):
    name = "home"
    OUT_ORDER = ["lantern", "wheels", "digger", "springs", "teeth", "tentacles"]
    SPOT = {"lantern": 2330.0, "wheels": 2540.0, "digger": 2750.0, "springs": 2950.0, "teeth": 3130.0,
            "tentacles": 3800.0}

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.out = {k: 0.8 + 1.6 * q for q, k in enumerate(self.OUT_ORDER)}      # starts coming out of the dark
        self.step = {k: self.out[k] + DEPTH_T for k in self.OUT_ORDER}             # on the doorstep
        self.walk_home = {k: Route(self.x_in, self.step[k]).go(self.SPOT[k], v=190) for k in self.OUT_ORDER}
        self.home = {k: self.walk_home[k].t for k in self.OUT_ORDER}
        self.hog_t = max(self.home["teeth"], self.home["tentacles"]) + 1.0
        self.bunny_t = self.hog_t + 4.5
        self.wave_t = self.bunny_t + 7.5
        self.dur = self.wave_t + 9.0

    def bunny_st(self, t):
        b = self.bunny_t
        if t < b:
            return BUSH[0] + 10, 0.0, -1
        n, d = 3, 0.5
        u = (t - b) / (n * d)
        if u >= 1:
            return 3590.0, 0.0, 1 if t > b + 3.5 else -1
        k_, ph = int(u * n), u * n - int(u * n)
        return lerp(BUSH[0] + 10, 3590.0, (k_ + ph) / n), 4 * 30 * ph * (1 - ph), -1

    def hog_st(self, t):
        u = 1 - smoothstep(seg(t, self.hog_t + 0.6, self.hog_t + 1.2))
        x = px([(self.hog_t + 1.8, HOG), (self.hog_t + 3.4, HOG - 50)], t)
        return x, -1, u

    def props(self, t):
        bx, hop, _ = self.bunny_st(t)
        return {"bunny": (bx, G - hop), "hog": (self.hog_st(t)[0], G)}

    def target(self, t):
        keys = [(0.0, 4300.0, None, 1.0), (self.out["tentacles"], 4050.0, None, 1.0),
                (self.hog_t - 0.5, 3450.0, None, 1.05), (self.bunny_t + 4.0, 3500.0, None, 1.05),
                (self.wave_t, 3100.0, None, 0.85), (self.dur, 2900.0, None, 0.72)]
        return cam_keys(keys, t)

    def update(self, t, dt):
        self.reach = {}
        for kind in self.OUT_ORDER:
            m = self.m(kind)
            if m is None:
                continue
            x0, x1 = self.x_in, self.SPOT[kind]
            y = G - GLO_UP if kind == "lantern" else G
            dy = 0.0
            fl = bump(t, self.step[kind] + 0.3, 1.1) + bump(t, self.wave_t + 0.3 * self.OUT_ORDER.index(kind), 1.1)
            u = depth_out(t, self.out[kind]) if t < self.step[kind] else 0.0
            self.door_depth[kind] = u
            if u > 0.0:                                   # out of the dark tunnel towards the camera
                if kind == "springs":
                    ph = ((t - self.out[kind]) / 0.55) % 1.0
                    dy, m.spring = -4 * 40 * ph * (1 - ph), 0.0
                self.doorway.walking(self, m, t, dt, u, y, dy)
                self.new_look(m, fl)
                continue
            if kind == "springs":
                x, lift, sq = hops(x0, x1, self.step[kind], self.home[kind], t, apex=55, step=170)
                dy, m.spring = -lift, sq
            else:
                x = self.walk_home[kind].at(t)
            if kind == "tentacles" and self.bunny_t + 2.2 <= t < self.bunny_t + 6.0:   # a gentle pat
                u = smoothstep(seg(t, self.bunny_t + 2.2, self.bunny_t + 3.0)) * \
                    (1 - smoothstep(seg(t, self.bunny_t + 5.2, self.bunny_t + 6.0)))
                hx, hy = x - 40, G - 300 * m.k
                tx, ty = 3615.0 + 8 * math.sin(t * 3), G - 112 + 6 * math.sin(t * 6)
                self.reach["tentacles"] = [(lerp(hx, tx, u), lerp(hy, ty, u))]
            wave = 0.0
            if self.wave_t <= t:
                wave = -10 * bump(t, self.wave_t + 0.3 * self.OUT_ORDER.index(kind), 0.5)
            self.place(m, x, t, dt, y=y, dy=dy + wave)
            self.new_look(m, fl, smile=0.9 if kind == "tentacles" and t > self.bunny_t + 1.0 else 0.6)
        self.fireflies()
        self._sounds(t)

    def _sounds(self, t):
        for kind in self.OUT_ORDER:
            if self.crossed(self.step[kind] + 0.3):
                self.hit(self.step[kind] + 0.3, "soft_bell", 79, 0.08, self.m(kind).x, G - 200)
        if self.crossed(self.hog_t):
            self.chat(self.hog_t, "teeth", "hehe", icon="smile")
        if self.crossed(self.hog_t + 1.5):
            self.chat(self.hog_t + 1.5, "teeth", "aww")
        if self.crossed(self.bunny_t - 1.0):
            self.chat(self.bunny_t - 1.0, "tentacles", "mm", icon="smile")
        if self.crossed(self.bunny_t + 3.0):
            self.chat(self.bunny_t + 3.0, "tentacles", "aww")
        if self.crossed(self.wave_t):
            self.chorus(self.wave_t, self.OUT_ORDER, "yay", gap=0.3)
        for q in range(len(self.OUT_ORDER)):
            if self.crossed(self.wave_t + 0.3 * q):
                self.hit(self.wave_t + 0.3 * q, "soft_bell", 72 + 2 * q, 0.08, 3000, G - 200)

    def aside_moods(self, t):
        return [] if t > self.wave_t - 1 else ["mm", "hehe", "aww"]

    def draw(self, c, t):
        self.scene_draw(c, t, 1.0, self.bunny_st(t), self.hog_st(t))
        if self.wave_t - 2 <= t:
            bx = 2000 + 150 * (t - self.wave_t + 2)
            PR.bird(c, bx, G - 560 - 40 * math.sin((bx - 2000) / 300.0), 1.0, 1, 0.5 + 0.5 * math.sin(t * 13), t=t)
