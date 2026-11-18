"""Forest Keepers episode 7: The River Raft Race (docs/engines/forest_keepers_raft_race.md).

  LEAF     - at the water wheel from episode 4: a leaf with a ladybird on it floats down the mill race, past the wheel
             and away down the stream. Digs has an idea: rafts!
  RAFTS    - on the bank above the brook's top pool: a row of six rafts, built bit by bit. Wheels brings the logs, Twigs
             trims every raft's four logs at the stop board (all the same length), Hans lashes them with his tentacles,
             Springs bounces each deck tight, Glo sets the mast and his light turns each leaf sail a Keeper's colour.
             Then every Keeper carries their own raft to the water and sets it in behind the log boom.
  RACE     - 3, 2, 1: Springs lifts the latch, the boom swings open and the six rafts race down the brook (real water
             physics, rafts.py): the riffle, the first falls, the quiet pool, the rapids, the second falls, the glide to
             the finish rope. Springs bounces along the bank beside them, Glo lights the way, the others cheer at the
             finish on the far bank.
  CHEER    - the winner's Keeper cheers; the rafts bump against the boom in the finish pool; a duck and her ducklings
             paddle over to see; pull back over the lit brook.
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, Jump, Night, PLANK, ellipse, lerp, rect, seg, smoothstep, \
    smootherstep
from families.foundry.keepers.halloween import hops, path
from families.foundry.tree_monsters import LAMP, TRUNK

from . import rafts as R
from .animal_houses import saw_to
from .marble_run import KEEPERS, MarbleAct, cam

G = R.G
LANE_KIND = list(R.KINDS)                      # lane j carries this Keeper's raft
COLS = {k: np.asarray(v, np.float64) for k, v in R.MARBLE_COLS.items()}


def smooth_surface(x):
    """The water level averaged over a stretch either side (for things that float well above it: no steps)."""
    return sum(R.surface(x + d) for d in np.linspace(-320.0, 320.0, 17)) / 17.0


def far_bank_y(x):
    """Where someone stands on the far bank (x on screen: the far bank is drawn FAR_DX right of lane 0)."""
    return R.far_edge(x - R.FAR_DX) - 42.0


class RaftAct(MarbleAct):
    """An act of the raft episode: a late-autumn night by the brook, leaves falling, the Keepers talk."""

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + 77), G + 2000, 5000, 15000)

    def backdrop(self, c, t):
        self.night.draw(self.s, c, t)
        R.draw_far(c, self.s, t)

    def brook(self, c, t, rafts=None, boom=0.0, finish=True, lit=1.0, between=None, far=None):
        """The brook in layers: far bank (and whoever stands on it: far(c)), the water, rocks / lily pads / rafts
        lane by lane from the back, the booms, the near bank. rafts(c, j): draws lane j's raft. between(c): after the
        water things, before the near bank."""
        s = self.s
        R.draw_far_bank(c, s)
        if finish:
            R.draw_finish_back(c, s, t, lit)
        if far is not None:
            far(c)
        R.draw_water(c, s, t)

        def booms(d0, d1):                       # the slice of each boom between these depths (lanes from us)
            if s.visible(R.END_BOOM - 400, R.END_BOOM + 400):
                R.draw_boom(c, R.END_BOOM, 0.0, d0, d1)
            if s.visible(R.START_BOOM - 400, R.START_BOOM + 400):
                R.draw_boom(c, R.START_BOOM, boom, d0, d1)
        booms(R.N_LANES - 0.5, 99.0)
        for j in reversed(range(R.N_LANES)):
            booms(j - 0.5 if j > 0 else -99.0, j + 0.5)
            for (xr, lj, r, h) in R.ROCKS:
                if lj == j and s.visible(xr - 200, xr + 200):
                    R.draw_rock(c, xr, j, r, h, t)
            for k, (xl, lj) in enumerate(R.LILY):
                if lj == j and s.visible(xl - 200, xl + 200):
                    R.draw_lily(c, xl, j, t, k)
            if rafts is not None:
                rafts(c, j)
        if between is not None:
            between(c)
        R.draw_near_bank(c, s, t)
        if finish and s.visible(R.FINISH_X - 300, R.FINISH_X + 300):
            R.draw_finish_front(c)

    def glo_light(self, c, x, y, k=1.0):
        """Glo's lantern lights the water under him."""
        wy = R.surface(x) - R.FAR_DEPTH * 0.4
        self.s.glow_draw(lambda g: g.polygon([(x - 30, y), (x + 30, y), (x + 200, wy), (x - 160, wy)], LAMP * 0.05 * k))
        self.s.glow_draw(lambda g: g.polygon(ellipse(x + 20, wy, 230, 60, 24), LAMP * 0.05 * k))

    def raft_in_water(self, c, j, x, y, th, vx, t, L, dye=1.0):
        """Lane j's raft floating at (x, y) (lane-0 coordinates)."""
        dx, dy, sc = R.lane_off(j)
        k = LANE_KIND[j]
        st = R.stretch_at(x)
        wy = R.surface(x) - R.rock_pillow(x, j) + R.wave(x, t, st[6], j)
        if R.FALLS[0] - 30 < x < R.FALLS[0] or R.FALLS[1] - 30 < x < R.FALLS[1]:
            wy = R.surface(x - 40)
        u = R.current(x, j, t)
        sl = 0.0 if any(abs(x - xf) < 90 for xf in R.FALLS) else (R.surface(x + 40) - R.surface(x - 40)) / 80.0
        R.draw_raft(c, x + dx, y + dy, th, L, COLS[k], sc=sc, t=t, water=wy + dy if y < wy + 40 else None,
                    wake=0.0 if any(0 < x - xf < 140 for xf in R.FALLS) else abs(vx - u), shade=1.0 - 0.04 * j,
                    slope=sl)


# ====================================================================== RACE

FAR_WATCH = {"wheels": 12650.0, "digger": 12800.0, "tentacles": 13230.0, "teeth": 13380.0}
SPRINGS_START = R.START_BOOM + R.FAR_DX - 60.0      # by the boom's hinge post on the far bank


class RaftRaceAct(RaftAct):
    """3, 2, 1: the boom swings open and the six rafts race down the brook."""
    name = "raft_race"
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.race = R.Race(int(P.get("race_seed", 6)))
        self.T = dict(count=3.5, go=6.5)
        self.go = self.T["go"]
        self.fin = [self.go + f for f in self.race.finish]
        self.first = min(self.fin)
        self.dur = max(self.fin) + 4.0
        self.hud = {i: float(i) for i in range(R.N_LANES)}
        self.lead_said, self._lead = -9.0, None
        win = self.race.order[0]
        self.stats = {"raft_seed": self.race.seed, "raft_finish_s": [round(f, 2) for f in self.race.finish],
                      "raft_order": [R.NAMES[LANE_KIND[i]] for i in self.race.order],
                      "raft_winner": R.NAMES[LANE_KIND[win]], "raft_lead_changes": self.race.changes,
                      "raft_holds_s": self.race.holds()}
        self._plan_springs()
        self.glo = None

    def aside_moods(self, t):
        if self.go < t < self.first:
            return []
        return ["ooh", "hehe", "q", "aww"]

    # ----- the rafts -----

    def raft(self, i, t):
        """(x, y, pitch, vx) of lane i's raft at act time t."""
        tau = t - self.go
        run = self.race.runs[i]
        if tau < 0:
            x, y, th, vx, _ = run.at(0.0)
            st = R.stretch_at(x)
            return x, R.surface(x) + R.wave(x, t, st[6], i), 0.0, 0.0
        x, y, th, vx, _ = run.at(tau)
        return x, y, th, vx

    def pack(self, tau):
        xs = sorted(self.race.runs[i].at(max(0.0, tau))[0] for i in range(R.N_LANES))
        return xs

    # ----- Springs bounces along the bank beside them -----

    def _plan_springs(self):
        """A chain of real hops along the far bank (behind the water, so he never hides a raft), keeping up with the
        middle of the pack, from the boom latch to the finish."""
        t = self.go + 1.0
        x = SPRINGS_START
        self.sp_hops = []
        while x < R.FINISH_X - 420 and t < self.first + 2:
            xs = self.pack(t + 0.5 - self.go)
            want = min(xs[2] - 60, R.FINISH_X - 420)
            if want - x < 40:
                t += 0.25                                   # waits for them
                continue
            x1 = min(x + 240.0, want)
            jp = Jump(x, far_bank_y(x), x1, far_bank_y(x1), apex=60)
            self.sp_hops.append((t, jp))
            t += jp.dur + 0.06
            x = x1
        self.sp_end = t

    def springs_xy(self, t, m):
        m.spring = 0.0
        if not self.sp_hops or t < self.sp_hops[0][0]:
            return SPRINGS_START, far_bank_y(SPRINGS_START)
        for i, (t0, jp) in enumerate(self.sp_hops):
            nxt = self.sp_hops[i + 1][0] if i + 1 < len(self.sp_hops) else 1e9
            if t0 <= t < t0 + jp.dur:
                return jp.at(t - t0)
            if t0 + jp.dur <= t < nxt:
                m.spring = 0.8 * max(0.0, 1 - (t - t0 - jp.dur) / 0.12)
                return jp.x1, jp.y1
        return self.sp_hops[-1][1].x1, self.sp_hops[-1][1].y1

    # ----- camera -----

    def target(self, t):
        h = self.s.h
        if t < self.go + 0.8:
            x = R.START_BOOM + 60
            return x, R.surface(x) - 240, 1.2
        if t < self.first + 1.5:
            tau = t - self.go
            ld = self.race.leader(tau)
            xl = self.race.runs[ld].at(tau)[0]
            xs = self.pack(tau)
            px = 0.55 * xl + 0.45 * (xs[2] + xs[3]) / 2 + 60
            return px, R.surface(px) - 225, 1.42
        u = smoothstep(seg(t, self.first + 1.5, self.first + 4.0))
        x = lerp(R.FINISH_X + 80, R.FINISH_X + 300, u)
        return x, R.surface(x) - 260, lerp(1.25, 1.05, u)

    @property
    def cam_omega(self):
        return 1.8

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        for kind, x in FAR_WATCH.items():
            m = self.m(kind)
            if m is None:
                continue
            dy = 0.0
            fin = self.fin[LANE_KIND.index(kind)]
            if t > fin:                                   # its raft is in: a little happy hop now and then
                ph = (t - fin) % 1.6
                dy = -4 * 30 * (ph / 0.4) * (1 - ph / 0.4) if ph < 0.4 and t < fin + 6.0 else 0.0
            m.punch = 0.5 if (kind == "wheels" and self.go < t < self.first + 3) else 0.0
            self.place(m, x, t, dt, y=far_bank_y(x), dy=dy, k=0.9)
        m = self.m("springs")
        if m is not None:
            x, y = self.springs_xy(t, m)
            m.punch = smoothstep(seg(t, self.go - 0.5, self.go)) * (1 - smoothstep(seg(t, self.go + 0.4, self.go + 0.9)))
            self.place(m, x, t, dt, y=y, k=0.9)
        self._glo(t, dt)
        self._hud(t, dt)
        self.leaves(0.03)
        self._sounds(t)

    def glo_x(self, t):
        tau = t - self.go
        if tau < 0:
            return R.START_BOOM + 60
        ld = self.race.leader(tau)
        return self.race.runs[ld].at(tau)[0] + 40

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        want = self.glo_x(t)
        if t > self.first:
            want = R.FINISH_X + 200
        if self.glo is None:
            self.glo = [want, 0.0]
        # floats after the leader: a soft spring, so he glides (never jumps) when the lead changes
        x, v = self.glo
        a = 6.0 * (want - x) - 4.5 * v
        v += a * dt
        v = max(-420.0, min(420.0, v))
        x += v * dt
        self.glo = [x, v]
        m.lamp = 1.25
        self.place(m, x, t, dt, y=smooth_surface(x) - 300 + 12 * math.sin(t * 1.4))

    def _hud(self, t, dt):
        order = self.race.standings(max(0.0, t - self.go))
        for slot, i in enumerate(order):
            self.hud[i] += (slot - self.hud[i]) * min(1.0, dt * 7.0)

    # ----- sounds -----

    def _sounds(self, t):
        T, Rc = self.T, self.race
        if self.crossed(0.2):
            self.fx(t, "gurgle", self.dur, 0.05, R.START_BOOM, R.surface(R.START_BOOM))
        if self.crossed(1.0):
            self.chat(t, "springs", "hey", icon="!")
        for q, (icon, kind) in enumerate((("3", "springs"), ("2", "lantern"), ("1", "springs"))):
            if self.crossed(T["count"] + q * 1.0):
                self.chat(t, kind, "hey", icon=icon, step=q * 2)
        if self.crossed(self.go):
            self.hit(t, "clunk", 48, 0.26, R.START_BOOM, R.surface(R.START_BOOM))
            self.chat(t + 0.3, "springs", "wee")
        tau0, tau1 = self.s.prev_t - self.t0 - self.go, t - self.go
        for i, run in enumerate(Rc.runs):
            for (te, kind, x, y, v) in run.events:
                if tau0 < te <= tau1:
                    if kind == "splash":
                        self.fx(t, "splash", 0.7, 0.12 + 0.2 * v, x, y)
                        self.s.particles.burst(x + R.lane_off(i)[0], y + R.lane_off(i)[1], 10, R.FOAM, 220 * (0.5 + v),
                                               0.7, 5, g=1400, up=200, spread=1.4)
                    elif kind == "rock":
                        self.hit(t, "thud", 50, 0.06 + 0.08 * v, x, y)
                        self.s.particles.burst(x + 40 + R.lane_off(i)[0], y + R.lane_off(i)[1], 4, R.FOAM, 120, 0.5, 4,
                                               g=1200, up=120, spread=1.0)
                    elif kind == "drop":
                        self.chat(t, LANE_KIND[i], "wee") if i == Rc.leader(tau1) else None
                    elif kind == "boom":
                        self.hit(t, "clack", self.s.note(i, -1), 0.08 + 0.1 * v, x, y)
            if self.crossed(self.fin[i]):
                place = Rc.order.index(i)
                self.hit(t, "soft_bell", self.s.note(6 - place, 0), 0.25 if place == 0 else 0.14, R.FINISH_X, R.surface(R.FINISH_X))
                if place == 0:
                    for q, n in enumerate((72, 76, 79, 84)):
                        self.hit(t + 0.15 + q * 0.11, "chime", n, 0.2, R.FINISH_X, R.surface(R.FINISH_X) - 200)
        for f, xf in enumerate(R.FALLS):                  # the falls rush louder as we pass them
            pass
        for i, (t0, jp) in enumerate(self.sp_hops):
            if self.crossed(t0) and i % 2 == 0:
                self.hit(t, "boing", 62 + (i % 4) * 2, 0.1, jp.x0, jp.y0)
        if self.go < t < self.first:
            ld = Rc.leader(t - self.go)
            if ld != self._lead and t - self.lead_said > 2.2:
                self._lead = ld
                self.lead_said = t
                self.chat(t, LANE_KIND[ld], "wee" if self.s.particles.rng.uniform() < 0.5 else "yay", icon="note")
        if self.crossed(self.first + 0.4):
            win = LANE_KIND[Rc.order[0]]
            self.chat(t, win, "yay", icon="star")
            others = [k for k in KEEPERS if k != win]
            self.chorus(t + 0.9, others, "yay", gap=0.22, icon="star")

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)
        boom = smootherstep(seg(t, self.go, self.go + 0.9))

        def rafts(c, j):
            x, y, th, vx = self.raft(j, t)
            if s.visible(x - 200, x + 200):
                self.raft_in_water(c, j, x, y, th, vx, t, self.race.traits[j].length)

        def far(c):
            self.draw_monsters(c, t, kinds=list(FAR_WATCH) + ["springs"])

        def between(c):
            gl = self.m("lantern")
            if gl is not None:
                self.glo_light(c, gl.x, gl.y - 100)
        self.brook(c, t, rafts=rafts, boom=boom, far=far, between=between)
        self.draw_monsters(c, t, kinds=["lantern"])
        self._draw_hud(c, t)

    def _draw_hud(self, c, t):
        """The standings: six sails in race order in a little wooden strip at the top left."""
        a = smoothstep(seg(t, self.go - 1.5, self.go - 0.5)) * (1 - smoothstep(seg(t, self.dur - 1.5, self.dur - 0.5)))
        if a <= 0.01:
            return
        x0, x1, y0, y1 = self.s.view()
        u = 1.0 / self.s.zoom
        px, py = x0 + 34 * u, y0 + 34 * u
        w, row = 250 * u, 42 * u
        bg = np.array([14, 16, 24], np.float64)
        rect(c, px, py, px + w, py + row * R.N_LANES + 16 * u, bg + (np.array([96, 70, 48]) - bg) * a)
        c.polyline([(px, py), (px + w, py), (px + w, py + row * R.N_LANES + 16 * u), (px, py + row * R.N_LANES + 16 * u)],
                   bg + (np.array([150, 112, 72]) - bg) * a, 3 * u, closed=True)
        for slot in range(R.N_LANES):
            c.text(str(slot + 1), px + 24 * u, py + 8 * u + row * (slot + 0.5), 26 * u,
                   bg + (np.array([236, 226, 200]) - bg) * a)
        for i in range(R.N_LANES):
            yy = py + 8 * u + row * (self.hud[i] + 0.5)
            col = COLS[LANE_KIND[i]]
            sx = px + 64 * u
            c.polygon([(sx - 4 * u, yy - 15 * u), (sx + 12 * u, yy - 8 * u), (sx + 14 * u, yy + 4 * u),
                       (sx - 4 * u, yy + 10 * u)], bg + (col - bg) * a)
            c.line(sx - 5 * u, yy - 17 * u, sx - 5 * u, yy + 14 * u, bg + (TRUNK * 1.2 - bg) * a, 3 * u)
            c.text(R.NAMES[LANE_KIND[i]], px + 90 * u, yy, 24 * u, bg + (np.array([236, 226, 200]) - bg) * a,
                   anchor="lm")
            if t >= self.fin[i] and self.race.order[0] == i:
                c.text("*", px + w - 26 * u, yy + 4 * u, 34 * u, bg + (np.array([246, 196, 70]) - bg) * a)


# ====================================================================== RAFTS (the workshop on the bank)

SPOT = [6720.0 + 215.0 * i for i in range(6)]       # where raft i is built (middle of its logs)
RY = R.PLATEAU_Y + 36.0                             # the rafts lie on the bank in front of the Keepers
PILE_X = 6400.0                                     # the log pile
MAST_X = 6260.0                                     # six masts with pale leaves lean here
SLIP = (7905.0, 8000.0)                             # the slipway Digs makes: from the bank down into the pool
L = R.RAFT_L
S = 6.0                                             # one raft per job every S seconds
W_SPEED = 380.0                                     # Wheels rolling with a load of logs
HEAD = {"wheels": 338.0, "tentacles": 455.0, "teeth": 440.0, "springs": 268.0, "digger": 292.0}
DECK = RY - 16.0                                    # where Springs stands on a deck


def ragged(i):
    """The four raw logs of raft i stick out past the cut line by these amounts (they came off a pile)."""
    rs = np.random.default_rng(40 + i)
    return [float(v) for v in rs.uniform(14, 46, 4)]


def draw_offcut(c, x, y, ln, k):
    c.polygon([(x, y - 6), (x + ln, y - 6), (x + ln, y + 6), (x, y + 6)], R.LOG * (0.9 - 0.04 * k))
    c.circle(x, y, 6, R.LOG_END * 0.9)


def draw_mast_free(c, x, y, ang, col, dye, t):
    """A mast with its leaf sail, not on a raft: (x, y) = its foot."""
    from families.foundry.keepers.common import Xform
    cv = Xform(c, 0, 0, ang, 1.0, x, y)
    cv.line(x, y, x, y - 78, TRUNK * 1.15, 5)
    scol = lerp(R.SAIL_RAW, np.asarray(col, np.float64), dye)
    leaf = [(x + 3, y - 70), (x + 28, y - 60), (x + 46, y - 36), (x + 36, y - 12), (x + 3, y - 4)]
    cv.polygon(leaf, scol)
    cv.polyline(leaf, scol * 0.7, 2, closed=True)
    cv.line(x + 3, y - 66, x + 30, y - 26, scol * 0.65, 2)


class RaftsAct(RaftAct):
    """The raft workshop on the bank above the top pool: six rafts built side by side, every Keeper at their own job
    raft after raft (so the rafts come out the same), then each carries their own to the water."""
    name = "rafts"
    names = (1.0, 8.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        # Wheels' trips: pick up four logs at the pile, roll to the raft's spot, set them down, back for the next
        self.w_trips = []
        t = 2.0
        for i in range(6):
            d = SPOT[i] - PILE_X - 40
            pick, go = t, t + 0.8
            arrive = go + d / W_SPEED
            drop = arrive + 0.8
            self.w_trips.append((pick, go, arrive, drop))
            t = drop + d / W_SPEED
        self.w_done = t
        self.t_cut = [max(6.5 + S * i, self.w_trips[i][3] + 1.0) for i in range(6)]
        self.t_tie = [self.t_cut[i] + S for i in range(6)]
        self.t_press = [self.t_tie[i] + S for i in range(6)]
        self.t_sail = [self.t_press[i] + S for i in range(6)]
        self.built = self.t_sail[5] + 3.4
        # Springs hops from raft to raft: (start, Jump)
        self.sp = []
        xs = [SPOT[0] - 260.0] + [SPOT[i] + 6 for i in range(6)] + [SPOT[5] + 210.0]
        ys = [R.PLATEAU_Y] + [DECK] * 6 + [R.PLATEAU_Y]
        for k in range(7):
            t0 = self.t_press[k] - 0.9 if k < 6 else self.t_press[5] + 2.6
            self.sp.append((t0, Jump(xs[k], ys[k], xs[k + 1], ys[k + 1], apex=70)))
        # the launch: owners carry their rafts to the slipway, nearest first, one every 2.6 s
        self.c0 = self.built + 3.0
        self.rank = {i: 5 - i for i in range(6)}
        self.launch = {i: self.c0 + 2.0 + 2.6 * self.rank[i] for i in range(6)}
        self.dur = self.launch[0] + 6.5
        self.slip_dug = (6.0, 26.0)
        self.rails = (27.0, 33.0)
        self.stats = {"rafts_built": 6, "rafts_even": True, "raft_len_px": L}

    def aside_moods(self, t):
        return ["hm", "hehe", "ooh", "mm"]

    # ----- each raft's state -----

    def logs_at(self, i, t):
        """Where raft i's logs are: None (in the pile), ('carry', x, y) on Wheels, ('ground', u) set down."""
        pick, go, arrive, drop = self.w_trips[i]
        if t < go:
            return None
        if t < arrive + 0.4:
            m = self.m("wheels")
            return ("carry", m.x, m.y - HEAD["wheels"] * m.k) if m is not None else None
        return ("ground", smoothstep(seg(t, arrive + 0.4, drop)))

    def cut_u(self, i, t):
        return smoothstep(seg(t, self.t_cut[i] + 0.6, self.t_cut[i] + 2.4))

    def ties(self, i, t):
        a = self.t_tie[i]
        return int(t >= a + 2.2) + int(t >= a + 4.2)

    def press(self, i, t):
        """How far raft i is squeezed down by Springs (px)."""
        a = self.t_press[i]
        out = 0.0
        for b in (a + 0.15, a + 1.0, a + 1.85):
            out = max(out, 3.0 * math.exp(-((t - b) / 0.12) ** 2))
        return out

    def mast_u(self, i, t):
        """0 = still in Glo's bundle, 0..1 being lowered into the deck, 1 = planted."""
        return smoothstep(seg(t, self.t_sail[i] + 0.5, self.t_sail[i] + 1.4)) if t >= self.t_sail[i] + 0.5 else 0.0

    def dye(self, i, t):
        return smoothstep(seg(t, self.t_sail[i] + 2.0, self.t_sail[i] + 2.9))

    def magic(self, i, t):
        a = self.t_sail[i]
        return smoothstep(seg(t, a + 1.6, a + 2.0)) * (1 - smoothstep(seg(t, a + 2.9, a + 3.4)))

    # ----- the launch -----

    def owner(self, i):
        return LANE_KIND[i]

    def carry_path(self, i):
        """Owner of raft i: where it stands to lift the raft, then the walk to the slipway with it."""
        kind = self.owner(i)
        lift = self.c0 - 0.6 + 0.0 * i
        arrive = self.launch[i] - 0.5
        top = SLIP[0] - 60.0
        return lift, arrive, top

    def raft_pos(self, i, t):
        """Raft i: ('built', x, y, th) on the bank, ('held', x, y, th) overhead, ('water', x, y, th, lane) launched."""
        lift, arrive, top = self.carry_path(i)
        if t < lift + 0.6:
            return ("built", SPOT[i], RY + self.press(i, t), 0.0)
        m = self.m(self.owner(i))
        if t < self.launch[i] and m is not None:
            if self.owner(i) == "lantern":
                hx, hy = m.x, m.y - 64 * m.k
            else:
                hx, hy = m.x, m.y - HEAD[self.owner(i)] * m.k - 8
            u = smootherstep(seg(t, lift + 0.6, lift + 1.2))
            x, y = lerp(SPOT[i], hx, u), lerp(RY, hy, u)
            if t > self.launch[i] - 0.6:                # set down at the top of the slipway
                v = smootherstep(seg(t, self.launch[i] - 0.6, self.launch[i]))
                x, y = lerp(hx, SLIP[0], v), lerp(hy, R.PLATEAU_Y + 30, v)
            return ("held", x, y, 0.0)
        # down the slipway (it slides: a little faster all the way) and out to its lane at the boom
        tau = t - self.launch[i]
        x0, y0 = SLIP[0], R.PLATEAU_Y + 30
        x1, y1 = SLIP[1] + 30, R.surface(SLIP[1]) + 2
        ang = math.atan2(y1 - y0, x1 - x0)
        ts = 0.7
        if tau < ts:
            u = (tau / ts) ** 2
            return ("water", lerp(x0, x1, u), lerp(y0, y1, u), ang * (1 - smoothstep(seg(u, 0.85, 1.0))), 0.0, tau)
        u = smootherstep(seg(tau, ts, ts + 3.6))
        xs = R.START_BOOM - 8 - L / 2
        x = lerp(x1, xs, u)
        lane = i * u
        st = R.stretch_at(x)
        y = R.surface(x) + R.wave(x, t, st[6], i) + 9 * math.exp(-(tau - ts) * 3) * math.sin((tau - ts) * 9)
        return ("water", x, y, 0.0, lane, tau)

    # ----- camera -----

    def target(self, t):
        mid = (SPOT[0] + SPOT[5]) / 2
        wide = (mid + 80, R.PLATEAU_Y - 300, 0.9)
        if t < 5.0:
            return lerp(6300.0, SPOT[0] + 200, smoothstep(seg(t, 1.0, 5.0))), R.PLATEAU_Y - 240, 1.2
        if t < self.built + 1.0:
            # follow the work front: between the newest cut and the newest sail
            lo = max([SPOT[i] for i in range(6) if t >= self.t_sail[i] - 1.0] + [SPOT[0]])
            hi = max([SPOT[i] for i in range(6) if t >= self.t_cut[i] - 2.0] + [SPOT[0]])
            x = (lo + hi) / 2 + 40
            return x, R.PLATEAU_Y - 200, 1.5
        if t < self.c0 + 1.0:
            return wide[0] + 300, wide[1], 0.95
        u = smootherstep(seg(t, self.c0 + 1.0, self.c0 + 6.0))
        return lerp(wide[0] + 300, 7980.0, u), lerp(wide[1], R.PLATEAU_Y - 280, u), lerp(0.95, 1.15, u)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._wheels(t, dt)
        self._twigs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._digs(t, dt)
        self._particles(t)
        self.leaves(0.04)
        self._sounds(t)

    def _carry_x(self, i, t, x_before):
        """The owner's x from the lift on: under the raft, walking to the slipway, then to a spot to watch."""
        lift, arrive, top = self.carry_path(i)
        watch = SLIP[0] - 330.0 - 120.0 * self.rank[i] if self.owner(i) != "lantern" else SLIP[1] + 100
        return path([(lift - 2.6, x_before, 0), (lift, SPOT[i], 0), (arrive - (top - SPOT[i]) / 260.0, SPOT[i], 0),
                     (arrive, top, 0), (self.launch[i] + 0.2, top, 0), (self.launch[i] + 2.6, watch, 0)], t)[0]

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        keys = [(0.0, PILE_X - 140, 0)]
        for (pick, go, arrive, drop) in self.w_trips:
            keys += [(pick, PILE_X + 20, 0), (go, PILE_X + 20, 0), (arrive, SPOT_W(arrive, self), 0)]
            keys += [(drop, keys[-1][1], 0)]
        keys += [(self.w_done, PILE_X + 20, 0), (self.w_done + 3.0, SPOT[0] - 150, 0)]
        x = path(keys, t)[0]
        if t >= self.c0 - 3.5:
            x = self._carry_x(0, t, SPOT[0] - 150)
        m.punch = 0.6 if any(p <= t < a + 0.5 for (p, g, a, d) in self.w_trips) else 0.0
        if t >= self.c0 - 0.6 and t < self.launch[0]:
            m.punch = 0.8
        self.place(m, x, t, dt, y=R.PLATEAU_Y)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run = 0.0
        stand = [SPOT[i] + L / 2 + 70 for i in range(6)]
        keys = [(0.0, SPOT[0] - 320, 0), (self.t_cut[0] - 1.5, stand[0], 0)]
        for i in range(6):
            keys += [(self.t_cut[i] - 0.3, stand[i], 0), (self.t_cut[i] + 2.8, stand[i], 0)]
        keys += [(self.t_cut[5] + 5.0, SLIP[0] - 200, 0)]
        x = path(keys, t)[0]
        m.punch, m.punch_l = 0.0, 0.0
        for i in range(6):
            a = self.t_cut[i]
            if a - 0.1 <= t < a + 2.7:
                # the left wrist saw down through the four logs at the cut line
                u = self.cut_u(i, t)
                tx, ty = SPOT[i] + L / 2 + 2, lerp(RY - 30, RY + 10, u)
                m.x = x
                x = saw_to(m, t, tx, ty, sx=-1) if t > a + 0.3 else x
                m.saw_run = 1.0 if a + 0.5 < t < a + 2.5 else 0.0
        if t >= self.c0 - 3.5:
            x = self._carry_x(2, t, SLIP[0] - 200)
        if self.c0 - 0.6 <= t < self.launch[2]:
            m.punch, m.punch_l = 0.9, 0.9
        self.place(m, x, t, dt, y=R.PLATEAU_Y)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        keys = [(0.0, SPOT[0] - 470, 0), (self.t_tie[0] - 1.8, SPOT[0], 0)]
        for i in range(6):
            keys += [(self.t_tie[i] - 0.4, SPOT[i], 0), (self.t_tie[i] + 4.5, SPOT[i], 0)]
        x = path(keys, t)[0]
        reach = []
        for i in range(6):
            a = self.t_tie[i]
            for q in range(2):                            # wraps the twine round and round, one lashing then the other
                b = a + 0.3 + 2.0 * q
                if b <= t < b + 1.9:
                    lx = SPOT[i] + (-0.3 if q == 0 else 0.3) * L + 6
                    ph = (t - b) * 9
                    reach.append((lx + 6 * math.cos(ph), RY - 10 + 9 * math.sin(ph)))
        if t >= self.c0 - 3.5:
            x = self._carry_x(1, t, SPOT[5])
            hs = self.raft_pos(1, t)
            if hs[0] == "held":
                reach = [(hs[1] - L * 0.3, hs[2] + 4), (hs[1] + L * 0.3, hs[2] + 4)]
        self.reach["tentacles"] = reach
        self.place(m, x, t, dt, y=R.PLATEAU_Y)

    def springs_at(self, t, m):
        """On the bank, then hop by hop from deck to deck (bouncing each one tight), then down again."""
        m.spring = 0.0
        x, y = self.sp[0][1].x0, self.sp[0][1].y0
        for k, (t0, jp) in enumerate(self.sp):
            if t >= t0:
                if t < t0 + jp.dur:
                    return jp.at(t - t0)
                x, y = jp.x1, jp.y1
                if t - t0 - jp.dur < 0.12:
                    m.spring = 0.8 * (1 - (t - t0 - jp.dur) / 0.12)
        for i in range(6):                                 # two little bounces on each deck
            a = self.t_press[i]
            for b in (a + 0.15, a + 1.0):
                if b <= t < b + 0.85:
                    u = (t - b) / 0.85
                    y -= 4 * 34 * u * (1 - u)
                    if u > 0.9 or u < 0.1:
                        m.spring = 0.7
        return x, y

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y = self.springs_at(t, m)
        if t >= self.c0 - 3.5:
            lift, arrive, top = self.carry_path(3)
            x = self._carry_x(3, t, self.sp[-1][1].x1)
            y = R.PLATEAU_Y
            if lift + 0.6 <= t < self.launch[3]:          # bounces along with his raft on his head
                y -= abs(math.sin((t - lift) * 5.5)) * 26 * (1 - smoothstep(seg(t, self.launch[3] - 1.2,
                                                                                    self.launch[3] - 0.5)))
        self.place(m, x, t, dt, y=y)

    def glo_pos(self, t):
        hover = RY - 150
        keys = [(0.0, MAST_X + 60, R.PLATEAU_Y - 200), (self.t_sail[0] - 4.0, MAST_X + 60, R.PLATEAU_Y - 200),
                (self.t_sail[0] - 0.3, SPOT[0] + 4, hover)]
        for i in range(6):
            keys += [(self.t_sail[i] - 0.3, SPOT[i] + 4, hover), (self.t_sail[i] + 3.3, SPOT[i] + 4, hover)]
        x, y = path(keys, t)[:2]
        if t >= self.c0 - 3.5:
            lift, arrive, top = self.carry_path(4)
            x = self._carry_x(4, t, SPOT[5] + 4)
            y = path([(self.c0 - 3.5, y, 0), (lift, RY - 60, 0), (lift + 1.0, R.PLATEAU_Y - 140, 0),
                      (self.launch[4] - 0.6, R.PLATEAU_Y - 140, 0), (self.launch[4] + 1.0, R.PLATEAU_Y - 260, 0)], t)[0]
        return x, y

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        x, y = self.glo_pos(t)
        m.lamp = 1.1 + 1.3 * max(self.magic(i, t) for i in range(6))
        self.place(m, x, t, dt, y=y)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        a, b = self.slip_dug
        r0, r1 = self.rails
        keys = [(0.0, SPOT[0] - 600, 0), (a - 0.5, SLIP[0] - 30, 0), (b, SLIP[0] + 20, 0),
                (r0, SLIP[0] - 120, 0), (r0 + 1.6, SLIP[0] - 120, 0), (r0 + 3.0, SLIP[0] - 10, 0),
                (r1, SLIP[0] - 10, 0), (r1 + 2.0, SLIP[0] - 160, 0)]
        x = path(keys, t)[0]
        m.dig = 0.5 + 0.5 * math.sin(t * 16) if a <= t < b else 0.0
        if t >= self.c0 - 3.5:
            x = self._carry_x(5, t, SLIP[0] - 160)
        m.punch = 0.8 if self.c0 - 0.6 <= t < self.launch[5] else 0.0
        self.place(m, x, t, dt, y=R.PLATEAU_Y)

    def slip_u(self, t):
        return seg(t, *self.slip_dug)

    # ----- particles + sounds -----

    def _particles(self, t):
        P = self.s.particles
        dg = self.m("digger")
        if dg is not None and getattr(dg, "dig", 0) > 0.6 and P.rng.uniform() < 0.5:
            P.burst(dg.x + 60, dg.y - 10, 2, np.array([96, 70, 52]), 300, 0.8, 5, g=1300, spread=0.7,
                    direction=-math.pi * 0.35)
        tw = self.m("teeth")
        if tw is not None and getattr(tw, "saw_run", 0) > 0.5 and P.rng.uniform() < 0.8:
            cx, cy = tw.saw_center(-1, t, 0.0)
            P.burst(cx, cy, 2, np.array([214, 186, 140]), 260, 0.6, 3.5, g=900, spread=0.6, direction=math.pi * 0.7)

    def _sounds(self, t):
        if self.crossed(0.4):
            self.fx(t, "gurgle", self.dur, 0.04, 8200, R.surface(8200))
        if self.crossed(1.2):
            self.chat(t, "digger", "hey", icon="raft")
        if self.crossed(2.4):
            self.chorus(t, ["wheels", "teeth", "tentacles"], "yay", gap=0.25)
        for i, (pick, go, arrive, drop) in enumerate(self.w_trips):
            if self.crossed(arrive + 0.6):
                for q in range(4):
                    self.hit(t + q * 0.07, "clack", self.s.note(q + i % 3, -1), 0.1, SPOT[i], RY)
        for i in range(6):
            a = self.t_cut[i]
            if self.crossed(a + 0.6):
                self.fx(t, "saw", 1.8, 0.16, SPOT[i] + L / 2, RY)
            if self.crossed(a + 2.45):
                for q in range(4):
                    self.hit(t + q * 0.06, "clack", self.s.note(4 - q, 0), 0.08, SPOT[i] + L / 2 + 20, RY + 10)
            if i in (0, 5) and self.crossed(a + 3.0):
                self.chat(t, "teeth", "hehe" if i == 0 else "yay")
            b = self.t_tie[i]
            for q in range(2):
                if self.crossed(b + 0.3 + 2.0 * q):
                    self.fx(t, "rustle", 1.7, 0.08, SPOT[i], RY)
                if self.crossed(b + 2.2 + 2.0 * q):
                    self.hit(t, "pluck", self.s.note(q + 2, 0), 0.12, SPOT[i], RY)
            if i == 2 and self.crossed(b + 4.5):
                self.chat(t, "tentacles", "mm")
            p = self.t_press[i]
            for q, bb in enumerate((p + 0.15, p + 1.0, p + 1.85)):
                if self.crossed(bb):
                    self.hit(t, "boing", 62 + q * 2 + (i % 2) * 2, 0.16, SPOT[i], RY)
            if i == 1 and self.crossed(p + 2.2):
                self.chat(t, "springs", "wee")
            sl = self.t_sail[i]
            if self.crossed(sl + 1.4):
                self.hit(t, "clack", 55, 0.12, SPOT[i], RY - 20)
            if self.crossed(sl + 2.0):
                self.hit(t, "chime", self.s.note(i + 2, 0), 0.14, SPOT[i], RY - 150)
                self.hit(t + 0.12, "chime", self.s.note(i + 4, 0), 0.1, SPOT[i], RY - 150)
            if self.crossed(sl + 3.1):
                kind = LANE_KIND[i]
                self.chat(t, kind, "aww" if i % 2 == 0 else "yay", icon="heart" if i % 2 == 0 else "star")
        a, b = self.slip_dug
        for k in range(int((b - a) / 1.3)):
            if self.crossed(a + 0.4 + k * 1.3):
                self.fx(t, "slide", 0.5, 0.06, SLIP[0], R.PLATEAU_Y)
        if self.crossed(b + 0.5):
            self.chat(t, "digger", "huff")
        if self.crossed(self.rails[0] + 3.0) or self.crossed(self.rails[1]):
            self.hit(t, "thud", 52, 0.14, SLIP[0], R.PLATEAU_Y)
        if self.crossed(self.built - 0.5):
            self.chorus(t, ["springs", "digger", "wheels", "tentacles", "teeth", "lantern"], "yay", gap=0.18,
                        icon="star")
        if self.crossed(self.c0 - 1.0):
            self.chat(t, "wheels", "hey", icon="raft")
        for i in range(6):
            if self.crossed(self.launch[i] + 0.1):
                self.fx(t, "slide", 0.6, 0.08, SLIP[0], R.PLATEAU_Y)
            if self.crossed(self.launch[i] + 0.7):
                self.fx(t, "splash", 0.7, 0.18, SLIP[1], R.surface(SLIP[1]))
                self.s.particles.burst(SLIP[1] + 30, R.surface(SLIP[1]), 12, R.FOAM, 260, 0.7, 5, g=1400, up=240,
                                       spread=1.3)
                self.chat(t + 0.3, self.owner(i), "wee" if i % 2 else "yay")
            if self.crossed(self.launch[i] + 4.3):
                self.hit(t, "clack", self.s.note(i, -1), 0.08, R.START_BOOM, R.surface(R.START_BOOM))

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)

        def rafts(c, j):
            for i in range(6):
                st = self.raft_pos(i, t)
                if st[0] == "water" and abs(st[4] - j) < 0.5 and st[5] > 0.6:
                    self._raft_water(c, i, st, t)

        def between(c):
            gl = self.m("lantern")
            if gl is not None:
                self.glo_light(c, gl.x, gl.y - 100, 0.8)
        self.brook(c, t, rafts=rafts, boom=0.0, finish=False, between=between)
        self._site_back(c, t)
        self.draw_monsters(c, t, kinds=["wheels", "teeth", "tentacles", "digger", "lantern"] +
                           ([] if self._springs_on_deck(t) else ["springs"]))
        self._rafts_on_bank(c, t)
        if self._springs_on_deck(t):
            self.draw_monsters(c, t, kinds=["springs"])
        self._held(c, t)

    def _springs_on_deck(self, t):
        return self.sp[0][0] + self.sp[0][1].dur * 0.5 < t < self.sp[-1][0] + self.sp[-1][1].dur * 0.5

    def _raft_water(self, c, i, st, t):
        _, x, y, th, lane, tau = st
        dx, dy, sc = R.lane_off(lane)
        wy = R.surface(x) + R.wave(x, t, R.stretch_at(x)[6], i)
        R.draw_raft(c, x + dx, y + dy, th, L, COLS[LANE_KIND[i]], sc=sc, t=t, water=wy + dy if tau > 0.6 else None,
                    wake=40.0 if tau < 3 else 0.0, shade=1.0 - 0.04 * lane)

    def _site_back(self, c, t):
        """Behind the Keepers: the sign, the log pile, the masts leaning on their stand, the slipway."""
        s = self.s
        from families.foundry.keepers.common import wood_sign
        wood_sign(c, 6080.0, R.PLATEAU_Y, "RAFTS", 40, 1.0, s.glow_draw)
        # the log pile: sets of four still waiting
        left = sum(1 for i in range(6) if self.logs_at(i, t) is None)
        for k in range(left * 4):                          # stacked two wide, like bricks
            row, col = divmod(k, 2)
            x = PILE_X - 60 + col * 118 + (row % 2) * 40
            y = R.PLATEAU_Y - 8 - row * 15
            c.polygon([(x - 55, y - 7), (x + 55, y - 7), (x + 55, y + 7), (x - 55, y + 7)], R.LOG * (0.8 + 0.04 * (k % 3)))
            c.line(x - 55, y - 3, x + 55, y - 3, R.LOG * 0.95, 3)
            c.circle(x + 55, y, 7, R.LOG_END)
        # the masts with their pale leaves lean on a little rack until Glo takes them
        rect(c, MAST_X - 70, R.PLATEAU_Y - 70, MAST_X + 70, R.PLATEAU_Y - 60, TRUNK)
        if t < self.t_sail[0] - 3.4:
            for k in range(6):
                draw_mast_free(c, MAST_X - 50 + k * 18, R.PLATEAU_Y, -0.12, COLS[LANE_KIND[k]], 0.0, t)
        # the slipway: a notch dug in the bank, two rails down into the pool
        u = self.slip_u(t)
        if u > 0:
            x0, x1 = SLIP
            y0, y1 = R.PLATEAU_Y + 30, R.surface(x1) + 6
            c.polygon([(x0 - 30, y0 - 6), (x0 + (x1 - x0) * u + 20, lerp(y0, y1, u) - 6),
                       (x0 + (x1 - x0) * u + 20, y0 + 30), (x0 - 30, y0 + 30)], np.array([60, 44, 34]) * 0.9)
            heap = 30 * u
            c.polygon(ellipse(x0 - 90, R.PLATEAU_Y + 4, 50 * u + 10, heap + 4, 16, math.pi, 2 * math.pi),
                      np.array([84, 62, 46]))
        for q, r in enumerate((self.rails[0] + 3.0, self.rails[1])):
            if t >= r:
                dy = 10 * q
                c.line(SLIP[0] - 10, R.PLATEAU_Y + 22 + dy, SLIP[1] + 20, R.surface(SLIP[1]) + 8 + dy, TRUNK * 1.1, 7)

    def _rafts_on_bank(self, c, t):
        for i in range(6):
            st = self.raft_pos(i, t)
            lg = self.logs_at(i, t)
            if st[0] != "built" or lg is None or lg[0] == "carry":
                continue
            # the stop board every raft's logs are pushed against, and the chalk line where they are cut
            sx = SPOT[i] - L / 2 - 8
            rect(c, sx - 6, RY - 40, sx, RY + 12, TRUNK * 1.25)
            cut = self.cut_u(i, t)
            if cut < 1:
                c.line(SPOT[i] + L / 2 + 1, RY - 26, SPOT[i] + L / 2 + 13, RY + 8 - 22, np.array([236, 232, 220]), 2)
            down = lg[1]
            mast = self.mast_u(i, t)
            R.draw_raft(c, SPOT[i], st[2] - 14 * (1 - down), 0.0, L, COLS[LANE_KIND[i]], t=t, logs=4, cut=cut,
                        ties=self.ties(i, t), mast=1.0 if mast >= 1 else 0.0, dye=self.dye(i, t), ragged=ragged(i))
            if 0 < mast < 1:                               # Glo lowers the mast into its hole
                gl = self.m("lantern")
                fx, fy = R.mast_foot(SPOT[i], RY, 0.0)
                hx, hy = (gl.x - 26, gl.y - 6) if gl is not None else (fx, fy - 80)
                draw_mast_free(c, lerp(hx, fx, mast), lerp(hy, fy, mast), 0.0, COLS[LANE_KIND[i]], 0.0, t)
            g = self.magic(i, t)
            if g > 0:
                self._magic(c, i, t, g)
            if cut >= 1:                                   # the offcuts lie on the ground in front
                for k, ln in enumerate(ragged(i)):
                    draw_offcut(c, SPOT[i] + L / 2 + 20 + 8 * k, RY + 26 + 3 * k, ln, k)
            elif cut > 0.9:
                pass
        # Glo carries the bundle of masts until the last is in
        gl = self.m("lantern")
        if gl is not None and self.t_sail[0] - 3.4 <= t < self.t_sail[5] + 0.5:
            n = sum(1 for i in range(6) if self.mast_u(i, t) <= 0)
            for k in range(n):                           # held in his short tendrils, hanging below the lamp
                draw_mast_free(c, gl.x - 26 + k * 5, gl.y - 6 + 2 * k, -0.06, COLS[LANE_KIND[5 - k]], 0.0, t)

    def _magic(self, c, i, t, g):
        """Glo's light flares over raft i's leaf: a soft beam, sparkles falling to it, the leaf glows into colour."""
        s = self.s
        gl = self.m("lantern")
        lx, ly = gl.x, gl.y - 178 * gl.k
        x, y = R.raft_sail_center(SPOT[i], RY, 0.0)
        col = COLS[LANE_KIND[i]]
        p = self.dye(i, t)
        s.glow_draw(lambda gg: gg.polygon([(lx - 26, ly + 30), (lx + 26, ly + 30), (x + 44, y + 30), (x - 34, y + 30)],
                                          LAMP * 0.10 * g))
        s.glow_draw(lambda gg: gg.circle(x, y, 50 + 30 * g, lerp(LAMP, col, p) * 0.5 * g))
        for q in range(9):
            u = (t * 0.9 + q / 9.0) % 1.0
            sx = lerp(lx, x, u) + 16 * math.sin(7.0 * u + q * 2.1) * (1 - u)
            sy = lerp(ly + 30, y, u)
            tw = 0.6 + 0.4 * math.sin(t * 11 + q * 1.7)
            sc = lerp(LAMP, col, u) * g * tw
            c.circle(sx, sy, 3.5, np.minimum(255, sc * 1.1))
            s.glow_draw(lambda gg, sx=sx, sy=sy, sc=sc: gg.circle(sx, sy, 12, sc * 0.5))

    def _held(self, c, t):
        """Rafts carried overhead, and Wheels' load of logs."""
        for i in range(6):
            st = self.raft_pos(i, t)
            if st[0] == "held":
                R.draw_raft(c, st[1], st[2], 0.0, L, COLS[LANE_KIND[i]], t=t)
            elif st[0] == "water" and st[5] <= 0.6:          # still on the slipway rails
                R.draw_raft(c, st[1], st[2], st[3], L, COLS[LANE_KIND[i]], t=t)
        for i in range(6):
            lg = self.logs_at(i, t)
            if lg is not None and lg[0] == "carry":
                x, y = lg[1], lg[2]
                for k in range(4):
                    c.polygon([(x - 64, y - 12 - k * 12), (x + 64, y - 12 - k * 12), (x + 64, y - k * 12),
                               (x - 64, y - k * 12)], R.LOG * (0.9 + 0.03 * k))
                    c.circle(x + 64, y - 6 - k * 12, 6, R.LOG_END)


def SPOT_W(arrive, act):
    """Where Wheels stops to set raft i's logs down (just behind its spot)."""
    for i, (p, g, a, d) in enumerate(act.w_trips):
        if a == arrive:
            return SPOT[i] - 10
    return SPOT[0]


# ====================================================================== little friends

LEAF_ORANGE = np.array([214, 120, 46], np.float64)
DUCK = np.array([150, 116, 82], np.float64)
DUCKLING = np.array([226, 196, 92], np.float64)


def draw_leaf_boat(c, x, y, th, t, bug=True, k=1.8):
    """A big autumn leaf floating flat, a ladybird riding on it."""
    from families.foundry.keepers.common import Xform
    cv = Xform(Xform(c, 0, 0, 0.0, k, x, y), 0, 0, th, 1.0, x, y)
    cv.polygon(ellipse(x, y - 3, 30, 9, 20), LEAF_ORANGE * 0.85)
    cv.polygon(ellipse(x - 2, y - 5, 24, 6, 16), LEAF_ORANGE)
    cv.line(x - 30, y - 4, x + 32, y - 4, LEAF_ORANGE * 0.6, 2)
    cv.line(x + 30, y - 4, x + 40, y - 9, LEAF_ORANGE * 0.6, 2)          # the stalk
    if bug:
        bx, by = x + 4, y - 12
        cv.polygon(ellipse(bx, by, 8, 6, 14, math.pi, 2 * math.pi), np.array([206, 40, 36]))
        cv.circle(bx - 9, by - 1, 3.5, np.array([20, 20, 22]))
        cv.circle(bx + 2, by - 3, 1.5, np.array([20, 20, 22]))
        cv.circle(bx - 3, by - 2, 1.4, np.array([20, 20, 22]))


def draw_duck(c, x, y, size, face, t, col=DUCK, beak=np.array([236, 160, 52]), bob=0.0):
    """A duck on the water, (x, y) = the waterline under its middle."""
    y = y - bob
    c.polygon(ellipse(x, y - 9 * size, 22 * size, 11 * size, 20, math.pi, 2 * math.pi), col)
    c.polygon([(x - 22 * size * face, y - 9 * size), (x - 30 * size * face, y - 17 * size),
               (x - 16 * size * face, y - 14 * size)], col * 0.9)                      # the tail
    hx, hy = x + 16 * size * face, y - 26 * size
    c.circle(hx, hy, 9 * size, col * 1.05)
    c.polygon([(hx + 7 * size * face, hy - 1 * size), (hx + 17 * size * face, hy + 2 * size),
               (hx + 7 * size * face, hy + 4 * size)], beak)
    c.circle(hx + 3 * size * face, hy - 3 * size, 1.8 * size, np.array([20, 20, 24]))
    c.line(x - 18 * size, y + 1, x + 18 * size, y + 1, R.WATER * 1.5, 2)


def draw_frog(c, x, y, s, t):
    c.polygon(ellipse(x, y - 8 * s, 15 * s, 10 * s, 18, math.pi, 2 * math.pi), np.array([84, 150, 70]))
    for e in (-1, 1):
        c.circle(x + e * 7 * s, y - 16 * s, 4.5 * s, np.array([96, 168, 80]))
        c.circle(x + e * 7 * s, y - 16 * s, 2 * s, np.array([20, 20, 24]))
    c.line(x - 15 * s, y - 2, x + 15 * s, y - 2, np.array([60, 120, 56]), 3)


# ====================================================================== LEAF (the opening)

LEAF_WATCH = {"digger": 9760.0, "lantern": 9880.0, "teeth": 9990.0, "tentacles": 10110.0, "springs": 10240.0,
              "wheels": 10380.0}


class LeafAct(RaftAct):
    """By the brook on an autumn night: a leaf with a ladybird on it floats down the riffle, over the little falls
    (where it is held in the hole for a moment) and out into the pool. Digs has an idea: rafts!"""
    name = "leaf"
    names = (2.0, 8.5)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.t_leaf = 5.0
        self.leaf = R.Run(R.Trait(0.4, 1.0, 0.25, 50.0), 1, t_max=40.0, x0=9020.0)
        self.over = next(te for (te, k, x, y, v) in self.leaf.events if k == "drop") + self.t_leaf
        self.splash = next(te for (te, k, x, y, v) in self.leaf.events if k == "splash") + self.t_leaf
        # when it is out of the hole and drifting past the watchers
        rec = self.leaf.rec
        self.out = self.t_leaf + float(np.argmax(rec[:, 0] > R.FALLS[0] + R.HOLE)) / R.REC_HZ
        self.idea = self.out + 4.5
        self.go = self.idea + 4.0
        self.dur = self.go + 8.0

    def aside_moods(self, t):
        if self.t_leaf < t < self.idea + 1:
            return []
        return ["hehe", "ooh", "mm", "aww"]

    def leaf_at(self, t):
        tau = max(0.0, t - self.t_leaf)
        x, y, th, vx, air = self.leaf.at(tau)
        return x, y, th, vx

    def target(self, t):
        if t < self.t_leaf - 0.5:
            return 9750.0, R.surface(9750.0) - 290, 0.95
        if t < self.out + 2.0:
            x = self.leaf_at(t)[0]
            x = max(9150.0, x + 60)
            return x, R.surface(x) - 250, 1.5
        if t < self.go:
            return 9950.0, R.surface(9950.0) - 280, 1.15
        u = smoothstep(seg(t, self.go, self.dur))
        return lerp(9950.0, 9500.0, u), R.surface(9600.0) - 330, lerp(1.15, 0.95, u)

    def update(self, t, dt):
        self.reach = {}
        for q, (kind, x1) in enumerate(LEAF_WATCH.items()):
            m = self.m(kind)
            if m is None:
                continue
            x0 = x1 + 900 + 120 * q
            keys = [(0.0, x0, 0), (4.5 + 0.3 * q, x1, 0)]
            if kind == "wheels":                          # rolls along after the leaf, then back
                lx = self.leaf_at(t)[0]
                keys = [(0.0, x0, 0), (4.5, x1, 0), (self.out, x1, 0), (self.out + 3.0, 10650.0, 0),
                        (self.idea - 0.5, 10650.0, 0), (self.idea + 2.5, x1, 0)]
            keys += [(self.go + 0.4 * q, keys[-1][1], 0), (self.go + 7.5, 9640.0 + 60 * q, 0)]
            x = path(keys, t)[0]
            y = far_bank_y(x)
            dy = 0.0
            if kind == "springs":                         # bounces everywhere: in, and off up the rock step
                t1 = 4.5 + 0.3 * q
                if t < self.go:
                    x, lift, sq = hops(x0, x1, 0.0, t1, t, apex=40, step=150)
                elif t < self.go + 3.5:
                    x, lift, sq = hops(x1, 9640.0, self.go, self.go + 3.5, t, apex=50, step=150)
                else:                                     # a breath, then up the step
                    jp = Jump(9640.0, far_bank_y(9640.0), 9440.0, far_bank_y(9440.0), apex=60)
                    x, yy = jp.at(t - self.go - 3.8)
                    lift, sq = 0.0, 0.0
                y = far_bank_y(x) if t < self.go + 3.5 else yy
                dy, m.spring = -lift, sq
            if kind == "lantern":
                y = far_bank_y(x) - 170 - 10 * math.sin(t * 1.2)
                bump = math.exp(-((t - self.idea - 0.3) / 0.6) ** 2)
                m.lamp = 1.0 + 0.6 * bump
            if kind == "digger":
                dy = -18 * math.exp(-((t - self.idea - 0.3) / 0.3) ** 2)
            self.place(m, x, t, dt, y=y, dy=dy, k=0.9)
        self.leaves(0.05)
        self._sounds(t)

    def _sounds(self, t):
        if self.crossed(0.2):
            self.fx(t, "gurgle", self.dur, 0.06, 9550.0, R.surface(9550.0))
        if self.crossed(2.0):
            self.chat(t, "wheels", "hey")
        if self.crossed(self.t_leaf + 0.8):
            self.chat(t, "wheels", "ooh", icon="!")
        if self.crossed(self.over - 0.6):
            self.chat(t, "teeth", "uhoh")
        if self.crossed(self.splash):
            x, y, _, _ = self.leaf_at(t)
            self.fx(t, "splash", 0.6, 0.16, x, y)
            self.s.particles.burst(x + R.LANE_DX, y - R.LANE_DY, 8, R.FOAM, 200, 0.6, 4, g=1400, up=180, spread=1.4)
        if self.crossed(self.splash + 0.6):
            self.chorus(t, ["springs", "lantern"], "uhoh", gap=0.3)
        if self.crossed(self.out + 0.3):
            self.chat(t, "wheels", "yay", icon="heart")
        if self.crossed(self.out + 1.5):
            self.chorus(t, ["teeth", "tentacles", "springs"], "hehe", gap=0.25)
        if self.crossed(self.idea - 1.8):
            self.chat(t, "digger", "hm")
        if self.crossed(self.idea):
            self.hit(t, "bloop", 69, 0.3, LEAF_WATCH["digger"], far_bank_y(LEAF_WATCH["digger"]) - 300)
            self.chat(t + 0.15, "digger", "idea", icon="raft")
            for k, n in enumerate((67, 72, 76, 79)):
                self.hit(t + 0.3 + k * 0.1, "chime", n, 0.22, LEAF_WATCH["digger"], far_bank_y(9760.0) - 300)
        if self.crossed(self.idea + 1.6):
            self.chorus(t, ["springs", "wheels", "tentacles", "lantern", "teeth"], "yay", gap=0.2, icon="star")
        if self.crossed(self.go + 0.6):
            self.chat(t, "springs", "wee")

    def draw(self, c, t):
        self.backdrop(c, t)

        def leaf(c, j):
            if j == 1 and t >= self.t_leaf - 3:
                x, y, th, vx = self.leaf_at(t)
                if t < self.t_leaf:                        # drifts in from upstream
                    x -= (self.t_leaf - t) * 60
                dx, dy, sc = R.lane_off(1)
                wy = R.surface(x) + R.wave(x, t, R.stretch_at(x)[6], 1) + dy
                if y < wy + 30:                            # the water hides the underside of the leaf
                    R.hide_under(c, [(x + dx - 90, wy + 2), (x + dx + 90, wy + 2), (x + dx + 90, wy + 60),
                                     (x + dx - 90, wy + 60)], lambda: draw_leaf_boat(c, x + dx, y + dy, th, t))
                    c.line(x + dx - 60, wy + 2, x + dx + 60, wy + 2, R.WATER * 1.4, 2)
                else:
                    draw_leaf_boat(c, x + dx, y + dy, th, t)

        def far(c):
            self.draw_monsters(c, t, kinds=[k for k in LEAF_WATCH if k != "lantern"])

        self.brook(c, t, rafts=leaf, finish=False, far=far,
                   between=lambda c: self.glo_light(c, self.m("lantern").x, self.m("lantern").y - 100, 0.8))
        self.draw_monsters(c, t, kinds=["lantern"])


# ====================================================================== CHEER (continues the race, no cut)

class RaftCheerAct(RaftAct):
    """The rafts bump against the boom in the finish pool; the winner's Keeper dances; a duck and her ducklings come
    to look; everyone waves; slow pull back over the brook."""
    name = "raft_cheer"
    joins_prev = True
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.race_act = next(a for a in scene.acts if a.name == "raft_race")
        self.dur = 22.0
        self.T = dict(ducks=1.0, wave=12.0, pull=15.0)

    def aside_moods(self, t):
        return ["hehe", "aww", "yay", "ooh"]

    def rt(self, t):
        """Race-act time for cheer time t."""
        return self.race_act.dur + t

    def duck_xy(self, k, t):
        """Mother (k 0) and three ducklings: in from downstream, hop over the boom, paddle among the rafts."""
        x0 = 14300.0 + 60 * k
        stop = R.END_BOOM - 160 - 70 * k
        a = self.T["ducks"] + 0.5 * k
        hop_t = a + (x0 - (R.END_BOOM + 40)) / 90.0
        lane = 4.6 - 0.25 * k
        if t < hop_t:
            x = x0 - (t - a) * 90.0 if t > a else x0
            return x, 0.0, lane
        if t < hop_t + 0.5:                              # over the boom
            u = (t - hop_t) / 0.5
            return lerp(R.END_BOOM + 40, R.END_BOOM - 40, u), 4 * 28 * u * (1 - u), lane
        u = smootherstep(seg(t, hop_t + 0.5, hop_t + 4.0))
        x = lerp(R.END_BOOM - 40, stop, u) + 10 * math.sin(t * 0.8 + k)
        return x, 0.0, lane

    def target(self, t):
        x0 = R.FINISH_X + 300
        x1 = R.END_BOOM - 120
        a = smootherstep(seg(t, 0.0, 3.0))
        u = smootherstep(seg(t, self.T["pull"], self.dur))
        x = lerp(lerp(x0, x1, a), 12300.0, u)
        y = lerp(lerp(R.surface(x0) - 260, R.surface(x1) - 200, a), R.surface(12300.0) - 420, u)
        return x, y, lerp(lerp(1.05, 1.45, a), 0.62, u)

    def update(self, t, dt):
        ra = self.race_act
        win = LANE_KIND[ra.race.order[0]]
        self.reach = {}
        for kind, x in FAR_WATCH.items():
            m = self.m(kind)
            if m is None:
                continue
            dy = 0.0
            if kind == win:                              # the winner hops for joy
                ph = t % 0.7
                dy = -4 * 40 * (ph / 0.7) * (1 - ph / 0.7) if t < self.T["wave"] else 0.0
            if t > self.T["wave"]:
                m.punch = 0.6 + 0.4 * math.sin((t - self.T["wave"]) * 6)
            self.place(m, x, t, dt, y=far_bank_y(x), dy=dy, k=0.9)
        m = self.m("springs")
        if m is not None:
            x0 = ra.sp_hops[-1][1].x1 if ra.sp_hops else SPRINGS_START
            x, lift, sq = hops(x0, 12400.0, 1.0, 5.0, t, apex=50, step=160)
            m.spring = sq
            if t > self.T["wave"]:
                m.punch = 0.6 + 0.4 * math.sin((t - self.T["wave"]) * 6 + 1)
            self.place(m, x, t, dt, y=far_bank_y(x), dy=-lift, k=0.9)
        m = self.m("lantern")
        if m is not None:
            x, v = ra.glo
            want = 13560.0
            a = 6.0 * (want - x) - 4.5 * v
            v = max(-420.0, min(420.0, v + a * dt))
            x += v * dt
            ra.glo = [x, v]
            m.lamp = 1.25
            self.place(m, x, t, dt, y=smooth_surface(x) - 300 + 12 * math.sin((self.t0 + t) * 1.4))
        self.leaves(0.03)
        self._sounds(t)

    def _sounds(self, t):
        ra = self.race_act
        win = LANE_KIND[ra.race.order[0]]
        if self.crossed(0.5):
            self.chat(t, win, "yay", icon="star")
        for k in range(4):
            a = self.T["ducks"] + 0.5 * k
            hop_t = a + (14300.0 + 60 * k - (R.END_BOOM + 40)) / 90.0
            if self.crossed(hop_t):
                self.hit(t, "bloop", 76 + 3 * (k > 0), 0.1, R.END_BOOM, R.surface(R.END_BOOM))
            if self.crossed(hop_t + 0.55):
                self.fx(t, "splash", 0.3, 0.05, R.END_BOOM - 40, R.surface(R.END_BOOM))
        if self.crossed(self.T["ducks"] + 3.0):
            self.chat(t, "digger", "ooh", icon="heart")
        if self.crossed(self.T["ducks"] + 9.0):
            self.chorus(t, ["springs", "lantern"], "aww", gap=0.3, icon="heart")
        if self.crossed(self.T["wave"]):
            self.chorus(t, ["wheels", "tentacles", "teeth", "digger", "springs", "lantern"], "hey", gap=0.2,
                        icon="heart")

    def draw(self, c, t):
        ra = self.race_act
        s = self.s
        rt = self.rt(t)
        self.backdrop(c, t)

        def rafts(c, j):
            x, y, th, vx = ra.raft(j, rt)
            if s.visible(x - 200, x + 200):
                self.raft_in_water(c, j, x, y, th, vx, self.t0 + t, ra.race.traits[j].length)
            for k in range(4):
                dx_, hop, lane = self.duck_xy(k, t)
                if int(round(lane)) == j:
                    ddx, ddy, sc = R.lane_off(lane)
                    size = 1.5 if k == 0 else 0.85
                    draw_duck(c, dx_ + ddx, R.surface(dx_) + ddy - hop, size * sc, -1, t,
                              col=DUCK if k == 0 else DUCKLING, bob=1.5 * math.sin(t * 3 + k))

        def far(c):
            self.draw_monsters(c, t, kinds=list(FAR_WATCH) + ["springs"])

        def between(c):
            gl = self.m("lantern")
            if gl is not None:
                self.glo_light(c, gl.x, gl.y - 100)
        self.brook(c, t, rafts=rafts, boom=1.0, far=far, between=between)
        self.draw_monsters(c, t, kinds=["lantern"])
