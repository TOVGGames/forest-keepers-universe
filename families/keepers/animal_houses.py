"""Forest Keepers episode 4: The Animal Houses (docs/engines/forest_keepers_animal_houses.md).

  WAKE     - a cold night at the treehouse: two bunnies, a hedgehog and two little birds huddle under it with
             nowhere warm to sleep. Glo has an idea; down the Keepers come and off they go.
  WHEEL    - by the stream: Digs digs a mill race, Hans sets the sluice gate, Twigs saws eight paddles with his
             new wrist saws while Wheels feeds the beam, Springs sets the A-frame legs, Glo checks it is level,
             Hans lifts the wheel in and fits every paddle, then the belt; the gate opens and the wheel turns.
  HOUSES   - (same world, no cut) the wheel drives a little forest workshop: Twigs cuts the panels, Digs drills
             the doors, Hans holds everything square while Springs bounces the nail press, Glo paints, Wheels
             loads them. Six houses: four birdhouses, a hedgehog house and a bunny house.
  DELIVER  - back at the treehouse every house goes where it belongs, the lamps go on and the animals move in.
Each Keeper's own body is the tool. Hans always works with his own tentacles (Monster.work_tentacle).
"""
import math

import numpy as np

from families.foundry.keepers.common import (GRAVITY, Jump, PLANK, WATER, WATER_DEEP, bunny, ellipse, hedgehog,
                                             lerp, rect, seg, settle, smoothstep, smootherstep, tree, wood_sign)
from families.foundry.keepers.forest import FIREFLY, POST, _firefly
from families.foundry.keepers.halloween import KeeperAct, hops, path
from families.foundry.products.monster import reach_tentacle
from families.foundry.style import IRON, STEEL
from families.foundry.tree_monsters import BARK, EARTH, EARTH_DARK, GRASS, LAMP, LEAF, SAWDUST, TRUNK

from . import props as PR

G = 1000.0
SOIL = np.array([58, 42, 32], np.float64)


def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def saw_to(m, t, tx, ty, dy=0.0, sx=-1):
    """Point one of Twigs' wrist saws (sx -1 left, 1 right) at (tx, ty): pick that arm's lift for the height, then
    return the body x that puts the blade at tx."""
    attr = "punch" if sx > 0 else "punch_l"
    lo, hi = 0.0, 1.0
    for _ in range(18):
        mid = (lo + hi) / 2
        setattr(m, attr, mid)
        if m.saw_center(sx, t, dy)[1] > ty:
            lo = mid
        else:
            hi = mid
    setattr(m, attr, (lo + hi) / 2)
    return m.x + tx - m.saw_center(sx, t, dy)[0]


def flying_bird(t, t0, t1, p0, p2, lift=260.0):
    """Bird flight from p0 to p2 on a soft arc, landing at t1 -> (x, y, flap, face)."""
    u = seg(t, t0, t1)
    ue = smoothstep(u) * 0.6 + u * 0.4
    p1 = ((p0[0] + p2[0]) / 2, min(p0[1], p2[1]) - lift)
    x, y = bez(p0, p1, p2, ue)
    flap = math.sin(t * 34) if 0 < u < 1 else 0.0
    return x, y, flap, (1 if p2[0] >= p0[0] else -1)


# ====================================================================== WAKE

class WakeAct(KeeperAct):
    """The treehouse on a cold night; the animals have nowhere warm to go."""
    name = "wake"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        H = self.house
        d = dict(hold=3.0, arrive=8.5, shiver=4.0, idea=2.5, down=8.5, go=6.5)
        d.update(P.get("durations", {}))
        T, t = {}, 0.0
        for k in ("hold", "arrive", "shiver", "idea", "down", "go"):
            T[k] = t
            t += d[k]
        self.T, self.d, self.dur = T, d, t
        self.start = {"tentacles": (1700.0, H.py), "teeth": (1210.0, H.py), "springs": (1460.0, H.py),
                      "lantern": (1360.0, H.py - 230), "wheels": (2300.0, G), "digger": (2470.0, G)}
        self.gx = {"lantern": 2010.0, "tentacles": 2150.0, "teeth": 2330.0, "springs": 2500.0, "wheels": 2670.0,
                   "digger": 2840.0}
        a = T["arrive"]
        self.animals = [dict(kind="bunny", x0=-520.0, x1=860.0, t0=a + 0.2, t1=a + 5.6),
                        dict(kind="bunny", x0=-780.0, x1=960.0, t0=a + 0.9, t1=a + 6.6),
                        dict(kind="hedgehog", x0=-420.0, x1=1080.0, t0=a + 0.4, t1=a + 7.6)]
        self.birds = [dict(cols=PR.ROBIN, p0=(-300.0, 160.0), p2=(1030.0, H.py), t0=a + 1.5, t1=a + 6.0),
                      dict(cols=PR.BLUE_TIT, p0=(3100.0, 120.0), p2=(1112.0, H.py), t0=a + 2.6, t1=a + 7.4)]

    def target(self, t):
        T, H = self.T, self.house
        base = (H.tx + 150, H.py + 150, 0.78)
        close = (1000.0, G - 290, 1.3)                  # the animals under the platform and the birds on it
        idea = (1300.0, G - 470, 0.98)
        if t < T["arrive"] + 1.0:
            return base
        if t < T["idea"]:
            u = smootherstep(seg(t, T["arrive"] + 1.0, T["arrive"] + 6.0))
            return lerp(base[0], close[0], u), lerp(base[1], close[1], u), lerp(base[2], close[2], u)
        if t < T["down"] + 1.0:
            u = smootherstep(seg(t, T["idea"] - 0.3, T["idea"] + 1.4))
            return lerp(close[0], idea[0], u), lerp(close[1], idea[1], u), lerp(close[2], idea[2], u)
        if t < T["go"] + 1.0:
            u = smootherstep(seg(t, T["down"] + 1.0, T["down"] + 4.0))
            return lerp(idea[0], base[0], u), lerp(idea[1], base[1], u), lerp(idea[2], base[2], u)
        u = smootherstep(seg(t, T["go"] + 1.0, self.dur))
        return lerp(base[0], 2900.0, u), base[1], base[2]

    def cold(self, t):
        """0..1 how much the animals shiver (until the Keepers set off)."""
        return smoothstep(seg(t, self.T["shiver"] - 1.0, self.T["shiver"] + 0.5))

    def update(self, t, dt):
        T, H, s = self.T, self.house, self.s
        self.reach = {}
        order = ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"]
        for q, kind in enumerate(order):
            m = self.m(kind)
            if m is None:
                continue
            x0, y0 = self.start[kind]
            gx = self.gx[kind]
            dy, walk, y = 0.0, None, None
            m.lamp = None
            if t < T["down"]:
                x, y = x0, y0
                if kind == "lantern":
                    i0 = T["idea"]
                    bump = math.exp(-((t - i0 - 0.5) / 0.7) ** 2) if t > i0 - 1 else 0.0
                    m.lamp = 1.0 + 0.9 * bump
                    dy = -34 * bump
            elif kind == "springs":
                j0 = T["down"] + 0.6
                jump = Jump(x0, y0, gx, G, apex=90)
                if t < j0:
                    x, y = x0, y0
                elif t < j0 + jump.dur:
                    x, y = jump.at(t - j0)
                else:
                    x, y = gx, G
                m.spring = 0.8 * max(0.0, 1 - min(abs(t - j0), abs(t - j0 - jump.dur)) / 0.12)
            elif kind == "lantern":
                x, y, _ = path([(T["down"] + 0.3, x0, y0), (T["down"] + 4.5, gx, G - 60)], t)
            elif kind in ("tentacles", "teeth"):
                k0 = T["down"] + (0.4 if kind == "tentacles" else 3.4)
                x, y, mv = path([(k0, x0, y0), (k0 + 1.0, H.ladder_x, y0), (k0 + 4.2, H.ladder_x, G),
                                 (k0 + 4.9, gx, G)], t)
                if kind == "tentacles" and k0 + 0.8 <= t < k0 + 4.3:
                    # lowers himself hand over hand: two tentacles hold the rungs just above his head
                    hy = y - 305 * m.k
                    grips = [(H.ladder_x + (26 if k % 2 else -26), H.rung_y(k)) for k in range(H.n_rungs)]
                    grips += [(H.ladder_x - 70, H.py + 4), (H.ladder_x + 34, H.py - 2)]
                    above = sorted((g for g in grips if g[1] < hy - 60), key=lambda g: -g[1])
                    self.reach["tentacles"] = above[:2]
                walk = 1.0 if mv else 0.0
            else:
                x, y, _ = path([(T["down"] + 1.0 + q * 0.3, x0, G), (T["down"] + 4.0 + q * 0.3, gx, G)], t)
            if t >= T["go"]:
                lead = T["go"] + 0.25 * q
                if kind == "springs":
                    x, lift, sq = hops(gx, gx + 1700, lead, lead + 5.6, t, apex=60, step=170)
                    dy -= lift
                    m.spring = sq
                elif kind == "lantern":
                    x, y, _ = path([(lead, gx, G - 60), (lead + 5.6, gx + 1700, G - 60)], t)
                else:
                    x, y, mv = path([(lead, gx, G), (lead + 5.6, gx + 1700, G)], t)
                    walk = 1.0 if mv else 0.0
            if kind == "lantern" and T["down"] + 4.5 <= t:
                y = G - 60 if y is None or y > G - 70 else y
            self.place(m, x, t, dt, y=y, dy=dy, walk=walk)
        # cold wind: leaves come down from the tree now and then
        if s.particles.rng.uniform() < 0.05 + 0.1 * self.cold(t):
            s.particles.leaves(H.tx + s.particles.rng.uniform(-700, 700), G - 1150, 1, 120)
        self._sounds(t)

    def _sounds(self, t):
        T, H = self.T, self.house
        for i, a in enumerate(self.animals):
            if a["kind"] == "bunny":
                n = 10
                for k in range(n):
                    if self.crossed(lerp(a["t0"], a["t1"], (k + 0.5) / n)):
                        self.hit(t, "pluck", self.s.note(k % 5 + 2 * i, 0), 0.18, lerp(a["x0"], a["x1"], k / n), G)
            else:
                if self.crossed(a["t0"] + 1.0):
                    self.fx(t, "rustle", a["t1"] - a["t0"] - 1.0, 0.2, a["x1"], G)
        for b in self.birds:
            if self.crossed(b["t1"]):
                self.hit(t, "bloop", 79, 0.25, b["p2"][0], b["p2"][1])
            if self.crossed(b["t1"] + 0.6):
                for k in range(3):
                    self.hit(t + k * 0.11, "music_box", (84, 88, 86)[k], 0.14, b["p2"][0], b["p2"][1])
        if self.crossed(T["shiver"] + 0.4):
            self.fx(t, "whoosh", 2.4, 0.18, H.tx, G - 600)
            self.say(t + 0.8, "wheels", "down", 2300, G, 0.35)
            self.say(t + 1.6, "tentacles", "down", 1700, H.py, 0.35)
        if self.crossed(T["idea"] + 0.3):
            self.hit(t, "bloop", 72, 0.4, 1360, H.py - 300)
            for k, n in enumerate((72, 76, 79, 84)):
                self.hit(t + 0.2 + k * 0.1, "chime", n, 0.3, 1360, H.py - 300)
            for q, kind in enumerate(("lantern", "tentacles", "teeth", "springs", "wheels", "digger")):
                self.say(t + 0.7 + q * 0.18, kind, "up", 1700, H.py, 0.38)
        if self.crossed(T["down"] + 0.6):
            self.hit(t, "boing", 55, 0.45, 1460, H.py)
        j = Jump(self.start["springs"][0], H.py, self.gx["springs"], G, apex=90)
        if self.crossed(T["down"] + 0.6 + j.dur):
            self.hit(t, "thud", 44, 0.4, self.gx["springs"], G)
        for k in range(H.n_rungs):
            for k0 in (T["down"] + 1.4, T["down"] + 4.4):
                if self.crossed(k0 + (H.n_rungs - 1 - k) * 3.2 / H.n_rungs):
                    self.hit(t, "clack", self.s.note(H.n_rungs - k, -1), 0.2, H.ladder_x, H.rung_y(k))
        if self.crossed(T["go"] + 0.3):
            self.fx(t, "rustle", 5.0, 0.16, 2600, G)
        if self.crossed(T["idea"] + 1.0):
            sp = self.s.particles
            sp.burst(1360, H.py - 330, 18, LAMP, 220, 1.0, 3, g=-60, glow=True)

    def animal_state(self, a, t):
        u = seg(t, a["t0"], a["t1"])
        x = lerp(a["x0"], a["x1"], smootherstep(u) * 0.3 + u * 0.7) if u > 0 else a["x0"]
        hop = abs(math.sin(u * 10 * math.pi)) * 30 if 0 < u < 1 and a["kind"] == "bunny" else 0.0
        if u >= 1:
            x += 2.0 * self.cold(t) * math.sin(t * 60 + a["x1"])
        return x, hop

    def draw(self, c, t):
        s, T, H = self.s, self.T, self.house
        self.backdrop(c, t)
        for j, x in enumerate((-400, 200, 2700, 3200, 3700, 4300)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        H.draw_tree(c, s)
        H.draw_house(c, s, t, windows=1.0, lanterns=1.0)
        for a in self.animals:
            x, hop = self.animal_state(a, t)
            if a["kind"] == "bunny":
                bunny(c, x, G, 1.3, hop, 1)
            else:
                hedgehog(c, x, G, 1.3, 1, t)
        for k, b in enumerate(self.birds):
            if t < b["t0"]:
                continue
            x, y, flap, face = flying_bird(t, b["t0"], b["t1"], b["p0"], b["p2"])
            if t >= b["t1"]:
                face = 1 if k == 0 else -1
                y -= 2.5 * self.cold(t) * abs(math.sin(t * 40 + k))
            PR.bird(c, x, y, 1.45, face, flap, b["cols"], t)
        if "lantern" in self.poses:
            ln = self.m("lantern")
            self.lantern_light(c, ln.x, ln.y - 140, k=0.8)
        self.draw_monsters(c, t)


# ====================================================================== the mill (WHEEL + HOUSES share this world)

STREAM = (150.0, 640.0)            # stream banks (the episode 2 bridge crosses it)
WY = G + 50.0                      # water surface of the stream / the race when it runs
RACE = (640.0, 1950.0)             # the mill race: from the stream to the culvert
RACE_FLOOR = G + 110.0
GATE_X = 760.0
WX, WR = 1650.0, 200.0             # water wheel
PLEN = 58.0                        # paddle length (radial)
WCY = G + 80.0 - (WR + PLEN)       # axle height: the lowest paddle tips run 30 above the race floor
LOAD_ANG = -math.pi / 4            # slot position where Hans fits the paddles (upper right)
STACK_X = 2140.0                   # paddle stack (two columns of four)
CUT_X, STOP_X, PIECE = 2330.0, 2272.0, 58.0
BEAM_Y = (G - 150.0, G - 120.0)    # beam top / bottom on the sawhorses
HORSES = (2330.0, 2640.0)
SHED = (3000.0, 6400.0)
ROOF_Y = G - 860.0
SHAFT_Y = G - 760.0
SHAFT_P = (3080.0, SHAFT_Y)        # the line shaft's drive pulley (the belt from the wheel)
SHAFT_R, AXLE_R = 34.0, 24.0


class Mill:
    """State shared by WHEEL and HOUSES: the race, gate, wheel and shed, drawn the same way in both."""

    def __init__(self):
        self.race_front = RACE[1]      # dug from here (culvert end) leftwards; RACE[0] when finished
        self.inlet = 0.0               # 0..1 the last bit to the stream is dug
        self.gate = 0.0                # gate frame placed 0..1
        self.gate_lift = 0.0           # board raised 0..1
        self.water_front = None        # x the race water has reached (None = dry)
        self.rot = 0.0                 # wheel angle
        self.omega = 0.0
        self.paddles = set()
        self.wheel_in = False          # on its bearing
        self.wheel_pos = None          # (x, y, rot) while it is moved by hand
        self.legs = (0.0, 0.0)
        self.bearing = 0.0
        self.belt = 0.0                # 0 hanging from the shaft, 1 on the axle pulley
        self.belt_end = None           # where Hans holds the belt loop while fitting it
        self.shaft_rot = 0.0

    def race_depth(self, x):
        """Floor of the race at x (G where not dug)."""
        if x < RACE[0] or x > RACE[1]:
            return G
        if x < GATE_X:
            return lerp(G, RACE_FLOOR, smoothstep(self.inlet * 1.05 - (GATE_X - x) / (GATE_X - RACE[0]) * 0.05)) \
                if self.inlet < 1 else RACE_FLOOR
        if x > self.race_front + 40:          # dug from the culvert end leftwards: x > front is done
            return RACE_FLOOR
        if x > self.race_front:
            return lerp(G, RACE_FLOOR, (x - self.race_front) / 40)
        return G

    def draw_ground(self, c, s, t):
        """Ground, stream with the episode 2 bridge, the race cut into the ground, its water."""
        vx0, vx1 = s.view()[:2]
        L, R = vx0 - 300, vx1 + 300
        # ground slabs either side of the stream
        for a, b in ((L, STREAM[0]), (STREAM[1], R)):
            if b > a:
                rect(c, a, G, b, G + 2500, EARTH)
                rect(c, a, G - 6, b, G + 4, GRASS)
        c.polygon([(STREAM[0], G), (STREAM[0] + 60, G + 200), (STREAM[1] - 60, G + 200), (STREAM[1], G),
                   (STREAM[1], G + 2500), (STREAM[0], G + 2500)], np.array([24, 20, 20]))
        # race: cut-away channel
        xs = np.linspace(RACE[0], RACE[1], 90)
        floor = [(x, self.race_depth(x)) for x in xs]
        if any(f > G + 1 for _, f in floor):
            # the far bank of the cut (fresh soil, lighter than the cut-away ground) and its wet floor
            c.polygon([(RACE[0], G - 4)] + floor + [(RACE[1], G - 4)], SOIL * 1.25)
            for k in range(3):
                yy = G + 25 + k * 28
                pts = [(x, yy + 4 * math.sin(x * 0.02 + k)) for x, f in floor if f > yy + 8]
                if len(pts) > 1:
                    c.polyline(pts, SOIL * 1.05, 3)
            c.polyline(floor, SOIL * 0.7, 7)
            c.polyline([(x, G - 2) for x, f in floor if f > G + 2], GRASS * 1.3, 4)
            for x in np.arange(RACE[0] + 20, RACE[1], 70):           # stones in the floor
                fy = self.race_depth(x)
                if fy > G + 60:
                    c.polygon(ellipse(x, fy - 6, 16, 7, 10), np.array([70, 64, 60]))
            c.circle(RACE[1] - 6, RACE_FLOOR - 40, 34, np.array([12, 10, 12]))       # culvert
            c.circle(RACE[1] - 6, RACE_FLOOR - 40, 34, np.array([90, 86, 82]), False, 6)
        # the spoil heap along the back of the race (behind, so drawn here, low and dark)
        dug = RACE[1] - self.race_front
        if dug > 5:
            pts = [(x, G - 10 - 26 * max(0.0, math.sin(math.pi * (x - self.race_front) / max(1.0, dug))) ** 0.6)
                   for x in np.linspace(self.race_front, RACE[1], 24)]
            c.polyline(pts, SOIL * 0.75, 10)

    def draw_water(self, c, s, t):
        """Stream water and race water, drawn in front of the banks (wading things sit half under it)."""
        L2, R2 = STREAM
        wave = [(x, WY + 4 * math.sin(x * 0.04 + t * 2.2)) for x in np.linspace(L2 + 10, R2 - 10, 40)]
        c.polygon(wave + [(R2 - 60, G + 200), (L2 + 60, G + 200)], WATER * 0.9)
        c.polyline(wave, WATER * 1.6, 3)
        s.glow_draw(lambda g: g.polyline(wave, np.array([120, 160, 220]) * 0.12, 5))
        for k in range(6):
            ph = (t * 0.4 + k * 0.19) % 1.0
            x = lerp(L2 + 60, R2 - 60, ph)
            c.line(x, WY + 30 + k * 18, x + 40, WY + 30 + k * 18, WATER * 1.4, 2)
        # race water: the inlet fills up to the gate as soon as it is open to the stream, past the gate once
        # the gate is lifted
        segs = []
        if self.inlet > 0.02:
            segs.append((RACE[0], GATE_X - 20 if self.water_front is None else self.water_front))
        for a, b in segs:
            if b - a < 4:
                continue
            xs = np.linspace(a, b, max(4, int((b - a) / 25)))
            top = []
            for x in xs:
                fl = self.race_depth(x)
                lvl = WY + 3 * math.sin(x * 0.05 + t * 3.0)
                if self.water_front is not None and x > self.water_front - 80:      # the front slopes down
                    lvl = lerp(lvl, fl - 6, (x - (self.water_front - 80)) / 80)
                top.append((x, min(lvl, fl - 2)))
            bottom = [(x, self.race_depth(x)) for x in xs[::-1]]
            c.polygon(top + bottom, WATER * 0.95)
            c.polyline(top, WATER * 1.65, 3)
            if self.water_front is not None:
                for k in range(int((b - a) / 70)):
                    x = a + ((k * 70 + t * 260) % max(1.0, b - a))
                    c.line(x, WY + 22, x + 30, WY + 22, PR.WATER_LIGHT * 0.8, 2)

    def draw_gate(self, c, t):
        if self.gate > 0:
            e = (1 - self.gate) ** 2 * 160
            PR.sluice(c, GATE_X, G - e, RACE_FLOOR - G, self.gate_lift)

    def wheel_xy(self):
        if self.wheel_in:
            return WX, WCY, self.rot
        return self.wheel_pos

    def draw_wheel(self, c, t):
        wp = self.wheel_xy()
        if wp is not None:
            PR.water_wheel(c, wp[0], wp[1], WR, wp[2], self.paddles)
        PR.aframe(c, WX, WCY, RACE_FLOOR, self.legs, self.bearing, spread=235.0)

    def draw_shed(self, c, s, t, front=False):
        if not front:
            PR.shed_back(c, SHED[0], SHED[1], G, ROOF_Y)
            return
        PR.shed_front(c, s, SHED[0], SHED[1], G, ROOF_Y, [SHED[0] + 20 + k * 850 for k in range(5)],
                      [SHED[0] + 425 + k * 850 for k in range(4)], t)
        PR.line_shaft(c, SHED[0] + 40, SHED[1] - 300, SHAFT_Y, self.shaft_rot,
                      [SHED[0] + 300 + k * 850 for k in range(4)])
        PR.pulley(c, SHAFT_P[0], SHAFT_P[1], SHAFT_R, self.shaft_rot)

    def draw_belt(self, c, t):
        if self.belt <= 0 and self.belt_end is None:
            # the loop hangs from the drive pulley, waiting
            hx, hy = SHAFT_P[0] - 10, SHAFT_P[1] + 330
            PR.belt(c, SHAFT_P, SHAFT_R, (hx, hy), 6, 0.0)
            return
        if self.belt < 1 and self.belt_end is not None:
            PR.belt(c, SHAFT_P, SHAFT_R, self.belt_end, 8, 0.0)
            return
        PR.belt(c, SHAFT_P, SHAFT_R, (WX, WCY), AXLE_R, -self.rot * AXLE_R)


def paddle_poly(cx, cy, ang, w=PLEN, h=30.0):
    """Paddle board centred at (cx, cy), its long side along angle `ang`."""
    ca, sa = math.cos(ang), math.sin(ang)
    hw, hh = w / 2, h / 2
    return [(cx - ca * hw + sa * hh, cy - sa * hw - ca * hh), (cx + ca * hw + sa * hh, cy + sa * hw - ca * hh),
            (cx + ca * hw - sa * hh, cy + sa * hw + ca * hh), (cx - ca * hw - sa * hh, cy - sa * hw + ca * hh)]


def stack_spot(i):
    """Bottom-centre of paddle i on the stack (two columns of four)."""
    col, row = divmod(i, 4)
    return STACK_X + col * 66, G - row * 31


# ====================================================================== WHEEL

class WheelAct(KeeperAct):
    """Build the water wheel (see module docstring)."""
    name = "wheel"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.mill = scene.__dict__.setdefault("mill", Mill())
        d = dict(arrive=8.0, dig=14.0, gate=3.5, inlet=3.5, cut=22.0, legs=10.0, bearing=2.5, level=4.5,
                 lift=7.0, paddles=28.0, belt=5.0, open=3.0, flow=4.0, spin=6.0, pan=8.0)
        d.update(P.get("durations", {}))
        T, t = {}, 0.0
        for k in ("arrive", "dig", "gate", "inlet", "cut", "legs", "bearing", "level", "lift", "paddles", "belt",
                  "open", "flow", "spin", "pan"):
            T[k] = t
            t += d[k]
        self.T, self.d, self.dur = T, d, t
        self.cut_cyc = d["cut"] / 8
        self.pad_cyc = d["paddles"] / 8
        self._plan_springs()
        self.stats = {}

    # ----- timing helpers -----

    def cut_phase(self, t):
        """(piece index i, phase 0..1 within its cycle) while the paddles are cut, else None."""
        T = self.T
        if not T["cut"] <= t < T["cut"] + self.d["cut"]:
            return None
        u = (t - T["cut"]) / self.cut_cyc
        return int(u), u - int(u)

    def beam_left(self, t):
        """Left end of the beam: pieces 0..i-1 are gone; Wheels pushes it up to the stop after each cut."""
        T = self.T
        if t < T["cut"]:
            return STOP_X
        k = min(8.0, (t - T["cut"]) / self.cut_cyc)
        i, ph = int(k), k - int(k)
        push = smootherstep(seg(ph, 0.62, 0.92))
        return STOP_X + PIECE * (1 - push) if i >= 1 or ph >= 0.62 else STOP_X

    def pieces_cut(self, t):
        T = self.T
        if t < T["cut"]:
            return 0
        k = (t - T["cut"]) / self.cut_cyc
        return min(8, int(k) + (1 if k - int(k) >= 0.32 else 0))

    def piece_state(self, i, t):
        """Paddle i before it goes on the wheel: ('beam'|'carry'|'stack', x, y, ang)."""
        T = self.T
        t_take = T["cut"] + (i + 0.35) * self.cut_cyc
        t_down = T["cut"] + (i + 0.6) * self.cut_cyc
        bx, by = STOP_X + PIECE / 2, (BEAM_Y[0] + BEAM_Y[1]) / 2
        sx, sy = stack_spot(i)
        sy -= 15
        if t < t_take:
            return "beam", bx, by, 0.0
        if t < t_down:
            u = smootherstep(seg(t, t_take, t_down))
            x, y = bez((bx, by), ((bx + sx) / 2, min(by, sy) - 90), (sx, sy), u)
            return "carry", x, y, 0.0
        return "stack", sx, sy, 0.0

    def paddle_times(self, k):
        """Paddle k (slot k): (take from stack, slotted, turn start, turn end)."""
        t0 = self.T["paddles"] + k * self.pad_cyc
        return t0 + 0.1, t0 + 0.55 * self.pad_cyc, t0 + 0.62 * self.pad_cyc, t0 + 0.95 * self.pad_cyc

    def wheel_rot(self, t):
        """Wheel angle: slot k sits at LOAD_ANG while paddle k goes in; each turn advances it by one slot."""
        T = self.T
        rot = LOAD_ANG
        if t < T["paddles"]:
            return rot
        for k in range(8):
            _, _, a, b = self.paddle_times(k)
            if k < 7:
                rot -= (2 * math.pi / 8) * smootherstep(seg(t, a, b))
        return rot

    def _plan_springs(self):
        """Springs sets the two A-frame legs: a jump into the dry race with each leg overhead, a stomp, a jump out."""
        T, segs = self.T, []
        bank = RACE[1] + 70
        t = T["legs"] + 0.3
        self.leg_t = {}
        for k, fx in enumerate((WX + 235.0, WX - 235.0)):
            j = Jump(bank, G, fx, RACE_FLOOR, apex=120 if k == 0 else 220)
            segs.append((t, t + j.dur, j, k))
            t += j.dur
            self.leg_t[k] = t
            st = Jump(fx, RACE_FLOOR, fx, RACE_FLOOR, apex=90)
            segs.append((t + 0.35, t + 0.35 + st.dur, st, None))
            t += 0.35 + st.dur + 0.15
            out = Jump(fx, RACE_FLOOR, bank, G, apex=140 if k == 0 else 230)
            segs.append((t, t + out.dur, out, None))
            t += out.dur + 0.4
        self.sp_segs = segs

    def springs_at(self, t):
        """(x, y, carrying leg k or None) during the legs step."""
        last = (RACE[1] + 70, G)
        for t0, t1, j, carry in self.sp_segs:
            if t0 <= t < t1:
                x, y = j.at(t - t0)
                return x, y, carry
            if t >= t1:
                last = (j.x1, j.y1)
        return last[0], last[1], None

    def leg_u(self, k, t):
        tl = self.leg_t[k]
        return smootherstep(seg(t, tl, tl + 0.7))

    def gate_t(self):
        return self.T["open"] + 0.5

    def flow_t(self):
        return self.T["open"] + 1.6

    # ----- camera -----

    def target(self, t):
        T, H = self.T, self.s.h
        z = 1.05

        def yz(z):
            return G - H * 0.3 / z
        y = yz(z)
        if t < T["arrive"]:
            u = smootherstep(seg(t, 0, T["arrive"]))
            return lerp(100, 1300, u), yz(0.9), 0.9
        if t < T["gate"]:
            dg = self.m("digger")
            u = smootherstep(seg(t, T["arrive"], T["arrive"] + 2.0))
            return float(np.clip(dg.x if dg else 1300, 1000, 1800)) - 50, lerp(yz(0.9), y, u), lerp(0.9, z, u)
        if t < T["cut"]:
            return 1000, y, z
        if t < T["legs"]:
            return 2430, yz(1.2), 1.2
        if t < T["lift"]:
            return 1760, yz(0.95), 0.95
        if t < T["paddles"]:
            u = smootherstep(seg(t, T["lift"], T["lift"] + 3.0))
            return lerp(2700, 1950, u), yz(0.95), 0.95
        if t < T["belt"]:
            return 1840, yz(1.12) - 60, 1.12
        if t < T["open"]:
            u = smootherstep(seg(t, T["belt"], T["belt"] + 2.0))
            return lerp(1880, 2300, u), lerp(y, y - 90, u), lerp(z, 0.75, u)
        if t < T["pan"]:
            u = smootherstep(seg(t, T["open"], T["open"] + 1.5))
            return lerp(2300, 1350, u), lerp(y - 90, y, u), lerp(0.75, 0.82, u)
        u = smootherstep(seg(t, T["pan"], self.dur))
        return lerp(1350, 3500, u), lerp(y, y - 60, u), lerp(0.82, 0.78, u)

    # ----- update -----

    def update(self, t, dt):
        T, M, s = self.T, self.mill, self.s
        self.reach = {}
        self.carry = {}
        # the race, the gate and the water
        M.race_front = lerp(RACE[1], GATE_X, seg(t, T["dig"], T["dig"] + self.d["dig"]))
        M.gate = smootherstep(seg(t, T["gate"] + 0.6, T["gate"] + 2.8))
        M.inlet = seg(t, T["inlet"] + 0.3, T["inlet"] + 2.8)
        M.gate_lift = smootherstep(seg(t, self.gate_t(), self.gate_t() + 1.2))
        if t >= self.gate_t() + 0.3:
            M.water_front = min(RACE[1] - 30, GATE_X + 520 * (t - self.gate_t() - 0.3))
        else:
            M.water_front = None
        M.legs = (self.leg_u(0, t), self.leg_u(1, t))
        M.bearing = smootherstep(seg(t, T["bearing"] + 0.6, T["bearing"] + 2.0))
        M.paddles = {k for k in range(8) if t >= self.paddle_times(k)[1]}
        # the wheel: leaning by the shed, rolled over, lifted onto its bearing
        lean = (3000.0, G - WR - 9, 0.0)                     # rolled in from the shed side
        r0 = T["lift"]
        roll_end = (2330.0, G - WR - 9)
        if t < r0 - 1.4:
            M.wheel_pos, M.wheel_in = None, False
        elif t < r0 + 2.6:
            u = smootherstep(seg(t, r0 - 1.4, r0 + 2.6))
            x = lerp(lean[0], roll_end[0], u)
            M.wheel_pos, M.wheel_in = (x, roll_end[1], (x - lean[0]) / WR), False
        elif t < r0 + 6.2:
            u = smootherstep(seg(t, r0 + 2.6, r0 + 6.2))
            x, y = bez(roll_end, (2000.0, roll_end[1] - 160), (WX, WCY), u)
            rot0 = (roll_end[0] - lean[0]) / WR
            M.wheel_pos, M.wheel_in = (x, y, lerp(rot0, LOAD_ANG, u)), False
        else:
            M.wheel_in = True
        # spinning: once the water reaches the wheel it spins up (exponential approach to its running speed)
        t_hit = self.gate_t() + 0.3 + (WX - 230 - GATE_X) / 520.0
        if t < T["paddles"] + self.d["paddles"]:
            M.rot = self.wheel_rot(t)
            M.omega = 0.0
        elif t >= t_hit:
            tau, w_run = 1.8, 1.25
            dtt = t - t_hit
            M.omega = w_run * (1 - math.exp(-dtt / tau))
            M.rot = self.wheel_rot(t) - w_run * (dtt - tau * (1 - math.exp(-dtt / tau)))
        else:
            M.rot = self.wheel_rot(t)
        M.shaft_rot = M.rot * AXLE_R / SHAFT_R if M.belt >= 1 else 0.0
        self.t_hit = t_hit
        self._digs(t, dt)
        self._twigs(t, dt)
        self._wheels(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._particles(t)
        self._sounds(t)
        self.stats = {"paddles_fitted": len(M.paddles)}

    def _arrive_x(self, q, x1, t):
        """Walk in over the bridge, front of the line first."""
        x, y, mv = path([(0.3 + q * 0.35, -700.0 - q * 170, G), (self.T["dig"] - 0.6 + q * 0.2, x1, G)], t)
        on_bridge = STREAM[0] - 20 < x < STREAM[1] + 20
        return x, (G - 40 if on_bridge else G), mv

    def _digs(self, t, dt):
        m, T, M = self.m("digger"), self.T, self.mill
        if m is None:
            return
        m.dig = 0.0
        y, walk = None, None
        if t < T["dig"]:
            x, y, mv = self._arrive_x(1, RACE[1] + 70, t)
            walk = 1.0 if mv else 0.0
        elif t < T["gate"]:
            # digs leftwards, standing in the race just behind the face
            x = M.race_front + 70
            y = M.race_depth(x - 30) if t > T["dig"] + 0.6 else G
            y = min(RACE_FLOOR, y)
            m.dig = 0.5 + 0.5 * math.sin(t * 16)
        elif t < T["inlet"]:
            x, y = GATE_X + 120, RACE_FLOOR
        elif t < T["inlet"] + 3.0:
            u = seg(t, T["inlet"], T["inlet"] + 2.6)
            x = lerp(GATE_X + 100, GATE_X - 40, smoothstep(min(1.0, u * 1.5)))
            y = RACE_FLOOR
            m.dig = 0.5 + 0.5 * math.sin(t * 16) if u < 1 else 0.0
        elif t < T["cut"] + 1.5:
            # climbs out of the race next to the gate and waits on the bank
            x, y, _ = path([(T["inlet"] + 3.0, GATE_X + 120, RACE_FLOOR), (T["cut"] + 1.5, GATE_X + 60, G)], t)
        elif t < self.gate_t() - 1.0:
            x, y = GATE_X + 60, G
        else:
            # pulls the gate rod up with a shovel hand
            x, y = GATE_X + 60, G
            m.dig = 0.4 + 0.6 * smoothstep(seg(t, self.gate_t() - 0.2, self.gate_t() + 1.2))
        if t >= T["spin"] + 1.0:
            x, y, mv = path([(T["spin"] + 1.0, GATE_X + 60, G), (T["pan"] + 6.0, 3150.0, G)], t)
            walk = 1.0 if mv else 0.0
        self.place(m, x, t, dt, y=y, walk=walk)

    def _twigs(self, t, dt):
        m, T = self.m("teeth"), self.T
        if m is None:
            return
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        walk = None
        home = CUT_X + 80                    # stands right of the cut line and saws with his left wrist
        if t < T["dig"]:
            x, _, mv = self._arrive_x(3, home, t)
            walk = 1.0 if mv else 0.0
        elif t < T["cut"]:
            x = home
        elif t < T["cut"] + self.d["cut"]:
            i, ph = self.cut_phase(t)
            if i < 7:
                # down through the beam at the cut line: from above the top to below the bottom
                if ph < 0.06:
                    ty = lerp(BEAM_Y[0] - 70, BEAM_Y[0] - 22, ph / 0.06)
                elif ph < 0.32:
                    ty = lerp(BEAM_Y[0] - 22, BEAM_Y[1] + 24, smoothstep((ph - 0.06) / 0.26))
                elif ph < 0.5:
                    ty = lerp(BEAM_Y[1] + 24, BEAM_Y[0] - 70, smoothstep((ph - 0.32) / 0.18))
                else:
                    ty = BEAM_Y[0] - 70
                m.saw_run = smoothstep(seg(ph, 0.0, 0.05)) * (1 - smoothstep(seg(ph, 0.4, 0.55)))
                m.x = home if not m.x else m.x
                x = saw_to(m, t, CUT_X, ty, sx=-1)
            else:
                x = m.x
        else:
            x = home
            if t >= T["legs"]:
                x, _, mv = path([(T["legs"], home, G), (T["legs"] + 3.0, 2800.0, G)], t)
                walk = 1.0 if mv else 0.0
            if t >= T["spin"] + 1.0:
                x, _, mv = path([(T["spin"] + 1.0, 2800.0, G), (T["pan"] + 6.0, 3360.0, G)], t)
                walk = 1.0 if mv else 0.0
        m.saw_spin += dt * 38 * m.saw_run
        self.place(m, x, t, dt, walk=walk)

    def _wheels(self, t, dt):
        m, T = self.m("wheels"), self.T
        if m is None:
            return
        m.punch = 0.0
        if t < T["dig"]:
            x, _, _ = self._arrive_x(4, 2736.0 + 128, t)
        elif t < T["cut"] + self.d["cut"]:
            right = self.beam_left(t) + 8 * PIECE - PIECE * min(8, self.pieces_taken(t))
            x = right + 128
            i_ph = self.cut_phase(t)
            if i_ph and 0.6 < i_ph[1] < 0.95:
                m.punch = 0.6
        else:
            x = 2736.0 - 7 * PIECE + 128
            if t >= T["belt"]:
                x, _, _ = path([(T["belt"], x, G), (T["belt"] + 3.0, 2720.0, G)], t)
            if t >= T["spin"] + 1.0:
                x, _, _ = path([(T["spin"] + 1.0, 2720.0, G), (T["pan"] + 6.0, 3600.0, G)], t)
        self.place(m, x, t, dt)

    def pieces_taken(self, t):
        T = self.T
        if t < T["cut"]:
            return 0
        return sum(1 for i in range(8) if t >= T["cut"] + (i + 0.35) * self.cut_cyc)

    def _hans(self, t, dt):
        m, T, M = self.m("tentacles"), self.T, self.mill
        if m is None:
            return
        reach = []
        walk = None
        x = 2000.0
        if t < T["dig"]:
            x, y, mv = self._arrive_x(0, 1100.0, t)
            walk = 1.0 if mv else 0.0
        elif t < T["gate"]:
            x, _, mv = path([(T["dig"], 1100.0, G), (T["gate"], 980.0, G)], t)
            walk = 1.0 if mv else 0.0
        elif t < T["inlet"]:
            x = 980.0
            u = M.gate
            reach = [(GATE_X - 30, G - 150 - (1 - u) ** 2 * 160), (GATE_X + 30, G - 150 - (1 - u) ** 2 * 160)]
        elif t < T["cut"]:
            x, _, mv = path([(T["inlet"] + 0.5, 980.0, G), (T["cut"], 2040.0, G)], t)
            walk = 1.0 if mv else 0.0
        elif t < T["cut"] + self.d["cut"]:
            x = 2040.0
            for i in range(8):
                st = self.piece_state(i, t)
                if st[0] == "carry":
                    reach = [(st[1], st[2])]
        elif t < T["legs"] + self.d["legs"] + self.d["bearing"]:
            x = 2010.0
            # holds the tops of the legs together while Springs sets them, then fits the bearing block
            for k, lx in enumerate((WX + 20, WX - 20)):
                if M.legs[k] > 0:
                    u = M.legs[k]
                    e = (1 - u) ** 2 * 200
                    reach.append((lx + (1 if k == 0 else -1) * e, WCY + 14 - e))
            if T["bearing"] <= t:
                u = M.bearing
                bx, by = bez((2060.0, G - 230), (1850.0, WCY - 220), (WX, WCY - (1 - u) ** 2 * 120), min(1.0, seg(t, T["bearing"], T["bearing"] + 2.0)))
                reach.append((bx, by))
        elif t < T["lift"] - 1.4:
            x, _, mv = path([(T["level"], 2010.0, G), (T["lift"] - 1.4, 3190.0, G)], t)
            walk = 1.0 if mv else 0.0
        elif t < T["paddles"]:
            r0 = T["lift"]
            wp = M.wheel_xy()
            if wp is None:
                wp = (3000.0, G - WR - 9, 0.0)
            if t < r0 + 2.6:
                x = wp[0] + 190
                walk = 1.0
            else:
                x, _, mv = path([(r0 + 2.6, 2520.0, G), (r0 + 5.0, 2030.0, G)], t)
                walk = 1.0 if mv else 0.0
            # two tentacles on the rim (top-right and right), a third under it while lifting
            reach = [(wp[0] + WR * 0.62, wp[1] - WR * 0.78), (wp[0] + WR * 0.98, wp[1] + 10)]
            if t >= r0 + 2.6:
                reach.append((wp[0] + WR * 0.35, wp[1] + WR * 0.94))
            if t >= r0 + 6.2:
                reach = []
        elif t < T["belt"]:
            x = 2030.0
            for k in range(8):
                t_take, t_in, a, b = self.paddle_times(k)
                if t_take <= t < t_in + 0.15:
                    reach = [self.paddle_carry(k, t)[:2]]
                if a - 0.05 <= t < b:
                    # turns the wheel one slot on with another tentacle on the rim
                    ang = M.rot - math.pi / 2 + 0.35
                    reach.append((WX + math.cos(ang) * (WR + 4), WCY + math.sin(ang) * (WR + 4)))
        elif t < T["open"]:
            x, _, mv = path([(T["belt"], 2030.0, G), (T["belt"] + 1.4, 2350.0, G)], t)
            walk = 1.0 if mv else 0.0
            u = seg(t, T["belt"] + 0.6, T["belt"] + 4.2)
            hang = (SHAFT_P[0] - 10, SHAFT_P[1] + 330)
            if u <= 0:
                M.belt, M.belt_end = 0.0, None
            elif u < 1:
                p = bez(hang, ((hang[0] + WX) / 2 + 200, WCY - 120), (WX, WCY), smootherstep(u))
                M.belt, M.belt_end = 0.5, p
                reach = [p]
            else:
                M.belt, M.belt_end = 1.0, None
        else:
            x = 2350.0
            M.belt, M.belt_end = 1.0, None
            if t >= T["spin"] + 1.0:
                x, _, mv = path([(T["spin"] + 1.0, 2350.0, G), (T["pan"] + 6.0, 3780.0, G)], t)
                walk = 1.0 if mv else 0.0
        if t < T["belt"]:
            M.belt, M.belt_end = 0.0, None
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt, walk=walk)

    def paddle_carry(self, k, t):
        """Paddle k on its way from the stack to slot k (x, y, angle)."""
        t_take, t_in, _, _ = self.paddle_times(k)
        i = 7 - k                                            # top of the stack first
        sx, sy = stack_spot(i)
        sy -= 15
        u = smootherstep(seg(t, t_take, t_in))
        ang_slot = LOAD_ANG
        r = WR - 12 + PLEN / 2
        tx, ty = WX + math.cos(ang_slot) * (r + 30 * (1 - smoothstep(seg(t, t_in - 0.35, t_in)))), \
                 WCY + math.sin(ang_slot) * (r + 30 * (1 - smoothstep(seg(t, t_in - 0.35, t_in))))
        x, y = bez((sx, sy), ((sx + tx) / 2 + 60, min(sy, ty) - 120), (tx, ty), min(1.0, u * 1.15))
        return x, y, lerp(0.0, ang_slot, smoothstep(u))

    def _springs(self, t, dt):
        m, T = self.m("springs"), self.T
        if m is None:
            return
        m.spring = 0.0
        y, dy = None, 0.0
        if t < T["dig"]:
            x, _, mv = self._arrive_x(2, RACE[1] + 70, t)
            if mv:
                ph = (t * 2.8) % 1.0
                dy = -4 * 55 * ph * (1 - ph)
        elif t < T["cut"]:
            x = RACE[1] + 150
        elif t < T["legs"]:
            x, _, mv = path([(T["cut"], RACE[1] + 150, G), (T["cut"] + 3.0, 3040.0, G),
                             (T["legs"] - 2.6, 3040.0, G), (T["legs"] + 0.2, RACE[1] + 70, G)], t)
            if mv:
                ph = (t * 2.8) % 1.0
                dy = -4 * 55 * ph * (1 - ph)
        elif t < T["lift"]:
            x, y, carry = self.springs_at(t)
            for t0, t1, j, cr in self.sp_segs:
                if abs(t - t0) < 0.1 or abs(t - t1) < 0.1:
                    m.spring = 0.7
            self.carry["springs"] = carry
        else:
            x = RACE[1] + 70
            if t >= T["flow"] + 1.0:
                ph = (t - T["flow"] - 1.0) % 1.1
                if t < T["pan"]:
                    dy = -4 * 80 * (ph / 0.55) * (1 - ph / 0.55) if ph < 0.55 else 0.0
                    m.spring = 0.6 if ph < 0.06 or 0.5 < ph < 0.6 else 0.0
            if t >= T["spin"] + 1.0:
                x, lift, sq = hops(RACE[1] + 70, 3560.0, T["pan"] + 0.5, T["pan"] + 6.5, t, apex=60, step=170)
                dy -= lift
                m.spring = max(m.spring, sq)
        self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)

    def _glo(self, t, dt):
        m, T, M = self.m("lantern"), self.T, self.mill
        if m is None:
            return
        y = G - 60
        if t < T["dig"]:
            x, _, _ = self._arrive_x(-1, 1500.0, t)
            x += 260
        elif t < T["cut"]:
            dg = self.m("digger")
            x = (dg.x if dg else 1300) - 170
            y = G - 120
        elif t < T["level"]:
            x, y, _ = path([(T["cut"], 1200.0, G - 120), (T["cut"] + 3.0, 2480.0, G - 260),
                            (T["legs"], 2480.0, G - 260), (T["legs"] + 3.0, 1650.0, G - 380)], t)
        elif t < T["lift"]:
            # carries the level down onto the A-frame's cross bar, holds it there, lifts it away
            bar_y = lerp(WCY, RACE_FLOOR, 0.55) - 8
            x, yy, _ = path([(T["level"], 1650.0, G - 380), (T["level"] + 1.0, 1650.0, bar_y + 20),
                             (T["level"] + 2.8, 1650.0, bar_y + 20), (T["lift"], 1500.0, G - 380)], t)
            y = yy
        else:
            x, y = 1430.0, G - 380
            if t >= T["belt"]:
                x, y, _ = path([(T["belt"], 1430.0, G - 380), (T["belt"] + 3.0, 2100.0, G - 480)], t)
            if t >= T["open"]:
                x, y, _ = path([(T["open"], 2100.0, G - 480), (T["open"] + 2.0, 1150.0, G - 300)], t)
            if t >= T["spin"] + 1.0:
                x, y, _ = path([(T["spin"] + 1.0, 1150.0, G - 300), (T["pan"] + 6.0, 3250.0, G - 380)], t)
        self.place(m, x, t, dt, y=y)

    def level_state(self, t):
        """(x, y, bubble, ok) of the spirit level Glo carries, or None."""
        T = self.T
        if not T["level"] <= t < T["lift"]:
            return None
        gl = self.m("lantern")
        bar_y = lerp(WCY, RACE_FLOOR, 0.55) - 8
        u = seg(t, T["level"] + 1.0, T["level"] + 2.8)
        y = gl.y - 2 if not 0 < u < 1 else bar_y
        bub = 0.9 * math.exp(-u * 3.0) * math.cos(u * 14) if u > 0 else 0.9
        ok = smoothstep(seg(u, 0.6, 0.8))
        return gl.x, y, bub, ok

    # ----- particles + sounds -----

    def _particles(self, t):
        T, M, P = self.T, self.mill, self.s.particles
        dg = self.m("digger")
        if dg is not None and dg.dig > 0.6 and P.rng.uniform() < 0.6:
            P.burst(dg.x - 70, dg.y - 20, 2, SOIL * 1.7, 320, 0.8, 5, g=1300, spread=0.7, direction=-math.pi * 0.7)
        tw = self.m("teeth")
        if tw is not None and tw.saw_run > 0.5:
            cx, cy = tw.saw_center(-1, self.t_local(), 0.0)
            if BEAM_Y[0] - 20 < cy < BEAM_Y[1] + 20 and P.rng.uniform() < 0.9:
                P.burst(CUT_X, BEAM_Y[1], 3, SAWDUST, 300, 0.6, 3.5, g=900, spread=0.6, direction=math.pi * 0.6)
        if M.omega > 0.2 and M.wheel_in:
            for k in M.paddles:
                tx, ty = PR.paddle_tip(WX, WCY, WR, M.rot, k)
                if WY - 10 < ty < WY + 40 and P.rng.uniform() < 0.5 * M.omega:
                    P.burst(tx, WY, 2, PR.FOAM, 260, 0.6, 3.5, g=1400, spread=0.6, direction=-math.pi * 0.55)
        if M.water_front is not None and M.water_front < RACE[1] - 40 and P.rng.uniform() < 0.6:
            P.burst(M.water_front, WY - 4, 2, PR.FOAM, 200, 0.5, 3, g=1200, spread=0.8, direction=-math.pi * 0.3)

    def t_local(self):
        return self.s._t - self.t0

    def _sounds(self, t):
        T, s = self.T, self.s
        if self.crossed(0.6):
            self.fx(t, "bubble", self.dur - 1.0, 0.12, (STREAM[0] + STREAM[1]) / 2, WY)
        for k in range(10):
            if self.crossed(T["dig"] + 0.4 + k * self.d["dig"] / 10):
                self.fx(t, "slide", 0.35, 0.28, lerp(RACE[1], GATE_X, k / 10), G)
        if self.crossed(T["gate"] + 2.7):
            self.hit(t, "clunk", 48, 0.4, GATE_X, G)
        if self.crossed(T["inlet"] + 2.2):
            self.fx(t, "splash", 0.9, 0.4, RACE[0] + 40, WY)
            self.fx(t + 0.4, "gurgle", 1.4, 0.25, RACE[0] + 60, WY)
        for i in range(8):
            c0 = T["cut"] + i * self.cut_cyc
            if i < 7 and self.crossed(c0 + 0.02):
                self.fx(t, "saw", self.cut_cyc * 0.42, 0.22, CUT_X, BEAM_Y[0])
            if self.crossed(c0 + 0.6 * self.cut_cyc):
                self.hit(t, "clack", s.note(i, 0), 0.32, STACK_X, G)
            if i < 7 and self.crossed(c0 + 0.9 * self.cut_cyc):
                self.fx(t, "slide", 0.3, 0.2, CUT_X + 200, BEAM_Y[0])
        for k in range(2):
            tl = self.leg_t[k]
            if self.crossed(tl):
                self.hit(t, "thud", 42, 0.45, WX, RACE_FLOOR)
            if self.crossed(tl + 0.7):
                self.hit(t, "clack", s.note(2 + k * 2, -1), 0.4, WX, WCY)
        for t0, t1, j, cr in self.sp_segs:
            if self.crossed(t0):
                self.hit(t, "boing", s.note(int(t0 * 3) % 5, -1), 0.4, j.x0, j.y0)
        if self.crossed(T["bearing"] + 2.0):
            self.hit(t, "clunk", 50, 0.45, WX, WCY)
            self.fx(t, "servo", 0.6, 0.2, WX, WCY)
        lv = T["level"] + 1.0 + 0.7 * 1.8
        if self.crossed(lv):
            for k, n in enumerate((76, 79, 84)):
                self.hit(t + k * 0.09, "chime", n, 0.3, WX, WCY)
        r0 = T["lift"]
        if self.crossed(r0 + 0.1):
            self.fx(t, "creak", 2.5, 0.25, 2700, G)
        if self.crossed(r0 + 6.2):
            self.hit(t, "clunk", 45, 0.5, WX, WCY)
            self.say(t + 0.3, "tentacles", "hum", WX, WCY, 0.4)
        for k in range(8):
            _, t_in, a, b = self.paddle_times(k)
            if self.crossed(t_in):
                self.hit(t, "clack", s.note(k, 0), 0.4, WX + 140, WCY - 140)
            if k < 7 and self.crossed(b - 0.05):
                self.hit(t, "clack", s.note(k + 2, -1), 0.18, WX, WCY)
        if self.crossed(T["paddles"] + self.d["paddles"] - 0.4):
            for q, kind in enumerate(("springs", "lantern", "wheels")):
                self.say(t + q * 0.2, kind, "up", 2200, G - 200, 0.4)
        if self.crossed(T["belt"] + 4.2):
            self.hit(t, "clunk", 52, 0.35, WX, WCY)
        if self.crossed(self.gate_t()):
            self.fx(t, "creak", 1.2, 0.3, GATE_X, G - 100)
        if self.crossed(self.gate_t() + 0.3):
            self.fx(t, "splash", 1.2, 0.45, GATE_X, WY)
            self.fx(t + 0.2, "gurgle", 3.5, 0.3, GATE_X + 300, WY)
        if self.crossed(self.t_hit):
            self.fx(t, "splash", 1.0, 0.5, WX, WY)
            self.fx(t, "creak", 3.0, 0.3, WX, WCY)
        if self.crossed(self.t_hit + 1.5):
            self.fx(t, "bubble", self.dur - self.t_hit - 1.0, 0.18, WX, WY)
        if self.crossed(self.t_hit + 2.2):
            for q, kind in enumerate(("wheels", "tentacles", "teeth", "springs", "lantern", "digger")):
                self.say(t + q * 0.2, kind, "cheer", WX + 300, G - 200, 0.45)
            for k, n in enumerate((72, 76, 79, 84)):
                self.hit(t + 1.3 + k * 0.12, "soft_bell", n, 0.35, WX, WCY)
        # the wheel's splashes keep time as it runs
        if self.t_hit < t:
            M = self.mill
            for k in M.paddles:
                a = M.rot + k * 2 * math.pi / 8
                prev = a + M.omega * (1 / 60)
                if math.sin(prev) < 0.92 <= math.sin(a) and P_ok(M.omega):
                    self.fx(t, "splash", 0.35, 0.1 * M.omega, WX, WY)

    # ----- drawing -----

    def draw(self, c, t):
        s, T, M = self.s, self.T, self.mill
        self.night.draw(s, c, t)
        for j, x in enumerate((-650, -250, 2950, 3250)):
            if s.visible(x - 250, x + 250) and not (SHED[0] - 200 < x < SHED[1]):
                tree(c, x, G, 640 + 60 * (j % 2), 1300 + j)
        M.draw_shed(c, s, t)
        M.draw_ground(c, s, t)
        wood_sign(c, -420, G, "WATER WHEEL", lit=1.0, glow_fn=s.glow_draw)
        # bridge from episode 2
        for px in (STREAM[0] - 20, STREAM[1] + 20):
            rect(c, px - 14, G - 40, px + 14, G + 40, POST)
        pw = (STREAM[1] - STREAM[0] + 40) / 9
        for k in range(9):
            x0 = STREAM[0] - 20 + k * pw
            rect(c, x0 + 2, G - 40, x0 + pw - 2, G - 22, PLANK * (0.95 + 0.08 * (k % 2)))
        M.draw_gate(c, t)
        self._saw_bench(c, t)
        self._stack(c, t)
        M.draw_belt(c, t)
        M.draw_wheel(c, t)
        lv = self.level_state(t)
        if lv is not None:
            PR.level(c, lv[0], lv[1], 170, lv[2], lv[3])
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 120, k=0.9)
        self.draw_monsters(c, t, before=lambda kind: self._carried(c, kind, t))
        M.draw_water(c, s, t)
        M.draw_shed(c, s, t, front=True)

    def _saw_bench(self, c, t):
        T = self.T
        for hx in HORSES:                                         # sawhorses
            c.line(hx - 34, G, hx - 8, BEAM_Y[1], TRUNK * 0.9, 9)
            c.line(hx + 34, G, hx + 8, BEAM_Y[1], TRUNK * 0.9, 9)
            rect(c, hx - 40, BEAM_Y[1], hx + 40, BEAM_Y[1] + 10, TRUNK)
        rect(c, STOP_X - 14, BEAM_Y[0] - 16, STOP_X - 4, BEAM_Y[1], IRON * 1.3)       # stop block
        left = self.beam_left(t)
        cut = self.pieces_cut(t)
        taken = self.pieces_taken(t)
        right = STOP_X + 8 * PIECE - PIECE * (0 if t < T["cut"] else 0)
        # the beam: what's left of it after the taken pieces, pushed to the stop
        b0 = left if taken < 8 else None
        if b0 is not None:
            b1 = b0 + (8 - taken) * PIECE
            rect(c, b0, BEAM_Y[0], b1, BEAM_Y[1], PLANK * 0.92)
            c.line(b0, BEAM_Y[0], b1, BEAM_Y[0], PLANK * 1.2, 2)
            for k in range(1, 8 - taken):                         # pencil marks every paddle length
                mx = b0 + k * PIECE
                c.line(mx, BEAM_Y[0] - 4, mx, BEAM_Y[0] + 8, np.array([40, 34, 30]), 2)
            if cut > taken:                                       # the kerf of the cut just made
                c.line(b0 + PIECE, BEAM_Y[0], b0 + PIECE, BEAM_Y[1], np.array([28, 22, 20]), 3)
        _ = right

    def _stack(self, c, t):
        for i in range(8):
            st = self.piece_state(i, t)
            if st[0] == "beam":
                continue
            if st[0] == "stack":
                k = 7 - i
                if t >= self.paddle_times(k)[0]:
                    continue
            c.polygon(paddle_poly(st[1], st[2], st[3]), PLANK * 1.05)
            c.polyline(paddle_poly(st[1], st[2], st[3]), PR.WOOD_DARK, 2, closed=True)

    def _carried(self, c, kind, t):
        T = self.T
        if kind == "tentacles":
            for k in range(8):
                t_take, t_in, _, _ = self.paddle_times(k)
                if t_take <= t < t_in:
                    x, y, a = self.paddle_carry(k, t)
                    c.polygon(paddle_poly(x, y, a), PLANK * 1.05)
                    c.polyline(paddle_poly(x, y, a), PR.WOOD_DARK, 2, closed=True)
        if kind == "springs" and self.carry.get("springs") is not None:
            sp = self.m("springs")
            top = sp.y - 310 * sp.k
            rect(c, sp.x - 12, top - 290, sp.x + 12, top, TRUNK * 1.05)
            for sxp in (-1, 1):
                c.line(sp.x + sxp * 50 * sp.k, sp.y - 190 * sp.k, sp.x + sxp * 12, top - 30, sp.color * 0.8, 10 * sp.k)


def P_ok(omega):
    return omega > 0.3


# ====================================================================== HOUSES (the forest workshop)

ROLL_Y = G - 130.0                 # roller line / bench top: a low line, so the little Keepers can work at it
BENCH = (3130.0, 3540.0)
RACK = (2770.0, 3120.0)            # boards wait on a rack left of the bench
SAW_X = 3445.0                     # Twigs' cut line at the right end of the bench (the board is fed to it)
PIECE_W = 95.0
ST = [3660.0, 4300.0, 5000.0, 5700.0, 6250.0]       # kit, drill, build, paint, unload
KIT_IN = ST[2] - 170.0             # the kit waits beside the build spot
ROLLERS = (3570.0, 6340.0)
WAGON = (6470.0, 7470.0)
PRESS_TOP = G - 470.0
NAIL_REST = PRESS_TOP + 74.0       # nail tips with the press up
DRILL_POST = 4410.0
PEDAL_X = 4190.0
HEAD_Y = G - 430.0


def wagon_slots():
    """Centres of the six houses on the wagon, evenly spaced (same gap between neighbours)."""
    ws = [sp.w + 32 for sp in PR.SPECS]                     # body + eaves
    gap = (WAGON[1] - WAGON[0] - 60 - sum(ws)) / 5
    xs, x = [], WAGON[0] + 30
    for w in ws:
        xs.append(x + w / 2)
        x += w + gap
    return xs, gap


class HousesAct(KeeperAct):
    """The forest workshop, run by the water wheel: an indexed line of four stations (see module docstring)."""
    name = "houses"
    joins_prev = True                  # same world as WHEEL: no fade, the camera glides on into the shed
    names = (-1.0, -0.5)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.mill = scene.__dict__.setdefault("mill", Mill())
        self.Tc, self.IDX = P.get("cycle", 11.0), 1.6
        self.t_line = P.get("intro", 7.0)
        self.n = len(PR.SPECS)
        self.t_end = self.t_line + (self.n + 4) * self.Tc
        self.dur = self.t_end + P.get("finale", 10.0)
        self.slots, self.gap = wagon_slots()
        self.rot0 = None
        self.stats = {}
        self._check_alignment()

    def _check_alignment(self):
        xs, gap = self.slots, self.gap
        ws = [sp.w + 32 for sp in PR.SPECS]
        gaps = [(xs[i + 1] - ws[i + 1] / 2) - (xs[i] + ws[i] / 2) for i in range(len(xs) - 1)]
        self.stats["houses_even_gaps"] = bool(max(gaps) - min(gaps) < 0.5)

    # ----- the line's clock -----

    def cyc(self, t):
        """(cycle index, time into it) of the line; cycle < 0 before it starts."""
        if t < self.t_line:
            return -1, t - self.t_line
        c = int((t - self.t_line) // self.Tc)
        return c, t - self.t_line - c * self.Tc

    def work(self, q, j):
        """Start of the work window for house j at station q."""
        return self.t_line + (j + q) * self.Tc + self.IDX

    def at(self, j, t):
        """(stage q, time into its work window) of house j; work time < 0 while it is indexing in."""
        c, ph = self.cyc(t)
        q = c - j
        return q, ph - self.IDX

    def spot(self, q):
        return {0: ST[0], 1: ST[1], 2: KIT_IN, 3: ST[3], 4: ST[4]}[q]

    def item_x(self, j, t):
        """x of house j on the line (kit or house)."""
        q, w = self.at(j, t)
        if q < 0:
            return None
        if w < 0 and q > 0:                                  # indexing: rollers carry it from the last spot
            u = smootherstep((w + self.IDX) / self.IDX)
            prev = ST[2] if q == 3 else self.spot(q - 1)
            return lerp(prev, self.spot(q), u)
        if q == 2 and self.asm_started(j, t):
            return ST[2]
        if q >= 3:
            return self.spot(min(q, 4))
        return self.spot(q)

    # ----- station timings (seconds into the work window) -----

    PANEL_T = {"back": (0.3, 1.3), "left": (1.3, 2.1), "right": (1.9, 2.7), "front": (2.8, 3.8),
               "roofL": (5.2, 6.2), "roofR": (5.8, 6.8)}
    BOUNCE = (3.45, 6.95)              # Springs takes off for the two presses
    CUTS = (1.6, 3.7, 5.8)             # Twigs' three cuts (the 4th piece is the end of the board)

    def asm_started(self, j, t):
        q, w = self.at(j, t)
        return q > 2 or (q == 2 and w >= self.PANEL_T["back"][0])

    def parts(self, j, t):
        q, w = self.at(j, t)
        if q > 2:
            return None
        return {k: smootherstep(seg(w, a, b)) for k, (a, b) in self.PANEL_T.items()}

    def press_amount(self, w, jump):
        """Press plate travel 0..1 when Springs lands at w = take-off + flight time."""
        out = 0.0
        for b in self.BOUNCE:
            land = b + jump.dur
            if land <= w < land + 0.18:
                out = smoothstep((w - land) / 0.18)
            elif land + 0.18 <= w < land + 0.32:
                out = 1.0
            elif land + 0.32 <= w < land + 0.85:
                out = 1 - smoothstep((w - land - 0.32) / 0.53)
        return out

    def springs_jump(self):
        return Jump(ST[2], 0.0, ST[2], 0.0, apex=95)

    def pieces(self, w):
        """Pieces cut off the board so far in this work window (0..4)."""
        n = sum(1 for c0 in self.CUTS if w >= c0 + 0.9)
        return n + (1 if w >= self.CUTS[-1] + 2.3 else 0)

    def board(self, w):
        """(left, right) of the board on the bench; it slides in from the rack, then is fed one piece length
        to the right after each cut, so the cut line stays at SAW_X."""
        L = 4 * PIECE_W
        x_r = SAW_X + PIECE_W
        if w < 0:
            u = smootherstep((w + self.IDX) / self.IDX)
            return lerp(RACK[1] - L + 20, x_r - L, u) if u > 0 else None, None
        cut = sum(1 for c0 in self.CUTS if w >= c0 + 0.9)
        feed = 0.0
        for k, c0 in enumerate(self.CUTS):
            if w >= c0 + 1.1:
                feed = (k + 1) * PIECE_W * (1.0 if w >= c0 + 1.7 or k < cut - 1 else
                                             smootherstep(seg(w, c0 + 1.1, c0 + 1.7)) + k / (k + 1) * 0)
        left = x_r - L + min(feed, 3 * PIECE_W)
        right = x_r - cut * PIECE_W + min(feed, 3 * PIECE_W)
        if w >= self.CUTS[-1] + 2.3:
            return None, None
        return left, min(right, x_r)

    def drill_feed(self, w):
        return smoothstep(seg(w, 1.0, 4.0)) * (1 - smoothstep(seg(w, 4.3, 5.3)))

    def drilled(self, j, t):
        q, w = self.at(j, t)
        return q > 1 or (q == 1 and w >= 3.6)

    def paint(self, j, t):
        q, w = self.at(j, t)
        if q < 3:
            return 0.0
        if q > 3:
            return 1.0
        return smootherstep(seg(w, 0.5, 6.5))

    def hung(self, j, t):
        q, w = self.at(j, t)
        return q > 3 or (q == 3 and w >= 8.2)

    def carry(self, j, t):
        """House j after the paint stand: (x, y_bottom) - on the rollers, in Wheels' claws, or on the wagon."""
        q, w = self.at(j, t)
        tx = self.slots[j]
        if q < 4 or (q == 4 and w < 0.6):
            return self.item_x(j, t), ROLL_Y
        if q == 4 and w < 1.4:
            return ST[4], lerp(ROLL_Y, ROLL_Y - 30, smoothstep(seg(w, 0.6, 1.4)))
        if q == 4 and w < 5.2:
            u = smootherstep(seg(w, 1.4, 5.2))
            return lerp(ST[4], tx, u), lerp(ROLL_Y - 30, G - 100, u)
        if q == 4 and w < 6.0:
            return tx, lerp(G - 100, G - 70, smoothstep(seg(w, 5.2, 6.0)))
        return tx, G - 70

    # ----- camera -----

    def target(self, t):
        H = self.s.h

        def cam(x, z, gf):
            """camera at x, zoom z, with the floor at fraction gf of the screen height"""
            return x, G - (gf - 0.5) * H / z, z
        keys = {0: (3420, 1.45, 0.87), 1: (4170, 1.4, 0.87), 2: (4930, 1.2, 0.88), 3: (5660, 1.35, 0.87),
                4: (4800, 0.62, 0.86), 5: (4250, 1.4, 0.87), 6: (4930, 1.2, 0.88), 7: (4990, 1.2, 0.88),
                8: (5660, 1.3, 0.87), 9: (6420, 1.0, 0.86)}
        c, ph = self.cyc(t)
        if c < 0:
            u = smootherstep(seg(t, 0, self.t_line - 0.5))
            x0, y0, z0 = cam(3500, 0.78, 0.8)
            x1, y1, z1 = cam(*keys[0])
            return lerp(x0, x1, u), lerp(y0, y1, u), lerp(z0, z1, u)
        if c >= self.n + 4:
            xs = self.slots
            u = smootherstep(seg(t, self.t_end, self.t_end + 3.0))
            a, b = cam(*keys[9]), cam(WAGON[0] + 700, 0.8, 0.84)
            return lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)
        b = cam(*keys[min(c, 9)])
        if c == 0:
            return b
        a = cam(*keys[min(c - 1, 9)])
        u = smootherstep(seg(ph, 0.0, 2.2))
        return lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)

    # ----- update -----

    def update(self, t, dt):
        M = self.mill
        if self.rot0 is None:
            self.rot0 = M.rot
        M.wheel_in, M.belt, M.belt_end = True, 1.0, None
        M.omega = 1.25
        M.rot = self.rot0 - 1.25 * t
        M.shaft_rot = M.rot * AXLE_R / SHAFT_R
        M.gate_lift, M.gate, M.inlet = 1.0, 1.0, 1.0
        M.race_front, M.water_front = GATE_X, RACE[1] - 30
        M.paddles = set(range(8))
        M.legs, M.bearing = (1.0, 1.0), 1.0
        self.reach = {}
        self.held = {}
        self._twigs(t, dt)
        self._digs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._wheels(t, dt)
        self._particles(t)
        self._sounds(t)
        self.stats["houses_built"] = sum(1 for j in range(self.n) if self.at(j, t)[0] > 4 or
                                         (self.at(j, t)[0] == 4 and self.at(j, t)[1] >= 6.0))

    def _intro(self, kind, x_from, x_to, t, y_from=None, y_to=None):
        x, y, mv = path([(0.0, x_from, y_from if y_from is not None else G),
                         (self.t_line - 0.6, x_to, y_to if y_to is not None else G)], t)
        return x, y, mv

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        home = SAW_X - 82
        c, ph = self.cyc(t)
        x = home
        if c < 0:
            x, _, _ = self._intro("teeth", 3360.0, home, t)
        elif c < self.n:
            w = ph - self.IDX
            ty = BENCH_TOP - 70
            for c0 in self.CUTS:
                if c0 - 0.1 <= w < c0 + 1.0:
                    u = (w - c0) / 0.9
                    if u < 0.1:
                        ty = lerp(BENCH_TOP - 70, BENCH_TOP - 22, max(0.0, u) / 0.1)
                    elif u < 0.6:
                        ty = lerp(BENCH_TOP - 22, BENCH_TOP + 40, smoothstep((u - 0.1) / 0.5))
                    else:
                        ty = lerp(BENCH_TOP + 40, BENCH_TOP - 70, smoothstep(min(1.0, (u - 0.6) / 0.4)))
                    m.saw_run = smoothstep(seg(u, 0.0, 0.08)) * (1 - smoothstep(seg(u, 0.55, 0.75)))
            m.x = m.x or home
            x = saw_to(m, t, SAW_X, ty, sx=1)
        else:
            u = smootherstep(seg(t, self.t_line + self.n * self.Tc, self.t_line + self.n * self.Tc + 4.0))
            x = lerp(home, 3900.0, u)
            if t >= self.t_end:
                x, _, _ = path([(self.t_end, 3900.0, G), (self.t_end + 4.0, WAGON[1] + 330, G)], t)
        m.saw_spin += dt * 38 * m.saw_run
        self.place(m, x, t, dt)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        m.dig = 0.0
        dy = 0.0
        c, ph = self.cyc(t)
        x = PEDAL_X - 40
        if c < 0:
            x, _, _ = self._intro("digger", 3150.0, x, t)
        elif 1 <= c <= self.n:
            w = ph - self.IDX
            f = self.drill_feed(w)
            if 1.0 <= w < 4.3:                               # treads the pedal in little stomps
                m.dig = 0.4 + 0.3 * math.sin(w * 9)
                dy = -abs(math.sin(w * 4.5)) * 10
            if 5.6 <= w < 8.6:                               # sweeps the sawdust out from under the drill
                x = lerp(PEDAL_X - 40, ST[1] - 10, smoothstep(seg(w, 5.6, 6.4)) * (1 - smoothstep(seg(w, 7.8, 8.6))))
                m.dig = 0.5 + 0.5 * math.sin(w * 14) if 6.4 <= w < 7.8 else 0.0
            _ = f
        elif c > self.n:
            if t >= self.t_end:
                x, _, _ = path([(self.t_end, x, G), (self.t_end + 4.0, WAGON[1] + 820, G)], t)
        self.place(m, x, t, dt, dy=dy)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        x = ST[2] - 230
        reach = []
        c, ph = self.cyc(t)
        if c < 0:
            x, _, _ = self._intro("tentacles", 3780.0, x, t)
        else:
            j = c - 2
            if 0 <= j < self.n:
                sp = PR.SPECS[j]
                w = ph - self.IDX
                src = (KIT_IN, ROLL_Y - 30)
                for name, (a, b) in self.PANEL_T.items():
                    if a - 0.15 <= w < b + 0.1:
                        u = smootherstep(seg(w, a, b))
                        reach.append(PR.panel_grip(sp, ST[2], ROLL_Y, name, u, src=src))
                # holds the box square while Springs presses: two tentacles on the side panels
                for b0 in self.BOUNCE:
                    land = b0 + self.springs_jump().dur
                    if b0 - 0.3 <= w < land + 0.9:
                        reach = [(ST[2] - sp.w / 2 - 4, ROLL_Y - sp.h * 0.45),
                                 (ST[2] + sp.w / 2 + 4, ROLL_Y - sp.h * 0.45)]
            if t >= self.t_end:
                x, _, _ = path([(self.t_end, x, G), (self.t_end + 4.0, WAGON[1] + 160, G)], t)
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        m.spring = 0.0
        c, ph = self.cyc(t)
        y, dy = None, 0.0
        step_y = self.step_y(t)
        if c < 0:
            if t < self.t_line - 2.0:
                x, _, mv = path([(0.0, 3560.0, G), (self.t_line - 2.0, ST[2] - 140, G)], t)
                if mv:
                    ph2 = (t * 2.8) % 1.0
                    dy = -4 * 55 * ph2 * (1 - ph2)
            else:
                j = Jump(ST[2] - 140, G, ST[2], step_y, apex=70)
                tt = t - (self.t_line - 2.0)
                if tt < j.dur:
                    x, y = j.at(tt)
                else:
                    x, y = ST[2], step_y
            self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)
            return
        if t < self.t_end:
            x, y = ST[2], step_y
            w = ph - self.IDX
            jp = self.springs_jump()
            if 2 <= c < self.n + 2:
                for b in self.BOUNCE:
                    if b <= w < b + jp.dur:
                        dy = jp.at(w - b)[1]
                    if abs(w - b) < 0.1 or abs(w - b - jp.dur) < 0.12:
                        m.spring = 0.8
            self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)
            return
        j = Jump(ST[2], step_y, ST[2] + 180, G, apex=60)
        tt = t - self.t_end
        if tt < j.dur:
            x, y = j.at(tt)
        else:
            x, lift, sq = hops(ST[2] + 180, WAGON[1] + 500, self.t_end + j.dur + 0.3, self.t_end + 5.0, t,
                               apex=60, step=170)
            y, dy = G, -lift
            m.spring = sq
        self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)

    def step_y(self, t):
        """y of the press's top step (where Springs stands) - it moves down with the plate."""
        c, ph = self.cyc(t)
        j = c - 2
        if c < 2 or j >= self.n:
            return PRESS_TOP - 56
        sp = PR.SPECS[j]
        w = ph - self.IDX
        return PRESS_TOP - 56 + self.press_amount(w, self.springs_jump()) * self.stroke(sp, w)

    def stroke(self, sp, w):
        """Plate travel for this press: first to the top of the box, then (roof on) to the ridge."""
        top = ROLL_Y - sp.h if w < self.BOUNCE[1] else ROLL_Y - sp.h - sp.roof
        return max(0.0, top - NAIL_REST)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        c, ph = self.cyc(t)
        x, y = ST[3] + 140, G - 330
        self.brush = None
        if c < 0:
            x, y, _ = self._intro("lantern", 3250.0, x, t, G - 380, y)
        else:
            j = c - 3
            if 0 <= j < self.n:
                sp = PR.SPECS[j]
                w = ph - self.IDX
                p = self.paint(j, t)
                if 0.3 <= w < 6.7:
                    # floats beside the house and paints it with one tendril, side to side, roof first
                    top = ROLL_Y - sp.h - sp.roof
                    by = top + (sp.h + sp.roof) * p
                    half = sp.w / 2 - 6 if by > ROLL_Y - sp.h else (sp.w / 2 + 10) * (by - top) / sp.roof
                    bx = ST[3] + half * math.sin(w * 5.0)
                    self.brush = (bx, by, sp.color)
                    x, y = ST[3] + sp.w / 2 + 120, min(G - 40, by + 150)
                elif 7.0 <= w < 8.4:
                    lx, ly = PR.lamp_point(sp, ST[3], ROLL_Y)
                    x, y = lx + 50, ly - 30
                    self.brush = None
            if t >= self.t_end:
                x, y, _ = path([(self.t_end, x, y), (self.t_end + 3.0, WAGON[1] + 660, G - 60)], t)
        self.place(m, x, t, dt, y=y)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        m.punch = 0.0
        c, ph = self.cyc(t)
        x = ST[4] + 10
        if c < 0:
            x, _, _ = self._intro("wheels", 3600.0, x, t)
        else:
            j = c - 4
            if 0 <= j < self.n:
                w = ph - self.IDX
                hx, hy = self.carry(j, t)
                if 0.4 <= w < 6.2:
                    x = hx
                    m.punch = 0.3 if w < 5.4 else 0.0
                elif w >= 6.2:
                    x = lerp(self.slots[j], ST[4] + 10, smootherstep(seg(w, 6.2, 9.2)))
            if t >= self.t_end:
                x, _, _ = path([(self.t_end, x, G), (self.t_end + 3.0, WAGON[0] - 150, G)], t)
        self.place(m, x, t, dt)

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        c, ph = self.cyc(t)
        w = ph - self.IDX
        tw = self.m("teeth")
        if tw is not None and tw.saw_run > 0.5 and P.rng.uniform() < 0.9:
            P.burst(SAW_X, BENCH_TOP + 10, 2, SAWDUST, 300, 0.6, 3.5, g=900, spread=0.6, direction=math.pi * 0.55)
        if 1 <= c <= self.n and 2.6 < w < 4.2 and P.rng.uniform() < 0.7:
            P.burst(ST[1] + 20, ROLL_Y - 40, 2, SAWDUST, 220, 0.5, 3, g=900, spread=1.0, direction=-math.pi * 0.1)
        if self.brush is not None and P.rng.uniform() < 0.12:
            bx, by, col = self.brush
            P.burst(bx, by + 4, 1, col, 40, 0.5, 3, g=1400, spread=0.3, direction=math.pi / 2)

    def _sounds(self, t):
        s = self.s
        for c in range(self.n + 5):
            t0 = self.t_line + c * self.Tc
            if self.crossed(t0 + 0.05):
                self.fx(t, "servo", self.IDX, 0.16, 4800, ROLL_Y)
            if self.crossed(t0 + self.IDX - 0.05):
                self.hit(t, "clunk", 48, 0.22, 4800, ROLL_Y)
            w0 = t0 + self.IDX
            if c < self.n:
                for k, c0 in enumerate(self.CUTS):
                    if self.crossed(w0 + c0):
                        self.fx(t, "saw", 0.7, 0.16, SAW_X, BENCH_TOP)
                    if self.crossed(w0 + c0 + 1.2):
                        self.hit(t, "clack", s.note(k + c, 0), 0.26, ST[0], ROLL_Y)
            if 1 <= c <= self.n:
                if self.crossed(w0 + 1.0):
                    self.fx(t, "saw", 3.0, 0.1, ST[1], ROLL_Y - 60)
                if self.crossed(w0 + 4.0):
                    self.hit(t, "bloop", 64, 0.3, ST[1], ROLL_Y)
            j = c - 2
            if 0 <= j < self.n:
                for k, (name, (a, b)) in enumerate(self.PANEL_T.items()):
                    if self.crossed(w0 + b):
                        self.hit(t, "clack", s.note(k, 0), 0.28, ST[2], ROLL_Y - 100)
                jp = self.springs_jump()
                for i, b in enumerate(self.BOUNCE):
                    if self.crossed(w0 + b):
                        self.hit(t, "boing", s.note(i * 2 + j, -1), 0.4, ST[2], PRESS_TOP)
                    if self.crossed(w0 + b + jp.dur + 0.18):
                        self.hit(t, "thud", 43, 0.3, ST[2], ROLL_Y - 150)
                        for k in range(4):
                            self.hit(t + 0.02 * k, "clack", 60 + (0, 4, 7, 12)[k], 0.14, ST[2], ROLL_Y - 150)
            j = c - 3
            if 0 <= j < self.n:
                for k in range(6):
                    if self.crossed(w0 + 0.6 + k):
                        self.fx(t, "slide", 0.5, 0.08, ST[3], ROLL_Y - 100)
                if self.crossed(w0 + 8.2):
                    self.hit(t, "music_box", 84, 0.18, ST[3], ROLL_Y - 100)
            j = c - 4
            if 0 <= j < self.n:
                if self.crossed(w0 + 0.6):
                    self.fx(t, "servo", 0.8, 0.14, ST[4], ROLL_Y)
                if self.crossed(w0 + 6.0):
                    self.hit(t, "clunk", 50, 0.3, self.slots[j], G - 70)
                    self.hit(t + 0.15, "chime", (72, 74, 76, 79, 81, 84)[j], 0.3, self.slots[j], G - 200)
        if self.crossed(self.t_end + 2.5):
            for q, kind in enumerate(("wheels", "tentacles", "teeth", "springs", "lantern", "digger")):
                self.say(t + q * 0.2, kind, "cheer", (self.slots[0] + self.slots[-1]) / 2, G - 200, 0.45)

    # ----- drawing -----

    def draw(self, c, t):
        s, M = self.s, self.mill
        self.night.draw(s, c, t)
        M.draw_shed(c, s, t)
        M.draw_ground(c, s, t)
        M.draw_belt(c, t)
        M.draw_wheel(c, t)
        for x, txt in ((3330.0, "CUT"), (ST[1] - 170, "DRILL"), (ST[2] + 10, "BUILD"), (ST[3], "PAINT")):
            PR.hanging_sign(c, x, ROOF_Y + 130, txt)
        self._machines(c, t)
        self._line(c, t)
        PR.flat_wagon(c, WAGON[0], WAGON[1], G)
        for j in range(self.n):
            q, w = self.at(j, t)
            if q >= 4 and not (q == 4 and 0.6 <= w < 6.0):
                hx, hy = self.carry(j, t)
                PR.draw_house(c, s, PR.SPECS[j], hx, hy, t, paint=1.0, hanger=True)
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 120, k=0.9)
        self.draw_monsters(c, t, before=lambda kind: self._carried(c, kind, t))
        if self.brush is not None:
            bx, by, col = self.brush
            gl = self.m("lantern")
            k = gl.k
            root = (gl.x - 50 * k, gl.y - 260 * k + 40 * k)
            reach_tentacle(c, root[0], root[1], bx + 10, by - 16, 15 * k, np.asarray(gl.color) * 0.8, t, 0.4, -1, 0.6,
                           segs=20)
            c.polygon([(bx - 2, by - 22), (bx + 16, by - 18), (bx + 8, by + 2), (bx - 2, by + 2)], col * 0.95)
        M.draw_water(c, s, t)
        M.draw_shed(c, s, t, front=True)
        # belts from the line shaft down to the drill and to the roller drive
        PR.belt(c, (ST[1], SHAFT_Y), 22, (ST[1], HEAD_Y - 30), 22, -M.shaft_rot * 22)
        PR.pulley(c, ST[1], SHAFT_Y, 22, M.shaft_rot)
        PR.belt(c, (ROLLERS[0] + 40, SHAFT_Y), 22, (ROLLERS[0] + 40, ROLL_Y + 30), 18, -M.shaft_rot * 22)
        PR.pulley(c, ROLLERS[0] + 40, SHAFT_Y, 22, M.shaft_rot)

    def roller_rot(self, t):
        c, ph = self.cyc(t)
        k = max(0, c) + (smootherstep(min(1.0, ph / self.IDX)) if c >= 0 else 0.0)
        return k * 700 / 8.0

    def _machines(self, c, t):
        s, M = self.s, self.mill
        cyc, ph = self.cyc(t)
        w = ph - self.IDX
        # rack of boards + Twigs' bench
        left = max(0, self.n - max(0, cyc + (1 if cyc >= 0 and ph >= 0.0 else 0)))
        for k in range(left):
            rect(c, RACK[0] + 6, BENCH_TOP - 16 - k * 15, RACK[1] - 6, BENCH_TOP - 3 - k * 15, PLANK * (0.86 + 0.06 * (k % 2)))
        for lx in (RACK[0] + 20, RACK[1] - 20):
            rect(c, lx - 7, BENCH_TOP, lx + 7, G, TRUNK * 0.8)
        PR.bench(c, BENCH[0], BENCH[1], BENCH_TOP, G)
        if 0 <= cyc < self.n:
            b0, b1 = self.board(w)
            if b0 is not None:
                b1 = b1 if b1 is not None else b0 + 4 * PIECE_W
                rect(c, b0, BENCH_TOP - 16, b1, BENCH_TOP, PLANK * 0.95)
                c.line(b0, BENCH_TOP - 16, b1, BENCH_TOP - 16, PLANK * 1.2, 2)
                for k in range(1, 4):
                    mx = b1 - k * PIECE_W
                    if mx > b0 + 5:
                        c.line(mx, BENCH_TOP - 20, mx, BENCH_TOP - 8, np.array([40, 34, 30]), 2)
            # the cut-off piece slides along the bench into the kit
            for k, c0 in enumerate(self.CUTS + (self.CUTS[-1] + 1.4,)):
                u = seg(w, c0 + 0.8, c0 + 1.3)
                if 0 < u < 1:
                    px = lerp(SAW_X + PIECE_W / 2, ST[0], smoothstep(u))
                    py = lerp(BENCH_TOP - 8, ROLL_Y - 12 - 9 * (k * 1.5), smoothstep(u))
                    rect(c, px - PIECE_W / 2, py - 8, px + PIECE_W / 2, py + 8, PLANK)
        PR.sawdust_pile(c, SAW_X + 30, G, min(1.0, max(0.0, (t - self.t_line) / (self.n * self.Tc))))
        # drill
        f = self.drill_feed(w) if 1 <= cyc <= self.n else 0.0
        j = cyc - 1
        r = PR.SPECS[j].hole_r if 0 <= j < self.n else 15
        PR.drill_over(c, ST[1], HEAD_Y, ROLL_Y - 6 * 9 - 2, f, M.shaft_rot, r, DRILL_POST)
        PR.pedal(c, PEDAL_X, G, f)
        # press
        jj = cyc - 2
        if 0 <= jj < self.n:
            sp = PR.SPECS[jj]
            pr = self.press_amount(w, self.springs_jump())
            PR.nail_press(c, ST[2], PRESS_TOP, ROLL_Y, pr, stroke=self.stroke(sp, w))
        else:
            PR.nail_press(c, ST[2], PRESS_TOP, ROLL_Y, 0.0)

    def _line(self, c, t):
        s = self.s
        PR.rollers(c, ROLLERS[0], ROLLERS[1], ROLL_Y, G, self.roller_rot(t))
        for j in range(self.n):
            q, w = self.at(j, t)
            if q < 0 or q > 4:
                continue
            sp = PR.SPECS[j]
            x = self.item_x(j, t)
            if q == 0:
                n = 0 if w < 0 else min(6, int(math.ceil(self.pieces(w) * 1.5)))
                if n:
                    PR.draw_kit(c, sp, x, ROLL_Y, n)
            elif q == 1 or (q == 2 and not self.asm_started(j, t)):
                PR.draw_kit(c, sp, x, ROLL_Y, 6)
                if self.drilled(j, t):                         # the hole shows in the top board's edge
                    c.line(x - sp.hole_r, ROLL_Y - 6 * 9 + 2, x + sp.hole_r, ROLL_Y - 6 * 9 + 2, PR.INSIDE, 3)
            elif q == 2:
                parts = self.parts(j, t)
                left = sum(1 for v in parts.values() if v <= 0)
                if left:
                    PR.draw_kit(c, sp, KIT_IN, ROLL_Y, left)
                PR.draw_house(c, s, sp, ST[2], ROLL_Y, t, parts=parts, paint=0.0, src=(KIT_IN, ROLL_Y - 30))
            elif q == 3:
                PR.draw_house(c, s, sp, x, ROLL_Y, t, paint=self.paint(j, t), hanger=self.hung(j, t))
            elif q == 4 and w < 0.6:
                PR.draw_house(c, s, sp, x, ROLL_Y, t, paint=1.0)
        # a plug drops out from under the drill once the hole saw is through
        cyc, ph = self.cyc(t)
        w = ph - self.IDX
        if 1 <= cyc <= self.n and 3.8 <= w < 5.0:
            j = cyc - 1
            r = PR.SPECS[j].hole_r
            u = (w - 3.8) / 1.2
            px, py = ST[1] + 60 + 120 * u, ROLL_Y - 54 + 0.5 * GRAVITY * (u * 1.2) ** 2 * 0.25
            if py < G - 6:
                c.polygon(ellipse(px, py, r, 5, 14), PLANK * 1.1)
            else:
                c.polygon(ellipse(px, G - 5, r, 5, 14), PLANK * 1.1)

    def _carried(self, c, kind, t):
        if kind != "wheels":
            return
        cyc, ph = self.cyc(t)
        j = cyc - 4
        if 0 <= j < self.n:
            q, w = self.at(j, t)
            if 0.6 <= w < 6.0:
                hx, hy = self.carry(j, t)
                PR.draw_house(c, self.s, PR.SPECS[j], hx, hy, t, paint=1.0)

    def draw_monsters(self, c, t, kinds=None, before=None):
        # Wheels carries a house in front of him: draw him first, then the house over his body
        super().draw_monsters(c, t, kinds=[k for k in self.poses if k != "wheels"] if kinds is None else kinds,
                              before=before)
        if kinds is None and "wheels" in self.poses:
            super().draw_monsters(c, t, kinds=["wheels"])
            self._carried(c, "wheels", t)


BENCH_TOP = ROLL_Y


# ====================================================================== DELIVER

POSTS = [2080.0, 2310.0, 2540.0, 2770.0]   # birdhouse posts, evenly spaced right of the treehouse ladder
POST_TOP = G - 330.0
HEDGE_X, BUNNY_X = 3090.0, 3440.0
PARK = (3820.0, 4820.0)                   # where the wagon stands while it is unloaded
BUNDLE_X = 2950.0                         # Hans drops the post bundle here
GOLDFINCH = (np.array([200, 170, 60]), np.array([236, 214, 120]))
WREN = (np.array([140, 104, 74]), np.array([196, 160, 120]))
BIRD_COLS = [PR.ROBIN, PR.BLUE_TIT, GOLDFINCH, WREN]
# where the Keepers wait when they are not working (left of the posts, clear of the houses)
IDLE = {"springs": 1640.0, "tentacles": 1500.0, "digger": 1800.0, "teeth": 1950.0, "wheels": 2000.0}


class DeliverAct(KeeperAct):
    """Back at the treehouse: posts for the birdhouses, every house to its place, lamps, the animals move in."""
    name = "deliver"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.slots, _ = wagon_slots()
        d = dict(arrive=8.0, posts=17.0, level=5.0, birdhouses=27.0, ground=9.0, lamps=8.0, movein=26.0, finale=12.0)
        d.update(P.get("durations", {}))
        T, t = {}, 0.0
        for k in ("arrive", "posts", "level", "birdhouses", "ground", "lamps", "movein", "finale"):
            T[k] = t
            t += d[k]
        self.T, self.d, self.dur = T, d, t
        # posts: Digs digs, Hans stands each post in its hole, Springs stomps it down from the top
        self.hole_t = [T["posts"] + 0.4 + 2.8 * k for k in range(4)]            # start digging
        self.stand_t = [h + 2.6 for h in self.hole_t]                             # Hans starts lifting the post
        self._plan_springs()
        # birdhouses: Wheels drives each from the wagon to the foot of its post, Hans lifts it on top
        self.bh_cyc = d["birdhouses"] / 4
        # houses in their final places
        self.home = [(POSTS[j], POST_TOP) for j in range(4)] + [(HEDGE_X, G), (BUNNY_X, G)]
        self.stats = {}
        self._check_alignment()

    def _check_alignment(self):
        gaps = [POSTS[i + 1] - POSTS[i] for i in range(3)]
        tops = [self.post_top(k, self.dur) for k in range(4)]
        self.stats["posts_even"] = bool(max(gaps) - min(gaps) < 0.5 and max(tops) - min(tops) < 0.5)

    # ----- the posts -----

    def _plan_springs(self):
        segs = []
        self.stomp_land = {k: [] for k in range(4)}
        t = self.stand_t[0] + 2.2
        x0 = POSTS[0] - 140
        top0 = POST_TOP - 80
        j = Jump(x0, G, POSTS[0], top0, apex=90)
        segs.append((t, t + j.dur, j))
        t += j.dur
        for k in range(4):
            if k > 0:
                t = max(t, self.stand_t[k] + 2.2)
                j = Jump(POSTS[k - 1], POST_TOP, POSTS[k], POST_TOP - 80, apex=90)
                segs.append((t, t + j.dur, j))
                t += j.dur
            for q in range(2):                                     # two stomps drive it 40 each
                y0 = POST_TOP - 80 + 40 * q
                st = Jump(POSTS[k], y0, POSTS[k], y0 + 40, apex=80)
                t += 0.12
                segs.append((t, t + st.dur, st))
                t += st.dur
                self.stomp_land[k].append(t)
        j = Jump(POSTS[3], POST_TOP, POSTS[3] + 170, G, apex=70)
        t += 0.3
        segs.append((t, t + j.dur, j))
        self.sp_segs = segs
        self.sp_done = t + j.dur

    def springs_at(self, t):
        last = None
        for t0, t1, j in self.sp_segs:
            if t0 <= t < t1:
                return j.at(t - t0)
            if t >= t1:
                last = (j.x1, j.y1)
        return last

    def post_top(self, k, t):
        """Top of post k (None before Hans stands it up)."""
        if t < self.stand_t[k]:
            return None
        n = sum(1 for tl in self.stomp_land[k] if t >= tl)
        return POST_TOP - 80 + 40 * n

    def post_state(self, k, t):
        """('bundle'|'carry'|'in', x, top y, angle)"""
        s0 = self.stand_t[k]
        if t < s0:
            return "bundle", BUNDLE_X, G - 14 - 26 * k, math.pi / 2
        if t < s0 + 2.0:
            u = smootherstep(seg(t, s0, s0 + 2.0))
            x, y = bez((BUNDLE_X, G - 200), ((BUNDLE_X + POSTS[k]) / 2, G - 520), (POSTS[k], POST_TOP - 80), u)
            return "carry", x, y, lerp(math.pi / 2, 0.0, smoothstep(seg(u, 0.0, 0.6)))
        return "in", POSTS[k], self.post_top(k, t), 0.0

    # ----- houses -----

    def wagon_x0(self, t):
        u = smootherstep(seg(t, 0.0, self.T["arrive"] - 0.6))
        return lerp(5900.0, PARK[0], u)

    def bh_times(self, j):
        """Birdhouse j: (Wheels lifts it off the wagon, at the post foot, Hans has it on the post)."""
        t0 = self.T["birdhouses"] + j * self.bh_cyc
        return t0 + 0.2, t0 + 3.0, t0 + 4.8

    def ground_times(self, j):
        """Hedgehog (j=4) / bunny (j=5) house: (lift, set down)."""
        t0 = self.T["ground"] + (j - 4) * 4.4
        return t0 + 0.2, t0 + 3.4

    def house_pos(self, j, t):
        """Where house j is: (x, y_bottom, who) - who = 'wagon', 'wheels', 'hans' or None (placed)."""
        wx = self.wagon_x0(t) + (self.slots[j] - WAGON[0])
        on_wagon = (wx, G - 70, "wagon")
        if j < 4:
            a, b, c_ = self.bh_times(j)
            if t < a:
                return on_wagon
            foot = (POSTS[j] + 6, G - 130)
            if t < b:
                u = smootherstep(seg(t, a, b))
                return lerp(wx, foot[0], u), lerp(G - 100, foot[1], smoothstep(min(1.0, u * 3))), "wheels"
            if t < c_:
                u = smootherstep(seg(t, b + 0.2, c_))
                x, y = bez(foot, (POSTS[j] + 120, POST_TOP - 140), (POSTS[j], POST_TOP), u)
                return x, y, "hans"
            return POSTS[j], POST_TOP, None
        a, b = self.ground_times(j)
        home = self.home[j][0]
        if t < a:
            return on_wagon
        if t < b:
            u = smootherstep(seg(t, a, b))
            return lerp(wx, home, u), lerp(G - 100, G - 30, u) if u < 0.9 else lerp(G - 30, G, (u - 0.9) / 0.1), "wheels"
        return home, G, None

    def lamp(self, j, t):
        t0 = self.T["lamps"] + 0.6 + j * 1.2
        return smoothstep(seg(t, t0, t0 + 0.5))

    def lamp_order(self):
        return [0, 1, 2, 3, 4, 5]

    # ----- the animals -----

    def bird_state(self, b, t):
        """Bird b: (x, y, flap, face, inside) - from the treehouse rail (or the forest) to birdhouse b."""
        T, H = self.T, self.house
        perch0 = [(1030.0, H.py), (1112.0, H.py), (-400.0, 200.0), (-700.0, 260.0)][b]
        sp = PR.SPECS[b]
        hx, hy = PR.hole_center(sp, POSTS[b], POST_TOP)
        land = (hx + 10, hy + sp.hole_r + 14)
        t0 = T["movein"] + 0.4 + b * 1.6 - (6.0 if b >= 2 else 0.0)
        t1 = t0 + (3.2 if b < 2 else 8.0)
        if b >= 2 and t < t0:
            return None
        if t < t1:
            x, y, flap, face = flying_bird(t, t0, t1, perch0, land, lift=200 if b < 2 else 120)
            return x, y, flap, face, 0.0
        go_in = t1 + 1.2
        if t < go_in:
            hop = max(0.0, math.sin((t - t1) * 9)) * 6 if t > t1 + 0.6 else 0.0
            return land[0], land[1] - hop, 0.0, -1, 0.0
        return land[0], land[1], 0.0, -1, smoothstep(seg(t, go_in, go_in + 0.4))

    def ground_animal(self, i, t):
        """Bunnies (i 0, 1) and the hedgehog (2): (x, hop, gone 0..1)."""
        T = self.T
        x0 = [1150.0, 1260.0, 1370.0][i]
        door = [BUNNY_X - 30, BUNNY_X - 10, HEDGE_X - 20][i]
        t0 = T["movein"] + 7.0 + i * 1.5
        dur = 8.0 if i < 2 else 12.0
        u = seg(t, t0, t0 + dur)
        x = lerp(x0, door, smootherstep(u) * 0.3 + u * 0.7) if u > 0 else x0
        hop = abs(math.sin(u * 20 * math.pi)) * 30 if i < 2 and 0 < u < 1 else 0.0
        gone = smoothstep(seg(t, t0 + dur + 0.3, t0 + dur + 0.9))
        return x, hop, gone

    def inside(self, j, t):
        T = self.T
        if j < 4:
            b = self.bird_state(j, t)
            return 0.0 if b is None else b[4]
        i = 2 if j == 4 else 1
        t0 = T["movein"] + 7.0 + i * 1.5
        dur = 8.0 if i < 2 else 12.0
        return smoothstep(seg(t, t0 + dur + 0.6, t0 + dur + 1.6))

    # ----- camera -----

    def target(self, t):
        T, h = self.T, self.s.h

        def cam(x, z, gf=0.84):
            return x, G - (gf - 0.5) * h / z, z
        keys = [(0.0, *cam(3700, 0.62)), (T["posts"] - 1.0, *cam(3500, 0.66)), (T["posts"] + 1.5, *cam(2420, 0.95, 0.86)),
                (T["level"] + self.d["level"], *cam(2420, 0.95, 0.86)),
                (T["birdhouses"] + 2.0, *cam(2900, 0.72)), (T["ground"], *cam(2800, 0.72)),
                (T["ground"] + 2.0, *cam(3150, 0.85)), (T["lamps"] + self.d["lamps"], *cam(2760, 0.72)),
                (T["movein"] + 2.0, *cam(2300, 0.9, 0.82)), (T["movein"] + 8.0, *cam(2450, 0.9, 0.82)),
                (T["movein"] + 12.0, *cam(2900, 0.85)), (T["movein"] + self.d["movein"], *cam(3000, 0.85)),
                (self.dur, *cam(2500, 0.55, 0.8))]
        return _ease(keys, t)

    # ----- update -----

    def update(self, t, dt):
        T = self.T
        self.reach = {}
        self._wheels(t, dt)
        self._hans(t, dt)
        self._digs(t, dt)
        self._springs(t, dt)
        self._twigs(t, dt)
        self._glo(t, dt)
        P = self.s.particles
        if P.rng.uniform() < (0.1 if t > T["lamps"] else 0.04):
            P.items.append(_firefly(P.rng, 2400.0, G - 500, G))
        self._sounds(t)
        self.stats["animals_home"] = sum(1 for j in range(6) if self.inside(j, t) > 0.5)

    FINAL = {"lantern": 1180.0, "tentacles": 1350.0, "teeth": 1530.0, "springs": 1690.0, "wheels": 1850.0,
             "digger": 1990.0}

    def _final(self, kind, x, t, y=None):
        """Everyone gathers in front of the treehouse for the last shot."""
        T = self.T
        t0 = T["finale"] - 3.0 + 0.2 * list(self.FINAL).index(kind)
        if t < t0:
            return x, y, False
        yy = G - 60 if kind == "lantern" else G
        xx, y2, mv = path([(t0, x, y if y is not None else yy), (t0 + 4.0, self.FINAL[kind], yy)], t)
        return xx, y2, mv

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        T = self.T
        m.punch = 0.0
        x = self.wagon_x0(t) - 150
        if t >= T["birdhouses"]:
            x = PARK[0] - 150
            for j in range(4):
                a, b, c_ = self.bh_times(j)
                if a - 1.2 <= t < a:
                    hx = self.house_pos(j, a)[0]
                    x = lerp(PARK[0] - 150 if j == 0 else POSTS[j - 1] + 6, hx, smootherstep(seg(t, a - 1.2, a)))
                elif a <= t < b + 0.5:
                    x = self.house_pos(j, min(t, b))[0]
                    m.punch = 0.3
                elif b + 0.5 <= t < c_ + 1.0:
                    x = POSTS[j] + 6
            for j in (4, 5):
                a, b = self.ground_times(j)
                wx = self.wagon_x0(t) + (self.slots[j] - WAGON[0])
                if a - 1.0 <= t < a:
                    prev = POSTS[3] + 6 if j == 4 else HEDGE_X
                    x = lerp(prev, wx, smootherstep(seg(t, a - 1.0, a)))
                elif a <= t < b + 0.4:
                    x = self.house_pos(j, min(t, b))[0]
                    m.punch = 0.3
                elif t >= b + 0.4 and j == 5:
                    x = path([(b + 0.4, BUNNY_X, G), (b + 3.4, IDLE["wheels"], G)], t)[0]
        x, _, _ = self._final("wheels", x, t)
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        T = self.T
        reach, x = [], 3380.0
        if t < T["arrive"]:
            x, _, _ = path([(0.0, 5500.0, G), (T["arrive"] - 0.8, 3150.0, G)], t)
            reach = [(x - 140, G - 260), (x - 60, G - 290)]           # the post bundle in two tentacles
        elif t < T["level"]:
            x = 2980.0
            for k in range(4):
                st, px, py, ang = self.post_state(k, t)
                if st == "carry":
                    reach = [(px, py + 40)]
                    x = lerp(2980.0, POSTS[k] + 330, smoothstep(seg(t, self.stand_t[k], self.stand_t[k] + 1.0)))
                elif st == "in" and t < self.stand_t[k] + 2.6:
                    reach = [(POSTS[k] - 6, self.post_top(k, t) + 60)]
                    x = POSTS[k] + 330
            if t < self.stand_t[0]:
                x = path([(T["arrive"], 3150.0, G), (T["arrive"] + 1.5, 2980.0, G)], t)[0]
        elif t < T["ground"]:
            x = POSTS[0] + 280
            for j in range(4):
                a, b, c_ = self.bh_times(j)
                if a <= t < c_ + 0.6:
                    x = POSTS[j] + 260
                    if t >= b - 0.2:
                        hx, hy, who = self.house_pos(j, t)
                        sp = PR.SPECS[j]
                        reach = [(hx - sp.w / 2 + 4, hy - sp.h * 0.5), (hx + sp.w / 2 - 4, hy - sp.h * 0.5)]
                        if who is None:
                            reach = []
            if t >= T["birdhouses"] + 3 * self.bh_cyc + 5.0:
                x = path([(T["birdhouses"] + 3 * self.bh_cyc + 5.0, POSTS[3] + 260, G), (T["ground"] + 2.0, IDLE["tentacles"], G)], t)[0]
        else:
            x = path([(T["ground"] - 2.0, POSTS[3] + 260, G), (T["ground"] + 2.0, IDLE["tentacles"], G)], t)[0]
        x, _, _ = self._final("tentacles", x, t)
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        T = self.T
        m.dig = 0.0
        x = POSTS[0] - 170
        if t < T["arrive"]:
            x, _, _ = path([(0.0, 5300.0, G), (T["arrive"] - 0.4, POSTS[0] - 170, G)], t)
        for k in range(4):
            h0 = self.hole_t[k]
            if h0 - 1.0 <= t < h0:
                x = lerp(POSTS[k - 1] - 70 if k else POSTS[0] - 170, POSTS[k] - 70, smootherstep(seg(t, h0 - 1.0, h0)))
            elif h0 <= t < h0 + 2.4:
                x = POSTS[k] - 70
                m.dig = 0.5 + 0.5 * math.sin(t * 16)
            elif t >= h0 + 2.4 and (k == 3 or t < self.hole_t[k + 1] - 1.0):
                x = POSTS[k] - 70
        if t >= self.hole_t[3] + 2.4:
            x, _, _ = path([(self.hole_t[3] + 2.4, POSTS[3] - 70, G), (self.hole_t[3] + 6.0, IDLE["digger"], G)], t)
        x, _, _ = self._final("digger", x, t)
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        T = self.T
        m.spring = 0.0
        y, dy = None, 0.0
        if t < T["arrive"]:
            x, lift, sq = hops(5600.0, POSTS[0] - 140, 0.0, T["arrive"] - 0.2, t, apex=60, step=170)
            dy, m.spring = -lift, sq
        else:
            p = self.springs_at(t)
            if p is None or t < self.sp_segs[0][0]:
                x = POSTS[0] - 140
            else:
                x, y = p
            if t >= self.sp_done + 0.3:
                x, lift, sq = hops(POSTS[3] + 170, IDLE["springs"], self.sp_done + 0.3, self.sp_done + 4.3, t,
                                   apex=60, step=170)
                y, dy, m.spring = None, -lift, sq
            for t0, t1, j in self.sp_segs:
                if abs(t - t0) < 0.1 or abs(t - t1) < 0.1:
                    m.spring = 0.7
        x2, y2, mv = self._final("springs", x, t, y)
        if x2 != x or (y2 is not None and y2 != y):
            if mv:
                ph = (t * 2.8) % 1.0
                dy = -4 * 55 * ph * (1 - ph)
            x, y = x2, y2
        self.place(m, x, t, dt, y=y, dy=dy, walk=0.0)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        T = self.T
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        x, _, _ = path([(0.0, 5750.0, G), (T["arrive"] + 4.0, IDLE["teeth"], G)], t)
        x, _, _ = self._final("teeth", x, t)
        self.place(m, x, t, dt)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        T = self.T
        x, y = 2600.0, G - 420
        if t < T["arrive"]:
            x, y, _ = path([(0.0, 5400.0, G - 300), (T["arrive"], 2600.0, G - 420)], t)
        elif T["level"] <= t < T["birdhouses"]:
            # runs a glowing string line across the four post tops: they are all the same height
            u = smootherstep(seg(t, T["level"] + 0.4, T["level"] + 4.0))
            x, y = lerp(POSTS[0] - 60, POSTS[3] + 60, u), POST_TOP + 20
        elif T["lamps"] <= t < T["movein"]:
            for j in self.lamp_order():
                t0 = T["lamps"] + 0.6 + j * 1.2
                if t0 - 1.0 <= t < t0 + 0.4:
                    hx, hy, _ = self.house_pos(j, t)
                    lx, ly = PR.lamp_point(PR.SPECS[j], hx, hy)
                    x, y = lx + 60, ly + 150
        elif t >= T["movein"]:
            x, y = 2600.0, G - 520
        x, y, _ = self._final("lantern", x, t, y)
        self.place(m, x, t, dt, y=y)

    # ----- sound -----

    def _sounds(self, t):
        T, s = self.T, self.s
        if self.crossed(0.3):
            self.fx(t, "rustle", self.d["arrive"] - 1.0, 0.18, 4200, G)
        if self.crossed(T["arrive"] - 0.6):
            self.hit(t, "clunk", 45, 0.35, PARK[0], G)
        for k in range(4):
            h0 = self.hole_t[k]
            for q in range(3):
                if self.crossed(h0 + 0.3 + q * 0.7):
                    self.fx(t, "slide", 0.3, 0.25, POSTS[k], G)
            if self.crossed(self.stand_t[k] + 2.0):
                self.hit(t, "thud", 42, 0.35, POSTS[k], G)
            for n, tl in enumerate(self.stomp_land[k]):
                if self.crossed(tl):
                    self.hit(t, "thud", 40, 0.4, POSTS[k], POST_TOP)
                    self.hit(t, "pluck", s.note(k * 2 + n, 0), 0.32, POSTS[k], POST_TOP)
        for t0, t1, j in self.sp_segs:
            if self.crossed(t0):
                self.hit(t, "boing", s.note(int(t0 * 3) % 5, -1), 0.4, j.x0, j.y0)
        lv = T["level"] + 4.0
        if self.crossed(lv):
            for k, n in enumerate((72, 76, 79, 84)):
                self.hit(t + k * 0.1, "chime", n, 0.3, POSTS[k], POST_TOP)
        for j in range(4):
            a, b, c_ = self.bh_times(j)
            if self.crossed(a):
                self.fx(t, "servo", 0.6, 0.14, POSTS[j], G)
            if self.crossed(c_):
                self.hit(t, "clack", s.note(j + 2, 0), 0.35, POSTS[j], POST_TOP)
        for j in (4, 5):
            a, b = self.ground_times(j)
            if self.crossed(b):
                self.hit(t, "clunk", 47, 0.35, self.home[j][0], G)
        for j in range(6):
            t0 = T["lamps"] + 0.6 + j * 1.2
            if self.crossed(t0 + 0.2):
                self.hit(t, "music_box", (72, 76, 79, 84, 88, 91)[j] - 12, 0.3, self.home[j][0], self.home[j][1])
        for b in range(4):
            st = self.bird_state(b, t)
            t0 = T["movein"] + 0.4 + b * 1.6 - (6.0 if b >= 2 else 0.0)
            t1 = t0 + (3.2 if b < 2 else 8.0)
            if self.crossed(t1):
                self.hit(t, "bloop", 79, 0.25, POSTS[b], POST_TOP)
            if self.crossed(t1 + 1.25):
                for k in range(3):
                    self.hit(t + k * 0.1, "music_box", (84, 88, 86)[k] - 12 * (b % 2), 0.16, POSTS[b], POST_TOP)
            _ = st
        for i in range(3):
            t0 = T["movein"] + 7.0 + i * 1.5
            dur = 8.0 if i < 2 else 12.0
            if i < 2:
                for k in range(10):
                    if self.crossed(t0 + (k + 0.5) * dur / 10):
                        self.hit(t, "pluck", s.note(k + 2 * i, 0), 0.18, 2600, G)
            if self.crossed(t0 + dur + 0.6):
                self.hit(t, "chime", (76, 79, 72)[i], 0.3, [BUNNY_X, BUNNY_X, HEDGE_X][i], G - 100)
        if self.crossed(T["finale"] + 1.5):
            for q, kind in enumerate(self.FINAL):
                self.say(t + q * 0.2, kind, "cheer", 1600, G - 200, 0.45)
            for k, n in enumerate((60, 64, 67, 72, 76, 79, 84)):
                self.hit(t + 1.2 + k * 0.12, "soft_bell", n, 0.3, 2400, G - 300)

    # ----- drawing -----

    def draw(self, c, t):
        s, T, H = self.s, self.T, self.house
        self.backdrop(c, t)
        for j, x in enumerate((-400, 200, 3900, 4400, 5000, 5600)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 3), 900 + j)
        H.draw_tree(c, s)
        H.draw_house(c, s, t, windows=1.0, lanterns=1.0)
        # bushes behind the hedgehog and bunny houses
        for bx, r in ((HEDGE_X - 40, 120), (HEDGE_X + 90, 90), (BUNNY_X + 40, 140), (BUNNY_X - 120, 100)):
            c.circle(bx, G - r * 0.55, r, LEAF[1] * 0.75)
        # posts
        for k in range(4):
            st, px, py, ang = self.post_state(k, t)
            if st == "bundle":
                rect(c, px - 165, py - 13, px + 165, py + 13, POST)
                c.line(px - 165, py - 13, px + 165, py - 13, POST * 1.25, 2)
            elif st == "carry":
                ca, sa = math.cos(ang), math.sin(ang)
                L = 370
                cx, cy = px + sa * L / 2, py + ca * L / 2
                pts = [(cx - sa * L / 2 - ca * 13, cy - ca * L / 2 + sa * 13), (cx - sa * L / 2 + ca * 13, cy - ca * L / 2 - sa * 13),
                       (cx + sa * L / 2 + ca * 13, cy + ca * L / 2 - sa * 13), (cx + sa * L / 2 - ca * 13, cy + ca * L / 2 + sa * 13)]
                c.polygon(pts, POST)
            else:
                rect(c, px - 13, py, px + 13, G + 40, POST)
                rect(c, px - 34, py - 8, px + 34, py, POST * 1.15)
        for k in range(4):                                          # holes, until the post is in
            h0 = self.hole_t[k]
            if h0 <= t and self.post_top(k, t) is None:
                u = smoothstep(seg(t, h0, h0 + 2.4))
                c.polygon(ellipse(POSTS[k], G + 2, 24 * u + 2, 10 * u + 1, 16), np.array([18, 14, 14]))
                c.polygon(ellipse(POSTS[k] - 60, G, 30 * u, 14 * u, 16, math.pi, 2 * math.pi), SOIL)
        if T["level"] + 0.3 <= t < T["birdhouses"] + 1.0:
            u = smootherstep(seg(t, T["level"] + 0.4, T["level"] + 4.0))
            ok = smoothstep(seg(t, T["level"] + 3.8, T["level"] + 4.3))
            fade = 1 - smoothstep(seg(t, T["birdhouses"], T["birdhouses"] + 1.0))
            x1 = lerp(POSTS[0] - 60, POSTS[3] + 60, u)
            col = (np.array([255, 196, 110]) * (1 - ok) + np.array([140, 255, 160]) * ok) * fade
            c.line(POSTS[0] - 60, POST_TOP - 10, x1, POST_TOP - 10, col * 0.9, 3)
            s.glow_draw(lambda g: g.line(POSTS[0] - 60, POST_TOP - 10, x1, POST_TOP - 10, col * 0.6, 8))
        PR.flat_wagon(c, self.wagon_x0(t), self.wagon_x0(t) + (WAGON[1] - WAGON[0]), G,
                      wheel_rot=-(self.wagon_x0(t) - 5900.0) / 24)
        carried = {}
        for j in range(6):
            hx, hy, who = self.house_pos(j, t)
            if who in ("wheels", "hans"):
                carried[who] = (j, hx, hy)
                continue
            self._house(c, j, hx, hy, t)
        for b in range(4):
            st = self.bird_state(b, t)
            if st is None:
                continue
            x, y, flap, face, ins = st
            if ins >= 1:
                sp = PR.SPECS[b]
                hx, hy = PR.hole_center(sp, POSTS[b], POST_TOP)
                peek = 0.5 + 0.5 * math.sin(t * 1.3 + b)
                c.circle(hx + 3 * peek, hy + 3, 8.5, BIRD_COLS[b][0])
                c.circle(hx + 6 * peek, hy + 6, 4.5, BIRD_COLS[b][1])
                c.circle(hx + 5 * peek, hy, 2.0, np.array([16, 16, 20]))
                continue
            PR.bird(c, x, y - 10 * ins, 1.45 * (1 - 0.6 * ins), face, flap, BIRD_COLS[b], t)
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)

        def before(kind):
            if kind == "tentacles" and "hans" in carried:
                j, hx, hy = carried["hans"]
                self._house(c, j, hx, hy, t)
        self.draw_monsters(c, t, kinds=[k for k in self.poses if k != "wheels"], before=before)
        if "wheels" in self.poses:
            super().draw_monsters(c, t, kinds=["wheels"])
            if "wheels" in carried:
                j, hx, hy = carried["wheels"]
                self._house(c, j, hx, hy, t)
        # the bunnies and the hedgehog, in front of the Keepers (they are small and hop past them)
        for i in range(3):
            x, hop, gone = self.ground_animal(i, t)
            if gone >= 1:
                continue
            sc = 1.3 * (1 - 0.5 * gone)
            if i < 2:
                bunny(c, x, G + 6, sc, hop, 1)
            else:
                hedgehog(c, x, G + 6, sc, 1, t)

    def _house(self, c, j, x, y, t):
        PR.draw_house(c, self.s, PR.SPECS[j], x, y, t, paint=1.0, lamp=self.lamp(j, t), inside=self.inside(j, t))


def _ease(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t < t1:
            u = smootherstep((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return tuple(lerp(p, q, u) for p, q in zip(a, b))
    return keys[-1][1:]
