"""Forest Keepers episode 8: The Harvest Feast (docs/engines/forest_keepers_harvest_feast.md). Thanksgiving episode.

  MILL   - an autumn night at the water wheel from episode 4, which now turns a little roller mill. Hook: a squirrel on
           the oak branch knocks an acorn into Wheels' basket, Wheels rolls it to the mill, Hans tips it into the hopper,
           the stones grind and flour puffs into the sack: what are they making? Then every step twice more: Springs
           bounces on the branch and the acorns drop into the basket, Hans tips them into the hopper, the acorns go
           one by one between the two round millstones, the flour runs into the sack. Hans ties the sack.
  TABLE  - the clearing by the treehouse village: Twigs trims ten planks at a stop block with his wrist saw (all the
           same length), Wheels carries them on his head, Hans lays them across two fallen logs, Springs bounces each
           one flat, Glo's spirit level says it is level. Meanwhile Digs builds a clay oven coil by coil (Springs
           stomps the clay soft, Hans smooths it) and Twigs saws the firewood.
  BAKE   - (no cut) Glo's light flare lights the fire. Hans scoops flour, pours water, kneads; Twigs cuts the dough with
           his wrist saw; Hans shapes four loaves and two acorn pies, Springs bounces the pie bases flat, Twigs scores
           the loaves; Digs slides them into the oven on his shovel and they bake golden. Hans sets the table, Glo
           lights the lanterns one by one, Wheels brings the bread.
  FEAST  - (no cut) the birds, the bunnies and the hedgehog from episode 4 come out of their houses; everyone eats
           together at the long table. The camera pulls back over the lit forest.
Each Keeper's own body is the tool: Hans works with his tentacles, Twigs cuts with his wrist saws, Glo changes and
lights things with his light (never a floating tendril), Digs digs and carries on his shovels.
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, Jump, Night, ellipse, lerp, rect, seg, smoothstep, smootherstep, \
    tree, bunny, hedgehog, wood_sign
from families.foundry.keepers.forest import FIREFLY, POST, _firefly
from families.foundry.keepers.halloween import path
from families.foundry.tree_monsters import BARK, LAMP, LEAF, TRUNK

from . import feast_props as F
from . import props as PR
from .animal_houses import (AXLE_R, BUNNY_X, G, HEDGE_X, POST_TOP, POSTS, RACE, STREAM, WCY, WR, WX, BIRD_COLS, Mill,
                            flying_bird, saw_to)
from .marble_run import MarbleAct

K = 0.55                                    # the Keepers' scale in this episode (params monster_scale)
HEAD_W = 338.0                              # top of Wheels' head (x m.k): baskets, planks and boards ride there
KEEPERS = ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"]


def px(keys, t):
    """x from keys [(t, x), ...]: eased between keys (zero speed at every key), held outside."""
    return path([(a, b, 0.0) for a, b in keys], t)[0]


def ballistic_land(y0, y1, g=GRAVITY):
    """Time to fall from y0 to y1 (y down) from rest."""
    return math.sqrt(max(0.0, 2 * (y1 - y0) / g))


class Moves:
    """Springs' moves: real-gravity Jumps with a short rest between, and little bounces on the spot."""

    def __init__(self, x, y):
        self.x0, self.y0 = x, y
        self.hops, self.bounces = [], []
        self.x, self.y, self.t = x, y, 0.0

    def hop(self, t, x1, y1, apex=60.0):
        jp = Jump(self.x, self.y, x1, y1, apex=apex)
        self.hops.append((t, jp))
        self.x, self.y, self.t = x1, y1, t + jp.dur
        return self.t

    def walk(self, t, x1, y1=None, step=200.0, apex=55.0, rest=0.08):
        """Hop by hop to x1 (each hop a real Jump), starting at t -> end time."""
        y1 = self.y if y1 is None else y1
        n = max(1, int(math.ceil(abs(x1 - self.x) / step)))
        xa, ya = self.x, self.y
        for k in range(n):
            u = (k + 1) / n
            t = self.hop(t, lerp(xa, x1, u), lerp(ya, y1, u) if k == n - 1 else ya, apex) + rest
        return t

    def bounce(self, t, h=34.0, d=0.62):
        self.bounces.append((t, d, h))
        return t + d

    def at(self, t):
        """-> (x, y, spring squash)."""
        x, y, spring = self.x0, self.y0, 0.0
        for (ts, jp) in self.hops:
            if t < ts:
                break
            if t < ts + jp.dur:
                return jp.at(t - ts) + (0.0,)
            x, y = jp.x1, jp.y1
            dt_ = t - ts - jp.dur
            spring = 0.8 * (1 - dt_ / 0.12) if dt_ < 0.12 else 0.0
        for (tb, d, h) in self.bounces:
            if tb <= t < tb + d:
                u = (t - tb) / d
                y -= 4 * h * u * (1 - u)
                if u < 0.12 or u > 0.88:
                    spring = 0.7
        return x, y, spring


def _slowed(fn, name):
    """Wrap an act method so it sees the act's own clock (once: a super() call inside is not mapped again)."""
    def wrapped(self, *a):
        if getattr(self, "_slow_in", False):
            return fn(self, *a)
        self._slow_in = True
        try:
            a = list(a)
            i = 1 if name == "draw" else 0                 # draw(c, t), the others (t, ...)
            a[i] = a[i] / self.STRETCH - self.LEAD
            return fn(self, *a)
        finally:
            self._slow_in = False
    wrapped.__name__ = name
    return wrapped


class FeastAct(MarbleAct):
    """An act of the harvest feast: a late-autumn night, leaves drifting down, the Keepers talk.

    Every act runs on its own clock (owner after FK0005: "slow on purpose", like Mr. Rogers): its schedules are
    written in act time, the scene runs them STRETCH times slower, and LEAD seconds of calm come first (act time
    -LEAD..0: everyone is where the act starts them, the name tags show, nothing happens yet). update / draw / target
    / aside_moods get act time; every sound, voice and `crossed` is mapped back to scene time."""
    STRETCH = 1.0
    LEAD = 0.0

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + 81), G, -2500, 9500)

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        for name in ("update", "draw", "target", "aside_moods", "props"):
            if name in cls.__dict__ and not getattr(cls.__dict__[name], "_mapped", False):
                w = _slowed(cls.__dict__[name], name)
                w._mapped = True
                setattr(cls, name, w)

    def real(self, at):
        """Scene time of act time `at`."""
        return self.t0 + (at + self.LEAD) * self.STRETCH

    @property
    def dur(self):
        return (self._dur_base + self.LEAD) * self.STRETCH

    @dur.setter
    def dur(self, v):
        self._dur_base = v

    def crossed(self, at):
        return self.s.crossed(self.real(at))

    def hit(self, t, inst, note, vel, x, y):
        self.s.hit(self.real(t), inst, note, vel, x, y)

    def fx(self, t, name, dur, vel, x, y):
        self.s.fx(self.real(t), name, dur * self.STRETCH, vel, x, y)

    def say(self, t, kind, contour, x, y, vel=0.45):
        self.s.say(self.real(t), kind, contour, x, y, vel)

    def chat(self, t, kind, mood, **kw):
        self.s.chatter.say(self.real(t), kind, mood, **kw)

    def chorus(self, t, kinds, mood, gap=0.2, **kw):
        self.s.chatter.chorus(self.real(t), kinds, mood, gap=gap, **kw)

    def props(self, t):
        """{name: (x, y)} of the things that move this frame (carried, laid, served): the scene checks they never
        jump (owner: things warped to the table and back into Digs' hands). Act time."""
        return {}

    def lamp_xy(self):
        gl = self.m("lantern")
        return gl.x, gl.y - 178 * gl.k

    def flare(self, c, tx, ty, g, col=None, n=9):
        """Glo's light flares up: a soft beam from his lantern to (tx, ty), sparkles drift down it, a glow there."""
        if g <= 0.01 or self.m("lantern") is None:
            return
        s = self.s
        col = LAMP if col is None else np.asarray(col, np.float64)
        lx, ly = self.lamp_xy()
        s.glow_draw(lambda gg: gg.polygon([(lx - 24, ly + 28), (lx + 24, ly + 28), (tx + 30, ty), (tx - 30, ty)],
                                          LAMP * 0.10 * g))
        s.glow_draw(lambda gg: gg.circle(tx, ty, 40 + 26 * g, col * 0.45 * g))
        t = s._t
        for q in range(n):
            u = (t * 0.9 + q / n) % 1.0
            sx = lerp(lx, tx, u) + 14 * math.sin(7.0 * u + q * 2.1) * (1 - u)
            sy = lerp(ly + 28, ty, u)
            tw = 0.6 + 0.4 * math.sin(t * 11 + q * 1.7)
            sc = lerp(LAMP, col, u) * g * tw
            c.circle(sx, sy, 3.5, np.minimum(255, sc * 1.1))
            s.glow_draw(lambda gg, sx=sx, sy=sy, sc=sc: gg.circle(sx, sy, 12, sc * 0.5))

    def glo_light(self, c, k=1.0, ground=None):
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 120, k=k)


# ====================================================================== the mill by the water wheel

# the open mill shed the Keepers build beside the wheel (four posts, two beams, a roof of four boards)
HUT = (2020.0, 2640.0)
EAVE, RIDGE = G - 560.0, G - 700.0
POST_L = 590.0                                        # every hut post is cut this long (30 of it goes in the hole)
BACK = (26.0, -14.0)                                  # the back posts stand this far behind the front ones
HUT_POSTS = [(HUT[0] + BACK[0], G + BACK[1]), (HUT[0], G), (HUT[1] + BACK[0], G + BACK[1]), (HUT[1], G)]
R1, R2 = (2277.0, G - 300.0), (2415.0, G - 300.0)      # the two millstones (axles), each on its forked stand
STAND_L = 330.0
STONE_R, GEAR_R = 62.0, 69.0                          # gear pitch radius: the gears mesh at the middle (R2-R1 = 2x)
# The drive (owner after FK0005's re-render: the crossed belt looked wrong, and the pulley and gears were drawn over
# the stones): a plain open belt from the water wheel's axle pulley to a small pulley on a third gear left of the
# stones, on an arm from the front post. The wheel turns anticlockwise, so the third gear does too; it turns the first
# stone's gear clockwise and that one the second's anticlockwise: both stones move DOWN at the nip.
R0 = (R1[0] - 2 * GEAR_R, R1[1])                      # the drive gear's shaft
PULLEY_R = 34.0                                       # the belt pulley in front of the drive gear
ARM_Y = R0[1]
HX = (R1[0] + R2[0]) / 2                              # the nip / hopper / sack line
HOP_TOP, HOP_THROAT = G - 470.0, G - 385.0
NIP_Y = R1[1]
SACK_X = HX
OAK_X = 3170.0
PILE = (3010.0, G)                                    # the heap of acorns under the oak
BX = 2880.0                                           # Wheels waits here under the branch with his basket
PARK = 2700.0                                         # ... and here by the mill for Hans to lift it
HANS_MILL = 2525.0
DIGS_MILL = 2150.0
FEED = 0.42                                           # one acorn into the stones every FEED s
W_RUN = 1.25                                          # the water wheel's speed (rad/s), as in episode 4
# the saw station right of the oak
STOP_B = 3420.0                                       # stop block: every piece is pushed against it
SH_B = G - 104.0
HORSES_B = (3500.0, 3860.0)
WF_B = 3350.0                                         # Wheels feeds the logs from here
STUMP = (2830.0, G)                                   # a fat stump by the shed: Twigs slices the gear wheels off it
STUMP_R, STUMP_H = 72.0, 150.0
SLICE = 20.0


def stones_rot(wheel_rot):
    """The first stone's angle from the wheel's: the open belt turns the drive gear with the wheel (anticlockwise),
    the drive gear turns the first stone's gear the other way (clockwise, its top towards the nip); the second stone
    (geared to the first) turns anticlockwise. Both move DOWN at the nip and pull the acorns through."""
    return -wheel_rot * AXLE_R / PULLEY_R


def drive_rot(rot1):
    """The drive gear (and its pulley) from the first stone's angle: the other way round, teeth in mesh."""
    return -rot1 + math.pi / 24


def cam_keys(keys, t, h=1080.0):
    """Camera keys (t, x, y, zoom), eased between keys; y None = the ground at 86% of the screen height."""
    keys = [(k[0], k[1], G - 0.36 * h / k[3] if k[2] is None else k[2], k[3]) for k in keys]
    if t <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if b[0] <= a[0]:                                # two keys at one time: a cut (the act lists it in `cuts`)
            continue
        if t < b[0]:
            u = smootherstep((t - a[0]) / (b[0] - a[0]))
            return tuple(lerp(p, q, u) for p, q in zip(a[1:], b[1:]))
    return keys[-1][1:]


def done_site():
    """The finished mill: everything built and turning."""
    return dict(holes=[(1.0, 1.0)] * 6, posts=[0.0] * 4, stands=[0.0, 0.0], beams=2, roof=4,
                stones=[(R1[0], R1[1], None, 1.0, 6), (R2[0], R2[1], None, 1.0, 6)], gears=[24, 24, 24], pulley=True,
                arm=True, hopper=4, belt="on", belt_end=None, run=1.0, sign=True, stump=STUMP_H - 3 * SLICE, pile=40,
                sack=None, hopper_n=0)


def draw_arm(c, x1=None):
    """The drive gear's arm: a board from the front post to the drive shaft, with a bearing block at its end."""
    x1 = R0[0] if x1 is None else x1
    rect(c, HUT[0], ARM_Y - 13, x1 + 18, ARM_Y + 13, PR.WOOD * 0.86)
    c.line(HUT[0], ARM_Y - 13, x1 + 18, ARM_Y - 13, PR.WOOD * 1.05, 3)
    rect(c, x1 - 20, ARM_Y - 20, x1 + 20, ARM_Y + 20, PR.WOOD * 0.7)


class MillSiteAct(FeastAct):
    """An act at the mill site: the brook, the water wheel, the oak, and the shed as far as it is built (site(t))."""

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.mill = M = Mill()
        M.wheel_in, M.belt, M.belt_end = True, 1.0, None
        M.gate_lift, M.gate, M.inlet = 1.0, 1.0, 1.0
        M.race_front, M.water_front = 760.0, RACE[1] - 30
        M.paddles = set(range(8))
        M.legs, M.bearing = (1.0, 1.0), 1.0
        M.omega = W_RUN
        self.oak = F.Oak(OAK_X, G)

    def wheel_rot(self, t):
        return -W_RUN * (t + self.t0 + 3.0)

    def site(self, t):
        return done_site()

    def stone_angle(self, t):
        """The first stone's angle (the second turns the other way)."""
        return stones_rot(self.wheel_rot(t))

    # hooks for the acts
    def behind_stones(self, c, t, st):
        """Acorns dropping into the nip, the flour stream: drawn before the stones so the stones hide them."""

    def ground_things(self, c, t, st):
        """Things lying about (saw station, the basket on the floor ...)."""

    def branch_things(self, c, t):
        """The oak branch, the squirrel, acorns in the air."""
        self.oak.draw_branch(c, t, 0.0, [])

    def held(self, c, kind, t):
        pass

    def carried(self, c, t):
        pass

    def draw(self, c, t):
        s, M, o = self.s, self.mill, self.oak
        st = self.site(t)
        M.rot = self.wheel_rot(t)
        rot1 = self.stone_angle(t)
        self.night.draw(s, c, t)
        for j, x in enumerate((-650, -250, 4450, 4800)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 640 + 60 * (j % 2), 1300 + j)
        o.draw_back(c, s, t)
        M.draw_ground(c, s, t)
        for px_ in (STREAM[0] - 20, STREAM[1] + 20):              # the bridge from episode 2
            rect(c, px_ - 14, G - 40, px_ + 14, G + 40, POST)
        pw = (STREAM[1] - STREAM[0] + 40) / 9
        for k in range(9):
            x0 = STREAM[0] - 20 + k * pw
            rect(c, x0 + 2, G - 40, x0 + pw - 2, G - 22, PR.WOOD * (0.95 + 0.08 * (k % 2)))
        M.draw_gate(c, t)
        if st["pile"] > 0:
            F.acorn_pile(c, PILE[0], PILE[1], st["pile"], 110)
        # the post holes, the back posts and the back beam
        holes = [HUT_POSTS[0], HUT_POSTS[1], HUT_POSTS[2], HUT_POSTS[3], (R1[0], G), (R2[0], G)]
        for k, (hx, hy) in enumerate(holes):
            dug, filled = st["holes"][k]
            if dug > 0 and filled < 1:
                F.post_hole(c, hx, hy, dug, filled)
        for k in (0, 2):
            a = st["posts"][k]
            if a is not None:
                F.post(c, HUT_POSTS[k][0], HUT_POSTS[k][1] + 30, POST_L, a, shade=0.72)
        if st["beams"] >= 1:
            F.beam(c, HUT[0] + BACK[0] - 16, HUT[1] + BACK[0] + 16, EAVE + BACK[1] + 24, shade=0.72)
        # the stone stands, the drive gear's arm, the gears (all behind the stones, whose faces stay in view)
        for k, (sx, sy) in enumerate((R1, R2)):
            a = st["stands"][k]
            if a is not None:
                F.post(c, sx, G + 30, STAND_L, a, w=24, fork=True)
        if st["arm"]:
            draw_arm(c)
        for k, (gx, gy) in enumerate((R1, R2, R0)):
            n = st["gears"][k]
            if n is not None:
                F.gear_cut(c, gx, gy, GEAR_R - 7, (rot1, -rot1 + math.pi / 24, drive_rot(rot1))[k], 24, n)
        if st["pulley"]:
            PR.pulley(c, R0[0], R0[1], PULLEY_R, drive_rot(rot1))
        self.behind_stones(c, t, st)
        for k, sp in enumerate(st["stones"]):
            if sp is None:
                continue
            x, y, roll, hole, grooves = sp
            ang = (rot1 if k == 0 else -rot1) if roll is None else roll
            F.millstone_dressed(c, x, y, STONE_R, ang, hole, grooves)
        if st["hopper"] >= 4:
            F.hopper(c, HX, HOP_TOP, HOP_THROAT, 210, 34, st["hopper_n"], t)
        else:
            F.hopper_build(c, HX, HOP_TOP, HOP_THROAT, 210, 34, st["hopper"])
        if st["hopper"] >= 1:
            c.line(HX - 60, HOP_THROAT + 4, HX - 20, R1[1] - 50, PR.WOOD * 0.7, 6)
            c.line(HX + 60, HOP_THROAT + 4, HX + 20, R2[1] - 50, PR.WOOD * 0.7, 6)
        if st["sack"] is not None:
            F.sack(c, SACK_X, G, *st["sack"])
        rect(c, STUMP[0] - STUMP_R, STUMP[1] - st["stump"], STUMP[0] + STUMP_R, STUMP[1], TRUNK * 1.05)
        c.polygon(ellipse(STUMP[0], STUMP[1] - st["stump"], STUMP_R, 14, 20), np.array([186, 148, 104]))
        for q in range(3):
            c.polygon(ellipse(STUMP[0], STUMP[1] - st["stump"], STUMP_R * (0.25 + 0.22 * q), 3.5 + 3 * q, 16),
                      np.array([170, 132, 92]) if q % 2 else np.array([186, 148, 104]))
        PR.water_wheel(c, WX, WCY, WR, M.rot, M.paddles)
        PR.aframe(c, WX, WCY, G + 110.0, M.legs, M.bearing, spread=235.0)
        # the belt: from the wheel's axle pulley to the drive pulley (open, nothing crossed), in front of the wheel
        if st["belt"] == "on":
            PR.belt(c, (WX, WCY), AXLE_R, R0, PULLEY_R, -M.rot * AXLE_R)
        elif st["belt"] == "partial" and st["belt_end"] is not None:
            ex, ey = st["belt_end"]
            for sg in (-1, 1):
                c.line(R0[0], R0[1] + sg * PULLEY_R, ex, ey + sg * 6, PR.LEATHER, 7)
        self.ground_things(c, t, st)
        self.branch_things(c, t)
        self.glo_light(c, 0.9)
        self.draw_monsters(c, t, before=lambda kind: self.held(c, kind, t))
        self.carried(c, t)
        for k in (1, 3):
            a = st["posts"][k]
            if a is not None:
                F.post(c, HUT_POSTS[k][0], HUT_POSTS[k][1] + 30, POST_L, a)
        if st["beams"] >= 2:
            F.beam(c, HUT[0] - 16, HUT[1] + 16, EAVE + 24)
        if st["roof"] > 0:
            F.shed_roof(c, HUT[0], HUT[1], EAVE, RIDGE, st["roof"])
        if st["sign"]:
            PR.hanging_sign(c, (HUT[0] + HUT[1]) / 2, EAVE + 32, "MILL", 34)
        M.draw_water(c, s, t)


# ====================================================================== BUILD (the mill)

B1 = [("post", POST_L)] * 4 + [("stand", STAND_L)] * 2   # cut first: four hut posts, two stone stands
B2 = [("roof", 380.0)] * 4 + [("beam", 690.0)] * 2        # then: four roof boards (their offcuts: the hopper), two beams on top
CY_B1, CY_B2 = 3.4, 2.8


DISC_DEST = {2: R0, 1: R1, 0: R2}                       # slice k (sliced in this order) -> its shaft
PUL_SRC = (2620.0, G - 8.0)                             # the drive pulley lies by the coiled belt
ARM_SRC = (2470.0, G - 8.0)                             # the arm (a board offcut) lies by the shed
ARM_L = R0[0] + 18 - HUT[0]


class BuildMillAct(MillSiteAct):
    """The Keepers build the mill by the water wheel: the shed, two millstones, three gears, the hopper and the belt."""
    name = "build"
    LEAD = 8.0                                            # (owner) the name tags first, then the squirrel
    names = (0.8 - LEAD, 7.0 - LEAD)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.dur = 119.0
        self.knock = 2.25
        self.bonk = self.knock + ballistic_land(self.oak.branch_y(2884.0) + 26, G - 158)
        self.hole_t = [10.6, 12.4, 15.6, 17.4, 19.8, 22.2]      # Digs digs the six holes (1.5 s each)
        self.b1 = [11.0 + CY_B1 * i for i in range(len(B1))]
        self.b1_carry = (self.b1[-1] + 3.4, self.b1[-1] + 7.2)   # Wheels rolls the stack to the shed
        self.roll = [(14.0, 18.0), (18.2, 22.2)]                # Hans rolls the two stones up from the brook bed
        self.dress = [(25.0, 30.4), (30.8, 36.2)]               # Digs taps the hole and the grooves into them
        self.raise_t = [self.b1_carry[1] + 0.2 + 2.8 * k for k in range(6)]   # posts BL, FL, BR?, see order
        self.raise_order = [0, 1, 4, 5, 2, 3]                   # left posts, the two stands, right posts
        self.cut_piece = self.raise_order[::-1]                 # cut in reverse, so the next one is always on top
        t_up = self.raise_t[-1] + 2.6
        self.b2_go = (t_up - 0.4, t_up + 3.0)                   # Wheels back to the saw station
        self.b2 = [self.b2_go[1] + 0.4 + CY_B2 * i for i in range(len(B2))]
        self.b2_carry = (self.b2[-1] + 2.9, self.b2[-1] + 6.9)
        self.line_t = (t_up + 0.2, t_up + 4.2)                   # Glo's string line over the post tops
        self.mount = [(self.line_t[1] + 0.2, self.line_t[1] + 4.0), (self.line_t[1] + 4.4, self.line_t[1] + 8.2)]
        self.gap_t = (self.mount[1][1] + 0.3, self.mount[1][1] + 3.3)
        b = self.b2_carry[1] + 0.3
        self.beam_t = [(b, b + 2.5), (b + 2.6, b + 5.1)]
        self.roof_t = [(b + 5.3 + 1.5 * k, b + 6.6 + 1.5 * k) for k in range(4)]
        self.tw_walk = (self.b2[-1] + 2.4, self.b2[-1] + 7.0)
        self.slice_t = [(self.tw_walk[1] + 0.4 + 2.0 * k, self.tw_walk[1] + 1.9 + 2.0 * k) for k in range(3)]
        self.arm_t = (self.roof_t[-1][1] + 0.4, self.roof_t[-1][1] + 2.8)   # Hans fits the drive gear's arm
        # the three gears, the top slice first: Springs holds it, Twigs notches it, Hans takes it and fits it on its
        # shaft (the drive gear first, then its pulley, then the stones' gears)
        a = max(self.arm_t[1], self.slice_t[-1][1]) + 1.0
        self.notch_t, self.gfit = [], {}
        hans_free = self.arm_t[1] + 0.2
        for q in range(3):
            k = 2 - q
            self.notch_t.append((a, a + 3.8))
            fa = max(a + 4.1, hans_free)
            self.gfit[k] = (fa, fa + 2.2)
            hans_free = fa + 2.4
            if k == 2:
                self.pul_t = (hans_free, hans_free + 2.0)
                hans_free = self.pul_t[1] + 0.2
            a += 5.2
        self.fit_t = [self.arm_t, self.gfit[2], self.pul_t, self.gfit[1], self.gfit[0]]
        h0 = max(b for (a_, b) in self.fit_t) + 0.3
        self.hop_t = [(h0 + 1.3 * k, h0 + 1.3 * k + 1.1) for k in range(4)]
        self.sack_t = (self.hop_t[0][0], self.hop_t[0][0] + 3.0)
        e0 = self.hop_t[-1][1] + 0.4
        self.belt_t = dict(pick=e0, on1=e0 + 1.6, walk=(e0 + 1.8, e0 + 4.4), twist=(e0 + 4.4, e0 + 6.6))
        self.start = self.belt_t["twist"][1]
        self.test = dict(take=self.start + 1.0, drop=self.start + 2.4)
        self.test["milled"] = self.test["drop"] + ballistic_land(HOP_TOP - 20, HOP_THROAT) + ballistic_land(HOP_THROAT, NIP_Y - 18) + 0.15
        self.dur = self.test["milled"] + 6.0
        # Springs: tamps each post, holds the discs, fetches the test acorn
        mv = Moves(2600.0, G)
        mv.walk(9.0, 2520.0, G, step=120)
        self.tamp = []
        for k, piece in enumerate(self.raise_order):
            fx = self.foot_x(piece)
            t0 = self.raise_t[k] + 2.3
            sx = fx + (60 if fx < 2330 else -60)
            mv.walk(max(mv.t + 0.05, t0 - 0.9), sx, G, step=160, apex=40)
            b0 = max(mv.t + 0.06, t0)
            self.tamp.append((b0, piece))
            mv.bounce(b0, h=28, d=0.45)
        disc_x = STUMP[0] - 150.0
        mv.walk(max(mv.t + 0.1, self.notch_t[0][0] - 2.2), disc_x, G, step=200)
        mv.walk(self.gfit[0][0] + 0.4, PILE[0] - 90, G, step=200)
        mv.walk(mv.t + 0.8, HANS_MILL - 120, G, step=200)
        self.sp = mv
        self.springs_disc_x = disc_x
        self.stats = {"hut_posts": 4, "posts_level": True, "post_len": POST_L, "stands_equal": True,
                      "stone_gap_px": round(R2[0] - R1[0] - 2 * STONE_R, 1),
                      "gears_mesh": bool(abs(R2[0] - R1[0] - 2 * GEAR_R) < 0.5 and abs(R1[0] - R0[0] - 2 * GEAR_R) < 0.5),
                      # y points down, so a growing angle is clockwise: the left stone's top moves right, into the nip
                      "stones_turn_in": bool(stones_rot(-W_RUN * 1.0) - stones_rot(0.0) > 0 and self.stone_angle(self.start + 2) > 0)}

    # ----- where things are -----

    def foot_x(self, piece):
        """Foot of piece (0-3 the hut posts, 4-5 the stands)."""
        return HUT_POSTS[piece][0] if piece < 4 else (R1, R2)[piece - 4][0]

    def foot_y(self, piece):
        return HUT_POSTS[piece][1] if piece < 4 else G

    def piece_len(self, piece):
        return POST_L if piece < 4 else STAND_L

    def b1_state(self, i, t):
        """B1 piece i: ('rough'), ('feed', x, y), ('saw', u), ('lift', x, y), ('head', k), ('raise', ...), ('up')."""
        a = self.b1[i]
        piece = self.cut_piece[i]
        L = self.piece_len(piece)
        if t < a:
            return ("rough",)
        if t < a + 0.9:
            u = smootherstep(seg(t, a, a + 0.9))
            x0, y0 = STOP_B + L / 2 + 20, G + 26
            return ("feed", lerp(x0, STOP_B + L / 2, u), lerp(y0, SH_B, u) - 30 * math.sin(math.pi * u))
        if t < a + 2.4:
            return ("saw", smoothstep(seg(t, a + 1.1, a + 2.2)))
        if t < a + 3.1:
            u = smootherstep(seg(t, a + 2.4, a + 3.1))
            m = self.m("wheels")
            hx, hy = (m.x, m.y - HEAD_W * m.k - 13 * i) if m is not None else (WF_B, G - 186)
            return ("lift", lerp(STOP_B + L / 2, hx, u), lerp(SH_B, hy, u) - 40 * math.sin(math.pi * u))
        k = self.raise_order.index(piece)
        r = self.raise_t[k]
        if t < r:
            return ("head", i)
        if t < r + 2.3:
            return ("raise", piece, t - r)
        return ("up", piece)

    def raise_pose(self, piece, tau):
        """A piece being stood up: (foot x, foot y, angle, held point). It comes off Wheels' head lying flat, its foot
        goes into the hole, then Hans swings it upright."""
        fx, fy = self.foot_x(piece), self.foot_y(piece) + 30
        L = self.piece_len(piece)
        side = 1 if fx < 2330 else -1                        # it lies pointing in towards the middle of the shed
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k) if m is not None else (2330.0, G - 186)
        if tau < 0.8:                                        # off the stack: its foot swings over to the hole
            u = smootherstep(tau / 0.8)
            ang = side * math.pi / 2
            cx0, cy0 = hx - side * L / 2, hy                 # foot when lying on the stack
            return lerp(cx0, fx, u), lerp(cy0, fy - 60, u), ang, None
        if tau < 1.0:
            u = smootherstep((tau - 0.8) / 0.2)
            return fx, lerp(fy - 60, fy, u), side * math.pi / 2 * lerp(1.0, 0.92, u), None
        u = smootherstep(seg(tau, 1.0, 2.3))
        return fx, fy, side * math.pi / 2 * 0.92 * (1 - u), None

    def b2_state(self, i, t):
        a = self.b2[i]
        L = B2[i][1]
        if t < a:
            return ("rough",)
        if t < a + 0.8:
            u = smootherstep(seg(t, a, a + 0.8))
            return ("feed", lerp(STOP_B + L / 2 + 20, STOP_B + L / 2, u), lerp(G + 26, SH_B, u) - 30 * math.sin(math.pi * u))
        if t < a + 2.0:
            return ("saw", smoothstep(seg(t, a + 0.9, a + 1.9)))
        if t < a + 2.7:
            u = smootherstep(seg(t, a + 2.0, a + 2.7))
            m = self.m("wheels")
            hx, hy = (m.x, m.y - HEAD_W * m.k - 13 * i) if m is not None else (WF_B, G - 186)
            return ("lift", lerp(STOP_B + L / 2, hx, u), lerp(SH_B, hy, u) - 40 * math.sin(math.pi * u))
        return ("head", i)

    def site(self, t):
        st = done_site()
        st["holes"] = [(smoothstep(seg(t, h, h + 1.5)), 0.0) for h in self.hole_t]
        posts, stands = [None] * 4, [None, None]
        for i in range(6):
            piece = self.cut_piece[i]
            bs = self.b1_state(i, t)
            ang = None
            if bs[0] == "up":
                ang = 0.0
            if ang is not None:
                if piece < 4:
                    posts[piece] = ang
                else:
                    stands[piece - 4] = ang
        for (tb, piece) in self.tamp:
            if t >= tb + 0.45:
                hole = piece                                  # holes are indexed like the pieces
                st["holes"][hole] = (1.0, 1.0)
        st["posts"], st["stands"] = posts, stands
        st["beams"] = sum(1 for (a, b) in self.beam_t if t >= b)
        st["roof"] = sum(1 for (a, b) in self.roof_t if t >= b)
        stones = []
        for k in range(2):
            stones.append(self.stone_state(k, t))
        st["stones"] = stones
        st["gears"] = [24 if t >= self.gfit[1][1] else None, 24 if t >= self.gfit[0][1] else None,
                       24 if t >= self.gfit[2][1] else None]
        st["pulley"] = t >= self.pul_t[1]
        st["arm"] = t >= self.arm_t[1]
        st["hopper"] = sum(1 for (a, b) in self.hop_t if t >= b)
        st["hopper_n"] = 1 if self.test["drop"] + 0.3 <= t < self.test["drop"] + 0.75 else 0
        bt = self.belt_t
        if t < bt["on1"]:
            st["belt"] = None
        elif t < bt["twist"][1]:
            st["belt"] = "partial"
            st["belt_end"] = self.belt_hold(t)
        else:
            st["belt"] = "on"
        st["sign"] = t >= self.roof_t[-1][1] + 0.5
        st["stump"] = STUMP_H - SLICE * sum(1 for (a, b) in self.slice_t if t >= b)
        st["sack"] = (0.03 if t >= self.test["milled"] + 0.3 else 0.0, 0.0) if t >= self.sack_t[1] else None
        return st

    def stone_state(self, k, t):
        """Millstone k: (x, y, roll angle or None when turning on its axle, hole, grooves) or None (still in the brook)."""
        a, b = self.roll[k]
        start = (1930.0 + 40 * k, G - STONE_R)
        floor = (R1[0] - 70 if k == 0 else R2[0] + 70, G - STONE_R)
        da, db = self.dress[k]
        hole = smoothstep(seg(t, da + 0.3, da + 1.6))
        grooves = int(6 * seg(t, da + 1.8, db))
        ma, mb = self.mount[k]
        if t < a:
            return (start[0], start[1], 0.0, 0.0, 0)
        if t < b:
            u = smootherstep(seg(t, a + 0.3, b - 0.3))
            x = lerp(start[0], floor[0], u)
            return (x, start[1], (x - start[0]) / STONE_R, 0.0, 0)
        roll0 = (floor[0] - start[0]) / STONE_R
        if t < ma:
            return (floor[0], floor[1], roll0, hole, grooves)
        dest = R1 if k == 0 else R2
        if t < mb:
            u = smootherstep(seg(t, ma + 0.4, mb - 0.4))
            return (lerp(floor[0], dest[0], u), lerp(floor[1], dest[1], u) - 40 * math.sin(math.pi * u), roll0, 1.0, 6)
        if t < self.start:
            return (dest[0], dest[1], roll0, 1.0, 6)
        return (dest[0], dest[1], None, 1.0, 6)

    def stone_angle(self, t):
        """Still until the belt goes on, then the stones spin up (exponential)."""
        if t < self.start:
            return 0.0
        tau, w = 1.4, W_RUN * AXLE_R / PULLEY_R
        d = t - self.start
        return w * (d - tau * (1 - math.exp(-d / tau)))

    def belt_hold(self, t):
        """Where Hans holds the free end of the belt: from the stone pulley over to the wheel's axle."""
        bt = self.belt_t
        m = self.m("tentacles")
        a, b = bt["walk"]
        if t < b:
            return (m.x - 70, G - 200) if m is not None else (R1[0] - 200, G - 200)
        u = smootherstep(seg(t, *bt["twist"]))
        return lerp(m.x - 70 if m is not None else WX + 100, WX, u), lerp(G - 200, WCY, u)

    def disc_stack(self, k):
        """Where slice k lies once cut: stacked by the stump, the first one at the bottom."""
        return STUMP[0] + 130.0, G - 8.0 - 13.0 * k

    def disc_state(self, k, t):
        """Slice k: None (still the stump's top), ('flat', x, y) lying on the stack, ('held', x, y, face 0..1,
        teeth) - with Springs while Twigs notches it, with Hans while he fits it - or ('fit',) on its shaft."""
        a, b = self.slice_t[k]
        top = STUMP[1] - (STUMP_H - SLICE * k)
        sx0, sy0 = self.disc_stack(k)
        if t < b:
            return None
        if t < b + 0.6:
            u = smootherstep(seg(t, b, b + 0.6))
            return ("flat", lerp(STUMP[0], sx0, u), lerp(top, sy0, u) - 40 * math.sin(math.pi * u))
        na, nb = self.notch_t[2 - k]
        if t < na - 1.0:
            return ("flat", sx0, sy0)
        hx, hy = self.springs_disc_x + 70, G - 150
        if t < na:
            u = smootherstep(seg(t, na - 1.0, na))
            return ("held", lerp(sx0, hx, u), lerp(sy0, hy, u), u, 0)
        fa, fb = self.gfit[k]
        if t < fa:
            return ("held", hx, hy, 1.0, int(24 * seg(t, na + 0.2, nb - 0.2)))
        if t < fb:
            dest = DISC_DEST[k]
            u = smootherstep(seg(t, fa + 0.1, fb - 0.1))
            return ("held", lerp(hx, dest[0], u), lerp(hy, dest[1], u) - 60 * math.sin(math.pi * u), 1.0, 24)
        return ("fit",)

    def props(self, t):
        out = {}
        for k in range(3):
            d = self.disc_state(k, t)
            if d is not None and d[0] in ("flat", "held"):
                out[f"disc{k}"] = (d[1], d[2])
        a, b = self.pul_t
        if a <= t < b:
            out["pulley"] = self.pulley_pos(t)[:2]
        a, b = self.arm_t
        if a <= t < b:
            out["arm"] = self.arm_pos(t)
        bt = self.belt_t
        if bt["on1"] <= t < bt["twist"][1]:
            out["belt_end"] = self.belt_hold(t)
        if self.test["take"] <= t < self.test["drop"]:
            out["test_acorn"] = self.test_acorn(t)
        m = self.m("wheels")
        k = 0
        for i in range(len(B1)):
            bs = self.b1_state(i, t)
            if bs[0] in ("feed", "lift"):
                out[f"b1_{i}"] = (bs[1], bs[2])
            elif bs[0] == "head" and m is not None:
                out[f"b1_{i}"] = (m.x, m.y - HEAD_W * m.k - 13 * k)
                k += 1
        for i in range(len(B2)):
            bs = self.b2_state(i, t)
            taken = self.beam_t[5 - i][0] if i >= 4 else self.roof_t[3 - i][0]
            if bs[0] in ("feed", "lift"):
                out[f"b2_{i}"] = (bs[1], bs[2])
            elif bs[0] == "head" and t < taken and m is not None:
                out[f"b2_{i}"] = (m.x, m.y - HEAD_W * m.k - 13 * k)
                k += 1
        for q, (a, b) in enumerate(self.roof_t):
            if a <= t < b:
                out[f"roof{q}"] = self.roof_board_pos(q, t)
        for q, (a, b) in enumerate(self.hop_t):
            if a <= t < b:
                out[f"hop{q}"] = self.hop_board_pos(q, t)
        return out

    def pulley_pos(self, t):
        a, b = self.pul_t
        u = smootherstep(seg(t, a + 0.1, b - 0.1))
        return lerp(PUL_SRC[0], R0[0], u), lerp(PUL_SRC[1] - 10, R0[1], u) - 60 * math.sin(math.pi * u), u

    def arm_pos(self, t):
        """Middle of the arm board while Hans carries it to the front post."""
        a, b = self.arm_t
        u = smootherstep(seg(t, a + 0.1, b - 0.1))
        return lerp(ARM_SRC[0], HUT[0] + ARM_L / 2, u), lerp(ARM_SRC[1], ARM_Y, u) - 50 * math.sin(math.pi * u)

    # ----- camera -----

    def target(self, t):
        T = self
        keys = [(-self.LEAD, 2830.0, G - 380.0, 1.22), (0.0, 2900.0, G - 390.0, 1.3), (8.5, 2900.0, G - 390.0, 1.3), (15.0, 3060.0, None, 0.85),
                (T.b1_carry[0], 3060.0, None, 0.85), (T.b1_carry[1] + 1.5, 2340.0, G - 340.0, 1.0),
                (T.raise_t[-1] + 2.0, 2340.0, G - 340.0, 1.0), (T.line_t[0] + 1.5, 2340.0, G - 400.0, 0.95),
                (T.line_t[1], 2340.0, G - 400.0, 0.95), (T.mount[0][0] + 3.0, 2300.0, None, 1.2),
                (T.gap_t[1], 2310.0, None, 1.25), (T.b2_carry[1] - 1.0, 2620.0, None, 0.95),
                (T.beam_t[0][0] + 3.0, 2380.0, G - 420.0, 0.95), (T.roof_t[-1][1], 2380.0, G - 420.0, 0.95),
                (T.notch_t[0][0] + 2.0, 2520.0, None, 1.15), (T.fit_t[0][0], 2560.0, None, 1.15),
                (T.fit_t[2][1], 2400.0, None, 1.15), (T.hop_t[-1][1], 2360.0, None, 1.25),
                (T.belt_t["walk"][1] + 1.0, 2020.0, None, 0.95), (T.start, 2080.0, None, 0.95),
                (T.test["milled"] + 1.5, 2330.0, None, 1.3), (self.dur, 2330.0, None, 1.32)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._wheels(t, dt)
        self._hans(t, dt)
        self._digs(t, dt)
        self._twigs(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._particles(t)
        self.leaves(0.04)
        self._sounds(t)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        a, b = self.b1_carry
        c0, c1 = self.b2_go
        d0, d1 = self.b2_carry
        x = px([(0.0, 2720.0), (9.2, 2720.0), (10.6, WF_B), (a, WF_B), (b, 2330.0), (c0, 2330.0), (c1, WF_B),
                (d0, WF_B), (d1, 2330.0), (self.roof_t[-1][1] + 0.5, 2330.0), (self.roof_t[-1][1] + 3.0, 1880.0)], t)
        m.punch = 0.0
        for cyc in self.b1:
            if cyc - 0.1 <= t < cyc + 1.0 or cyc + 2.35 <= t < cyc + 3.2:
                m.punch = 0.7
        for cyc in self.b2:
            if cyc - 0.1 <= t < cyc + 0.9 or cyc + 1.95 <= t < cyc + 2.8:
                m.punch = 0.7
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        keys = [(0.0, 2450.0), (12.0, 2450.0), (13.6, 2040.0), (self.roll[0][1], R1[0] - 70 + 110)]
        keys += [(self.roll[1][0], 2010.0), (self.roll[1][1], R2[0] + 70 + 110), (self.b1_carry[1] - 1.0, 2460.0)]
        for k, piece in enumerate(self.raise_order):
            fx = self.foot_x(piece)
            hx = fx + (115 if fx < 2330 else -115)
            keys += [(self.raise_t[k] - 0.2, hx), (self.raise_t[k] + 2.3, hx)]
        for k in range(2):
            ma, mb = self.mount[k]
            fl = R1[0] - 70 if k == 0 else R2[0] + 70
            keys += [(ma, fl + (130 if k == 1 else -120)), (mb, fl + (130 if k == 1 else -120))]
        keys += [(self.beam_t[0][0], 2330.0), (self.roof_t[-1][1], 2330.0), (self.arm_t[0] - 0.2, 2560.0),
                 (self.arm_t[1] + 0.3, 2330.0), (self.gfit[2][0], 2450.0), (self.gfit[0][1], 2450.0),
                 (self.hop_t[0][0], HANS_MILL), (self.belt_t["on1"], HANS_MILL - 40), (self.belt_t["walk"][1], WX + 190),
                 (self.belt_t["twist"][1] + 0.4, WX + 190), (self.test["take"], HANS_MILL), (self.dur, HANS_MILL)]
        x = px(keys, t)
        reach = []
        for k in range(2):                                    # rolls a stone along: two tentacles on its rim
            a, b = self.roll[k]
            if a <= t < b:
                sx, sy = self.stone_state(k, t)[:2]
                reach = [(sx - 40, sy - 30), (sx - 30, sy + 20)] if k == 0 else [(sx - 40, sy - 30), (sx - 30, sy + 20)]
            ma, mb = self.mount[k]
            if ma <= t < mb:
                sx, sy = self.stone_state(k, t)[:2]
                reach = [(sx - 50, sy), (sx + 50, sy)]
        for k, piece in enumerate(self.raise_order):
            r = self.raise_t[k]
            if r <= t < r + 2.3:
                fx, fy, ang, _ = self.raise_pose(piece, t - r)
                L = self.piece_len(piece)
                gx, gy = fx + math.sin(ang) * L * 0.62, fy - math.cos(ang) * L * 0.62
                reach = [(gx, gy), (lerp(fx, gx, 0.5), lerp(fy, gy, 0.5))]
        for (a, b), yy in zip(self.beam_t, (EAVE + BACK[1] + 12, EAVE + 12)):
            if a <= t < b:
                bx, by = self.beam_pos(t, a, b, yy)
                reach = [(bx - 140, by), (bx + 140, by)]
        for q, (a, b) in enumerate(self.roof_t):
            if a <= t < b:
                p = self.roof_board_pos(q, t)
                reach = [(p[0] - 40, p[1]), (p[0] + 40, p[1])]
        for k in range(3):
            fa, fb = self.gfit[k]
            if fa <= t < fb:
                d = self.disc_state(k, t)
                reach = [(d[1] - 50, d[2] + 10), (d[1] + 50, d[2] + 10)]
        a, b = self.pul_t
        if a <= t < b:
            px_, py_, _ = self.pulley_pos(t)
            reach = [(px_ - 26, py_ + 8), (px_ + 26, py_ + 8)]
        a, b = self.arm_t
        if a <= t < b:
            px_, py_ = self.arm_pos(t)
            reach = [(px_ - 55, py_ + 4), (px_ + 55, py_ + 4)]
        for q, (a, b) in enumerate(self.hop_t):
            if a <= t < b:
                p = self.hop_board_pos(q, t)
                reach = [p]
        bt = self.belt_t
        if bt["pick"] <= t < bt["on1"]:
            u = seg(t, bt["pick"], bt["on1"])
            reach = [(lerp(2560, R0[0], u), lerp(G - 10, R0[1] - PULLEY_R, u))]
        if bt["on1"] <= t < bt["twist"][1]:
            reach = [self.belt_hold(t)]
        if self.test["take"] <= t < self.test["drop"] + 0.2:
            reach = [self.test_acorn(t)]
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt)

    def beam_pos(self, t, a, b, yy):
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k) if m is not None else (2330.0, G - 186)
        u = smootherstep(seg(t, a + 0.2, b - 0.2))
        return lerp(hx, (HUT[0] + HUT[1]) / 2 + (BACK[0] if yy < EAVE + 10 else 0), u), lerp(hy, yy, u) - 30 * math.sin(math.pi * u)

    def roof_board_pos(self, q, t):
        a, b = self.roof_t[q]
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k) if m is not None else (2330.0, G - 186)
        side, j = divmod(q, 2)
        xm = (HUT[0] + HUT[1]) / 2
        e = (HUT[0] - 70 if side == 0 else HUT[1] + 70, EAVE + 14)
        f = (j + 0.5) / 2
        dest = (lerp(xm, e[0], f), lerp(RIDGE, e[1], f) + 10)
        u = smootherstep(seg(t, a + 0.1, b - 0.1))
        return lerp(hx, dest[0], u), lerp(hy, dest[1], u) - 40 * math.sin(math.pi * u)

    def hop_board_pos(self, q, t):
        a, b = self.hop_t[q]
        src = self.offcut_src(q)
        dests = [(HX - 75, HOP_TOP + 40), (HX + 75, HOP_TOP + 40), (HX, HOP_TOP), (HX, HOP_THROAT)]
        u = smootherstep(seg(t, a + 0.1, b - 0.1))
        return lerp(src[0], dests[q][0], u), lerp(src[1], dests[q][1], u) - 50 * math.sin(math.pi * u)

    def offcut_src(self, q):
        """The four roof-board offcuts ride on Wheels' head with the other pieces, then lie by the shed."""
        return (2560.0 + 26 * q, G - 8)

    def test_acorn(self, t):
        """The test acorn: Springs brings it, Hans lifts it over the hopper and lets go."""
        tk, td = self.test["take"], self.test["drop"]
        sp = self.m("springs")
        sx, sy = (sp.x + 30, sp.y - 120) if sp is not None else (HANS_MILL - 90, G - 120)
        u = smootherstep(seg(t, tk + 0.2, td))
        return lerp(sx, HX, u), lerp(sy, HOP_TOP - 20, u) - 60 * math.sin(math.pi * u)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        holes = [HUT_POSTS[0], HUT_POSTS[1], HUT_POSTS[2], HUT_POSTS[3], (R1[0], G), (R2[0], G)]
        keys = [(0.0, 2884.0), (9.0, 2884.0)]
        m.dig = 0.0
        for k, h in enumerate(self.hole_t):
            hx = holes[k][0] - 70
            keys += [(h - 0.1, hx), (h + 1.5, hx)]
            if h <= t < h + 1.5:
                m.dig = 0.5 + 0.5 * math.sin((t - h) * 12)
        for k in range(2):
            da, db = self.dress[k]
            fl = R1[0] - 70 if k == 0 else R2[0] + 70
            keys += [(da - 0.1, fl + (-120 if k == 0 else 125)), (db, fl + (-120 if k == 0 else 125))]
            if da <= t < db:
                m.dig = 0.35 + 0.35 * max(0.0, math.sin((t - da) * 14))      # taps with the shovel tip
        keys += [(self.sack_t[0], 2560.0), (self.sack_t[0] + 0.4, 2560.0), (self.sack_t[1], SACK_X - 100),
                 (self.dur, SACK_X - 100)]
        x = px(keys, t)
        self.place(m, x, t, dt)

    def tw_dx(self):
        if not hasattr(self, "_twdx"):
            m = self.m("teeth")
            ox, oy = m.x, m.y
            m.x, m.y = 4100.0, G
            self._twdx = saw_to(m, 0.0, 4000.0, SH_B - 10, sx=-1) - 4000.0
            m.x, m.y = ox, oy
            m.punch_l = 0.0
        return self._twdx

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run, m.punch, m.punch_l = 0.0, 0.0, 0.0
        dx = self.tw_dx()
        cuts = []
        keys = [(0.0, 3380.0), (9.5, 3380.0)]
        for i, a in enumerate(self.b1):
            cx = STOP_B + self.piece_len(self.cut_piece[i])
            keys += [(a + 0.7, cx + dx), (a + 2.4, cx + dx)]
            cuts.append((a + 1.1, a + 2.2, cx, SH_B - 26, SH_B + 8))
        keys += [(self.b2[0] - 1.0, STOP_B + B2[0][1] + dx)]
        for i, a in enumerate(self.b2):
            cx = STOP_B + B2[i][1]
            keys += [(a + 0.6, cx + dx), (a + 2.0, cx + dx)]
            cuts.append((a + 0.9, a + 1.9, cx, SH_B - 26, SH_B + 8))
        keys += [(self.tw_walk[1], STUMP[0] - STUMP_R + dx)]
        for k, (a, b) in enumerate(self.slice_t):           # slices a disc off the top of the stump, left to right
            y = STUMP[1] - (STUMP_H - SLICE * (k + 1)) - 2
            keys += [(a, STUMP[0] - STUMP_R + dx), (b, STUMP[0] + STUMP_R + dx), (b + 0.1, STUMP[0] + STUMP_R + dx)]
            cuts.append((a, b, None, y, y))
        sx = self.springs_disc_x + 70 + 78                   # the notches: the right edge of the disc Springs holds
        keys += [(self.notch_t[0][0] - 0.2, sx + dx), (self.notch_t[-1][1], sx + dx), (self.dur, sx + dx + 40)]
        for (a, b) in self.notch_t:
            cuts.append((a + 0.2, b - 0.2, sx, G - 150 - 4, G - 150 + 4))
        x = px(keys, t)
        for (a, b, tx, y0, y1) in cuts:
            if a - 0.2 <= t < b + 0.2:
                u = smoothstep(seg(t, a, b))
                k = smoothstep(seg(t, a - 0.2, a)) * (1 - smoothstep(seg(t, b, b + 0.2)))
                m.x, m.y = x, G
                txx = (x - dx) if tx is None else tx
                yy = lerp(y0, y1, u) if tx is not None and abs(y1 - y0) > 10 else y0 + (4 * math.sin(t * 20) if tx is not None else 0)
                xs = saw_to(m, t, txx, yy, sx=-1)
                m.punch_l *= k
                x = lerp(x, xs, k)
                m.saw_run = 1.0 if a < t < b else 0.0
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y, sq = self.sp.at(t)
        m.spring = sq
        m.punch = 0.0
        for q, (a, b) in enumerate(self.notch_t):
            if a - 1.0 <= t < self.gfit[2 - q][0] + 0.2:          # holds the disc until Hans takes it
                m.punch = 0.9
        if self.test["take"] - 1.5 <= t < self.test["take"] + 0.3:
            m.punch = 0.8
        self.place(m, x, t, dt, y=y)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        a, b = self.line_t
        ga, gb = self.gap_t
        keys = [(0.0, 2790.0, G - 430.0), (9.0, 2790.0, G - 430.0), (13.0, 3300.0, G - 470.0), (self.b1_carry[1], 3300.0, G - 470.0),
                (a - 0.4, HUT[0] + 40, EAVE - 120), (b, HUT[1] + 40, EAVE - 120), (ga - 0.6, HX + 20, NIP_Y - 120),
                (gb + 0.4, HX + 20, NIP_Y - 120), (gb + 3.0, 2560.0, G - 420.0), (self.dur, 2190.0, G - 330.0)]
        x, y = path(keys, t)[:2]
        m.lamp = 1.15 + 0.6 * smoothstep(seg(t, a + 2.6, a + 3.0)) * (1 - smoothstep(seg(t, b, b + 0.4)))
        self.place(m, x, t, dt, y=y + 9 * math.sin(t * 1.3))

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        tw = self.m("teeth")
        if tw is not None and tw.saw_run > 0.5 and P.rng.uniform() < 0.8:
            cx, cy = tw.saw_center(-1, t, 0.0)
            P.burst(cx, cy, 2, np.array([214, 186, 140]), 200, 0.32, 3.5, g=900, spread=0.6, direction=math.pi * 0.7)
        dg = self.m("digger")
        if dg is not None and dg.dig > 0.7 and P.rng.uniform() < 0.4:
            P.burst(dg.x + 60, G - 10, 2, np.array([96, 70, 52]), 240, 0.6, 5, g=1300, spread=0.7, direction=-math.pi * 0.35)
        for k in range(2):
            da, db = self.dress[k]
            if da <= t < db and dg is not None and dg.dig > 0.6 and P.rng.uniform() < 0.3:
                sx, sy = self.stone_state(k, t)[:2]
                P.burst(sx, sy, 2, F.STONE * 1.3, 120, 0.4, 2.5, g=900, spread=1.2)
        if self.crossed(self.test["milled"]):
            P.burst(SACK_X, G - 90, 10, F.FLOUR, 120, 0.9, 4, g=-30, up=60, spread=1.2)

    def _sounds(self, t):
        s = self.s
        if self.crossed(0.1 - self.LEAD):
            self.fx(t, "gurgle", self.dur, 0.05, WX, G)
        if self.crossed(self.knock - 0.15):
            self.hit(t, "pluck", 72, 0.12, 2884, G - 470)
        if self.crossed(self.bonk):
            self.hit(t, "clunk", 60, 0.14, 2884, G - 160)
            self.chat(t + 0.1, "digger", "uhoh")
        if self.crossed(self.bonk + 1.0):
            self.hit(t, "pluck", 67, 0.08, PILE[0], G)
        if self.crossed(4.2):
            self.chat(t, "lantern", "hm", icon="acorn")
        if self.crossed(6.0):
            self.chat(t, "lantern", "idea", icon="bread")
        if self.crossed(7.4):
            self.chorus(t, ["wheels", "springs", "tentacles", "teeth"], "yay", gap=0.22, icon="bread")
        if self.crossed(9.2):
            self.chat(t, "digger", "hey", icon="!")
        for k, h in enumerate(self.hole_t):
            if self.crossed(h + 0.1):
                self.fx(t, "slide", 1.2, 0.05, self.foot_x([0, 1, 2, 3, 4, 5][k]), G)
        for i, a in enumerate(self.b1 + self.b2):
            b2 = i >= len(self.b1)
            if self.crossed(a + (0.85 if b2 else 0.95)):
                self.hit(t, "clack", s.note(i % 4 + 1, -1), 0.08, STOP_B, SH_B)
            if self.crossed(a + (0.9 if b2 else 1.1)):
                self.fx(t, "saw", 1.0, 0.12, STOP_B + 500, SH_B)
            if self.crossed(a + (1.95 if b2 else 2.25)):
                self.hit(t, "thud", 48, 0.06, STOP_B + 500, G)
        for k in range(2):
            a, b = self.roll[k]
            if self.crossed(a + 0.3):
                self.fx(t, "slide", b - a - 0.6, 0.05, 2100, G)
            if self.crossed(b - 0.2):
                self.hit(t, "thud", 45, 0.1, 2200, G)
            da, db = self.dress[k]
            n = int((db - da) / 0.45)
            for q in range(n):
                if self.crossed(da + 0.2 + q * 0.45):
                    self.hit(t, "clack", 64 + (q % 3) * 3, 0.05, 2300, G - 60)
        if self.crossed(self.dress[1][1] + 0.3):
            self.chat(t, "digger", "yay", icon="star")
        for k, (tb, piece) in enumerate(self.tamp):
            if self.crossed(self.raise_t[k] + 1.0):
                self.hit(t, "thud", 46, 0.1, self.foot_x(piece), G)
            if self.crossed(self.raise_t[k] + 2.25):
                self.hit(t, "clunk", 50, 0.08, self.foot_x(piece), G - 200)
            if self.crossed(tb):
                self.hit(t, "boing", 62 + (k % 3) * 2, 0.09, self.foot_x(piece), G)
        if self.crossed(self.raise_t[1] + 2.6):
            self.chat(t, "tentacles", "mm", icon="heart")
        if self.crossed(self.raise_t[5] + 2.8):
            self.chorus(t, ["springs", "wheels"], "yay", gap=0.3)
        a, b = self.line_t
        if self.crossed(a + 2.8):
            self.hit(t, "chime", 76, 0.16, 2330, EAVE)
            self.hit(t + 0.14, "chime", 81, 0.12, 2330, EAVE)
        for k in range(2):
            ma, mb = self.mount[k]
            if self.crossed(mb - 0.3):
                self.hit(t, "clunk", 47 + 2 * k, 0.12, (R1, R2)[k][0], NIP_Y)
        ga, gb = self.gap_t
        if self.crossed(ga + 1.2):
            self.hit(t, "chime", 79, 0.14, HX, NIP_Y)
            self.chat(t + 0.3, "lantern", "mm", icon="acorn")
        for (a2, b2) in self.beam_t + self.roof_t:
            if self.crossed(b2 - 0.1):
                self.hit(t, "clack", s.note(int(a2) % 6 + 1, 0), 0.1, 2330, EAVE)
        if self.crossed(self.roof_t[-1][1] + 0.4):
            self.chorus(t, ["tentacles", "wheels", "digger"], "yay", gap=0.25, icon="star")
        for (a2, b2) in self.slice_t:
            if self.crossed(a2):
                self.fx(t, "saw", b2 - a2, 0.1, STUMP[0], G - 120)
        for (a2, b2) in self.notch_t:
            n = 24
            for q in range(n):
                if self.crossed(a2 + 0.2 + (b2 - a2 - 0.4) * q / n):
                    self.hit(t, "clack", 60 + (q % 4) * 2, 0.035, STUMP[0] - 80, G - 150)
        if self.crossed(self.notch_t[-1][1] + 0.2):
            self.chat(t, "teeth", "hehe", icon="star")
        for (a2, b2) in self.fit_t + self.hop_t:
            if self.crossed(b2 - 0.1):
                self.hit(t, "clack", s.note(int(a2 * 3) % 6 + 1, 0), 0.08, HX, NIP_Y)
        bt = self.belt_t
        if self.crossed(bt["twist"][0] + 0.5):
            self.chat(t, "tentacles", "hm", icon="dots")
        if self.crossed(self.start):
            self.hit(t, "pluck", 60, 0.12, WX, WCY)
            self.fx(t + 0.4, "rush", self.dur - self.start, 0.03, HX, NIP_Y)
        if self.crossed(self.start + 1.0):
            self.chorus(t, ["lantern", "springs"], "ooh", gap=0.3, icon="sparkle")
        if self.crossed(self.test["drop"]):
            self.hit(t, "clack", 72, 0.08, HX, HOP_TOP)
        if self.crossed(self.test["milled"]):
            self.hit(t, "thud", 47, 0.07, HX, NIP_Y)
            self.fx(t + 0.1, "air_blow", 0.5, 0.05, SACK_X, G - 80)
        if self.crossed(self.test["milled"] + 0.8):
            self.chorus(t, ["tentacles", "digger", "teeth", "wheels", "springs", "lantern"], "yay", gap=0.2, icon="star")

    # ----- drawing -----

    def squirrel_state(self, t):
        o = self.oak
        kx = 2884.0
        if t < 0.5:
            return 3080.0, o.branch_y(3080.0), -1, 0.0, 0.0
        if t < 2.0:
            x = lerp(3080.0, kx + 24, smoothstep(seg(t, 0.5, 2.0)))
            return x, o.branch_y(x), -1, 1.0, 0.0
        if t < 4.0:
            return kx + 24, o.branch_y(kx + 24), -1, 0.0, 0.0
        u = seg(t, 4.0, 7.5)
        x = lerp(kx + 24, OAK_X - 40, smoothstep(seg(u, 0.0, 0.35)))
        y = lerp(o.branch_y(kx + 24), G - 1000, smoothstep(seg(u, 0.3, 1.0)))
        return x, y, 1, 1.0 if u < 1 else 0.0, 0.0

    def branch_things(self, c, t):
        o = self.oak
        hang = [(2884.0, 9.5)] if t < self.knock else []
        o.draw_branch(c, t, 0.0, hang)
        sq = self.squirrel_state(t)
        F.squirrel(c, sq[0], sq[1], sq[2], t, sq[3], 1.1, sq[4])
        # the acorn: falls, bonks Digs' hat, bounces off and rolls to the heap
        y0 = o.branch_y(2884.0) + 26
        if self.knock <= t < self.bonk:
            F.acorn(c, 2884.0, y0 + 0.5 * GRAVITY * (t - self.knock) ** 2, 9.5, (t - self.knock) * 4)
        elif self.bonk <= t < self.bonk + 1.5:
            d = t - self.bonk
            if d < 0.55:
                x = 2884.0 + 160 * d
                y = G - 158 - 420 * d + 0.5 * GRAVITY * d * d
                F.acorn(c, x, min(y, G - 9), 9.5, d * 12)
            else:
                u = smoothstep(seg(d, 0.55, 1.5))
                x = lerp(2884.0 + 88, PILE[0] - 80, u)
                F.acorn(c, x, G - 9, 9.5, (x - 2884.0) / 9.5)

    def behind_stones(self, c, t, st):
        td = self.test["drop"]
        t1 = td + ballistic_land(HOP_TOP - 20, HOP_THROAT)
        if t1 <= t < self.test["milled"]:
            u = t - t1
            F.acorn(c, HX, HOP_THROAT + 0.5 * GRAVITY * u * u, 8.5, u * 6)
        if self.test["milled"] <= t < self.test["milled"] + 1.0:
            F.flour_stream(c, self.s, HX, NIP_Y + 10, G - 80, 0.5 * (1 - seg(t, self.test["milled"], self.test["milled"] + 1.0)), t)

    def ground_things(self, c, t, st):
        s = self.s
        if s.visible(STOP_B - 200, STOP_B + 900):
            for x in HORSES_B:
                F.sawhorse(c, x, SH_B, G)
            rect(c, STOP_B - 10, SH_B - 34, STOP_B, SH_B + 4, TRUNK * 1.3)
            rough = [i for i in range(len(B1)) if self.b1_state(i, t)[0] == "rough"]
            rough2 = [i for i in range(len(B2)) if self.b2_state(i, t)[0] == "rough"]
            k = 0
            lens = [self.piece_len(self.cut_piece[i]) for i in rough] + [B2[i][1] for i in rough2]
            for L in sorted(lens, reverse=True):               # rough logs and boards lie in front, longest at the bottom
                F.plank_side(c, STOP_B + L / 2 + 20, G + 26 - 13 * k, L, ragged=40)
                k += 1
            for i in range(len(B1)):
                bs = self.b1_state(i, t)
                L = self.piece_len(self.cut_piece[i])
                if bs[0] == "feed":
                    F.plank_side(c, bs[1], bs[2], L, ragged=40)
                elif bs[0] == "saw":
                    F.plank_side(c, STOP_B + L / 2, SH_B, L, ragged=40 if bs[1] < 1 else 0.0)
            for i in range(len(B2)):
                bs = self.b2_state(i, t)
                L = B2[i][1]
                if bs[0] == "feed":
                    F.plank_side(c, bs[1], bs[2], L, ragged=30)
                elif bs[0] == "saw":
                    F.plank_side(c, STOP_B + L / 2, SH_B, L, ragged=30 if bs[1] < 1 else 0.0)
            n_off = sum(1 for a in self.b1 if t >= a + 2.25) + sum(1 for a in self.b2[4:] if t >= a + 1.95)
            for q in range(n_off):
                c.polygon([(STOP_B + 600 + 8 * q, G + 6 + 3 * (q % 3)), (STOP_B + 636 + 8 * q, G + 6 + 3 * (q % 3)),
                           (STOP_B + 636 + 8 * q, G + 16 + 3 * (q % 3)), (STOP_B + 600 + 8 * q, G + 16 + 3 * (q % 3))],
                          PR.WOOD * 0.9)
        # the roof boards' offcuts lie by the shed until Hans makes the hopper from them
        if t >= self.b2_carry[1]:
            for q in range(4):
                if t < self.hop_t[q][0]:
                    ox, oy = self.offcut_src(q)
                    F.plank_side(c, ox, oy, 120)
            if t < self.arm_t[0] + 0.1:                         # a longer offcut: the drive gear's arm
                F.plank_side(c, ARM_SRC[0], ARM_SRC[1], ARM_L)
        if t < self.pul_t[0] + 0.1:                            # the drive pulley, lying by the belt
            c.polygon(ellipse(PUL_SRC[0], PUL_SRC[1], PULLEY_R, 9, 20), PR.LEATHER * 0.9)
            c.polygon(ellipse(PUL_SRC[0], PUL_SRC[1] - 2, PULLEY_R * 0.25, 3, 12), PR.STEEL * 1.3)
        if t < self.belt_t["pick"]:                            # the leather belt, coiled on the floor
            c.polygon(ellipse(2560.0, G - 8, 34, 10, 20), np.array([96, 62, 40]))
            c.polygon(ellipse(2560.0, G - 9, 20, 5, 16), np.array([70, 46, 30]))
        if t < self.sack_t[0] + 0.3:                           # the empty sack, folded
            c.polygon([(2600, G - 14), (2660, G - 14), (2664, G), (2596, G)], F.SACK)
        for k in range(3):
            d = self.disc_state(k, t)
            if d is not None and d[0] == "flat":
                c.polygon([(d[1] - STUMP_R, d[2]), (d[1] + STUMP_R, d[2]), (d[1] + STUMP_R, d[2] + SLICE - 8),
                           (d[1] - STUMP_R, d[2] + SLICE - 8)], TRUNK * 1.05)
                c.polygon(ellipse(d[1], d[2], STUMP_R, 10, 20), np.array([186, 148, 104]))

    def held(self, c, kind, t):
        if kind != "tentacles":
            return
        for k, piece in enumerate(self.raise_order):
            r = self.raise_t[k]
            if r <= t < r + 2.3:
                fx, fy, ang, _ = self.raise_pose(piece, t - r)
                F.post(c, fx, fy, self.piece_len(piece), ang, w=26 if piece < 4 else 24, fork=piece >= 4,
                       shade=0.72 if piece in (0, 2) else 1.0)
        for (a, b), yy in zip(self.beam_t, (EAVE + BACK[1] + 12, EAVE + 12)):
            if a <= t < b:
                bx, by = self.beam_pos(t, a, b, yy)
                F.beam(c, bx - 345, bx + 345, by + 12)
        for q, (a, b) in enumerate(self.roof_t):
            if a <= t < b:
                p = self.roof_board_pos(q, t)
                F.plank_side(c, p[0], p[1] + 6, 300)
        for q, (a, b) in enumerate(self.hop_t):
            if a <= t < b:
                p = self.hop_board_pos(q, t)
                F.plank_side(c, p[0], p[1] + 6, 100)
        if self.test["take"] <= t < self.test["drop"]:
            p = self.test_acorn(t)
            F.acorn(c, p[0], p[1] + 8, 9.0)
        for k in range(3):                                    # a gear on its way to its shaft
            fa, fb = self.gfit[k]
            if fa <= t < fb:
                self._disc(c, k, self.disc_state(k, t))
        a, b = self.pul_t
        if a <= t < b:                                        # the pulley: lifted, turned to face us, put on
            x, y, u = self.pulley_pos(t)
            f = smoothstep(seg(u, 0.0, 0.4))
            if f >= 1:
                PR.pulley(c, x, y, PULLEY_R, 0.0)
            else:
                c.polygon(ellipse(x, y, PULLEY_R, max(8.0, PULLEY_R * f), 20), PR.LEATHER * 0.9)
        a, b = self.arm_t
        if a <= t < b:
            x, y = self.arm_pos(t)
            F.plank_side(c, x, y + 13, ARM_L)

    def _disc(self, c, k, d):
        _, x, y, face, n = d
        if face >= 1:
            F.gear_cut(c, x, y, GEAR_R - 7, 0.0 + (self.s._t * 0.6 if n < 24 else 0.0), 24, max(0, n))
        else:
            c.polygon(ellipse(x, y, GEAR_R, max(8.0, GEAR_R * face), 24), np.array([186, 148, 104]))

    def carried(self, c, t):
        m = self.m("wheels")
        stack = []
        for i in range(len(B1)):
            bs = self.b1_state(i, t)
            if bs[0] == "head":
                stack.append(("b1", i))
            elif bs[0] == "lift":
                F.plank_side(c, bs[1], bs[2], self.piece_len(self.cut_piece[i]))
        for i in range(len(B2)):
            bs = self.b2_state(i, t)
            taken = self.beam_t[5 - i][0] if i >= 4 else self.roof_t[3 - i][0]
            on = bs[0] == "head" and t < taken
            if on:
                stack.append(("b2", i))
            elif bs[0] == "lift":
                F.plank_side(c, bs[1], bs[2], B2[i][1])
        if m is not None:
            for k, (b, i) in enumerate(stack):
                L = self.piece_len(self.cut_piece[i]) if b == "b1" else B2[i][1]
                F.plank_side(c, m.x, m.y - HEAD_W * m.k - 13 * k, L)
            if self.b2_carry[0] <= t < self.b2_carry[1] + 0.2:     # the offcuts ride on top
                for q in range(4):
                    F.plank_side(c, m.x - 60 + 40 * q, m.y - HEAD_W * m.k - 13 * len(stack) - 2, 100)
                F.plank_side(c, m.x, m.y - HEAD_W * m.k - 13 * len(stack) - 15, ARM_L)
        for k in range(3):
            d = self.disc_state(k, t)
            if d is not None and d[0] == "held" and t < self.gfit[k][0]:   # Springs holds it up for the notching
                self._disc(c, k, d)
        if self.sack_t[0] + 0.3 <= t < self.sack_t[1]:
            dg = self.m("digger")
            if dg is not None:
                c.polygon([(dg.x - 150, G - 90), (dg.x - 90, G - 90), (dg.x - 86, G - 76), (dg.x - 154, G - 76)], F.SACK)


# ====================================================================== MILL (it works)

class MillAct(MillSiteAct):
    """The mill at work: two basket loads of acorns become a sack of flour."""
    name = "mill"
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.loads = [dict(w_go=7.0, lift=9.0), dict(w_go=17.4, lift=19.4)]
        for L in self.loads:
            L["arrive"] = L["w_go"] + 1.8
            L["pour"] = L["lift"] + 0.8
            L["back"] = L["pour"] + 0.75
        self.loads[1]["at_branch"] = 13.0
        rs = np.random.default_rng(11)
        self.hang, self.falls = [], []
        bounce_t = {0: [4.0, 4.95, 5.9], 1: [14.4, 15.35, 16.3]}
        for L in (0, 1):
            for b, tb in enumerate(bounce_t[L]):
                for q in range(4):
                    x = BX - 38 + rs.uniform(0, 76)
                    self.hang.append((x, 9.5))
                    self.falls.append((tb + 0.08 + q * 0.06 + rs.uniform(0, 0.05), x, L))
        self.bounce_t = bounce_t
        self.start_n = 0
        self.basket_y = G - HEAD_W * K
        self.land = []
        for (tr, x, L) in self.falls:
            y0 = self.oak.branch_y(x) + 26
            self.land.append((tr + ballistic_land(y0, self.basket_y - 20), L))
        self.into_hop = []
        for i, L in enumerate(self.loads):
            for k in range(self.load_n(i)):
                tr = L["pour"] + 0.18 + 0.035 * k
                self.into_hop.append(tr + ballistic_land(HOP_TOP - 80, HOP_THROAT - 30))
        self.into_hop.sort()
        self.release, last = [], -9.0
        for ta in self.into_hop:
            tr = max(ta + 0.25, last + FEED)
            self.release.append(tr)
            last = tr
        self.fall_nip = ballistic_land(HOP_THROAT, NIP_Y - 18)
        self.milled = [tr + self.fall_nip for tr in self.release]
        self.n_total = len(self.milled)
        self.tie = (self.milled[-1] + 1.4, self.milled[-1] + 3.8)
        self.sack_lift = (self.tie[1] + 1.2, self.tie[1] + 2.1)
        self.w_off = (self.sack_lift[1] + 0.2, self.sack_lift[1] + 3.2)
        self.dur = self.w_off[1] + 1.0
        mv = Moves(2900.0, G)
        st = self.oak.stubs
        mv.hop(1.0, st[0][0] - 10, st[0][1], apex=50)
        mv.hop(1.7, st[1][0] - 10, st[1][1], apex=50)
        mv.hop(2.4, 2985.0, self.oak.branch_y(2985.0), apex=40)
        for L in (0, 1):
            for tb in bounce_t[L]:
                mv.bounces.append((tb - 0.62, 0.62, 30.0))
        mv.x, mv.y = 2985.0, self.oak.branch_y(2985.0)
        mv.hop(17.2, st[1][0] - 10, st[1][1], apex=30)
        mv.hop(17.9, st[0][0] - 10, st[0][1], apex=30)
        mv.hop(18.6, 3020.0, G, apex=30)
        mv.walk(19.4, 2900.0, G, step=140)
        self.sp = mv
        self.stats = {"acorns_milled": self.n_total}

    def load_n(self, i):
        return sum(1 for f in self.falls if f[2] == i)

    def aside_moods(self, t):
        return ["ooh", "mm", "hehe", "aww", "hm"]

    # ----- state -----

    def basket_n(self, t):
        n = self.start_n + sum(1 for (tl, L) in self.land if tl <= t)
        for i, L in enumerate(self.loads):
            if t >= L["pour"] + 0.18:
                n -= min(self.load_n(i), int((t - L["pour"] - 0.18) / 0.035) + 1)
        return max(0, n)

    def hopper_n(self, t):
        return sum(1 for ta in self.into_hop if ta <= t) - sum(1 for tr in self.release if tr <= t)

    def flour_rate(self, t):
        r = 0.0
        for tm in self.milled:
            d = t - tm
            if -0.05 < d < 0.9:
                r += math.exp(-d * 2.2) if d > 0 else 0.4
        return min(1.0, r * 0.7)

    def sack_fill(self, t):
        return min(1.0, 0.03 + sum(1 for tm in self.milled if tm + 0.35 <= t) / self.n_total)

    def basket_pose(self, t):
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k) if m is not None else (PARK, self.basket_y)
        for i, L in enumerate(self.loads):
            a, p, b = L["lift"], L["pour"], L["back"]
            over = (HX + 30, HOP_TOP - 70)
            if a <= t < b + 0.8:
                if t < p:
                    u = smootherstep(seg(t, a, p))
                    return lerp(hx, over[0], u), lerp(hy, over[1], u) - 60 * math.sin(math.pi * u), 0.0, "held"
                if t < b:
                    return over[0], over[1], -1.9 * smoothstep(seg(t, p, p + 0.3)) * (1 - smoothstep(seg(t, b - 0.3, b))), \
                        "held"
                u = smootherstep(seg(t, b, b + 0.8))
                if i < len(self.loads) - 1:
                    return lerp(over[0], hx, u), lerp(over[1], hy, u) - 50 * math.sin(math.pi * u), 0.0, "held"
                return lerp(over[0], 2585.0, u), lerp(over[1], G, u) - 50 * math.sin(math.pi * u), 0.0, "held"
        if t >= self.loads[-1]["back"] + 0.8:
            return 2585.0, G, 0.0, "floor"
        return hx, hy, 0.0, "head"

    def site(self, t):
        st = done_site()
        st["hopper_n"] = self.hopper_n(t)
        st["sack"] = None if t >= self.sack_lift[0] else (self.sack_fill(t), smoothstep(seg(t, self.tie[0] + 0.5, self.tie[1])))
        st["pile"] = 16
        return st

    # ----- camera (slow: few moves, each over several seconds) -----

    def target(self, t):
        L0, L1 = self.loads
        keys = [(0.0, 2740.0, None, 0.95), (L0["w_go"], 2740.0, None, 0.95), (L0["lift"] + 0.5, 2480.0, None, 1.15),
                (L0["back"] + 1.0, 2480.0, None, 1.15), (L1["at_branch"] + 2.0, 2740.0, None, 1.0),
                (L1["w_go"] + 0.5, 2740.0, None, 1.0), (L1["lift"] + 0.5, 2480.0, None, 1.15),
                (L1["back"] + 2.5, 2330.0, G - 320.0, 1.5), (self.tie[0] - 0.5, 2330.0, G - 320.0, 1.5),
                (self.tie[0] + 2.5, 2360.0, None, 1.15), (self.dur, 2600.0, None, 1.0)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._wheels(t, dt)
        self._hans(t, dt)
        self._digs(t, dt)
        self._twigs(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._particles(t, dt)
        self.leaves(0.05)
        self._sounds(t)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        keys = [(0.0, BX)]
        for i, L in enumerate(self.loads):
            keys += [(L["w_go"], keys[-1][1]), (L["arrive"], PARK)]
            if i < len(self.loads) - 1:
                keys += [(L["back"] + 0.8, PARK), (self.loads[i + 1]["at_branch"], BX)]
        keys += [(self.tie[0], PARK), (self.tie[1], SACK_X + 4), (self.w_off[0], SACK_X + 4), (self.w_off[1], 3060.0)]
        x = px(keys, t)
        m.punch = 0.8 if self.sack_lift[0] - 0.3 <= t < self.sack_lift[1] + 0.2 else 0.0
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        reach = []
        bx, by, ang, where = self.basket_pose(t)
        if where == "held":
            reach = [(bx - 50, by - 24), (bx + 50, by - 24)]
        a, b = self.tie
        if a <= t < b:
            f = self.sack_fill(t)
            ny = G - 76 - 70 * f + 10
            ph = (t - a) * 8
            reach = [(SACK_X + 30 * math.cos(ph), ny + 6 * math.sin(ph)), (SACK_X - 26, ny + 14)]
        self.reach["tentacles"] = reach
        x = px([(0.0, HANS_MILL), (a - 0.8, HANS_MILL), (a, HANS_MILL - 40), (b, HANS_MILL - 40), (b + 0.8, HANS_MILL)], t)
        self.place(m, x, t, dt)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        a, b = self.tie
        x = px([(0.0, SACK_X - 100), (a - 2.0, SACK_X - 100), (a - 1.0, SACK_X - 95), (b, SACK_X - 95), (b + 0.8, DIGS_MILL - 40)], t)
        m.dig = 0.5 + 0.5 * math.sin((t - a) * 9) if a - 1.4 <= t < a - 0.6 else (0.6 if a - 0.6 <= t < b else 0.0)
        self.place(m, x, t, dt)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run = 0.0
        x = px([(0.0, 3330.0), (self.dur - 6.0, 3330.0), (self.dur - 2.0, 3000.0)], t)
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y, sq = self.sp.at(t)
        m.spring = sq
        self.place(m, x, t, dt, y=y)

    def branch_dip(self, t):
        x, y, sq = self.sp.at(t)
        on = abs(y - self.oak.branch_y(x)) < 60 and x < OAK_X - 60 and 2.2 < t
        d = 0.0
        if on:
            d = 6.0
            for L in (0, 1):
                for tb in self.bounce_t[L]:
                    dd = t - tb
                    if 0 <= dd < 1.2:
                        d += 16.0 * math.exp(-dd * 4.5) * math.cos(dd * 16)
        return d

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        x = px([(0.0, 2780.0), (11.0, 2780.0), (14.0, 2190.0), (18.0, 2190.0), (21.0, 2780.0), (26.0, 2780.0),
                (29.0, 2190.0)], t)
        y = px([(0.0, G - 470.0), (11.0, G - 470.0), (14.0, G - 330.0), (18.0, G - 330.0), (21.0, G - 470.0),
                (26.0, G - 470.0), (29.0, G - 330.0)], t)
        m.lamp = 1.15
        self.place(m, x, t, dt, y=y + 10 * math.sin(t * 1.3))

    # ----- particles + sounds -----

    def _particles(self, t, dt):
        P = self.s.particles
        r = self.flour_rate(t)
        if r > 0.3 and P.rng.uniform() < 0.25 * r:
            P.burst(SACK_X + P.rng.uniform(-20, 20), G - 80 - 70 * self.sack_fill(t), 1, F.FLOUR * 0.9, 60, 0.9, 3,
                    g=-30, spread=1.4)

    def _sounds(self, t):
        s = self.s
        if self.crossed(0.1):
            self.fx(t, "gurgle", self.dur, 0.05, WX, G)
            self.fx(t, "rush", self.dur, 0.03, HX, NIP_Y)
        if self.crossed(0.6):
            self.chat(t, "springs", "hey", icon="acorn")
        for i, (tl, L) in enumerate(self.land):
            if self.crossed(tl):
                self.hit(t, "clack", s.note(i % 5 + 2, 0), 0.08, BX, self.basket_y)
        for i, L in enumerate(self.loads):
            if self.crossed(L["pour"] + 0.2):
                self.fx(t, "rustle", 0.7, 0.07, HX, HOP_TOP)
                for q in range(5):
                    self.hit(t + 0.1 + q * 0.08, "clack", s.note(5 - q, 0), 0.05, HX, HOP_TOP)
            if self.crossed(L["lift"] + 0.1):
                self.chat(t, "tentacles", "mm", icon="auto" if i else None)
        for k, tm in enumerate(self.milled):
            if self.crossed(tm):
                self.hit(t, "thud", 45 + (k % 3) * 2, 0.05, HX, NIP_Y)
        if self.crossed(self.milled[0] + 0.6):
            self.chorus(t, ["digger", "lantern"], "ooh", gap=0.3, icon="sparkle")
        for L in (0, 1):
            for b, tb in enumerate(self.bounce_t[L]):
                if self.crossed(tb - 0.6):
                    self.hit(t, "boing", 62 + b * 2, 0.12, 2985, G - 500)
                if self.crossed(tb - 0.05):
                    self.fx(t, "rustle", 0.6, 0.06, 2985, G - 520)
            if self.crossed(self.bounce_t[L][-1] + 0.8):
                self.chat(t, "springs", "wee" if L == 0 else "hehe")
        if self.crossed(self.tie[0] + 0.2):
            self.fx(t, "rustle", 2.0, 0.06, SACK_X, G - 150)
        if self.crossed(self.tie[1]):
            self.hit(t, "pluck", 67, 0.12, SACK_X, G - 150)
            self.chat(t + 0.2, "digger", "yay")
        if self.crossed(self.sack_lift[1] + 0.1):
            self.chat(t, "wheels", "huff")
        if self.crossed(self.w_off[0] + 0.6):
            self.chorus(t, ["teeth", "springs"], "hey", gap=0.3, icon="bread")

    # ----- drawing -----

    def behind_stones(self, c, t, st):
        for tr in self.release:
            u = t - tr
            if 0 <= u < self.fall_nip:
                F.acorn(c, HX, HOP_THROAT + 0.5 * GRAVITY * u * u, 8.5, u * 6)
        if st["sack"] is not None:
            F.flour_stream(c, self.s, HX, NIP_Y + 10, G - 76 - 70 * st["sack"][0], self.flour_rate(t), t)

    def ground_things(self, c, t, st):
        for i, L in enumerate(self.loads):                   # the acorns tumbling into the hopper
            bx, by, ang, _ = self.basket_pose(L["pour"] + 0.5)
            mx, my = F.basket_mouth(bx, by, -1.9)
            for k in range(self.load_n(i)):
                tr = L["pour"] + 0.18 + 0.035 * k
                u = t - tr
                T = ballistic_land(my, HOP_THROAT - 30)
                if 0 <= u < T:
                    F.acorn(c, lerp(mx, HX + ((k * 37) % 60 - 30) * 0.8, u / T), my + 0.5 * GRAVITY * u * u, 8.5, u * 5 + k)
        bx, by, ang, where = self.basket_pose(t)
        if where == "floor":
            F.basket(c, bx, by, 0)

    def branch_things(self, c, t):
        o = self.oak
        dip = self.branch_dip(t)
        hang = [(x, r) for (x, r), (tr, _, _) in zip(self.hang, self.falls) if t < tr]
        o.draw_branch(c, t, dip, hang)
        for (tr, x, L), (tl, _) in zip(self.falls, self.land):
            if tr <= t < tl:
                y0 = o.branch_y(x) + 26
                F.acorn(c, x, y0 + 0.5 * GRAVITY * (t - tr) ** 2, 9.5, (t - tr) * 4)

    def sack_pos(self, t):
        a, b = self.sack_lift
        if t < a:
            return None
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k) if m is not None else (SACK_X, G - 186)
        u = smootherstep(seg(t, a, b))
        return lerp(SACK_X, hx, u), lerp(G, hy, u)

    def held(self, c, kind, t):
        if kind == "tentacles":
            bx, by, ang, where = self.basket_pose(t)
            if where == "held":
                F.basket(c, bx, by, self.basket_n(t), ang)

    def carried(self, c, t):
        bx, by, ang, where = self.basket_pose(t)
        if where == "head":
            F.basket(c, bx, by, self.basket_n(t), ang)
        lifted = self.sack_pos(t)
        if lifted is not None:
            F.sack(c, 0, 0, 1.0, 1.0, lift=lifted)


# ====================================================================== the clearing by the treehouse village

TABLE = (3950.0, 5050.0)                              # the feast table: ten cross planks on two fallen logs
NPL, PW = 10, 110.0
LOG_TOP_B, LOG_TOP_F, LOG_R = G - 64.0, G - 24.0, 30.0
YB, YF = LOG_TOP_B - 9.0, LOG_TOP_F - 9.0             # plank tops at the back and front log
BEHIND = G - 14.0                                     # where the diners stand (behind the back log)
SEATS = [TABLE[0] + 69.0 + 137.5 * i for i in range(8)]
SEAT_OF = {"lantern": 0, "tentacles": 2, "teeth": 3, "springs": 4, "wheels": 6, "digger": 7}
BUNNY_SEAT = (1, 5)
PLATE_Y, CUP_Y = lerp(YB, YF, 0.72), lerp(YB, YF, 0.25)
FOOD_X = [4100.0 + 170.0 * i for i in range(6)]
FOOD_Y = lerp(YB, YF, 0.5) + 4
FOOD_KIND = ["loaf", "pie", "loaf", "loaf", "pie", "loaf"]
BIRD_X = [(SEATS[2 * b] + SEATS[2 * b + 1]) / 2 for b in range(4)]
HEDGE_SPOT, HEDGE_PLATE = (3850.0, G + 30.0), (3912.0, G + 44.0)
LAMP_TREES = (3790.0, 5210.0)
LAMPS = [4040.0 + 184.0 * k for k in range(6)]
ROPE_Y, ROPE_SAG = G - 430.0, 70.0
OWL_XY = (5292.0, G - 474.0)
# act 2's stations
ROUGH_X = 5240.0                                      # the rough boards, stacked
WF = 5345.0                                           # Wheels feeds the boards from here
STOP, PLANK_L = 5420.0, 170.0                         # the stop block; every plank is cut PLANK_L long
CUT = STOP + PLANK_L
SH_TOP = G - 104.0                                    # sawhorse top
WOODPILE, WOOD_X = 5760.0, 5930.0                     # firewood: the pile, the stack by the oven
OVEN_X, OVEN_R, OVEN_H = 6200.0, 180.0, 230.0
OVEN_RINGS = 4                                        # thick coils of clay, each laid by Hans
DIGS_PRESS = 6440.0
PIT = (6850.0, 7050.0)
BENCH = (6300.0, 6720.0)
BT = G - 80.0                                         # bench top (= the bread board's top)
BOARD = (6400.0, 6700.0)
BOWL_X = 6345.0
ITEM_X = [6425.0 + 52.0 * i for i in range(6)]        # the dough pieces / loaves on the board, evenly spaced
ITEM_KIND = FOOD_KIND
SACK_V, JUG_V = 6770.0, 6740.0
POT_X = 6240.0
LOAF_R, PIE_R = 22.0, 24.0
# inside the oven: two rows of three (the back row smaller: it is further in)
PLATE_STUMP, STUMP_TOP = (3780.0, G), 64.0              # the plates and cups wait on a stump left of the table
HANS_OVEN = 5990.0                                    # Hans stands here to lay the oven's coils
SHOVEL_DX = 118 * K * 1.6
CARRY = -0.6                                          # Digs' dig value with the shovel held up level (to carry)                             # Digs' x minus his shovel blade's x
OVEN_SLOTS = [(OVEN_X - 44 + 44 * (i % 3), G - 40 if i < 3 else G - 16, 0.66 if i < 3 else 0.82) for i in range(6)]


def slot_x(j):
    """Middle of plank slot j (slot 0 at the right end of the table)."""
    return TABLE[1] - PW * (j + 0.5)


def rope_y(x):
    u = (x - LAMP_TREES[0] - 20) / (LAMP_TREES[1] - LAMP_TREES[0] - 40)
    return ROPE_Y + ROPE_SAG * 4 * u * (1 - u)


def ragged_of(i):
    rs = np.random.default_rng(80 + i)
    return float(rs.uniform(18, 46))


def row_y(x):
    """The row a Keeper walks in: the front (G) until they come round the table's right end, then behind it."""
    return G + (BEHIND - G) * smoothstep(min(1.0, max(0.0, (TABLE[1] + 140 - x) / 100.0)))


def draw_stack(c, x, y, plates, cups):
    """A stack of plates (bottom at y) with the cups standing beside it."""
    for k in range(plates):
        c.polygon(ellipse(x, y - k * 5, 30, 8, 16), F.PLATE * (0.8 + 0.02 * k))
    for k in range(cups):
        F.cup(c, x + 44 + (k % 2) * 4, y - 2 - (k // 2) * 22)


def draw_item(c, kind, x, y, bake, eaten=0.0, scored=0.0, filled=1.0, flat=1.0, sc=1.0):
    if kind == "loaf":
        F.loaf(c, x, y, bake, eaten, scored, LOAF_R * sc)
    else:
        F.pie(c, x, y, bake, eaten, filled, PIE_R * sc)


class VillageAct(FeastAct):
    """Acts 2-4 share the clearing to the right of the treehouse village. Each act describes the world it shows with
    world(t) (what is built, set, lit, baking) and draws its own moving things; this class draws the rest in depth
    order: the village and trees, the lantern string, the stations at the back, the diners behind the table, the table
    and what is on it, the bench and the oven, then everyone in front.

    Calmer pace (owner after FK0005's first cut and again after its re-render: rushed, jumpy): these acts run
    STRETCH times slower than their schedules are written (FeastAct)."""
    STRETCH = 1.3

    def world(self, t):
        return dict(planks=[0.0] * NPL, rough=0, offcuts=0, rings=OVEN_RINGS, ring_u=0.0, chimney=1.0, wood=1.0,
                    fire=1.0, lamps=[1.0] * 6, plates=9, cups=8, food=[], bowl=None, board_items=None,
                    oven_items=[], sawhorses=False, logs_in_pile=0, wood_stack=0, level=None, board_on_bench=True,
                    sack=1.0, jug=(JUG_V, G, 0.0), birds_home=(0, 0, 0, 0), pot=True)

    def behind(self, kind):
        """Is this Keeper behind the table (drawn before it)?"""
        m = self.m(kind)
        return m is not None and m.y < G - 6 and kind not in self.on_top

    on_top = ()

    def diners_behind(self, c, t):
        """Animals sitting behind the table (drawn with the Keepers behind it)."""

    def animals_front(self, c, t):
        """Animals walking about in front."""

    def carried(self, c, t):
        """What is held up: on Wheels' head, on Digs' shovel, in the air."""

    def held(self, kind, c, t):
        """Drawn just before a Keeper (so Hans' tentacles wrap over it)."""

    def table_extra(self, c, t):
        """Things on the table drawn by the act (a plank being laid, served pieces)."""

    def oven_inside(self, c, t, w):
        for (kind, x, y, sc, bake, scored, filled) in w["oven_items"]:
            draw_item(c, kind, x, y, bake, 0.0, scored, filled, sc=sc)

    def draw(self, c, t):
        return self._draw(c, t)

    def _draw(self, c, t):
        s = self.s
        w = self.world(t)
        self.night.draw(s, c, t)
        self.night.ground_slab(s, c)
        for j, x in enumerate((-400, 200, 7350, 7800, 8300)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        self.draw_village(c, t, peek=1.0, birds_home=w["birds_home"])
        for j, x in enumerate(LAMP_TREES):
            if s.visible(x - 300, x + 300):
                tree(c, x, G, 700 + 40 * j, 1700 + j)
        if s.visible(OWL_XY[0] - 200, OWL_XY[0] + 200):
            c.line(LAMP_TREES[1] + 10, OWL_XY[1] + 10, OWL_XY[0] + 50, OWL_XY[1] - 4, TRUNK, 12)
            F.owl(c, s, OWL_XY[0], OWL_XY[1], t + self.t0)
        if s.visible(LAMP_TREES[0], LAMP_TREES[1]):
            F.lantern_string(c, s, t, LAMP_TREES[0] + 20, LAMP_TREES[1] - 20, ROPE_Y, ROPE_SAG, LAMPS, w["lamps"])
        behind = [k for k in KEEPERS if self.behind(k)]
        self.draw_monsters(c, t, kinds=behind, before=lambda kind: self.held(kind, c, t))   # behind everything
        self.diners_behind(c, t)
        self._stations_back(c, t, w)
        self.glo_light(c, 0.8)
        self._table(c, t, w)
        self.table_extra(c, t)
        self._stations_front(c, t, w)
        front = [k for k in KEEPERS if k not in behind]
        self.draw_monsters(c, t, kinds=front, before=lambda kind: self.held(kind, c, t))
        self.animals_front(c, t)
        self.carried(c, t)

    def _stations_back(self, c, t, w):
        s = self.s
        if not s.visible(5000, 7200):
            return
        # the firewood pile and the stack by the oven
        for k in range(w["logs_in_pile"]):
            row, col = divmod(k, 3)
            x, y = WOODPILE - 40 + col * 40 + (row % 2) * 20, G - 12 - row * 22
            c.circle(x, y, 12, F.LOG_END)
            c.circle(x, y, 12, F.LOG * 0.8, False, 3)
        for k in range(w["wood_stack"]):
            row, col = divmod(k, 3)
            x, y = WOOD_X - 40 + col * 40 + (row % 2) * 20, G - 12 - row * 22
            c.circle(x, y, 12, F.LOG_END)
            c.circle(x, y, 12, F.LOG * 0.8, False, 3)
        # the clay pit: a hollow of red-brown clay
        c.polygon(ellipse((PIT[0] + PIT[1]) / 2, G + 8, (PIT[1] - PIT[0]) / 2, 22, 30), F.CLAY_WET * 0.8)
        c.polygon(ellipse((PIT[0] + PIT[1]) / 2, G + 4, (PIT[1] - PIT[0]) / 2 - 16, 12, 30), F.CLAY_WET)
        if w["sawhorses"]:
            for k in range(w["rough"]):                    # rough boards, stacked
                F.plank_side(c, ROUGH_X, G - k * 11, PLANK_L, ragged=ragged_of(9 - k) if k < 10 else 30)
            for x in (STOP + 30, CUT - 20):
                F.sawhorse(c, x, SH_TOP, G)
            rect(c, STOP - 10, SH_TOP - 34, STOP, SH_TOP + 4, TRUNK * 1.3)   # the stop block
            c.line(CUT, SH_TOP - 3, CUT, SH_TOP + 5, np.array([236, 232, 220]), 2)
            for k in range(w["offcuts"]):                  # offcuts on the ground
                c.polygon([(CUT + 14 + 6 * k, G + 8 + 2 * (k % 3)), (CUT + 46 + 6 * k, G + 8 + 2 * (k % 3)),
                           (CUT + 46 + 6 * k, G + 18 + 2 * (k % 3)), (CUT + 14 + 6 * k, G + 18 + 2 * (k % 3))],
                          PR.WOOD * (0.85 + 0.03 * (k % 4)))
        oi = lambda c: self.oven_inside(c, t, w)
        F.draw_oven(c, s, OVEN_X, G, OVEN_R, OVEN_H, w["rings"], w["ring_u"], w["chimney"], w["wood"], w["fire"],
                    t + self.t0, items=oi, n=OVEN_RINGS)
        if w["fire"] > 0.3 and w["chimney"] >= 1:           # a thin curl of smoke from the chimney
            cx, cy = F.chimney_top(OVEN_X, G, OVEN_R, OVEN_H)
            for k in range(7):
                u = ((t * 0.25) + k / 7.0) % 1.0
                c.circle(cx + 18 * math.sin(u * 5 + k) + 30 * u, cy - 20 - u * 260, 10 + 22 * u,
                         np.array([60, 58, 62]) * (1 - u) * 0.9 * w["fire"] + np.array([14, 16, 24]) * u)

    def _table(self, c, t, w):
        s = self.s
        if not s.visible(TABLE[0] - 200, TABLE[1] + 200):
            return
        sx, sy = PLATE_STUMP                              # the plate stump (and the stack until Hans takes it)
        rect(c, sx - 40, sy - STUMP_TOP, sx + 40, sy, TRUNK * 1.05)
        c.polygon(ellipse(sx, sy - STUMP_TOP, 40, 9, 18), np.array([186, 148, 104]))
        if w.get("stack", 0):
            draw_stack(c, sx, sy - STUMP_TOP - 4, 9, 8)
        F.log_rail(c, TABLE[0] - 30, TABLE[1] + 30, LOG_TOP_B, LOG_R)
        for j in range(NPL):
            pr = w["planks"][j]
            if pr is not None:
                F.plank_laid(c, slot_x(j) - PW / 2 + 2, slot_x(j) + PW / 2 - 2, YB, YF, 1.0 - 0.025 * (j % 3), pr)
        F.log_rail(c, TABLE[0] - 30, TABLE[1] + 30, LOG_TOP_F, LOG_R)
        for j in range(NPL):                               # the front edges, over the front log
            pr = w["planks"][j]
            if pr is not None:
                x0 = slot_x(j) - PW / 2 + 2
                c.polygon([(x0 + 6, YF + pr), (x0 + PW - 4 + 6 - 4, YF + pr), (x0 + PW - 4 + 6 - 4, YF + 9 + pr),
                           (x0 + 6, YF + 9 + pr)], PR.WOOD * 0.72)
        for i in range(min(w["cups"], 8)):
            F.cup(c, SEATS[i] + 42, CUP_Y)
        self.birds_on_table(c, t)
        for (kind, x, y, bake, eaten) in w["food"]:
            draw_item(c, kind, x, y, bake, eaten)
        for i in range(min(w["plates"], 8)):
            F.plate(c, SEATS[i], PLATE_Y)
        if w.get("hedge_plate", w["plates"] >= 9):
            F.plate(c, *HEDGE_PLATE)

    def birds_on_table(self, c, t):
        pass

    def _stations_front(self, c, t, w):
        s = self.s
        if not s.visible(BENCH[0] - 200, BENCH[1] + 400):
            return
        PR.bench(c, BENCH[0], BENCH[1], BT, G)
        if w["board_on_bench"]:
            F.stump_board(c, BOARD[0], BOARD[1], BT)
        if w["bowl"] is not None:
            F.bowl(c, *w["bowl"])
        if w["board_items"] is not None:
            for (kind, x, y, bake, scored, filled, flat) in w["board_items"]:
                if kind == "dough":
                    c.polygon(ellipse(x, y - 12 * flat, 20 * (2 - flat), 12 * flat, 20), F.DOUGH)
                else:
                    draw_item(c, kind, x, y, bake, 0.0, scored, filled)
        if w["sack"] is not None:
            F.sack(c, SACK_V, G, w["sack"], 1.0 if w["sack"] >= 0.99 else 0.0)
        jx, jy, ja = w["jug"]
        F.jug(c, jx, jy, ja)
        if w["pot"]:
            c.polygon([(POT_X - 30, G - 44), (POT_X + 30, G - 44), (POT_X + 24, G), (POT_X - 24, G)], np.array([90, 70, 60]))
            c.polygon(ellipse(POT_X, G - 44, 30, 7, 16), F.PIE_FILL)
            c.line(POT_X - 34, G - 44, POT_X + 34, G - 44, np.array([70, 54, 46]), 5)

    # ----- helpers for the acts -----

    def board_items_default(self, bake=0.0):
        return [(ITEM_KIND[i], ITEM_X[i], BT - 8, bake, 1.0 if ITEM_KIND[i] == "loaf" else 0.0, 1.0, 1.0)
                for i in range(6)]


# ====================================================================== TABLE

CY2 = 2.6                                             # one plank every CY2 s


class FeastTableAct(VillageAct):
    """The long table and the clay oven, then the table set and the lanterns lit; everyone strolls to the oven.

    Owner after FK0005's re-render: Hans' tentacle lagged behind the clay (the coil went round by itself, then the
    tentacle followed), a plank being laid slid under the front log and popped on top, Glo carried a spirit level
    about for a minute, and the act jumped between the saw, the oven and the table with dip-to-black cuts. Now: one
    calm wide shot of the saw and the oven, then the oven close up while Hans lays every coil himself (his tentacle
    tip is the end of the coil being laid, a second one smooths it just behind), then the camera follows Hans to the
    table; Glo just lights the way. The lanterns and the plates are done here (no cut away from the baking later)."""
    name = "table"
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.cyc = [2.2 + CY2 * i for i in range(NPL)]   # plank i: fed, cut, lifted onto Wheels' head
        # Hans: two trips with firewood logs, then he lays every coil of clay Digs brings from the pit
        self.log_trips = ((0.4, 2.3), (2.9, 4.8))
        self.ring_t = [8.0 + 6.4 * k for k in range(OVEN_RINGS + 1)]   # dig start of each trip (the last: chimney)
        _, _, _, last = self.ring_times(OVEN_RINGS)
        self.hans_go = (last + 0.4, last + 8.4)           # Hans walks round to the table
        self.tl0 = self.hans_go[1] + 0.2
        self.tl = [self.tl0 + 1.7 * j for j in range(NPL)]
        self.wood_saw = [(self.tl0 + 1.0, self.tl0 + 2.8), (self.tl0 + 3.2, self.tl0 + 5.0)]
        self.wood_in = [(self.tl0 + 5.6, self.tl0 + 7.4), (self.tl0 + 7.8, self.tl0 + 9.6)]
        # then Glo lights the six lanterns (left to right) while Hans sets the hedgehog's plate and the eight places
        t_set = self.tl[-1] + 3.6
        self.lamp_t = [t_set + 0.2 + 1.8 * k for k in range(6)]
        self.pick_t = (t_set, t_set + 0.8)                # Hans lifts the stack of plates and cups off the stump
        self.place_plates = [t_set + 1.2 + 1.3 * q for q in range(9)]   # q 0: the hedgehog's, then seats 0..7
        self.walk = (self.place_plates[-1] + 2.0, self.place_plates[-1] + 15.0)   # everyone strolls to the oven
        self.dur = self.walk[1] + 0.5
        # Springs: stomps the clay soft, then bounces each plank flat
        mv = Moves(6960.0, G)
        t = 3.0
        while t < self.ring_t[-1]:
            mv.bounce(t, h=42, d=0.6)
            t += 0.92
        mv.walk(t + 0.6, 5130.0, G, step=210)
        mv.hop(self.tl[0] + 0.9, slot_x(0), FOOD_Y - 4, apex=50)
        for j in range(NPL):
            if j:
                mv.hop(self.tl[j] + 0.9, slot_x(j), FOOD_Y - 4, apex=36)
            mv.bounce(mv.t + 0.06, h=26, d=0.5)
        mv.hop(self.tl[-1] + 2.0, TABLE[0] - 70, G, apex=30)
        mv.walk(mv.t + 0.4, 5250.0, G, step=220)
        self.sp = mv
        ln = [PLANK_L] * NPL                              # every plank cut between the stop block and the line
        gaps = [slot_x(j) - slot_x(j + 1) for j in range(NPL - 1)]
        self.stats = {"planks": NPL, "planks_even": bool(max(ln) - min(ln) < 0.5 and max(gaps) - min(gaps) < 0.5),
                      "table_level": bool(abs(YB - (LOG_TOP_B - 9)) < 0.5 and abs(YF - (LOG_TOP_F - 9)) < 0.5),
                      "oven_rings": OVEN_RINGS,
                      "lanterns_even": bool(max(np.diff(LAMPS)) - min(np.diff(LAMPS)) < 0.5),
                      "settings_even": bool(max(np.diff(SEATS)) - min(np.diff(SEATS)) < 0.5)}
        self._tw_dx = None

    def aside_moods(self, t):
        return ["hm", "hehe", "ooh", "mm", "aww"]

    # ----- plank states -----

    def plank_state(self, i, t):
        """Plank i (the one for slot i): ('rough'), ('feed', x, y), ('saw', cut 0..1), ('lift', x, y), ('head',),
        ('lay', u), ('laid', press). Slot 0 is laid first, so its plank is cut last: it is on top of Wheels' stack."""
        a = self.cyc[NPL - 1 - i]
        if t < a:
            return ("rough",)
        if t < a + 0.8:
            u = smootherstep(seg(t, a, a + 0.8))
            x0, y0 = ROUGH_X, G - i * 11
            x1, y1 = STOP + PLANK_L / 2, SH_TOP
            return ("feed", lerp(x0, x1 + 30, u) - 30 * smoothstep(seg(u, 0.75, 1.0)), lerp(y0, y1, u) - 40 * math.sin(math.pi * u))
        if t < a + 2.0:
            return ("saw", smoothstep(seg(t, a + 0.95, a + 1.85)))
        if t < a + 2.55:
            u = smootherstep(seg(t, a + 2.0, a + 2.55))
            hx, hy = self.head_xy(i)
            return ("lift", lerp(STOP + PLANK_L / 2, hx, u), lerp(SH_TOP, hy, u) - 30 * math.sin(math.pi * u))
        tl = self.tl[i]
        if t < tl:
            return ("head", i)
        if t < tl + 0.9:
            return ("lay", smootherstep(seg(t, tl, tl + 0.9)))
        return ("laid", self.press(i, t))

    def head_xy(self, i):
        """Plank i on Wheels' stack (the first cut at the bottom)."""
        m = self.m("wheels")
        return m.x, m.y - HEAD_W * m.k - 11 * (NPL - 1 - i)

    def press(self, j, t):
        out = 0.0
        land = self.tl[j] + 0.9
        for (ts, jp) in self.sp.hops:
            if abs(jp.x1 - slot_x(j)) < 1 and jp.y1 < G - 20:
                land = ts + jp.dur
        for b in (land, land + 0.06 + 0.5):
            out = max(out, 3.0 * math.exp(-((t - b) / 0.1) ** 2))
        return out

    def ring_times(self, k):
        d = self.ring_t[k]
        return d, d + 1.0, d + 2.6, d + 4.4                # dig, leave the pit, Hans starts laying, coil laid

    def coil_front(self, k, u):
        """Where the end of coil k is when a fraction u of it is laid (round the dome from the left)."""
        hh = OVEN_H / OVEN_RINGS
        h = (k + 0.5) * hh
        half = OVEN_R * math.sqrt(max(0.0, 1 - (h / OVEN_H) ** 2))
        return OVEN_X - half + 2 * half * u, G - h

    def shovel_xy(self):
        dg = self.m("digger")
        return (dg.x - SHOVEL_DX, G - 80) if dg is not None else (DIGS_PRESS - SHOVEL_DX, G - 80)

    def plate_xy(self, q):
        return HEDGE_PLATE if q == 0 else (SEATS[q - 1], PLATE_Y)

    def stack_xy(self):
        m = self.m("tentacles")
        return (m.x + 85, G - 170) if m is not None else (PLATE_STUMP[0], PLATE_STUMP[1] - STUMP_TOP)

    def setting_pos(self, q, t):
        """Plate q (and its cup) on the way from the stack in Hans' tentacles to its place: (x, y, u) or None."""
        p = self.place_plates[q]
        if not (p <= t < p + 0.8):
            return None
        u = smootherstep(seg(t, p, p + 0.8))
        sx, sy = self.stack_xy()
        tx, ty = self.plate_xy(q)
        return lerp(sx, tx, u), lerp(sy, ty - 6, u) - 50 * math.sin(math.pi * u), u

    def world(self, t):
        w = super().world(t)
        planks = []
        for j in range(NPL):
            st = self.plank_state(j, t)
            planks.append(st[1] if st[0] == "laid" else None)
        rings, ring_u = 0, 0.0
        for k in range(OVEN_RINGS):
            d, l, p0, p1 = self.ring_times(k)
            if t >= p1:
                rings = k + 1
            elif t >= p0:
                ring_u = seg(t, p0, p1)
                break
        d, l, p0, p1 = self.ring_times(OVEN_RINGS)
        trips_in = sum(1 for (a, b) in self.wood_in if t >= b - 0.3)
        picks = sum(1 for (a, b) in self.log_trips if t >= a + 0.6)
        drops = sum(1 for (a, b) in self.log_trips if t >= b)
        set_n = sum(1 for p in self.place_plates if t >= p + 0.8)
        w.update(planks=planks, rough=sum(1 for i in range(NPL) if self.plank_state(i, t)[0] == "rough"),
                 offcuts=sum(1 for i in range(NPL) if t >= self.cyc[i] + 1.95), rings=rings, ring_u=ring_u,
                 chimney=seg(t, p0, p1), wood=trips_in / 2.0, fire=0.0,
                 lamps=[smoothstep(seg(t, a + 0.35, a + 0.8)) for a in self.lamp_t],
                 plates=max(0, set_n - 1), cups=max(0, set_n - 1), hedge_plate=set_n >= 1,
                 stack=9 if t < self.pick_t[0] + 0.5 else 0,
                 sawhorses=True, logs_in_pile=6 - 3 * picks, wood_stack=max(0, 3 * drops - 3 * trips_in),
                 board_items=None, bowl=(BOWL_X, BT, 0.0, 0.0, 0.0), sack=0.999, birds_home=(1, 1, 1, 1))
        return w

    # ----- camera: a wide shot of the saw and the oven, the oven close up, follow Hans to the table, the whole
    # table for the lanterns and the plates, then a slow pan with everyone to the oven -----

    def target(self, t):
        keys = [(0.0, 5800.0, None, 0.95), (4.5, 5800.0, None, 0.95), (9.0, 6260.0, None, 1.2),
                (self.hans_go[0], 6260.0, None, 1.2), (self.tl0, 5000.0, None, 1.15),
                (self.tl[-1] + 1.1, slot_x(NPL - 1) + 40, None, 1.15), (self.pick_t[0] + 1.0, 4450.0, G - 330.0, 1.0),
                (self.walk[0], 4450.0, G - 330.0, 1.0), (self.walk[1], 6150.0, None, 1.3)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._wheels(t, dt)
        self._twigs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._digs(t, dt)
        self._glo(t, dt)
        self._particles(t)
        self.leaves(0.04)
        self._sounds(t)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        e = self.tl[-1]
        keys = [(0.0, WF), (self.cyc[-1] + 2.7, WF), (self.tl0 - 0.4, slot_x(0) + 150)]
        for j in range(NPL):
            keys += [(self.tl[j] + 0.75, slot_x(j) + 150)]
        keys += [(e + 1.6, slot_x(NPL - 1) + 150), (e + 3.0, 3860.0), (e + 3.8, 3800.0), (e + 5.4, 3620.0),
                 (self.walk[0], 3620.0), (self.walk[1], 5400.0)]
        x = px(keys, t)
        y = px([(0.0, G), (self.cyc[-1] + 2.7, G), (self.tl0 - 0.4, BEHIND), (e + 3.0, BEHIND), (e + 3.8, G)], t)
        m.punch = 0.0
        for i in range(NPL):
            a = self.cyc[i]
            if a - 0.1 <= t < a + 0.9 or a + 1.95 <= t < a + 2.6:
                m.punch = 0.7
        self.place(m, x, t, dt, y=y)

    def tw_dx(self, t):
        """Body x minus the left blade's x when Twigs holds it at the cut line (found once with saw_to)."""
        if self._tw_dx is None:
            m = self.m("teeth")
            ox, oy, op = m.x, m.y, m.punch_l
            m.x, m.y = CUT + 100, G
            self._tw_dx = saw_to(m, 0.0, CUT, SH_TOP - 10, sx=-1) - CUT
            m.x, m.y, m.punch_l = ox, oy, op
        return self._tw_dx

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run, m.punch, m.punch_l = 0.0, 0.0, 0.0
        stand = CUT + self.tw_dx(t)
        log_x = WOOD_X + 10
        keys = [(0.0, stand), (self.cyc[-1] + 2.2, stand), (self.wood_saw[0][0] - 1.5, log_x + self.tw_dx(t) + 6),
                (self.wood_saw[1][1] + 0.4, log_x + self.tw_dx(t) + 6), (self.wood_saw[1][1] + 2.4, 5990.0)]
        x = px(keys, t)
        for i in range(NPL):
            a = self.cyc[i]
            if a + 0.75 <= t < a + 2.05:
                u = smoothstep(seg(t, a + 0.95, a + 1.85))
                ty = lerp(SH_TOP - 24, SH_TOP + 8, u)
                k = smoothstep(seg(t, a + 0.75, a + 0.95)) * (1 - smoothstep(seg(t, a + 1.85, a + 2.05)))
                m.x, m.y = x, G
                xs = saw_to(m, t, CUT, ty, sx=-1)
                m.punch_l *= k
                x = lerp(x, xs, k)
                m.saw_run = 1.0 if a + 0.9 < t < a + 1.9 else 0.0
        for (a, b) in self.wood_saw:                      # saws a firewood log in two on the chopping stump
            if a <= t < b:
                u = smoothstep(seg(t, a + 0.3, b - 0.3))
                k = smoothstep(seg(t, a, a + 0.3)) * (1 - smoothstep(seg(t, b - 0.3, b)))
                m.x, m.y = x, G
                xs = saw_to(m, t, log_x, lerp(G - 92, G - 58, u), sx=-1)
                m.punch_l *= k
                x = lerp(x, xs, k)
                m.saw_run = 1.0 if a + 0.3 < t < b - 0.3 else 0.0
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        reach = []
        (a1, b1), (a2, b2) = self.log_trips
        keys = [(0.0, 5820.0), (a1 + 0.6, 5820.0), (b1 - 0.1, 5880.0), (b1 + 0.2, 5880.0), (a2, 5820.0),
                (a2 + 0.6, 5820.0), (b2 - 0.1, 5880.0), (b2 + 0.9, HANS_OVEN), (self.hans_go[0], HANS_OVEN),
                (self.hans_go[1] - 2.0, TABLE[1] + 70), (self.tl0 - 0.3, slot_x(0) - 110)]
        for j in range(NPL):
            keys += [(self.tl[j] + 0.8, slot_x(j) - 110)]
        keys += [(self.tl[-1] + 1.4, slot_x(NPL - 1) - 110), (self.pick_t[0] - 0.2, PLATE_STUMP[0] + 30)]
        for q, p in enumerate(self.place_plates):
            hx = (TABLE[0] + 20) if q == 0 else SEATS[q - 1] - 40
            keys += [(p - 0.2, hx), (p + 0.8, hx)]
        keys += [(self.walk[0], SEATS[7] - 40), (self.walk[0] + 1.6, TABLE[1] + 80), (self.walk[1], 5640.0)]
        x = px(keys, t)
        y = px([(0.0, G), (self.hans_go[1] - 2.0, G), (self.hans_go[1] - 0.8, BEHIND), (self.walk[0] + 1.6, BEHIND),
                (self.walk[0] + 2.4, G)], t)
        for (a, b) in self.log_trips:                      # carries three logs each trip
            if a <= t < b:
                hx = m.x + 70
                reach = [(hx - 26, G - 150), (hx + 26, G - 150)]
        for k in range(OVEN_RINGS):                        # lays each coil: the tentacle tip is the end of the coil
            d, l, p0, p1 = self.ring_times(k)
            if p0 - 0.6 <= t < p0:                         # takes the coil's end off Digs' shovel
                sx, sy = self.shovel_xy()
                fx, fy = self.coil_front(k, 0.0)
                v = smootherstep(seg(t, p0 - 0.6, p0))
                reach = [(lerp(sx, fx, v), lerp(sy, fy, v) - 40 * math.sin(math.pi * v))]
            elif p0 <= t < p1 + 0.4:
                u = seg(t, p0, p1)
                reach = [self.coil_front(k, u), self.coil_front(k, max(0.0, u - 0.18))]
        d, l, p0, p1 = self.ring_times(OVEN_RINGS)        # and the chimney, coil by coil up from the dome
        if p0 - 0.6 <= t < p1 + 0.4:
            cx, cy = F.chimney_top(OVEN_X, G, OVEN_R, OVEN_H)
            u = seg(t, p0, p1)
            reach = [(cx - 10, lerp(cy + 70, cy, u)), (cx + 14, lerp(cy + 76, cy + 6, u))]
        for j in range(NPL):
            st = self.plank_state(j, t)
            if st[0] == "lay":
                px_, py_ = self.lay_pos(j, st[1])
                reach = [(px_ - 50, py_ - 8), (px_ + 40, py_ - 8)]
        a, b = self.pick_t
        if a <= t < b:                                     # lifts the stack off the stump
            u = smootherstep(seg(t, a, b))
            sx = lerp(PLATE_STUMP[0], m.x + 85, u)
            sy = lerp(PLATE_STUMP[1] - STUMP_TOP - 10, G - 170, u)
            reach = [(sx - 26, sy + 4), (sx + 26, sy + 4)]
        if b <= t < self.place_plates[-1] + 0.8:          # holds the stack, sets a plate and its cup at each place
            sx, sy = self.stack_xy()
            reach = [(sx - 26, sy + 4), (sx + 26, sy + 4)]
            for q in range(9):
                sp = self.setting_pos(q, t)
                if sp is not None:
                    reach = [(sp[0] - 8, sp[1] - 4), (sx + 26, sy + 4)]
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt, y=y)

    def lay_pos(self, j, u):
        """Where plank j is while Hans lays it: from the top of Wheels' stack to its slot (bottom middle)."""
        m = self.m("wheels")
        hx, hy = (m.x, m.y - HEAD_W * m.k - 11 * (NPL - 1 - j)) if m is not None else (slot_x(j) + 150, BEHIND - 186)
        e = smootherstep(u)
        return lerp(hx, slot_x(j), e), lerp(hy, YF, e) - 50 * math.sin(math.pi * u)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y, sq = self.sp.at(t)
        m.spring = sq
        self.place(m, x, t, dt, y=y)

    @property
    def on_top(self):
        m = self.m("springs")
        return ("springs",) if m is not None and m.y < G - 30 else ()

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        dig_x = PIT[0] + 30
        keys = [(0.0, 6650.0)]
        m.dig = 0.0
        for k in range(OVEN_RINGS + 1):
            d, l, p0, p1 = self.ring_times(k)
            keys += [(d - 0.1, dig_x), (l, dig_x), (p0 - 0.6, DIGS_PRESS), (p1, DIGS_PRESS)]
            if d <= t < l - 0.3:
                m.dig = 0.5 + 0.5 * math.sin((t - d) * 12)
            elif l - 0.3 <= t < p1 + 0.3:                  # the coil on the raised shovel, held out for Hans
                m.dig = lerp(0.5, CARRY, smoothstep(seg(t, l - 0.3, l))) * (1 - smoothstep(seg(t, p1, p1 + 0.3)))
        (a1, b1), (a2, b2) = self.wood_in
        keys += [(a1 - 1.2, WOOD_X + 150), (a1 + 0.3, WOOD_X + 150), (b1 - 0.3, OVEN_X - 30), (a2 - 0.2, WOOD_X + 150),
                 (a2 + 0.3, WOOD_X + 150), (b2 - 0.3, OVEN_X - 30), (b2 + 1.5, 5965.0)]
        x = px(keys, t)
        for (a, b) in self.wood_in:
            if a <= t < b + 0.3:
                m.dig = lerp(0.0, CARRY, smoothstep(seg(t, a, a + 0.3))) * (1 - smoothstep(seg(t, b - 0.6, b - 0.2)))
                if b - 0.6 <= t:
                    m.dig = lerp(m.dig, 0.6, smoothstep(seg(t, b - 0.6, b - 0.2)) * (1 - smoothstep(seg(t, b, b + 0.3))))
        self.place(m, x, t, dt)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        keys = [(0.0, 5640.0, G - 440.0), (4.5, 5700.0, G - 440.0), (9.0, 6230.0, G - 450.0),
                (self.hans_go[0], 6230.0, G - 450.0), (self.tl0, slot_x(0), G - 330.0)]
        for j in range(NPL):
            keys += [(self.tl[j] + 0.5, slot_x(j) - 10, G - 330.0)]
        for k in range(6):
            gx, gy = self.glo_lamp_spot(k)
            keys += [(self.lamp_t[k] - 0.25, gx, gy), (self.lamp_t[k] + 0.8, gx, gy)]
        keys += [(self.walk[0] + 1.0, LAMPS[5] + 200, G - 330.0), (self.walk[1], OVEN_X + 40, G - 250.0)]
        x, y = path(keys, t)[:2]
        g = 0.0
        for a in self.lamp_t:
            g = max(g, smoothstep(seg(t, a, a + 0.25)) * (1 - smoothstep(seg(t, a + 0.7, a + 0.95))))
        self.flare_g = g
        m.lamp = 1.15 + 1.2 * g
        self.place(m, x, t, dt, y=y + 9 * math.sin(t * 1.3))

    def glo_lamp_spot(self, k):
        """Where Glo floats to light lantern k (his own lamp just right of it)."""
        return LAMPS[k] + 60, rope_y(LAMPS[k]) + 41 - 10 + 178 * K

    # ----- what moves (the scene checks none of it jumps) -----

    def props(self, t):
        out = {}
        m = self.m("wheels")
        for i in range(NPL):
            st = self.plank_state(i, t)
            if st[0] in ("feed", "lift"):
                out[f"plank{i}"] = (st[1], st[2])
            elif st[0] == "head" and m is not None:
                out[f"plank{i}"] = self.head_xy(i)
            elif st[0] == "lay":
                out[f"plank{i}"] = self.lay_pos(i, st[1])
        for k in range(OVEN_RINGS + 1):
            d, l, p0, p1 = self.ring_times(k)
            if l - 0.2 <= t < p1:
                out[f"coil{k}"] = self.shovel_xy()
        if self.pick_t[0] <= t < self.place_plates[-1] + 0.8:
            out["stack"] = self.stack_xy()
        for q in range(9):
            sp = self.setting_pos(q, t)
            if sp is not None:
                out[f"plate{q}"] = sp[:2]
        return out

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        tw = self.m("teeth")
        if tw is not None and getattr(tw, "saw_run", 0) > 0.5 and P.rng.uniform() < 0.8:
            cx, cy = tw.saw_center(-1, t, 0.0)
            P.burst(cx, cy, 2, np.array([214, 186, 140]), 200, 0.32, 3.5, g=900, spread=0.6, direction=math.pi * 0.7)
        dg = self.m("digger")
        if dg is not None and dg.dig > 0.7 and dg.x > PIT[0] - 10 and P.rng.uniform() < 0.4:
            P.burst(dg.x + 60, G - 10, 2, F.CLAY_WET, 260, 0.7, 5, g=1300, spread=0.7, direction=-math.pi * 0.35)
        for (tb, d, h) in self.sp.bounces:
            if self.crossed(tb + d) and tb < self.ring_t[-1]:
                P.burst(self.sp.at(tb)[0], G - 2, 4, F.CLAY_WET, 160, 0.5, 4, g=1200, up=80, spread=1.2)

    def _sounds(self, t):
        s = self.s
        if self.crossed(0.8):
            self.chat(t, "teeth", "hey", icon="!")
        if self.crossed(1.6):
            self.chat(t, "digger", "idea", icon="bread")
        for i in range(NPL):
            a = self.cyc[i]
            if self.crossed(a + 0.75):
                self.hit(t, "clack", s.note(i % 4 + 1, -1), 0.08, STOP, SH_TOP)
            if self.crossed(a + 0.9):
                self.fx(t, "saw", 1.0, 0.13, CUT, SH_TOP)
            if self.crossed(a + 1.95):
                self.hit(t, "thud", 50, 0.06, CUT + 30, G)
            if self.crossed(a + 2.5):
                self.hit(t, "clack", s.note(i % 5 + 2, 0), 0.07, WF, G - 200)
            if i in (0, 4, 9) and self.crossed(a + 2.7):
                self.chat(t, "teeth" if i != 4 else "wheels", ["hehe", "mm", "yay"][(0, 4, 9).index(i)])
        for (a, b) in self.log_trips:
            if self.crossed(b - 0.1):
                self.hit(t, "thud", 46, 0.07, WOOD_X, G - 20)
        for k in range(OVEN_RINGS + 1):
            d, l, p0, p1 = self.ring_times(k)
            if self.crossed(d + 0.1):
                self.fx(t, "slide", 0.6, 0.05, PIT[0], G)
            if self.crossed(p0 + 0.1):
                self.fx(t, "rustle", p1 - p0 - 0.2, 0.05, OVEN_X, G - 100)
            if self.crossed(p1):
                self.hit(t, "pluck", s.note(k + 1, 0), 0.1, OVEN_X, G - 100)
            if k in (2, 5) and self.crossed(p1 + 0.3):
                self.chat(t, "digger", "mm" if k == 2 else "yay")
            if k == 3 and self.crossed(p1 + 0.5):
                self.chat(t, "tentacles", "mm", icon="heart")
        for (tb, d, h) in self.sp.bounces:
            if self.crossed(tb) and tb < self.ring_t[-1] and int(tb * 10) % 3 == 0:
                self.hit(t, "boing", 60 + int(tb) % 3 * 2, 0.07, 6960, G)
        if self.crossed(12.0):
            self.chat(t, "springs", "wee")
        for (a, b) in self.wood_saw:
            if self.crossed(a + 0.3):
                self.fx(t, "saw", b - a - 0.6, 0.11, WOOD_X, G - 70)
        for (a, b) in self.wood_in:
            if self.crossed(b - 0.4):
                self.hit(t, "thud", 47, 0.08, OVEN_X, G - 40)
        for j in range(NPL):
            if self.crossed(self.tl[j] + 0.85):
                self.hit(t, "clack", s.note(j % 6 + 1, 0), 0.11, slot_x(j), YB)
        for (ts, jp) in self.sp.hops:
            if self.crossed(ts) and jp.y1 < G - 20:
                self.hit(t, "boing", 64, 0.08, jp.x0, jp.y0)
        if self.crossed(self.tl[0] + 1.6):
            self.chat(t, "tentacles", "mm", icon="heart")
        if self.crossed(self.tl[5] + 1.0):
            self.chat(t, "springs", "wee")
        if self.crossed(self.tl[-1] + 2.4):
            self.chorus(t, ["wheels", "tentacles", "springs"], "yay", gap=0.22, icon="star")
        for k, a in enumerate(self.lamp_t):
            if self.crossed(a + 0.5):
                self.hit(t, "music_box", (72, 76, 79, 84, 88, 91)[k] - 12, 0.22, LAMPS[k], ROPE_Y)
                self.hit(t + 0.1, "chime", (79, 84, 86, 88, 91, 93)[k] - 12, 0.1, LAMPS[k], ROPE_Y)
        if self.crossed(self.lamp_t[-1] + 1.4):
            self.chorus(t, ["springs", "wheels", "tentacles"], "ooh", gap=0.24, icon="sparkle")
        for q, p in enumerate(self.place_plates):
            if self.crossed(p + 0.78):
                x, y = self.plate_xy(q)
                self.hit(t, "clack", s.note(q % 8, 0), 0.07, x, y)
        if self.crossed(self.walk[0] + 0.5):
            self.chat(t, "digger", "hey", icon="bread")

    # ----- drawing -----

    def draw(self, c, t):
        super().draw(c, t)
        g = getattr(self, "flare_g", 0.0)
        if g > 0.01:
            k = min(5, max(0, int((t - self.lamp_t[0] + 0.6) / 1.8)))
            self.flare(c, LAMPS[k], rope_y(LAMPS[k]) + 41, g)

    def held(self, kind, c, t):
        m = self.m(kind)
        if kind == "tentacles":
            for (a, b) in self.log_trips:
                if a + 0.6 <= t < b:
                    hx = m.x + 70
                    for k in range(3):
                        c.polygon(ellipse(hx - 30 + k * 2, G - 150 - k * 22, 40, 11, 16), F.LOG)
                        c.circle(hx + 10 + k * 2, G - 150 - k * 22, 11, F.LOG_END)

    def table_extra(self, c, t):
        for i in range(NPL):                                # the plank on the sawhorses / being fed
            st = self.plank_state(i, t)
            if st[0] == "feed":
                F.plank_side(c, st[1], st[2], PLANK_L, ragged=ragged_of(i))
            elif st[0] == "saw":
                F.plank_side(c, STOP + PLANK_L / 2, SH_TOP, PLANK_L, ragged=ragged_of(i) if st[1] < 1 else 0.0)
                if 0.0 < st[1] < 1.0:
                    c.line(CUT, SH_TOP - 11, CUT, SH_TOP - 11 + 11 * st[1], np.array([60, 44, 30]), 2)
            elif st[0] == "lay":                            # the plank Hans is laying: over the table, never under it
                x, y = self.lay_pos(i, st[1])
                F.plank_between(c, x, y, st[1], PLANK_L, PW - 4, YB, YF)
        for (a, b) in self.wood_saw:                        # the log on the chopping stump
            if a - 0.6 <= t < b + 0.5:
                rect(c, WOOD_X - 20, G - 50, WOOD_X + 40, G, TRUNK * 1.1)
                u = smoothstep(seg(t, b - 0.3, b + 0.3))
                for sgn in (-1, 1):
                    xx = WOOD_X + 10 + sgn * (28 + 30 * u)
                    c.polygon(ellipse(xx, G - 62 + 40 * u, 28, 11, 14), F.LOG)
                    c.circle(xx + sgn * 26, G - 62 + 40 * u, 11, F.LOG_END)
        if self.pick_t[0] <= t < self.place_plates[-1] + 0.8:     # the stack in Hans' tentacles
            sx, sy = self.stack_xy()
            left = 9 - sum(1 for p in self.place_plates if t >= p)
            draw_stack(c, sx, sy, left, min(left, 8) if left < 9 else 8)
            if t < self.pick_t[1]:
                pass
        for q in range(9):                                  # a plate and its cup on the way to their place
            sp = self.setting_pos(q, t)
            if sp is not None:
                F.plate(c, sp[0], sp[1] + 6)
                if q > 0:
                    F.cup(c, sp[0] + 30, sp[1] + 2)

    def carried(self, c, t):
        m = self.m("wheels")
        for i in range(NPL):                                # on Wheels' head: the cut planks, stacked
            st = self.plank_state(i, t)
            if st[0] == "head" and m is not None:
                F.plank_side(c, *self.head_xy(i), PLANK_L)
            elif st[0] == "lift":
                F.plank_side(c, st[1], st[2], PLANK_L)
        dg = self.m("digger")
        if dg is not None:                                  # the coil of clay on Digs' shovel, fed out as Hans lays it
            for k in range(OVEN_RINGS + 1):
                d, l, p0, p1 = self.ring_times(k)
                if l - 0.2 <= t < p1:
                    left = 1.0 - seg(t, p0, p1)
                    sx, sy = self.shovel_xy()
                    c.polygon(ellipse(sx, sy, 12 + 22 * left, 6 + 7 * left, 16), F.CLAY_WET)
            for (a, b) in self.wood_in:
                if a + 0.3 <= t < b - 0.3:
                    sx, sy = dg.x - SHOVEL_DX, G - 84
                    for q in range(3):
                        c.circle(sx - 12 + q * 12, sy - (q % 2) * 10, 10, F.LOG_END)


# ====================================================================== BAKE

class BakeAct(VillageAct):
    """(no cut) Fire, dough, into the oven, everyone waits by the warm oven while it bakes, out, and all together
    to the table with the bread.

    Owner after FK0005's re-render: the camera cut away to the table and back, the bread jumped from Digs' shovel to
    the board while he was still at the oven, then back into his hands. Now the camera stays at the oven and the
    bench until the bread is on Wheels' head, then follows the procession to the table; every loaf and pie rides
    on Digs' shovel (it is wherever the shovel is), slides off it only where it is set down."""
    name = "bake"
    joins_prev = True
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.light = (2.5, 4.6)
        self.scoops = [7.0, 8.1, 9.2]
        self.pour = (10.2, 11.2)
        self.knead = (11.4, 13.6)
        self.bowl_out = (13.6, 14.2)
        self.dough_cuts = [14.6, 15.3, 16.0]
        self.spread = (16.6, 17.4)
        self.fills = [(19.0, 19.7), (19.8, 20.5)]
        self.scores = [19.0 + 0.55 * q for q in range(4)]          # loaves 0, 2, 3, 5
        # Digs' trips: two at a time on the shovel; scoop (0.6 s), carry, slide in (0.5 s); out the same way
        self.in_trips = [22.0, 25.4, 28.8]
        self.out_trips = [40.0, 43.4, 46.8]
        self.t_in = {}
        for q, a in enumerate(self.in_trips):
            for i in (2 * q, 2 * q + 1):
                self.t_in[i] = a + 2.8
        self.board_lift = (50.6, 51.6)
        self.walk = (52.0, 64.0)                                     # all together to the table
        self.dur = self.walk[1] + 0.5
        # Springs: up onto the bench to bounce the two pie bases flat, then by the oven to watch, then to his seat
        mv = Moves(5250.0, G)
        mv.walk(0.5, 5420.0, G, step=200)
        mv.walk(9.0, 6880.0, G, step=230)
        self.pie_flat = []
        mv.hop(16.7, ITEM_X[4], BT - 6, apex=50)
        self.pie_flat.append(mv.t + 0.06)
        mv.bounce(mv.t + 0.06, h=24, d=0.5)
        mv.hop(17.9, ITEM_X[1], BT - 6, apex=30)
        self.pie_flat.append(mv.t + 0.06)
        mv.bounce(mv.t + 0.06, h=24, d=0.5)
        mv.hop(19.0, 6385.0, G, apex=30)
        mv.walk(19.7, 5700.0, G, step=200)                # by the oven, clear of its mouth
        mv.walk(self.walk[0] - 0.5, SEATS[SEAT_OF["springs"]], G, step=200, rest=0.25)
        self.sp = mv
        self.stats = {"board_even": bool(max(np.diff(ITEM_X)) - min(np.diff(ITEM_X)) < 0.5), "loaves": 4, "pies": 2}

    def aside_moods(self, t):
        return ["mm", "ooh", "hehe", "aww"]

    # ----- state -----

    def fire(self, t):
        return smoothstep(seg(t, self.light[0] + 1.0, self.light[1] + 1.6))

    def bake(self, i, t):
        if i not in self.t_in or t < self.t_in[i]:
            return 0.0
        return smoothstep(seg(t, self.t_in[i] + 0.5, self.t_in[i] + 10.5))

    def shovel_xy(self):
        """Where the blade of Digs' shovel is (what he carries sits on it)."""
        dg = self.m("digger")
        return (dg.x - SHOVEL_DX, G - 84) if dg is not None else (OVEN_X + 30, G - 84)

    def trip_board_x(self, q):
        """Digs' x while the shovel's blade is under items 2q, 2q+1 on the board."""
        return (ITEM_X[2 * q] + ITEM_X[2 * q + 1]) / 2 + SHOVEL_DX

    def item_state(self, i, t):
        """Item i: ('board', x, y) / ('shovel', x, y) / ('into', x, y, scale) / ('oven', i) / ('wheels',)."""
        q = i // 2
        off = -14.0 if i % 2 == 0 else 14.0
        sx, sy = self.shovel_xy()
        a = self.in_trips[q]
        if t < a + 0.1:
            return ("board", ITEM_X[i], BT - 8)
        if t < a + 0.7:                                    # the blade slides under: the two close up onto it
            u = smootherstep(seg(t, a + 0.1, a + 0.7))
            return ("shovel", lerp(ITEM_X[i], sx + off, u), lerp(BT - 8, sy, u))
        if t < a + 2.3:
            return ("shovel", sx + off, sy)
        if t < a + 2.8:                                    # slid off the blade into the oven
            u = smootherstep(seg(t, a + 2.3, a + 2.8))
            ox, oy, osc = OVEN_SLOTS[i]
            return ("into", lerp(sx + off, ox, u), lerp(sy, oy, u), lerp(1.0, osc, u))
        b = self.out_trips[q]
        if t < b + 0.1:
            return ("oven", i)
        if t < b + 0.6:                                    # out of the oven onto the blade
            u = smootherstep(seg(t, b + 0.1, b + 0.6))
            ox, oy, osc = OVEN_SLOTS[i]
            return ("into", lerp(ox, sx + off, u), lerp(oy, sy, u), lerp(osc, 1.0, u))
        if t < b + 2.3:
            return ("shovel", sx + off, sy)
        if t < b + 2.9:                                    # slid off onto its place on the board
            u = smootherstep(seg(t, b + 2.3, b + 2.9))
            return ("shovel", lerp(sx + off, ITEM_X[i], u), lerp(sy, BT - 8, u))
        if t < self.board_lift[0]:
            return ("board", ITEM_X[i], BT - 8)
        return ("wheels",)

    def dough_pieces(self, t):
        """Before the shapes: the ball of dough on the board, cut into pieces."""
        a, b = self.bowl_out
        if t < b:
            return None
        cut = sum(1 for c_ in self.dough_cuts if t >= c_ + 0.45)
        sp = smoothstep(seg(t, *self.spread))
        out = []
        if cut == 0:
            return [("dough", 6560.0, BT - 2, 0, 0, 0, 1.0)]
        n = [2, 4, 6][cut - 1]
        for i in range(n):
            x0 = 6560.0 + (i - (n - 1) / 2) * 30
            x1 = ITEM_X[i] if n == 6 else x0
            out.append(("dough", lerp(x0, x1, sp), BT - 2, 0, 0, 0, 0.8))
        return out

    def world(self, t):
        w = super().world(t)
        flour = sum(1 for a in self.scoops if t >= a + 0.9) / 3.0
        water = smoothstep(seg(t, self.pour[0] + 0.3, self.pour[1]))
        dough = smoothstep(seg(t, self.knead[0], self.knead[1]))
        a, b = self.bowl_out
        bowl = (BOWL_X, BT, flour, water, dough * (1 - smoothstep(seg(t, a, a + 0.5))),
                (0.5 + 0.5 * math.sin(t * 7)) if self.knead[0] < t < self.knead[1] else 0.0)
        if t >= a + 0.5:
            bowl = (BOWL_X, BT, 0.0, 0.0, 0.0, 0.0)
        items = []
        shaped = t >= self.spread[1] + 0.1
        if not shaped:
            items = self.dough_pieces(t)
        else:
            for i in range(6):
                st = self.item_state(i, t)
                if st[0] == "board":
                    kind = ITEM_KIND[i]
                    shape = smoothstep(seg(t, self.spread[1], self.spread[1] + 1.4))
                    if kind == "pie":
                        k = [1, 4].index(i)
                        tf = self.pie_flat[1 - k]
                        flat = 1.0 - smoothstep(seg(t, tf, tf + 0.3))
                        fa, fb = self.fills[k]
                        filled = smoothstep(seg(t, fa, fb))
                        if flat > 0.02:
                            items.append(("dough", st[1], st[2] + 6, 0, 0, 0, 0.3 + 0.7 * flat))
                        else:
                            items.append((kind, st[1], st[2] + 8, self.bake(i, t), 0.0, filled, 1.0))
                    else:
                        q = [0, 2, 3, 5].index(i)
                        sc = smoothstep(seg(t, self.scores[q] + 0.1, self.scores[q] + 0.45))
                        if shape < 1:
                            items.append(("dough", st[1], st[2] + 8, 0, 0, 0, lerp(0.8, 1.0, shape)))
                        else:
                            items.append((kind, st[1], st[2] + 8, self.bake(i, t), sc, 1.0, 1.0))
        oven = []
        for i in range(6):
            st = self.item_state(i, t)
            if st[0] == "oven":
                ox, oy, osc = OVEN_SLOTS[i]
                oven.append((ITEM_KIND[i], ox, oy, osc, self.bake(i, t), 1.0, 1.0))
        w.update(fire=self.fire(t), wood=1.0 - 0.3 * self.fire(t), bowl=bowl, board_items=items, oven_items=oven,
                 birds_home=(1, 1, 1, 1), board_on_bench=t < self.board_lift[0], sack=1.0, wood_stack=0,
                 logs_in_pile=0, jug=self.jug_pose(t))
        return w

    def jug_pose(self, t):
        a, b = self.pour
        if t < a - 0.6 or t >= b + 0.6:
            return (JUG_V, G, 0.0)
        u = smootherstep(seg(t, a - 0.6, a))
        v = smootherstep(seg(t, b, b + 0.6))
        x = lerp(JUG_V, BOWL_X + 70, u * (1 - v))
        y = lerp(G, BT - 40, u * (1 - v))
        ang = -1.1 * smoothstep(seg(t, a, a + 0.3)) * (1 - smoothstep(seg(t, b - 0.3, b)))
        return (x, y, ang)

    # ----- camera: the oven and the bench the whole time, then along with the procession to the table -----

    def target(self, t):
        keys = [(0.0, 6150.0, None, 1.3), (6.4, 6170.0, None, 1.3), (9.0, 6480.0, None, 1.45), (14.0, 6500.0, None, 1.45),
                (21.0, 6460.0, None, 1.4), (24.0, 6380.0, None, 1.3), (self.board_lift[1], 6420.0, None, 1.3),
                (self.walk[1], 4700.0, None, 1.2)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._glo(t, dt)
        self._hans(t, dt)
        self._twigs(t, dt)
        self._digs(t, dt)
        self._wheels(t, dt)
        self._springs(t, dt)
        self._particles(t)
        self.leaves(0.035)
        self._sounds(t)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        w0, w1 = self.walk
        x, y = path([(0.0, OVEN_X + 40, G - 250.0), (18.0, OVEN_X + 40, G - 250.0), (24.0, OVEN_X - 60, G - 300.0),
                     (w0 + 0.5, OVEN_X - 60, G - 300.0), (w1 - 1.0, SEATS[0] + 20, G - 300.0)], t)[:2]
        g = smoothstep(seg(t, self.light[0], self.light[0] + 0.4)) * (1 - smoothstep(seg(t, self.light[1] - 0.3, self.light[1])))
        self.flare_g = g
        m.lamp = 1.1 + 1.2 * g
        self.place(m, x, t, dt, y=y + 9 * math.sin(t * 1.3))

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        stand = 6540.0
        w0, w1 = self.walk
        x = px([(0.0, 5640.0), (4.8, 5640.0), (6.8, stand), (w0 - 1.0, stand), (w1 - 0.6, SEATS[SEAT_OF["tentacles"]])], t)
        y = px([(0.0, G), (4.8, G), (5.8, BEHIND)], t)        # behind the oven and the bench from here on
        reach = []
        bx, by = BOWL_X, BT - 40
        for a in self.scoops:                               # a scoop of flour from the sack to the bowl
            if a <= t < a + 1.1:
                u = smootherstep(seg(t, a, a + 1.1))
                sx_, sy_ = SACK_V, G - 150
                p = (lerp(sx_, bx, smoothstep(seg(u, 0.35, 1.0))), lerp(sy_, by, smoothstep(seg(u, 0.35, 1.0))) -
                     60 * math.sin(math.pi * seg(u, 0.35, 1.0)))
                reach = [p]
        a, b = self.pour
        if a - 0.6 <= t < b + 0.6:
            jx, jy, ja = self.jug_pose(t)
            reach = [(jx - 10, jy - 40), (jx + 16, jy - 20)]
        a, b = self.knead
        if a <= t < b:
            ph = (t - a) * 7
            reach = [(bx - 22 + 8 * math.sin(ph), by + 4 + 6 * math.cos(ph)), (bx + 22 - 8 * math.sin(ph), by + 4 - 6 * math.cos(ph))]
        a, b = self.bowl_out
        if a <= t < b:
            u = seg(t, a, b)
            reach = [(lerp(bx, 6560, u) - 20, BT - 16), (lerp(bx, 6560, u) + 20, BT - 16)]
        a, b = self.spread
        if a <= t < b + 1.4:
            u = seg(t, a, b + 1.4)
            k = int(u * 6) % 6
            reach = [(ITEM_X[k], BT - 20), (ITEM_X[min(5, k + 1)], BT - 20)]
        for k, (fa, fb) in enumerate(self.fills):           # acorn mash from the pot into each pie
            if fa <= t < fb:
                u = seg(t, fa, fb)
                ix = ITEM_X[[1, 4][k]]
                reach = [(lerp(POT_X, ix, smoothstep(u)), lerp(G - 50, BT - 20, smoothstep(u)) - 50 * math.sin(math.pi * u))]
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt, y=y)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run, m.punch, m.punch_l = 0.0, 0.0, 0.0
        if not hasattr(self, "_tdx"):
            ox, oy = m.x, m.y
            m.x, m.y = 6700.0, G
            self._tdx = saw_to(m, 0.0, 6560.0, BT - 20, sx=-1) - 6560.0
            m.x, m.y = ox, oy
            m.punch_l = 0.0
        stand = 6560.0 + self._tdx
        keys = [(0.0, 5990.0), (10.0, 5990.0), (13.8, stand), (16.6, stand)]
        for q in range(4):
            i = [0, 2, 3, 5][q]
            keys += [(self.scores[q] - 0.15, ITEM_X[i] + self._tdx), (self.scores[q] + 0.45, ITEM_X[i] + self._tdx)]
        keys += [(21.6, ITEM_X[5] + self._tdx), (23.4, 6950.0), (self.walk[0], 6950.0),
                 (self.walk[1] - 0.2, SEATS[SEAT_OF["teeth"]])]
        x = px(keys, t)
        y = row_y(x) if t > self.walk[0] else G
        cuts = [(a, a + 0.45, 6560.0 + (q - 1) * 30, BT - 26, BT + 2) for q, a in enumerate(self.dough_cuts)]
        cuts += [(self.scores[q], self.scores[q] + 0.45, ITEM_X[[0, 2, 3, 5][q]], BT - 58, BT - 44) for q in range(4)]
        for (a, b, tx, y0, y1) in cuts:
            if a - 0.15 <= t < b + 0.15:
                u = smoothstep(seg(t, a, b))
                k = smoothstep(seg(t, a - 0.15, a)) * (1 - smoothstep(seg(t, b, b + 0.15)))
                m.x, m.y = x, G
                xs = saw_to(m, t, tx, lerp(y0, y1, u), sx=-1)
                m.punch_l *= k
                x = lerp(x, xs, k)
                m.saw_run = 1.0 if a < t < b else 0.0
        self.place(m, x, t, dt, y=y)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        oven = OVEN_X + 30 + SHOVEL_DX                      # the blade at the oven's mouth
        keys = [(0.0, 5965.0), (19.6, 5965.0)]
        for q, a in enumerate(self.in_trips):
            bx = self.trip_board_x(q)
            keys += [(a - 0.1, bx), (a + 0.7, bx), (a + 2.2, oven), (a + 2.9, oven)]
        for q, b in enumerate(self.out_trips):
            bx = self.trip_board_x(q)
            keys += [(b - 0.2, oven), (b + 0.7, oven), (b + 2.2, bx), (b + 3.0, bx)]
        w0, w1 = self.walk
        keys += [(w0 + 1.0, self.trip_board_x(2) + 60), (w1, SEATS[SEAT_OF["digger"]])]
        x = px(keys, t)
        y = row_y(x) if t > w0 else G
        dk = [(0.0, 0.0)]                                  # the shovel: down to scoop, held up level to carry
        for a in self.in_trips:
            dk += [(a - 0.1, 0.0), (a + 0.25, 0.3), (a + 0.75, CARRY), (a + 2.2, CARRY), (a + 2.5, 0.3), (a + 2.9, 0.0)]
        for b in self.out_trips:
            dk += [(b, 0.0), (b + 0.25, 0.3), (b + 0.65, CARRY), (b + 2.3, CARRY), (b + 2.6, 0.3), (b + 3.0, 0.0)]
        m.dig = px(dk, t)
        self.place(m, x, t, dt, y=y)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        cx = (BOARD[0] + BOARD[1]) / 2
        a, b = self.board_lift
        x = px([(0.0, 5400.0), (3.0, 5540.0), (a - 4.5, 5540.0), (a, cx), (b + 0.4, cx),
                (self.walk[1], FOOD_X[5] + 60)], t)
        m.punch = 0.8 if a - 0.2 <= t < b + 0.2 else 0.0
        self.place(m, x, t, dt, y=row_y(x))

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y, sq = self.sp.at(t)
        y += row_y(x) - G if t > self.walk[0] - 1.0 else 0.0
        m.spring = sq
        self.place(m, x, t, dt, y=y)

    @property
    def on_top(self):
        m = self.m("springs")
        return ("springs",) if m is not None and m.y < G - 40 and m.x > 6000 else ()

    # ----- what moves -----

    def props(self, t):
        out = {}
        for i in range(6):
            st = self.item_state(i, t)
            if st[0] in ("board", "shovel", "into"):
                out[f"food{i}"] = (st[1], st[2])
        a, b = self.board_lift
        if t >= a:
            out["board"] = self.board_xy(t)
        return out

    def board_xy(self, t):
        m = self.m("wheels")
        a, b = self.board_lift
        u = smootherstep(seg(t, a, b))
        cx = (BOARD[0] + BOARD[1]) / 2
        return lerp(cx, m.x, u), lerp(BT, m.y - HEAD_W * m.k, u) - 30 * math.sin(math.pi * u)

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        if self.fire(t) > 0.5 and P.rng.uniform() < 0.12:
            P.burst(OVEN_X + P.rng.uniform(-30, 30), G - 40, 1, np.array([255, 170, 80]), 60, 0.8, 2.5, g=-160,
                    glow=True, spread=0.6)
        for a in self.scoops:
            if self.crossed(a + 0.9):
                P.burst(BOWL_X, BT - 44, 8, F.FLOUR, 120, 0.8, 4, g=-20, up=40, spread=1.4)
        tw = self.m("teeth")
        if tw is not None and tw.saw_run > 0.5 and P.rng.uniform() < 0.5:
            cx, cy = tw.saw_center(-1, t, 0.0)
            P.burst(cx, cy, 1, F.DOUGH, 120, 0.5, 3, g=900, spread=0.6, direction=math.pi * 0.7)

    def _sounds(self, t):
        s = self.s
        a, b = self.light
        if self.crossed(a):
            self.chat(t, "lantern", "hey", icon="sparkle")
        if self.crossed(a + 0.6):
            for q, n in enumerate((72, 76, 79)):
                self.hit(t + q * 0.12, "chime", n, 0.13, OVEN_X, G - 60)
        if self.crossed(a + 1.2):
            self.fx(t, "air_blow", 1.4, 0.06, OVEN_X, G - 60)
        if self.crossed(b + 1.0):
            self.chorus(t, ["digger", "teeth"], "ooh", gap=0.25)
        for q, a_ in enumerate(self.scoops):
            if self.crossed(a_ + 0.9):
                self.fx(t, "sand_pour", 0.5, 0.05, BOWL_X, BT)
        if self.crossed(self.pour[0] + 0.3):
            self.fx(t, "gurgle", 1.0, 0.07, BOWL_X, BT)
        if self.crossed(self.knead[0] + 0.3):
            self.chat(t, "tentacles", "mm", icon="bread")
        for k in range(4):
            if self.crossed(self.knead[0] + 0.5 + k * 0.8):
                self.fx(t, "paint_wipe", 0.5, 0.05, BOWL_X, BT)
        for q, a_ in enumerate(self.dough_cuts):
            if self.crossed(a_):
                self.fx(t, "saw", 0.45, 0.08, 6560, BT)
        if self.crossed(self.dough_cuts[-1] + 0.7):
            self.chat(t, "teeth", "hehe")
        for k in range(2):
            if self.crossed(self.pie_flat[k]) or self.crossed(self.pie_flat[k] + 0.5):
                self.hit(t, "boing", 64 + 2 * k, 0.1, ITEM_X[[4, 1][k]], BT)
        if self.crossed(19.5):
            self.chat(t, "springs", "wee")
        for q, a_ in enumerate(self.scores):
            if self.crossed(a_ + 0.1):
                self.fx(t, "saw", 0.3, 0.06, ITEM_X[[0, 2, 3, 5][q]], BT)
        for q, a_ in enumerate(self.in_trips):
            if self.crossed(a_ + 0.2):
                self.fx(t, "slide", 0.4, 0.05, ITEM_X[2 * q], BT)
            if self.crossed(a_ + 2.6):
                self.hit(t, "pluck", s.note(q + 2, 0), 0.1, OVEN_X, G - 30)
        if self.crossed(self.in_trips[-1] + 3.4):
            self.chat(t, "digger", "yay", icon="pie")
        # while it bakes: a quiet wait by the warm oven
        if self.crossed(self.in_trips[-1] + 5.0):
            self.chat(t, "springs", "ooh", icon="bread")
        if self.crossed(self.in_trips[-1] + 8.0):
            self.chorus(t, ["lantern", "wheels"], "mm", gap=0.4)
        for q, b_ in enumerate(self.out_trips):
            if self.crossed(b_ + 0.4):
                self.fx(t, "slide", 0.4, 0.05, OVEN_X, G - 30)
            if self.crossed(b_ + 2.8):
                self.hit(t, "pluck", s.note(q + 4, 0), 0.1, ITEM_X[2 * q], BT)
        if self.crossed(self.out_trips[0] + 0.8):
            self.chat(t, "digger", "ooh", icon="bread")
        if self.crossed(self.out_trips[-1] + 3.2):
            self.chorus(t, ["digger", "wheels"], "yay", gap=0.3, icon="star")
        if self.crossed(self.board_lift[1]):
            self.chat(t, "wheels", "hey", icon="bread")
        if self.crossed(self.walk[0] + 3.0):
            self.chorus(t, ["springs", "teeth", "tentacles"], "hehe", gap=0.3)

    # ----- drawing -----

    def draw(self, c, t):
        super().draw(c, t)
        g = getattr(self, "flare_g", 0.0)
        if g > 0.01:
            self.flare(c, OVEN_X - 10, G - 40, g)

    def carried(self, c, t):
        for i in range(6):
            st = self.item_state(i, t)
            if st[0] == "shovel":
                draw_item(c, ITEM_KIND[i], st[1], st[2], self.bake(i, t), 0.0, 1.0)
            elif st[0] == "into":
                draw_item(c, ITEM_KIND[i], st[1], st[2], self.bake(i, t), 0.0, 1.0, sc=st[3])
        m = self.m("wheels")
        a, b = self.board_lift
        if m is not None and t >= a:
            bx, by = self.board_xy(t)
            cx = (BOARD[0] + BOARD[1]) / 2
            F.stump_board(c, bx - 150, bx + 150, by)
            for i in range(6):
                draw_item(c, ITEM_KIND[i], bx + ITEM_X[i] - cx, by - 8, 1.0, 0.0, 1.0)

    def held(self, kind, c, t):
        pass


# ====================================================================== FEAST

class SupperAct(VillageAct):
    """(no cut) The animals come out of their houses; everyone eats together at the long table; pull back."""
    name = "feast"
    joins_prev = True
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        # (owner after FK0005's re-render: no cut, slow on purpose) Hans serves the six dishes one by one, then the
        # camera drifts over to the houses as the animals come out and comes back to the table with them; everything
        # after the serving runs A s later than it used to
        self.serve = [0.6 + 1.6 * q for q in range(6)]            # Hans lifts food 5..0 off the board onto the table
        self.board_down = (self.serve[-1] + 1.6, self.serve[-1] + 2.8)
        A = self.A = self.board_down[1] + 7.4 - 4.8
        self.dur = 44.0 + A
        self.bird_out = [4.8 + A + 0.8 * b for b in range(4)]
        self.bunny_out = [5.6 + A, 6.8 + A]
        self.hedge_out = 6.2 + A
        # pieces: who takes a piece from which dish, when (-> their plate)
        self.takes = [("lantern", 0, 12.0 + A), ("tentacles", 1, 12.6 + A), ("teeth", 2, 13.2 + A),
                      ("springs", 3, 13.8 + A), ("wheels", 4, 14.4 + A), ("digger", 5, 15.0 + A),
                      ("hedgehog", 0, 16.0 + A)]
        self.bites = {}
        rs = np.random.default_rng(31)
        for (who, d, tt) in self.takes:
            b0 = tt + 1.6 + rs.uniform(0, 0.8)
            self.bites[who] = [b0 + 2.6 * k + rs.uniform(0, 0.6) for k in range(4)]
        self.nibbles = {"bunny0": [18.0 + A + 2.2 * k for k in range(5)], "bunny1": [18.9 + A + 2.3 * k for k in range(5)]}
        self.pecks = [[17.0 + A + b * 0.7 + 1.9 * k for k in range(6)] for b in range(4)]
        self.pull = (31.0 + A, 44.0 + A)
        self.stats = {"animals_seated": 7, "food_even": bool(max(np.diff(FOOD_X)) - min(np.diff(FOOD_X)) < 0.5)}

    def aside_moods(self, t):
        if 11.0 + self.A < t < 31.0 + self.A:
            return []
        return ["aww", "mm", "hehe", "ooh"]

    # ----- state -----

    def food_eaten(self, d, t):
        e = 0.0
        for (who, dd, tt) in self.takes:
            if dd == d and t >= tt + 0.3:
                e += 0.22
        for who, (seat, dd) in (("bunny0", (1, 0)), ("bunny1", (5, 3))):
            if dd == d:
                e += 0.05 * sum(1 for b in self.nibbles[who] if t >= b + 0.2)
        for b in range(4):
            near = int(np.argmin([abs(BIRD_X[b] - fx) for fx in FOOD_X]))
            if near == d:
                e += 0.01 * sum(1 for p in self.pecks[b] if t >= p + 0.15)
        return min(0.9, e)

    def served(self, i, t):
        """Dish i: None still on the board, ('lift', u) going to the table, ('table')."""
        q = 5 - i
        a = self.serve[q]
        if t < a:
            return None
        if t < a + 1.2:
            return ("lift", smootherstep(seg(t, a, a + 1.2)))
        return ("table",)

    def world(self, t):
        w = super().world(t)
        food = []
        for i in range(6):
            st = self.served(i, t)
            if st is not None and st[0] == "table":
                food.append((FOOD_KIND[i], FOOD_X[i], FOOD_Y, 1.0, self.food_eaten(i, t)))
        homes = tuple(0 if t >= self.bird_out[b] + 0.2 else 1 for b in range(4))
        w.update(food=food, board_items=None, board_on_bench=False, birds_home=homes, bowl=(BOWL_X, BT, 0, 0, 0, 0))
        return w

    # ----- camera: the dishes, a slow drift to the houses as the animals come out, back to the table with them,
    # then the pull back -----

    def target(self, t):
        A = self.A
        keys = [(0.0, 4700.0, None, 1.2), (self.board_down[1], 4560.0, None, 1.2),
                (4.6 + A, 3550.0, G - 310.0, 0.9), (10.5 + A, 3700.0, G - 300.0, 0.9), (16.5 + A, 4450.0, None, 1.25),
                (24.0 + A, 4420.0, None, 1.4), (30.0 + A, 4600.0, None, 1.4), (31.0 + A, 4600.0, None, 1.38),
                (44.0 + A, 3600.0, G - 640.0, 0.36)]
        return cam_keys(keys, t)

    @property
    def cam_omega(self):
        return 0.8 if (self.s._t - self.t0) / self.STRETCH - self.LEAD > self.pull[0] else 1.0

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        k = self.s.k
        # Hans serves along the table from the right, then takes his own seat
        m = self.m("tentacles")
        if m is not None:
            keys = [(0.0, SEATS[2])]
            for q in range(6):
                keys += [(self.serve[q] - 0.1, FOOD_X[5 - q] - 120), (self.serve[q] + 1.2, FOOD_X[5 - q] - 120)]
            keys += [(self.board_down[1] + 0.2, FOOD_X[0] - 120), (self.board_down[1] + 2.4, SEATS[2])]
            x = px(keys, t)
            reach = []
            for i in range(6):
                st = self.served(i, t)
                if st is not None and st[0] == "lift":
                    p = self.dish_pos(i, st[1])
                    reach = [(p[0] - 22, p[1] - 14), (p[0] + 22, p[1] - 14)]
            a, b = self.board_down
            if a <= t < b:
                p = self.board_pos(t)
                reach = [(p[0] - 120, p[1] - 4), (p[0] + 120, p[1] - 4)]
            reach += self.take_reach("tentacles", t)
            self.reach["tentacles"] = reach
            self.place(m, x, t, dt, y=BEHIND)
        m = self.m("wheels")
        if m is not None:
            keys = [(0.0, FOOD_X[5] + 60)]
            for q in range(6):
                keys += [(self.serve[q] - 0.1, FOOD_X[5 - q] + 60), (self.serve[q] + 1.2, FOOD_X[5 - q] + 60)]
            keys += [(self.board_down[1], FOOD_X[0] + 60), (self.board_down[1] + 3.0, SEATS[6])]
            x = px(keys, t)
            m.punch = 0.7 if self.taking("wheels", t) else 0.0
            self.place(m, x, t, dt, y=BEHIND)
        for kind in ("teeth", "springs", "digger"):
            m = self.m(kind)
            if m is not None:
                m.saw_run = 0.0
                if kind == "teeth":
                    m.punch_l = 0.5 if self.taking("teeth", t) else 0.0
                    m.saw_run = 1.0 if self.taking("teeth", t, 0.1, 0.5) else 0.0
                if kind == "springs":
                    m.punch = 0.6 if self.taking("springs", t) else 0.0
                if kind == "digger":
                    m.dig = 0.5 if self.taking("digger", t) else 0.0
                self.place(m, SEATS[SEAT_OF[kind]], t, dt, y=BEHIND)
        m = self.m("lantern")
        if m is not None:
            A = self.A
            x = px([(0.0, SEATS[0] + 20), (10.0 + A, SEATS[0]), (15.9 + A, SEATS[0]), (16.4 + A, SEATS[0] - 60),
                    (17.4 + A, SEATS[0] - 60), (18.2 + A, SEATS[0])], t)
            y = px([(0.0, G - 300.0), (10.0 + A, G - 130.0), (15.9 + A, G - 130.0), (16.4 + A, G - 110.0),
                    (17.4 + A, G - 110.0), (18.2 + A, G - 130.0)], t)
            m.lamp = 1.25
            self.place(m, x, t, dt, y=y + 7 * math.sin(t * 1.3))
        self._particles(t)
        self.leaves(0.03)
        self._sounds(t)

    def props(self, t):
        out = {}
        m = self.m("wheels")
        a, b = self.board_down
        if m is not None and t < b:
            out["board"] = (m.x, m.y - HEAD_W * m.k) if t < a else self.board_pos(t)
        for i in range(6):
            st = self.served(i, t)
            if st is not None and st[0] == "lift":
                out[f"food{i}"] = self.dish_pos(i, st[1])
        for (who, d, tt) in self.takes:
            if tt <= t < tt + 0.9:
                out[f"piece_{who}"] = self.piece_pos(who, d, tt, t)
        return out

    def taking(self, who, t, a=0.0, b=0.6):
        for (w, d, tt) in self.takes:
            if w == who and tt + a <= t < tt + b:
                return True
        return False

    def take_reach(self, who, t):
        for (w, d, tt) in self.takes:
            if w == who and tt <= t < tt + 0.9:
                p = self.piece_pos(w, d, tt, t)
                return [p]
        return []

    def plate_of(self, who):
        return HEDGE_PLATE if who == "hedgehog" else (SEATS[SEAT_OF[who]], PLATE_Y)

    def piece_pos(self, who, d, tt, t):
        u = smootherstep(seg(t, tt, tt + 0.9))
        px_, py_ = self.plate_of(who)
        x0, y0 = FOOD_X[d], FOOD_Y - 10
        lift = 40 if who != "hedgehog" else 70
        return lerp(x0, px_, u), lerp(y0, py_ - 4, u) - lift * math.sin(math.pi * u)

    def dish_pos(self, i, u):
        m = self.m("wheels")
        bx, by = (m.x, m.y - HEAD_W * m.k) if m is not None else (FOOD_X[i] + 60, BEHIND - 186)
        cx = (BOARD[0] + BOARD[1]) / 2
        x0, y0 = bx + ITEM_X[i] - cx, by - 8
        return lerp(x0, FOOD_X[i], u), lerp(y0, FOOD_Y, u) - 40 * math.sin(math.pi * u)

    def board_pos(self, t):
        m = self.m("wheels")
        bx, by = (m.x, m.y - HEAD_W * m.k) if m is not None else (FOOD_X[0] + 60, BEHIND - 186)
        a, b = self.board_down
        u = smootherstep(seg(t, a, b))
        return lerp(bx, 4230.0, u), lerp(by, BEHIND - 2, u) - 40 * math.sin(math.pi * u)

    # ----- the animals -----

    def bird_state(self, b, t):
        """(x, y, flap, face, clip) clip: None or the hole polygon it is coming out of."""
        sp = PR.SPECS[b]
        hx, hy = PR.hole_center(sp, POSTS[b], POST_TOP)
        perch = (hx + 10, hy + sp.hole_r + 14)
        t0 = self.bird_out[b]
        if t < t0:
            return None
        if t < t0 + 0.6:                                   # out through the round hole onto the perch
            u = smoothstep(seg(t, t0, t0 + 0.6))
            return lerp(hx, perch[0], u), lerp(hy + 8, perch[1], u), 0.0, 1, ellipse(hx, hy, sp.hole_r, sp.hole_r, 20) \
                if u < 0.7 else None
        t1, t2 = t0 + 1.4, t0 + 5.0
        land = (BIRD_X[b], YB + 3)
        if t < t1:
            hop = max(0.0, math.sin((t - t0 - 0.6) * 9)) * 5
            return perch[0], perch[1] - hop, 0.0, 1, None
        if t < t2:
            x, y, flap, face = flying_bird(t, t1, t2, perch, land, lift=160)
            return x, y, flap, face, None
        peck = 0.0
        for p in self.pecks[b]:
            if p <= t < p + 0.35:
                peck = math.sin(math.pi * (t - p) / 0.35)
        near = FOOD_X[int(np.argmin([abs(BIRD_X[b] - fx) for fx in FOOD_X]))]
        face = 1 if near >= BIRD_X[b] else -1
        return land[0] + face * 4 * peck, land[1] + 6 * peck, 0.0, face, None

    def ground_state(self, who, t):
        """Bunnies and the hedgehog: (x, y, hop, scale, clip, face)."""
        if who == "hedgehog":
            sp, hx0 = PR.SPECS[4], HEDGE_X
            t0, dest, speed = self.hedge_out, HEDGE_SPOT, 120.0
        else:
            i = int(who[-1])
            sp, hx0 = PR.SPECS[5], BUNNY_X
            t0, dest, speed = self.bunny_out[i], (SEATS[BUNNY_SEAT[i]], BEHIND), 170.0
        dx, dy = PR.hole_center(sp, hx0, G)
        r = sp.hole_r
        door = ellipse(dx, dy, r, r * 1.1, 24, math.pi, 2 * math.pi) + [(dx + r, G), (dx - r, G)]
        if t < t0:
            return None
        if t < t0 + 0.8:                                    # comes forward out of the doorway
            u = smoothstep(seg(t, t0, t0 + 0.8))
            return dx, G, 0.0, lerp(0.7, 1.0, u), door if u < 0.75 else None, 1
        d = dest[0] - dx
        T = abs(d) / speed
        u = seg(t, t0 + 0.8, t0 + 0.8 + T)
        x = dx + d * (smoothstep(u) * 0.3 + u * 0.7)
        y = lerp(G, dest[1], smoothstep(seg(u, 0.85, 1.0)))
        hop = 0.0
        if who != "hedgehog" and 0 < u < 1:
            n = max(1, int(T / 0.42))
            hop = abs(math.sin(u * n * math.pi)) * 26
        if u >= 1 and who != "hedgehog":
            hop = 30.0                                        # sitting up at the table
            nib = self.nibbles[who]
            for b in nib:
                if b <= t < b + 0.5:
                    hop -= 8 * math.sin(math.pi * (t - b) / 0.5)
            hop *= smoothstep(seg(t, t0 + 0.8 + T, t0 + 1.4 + T))
        return x, y, hop, 1.0, None, 1

    def diners_behind(self, c, t):
        for i, who in enumerate(("bunny0", "bunny1")):
            st = self.ground_state(who, t)
            if st is not None and st[1] < G - 6:
                bunny(c, st[0], st[1], 1.3, st[2], st[5])

    def animals_front(self, c, t):
        for who in ("bunny0", "bunny1", "hedgehog"):
            st = self.ground_state(who, t)
            if st is None or st[1] < G - 6:
                continue
            x, y, hop, sc, clip, face = st
            if who == "hedgehog":
                draw = lambda: hedgehog(c, x, y, 1.2 * sc, face, t)
            else:
                draw = lambda: bunny(c, x, y, 1.3 * sc, hop, face)
            if clip is not None:
                F.clip_inside(c, clip, draw)
            else:
                draw()
        for b in range(4):
            st = self.bird_state(b, t)
            if st is None or st[1] >= YB + 2.5 and t > self.bird_out[b] + 5.0:
                continue
            x, y, flap, face, clip = st
            draw = lambda: PR.bird(c, x, y, 1.0, face, flap, BIRD_COLS[b], t)
            if clip is not None:
                F.clip_inside(c, clip, draw)
            else:
                draw()

    def birds_on_table(self, c, t):
        for b in range(4):
            st = self.bird_state(b, t)
            if st is not None and t >= self.bird_out[b] + 5.0:
                x, y, flap, face, clip = st
                PR.bird(c, x, y, 1.0, face, 0.0, BIRD_COLS[b], t)

    def table_extra(self, c, t):
        # pieces: in the air on the way to a plate, then on the plate, eaten bite by bite
        for (who, d, tt) in self.takes:
            if t < tt:
                continue
            kind = FOOD_KIND[d]
            if t < tt + 0.9:
                if who == "hedgehog":
                    continue                                 # drawn in front (it goes down to the ground)
                x, y = self.piece_pos(who, d, tt, t)
                F.piece(c, x, y, kind, 1.0)
            else:
                px_, py_ = self.plate_of(who)
                if who == "hedgehog":
                    continue
                eaten = 0.25 * sum(1 for b in self.bites[who] if t >= b + 0.1)
                F.piece(c, px_, py_ - 2, kind, 1.0, eaten)

    def carried(self, c, t):
        m = self.m("wheels")
        for (who, d, tt) in self.takes:                       # the hedgehog's piece and plate are in front
            if who != "hedgehog" or t < tt:
                continue
            kind = FOOD_KIND[d]
            if t < tt + 0.9:
                x, y = self.piece_pos(who, d, tt, t)
            else:
                x, y = HEDGE_PLATE[0], HEDGE_PLATE[1] - 2
            eaten = 0.25 * sum(1 for b in self.bites[who] if t >= b + 0.1)
            F.piece(c, x, y, kind, 1.0, eaten if t >= tt + 0.9 else 0.0)
        a, b = self.board_down
        if m is not None and t < b:
            if t < a:
                bx, by = m.x, m.y - HEAD_W * m.k
            else:
                bx, by = self.board_pos(t)
            if t < b - 0.05:
                F.stump_board(c, bx - 150, bx + 150, by)
            cx = (BOARD[0] + BOARD[1]) / 2
            for i in range(6):
                if self.served(i, t) is None:
                    draw_item(c, FOOD_KIND[i], bx + ITEM_X[i] - cx, by - 8, 1.0, 0.0, 1.0)
        for i in range(6):
            st = self.served(i, t)
            if st is not None and st[0] == "lift":
                x, y = self.dish_pos(i, st[1])
                draw_item(c, FOOD_KIND[i], x, y, 1.0, 0.0, 1.0)

    def held(self, kind, c, t):
        pass

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        if P.rng.uniform() < 0.05:
            P.burst(P.rng.uniform(3600, 5300), P.rng.uniform(G - 420, G - 160), 1, FIREFLY, 20, 5.0, 4.5,
                    kind="firefly", g=0.0, spread=3.0)
        for who, times in self.bites.items():
            for b in times:
                if self.crossed(b):
                    px_, py_ = self.plate_of(who)
                    P.burst(px_, py_ - 10, 3, F.CRUST * 1.1, 70, 0.5, 2.0, g=600, up=40, spread=1.2)
        for b in range(4):
            for p in self.pecks[b]:
                if self.crossed(p + 0.15):
                    P.burst(BIRD_X[b] + 8, YB, 2, F.CRUST * 1.1, 50, 0.4, 1.8, g=600, up=30, spread=1.2)

    def _sounds(self, t):
        s = self.s
        A = self.A
        for q in range(6):
            if self.crossed(self.serve[q] + 1.15):
                self.hit(t, "clack", s.note(q + 1, 0), 0.08, FOOD_X[5 - q], FOOD_Y)
        if self.crossed(0.6):
            self.chat(t, "wheels", "yay", icon="bread")
        for b in range(4):
            if self.crossed(self.bird_out[b] + 0.3):
                for k in range(3):
                    self.hit(t + k * 0.1, "music_box", (84, 88, 86)[k] - 12 * (b % 2), 0.13, POSTS[b], POST_TOP)
            if self.crossed(self.bird_out[b] + 5.0):
                self.hit(t, "bloop", 79, 0.12, BIRD_X[b], YB)
        for i, t0 in enumerate(self.bunny_out):
            if self.crossed(t0 + 0.4):
                self.hit(t, "chime", (76, 79)[i], 0.14, BUNNY_X, G - 60)
        if self.crossed(self.hedge_out + 0.4):
            self.hit(t, "chime", 72, 0.14, HEDGE_X, G - 60)
        if self.crossed(4.0 + A):
            self.chat(t, "lantern", "aww", icon="heart")
        if self.crossed(7.0 + A):
            self.chorus(t, ["springs", "teeth", "digger"], "hey", gap=0.25, icon="heart")
        if self.crossed(10.5 + A):
            self.chat(t, "tentacles", "aww", icon="heart")
        for (who, d, tt) in self.takes:
            if self.crossed(tt + 0.85):
                self.hit(t, "clack", s.note(d + 2, 0), 0.06, FOOD_X[d], PLATE_Y)
        moods = {"lantern": "mm", "tentacles": "mm", "teeth": "hehe", "springs": "mm", "wheels": "mm", "digger": "mm"}
        for who, times in self.bites.items():
            if who == "hedgehog":
                for b in times:
                    if self.crossed(b):
                        self.hit(t, "pluck", 69, 0.06, HEDGE_PLATE[0], HEDGE_PLATE[1])
                continue
            for k, b in enumerate(times):
                if self.crossed(b):
                    self.chat(t, who, moods[who], icon=("heart" if k == 1 else ("bread" if k == 0 else None)))
        for who, times in self.nibbles.items():
            for b in times:
                if self.crossed(b):
                    self.hit(t, "pluck", 74 if who == "bunny0" else 71, 0.05, SEATS[BUNNY_SEAT[int(who[-1])]], YB)
        if self.crossed(27.0 + A):
            for k, n in enumerate((60, 64, 67)):
                self.hit(t + k * 0.08, "clack", n, 0.06, 4500, CUP_Y)             # a clink of cups
        if self.crossed(self.pull[0] + 1.0):
            self.chorus(t, ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"], "aww", gap=0.2,
                        icon="heart")
        if self.crossed(self.pull[0] + 6.0):
            for k, n in enumerate((60, 64, 67, 72, 76, 79, 84)):
                self.hit(t + k * 0.14, "soft_bell", n, 0.2, 4500, G - 300)

    # ----- drawing -----

    def draw(self, c, t):
        super().draw(c, t)
