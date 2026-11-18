"""Forest Keepers episode 8, The River Raft Race, in the flat picture-book look (a remake of FK0004, the same story:
docs/engines/forest_keepers_raft_race.md; staging: docs/engines/forest_keepers_raft_flat.md). The world, the water
and the race physics are raft_flat_world.py.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep8.py). Six Keepers (no Sprout yet), the new faces, the ep 14 walks (arm swing, Twigs' forward knees, Hans' ripple).

    plan().end                              the timeline
    frame(pg, valley, t)                    draw one frame onto a flat.FlatPage
    things(t) / limbs(t)                    what the storycheck sees (ep8.py --check)
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import (TURN_NARROW, TWIGS_FORE, TWIGS_UPPER, WHEELS_FORE, WHEELS_UPPER, Monster,
                                               two_bone)

from . import illustrate as il
from . import raft_flat_world as RW
from .flat_motion import (HANS_LEG, Hopper, MoleDig, Spoil, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing,
                          stance_drop, walk_path)
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H, K = RW.W, RW.H, RW.K
FPS = 60
STEP = 1.0 / FPS
ORDER = ["springs", "wheels", "teeth", "tentacles", "digger", "lantern"]
WALKERS = ["springs", "wheels", "teeth", "tentacles", "digger"]
NAMES = {"teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs", "tentacles": "Hans",
         "lantern": "Glo"}
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300}
V_WALK = 100.0
EASE = 1.0
GB = RW.ground(2000.0)                      # the path at the raft line (level there)
RACE_SEED = 146                             # 3 lead changes; the leader most of the way is caught on the line
# raft k (built k-th) belongs to OWNERS[k] and waits in lane 5 - k (the first one furthest back)
OWNERS = ["wheels", "tentacles", "digger", "teeth", "springs", "lantern"]
LANE = [5 - k for k in range(6)]

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("Down by the brook, the Keepers come across a pile of driftwood, washed up by the old slide. And before the "
        "sun goes down, six little rafts will race all the way down the brook... over two little waterfalls.")
LINES = {
    "leaf": "Oh, look. A leaf, sailing down the brook... with a ladybird on board.",
    "over": "Over the little waterfall she goes.",
    "fine": "She's quite all right.",
    "idea": "And that gives Wheels an idea. All this driftwood would make a raft. Six rafts, in fact. One for every "
            "Keeper.",
    "slide": "Here on the bank there's an old wooden slide, down into the pool.",
    "shake": "Springs bounces up into the old maple, and shakes down six big leaves, still on their twigs.",
    "gather": "Glo gathers them up. They'll make lovely sails.",
    "dig": "And Digs clears the mud out from the bottom of the slide.",
    "logs": "Wheels lays four logs against the stop block.",
    "trim": "Twigs trims them at the notch, so every raft comes out just the same length.",
    "lash": "Hans ties them together, with three tentacles at once.",
    "sail": "And Glo's light turns each leaf sail its Keeper's colour.",
    "splash": "Down the slide... and into the pool.",
    "six": "Six rafts, waiting at the log boom.",
    "walk": "Springs will start the race. Everyone else walks down to the finish, to watch.",
    "riffle": "First, the riffle, quick over the stones.",
    "f1": "Then the first little waterfall.",
    "lily": "The quiet lily pool.",
    "rapids": "The rapids.",
    "f2": "The second little waterfall.",
    "glide": "And the long, slow glide to the finish.",
    "ready": "Back at the start, Springs is ready.",
    "off": "And they're off!",
    "over1": "Over the first waterfall...",
    "lead": "Wheels' raft takes the lead.",
    "over2": "And over the second.",
    "catch": "But here comes Twigs' raft...",
    "win": "Twigs' raft wins! By a whisker.",
    "ducks": "And look who's paddled out to see. A mother duck, and her three ducklings.",
    "late": "And here comes Springs, all the way from the start.",
}
FINALE = "What a race. Goodnight, little brook."
SIGNOFF = "What should the Keepers build next? Tell us in the comments."
HOLD_END = 4.5                              # s of quiet after the goodnight (owner 2026-11-05: 3-5 s)


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-9), 0.0), 1.0)


def ease(t, a, b):
    return smoothstep(_seg(t, a, b))


def lerp2(p, q, u):
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


# ----------------------------------------------------------------------------------------------- walking on the slope

class Slope:
    """A flat_motion gait (built on ground 0) walked on the path's real ground: each foot stands on the ground under
    it, the body on the ground under the body (the path eases down beside each little falls)."""

    def __init__(self, g):
        self.g = g

    def __getattr__(self, k):
        return getattr(self.g, k)

    def foot(self, i, t):
        x, y, down, n = self.g.foot(i, t)
        return x, y + RW.ground(x), down, n

    def feet(self, t):
        return [self.foot(i, t)[:2] for i in range(len(self.g.home))]


# ----------------------------------------------------------------------------------------------- the build line

RAIL0 = RW.ST[0] - 100.0                    # the slide's top end
OVER_Y = GB - 262.0                         # a bundle held up over Wheels' head (its near bottom): arms straight up
STOP_X = RW.ST[0] - RW.RAFT_L / 2           # the stop block: every raft's left end against it
NOTCH_X = RW.ST[0] + RW.RAFT_L / 2          # the notch on the rail: Twigs trims every log here
PEGS = [RW.ST[i] + RW.RAFT_L / 2 + 5.0 for i in range(3)]   # a peg holds each raft at its station (right end)
PILE_X = 1400.0                             # the driftwood washed up on the bank, behind the path at Wheels' left


def rail_y(x):
    """Top of the slide's near rail at x: two old poles on trestles, falling gently to the right."""
    return GB - 108.0 + 0.008 * (x - RAIL0)


SLIP_END = RW.SLIP + 160.0                  # the rails come down to the water's edge here
FLOAT_Y = lambda x: RW.lane_y(-0.55, x) + 6.0   # noqa: E731  a raft afloat at the slide's foot: its near bottom


def slip_curve(u):
    """The slide's foot: from the end of the level rails (u 0) down the bank into the water (u 1): (x, y)."""
    x0, y0 = RW.SLIP, rail_y(RW.SLIP)
    x1, y1 = SLIP_END, FLOAT_Y(SLIP_END) + 14.0              # its foot under the water
    x = x0 + (x1 - x0) * u
    return x, y0 + (y1 - y0) * (0.5 - 0.5 * math.cos(math.pi * u)) ** 0.9


FLOAT_X0 = SLIP_END + 15.0                  # a raft's middle when it floats off the slide's foot
WET = 0.35                                  # the share of a floating raft below the waterline


def support(x):
    """The height (screen y) a raft's end rests on at x along the slide: the rails, the slide's foot, the water."""
    if x <= RW.SLIP:
        return rail_y(x) - 1
    if x <= SLIP_END:                                       # down the foot until it floats
        return min(slip_curve((x - RW.SLIP) / (SLIP_END - RW.SLIP))[1], FLOAT_Y(x)) - 1
    return FLOAT_Y(x) - 1


def pile_y(b):
    """The near-bottom y of driftwood bundle b (0 bottom .. 5 top) in the pile on the bank."""
    return GB - 44.0 - 14.0 * b


# Twigs trims at the notch: where his left hand is so the blade crosses the logs there, pointing down
def _twigs_cut_pose():
    """Twigs' left hand for the trim: the blade (straight on from his forearm, as monster.py draws it) crosses the
    four logs at the notch, slanting down and in like a pruning saw, its middle at the middle of the stack."""
    x, y = RW.SPOT["teeth"], GB
    k = K
    sh = (x - 82 * k, y - 350 * k + 10 * k)

    def safe(hd):                                                  # well inside the side his elbow stays on
        return math.degrees(math.atan2(-(hd[0] - sh[0]), hd[1] - sh[1])) < 15.0
    ylo, yhi = rail_y(NOTCH_X) - RW.LOG_T - 3 * 7.0, rail_y(NOTCH_X)
    ym = (ylo + yhi) / 2
    best = None
    for hx in np.linspace(NOTCH_X - 60, NOTCH_X + 90, 76):
        for hy in np.linspace(ylo - 140, yhi + 30, 86):
            hd = (hx, hy)
            if math.hypot(hd[0] - sh[0], hd[1] - sh[1]) > (TWIGS_UPPER + TWIGS_FORE) * k * 0.97:
                continue
            el = two_bone(sh, hd, TWIGS_UPPER * k, TWIGS_FORE * k, -1, (-0.4, 1.0))
            ux, uy = hd[0] - el[0], hd[1] - el[1]
            L = math.hypot(ux, uy) or 1.0
            ux, uy = ux / L, uy / L
            if uy < 0.55 or not all(safe((hd[0] + 0.3 * q, hd[1] + 0.95 * q)) for q in (-3.0, 0.0, 15.0)):
                continue
            nx, ny = -uy, ux
            if nx * -1 < 0:
                nx, ny = -nx, -ny
            base = (hd[0] + ux * 6 * k + nx * 13 * k, hd[1] + uy * 6 * k + ny * 13 * k)
            tip = (base[0] + ux * 64 * k, base[1] + uy * 64 * k)
            if not (min(base[0], tip[0]) + 6 < NOTCH_X < max(base[0], tip[0]) - 6):
                continue
            v = (NOTCH_X - base[0]) / (tip[0] - base[0])
            yc = base[1] + (tip[1] - base[1]) * v                 # where the blade crosses the notch
            err = abs(yc - ym) + 8 * abs(v - 0.55)
            if best is None or err < best[0]:
                best = (err, hd, (ux, uy))
    assert best is not None, "Twigs cannot reach the notch"
    return best[1], best[2]


CUT_HAND, CUT_DIR = _twigs_cut_pose()


# ----------------------------------------------------------------------------------------------- the plan

STOPS = {
    "watch": dict(springs=1040.0, wheels=1440.0, teeth=1680.0, tentacles=1950.0, digger=2200.0, lantern=1830.0),
    "work": dict(springs=1040.0, wheels=RW.SPOT["wheels"], teeth=RW.SPOT["teeth"], tentacles=RW.SPOT["tentacles"],
                 digger=RW.SLIP + 100.0, lantern=1830.0),
    "finish": dict(springs=6700.0, wheels=6915.0, teeth=7140.0, tentacles=7405.0, digger=7680.0, lantern=7272.0),
}
STOPS["start"] = {kd: x - 2100.0 for kd, x in STOPS["watch"].items()}     # all of them out of view at first
DIG_X = RW.SLIP + 100.0                     # where Digs clears the slide's foot
PIN_POST = RW.START_BOOM - 230.0            # the post the start boom's rope is pinned to (upstream of the rafts)
START_X = PIN_POST - 100.0 * K - 26.0       # Springs, just upstream of it (never in front of a raft)
CAM_END = 6905.0                            # the finish pool, the finish line and the Keepers in view
GLO_TWIGS = [-56.0, -42.0, -28.0, 28.0, 42.0, 56.0]   # either side of his lantern, a bunch each side     # where each leafy twig is in Glo's bunch (x from his middle)


class Plan:
    def __init__(self):
        self.race = RW.Race(RACE_SEED)
        self.hook = 1.5
        t_hook = self.hook + _dur(HOOK)
        self.walk_in = (1.0, 1.0 + 2100.0 / V_WALK + EASE)
        self._leaf(t_hook)
        self.spread = (self.say_idea + _dur(LINES["idea"]) + 0.6, None)
        d = max(abs(STOPS["work"][kd] - STOPS["watch"][kd]) for kd in WALKERS)
        self.spread = (self.spread[0], self.spread[0] + d / V_WALK + EASE)
        self.say_slide = self.spread[0] + 1.0
        self._shake(max(self.spread[1] - 1.0, self.say_slide + _dur(LINES["slide"]) + 0.4))
        self._gather(self.shake_end + 0.4)
        self._dig(self.gather_end + 0.2)
        self._build(self.dig_end + 0.8)
        self._walk(self.build_end)
        self._race(self.tour_end + 1.6)
        self._cheer()
        self.end = self.signoff + _dur(SIGNOFF) + 2.5
        self.paths = self._paths()
        # they turn to where they go before setting off (a longer look ahead than flat_motion's 0.3 s), so a
        # swinging arm's elbow comes round over several frames, not in two or three
        self.turns = {kd: heading(self.paths[kd], ahead=0.8) for kd in ORDER}
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {kd: Slope(biped(kd, self.paths[kd], 0.0, K, spread=narrow(kd))) for kd in ("teeth", "digger")}
        self.gaits["tentacles"] = Slope(WaveGait(0.0, K, self.paths["tentacles"], spread=narrow("tentacles", 0.5)))
        self.hopper = Hopper(self.paths["springs"], 0.0, K)
        self.cam = self._camera()
        RW.LIGHT[:] = [(0.0, "day"), (self.tour[0], "day"), (self.cut, "gold"), (self.fin_t + 4.0, "gold"),
                       (self.finale, "evening")]
        self.voices = []
        self.voices = voices(self)

    # --- 1. the leaf with the ladybird, over the little falls above the start pool
    def _leaf(self, t_hook):
        self.leaf_lane = 1.2
        self.t_lip = self.walk_in[1] + 3.2                         # it goes over the falls
        # the leaf drifts with the water (a light thing, no sail): simulated from well upstream
        tr = RW.Trait(0.45, 1.25, 0.0)
        x, v = RW.F0 - 900.0, 55.0
        dt = 1.0 / 240
        rec = []
        tau = 0.0
        hit = None
        while tau < 60.0:
            u = RW.current(x, int(self.leaf_lane), tau)
            a = (u - v) * (1.6 + 0.02 * abs(u - v)) * tr.drag / tr.mass
            if RW.on_chute(x):
                a += 700.0 * RW.surface_slope(x)
            foot = RW.F0 + RW.CW
            if foot - 10 <= x < foot + 30:
                a += 300.0 * (1 - (x - foot + 10) / 40)
            v += a * dt
            x += v * dt
            rec.append((tau, x))
            if hit is None and x >= RW.F0:
                hit = tau
            tau += dt
        self._leaf_rec = np.array(rec)
        self.leaf_t0 = self.t_lip - hit                             # world time of the sim's start
        self.say_leaf = max(t_hook + 0.4, self.t_lip - 5.5)
        self.say_over = max(self.say_leaf + _dur(LINES["leaf"]) + 0.2, self.t_lip - 0.6)
        out = self.t_lip + 3.5                                     # out of the hole, drifting in the start pool
        self.lady_fly = (out + 0.6, out + 3.4)                      # the ladybird flies off to a reed
        self.say_fine = self.lady_fly[0] + 0.2
        # Wheels' idea (a raft in his bubble) first, then she says it
        self.idea_t = max(self.say_fine + _dur(LINES["fine"]) + 0.8, self.lady_fly[1] + 0.3)
        self.say_idea = self.idea_t + 1.9

    def leaf_x(self, t):
        tau = t - self.leaf_t0
        r = self._leaf_rec
        if tau <= 0:
            return r[0, 1] + 55.0 * tau
        i = min(int(tau * 240), len(r) - 1)
        return float(r[i, 1])

    # --- 2. Springs shakes the maple's low branch: six leafy twigs flutter down
    def _shake(self, t0):
        self.shake0 = t0
        self.say_shake = t0
        self.hop_up = (t0 + 0.8, t0 + 1.35)                        # springs up, grabs the branch
        self.bounces = [(self.hop_up[1] + 0.2 + 0.9 * i, self.hop_up[1] + 0.2 + 0.9 * (i + 1)) for i in range(3)]
        self.let_go = self.bounces[-1][1] + 0.3
        self.drop = (self.let_go, self.let_go + 0.45)
        self.shake_end = max(self.drop[1] + 0.8, t0 + _dur(LINES["shake"]) + 0.3)
        rs = np.random.default_rng(81)
        self.twigs = []
        for i in range(6):
            b = self.bounces[i // 2]
            u = 0.3 + 0.13 * i                                    # where on the branch it grew
            self.twigs.append(dict(i=i, u=u, off=b[0] + 0.45 + 0.12 * (i % 2), fall=rs.uniform(1.2, 1.6),
                                   land=(RW.TREE + 200.0 + 20.0 * i + rs.uniform(-5, 5)), spin=rs.uniform(-1, 1)))

    def branch_pts(self, t):
        """The low branch's live outer part: (root, tip) - it bends down with Springs hanging on it."""
        (x0, y0), (x1, y1) = RW.MAPLE_BRANCH[1], RW.MAPLE_BRANCH[2]
        bend = 0.0
        if self.hop_up[1] <= t < self.let_go + 0.8:
            if t < self.let_go:
                bend = 14.0 + 10.0 * sum(math.sin(math.pi * _seg(t, a, b)) for a, b in self.bounces)
            else:                                                   # springs back up, a little wobble
                u = t - self.let_go
                bend = 14.0 * math.exp(-4 * u) * math.cos(14 * u)
        return (x0, y0), (x1, y1 + bend)

    def branch_at(self, u, t):
        """A point u (0 root .. 1 tip) along the live outer branch (it bends most at its tip)."""
        (x0, y0), (x1, y1) = RW.MAPLE_BRANCH[1], RW.MAPLE_BRANCH[2]
        (_, _), (_, yb) = self.branch_pts(t)
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + (yb - y1) * u ** 1.6

    def springs_lift(self, t):
        """How far up Springs is (px) and his coil squash, through the shake."""
        if not (self.shake0 <= t < self.drop[1] + 0.4):
            return 0.0, 0.0
        x = STOPS["work"]["springs"]
        hand_y = self.branch_at(self.grab_u(), t)[1]
        hang = RW.ground(x) - (hand_y + (170 - 46 * -0.4) * K - 10 * K + 47.0 * K)    # his feet, hanging from it
        if t < self.hop_up[0]:
            u = _seg(t, self.hop_up[0] - 0.4, self.hop_up[0])
            return 0.0, 0.5 * math.sin(math.pi * u)                 # crouches to jump
        if t < self.hop_up[1]:
            u = _seg(t, *self.hop_up)
            return hang * math.sin(u * math.pi / 2), -0.3 * u
        if t < self.let_go:
            return hang, -0.4
        u = _seg(t, *self.drop)
        if u < 1:
            return hang * (1 - u * u), -0.2
        return 0.0, 0.45 * math.sin(math.pi * _seg(t, self.drop[1], self.drop[1] + 0.4))   # lands, squashes

    def grab_u(self):
        """Where his right hand takes the branch (right above his right shoulder)."""
        (x0, _), (x1, _) = RW.MAPLE_BRANCH[1], RW.MAPLE_BRANCH[2]
        return (STOPS["work"]["springs"] + 100 * K - x0) / (x1 - x0)

    def twig_pos(self, i, t):
        """(world x, y of its foot, angle deg, state) of leafy twig i up to Glo's bunch: on the branch, falling,
        lying on the meadow."""
        tw = self.twigs[i]
        if t < tw["off"]:
            x, y = self.branch_at(tw["u"], t)
            return x, y + 4.0, 180.0 + (8.0 if i % 2 else -10.0) + 3 * math.sin(t * 1.3 + i), "branch"
        u = (t - tw["off"]) / tw["fall"]
        x0, y0 = self.branch_at(tw["u"], tw["off"])
        y1 = RW.near_edge(tw["land"]) + 34.0
        if u < 1:                                                   # it flutters down, turning over
            e = u * u * (3 - 2 * u) * 0.4 + 0.6 * u
            x = x0 + (tw["land"] - x0) * e + 14 * math.sin(u * 7 + i)
            y = y0 + 4 + (y1 - y0 - 4) * e
            a0 = 180.0 + (8.0 if i % 2 else -10.0) + 3 * math.sin(tw["off"] * 1.3 + i)   # as it hung
            ang = a0 + (90 - a0) * e + 25 * math.sin(u * 6) * u * (1 - u) * 4
            return x, y, ang, "falling"
        return tw["land"], y1, 90.0 + 4 * tw["spin"], "ground"

    # --- 3. Glo gathers the six leafy twigs and floats along behind everyone to station 3
    def _gather(self, t0):
        self.gather0 = t0
        self.say_gather = t0 + 0.3
        self.glo_down = (t0 + 0.2, t0 + 2.4)                       # floats over and down to them
        self.picks = [(self.glo_down[1] + 0.45 * i, self.glo_down[1] + 0.45 * i + 0.6) for i in range(6)]
        self.glo_up = (self.picks[-1][1], self.picks[-1][1] + 1.0)
        d = RW.ST[2] - self.glo_pick_x()
        self.glo_to = (self.glo_up[1], self.glo_up[1] + d / 140.0 + 1.0)
        self.gather_end = self.glo_to[1] - 1.5

    def glo_pick_x(self):
        return sum(tw["land"] for tw in self.twigs) / 6.0

    # --- 4. Digs clears the mud out of the slide's foot
    def _dig(self, t0):
        self.dig0 = t0
        self.say_dig = t0 + 0.2
        self.dig = MoleDig(K, period=1.1, t_start=t0 + 0.5)
        self.dig_t = (t0 + 0.5, t0 + 0.5 + 6 * 1.1)
        self.digs_back = (self.dig_t[1] + 0.4, None)
        self.digs_back = (self.digs_back[0], self.digs_back[0] + (DIG_X - RW.SPOT["digger"]) / 85.0 + EASE)
        self.dig_end = max(self.digs_back[1] - 1.0, t0 + _dur(LINES["dig"]) + 0.4)
        bob = lambda t: 2 * K * math.sin(t * 2.6)                  # noqa: E731
        self.spoil = Spoil(self.dig, DIG_X, GB - 40.0, K, self.dig_t[1], (118 * K, -150 * K + 4 * K + 40.0), 95 * K,
                           bob)

    def digs_paws(self, t):
        if self.dig_t[0] - 0.3 <= t < self.dig_t[1]:
            return self.dig.angles(t)
        return None

    def trench(self, t):
        """How far the slide's foot is cleared (0 mud .. 1 open to the water)."""
        return ease(t, self.dig_t[0], self.dig_t[1])

    # --- 5. the build: six rafts down the line, every Keeper at their own job
    def _build(self, t0):
        self.build0 = t0
        R = self.rafts = []
        st1_free = t0
        twigs_free, hans_free, glo_free, digs_free, wheels_free = t0, t0, t0, t0, t0
        st2_free, st3_free = t0, t0
        for k in range(6):
            r = dict(k=k, owner=OWNERS[k], lane=LANE[k], ext=RW.ragged(k))
            first = k == 0
            # Wheels: rolls to the pile, lifts the next bundle up over his head (left pincer, then both), rolls to
            # the slide and lays it against the stop block (right pincer), lets go, rolls back to his place
            w0 = max(wheels_free, st1_free - 4.0)
            r["go"] = (w0, w0 + 0.9)                                # rolls left to the pile
            r["pick"] = (r["go"][1], r["go"][1] + 0.8)              # left pincer down to it, grips
            r["lift"] = (r["pick"][1], r["pick"][1] + 1.3)          # up over his head (the right joins at the top)
            r["pass"] = (r["lift"][1], r["lift"][1] + 0.3)
            lay0 = max(r["pass"][1], st1_free)
            if first:
                lay0 = max(lay0, t0 + 1.2)
            r["lay"] = (lay0, lay0 + 1.4)                           # rolls right, lowers it onto the slide
            r["release_w"] = (r["lay"][1], r["lay"][1] + 0.4)
            r["back"] = (r["release_w"][1], r["release_w"][1] + 1.0)
            wheels_free = r["back"][1]
            if first:
                r["say_logs"] = r["lay"][0] - 0.8
            # Twigs: blade out, four strokes (one log each, the far log first), blade in, the peg
            c0 = max(r["release_w"][1] + 0.1, twigs_free)
            if first:
                c0 = max(c0, r["say_logs"] + _dur(LINES["logs"]) + 0.2)
                r["say_trim"] = c0
            r["reach_t"] = (c0, c0 + 0.6)
            r["blade"] = (r["reach_t"][1], r["reach_t"][1] + 0.4)
            r["strokes"] = [(r["blade"][1] + 0.6 * i, r["blade"][1] + 0.6 * (i + 1)) for i in range(4)]
            r["blade_in"] = (r["strokes"][-1][1], r["strokes"][-1][1] + 0.4)
            if first:
                b0 = max(r["blade_in"][0], r["say_trim"] + _dur(LINES["trim"]) - 0.6)
                r["blade_in"] = (b0, b0 + 0.4)
            r["peg1"] = (max(r["blade_in"][1], st2_free - 0.7), None)
            r["peg1"] = (r["peg1"][0], r["peg1"][0] + 0.7)          # his left hand taps the peg down
            twigs_free = r["peg1"][1] + 0.5
            r["slide1"] = (r["peg1"][1] - 0.15, r["peg1"][1] - 0.15 + 2.2)
            st1_free = r["slide1"][0] + 1.0
            # Hans: three tentacles - one holds the twine ball up, one winds, one steadies the logs
            l0 = max(r["slide1"][1] + 0.2, hans_free)
            if first:
                r["say_lash"] = l0
            r["lashA"] = (l0 + 0.5, l0 + 0.5 + 1.5)
            r["lashB"] = (r["lashA"][1] + 0.35, r["lashA"][1] + 0.35 + 1.5)
            if first:
                r["lashB"] = (r["lashB"][0], max(r["lashB"][1], l0 + _dur(LINES["lash"]) - 0.2))
            r["peg2"] = (max(r["lashB"][1] + 0.2, st3_free - 0.7), None)
            r["peg2"] = (r["peg2"][0], r["peg2"][0] + 0.8)
            hans_free = r["peg2"][1] + 0.4
            st2_free = r["peg2"][1] + 1.2
            r["slide2"] = (r["peg2"][1] - 0.15, r["peg2"][1] - 0.15 + 2.6)
            # Glo: lowers the next leafy twig into its deck, lets go, flares his light over the leaf
            g0 = max(r["slide2"][1] + 0.1, glo_free)
            r["lower"] = (g0, g0 + 1.1)
            r["plant"] = (r["lower"][1], r["lower"][1] + 0.35)
            r["rise"] = (r["plant"][1], r["plant"][1] + 0.7)
            r["flare"] = (r["rise"][1], r["rise"][1] + 1.3)
            if first:
                r["say_sail"] = r["flare"][0] - 0.6
                r["flare"] = (r["flare"][0], max(r["flare"][1], r["say_sail"] + _dur(LINES["sail"]) - 0.4))
            glo_free = r["flare"][1] + 0.3
            # Digs taps the last peg: down the slide's foot into the pool
            p0 = max(r["flare"][1] + 0.2, digs_free)
            if first:
                p0 = max(p0, r["say_sail"] + _dur(LINES["sail"]) + 0.3)
                r["say_splash"] = p0
            r["peg3"] = (p0, p0 + 0.8)
            digs_free = r["peg3"][1] + 0.4
            st3_free = r["peg3"][1] + 1.0
            r["slide3"] = (r["peg3"][1] - 0.15, r["peg3"][1] - 0.15 + 1.9)     # along to the slide's end
            r["slip"] = (r["slide3"][1], r["slide3"][1] + 1.8)                 # down its foot into the water
            r["float"] = (r["slip"][1], r["slip"][1] + 7.5)                    # out across the pool to the boom
            R.append(r)
        last = R[-1]
        self.say_six = last["float"][1] - 1.0
        self.build_end = max(last["float"][1] + 0.6, self.say_six + _dur(LINES["six"]) + 0.3)
        self.wheels_rest = R[-1]["release_w"][1] + 0.6

    # --- where each raft is
    def raft_state(self, k, t):
        """dict(where, x (world, its middle), y (screen, its near bottom), d (lane depth), pitch, logs, ext, lash,
        mast, dye, wet) for raft k at time t."""
        r = self.rafts[k]
        ext = list(r["ext"])
        out = dict(logs=4, ext=ext, lash=(0.0, 0.0), mast=None, dye=0.0, pitch=0.0, wet=0.0, wake=0.0)
        # trimmed logs: the far log first
        for i, (a, b) in enumerate(r["strokes"]):
            if t >= b:
                ext[3 - i] = 0.0
        out["lash"] = (ease(t, *r["lashA"]), ease(t, *r["lashB"]))
        if t >= r["plant"][0]:
            out["mast"] = 1.0
            out["dye"] = ease(t, r["flare"][0] + 0.45, r["flare"][1] - 0.1)
        if t < r["pick"][1]:                                        # in the driftwood pile on the bank
            return dict(out, where="pile", x=PILE_X, y=pile_y(5 - k), d=-2.0)
        if t < r["lay"][1]:                                         # in Wheels' pincers
            x, y = self.wheels_bundle(k, t)
            return dict(out, where="wheels", x=x, y=y, d=-2.0)
        x_st1 = STOP_X + RW.RAFT_L / 2
        if t < r["slide1"][0]:
            return dict(out, where="st1", x=x_st1, y=rail_y(x_st1) - 1, d=-2.0)
        if t < r["slide2"][0]:
            x = x_st1 + (RW.ST[1] - x_st1) * self._slide(t, r["slide1"])
            return dict(out, where="st2", x=x, y=rail_y(x) - 1, d=-2.0)
        if t < r["slide3"][0]:
            x = RW.ST[1] + (RW.ST[2] - RW.ST[1]) * self._slide(t, r["slide2"])
            return dict(out, where="st3", x=x, y=rail_y(x) - 1, d=-2.0)
        if t < r["slip"][0]:
            x = RW.ST[2] + (RW.SLIP - RW.RAFT_L / 2 - RW.ST[2]) * self._slide(t, r["slide3"], stop=False)
            return dict(out, where="rails", x=x, y=rail_y(x) - 1, d=-2.0)
        if t < r["slip"][1]:                                        # down the slide's foot, into the water
            u = _seg(t, *r["slip"])
            e = u * u * (2.2 - 1.2 * u)                             # speeds up down the foot, the water slows it
            x0, x1 = RW.SLIP - RW.RAFT_L / 2, FLOAT_X0
            x = x0 + (x1 - x0) * e
            ya, yb = support(x - RW.RAFT_L / 2), support(x + RW.RAFT_L / 2)
            y = (ya + yb) / 2
            pitch = math.degrees(math.atan2(yb - ya, RW.RAFT_L))
            wl = RW.lane_y(-0.55, x)                                # the water at the slide's foot
            wet = WET * min(1.0, max(0.0, (y - wl) / 5.0))
            return dict(out, where="slip", x=x, y=y, d=-0.55, pitch=max(0.0, pitch), wet=wet,
                        water=wl if y > wl - 3 else None)
        return dict(out, **self.raft_water(k, t))

    def _slide(self, t, seg, stop=True):
        """0..1 along a slide between pegs: it speeds up down the slope, the next peg stops it (a little bump)."""
        u = _seg(t, *seg)
        e = u * u * (3 - 2 * u)
        if stop and 0.86 < u < 1.0:
            e -= 0.012 * math.sin(math.pi * (u - 0.86) / 0.14)
        return e

    def raft_water(self, k, t):
        """A raft on the water: gliding out from the slide's foot to its lane at the boom, waiting, racing."""
        r = self.rafts[k]
        j = r["lane"]
        tau = t - self.race_t0
        if tau >= 0:
            x, v = self.race.runs[j].at(tau)
            d = j
        else:
            u = _seg(t, *r["float"])
            e = 1 - (1 - u) ** 2.2                                  # glides out, the water slowing it
            x = FLOAT_X0 + (RW.WAIT_X - FLOAT_X0) * (1 - (1 - u) ** 1.6)
            d = -0.55 + (j + 0.55) * e
            v = 0.0
        y, pitch, s = RW.raft_pose(d, x, t)
        wake = abs(v)
        return dict(where="water", x=x, y=y + 6 * s, d=d, pitch=pitch, wet=WET, water=y, wake=wake, sc=s, tau=tau)

    # --- Wheels and the driftwood
    def wheels_bundle(self, k, t):
        """Raft k's bundle while Wheels has it: (x, y) of its middle-near-bottom - up out of the pile beside his left,
        over his head, across and down onto the slide (always behind him: it is going to the slide)."""
        r = self.rafts[k]
        wx = self.paths["wheels"](t)
        p0 = (PILE_X, pile_y(5 - k))
        p1 = (PILE_X + 40.0, GB - 205.0)                           # up beside his left side
        p2 = (wx, OVER_Y)                                          # over his head
        on = (STOP_X + RW.RAFT_L / 2, rail_y(STOP_X + RW.RAFT_L / 2) - 1)
        if t < r["lift"][0]:
            return p0
        if t < r["lift"][1]:
            u = _seg(t, *r["lift"])
            if u < 0.5:
                return lerp2(p0, p1, smoothstep(u / 0.5))
            q = lerp2(p1, (wx, OVER_Y), smoothstep((u - 0.5) / 0.5))
            return q
        if t < r["lay"][0]:
            return p2
        u = _seg(t, *r["lay"])
        mid = (wx + 90.0, GB - 230.0)
        if u < 0.5:
            return lerp2(p2, mid, smoothstep(u / 0.5))
        return lerp2(mid, on, smoothstep((u - 0.5) / 0.5))

    # --- 6. the walk to the finish (the course, told on the way)
    def _walk(self, t0):
        self.say_walk = t0 + 0.2
        self.tour = (t0 + 1.0, None)
        d = {kd: abs(STOPS["finish"][kd] - STOPS["work"][kd]) for kd in WALKERS}
        d["springs"] = abs(START_X - STOPS["work"]["springs"])
        self.tour_arrive = {kd: self.tour[0] + d[kd] / V_WALK + EASE for kd in d}
        self.tour_arrive["lantern"] = self.tour_arrive["digger"] + 0.5
        lead = "digger"
        x0 = RW.SPOT["digger"]
        self.marks = {}
        for name, xm in (("riffle", RW.START_BOOM + 200.0), ("f1", RW.F1 + 150.0), ("lily", 4300.0),
                         ("rapids", 4750.0), ("f2", RW.F2 + 150.0), ("glide", 5500.0)):
            self.marks[name] = self.tour[0] + EASE / 2 + (xm - x0) / V_WALK
        # the lines one after the other, never on top of each other
        t_free = self.say_walk + _dur(LINES["walk"]) + 0.3
        for name in ("riffle", "f1", "lily", "rapids", "f2", "glide"):
            self.marks[name] = max(self.marks[name], t_free)
            t_free = self.marks[name] + _dur(LINES[name]) + 0.3
        self.tour = (self.tour[0], max(self.tour_arrive.values()))
        self.tour_end = max(self.tour_arrive["digger"] + 1.5, t_free + 0.8)

    # --- 7. the race
    def _race(self, t_cut):
        self.cut = t_cut                                            # a dip to black between the two acts
        self.ready = t_cut + 1.2
        self.say_ready = self.ready + 0.2
        c0 = self.say_ready + _dur(LINES["ready"]) + 0.6
        self.count = [(c0 + 1.0 * i, c0 + 1.0 * (i + 1)) for i in range(3)]
        self.pin = (self.count[-1][1], self.count[-1][1] + 0.7)     # Springs pulls the pin
        self.race_t0 = self.pin[1] - 0.1                            # the boom swings open: they're off
        self.boom_open = (self.race_t0, self.race_t0 + 1.8)
        R = self.race
        self.fin_t = self.race_t0 + min(R.finish)
        self.last_in = self.race_t0 + max(R.finish)
        f1 = min(R.runs[i].at(0)[0] for i in range(6))
        lead_x = lambda tau: max(R.runs[i].at(tau)[0] for i in range(6))   # noqa: E731

        def reach(xm):
            for f in range(int(min(R.finish) * 30)):
                if lead_x(f / 30) + RW.RAFT_L / 2 >= xm:
                    return f / 30
            return min(R.finish)
        t0 = self.race_t0
        self.say = {"off": t0 + 0.35}
        self.say["over1"] = max(t0 + reach(RW.F1) - 0.6, self.say["off"] + _dur(LINES["off"]) + 0.3)
        lead_t = [tt for tt, i in R.leaders if i == LANE[0]]
        self.say["lead"] = max(t0 + (lead_t[0] if lead_t else 9.0) + 0.2,
                               self.say["over1"] + _dur(LINES["over1"]) + 0.3)
        self.say["over2"] = max(t0 + reach(RW.F2) - 0.4, self.say["lead"] + _dur(LINES["lead"]) + 0.3)
        self.say["catch"] = max(self.fin_t - 2.6, self.say["over2"] + _dur(LINES["over2"]) + 0.3)
        self.say["win"] = max(self.fin_t + 0.5, self.say["catch"] + _dur(LINES["catch"]) + 0.2)
        # Springs hops along after them, always behind the last raft
        self.springs_go = (t0 + 2.0, t0 + 2.0 + (STOPS["finish"]["springs"] - START_X) / SPRINGS_V + EASE)

    # --- 8. the cheer, the ducks, Springs, goodnight
    def _cheer(self):
        """Springs bounds in first (he followed the race all the way down), then the ducks paddle out."""
        self.say["late"] = max(self.springs_go[1] - 2.0, self.say["win"] + _dur(LINES["win"]) + 1.0)
        self.ducks = (max(self.springs_go[1] + 0.8, self.say["late"] + _dur(LINES["late"]) - 0.5), None)
        self.ducks = (self.ducks[0], self.ducks[0] + 18.0)
        self.say["ducks"] = self.ducks[0] + 2.5
        self.finale = max(self.say["ducks"] + _dur(LINES["ducks"]) + 4.0, self.ducks[0] + 12.0)
        self.sign = (self.finale + _dur(FINALE) + HOLD_END, None)
        self.sign = (self.sign[0], self.sign[0] + 1.0)
        self.signoff = self.sign[1] + 0.3

    # --- paths
    def _paths(self):
        out = {}
        S = STOPS
        for kd in ORDER:
            keys = [(self.walk_in[0], S["start"][kd]), (self.walk_in[1], S["watch"][kd]),
                    (self.spread[0], S["watch"][kd]), (self.spread[0] + abs(S["work"][kd] - S["watch"][kd]) / V_WALK
                                                      + EASE, S["work"][kd])]
            if kd == "wheels":                                    # to the pile and back, for every raft
                for r in self.rafts:
                    w = RW.SPOT["wheels"]
                    keys += [(r["go"][0], w), (r["go"][1], w - 80.0), (r["lift"][0] + 0.4, w - 80.0),
                             (r["lift"][1], w - 20.0), (r["lay"][0], w - 20.0), (r["lay"][1] - 0.2, w + 40.0),
                             (r["release_w"][1], w + 40.0), (r["back"][1], w)]
            if kd == "digger":                                    # clears the slide's foot, then back to his place
                keys += [(self.digs_back[0], DIG_X), (self.digs_back[1], RW.SPOT["digger"])]
            if kd == "lantern":                                   # floats to the twigs and on to station 3
                gx = self.glo_pick_x()
                keys += [(self.glo_down[0], S["work"]["lantern"]), (self.glo_down[1], gx), (self.glo_to[0], gx),
                         (self.glo_to[1], self.glo_x_at(0, self.rafts[0]["lower"][0]))]
                for k, r in enumerate(self.rafts):
                    keys += [(r["lower"][0] - 0.8, self.glo_x_at(k, r["lower"][0])),
                             (r["flare"][1], self.glo_x_at(k, r["lower"][0]))]
            at = RW.SPOT.get(kd, S["work"][kd])
            if kd == "digger":
                at = RW.SPOT["digger"]
            if kd == "lantern":
                at = self.glo_x_at(5, 0)
            keys += [(self.tour[0], at), (self.tour_arrive[kd], START_X if kd == "springs" else S["finish"][kd])]
            if kd == "springs":
                keys += [(self.springs_go[0], START_X), (self.springs_go[1], S["finish"]["springs"])]
            out[kd] = walk_path(sorted(set(keys)), EASE)
        return out

    def glo_x_at(self, k, t):
        """Glo's x while planting raft k's twig: the twig in his bunch right over the deck's mast hole."""
        mx, _ = RW.mast_foot(RW.ST[2], 0.0, 1.0)
        return mx - GLO_TWIGS[k]

    def _camera(self):
        keys = [(0.0, 1350.0), (self.walk_in[1], 1350.0), (self.spread[0], 1350.0), (self.spread[1], 1420.0),
                (self.shake_end, 1420.0), (self.picks[-1][1], 1480.0), (self.glo_to[1], 2330.0), (self.dig0, 2330.0), (self.dig0 + 2.0, 2420.0),
                (self.dig_end, 2420.0), (self.build0 + 1.5, 2330.0), (self.build_end - 6.0, 2330.0),
                (self.build_end - 1.0, 2650.0), (self.tour[0] + 1.5, 2650.0)]
        # the tour: follow the leader (Digs), keeping him on the left half, the brook ahead in view
        lead = self.paths["digger"]
        for f in range(int((self.tour[1] - self.tour[0]) / 2.0) + 1):
            tt = self.tour[0] + 2.0 + 2.0 * f
            keys.append((tt, max(2650.0, min(CAM_END, lead(tt) + 300.0))))
        keys.append((self.cut - 0.5, CAM_END))
        self.cam_tour = walk_path(sorted(keys), 2.5)
        # the race: the pack's middle (each frame), never faster than a slow pan
        self.cam_race_keys = []
        R = self.race
        for f in range(int((self.last_in - self.race_t0 + 30) * 10)):
            tau = f / 10.0
            xs = [RW.at_depth(R.runs[j].at(tau)[0], j) for j in range(6)]
            self.cam_race_keys.append((self.race_t0 + tau, (max(xs) + min(xs)) / 2 + 160.0))
        return None

    def shift(self, t):
        if t < self.cut:
            return self.cam_tour(t) - W / 2
        return self.cam_race(t) - W / 2

    def cam_race(self, t):
        """The race camera: holds on Springs and the rafts at the start, follows the pack's middle down the brook
        (eased: at most a slow pan), and comes to rest on the finish pool with the Keepers."""
        if not hasattr(self, "_race_cam"):
            x0 = RW.START_BOOM + 300.0
            xe = CAM_END
            ts = np.arange(self.cut, self.end + 1.0, 1.0 / FPS)
            out, x, v = [], x0, 0.0
            keys = self.cam_race_keys
            ki = 0
            for tt in ts:
                while ki + 1 < len(keys) and keys[ki + 1][0] <= tt:
                    ki += 1
                target = x0 if tt < self.race_t0 + 1.0 else min(xe, max(x0, keys[ki][1]))
                if tt > self.last_in:
                    target = xe
                a = 6.0 * (target - x) - 4.2 * v                   # a soft spring behind the target
                v = max(-240.0, min(240.0, v + a / FPS))
                x += v / FPS
                out.append(x)
            self._race_cam = (ts, np.array(out))
        ts, xs_ = self._race_cam
        return float(np.interp(t, ts, xs_))

    def narration(self):
        out = [(self.hook, HOOK), (self.say_leaf, LINES["leaf"]), (self.say_over, LINES["over"]),
               (self.say_fine, LINES["fine"]), (self.say_idea, LINES["idea"]), (self.say_slide, LINES["slide"]),
               (self.say_shake, LINES["shake"]), (self.say_gather, LINES["gather"]), (self.say_dig, LINES["dig"])]
        r = self.rafts[0]
        out += [(r["say_logs"], LINES["logs"]), (r["say_trim"], LINES["trim"]), (r["say_lash"], LINES["lash"]),
                (r["say_sail"], LINES["sail"]), (r["say_splash"], LINES["splash"]), (self.say_six, LINES["six"]),
                (self.say_walk, LINES["walk"])]
        out += [(self.marks[n], LINES[n]) for n in ("riffle", "f1", "lily", "rapids", "f2", "glide")]
        out += [(self.say_ready, LINES["ready"])]
        out += [(self.say[n], LINES[n]) for n in ("off", "over1", "lead", "over2", "catch", "win", "ducks", "late")]
        out += [(self.finale, FINALE), (self.signoff, SIGNOFF)]
        return out


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6
BUBBLE_R = 50.0


def voices(P):
    """The Keepers' little noises at their story beats: (t, kind, mood, picture or None for the mood's own)."""
    key = [(P.idea_t, "wheels", "idea", "raft")]                  # these first: they carry the story
    f = P.fin_t
    win_end = P.say["win"] + _dur(LINES["win"])
    key += [(win_end + 0.8, "teeth", "yay", None), (win_end + 2.2, "wheels", "aww", None),
            (win_end + 3.6, "tentacles", "yay", None), (win_end + 5.0, "digger", "hehe", None),
            (win_end + 6.4, "lantern", "ooh", None)]
    ev = [(P.walk_in[1] + 0.3, "springs", "ooh", None), (P.t_lip + 0.3, "teeth", "ooh", None),
          (P.t_lip + 1.6, "tentacles", "uhoh", None), (P.lady_fly[1] + 0.2, "digger", "aww", None), (P.spread[0] + 0.4, "springs", "yay", None),
          (P.bounces[0][0] + 0.2, "springs", "wee", None), (P.drop[1] + 0.3, "springs", "hehe", None),
          (P.picks[-1][1], "lantern", "mm", None), (P.dig_t[1] - 0.4, "digger", "huff", None),
          (P.digs_back[1] + 0.2, "digger", "mm", None)]
    for r in P.rafts:
        kd = r["owner"]
        ev.append((r["flare"][1] - 0.2, kd, "ooh" if r["k"] % 2 == 0 else "yay", None))  # its owner sees its colour
        ev.append((r["slip"][1] + 0.3, "wheels" if r["k"] % 3 == 0 else ("teeth" if r["k"] % 3 == 1 else "tentacles"),
                   "wee" if r["k"] % 2 else "yay", None))
    ev += [(P.tour[0] + 1.5, "springs", "hey", None), (P.tour_arrive["digger"] + 0.6, "digger", "mm", None),
           (P.count[0][0], "springs", "hm", None), (P.race_t0 + 0.8, "springs", "wee", None)]
    ev += [(P.race_t0 + 4.5, "springs", "wee", None), (P.race_t0 + 9.5, "springs", "ooh", None),
           (P.race_t0 + 14.0, "springs", "wee", None),
           (P.ducks[0] + 3.0, "teeth", "aww", None), (P.springs_go[1] + 0.4, "springs", "yay", None),
           (P.sign[1] + 0.3, "wheels", "yay", None)]
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    out = []

    def free(tv):
        return not any(a - 0.7 <= tv <= b + 0.7 for a, b in lines) and all(abs(tv - o[0]) >= 1.2 for o in out)
    for group in (key, sorted(ev, key=lambda e: e[0])):          # each near its beat, in the nearest quiet moment
        for tv, kd, mood, pic in group:
            for d in [0.0] + [s_ * 0.3 * n for n in range(1, 9) for s_ in (1, -1)]:
                if free(tv + d):
                    out.append((tv + d, kd, mood, pic))
                    break
    return sorted(out, key=lambda e: e[0])


def talking(P, kd, t):
    m, look, hop = 0.0, 0.0, 0.0
    for tv, k, mood, _ in P.voices:
        if k != kd or not (tv - 0.4 <= t <= tv + VOICE_DUR_S + 0.6):
            continue
        u = (t - tv) / VOICE_DUR_S
        if 0 <= u <= 1:
            m = max(m, 0.7 * math.sin(math.pi * u) * (0.75 + 0.25 * math.sin(u * 18)))
            hop = max(hop, 7 * K * math.sin(math.pi * u))
        look = max(look, smoothstep((t - tv + 0.4) / 0.4) * (1 - smoothstep((t - tv - VOICE_DUR_S - 0.2) / 0.4)))
    return m, look, hop


# ----------------------------------------------------------------------------------------------- hands

WR = 46.0 * K
JAW = 45.0                                  # Wheels' pincer jaws close on a thing this far past his wrist
SPRINGS_ARM = 47.0 * K
DIGS_ARM = 95.0 * K


def wheels_shoulder(x, y, sx, t):
    by = y - 210 * K + 3 * math.sin(t * 2.2) * K
    return x + sx * 100 * K, by + 10 * K


def wheels_rest(x, y, sx, t):
    sh = wheels_shoulder(x, y, sx, t)
    R = (WHEELS_UPPER + WHEELS_FORE) * K * 0.9
    return sh[0] + sx * math.sin(0.6) * R, sh[1] + math.cos(0.6) * R


def wrist_for(sh, grip):
    """Where Wheels' wrist goes so his jaws close on `grip` (nearer than his jaws are long: the arm folds)."""
    d = math.hypot(grip[0] - sh[0], grip[1] - sh[1]) or 1.0
    j = min(JAW, 0.6 * d)
    return grip[0] - (grip[0] - sh[0]) / d * j, grip[1] - (grip[1] - sh[1]) / d * j


def twigs_shoulder(x, y, sx, t):
    sway = 4 * math.sin(t * 1.1) * K
    cy = y - 350 * K + sway * 0.3
    return x + sway + sx * 82 * K, cy + 10 * K


def twigs_rest(x, y, sx, t):
    sh = twigs_shoulder(x, y, sx, t)
    R = (TWIGS_UPPER + TWIGS_FORE) * K * 0.93
    return sh[0] + sx * math.sin(0.16) * R, sh[1] + math.cos(0.16) * R


def arm_angle(sh, p, sx):
    """(angle from straight down, outward positive for side sx; distance) of point p from shoulder sh."""
    dx, dy = (p[0] - sh[0]) * sx, p[1] - sh[1]
    return math.atan2(dx, dy), math.hypot(dx, dy)


def arc(sh, p0, p1, u, sx, ext=None, phi=26.6):
    """A hand going from p0 to p1 round the shoulder (angle and reach eased, not a straight line through the body);
    ext: how far the arm reaches out on the way (straight, so its elbow never flips). phi (deg): the direction of the
    arm's elbow preference in monster.py (Wheels 26.6, Twigs 21.8); angles are taken within 180 of it, so the hand
    never swings through the opposite direction, where the elbow would flip."""
    lo = math.radians(phi) - math.pi
    a0, r0 = arm_angle(sh, p0, sx)
    a1, r1 = arm_angle(sh, p1, sx)
    a0 = lo + (a0 - lo) % (2 * math.pi)
    a1 = lo + (a1 - lo) % (2 * math.pi)
    e = smoothstep(min(max(u, 0.0), 1.0))
    a = a0 + (a1 - a0) * e
    r = r0 + (r1 - r0) * e
    if ext is not None:                                       # straight while it passes the elbow's turn-over line
        near = max(0.0, 1.0 - abs(a - math.radians(phi)) / math.radians(12.0))
        r += (ext - r) * max(smoothstep(min(1.0, 2.5 * math.sin(math.pi * e))), smoothstep(near))
    return sh[0] + sx * math.sin(a) * r, sh[1] + math.cos(a) * r


def blend(rest, target, u):
    return rest if target is None else lerp2(rest, target, u)


def digs_shoulder(x, y, sx, t):
    by = y - 150 * K + 2 * K * math.sin(t * 2.6)
    return x + sx * 118 * K, by + 4 * K


def springs_shoulder(x, y, sx, t, sq):
    s = sq + 0.06 * math.sin(t * 3.0)
    return x + sx * 100 * K, y - (170 - 46 * s) * K + 10 * K


def glo_bob(t):
    return 14 * K * math.sin(t * 1.3)


# ----------------------------------------------------------------------------------------------- the Keepers

def _sink(P, kd, t, x):
    hip, leg = {"digger": (62.0, 78.0)}[kd]
    n = 1.0 - TURN_NARROW * abs(P.turns[kd](t))
    g = P.gaits[kd]
    d = 0.0
    for i, hx in enumerate((x - hip * K * n, x + hip * K * n)):
        fx, fy, down, _ = g.foot(i, t)
        if down:
            dx = min(abs(fx - hx), leg * K * 0.95)
            # the foot on the slope stands a little higher or lower than under the hip
            dd = (leg * K - math.sqrt((leg * K) ** 2 - dx * dx)) - (fy - RW.ground(x))
            d = max(d, dd)
    return d


def keeper(kd, t):
    """(world x, screen y of its feet, monster attrs) of Keeper kd at time t, talking when it says something."""
    x, y, a = _keeper(kd, t)
    P = plan()
    a["legs_turn"] = P.turns[kd](t)
    a["turn"] = a["legs_turn"] * (1 - a.pop("face_us", 0.0))
    if P.voices:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd in ("wheels", "springs", "lantern") and not a.get("_fixed"):
                y -= hop
    a.pop("_fixed", None)
    return x, y, a


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":
            a.update(float=0.2, **hans_mood(*P.hans_mood_at(t)))
            return x, RW.ground(x) + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            y = RW.ground(x)
            a.update(hands=True, saws=False, blades=0.0, blades_l=0.0, knee_fwd=True, clamp_reach=True)
            hd, blade, grip, up = twigs_hand(P, t, x, y)
            if hd is not None:
                a.update(arm_to={-1: (hd[0] - sh, hd[1])}, blades_l=blade, grip=grip)
            if up > 0:                                             # both arms up: he cheers (his raft won)
                to = {}
                for sx in (-1, 1):
                    s_ = twigs_shoulder(x, y, sx, t)
                    p = arc(s_, twigs_rest(x, y, sx, t), (s_[0] + sx * 60, s_[1] - 95), up, sx,
                            (TWIGS_UPPER + TWIGS_FORE) * K * 0.995, phi=21.8)
                    to[sx] = (p[0] - sh, p[1])
                a.update(arm_to=to, smile=0.6 + 0.4 * up)
            return x, y, a
        y = RW.ground(x) + _sink(P, kd, t, x)
        ang = digs_paw(P, t, x, y)
        if ang is not None:
            a["paw_ang"] = ang
        return x, y, a
    if kd == "springs":
        if P.shake0 - 0.5 <= t < P.drop[1] + 0.5:                 # the maple: up, hangs and bounces, drops
            x = STOPS["work"]["springs"]
            lift, sq = P.springs_lift(t)
            y = RW.ground(x) - lift
            a = dict(spring=sq, attend=0.25, arm_swing=0.0, _fixed=True)
            if P.hop_up[0] + 0.15 <= t < P.let_go:
                gx, gy = P.branch_at(P.grab_u(), t)
                a["arm_to"] = {1: (gx - sh, gy)}
            return x, y, a
        x, yr, sq = P.hopper.state(t)
        y = RW.ground(x) + yr
        a = dict(spring=sq, attend=0.25, arm_swing=0.0)
        lift, sq2 = springs_start(P, t)
        if lift or sq2:
            y -= lift
            a["spring"] = sq + sq2
            a["_fixed"] = True
        hd = springs_pin_hand(P, t, x, y, a["spring"])
        if hd is not None:
            a["arm_to"] = {1: (hd[0] - sh, hd[1])}
        return x, y, a
    if kd == "wheels":
        x = P.paths[kd](t)
        y = RW.ground(x)
        a = dict(wheel_rot=x / WR, attend=0.25, arm_swing=roll_swing(P.paths[kd], t, WR), clamp_reach=True)
        hands, grip = wheels_hands(P, t, x, y)
        if hands:
            a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, grip=grip)
        return x, y, a
    # Glo floats at the meadow's depth, behind the path
    x = P.paths[kd](t)
    return x, glo_y(P, t, x), dict(attend=0.25, lamp=1.0 + 0.9 * glo_flare(P, t))


WHEELS_R = (WHEELS_UPPER + WHEELS_FORE) * K       # his arm's full reach (shoulder to wrist)


REST_A = math.radians(12.0)                         # Wheels' arms at rest: hanging a little out (inside the
#                                                     side his elbow keeps in monster.py's arm_to, so it never flips)


def wheels_rest_at(P, x, y, sx, t):
    """Wheels' wrist at rest, swinging a little as he rolls (his own arm, never monster.py's hanging arm: one way of
    bending all the episode)."""
    sh = wheels_shoulder(x, y, sx, t)
    sw = roll_swing(P.paths["wheels"], t, WR) * sx
    a = REST_A + math.radians(6.0) * sw
    R = WHEELS_R * 0.9
    return sh[0] + sx * math.sin(a) * R, sh[1] + math.cos(a) * R


def wheels_hands(P, t, x, y):
    """Wheels' wrists (world) and how hard his pincers close, all episode: at rest (a little swing as he rolls), and
    for each raft's bundle from the pile to the slide - the left takes it from the pile and lifts it up over his head,
    the right joins at the top and lays it on the slide. Every move is an arc round the shoulder; where it crosses
    the line his elbow turns over at, the arm is straight (so the elbow never jumps)."""
    sh = {sx: wheels_shoulder(x, y, sx, t) for sx in (-1, 1)}
    rest = {sx: wheels_rest_at(P, x, y, sx, t) for sx in (-1, 1)}
    out, grip = dict(rest), 0.3
    ext = WHEELS_R * 0.995
    for r in P.rafts:
        k = r["k"]
        if not (r["go"][1] - 0.2 <= t < r["back"][1] + 0.4):
            continue
        bx, by_ = P.wheels_bundle(k, t)
        gl = wrist_for(sh[-1], (bx - 22.0, by_ - 18.0))
        gr = wrist_for(sh[1], (bx + 22.0, by_ - 18.0))
        if t < r["pick"][1]:
            out[-1] = arc(sh[-1], rest[-1], gl, _seg(t, r["go"][1] - 0.2, r["pick"][1] - 0.2), -1, ext)
        elif t < r["lay"][0]:
            out[-1] = gl
        else:
            g0 = P.wheels_bundle(k, r["lay"][0])
            out[-1] = arc(sh[-1], wrist_for(sh[-1], (g0[0] - 22.0, g0[1] - 18.0)), rest[-1],
                          _seg(t, r["lay"][0], r["lay"][0] + 0.9), -1, ext)
        if t < r["lift"][1] - 0.6:
            pass
        elif t < r["lift"][1]:
            g1 = P.wheels_bundle(k, r["lift"][1])
            out[1] = arc(sh[1], rest[1], wrist_for(sh[1], (g1[0] + 22.0, g1[1] - 18.0)),
                         _seg(t, r["lift"][1] - 0.6, r["lift"][1]), 1, ext)
        elif t < r["release_w"][0]:
            out[1] = gr
        else:
            g0 = P.wheels_bundle(k, r["release_w"][0])
            out[1] = arc(sh[1], wrist_for(sh[1], (g0[0] + 22.0, g0[1] - 18.0)), rest[1],
                         _seg(t, r["release_w"][0] + 0.1, r["back"][1]), 1, ext)
        grip = 1.0 if r["pick"][1] - 0.3 <= t < r["release_w"][0] + 0.15 else 0.3
        break
    return out, grip


def twigs_hand(P, t, x, y):
    """Twigs' left hand (world), his left blade 0..1, grip, and his cheer (both arms up) at the finish."""
    up = _seg(t, P.fin_t + 0.2, P.fin_t + 1.0) * (1 - _seg(t, P.fin_t + 4.5, P.fin_t + 5.4))
    rest = twigs_rest(x, y, -1, t)
    for r in P.rafts:
        if not (r["reach_t"][0] <= t < r["peg1"][1] + 0.7):
            continue
        cut = CUT_HAND
        if t < r["blade_in"][1] + 0.1:
            u = ease(t, *r["reach_t"])
            hd = blend(rest, cut, u)
            s = 0.0
            for i, (a, b) in enumerate(r["strokes"]):              # a saw stroke along the blade, then a little deeper
                if a <= t < b:
                    s = 6.0 + 6.0 * math.sin(2 * math.pi * _seg(t, a, b)) + (i - 1.5) * 1.0
            hd = (hd[0] + CUT_DIR[0] * s, hd[1] + CUT_DIR[1] * s)
            blade = ease(t, *r["blade"]) * (1 - ease(t, *r["blade_in"]))
            return hd, blade, 0.25, up
        peg = (PEGS[0] + 4.0, rail_y(PEGS[0]) - 22.0)
        if t < r["peg1"][0] + 0.35:
            hd = lerp2(cut, peg, ease(t, r["blade_in"][1], r["peg1"][0] + 0.35))
        else:
            push = ease(t, r["peg1"][0] + 0.35, r["peg1"][1] - 0.1)
            hd = (peg[0] + 6 * push, peg[1] + 9 * push)
            hd = lerp2(hd, rest, ease(t, r["peg1"][1], r["peg1"][1] + 0.7))
        return hd, 0.0, 0.5, up
    return None, 0.0, 0.0, up


def peg_down(P, i, t):
    """0 up (holding the raft at station i) .. 1 tapped flat (the raft slides on), for the raft there now."""
    key = ("peg1", "peg2", "peg3")[i]
    for r in P.rafts:
        a, b = r[key]
        if a + 0.3 <= t < b + 0.6:
            return ease(t, a + 0.35, a + 0.6)
        if b + 0.6 <= t < b + 1.6:                                # pops back up behind it (a little spring peg)
            return 1.0 - ease(t, b + 0.9, b + 1.3)
    return 0.0


def hans_targets(P, t, x, y):
    """Hans' working tentacles: [(slot, world target, grip)]: one always has his ball of twine; while lashing one
    winds and one steadies the logs; a tip taps the second peg."""
    ball = hans_ball(P, t, x, y)
    out = [(-1, ball, 1.0)]
    for r in P.rafts:
        if not (r["lashA"][0] - 0.6 <= t < r["peg2"][1] + 0.6):
            continue
        rs = P.raft_state(r["k"], t)
        rx, ry = rs["x"], rs["y"]
        top = ry - RW.LOG_T - 3 * 7.0
        steady = (rx + 10.0, top + 4.0)
        us = ease(t, r["lashA"][0] - 0.6, r["lashA"][0]) * (1 - ease(t, r["lashB"][1], r["lashB"][1] + 0.5))
        out.append((0, steady, us))
        wind = None
        for q, (a, b) in enumerate((r["lashA"], r["lashB"])):
            lx = rx + (-0.3 if q == 0 else 0.3) * RW.RAFT_L
            if a <= t < b:                                         # round and round the four logs
                ph = 2 * math.pi * 3.0 * _seg(t, a, b)
                wind = (lx + 5.0 + 10.0 * math.sin(ph), ry - 18.0 - 16.0 * math.cos(ph))
        if wind is None:                                           # between the lashings / to the peg
            la = (rx - 0.3 * RW.RAFT_L + 5.0, ry - 34.0)
            lb = (rx + 0.3 * RW.RAFT_L + 5.0, ry - 34.0)
            peg = (PEGS[1] + 4.0, rail_y(PEGS[1]) - 20.0)
            if t < r["lashA"][0]:
                wind = la
                g = ease(t, r["lashA"][0] - 0.6, r["lashA"][0])
            elif t < r["lashB"][0]:
                wind = lerp2(la, lb, ease(t, r["lashA"][1], r["lashB"][0]))
                g = 1.0
            elif t < r["peg2"][0] + 0.4:
                wind = lerp2(lb, peg, ease(t, r["lashB"][1], r["peg2"][0] + 0.4))
                g = 1.0
            else:
                push = ease(t, r["peg2"][0] + 0.4, r["peg2"][1] - 0.1)
                wind = (peg[0] + 6 * push, peg[1] + 9 * push)
                g = 1.0 - ease(t, r["peg2"][1], r["peg2"][1] + 0.6)
            out.append((-2, wind, g))
        else:
            out.append((-2, wind, 1.0))
        return out
    return out


def hans_ball(P, t, x, y):
    """His ball of twine: held up by his side, or over the raft he is lashing (the twine runs from it)."""
    hold = (x - 118.0, y - 200.0)
    for r in P.rafts:
        if r["lashA"][0] - 1.0 <= t < r["lashB"][1] + 1.0:
            over = (RW.ST[1] + 95.0, rail_y(RW.ST[1]) - 85.0)
            u = ease(t, r["lashA"][0] - 1.0, r["lashA"][0] - 0.2) * (1 - ease(t, r["lashB"][1], r["lashB"][1] + 1.0))
            return lerp2(hold, over, u)
    return hold


def hans_mood_at(self, t):
    if self.fin_t - 0.5 <= t < self.fin_t + 6.0:
        return ("calm", "excited", ease(t, self.fin_t - 0.5, self.fin_t + 0.3) * (1 - ease(t, self.fin_t + 4.0,
                                                                                         self.fin_t + 6.0)))
    if self.t_lip - 0.2 <= t < self.t_lip + 3.0:
        return ("calm", "surprised", ease(t, self.t_lip - 0.2, self.t_lip + 0.4) * (1 - ease(t, self.t_lip + 1.8,
                                                                                            self.t_lip + 3.0)))
    return ("calm", None, 0.0)


Plan.hans_mood_at = hans_mood_at


def digs_paw(P, t, x, y):
    """Digs' paw angles: clearing the slide's foot (a mole's strokes), tapping the last peg."""
    d = P.digs_paws(t)
    if d is not None:
        u = ease(t, P.dig_t[0] - 0.3, P.dig_t[0])
        if u < 1:
            return {s: (math.radians(112.0) if s < 0 else math.radians(68.0)) * (1 - u) + d[s] * u for s in d}
        return d
    for r in P.rafts:
        a, b = r["peg3"]
        if a - 0.5 <= t < b + 0.6:
            sh = digs_shoulder(x, y, -1, t)
            peg = (PEGS[2] + 4.0, rail_y(PEGS[2]) - 20.0)
            push = ease(t, a + 0.3, b - 0.1)
            tg = (peg[0] + 6 * push, peg[1] + 9 * push)
            ang = math.atan2(tg[1] - sh[1], tg[0] - sh[0])
            rest = math.radians(112.0)
            u = ease(t, a - 0.5, a + 0.1) * (1 - ease(t, b, b + 0.6))
            return {-1: rest + (ang - rest) * u}
    return None


def springs_start(P, t):
    """Springs' three little bounces for 3, 2, 1: (lift px, squash)."""
    for a, b in P.count:
        if a <= t < b:
            u = _seg(t, a, a + 0.6)
            if u < 1:
                return 16.0 * math.sin(math.pi * u), 0.3 * math.sin(math.pi * u) * (u < 0.15 or u > 0.85)
    return 0.0, 0.0


PIN = (PIN_POST, RW.near_edge(PIN_POST) - 34.0)             # its top, in the post


def pin_pos(P, t):
    """The start boom's pin (world): in its post, in Springs' left hand, dropped on the path."""
    if t < P.pin[0] + 0.3:
        return PIN, "post"
    td = P.springs_go[0] - 0.6                                     # he drops it as he sets off
    tq = min(t, td - 1e-3)
    x, y, a = keeper("springs", tq)
    hd = springs_pin_hand(P, tq, x, y, a.get("spring", 0.0))
    if t < td:
        return hd, "hand"
    u = t - td
    gy = RW.ground(hd[0]) + 6
    y = min(gy, hd[1] + 0.5 * 1500 * u * u)
    return (hd[0], y), ("falling" if y < gy else "ground")


def springs_pin_hand(P, t, x, y, sq):
    if not (P.pin[0] - 0.4 <= t < P.springs_go[0] - 0.6):
        return None
    sh = springs_shoulder(x, y, 1, t, sq)
    lift = 24.0 * ease(t, P.pin[0] + 0.3, P.pin[1])
    tg = (PIN[0], PIN[1] - lift)
    if t >= P.pin[1]:
        tg = lerp2(tg, (sh[0] + 22.0, sh[1] + 20.0), ease(t, P.pin[1], P.pin[1] + 0.6))
    d = math.hypot(tg[0] - sh[0], tg[1] - sh[1]) or 1.0
    return sh[0] + (tg[0] - sh[0]) / d * SPRINGS_ARM, sh[1] + (tg[1] - sh[1]) / d * SPRINGS_ARM


# ----------------------------------------------------------------------------------------------- Glo

SPRINGS_V = 100.0                           # Springs hops after the pack at this pace: always behind the last raft
CRUISE = 160.0                              # Glo floats with his feet this far above the path (behind it)


def glo_hold_dy():
    """From Glo's y to where his tendrils hold his bunch (the twigs' middles)."""
    return -95.0


def glo_y(P, t, x):
    """Glo's y: cruising behind the path; down to the twigs on the meadow; down a little to plant each one."""
    base = RW.ground(x) - CRUISE
    if t >= P.tour[0]:
        lift = 0.0
        return base - lift + glo_bob(t) * 0
    low = RW.near_edge(P.glo_pick_x()) + 34.0 - glo_hold_dy() - 48.0 + 48.0   # his tendrils at the twigs on the ground
    if P.glo_down[0] <= t < P.glo_up[1]:
        u = ease(t, P.glo_down[0] + 0.8, P.glo_down[1]) * (1 - ease(t, *P.glo_up))
        return base + (low - base) * u
    for r in P.rafts:
        if r["lower"][0] <= t < r["rise"][1]:
            mx, my = RW.mast_foot(RW.ST[2], rail_y(RW.ST[2]) - 1, 1.0)
            plant = my - 48.0 - glo_hold_dy() - glo_bob(t)
            u = ease(t, *r["lower"]) * (1 - ease(t, *r["rise"]))
            return base + (plant - base) * u
    return base


def glo_flare(P, t):
    u = 0.0
    for r in P.rafts:
        a, b = r["flare"]
        u = max(u, ease(t, a - 0.3, a + 0.2) * (1 - ease(t, b - 0.2, b + 0.4)))
    f = P.fin_t
    u = max(u, ease(t, f + 3.4, f + 3.9) * (1 - ease(t, f + 5.0, f + 5.6)))
    return u


def glo_bunch(P, t):
    """The leafy twigs in Glo's bunch now: [(i, x, foot y)] (world)."""
    gx, gy = P.paths["lantern"](t), glo_y(P, t, P.paths["lantern"](t))
    hold = gy + glo_hold_dy() + glo_bob(t)
    out = []
    for i in range(6):
        if t < P.picks[i][1]:
            continue
        if t >= P.rafts[i]["plant"][0]:
            continue
        out.append((i, gx + GLO_TWIGS[i], hold + 48.0))
    return out


def twig_state(P, i, t):
    """Leafy twig i: (world x, foot y, angle deg, state, holder) - on the branch, falling, on the meadow, rising into
    Glo's bunch, in the bunch, in raft i's deck."""
    if t < P.picks[i][0]:
        return (*P.twig_pos(i, t), None)
    gx = P.paths["lantern"](t)
    gy = glo_y(P, t, gx)
    bunch = (gx + GLO_TWIGS[i], gy + glo_hold_dy() + glo_bob(t) + 48.0)
    if t < P.picks[i][1]:                                          # his tendrils lift it, standing it up
        x0, y0, a0, _ = P.twig_pos(i, P.picks[i][0])
        u = ease(t, *P.picks[i])
        return (x0 + (bunch[0] - x0) * u, y0 + (bunch[1] - y0) * u, a0 * (1 - u), "rising", "Glo's tendrils")
    if t < P.rafts[i]["plant"][0]:
        return (*bunch, 0.0, "bunch", "Glo's tendrils")
    rs = P.raft_state(i, t)
    mx, my = RW.mast_foot(RW.at_depth(rs["x"], rs["d"]) if rs["where"] == "water" else rs["x"], rs["y"],
                          rs.get("sc", 1.0))
    return mx, my, rs["pitch"], "deck", "raft"


# ----------------------------------------------------------------------------------------------- the ladybird, ducks

def leaf_state(P, t):
    """The leaf boat: (world x, screen y of its waterline, pitch, lane depth)."""
    x = P.leaf_x(t)
    d = P.leaf_lane
    y = RW.lane_y(d, x) + RW.wave(x, t, int(d)) * 0.6 * (0.0 if RW.on_chute(x) else 1.0)
    sl = RW.surface_slope(x)
    return x, y, math.degrees(math.atan(sl)), d


def ladybird_state(P, t):
    """(world-screen x, y, fly 0..1, state)."""
    lx, ly, lp, d = leaf_state(P, min(t, P.lady_fly[0]))
    on = (RW.at_depth(lx, d) + 4.0, ly - 11.0)
    if t < P.lady_fly[0]:
        return on[0], on[1], 0.0, "leaf"
    reed = (RW.LADY_REED + RW.FDX + 4.0, RW.far_edge(RW.LADY_REED) - 4 - 54.0)
    if t < P.lady_fly[1]:
        u = _seg(t, *P.lady_fly)
        e = u * u * (3 - 2 * u)
        bump = math.sin(math.pi * u) ** 2                          # its loops ease out as it lands
        x = on[0] + (reed[0] - on[0]) * e + 30 * math.sin(u * 5.0) * bump
        y = on[1] + (reed[1] - on[1]) * e - 70 * bump
        return x, y, min(1.0, u * 6, (1 - u) * 6), "flying"
    return reed[0], reed[1], 0.0, "reed"


DUCK_S, CHICK_S = 72.0, 32.0
LADY_S = 22.0                               # the ladybird (px long): big enough to see, a storybook ladybird


def duck_states(P, t):
    """The mother duck and three ducklings: [(name, world x, depth, face, size, chick)] - out of the reeds on the far
    bank of the finish pool, among the rafts, the ducklings in a line behind her."""
    a, b = P.ducks
    if t < a:
        return []
    out = []
    for n in range(4):
        lag = 1.1 * n
        u = _seg(t - lag, a, b)
        e = u * u * (3 - 2 * u)
        x0, x1 = RW.DUCK_REEDS[1], RW.FINISH + 90.0
        x = x0 + (x1 - x0) * e
        d = 5.7 - 2.0 * smoothstep(min(1.0, u * 2.5))
        name = "mother duck" if n == 0 else f"duckling {n}"
        out.append((name, x, d, -1, DUCK_S if n == 0 else CHICK_S, n > 0))
    return out


# ----------------------------------------------------------------------------------------------- drawing: the slide

def draw_slide(pg, t, sh):
    """The old wooden slide on the bank: two poles on trestles (the stop block, the notch, three spring pegs), and its
    foot down the bank into the pool (cleared by Digs)."""
    P = plan()
    near, far = rail_y, (lambda x: rail_y(x) - 20.0)
    for x in np.arange(RAIL0 + 30.0, RW.SLIP, 260.0):              # trestles: an X of sticks under the poles
        y0, yb = rail_y(x), RW.ground(x) - 48.0
        for dx in (-26, 26):
            pg.stroke(skia.Path().moveTo(x - sh - dx, y0 + 4).lineTo(x - sh + dx, yb), tone(RW.RAIL, -0.12), 7.0)
    tr = P.trench(t)                                               # the slide's foot: mud, then cleared
    xa, xb = RW.SLIP + 10, SLIP_END + 20
    pg.flat(smooth([(xa - sh, RW.ground(xa) - 44), (xb - sh, RW.near_edge(xb) + 2), (xb + 40 - sh, RW.near_edge(xb) + 10),
                    (xa + 40 - sh, RW.ground(xa) - 36)]), mix((120, 92, 68), (98, 128, 142), 0.6 * tr), 0.9)
    if tr < 1:                                                     # the mud plug at its foot (Digs scoops it out)
        cx, cy = SLIP_END - 30, RW.near_edge(SLIP_END) - 6
        pg.shape(oval(cx - sh, cy, 60 * (1 - tr) + 4, 16 * (1 - tr) + 2), (128, 96, 70), 0.12)
    for side, yf in ((1, far), (0, near)):                         # the poles: far first
        p = skia.Path()
        for i, x in enumerate(np.linspace(RAIL0, RW.SLIP, 24)):
            (p.moveTo if i == 0 else p.lineTo)(x - sh + (6 if side else 0), yf(x))
        for i in range(1, 9):
            u = i / 8
            x, y = slip_curve(u)
            p.lineTo(x - sh + (6 if side else 0), y - (20.0 if side else 0) * (1 - u))
        pg.stroke(p, tone(RW.RAIL, -0.06 if side else 0.04), 9.0)
        if not side:
            pg.stroke(p, tone(RW.RAIL, 0.2), 2.5, 0.8)
    pg.shape(rrect(STOP_X - 10 - sh, rail_y(STOP_X) - 36, STOP_X - sh, rail_y(STOP_X) + 4, 2), tone(RW.RAIL, -0.1), 0.1)
    pg.flat(rrect(NOTCH_X - 1.5 - sh, rail_y(NOTCH_X) - 3, NOTCH_X + 1.5 - sh, rail_y(NOTCH_X) + 4, 1), (246, 240, 226))
    for i, px in enumerate(PEGS):                                  # the pegs (spring back up after each raft)
        u = peg_down(P, i, t)
        ang = -80.0 * u
        c = pg.c
        c.save()
        c.rotate(ang, px - sh, rail_y(px) + 2)
        pg.shape(rrect(px - 3.5 - sh, rail_y(px) - 22, px + 3.5 - sh, rail_y(px) + 3, 3), (176, 136, 96), 0.0)
        c.restore()


def draw_heaps(pg, t, sh):
    P = plan()
    for sx in (-1, 1):
        cx, h = P.spoil.heap(sx, t)
        h = max(0.0, h - P.spoil.h0) * 0.45
        if h <= 0.3:
            continue
        r = 2.0 * h + 10
        y = P.spoil.rim
        pg.shape(smooth([(cx - r - sh, y + 4), (cx - r * 0.5 - sh, y - h * 0.6), (cx - sh, y - h),
                         (cx + r * 0.5 - sh, y - h * 0.6), (cx + r - sh, y + 4), (cx - sh, y + 6)]), (128, 96, 70), 0.12)


def draw_soil(pg, t, sh):
    P = plan()
    for name, px, py, size, carried, _ in P.spoil.pieces(t, STEP):
        pg.shape(oval(px - sh, py, size, size * 0.85), (112, 84, 62), 0.12)


# ----------------------------------------------------------------------------------------------- drawing: rafts, logs

def on_bank(rs):
    """Drawn with the bank (after the meadow, before the Keepers): in the pile, in Wheels' pincers, on the slide, and
    afloat until it is clear of the slide's foot (so it never pops behind or in front of it)."""
    if rs["where"] in ("pile", "wheels", "st1", "st2", "st3", "rails", "slip"):
        return True
    return rs["where"] == "water" and rs["x"] - RW.RAFT_L / 2 < SLIP_END + 10.0 and \
        rs.get("tau", -1.0) < 0


def raft_screen(rs, sh):
    if rs["where"] == "water":
        return RW.at_depth(rs["x"], rs["d"]) - sh, rs["y"], rs.get("sc", 1.0)
    if rs["where"] == "slip":
        return RW.at_depth(rs["x"], rs["d"] * ease(rs["x"], RW.SLIP + 20, FLOAT_X0)) - sh, rs["y"], 1.0
    return rs["x"] - sh, rs["y"], 1.0


def draw_one_raft(pg, k, t, sh, rs=None):
    rs = rs or plan().raft_state(k, t)
    x, y, s = raft_screen(rs, sh)
    col = RW.COLS[OWNERS[k]]
    mast = 1.0 if rs["mast"] else None
    RW.draw_raft(pg, x, y, s, col, t, pitch=rs["pitch"], logs=rs["logs"], ext=rs["ext"],
                 lash=rs["lash"] if rs["where"] not in ("pile", "carried", "wheels", "st1") else (0.0, 0.0),
                 mast=mast, dye=rs["dye"], water=rs.get("water"), wake=rs.get("wake", 0.0))


def draw_offcuts(pg, t, sh):
    for name, x, y, ln, _ in offcuts(t):
        pg.shape(rrect(x - ln / 2 - sh, y - RW.LOG_T, x + ln / 2 - sh, y, RW.LOG_T / 2), tone(RW.LOG, -0.05), 0.1)
        pg.flat(oval(x - ln / 2 + 4 - sh, y - RW.LOG_T / 2, 3.5, 6), RW.LOG_END)


OFFCUT_REST = GB - 44.0


def offcuts(t):
    """Every log end Twigs has sawn off: [(name, world x, y of its bottom, length, falling)] - it drops from the
    notch onto the meadow under the slide and lies there."""
    P = plan()
    out = []
    for r in P.rafts:
        for i, (a, b) in enumerate(r["strokes"]):
            if t < b:
                continue
            k = 3 - i
            ln = r["ext"][k]
            x0 = NOTCH_X + ln / 2 + RW.LOG_DX * k
            y0 = rail_y(NOTCH_X) - 1 + RW.LOG_DY * k
            yr = OFFCUT_REST + 6.0 * (r["k"] % 3) - 2.0 * i
            u = t - b
            y = y0 + 0.5 * 1500 * u * u
            xr = x0 + 18.0 + 9.0 * ((r["k"] * 4 + i) % 5)
            fall = math.sqrt(2 * max(yr - y0, 1.0) / 1500)
            if y < yr:
                x = x0 + (xr - x0) * (u / fall)
                out.append((f"offcut {r['k']}.{i}", x, y, ln, True))
            else:
                out.append((f"offcut {r['k']}.{i}", xr, yr, ln, False))
    return out


def draw_pile(pg, t, sh):
    """The driftwood on the bank: the bundles not yet taken (top first)."""
    P = plan()
    for k in reversed(range(6)):
        rs = P.raft_state(k, t)
        if rs["where"] == "pile":
            RW.draw_raft(pg, rs["x"] - sh, rs["y"], 1.0, RW.COLS[OWNERS[k]], t, ext=rs["ext"], lash=(0, 0), mast=None)


def draw_twig(pg, i, t, sh, only=None):
    P = plan()
    x, y, ang, state, _ = twig_state(P, i, t)
    if only is not None and state not in only:
        return
    if state == "deck":
        return                                                     # drawn with its raft
    RW.draw_leafy_twig(pg, x - sh, y, 1.0, RW.COLS[OWNERS[i]], 0.0, t, ang)


def draw_branch(pg, t, sh):
    P = plan()
    (x0, y0), (x1, y1) = P.branch_pts(t)
    pg.shape(tube([(x0 - sh, y0), ((x0 + x1) / 2 - sh, (y0 + y1) / 2 - 4), (x1 - sh, y1)], 7.0, 3.5), RW.TRUNK, 0.1,
             (0.0, -0.4))
    for k in range(5):                                             # its own leaves (they stay on)
        u = 0.15 + 0.2 * k
        bx, by = P.branch_at(u, t)
        p = RW.leaf_path(bx - sh, by, 34.0, 150.0 + 25 * k)
        pg.shape(p, (RW.PAL["orange"], RW.PAL["ochre"])[k % 2], 0.1)


# ----------------------------------------------------------------------------------------------- overlays

_FONT = {}
INK, PAPER = (70, 52, 44), (252, 246, 234)


def _font(size, weight="Bold"):
    key = (size, weight)
    if key not in _FONT:
        import os
        path = os.path.join("engine", "assets", "fonts", f"Inter-{weight}.otf")
        _FONT[key] = skia.Font(skia.Typeface.MakeFromFile(path), size)
    return _FONT[key]


def _text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold", center=False):
    f = _font(size, weight)
    if center:
        x -= f.measureText(s) / 2
    pg.c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def _card(pg, x, y, w, h, a, r=18):
    pg.flat(rrect(x + 4, y + 6, x + w + 4, y + h + 6, r), (40, 28, 24), 0.18 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, r), PAPER, 0.94 * a)


def name_tags(pg, t, a):
    P = plan()
    sh = P.shift(t)
    for kd in ORDER:
        x, y, _ = keeper(kd, t)
        if 60 < x - sh < W - 60:
            top = y - KH[kd] * K - 26
            tw = _font(30).measureText(NAMES[kd])
            _card(pg, x - sh - tw / 2 - 16, top - 34, tw + 32, 46, a)
            _text(pg, NAMES[kd], x - sh, top, 30, a=a, center=True)


def overlays(pg, t):
    """Screen-space text (drawn straight onto the frame, fading, never moving): the name tags as they arrive, the
    countdown, the standings strip in the race, the end sign."""
    P = plan()
    a = ease(t, P.walk_in[1] - 2.0, P.walk_in[1] - 1.0) * (1 - ease(t, P.walk_in[1] + 3.5, P.walk_in[1] + 4.5))
    if a > 0:
        name_tags(pg, t, a)
    for n, (c0, c1) in enumerate(P.count):                        # 3, 2, 1
        u = ease(t, c0, c0 + 0.15) * (1 - ease(t, c1 - 0.25, c1))
        if u > 0:
            x, y = 300, 300
            pg.flat(oval(x, y - 40, 74, 74), PAPER, 0.92 * u)
            _text(pg, str(3 - n), x, y, 96, col=RW.COLS["springs"], a=u, center=True)
    hud(pg, t)
    end_sign(pg, t)


def hud(pg, t):
    """The standings: the six sails in race order, in a little wooden strip at the top left."""
    P = plan()
    t_off = P.say["late"]
    if not (P.race_t0 - 0.5 <= t < t_off):
        return
    a = ease(t, P.race_t0 - 0.5, P.race_t0 + 0.3) * (1 - ease(t, t_off - 1.0, t_off))
    tau = max(0.0, t - P.race_t0)
    order = P.race.standings(tau)
    x0, y0 = 40, 36
    pg.flat(rrect(x0 + 4, y0 + 6, x0 + 6 * 64 + 28 + 4, y0 + 96 + 6, 16), (40, 28, 24), 0.2 * a, blur=8)
    pg.flat(rrect(x0, y0, x0 + 6 * 64 + 28, y0 + 96, 16), (176, 132, 90), 0.95 * a)
    for i, lane in enumerate(order):
        k = LANE.index(lane)
        cx = x0 + 46 + 64 * i
        done = P.race.finish[lane] <= tau
        pg.flat(oval(cx, y0 + 46, 26, 26), PAPER, (0.95 if done else 0.75) * a)
        p = RW.leaf_path(cx - 4, y0 + 68, 44.0)
        pg.flat(p, RW.COLS[OWNERS[k]], a)
        _text(pg, str(i + 1), cx, y0 + 92, 16, col=PAPER, a=a, center=True)


def end_sign(pg, t):
    P = plan()
    sa = ease(t, *P.sign)
    if sa <= 0:
        return
    bw, bh = 1120, 210
    x0, y0 = (W - bw) / 2, 70
    pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * sa, blur=10)
    pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), sa)
    pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), sa)
    _text(pg, "WHAT SHOULD THEY BUILD NEXT?", W / 2, y0 + 104, 54, col=PAPER, a=sa, center=True)
    _text(pg, "Tell us in the comments", W / 2, y0 + 162, 34, col=(250, 232, 200), a=sa, weight="Medium", center=True)
    name_tags(pg, t, sa)


def bubbles(pg, t):
    from .chatter import MOODS, _back, bubble
    P = plan()
    sh = P.shift(t)
    for tv, kd, mood, pic in P.voices:
        u = t - tv
        pic = pic or MOODS[mood][2]
        if pic is None or pic in ("!", "?") or not (0 <= u < 1.4) or t >= P.sign[0] - 4.0:
            continue
        if (tv < P.cut) != (t < P.cut):
            continue
        x, y, _ = keeper(kd, t)
        top = y - KH[kd] * K
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - 1.1) / 0.3))
        bx, by = x - sh + 70 * K + 26, top - 62
        il.creature(pg, lambda cv, bx=bx, by=by, s=s, pic=pic: bubble(cv, bx, by, BUBBLE_R * s, pic, (214, 196, 176),
                                                                     1.0, (bx - 62, by + 92)), bx, by)


# ----------------------------------------------------------------------------------------------- the frame

def hans_extra(t, sh):
    """Hans' working tentacles (his twine ball, the lashing, the peg), drawn on his own layer; records m.work."""
    P = plan()

    def draw(cv, m):
        m.work = []
        for slot, (tx, ty), grip in hans_targets(P, t, m.x + sh, m.y):
            if grip <= 0.001 and slot != -1:
                continue
            root_rest = (m.x + slot * 40 * K, m.y - 305 * K + 150 * K)
            gx, gy = (tx - sh, ty) if slot == -1 else lerp2(root_rest, (tx - sh, ty), grip)
            root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=max(grip, 0.3))
            m.work.append((slot, root, (gx, gy), L))
        bx, by = hans_ball(P, t, m.x + sh, m.y)
        cv.circle(bx - sh, by, 15 * K / 0.72, np.array(RW.TWINE, np.float64))
        for q in range(3):
            cv.arc(bx - sh, by, (6 + 4 * q), 200 + 40 * q, 320 + 40 * q, np.array(tone(RW.TWINE, -0.2), np.float64), 2.0)
    return draw


def twine_strand(pg, t, sh):
    """While Hans lashes, the twine runs from the ball to the winding tip."""
    P = plan()
    x, y, _ = keeper("tentacles", t)
    for slot, tip, g in hans_targets(P, t, x, y):
        if slot == -2 and g > 0.5:
            for r in P.rafts:
                if r["lashA"][0] <= t < r["lashB"][1]:
                    bx, by = hans_ball(P, t, x, y)
                    pg.stroke(skia.Path().moveTo(bx - sh, by).quadTo((bx + tip[0]) / 2 - sh, max(by, tip[1]) + 14,
                                                                     tip[0] - sh, tip[1]), RW.TWINE, 1.6, 0.9)


def figure(pg, kd, x, y, t, sh, a, extra=None):
    """One Keeper; Wheels leans with the slope under his wheels (his wheels on it, like a cart)."""
    tilt = math.degrees(math.atan(RW.ground_slope(x))) if kd == "wheels" else 0.0
    if tilt:
        pg.c.save()
        pg.c.rotate(tilt, x - sh, y)
    m = il.figure(pg, kd, x - sh, y, K, 6, t=t, extra=extra, **a)
    if tilt:
        pg.c.restore()
    return m


def glo_lights(pg, t, sh):
    """Glo's flare: light gathers in his lantern and floats down onto the leaf, which takes its Keeper's colour (owner:
    Glo changes things with a light flare)."""
    P = plan()
    gx = P.paths["lantern"](t)
    gy = glo_y(P, t, gx)
    lx, ly = gx - sh, gy - 260 * K + glo_bob(t) + 82 * K
    for r in P.rafts:
        a, b = r["flare"]
        if a - 0.3 <= t < b + 0.4:
            rs = P.raft_state(r["k"], t)
            mx, my = RW.mast_foot(rs["x"], rs["y"], 1.0)
            tx, ty = mx + 26 - sh, my - 60
            u = ease(t, a, a + 0.6)
            fade = 1 - ease(t, b, b + 0.4)
            x = lx + (tx - lx) * u
            y = ly + (ty - ly) * u - 30 * math.sin(math.pi * u)
            pg.glow(x, y, 70, "#ffe7a8", 0.75 * fade)
            pg.flat(oval(x, y, 7, 7), "#fff4d0", fade)
            if u >= 1:
                for q in range(6):                                 # sparkles round the leaf
                    ph = (t * 2 + q / 6) % 1.0
                    ang = q * 1.05 + t
                    pg.flat(oval(tx + math.cos(ang) * (20 + 24 * ph), ty + math.sin(ang) * (26 + 20 * ph), 3, 3),
                            "#fff4d0", 0.9 * (1 - ph) * fade)
    if glo_flare(P, t) > 0.01:
        pg.glow(lx, ly, 110, "#ffe7a8", 0.45 * glo_flare(P, t))


def fade_black(pg, t):
    P = plan()
    u = 1 - abs(t - P.cut) / 0.9
    if u > 0:
        pg.flat(skia.Path().addRect(skia.Rect(0, 0, W, H)), (34, 26, 30), smoothstep(u))


def frame(pg, valley, t):
    P = plan()
    sh = P.shift(t)
    RW.sky(pg, t)
    valley.draw(pg, sh, only={"clouds", "far", "far2", "far_trees", "mid", "far_bank"})
    RW.draw_water(pg, t, sh)
    # things on the water, far to near, the booms and the finish a slice at a time between them
    items = []
    for x, j in RW.STONES:
        items.append((j, lambda x=x, j=j: RW.draw_stone(pg, x, j, t, sh)))
    for i, (x, j) in enumerate(RW.LILY):
        items.append((j, lambda x=x, j=j, i=i: RW.draw_lily(pg, x, j, t, sh, i)))
    for k in range(6):
        rs = P.raft_state(k, t)
        if rs["where"] == "water" and not on_bank(rs):
            items.append((rs["d"], lambda k=k, rs=rs: draw_one_raft(pg, k, t, sh, rs)))
    if t < P.lady_fly[1] + 2.0 or P.leaf_x(t) < sh + W + 200:
        lx, ly, lp, ld = leaf_state(P, t)
        if sh - 200 < lx < sh + W + 200:
            items.append((ld, lambda: draw_leaf(pg, t, sh)))
    for name, x, d, face, s, chick in duck_states(P, t):
        items.append((d, lambda x=x, d=d, face=face, s=s, chick=chick:
                      RW.duck(pg, RW.at_depth(x, d) - sh, RW.lane_y(d, x), s * RW.lane_sc(d), t, face, chick)))
    if P.ducks[0] - 1.0 < t:
        items.append((5.3, lambda: draw_duck_reeds(pg, t, sh)))
    items.sort(key=lambda e: -e[0])
    bo = boom_open(P, t)
    edges = [99.0] + [j + 0.5 for j in range(5, -1, -1)] + [-99.0]
    for d1, d0 in zip(edges, edges[1:]):
        RW.draw_boom(pg, RW.START_BOOM, sh, bo, d0, d1)
        RW.draw_boom(pg, RW.END_BOOM, sh, 0.0, d0, d1)
        RW.finish_line(pg, t, sh, d0, d1)
        for d, fn in items:
            if d0 <= d < d1:
                fn()
    if sh - 100 < PIN[0] < sh + W + 300:                          # the post, its pin and the boom's rope
        draw_rope(pg, t, sh)
        RW.draw_post(pg, PIN[0], RW.near_edge(PIN_POST) + 6, sh, 44.0, 6.0)
        pp, st = pin_pos(P, t)
        if st == "post":
            draw_pin(pg, pp, sh)
    lb = ladybird_state(P, t)
    if lb[3] == "reed":
        RW.ladybird(pg, lb[0] - sh, lb[1], LADY_S, t, 0.0, -1)
    valley.draw(pg, sh, only={"meadow"})
    # the bank: the maple's live branch, the slide, what lies on the meadow
    if sh - 400 < RW.TREE < sh + W + 400:
        draw_branch(pg, t, sh)
        for i in range(6):
            draw_twig(pg, i, t, sh, only=("branch", "falling", "ground", "rising"))
    if sh - 300 < RW.ST[0] and RAIL0 < sh + W + 300:
        draw_slide(pg, t, sh)
        draw_heaps(pg, t, sh)
        draw_offcuts(pg, t, sh)
        draw_pile(pg, t, sh)
        for k in range(6):
            rs = P.raft_state(k, t)
            if on_bank(rs):
                draw_one_raft(pg, k, t, sh, rs)
    lb = ladybird_state(P, t)
    if lb[3] == "flying":
        RW.ladybird(pg, lb[0] - sh, lb[1], LADY_S, t, lb[2], 1)
    # Glo, behind the path: his bunch of leafy twigs behind his tendrils
    gx, gy, ga = keeper("lantern", t)
    if -400 < gx - sh < W + 400:
        for i, x, y in glo_bunch(P, t):
            RW.draw_leafy_twig(pg, x - sh, y, 1.0, RW.COLS[OWNERS[i]], 0.0, t)
        il.figure(pg, "lantern", gx - sh, gy, K, 6, t=t, shadow=False, **ga)
    draw_soil(pg, t, sh)
    pp, st = pin_pos(P, t)
    if st != "post":                                               # the pin: held from in front, so drawn behind him
        draw_pin(pg, pp, sh)
    # the Keepers on the path
    for kd in WALKERS:
        x, y, a = keeper(kd, t)
        if -500 < x - sh < W + 500:
            figure(pg, kd, x, y, t, sh, a, extra=hans_extra(t, sh) if kd == "tentacles" else None)
    twine_strand(pg, t, sh)
    valley.draw(pg, sh, only={"fg"})
    RW.apply_light(pg, t)
    glo_lights(pg, t, sh)
    bubbles(pg, t)
    overlays(pg, t)
    fade_black(pg, t)


def boom_open(P, t):
    return ease(t, *P.boom_open)


def draw_rope(pg, t, sh):
    """The rope from the start boom's free end to the pin on our bank (it holds the boom shut against the current);
    once the pin is out it slips off and trails behind the boom's end on the water."""
    P = plan()
    ex, ey = RW.boom_screen(RW.START_BOOM, boom_open(P, t), 1.0)
    if t < P.pin[0] + 0.55:
        px, py = PIN[0], PIN[1] + 6
        pg.stroke(skia.Path().moveTo(px - sh, py).quadTo((px + ex) / 2 - sh, max(py, ey) + 10, ex - sh, ey - 3),
                  tone(RW.TWINE, -0.2), 2.6)
        return
    u = ease(t, P.pin[0] + 0.55, P.pin[0] + 1.6)                  # slips off the pin and falls slack on the water
    px0, py0 = PIN[0], PIN[1] + 6
    tx, ty = ex - 70.0, RW.lane_y(RW.D_NEAR + 0.4, RW.START_BOOM) + 1
    px, py = px0 + (tx - px0) * u, py0 + (ty - py0) * u
    pg.stroke(skia.Path().moveTo(px - sh, py).quadTo((px + ex) / 2 - sh, max(py, ey) + 6, ex - sh, ey - 3),
              tone(RW.TWINE, -0.2), 2.6)


def draw_pin(pg, p, sh):
    x, y = p
    pg.shape(rrect(x - 3 - sh, y, x + 3 - sh, y + 22, 2), (186, 150, 110), 0.0)
    pg.flat(oval(x - sh, y, 6, 4), (200, 164, 120))


def draw_leaf(pg, t, sh):
    P = plan()
    x, y, pitch, d = leaf_state(P, t)
    sx = RW.at_depth(x, d) - sh
    c = pg.c
    c.save()
    c.clipRect(skia.Rect(-W, -H, 2 * W, y + 1.5))
    c.rotate(pitch, sx, y)
    leaf = smooth([(sx - 52, y - 2), (sx - 16, y - 14), (sx + 32, y - 12), (sx + 60, y - 2), (sx + 28, y + 8),
                   (sx - 28, y + 8)])
    pg.shape(leaf, RW.PAL["orange"], 0.12)
    pg.stroke(skia.Path().moveTo(sx - 46, y - 3).lineTo(sx + 54, y - 5), tone(RW.PAL["orange"], -0.2), 2.5)
    pg.stroke(skia.Path().moveTo(sx + 54, y - 5).quadTo(sx + 66, y - 8, sx + 72, y - 16), tone(RW.PAL["orange"], -0.3),
              3.0)                                                 # its stalk
    if t < P.lady_fly[0]:
        RW.ladybird(pg, sx + 4, y - 11, LADY_S, t, 0.0, 1)
    c.restore()


def draw_duck_reeds(pg, t, sh):
    """The reed bed the ducks paddle out of, standing in the water at the far bank (in front of where they wait)."""
    for x in RW.DUCK_REEDS:
        for q in range(7):
            xx = x + (q - 3) * 9.0
            d = 5.3 + 0.1 * (q % 2)
            y = RW.lane_y(d, xx) + 2
            sx = RW.at_depth(xx, d) - sh
            hh = 60 + 14 * ((q * 7) % 3)
            lean = 6 * math.sin(t * 0.8 + q)
            pg.stroke(skia.Path().moveTo(sx, y).quadTo(sx + lean * 0.4, y - hh * 0.6, sx + lean, y - hh),
                      tone(RW.GRASS_D, -0.1), 3.4)
            if q % 2 == 0:
                pg.shape(rrect(sx + lean - 3.5, y - hh - 17, sx + lean + 3.5, y - hh + 2, 3), (138, 96, 66), 0.0)


# ----------------------------------------------------------------------------------------------- the soundtrack

def soundtrack(path):
    """The music box (the episode's own variant), the Keepers' voices, soft warm sounds for what happens on screen,
    the brook, and the narrator over it all (the music eases down only while she speaks). -> (wav, stats, track)"""
    from engine.audio import EventTrack
    from . import music
    from .chatter import MOODS, VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    P = plan()
    track = EventTrack(8)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="raftrace")
    pan = lambda x: max(-0.6, min(0.6, (x / W) * 1.2 - 0.6))       # noqa: E731
    for tv, kd, mood, _ in P.voices:
        contour, st, _ = MOODS[mood]
        x = keeper(kd, tv)[0] - P.shift(tv)
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3, pan(x))
    # the brook all the way, a little louder by the falls
    for t0 in np.arange(0.0, P.end, 8.0):
        track.fx(t0, "rush", 8.6, 0.03, 0.0)
    track.fx(P.t_lip - 0.2, "gurgle", 1.6, 0.07, -0.3)
    for i, tw in enumerate(P.twigs):
        track.fx(tw["off"], "leaf_settle", 1.2, 0.04, -0.4)
    for a, b in P.bounces:
        track.fx(a, "rustle", 0.8, 0.07, -0.4)
    for sx in (-1, 1):
        for tt in P.dig.scrapes(sx, *P.dig_t):
            track.fx(tt, "sand_scrape", 0.4, 0.06, 0.3)
    for r in P.rafts:
        sx_ = pan(RW.ST[0] - P.shift(r["lay"][1]))
        track.fx(r["lay"][1] - 0.15, "sand_thump", 0.3, 0.07, sx_)
        for a, b in r["strokes"]:
            track.fx(a + 0.1, "sand_slice", 0.4, 0.05, sx_)
            track.fx(b - 0.02, "sand_thump", 0.15, 0.03, sx_)       # the offcut drops
        for a, b in (r["lashA"], r["lashB"]):
            track.fx(a, "rustle", b - a, 0.04, 0.0)
        for key in ("peg1", "peg2", "peg3"):
            track.hit(r[key][0] + 0.55, "pluck", 62, 0.07, 0.0)
        for key in ("slide1", "slide2", "slide3"):
            track.fx(r[key][0], "slide", r[key][1] - r[key][0], 0.04, 0.2)
        track.hit(r["flare"][0] + 0.5, "plink", 64, 0.07, 0.0)
        track.fx(r["slip"][1] - 0.5, "splash", 0.7, 0.06, 0.4)
        track.fx(r["slip"][1] - 0.2, "bubble", 0.8, 0.04, 0.4)
    for n, (a, b) in enumerate(P.count):                          # 3, 2, 1
        track.hit(a, "music_box", 72, 0.18, 0.0)
    track.hit(P.race_t0, "music_box", 79, 0.22, 0.0)
    track.fx(P.boom_open[0], "creak", 1.4, 0.05, -0.2)
    R = P.race
    for j, run in enumerate(R.runs):                              # each raft down each little falls: a soft splash
        for f in (RW.F1, RW.F2):
            for fr in range(len(run.rec) - 1):
                if run.rec[fr, 0] < f + RW.CW <= run.rec[fr + 1, 0]:
                    track.fx(P.race_t0 + fr / RW.REC_HZ, "splash", 0.6, 0.05, 0.0)
                    break
        if run.boom_t is not None:
            track.hit(P.race_t0 + run.boom_t, "pluck", 52, 0.06, 0.2)
    track.fx(P.fin_t - 0.05, "clap", 1.8, 0.05, 0.2)
    bed = {"type": "procedural", "name": "keepers_song", "gain": 0.9, "chords": chords,
           "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}

    class Shim:
        p = {"audio": {}}
        events_gain = 1.0
        reverb = None
    sc_ = Shim()
    sc_.bed = bed
    sc_.narration = [(t0, take(tx)) for t0, tx in P.narration()]
    wav, stats = narr_mix(sc_, track, P.end)
    import shutil
    shutil.move(wav, path)
    return path, stats, track
