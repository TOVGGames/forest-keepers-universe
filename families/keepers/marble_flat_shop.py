"""The Treetop Marble Run (flat), beat 2: making the marbles in the workshop (docs/engines/
forest_keepers_marble_run_flat.md).

Left to right under the awning: the low sawhorse with the square beam and its stop block (Twigs), the basket the
cubes drop into, the tumbler drum on its stand (Hans loads and empties it), the rack the balls roll into, and the
drive rollers Wheels rolls onto: his turning wheels turn the rollers, the belt turns the drum.

- Twigs: the left hand slides the beam up to the stop block (so every cube is the same size), the blade slides out
  of the sheath on his right forearm and saws straight down through the beam at the cut line in short strokes
  (sawdust flies from the blade), the blade goes back in, the hand tips the cube off the front edge: it falls into
  the basket.
- Hans lifts the basket with two tentacles, tips the six cubes into the drum's open hatch, sets the basket down
  and swings the hatch shut with a third.
- Wheels rolls onto the drive rollers; his wheels turn on the spot, the belt turns the drum (the cubes clatter
  inside, sawdust puffs from the seams), slowing to a stop with the hatch down to the right.
- Hans opens the hatch: six round wooden balls roll out one by one, down the chute and along the rack, each up
  against the one before.
- Glo floats over the rack: for each ball his lantern flares, a mote of light drifts down to it, sparkles fall on
  it and it takes a Keeper's colour (a visible cause).
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep
from families.foundry.products.monster import ORB, Monster

from . import storycheck as sc
from .marble_flat_course import BAND, KINDS, MARBLE_COLS, PLAIN, R0, draw_marble
from .marble_flat_world import BACK, G, TRUNK, WOOD, WOOD2, WOOD3
from .storybook import mix, oval, rrect, smooth, tone

K = 0.72
GBALL = 2600.0

# the layout (world x)
TWIGS_X = 3650.0
BT = G - 80.0                       # the sawhorse's top (low: Twigs saws straight down with his arm hanging)
CUBE = 2 * R0 + 4.0                 # a cube's side: a little bigger than the ball it becomes
BEAM_T = CUBE
HANS_X = 4080.0
DRUM = (4320.0, G - 200.0)
DRUM_R = 96.0
HATCH_W = 0.62                      # rad: the hatch's width on the rim
LOAD_ANG = math.radians(-135.0)     # the hatch up and to the left, for loading
EMPTY_ANG = math.radians(45.0)      # ... down and to the right, over the chute
RACK = (4450.0, 4850.0)             # the rack's channel (x), sloping gently down to the right, a stop at its end
RACK_Y0 = RACK_Y1 = BACK - 24.0              # the rack-tray: level (it lifts off its legs)
ROLLERS = 5030.0                    # Wheels' drive rollers (his middle when he is on them)
WHEELS_WAIT = 5210.0
WHEELS_RACK = 4706.0                # his middle when his right pincer reaches the rack's end slot
TRAY_GRIP = (4620.0, 4810.0)        # where his pincers hold the tray
GLO_OVER = 4650.0
WR = 46.0 * K


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def _ease(p, q, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


def rack_y(x):
    return RACK_Y0 + (RACK_Y1 - RACK_Y0) * (x - RACK[0]) / (RACK[1] - RACK[0])


# ----------------------------------------------------------------------------------------------- Twigs' blade

class _Null:
    flat_look, eye_scale, glowing, iris_col = True, 1.15, False, ORB

    def __getattr__(self, k):
        return lambda *a, **kw: None


def twigs_arm(x, hand, t, blades=1.0):
    """(shoulder, elbow, hand, blade tip) of Twigs' right arm as drawn with arm_to = hand (screen = world here)."""
    from . import illustrate as il
    m = Monster("teeth", k=K)
    m.x, m.y, m.newlook = x, G, True
    m.hands, m.saws, m.blades, m.clamp_reach, m.knee_fwd = True, False, blades, True, True
    m.arm_to = {1: hand}
    m.draw(_Null(), t, il.Glow())
    sh, el, hd = m.arm_len[1]
    ux, uy, nx, ny = m._blade_frame(hd, el, 1)
    out = (6 + 74 * smoothstep(blades)) * K
    return sh, el, hd, (hd[0] + nx * 13 * K + ux * out, hd[1] + ny * 13 * K + uy * out)


def _saw_hands():
    """The hand targets that put the blade tip at the top and at the bottom of the cut with the forearm hanging
    near straight down (searched once, with the real arm)."""
    grid = []
    for dx in np.arange(0.0, 120.0, 3.0):
        for dy in np.arange(-210.0, -80.0, 3.0):
            hand = (TWIGS_X + dx, G + dy)
            sh, el, hd, tip = twigs_arm(TWIGS_X, hand, 0.0)
            vert = (hd[1] - el[1]) / (math.hypot(hd[0] - el[0], hd[1] - el[1]) + 1e-9)
            # keep clear of the line where his elbow changes sides (~68 deg below the shoulder): no flips mid-cut
            ang = math.degrees(math.atan2(hand[1] - sh[1], hand[0] - sh[0]))
            if ang < 76.0 or math.hypot(hand[0] - sh[0], hand[1] - sh[1]) < 60.0:
                continue
            grid.append((hand, tip, vert))
    y_top, y_bot = BT - BEAM_T - 4.0, BT + 3.0
    best = None
    for h0, t0, v0 in grid:                                       # the top pose sets the line ...
        if abs(t0[1] - y_top) > 3 or v0 < 0.45:
            continue
        for h1, t1, v1 in grid:                                   # ... the bottom pose must cut straight down it
            if abs(t1[1] - y_bot) > 3 or v1 < 0.45:
                continue
            s = abs(t1[0] - t0[0]) * 3 + abs(v1 - v0) * 120 + (2 - v0 - v1) * 10
            if best is None or s < best[0]:
                best = (s, (h0, t0), (h1, t1))
    return {"top": (0, best[1][0], best[1][1]), "bottom": (0, best[2][0], best[2][1])}


SAW = None


def saw_setup():
    global SAW
    if SAW is None:
        b = _saw_hands()
        cut_x = (b["top"][2][0] + b["bottom"][2][0]) / 2           # the cut line: where the blade hangs
        SAW = dict(top=b["top"][1], bottom=b["bottom"][1], cut=cut_x, tip_top=b["top"][2], tip_bottom=b["bottom"][2])
    return SAW


# ----------------------------------------------------------------------------------------------- the beat

class Shop:
    def __init__(self, t0):
        S = saw_setup()
        self.tray_off = lambda t: (0.0, 0.0)                      # the plan moves the tray (Wheels carries it)
        self.tray_grips = lambda t: ((TRAY_GRIP[0], RACK_Y0 + 10), (TRAY_GRIP[1], RACK_Y0 + 10))
        self.release = 1e9
        self.cut = S["cut"]
        self.stop = self.cut + CUBE                               # the stop block's left face
        self.t0 = t0
        t = t0 + 2.0
        self.cuts = []
        for j in range(6):
            c = {}
            if j > 0:
                c["slide"] = (t, t + 1.1)
                t += 1.3
            c["out"] = (t, t + 0.45)
            c["saw"] = (t + 0.45, t + 0.45 + 2.6)
            c["in"] = (c["saw"][1], c["saw"][1] + 0.35)
            c["tip"] = (c["in"][1], c["in"][1] + 0.5)               # the hand tips the cube off the front edge
            c["fall"] = c["tip"][1]
            t = c["tip"][1] + 0.4
            self.cuts.append(c)
        self.cuts_end = t
        rs = np.random.default_rng(7)
        self.dust = []                                            # sawdust: specks flicked out of the cut
        for j, c in enumerate(self.cuts):
            a, b = c["saw"]
            for q in range(14):
                tt = a + (b - a) * (q + 0.5) / 14
                self.dust.append(dict(t=tt, vx=rs.uniform(-120, 120), vy=rs.uniform(-260, -120),
                                      r=rs.uniform(2.0, 3.6), j=j))
        # Hans: the basket up to the hatch, tipped, down; the hatch shut
        h = {}
        h["reach"] = (t + 0.2, t + 1.2)
        h["lift"] = (h["reach"][1], h["reach"][1] + 1.6)
        h["tip"] = (h["lift"][1], h["lift"][1] + 0.9)
        h["pour"] = (h["tip"][1] - 0.3, h["tip"][1] + 0.9)          # the cubes slide out, one after another
        h["back"] = (h["pour"][1] + 0.2, h["pour"][1] + 1.7)
        h["shut"] = (h["back"][1] + 2.2, h["back"][1] + 3.4)        # back at the drum, a tentacle swings it shut
        self.hans = h
        # Wheels: onto the rollers, the drum turns ~4 times, slows, stops with the hatch over the chute
        w = {}
        w["roll_on"] = (h["shut"][1] - 1.0, h["shut"][1] + 1.0)
        w["drive"] = (w["roll_on"][1] + 0.3, w["roll_on"][1] + 0.3 + 10.0)
        # off the rollers to the rack's end: his plain ball from the very start goes in the end slot first
        w["to_rack"] = (w["drive"][1] + 0.6, w["drive"][1] + 2.6)
        w["place"] = (w["to_rack"][1] + 0.5, w["to_rack"][1] + 1.8)   # (stopped first: the slot is in reach)
        self.wheels = w
        self.plain_slot = RACK[1] - 6 - R0
        turns = 4.0
        self.drum_total = 2 * math.pi * turns + ((EMPTY_ANG - LOAD_ANG) % (2 * math.pi))
        # Hans opens it; the balls roll out
        o = {}
        o["open"] = (w["place"][1] + 0.2, w["place"][1] + 1.0)
        o["out"] = [o["open"][1] + 0.3 + 0.7 * i for i in range(6)]
        self.empty = o
        self.balls = [self._ball_path(i, o["out"][i]) for i in range(6)]
        # Glo colours them, one after another (lane order: ball i becomes KINDS[i]'s marble)
        g0 = max(b["settle"] for b in self.balls) + 1.2
        self.glo_in = (g0 - 1.8, g0)
        self.colour = [(g0 + 2.1 * i, g0 + 2.1 * i + 1.6) for i in range(6)]
        # Wheels lifts the tray off its legs with both pincers (he carries it to the run)
        self.lift = (self.colour[-1][1] + 1.0, self.colour[-1][1] + 2.4)
        self.end = self.lift[1] + 0.4

    # --- Twigs
    def beam_right(self, t):
        """The beam's right end (world x): against the stop block, cut back by a cube, slid up again."""
        n_cut = sum(1 for c in self.cuts if t >= c["saw"][1])
        slid = sum(smoothstep(_seg(t, *c["slide"])) for c in self.cuts if "slide" in c)
        return self.stop - CUBE * n_cut + CUBE * slid

    def beam_left(self, t=0.0):
        slid = sum(smoothstep(_seg(t, *c["slide"])) for c in self.cuts if "slide" in c)
        return self.stop - 6 * CUBE - 60.0 + CUBE * slid

    def cube(self, j, t):
        """(x, y, angle deg, state) of cube j: part of the beam, tipping off, falling, in the basket, carried, gone."""
        c = self.cuts[j]
        x0, y0 = self.cut + CUBE / 2, BT - CUBE / 2
        if t < c["saw"][1]:
            return None
        if t < c["tip"][0]:
            return x0, y0, 0.0, "on the sawhorse"
        u = _seg(t, *c["tip"])
        if t < c["tip"][1]:                                       # tipping over the front edge (toward us)
            return x0, y0 + 4 * u, 0.0, "tipped by Twigs' hand"
        bx, by = self.basket_pos(t)
        rest = (bx - 34 + 14 * j, by - 40 - (j % 2) * 8)
        tf = math.sqrt(2 * max(rest[1] - y0, 1.0) / GBALL)
        if t < c["fall"] + tf:
            v = t - c["fall"]
            return x0 + (rest[0] - x0) * v / tf, y0 + 0.5 * GBALL * v * v, 30.0 * v / tf, "falls"
        h = self.hans
        if t < h["pour"][0] + 0.12 * j:
            return rest[0], rest[1], 30.0 + 9 * j, "in the basket"
        # slides out of the tipped basket over its rim, then drops into the hatch
        t_p = h["pour"][0] + 0.12 * j
        hx, hy = self.hatch_pos(t)
        bx, by = self.basket_pos(t)
        x0, y0 = rest                                             # where it lay in the basket (it moves with it)
        rim = (bx + 50, by - 50)
        v = t - t_p
        if v < 0.25:
            u = smoothstep(v / 0.25)
            return x0 + (rim[0] - x0) * u, y0 + (rim[1] - y0) * u, 30.0 + 9 * j + 20 * u, "tipped out of the basket"
        v -= 0.25
        tf = 0.3
        if v < tf:
            f = v / tf
            return rim[0] + (hx - rim[0]) * f, rim[1] + (hy - rim[1]) * f * f, 50.0, "falls"
        return None

    def twigs_hands(self, t, x):
        """{side: world xy}, blade 0..1, grip, for Twigs at the sawhorse."""
        S = saw_setup()
        if not (self.t0 + 0.8 <= t < self.cuts_end + 0.8):
            return {}, 0.0, 0.0
        rest_r = (self.cut - 26, BT - BEAM_T - 4)                 # resting on the beam beside the cut
        hold = (self.beam_right(t) - CUBE - 110, BT - BEAM_T - 2)
        hands = {-1: hold}
        blade, grip = 0.0, 0.6
        r = rest_r
        for c in self.cuts:
            if "slide" in c and c["slide"][0] <= t < c["slide"][1]:
                hands[-1] = (self.beam_right(t) - CUBE - 110, BT - BEAM_T - 2)
            if c["out"][0] - 0.6 <= t < c["out"][0]:
                r = _ease(rest_r, S["top"], _seg(t, c["out"][0] - 0.6, c["out"][0]))
            elif c["out"][0] <= t < c["out"][1]:
                r, blade = S["top"], smoothstep(_seg(t, *c["out"]))
            elif c["saw"][0] <= t < c["saw"][1]:
                u = _seg(t, *c["saw"])
                d = smoothstep(u)                                 # down through the beam, in short strokes
                stroke = 7.0 * math.sin(u * 6 * 2 * math.pi)
                hx = S["top"][0] + (S["bottom"][0] - S["top"][0]) * d
                hy = S["top"][1] + (S["bottom"][1] - S["top"][1]) * d - stroke
                r, blade = (hx, hy), 1.0
            elif c["in"][0] <= t < c["in"][1]:
                r, blade = S["bottom"], 1.0 - smoothstep(_seg(t, *c["in"]))
            elif c["tip"][0] - 0.0 <= t < c["tip"][1] + 0.5:
                cube_top = (self.cut + CUBE / 2 + 6, BT - CUBE - 2)
                if t < c["tip"][0] + 0.25:
                    r = _ease(S["bottom"], cube_top, _seg(t, c["tip"][0], c["tip"][0] + 0.25))
                elif t < c["tip"][1]:
                    r = (cube_top[0], cube_top[1] + 6 * _seg(t, c["tip"][0] + 0.25, c["tip"][1]))
                else:
                    r = _ease(cube_top, rest_r, _seg(t, c["tip"][1], c["tip"][1] + 0.5))
        hands[1] = r
        return hands, blade, grip

    def dust_pos(self, d, t):
        u = t - d["t"]
        if u < 0 or u > 1.4:
            return None
        S = saw_setup()
        x0, y0 = self.cut, BT - BEAM_T * 0.3
        y = y0 + d["vy"] * u + 0.5 * 1400 * u * u
        if y > G + 10:
            return None
        return x0 + d["vx"] * u, y

    # --- the basket (on the ground in front of the sawhorse, then in Hans' tentacles)
    BASKET0 = None

    def basket_home(self):
        return (self.cut + 40.0, G + 26.0)

    def basket_pos(self, t):
        h = self.hans
        home = self.basket_home()
        top = (DRUM[0] - DRUM_R * 0.9 - 40, DRUM[1] - DRUM_R - 40)
        if t < h["lift"][0]:
            return home
        up = (home[0], top[1])                                    # straight up first, then over to the hatch
        if t < h["lift"][1]:                                      # (it never passes close in front of his middle)
            u = _seg(t, *h["lift"])
            return _ease(home, up, u / 0.5) if u < 0.5 else _ease(up, top, (u - 0.5) / 0.5)
        if t < h["back"][0]:
            return top
        if t < h["back"][1]:
            u = _seg(t, *h["back"])
            return _ease(top, up, u / 0.5) if u < 0.5 else _ease(up, home, (u - 0.5) / 0.5)
        return home

    def basket_tilt(self, t):
        h = self.hans
        return 70.0 * smoothstep(_seg(t, *h["tip"])) * (1 - smoothstep(_seg(t, h["back"][0], h["back"][0] + 0.8)))

    def hans_targets(self, t, x):
        """[(slot, world xy, grip)] Hans' working tentacles: two on the basket's rim, one for the hatch."""
        h, o = self.hans, self.empty
        out = []
        on = smoothstep(_seg(t, *h["reach"])) * (1 - smoothstep(_seg(t, h["back"][1], h["back"][1] + 0.8)))
        if on > 0.001:
            bx, by = self.basket_pos(t)
            out += [(-1, (bx - 34, by - 26), on), (1, (bx + 34, by - 30), on)]
        for (a, b) in (h["shut"], o["open"]):
            u = smoothstep(_seg(t, a - 0.6, a)) * (1 - smoothstep(_seg(t, b, b + 0.7)))
            if u > 0.001:
                out.append((2, self.hatch_lid(t)[1], u))
        return out

    # --- the drum
    def drum_ang(self, t):
        """The hatch's angle on the rim (rad, screen: 0 = right, +pi/2 = down)."""
        w = self.wheels
        u = _seg(t, *w["drive"])
        return LOAD_ANG + self.drum_total * smoothstep(u)

    def drum_speed(self, t, h=0.02):
        return (self.drum_ang(t + h) - self.drum_ang(t - h)) / (2 * h)

    def hatch_pos(self, t):
        a = self.drum_ang(t)
        return DRUM[0] + math.cos(a) * (DRUM_R - 20), DRUM[1] + math.sin(a) * (DRUM_R - 20)

    def hatch_open(self, t):
        h, o = self.hans, self.empty
        if t < h["shut"][0]:
            return 1.0
        if t < h["shut"][1]:
            return 1.0 - smoothstep(_seg(t, *h["shut"]))
        if t < o["open"][0]:
            return 0.0
        return smoothstep(_seg(t, *o["open"]))

    def hatch_lid(self, t):
        """The lid: (hinge xy, free edge xy) - hinged on the hatch's trailing side, it swings out to open."""
        a = self.drum_ang(t)
        hinge_a = a - HATCH_W / 2
        hx, hy = DRUM[0] + math.cos(hinge_a) * DRUM_R, DRUM[1] + math.sin(hinge_a) * DRUM_R
        L = 2 * DRUM_R * math.sin(HATCH_W / 2)
        closed = hinge_a + math.pi / 2 + HATCH_W / 2           # along the rim
        ang = closed - 1.9 * self.hatch_open(t)
        return (hx, hy), (hx + math.cos(ang) * L, hy + math.sin(ang) * L)

    # --- the balls out of the drum, down the chute, along the rack
    def _ball_path(self, i, t_out):
        hx, hy = DRUM[0] + math.cos(EMPTY_ANG) * (DRUM_R - 18), DRUM[1] + math.sin(EMPTY_ANG) * (DRUM_R - 18)
        cx1, cy1 = RACK[0] + 10, rack_y(RACK[0] + 10) - R0
        drop = cy1 - hy
        L = math.hypot(cx1 - hx, drop)
        a = 5.0 / 7.0 * GBALL * drop / L                          # rolling down the chute
        t_ch = math.sqrt(2 * L / a)
        v = a * t_ch
        slot = RACK[1] - 6 - R0 - (i + 1) * (2 * R0 + 2)          # behind Wheels' ball in the end slot
        d = slot - cx1
        ar = 5.0 / 7.0 * GBALL * (RACK_Y1 - RACK_Y0) / (RACK[1] - RACK[0]) - 120.0   # rack slope less rolling drag
        vx = v * (cx1 - hx) / L + 0.0
        # along the rack: x = cx1 + vx t + 0.5 ar t^2 until the slot (it meets the ball before it / the end stop)
        if ar < 0:
            disc = vx * vx + 2 * ar * d
            t_r = (-vx + math.sqrt(max(disc, 0.0))) / ar if disc > 0 else 2 * d / vx
        else:
            t_r = (-vx + math.sqrt(vx * vx + 2 * ar * d)) / ar
        return dict(t=t_out, h=(hx, hy), c=(cx1, cy1), t_ch=t_ch, vx=vx, ar=ar, t_r=t_r, slot=slot,
                    settle=t_out + t_ch + t_r + 0.35)

    def ball(self, i, t):
        """(x, y, spin, state) of ball i (None before it rolls out)."""
        b = self.balls[i]
        u = t - b["t"]
        if u < 0:
            return None
        (hx, hy), (cx1, cy1) = b["h"], b["c"]
        if u < b["t_ch"]:
            f = (u / b["t_ch"]) ** 2
            x, y = hx + (cx1 - hx) * f, hy + (cy1 - hy) * f
            return x, y, (x - hx) / R0, "rolls"
        u -= b["t_ch"]
        if u < b["t_r"]:
            x = cx1 + b["vx"] * u + 0.5 * b["ar"] * u * u
            return x, rack_y(x) - R0, (x - hx) / R0, "rolls"
        u -= b["t_r"]
        back = 5.0 * math.sin(math.pi * min(u / 0.35, 1.0)) if u < 0.35 else 0.0   # a little knock back
        x = b["slot"] - back
        ox, oy = self.tray_off(t)
        return x + ox, rack_y(x) - R0 + oy, (x - hx) / R0, ("rolls" if u < 0.4 else "in the rack")

    def colour_u(self, i, t):
        a, b = self.colour[i]
        return smoothstep(_seg(t, a + 0.7, b))

    def ball_col(self, i, t):
        return mix(PLAIN, MARBLE_COLS[KINDS[i]], self.colour_u(i, t))

    def glo_x(self, t):
        """Where Glo floats while colouring: over each ball in turn."""
        if t < self.colour[0][0]:
            return None
        for i, (a, b) in enumerate(self.colour):
            if t < b + 0.5:
                x = self.balls[i]["slot"]
                if i > 0 and t < a:
                    return x
                return x
        return self.balls[5]["slot"]

    # --- Wheels
    def wheels_spin(self, t):
        """Extra wheel turn (rad) while he drives the rollers on the spot."""
        w = self.wheels
        u = _seg(t, *w["drive"])
        # his wheels turn the drive rollers; the rollers' pulley drives the drum (ratio 1:2.4)
        return self.drum_total * 2.4 * smoothstep(u)

    def wheels_keys(self):
        w = self.wheels
        # after his ball is in, he rolls back out of the way (Glo colours the balls), and comes back for the tray
        return [(w["roll_on"][0], WHEELS_WAIT), (w["roll_on"][1], ROLLERS), (w["to_rack"][0], ROLLERS),
                (w["to_rack"][1], WHEELS_RACK), (w["place"][1] + 0.6, WHEELS_RACK),
                (w["place"][1] + 3.6, WHEELS_WAIT), (self.lift[0] - 3.6, WHEELS_WAIT), (self.lift[0] - 0.9, WHEELS_RACK)]

    def wheels_hands(self, t, x):
        """{side: world xy}: his ball into the end slot, then both pincers under the tray to lift it."""
        w = self.wheels
        a, b = w["place"]
        chest = (x + 112.0, G - 192.0)
        slot = (self.plain_slot, rack_y(self.plain_slot) - 2 * R0 + 2)
        if a - 0.2 <= t < b + 0.5:
            if t < a + 0.6:
                return {1: _ease(chest, slot, _seg(t, a - 0.2, a + 0.6))}
            if t < b:
                return {1: slot}
            return {1: _ease(slot, (x + 124.4, G - 65.8), _seg(t, b, b + 0.5))}
        a, b = self.lift
        rel = self.release                                        # the plan: when the tray is down on the bench
        if a - 0.8 <= t < rel + 0.6:
            u = smoothstep(_seg(t, a - 0.8, a)) * (1 - smoothstep(_seg(t, rel, rel + 0.6)))
            l0, r0 = (x - 124.4, G - 65.8), (x + 124.4, G - 65.8)
            lt, rt = self.tray_grips(t)                           # under the tray, wherever it is
            return {-1: _ease(l0, lt, u), 1: _ease(r0, rt, u)}
        return None

    # --- drawing
    def draw_back(self, pg, t, sh):
        """Behind the Keepers: the drum on its stand, its belt, the chute, the rack, the drive rollers."""
        x, y = DRUM[0] - sh, DRUM[1]
        for dx in (-70, 70):                                      # the stand's legs
            pg.shape(rrect(x + dx - 10, y + 30, x + dx + 10, BACK + 8, 4), WOOD3, 0.0)
        pg.shape(rrect(x - 110, y + DRUM_R - 4, x + 110, y + DRUM_R + 14, 5), WOOD2, 0.1)
        for dx in (-46, 46):                                      # the two support rollers
            pg.shape(oval(x + dx, y + DRUM_R - 6, 14, 14), (120, 110, 104), 0.1)
        # the belt: from the drive rollers' pulley up to the drum's axle pulley
        rx = ROLLERS - sh
        pg.stroke(skia.Path().moveTo(x + 22, y - 8).lineTo(rx + 12, G - 22), (98, 74, 58), 6.0)
        pg.stroke(skia.Path().moveTo(x - 22, y + 8).lineTo(rx - 12, G - 6), (98, 74, 58), 6.0)
        a = self.drum_ang(t)
        pg.shape(oval(x, y, DRUM_R, DRUM_R), WOOD, 0.12)          # the drum end-on: staves, two iron hoops
        for k in range(10):
            b = a + k * 2 * math.pi / 10
            pg.stroke(skia.Path().moveTo(x + math.cos(b) * 20, y + math.sin(b) * 20)
                      .lineTo(x + math.cos(b) * (DRUM_R - 4), y + math.sin(b) * (DRUM_R - 4)), tone(WOOD, -0.1), 2.0)
        pg.stroke(skia.Path().addOval(skia.Rect(x - DRUM_R + 6, y - DRUM_R + 6, x + DRUM_R - 6, y + DRUM_R - 6)),
                  (110, 104, 100), 5.0)
        # the hatch: the opening (dark when open) and its lid
        op = self.hatch_open(t)
        p = skia.Path()
        for j in range(9):
            b = a - HATCH_W / 2 + HATCH_W * j / 8
            (p.moveTo if j == 0 else p.lineTo)(x + math.cos(b) * DRUM_R, y + math.sin(b) * DRUM_R)
        for j in range(9):
            b = a + HATCH_W / 2 - HATCH_W * j / 8
            p.lineTo(x + math.cos(b) * (DRUM_R - 34), y + math.sin(b) * (DRUM_R - 34))
        p.close()
        pg.flat(p, mix(tone(WOOD, -0.2), (46, 34, 28), op))
        (hx, hy), (ex, ey) = self.hatch_lid(t)
        pg.stroke(skia.Path().moveTo(hx - sh, hy).lineTo(ex - sh, ey), (96, 84, 78), 8.0)
        pg.shape(oval(x, y, 18, 18), (110, 104, 100), 0.1)        # the axle and its pulley
        pg.shape(oval(x, y, 7, 7), (80, 74, 70), 0.0)
        # the chute from under the hatch down to the rack, the rack and its end stop
        hx2, hy2 = DRUM[0] + math.cos(EMPTY_ANG) * (DRUM_R + 2) - sh, DRUM[1] + math.sin(EMPTY_ANG) * (DRUM_R + 2)
        cx1, cy1 = RACK[0] + 10 - sh, rack_y(RACK[0] + 10)
        pg.stroke(skia.Path().moveTo(hx2 - 6, hy2 + 4).lineTo(cx1, cy1 + 4), WOOD2, 12.0)
        x0, x1 = RACK[0] - sh, RACK[1] - sh
        for lx in (x0 + 20, x1 - 20):                             # the rack's legs (the tray lifts off them)
            pg.shape(rrect(lx - 6, RACK_Y0 + 14, lx + 6, BACK + 8, 3), WOOD3, 0.0)
        if self.tray_off(t) == (0.0, 0.0):
            draw_tray(pg, x0, x1, 0.0)
        # the drive rollers Wheels rolls onto
        spin = self.wheels_spin(t)
        for dx in (-38, 38):
            cx = ROLLERS + dx * K * 1.9 - sh
            pg.shape(oval(cx, G - 8, 14, 14), (120, 110, 104), 0.1)
            pg.stroke(skia.Path().moveTo(cx, G - 8).lineTo(cx + math.cos(-spin * 3.3) * 12,
                                                          G - 8 + math.sin(-spin * 3.3) * 12), (80, 74, 70), 2.5)
        pg.shape(rrect(ROLLERS - 110 - sh, G - 4, ROLLERS + 110 - sh, G + 8, 4), WOOD3, 0.0)

    def draw_balls(self, pg, t, sh):
        for i in range(6):
            s = self.ball(i, t)
            if s is not None:
                x, y, sp, _ = s
                draw_marble(pg, x - sh, y, R0, self.ball_col(i, t), ang=sp, band=self.colour_u(i, t) > 0.3,
                            a=self.colour_u(i, t))

    def draw_front(self, pg, t, sh):
        """In front of the Keepers: the sawhorse and the beam, the cubes, the basket, the sawdust."""
        x0, x1 = self.beam_left() - 30 - sh, self.stop + 60 - sh
        for lx in (x0 + 40, x1 - 40):
            pg.shape(rrect(lx - 9, BT, lx + 9, G + 30, 3), WOOD3, 0.0)
        pg.shape(rrect(x0, BT, x1, BT + 16, 5), WOOD2, 0.1)
        pg.shape(rrect(self.stop - sh, BT - CUBE - 10, self.stop + 26 - sh, BT, 3), WOOD3, 0.1)   # the stop block
        # the beam (its right end cut back cube by cube, slid up to the stop block again)
        br = self.beam_right(t)
        pg.shape(rrect(self.beam_left(t) - sh, BT - BEAM_T, br - sh, BT, 3), PLAIN, 0.1)
        for gx in np.arange(self.beam_left(t) + 30, br - 10, 46):
            pg.stroke(skia.Path().moveTo(gx - sh, BT - BEAM_T + 8).lineTo(gx + 20 - sh, BT - BEAM_T + 14),
                      tone(PLAIN, -0.1), 1.4)
        S = saw_setup()
        pg.stroke(skia.Path().moveTo(self.cut - sh, BT - BEAM_T - 8).lineTo(self.cut - sh, BT - BEAM_T - 2),
                  (90, 70, 56), 2.0)                              # the cut line, pencilled
        for c in self.cuts:                                       # the kerf as it is cut
            if c["saw"][0] <= t < c["saw"][1]:
                d = smoothstep(_seg(t, *c["saw"]))
                pg.flat(rrect(self.cut - 2.5 - sh, BT - BEAM_T, self.cut + 2.5 - sh, BT - BEAM_T + BEAM_T * d, 1),
                        tone(PLAIN, -0.35))
        # the basket
        bx, by = self.basket_pos(t)
        tilt = self.basket_tilt(t)
        for j in range(6):
            s = self.cube(j, t)
            if s is not None:
                cx, cy, ang, _ = s
                c = pg.c
                c.save()
                c.rotate(ang, cx - sh, cy)
                pg.shape(rrect(cx - CUBE / 2 - sh, cy - CUBE / 2, cx + CUBE / 2 - sh, cy + CUBE / 2, 4), PLAIN, 0.12)
                c.restore()
        c = pg.c
        c.save()
        c.rotate(tilt, bx - sh, by)
        pg.shape(smooth([(bx - 62 - sh, by - 46), (bx + 62 - sh, by - 46), (bx + 50 - sh, by), (bx - 50 - sh, by)]),
                 (176, 132, 84), 0.12)
        for k in range(1, 4):
            pg.stroke(skia.Path().moveTo(bx - 60 + k * 3 - sh, by - 46 + k * 11).lineTo(bx + 60 - k * 3 - sh,
                                                                                       by - 46 + k * 11),
                      (150, 108, 70), 2.0)
        c.restore()
        for d in self.dust:
            p = self.dust_pos(d, t)
            if p is not None:
                pg.flat(oval(p[0] - sh, p[1], d["r"], d["r"] * 0.8), (232, 206, 160),
                        1 - smoothstep(_seg(t, d["t"] + 0.9, d["t"] + 1.4)))
        # the drum's sawdust puffs while it turns
        w = self.wheels
        if w["drive"][0] < t < w["drive"][1] + 1.5:
            for q in range(10):
                tq = w["drive"][0] + 0.4 + q * 0.95
                u = t - tq
                if 0 <= u < 1.4:
                    a = self.drum_ang(tq) + q
                    px = DRUM[0] + math.cos(a) * DRUM_R + 30 * u * math.cos(a) - sh
                    py = DRUM[1] + math.sin(a) * DRUM_R - 40 * u
                    pg.flat(oval(px, py, 9 + 14 * u, 7 + 10 * u), (238, 220, 186), 0.5 * (1 - u / 1.4))

    def draw_lights(self, pg, t, sh, glo):
        """Glo's flare over each ball: light gathers under his dome, a mote drifts down to it, sparkles fall on it."""
        gx, gy = glo
        for i, (a, b) in enumerate(self.colour):
            if a <= t < b + 0.6:
                s = self.ball(i, t)
                if s is None:
                    continue
                bx, by = s[0], s[1]
                fl = smoothstep(_seg(t, a, a + 0.4)) * (1 - smoothstep(_seg(t, b - 0.2, b + 0.4)))
                pg.glow(gx - sh, gy - 170 * K, 90, "#ffe9b0", 0.55 * fl)
                u = smoothstep(_seg(t, a + 0.2, a + 0.9))
                mx, my = gx + (bx - gx) * u, (gy - 150 * K) + (by - 30 - (gy - 150 * K)) * u
                if u < 1:
                    pg.glow(mx - sh, my, 34, "#fff1c8", 0.7 * fl)
                    pg.flat(oval(mx - sh, my, 5, 5), "#fff8e0", fl)
                for q in range(7):                                # sparkles drifting down onto it
                    tq = a + 0.7 + q * 0.11
                    v = t - tq
                    if 0 <= v < 0.7:
                        px = bx + (q - 3) * 7 + 4 * math.sin(q * 2.1 + v * 5)
                        py = by - 46 + 52 * v
                        pg.flat(oval(px - sh, py, 3.2, 3.2), MARBLE_COLS[KINDS[i]], 1 - v / 0.7)
                        pg.flat(oval(px - sh, py, 1.6, 1.6), "#fffbe8", 1 - v / 0.7)

    # --- the checks
    def things(self, t, sh, twigs_hand, hans_tip):
        out = {}
        for j in range(6):
            s = self.cube(j, t)
            c = self.cuts[j]
            if s is None:
                continue
            x, y, ang, st = s
            held, moves, born, gone = None, None, None, None
            if t - c["saw"][1] < 0.04:
                born = "sawn off the beam by Twigs' blade"
            if st == "on the sawhorse":
                pass
            elif st == "tipped by Twigs' hand":
                held = ("Twigs' right hand", twigs_hand(t))
            elif st == "falls":
                moves = "falls"
            elif st in ("in the basket", "tipped out of the basket"):
                if self.hans["lift"][0] <= t:
                    held = ("the basket Hans carries", (x - sh, y))
            nxt = self.cube(j, t + 1 / 30)
            if nxt is None and st == "falls":
                gone = ("into the tumbler's hatch", (self.hatch_pos(t)[0] - sh, self.hatch_pos(t)[1]))
            out[f"cube {j}"] = sc.Thing(x - sh, y, CUBE / 2, held=held, moves=moves, born=born, gone=gone)
        bx, by = self.basket_pos(t)
        h = self.hans
        held = ("Hans' tentacles", hans_tip(t)) if h["lift"][0] <= t < h["back"][1] else None
        out["the basket"] = sc.Thing(bx - sh, by - 23, 46, held=(held[0], (bx - sh, by - 23)) if held else None)
        for i in range(6):
            s = self.ball(i, t)
            if s is None:
                continue
            x, y, _, st = s
            born = "rolls out of the tumbler's hatch" if t - self.balls[i]["t"] < 0.04 else None
            out[f"marble {KINDS[i]}"] = sc.Thing(x - sh, y, R0, born=born, moves="rolls" if st == "rolls" else None)
        return out


def draw_tray(pg, x0, x1, dy):
    """The rack-tray (screen x0..x1, raised dy): a level channel with an end stop at its right."""
    y = RACK_Y0 + dy
    pg.shape(rrect(x0, y, x1, y + 16, 4), WOOD2, 0.1)
    pg.flat(rrect(x0 + 2, y - 4, x1 - 2, y + 2, 2), tone(WOOD2, 0.06))
    pg.shape(rrect(x1 - 4, y - 40, x1 + 8, y + 16, 3), WOOD3, 0.0)
    pg.shape(rrect(x0 - 8, y - 22, x0 + 4, y + 16, 3), WOOD3, 0.0)
