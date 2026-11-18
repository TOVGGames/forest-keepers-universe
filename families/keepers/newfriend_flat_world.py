"""Forest Keepers ep 12, A New Friend from the Factory, in the flat picture-book look: the world
(docs/engines/forest_keepers_new_friend_flat.md). Two places, each its own strip of world x:

    VILLAGE   the Keepers' treehouse, the old oak (its dead branch), the acorn stump, the path up the hill; the
              night-shift factory far off on the hill, its door lit. At night (beat 1) and just before dawn (beat 3).
    HALL      the night-shift factory inside: one compact line (HOIST, CUT, TURN, CARVE, FIT, PLANT/ORB) on its
              deck, the walkway in front, the door the Keepers come in by at the right end, right by the walkway's
              watching spot (no long walks: owner, FK0019).

The camera pans and zooms as in the marble run (marble_flat_world): everything is drawn in working coords (world x
minus the pan, world y = the frame at zoom 1); a pulled-back frame is painted at that scale on a bigger page and
scaled down as a whole, so the grain shrinks with what it is printed on.
"""
import math

import numpy as np
import skia

from .flat import PAL, FlatPage, bush, hill_band, leaf, lolly_tree, pine, poplar, treehouse, tuft
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
G = H * 0.93                        # the Keepers' feet (the path; the hall's walkway)
BACK = G - 40.0                     # just behind the path: the trees' feet; in the hall, the line deck's front foot
ZMIN = 0.6

TRUNK = (138, 100, 76)
TRUNK_D = (118, 84, 64)
OAK_BARK = (98, 74, 70)       # the old oak: a darker, greyer bark than Twigs' wood-brown antler tips, so they
OAK_BARK_D = (82, 62, 58)     # still read over it (fresh agent, FK0024 round 8: they melted into the trunk)
WOOD, WOOD2, WOOD3 = (205, 158, 108), (186, 136, 92), (160, 116, 80)
LAMP = (246, 212, 138)
MOON = "#f3ead0"

# ---- the village (world x)
TREEHOUSE = 1500.0
OAK_X = 2900.0                      # the old oak by the path: the dead branch on its left
STUMP_X = 3994.0                    # a little stump (the acorns on it; later the watering can)
PLANT_X = 3520.0                    # where Sprout's first tree comes up: right of where the first dead branch lies
#                                     (2995-3289), its hole's lip 70 px clear of the branch's tip (fresh agent, FK0024
#                                     round 12: the log ran into the hole and under the fill); the stump and the
#                                     others at home moved along with it, so the planting's own spacing is unchanged
HILL_DOOR = 5650.0                  # the factory on the hill (far: in the mid layer, so its x is a screen anchor)
VILLAGE_W = 7600.0

# ---- the hall (world x)
STATION = {"hoist": 1250.0, "cut": 1700.0, "turn": 2150.0, "carve": 2600.0, "fit": 3050.0, "plant": 3500.0}
DECK_Y = G - 64.0                   # the line deck's top (the jig cart runs on it)
DECK_X = (950.0, 3780.0)
WATCH = (3900.0, 4900.0)            # the walkway spot the Keepers watch from
LOG_STORE = (230.0, 800.0)           # the log store's opening in the back wall (the hoist comes out of it)
DOOR = (5020.0, 5460.0)             # the way in and out (doorway: they walk into the opening)
HALL_W = 6200.0
HALL = dict(wall_top="#28324a", wall_low="#36425a", pillar="#3e4b63", beam="#4a5873", floor="#4a4a52",
            floor_low="#3e3e46", walk="#58585f", belt="#2c3140", frame="#55617a", pallet="#c79a4a", lamp="#ffe0a0",
            cone="#f6d28a", steel="#68758e", steel2="#5a667e", sign="#f0dcb4", night="#1c2944", door="#59647a",
            hazard="#c9a050", bin="#4e5a52", bin2="#5c685f")

X0 = W / 2 - W / (2 * ZMIN)
Y0 = G - G / ZMIN
WB, HB = int(math.ceil(W / ZMIN)) + 8, int(math.ceil(H / ZMIN)) + 8


# ----------------------------------------------------------------------------------------------- the camera

def _ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class Cam:
    """keys [(t, x, z)]: the frame's middle (world x) and zoom; eased from key to key (it holds at each key)."""

    def __init__(self, keys):
        self.keys = sorted(keys)

    def __call__(self, t):
        k = self.keys
        if t <= k[0][0]:
            return k[0][1], k[0][2]
        for (t0, x0, z0), (t1, x1, z1) in zip(k, k[1:]):
            if t <= t1:
                u = _ss((t - t0) / max(t1 - t0, 1e-9))
                return x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
        return k[-1][1], k[-1][2]


def to_frame(X, Y, z):
    """Working coords -> the finished frame's px at zoom z."""
    return W / 2 + (X - W / 2) * z, G + (Y - G) * z


class Page:
    """The page frame t is painted on: the normal 1920x1080 FlatPage at zoom 1, a bigger one when pulled back."""

    _cache = {}

    def __init__(self, z, seed=3):
        self.z = z
        self.big = z < 0.999
        self.close = z > 1.001                   # a close shot: the normal page, cropped and scaled up
        key = "big" if self.big else "small"
        if key not in Page._cache:
            pg = FlatPage(WB, HB, seed=seed) if self.big else FlatPage(W, H, seed=seed)
            pg._sc = 1.0
            Page._cache[key] = pg
        self.pg = pg = Page._cache[key]
        self.ox, self.oy = (-X0, -Y0) if self.big else (0.0, 0.0)
        pg.c.restoreToCount(1)
        pg.c.resetMatrix()
        pg.c.clear(skia.ColorWHITE)
        pg.c.save()
        pg.c.translate(self.ox, self.oy)
        pg.ox, pg.oy = self.ox, self.oy

    def visible(self):
        z = self.z
        return W / 2 - W / (2 * z), W / 2 + W / (2 * z), G - G / z, G + (H - G) / z

    def final(self):
        pg = self.pg
        if not self.big and not self.close:
            return pg
        x0, x1, y0, y1 = self.visible()
        src = skia.Rect(x0 + self.ox, y0 + self.oy, x1 + self.ox, y1 + self.oy)
        out = _out()
        img = pg.surface.makeImageSnapshot()
        out.c.resetMatrix()
        out.c.drawImageRect(img, src, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.CubicResampler.Mitchell()),
                            None, skia.Canvas.kStrict_SrcRectConstraint)
        return out


_OUT = {}


def _out():
    if "p" not in _OUT:
        p = FlatPage(W, H, seed=3)
        p._sc = 1.0
        p.ox = p.oy = 0.0
        _OUT["p"] = p
    return _OUT["p"]


def raw(pg):
    """Context: draw in the page's own px (no working-coords translation)."""
    class _R:
        def __enter__(self):
            pg.c.save()
            pg.c.resetMatrix()
            return pg

        def __exit__(self, *a):
            pg.c.restore()
    return _R()


# ----------------------------------------------------------------------------------------------- the light

# night (beat 1), the hall (its own lamps), before dawn (beat 3): sky top, mid, low; multiply over the page
SKIES = {"night": ("#17213e", "#2b3a5e", "#3c4a6c", (0.70, 0.74, 0.90), 1.0),
         "predawn": ("#2b3a66", "#7a7ea6", "#e0a998", (0.86, 0.84, 0.92), 0.55)}


def sky(P, t, mood, sh):
    """The sky over the whole page: a gradient, stars (fixed to the far sky: they drift a little with the pan),
    the moon. mood: (a, b, u) between two SKIES."""
    pg = P.pg
    a, b, u = mood
    A, B = SKIES[a], SKIES[b]
    top, mid, low = (mix(A[i], B[i], u) for i in range(3))
    stars = A[4] + (B[4] - A[4]) * u
    x0, x1, y0, y1 = P.visible()
    with raw(pg):
        ty0, ty1 = y0 + P.oy, y0 + P.oy + (y1 - y0) * 0.66
        g = skia.GradientShader.MakeLinear([(0, ty0), (0, ty1)], [C(top), C(mid), C(low)], [0, 0.55, 1])
        pg.c.drawPaint(skia.Paint(Shader=g))
    rs = np.random.default_rng(61)
    for _ in range(260):
        sx, sy = rs.uniform(-600, VILLAGE_W * 0.04 + W + 600), rs.uniform(-260, H * 0.42)
        X = sx - sh * 0.04
        if not (x0 - 10 < X < x1 + 10):
            continue
        tw = 0.65 + 0.35 * math.sin(t * rs.uniform(0.6, 1.6) + rs.uniform(0, 6.3))
        r = rs.uniform(1.2, 2.4)
        pg.flat(oval(X, sy, r, r), "#f4ecd2", 0.8 * tw * stars)
    mx, my = W * 0.24 - sh * 0.04 + 300, H * 0.13
    pg.flat(oval(mx, my, 96, 96), MOON, 0.16 * stars, blur=32)
    pg.flat(oval(mx, my, 46, 46), mix("#c9c3b4", MOON, stars))
    pg.flat(oval(mx - 13, my - 9, 9, 9), tone(MOON, -0.06), stars)
    pg.flat(oval(mx + 15, my + 12, 6, 6), tone(MOON, -0.05), stars)
    with raw(pg):
        pg.c.drawPaint(skia.Paint(Shader=pg.grain_shader(), BlendMode=skia.BlendMode.kSrcOver))


def multiply(pg, mul):
    """The night: a soft multiply over everything painted so far (lights painted after it stay lit)."""
    col = skia.Color(*(int(round(255 * m)) for m in mul))
    with raw(pg):
        pg.c.drawPaint(skia.Paint(Color=col, BlendMode=skia.BlendMode.kMultiply))


def sky_mul(mood):
    a, b, u = mood
    A, B = SKIES[a], SKIES[b]
    return tuple(p + (q - p) * u for p, q in zip(A[3], B[3]))


# ----------------------------------------------------------------------------------------------- village layers

def _hills(p, y, amp, seed, col, step=520.0, light_=0.05, dark=0.06):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H + 400, col, light_, dark)


def _v_far(p):
    _hills(p, H * 0.56, H * 0.09, 21, PAL["far"], 640.0)


def _v_far2(p):
    _hills(p, H * 0.61, H * 0.05, 22, PAL["far2"], 560.0)


def _v_far_trees(p):
    rs = np.random.default_rng(23)
    x = 20.0
    i = 0
    while x < p.strip:
        (pine if i % 3 else lolly_tree)(p, x, H * 0.635, H * rs.uniform(0.06, 0.08),
                                        tone(PAL["pine"] if i % 3 else PAL["olive"], 0.18))
        x += rs.uniform(70, 140)
        i += 1


FACTORY_MID = 0.35                  # the mid layer's depth (the factory sits on its hill)


def factory_mid_x(sh):
    """Working x of the factory's door (mid layer) for pan sh."""
    return HILL_DOOR * FACTORY_MID + 900.0 - sh * FACTORY_MID


def _v_mid(p):
    _hills(p, H * 0.67, H * 0.04, 24, PAL["mid"], 480.0)
    rs = np.random.default_rng(25)
    fx = HILL_DOOR * FACTORY_MID + 900.0                   # working x of the factory door at pan 0
    # the factory's hill: a rounded rise; the factory on top (a long low hall, a chimney, the big door)
    hill = smooth([(fx - 700, H * 0.69), (fx - 380, H * 0.6), (fx - 40, H * 0.55), (fx + 340, H * 0.57),
                   (fx + 720, H * 0.66), (fx + 900, H * 0.7)])
    hill.lineTo(fx + 900, H + 400)
    hill.lineTo(fx - 700, H + 400)
    hill.close()
    p.shape(hill, tone(PAL["mid"], -0.04), 0.05)
    fy = H * 0.555
    p.shape(rrect(fx - 220, fy - 120, fx + 260, fy + 6, 6), (96, 104, 122), 0.06)
    p.shape(skia.Path().moveTo(fx - 236, fy - 116).lineTo(fx + 276, fy - 116).lineTo(fx + 250, fy - 150)
            .lineTo(fx - 210, fy - 150).close(), (78, 84, 100), 0.0)
    p.shape(rrect(fx + 150, fy - 230, fx + 186, fy - 140, 4), (88, 92, 108), 0.0)
    p.flat(rrect(fx - 40, fy - 78, fx + 40, fy + 4, 6), (40, 44, 56))           # the door (lit live)
    for wx in (fx - 170, fx - 110, fx + 100, fx + 170):
        p.flat(rrect(wx - 16, fy - 92, wx + 16, fy - 62, 4), (40, 44, 56))      # windows (lit live)
    x = 60.0
    # no orange: an orange tree behind Hans' head read as part of him, a cone hat / a balloon (fresh agent, FK0024
    # round 6); a deeper gold in its place (same draws, so every tree keeps its spot)
    cols = [PAL["ochre"], tone(PAL["ochre"], -0.16), PAL["pine"], PAL["pink"], PAL["olive"]]
    i = 0
    while x < p.strip:
        if abs(x - fx) > 520:
            f = (poplar, lolly_tree, pine, lolly_tree, poplar)[int(rs.integers(0, 5))]
            h, c = H * rs.uniform(0.13, 0.19), cols[int(rs.integers(0, 5))]
            if i not in MID_SKIP:
                f(p, x + MID_NUDGE.get(i, 0.0), H * 0.675, h, c)
            i += 1
        x += rs.uniform(150, 280)


# mid-layer trees that stood right behind a Keeper's head for long stretches, so they read as part of him (fresh
# agent, FK0024 round 6: a cone "hat" on Hans, a "balloon" on his head in the finale, a ball behind Twigs' antlers):
# nudged aside or left out (worked out from every frame's camera and Keeper positions; scratchpad tree_heads.py)
MID_NUDGE = {}
MID_SKIP = {4, 5, 6, 7, 8, 9, 10}   # (every mid tree that stood behind a head for seconds at a time)


def factory_lights(pg, sh, lit=1.0):
    """The factory's door and windows, lit (drawn after the night multiply, so they glow)."""
    fx = factory_mid_x(sh)
    fy = H * 0.555
    pg.glow(fx, fy - 40, 150, "#ffd890", 0.4 * lit)
    pg.flat(rrect(fx - 34, fy - 72, fx + 34, fy + 2, 5), "#f2c878", lit)
    for wx in (fx - 170, fx - 110, fx + 100, fx + 170):
        pg.flat(rrect(wx - 12, fy - 88, wx + 12, fy - 66, 3), "#ffd890", 0.9 * lit)


def _v_field(p):
    _hills(p, H * 0.75, H * 0.03, 26, PAL["field"], 600.0, 0.06, 0.04)
    rs = np.random.default_rng(27)
    x = 200.0
    while x < p.strip:
        bush(p, x, H * rs.uniform(0.74, 0.76), H * rs.uniform(0.03, 0.045), tone(PAL["olive"], -0.05))
        x += rs.uniform(600, 1200)


OAK_TOP = BACK - 1000.0
OAK_FOOT = BACK - 30.0                  # the oak's flat foot, on the grass behind the path
DEAD = [(OAK_X - 60, BACK - 262), (OAK_X - 250, BACK - 300), (OAK_X - 390, BACK - 292)]   # the dead branch
# (50 px lower too, like DEAD2: the cut beside Twigs' head, clear of his antlers; Hans' tentacles reach it without
# stretching - fresh agents, FK0024 round 6)
DEAD2_CUT_U = 0.555                  # where branch 1 (DEAD2) is cut: out past Twigs' head (fresh agent, FK0024
#                                     round 16: at 0.22 his head and hand hid the saw cut)
DEAD2 = [(OAK_X + 60, BACK - 256), (OAK_X + 240, BACK - 296), (OAK_X + 390, BACK - 288)]  # the second (beat 3)
# (50 px lower than it was: its cut point sat in among Twigs' antler tines; now it's beside his head, below them -
# fresh agent, FK0024 round 6)


def oak(p):
    """The old oak by the path: a thick trunk, two low limbs where the dead branches grow from (they're drawn live:
    they come off), the big round crown high up."""
    x, y = OAK_X, BACK + 6
    # its foot on the grass well behind the path, cut flat with two root flares and a soft shadow (fresh agent,
    # FK0024 round 13: its round foot reached the path, so Twigs and Digs in front of it read as pressed into it)
    yf = OAK_FOOT
    p.shadow(x, yf + 2, 112, 11, 0.3)
    p.c.save()
    p.c.clipRect(skia.Rect(x - 400, -10000, x + 400, yf))
    p.shape(tube([(x, y - 30), (x + 10, y - 400), (x - 8, OAK_TOP + 200)], 70, 46), OAK_BARK, 0.12, (-0.5, 0.0))
    p.c.restore()
    for sx in (-1, 1):
        p.shape(tube([(x + sx * 52, yf - 46), (x + sx * 84, yf - 12), (x + sx * 104, yf)], 20, 5), OAK_BARK, 0.1)
    for q in range(7):
        yy = y - 80 - q * 110
        p.stroke(skia.Path().moveTo(x - 36, yy).quadTo(x, yy - 18, x + 30, yy - 4), OAK_BARK_D, 3.5, 0.7)
    for pts in ([(x - 20, y - 660), (x - 230, y - 760), (x - 360, y - 830)],
                [(x + 20, y - 700), (x + 220, y - 790), (x + 330, y - 860)]):
        p.shape(tube(pts, 26, 12), OAK_BARK, 0.1, (0.0, -0.4))
    for dx, dy, r, col in ((-240, -860, 220, PAL["olive"]), (40, -960, 250, PAL["ochre"]),
                           (270, -870, 200, PAL["orange"]), (-60, -800, 200, tone(PAL["olive"], 0.05)),
                           (170, -770, 170, tone(PAL["ochre"], -0.05)), (-330, -760, 140, PAL["orange"])):
        p.shape(oval(x + dx, y + dy, r, r * 0.9), col, 0.1)
    for pts in (DEAD, DEAD2):                                   # the stubs the dead branches are cut back to
        a, b = pts[0], pts[1]
        u = DEAD2_CUT_U if pts is DEAD2 else 0.22
        q = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        p.shape(tube([(x + (a[0] - x) * 0.4, a[1] + 10), q], 15, 13), OAK_BARK, 0.1, (0.0, -0.4))


STUMP_Y = BACK - 4                   # the stump's foot: on the grass behind the path, with the trees (fresh agent,
#                                     FK0024 round 11: at BACK + 30 it stood in the path, where Wheels was parked)


def stump(p, x):
    y = STUMP_Y
    p.shape(rrect(x - 52, y - 70, x + 52, y + 6, 10), TRUNK, 0.1)
    p.flat(oval(x, y - 70, 52, 13), (206, 168, 122))
    p.stroke(oval(x, y - 70, 32, 8), (176, 138, 98), 2.0)
    p.stroke(oval(x, y - 70, 16, 4), (176, 138, 98), 2.0)


STUMP_TOP = STUMP_Y - 70


def _v_ground(p):
    hill_band(p, [(x, H * 0.8 + 6 * math.sin(x / 700.0)) for x in np.arange(-100.0, p.strip + 400, 400.0)], H + 400,
              PAL["ground"], 0.06, 0.08)
    top = [(x, G - 26 + 4 * math.sin(x / 900.0)) for x in np.arange(-100.0, p.strip + 300, 300.0)]
    bot = [(x, G + 44 + 5 * math.sin(x / 1100.0 + 1)) for x in np.arange(p.strip + 300, -400.0, -300.0)]
    p.flat(smooth(top + bot), PAL["path"], 0.85)
    treehouse(p, TREEHOUSE, BACK + 8, 760)
    oak(p)
    stump(p, STUMP_X)
    rs = np.random.default_rng(33)
    for i in range(int(p.strip / 50)):
        x = rs.uniform(0, p.strip)
        y = G + rs.uniform(50, 130) if rs.random() < 0.5 else BACK - rs.uniform(-4, 90)
        if (abs(x - TREEHOUSE) < 300 or abs(x - PLANT_X) < 120 or abs(x - STUMP_X) < 90) and y < G:
            continue
        tuft(p, x, y, H * rs.uniform(0.014, 0.022), tone(PAL["ground"], -0.14))
        leaf(p, x + rs.uniform(-40, 40), y + rs.uniform(-6, 10), H * 0.007, rs.uniform(0, 180),
             (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])


def village_layers():
    return [("far", 0.08, _v_far), ("far2", 0.14, _v_far2), ("far_trees", 0.2, _v_far_trees),
            ("mid", FACTORY_MID, _v_mid), ("field", 0.55, _v_field), ("ground", 1.0, _v_ground)]


# ----------------------------------------------------------------------------------------------- hall layers

def _h_back(p):
    """The back wall (a gradient), pillars, beams, the lamp housings and their soft warm cones, the floor."""
    s = p.strip
    p.grad(skia.Path().addRect(skia.Rect(-200, Y0 - 50, s + 200, G)), HALL["wall_top"], HALL["wall_low"])
    top = G - 1300
    for gx in np.arange(200.0, s, 700.0):
        p.flat(skia.Path().addRect(skia.Rect(gx, top, gx + 46, G)), HALL["pillar"])
    p.flat(skia.Path().addRect(skia.Rect(-200, top - 400, s + 200, G - 1180)), HALL["beam"])
    for gy in (G - 1000, G - 430):
        p.flat(skia.Path().addRect(skia.Rect(-200, gy - 5, s + 200, gy + 5)), HALL["pillar"])
    for lx in np.arange(550.0, s, 700.0):
        p.flat(skia.Path().moveTo(lx - 42, G - 900).lineTo(lx + 42, G - 900).lineTo(lx + 300, G)
               .lineTo(lx - 300, G).close(), HALL["cone"], 0.07, blur=14)
        p.stroke(skia.Path().moveTo(lx, G - 1180).lineTo(lx, G - 905), HALL["pillar"], 3.0)
        p.shape(skia.Path().moveTo(lx - 40, G - 868).lineTo(lx + 40, G - 868).lineTo(lx + 22, G - 902)
                .lineTo(lx - 22, G - 902).close(), HALL["steel2"], 0.06)
        p.flat(oval(lx, G - 864, 22, 22), HALL["lamp"], 0.35, blur=10)
        p.flat(oval(lx, G - 864, 11, 11), HALL["lamp"])
    p.flat(skia.Path().addRect(skia.Rect(-200, G - 6, s + 200, G + 700)), HALL["floor"])
    p.flat(skia.Path().addRect(skia.Rect(-200, G + 70, s + 200, G + 700)), HALL["floor_low"])
    # the log store: an opening in the back wall where the line starts, logs stacked in the dark inside, the hoist's
    # rail running on into it (fresh agent, FK0024 round 11: the hoist and its log came in past the rail's end, out
    # of a blank wall)
    s0, s1 = LOG_STORE
    p.flat(skia.Path().addRect(skia.Rect(s0, G - 880, s1, G - 6)), (24, 29, 42))
    rs = np.random.default_rng(7)
    for row in range(4):
        for i in range(7 - row):
            lx = s0 + 70 + row * 34 + i * 68 + rs.uniform(-4, 4)
            ly = G - 40 - row * 62
            p.flat(oval(lx, ly, 32, 32), (92, 70, 54))
            p.flat(oval(lx, ly, 25, 25), (126, 98, 72))
            p.stroke(oval(lx, ly, 13, 13), (100, 78, 58), 2.0)
    p.flat(skia.Path().addRect(skia.Rect(s0, G - 880, s1, G - 6)), (24, 29, 42), 0.35)   # in the store's shade
    p.shape(rrect(s0 - 24, G - 904, s1 + 24, G - 880, 2), HALL["steel2"], 0.06)
    p.shape(rrect(s0 - 24, G - 880, s0, G, 2), HALL["steel2"], 0.06)
    p.shape(rrect(s1, G - 880, s1 + 24, G, 2), HALL["steel2"], 0.06)
    # the overhead rail the orb trolley and the hoist run on (from inside the log store)
    p.flat(skia.Path().addRect(skia.Rect(s0 + 10, G - 800, WATCH[0] + 200, G - 786)), HALL["steel"])
    # the door's frame (the opening itself and the night outside are live: the door rolls up)
    d0, d1 = DOOR
    p.shape(rrect(d0 - 24, G - 566, d1 + 24, G - 520, 2), HALL["steel2"], 0.06)
    p.shape(rrect(d0 - 24, G - 520, d0, G, 2), HALL["steel2"], 0.06)
    p.shape(rrect(d1, G - 520, d1 + 24, G, 2), HALL["steel2"], 0.06)


def _h_deck(p):
    """The line deck: a long low steel deck the jig cart runs on, its rail, the station frames and their signs."""
    from .christmas_flat import _font
    x0, x1 = DECK_X
    p.shape(rrect(x0, DECK_Y, x1, G + 6, 4), HALL["belt"], 0.05)
    p.flat(skia.Path().addRect(skia.Rect(x0, DECK_Y - 6, x1, DECK_Y + 4)), HALL["frame"])
    for bx in np.arange(x0 + 40, x1 - 20, 90.0):
        p.flat(oval(bx, (DECK_Y + G) / 2, 9, 9), tone(HALL["belt"], 0.1))
    f = _font(40, "Bold")
    for name, sx in STATION.items():
        label = {"hoist": "LOGS", "cut": "CUT", "turn": "TURN", "carve": "CARVE", "fit": "FIT", "plant": "PLANT"}[name]
        p.shape(rrect(sx - 200, G - 760, sx - 186, DECK_Y, 3), HALL["frame"], 0.04)
        p.shape(rrect(sx + 186, G - 760, sx + 200, DECK_Y, 3), HALL["frame"], 0.04)
        p.shape(rrect(sx - 200, G - 774, sx + 200, G - 752, 3), HALL["frame"], 0.04)
        sg = sx - 120.0 if name == "hoist" else sx    # (LOGS: off to the side, clear of the hoist's chain)
        dy = -154.0 if name in ("hoist", "cut", "turn") else 0.0   # LOGS, CUT: up on the wall over the hoist's rail, out of
        # the hook's and chain's way as it runs between them (fresh agent, FK0024 round 8: it ran through the plates)
        p.shape(rrect(sg - 110, G - 730 + dy, sg + 110, G - 672 + dy, 6), (42, 48, 64), 0.04)
        tw = f.measureText(label)
        p.c.drawString(label, sg - tw / 2, G - 686 + dy, f, skia.Paint(AntiAlias=True, Color=C(HALL["sign"])))
        p.flat(oval(sg + 88, G - 701 + dy, 7, 7), HALL["hazard"])
    # CUT again on the deck's front, right under the cut, so the saw's station is named in its close shot too (fresh
    # agent, FK0024 round 9: with CUT up over the rail, only TURN was in frame beside the disc saw)
    # (TURN too, its wall sign also up over the rail: round 10, a big TURN sign stood beside the disc saw)
    f2 = _font(30, "Bold")
    for name, label in (("cut", "CUT"), ("turn", "TURN")):
        sx = STATION[name]
        p.shape(rrect(sx - 84, DECK_Y + 12, sx + 84, G - 2, 5), (42, 48, 64), 0.04)
        tw = f2.measureText(label)
        p.c.drawString(label, sx - tw / 2 - 8, G - 15, f2, skia.Paint(AntiAlias=True, Color=C(HALL["sign"])))
        p.flat(oval(sx + 62, G - 26, 6, 6), HALL["hazard"])


def hall_layers():
    return [("back", 1.0, _h_back), ("deck", 1.0, _h_deck)]


# ----------------------------------------------------------------------------------------------- scenes

class Scene:
    """Layers painted once on strips tall enough for the widest zoom and wide enough for the whole pan, each with its
    own grain; slid by the pan times its depth."""

    def __init__(self, layers, world, page_seed=3):
        self.layers = []
        span = world - W
        for name, d, fn in layers:
            strip = int(WB + math.ceil(span * d)) + 4
            p = FlatPage(strip, HB, seed=page_seed)
            p._sc, p.strip = 1.0, strip
            p.c.clear(skia.ColorTRANSPARENT)
            p.begin_grain()
            p.c.save()
            p.c.translate(-X0, -Y0)
            fn(p)
            p.c.restore()
            p.end_grain()
            self.layers.append((name, d, p.surface.makeImageSnapshot()))

    def draw(self, P, sh, only=None):
        pg = P.pg
        x0, x1, y0, y1 = P.visible()
        for name, d, img in self.layers:
            if only is not None and name not in only:
                continue
            a = max(0.0, x0 - X0 + sh * d)
            b = min(float(img.width()), x1 - X0 + sh * d)
            if b <= a:
                continue
            src = skia.Rect(a, 0, b, img.height())
            dst = skia.Rect(a + X0 - sh * d, Y0, b + X0 - sh * d, Y0 + img.height())
            pg.c.drawImageRect(img, src, dst, skia.SamplingOptions(skia.FilterMode.kLinear), None,
                               skia.Canvas.kFast_SrcRectConstraint)


class World:
    """Both places, painted once (frames render in parallel workers: each builds its own)."""

    def __init__(self):
        self.village = Scene(village_layers(), VILLAGE_W)
        self.hall = Scene(hall_layers(), HALL_W)


# ----------------------------------------------------------------------------------------------- live props

def door_opening(pg, sh, u):
    """The hall door's opening: the night outside (stars, the ground), seen as the roll-up door goes up (u 0..1)."""
    d0, d1 = DOOR[0] - sh, DOOR[1] - sh
    pg.flat(skia.Path().addRect(skia.Rect(d0, G - 520, d1, G)), HALL["night"])
    for q in range(7):
        pg.flat(oval(d0 + 40 + q * 58, G - 470 + 37 * ((q * 7) % 5), 2.6, 2.6), "#f4ecd2", 0.8)
    pg.flat(skia.Path().addRect(skia.Rect(d0, G - 34, d1, G)), (52, 66, 54))


def door_panel(pg, sh, u):
    """The roll-up door itself (in front of whoever stands in the doorway): u 0 shut .. 1 up."""
    d0, d1 = DOOR[0] - sh, DOOR[1] - sh
    bot = G - 514 * u
    if bot > G - 512:
        pg.shape(skia.Path().addRect(skia.Rect(d0, G - 520, d1, bot)), HALL["door"], 0.05)
        for y in np.arange(G - 490, bot - 10, 34):
            pg.flat(skia.Path().addRect(skia.Rect(d0 + 6, y, d1 - 6, y + 3)), tone(HALL["door"], -0.08))
        pg.flat(skia.Path().addRect(skia.Rect(d0, bot - 14, d1, bot)), HALL["hazard"])
