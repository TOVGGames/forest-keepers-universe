"""Forest Keepers ep 14, beat 2: at the workbench every Keeper makes something for the little fir (docs/engines/
forest_keepers_christmas.md, build staging). Every piece is made where we can see it, by someone's hands, paws or
tentacles; nothing appears or changes by itself:
- Twigs takes a block from his stack, holds it with his left hand and carves it into a star with the blade on his
  right forearm (curls of wood fall off it), then slides it along the bench to Wheels;
- Wheels dips his brush in the paint pot and paints it, stroke by stroke, then lifts it into the basket;
- Hans braids the garland from a pile of pine sprigs with three tentacles; it coils up on the snow as it grows;
- Digs picks cones off the snow under the cone pine with his right paw, passes each to his left in front of him and
  sets it in the little basket on the stump; Sprout pulls ribbon off the spool and ties a bow round each one;
- Springs picks holly berries off the bush and pushes each onto a string tied to the bush; they slide down it;
- Glo lights the bench lantern with a flare of light from under his dome.
"""
import math

import numpy as np

from families.foundry.keepers.common import smoothstep

from . import christmas_flat_world as XW
from . import storycheck as sc
from .storybook import oval, rrect, smooth, tone

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
K = 0.72
BT = G - 150.0                                       # the bench top: a counter in front of Twigs and Wheels
BENCH_X, BENCH_HALF = 4462.0, 250.0
X = dict(springs=5640.0, digger=5280.0, sprout=4960.0, teeth=4560.0, wheels=4340.0, tentacles=4040.0, lantern=3820.0)
STACK = (4668.0, BT)                                 # Twigs' blocks
CARVE = (4524.0, BT)                                 # where he carves
HANDOFF = (4448.0, BT)                               # where he slides each star to Wheels
# (advisor FK0017 r3: the blocks hung over the bench's front edge and sank into it) a piece's middle on the bench: a
# star block's square (half 0.92 * STAR_R) and an acorn block stand on the top
STAR_Y = BT - 22.0
ACORN_Y = BT - 15.0
PAINT_POT = (4410.0, BT)                             # the gold paint (FK0017 r2: the red star had no red pot)
RED_POT = (4388.0, BT)                               # the red paint, beside it (both in Wheels' reach)
BRUSH = (-12.0, 38.0)                                # a brush's tip from where it is held (each pot has its own
                                                     # brush standing in it; Wheels holds it by the top)
BASKET = (4352.0, BT)                                # the ornament basket, bench's left end
BENCH_LAMP = (4700.0, BT)
STUMP = (X["sprout"] - 108.0, BACK - 52.0)          # the little stump (its top) with the ribbon spool, on Sprout's
                                                     # left: it ties with its left hand, the can stays in its right
# FK0017 r2: the cones lay behind Digs' own body and his basket read as a plank - now a little heap of five just
# clear of his right side (top ones first, all in his paw's reach) and a real basket past it that fills up
CONES = [(5414.0, BACK - 7), (5406.0, BACK + 1), (5398.0, BACK + 6), (5390.0, BACK + 10), (5383.0, BACK + 12)]
                                                     # (each one just an arm's length from his shoulder)
CONE_BASKET = (5450.0, BACK + 8)                     # Digs' basket, on his right too (nothing crosses him)
CONE_OVER = (5432.0, BACK - 39)                      # where his paw lets go of each cone, over the basket
CONE_SLOTS = [(-12, 0), (2, 0), (-5, -8), (9, -8), (-2, -14)]


def cone_slot(j):
    """Where cone j comes to rest in Digs' basket (bottom of the cone)."""
    dx, dy = CONE_SLOTS[j]
    return CONE_BASKET[0] + dx, CONE_BASKET[1] - 6 + dy
BUSH = (5750.0, BACK + 6)                            # the holly bush
STAR_R = 24.0
CONE_S = 1.2        # (FK0017 r1: three cones did not fit side by side on the little fir)
WOOD = (205, 160, 112)
GOLD, RED, BERRY, RIB = (226, 178, 72), (196, 82, 70), (184, 52, 52), (196, 70, 74)
TWIGS_SH, TWIGS_REACH = 59.0, 125.0
POTS = {GOLD: PAINT_POT, RED: RED_POT}


def twigs_blade_hand(x, t, tip):
    """World point for Twigs' right hand (arm_to) so the tip of his slid-out blade lands on `tip`: his arm keeps its
    bones (monster.py _teeth_arm / two_bone / _twigs_hand), so the hand is found by a few corrections (FK0017 r2: the
    blade was under the block, never seen touching it)."""
    from families.foundry.products.monster import TWIGS_FORE, TWIGS_UPPER, two_bone
    k = K
    sway = 4 * math.sin(t * 1.1) * k
    s = (x + sway + 82 * k, G - 350 * k + sway * 0.3 + 10 * k)
    frame = blade_frame(math.pi / 2)
    hd = (tip[0] + 50.0, tip[1] - 15.0)
    for _ in range(30):
        el = two_bone(s, hd, TWIGS_UPPER * k, TWIGS_FORE * k, 1, (0.4, 1.0))
        ux, uy, nx, ny = frame(hd, el, 1)
        tp = (hd[0] + ux * (70 * k) + nx * 21 * k, hd[1] + uy * (70 * k) + ny * 21 * k)
        hd = (hd[0] + 0.5 * (tip[0] - tp[0]), hd[1] + 0.5 * (tip[1] - tp[1]))
    return hd


def blade_frame(ref):
    """Twigs' forearm frame (monster.py _blade_frame) for his right arm with the sheath + blade on the side of the
    forearm facing direction `ref` (radians, screen: 0 = right, the usual outward side; pi/2 = down). While he carves,
    his right forearm points left across him at the block; there the usual rule flips the blade from below to above
    the forearm whenever it passes level, so the carving uses ref = down, eased from/to 0 as he brings the block and
    lets go (the forearm never points along ref then, so it never flips)."""
    rx, ry = math.cos(ref), math.sin(ref)

    def frame(hd, el, sx):
        ax, ay = hd[0] - el[0], hd[1] - el[1]
        L = math.hypot(ax, ay) + 1e-9
        ux, uy = ax / L, ay / L
        nx, ny = -uy, ux
        if sx > 0:
            if nx * rx + ny * ry < 0:
                nx, ny = -nx, -ny
        elif nx * sx < 0:
            nx, ny = -nx, -ny
        return ux, uy, nx, ny
    return frame


def _ease(a, b, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def _seg(t, t0, t1):
    return (t - t0) / max(t1 - t0, 1e-6)


def star_path(x, y, r, inner):
    import skia
    p = skia.Path()
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * inner
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    p.addPoly(pts, True)
    return p


CUTS = 6          # Twigs' strokes on each star: the corners off, then one notch each (the block turned to his blade)
NOTCH0 = -54.0    # the first notch's direction (deg): the five notches are 72 deg apart


def _cut(s, k):
    return smoothstep(min(max(s - k, 0.0), 1.0))


def carved_path(x, y, r, carved):
    """The block part-carved: carved 0 = the square block; the first stroke takes its corners off, each next one cuts
    one notch between two points (the notch facing the blade); 1 = the star."""
    import skia
    s = carved * CUTS
    half = r * 0.92

    def sq(a):                                             # where the ray at angle a leaves the square block
        return half / max(abs(math.cos(a)), abs(math.sin(a)))
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        if i % 2:                                          # a notch (dirs -54, 18, 90, 162, 234): in with its stroke
            k = (i - 1) // 2
            rr = sq(a) + (r * 0.45 - sq(a)) * _cut(s, 1 + k)
        else:                                              # a point: pared to its tip by the notches beside it
            k1, k0 = (i // 2) % 5, (i // 2 - 1) % 5
            u = 0.5 * (_cut(s, 1 + k0) + _cut(s, 1 + k1))
            r0 = min(sq(a), r)
            rr = r0 + (r - r0) * u
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    u0 = _cut(s, 0)                                        # the corners, until the first stroke takes them off
    out = []
    for i in range(10):
        out.append(pts[i])
        a0, a1 = -90 + i * 36, -90 + (i + 1) * 36
        for ca in (-135, -45, 45, 135):                    # a square corner between these two directions
            if a0 < ca < a1 or a0 < ca + 360 < a1:
                cx = x + half * math.copysign(1, math.cos(math.radians(ca)))
                cy = y + half * math.copysign(1, math.sin(math.radians(ca)))
                p0, p1 = pts[i], pts[(i + 1) % 10]
                mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                out.append((cx + (mx - cx) * u0, cy + (my - cy) * u0))
    p = skia.Path()
    p.addPoly(out, True)
    return p


def draw_star(pg, x, y, carved=1.0, paint=0.0, col=GOLD, r=STAR_R, ang=0.0):
    """A wooden star: a square block (carved 0) cut stroke by stroke into a star (1, the same size), painted left to
    right."""
    import skia
    c = pg.c
    c.save()
    c.rotate(math.degrees(ang), x, y)
    if carved < 1.0:
        pg.shape(carved_path(x, y, r, carved), WOOD, 0.1)
    else:
        pg.shape(star_path(x, y, r, 0.45), WOOD, 0.1)
    c.restore()
    if paint > 0.0:                                        # the paint edge is upright on screen, under the brush
        c.save()                                           # tip (FK0017 r2: clipped in the turned star's own frame
        c.clipRect(skia.Rect(x - r - 2, y - r - 2, x - r + 2 * r * paint, y + r + 2))     # it came in from a point)
        c.rotate(math.degrees(ang), x, y)
        pg.shape(star_path(x, y, r, 0.45), col, 0.1)
        c.restore()


def draw_cone(pg, x, y, bow=0.0, s=1.0):
    """A pine cone lying on its side-ish, scales showing; bow 0..1 the red ribbon tied round it."""
    pg.shape(oval(x, y - 12 * s, 9 * s, 13 * s), (140, 98, 64), 0.12)
    for j in range(4):
        pg.flat(oval(x, y - 20 * s + j * 6 * s, 8 * s, 2.2 * s), (112, 76, 50), 0.8)
    if bow > 0.01:
        u = smoothstep(bow)
        pg.flat(rrect(x - 9 * s, y - 15 * s, x + 9 * s, y - 11 * s, 2), RIB, u)
        for sx in (-1, 1):
            pg.flat(smooth([(x, y - 24 * s), (x + sx * 9 * u * s, y - 30 * s), (x + sx * 11 * u * s, y - 22 * s)]),
                    RIB, u)


def draw_bow(pg, x, y, tied):
    """A red ribbon bow tied from a loose strip: tied 0 the strip; 0-0.4 its left end is looped over, 0.4-0.8 its
    right end, 0.8-1 pulled tight so the tails drop (FK0017 r2: a bow grew out of a knot with no tying - each loop
    now takes up the strip it is made of, in step with Sprout's hand)."""
    u = min(max(tied, 0.0), 1.0)
    a = smoothstep(min(u / 0.4, 1.0))
    b = smoothstep(min(max((u - 0.4) / 0.4, 0.0), 1.0))
    c = smoothstep(min(max((u - 0.8) / 0.2, 0.0), 1.0))
    for sx, f in ((-1, a), (1, b)):
        if f < 0.98:                                              # what is left of this half of the strip
            x1 = x + sx * 18 * (1 - f)
            pg.flat(rrect(min(x, x1), y - 2, max(x, x1), y + 2, 2), RIB)
        if c > 0.02:                                              # the tails, as it is pulled tight
            pg.flat(smooth([(x, y + 2), (x + sx * 8, y + 16 * c + 4), (x + sx * 4, y + 18 * c + 4)]),
                    tone(RIB, -0.1))
        if f > 0.02:                                              # the loop it makes
            pg.flat(smooth([(x, y), (x + sx * 16 * f, y - 10 * f), (x + sx * 20 * f, y + 2 * f),
                            (x + sx * 10 * f, y + 4 * f)]), RIB)
    if a > 0.02:
        pg.flat(oval(x, y + 1, 3 + 2 * max(a, c), 2.5 + 1.5 * max(a, c)), tone(RIB, -0.15))


def draw_berry(pg, x, y):
    pg.flat(oval(x, y, 8.5, 8.5), BERRY)
    pg.flat(oval(x - 2.5, y - 2.5, 2.6, 2.6), (236, 140, 130), 0.8)


def stack_xy(j):
    """Where block j stands on Twigs' stack (the stars' square blocks, then the two acorn blocks)."""
    return STACK[0] - 20 * (4 - j), STAR_Y if j < 3 else ACORN_Y


class Bench:
    def __init__(self, t0):
        self.t0 = t0
        self.say = t0 + 1.5
        self.glo = (t0 + 0.8, t0 + 2.6)                   # Glo's flare lights the bench lantern
        # Twigs: three stars (each slid to Wheels), then two acorns (kept by him, for the tree)
        self.carves = []
        t = t0 + 2.0
        for j in range(3):
            c = dict(kind="star", reach=(t, t + 1.0), bring=(t + 1.0, t + 2.2), cut=(t + 2.2, t + 7.2),
                     slide=(t + 7.2, t + 8.4), back=(t + 8.4, t + 9.2))
            self.carves.append(c)
            t += 9.6
        for j in range(2):
            c = dict(kind="acorn", reach=(t, t + 1.0), bring=(t + 1.0, t + 2.2), cut=(t + 2.2, t + 6.2),
                     slide=(t + 6.2, t + 7.2), back=(t + 7.2, t + 8.0))
            self.carves.append(c)
            t += 8.4
        self.twigs_done = t
        # Wheels: each star as it arrives: dip, paint, lift it into the basket
        self.paints = []
        for j, c in enumerate(self.carves[:3]):
            a = c["slide"][1] + 0.3
            self.paints.append(dict(pick=(a - 0.8, a - 0.2), dip=(a - 0.2, a + 1.0), paint=(a + 1.0, a + 5.0),
                                    stow=(a + 5.0, a + 5.9), take=(a + 5.9, a + 6.5), lift=(a + 6.5, a + 7.7),
                                    back=(a + 7.7, a + 8.5), col=(GOLD, RED, GOLD)[j]))
        # Digs: three cones; Sprout ties a bow round each once it is in the basket
        self.cones = []
        self.bows = []                                    # Sprout: three ribbon bows, into the little basket
        t = t0 + 33.0
        for j in range(3):
            self.bows.append(dict(spool=(t, t + 0.9), pull=(t + 0.9, t + 1.8), tie=(t + 1.8, t + 3.6),
                                  put=(t + 3.6, t + 4.4), back=(t + 4.4, t + 5.1)))
            t += 5.6
        self.cones = []                                   # Digs: five cones off the heap into his basket
        t = t0 + 36.5
        for j in range(len(CONES)):
            self.cones.append(dict(down=(t, t + 1.0), lift=(t + 1.0, t + 2.2), drop=(t + 2.2, t + 2.6),
                                   back=(t + 2.6, t + 3.4)))
            t += 4.0
        # Springs: eight berries onto the string
        self.berries_on = [(BUSH[0] + dx, BUSH[1] + dy) for dx, dy in       # inside the bush's outline (r1: some
                           ((-30, -40), (-10, -62), (14, -80), (30, -48), (44, -36), (-44, -24), (0, -36), (24, -24))]
        self.picks = []
        t = t0 + 40.0
        for j in range(8):
            self.picks.append(dict(reach=(t, t + 0.9), bring=(t + 0.9, t + 1.8), slide=(t + 1.8, t + 2.6)))
            t += 3.2
        # Hans: the garland grows as he braids
        self.braid = (t0 + 2.0, t0 + 2.0 + 28.0)
        self.pan = (t0 + 29.0, t0 + 34.0)                  # the camera eases over to Sprout, Digs and Springs
        self.end = max(self.twigs_done, self.paints[-1]["back"][1], self.bows[-1]["back"][1],
                       self.picks[-1]["slide"][1], self.braid[1]) + 2.0

    # ------------------------------------------------------------------ Twigs
    def _carve(self, t):
        for j, c in enumerate(self.carves):
            if c["reach"][0] <= t < c["back"][1]:
                return j, c
        return None, None

    def piece(self, j, t):
        """(x, y, carved, kind) of Twigs' piece j at t, or None before he takes its block."""
        c = self.carves[j]
        y0 = STAR_Y if c["kind"] == "star" else ACORN_Y
        if t < c["reach"][1]:
            return stack_xy(j), 0.0, c["kind"]                                # still on his stack
        if t < c["bring"][1]:
            p = _ease(stack_xy(j), (CARVE[0], y0), _seg(t, *c["bring"]))
            return p, 0.0, c["kind"]
        carved = smoothstep(_seg(t, *c["cut"]))
        if t < c["slide"][0]:
            return (CARVE[0], y0), carved, c["kind"]
        to = (HANDOFF[0], STAR_Y) if c["kind"] == "star" else (4562.0 + 18 * (j - 3), ACORN_Y)
        return _ease((CARVE[0], y0), to, _seg(t, *c["slide"])), 1.0, c["kind"]

    def carve_turn(self, j, t):
        """How far (deg) Twigs has turned star j in his left hand, so the notch being cut faces his blade (the
        blade works on the block's right side); back upright (a star looks the same every 72 deg) as he lets go."""
        c = self.carves[j]
        if c["kind"] != "star" or t < c["cut"][0]:
            return 0.0
        s = _seg(t, *c["cut"]) * CUTS

        def at(k):                                          # stroke k: 0 the corners (upright), then notch k - 1
            return 0.0 if k <= 0 else -(NOTCH0 + 72.0 * (k - 1))
        if s < CUTS:
            k = int(s)
            if k < 1:
                return 0.0
            return at(k - 1) + (at(k) - at(k - 1)) * smoothstep(min((s - k) / 0.3, 1.0))
        end = at(CUTS - 1)
        up = round(end / 72.0) * 72.0
        return end + (up - end) * smoothstep(_seg(t, c["cut"][1], c["slide"][0] + 0.5))

    def twigs_hands(self, t, x):
        """{side: world (x, y)} for Twigs' hands, blade out amount, grip."""
        j, c = self._carve(t)
        if c is None:
            return {}, 0.0, 0.0
        (px, py), _, kind = self.piece(j, t)
        hands = {}
        blade = 0.0
        # right hand: takes the block from the stack, brings it, then carves with the blade
        if t < c["bring"][1]:
            rest = (x + 110, G - 150)
            hands[1] = _ease(rest, (px, py - 6), _seg(t, *c["reach"])) if t < c["reach"][1] else (px, py - 6)
        elif t < c["cut"][1]:
            u = _seg(t, *c["cut"])
            blade = smoothstep(min(u / 0.12, 1.0)) * (1 - smoothstep((u - 0.9) / 0.1))
            h = twigs_blade_hand(x, t, self.blade_tip_at(j, t))   # the blade's tip on the block's right side
            hands[1] = _ease((px, py - 6), h, u / 0.12) if u < 0.12 else h
        elif t < c["back"][1]:
            h = twigs_blade_hand(x, c["cut"][1], self.blade_tip_at(j, c["cut"][1] - 1e-3))
            hands[1] = _ease(h, (x + 110, G - 150), _seg(t, c["cut"][1], c["back"][1]))
        # left hand: holds it at its left side while he carves (seen there, not hidden behind it), and slides it
        if c["bring"][1] - 0.4 <= t < c["slide"][1]:
            hold = (px - 30, py - 2)
            hands[-1] = _ease((x - 110, G - 150), hold, _seg(t, c["bring"][1] - 0.4, c["bring"][1])) \
                if t < c["bring"][1] else hold
        elif c["slide"][1] <= t < c["back"][1]:
            hands[-1] = _ease((px - 30, py - 2), (x - 110, G - 150), _seg(t, c["slide"][1], c["back"][1]))
        return hands, blade, 1.0

    def twigs_ref(self, t):
        """blade_frame's ref for Twigs at t: down while he carves, eased over the bring and back (0 otherwise)."""
        for c in self.carves:
            if c["bring"][0] <= t < c["back"][1]:
                if t < c["cut"][0]:
                    return math.pi / 2 * smoothstep(_seg(t, c["bring"][0], c["cut"][0]))
                if t < c["cut"][1]:
                    return math.pi / 2
                return math.pi / 2 * (1 - smoothstep(_seg(t, c["cut"][1], c["back"][1])))
        return 0.0

    def blade_tip_at(self, j, t):
        """World point the tip of Twigs' blade is on while he carves piece j: one stroke per cut, down across the
        block's right side (the notch being cut is turned to face it), then back up just clear of the wood."""
        c = self.carves[j]
        u = min(max(_seg(t, *c["cut"]), 0.0), 1.0 - 1e-9)
        v = (u * CUTS) % 1.0
        px, py = CARVE[0], STAR_Y if c["kind"] == "star" else ACORN_Y
        if v < 0.6:
            w = smoothstep(v / 0.6)
            return px + 14, py - 22 + 30 * w
        w = smoothstep((v - 0.6) / 0.4)
        return px + 14 + 16 * math.sin(math.pi * w), py + 8 - 30 * w

    def shavings(self, t):
        """[(x, y, ang, id)] the curls of wood off each cut, falling to the bench (then lying there)."""
        out = []
        for j, c in enumerate(self.carves):
            a, b = c["cut"]
            for k in range(CUTS):
                tb = a + (k + 0.55) * (b - a) / CUTS                  # as stroke k's blade comes down the side
                if t < tb:
                    continue
                u = t - tb
                x0, y0 = CARVE[0] + 16, CARVE[1] - 6                  # where the blade is then
                vx = 40 + 14 * ((k * 7 + j * 3) % 5)
                y = y0 - 80 * u + 0.5 * 1400 * u * u
                if y >= BT - 2:                                    # landed on the bench top
                    tl = (80 + math.sqrt(80 * 80 + 2 * 1400 * (BT - 2 - y0))) / 1400
                    out.append((x0 + vx * tl, BT - 2, k * 40.0, f"curl {j}.{k}"))
                else:
                    out.append((x0 + vx * u, y, k * 40.0 + 300 * u, f"curl {j}.{k}"))
        return out

    # ------------------------------------------------------------------ Wheels
    def star_painted(self, j, t):
        p = self.paints[j]
        return smoothstep(_seg(t, *p["paint"]))

    def star_state(self, j, t):
        """(x, y, carved, paint, colour, held_by) of star j."""
        p = self.paints[j]
        (x, y), carved, _ = self.piece(j, t)
        paint = self.star_painted(j, t)
        held = None
        if t >= p["lift"][0]:
            slot = (BASKET[0] - 12 + 12 * j, BASKET[1] - 14)
            if t < p["lift"][1]:                                 # lifted up over the paint pots and down into
                u = _seg(t, *p["lift"])                          # the basket (r3: it slid along the bench through
                x, y = _ease((HANDOFF[0], STAR_Y), slot, u)      # the pots by itself)
                y -= 70.0 * math.sin(math.pi * min(max(u, 0.0), 1.0))
                held = "Wheels' right pincer"
            else:
                x, y = slot
        return x, y, carved, paint, p["col"], held

    def brush_top(self, j):
        """Where brush j's top is while it stands in its pot (its tip down in the paint)."""
        px, py = POTS[self.paints[j]["col"]]
        return px + 10.0, py - 14.0 - BRUSH[1]

    def paint_tip(self, j, t):
        """The brush tip on star j while painting: left to right across it, scrubbing up and down; the paint edge
        (star_painted) is exactly under it."""
        p = self.paints[j]
        u = min(max(_seg(t, *p["paint"]), 0.0), 1.0)
        return HANDOFF[0] - STAR_R + 2 * STAR_R * smoothstep(u), STAR_Y + 10 * math.sin(u * 40)

    def brush_held(self, t):
        """j of the brush in Wheels' pincer at t, or None (it stands in its pot)."""
        for j, p in enumerate(self.paints):
            if p["pick"][1] <= t < p["stow"][1]:
                return j
        return None

    def wheels_hands(self, t, x):
        """({1: world xy}, grip) Wheels' right pincer: to the brush in its pot, up out of the paint, paints the
        star, back into the pot; then the star into the basket."""
        rest = (x + 70, G - 165)
        for j, p in enumerate(self.paints):
            if not (p["pick"][0] <= t < p["back"][1]):
                continue
            top = self.brush_top(j)
            up = (top[0], top[1] - 18)
            t0, t1 = self.paint_tip(j, p["paint"][0]), self.paint_tip(j, p["paint"][1])
            h0, h1 = (t0[0] - BRUSH[0], t0[1] - BRUSH[1]), (t1[0] - BRUSH[0], t1[1] - BRUSH[1])
            grip = 1.0
            if t < p["pick"][1]:
                h, grip = _ease(rest, top, _seg(t, *p["pick"])), 0.0
            elif t < p["dip"][1]:
                u = _seg(t, *p["dip"])
                h = _ease(top, up, u / 0.3) if u < 0.3 else _ease(up, h0, (u - 0.3) / 0.7)
            elif t < p["paint"][1]:
                tp = self.paint_tip(j, t)
                h = (tp[0] - BRUSH[0], tp[1] - BRUSH[1])
            elif t < p["stow"][1]:
                u = _seg(t, *p["stow"])
                h = _ease(h1, up, u / 0.7) if u < 0.7 else _ease(up, top, (u - 0.7) / 0.3)
            elif t < p["take"][1]:
                h, grip = _ease(top, (HANDOFF[0], STAR_Y - 4), _seg(t, *p["take"])), 0.0
            elif t < p["lift"][1]:
                x_, y_, *_ = self.star_state(j, t)
                h = (x_, y_ - 4)
            else:
                h, grip = _ease((BASKET[0] + 12 * j - 12, BASKET[1] - 18), rest, _seg(t, *p["back"])), 0.0
            return {1: h}, grip
        return {}, 0.0

    def brush_tip(self, t, x, hand):
        return hand[0] + BRUSH[0], hand[1] + BRUSH[1]

    # ------------------------------------------------------------------ Digs + Sprout
    def digs_paws(self, t, x, sh_fn):
        """{1: angle} for Digs' right paw while he fetches cones (None outside): down to each cone at the pine's
        foot, up and over into his basket."""
        def ang_to(p):
            sx_, sy_ = sh_fn(1)
            return math.atan2(p[1] - sy_, p[0] - sx_)
        rest = math.radians(72)
        for j, c in enumerate(self.cones):
            if c["down"][0] - 0.6 <= t < c["back"][1]:
                low = ang_to((CONES[j][0], CONES[j][1] - 13 * CONE_S))
                over = ang_to(CONE_OVER)
                start = rest if j == 0 else over                       # between cones it waits over the basket,
                if t < c["down"][1]:                                    # clear of the heap (r2: it hid the heap)
                    return {1: start + (low - start) * smoothstep(_seg(t, c["down"][0] - 0.6, c["down"][1]))}
                if t < c["lift"][1]:
                    return {1: low + (over - low) * smoothstep(_seg(t, *c["lift"]))}
                if t < c["drop"][1]:
                    return {1: over}
                if j < len(self.cones) - 1:
                    return {1: over}
                return {1: over + (rest - over) * smoothstep(_seg(t, *c["back"]))}
        return None

    def cone_state(self, j, t, paw):
        """(x, y, held) of cone j; paw(side, t) -> Digs' paw xy."""
        c = self.cones[j]
        if t < c["down"][1]:
            return CONES[j][0], CONES[j][1], None
        if t < c["drop"][0]:
            p = paw(1, t)
            return p[0], p[1] + 13 * CONE_S, "Digs' right paw"
        p = paw(1, c["drop"][0])
        u = t - c["drop"][0]                                         # it drops into the basket
        (x1, y1), y0 = cone_slot(j), p[1] + 13 * CONE_S
        y = min(y0 + 0.5 * 1500 * u * u, y1)
        f = (y - y0) / (y1 - y0) if y1 > y0 else 1.0                 # sideways as it drops (no snap)
        return p[0] + (x1 - p[0]) * f, y, None if y >= y1 else "falls into the basket"

    def sprout_arm(self, t, x):
        """Sprout's left arm angle while it ties the bows (None outside). Angles in 0..2pi: the arm works on its
        left, so nothing swings round the wrong way."""
        sh = (x - 78.0 * K, G - 105.0)
        tau = 2 * math.pi
        rest = math.atan2(34, -46) % tau
        for j, b in enumerate(self.bows):
            if b["spool"][0] - 0.2 <= t < b["back"][1]:
                spool = math.atan2(STUMP[1] - 14 - sh[1], STUMP[0] - 22 - sh[0]) % tau
                hold = math.radians(200)                              # held up in front, to tie it
                into = math.atan2(STUMP[1] - 10 - sh[1], STUMP[0] + 16 - 12 * j - sh[0]) % tau
                if t < b["spool"][1]:
                    return rest + (spool - rest) * smoothstep(_seg(t, *b["spool"]))
                if t < b["pull"][1]:                                  # pulls a length off and lays it down
                    return spool + (into - spool) * smoothstep(_seg(t, *b["pull"]))
                if t < b["tie"][1]:                                   # ties it there: loops one end over, then the
                    u = _seg(t, *b["tie"])                            # other, then little tugs to pull it tight
                    if u < 0.8:                                       # (r2: it was held up and grew by itself)
                        return into + 0.24 * math.sin(u / 0.4 * math.pi) * (1 if u < 0.4 else -1)
                    return into - 0.06 * math.sin((u - 0.8) / 0.2 * math.pi * 3)
                if t < b["put"][1]:
                    return into
                return into + (rest - into) * smoothstep(_seg(t, *b["back"]))
        return None

    def bow_state(self, j, t, x):
        """(x, y, tied 0..1, held) of Sprout's bow j (None before its ribbon comes off the spool)."""
        b = self.bows[j]
        if t < b["pull"][0]:
            return None
        slot = (STUMP[0] + 16 - 12 * j, STUMP[1] - 6)          # lying on the stump top (r2: over its back edge)
        ang = self.sprout_arm(min(t, b["put"][1]), x)
        hx, hy = x - 78.0 * K + math.cos(ang) * 41, G - 105 + math.sin(ang) * 41 - 6
        if t < b["tie"][0]:                                       # pulled off, laid down where it is tied
            u = smoothstep(_seg(t, b["pull"][0] + 0.55 * (b["pull"][1] - b["pull"][0]), b["pull"][1]))
            return hx + (slot[0] - hx) * u, hy + (slot[1] - hy) * u, 0.0, "Sprout's left hand"
        if t < b["tie"][1]:
            return slot[0], slot[1], _seg(t, *b["tie"]), "Sprout's left hand"
        return slot[0], slot[1], 1.0, None

    # ------------------------------------------------------------------ Springs
    def springs_hand(self, t, x):
        sh = (x + 72.0, G - 115.0)
        for j, p in enumerate(self.picks):
            if p["reach"][0] <= t < p["slide"][0]:
                b = self.berries_on[j]
                if t < p["reach"][1]:
                    return {1: _ease((sh[0] + 30, sh[1] + 20), b, _seg(t, *p["reach"]))}
                return {1: _ease(b, self.string_pt(0.72), _seg(t, *p["bring"]))}
        return {}

    def string_pt(self, u):
        """A point along the berry string: u 0 at Springs' left hand (4828, G-110), 1 at the bush (tied)."""
        a, b = (X["springs"] - 95.0, G - 90.0), (BUSH[0] - 14, BACK - 58)      # his left hand, hanging
        x = a[0] + (b[0] - a[0]) * u
        y = a[1] + (b[1] - a[1]) * u + 42 * math.sin(math.pi * u)
        return x, y

    def berry_state(self, j, t, hand):
        p = self.picks[j]
        if t < p["reach"][1]:
            return self.berries_on[j], None
        if t < p["slide"][0]:
            return hand, "Springs' right hand"
        u0, u1 = 0.72, 0.5 - 0.055 * (j - 3.5)                   # slides down the string to its place
        u = u0 + (u1 - u0) * smoothstep(_seg(t, *p["slide"]))
        return self.string_pt(u), None if t >= p["slide"][1] else "slides down the string"

    # ------------------------------------------------------------------ Hans
    def garland_len(self, t):
        """0..1 how much is braided: a sprig's worth more each time one goes in (at the top of its fetch)."""
        n = (t - self.braid[0]) * self.FETCH - 0.5
        if n < 0:
            return 0.0
        k = math.floor(n)
        return min(1.0, (k + smoothstep(min((n - k) / 0.3, 1.0))) / self.SPRIGS)

    def hans_targets(self, t, x):
        """[(slot, world xy, grip)] Hans' working tentacles: two weaving at the braid, one fetching sprigs."""
        if not (self.braid[0] - 0.8 <= t <= self.braid[1] + 0.8):
            return []
        on = smoothstep(_seg(t, self.braid[0] - 0.8, self.braid[0])) * (1 - smoothstep(_seg(t, self.braid[1],
                                                                                            self.braid[1] + 0.8)))
        wx, wy = x - 112, G - 196
        ph = t * 2.2
        out = [(-1, (wx + 14 * math.cos(ph), wy + 10 * math.sin(ph)), on),
               (1, (wx + 14 * math.cos(ph + 2.1), wy + 10 * math.sin(ph + 2.1)), on)]
        out.append((-2, self.fetch_pt(t, x), on))
        return out

    FETCH = 0.35                                                      # sprig fetches a second
    SPRIGS = 10

    def fetch_pt(self, t, x):
        """Hans' third tentacle: from the pile (u 0) up to the braid (u 0.5) with a sprig, and back down."""
        wx, wy = x - 112, G - 196
        pile = (x - 175, BACK + 6)
        u = ((t - self.braid[0]) * self.FETCH) % 1.0
        f = math.sin(math.pi * u)
        return pile[0] + (wx - pile[0]) * f, pile[1] + (wy - pile[1]) * f

    def sprigs_taken(self, t):
        if t < self.braid[0]:
            return 0
        return min(self.SPRIGS, int((t - self.braid[0]) * self.FETCH) + 1)

    def sprig_carried(self, t):
        """True while the fetching tentacle carries a sprig up to the braid."""
        if not (self.braid[0] <= t < self.braid[1]) or self.sprigs_taken(t) > self.SPRIGS:
            return False
        return ((t - self.braid[0]) * self.FETCH) % 1.0 < 0.5

    def garland_pts(self, t, x):
        """The braid: from the weaving point down to its coil on the snow (the coil grows)."""
        L = self.garland_len(t)
        wx, wy = x - 112, G - 196
        cx, cy = x - 150, G + 10
        pts = [(wx, wy)]
        n = 14
        for i in range(1, n + 1):
            u = i / n
            pts.append((wx + (cx - wx) * u + 6 * math.sin(u * 6), wy + (cy - wy) * u))
        turns = 0.2 + 2.2 * L
        for i in range(1, int(40 * turns) + 2):
            a = i / 40 * 2 * math.pi
            r = 6 + 34 * (i / 40) / max(turns, 0.2) * L
            pts.append((cx + r * math.cos(a), cy + 0.35 * r * math.sin(a)))
        return pts

    # ------------------------------------------------------------------ drawing
    def draw_back(self, pg, t, sh, keeper):
        """The stump with the cone basket and the ribbon spool, the holly bush, Hans' sprigs (behind the Keepers)."""
        import skia
        if BENCH_X + 1200 - sh < 0 or BENCH_X - 1200 - sh > W:
            return
        sx_, sy_ = STUMP
        x_ = sx_ - sh                                             # a tree stump: straight sides, roots flaring
        p = skia.Path()                                           # at its foot, a flat ringed top (r1: it read as
        p.moveTo(x_ - 36, sy_)                                    # a sack, its sides bulged)
        p.lineTo(x_ + 36, sy_)
        p.lineTo(x_ + 38, BACK - 4)
        p.quadTo(x_ + 40, BACK + 6, x_ + 50, BACK + 8)
        p.lineTo(x_ - 50, BACK + 8)
        p.quadTo(x_ - 40, BACK + 6, x_ - 38, BACK - 4)
        p.close()
        pg.shape(p, XW.TRUNK, 0.12)
        for dx in (-22, -4, 16):                                  # bark grooves
            pg.stroke(skia.Path().moveTo(x_ + dx, sy_ + 12).lineTo(x_ + dx + 2, BACK - 2), tone(XW.TRUNK, -0.12), 2.5)
        pg.shape(oval(x_, sy_, 37, 9), tone(XW.TRUNK, 0.25), 0.0)
        for r in (24, 12):                                        # its rings
            pg.stroke(oval(x_, sy_, r, r * 9 / 37), tone(XW.TRUNK, 0.1), 1.5)
        rx, ry = x_ - 22, sy_ - 2                                 # the ribbon spool: a little reel standing on it
        pg.shape(rrect(rx - 10, ry - 18, rx + 10, ry, 3), RIB, 0.1)
        for yy in (ry - 18, ry):
            pg.shape(oval(rx, yy, 12, 3.5), tone(XW.WOOD, -0.05), 0.05)
        bx, by = BUSH
        for dx, dy, r in ((-30, -40, 34), (10, -60, 40), (40, -36, 32)):
            pg.shape(oval(bx + dx - sh, by + dy, r, r * 0.9), (64, 104, 72), 0.12)
        pg.flat(oval(bx + 6 - sh, by - 92, 40, 10), XW.SNOW, 0.9)
        for j, b in enumerate(self.berries_on):
            pg.stroke(skia.Path().moveTo(b[0] - sh, b[1]).lineTo(b[0] + 3 - sh, b[1] - 10), (52, 84, 58), 2.2)
            pg.flat(oval(b[0] + 7 - sh, b[1] - 11, 8, 4, rot=-25), (48, 92, 60))      # its stem and a holly leaf
            if t < self.picks[j]["reach"][1]:
                draw_berry(pg, b[0] - sh, b[1])
        hx = keeper("tentacles", t)[0]
        n = self.SPRIGS - self.sprigs_taken(t)                      # the sprigs left in his pile
        for k in range(n):
            _sprig(pg, hx - 175 + ((k * 7) % 10 - 5) * 7 - sh, BACK + 6 - (k % 3) * 5, 20 * ((k * 3) % 5 - 2))
        if self.sprig_carried(t):                                  # the one on its way up, in the tentacle tip
            fx, fy = self.fetch_pt(t, hx)
            _sprig(pg, fx - sh, fy, 60)

    def draw_front(self, pg, t, sh, keeper, digs_paw):
        """The bench (a counter in front of Twigs and Wheels) and everything on it, the garland, the cones, the
        berries and their string, the ribbon: all in front of the Keepers so we see the work."""
        import skia
        if BENCH_X + 1200 - sh < 0 or BENCH_X - 1200 - sh > W:
            return
        taken = t >= getattr(self, "taken", (1e9, 1e9))[0] + 0.5 * (self.taken[1] - self.taken[0]) \
            if hasattr(self, "taken") else False
        x0, x1 = BENCH_X - BENCH_HALF - sh, BENCH_X + BENCH_HALF - sh
        for lx in (x0 + 26, x1 - 26):
            pg.shape(rrect(lx - 10, BT + 18, lx + 10, G + 22, 4), tone(XW.TRUNK, 0.05), 0.0)
        pg.shape(rrect(x0, BT, x1, BT + 22, 6), XW.WOOD2, 0.12)
        u = smoothstep(_seg(t, *self.glo))
        XW.lantern(pg, BENCH_LAMP[0] - sh, BT, u, post=0.0, flicker=math.sin(t * 7))
        held = self.brush_held(t)
        for col, (qx, qy) in POTS.items():                         # each pot with its own brush standing in it
            j = next(i for i, p in enumerate(self.paints) if p["col"] == col)
            if held is None or self.paints[held]["col"] != col:
                tx_, ty_ = self.brush_top(j)
                pg.stroke(skia.Path().moveTo(tx_ - sh, ty_).lineTo(tx_ + BRUSH[0] - sh, ty_ + BRUSH[1]),
                          (150, 110, 80), 4.0)
            pg.shape(oval(qx - sh, qy - 10, 10, 11), (120, 90, 70), 0.1)
            pg.flat(oval(qx - sh, qy - 19, 8.5, 3), col)
        for i in reversed(range(5)):                               # the blocks left on his stack, each just as
            if t < self.carves[i]["reach"][1] and not taken:       # it looks once he picks it up (r3: it popped)
                bx, by = stack_xy(i)
                if i < 3:
                    draw_star(pg, bx - sh, by, 0.0)
                else:
                    _acorn(pg, bx - sh, by, 0.0)
        for x_, y_, ang, _ in self.shavings(t):
            pg.flat(oval(x_ - sh, y_, 6, 2.5, rot=ang), (232, 196, 140))
        for j in range(5):
            c = self.carves[j]
            if t < c["reach"][1] or taken:
                continue
            if j < 3:
                x_, y_, carved, paint, col, _ = self.star_state(j, t)
                draw_star(pg, x_ - sh, y_, carved, paint, col, ang=math.radians(self.carve_turn(j, t)))
            else:
                (x_, y_), carved, _ = self.piece(j, t)
                _acorn(pg, x_ - sh, y_, carved)
        if not taken:                                              # the basket: its front over the stars in it
            pg.shape(rrect(BASKET[0] - 26 - sh, BASKET[1] - 22, BASKET[0] + 26 - sh, BASKET[1], 8), (170, 130, 86),
                     0.12)
        hx = keeper("tentacles", t)[0]
        if t >= self.braid[0] and not taken:
            pts = self.garland_pts(t, hx)
            draw_garland(pg, [(q[0] - sh, q[1]) for q in pts])
        bx_, by_ = CONE_BASKET[0] - sh, CONE_BASKET[1]               # Digs' basket: its back and handle, the cones
        bc = (170, 130, 86)                                            # in it, then its front wall over them
        pg.stroke(skia.Path().moveTo(bx_ - 22, by_ - 22).cubicTo(bx_ - 18, by_ - 58, bx_ + 18, by_ - 58, bx_ + 22,
                                                                 by_ - 22), tone(bc, -0.1), 4.0)
        pg.shape(oval(bx_, by_ - 22, 27, 6), tone(bc, -0.25), 0.0)
        sx = keeper("sprout", t)[0]
        for j in sorted(range(len(CONES)), key=lambda j_: self.cone_state(j_, t, digs_paw)[1]):   # back to front
            if not taken or j >= 3:                                    # (the two he keeps stay in it)
                x_, y_, held = self.cone_state(j, t, digs_paw)
                draw_cone(pg, x_ - sh, y_, 0.0, CONE_S)
        wall = skia.Path().moveTo(bx_ - 27, by_ - 22).lineTo(bx_ + 27, by_ - 22).lineTo(bx_ + 21, by_ - 2)
        wall.quadTo(bx_, by_ + 3, bx_ - 21, by_ - 2).close()
        pg.shape(wall, bc, 0.12)
        pg.stroke(skia.Path().moveTo(bx_ - 27, by_ - 22).quadTo(bx_, by_ - 15, bx_ + 27, by_ - 22), tone(bc, 0.15), 3.0)
        for k in range(3):                                             # woven bands
            yk = by_ - 16 + 5 * k
            pg.stroke(skia.Path().moveTo(bx_ - 25 + 1.5 * k, yk).quadTo(bx_, yk + 4, bx_ + 25 - 1.5 * k, yk),
                      tone(bc, -0.12), 1.5)
        if not taken:
            for j in range(3):
                st = self.bow_state(j, t, sx)
                if st is not None:
                    draw_bow(pg, st[0] - sh, st[1], st[2])
        if taken:
            return
        p = skia.Path()                                            # the berry string, tied to the bush
        a = self.string_pt(0.0)
        p.moveTo(a[0] - sh, a[1])
        for i in range(1, 21):
            q = self.string_pt(i / 20)
            p.lineTo(q[0] - sh, q[1])
        pg.stroke(p, (214, 200, 176), 2.0)
        sp = keeper("springs", t)
        hand = self.springs_hand(t, sp[0]).get(1)
        for j in range(8):
            if t >= self.picks[j]["reach"][1]:
                q, _ = self.berry_state(j, t, hand)
                draw_berry(pg, q[0] - sh, q[1])
        for j, b in enumerate(self.bows):                          # the ribbon, pulled off the spool
            if b["pull"][0] <= t < b["pull"][1]:
                st = self.bow_state(j, t, sx)
                pg.stroke(skia.Path().moveTo(STUMP[0] - 22 - sh, STUMP[1] - 10).lineTo(st[0] - sh, st[1] + 6), RIB,
                          4.0)

    def draw_lights(self, pg, t, glo_xy, sh):
        """Glo's flare: light gathers under his dome and floats over to the bench lantern."""
        a, b = self.glo
        if a <= t < b + 0.4:
            gx, gy = glo_xy
            u = smoothstep(_seg(t, a, b))
            x = gx + (BENCH_LAMP[0] - gx) * u
            y = gy - 250 * K + (BT - 18 - gy + 250 * K) * u - 60 * math.sin(math.pi * u)
            pg.glow(x - sh, y, 60, "#ffe7a8", 0.7 * (1 - smoothstep(_seg(t, b, b + 0.4))))
            pg.flat(oval(x - sh, y, 7, 7), "#fff4d0", 1 - smoothstep(_seg(t, b, b + 0.4)))

    # ------------------------------------------------------------------ storycheck
    def things(self, t, sh, keeper, digs_paw, twigs_hand, step=1 / 30):
        out = {}
        tk = getattr(self, "taken", None)
        mid = tk[0] + 0.5 * (tk[1] - tk[0]) if tk else 1e9
        if t >= mid:                                               # taken off the bench: the deco reports them
            for x_, y_, ang, name in self.shavings(t):
                out[name] = sc.Thing(x_ - sh, y_, 6, moves="falls")
            for j in range(3, len(CONES)):                         # the two Digs keeps, still in his basket
                x_, y_, _ = self.cone_state(j, t, digs_paw)
                out[f"cone {j + 1}"] = sc.Thing(x_ - sh, y_ - 13 * CONE_S, 26 * CONE_S)
            return out
        for j in range(5):
            c = self.carves[j]
            (x_, y_), carved, kind = self.piece(j, t)
            held = None
            if c["reach"][1] <= t < c["bring"][1]:
                held = ("Twigs' right hand", twigs_hand(1, t))
            elif c["bring"][1] <= t < c["slide"][1] and c["slide"][0] <= t:
                held = ("Twigs' left hand", twigs_hand(-1, t))
            if j < 3:
                x_, y_, carved, paint, col, wh = self.star_state(j, t)
                if wh is not None:
                    held = None
                    moves = "lifted by Wheels' pincer into the basket"
                    out[f"star {j + 1}"] = sc.Thing(x_ - sh, y_, STAR_R * 2, moves=moves)
                    continue
            out[f"{kind} {j + 1}"] = sc.Thing(x_ - sh, y_, STAR_R * 2 if kind == "star" else 26.0, held=(held[0], (held[1][0] - sh, held[1][1]))
                                              if held else None)
        for x_, y_, ang, name in self.shavings(t):
            out[name] = sc.Thing(x_ - sh, y_, 6, born="shaved off by Twigs' blade", moves="falls")
        for j in range(len(CONES)):
            x_, y_, held = self.cone_state(j, t, digs_paw)
            hp = digs_paw(1, t)
            out[f"cone {j + 1}"] = sc.Thing(x_ - sh, y_ - 13 * CONE_S, 26 * CONE_S,
                                            held=(held, (hp[0] - sh, hp[1])) if held == "Digs' right paw" else None,
                                            moves=held if held == "falls into the basket" else None)
        sx = keeper("sprout", t)[0]
        for j in range(3):
            st = self.bow_state(j, t, sx)
            if st is not None:
                out[f"bow {j + 1}"] = sc.Thing(st[0] - sh, st[1], 36, born="pulled off the spool by Sprout" if
                                               t < self.bows[j]["pull"][0] + 0.05 else None,
                                               held=(st[3], (st[0] - sh, st[1] + 6)) if st[3] else None)
        sp = keeper("springs", t)
        hand = self.springs_hand(t, sp[0]).get(1)
        for j in range(8):
            p, how = self.berry_state(j, t, hand)
            out[f"berry {j + 1}"] = sc.Thing(p[0] - sh, p[1], 13, held=(how, (p[0] - sh, p[1]))
                                             if how == "Springs' right hand" else None,
                                             moves=how if how and how != "Springs' right hand" else None)
        if t >= self.braid[0]:
            out["garland"] = sc.Thing(keeper("tentacles", t)[0] - 150 - sh, G - 60, 60,
                                      born="braided by Hans' tentacles", grows="braided by Hans' tentacles")
        if t + step >= mid:                                        # the berries go with the string
            for j in range(8):
                k = f"berry {j + 1}"
                if k in out:
                    out[k].gone = ("on the string, in Springs' hands", (out[k].x, out[k].y))
        return out


def _sprig(pg, x, y, rot=0.0):
    """One little fir sprig: a twig with needles both sides."""
    import skia
    a = math.radians(rot)
    dx, dy = math.cos(a), math.sin(a)
    pg.stroke(skia.Path().moveTo(x - 12 * dx, y - 12 * dy).lineTo(x + 12 * dx, y + 12 * dy), (96, 80, 60), 1.6)
    for i in range(-2, 3):
        cx, cy = x + 5 * i * dx, y + 5 * i * dy
        for sgn in (-1, 1):
            pg.flat(oval(cx - sgn * 4 * dy, cy + sgn * 4 * dx, 4.5, 1.8, rot=rot + sgn * 50), (70, 118, 80))


def draw_garland(pg, pts, leaf=(70, 118, 80), dark=(52, 94, 64)):
    """A braided fir garland along pts (screen): a twisted core with sprig needles all along (not a rope or a
    hose: FK0017 r1)."""
    import skia
    if len(pts) < 2:
        return
    gp = skia.Path()
    gp.moveTo(*pts[0])
    for q in pts[1:]:
        gp.lineTo(*q)
    pg.stroke(gp, dark, 7.0)
    acc, i = 0.0, 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1e-6:
            continue
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        s = (6.0 - acc) % 6.0
        while s <= d:
            cx, cy = x0 + ux * s, y0 + uy * s
            sgn = 1 if i % 2 else -1
            ang = math.degrees(math.atan2(uy, ux)) + sgn * 55
            pg.flat(oval(cx - sgn * 3 * uy, cy + sgn * 3 * ux, 6.0, 2.2, rot=ang), leaf if i % 3 else tone(leaf, 0.12))
            i += 1
            s += 6.0
        acc = (acc + d) % 6.0
    for k in range(0, len(pts), 3):                         # the twist of the braid
        pg.flat(oval(pts[k][0], pts[k][1], 2.2, 2.2), tone(dark, -0.15), 0.8)


def _acorn(pg, x, y, carved):
    """A carved wooden acorn: the block (carved 0) pared round stroke by stroke into a nut with a cap (1); the cap's
    crosshatch is cut in with the last strokes. One wood all the way (r1: nothing changes by itself)."""
    import skia
    u = smoothstep(min(carved / 0.75, 1.0))
    w = 12 - 2 * u                                           # the nut: the block's lower part, rounding off
    pg.shape(rrect(x - w, y - 4 - 2 * (1 - u), x + w, y + 15 - 3 * (1 - u), 3 + 7 * u), XW.WOOD, 0.1)
    cw = 12 + 1 * u                                          # the cap: the block's top, its edge flaring a little
    pg.shape(rrect(x - cw, y - 14, x + cw, y - 1, 3 + 4 * u), tone(XW.WOOD, -0.06), 0.1)
    n = int(max(0.0, carved - 0.6) / 0.4 * 4 + 1e-6)         # the crosshatch, one score per stroke
    for i in range(min(n, 4)):
        pg.stroke(skia.Path().moveTo(x - 9 + 6 * i, y - 13).lineTo(x - 5 + 6 * i, y - 3), tone(XW.WOOD, -0.3), 1.4)
    if u > 0.99:
        pg.stroke(skia.Path().moveTo(x - 1, y - 14).lineTo(x + 1, y - 19), tone(XW.WOOD, -0.3), 2.4)
