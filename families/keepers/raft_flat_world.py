"""Forest Keepers episode 8, The River Raft Race, in the flat picture-book look: the world (the brook, its two little
falls, the raft line on the bank, the race physics). Story and staging: docs/engines/forest_keepers_raft_flat.md;
the episode itself is raft_flat.py.

We look at the brook from the side and a little from above. The Keepers' path runs along the near bank at the bottom
of the frame; behind it a strip of meadow, then the brook (six lanes in depth, lane 0 nearest), then the far bank and
the autumn hills. The brook runs left to right down the valley in steps, and the path follows it down:

    F0  a little falls above the start pool (the leaf with the ladybird comes over it)
        the start pool + the raft line on the bank (stations 1-3, the slipway), the start boom
        the riffle over stones
    F1  the first little falls (the race)
        the lily pool, the rapids
    F2  the second little falls
        the long glide, the finish line, the finish pool and its boom

The falls are smooth chutes of glassy water (owner rule: rafts lie flat on the water, never nose-up): a raft rides
down the sloping water parallel to it, nose down, and levels out below, where the water circles back (the hole) and
can hold it for a moment until a surge flushes it out.

World x is the ground layer's own px. Everything here is a pure function of x and t (no state), so frames render in
parallel.
"""
import math

import numpy as np
import skia

from .flat import PAL, bush, cloud, hill_band, lolly_tree, pine, poplar, tuft
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
K = 0.72
G_LO = H * 0.93                    # the path below the last falls (the finish)
DROP = 64.0                        # each little falls lowers the water (and the path beside it) this much on screen
CW = 96.0                          # a falls' chute: from its lip to its foot
RAMP = 560.0                       # the path eases down beside a falls over this far either side
BANK = 92.0                        # path to the water's near edge on the level stretches (the meadow)
LANE0, LANE_DY = 24.0, 25.0        # lane 0's waterline above the near edge; each lane further back is this much higher
N_LANES = 6
DEPTH = LANE0 + LANE_DY * (N_LANES - 1) + 22.0    # near edge to far edge of the water
LANE_SC = 0.035                    # each lane further back is drawn this much smaller

F0, F1, F2 = 700.0, 3990.0, 5290.0  # the falls' lips
FALLS = (F0, F1, F2)
HOLE = 200.0                       # below a falls' foot the water circles back this far

# the raft line on the bank (x of each Keeper's place and each station's middle)
TREE = 950.0                      # the old maple Springs shakes the leafy twigs from
SPOT = dict(springs=1040.0, wheels=1600.0, teeth=1952.0, tentacles=2390.0, digger=2838.0)
ST = [1809.0, 2145.0, 2635.0]      # station 1 (logs + trim), 2 (lashing), 3 (mast + sail)
SLIP = 3041.0                      # the slipway: the rails curve down into the start pool here
START_BOOM = 3400.0
FINISH = 6120.0
END_BOOM = 6470.0
WORLD = 9000.0

RAFT_L = 150.0                     # every raft trimmed to this at the chalk line (lane-0 px)


def _ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ----------------------------------------------------------------------------------------------- the land

def _ramp(x, f):
    """0 above falls f, 1 below it: how far the path has come down beside it."""
    return _ss((x - (f - RAMP)) / (2 * RAMP + CW))


def ground(x):
    """The path (a Keeper's feet) at world x."""
    return G_LO - DROP * (3 - sum(_ramp(x, f) for f in FALLS))


def ground_slope(x, h=6.0):
    return (ground(x + h) - ground(x - h)) / (2 * h)


def chute(u):
    """A falls' water profile 0..1 over its chute (u 0 lip .. 1 foot): rounded over the lip, steep, easing out at the
    foot."""
    u = min(max(u, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * u)


def level(x):
    """How far the water has come down (screen px) at x: one DROP per falls passed."""
    d = 0.0
    for f in FALLS:
        d += DROP * chute((x - f) / CW)
    return d


def near_edge(x):
    """y of the water's near edge (where the meadow meets it)."""
    return G_LO - 3 * DROP - BANK + level(x)


def lane_y(j, x):
    """Lane j's waterline (the calm surface) at x."""
    return near_edge(x) - LANE0 - LANE_DY * j


def lane_sc(j):
    return 1.0 - LANE_SC * j


def far_edge(x):
    return near_edge(x) - DEPTH


# We look a little from the left as well: everything further back across the brook is drawn a little to the right,
# so a log or a line lying straight across the water (a boom, the finish) reads as a slanted line across it.
DX = 16.0                                   # screen px right per lane further back
D_NEAR = -LANE0 / LANE_DY                   # the near edge's lane depth (drawn where its world x is)
D_FAR = (DEPTH - LANE0) / LANE_DY           # the far edge's
FDX = DX * (D_FAR - D_NEAR)                 # the far bank is drawn this far right of its world x


def at_depth(x, d):
    """Screen-world x of a point at world x and lane depth d (subtract the camera shift for the screen)."""
    return x + DX * (d - D_NEAR)


def on_chute(x):
    for f in FALLS:
        if f <= x <= f + CW:
            return f
    return None


def surface_slope(x, h=3.0):
    return (level(x + h) - level(x - h)) / (2 * h)


# ----------------------------------------------------------------------------------------------- the water

# (kind, x0, x1, current px/s, chop): the current of each stretch (lane 0..5 vary a little, LANE_FLOW)
STRETCHES = [
    ("pool", -400.0, F0, 55.0, 1.0),
    ("pool", F0 + CW, START_BOOM, 62.0, 1.0),
    ("riffle", START_BOOM, F1, 150.0, 3.5),
    ("pool", F1 + CW, 4620.0, 78.0, 1.2),
    ("rapids", 4620.0, F2, 205.0, 4.5),
    ("glide", F2 + CW, FINISH + 120.0, 128.0, 2.0),
    ("pool", FINISH + 120.0, WORLD + 400.0, 40.0, 1.0),
]
LANE_FLOW = {"pool": [1.0, 0.98, 1.0, 1.02, 1.0, 1.0], "riffle": [1.06, 1.03, 1.0, 0.97, 0.96, 0.98],
             "rapids": [0.95, 0.97, 1.0, 1.01, 1.04, 1.05], "glide": [1.0, 0.99, 1.02, 1.02, 0.99, 0.98]}
CHUTE_V = 250.0                    # the water down a chute
# how hard the water circles back below each race falls, per lane (px/s)
HOLE_PULL = {F1: [128.0, 152.0, 170.0, 160.0, 140.0, 134.0], F2: [146.0, 166.0, 154.0, 178.0, 166.0, 140.0],
             F0: [60.0] * 6}
# stones sticking up through the riffle and the rapids: (x, lane) - a raft's lane runs beside them, never into them;
# they show where the water runs fast
STONES = [(3560.0, 2.5), (3700.0, 0.5), (3840.0, 4.5), (4760.0, 3.5), (4930.0, 1.5), (5100.0, 5.4), (5180.0, 0.5)]
LILY = [(4190.0, 4.6), (4290.0, 5.3), (4460.0, 5.0), (4540.0, 4.2)]


def stretch(x):
    for st in STRETCHES:
        if x < st[2]:
            return st
    return STRETCHES[-1]


def current(x, lane, t):
    """Downstream speed of the water at x in lane `lane` (negative in a hole below a falls)."""
    f = on_chute(x)
    if f is not None:
        return CHUTE_V
    st = stretch(x)
    u = st[3] * LANE_FLOW.get(st[0], LANE_FLOW["pool"])[int(lane)]
    for k, f in enumerate(FALLS):
        foot = f + CW
        if foot <= x < foot + HOLE:
            s = (x - foot) / HOLE
            # the hole breathes: now and then a surge of water comes through and flushes it downstream
            surge = max(0.0, math.sin(2 * math.pi * t / (2.1 + 0.25 * k) + lane * 1.7 + k))
            back = HOLE_PULL[f][int(lane)] * (1.0 - 2.5 * surge)
            u = -back + (u + back) * _ss(s)
    return u


def wave(x, t, lane, amp=None):
    """Little waves running down the stream (px, up is negative)."""
    a = stretch(x)[4] if amp is None else amp
    return a * (0.6 * math.sin(x * 0.045 - t * 5.0 + lane * 1.3) + 0.4 * math.sin(x * 0.11 - t * 7.3 + lane * 2.1))


def breeze(t):
    """The breeze down the valley (px/s^2 on a sail of size 1)."""
    return 14.0 + 9.0 * math.sin(0.7 * t + 0.4) + 4.0 * math.sin(1.9 * t + 2.0)


# ----------------------------------------------------------------------------------------------- the race

REC_HZ = 120
SIM_HZ = 480


class Trait:
    def __init__(self, mass, drag, sail):
        self.mass, self.drag, self.sail = mass, drag, sail


def traits(seed):
    rs = np.random.default_rng(1000 + seed)
    # every raft is trimmed to the same length at the chalk line; they differ in the wood (weight), how the logs sit
    # in the water (drag) and the leaf each one got for a sail
    return [Trait(float(rs.uniform(0.84, 1.18)), float(rs.uniform(0.84, 1.16)), float(rs.uniform(0.65, 1.35)))
            for _ in range(N_LANES)]


WAIT_X = START_BOOM - RAFT_L / 2 - 8.0        # a raft's middle, waiting at the start boom


class Run:
    """One raft down the brook in its lane, from the boom opening (tau 0). rec rows: x, vx."""

    def __init__(self, trait, lane, t_max=60.0, t_off=0.0):
        tr = trait
        dt = 1.0 / SIM_HZ
        x, v = WAIT_X, 0.0
        rec = []
        self.finish_t = self.boom_t = None
        every = SIM_HZ // REC_HZ
        self.events = []
        last_hold = -9.0
        for i in range(int(t_max * SIM_HZ)):
            tau = i * dt
            t = tau + t_off
            u = current(x, lane, t)
            rel = u - v
            a = rel * (1.25 + 0.011 * abs(rel)) * tr.drag / tr.mass + breeze(t) * tr.sail / tr.mass
            f = on_chute(x)
            if f is not None:                                     # down the chute: gravity along the water
                a += 700.0 * surface_slope(x) / math.hypot(1.0, surface_slope(x))
            for ff in FALLS:                                       # the foot of a falls pushes a raft back out of it
                foot = ff + CW
                if foot - 10 <= x < foot + 30:
                    a += 520.0 * (1 - (x - foot + 10) / 40)
            v += a * dt
            x += v * dt
            if v < -5 and tau - last_hold > 1.0:
                self.events.append((tau, "held", x))
                last_hold = tau
            if x > END_BOOM - RAFT_L / 2 - 5 - 3 * lane and v > 0:   # the boom catches it
                if self.boom_t is None:
                    self.boom_t = tau
                    self.events.append((tau, "boom", x, min(1.0, v / 120.0)))
                x = END_BOOM - RAFT_L / 2 - 5 - 3 * lane
                v = -0.2 * v
            if self.finish_t is None and x + RAFT_L / 2 >= FINISH:
                self.finish_t = tau
            if i % every == 0:
                rec.append((x, v))
            if self.boom_t is not None and tau > self.boom_t + 14.0:
                break
        self.rec = np.array(rec)
        self.lane = lane

    def at(self, tau):
        """(x, vx) at tau s after the start (holds the first and last rows)."""
        f = max(0.0, tau) * REC_HZ
        i = int(min(len(self.rec) - 2, f))
        u = min(1.0, max(0.0, f - i))
        a, b = self.rec[i], self.rec[i + 1]
        return float(a[0] + (b[0] - a[0]) * u), float(a[1] + (b[1] - a[1]) * u)


class Race:
    """Six rafts released together: the finish order and the lead changes as a viewer sees them."""

    def __init__(self, seed, t_off=0.0):
        self.seed = seed
        self.traits = traits(seed)
        self.runs = [Run(tr, j, t_off=t_off) for j, tr in enumerate(self.traits)]
        self.finish = [r.finish_t if r.finish_t is not None else 999.0 for r in self.runs]
        self.order = sorted(range(N_LANES), key=lambda i: self.finish[i])
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
            if best != last and prog[best] > prog[last] + 26.0:  # clearly ahead (a sixth of a raft) for half a second
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
        self.last_change_x = self.runs[self.leaders[-1][1]].at(self.leaders[-1][0])[0]
        self.max_spread = max(max(r.at(f / 10)[0] for r in self.runs) - min(r.at(f / 10)[0] for r in self.runs)
                              for f in range(int(min(self.finish) * 10)))

    def standings(self, tau):
        def key(i):
            if self.finish[i] <= tau:
                return (0, self.finish[i])
            return (1, -self.runs[i].at(tau)[0])
        return sorted(range(N_LANES), key=key)

    def holds(self):
        return [round(float(np.sum(r.rec[:, 1] < -5)) / REC_HZ, 2) for r in self.runs]


def raft_pose(j, x, t, L=RAFT_L):
    """(y of its near waterline, pitch deg, scale) of a raft in lane j with its middle at x: it lies along the water
    (parallel to it, so down a chute it is nose down; never nose up), bobbing on the little waves."""
    s = lane_sc(j)
    h = L * s / 2
    yl, yr = lane_y(j, x - h), lane_y(j, x + h)
    pitch = math.degrees(math.atan2(yr - yl, 2 * h))
    pitch = max(0.0, pitch)                       # nose down (or level) only
    y = (yl + yr) / 2 + 0.5 * (wave(x - h * 0.5, t, j) + wave(x + h * 0.5, t, j)) * (0.0 if on_chute(x) else 1.0)
    return y, pitch, s


# ----------------------------------------------------------------------------------------------- colours

WATER_C = (112, 146, 164)
WATER_FAR = (138, 168, 178)
WATER_DEEP = (96, 128, 148)
FOAM = (232, 238, 234)
STONE = (150, 140, 128)
STONE_D = (118, 110, 102)
LOG = (170, 128, 88)
LOG_TOP = (196, 152, 106)
LOG_END = (224, 188, 140)
LOG_RING = (176, 132, 92)
TWINE = (220, 196, 140)
MAST = (126, 96, 70)
LEAF_RAW = (214, 150, 92)           # a plain autumn leaf (soft russet) before Glo's light colours it
GRASS = (152, 160, 92)
GRASS_D = (128, 138, 78)
MEADOW = (170, 172, 104)
GRAVEL = (196, 178, 140)
EARTH = (160, 124, 92)
BANK_FACE = (140, 112, 86)
TRUNK = (128, 96, 72)
RAIL = (150, 110, 76)

COLS = {"wheels": (64, 112, 196), "tentacles": (224, 112, 30), "teeth": (138, 76, 196), "springs": (214, 166, 40),
        "lantern": (40, 170, 158), "digger": (200, 74, 54)}


# ----------------------------------------------------------------------------------------------- sky + light

LIGHT = [(0.0, "day")]
PRESETS = {      # sky top, mid, low; light multiplier; sun (alpha, x, y as fractions of the frame)
    "day": ("#bccbd4", "#ece5d6", "#f2dcc8", (1.0, 1.0, 1.0), (0.7, 0.8, 0.18)),
    "gold": ("#a9b6c8", "#f0d8bc", "#f4bf96", (1.03, 0.97, 0.9), (0.85, 0.82, 0.32)),
    "evening": ("#7f88aa", "#d6a6a2", "#efb38c", (0.93, 0.86, 0.86), (0.9, 0.86, 0.5)),
}


def light_at(t):
    keys = LIGHT
    if t <= keys[0][0] or len(keys) == 1:
        return keys[0][1], keys[0][1], 0.0
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return a, b, _ss((t - t0) / max(t1 - t0, 1e-6))
    return keys[-1][1], keys[-1][1], 0.0


def sky(pg, t):
    a, b, u = light_at(t)
    A, B = PRESETS[a], PRESETS[b]
    top, mid, low = (mix(A[i], B[i], u) for i in range(3))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.62)], [C(top), C(mid), C(low)], [0, 0.55, 1])
    pg.c.drawPaint(skia.Paint(Shader=sh))
    sa, sx, sy = (p + (q - p) * u for p, q in zip(A[4], B[4]))
    if sa > 0.02:
        r = 44.0
        pg.glow(W * sx, H * sy, r * 7, "#ffe2a8", 0.45 * sa)
        pg.flat(oval(W * sx, H * sy, r, r), "#fff2d2", sa)
    pg.grain_opaque()


def apply_light(pg, t):
    a, b, u = light_at(t)
    mul = np.array([p + (q - p) * u for p, q in zip(PRESETS[a][3], PRESETS[b][3])], np.float32)
    if np.allclose(mul, 1.0):
        return
    import cv2
    img = pg.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    M = np.array([[mul[0], 0, 0, 0], [0, mul[1], 0, 0], [0, 0, mul[2], 0]], np.float32)
    img[..., :3] = cv2.transform(np.ascontiguousarray(img[..., :3]), M)
    pg.c.drawImage(skia.Image.fromarray(np.ascontiguousarray(img), colorType=skia.ColorType.kRGBA_8888_ColorType),
                   0, 0)


# ----------------------------------------------------------------------------------------------- static layers

def _hills(p, y, amp, seed, col, step=520.0, slope=0.0, light_=0.05, dark=0.06):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0) + slope * x) for x in xs]
    return hill_band(p, pts, H, col, light_, dark)


def _clouds(p):
    rs = np.random.default_rng(21)
    x = 120.0
    while x < p.strip:
        cloud(p, x, H * rs.uniform(0.08, 0.2), W * rs.uniform(0.1, 0.16))
        x += rs.uniform(420, 760)


def _far(p):
    _hills(p, H * 0.4, H * 0.08, 31, PAL["far"], 640.0, 0.004)


def _far2(p):
    _hills(p, H * 0.45, H * 0.05, 32, PAL["far2"], 560.0, 0.005)


def _far_trees(p):
    rs = np.random.default_rng(33)
    x = 30.0
    while x < p.strip:
        y = H * 0.47 + 0.006 * x
        if rs.random() < 0.5:
            pine(p, x, y, H * rs.uniform(0.06, 0.085), tone(PAL["pine"], 0.2))
        else:
            lolly_tree(p, x, y, H * rs.uniform(0.06, 0.08), tone((PAL["ochre"], PAL["orange"], PAL["olive"])[
                int(rs.integers(3))], 0.15))
        x += rs.uniform(60, 130)


def _mid(p):
    """The wooded slope across the brook (it falls away to the right with the valley)."""
    rs = np.random.default_rng(34)
    pts = [(x, H * 0.5 + 0.011 * x + rs.uniform(-12, 12)) for x in np.arange(-200.0, p.strip + 400, 380.0)]
    hill_band(p, pts, H, PAL["mid"], 0.05, 0.05)
    x = 40.0
    while x < p.strip:
        y = H * 0.51 + 0.011 * x
        kind = rs.integers(3)
        hh = H * rs.uniform(0.13, 0.2)
        col = (PAL["ochre"], PAL["orange"], PAL["pine"], PAL["olive"], PAL["pink"])[int(rs.integers(5))]
        (poplar, lolly_tree, pine)[int(kind)](p, x, y, hh, col)
        x += rs.uniform(110, 230)


def _far_bank(p):
    """The bank across the brook: a grassy slope down to the far water's edge, with stones along the water and the
    rock steps of the three falls; a few trees and reeds on it."""
    xw = np.arange(-300.0, p.strip + 60, 30.0)
    top = [(x + FDX, far_edge(x) - 70 - 14 * math.sin(x / 530.0)) for x in xw]
    edge = [(x + FDX, far_edge(x) + 2) for x in xw[::-1]]
    p.grad(smooth(top + edge), tone(MEADOW, 0.04), tone(GRASS_D, -0.02))
    p.flat(smooth([(x, y + 1) for x, y in top] + [(x, y - 52) for x, y in edge]), tone(MEADOW, 0.08), 0.5, blur=6)
    rs = np.random.default_rng(41)
    for x in np.arange(-200.0, p.strip, 34.0):                 # stones along the water's edge
        if on_chute(x + 20) or on_chute(x - 20):
            continue
        xx = x + rs.uniform(-8, 8)
        y = far_edge(xx) - 3
        r = rs.uniform(10, 18)
        p.shape(oval(xx + FDX, y, r, r * 0.5), tone(STONE, rs.uniform(-0.08, 0.06)), 0.12)
    for f in FALLS:                                            # the rock step of each falls on the far side
        y0, y1 = far_edge(f - 2), far_edge(f + CW + 2)
        x = f + FDX
        p.shape(smooth([(x - 34, y0 - 30), (x + 26, y0 - 34), (x + CW + 24, y1 - 10), (x + CW + 30, y1 + 4),
                        (x - 6, y1 + 4), (x - 38, y0 + 2)]), STONE_D, 0.14)
        p.shape(smooth([(x - 26, y0 - 28), (x + 22, y0 - 32), (x + 26, y0 - 4), (x - 22, y0 + 2)]), STONE, 0.1)
    for x in (430.0, 2480.0, 4440.0, 5740.0, 6840.0, 8000.0):  # a few trees on the far bank
        y = far_edge(x) - 52
        if x in (2480.0, 6840.0):
            pine(p, x + FDX, y, 300, tone(PAL["pine"], 0.04))
        else:
            lolly_tree(p, x + FDX, y, 330, (PAL["orange"], PAL["ochre"])[int(x) % 2])
    for x in np.arange(60.0, p.strip, 140.0):                   # reeds at the water's edge here and there
        rx = x + rs.uniform(-30, 30)
        if rs.random() < 0.45 and not any(abs(rx - f - 40) < 120 for f in FALLS) and abs(rx - LADY_REED) > 120:
            _reeds(p, rx + FDX, far_edge(rx) - 4, rs)
    _reeds(p, LADY_REED + FDX, far_edge(LADY_REED) - 4, np.random.default_rng(7), n=6, h=56.0)
    for x in DUCK_REEDS:                                       # the reed bed the ducks paddle out of
        _reeds(p, x + FDX, far_edge(x) - 2, np.random.default_rng(int(x)), n=9, h=70.0)


LADY_REED = 1260.0                  # the reed the ladybird flies to
DUCK_REEDS = (6200.0, 6280.0, 6360.0)


def _reeds(p, x, y, rs, n=5, h=46.0):
    for k in range(n):
        dx = (k - n / 2) * 6 + rs.uniform(-2, 2)
        hh = h * rs.uniform(0.7, 1.1)
        lean = rs.uniform(-8, 8)
        p.stroke(skia.Path().moveTo(x + dx, y).quadTo(x + dx + lean * 0.4, y - hh * 0.6, x + dx + lean, y - hh),
                 tone(GRASS_D, -0.08), 3.0)
        if k % 2 == 0:
            p.shape(rrect(x + dx + lean - 3.5, y - hh - 16, x + dx + lean + 3.5, y - hh + 2, 3), (138, 96, 66), 0.0)


def _meadow(p):
    """The near bank: from the water's near edge down to the path, the path itself, and the bank in front of it to the
    bottom of the frame. The raft line's rails and the slipway are drawn live (they are built on)."""
    xs = np.arange(-100.0, p.strip + 60, 24.0)
    edge = [(x, near_edge(x) - 1) for x in xs]
    bottom = [(x, H + 10) for x in xs[::-1]]
    p.grad(smooth(edge + bottom), MEADOW, tone(GRASS, -0.04))
    # wet stones and gravel along the water's edge
    rs = np.random.default_rng(51)
    p.flat(smooth(edge + [(x, near_edge(x) + 16) for x in xs[::-1]]), tone(GRAVEL, -0.12), 0.9)
    for x in np.arange(0.0, p.strip, 28.0):
        if on_chute(x + 10) or on_chute(x - 10):
            continue
        xx = x + rs.uniform(-6, 6)
        r = rs.uniform(9, 15)
        p.shape(oval(xx, near_edge(xx) + 4, r, r * 0.45), tone(STONE, rs.uniform(-0.12, 0.02)), 0.12)
    for f in FALLS:                                            # the rock step of each falls on our side
        y0, y1 = near_edge(f - 2), near_edge(f + CW + 2)
        p.shape(smooth([(f - 40, y0 + 2), (f + 10, y0 - 4), (f + CW + 10, y1 - 2), (f + CW + 34, y1 + 14),
                        (f - 4, y1 + 18), (f - 46, y0 + 20)]), STONE_D, 0.14)
        for dx, dy, r in ((-24, 6, 16), (30, 34, 14), (CW, y1 - y0 + 8, 13)):
            p.shape(oval(f + dx, y0 + dy, r, r * 0.55), STONE, 0.12)
    # the path: trodden earth along the bank
    top = [(x, ground(x) - 30) for x in xs]
    bot = [(x, ground(x) + 34) for x in xs[::-1]]
    p.flat(smooth(top + bot), PAL["path"], 0.75)
    p.flat(smooth([(x, y + 10) for x, y in top] + [(x, y - 12) for x, y in bot]), tone(PAL["path"], 0.06), 0.5)
    # tufts, fallen leaves and pebbles on the meadow and the bank (none on the stations or the path itself)
    for i in range(int(p.strip / 30)):
        x = rs.uniform(0, p.strip)
        y = rs.uniform(near_edge(x) + 22, H)
        if abs(y - ground(x)) < 40 or (ST[0] - 120 < x < SLIP + 90 and y < ground(x)):
            continue
        r = rs.random()
        if r < 0.45:
            tuft(p, x, y, rs.uniform(12, 20) * (0.8 + 0.5 * (y - near_edge(x)) / 200), tone(GRASS_D, -0.08))
        elif r < 0.85:
            from .flat import leaf
            leaf(p, x, y, 6.0, rs.uniform(0, 180), (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])
        else:
            p.flat(oval(x, y, 5, 3), tone(STONE, -0.05), 0.8)
    # the maple Springs shakes (in the meadow at the start pool's left end)
    _maple(p, TREE, near_edge(TREE) + 30)


def _maple(p, x, y):
    """The old maple: a stout trunk, one long low branch out to the right over the path (Springs can reach it), a
    round autumn crown. The low branch's leafy twigs are drawn live (they come off)."""
    p.shape(tube([(x, y), (x + 6, y - 180), (x - 4, y - 330)], 30, 18), TRUNK, 0.12, (-0.5, 0.0))
    p.shape(tube(MAPLE_BRANCH[:2], 12, 7), TRUNK, 0.1, (0.0, -0.4))
    for dx, dy, r, col in ((-110, -400, 115, PAL["orange"]), (30, -440, 125, PAL["ochre"]), (-40, -510, 110,
                           tone(PAL["orange"], 0.05)), (110, -390, 80, tone(PAL["ochre"], -0.04)),
                           (-170, -330, 80, PAL["pink"])):
        p.shape(oval(x + dx, y + dy, r, r * 0.92), col, 0.1)


MAPLE_BRANCH = [(TREE + 8, near_edge(TREE) + 30 - 205), (TREE + 110, near_edge(TREE) + 30 - 262),
                (TREE + 290, near_edge(TREE) + 30 - 286)]


def _fg(p):
    """A few soft foreground ferns and grasses along the bottom edge (nearer than the path)."""
    rs = np.random.default_rng(61)
    x = 80.0
    while x < p.strip:
        y = H + 6
        if ground(x) < H - 120:
            for k in range(5):
                a = -math.pi / 2 + (k - 2) * 0.32
                L = rs.uniform(60, 90)
                p.stroke(skia.Path().moveTo(x, y).quadTo(x + math.cos(a) * L * 0.5, y + math.sin(a) * L * 0.7,
                                                         x + math.cos(a) * L, y + math.sin(a) * L),
                         tone(GRASS_D, -0.16), 6.0)
        x += rs.uniform(260, 520)


def layers():
    return [("clouds", 0.03, _clouds), ("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees),
            ("mid", 0.4, _mid), ("far_bank", 1.0, _far_bank), ("meadow", 1.0, _meadow), ("fg", 1.12, _fg)]


# ----------------------------------------------------------------------------------------------- live water

def draw_water(pg, t, sh):
    """The brook in the view: the water band (lighter towards the far bank), soft light on it, flow streaks fixed in
    the brook, chop in the fast water, the falls' chutes and the foam at their feet."""
    x0, x1 = sh - 200, sh + W + 60
    c = pg.c
    xw = np.arange(x0, x1 + 16, 16.0)
    band = smooth([(x + FDX - sh, far_edge(x) - 2) for x in xw] + [(x - sh, near_edge(x) + 4) for x in xw[::-1]])
    b = band.getBounds()
    pg.c.drawPath(band, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, b.top()), (0, b.bottom())], [C(WATER_FAR), C(WATER_C), C(WATER_DEEP)], [0.0, 0.6, 1.0])))
    c.save()
    c.clipPath(band, doAntiAlias=True)
    for k in range(int(x0 // 300), int(x1 // 300) + 1):        # soft light along the far half (the sky in the water)
        x = k * 300.0 + 80 * math.sin(k * 1.7)
        if any(f - 80 < x < f + CW + 80 for f in FALLS):
            continue
        for q in range(2):
            d = 4.2 - q
            y = lane_y(d, x) - 2 + 1.5 * math.sin(t * 1.3 + k + q)
            w = 60 - 18 * q + 10 * math.sin(t * 0.9 + k * 2.1 + q)
            xx = at_depth(x, d) - sh
            pg.flat(rrect(xx - w, y - 2, xx + w, y + 2, 2), tone(WATER_FAR, 0.25), 0.55 - 0.15 * q)
    _streaks(pg, t, sh, x0, x1)
    for f in FALLS:
        if x0 - 300 < f < x1 + 100:
            _falls(pg, t, sh, f)
    c.restore()


def _streaks(pg, t, sh, x0, x1):
    """Lines on the water moving downstream with the current, each riding through its own fixed cell of the brook
    (so the camera never drags them along) and fading in and out at the ends of its cell."""
    for j in range(N_LANES):
        d = j + 0.45
        spacing = 120.0 + 21 * j
        for k in range(int(math.floor(x0 / spacing)), int(x1 / spacing) + 1):
            base = k * spacing
            if any(f - 30 < base + spacing and base < f + CW + 20 for f in FALLS):
                continue
            st = stretch(base)
            u = st[3] * LANE_FLOW.get(st[0], LANE_FLOW["pool"])[j]
            ph = (u * t * 0.9 / spacing + 0.37 * k + 0.29 * j) % 1.0
            x = base + ph * spacing
            ln = (16 + u * 0.12) * lane_sc(j)
            a = math.sin(math.pi * ph)
            if a <= 0.05:
                continue
            y = lane_y(d, x) + 1.5 * math.sin(x * 0.03 + t * 3)
            sx = at_depth(x, d) - sh
            fast = st[0] in ("riffle", "rapids")
            pg.stroke(skia.Path().moveTo(sx, y).lineTo(sx + ln, y), tone(WATER_C, 0.32 + 0.18 * fast),
                      2.2 * lane_sc(j), 0.75 * a)
            if fast and (k + j) % 2 == 0:                      # chop: a little white crest
                cx = sx + ln * 0.5
                pg.stroke(skia.Path().moveTo(cx - 7, y - 3).quadTo(cx, y - 7, cx + 7, y - 3),
                          FOAM, 2.0 * lane_sc(j), 0.6 * a)


def _falls(pg, t, sh, f):
    """A little falls: a smooth glassy chute over the rock step (bright as it curves over the lip), white strands
    sliding down it at every depth, and the boil of foam at its foot."""
    xw = np.linspace(f - 4, f + CW + 4, 16)
    top = [(x + FDX - sh, far_edge(x) - 1) for x in xw]
    bot = [(x - sh, near_edge(x) + 3) for x in xw[::-1]]
    pg.flat(smooth(top + bot), tone(WATER_FAR, 0.18), 0.95)
    lip = [(at_depth(f + u, D_FAR) - sh, far_edge(f + u)) for u in (-10, 34)] + \
          [(at_depth(f + u, D_NEAR) - sh, near_edge(f + u) + 2) for u in (34, -10)]
    pg.flat(smooth(lip), tone(WATER_FAR, 0.45), 0.6)
    for k in range(26):                                        # strands sliding down the chute, at every depth
        d = D_NEAR + 0.3 + (k + 0.5) / 26 * (D_FAR - D_NEAR - 0.6)
        ph = (t * 1.4 + k * 0.618) % 1.0
        u0, u1 = ph * 0.7, min(1.0, ph * 0.7 + 0.34)
        p = skia.Path()
        for i in range(7):
            u = u0 + (u1 - u0) * i / 6
            x = f + CW * u
            (p.moveTo if i == 0 else p.lineTo)(at_depth(x, d) - sh, near_edge(x) - LANE0 - LANE_DY * (d - 0.0) +
                                              LANE0 * 0.0)
        pg.stroke(p, FOAM, 2.4, 0.4 + 0.45 * math.sin(math.pi * ph))
    foot = f + CW
    for k in range(16):                                        # the boil at the foot, across the brook
        d = D_NEAR + 0.4 + (k + 0.5) / 16 * (D_FAR - D_NEAR - 0.7)
        x = foot + 6 + 10 * math.sin(t * 2.6 + k * 1.3)
        y = near_edge(x) - LANE0 - LANE_DY * d + 2
        r = (9 + 3.5 * math.sin(t * 6 + k * 1.9)) * lane_sc(max(d, 0))
        sx = at_depth(x, d) - sh
        pg.flat(oval(sx, y, r * 1.7, r * 0.75), FOAM, 0.9)
        pg.flat(oval(sx + 28 + 4 * math.sin(t * 2.0 + k), y + 1, r * 1.2, r * 0.5), FOAM, 0.6)
        pg.flat(oval(sx + 56 + 4 * math.sin(t * 1.5 + k), y + 2, r * 0.9, r * 0.32), FOAM, 0.4)


def draw_stone(pg, x, j, t, sh):
    """A stone sticking up through the fast water, the water piling white against it."""
    s = lane_sc(j)
    y = lane_y(j, x)
    sx = at_depth(x, j) - sh
    pg.shape(smooth([(sx - 22 * s, y + 3), (sx - 12 * s, y - 13 * s), (sx + 8 * s, y - 16 * s), (sx + 24 * s, y + 3)]),
             STONE, 0.14)
    ph = 0.5 + 0.5 * math.sin(t * 8 + x)
    pg.stroke(skia.Path().moveTo(sx - 26 * s, y + 2).quadTo(sx - 20 * s, y - 6 * s, sx - 12 * s, y - 4 * s),
              FOAM, 2.5 * s, 0.6 + 0.3 * ph)
    for d in (-1, 1):
        pg.stroke(skia.Path().moveTo(sx + 22 * s, y + 1).lineTo(sx + 60 * s, y + d * 4 * s), FOAM, 2.0 * s, 0.4)


def draw_lily(pg, x, j, t, sh, k=0):
    s = lane_sc(j)
    xx, yy = at_depth(x, j) + 5 * math.sin(t * 0.4 + x) - sh, lane_y(j, x) + 1
    pad = skia.Op(oval(xx, yy, 30 * s, 8 * s), skia.Path().moveTo(xx, yy).lineTo(xx + 34 * s, yy - 3).lineTo(
        xx + 34 * s, yy + 6).close(), skia.PathOp.kDifference_PathOp)
    pg.shape(pad, (96, 140, 86), 0.1)
    if k % 2 == 0:
        pg.flat(oval(xx - 9 * s, yy - 5 * s, 7 * s, 5 * s), (238, 214, 222))
        pg.flat(oval(xx - 9 * s, yy - 6 * s, 3 * s, 2.5 * s), (246, 222, 150))


# ----------------------------------------------------------------------------------------------- booms, posts

def depth_of_y(x, y):
    """Which lane depth a point on the water at world x and screen y is at."""
    return (near_edge(x) - LANE0 - y) / LANE_DY


LANE_W = 60.0                      # a lane's width across the brook in world px (depth is drawn LANE_DY px a lane)


def boom_line(x, open_=0.0):
    """A log boom hinged on the far bank at world x: -> f(v) the (world x, lane depth) of the point v (0 hinge .. 1
    free end) along it. open_ 0 = straight across the brook to our side, 1 = swung round downstream to lie along
    the far bank (behind every lane). A rigid log: its length in the world never changes."""
    d_h, d_e = D_FAR - 0.25, D_NEAR + 0.55
    Lw = (d_h - d_e) * LANE_W
    th = _ss(open_) * math.pi / 2
    ex, ed = x + Lw * math.sin(th), d_h - Lw * math.cos(th) / LANE_W
    return lambda v: (x + (ex - x) * v, d_h + (ed - d_h) * v)


def boom_screen(x, open_, v):
    wx, d = boom_line(x, open_)(v)
    return at_depth(wx, d), lane_y(d, wx)


def draw_boom(pg, x, sh, open_=0.0, d0=-99.0, d1=99.0, post=True):
    """Only the part of the boom between lane depths d0 and d1 (drawn a slice at a time between the lanes, so a raft
    in a nearer lane passes in front of it and one further back behind it)."""
    f = boom_line(x, open_)
    dh, de = f(0.0)[1], f(1.0)[1]
    if post and d0 <= dh < d1:                                 # the hinge post on the far bank
        hx, hy = boom_screen(x, open_, 0.0)
        pg.shape(rrect(hx - 8 - sh, hy - 60, hx + 8 - sh, hy + 6, 4), tone(TRUNK, 0.05), 0.1)
    if abs(dh - de) < 1e-3:
        if not d0 <= dh < d1:
            return
        v0, v1 = 0.0, 1.0
    else:
        v0 = min(1.0, max(0.0, (dh - d1) / (dh - de)))
        v1 = min(1.0, max(0.0, (dh - d0) / (dh - de)))
        if v1 <= v0:
            return
    n = 6
    p, q = skia.Path(), skia.Path()
    for i in range(n + 1):
        v = v0 + (v1 - v0) * i / n
        bx, by = boom_screen(x, open_, v)
        (p.moveTo if i == 0 else p.lineTo)(bx - sh, by - 2)
        (q.moveTo if i == 0 else q.lineTo)(bx - sh, by - 6)
    w = 16.0 * lane_sc(max(0.0, (dh + de) / 2))
    pg.stroke(p, tone(LOG, -0.12), w)
    pg.stroke(q, LOG_TOP, w * 0.32)
    if v1 >= 1.0:
        ex, ey = boom_screen(x, open_, 1.0)
        pg.flat(oval(ex - sh, ey - 2, 8, 7.5), LOG_END)
        pg.flat(oval(ex - sh, ey - 2, 4, 3.6), LOG_RING)


def draw_post(pg, x, y, sh, h=110.0, w=8.0):
    pg.shape(rrect(x - w - sh, y - h, x + w - sh, y + 4, 4), tone(TRUNK, 0.08), 0.1)
    pg.flat(oval(x - sh, y - h + 1, w, 3), tone(TRUNK, 0.2))


FLAG_COLS = ["wheels", "tentacles", "teeth", "springs", "lantern", "digger"]
FIN_TOP = 210.0                    # the finish posts stand this tall above the water (the flag rope well above the sails)


def finish_rope(sh):
    xn, yn = at_depth(FINISH, D_NEAR) - sh, near_edge(FINISH) + 8
    xf, yf = at_depth(FINISH, D_FAR) - sh, far_edge(FINISH) + 2
    top_n, top_f = yn - FIN_TOP - 40, yf - FIN_TOP + 20
    pts = [(xn + (xf - xn) * u, top_n + (top_f - top_n) * u + 26 * u * (1 - u)) for u in np.linspace(0, 1, 15)]
    return (xn, yn, top_n), (xf, yf, top_f), pts


def finish_line(pg, t, sh, d0=-99.0, d1=99.0):
    """The finish: a tall post each side of the brook with a rope of little flags in the six colours high across it,
    and a row of floats across the water between the lanes; only the part between lane depths d0 and d1 (drawn a
    slice at a time, so the rafts pass in front of the far part and behind the near part)."""
    (xn, yn, top_n), (xf, yf, top_f), pts = finish_rope(sh)
    if d0 <= D_FAR - 0.01 < d1:
        draw_post(pg, xf, yf, sh=0.0, h=yf - top_f, w=7.0)
        p = skia.Path()
        for i, (px, py) in enumerate(pts):
            (p.moveTo if i == 0 else p.lineTo)(px, py)
        pg.stroke(p, tone(TWINE, -0.15), 2.5)
        for k in range(1, 14):
            px, py = pts[k]
            fl = 3 * math.sin(t * 3 + k)
            pg.flat(smooth([(px - 8, py + 1), (px + 8, py + 1), (px + fl, py + 20)]), COLS[FLAG_COLS[k % 6]], 0.95)
    for j in range(N_LANES - 1):                               # floats between the lanes
        d = j + 0.5
        if d0 <= d < d1:
            fx, fy = at_depth(FINISH, d) - sh, lane_y(d, FINISH) + 1 + 1.2 * math.sin(t * 2 + j)
            s = lane_sc(d)
            pg.shape(oval(fx, fy - 3 * s, 7 * s, 5 * s), (238, 230, 214), 0.12)
            pg.flat(rrect(fx - 1 * s, fy - 22 * s, fx + 1 * s, fy - 4 * s, 1), MAST)
            pg.flat(smooth([(fx + 1 * s, fy - 22 * s), (fx + 13 * s, fy - 18 * s), (fx + 1 * s, fy - 13 * s)]),
                    COLS[FLAG_COLS[j % 6]])
    if d0 <= D_NEAR + 0.01 < d1:
        draw_post(pg, xn, yn, sh=0.0, h=yn - top_n, w=8.0)


# ----------------------------------------------------------------------------------------------- the rafts

LOG_T = 14.0                       # a log's thickness on screen (lane-0 px)
LOG_DX, LOG_DY = 3.0, -7.0         # each log further back in the raft is drawn this much right / up
MAST_H = 96.0


def ragged(i):
    """How far raft i's four raw logs stick out past the notch (they came off a driftwood pile)."""
    rs = np.random.default_rng(300 + i)
    return [float(v) for v in rs.uniform(12, 30, 4)]


def raft_shape(x, y, sc, L=RAFT_L, ext=(0, 0, 0, 0)):
    """The four logs' rectangles (far log first): [(x0, y0, x1, y1)] with (x, y) the middle of the near log's
    bottom; ext: how far each log (0 near .. 3 far) still sticks out to the right (untrimmed)."""
    out = []
    for k in reversed(range(4)):
        ox, oy = LOG_DX * k * sc, LOG_DY * k * sc
        out.append((x - L / 2 * sc + ox, y + oy - LOG_T * sc, x + (L / 2 + ext[k]) * sc + ox, y + oy))
    return out


def mast_foot(x, y, sc):
    """Where the leafy twig stands in the deck (middle of the raft, on the middle logs)."""
    return x + 1.5 * LOG_DX * sc, y + 1.5 * LOG_DY * sc - LOG_T * sc + 2 * sc


def leaf_path(x, y, s, ang=0.0, flap=0.0):
    """A big broad autumn leaf (x, y: where it meets its twig, pointing up; s its length): round-shouldered, a pointed
    tip, a little notch at the base. flap bends it gently in the breeze."""
    pts = [(0.0, 0.0), (0.2, -0.06), (0.4, -0.24), (0.46, -0.48), (0.36, -0.72), (0.16, -0.9), (0.0, -1.02),
           (-0.16, -0.9), (-0.36, -0.72), (-0.46, -0.48), (-0.4, -0.24), (-0.2, -0.06)]
    q = [(x + (px + flap * (-py) * 0.1) * s, y + py * s) for px, py in pts]
    p = smooth(q)
    if ang:
        p.transform(skia.Matrix.RotateDeg(ang, (x, y)))
    return p


def draw_leafy_twig(pg, x, y, s, col, dye, t, ang=0.0):
    """A leafy twig: the mast (a thin straight twig, (x, y) its foot) and the big leaf at its top for the sail; dye 0
    the plain autumn leaf .. 1 its Keeper's colour."""
    c = pg.c
    c.save()
    if ang:
        c.rotate(ang, x, y)
    top = y - MAST_H * s
    pg.shape(rrect(x - 2.4 * s, top + 40 * s, x + 2.4 * s, y, 2 * s), MAST, 0.0)
    scol = mix(LEAF_RAW, col, dye)
    fl = 0.5 * math.sin(t * 3.1 + x * 0.01)
    base = (x, top + 44 * s)
    pg.shape(leaf_path(base[0], base[1], 52 * s, 0.0, fl), scol, 0.12, (0.2, -0.2))
    vein = tone(scol, -0.2)
    pg.stroke(skia.Path().moveTo(base[0], base[1]).lineTo(base[0] + fl * 3 * s, base[1] - 46 * s), vein, 1.8 * s)
    for k, (u, d) in enumerate(((0.3, 0.42), (0.55, 0.36))):
        for sd in (-1, 1):
            yy = base[1] - u * 52 * s
            pg.stroke(skia.Path().moveTo(base[0], yy).lineTo(base[0] + sd * d * 52 * s * 0.7, yy - 10 * s), vein,
                      1.2 * s, 0.8)
    c.restore()


def draw_raft(pg, x, y, sc, col, t, pitch=0.0, logs=4, ext=(0, 0, 0, 0), lash=(1.0, 1.0), mast=1.0, dye=1.0,
              water=None, wake=0.0):
    """A little log raft seen from the side and a little above. (x, y): the middle of its near log's bottom (screen);
    pitch deg (nose down +). Built bit by bit: logs 0..4 laid, ext how far each still sticks out (untrimmed), lash
    each lashing 0..1 wound, mast 1 planted (None: no mast), dye its leaf's colour. water: the waterline y here
    (what is below it is under the water: clipped), wake: its speed through the water."""
    c = pg.c
    c.save()
    if water is not None:
        c.clipRect(skia.Rect(-W, -H, 2 * W, water + 1.0))
    if pitch:
        c.rotate(pitch, x, y - LOG_T * sc)
    rects = raft_shape(x, y, sc, RAFT_L, ext)
    for i, (x0, y0, x1, y1) in enumerate(rects):
        k = 3 - i                                             # this log's place, 0 near .. 3 far
        if k >= logs:
            continue
        r = (y1 - y0) / 2
        shade = -0.04 * k
        pg.shape(rrect(x0, y0, x1, y1, r), tone(LOG, shade), 0.1, (0.0, -0.5))
        pg.flat(rrect(x0 + r * 0.6, y0 + 1.5 * sc, x1 - r * 0.6, y0 + 4.5 * sc, 1.5 * sc), tone(LOG_TOP, shade), 0.9)
        pg.flat(rrect(x0 + r, y1 - 3.0 * sc, x1 - r, y1 - 1.0 * sc, 1.0), tone(LOG, shade - 0.16), 0.6)   # its round
        pg.flat(oval(x0 + r * 0.5, (y0 + y1) / 2, r * 0.42, r * 0.86), tone(LOG_END, -0.1))   # the end we see
        pg.flat(oval(x0 + r * 0.5, (y0 + y1) / 2, r * 0.18, r * 0.38), LOG_RING, 0.7)
        if ext[k] < 0.5:                                      # a fresh cut end: pale, with a ring
            pg.flat(oval(x1 - r * 0.55, (y0 + y1) / 2, r * 0.5, r * 0.92), LOG_END)
            pg.flat(oval(x1 - r * 0.55, (y0 + y1) / 2, r * 0.22, r * 0.42), LOG_RING, 0.8)
        else:                                                 # a rough bark end
            pg.flat(oval(x1 - r * 0.6, (y0 + y1) / 2, r * 0.45, r * 0.85), tone(LOG, -0.2), 0.9)
    if logs >= 4:
        for q, u in enumerate(lash):                          # the lashings: twine wound round all four logs
            if u <= 0:
                continue
            lx = x + (-0.3 if q == 0 else 0.3) * RAFT_L * sc
            top = y + 3 * LOG_DY * sc - LOG_T * sc
            n = max(1, int(math.ceil(6 * u - 1e-6)))
            for i in range(n):
                dx = (i - 2.5) * 2.6 * sc
                pg.stroke(skia.Path().moveTo(lx + dx + 3 * LOG_DX * sc, top + 1).lineTo(lx + dx, y - 1),
                          TWINE if i % 2 else tone(TWINE, -0.1), 2.2 * sc)
    if mast is not None and mast >= 1.0:
        mx, my = mast_foot(x, y, sc)
        draw_leafy_twig(pg, mx, my, sc, col, dye, t)
    c.restore()
    if water is not None:                                     # where it sits in the water: a soft ripple line
        xa, xb = x - RAFT_L / 2 * sc - 8, x + (RAFT_L / 2 + 3 * LOG_DX) * sc + 8
        pg.stroke(skia.Path().moveTo(xa, water + 1).lineTo(xb, water + 1), tone(WATER_FAR, 0.35), 2.2, 0.8)
        if wake > 20:
            k_ = min(1.0, wake / 200.0)
            pg.stroke(skia.Path().moveTo(xb - 4, water + 1).quadTo(xb + 6, water - 3, xb + 10, water), FOAM, 2.0,
                      0.4 + 0.4 * k_)
            pg.stroke(skia.Path().moveTo(xa + 2, water + 2).lineTo(xa - 36 * k_ - 8, water + 1), FOAM, 1.8, 0.35 * k_)


# ----------------------------------------------------------------------------------------------- animals

def ladybird(pg, x, y, s, t, fly=0.0, face=1):
    """A ladybird (s = its length, px; (x, y) under its middle): a red dome with spots and a small dark head; fly 0..1
    lifts it a little nose-up and two clear wings flutter out."""
    red, dark = (204, 68, 52), (70, 52, 50)
    c = pg.c
    c.save()
    if fly > 0.01:
        c.rotate(-face * 18 * fly, x, y)
        for sx in (-1, 1):
            a = math.sin(t * 60 + sx) * 0.5 + 0.5
            pg.flat(oval(x - face * s * 0.1 + sx * s * 0.4, y - s * (0.55 + 0.25 * a), s * 0.55, s * 0.2, sx * 25),
                    (236, 236, 226), 0.55 * fly)
    pg.flat(oval(x + face * s * 0.5, y - s * 0.2, s * 0.2, s * 0.18), dark)
    body = skia.Path()
    body.addArc(skia.Rect(x - s * 0.5, y - s * 0.5, x + s * 0.5, y + s * 0.5), 180, 180)
    body.close()
    pg.flat(body, red)
    for dx, dy in ((-0.22, -0.2), (0.12, -0.3), (0.28, -0.12), (-0.05, -0.08)):
        pg.flat(oval(x + dx * s, y + dy * s, s * 0.07, s * 0.07), dark)
    pg.stroke(skia.Path().moveTo(x, y - s * 0.49).lineTo(x, y - s * 0.02), dark, max(0.8, s * 0.05))
    c.restore()


DUCK_C, DUCK_D, DUCK_HEAD = (150, 118, 86), (118, 90, 66), (128, 100, 74)
BILL = (226, 160, 60)
CHICK, CHICK_D = (214, 182, 104), (170, 136, 80)


def duck(pg, x, y, s, t, face=-1, chick=False, paddle=1.0, dip=0.0):
    """A swimming duck seen from the side (y = the waterline under it, s = its length): a mallard hen (brown) or a
    fluffy duckling; face -1 swims left. paddle bobs it a little, dip tips its head down to the water."""
    body_c, body_d = (CHICK, CHICK_D) if chick else (DUCK_C, DUCK_D)
    bob = 1.2 * math.sin(t * 4.0 + x * 0.05) * paddle * s / 40
    f = face
    c = pg.c
    c.save()
    c.clipRect(skia.Rect(-W, -H, 2 * W, y + 1.5))
    yy = y + bob
    if chick:
        pg.shape(oval(x, yy - s * 0.22, s * 0.5, s * 0.34), body_c, 0.12)
        hx, hy = x + f * s * 0.36, yy - s * 0.62 + dip * s * 0.3
        pg.shape(oval(hx, hy, s * 0.26, s * 0.25), body_c, 0.1)
    else:
        pg.shape(smooth([(x - f * s * 0.55, yy - s * 0.32), (x - f * s * 0.2, yy - s * 0.42),
                         (x + f * s * 0.3, yy - s * 0.36), (x + f * s * 0.42, yy - s * 0.12),
                         (x + f * s * 0.1, yy + s * 0.08), (x - f * s * 0.45, yy + s * 0.02)]), body_c, 0.12)
        pg.flat(smooth([(x - f * s * 0.3, yy - s * 0.3), (x + f * s * 0.05, yy - s * 0.33), (x + f * s * 0.12, yy - s * 0.2),
                        (x - f * s * 0.25, yy - s * 0.16)]), body_d, 0.8)        # the folded wing
        pg.flat(rrect(x - f * s * 0.12 - s * 0.06, yy - s * 0.3, x - f * s * 0.12 + s * 0.06, yy - s * 0.24, 2),
                (96, 110, 170), 0.8)                                               # a little blue on the wing
        hx, hy = x + f * s * 0.36, yy - s * 0.58 + dip * s * 0.3
        pg.shape(tube([(x + f * s * 0.3, yy - s * 0.3), (hx, hy)], s * 0.1, s * 0.09), DUCK_HEAD, 0.0)
        pg.shape(oval(hx, hy, s * 0.15, s * 0.13), DUCK_HEAD, 0.1)
    r = s * (0.26 if chick else 0.15)
    bill_l = s * (0.16 if chick else 0.22)
    pg.flat(smooth([(hx + f * r * 0.7, hy - r * 0.1), (hx + f * (r + bill_l), hy + r * 0.2),
                    (hx + f * r * 0.7, hy + r * 0.45)]), BILL)
    pg.flat(oval(hx + f * r * 0.35, hy - r * 0.25, r * 0.16, r * 0.16), (46, 36, 34))
    pg.flat(oval(hx + f * r * 0.38, hy - r * 0.31, r * 0.05, r * 0.05), (250, 246, 236))
    c.restore()
    for k in range(2):                                         # a soft V of ripples behind it
        dx = -f * (s * 0.5 + 14 * k)
        pg.stroke(skia.Path().moveTo(x + dx, y + 1).lineTo(x + dx * 1.3, y + 3 + 2 * k), tone(WATER_FAR, 0.35), 1.8,
                  0.6 - 0.2 * k)
