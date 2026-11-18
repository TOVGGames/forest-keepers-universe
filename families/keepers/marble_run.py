"""Forest Keepers episode 6: The Treetop Marble Run (docs/engines/forest_keepers_marble_run.md).

  BALL     - at the treehouse Springs bounces a little wooden ball; it rolls off the platform, bounces down and away,
             Wheels races after it. Glo has an idea: a marble run.
  MARBLES  - the workshop by the two big trees: Twigs saws six cubes off a beam at the stop block, Hans tips them into
             the tumbler, Wheels drives it, out roll six wooden balls; Glo's light flares over each one and turns it
             a Keeper's colour.
  RUN      - building the run between the trees: boards cut to length, pegs in the trunks (Springs) checked with the
             slope level (Glo), the boards hoisted on a pulley (Hans), the peg forest, the tunnel (Digs), the last
             ramp and the tray. Test run with Wheels' plain ball.
  RACE     - Glo loads the six marbles behind the gate, Springs bounces up to the lever; 3, 2, 1: six marbles race
             down the run (real physics, marbles.py), through the peg forest and the tunnel, into the tray.
  CHEER    - the winner's Keeper cheers, the marbles in the tray, the run lit in the trees.
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, Jump, Night, PLANK, bunny, ellipse, hedgehog, lerp, rect, seg, wood_sign, \
    smoothstep, smootherstep
from families.foundry.keepers.halloween import KeeperAct, hops, path
from families.foundry.style import IRON, lighten
from families.foundry.tree_monsters import LAMP, LEAF, TRUNK, tree

from . import marbles as M
from . import props as PR
from .animal_houses import BIRD_COLS, BUNNY_X, HEDGE_X, POST, POST_TOP, POSTS, _ease, bez, flying_bird, saw_to

G = 1000.0
KEEPERS = ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"]
HOME = {"lantern": 1180.0, "tentacles": 1350.0, "teeth": 1530.0, "springs": 1690.0, "wheels": 1850.0,
        "digger": 1990.0}
LEAF_FALL = [np.array([176, 112, 52]), np.array([150, 84, 44]), np.array([196, 150, 64])]
# little branch stubs up the right side of TREE_B: Springs bounces up them to the start platform
STUBS = [(M.TREE_B + 128 + (14 if i % 2 else -6) - 3.0 * i, G - 150.0 * (i + 1)) for i in range(10)]


def cam(h, x, z, gf=0.84, ground=G):
    """Camera keyframe: centre x, zoom, with the ground at fraction gf of the screen height."""
    return x, ground - (gf - 0.5) * h / z, z


class MarbleAct(KeeperAct):
    """An autumn-night act of the marble run episode: leaves falling, the Keepers talk (act.chat)."""

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + 71), G, -2500, 10500)

    def place(self, m, x, t, dt, k=None, **kw):
        if m is not None:
            m.k = self.s.k * (1.0 if k is None else k)
        super().place(m, x, t, dt, **kw)

    def chat(self, t, kind, mood, **kw):
        self.s.chatter.say(self.t0 + t, kind, mood, **kw)

    def chorus(self, t, kinds, mood, gap=0.2, **kw):
        self.s.chatter.chorus(self.t0 + t, kinds, mood, gap=gap, **kw)

    def leaves(self, rate=0.05):
        """Autumn leaves drifting down from wherever the camera looks."""
        p = self.s.particles
        if p.rng.uniform() < rate:
            x0, x1, y0, _ = self.s.view()
            p.burst(p.rng.uniform(x0, x1), y0 - 40, 1, LEAF_FALL[int(p.rng.integers(3))], 60, 7.0, 7, g=60,
                    spread=1.2)

    def backdrop(self, c, t):
        self.night.draw(self.s, c, t)
        self.night.ground_slab(self.s, c)

    def forest(self, c, xs):
        for j, (x, h) in enumerate(xs):
            if self.s.visible(x - 260, x + 260):
                tree(c, x, G, h, 900 + j)

    # ----- the village from episodes 4-5 -----

    def draw_village(self, c, t, peek=1.0, birds_home=(1, 1, 1, 1)):
        s, H = self.s, self.house
        if not s.visible(700, 3700):
            return
        H.draw_tree(c, s)
        H.draw_house(c, s, t, windows=1.0, lanterns=1.0)
        for bx, r in ((HEDGE_X - 40, 120), (HEDGE_X + 90, 90), (BUNNY_X + 40, 140), (BUNNY_X - 120, 100)):
            c.circle(bx, G - r * 0.55, r, LEAF[1] * 0.75)
        for k in range(4):
            px = POSTS[k]
            rect(c, px - 13, POST_TOP, px + 13, G + 40, POST)
            rect(c, px - 34, POST_TOP - 8, px + 34, POST_TOP, POST * 1.15)
        homes = [(POSTS[j], POST_TOP) for j in range(4)] + [(HEDGE_X, G), (BUNNY_X, G)]
        for j, (x, y) in enumerate(homes):
            PR.draw_house(c, s, PR.SPECS[j], x, y, t, paint=1.0, lamp=1.0, inside=1.0)
        for b in range(4):
            if not birds_home[b]:
                continue
            hx, hy = PR.hole_center(PR.SPECS[b], POSTS[b], POST_TOP)
            out = peek * (0.6 + 0.4 * math.sin(t * 1.1 + b * 1.7))
            c.circle(hx + 3 * out, hy + 3, 8.5, BIRD_COLS[b][0])
            c.circle(hx + 6 * out, hy + 6, 4.5, BIRD_COLS[b][1])
            c.circle(hx + 5 * out, hy, 2.0, np.array([16, 16, 20]))

    # ----- the course -----

    def full_course(self):
        return dict(pegs=99, boards={k: (0.0, 0.0, 0.0) for k in range(M.N_BOARDS)}, stops=99, box=(99, 1.0),
                    final=1.0, dug=1.0, lights=[1.0] * 9, finish=1.0, gate=0.0, platform=True, pulley=None)

    def draw_course(self, c, t, st, marbles=None, before_front=None, after=None):
        """The whole run in layers. st: what is built (see full_course). marbles(c): draws the marbles between the
        backs and the fronts; before_front / after: extra layers (things on the boards, Keepers in front)."""
        s = self.s
        M.draw_mound(c, s, "back")
        M.draw_trees(c, s, t)
        for (x, y) in STUBS:
            c.line(x - 30, y + 10, x + 26, y, TRUNK * 0.95, 14)
        for (x, y) in STUBS_A:
            c.line(x + 30, y + 10, x - 26, y, TRUNK * 0.95, 14)
        M.draw_turn_lights(c, s, st.get("lights", []), t)
        M.draw_trunk_pegs(c, st.get("pegs", 0))
        if st.get("platform"):
            M.draw_platform(c)
        boards = st.get("boards", {})
        for k, pose in boards.items():
            if pose is not None:
                M.draw_board_back(c, k, *pose)
        ns = st.get("stops", 0)
        for i, (x, y0, y1) in enumerate(M.stops()):
            if i < ns:
                M.draw_stop(c, x, y0, y1, "back")
        bx = st.get("box")
        if bx is not None:
            M.draw_pegbox_back(c, *bx)
        M.draw_final_back(c, st.get("final", 0.0), st.get("tray", True))
        if marbles is not None:
            marbles(c)
        if before_front is not None:
            before_front(c)
        for k, pose in boards.items():
            if pose is not None:
                M.draw_board_front(c, k, *pose)
        for i, (x, y0, y1) in enumerate(M.stops()):
            if i < ns:
                M.draw_stop(c, x, y0, y1, "front")
        if bx is not None:
            M.draw_pegbox_front(c, *bx)
        M.draw_final_front(c, st.get("final", 0.0), st.get("tray", True))
        if st.get("tray", True):
            M.draw_tray_stand(c)
        M.draw_mound(c, s, "cover", st.get("dug", 0.0))
        if st.get("finish") is not None:
            M.draw_finish(c, s, st.get("finish", 0.0), t)
        if st.get("platform"):
            M.draw_gate(c, st.get("gate", 0.0))
        if st.get("pulley") is not None:
            M.draw_pulley(c, st["pulley"])
        if after is not None:
            after(c)


# ====================================================================== BALL

BALL_R = 20.0
TOP_WHEELS = 335.0              # top of Wheels' head above his feet at k = 1


class BallFlight:
    """Wheels' little wooden ball after Springs' last bounce: off the platform, real bounces on the ground (each one
    lower, restitution 0.45, a little speed lost at every bounce), then it rolls and slows to a stop. Simulated at
    1 kHz from the launch; the launch speed is picked so it stops at the hedgehog's door."""
    E, ROLL_DECEL = 0.45, 70.0

    def __init__(self, x0, y0, vy0, stop_x, ground=G):
        lo, hi = 150.0, 900.0
        for _ in range(30):
            vx = (lo + hi) / 2
            if self._sim(x0, y0, vx, vy0, ground)[-1][1] < stop_x:
                lo = vx
            else:
                hi = vx
        self.vx = (lo + hi) / 2
        self.rec = self._sim(x0, y0, self.vx, vy0, ground)
        self.dur = self.rec[-1][0]
        self.bounces = []
        prev = None
        for (t, x, y, a, onground) in self.rec:
            if prev is not None and onground and not prev:
                self.bounces.append((t, x))
            prev = onground

    def _sim(self, x, y, vx, vy, ground):
        dt, t, a = 0.001, 0.0, 0.0
        out = [(0.0, x, y, 0.0, False)]
        rolling = False
        while t < 30:
            t += dt
            if not rolling:
                vy += GRAVITY * dt
                x += vx * dt
                y += vy * dt
                a += vx / BALL_R * dt * 0.6
                hit = False
                if y >= ground - BALL_R and vy > 0:
                    y = ground - BALL_R
                    vy = -vy * self.E
                    vx *= 0.9
                    hit = True
                    if abs(vy) < 60:
                        vy, rolling = 0.0, True
                out.append((t, x, y, a, hit))
            else:
                vx = max(0.0, vx - self.ROLL_DECEL * dt)
                x += vx * dt
                a += vx / BALL_R * dt
                out.append((t, x, y, a, False))
                if vx <= 0:
                    break
        return out

    def at(self, tau):
        i = int(min(len(self.rec) - 1, max(0, tau * 1000)))
        _, x, y, a, _ = self.rec[i]
        return x, y, a


class BallAct(MarbleAct):
    """At the treehouse: Springs bounces Wheels' little wooden ball, it gets away; Wheels chases it; Glo's idea."""
    name = "ball"
    names = (1.0, 7.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        H = self.house
        self.py = H.py
        self.T = dict(dribble=2.6, escape=6.2, idea=22.0, go=26.0)
        self.dur = 35.0
        self.bx = 1700.0                                   # where Springs bounces it on the platform
        self.n_drib = 6
        self.drib_T = 2 * math.sqrt(2 * 110.0 / GRAVITY)
        # he lets it drop from the top of a bounce; it gets away at its n-th touch of the planks
        self.T["escape"] = self.T["dribble"] + self.drib_T / 2 + self.n_drib * self.drib_T
        self.flight = BallFlight(self.bx, self.py - BALL_R, -420.0, HEDGE_X - 70)
        self.stop_t = self.T["escape"] + self.flight.dur
        self.stop_x = self.flight.at(self.flight.dur)[0]
        T = self.T
        T["nudge"] = self.stop_t + 0.8
        T["back"] = T["nudge"] + 2.0
        # Springs comes down the ladder rung by rung
        lx = H.ladder_x
        pts = [(1690.0, self.py), (H.p1 - 20, self.py)] + [(lx, H.rung_y(k)) for k in reversed(range(0, H.n_rungs, 2))] \
            + [(lx + 90, G)]
        self.down = []
        t = T["escape"] + 1.8
        for a, b in zip(pts, pts[1:]):
            jp = Jump(a[0], a[1], b[0], b[1], apex=30)
            self.down.append((t, jp))
            t += jp.dur + 0.1
        self.down_end = t

    def aside_moods(self, t):
        return ["hehe", "ooh", "aww", "q"]

    # ----- the ball -----

    def ball(self, t):
        """(x, y, angle) of the ball."""
        T = self.T
        top = self.py - BALL_R - 110.0
        if t < T["escape"]:
            if t < T["dribble"]:                           # Springs holds it up, ready
                return self.bx, top - 3 * math.sin(t * 2.0), 0.0
            u = (t - T["dribble"] + self.drib_T / 2) % self.drib_T
            vy0 = GRAVITY * self.drib_T / 2
            h = vy0 * u - GRAVITY * u * u / 2
            return self.bx, self.py - BALL_R - h, 0.0
        tau = t - T["escape"]
        if tau < self.flight.dur + 0.8:
            return self.flight.at(tau)
        # the hedgehog noses it back a little; Wheels flicks it up onto his head and takes it home
        x0, y0, a0 = self.flight.at(self.flight.dur)
        x1, a1 = x0 - 70, a0 - 70 / BALL_R
        if t < T["back"]:
            u = smootherstep(seg(t, T["nudge"], T["nudge"] + 0.9))
            return lerp(x0, x1, u), y0, lerp(a0, a1, u)
        m = self.m("wheels")
        wx, wy = (m.x, m.y) if m is not None else (x1, G)
        head = (wx, wy - TOP_WHEELS * self.s.k - BALL_R + 4)
        if t < T["back"] + 0.6:                            # the flick: a little ballistic arc
            u = (t - T["back"]) / 0.6
            x = lerp(x1, head[0], u)
            y = lerp(y0, head[1], u) - 4 * 120 * u * (1 - u)
            return x, y, a1 - 6 * u
        return head[0], head[1], a1 - 6

    def hog(self, t):
        """The hedgehog: (x, amount out of its door) - it comes out to nose the ball back, then goes home."""
        T = self.T
        hx = HEDGE_X - 10
        out = smoothstep(seg(t, self.stop_t + 0.1, T["nudge"])) * (1 - smoothstep(seg(t, T["back"] + 0.8, T["back"] + 2.2)))
        x = hx - 40 * out - 24 * smoothstep(seg(t, T["nudge"], T["nudge"] + 0.6)) * \
            (1 - smoothstep(seg(t, T["nudge"] + 0.6, T["nudge"] + 1.2)))
        return x, out

    # ----- camera -----

    def target(self, t):
        h, T = self.s.h, self.T
        if t < 1.5:
            return 1500.0, G - 420.0, 0.8
        if t < T["escape"] + 0.3:
            u = smootherstep(seg(t, 1.5, 3.0))
            return lerp(1500.0, 1690.0, u), lerp(G - 420.0, G - 640.0, u), lerp(0.8, 1.25, u)
        if t < self.stop_t + 0.6:
            bx, by, _ = self.ball(t)
            return bx + 120, G - 380.0, 0.95
        if t < T["back"] + 0.6:
            return self.stop_x - 60, G - 250.0, 1.3
        if t < T["idea"] - 1.0:
            m = self.m("wheels")
            return (m.x if m is not None else 2000.0) - 60, G - 330.0, 1.0
        if t < T["go"] + 1.0:
            return 1560.0, G - 380.0, 1.05
        u = smootherstep(seg(t, T["go"] + 1.0, self.dur))
        return lerp(1560.0, 3600.0, u), G - 420.0, lerp(1.05, 0.8, u)

    # ----- the Keepers -----

    def update(self, t, dt):
        T, H = self.T, self.house
        self.reach = {}
        for q, kind in enumerate(KEEPERS):
            m = self.m(kind)
            if m is None:
                continue
            x0 = HOME[kind]
            y, dy, walk = None, 0.0, None
            x = x0
            m.punch = m.punch_l = 0.0
            if kind == "lantern":
                y = G - 60 - 14 * math.sin(t * 0.9)
                x = x0 + 24 * math.sin(t * 0.37)
                bump = math.exp(-((t - T["idea"] - 0.3) / 0.6) ** 2)
                m.lamp = 1.0 + 0.9 * bump
                dy = -30 * bump
            if kind == "springs":
                x, y, dy = self._springs(t, m)
            if kind == "wheels":
                x = self.wheels_x(t)
                m.punch = 0.5 * smoothstep(seg(t, T["nudge"] + 0.4, T["nudge"] + 0.9)) * \
                    (1 - smoothstep(seg(t, T["back"] + 0.4, T["back"] + 1.0)))
            if t >= T["go"]:
                lead = T["go"] + 0.3 * q
                x1 = x + 2000
                if kind == "springs":
                    x, lift, sq = hops(x, x1, lead, lead + 9.0, t, apex=55, step=160)
                    dy -= lift
                    m.spring = sq
                elif kind == "lantern":
                    x, y = path([(lead, x, y), (lead + 9.0, x1, G - 60)], t)[:2]
                else:
                    x = path([(lead, x, G), (lead + 9.0, x1, G)], t)[0]
            self.place(m, x, t, dt, y=y, dy=dy, walk=walk)
        if self.crossed(0.1):
            self.s.particles.leaves(H.tx, G - 1150, 3, 300)
        self.leaves(0.05)
        self._sounds(t)

    def _springs(self, t, m):
        """On the platform bouncing the ball, then down the ladder rung by rung."""
        T = self.T
        m.spring = 0.0
        x, y, dy = 1690.0, self.py, 0.0
        if T["dribble"] <= t < T["escape"]:
            u = (t - T["dribble"]) % self.drib_T / self.drib_T     # hops in time with the bounces
            dy = -4 * 22 * u * (1 - u)
            m.spring = 0.5 * max(0.0, 1 - min(u, 1 - u) / 0.12)
        for i, (t0, jp) in enumerate(self.down):
            nxt = self.down[i + 1][0] if i + 1 < len(self.down) else 1e9
            if t0 <= t < t0 + jp.dur:
                x, y = jp.at(t - t0)
            elif t0 + jp.dur <= t < nxt:
                x, y = jp.x1, jp.y1
                m.spring = 0.7 * max(0.0, 1 - (t - t0 - jp.dur) / 0.12)
        if t >= self.down_end:
            x, y = path([(self.down_end, self.down[-1][1].x1, G), (self.down_end + 2.0, HOME["springs"] + 380, G)], t)[:2]
        return x, y, dy

    def wheels_x(self, t):
        T = self.T
        chase0 = T["escape"] + 0.9
        stop = self.stop_x - 100
        keys = [(chase0, HOME["wheels"], G), (self.stop_t - 0.2, stop - 60, G), (T["nudge"] + 0.5, stop - 60, G),
                (T["back"], stop - 70, G), (T["idea"] - 1.5, 1680.0, G)]
        return path(keys, t)[0]

    # ----- sounds -----

    def _sounds(self, t):
        T = self.T
        if self.crossed(1.2):
            self.chat(t, "springs", "hey", icon="ball")
        for k in range(self.n_drib):
            if self.crossed(T["dribble"] + (k + 0.5) * self.drib_T):
                self.hit(t, "clack", self.s.note(k % 5, 0), 0.16, self.bx, self.py)
        if self.crossed(T["escape"] + 0.15):
            self.chat(t, "springs", "uhoh")
        for tb, xb in self.flight.bounces:
            if self.crossed(T["escape"] + tb):
                self.hit(t, "clack", 60, 0.22 * max(0.25, 1 - tb / 2.0), xb, G)
        if self.crossed(T["escape"] + 0.5):
            self.chat(t, "wheels", "hey", icon="!")
        if self.crossed(T["escape"] + 1.0):
            self.fx(t, "marble_roll", self.flight.dur - 1.0, 0.1, 2400, G)
        for i, (t0, jp) in enumerate(self.down):
            if self.crossed(t0):
                self.hit(t, "boing", 66 - i, 0.14, jp.x0, jp.y0)
        if self.crossed(self.stop_t + 0.3):
            self.fx(t, "rustle", 1.2, 0.12, HEDGE_X, G)
        if self.crossed(T["nudge"]):
            self.hit(t, "bloop", 74, 0.18, HEDGE_X, G)
        if self.crossed(T["nudge"] + 1.0):
            self.chat(t, "wheels", "aww")
        if self.crossed(T["back"] + 0.4):
            self.chat(t, "wheels", "yay", icon="ball")
        if self.crossed(T["idea"] - 2.2):
            self.chat(t, "lantern", "hm")
        if self.crossed(T["idea"]):
            self.hit(t, "bloop", 72, 0.3, HOME["lantern"], G - 400)
            self.chat(t + 0.15, "lantern", "idea", icon="run")
            for k, n in enumerate((72, 76, 79, 84)):
                self.hit(t + 0.3 + k * 0.1, "chime", n, 0.22, HOME["lantern"], G - 400)
        if self.crossed(T["idea"] + 1.6):
            self.chorus(t, ["springs", "wheels", "tentacles", "digger", "teeth"], "yay", gap=0.2, icon="star")
        if self.crossed(T["go"] + 0.5):
            self.fx(t, "rustle", 6.0, 0.14, 2600, G)

    # ----- drawing -----

    def draw(self, c, t):
        s, T = self.s, self.T
        self.backdrop(c, t)
        self.forest(c, [(-400, 640), (200, 700), (3950, 720), (4500, 660)])
        peek = 0.4 + 0.6 * smoothstep(seg(t, T["escape"] + 0.6, T["escape"] + 1.6))
        self.draw_village(c, t, peek=peek)
        hx, out = self.hog(t)
        if out > 0:
            hedgehog(c, hx - 30 * out, G, 1.1, -1, t)
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t)
        bx, by, ba = self.ball(t)
        M.draw_marble(c, bx, by, BALL_R, ba, M.PLAIN)


# ====================================================================== MARBLES (the workshop right of TREE_B)

W_SIGN = 7120.0
BEAM_PILE = 7260.0
W_HORSES = (7420.0, 7640.0)
BEAM_Y = (G - 150.0, G - 102.0)        # the square beam's top / bottom on the horses
CUBE = 48.0                            # every cube as long as the beam is wide: cubes
W_STOP = 7760.0                        # stop block
W_CUT = W_STOP - CUBE
BEAM_LEN = 6 * CUBE + 44.0
BEAM_C = W_STOP - 150.0 - BEAM_LEN / 2  # where Digs sets the beam down
BASKET = (7750.0, G - 4.0)             # the cubes drop into it (centre of its bottom)
BARREL = (8580.0, G - 300.0)           # the tumbler on its stand ...
BARREL_R = 104.0
ROLLER_R = 26.0
ROLLERS = (8510.0, 8650.0)             # ... resting on two rollers ...
ROLLER_Y = BARREL[1] + math.sqrt((BARREL_R + ROLLER_R) ** 2 - 70.0 ** 2)
DYNO = 8900.0                          # ... driven by a belt from the two rollers Wheels drives on
DYNO_Y = G - 26.0
CRATE = (8730.0, G - 200.0)            # Springs' step up to the top of the barrel
HATCH_TOP, HATCH_OUT = -math.pi / 2, 0.8 * math.pi      # the hatch on top (loading), lower left (balls out)
TRAY_W = (8040.0, 8360.0)               # the tray table the new balls roll into, seven cups
TRAY_WY = G - 150.0
CUP = [TRAY_W[0] + 30.0 + 44.0 * i for i in range(7)]   # cup 0 (left) holds Wheels' plain ball
CHUTE = ((BARREL[0] + BARREL_R * math.cos(HATCH_OUT) - 6, BARREL[1] + BARREL_R * math.sin(HATCH_OUT) + 10),
         (TRAY_W[1] + 6, TRAY_WY - 6))


class MarblesAct(MarbleAct):
    """The workshop: six cubes sawn off a beam, tumbled round in a barrel, painted in the Keepers' colours."""
    name = "marbles"
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.cyc = 2.2
        self.P0 = 7.0                                        # the beam is pushed up to the stop block
        self.cut_end = self.cut_t(5) + 1.6
        self.L0 = self.cut_end + 0.8                          # Hans takes the basket to the barrel
        self.pour = self.L0 + 3.4
        self.close = self.pour + 2.2                          # Springs bounces the hatch shut
        self.tumble = (self.close + 1.6, self.close + 12.6)
        self.open_t = self.tumble[1] + 0.8
        self.out_t = [self.open_t + 0.9 + 0.55 * i for i in range(6)]
        self.paint_t = [self.out_t[5] + 2.5 + 2.7 * i for i in range(6)]
        self.done_t = self.paint_t[5] + 2.4
        self.dur = self.done_t + 6.5
        self.turns = (HATCH_OUT - HATCH_TOP) + 2 * math.pi * 3
        self.stats = {"cubes": 6, "cubes_even": True, "marbles": 6}

    def cut_t(self, i):
        return self.P0 + 1.4 + i * self.cyc

    def aside_moods(self, t):
        return ["hehe", "mm", "ooh", "hm"]

    # ----- the beam and the cubes -----

    def beam(self, t):
        """('pile'|'carry'|'horses', left, right, top y) or None once it is all cut."""
        P = self.P0
        if t < P - 3.0:
            return "pile", BEAM_PILE - BEAM_LEN / 2, BEAM_PILE + BEAM_LEN / 2, G - 48
        if t < P - 0.3:
            u = seg(t, P - 3.0, P - 0.3)
            m = self.m("digger")
            cx = m.x if m is not None else BEAM_C
            lift = smoothstep(seg(u, 0.0, 0.2)) * (1 - smoothstep(seg(u, 0.82, 1.0)))
            top = lerp(G - 48, BEAM_Y[0], smoothstep(seg(u, 0.8, 1.0))) - 70 * lift
            return "carry", cx - BEAM_LEN / 2, cx + BEAM_LEN / 2, top
        n = sum(1 for i in range(6) if t >= self.cut_t(i) + 0.9)
        if n == 6 and t >= self.cut_t(5) + 1.2:
            return None
        if n == 0:
            R = W_STOP - 150 + 150 * smootherstep(seg(t, P + 0.1, P + 1.2))
        else:
            ci = self.cut_t(n - 1)
            R = W_CUT + (CUBE * smootherstep(seg(t, ci + 1.6, ci + 2.1)) if n < 6 else 0.0)
        return "horses", R - (BEAM_LEN - CUBE * n), R, BEAM_Y[0]

    def cube(self, i, t):
        """Cube i: None (still the beam), or ('fall'|'basket'|'carry'|'in', x, y, angle)."""
        ci = self.cut_t(i)
        if t < ci + 0.9:
            return None
        rest = (BASKET[0] - 30 + 30 * (i % 3), BASKET[1] - 22 - 40 * (i // 3) + (6 if i % 3 == 1 else 0))
        if t < ci + 1.3:                                     # drops off the end into the basket
            u = (t - ci - 0.9) / 0.4
            x = lerp(W_CUT + CUBE / 2, rest[0], u)
            y = lerp((BEAM_Y[0] + BEAM_Y[1]) / 2, rest[1], u * u)
            return "fall", x, y, 0.8 * u
        bx, by = self.basket_pos(t)
        dx, dy = bx - BASKET[0], by - BASKET[1]
        tp = self.pour + 0.25 * i
        if t < tp:
            return "basket", rest[0] + dx, rest[1] + dy, 0.0
        if t < tp + 0.5:                                     # tipped in through the hatch
            u = (t - tp) / 0.5
            hx, hy = self.hatch_xy(t)
            x = lerp(rest[0] + dx, hx, u)
            y = lerp(rest[1] + dy, hy, u) - 4 * 70 * u * (1 - u)
            return "carry", x, y, 3 * u
        return "in", 0.0, 0.0, 0.0

    def basket_pos(self, t):
        """The basket: on the ground under the cut; Hans carries it up to the barrel's hatch and back."""
        hx, hy = BARREL[0] - 40, BARREL[1] - BARREL_R - 110
        keys = [(self.L0, BASKET[0], BASKET[1]), (self.L0 + 2.0, BASKET[0] + 160, G - 330),
                (self.pour - 0.2, hx, hy), (self.pour + 1.9, hx, hy), (self.close + 1.0, 7950.0, G - 330),
                (self.close + 2.4, 7920.0, BASKET[1])]
        return path(keys, t)[:2]

    # ----- the barrel -----

    def rot(self, t):
        a, b = self.tumble
        return self.turns * smootherstep(seg(t, a, b))

    def omega(self, t):
        a, b = self.tumble
        if not (a < t < b):
            return 0.0
        u = (t - a) / (b - a)
        return self.turns * 30 * u * u * (1 - u) * (1 - u) / (b - a)

    def hatch_ang(self, t):
        return HATCH_TOP + self.rot(t)

    def hatch_xy(self, t):
        a = self.hatch_ang(t)
        return BARREL[0] + BARREL_R * math.cos(a), BARREL[1] + BARREL_R * math.sin(a)

    def hatch_open(self, t):
        """0..1: open for loading (top), shut for the tumble, open again at the bottom to let the balls out."""
        u = smoothstep(seg(t, self.L0 + 2.0, self.L0 + 2.6)) * (1 - smoothstep(seg(t, self.close - 0.1, self.close + 0.15)))
        return max(u, smoothstep(seg(t, self.open_t, self.open_t + 0.6)))

    # ----- the new balls -----

    def ball(self, i, t):
        """Ball i (cup i): None while in the barrel, else (x, y, angle, paint 0..1)."""
        t0 = self.out_t[i]
        if t < t0:
            return None
        (cx0, cy0), (cx1, cy1) = CHUTE
        hx, hy = self.hatch_xy(t)
        if t < t0 + 0.25:                                    # out of the hatch onto the chute
            u = (t - t0) / 0.25
            x, y = lerp(hx, cx0, u), lerp(hy, cy0 - M.R0, u)
        else:
            # rolls down the chute, along the tray and stops against the ball before it (real rolling, a = 5/7 g sin)
            tau = t - t0 - 0.25
            Lc = math.hypot(cx1 - cx0, cy1 - cy0)
            ac = 5 / 7 * GRAVITY * (cy1 - cy0) / Lc
            tc = math.sqrt(2 * Lc / ac)
            if tau < tc:
                s = 0.5 * ac * tau * tau
                x, y = lerp(cx0, cx1, s / Lc), lerp(cy0, cy1, s / Lc) - M.R0
            else:
                v0 = ac * tc
                stop = CUP[i + 1]
                d = cx1 - stop
                decel = v0 * v0 / (2 * d) if d > 0 else 1.0
                tt = min(tau - tc, v0 / decel)
                x = cx1 - (v0 * tt - 0.5 * decel * tt * tt)
                y = TRAY_WY - M.R0
        ang = -(cx0 - x) / M.R0
        p = self.paint(i, t)
        if p > 0:
            ang += 4.0 * smoothstep(seg(t, self.paint_t[i], self.paint_t[i] + 2.2))     # Hans turns it
        return x, y, ang, p

    def paint(self, i, t):
        """0..1: ball i takes its colour while Glo's light is at its brightest."""
        return smoothstep(seg(t, self.paint_t[i] + 0.6, self.paint_t[i] + 1.6))

    def magic(self, i, t):
        """0..1: Glo's lantern flares up over ball i for about a second (owner after FK0003: no paint tendril)."""
        p = self.paint_t[i]
        return smoothstep(seg(t, p + 0.2, p + 0.6)) * (1 - smoothstep(seg(t, p + 1.6, p + 2.2)))

    def glo_lamp(self, t):
        """Where Glo's lantern hangs (under her dome)."""
        gl = self.m("lantern")
        return gl.x, gl.y - 178 * gl.k

    # ----- camera -----

    def target(self, t):
        keys = [(0.0, 7700.0, G - 420.0, 0.8), (4.0, 7650.0, G - 380.0, 0.85), (self.P0 + 1.0, 7640.0, G - 300.0, 1.2),
                (self.cut_end, 7680.0, G - 300.0, 1.2), (self.L0 + 2.0, 8200.0, G - 400.0, 0.95),
                (self.close + 2.0, 8500.0, G - 380.0, 0.95), (self.tumble[1] - 1.0, 8650.0, G - 360.0, 1.05),
                (self.open_t + 1.0, 8350.0, G - 300.0, 1.25), (self.paint_t[0], 8200.0, G - 300.0, 1.4),
                (self.done_t, 8200.0, G - 300.0, 1.4), (self.dur, 8250.0, G - 380.0, 1.0)]
        return _ease(keys, t)

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._twigs(t, dt)
        self._wheels(t, dt)
        self._digs(t, dt)
        self._hans(t, dt)
        self._springs(t, dt)
        self._glo(t, dt)
        self._fx(t)
        self.leaves(0.03)
        self._sounds(t)

    def _end(self, kind, x, t, y=None):
        """At the end everyone comes over to the tray to look at the marbles."""
        spots = {"teeth": 7880.0, "digger": 7990.0, "springs": 8440.0, "wheels": 8740.0}
        t0 = self.done_t + 0.3 * KEEPERS.index(kind)
        if kind not in spots or t < t0:
            return x, y
        return path([(t0, x, y if y is not None else G), (t0 + 2.6, spots[kind], G)], t)[:2]

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        rest = BEAM_Y[0] - 70
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        if not m.x:
            m.x = W_CUT + 80
        if t < self.cut_end:
            ty = rest
            for i in range(6):
                ph = t - self.cut_t(i)
                if 0 <= ph < 1.2:
                    if ph < 0.1:
                        ty = lerp(rest, BEAM_Y[0] - 22, ph / 0.1)
                    elif ph < 0.8:
                        ty = lerp(BEAM_Y[0] - 22, BEAM_Y[1] + 24, smoothstep((ph - 0.1) / 0.7))
                    else:
                        ty = lerp(BEAM_Y[1] + 24, rest, smoothstep((ph - 0.8) / 0.4))
                    m.saw_run = smoothstep(seg(ph, 0.0, 0.08)) * (1 - smoothstep(seg(ph, 0.8, 1.0)))
            sx = saw_to(m, t, W_CUT, ty, sx=-1)
            ax = path([(0.0, 7150.0, G), (5.0, W_CUT + 80, G)], t)[0]
            w = smoothstep(seg(t, 4.6, 5.6))
            x = lerp(ax, sx, w)
            m.punch_l *= w
        else:
            x0 = saw_to(m, self.cut_end, W_CUT, rest, sx=-1)
            m.punch_l *= 1 - smoothstep(seg(t, self.cut_end, self.cut_end + 0.8))
            x = path([(self.cut_end, x0, G), (self.cut_end + 3.0, 7700.0, G)], t)[0]
            x, _ = self._end("teeth", x, t)
        m.saw_spin += dt * 38 * m.saw_run
        self.place(m, x, t, dt)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        m.punch = 0.0
        feed = BEAM_C - BEAM_LEN / 2 - 75
        y = None
        if t < self.P0:
            x = path([(0.0, 7000.0, G), (5.4, feed, G)], t)[0]
        elif t < self.cut_end:
            b = self.beam(t)
            x = (b[1] - 75) if b is not None and b[0] == "horses" else W_CUT - 52 - 75
            pushing = any(self.cut_t(i) + 1.5 <= t < self.cut_t(i) + 2.1 for i in range(5)) or \
                self.P0 + 0.1 <= t < self.P0 + 1.2
            m.punch = 0.6 if pushing else 0.0
        else:
            x0 = W_CUT - 52 - 75
            on = self.tumble[0] - 1.6                         # up onto the drive rollers
            keys = [(self.cut_end, x0, G), (on - 1.0, DYNO - 260, G), (on, DYNO, G)]
            x = path(keys, t)[0]
            if t >= on - 1.0:
                y = lerp(G, DYNO_Y + 4, smoothstep(seg(t, on - 0.5, on)))
            if t >= self.tumble[1] + 0.6:                    # down again
                y = lerp(DYNO_Y + 4, G, smoothstep(seg(t, self.tumble[1] + 0.6, self.tumble[1] + 1.1)))
                x = path([(self.tumble[1] + 0.6, DYNO, G), (self.tumble[1] + 1.6, DYNO + 120, G)], t)[0]
                x, y = self._end("wheels", x, t, y)
        self.place(m, x, t, dt, y=y)
        if self.tumble[0] <= t < self.tumble[1]:             # his wheels drive the rollers
            m.wheel_rot += self.omega(t) * BARREL_R / (46 * m.k) * dt * 1.0

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        m.dig = 0.0
        P = self.P0
        keys = [(0.0, 6950.0, G), (P - 4.2, BEAM_PILE - 120, G), (P - 3.0, BEAM_PILE, G), (P - 0.8, BEAM_C, G),
                (P + 0.2, BEAM_C, G), (P + 1.6, 7380.0, G)]
        x = path(keys, t)[0]
        if P - 3.0 <= t < P - 0.3:
            m.dig = -0.2
        x, _ = self._end("digger", x, t)
        self.place(m, x, t, dt)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        keys = [(0.0, 7050.0, G), (5.5, 7900.0, G), (self.L0 - 1.0, 7900.0, G), (self.L0 + 2.0, 8240.0, G),
                (self.close + 2.4, 8240.0, G), (self.open_t - 1.0, 8240.0, G), (self.paint_t[0] - 0.5, 8200.0, G)]
        x = path(keys, t)[0]
        reach = []
        if self.L0 - 0.4 <= t < self.close + 2.4:             # carries the basket by its two handles
            bx, by = self.basket_pos(t)
            reach += [(bx - 40, by - 40), (bx + 40, by - 40)]
        if self.L0 + 2.0 <= t < self.L0 + 2.8 or self.open_t - 0.2 <= t < self.open_t + 0.6:
            reach.append(self.hatch_xy(t))                    # opens the hatch
        for i in range(6):                                    # turns each ball while Glo paints it
            if self.paint_t[i] - 0.3 <= t < self.paint_t[i] + 2.4:
                b = self.ball(i, t)
                if b is not None:
                    reach.append((b[0] + M.R0 * 0.9, b[1] - M.R0 * 0.6))
        self.reach["tentacles"] = reach[:4]
        x, _ = self._end("tentacles", x, t)
        self.place(m, x, t, dt)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        m.spring = 0.0
        x, y = path([(0.0, 7100.0, G), (6.0, 8830.0, G)], t)[:2]
        # up onto the crate, onto the barrel to bounce the hatch shut, back down the same way (every hop real)
        top = (BARREL[0], BARREL[1] - BARREL_R)
        crate = (CRATE[0], CRATE[1])
        hops_ = [Jump(8830.0, G, *crate, apex=40), Jump(*crate, *top, apex=40), Jump(*top, *crate, apex=40),
                 Jump(*crate, 8830.0, G, apex=30)]
        starts = [self.close - hops_[1].dur - 0.3 - hops_[0].dur, self.close - hops_[1].dur, self.close + 0.5,
                  self.close + 0.5 + hops_[2].dur + 0.25]
        for k, (t0, jp) in enumerate(zip(starts, hops_)):
            if t0 <= t < t0 + jp.dur:
                x, y = jp.at(t - t0)
            elif t >= t0 + jp.dur and (k == 3 or t < starts[k + 1]):
                x, y = jp.x1, jp.y1
                m.spring = 0.9 * max(0.0, 1 - (t - t0 - jp.dur) / 0.2)
        if t >= self.paint_t[0]:                             # bounces about while the paint goes on
            x, lift, sq = hops(8830.0, 8440.0, self.paint_t[2], self.paint_t[3], t, apex=40, step=60)
            y = G - lift
            m.spring = sq
        x, y = self._end("springs", x, t, y)
        self.place(m, x, t, dt, y=y)

    def glo_pos(self, t):
        keys = [(0.0, 7250.0, G - 70.0), (6.0, 8100.0, G - 380.0), (self.paint_t[0] - 1.6, 8100.0, G - 380.0)]
        for i in range(6):
            p = self.paint_t[i]
            keys += [(p - 0.3, CUP[i + 1] - 20, G - 330.0), (p + 2.0, CUP[i + 1] - 20, G - 330.0)]
        keys += [(self.done_t + 1.0, 8200.0, G - 420.0)]
        return path(keys, t)[:2]

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        x, y = self.glo_pos(t)
        m.lamp = 1.1 + 1.3 * max(self.magic(i, t) for i in range(6))
        self.place(m, x, t, dt, y=y)

    # ----- effects and sounds -----

    def _fx(self, t):
        p = self.s.particles
        w = self.omega(t)
        if w > 0.5 and p.rng.uniform() < 0.25 * min(1.0, w / 3):    # sawdust puffs out of the vent
            a = self.hatch_ang(t) + math.pi
            p.burst(BARREL[0] + BARREL_R * math.cos(a), BARREL[1] + BARREL_R * math.sin(a), 1,
                    np.array([196, 160, 112]), 50, 1.4, 9, g=-40, spread=1.0)

    def _sounds(self, t):
        if self.crossed(1.5):
            self.chat(t, "lantern", "hey", icon="ball")
        if self.crossed(self.P0 + 0.2):
            self.fx(t, "slide", 1.0, 0.16, W_STOP - 300, BEAM_Y[0])
        if self.crossed(self.P0 + 1.15):
            self.hit(t, "clack", 55, 0.22, W_STOP, BEAM_Y[0])
        if self.crossed(self.P0 - 2.6):
            self.chat(t, "digger", "huff")
        for i in range(6):
            ci = self.cut_t(i)
            if self.crossed(ci + 0.05):
                self.fx(t, "saw", 0.75, 0.18, W_CUT, BEAM_Y[0])
            if self.crossed(ci + 1.3):
                self.hit(t, "clack", self.s.note(i, 0), 0.2, BASKET[0], BASKET[1])
            if i < 5 and self.crossed(ci + 2.05):
                self.hit(t, "clack", 55, 0.18, W_STOP, BEAM_Y[0])
        if self.crossed(self.cut_t(0) + 1.4):
            self.chat(t, "teeth", "hehe")
        if self.crossed(self.cut_t(5) + 1.6):
            self.chat(t, "teeth", "yay")
        if self.crossed(self.L0 + 0.3):
            self.chat(t, "tentacles", "hm")
        for i in range(6):
            if self.crossed(self.pour + 0.25 * i + 0.5):
                self.hit(t, "clunk", 48 + i, 0.16, BARREL[0], BARREL[1])
        if self.crossed(self.close):
            self.hit(t, "boing", 62, 0.3, BARREL[0], BARREL[1] - BARREL_R)
            self.hit(t + 0.05, "clunk", 46, 0.22, BARREL[0], BARREL[1] - BARREL_R)
            self.chat(t + 0.3, "springs", "hehe")
        a, b = self.tumble
        if self.crossed(a - 0.6):
            self.chat(t, "wheels", "hey", icon="!")
        if self.crossed(a):
            self.fx(t, "marble_roll", b - a, 0.12, BARREL[0], BARREL[1])
            self.fx(t + 0.5, "rustle", b - a - 1.0, 0.08, BARREL[0], BARREL[1])
        for k in range(int((b - a) * 7)):                     # the cubes clatter around inside
            tk = a + 0.4 + k / 7.0
            if tk < b - 0.3 and self.crossed(tk):
                v = self.omega(t) / 4.0
                self.hit(t, "clack", self.s.note(k * 3 % 8, -1), 0.05 + 0.08 * min(1.0, v), BARREL[0], BARREL[1])
        if self.crossed(a + 3.0):
            self.chat(t, "wheels", "wee")
        if self.crossed(b - 2.0):
            self.chat(t, "digger", "q")
        if self.crossed(self.open_t + 0.1):
            self.hit(t, "clunk", 50, 0.2, BARREL[0], BARREL[1])
        for i in range(6):
            t0 = self.out_t[i]
            if self.crossed(t0 + 0.2):
                self.hit(t, "clack", self.s.note(i + 2, 0), 0.16, CHUTE[0][0], CHUTE[0][1])
            if self.crossed(t0 + 0.5):
                self.fx(t, "marble_roll", 0.9, 0.08, CHUTE[1][0], TRAY_WY)
        if self.crossed(self.out_t[0] + 0.6):
            self.chat(t, "springs", "ooh")
        if self.crossed(self.out_t[5] + 1.4):
            self.chorus(t, ["teeth", "digger", "tentacles"], "ooh", gap=0.3)
        for i in range(6):
            p = self.paint_t[i]
            if self.crossed(p + 0.6):
                self.hit(t, "chime", self.s.note(i + 2, 0), 0.14, CUP[i + 1], TRAY_WY - 150)
                self.hit(t + 0.12, "chime", self.s.note(i + 4, 0), 0.1, CUP[i + 1], TRAY_WY - 150)
            if self.crossed(p + 2.3):
                kind = M.KINDS[i]
                self.hit(t, "soft_bell", self.s.note(i, 0), 0.18, CUP[i + 1], TRAY_WY)
                self.chat(t + 0.15, kind, "aww" if i % 2 == 0 else "yay", icon="heart" if i % 2 == 0 else "star")
        if self.crossed(self.done_t + 2.2):
            self.chorus(t, ["springs", "digger", "wheels", "tentacles", "teeth", "lantern"], "yay", gap=0.18,
                        icon="star")

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)
        self.forest(c, [(6150, 700), (9100, 720), (9700, 660)])
        if s.visible(M.TREE_B - 800, M.TREE_B + 800):
            M.draw_big_tree(c, s, M.TREE_B, 62)
        wood_sign(c, W_SIGN, G, "MARBLES", 40, 1.0, s.glow_draw)
        for lx in (7540.0, 9080.0):
            M_post_lamp(c, s, lx, t)
        self._saw(c, t)
        self._barrel(c, t)
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t, kinds=["tentacles", "lantern"])     # Hans and Glo work from behind the tray
        self._tray(c, t)
        self.draw_monsters(c, t, kinds=["teeth", "wheels", "digger", "springs"])
        bx, by = self.basket_pos(t)
        for i in range(6):                                   # cubes in the basket or in the air
            cb = self.cube(i, t)
            if cb is not None and cb[0] in ("fall", "basket", "carry"):
                _cube(c, cb[1], cb[2], cb[3])
        _basket(c, bx, by)
        for i in range(6):                                   # Glo's light flares and colours the ball
            g = self.magic(i, t)
            if g > 0 and gl is not None:
                self._magic(c, i, t, g)

    def _magic(self, c, i, t, g):
        """Glo's lantern over ball i: a soft beam down to it, sparkles drifting down it, the ball glowing in its
        new colour."""
        s = self.s
        x, y, _, p = self.ball(i, t)
        lx, ly = self.glo_lamp(t)
        col = np.asarray(M.MARBLE_COLS[M.KINDS[i]], np.float64)
        s.glow_draw(lambda gg: gg.polygon([(lx - 26, ly + 30), (lx + 26, ly + 30), (x + 40, y + 10), (x - 40, y + 10)],
                                          LAMP * 0.10 * g))
        s.glow_draw(lambda gg: gg.circle(x, y, M.R0 + 30 * g, lerp(LAMP, col, p) * 0.55 * g))
        for q in range(9):                                   # sparkles fall from the lantern to the ball
            u = (t * 0.9 + q / 9.0) % 1.0
            sx = lerp(lx, x, u) + 16 * math.sin(7.0 * u + q * 2.1) * (1 - u)
            sy = lerp(ly + 30, y, u)
            tw = 0.6 + 0.4 * math.sin(t * 11 + q * 1.7)
            sc = lerp(LAMP, col, u) * g * tw
            c.circle(sx, sy, 3.5, np.minimum(255, sc * 1.1))
            s.glow_draw(lambda gg, sx=sx, sy=sy, sc=sc: gg.circle(sx, sy, 12, sc * 0.5))

    def _saw(self, c, t):
        for hx in W_HORSES:
            c.line(hx - 34, G, hx - 8, BEAM_Y[1], TRUNK * 0.9, 9)
            c.line(hx + 34, G, hx + 8, BEAM_Y[1], TRUNK * 0.9, 9)
            rect(c, hx - 40, BEAM_Y[1], hx + 40, BEAM_Y[1] + 10, TRUNK)
        rect(c, W_STOP, BEAM_Y[0] - 18, W_STOP + 12, BEAM_Y[1] + 4, IRON * 1.3)
        b = self.beam(t)
        if b is not None:
            st, left, right, top = b
            rect(c, left, top, right, top + CUBE, PLANK * 0.95)
            c.line(left, top, right, top, PLANK * 1.2, 2)
            if st == "horses":
                for q in range(1, 7):                        # pencil marks every cube length
                    mx = right - q * CUBE
                    if mx > left + 4:
                        c.line(mx, top - 4, mx, top + 8, np.array([40, 34, 30]), 2)
        n = sum(1 for i in range(6) if t >= self.cut_t(i) + 0.9)
        if n:
            c.polygon(ellipse(W_CUT + 10, G, 30 + 4 * n, 6 + 1.2 * n, 20, math.pi, 2 * math.pi),
                      np.array([196, 160, 112]))
        if t >= self.cut_t(5) + 1.2:                          # the offcut under the horses
            u = min(1.0, (t - self.cut_t(5) - 1.2) / 0.32)
            ox, oy = W_CUT - 22 - 30 * u, lerp(BEAM_Y[0] + 24, G - 22, u * u)
            rect(c, ox - 22, oy - 22, ox + 22, oy + 22, PLANK * 0.85)

    def _barrel(self, c, t):
        """The tumbler barrel seen end-on (its staves turn with it) on two rollers, belt to Wheels' drive rollers."""
        x, y = BARREL
        rot = self.rot(t)
        roll = -rot * BARREL_R / ROLLER_R
        for lx in (ROLLERS[0] - 40, ROLLERS[1] + 40):           # the stand
            c.line(lx, ROLLER_Y + 10, lx + (-30 if lx < x else 30), G, TRUNK * 0.9, 12)
        rect(c, ROLLERS[0] - 50, ROLLER_Y + 4, ROLLERS[1] + 50, ROLLER_Y + 22, TRUNK)
        rect(c, CRATE[0] - 60, CRATE[1], CRATE[0] + 60, G, PLANK * 0.8)       # Springs' crate
        c.polyline([(CRATE[0] - 60, CRATE[1]), (CRATE[0] + 60, G), (CRATE[0] + 60, CRATE[1]), (CRATE[0] - 60, G)],
                   PLANK * 0.6, 3)
        for rx in ROLLERS:
            PR.pulley(c, rx, ROLLER_Y, ROLLER_R, roll)
        for dx in (-34, 34):
            PR.pulley(c, DYNO + dx, DYNO_Y, 22, roll * ROLLER_R / 22)
        rect(c, DYNO - 70, G - 10, DYNO + 70, G, IRON * 0.8)
        PR.belt(c, (ROLLERS[1], ROLLER_Y), 12, (DYNO - 34, DYNO_Y), 10, -rot * BARREL_R)
        c.circle(x, y, BARREL_R, PLANK * 0.75)
        for k in range(12):                                   # staves
            a = rot + k * math.pi / 6
            c.line(x + math.cos(a) * 30, y + math.sin(a) * 30, x + math.cos(a) * (BARREL_R - 4),
                   y + math.sin(a) * (BARREL_R - 4), PLANK * 0.6, 3)
        c.circle(x, y, BARREL_R, IRON * 0.9, False, 9)        # iron hoop
        c.circle(x, y, 30, PLANK * 0.6)
        c.circle(x, y, 10, IRON)
        a = self.hatch_ang(t)                                 # the hatch on the rim: a dark opening when open
        hx, hy = x + math.cos(a) * (BARREL_R - 26), y + math.sin(a) * (BARREL_R - 26)
        o = self.hatch_open(t)
        ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        pts = [(hx + ca * 30 + math.cos(a) * 20, hy + sa * 30 + math.sin(a) * 20),
               (hx - ca * 30 + math.cos(a) * 20, hy - sa * 30 + math.sin(a) * 20),
               (hx - ca * 30 - math.cos(a) * 20, hy - sa * 30 - math.sin(a) * 20),
               (hx + ca * 30 - math.cos(a) * 20, hy + sa * 30 - math.sin(a) * 20)]
        c.polygon(pts, lerp(PLANK * 0.95, np.array([28, 20, 16]), o))
        c.polyline(pts, IRON, 3, closed=True)

    def _tray(self, c, t):
        (cx0, cy0), (cx1, cy1) = CHUTE
        c.line(cx0, cy0 + 4, cx1, cy1 + 4, PLANK * 0.9, 12)
        rect(c, TRAY_W[0], TRAY_WY, TRAY_W[1], TRAY_WY + 18, PLANK * 0.9)
        rect(c, TRAY_W[0] - 8, TRAY_WY - 30, TRAY_W[0], TRAY_WY + 18, PLANK * 0.8)
        for lx in (TRAY_W[0] + 20, TRAY_W[1] - 20):
            rect(c, lx - 7, TRAY_WY + 18, lx + 7, G + 4, TRUNK * 0.9)
        M.draw_marble(c, CUP[0], TRAY_WY - BALL_R, BALL_R, 0.3, M.PLAIN)       # Wheels' ball waits in the first cup
        for i in range(6):
            b = self.ball(i, t)
            if b is None:
                continue
            x, y, ang, p = b
            col = lerp(M.PLAIN, np.asarray(M.MARBLE_COLS[M.KINDS[i]], np.float64), p)
            M.draw_marble(c, x, y, M.R0, ang, col)


def M_post_lamp(c, s, x, t):
    """A lantern on a post lighting the workshop."""
    rect(c, x - 8, G - 300, x + 8, G + 4, TRUNK * 0.9)
    c.line(x, G - 300, x + 36, G - 300, TRUNK * 0.9, 6)
    sway = 0.06 * math.sin(t * 1.2 + x)
    lx = x + 36 + 20 * sway
    c.polygon([(lx - 12, G - 290), (lx + 12, G - 290), (lx + 14, G - 258), (lx - 14, G - 258)],
              np.array([50, 50, 46]) + LAMP * 0.85)
    s.glow_draw(lambda g: g.circle(lx, G - 274, 90, LAMP * 0.5))


def _cube(c, x, y, ang):
    h = CUBE / 2
    pts = [(x + math.cos(ang + k * math.pi / 2 + math.pi / 4) * h * 1.414,
            y + math.sin(ang + k * math.pi / 2 + math.pi / 4) * h * 1.414) for k in range(4)]
    c.polygon(pts, PLANK * 1.02)
    c.polyline(pts, PLANK * 0.7, 2, closed=True)


def _basket(c, x, y):
    """A woven basket, (x, y) = the middle of its bottom."""
    c.polygon([(x - 62, y - 70), (x + 62, y - 70), (x + 50, y), (x - 50, y)], np.array([150, 116, 70]))
    for k in range(4):
        yy = y - 14 - 16 * k
        c.line(x - 52 - 3 * k, yy, x + 52 + 3 * k, yy, np.array([118, 88, 52]), 3)
    c.arc(x, y - 70, 50, 180, 360, np.array([118, 88, 52]), 5)


# ====================================================================== RUN (building it between the trees)

STUBS_A = [(M.TREE_A - 128 - (14 if i % 2 else -6) + 3.0 * i, G - 150.0 * (i + 1)) for i in range(10)]
HORSES_R = (5520.0, 6380.0)            # the boards wait stacked on two long sawhorses under the run
HORSE_TOP = G - 110.0
STACK_CX = (M.LEFT_X[0] + M.LEFT_X[1]) / 2
EXTRA = 60.0                           # every board comes 60 long: Twigs trims it at the line, the stop block sets it
RUN_STOP = M.LEFT_X[1] + 4             # stop block at the right end of the horses
BOX_DY0 = 320.0                        # the peg panel is built standing on the ground, 320 lower than its place
HANS_HOIST = 6260.0
FIN_SPOTS = {"wheels": 4060.0, "digger": 4140.0, "tentacles": 4215.0, "teeth": 4285.0, "springs": 3580.0}


class RunAct(MarbleAct):
    """Building the run: pegs, string line, boards hoisted top first, stops, peg forest, tunnel, last ramp, lights,
    then the test run with Wheels' plain ball."""
    name = "run"
    names = (-2.0, -1.0)

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self._plan_springs()
        # Glo checks each board's two pegs with a string line as soon as both are in (top board first); she starts
        # each one from the side where the last one ended, so the line goes A->B, B->A, ...
        self.check_t, t = {}, 0.0
        for k in range(M.N_BOARDS):
            t = max(t, self.drive_t[("B", k)] + 0.3)
            self.check_t[k] = t
            t += 3.8
        # boards: pushed to the stop, trimmed, tied, hoisted (top board first, so a rising board never passes one
        # already in place); Glo puts the stop in at the low end of each one
        self.cyc = 8.0
        self.board_t = {}
        t = self.check_t[0] + 2.0
        for k in range(M.N_BOARDS):
            t = max(t, self.check_t[k] + 2.0)
            self.board_t[k] = t
            t += self.cyc
        self.boards_done = t
        # Glo fits a stop at the low end of each board once her string-line checks are done: fetch it from beside
        # the horses, fly it up, fit it, fly back down for the next
        self.stop_t, t = {}, self.check_t[M.N_BOARDS - 1] + 2.8 + 2.4
        for i in range(M.N_BOARDS - 1):
            t = max(t, self.board_t[i] + 7.2)
            self.stop_t[i] = t
            t += 4.4
        self.dig = (6.0, 30.0)
        self.panel_lift = self.boards_done + 2.5
        f0 = max(self.panel_lift + 3.5, t)
        self.final = (f0, f0 + 5.0)
        # Glo lights the finish lantern; a spark runs from it up the whole run and lights every turn on its way
        self.finish_light = self.final[1] + 3.5
        self.spark_pts, catch = M.spark_path()
        seglen = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(self.spark_pts, self.spark_pts[1:])]
        self.spark_s = np.concatenate([[0.0], np.cumsum(seglen)])
        self.spark_v = 2400.0
        self.spark0 = self.finish_light + 0.4
        self.light_t = [self.spark0 + self.spark_s[catch[i]] / self.spark_v for i in range(len(M.turn_lights()))]
        self.spark1 = self.spark0 + self.spark_s[-1] / self.spark_v
        self.ball_pick = self.spark1 + 1.2
        self.ball_up = self.ball_pick + 1.2
        self.release = self.ball_up + 7.5
        self.test = M.Run(M.Trait(BALL_R, 0.4, 0.04), 50.0)
        self.test_fin = self.release + (self.test.finish_t or self.test.dur)
        self.dur = self.test_fin + 9.0
        self.stats = {"string_line_checks": M.N_BOARDS, "test_run_s": round(self.test.finish_t or -1.0, 2)}

    # ----- Springs' route: up the stubs, a hop out to every peg spot (the bounce drives the peg), back -----

    def _plan_springs(self):
        moves = []                                   # (t0, Jump)
        self.drive_t = {}
        t = 4.0
        pos = (M.TREE_A - 330.0, G)

        def hop(a, b, apex=40.0, pause=0.12):
            nonlocal t, pos
            jp = Jump(a[0], a[1], b[0], b[1], apex=apex)
            moves.append((t, jp))
            t += jp.dur + pause
            pos = b

        spots = M.peg_spots()
        for side, stubs, ground in (("A", STUBS_A, (M.TREE_A - 330.0, G)), ("B", STUBS, (M.TREE_B + 290.0, G))):
            if pos != ground:                        # along the ground to the next trunk
                n = max(1, int(abs(ground[0] - pos[0]) / 170))
                x0 = pos[0]
                for i in range(n):
                    hop(pos, (lerp(x0, ground[0], (i + 1) / n), G), apex=50, pause=0.04)
            for s in stubs:                          # up to the top stub
                hop(pos, (s[0], s[1] - 6))
            j = len(stubs) - 1
            for k in range(M.N_BOARDS):              # top board first: down the stubs, out to each peg, back
                px, py = spots[2 * k] if side == "A" else spots[2 * k + 1]
                while j > 0 and stubs[j - 1][1] - 6 < G and stubs[j][1] < py - 150:
                    j -= 1
                    hop(pos, (stubs[j][0], stubs[j][1] - 6))
                while j > 0 and stubs[j][1] < py:
                    j -= 1
                    hop(pos, (stubs[j][0], stubs[j][1] - 6))
                back = pos
                hop(pos, (px, py - 8), pause=0.0)
                self.drive_t[(side, k)] = t
                t += 0.4
                hop(pos, back)
            while j > 0:                             # and down again
                j -= 1
                hop(pos, (stubs[j][0], stubs[j][1] - 6))
            hop(pos, (pos[0] + (60 if side == "B" else -60), G))
        # then the peg panel, standing on the ground in front of TREE_A: a bounce on each spot drives a peg, bottom
        # row first
        ps = M.pegs()
        rows = {}
        for i, (x, y) in enumerate(ps):
            rows.setdefault(y, []).append(i)
        order = []
        for r, y in enumerate(sorted(rows, reverse=True)):
            idx = sorted(rows[y], key=lambda i: ps[i][0], reverse=r % 2 == 1)
            order += idx
        self.panel_order = order
        self.panel_t = {}
        n = max(1, int(abs(M.BOX[0] - 40 - pos[0]) / 170))
        x0 = pos[0]
        for i in range(n):
            hop(pos, (lerp(x0, M.BOX[0] - 40, (i + 1) / n), G), apex=50, pause=0.04)
        t = max(t, 0.0)
        for i in order:
            x, y = ps[i]
            hop(pos, (x, y + BOX_DY0 - 8), apex=30, pause=0.0)
            self.panel_t[i] = t
            t += 0.22
        hop(pos, (M.BOX[1] + 60, G), apex=30)
        self.springs_moves = moves
        self.springs_free = t

    # ----- what is built when -----

    def trunk_pegs(self, t):
        """Set of peg spot indices (2k = A end of board k, 2k + 1 = B end) that are in."""
        out = set()
        for (side, k), td in self.drive_t.items():
            if t >= td:
                out.add(2 * k + (0 if side == "A" else 1))
        return out

    def board_pose(self, k, t):
        """None (not yet off the stack ... drawn by the stack), or (dx, dy, ang) of board k relative to its place."""
        c0 = self.board_t[k]
        (x0, y0), (x1, y1), _ = M.board(k)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        a = M.board_ang(k)
        s = 4 - k                                         # its place in the stack (the top board is board 0)
        sy = HORSE_TOP - M.BOARD_T * (s + 1)
        push = -150.0 * (1 - smootherstep(seg(t, c0 + 0.2, c0 + 1.2)))
        if t < c0 + 3.2:
            return (STACK_CX + push - cx, sy - cy, -a)
        u = seg(t, c0 + 3.2, c0 + 7.0)
        px = lerp(STACK_CX, cx, smootherstep(u))
        py = lerp(sy, cy, smootherstep(u))
        ang = lerp(-a, 0.0, smoothstep(seg(u, 0.7, 1.0)))
        return (px - cx, py - cy, ang)

    def board_placed(self, k, t):
        return t >= self.board_t[k] + 7.0

    def offcut(self, k, t):
        """The 60 Twigs trims off board k: (x0, x1, y) of its top while on the board, or falling, or None."""
        c0 = self.board_t[k]
        s = 4 - k
        sy = HORSE_TOP - M.BOARD_T * (s + 1)
        push = -150.0 * (1 - smootherstep(seg(t, c0 + 0.2, c0 + 1.2)))
        x1 = M.LEFT_X[0] + push
        if t < c0 + 2.4:
            return x1 - EXTRA, x1, sy
        u = min(1.0, (t - c0 - 2.4) / 0.35)
        if u < 1:
            return x1 - EXTRA - 20 * u, x1 - 20 * u, lerp(sy, G - 20, u * u)
        return x1 - EXTRA - 20, x1 - 20, G - 20 - 2 * k        # in the little pile of offcuts

    def stop_state(self, i, t):
        """Stop i: None before Glo fetches it, (dx, dy) offset while she carries it, (0, 0) once in."""
        tp = self.stop_t[i]
        x, y0, y1 = M.stops()[i]
        if t < tp:
            return None
        if t < tp + 1.4:
            gl = self.m("lantern")
            u = smootherstep(seg(t, tp, tp + 1.4))
            hx, hy = (gl.x, gl.y - 60) if gl is not None else (x, y0)
            return (lerp(hx - x, 0.0, u), lerp(hy - y0, 0.0, u))
        return (0.0, 0.0)

    def stops_in(self, t):
        return sum(1 for i in range(M.N_BOARDS - 1) if t >= self.stop_t[i] + 1.4)

    def box_dy(self, t):
        return BOX_DY0 * (1 - smootherstep(seg(t, self.panel_lift, self.panel_lift + 2.8)))

    def box_pegs(self, t):
        return sum(1 for i in self.panel_order if t >= self.panel_t[i])

    def lights(self, t):
        return [smoothstep(seg(t, lt, lt + 0.3)) for lt in self.light_t]

    def course_state(self, t):
        boards = {}
        for k in range(M.N_BOARDS):
            boards[k] = (0.0, 0.0, 0.0) if self.board_placed(k, t) else self.board_pose(k, t)
        return dict(pegs=0, boards=boards, stops=self.stops_in(t), box=(self.box_pegs(t), 1.0, self.box_dy(t)),
                    final=smootherstep(seg(t, *self.final)), dug=seg(t, *self.dig), lights=self.lights(t),
                    finish=smoothstep(seg(t, self.finish_light, self.finish_light + 0.4)),
                    gate=seg(t, self.release - 0.1, self.release + 0.25), platform=True, pulley=self.rope(t))

    def rope(self, t):
        """The hoist rope's two ends: [board end, Hans' end] while a board is on it, else hanging slack."""
        m = self.m("tentacles")
        hx, hy = (m.x + 10, m.y - 330) if m is not None else (HANS_HOIST, G - 330)
        # Hans holds his end from the first hoist to the last; before and after it hangs from the pulley
        hold = smoothstep(seg(t, self.board_t[0] + 1.8, self.board_t[0] + 2.6)) * \
            (1 - smoothstep(seg(t, self.boards_done - self.cyc + 7.6, self.boards_done - self.cyc + 8.4)))
        hang = (M.PULLEY[0] + 22, M.PULLEY[1] + 260)
        hx, hy = lerp(hang[0], hx, hold), lerp(hang[1], hy, hold)
        for k in range(M.N_BOARDS):
            c0 = self.board_t[k]
            if c0 + 2.6 <= t < c0 + 7.6:
                pose = self.board_pose(k, t) if not self.board_placed(k, t) else (0.0, 0.0, 0.0)
                a, b = M.board_pts(k, *pose)
                bx, by = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - M.FACE * 0.4
                if t < c0 + 3.2:                          # the rope comes down to the board
                    u = smoothstep(seg(t, c0 + 2.6, c0 + 3.2))
                    bx, by = lerp(M.PULLEY[0] - 22, bx, u), lerp(M.PULLEY[1] + 200, by, u)
                if t >= c0 + 7.0:                         # untied, pulled back up a little
                    u = smoothstep(seg(t, c0 + 7.0, c0 + 7.6))
                    by = lerp(by, M.PULLEY[1] + 200, u)
                return [(bx, by), (hx, hy)]
        return [(M.PULLEY[0] - 22, M.PULLEY[1] + 200), (hx, hy)]

    # ----- camera -----

    def target(self, t):
        keys = [(0.0, 5600.0, G - 900.0, 0.55), (3.5, 5600.0, G - 900.0, 0.55)]
        sp = self.springs_moves
        for (t0, jp) in sp[::3]:                          # follow Springs up and down the trunks
            if t0 > self.drive_t[("B", M.N_BOARDS - 1)] + 2.0:
                break
            keys.append((t0 + 0.4, lerp(jp.x0, 5900.0, 0.45), min(G - 420.0, jp.y0 - 120), 0.85))
        keys.sort(key=lambda q: q[0])
        keys = [q for q in keys if q[0] < self.board_t[0] - 1.0]
        for k in range(M.N_BOARDS):
            c0 = self.board_t[k]
            (x0, y0), (x1, y1), _ = M.board(k)
            keys += [(c0 + 0.2, 5600.0, G - 320.0, 0.9), (c0 + 2.8, 5600.0, G - 330.0, 0.9),
                     (c0 + 6.5, 5950.0, min(G - 420.0, (y0 + y1) / 2 + 160), 0.7)]
        keys += [(self.panel_lift - 0.5, 5000.0, G - 420.0, 0.95), (self.final[0], 5000.0, G - 420.0, 0.95),
                 (self.final[1], 4500.0, G - 380.0, 0.75), (self.finish_light, 4300.0, G - 420.0, 0.75),
                 (self.spark0 + 0.6, 5300.0, G - 860.0, 0.52),
                 (self.ball_up, 5300.0, G - 860.0, 0.52), (self.release - 1.5, 6500.0, G - 1640.0, 1.15)]
        keys.sort(key=lambda q: q[0])
        if t < self.release - 1.5:
            return _ease(keys, t)
        tau = t - self.release
        x, y, _, _, _ = self.test.at(max(0.0, tau))
        if t > self.test_fin + 1.0:
            u = smoothstep(seg(t, self.test_fin + 1.0, self.test_fin + 3.0))
            return lerp(3950.0, 3800.0, u), G - 330.0, 1.0
        if y < M.BOX_TOP - 20:
            return min(6350.0, max(5450.0, x)), y - 50, 1.3
        if x > M.BOX[0] - 40:
            return 5080.0, y - 30, 1.35
        return max(3950.0, x - 220), min(G - 300, y - 110), 1.25

    def aside_moods(self, t):
        return ["hehe", "mm", "ooh", "hm", "huff"]

    # ----- the Keepers -----

    def update(self, t, dt):
        self.reach = {}
        self._springs(t, dt)
        self._glo(t, dt)
        self._hans(t, dt)
        self._wheels(t, dt)
        self._twigs(t, dt)
        self._digs(t, dt)
        self._fx(t)
        self.leaves(0.04)
        self._sounds(t)

    def _to_finish(self, kind, x, t, y=None):
        """Once the run is built, everyone goes down to the finish to watch the test."""
        t0 = self.final[1] + 0.4 * KEEPERS.index(kind)
        if kind not in FIN_SPOTS or t < t0:
            return x, y
        d = abs(FIN_SPOTS[kind] - x)
        return path([(t0, x, y if y is not None else G), (t0 + max(3.0, d / 380.0), FIN_SPOTS[kind], G)], t)[:2]

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        m.spring = 0.0
        x, y = self.springs_moves[0][1].x0, self.springs_moves[0][1].y0
        for i, (t0, jp) in enumerate(self.springs_moves):
            nxt = self.springs_moves[i + 1][0] if i + 1 < len(self.springs_moves) else 1e9
            if t0 <= t < t0 + jp.dur:
                x, y = jp.at(t - t0)
            elif t0 + jp.dur <= t < nxt:
                x, y = jp.x1, jp.y1
                m.spring = 0.85 * max(0.0, 1 - (t - t0 - jp.dur) / 0.16)
        if t < self.springs_moves[0][0]:
            x, y = self.springs_moves[0][1].x0, self.springs_moves[0][1].y0
        if t >= self.springs_free:
            x, y = self._to_finish("springs", x, t, y)
        self.place(m, x, t, dt, y=y)

    def glo_pos(self, t):
        keys = [(0.0, 5600.0, G - 300.0), (2.0, 5600.0, G - 300.0)]
        for k in range(M.N_BOARDS):                       # the string line, across and back
            ct = self.check_t[k]
            a, b = self.check_ends(k)
            keys += [(ct - 0.1, a[0], a[1] + 60), (ct + 2.0, b[0], b[1] + 60), (ct + 2.8, b[0], b[1] + 60)]
        for i in range(M.N_BOARDS - 1):                    # then a stop for each board
            tp = self.stop_t[i]
            x, y0, y1 = M.stops()[i]
            keys += [(tp - 0.6, 5800.0, G - 250.0), (tp, 5800.0, G - 250.0), (tp + 1.4, x + 70, y0 + 40),
                     (tp + 1.9, x + 70, y0 + 40)]
        keys += [(self.final[0] + 1.0, 4700.0, G - 600.0), (self.finish_light - 0.4, M.FINISH_X + 90, G - 330.0),
                 (self.spark1, M.FINISH_X + 90, G - 330.0)]
        wh = FIN_SPOTS["wheels"]
        keys += [(self.ball_pick, wh + 20, G - 420.0), (self.ball_up, wh + 20, G - 420.0),
                 (self.release - 1.6, M.PLATFORM[0] + 60, M.PLATFORM[2] - 180),
                 (self.release + 2.0, M.PLATFORM[0] + 60, M.PLATFORM[2] - 180),
                 (self.test_fin + 1.5, 3820.0, G - 430.0)]
        keys.sort(key=lambda q: q[0])
        return path(keys, t)[:2]

    def check_ends(self, k):
        """Where Glo's string line for board k starts and ends: A->B on even boards, B->A on odd ones."""
        spots = M.peg_spots()
        (ax, ay), (bx, by) = spots[2 * k], spots[2 * k + 1]
        a, b = (ax + 20, ay), (bx - 20, by)
        return (a, b) if k % 2 == 0 else (b, a)

    def spark(self, t):
        """The spark running up the run, or None."""
        if not (self.spark0 <= t < self.spark1):
            return None
        s = (t - self.spark0) * self.spark_v
        i = int(np.searchsorted(self.spark_s, s, side="right")) - 1
        i = min(i, len(self.spark_pts) - 2)
        u = (s - self.spark_s[i]) / max(1e-6, self.spark_s[i + 1] - self.spark_s[i])
        (x0, y0), (x1, y1) = self.spark_pts[i], self.spark_pts[i + 1]
        return lerp(x0, x1, u), lerp(y0, y1, u)

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        x, y = self.glo_pos(t)
        m.lamp = 1.1 + 0.9 * math.exp(-((t - self.finish_light - 0.1) / 0.3) ** 2)
        self.place(m, x, t, dt, y=y)

    def _hans(self, t, dt):
        m = self.m("tentacles")
        if m is None:
            return
        keys = [(0.0, 6600.0, G), (self.board_t[0] - 1.5, HANS_HOIST, G)]
        keys += [(self.boards_done, HANS_HOIST, G), (self.panel_lift - 0.3, M.BOX[1] + 160, G),
                 (self.panel_lift + 3.0, M.BOX[1] + 160, G), (self.final[0] + 0.2, M.FIN0[0] - 120, G),
                 (self.final[1], M.FIN1[0] + 260, G)]
        x = path(keys, t)[0]
        reach = []
        for k in range(M.N_BOARDS):
            c0 = self.board_t[k]
            if c0 + 2.6 <= t < c0 + 7.2:                  # hand over hand on the rope
                (rx0, ry0), (rx1, ry1) = self.rope(t)[1], (M.PULLEY[0] + 22, M.PULLEY[1])
                for j in range(2):
                    ph = ((t - c0) * 1.6 + 0.5 * j) % 1.0
                    reach.append((lerp(rx0, rx1, 0.06 + 0.12 * ph), lerp(ry0, ry1, 0.06 + 0.12 * ph)))
        if self.panel_lift - 0.2 <= t < self.panel_lift + 3.0:     # lifts the peg panel up onto TREE_A
            dy = self.box_dy(t)
            reach += [(M.BOX[0] + 10, M.BOX_TOP + 120 + dy), (M.BOX[1] - 10, M.BOX_TOP + 120 + dy)]
        if self.final[0] <= t < self.final[1] + 0.3:              # lays the last ramp down to the tray
            u = smootherstep(seg(t, *self.final))
            xe = lerp(M.FIN0[0], M.FIN1[0], u)
            reach += [(xe + 30, M.fin_y(xe) - 20), (xe + 260, M.fin_y(xe + 230) - 20)]
        self.reach["tentacles"] = reach[:4]
        x, _ = self._to_finish("tentacles", x, t)
        self.place(m, x, t, dt)

    def _wheels(self, t, dt):
        m = self.m("wheels")
        if m is None:
            return
        m.punch = 0.0
        keys = [(0.0, 4500.0, G), (self.board_t[0] - 1.2, M.LEFT_X[0] - EXTRA - 150 - 75, G)]
        for k in range(M.N_BOARDS):
            c0 = self.board_t[k]
            left = M.LEFT_X[0] - EXTRA - 75
            keys += [(c0 + 0.2, left - 150, G), (c0 + 1.2, left, G), (c0 + 2.0, left - 60, G),
                     (c0 + self.cyc - 1.0, left - 150, G)]
            if c0 + 0.2 <= t < c0 + 1.3:
                m.punch = 0.6
        x = path(sorted(keys), t)[0]
        x, _ = self._to_finish("wheels", x, t)
        self.place(m, x, t, dt)

    def _twigs(self, t, dt):
        m = self.m("teeth")
        if m is None:
            return
        m.saw_run = 0.0
        m.punch = m.punch_l = 0.0
        if not m.x:
            m.x = 5400.0
        rest = 5400.0
        x = path([(0.0, 5000.0, G), (5.0, rest, G)], t)[0]
        for k in range(M.N_BOARDS):
            c0 = self.board_t[k]
            if c0 + 1.0 <= t < c0 + 2.8:                  # trims the end at the line
                s = 4 - k
                sy = HORSE_TOP - M.BOARD_T * (s + 1)
                ph = t - c0 - 1.4
                top, bot = sy - 22, sy + M.BOARD_T + 22
                if ph < 0:
                    ty = top - 40
                elif ph < 0.9:
                    ty = lerp(top, bot, smoothstep(ph / 0.9))
                else:
                    ty = lerp(bot, top - 40, smoothstep((ph - 0.9) / 0.4))
                m.saw_run = smoothstep(seg(ph, 0.0, 0.08)) * (1 - smoothstep(seg(ph, 0.9, 1.1)))
                sx = saw_to(m, t, M.LEFT_X[0], ty, sx=-1)
                w = smoothstep(seg(t, c0 + 1.0, c0 + 1.3)) * (1 - smoothstep(seg(t, c0 + 2.5, c0 + 2.8)))
                x = lerp(rest, sx, w)
                m.punch_l *= w
        m.saw_spin += dt * 38 * m.saw_run
        x, _ = self._to_finish("teeth", x, t)
        self.place(m, x, t, dt)

    def _digs(self, t, dt):
        m = self.m("digger")
        if m is None:
            return
        m.dig = 0.0
        xin, xout = M.tunnel_span()
        a, b = self.dig
        mid = (a + b) / 2
        keys = [(0.0, 4900.0, G), (a - 0.5, xin + 120, G), (mid - 1.0, xin + 120, G), (mid + 1.5, xout - 140, G),
                (b, xout - 140, G), (b + 3.0, 4750.0, G)]
        x = path(keys, t)[0]
        if a <= t < mid - 1.0 or mid + 1.5 <= t < b:
            m.dig = 0.5 + 0.5 * math.sin(t * 7)
        x, _ = self._to_finish("digger", x, t)
        self.place(m, x, t, dt)

    # ----- effects and sounds -----

    def _fx(self, t):
        p = self.s.particles
        a, b = self.dig
        mid = (a + b) / 2
        xin, xout = M.tunnel_span()
        for (t0, t1, px, d) in ((a, mid - 1.0, xin, 1), (mid + 1.5, b, xout, -1)):
            if t0 <= t < t1 and p.rng.uniform() < 0.45:
                p.burst(px + 30 * d, M.fin_y(px) - 20, 2, M.EARTH * 1.3, 380, 0.8, 8, g=1500, spread=0.6,
                        direction=-math.pi / 2 + 0.7 * d)
        for k in range(M.N_BOARDS):                       # sawdust at each trim
            c0 = self.board_t[k]
            if c0 + 1.4 <= t < c0 + 2.3 and p.rng.uniform() < 0.5:
                p.burst(M.LEFT_X[0], HORSE_TOP - M.BOARD_T * (5 - k), 1, np.array([196, 160, 112]), 120, 0.6, 4,
                        g=900, spread=0.8)

    def _sounds(self, t):
        if self.crossed(1.2):
            self.chat(t, "springs", "hey", icon="run")
        if self.crossed(2.4):
            self.chorus(t, ["wheels", "digger"], "yay", gap=0.3)
        for i, (t0, jp) in enumerate(self.springs_moves):
            if self.crossed(t0):
                self.hit(t, "boing", 60 + (i % 6), 0.1, jp.x0, jp.y0)
        for (side, k), td in self.drive_t.items():
            if self.crossed(td):
                x, y = M.peg_spots()[2 * k + (0 if side == "A" else 1)]
                self.hit(t, "clunk", 50 + k, 0.24, x, y)
        for i, tp in self.panel_t.items():
            if self.crossed(tp):
                x, y = M.pegs()[i]
                self.hit(t, "clack", self.s.note(i, 0), 0.14, x, y + BOX_DY0)
        if self.crossed(self.drive_t[("A", 0)] + 0.5):
            self.chat(t, "springs", "wee")
        for k in range(M.N_BOARDS):
            ct = self.check_t[k]
            if self.crossed(ct + 2.0):
                self.hit(t, "soft_bell", self.s.note(k + 2, 0), 0.18, M.peg_spots()[2 * k + 1][0], M.peg_spots()[2 * k + 1][1])
            if k == 0 and self.crossed(ct + 2.3):
                self.chat(t, "lantern", "mm")
            c0 = self.board_t[k]
            if self.crossed(c0 + 0.25):
                self.fx(t, "slide", 1.0, 0.14, STACK_CX, HORSE_TOP)
            if self.crossed(c0 + 1.2):
                self.hit(t, "clack", 55, 0.2, RUN_STOP, HORSE_TOP)
            if self.crossed(c0 + 1.45):
                self.fx(t, "saw", 0.8, 0.16, M.LEFT_X[0], HORSE_TOP)
            if self.crossed(c0 + 2.75):
                self.hit(t, "thud", 50, 0.12, M.LEFT_X[0], G)
            if self.crossed(c0 + 3.3):
                self.fx(t, "creak", 3.6, 0.14, M.PULLEY[0], M.PULLEY[1])
                if k == 0:
                    self.chat(t + 0.4, "tentacles", "huff")
            if self.crossed(c0 + 7.0):
                (x0, y0), (x1, y1), _ = M.board(k)
                self.hit(t, "clunk", 48 + k, 0.24, (x0 + x1) / 2, (y0 + y1) / 2)
                if k == M.N_BOARDS - 1:
                    self.chat(t + 0.4, "tentacles", "yay")
            if k < M.N_BOARDS - 1 and self.crossed(self.stop_t[k] + 1.4):
                x, y0, y1 = M.stops()[k]
                self.hit(t, "clack", self.s.note(k, 0), 0.18, x, y0)
        if self.crossed(self.dig[0] + 0.5):
            self.chat(t, "digger", "hey")
            self.fx(t + 0.3, "rustle", self.dig[1] - self.dig[0] - 1.0, 0.1, M.MOUND[0] + 300, G - 200)
        if self.crossed(self.dig[1] - 0.5):
            self.chat(t, "digger", "yay")
        if self.crossed(self.panel_lift + 2.8):
            self.hit(t, "clunk", 46, 0.24, M.TREE_A, M.BOX_TOP)
        if self.crossed(self.final[1]):
            self.hit(t, "clunk", 52, 0.22, M.FIN1[0], M.FIN1[1])
        if self.crossed(self.finish_light):
            self.hit(t, "bloop", 72, 0.24, M.FINISH_X, G - 300)
            self.chat(t + 0.3, "lantern", "ooh")
        if self.crossed(self.spark0):
            self.fx(t, "whoosh", self.spark1 - self.spark0, 0.12, M.FIN0[0], M.FIN0[1])
        for i, lt in enumerate(self.light_t):
            if self.crossed(lt):
                lx, ly = M.turn_lights()[i]
                self.hit(t, "chime", self.s.note(i, 1), 0.14, lx, ly)
        if self.crossed(self.spark1 + 0.3):
            self.chorus(t, ["springs", "digger", "teeth"], "ooh", gap=0.3)
        if self.crossed(self.ball_pick + 0.2):
            self.chat(t, "wheels", "hey", icon="ball")
        if self.crossed(self.release - 0.8):
            self.chat(t, "lantern", "hey", icon="!")
        if self.crossed(self.release):
            self.hit(t, "clunk", 50, 0.3, M.GATE_X, M.board_y(0, M.GATE_X))
        tau0, tau1 = self.s.prev_t - self.t0 - self.release, t - self.release
        for (te, kind, x, y, imp) in self.test.events:
            if tau0 < te <= tau1:
                v = min(1.0, imp / 900.0)
                if kind == "peg":
                    self.hit(t, "pluck", self.s.note(int(x / 40) % 8, 0), 0.08 + 0.1 * v, x, y)
                elif kind == "stop":
                    self.hit(t, "clack", self.s.note(3, -1), 0.1 + 0.12 * v, x, y)
                else:
                    self.hit(t, "thud", 48, 0.06 + 0.1 * v, x, y)
        if self.crossed(self.release + 0.05):
            rec = self.test.rec
            j, n = 0, len(rec)
            while j < n:
                if rec[j, 4] > 0.5 and rec[j, 3] > 60:
                    k = j
                    while k < n and rec[k, 4] > 0.5 and rec[k, 3] > 40:
                        k += 1
                    if k - j > 30:
                        self.s.fx(self.t0 + self.release + j / M.REC_HZ, "marble_roll", (k - j) / M.REC_HZ,
                                  0.06 + 0.08 * min(1.0, float(np.mean(rec[j:k, 3])) / 900.0), float(rec[j, 0]),
                                  float(rec[j, 1]))
                    j = k
                j += 1
        if self.crossed(self.release + 1.0):
            self.chat(t, "springs", "wee")
        if self.crossed(self.test_fin):
            self.hit(t, "soft_bell", 72, 0.24, M.FINISH_X, G - 150)
        if self.crossed(self.test_fin + 0.6):
            self.chorus(t, ["wheels", "springs", "digger", "tentacles", "teeth"], "yay", gap=0.2, icon="star")

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)
        self.forest(c, [(2900, 640), (4100, 700), (7300, 720), (7900, 660)])
        self.draw_village(c, t, peek=1.0)
        st = self.course_state(t)
        tp = self.trunk_pegs(t)

        def stack(c):
            """Boards still on the horses (with their uncut ends), the offcuts, the trunk pegs, the stops being
            carried, the string line."""
            for hx in HORSES_R:
                c.line(hx - 40, G, hx - 10, HORSE_TOP, TRUNK * 0.9, 10)
                c.line(hx + 40, G, hx + 10, HORSE_TOP, TRUNK * 0.9, 10)
                rect(c, hx - 50, HORSE_TOP, hx + 50, HORSE_TOP + 12, TRUNK)
            rect(c, RUN_STOP, HORSE_TOP - 110, RUN_STOP + 14, HORSE_TOP + 4, IRON * 1.3)
            for k in range(M.N_BOARDS):
                oc = self.offcut(k, t)
                if oc is None:
                    continue
                x0, x1, y = oc
                if t < self.board_t[k] + 2.4:
                    M._face(c, (x0, y), (x1, y), M.FACE, M.WOOD_FACE, grooves=False)
                    M._edge(c, (x0, y), (x1, y))
                else:
                    rect(c, x0, y, x1, y + M.BOARD_T, M.WOOD * 0.9)
            spots = M.peg_spots()
            for i in sorted(tp):
                x, y = spots[i]
                c.line(x, y - 4, x, y + 4, M.DOWEL * 0.7, 16)
                c.circle(x, y, 8, M.DOWEL)
            for i in range(M.N_BOARDS - 1):
                ss = self.stop_state(i, t)
                if ss is not None and t < self.stop_t[i] + 1.4:
                    x, y0, y1 = M.stops()[i]
                    M.draw_stop(c, x + ss[0], y0 + ss[1], y1 + ss[1], "back")
                    M.draw_stop(c, x + ss[0], y0 + ss[1], y1 + ss[1], "front")
            gl = self.m("lantern")
            for k in range(M.N_BOARDS):                   # Glo's string line, then the level on it
                ct = self.check_t[k]
                if ct <= t < ct + 3.0 and gl is not None:
                    (ax, ay), (bx, by) = self.check_ends(k)
                    u = seg(t, ct, ct + 2.0)
                    ex, ey = lerp(ax, bx, smoothstep(u)), lerp(ay, by, smoothstep(u))
                    c.line(ax, ay - 10, ex, ey - 10, np.array([236, 220, 170]), 2)
                    if u >= 1:
                        mx, my = (ax + bx) / 2, (ay + by) / 2 - 10
                        ok = seg(t, ct + 2.0, ct + 2.4)
                        PR.level(c, mx, my - 12, 160, bubble=0.0, ok=ok)

        def marble(c):
            if self.release - 2.0 <= t:
                x, y, a, _, _ = self.test.at(max(0.0, t - self.release))
                M.draw_marble(c, x, y, BALL_R, a, M.PLAIN)

        def spark(c):
            p = self.spark(t)
            if p is not None:
                for q in range(5):
                    tq = self.spark(max(self.spark0, t - 0.025 * q))
                    if tq is not None:
                        c.circle(tq[0], tq[1], 9 - 1.5 * q, LAMP * (1.0 - 0.15 * q))
                s.glow_draw(lambda g: g.circle(p[0], p[1], 50, LAMP * 0.8))
        self.draw_course(c, t, st, marbles=marble, before_front=stack, after=spark)
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t)
        # Wheels' ball rides on his head until Glo takes it up to the start
        if t < self.release - 2.0:
            if t < self.ball_pick:
                m = self.m("wheels")
                bx, by = (m.x, m.y - TOP_WHEELS * self.s.k - BALL_R + 4) if m is not None else (4500.0, G - 200)
            elif gl is not None:
                bx, by = gl.x - 20, gl.y - 60
                if t < self.ball_pick + 0.5:
                    m = self.m("wheels")
                    u = smoothstep(seg(t, self.ball_pick, self.ball_pick + 0.5))
                    hx, hy = (m.x, m.y - TOP_WHEELS * self.s.k - BALL_R + 4) if m is not None else (bx, by)
                    bx, by = lerp(hx, bx, u), lerp(hy, by, u)
                if t >= self.release - 2.6:
                    u = smoothstep(seg(t, self.release - 2.6, self.release - 2.0))
                    x0, y0, _, _, _ = self.test.at(0.0)
                    bx, by = lerp(bx, x0, u), lerp(by, y0, u)
            M.draw_marble(c, bx, by, BALL_R, 0.3, M.PLAIN)


# ====================================================================== CHEER (same world as the race, no cut)

class CheerAct(MarbleAct):
    """After the race: the winner's Keeper celebrates, the bunny comes to sniff the marbles in the tray, and the
    camera pulls back to the whole lit run in the trees."""
    name = "cheer"
    names = (-2.0, -1.0)
    joins_prev = True

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        race_act = next(a for a in scene.acts if a.name == "marble_race")
        self.race = race_act.race
        self.lane_kind = race_act.lane_kind
        self.winner = self.lane_kind[self.race.order[0]]
        self.last = self.race.order[-1]
        self.dur = 24.0
        self.T = dict(loop=1.0, bunny=5.0, sniff=9.5, home=13.0, pull=12.0)
        self.glo0 = race_act.glo_pos(race_act.dur)
        self.springs0 = (M.PLATFORM[0] + 90, M.PLATFORM[2])
        self.stats = {"race_winner": M.NAMES[self.winner]}

    def aside_moods(self, t):
        return ["hehe", "aww", "mm", "yay"]

    def target(self, t):
        keys = [(0.0, 3720.0, G - 330.0, 0.95), (self.T["sniff"] + 1.5, 3700.0, G - 280.0, 1.15),
                (self.T["pull"] + 1.0, 3800.0, G - 340.0, 1.0), (self.dur, 5150.0, G - 860.0, 0.5)]
        return _ease(keys, t)

    def bunny_pos(self, t):
        """The bunny hops from its house to the end of the tray, sniffs the marbles, hops home."""
        T = self.T
        x0, x1 = BUNNY_X + 40, M.TRAY[0] - 46
        if t < T["bunny"]:
            return None
        if t < T["sniff"]:
            u = seg(t, T["bunny"], T["sniff"])
            return lerp(x0, x1, u), abs(math.sin(u * 7 * math.pi)) * 26, 1
        if t < T["home"]:
            return x1, 3 * abs(math.sin(t * 9)) * (t < T["sniff"] + 1.5), 1
        u = seg(t, T["home"], T["home"] + 3.0)
        if u >= 1:
            return None
        return lerp(x1, x0, u), abs(math.sin(u * 7 * math.pi)) * 26, -1

    def update(self, t, dt):
        T = self.T
        self.reach = {}
        for kind, x in FINISHERS.items():
            m = self.m(kind)
            if m is None:
                continue
            dy = 0.0
            if t > T["pull"]:                                # everyone waves at us
                m.punch = 0.5 + 0.3 * math.sin(t * 6 + KEEPERS.index(kind))
            else:
                m.punch = 0.0
                ph = (t + 0.3 * KEEPERS.index(kind)) % 1.4
                dy = -4 * 26 * (ph / 0.36) * (1 - ph / 0.36) if ph < 0.36 and t < 4.0 else 0.0
            self.place(m, x, t, dt, dy=dy)
        m = self.m("lantern")                               # Glo's victory loop-the-loop
        if m is not None:
            x0, y0 = self.glo0
            u = seg(t, T["loop"], T["loop"] + 2.6)
            a = 2 * math.pi * smootherstep(u)
            x, y = x0 + 130 * math.sin(a), y0 - 130 * (1 - math.cos(a))
            m.lamp = 1.2 + 0.8 * math.sin(math.pi * u)
            self.place(m, x, t, dt, y=y)
        m = self.m("springs")                               # still up at the gate: bounces and waves
        if m is not None:
            ph = t % 0.9
            lift = 4 * 40 * (ph / 0.5) * (1 - ph / 0.5) if ph < 0.5 else 0.0
            m.spring = 0.7 * max(0.0, 1 - min(ph, abs(ph - 0.5)) / 0.1) if ph < 0.6 else 0.0
            self.place(m, self.springs0[0], t, dt, y=self.springs0[1] - lift)
        self.leaves(0.04)
        self._sounds(t)

    def _sounds(self, t):
        T = self.T
        if self.crossed(T["loop"] + 0.2):
            self.chat(t, self.winner, "wee", icon="star")
            for q, n in enumerate((72, 76, 79, 84, 88)):
                self.hit(t + 0.4 + q * 0.12, "chime", n, 0.16, self.glo0[0], self.glo0[1] - 200)
        if self.crossed(T["loop"] + 2.8):
            self.chorus(t, ["teeth", "digger", "tentacles", "wheels"], "yay", gap=0.22, icon="star")
        for k in range(7):
            if self.crossed(T["bunny"] + (k + 0.5) * (T["sniff"] - T["bunny"]) / 7):
                self.hit(t, "pluck", self.s.note(k % 5 + 2, 0), 0.14, M.TRAY[0], G)
        if self.crossed(T["sniff"] + 0.3):
            self.hit(t, "bloop", 76, 0.16, M.TRAY[0], G - 100)
        if self.crossed(T["sniff"] + 1.0):
            self.chat(t, self.lane_kind[self.last], "hehe")
        if self.crossed(T["sniff"] + 2.2):
            self.chat(t, "digger", "aww", icon="heart")
        if self.crossed(T["pull"] + 1.5):
            self.chorus(t, ["wheels", "tentacles", "teeth", "digger"], "hey", gap=0.25, icon="heart")
        if self.crossed(T["pull"] + 4.0):
            self.chat(t, "springs", "yay", icon="star")

    def draw(self, c, t):
        self.backdrop(c, t)
        self.forest(c, [(2900, 640), (4600, 700), (7300, 720), (7900, 660), (8600, 700)])
        self.draw_village(c, t, peek=1.0)

        def marbles(c):
            items = []
            for i in range(M.N_LANES):
                x, y, a, _, _ = self.race.runs[i].at(999.0)
                items.append((i, x, y, self.race.traits[i].r, a, M.MARBLE_COLS[self.lane_kind[i]]))
            draw_lane_marbles(c, items)
        self.draw_course(c, t, self.full_course(), marbles=marbles)
        b = self.bunny_pos(t)
        if b is not None:
            bunny(c, b[0], G, 1.3, b[1], b[2])
        gl = self.m("lantern")
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t, kinds=list(FINISHERS) + ["springs", "lantern"])     # the watchers stand in front


def draw_lane_marbles(c, items):
    """items: [(lane, x, y, r, ang, colour)] drawn back lane first, at their lane's depth."""
    for j, x, y, r, ang, col in sorted(items, key=lambda q: -q[0]):
        dx, dy, sc = M.lane_off(j)
        M.draw_marble(c, x + dx, y + dy, r * sc, ang, col, shade=1.0 - 0.05 * j)


# ====================================================================== RACE

FINISHERS = {"wheels": 4060.0, "digger": 4140.0, "tentacles": 4215.0, "teeth": 4285.0}    # in front of the last ramp
GLO_WATCH = (6150.0, G - 1820.0)


class RaceAct(MarbleAct):
    """The race: Glo loads the marbles, Springs bounces up to the lever, 3-2-1, six marbles down the run."""
    name = "marble_race"
    names = (-2.0, -1.0)
    fast_ok = False

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.race = M.Race(int(P.get("race_seed", 3)))
        self.lane_kind = list(M.KINDS)
        self.T = dict(springs=2.5, glo=1.5, load=10.5, count=14.5, go=17.5)
        self.go = self.T["go"]
        self.fin = [self.go + f for f in self.race.finish]
        self.first = min(self.fin)
        self.dur = max(self.fin) + 5.0
        self.hud = {i: float(i) for i in range(M.N_LANES)}
        self.lead_said = -9.0
        self._lead = None
        win = self.race.order[0]
        self.stats = {"race_seed": self.race.seed, "race_finish_s": [round(f, 2) for f in self.race.finish],
                      "race_order": [M.NAMES[self.lane_kind[i]] for i in self.race.order],
                      "race_winner": M.NAMES[self.lane_kind[win]], "race_lead_changes": self.race.changes,
                      **M.course_checks()}
        # Springs' bounces up the stubs on TREE_B to the platform
        pts = [(6990.0, G)] + STUBS + [(M.PLATFORM[0] + 90, M.PLATFORM[2])]
        self.hops = []
        t = self.T["springs"]
        for a, b in zip(pts, pts[1:]):
            jp = Jump(a[0], a[1], b[0], b[1], apex=40)
            self.hops.append((t, jp))
            t += jp.dur + 0.12
        self.top_t = t

    def aside_moods(self, t):
        if self.go < t < self.first:
            return []                                     # during the race the Keepers cheer their marbles
        return ["ooh", "hehe", "q", "aww"]

    # ----- marbles -----

    def marble(self, i, t):
        """Lane i's marble: (x, y, r, angle) at act time t."""
        tau = t - self.go
        if tau < 0:
            x, y, a, _, _ = self.race.runs[i].at(0.0)
            u = self.load_u(i, t)
            if u < 1:                                     # Glo is still putting it in
                gl = self.m("lantern")
                hx, hy = (gl.x - 30, gl.y - 70) if gl is not None else (x, y - 200)
                x, y = lerp(hx, x, smootherstep(u)), lerp(hy, y, smootherstep(u))
            return x, y, self.race.traits[i].r, a
        x, y, a, _, _ = self.race.runs[i].at(tau)
        return x, y, self.race.traits[i].r, a

    def load_u(self, i, t):
        return seg(t, self.T["load"] + 0.55 * i, self.T["load"] + 0.55 * i + 0.45)

    # ----- camera -----

    def target(self, t):
        h = self.s.h
        T = self.T
        wide = (5300.0, G - 860.0, 0.52)
        if t < T["springs"]:
            return wide
        if t < self.top_t + 0.5:
            m = self.m("springs")
            y = m.y if m is not None and m.y else G
            u = smoothstep(seg(t, T["springs"], T["springs"] + 2.0))
            return lerp(wide[0], 6550.0, u), lerp(wide[1], min(G - 300, y - 120), u), lerp(wide[2], 0.95, u)
        if t < self.go + 0.5:
            return 6470.0, G - 1640.0, 1.25
        if t < self.first + 2.0:
            tau = t - self.go
            ld = self.race.leader(tau)
            x, y, _, _, _ = self.race.runs[ld].at(tau)
            xs = sorted(self.race.runs[i].at(tau)[0] for i in range(M.N_LANES))
            px = (x + xs[2] + xs[3]) / 3                  # the leader and the middle of the pack
            if y < M.BOX_TOP - 20:                        # the zigzag: follow the pack along the board
                return min(6350.0, max(5450.0, px)), y - 50, 1.45
            if x > M.BOX[0] - 40:                         # the peg forest
                return 5080.0, y - 30, 1.45
            return max(4000.0, x - 240), min(G - 300, y - 110), 1.35
        u = smoothstep(seg(t, self.first + 2.0, self.first + 5.0))
        return lerp(3950.0, 3720.0, u), G - 330.0, lerp(1.05, 0.95, u)

    @property
    def cam_omega(self):
        return 1.7

    # ----- the Keepers -----

    def update(self, t, dt):
        T = self.T
        self.reach = {}
        for kind, x in FINISHERS.items():
            m = self.m(kind)
            if m is None:
                continue
            dy = 0.0
            fin = self.fin[self.lane_kind.index(kind)]
            if t > fin:                                   # its marble is in: a little happy hop now and then
                ph = (t - fin) % 1.6
                dy = -4 * 30 * (ph / 0.4) * (1 - ph / 0.4) if ph < 0.4 and t < fin + 6.0 else 0.0
            if kind == "wheels":
                m.punch = 0.5 if self.go < t < self.first + 3 else 0.0
            if kind == "teeth":
                m.punch_l = 0.4 if self.go < t < self.first + 3 else 0.0
            self.place(m, x, t, dt, dy=dy)
        self._springs(t, dt)
        self._glo(t, dt)
        self._hud(t, dt)
        self.leaves(0.04)
        self._sounds(t)

    def _springs(self, t, dt):
        m = self.m("springs")
        if m is None:
            return
        x, y = 6990.0, G
        m.spring = 0.0
        for i, (t0, jp) in enumerate(self.hops):
            nxt = self.hops[i + 1][0] if i + 1 < len(self.hops) else 1e9
            if t0 <= t < t0 + jp.dur:
                x, y = jp.at(t - t0)
            elif t0 + jp.dur <= t < nxt:
                x, y = jp.x1, jp.y1
                m.spring = 0.8 * max(0.0, 1 - (t - t0 - jp.dur) / 0.12)
            elif t < self.hops[0][0]:
                x, y = 6990.0, G
        if t >= self.go - 0.4:                            # pulls the lever: leans on it
            m.punch = smoothstep(seg(t, self.go - 0.4, self.go)) * (1 - smoothstep(seg(t, self.go + 0.6, self.go + 1.2)))
        self.place(m, x, t, dt, y=y)

    def glo_pos(self, t):
        T = self.T
        start = (3760.0, G - 420.0)
        gate = (M.GATE_X + 150, M.board_y(0, M.GATE_X) - 210)
        keys = [(T["glo"], *start), (T["load"] - 0.4, *gate), (T["load"] + 0.55 * 5 + 0.6, *gate),
                (T["count"], *GLO_WATCH), (self.first - 1.0, *GLO_WATCH), (self.first + 6.0, 3760.0, G - 420.0)]
        return path(keys, t)[:2]

    def _glo(self, t, dt):
        m = self.m("lantern")
        if m is None:
            return
        x, y = self.glo_pos(t)
        m.lamp = 1.2
        self.place(m, x, t, dt, y=y)

    def _hud(self, t, dt):
        order = self.race.standings(max(0.0, t - self.go))
        for slot, i in enumerate(order):
            self.hud[i] += (slot - self.hud[i]) * min(1.0, dt * 7.0)

    # ----- sounds -----

    def _sounds(self, t):
        T, R = self.T, self.race
        if self.crossed(0.8):
            self.chat(t, "teeth", "ooh")
        for i, (t0, jp) in enumerate(self.hops):
            if self.crossed(t0):
                self.hit(t, "boing", 60 + (i % 5) * 2, 0.2, jp.x0, jp.y0)
        if self.crossed(self.top_t + 0.3):
            self.chat(t, "springs", "hey", icon="!")
        for i in range(M.N_LANES):
            if self.crossed(T["load"] + 0.55 * i + 0.45):
                x, y, _, _ = self.marble(i, t)
                self.hit(t, "clack", self.s.note(i, 0), 0.2, x, y)
        if self.crossed(T["load"] + 0.55 * 6 + 0.2):
            self.chat(t, "lantern", "mm")
        for q, (icon, kind) in enumerate((("3", "springs"), ("2", "lantern"), ("1", "springs"))):
            if self.crossed(T["count"] + q * 1.0):
                self.chat(t, kind, "hey", icon=icon, step=q * 2)
        if self.crossed(self.go):
            self.hit(t, "clunk", 50, 0.3, M.GATE_X, M.board_y(0, M.GATE_X))
            self.chat(t + 0.3, "springs", "wee")
        tau0, tau1 = self.s.prev_t - self.t0 - self.go, t - self.go
        for i, run in enumerate(R.runs):
            for (te, kind, x, y, imp) in run.events:
                if tau0 < te <= tau1:
                    v = min(1.0, imp / 900.0)
                    if kind == "peg":
                        self.hit(t, "pluck", self.s.note(int(x / 40) % 8, 0), 0.05 + 0.1 * v, x, y)
                    elif kind == "stop":
                        self.hit(t, "clack", self.s.note(i + 2, -1), 0.08 + 0.12 * v, x, y)
                    else:
                        self.hit(t, "thud", 48, 0.05 + 0.1 * v, x, y)
            if self.crossed(self.go + 0.05):
                self._roll_sounds(i)
            if self.crossed(self.fin[i]):
                place = R.order.index(i)
                self.hit(t, "soft_bell", self.s.note(6 - place, 0), 0.25 if place == 0 else 0.14, M.FINISH_X, G - 150)
                if place == 0:
                    for q, n in enumerate((72, 76, 79, 84)):
                        self.hit(t + 0.15 + q * 0.11, "chime", n, 0.2, M.FINISH_X, G - 300)
        # cheering the leader: when the lead changes, the new leader's Keeper calls out (not too often)
        if self.go < t < self.first:
            ld = R.leader(t - self.go)
            if ld != self._lead and t - self.lead_said > 2.2:
                self._lead = ld
                self.lead_said = t
                self.chat(t, self.lane_kind[ld], "wee" if self.s.particles.rng.uniform() < 0.5 else "yay", icon="note")
        if self.crossed(self.first + 0.4):
            win = self.lane_kind[R.order[0]]
            self.chat(t, win, "yay", icon="star")
            others = [k for k in FINISHERS if k != win]
            self.chorus(t + 0.9, others, "yay", gap=0.25, icon="star")
        if self.crossed(self.first + 4.0):
            self.chorus(t, ["lantern", "teeth"], "hehe", gap=0.3)

    def _roll_sounds(self, i):
        """Each stretch a marble rolls along the wood: one soft rumble, louder the faster it goes."""
        run = self.race.runs[i]
        rec = run.rec
        n = len(rec)
        j = 0
        while j < n:
            if rec[j, 4] > 0.5 and rec[j, 3] > 60:
                k = j
                while k < n and rec[k, 4] > 0.5 and rec[k, 3] > 40:
                    k += 1
                dur = (k - j) / M.REC_HZ
                if dur > 0.25:
                    v = float(np.mean(rec[j:k, 3]))
                    t0 = self.t0 + self.go + j / M.REC_HZ
                    x, y = float(rec[j, 0]), float(rec[j, 1])
                    self.s.fx(t0, "marble_roll", dur, 0.05 + 0.08 * min(1.0, v / 900.0), x, y)
                j = k
            j += 1

    # ----- drawing -----

    def draw(self, c, t):
        s = self.s
        self.backdrop(c, t)
        self.forest(c, [(2900, 640), (4600, 700), (7300, 720), (7900, 660), (8600, 700)])
        self.draw_village(c, t, peek=1.0)
        st = self.full_course()
        st["gate"] = seg(t, self.go - 0.1, self.go + 0.25)
        gl = self.m("lantern")


        def marbles(c):
            items = []
            for i in range(M.N_LANES):
                if t < self.T["load"] + 0.55 * i:
                    continue
                x, y, r, a = self.marble(i, t)
                items.append((i, x, y, r, a, M.MARBLE_COLS[self.lane_kind[i]]))
            draw_lane_marbles(c, items)
        self.draw_course(c, t, st, marbles=marbles)
        if gl is not None:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
            if t < self.T["load"] + 0.55 * 6:              # the little basket she carries the marbles in
                bx, by = gl.x - 30, gl.y - 50
                c.line(gl.x - 10, gl.y - 120, bx, by - 20, IRON, 2)
                c.polygon(ellipse(bx, by, 36, 18, 16, 0, math.pi), PLANK * 0.9)
        self.draw_monsters(c, t, kinds=list(FINISHERS) + ["springs", "lantern"])     # the watchers stand in front
        self._draw_hud(c, t)

    def _draw_hud(self, c, t):
        """The standings: six marbles in race order in a little wooden strip at the top left."""
        a = smoothstep(seg(t, self.go - 1.5, self.go - 0.5)) * (1 - smoothstep(seg(t, self.dur - 2.0, self.dur - 0.8)))
        if a <= 0.01:
            return
        x0, x1, y0, y1 = self.s.view()
        z = self.s.zoom
        u = 1.0 / z
        px, py = x0 + 34 * u, y0 + 34 * u
        w, row = 250 * u, 42 * u
        bg = np.array([14, 16, 24], np.float64)
        board = bg + (np.array([96, 70, 48]) - bg) * a
        rect(c, px, py, px + w, py + row * M.N_LANES + 16 * u, board)
        c.polyline([(px, py), (px + w, py), (px + w, py + row * M.N_LANES + 16 * u), (px, py + row * M.N_LANES + 16 * u)],
                   bg + (np.array([150, 112, 72]) - bg) * a, 3 * u, closed=True)
        for slot in range(M.N_LANES):
            c.text(str(slot + 1), px + 24 * u, py + 8 * u + row * (slot + 0.5), 26 * u,
                   bg + (np.array([236, 226, 200]) - bg) * a)
        for i in range(M.N_LANES):
            yy = py + 8 * u + row * (self.hud[i] + 0.5)
            col = np.asarray(M.MARBLE_COLS[self.lane_kind[i]], np.float64)
            done = t >= self.fin[i]
            c.circle(px + 64 * u, yy, 14 * u, bg + (col - bg) * a)
            c.text(M.NAMES[self.lane_kind[i]], px + 90 * u, yy, 24 * u, bg + (np.array([236, 226, 200]) - bg) * a,
                   anchor="lm")
            if done and self.race.order[0] == i:
                c.text("*", px + w - 26 * u, yy + 4 * u, 34 * u, bg + (np.array([246, 196, 70]) - bg) * a)
