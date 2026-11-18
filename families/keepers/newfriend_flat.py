"""Forest Keepers ep 12, A New Friend from the Factory, in the flat picture-book look (docs/engines/
forest_keepers_new_friend_flat.md): the approved FK0011 story (Sprout built at the night-shift factory from an oak
log, its very first tree), narrated, the music box all the way.

Stateless: every frame is a pure function of time t (s), so frames render in parallel (experiments/keepers_flat/
ep12.py). The world is newfriend_flat_world.py, the factory line newfriend_flat_line.py, the village beats
newfriend_flat_village.py; the walking kit is flat_motion.py. Three places, joined by act breaks (the page dims and
comes up somewhere else: owner, FK0019: a long trip never plays out as a long walk):

    1  the village at night    Twigs trims a dead branch, Hans holds it; Glo's idea; they set off
    2  the factory hall        the line builds Sprout; Twigs plants the seedling; the orb; Sprout wakes up
    3  home, before dawn       another branch; Digs digs, Sprout plants its acorn and waters it; the little tree

    plan().end                      the timeline
    frame(world, t) -> rgb          one finished 1920x1080 frame
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import TURN_NARROW, Monster, planted_tentacle, reach_tentacle
from families.foundry.style import lighten

from . import illustrate as il
from . import newfriend_flat_line as LN
from . import newfriend_flat_village as VB
from . import newfriend_flat_world as NW
from .flat_motion import Hopper, WaveGait, arm_swing, biped, hans_mood, heading, roll_swing, stance_drop, walk_path
from .storybook import C, oval, rrect

W, H, G, BACK = NW.W, NW.H, NW.G, NW.BACK
FPS = 60
STEP = 1.0 / FPS
K = 0.72
SIX = ["wheels", "springs", "digger", "teeth", "tentacles", "lantern"]
ORDER = SIX + ["sprout"]
NAMES = {"teeth": "Twigs", "wheels": "Wheels", "digger": "Digs", "springs": "Springs", "tentacles": "Hans",
         "lantern": "Glo", "sprout": "Sprout"}
KH = {"wheels": 420, "tentacles": 610, "teeth": 760, "springs": 340, "lantern": 600, "digger": 300, "sprout": 330}
V_WALK = 100.0
EASE = 1.0
WR = 46.0 * K
GLO_Y = G - 40 * K
DIM = (1.3, 0.5, 1.3)               # an act break: the page dims (s), stays dark, comes up again

# ----------------------------------------------------------------------------------------------- narration

HOOK = ("Tonight, the Forest Keepers go back to the night-shift factory. And at the very end, a brand-new Keeper "
        "plants its very first tree.")
LINES = {
    "trim": "Twigs trims the old dead branches, so the oak can grow strong.",
    "none": "But where an old branch comes down, nobody plants anything new.",
    "idea": "Glo has an idea. A new friend... one who plants trees! Off to the night-shift factory.",
    "hall": "The night-shift factory. The machines are humming.",
    "log": "First, a round oak log.",
    "cut": "Cut to just the right size.",
    "turn": "Round and round it goes, until it's shaped like an acorn.",
    "carve": "A scaly cap, and a little round socket.",
    "fit_feet": "Feet,",                  # FIT, one short line per step, each as it happens (fresh agents,
    "fit_arms": "two arms,",              # FK0024 review: one line over 17 s of different work; the face is asleep)
    "fit_face": "and a sleepy little face.",
    "plant": "And Twigs plants a seedling, right on top.",
    "home": "Back home, just before the sun comes up.",
    "trim2": "One more dead branch for Twigs.",
    "dig": "Digs digs a little hole.",
    "acorn": "And Sprout plants its acorn.",
    "water": "A drink of water...",
}
MEET = "This is Sprout, the seventh Forest Keeper."
FINALE = "And there it is: Sprout's very first tree. Goodnight, forest."
SIGNOFF = "What should the Keepers build next? Tell us in the comments."
CARD = ("Sprout", "The seventh Forest Keeper, the gardener")
HOLD_END = 4.5


def _dur(text):
    from .narrator import take
    return take(text)["duration"]


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def ease(t, a, b):
    return smoothstep(_seg(t, a, b))


# ----------------------------------------------------------------------------------------------- places

# beat 1, the village at night: the right-hand dead branch (DEAD2); Twigs under its cut, Hans under its far end
V1 = dict(springs=2200.0, digger=2440.0, lantern=2660.0, teeth=2960.0, tentacles=3420.0, wheels=3800.0)
# the hall: the watching spot on the walkway, Twigs nearest the PLANT station
HALL = dict(teeth=3800.0, digger=4030.0, springs=4260.0, tentacles=4540.0, wheels=4830.0, lantern=4965.0)
ACORN_R = 22.0                      # Sprout's acorn's radius / k: big enough to see it drop in (causecheck
                                    # too_small, after FK0021's tiny acorn); monster.py default is 11
TWIGS_PLANT = 3675.0                # where Twigs stands to plant (his left hand reaches the arm and the cap;
                                    # 25 px clear of Sprout so his hand can come back outside its face)
SPROUT_DOWN = 3610.0                # where Sprout lands hopping off the cart
# beat 3, home: the left-hand branch (DEAD), the planting right of the oak
TWIGS_ASIDE_1 = 80.0                   # Twigs' step left, onto the trunk, as Hans lowers the first branch (its cut end
#                                       lands 140 px clear of his foot: fresh agent, FK0024 round 16, it was at his ankle)
TWIGS_ASIDE = 160.0                    # Twigs' step out from under the second branch as Hans lowers it
TWIGS_PAST = 160.0                     # ...and at home, where he waits right of the oak while it comes down
V3 = dict(teeth=2710.0, tentacles=2380.0, digger=VB.Planting.HOLE, sprout=VB.Planting.SPROUT_WAIT, lantern=4130.0,
          wheels=4440.0, springs=4620.0)   # (Wheels and Springs wholly outside the planting close shots)


class Plan:
    """The timeline, beat by beat."""

    def __init__(self):
        LN.SEED_FROM_ARM = True
        self.hook = 1.6
        # ---- 1. the village at night
        self.tags = (0.4, 3.3)                     # gone before the camera starts moving in (fresh agent, FK0024
                                                   # round 7: placed with the t=6 camera, they floated off)
        self.branch1 = VB.Branch(NW.DEAD2, self.hook + _dur(HOOK) - 1.0, +1, hold=1.8)   # (Twigs steps out first)
        b1 = self.branch1
        self.say_trim = self.hook + _dur(HOOK) + 0.5
        self.say_none = max(b1.end + 0.2, self.say_trim + _dur(LINES["trim"]) + 0.6)
        self.idea = self.say_none + _dur(LINES["none"]) + 0.4
        self.say_idea = self.idea + 0.6
        self.go1 = self.say_idea + _dur(LINES["idea"]) - 2.0
        self.dim1 = (self.go1 + 3.0, self.go1 + 3.0 + sum(DIM))
        # ---- 2. the factory hall
        h0 = self.dim1[0] + DIM[0] + DIM[1]                     # the hall comes up from here
        self.hall_t0 = h0 - DIM[1] / 2                          # the scene switches in the dark
        self.say_hall = h0 + 0.8
        self.line = LN.Line(h0 + 8.0)
        L = self.line
        self.say_log = L.hoist["come"][0] + 2.6         # as the log comes into view
        self.say_cut = L.cut["saw"][0] - 0.2              # as the disc meets the log (fresh agent, FK0024 round 13)
        self.say_turn = L.turn["run"][0]
        # "A scaly cap" as the chisel finishes it, "socket" (2.4 s in) as the drill bores it - not on the chisel's
        # seed-hole poke (fresh agent, FK0024 round 15: the word landed on the poke and the top hole read as the socket)
        self.say_carve = L.carve["drill"][0] + 0.3 - 2.4
        self.say_fit_feet = L.fit[0]["press"][0] - 0.2    # as the legs go on
        self.say_fit_arms = L.fit[1]["press"][0] - 0.2    # as the first arm goes on
        self.say_fit_face = L.paint["paint"][0] + 0.2     # as the brush starts on the face
        p0, p1 = L.at["plant"]
        # PLANT: Twigs steps over to the cart, takes the seedling from the arm, plants it in the cap, steps back
        self.tw_step = (p0 + 0.4, p0 + 1.9)
        self.tw_take = (L.plant["offer"][1] + 0.3, L.plant["offer"][1] + 1.7)       # hand to the seedling
        self.tw_grab = self.tw_take[1] + 0.2
        self.tw_lift = (self.tw_grab + 0.2, self.tw_grab + 2.2)                      # over to the cap
        self.tw_set = (self.tw_lift[1], self.tw_lift[1] + 0.9)                       # down into the hole
        self.tw_let = self.tw_set[1] + 0.2
        self.tw_back = (self.tw_let + 0.2, self.tw_let + 1.4)
        self.tw_home = (self.tw_back[1] + 0.2, self.tw_back[1] + 1.7)
        self.say_plant = self.tw_set[0] - 1.4          # as he lifts it over and sets it in
        # the seventh orb, the wake, the cheer, the name card
        o0 = self.tw_home[0]
        self.orb = ((o0, o0 + 3.0), (o0 + 3.2, o0 + 5.2), o0 + 5.4)              # come, lower, in
        self.flash = (self.orb[2], self.orb[2] + 1.2)
        self.wake = (self.orb[2] + 0.4, self.orb[2] + 2.6)
        self.blink = self.wake[1] + 0.3
        self.wave = (self.wake[1] + 0.8, self.wake[1] + 3.4)
        self.zoom_out = (self.wake[1] + 0.6, self.wake[1] + 9.6)       # close on Sprout, back out to all seven
        self.cheer = (self.zoom_out[1] + 0.2, self.zoom_out[1] + 3.4)    # once they are all in the frame
        self.card = (self.wave[0] + 0.4, self.wave[0] + 0.4 + max(7.0, _dur(MEET) + 2.5))
        self.say_meet = self.card[0] + 0.4
        self.hop_down = (max(self.card[1], self.cheer[1]) + 0.4, max(self.card[1], self.cheer[1]) + 1.2)
        self.go2 = self.hop_down[1] + 1.2
        self.dim2 = (self.go2 + 2.5, self.go2 + 2.5 + sum(DIM))
        # ---- 3. home, before dawn
        m0 = self.dim2[0] + DIM[0] + DIM[1]
        self.home_t0 = m0 - DIM[1] / 2
        self.say_home = m0 + 0.6
        self.branch2 = VB.Branch(NW.DEAD, self.say_home + _dur(LINES["home"]) + 0.6, -1, hold=3.0)
        b2 = self.branch2
        self.say_trim2 = b2.t0 + 0.2
        self.plant = VB.Planting(b2.end + 6.5)              # (time for the camera to ease back out of the cut)
        pl = self.plant
        self.say_dig = pl.strokes[0][0] + 0.2
        self.say_acorn = pl.drop - 1.3              # ("...plants its acorn" as it lets go)
        self.say_water = pl.water[0] - 0.2
        self.finale = pl.grow[1] + 0.6
        self.sign = (self.finale + _dur(FINALE) + HOLD_END, None)
        self.sign = (self.sign[0], self.sign[0] + 1.0)
        # all of them in the wide shot, a cheer for the new tree: Hans waves two legs as arms (fresh agent, FK0024
        # round 14: the ending just stood still, Hans out of the frame)
        self.cheer2 = (self.sign[0] - 0.2, self.sign[0] + 3.0)
        self.signoff = max(self.sign[1] + 0.3, self.cheer2[1] + 0.2)
        self.end = self.signoff + _dur(SIGNOFF) + 2.5
        # ---- the moves, the camera, the light
        self.paths = self._paths()
        self.glo_keys = [(0.0, 0.0)]
        self.cam = self._cam()
        # each place has its own walks (the act breaks): gaits and headings are built per place, so nothing
        # carries a step or a turn across a break
        self.turns = {kd: _ByPlace(self, [heading(f) if f else (lambda t: 0.0) for f in self.paths[kd].fns()])
                      for kd in ORDER}
        narrow = lambda kd, f=1.0: (lambda t: 1.0 - TURN_NARROW * f * abs(self.turns[kd](t)))   # noqa: E731
        self.gaits = {kd: _GaitByPlace(self, [biped(kd, f, G, K, spread=narrow(kd)) if f else None
                                              for f in self.paths[kd].fns()]) for kd in ("teeth", "digger", "sprout")}
        self.gaits["tentacles"] = _GaitByPlace(self, [WaveGait(G, K, f, spread=narrow("tentacles", 0.5))
                                                      for f in self.paths["tentacles"].fns()])
        self.hopper = _GaitByPlace(self, [Hopper(f, G, K) for f in self.paths["springs"].fns()])
        self.voices = []
        self.voices = voices(self)

    # ----- where everyone is

    def place(self, t):
        """0 the village at night, 1 the hall, 2 home."""
        if t < self.hall_t0:
            return 0
        if t < self.home_t0:
            return 1
        return 2

    def _paths(self):
        """Walks along x [(t, x)] for each Keeper, within each place (the act breaks reset them: a new place)."""
        out = {}
        g1 = self.go1
        L = self.line
        pl = self.plant
        for kd in ORDER:
            keys = []
            # 1. the village: they stand, then set off right (Wheels, Hans, Glo first; Twigs, Digs, Springs after)
            if kd != "sprout":
                # (Twigs sets off before Glo, at Glo's pace: he's nearer Glo since stepping aside for the branch)
                lag = {"wheels": 0.0, "tentacles": 0.3, "teeth": 0.5, "lantern": 1.2, "digger": 1.6,
                       "springs": 2.0}[kd]
                v = {"wheels": 130.0, "lantern": V_WALK, "springs": 110.0}.get(kd, V_WALK)
                x1 = V1[kd]
                if kd == "teeth":               # after the cut, a step left, out from under the branch coming down
                    b1 = self.branch1           # (fresh agent, FK0024 round 9: it came down behind him, hidden)
                    keys += [(0.0, x1), (b1.cut + 0.9, x1)]
                    x1 -= TWIGS_ASIDE_1
                    keys += [(b1.cut + 2.4, x1)]
                else:
                    keys += [(0.0, x1)]
                keys += [(g1 + lag, x1), (g1 + lag + 6.0, x1 + v * 5.0)]
            out[kd] = keys
        self._keys = out
        return {kd: _Paths(self, kd) for kd in ORDER}

    def _cam(self):
        b1, b2, L, pl = self.branch1, self.branch2, self.line, self.plant
        # in close for Twigs' cut and Hans laying the branch down (fresh agent, FK0024 round 6: at zoom 1 the blade
        # was too small to read), back out before they set off
        # (wide: a touch further out and right, so Wheels, parked right of the stump, is all in - fresh agent, FK0024
        # round 11: he stood in front of the stump)
        VX, VZ = 3060.0, 0.94
        keys1 = [(0.0, VX, VZ), (b1.t0 - 5.4, VX, VZ), (b1.t0 + 0.1, 3100.0, 1.7), (b1.end, 3100.0, 1.7),
                 (b1.end + 5.0, VX, VZ), (self.go1 + 0.6, VX, VZ),
                 (self.dim1[1], VX + 130.0 * (self.dim1[1] - self.go1 - 0.6), VZ)]
        h0 = self.hall_t0
        st = NW.STATION
        # close on each station's work (fresh agent, FK0024 review: the build was too small to see at zoom 1); the
        # moves between stations stay under the camera's speed limit; out for the cheer, so all seven are in it
        OFF = {"hoist": 100.0, "cut": 120.0, "turn": 100.0, "carve": 80.0, "fit": -80.0, "plant": 40.0}
        Z = {"hoist": 1.3, "cut": 1.3, "turn": 1.8, "carve": 2.0, "fit": 2.0, "plant": 1.4}
        nxt = {"hoist": "cut", "cut": "turn", "turn": "carve", "carve": "fit", "fit": "plant"}
        hk = [(h0, 3460.0, 0.6), (h0 + 1.5, 3460.0, 0.6),
              (L.hoist["come"][1] + 1.0, st["hoist"] + 260.0, 1.0),
              (L.hoist["lower"][1], st["hoist"] + OFF["hoist"], 1.3)]
        for name in ("hoist", "cut", "turn", "carve", "fit"):
            a, b = L.at[name]
            hk.append((b, st[name] + OFF[name], Z[name]))
            n2 = nxt[name]
            a2 = L.at[n2][0]
            if Z[n2] > Z[name] + 0.2:                  # arrive at the old zoom, then close in (one move at a time)
                hk.append((a2 + 0.3, st[n2] + OFF[n2], Z[name]))
                hk.append((a2 + 3.6, st[n2] + OFF[n2], Z[n2]))
            else:
                hk.append((a2 + (3.5 if n2 == "plant" else 0.3), st[n2] + OFF[n2], Z[n2]))
        # the seventh orb going in and Sprout waking: close on its belly and face (fresh agent, FK0024 review: too
        # small at 1.4), then slowly back out to all seven for the cheer
        hk += [(self.orb[0][0] - 1.0, st["plant"] + OFF["plant"], 1.4), (self.orb[1][0], st["plant"] + 40.0, 1.8),
               (self.zoom_out[0], st["plant"] + 40.0, 1.8), (self.zoom_out[1], st["plant"] + 470.0, 0.85),
               (self.go2, st["plant"] + 470.0, 0.85), (self.dim2[1], st["plant"] + 650.0, 0.85)]
        m0 = self.home_t0
        p_end = pl.pats[-1][1]
        HO = VB.Planting.HOLE
        # in a little for the second cut too (fresh agent, FK0024 round 6: the blade was hard to read at zoom 1)
        mk = [(m0, 2700.0, 1.0), (b2.t0 - 2.6, 2700.0, 1.0), (b2.t0 + 0.2, 2760.0, 1.3), (b2.end, 2760.0, 1.3),
              (pl.dig_t[0], HO - 10.0, 1.0),
              # (Digs aside, Sprout, the stump and Glo all in the close shot; then the watering with Digs by the oak
              # and Twigs / Hans either fully in or fully out: fresh agent, FK0024 round 12)
              # slowly in closer while he digs, for the acorn going in (Digs aside and Sprout both wholly in, Glo
              # out), a touch back out for the fill (fresh agent, FK0024 round 14: the drop was too small)
              (pl.dig_t[0] + 5.6, HO + 170.0, 1.6), (pl.drop_arm[0], HO - 65.0, 2.13),
              (pl.drop_land + 0.6, HO - 65.0, 2.13), (pl.fill_a[0], HO - 13.0, 1.91), (pl.fill_b[1], HO - 13.0, 1.91),
              (pl.hop[1], HO - 80.0, 1.15),       # (Twigs wholly in at the left, Glo at the right: round 16)
              (self.finale + 2.6, HO - 80.0, 1.15),
              (self.sign[0] - 0.4, 3475.0, 0.76), (self.end, 3475.0, 0.76)]
        return _CamSet(keys1, hk, mk, self)

    def shift(self, t):
        return self.cam(t)[0] - W / 2

    def narration(self):
        return [(self.hook, HOOK), (self.say_trim, LINES["trim"]), (self.say_none, LINES["none"]),
                (self.say_idea, LINES["idea"]), (self.say_hall, LINES["hall"]), (self.say_log, LINES["log"]),
                (self.say_cut, LINES["cut"]), (self.say_turn, LINES["turn"]), (self.say_carve, LINES["carve"]),
                (self.say_fit_feet, LINES["fit_feet"]), (self.say_fit_arms, LINES["fit_arms"]),
                (self.say_fit_face, LINES["fit_face"]), (self.say_plant, LINES["plant"]), (self.say_meet, MEET),
                (self.say_home, LINES["home"]), (self.say_trim2, LINES["trim2"]), (self.say_dig, LINES["dig"]),
                (self.say_acorn, LINES["acorn"]), (self.say_water, LINES["water"]), (self.finale, FINALE),
                (self.signoff, SIGNOFF)]

    def dim(self, t):
        """0..1 how dark the page is (an act break)."""
        out = 0.0
        for a, _ in (self.dim1, self.dim2):
            d0, d1, d2 = DIM
            if a <= t < a + d0 + d1 + d2:
                if t < a + d0:
                    out = smoothstep((t - a) / d0)
                elif t < a + d0 + d1:
                    out = 1.0
                else:
                    out = 1.0 - smoothstep((t - a - d0 - d1) / d2)
        return out


class _ByPlace:
    """f(t) from one function per place."""

    def __init__(self, P, fns):
        self.P, self.fns = P, fns

    def __call__(self, t):
        return self.fns[self.P.place(t)](t)


class _GaitByPlace:
    """A gait (biped, WaveGait, Hopper) per place: every method goes to the one for t's place."""

    def __init__(self, P, gaits):
        self.P, self.gaits = P, gaits
        self.home = next(g for g in gaits if g is not None).home if hasattr(gaits[-1], "home") else None

    def _g(self, t):
        return self.gaits[self.P.place(t)] or self.gaits[-1]

    def body_x(self, t):
        return self._g(t).body_x(t)

    def feet(self, t):
        return self._g(t).feet(t)

    def foot(self, i, t):
        return self._g(t).foot(i, t)

    def bob(self, t):
        return self._g(t).bob(t)

    def state(self, t):
        return self._g(t).state(t)

    def __getattr__(self, k):
        return getattr(self.gaits[-1], k)


class _CamSet:
    """The camera, one key list per place."""

    def __init__(self, k1, k2, k3, P):
        self.cams = (NW.Cam(k1), NW.Cam(k2), NW.Cam(k3))
        self.P = P

    def __call__(self, t):
        return self.cams[self.P.place(t)](t)


class _Paths:
    """x(t) for one Keeper: its walk within each place (the hall and home have their own spots and moves)."""

    def __init__(self, P, kd):
        self.P, self.kd = P, kd
        self.v1 = walk_path(sorted(set(P._keys[kd])), EASE) if P._keys[kd] else None
        self.v2 = walk_path(self._hall_keys(), EASE)
        self.v3 = walk_path(self._home_keys(), EASE)

    def _hall_keys(self):
        P, kd = self.P, self.kd
        if kd == "sprout":
            return [(0.0, SPROUT_DOWN), (P.go2 + 2.6, SPROUT_DOWN), (P.go2 + 8.6, SPROUT_DOWN + 90.0 * 5.0)]
        x = HALL[kd]
        keys = [(0.0, x)]
        if kd == "teeth":
            keys += [(P.tw_step[0], x), (P.tw_step[1], TWIGS_PLANT), (P.tw_home[0], TWIGS_PLANT), (P.tw_home[1], x)]
        lag = {"lantern": 0.0, "wheels": 0.2, "tentacles": 0.5, "springs": 0.9, "digger": 1.3, "teeth": 1.7}[kd]
        v = {"wheels": 130.0, "lantern": 120.0, "springs": 110.0}.get(kd, V_WALK)
        end = x + v * 5.0
        if kd == "lantern":                     # Glo starts in front of the doorway: he floats into it, not past it
            end = min(end, NW.DOOR[1] - 80.0)
        keys += [(P.go2 + lag, x), (P.go2 + lag + 6.0, end)]
        return sorted(set(keys))

    def _home_keys(self):
        P, kd = self.P, self.kd
        pl = P.plant
        x = V3[kd]
        keys = [(0.0, x)]
        if kd == "digger":                      # over the spot to dig; aside for the drop; back to fill; away
            D = VB.Planting.DIGS
            keys += [(pl.digs_out[0], x), (pl.digs_out[1], D), (pl.digs_in[0], D), (pl.digs_in[1], x),
                     (pl.aside[0], x), (pl.aside[1], D), (pl.digs_back[0], D), (pl.digs_back[1], VB.Planting.DIGS_BACK)]
        if kd == "teeth":                       # after the cut, right past the trunk, clear of the stub and the branch
            b2 = P.branch2                      # coming down (fresh agent, FK0024 round 10: he stood in front of the
            xr = NW.OAK_X + TWIGS_PAST          # trunk and hid both); then back left in two short bursts, a look at
            keys += [(b2.cut + 0.9, x), (b2.cut + 3.7, xr),          # the branch between: room for Digs later
                     (b2.end + 1.0, xr), (b2.end + 2.6, NW.OAK_X - 80.0), (b2.end + 3.4, NW.OAK_X - 80.0), (b2.end + 5.6, x - 40.0)]
            # (x - 40: clear of Hans' raised tentacles at the cheers - fresh agent, FK0024 round 15: at x - 140 one
            # curled across Twigs' face)
        if kd == "sprout":                      # waits clear of Digs; up to the hole to drop its acorn; back; up
            S = VB.Planting.SPROUT              # to the mound's edge with the can, and over it
            keys += [(pl.sprout_in[0], x), (pl.sprout_in[1], S), (pl.sprout_out[0], S), (pl.sprout_out[1], x),
                     (pl.sprout_up[0], x), (pl.sprout_up[1], VB.Planting.SPROUT_EDGE + 40.0),
                     # round the back: a step back (and a little in), along behind the mound, a step forward, the
                     # feet clear of the soil patch all the way (fresh agent, FK0024 round 12: they crossed its end)
                     (pl.hop[0], VB.Planting.SPROUT_EDGE + 40.0)]
            # three bounces round the front of the mound (fresh agent, FK0024 round 16: a 4.5 s walk across it)
            PL, e0 = VB.Planting, VB.Planting.SPROUT_EDGE + 40.0
            keys += [(pl.hop[0] + i * PL.HOP_DUR, e0 + (PL.SPROUT_WATER - e0) * i / PL.HOPS)
                     for i in range(1, PL.HOPS + 1)]
            keys += [
                     (pl.step_back[0], VB.Planting.SPROUT_WATER), (pl.step_back[1], VB.Planting.SPROUT_BACK)]
        return keys

    def fns(self):
        return [self.v1, self.v2, self.v3]

    def __call__(self, t):
        p = self.P.place(t)
        if p == 0:
            return self.v1(t) if self.v1 else -9999.0
        return (self.v2 if p == 1 else self.v3)(t)


PLAN = None


def plan():
    global PLAN
    if PLAN is None:
        PLAN = Plan()
    return PLAN


# ----------------------------------------------------------------------------------------------- voices

VOICE_DUR_S = 0.6
BUBBLE_R = 50.0
CUSTOM = {"idea": ("up", 2, "acorn")}


def mood_info(mood):
    from .chatter import MOODS
    return CUSTOM.get(mood, MOODS.get(mood))


def voices(P):
    b1, L, b2, pl = P.branch1, P.line, P.branch2, P.plant
    ev = [(b1.cut + 0.2, "teeth", "mm"), (b1.let_go[1], "tentacles", "hehe"), (b1.cut + 1.0, "springs", "ooh"),
          (P.idea, "lantern", "idea"), (P.idea + 1.8, "wheels", "ooh"), (P.go1 + 0.3, "springs", "wee")]
    ev += [(P.hall_t0 + 1.8, "springs", "ooh"), (P.hall_t0 + 2.6, "wheels", "ooh"),
           (L.hoist["lower"][1], "digger", "ooh"), (L.hoist2["lift"][1], "springs", "hehe"),
           (L.turn["run"][0] + 3.0, "wheels", "wee"), (L.turn["run"][1], "lantern", "ooh"),
           (L.carve["drill"][1], "digger", "hm"), (L.carve["brush"][1], "tentacles", "mm"),
           (L.fit[0]["press"][1], "springs", "ooh"), (L.fit[2]["press"][1], "wheels", "yay"),
           (L.paint["paint"][1], "lantern", "aww"), (P.tw_let + 0.3, "teeth", "mm"),
           (P.orb[2] + 0.2, "springs", "ooh"), (P.blink + 0.4, "sprout", "q"), (P.cheer[0], "wheels", "yay"),
           (P.cheer[0] + 0.5, "springs", "yay"), (P.cheer[0] + 1.0, "tentacles", "yay"),
           (P.cheer[0] + 1.6, "digger", "yay"), (P.cheer[0] + 2.2, "sprout", "hehe"),
           (P.go2 + 0.3, "sprout", "wee")]
    ev += [(b2.cut + 0.2, "teeth", "mm"), (b2.let_go[1], "tentacles", "mm"),
           (pl.strokes[2][0], "digger", "huff"), (pl.strokes[-1][1], "digger", "hehe"),
           (pl.drop_land + 0.3, "sprout", "hehe"), (pl.pats[-1][1], "digger", "mm"),
           (pl.can_take[1] + 0.2, "sprout", "hm"), (pl.grow[1] - 0.6, "sprout", "ooh"),
           (pl.grow[1] + 0.2, "springs", "yay"), (pl.grow[1] + 0.8, "wheels", "aww"),
           (P.cheer2[0] + 0.2, "tentacles", "yay"), (P.cheer2[0] + 0.8, "wheels", "yay"),
           (P.cheer2[0] + 1.4, "digger", "yay"), (P.cheer2[0] + 2.0, "sprout", "hehe")]
    lines = [(t0, t0 + _dur(tx)) for t0, tx in P.narration()]
    keep = ("idea",)
    ev = [e for e in sorted(ev) if e[2] in keep or not any(a - 0.7 <= e[0] <= b_ + 0.7 for a, b_ in lines)]
    def seen(e):
        tv, kd, _ = e
        x = P.line.sprout(tv)[0] if (kd == "sprout" and P.place(tv) == 1) else P.paths[kd](tv)
        for u in (tv, tv + VOICE_DUR_S):
            cx, z = P.cam(u)
            if abs(x - cx) > W / (2 * z) - 70.0:
                return False
        return True
    ev = [e for e in ev if seen(e)]
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


# ----------------------------------------------------------------------------------------------- arms (Twigs, Wheels)

UNFLIP = {"teeth": (0.4, lambda x, y, sx: (x + sx * 82 * K, y - 340 * K)),
          "wheels": (0.5, lambda x, y, sx: (x + sx * 100 * K, y - 210 * K + 10 * K))}
UNFLIP_BAND = 9.0
REST_ARM = {"teeth": (0.93, 0.16, 0.42), "wheels": (0.9, 0.6, 0.4)}


def _arm_len(kd):
    from families.foundry.products.monster import TWIGS_FORE, TWIGS_UPPER, WHEELS_FORE, WHEELS_UPPER
    return ((TWIGS_UPPER + TWIGS_FORE) if kd == "teeth" else (WHEELS_UPPER + WHEELS_FORE)) * K


def unflip(kd, x, y, arm_to, sh):
    """arm_to targets (screen) eased out to a straight arm near the elbow's change-over line (marble_flat)."""
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
        band = UNFLIP_BAND * (1.8 if kd == "wheels" else 1.6)
        if diff < band and d < L:
            w = smoothstep(1 - diff / band)
            d2 = d + (L - d) * w
            tx, ty = sxw + dx / d * d2 - sh, syw + dy / d * d2
        out[sx] = (tx, ty)
    return out


def _rest_hand(kd, x, y, sx, swing=0.0, h=0.0):
    reach, o, amp = REST_ARM[kd]
    L = _arm_len(kd) * reach
    ang = sx * o * (1 - 0.6 * abs(h)) + h * swing * sx * amp
    shx, shy = UNFLIP[kd][1](x, y, sx)
    return shx + math.sin(ang) * L, shy + math.cos(ang) * L


def rest_arms(kd, x, y, t, a):
    P = plan()
    sh = P.shift(t)
    out = dict(a.get("arm_to") or {})
    h = max(-1.0, min(1.0, a.get("legs_turn", 0.0) or 0.0))
    for sx in (-1, 1):
        if sx in out:
            continue
        hx, hy = _rest_hand(kd, x, y, sx, a.get("arm_swing") or 0.0, h)
        out[sx] = (hx - sh, hy)
    return out


# ----------------------------------------------------------------------------------------------- the Keepers

def keeper(kd, t):
    """(world x, y, monster attrs) of Keeper kd at time t (None for Sprout before it exists)."""
    P = plan()
    r = _keeper(kd, t)
    if r is None:
        return None
    x, y, a = r
    a.setdefault("legs_turn", P.turns[kd](t))
    a["turn"] = a.get("turn", a["legs_turn"] * (1 - a.pop("face_us", 0.0)))
    if P.voices and a.get("alive", 1.0) >= 1.0:
        m, look, hop = talking(P, kd, t)
        if m > 0 or look > 0:
            a = dict(a, talk=m, attend=max(a.get("attend", 0.0), look), turn=a["turn"] * (1 - look))
            if kd not in ("teeth", "digger", "tentacles", "sprout"):
                y -= hop
    if kd in UNFLIP:
        a["arm_to"] = unflip(kd, x, y, rest_arms(kd, x, y, t, a), P.shift(t))
    return x, y, a


def watching(P, t, kd, x):
    """In the hall the watchers turn a little towards the line (left); at the orb they look at Sprout."""
    if P.place(t) != 1 or kd == "sprout":
        return None
    return -0.45


def arc_reach(shoulder, p0, p1, u):
    """A hand moving from p0 to p1 (world) the way an arm swings: round the shoulder (angle and reach eased
    separately, the short way round), never cutting in close to it, where the elbow would swing wildly."""
    a0 = math.atan2(p0[1] - shoulder[1], p0[0] - shoulder[0])
    a1 = math.atan2(p1[1] - shoulder[1], p1[0] - shoulder[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    r0, r1 = math.dist(shoulder, p0), math.dist(shoulder, p1)
    a = a0 + da * u
    r = r0 + (r1 - r0) * u
    return shoulder[0] + math.cos(a) * r, shoulder[1] + math.sin(a) * r


def polar_path(shoulder, pts, u):
    """A hand moving through waypoints round the shoulder, eased per leg; a waypoint is a world point or
    (angle in degrees, reach px). Twigs' reach for the seedling comes up close in, past Sprout's face, never across it."""
    pol = []
    for q in pts:
        if q[0] > 1000:                                    # a world point (the hall's x is in the thousands)
            pol.append((math.degrees(math.atan2(q[1] - shoulder[1], q[0] - shoulder[0])),
                        math.dist(shoulder, q)))
        else:
            pol.append((float(q[0]), float(q[1])))
    for i in range(1, len(pol)):                           # unwrap: each leg the short way round
        a = pol[i][0]
        while a - pol[i - 1][0] > 180:
            a -= 360
        while a - pol[i - 1][0] < -180:
            a += 360
        pol[i] = (a, pol[i][1])
    # one smooth move along the whole path (by distance travelled), never a stop at each waypoint
    legs = [abs(b[1] - a[1]) + math.radians(abs(b[0] - a[0])) * (a[1] + b[1]) / 2 for a, b in zip(pol, pol[1:])]
    want = u * (sum(legs) or 1.0)
    k = 0
    while k < len(legs) - 1 and want > legs[k]:
        want -= legs[k]
        k += 1
    v = min(1.0, want / (legs[k] or 1.0))
    a = pol[k][0] + (pol[k + 1][0] - pol[k][0]) * v
    r = pol[k][1] + (pol[k + 1][1] - pol[k][1]) * v
    return shoulder[0] + math.cos(math.radians(a)) * r, shoulder[1] + math.sin(math.radians(a)) * r


def _arcify(P, t, x, side, hand, windows):
    """Within a reach / return window, put the hand on the arc between the window's end points."""
    for a, b, p0f, p1f in windows:
        if a <= t < b:
            sh_ = UNFLIP["teeth"][1](x, G, side)
            return arc_reach(sh_, p0f(), p1f(), smoothstep(_seg(t, a, b)))
    return hand


STEM = -14.0                         # Twigs holds the seedling this far up from its root ball (up its stem)


_BLADE_FIX = {}
_BLADE_DIR = {}


def _twigs_blade(t, side):
    """Twigs' pruning blade on that side as drawn (world): (sheath mouth, tip)."""
    x, y, a = keeper("teeth", t)
    sh = plan().shift(t)                    # arm targets are screen px: measure on screen, give back world px
    m = Monster("teeth", k=K)
    m.x, m.y, m.newlook = x - sh, y, True
    for k_, v_ in a.items():
        setattr(m, k_, v_)
    m.draw(_NullCanvas(), t, il.Glow())
    _, el, hd = m.arm_len[side]
    ux, uy, nx, ny = m._blade_frame(hd, el, side)
    out = (6 + 74 * smoothstep(m._blade(side))) * K
    # the middle of the blade as monster.py draws it (its back 0.4 w in, its toothed edge 0.6 w out, curving 8 k
    # out toward the tip), not the sheath line (fresh agent, FK0024 round 13: the notch sat 15-35 px off the blade)
    c0, c1 = 0.1 * 13 * K, (0.1 * 13 + 8) * K
    return ((hd[0] + sh + nx * (13 * K + c0) + ux * 6 * K, hd[1] + ny * (13 * K + c0) + uy * 6 * K),
            (hd[0] + sh + nx * (13 * K + c1) + ux * out, hd[1] + ny * (13 * K + c1) + uy * out))


def _nearest(seg, p):
    (ax, ay), (bx, by) = seg
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    u = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return ax + dx * u, ay + dy * u


BLADE_AT = 30.0                     # px out along Twigs' blade (from the sheath) that saws the cut: his fist
#                                     well below it (fresh agent, FK0024 round 10: at 24 the fist hid the notch),
#                                     and still short of the tip when the blade slides in on a stroke (at 46 the
#                                     tip pulled back past the cut: storycheck effect_off_tool 19 px; round 13:
#                                     at 40 the tip only reached the branch's middle - 30 crosses it)


def blade_fix(P, br, side):
    """How far Twigs' hand moves from the branch's 'hand here' spot so that his blade's edge crosses the branch
    right at the cut point, where the branch then breaks (owner, FK0021 review: the cut is where the blade is).
    Found once per branch, from the blade as drawn at the start of the sawing."""
    key = id(br)
    if key not in _BLADE_FIX:
        _BLADE_FIX[key] = (0.0, 0.0)
        for _ in range(14):
            # the point BLADE_AT out along the blade from its sheath goes on the cut, so his fist sits clear of it
            # (fresh agent, FK0024 round 6: the fist covered the cut)
            (ax, ay), (bx, by) = _twigs_blade(br.saw[0], side)
            L_ = math.hypot(bx - ax, by - ay) or 1.0
            nq = (ax + (bx - ax) * BLADE_AT / L_, ay + (by - ay) * BLADE_AT / L_)
            fx, fy = _BLADE_FIX[key]
            fx, fy = fx + br.q[0] - nq[0], fy + br.q[1] - nq[1]
            d = math.hypot(fx, fy)
            if d > 50.0:                    # never more than a small shift of the hand
                fx, fy = fx * 50.0 / d, fy * 50.0 / d
            _BLADE_FIX[key] = (fx, fy)
        (ax, ay), (bx, by) = _twigs_blade(br.saw[0], side)
        L = math.hypot(bx - ax, by - ay) or 1.0
        _BLADE_DIR[key] = ((bx - ax) / L, (by - ay) / L)
    return _BLADE_FIX[key]


class _NullCanvas:
    """A canvas that draws nothing (for measuring a Monster's limbs)."""
    flat_look, eye_scale, glowing = True, 1.15, False

    def __init__(self):
        from families.foundry.products.monster import ORB
        self.iris_col = ORB

    def __getattr__(self, k):
        return lambda *a, **kw: None


def twigs_hands(P, t, x):
    """Twigs' working hand targets (world) {side: (x, y)}, the blade 0..1, grip 0..1."""
    place = P.place(t)
    if place == 0 or place == 2:
        br = P.branch1 if place == 0 else P.branch2
        side = br.hand                                          # (VB.Branch: which hand saws)
        rest = _rest_hand("teeth", x, G, side)
        r = br.twigs_hand(t, rest)
        if r is not None:
            hd, blade = r
            fx, fy = blade_fix(P, br, side)
            u = 1.0 if t >= br.reach[1] and t < br.back[0] else (
                ease(t, *br.reach) if t < br.reach[1] else 1.0 - ease(t, *br.back))
            hd = (hd[0] + fx * u, hd[1] + fy * u)
            at = br.twigs_hand(br.reach[1], rest)[0]
            at = (at[0] + fx, at[1] + fy)
            bu = _BLADE_DIR.get(id(br))                       # (None only while blade_fix measures it)
            if bu is not None and br.saw[0] <= t < br.saw[1]:  # each stroke slides along the blade itself, so it
                ph = math.pi * 2 * (t - br.saw[0]) / br.STROKE
                push = math.sin(ph) * 5.0
                hd = (at[0] + bu[0] * push, at[1] + bu[1] * push)
                # and the blade itself saws: it slides in and out of its sheath along its own line, so it keeps
                # crossing the branch right at the cut (fresh agent, FK0024 round 6: the blade barely moved; a
                # bigger hand stroke turned his forearm and the blade missed the cut by 14 px)
                blade *= 0.85 + 0.15 * math.cos(ph)
            hd = _arcify(P, t, x, side, hd, [(br.reach[0], br.reach[1], lambda: rest, lambda: at),
                                             (br.back[0], br.back[1], lambda: at, lambda: rest)])
            return {side: hd}, blade, 0.3
        return {}, 0.0, 0.0
    # the hall: take the seedling from the arm, plant it in the cap
    sh = 0.0
    if P.tw_take[0] - 0.01 <= t < P.tw_home[1]:
        rest = _rest_hand("teeth", x, G, -1)
        tip = seed_world(P, t)
        if t < P.tw_take[1]:
            sh_ = UNFLIP["teeth"][1](x, G, -1)
            # the arm crosses the elbow's change-over line straight (low, by Sprout's hip, below its face), then
            # bends in close and comes up past the face to the seedling (no elbow flip, nothing across the face)
            return {-1: polar_path(sh_, [rest, (118.0, 121.0), (132.0, 118.0), (150.0, 72.0), (195.0, 64.0),
                                         (tip[0], tip[1] + STEM)], ease(t, *P.tw_take))}, 0.0, 0.0
        if t < P.tw_let:
            g = min(1.0, (t - P.tw_take[1]) / 0.3)
            return {-1: (tip[0], tip[1] + STEM)}, 0.0, 0.6 * g
        # back from the cap without crossing Sprout's face (owner, FK0021 review: nothing blocking the action): the
        # hand comes up over the cap and stays raised (held with his shoulder) while he steps back to his place, and
        # comes down to his side only once he is well clear of Sprout
        sh_ = UNFLIP["teeth"][1](x, G, -1)
        hold = (sh_[0] - 45.0, sh_[1] - 62.0)
        if t < P.tw_back[1]:
            tp = seed_anchor(P)
            return {-1: arc_reach(sh_, (tp[0], tp[1] + STEM), hold, ease(t, *P.tw_back))}, 0.0, 0.0
        u = _seg(t, *P.tw_home)
        if u < 0.55:
            return {-1: hold}, 0.0, 0.0
        return {-1: arc_reach(sh_, hold, rest, smoothstep((u - 0.55) / 0.45))}, 0.0, 0.0
    return {}, 0.0, 0.0


def seed_anchor(P):
    """Where the seedling's root ball goes: the hole in Sprout's cap (world), Sprout on the cart at PLANT."""
    return LN.geom(NW.STATION["plant"], LN.CART_TOP)["hole"]


def seed_world(P, t):
    """The seedling's root ball (world): in the PLANT arm, in Twigs' hand, in the cap."""
    L = P.line
    arm = LN.plant_arm_tip(L, t, 0.0)
    arm = (arm[0] + 10.0, arm[1] - 10.0)
    if t < P.tw_grab:
        return arm
    a = seed_anchor(P)
    lifted = (arm[0] + (a[0] - arm[0]) * 0.7, a[1] - 40.0)           # (within Twigs' reach, held up its stem)
    if t < P.tw_lift[1]:
        u = ease(t, *P.tw_lift)
        return arm[0] + (lifted[0] - arm[0]) * u, arm[1] + (lifted[1] - arm[1]) * u
    if t < P.tw_set[1]:
        u = ease(t, *P.tw_set)
        return lifted[0] + (a[0] - lifted[0]) * u, lifted[1] + (a[1] - lifted[1]) * u
    return a


def sprout_state(P, t):
    """(x, y, attrs) of Sprout: on the line (the log -> asleep), awake on the cart, hopping down, walking."""
    place = P.place(t)
    if place == 0:
        return None
    if place == 2:
        return _sprout_home(P, t)
    L = P.line
    if t < P.hop_down[0]:
        x, y, a = L.sprout(t)
        a.update(acorn=True)
        # the seedling: in the arm / in Twigs' hand (its own part, shifted), planted
        if L.at["plant"][0] <= t:
            sw = seed_world(P, t)
            an = LN.geom(x, y)["hole"]
            if t < P.tw_set[1]:
                a["attach"]["seed"] = 0.001
                a["part_dxy"]["seed"] = (sw[0] - an[0], sw[1] - an[1])
            else:
                a["attach"]["seed"] = 1.0
        # the orb, the wake
        a["orb_in"] = 1.0 if t >= P.orb[2] else 0.0
        a["flash"] = 0.0      # the orb stays the same blue orb in the socket (fresh agent, FK0024 round 9: the badge
        #                       flash read as the orb turning into a yellow disc); orb_burst's light is the wake's cause
        a["alive"] = ease(t, *P.wake)
        # the painted mouth: closed until its eyes are half open (monster.py: the grin starts there), then a small
        # mouth that widens into the smile, not a sudden open grin (fresh agent, FK0024 round 11)
        wm = 0.5 * (P.wake[0] + P.wake[1])
        if t < wm + 1.4:
            a["smile"] = 0.6 * ease(t, wm, wm + 1.4)
        if a["alive"] > 0.0:
            a["attach"] = None if t >= P.tw_set[1] else a["attach"]
            a["wave"] = smoothstep(_seg(t, P.wave[0], P.wave[0] + 0.5)) * (1 - smoothstep(_seg(t, P.wave[1] - 0.5,
                                                                                              P.wave[1])))
            if P.blink <= t < P.blink + 0.25:
                a["lid_top"] = 1.0
            a["turn"] = 0.0
            a["legs_turn"] = 0.0
        return x, y, a
    # hopping down off the cart onto the walkway, then with the others
    x0, y0 = NW.STATION["plant"], LN.CART_TOP
    if t < P.hop_down[1]:
        u = _seg(t, *P.hop_down)
        x = x0 + (SPROUT_DOWN - x0) * smoothstep(u)
        y = y0 + (G - y0) * u - 70.0 * math.sin(math.pi * u)
        return x, y, dict(acorn=True, smile=1.0)
    x = P.paths["sprout"](t)
    g = P.gaits["sprout"]
    return x, G, dict(acorn=True, feet=[(fx - P.shift(t), fy) for fx, fy in g.feet(t)], arm_swing=arm_swing(g, t))


def _sprout_home(P, t):
    pl = P.plant
    x = P.paths["sprout"](t)
    g = P.gaits["sprout"]
    a = dict(feet=[(fx - P.shift(t), fy) for fx, fy in g.feet(t)], arm_swing=arm_swing(g, t))
    a["acorn"] = t < pl.drop
    # the left hand: the acorn held at its chest while Digs digs (clear of his claw), out level over the hole to drop
    # it, back to its chest while he pats the soil in (fresh agent, FK0024 beat review: his claw met its hand)
    up = smoothstep(_seg(t, pl.sprout_in[0] - 0.8, pl.sprout_in[0]))
    if up > 0.0:                                       # (until then its arm hangs, the acorn in sight)
        ang = SPROUT_HANG + (SPROUT_RAISE - SPROUT_HANG) * up
        ang += (SPROUT_PLACE - ang) * smoothstep(_seg(t, *pl.drop_arm))
        ang += (SPROUT_CHEST - ang) * smoothstep(_seg(t, *pl.arm_back))
        a["arm_ang"] = ang
        a["arm_swing"] = None
    y = G
    if pl.hop[0] <= t < pl.hop[1]:                     # round the FRONT of the mound to the watering side (fresh
        st_ = VB.Planting.HOP_DUR                      # agent, FK0024 round 7: along the path in front it walked over
        dy = -SPROUT_BEHIND * smoothstep(_seg(t, pl.hop[0], pl.hop[0] + st_)) * (   # the just-planted spot), in
            1 - smoothstep(_seg(t, pl.hop[1] - st_, pl.hop[1])))                     # three little bounces (round
        f = ((t - pl.hop[0]) / st_) % 1.0                                            # 16: no long walk), feet
        y = G + dy - VB.Planting.HOP_H * math.sin(math.pi * f)                       # together under it
        a.pop("feet", None)
        a["arm_swing"] = None
    if t >= pl.can_take[0]:
        m = Monster("sprout", k=K)
        m.x, m.y = x, G
        if t < pl.can_take[1]:
            u = smoothstep(_seg(t, *pl.can_take))
            sh_ = (x + 78 * K, G - 150 * K + 4 * K)
            gx, gy = can_grip()
            ang0, ang1 = math.atan2(34, 46), math.atan2(gy - sh_[1], gx - sh_[0])
            a["arm_ang_r"] = ang0 + (ang1 - ang0) * u
            a["arm_swing"] = None
            a["grip"] = 0.0
        else:
            a["can"] = True
            a["arm_swing"] = None
            a["water"] = smoothstep(_seg(t, pl.water[0], pl.water[0] + 0.7)) * (
                1 - smoothstep(_seg(t, pl.water[1] - 0.7, pl.water[1])))
            lift = smoothstep(_seg(t, pl.water[0] - 0.4, pl.water[0] + 0.3)) * (
                1 - smoothstep(_seg(t, pl.water[1] - 0.2, pl.step_back[0] + 0.5)))
            if t >= pl.hop[1]:                         # the can lifted while it waters (its rose over the mound)
                a["arm_ang_r"] = math.atan2(34, 46) - 0.65 * lift + 0.55 * smoothstep(_seg(t, *pl.step_back))
            a["water_floor"] = VB.BACK + 4.0           # the drops land on the mound, not the path in front
    return x, y, a


SPROUT_BEHIND = -42.0                # its feet's step up the screen to go round the mound: negative, a step DOWN
                                     # it: round the FRONT, nearer us, clear of the soil patch's front lip (fresh
                                     # agent, FK0024 round 13: 84 up behind it, the same size, read as floating)
SPROUT_HANG = math.atan2(34, -46)    # Sprout's left arm hanging (monster.py's own rest)
SPROUT_RAISE = math.radians(200)     # ...held up beside its head, the acorn shown (clear of Digs' claw)
SPROUT_PLACE = math.radians(140)     # ...lowered over the hole to let the acorn drop in
SPROUT_CHEST = math.radians(54)      # ...tucked in, empty, while Digs pats the soil back


def can_grip():
    """The watering can's handle (world) standing on the stump: the can's bottom on the stump's top."""
    m = Monster("sprout", k=K)
    hd = (NW.STUMP_X - 4.0, 0.0)
    return hd[0], NW.STUMP_TOP - m.can_bottom(hd)


def _keeper(kd, t):
    P = plan()
    sh = P.shift(t)
    place = P.place(t)
    if kd == "sprout":
        return sprout_state(P, t)
    look = watching(P, t, kd, 0.0)
    if kd in ("teeth", "digger", "tentacles"):
        g = P.gaits[kd]
        x = g.body_x(t)
        a = dict(feet=[(fx - sh, fy) for fx, fy in g.feet(t)], attend=0.25)
        if look is not None and abs(P.turns[kd](t)) < 0.05:
            a["turn"] = look * 0.6
        if kd == "tentacles":
            a.update(float=0.2, **hans_mood("calm"))
            if hans_lift(t) > 0.0:
                a["attach"] = dict(wings=1.0, beard=1.0, eyes=1.0, legs=0.0)
            return x, G + g.bob(t), a
        a["arm_swing"] = arm_swing(g, t)
        if kd == "teeth":
            a.update(hands=True, saws=False, blades=0.0, knee_fwd=True, clamp_reach=True)
            hands, blade, grip = twigs_hands(P, t, x)
            if hands:
                side = list(hands)[0]
                a.update(arm_to={s_: (hx - sh, hy) for s_, (hx, hy) in hands.items()}, grip=grip)
                if side < 0:
                    a.update(blades_l=blade, blades=0.0)
                else:
                    a.update(blades=blade, blades_l=0.0)
            return x, G, a
        hip, leg = (62.0, 78.0)
        n = 1.0 - TURN_NARROW * abs(P.turns[kd](t))
        y = G + stance_drop(g, lambda t_: (x - hip * K * n, x + hip * K * n), leg * K, t)
        if place == 2:                          # digging / filling: both paws, a mole's strokes
            pa = P.plant.paws(t)
            if pa is not None:
                a["paw_ang"] = pa
        return x, y, a
    if kd == "springs":
        x, y, sq = P.hopper.state(t)
        a = dict(spring=sq, attend=0.25, arm_swing=0.0)
        if look is not None:
            a["turn"] = look * 0.6
        return x, y, a
    if kd == "wheels":
        x = P.paths[kd](t)
        a = dict(wheel_rot=x / WR, attend=0.25, arm_swing=roll_swing(P.paths[kd], t, WR), clamp_reach=True)
        if look is not None and abs(P.turns[kd](t)) < 0.05:
            a["turn"] = look * 0.6
        return x, G, a
    x = P.paths[kd](t)
    a = dict(attend=0.25, lamp=1.0 + 0.8 * glo_flare(t))
    if look is not None:
        a["turn"] = look * 0.6
    return x, GLO_Y - 60.0 * (place == 1), a


def glo_flare(t):
    P = plan()
    u = t - P.idea
    return math.sin(math.pi * u / 2.2) if 0 <= u < 2.2 else 0.0      # (a long light flare as the idea comes)


# ----------------------------------------------------------------------------------------------- Hans

HANS_LIFT = {-2: 0, 2: 5}           # the cheer: his outermost legs lift and wave as a 3rd and 4th arm
N_SPINE = 48


def _cheer_win(P, t):
    """The cheer Hans is in (or coming up to) at t: the hall's, or the one at home at the end; None while not."""
    place = P.place(t)
    if place == 1:
        return P.cheer
    if place == 2 and t >= P.cheer2[0] - 1.4:
        return P.cheer2
    return None


def _hans_targets(t, x):
    P = plan()
    place = P.place(t)
    if place == 0:
        return P.branch1.hans_targets(t, (-1, -2))
    cw = _cheer_win(P, t)
    if cw is None:
        return P.branch2.hans_targets(t, (1, 2)) if place == 2 else []
    c0, c1 = cw
    if c0 - 0.6 <= t < c1 + 0.8:                            # cheering: his two outer legs lift and wave (fresh
        g = smoothstep(_seg(t, c0 - 0.6, c0)) * (1 - smoothstep(_seg(t, c1, c1 + 0.8)))   # agent, FK0024 round 8:
        y0 = G - 305 * K                                    # two more tentacles popped in over his chest and eyes)
        out = []
        for slot, dx in ((-2, -190), (2, 190)):
            w = 18.0 * math.sin((t - c0) * 6.0 + slot)
            out.append((slot, (x + dx * K + w, y0 - (190 if abs(slot) == 1 else 120) * K), g))
        return out
    return []


HANS_LIFT_BRANCH = ({-2: 0, -1: 1}, {1: 4, 2: 5})   # holding a branch: the two legs on its side lift into arms


def hans_lift_map(t):
    """{working slot: the leg that lifts to be it} (owner 2026-11-06: 8 tentacles in all, arms come from legs that
    visibly lift; fresh agent, FK0024 round 7: two tentacles grew out of nothing at 0:10 and vanished at 0:21)."""
    P = plan()
    place = P.place(t)
    if place == 0:
        return HANS_LIFT_BRANCH[0]
    return HANS_LIFT if _cheer_win(P, t) is not None else HANS_LIFT_BRANCH[1]


def hans_lift(t):
    P = plan()
    place = P.place(t)
    cw = _cheer_win(P, t)
    if place == 0 or (place == 2 and cw is None):
        br = P.branch1 if place == 0 else P.branch2
        a, b = br.grip[0], br.let_go[1]
        return smoothstep(_seg(t, a - 0.7, a)) * (1 - smoothstep(_seg(t, b, b + 0.7)))
    c0, c1 = cw
    a, b = c0 - 0.6, c1 + 0.8
    return smoothstep(_seg(t, a - 0.7, a + 0.1)) * (1 - smoothstep(_seg(t, b, b + 0.7)))


class _Rec:
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
    q = rec.poly
    n = len(q) // 2
    left, right = q[:n], q[n:][::-1]
    sp, w = (left + right) / 2, np.linalg.norm(left - right, axis=1)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
    v = np.linspace(0.0, arc[-1], N_SPINE)
    return np.stack([np.interp(v, arc, sp[:, 0]), np.interp(v, arc, sp[:, 1])], axis=1), np.interp(v, arc, w)


def _draw_leg(cv, sp, w, col, side, sucker, flat):
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
    """Hans' legs while two of them lift to wave (as marble_flat): the four standing as the Monster draws them, the
    two outer ones blending from planted legs into arms. Records m.leg_len and m.lifted for the checks."""
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
        lm = hans_lift_map(t)
        P = plan()
        place = P.place(t)
        br = (P.branch1 if place == 0 else P.branch2) if place in (0, 2) and _cheer_win(P, t) is None else None
        m.leg_len = []
        for i, ft in enumerate(m.feet):
            root = m.leg_root(i, t)
            side = 1 if (i - 2.5) / 2.5 > 0 else -1
            slot = next((s_ for s_, j in lm.items() if j == i), None)
            if slot is None:
                m.leg_len.append(planted_tentacle(cv, root, ft, 275 * k, 44 * k, col, side, sucker))
                continue
            (tx, ty), on = tg.get(slot, ((ft[0] + sh, ft[1]), 0.0))
            on = min(max(on, 0.0), 1.0)
            tip = (ft[0] + (tx - sh - ft[0]) * on, ft[1] + (ty - ft[1]) * on)
            rp, rr = _Rec(flat), _Rec(flat)
            L0 = planted_tentacle(rp, root, ft, 275 * k, 44 * k, col, side, sucker)
            sd = 1 if tip[0] >= root[0] else -1
            if br is not None and on >= 0.999 and t >= br.grip[1]:
                # holding the branch: it keeps the length it had when it took hold (owner, FK0012: no stretching)
                th = br.grip[1]
                hx, hy = dict((s_, p_) for s_, p_, g_ in _hans_targets(th, m.x + sh))[slot]
                hold = reach_tentacle(_Rec(flat), root[0], root[1], hx - sh, hy, 50 * k, col, th, 1.3 * slot + 0.7,
                                      1 if hx - sh >= root[0] else -1, 1.0)
                L1 = fixed_tentacle(rr, root, tip, hold, 50 * k, col, t, 1.3 * slot + 0.7, sd, 1.0, sucker)
            else:
                L1 = reach_tentacle(rr, root[0], root[1], tip[0], tip[1], 50 * k, col, t, 1.3 * slot + 0.7, sd, on)
            (s0, w0), (s1, w1) = _spine_of(rp), _spine_of(rr)
            e = smoothstep(u)
            _draw_leg(cv, s0 * (1 - e) + s1 * e, w0 * (1 - e) + w1 * e, col, side, sucker, flat)
            m.lifted.append((i, root, tip, L0 * (1 - e) + L1 * e))
    return draw


def hans_extra(t, sh):
    """Hans' working tentacles, drawn on his own layer; records m.work for the checks."""
    def draw(cv, m):
        m.work = []
        lifted = hans_lift(t) > 0.0
        lm = hans_lift_map(t)
        for slot, (tx, ty), grip in _hans_targets(t, m.x + sh):
            if grip <= 0.001 or (lifted and slot in lm):
                continue
            side = 1 if tx - sh >= m.x else -1
            rest = (m.x + side * (80 + 20 * abs(slot)) * K, m.y - 12.0)      # slack: hanging down beside him
            gx, gy = rest[0] + (tx - sh - rest[0]) * grip, rest[1] + (ty - rest[1]) * grip
            place = plan().place(t)
            hold = hold_length(t, slot, m.x + sh) if place in (0, 2) and grip >= 0.999 else None
            if hold is None:
                root, L = m.work_tentacle(cv, gx, gy, t, slot=slot, grip=1.0)
            else:
                root = work_root(m, gx, t, slot)
                L = fixed_tentacle(cv, root, (gx, gy), hold, 50 * K,
                                   m.parts_col.get("legs", np.asarray(m.color) * 0.82), t, 1.3 * slot + 0.7,
                                   1 if gx >= m.x else -1, 1.0, m.parts_col.get("suckers"))
            m.work.append((slot, root, (gx, gy), L))
    return draw


def work_root(m, tx, t, slot):
    """Where Hans' working tentacle in `slot` comes out (monster.work_tentacle's root ring)."""
    k = m.k
    hy = m.y - 305 * k + m.alive * 5 * math.sin(t * 1.4) * k * m.float
    side = 1 if tx >= m.x else -1
    return m.x + side * (40 + 22 * abs(slot)) * k, hy + (64 + 8 * abs(slot)) * k


def hold_length(t, slot, hx_world):
    """The length Hans' tentacle in `slot` has when it takes hold of the branch (its grip window's end): from then
    on it stays that long (owner, FK0012: no stretching tentacles)."""
    P = plan()
    br = P.branch1 if P.place(t) == 0 else P.branch2
    if t < br.grip[1]:
        return None
    th = br.grip[1]
    x, y, a = keeper("tentacles", th)                  # (where he stood when he took hold)
    for s_, (tx, ty), g in _hans_targets(th, x):
        if s_ == slot:
            m = Monster("tentacles", k=K)
            m.x, m.y = x, y
            for k_, v_ in a.items():
                setattr(m, k_, v_)
            r = work_root(m, tx, th, slot)
            return math.dist(r, (tx, ty))
    return None


def fixed_tentacle(cv, root, tip, L, width, col, t, phase, side, grip, sucker):
    """monster.reach_tentacle's look, but always `L` long: when the held point comes nearer than that, the S-curve
    bulges more (the tentacle bends and takes up the slack) instead of the tentacle shrinking. Returns its length."""
    from families.foundry.products.monster import lighten
    x0, y0 = root
    tx, ty = tip
    c = math.hypot(tx - x0, ty - y0) + 1e-6
    up = ty < y0
    p0, p3 = np.array([x0, y0]), np.array([tx, ty])
    u = np.linspace(0, 1, 29)[:, None]

    def spine_for(s_):
        p1 = p0 + np.array([side * 0.45 * c, 0.18 * c]) * s_
        p2 = p3 + np.array([-side * 0.12 * c, (0.32 if up else -0.28) * c]) * s_
        return ((1 - u) ** 3) * p0 + 3 * ((1 - u) ** 2) * u * p1 + 3 * (1 - u) * u * u * p2 + (u ** 3) * p3

    def length(sp):
        return float(np.sum(np.linalg.norm(np.diff(sp, axis=0), axis=1)))
    lo, hi = 1.0, 1.0
    if length(spine_for(1.0)) < L:
        hi = 2.0
        while length(spine_for(hi)) < L and hi < 12:
            hi *= 1.6
        for _ in range(30):
            mid = (lo + hi) / 2
            if length(spine_for(mid)) < L:
                lo = mid
            else:
                hi = mid
    spine = spine_for(hi if hi > 1.0 else 1.0)
    d = np.gradient(spine, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], axis=1)
    uu = u[:, 0]
    wave = 0.05 * c * np.sin(np.pi * uu) * np.sin(t * 1.7 + phase + uu * 4.0)
    spine = spine + nrm * wave[:, None]
    r0 = width * 0.55
    a0 = math.atan2(spine[-1][1] - spine[-2][1], spine[-1][0] - spine[-2][0]) - side * math.pi / 2
    turn = (0.55 + 0.25 * grip) * 2 * math.pi
    wrap = []
    for i in range(1, 11):
        f = i / 10
        a = a0 + side * turn * f
        r = r0 * (1 - 0.35 * f)
        wrap.append((tx + math.cos(a) * r - math.cos(a0) * r0, ty + math.sin(a) * r - math.sin(a0) * r0))
    pts = np.vstack([spine, np.array(wrap)])
    n = len(pts)
    dd = np.gradient(pts, axis=0)
    dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-9
    nn = np.stack([-dd[:, 1], dd[:, 0]], axis=1)
    w = width * (1 - 0.62 * np.linspace(0, 1, n) ** 0.8)
    left = pts + nn * (w / 2)[:, None]
    right = pts - nn * (w / 2)[:, None]
    poly = np.vstack([left, right[::-1]])
    col = np.asarray(col)
    cv.polygon(poly, col)
    cv.polyline(poly, col * 0.55, 2, closed=True)
    cv.polyline(pts[2:-4] + nn[2:-4] * (w[2:-4] * 0.22)[:, None], lighten(col, 1.18), max(2.0, width * 0.12))
    under = -side if not up else side
    for i in range(4, n - 3, 3):
        sx, sy = pts[i] + nn[i] * (under * w[i] * 0.36)
        cv.circle(sx, sy, w[i] * 0.15, lighten(col, 1.35) if sucker is None else sucker)
    return float(np.sum(np.linalg.norm(np.diff(spine, axis=0), axis=1)))


# ----------------------------------------------------------------------------------------------- drawing helpers

def figure(pg, kind, x, y, k, t=1.3, extra=None, pre=None, **attrs):
    """il.figure (flat style 6) for a page whose canvas is translated (a pulled-back frame)."""
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
    if kind == "sprout":
        m.acorn_r = ACORN_R
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
    if m.alive > 0.0 or kind != "sprout":
        pg.shadow(x, y + 4, hw * 0.75, 14 + 10 * k, il.STYLES[6]["shadow"])
    with NW.raw(pg):
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
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=int(abs(x)) % 97 + 1)
    cv.c.translate(pg.ox, pg.oy)
    draw(cv)
    pg.grain_on(cv.c, x, y, getattr(cv, "bounds", None))
    if shadow:
        pg.shadow(x, y + 2, shadow, max(6.0, shadow * 0.16), il.STYLES[6]["shadow"])
    with NW.raw(pg):
        pg.c.drawImage(cv.surface.makeImageSnapshot(), 0, 0)


def draw_can_on_stump(pg, t, sh):
    m = Monster("sprout", k=K)
    gx, gy = can_grip()
    creature(pg, lambda cv: m._draw_can(cv, t, (gx - sh, gy), 0.0), gx - sh, gy)


# ----------------------------------------------------------------------------------------------- overlays (screen)

_FONT = {}
INK, PAPER = (70, 52, 44), (252, 246, 234)


def _font(size, weight="Bold"):
    key = (round(size, 1), weight)
    if key not in _FONT:
        path = {"Bold": "engine/assets/fonts/Inter-Bold.otf", "Medium": "engine/assets/fonts/Inter-Medium.otf"}[weight]
        _FONT[key] = skia.Font(skia.Typeface.MakeFromFile(path), size)
    return _FONT[key]


def _text(pg, s, x, y, size, col=INK, a=1.0, weight="Bold", center=False):
    f = _font(size, weight)
    if center:
        x -= f.measureText(s) / 2
    pg.c.drawString(s, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))


def _card(pg, x, y, w, h, a):
    pg.flat(rrect(x + 3, y + 5, x + w + 3, y + h + 5, 14), (40, 28, 24), 0.18 * a, blur=6)
    pg.flat(rrect(x, y, x + w, y + h, 14), PAPER, a)


def screen_xy(P, t, x, y):
    cx, z = P.cam(t)
    return NW.to_frame(x - (cx - W / 2), y, z)


TAG_DY = {"lantern": 166.0, "tentacles": 123.0, "teeth": 72.0, "wheels": 60.0, "springs": 33.0}  # the tag
# sits just over each head (KH tops sit high), not up in the sky (fresh agent, FK0024 round 7)


def overlays(out, t):
    """Screen-space text on the finished frame (it holds still): name tags, Sprout's name card, the end sign."""
    P = plan()
    a0, a1 = P.tags
    if a0 < t < a1 + 1.0:
        a = smoothstep((t - a0) / 0.8) * (1 - smoothstep((t - a1) / 1.0))
        for kd in SIX:
            r = keeper(kd, t)                          # over each Keeper's own head, with this frame's camera
            x, y, _ = r
            sx, sy = screen_xy(P, t, x, y - KH[kd] * K - 26 + TAG_DY.get(kd, 0.0))
            if 60 < sx < W - 60:
                tw = _font(30).measureText(NAMES[kd])
                _card(out, sx - tw / 2 - 16, sy - 34, tw + 32, 46, a)
                _text(out, NAMES[kd], sx, sy, 30, a=a, center=True)
    c0, c1 = P.card
    if c0 < t < c1 + 1.0:
        a = smoothstep((t - c0) / 0.8) * (1 - smoothstep((t - c1) / 1.0))
        bw, bh = 820, 150
        x0, y0 = (W - bw) / 2, 34                 # (clear of the PLANT sign below it as the camera pulls back)
        _card(out, x0, y0, bw, bh, a)
        _text(out, CARD[0], W / 2, y0 + 72, 60, col=(76, 140, 72), a=a, center=True)
        _text(out, CARD[1], W / 2, y0 + 122, 32, a=a, weight="Medium", center=True)
    end_sign(out, t)


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
    _text(out, "WHAT SHOULD THEY BUILD NEXT?", W / 2, y0 + 110, 50, col=PAPER, a=sa, center=True)
    _text(out, "Comment your idea below!", W / 2, y0 + 172, 34, col=(250, 232, 200), a=sa, weight="Medium",
          center=True)


def bubbles(out, t):
    from .chatter import _back, bubble
    P = plan()
    for tv, kd, mood in P.voices:
        u = t - tv
        pic = mood_info(mood)[2]
        life = IDEA_LIFE if mood == "idea" else 1.4
        if pic is None or pic in ("!", "?") or not (0 <= u < life) or t >= P.sign[0] - 4.0:
            continue
        if P.place(t) != P.place(tv):
            continue
        r_ = keeper(kd, t)
        if r_ is None:
            continue
        x, y, _ = r_
        sx, sy = screen_xy(P, t, x + 70 * K, y - KH[kd] * K)
        sx, sy = sx + 26, sy - 62
        s = _back(min(u / 0.25, 1.0)) * (1 - smoothstep((u - life + 0.3) / 0.3))
        if s < 0.08:
            continue
        r = BUBBLE_R * (IDEA_R if mood == "idea" else 1.0)
        if mood == "idea":
            sx, sy = sx + 30, sy - 40                    # (the bigger bubble clear of Glo's dome)

            def draw(cv, bx=sx, by=sy, s=s, r=r):
                bubble(cv, bx, by, r * s, "none", (214, 196, 176), 1.0, (bx - 92 * s, by + 120 * s))
                idea_friend(cv, bx, by, r * s)
            il.creature(out, draw, sx, sy)
            continue
        il.creature(out, lambda cv, bx=sx, by=sy, s=s, pic=pic, r=r: bubble(cv, bx, by, r * s, pic, (214, 196, 176), 1.0,
                                                                          (bx - 62 * s, by + 92 * s)), sx, sy)


IDEA_LIFE = 5.6        # Glo's idea bubble stays up through "...one who plants trees!" (fresh agent, FK0024 round 16:
IDEA_R = 1.7           # at 2.6 s and 1.25x it was gone before the words and too small to read)


def idea_friend(cv, x, y, r):
    """Glo's idea, in his bubble: a new friend who plants trees - a little acorn with a face, a sapling beside it."""
    from families.foundry.products.monster import ellipse
    if r < 6:
        return
    ax, ay = x - r * 0.28, y + r * 0.08
    nut, cap, ink = np.array([168, 116, 64.0]), np.array([104, 78, 50.0]), np.array([60, 44, 34.0])
    cv.polygon(ellipse(ax, ay + r * 0.12, r * 0.34, r * 0.42, 24), nut)
    cv.polygon(ellipse(ax, ay - r * 0.2, r * 0.42, r * 0.24, 24, math.pi, 2 * math.pi), cap)
    cv.line(ax - r * 0.42, ay - r * 0.2, ax + r * 0.42, ay - r * 0.2, cap, max(2.0, r * 0.1))
    for ex in (-1, 1):                                   # two happy eyes and a smile
        cv.circle(ax + ex * r * 0.13, ay + r * 0.04, max(1.2, r * 0.055), ink)
    cv.arc(ax, ay + r * 0.12, r * 0.14, 20, 160, ink, max(1.2, r * 0.04))
    cv.line(ax + r * 0.32, ay + r * 0.12, ax + r * 0.5, ay + r * 0.02, nut * 0.9, max(1.5, r * 0.07))   # its arm
    gx, gy = x + r * 0.42, y + r * 0.5                   # the sapling, in a little mound of soil
    cv.polygon(ellipse(gx, gy, r * 0.26, r * 0.08, 18), np.array([110, 84, 60.0]))
    cv.line(gx, gy, gx, gy - r * 0.62, np.array([96, 120, 62.0]), max(1.5, r * 0.06))
    leaf = np.array([120, 176, 92.0])
    for i, (dy, sd) in enumerate(((0.62, 0), (0.42, -1), (0.3, 1))):
        lx, ly = gx + sd * r * 0.14, gy - r * dy
        cv.polygon(ellipse(lx, ly, r * 0.13, r * 0.07, 14), leaf * (1.0 - 0.06 * i))


# ----------------------------------------------------------------------------------------------- the frame

def frame(world, t, cam=None, ui=True):
    """cam: (x, zoom) to look from instead of the plan's camera (thumbnails); ui False: no bubbles, tags or cards."""
    P = plan()
    cx, z = cam if cam is not None else P.cam(t)
    sh = cx - W / 2
    Pg = NW.Page(z)
    pg = Pg.pg
    place = P.place(t)
    ms = {}
    if place == 1:
        _hall(Pg, pg, world, P, t, sh, z, ms)
    else:
        _village(Pg, pg, world, P, t, sh, z, ms, place)
    out = Pg.final()
    d = P.dim(t)
    if d > 0.0:
        with NW.raw(out):
            out.c.drawPaint(skia.Paint(Color=skia.Color4f(0.05, 0.06, 0.09, d)))
    if ui:
        with NW.raw(out):
            bubbles(out, t)
            overlays(out, t)
    return out.finish(), ms


def _draw_keepers(pg, P, t, sh, z, ms, order):
    for kd in order:
        r = keeper(kd, t)
        if r is None:
            continue
        x, y, a = r
        if -800 < x - sh < W / z + 800:
            ms[kd] = figure(pg, kd, x - sh, y, K, t=t, extra=hans_extra(t, sh) if kd == "tentacles" else None,
                            pre=hans_pre(t, sh) if kd == "tentacles" else None, **a)


def _village(Pg, pg, world, P, t, sh, z, ms, place):
    mood = ("night", "night", 0.0) if place == 0 else ("predawn", "predawn", 0.0)
    NW.sky(Pg, t, mood, sh)
    world.village.draw(Pg, sh)
    b1, b2 = P.branch1, P.branch2
    # beat 1's branch: on the oak, cut, laid down (still lying there at home)
    b1.draw(pg, t if place == 0 else 1e9, sh)
    b1.draw_stub_end(pg, t if place == 0 else 1e9, sh)
    if place == 2:
        b2.draw(pg, t, sh)
        b2.draw_stub_end(pg, t, sh)
        ac = P.plant.acorn_pos(t, lambda tt: sprout_hand(P, tt))

        def draw_acorn():
            from families.foundry.products.monster import acorn_nut
            pg.c.save()
            pg.c.clipRect(skia.Rect(-4000, -4000, 9000, P.plant.acorn_clip(t)))
            creature(pg, lambda cv: acorn_nut(cv, ac[0] - sh, ac[1], ACORN_R * K), ac[0] - sh, ac[1])
            pg.c.restore()
        P.plant.draw_ground(pg, t, sh, draw_acorn if (ac is not None and ac != "buried") else None)
        VB.draw_stump_can(pg, t, sh, P.plant, lambda x, y: None)
        if t < P.plant.can_take[1]:
            draw_can_on_stump(pg, t, sh)
        P.plant.draw_tree(pg, t, sh, lambda f: creature(pg, f, P.plant.HOLE - sh, BACK))
    # the sawdust falls from the branch, behind the Keepers in front of it (fresh agent, FK0024 round 13: drawn over
    # Twigs it read as pale spots on his paw)
    (b1 if place == 0 else b2).sawdust(pg, t, sh)
    order = ["springs", "digger", "lantern", "teeth", "tentacles", "wheels"] if place == 0 else \
        ["lantern", "wheels", "springs", "teeth", "tentacles", "digger", "sprout"]
    _draw_keepers(pg, P, t, sh, z, ms, order)
    if place == 2:
        P.plant.draw_soil(pg, t, sh)
    if place == 2 and "sprout" in ms:
        water_stream(pg, P, t, ms["sprout"])
    NW.multiply(pg, NW.sky_mul(mood))
    NW.factory_lights(pg, sh, 1.0 if place == 0 else 0.5)
    gx, gy, ga = keeper("lantern", t)
    pg.glow(gx - sh, gy - 120 * K, 160, "#ffe6a6", 0.18 * ga.get("lamp", 1.0))


def water_stream(pg, P, t, m):
    """One clear, see-through stream of water arcing from the can's spout down onto the mound and a little splash where
    it lands (fresh agent, FK0024 round 15: the threads of outlined drops read as a pile of blue beads, not water).
    The soil going dark under it is the mound's own wet patch (Planting.draw)."""
    w = getattr(m, "water", 0.0)
    rx, ry = m.can_rose(t)
    floor = VB.BACK + 4.0
    lx = rx + 26.0                                     # where it lands on the mound
    if w <= 0.5:
        return
    s = min(1.0, (w - 0.5) / 0.3)
    fall = max(20.0, floor - ry)
    x0, y0 = rx + 2.0, ry + 3.0                        # leaves the spout going out and down, curves down to the mound
    cx_, cy_ = rx + 20.0, ry + 4.0
    pts = []
    for q in range(17):
        u = q / 16
        x = (1 - u) ** 2 * x0 + 2 * u * (1 - u) * cx_ + u * u * lx
        y = (1 - u) ** 2 * y0 + 2 * u * (1 - u) * cy_ + u * u * (floor - 1.0)
        pts.append((x + 0.8 * math.sin(t * 11 + u * 7) * u, y))
    left, right = [], []
    for q, (x, y) in enumerate(pts):
        xa, ya = pts[max(0, q - 1)]
        xb, yb = pts[min(16, q + 1)]
        dx, dy = xb - xa, yb - ya
        n = math.hypot(dx, dy) or 1.0
        hw = (3.2 + 2.6 * q / 16) * s
        left.append((x - dy / n * hw, y + dx / n * hw))
        right.append((x + dy / n * hw, y - dx / n * hw))
    path = skia.Path()
    path.moveTo(*left[0])
    for pnt in left[1:]:
        path.lineTo(*pnt)
    for pnt in reversed(right):
        path.lineTo(*pnt)
    path.close()
    pg.flat(path, (150, 205, 245), 0.55 * s)           # the see-through stream
    core = skia.Path()
    core.moveTo(*pts[0])
    for pnt in pts[1:]:
        core.lineTo(*pnt)
    pg.stroke(core, (225, 242, 255), 1.4 * s, 0.6 * s)   # a bright line down its middle
    for i in range(6):                                 # a little splash where it lands
        ph = (t * 2.4 + i / 6) % 1.0
        side = -1 if i % 2 else 1
        sx_ = lx + side * (4 + 10 * ph) * (0.6 + 0.15 * (i % 3))
        sy_ = floor - 2 - 9 * math.sin(math.pi * ph) * (0.7 + 0.15 * (i % 3))
        pg.flat(LN.oval(sx_, sy_, 1.8 * s, 1.8 * s), (190, 225, 250), 0.75 * (1 - ph) * s)


WAVE_R = 270.0 * K                    # far enough out from the socket to cover all of Sprout (cap, feet, hands)


def green_wave(P, t):
    """The radius (px) of the orb's green spreading out from its socket over Sprout's wood while it wakes, or None
    outside it (fresh agent, FK0024 round 11: the whole body turned green at once with no visible cause, read as a
    new face replacing the painted one; now the colour comes from the orb as a ring, and the painted eyes open
    where they are)."""
    a, b = P.orb[2] + 0.2, P.wake[1]
    if not (a <= t < b):
        return None
    return WAVE_R * ease(t, a, b)


def orb_burst(pg, P, t, sh):
    """The moment the seventh orb clicks in: a soft burst of its light round the socket, then Sprout's colour comes
    (fresh agent, FK0024 beat review: the wake spark was too small to see)."""
    a, b = P.flash
    if not (a <= t <= b + 0.6):
        return
    u = (t - a) / (b + 0.6 - a)
    ox, oy = LN.geom(P.line.cart_x(t) - sh, LN.CART_TOP)["socket"]
    k = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.6 else max(0.0, 1.0 - (u - 0.3) / 0.7)
    for r, al in ((90.0, 0.10), (60.0, 0.16), (36.0, 0.26)):
        pg.flat(LN.oval(ox, oy, r * (0.6 + 0.4 * k), r * (0.6 + 0.4 * k)), (200, 230, 255), al * k)


def sprout_hand(P, t):
    """Sprout's left hand (world), where the acorn is."""
    x, y, a = sprout_state(P, t)
    m = Monster("sprout", k=K)
    m.x, m.y = x, y
    m.acorn_r = ACORN_R
    for k_, v in a.items():
        if k_ in ("hold_out", "wave", "arm_ang"):
            setattr(m, k_, v)
    return m.acorn_xy(t)


def _hall(Pg, pg, world, P, t, sh, z, ms):
    L = P.line
    world.hall.draw(Pg, sh)
    NW.door_opening(pg, sh, 1.0)
    LN.bin_(pg, LN.TRAY_X - sh, "SHAVINGS", front=False)
    LN.draw_hoist(pg, L, t, sh)
    LN.draw_cut_back(pg, L, t, sh)
    LN.draw_turn_back(pg, L, t, sh)
    LN.draw_fit(pg, L, t, sh)
    LN.draw_plant(pg, L, t, sh, holding=t < L.at["plant"][0])
    if t < P.hop_down[1]:
        LN.cart(pg, L.cart_x(t) - sh, L.sprout(t)[2]["spin"])
    else:
        LN.cart(pg, NW.STATION["plant"] - sh, 0.0)
    LN.draw_fit_front(pg, L, t, sh)           # the jaws holding the legs: in front of the peg, behind Sprout
    # Sprout on the line (the face painted on across: the painted part over the bare one)
    LN.saw_disc(pg, L, t, sh, "back")
    s = sprout_state(P, t)
    if s is not None and t < P.hop_down[0]:
        x, y, a = s
        rv = LN.reveal(L, t, x - sh)          # the scales / stain / face: done only where the tool's tip has been
        if rv is not None:
            key, clip = rv
            if key == "face":
                a0 = dict(a, attach=dict(a["attach"], face=0.0))
                a1 = dict(a, attach=dict(a["attach"], face=1.0))
            elif key == "carved":
                a0, a1 = dict(a, carved=0.0), dict(a, carved=0.999)
            else:
                a0, a1 = dict(a, stained=0.0), dict(a, stained=1.0)
            ms["sprout"] = figure(pg, "sprout", x - sh, y, K, t=t, **a0)
            pg.c.save()
            pg.c.clipPath(clip, skia.ClipOp.kIntersect, True)
            figure(pg, "sprout", x - sh, y, K, t=t, **a1)
            if key == "face":
                LN.cheek_dabs(pg, x - sh, y, a["alive"], LN._seg(t, *L.paint["paint"]))
                LN.smile_dab(pg, x - sh, y, a["alive"])        # (inside the brush's clip: painted as it goes)
            pg.c.restore()
        else:
            tc = LN.turn_clip(L, t, x - sh, y)
            if tc is not None:
                pg.c.save()
                pg.c.clipPath(tc, skia.ClipOp.kIntersect, True)
            gw = green_wave(P, t)
            if gw is None:
                ms["sprout"] = figure(pg, "sprout", x - sh, y, K, t=t, **a)
            else:                             # the orb's green spreading out from the socket over the wood
                ox, oy = LN.geom(x - sh, y)["socket"]
                ms["sprout"] = figure(pg, "sprout", x - sh, y, K, t=t, **dict(a, tint=0.0))
                pg.c.save()
                pg.c.clipPath(skia.Path().addCircle(ox, oy, max(0.5, gw)), skia.ClipOp.kIntersect, True)
                figure(pg, "sprout", x - sh, y, K, t=t, **dict(a, tint=1.0))
                pg.c.restore()
            if tc is not None:
                pg.c.restore()
            if gw is not None:
                ox, oy = LN.geom(x - sh, y)["socket"]
                fade = 1.0 - _seg(gw, WAVE_R * 0.4, WAVE_R * 0.65)   # (gone once it is past the body)
                # the orb's light itself, spreading: a wide soft glow on the wave's front and a bright core at the
                # socket while it runs (fresh agent, FK0024 round 12: a thin ring alone did not read as the cause)
                pg.stroke(skia.Path().addCircle(ox, oy, gw), (200, 250, 170), 22.0, 0.22 * fade)
                pg.flat(oval(ox, oy, 30.0, 30.0), (220, 255, 200), 0.35 * fade)
                pg.stroke(skia.Path().addCircle(ox, oy, gw), (170, 236, 150), 7.0, 0.55 * fade)
                pg.stroke(skia.Path().addCircle(ox, oy, gw), (230, 255, 210), 2.5, 0.8 * fade)
            if (a["attach"] is None or a["attach"].get("face", 0.0) >= 1.0) and a.get("alive", 1.0) < 1.0:
                LN.cheek_dabs(pg, x - sh, y, a["alive"])
                LN.smile_dab(pg, x - sh, y, a["alive"])
        LN.kerf(pg, L, t, sh)
        LN.turn_tip_front(pg, L, t, sh)
        LN.draw_carve(pg, L, t, sh)           # the chisel and the stain brush on the cap's front, where they work
        LN.draw_drill(pg, L, t, sh)
        orb_burst(pg, P, t, sh)
        if t < L.cut["saw"][1] and t >= L.hoist["come"][0]:
            g = LN.geom(x - sh, y)
            LN.eye_bolt(pg, x - sh, g["top"] - LN.LT * K - 2)
    oc = LN.offcut_pose(L, t, sh)
    if oc:                                             # the log's own top part, exactly as it looked before the cut
        x0_, y0_, _ = LN.offcut_pose(L, L.cut["saw"][1], sh)
        xl, yl, al = L.sprout(L.cut["saw"][1] - 1e-3)
        # (just the wood: not the parts waiting on the PARTS shelf - fresh agent, FK0024 round 9: with the shelf up
        # above the cut line they rode up with the offcut as a second set)
        al = dict(al, attach={k_: 0.0 for k_ in al["attach"]}, part_dxy={})
        ycut = LN.geom(0, LN.CART_TOP)["top"]
        dx_, dy_ = oc[0] - x0_, oc[1] - y0_
        pg.c.save()
        pg.c.clipRect(skia.Rect(-4000, -4000, 9000, ycut + dy_ + 1))
        figure(pg, "sprout", xl - sh + dx_, yl + dy_, K, t=L.cut["saw"][1] - 1e-3, **al)
        pg.c.restore()
        LN.eye_bolt(pg, oc[0], oc[1] - 2)
    LN.saw_disc(pg, L, t, sh, "front")
    LN.shavings(pg, L, t, sh)
    LN.face_brush(pg, L, t, sh)
    LN.bin_(pg, LN.TRAY_X - sh, "SHAVINGS")
    LN.draw_orb_trolley(pg, L, t, sh, P.orb)
    order = ["lantern", "wheels", "tentacles", "springs", "digger", "teeth"]
    if t >= P.hop_down[0]:
        order.append("sprout")
    _draw_keepers(pg, P, t, sh, z, ms, order)
    NW.door_panel(pg, sh, 1.0)


# ----------------------------------------------------------------------------------------------- the sound

def _music_variant():
    """This episode's own music-box variant (registered here so the shared music.py is untouched): in A flat, a
    little slower and cosy, the curious part early, quiet bars for the narrator."""
    from . import music
    if "newfriendflat" not in music.VARIANTS:
        music.VARIANTS["newfriendflat"] = (8, 94.0, [(music.B, -12), (music.REST, -12), (music.A, -12),
                                                     (music.C, -12), (music.REST, -12), (music.D, -12),
                                                     (music.A, -12), (music.REST, -12), (music.B, -12),
                                                     (music.C, -12), (music.REST, -12)])


PENTA = [56, 58, 60, 63, 65, 68, 70, 72]            # A flat major pentatonic, for the wooden clacks


def soundtrack(path):
    """The music box (its own variant), the Keepers' voices, soft sounds for what happens on screen, the narrator
    over it all (the music eases down only while she speaks). -> (wav, stats, track)"""
    from engine.audio import EventTrack
    from . import music
    from .chatter import VOICE, VOWEL
    from .narrator import soundtrack as narr_mix, take
    _music_variant()
    P = plan()
    track = EventTrack(12)
    chords = music.compose(track, 0.3, P.end - 1.0, gain=0.9, variant="newfriendflat")

    def pan_at(t, x):
        cx, z = P.cam(t)
        return max(-0.6, min(0.6, ((x - cx) * z / W) * 1.2))

    for tv, kd, mood in P.voices:
        contour, st, _ = mood_info(mood)
        r = keeper(kd, tv)
        x = r[0] if r else P.cam(tv)[0]
        track.hit(tv, f"voice_{contour}@{int(round(VOWEL[kd] * 100))}", VOICE[kd] + st, 0.3, pan_at(tv, x))
    L = P.line
    for br in (P.branch1, P.branch2):
        for q in range(br.STROKES):
            ta = br.saw[0] + q * br.STROKE
            track.fx(ta, "saw", 0.3, 0.05, pan_at(ta, br.q[0]))
        track.hit(br.cut + 0.05, "wood_thud", 50, 0.06, pan_at(br.cut, br.q[0]))
        track.hit(br.lower[1] + 0.05, "wood_thud", 43, 0.12, pan_at(br.lower[1], br.lie[0][0]))
    # the line
    h = L.hoist
    track.fx(h["come"][0], "creak", h["come"][1] - h["come"][0], 0.04, pan_at(h["come"][0], NW.STATION["hoist"]))
    track.fx(h["lower"][0], "creak", h["lower"][1] - h["lower"][0], 0.05, 0.0)
    track.hit(h["lower"][1], "wood_thud", 45, 0.12, 0.0)
    track.hit(h["unhook"][0] + 0.2, "plink", 70, 0.05, 0.0)
    for name in ("cut", "turn", "carve", "fit", "plant"):
        a, _ = L.at[name]
        track.fx(a - LN.MOVE, "marble_roll", LN.MOVE, 0.035, 0.0)
        track.hit(a, "clack", 51, 0.06, 0.0)
    c = L.cut
    track.fx(c["saw"][0], "saw", c["saw"][1] - c["saw"][0], 0.06, 0.0)
    track.hit(L.hoist2["drop"][1], "clack", 55, 0.04, 0.0)          # the hook on the offcut's eye bolt
    track.fx(L.hoist2["lift"][0], "slide", 1.2, 0.03, 0.0)
    u = L.turn
    track.fx(u["spin"][0], "marble_roll", u["spin"][1] - u["spin"][0], 0.05, 0.0)
    for q in range(int((u["run"][1] - u["run"][0]) / 0.5)):
        track.fx(u["run"][0] + q * 0.5, "sand_scrape", 0.4, 0.03, 0.15)
    ca = L.carve
    for q in range(int((ca["chisel"][1] - ca["chisel"][0]) / 0.3)):
        track.hit(ca["chisel"][0] + q * 0.3, "pluck", PENTA[q % 6], 0.04, 0.0)
    track.fx(ca["drill"][0], "saw", ca["drill"][1] - ca["drill"][0], 0.03, 0.1)
    track.fx(ca["brush"][0], "rustle", ca["brush"][1] - ca["brush"][0], 0.04, 0.0)
    for d in L.fit:
        track.hit(d["grip"][0] + 0.1, "plink", 68, 0.04, 0.0)
        track.hit(d["press"][1] - 0.1, "clack", PENTA[2], 0.08, 0.0)
    track.fx(L.paint["paint"][0], "rustle", L.paint["paint"][1] - L.paint["paint"][0], 0.03, 0.0)
    track.hit(P.tw_set[1], "plink", 72, 0.05, 0.0)
    o = P.orb
    track.fx(o[0][0], "creak", o[0][1] - o[0][0], 0.03, 0.2)
    track.hit(o[2], "plink", 75, 0.08, 0.0)
    track.hit(o[2] + 0.4, "plink", 80, 0.06, 0.0)
    track.hit(P.hop_down[1], "wood_thud", 48, 0.08, 0.0)
    # home: the dig, the acorn, the water, the tree
    pl = P.plant
    for sx in (-1, 1):
        for a in pl.dig.scrapes(sx, *pl.dig_t):
            track.fx(a, "sand_scrape", 0.4, 0.05, pan_at(a, pl.HOLE + sx * 60))
    for a, b in pl.pats:
        track.fx(b, "sand_thump", 0.2, 0.04, pan_at(a, pl.HOLE))
    track.hit(pl.drop_land, "pluck", 60, 0.07, pan_at(pl.drop_land, pl.HOLE))
    track.fx(pl.water[0] + 0.6, "sand_patter", pl.water[1] - pl.water[0] - 1.0, 0.04, pan_at(pl.water[0], pl.HOLE))
    track.hit(pl.grow[1] - 0.4, "plink", 72, 0.05, 0.0)
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
