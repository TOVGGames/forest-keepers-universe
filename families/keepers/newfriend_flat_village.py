"""Forest Keepers ep 12 (flat remake): the village beats (docs/engines/forest_keepers_new_friend_flat.md, beats 1 and 3).

    Branch      Twigs trims a dead branch off the old oak (one blade out, short strokes, sawdust); Hans holds it with
                two tentacles so it can't drop, and once it's cut he lowers it and lays it down along the ground behind
                them. Beat 1: the right-hand branch (DEAD2); beat 3: the left-hand one (DEAD). The one laid down in
                beat 1 is still lying there in beat 3.
    Planting    beat 3, right of the oak: Digs digs a hole (his paw scoops, the soil flies onto a little heap), Sprout
                drops in the acorn it has carried since the factory, Digs pats the soil back over it, Sprout takes the
                watering can from the stump, walks round the back of the mound and waters it, and the little tree comes up.

Pure functions of time (frames render in parallel).
"""
import math

import numpy as np
import skia

from families.foundry.products.monster import ACORN, CAP, LEAF, SEED_STEM, Monster, acorn_nut, seedling
from .flat_motion import MoleDig, Spoil
from .newfriend_flat_world import BACK, DEAD, DEAD2, DEAD2_CUT_U, G, OAK_X, PLANT_X, STUMP_TOP, STUMP_X, TRUNK
from .storybook import oval, rrect, smooth, tone, tube

K = 0.72
DEADWOOD = (122, 104, 88)           # a dead branch: grey-brown, no leaves
FRESH = (214, 182, 138)             # a fresh cut end
SOIL = (112, 86, 64)
SOIL_D = (70, 52, 40)
WATER = (150, 190, 220)
GRAV = 1500.0


def _seg(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return min(max((t - a) / (b - a), 0.0), 1.0)


def _digs_bob(t):
    return 2 * K * math.sin(t * 2.6)                 # monster.py's digger bob (awake)


def ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease(t, a, b):
    return ss(_seg(t, a, b))


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


# ----------------------------------------------------------------------------------------------- the dead branch

class Branch:
    """One dead branch: its live part runs from the cut point (where the layer's stub ends, 22% along) to the tip.

    side: +1 the branch reaches right from the trunk (DEAD2), -1 left (DEAD). Twigs stands under the cut point and
    reaches up with the hand on the trunk's side... Hans stands under the far part and holds it with two tentacles.
    """

    CUT_U = 0.22                     # where the layer's stub ends (newfriend_flat_world.oak)
    STROKES = 8
    STROKE = 0.5

    def __init__(self, pts, t0, side, hold=0.0, cut_u=None, hand=None):
        self.side = side
        cut_u = (DEAD2_CUT_U if pts is DEAD2 else self.CUT_U) if cut_u is None else cut_u
        # Twigs' sawing hand: the one on the trunk's side, unless he stands nearer the trunk than the cut (branch 1,
        # round 16: he saws it from its trunk side with his right hand, his head clear of the cut)
        self.hand = hand if hand is not None else ((1 if pts is DEAD2 else -1) if side > 0 else 1)
        a, b = pts[0], pts[1]
        self.q = (a[0] + (b[0] - a[0]) * cut_u, a[1] + (b[1] - a[1]) * cut_u)
        self.spine = [self.q, pts[1], pts[2]]
        self.L = sum(math.dist(p, r) for p, r in zip(self.spine, self.spine[1:]))
        self.t0 = t0
        self.reach = (t0 + 0.2, t0 + 1.4)            # Twigs' hand up to the cut
        self.blade_out = (t0 + 1.4, t0 + 2.0)
        self.saw = (t0 + 2.2, t0 + 2.2 + self.STROKES * self.STROKE)
        self.cut = self.saw[1]                       # cut through: Hans has it
        self.blade_in = (self.cut + 0.3, self.cut + 0.9)
        self.back = (self.cut + 0.6, self.cut + 1.8)
        self.grip = (t0 + 0.5, t0 + 1.7)             # Hans' two tentacles reach it and take hold
        # he swings it down and lays it along the ground behind (`hold`: he holds it up a little longer while Twigs
        # steps out from under it - fresh agent, FK0024 round 5: Twigs stood in front of the second one coming down)
        self.lower = (self.cut + 0.8 + hold, self.cut + 4.6 + hold)
        self.let_go = (self.lower[1] + 0.2, self.lower[1] + 1.2)
        self.end = self.let_go[1]
        # where his tentacles hold it (fraction along it): spread out, so it hangs level between them (fresh agent,
        # FK0024 round 13: both at the far end, the cut end floated level with nothing under it)
        self.grips = (0.74, 0.97)
        # lying: along the ground behind the path, its cut end by the trunk, slightly downhill to the tip
        x_cut = OAK_X + side * 95.0 + (cut_u - self.CUT_U) * (b[0] - a[0])   # (its cut end where it was cut)
        self.lie = ((x_cut, BACK + 2.0), (x_cut + side * self.L, BACK + 8.0))

    def point(self, u, t):
        """Point u (0 cut end .. 1 tip) of the branch at time t."""
        p0 = self._along(u)
        if t >= self.cut:                            # cut through, its end drops a little in Hans' hold: a gap opens
            sag = 9.0 * ease(t, self.cut, self.cut + 0.35) * max(0.0, 1.0 - u / self.grips[0])   # at the stub
            p0 = (p0[0], p0[1] + sag)                # (fresh agent, FK0024 round 13: it looked never cut)
        if t < self.lower[0]:
            return p0
        e = ease(t, *self.lower)
        p1 = lerp2(self.lie[0], self.lie[1], u)
        # swing down: the cut end stays near the trunk, the tip comes down in an arc (a little lift first)
        mid = lerp2(p0, p1, e)
        return mid[0], mid[1] - 40.0 * math.sin(math.pi * e) * u

    def _along(self, u):
        d = u * self.L
        for p, r in zip(self.spine, self.spine[1:]):
            s = math.dist(p, r)
            if d <= s or r is self.spine[-1]:
                f = min(1.0, d / s if s else 0.0)
                return lerp2(p, r, f)
            d -= s
        return self.spine[-1]

    # ----- Twigs

    def twigs_hand(self, t, rest):
        """Twigs' cutting hand target (world) and the blade (0..1), or None. rest: his resting hand (world)."""
        if not (self.reach[0] <= t < self.back[1]):
            return None
        q = self.q
        n = self._normal()
        at = (q[0] - n[0] * 16.0, q[1] - n[1] * 16.0 + 10.0)     # the hand just under the branch, blade across it
        blade = ease(t, *self.blade_out) * (1 - ease(t, *self.blade_in))
        if t < self.reach[1]:
            return lerp2(rest, at, ease(t, *self.reach)), blade
        if t < self.saw[0]:
            return at, blade
        if t < self.saw[1]:
            u = (t - self.saw[0]) / self.STROKE
            push = math.sin(math.pi * 2 * u) * 13.0                 # back and forth along the blade (across)
            deep = 22.0 * _seg(t, *self.saw)                        # and a little deeper each stroke
            d = (self._dir()[0] * push, self._dir()[1] * push)
            return (at[0] + d[0] - n[0] * deep * 0.4, at[1] + d[1] - n[1] * deep * 0.4), blade
        if t < self.back[0]:
            return at, blade
        return lerp2(at, rest, ease(t, *self.back)), blade

    def _dir(self):
        """Across the branch at the cut: the direction the blade strokes (perpendicular to the branch)."""
        a, b = self.spine[0], self.spine[1]
        L = math.dist(a, b)
        return ((b[1] - a[1]) / L, -(b[0] - a[0]) / L)

    def _normal(self):
        a, b = self.spine[0], self.spine[1]
        L = math.dist(a, b)
        return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

    # ----- Hans

    def hans_targets(self, t, slots):
        """[(slot, (x, y) world, grip 0..1)] for Hans' two working tentacles (slots: which two)."""
        if not (self.grip[0] <= t < self.let_go[1]):
            return []
        g = ease(t, *self.grip) * (1 - ease(t, *self.let_go))
        return [(s, self.point(u, t), g) for s, u in zip(slots, self.grips)]

    def held(self, t):
        return self.grip[1] <= t < self.let_go[0]

    # ----- drawing

    def draw(self, pg, t, sh, attached=True):
        """The live branch (behind the path's Keepers, in front of the trunk), its little side twigs; a fresh cut
        end on it once cut, and on the stub."""
        pts = [self.point(u, t) for u in np.linspace(0, 1, 9)]
        pts = [(x - sh, y) for x, y in pts]
        pg.shape(tube(pts, 13, 5), DEADWOOD, 0.1, (0.0, -0.4))
        for u, ang, ln in ((0.35, 0.9, 60), (0.55, -0.8, 50), (0.75, 0.7, 44)):
            p = self.point(u, t)
            r = self.point(min(1.0, u + 0.05), t)
            d = math.atan2(r[1] - p[1], r[0] - p[0])
            a = d + ang * self.side
            pg.stroke(skia.Path().moveTo(p[0] - sh, p[1]).lineTo(p[0] - sh + math.cos(a) * ln,
                                                                 p[1] + math.sin(a) * ln), DEADWOOD, 4.0)
        if t >= self.cut:
            c = pts[0]
            pg.flat(oval(c[0], c[1], 6, 12), FRESH)
        if self.saw[0] < t < self.cut:                               # the kerf growing in the cut: pale fresh
            k = 0.12 + 0.88 * _seg(t, *self.saw)                     # wood in a notch that deepens stroke by
            q = (self.q[0] - sh, self.q[1])                          # stroke (fresh agent, FK0024 round 6: a thin
            n, a = self._dir(), self._normal()                       # dark line on dark wood didn't show)
            if n[1] < 0:                                             # from the underside, where the blade comes
                n = (-n[0], -n[1])                                   # in, up (round 13: branch 2's grew down)
            r0, r1 = 13.0, 13.0 - 26.0 * k
            w0, w1 = 9.0, 6.0                                        # a little wider at the mouth
            notch = skia.Path()
            notch.moveTo(q[0] + n[0] * r0 - a[0] * w0, q[1] + n[1] * r0 - a[1] * w0)
            notch.lineTo(q[0] + n[0] * r1 - a[0] * w1, q[1] + n[1] * r1 - a[1] * w1)
            notch.lineTo(q[0] + n[0] * r1 + a[0] * w1, q[1] + n[1] * r1 + a[1] * w1)
            notch.lineTo(q[0] + n[0] * r0 + a[0] * w0, q[1] + n[1] * r0 + a[1] * w0)
            notch.close()
            pg.flat(notch, FRESH)
            pg.stroke(notch, (60, 46, 36), 1.5)

    def draw_stub_end(self, pg, t, sh):
        if t >= self.cut:
            pg.flat(oval(self.q[0] - sh, self.q[1], 6, 12), FRESH)

    def sawdust(self, pg, t, sh):
        if not (self.saw[0] < t < self.cut + 1.2):
            return
        rs = np.random.default_rng(7)
        te = self.saw[0]
        while te < min(t, self.cut):
            tau = t - te
            vx = rs.uniform(-40, 40)
            x = self.q[0] + vx * tau
            y = self.q[1] + 10 + 0.5 * 600 * tau * tau
            if y < G - 4:
                pg.flat(oval(x - sh, y, 3.2, 3.2), (226, 200, 160), 0.9)
            te += 0.05


# ----------------------------------------------------------------------------------------------- the planting

class Dig(MoleDig):
    """flat_motion's MoleDig, its strokes counted from t_start only (harvest_flat.Dig: Spoil throws soil for every
    stroke it counts, so strokes from long before would have built a heap before he started)."""

    def flicks(self, sx, t0, t1, at=None):
        return super().flicks(sx, max(t0, self.t0), t1, at)


class SideSpoil(Spoil):
    """Spoil with the clods' sideways throw scaled (harvest_flat.SideSpoil): the heaps land close beside the hole,
    where his paws can reach them again to fill it back in."""

    def __init__(self, *a, throw=1.0, **kw):
        super().__init__(*a, **kw)
        self.flights = [f[:6] + (f[6] * throw,) + f[7:] for f in self.flights]
        self.landed = [(f, f[3] + self._fall(f)) for f in self.flights]
        for sx in (-1, 1):
            xs = [self._fly(f, tl)[0] for f, tl in self.landed if f[1] == sx and f[0].endswith(".0")]
            self.cx[sx] = sum(xs) / len(xs)


class Planting:
    """Beat 3, right of the oak. Digs digs the hole the way a mole does (flat_motion.MoleDig, owner FK0011: "dig like
    a dog would, or look up how a mole would"): standing over the spot, both broad paws in turn, each stroke scooping
    soil out and flinging it onto a heap beside the hole (fresh agent, FK0024 round 5: one paw scratching from the
    side didn't read as digging). He steps aside, Sprout steps up and drops its acorn in (it lies there in the open
    hole a moment), Sprout steps back, Digs comes back and sweeps both heaps back in, paw by paw, over the acorn.
    Positions (world x): the hole, where Digs stands aside, Sprout's drop spot and where it waits, the stump."""

    HOLE = PLANT_X
    DIGS = HOLE - 340.0              # Digs aside, left of the hole, while Sprout puts its acorn in (his hanging
                                     # right paw well clear of the hole's lip: at -215 it hung over its left end,
                                     # fresh agent, FK0024 round 11); from here he tosses the left heap back in,
                                     # his body clear of the hole, so the acorn's burial shows (round 14)
    SPROUT = HOLE + 100.0            # Sprout's drop spot: its left hand (shoulder -78 k, arm 57 k) over the hole
    SPROUT_WAIT = HOLE + 380.0       # where Sprout waits while Digs digs and fills (clear of his paws' widest sweep)
    STUMP = STUMP_X                  # right beside Sprout waiting: its right hand reaches the can's handle
    SPROUT_WATER = HOLE - 167.0      # where Sprout waters from: its can's rose (lifted) right over the mound
    SPROUT_EDGE = HOLE + 190.0       # where it steps back to go round the mound (its feet clear of the soil patch)
    HOPS, HOP_DUR = 3, 0.65          # Sprout's bounces round the front of the mound (s each)
    HOP_H = 30.0                     # ...and how high each one goes (px)
    SPROUT_BACK = SPROUT_WATER - 60.0  # ...and the little step back it takes, can lowered, before the tree comes up
    DIGS_BACK = OAK_X + 160.0        # where Digs goes at the end: just right of the oak's trunk, wholly in the shot
                                     # (fresh agent, FK0024 round 15: left of the trunk he was cut in half by the
                                     # frame's edge all through the payoff), clear of Sprout all through the
                                     # watering
    RIM = BACK + 6.0                 # the hole's middle line (its opening, seen a little from above)
    HOLE_RX, HOLE_RY = 70.0, 14.0    # about four acorns across, well narrower than Digs (fresh agent, FK0024 round 7:
                                     # the 66 px hole hid under him; round 14: 150 was too big for one acorn; round 15:
                                     # 236 was wider than Digs himself, not "a little hole")
    PERIOD, STROKES = 1.1, 8         # the dig: eight strokes each paw
    FILL_P, FILLS = 1.3, 3           # the fill: three pawfuls from each heap
    # the left heap, from beside the hole: the right paw scoops at the heap's foot and tosses the pawful up and over
    # into the hole, onto the acorn (angle at the shoulder; 0 out to the side, negative up)
    TOSS_KEYS = [(0.0, 1.19), (0.3, 0.62), (0.44, 0.60), (0.62, -0.35), (0.74, -0.35), (1.0, 1.19)]
    TOSS_TAKE, TOSS_LET, TOSS_T = 0.40, 0.64, 0.55
    TOSS_LAND = (-14.0, 10.0, -2.0)  # where each pawful lands (from the hole's middle)
    THROW = 0.45                     # each heap lands just beside the (wide) hole, where his paws reach it again
    HEAP_DY = -28.0                  # ...and a little behind it (flung back, a dog's way): clear of Sprout's spot
    SHOULDER = (118 * K, -150 * K + 4 * K + 40.0)   # Digs' shoulder from (hole x, BACK) when he stands over it
    ARM = 95 * K
    # the fill sweep (right paw; the left mirrors it): angle at the shoulder (0 out to the side, pi/2 down)
    FILL_KEYS = [(0.0, 2.15), (0.32, 0.40), (0.44, 0.52), (0.82, 2.2), (1.0, 2.15)]
    TAKE, DROP = 0.44, 0.82

    def __init__(self, t0):
        self.t0 = t0
        self.dig = Dig(K, period=self.PERIOD, t_start=t0 + 0.6)
        self.dig_t = (t0 + 0.6, t0 + 0.6 + self.STROKES * self.PERIOD)
        hy = BACK + self.HEAP_DY                      # (Spoil's rim: where the heaps sit; the shoulder from it)
        self.spoil = SideSpoil(self.dig, self.HOLE, hy, K, self.dig_t[1],
                               (self.SHOULDER[0], self.SHOULDER[1] - self.HEAP_DY), self.ARM, _digs_bob,
                               throw=self.THROW)
        e = self.dig_t[1]
        self.digs_out = (e + 0.6, e + 3.2)            # Digs steps aside (left)
        self.sprout_in = (self.digs_out[0] + 0.9, self.digs_out[0] + 3.1)   # Sprout steps up to the hole
        # holds its acorn out over the hole, slowly (fresh agent, FK0024 round 14: the drop was over too fast)
        self.drop_arm = (self.sprout_in[1] + 0.2, self.sprout_in[1] + 2.0)
        self.drop = self.drop_arm[1] + 1.0            # a moment held over the open hole, then lets go
        self.drop_land = self.drop + math.sqrt(2 * 50.0 / GRAV)
        self.arm_back = (self.drop + 0.4, self.drop + 1.2)
        self.sprout_out = (self.drop + 1.6, self.drop + 3.8)   # (the acorn lies in the open hole), Sprout steps back
        # Digs, still beside the hole, tosses the left heap in over the acorn; then steps over the hole and sweeps
        # the right heap in (fresh agent, FK0024 round 14: filling from over the hole hid the burial)
        a0 = self.sprout_out[1] - 0.6
        self.fill_a = (a0, a0 + self.FILLS * self.FILL_P)
        self.digs_in = (self.fill_a[1] + 0.4, self.fill_a[1] + 3.0)          # Digs over the hole
        b0 = self.digs_in[1] + 0.4
        self.fill_b = (b0, b0 + self.FILLS * self.FILL_P)
        self.fill_t = (self.fill_a[0], self.fill_b[1])
        self.strokes = [(self.dig_t[0] + i * self.PERIOD, self.dig_t[0] + (i + 1) * self.PERIOD)
                        for i in range(self.STROKES)]                    # (for the sounds and the bubbles)
        self.sweeps = self._sweeps()
        self.pats = [(s["take"], s["land"]) for s in self.sweeps]   # the fill's pawfuls: taken, landed in the hole
        p1 = self.fill_t[1]
        self.aside = (p1 + 0.3, p1 + 3.1)             # Digs steps aside again...
        self.can_take = (p1 + 0.8, p1 + 1.8)          # Sprout's right hand to the can, picks it up
        self.sprout_up = (self.can_take[1] + 0.3, self.can_take[1] + 2.5)   # ...carries it up to the mound's edge
        self.digs_back = (self.aside[1] + 0.3, self.aside[1] + 2.1)        # Digs goes on, to beside the oak
        self.hop = (max(self.sprout_up[1] + 0.3, self.digs_back[0] + 1.6), None)
        self.hop = (self.hop[0], self.hop[0] + self.HOPS * self.HOP_DUR)   # three little bounces along in front
                                                      # of the mound to the other side (fresh agent, FK0024 round 16:
                                                      # a 4.5 s walk across it; walks only in short bursts)
        self.water = (self.hop[1] + 0.5, self.hop[1] + 6.0)   # a good long drink (fresh agent, FK0024 round 14)
        self.step_back = (self.water[1] + 0.2, self.water[1] + 1.2)  # can lowered, a step back from the mound
        self.grow = (self.step_back[1] + 0.2, self.step_back[1] + 6.2)  # the little tree comes up (nothing over it)
        self.end = self.grow[1] + 1.0

    # ----- Digs' paws
    @staticmethod
    def _keyed(keys, f):
        for (f0, a0), (f1, a1) in zip(keys, keys[1:]):
            if f0 <= f <= f1:
                return a0 + (a1 - a0) * ss((f - f0) / (f1 - f0))
        return keys[-1][1]

    def fill_angle(self, sx, t):
        """The paw angle while filling: the right paw works (tossing from beside, then sweeping from over the
        hole), the left one hangs at his side."""
        for s in self.sweeps:
            if s["base"] <= t < s["base"] + self.FILL_P or (s is self.sweeps[-1] and t >= s["base"]):
                if sx != s["paw"]:
                    break
                f = min(1.0, (t - s["base"]) / self.FILL_P)
                return self._keyed(self.TOSS_KEYS if s["toss"] else self.FILL_KEYS, f)
        return self.REST[sx]

    def _sweeps(self):
        """Every pawful of the fill: {paw, heap (its side), toss, base, take, let (go), land, dx}."""
        out = []
        for i in range(self.FILLS):                    # the left heap, tossed in from beside the hole
            base = self.fill_a[0] + i * self.FILL_P
            let = base + self.TOSS_LET * self.FILL_P
            out.append(dict(paw=1, heap=-1, toss=True, base=base, take=base + self.TOSS_TAKE * self.FILL_P, let=let,
                            land=let + self.TOSS_T, dx=self.TOSS_LAND[i]))
        for i in range(self.FILLS):                    # the right heap, swept in from over the hole
            base = self.fill_b[0] + i * self.FILL_P
            let = base + self.DROP * self.FILL_P
            out.append(dict(paw=1, heap=1, toss=False, base=base, take=base + self.TAKE * self.FILL_P, let=let,
                            land=let + 0.15, dx=0.0))
        return out

    REST = {-1: math.radians(112.0), 1: math.radians(68.0)}

    def digs_x(self, t):
        """Where Digs stands while his paws work: beside the hole for the dig's end and the first fill, else over."""
        return self.DIGS if self.digs_out[1] <= t < self.digs_in[0] else self.HOLE

    def paws(self, t):
        """Digs' paw angles {-1: rad, 1: rad} (monster.paw_ang) while he digs or fills, else None. Into and out of
        each, the paws come from / go back to hanging at his sides over 0.3-0.4 s (never a jump)."""
        for (a, b), fn in ((self.dig_t, self.dig.angle), (self.fill_a, self.fill_angle),
                           (self.fill_b, self.fill_angle)):
            if a - 0.35 <= t < b + 0.45:
                tt = min(max(t, a), b)
                cur = {s: fn(s, tt) for s in (-1, 1)}
                if t < a:
                    u = ss(_seg(t, a - 0.35, a))
                elif t >= b:
                    u = 1.0 - ss(_seg(t, b, b + 0.45))
                else:
                    return cur
                return {s: self.REST[s] + (cur[s] - self.REST[s]) * u for s in (-1, 1)}
        return None

    def paw_pos(self, sx, t, ang):
        return (self.digs_x(t) + sx * self.SHOULDER[0] + math.cos(ang) * self.ARM,
                BACK + self.SHOULDER[1] + _digs_bob(t) + math.sin(ang) * self.ARM)

    # ----- the hole
    def depth(self, t):
        return ease(t, *self.dig_t)

    def filled(self, t):
        """0..1 how much soil is back in the hole: a sixth with each pawful that lands in it (over 0.25 s)."""
        sw = self.sweeps
        return sum(ss(_seg(t, s["land"], s["land"] + 0.25)) for s in sw) / max(1, len(sw))

    def heap(self, sx, t):
        """(centre x, height px) of the heap on side sx: built by the clods the dig throws, taken back a pawful at a
        time by the fill."""
        cx, h = self.spoil.heap(sx, t)
        h = max(0.0, h - self.spoil.h0) * 1.5
        sw = [s["take"] for s in self.sweeps if s["heap"] == sx]
        took = sum(ss(_seg(t, ta - 0.05, ta + 0.2)) for ta in sw) / max(1, len(sw))
        return cx, h * (1.0 - took)

    def heap_rect(self, sx, t, sh=0.0):
        cx, h = self.heap(sx, t)
        r = 1.6 * h + 14 * min(1.0, h / 9.0)
        y = BACK + self.HEAP_DY
        return cx - r - sh, y - h, cx + r - sh, y + 6

    def soil_pieces(self, t):
        """Soil in the air or in a paw: [(x, y, size)] (world): the dig's clods (Spoil) and the fill's pawfuls."""
        out = [(x, y, s * 1.35) for _, x, y, s, _, _ in self.spoil.pieces(t, 1 / 30.0)]
        for s in self.sweeps:
            ta, td, tl = s["take"], s["let"], s["land"]
            if not (ta <= t < tl + 0.05):
                continue
            tt = min(t, td)
            x, y = self.paw_pos(s["paw"], tt, self.fill_angle(s["paw"], tt))
            y -= 5 * K
            if t > td:
                u = min(1.0, (t - td) / (tl - td))
                if s["toss"]:                              # tossed: up and over in an arc, onto the acorn
                    x1, y1 = self.HOLE + s["dx"], self.RIM + 2
                    x, y = lerp(x, x1, u), lerp(y, y1, u) - 55.0 * 4 * u * (1 - u)
                else:                                      # let go over the hole: drops in
                    y = min(self.RIM + 2, y + 0.5 * GRAV * (t - td) ** 2)
            out.append((x, y, 10.0 if s["toss"] else 9.0))
        return out

    def draw_ground(self, pg, t, sh, acorn=None):
        """The hole (it opens up with the dig), the heaps either side; the acorn in it; the soil going back in and
        the mound over it."""
        d = self.depth(t)
        if d <= 0.0:
            return
        f = self.filled(t)
        hx = self.HOLE - sh
        for sx in (-1, 1):                             # the heaps: grow with each clod, go back a pawful at a time
            cx, h = self.heap(sx, t)
            if h > 0.4:
                r = 1.6 * h + 14 * min(1.0, h / 9.0)       # (narrows as it goes: never a flat lid)
                x, y = cx - sh, BACK + self.HEAP_DY
                pg.shape(smooth([(x - r, y + 4), (x - r * 0.5, y - h * 0.62), (x, y - h),
                                 (x + r * 0.5, y - h * 0.62), (x + r, y + 4), (x, y + 7)]), SOIL, 0.12)
        if f < 1.0:
            o = min(1.0, d * 5)
            pg.flat(oval(hx, self.RIM, (self.HOLE_RX + 10) * (0.4 + 0.6 * d), (self.HOLE_RY + 5) * (0.4 + 0.6 * d)),
                    tone(SOIL, 0.04), o)                 # the dug lip
            pg.flat(oval(hx, self.RIM, self.HOLE_RX * (0.3 + 0.7 * d) * (1 - f), self.HOLE_RY * (0.3 + 0.7 * d) * (1 - f)),
                    SOIL_D, o)                           # the hole
        if acorn is not None:                          # the acorn down in the hole, under the soil going back in
            acorn()
        cover = min(1.0, f * 2.0)
        if cover > 0.0:                                # the first pawfuls heap up over the acorn
            top = self.acorn_clip(t)
            pg.c.save()
            pg.c.clipRect(skia.Rect(-4000, -4000, 9000, self.RIM + self.HOLE_RY))
            pg.flat(oval(hx, self.RIM + 2, 26 + 10 * f, max(1.0, self.RIM + 2 - top)), SOIL)
            pg.c.restore()
        if f > 0.0:
            pg.flat(oval(hx, self.RIM, self.HOLE_RX * (0.5 + 0.3 * f), 5 + 9 * f), SOIL, min(1.0, f * 3))
            pg.flat(oval(hx - 6, self.RIM - 4 - 3 * f, 24, 3), tone(SOIL, 0.08), 0.6 * f)
            wet = ease(t, self.water[0] + 0.9, self.water[1])
            if wet > 0.0:                              # damp soil, a shade darker, spreading as the water lands
                pg.flat(oval(hx, self.RIM - 2, 10 + 30 * wet, 3 + 7 * wet), (96, 72, 54), 0.55 * wet)

    def draw_soil(self, pg, t, sh):
        """The soil flying and in his paws (drawn over Digs)."""
        for x, y, s in self.soil_pieces(t):
            pg.shape(oval(x - sh, y, s, s * 0.85), tone(SOIL, -0.06), 0.15)

    # ----- the acorn
    def acorn_pos(self, t, hand):
        """The acorn: in Sprout's left hand (None = the Monster draws it there), falling, in the hole (hidden once
        the soil goes back). hand: Sprout's left hand (world) at t."""
        if t < self.drop:
            return None
        x0, y0 = hand(self.drop)
        y = min(self.ACORN_Y, y0 + 0.5 * GRAV * (t - self.drop) ** 2)
        if t >= self.drop_land and self.acorn_clip(t) <= self.ACORN_Y - 1.5 * self.ACORN_RW:
            return "buried"
        return x0, y

    ACORN_RW = 22.0 * K              # its radius on the page (newfriend_flat.ACORN_R x K)
    ACORN_Y = BACK + 10.0            # where it lies: down in the hole, most of it showing over the near lip

    def acorn_clip(self, t):
        """The acorn is drawn only above this line: the hole's near lip once it's in, then the soil the first
        pawfuls heap over it, rising until it's covered."""
        if t < self.drop:
            return 1e9                                 # (falling in, it goes behind the near lip as it drops)
        cover = min(1.0, self.filled(t) * 2.0)
        lip = self.RIM + self.HOLE_RY - 2.0
        return lip - cover * (lip - (self.ACORN_Y - 1.6 * self.ACORN_RW))

    # ----- the little tree
    def tree_grow(self, t):
        return ease(t, *self.grow)

    def draw_tree(self, pg, t, sh, cv_draw):
        g = self.tree_grow(t)
        if g <= 0.0:
            return
        cv_draw(lambda cv: sapling(cv, self.HOLE - sh, BACK + 2, K * 2.3, t, g))


TREE_BARK = np.array([116, 84, 58], np.float64)
CROWN = (np.array([62, 150, 80], np.float64), np.array([78, 172, 92], np.float64), np.array([96, 188, 104], np.float64))
# the crown's leaf clumps round the top: (dx, dy, radius) in units of k, and when each starts (0..1 of the crown)
CLUMPS = ((0, -6, 30, 0.0), (-22, 6, 24, 0.12), (22, 4, 25, 0.18), (-10, -24, 22, 0.3), (14, -22, 21, 0.38),
          (-32, -10, 17, 0.5), (32, -12, 18, 0.56), (0, 14, 20, 0.64))


def sapling(c, x, y, k, t, grow):
    """Sprout's first tree (fresh agent, FK0024 round 9: the two-leaf shoot read as a sprout, not "its very first
    tree"): it comes up as the seedling, then keeps going - the stem thickens and turns to wood as it gets taller,
    two little branches push out, and a round crown of leaves fills out around its first two leaves."""
    if grow <= 0.01:
        return
    if grow < 0.3:
        seedling(c, x, y, k, t, 0.0, grow / 0.3)
        return
    u = (grow - 0.3) / 0.7
    us = u * u * (3 - 2 * u)
    sway = 0.08 * (1 - 0.5 * us) * math.sin(t * 1.3)  # (the seedling's sway, steadying as the trunk thickens)
    ca, sa = math.cos(sway), math.sin(sway)
    q = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    H = 56 + 120 * us                                  # trunk height (k units): from the seedling's stem up
    w0, w1 = 3 + 6 * us, 3 + 1 * us                    # half-widths at the foot and the top
    lean = 6 * (1 - us)                                # the seedling's lean straightens out as it grows
    col = SEED_STEM + (TREE_BARK - SEED_STEM) * min(1.0, us * 1.3)   # green stem slowly turning to wood
    top = (lean, -H)
    c.polygon([q(-w0 * k, 0), q(w0 * k, 0), q((top[0] + w1) * k, top[1] * k), q((top[0] - w1) * k, top[1] * k)], col)
    if u > 0.25:                                       # two little branches push out from the trunk
        b = min(1.0, (u - 0.25) / 0.5)
        for sx, hh in ((-1, 0.62), (1, 0.74)):
            bx, by = lean * hh, -H * hh
            c.polyline([q(bx * k, by * k), q((bx + sx * 26 * b) * k, (by - 20 * b) * k)], col, max(1.5, 3.2 * k * b))
    tx, ty = q(top[0] * k, top[1] * k)                 # its first two leaves stay on, the crown grows round them
    for sx in (-1, 1):
        a = -math.pi / 2 + sx * 1.0 + sway
        L = 46 * k
        lf = [(tx, ty), (tx + math.cos(a - 0.35) * L * 0.57, ty + math.sin(a - 0.35) * L * 0.57),
              (tx + math.cos(a) * L, ty + math.sin(a) * L),
              (tx + math.cos(a + 0.35) * L * 0.57, ty + math.sin(a + 0.35) * L * 0.57)]
        c.polygon(lf, LEAF * 1.08)
        c.line(tx, ty, tx + math.cos(a) * L * 0.87, ty + math.sin(a) * L * 0.87, LEAF * 0.7, 2 * k)
    cx, cy = top[0], top[1] - 6
    for i, (dx, dy, r, a) in enumerate(CLUMPS):        # the crown fills out round the first two leaves
        f = min(1.0, max(0.0, (us - a) / 0.4))
        if f <= 0.0:
            continue
        px, py = q((cx + dx * us) * k, (cy + dy * us) * k)
        c.circle(px, py, r * k * f, CROWN[i % 3])


def draw_stump_can(pg, t, sh, P_, can_draw):
    """The watering can standing on the stump until Sprout picks it up."""
    if t < P_.can_take[1] - 0.25:
        can_draw(P_.STUMP - sh - 4.0, STUMP_TOP)
