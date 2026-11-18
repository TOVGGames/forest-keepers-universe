"""The end card of every Forest Keepers video (owner, 2026-10-27): a wooden sign drops down on two ropes from a
branch and hangs there for the last ~8 seconds, asking viewers to comment their idea for the next episode, while
the Keepers (six, seven from the factory-trip episode) stand in a neat row underneath and wave.

Two equal ropes from two points on a level branch make a parallelogram, so the sign swings on an arc but stays
level (text never tilts), as a real pendulum: omega = sqrt(g / L) with the scene's g, gently damped.
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, PLANK, lerp, rect, seg, settle, smoothstep, smootherstep
from families.foundry.keepers.forest import FIREFLY, _firefly
from families.foundry.keepers.halloween import KeeperAct
from families.foundry.tree_monsters import BARK, LAMP, LEAF, TRUNK

from . import snow as SN

SIGN_WOOD = np.array([136, 98, 62], np.float64)
CARVE = np.array([250, 236, 204], np.float64)
ROPE = np.array([150, 128, 92], np.float64)

LINES = [("WHAT SHOULD THEY BUILD NEXT?", 76), ("Comment your idea below!", 64),
         ("We'll pick one for the next episode", 46)]


class CommentSignAct(KeeperAct):
    name = "comment_sign"
    names = (1.6, 99.0)                     # nameplates stay up, so people can name their favourite Keeper
    bubbles = False                         # they cheer and look at us, but no speech bubbles over the names

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        G = self.G
        self.dur = P.get("duration", 10.0)
        # owner after FK0008: when the Keepers didn't build anything, "build" is the wrong word (params end_sign_text)
        head = scene.p.get("end_sign_text")
        self.lines = [(head, LINES[0][1])] + LINES[1:] if head else LINES
        self.cx = 960.0
        self.branch_y = G - 1040.0
        self.hooks = (self.cx - 600.0, self.cx + 600.0)
        self.L = 190.0                       # rope length once it has dropped
        self.w, self.h = 1440.0, 330.0
        self.zoom = 0.92
        self.drop = (0.5, 1.5)               # the sign unrolls down on its ropes
        self.omega = math.sqrt(GRAVITY / self.L)
        self.order = ["digger", "wheels", "tentacles", "teeth", "springs", "lantern"]
        # a snowy episode (it has a Snowfall) gets a snowy end card too
        self.snow = getattr(scene, "snowfall", None) is not None
        if self.snow:
            self.night = SN.SnowNight(np.random.default_rng(scene.seed + 62), G, -2500, 4000)
            self.night.depth = 30.0
        if "sprout" in scene.by_kind:            # the seventh Keeper (from the factory-trip episode): in the middle,
            self.order.insert(3, "sprout")       # short enough for Hans' waving tentacle to pass over
        mid, gap = (len(self.order) - 1) / 2, (262 if len(self.order) <= 6 else 236)
        self.row = {k: self.cx + (i - mid) * gap for i, k in enumerate(self.order)}

    def target(self, t):
        return self.cx, self.G - self.s.h * 0.42 / self.zoom, self.zoom

    def sign_pos(self, t):
        """(x offset, rope length) of the hanging sign."""
        d0, d1 = self.drop
        u = seg(t, d0, d1)
        L = self.L * settle(u, 0.18) if u < 1 else self.L
        if t < d1:
            return 0.0, max(0.0, L)
        tau = t - d1
        amp = 26.0 * math.exp(-tau / 2.6)
        return amp * math.sin(self.omega * tau), self.L

    def update(self, t, dt):
        G, s = self.G, self.s
        self.reach = {}
        for q, kind in enumerate(self.order):
            m = self.m(kind)
            if m is None:
                continue
            x, y, dy = self.row[kind], None, 0.0
            m.punch = 0.0
            if kind == "lantern":
                y = G - 70
            if kind == "springs":                          # a little happy hop now and then
                ph = (t - 2.2) % 2.6
                if t > 2.2 and ph < 0.42:
                    dy = -4 * 70 * (ph / 0.42) * (1 - ph / 0.42)
                    m.spring = 0.6 if ph < 0.06 or ph > 0.36 else 0.0
                else:
                    m.spring = 0.0
            if kind == "wheels":                            # waves a claw
                m.punch = 0.5 + 0.5 * math.sin(t * 5.0) if 2.0 < t < 6.0 else 0.0
            if kind == "teeth":
                m.saws, m.saw_run = True, 0.0
            if kind == "tentacles" and t > self.drop[1] - 0.2:
                # one tentacle swings up and waves hello: the same length all the way (it turns about its root,
                # never stretches; advisor FK0022 r2), the tip no higher than his head
                k = m.k
                rx, ry = m.x + 51 * k, G - 237 * k                 # its root under his head (work_tentacle slot 0.5)
                u = smoothstep(seg(t, self.drop[1] - 0.2, self.drop[1] + 0.8))
                a = lerp(math.radians(60), math.radians(-38), u) + u * math.radians(11) * math.sin(t * 3.2)
                L = 118 * k
                self.reach["tentacles"] = [(rx + L * math.cos(a), ry + L * math.sin(a))]
            self.place(m, x, t, dt, y=y, dy=dy)
        if s.particles.rng.uniform() < 0.12 and not self.snow:      # fireflies (not in the snow)
            s.particles.items.append(_firefly(s.particles.rng, self.cx, G - 500, G))
        self._sounds(t)

    def _sounds(self, t):
        d0, d1 = self.drop
        if self.crossed(d0):
            self.fx(t, "creak", d1 - d0, 0.35, self.cx, self.branch_y)
        if self.crossed(d1 - 0.05):
            self.hit(t, "clunk", 48, 0.35, self.cx, self.branch_y + self.L)
            for i, n in enumerate((72, 76, 79, 84)):
                self.hit(t + 0.15 + i * 0.12, "chime", n, 0.28, self.cx + (i - 1.5) * 200, self.branch_y + self.L)
        if self.crossed(d1 + 0.6):
            for q, kind in enumerate(self.order):
                self.say(t + q * 0.16, kind, "cheer", self.row[kind], self.G - 200, 0.4)
        ph = 2.2
        while ph < self.dur - 1.0:
            if self.crossed(ph):
                self.hit(t, "boing", 55, 0.25, self.row["springs"], self.G)
            ph += 2.6

    def draw(self, c, t):
        s, G = self.s, self.G
        self.backdrop(c, t)
        if self.snow:
            s.snowfall.draw(c, s, self.t0 + t, 0.4)
            SN.ground(c, s, G, 30.0)
        # the tree on the left and its long level branch across the top
        tx = self.cx - 820
        c.polygon([(tx - 110, G), (tx + 110, G), (tx + 80, self.branch_y - 260), (tx - 80, self.branch_y - 260)],
                  TRUNK)
        c.line(tx - 20, G, tx - 10, self.branch_y - 200, BARK, 5)
        br = [(tx + 40, self.branch_y + 30)] + [(x, self.branch_y + 6 * math.sin((x - tx) / 400))
                                               for x in np.linspace(tx + 200, self.cx + 900, 14)]
        c.polyline(br, TRUNK, 34)
        c.polyline([(x, y - 6) for x, y in br], BARK, 3)
        rs = np.random.default_rng(55)
        leaves = []
        for k in range(14):
            lx = tx + rs.uniform(-300, 1900)
            ly, lr = self.branch_y - rs.uniform(110, 260), rs.uniform(150, 230)
            c.circle(lx, ly, lr, LEAF[k % 3] * 0.8)
            leaves.append((lx, ly, lr))
        if self.snow:
            for lx, ly, lr in sorted(leaves, key=lambda q: q[1]):
                SN.cap_circle(c, lx, ly, lr, 26)
            SN.cap_line(c, [(x, y - 17) for x, y in br[1:]], 14, overhang=0.3)
        # sign: two ropes, a plank board with carved letters, a lantern hanging at each top corner
        dx, L = self.sign_pos(t)
        if L > 2:
            top = self.branch_y + L
            x0, x1 = self.cx + dx - self.w / 2, self.cx + dx + self.w / 2
            for hx in self.hooks:
                c.line(hx, self.branch_y + 8, hx + dx, top + 10, ROPE, 5)
                c.circle(hx, self.branch_y + 6, 9, ROPE * 0.8)
            rect(c, x0, top, x1, top + self.h, SIGN_WOOD)
            if self.snow:
                SN.cap_flat(c, x0, x1, top, 16)
            for k in range(1, 4):                                  # board seams
                yy = top + k * self.h / 4
                c.line(x0 + 6, yy, x1 - 6, yy, SIGN_WOOD * 0.78, 3)
            c.polyline([(x0, top), (x1, top), (x1, top + self.h), (x0, top + self.h)], SIGN_WOOD * 0.55, 6,
                       closed=True)
            for hx in self.hooks:                                  # nails where the ropes hold
                c.circle(hx + dx, top + 14, 7, np.array([90, 90, 96]))
            ys = (top + 84, top + 182, top + 266)
            for (text, size), yy in zip(self.lines, ys):
                c.text(text, self.cx + dx + 1.5, yy + 2.5, size, SIGN_WOOD * 0.45)       # carved shadow
                c.text(text, self.cx + dx, yy, size, CARVE)
            # a little arrow pointing down (to the comments)
            ax, ay = x1 - 100, top + self.h - 90
            bob = 6 * math.sin(t * 3.0)
            c.polygon([(ax - 18, ay - 36 + bob), (ax + 18, ay - 36 + bob), (ax + 18, ay + bob), (ax + 36, ay + bob),
                       (ax, ay + 40 + bob), (ax - 36, ay + bob), (ax - 18, ay + bob)], CARVE)
            for k, hx in enumerate(self.hooks):
                lx, ly = hx + dx + (-150 if k == 0 else 150), top - 6
                c.line(lx, self.branch_y + 8, lx, ly, ROPE * 0.8, 3)
                c.line(lx, ly, lx, ly + 34, ROPE * 0.8, 3)
                c.polygon([(lx - 16, ly + 34), (lx + 16, ly + 34), (lx + 19, ly + 72), (lx - 19, ly + 72)],
                          np.array([50, 50, 46]) + LAMP * 0.85)
                s.glow_draw(lambda g, lx=lx, ly=ly: g.circle(lx, ly + 52, 46, LAMP * 0.55))
            s.glow_draw(lambda g: g.polygon([(x0, top), (x1, top), (x1, top + self.h), (x0, top + self.h)],
                                            LAMP * 0.05))
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 120, k=0.8)
        self.draw_monsters(c, t)
        if self.snow:
            SN.front_lip(c, s, G, 30.0)
            s.snowfall.draw(c, s, self.t0 + t, 0.4, near=True)
