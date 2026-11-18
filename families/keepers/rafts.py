"""The brook and the six rafts of Forest Keepers episode 7 (raft_race.py): the course, the water physics and the
drawing.

We look at the brook from the side and a little from above (like the marble run's lanes): it runs left to right down
the hillside in steps - the start pool, a riffle over stones, the first little falls, a quiet pool with lily pads, the
rapids, the second falls, a long glide to the finish rope and the finish pool with a log boom that catches the rafts.
Lane 0 is nearest us; further lanes are drawn higher, a little right and smaller.

The race is simulated (480 Hz, recorded at 120 Hz), each raft in its own lane, all on the same water:
- the current: every stretch has its own speed, faster in the middle of the stream than by the banks; a raft is
  dragged towards the water's speed (linear + quadratic drag on its logs) and pushed a little by the breeze on its
  sail;
- it floats: a damped buoyancy spring holds it on the surface (waves, the pillow of water over a rock), a heavier raft
  sits deeper and settles more slowly; it lies along the water surface (pitch follows the surface slope);
- rocks under the surface: a raft rides up over them and scrapes (it slows down, more so when heavy);
- the falls: over the lip it flies (real gravity), tips nose down, plunges and bobs back up; just below each falls the
  water circles back (the hole / backwash), pulsing, so a raft can be held there for a moment until a surge flushes it
  out.
The rafts differ a little (hand-made: weight, drag, sail size, length) and that decides the race.
"""
import math

import cv2
import numpy as np

from families.foundry.keepers.common import GRAVITY, PLANK, WATER, Xform, ellipse, lerp, rect, smoothstep
from families.foundry.style import lighten
from families.foundry.tree_monsters import EARTH, GRASS, LEAF, TRUNK, tree

from .marbles import KINDS, MARBLE_COLS, NAMES

G = 1000.0
N_LANES = 6
LANE_DY = 27.0                 # each lane further back is drawn this much higher ...
LANE_DX = 12.0                 # ... this much further right ...
LANE_SC = 0.03                 # ... and this much smaller
REC_HZ = 120
RAFT_L = 104.0                 # every raft's logs are cut to this at the stop board
SIM_HZ = 480

# ----- the course (x along the brook; y = water surface at lane 0) -----
# (kind, x0, x1, y0, y1, current px/s, wave amplitude px); a falls sits at the end of a stretch whose next one starts lower
STRETCHES = [
    ("pool", 7900.0, 8650.0, G - 640.0, G - 640.0, 62.0, 1.5),
    ("riffle", 8650.0, 9550.0, G - 640.0, G - 612.0, 175.0, 4.5),
    ("pool", 9550.0, 10350.0, G - 482.0, G - 480.0, 78.0, 2.0),
    ("rapids", 10350.0, 11550.0, G - 480.0, G - 404.0, 235.0, 6.5),
    ("glide", 11550.0, 13250.0, G - 252.0, G - 236.0, 135.0, 2.5),
    ("pool", 13250.0, 14100.0, G - 236.0, G - 236.0, 38.0, 1.5),
]
FALLS = [9550.0, 11550.0]                 # the lips
HOLE = 230.0                              # how far below a falls the water circles back
START_BOOM = 8330.0                       # the log boom the rafts wait behind
FINISH_X = 13000.0                        # the finish rope between two posts
END_BOOM = 13700.0                        # the boom across the finish pool that catches them
# the current across the stream: the fast water swings from side to side with the bends (no lane is faster all the
# way down)
LANE_FLOW = {"pool": [1.0, 0.98, 1.0, 1.02, 1.0, 1.0], "riffle": [1.06, 1.04, 1.0, 0.97, 0.96, 0.97],
             "rapids": [0.95, 0.97, 1.0, 1.0, 1.04, 1.04], "glide": [0.99, 0.99, 1.02, 1.02, 0.99, 0.99]}
# rocks just under the surface: (x, lane, half width, height of the water pillow over it)
# (one per lane)
ROCKS = [(8930.0, 2, 46.0, 20.0), (9180.0, 0, 44.0, 20.0), (9330.0, 4, 44.0, 20.0), (10640.0, 3, 46.0, 20.0),
         (10860.0, 1, 44.0, 20.0), (11120.0, 5, 46.0, 20.0)]
# how hard the water circles back below each falls, per lane (px/s)
HOLE_PULL = [[133.0, 161.0, 182.0, 168.0, 147.0, 140.0], [154.0, 175.0, 161.0, 189.0, 175.0, 147.0]]
LILY = [(9800.0, 4), (9900.0, 5), (10060.0, 5), (10150.0, 4)]       # lily pads in the quiet pool (x, lane)


def stretch_at(x):
    for st in STRETCHES:
        if x < st[2]:
            return st
    return STRETCHES[-1]


def surface(x):
    """Water surface y at lane 0 (calm, without waves or rocks)."""
    k, x0, x1, y0, y1, _, _ = stretch_at(x)
    if x < x0:
        return y0
    return lerp(y0, y1, (x - x0) / (x1 - x0))


def lane_off(j):
    """(dx, dy, scale) of lane j."""
    return LANE_DX * j, -LANE_DY * j, 1.0 - LANE_SC * j


def rock_pillow(x, lane):
    """How far the water bulges up over a rock in this lane at x (0 if none)."""
    h = 0.0
    for (xr, j, r, hr) in ROCKS:
        if j == lane and abs(x - xr) < r:
            h = max(h, hr * math.cos(0.5 * math.pi * (x - xr) / r) ** 2)
    return h


def wave(x, t, amp, lane):
    """Little waves running down the stream."""
    return amp * (0.6 * math.sin(x * 0.045 - t * 5.0 + lane * 1.3) + 0.4 * math.sin(x * 0.11 - t * 7.3 + lane * 2.1))


def current(x, lane, t):
    """Downstream speed of the water at x in this lane (negative in a hole below a falls)."""
    st = stretch_at(x)
    kind, u = st[0], st[5]
    u *= LANE_FLOW.get(kind, LANE_FLOW["pool"])[lane]
    for f, xf in enumerate(FALLS):
        if xf <= x < xf + HOLE:
            s = (x - xf) / HOLE
            # the hole breathes: now and then a surge of water comes through and flushes it downstream
            surge = max(0.0, math.sin(2 * math.pi * t / (2.1 + 0.25 * f) + lane * 1.7 + f))
            back = HOLE_PULL[f][lane] * (1.0 - 2.5 * surge)
            u = lerp(-back, u, smoothstep(s))
    return u


# ----- the rafts -----

class Trait:
    def __init__(self, mass, drag, sail, length):
        self.mass, self.drag, self.sail, self.length = mass, drag, sail, length


def traits(seed):
    rs = np.random.default_rng(1000 + seed)
    # every raft is trimmed to the same length at the stop board; they differ in the wood (weight), how the logs sit
    # in the water (drag) and the leaf each one got for a sail
    return [Trait(float(rs.uniform(0.82, 1.2)), float(rs.uniform(0.82, 1.18)), float(rs.uniform(0.6, 1.4)),
                  RAFT_L) for _ in range(N_LANES)]


def breeze(t):
    """The breeze down the valley (px/s^2 on a sail of size 1)."""
    return 16.0 + 10.0 * math.sin(0.7 * t + 0.4) + 5.0 * math.sin(1.9 * t + 2.0)


class Run:
    """One raft down the brook. rec rows: x, y, pitch, vx, airborne; events (t, kind, x, y, strength)."""

    def __init__(self, trait, lane, t_max=90.0, x0=None):
        self.trait, self.lane = trait, lane
        tr = trait
        dt = 1.0 / SIM_HZ
        x = (START_BOOM - 8.0 - tr.length / 2) if x0 is None else x0
        y = surface(x)
        vx = vy = 0.0
        th = om = 0.0
        air = False
        rec, ev = [], []
        self.finish_t = None
        self.boom_t = None
        n = int(t_max * SIM_HZ)
        every = SIM_HZ // REC_HZ
        fall_i = 0
        for i in range(n):
            t = i * dt
            lo = FALLS[fall_i - 1] + 1.0 if fall_i > 0 else -1e9      # below a falls: the water there, not above it

            def S(xq):
                return surface(max(xq, lo))

            if not air:
                if x < lo + 16:                                  # the rock face under the falls
                    x, vx = lo + 16, abs(vx) * 0.3
                u = current(x, lane, t)
                rel = u - vx
                ax = rel * (1.3 + 0.011 * abs(rel)) * tr.drag / tr.mass + breeze(t) * tr.sail / tr.mass
                # rocks: it rides up over the pillow of water and scrapes, more so when heavy
                p = rock_pillow(x, lane)
                if p > 0:
                    ax -= 2.2 * tr.mass * vx * p / 20.0
                    if not ev or ev[-1][1] != "rock" or t - ev[-1][0] > 0.6:
                        if p > 6:
                            ev.append((t, "rock", x, y, min(1.0, abs(vx) / 260.0)))
                # the curtain of a falls pushes a raft that drifted back into it down and out again
                for xf in FALLS:
                    if xf <= x < xf + 34:
                        ax += 600.0 * (1 - (x - xf) / 34)
                kind = stretch_at(x)[0]
                amp = stretch_at(x)[6]
                target = S(x) - p + wave(x, t, amp, lane)
                ay = (-80.0 * (y - target) - 10.0 * vy) / tr.mass
                # it lies along the water: pitch follows the surface slope under it
                h = tr.length / 2
                yl = S(x - h) - rock_pillow(x - h, lane) + wave(x - h, t, amp, lane)
                yr = S(x + h) - rock_pillow(x + h, lane) + wave(x + h, t, amp, lane)
                if fall_i < len(FALLS) and x + h > FALLS[fall_i] > x - h:
                    yr = surface(FALLS[fall_i] - 1)              # over the lip: the nose still rests on the top
                th_t = math.atan2(yr - yl, 2 * h)
                al = -60.0 * (th - th_t) - 9.0 * om
                # over the lip: off it goes
                if fall_i < len(FALLS) and x >= FALLS[fall_i]:
                    air = True
                    vx = max(vx, 0.8 * stretch_at(FALLS[fall_i] - 1)[5])
                    ev.append((t, "drop", x, y, min(1.0, vx / 300.0)))
                    fall_i += 1
            if air:
                ax, ay = 0.0, GRAVITY
                th_t = 0.75 * math.atan2(vy, max(1.0, vx))
                al = -40.0 * (th - th_t) - 6.0 * om
                if vy > 0 and y >= surface(x):
                    air = False
                    s = min(1.0, vy / 700.0)
                    ev.append((t, "splash", x, surface(x), s))
                    vy *= 0.35
                    vx *= 0.72
            vx += ax * dt
            vy += ay * dt
            om += al * dt
            x += vx * dt
            y += vy * dt
            th += om * dt
            if x > END_BOOM - tr.length / 2 - 6 - 4 * lane and vx > 0:      # the boom catches it
                if self.boom_t is None:
                    self.boom_t = t
                    ev.append((t, "boom", x, y, min(1.0, vx / 120.0)))
                vx = -0.2 * vx
            if self.finish_t is None and x + tr.length / 2 >= FINISH_X:
                self.finish_t = t
            if i % every == 0:
                rec.append((x, y, th, vx, 1.0 if air else 0.0))
            if self.boom_t is not None and t > self.boom_t + 45.0:
                break
        self.rec = np.array(rec)
        self.events = ev
        self.dur = len(rec) / REC_HZ

    def at(self, tau):
        """(x, y, pitch, vx, airborne) at tau (s after the start); holds the last row."""
        f = tau * REC_HZ
        i = int(min(len(self.rec) - 2, max(0, f)))
        u = min(1.0, max(0.0, f - i))
        a, b = self.rec[i], self.rec[i + 1]
        return tuple(float(v) for v in a + (b - a) * u)

    def progress(self, tau):
        return (self.at(tau)[0] - START_BOOM) / (FINISH_X - START_BOOM)


class Race:
    """Six rafts released together: finish order, lead changes as a viewer sees them."""

    def __init__(self, seed, t_max=90.0):
        self.seed = seed
        self.traits = traits(seed)
        self.runs = [Run(tr, j, t_max) for j, tr in enumerate(self.traits)]
        self.finish = [r.finish_t if r.finish_t is not None else 999.0 for r in self.runs]
        self.order = sorted(range(N_LANES), key=lambda i: self.finish[i])
        # a raft takes the lead only when it is clearly ahead (a quarter raft) for half a second
        self.leaders, self.changes = [], 0
        last, cand, since = None, None, 0.0
        for f in range(int(min(self.finish) * 30) + 1):
            tau = f / 30.0
            prog = [r.at(tau)[0] for r in self.runs]
            best = max(range(N_LANES), key=lambda i: prog[i])
            if last is None:
                last = best
                self.leaders.append((0.0, best))
                continue
            if best != last and prog[best] > prog[last] + 26.0:
                if best != cand:
                    cand, since = best, tau
                if tau - since >= 0.5:
                    self.changes += 1
                    self.leaders.append((round(tau, 2), best))
                    last, cand = best, None
            else:
                cand = None
        if self.leaders[-1][1] != self.order[0]:
            self.leaders.append((round(min(self.finish), 2), self.order[0]))
            self.changes += 1
        self.spread = self.finish[self.order[-1]] - self.finish[self.order[0]]
        self.gap12 = self.finish[self.order[1]] - self.finish[self.order[0]]
        # where the lead was last taken (stretch kind)
        self.last_change_x = self.runs[self.leaders[-1][1]].at(self.leaders[-1][0])[0]

    def standings(self, tau):
        def key(i):
            if self.finish[i] <= tau:
                return (0, self.finish[i])
            return (1, -self.runs[i].at(tau)[0])
        return sorted(range(N_LANES), key=key)

    def leader(self, tau):
        ld = self.leaders[0][1]
        for t0, i in self.leaders:
            if t0 <= tau:
                ld = i
        return ld

    def holds(self):
        """Seconds each raft spent going backwards (held in a hole)."""
        return [round(float(np.sum(r.rec[:, 3] < -5)) / REC_HZ, 2) for r in self.runs]


# ====================================================================== drawing

STONE = np.array([74, 70, 66], np.float64)
STONE_WET = np.array([48, 50, 54], np.float64)
FOAM = np.array([200, 214, 226], np.float64)
WATER_FAR = WATER * 0.72
LOG = np.array([132, 98, 64], np.float64)
LOG_END = np.array([196, 160, 112], np.float64)
ROPE = np.array([206, 186, 140], np.float64)
SAIL_RAW = np.array([206, 188, 150], np.float64)      # the pale leaf before Glo's light colours it
LAMP_C = np.array([255, 196, 110], np.float64)
FAR_DEPTH = (N_LANES - 1) * LANE_DY + 26.0          # the water band from lane 0's waterline to the far bank
FAR_DX = (N_LANES - 1) * LANE_DX + 14.0
NEAR = 16.0                                         # the near edge of the water below lane 0's waterline
BANK = 70.0                                         # the near bank (where the Keepers stand) below lane 0's waterline
PLATEAU_Y = G - 640.0 + BANK                        # the flat bank above the start pool (the raft workshop)


def ground(x):
    """Where a Keeper stands on the near bank."""
    if x < STRETCHES[0][1]:
        return PLATEAU_Y
    return surface(x) + BANK


def levels():
    """The water in contiguous stretches between the falls: [(x0, x1)]."""
    edges = [STRETCHES[0][1] - 2500.0] + FALLS + [STRETCHES[-1][2] + 2500.0]
    return list(zip(edges, edges[1:]))


def far_edge(x):
    return surface(x) - FAR_DEPTH


def far_hill(x):
    """The far hillside behind the brook (a smooth valley)."""
    return G - 900.0 + 0.11 * (x - 7000.0) + 60 * math.sin(x * 0.0011) + 30 * math.sin(x * 0.0031 + 1.0)


def draw_far(c, s, t):
    """The hillside across the brook: a dark slope with a far tree line on it."""
    vx0, vx1, vy0, vy1 = s.view()
    xs = np.linspace(vx0 - 200, vx1 + 200, 60)
    c.polygon([(x, far_hill(x)) for x in xs] + [(vx1 + 200, vy1 + 2000), (vx0 - 200, vy1 + 2000)],
              np.array([20, 30, 28], np.float64))
    for k in range(int((vx0 - 300) // 95), int((vx1 + 300) // 95) + 1):
        rs = np.random.default_rng(5000 + k)
        x = k * 95 + rs.uniform(-30, 30)
        hh = rs.uniform(230, 400)
        y = far_hill(x) + 10
        c.polygon([(x - 10, y), (x + 10, y), (x + 7, y - hh * 0.5), (x - 7, y - hh * 0.5)], np.array([18, 30, 26]))
        c.circle(x, y - hh * 0.72, hh * 0.27, np.array([22, 38, 32]))
        c.circle(x - hh * 0.15, y - hh * 0.6, hh * 0.2, np.array([20, 34, 30]))
        c.circle(x + hh * 0.16, y - hh * 0.62, hh * 0.2, np.array([24, 40, 34]))


FAR_TREES = (7300.0, 7760.0, 8450.0, 9200.0, 9950.0, 10500.0, 11300.0, 12050.0, 12700.0, 13500.0)


def draw_far_bank(c, s, trees=True):
    """The bank across the brook, from the far hillside down to the water, with stones at the water and trees."""
    vx0, vx1 = s.view()[:2]
    for a, b in levels():
        a0, b1 = max(a, vx0 - 300), min(b, vx1 + 300)
        if b1 <= a0:
            continue
        xs = np.linspace(a0, b1, max(4, int((b1 - a0) / 40)))
        top = [(x + FAR_DX, far_edge(x) - 46) for x in xs]
        edge = [(x + FAR_DX, far_edge(x)) for x in xs[::-1]]
        c.polygon([(x + FAR_DX, far_hill(x) - 40) for x in xs] + top[::-1], EARTH * 0.95)
        c.polygon(top + edge, EARTH * 1.15)
        c.polyline(top, GRASS * 1.15, 6)
        for x in np.arange(a0 - a0 % 37, b1, 37):           # stones along the water's edge
            rs = np.random.default_rng(int(x) + 17)
            c.polygon(ellipse(x + FAR_DX + rs.uniform(-8, 8), far_edge(x) - 4, rs.uniform(12, 22), rs.uniform(6, 10), 10),
                      STONE * rs.uniform(0.75, 1.0))
    for xf in FALLS:                                          # the rock step of each falls on the far side
        if not s.visible(xf - 200, xf + 200):
            continue
        top_y, low_y = far_edge(xf - 1), far_edge(xf + 1)
        x = xf + FAR_DX
        c.polygon([(x - 30, top_y - 50), (x + 26, top_y - 50), (x + 40, low_y + 6), (x - 6, low_y + 6)], STONE * 0.7)
        c.polygon([(x - 10, top_y - 50), (x + 26, top_y - 50), (x + 30, top_y + 20)], STONE * 0.85)
    if trees:
        for j, x in enumerate(FAR_TREES):
            if s.visible(x - 300, x + 300):
                tree(c, x + FAR_DX, far_edge(x) - 40, 560 + 70 * (j % 3), 3100 + j)


def _flow_streaks(c, x0, x1, t):
    """Lines on the water moving downstream with the current: you can see how fast each stretch runs. Each streak
    rides through its own cell of the brook, fixed in the world (so a moving camera never drags them along: FK0004's
    first cut had them tied to the edge of the view and they ran upstream when the camera pulled back), and fades in
    and out at the ends of its cell."""
    for j in range(N_LANES):
        dx, dy, _ = lane_off(j)
        spacing = 120.0 + 23 * j
        bg = lerp(WATER * 1.04, WATER_FAR, j / 6.0)          # the water under lane j (draw_water's bands)
        for k in range(int(math.floor(x0 / spacing)), int(x1 / spacing) + 1):
            base = k * spacing
            st = stretch_at(base)
            u = st[5] * LANE_FLOW.get(st[0], LANE_FLOW["pool"])[j]
            ph = (u * t * 0.9 / spacing + 0.37 * k + 0.29 * j) % 1.0
            x = base + ph * spacing
            ln = 18 + u * 0.12
            a = math.sin(math.pi * ph) * min(1.0, (x - x0) / 40.0, (x1 - x - ln) / 40.0)
            if a <= 0.02:
                continue
            y = surface(x) + dy - 4 + 2 * math.sin(x * 0.03 + t * 3)
            col = WATER * (1.5 + 0.25 * (st[0] in ("riffle", "rapids")))
            c.line(x + dx, y, x + dx + ln, y + (surface(x + ln) - surface(x)), lerp(bg, col, min(1.0, a * 1.4)), 2)


def draw_water(c, s, t):
    """The brook: every level of water as a band from the near edge to the far bank, the falls, foam."""
    vx0, vx1 = s.view()[:2]
    for a, b in levels():
        a0, b1 = max(a, vx0 - 300), min(b, vx1 + 300)
        if b1 <= a0:
            continue
        xs = np.linspace(a0, b1, max(4, int((b1 - a0) / 30)))
        far = [(x + FAR_DX, far_edge(x)) for x in xs[::-1]]
        for q in range(6):                                # deeper and darker towards the far bank
            u = q / 6.0
            near = [(x + FAR_DX * u, surface(x) + NEAR - (FAR_DEPTH + NEAR) * u) for x in xs]
            c.polygon(near + far, lerp(WATER * 1.04, WATER_FAR, u))
        c.polyline(far[::-1], WATER * 1.35, 3)
        for k in range(int(a0 // 260), int(b1 // 260) + 1):  # the moon on the water
            x = k * 260.0 + 90 * math.sin(k * 1.7)
            if a0 < x < b1:
                for q in range(3):
                    y = surface(x) - FAR_DEPTH * (0.3 + 0.2 * q) + 2 * math.sin(t * 2 + k + q)
                    w = 26 - 6 * q + 6 * math.sin(t * 1.3 + k * 2.1 + q)
                    c.line(x + FAR_DX * (0.3 + 0.2 * q) - w, y, x + FAR_DX * (0.3 + 0.2 * q) + w, y,
                           np.array([150, 170, 190]) * (0.55 - 0.1 * q), 2)
        _flow_streaks(c, a0, b1, t)
        for x in np.arange(math.ceil(a0 / 60.0) * 60.0, b1, 60.0):   # chop and foam where the water runs fast
            st = stretch_at(x)
            if st[0] in ("riffle", "rapids"):
                for j in range(0, N_LANES, 2):
                    dx, dy, _ = lane_off(j)
                    ph = math.sin(x * 0.07 + t * 6 + j * 2.0)
                    if ph > 0.3:
                        y = surface(x) + dy + 2
                        c.line(x + dx, y, x + dx + 14, y - 3 * ph, FOAM * (0.45 + 0.3 * ph), 2)
    for f, xf in enumerate(FALLS):
        if s.visible(xf - 200, xf + 300):
            draw_falls(c, s, xf, t)


def draw_falls(c, s, xf, t):
    """A little falls: the water curls over the lip in a smooth sheet (each strand a falling arc) and boils white at
    the foot."""
    y_up, y_low = surface(xf - 1), surface(xf + 1)
    drop = y_low - y_up

    def strand(u, q):
        """Point q (0 lip .. 1 foot) of the strand at depth u (0 near .. 1 far)."""
        x0, y0 = xf + FAR_DX * u, y_up - FAR_DEPTH * u + NEAR * (1 - u)
        return x0 + 34 * math.sqrt(q), y0 + drop * q

    near = [strand(0.0, q / 10) for q in range(11)]
    far = [strand(1.0, q / 10) for q in range(11)]
    c.polygon(near + far[::-1], WATER * 1.18)
    c.polygon([strand(u / 6, 0.0) for u in range(7)] + [strand(u / 6, 0.35) for u in reversed(range(7))],
              WATER * 1.45)                                  # the glassy lip
    for k in range(22):                                    # strands of white water sliding down the sheet
        u = (k + 0.5) / 22
        ph = (t * 1.6 + k * 0.618) % 1.0
        q0, q1 = ph * 0.8 + 0.1, min(1.0, ph * 0.8 + 0.38)
        pts = [strand(u, lerp(q0, q1, i / 4)) for i in range(5)]
        c.polyline(pts, FOAM * (0.45 + 0.35 * ((k * 7) % 5) / 4), 2)
    for k in range(12):                                    # the boil at the foot
        u = (k + 0.5) / 12
        x, y = strand(u, 1.0)
        r = 9 + 4 * math.sin(t * 7 + k * 1.9)
        c.circle(x + 10 + 6 * math.sin(t * 3 + k), y - 3, r, FOAM * (0.85 + 0.12 * math.sin(t * 5 + k)))
        c.circle(x + 30 + 6 * math.sin(t * 2.3 + k), y, r * 0.7, FOAM * 0.7)
        c.circle(x + 52 + 5 * math.sin(t * 1.7 + k), y + 2, r * 0.45, FOAM * 0.5)
    s.glow_draw(lambda g: g.polygon(near + far[::-1], FOAM * 0.07))
    s.glow_draw(lambda g: g.circle(strand(0.5, 1.0)[0] + 20, strand(0.5, 1.0)[1], 70, FOAM * 0.08))


def draw_rock(c, xr, j, r, h, t):
    """A boulder just under the water: its wet top shows, the water piles up over it and leaves a V behind."""
    dx, dy, sc = lane_off(j)
    x, y = xr + dx, surface(xr) + dy
    c.polygon(ellipse(x, y + 4, r * 0.75 * sc, 12 * sc, 16, math.pi, 2 * math.pi), STONE_WET)
    c.polygon(ellipse(x - 4, y + 1, r * 0.45 * sc, 6 * sc, 12, math.pi, 2 * math.pi), STONE * 0.9)
    ph = 0.5 + 0.5 * math.sin(t * 8 + xr)
    c.polyline(ellipse(x - r * 0.15, y + 1, r * 0.85 * sc, 6 * sc, 14, math.pi * 1.05, math.pi * 1.95),
               FOAM * (0.55 + 0.2 * ph), 3)
    c.line(x + r * 0.5, y + 3, x + r * 1.6, y - 4, FOAM * 0.45, 2)
    c.line(x + r * 0.5, y + 5, x + r * 1.6, y + 9, FOAM * 0.45, 2)


def draw_lily(c, x, j, t, k=0):
    dx, dy, sc = lane_off(j)
    xx, yy = x + dx + 6 * math.sin(t * 0.4 + x), surface(x) + dy + 2
    c.polygon(ellipse(xx, yy, 34 * sc, 9 * sc, 16), np.array([46, 92, 54]))
    c.line(xx, yy, xx + 30 * sc, yy - 3, np.array([30, 66, 40]), 2)
    if k % 2 == 0:
        c.circle(xx - 10, yy - 5, 6 * sc, np.array([228, 206, 220]))
        c.circle(xx - 10, yy - 7, 3 * sc, np.array([250, 236, 160]))
    return xx, yy


def draw_near_bank(c, s, t):
    """The bank in front of the brook: wet stones at the water, then the grassy bank the Keepers stand on."""
    vx0, vx1, vy0, vy1 = s.view()
    for a, b in levels():
        a0, b1 = max(a, vx0 - 300), min(b, vx1 + 300)
        if b1 <= a0:
            continue
        b1e = b1 + 14
        xs = np.linspace(a0, b1e, max(4, int((b1e - a0) / 30)))
        sy = [surface(min(x, b1 - 1)) for x in xs]
        edge = [(x, y + NEAR) for x, y in zip(xs, sy)]
        c.polygon(edge + [(b1e, vy1 + 3000), (a0, vy1 + 3000)], EARTH)
        c.polygon(edge + [(x, y + 34) for x, y in zip(xs[::-1], sy[::-1])], STONE_WET * 0.9)
        c.polyline([(x, y + 36) for x, y in zip(xs, sy)], GRASS * 1.2, 6)
        for x in np.arange(a0 - a0 % 31, b1, 31):
            rs = np.random.default_rng(int(x) + 3)
            c.polygon(ellipse(x + rs.uniform(-6, 6), surface(x) + NEAR + 4, rs.uniform(11, 19), rs.uniform(6, 9), 10),
                      STONE * rs.uniform(0.7, 0.95))
    for k in range(int((vx0 - 200) // 70), int((vx1 + 200) // 70) + 1):    # tufts, ferns, fallen leaves
        rs = np.random.default_rng(7000 + k)
        x = k * 70.0 + rs.uniform(-25, 25)
        y = surface(x) + rs.uniform(60, 330)
        if any(abs(x - xf) < 50 for xf in FALLS):
            continue
        kind = rs.integers(4)
        if kind == 0:                                       # a grass tuft
            for q in range(5):
                a = -math.pi / 2 + (q - 2) * 0.28
                c.line(x, y, x + 26 * math.cos(a), y + 26 * math.sin(a), GRASS * 1.4, 3)
        elif kind == 1:                                     # a little fern
            for q in range(4):
                c.line(x, y, x - 18 + 12 * q, y - 18 - 4 * (q % 2), LEAF[1] * 0.95, 4)
        elif kind == 2:                                     # fallen leaves
            for q in range(3):
                col = (np.array([176, 112, 52]), np.array([150, 84, 44]), np.array([196, 150, 64]))[q]
                c.polygon(ellipse(x + q * 14, y + 3 * q, 8, 4, 8, rs.uniform(0, 3)), col * 0.7)
        else:                                               # a stone
            c.polygon(ellipse(x, y, rs.uniform(14, 26), rs.uniform(7, 12), 10, math.pi, 2 * math.pi), STONE * 0.7)
    for xf in FALLS:                                          # the rock step on our side
        if not s.visible(xf - 100, xf + 100):
            continue
        top_y, low_y = surface(xf - 1) + NEAR, surface(xf + 1) + NEAR
        c.polygon([(xf - 40, top_y - 6), (xf + 18, top_y - 6), (xf + 30, low_y + 60), (xf - 30, low_y + 80)],
                  STONE * 0.62)
        c.polygon([(xf - 40, top_y - 6), (xf + 18, top_y - 6), (xf + 4, top_y + 40)], STONE * 0.8)
        c.polygon([(xf - 18, low_y + 10), (xf + 34, low_y + 2), (xf + 40, low_y + 40), (xf - 12, low_y + 46)],
                  STONE * 0.75)


def boom_ends(x, open_=0.0):
    """A log boom hinged on the far bank at x: (near end, far end). open_ 0 = across the brook, 1 = swung round
    along the far bank, downstream."""
    fx, fy = x + FAR_DX - 4, surface(x) - FAR_DEPTH + 8
    a = open_ * math.pi / 2
    across = (-(FAR_DX - 4), FAR_DEPTH + 4)                 # from the far bank to our side, on screen
    nx = fx + across[0] * math.cos(a) + 240 * math.sin(a)
    ny = fy + across[1] * math.cos(a)
    return (nx, ny), (fx, fy)


BOOM_FAR = (FAR_DEPTH - 8.0) / LANE_DY      # how far back the boom's hinge is, in lanes from lane 0


def _bar(c, p0, p1, w, col):
    """A straight bar w thick from p0 to p1 (flat ends, so slices of it join up)."""
    ex, ey = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(ex, ey)
    if n < 1e-6:
        return
    ox, oy = -ey / n * w / 2, ex / n * w / 2
    c.polygon([(p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy), (p1[0] - ox, p1[1] - oy),
               (p0[0] - ox, p0[1] - oy)], col)


def draw_boom(c, x, open_=0.0, d0=-99.0, d1=99.0):
    """The log boom, only the part of it between depths d0 and d1 (in lanes from us): brook() draws it a slice at a
    time between the lanes, so a raft in a nearer lane passes in front of it and one further back behind it. Swung
    open it lies along the far bank, behind every raft (FK0004's first cut drew it over all of them)."""
    (nx, ny), (fx, fy) = boom_ends(x, open_)
    dfar = BOOM_FAR
    dnear = dfar - (FAR_DEPTH + 4) / LANE_DY * math.cos(open_ * math.pi / 2)
    if d0 <= dfar < d1:
        rect(c, fx - 8, fy - 70, fx + 8, fy + 6, TRUNK)             # the hinge post on the far bank
    if dfar - dnear < 1e-3:
        if not d0 <= dfar < d1:
            return
        v0, v1 = 0.0, 1.0
    else:
        v0 = min(1.0, max(0.0, (dfar - d1) / (dfar - dnear)))
        v1 = min(1.0, max(0.0, (dfar - d0) / (dfar - dnear)))
        if v1 <= v0:
            return
    p0, p1 = (lerp(fx, nx, v0), lerp(fy, ny, v0)), (lerp(fx, nx, v1), lerp(fy, ny, v1))
    _bar(c, p0, p1, 18, LOG * 0.8)
    _bar(c, (p0[0], p0[1] - 5), (p1[0], p1[1] - 5), 8, LOG * 1.05)
    if v1 >= 1.0:
        c.circle(nx, ny, 9, LOG_END)


def finish_rope(x=FINISH_X):
    ny, fy = surface(x) + BANK - 10, far_edge(x) - 40
    nx, fx = x - 24, x + FAR_DX + 10
    top_n, top_f = ny - 300, fy - 220
    n = 13
    pts = []
    for k in range(n + 1):
        u = k / n
        pts.append((lerp(nx, fx, u), lerp(top_n, top_f, u) + 160 * u * (1 - u)))
    return pts, (nx, ny), (fx, fy, top_f)


def draw_finish_back(c, s, t, lit=1.0):
    """The far post, the rope of little flags in the six colours, the finish lantern in the middle."""
    pts, _, (fx, fy, top_f) = finish_rope()
    rect(c, fx - 9, top_f, fx + 9, fy, TRUNK * 0.9)
    c.polyline(pts, ROPE * 0.8, 2)
    n = len(pts) - 1
    for k in range(1, n):
        if k == n // 2:
            continue
        col = np.asarray(MARBLE_COLS[KINDS[k % 6]], np.float64)
        px, py = pts[k]
        flap = 3 * math.sin(t * 3 + k)
        c.polygon([(px - 8, py), (px + 8, py), (px + flap, py + 20)], col * 0.9)
    lx, ly = pts[n // 2]
    c.line(lx, ly, lx, ly + 18, ROPE * 0.6, 2)
    c.polygon([(lx - 10, ly + 18), (lx + 10, ly + 18), (lx + 12, ly + 44), (lx - 12, ly + 44)],
              np.array([50, 50, 46]) + LAMP_C * 0.8 * lit)
    if lit > 0:
        s.glow_draw(lambda g: g.circle(lx, ly + 31, 70, LAMP_C * 0.5 * lit))


def draw_finish_front(c):
    """The near post (in front of lane 0)."""
    _, (nx, ny), _ = finish_rope()
    rect(c, nx - 10, ny - 300, nx + 10, ny + 8, TRUNK)
    c.line(nx - 12, ny - 300, nx + 12, ny - 300, TRUNK * 1.2, 4)


# ----- the rafts -----

DDX, DDY = 11.0, -17.0          # across a raft's deck on screen, from its near log to its far one


def mast_foot(x, y, th, sc=1.0):
    """Where the mast stands (for the sail being fitted)."""
    mx, my = DDX * 0.5 + 4, DDY * 0.5 - 6
    c, s = math.cos(th), math.sin(th)
    return x + sc * (c * mx - s * my), y + sc * (s * mx + c * my)


_MASKS = {}


def hide_under(c, pts, draw):
    """draw(), then put back what was there before inside the polygon pts (world units). The part of a raft or leaf
    under the waterline disappears and the water shows through in its own shade, streaks and all (FK0004's first cut
    drew a patch of water over it instead: a box in the wrong shade that followed the rafts, and fell ahead of them
    at the falls)."""
    img = c.target
    before = img.copy()
    draw()
    m = _MASKS.get(img.shape[:2])
    if m is None:
        m = _MASKS[img.shape[:2]] = np.zeros(img.shape[:2], np.uint8)
    c.target = m
    try:
        c.polygon(pts, (255, 255, 255))
    finally:
        c.target = img
    bx, by, bw, bh = cv2.boundingRect(m)
    if bw and bh:
        a = m[by:by + bh, bx:bx + bw, None].astype(np.float32) / 255.0
        roi = img[by:by + bh, bx:bx + bw]
        roi[:] = (roi * (1 - a) + before[by:by + bh, bx:bx + bw] * a + 0.5).astype(np.uint8)
        m[by:by + bh, bx:bx + bw] = 0


def draw_raft(c, x, y, th, L, col, sc=1.0, t=0.0, logs=4, cut=1.0, ties=2, mast=1.0, dye=1.0, water=None, wake=0.0,
              shade=1.0, ragged=None, slope=0.0):
    """A little log raft seen from the side and a little above: four logs side by side, two lashings, a mast with a big
    leaf for a sail in its Keeper's colour (dye 0 = the pale leaf). (x, y) = middle of the near log at the waterline,
    th = pitch. water: y of the water surface here (what is under it is hidden), slope: of the water surface, wake: how
    fast it moves through the water. Built bit by bit: logs 0..4 laid, cut 0..1 (the ragged ends trimmed), ties 0..2,
    mast 0..1 (planted)."""
    if water is not None:
        x0, x1 = x - (L / 2 + 30) * sc, x + (L / 2 + DDX + 30) * sc
        under = [(x0, water + 4 + slope * (x0 - x)), (x1, water + 4 + slope * (x1 - x)), (x1, water + 70 * sc),
                 (x0, water + 70 * sc)]
        hide_under(c, under, lambda: draw_raft(c, x, y, th, L, col, sc, t, logs, cut, ties, mast, dye, None, 0.0, shade,
                                               ragged))
        if y < water - 10:                                  # in the air (over a falls): no ripple at its waterline
            return
        xa, xb = x - L / 2 * sc - 8, x + (L / 2 + DDX) * sc + 10
        c.line(xa, water + 4 + slope * (xa - x), xb, water + 4 + slope * (xb - x), WATER * 1.4, 2)
        if wake > 20:
            k = min(1.0, wake / 200.0)
            c.line(xb - 6, water + 3, xb + 6, water - 1, FOAM * (0.4 + 0.4 * k), 2)
            c.line(xa + 4, water + 4, xa - 40 * k - 10, water + 2, FOAM * 0.35 * k + WATER * 0.5, 2)
        return
    cv = c
    c = Xform(cv, 0.0, 0.0, th, sc, x, y)
    h = L / 2
    if logs >= 4:                                           # the deck: the tops of the four logs, seen from above
        c.polygon([(x - h, y - 6), (x + h, y - 6), (x + h + DDX, y + DDY - 6), (x - h + DDX, y + DDY - 6)],
                  LOG * shade * 1.12)
    for k in reversed(range(4)):                           # far log first
        if k >= logs:
            continue
        u0 = k / 3.0
        ox, oy = DDX * u0, DDY * u0
        ex = ragged[k] * (1 - cut) if ragged is not None else 0.0
        w = 7.0
        top = LOG * shade * (1.08 - 0.05 * k)
        c.polygon([(x - h + ox, y + oy - w), (x + h + ex + ox, y + oy - w), (x + h + ex + ox, y + oy + w),
                   (x - h + ox, y + oy + w)], top * 0.82)
        c.line(x - h + ox, y + oy - w * 0.45, x + h + ex + ox, y + oy - w * 0.45, top, 5)
        c.circle(x + h + ex + ox, y + oy, w, LOG_END * shade * 0.95)
        c.circle(x + h + ex + ox, y + oy, w * 0.45, LOG_END * shade * 0.72, False, 1.5)
    for q in range(ties):                                   # the lashings across the deck
        lx = x + (-0.3 if q == 0 else 0.3) * L
        c.line(lx, y + 7, lx + DDX, y + DDY - 7, ROPE * shade, 4)
        c.line(lx + 6, y + 7, lx + 6 + DDX, y + DDY - 7, ROPE * shade * 0.85, 3)
    if mast > 0:
        mx, my = x + DDX * 0.5 + 4, y + DDY * 0.5 - 6
        mh = 78.0 * mast
        c.line(mx, my, mx, my - mh, TRUNK * 1.15 * shade, 5)
        if mast >= 1:
            scol = lerp(SAIL_RAW, np.asarray(col, np.float64), dye) * shade
            fl = 4 * math.sin(t * 3.1 + x * 0.01)
            leaf = [(mx + 3, my - 76), (mx + 28 + fl, my - 66), (mx + 46 + fl, my - 42), (mx + 36 + fl * 0.6, my - 18),
                    (mx + 3, my - 10)]
            c.polygon(leaf, scol)
            c.polyline(leaf, scol * 0.7, 2, closed=True)
            c.line(mx + 3, my - 72, mx + 30 + fl * 0.8, my - 32, scol * 0.65, 2)
            c.line(mx + 14, my - 54, mx + 30 + fl, my - 58, scol * 0.75, 1.5)
            c.line(mx + 14, my - 34, mx + 34 + fl, my - 28, scol * 0.75, 1.5)
            c.polygon([(mx, my - mh), (mx - 16, my - mh + 5 + fl * 0.3), (mx, my - mh + 10)], scol * 1.05)


def raft_sail_center(x, y, th, sc=1.0):
    mx, my = mast_foot(x, y, th, sc)
    return mx + 24 * sc, my - 44 * sc
