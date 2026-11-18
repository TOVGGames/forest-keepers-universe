"""Forest Keepers ep 14, beat 6: the forever home (docs/engines/forest_keepers_christmas.md, build staging).
After the visit they all walk home to the treehouse for the night; the fir glows on alone in the snow while night turns
to a bright winter morning. An act break: they are all out again. Hans stands at the fir's right by the basket: his
left tentacle (a lifted leg) takes each piece off, hands it over his head to his right one, which lays it in the
basket (the ornaments go back in their basket for next year). Then he lifts the fir out of its pot the same way and
carries it in front of him; Wheels takes the basket in his left pincer and they all set off. Another act break: the
sunny clearing. Hans holds the fir up high, over Sprout; Digs digs the hole like a dog beside him (the earth piles up
behind it); Hans lowers the fir in; Digs pats the earth back round it and Sprout waters it. Evening comes. "Goodnight,
little fir. Goodnight, forest." Then the end sign.

FK0017 advisor r1 (the old staging): Hans undid the fir from the far side of a lamp post with a tentacle stretched to
three times its length, the fir warped into his tentacle, he carried it by a tentacle from his face, the walk to the
clearing was one 31 s shot through the workbench, the dig and the watering were tiny and hidden. Now every reach is
short, every hand-over is above his head in plain view, the long walks are act breaks, and the dig, the planting and
the watering are close.
"""
import math

from families.foundry.keepers.common import smoothstep

from . import christmas_flat_world as XW
from . import storycheck as sc
from .christmas_deco import BASKET_DOWN, HANG, STRING, SWAGS, swag   # noqa: F401  (swag: used by the flat plan)

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
K = 0.72
SPOT = XW.SPOT
HOLE = XW.CLEARING
OFF = SPOT + 1450.0                                       # the treehouse: home for the night
# the morning, after the act break: Hans by the basket at the fir's right, Wheels beyond it, the others at its left
M_AT = {"tentacles": SPOT + 200.0, "wheels": SPOT + 540.0, "sprout": SPOT - 250.0, "digger": SPOT - 520.0,
        "teeth": SPOT - 690.0, "springs": SPOT - 850.0, "lantern": SPOT - 1010.0}
MORNING_CAM = SPOT - 195.0
UNDO_SHOT = (SPOT + 165.0, 1.9)                           # close: the fir, Hans, the basket (Sprout, Wheels whole)
# the clearing, after the second act break: Hans holds the fir up over Sprout; Digs at the hole's right
C_AT = {"tentacles": HOLE - 325.0, "sprout": None, "digger": HOLE + 127.0, "teeth": HOLE + 560.0,
        "wheels": HOLE + 720.0, "springs": HOLE + 880.0, "lantern": HOLE + 1030.0}
CLEAR_CAM = HOLE + 180.0
PLANT_SHOT = (HOLE - 100.0, 1.75)                          # close: Hans, Sprout, the hole, Digs (Twigs whole)
REMOVE = ["top star", "acorn 2", "star 2", "swag 3", "swag 2", "acorn 1", "string", "swag 1", "cone 3", "cone 2",
          "cone 1", "bow 3", "bow 2", "bow 1", "star 1"]
PIECE_S = 1.9                                             # one piece every this many s (the two tentacles in turn)
# Hans' working legs (0: his leftmost, 5: his rightmost) and where their tips go, relative to him (x, G)
REST = {0: (-140.0, -205.0), 5: (140.0, -205.0)}
OVER = (0.0, -410.0)                                      # the hand-over, above his head (seen whole)
SIDE = {0: (-200.0, -300.0), 5: (200.0, -300.0)}          # up beside his head first (advisor FK0017 r3: the straight
                                                          # line from the fir to above him ran across his face)
FIR_OVER = (0.0, -380.0)
CARRY_FIR = (150.0, -338.0)                               # the fir held up in front of him: its ball clears Sprout
BALL_DY = -14.0                                           # the tentacle wraps its trunk this far above its base
DIG = 6                                                   # Digs' quick strokes (dog-style)
DIG_S = 0.6
HANDLE = 36.0                                             # the basket's handle top above its foot (as drawn)


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def _ease(p, q, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


def item_xy(name):
    if name.startswith("swag"):
        a, b, sag = SWAGS[int(name.split()[1]) - 1]
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag
    if name == "string":
        a, b, sag = STRING
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag
    return HANG[name]


def _pot_ball():
    from .christmas_flat import POT_Y, pot_soil_y
    return SPOT, pot_soil_y(POT_Y) + BALL_DY


class Home:
    def __init__(self, h0, start_x, sprout_water_dx):
        self.t0 = h0
        self.keys = {kd: [(h0, start_x[kd])] for kd in start_x}
        self.hans_xy = None                                         # set by the plan: Hans' (x, y) at t
        self.wheels_xy = None
        # home for the night: all walk off to the right past the fir (in front of it), the rightmost first
        order = sorted(start_x, key=lambda k: -start_x[k])
        t = h0 + 0.5
        for i, kd in enumerate(order):
            ta = t + 1.2 * i
            self.keys[kd] += [(ta, start_x[kd]), (ta + abs(OFF + 200 * i - start_x[kd]) / 110.0 + 1.0, OFF + 200 * i)]
        self.gone = max(k[-1][0] for k in self.keys.values())
        self.morning = (self.gone - 2.0, self.gone + 10.0)
        # act break: in the morning they are all out again, in their places
        mc = (self.morning[1] + 1.5, self.morning[1] + 5.5)
        self.cuts = [mc]
        for kd in self.keys:
            self.keys[kd] += [(mc[0] + 0.2, self.keys[kd][-1][1]), (mc[1] - 0.2, M_AT[kd])]
        self.back = mc[1]
        self.say_after = mc[1] + 0.6
        # each piece: off the fir in the left tentacle, over his head to the right one, into the basket
        self.removes, self.passes = {}, {}
        u0 = mc[1] + 1.6
        legs = {0: [(u0 - 0.8, ("r", REST[0]))], 5: [(u0 + 0.0, ("r", REST[5]))]}
        u = u0
        for name in REMOVE:
            it = ("w", item_xy(name))
            legs[0] += [(u, it), (u + 0.3, it), (u + 0.6, ("r", SIDE[0])), (u + 0.9, ("r", OVER)),
                        (u + 1.1, ("r", OVER))]
            legs[5] += [(u + 0.4, ("r", REST[5])), (u + 0.65, ("r", SIDE[5])), (u + 0.9, ("r", OVER)),
                        (u + 1.1, ("r", OVER)), (u + 1.4, ("r", SIDE[5])),
                        (u + 1.7, ("w", (BASKET_DOWN[0], BASKET_DOWN[1] - 24))),
                        (u + 1.9, ("w", (BASKET_DOWN[0], BASKET_DOWN[1] - 24)))]
            self.removes[name] = (u, u + 0.3, u + 1.7)                 # reached, lifted off, in the basket
            self.passes[name] = u + 1.0                                # from the left tentacle to the right
            u += PIECE_S
        self.undone = u
        # the fir: the left tentacle round its ball in the pot, up and over his head, to the right one; held in front
        ball = ("w", _pot_ball())
        fg = u - 0.1
        legs[0] += [(fg, ball), (fg + 0.4, ball)]
        self.fir_grip = (fg, fg + 0.4)
        self.fir_lift = (fg + 0.4, fg + 2.0)
        legs[0] += [(self.fir_lift[1], ("r", FIR_OVER)), (self.fir_lift[1] + 0.4, ("r", FIR_OVER)),
                    (self.fir_lift[1] + 1.0, ("r", REST[0]))]
        legs[5] += [(self.fir_lift[1] - 0.5, ("r", REST[5])), (self.fir_lift[1], ("r", FIR_OVER)),
                    (self.fir_lift[1] + 0.4, ("r", FIR_OVER)), (self.fir_lift[1] + 1.1, ("r", CARRY_FIR))]
        self.fir_pass = self.fir_lift[1] + 0.2
        self.grab_pot = (self.fir_grip[0], self.fir_lift[1])           # (kept for the sounds / voices)
        self.say_lift = self.fir_lift[0]
        # Wheels takes the full basket in his left pincer while Hans lifts the fir
        self.basket_take = (self.undone + 0.3, self.undone + 1.6)
        take_x = BASKET_DOWN[0] + 100.0                                # (he waits clear of it, so it shows)
        self.keys["wheels"] += [(self.undone - 1.8, M_AT["wheels"]), (self.undone - 0.2, take_x)]
        # they set off: Wheels first, then Hans with the fir, then the others; an act break, the clearing
        t = self.fir_lift[1] + 1.4
        self.walk = t
        go = ["wheels", "tentacles", "sprout", "digger", "teeth", "springs", "lantern"]
        cc = (t + 3.2, t + 7.2)
        self.cuts.append(cc)
        AT = dict(C_AT, sprout=HOLE - sprout_water_dx)
        for i, kd in enumerate(go):
            x0 = take_x if kd == "wheels" else M_AT[kd]
            ta = t + 0.9 * i
            self.keys[kd] += [(ta, x0), (cc[0], x0 + max(0.0, cc[0] - ta - 0.5) * 100.0), (cc[1] - 0.2, AT[kd])]
        self.at_hole = cc[1]
        self.sprout_x = AT["sprout"]
        a = cc[1] + 1.0
        self.strokes = [(a + DIG_S * i, a + DIG_S * (i + 1)) for i in range(DIG)]
        a = self.strokes[-1][1] + 0.5
        self.over = (a, a + 1.6)                                        # the fir over to above the hole
        self.lower = (self.over[1], self.over[1] + 1.6)                 # and down into it
        self.let_go = self.lower[1] + 0.3
        self.lift = self.over                                           # (kept for the voices)
        self.pot_down = self.over
        into = ("w", (HOLE, BACK + BALL_DY + 2.0))
        legs[5] += [(self.over[0], ("r", CARRY_FIR)), (self.over[1], ("w", (HOLE, G + CARRY_FIR[1]))),
                    (self.lower[1], into), (self.let_go, into), (self.let_go + 0.9, ("r", REST[5]))]
        self.legs = legs
        self.windows = {0: (legs[0][0][0], legs[0][-1][0]), 5: (legs[5][0][0], legs[5][-1][0])}
        self.pats = [(self.let_go + 0.4, self.let_go + 1.2), (self.let_go + 1.3, self.let_go + 2.1)]
        self.digs_back = (self.pats[1][1] + 0.1, self.pats[1][1] + 1.7)   # Digs steps clear, paws away, first
        self.keys["digger"] += [(self.digs_back[0], C_AT["digger"]), (self.digs_back[1], C_AT["digger"] + 100.0)]
        self.water = (self.digs_back[1] - 0.2, self.digs_back[1] + 3.2)
        self.evening = (self.water[1] + 0.5, self.water[1] + 9.0)
        self.step_back = (self.water[1] + 0.6, self.water[1] + 2.8)       # Sprout and Digs step back: the fir alone
        self.keys["sprout"] += [(self.step_back[0], self.sprout_x), (self.step_back[1], self.sprout_x - 22.0)]
        self.finale = self.water[1] + 2.0
        self.end = None                                            # set by the plan (after the goodnight + hold)
        for kd in self.keys:
            self.keys[kd] = sorted(set(self.keys[kd]))
        self.shots = [(self.removes[REMOVE[0]][0] - 1.0, self.removes[REMOVE[5]][2] + 0.1, UNDO_SHOT[0],
                       G + 70.0 - 540.0 / UNDO_SHOT[1], UNDO_SHOT[1]),
                      (self.removes[REMOVE[11]][0] - 0.5, self.fir_lift[0] + 0.4, UNDO_SHOT[0],
                       G + 70.0 - 540.0 / UNDO_SHOT[1], UNDO_SHOT[1]),
                      (self.at_hole + 0.4, self.water[1] + 0.8, PLANT_SHOT[0], G + 70.0 - 540.0 / PLANT_SHOT[1],
                       PLANT_SHOT[1])]

    # ------------------------------------------------------------------ Hans' working tentacles
    def _leg_at(self, leg, t, x, y):
        ks = self.legs[leg]
        a, b = self.windows[leg]
        if not (a <= t <= b):
            return None
        res = lambda s: (x + s[1][0], G + s[1][1]) if s[0] == "r" else s[1]   # noqa: E731
        for (t0, s0), (t1, s1) in zip(ks, ks[1:]):
            if t0 <= t <= t1:
                return _ease(res(s0), res(s1), _seg(t, t0, t1))
        return res(ks[-1][1])

    def hans_targets(self, t, x, y):
        """[(leg, (x, y))]: Hans' lifted legs working right now and where their tips are (world)."""
        out = []
        for leg in (0, 5):
            p = self._leg_at(leg, t, x, y)
            if p is not None:
                out.append((leg, p))
        return out

    def hans_target(self, t, x, y):
        tg = self.hans_targets(t, x, y)
        return tg[-1][1] if tg else None

    def _tip(self, leg, t):
        x, y = self.hans_xy(t)
        p = self._leg_at(leg, t, x, y)
        return p if p is not None else (x + REST[leg][0], G + REST[leg][1])

    # ------------------------------------------------------------------ the fir, the pot and the basket
    def pot_pos(self, t, hans_hand=None):
        from .christmas_flat import POT_Y
        return SPOT, POT_Y

    def fir_pos(self, t, hans_hand=None):
        """(x, base y, in_pot, planted) of the fir in this beat."""
        from .christmas_flat import POT_H, POT_Y, pot_soil_y
        if t < self.fir_grip[1]:
            return SPOT, pot_soil_y(POT_Y), True, False
        if t >= self.let_go:
            return HOLE, BACK + 2.0, False, True
        hx, hy = self._tip(0 if t < self.fir_pass else 5, t)
        inside = hy > POT_Y - POT_H - 41.0                          # its ball still down in the pot
        return hx, hy - BALL_DY, inside and t < self.fir_pass, False

    def basket_at(self, t):
        """(x, y of its foot, held) of the basket in this beat, or None before it (the deco has it)."""
        if t < self.basket_take[0] + 0.5:
            return None if t < self.t0 else (BASKET_DOWN[0], BASKET_DOWN[1], False)
        hx, hy = self.wheels_hand(t)
        return hx, hy + HANDLE, True

    def wheels_target(self, t, x, y):
        """Wheels' left pincer: down to the basket's handle, up, held at his side (world), or None."""
        a, b = self.basket_take
        if t < a - 0.6:
            return None
        handle = (BASKET_DOWN[0], BASKET_DOWN[1] - HANDLE)
        carry = (x - 96.0, y - 120.0)
        if t < a:
            return _ease((x - 92.0, y - 160.0), handle, _seg(t, a - 0.6, a))
        if t < a + 0.5:
            return handle
        return _ease(handle, carry, _seg(t, a + 0.5, b))

    def wheels_hand(self, t):
        x, y = self.wheels_xy(t)
        return self.wheels_target(t, x, y)

    def removed(self, name, t):
        return name in self.removes and t >= self.removes[name][1]

    def piece_at(self, name, t):
        """Where a piece Hans has taken off is (world), and who has it, or None (on the fir / in the basket)."""
        a, b, c = self.removes[name]
        if not (b <= t < c):
            return None
        leg = 0 if t < self.passes[name] else 5
        x, y = self._tip(leg, t)
        return x, y, "Hans' left tentacle" if leg == 0 else "Hans' right tentacle"

    def basket_full(self, t):
        return sum(1 for n, (a, b, c) in self.removes.items() if t >= c)

    # ------------------------------------------------------------------ Digs
    def digs_paw_angle(self, t, shoulder):
        """Digs' left paw: quick strokes digging the hole (like a dog), then two pats round the fir."""
        sx_, sy_ = shoulder
        down = math.atan2(BACK - 10 - sy_, HOLE - sx_)
        out = down + 0.6
        for a, b in self.strokes + self.pats:
            if a - 0.5 <= t < b:
                if t < a:
                    if (a, b) != self.strokes[0] and (a, b) != self.pats[0]:
                        return out                                  # (between strokes: straight on to the next)
                    return math.radians(108) + (out - math.radians(108)) * smoothstep(_seg(t, a - 0.5, a))
                u = _seg(t, a, b)
                if u < 0.35:
                    return out + (down - out) * smoothstep(u / 0.35)
                if u < 0.55:
                    return down
                return down + (out - down) * smoothstep((u - 0.55) / 0.45)
        if self.strokes[-1][1] <= t < self.pats[0][0] - 0.5:            # waits, paw ready, while the fir goes in
            return out + (math.radians(108) - out) * smoothstep(_seg(t, self.strokes[-1][1], self.strokes[-1][1] + 0.6)) \
                if t < self.strokes[-1][1] + 0.6 else (math.radians(108) + (out - math.radians(108)) *
                                                       smoothstep(_seg(t, self.pats[0][0] - 1.1, self.pats[0][0] - 0.5)))
        last = self.pats[-1][1]
        if last <= t < last + 0.6:
            return out + (math.radians(108) - out) * smoothstep(_seg(t, last, last + 0.6))
        return None

    def hole_depth(self, t):
        return smoothstep(_seg(t, self.strokes[0][0], self.strokes[-1][1]))

    def _flecks(self):
        if not hasattr(self, "_fl"):
            import numpy as np
            rs = np.random.default_rng(17)
            self._fl = []
            for k, (a, b) in enumerate(self.strokes):                  # flung up and back onto the pile behind it
                for j in range(4):
                    self._fl.append(dict(t=a + 0.6 * (b - a) + 0.03 * j, vx=rs.uniform(-70, 30),
                                         vy=rs.uniform(-330, -220), r=rs.uniform(3.5, 6.0), k=k))
        return self._fl

    def fleck_pos(self, f, t):
        u = t - f["t"]
        if u < 0:
            return None
        x0, y0 = HOLE + 6, BACK - 2
        land = BACK - 16 + 6 * ((f["k"] * 4) % 3) / 2
        tl = (-f["vy"] + math.sqrt(f["vy"] ** 2 + 2 * 1500 * (land - y0))) / 1500   # comes down onto the pile
        if u >= tl:
            return x0 + f["vx"] * tl, land
        return x0 + f["vx"] * u, y0 + f["vy"] * u + 0.5 * 1500 * u * u

    def filled(self, t):
        """0..1: how far the hole is filled back in (by the two pats, after he lets go of the fir)."""
        return smoothstep(_seg(t, self.pats[0][0], self.pats[1][1]))

    def fleck_back(self, f, t):
        """Is this fleck patted back in yet? Near ones go with the first pat, the far ones with the second."""
        q = self.fleck_pos(f, t)
        if q is None or abs(q[0] - HOLE) >= 110:
            return False
        i = self._flecks().index(f)
        a, b = self.pats[i % 2]
        return t > a + (b - a) * 0.6

    def mound(self, t):
        """The pile of earth behind the hole: it grows with each stroke, and goes back in with the pats."""
        d = self.hole_depth(t)
        back = smoothstep(_seg(t, self.pats[0][0], self.pats[1][1]))
        return d * (1 - 0.8 * back)

    # ------------------------------------------------------------------ drawing
    def draw_ground(self, pg, t, sh):
        from .christmas_flat import SOIL
        from .storybook import oval, tone
        if t < self.strokes[0][0]:
            return
        d = self.hole_depth(t)
        m = self.mound(t)
        if m > 0.01:                                            # the pile, behind the hole
            pg.shape(oval(HOLE - 14 - sh, BACK - 18, 42 * m + 4, 16 * m + 2), SOIL, 0.1)
            pg.flat(oval(HOLE - 22 - sh, BACK - 22 - 8 * m, 18 * m + 2, 5 * m + 1), tone(SOIL, 0.15), 0.8)
        fill = self.filled(t)
        if fill < 1.0:                                          # the hole (open until the pats fill it)
            e = d * (1 - fill)
            pg.flat(oval(HOLE - sh, BACK + 4, 34 + 16 * d, 9 + 5 * d), SOIL, (0.5 + 0.5 * d) * (1 - fill))
            pg.flat(oval(HOLE - sh, BACK + 3, 30 * e + 2, 8 * e + 1), (60, 46, 36), 1 - fill)
        if t >= self.let_go and fill > 0:                       # planted: a soft mound of earth at its foot
            pg.flat(oval(HOLE - sh, BACK + 4, 44, 10), SOIL, fill)
            wet = smoothstep(_seg(t, self.water[0] + 0.3, self.water[1]))
            if wet > 0:                                         # the water soaks in: the earth goes dark
                pg.flat(oval(HOLE - sh, BACK + 4, 40 * (0.5 + 0.5 * wet), 8), tone(SOIL, -0.45), 0.8 * wet)
            pg.flat(oval(HOLE - sh, BACK + 1, 26, 4), (124, 96, 74), 0.6 * fill)
        for f in self._flecks():
            p = self.fleck_pos(f, t)
            if p is None:
                continue
            if self.fleck_back(f, t):
                continue                                         # patted back in with the pile
            pg.flat(oval(p[0] - sh, p[1], f["r"], f["r"] * 0.8), SOIL)

    def draw_removed(self, pg, t, sh, deco, hans_hand=None):
        """The pieces in Hans' tentacles on their way to the basket."""
        import skia
        for name in self.removes:
            p = self.piece_at(name, t)
            if p is None:
                continue
            hx, hy, _ = p
            if name.startswith("swag") or name == "string":
                for k in range(3):
                    r = 8 + 6 * k
                    pg.stroke(skia.Path().addOval(skia.Rect(hx - r - sh, hy + 6 - r * 0.5, hx + r - sh,
                                                            hy + 6 + r * 0.5)),
                              (70, 116, 78) if name != "string" else (184, 52, 52), 5.0)
            else:
                deco.draw_piece(pg, "gold star" if name == "top star" else name, hx - sh, hy + 6)

    IDS = {"star 1": "star 1", "star 2": "star 2", "top star": "star 3", "acorn 1": "acorn 4", "acorn 2": "acorn 5",
           "bow 1": "bow 1", "bow 2": "bow 2", "bow 3": "bow 3", "cone 1": "cone 1", "cone 2": "cone 2",
           "cone 3": "cone 3", "swag 1": "garland swag 1", "swag 2": "garland swag 2", "swag 3": "garland swag 3",
           "string": "berry string"}

    def things(self, t, sh, hans_hand=None, step=1 / 30):
        """Each piece Hans takes off (by the id it had all along), into the basket; the fir; the earth."""
        from .christmas_deco import SIZES
        from .christmas_flat import FIR_H
        out = {}
        for name in self.removes:
            p = self.piece_at(name, t)
            if p is None or name not in self.IDS:
                continue
            hx, hy, who = p
            c = self.removes[name][2]
            gone = ("into the basket", (BASKET_DOWN[0] - sh, BASKET_DOWN[1] - 24)) if t + step >= c else None
            size = SIZES.get(self.IDS[name].split()[0], 60.0 if name.startswith("swag") else 120.0)
            out[self.IDS[name]] = sc.Thing(hx - sh, hy + 6, size, held=(who, (hx - sh, hy)), gone=gone)
        if t >= self.fir_grip[0]:
            x, base, in_pot, planted = self.fir_pos(t)
            held = None
            if not planted and t >= self.fir_grip[1]:
                held = ("Hans' left tentacle, round its trunk" if t < self.fir_pass else
                        "Hans' right tentacle, round its trunk", (x - sh, base + BALL_DY))
            out["the little fir"] = sc.Thing(x - sh, base - FIR_H / 2, FIR_H, held=held)
        for i, f in enumerate(self._flecks()):
            p = self.fleck_pos(f, t)
            if p is None:
                continue
            if self.fleck_back(f, t):
                continue
            out[f"earth fleck {i}"] = sc.Thing(p[0] - sh, p[1], f["r"], born="flung out by Digs' paw" if
                                               t - f["t"] < step * 1.5 else None, moves="falls",
                                               gone=("patted back in", (p[0] - sh, p[1]))
                                               if self.fleck_back(f, t + step) else None)
        return out
