"""Forest Keepers, The Treetop Marble Run, in the flat picture-book look (docs/engines/forest_keepers_marble_run_flat.md):
the same story as FK0003 with the original six Keepers, narrated, the music box all the way.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/ep7.py).
The world is marble_flat_world.py, the run and the race marble_flat_course.py, the beats marble_flat_<beat>.py (ball,
shop, build, finish, race); the walking kit is flat_motion.py (arm swing, Twigs knee_fwd, Hans WaveGait: owner,
approving FK0016). Where one Keeper has to pass another it steps into the front lane (a little nearer us, painted in
front) and back: nobody walks through anybody.

    plan().end                      the timeline
    frame(valley, t) -> rgb         one finished 1920x1080 frame
"""
import math

import skia

from families.foundry.keepers.common import smoothstep
import numpy as np

from families.foundry.products.monster import TURN_NARROW, Monster, planted_tentacle, reach_tentacle
from families.foundry.style import lighten

from . import illustrate as il
from . import marble_flat_build as BU
from . import marble_flat_course as MC
from . import marble_flat_finish as FI
from . import marble_flat_race as RA
from . import marble_flat_shop as SH
from . import marble_flat_world as XW
from .flat_motion import Hopper, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing, stance_drop, walk_path
from .marble_flat_ball import Ball
from .storybook import C, oval, rrect

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
FPS = 60
STEP = 1.0 / FPS
K = 0.72
ORDER = ["wheels", "springs", "digger", "teeth", "tentacles", "lantern"]          # front (right) to back
NAMES = {"teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs", "tentacles": "Hans",
         "lantern": "Glo"}
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300}
V_WALK = 100.0
EASE = 1.0
WR = 46.0 * K                       # Wheels' wheel radius
FRONT = 50.0                        # the front lane: this much nearer us (feet lower on screen)

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("Springs has found a little wooden ball. And it's a very bouncy one. Today the Keepers make six marbles, "
        "and at the very end, all six race down from the treetops. Which one will come out of the tunnel first?")
LINES = {
    "idea": "Glo watches it roll... and has an idea.",
    "shop": "A marble run! But first, they need marbles. Off to the workshop.",
    "saw": "Twigs saws six little cubes, every one the very same size.",
    "tumble": "Round and round goes the tumbler, until every corner is worn smooth.",
    "colour": "Six round wooden balls. And Glo's light gives each one a Keeper's colour.",
    "run": "Now, the marble run. Two big old trees, just right for it.",
    "pegs": "Springs bounces up, and taps every peg in tight.",
    "pegforest": "And here is a peg forest, for the marbles to rattle through.",
    "boards": "Hans hoists the boards up, hand over hand. Every board the same length, and the same gentle slope.",
    "tunnel": "Digs digs a tunnel, right through the mound.",
    "panel": "Hans lifts the peg forest into place, with four tentacles at once.",
    "lantern": "And Glo lights the finish lantern.",
    "test": "Time for a test. Wheels' little ball goes first.",
    "race": "And now, the race. Six marbles, one for each Keeper.",
    "done": "What a race! Every marble made it home.",
}
FINALE = "Goodnight, little marbles. Goodnight, forest."
SIGNOFF = "What should the Keepers build next? Tell us in the comments."
HOLD_END = 4.5


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


# ----------------------------------------------------------------------------------------------- stops

DIGS_WAIT = 4650.0                  # Digs waits here, well clear of Springs' hops by the peg forest
WHEELS_BENCH = RA.BENCH[0] + 170.0 + (SH.WHEELS_RACK - SH.RACK[0])  # the tray's left end, right of the crate
STOPS = {
    "start": dict(digger=1700.0, springs=1920.0, teeth=2160.0, tentacles=2420.0, lantern=2660.0, wheels=2900.0),
    "shop": dict(digger=3000.0, springs=3200.0, teeth=SH.TWIGS_X, tentacles=SH.HANS_X, lantern=4540.0,
                 wheels=SH.WHEELS_RACK),
    "run": dict(digger=DIGS_WAIT, springs=5380.0, teeth=BU.TWIGS_HOOK, tentacles=BU.HANS_HAUL, lantern=6960.0,
                wheels=WHEELS_BENCH),
}
RACE_SPOTS = dict(digger=4960.0, tentacles=5200.0, teeth=5420.0)
GLO_Y = G - 40 * K
GLO_RACE = (7480.0, 330.0)          # where Glo floats to watch the race (x, lift)

# Short walking bursts only (owner, approving FK0019 2026-11-06: Twigs' and Digs' walks still look "a little creepy",
# "change the angle or the crop or the zoom or something to where you're not just sitting there watching them walk").
# On the two long trips the camera rides ahead with Wheels (rolling), Hans and Glo (floating); Springs, Twigs and Digs
# set off once it has left them (LAGGED, in their order so nobody passes anybody) and are only seen arriving.
LAGGED = ("springs", "teeth", "digger")
LAG = (5.0, 5.0)                    # their later start on leg 1 (treehouse -> workshop) and leg 2 (-> the run), s
CAM_SHOP_IN = 4500.0                # the workshop frame they arrive into (Twigs walks in for the last ~3 s)
CAM_RUN_IN = 7080.0                 # the frame at the bench by TREE_B the second trip arrives into
CAM_MOUND_IN = 6750.0               # the mound frame Digs walks into
CAM_TUNNEL_OUT = 6850.0             # a look at the tunnel's far side while Digs walks back (off screen)
CAM_LANTERN = 7100.0                # the lantern shot (Twigs walks out of it to his race spot)
DIG_SETTLE = 2.0                    # Digs at the mound a moment before he digs (the camera comes over to him)


class Tray:
    """The rack-tray: on its legs in the workshop, lifted and carried by Wheels, set on the bench by TREE_B, lifted
    and tipped at the crate before the race. pose(t) -> (dx, dy, tilt deg) from its place in the workshop."""

    def __init__(self, shop, wheels_x, t_set):
        self.shop, self.wheels_x, self.t_set = shop, wheels_x, t_set
        self.race = None
        self.home_wheels = WHEELS_BENCH
        self.dx_bench = WHEELS_BENCH - SH.WHEELS_RACK
        self.dy_bench = (RA.BENCH_Y - 16.0) - SH.RACK_Y0

    def pose(self, t):
        s = self.shop
        a, b = s.lift
        if t < a:
            return 0.0, 0.0, 0.0
        if t < b:
            return 0.0, -60.0 * smoothstep(_seg(t, a, b)), 0.0
        if t < self.t_set[0]:
            return self.wheels_x(t) - SH.WHEELS_RACK, -60.0, 0.0
        if t < self.t_set[1]:
            u = smoothstep(_seg(t, *self.t_set))
            return self.dx_bench, -60.0 + (self.dy_bench + 60.0) * u, 0.0
        dx, dy, tilt = self.dx_bench, self.dy_bench, 0.0
        if self.race is not None:
            ddx, ddy, tilt = self.race.tray_pose(t)
            dx, dy = dx + ddx, dy + ddy
        return dx, dy, tilt

    def _xf(self, x, y, t):
        dx, dy, tilt = self.pose(t)
        x, y = x + dx, y + dy
        if tilt:
            px, py = SH.RACK[0] + dx, SH.RACK_Y0 + dy               # it tips about its left end
            a = math.radians(tilt)
            x, y = px + (x - px) * math.cos(a) - (y - py) * math.sin(a), py + (x - px) * math.sin(a) + (y - py) * math.cos(a)
        return x, y

    def slot_xy(self, i, t):
        return self._xf(self.shop.balls[i]["slot"], SH.RACK_Y0 - MC.R0, t)

    def plain_xy(self, t):
        return self._xf(self.shop.plain_slot, SH.RACK_Y0 - MC.R0, t)

    def end_xy(self, t):
        """Under the tray's right end (where Wheels lifts it)."""
        return self._xf(SH.RACK[1] - 14.0, SH.RACK_Y0 + 14.0, t)

    def grips(self, t):
        return (self._xf(SH.TRAY_GRIP[0], SH.RACK_Y0 + 10, t), self._xf(SH.TRAY_GRIP[1], SH.RACK_Y0 + 10, t))

    def draw(self, pg, t, sh):
        dx, dy, tilt = self.pose(t)
        if (dx, dy) == (0.0, 0.0):
            return                                                # on its legs: the workshop draws it
        x0, x1 = SH.RACK[0] + dx - sh, SH.RACK[1] + dx - sh
        c = pg.c
        c.save()
        if tilt:
            c.rotate(tilt, x0, SH.RACK_Y0 + dy)
        SH.draw_tray(pg, x0, x1, dy)
        c.restore()


class Plan:
    """The timeline, beat by beat."""

    def __init__(self):
        self.tags = (0.4, 6.0)                                     # name tags while all is calm
        self.hook = 1.6
        t_hook = _dur(HOOK)
        S0 = STOPS["start"]
        # 1. the ball
        self.ball = Ball(self.hook + 2.4, int(round((t_hook - 4.0) / 0.34)), S0["springs"], S0["wheels"])
        b = self.ball
        STOPS["caught"] = dict(S0, wheels=b.catch_x)
        self.say_idea = b.lift[1] + 1.4
        self.idea = self.say_idea + 1.2
        t_go = self.idea + 2.4
        self.say_shop = t_go + 1.0
        # 2. the marbles
        t_arr = self._walk("caught", "shop", t_go)                 # Wheels, Hans and Glo there
        t_shop = t_arr + LAG[0] + 2.5                              # Twigs in, the camera back on the bench
        self.shop = SH.Shop(t_shop)
        s = self.shop
        self.say_saw = s.cuts[0]["out"][0] - 0.6
        self.say_tumble = s.wheels["drive"][0] + 1.0
        self.say_colour = s.glo_in[0]
        # 3. the run
        t_go2 = s.end + 0.4
        self.say_run = t_go2 + 2.0
        t_run = self._walk("shop", "run", t_go2)                  # Wheels, Hans and Glo there
        self.t_run = t_run
        self.build = BU.Build(t_run + LAG[1] + 7.1, STOPS["run"]["springs"])   # once the camera is back at TREE_A
        bu = self.build
        self.say_pegs = bu.taps[0][2] - 1.0
        self.say_pegforest = bu.dowel_taps[0][2] - 2.2
        self.say_boards = bu.boards[0]["rise"][0]
        # Springs: back up onto TREE_B's lowest stub to wait (the race starts from there)
        self.b_stands = [BU.Build.stand_for(sp, -1) for k, side, sp in reversed(bu.b_spots)]
        self.sp_wait = BU.Hops()
        self.sp_wait.hop(bu.pegs_end + 0.4, (BU.B_GROUND, G), self.b_stands[0])
        # Digs walks to the mound; the tunnel, the peg forest, the lantern
        t_dig = bu.end + 0.5
        self.digs_at = t_dig + abs(FI.DIG_X - STOPS["run"]["digger"]) / V_WALK + EASE
        self.fin = FI.Finish(self.digs_at + DIG_SETTLE, BU.HANS_HAUL)
        f = self.fin
        self.t_dig_walk = t_dig
        self.say_tunnel = f.dig[0]
        self.say_panel = f.lift[0]
        self.say_lantern = f.lamp[0] - 0.6
        # to the race spots: Hans first, then Twigs and Digs (so nobody passes anybody)
        self.spots_hans = (f.panel_end + 0.4, f.panel_end + 0.4 + abs(f.hans_carry_x(f.panel_end) -
                                                                          RACE_SPOTS["tentacles"]) / V_WALK + EASE)
        self.spots_twigs = (self.spots_hans[0] + 4.0, self.spots_hans[0] + 4.0 +
                            abs(BU.TWIGS_HOOK - RACE_SPOTS["teeth"]) / V_WALK + EASE)
        self.spots_digs = (self.spots_hans[1] - 2.0, self.spots_hans[1] + 1.0)
        t_race = max(f.end, self.spots_twigs[1]) + 0.5
        # 4. the test run, the race, 5. the cheer
        self.tray = Tray(self.shop, lambda tt: self.paths["wheels"](tt), (t_run + 0.2, t_run + 1.6))
        self.race = RA.Race(t_race, self.b_stands, self.tray)
        self.tray.race = self.race
        r = self.race
        self.shop.tray_off = lambda tt: self.tray.pose(tt)[:2]
        self.shop.tray_grips = self.tray.grips
        self.shop.release = self.tray.t_set[1]
        self.say_test = r.w_take[0] + 0.2
        self.say_race = r.cycles[1]["up"] - 0.4
        self.say_done = r.cheer[0] + 0.6
        self.finale = r.rabbit[1] - 1.0
        self.sign = (self.finale + _dur(FINALE) + HOLD_END, None)
        self.sign = (self.sign[0], self.sign[0] + 1.0)
        self.signoff = self.sign[1] + 0.3
        self.end = self.signoff + _dur(SIGNOFF) + 2.5
        self.legs = [("caught", t_go, "shop", t_arr), ("shop", t_go2, "run", t_run)]
        self.lanes = {"springs": [(bu.b_go - 0.2, bu.b_at + 0.2)],
                      "tentacles": [(f.dig_end + 1.0, f.panel_at - 0.3)]}
        self.paths = self._paths()
        self.glo_keys = self._glo()
        tw1 = t_arr + LAG[0]                                       # Twigs at the bench (leg 1)
        tw2 = t_run + LAG[1]                                       # Twigs at the hook (leg 2)
        self.cam = XW.Cam([(0.0, 2150.0, 1.0), (b.away + 0.6, 2150.0, 1.0), (b.rest_t + 1.2, 2750.0, 1.0),
                           # leg 1: ride ahead with Wheels, Hans and Glo; Twigs walks into the workshop frame
                           (t_go + 1.0, 2750.0, 1.0), (t_go + 15.0, CAM_SHOP_IN, 1.0), (tw1 + 0.6, CAM_SHOP_IN, 1.0),
                           (tw1 + 3.8, 4150.0, 1.0), (s.hans["reach"][0], 4150.0, 1.0),
                           (s.wheels["drive"][0], 4450.0, 1.0), (s.end + 1.0, 4450.0, 1.0),
                           # leg 2: ride ahead with Wheels carrying the tray, to the bench; back to TREE_A
                           (t_go2 + 24.0, CAM_RUN_IN, 1.0), (tw2 + 0.6, CAM_RUN_IN, 1.0),
                           (tw2 + 8.6, 5900.0, 1.0), (bu.dowels_end, 5900.0, 1.0),
                           (bu.b_at + 1.0, 6400.0, 0.86), (bu.end, 6400.0, 0.86),
                           # Digs walks into the mound frame, the camera comes over to his dig
                           (bu.end + 9.0, CAM_MOUND_IN, 1.0), (self.digs_at + 0.3, CAM_MOUND_IN, 1.0),
                           (self.digs_at + 5.5, 6000.0, 1.0), (f.dig_end, 6000.0, 1.0),
                           # the tunnel's far side while Digs walks back; Hans and the peg forest
                           (f.dig_end + 5.5, CAM_TUNNEL_OUT, 1.0), (f.dig_end + 6.0, CAM_TUNNEL_OUT, 1.0),
                           (f.panel_at - 0.5, 5900.0, 1.0), (f.panel_end, 5900.0, 1.0),
                           # the lantern shot (Twigs walks out of it), then back for the whole run
                           (f.panel_end + 8.0, CAM_LANTERN, 1.0), (self.spots_twigs[1] + 0.8, CAM_LANTERN, 1.0),
                           (r.cycles[0]["up"] - 2.0, 6320.0, 0.63), (r.cheer[0], 6320.0, 0.63),
                           (r.rabbit[0] + 3.0, 6800.0, 0.8), (self.end, 6800.0, 0.8)])
        XW.LIGHT = [(0.0, "day"), (t_run, "day"), (bu.end, "golden"), (r.cycles[1]["take"][0], "golden"),
                    (r.go, "dusk")]
        self.turns = {kd: heading(self.paths[kd]) for kd in ORDER}
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {kd: biped(kd, self.paths[kd], G, K, spread=narrow(kd)) for kd in ("teeth", "digger")}
        self.gaits["tentacles"] = WaveGait(G, K, self.paths["tentacles"], spread=narrow("tentacles", 0.5))
        self.hopper = Hopper(self.paths["springs"], G, K)
        self.voices = []
        self.voices = voices(self)

    def _walk(self, a, b, t0):
        d = max(abs(STOPS[b][kd] - STOPS[a][kd]) / (2.0 if kd == "lantern" else (1.3 if kd == "wheels" else 1.0))
                for kd in ORDER)
        return t0 + d / V_WALK + EASE

    def _paths(self):
        out = {}
        bu, f, r, s = self.build, self.fin, self.race, self.shop
        for kd in ORDER:
            keys = [(0.0, STOPS["start"][kd])]
            if kd == "wheels":
                keys += self.ball.wheels_keys()
                keys += s.wheels_keys()
                keys += r.wheels_keys(WHEELS_BENCH)
            for i, (a, ta, b, tb) in enumerate(self.legs):
                d = LAG[i] if kd in LAGGED else 0.0
                keys += [(ta + d, STOPS[a][kd]), (tb + d, STOPS[b][kd])]
            if kd == "springs":                                    # the ground walk from TREE_A over to TREE_B
                # (under his hop schedules the walk moves early, so it has settled before he walks on by himself)
                keys += [(bu.hops_a.hops[0][0] + 0.6, STOPS["run"]["springs"]),
                         (bu.hops_a.hops[0][0] + 1.7, bu.springs_ground_a[0]), (bu.dowels_end, bu.springs_ground_a[0]),
                         (bu.b_go, bu.springs_ground_a[0]), (bu.b_at, BU.B_GROUND)]
            if kd == "digger":
                keys += [(self.t_dig_walk, STOPS["run"]["digger"]), (self.digs_at, FI.DIG_X),
                         (f.dig_end, FI.DIG_X), (f.dig_end + 1.0 + abs(FI.DIG_X - DIGS_WAIT) / V_WALK, DIGS_WAIT),
                         (self.spots_digs[0], DIGS_WAIT), (self.spots_digs[1], RACE_SPOTS["digger"])]
            if kd == "tentacles":                                  # over to the basket and back, both ways
                h = s.hans
                keys += [(h["reach"][0] - 1.6, SH.HANS_X), (h["reach"][0] + 0.2, SH.HANS_X - 110.0),
                         (h["lift"][0], SH.HANS_X - 110.0), (h["lift"][1], SH.HANS_X),
                         (h["back"][0], SH.HANS_X), (h["back"][1], SH.HANS_X - 110.0),
                         (h["back"][1] + 0.3, SH.HANS_X - 110.0), (h["back"][1] + 2.0, SH.HANS_X)]
                keys += [(f.dig_end + 1.5, BU.HANS_HAUL), (f.panel_at, FI.Finish.panel_stand()),
                         (f.carry[0], f.hans_carry_x(f.carry[0])), (f.carry[1], f.hans_carry_x(f.carry[1])),
                         (self.spots_hans[0], f.hans_carry_x(f.carry[1])), (self.spots_hans[1], RACE_SPOTS["tentacles"])]
            if kd == "teeth":
                keys += [(self.spots_twigs[0], BU.TWIGS_HOOK), (self.spots_twigs[1], RACE_SPOTS["teeth"])]
            if kd == "lantern":                                    # Glo floats over to the rack to colour the balls
                keys += [(s.glo_in[0], STOPS["shop"]["lantern"]), (s.glo_in[1], s.balls[0]["slot"])]
                for i, (a_, b_) in enumerate(s.colour[1:], 1):
                    keys += [(a_ - 0.8, s.balls[i - 1]["slot"]), (a_, s.balls[i]["slot"])]
                keys += [(s.end, s.balls[5]["slot"])]
                # to each board with his level, to the finish lantern, then where he watches the race
                for k, bd in enumerate(bu.boards):
                    a_, c_ = bd["level"]
                    keys += [(a_ - 1.4, STOPS["run"]["lantern"] if k == 0 else bd["level_x"] - 40),
                             (a_, bd["level_x"]), (c_, bd["level_x"]), (c_ + 1.4, bd["level_x"] - 40)]
                keys += [(f.lamp[0] - 2.0, bu.boards[-1]["level_x"] - 40), (f.lamp[0], FI.LANTERN_X - 190.0),
                         (f.lamp[1] + 0.6, FI.LANTERN_X - 190.0), (f.lamp[1] + 4.0, GLO_RACE[0])]
            out[kd] = walk_path(sorted(set(keys)), EASE)
        return out

    def _glo(self):
        """Glo's height keys [(t, lift)]: he floats above the others whenever he moves among them."""
        s, bu, f = self.shop, self.build, self.fin
        keys = [(0.0, 0.0), (self.legs[0][3] - 4.0, 0.0), (self.legs[0][3] - 1.0, 170.0), (s.end, 170.0),
                (self.legs[1][3], 140.0)]
        for k, bd in enumerate(bu.boards):
            a_, c_ = bd["level"]
            lx = bd["level_x"]
            sy = MC.board_y(k, lx) - 6.0
            lift = GLO_Y - (sy - 10.0 + BU.GLO_TIPS)               # his tendrils' tips just over the board
            keys += [(a_ - 1.4, 140.0 if k == 0 else lift - 60.0), (a_, lift), (c_, lift), (c_ + 1.4, lift - 60.0)]
        keys += [(f.lamp[0] - 2.0, 200.0), (f.lamp[0], 200.0), (f.lamp[1] + 0.6, 200.0), (f.lamp[1] + 4.0, GLO_RACE[1])]
        return sorted(keys)

    def glo_lift(self, t):
        keys = self.glo_keys
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, a), (t1, b) in zip(keys, keys[1:]):
            if t <= t1:
                return a + (b - a) * smoothstep(_seg(t, t0, t1))
        return keys[-1][1]

    def lane(self, kd, t):
        """How far into the front lane Keeper kd is (0..1)."""
        u = 0.0
        for a, b in self.lanes.get(kd, []):
            u = max(u, smoothstep(_seg(t, a - 0.8, a)) * (1 - smoothstep(_seg(t, b, b + 0.8))))
        return u

    def shift(self, t):
        return self.cam.shift(t)

    def narration(self):
        return [(self.hook, HOOK), (self.say_idea, LINES["idea"]), (self.say_shop, LINES["shop"]),
                (self.say_saw, LINES["saw"]), (self.say_tumble, LINES["tumble"]), (self.say_colour, LINES["colour"]),
                (self.say_run, LINES["run"]), (self.say_pegs, LINES["pegs"]), (self.say_pegforest, LINES["pegforest"]),
                (self.say_boards, LINES["boards"]), (self.say_tunnel, LINES["tunnel"]), (self.say_panel, LINES["panel"]),
                (self.say_lantern, LINES["lantern"]), (self.say_test, LINES["test"]), (self.say_race, LINES["race"]),
                (self.say_done, LINES["done"]), (self.finale, FINALE), (self.signoff, SIGNOFF)]


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6
BUBBLE_R = 50.0
CUSTOM = {"idea": ("up", 2, "run"), "c3": ("up", 0, "3"), "c2": ("up", 1, "2"), "c1": ("up", 2, "1")}


def mood_info(mood):
    from .chatter import MOODS
    return CUSTOM.get(mood, MOODS.get(mood))


def voices(P):
    b, s, bu, f, r = P.ball, P.shop, P.build, P.fin, P.race
    ev = [(b.t0 + 1.0, "springs", "hehe"), (b.hits[1] + 0.1, "springs", "uhoh"), (b.w_go + 0.3, "wheels", "wee"),
          (b.lift[1] + 0.1, "wheels", "yay"), (b.lift[1] + 0.8, "springs", "hehe"), (b.lift[1] + 1.0, "digger", "hehe"),
          (P.idea, "lantern", "idea"), (P.idea + 1.6, "wheels", "ooh")]
    ev += [(s.cuts[1]["tip"][1], "teeth", "mm"), (s.cuts[3]["tip"][1], "springs", "ooh"),
           (s.cuts[5]["tip"][1] + 0.2, "teeth", "yay"), (s.hans["pour"][1], "tentacles", "hehe"),
           (s.wheels["drive"][0] + 2.0, "wheels", "wee"), (s.wheels["drive"][0] + 6.0, "digger", "ooh"),
           (s.empty["out"][0] + 0.4, "springs", "ooh"), (s.balls[5]["settle"], "tentacles", "yay")]
    for i, (a_, b_) in enumerate(s.colour):
        ev.append((b_ + 0.1, MC.KINDS[i], "yay" if i % 2 == 0 else "aww"))
    for name, spot, a_, b_, side, stand in bu.taps:
        ev.append((b_ + 0.1, "springs", "wee" if "A" in name else "hehe"))
    for k, bd in enumerate(bu.boards):
        ev += [(bd["clip"][1], "teeth", "mm"), (bd["rise"][1] - 0.4, "tentacles", "huff"),
               (bd["level"][0] + 1.6, "lantern", "mm")]
    ev += [(f.dig[0] + 3.0, "digger", "huff"), (f.through[1], "digger", "yay"), (f.let_go[1], "tentacles", "mm"),
           (f.lamp[1] + 0.2, "lantern", "aww")]
    ev += [(r.w_drop[1], "wheels", "hehe"), (r.cycles[0]["up"] + 0.4, "springs", "wee"),
           (r.test_go + r.test.finish_t + 0.3, "wheels", "yay"), (r.test_go + r.test.finish_t + 1.2, "digger", "yay"),
           (r.t_tip[1], "wheels", "mm")]
    for i, tc in enumerate(r.count):
        ev.append((tc, "springs", ("c3", "c2", "c1")[i]))
    ev += [(r.first + 0.2, r.winner, "yay"), (r.cheer[0], "teeth", "yay"), (r.cheer[0] + 1.2, "tentacles", "yay"),
           (r.rabbit[0] + 3.0, "digger", "aww")]
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    keep = ("idea", "c3", "c2", "c1")
    ev = [e for e in sorted(ev) if e[2] in keep or not any(a - 0.7 <= e[0] <= b_ + 0.7 for a, b_ in lines)]
    out = []
    for e in ev:
        if not out or e[0] - out[-1][0] >= 1.0 or e[2] in keep:
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


# ----------------------------------------------------------------------------------------------- the Keepers

LEG = {"digger": (62.0, 78.0)}


# monster.py's two-bone arms put the elbow "down and out" (prefer (sx * 0.4, 1) Twigs, (sx * 0.5, 1) Wheels): the
# elbow changes sides where the hand's direction from the shoulder crosses that line (either way along it). Close to
# those lines the hand is eased out to a straight arm, so the change happens with the elbow on the arm's line and
# can't be seen (it would otherwise snap 40-110 px in one frame).
UNFLIP = {"teeth": (0.4, lambda x, y, sx: (x + sx * 82 * K, y - 340 * K)),
          "wheels": (0.5, lambda x, y, sx: (x + sx * 100 * K, y - 210 * K + 10 * K))}
ARM_L = {"teeth": None, "wheels": None}
UNFLIP_BAND = 9.0                                                  # degrees either side of the line


def _arm_len(kd):
    from families.foundry.products.monster import TWIGS_FORE, TWIGS_UPPER, WHEELS_FORE, WHEELS_UPPER
    return ((TWIGS_UPPER + TWIGS_FORE) if kd == "teeth" else (WHEELS_UPPER + WHEELS_FORE)) * K


def unflip(kd, x, y, arm_to, sh):
    """arm_to targets (screen) eased out to a straight arm near the elbow's change-over line."""
    if kd not in UNFLIP or not arm_to:
        return arm_to
    px, shoulder = UNFLIP[kd]
    L = _arm_len(kd) * 1.012
    out = {}
    for sx, (tx, ty) in arm_to.items():
        sxw, syw = shoulder(x, y, sx)
        dx, dy = tx + sh - sxw, ty - syw
        d = math.hypot(dx, dy) or 1e-6
        th = math.degrees(math.atan2(dy, dx))
        line = math.degrees(math.atan2(1.0, sx * px))
        diff = min(abs((th - line + 180) % 360 - 180), abs((th - line) % 360 - 180))
        band = UNFLIP_BAND * (1.8 if kd == "wheels" else 1.0)     # Wheels' short arms swing faster past it
        if diff < band and d < L:
            w = smoothstep(1 - diff / band)
            d2 = d + (L - d) * w
            tx, ty = sxw + dx / d * d2 - sh, syw + dy / d * d2
        out[sx] = (tx, ty)
    return out


# The resting arm is aimed by the same two-bone reach as a working one (never monster.py's separate hanging-arm code,
# whose elbow sits on the other side): a reach starting or ending is then one continuous motion, with no switch.
REST_ARM = {"teeth": (0.93, 0.16, 0.42), "wheels": (0.9, 0.6, 0.4)}    # reach (x arm length), out (rad), swing


def rest_arms(kd, x, y, t, a):
    """arm_to with the resting hand added for any arm that has no target (screen coords)."""
    P = plan()
    sh = P.shift(t)
    out = dict(a.get("arm_to") or {})
    reach, o, amp = REST_ARM[kd]
    L = _arm_len(kd) * reach
    h = max(-1.0, min(1.0, a.get("legs_turn", 0.0) or 0.0))
    for sx in (-1, 1):
        if sx in out:
            continue
        sw = (a.get("arm_swing") or 0.0) * sx
        ang = sx * o * (1 - 0.6 * abs(h)) + h * sw * amp
        shx, shy = UNFLIP[kd][1](x, y, sx)
        out[sx] = (shx + math.sin(ang) * L - sh, shy + math.cos(ang) * L)
    return out


def keeper(kd, t):
    """(world x, y, monster attrs) of Keeper kd at time t, talking when it says something."""
    x, y, a = _keeper(kd, t)
    P = plan()
    a["legs_turn"] = P.turns[kd](t)
    a["turn"] = a["legs_turn"] * (1 - a.pop("face_us", 0.0))
    if kd != "lantern":
        y += FRONT * P.lane(kd, t)
    if P.voices:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd not in ("teeth", "digger", "tentacles"):
                y -= hop
    if kd == P.race.winner and P.race.cheer[0] <= t < P.race.cheer[1]:   # the winner's Keeper hops for joy
        u = (t - P.race.cheer[0]) / 0.8
        if kd not in ("teeth", "digger", "tentacles"):
            y -= 34.0 * abs(math.sin(math.pi * u))
    if kd in UNFLIP:                                               # both arms always reach for a point: at rest
        a["arm_to"] = unflip(kd, x, y, rest_arms(kd, x, y, t, a), P.shift(t))   # (hanging, swinging) too
    return x, y, a


def wheels_x(t):
    return plan().paths["wheels"](t)


def wheels_hand(t, side=1):
    """Wheels' pincer on `side` (world xy) as aimed."""
    x = wheels_x(t)
    h = wheels_hands(t, x)
    rest = (x + side * 110 * K, G - 150 * K)
    return h.get(side, rest) if h else rest


def wheels_hands(t, x):
    P = plan()
    for src in (P.race.wheels_hands(t, x), P.shop.wheels_hands(t, x)):
        if src:
            return src
    hd = P.ball.wheels_hand(t, x)
    if hd is not None and t < P.shop.wheels["place"][1] + 0.5:
        return {1: hd}
    return None


def springs_xy(t):
    x, y, a = keeper("springs", t)
    return x, y


def twigs_hand(t, side=1):
    """Twigs' hand target (screen xy) on side, for the checks."""
    P = plan()
    x = P.gaits["teeth"].body_x(t)
    h = _twigs_hands(t, x)[0].get(side)
    return (h[0] - P.shift(t), h[1]) if h else (x - P.shift(t), G - 150)


def _rest_hand(kd, x, y, t, sx):
    """Where the resting arm's hand is (world xy), as rest_arms aims it (standing still)."""
    reach, o, amp = REST_ARM[kd]
    L = _arm_len(kd) * reach
    shx, shy = UNFLIP[kd][1](x, y, sx)
    return shx + math.sin(sx * o) * L, shy + math.cos(sx * o) * L


def _twigs_hands(t, x):
    P = plan()
    hands, blade, grip = P.shop.twigs_hands(t, x)
    if hands:
        s = P.shop                                                 # into and out of the sawing: eased, no snap
        a0, a1 = s.t0 + 0.8, s.cuts_end + 0.8
        u = smoothstep(_seg(t, a0, a0 + 0.7)) * (1 - smoothstep(_seg(t, a1 - 0.7, a1)))
        if u < 1.0:
            hands = {sx: (lambda r, h: (r[0] + (h[0] - r[0]) * u, r[1] + (h[1] - r[1]) * u))(
                _rest_hand("teeth", x, G, t, sx), hd) for sx, hd in hands.items()}
        return hands, blade, grip
    h = P.build.twigs_hands(t, x)
    if h:
        return h, 0.0, 0.9
    return {}, 0.0, 0.0


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    if kd in ("teeth", "digger", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        lane = FRONT * P.lane(kd, t)
        a = dict(feet=[(fx - sh, fy + lane) for fx, fy in g.feet(t)], attend=0.25)
        if kd == "tentacles":
            a.update(float=0.2, **hans_mood("calm"))
            if hans_lift(t) > 0.0:                                 # his legs are drawn by hans_pre (two lift)
                a["attach"] = dict(wings=1.0, beard=1.0, eyes=1.0, legs=0.0)
            return x, G + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(hands=True, saws=False, blades=0.0, knee_fwd=True, clamp_reach=True)
            hands, blade, grip = _twigs_hands(t, x)
            if hands:
                a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, blades=blade, blades_l=0.0,
                         grip=grip)
            c0, c1 = P.race.cheer
            if P.race.winner == "teeth" and c0 - 0.5 <= t < c1 + 0.8:    # his marble won: both arms up, waving
                u = smoothstep(_seg(t, c0 - 0.5, c0)) * (1 - smoothstep(_seg(t, c1, c1 + 0.8)))
                wave = 10.0 * math.sin((t - c0) * 7.0)
                up = {s_: (x + s_ * (80 + 30 * u) * K, G - 380 * K - 150 * K * u + s_ * wave * u) for s_ in (-1, 1)}
                a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in up.items()}, grip=0.0, smile=1.0)
            return x, G, a
        hip, leg = LEG[kd]
        n = 1.0 - TURN_NARROW * abs(P.turns[kd](t))
        y = G + stance_drop(g, lambda t_: (x - hip * K * n, x + hip * K * n), leg * K, t)
        ang = P.fin.paw_angle(t, x, y)
        if ang is not None:
            a["paw_ang"] = {1: ang}
        return x, y, a
    if kd == "springs":
        st = None
        for src in (P.race.springs_state, P.build.springs_state, P.sp_wait.state):
            st = src(t)
            if st is not None:
                break
        if st is None and t >= P.sp_wait.hops[-1][1]:            # waiting on his stub
            st = (P.b_stands[0][0], P.b_stands[0][1], 0.0)
        if st is None:
            x, y, sq = P.hopper.state(t)
        else:
            x, y, sq = st
        a = dict(spring=sq + P.ball.springs_squash(t), attend=0.25, arm_swing=0.0)
        hd = P.ball.springs_hand(t)
        hands = {1: hd} if hd is not None else (P.build.springs_hand(t) or P.race.springs_hands(t, x, y))
        if hands:
            a["arm_to"] = {s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}
        return x, y, a
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR + P.shop.wheels_spin(t), attend=0.25, arm_swing=roll_swing(P.paths[kd], t, WR),
                 clamp_reach=True)
        hands = wheels_hands(t, x)
        if hands:
            a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, grip=1.0)
        return x, G, a
    return P.paths[kd](t), GLO_Y - P.glo_lift(t), dict(attend=0.25, lamp=1.0 + 0.8 * glo_flare(t))


def glo_flare(t):
    P = plan()
    u = 0.0
    for a_, b_ in list(P.shop.colour) + [P.fin.lamp]:
        u = max(u, smoothstep(_seg(t, a_, a_ + 0.4)) * (1 - smoothstep(_seg(t, b_ - 0.2, b_ + 0.4))))
    return u


def _hans_targets(t, x):
    P = plan()
    return P.shop.hans_targets(t, x) + P.build.hans_targets(t, x) + P.fin.hans_targets(t, x)


# Hans has 8 tentacles in all, never more (owner 2026-11-06): six legs down means two arms; for a 3rd and 4th arm a
# leg visibly lifts off the ground and becomes it. Only the peg forest needs four (slots -2..2): his two left legs
# (nearest the panel) lift to be slots -2 and 2 while he stands and walks on the other four.
HANS_LIFT = {-2: 0, 2: 1}           # working slot -> the leg that lifts to become it (outer leg, farther target)
N_SPINE = 48


def hans_lift(t):
    """0..1: how far Hans' legs 0 and 1 have turned from legs into arms (around the peg forest's grip .. let go)."""
    f = plan().fin
    a, b = f.grip[0] - 0.4, f.let_go[1] + 0.8                     # the panel tentacles' own window
    return smoothstep(_seg(t, a - 0.7, a + 0.1)) * (1 - smoothstep(_seg(t, b, b + 0.7)))


class _Rec:
    """A canvas that only keeps the first polygon (a tentacle's outline), to read its spine and widths."""

    def __init__(self, flat):
        self.flat_look, self.poly = flat, None

    def polygon(self, poly, col):
        if self.poly is None:
            self.poly = np.asarray(poly, np.float64)

    def polyline(self, *a, **kw):
        pass

    def circle(self, *a, **kw):
        pass


def _spine_of(rec):
    """-> (spine N_SPINE x 2, widths) resampled evenly along its length, from a tentacle's outline."""
    q = rec.poly
    n = len(q) // 2
    left, right = q[:n], q[n:][::-1]
    sp, w = (left + right) / 2, np.linalg.norm(left - right, axis=1)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
    v = np.linspace(0.0, arc[-1], N_SPINE)
    return np.stack([np.interp(v, arc, sp[:, 0]), np.interp(v, arc, sp[:, 1])], axis=1), np.interp(v, arc, w)


def _draw_leg(cv, sp, w, col, side, sucker, flat):
    """A leg tentacle from its spine and widths, drawn the way monster.planted_tentacle draws one."""
    dd = np.gradient(sp, axis=0)
    dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-9
    nn = np.stack([-dd[:, 1], dd[:, 0]], axis=1)
    poly = np.vstack([sp + nn * (w / 2)[:, None], (sp - nn * (w / 2)[:, None])[::-1]])
    col = np.asarray(col)
    cv.polygon(poly, col)
    if flat:
        cv.circle(sp[-1][0], sp[-1][1], w[-1] / 2, col)
    cv.polyline(poly, col * 0.55, 2, closed=True)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
    for q in np.linspace(0.18, 0.8, 5):
        i = int(np.searchsorted(arc, q * arc[-1]))
        sx, sy = sp[i] - nn[i] * (side * w[i] * 0.32)
        cv.circle(sx, sy, w[i] * 0.13, lighten(col, 1.35) if sucker is None else sucker)
    return float(arc[-1])


def hans_pre(t, sh):
    """Hans' legs while two of them lift to work (drawn before his body, as his own legs are): the four still
    standing exactly as the Monster draws them, legs 0 and 1 blending from planted legs into reaching arms (their tips
    leave the ground and go to the panel). Records m.leg_len (legs down) and m.lifted for the checks."""
    def draw(cv, m):
        u = hans_lift(t)
        m.lifted = []
        if u <= 0.0 or m.feet is None:
            return
        k = m.k
        col = m.parts_col.get("legs", np.asarray(m.color) * 0.82)
        sucker = m.parts_col.get("suckers")
        flat = bool(getattr(cv, "flat_look", False) is True)
        tg = {slot: (p, g) for slot, p, g in _hans_targets(t, m.x + sh)}
        m.leg_len = []
        for i, ft in enumerate(m.feet):
            root = m.leg_root(i, t)
            side = 1 if (i - 2.5) / 2.5 > 0 else -1
            slot = next((s_ for s_, j in HANS_LIFT.items() if j == i), None)
            if slot is None:
                m.leg_len.append(planted_tentacle(cv, root, ft, 275 * k, 44 * k, col, side, sucker))
                continue
            (tx, ty), on = tg.get(slot, ((ft[0] + sh, ft[1]), 0.0))
            on = min(max(on, 0.0), 1.0)
            tip = (ft[0] + (tx - sh - ft[0]) * on, ft[1] + (ty - ft[1]) * on)
            rp, rr = _Rec(flat), _Rec(flat)
            L0 = planted_tentacle(rp, root, ft, 275 * k, 44 * k, col, side, sucker)
            L1 = reach_tentacle(rr, root[0], root[1], tip[0], tip[1], 50 * k, col, t, 1.3 * slot + 0.7,
                                1 if tip[0] >= root[0] else -1, on)
            (s0, w0), (s1, w1) = _spine_of(rp), _spine_of(rr)
            e = smoothstep(u)
            _draw_leg(cv, s0 * (1 - e) + s1 * e, w0 * (1 - e) + w1 * e, col, side, sucker, flat)
            # its length measured as monster.py measures each (a reaching arm without its wrapped tip)
            m.lifted.append((i, root, tip, L0 * (1 - e) + L1 * e))
    return draw


def hans_extra(t, sh):
    """Hans' working tentacles, drawn on his own layer; records m.work for the checks."""
    def draw(cv, m):
        m.work = []
        lifted = hans_lift(t) > 0.0
        for slot, (tx, ty), grip in _hans_targets(t, m.x + sh):
            if grip <= 0.001 or (lifted and slot in HANS_LIFT):  # a lifted leg holds it (hans_pre)
                continue
            side = 1 if tx - sh >= m.x else -1
            rest = (m.x + side * (30 + 20 * abs(slot)) * K, m.y - 24.0)          # hanging among his legs
            gx, gy = rest[0] + (tx - sh - rest[0]) * grip, rest[1] + (ty - rest[1]) * grip
            root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=1.0)       # always the whole tentacle
            m.work.append((slot, root, (gx, gy), L))
    return draw


def hans_tip(t):
    """Where Hans' first working tentacle holds (screen xy), for the checks."""
    P = plan()
    x = P.gaits["tentacles"].body_x(t)
    tg = _hans_targets(t, x)
    return (tg[0][1][0] - P.shift(t), tg[0][1][1]) if tg else (x - P.shift(t), G - 200)


def hans_grip(t):
    """The lowest pulling grip on the rope (world), for drawing the rope's hauling side."""
    P = plan()
    x = P.gaits["tentacles"].body_x(t)
    tg = [p for slot, p, g in P.build.hans_targets(t, x) if g > 0.5]
    if tg:
        return max(tg, key=lambda p: p[1])
    return BU.ROPE_X, G - 260.0


# ----------------------------------------------------------------------------------------------- drawing helpers

def figure(pg, kind, x, y, k, t=1.3, extra=None, pre=None, **attrs):
    """il.figure (flat style 6) for a page whose canvas is translated (a pulled-back frame): the Keeper's own layer
    is translated the same way, so it lands where the working coords say, its grain fixed to it."""
    from .doorway import HALF_W
    m = Monster(kind, k=k)
    m.x, m.y, m.newlook = x, y, True
    if kind == "teeth":
        m.hands, m.saws = True, False
    if kind == "tentacles":
        from .flat_motion import HANS_COLOURS
        m.parts_col = dict(HANS_COLOURS, wings=(214, 100, 28))
    if kind == "digger":
        m.mole_claws, m.hat_orb = True, True
    for a, v in attrs.items():
        setattr(m, a, v)
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=Monster.KINDS.index(kind) + 1)
    cv.eye_scale = 1.15
    cv.c.translate(pg.ox, pg.oy)
    if pre is not None:
        pre(cv, m)
    m.draw(cv, t, il.Glow())
    if extra is not None:
        extra(cv, m)
    pg.grain_on(cv.c, x, y, getattr(cv, "bounds", None))
    hw = HALF_W.get(kind, 200.0) * k
    pg.shadow(x, y + 4, hw * 0.75, 14 + 10 * k, il.STYLES[6]["shadow"])
    with XW.raw(pg):
        pg.c.drawImage(cv.surface.makeImageSnapshot(), 0, 0)
    for path, col in cv.glows:
        b = path.getBounds()
        r = max(b.width(), b.height()) * 0.5
        pg.glow(b.centerX(), b.centerY(), r * 2.2, col, 0.38)
        p = skia.Paint(AntiAlias=True, Color=C(col, 0.55), BlendMode=skia.BlendMode.kScreen)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.35 + 1))
        pg.c.drawPath(path, p)
    return m


def creature(pg, draw, x, y, shadow=None):
    """il.creature for a translated page."""
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=int(abs(x)) % 97 + 1)
    cv.c.translate(pg.ox, pg.oy)
    draw(cv)
    pg.grain_on(cv.c, x, y, getattr(cv, "bounds", None))
    if shadow:
        pg.shadow(x, y + 2, shadow, max(6.0, shadow * 0.16), il.STYLES[6]["shadow"])
    with XW.raw(pg):
        pg.c.drawImage(cv.surface.makeImageSnapshot(), 0, 0)


# ----------------------------------------------------------------------------------------------- overlays (screen)

_FONT = {}
INK, PAPER = (70, 52, 44), (252, 246, 234)


def _font(size, weight="Bold"):
    key = (size, weight)
    if key not in _FONT:
        import os
        path = os.path.join(XW.__file__, "..", "..", "..", "engine", "assets", "fonts", f"Inter-{weight}.otf")
        _FONT[key] = skia.Font(skia.Typeface.MakeFromFile(os.path.abspath(path)), size)
    return _FONT[key]


def _text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold", center=False):
    f = _font(size, weight)
    if center:
        x -= f.measureText(s) / 2
    pg.c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def _card(pg, x, y, w, h, a):
    pg.flat(rrect(x + 4, y + 6, x + w + 4, y + h + 6, 18), (40, 28, 24), 0.18 * a, blur=8)
    pg.flat(rrect(x, y, x + w, y + h, 18), PAPER, 0.94 * a)


def screen_xy(P, t, x, y):
    cx, z = P.cam(t)
    return XW.to_frame(x - (cx - W / 2), y, z)




def overlays(out, t):
    """Screen-space text on the finished frame (it holds still): the name tags, the standings, the end sign."""
    P = plan()
    a0, a1 = P.tags
    if a0 < t < a1 + 1.0:
        a = smoothstep((t - a0) / 0.8) * (1 - smoothstep((t - a1) / 1.0))
        for kd in ORDER:
            x, y, _ = keeper(kd, a1)                               # tags hold still: placed where they stand then
            sx, sy = screen_xy(P, a1, x, y - KH[kd] * K - 26)
            if 60 < sx < W - 60:
                tw = _font(30).measureText(NAMES[kd])
                _card(out, sx - tw / 2 - 16, sy - 34, tw + 32, 46, a)
                _text(out, NAMES[kd], sx, sy, 30, a=a, center=True)
    standings(out, t)
    end_sign(out, t)


def standings(out, t):
    """The standings strip (top left): each marble's colour and its Keeper's name, in race order."""
    P = plan()
    r = P.race
    order = r.standings(t)
    if order is None:
        return
    a = smoothstep(_seg(t, r.go - 0.2, r.go + 0.6)) * (1 - smoothstep(_seg(t, r.cheer[1] + 2.0, r.cheer[1] + 3.0)))
    if a <= 0.01:
        return
    x0, y0 = 36.0, 36.0
    _card(out, x0, y0, 270, 30 + 46 * 6, a)
    for j, lane in enumerate(order):
        kd = MC.KINDS[lane]
        y = y0 + 38 + 46 * j
        done = r.finish[lane] <= t
        _text(out, f"{j + 1}", x0 + 30, y + 10, 26, a=a, center=True)
        out.flat(oval(x0 + 74, y, 15, 15), MC.MARBLE_COLS[kd], a)
        _text(out, NAMES[kd], x0 + 102, y + 10, 28, a=a, weight="Bold" if done else "Medium")


def end_sign(out, t):
    P = plan()
    sa = smoothstep(_seg(t, *P.sign))
    if sa <= 0:
        return
    bw, bh = 1000, 230
    x0, y0 = (W - bw) / 2, 110
    out.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * sa, blur=10)
    out.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), sa)
    out.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), sa)
    _text(out, "WHAT SHOULD THEY BUILD NEXT?", W / 2, y0 + 110, 58, col=PAPER, a=sa, center=True)
    _text(out, "Comment your idea below!", W / 2, y0 + 172, 34, col=(250, 232, 200), a=sa, weight="Medium",
          center=True)


def bubbles(out, t):
    from .chatter import _back, bubble
    P = plan()
    _, z = P.cam(t)
    for tv, kd, mood in P.voices:
        u = t - tv
        pic = mood_info(mood)[2]
        life = 2.6 if mood == "idea" else (1.0 if mood in ("c3", "c2", "c1") else 1.4)
        if pic is None or pic in ("!", "?") or not (0 <= u < life) or t >= P.sign[0] - 4.0:
            continue
        x, y, _ = keeper(kd, t)
        sx, sy = screen_xy(P, t, x + 70 * K, y - KH[kd] * K)
        sx, sy = sx + 26, sy - 62
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - life + 0.3) / 0.3))
        r = BUBBLE_R * (1.25 if mood == "idea" else 1.0)
        digit = pic if pic in ("1", "2", "3") else None
        il.creature(out, lambda cv, bx=sx, by=sy, s=s, pic=pic, r=r: bubble(cv, bx, by, r * s, "none" if digit else pic,
                                                                          (214, 196, 176), 1.0, (bx - 62, by + 92)),
                    sx, sy)
        if digit and s > 0.2:                                      # the countdown: a big number in the bubble
            _text(out, digit, sx, sy + 22 * s, 64 * s, col=(196, 70, 60), center=True)


# ----------------------------------------------------------------------------------------------- the plain ball

def plain(t):
    """(x, y, spin, holder) of Wheels' plain ball: Springs' bouncy ball, then in Wheels' pincer, the tray's end slot,
    the test run. holder None = it lies or rolls by itself."""
    P = plan()
    s, r = P.shop, P.race
    a = s.wheels["place"][0] + 0.6
    if t < a:
        x, y, held = P.ball.pos(t, wheels_hand)
        return x, y, P.ball.spin(t), held
    if t < r.w_take[0] + 0.6:
        x, y = P.tray.plain_xy(t)
        return x, y, 0.0, "the tray"
    return None


def dowel_drawer(pg, t, sh, placed):
    """Draws one lane's slice of every peg-forest dowel (for interleaving with the marbles)."""
    def draw(lane):
        if not placed:
            return
        for (x, y) in MC.pegs():
            MC.draw_dowel(pg, x, y, lane, lane, sh)
    return draw


# ----------------------------------------------------------------------------------------------- the frame

def frame(valley, t, cam=None, ui=True):
    """cam: (x, zoom) to look from instead of the plan's camera (thumbnails); ui False: no bubbles, tags or strip."""
    P = plan()
    cx, z = cam if cam is not None else P.cam(t)
    sh = cx - W / 2
    Pg = XW.Page(z)
    pg = Pg.pg
    bu, f, r, s = P.build, P.fin, P.race, P.shop
    XW.sky(Pg, t)
    valley.draw(Pg, sh)
    # the trees: stubs and pegs, the pulley's rope, the run
    bu.draw_trees_bits(pg, t, sh)
    placed = t >= f.seat[1]
    if placed:
        MC.draw_box_back(pg, sh)
    bu.draw_boards(pg, t, sh, placed=True)
    MC.draw_tunnel_inside(pg, sh, f.hole(t))
    f.draw_ramp(pg, t, sh)
    r.draw_marbles(pg, t, sh, dowel_drawer(pg, t, sh, placed), wheels_hand)
    MC.draw_tunnel_shade(pg, sh, f.hole(t))
    MC.draw_mound(pg, sh, f.hole(t))
    if placed:
        MC.draw_box_walls(pg, sh)
    else:
        bu.draw_panel(pg, t, sh, f.panel_pose(t))
    bu.draw_stack(pg, t, sh)
    bu.draw_boards(pg, t, sh, placed=False)
    bu.draw_rope(pg, t, sh, hans_grip(t))
    sx, sy = springs_xy(t)
    r.draw_gate(pg, t, sh, (r.springs_hands(t, sx, sy) or {}).get(-1))
    f.draw_lantern(pg, t, sh)
    # the workshop and the bench
    s.draw_back(pg, t, sh)
    r.draw_bench(pg, t, sh)
    carried = s.lift[0] <= t < P.tray.t_set[1]
    if not carried:
        P.tray.draw(pg, t, sh)
        if t < r.t0:
            s.draw_balls(pg, t, sh)
        else:
            r.draw_loose(pg, t, sh, wheels_hand)
    crate_held = any(c["take"][0] <= t < c["put"][1] and not (c["hold"][1] + 0.6 <= t < c["gate"][1] + 1.2)
                     for c in r.cycles)
    if not crate_held:
        r.draw_crate(pg, t, sh, (sx, sy))
    f.draw_heap(pg, t, sh)
    # the Keepers, the back lane first
    ms = {}
    order = sorted(reversed(ORDER), key=lambda kd: P.lane(kd, t) if kd != "lantern" else -1.0)
    for kd in order:
        x, y, a = keeper(kd, t)
        if -800 < x - sh < W / z + 800:
            ms[kd] = figure(pg, kd, x - sh, y, K, t=t, extra=hans_extra(t, sh) if kd == "tentacles" else None,
                            pre=hans_pre(t, sh) if kd == "tentacles" else None, **a)
    # in front of them
    if carried:
        P.tray.draw(pg, t, sh)
        s.draw_balls(pg, t, sh)
    if crate_held:
        r.draw_crate(pg, t, sh, (sx, sy))
    RA.draw_rabbit(pg, r, t, sh)
    s.draw_front(pg, t, sh)
    p = plain(t)
    if p is not None:
        P.ball.draw_at(pg, p[0] - sh, p[1], p[2])
    f.draw_soil(pg, t, sh, lambda tt: keeper("digger", tt)[:2])
    gx, gy, _ = keeper("lantern", t)
    bu.draw_level(pg, t, sh, (gx, gy))
    XW.apply_light(pg, t)
    f.draw_lantern(pg, t, sh, lit_only=True)
    s.draw_lights(pg, t, sh, (gx, gy))
    f.draw_flare(pg, t, sh, (gx, gy))
    out = Pg.final()
    if ui:
        with XW.raw(out):
            bubbles(out, t)
            overlays(out, t)
    return out.finish(), ms


# ----------------------------------------------------------------------------------------------- the checks

def things(t, sh):
    """Every loose thing on screen this frame under its one id (storycheck)."""
    from . import storycheck as sc
    P = plan()
    out = {}
    p = plain(t)
    if p is not None:
        x, y, spin, held = p
        if held is None:
            mv = "rolls" if P.ball.away <= t < P.ball.rest_t + 0.2 else ("falls" if P.ball.t0 <= t < P.ball.away + 0.3
                                                                         else None)
            out["Wheels' plain ball"] = sc.Thing(x - sh, y, MC.R0, moves=mv)
        else:
            out["Wheels' plain ball"] = sc.Thing(x - sh, y, MC.R0, held=(held, (x - sh, y)))
    out.update(P.shop.things(t, sh, lambda tt: twigs_hand(tt), hans_tip))
    out.update(P.build.things(t, sh, lambda tt: twigs_hand(tt), hans_tip))
    out.update(P.fin.things(t, sh, lambda tt: keeper("digger", tt)[:2]))
    rt = P.race.things(t, sh, springs_xy, wheels_hand)
    if "Wheels' plain ball" in out:
        rt.pop("Wheels' plain ball", None)
    out.update(rt)
    out.update(RA.rabbit_thing(P.race, t, sh))
    return out


def impacts():
    """{thing id: [t]} real collisions from the physics (a bounce, a pat, a marble off a peg): at these instants a
    velocity really does change at once, so the checks skip the jump rule for that one frame (and count them)."""
    P = plan()
    if getattr(P, "_impacts", None) is None:
        b, r = P.ball, P.race
        n = int((b.away - b.t0) / b.T) + 1
        ts = [b.t0 + i * b.T for i in range(n + 1)] + [b.t0 + i * b.T + b.t_dn for i in range(n + 1)] + list(b.hits)
        ts += [b.rest_t, b.grab[1]]
        ts += [r.test_go + e[0] for e in r.test.events] + [r.test_go, r.w_fetch[0] + 0.7]
        P._impacts = {"Wheels' plain ball": sorted(ts)}
        s = P.shop
        for j, c in enumerate(s.cuts):                             # each cube landing in the basket
            tt = c["fall"]
            while tt < c["fall"] + 1.0 and s.cube(j, tt)[3] == "falls":
                tt += 1 / 240
            P._impacts[f"cube {j}"] = [tt]
        hs = []                                                    # Springs' hops: each take-off and landing
        for H in (P.build.hops_a, P.build.hops_b, P.sp_wait) + tuple(h for c in r.cycles
                                                                     for h in (c["hops"], c["hops_down"])):
            for a_, b_, p0, p1, vy in H.hops:
                hs += [a_, b_]
        P._impacts["Springs"] = sorted(hs)
        held = [h for c in r.cycles for H in (c["hops"], c["hops_down"]) for a_, b_, p0, p1, vy in H.hops
                for h in (a_, b_)]                                 # what rides in his crate hops with him
        P._impacts["Wheels' plain ball"] = sorted(P._impacts["Wheels' plain ball"] + held)
        for i, run in enumerate(r.race.runs):
            P._impacts[f"marble {MC.KINDS[i]}"] = sorted([r.go + e[0] for e in run.events] + [r.go] + held)
    return P._impacts


# ----------------------------------------------------------------------------------------------- the sound

def _music_variant():
    """This episode's own music-box variant (owner 2026-10-30: every episode its own soundtrack): in A, a little
    slower, the curious part early, quiet bars for the narrator. Registered here so the shared music.py is untouched."""
    from . import music
    if "marblerun" not in music.VARIANTS:
        music.VARIANTS["marblerun"] = (9, 92.0, [(music.A, -12), (music.REST, -12), (music.D, -12), (music.B, -12),
                                                 (music.REST, -12), (music.C, -12), (music.A, -12), (music.REST, -12),
                                                 (music.D, -12), (music.REST, -12), (music.B, -12), (music.C, -12)])


PENTA = [57, 59, 61, 64, 66, 69, 71, 73]            # A major pentatonic (two octaves), for the wooden clacks


def soundtrack(path):
    """The music box (the episode's own variant), the Keepers' voices, soft warm sounds for everything that happens
    on screen, and the narrator over it all (the music eases down only while she speaks). -> (wav, stats, track)"""
    from engine.audio import EventTrack
    from . import music
    from .chatter import VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    _music_variant()
    P = plan()
    track = EventTrack(7)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="marblerun")

    def pan_at(t, x):
        cx, z = P.cam(t)
        return max(-0.6, min(0.6, ((x - cx) * z / W) * 1.2))

    for tv, kd, mood in P.voices:
        contour, st, _ = mood_info(mood)
        x = keeper(kd, tv)[0]
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3, pan_at(tv, x))
    b, s, bu, f, r = P.ball, P.shop, P.build, P.fin, P.race
    # 1. the ball: each pat and bounce a soft wooden tock, the roll
    n = int((b.away - b.t0) / b.T) + 1
    for i in range(n + 1):
        tb = b.t0 + i * b.T + b.t_dn
        if tb < b.away + b.t_dn + 0.01:
            track.hit(tb, "pluck", 57, 0.07, pan_at(tb, b.bx))
    for i, th in enumerate(b.hits[1:]):
        track.hit(th, "pluck", 55, 0.08 * (0.75 ** i), pan_at(th, b.pos(th)[0]))
    track.fx(b.roll0[0], "marble_roll", b.roll_t, 0.06, pan_at(b.roll0[0], b.rest_x))
    # 2. the workshop: sawing, the cubes into the basket, the tumbler, the balls out, Glo's flares
    for j, c in enumerate(s.cuts):
        a_, b_ = c["saw"]
        for q in range(6):
            track.fx(a_ + (q + 0.1) * (b_ - a_) / 6, "saw", 0.3, 0.06, pan_at(a_, s.cut))
        track.hit(c["fall"] + 0.25, "clack", PENTA[j % 5], 0.12, pan_at(c["fall"], s.cut))
    track.hit(s.hans["pour"][0] + 0.4, "clack", 55, 0.12, 0.0)
    w = s.wheels
    track.fx(w["drive"][0], "marble_roll", w["drive"][1] - w["drive"][0], 0.08, 0.0)
    for q in range(26):
        tq = w["drive"][0] + 0.3 + q * 0.37
        if tq < w["drive"][1] - 0.3:
            track.hit(tq, "clack", PENTA[(q * 3) % 6] - 12, 0.04, 0.0)
    for i, bb in enumerate(s.balls):
        track.hit(bb["t"] + 0.05, "clack", PENTA[(i + 2) % 6], 0.1, 0.1)
        track.fx(bb["t"] + bb["t_ch"], "marble_roll", bb["t_r"], 0.05, 0.2)
    for a_, b_ in s.colour:
        track.hit(a_ + 0.9, "plink", 69, 0.07, 0.0)
    track.fx(s.lift[0], "rustle", 1.0, 0.05, 0.0)
    # 3. the run: peg taps, dowels, the pulley's creak, the boards landing, the level's ding, the digging
    for name, spot, a_, b_, side, stand in bu.taps:
        for q in range(3):
            tq = a_ + (b_ - a_) * (q + 0.25) / 3
            track.hit(tq, "pluck", 52 + 2 * q, 0.09, pan_at(tq, spot[0]))
    for j, (dx, dy), at, _ in bu.dowel_taps:
        track.hit(at, "pluck", PENTA[j % 6] - 7, 0.08, pan_at(at, dx))
    for H in (bu.hops_a, bu.hops_b, r.cycles[0]["hops"], r.cycles[1]["hops"], r.cycles[0]["hops_down"],
              r.cycles[1]["hops_down"]):
        for a_, b_, p0, p1, vy in H.hops:
            track.fx(a_, "slide", 0.18, 0.03, pan_at(a_, p0[0]))                 # his springs: a soft boing
    for a_, b_ in bu.haul:
        track.fx(a_, "creak", b_ - a_, 0.05, pan_at(a_, MC.RUN))
    for bd in bu.boards:
        track.hit(bd["settle"][0] + 0.7, "wood_thud", 45, 0.14, 0.0)
        track.hit(bd["settle"][1] - 0.05, "wood_thud", 43, 0.12, 0.0)
        track.hit(bd["level"][0] + 1.6, "plink", 76, 0.06, 0.2)
    for a_, b_ in f.strokes:
        track.fx(a_ + 0.35 * (b_ - a_), "sand_scrape", 0.45, 0.07, pan_at(a_, FI.DIG_X))
        track.fx(a_ + 0.9 * (b_ - a_), "sand_thump", 0.2, 0.04, pan_at(a_, FI.HEAP_X))
    track.fx(f.through[0] + 0.5, "sand_patter", 1.4, 0.05, pan_at(f.through[0], MC.TUNNEL_OUT))
    track.hit(f.seat[1] - 0.1, "wood_thud", 41, 0.14, pan_at(f.seat[1], MC.BOX[0]))
    track.hit(f.lamp[1] - 0.3, "plink", 64, 0.08, pan_at(f.lamp[1], FI.LANTERN_X))
    # 4. the test run and the race: wooden clacks off pegs and stops, the rumble of rolling, the gate
    for c in r.cycles:
        track.fx(c["gate"][0], "creak", 0.5, 0.06, pan_at(c["gate"][0], MC.GATE_X))
        track.fx(c["tip"][0] + 0.4, "marble_roll", 0.8, 0.06, pan_at(c["tip"][0], MC.START_X))
    for i, tc in enumerate(r.count):
        track.hit(tc, "plink", (64, 66, 69)[i], 0.07, 0.3)

    def run_sound(t0, run, lane, vel):
        k = 0
        for te, kind, x, y, imp in run.events:
            v = min(1.0, imp / 900.0)
            note = PENTA[k % len(PENTA)] if kind == "peg" else (52 if kind == "stop" else 57)
            if kind != "wood" or v > 0.25:
                track.hit(t0 + te, "clack", note, vel * (0.4 + 0.6 * v), pan_at(t0 + te, x))
            k += 1
        dur = (run.finish_t or run.dur) + 1.0
        track.fx(t0, "marble_roll", dur, 0.035, pan_at(t0, MC.RUN))
    run_sound(r.test_go, r.test, 0, 0.14)
    for i, run in enumerate(r.race.runs):
        run_sound(r.go, run, i, 0.08)
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
