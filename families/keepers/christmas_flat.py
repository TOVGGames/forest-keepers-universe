"""Forest Keepers episode 14, Sprout's Christmas Tree, in the flat picture-book look (storyboard approved by the owner
2026-11-06, "Yes", gust moment included). Staging: docs/engines/forest_keepers_christmas.md, "Build staging".

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep14.py). The world is christmas_flat_world.py; the walking and digging kit is flat_motion.py. From this episode on
(owner, approving FK0016): arms hang and swing on a walk (Monster.arm_swing), Twigs' knees bend forward
(Monster.knee_fwd), Hans walks on a staggered ripple (flat_motion.WaveGait).

    plan().end                              the timeline
    frame(pg, valley, t) -> metrics         draw one frame onto a flat.FlatPage
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import TURN_NARROW, Monster

from . import christmas_bench as CB
from . import christmas_deco as CD
from . import christmas_flat_world as XW
from . import christmas_home as CH
from . import christmas_night as CN
from .christmas_night import STAR_REST as NSTAR_REST
from . import illustrate as il
from . import storycheck as sc
from .flat_motion import (Hopper, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing, stance_drop,
                          walk_path)
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
FPS = 60
STEP = 1.0 / FPS
K = 0.72
# front (right) to back (left) on the way out; the same order at the bench, right to left (docs: build staging)
ORDER = ["springs", "digger", "sprout", "teeth", "wheels", "tentacles", "lantern"]
NAMES = {"sprout": "Sprout", "teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs",
         "tentacles": "Hans", "lantern": "Glo"}
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300, "sprout": 330}
V_WALK = 100.0
EASE = 1.0
NIGHT_CAM = XW.SPOT - 240.0  # the night camera: all six, the fir and the visitors in frame (r1: Hans out, Wheels cut)
SPRINGS_STAR_DX = 110.0   # Springs puts the star on from beside the fir: in front of it he hid it (r1)
WALK_SHOW = 3.0       # a long walk shows this much as they set off and as they arrive, round an act break
WALK_GAP = 4.0        # cut out only if at least this much walking is left between (a shorter cut is just choppy)
DIP = 0.7             # s each side of an act break: the page dims to dark and comes up again


class _Recorder:
    """Collects the times of the on-screen actions' sounds (for where a walk may be cut)."""
    def __init__(self):
        self.times = []

    def fx(self, t, name, dur=0.5, *a, **k):
        self.times.append((t, dur))

    def hit(self, t, *a, **k):
        self.times.append((t, 0.4))
FIR0, SPOT = XW.FIR0, XW.SPOT

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("It's nearly Christmas in the forest. And look... a little fir is growing right in the middle of the path. "
        "At the very end, it gets a forever home of its own.")
LINES = {
    "lift": "Digs lifts it out gently, roots and soil and all, so nobody steps on it.",
    "pot": "Sprout has a pot ready.",   # the cached take, cut after "ready" (r1: no home in sight; no new take)
    "bench": "Every Keeper is making something for the little tree.",
    "hang": "One by one, they hang what they made.",
    "eve": "Christmas Eve. Oh... a gust of wind. The star has tumbled into the snow, and the lanterns have gone out.",
    "lamp": "Digs has the very lamp for looking in the snow.",
    "up": "Up goes the star again. And the lanterns glow.",
    "visit": "Someone has come to see. A deer, a fox, a rabbit, and a little chickadee.",
    "after": "After the holidays, on a bright winter morning, the little fir gets its forever home, in a sunny "
             "clearing.",
}
FINALE = "Goodnight, little fir. Goodnight, forest."
SIGNOFF = "What should the Keepers do next? Tell us in the comments."
HOLD_END = 4.5                              # s of quiet after "Goodnight, forest" (owner 2026-11-05: 3-5 s)


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


# ----------------------------------------------------------------------------------------------- Digs' arms

DIGS_ARM = 95.0 * K                         # shoulder to paw (fixed)
DIGS_SH = 118.0 * K                         # shoulder out from his middle


def digs_shoulder(x, y, sx, t):
    by = y - 150 * K + 2 * K * math.sin(t * 2.6)
    return x + sx * DIGS_SH, by + 4 * K


def digs_paw(x, y, sx, ang, t):
    sx_, sy_ = digs_shoulder(x, y, sx, t)
    return sx_ + math.cos(ang) * DIGS_ARM, sy_ + math.sin(ang) * DIGS_ARM


def angle_to(x, y, sx, t, px, py):
    """Digs' arm angle pointing his paw at (px, py) (as near as its length lets it)."""
    sx_, sy_ = digs_shoulder(x, y, sx, t)
    return math.atan2(py - sy_, px - sx_)


# ----------------------------------------------------------------------------------------------- the fir + the pot

FIR_H = 190.0                               # the little fir: crown height (px), trunk to tip
BALL_R = 27.0                               # its ball of soil
POT_H, POT_W = 78.0, 70.0
POT_Y = BACK + 8.0                          # the pot's foot (at home by the lanterns)
HOLD = 1.3                                  # the paw holds the ball this many radii under the fir's base
FIR_C, FIR_D = (79, 122, 94), (63, 101, 80)
SOIL = (110, 84, 64)


def fir_tiers(x, base, h, lean=0.0):
    """The three tiers of the fir (paths), from the bottom; base = where the trunk meets the soil."""
    out = []
    for yb_, w, yt in ((0.92, 0.42, 0.18), (0.66, 0.33, 0.42), (0.4, 0.22, 0.68)):
        y0, y1 = base - h * (1 - yb_) - h * 0.1, base - h * yt - h * 0.28
        p = smooth([(x, y1 - h * 0.1), (x + h * w * 0.5, (y0 + y1) / 2), (x + h * w, y0), (x, y0 + h * 0.04),
                    (x - h * w, y0), (x - h * w * 0.5, (y0 + y1) / 2)])
        out.append((p, y0, w))
    return out


def draw_fir(pg, x, base, h=FIR_H, ball=True, snow=0.0, lean=0.0, deco=None):
    """The little fir at (x, base): its ball of soil under it (while it is out of the ground), a short trunk, three
    soft tiers; deco(pg, x, base, h) draws what hangs on it. lean (deg) sways it about its foot."""
    c = pg.c
    c.save()
    if lean:
        c.rotate(lean, x, base)
    if ball:
        pg.shape(oval(x, base + BALL_R * 0.55, BALL_R, BALL_R * 0.85), SOIL, 0.12)
        for dx in (-14, 3, 15):                                   # a few roots in it
            pg.stroke(skia.Path().moveTo(x + dx * 0.4, base + 4).quadTo(x + dx, base + 14, x + dx * 1.2, base + 26),
                      tone(SOIL, -0.25), 2.2)
    pg.shape(rrect(x - h * 0.035, base - h * 0.16, x + h * 0.035, base + 3, 4), (122, 86, 64), 0.0)
    for i, (p, y0, w) in enumerate(fir_tiers(x, base, h)):
        pg.shape(p, FIR_C if i % 2 == 0 else tone(FIR_C, 0.04), 0.14)
        if snow > 0.01:
            pg.flat(smooth([(x - h * w * 0.9, y0 - 2), (x - h * w * 0.4, y0 - h * 0.05 * snow), (x, y0 - h * 0.02),
                            (x + h * w * 0.5, y0 - h * 0.06 * snow), (x + h * w * 0.9, y0 - 2),
                            (x, y0 + h * 0.02)]), XW.SNOW, 0.95 * min(1.0, snow * 1.5))
    if deco is not None:
        deco(pg, x, base, h)
    c.restore()


def draw_pot(pg, x, y, front=True):
    """The clay pot (x, y = the middle of its foot). front=False: its back half only (inside, behind the fir)."""
    w = POT_W
    if not front:
        pg.flat(oval(x, y - POT_H + 4, w * 0.5, 9), tone((192, 122, 82), -0.35))
        return
    pg.shape(smooth([(x - w * 0.55, y - POT_H * 0.9), (x + w * 0.55, y - POT_H * 0.9), (x + w * 0.42, y),
                     (x - w * 0.42, y)]), (192, 122, 82), 0.12)
    pg.shape(rrect(x - w * 0.62, y - POT_H, x + w * 0.62, y - POT_H * 0.82, 6), (204, 136, 94), 0.0)


def pot_snow(pg, x, y):
    """A soft bank of snow round the pot's foot: it stands in the snow behind the path, not on the path."""
    pg.flat(oval(x, y + 7, POT_W * 0.9, 9), (0, 0, 0), 0.06, blur=4)
    pg.shape(smooth([(x - POT_W * 0.85, y + 4), (x - POT_W * 0.4, y - 9), (x, y - 6), (x + POT_W * 0.45, y - 10),
                     (x + POT_W * 0.85, y + 4), (x, y + 9)]), XW.SNOW, 0.05)


def pot_soil_y(y):
    return y - POT_H * 0.88                 # the soil's top in the pot: the fir's base when it is potted


# Digs lowers it in from his place by the pot: the paw's angle that puts the ball right in (the arm keeps its length),
# and where he stands so that paw is over the pot's middle
_SHY = G - 150 * K + 4 * K
LOWER_ANG = math.pi - math.asin((pot_soil_y(POT_Y) + BALL_R * HOLD - _SHY) / DIGS_ARM)
DIGS_AT_POT = SPOT - math.cos(LOWER_ANG) * DIGS_ARM + DIGS_SH
# at the fir he reaches out and down to its foot, well clear of his own body (so we see it)
DIG_DOWN_ANG = math.radians(128.0)
SHOW_ANG = math.radians(176.0)              # the fir held up beside the pot before he lowers it in (FK0017 r3)
DIGS_AT_FIR = FIR0 - math.cos(DIG_DOWN_ANG) * DIGS_ARM + DIGS_SH


# ----------------------------------------------------------------------------------------------- stops

STOPS = {
    "start": dict(springs=1100.0, digger=870.0, sprout=570.0, teeth=340.0, wheels=90.0, tentacles=-190.0,
                  lantern=-430.0),                         # (just out of the first shot, on its left)
    # Springs walks on past in front of the fir; Digs stops with it at his left paw (a straight-down reach)
    "fir": dict(springs=FIR0 + 430.0, digger=None, sprout=FIR0 - 270.0, teeth=FIR0 - 445.0,
                wheels=FIR0 - 700.0, tentacles=FIR0 - 975.0, lantern=FIR0 - 1215.0),
    "spot": dict(springs=SPOT + 470.0, digger=None, sprout=SPOT - 300.0, teeth=SPOT - 530.0,
                 wheels=SPOT - 785.0, tentacles=SPOT - 1060.0, lantern=SPOT - 1300.0),
}
STOPS["spot"]["digger"] = DIGS_AT_POT
STOPS["bench"] = dict(CB.X)
STOPS["fir"]["digger"] = DIGS_AT_FIR

REST_R = math.atan2(34, 46)                 # Sprout's right arm at rest (monster.sprout_arm)
HOLD_R = math.radians(-95.0)                # ... held up by its shoulder, out of the way of the hole (r1)
POUR_ANG = math.radians(-24.0)              # ... and lifted, the can held up to pour (at the clearing: onto the ground)
POT_POUR, POT_TIP = math.radians(-75.0), 0.3   # into the pot: held up high, its spout over the rim, tipped a little
                                            # (FK0017 r2: the spout was below the rim, the drops ran down the pot)

# ----------------------------------------------------------------------------------------------- beat 1: potting

class Potting:
    """Digs loosens the soil round the fir's foot with his left paw (soil flecks fly and land), lifts it out by its
    ball of soil, carries it home at his left paw and lowers it into the waiting pot; Sprout steps up and waters it."""

    DIG_DOWN, DIG_IN = DIG_DOWN_ANG, math.radians(162.0)      # his paw's stroke: out at its foot, out and up

    def __init__(self, t_arrive, t_lift_line):
        self.t0 = t_arrive                                        # all stopped at the fir
        self.intro = t_arrive + 0.6
        self.dig = (t_arrive + 1.0, t_arrive + 1.0 + 4 * 1.1)     # four strokes
        self.grip = (self.dig[1], self.dig[1] + 0.6)              # paw under its soil ball
        self.lift = (self.grip[1], self.grip[1] + 1.4)            # lifted out, up to carrying height
        self.say_lift = self.lift[1] + 0.2
        self.set_off = max(self.lift[1] + 0.6, self.say_lift + t_lift_line + 0.2)
        self.strokes = [(self.dig[0] + i * 1.1, self.dig[0] + (i + 1) * 1.1) for i in range(4)]
        rs = np.random.default_rng(41)
        self.flecks = []                                          # soil flecks flicked out of each stroke
        for a, b in self.strokes:
            for j in range(4):
                self.flecks.append(dict(t=a + 0.75 * (b - a) + 0.04 * j, vx=rs.uniform(-160, -60) if j % 2 else
                                        rs.uniform(40, 120), vy=rs.uniform(-300, -200), r=rs.uniform(3.5, 6)))

    def place(self, t_arrive_spot):
        self.at_spot = t_arrive_spot
        # (advisor FK0017 r3: in 0.5 s behind his arm, and "Sprout has a pot ready" after it was in) he holds it up
        # beside the pot while we hear the line, then lowers it in slowly, his paw going in over the rim
        self.say_pot = t_arrive_spot + 0.1
        self.lower = (t_arrive_spot + 1.7, t_arrive_spot + 3.7)
        self.let_go = (self.lower[1], self.lower[1] + 0.5)
        self.sprout_up = (self.let_go[1] + 0.2, self.let_go[1] + 2.0)  # Sprout steps up to the pot
        self.water = (self.sprout_up[1] + 0.2, self.sprout_up[1] + 3.6)
        self.end = self.water[1] + 1.2

    # --- Digs' left paw (angle), and where the fir is
    def paw_angle(self, t, dx, dy):
        """Digs' left arm angle at t (None = his own swing), given his x and feet y."""
        if t < self.dig[0] or t > self.let_go[1] + 0.6:
            return None
        rest = math.radians(112.0)
        if t < self.dig[1]:
            for a, b in self.strokes:
                if a <= t < b:
                    u = (t - a) / (b - a)
                    # down into the soil at its foot, scrape, then flick out and up to the left (the soil flies)
                    if u < 0.35:
                        return self.DIG_IN + (self.DIG_DOWN - self.DIG_IN) * smoothstep(u / 0.35)
                    if u < 0.6:
                        return self.DIG_DOWN
                    return self.DIG_DOWN + (self.DIG_IN - self.DIG_DOWN) * smoothstep((u - 0.6) / 0.4)
            return self.DIG_DOWN
        carry = self.carry_angle()
        if t < self.grip[1]:
            return self.DIG_DOWN
        if t < self.lift[1]:
            return self.DIG_DOWN + (carry - self.DIG_DOWN) * smoothstep((t - self.lift[0]) / (self.lift[1] - self.lift[0]))
        if t < self.at_spot - 1.0:
            return carry
        hold = SHOW_ANG                                           # held up beside the pot, clear of it, while we
        if t < self.lower[0]:                                     # hear "Sprout has a pot ready" (advisor r3)
            return carry + (hold - carry) * smoothstep(CB._seg(t, self.at_spot - 1.0, self.at_spot - 0.1))
        low = self.lower_angle()
        if t < self.lower[1]:
            return hold + (low - hold) * smoothstep((t - self.lower[0]) / (self.lower[1] - self.lower[0]))
        if t < self.let_go[1]:
            return low
        return low + (rest - low) * smoothstep((t - self.let_go[1]) / 0.6)

    @staticmethod
    def carry_angle():
        return math.radians(152.0)                                # out to his left and a little up

    @staticmethod
    def lower_angle():
        return LOWER_ANG

    def fir_pos(self, t, digs_x, digs_y):
        """(x, base y, in_pot) of the fir at t: growing (in the ground), on Digs' paw, or in its pot."""
        if t < self.grip[1]:
            return FIR0, BACK + 2, False
        if t >= self.let_go[0]:
            return SPOT, pot_soil_y(POT_Y), True
        ang = self.paw_angle(t, digs_x, digs_y)
        px, py = digs_paw(digs_x, digs_y, -1, ang, t)
        x, y = px, py - BALL_R * HOLD                             # the paw is under its ball
        if t < self.lift[1]:                                      # it comes up out of the ground as he lifts
            px0, py0 = digs_paw(digs_x, digs_y, -1, self.DIG_DOWN, self.grip[1])
            ox, oy = FIR0 - px0, (BACK + 2) - (py0 - BALL_R * HOLD)
            u = smoothstep((t - self.lift[0]) / (self.lift[1] - self.lift[0])) if t >= self.lift[0] else 0.0
            x, y = x + ox * (1 - u), y + oy * (1 - u)
        return x, y, False

    def fleck_pos(self, f, t):
        u = t - f["t"]
        if u < 0:
            return None
        x0, y0 = FIR0 - 10, BACK - 4
        y = y0 + f["vy"] * u + 0.5 * 1500 * u * u
        if y > BACK + 6:                                          # landed on the snow by the hole
            tl = (-f["vy"] + math.sqrt(f["vy"] ** 2 + 2 * 1500 * 10)) / 1500
            return x0 + f["vx"] * tl, BACK + 6
        return x0 + f["vx"] * u, y

    def draw_ground(self, pg, t, sh):
        """The loosened soil round its foot (a dark ring, then the hole once it is out), the flecks."""
        if t < self.dig[0]:
            return
        u = smoothstep((t - self.dig[0]) / (self.dig[1] - self.dig[0]))
        pg.flat(oval(FIR0 - sh, BACK + 4, 34 + 10 * u, 9 + 3 * u), SOIL, 0.6 + 0.4 * u)
        if t >= self.grip[1]:
            pg.flat(oval(FIR0 - sh, BACK + 3, 30, 8), tone(SOIL, -0.4))
        for f in self.flecks:
            p = self.fleck_pos(f, t)
            if p is not None:
                pg.flat(oval(p[0] - sh, p[1], f["r"], f["r"] * 0.8), SOIL)

    def things(self, t, sh, digs_x, digs_y):
        x, y, in_pot = self.fir_pos(t, digs_x, digs_y)
        held = None
        if self.grip[1] <= t < self.let_go[0]:
            ang = self.paw_angle(t, digs_x, digs_y)
            px, py = digs_paw(digs_x, digs_y, -1, ang, t)
            held = ("Digs' left paw, under its soil ball", (px - sh, py))
        out = {"the little fir": sc.Thing(x - sh, y - FIR_H / 2, FIR_H, held=held)}
        for i, f in enumerate(self.flecks):
            p = self.fleck_pos(f, t)
            if p is not None:
                out[f"soil fleck {i}"] = sc.Thing(p[0] - sh, p[1], f["r"], born="flicked out by Digs' paw" if
                                                  t - f["t"] < STEP * 1.5 else None, moves="falls")
        return out


# ----------------------------------------------------------------------------------------------- the plan

class Plan:
    """The timeline: the empty path and the hook, the walk in, potting, ... (later beats are added beat by beat)."""

    def __init__(self):
        STOPS["spot"]["sprout"] = self.sprout_water_x()          # Sprout waits by his pot (r1: whose pot? Digs did it all)
        self.hook = 1.5
        t_hook_end = self.hook + _dur(HOOK)
        self.walk_in = (t_hook_end - 4.0, None)                   # they come in as the hook ends: the fir alone on
                                                                  # the path first, then a short burst of the walk
                                                                  # in, an act break, they arrive (r2: 6 s walk)
        self.walk_in = (self.walk_in[0], self._walk("start", "fir", self.walk_in[0]))
        self.pot = Potting(self.walk_in[1], _dur(LINES["lift"]))
        t_spot = self._walk("fir", "spot", self.pot.set_off)
        self.pot.place(t_spot)
        t_bench = self._walk("spot", "bench", self.pot.end)
        self.bench = CB.Bench(t_bench)
        self.deco = CD.Deco(self.bench.end, dict(STOPS["bench"]), self.bench)
        self.bench.taken = self.deco.pick
        self.night = CN.Night(self.deco.night_t0)
        self.night.glo_rise = self.deco.end + 0.5                 # Glo floats up over the others, then across
        at_end = dict(CD.WAIT, lantern=CN.GLO_NIGHT[0], digger=CD.WAIT["digger"] + CN.DIGS_STEP, **CN.GATHER)
        self.home = CH.Home(self.night.end, at_end, self._sprout_rose_dx())
        self.deco.string_gone = lambda tt: self.home.removed("string", tt)
        self.deco.basket_override = self.home.basket_at
        self.deco.basket_heap = _basket_heap
        self.home.end = self.home.finale + _dur(FINALE) + HOLD_END
        self.sign = (self.home.end, self.home.end + 1.0)
        self.signoff = self.sign[1] + 0.3
        self.end = self.signoff + _dur(SIGNOFF) + 2.5
        self.legs = [("start", self.walk_in[0], "fir", self.walk_in[1]), ("fir", self.pot.set_off, "spot", t_spot),
                     ("spot", self.pot.end, "bench", t_bench)]
        self.paths = self._paths()
        self.cam = walk_path([(0.0, FIR0 - 120.0), (self.walk_in[1] - 2.0, FIR0 - 250.0),
                              (self.pot.set_off, FIR0 - 250.0), (t_spot, SPOT - 250.0), (self.pot.end, SPOT - 250.0),
                              (t_bench, 4350.0), (self.bench.pan[0], 4350.0), (self.bench.pan[1], 5260.0),
                              (self.deco.cuts[0][0] + 0.1, 5260.0), (self.deco.cuts[0][1] - 0.1, CD.DECO_CAM),
                              (self.deco.end, CD.DECO_CAM), (self.night.gather[0], CD.DECO_CAM),
                              (self.night.gather[1] + 1.0, NIGHT_CAM), (self.home.t0 + 4.0, NIGHT_CAM),
                              (self.home.gone, SPOT + 120.0), (self.home.cuts[0][0] + 0.1, SPOT + 120.0),
                              (self.home.cuts[0][1] - 0.1, CH.MORNING_CAM), (self.home.cuts[1][0] + 0.1, CH.MORNING_CAM),
                              (self.home.cuts[1][1] - 0.1, CH.CLEAR_CAM), (self.end, CH.CLEAR_CAM)], 3.0)
        XW.LIGHT = [(0.0, "day"), (self.deco.turns["teeth"]["arrive"], "day"), (self.deco.end, "dusk"),
                    (self.night.dark[1], "night"), (self.home.morning[0], "night"), (self.home.morning[1], "morning"),
                    (self.home.evening[0], "morning"), (self.home.evening[1], "evening")]
        self.turns = {kd: heading(self.paths[kd]) for kd in ORDER}
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {kd: biped(kd, self.paths[kd], G, K, spread=narrow(kd)) for kd in ("teeth", "digger", "sprout")}
        self.gaits["tentacles"] = WaveGait(G, K, self.paths["tentacles"], spread=narrow("tentacles", 0.5))
        self.hopper = Hopper(self.paths["springs"], G, K)
        self.voices = []
        self.voices = voices(self)
        self.skips = self._skips()
        self.vend = self.video_t(self.end)
        b = self.bench
        cy = G - 230.0                                         # bench close shots (straight cuts; FK0017 r1: the
        tw = (STOPS["bench"]["wheels"] + STOPS["bench"]["teeth"]) / 2 + 30   # ornament making was two tiny wide shots)
        self.shots = [(b.carves[0]["cut"][0] - 0.6, 90.0 if False else b.paints[0]["paint"][1], tw, cy, 1.9),
                      (b.paints[0]["paint"][1], b.paints[1]["dip"][0], STOPS["bench"]["tentacles"] + 30, cy, 1.8),
                      (b.paints[1]["dip"][0], b.pan[0], tw, cy, 1.9),
                      (b.pan[1], b.picks[0]["slide"][0] + 1.0, CB.STUMP[0] + 228.0, G - 215.0, 2.1),   # the stump,
                      (b.picks[0]["slide"][0] + 1.0, b.end - 1.0, STOPS["bench"]["springs"] - 340, cy, 1.75)]  # Sprout, Digs
                                                                # (nobody cut by the edge); then Sprout to the bush
        p = self.pot                                            # the dig and the potting, close (r1: tiny, hidden)
        self.shots += [(p.dig[0] - 0.6, p.lift[1] + 0.8, FIR0 + 70.0, G + 70.0 - 540.0 / 1.7, 1.7),
                       (p.at_spot - 0.8, p.end, SPOT + 20.0, G + 70.0 - 540.0 / 1.7, 1.7)]
        self.shots += self.deco.shots                           # each Keeper at the fir, close
        self.shots += self.home.shots                           # the fir undecorated, and planted, close
        nt = self.night                                         # the gust and the star going back on, close
        # (advisor FK0017 r3: the fall and the dig were both too small to follow) the fall closer, and the dig-out
        # close from Digs stepping over until the star is in Springs' hand
        self.shots += [(nt.gust[0] - 1.0, nt.landed + 1.5, SPOT - 110.0, G - 260.0, 1.8),
                       (nt.step[0] - 0.4, nt.give[1] + 0.6, NSTAR_REST[0] - 60.0, G + 70.0 - 540.0 / 1.8, 1.8),
                       (nt.springs_to[0], nt.relight[1][1] + 1.2, SPOT - 40.0, G - 330.0, 1.55)]   # (r2: it cut
                                                                # away while the first spark was still on its way)
        # no close shot may look past the page's foot (FK0017 r2: a bare band under the pot shots)
        self.shots = [(a, b, cx, min(cy, H - 540.0 / z), z) for a, b, cx, cy, z in self.shots]

    def shot(self, w):
        """(cx world, cy, zoom) of the close shot at world time w, or None (the walking camera)."""
        for a, b, cx, cy, z in self.shots:
            if a <= w < b:
                return cx, cy, z
        return None

    # ----- the time warp: long walks shown as short bursts round an act break (FK0017 advisor r1) -----

    def _moving(self, step=0.1):
        """World-time spans when some Keeper is walking (Glo floats, he doesn't count)."""
        ts = np.arange(0.0, self.end, step)
        mv = np.zeros(len(ts), bool)
        for kd in ORDER:
            if kd == "lantern":
                continue
            xs = np.array([self.paths[kd](t) for t in ts])
            mv[1:] |= np.abs(np.diff(xs)) / step > 25.0
        spans, a = [], None
        for t, m_ in zip(ts, mv):
            if m_ and a is None:
                a = t
            if not m_ and a is not None:
                spans.append([a, t])
                a = None
        if a is not None:
            spans.append([a, self.end])
        out = []
        for s_ in spans:                                   # short stops between steps don't end a walk
            if out and s_[0] - out[-1][1] < 0.8:
                out[-1][1] = s_[1]
            else:
                out.append(s_)
        return out

    def _skips(self):
        """[(world a, world b)]: the middle of every walk longer than WALK_SHOW * 2 + WALK_GAP, cut out at an act
        break, unless a narration line or an on-screen action (anything with its own sound) falls in it."""
        busy = [(t0, t0 + _dur(tx)) for t0, tx in self.narration()]
        rec = _Recorder()
        _action_sounds(self, rec, lambda x: 0.0)
        busy += [(t, t + d) for t, d in rec.times]
        d = self.deco                                      # every piece going on the fir is seen whole (a cut had
        acts = list(d.hang_t.values()) + list(d.swag_t) + [d.basket_down, d.star_take] + list(d.string_on)
        busy += [(a - 1.2, b + 0.6) for a, b in acts]      # taken star 1, acorn 1 and bow 1 half on)
        out = list(d.cuts) + list(self.home.cuts)          # the decorating and the morning have their own breaks
        for a, b in self._moving():
            if b - a < 2 * WALK_SHOW + WALK_GAP or (b > d.pick[0] and a < d.dusk_cut[1]) or                     any(b > ca and a < cb for ca, cb in self.home.cuts):
                continue
            sa, sb = a + WALK_SHOW, b - WALK_SHOW
            for ba, bb in sorted(busy):                    # keep the cut clear of every line and action
                if ba < sb and bb > sa:
                    if ba - sa >= WALK_GAP:
                        out.append((sa, ba - 0.5))
                    sa = max(sa, bb + 0.5)
            if sb - sa >= WALK_GAP:
                out.append((sa, sb))
        return sorted(out)

    def video_t(self, w):
        """World time -> video time (None inside a cut-out stretch)."""
        v = w
        for a, b in self.skips:
            if w >= b:
                v -= b - a
            elif w > a:
                return None
        return v

    def world_t(self, v):
        """Video time -> world time."""
        w = v
        for a, b in self.skips:
            if w >= a:
                w += b - a
        return w

    def dip(self, v):
        """0..1 how dark the page is at video time v (the act breaks)."""
        d = 0.0
        for a, b in self.skips:
            c = self.video_t(b)
            d = max(d, 1.0 - min(1.0, abs(v - c) / DIP))
        return d

    def stretches(self):
        """The world-time stretches the video shows, in order."""
        out, a = [], 0.0
        for sa, sb in self.skips:
            out.append((a, sa))
            a = sb
        out.append((a, self.end))
        return out

    def _walk(self, a, b, t0):
        d = max(abs(STOPS[b][kd] - STOPS[a][kd]) / (2.0 if kd == "lantern" else 1.0) for kd in ORDER)
        return t0 + d / V_WALK + EASE

    def _paths(self):
        out = {}
        for kd in ORDER:
            keys = []
            for a, ta, b, tb in self.legs:
                keys += [(ta, STOPS[a][kd]), (tb, STOPS[b][kd])]
            if kd == "sprout":                                    # steps up to the pot to water it
                keys += [(self.pot.sprout_up[0], STOPS["spot"]["sprout"]), (self.pot.sprout_up[1], self.sprout_water_x())]
            if kd in CD.ORDER:
                keys += self.deco.keys[kd]
            if kd == "springs":                                   # in front of the fir for the star, and back
                n = self.night
                keys += [(n.springs_in[0], CD.WAIT["springs"]), (n.springs_in[1], CN.SPRINGS_GIVE_X),
                         (n.springs_to[0], CN.SPRINGS_GIVE_X), (n.springs_to[1], SPOT + SPRINGS_STAR_DX),
                         (n.springs_back[0], SPOT + SPRINGS_STAR_DX), (n.springs_back[1], CD.WAIT["springs"])]
            if kd == "lantern":                                   # Glo floats over to the fir, to light the lanterns
                d = self.deco                                     # lights them from where he is, by the bench
                keys += [(d.end + 0.5, STOPS["bench"]["lantern"]),   # at dusk: up, then over between Sprout and Digs
                         (d.dusk_cut[1] - 0.2, CN.GLO_NIGHT[0])]
            if kd in CN.GATHER:                                   # at dusk the far ones come in closer (r1: the
                n = self.night                                    # visit had Hans out of frame, Wheels cut in half)
                keys += [(n.gather[0], CD.WAIT[kd]), (n.gather[1], CN.GATHER[kd])]
            if kd == "digger":                                    # steps over to where the beam found the star
                n = self.night
                keys += [(n.step[0], CD.WAIT[kd]), (n.step[1], CD.WAIT[kd] + CN.DIGS_STEP)]
            keys += self.home.keys.get(kd, [])
            out[kd] = walk_path(sorted(set(keys)), EASE)
        return out

    def _sprout_rose_dx(self):
        m = Monster("sprout", k=K)
        m.x, m.y, m.newlook, m.can, m.water, m.arm_ang_r = 0.0, G, True, True, 1.0, POUR_ANG
        return m.can_rose(0.0)[0]

    def sprout_water_x(self):
        """Where Sprout stands so its watering can's rose, lifted to pour, is right over the pot."""
        m = Monster("sprout", k=K)
        m.x, m.y, m.newlook, m.can, m.water, m.arm_ang_r = 0.0, G, True, True, 1.0, POT_POUR
        m.can_tip = POT_TIP
        rx, ry = m.can_rose(0.0)
        self.rose_y = ry
        return SPOT - 14.0 - rx                                  # the rose just left of the pot's middle

    def shift(self, t):
        return self.cam(t) - W / 2

    def narration(self):
        p = self.pot
        return [(self.hook, HOOK), (p.say_lift, LINES["lift"]), (p.say_pot, LINES["pot"]),
                (self.bench.say, LINES["bench"]), (self.deco.say2, LINES["hang"]),
                (self.night.say_eve, LINES["eve"]), (self.night.say_lamp, LINES["lamp"]),
                (self.night.say_up, LINES["up"]), (self.night.say_visit, LINES["visit"]),
                (self.home.say_after, LINES["after"]), (self.home.finale, FINALE), (self.signoff, SIGNOFF)]


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
        PLAN.home.hans_xy = lambda tt: keeper("tentacles", tt)[:2]
        PLAN.home.wheels_xy = lambda tt: keeper("wheels", tt)[:2]
        PLAN.night.give_pt = digs_paw_at(PLAN.night.give[0], 1)     # Springs reaches exactly to Digs' raised paw
    return PLAN


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6
BUBBLE_R = 50.0


def voices(P):
    p = P.pot
    ev = [(P.walk_in[1] + 0.2, "sprout", "q"), (p.lift[1] - 0.2, "digger", "huff"), (p.lift[1] + 0.6, "springs", "ooh"),
          (p.let_go[1] + 0.2, "digger", "mm"), (p.water[0] + 0.5, "sprout", "hehe"), (p.water[1] + 0.3, "wheels", "yay")]
    b, d, n, h = P.bench, P.deco, P.night, P.home
    ev += [(b.glo[1] + 0.3, "lantern", "ooh"), (b.carves[0]["slide"][0], "teeth", "mm"),
           (b.paints[0]["paint"][1] + 0.2, "wheels", "yay"), (b.braid[0] + 6.0, "tentacles", "hm"),
           (b.bows[0]["tie"][1], "sprout", "hehe"), (b.cones[0]["drop"][1], "digger", "mm"),
           (b.picks[2]["slide"][1], "springs", "wee"), (b.picks[6]["slide"][1], "springs", "hehe")]
    for kd, tn in d.turns.items():
        ev.append((tn["leave"] - 0.4, kd, "mm" if kd != "springs" else "yay"))
    ev += [(d.star_up[1] + 0.2, "springs", "yay"), (d.lamps[1][1] + 0.4, "lantern", "aww"),
           (n.landed + 0.4, "sprout", "uhoh"), (n.landed + 1.4, "springs", "aww"), (n.lift[1] - 0.2, "digger", "yay"),
           (n.bounce1[1] + 0.2, "springs", "hm"), (n.placed + 0.3, "springs", "wee"),
           (n.relight[1][1] + 0.4, "lantern", "mm"), (n.deer_in[1] + 1.0, "sprout", "ooh"),
           (n.dee_in[1] + 0.6, "digger", "aww"), (n.e0 + 22.0, "teeth", "mm"),
           (h.back + 0.5, "tentacles", "hey"), (h.undone - 0.5, "tentacles", "mm"), (h.at_hole + 0.3, "digger", "hm"),
           (h.let_go + 0.2, "tentacles", "mm"), (h.water[1] + 0.2, "sprout", "aww")]
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    ev = [e for e in sorted(ev) if not any(a - 0.7 <= e[0] <= b + 0.7 for a, b in lines)]
    out = []
    for e in ev:
        if not out or e[0] - out[-1][0] >= 1.2:
            out.append(e)
    return out


def talking(P, kd, t):
    m, look, hop = 0.0, 0.0, 0.0
    for tv, k, mood in P.voices:
        if k != kd or not (tv - 0.4 <= t <= tv + VOICE_DUR_S + 0.6):
            continue
        u = (t - tv) / VOICE_DUR_S
        if 0 <= u <= 1:
            m = max(m, 0.7 * math.sin(math.pi * u) * (0.75 + 0.25 * math.sin(u * 18)))
            hop = max(hop, 7 * K * math.sin(math.pi * u))
        look = max(look, smoothstep((t - tv + 0.4) / 0.4) * (1 - smoothstep((t - tv - VOICE_DUR_S - 0.2) / 0.4)))
    return m, look, hop


def soundtrack(path):
    """The music box (the episode's own variant), the Keepers' voices, soft warm sounds for what happens on screen,
    and the narrator over it all (the music eases down only while she speaks). -> (wav, stats, track)"""
    from engine.audio import EventTrack
    from . import music
    from .chatter import MOODS, VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    P = plan()
    track = EventTrack(14)
    chords = music.compose(track, 0.3, P.vend - 1.0, gain=0.9, variant="christmastree")
    pan = lambda x: max(-0.6, min(0.6, (x / W) * 1.2 - 0.6))       # noqa: E731
    for tv, kd, mood in P.voices:
        contour, st, _ = MOODS[mood]
        x = keeper(kd, tv)[0] - P.shift(tv)
        if P.video_t(tv) is None:
            continue
        track.hit(P.video_t(tv), f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3, pan(x))
    _action_sounds(P, _Warped(P, track), pan)
    bed = {"type": "procedural", "name": "keepers_song", "gain": 0.9, "chords": chords,
           "reverb": {"decay": 3.5, "wet": 0.4, "tone": 2600}}

    class Shim:
        p = {"audio": {}}
        events_gain = 1.0
        reverb = None
    sc_ = Shim()
    sc_.bed = bed
    sc_.narration = [(P.video_t(t0), take(tx)) for t0, tx in P.narration()]
    wav, stats = narr_mix(sc_, track, P.vend)
    import shutil
    shutil.move(wav, path)
    return path, stats, track


class _Warped:
    """An EventTrack seen through the warp: world times in, video times out; cut-out sounds dropped."""
    def __init__(self, P, track):
        self.P, self.track = P, track

    def fx(self, t, *a, **k):
        v = self.P.video_t(t)
        if v is not None:
            self.track.fx(v, *a, **k)

    def hit(self, t, *a, **k):
        v = self.P.video_t(t)
        if v is not None:
            self.track.hit(v, *a, **k)


def _action_sounds(P, track, pan):
    """The soft sounds of what happens on screen (world times)."""
    p, b, d, n, h = P.pot, P.bench, P.deco, P.night, P.home
    for a_, b_ in p.strokes:                                       # potting: the soil loosened, the fir lifted
        track.fx(a_ + 0.4, "sand_scrape", 0.6, 0.08)
    track.fx(p.lift[0], "rustle", 1.0, 0.08)
    track.fx(p.lower[1] - 0.2, "sand_thump", 0.4, 0.08)
    track.fx(p.water[0] + 0.2, "sand_patter", 2.6, 0.06)
    for c in b.carves:                                             # the bench: carving, painting, berries, cones
        for k in range(6):
            track.fx(c["cut"][0] + (k + 0.3) * (c["cut"][1] - c["cut"][0]) / 6, "sand_slice", 0.25, 0.05)
    for pt in b.paints:
        track.fx(pt["paint"][0], "paint_wipe", pt["paint"][1] - pt["paint"][0], 0.05)
    for c in b.cones:
        track.hit(c["drop"][0] + 0.25, "pluck", 55, 0.1, pan(CB.CONE_BASKET[0] - P.shift(c["drop"][0])))
    for pk in b.picks:
        track.hit(pk["slide"][1], "pluck", 67, 0.06, 0.4)
    for bw in b.bows:
        track.fx(bw["tie"][0], "rustle", 1.2, 0.05)
    track.fx(b.braid[0] + 1.0, "rustle", b.braid[1] - b.braid[0] - 2.0, 0.04)
    for name, (a_, b_) in d.hang_t.items():                       # each piece onto a branch: a soft wooden tick
        track.hit(b_ - 0.05, "pluck", 60 if "cone" in name else 64, 0.07, 0.0)
    for a_, b_ in d.swag_t:
        track.fx(a_, "rustle", b_ - a_, 0.05)
    for a_, b_ in list(d.lamps) + list(n.relight) + [n.helmet_flare]:   # Glo's flare: a low, warm note
        track.hit(b_ - 0.3, "plink", 60, 0.08, 0.0)
    track.fx(n.gust[0], "air_blow", n.gust[1] - n.gust[0], 0.12)  # the gust (soft, low)
    track.fx(n.landed, "sand_thump", 0.4, 0.08)
    for a_, b_ in n.out:
        track.fx(a_, "air_blow", 0.6, 0.05)
    for a_, b_ in n.digs:
        track.fx(a_ + 0.2, "sand_scrape", 0.5, 0.06)
    track.hit(n.placed, "pluck", 64, 0.1, 0.0)
    for a_, b_, hg in (n.bounce1, n.bounce2):
        track.fx(a_, "slide", 0.3, 0.04)
    for nm, (a_, b_, c_) in h.removes.items():
        track.hit(c_ - 0.1, "pluck", 58, 0.05, 0.1)
    for a_, b_ in h.strokes:
        track.fx(a_ + 0.3, "sand_scrape", 0.6, 0.08)
    track.fx(h.lower[1] - 0.2, "sand_thump", 0.4, 0.07)
    for a_, b_ in h.pats:
        track.fx(a_ + 0.3, "sand_thump", 0.25, 0.05)
    track.fx(h.water[0] + 0.2, "sand_patter", 2.6, 0.06)


# ----------------------------------------------------------------------------------------------- the Keepers

WR = 46.0 * K
LEG = {"digger": (62.0, 78.0), "sprout": (38.0, 70.0)}


def _sink(kd, t, x):
    hip, leg = LEG[kd]
    P = plan()
    n = 1.0 - TURN_NARROW * abs(P.turns[kd](t))
    return stance_drop(P.gaits[kd], lambda t_: (x - hip * K * n, x + hip * K * n), leg * K, t)


def keeper(kd, t):
    """(world x, y, monster attrs) of Keeper kd at time t, talking when it says something."""
    x, y, a = _keeper(kd, t)
    P = plan()
    a["legs_turn"] = P.turns[kd](t)
    a["turn"] = a["legs_turn"] * (1 - a.pop("face_us", 0.0))
    if P.voices:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd not in ("teeth", "digger", "sprout", "tentacles"):
                y -= hop
    return x, y, a


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "sprout", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":
            a.update(float=0.2, **hans_mood("calm"))
            if any(slot == HANS_LIFT_SLOT and grip > 0.001 for slot, _, grip in P.bench.hans_targets(t, x)):
                a["legs_up"] = (HANS_LIFT_LEG,)                       # 6 legs - 1 + 3 working = 8 (hans_tentacles)
            cl = _carry_leg(t, x)
            if cl is not None:                                        # carrying / hanging: that leg is lifted
                a["legs_up"] = tuple(sorted(set(a.get("legs_up", ())) | {cl}))
            hl = {leg for leg, _ in P.home.hans_targets(t, x, G)}     # the morning: one or both end legs working
            if hl:
                a["legs_up"] = tuple(sorted(set(a.get("legs_up", ())) | hl))
            return x, G + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(hands=True, saws=False, blades=0.0, knee_fwd=True, clamp_reach=True)
            hands, blade, grip = P.bench.twigs_hands(t, x)
            if hands:
                a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, blades=blade, blades_l=0.0,
                         grip=grip)
            ref = P.bench.twigs_ref(t)
            if ref:                                                   # the blade under his forearm while he carves
                a["_blade_frame"] = CB.blade_frame(ref)
            return x, G, _deco_attrs(kd, t, x, G, sh, a)
        y = G + _sink(kd, t, x)
        if kd == "digger":
            ang = P.pot.paw_angle(t, x, y)
            if ang is not None:
                a["paw_ang"] = {-1: ang}
            paws = P.bench.digs_paws(t, x, lambda s_: digs_shoulder(x, y, s_, t))
            if paws is not None:
                a["paw_ang"] = paws
            ang = P.night.digs_paw_angle(t, digs_shoulder(x, y, 1, t))
            if ang is not None:
                a["paw_ang"] = {1: ang}
            a["lamp"] = 1.6 * P.night.beam(t, x)[0]
            ang = P.home.digs_paw_angle(t, digs_shoulder(x, y, -1, t))
            if ang is not None:
                a["paw_ang"] = {-1: ang}
        if kd == "sprout":
            a["can"] = True
            u = P.pot.water if t < P.home.t0 else P.home.water
            lift = smoothstep((t - u[0] + 0.7) / 0.7) * (1 - smoothstep((t - u[1]) / 0.7))   # lifts the can to pour
            h = P.home
            base = REST_R
            if t >= h.t0 and h.at_hole - 0.8 <= t < h.water[0]:  # at the clearing: the can held up out of the way
                base = REST_R + (HOLD_R - REST_R) * smoothstep(CB._seg(t, h.at_hole - 0.8, h.at_hole - 0.2))
                a["arm_ang_r"] = base
            if t >= h.t0:
                a["water_floor"] = CH.BACK + 4.0                # the drops land on the fir's foot, not the path
            if t < h.t0:                                        # into the pot: the can up over the rim
                a["can_tip"] = POT_TIP
                a["water_floor"] = pot_soil_y(POT_Y) + 1.0
            if lift > 0:
                a["arm_ang_r"] = base + ((POUR_ANG if t >= h.t0 else POT_POUR) - base) * lift
            ang = P.bench.sprout_arm(t, x)                     # ties the bows with its left hand (the can in
            if ang is not None:                                # its right)
                a["arm_ang"] = ang
            a["water"] = smoothstep((t - u[0]) / 0.5) * (1 - smoothstep((t - u[1] + 0.5) / 0.5))
        return x, y, _deco_attrs(kd, t, x, y, sh, a)
    if kd == "springs":
        x, y, sq = P.hopper.state(t)
        lift, sq2 = P.deco.springs_bounce(t)
        l2, sq3 = P.night.springs_lift(t)
        lift, sq2 = lift + l2, sq2 + sq3
        y -= lift
        h = P.home                                          # home for the night: he hops off a little nearer us, in
        mc = h.cuts[0]                                      # front of the basket (advisor FK0017 r3: walked through it)
        y += 28.0 * smoothstep(CB._seg(t, h.t0 + 0.5, h.t0 + 1.4)) * (1 - smoothstep(CB._seg(t, mc[0] + 0.2,
                                                                                              mc[1] - 0.4)))
        a = dict(spring=sq + sq2, attend=0.25, arm_swing=0.0)
        hands = P.bench.springs_hand(t, x)
        if hands:
            a["arm_to"] = {s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}
        tg = P.night.springs_hand_target(t, x, y)
        if tg is not None:
            a["arm_to"] = {**a.get("arm_to", {}), -1: (tg[0] - sh, tg[1])}
        return x, y, _deco_attrs(kd, t, x, y, sh, a)
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR, attend=0.25, arm_swing=roll_swing(P.paths[kd], t, WR), clamp_reach=True)
        hands, grip = P.bench.wheels_hands(t, x)
        if hands:
            a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, grip=grip)
        tg = P.home.wheels_target(t, x, G)                    # the morning: the basket in his left pincer
        if tg is not None:
            a.update(arm_to={-1: (tg[0] - sh, tg[1])}, grip=1.0)
        return x, G, _deco_attrs(kd, t, x, G, sh, a)
    u = smoothstep(CB._seg(t, P.bench.glo[0] - 0.6, P.bench.glo[0])) * (1 - smoothstep(CB._seg(t, P.bench.glo[1],
                                                                                              P.bench.glo[1] + 0.8)))
    for a_, b_ in list(P.deco.lamps) + list(P.night.relight):
        u = max(u, smoothstep(CB._seg(t, a_ - 0.6, a_)) * (1 - smoothstep(CB._seg(t, b_, b_ + 0.8))))
    return P.paths[kd](t), G - 40 * K - P.night.glo_up(t), dict(attend=0.25, lamp=1.0 + 0.8 * u)


def deco_hand(kd, side, t):
    """The actual world xy of holder kd's hand on `side` at t while decorating (each arm keeps its length)."""
    P = plan()
    x, y, a = keeper(kd, t)
    tgt = P.deco.hand_target(kd, side, t, x, y)
    if tgt is None:
        tgt = P.deco.carry_pt(kd, side, x, y)
    if kd == "sprout":
        sx_, sy_ = x + side * 78 * K, y - 150 * K + 4 * K + 2 * K * math.sin(t * 2.0)
        L = CD.SPROUT_L
    elif kd == "digger":
        sx_, sy_ = digs_shoulder(x, y, side, t)
        L = DIGS_ARM
    elif kd == "springs":
        sq = a.get("spring", 0.0) + 0.06 * math.sin(t * 3.0)
        sx_, sy_ = x + side * 100 * K, y - (170 - 46 * sq) * K + 10 * K
        L = CD.SPRINGS_L
    else:
        return tgt
    d = math.hypot(tgt[0] - sx_, tgt[1] - sy_) or 1.0
    return sx_ + (tgt[0] - sx_) / d * L, sy_ + (tgt[1] - sy_) / d * L


def _deco_attrs(kd, t, x, y, sh, a):
    """Each holder's hands while decorating (from the bench to the fir)."""
    P = plan()
    D = P.deco
    if not (D.pick[0] - 0.6 <= t <= D.end):
        return a
    if kd in ("wheels", "teeth"):
        to = {}
        for side in (-1, 1):
            tg = D.hand_target(kd, side, t, x, y)
            if tg is not None:
                to[side] = (tg[0] - sh, tg[1])
        if to:
            a = dict(a, arm_to=to, grip=1.0)
        if kd == "wheels" and -1 not in to and "star 1" in D.hang_t:     # before / after the stars, its left pincer
            a0, b0 = D.hang_t["star 1"][0] - 0.9, D.hang_t["star 2"][1] + 0.9   # eases from / back to its own pose
            w_ = smoothstep(CB._seg(t, a0 - 0.6, a0)) if t < a0 else 1 - smoothstep(CB._seg(t, b0, b0 + 0.6))
            if w_ > 0.001:                                      # (r2: it snapped 99 px as it let go)
                rx, ry = x - 90, y - 160
                push = max(0.0, 46.0 - math.hypot(rx - (x - 72.0), ry - (y - 142.7)))   # (as the deco bows it out)
                to[-1] = (rx - 0.96 * push - sh, ry + 0.29 * push)
                a = dict(a, arm_to=to, arm_w={**(a.get("arm_w") or {}), -1: w_})
        if kd == "wheels" and -1 in to:                         # from the basket (down right of that shoulder) up to
            ux, uy = to[-1][0] - (x - sh - 72.0), to[-1][1] - (y - 144.0)   # the fir (up left) the elbow kept
            n_ = math.hypot(ux, uy) or 1.0                                    # jumping sides (r2 2:18): it stays on
            a["elbow_pref"] = {-1: (uy / n_, -ux / n_)}                       # one side of the arm the whole way
    elif kd == "sprout":                                    # the can in its right hand, the bows in its left
        for side, key in ((1, "arm_ang_r"), (-1, "arm_ang")):
            tg = D.hand_target("sprout", side, t, x, y)
            if tg is not None:
                sx_, sy_ = x + side * 78 * K, y - 150 * K + 4 * K
                a = dict(a, **{key: math.atan2(tg[1] - sy_, tg[0] - sx_)})
    elif kd == "digger":
        tg = D.hand_target("digger", 1, t, x, y)
        if tg is not None:
            sx_, sy_ = digs_shoulder(x, y, 1, t)
            a = dict(a, paw_ang={1: math.atan2(tg[1] - sy_, tg[0] - sx_)})
    elif kd == "springs":
        to = {}
        for side in (-1, 1):
            tg = D.hand_target("springs", side, t, x, y)
            if tg is not None:
                to[side] = (tg[0] - sh, tg[1])
        if to:
            a = dict(a, arm_to=to)
    return a


def hans_hand(t):
    """The tip of Hans' working tentacle (world) in the forever-home beat."""
    P = plan()
    x, y, _ = keeper("tentacles", t)
    tg = P.home.hans_target(t, x, y)
    return tg if tg is not None else (x + 170, y - 150)


def digs_paw_at(t, side):
    """Digs' paw (world xy) on side at time t, as drawn."""
    x, y, a = keeper("digger", t)
    ang = (a.get("paw_ang") or {}).get(side)
    if ang is None:
        ang = math.radians(72 if side > 0 else 108)
    return digs_paw(x, y, side, ang, t)


def wheels_front_arm(t):
    """At the fir Wheels takes each star out of the basket held in front of his belly with his left pincer, so that arm
    is drawn again over his body (monster.py draws arms behind it: FK0017 r2, the claw vanished behind him and the
    red star seemed to float up on its own). Switched on and off inside the act breaks either side, never seen."""
    P = plan()
    tw = P.deco.turns.get("wheels") if hasattr(P.deco, "turns") else None
    if tw is None or not (tw["arrive"] - 1.1 <= t < tw["leave"] + 0.8):
        return None

    def draw(cv, m):
        if -1 not in m.arm_len:
            return
        from families.foundry.products.monster import CLAW
        s_, el, hd = m.arm_len[-1]
        c = m.part(cv, "arms")
        if c is None:
            return
        k = m.k
        c.line(*s_, *el, CLAW * 0.8, 18 * k)
        c.line(*el, *hd, CLAW * 0.8, 16 * k)
        c.circle(*el, 12 * k, CLAW)
        snap = 0.35 + m.alive * 0.25 * (0.5 + 0.5 * math.sin(t * 2.4 - 1))
        if m.grip > 0.01:
            snap += (0.08 - snap) * m.grip
        for side in (-1, 1):
            base = math.atan2(hd[1] - el[1], hd[0] - el[0]) + side * snap
            tip = (hd[0] + math.cos(base) * 70 * k, hd[1] + math.sin(base) * 70 * k)
            mid = (hd[0] + math.cos(base - side * 0.45) * 42 * k, hd[1] + math.sin(base - side * 0.45) * 42 * k)
            jaw = [hd, mid, tip, (hd[0] + math.cos(base + side * 0.25) * 34 * k, hd[1] + math.sin(base + side * 0.25) * 34 * k)]
            c.polygon(jaw, CLAW)
            c.polyline(jaw, CLAW * 0.55, 2, closed=True)
        c.circle(*hd, 14 * k, CLAW * 0.9)
    return draw


HANS_LIFT_SLOT, HANS_LIFT_LEG = -2, 0   # the bench: the sprig-fetching tentacle is his leftmost leg (the pile is left)


def _hans_target(t, x, y):
    """The deco's one working tentacle (the home beat's legs are drawn on their own: P.home.hans_targets)."""
    P = plan()
    return P.deco.hand_target("tentacles", -1, t, x, y)


def _carry_leg(t, x):
    """Which of Hans' legs is lifted to carry / hang (its end side nearest the target), or None (FK0017 advisor r1:
    the carrying tentacle came out of his face; it is one of his eight limbs, a leg lifted off the snow)."""
    tg = _hans_target(t, x, G)
    if tg is None:
        return None
    return 0 if tg[0] < x else 5


def twigs_front_arm(t):
    """At the bench Twigs works in front of himself (the block and his blade are on the counter before his body), so
    his right arm is drawn again over his body there (monster.py draws both arms behind it: FK0017 r2, the blade was
    never seen touching the wood). From the bench beat's start to just after his last piece, while that arm hangs
    at his side, so the change is never seen."""
    B = plan().bench
    if not (B.t0 <= t < B.twigs_done + 1.0):
        return None

    def draw(cv, m):
        if 1 not in m.arm_len:
            return
        s_, el, hd = m.arm_len[1]
        c = m.part(cv, "arms")
        if c is None:
            return
        k, col = m.k, np.asarray(m.color)
        c.line(*s_, *el, col * 0.8, 13 * k)
        c.line(*el, *hd, col * 0.8, 11 * k)
        m._twigs_hand(c, hd, el, 1)
    return draw


def hans_extra(t, sh):
    """Hans' working tentacles (the garland), drawn on his own layer; records m.work."""
    P = plan()

    def draw(cv, m):
        m.work = []
        tg = _hans_target(t, m.x + sh, m.y)
        if tg is not None:
            leg = _carry_leg(t, m.x + sh)
            root, L = m.work_tentacle(cv, tg[0] - sh, tg[1], t, slot=-1, grip=1.0, root=m.leg_root(leg, t))
            m.work.append((-1, root, (tg[0] - sh, tg[1]), L))
        for leg, (tx, ty) in P.home.hans_targets(t, m.x + sh, G):    # the morning: his two end legs, lifted
            slot = -1 if leg == 0 else -3
            root, L = m.work_tentacle(cv, tx - sh, ty, t, slot=slot, grip=1.0, root=m.leg_root(leg, t))
            m.work.append((slot, root, (tx - sh, ty), L))
        for slot, (tx, ty), grip in P.bench.hans_targets(t, m.x + sh):
            if grip <= 0.001:
                continue
            rest = (m.x + slot * 40 * K, m.y - 305 * K + 150 * K)
            if slot == HANS_LIFT_SLOT:                               # his lifted leg: it reaches out from its foot
                fx, fy = P.gaits["tentacles"].feet(t)[HANS_LIFT_LEG]
                rest = (fx - sh, fy)
            gx, gy = rest[0] + (tx - sh - rest[0]) * grip, rest[1] + (ty - rest[1]) * grip
            root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=grip)
            m.work.append((slot, root, (gx, gy), L))
    return draw


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


def _card(pg, x, y, w, h, a):
    pg.flat(rrect(x + 4, y + 6, x + w + 4, y + h + 6, 18), (40, 28, 24), 0.18 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, 18), PAPER, 0.94 * a)


def overlays(pg, t):
    """Screen-space text: the name tags as they come in, the end sign."""
    P = plan()
    t_tags = P.walk_in[1]
    if P.walk_in[0] + 2 < t < t_tags + 4.0:
        a = smoothstep((t - P.walk_in[0] - 3.0) / 0.8) * (1 - smoothstep((t - t_tags - 2.8) / 1.0))
        sh = P.shift(t)
        shot = P.shot(t)
        for kd in ORDER:
            x, y, _ = keeper(kd, t)
            sx_, top = x - sh, y - KH[kd] * K
            if shot is not None:                                   # in a close shot: over the zoomed Keeper (r1)
                cx, cy, z = shot
                sx_, top = W / 2 + z * (sx_ - (cx - sh)), H / 2 + z * (top - cy)
            top -= 26
            if 60 < sx_ < W - 60 and top > 60:
                tw = _font(30).measureText(NAMES[kd])
                _card(pg, sx_ - tw / 2 - 16, top - 34, tw + 32, 46, a)
                _text(pg, NAMES[kd], sx_, top, 30, a=a, center=True)
    end_sign(pg, t)


def end_sign(pg, t):
    P = plan()
    sa = smoothstep(CB._seg(t, *P.sign))
    if sa <= 0:
        return
    bw, bh = 940, 220
    x0, y0 = (W - bw) / 2, 120
    pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * sa, blur=10)
    pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), sa)
    pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), sa)
    _text(pg, "WHAT SHOULD THEY DO NEXT?", W / 2, y0 + 108, 58, col=PAPER, a=sa, center=True)
    _text(pg, "Tell us in the comments", W / 2, y0 + 168, 34, col=(250, 232, 200), a=sa, weight="Medium",
          center=True)


def bubbles(pg, t):
    from .chatter import MOODS, _back, bubble
    P = plan()
    sh = P.shift(t)
    for tv, kd, mood in P.voices:
        u = t - tv
        pic = MOODS[mood][2]
        if pic is None or pic in ("!", "?") or not (0 <= u < 1.4) or t >= P.sign[0] - 4.0:
            continue
        x, y, _ = keeper(kd, t)
        top = y - KH[kd] * K
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - 1.1) / 0.3))
        bx, by = x - sh + 70 * K + 26, top - 62
        shot = P.shot(t)
        if shot is not None:                                  # a close shot: the bubble stays inside it
            cx, cy, z = shot
            by = max(by, cy - 540.0 / z + BUBBLE_R * 1.15 + 8.0)
            bx = min(max(bx, cx - sh - 960.0 / z + BUBBLE_R * 1.15 + 8.0), cx - sh + 960.0 / z - BUBBLE_R * 1.15 - 8.0)
        il.creature(pg, lambda cv, bx=bx, by=by, s=s, pic=pic: bubble(cv, bx, by, BUBBLE_R * s, pic, (214, 196, 176),
                                                                     1.0, (bx - 62, by + 92)), bx, by)


# ----------------------------------------------------------------------------------------------- the frame

def _brush(pg, t, sh, x, a):
    """Wheels' paint brush, in his right pincer (or lying by the pot before and after)."""
    B = plan().bench
    j = B.brush_held(t)                                             # else it stands in its pot (draw_front)
    hd = (a.get("arm_to") or {}).get(1)
    if j is None or hd is None:
        return
    hx, hy = hd                                                     # held by its top, tip down: the paint goes on
    tx, ty = hx + CB.BRUSH[0], hy + CB.BRUSH[1]                     # only under the tip (FK0017 r2)
    pg.stroke(skia.Path().moveTo(hx, hy).lineTo(tx + 1.5, ty - 4), (150, 110, 80), 4.0)
    pg.flat(oval(tx, ty, 4, 5.5, rot=math.degrees(math.atan2(-CB.BRUSH[0], CB.BRUSH[1]))), B.paints[j]["col"])


def lamp_lit(j, t):
    P = plan()
    a, b = P.deco.lamps[j]
    lit = smoothstep(CB._seg(t, a + FLARE_HIT * (b - a), a + (FLARE_HIT + 0.12) * (b - a)))   # as the flare lands
    return lit * P.night.lamp_factor(j, t)


def springs_hand_at(t, side=-1):
    """Springs' hand (world xy) as drawn (its arm keeps its length)."""
    P = plan()
    x, y, a = keeper("springs", t)
    sq = a.get("spring", 0.0) + 0.06 * math.sin(t * 3.0)
    sx_, sy_ = x + side * 100 * K, y - (170 - 46 * sq) * K + 10 * K
    tg = (a.get("arm_to") or {}).get(side)
    if tg is None:
        return sx_ + side * 20, sy_ + 26
    tx, ty = tg[0] + P.shift(t), tg[1]
    d = math.hypot(tx - sx_, ty - sy_) or 1.0
    return sx_ + (tx - sx_) / d * CD.SPRINGS_L, sy_ + (ty - sy_) / d * CD.SPRINGS_L


FLARE_GO, FLARE_HIT = 0.3, 0.8      # of each flare's span: it leaves Glo, it lands on the lantern


def glo_flares(pg, t, sh):
    """Glo's flare: light gathers under his dome and floats over to each lantern (owner: he changes things with a
    light flare). FK0017 r2: a 20 px spark read as nothing - now a big bright gathering under his dome, a glowing
    ball with a streak behind it, and a bloom at the lantern as it catches (held about a second)."""
    P = plan()
    gx, gy, _ = keeper("lantern", t)
    gy0 = gy - 178 * K
    for j, (a, b) in list(enumerate(P.deco.lamps)) + list(enumerate(P.night.relight)) + [(-1, P.night.helmet_flare)]:
        if not (a <= t < b + 1.4):
            continue
        if j < 0:                                              # Digs' hat lamp (r2: it came on by itself)
            dx_, dy_, _ = keeper("digger", t)
            tx, ty = dx_, dy_ - 182
        else:
            tx, ty = SPOT + XW.LAMP_DX[j], XW.LAMP_Y - 18
        go, hit = a + FLARE_GO * (b - a), a + FLARE_HIT * (b - a)

        def at(tt):
            u = smoothstep(CB._seg(tt, go, hit))
            return gx + (tx - gx) * u, gy0 + (ty - gy0) * u - 70 * math.sin(math.pi * u)
        if t < go + 0.25:                                      # it gathers under his dome, brighter and brighter
            g = smoothstep(CB._seg(t, a, go)) * (1 - smoothstep(CB._seg(t, go, go + 0.25)))
            pg.glow(gx - sh, gy0, 50 + 70 * g, "#ffe7a8", 0.9 * g)
            pg.flat(oval(gx - sh, gy0, 6 + 10 * g, 6 + 10 * g), "#fff8e0", g)
        if go <= t < hit + 0.15:                               # the ball of light, a streak trailing behind it
            fade = 1 - smoothstep(CB._seg(t, hit, hit + 0.15))
            for q in range(10, 0, -1):
                px, py = at(t - 0.035 * q)
                pg.flat(oval(px - sh, py, 10 - 0.7 * q, 10 - 0.7 * q), "#ffe9a8", 0.5 * fade * (1 - q / 11))
            x, y = at(t)
            pg.glow(x - sh, y, 80, "#ffe7a8", 0.85 * fade)
            pg.flat(oval(x - sh, y, 12, 12), "#fff8e0", fade)
        if hit <= t < hit + 1.4:                               # it catches: a bloom round the lantern, then settles
            v = CB._seg(t, hit, hit + 1.4)
            f = smoothstep(CB._seg(t, hit, hit + 0.15)) * (1 - smoothstep(CB._seg(t, hit + 0.5, hit + 1.4)))
            k = 0.3 if j < 0 else 1.0                          # Digs' lamp: a tight bloom round the lamp only (advisor
            pg.glow(tx - sh, ty, (90 + 90 * v) * k, "#ffe2a0", 0.9 * f)   # FK0017 r3: a big one turned him pale)
            r = (20 + 70 * v) * (0.45 if j < 0 else 1.0)
            pg.stroke(skia.Path().addOval(skia.Rect(tx - sh - r, ty - r, tx - sh + r, ty + r)), "#fff2c8", 3.0,
                      0.6 * f)


def _water_stream(pg, t, sh, m):
    """Sprout waters the planted fir: a clear stream from the can's rose onto its foot (r1: only a few tiny drops)."""
    P = plan()
    home = t >= P.home.t0
    a, b = P.home.water if home else P.pot.water
    if m is None or not (a <= t <= b):
        return
    u = smoothstep(CB._seg(t, a + 0.35, a + 0.75)) * (1 - smoothstep(CB._seg(t, b - 0.6, b - 0.2)))
    if u < 0.01:
        return
    rx, ry = m.can_rose(t)
    fx, fy = (CH.HOLE - sh, CH.BACK + 2.0) if home else (SPOT - sh, pot_soil_y(POT_Y) + 1.0)   # (r2: the pot too)
    for j in range(3):
        sx = rx + 3.0 + 3.0 * j
        p = skia.Path().moveTo(sx, ry + 4).quadTo(sx + 4 + 2 * j, (ry + fy) / 2, fx - 6 + 6 * j, fy)
        pg.stroke(p, (150, 200, 240), 2.6 - 0.4 * j, 0.75 * u)
    for j in range(4):                                           # a little splash where it lands
        ph = (t * 2.3 + j * 0.25) % 1.0
        pg.flat(oval(fx - 10 + 7 * j, fy - 4 - 8 * math.sin(math.pi * ph), 2.2, 2.8), (150, 200, 240), 0.8 * u * (1 - ph))


def _basket_heap(pg, t, bx, by, sh):
    """The ornaments back in the basket in the morning (drawn with it, wherever it is)."""
    P = plan()
    n = P.home.basket_full(t)
    for k in range(min(n, 6)):                                 # a little heap of them, peeking over the rim
        pg.flat(oval(bx - 20 + 8 * k - sh, by - 22 - (k % 2) * 3, 8, 6),
                ((226, 178, 72), (196, 82, 70), (70, 116, 78), (196, 70, 74), (140, 98, 64), (205, 160, 112))[k])


def frame(pg, valley, t, video=True):
    """One frame at video time t (world time if video is False)."""
    P = plan()
    dip = P.dip(t) if video else 0.0
    if video:
        t = P.world_t(t)
    shot = P.shot(t)
    if shot is not None:                                           # a close shot: the page seen nearer
        cx, cy, z = shot
        c = pg.c
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-(cx - P.shift(t)), -cy)
    out = _frame_world(pg, valley, t)
    if shot is not None:
        pg.c.restore()
    overlays(pg, t)                                                # screen text: never zoomed
    if dip > 0.001:                                                # an act break: the page dims to dark and back
        pg.flat(rrect(-10, -10, W + 10, H + 10, 0), (14, 12, 18), smoothstep(min(1.0, dip)))
    return out


def _frame_world(pg, valley, t):
    P = plan()
    sh = P.shift(t)
    XW.sky(pg, t)
    valley.draw(pg, sh)
    for j, dx in enumerate(XW.LAMP_DX):
        XW.lantern(pg, SPOT + dx - sh, XW.LAMP_Y, lamp_lit(j, t), flicker=math.sin(t * 6 + j), post=BACK - XW.LAMP_Y)
    P.pot.draw_ground(pg, t, sh)
    P.bench.draw_back(pg, t, sh, keeper)
    dx, dy, _ = keeper("digger", t)
    fx, fy, in_pot = P.pot.fir_pos(t, dx, dy)
    px, py = SPOT, POT_Y
    planted = False
    if t >= P.home.t0:
        px, py = P.home.pot_pos(t, hans_hand)
        fx, fy, in_pot, planted = P.home.fir_pos(t, hans_hand)
        P.home.draw_ground(pg, t, sh)
    P.night.draw_star(pg, t, sh, lambda tt: digs_paw_at(tt, 1), springs_hand_at, in_drift=True)
    P.night.draw_drift(pg, t, sh)
    behind = in_pot or P.pot.lower[0] - 0.2 <= t < P.pot.let_go[0]   # lowered in: its ball goes in behind the pot's
    if behind:                                                         # front wall, over the rim (r2: through it)
        draw_pot(pg, px - sh, py, front=False)
    else:
        draw_pot(pg, px - sh, py)
    lean = P.night.lean(t) if in_pot else 0.0
    pg.c.save()
    if lean:
        pg.c.rotate(lean, fx - sh, POT_Y - POT_H)
    growing = t < P.pot.grip[1]                                    # still in the ground: no soil ball shows (r1)
    if P.pot.grip[1] <= t < P.pot.lift[1]:                         # the ball comes up out of the hole, not in front
        pg.c.clipRect(skia.Rect(-1e5, -1e5, 1e5, BACK + 5))
    draw_fir(pg, fx - sh, fy, ball=not planted and not growing, snow=0.6 * smoothstep(CB._seg(t, P.night.snow[0], P.night.snow[0] + 20)))
    if in_pot:
        P.deco.draw_on_fir(pg, t, sh, top_star=P.night.star_on_top(t), removed=lambda n: P.home.removed(n, t))
    pg.c.restore()
    if behind:
        draw_pot(pg, px - sh, py)
    if t < P.home.t0 or (px, py) == (SPOT, POT_Y):                 # set in the snow beside the path, not on it (r1:
        pot_snow(pg, px - sh, py)                                  # they seemed to walk through it)
    P.deco.draw_carried(pg, t, sh, deco_hand, layer="back")        # what is on the fir or the ground: behind them
    P.night.draw_visitors(pg, t, sh)
    ms = {}
    for kd in reversed(ORDER):
        x, y, a = keeper(kd, t)
        if -500 < x - sh < W + 500:
            ms[kd] = il.figure(pg, kd, x - sh, y, K, 6, t=t, extra_behind=hans_extra(t, sh) if kd == "tentacles" else None,
                               extra=twigs_front_arm(t) if kd == "teeth" else (wheels_front_arm(t) if kd == "wheels"
                                                                                else None),
                               **a)
        if kd == "wheels":
            wheels_now = (x, a)
    _water_stream(pg, t, sh, ms.get("sprout"))
    P.bench.draw_front(pg, t, sh, keeper, lambda side, tt: digs_paw_at(tt, side))
    if "wheels_now" in locals():                                   # the brush over the star it paints (it was drawn
        _brush(pg, t, sh, *wheels_now)                             # under the bench's pieces: paint with no brush, r1)
    P.deco.draw_carried(pg, t, sh, deco_hand, layer="front")       # only what someone is holding: in front
    P.night.draw_star(pg, t, sh, lambda tt: digs_paw_at(tt, 1), springs_hand_at)
    P.home.draw_removed(pg, t, sh, P.deco, hans_hand)
    P.night.draw_wisps(pg, t, sh)
    P.night.draw_snow(pg, t)
    P.night.draw_streaks(pg, t)
    XW.apply_light(pg, t)
    P.night.draw_beam(pg, t, sh, keeper("digger", t)[:2])
    for j, dx in enumerate(XW.LAMP_DX):                            # the lanterns glow over the dusk
        if lamp_lit(j, t) > 0.01:
            XW.lantern(pg, SPOT + dx - sh, XW.LAMP_Y, lamp_lit(j, t), flicker=math.sin(t * 6 + j), glow_only=True)
    P.bench.draw_lights(pg, t, keeper("lantern", t)[:2], sh)
    glo_flares(pg, t, sh)
    bubbles(pg, t)
    return {kd: list(getattr(m, "leg_len", [])) for kd, m in ms.items()}
