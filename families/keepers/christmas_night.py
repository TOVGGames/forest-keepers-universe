"""Forest Keepers ep 14, beats 4-5: Christmas Eve (docs/engines/forest_keepers_christmas.md, build staging).
4. The gust (night, snow): the fir sways, the gold star tumbles off to the left into the snow, the lantern flames shrink
   out with a wisp. Digs' hat lamp sweeps the snow and finds it at his right paw; he digs it out and lifts it. Springs
   hops in front of the fir and takes it; his first bounce falls short, the second puts it back on top. Glo relights
   the lanterns.
5. The visit: the snow eases; a rabbit hops in, a white-tailed deer walks in, a red fox trots in and sits, a
   chickadee lands on a lantern post (all out and about in winter). They stay a while, then go back into the forest.
"""
import math

import skia

import numpy as np

from families.foundry.keepers.common import smoothstep

from . import christmas_flat_world as XW
from . import illustrate as il
from . import storycheck as sc
from .animals import deer, deer_back, fox, fox_back
from .christmas_bench import GOLD, STAR_R, draw_star
from .christmas_deco import HANG
from .storybook import oval, smooth
from .winter_animals import chickadee, per_s

W, H, G, BACK = XW.W, XW.H, XW.G, XW.BACK
K = 0.72
SPOT = XW.SPOT
STAR_TOP = HANG["top star"]
STAR_REST = (SPOT - 225.0, BACK + 4.0)                     # where it lands: in the drift at the lantern post's foot,
                                                           # well clear of Digs' paw and buried all the way (FK0017 r1:
                                                           # it fell at his paw; r2: still by his claws, tip showing)
DRIFT = (SPOT - 225.0, BACK + 12.0, 50.0, 26.0)             # the drift (x, y, rx, ry)
SINK = 0.55                                                 # how far it sinks in: a gold point stays sticking out
LAND_Y = BACK - 14.0                                        # it lands on the drift's top (r3: it landed in front of
                                                            # it, then was switched off behind it)
DIGS_STEP = 88.0                                           # Digs steps this far towards it to dig it out
RABBIT_X, DEER_X, FOX_X = SPOT + 400.0, SPOT + 500.0, SPOT + 585.0   # the visitors, all in frame with the Keepers
DEER_Y, DEER_S = BACK - 14.0, 260.0                        # the deer a step further back (drawn behind the others)
GATHER = {"tentacles": SPOT - 1060.0, "wheels": SPOT - 880.0, "teeth": SPOT - 730.0}   # at dusk they gather round
GLO_NIGHT = (SPOT - 505.0, 80.0)                           # Glo floats over between Sprout and Digs, up a little
SPRINGS_GIVE_X = SPOT - 100.0                              # Springs takes the star from Digs here (r2: at
                                                         # -160 Digs' paw met it inside Springs' body)
GRAV = 1500.0
DEE_H = 0.66 * 300.0 * K * (10 / 20) ** 0.6


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def rabbit(pg, x, y, s, face=-1, hop=0.0):
    """An eastern cottontail: round grey-brown body, white tail puff, long ears, a big dark eye (sitting; hop lifts and
    stretches it a little)."""
    y = y - hop
    f = face
    st = 1.0 + 0.12 * min(hop / 30.0, 1.0)
    body = (154, 134, 114)
    if f == 0:                                                     # seen from behind as it turns round (r2)
        for dx in (-1, 1):
            pg.shape(oval(x + dx * 10 * s, y - 104 * s, 8 * s, 28 * s, rot=dx * 8), body, 0.08)
        pg.shape(oval(x, y - 64 * s, 25 * s, 23 * s), body, 0.1)
        pg.shape(oval(x, y - 32 * s, 36 * s, 34 * s), body, 0.12)
        pg.flat(oval(x, y - 26 * s, 13 * s, 13 * s), (244, 239, 230))
        return
    pg.shape(oval(x - f * 10 * s, y - 34 * s, 46 * s * st, 36 * s / st), body, 0.12)
    pg.flat(oval(x - f * 50 * s * st, y - 34 * s, 13 * s, 13 * s), (244, 239, 230))
    pg.shape(oval(x + f * 30 * s, y - 62 * s, 26 * s, 24 * s), body, 0.1)
    for dx in (-6, 8):
        pg.shape(oval(x + f * (22 + dx) * s, y - 104 * s, 8 * s, 28 * s, rot=-f * (10 + dx)), body, 0.08)
        pg.flat(oval(x + f * (22 + dx) * s, y - 102 * s, 4 * s, 20 * s, rot=-f * (10 + dx)), (212, 168, 160))
    pg.flat(oval(x + f * 38 * s, y - 66 * s, 6 * s, 7 * s), (58, 44, 36))
    pg.flat(oval(x + f * 40 * s, y - 68 * s, 2 * s, 2 * s), (255, 255, 255))
    pg.flat(oval(x + f * 52 * s, y - 56 * s, 3.5 * s, 3 * s), (176, 122, 112))


class Night:
    def __init__(self, g0):
        self.t0 = g0
        self.dark = (g0, g0 + 7.0)                          # dusk to night
        self.snow = (g0 + 3.0, None)
        self.give_pt = (SPOT - 205.0, G - 124.0)            # Digs' paw held up (set exactly from the plan)
        self.gather = (g0 + 0.8, g0 + 3.8)                  # at dusk the far ones come in closer (all in view, r1)
        self.glo_rise = self.gather[0]                       # when Glo floats up (the plan sets it)
        self.say_eve = g0 + 4.0
        self.gust = (g0 + 7.0, g0 + 11.5)
        self.fall = g0 + 7.8                                # the star leaves the top
        self.tf = 3.2                                       # it tumbles down slowly in the wind, into the drift
                                                            # (r2: 1.5 s was too quick to follow where it went)
        self.landed = self.fall + self.tf
        self.out = [(g0 + 8.2, g0 + 8.9), (g0 + 8.6, g0 + 9.3)]   # the lantern flames shrink out in the gust
        self.helmet_flare = (g0 + 12.4, g0 + 14.2)          # Glo's flare lights Digs' hat lamp (r2: it came on
        hit = g0 + 12.4 + 0.8 * 1.8                         # by itself, nothing touched it)
        self.lamp_on = (hit, hit + 0.4)
        self.say_lamp = g0 + 14.4
        self.sweep = (g0 + 15.0, g0 + 19.0)                 # the beam searches the snow and finds a glint
        self.step = (g0 + 19.2, g0 + 20.4)                  # Digs steps over to it
        self.digs = [(g0 + 20.6, g0 + 21.4), (g0 + 21.4, g0 + 22.2), (g0 + 22.2, g0 + 23.0)]   # digs like a dog
        self.lift = (g0 + 23.2, g0 + 24.6)
        self.springs_in = (g0 + 21.0, g0 + 24.4)            # Springs hops over, beside Digs
        self.give = (g0 + 24.8, g0 + 25.8)                  # from Digs' paw to Springs' left hand
        self.springs_to = (g0 + 26.2, g0 + 27.8)            # beside the fir, under the top
        self.bounce1 = (g0 + 28.4, g0 + 30.0, 120.0)        # short
        self.bounce2 = (g0 + 31.6, g0 + 34.0, 178.0)        # on it goes
        self.placed = self.bounce2[0] + 0.62 * (self.bounce2[1] - self.bounce2[0])
        self.relight = [(g0 + 34.8, g0 + 36.6), (g0 + 37.2, g0 + 39.0)]
        self.say_up = g0 + 34.6
        self.springs_back = (g0 + 36.2, g0 + 39.2)
        e = g0 + 41.2
        self.e0 = e
        self.snow_ease = (e, e + 8.0)
        self.rabbit_in = (e + 0.0, e + 6.0)
        self.deer_in = (e + 3.0, e + 11.0)
        self.fox_in = (e + 7.0, e + 13.0)
        self.fox_sit = (e + 13.0, e + 14.2)
        self.dee_in = (e + 12.0, e + 15.0)
        self.say_visit = e + 9.0
        self.dee_out = (e + 30.0, e + 33.0)
        self.fox_up = (e + 30.5, e + 31.5)                  # the fox first, then the rabbit (never through each other)
        self.fox_out = (e + 31.5, e + 37.0)
        self.rabbit_out = (e + 33.0, e + 39.0)
        self.deer_out = (e + 32.0, e + 40.0)
        self.end = e + 41.0
        self.lamp_off = (self.end + 4.4, self.end + 5.0)    # stays on all night: off in the overnight break (r2: it
                                                            # went off by itself)
        self.wind = lambda t: smoothstep(_seg(t, self.gust[0], self.gust[0] + 0.8)) * (
            1 - smoothstep(_seg(t, self.gust[1] - 1.2, self.gust[1])))

    # ------------------------------------------------------------------ the fir, the lanterns
    def lean(self, t):
        w = self.wind(t)
        return -9.0 * w * (0.7 + 0.3 * math.sin((t - self.gust[0]) * 5.0))

    def glo_up(self, t):
        """How far (px) Glo floats up over the group at night (0 .. GLO_NIGHT[1])."""
        u = smoothstep(_seg(t, self.glo_rise, self.glo_rise + 1.2)) * (1 - smoothstep(_seg(t, self.end,
                                                                                         self.end + 1.6)))
        return GLO_NIGHT[1] * u

    def star_on_top(self, t):
        return t < self.fall or t >= self.placed

    def lamp_factor(self, j, t):
        """Gust: 1 lit .. 0 out; relit by Glo after."""
        a, b = self.out[j]
        f = 1.0 - smoothstep(_seg(t, a, b))
        ra, rb = self.relight[j]
        return max(f, smoothstep(_seg(t, ra + 0.8 * (rb - ra), ra + 0.92 * (rb - ra))))   # as Glo's flare lands

    # ------------------------------------------------------------------ the star
    def star_state(self, t, digs_paw, springs_hand):
        """(x, y, angle, buried 0..1, holder) of the gold star between its fall and its return to the top."""
        if t < self.fall:
            return STAR_TOP[0], STAR_TOP[1], 0.0, 0.0, None
        if t < self.landed:
            x, y, ang = self.tumble(t)
            return x, y, ang, 0.0, "tumbles off in the gust"
        if t < self.lift[0]:
            dug = smoothstep(_seg(t, self.digs[0][0], self.digs[-1][1]))
            sink = SINK * smoothstep(_seg(t, self.landed, self.landed + 0.5))    # (advisor FK0017 r3: it sank
            return STAR_REST[0], LAND_Y, self.tumble(self.landed)[2], sink * (1 - dug), None   # out of sight)
        if t < self.give[0]:
            px, py = digs_paw(t)
            return px, py - 10, 0.0, 0.0, "Digs' right paw"
        if t < self.give[1]:                                     # from paw to hand, both on it
            px, py = digs_paw(t)
            hx, hy = springs_hand(t)
            u = smoothstep(_seg(t, *self.give))
            return px + (hx - px) * u, py - 10 + (hy - py) * u, 0.0, 0.0, \
                "Digs' right paw" if u < 0.5 else "Springs' left hand"
        if t < self.placed:
            hx, hy = springs_hand(t)
            w = self.grip_off(t)                                 # held by its right point, so its hand shows (r2:
            return hx - 20 * w, hy - 10 + 4 * w, 0.0, 0.0, "Springs' left hand"   # centred on it hid the hand)
        return STAR_TOP[0], STAR_TOP[1], 0.0, 0.0, None

    def grip_off(self, t):
        """0..1 how far the carried star sits out past Springs' hand (0 while reaching it up onto the top)."""
        w = smoothstep(_seg(t, self.give[1], self.give[1] + 0.6))
        for a, b, _ in (self.bounce1, self.bounce2):
            if a - 0.4 <= t < b + 0.4:
                if t < a:
                    w = min(w, 1 - smoothstep(_seg(t, a - 0.4, a)))
                elif t < b:
                    w = 0.0
                else:
                    w = min(w, smoothstep(_seg(t, b, b + 0.4)))
        return w

    def tumble(self, t):
        """(x, y, angle) of the star blown off the top: carried left on the wind, rocking, slowly down (3.2 s)."""
        u = _seg(t, self.fall, self.landed)
        x = STAR_TOP[0] + (STAR_REST[0] - STAR_TOP[0]) * (1 - (1 - u) ** 1.6) + 26 * math.sin(math.pi * 3 * u) * (1 - u)
        y = STAR_TOP[1] + (LAND_Y - STAR_TOP[1]) * u ** 1.4 - 40 * math.sin(math.pi * u)
        return x, y, -8.0 * u + 0.5 * math.sin(math.pi * 4 * u)

    def glint(self, t):
        """0..1 how much the buried star's tip catches the light (Digs' beam finding it)."""
        if not (self.landed + 0.3 <= t < self.lift[0]):
            return 0.0
        on, gx = self.beam(t, STAR_REST[0] - 150)
        near = max(0.0, 1.0 - abs(gx - STAR_REST[0]) / 110.0)
        return on * near * (0.75 + 0.25 * math.sin(t * 9.0))

    # ------------------------------------------------------------------ Digs
    def digs_paw_angle(self, t, shoulder):
        """Digs' right paw while he searches, digs it out and holds it up (None outside)."""
        if not (self.sweep[0] <= t < self.give[1] + 0.8):
            return None
        sx_, sy_ = shoulder
        down = math.atan2(STAR_REST[1] - 14 - sy_, STAR_REST[0] - sx_)
        rest = math.radians(72)
        up = math.atan2(-20, 65)                                  # held out to the right, a little up
        if t < self.digs[0][0] - 0.6:
            return None
        if t < self.digs[0][0]:
            return rest + (down - rest) * smoothstep(_seg(t, self.digs[0][0] - 0.6, self.digs[0][0]))
        for a, b in self.digs:
            if a <= t < b:
                u = _seg(t, a, b)
                return down + 0.55 * math.sin(math.pi * u)        # paws the snow back towards him, like a dog
        if t < self.lift[1]:
            return down + (up - down) * smoothstep(_seg(t, *self.lift))
        if t < self.give[1]:
            return up
        return up + (rest - up) * smoothstep(_seg(t, self.give[1], self.give[1] + 0.8))

    def beam(self, t, digs_x):
        """(on 0..1, ground x) of Digs' hat lamp beam."""
        on = smoothstep(_seg(t, *self.lamp_on)) * (1 - smoothstep(_seg(t, *self.lamp_off)))
        x0 = STAR_REST[0] - 410.0                                  # it starts on the snow to his left
        if t < self.sweep[0]:
            gx = x0
        elif t < self.sweep[1]:
            u = _seg(t, *self.sweep)
            gx = x0 + (STAR_REST[0] - x0) * smoothstep(u) + 120 * math.sin(u * math.pi * 2) * (1 - u)
        elif t < self.lift[1]:
            gx = STAR_REST[0]
        else:                                                      # found: the beam comes back to his own feet
            gx = STAR_REST[0] + (digs_x + 20 - STAR_REST[0]) * smoothstep(_seg(t, self.lift[1], self.lift[1] + 1.2))
        return on, gx

    # ------------------------------------------------------------------ Springs
    def springs_lift(self, t):
        for a, b, hgt in (self.bounce1, self.bounce2):
            if a - 0.35 <= t < b:
                if t < a:
                    return 0.0, 0.6 * math.sin(math.pi * _seg(t, a - 0.35, a))
                return hgt * math.sin(math.pi * _seg(t, a, b)), 0.0
        return 0.0, 0.0

    def springs_hand_target(self, t, x, y):
        """Springs' left hand (world) while it takes the star and puts it on top."""
        if self.give[0] - 0.6 <= t < self.give[1]:
            return self.give_pt
        if self.give[1] <= t < self.bounce2[1]:
            top = (STAR_TOP[0], STAR_TOP[1] + 10)                   # reaching up for the top
            hold = (x - 72 * K - 60, y - 112)                    # out at its side, clear of its body (r2: held up
                                                                 # by its face the star read as stuck to it)
            if t < self.give[1] + 0.6:                              # draws it in from Digs' paw (no snap)
                u = smoothstep(_seg(t, self.give[1], self.give[1] + 0.6))
                hold = (self.give_pt[0] + (hold[0] - self.give_pt[0]) * u, self.give_pt[1] + (hold[1] - self.give_pt[1]) * u)
            for a, b, hgt in (self.bounce1, self.bounce2):
                if a - 0.4 <= t < b + 0.4:                          # raised up as it crouches, lowered as it lands
                    u = 1.0 if a <= t < b else (smoothstep(_seg(t, a - 0.4, a)) if t < a else 1 - smoothstep(_seg(t, b, b + 0.4)))
                    return (hold[0] + (top[0] - hold[0]) * u, hold[1] + (top[1] - hold[1]) * u)
            return hold
        return None

    # ------------------------------------------------------------------ the visit
    def rabbit_xy(self, t):
        if t < self.rabbit_in[0] or t > self.rabbit_out[1]:
            return None
        if t < self.rabbit_in[1]:
            u = _seg(t, *self.rabbit_in)
            x = SPOT + 1150 + (RABBIT_X - SPOT - 1150) * smoothstep(u)
            hop = 26 * abs(math.sin(u * math.pi * 7))
            return x, hop, -1
        if t < self.rabbit_out[0]:
            return RABBIT_X, 0.0, -1
        a, b = self.rabbit_out
        if t < a + self.TURN_S:                                  # turns round first, on the spot (r2: a mirror flip)
            return RABBIT_X, 0.0, self._turn((t - a) / self.TURN_S)
        u = _seg(t, a + self.TURN_S, b)
        return RABBIT_X + 800 * smoothstep(u), 26 * abs(math.sin(u * math.pi * 7)), 1

    TURN_S = 0.9          # an animal turns round over this long (seen from the side: it swings through facing away)

    @staticmethod
    def _turn(u):
        """-1 (facing left), 0 (seen from behind, the in-between pose) or 1 (facing right) as it turns round: never a
        one-frame mirror (FK0017 advisor r1), never the side view squashed thin (r2: a stick puppet)."""
        return -1 if u < 0.3 else (0 if u < 0.7 else 1)

    def deer_xy(self, t):
        if t < self.deer_in[0] or t > self.deer_out[1]:
            return None
        if t < self.deer_in[1]:
            u = _seg(t, *self.deer_in)
            return SPOT + 1500 + (DEER_X - SPOT - 1500) * smoothstep(u), 1.0 - smoothstep((u - 0.85) / 0.15), -1
        if t < self.deer_out[0]:
            return DEER_X, 0.0, -1
        a, b = self.deer_out
        if t < a + self.TURN_S:                                  # turns round first, on the spot
            return DEER_X, 0.0, self._turn((t - a) / self.TURN_S)
        u = _seg(t, a + self.TURN_S, b)
        return DEER_X + 900 * smoothstep(u), smoothstep(u / 0.1), 1

    def fox_xy(self, t):
        if t < self.fox_in[0] or t > self.fox_out[1]:
            return None
        if t < self.fox_in[1]:
            u = _seg(t, *self.fox_in)
            return SPOT + 1700 + (FOX_X - SPOT - 1700) * smoothstep(u), 0.0, 1.0, -1
        if t < self.fox_up[0]:
            return FOX_X, smoothstep(_seg(t, *self.fox_sit)), 0.0, -1
        if t < self.fox_out[0]:                                  # stands up and turns round as it does
            a, b = self.fox_up
            return FOX_X, 1 - smoothstep(_seg(t, a, b)), 0.0, self._turn((t - a) / max(0.3, min(self.TURN_S, self.fox_out[0] - a)))
        u = _seg(t, *self.fox_out)
        return FOX_X + 900 * smoothstep(u), 0.0, 1.0, 1

    def dee_xy(self, t):
        post = (SPOT + XW.LAMP_DX[1], XW.LAMP_Y - 50)
        if t < self.dee_in[0] or t > self.dee_out[1]:
            return None
        if t < self.dee_in[1]:
            u = _seg(t, *self.dee_in)
            x = post[0] + 500 * (1 - smoothstep(u))
            y = post[1] - 320 * (1 - smoothstep(u)) + 40 * math.sin(math.pi * u)
            return x, y, 1.0 - smoothstep((u - 0.8) / 0.2), -1
        if t < self.dee_out[0]:
            return post[0], post[1], 0.0, -1
        u = _seg(t, *self.dee_out)
        return post[0] + 520 * smoothstep(u), post[1] - 340 * smoothstep(u), smoothstep(u / 0.1), 1

    def snow_amount(self, t):
        if t < self.snow[0]:
            return 0.0
        return smoothstep(_seg(t, self.snow[0], self.snow[0] + 3.0)) * (1 - 0.6 * smoothstep(_seg(t, *self.snow_ease)))

    # ------------------------------------------------------------------ drawing
    def draw_snow(self, pg, t):
        """Falling snow (screen space: the flakes are near and the camera hardly moves), blown sideways in the gust."""
        a = self.snow_amount(t)
        if a <= 0.01:
            return
        rs = np.random.default_rng(57)
        n = 140
        wind = self.wind(t)
        drift = 0.0
        # wind displacement integrated simply: the gust pushes everything sideways for its length
        if t > self.gust[0]:
            tt = min(t, self.gust[1]) - self.gust[0]
            drift = -260.0 * tt * (0.6 + 0.4 * min(tt / 2.0, 1.0))
        for i in range(n):
            x0, ph, v, r = rs.uniform(0, W), rs.uniform(0, 1), rs.uniform(40, 80), rs.uniform(2.0, 4.8)
            if i / n > a:
                continue
            y = (ph * (H + 40) + v * (t - self.snow[0])) % (H + 40) - 20
            x = (x0 + 14 * math.sin(t * 0.7 + i) + drift * (0.6 + 0.4 * r / 4.8) - 180 * wind * (y / H)) % (W + 40) - 20
            pg.flat(oval(x, y, r, r), (252, 250, 244), 0.85)

    def in_drift(self, t):
        return self.landed <= t < self.lift[0]

    def draw_star(self, pg, t, sh, digs_paw, springs_hand, in_drift=False):
        """The loose star; in_drift=True draws it only while it lies in the drift (that pass goes under the drift)."""
        if self.star_on_top(t) or self.in_drift(t) != in_drift:
            return
        x, y, ang, buried, _ = self.star_state(t, digs_paw, springs_hand)
        if not in_drift:
            draw_star(pg, x - sh, y, 1.0, 1.0, GOLD, STAR_R, ang)
            return
        import skia                                                # in the drift: sunk all the way in (the drift is
        dx_, dy_, rx, ry = DRIFT                                   # drawn over it), then dug out; nothing of it shows
        y += 14.0 * buried                                         # below the drift's foot
        k = self._drift_k(t)
        cx, cy, ex, ey = dx_ - sh, dy_, rx * (0.8 + 0.2 * k), ry * k + 4
        clip = skia.Path().addRect(skia.Rect(-1e5, -1e5, 1e5, cy))
        clip.addOval(skia.Rect(cx - ex, cy - ey, cx + ex, cy + ey))
        pg.c.save()
        pg.c.clipPath(clip, doAntiAlias=True)
        draw_star(pg, x - sh, y, 1.0, 1.0, GOLD, STAR_R, ang)
        pg.c.restore()

    def _drift_k(self, t):
        dug = smoothstep(_seg(t, self.digs[0][0], self.digs[-1][1])) if t >= self.digs[0][0] else 0.0
        return 1.0 - 0.55 * dug

    def draw_drift(self, pg, t, sh):
        """The little drift the star falls into (in front of the star, behind the Keepers); Digs paws it away."""
        x, y, rx, ry = DRIFT
        k = self._drift_k(t)
        pg.flat(oval(x - sh + 6, y + 4, rx * (0.8 + 0.2 * k) + 6, (ry * k + 4) * 0.7), (150, 164, 200), 0.45, blur=5)
        pg.shape(oval(x - sh, y, rx * (0.8 + 0.2 * k), ry * k + 4), XW.SNOW, 0.12)
        pg.flat(oval(x - sh - rx * 0.25, y - ry * k * 0.45, rx * 0.4, ry * k * 0.3 + 1), (255, 255, 255), 0.7)
        for a, b in self.digs:                                     # each stroke throws a little spray of snow back
            if a <= t < b + 0.5:
                u = _seg(t, a, b + 0.5)
                for q in range(6):
                    px = x - sh - 20 - 90 * u * (0.6 + 0.12 * q)
                    py = y - 10 - 70 * math.sin(math.pi * min(1.0, u * 1.2)) * (0.5 + 0.1 * q) + 8 * q * u
                    pg.flat(oval(px, py, 4 + q % 3, 4 + q % 3), XW.SNOW, 0.9 * (1 - u))
        g = self.glint(t)                                          # the beam finds it: a gold gleam shines up
        if g > 0.01:                                               # through the top of the drift
            gx, gy = x - sh - 6, y - ry * k - 2
            pg.glow(gx, gy, 38, "#fff2b0", 0.8 * g)
            pg.flat(oval(gx, gy, 4 + 3 * g, 3 + 2 * g), "#ffe680", g)
            pg.flat(oval(gx, gy, 2 + 2 * g, 1.5 + g), "#fffbe8", g)

    def draw_streaks(self, pg, t):
        """The gust you can see: long soft wind streaks sweeping right to left across the page."""
        w = self.wind(t)
        if w <= 0.01:
            return
        rs = np.random.default_rng(91)
        for i in range(16):
            y0, ph, ln = rs.uniform(H * 0.25, H * 0.95), rs.uniform(0, 1), rs.uniform(160, 340)
            x = W + 200 - ((ph * (W + 600) + 1500.0 * (t - self.gust[0])) % (W + 600))
            y = y0 + 18 * math.sin(x / 140.0 + i)
            p = smooth([(x, y), (x + ln * 0.35, y - 10), (x + ln * 0.7, y - 4), (x + ln, y + 8)])
            q = smooth([(px_, py_ + 4) for px_, py_ in [(x, y), (x + ln * 0.35, y - 10), (x + ln * 0.7, y - 4),
                                                        (x + ln, y + 8)]])
            pg.stroke(q, (96, 112, 150), 4.0, 0.18 * w, blur=3)          # a soft shade under it, so it reads on snow
            pg.stroke(p, (252, 253, 255), 4.0, 0.8 * w, blur=1)

    def draw_beam(self, pg, t, sh, digs_xy):
        dx, dy = digs_xy
        on, gx = self.beam(t, dx)
        if on <= 0.01:
            return
        hx, hy = dx - sh, dy - 182
        p = smooth([(hx - 6, hy), (gx - 70 - sh, BACK + 14), (gx + 70 - sh, BACK + 14), (hx + 6, hy)], closed=True)
        pg.c.save()                                                   # (advisor FK0017 r3: the beam's haze lay over
        body = skia.Path().addOval(skia.Rect(hx - 112, hy + 14, hx + 112, dy + 4))   # his whole body: he looked pale)
        pg.c.clipPath(body, skia.ClipOp.kDifference, True)
        pg.flat(p, (255, 244, 214), 0.24 * on, blur=10)               # (r2: too faint to link lamp and pool)
        pg.c.restore()
        pg.glow(hx, hy, 26, "#fff2cc", 0.6 * on)                      # the lamp itself
        pg.glow(gx - sh, BACK + 6, 90, "#fff2cc", 0.35 * on)

    def draw_wisps(self, pg, t, sh):
        for j, (a, b) in enumerate(self.out):
            if a <= t < b + 1.6:
                u = _seg(t, a, b + 1.6)
                x = SPOT + XW.LAMP_DX[j] - sh - 30 * u
                y = XW.LAMP_Y - 40 - 60 * u
                pg.flat(oval(x, y, 8 + 10 * u, 6 + 8 * u), (210, 210, 220), 0.35 * (1 - u))

    def draw_visitors(self, pg, t, sh):
        d = self.deer_xy(t)
        if d is not None:
            x, walk, face = d
            if face == 0:
                il.creature(pg, lambda cv, x=x: deer_back(cv, x - sh, DEER_Y, DEER_S, t), x - sh, DEER_Y)
            else:
                il.creature(pg, lambda cv, x=x, walk=walk, face=face: deer(cv, x - sh, DEER_Y, DEER_S, t, face=face,
                                                                            walk=walk, gait=x / 180.0, head_up=1.0,
                                                                            ears=0.3 * math.sin(t)), x - sh, DEER_Y)
        r = self.rabbit_xy(t)                                     # (the deer is a step further back: drawn first)
        if r is not None:
            rabbit(pg, r[0] - sh, BACK + 30, 1.1, face=r[2], hop=r[1])
        f = self.fox_xy(t)
        if f is not None:
            x, sit, walk, face = f
            if face == 0:
                il.creature(pg, lambda cv, x=x: fox_back(cv, x - sh, BACK + 34, 140, t, tail=0.3 * math.sin(t * 0.8)),
                            x - sh, BACK + 34)
            else:
                il.creature(pg, lambda cv, x=x, sit=sit, walk=walk, face=face: fox(cv, x - sh, BACK + 34, 140, t,
                                                                                   face=face, sit=sit, walk=walk,
                                                                                   gait=x / 90.0,
                                                                                   tail=0.3 * math.sin(t * 0.8)),
                            x - sh, BACK + 34)
        c = self.dee_xy(t)
        if c is not None:
            x, y, fly, face = c
            s = DEE_H / per_s("chickadee")
            il.creature(pg, lambda cv, x=x, y=y, fly=fly, face=face: chickadee(cv, x - sh, y, s, t, face=face, fly=fly,
                                                                               flap=t * 14.0, fluff=0.5 * (1 - fly)),
                        x - sh, y)

    # ------------------------------------------------------------------ storycheck
    def things(self, t, sh, digs_paw, springs_hand):
        out = {}
        if self.fall <= t < self.placed:
            x, y, ang, buried, who = self.star_state(t, digs_paw, springs_hand)
            held = None
            moves = None
            if who in ("Digs' right paw",):
                p = digs_paw(t) if t < self.give[0] else (x, y + 10)
                held = (who, (p[0] - sh, p[1]))
            elif who == "Springs' left hand":
                p = springs_hand(t) if t >= self.give[1] else (x, y + 10)
                held = (who, (p[0] - sh, p[1]))
            elif who:
                moves = who
            out["star 3"] = sc.Thing(x - sh, y, STAR_R * 2, held=held, moves=moves)
        for name, fn, size, gy in (("rabbit", self.rabbit_xy, 110, BACK + 34), ("deer", self.deer_xy, DEER_S, DEER_Y),
                                   ("fox", self.fox_xy, 140, BACK + 34)):
            p = fn(t)
            if p is not None:
                out[name] = sc.Thing(p[0] - sh, gy - size / 2, size, born="comes in from the forest",
                                     gone=("back into the forest", (p[0] - sh, gy - size / 2)), moves="walks",
                                     flat=1.0)
        c = self.dee_xy(t)
        if c is not None:
            out["chickadee"] = sc.Thing(c[0] - sh, c[1], DEE_H, born="flies in", moves="flies",
                                        gone=("flies off", (c[0] - sh, c[1])))
        return out



