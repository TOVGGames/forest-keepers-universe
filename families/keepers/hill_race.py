"""Forest Keepers episode 5, acts 3-5 (docs/engines/forest_keepers_first_snow.md).

HILL   Digs packs the three lanes, Glo lights the first lantern and a spark runs up the hill from lantern to
       lantern, lighting the whole run; the Keepers pull their sleds up.
RACE   At the top: on board, a countdown (3, 2, 1 in their bubbles), and three sleds side by side down the long
       hill with real sled physics (sled.Ride), into the soft snowbank at the bottom.
COZY   Back at the treehouse in the falling snow, the sleds parked, everyone home.
The race is downhill only (owner rule for chase races, FE0015 review).
"""
import math

import numpy as np

from families.foundry.keepers.common import Jump, LEAF_FAR, PLANK, ellipse, lerp, rect, seg, smoothstep, smootherstep
from families.foundry.keepers.halloween import hops, path
from families.foundry.tree_monsters import LAMP

from . import props as PR
from . import sled as SL
from . import snow as SN
from .animal_houses import BIRD_COLS, POST_TOP, POSTS, _ease, bez, flying_bird
from .first_snow import HOME, KEEPERS, SLEDS, G, SnowAct, cam
from .sled_shop import PARK

RIDERS = {kind: (k, q) for k, (pair, _) in enumerate(SLEDS) for q, kind in enumerate(pair)}   # kind: (sled, seat)
SEAT_X = (-SL.L / 2 + 150, SL.L / 2 - 120)          # front / back seat along the sled (nose = -L/2)
HOLD_ON = {"lantern": -40.0}                        # Glo floats just above her seat


def lane_y(x, k):
    return SL.hill_y(x) + SL.LANES[k]


def hill_trees(x0, x1, step=900.0):
    """Snowy trees along the far side of the run (deterministic)."""
    rs = np.random.default_rng(77)
    out = []
    x = SL.HILL_X0 + 300
    while x < SL.TOP_END + 1500:
        jx = x + rs.uniform(-250, 250)
        h = rs.uniform(560, 780)
        if x0 - 400 < jx < x1 + 400:
            out.append((jx, h, int(1000 + x // step)))
        x += step
    return out


class HillMixin:
    """Drawing the hill world (acts HILL and RACE)."""

    def draw_hill_world(self, c, t, lit, packed=None):
        s = self.s
        x0, x1 = s.view()[:2]
        d = self.depth(t)
        # far forest band along the top edge of the run, then trees, then the snow slope
        if x1 > SL.HILL_X0 - 500:
            xs = np.arange(max(x0 - 300, SL.HILL_X0 - 800), x1 + 300, 140.0)
            for x in xs:
                yb = lane_y(x, 2) - 40
                r = 70 + 26 * math.sin(x * 0.013)
                c.circle(x, yb - r * 0.6, r, LEAF_FAR)
                if r > 50 and s.zoom > 0.12:
                    SN.cap_circle(c, x, yb - r * 0.6, r, d * 0.35, SN.SNOW_SHADE * 0.62)
            for x, h, seed in hill_trees(x0, x1):
                SN.snowy_tree(c, x, lane_y(x, 2) - 30, h, seed, d)
        SL.draw_hill(c, s, t, lit=lit, groove=1.0, packed=packed)


# ====================================================================== HILL

class HillAct(SnowAct, HillMixin):
    """The lanes, the lanterns, up the hill."""
    name = "hill"
    names = (-2.0, -1.0)
    depth0, depth1 = 31.0, 32.0
    fall0, fall1 = 0.5, 0.45
    cam_omega = 1.4

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.dur = 48.0
        self.T = dict(pack=1.0, glo=3.0, light=8.0, spark=8.6, wide=17.5, back=25.0, pull=29.0)
        self.lx = SL.lantern_xs()
        self.spark_dt = 0.36
        self.start = {"lantern": (8040.0, G - 60), "tentacles": (8420.0, G), "teeth": (8980.0, G),
                      "springs": (8560.0, G), "wheels": (9500.0, G), "digger": (9700.0, G)}
        self.stats = {"lanterns": len(self.lx)}
        gaps = np.diff(self.lx)
        self.stats["lanterns_even"] = bool(np.ptp(gaps) < 0.5)
        self.pull_v = 330.0

    def aside_moods(self, t):
        return ["ooh", "hehe", "aww", "q"]

    def lit_t(self, i):
        return self.T["light"] if i == 0 else self.T["spark"] + i * self.spark_dt

    def lit(self, x):
        i = int(round((x - self.lx[0]) / SL.LANTERN_EVERY))
        return smoothstep(seg(self._t, self.lit_t(i), self.lit_t(i) + 0.35))

    def spark(self, t):
        """The little spark that runs up the hill from lantern to lantern -> (x, y) or None."""
        u = (t - self.T["spark"]) / self.spark_dt
        if u < 0 or u >= len(self.lx) - 1:
            return None
        i = int(u)
        f = u - i
        a = (self.lx[i] + 30, lane_y(self.lx[i], 2) - 34 - 212)
        b = (self.lx[i + 1] + 30, lane_y(self.lx[i + 1], 2) - 34 - 212)
        return bez(a, ((a[0] + b[0]) / 2, min(a[1], b[1]) - 260), b, smoothstep(f))

    def packed(self, t):
        return 9640.0 + 2160.0 * smoothstep(seg(t, self.T["pack"], self.T["pack"] + 12.0))

    def sled_x(self, k, t):
        """Sled k (nose right) being pulled up its lane."""
        t0 = self.T["pull"] + 2.0 * (2 - k)            # the front sled goes first, so the teams spread out
        return PARK[k] + self.pull_v * max(0.0, t - t0) * smoothstep(seg(t, t0, t0 + 1.0)) ** 0.5

    def sled_y(self, k, t):
        x = self.sled_x(k, t)
        into = smoothstep(seg(x, PARK[k], PARK[k] + 900))           # steers over into its lane
        return SL.hill_y(x) + SL.LANES[k] * into

    def lane_sc(self, k, t):
        """Scale of sled k and its team as it moves over into its lane."""
        if k == 0:
            return 1.0
        into = (self.sled_y(k, t) - SL.hill_y(self.sled_x(k, t))) / SL.LANES[k]
        return lerp(1.0, SL.LANE_SCALE[k], into)

    def target(self, t):
        h, T = self.s.h, self.T
        lead = self.sled_x(0, t)
        wide_y = -1200.0
        keys = [(0.0, *cam(h, 8900, 0.66)), (T["glo"], *cam(h, 9600, 0.66)), (T["light"], *cam(h, 10300, 0.78)),
                (T["spark"] + 1.0, *cam(h, 11500, 0.5)), (T["wide"], 21000.0, wide_y, 0.075),
                (T["back"] - 2.0, 22000.0, wide_y - 300, 0.075), (T["back"] + 2.0, *cam(h, 9200, 0.62)),
                (T["pull"] + 1.0, *cam(h, 9300, 0.7))]
        if t < T["pull"] + 1.0:
            return _ease(keys, t)
        follow = (lead + 500, SL.hill_y(lead + 500) - 260, 0.7)
        if t < self.dur - 9.0:
            u = smoothstep(seg(t, T["pull"] + 1.0, T["pull"] + 3.0))
            k0 = _ease(keys, t)
            return tuple(lerp(a, b, u) for a, b in zip(k0, follow))
        u = smootherstep(seg(t, self.dur - 9.0, self.dur - 1.0))
        lead = self.sled_x(2, t)
        far = (lead + 3000, SL.hill_y(lead + 3000) - 500, 0.2)
        return tuple(lerp(a, b, u) for a, b in zip(follow, far))

    def team_spot(self, kind, t):
        """Where `kind` is while its team pulls its sled: (x, y, scale)."""
        k, seat = RIDERS[kind]
        sx, sy = self.sled_x(k, t), self.sled_y(k, t)
        sc = self.lane_sc(k, t)
        if seat == 0:                # the front one pulls the rope (in front of the nose)
            x = sx + (SL.L / 2 + (230 if kind == "wheels" else 200)) * sc
        else:                        # the back one pushes from behind
            x = sx - (SL.L / 2 + 110) * sc
        y = SL.hill_y(x) + (sy - SL.hill_y(sx)) + (-60 * sc if kind == "lantern" else 0.0)
        return x, y, sc

    def base(self, kind, t):
        """Before the pull: Digs packs the lanes, Glo lights the first lantern, the others wait. -> (x, y)"""
        T = self.T
        x, y0 = self.start[kind]
        if kind == "digger":
            x = self.packed(t) + 60
            return x, SL.hill_y(x)
        if kind == "lantern":
            lx0 = self.lx[0]
            return path([(T["glo"], x, y0), (T["light"] - 0.6, lx0 - 60, lane_y(lx0, 2) - 300)], t)[:2]
        return x, y0

    def walk_t(self, kind):
        """When `kind` sets off to its sled (Digs has the furthest to come down)."""
        return self.T["pack"] + 13.0 if kind == "digger" else self.T["back"]

    def update(self, t, dt):
        T = self.T
        self._t = t
        self.reach = {}
        for kind in KEEPERS:
            m = self.m(kind)
            if m is None:
                continue
            dy, kk = 0.0, 1.0
            m.dig = 0.0
            m.punch = 0.0
            w0, w1 = self.walk_t(kind), T["pull"] - 0.5
            if t < w0:
                x, y = self.base(kind, t)
            elif t < w1:
                bx, by = self.base(kind, w0)
                tx, ty, _ = self.team_spot(kind, w1)
                x, y = path([(w0, bx, by), (w1, tx, ty)], t)[:2]
            else:
                x, y, kk = self.team_spot(kind, t)
            if kind == "digger":
                y = SL.hill_y(x)
                if T["pack"] <= t < T["pack"] + 12.0:
                    m.dig = 0.5 + 0.5 * math.sin(t * 7)
                    if self.s.particles.rng.uniform() < 0.35:
                        self.s.particles.burst(x + 80, SL.hill_y(x) - 20, 2, SN.SNOW, 380, 0.8, 7, kind="snow",
                                               g=1400, spread=0.5, direction=-math.pi * 0.3)
            if t >= w1:
                if kind == "lantern":
                    y += 5 * math.sin(t * 1.4) - 5 * math.sin(w1 * 1.4)
                if kind == "wheels":
                    m.punch = 0.4
                if kind == "springs":
                    dy = -18 * abs(math.sin((t - w1) * 3.2))
            if kind == "tentacles" and t >= T["pull"]:
                sx, sy = self.sled_x(1, t), self.sled_y(1, t)
                sc0 = self.lane_sc(1, t)
                self.reach["tentacles"] = [(sx - (SL.L / 2 - 30) * sc0, sy - (SL.DECK_Y - 10) * sc0)]
            self.place(m, x, t, dt, y=y, dy=dy, k=kk)
        self._sounds(t)

    def _sounds(self, t):
        T = self.T
        if self.crossed(T["pack"] + 0.5):
            self.fx(t, "rustle", 11.0, 0.14, 10500, G - 100)
            self.chat(t, "digger", "huff")
        if self.crossed(T["glo"] + 0.5):
            self.chat(t, "lantern", "hey", icon="!")
        if self.crossed(T["light"]):
            self.hit(t, "bloop", 72, 0.3, self.lx[0], G - 300)
            self.chat(t + 0.3, "lantern", "ooh")
        for i in range(1, len(self.lx)):
            if self.crossed(self.lit_t(i)):
                self.hit(t, "music_box", self.s.note(i % 8, 0 if i < 8 else -1 if i > 20 else 0), 0.15 * (1 - i / 40),
                         self.lx[i], G - 300)
        if self.crossed(T["wide"] - 1.0):
            self.chorus(t, ["springs", "wheels", "teeth", "tentacles", "digger"], "ooh", gap=0.3)
        if self.crossed(T["pull"] + 0.3):
            self.chat(t, "wheels", "hey")
            self.fx(t + 0.5, "slide", 12.0, 0.1, 9500, G)
        if self.crossed(T["pull"] + 3.0):
            self.chorus(t, ["springs", "tentacles"], "huff", gap=0.5)
        if self.crossed(T["pull"] + 7.0):
            self.chat(t, "teeth", "hehe")

    def draw(self, c, t):
        s = self.s
        self._t = t
        self.backdrop(c, t)
        self.trees(c, t, [(7050, 680), (8000, 720)])
        self.snow_ground(c, t, x1=SL.HILL_X0 + 400)
        self.draw_hill_world(c, t, lit=self.lit, packed=self.packed(t))
        sp = self.spark(t)
        if sp is not None:
            c.circle(sp[0], sp[1], 9 / max(0.3, s.zoom), LAMP)
            s.glow_draw(lambda g: g.circle(sp[0], sp[1], 40 / max(0.3, s.zoom), LAMP * 0.8))
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        for k in (2, 1, 0):                                   # far lane first: each sled with its team
            sx, sy = self.sled_x(k, t), self.sled_y(k, t)
            sc = self.lane_sc(k, t)
            SL.draw_sled(c, sx, sy, SL.hill_ang(sx), SLEDS[k][1], nose=1, snow=6.0, sc=sc)
            team = list(SLEDS[k][0])
            if t >= self.T["pull"] - 0.5:                     # the pull rope goes to whoever pulls
                front = team[0]
                m = self.m(front)
                if m is not None and front != "tentacles":
                    nx, ny = sx + (SL.L / 2 + 20) * sc, sy - (SL.RUN_H + 36) * sc
                    c.line(nx, ny, m.x - 60, m.y - 90 if front != "lantern" else m.y - 120, SL.ROPE, 4)
            self.draw_monsters(c, t, kinds=team)
        self.snow_front(c, t, x1=SL.HILL_X0 + 400)


# ====================================================================== RACE

class RaceAct(SnowAct, HillMixin):
    """Countdown and the race down the hill."""
    name = "race"
    names = (-2.0, -1.0)
    depth0, depth1 = 32.0, 32.0
    fall0, fall1 = 0.38, 0.38
    fast_ok = True                       # real sleds on a real hill go faster than walking
    cam_omega = 2.5

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.T = dict(board=1.0, three=6.4, two=7.4, one=8.4, go=9.4)
        rides = P.get("rides", [(250.0, 0.0400), (262.0, 0.0402), (238.0, 0.0398)])
        self.rides = [SL.Ride(SL.START_X, v0, mu, 1.0e-4, self.T["go"] + 0.15 * k)
                      for k, (v0, mu) in enumerate(rides)]
        self.finish = [r.t_push + r.bank_t for r in self.rides]
        self.dur = max(self.finish) + 9.5
        self.stats = {"race_finish_s": [round(f - self.T["go"], 2) for f in self.finish],
                      "race_winner_sled": int(np.argmin(self.finish)),
                      "race_airs": [len(r.takeoffs) for r in self.rides]}
        self.stand = {}                  # where each rider waits before climbing on
        for kind, (k, seat) in RIDERS.items():
            x, y = self.seat_point(k, 0.0, seat)
            self.stand[kind] = x + (70 if seat == 1 else -70)

    def aside_moods(self, t):
        if self.T["go"] < t < min(self.finish):
            return ["wee", "hehe", "wee"]
        return ["hehe", "ooh", "yay"] if t > max(self.finish) else ["ooh", "hehe", "brr"]

    def sled_state(self, k, t):
        r = self.rides[k]
        x, y, a, air, sp = r.at(t - r.t_push)
        return x, y + SL.LANES[k], a, air, sp

    def seat_point(self, k, t, seat):
        x, y, ang, _, _ = self.sled_state(k, t)
        return SL.deck_point(x, y, ang, SEAT_X[seat], nose=-1, sc=SL.LANE_SCALE[k])

    def off_t(self, kind):
        k, seat = RIDERS[kind]
        return self.finish[k] + 1.6 + 0.35 * seat

    def off_spot(self, kind):
        """Where `kind` lands when it hops off its sled: just beside it, in its own lane."""
        k, seat = RIDERS[kind]
        fx, _ = self.seat_point(k, self.off_t(kind), seat)
        x = fx + 240 + 60 * seat
        return x, SL.hill_y(x) + SL.LANES[k] - (60 * SL.LANE_SCALE[k] if kind == "lantern" else 0.0)

    def leader(self, t):
        return min(range(3), key=lambda k: self.sled_state(k, t)[0])

    def target(self, t):
        h = self.s.h
        T = self.T
        x1, _, _, _, _ = self.sled_state(1, t)
        start = (SL.START_X + 160, SL.hill_y(SL.START_X) - 230, 0.78)
        if t < T["go"]:
            return start
        xs = [self.sled_state(k, t) for k in range(3)]
        lead = min(xs, key=lambda q: q[0])
        last = max(xs, key=lambda q: q[0])
        cx = (lead[0] + last[0]) / 2 - 2.0 * lead[4] / (1.6 * self.cam_omega)    # feed-forward against the lag
        cx = max(cx, SL.BANK_X - 300)
        z = 0.72
        cy = SL.hill_y(cx) - (0.62 - 0.5) * h / z - 150
        u = smoothstep(seg(t, T["go"], T["go"] + 2.5))
        end = smoothstep(seg(t, max(self.finish) + 1.0, max(self.finish) + 4.0))
        fin = (SL.BANK_X + 260, G - (0.8 - 0.5) * h / 0.8, 0.8)
        follow = (lerp(start[0], cx, u), lerp(start[1], cy, u), lerp(start[2], z, u))
        return tuple(lerp(a, b, end) for a, b in zip(follow, fin))

    def update(self, t, dt):
        T = self.T
        self.reach = {}
        for kind in KEEPERS:
            m = self.m(kind)
            if m is None:
                continue
            k, seat = RIDERS[kind]
            sx, sy = self.seat_point(k, t, seat)
            sx0, sy0 = self.seat_point(k, 0.0, seat)
            fin = self.finish[k]
            hold = HOLD_ON.get(kind, 0.0) * SL.LANE_SCALE[k]
            x, y, dy, ang = sx, sy + hold, 0.0, 0.0
            hop_on = T["board"] + 0.5 * KEEPERS.index(kind)
            if t < hop_on + 0.8:         # climbs on: a hop from beside the sled onto its seat
                gx = self.stand[kind]
                jp = Jump(gx, SL.hill_y(gx) + SL.LANES[k] + hold * 1.5, sx0, sy0 + hold, apex=70)
                if t < hop_on:
                    x, y = gx, SL.hill_y(gx) + SL.LANES[k] + hold * 1.5
                elif t < hop_on + jp.dur:
                    x, y = jp.at(t - hop_on)
                else:
                    x, y = sx0, sy0 + hold
            else:
                ang = self.sled_state(k, t)[2]
                if fin <= t:             # into the snowbank: then everyone pops out and hops off
                    off = self.off_t(kind)
                    fx, fy = self.seat_point(k, min(t, off), seat)
                    fy += hold
                    lx, ly = self.off_spot(kind)
                    jp = Jump(fx, fy, lx, ly, apex=55)
                    if t < off:
                        x, y = fx, fy
                    elif t < off + jp.dur:
                        x, y = jp.at(t - off)
                        ang *= 1 - seg(t, off, off + jp.dur)
                    else:                # then over to a row in front of the bank
                        w0 = off + jp.dur + 0.4
                        rx = SL.BANK_X + 330 + 150 * KEEPERS.index(kind)
                        ry = G - (60 if kind == "lantern" else 0.0)
                        x, y = path([(w0, lx, ly), (w0 + 2.6, rx, ry)], t)[:2]
                        ang = 0.0
                        if kind == "springs" and t > w0 + 2.8:
                            ph = (t - w0 - 2.8) % 1.3
                            dy = -4 * 50 * (ph / 0.42) * (1 - ph / 0.42) if ph < 0.42 else 0.0
            if kind == "tentacles" and T["board"] + 2.5 < t < fin:          # holds on with two tentacles
                fx_, fy_ = SL.deck_point(*self.sled_state(k, t)[:3], -SL.L / 2 + 40, nose=-1, sc=SL.LANE_SCALE[k])
                self.reach["tentacles"] = [(fx_, fy_ + 6)]
            if kind == "wheels":
                m.punch = 0.5 if T["go"] < t < fin else 0.0
            if kind == "teeth":
                m.punch_l = 0.4 if T["go"] < t < fin else 0.0       # arms up: whee
            off = self.off_t(kind)
            if t < hop_on:
                kk = SL.LANE_SCALE[k]
            elif t < off + 0.6:
                kk = SL.LANE_SCALE[k]
            else:                        # walking out of its lane towards us: back to full size
                kk = lerp(SL.LANE_SCALE[k], 1.0, smoothstep(seg(t, off + 0.6, off + 4.0)))
            self.place(m, x, t, dt, y=y, dy=dy, ang=ang, k=kk)
        # snow spray off the runners, more the faster they go
        p = self.s.particles
        for k in range(3):
            x, y, a, air, sp = self.sled_state(k, t)
            if T["go"] < t < self.finish[k] and not air and p.rng.uniform() < min(0.9, sp / 900.0):
                p.burst(x + (SL.L / 2 - 20) * SL.LANE_SCALE[k], y - 6, 2, SN.SNOW, 160 + sp * 0.15, 0.55,
                        6 * SL.LANE_SCALE[k], kind="snow", g=1600, spread=0.5, direction=-math.pi * 0.25)
            if self.crossed(self.finish[k] - 0.05):
                p.burst(SL.BANK_X - 80, y - 60, 40, SN.SNOW, 700, 1.4, 14, kind="snow", g=1300, spread=1.2,
                        direction=-math.pi * 0.62)
        self._sounds(t)

    def _sounds(self, t):
        T = self.T
        if self.crossed(0.6):
            self.chat(t, "springs", "hey", icon="sled")
        for q, kind in enumerate(KEEPERS):
            if self.crossed(T["board"] + 0.5 * q + 0.1):
                self.hit(t, "boing" if kind == "springs" else "clack", 60 + q * 2, 0.16, self.stand[kind], G)
        for icon, key, kind, step in (("3", "three", "springs", 0), ("2", "two", "lantern", 2), ("1", "one", "wheels", 4)):
            if self.crossed(T[key]):
                self.chat(t, kind, "hey", icon=icon, step=step, vel=0.4)
                self.hit(t, "soft_bell", 67 + step, 0.22, SL.START_X, G - 3000)
        if self.crossed(T["go"]):
            self.hit(t, "chime", 79, 0.3, SL.START_X, G - 3000)
            self.chorus(t + 0.2, ["wheels", "springs", "lantern", "digger", "tentacles", "teeth"], "wee", gap=0.15,
                        icon="note")
        for k, r in enumerate(self.rides):
            if self.crossed(r.t_push + 0.3):
                self.fx(t, "sand_scrape", self.finish[k] - r.t_push - 0.3, 0.12, SL.START_X, G - 3000)
            for to in r.takeoffs:
                if self.crossed(r.t_push + to):
                    rider = SLEDS[k][0][0 if k != 1 else 1]
                    self.chat(t, rider, "wee" if k != 2 else "hehe")
            for ld in r.landings:
                if self.crossed(r.t_push + ld):
                    x, y, _, _, _ = self.sled_state(k, t)
                    self.hit(t, "thud", 44, 0.18, x, y)
                    self.s.particles.burst(x, y - 8, 14, SN.SNOW, 300, 0.7, 8, kind="snow", g=1400, spread=1.0)
            if self.crossed(self.finish[k] - 0.05):
                self.fx(t, "whoosh", 0.7, 0.2, SL.BANK_X, G - 60)
                self.hit(t + 0.05, "thud", 40, 0.3, SL.BANK_X, G - 60)
        # mid-race shouts so the long run stays lively (the asides add more)
        for q, tt in enumerate((14.0, 19.0, 26.0, 31.0)):
            if self.crossed(T["go"] + tt):
                k = q % 3
                self.chat(t, SLEDS[k][0][q % 2], "wee" if q % 2 == 0 else "hehe")
        last = max(self.finish)
        if self.crossed(last + 1.6):
            self.chorus(t, ["springs", "digger", "lantern"], "hehe", gap=0.3)
        if self.crossed(last + 4.0):
            self.chorus(t, ["wheels", "tentacles", "teeth", "springs", "lantern", "digger"], "yay", gap=0.18,
                        icon="star")
            for q, n in enumerate((60, 64, 67, 72, 76, 79)):
                self.hit(t + 0.6 + q * 0.12, "soft_bell", n, 0.24, SL.BANK_X, G - 300)

    def draw(self, c, t):
        s, T = self.s, self.T
        self.backdrop(c, t)
        self.trees(c, t, [(7050, 680), (8000, 720), (8800, 660)])
        self.snow_ground(c, t, x1=SL.HILL_X0 + 400)
        self.draw_hill_world(c, t, lit=lambda x: 1.0)
        # start line on the flat top: a rope between two flag poles across the three lanes
        sx_ = SL.START_X - SL.L / 2 - 40
        if s.visible(sx_ - 200, sx_ + 200):
            sy = SL.hill_y(sx_)
            c.line(sx_, sy + SL.LANES[2] - 10, sx_, sy - 260 + SL.LANES[2], np.array([150, 112, 72]), 8)
            c.polygon([(sx_, sy - 260 + SL.LANES[2]), (sx_ - 70, sy - 230 + SL.LANES[2]), (sx_, sy - 200 + SL.LANES[2])],
                      np.array([200, 70, 60]))
        gl = self.m("lantern")
        for k in (2, 1, 0):                      # far lane first
            x, y, ang, air, sp = self.sled_state(k, t)
            if air:                              # its shadow on the snow under it
                gy = SL.hill_y(x) + SL.LANES[k]
                c.polygon(ellipse(x, gy + 2, SL.L * 0.42, 7, 20), SN.SNOW_SHADE)
            SL.draw_sled(c, x, y, ang, SLEDS[k][1], nose=-1, snow=4.0, sc=SL.LANE_SCALE[k])
            riders = [kind for kind in SLEDS[k][0]]
            if gl is not None and "lantern" in riders and "lantern" in self.poses:
                self.lantern_light(c, gl.x, gl.y - 140, k=0.6)
            self.draw_monsters(c, t, kinds=riders)
        # the birds come along for a stretch
        if T["go"] + 12.0 < t < T["go"] + 22.0:
            k0 = self.leader(t)
            x, y, _, _, _ = self.sled_state(k0, t)
            for b in range(2):
                u = seg(t, T["go"] + 12.0, T["go"] + 22.0)
                bx = x - 260 - 140 * b + 120 * math.sin(t * 1.3 + b)
                by = y - 420 - 60 * b + 40 * math.sin(t * 2.1 + b) - 600 * (1 - smoothstep(seg(u, 0, 0.15))) \
                    - 600 * smoothstep(seg(u, 0.85, 1.0))
                PR.bird(c, bx, by, 1.6, -1, math.sin(t * 30 + b), BIRD_COLS[b], t)
        dent = max((smoothstep(seg(t, f - 0.1, f + 0.3)) for f in self.finish), default=0.0)
        SL.snowbank(c, SL.BANK_X, G + 4, w=300.0, h=150.0, dent=dent)
        for kind in KEEPERS:                     # snow on their heads after the bank
            k, seat = RIDERS[kind]
            m = self.m(kind)
            if m is not None and t > self.finish[k] + 0.1:
                from families.foundry.products.monster import TOPS
                u = 1 - smoothstep(seg(t, self.finish[k] + 5.5, self.finish[k] + 7.0))
                hy = m.y - TOPS[kind] * m.k * 0.82 + self.poses.get(kind, (0, 0))[0]
                c.polygon(ellipse(m.x, hy, 46 * u, 18 * u, 18, math.pi, 2 * math.pi), SN.SNOW)
        self.snow_front(c, t, x1=SL.HILL_X0 + 400)


# ====================================================================== COZY

COZY_PARK = [180.0, 700.0, -340.0]         # the sleds, left of the treehouse (nose to the left)


class CozyAct(SnowAct):
    """Back at the treehouse in the falling snow."""
    name = "cozy"
    names = (-2.0, -1.0)
    depth0, depth1 = 32.0, 34.0
    fall0, fall1 = 0.7, 0.85

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.dur = 27.0
        self.arrive = 10.0
        self.order = ["wheels", "springs", "lantern", "digger", "tentacles", "teeth"]

    def aside_moods(self, t):
        return ["aww", "mm", "hehe"]

    def sled_x(self, k, t):
        t0 = 0.4 * k
        return path([(t0, 4400.0 + 650 * k, G), (self.arrive + t0, COZY_PARK[k], G)], t)[0]

    def target(self, t):
        h = self.s.h
        keys = [(0.0, *cam(h, 3200, 0.62)), (self.arrive - 2.0, *cam(h, 1500, 0.62)),
                (self.arrive + 3.0, *cam(h, 1500, 0.8, 0.86)), (self.arrive + 7.0, *cam(h, 1550, 0.8, 0.86)),
                (self.dur, 1500.0, G - 900.0, 0.5)]
        return _ease(keys, t)

    def update(self, t, dt):
        self.reach = {}
        for kind in KEEPERS:
            m = self.m(kind)
            if m is None:
                continue
            k, seat = RIDERS[kind]
            y = G - 60 if kind == "lantern" else None
            t0 = 0.4 * k
            sx = self.sled_x(k, t)
            puller = sx - SL.L / 2 - (230 if kind == "wheels" else 200) if seat == 0 else sx + SL.L / 2 + 110
            x = puller
            if t >= self.arrive + t0 + 0.3:
                x = path([(self.arrive + t0 + 0.3, puller, G), (self.arrive + t0 + 4.5, HOME[kind], G)], t)[0]
            self.place(m, x, t, dt, y=y)
            if kind == "tentacles" and t < self.arrive + t0 + 0.3:
                self.reach["tentacles"] = [(sx - SL.L / 2 - 40, G - SL.RUN_H - 30)]
        self._sounds(t)

    def _sounds(self, t):
        if self.crossed(1.0):
            self.fx(t, "slide", self.arrive, 0.08, 2500, G)
        if self.crossed(self.arrive + 6.0):
            self.chat(t, "lantern", "aww")
        if self.crossed(self.arrive + 8.0):
            self.chorus(t, ["springs", "wheels", "digger"], "mm", gap=0.4)
        if self.crossed(self.arrive + 11.5):
            self.chat(t, "tentacles", "hey", icon="heart")
        if self.crossed(self.arrive + 13.0):
            for q, n in enumerate((72, 76, 79, 84)):
                self.hit(t + q * 0.2, "music_box", n - 12, 0.14, 1400, G - 600)

    def draw(self, c, t):
        self.backdrop(c, t)
        self.trees(c, t, [(-400, 640), (200, 700), (3950, 720), (4500, 660)])
        self.snow_ground(c, t)
        self.draw_village(c, t, peek=1.0, hog=0.7)
        for k in range(3):
            SL.draw_sled(c, self.sled_x(k, t), G, 0.0, SLEDS[k][1], nose=-1, snow=8.0 + 6 * seg(t, self.arrive, self.dur))
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t)
        for k in range(3):                       # the pull ropes
            m = self.m(SLEDS[k][0][0])
            sx = self.sled_x(k, t)
            if m is not None and SLEDS[k][0][0] != "tentacles" and t < self.arrive + 0.4 * k + 0.3:
                c.line(sx - SL.L / 2 - 20, G - SL.RUN_H - 36, m.x + 60, m.y - (120 if m.kind == "lantern" else 90),
                       SL.ROPE, 4)
        self.snow_front(c, t)
