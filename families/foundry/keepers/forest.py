"""Forest Keepers acts 2-4: the monsters put the forest back (docs/engines/foundry_keepers.md).

Every mission is a little assembly line outdoors, each monster's body is its tool:
  REPLANT   - along the 8 stumps: teeth chews the stump to mulch -> digger digs -> wheels plants a
              sapling from its wagon -> tentacles waters with three cans -> springs stomps the soil;
              the lantern lights the front of the line. Then all eight grow in a time-lapse.
  BRIDGE    - animals can't cross the stream. Teeth chews a fallen log into planks, digger digs and
              wades across, springs drives the posts, teeth lays the beams, wheels + tentacles lay
              the planks; springs tests it; the bunnies and a hedgehog hop across.
  HOME      - a treehouse in a huge old tree: platform, ladder, walls, round windows, roof; lanterns
              hung by tentacles and lit by the lantern monster; fireflies; everyone goes in; lights out.
"""
import math

import numpy as np

from ..products.monster import Xform, ellipse
from ..tree_monsters import LAMP, LEAF, TRUNK, BARK, SAWDUST
from .common import (Act, Jump, Night, PLANK, SOIL, SOIL_WET, WATER, WATER_DEEP, bunny, hedgehog, lerp, rect, seg,
                     settle, smoothstep, smootherstep, tree, wood_sign)

DROP = np.array([120, 170, 230], np.float64)
SPARK = np.array([150, 240, 170], np.float64)
FIREFLY = np.array([210, 255, 140], np.float64)
CAN = np.array([96, 140, 120], np.float64)
POST = np.array([110, 80, 54], np.float64)
ROOF = np.array([92, 60, 46], np.float64)


class ForestAct(Act):
    """Night forest act: ground at G, monsters placed each frame with an optional body transform."""
    G = 1000.0

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = Night(np.random.default_rng(scene.seed + {"replant": 31, "bridge": 32, "treehouse": 33}.get(self.name, 30)), self.G, -2500, 6000)
        self.poses = {}
        self.stats = {}

    def m(self, kind):
        return self.s.by_kind.get(kind)

    def place(self, m, x, t, dt, y=None, dy=0.0, ang=0.0, walk=None, face_bob=True):
        """Put monster m at x (feet on the ground unless y is given); walking/wheels from its speed."""
        if m is None:
            return
        vx = (x - m.x) / dt if dt > 0 and m.x else 0.0
        m.x, m.y = x, self.G if y is None else y
        moving = abs(vx) > 15
        m.walk = (1.0 if moving else 0.0) if walk is None else walk
        m.gait += dt * 9 * m.walk
        m.wheel_rot += vx * dt / (46 * m.k)
        if moving and face_bob and m.kind not in ("wheels", "lantern"):
            dy -= abs(math.sin(m.gait * 0.5)) * 8
        self.poses[m.kind] = (dy, ang)
        m.alive = 1.0
        m.orb_in = 1.0
        m.rough = 0.0
        m.attach = None
        m.badge = 1.0

    def draw_monsters(self, c, t, kinds=None):
        for m in self.s.monsters:
            if kinds is not None and m.kind not in kinds:
                continue
            if m.kind not in self.poses or not self.s.visible(m.x - 400, m.x + 400):
                continue
            dy, ang = self.poses[m.kind]
            bc = m.body_center()
            mc = Xform(c, 0, dy, ang, 1.0, bc[0], bc[1]) if (dy or ang) else c
            m.draw(mc, t, self.s.glow)
            # names float above them for the first seconds of every mission
            amt = smoothstep(seg(t, 1.0, 1.6)) * (1 - smoothstep(seg(t, 7.0, 8.0)))
            m.draw_name(Xform(c, 0, dy) if dy else c, amt, 30)

    def backdrop(self, c, t):
        self.night.draw(self.s, c, t)
        self.night.ground_slab(self.s, c)

    def lantern_light(self, c, x, y, r=420, k=1.0):
        """Warm pool of light under the lantern monster."""
        self.s.glow_draw(lambda g: g.polygon([(x - 30, y), (x + 30, y), (x + r * 0.55, self.G + 10),
                                              (x - r * 0.55, self.G + 10)], LAMP * 0.05 * k))


# ====================================================================== REPLANT

class ReplantAct(ForestAct):
    name = "replant"
    ORDER = ["teeth", "digger", "wheels", "tentacles", "springs"]     # the line, front to back

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        d = dict(intro=7.0, move=1.4, work=4.4, grow=13.0, hold=6.0)
        d.update(P.get("durations", {}))
        self.d = d
        self.n = P.get("stumps", 8)
        self.X = [800 + i * 360 for i in range(self.n)]
        self.sign_x = 350
        self.steps = self.n + len(self.ORDER) - 1
        self.cyc = d["move"] + d["work"]
        self.T = {"line": d["intro"], "grow": d["intro"] + self.steps * self.cyc}
        self.T["hold"] = self.T["grow"] + d["grow"]
        self.dur = self.T["hold"] + d["hold"]
        self.tree_h = 600

    def sx(self, i):
        """Stump x (virtual stumps to the left form the waiting queue)."""
        return 800 + i * 360

    def stage_t(self, i, q):
        """(work start, work end) of stage q on stump i."""
        s = i + q
        w0 = self.T["line"] + s * self.cyc + self.d["move"]
        return w0, w0 + self.d["work"]

    def stomp_t0(self, k):
        """Take-off time (into the work slot) of Springs' k-th stomp."""
        return self.d["work"] * (0.18 + 0.42 * k)

    def progress(self, i, q, t):
        w0, w1 = self.stage_t(i, q)
        return seg(t, w0, w1)

    def target(self, t):
        h = self.s.h
        y = self.G - h * 0.3 / 1.2
        if t < self.T["line"]:
            u = smootherstep(seg(t, 0, self.T["line"]))
            return lerp(self.sign_x + 200, self.sx(0) - 300, u), y, 1.2
        if t < self.T["grow"]:
            k = (t - self.T["line"]) / self.cyc
            mid = self.sx(min(k, self.n - 1) - 2.0) - 60      # middle of the five workers
            return mid, y, 1.2
        u = smootherstep(seg(t, self.T["grow"], self.T["grow"] + 4))
        wide = (self.sx(0) + self.sx(self.n - 1)) / 2
        return lerp(self.sx(self.n - 1) - 2 * 360 - 60, wide, u), lerp(y, self.G - h * 0.40, u), lerp(1.2, 0.62, u)

    def wait_x(self, q):
        """Where each worker waits once its last stump is done (right of the row, in line order)."""
        return self.sx(self.n - 1) + 260 + (len(self.ORDER) - 1 - q) * 150

    def gather_x(self, q):
        """Where they stand to watch the trees grow: in the middle of the new grove."""
        mid = (self.sx(0) + self.sx(self.n - 1)) / 2
        return mid + (2 - q) * 190

    def worker_x(self, q, t):
        """x of the monster at stage q: walks stump to stump, slightly left of the work spot."""
        if t < self.T["line"]:
            u = smootherstep(seg(t, 0.5 + q * 0.4, self.T["line"] - 0.3))
            return lerp(-900 - q * 200, self.sx(-q) - 120, u)
        if t >= self.T["grow"]:
            u = smootherstep(seg(t, self.T["grow"] + 0.3 * q, self.T["grow"] + 4.0 + 0.3 * q))
            return lerp(self.wait_x(q), self.gather_x(q), u)
        s = (t - self.T["line"]) / self.cyc
        k = int(s)
        r = (s - k) * self.cyc
        u = smootherstep(min(1.0, r / self.d["move"]))
        spot = lambda i: self.sx(i) - 120 if i <= self.n - 1 else self.wait_x(q)
        return lerp(spot(k - 1 - q), spot(k - q), u)

    def update(self, t, dt):
        s, P = self.s, self.s.particles
        for q, kind in enumerate(self.ORDER):
            m = self.m(kind)
            if m is None:
                continue
            x = self.worker_x(q, t)
            dy, ang = 0.0, 0.0
            m.dig = 0.0
            m.spring = 0.0
            m.punch = 0.0
            i_now = int((t - self.T["line"]) / self.cyc) - q if t >= self.T["line"] else -1
            working = False
            if 0 <= i_now < self.n and self.T["line"] <= t < self.T["grow"]:
                u = self.progress(i_now, q, t)
                working = 0 < u < 1
                sxp = self.sx(i_now)
                if working:
                    if kind == "teeth":                       # bend over the stump and chomp
                        ang = 0.25 * (0.5 + 0.5 * math.sin(u * 40))
                        if P.rng.uniform() < 0.7:
                            P.burst(sxp, self.G - 30, 2, SAWDUST, 330, 0.7, 4, g=1000, spread=1.0)
                    elif kind == "digger":
                        m.dig = 0.5 + 0.5 * math.sin(u * 30)
                        if P.rng.uniform() < 0.5:
                            P.burst(sxp - 40, self.G - 5, 2, SOIL * 1.6, 300, 0.8, 5, g=1300, spread=0.8,
                                    direction=-math.pi * 0.75)
                    elif kind == "springs":                    # two real-gravity stomps on the soil
                        tw = u * self.d["work"]
                        j = Jump(0, 0, 0, 0, apex=240)
                        for k in range(2):
                            t0 = self.stomp_t0(k)
                            if t0 <= tw < t0 + j.dur:
                                dy = j.at(tw - t0)[1]
                            if abs(tw - t0) < 0.1 or abs(tw - t0 - j.dur) < 0.1:
                                m.spring = 0.8
                        x = lerp(x, sxp - 40, smoothstep(u * 4))
                    elif kind == "tentacles":
                        if P.rng.uniform() < 0.8 and 0.15 < u < 0.85:
                            for k in range(3):
                                P.burst(sxp - 40 + k * 40, self.G - 170, 1, DROP, 60, 0.6, 3.5, g=1500,
                                        direction=math.pi / 2, spread=0.2)
            if t >= self.T["grow"]:
                dy = -abs(math.sin(t * 3 + q)) * 6 * smoothstep(seg(t, self.T["grow"] + 4, self.T["grow"] + 5))
            self.place(m, x, t, dt, dy=dy, ang=ang)
            # sounds for each stage
            for i in range(self.n):
                w0, w1 = self.stage_t(i, q)
                xx = self.sx(i)
                if self.crossed(w0 + 0.1):
                    if kind == "teeth":
                        self.fx(t, "saw", self.d["work"] * 0.6, 0.35, xx, self.G)
                        for k in range(6):
                            self.hit(t + 0.2 + k * 0.45, "clack", s.note(k % 3, -1), 0.3, xx, self.G)
                    elif kind == "digger":
                        if i % 3 == 0:
                            self.say(t, "digger", "down", xx, self.G, 0.4)
                        for k in range(5):
                            self.fx(t + k * 0.7, "slide", 0.3, 0.35, xx, self.G)
                    elif kind == "wheels":
                        self.fx(t, "servo", 1.2, 0.3, xx, self.G - 200)
                    elif kind == "tentacles":
                        self.fx(t + 0.4, "hiss", self.d["work"] * 0.6, 0.3, xx, self.G - 150)
                if kind == "wheels" and self.crossed(w0 + self.d["work"] * 0.55):
                    self.hit(t, "clunk", s.note(i), 0.45, xx, self.G)
                if kind == "springs":
                    for k in range(2):
                        if self.crossed(w0 + self.stomp_t0(k)):
                            self.hit(t, "boing", s.note(i + k, -1), 0.45, xx, self.G)
                        if self.crossed(w0 + self.stomp_t0(k) + Jump(0, 0, 0, 0, apex=240).dur):
                            self.hit(t, "thud", 42, 0.6, xx, self.G)
                            self.hit(t, "pluck", s.note(i + k * 2), 0.4, xx, self.G)
                            P.burst(xx - 40, self.G - 4, 10, SAWDUST * 0.6, 220, 0.6, 5, g=400, spread=1.4)
                    if self.crossed(w1):
                        P.burst(xx, self.G - 60, 12, SPARK, 160, 0.9, 3, g=-50, glow=True)
                        self.hit(t, "chime", s.note(i + 2, 0), 0.35, xx, self.G - 100)
        lan = self.m("lantern")
        if lan is not None:
            if t < self.T["line"]:
                lx = self.worker_x(0, t) + 150
            elif t < self.T["grow"]:
                front = min(self.n - 1, max(0, int((t - self.T["line"]) / self.cyc)))
                lx = lerp(self.sx(max(0, front - 1)), self.sx(front), smootherstep(min(1.0, ((t - self.T["line"]) % self.cyc) / self.d["move"])))
                lx += 40
            else:
                u = seg(t, self.T["grow"], self.T["hold"])
                lx = lerp(self.sx(0), self.sx(self.n - 1), 0.5 - 0.5 * math.cos(u * math.pi * 2)) if u < 1 else \
                    (self.sx(0) + self.sx(self.n - 1)) / 2
            self.place(lan, lx, t, dt, y=self.G - 170)
        # growth time-lapse sounds + sparkles
        g0 = self.T["grow"]
        for q, kind in enumerate(("teeth", "digger", "wheels", "tentacles", "springs", "lantern")):
            if self.crossed(g0 + self.d["grow"] - 3.0 + q * 0.22):
                self.say(t, kind, "cheer", self.gather_x(min(q, 4)), self.G, 0.5)
        if self.crossed(g0 + 1.0):
            for k in range(8):
                self.hit(t + k * 0.55, "soft_bell", s.note(k), 0.4, self.sx(k % self.n), self.G - 300)
        if g0 + 1 < t < g0 + self.d["grow"] - 2:
            for i in range(self.n):
                if P.rng.uniform() < 0.12:
                    P.burst(self.sx(i) + P.rng.uniform(-100, 100), self.G - P.rng.uniform(100, 450), 1, SPARK, 40,
                            1.6, 3, g=-30, glow=True)
        self.stats = {"replant_stumps": self.n}

    # ----- drawing -----

    def draw(self, c, t):
        self.backdrop(c, t)
        s = self.s
        wood_sign(c, self.sign_x, self.G, "REPLANT", lit=1.0, glow_fn=s.glow_draw)
        # background old forest beyond the clearing
        for j, x in enumerate((-500, 30, 3900, 4300, 4700)):
            if s.visible(x - 250, x + 250):
                tree(c, x, self.G, 650 + 60 * (j % 2), 500 + j)
        grow = smootherstep(seg(t, self.T["grow"] + 1, self.T["grow"] + self.d["grow"] - 2))
        for i in range(self.n):
            self._stump(c, i, t, grow)
        lan = self.m("lantern")
        if lan is not None and "lantern" in self.poses:
            self.lantern_light(c, lan.x, lan.y - 80)
        self._wagon(c, t)
        self._cans(c, t)
        self.draw_monsters(c, t)

    def _stump(self, c, i, t, grow):
        x, G = self.sx(i), self.G
        if not self.s.visible(x - 300, x + 300):
            return
        chew = self.progress(i, 0, t)
        dig = self.progress(i, 1, t)
        plant = self.progress(i, 2, t)
        water = self.progress(i, 3, t)
        stomp = self.progress(i, 4, t)
        # soil circle (wet after watering, flat after stomping)
        if dig > 0:
            mound = 26 * smoothstep(dig) * (1 - smoothstep(stomp))
            col = SOIL * (1 - water) + SOIL_WET * water
            c.polygon(ellipse(x - 60, G - 2, 60 * smoothstep(dig), mound + 4, 20, math.pi, 2 * math.pi), col)
            c.polygon(ellipse(x, G + 2, 46 * smoothstep(dig), 10, 24), col * 0.6)
        if chew < 1:                                       # the old stump, chewed down to mulch
            hgt = 44 * (1 - chew)
            rect(c, x - 26, G - hgt, x + 26, G, TRUNK)
            c.polygon(ellipse(x, G - hgt, 26, 7, 20), SAWDUST * 0.7)
        if chew > 0 and dig < 0.6:
            c.polygon(ellipse(x + 30, G, 34 * smoothstep(chew), 14 * smoothstep(chew), 18, math.pi, 2 * math.pi),
                      SAWDUST * 0.55)
        if plant > 0.55:
            h = lerp(150, 560, grow)
            sway = 0.03 * math.sin(t * 1.2 + i)
            tc = Xform(c, ang=sway, px=x, py=G)
            if grow < 0.02:
                tc.line(x, G, x, G - 120, TRUNK, 8)
                tc.circle(x, G - 130, 34, LEAF[1])
                tc.circle(x - 16, G - 120, 22, LEAF[0])
                tc.circle(x + 18, G - 118, 20, LEAF[2])
            else:
                tree(tc, x, G, h, 700 + i, leaf_k=lerp(0.8, 1.0, grow))

    def _wagon(self, c, t):
        m = self.m("wheels")
        if m is None or "wheels" not in self.poses:
            return
        wx = m.x - 210 * m.k / 0.55
        G = self.G
        left = self.n
        for i in range(self.n):
            if self.progress(i, 2, t) > 0.3:
                left -= 1
        c.line(wx + 50, G - 40, m.x - 60, G - 40, STEEL_C, 5)
        rect(c, wx - 70, G - 80, wx + 60, G - 34, PLANK * 0.8)
        for k in range(left):
            sx = wx - 55 + (k % 4) * 34
            c.line(sx, G - 80, sx, G - 140, TRUNK, 4)
            c.circle(sx, G - 148, 16, LEAF[k % 3])
        for wxx in (wx - 40, wx + 30):
            c.circle(wxx, G - 22, 22, np.array([30, 30, 34]))
            c.circle(wxx, G - 22, 9, STEEL_C)
        # sapling in the claw while planting
        for i in range(self.n):
            u = self.progress(i, 2, t)
            if 0 < u < 0.55:
                hx = m.x + 150 * m.k
                y = lerp(G - 260 * m.k, G - 10, smoothstep(u / 0.55))
                c.line(hx, y, hx, y - 120, TRUNK, 8)
                c.circle(hx, y - 130, 34, LEAF[1])

    def _cans(self, c, t):
        m = self.m("tentacles")
        if m is None or "tentacles" not in self.poses:
            return
        for i in range(self.n):
            u = self.progress(i, 3, t)
            if 0 < u < 1:
                x = self.sx(i)
                tilt = 0.6 * smoothstep(seg(u, 0.05, 0.2)) * (1 - smoothstep(seg(u, 0.85, 1.0)))
                for k in range(3):
                    cx, cy = x - 60 + k * 40, self.G - 200 - 20 * math.sin(k + t)
                    cc = Xform(c, ang=tilt, px=cx, py=cy)
                    rect(cc, cx - 14, cy - 16, cx + 14, cy + 16, CAN)
                    cc.line(cx + 14, cy - 6, cx + 34, cy - 18, CAN * 0.8, 4)
                    cc.line(m.x, m.y - 200 * m.k, cx - 10, cy, m.color * 0.8, 6)
                return


STEEL_C = np.array([120, 126, 138], np.float64)


# ====================================================================== BRIDGE

class BridgeAct(ForestAct):
    name = "bridge"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        d = dict(intro=6.0, chew=13.0, posts=12.0, beams=6.0, planks=20.0, test=5.0, cross=16.0, hold=5.0)
        d.update(P.get("durations", {}))
        self.d = d
        T, t = {}, 0.0
        for k in ("intro", "chew", "posts", "beams", "planks", "test", "cross", "hold"):
            T[k] = t
            t += d[k]
        self.T, self.dur = T, t
        self.s0, self.s1 = 1500.0, 2060.0                  # stream banks
        self.wy = self.G + 60                              # water surface
        self.log = (250.0, 800.0)                          # fallen log on the left
        self.pile_x = 1020.0
        self.posts_x = (self.s0 - 20, self.s1 + 20)
        self.n_planks = 9
        self.plank_w = (self.posts_x[1] - self.posts_x[0]) / self.n_planks
        # the animals wait on the far bank and come across to the monsters once the bridge is done
        self.animals = [("bunny", 2230), ("bunny", 2330), ("hedgehog", 2440), ("bunny", 2540)]
        self._plan_springs()

    def _plan_springs(self):
        """Springs' moves as real jumps: carry post 1 onto its hole and stomp it in, then carry post 2 in
        one big bounce over the water and stomp that in, then test the finished bridge hop by hop."""
        T, G = self.T, self.G
        pile = self.pile_x + 60
        segs, self.post_t = [], {}
        p0 = T["posts"]
        segs.append(("walk", 0.0, p0 + 2.6, -700, pile, G))
        for k, (t_go, land_x) in enumerate(((p0 + 2.6, self.posts_x[0]), (p0 + 10.4, self.posts_x[1]))):
            if k == 1:
                segs.append(("walk", segs[-1][2], t_go, segs[-1][4], pile, G))
            j = Jump(pile, G, land_x, G - 140, apex=110 if k == 0 else 220)
            segs.append(("jump", t_go, t_go + j.dur, j, k))                   # carrying post k
            t_land = t_go + j.dur
            self.post_t[k] = t_land
            tt = t_land + 0.15
            for q in range(2):                                                  # two stomps drive it in
                top0 = G - 140 + 45 * q
                st = Jump(land_x, top0, land_x, top0 + 45, apex=110)
                segs.append(("jump", tt, tt + st.dur, st, None))
                tt += st.dur + 0.12
            self.post_t[(k, "done")] = tt
            off_x = self.s0 - 330 if k == 0 else self.posts_x[1] + 90
            j = Jump(land_x, G - 50, off_x, G, apex=70)
            segs.append(("jump", tt, tt + j.dur, j, None))
            segs.append(("stand", tt + j.dur, tt + j.dur + 0.01, off_x, G))
        # waits on the far bank until the bridge is done, then tests it: hops across and back
        t = T["test"]
        segs.append(("stand", segs[-1][2], t, self.posts_x[1] + 90, G))
        xs = [self.posts_x[1] + 90] + list(np.linspace(self.posts_x[1] - 60, self.posts_x[0] + 60, 4)) + [self.posts_x[0] - 90]
        xs = xs + xs[-2::-1]
        for i in range(len(xs) - 1):
            y0 = G - 40 if self.posts_x[0] < xs[i] < self.posts_x[1] else G
            y1 = G - 40 if self.posts_x[0] < xs[i + 1] < self.posts_x[1] else G
            j = Jump(xs[i], y0, xs[i + 1], y1, apex=110)
            segs.append(("jump", t, t + j.dur, j, None))
            t += j.dur + 0.05
        segs.append(("stand", t, 1e9, xs[-1], G))
        self.sp_segs = segs

    def springs_at(self, t):
        """(x, feet y, carrying post k or None)"""
        last = None
        for sg in self.sp_segs:
            if sg[0] == "jump":
                _, t0, t1, j, carry = sg
                if t0 <= t < t1:
                    x, y = j.at(t - t0)
                    return x, y, carry
                if t >= t1:
                    last = (j.x1, j.y1)
            elif sg[0] == "walk":                         # ("walk", t0, t1, x0, x1, y)
                _, t0, t1, x0, x1, y = sg
                if t0 <= t < t1:
                    return lerp(x0, x1, smootherstep(seg(t, t0, t1))), y, None
                if t >= t1:
                    last = (x1, y)
            else:                                          # ("stand", t0, t1, x, y)
                _, t0, t1, x0, y = sg
                if t0 <= t < t1:
                    return x0, y, None
                if t >= t1:
                    last = (x0, y)
        return (last[0], last[1], None) if last else (-700, self.G, None)

    def post_top(self, k, t):
        """Top of post k once it is in its hole (None before Springs sets it down)."""
        tl = self.post_t[k]
        if t < tl:
            return None
        drove = sum(1 for sg in self.sp_segs if sg[0] == "jump" and sg[4] is None and tl < sg[2] <= t
                    and abs(sg[3].x0 - self.posts_x[k]) < 1 and abs(sg[3].x1 - self.posts_x[k]) < 1)
        return self.G - 140 + 45 * min(2, drove)

    def target(self, t):
        T, h = self.T, self.s.h
        y = self.G - h * 0.3 / 1.15
        if t < T["chew"]:
            return lerp(700, 900, seg(t, 0, T["chew"])), y, 1.15
        if t < T["posts"]:
            return lerp(600, 1000, smootherstep(seg(t, T["chew"], T["posts"]))), y, 1.15
        if t < T["cross"]:
            return (self.s0 + self.s1) / 2 - 100, y, 1.15
        u = smootherstep(seg(t, T["cross"], T["cross"] + self.d["cross"] * 0.8))
        return lerp((self.s0 + self.s1) / 2 - 100, (self.s0 + self.s1) / 2 - 450, u), y, 1.15

    def beam_x0(self, k, t):
        """Left end of beam k while Twigs slides it across the posts (it rests on both when done)."""
        span = self.posts_x[1] - self.posts_x[0] + 20
        t0 = self.T["beams"] + 0.8 + k * 2.4
        u = smootherstep(seg(t, t0, t0 + 1.8))
        return lerp(self.posts_x[0] - 10 - span, self.posts_x[0] - 10, u)

    def planks_laid(self, t):
        T = self.T
        return (t - T["planks"]) / self.d["planks"] * self.n_planks if t >= T["planks"] else 0.0

    def update(self, t, dt):
        T, d, s, P = self.T, self.d, self.s, self.s.particles
        G = self.G
        # --- teeth: chew the log into planks, then lay the beams, then cheer
        te = self.m("teeth")
        if te is not None:
            ang = 0.0
            if t < T["chew"]:
                x = lerp(-600, self.log[0] - 60, smootherstep(seg(t, 0.5, T["chew"])))
            elif t < T["posts"]:
                u = seg(t, T["chew"], T["posts"])
                x = lerp(self.log[0] - 60, self.log[1] - 60, u)
                ang = 0.22 * (0.5 + 0.5 * math.sin(t * 14))
                if P.rng.uniform() < 0.8:
                    P.burst(x + 80, G - 50, 2, SAWDUST, 380, 0.7, 4, g=1000, spread=1.1)
            elif t < T["beams"] + 0.6:
                x = lerp(self.log[1] - 60, self.beam_x0(0, T["beams"] + 0.6) - 90, smootherstep(seg(t, T["posts"], T["beams"] + 0.6)))
            elif t < T["planks"]:
                k = 0 if t < T["beams"] + 3.0 else 1
                x = self.beam_x0(k, t) - 90                      # pushing the beam's back end
                if k == 1 and t < T["beams"] + 3.4:
                    x = lerp(self.beam_x0(0, t) - 90, self.beam_x0(1, T["beams"] + 3.4) - 90,
                             smootherstep(seg(t, T["beams"] + 3.0, T["beams"] + 3.4)))
            else:
                x = self.s0 - 160 - 120
            self.place(te, x, t, dt, ang=ang)
        # --- digger: dig left post hole, wade across, dig right hole
        dg = self.m("digger")
        if dg is not None:
            dg.dig = 0.0
            dy = 0.0
            p0 = T["posts"]
            if t < p0:
                x = lerp(-800, self.s0 - 260, smootherstep(seg(t, 1.0, T["chew"])))
            elif t < p0 + 3.5:
                x = self.s0 - 120
                dg.dig = 0.5 + 0.5 * math.sin(t * 20)
            elif t < p0 + 7.5:
                u = smootherstep(seg(t, p0 + 3.5, p0 + 7.5))
                x = lerp(self.s0 - 120, self.s1 + 120, u)
                dy = 70 * math.sin(math.pi * seg(x, self.s0 - 40, self.s1 + 40))       # wading
            elif t < p0 + 11:
                x = self.s1 + 120
                dg.dig = 0.5 + 0.5 * math.sin(t * 20)
            else:
                x = self.s1 + 200
            self.place(dg, x, t, dt, dy=dy)
        # --- springs: real jumps (see _plan_springs)
        sp = self.m("springs")
        if sp is not None:
            x, y, carry = self.springs_at(t)
            sp.spring = 0.0
            for sg in self.sp_segs:
                if sg[0] == "jump" and (abs(t - sg[1]) < 0.1 or abs(t - sg[2]) < 0.1):
                    sp.spring = 0.7
                if sg[0] == "jump" and self.crossed(sg[1]):
                    self.hit(t, "boing", s.note(int(sg[1] * 3) % 5, -1), 0.45, sg[3].x0, G)
                if sg[0] == "jump" and self.crossed(sg[2]):
                    self.hit(t, "thud", 42 if sg[4] is None else 40, 0.5, sg[3].x1, G)
            self.place(sp, x, t, dt, y=y, walk=0.0)
        # --- wheels + tentacles: lay planks (wheels carries, tentacles holds the end)
        wh, tn = self.m("wheels"), self.m("tentacles")
        laid = self.planks_laid(t)
        if wh is not None:
            if t < T["planks"]:
                x = lerp(-900, self.pile_x - 140, smootherstep(seg(t, 1.5, T["chew"] + 2)))
            elif t < T["test"]:
                k = min(self.n_planks - 1, int(laid))
                ph = laid - int(laid)
                end_x = self.posts_x[0] + k * self.plank_w
                x = lerp(self.pile_x - 140, end_x - 120, math.sin(ph * math.pi))
            else:
                x = lerp(self.pile_x - 140, self.s0 - 420, smootherstep(seg(t, T["test"], T["test"] + 2)))
            onb = self.posts_x[0] < x < self.posts_x[0] + laid * self.plank_w
            self.place(wh, x, t, dt, y=G - 40 if onb else None)
        if tn is not None:
            if t < T["planks"]:
                x = lerp(-1000, self.s0 - 330, smootherstep(seg(t, 2.0, T["chew"] + 3)))
            elif t < T["test"]:
                x = self.s0 - 200
            else:
                x = lerp(self.s0 - 200, self.s0 - 560, smootherstep(seg(t, T["test"], T["test"] + 2)))
            self.place(tn, x, t, dt)
        ln = self.m("lantern")
        if ln is not None:
            if t < T["posts"]:
                x = lerp(-700, self.log[1], smootherstep(seg(t, 0.5, T["chew"])))
            elif t < T["planks"]:
                x = lerp(self.log[1], (self.s0 + self.s1) / 2, smootherstep(seg(t, T["posts"], T["posts"] + 4)))
            else:
                x = self.posts_x[0] + max(0.5, laid) * self.plank_w
                if t >= T["test"]:
                    x = (self.s0 + self.s1) / 2
            self.place(ln, x, t, dt, y=G - 260)
        # --- sounds
        if self.crossed(T["chew"]):
            self.fx(t, "saw", 6.0, 0.35, self.log[0], G)
        for k in range(8):
            tk = T["chew"] + 0.5 + k * 1.4
            if self.crossed(tk) and tk < T["posts"]:
                self.hit(t, "clack", s.note(k, -1), 0.4, self.pile_x, G)
        p0 = T["posts"]
        for k, tk in enumerate((p0 + 0.4, p0 + 8.0)):
            if self.crossed(tk):
                for q in range(5):
                    self.fx(t + q * 0.6, "slide", 0.3, 0.3, self.posts_x[k], G)
        if self.crossed(p0 + 4.0):
            self.fx(t, "splash", 0.8, 0.5, self.s0 + 50, self.wy)
            self.say(t + 0.1, "digger", "up", self.s0 + 50, self.wy, 0.5)
        if self.crossed(p0 + 7.2):
            self.fx(t, "splash", 0.8, 0.5, self.s1 - 50, self.wy)
        for tk, xx in ((p0 + 5.5, self.posts_x[0]), (T["beams"] + 1.0, self.posts_x[1])):
            if self.crossed(tk - 0.02):
                self.hit(t, "thud", 40, 0.7, xx, G)
                self.hit(t, "pluck", s.note(2), 0.4, xx, G)
        for k in range(2):
            if self.crossed(T["beams"] + 1.5 + k * 2):
                self.hit(t, "clunk", s.note(k * 3, -1), 0.6, (self.s0 + self.s1) / 2, G)
        for k in range(self.n_planks):
            if self.crossed(T["planks"] + (k + 0.6) * d["planks"] / self.n_planks):
                self.hit(t, "clunk", s.note(k), 0.55, self.posts_x[0] + (k + 0.5) * self.plank_w, G)
        for k in range(6):
            if self.crossed(T["test"] + (k + 0.5) * d["test"] / 6):
                self.hit(t, "pluck", s.note(k + 3), 0.5, (self.s0 + self.s1) / 2, G)
        for a, (kind, ax) in enumerate(self.animals):
            c0, c1 = self.animal_t(a)
            hops = 8 if kind == "bunny" else 0
            for k in range(hops):
                if self.crossed(lerp(c0, c1, (k + 0.5) / hops)):
                    self.hit(t, "pluck", s.note(k + a * 2, 0), 0.3, ax, G)
            if self.crossed(c1):
                self.hit(t, "chime", s.note(a + 4, 0), 0.35, self.s1 + 300, G)
                greeter = ("wheels", "tentacles", "teeth", "digger")[a % 4]
                self.say(t + 0.2, greeter, "hum" if kind == "hedgehog" else "up", self.s0 - 300, G, 0.45)
        if self.crossed(T["cross"] + d["cross"] - 2.2):
            for q, kind in enumerate(("wheels", "tentacles", "teeth", "springs", "lantern", "digger")):
                self.say(t + q * 0.2, kind, "cheer", self.s0 - 300, G, 0.45)
        if self.crossed(T["cross"] + d["cross"] - 1.5):
            for k, nn in enumerate((0, 2, 4, 7)):
                self.hit(t + k * 0.13, "soft_bell", s.note(nn) if nn < 7 else s.note(0, 1), 0.5, self.s1, G - 300)
        if self.crossed(1.0):
            self.fx(t, "bubble", self.dur - 2, 0.15, (self.s0 + self.s1) / 2, self.wy)
        self.stats = {"bridge_planks": self.n_planks, "animals_crossed": len(self.animals)}

    def animal_t(self, a):
        T, d = self.T, self.d
        c0 = T["cross"] + 0.5 + a * 2.6
        return c0, c0 + (4.5 if self.animals[a][0] == "bunny" else 7.5)

    # ----- drawing -----

    def draw(self, c, t):
        s, T, G = self.s, self.T, self.G
        self.night.draw(s, c, t)
        L, R = s.cam_x - 1200, s.cam_x + s.w + 1200
        # banks + stream bed
        rect(c, L, G, self.s0, G + 2500, np.array([31, 25, 24]))
        rect(c, self.s1, G, R, G + 2500, np.array([31, 25, 24]))
        c.polygon([(self.s0, G), (self.s0 + 60, G + 200), (self.s1 - 60, G + 200), (self.s1, G), (self.s1, G + 2500),
                   (self.s0, G + 2500)], np.array([24, 20, 20]))
        rect(c, L, G - 6, self.s0, G + 4, np.array([30, 52, 38]))
        rect(c, self.s1, G - 6, R, G + 4, np.array([30, 52, 38]))
        wood_sign(c, 60, G, "BRIDGE", lit=1.0, glow_fn=s.glow_draw)
        for j, x in enumerate((-300, 380, 2500, 2900, 3300)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 620 + 60 * (j % 2), 800 + j)
        # fallen log (chewed from the left)
        u = seg(t, T["chew"], T["posts"])
        lx0 = lerp(self.log[0], self.log[1], u)
        if lx0 < self.log[1] - 5:
            rect(c, lx0, G - 76, self.log[1], G, TRUNK)
            c.line(lx0, G - 52, self.log[1], G - 50, BARK, 4)
            c.polygon(ellipse(self.log[1], G - 38, 14, 38, 16), SAWDUST * 0.85)
            c.polygon(ellipse(lx0, G - 38, 14, 38, 16), SAWDUST * 0.95)
        # plank pile (made while chewing, used while laying)
        made = min(self.n_planks, int(u * self.n_planks + 0.5)) if t >= T["chew"] else 0
        left = made - int(self.planks_laid(t) + 0.4) if t < T["test"] else 0
        for k in range(max(0, left)):
            rect(c, self.pile_x - 70, G - 14 - k * 13, self.pile_x + 70, G - 3 - k * 13, PLANK * (0.9 + 0.1 * (k % 2)))
        # posts: in the pile until Springs takes one, carried overhead, then set in the hole and driven
        for k, px in enumerate(self.posts_x):
            top = self.post_top(k, t)
            if top is not None:
                rect(c, px - 14, top, px + 14, G + 40, POST)
                c.line(px - 14, top, px + 14, top, SAWDUST * 0.7, 3)
            elif t < self.post_t[k] - 1.5:
                rect(c, self.pile_x + 110 + k * 34, G - 150, self.pile_x + 136 + k * 34, G, POST)
        # beams + planks
        wob = 0.0
        if T["test"] <= t < T["cross"]:
            wob = 3 * math.sin(t * 18) * math.exp(-((t - T["test"]) % 0.8) * 3)
        span = self.posts_x[1] - self.posts_x[0] + 20
        for k in range(2):
            if t >= T["beams"] + 0.8 + k * 2.4:
                x0 = self.beam_x0(k, t)
                rect(c, x0, G - 30 + k * 10 + wob, x0 + span, G - 18 + k * 10 + wob, POST * 1.1)
        laid = self.planks_laid(t)
        for k in range(self.n_planks):
            u = laid - k
            if u <= 0:
                continue
            drop = 30 * (1 - settle(min(1.0, u * 1.6), 0.1))
            x0 = self.posts_x[0] + k * self.plank_w
            rect(c, x0 + 2, G - 40 - drop + wob, x0 + self.plank_w - 2, G - 22 - drop + wob, PLANK * (0.95 + 0.08 * (k % 2)))
            c.line(x0 + 2, G - 40 - drop + wob, x0 + self.plank_w - 2, G - 40 - drop + wob, PLANK * 1.25, 2)
        # plank being carried
        if T["planks"] <= t < T["test"]:
            wh = self.m("wheels")
            if wh is not None and laid - int(laid) < 0.5:
                rect(c, wh.x + 40, G - 190 * wh.k / 0.55, wh.x + 40 + self.plank_w * 1.2, G - 178 * wh.k / 0.55, PLANK)
        # animals (back row, behind the monsters)
        for a, (kind, ax) in enumerate(self.animals):
            c0, c1 = self.animal_t(a)
            u = seg(t, c0, c1)
            x = lerp(ax, self.s0 - 330 - a * 95, smootherstep(u)) if u > 0 else ax
            y = G - 40 if self.posts_x[0] < x < self.posts_x[1] else G
            if kind == "bunny":
                hop = abs(math.sin(u * 8 * math.pi)) * 34 if 0 < u < 1 else abs(math.sin(t * 2.2 + a)) * 6 * (int(t + a) % 3 == 0)
                bunny(c, x, y, 1.0, hop, -1)
            else:
                hedgehog(c, x, y, 1.0, -1, t)
        if "lantern" in self.poses:
            ln = self.m("lantern")
            self.lantern_light(c, ln.x, ln.y - 80)
        self.draw_monsters(c, t)
        if "springs" in self.poses:
            sp = self.m("springs")
            x, y, carry = self.springs_at(t)
            if carry is not None:
                top = y - 330 * sp.k
                rect(c, x - 13, top - 150, x + 13, top, POST)
                for sxp in (-1, 1):
                    c.line(x + sxp * 50 * sp.k, y - 190 * sp.k, x + sxp * 14, top - 20, sp.color * 0.8, 10 * sp.k)
        # water in front (monsters wading are half under it)
        L2, R2 = self.s0, self.s1
        wave = [(x, self.wy + 4 * math.sin(x * 0.04 + t * 2.2)) for x in np.linspace(L2 + 20, R2 - 20, 40)]
        body = wave + [(R2 - 60, G + 200), (L2 + 60, G + 200)]
        c.polygon(body, WATER * 0.9)
        c.polyline(wave, WATER * 1.6, 3)
        s.glow_draw(lambda g: g.polyline(wave, np.array([120, 160, 220]) * 0.15, 5))
        for k in range(6):
            ph = (t * 0.4 + k * 0.19) % 1.0
            x = lerp(L2 + 60, R2 - 60, ph)
            c.line(x, self.wy + 30 + k * 18, x + 40, self.wy + 30 + k * 18, WATER * 1.4, 2)


# ====================================================================== TREEHOUSE

class TreehouseAct(ForestAct):
    """Physical build: Twigs chews logs into boards at a pile; Springs carries two at a time on real
    gravity jumps to the exact spot and puts them down (planks, then wall boards, then the two roof
    panels); Hans builds the ladder rung by rung with a tentacle, climbs up and hangs the lanterns
    within reach; Glo lights the work and then every lantern."""
    name = "treehouse"

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        d = dict(intro=7.0, place=0.35, pickup=0.45, lanterns=18.0, fireflies=8.0, inside=16.0, glow=6.0,
                 lightsout=7.0, hold=8.0)
        d.update(P.get("durations", {}))
        self.d = d
        self.tx = 1400.0                                       # trunk center
        self.py = self.G - 560                                 # platform top
        self.p0, self.p1 = 1000.0, 1800.0
        self.h0, self.h1 = 1080.0, 1640.0                      # house walls
        self.wall_top = self.py - 270
        self.ladder_x = 1880.0
        self.pile_x = 2280.0                                   # Twigs' board pile
        self.n_planks, self.n_rungs, self.n_boards = 10, 9, 10
        self.windows = [(1190, self.py - 150), (1530, self.py - 150), (1360, self.wall_top - 70)]
        self._plan(d)

    def _plan(self, d):
        """Springs' trips: pile -> spot (carrying) -> place -> back to the pile. Times fall out of the jumps."""
        G, t = self.G, d["intro"]
        self.trips = []
        pw = (self.p1 - self.p0) / self.n_planks
        bw = (self.h1 - self.h0) / self.n_boards
        jobs = [("plank", [2 * i, 2 * i + 1], self.p0 + (2 * i + 1) * pw) for i in range(self.n_planks // 2)]
        jobs += [("board", [2 * i, 2 * i + 1], self.h0 + (2 * i + 1) * bw) for i in range(self.n_boards // 2)]
        jobs += [("roof", [0], self.h0 + 60), ("roof", [1], self.h1 - 60)]
        for kind, items, x in jobs:
            up = Jump(self.pile_x - 60, G, x, self.py, apex=80)
            down = Jump(x, self.py, self.pile_x - 60, G, apex=60)
            t_up, t_land = t, t + up.dur
            t_place = t_land + d["place"] * (2.0 if kind == "roof" else 1.0)
            t_back = t_place + down.dur
            self.trips.append(dict(kind=kind, items=items, x=x, up=up, down=down, t_up=t_up, t_land=t_land,
                                   t_place=t_place, t_back=t_back))
            t = t_back + d["pickup"]
        self.placed = {}                                       # (kind, index) -> time it was put down
        for tr in self.trips:
            for i in tr["items"]:
                self.placed[(tr["kind"], i)] = tr["t_place"] if tr["kind"] == "roof" else tr["t_land"]
        T = {"intro": 0.0, "build": d["intro"], "walls": self.trips[self.n_planks // 2]["t_up"],
             "roof": self.trips[-2]["t_up"], "build_end": t}
        # the ladder goes up (Hans) while the walls are going up
        T["ladder"] = T["walls"]
        T["ladder_end"] = T["walls"] + 7.0
        t = max(t, T["ladder_end"]) + 1.0
        for k in ("lanterns", "fireflies", "inside", "glow", "lightsout", "hold"):
            T[k] = t
            t += d[k]
        self.T, self.dur = T, t

    def lantern_pos(self, i):
        """Lanterns hang along the big branches around the house, all within Hans' reach from the platform."""
        x = 820 + i * 170
        y = self.py - 330 - 60 * math.sin(i * 0.9 + 0.4) - 0.00012 * (x - self.tx) ** 2
        return x, y

    def hang_time(self, k):
        T, d = self.T, self.d
        return T["lanterns"] + 2.0 + (k + 0.6) * (d["lanterns"] * 0.5 - 2.0) / 8

    def lit_time(self, k):
        T, d = self.T, self.d
        return T["lanterns"] + d["lanterns"] * 0.45 + (k + 0.7) * d["lanterns"] * 0.55 / 8

    def rung_time(self, k):
        return self.T["ladder"] + 0.8 + (k + 0.5) * (self.T["ladder_end"] - self.T["ladder"] - 0.8) / self.n_rungs

    def target(self, t):
        T, h = self.T, self.s.h
        if t < T["build"]:
            u = smootherstep(seg(t, 0, T["build"]))
            return lerp(600, self.tx + 300, u), lerp(self.G - h * 0.3, self.py + 90, u), lerp(1.1, 0.88, u)
        if t < T["lanterns"]:
            return self.tx + 300, self.py + 90, 0.88
        if t < T["hold"]:
            return self.tx + 160, self.py + 40, 0.82
        u = smootherstep(seg(t, T["hold"], self.dur))
        return self.tx + 160, lerp(self.py + 40, self.py - 40, u), lerp(0.82, 0.74, u)

    # ----- who is where -----

    def springs_state(self, t):
        """(x, feet y, carrying trip or None, airborne)"""
        G = self.G
        home = self.pile_x - 60
        for tr in self.trips:
            if tr["t_up"] <= t < tr["t_land"]:
                x, y = tr["up"].at(t - tr["t_up"])
                return x, y, tr, True
            if tr["t_land"] <= t < tr["t_place"]:
                return tr["x"], self.py, tr if tr["kind"] == "roof" else None, False
            if tr["t_place"] <= t < tr["t_back"]:
                x, y = tr["down"].at(t - tr["t_place"])
                return x, y, None, True
        if t < self.T["build"]:
            return lerp(-700, home, smootherstep(seg(t, 1.0, self.T["build"] - 0.5))), G, None, False
        if t < self.T["build_end"] + 1.0:
            return home, G, None, False
        return lerp(home, 2050, smootherstep(seg(t, self.T["build_end"], self.T["build_end"] + 2))), G, None, False

    def hans_state(self, t):
        """(x, feet y, reach target or None)"""
        T, G = self.T, self.G
        if t < T["ladder"]:
            return lerp(-900, 2100, smootherstep(seg(t, 1.4, T["build"] + 1))), G, None
        if t < T["ladder_end"]:
            x = lerp(2100, self.ladder_x + 140, smootherstep(seg(t, T["ladder"], T["ladder"] + 0.8)))
            k = min(self.n_rungs - 1, max(0, int((t - T["ladder"] - 0.8) / ((T["ladder_end"] - T["ladder"] - 0.8) / self.n_rungs))))
            return x, G, (self.ladder_x, self.rung_y(k))
        if t < T["lanterns"]:
            return self.ladder_x + 140, G, None
        # climb the ladder, then walk along the platform hanging lanterns
        u = seg(t, T["lanterns"], T["lanterns"] + 2.0)
        if u < 1:
            if u < 0.25:
                return lerp(self.ladder_x + 140, self.ladder_x, u / 0.25), G, None
            return self.ladder_x, lerp(G, self.py, smootherstep((u - 0.25) / 0.75)), None
        k = min(7, int((t - T["lanterns"] - 2.0) / ((self.d["lanterns"] * 0.5 - 2.0) / 8)))
        lx, ly = self.lantern_pos(k)
        x = float(np.clip(lx, self.p0 + 70, self.p1 - 70))
        if t < self.T["lanterns"] + self.d["lanterns"] * 0.5:
            return x, self.py, (lx, ly - 40)
        return x, self.py, None

    def rung_y(self, k):
        return self.G - (k + 1) * (self.G - self.py) / (self.n_rungs + 1)

    def update(self, t, dt):
        T, d, s, P = self.T, self.d, self.s, self.s.particles
        G = self.G
        # Springs: the carrier
        sp = self.m("springs")
        if sp is not None:
            x, y, carry, air = self.springs_state(t)
            sp.spring = 0.0
            for tr in self.trips:                               # squash on take-off and landing
                for tk in (tr["t_up"], tr["t_land"], tr["t_place"], tr["t_back"]):
                    if abs(t - tk) < 0.12:
                        sp.spring = 0.8 * (1 - abs(t - tk) / 0.12)
            self.place(sp, x, t, dt, y=y, walk=0.0)
        # Twigs: chews logs into boards at the pile
        tw = self.m("teeth")
        if tw is not None:
            ang = 0.22 * (0.5 + 0.5 * math.sin(t * 13)) if T["build"] - 1 <= t < T["build_end"] else 0.0
            x = lerp(-1000, self.pile_x + 150, smootherstep(seg(t, 0.6, T["build"] - 0.5)))
            if T["build"] - 1 <= t < T["build_end"] and P.rng.uniform() < 0.5:
                P.burst(self.pile_x + 90, G - 60, 2, SAWDUST, 300, 0.6, 3.5, g=1000, spread=1.0)
            self.place(tw, x, t, dt, ang=ang)
        # Hans: ladder rungs, then lanterns from the platform
        hn = self.m("tentacles")
        if hn is not None:
            x, y, reach = self.hans_state(t)
            self.hans_reach = reach
            if t >= T["inside"]:
                y = self.py
            self.place(hn, x, t, dt, y=y)
        # Glo: lights the spot where Springs is building, then lights the lanterns
        gl = self.m("lantern")
        if gl is not None:
            if t < T["build_end"]:
                cur = next((tr for tr in self.trips if t < tr["t_back"] + d["pickup"]), self.trips[-1])
                x, y = lerp(-600, cur["x"], smootherstep(seg(t, 0.3, T["build"]))) if t < T["build"] else cur["x"], self.py - 280
            elif t < T["lanterns"] + d["lanterns"] * 0.45:
                x, y = self.tx + 500, self.py - 250
            elif t < T["fireflies"]:
                k = min(7, int(seg(t, T["lanterns"] + d["lanterns"] * 0.45, T["fireflies"]) * 8))
                lx, ly = self.lantern_pos(k)
                x, y = lx, ly + 220
            else:
                x, y = self.tx + 650, self.py - 60
            self.place(gl, x, t, dt, y=y)
        # Wheels and Digs: the cheering section by the pile
        for kind, home, q in (("wheels", 2560, 0), ("digger", 2760, 1)):
            m = self.m(kind)
            if m is None:
                continue
            x = lerp(-800 - q * 250, home, smootherstep(seg(t, 0.2 + q * 0.4, T["build"])))
            dy = -abs(math.sin(t * 7)) * 18 if T["build_end"] <= t < T["build_end"] + 1.5 else 0.0
            self.place(m, x, t, dt, dy=dy)
        # going inside, one by one (up the ladder; Springs bounces, Glo floats)
        door_x = self.h1 - 70
        for q, kind in enumerate(["wheels", "tentacles", "teeth", "springs", "lantern", "digger"]):
            m = self.m(kind)
            gi = T["inside"] + q * (d["inside"] - 2) / 6
            if m is None or t < gi:
                continue
            u = seg(t, gi, gi + 2.2)
            x0 = m.x if u == 0 else getattr(m, "_x_in", m.x)
            if u <= 0.02:
                m._x_in = m.x
            x0 = m._x_in
            y = None
            if kind == "tentacles":
                x, y = lerp(x0, door_x, smootherstep(u)), self.py
            elif kind == "lantern":
                x, y = lerp(x0, door_x, smootherstep(u)), lerp(self.py - 60, self.py - 160, u)
            elif kind == "springs":
                j = Jump(x0, G, door_x - 40, self.py, apex=70)
                x, y = j.at(u * 2.2 if u * 2.2 < j.dur else j.dur)
                x = x if u * 2.2 < j.dur else lerp(door_x - 40, door_x, smoothstep((u * 2.2 - j.dur) / max(0.01, 2.2 - j.dur)))
            elif u < 0.35:
                x = lerp(x0, self.ladder_x, smootherstep(u / 0.35))
            elif u < 0.8:
                x, y = self.ladder_x, lerp(G, self.py, smootherstep((u - 0.35) / 0.45))
            else:
                x, y = lerp(self.ladder_x, door_x, smootherstep((u - 0.8) / 0.2)), self.py
            if u >= 1:
                self.poses.pop(kind, None)
                continue
            self.place(m, x, t, dt, y=y)
        self._sounds(t)
        if T["fireflies"] <= t < self.dur - 1:
            rate = 0.5 if t < T["inside"] else 0.25
            if P.rng.uniform() < rate:
                P.items.append(_firefly(P.rng, self.tx, self.py, self.G))
        self.stats = {"treehouse_trips": len(self.trips), "treehouse_lanterns": 8}

    def _sounds(self, t):
        T, d, s, P = self.T, self.d, self.s, self.s.particles
        n = 0
        for tr in self.trips:
            if self.crossed(tr["t_up"]):
                self.hit(t, "boing", s.note(n % 5, -1), 0.5, tr["x"], self.G)
            if self.crossed(tr["t_land"]):
                self.hit(t, "thud", 44, 0.4, tr["x"], self.py)
                for k, i in enumerate(tr["items"]):
                    if tr["kind"] != "roof":
                        self.hit(t + k * 0.12, "clunk", s.note(n + k), 0.5, tr["x"], self.py)
                P.burst(tr["x"], self.py, 6, SAWDUST * 0.7, 160, 0.5, 3, g=900, spread=1.2)
            if tr["kind"] == "roof" and self.crossed(tr["t_place"]):
                self.hit(t, "clunk", s.note(n), 0.6, tr["x"], self.wall_top)
            if self.crossed(tr["t_place"]):
                self.hit(t, "boing", s.note(n % 5 + 2, -1), 0.35, tr["x"], self.py)
            n += 1
        if self.crossed(T["build_end"] + 0.2):
            for q, kind in enumerate(("wheels", "digger", "teeth", "springs")):
                self.say(t + q * 0.18, kind, "cheer", self.pile_x, self.G, 0.5)
        for k in range(self.n_rungs):
            if self.crossed(self.rung_time(k)):
                self.hit(t, "clack", s.note(k, 0), 0.35, self.ladder_x, self.rung_y(k))
        for k in range(8):
            if self.crossed(self.hang_time(k)):
                self.hit(t, "clack", s.note(k, 0), 0.3, self.lantern_pos(k)[0], self.lantern_pos(k)[1])
            if self.crossed(self.lit_time(k)):
                self.hit(t, "bloop", s.note(k, 0), 0.4, self.lantern_pos(k)[0], self.lantern_pos(k)[1])
                self.hit(t + 0.05, "chime", s.note(k), 0.4, self.lantern_pos(k)[0], self.lantern_pos(k)[1])
                lx, ly = self.lantern_pos(k)
                P.burst(lx, ly, 10, LAMP, 120, 0.7, 3, g=0, glow=True)
        if self.crossed(T["fireflies"]):
            for k, nn in enumerate((0, 2, 4, 7, 9)):
                self.hit(t + k * 0.35, "soft_bell", s.note(nn % 8, nn // 8), 0.4, self.tx, self.py - 300)
            self.say(t + 2.0, "lantern", "hum", self.tx, self.py, 0.45)
        order = ["wheels", "tentacles", "teeth", "springs", "lantern", "digger"]
        for q, kind in enumerate(order):
            gi = T["inside"] + q * (d["inside"] - 2) / 6
            if self.crossed(gi + 0.2):
                self.say(t, kind, "up", self.ladder_x, self.G, 0.45)
                if kind == "springs":
                    self.hit(t + 0.1, "boing", s.note(2), 0.5, self.ladder_x, self.G)
                elif kind not in ("lantern", "tentacles"):
                    for k in range(4):
                        self.hit(t + 0.8 + k * 0.28, "clack", s.note(q + k, -1), 0.25, self.ladder_x, self.py)
            if self.crossed(gi + 2.2):
                self.hit(t, "pluck", s.note(q + 2, 0), 0.35, self.h1, self.py)
        for k in range(len(self.windows)):
            if self.crossed(T["glow"] + k * 0.4):
                self.hit(t, "soft_bell", s.note(k * 2, 0), 0.4, self.windows[k][0], self.windows[k][1])
            if self.crossed(T["lightsout"] + 1.0 + k * 1.6):
                self.hit(t, "soft_bell", s.note(4 - k * 2, -1), 0.3, self.windows[k][0], self.windows[k][1])
        if self.crossed(T["lightsout"] + 0.4):
            self.say(t, "springs", "down", self.h1, self.py, 0.3)          # a sleepy yawn from inside

    # ----- drawing -----

    def _shown(self, kind, i, t):
        tp = self.placed.get((kind, i))
        return None if tp is None or t < tp else t - tp

    def draw(self, c, t):
        s, T, d, G = self.s, self.T, self.d, self.G
        self.backdrop(c, t)
        wood_sign(c, 300, G, "HOME", lit=1.0, glow_fn=s.glow_draw)
        for j, x in enumerate((-400, 120, 2900, 3350)):
            if s.visible(x - 250, x + 250):
                tree(c, x, G, 640 + 50 * (j % 2), 900 + j)
        # the huge old tree, with two flat branch stubs + braces that carry the platform
        tx = self.tx
        c.polygon([(tx - 130, G), (tx + 130, G), (tx + 90, G - 1050), (tx - 90, G - 1050)], TRUNK)
        for k in (-1, 1):
            c.polygon([(tx + k * 120, G), (tx + k * 220, G + 4), (tx + k * 100, G - 80)], TRUNK * 0.9)
        c.line(tx - 30, G, tx - 20, G - 1000, BARK, 6)
        c.line(tx + 40, G - 100, tx + 30, G - 900, BARK, 4)
        for (bx, by), (ex, ey) in (((tx - 60, G - 760), (tx - 640, G - 980)), ((tx + 60, G - 800), (tx + 620, G - 1010)),
                                   ((tx, G - 980), (tx - 300, G - 1250)), ((tx, G - 980), (tx + 320, G - 1260))):
            c.line(bx, by, ex, ey, TRUNK, 34)
        rs = np.random.default_rng(42)
        for k in range(16):
            cx = tx + rs.uniform(-750, 750)
            cy = G - 1150 - rs.uniform(-120, 260) - 200 * math.cos((cx - tx) / 1500 * math.pi)
            c.circle(cx, cy, rs.uniform(170, 260), LEAF[k % 3] * 0.85)
        for xk in (self.p0 + 60, self.p1 - 60):
            c.line(tx + (60 if xk > tx else -60), self.py + 120, xk, self.py + 14, TRUNK * 0.9, 16)
        c.line(self.p0 + 20, self.py + 18, self.p1 - 20, self.py + 18, TRUNK * 0.85, 12)     # joist
        # board pile at Twigs' feet (made faster than Springs takes them)
        if T["build"] - 1 <= t < T["build_end"] + 0.5:
            made = int(seg(t, T["build"] - 1, T["build_end"] - 3) * len(self.trips)) + 2
            taken = sum(1 for tr in self.trips if t >= tr["t_up"])
            for k in range(max(0, min(5, made - taken))):
                rect(c, self.pile_x - 70, G - 14 - k * 13, self.pile_x + 70, G - 3 - k * 13, PLANK * (0.9 + 0.1 * (k % 2)))
        # platform planks (put down where Springs landed)
        pw = (self.p1 - self.p0) / self.n_planks
        for k in range(self.n_planks):
            a = self._shown("plank", k, t)
            if a is not None:
                drop = 10 * (1 - settle(min(1.0, a / 0.2), 0.1))
                x0 = self.p0 + k * pw
                rect(c, x0 + 2, self.py - drop, x0 + pw - 2, self.py + 16 - drop, PLANK)
        # ladder (Hans' tentacle sets each rung)
        lx = self.ladder_x
        n_r = sum(1 for k in range(self.n_rungs) if t >= self.rung_time(k))
        if t >= T["ladder"] + 0.6:
            hh = smoothstep(seg(t, T["ladder"] + 0.2, T["ladder"] + 0.8))
            c.line(lx - 34, G, lx - 34, lerp(G, self.py, hh), PLANK * 0.8, 8)
            c.line(lx + 34, G, lx + 34, lerp(G, self.py, hh), PLANK * 0.8, 8)
            for k in range(n_r):
                c.line(lx - 34, self.rung_y(k), lx + 34, self.rung_y(k), PLANK, 7)
        # wall boards: stood up where Springs put them
        bw = (self.h1 - self.h0) / self.n_boards
        for k in range(self.n_boards):
            a = self._shown("board", k, t)
            if a is not None:
                rise = smootherstep(min(1.0, a / 0.3))
                x0 = self.h0 + k * bw
                top = lerp(self.py - 60, self.wall_top, rise)
                rect(c, x0 + 1, top, x0 + bw - 1, self.py, PLANK * (0.78 + 0.07 * (k % 2)))
                c.line(x0 + 1, top, x0 + 1, self.py, PLANK * 0.6, 2)
        walls_done = self._shown("board", self.n_boards - 1, t)
        win = smoothstep((walls_done or 0) / 0.6) if walls_done is not None else 0.0
        glow_amt = smoothstep(seg(t, T["glow"], T["glow"] + 2.0))
        for k, (wx, wy) in enumerate(self.windows[:2]):
            if win > 0:
                off = smoothstep(seg(t, T["lightsout"] + 1.0 + k * 1.6, T["lightsout"] + 1.6 + k * 1.6))
                lit = glow_amt * (1 - off)
                c.circle(wx, wy, 46 * win, np.array([20, 18, 20]) + LAMP * 0.85 * lit)
                c.circle(wx, wy, 46 * win, PLANK * 0.55, False, 6)
                c.line(wx - 46 * win, wy, wx + 46 * win, wy, PLANK * 0.55, 4)
                c.line(wx, wy - 46 * win, wx, wy + 46 * win, PLANK * 0.55, 4)
                if lit > 0:
                    s.glow_draw(lambda g, wx=wx, wy=wy, lit=lit: g.circle(wx, wy, 70, LAMP * 0.55 * lit))
        if win > 0:
            rect(c, self.h1 - 110, self.py - 170, self.h1 - 30, self.py, np.array([50, 36, 28]) + LAMP * 0.4 * glow_amt)
        # roof panels: Springs lifts each one from the platform onto the wall top
        ridge = ((self.h0 + self.h1) / 2, self.wall_top - 190)
        for k, sgn in enumerate((-1, 1)):
            tr = self.trips[-2 + k]
            if t < tr["t_land"]:
                continue
            u = smootherstep(seg(t, tr["t_land"], tr["t_place"]))
            eave = (self.h0 - 70 if sgn < 0 else self.h1 + 70, self.wall_top + 10)
            dyo = -120 * (1 - u)
            pts = [(ridge[0], ridge[1] + dyo), (eave[0], eave[1] + dyo), (eave[0], eave[1] + 24 + dyo),
                   (ridge[0], ridge[1] + 24 + dyo)]
            if u < 1:                                              # still in Springs' arms
                sx_ = self.m("springs").x if self.m("springs") else tr["x"]
                off = sx_ - (ridge[0] + eave[0]) / 2
                pts = [(p[0] + off * (1 - u), p[1]) for p in pts]
            c.polygon(pts, ROOF)
            c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], ROOF * 1.4, 3)
        if self._shown("roof", 1, t) is not None:
            wx, wy = self.windows[2]
            off = smoothstep(seg(t, T["lightsout"] + 1.0 + 2 * 1.6, T["lightsout"] + 1.6 + 2 * 1.6))
            lit = glow_amt * (1 - off)
            c.polygon([(self.h0 + 10, self.wall_top), (self.h1 - 10, self.wall_top), (ridge[0], self.wall_top - 170)],
                      PLANK * 0.7)
            c.circle(wx, wy, 30, np.array([20, 18, 20]) + LAMP * 0.85 * lit)
            c.circle(wx, wy, 30, PLANK * 0.5, False, 5)
            if lit > 0:
                s.glow_draw(lambda g, wx=wx, wy=wy, lit=lit: g.circle(wx, wy, 50, LAMP * 0.5 * lit))
        # lanterns: each hung by Hans, then lit by Glo
        for k in range(8):
            if t < self.hang_time(k):
                continue
            lx_, ly_ = self.lantern_pos(k)
            if k > 0:
                px, py = self.lantern_pos(k - 1)
                c.line(px, py - 40, lx_, ly_ - 40, np.array([60, 52, 40]), 2)
            lit = smoothstep(seg(t, self.lit_time(k), self.lit_time(k) + 0.5))
            sway = 0.08 * math.sin(t * 1.4 + k) + 0.25 * math.exp(-(t - self.hang_time(k)) * 3) * math.sin((t - self.hang_time(k)) * 9)
            lc = Xform(c, ang=sway, px=lx_, py=ly_ - 40)
            lc.line(lx_, ly_ - 40, lx_, ly_ - 20, np.array([60, 52, 40]), 2)
            lc.polygon([(lx_ - 14, ly_ - 20), (lx_ + 14, ly_ - 20), (lx_ + 17, ly_ + 14), (lx_ - 17, ly_ + 14)],
                       np.array([50, 50, 46]) + LAMP * 0.85 * lit)
            if lit > 0:
                s.glow_draw(lambda g, lx_=lx_, ly_=ly_, lit=lit: g.circle(lx_, ly_ - 2, 36, LAMP * 0.6 * lit))
        if "lantern" in self.poses:
            ln = self.m("lantern")
            self.lantern_light(c, ln.x, ln.y - 80, k=0.7)
        self.draw_monsters(c, t)
        self._draw_carried(c, t)

    def _draw_carried(self, c, t):
        """What the monsters are holding: Springs' boards overhead, Hans' tentacle reaching for a rung or hook."""
        sp = self.m("springs")
        if sp is not None and "springs" in self.poses:
            x, y, carry, air = self.springs_state(t)
            if carry is not None and carry["kind"] != "roof":
                dy = self.poses["springs"][0]
                top = sp.y + dy - 330 * sp.k
                vertical = carry["kind"] == "board"
                for k in range(len(carry["items"])):
                    if vertical:
                        rect(c, x - 30 + k * 30, top - 150, x - 4 + k * 30, top + 10, PLANK * 0.85)
                    else:
                        rect(c, x - 45, top - 8 - k * 15, x + 45, top + 4 - k * 15, PLANK)
                for sxp in (-1, 1):
                    c.line(x + sxp * 50 * sp.k, sp.y + dy - 190 * sp.k, x + sxp * 36, top + 4, sp.color * 0.8, 10 * sp.k)
            elif carry is not None:                               # roof panel overhead on the way up
                top = sp.y + self.poses["springs"][0] - 330 * sp.k
                c.polygon([(x - 120, top), (x + 120, top - 40), (x + 120, top - 18), (x - 120, top + 22)], ROOF)
        hn = self.m("tentacles")
        reach = getattr(self, "hans_reach", None)
        if hn is not None and reach is not None and "tentacles" in self.poses:
            bx, by = hn.x, hn.y + self.poses["tentacles"][0] - 300 * hn.k
            tx_, ty_ = reach
            mid = ((bx + tx_) / 2 + 40, (by + ty_) / 2 - 40)
            pts = [(bx, by), mid, (tx_, ty_)]
            for w, col in ((14, hn.color * 0.75), (6, hn.color * 1.05)):
                c.polyline(pts, col, w)
            c.circle(tx_, ty_, 9, hn.color)


def _firefly(rng, tx, py, G):
    from .common import Particle
    x = tx + rng.uniform(-1100, 1100)
    y = G - rng.uniform(20, 300)
    return Particle(x, y, rng.uniform(-20, 20), rng.uniform(-60, -20), rng.uniform(5, 9), rng.uniform(5, 8),
                    FIREFLY, "firefly", -8.0, True)
