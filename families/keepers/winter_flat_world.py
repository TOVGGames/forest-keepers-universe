"""Forest Keepers episode 13, Getting Ready for Winter, in the flat picture-book look: the world (docs/engines/
forest_keepers_winter_ready.md, "Remake"). One long walk to the right through the valley at sunset, into dusk and
night. Everything here is static and painted once per layer (flat.Valley); the sky and the light are live:

    layers(world_w) -> [(name, depth, fn)] for flat.Valley     every layer runs the whole walk (+ the frame)
    sky(pg, t)                                                 sunset -> dusk -> night, the sun setting behind the far
                                                               hills at one size on screen (FK0012 audit 10), stars
    light(t) -> skia.Paint | None                              the colour of the light over the rest (dusk, night)

World x is the ground layer's own px (the Keepers' path); the animals' places sit just behind the path.
"""
import math

import numpy as np
import skia

from .flat import (PAL, bush, cloud, hill_band, leaf, lolly_tree, pine, poplar, tuft)
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
G = H * 0.93                        # the Keepers' path (their feet)
BACK = G - 44.0                     # the animals' ground, just behind the path
# places (world x): staging in docs/engines/forest_keepers_winter_ready.md (remake)
OAK, STUMP, PILE, BURROW1 = 2420.0, 2650.0, 2760.0, 2890.0   # a young oak (its low twig holds the acorns),
TWIG_Y = BACK - 112.0                                         # the old stump, the pile, the chipmunk's burrow
ACORNS = [(2482.0, TWIG_Y + 20.0), (2514.0, TWIG_Y + 22.0), (2546.0, TWIG_Y + 19.0)]   # hanging under the twig
WILLOW = 3300.0                     # the willow on the pond's near (left) bank; the beaver's lodge across the pond
POND = (3600.0, 4860.0)
LODGE = 4380.0
WATER = BACK - 6.0                  # the pond's surface line
DOOR3, GRASS = 5350.0, 5790.0       # the groundhog's door, the dry grass (two bunches, Digs fetches them)
DEN = 7050.0                        # the bear's den: the entrance on the left face of a rocky bank
FEEDER = 9700.0
WORLD = 12300.0
# the light through the episode (s): sunset at the start, dusk from the bear, night from the chickadee
DUSK, NIGHT = (205.0, 255.0), (255.0, 290.0)

SOIL, SOIL_DARK = (141, 106, 75), (78, 58, 44)
ROCK, ROCK2 = (150, 142, 138), (128, 120, 118)
WATER_C, WATER_D = (110, 142, 160), (90, 120, 140)
LODGE_C = (122, 92, 66)
WILLOW_C, WILLOW_L = (156, 168, 84), (186, 190, 104)
TRUNK = (128, 96, 72)


def _ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def night(t):
    return _ss((t - NIGHT[0]) / (NIGHT[1] - NIGHT[0]))


def dusk(t):
    return _ss((t - DUSK[0]) / (DUSK[1] - DUSK[0]))


# ----------------------------------------------------------------------------------------------- the sky (live)

def sky(pg, t):
    """Sunset (warm, the low sun) -> dusk (violet) -> night (deep blue, stars). The sun keeps one size on screen and
    sinks behind the far hills (they are painted after it)."""
    c = pg.c
    d, n = dusk(t), night(t)
    top = mix(mix("#a9b8cf", "#6c6f9c", d), "#2a3462", n)
    mid = mix(mix("#f0cdb2", "#c99aa8", d), "#3b4676", n)
    low = mix(mix("#f6b98c", "#e39a86", d), "#56598a", n)
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.62)], [C(top), C(mid), C(low)], [0, 0.55, 1])
    c.drawPaint(skia.Paint(Shader=sh))
    sx, r = W * 0.78, 50.0                                     # the sun, low in the west of the frame, sinking
    sy = H * (0.4 + 0.22 * _ss(t / 230.0))
    if sy < H * 0.66:
        pg.glow(sx, sy, r * 7, mix("#ffcf8a", "#f59a74", d), 0.6 * (1 - n))
        pg.flat(oval(sx, sy, r * 1.12, r * 1.12), mix("#ffd9a0", "#ffb488", d), 0.7 * (1 - n))
        pg.flat(oval(sx, sy, r, r), mix("#fff4d6", "#ffdcb0", d), 1 - 0.8 * n)
    if n > 0.01:                                               # stars (fixed on screen: they are very far away)
        rs = np.random.default_rng(31)
        for _ in range(120):
            x, y = rs.uniform(0, W), rs.uniform(0, H * 0.5)
            a = n * rs.uniform(0.35, 0.9) * (0.8 + 0.2 * math.sin(t * rs.uniform(0.5, 1.5) + x))
            pg.flat(oval(x, y, rs.uniform(1.0, 2.2), rs.uniform(1.0, 2.2)), "#fff6dc", a)
        pg.flat(oval(W * 0.2, H * 0.14, 30, 30), "#f6efd8", n * 0.95)          # the moon
        pg.flat(oval(W * 0.2 + 11, H * 0.14 - 7, 26, 26), mix("#2c3560", top, 0.5), n * 0.95)
    pg.grain_opaque()


def light_mul(t):
    """The light on everything else (multiplier, offset 0..1 per channel): a warm sunset, a violet dusk, then night,
    dark and blue."""
    d, n = dusk(t), night(t)
    mul = np.array([1.0 - 0.06 * d - 0.36 * n, 0.97 - 0.12 * d - 0.28 * n, 0.92 - 0.04 * d - 0.1 * n], np.float32)
    add = np.array([0.03 * (1 - n), 0.01 * n, 0.03 * d + 0.05 * n], np.float32)   # a soft, calm blue night
    return mul, add


def apply_light(pg, t):
    """Tint what is on the page now by the light at time t (one pass over the frame; lights are drawn after it, so
    they stay lit)."""
    mul, add = light_mul(t)
    if np.allclose(mul, 1.0) and not add.any():
        return
    import cv2
    img = pg.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    M = np.array([[mul[0], 0, 0, add[0] * 255], [0, mul[1], 0, add[1] * 255], [0, 0, mul[2], add[2] * 255]],
                 np.float32)
    img[..., :3] = cv2.transform(np.ascontiguousarray(img[..., :3]), M)
    pg.c.drawImage(skia.Image.fromarray(np.ascontiguousarray(img), colorType=skia.ColorType.kRGBA_8888_ColorType),
                   0, 0)


def cloud_alpha(t):
    """The clouds clear away as night comes ("the stars are out")."""
    return 1.0 - _ss((t - DUSK[1]) / 25.0)


# ----------------------------------------------------------------------------------------------- layers (static)

def _hills(p, y, amp, seed, col, light_=0.05, dark=0.06, step=520.0):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H, col, light_, dark)


def _clouds(p):
    rs = np.random.default_rng(3)
    x = 120.0
    while x < p.strip:
        cloud(p, x, H * rs.uniform(0.08, 0.22), W * rs.uniform(0.1, 0.16))
        x += rs.uniform(420, 760)


def _far(p):
    _hills(p, H * 0.56, H * 0.09, 11, PAL["far"], step=640.0)


def _far2(p):
    _hills(p, H * 0.61, H * 0.05, 12, PAL["far2"], step=560.0)


def _far_trees(p):
    rs = np.random.default_rng(13)
    x = 20.0
    while x < p.strip:
        i = int(x) % 3
        (pine if i else lolly_tree)(p, x, H * 0.64, H * rs.uniform(0.06, 0.08),
                                    tone(PAL["pine"] if i else PAL["olive"], 0.18))
        x += rs.uniform(90, 160)


def _mid(p):
    _hills(p, H * 0.67, H * 0.04, 14, PAL["mid"], step=480.0)
    rs = np.random.default_rng(15)
    x = 60.0
    kinds = [(poplar, PAL["ochre"]), (lolly_tree, PAL["orange"]), (pine, PAL["pine"]), (lolly_tree, PAL["pink"]),
             (poplar, PAL["olive"]), (lolly_tree, PAL["ochre"])]
    while x < p.strip:
        f, col = kinds[rs.integers(len(kinds))]
        f(p, x, H * 0.675, H * rs.uniform(0.12, 0.19), col)
        x += rs.uniform(140, 300)


def _field(p):
    _hills(p, H * 0.72, H * 0.03, 16, mix(PAL["field"], PAL["olive"], 0.45), 0.06, 0.04, step=600.0)
    rs = np.random.default_rng(17)
    x = 200.0
    while x < p.strip:
        bush(p, x, H * rs.uniform(0.7, 0.72), H * rs.uniform(0.03, 0.045), tone(PAL["olive"], rs.uniform(-0.06, 0.0)))
        x += rs.uniform(500, 1100)


def _ground(p):
    """The meadow and the path, the places behind it, grass and fallen leaves."""
    hill_band(p, [(x, H * 0.75 + 6 * math.sin(x / 700.0)) for x in np.arange(-100.0, p.strip + 400, 400.0)], H,
              PAL["ground"], 0.05, 0.08)
    top = [(x, G - 28 + 4 * math.sin(x / 900.0)) for x in np.arange(-100.0, p.strip + 300, 300.0)]
    bot = [(x, G + 46 + 5 * math.sin(x / 1100.0 + 1)) for x in np.arange(p.strip + 300, -400.0, -300.0)]
    p.flat(smooth(top + bot), PAL["path"], 0.95)                                 # the path the Keepers walk
    _oak(p, OAK)
    _stump(p, STUMP)
    _burrow(p, BURROW1, 48.0)
    _pond(p)
    _willow(p, WILLOW)
    _burrow(p, DOOR3, 70.0)                                                    # (its dry grass: live, Digs gathers it)
    _rock_bank(p, DEN)
    _feeder_post(p, FEEDER)
    rs = np.random.default_rng(19)
    bank = rock_bank_outline(DEN)                         # (owner, FK0015 5:44-5:55: the meadow's tufts and leaves
    on_bank = lambda x, y, r: any(bank.contains(x + dx, y + dy)   # went on into the bear's den)   # noqa: E731
                                  for dx, dy in ((0, 0), (-r, 0), (r, 0), (0, -2 * r), (0, r)))
    for _ in range(int(p.strip / 40)):                                          # tufts and leaves, off the path
        x = rs.uniform(0, p.strip)
        y = G + rs.uniform(56, 120) if rs.random() < 0.5 else BACK - rs.uniform(0, 110)
        size = H * rs.uniform(0.012, 0.02)
        if POND[0] - 60 < x < POND[1] + 60 and y < G:
            continue
        if on_bank(x, y, size):
            continue
        tuft(p, x, y, size, tone(PAL["ground"], -0.14))
    for i in range(int(p.strip / 30)):
        x = rs.uniform(0, p.strip)
        y = G + rs.uniform(-120, 110)
        ang = rs.uniform(0, 180)
        if POND[0] - 40 < x < POND[1] + 40 and y < G - 20:
            continue
        if on_bank(x, y, H * 0.007):
            continue
        leaf(p, x, y, H * 0.007, ang, (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])


def _stump(p, x):
    y = BACK + 8
    p.shape(smooth([(x - 70, y), (x - 60, y - 70), (x - 56, y - 92), (x + 56, y - 92), (x + 60, y - 70),
                    (x + 70, y), (x, y + 8)]), TRUNK, 0.12, (-0.4, 0.0))
    p.shape(oval(x, y - 92, 57, 15), tone(TRUNK, 0.3), 0.0)                       # the cut top, its rings
    for r in (40, 24, 10):
        p.stroke(oval(x, y - 92, r, r * 0.26), tone(TRUNK, 0.12), 2.0)


def _oak(p, x):
    """A young oak in autumn: its low twig reaches out over the path's edge, three acorns hanging under it (the scene
    draws the acorns: Sprout picks them)."""
    y = BACK + 8
    p.shape(tube([(x, y), (x - 6, y - 260), (x + 10, y - 520)], 22, 12), TRUNK, 0.12, (-0.5, 0.0))
    for dx, dy, r, col in ((-90, -560, 120, PAL["orange"]), (90, -570, 125, PAL["ochre"]), (0, -650, 130, PAL["orange"]),
                           (-30, -500, 105, tone(PAL["ochre"], -0.05)), (70, -480, 95, PAL["orange"])):
        p.shape(oval(x + dx, y + dy, r, r * 0.92), col, 0.1)
    p.shape(tube([(x, TWIG_Y - 30), (x + 70, TWIG_Y - 8), (x + 150, TWIG_Y - 4)], 7, 3.5), TRUNK, 0.0)
    for ax, ay in ACORNS:                                         # their little stalks, and a few oak leaves
        p.stroke(skia.Path().moveTo(ax, TWIG_Y - 6).lineTo(ax, ay - 8), tone(TRUNK, 0.1), 2.5)
    for lx, ly, a in ((x + 100, TWIG_Y - 20, -30), (x + 150, TWIG_Y - 14, 20), (x + 40, TWIG_Y - 32, -60)):
        leaf(p, lx, ly, 14, a, PAL["ochre"])


def _burrow(p, x, r):
    y = BACK + 2
    p.shape(oval(x, y - 4, r * 2.1, r * 0.9), SOIL, 0.1)                         # the dug earth round it
    p.flat(oval(x, y - r * 0.35, r, r * 0.72), SOIL_DARK)                        # the dark way in
    p.flat(oval(x, y - r * 0.2, r * 0.8, r * 0.45), tone(SOIL_DARK, -0.25), blur=r * 0.15)


def _pond(p):
    x0, x1 = POND
    path = smooth([(x0, WATER + 6), (x0 + 120, WATER - 26), ((x0 + x1) / 2, WATER - 34), (x1 - 120, WATER - 26),
                   (x1, WATER + 6), ((x0 + x1) / 2, WATER + 26)])
    p.shape(path, WATER_C, 0.0)
    p.flat(smooth([(x0 + 60, WATER - 4), ((x0 + x1) / 2, WATER - 18), (x1 - 60, WATER - 4),
                   ((x0 + x1) / 2, WATER + 14)]), WATER_D, 0.5)
    for j in range(9):                                                           # a few soft ripples of light
        xx = x0 + 120 + j * (x1 - x0 - 240) / 8
        p.flat(rrect(xx - 26, WATER - 12 + (j % 3) * 8, xx + 26, WATER - 10 + (j % 3) * 8, 2), "#d4e0e4", 0.5)
    for xx in (x0 + 30, x0 + 70, x1 - 60):                                       # reeds at the edges
        for d in (-8, 0, 8):
            p.stroke(skia.Path().moveTo(xx + d, WATER + 8).quadTo(xx + d * 2, WATER - 40, xx + d * 3, WATER - 70),
                     PAL["olive"], 4.0)
    lx = LODGE                                                                   # the beaver's lodge: a big mound of
    p.shape(smooth([(lx - 330, WATER + 4), (lx - 250, WATER - 150), (lx - 80, WATER - 250), (lx + 90, WATER - 240),
                    (lx + 250, WATER - 140), (lx + 340, WATER + 4)]), LODGE_C, 0.14)   # sticks and mud, several
    rs = np.random.default_rng(23)                                                     # times a beaver's size
    for _ in range(70):
        a, r = rs.uniform(math.pi * 1.05, math.pi * 1.95), rs.uniform(0.3, 0.95)
        cx, cy = lx + math.cos(a) * 310 * r, WATER - 8 + math.sin(a) * 230 * r
        ang = rs.uniform(-0.5, 0.5)
        p.stroke(skia.Path().moveTo(cx - 40 * math.cos(ang), cy - 40 * math.sin(ang))
                 .lineTo(cx + 40 * math.cos(ang), cy + 40 * math.sin(ang)), tone(LODGE_C, rs.uniform(-0.2, 0.15)), 7.0)


def _willow(p, x):
    """A willow at the pond's edge: a leaning trunk and long hanging green strands (beavers' favourite)."""
    y = BACK + 6
    p.shape(tube([(x, y), (x + 20, y - 150), (x + 50, y - 290)], 26, 16), TRUNK, 0.12, (-0.5, 0.0))
    for ax, ay, L in ((x + 50, y - 290, 220), (x - 30, y - 250, 200), (x + 120, y - 260, 210), (x - 90, y - 210, 180),
                      (x + 170, y - 220, 190), (x + 10, y - 320, 240)):
        p.shape(smooth([(ax - 24, ay), (ax + 24, ay), (ax + 34, ay + L * 0.6), (ax + 8, ay + L),
                        (ax - 14, ay + L * 0.6)]), WILLOW_C if ax % 2 else WILLOW_L, 0.1)


def _grass_patch(p, x):
    """Dry grass, tall and pale, where Digs gathers the groundhog's bedding."""
    rs = np.random.default_rng(29)
    for _ in range(26):
        xx = x + rs.uniform(-110, 110)
        tuft(p, xx, BACK + rs.uniform(-6, 14), H * rs.uniform(0.03, 0.05), mix(PAL["ochre"], "#e6d39a", rs.uniform(0.3, 0.7)))


DEN_IN = 240.0                      # the den: its entrance on the bank's left face (x DEN), its far wall DEN + DEN_IN


def rock_bank_outline(x):
    y = BACK + 10
    return smooth([(x - 70, y), (x - 40, y - 230), (x + 60, y - 420), (x + 260, y - 500), (x + 480, y - 470),
                   (x + 650, y - 330), (x + 760, y - 150), (x + 820, y)])


def _rock_bank(p, x):
    """A big rocky bank; the bear's den is a dark hollow under it, open on its left face (the bear walks in from the
    left: in side view it can only walk *into* an opening it faces), and a tree stands at its foot just past the
    entrance (its low limb, live, hangs across the way in)."""
    y = BACK + 10
    p.shape(rock_bank_outline(x), ROCK, 0.14)
    for dx, dy, r in ((380, -380, 90), (560, -260, 110), (200, -440, 70), (700, -110, 80), (450, -150, 70)):
        p.shape(oval(x + dx, y + dy, r, r * 0.72), ROCK2, 0.1)
    p.flat(den_mouth(x), (44, 36, 40))                                            # the dark hollow
    p.flat(oval(x + DEN_IN * 0.6, y - 120, DEN_IN * 0.5, 120), (28, 22, 26), blur=30)
    tx = x + DEN_TREE_DX                                                          # the tree at its foot
    p.shape(tube([(tx, y), (tx + 6, y - 300), (tx - 10, y - 560)], 30, 16), TRUNK, 0.12, (-0.5, 0.0))
    for dx, dy, r, col in ((-60, -600, 120, PAL["ochre"]), (70, -620, 120, PAL["orange"]), (0, -700, 125, PAL["ochre"])):
        p.shape(oval(tx + dx, y + dy, r, r * 0.9), col, 0.1)


DEN_TREE_DX = 280.0
LIMB_PIVOT = (DEN_TREE_DX - 12.0, -310.0)     # where its low limb leaves the trunk (from (DEN, BACK + 10))
LIMB_TIP = (-120.0, -205.0)                   #   and hangs left across the den's entrance, at a bear's head height


def den_mouth(x=None):
    x = DEN if x is None else x
    y = BACK + 10
    return smooth([(x - 20, y), (x - 30, y - 220), (x + 60, y - 380), (x + DEN_IN * 0.7, y - 400),
                   (x + DEN_IN, y - 300), (x + DEN_IN + 20, y), (x + 100, y + 6)])


def _feeder_post(p, x):
    y = BACK + 6
    p.shape(rrect(x - 9, y - 300, x + 9, y, 4), TRUNK, 0.1, (-0.5, 0.0))
    p.shape(rrect(x - 90, y - 318, x + 90, y - 296, 6), tone(TRUNK, 0.15), 0.12)   # the tray
    p.shape(smooth([(x - 104, y - 372), (x, y - 420), (x + 104, y - 372), (x + 96, y - 364), (x - 96, y - 364)]),
            PAL["pink"], 0.12)                                                     # its little roof
    for dx in (-80, 80):
        p.flat(rrect(x + dx - 4, y - 368, x + dx + 4, y - 316, 2), tone(TRUNK, 0.05))


def layers(world_w=WORLD):
    """[(name, depth, fn)] for flat.Valley(W, H, pan=world_w, layers=...)."""
    return [("clouds", 0.03, _clouds), ("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees),
            ("mid", 0.35, _mid), ("field", 0.55, _field), ("ground", 1.0, _ground)]
