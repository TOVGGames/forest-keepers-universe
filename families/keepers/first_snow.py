"""Forest Keepers episode 5: First Snow (docs/engines/forest_keepers_first_snow.md).

  FIRST_SNOW - the first snow falls on the treehouse and the animals' new houses; the Keepers catch flakes,
               Wheels gets stuck, Twigs has an idea (a speech bubble with a sled in it).
  SLEDS      - the sled workshop at the foot of the hill: Twigs saws the slats (Wheels feeds the plank against
               a stop block), Hans steam-bends the runners two at a time, Springs pegs the slats on, Glo paints,
               Hans ties the rope. Three sleds, one per pair of Keepers, in their colours.
  HILL       - Digs packs three lanes, Glo lights the lanterns up the run, everyone pulls the sleds up.
  RACE       - the countdown, then three sleds side by side down the long hill (real sled physics), a photo
               finish into the soft snowbank.
  COZY       - back at the treehouse in the falling snow.
The Keepers talk (chatter.py): every act asks for voices at its story beats; quiet stretches get asides.
"""
import math

import numpy as np

from families.foundry.keepers.common import (GRAVITY, Jump, PLANK, bunny, ellipse, hedgehog, lerp, rect, seg,
                                             smoothstep, smootherstep)
from families.foundry.keepers.halloween import KeeperAct, hops, path
from families.foundry.style import IRON, lighten
from families.foundry.tree_monsters import BARK, LAMP, LEAF, TRUNK

from . import props as PR
from . import sled as SL
from . import snow as SN
from .animal_houses import BIRD_COLS, BUNNY_X, HEDGE_X, POST, POST_TOP, POSTS, _ease, bez

G = 1000.0
KEEPERS = ["lantern", "tentacles", "teeth", "springs", "wheels", "digger"]
# where everyone stood at the end of episode 4, in front of the treehouse
HOME = {"lantern": 1180.0, "tentacles": 1350.0, "teeth": 1530.0, "springs": 1690.0, "wheels": 1850.0,
        "digger": 1990.0}
# the three sleds: (riders front-to-back, colour = the front rider's), lane
SLEDS = [(("wheels", "digger"), (78, 140, 214)), (("springs", "tentacles"), (232, 178, 56)),
         (("lantern", "teeth"), (64, 186, 170))]


def cam(h, x, z, gf=0.84, ground=G):
    """Camera keyframe: centre x, zoom, with the ground at fraction gf of the screen height."""
    return x, ground - (gf - 0.5) * h / z, z


class SnowAct(KeeperAct):
    """A snowy Forest Keepers act: snow on everything, flakes falling, the Keepers talk (act.chat)."""
    depth0, depth1 = 26.0, 28.0            # settled snow at the start / end of the act
    fall0, fall1 = 0.55, 0.55              # how hard it snows at the start / end

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.night = SN.SnowNight(np.random.default_rng(scene.seed + 61), self.G, -2500, 50000)
        if not hasattr(scene, "snowfall"):
            scene.snowfall = SN.Snowfall(scene.seed)

    def place(self, m, x, t, dt, k=None, **kw):
        """As KeeperAct.place; k scales the Keeper (further lanes on the hill look smaller)."""
        if m is not None:
            m.k = self.s.k * (1.0 if k is None else k)
        super().place(m, x, t, dt, **kw)

    # ----- talking -----

    def chat(self, t, kind, mood, **kw):
        self.s.chatter.say(self.t0 + t, kind, mood, **kw)

    def chorus(self, t, kinds, mood, gap=0.2, **kw):
        self.s.chatter.chorus(self.t0 + t, kinds, mood, gap=gap, **kw)

    # ----- weather -----

    def depth(self, t):
        return lerp(self.depth0, self.depth1, seg(t, 0, self.dur))

    def fall(self, t):
        return lerp(self.fall0, self.fall1, seg(t, 0, self.dur))

    def backdrop(self, c, t):
        self.night.depth = self.depth(t)
        self.night.draw(self.s, c, t)
        self.night.ground_slab(self.s, c)
        self.s.snowfall.draw(c, self.s, self.t0 + t, self.fall(t) * 0.7)

    def snow_ground(self, c, t, x1=None):
        SN.ground(c, self.s, G, self.depth(t), x1=x1)

    def snow_front(self, c, t, x1=None):
        """Over the Keepers: the front lip of the snow they stand in, and the near flakes."""
        SN.front_lip(c, self.s, G, self.depth(t), x1=x1)
        self.s.snowfall.draw(c, self.s, self.t0 + t, self.fall(t), near=True)

    # ----- the treehouse and the animals' houses from episode 4 -----

    def draw_village(self, c, t, peek=1.0, hog=0.0):
        """Treehouse, posts with the four birdhouses, the hedgehog and bunny houses, all lit and snowed on.
        peek 0..1: the birds look out of their holes; hog 0..1: the hedgehog's nose out of his door."""
        s, H = self.s, self.house
        d = self.depth(t)
        H.draw_tree(c, s)
        SN.treehouse_caps(c, H, d, leaves=True)
        H.draw_house(c, s, t, windows=1.0, lanterns=1.0)
        SN.treehouse_caps(c, H, d, leaves=False)
        for bx, r in ((HEDGE_X - 40, 120), (HEDGE_X + 90, 90), (BUNNY_X + 40, 140), (BUNNY_X - 120, 100)):
            c.circle(bx, G - r * 0.55, r, LEAF[1] * 0.75)
            SN.cap_circle(c, bx, G - r * 0.55, r, d * 0.9)
        for k in range(4):
            px = POSTS[k]
            rect(c, px - 13, POST_TOP, px + 13, G + 40, POST)
            rect(c, px - 34, POST_TOP - 8, px + 34, POST_TOP, POST * 1.15)
            SN.cap_flat(c, px - 34, px - PR.SPECS[k].w / 2 - 2, POST_TOP - 8, d * 0.6)
            SN.cap_flat(c, px + PR.SPECS[k].w / 2 + 2, px + 34, POST_TOP - 8, d * 0.6)
        homes = [(POSTS[j], POST_TOP) for j in range(4)] + [(HEDGE_X, G), (BUNNY_X, G)]
        for j, (x, y) in enumerate(homes):
            PR.draw_house(c, s, PR.SPECS[j], x, y, t, paint=1.0, lamp=1.0, inside=1.0)
            SN.house_caps(c, PR.SPECS[j], x, y, d)
        for b in range(4):                 # the birds at home, looking out at the snow
            sp = PR.SPECS[b]
            hx, hy = PR.hole_center(sp, POSTS[b], POST_TOP)
            out = peek * (0.6 + 0.4 * math.sin(t * 1.1 + b * 1.7))
            c.circle(hx + 3 * out, hy + 3, 8.5, BIRD_COLS[b][0])
            c.circle(hx + 6 * out, hy + 6, 4.5, BIRD_COLS[b][1])
            c.circle(hx + 5 * out, hy, 2.0, np.array([16, 16, 20]))
        if hog > 0:
            sp = PR.SPECS[4]
            hx, hy = PR.hole_center(sp, HEDGE_X, G)
            c.polygon(ellipse(hx - 4 + 10 * hog, G - 12, 16, 10, 16), np.array([170, 140, 110]))
            c.circle(hx + 8 + 10 * hog, G - 13, 3.5, np.array([20, 20, 24]))

    def trees(self, c, t, xs):
        for j, (x, h) in enumerate(xs):
            if self.s.visible(x - 260, x + 260):
                SN.snowy_tree(c, x, G, h, 900 + j, self.depth(t))


# ====================================================================== FIRST SNOW

class FirstSnowAct(SnowAct):
    """The first snow on the treehouse; flakes, Wheels gets stuck, Twigs has an idea."""
    name = "first_snow"
    fall0, fall1 = 0.0, 0.75

    def __init__(self, scene, P, t0):
        super().__init__(scene, P, t0)
        self.dur = 44.0
        self.T = dict(look=3.0, springs=6.0, hans=9.0, flake=10.6, brr=12.8, birds=14.5, wheels=17.0, stuck=19.6,
                      digs=21.4, push=23.4, giggle=25.2, think=27.6, idea=29.0, go=32.5)
        self.hans_tip = None

    def depth(self, t):
        return 28.0 * smoothstep(seg(t, 3.0, 22.0))

    def fall(self, t):
        return 0.08 * smoothstep(seg(t, 1.5, 3.0)) + 0.67 * smoothstep(seg(t, 3.0, 14.0))

    def aside_moods(self, t):
        if t < self.T["wheels"]:
            return ["ooh", "aww", "hehe", "brr"]
        return ["hehe", "ooh", "q"]

    def target(self, t):
        h = self.s.h
        keys = [(0.0, *cam(h, 1750, 0.66)), (3.0, *cam(h, 1750, 0.66)), (8.0, *cam(h, 1640, 0.95, 0.86)),
                (13.0, *cam(h, 1600, 0.98, 0.86)), (15.5, *cam(h, 2350, 0.8)), (18.0, *cam(h, 2250, 0.95, 0.86)),
                (25.0, *cam(h, 2200, 0.95, 0.86)), (27.0, *cam(h, 1950, 0.9, 0.86)), (31.0, *cam(h, 1950, 0.9, 0.86)),
                (self.dur, *cam(h, 3300, 0.72))]
        return _ease(keys, t)

    # ----- the Keepers -----

    def wheels_x(self, t):
        T = self.T
        x, _, _ = path([(T["wheels"], HOME["wheels"], G), (T["stuck"] - 0.2, 2360.0, G)], t)
        if t >= T["stuck"] - 0.2:          # stuck: the wheels spin, he slides back a little
            x = 2360.0 - 34 * smoothstep(seg(t, T["stuck"], T["push"]))
        if t >= T["push"]:                 # Digs pushes: he lurches forward and rolls free
            x = 2326.0 + 190 * smootherstep(seg(t, T["push"], T["push"] + 1.4))
        if t >= T["go"]:
            x = path([(T["go"] + 0.6, 2516.0, G), (self.dur, 2516.0 + 1700, G)], t)[0]
        return x

    def update(self, t, dt):
        T, H, s = self.T, self.house, self.s
        self.reach = {}
        for q, kind in enumerate(KEEPERS):
            m = self.m(kind)
            if m is None:
                continue
            x0 = HOME[kind]
            y, dy, ang, walk = None, 0.0, 0.0, None
            x = x0
            if kind == "lantern":
                y = G - 60
                x = x0 + 30 * math.sin(t * 0.4)                     # drifts a little, looking at the snow
                m.lamp = None
            if kind == "springs":
                for k, j0 in enumerate((T["springs"], T["springs"] + 1.1)):   # hops up to catch flakes
                    jp = Jump(x0, G, x0, G, apex=60)
                    if j0 <= t < j0 + jp.dur:
                        y = jp.at(t - j0)[1]
                        m.spring = 0.0
                    elif abs(t - j0) < 0.12 or abs(t - j0 - jp.dur) < 0.12:
                        m.spring = 0.6
                m.spring = m.spring if T["springs"] - 0.2 < t < T["springs"] + 2.5 else 0.0
            if kind == "tentacles":                                   # holds a tentacle up for a flake
                u = smoothstep(seg(t, T["hans"], T["hans"] + 1.2)) * (1 - smoothstep(seg(t, T["flake"] + 2.6,
                                                                                          T["flake"] + 3.6)))
                if u > 0:
                    tip = (x0 + 120, lerp(G - 250, G - 360, u))
                    self.reach["tentacles"] = [tip]
                    self.hans_tip = tip
            if kind == "teeth" and T["brr"] <= t < T["brr"] + 1.2:     # a shiver
                ang = 0.035 * math.sin((t - T["brr"]) * 2 * math.pi * 9) * (1 - seg(t, T["brr"], T["brr"] + 1.2))
            if kind == "wheels":
                x = self.wheels_x(t)
            if kind == "digger":
                x, _, mv = path([(T["digs"], x0, G), (T["push"] - 0.25, 2190.0, G), (T["push"] + 1.4, 2370.0, G),
                                 (T["go"] + 0.5, 2370.0, G), (self.dur, 2370.0 + 1700, G)], t)
                m.punch = smoothstep(seg(t, T["push"] - 0.6, T["push"])) * (1 - smoothstep(seg(t, T["push"] + 1.4,
                                                                                              T["push"] + 2.0)))
                m.dig = 0.4 * m.punch
            if t >= T["go"] and kind not in ("wheels", "digger"):
                lead = T["go"] + 0.3 * q
                if kind == "springs":
                    x, lift, sq = hops(x0, x0 + 1900, lead, lead + 10.5, t, apex=55, step=160)
                    dy -= lift
                    m.spring = sq
                elif kind == "lantern":
                    x = path([(lead, x0 + 30 * math.sin(lead * 0.4), G - 60), (lead + 10.5, x0 + 1900, G - 60)], t)[0]
                else:
                    x = path([(lead, x0, G), (lead + 10.5, x0 + 1900, G)], t)[0]
            self.place(m, x, t, dt, y=y, dy=dy, ang=ang, walk=walk)
            if kind == "wheels" and T["stuck"] - 0.3 <= t < T["push"] + 0.6:      # wheels spinning in the snow
                spin = smoothstep(seg(t, T["stuck"] - 0.3, T["stuck"] + 0.2)) * (1 - smoothstep(seg(t, T["push"],
                                                                                                  T["push"] + 0.6)))
                m.wheel_rot -= 14.0 * spin * dt
                if s.particles.rng.uniform() < 0.7 * spin:
                    s.particles.burst(x - 70, G - 20, 2, SN.SNOW, 420, 0.7, 7, kind="snow", g=1400, spread=0.5,
                                      direction=-math.pi * 0.8)
        self._sounds(t)

    def _sounds(self, t):
        T = self.T
        if self.crossed(T["look"]):
            self.chat(t, "lantern", "ooh")
        if self.crossed(T["look"] + 1.4):
            self.chat(t, "springs", "hey", icon="snow")
        for j0 in (T["springs"], T["springs"] + 1.1):
            if self.crossed(j0):
                self.hit(t, "boing", 62, 0.25, HOME["springs"], G)
        if self.crossed(T["springs"] + 2.0):
            self.chat(t, "springs", "hehe")
        if self.crossed(T["hans"] + 0.2):
            self.chat(t, "tentacles", "hm", icon="snow")
        if self.crossed(T["flake"]):
            self.hit(t, "music_box", 79, 0.16, HOME["tentacles"] + 120, G - 360)
        if self.crossed(T["flake"] + 0.7):
            self.chat(t, "tentacles", "aww")
        if self.crossed(T["brr"]):
            self.chat(t, "teeth", "brr")
        if self.crossed(T["birds"]):
            for k, n in enumerate((84, 88, 86, 91)):
                self.hit(t + k * 0.13, "music_box", n - 12, 0.12, POSTS[k], POST_TOP - 60)
        if self.crossed(T["birds"] + 1.2):
            self.chat(t, "lantern", "aww")
        if self.crossed(T["wheels"] - 0.4):
            self.chat(t, "wheels", "hey", icon="!")
        if self.crossed(T["stuck"] + 0.3):
            self.fx(t, "rustle", 3.4, 0.2, 2360, G)
            self.chat(t + 0.4, "wheels", "uhoh")
        if self.crossed(T["digs"] + 0.2):
            self.chat(t, "digger", "q", icon="!")
        if self.crossed(T["push"] - 0.2):
            self.chat(t, "digger", "huff")
            self.fx(t + 0.2, "whoosh", 0.8, 0.12, 2400, G)
        if self.crossed(T["push"] + 1.0):
            self.chat(t, "wheels", "yay")
        if self.crossed(T["giggle"]):
            self.chorus(t, ["springs", "lantern", "tentacles", "digger"], "hehe", gap=0.25)
        if self.crossed(T["think"]):
            self.chat(t, "teeth", "hm")
        if self.crossed(T["idea"]):
            self.hit(t, "bloop", 72, 0.3, HOME["teeth"], G - 400)
            self.chat(t + 0.15, "teeth", "idea", icon="sled")
            for k, n in enumerate((72, 76, 79, 84)):
                self.hit(t + 0.3 + k * 0.1, "chime", n, 0.22, HOME["teeth"], G - 400)
        if self.crossed(T["idea"] + 1.5):
            self.chorus(t, ["springs", "wheels", "lantern", "digger", "tentacles"], "yay", gap=0.2, icon="star")
        if self.crossed(T["go"] + 0.5):
            self.fx(t, "rustle", 6.0, 0.14, 2600, G)

    def draw(self, c, t):
        s, T = self.s, self.T
        self.backdrop(c, t)
        self.trees(c, t, [(-400, 640), (200, 700), (3950, 720), (4500, 660)])
        self.snow_ground(c, t)
        # Wheels' ruts in the new snow, and the little pile he pushes up
        if t > T["wheels"] and self.depth(t) > 6:
            m = self.m("wheels")
            x1 = m.x if m is not None else 2360
            d = self.depth(t)
            c.line(HOME["wheels"] - 20, G - d * 0.45, x1 - 40, G - d * 0.45, SN.SNOW_SHADE, 9)
            c.polygon(ellipse(x1 + 70, G - d, 26, 10 + 6 * seg(t, T["stuck"], T["push"]), 16, math.pi, 2 * math.pi),
                      SN.SNOW)
        self.draw_village(c, t, peek=smoothstep(seg(t, T["birds"] - 0.5, T["birds"] + 1.0)),
                          hog=smoothstep(seg(t, T["birds"] + 2.0, T["birds"] + 3.5)))
        gl = self.m("lantern")
        if gl is not None and "lantern" in self.poses:
            self.lantern_light(c, gl.x, gl.y - 140, k=0.8)
        self.draw_monsters(c, t)
        # the one flake Hans catches
        if self.hans_tip is not None and T["hans"] + 0.6 <= t < T["flake"] + 2.6:
            tx, ty = self.hans_tip
            u = seg(t, T["hans"] + 0.6, T["flake"])
            fx_ = tx + 60 * math.sin(u * 5) * (1 - u)
            fy = lerp(ty - 420, ty - 10, u)
            melt = 1 - smoothstep(seg(t, T["flake"] + 1.2, T["flake"] + 2.6))
            _flake(c, fx_, fy, 9 * melt + 1, t)
        self.snow_front(c, t)


def _flake(c, x, y, r, t):
    """A single big snowflake (six arms)."""
    col = SN.FLAKE
    for i in range(3):
        a = i * math.pi / 3 + t * 0.6
        ca, sa = math.cos(a), math.sin(a)
        c.line(x - ca * r, y - sa * r, x + ca * r, y + sa * r, col, max(1.5, r * 0.22))
    c.circle(x, y, r * 0.3, col)
