"""Forest Keepers episode 5, act 2: the sled workshop at the foot of the hill (docs/engines/forest_keepers_first_snow.md).

CUT    Wheels pushes each plank up against the stop block, Twigs saws a slat off at the pencil line with his wrist
       saw (every slat the same length), Hans stacks it. Digs carries the next plank over from the pile.
BEND   Glo lights the fire under the steam box. Hans pulls two hot runner strips out onto the bending bed, curls
       their noses up with his tentacles, clamps them and puts the pair on the pile. Three pairs.
BUILD  Hans sets a pair of runners on the jig boards, fetches five slats at once (one per tentacle) and puts them
       on from the tail to the nose; Springs bounces each one down onto its pegs. Glo paints the sled in its riders'
       colour, Hans ties the pull rope, Twigs trims it, Wheels tows the sled to its place. Three sleds.
Sleds face right here (nose to the right, the way they will be pulled up the hill).
"""
import math

import numpy as np

from families.foundry.keepers.common import Jump, PLANK, ellipse, lerp, rect, seg, smoothstep, smootherstep, wood_sign
from families.foundry.keepers.halloween import path
from families.foundry.products.monster import reach_tentacle
from families.foundry.style import IRON, lighten
from families.foundry.tree_monsters import LAMP, TRUNK

from . import sled as SL
from . import snow as SN
from .animal_houses import _ease, bez, saw_to
from .first_snow import G, KEEPERS, SLEDS, SnowAct, cam

SIGN_X = 3880.0
WOOD_X = 4300.0                     # the plank pile
HORSES = (4720.0, 4990.0)           # sawhorses
PLANK_Y = (G - 150.0, G - 122.0)    # plank top / bottom on the horses
STOP_X = 5070.0                     # stop block: every slat the same length
SLAT_LEN = 120.0
CUT_X = STOP_X - SLAT_LEN
PLANK_LEN = 5 * SLAT_LEN + 30.0
PLANK_C = STOP_X - 150.0 - PLANK_LEN / 2     # where Digs sets each new plank down
HANS_CUT = 5140.0
STACK_X = 5300.0                    # the slat stack
SLAT_H = 14.0
JIG_X, JIG_Y = 5750.0, G - 8.0      # the sled is put together here, on two flat boards
PILE_X = 6350.0                     # bent runner pairs wait here, one on top of the other
FORM_X, FORM_Y = 6900.0, G - 110.0  # the bending bed (runner origin while it is bent)
BOX = (7250.0, 7900.0)              # steam box
BOX_C = (BOX[0] + BOX[1]) / 2
FIRE_X = 7700.0
PARK = [8150.0, 8700.0, 9250.0]     # the finished sleds, evenly spaced
SITE_LAMPS = [4480.0, 5520.0, 6620.0, 8420.0]
STRIP_EXTRA = math.pi * SL.CURL_R * 1.15
WAIT = {"teeth": 6420.0, "wheels": 6620.0, "springs": 5450.0}
GLO_WAIT = (6150.0, G - 200.0)
HANS_BEND = FORM_X - SL.L / 2 - STRIP_EXTRA - 90     # where Hans stands while he bends (left of the noses)


class SledsAct(SnowAct):
    """The sled workshop at the foot of the hill."""
    name = "sleds"
    names = (-2.0, -1.0)
    depth0, depth1 = 28.0, 31.0
    fall0, fall1 = 0.6, 0.5

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.P_ = [6.0 + 14.0 * k for k in range(3)]           # plank k goes on the horses
        self.cut_cyc = 2.2
        self.cut_end = self.cut_t(2, 4) + 1.4
        self.B0, self.bend_cyc = self.cut_end + 3.6, 8.8
        self.S0, self.build_cyc = self.bend_t(3) + 0.6, 21.0
        self.tow_d = [(PARK[k] - JIG_X) / 440.0 for k in range(3)]
        self.parked_t = [self.build_t(k) + 18.6 + self.tow_d[k] for k in range(3)]
        self.gather_t = self.build_t(2) + 19.0
        self.dur = self.parked_t[2] + 7.5
        gaps = [PARK[k + 1] - PARK[k] for k in range(2)]
        self.stats = {"sleds_even": bool(max(gaps) - min(gaps) < 0.5), "slats_per_sled": SL.N_SLATS}
        self.fire_t = 10.0
        self.gx = {"lantern": 8040.0, "tentacles": 8420.0, "teeth": 8980.0, "springs": 8560.0, "wheels": 9500.0,
                   "digger": 9700.0}

    # ----- schedule -----

    def cut_t(self, k, i):
        return self.P_[k] + 1.4 + i * self.cut_cyc

    def bend_t(self, j):
        return self.B0 + j * self.bend_cyc

    def build_t(self, k):
        return self.S0 + k * self.build_cyc

    def place_t(self, k, j):
        """Sled k, j-th slat (j = 0 is the tail slat, slat index 4): Hans starts lowering it."""
        return self.build_t(k) + 6.0 + j * 1.2

    def aside_moods(self, t):
        return ["hehe", "mm", "ooh", "hm", "aww"]

    # ----- the planks and slats -----

    def pieces_off(self, k, t):
        return sum(1 for i in range(5) if t >= self.cut_t(k, i) + 0.9)

    def plank(self, k, t):
        """('pile'|'carry'|'horses'|'gone', left, right, top y)."""
        P = self.P_[k]
        if k > 0 and t < P - 3.0:
            return "pile", None, None, None
        if k > 0 and t < P - 0.3:
            u = seg(t, P - 3.0, P - 0.3)
            m = self.m("digger")
            cx = m.x if m is not None else PLANK_C
            lift = smoothstep(seg(u, 0.0, 0.2)) * (1 - smoothstep(seg(u, 0.82, 1.0)))
            top = lerp(G - 34 - 14 * (2 - k), PLANK_Y[0], smoothstep(seg(u, 0.8, 1.0))) - 70 * lift
            return "carry", cx - PLANK_LEN / 2, cx + PLANK_LEN / 2, top
        n = self.pieces_off(k, t)
        if n == 5 and t >= self.cut_t(k, 4) + 1.2:
            return "gone", None, None, None
        if n == 0:
            R = STOP_X - 150 + 150 * smootherstep(seg(t, P + 0.1, P + 1.2))
        else:
            i = n - 1
            ci = self.cut_t(k, i)
            R = CUT_X + (SLAT_LEN * smootherstep(seg(t, ci + 1.6, ci + 2.1)) if i < 4 else 0.0)
        length = PLANK_LEN - SLAT_LEN * n
        return "horses", R - length, R, PLANK_Y[0]

    def offcut(self, k, t):
        """The last 30 left of plank k drops under the horses."""
        t0 = self.cut_t(k, 4) + 1.2
        if t < t0:
            return None
        u = min(1.0, (t - t0) / 0.32)
        return CUT_X - 15 - 30 * u, lerp(PLANK_Y[0] + 14, G - 8 - 2 * k, u * u)

    def piece(self, n, t):
        """Slat n (n = 5k + i: plank k, cut i): ('plank'|'carry'|'stack'|'hans'|'down'|'on', x, y)."""
        k, i = divmod(n, 5)
        ci = self.cut_t(k, i)
        if t < ci + 0.9:
            return "plank", None, None
        top = (STACK_X, G - SLAT_H * n - SLAT_H / 2)
        if t < ci + 1.6:
            u = smootherstep(seg(t, ci + 0.9, ci + 1.6))
            x, y = bez((CUT_X + SLAT_LEN / 2, (PLANK_Y[0] + PLANK_Y[1]) / 2), (5200.0, PLANK_Y[0] - 120), top, u)
            return "carry", x, y
        sled = 2 - n // 5                       # sled 0 takes the top five
        j = 4 - n % 5                           # the top slat of the five is put on first
        grab = self.build_t(sled) + 4.0
        if t < grab:
            return "stack", top[0], top[1]
        m = self.m("tentacles")
        hx = m.x if m is not None else JIG_X
        held = self.held_spot(j)
        if t < grab + 0.6:
            u = smootherstep(seg(t, grab, grab + 0.6))
            return "hans", lerp(top[0], hx + held[0], u), lerp(top[1], G + held[1], u)
        tp = self.place_t(sled, j)
        if t < tp:
            return "hans", hx + held[0], G + held[1]
        spot = (JIG_X - SL.slat_x(4 - j), JIG_Y - SL.DECK_Y + SL.SLAT_T / 2)
        if t < tp + 0.5:
            u = smootherstep(seg(t, tp, tp + 0.5))
            return "down", lerp(hx + held[0], spot[0], u), lerp(G + held[1], spot[1], u)
        return "on", spot[0], spot[1]

    @staticmethod
    def held_spot(j):
        """Where Hans holds the j-th of five slats while he puts them on, relative to (his x, G)."""
        return (-150 + 75 * j, -330 - 26 * math.sin(math.pi * j / 4))

    def slats_on(self, k, t):
        return {4 - j for j in range(5) if t >= self.place_t(k, j) + 0.5}

    # ----- runner pairs -----

    def pair(self, j, t):
        """Runner pair j (bent in bend cycle j): (state, x, y, bend, clamp), x/y = the runners' origin."""
        b = self.bend_t(j)
        if t < b:
            return "box", BOX_C, FORM_Y, 0.0, 0.0
        if t < b + 1.4:
            u = smootherstep(seg(t, b, b + 1.4))
            return "pull", lerp(BOX_C, FORM_X, u), FORM_Y, 0.0, 0.0
        if t < b + 4.4:
            return "bend", FORM_X, FORM_Y, smootherstep(seg(t, b + 1.4, b + 4.0)), smoothstep(seg(t, b + 4.0, b + 4.4))
        pile = (PILE_X, G - 40 - 30 * j)
        if t < b + 6.2:
            u = smootherstep(seg(t, b + 4.4, b + 6.2))
            x, y = bez((FORM_X, FORM_Y), ((FORM_X + PILE_X) / 2, FORM_Y - 150), pile, u)
            return "carry", x, y, 1.0, 1.0
        k = 2 - j                                   # the top of the pile goes first
        s0 = self.build_t(k)
        if t < s0 + 0.6:
            return "pile", pile[0], pile[1], 1.0, 1.0
        if t < s0 + 2.4:
            u = smootherstep(seg(t, s0 + 0.6, s0 + 2.4))
            x, y = bez(pile, ((PILE_X + JIG_X) / 2, pile[1] - 170), (JIG_X, JIG_Y), u)
            return "carry", x, y, 1.0, 1.0
        return "jig", JIG_X, JIG_Y, 1.0, 1.0 - smoothstep(seg(t, s0 + 2.8, s0 + 3.2))

    def sled_pos(self, k, t):
        """Sled k once its runners are on the jig: (x, y), or None before."""
        s0 = self.build_t(k)
        if t < s0 + 2.4:
            return None
        t0 = s0 + 18.6
        if t < t0:
            return JIG_X, JIG_Y
        u = seg(t, t0, t0 + self.tow_d[k])
        return lerp(JIG_X, PARK[k], smootherstep(u)), lerp(JIG_Y, G, smoothstep(seg(t, t0, t0 + 0.5)))

    def paint(self, k, t):
        return smoothstep(seg(t, self.build_t(k) + 12.6, self.build_t(k) + 15.6))

    def rope(self, k, t):
        return smoothstep(seg(t, self.build_t(k) + 15.4, self.build_t(k) + 16.6))

    def fire(self, t):
        return smoothstep(seg(t, self.fire_t, self.fire_t + 2.0))

    # ----- camera -----

    def target(self, t):
        h = self.s.h
        keys = [(0.0, *cam(h, 4700, 0.62)), (4.0, *cam(h, 4780, 0.62)), (7.0, *cam(h, 4900, 0.95, 0.86)),
                (self.P_[1] - 4.0, *cam(h, 4900, 0.95, 0.86)), (self.P_[1] - 2.0, *cam(h, 4750, 0.82)),
                (self.P_[1] + 1.5, *cam(h, 4900, 0.95, 0.86)), (self.P_[2] - 4.0, *cam(h, 4950, 0.95, 0.86)),
                (self.cut_end, *cam(h, 5050, 0.9)), (self.B0 + 0.5, *cam(h, 6950, 0.82)),
                (self.bend_t(1) + 6.0, *cam(h, 6750, 0.86, 0.86)), (self.S0 - 1.0, *cam(h, 6600, 0.8))]
        for k in range(3):
            s0 = self.build_t(k)
            keys += [(s0 + 1.0, *cam(h, 5850, 0.9, 0.86)), (s0 + 17.0, *cam(h, 5800, 0.95, 0.86)),
                     (s0 + 19.0, *cam(h, 6800 + 400 * k, 0.6))]
            if k < 2:
                keys += [(s0 + 20.0, *cam(h, 6800 + 400 * k, 0.6))]
        keys += [(self.parked_t[2] - 1.0, *cam(h, 8500, 0.62)), (self.dur, *cam(h, 8650, 0.6))]
        keys.sort(key=lambda q: q[0])
        return _ease(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._twigs(t, dt)
        self._wheels(t, dt)
        self._digs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._fx(t)
        self._sounds(t)

    def _gather(self, kind, x, t, y=None):
        """At the end everyone goes over to the three parked sleds."""
        t0 = self.gather_t + 0.4 * KEEPERS.index(kind)
        if t < t0:
            return x, y
        yy = G - 60 if kind == "lantern" else G
        xx, y2, _ = path([(t0, x, y if y is not None else yy), (t0 + 6.5, self.gx[kind], yy)], t)
        return xx, y2

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        rest = PLANK_Y[0] - 70
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        if not m.x:
            m.x = CUT_X + 80
        if t < self.cut_end:
            ty = rest
            for k in range(3):
                for i in range(5):
                    ph = t - self.cut_t(k, i)
                    if 0 <= ph < 1.2:
                        if ph < 0.1:
                            ty = lerp(rest, PLANK_Y[0] - 22, ph / 0.1)
                        elif ph < 0.8:
                            ty = lerp(PLANK_Y[0] - 22, PLANK_Y[1] + 24, smoothstep((ph - 0.1) / 0.7))
                        else:
                            ty = lerp(PLANK_Y[1] + 24, rest, smoothstep((ph - 0.8) / 0.4))
                        m.saw_run = smoothstep(seg(ph, 0.0, 0.08)) * (1 - smoothstep(seg(ph, 0.8, 1.0)))
            sx = saw_to(m, t, CUT_X, ty, sx=-1)
            ax = path([(0.0, 3500.0, G), (5.0, CUT_X + 80, G)], t)[0]
            w = smoothstep(seg(t, 4.6, 5.6))
            x = lerp(ax, sx, w)
            m.punch_l *= w
        else:
            x0 = saw_to(m, self.cut_end, CUT_X, rest, sx=-1)
            m.punch_l *= 1 - smoothstep(seg(t, self.cut_end, self.cut_end + 0.8))
            x = path([(self.cut_end, x0, G), (self.cut_end + 5.0, WAIT["teeth"], G)], t)[0]
            for k in range(3):                   # trims the end of each new pull rope with his saw
                s0 = self.build_t(k)
                if s0 + 15.8 <= t < s0 + 18.0:
                    w = smoothstep(seg(t, s0 + 15.8, s0 + 16.6)) * (1 - smoothstep(seg(t, s0 + 17.3, s0 + 18.0)))
                    ry = JIG_Y - SL.RUN_H - 40
                    lift = smoothstep(seg(t, s0 + 16.6, s0 + 16.9)) * (1 - smoothstep(seg(t, s0 + 16.9, s0 + 17.2)))
                    sx_ = saw_to(m, t, JIG_X + SL.L / 2 + 150, ry - 40 + 70 * lift, sx=-1)
                    x = lerp(WAIT["teeth"], sx_, w)
                    m.punch_l *= w
                    m.saw_run = w * 0.9
            x, _ = self._gather("teeth", x, t)
        m.saw_spin += dt * 38 * m.saw_run
        self.place(m, x, t, dt)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        m.punch = 0.0
        x = None
        feed = PLANK_C - PLANK_LEN / 2 - 75         # behind the left end of a new plank
        end_x = CUT_X - 30 - 75                     # behind what's left after the fifth cut
        if t < self.P_[0]:
            x = path([(0.0, 3300.0, G), (5.4, feed, G)], t)[0]
        elif t < self.cut_end + 1.0:
            for k in range(3):
                P = self.P_[k]
                nxt = self.P_[k + 1] if k < 2 else None
                last = self.cut_t(k, 4) + 0.9
                if P <= t < last + 0.6:
                    st, left, right, _ = self.plank(k, t)
                    x = left - 75 if st == "horses" else end_x
                    pushing = any(self.cut_t(k, i) + 1.5 <= t < self.cut_t(k, i) + 2.1 for i in range(4)) or \
                        P + 0.1 <= t < P + 1.2
                    m.punch = 0.6 if pushing else 0.0
                elif t >= last + 0.6 and (nxt is None or t < nxt):
                    t1 = nxt - 0.5 if nxt is not None else self.cut_end + 7.0
                    x = path([(last + 0.6, end_x, G), (t1, feed if nxt is not None else WAIT["wheels"], G)], t)[0]
            if x is None:
                x = feed
        else:
            x = path([(self.cut_t(2, 4) + 1.5, end_x, G), (self.cut_end + 7.0, WAIT["wheels"], G)], t)[0]
            for k in range(3):                       # tows each finished sled to its place
                s0 = self.build_t(k)
                hook = JIG_X + SL.L / 2 + 225
                t0 = s0 + 18.6
                arrive = t0 + self.tow_d[k]
                back = arrive + 0.8 + (PARK[k] + 225 - WAIT["wheels"]) / 420.0
                if s0 + 17.4 <= t < t0:
                    x = path([(s0 + 17.4, WAIT["wheels"], G), (t0, hook, G)], t)[0]
                elif t0 <= t < arrive:
                    x = self.sled_pos(k, t)[0] + SL.L / 2 + 225
                    m.punch = 0.4
                elif k < 2 and arrive <= t < back:
                    x = path([(arrive + 0.8, PARK[k] + 225, G), (back, WAIT["wheels"], G)], t)[0]
                elif k == 2 and t >= arrive:
                    x = PARK[k] + 225
            x, _ = self._gather("wheels", x, t)
        self.place(m, x, t, dt)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        m.dig = 0.0
        home = 3900.0
        keys = [(0.0, 3200.0, G), (5.0, home, G)]
        for k in (1, 2):
            P = self.P_[k]
            keys += [(P - 4.2, home, G), (P - 3.0, WOOD_X, G), (P - 2.4, WOOD_X, G), (P - 0.8, PLANK_C, G),
                     (P + 0.2, PLANK_C, G), (P + 1.6, home, G)]
        pack0 = self.cut_end + 9.5
        keys += [(self.cut_end + 0.5, home, G), (pack0, 8000.0, G)]
        x = path(keys, t)[0]
        if t >= pack0:                               # packs the snow at the foot of the hill
            x = 8000.0 + 1700.0 * seg(t, pack0, self.dur - 6.0)
            if t < self.dur - 6.0:
                m.dig = 0.5 + 0.5 * math.sin(t * 7)
                if self.s.particles.rng.uniform() < 0.3:
                    self.s.particles.burst(x + 90, G - 20, 2, SN.SNOW, 380, 0.8, 7, kind="snow", g=1400, spread=0.5,
                                           direction=-math.pi * 0.35)
        for k in (1, 2):
            if self.P_[k] - 3.0 <= t < self.P_[k] - 0.3:
                m.dig = -0.2                         # shovels up under the plank
        x, _ = self._gather("digger", x, t)
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        keys = [(0.0, 3100.0, G), (5.5, HANS_CUT, G), (self.cut_end, HANS_CUT, G)]
        for j in range(3):
            b = self.bend_t(j)
            grab = BOX_C - SL.L / 2 - STRIP_EXTRA - 90
            keys += [(b - 0.4, grab, G), (b + 1.4, HANS_BEND, G), (b + 4.4, HANS_BEND, G), (b + 6.2, PILE_X - 450, G)]
        for k in range(3):
            s0 = self.build_t(k)
            keys += [(s0, PILE_X - 450, G), (s0 + 2.0, JIG_X, G), (s0 + 2.8, JIG_X, G), (s0 + 4.0, STACK_X + 140, G),
                     (s0 + 4.6, STACK_X + 140, G), (s0 + 5.8, JIG_X, G), (s0 + 15.2, JIG_X, G),
                     (s0 + 15.6, JIG_X + 60, G), (s0 + 16.8, JIG_X + 60, G), (s0 + 17.6, JIG_X, G)]
            keys.append((s0 + 20.4, PILE_X - 450 if k < 2 else JIG_X, G))
        keys.sort(key=lambda q: q[0])
        x = path(keys, t)[0]
        reach = []
        for n in range(15):                          # carries each new slat from the cut to the stack
            st, px, py = self.piece(n, t)
            if st == "carry":
                reach.append((px, py))
        for j in range(3):                           # pulls the strips out, bends the noses up, carries the pair
            st, px, py, b, cl = self.pair(j, t)
            if st in ("pull", "bend") or (st == "carry" and t < self.bend_t(j) + 6.4):
                nx, ny = SL.runner_pts(b)[-1]
                for far in (0, 1):
                    reach.append((px + nx - 10 * far, py + ny - 8 * far))
            elif st == "carry":
                reach += [(px - 150, py - 30), (px + 120, py - 30)]
        for n in range(15):                          # five slats, one in each tentacle
            st, px, py = self.piece(n, t)
            if st in ("hans", "down"):
                reach.append((px, py))
        for k in range(3):                           # ties the pull rope onto the nose
            if 0 < self.rope(k, t) < 1:
                pos = self.sled_pos(k, t)
                reach.append((pos[0] + SL.L / 2 + 30, pos[1] - SL.RUN_H - 40))
        self.reach["tentacles"] = reach[:6]
        x, _ = self._gather("tentacles", x, t)
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y = path([(0.0, 3600.0, G), (5.6, WAIT["springs"], G)], t)[:2]
        m.spring = 0.0
        deck = JIG_Y - SL.DECK_Y
        for k in range(3):
            segs = []
            prev = (WAIT["springs"], G)
            for j in range(5):                       # hops onto each new slat and bounces it down
                tgt = (JIG_X - SL.slat_x(4 - j), deck)
                jp = Jump(prev[0], prev[1], tgt[0], tgt[1], apex=60 if j else 90)
                segs.append((self.place_t(k, j) + 0.42, jp))
                prev = tgt
            segs.append((self.place_t(k, 4) + 1.5, Jump(prev[0], prev[1], WAIT["springs"], G, apex=80)))
            for i, (t0, jp) in enumerate(segs):
                if t0 <= t < t0 + jp.dur:
                    x, y = jp.at(t - t0)
                elif i + 1 < len(segs) and t0 + jp.dur <= t < segs[i + 1][0]:
                    x, y = jp.x1, jp.y1
                    m.spring = 0.8 * max(0.0, 1 - (t - t0 - jp.dur) / 0.15)
        x, y = self._gather("springs", x, t, y)
        self.place(m, x, t, dt, y=y)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        keys = [(0.0, 3700.0, G - 60), (9.4, FIRE_X - 90, G - 60), (self.S0 - 3.5, FIRE_X - 90, G - 60),
                (self.S0 - 0.2, *GLO_WAIT)]
        for k in range(3):
            s0 = self.build_t(k)
            keys += [(s0 + 11.8, *GLO_WAIT), (s0 + 12.6, JIG_X + SL.L / 2 - 20, G - 270),
                     (s0 + 15.6, JIG_X - SL.L / 2 + 40, G - 270), (s0 + 17.2, *GLO_WAIT)]
        x, y, _ = path(keys, t)
        m.lamp = 1.0 + 0.8 * math.exp(-((t - self.fire_t - 0.3) / 0.5) ** 2)
        x, y = self._gather("lantern", x, t, y)
        self.place(m, x, t, dt, y=y)

    # ----- effects and sounds -----

    def _fx(self, t):
        p = self.s.particles
        f = self.fire(t)
        if f > 0 and p.rng.uniform() < 0.5 * f:
            p.burst(FIRE_X + p.rng.uniform(-30, 30), G - 30, 1, LAMP, 60, 0.6, 5, g=-260, glow=True, spread=0.4)
        if t > self.fire_t + 3.0:                   # steam out of both ends of the box
            for ex in (BOX[0] - 6, BOX[1] + 6):
                if p.rng.uniform() < 0.18:
                    p.burst(ex, FORM_Y - 15, 1, SN.SNOW * 0.62, 40, 2.2, 16, g=-70, spread=0.6)

    def _sounds(self, t):
        if self.crossed(2.0):
            self.chat(t, "teeth", "hey", icon="sled")
        if self.crossed(3.0):
            self.chorus(t, ["springs", "wheels"], "yay", gap=0.3)
        for k in range(3):
            P = self.P_[k]
            if self.crossed(P + 0.2):
                self.fx(t, "slide", 1.0, 0.16, STOP_X - 300, PLANK_Y[0])
            if self.crossed(P + 1.15):
                self.hit(t, "clack", 55, 0.22, STOP_X, PLANK_Y[0])
            for i in range(5):
                ci = self.cut_t(k, i)
                if self.crossed(ci + 0.05):
                    self.fx(t, "saw", 0.75, 0.18, CUT_X, PLANK_Y[0])
                if self.crossed(ci + 1.55):
                    self.hit(t, "clack", self.s.note(5 * k + i, -1), 0.18, STACK_X, G - SLAT_H * (5 * k + i))
                if i < 4 and self.crossed(ci + 2.05):
                    self.hit(t, "clack", 55, 0.18, STOP_X, PLANK_Y[0])
            if self.crossed(self.cut_t(k, 4) + 1.5):
                self.hit(t, "thud", 50, 0.14, CUT_X, G)
            if k > 0 and self.crossed(P - 2.6):
                self.chat(t, "digger", "huff")
            if k > 0 and self.crossed(P - 0.4):
                self.hit(t, "thud", 46, 0.22, PLANK_C, PLANK_Y[0])
        if self.crossed(self.cut_t(0, 0) + 1.2):
            self.chat(t, "teeth", "hehe")
        if self.crossed(self.cut_t(2, 4) + 1.8):
            self.chat(t, "tentacles", "yay")
        if self.crossed(self.fire_t):
            self.hit(t, "bloop", 67, 0.3, FIRE_X, G - 60)
            self.fx(t + 0.2, "crackle", 6.0, 0.12, FIRE_X, G - 40)
            self.chat(t + 0.4, "lantern", "ooh")
        for j in range(3):
            b = self.bend_t(j)
            if self.crossed(b + 0.1):
                self.fx(t, "slide", 1.3, 0.14, BOX_C, FORM_Y)
                self.fx(t, "hiss", 1.4, 0.1, BOX[0], FORM_Y)
            if self.crossed(b + 1.5):
                self.fx(t, "creak", 2.4, 0.16, FORM_X - SL.L / 2, FORM_Y)
                if j == 0:
                    self.chat(t + 0.3, "tentacles", "huff")
            if self.crossed(b + 4.1):
                self.hit(t, "clunk", 50, 0.22, FORM_X - SL.L / 2, FORM_Y)
                if j == 0:
                    self.chat(t + 0.4, "tentacles", "mm")
        for k in range(3):
            s0 = self.build_t(k)
            if self.crossed(s0 + 2.5):
                self.hit(t, "clunk", 48, 0.22, JIG_X, JIG_Y)
            if self.crossed(s0 + 4.2):
                for q in range(5):
                    self.hit(t + q * 0.06, "clack", self.s.note(q, 0), 0.12, STACK_X, G - 200)
            for j in range(5):
                tp = self.place_t(k, j)
                if self.crossed(tp + 0.48):
                    self.hit(t, "clack", self.s.note(j, 0), 0.2, JIG_X - SL.slat_x(4 - j), JIG_Y - SL.DECK_Y)
                if self.crossed(tp + 0.42):
                    self.hit(t, "boing", 60 + 2 * j, 0.2, JIG_X - SL.slat_x(4 - j), JIG_Y - 80)
            if self.crossed(self.place_t(k, 4) + 0.9):
                self.chat(t, "springs", "yay" if k != 1 else "hehe")
            if self.crossed(s0 + 12.6):
                self.fx(t, "spray", 3.0, 0.08, JIG_X, JIG_Y - 60)
            if self.crossed(s0 + 15.8):
                self.chat(t, "lantern", "aww")
            if self.crossed(s0 + 16.9):
                self.fx(t, "saw", 0.3, 0.12, JIG_X + SL.L / 2 + 150, JIG_Y - 80)
            if self.crossed(s0 + 18.7):
                self.fx(t, "slide", self.tow_d[k], 0.12, JIG_X + 300, G)
                self.chat(t + 0.3, "wheels", "hey" if k == 0 else "wee")
            if self.crossed(self.parked_t[k]):
                self.hit(t, "soft_bell", self.s.note(2 + 2 * k, 0), 0.22, PARK[k], G - 100)
        if self.crossed(self.parked_t[2] + 1.0):
            self.chorus(t, ["springs", "lantern", "digger", "wheels", "tentacles", "teeth"], "yay", gap=0.2,
                        icon="star")
            for q, n in enumerate((60, 64, 67, 72, 76)):
                self.hit(t + 1.3 + q * 0.12, "soft_bell", n, 0.24, 8700, G - 300)

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        d = self.depth(t)
        self.backdrop(c, t)
        self.trees(c, t, [(3500, 700), (6100, 760), (7050, 680), (10200, 720), (11000, 650)])
        SL.draw_hill(c, s, t, lit=lambda x: 0.0, groove=0.0)
        self.snow_ground(c, t, x1=SL.HILL_X0 + 400)
        for lx in SITE_LAMPS:
            SL.lantern_post(c, s, lx, G - d * 0.3, 1.0, t, h=260)
        if t > self.cut_end + 9.5:                  # the packed path Digs is making towards the hill
            dm = self.m("digger")
            c.line(8000.0, G - d * 0.4, dm.x if dm is not None else 8000.0, G - d * 0.4, SN.SNOW_DEEP, 12)
        self._woodpile(c, t)
        self._saw_bench(c, t)
        self._box(c, t)
        self._stack(c, t)
        self._bench_and_pile(c, t)
        self._sleds(c, t)
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self._fire(c, t)
        self.draw_monsters(c, t)
        for n in range(15):                          # the slats Hans is carrying
            st, px, py = self.piece(n, t)
            if st == "carry":
                _slat_flat(c, px, py)
            elif st in ("hans", "down"):
                _slat_end(c, px, py, PLANK * 1.05)
        for k in range(3):                           # Glo paints with one tendril
            p = self.paint(k, t)
            if 0 < p < 1 and gl is not None:
                bx, by = gl.x - 6, JIG_Y - SL.DECK_Y - 8
                reach_tentacle(c, gl.x + 20, gl.y - 200, bx, by, 12, np.asarray(gl.color) * 0.8, t, 0.4, -1, 1.0)
                c.circle(bx, by, 7, np.asarray(SLEDS[k][1], np.float64))
        self.snow_front(c, t, x1=SL.HILL_X0 + 400)

    def _woodpile(self, c, t):
        n = 2 - sum(1 for k in (1, 2) if t >= self.P_[k] - 3.0)
        for lx in (WOOD_X - 230, WOOD_X + 230):
            c.circle(lx, G - 16, 18, TRUNK * 0.8)
        for q in range(n):
            y0 = G - 34 - 14 * q
            rect(c, WOOD_X - PLANK_LEN / 2, y0, WOOD_X + PLANK_LEN / 2, y0 + 14, PLANK * (0.85 + 0.06 * q))
            c.line(WOOD_X - PLANK_LEN / 2, y0, WOOD_X + PLANK_LEN / 2, y0, PLANK * 1.15, 2)
        if n:
            SN.cap_flat(c, WOOD_X - PLANK_LEN / 2, WOOD_X + PLANK_LEN / 2, G - 34 - 14 * (n - 1), self.depth(t) * 0.5)
        wood_sign(c, SIGN_X, G, "SLEDS", 44, 1.0, self.s.glow_draw)

    def _saw_bench(self, c, t):
        for hx in HORSES:
            c.line(hx - 34, G, hx - 8, PLANK_Y[1], TRUNK * 0.9, 9)
            c.line(hx + 34, G, hx + 8, PLANK_Y[1], TRUNK * 0.9, 9)
            rect(c, hx - 40, PLANK_Y[1], hx + 40, PLANK_Y[1] + 10, TRUNK)
        rect(c, STOP_X, PLANK_Y[0] - 18, STOP_X + 12, PLANK_Y[1] + 4, IRON * 1.3)        # stop block
        for k in range(3):
            st, left, right, top = self.plank(k, t)
            if st == "carry":
                rect(c, left, top, right, top + 28, PLANK * 0.95)
            elif st == "horses":
                rect(c, left, PLANK_Y[0], right, PLANK_Y[1], PLANK * 0.95)
                c.line(left, PLANK_Y[0], right, PLANK_Y[0], PLANK * 1.2, 2)
                for q in range(1, 6):                                 # pencil marks every slat length
                    mx = right - q * SLAT_LEN
                    if mx > left + 4:
                        c.line(mx, PLANK_Y[0] - 4, mx, PLANK_Y[0] + 8, np.array([40, 34, 30]), 2)
            oc = self.offcut(k, t)
            if oc is not None:
                rect(c, oc[0] - 15, oc[1] - 14, oc[0] + 15, oc[1], PLANK * 0.85)
        n = sum(self.pieces_off(k, t) for k in range(3))
        if n:                                                         # sawdust under the cut
            c.polygon(ellipse(CUT_X + 10, G - self.depth(t) * 0.5, 30 + 4 * n, 6 + 1.2 * n, 20, math.pi, 2 * math.pi),
                      np.array([196, 160, 112]))

    def _stack(self, c, t):
        for n in range(15):
            st, px, py = self.piece(n, t)
            if st == "stack":
                _slat_flat(c, px, py)

    def _bench_and_pile(self, c, t):
        """The bending bed with its round nose block, the pile of bent pairs, the jig boards, the pairs."""
        rect(c, FORM_X - SL.L / 2 - 20, FORM_Y + 14, FORM_X + SL.L / 2 + 20, FORM_Y + 30, TRUNK)
        for lx in (FORM_X - 200, FORM_X + 200):
            c.line(lx, FORM_Y + 30, lx - 20, G, TRUNK * 0.9, 9)
        c.circle(FORM_X - SL.L / 2 + 2, FORM_Y - SL.RUN_H - SL.CURL_R + 6, SL.CURL_R - 12, TRUNK * 1.1)
        rect(c, PILE_X - 260, G - 22, PILE_X + 260, G, TRUNK * 0.85)
        for bx in (JIG_X - 170, JIG_X + 170):
            rect(c, bx - 40, G - 8, bx + 40, G + 2, TRUNK)
        for j in range(3):
            st, px, py, b, cl = self.pair(j, t)
            if st in ("pull", "bend", "carry", "pile"):
                for far in (1, 0):
                    SL.draw_runner(c, px - 10 * far, py - 8 * far, 0.0, b, PLANK * (0.9 if far else 1.0),
                                   far=bool(far), nose=-1)
                if cl > 0:
                    SL.draw_sled(c, px, py, 0.0, PLANK, runners=(None, None), slats=set(), paint=0.0, rope=0.0,
                                 clamp=cl, nose=-1)

    def _box(self, c, t):
        y0, y1 = FORM_Y - 50, FORM_Y + 40
        for lx in (BOX[0] + 60, BOX[1] - 60):
            c.line(lx, y1, lx, G, TRUNK * 0.9, 10)
        rect(c, BOX[0], y0, BOX[1], y1, PLANK * 0.7)
        for q in range(1, 6):
            xx = lerp(BOX[0], BOX[1], q / 6)
            c.line(xx, y0 + 4, xx, y1 - 4, PLANK * 0.55, 2)
        c.polyline([(BOX[0], y0), (BOX[1], y0), (BOX[1], y1), (BOX[0], y1)], PLANK * 0.45, 3, closed=True)
        SN.cap_flat(c, BOX[0], BOX[1], y0, self.depth(t) * 0.35 * (1 - self.fire(t) * 0.7))
        for j in range(3):                           # strip ends sticking out of the box until they are pulled
            if self.pair(j, t)[0] == "box":
                c.line(BOX[0] - 30, FORM_Y - 6 - 18 * j, BOX[0] + 4, FORM_Y - 6 - 18 * j, PLANK, 10)

    def _fire(self, c, t):
        f = self.fire(t)
        for q in range(4):                           # a little stack of firewood under the box
            a = (q - 1.5) * 0.35
            c.line(FIRE_X - 50 * math.cos(a), G - 6 - 10 * (q % 2), FIRE_X + 50 * math.cos(a), G - 14, TRUNK * 0.8, 9)
        if f > 0:
            for q in range(3):
                fl = 0.75 + 0.25 * math.sin(t * (9 + q * 3) + q)
                hh = (36 + 14 * q) * f * fl
                xx = FIRE_X + (q - 1) * 16
                c.polygon([(xx - 14, G - 12), (xx + 14, G - 12), (xx + 3 * math.sin(t * 7 + q), G - 12 - hh)],
                          LAMP * (0.9 - 0.15 * q) * f + np.array([30, 0, 0]))
            self.s.glow_draw(lambda g: g.circle(FIRE_X, G - 40, 120, LAMP * 0.45 * f))

    def _sleds(self, c, t):
        for k in range(3):
            pos = self.sled_pos(k, t)
            if pos is None:
                continue
            SL.draw_sled(c, pos[0], pos[1], 0.0, SLEDS[k][1], runners=(1.0, 1.0), slats=self.slats_on(k, t),
                         paint=self.paint(k, t), rope=self.rope(k, t), nose=1, clamp=self.pair(2 - k, t)[4], t=t)


def _slat_flat(c, x, y):
    """A slat lying flat (we see its length), centre (x, y)."""
    rect(c, x - SLAT_LEN / 2, y - SLAT_H / 2, x + SLAT_LEN / 2, y + SLAT_H / 2, PLANK * 1.02)
    c.line(x - SLAT_LEN / 2, y - SLAT_H / 2, x + SLAT_LEN / 2, y - SLAT_H / 2, PLANK * 1.2, 2)
    c.line(x - SLAT_LEN / 2, y + SLAT_H / 2, x + SLAT_LEN / 2, y + SLAT_H / 2, PLANK * 0.7, 2)


def _slat_end(c, x, y, col):
    """A slat seen end-on (as it sits on the sled), centre (x, y)."""
    h = SL.SLAT_T / 2
    rect(c, x - SL.SLAT_W / 2, y - h, x + SL.SLAT_W / 2, y + h, col)
    c.line(x - SL.SLAT_W / 2, y - h, x + SL.SLAT_W / 2, y - h, lighten(col, 1.2), 2)
