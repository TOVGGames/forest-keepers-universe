"""Forest Keepers ep 14, beat 3: decorating the little fir (docs/engines/forest_keepers_christmas.md, build staging).
They file past it from the right, each in turn stopping right in front of it (it stands just behind their lane) to
hang what they made, then walking on to wait on its left:
- Hans lays the garland on in three swags with a tentacle;
- Wheels holds the star basket in front of him in his right pincer, hangs two stars with his left, and sets the basket
  (the gold star still in it) down at the fir's foot;
- Twigs hangs his two acorns, one from each hand;
- Sprout ties on its three bows from the bunch in its hand, scooting along under the bottom branches;
- Digs hangs his three cones from his paw;
- Springs hooks the berry string on, one end and then the other (two bounces), takes the gold star from the basket and
  puts it on top in one big bounce.
Glo lights the two lanterns with a flare each. Every piece goes from a hand to its branch and stays there; whatever
is carried rides in a hand, paw, pincer or tentacle the whole way (from the bench).
"""
import math

from families.foundry.keepers.common import smoothstep

from . import christmas_bench as CB
from . import christmas_flat_world as XW
from . import storycheck as sc
from .christmas_bench import CONE_S, GOLD, RED, STAR_R, draw_berry, draw_bow, draw_cone, draw_star, _acorn

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
K = 0.72
SPOT = XW.SPOT
ORDER = ["tentacles", "wheels", "teeth", "sprout", "digger", "springs"]
# where each piece hangs: every one in plain view, none on another (FK0017 r1: cones stacked on cones and bows). Each
# Keeper works from beside the fir, never in front of it: Hans, Twigs and Digs from its left (right hand), Wheels and
# Sprout from its right (left hand: Sprout's right one holds its watering can), Springs from both sides in turn.
HANG = {
    "star 1": (SPOT + 14, G - 228), "star 2": (SPOT + 42, G - 180),
    "acorn 1": (SPOT + 16, G - 268), "acorn 2": (SPOT - 30, G - 205),
    # (advisor FK0017 r3: it stepped left for each next bow and its body hid the ones already on) the leftmost first,
    # then it steps right, away from them
    "bow 1": (SPOT + 24, G - 123), "bow 2": (SPOT + 52, G - 128), "bow 3": (SPOT + 80, G - 133),
    "cone 1": (SPOT - 58, G - 160), "cone 2": (SPOT - 30, G - 158), "cone 3": (SPOT - 6, G - 150),
    "top star": (SPOT, G - 300),
}
SWAGS = [((SPOT - 66, G - 150), (SPOT + 66, G - 146), 18), ((SPOT - 52, G - 198), (SPOT + 50, G - 196), 14),
         ((SPOT - 34, G - 244), (SPOT + 32, G - 242), 10)]
STRING = ((SPOT - 58, G - 190), (SPOT + 58, G - 186), 26)
BASKET_DOWN = (SPOT + 370.0, BACK + 6.0)          # Wheels sets it down well right of the fir, out of everyone's
WHEELS_SET = SPOT + 240.0                          # way (clear of Sprout's can); he rolls over to here to do it
# where they wait once their part is done (the night starts from here: all in view, r1)
WAIT = {"tentacles": SPOT - 1060.0, "wheels": SPOT - 880.0, "teeth": SPOT - 730.0, "sprout": SPOT - 590.0,
        "digger": SPOT - 420.0, "springs": SPOT + 240.0}
# while the others decorate, the ones done wait a little further off (out of the close shots, nobody cut by the frame's
# edge); at dusk (an act break) they come in to WAIT
# (advisor FK0017 r3: Digs waited at SPOT - 420, inside the next close shot, and seemed to jump there) all of them
# clear of the left close shot's edge (SPOT - 540)
DECO_WAIT = dict(WAIT, tentacles=SPOT - 1300.0, wheels=SPOT - 1120.0, teeth=SPOT - 970.0, sprout=SPOT - 830.0,
                 digger=SPOT - 680.0)
IN_STEPS = 100.0    # the last steps of each Keeper's walk up to the fir, seen after the act break
LAMP_SHOT = (SPOT + 50.0, 1.6)                     # Glo lights the lanterns: him, both lanterns and Digs in view
V = 100.0
SPROUT_L, SPRINGS_L = 57.0 * K, 47.0 * K
DIGS_SH, DIGS_ARM = 118.0 * K, 95.0 * K
SH_Y = G - 150 * K + 4 * K                        # Sprout's and Digs' shoulders
SIZES = {"star": STAR_R * 2, "acorn": 26.0, "cone": 26.0 * CONE_S, "bow": 36.0}   # one size per piece, everywhere
GAP = 8.5           # s from one Keeper leaving the fir to the next arriving: all but its ends cut out (act break)
DECO_CAM = SPOT - 280.0
CLOSE_Z, CLOSE_Y = 2.0, G - 200.0                 # the close shots of each Keeper at the fir


def reach_x(px, py, sh, L, side):
    """Where a Keeper stands (its middle) so that its `side` hand, at full stretch L from a shoulder `sh` out from its
    middle at SH_Y, is right at (px, py)."""
    dy = py - SH_Y
    return px - side * (math.sqrt(max(L * L - dy * dy, 0.0)) + sh)


SPROUT_XS = [reach_x(*HANG[f"bow {j}"], 78 * K, SPROUT_L, -1) for j in (1, 2, 3)]
DIGS_XS = [reach_x(*HANG[f"cone {j}"], DIGS_SH, DIGS_ARM, 1) for j in (1, 2, 3)]
WORK = {"tentacles": SPOT - 160.0, "wheels": SPOT + 140.0, "teeth": SPOT - 130.0, "sprout": SPROUT_XS[0],
        "digger": DIGS_XS[0], "springs": SPOT - 164.0}
SPRINGS_R, SPRINGS_BASKET, SPRINGS_TOP = SPOT + 164.0, BASKET_DOWN[0] + 97.0, SPOT + 105.0
SIDE = {"tentacles": -1, "wheels": 1, "teeth": -1, "sprout": 1, "digger": -1, "springs": -1}   # of the fir
CLOSE_X = {-1: SPOT - 60.0, 1: SPOT + 200.0}       # close shots: the fir and whoever works at it, nobody cut in half
STAR_SQUAT = 1.2    # Springs squats this deep (spring squash) to take the gold star out of the basket


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def _ease(p, q, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


def swag(a, b, sag, u=1.0, n=16):
    pts = []
    m = max(2, int(n * u) + 1)
    for i in range(m):
        v = u * i / (m - 1)
        pts.append((a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v + sag * math.sin(math.pi * v)))
    return pts


# what each one carries from the bench: (holder, side, source on the bench, carry offset from its middle, hang)
def _pieces(bench, kp_x):
    acorn = lambda j: (4548.0 + 18 * (j - 3), CB.ACORN_Y)                                # noqa: E731
    return {
        "star 1": ("wheels", -1, (CB.BASKET[0] - 12, CB.BASKET[1] - 14), (12, -190)),
        "star 2": ("wheels", -1, (CB.BASKET[0], CB.BASKET[1] - 14), (24, -190)),
        "gold star": ("wheels", 1, (CB.BASKET[0] + 12, CB.BASKET[1] - 14), (36, -190)),
        "acorn 1": ("teeth", 1, acorn(3), (110, -190)),
        "acorn 2": ("teeth", 1, acorn(4), (110, -190)),
        "bow 1": ("sprout", -1, (CB.STUMP[0] + 16, CB.STUMP[1] - 6), None),     # (off the stump at its left, in
        "bow 2": ("sprout", -1, (CB.STUMP[0] + 4, CB.STUMP[1] - 6), None),      # its free left hand)
        "bow 3": ("sprout", -1, (CB.STUMP[0] - 8, CB.STUMP[1] - 6), None),
        "cone 1": ("digger", 1, CB.cone_slot(0), None),            # (the other two stay in the basket)
        "cone 2": ("digger", 1, CB.cone_slot(1), None),
        "cone 3": ("digger", 1, CB.cone_slot(2), None),
    }


class Deco:
    """One at a time, from the bench to the fir, hang what they made, and off to wait on its left. Every walk there
    and away happens in an act break (only its last / first steps show, FK0017 r1: long walks); each Keeper's work is
    seen close (r1: two tiny wide shots)."""

    def __init__(self, t0, start_x, bench):
        self.t0, self.bench = t0, bench
        self.bench_hans_x = start_x["tentacles"]
        self.pick = (t0 + 0.3, t0 + 1.8)                            # each takes what they made off the bench
        self.sprout_pick = self.pick                                   # Sprout takes its bows off the stump
        self.pieces = _pieces(bench, start_x)
        self.keys = {kd: [(t0, start_x[kd])] for kd in ORDER}
        # Sprout takes its bows off the stump at its left (left hand; the can stays in its right), Digs his cones
        # from his basket at his right
        here = {kd: self.keys[kd][-1][1] for kd in ORDER}
        self.turns, self.cuts, self.shots, self.hang_t = {}, [], [], {}

        def go(kd, x_to, t_from, t_to):
            self.keys[kd] += [(t_from, here[kd]), (t_to, x_to)]
            here[kd] = x_to

        def close(a_, b_, side):
            self.shots.append((a_, b_, CLOSE_X[side], CLOSE_Y, CLOSE_Z))

        prev = None
        for i, kd in enumerate(ORDER):
            d = abs(WORK[kd] - here[kd]) / V + 1.0
            if prev is None:                                       # Hans sets off first (the rest wait at the bench)
                start = self.pick[1] + 0.4
                arrive = start + d
                self.cuts.append((start + 1.5, arrive - 1.0))
                # in the break the coil goes over to his fir-side leg (r2: it was passed across his belly in view)
                self.hans_swap = (start + 1.5 + arrive - 1.0) / 2 - 0.4
                go(kd, WORK[kd], start, arrive)
            else:
                # (advisor FK0017 r3: the next one was seen walking in at the frame's edge, then stood at the fir
                # after the break) it waits at the bench until the break, walks over inside it, and only its last
                # steps up to the fir are seen
                arrive = prev + GAP
                start = prev + 0.7
                self.cuts.append((start, arrive - 1.0))
                go(kd, WORK[kd] + IN_STEPS * SIDE[kd], start, arrive - 1.0)   # from its own side (not across the fir)
                go(kd, WORK[kd], arrive - 1.0, arrive)
            a = arrive
            seen = arrive - 1.0                                    # the close shot from the end of the act break
            if kd == "tentacles":
                self.say2 = a + 0.2
                self.swag_t = [(a + 1.0 + 2.6 * j, a + 3.2 + 2.6 * j) for j in range(3)]
                leave = a + 9.0
            elif kd == "wheels":
                # (star 2 only once his pincer is back from star 1: it took over his pincer mid-way, a snap)
                self.hang_t.update({"star 1": (a + 0.9, a + 3.0), "star 2": (a + 4.8, a + 6.8)})
                go(kd, WHEELS_SET, a + 7.1, a + 8.3)
                self.basket_down = (a + 8.5, a + 9.8)
                leave = a + 10.6
            elif kd == "teeth":
                # (r2: 0.2 s between them his arm snapped back down - now a calm 0.8 s return between)
                self.hang_t.update({"acorn 1": (a + 0.8, a + 2.9), "acorn 2": (a + 3.9, a + 6.3)})
                leave = a + 7.0
            elif kd == "sprout":                                   # ties each bow, a little step between
                self.hang_t.update({"bow 1": (a + 0.8, a + 3.1), "bow 2": (a + 4.6, a + 6.8),
                                    "bow 3": (a + 8.2, a + 10.4)})
                go(kd, SPROUT_XS[1], a + 3.4, a + 4.4)
                go(kd, SPROUT_XS[2], a + 7.0, a + 8.0)
                leave = a + 11.0
            elif kd == "digger":                                   # hangs each cone, a little step between
                self.hang_t.update({"cone 1": (a + 0.8, a + 3.1), "cone 2": (a + 4.4, a + 6.7),
                                    "cone 3": (a + 8.0, a + 10.3)})
                go(kd, DIGS_XS[1], a + 3.4, a + 4.2)
                go(kd, DIGS_XS[2], a + 7.0, a + 7.8)
                leave = a + 10.9
            else:                                                  # Springs: the berry string's left end, an act
                close(seen, a + 3.0, -1)                           # break, its right end, the gold star, the top
                self.string_on = [(a + 0.8, a + 1.6)]
                b1 = (a + 0.8, a + 2.4, 70.0)
                go(kd, SPRINGS_R, a + 2.8, a + 8.8)
                self.cuts.append((a + 3.0, a + 7.8))
                go("digger", WAIT["digger"], a + 3.3, a + 7.5)   # (in that break, out of shot) Digs back in
                                                                   # for the lantern shot
                r = a + 8.8
                self.string_on.append((r + 0.8, r + 1.6))
                b2 = (r + 0.8, r + 2.4, 70.0)
                go(kd, SPRINGS_BASKET, r + 2.8, r + 4.8)
                self.star_take = (r + 5.0, r + 6.4)
                go(kd, SPRINGS_TOP, r + 6.8, r + 9.2)
                self.star_up = (r + 9.6, r + 12.0)
                self.bounces = [b1, b2, (self.star_up[0], self.star_up[1], 175.0)]
                self.star_grab = self.star_take[0] + 0.55            # the bottom of his squat
                self.star_on = self.star_up[0] + 0.55 * (self.star_up[1] - self.star_up[0])   # top of the bounce
                self.hang_t["top star"] = (self.star_up[0], self.star_on)
                leave = r + 12.6
                seen = a + 7.8
                side_ = 1
            if kd != "springs":
                side_ = SIDE[kd]
            dw = abs(DECO_WAIT[kd] - here[kd]) / V + 1.0
            if kd == "springs":
                done = leave + dw
                go(kd, DECO_WAIT[kd], leave, done)
            else:                                                  # sets off (seen), the rest inside the break, so
                done = leave + GAP - 1.2                           # he's out of the next close shot when it opens
                go(kd, here[kd] - V * 0.7 * (1 if DECO_WAIT[kd] < here[kd] else -1), leave, leave + 0.7)
                go(kd, DECO_WAIT[kd], leave + 0.7, done)
            close(seen, (leave + 0.7) if kd != "springs" else done, side_)
            self.turns[kd] = dict(start=start, arrive=arrive, leave=leave, done=done)
            prev = leave
        sd = self.turns["springs"]["done"]
        self.lamps = [(sd + 0.6, sd + 2.4), (sd + 3.0, sd + 4.8)]
        self.end = self.lamps[1][1] + 3.5
        self.dusk_cut = (self.end + 0.4, self.end + 4.6)          # Glo floats over to the others (an act break)
        self.night_t0 = self.end + 5.0
        self.cuts.append(self.dusk_cut)
        self.shots.append((sd, self.dusk_cut[0], LAMP_SHOT[0], G + 70.0 - 540.0 / LAMP_SHOT[1], LAMP_SHOT[1]))
        for kd in ORDER:                                           # in to their places for the evening (in the break)
            if DECO_WAIT[kd] != WAIT[kd]:
                go(kd, WAIT[kd], self.dusk_cut[0] + 0.2, self.dusk_cut[1] - 0.2)
        self.say = self.say2
        for kd in ORDER:
            ks = sorted(set(self.keys[kd]))
            self.keys[kd] = ks + [(self.night_t0, ks[-1][1])]

    # ------------------------------------------------------------------ hands
    def carry_pt(self, kd, side, x, y):
        """Where a holder keeps what it carries (world), relative to where it is."""
        return {("wheels", 1): (x, y - 95), ("wheels", -1): (x - 92, y - 176),   # the basket low in front of him
                                                                                 # (r1: over his face; now both
                                                                                 # pincers reach into it)
                ("teeth", 1): (x + 104, y - 188), ("teeth", -1): (x - 104, y - 188),
                ("sprout", 1): (x + 78 * K + 30, y - 120), ("sprout", -1): (x - 78 * K - 30, y - 120),
                ("digger", 1): (x + 118 * K + 50, y - 120),
                ("springs", 1): (x + 95.0, y - 90), ("springs", -1): (x - 95.0, y - 90),
                ("tentacles", -1): (x - 130, y - 190)}[(kd, side)]

    def hand_target(self, kd, side, t, x, y):
        """Where holder kd's hand on `side` reaches at t (world), or None (its own pose)."""
        if t < self.pick[0] - 0.5 or t > self.end:
            return None
        carry = self.carry_pt(kd, side, x, y)
        mine = [(n, p) for n, p in self.pieces.items() if p[0] == kd and p[1] == side]
        if kd == "wheels" and side == 1:                           # the basket, held in front of him
            if self.basket_down[0] <= t:
                dn = (BASKET_DOWN[0], BASKET_DOWN[1] - 30)
                if t < self.basket_down[1]:
                    return _ease(carry, dn, _seg(t, *self.basket_down))
                return _ease(dn, (x + 92, y - 96), _seg(t, self.basket_down[1], self.basket_down[1] + 0.8)) \
                    if t < self.basket_down[1] + 0.8 else None
            if t < self.pick[1]:
                src = (CB.BASKET[0], CB.BASKET[1] - 26)
                u = _seg(t, *self.pick)
                return _ease(src, carry, (u - 0.5) * 2) if u > 0.5 else _ease((x + 70, y - 165), src, u * 2)
            return carry
        if kd == "wheels" and side == -1:                          # takes each star out of the basket, hangs it
            for n in ("star 1", "star 2"):
                a, b = self.hang_t[n]
                if a - 0.9 <= t < b + 0.9 and not (n == "star 1" and t >= self.hang_t["star 2"][0] - 0.9):
                    bx, by = self.carry_pt("wheels", 1, x, y)
                    src = (bx + {"star 1": -12, "star 2": 0}[n], by + 20)          # right where it sits in the basket
                    if t < a:
                        return _ease((x - 90, y - 160), src, _seg(t, a - 0.9, a))
                    if t < b:
                        return _ease(src, HANG[n], _seg(t, a, a + 0.65 * (b - a)))
                    return _ease(HANG[n], (x - 90, y - 160), _seg(t, b, b + 0.9))
            return None
        if kd == "tentacles":
            right = (x + 130, y - 190)
            carry = _ease(carry, right, _seg(t, self.hans_swap, self.hans_swap + 0.8)) if t >= self.hans_swap else carry
            for j, (a, b) in enumerate(self.swag_t):
                sa, sb, sag = SWAGS[j]
                if j == 0 and a - 0.6 <= t < a:
                    return _ease(carry, sa, _seg(t, a - 0.6, a))
                if a <= t < b:
                    pts = swag(sa, sb, sag, 1.0, 40)
                    u = smoothstep(_seg(t, a, b))
                    f = u * (len(pts) - 1)
                    i0 = min(int(f), len(pts) - 2)
                    w = f - i0
                    return (pts[i0][0] + (pts[i0 + 1][0] - pts[i0][0]) * w, pts[i0][1] + (pts[i0 + 1][1] - pts[i0][1]) * w)
                nxt = self.swag_t[j + 1][0] if j + 1 < len(self.swag_t) else None
                if nxt is not None and b <= t < nxt:
                    return _ease(sb, SWAGS[j + 1][0], _seg(t, b, nxt))
                if nxt is None and b <= t < b + 0.6:
                    return _ease(sb, carry, _seg(t, b, b + 0.6))
            if t < self.pick[1]:
                src = (x - 150, G + 6)
                u = _seg(t, *self.pick)
                return _ease(src, carry, (u - 0.5) * 2) if u > 0.5 else _ease((x - 60, y - 120), src, u * 2)
            return carry if t < self.swag_t[-1][1] else None
        if kd == "springs":
            sp_a = self.turns["springs"]["arrive"]
            if t < self.pick[1]:                                   # the string's free end, off the bush
                if side == 1:
                    src = self.bench.string_pt(1.0)
                    u = _seg(t, *self.pick)
                    return _ease(src, carry, (u - 0.5) * 2) if u > 0.5 else _ease(carry, src, u * 2)
                return self.bench.string_pt(0.0)
            ends = {1: STRING[0], -1: STRING[1]}
            for (a, b), s_ in zip(self.string_on, (1, -1)):
                if s_ == side and a <= t < b + 0.6:
                    if t < a + 0.6 * (b - a):
                        return _ease(carry, ends[side], _seg(t, a, a + 0.6 * (b - a)))
                    if t < b:
                        return ends[side]
                    return _ease(ends[side], carry, _seg(t, b, b + 0.6))
            if side == -1:
                a, b = self.star_take
                if a - 0.4 <= t < self.star_on + 0.6:
                    src = (BASKET_DOWN[0] + 12, BASKET_DOWN[1] - 10)
                    held = (x - 170, y - 60)                       # out low at his side (r2: held up by his face,
                                                                   # the star was drawn over his mouth and eye)
                    if t < self.star_grab:
                        return _ease(carry, src, _seg(t, a - 0.4, self.star_grab))
                    if t < self.star_up[0]:
                        return _ease(src, held, _seg(t, self.star_grab, self.star_up[0]))
                    if t < self.star_on:
                        return _ease(held, HANG["top star"], _seg(t, self.star_up[0], self.star_on))
                    return _ease(HANG["top star"], carry, _seg(t, self.star_on, self.star_on + 0.6))
            if t < sp_a + 0.8:
                return carry
            on = self.string_on[0 if side == 1 else 1][1]
            return carry if t < on else None
        if kd == "sprout" and (side == 1 or t < self.sprout_pick[1]):   # the can stays in its right hand; the left
            a, b = self.sprout_pick                                        # takes the bows off the stump
            if side == 1 or t < a:
                return None
            sh_ = (x - 78 * K, y - 150 * K + 4 * K)
            rest = (sh_[0] - 46 / 57.2 * SPROUT_L, sh_[1] + 34 / 57.2 * SPROUT_L)          # its arm's own pose
            src = self.pieces["bow 2"][2]
            u = _seg(t, a, b)
            return _ease(src, carry, (u - 0.5) * 2) if u > 0.5 else _ease(rest, src, u * 2)
        # a bunch in one hand (Twigs: one acorn each; Sprout, Digs: three each), hung one at a time
        if not mine:
            return None
        if t < self.pick[1]:
            src = mine[0][1][2]
            u = _seg(t, *self.pick)
            rest = (x + side * 100, y - 140)
            return _ease(src, carry, (u - 0.5) * 2) if u > 0.5 else _ease(rest, src, u * 2)
        mine = sorted(mine, key=lambda np_: self.hang_t[np_[0]][0])
        for i, (n, p) in enumerate(mine):
            a, b = self.hang_t[n]
            nxt = self.hang_t[mine[i + 1][0]][0] if i + 1 < len(mine) else b + 0.8
            if a <= t < nxt:
                off, lift = self.fan_off(n, t)                     # the hand puts that one (not its middle) there
                hn = (HANG[n][0] - off, HANG[n][1] - lift)
                if t < b:
                    return _ease(carry, hn, _seg(t, a, a + 0.65 * (b - a)))
                return _ease(hn, carry, _seg(t, b, min(b + 0.8, nxt)))
        last = max(self.hang_t[n][1] for n, _ in mine)
        return carry if t < last else None

    _hand_target = hand_target

    def hand_target(self, kd, side, t, x, y):
        tg = self._hand_target(kd, side, t, x, y)
        if tg is None or kd != "wheels":
            return tg
        # Wheels' pincer path from the basket to the fir crossed his own shoulder (the two-bone arm can't fold onto
        # its root: the elbow flew off, storycheck): it bows out round the shoulder instead (continuous)
        sx_, sy_ = x + side * 72.0, y - 142.7
        d = math.hypot(tg[0] - sx_, tg[1] - sy_)
        push = max(0.0, 46.0 - d)
        return tg[0] + side * 0.96 * push, tg[1] + 0.29 * push

    def springs_bounce(self, t):
        """(lift px, squash) for Springs' bounces at the fir."""
        a0 = self.star_take
        for a, b, hgt in self.bounces:
            if a - 0.35 <= t < b:
                if t < a:
                    return 0.0, 0.6 * math.sin(math.pi * _seg(t, a - 0.35, a))       # squash and push off
                u = _seg(t, a, b)
                return hgt * K / 0.72 * math.sin(math.pi * u), 0.0
        if a0[0] - 0.3 <= t < a0[1]:                                # squats down to reach the basket
            u = _seg(t, a0[0] - 0.3, a0[1])
            return 0.0, STAR_SQUAT * math.sin(math.pi * u)
        return 0.0, 0.0

    # ------------------------------------------------------------------ the pieces
    def piece_at(self, name, t, hand):
        """(x, y, holder) of a carried piece: on the bench, in its hand (hand(kd, side, t) -> world xy), on the fir."""
        kd, side, src, _ = self.pieces[name]
        if t < self.pick[0] + 0.5 * (self.pick[1] - self.pick[0]):
            return src[0], src[1], None
        if name in self.hang_t and t >= self.hang_t[name][1]:
            return HANG[name][0], HANG[name][1], None
        if name == "gold star":
            if t >= self.basket_down[1] and t < self.star_grab:
                return BASKET_DOWN[0] + 12, BASKET_DOWN[1] - 10, None
            if t >= self.star_grab:
                hx, hy = hand("springs", -1, t)
                if t >= self.star_on:
                    return HANG["top star"][0], HANG["top star"][1], None
                w = smoothstep(_seg(t, self.star_grab, self.star_grab + 0.5)) *                     (1 - smoothstep(_seg(t, self.star_up[0] - 0.4, self.star_up[0])))
                return hx - 26 * w, hy - 6 * w, "Springs' left hand"   # by its point, so his hand shows
        hx, hy = hand(kd, side, t)
        x_, y_, who = self._held_at(name, t, hand, kd, side, hx, hy)
        if t < self.pick[1]:                                       # it eases off the bench into the hand
            u = smoothstep(_seg(t, self.pick[0] + 0.5 * (self.pick[1] - self.pick[0]), self.pick[1]))
            return src[0] + (x_ - src[0]) * u, src[1] + (y_ - src[1]) * u, who
        return x_, y_, who

    def _held_at(self, name, t, hand, kd, side, hx, hy):
        if kd == "wheels" and side == -1:                          # in the basket until his left pincer takes it
            bx, by = hand("wheels", 1, t)
            a = self.hang_t.get(name, (1e9, 1e9))[0]
            if t < a:
                off = {"star 1": -12, "star 2": 0, "gold star": 12}[name]
                return bx + off, by + 20, "the basket in Wheels' right pincer"
            return hx, hy, "Wheels' left pincer"
        if kd == "wheels" and side == 1:
            bx, by = hand("wheels", 1, t)
            return bx + 12, by + 20, "the basket in Wheels' right pincer"
        idx = int(name.split()[-1]) if name.split()[-1].isdigit() else 0
        if kd == "sprout" and t < self.sprout_pick[1]:             # on the stump until its left hand takes them
            a, b = self.sprout_pick
            src = self.pieces[name][2]
            u = smoothstep(_seg(t, a + 0.5 * (b - a), b))
            off, lift = self.fan_off(name, t)
            return (src[0] + (hx + off - src[0]) * u, src[1] + (hy + lift - src[1]) * u,
                    "the stump" if u < 0.5 else "Sprout's left hand")
        a = self.hang_t[name][0]
        off, lift = self.fan_off(name, t)
        who = {"teeth": "Twigs", "sprout": "Sprout", "digger": "Digs"}[kd]
        return hx + off, hy + lift, f"{who}'s {'right' if side > 0 else 'left'} hand"

    def fan_off(self, name, t):
        """(dx, dy) of a piece in a holder's bunch from its hand: fanned out wide enough to count (r2: 9 px apart
        they read as one, and a 'new' one seemed to appear after each hang), closing up round the ones left as
        each is hung."""
        kd, side = self.pieces[name][:2]
        mine = sorted((n for n, p_ in self.pieces.items() if p_[0] == kd and p_[1] == side),
                      key=lambda n: self.hang_t[n][0])
        f = sum(smoothstep(_seg(t, self.hang_t[n][1], self.hang_t[n][1] + 0.8)) for n in mine)
        mid = (f + len(mine) - 1) / 2
        dx = (mine.index(name) - mid) * {"digger": 22.0, "sprout": 24.0, "teeth": 22.0}.get(kd, 9.0)
        return dx, -abs(dx) * 0.25

    def deco_on(self, t, top_star=True):
        on = {n: HANG[n] for n, (a, b) in self.hang_t.items() if t >= b and (top_star or n != "top star")}
        sw = [smoothstep(_seg(t, a, b)) for a, b in self.swag_t]
        st = [t >= b for a, b in self.string_on]
        return on, sw, st

    def draw_on_fir(self, pg, t, sh, top_star=True, removed=None):
        import skia
        removed = removed or (lambda name: False)
        on, sw, st = self.deco_on(t, top_star)
        for j, ((a, b, sag), u) in enumerate(zip(SWAGS, sw)):
            if u > 0.01 and not removed(f"swag {j + 1}"):
                pts = swag(a, b, sag, u)
                p = skia.Path()
                p.moveTo(pts[0][0] - sh, pts[0][1])
                for q in pts[1:]:
                    p.lineTo(q[0] - sh, q[1])
                pg.stroke(p, (70, 116, 78), 7.0)
                pg.stroke(p, (104, 152, 100), 2.5)
        for name, (x, y) in on.items():
            if not removed(name):
                self.draw_piece(pg, "gold star" if name == "top star" else name, x - sh, y)

    def draw_piece(self, pg, name, x, y):
        if "star" in name:
            col = GOLD if name in ("star 1", "gold star") else RED
            draw_star(pg, x, y, 1.0, 1.0, col, STAR_R)
        elif name.startswith("acorn"):
            _acorn(pg, x, y, 1.0)
        elif name.startswith("bow"):
            draw_bow(pg, x, y, 1.0)
        elif name.startswith("cone"):
            draw_cone(pg, x, y + 13 * CONE_S, 0.0, CONE_S)

    def string_pts(self, t, hand):
        """The berry string: from the bush/hands to the fir (its two ends)."""
        sp = self.turns["springs"]
        if t < self.pick[0]:
            return None
        hooked = [t >= b for a, b in self.string_on]
        a_ = STRING[0] if hooked[0] else hand("springs", 1, t)
        b_ = STRING[1] if hooked[1] else hand("springs", -1, t)
        sag = 26 if all(hooked) else 34
        return swag(a_, b_, sag, 1.0, 20)

    def draw_carried(self, pg, t, sh, hand, layer="all"):
        """Everything in someone's hands right now (in front of them) and the basket. layer "back": only what stands
        on the ground or hangs on the fir (the basket set down, the string hooked at both ends), drawn behind the
        Keepers; "front": only what someone holds (FK0017 advisor r1: the hooked garland and the basket were drawn
        over everyone who passed in front of the fir)."""
        import skia
        from .storybook import rrect as rr
        down = t >= self.basket_down[1]
        hb = self.basket_override(t) if getattr(self, "basket_override", None) else None
        if hb is not None:                                        # the morning: Wheels carries it off (the plan's)
            down = not hb[2]
        hooked = all(t >= b for a, b in self.string_on)
        show_basket = layer == "all" or (layer == "back") == down
        show_string = layer == "all" or (layer == "back") == hooked
        # the basket: in Wheels' right pincer, then at the fir's foot
        if t >= self.pick[0] and show_basket:
            if t < self.basket_down[1]:
                bx, by = hand("wheels", 1, t) if t >= self.pick[0] + 0.5 * (self.pick[1] - self.pick[0]) else \
                    (CB.BASKET[0], CB.BASKET[1] - 26)
                bx, by = bx, by + 26
            else:
                bx, by = BASKET_DOWN if hb is None else hb[:2]
            if getattr(self, "basket_heap", None):
                self.basket_heap(pg, t, bx, by, sh)
            pg.shape(rr(bx - 34 - sh, by - 22, bx + 34 - sh, by, 8), (170, 130, 86), 0.12)
            pg.stroke(skia.Path().moveTo(bx - 26 - sh, by - 20).quadTo(bx - sh, by - 52, bx + 26 - sh, by - 20),
                      (150, 112, 74), 4.0)
        for name in self.pieces:
            if t < self.pick[0]:
                continue
            x, y, who = self.piece_at(name, t, hand)
            # FK0017 r2 (3:06.5): the gold star lying in the set-down basket stands on the ground with it, so it is
            # drawn in the back layer (behind Springs reaching for it), not over him
            in_basket = name == "gold star" and who is None and self.basket_down[1] <= t < self.star_grab
            if layer != "all" and (layer == "back") != in_basket:
                continue
            if who is None and (name not in self.hang_t or t < self.hang_t[name][1]) and \
                    t < self.pick[0] + 0.5 * (self.pick[1] - self.pick[0]):
                continue                                          # (still on the bench: the bench draws it)
            if who is not None or name == "gold star":
                if name == "gold star" and t >= self.star_on:
                    continue
                self.draw_piece(pg, name, x - sh, y)
        pts = self.string_pts(t, hand)
        if pts is not None and show_string and not getattr(self, "string_gone", lambda tt: False)(t):
            p = skia.Path()
            p.moveTo(pts[0][0] - sh, pts[0][1])
            for q in pts[1:]:
                p.lineTo(q[0] - sh, q[1])
            pg.stroke(p, (214, 200, 176), 2.0)
            for j in range(8):
                q = pts[2 + j * 2]
                draw_berry(pg, q[0] - sh, q[1] + 4)
        # Hans' garland coil, carried in a tentacle until it is all laid on
        if self.pick[0] <= t < self.swag_t[-1][1]:
            hx, hy = hand("tentacles", -1, t)
            left = 1.0 - sum(smoothstep(_seg(t, a, b)) for a, b in self.swag_t) / 3
            if left > 0.02:
                for k in range(3):
                    r = (10 + 8 * k) * (0.4 + 0.6 * left)
                    pg.stroke(skia.Path().addOval(skia.Rect(hx - r - sh, hy + 8 - r * 0.5, hx + r - sh,
                                                            hy + 8 + r * 0.5)), (70, 116, 78), 6.0)

    # ------------------------------------------------------------------ storycheck
    IDS = {"star 1": "star 1", "star 2": "star 2", "gold star": "star 3", "acorn 1": "acorn 4", "acorn 2": "acorn 5",
           "bow 1": "bow 1", "bow 2": "bow 2", "bow 3": "bow 3", "cone 1": "cone 1", "cone 2": "cone 2",
           "cone 3": "cone 3"}

    def things(self, t, sh, hand, removed=None, step=1 / 30):
        """Every piece by the id it had on the bench (CB ids), in its hand or on the fir; the garland and the berry
        string as they are carried and laid on."""
        out = {}
        mid = self.pick[0] + 0.5 * (self.pick[1] - self.pick[0])
        if t < mid:
            return out
        removed = removed or (lambda n: False)
        for name in self.pieces:
            x, y, who = self.piece_at(name, t, hand)
            if name == "gold star" and t >= self.star_on:
                x, y = HANG["top star"]
            held = None
            if who is not None:
                kd, side = (("springs", -1) if name == "gold star" and t >= self.star_grab else
                            self.pieces[name][:2])
                if who.startswith("the basket"):
                    kd, side = "wheels", 1
                hx, hy = hand(kd, side, t)
                held = (who, (hx - sh, hy + (20 if who.startswith("the basket") else 0)))
            hang = "top star" if name == "gold star" else name
            if removed(hang):
                continue
            out[self.IDS[name]] = sc.Thing(x - sh, y, SIZES[self.IDS[name].split()[0]], held=held)
        from .christmas_home import item_xy
        for j, (a, b) in enumerate(self.swag_t):                  # each swag on the fir, once it is laid on
            if t >= b and not removed(f"swag {j + 1}"):
                x, y = item_xy(f"swag {j + 1}")
                out[f"garland swag {j + 1}"] = sc.Thing(x - sh, y, 60, born="laid on by Hans' tentacle")
        if True:                                                   # the garland: coiled on Hans' tentacle
            if t < self.swag_t[-1][1]:                            # coiled on his tentacle while he lays it on
                hx, hy = hand("tentacles", -1, t)
                gx, gy = hx, hy + 8
                if t < self.pick[1]:                               # off the snow into his tentacle
                    src = (self.bench_hans_x - 150, G - 60)
                    u = smoothstep(_seg(t, self.pick[0] + 0.5 * (self.pick[1] - self.pick[0]), self.pick[1]))
                    gx, gy = src[0] + (gx - src[0]) * u, src[1] + (gy - src[1]) * u
                gone = ("all laid on the fir", (hx - sh, hy)) if t + step >= self.swag_t[-1][1] else None
                out["garland"] = sc.Thing(gx - sh, gy, 60, held=("Hans' tentacle", (hx - sh, hy)), gone=gone,
                                          grows="laid on the fir a swag at a time")
        pts = self.string_pts(t, hand)
        if pts is not None and not removed("string") and not getattr(self, "string_gone", lambda tt: False)(t):
            q = pts[len(pts) // 2]
            out["berry string"] = sc.Thing(q[0] - sh, q[1], 120, born="the berries on their string", moves=
                                           "held between Springs' hands" if not all(t >= b for a, b in self.string_on)
                                           else None)
        return out
