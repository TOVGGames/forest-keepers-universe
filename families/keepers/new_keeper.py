"""Forest Keepers: A New Friend from the Factory (docs/engines/forest_keepers_factory_trip.md). Owner 2026-11-03: "Another
trip to the night shift factory, I want twigs to have hands and can also have retractable blades. Maybe make a 7th
keeper"; he picked Sprout and approved the storyboard (6 stills incl. the opening hook).

  NK_TRIP - the village at night. The narrator's hook first ("...and at the very end, a brand-new Keeper plants its
            very first tree"). Twigs trims a dead branch with his wrist saw, but when he tries to pick up an acorn
            from the stump the saw only nudges it and it rolls away. Twigs: "?". Glo has an idea (sparkle): back to
            the factory. They walk to the hill door and in.
  NK_HALL - the night-shift factory. Twigs steps onto a pallet; the orb trolley lifts his orb out and he falls asleep,
            pale grey. UNCLIP takes off each wrist saw into the OLD bin, FIT brings each new hand from the NEW tray and
            slides it on, and taps each sheath: the blade slides out and back in. His orb goes back in; he wiggles his
            new fingers. Then the hoist lowers an oak log onto the jig: CUT trims it to length, TURN spins it into the
            acorn body (curly shavings), CARVE cuts the cap's scales and the orb socket and stains the cap, FIT adds the
            root legs, the little hand with its acorn, the other hand and the face, one at a time. Twigs' first
            job with his hands: he plants the seedling in Sprout's cap. The trolley brings the new seventh orb: it
            drops in, flashes the Forest Keeper badge, green floods out from it and Sprout opens its eyes and waves.
            Name card. Everyone goes out through the roll-up door.
  NK_HOME - back in the forest: Twigs slides one blade out, trims a dead branch and slides it back in. Digs digs a
            little hole, Sprout drops its acorn in, Digs covers it, Sprout waters it and a tiny two-leaf sprout comes
            up: Sprout's very first tree (the hook's payoff). End sign with seven Keepers.

Same rules as the Tune-Up: nothing about a Keeper changes while it's awake (orb out first), a visible machine does
every step, carried pieces stay in their layer the whole way, nobody walks through a wall or through each other.
Sprout's pronoun is "it" (owner 2026-11-03); the narration happens not to need one.
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, Jump, lerp, rect, seg, smoothstep, smootherstep, tree
from families.foundry.keepers.halloween import hops, path
from families.foundry.products.monster import (ACORN, BARK_C, CAP, CLAW, PALE, WOOD, Monster, Xform, acorn_nut,
                                               ellipse, lighten, seedling)
from families.foundry.style import CABLE, FAR, FLOOR, IRON, MID, STEEL
from families.foundry.tree_monsters import HAZARD, INTERIOR, LAMP, SAWDUST, SIGN_WARM, machine_block, saw_blade

from . import narrator as NR
from .animal_houses import G
from .bug_hunt import CARD, INK, WOOD as CARD_WOOD
from .book import clipped
from .doorway import DEPTH_T, Doorway, depth_in, depth_out, half_width
from .harvest_feast import cam_keys, px
from .tune_up import (BIN, BUSH, GLO_UP, PLANK_C, STAR, WALK, Route, TuneAct, VillageAct, bump, curled_hog,
                      loose_orb)

HOOK = "Tonight, the Forest Keepers go back to the night-shift factory. And at the very end, a brand-new Keeper " \
       "plants its very first tree."
MEET = "This is Sprout, the seventh Forest Keeper."
FINALE = "And there it is: Sprout's very first tree. Goodnight, forest."
SIGNOFF = "What should the Keepers build next? Tell us in the comments."
CARD_LINES = ("Sprout", ["The seventh Forest Keeper, the gardener:", "plants a new tree for every branch Twigs trims."])

STEM = np.array([96, 150, 70], np.float64)
SOIL = np.array([70, 52, 38], np.float64)
POT = np.array([170, 96, 62], np.float64)
STAIN = np.array([110, 74, 44], np.float64)
CHAIN = np.array([120, 124, 132], np.float64)
CURL = np.array([214, 184, 140], np.float64)        # turning shavings: pale inner wood
TREE_X = 3900.0                                    # the oak by the hill (village tree from episode 4 on)


def twig_point(m, t, side, lift, reach=26.0, dy=0.0):
    """Twigs' wrist-saw centre / the point between the fingers of his hand on `side` with that arm lifted by `lift`
    (punch), at act time t, with the same arm maths as Monster._teeth_arm. -> (x, y, ux, uy) (forearm direction)."""
    k, a = m.k, m.alive
    keep = (m.punch, m.punch_l)
    if side > 0:
        m.punch = lift
    else:
        m.punch_l = lift
    sway = a * 4 * math.sin(t * 1.1) * k
    cy = m.y - 350 * k + sway * 0.3 + dy
    sh, el, hd = m._teeth_arm(side, t, m.x + sway, cy)
    m.punch, m.punch_l = keep
    ax, ay = hd[0] - el[0], hd[1] - el[1]
    L = math.hypot(ax, ay) + 1e-9
    return hd[0] + ax / L * reach * k, hd[1] + ay / L * reach * k, ax / L, ay / L


def probe(kind, k, x, y, alive=1.0, **kw):
    """A stand-in Monster for working out where a hand will be (the scene's own isn't placed yet)."""
    m = Monster(kind, k)
    m.newlook, m.x, m.y, m.alive = True, x, y, alive
    for a, v in kw.items():
        setattr(m, a, v)
    return m


def fall_y(y0, tau):
    return y0 + 0.5 * GRAVITY * tau * tau


class NewKeeperAct(TuneAct):
    """Every act of the episode: the new look for all, Twigs' saws until the factory gives him hands; Sprout only
    exists once the factory has built it (the trip has six Keepers)."""

    def present(self):
        return [m.kind for m in self.s.monsters if m.kind != "sprout"]

    @property
    def quiet(self):
        q = super().quiet
        if "sprout" not in self.present():
            q.append("sprout")
        return q

    def look_new(self, m, **kw):
        self.new_look(m, flash=kw.pop("flash", 0.0), smile=kw.pop("smile", 0.65))
        for a, v in kw.items():
            setattr(m, a, v)


# ====================================================================== NK_TRIP: the village -> the factory door

class NKTripAct(NewKeeperAct, VillageAct):
    name = "nk_trip"
    LEAD = 9.0
    names = (0.8 - LEAD, 7.5 - LEAD)
    TW = 3570.0                                    # Twigs' spot under the dead branch
    START = {"digger": 2050.0, "wheels": 2340.0, "springs": 2600.0, "tentacles": 2900.0, "lantern": 3250.0,
             "teeth": TW}
    IN_ORDER = ["teeth", "lantern", "tentacles", "springs", "wheels", "digger"]     # front first: nobody passes
    SAW = (3.0, 4.2, 6.2)                          # lift the saw and run it up, saw through, the piece drops
    NUDGE = (9.0, 10.0)                            # reach for the acorn, the saw touches it
    P_CUT, P_NUDGE = 0.85, 0.25
    GLO_TO = 3380.0

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        k = scene.k
        tw = probe("teeth", k, self.TW, G, saws=True)
        cx, cy, _, _ = twig_point(tw, self.SAW[1] + 1.0, 1, self.P_CUT)
        self.cut = (cx, cy)
        self.branch = [(TREE_X - 22, cy - 0.07 * (TREE_X - 22 - cx)), (cx - 135, cy + 0.07 * 135)]
        nx, ny, _, _ = twig_point(tw, self.NUDGE[1], 1, self.P_NUDGE)
        self.acorn_r = 10.0
        self.acorn0 = (nx + 30 * k + self.acorn_r, ny)                 # just right of the saw's edge
        self.stump = (self.acorn0[0] + 18, self.acorn0[1] + self.acorn_r, 48.0)   # (x, top, half width)
        self.go = 17.0
        self.wait, x, prev = {}, 4440.0, None             # the queue at the door: nobody's arms overlap
        for k_ in self.IN_ORDER:
            if prev is not None:
                x -= gap(prev, k_, k)
            self.wait[k_], prev = x, k_
        self.leave = {k_: self.go + 0.3 * q for q, k_ in enumerate(self.IN_ORDER)}
        self.route = {}
        for k_ in self.IN_ORDER:
            r = Route(self.START[k_], -self.LEAD)
            if k_ == "lantern":
                r.wait(12.5).go(self.GLO_TO, v=110)
            r.wait(self.leave[k_]).go(self.wait[k_], v=WALK)
            self.route[k_] = r
        self.arrive = {k_: self.route[k_].t for k_ in self.IN_ORDER}
        self.door = (self.arrive["teeth"] - 2.5, self.arrive["teeth"] + 0.5)
        self.enter, self.at_door, last, last_door = {}, {}, self.door[1], -1e9
        for k_ in self.IN_ORDER:
            walk = Route(self.wait[k_]).go(self.x_in, v=170).t
            last = self.enter[k_] = max(last + 1.0, self.arrive[k_] + 0.5, last_door + 2.4 - walk)
            self.route[k_].wait(self.enter[k_]).go(self.x_in, v=170)
            last_door = self.at_door[k_] = self.route[k_].t
        self.inside = {k_: self.at_door[k_] + DEPTH_T for k_ in self.IN_ORDER}
        self.dur = max(self.inside.values()) + 1.5
        NR.say(self, 1.0 - self.LEAD, HOOK)

    # ----- the cut branch piece and the acorn -----

    def piece(self, t):
        """The cut-off end of the dead branch: (x0, y0, x1, y1) or None before the cut."""
        (ax, ay), (bx, by) = self.branch
        cx, cy = self.cut
        yc = ay + (by - ay) * (cx - ax) / (bx - ax)
        if t < self.SAW[2]:
            return None
        tau = t - self.SAW[2]
        land = math.sqrt(2 * (G - 8 - max(yc, by)) / GRAVITY)
        d = fall_y(0, min(tau, land))
        tilt = 8.0 * smoothstep(min(1.0, tau / max(land, 1e-3)))
        return cx, yc + d, bx, by + d + tilt

    def acorn_at(self, t):
        """The acorn: on the stump, nudged by the saw it rolls off the far edge, drops into the grass and rolls a
        little way towards the tree. -> (x, y, roll angle)."""
        x0, y0 = self.acorn0
        r = self.acorn_r
        sx, top, hw = self.stump
        t0 = self.NUDGE[1]
        if t < t0:
            return x0, y0, 0.0
        edge = sx + hw + r * 0.3
        T1 = 0.7                                       # rolling across the stump top
        if t < t0 + T1:
            u = (t - t0) / T1
            x = lerp(x0, edge, u * (2 - u) * 0.5 + u * 0.5)
            return x, y0, (x - x0) / r
        v = (edge - x0) / T1 * 0.8
        land = math.sqrt(2 * (G - r - y0) / GRAVITY)
        tau = t - t0 - T1
        if tau < land:
            x = edge + v * tau
            return x, fall_y(y0, tau), (x - x0) / r
        xl = edge + v * land
        T2 = 1.4                                       # rolls on in the grass, slowing down
        u = min(1.0, (tau - land) / T2)
        x = xl + v * T2 * 0.5 * (2 * u - u * u)
        return x, G - r, (x - x0) / r

    def props(self, t):
        return {}

    # ----- camera -----

    def target(self, t):
        g, a = self.go, self.arrive
        keys = [(-self.LEAD, 2760.0, None, 0.85), (-6.0, 2760.0, None, 0.85), (2.0, 3640.0, None, 1.25),
                (12.0, 3640.0, None, 1.25), (15.0, 3500.0, None, 1.08), (g, 3500.0, None, 1.0),
                (a["wheels"], 3980.0, None, 0.95), (self.enter["springs"], 4250.0, None, 1.0),
                (self.dur, 4400.0, None, 1.0)]
        return cam_keys(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        tw = self.m("teeth")
        for kind in self.IN_ORDER:
            m = self.m(kind)
            if m is None:
                continue
            dy, y = 0.0, (G - GLO_UP if kind == "lantern" else G)
            u = depth_in(t, self.at_door[kind]) if t > self.at_door[kind] else 0.0
            self.door_depth[kind] = u
            if u > 0.0:                                   # in through the door, away from the camera
                if kind == "springs":
                    ph = ((t - self.at_door[kind]) / 0.55) % 1.0
                    dy, m.spring = -4 * 40 * ph * (1 - ph), 0.0
                self.doorway.walking(self, m, t, dt, u, y, dy)
                self.look_new(m)
                continue
            if kind == "springs":
                x, lift, sq = hops(self.START[kind], self.wait[kind], self.leave[kind], self.arrive[kind], t,
                                   apex=55, step=170)
                if t >= self.enter[kind]:
                    x, lift, sq = hops(self.wait[kind], self.x_in, self.enter[kind], self.at_door[kind], t, apex=50,
                                       step=170)
                if t < self.leave[kind]:
                    x = self.START[kind]
                dy, m.spring = -lift, sq
            else:
                x = self.route[kind].at(t)
            self.place(m, x, t, dt, y=y, dy=dy)
            self.look_new(m)
        if tw is not None:
            self._twigs(tw, t, dt)
        if self.m("sprout") is not None:
            self.door_depth["sprout"] = 0.0
        self.fireflies()
        self._sounds(t)

    def _twigs(self, m, t, dt):
        s0, s1, s2 = self.SAW
        n0, n1 = self.NUDGE
        lift = 0.0
        if t < s2 + 1.4:
            lift = self.P_CUT * smootherstep(seg(t, s0, s1)) * (1 - smootherstep(seg(t, s2 + 0.3, s2 + 1.4)))
            if s1 <= t < s2:
                lift += 0.03 * math.sin((t - s1) * 2 * math.pi * 1.6)      # sawing to and fro a little
        elif t < n1 + 1.8:
            lift = self.P_NUDGE * smootherstep(seg(t, n0, n1)) * (1 - smootherstep(seg(t, n1 + 0.6, n1 + 1.8)))
        m.punch = lift
        m.saws, m.hands = True, False
        run = smoothstep(seg(t, s0 + 0.4, s0 + 1.0)) * (1 - smoothstep(seg(t, s2 + 0.1, s2 + 0.9)))
        m.saw_run = run
        m.saw_spin += dt * 28 * run
        m.brow = -0.6 * smoothstep(seg(t, n1 + 1.6, n1 + 2.2)) * (1 - smoothstep(seg(t, 14.6, 15.4)))
        if m.brow < -0.05:
            m.smile = 0.25
        p = self.s.particles
        if s1 <= t < s2 and p.rng.uniform() < 0.7:
            p.burst(self.cut[0], self.cut[1] + 6, 2, SAWDUST * 1.05, 160, 0.9, 4.0, g=600, spread=1.0,
                    direction=math.pi / 2)

    def aside_moods(self, t):
        return [] if t < self.go + 1.0 else ["mm", "ooh", "hm"]

    def _sounds(self, t):
        s0, s1, s2 = self.SAW
        if self.crossed(s0 + 0.4):
            self.fx(s0 + 0.4, "saw", s2 - s0 + 0.2, 0.08, self.cut[0], self.cut[1])
        if self.crossed(s2 + 0.45):
            self.hit(s2 + 0.45, "thud", 48, 0.14, self.cut[0] - 60, G)
        if self.crossed(s2 + 1.6):
            self.chat(s2 + 1.6, "teeth", "hehe")
        n1 = self.NUDGE[1]
        if self.crossed(n1):
            self.hit(n1, "clack", 72, 0.1, *self.acorn0)
        if self.crossed(n1 + 0.95):
            self.hit(n1 + 0.95, "pluck", 64, 0.1, self.stump[0] + 60, G)
        if self.crossed(n1 + 2.0):
            self.chat(n1 + 2.0, "teeth", "q", icon="?")
        if self.crossed(14.6):
            self.chat(14.6, "lantern", "idea", icon="sparkle")
        if self.crossed(15.6):
            self.chorus(15.6, ["wheels", "springs", "digger", "tentacles"], "yay", gap=0.25)
        if self.crossed(16.3):
            self.chat(16.3, "teeth", "hehe", icon="orb")
        if self.crossed(self.door[0]):
            self.fx(self.door[0], "motor", self.door[1] - self.door[0], 0.4, self.hill.d0, G - 300)
        if self.crossed(self.door[1]):
            self.hit(self.door[1], "clunk", 45, 0.35, self.hill.d0, G - 500)
        for kind in self.IN_ORDER:
            if self.crossed(self.enter[kind] + 0.3):
                self.chat(self.enter[kind] + 0.3, kind, "wee" if kind == "springs" else "mm", icon=None)

    def bunny_st(self, t):
        """The bunny peeks out from behind the bush to watch the sawing, then hops back."""
        out, back, n, d = 4.6, 12.6, 2, 0.5
        x0, x1 = BUSH[0] + 10, BUSH[0] + 150
        for a, b, f in ((out, x1, 1), (back, x0, -1)):
            u = (t - a) / (n * d)
            if 0 <= u < 1:
                k_, ph = int(u * n), u * n - int(u * n)
                start = x0 if f > 0 else x1
                return lerp(start, b, (k_ + ph) / n), 4 * 26 * ph * (1 - ph), f
        if out + n * d <= t < back:
            return x1, 3 * max(0.0, math.sin(t * 2.3)) ** 8, -1
        return x0, 0.0, -1

    def hog_st(self, t):
        x = 3150.0 + 18 * math.sin(t * 0.25)
        return x, (1 if math.cos(t * 0.25) > 0 else -1), 0.0

    def draw(self, c, t):
        door = seg(t, *self.door)
        self.scene_draw(c, t, door, self.bunny_st(t), self.hog_st(t))

    def scene_draw(self, c, t, door, bunny_st, hog_st):
        """The village (tune_up's), with the dead branch on the oak, the stump and its acorn drawn behind the
        Keepers."""
        s = self.s
        self.backdrop(c, t)
        for j, x in enumerate((-300, 300, TREE_X)):
            if s.visible(x - 260, x + 260):
                tree(c, x, G, 640 + 60 * (j % 3), 950 + j)
        self._branch(c, t)
        self.hill.back(c, s, t, door)
        from families.foundry.keepers.common import bunny
        bx, hop, face = bunny_st
        if s.visible(bx - 80, bx + 80):
            bunny(c, bx, G, 1.5, hop, face)
        self.bush(c)
        self.draw_village(c, t, peek=1.0)
        hx, face, curl = hog_st
        if s.visible(hx - 80, hx + 80):
            curled_hog(c, hx, G, 1.45, face, curl, t)
        self._stump(c, t)
        self.glo_light(c, k=0.8)
        self.doorway.draw_inside(self, c, t, self.door_depth)
        self.hill.front(c, s, t, door)
        self.draw_monsters(c, t, kinds=self.outside())

    def _branch(self, c, t):
        (ax, ay), (bx, by) = self.branch
        cx, _ = self.cut
        yc = ay + (by - ay) * (cx - ax) / (bx - ax)
        col = BARK_C * 1.05
        c.line(ax, ay, cx, yc, col, 13)                   # the part left on the tree
        c.line(lerp(ax, cx, 0.45), lerp(ay, yc, 0.45), lerp(ax, cx, 0.45) - 26, lerp(ay, yc, 0.45) - 40, col, 6)
        pc = self.piece(t)
        if pc is None:
            pc = (cx, yc, bx, by)
        x0, y0, x1, y1 = pc
        c.line(x0, y0, x1, y1, col, 11)
        c.line(lerp(x0, x1, 0.6), lerp(y0, y1, 0.6), lerp(x0, x1, 0.6) - 18, lerp(y0, y1, 0.6) - 34, col, 5)
        if t >= self.SAW[2]:
            c.circle(cx, yc, 6, lighten(WOOD, 1.25))       # the fresh cut end

    def _stump(self, c, t):
        sx, top, hw = self.stump
        c.polygon([(sx - hw, G + 4), (sx + hw, G + 4), (sx + hw * 0.92, top + 6), (sx - hw * 0.92, top + 6)], BARK_C)
        c.polygon(ellipse(sx, top + 6, hw * 0.92, 9, 28), lighten(WOOD, 1.2))
        for f in (0.35, 0.7):
            c.polyline(ellipse(sx, top + 6, hw * 0.92 * f, 9 * f, 24), WOOD, 1.5, closed=True)
        x, y, ang = self.acorn_at(t)
        cc = Xform(c, 0, 0, ang, 1.0, x, y)
        acorn_nut(cc, x, y, self.acorn_r)


# ====================================================================== NK_HALL: the night-shift factory

PY = G - 40.0                                   # pallet top: feet on the line
FY = G + 60.0                                   # the walkway in front of the line
SLOT = 560.0
TS = [1300.0 + SLOT * i for i in range(3)]      # Twigs: ORB OUT, UNCLIP, FIT (his orb goes back in at FIT)
LS = [3000.0 + SLOT * i for i in range(6)]      # Sprout: the hoist, CUT, TURN, CARVE, FIT, PLANT (and orb in)
RAIL_Y = G - 780.0
BEAM_Y = G - 640.0
ENTRY = (-900.0, -440.0)
EXIT = (6380.0, 6840.0)
HALL = (-2000.0, 8000.0)
ROW = ["lantern", "tentacles", "springs", "wheels", "digger"]      # the watchers, right (nearest the work) first


def gap(a, b, m_k=0.55):
    from .doorway import HALF_W
    return (HALF_W.get(a, 200.0) + HALF_W.get(b, 200.0)) * m_k + 18.0


class NKHallAct(NewKeeperAct):
    name = "nk_hall"
    indoor = True
    names = (-9.0, -8.0)
    M = 3.4                                      # the line moves one slot
    W_U, W_F = 10.0, 15.6                        # Twigs at UNCLIP / FIT
    W_CUT, W_TURN, W_CARVE, W_FIT = 10.0, 11.0, 14.0, 22.0

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.mk = scene.k
        self.way_in = Doorway(ENTRY[0], ENTRY[1], FY, FY - (G - 520), rise=130.0)
        self.way_out = Doorway(EXIT[0], EXIT[1], FY, FY - (G - 520), rise=130.0)
        self.lamps = list(np.arange(HALL[0] + 350, HALL[1], 700))
        self._orb_at = {}
        self._plan()

    # ----- the plan -----

    def _plan(self):
        k = self.mk
        M = self.M
        IN = ["teeth"] + ROW
        self.in_door = {kd: 1.0 + 1.8 * j for j, kd in enumerate(IN)}
        R = {kd: Route(self.way_in.xc, self.in_door[kd] + DEPTH_T) for kd in IN}
        R["teeth"].go(TS[0], v=160)
        self.twigs_on = R["teeth"].t + 0.4
        self.R = R
        self._row(TS[0] - 120 - 83 * k / 0.55 - 30, 0.0, first=True)
        self.settle = max(max(r.t for r in R.values()), self.twigs_on + 1.0) + 1.0
        # Twigs: orb out, UNCLIP, FIT, orb in
        self.O = self.settle + 3.0
        self.T1 = self.O + 8.0
        self.U0 = self.T1 + M + 2.5
        self.T2 = self.U0 + self.W_U
        self.F0 = self.T2 + M + 2.0
        self.I0 = self.F0 + self.W_F + 0.4
        self.WAKE = self.I0 + 6.0
        self.D0 = self.I0 + 10.6                   # Twigs hops down off his pallet
        self._row(TS[1] - 244, self.T1)
        self._row(TS[2] - 244, self.T2)
        tw = probe("teeth", k, TS[2], FY)
        self.twigs_jump = Jump(TS[2], PY, TS[2] + 60, FY, apex=40)
        self.twigs_land = self.D0 + self.twigs_jump.dur
        R["teeth"] = Route(TS[2] + 60, self.twigs_land)
        # Sprout: the hoist, then the log line
        self.H0 = self.D0 + 3.0
        self.H1 = self.H0 + 6.0                    # the log sits on the jig
        self.LM = [self.H1 + 3.5]                  # line moves (to CUT, TURN, CARVE, FIT, PLANT)
        self.LW = [self.W_CUT, self.W_TURN, self.W_CARVE, self.W_FIT]
        self.LW0 = []
        for w in self.LW:
            self.LW0.append(self.LM[-1] + M + 1.5)
            self.LM.append(self.LW0[-1] + w)
        self.P0 = self.LM[-1] + M                  # at PLANT
        self._row_all(LS[0] - 244, self.D0 + 1.4)
        for j in range(4):
            self._row_all(LS[j + 1] - 244, self.LM[j])
        # PLANT: Twigs climbs the step, takes the seedling from the arm, plants it in the cap
        self._plant_plan()
        self._row_all(self.step_x, self.LM[4], skip=("teeth",))
        # the seventh orb, the wake, the card
        self.I1 = self.PL["done"] + 1.0
        self.WAKE_S = self.I1 + 6.0
        self.CARD = (self.WAKE_S + 3.5, self.WAKE_S + 3.5 + max(9.0, self.meet_d + 3.0))
        self.SD = self.CARD[1] + 1.0               # Sprout hops down
        self.sprout_jump = Jump(LS[5], PY, LS[5] + 80, FY, apex=40)
        self.sprout_land = self.SD + self.sprout_jump.dur
        self._exit_plan()
        self._trolley_keys()
        self.stats = {"orbs_out": 1, "orbs_in": 2, "stations": ["UNCLIP", "FIT", "CUT", "TURN", "CARVE", "FIT",
                                                                "PLANT"]}

    def _row(self, anchor, t, first=False, skip=()):
        """Line the watchers up on the walkway from `anchor` (the right end) leftwards, setting off at t."""
        x = anchor
        prev = None
        for j, kd in enumerate(ROW):
            if prev is not None:
                x -= gap(prev, kd, self.mk)
            prev = kd
            if kd in skip:
                continue
            r = self.R[kd]
            r.wait(t + 0.35 * j).go(x, v=160)

    def _row_all(self, anchor, t, skip=()):
        """The same with Twigs back in the row (on the right, nearest the work)."""
        x = anchor
        if "teeth" not in skip:
            self.R["teeth"].wait(t).go(x, v=160)
        prev = "teeth"
        for j, kd in enumerate(ROW):
            x -= gap(prev, kd, self.mk)
            prev = kd
            self.R[kd].wait(t + 0.35 * (j + 1)).go(x, v=160)

    def _plant_plan(self):
        """Where Twigs stands on the step so his right hand reaches the hole in Sprout's cap, and when."""
        k = self.mk
        P0 = self.P0
        hole = (LS[5], PY - 260 * k)
        self.hole = hole
        t_up = self.LM[4]                           # Twigs sets off for the step with the line move
        rel = P0 + 9.5                              # a first guess at when he lets go of the seedling
        R = self.R["teeth"]
        for _ in range(2):                          # solve the reach at the release time, then again
            best = None
            for p in np.linspace(0.2, 2.3, 421):
                tw = probe("teeth", k, 0.0, FY, hands=True)
                x, y, _, _ = twig_point(tw, rel, 1, p)
                if best is None or abs(y - hole[1]) < abs(best[1] - hole[1]):
                    best = (p, y, x)
            self.p_hole = best[0]
            self.step_x = hole[0] - best[2]
            walk = Route(R.x, t_up).go(self.step_x, v=150)
            take = walk.t + 0.3 + 4.2
            rel = take + 3.4 + 0.4
        self.p_take = max(0.1, self.p_hole - 0.5)
        R.wait(t_up).go(self.step_x, v=150)
        walk_end = R.t
        on = walk_end + 0.3
        self.PL = dict(walk_end=walk_end, on=on, take=on + 4.2)
        self.PL["lift"] = (self.PL["take"] + 0.8, self.PL["take"] + 3.4)
        self.PL["release"] = self.PL["lift"][1] + 0.4
        self.PL["done"] = self.PL["release"] + 1.6
        self.PL["down"] = self.PL["done"] + 0.4
        tw = probe("teeth", k, self.step_x, FY, hands=True)
        x, y, _, _ = twig_point(tw, self.PL["release"], 1, self.p_hole)
        self.hand_err = (round(x - hole[0], 1), round(y - hole[1], 1))
        self.meet_d = 0.0

    def _exit_plan(self):
        k = self.mk
        order = ["sprout", "teeth"] + ROW
        xq = {}
        x = EXIT[0] - 140.0
        prev = None
        for kd in order:
            if prev is not None:
                x -= gap(prev, kd, k)
            prev = kd
            xq[kd] = x
        self.queue_x = xq
        t0 = self.sprout_land + 0.6
        self.R["sprout"] = Route(LS[5] + 80, self.sprout_land).wait(t0).go(xq["sprout"], v=140)
        self.R["teeth"].wait(max(self.PL["down"] + 0.5, t0 + 0.4)).go(xq["teeth"], v=140)
        for j, kd in enumerate(ROW):
            self.R[kd].wait(t0 + 0.4 * (j + 2)).go(xq[kd], v=140)
        self.door = (max(r.t for r in self.R.values()) - 3.0, max(r.t for r in self.R.values()))
        self.exit_t, self.at_exit, last, last_door = {}, {}, self.door[1], -1e9
        for kd in order:
            walk = Route(xq[kd]).go(self.way_out.xc, v=170).t
            last = self.exit_t[kd] = max(last + 1.1, self.R[kd].t + 0.5, last_door + 2.4 - walk)
            self.R[kd].wait(last).go(self.way_out.xc, v=170)
            last_door = self.at_exit[kd] = self.R[kd].t
        self.gone = {kd: self.at_exit[kd] + DEPTH_T for kd in order}
        self.dur = max(self.gone.values()) + 1.5
        # the narrator meets Sprout over the name card
        self.meet_d = NR.say(self, self.CARD[0] + 0.6, MEET)

    # ----- the line -----

    def twigs_pallet(self, t):
        u = smootherstep(seg(t, self.T1, self.T1 + self.M)) + smootherstep(seg(t, self.T2, self.T2 + self.M))
        return TS[0] + SLOT * u

    def log_pallet(self, t):
        u = sum(smootherstep(seg(t, a, a + self.M)) for a in self.LM)
        return LS[0] + SLOT * u

    def log_y(self, t):
        """Sprout's feet (the jig's seat): lowered by the hoist from the loft onto the pallet."""
        u = smootherstep(seg(t, self.H0, self.H1))
        return lerp(PY - 1100.0, PY, u)

    # ----- the orb trolley (two cups: the new seventh orb, then Twigs' while it's out) -----

    def _trolley_keys(self):
        """The trolley rides along with the work, slowly: to Twigs' first slot, with him down the line, then over
        to the PLANT slot while Sprout is being built."""
        o = self.O
        x0 = TS[0] - 400.0
        self.tkeys = [(0.0, x0), (o - 2.0, x0), (o + 1.8, TS[0]), (o + 7.2, TS[0]), (self.T2 + self.M, TS[2]),
                      (self.LM[2], TS[2]), (self.LM[4] + self.M, LS[5])]

    def trolley_x(self, t):
        return px(self.tkeys, t)

    CUP = {"sprout": -20.0, "teeth": 20.0}

    def gripper(self, t):
        """(x, y, holding kind or None) of the trolley's gripper."""
        tx = self.trolley_x(t)
        top = RAIL_Y + 66
        o = self.O
        if o + 1.8 <= t < o + 7.0:                         # Twigs' orb out
            ox, oy = self.grab_xy("teeth", t)
            if t < o + 3.3:
                return tx, lerp(top, oy, smootherstep(seg(t, o + 1.8, o + 3.3))), None
            if t < o + 3.7:
                return tx, oy, None
            if t < o + 5.5:
                return tx, lerp(oy, top, smootherstep(seg(t, o + 3.7, o + 5.5))), "teeth"
            cx = tx + self.CUP["teeth"]
            if t < o + 6.3:
                return lerp(tx, cx, smootherstep(seg(t, o + 5.5, o + 6.3))), top, "teeth"
            return lerp(cx, tx, smootherstep(seg(t, o + 6.3, o + 7.0))), top, None
        for kd, i0 in (("teeth", self.I0), ("sprout", self.I1)):
            if i0 + 1.6 <= t < i0 + 5.0:
                cx = tx + self.CUP[kd]
                if t < i0 + 2.0:
                    return lerp(tx, cx, smootherstep(seg(t, i0 + 1.6, i0 + 2.0))), top, None
                if t < i0 + 2.6:
                    return lerp(cx, tx, smootherstep(seg(t, i0 + 2.1, i0 + 2.6))), top, kd
                ox, oy = self.m(kd).orb_now(t)
                if t < i0 + 3.9:
                    return tx, lerp(top, oy, smootherstep(seg(t, i0 + 2.6, i0 + 3.9))), kd
                if t < i0 + 4.1:
                    return tx, oy, None
                return tx, lerp(oy, top, smootherstep(seg(t, i0 + 4.1, i0 + 5.0))), None
        return tx, top, None

    def grab_xy(self, kd, t):
        if t >= self.O + 3.7 and kd in self._orb_at:
            return self._orb_at[kd]
        return self.m(kd).orb_now(t)

    def in_rack(self, kd, t):
        if kd == "sprout":
            return t < self.I1 + 2.0
        return self.O + 6.3 <= t < self.I0 + 2.0

    def alive(self, kd, t):
        if kd not in ("teeth", "sprout"):
            return 1.0
        if kd == "sprout":
            return smoothstep(seg(t, self.I1 + 4.2, self.I1 + 5.9))
        o = self.O
        if t < o + 3.7:
            return 1.0
        if t < self.I0 + 4.2:
            return 1.0 - smoothstep(seg(t, o + 3.7, o + 5.2))
        return smoothstep(seg(t, self.I0 + 4.2, self.I0 + 5.9))

    def orb_in(self, kd, t):
        if kd not in ("teeth", "sprout"):
            return 1.0
        if kd == "sprout":
            return 0.0 if t < self.I1 + 3.9 else 1.0
        return 0.0 if self.O + 3.7 <= t < self.I0 + 3.9 else 1.0

    # ----- the stations' tools -----

    def idle_xy(self, sx):
        return sx, BEAM_Y + 90.0

    def twigs_tool(self, t):
        """The UNCLIP / FIT arm working on Twigs: (station x, x, y, carrying) or None."""
        m = self.m("teeth")
        if self.U0 <= t < self.U0 + self.W_U:
            u, sx = t - self.U0, TS[1]
            ix, iy = self.idle_xy(sx)
            bx, by = self.old_bin()
            r = m.saw_center(1, t)
            l_ = m.saw_center(-1, t)
            keys = [(0.0, ix, iy), (1.0, *r), (1.2, *r), (3.2, bx, by - 50), (3.6, bx, by - 50), (4.8, *l_), (5.0, *l_),
                    (7.0, bx, by - 50), (7.4, bx, by - 50), (8.6, ix, iy)]
            x, y, _ = path(keys, u)
            item = "saw" if (1.2 <= u < 3.6 or 5.0 <= u < 7.4) else None
            return sx, x, y, item
        if self.F0 <= t < self.F0 + self.W_F:
            u, sx = t - self.F0, TS[2]
            ix, iy = self.idle_xy(sx)
            (r0x, r0y), (l0x, l0y) = self.tray_hands()
            r = self.wrist(1, t)
            l_ = self.wrist(-1, t)
            sr, sl = self.sheath(1, t), self.sheath(-1, t)
            keys = [(0.0, ix, iy), (1.8, r0x, r0y), (2.2, r0x, r0y), (4.2, *r), (4.6, *r), (5.4, l0x, l0y),
                    (5.8, l0x, l0y), (7.4, *l_), (7.8, *l_), (8.6, sr[0] + 30, sr[1] - 10), (9.0, *sr),
                    (9.3, sr[0] + 30, sr[1] - 10), (11.6, sl[0] - 30, sl[1] - 10), (12.0, *sl),
                    (12.3, sl[0] - 30, sl[1] - 10), (15.0, ix, iy)]
            x, y, _ = path(keys, u)
            item = "hand" if (2.2 <= u < 4.6 or 5.8 <= u < 7.8) else None
            return sx, x, y, item
        return None

    def old_bin(self):
        return TS[1] + 240.0, G + 18.0

    def tray_hands(self):
        """Where the two new hands lie on the NEW tray (the grip point: the palm)."""
        x, y = TS[2] + 240.0, G - 4.0
        return (x - 40, y - 34), (x + 40, y - 34)

    def wrist(self, side, t):
        m = self.m("teeth")
        x, y, _, _ = twig_point(m, t, side, 0.0, reach=0.0)
        return x, y

    def sheath(self, side, t):
        m = self.m("teeth")
        k = m.k
        sway = m.alive * 4 * math.sin(t * 1.1) * k
        cy = m.y - 350 * k + sway * 0.3
        sh, el, hd = m._teeth_arm(side, t, m.x + sway, cy)
        ux, uy, nx, ny = m._blade_frame(hd, el, side)
        return hd[0] + nx * 22 * k - ux * 20 * k, hd[1] + ny * 22 * k - uy * 20 * k

    def twigs_state(self, m, t):
        """Twigs' wrists and blades through UNCLIP and FIT."""
        u = t - self.U0
        m.punch = m.punch_l = 0.0
        m.bare = set()
        m.saws, m.hands = True, False
        if t >= self.U0 + 1.2:
            m.bare.add(1)
        if t >= self.U0 + 5.0:
            m.bare.add(-1)
            m.saws, m.hands = False, True
        f = t - self.F0
        if t >= self.F0 + 4.6:
            m.bare.discard(1)
        if t >= self.F0 + 7.8:
            m.bare.discard(-1)
        m.blades = smootherstep(seg(f, 9.1, 9.8)) * (1 - smootherstep(seg(f, 10.4, 11.1)))
        m.blades_l = smootherstep(seg(f, 12.1, 12.8)) * (1 - smootherstep(seg(f, 13.4, 14.1)))
        w = self.WAKE
        m.grip = 0.0
        if w + 0.5 <= t < w + 4.5:                          # he wiggles his new fingers
            m.grip = 0.45 + 0.45 * math.sin((t - w - 0.5) * 2 * math.pi * 0.9 - math.pi / 2)
            m.punch = 0.4 * smoothstep(seg(t, w + 0.2, w + 1.0)) * (1 - smoothstep(seg(t, w + 4.0, w + 4.8)))
            m.punch_l = m.punch
        del u

    def log_tool(self, t):
        """(station index, local time) of the log line's work right now, or None."""
        for j, a in enumerate(self.LW0):
            if a <= t < a + self.LW[j]:
                return j, t - a
        return None

    # ----- Sprout's build state -----

    CUT_T = (1.0, 2.0, 5.2, 6.4, 8.6)   # saw down, across, saw away, push the offcut, done
    TURN_T = (1.0, 2.0, 8.6, 9.6)       # spin up + cutter in, cutting down, cutter out, spin down
    CARVE_T = dict(chisel=(1.0, 1.6, 5.6), socket=(6.4, 6.8, 8.2), brush=(9.0, 9.6, 12.6))
    FIT_PARTS = ["legs", "arm", "hand", "face"]

    def sprout_state(self, m, t):
        k = m.k
        m.log_top, m.turned, m.carved, m.stained, m.socket = 180.0, 0.0, 0.0, 0.0, 0.0
        m.attach = {p: 0.0 for p in ("legs", "arm", "hand", "face", "seed")}
        m.part_dxy = {}
        m.acorn, m.water, m.wave, m.hold_out = True, 0.0, 0.0, 0.0
        a = self.LW0
        c0 = a[0]
        if t >= c0 + self.CUT_T[1] + 0.0:
            m.log_top = 180.0 if t < c0 + self.CUT_T[2] else 0.0
        t0 = a[1]
        if t >= t0:
            u = seg(t, t0 + self.TURN_T[1], t0 + self.TURN_T[2])
            m.turned = u if u < 1 else 1.0
            m.spin = 9.0 * (min(t, t0 + self.TURN_T[3]) - t0)
        k0 = a[2]
        if t >= k0:
            ch, so, br = self.CARVE_T["chisel"], self.CARVE_T["socket"], self.CARVE_T["brush"]
            m.carved = seg(t, k0 + ch[1], k0 + ch[2])
            m.socket = seg(t, k0 + so[1], k0 + so[2])
            m.stained = seg(t, k0 + br[1], k0 + br[2])
        f0 = a[3]
        for j, p in enumerate(self.FIT_PARTS):
            g0 = f0 + j * 5.2
            if t >= g0 + 4.3:
                m.attach[p] = 1.0
            elif t >= g0 + 1.7:
                m.attach[p] = 0.5
                gx, gy = self.fit_tool(t)[1:3]
                ax, ay = self.grip_anchor(m, p)
                m.part_dxy[p] = (gx - ax, gy - ay)
            else:
                m.attach[p] = 0.5
                tx, ty = self.fit_tray(p)
                ax, ay = self.grip_anchor(m, p)
                m.part_dxy[p] = (tx - ax, ty - ay)
        pl = self.PL
        if t >= pl["release"] + 0.5:
            m.attach["seed"] = 1.0
        elif t >= pl["take"] - 3.6:
            m.attach["seed"] = 0.5
            sx_, sy_ = self.seedling_xy(t)
            ax, ay = self.grip_anchor(m, "seed")
            m.part_dxy["seed"] = (sx_ - ax, sy_ - ay)
        else:
            m.attach["seed"] = 0.5
            tx, ty = self.seed_tray()
            ax, ay = self.grip_anchor(m, "seed")
            m.part_dxy["seed"] = (tx - ax, ty - ay)
        if all(v >= 1.0 for v in m.attach.values()):
            m.attach = None
        w = self.WAKE_S
        m.wave = smoothstep(seg(t, w + 1.2, w + 2.0)) * (1 - smoothstep(seg(t, w + 6.0, w + 7.0)))
        del k

    def grip_anchor(self, m, p):
        """Where on the finished Sprout the machine holds part p (world)."""
        k, x, y = m.k, m.x, m.y
        return {"legs": (x + 38 * k, y - 60 * k), "arm": (x - 124 * k, y - 112 * k), "hand": (x + 124 * k, y - 112 * k),
                "face": (x, y - 164 * k), "seed": (x, y - 260 * k)}[p]

    def fit_tray(self, p):
        """Grip points of the parts waiting on the FIT tray (right of the station), resting on the tray top."""
        k = self.mk
        x0, top = LS[4] + 150.0, G - 30.0
        return {"face": (x0 + 22, top - 66 * k), "hand": (x0 + 125, top - 18 * k),
                "arm": (x0 + 205, top - 18 * k), "legs": (x0 + 280, top - 60 * k)}[p]

    def fit_tool(self, t):
        """(station x, x, y, part carried) of the Sprout FIT arm."""
        sx = LS[4]
        ix, iy = self.idle_xy(sx)
        m = self.m("sprout")
        u = t - self.LW0[3]
        keys = [(0.0, ix, iy)]
        item = None
        for j, p in enumerate(self.FIT_PARTS):
            g = j * 5.2
            tx, ty = self.fit_tray(p)
            ax, ay = self.grip_anchor(m, p)
            keys += [(g + 1.4, tx, ty), (g + 1.7, tx, ty)]
            if p == "arm":                                  # up over the cap, then down on the left
                top = m.y - 420 * m.k
                keys += [(g + 2.6, tx, top), (g + 3.4, ax, top)]
            elif p == "face":
                keys += [(g + 2.8, ax, ay - 160)]
            elif p == "legs":
                keys += [(g + 3.0, ax + 160, ay)]
            keys += [(g + 3.9, ax, ay), (g + 4.3, ax, ay)]
            if g + 1.7 <= u < g + 4.3:
                item = p
        keys += [(4 * 5.2 + 0.8, ix, iy)]
        x, y, _ = path(keys, u)
        return sx, x, y, item

    def seed_tray(self):
        """The seedling in its little pot on the PLANT tray (right of the station): its root (the grip point)."""
        return LS[5] + 250.0, G - 30.0 - 22.0

    def plant_arm(self, t):
        """The PLANT arm: takes the seedling from its pot and holds it out to Twigs' right hand. -> (x, y, holding)."""
        sx = LS[5] + 80.0
        ix, iy = sx, BEAM_Y + 90.0
        pl = self.PL
        tk = pl["take"]
        tx, ty = self.seed_tray()
        hx, hy = self.twigs_hold(tk)
        top = PY - 520 * self.mk
        keys = [(tk - 6.0, ix, iy), (tk - 4.0, tx, ty), (tk - 3.6, tx, ty), (tk - 2.4, tx, top), (tk - 1.0, hx, top),
                (tk, hx, hy), (tk + 0.6, hx, hy), (tk + 1.6, hx + 60, hy - 40), (tk + 3.0, ix, iy)]
        x, y, _ = path(keys, t)
        holding = tk - 3.6 <= t < tk + 0.3
        return x, y, holding

    def twigs_hold(self, t):
        """The point between the fingers of Twigs' right hand on the step, for the lift he has at t."""
        if not hasattr(self, "_step_tw"):
            self._step_tw = probe("teeth", self.mk, self.step_x, FY, hands=True)
        x, y, _, _ = twig_point(self._step_tw, t, 1, self.twigs_lift(t))
        return x, y

    def twigs_lift(self, t):
        pl = self.PL
        if t < pl["on"]:
            return 0.0
        a, b = pl["lift"]
        p = self.p_take * smootherstep(seg(t, pl["on"] + 0.6, pl["take"] - 0.8))
        p += (self.p_hole - self.p_take) * smootherstep(seg(t, a, b))
        p *= 1 - smootherstep(seg(t, pl["release"] + 0.4, pl["done"]))
        return p

    def seedling_xy(self, t):
        """Root of the seedling: in the PLANT arm's gripper, then in Twigs' fingers, then settling into the hole."""
        pl = self.PL
        if t < pl["take"]:
            x, y, _ = self.plant_arm(t)
            return x, y
        hx, hy = self.twigs_hold(min(t, pl["release"]))
        if t < pl["release"]:
            return hx, hy
        u = smoothstep(seg(t, pl["release"], pl["release"] + 0.5))
        return lerp(hx, self.hole[0], u), lerp(hy, self.hole[1], u)

    # ----- camera -----

    def target(self, t):
        """Slow pans, close in on the work (owner: fill the frame; Twigs' hands and every build step big on screen)."""
        M = self.M
        k = [(0.0, -150.0, None, 0.8), (self.in_door["digger"] + 3.0, 300.0, None, 0.8),
             (self.settle, 900.0, None, 0.92),
             (self.O + 1.0, TS[0] - 40, None, 1.3), (self.O + 7.0, TS[0] - 40, None, 1.3),
             (self.T1 + M + 3.6, TS[1] + 40, None, 1.7), (self.T2 - 1.5, TS[1] + 40, None, 1.7),
             (self.T2 + M + 2.6, TS[2] + 40, None, 1.7), (self.F0 + 3.6, TS[2] + 60, None, 2.2),
             (self.I0 - 0.5, TS[2] + 60, None, 2.2),
             (self.I0 + 4.0, TS[2] + 20, None, 1.4), (self.WAKE + 1.5, TS[2] + 20, None, 1.6),
             (self.D0 + 0.5, TS[2] + 40, None, 1.6), (self.H0 + 5.0, LS[0] - 160, None, 1.2),
             (self.H1 + 1.0, LS[0] - 60, None, 1.5)]
        for j in range(4):
            a = self.LM[j]
            k.append((a + M + 3.0, LS[j + 1] - 30, None, 1.6))
            k.append((self.LM[j + 1] - 1.4, LS[j + 1] - 30, None, 1.6))
        pl = self.PL
        k += [(self.LM[4] + M + 3.0, LS[5] - 90, None, 1.5), (pl["done"], LS[5] - 90, None, 1.5),
              (self.I1 + 1.0, LS[5] - 60, None, 1.4), (self.WAKE_S + 1.0, LS[5] - 40, None, 1.6),
              (self.CARD[0] + 1.5, LS[5] - 60, None, 1.3), (self.SD, LS[5], None, 1.2),
              (self.door[1], EXIT[0] - 500, None, 0.95), (self.dur, EXIT[0] - 300, None, 0.95)]
        k.sort(key=lambda e: e[0])
        return cam_keys(k, t)

    # ----- the Keepers -----

    def walls(self, t):
        return [(ENTRY[0] - 900, ENTRY[0]), (EXIT[1], EXIT[1] + 900)]

    def name_amount(self, kind, t):
        if kind != "sprout":
            return 0.0
        w = self.WAKE_S + 1.0
        return smoothstep(seg(t, w, w + 0.6)) * (1 - smoothstep(seg(t, self.CARD[0] - 0.6, self.CARD[0])))

    def update(self, t, dt):
        self.reach = {}
        for kd in ["teeth"] + ROW + ["sprout"]:
            m = self.m(kd)
            if m is None:
                continue
            up = GLO_UP if kd == "lantern" else 0.0
            y, dy = FY - up, 0.0
            if kd == "sprout":
                self._sprout(m, t, dt)
                continue
            u = 0.0
            if t < self.in_door[kd] + DEPTH_T:
                u = depth_out(t, self.in_door[kd]) if t > self.in_door[kd] else 1.0
            elif t > self.at_exit[kd]:
                u = depth_in(t, self.at_exit[kd])
            self.door_depth[kd] = u
            if u > 0.0:
                (self.way_in if t < self.settle else self.way_out).walking(self, m, t, dt, u, FY - up)
                m.alive, m.orb_in = self.alive(kd, t), self.orb_in(kd, t)
                self.look_new(m)
                if kd == "teeth":
                    self.twigs_state(m, t)
                continue
            if kd == "teeth":
                x, y = self._twigs_xy(t)
            elif kd == "springs":
                x, lift = self._springs_x(t)
                dy = -lift
            else:
                x = self.R[kd].at(t)
            self.place(m, x, t, dt, y=y, dy=dy)
            m.alive, m.orb_in = self.alive(kd, t), self.orb_in(kd, t)
            if kd == "lantern":
                m.lamp = m.alive
            self.look_new(m)
            if kd == "teeth":
                self.twigs_state(m, t)
                m.punch = max(m.punch, self.twigs_lift(t))
                pl = self.PL
                if pl["take"] - 0.2 <= t < pl["release"] + 0.3:
                    m.grip = 0.8 * smoothstep(seg(t, pl["take"] - 0.2, pl["take"] + 0.2)) * \
                        (1 - smoothstep(seg(t, pl["release"], pl["release"] + 0.3)))
                if m.alive < 1.0:
                    m.walk = 0.0
                if t >= self.O + 3.7 and "teeth" not in self._orb_at:
                    self._orb_at["teeth"] = m.orb_now(t)
        self._particles(t)
        self._sounds(t)

    def _twigs_xy(self, t):
        if t < self.twigs_on:
            return self.R0("teeth", t), FY
        hj = Jump(TS[0], FY, TS[0], PY, apex=40)
        if t < self.twigs_on + hj.dur:
            return hj.at(t - self.twigs_on)
        if t < self.D0:
            return self.twigs_pallet(t), PY
        if t < self.twigs_land:
            return self.twigs_jump.at(t - self.D0)
        return self.R["teeth"].at(t), FY

    def R0(self, kd, t):
        """Twigs' walk in from the tunnel (his first route, before the factory took over)."""
        if not hasattr(self, "_r0"):
            self._r0 = Route(self.way_in.xc, self.in_door["teeth"] + DEPTH_T).go(TS[0], v=160)
        return self._r0.at(t)

    def _springs_x(self, t):
        """Springs hops along every leg of its route (real-gravity hops) instead of walking."""
        r = self.R["springs"]
        for ts, T, a, b, _ in r.legs:
            if ts <= t < ts + T:
                x, lift, sq = hops(a, b, ts, ts + T, t, apex=45, step=150)
                self.m("springs").spring = sq
                return x, lift
        self.m("springs").spring = 0.0
        return r.at(t), 0.0

    def _sprout(self, m, t, dt):
        if t < self.H0 - 0.5:
            m.x, m.y = LS[0], self.log_y(t)
            self.poses.pop("sprout", None)
            m.newlook = True
            self.sprout_state(m, t)
            m.alive, m.orb_in = 0.0, 0.0
            return
        u = 0.0
        if t > self.at_exit["sprout"]:
            u = depth_in(t, self.at_exit["sprout"])
        self.door_depth["sprout"] = u
        if u > 0.0:
            self.way_out.walking(self, m, t, dt, u, FY)
        elif t < self.SD:
            x, y = self.log_pallet(t), self.log_y(t)
            self.place(m, x, t, dt, y=y, walk=0.0)
        elif t < self.sprout_land:
            x, y = self.sprout_jump.at(t - self.SD)
            self.place(m, x, t, dt, y=y, walk=0.0)
        else:
            self.place(m, self.R["sprout"].at(t), t, dt, y=FY)
        m.alive, m.orb_in = self.alive("sprout", t), self.orb_in("sprout", t)
        self.look_new(m, flash=bump(t, self.I1 + 3.9, 1.4), smile=0.75)
        self.sprout_state(m, t)

    # ----- what moves (for the warp check) -----

    def props(self, t):
        out = {"trolley": (self.trolley_x(t), RAIL_Y)}
        gx, gy, _ = self.gripper(t)
        out["gripper"] = (gx, gy)
        out["pallet_twigs"] = (self.twigs_pallet(t), PY)
        out["pallet_log"] = (self.log_pallet(t), PY)
        tt = self.twigs_tool(t)
        if tt is not None:
            out["tool_twigs"] = tt[1:3]
        if self.LW0[3] <= t < self.LW0[3] + self.W_FIT:
            out["tool_fit"] = self.fit_tool(t)[1:3]
        pl = self.PL
        if pl["take"] - 6.0 <= t < pl["take"] + 3.0:
            out["plant_arm"] = self.plant_arm(t)[:2]
        if pl["take"] - 3.6 <= t < pl["release"] + 0.5:
            out["seedling"] = self.seedling_xy(t)
        return out

    # ----- particles and sounds -----

    def _particles(self, t):
        p = self.s.particles
        lt = self.log_tool(t)
        if lt is None:
            return
        j, u = lt
        sx = LS[j + 1]
        m = self.m("sprout")
        k = m.k
        top = m.y - 270 * k
        if j == 0 and self.CUT_T[1] <= u < self.CUT_T[2] and p.rng.uniform() < 0.7:
            x = lerp(sx - 120 * k, sx + 120 * k, seg(u, self.CUT_T[1], self.CUT_T[2]))
            p.burst(x, top, 2, SAWDUST * 1.05, 170, 0.9, 4.0, g=600, spread=0.9, direction=math.pi / 2)
        if j == 1 and self.TURN_T[1] <= u < self.TURN_T[2] and p.rng.uniform() < 0.45:
            yr = top + (m.y - 40 * k - top) * m.turned
            p.burst(sx + 100 * k, yr, 1, CURL, 200, 0.7, 7.0, g=900, spread=0.6, direction=-0.3)
        if j == 2:
            ch = self.CARVE_T["chisel"]
            if ch[1] <= u < ch[2] and p.rng.uniform() < 0.35:
                xc = sx - 100 * k + 200 * k * m.carved
                p.burst(xc, m.y - 224 * k, 1, CURL * 0.9, 120, 0.8, 3.5, g=700, spread=1.2)

    def _sounds(self, t):
        for j, kd in enumerate(["teeth"] + ROW):
            if self.crossed(self.in_door[kd] + 0.2):
                self.chat(self.in_door[kd] + 0.2, kd, "ooh" if j % 2 == 0 else "mm", icon=None)
        if self.crossed(self.twigs_on):
            self.hit(self.twigs_on, "thud", 50, 0.12, TS[0], PY)
        o = self.O
        if self.crossed(o - 1.5):
            self.chat(o - 1.5, "teeth", "mm")
        if self.crossed(o):
            self.fx(o, "servo", 1.8, 0.18, TS[0], RAIL_Y)
        if self.crossed(o + 3.4):
            self.hit(o + 3.4, "clack", 60, 0.18, TS[0], G - 300)
        if self.crossed(o + 3.8):
            self.hit(o + 3.8, "soft_bell", 70, 0.16, TS[0], G - 300)
        if self.crossed(o + 6.3):
            self.hit(o + 6.3, "clack", 67, 0.12, TS[0], RAIL_Y)
        if self.crossed(o + 6.6):
            self.chat(o + 6.6, "tentacles", "aww")
        moves = [self.T1, self.T2] + self.LM
        for mt in moves:
            if self.crossed(mt):
                self.fx(mt, "motor", self.M, 0.22, 3000, G - 100)
        u0, f0 = self.U0, self.F0
        for a, b in ((1.2, 3.6), (5.0, 7.4)):
            if self.crossed(u0 + a):
                self.hit(u0 + a, "clack", 64, 0.16, TS[1], G - 300)
            if self.crossed(u0 + b + 0.3):
                self.hit(u0 + b + 0.3, "thud", 55, 0.12, TS[1] + 240, G)
        for a in (4.6, 7.8):
            if self.crossed(f0 + a):
                self.hit(f0 + a, "clunk", 55, 0.18, TS[2], G - 300)
                self.hit(f0 + a + 0.1, "chime", 76, 0.1, TS[2], G - 300)
        for a in (9.0, 12.0):
            if self.crossed(f0 + a):
                self.hit(f0 + a, "clack", 74, 0.1, TS[2], G - 300)
                self.fx(f0 + a + 0.1, "servo", 0.8, 0.08, TS[2], G - 300)
                self.fx(f0 + a + 1.4, "servo", 0.8, 0.08, TS[2], G - 300)
        for kd, i0 in (("teeth", self.I0), ("sprout", self.I1)):
            x = TS[2] if kd == "teeth" else LS[5]
            if self.crossed(i0):
                self.fx(i0, "servo", 1.6, 0.16, x, RAIL_Y)
            if self.crossed(i0 + 3.95):
                self.hit(i0 + 3.95, "clack", 67, 0.14, x, G - 300)
                self.hit(i0 + 4.0, "chime", 72 if kd == "teeth" else 76, 0.16, x, G - 300)
                self.hit(i0 + 4.3, "soft_bell", 79, 0.12, x, G - 300)
        w = self.WAKE
        if self.crossed(w):
            self.chat(w, "teeth", "ooh")
        if self.crossed(w + 3.0):
            self.chat(w + 3.0, "teeth", "hehe", icon="smile")
        if self.crossed(w + 4.4):
            self.chorus(w + 4.4, ROW, "yay", gap=0.22)
        if self.crossed(self.D0 + self.twigs_jump.dur):
            self.hit(self.D0 + self.twigs_jump.dur, "thud", 48, 0.1, TS[2], FY)
        # the hoist and the log line
        if self.crossed(self.H0):
            self.fx(self.H0, "servo", self.H1 - self.H0, 0.12, LS[0], G - 900)
        if self.crossed(self.H1):
            self.hit(self.H1, "thud", 45, 0.2, LS[0], PY)
        if self.crossed(self.H1 + 0.6):
            self.chorus(self.H1 + 0.6, ["teeth", "lantern", "springs"], "ooh", gap=0.3)
        a = self.LW0
        if self.crossed(a[0] + self.CUT_T[1]):
            self.fx(a[0] + self.CUT_T[1], "saw", self.CUT_T[2] - self.CUT_T[1], 0.08, LS[1], G - 300)
        if self.crossed(a[0] + self.CUT_T[3] + 0.6):
            self.hit(a[0] + self.CUT_T[3] + 0.6, "thud", 50, 0.14, LS[1] + 240, G)
        if self.crossed(a[1] + self.TURN_T[0]):
            self.fx(a[1] + self.TURN_T[0], "motor", self.TURN_T[3] - self.TURN_T[0], 0.12, LS[2], G - 200)
        if self.crossed(a[1] + self.TURN_T[1]):
            self.fx(a[1] + self.TURN_T[1], "sand_scrape", self.TURN_T[2] - self.TURN_T[1], 0.1, LS[2], G - 200)
        ch, so, br = self.CARVE_T["chisel"], self.CARVE_T["socket"], self.CARVE_T["brush"]
        for q in range(12):
            tq = a[2] + ch[1] + q * (ch[2] - ch[1]) / 12
            if self.crossed(tq):
                self.hit(tq, "clack", 70 + (q % 3) * 2, 0.07, LS[3], G - 300)
        if self.crossed(a[2] + so[1]):
            self.fx(a[2] + so[1], "servo", so[2] - so[1], 0.08, LS[3], G - 300)
        if self.crossed(a[2] + br[1]):
            self.fx(a[2] + br[1], "paint_spread", br[2] - br[1], 0.1, LS[3], G - 300)
        for j in range(4):
            g = a[3] + j * 5.2
            if self.crossed(g + 4.3):
                self.hit(g + 4.3, "clunk", 55, 0.16, LS[4], G - 300)
                self.hit(g + 4.4, "chime", 72 + 2 * j, 0.1, LS[4], G - 300)
        pl = self.PL
        if self.crossed(pl["take"] + 0.3):
            self.chat(pl["take"] + 0.3, "teeth", "ooh")
        if self.crossed(pl["release"] + 0.4):
            self.hit(pl["release"] + 0.4, "chime", 79, 0.12, LS[5], G - 300)
        if self.crossed(pl["release"] + 1.2):
            self.chat(pl["release"] + 1.2, "teeth", "hehe", icon="smile")
        ws = self.WAKE_S
        if self.crossed(ws):
            self.chat(ws, "sprout", "ooh")
        if self.crossed(ws + 1.4):
            self.chat(ws + 1.4, "sprout", "hey", icon="smile")
        if self.crossed(ws + 2.6):
            self.chorus(ws + 2.6, ["teeth"] + ROW, "yay", gap=0.2)
        if self.crossed(self.sprout_land):
            self.hit(self.sprout_land, "thud", 52, 0.1, LS[5] + 80, FY)
        if self.crossed(self.door[0]):
            self.fx(self.door[0], "motor", self.door[1] - self.door[0], 0.35, EXIT[0], G - 300)
        if self.crossed(self.door[1]):
            self.hit(self.door[1], "clunk", 45, 0.3, EXIT[0], G - 500)
        for kd in self.exit_t:
            if self.crossed(self.exit_t[kd] + 0.2):
                self.chat(self.exit_t[kd] + 0.2, kd, "wee" if kd == "springs" else "mm", icon=None)

    def aside_moods(self, t):
        quiet = [(self.O - 1, self.T1), (self.I0 - 1, self.D0 + 1), (self.PL["take"] - 2, self.PL["done"]),
                 (self.I1 - 1, self.SD + 1)]
        if any(a < t < b for a, b in quiet) or NR.speaking(self, t):
            return []
        return ["mm", "hehe", "ooh", "aww"]

    # ----- drawing -----

    def draw(self, c, t):
        self._hall(c, t)
        self.way_in.draw_inside(self, c, t, self.door_depth)
        self.way_out.draw_inside(self, c, t, self.door_depth)
        self._exit_door(c, t)
        self._rail(c, t)
        self._hoist(c, t)
        self._stations(c, t)
        self._line(c, t)
        self._trays(c, t)
        self._bins(c, t)
        self.glo_light(c, k=0.6 * self.m("lantern").alive)
        out = [kd for kd in self.outside() if kd in self.poses]
        tw = self.m("teeth")
        back = [kd for kd in out if kd == "sprout" or (kd == "teeth" and abs(tw.y - PY) < 1 and
                                                         self.twigs_on <= t < self.D0)]
        self.draw_monsters(c, t, kinds=back)
        self.draw_monsters(c, t, kinds=[kd for kd in out if kd not in back])
        self._tools(c, t)
        self._gripper(c, t)
        self._front(c, t)

    def _hall(self, c, t):
        s = self.s
        vx0, vx1, vy0, vy1 = s.view()
        L, R = max(HALL[0], vx0 - 200), min(HALL[1], vx1 + 200)
        top = G - 1300
        rect(c, L, top - 400, R, G, INTERIOR)
        off = s.cam_x * 0.25
        for gx in np.arange(math.floor((L - off) / 340) * 340 + off, R, 340):
            rect(c, gx, top, gx + 26, G, FAR)
        for gy in (G - 1000, G - 430):
            c.line(L, gy, R, gy, FAR, 9)
        rect(c, L, top, R, G - 1180, MID)
        glo_x = self.m("lantern").x
        for lx in self.lamps:
            if not (L - 300 < lx < R + 300):
                continue
            on = smoothstep(seg(glo_x if t < self.settle else 1e9, lx - 260, lx - 60))
            c.line(lx, G - 1180, lx, G - 900, CABLE, 3)
            c.polygon([(lx - 42, G - 868), (lx + 42, G - 868), (lx + 22, G - 900), (lx - 22, G - 900)], STEEL)
            c.circle(lx, G - 864, 12, IRON * 1.2 + LAMP * 0.6 * on)
            if on > 0:
                s.glow_draw(lambda g, lx=lx, on=on: (g.circle(lx, G - 862, 22, LAMP * 0.7 * on),
                                                     g.polygon([(lx - 42, G - 862), (lx + 42, G - 862), (lx + 260, G),
                                                                (lx - 260, G)], LAMP * 0.035 * on)))
        rect(c, L, G, R, G + 700, FLOOR)
        c.line(L, G, R, G, lighten(FLOOR, 1.9), 2)
        c.line(L, FY + 40, R, FY + 40, lighten(FLOOR, 1.3), 2)
        for (d0, d1), outside in ((ENTRY, False), (EXIT, True)):
            if not (L < d1 + 100 and d0 - 100 < R):
                continue
            rect(c, d0, G - 520, d1, G, INTERIOR * 0.45)
            if outside:
                u = smoothstep(seg(t, *self.door))
                rect(c, d0, G - 520, d1, G, np.array([16, 22, 40]) * (0.4 + 0.6 * u))
                for q in range(5):
                    sx_ = d0 + 30 + q * 57
                    c.circle(sx_, G - 470 + 37 * ((q * 7) % 5), 2.5, SIGN_WARM * 0.6 * u)
                rect(c, d0, G - 30, d1, G, np.array([30, 44, 30]) * u + INTERIOR * 0.45 * (1 - u))
            else:
                for k_ in range(3):
                    c.line(d0 + 8, G - 440 + k_ * 140, d1 - 8, G - 440 + k_ * 140, INTERIOR * 0.8, 3)
            machine_block(c, d0 - 22, G - 566, d1 + 22, G - 520, STEEL)

    def _rail(self, c, t):
        s = self.s
        vx0, vx1 = s.view()[:2]
        c.line(max(HALL[0], vx0 - 100), RAIL_Y - 20, min(HALL[1], vx1 + 100), RAIL_Y - 20, CABLE, 10)
        for hx in np.arange(math.floor(vx0 / 600) * 600, vx1 + 600, 600):
            c.line(hx, G - 1180, hx, RAIL_Y - 20, CABLE * 0.8, 4)
        tx = self.trolley_x(t)
        if not s.visible(tx - 200, tx + 200):
            return
        machine_block(c, tx - 90, RAIL_Y - 40, tx + 90, RAIL_Y + 30, STEEL)
        for wx in (-60, 60):
            c.circle(tx + wx, RAIL_Y - 20, 12, IRON)
        c.text("ORBS", tx, RAIL_Y - 6, 26, SIGN_WARM * 0.75)
        top = RAIL_Y + 66
        for kd, dx in self.CUP.items():
            cx = tx + dx
            c.line(cx, RAIL_Y + 30, cx, top + 6, CABLE, 3)
            c.polygon(ellipse(cx, top + 6, 17, 10, 16, 0, math.pi), IRON * 1.3)
            if self.in_rack(kd, t):
                loose_orb(c, s, cx, top, (16 if kd == "teeth" else 14) * self.mk, 0.8)
        gx, gy, _ = self.gripper(t)
        rect(c, gx - 14, RAIL_Y + 24, gx + 14, RAIL_Y + 40, IRON * 1.3)

    def _gripper(self, c, t):
        s = self.s
        gx, gy, held = self.gripper(t)
        if not s.visible(gx - 100, gx + 100):
            return
        if held is not None:
            loose_orb(c, s, gx, gy, (16 if held == "teeth" else 14) * self.mk)
        c.line(gx, RAIL_Y + 40, gx, gy - 26, CABLE, 3)
        rect(c, gx - 12, gy - 34, gx + 12, gy - 22, STEEL * 1.2)
        open_ = 0.0 if held is not None else 1.0
        for sd in (-1, 1):
            c.line(gx + sd * 8, gy - 24, gx + sd * (14 + 8 * open_), gy - 6, STEEL * 1.4, 4)
            c.line(gx + sd * (14 + 8 * open_), gy - 6, gx + sd * (8 + 6 * open_), gy + 8, STEEL * 1.4, 4)

    def _hoist(self, c, t):
        """The log hoist over the first log slot: a chain from the loft, a hook in the eye bolt on the log's top."""
        x = LS[0]
        if not self.s.visible(x - 200, x + 200):
            return
        m = self.m("sprout")
        k = m.k
        machine_block(c, x - 70, G - 1190, x + 70, G - 1130, STEEL)
        c.text("LOGS", x, G - 1160, 24, SIGN_WARM * 0.75)
        eye_y = self.log_y(t) - (270 + 180 + 14) * k
        if t < self.H1 + 1.0:
            hook_y = eye_y
        else:
            hook_y = lerp(eye_y - 30, G - 1130 + 40, smootherstep(seg(t, self.H1 + 1.0, self.H1 + 3.0)))
            hook_y = min(hook_y, eye_y - 30 * smoothstep(seg(t, self.H1 + 0.2, self.H1 + 1.0)))
        if t >= self.LM[0] and hook_y >= G - 1100:
            hook_y = G - 1090
        for y in np.arange(G - 1130, hook_y - 14, 22):    # chain links
            c.polyline(ellipse(x, y + 11, 5, 11, 12), CHAIN, 3, closed=True)
        c.polyline([(x, hook_y - 16), (x, hook_y), (x + 12, hook_y + 10), (x + 4, hook_y + 20)], CLAW, 5)

    def _station(self, c, sx, name, busy):
        s = self.s
        for px_ in (sx - 210, sx + 210):
            rect(c, px_ - 10, BEAM_Y, px_ + 10, PY + 10, STEEL * 0.55)
        rect(c, sx - 220, BEAM_Y - 20, sx + 220, BEAM_Y + 4, STEEL * 0.7)
        machine_block(c, sx - 120, BEAM_Y - 86, sx + 120, BEAM_Y - 30, IRON)
        col = HAZARD if busy else STEEL * 0.6
        c.text(name, sx - 12, BEAM_Y - 58, 30, SIGN_WARM * 0.8)
        c.circle(sx + 98, BEAM_Y - 58, 8, col)
        if busy:
            s.glow_draw(lambda g: g.circle(sx + 98, BEAM_Y - 58, 15, col * 0.6))

    def _stations(self, c, t):
        s = self.s
        busy_tw = {TS[1]: self.U0 <= t < self.U0 + self.W_U, TS[2]: self.F0 <= t < self.F0 + self.W_F}
        for sx, name in ((TS[1], "UNCLIP"), (TS[2], "FIT")):
            if s.visible(sx - 260, sx + 260):
                self._station(c, sx, name, busy_tw[sx])
        lt = self.log_tool(t)
        for j, name in enumerate(("CUT", "TURN", "CARVE", "FIT", "PLANT")):
            sx = LS[j + 1]
            if s.visible(sx - 260, sx + 260):
                busy = (lt is not None and lt[0] == j) if j < 4 else (self.PL["take"] - 6 <= t < self.PL["done"])
                self._station(c, sx, name, busy)
        # the bins' backs
        bx, by = self.old_bin()
        if s.visible(bx - 80, bx + 80):
            rect(c, bx - 60, by - 10, bx + 60, by + 70, BIN * 0.7)
        ox, oy = self.offcut_bin()
        if s.visible(ox - 80, ox + 80):
            rect(c, ox - 70, oy - 10, ox + 70, oy + 70, BIN * 0.7)

    def offcut_bin(self):
        return LS[1] + 240.0, G + 18.0

    def _line(self, c, t):
        s = self.s
        x0, x1 = TS[0] - 260, LS[5] + 260
        vx0, vx1 = s.view()[:2]
        a, b = max(x0, vx0 - 100), min(x1, vx1 + 100)
        if a < b:
            rect(c, a, PY + 14, b, G + 24, IRON)
            c.line(a, PY + 14, b, PY + 14, lighten(IRON, 1.5), 2)
            roll = (self.twigs_pallet(t) + self.log_pallet(t)) / 9.0 / 60.0
            for rx_ in np.arange(math.floor(a / 48) * 48, b, 48):
                c.circle(rx_, PY + 30, 8, STEEL)
                c.line(rx_, PY + 30, rx_ + 7 * math.cos(roll), PY + 30 + 7 * math.sin(roll), STEEL * 0.6, 2)
        for ux in (self.twigs_pallet(t), self.log_pallet(t)):
            if s.visible(ux - 140, ux + 140):
                rect(c, ux - 120, PY, ux + 120, PY + 14, HAZARD * 0.55)
        # Sprout's jig: a steel plate and a short peg the log (then the body) stands on
        m = self.m("sprout")
        lx = self.log_pallet(t)
        k = self.mk
        if s.visible(lx - 100, lx + 100):
            rect(c, lx - 34, PY - 6, lx + 34, PY, STEEL * 1.1)
            rect(c, lx - 7, PY - 40 * k, lx + 7, PY - 4, STEEL * 1.3)
        if self.H0 - 0.5 <= t < self.LW0[0] + self.CUT_T[2]:       # the eye bolt in the log's top (CUT takes it)
            ey = self.log_y(t) - (270 + 180) * k
            c.polyline(ellipse(lx, ey - 12 * k, 9 * k, 12 * k, 14), CLAW, 3, closed=True)

    def _trays(self, c, t):
        """The NEW tray (Twigs' hands), the FIT tray (Sprout's parts sit on it; they're drawn by Sprout), the stain
        pot and the seedling's pot."""
        s = self.s
        m = self.m("teeth")
        x = TS[2] + 240.0
        if s.visible(x - 120, x + 120):
            self._table(c, x, G - 4, 90)
            c.text("NEW", x, G + 26, 20, SIGN_WARM * 0.5)
            for side, (hx, hy) in zip((1, -1), self.tray_hands()):
                grab = self.F0 + (2.2 if side > 0 else 5.8)
                if t < grab:
                    m._twigs_hand(c, (hx, hy), (hx, hy - 60), side)
        x = LS[4] + 290.0
        if s.visible(x - 200, x + 200):
            self._table(c, x, G - 30, 150)
            c.text("PARTS", x, G + 6, 20, SIGN_WARM * 0.5)
        px_, py_ = LS[3] + 240.0, G - 30.0
        if s.visible(px_ - 80, px_ + 80):
            self._table(c, px_, py_, 60)
            rect(c, px_ - 30, py_ - 46, px_ + 30, py_, STEEL * 0.9)
            c.polygon(ellipse(px_, py_ - 46, 30, 7, 20), STAIN)
        tx, ty = self.seed_tray()
        if s.visible(tx - 80, tx + 80):
            self._table(c, tx, G - 30, 60)
            c.polygon([(tx - 26, G - 30), (tx + 26, G - 30), (tx + 32, ty + 6), (tx - 32, ty + 6)], POT)
            c.polygon(ellipse(tx, ty + 6, 32, 6, 20), SOIL)
            if t < self.PL["take"] - 3.6:                 # the seedling still in its pot (Sprout draws it once lifted)
                pass

    def _table(self, c, x, top, hw):
        rect(c, x - hw, top, x + hw, top + 12, PLANK_C)
        for lx in (x - hw + 12, x + hw - 12):
            c.line(lx, top + 12, lx, G + 90, PLANK_C * 0.7, 6)

    def _arm(self, c, px_, x, y, bend=40):
        """A machine arm from its pivot on the beam to (x, y)."""
        elbow = (lerp(px_, x, 0.5) + bend, lerp(BEAM_Y, y, 0.5) - 60)
        c.line(px_, BEAM_Y, *elbow, STEEL * 0.85, 10)
        c.line(*elbow, x, y - 12, STEEL, 8)
        c.circle(*elbow, 9, IRON * 1.4)

    def _claw(self, c, x, y, closed):
        for sd in (-1, 1):
            c.line(x + sd * 6, y - 14, x + sd * (10 if closed else 18), y + 4, STEEL * 1.4, 4)
        rect(c, x - 10, y - 22, x + 10, y - 12, HAZARD * 0.8)

    def _idle(self, c, sx):
        ix, iy = self.idle_xy(sx)
        c.line(ix, BEAM_Y, ix, iy - 20, STEEL * 0.8, 9)
        rect(c, ix - 20, iy - 24, ix + 20, iy, IRON * 1.2)

    def _tools(self, c, t):
        s = self.s
        m = self.m("teeth")
        # Twigs' UNCLIP and FIT
        tt = self.twigs_tool(t)
        for sx in TS[1:]:
            if not s.visible(sx - 400, sx + 400):
                continue
            if tt is None or tt[0] != sx:
                self._idle(c, sx)
                continue
            _, x, y, item = tt
            self._arm(c, sx, x, y)
            if item == "saw":
                u = t - self.U0
                side, g0 = (1, 1.2) if u < 4.0 else (-1, 5.0)
                _, _, fx, fy = twig_point(m, t, side, 0.0)
                v = smoothstep(seg(u, g0, g0 + 0.8))
                dx, dy = lerp(fx, 0.0, v), lerp(fy, 1.0, v)
                L = math.hypot(dx, dy) + 1e-9
                dx, dy = dx / L, dy / L
                hd = (x - dx * 26 * m.k, y - dy * 26 * m.k)
                m._wrist_saw(c, hd, (hd[0] - dx * 60, hd[1] - dy * 60), side)
            elif item == "hand":
                u = t - self.F0
                side = 1 if u < 5.0 else -1
                w = self.wrist(side, t)
                el = self._elbow(side, t)
                fx, fy = w[0] - el[0], w[1] - el[1]
                L = math.hypot(fx, fy) + 1e-9
                g0 = 2.2 if side > 0 else 5.8
                v = smoothstep(seg(u, g0, g0 + 2.4))
                dx, dy = lerp(0.0, fx / L, v), lerp(1.0, fy / L, v)
                L2 = math.hypot(dx, dy) + 1e-9
                m._twigs_hand(c, (x, y), (x - dx / L2 * 60, y - dy / L2 * 60), side)
            closed = item is not None
            self._claw(c, x, y, closed)
        # the log line
        lt = self.log_tool(t)
        sp = self.m("sprout")
        k = sp.k
        for j, sx in enumerate(LS[1:5]):
            if not s.visible(sx - 400, sx + 400):
                continue
            if lt is None or lt[0] != j:
                self._idle(c, sx)
                continue
            u = lt[1]
            getattr(self, "_tool_" + ("cut", "turn", "carve", "fit")[j])(c, sx, u, sp, k, t)
        sx = LS[5]
        if s.visible(sx - 400, sx + 400):
            pl = self.PL
            if pl["take"] - 6.0 <= t < pl["take"] + 3.0:
                x, y, holding = self.plant_arm(t)
                self._arm(c, sx + 80, x, y, bend=-40)
                self._claw(c, x, y, holding)
            else:
                ix, iy = self.idle_xy(sx + 80)
                c.line(ix, BEAM_Y, ix, iy - 20, STEEL * 0.8, 9)
                rect(c, ix - 20, iy - 24, ix + 20, iy, IRON * 1.2)

    def _elbow(self, side, t):
        m = self.m("teeth")
        k = m.k
        sway = m.alive * 4 * math.sin(t * 1.1) * k
        cy = m.y - 350 * k + sway * 0.3
        return m._teeth_arm(side, t, m.x + sway, cy)[1]

    def _tool_cut(self, c, sx, u, m, k, t):
        a, b, e, p, d = self.CUT_T
        ix, iy = self.idle_xy(sx)
        top = m.y - 270 * k                        # the cut line: the finished top of the log
        x0, x1 = sx - 150 * k, sx + 150 * k
        keys = [(0.0, ix, iy), (a, x0, top), (b, x0, top), (e, x1, top), (e + 0.6, x1 + 60, top - 120),
                (e + 1.0, sx, top - 260 * k), (p - 0.4, sx - 160 * k, top - 230 * k),
                (p, sx - 112 * k, top - 60 * k), (p + 1.2, sx - 112 * k, top - 60 * k),
                (p + 1.6, sx + 40 * k, top - 200 * k), (d, ix, iy)]
        x, y, _ = path(keys, u)
        if p <= u < p + 1.2:                        # pushing: right behind the offcut's left side
            x = self.offcut(self.LW0[0] + u)[0] - 112 * k
        self._arm(c, sx, x, y)
        if u < e + 0.6:                             # the saw
            run = smoothstep(seg(u, a - 0.4, b)) * (1 - smoothstep(seg(u, e, e + 0.5)))
            saw_blade(c, x, y, 34, t * 30 * run, STEEL * 1.5)
            c.circle(x, y, 8, IRON)
        else:                                       # its guard doubles as a pusher pad
            rect(c, x - 10, y - 26, x + 10, y + 26, HAZARD * 0.8)

    def offcut(self, t):
        """The top of the log the CUT takes off: (x, y bottom, angle) or None once it's in the bin."""
        m = self.m("sprout")
        k = m.k
        a = self.LW0[0]
        p = a + self.CUT_T[3]
        if t < a + self.CUT_T[2]:
            return None
        sx = LS[1]
        top = m.y - 270 * k
        if t < p:
            return sx, top, 0.0
        u = seg(t, p, p + 1.2)
        x = lerp(sx, sx + 100 * k + 30, smoothstep(u))
        if t < p + 1.2:
            return x, top, 0.0
        bx, by = self.offcut_bin()
        tau = t - p - 1.2
        land = math.sqrt(2 * (by + 30 - top) / GRAVITY)
        if tau > land:
            return None
        return lerp(x, bx, tau / land), fall_y(top, tau), 0.9 * tau / land

    def _tool_turn(self, c, sx, u, m, k, t):
        a, b, e, d = self.TURN_T
        top, bot = m.y - 270 * k, m.y - 40 * k
        # the tailstock: a steel centre pressing down on the top while it turns
        ty = top - 10 * k
        cyl = lerp(BEAM_Y + 90, ty - 4, smoothstep(seg(u, 0.0, a)) * (1 - smoothstep(seg(u, d, d + 0.8))))
        c.line(sx, BEAM_Y, sx, cyl - 18, STEEL * 0.8, 10)
        c.polygon([(sx - 14, cyl - 18), (sx + 14, cyl - 18), (sx, cyl + 4)], STEEL * 1.3)
        yr = top + (bot - top) * m.turned
        ix, iy = self.idle_xy(sx + 140)
        keys = [(0.0, ix, iy), (a, sx + 100 * k + 14, top + 4), (b, sx + 100 * k + 4, top + 4),
                (e, sx + 100 * k + 4, bot), (e + 0.8, sx + 220, bot), (d + 1.0, ix, iy)]
        x, y, _ = path(keys, u)
        if b <= u < e:
            y = yr
        self._arm(c, sx + 140, x + 40, y, bend=50)
        c.line(x + 40, y, x, y, STEEL * 1.3, 8)       # the gouge
        c.polygon([(x - 2, y - 6), (x + 10, y - 6), (x + 6, y + 6), (x - 4, y + 4)], CLAW * 1.2)

    def _tool_carve(self, c, sx, u, m, k, t):
        ch, so, br = self.CARVE_T["chisel"], self.CARVE_T["socket"], self.CARVE_T["brush"]
        cy = m.y - 224 * k                          # the cap's scales
        orb_y = m.y - 78 * k
        ix, iy = self.idle_xy(sx - 70)
        keys = [(0.0, ix, iy), (ch[0], sx - 96 * k, cy - 20 * k), (ch[1], sx - 96 * k, cy - 20 * k),
                (ch[2], sx + 96 * k, cy - 20 * k), (so[0], sx, orb_y), (so[2], sx, orb_y), (so[2] + 0.8, ix, iy)]
        x, y, _ = path(keys, u)
        if ch[1] <= u < ch[2]:
            y += 8 * k * abs(math.sin((u - ch[1]) * 2 * math.pi * 3.0))
        if so[1] <= u < so[2]:
            ang = (u - so[1]) * 2 * math.pi * 1.5
            x += 5 * math.cos(ang)
            y += 5 * math.sin(ang)
        self._arm(c, sx - 70, x, y - 30, bend=-40)
        c.line(x, y - 30, x, y, STEEL * 1.2, 7)          # the chisel
        c.polygon([(x - 5, y - 4), (x + 5, y - 4), (x + 2, y + 6), (x - 2, y + 6)], CLAW * 1.3)
        # the stain brush on the right arm: dips in the pot, then strokes across the cap
        px_, py_ = LS[3] + 240.0, G - 30.0 - 46.0
        jx, jy = self.idle_xy(sx + 70)
        keys = [(0.0, jx, jy), (br[0] - 1.4, px_, py_ - 40), (br[0] - 0.8, px_, py_ + 4), (br[0] - 0.2, px_, py_ - 40),
                (br[1], sx - 98 * k, cy - 24 * k), (br[2], sx + 98 * k, cy - 24 * k), (br[2] + 1.0, jx, jy)]
        x, y, _ = path(keys, u)
        self._arm(c, sx + 70, x, y - 40, bend=40)
        c.line(x, y - 40, x, y - 10, PLANK_C, 6)
        c.polygon([(x - 10, y - 12), (x + 10, y - 12), (x + 8, y + 6), (x - 8, y + 6)],
                  STAIN if u > br[0] - 0.8 else np.array([214, 200, 170]))

    def _tool_fit(self, c, sx, u, m, k, t):
        _, x, y, item = self.fit_tool(t)
        self._arm(c, sx, x, y)
        self._claw(c, x, y, item is not None)

    def _bins(self, c, t):
        """The OLD bin and the OFFCUTS bin stand behind the walkway: whatever drops in falls in behind their fronts,
        and a Keeper on the walkway passes in front of them."""
        s = self.s
        m = self.m("teeth")
        bx, by = self.old_bin()
        if s.visible(bx - 80, bx + 80):
            for a in (3.6, 7.4):                    # the saws drop into the bin, behind its front
                d0 = self.U0 + a
                if d0 <= t < d0 + 0.45:
                    yy = fall_y(by - 50, t - d0)
                    m._wrist_saw(c, (bx, yy), (bx, yy - 46 * m.k), 1)
            rect(c, bx - 64, by + 6, bx + 64, by + 74, BIN)
            c.line(bx - 64, by + 6, bx + 64, by + 6, lighten(BIN, 1.4), 3)
            c.text("OLD", bx, by + 42, 22, SIGN_WARM * 0.55)
        ox, oy = self.offcut_bin()
        if s.visible(ox - 200, ox + 200):
            oc = self.offcut(t)
            if oc is not None:
                x, yb, ang = oc
                k = self.mk
                pts = [(x - 100 * k, yb - 180 * k), (x + 100 * k, yb - 180 * k), (x + 100 * k, yb), (x - 100 * k, yb)]
                cc = Xform(c, 0, 0, ang, 1.0, x, yb - 90 * k)
                cc.polygon(pts, BARK_C)
                cc.polygon(ellipse(x, yb, 100 * k, 14 * k, 24), lighten(WOOD, 1.25))
                cc.polyline(ellipse(x, yb - 180 * k - 12 * k, 9 * k, 12 * k, 14), CLAW, 3, closed=True)   # eye bolt
            rect(c, ox - 74, oy + 6, ox + 74, oy + 74, BIN)
            c.line(ox - 74, oy + 6, ox + 74, oy + 6, lighten(BIN, 1.4), 3)
            c.text("OFFCUTS", ox, oy + 42, 20, SIGN_WARM * 0.55)

    def _front(self, c, t):
        s = self.s
        for x0, x1, edge in ((ENTRY[0] - 900, ENTRY[0], ENTRY[0]), (EXIT[1], EXIT[1] + 900, EXIT[1])):
            if not s.visible(x0, x1):
                continue
            rect(c, x0, G - 1400, x1, FY + 120, MID * 1.05)
            for yy in np.arange(G - 1300, FY + 100, 160):
                c.line(x0, yy, x1, yy, MID * 0.85, 3)
            rect(c, edge - 14, G - 1400, edge + 14, FY + 120, STEEL * 0.9)
            c.line(edge - 14, G - 1400, edge - 14, FY + 120, lighten(STEEL, 1.4), 2)
            s.glow_draw(lambda g, x0=x0, x1=x1: g.polygon([(x0, G - 1400), (x1, G - 1400), (x1, FY + 120),
                                                           (x0, FY + 120)], np.zeros(3)))

    def _exit_door(self, c, t):
        if not self.s.visible(EXIT[0] - 50, EXIT[1] + 50):
            return
        u = smootherstep(seg(t, *self.door))
        bot = lerp(G, G - 514, u)
        if bot > G - 512:
            rect(c, EXIT[0], G - 520, EXIT[1], bot, IRON)
            for y in np.arange(G - 490, bot, 34):
                c.line(EXIT[0], y, EXIT[1], y, IRON * 0.7, 2)
            rect(c, EXIT[0], bot - 14, EXIT[1], bot, HAZARD * 0.7)

    # ----- on screen: Sprout's name card -----

    def screen(self, cv, ts):
        t = ts / self.STRETCH - self.LEAD
        a0, a1 = self.CARD
        if not (a0 <= t < a1 + 0.8):
            return
        a = smoothstep(seg(t, a0, a0 + 0.7)) * (1 - smoothstep(seg(t, a1, a1 + 0.7)))
        if a <= 0.01:
            return
        W, H = 1240, 210
        x0, y0 = 960 - W // 2, 1080 - 30 - H
        x1, y1 = x0 + W, y0 + H
        bg = cv.target.copy() if a < 0.999 else None
        g = self.s.glow.layer
        k = cv.s
        g[max(0, int(y0 * k)):int(y1 * k) + 1, max(0, int(x0 * k)):int(x1 * k) + 1] = 0
        cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], CARD_WOOD * 0.75)
        cv.polygon([(x0 + 8, y0 + 8), (x1 - 8, y0 + 8), (x1 - 8, y1 - 8), (x0 + 8, y1 - 8)], CARD)
        pic = (x0 + 24, y0 + 20, x0 + 214, y1 - 20)
        cv.polygon([(pic[0], pic[1]), (pic[2], pic[1]), (pic[2], pic[3]), (pic[0], pic[3])], np.array([226, 236, 214]))

        def draw_pic(cc):
            p = probe("sprout", 0.62, (pic[0] + pic[2]) / 2 - 8, pic[3] - 6)
            p.smile, p.attend = 0.8, 1.0
            p.draw(cc, t)
        clipped(cv, self.s.glow, pic, draw_pic)
        title, lines = CARD_LINES
        cx = (x0 + 240 + x1 - 40) // 2
        cv.text(title, cx, y0 + H // 2 - 52, 62, INK)
        for q, ln in enumerate(lines):
            cv.text(ln, cx, y0 + H // 2 + 14 + q * 42, 34, INK * 1.25)
        if bg is not None:
            cv.target[:] = (bg * (1 - a) + cv.target * a).astype(np.uint8)


# ====================================================================== NK_HOME: Sprout's very first tree

class NKHomeAct(NewKeeperAct, VillageAct):
    name = "nk_home"
    OUT_ORDER = ["wheels", "springs", "tentacles", "lantern", "digger", "sprout", "teeth"]   # furthest first
    HOLE = 3700.0                                   # where Sprout plants its acorn (by the oak)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        k = scene.k
        self.out = {kd: 0.8 + 1.6 * q for q, kd in enumerate(self.OUT_ORDER)}
        self.step = {kd: self.out[kd] + DEPTH_T for kd in self.OUT_ORDER}
        # Twigs right of the oak: his LEFT blade reaches a short dead branch sticking out of the trunk
        self.TW = 4100.0
        tw = probe("teeth", k, self.TW, G, hands=True)
        self.p_cut = 0.9
        # Sprout right of the hole (its acorn hand over it), Digs left of it, the others watching further left
        self.SPOT = {"sprout": self.HOLE + 76.0, "digger": self.HOLE - 150.0, "teeth": self.TW,
                     "lantern": 3110.0, "tentacles": 2830.0, "springs": 2515.0, "wheels": 2280.0}
        self.walk = {kd: Route(self.x_in, self.step[kd]).go(self.SPOT[kd], v=170) for kd in self.OUT_ORDER}
        self.home = {kd: self.walk[kd].t for kd in self.OUT_ORDER}
        t_tw = self.home["teeth"] + 1.0
        self.TRIM = (t_tw, t_tw + 1.0, t_tw + 2.2, t_tw + 4.6)    # blade out, lift, saw, cut
        bx, by, _, _ = self._blade_tip(tw, self.TRIM[2] + 1.0)
        self.cut = (bx, by)
        self.branch = [(TREE_X + 22, by - 0.07 * (bx - TREE_X - 22)), (bx + 60, by + 0.07 * 60)]
        t_dig = max(self.home["digger"], self.home["sprout"], self.TRIM[3] + 2.4) + 1.0
        self.DIG = (t_dig, t_dig + 4.0)
        self.DROP = self.DIG[1] + 1.4
        self.FILL = (self.DROP + 1.6, self.DROP + 4.6)
        # a watering can waits on a little stump by the oak, its handle right where Sprout's right hand stops
        # (owner 2026-11-03: two normal hands, no watering-can hand; Sprout picks a can up)
        sp = probe("sprout", k, self.SPOT["sprout"], G)
        self.PICK = self.home["sprout"] + 0.8
        self.can_grip = sp.sprout_arm(self.PICK, 0.0, 1)[1]
        self.stump_top = self.can_grip[1] + sp.can_bottom(self.can_grip)
        # Digs steps back, Sprout hops over the little mound so the rose of its watering can is over it
        self.walk["digger"].wait(self.FILL[1] + 0.3).go(3320.0, v=120)
        self.HOP = self.walk["digger"].t - 0.4
        # (a step up to the mound, a little hop over it, a step on: the can in its hand never jerks)
        rx = probe("sprout", k, 0.0, G, can=True, water=1.0).can_rose(0.0)[0]
        r = Route(self.HOLE + 76.0, self.HOP).go(self.HOLE + 55.0, v=60, ramp=0.3)
        self.sprout_hop = Jump(self.HOLE + 55.0, G, self.HOLE - 55.0, G, apex=28)
        self.HOP2 = r.t
        r.wait(self.HOP2 + self.sprout_hop.dur)
        r.x = self.HOLE - 55.0                      # where the hop lands
        r.go(self.HOLE - rx, v=60, ramp=0.3)
        self.sprout_steps = r
        self.WATER = (r.t + 0.8, r.t + 8.8)
        self.GROW = (self.WATER[0] + 1.6, self.WATER[1] - 0.6)
        self.CHEER = self.GROW[1] + 0.8
        d = NR.say(self, self.CHEER + 1.4, FINALE)
        self.dur = self.CHEER + 1.4 + d + 3.0
        NR.say(self, self.dur + 1.6, SIGNOFF)       # over the end sign

    def _blade_tip(self, m, t):
        m.punch_l, m.blades, m.blades_l = self.p_cut, 0.0, 1.0
        x, y = m.blade_tip(-1, t)
        m.punch_l = 0.0
        return x, y, 0, 0

    def props(self, t):
        sp = self.m("sprout")
        if sp is None or t < self.PICK:
            return {"can": self.can_grip}
        return {"can": sp.sprout_arm(t, 0.0, 1)[1]}

    def _can_stump(self, c, t):
        """The little stump by the oak and the watering can standing on it until Sprout picks it up."""
        gx, top = self.can_grip[0] + 8, self.stump_top
        c.polygon([(gx - 34, G + 4), (gx + 34, G + 4), (gx + 30, top + 4), (gx - 30, top + 4)], BARK_C)
        c.polygon(ellipse(gx, top + 4, 30, 7, 24), lighten(WOOD, 1.25))
        c.polyline(ellipse(gx, top + 4, 17, 4, 20), WOOD, 1.5, closed=True)
        sp = self.m("sprout")
        if t < self.PICK and sp is not None:
            sp._draw_can(c, t, hd=self.can_grip, th=0.0)

    def target(self, t):
        keys = [(0.0, 4350.0, None, 1.0), (self.out["digger"] + 1.0, 4100.0, None, 0.95),
                (self.TRIM[0] - 1.0, 3900.0, None, 1.05), (self.TRIM[3] + 2.0, 3900.0, None, 1.05),
                (self.DIG[0] + 2.0, self.HOLE + 60, None, 1.4), (self.HOP, self.HOLE - 20, None, 1.4),
                (self.GROW[1], self.HOLE - 40, None, 1.9),
                (self.CHEER + 3.5, self.HOLE - 100, None, 1.3), (self.dur, self.HOLE - 300, None, 0.85)]
        keys.sort(key=lambda e: e[0])
        return cam_keys(keys, t)

    def update(self, t, dt):
        self.reach = {}
        for kd in self.OUT_ORDER:
            m = self.m(kd)
            if m is None:
                continue
            y = G - GLO_UP if kd == "lantern" else G
            dy = 0.0
            u = depth_out(t, self.out[kd]) if t < self.step[kd] else 0.0
            self.door_depth[kd] = u
            fl = bump(t, self.step[kd] + 0.3, 1.1)
            if u > 0.0:
                if kd == "springs":
                    ph = ((t - self.out[kd]) / 0.55) % 1.0
                    dy, m.spring = -4 * 40 * ph * (1 - ph), 0.0
                self.doorway.walking(self, m, t, dt, u, y, dy)
                self.look_new(m, flash=fl)
                self._pose(m, kd, t)
                continue
            if kd == "springs":
                x, lift, sq = hops(self.x_in, self.SPOT[kd], self.step[kd], self.home[kd], t, apex=55, step=170)
                dy, m.spring = -lift, sq
            elif kd == "sprout" and t >= self.HOP:
                x = self.sprout_steps.at(t)
                if self.HOP2 <= t < self.HOP2 + self.sprout_hop.dur:
                    x, y = self.sprout_hop.at(t - self.HOP2)
            else:
                x = self.walk[kd].at(t)
            if t >= self.CHEER:
                dy += -10 * bump(t, self.CHEER + 0.3 * self.OUT_ORDER.index(kd), 0.5)
            self.place(m, x, t, dt, y=y, dy=dy)
            self.look_new(m, flash=fl + bump(t, self.CHEER + 0.3 * self.OUT_ORDER.index(kd), 1.1))
            self._pose(m, kd, t)
        self.fireflies()
        self._sounds(t)

    def _pose(self, m, kd, t):
        if kd == "teeth":
            m.saws, m.hands, m.bare = False, True, set()
            a, b, c_, d = self.TRIM
            m.blades = 0.0                              # only the cutting one comes out
            m.blades_l = smootherstep(seg(t, a, b)) * (1 - smootherstep(seg(t, d + 1.2, d + 2.0)))
            m.punch = 0.0
            m.punch_l = self.p_cut * smootherstep(seg(t, b, c_)) * (1 - smootherstep(seg(t, d + 0.2, d + 1.2)))
            if c_ <= t < d:
                m.punch_l += 0.03 * math.sin((t - c_) * 2 * math.pi * 1.4)
            m.grip = 0.0
        if kd == "sprout":
            m.acorn = t < self.DROP
            m.hold_out = smoothstep(seg(t, self.DROP - 1.2, self.DROP - 0.3)) * \
                (1 - smoothstep(seg(t, self.DROP + 0.6, self.DROP + 1.4)))
            m.water = smoothstep(seg(t, *self.WATER[:1], self.WATER[0] + 0.5)) if False else \
                smoothstep(seg(t, self.WATER[0], self.WATER[0] + 0.5)) * (1 - smoothstep(seg(t, self.WATER[1] - 0.5,
                                                                                            self.WATER[1])))
            m.attach = None
            m.wave = 0.0
            m.can = t >= self.PICK
        if kd == "digger":
            a, b = self.DIG
            f0, f1 = self.FILL
            m.dig = 0.0
            if a <= t < b or f0 <= t < f1:
                t0 = a if t < b else f0
                m.dig = 0.5 + 0.5 * math.sin((t - t0) * 2 * math.pi * 0.8 - math.pi / 2)

    def piece(self, t):
        (ax, ay), (bx, by) = self.branch
        cx, cy = self.cut
        yc = ay + (by - ay) * (cx - ax) / (bx - ax)
        cut_t = self.TRIM[3]
        if t < cut_t:
            return None
        tau = t - cut_t
        land = math.sqrt(2 * (G - 8 - max(yc, by)) / GRAVITY)
        d = fall_y(0, min(tau, land))
        return cx, yc + d, bx, by + d - 8 * smoothstep(min(1.0, tau / max(land, 1e-3)))

    def acorn_at(self, t):
        """Sprout's acorn after it lets go: drops into the hole."""
        sp = self.m("sprout")
        x, y = sp.acorn_xy(t) if t < self.DROP else self._drop0
        tau = t - self.DROP
        floor_ = G + 6
        land = math.sqrt(max(0.0, 2 * (floor_ - y) / GRAVITY))
        return x, fall_y(y, min(tau, land))

    def _sounds(self, t):
        for kd in self.OUT_ORDER:
            if self.crossed(self.step[kd] + 0.3):
                self.hit(self.step[kd] + 0.3, "soft_bell", 79, 0.08, self.m(kd).x, G - 200)
        a, b, c_, d = self.TRIM
        if self.crossed(a):
            self.fx(a, "servo", b - a, 0.08, self.TW, G - 300)
        if self.crossed(c_):
            self.fx(c_, "saw", d - c_, 0.06, self.cut[0], self.cut[1])
        if self.crossed(d + 0.45):
            self.hit(d + 0.45, "thud", 48, 0.14, self.cut[0] + 60, G)
        if self.crossed(d + 1.4):
            self.chat(d + 1.4, "teeth", "hehe", icon="smile")
        if self.crossed(self.DIG[0]):
            self.fx(self.DIG[0], "sand_scrape", self.DIG[1] - self.DIG[0], 0.1, self.HOLE, G)
        if self.crossed(self.DIG[1] + 0.3):
            self.chat(self.DIG[1] + 0.3, "digger", "mm")
        if self.crossed(self.DROP - 0.8):
            self.chat(self.DROP - 0.8, "sprout", "hm", icon="acorn")
        if self.crossed(self.DROP + 0.45):
            self.hit(self.DROP + 0.45, "pluck", 62, 0.12, self.HOLE, G)
        if self.crossed(self.FILL[0]):
            self.fx(self.FILL[0], "sand_scrape", self.FILL[1] - self.FILL[0], 0.08, self.HOLE, G)
        if self.crossed(self.WATER[0]):
            self.fx(self.WATER[0], "sand_patter", self.WATER[1] - self.WATER[0], 0.06, self.HOLE, G)
        if self.crossed(self.GROW[1] - 0.5):
            self.chat(self.GROW[1] - 0.5, "sprout", "ooh")
        if self.crossed(self.CHEER):
            self.chorus(self.CHEER, self.OUT_ORDER, "yay", gap=0.3)
        for q in range(len(self.OUT_ORDER)):
            if self.crossed(self.CHEER + 0.3 * q):
                self.hit(self.CHEER + 0.3 * q, "soft_bell", 72 + 2 * q, 0.08, self.HOLE, G - 200)

    def aside_moods(self, t):
        if t > self.DIG[0] - 1 or NR.speaking(self, t):
            return []
        return ["mm", "hehe", "aww", "ooh"]

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)
        for j, x in enumerate((-300, 300, TREE_X)):
            if s.visible(x - 260, x + 260):
                tree(c, x, G, 640 + 60 * (j % 3), 950 + j)
        self.hill.back(c, s, t, 1.0)
        self.bush(c)
        self._branch(c, t)
        self.draw_village(c, t, peek=1.0)
        hx = 3150.0 + 18 * math.sin(t * 0.25)
        if s.visible(hx - 80, hx + 80):
            curled_hog(c, hx, G, 1.45, 1 if math.cos(t * 0.25) > 0 else -1, 0.0, t)
        self._ground(c, t)
        self._can_stump(c, t)
        self.glo_light(c, k=0.8)
        self.doorway.draw_inside(self, c, t, self.door_depth)
        self.hill.front(c, s, t, 1.0)
        self.draw_monsters(c, t, kinds=self.outside())
        if self.CHEER - 2 <= t:                     # a living touch: a bird flies over as they cheer
            from . import props as PR
            bx = 2600 + 150 * (t - self.CHEER + 2)
            PR.bird(c, bx, G - 560 - 40 * math.sin((bx - 2600) / 300.0), 1.0, 1, 0.5 + 0.5 * math.sin(t * 13), t=t)

    def _branch(self, c, t):
        (ax, ay), (bx, by) = self.branch
        cx, _ = self.cut
        yc = ay + (by - ay) * (cx - ax) / (bx - ax)
        col = BARK_C * 1.05
        c.line(ax, ay, cx, yc, col, 13)
        pc = self.piece(t)
        if pc is None:
            pc = (cx, yc, bx, by)
        x0, y0, x1, y1 = pc
        c.line(x0, y0, x1, y1, col, 11)
        c.line(lerp(x0, x1, 0.5), lerp(y0, y1, 0.5), lerp(x0, x1, 0.5) + 14, lerp(y0, y1, 0.5) - 26, col, 5)
        if t >= self.TRIM[3]:
            c.circle(cx, yc, 6, lighten(WOOD, 1.25))

    def _ground(self, c, t):
        """The hole Digs digs, the dirt beside it, the acorn dropping in, the mound, the new little tree."""
        x = self.HOLE
        a, b = self.DIG
        dug = smoothstep(seg(t, a, b))
        filled = smoothstep(seg(t, *self.FILL))
        if t >= self.DROP and not hasattr(self, "_drop0"):
            self._drop0 = self.m("sprout").acorn_xy(self.DROP)
        pile = dug * (1 - filled)
        if pile > 0.01:                              # the dug-out dirt in a little heap to Digs' side
            c.polygon(ellipse(x - 62, G + 2, 34 * pile + 6, 18 * pile + 2, 20, math.pi, 2 * math.pi), SOIL * 1.15)
        if dug > 0.01 and filled < 0.99:
            c.polygon(ellipse(x, G + 4, 28 * dug, 9 * dug * (1 - filled), 20), SOIL * 0.55)
        if t >= self.DROP and filled < 0.6:
            ax, ay = self.acorn_at(t)
            acorn_nut(c, ax, ay, 10.0 * 0.55 / 0.55 * 1.0)
        if filled > 0.01:
            c.polygon(ellipse(x, G + 4, 30, 12 * filled, 22, math.pi, 2 * math.pi), SOIL * 1.05)
        g = smoothstep(seg(t, *self.GROW))
        if g > 0.01:
            seedling(c, x, G - 6 * filled, 0.95, t, grow=g)
        if a <= t < b + 0.3 or self.FILL[0] <= t < self.FILL[1]:
            p = self.s.particles
            if p.rng.uniform() < 0.35:
                p.burst(x - 10, G - 4, 1, SOIL * 1.2, 160, 0.7, 4.0, g=900, spread=0.5, direction=-math.pi * 0.7)
