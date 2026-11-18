"""Forest Keepers episode 14, Sprout's Christmas Tree, in the flat picture-book look: the world (docs/engines/
forest_keepers_christmas.md, "Flat-look storyboard"). A snowy walk to the right: the little fir growing on the path, the
Keepers' treehouse with its workbench (ornaments, decorating, Christmas Eve), a pine with cones under it, and a sunny
clearing further on (its forever home). Static layers are painted once (flat.Valley); the sky and the light are live
and follow the day the plan sets (LIGHT): day -> dusk -> night (Christmas Eve) -> morning -> evening.

World x is the ground layer's own px (the Keepers' path).
"""
import math

import numpy as np
import skia

from .flat import PAL, bush, hill_band, pine, treehouse
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
G = H * 0.93                        # the Keepers' path (their feet)
BACK = G - 40.0                     # the ground just behind the path
FIR0 = 2300.0                       # the little fir, growing right on the path
SPOT = 3300.0                       # where the pot waits by the two lanterns (its Christmas place)
LAMP_DX = (-200.0, 200.0)           # the two lanterns either side of it, on tall posts: their boxes stand clear above
LAMP_Y = BACK - 290.0               # every short Keeper's head (FK0017 r2: at +-150 / 150 high they sat on Sprout's and
                                    # Digs' heads like chimneys)
BENCH = 4580.0                      # the workbench (its middle), the treehouse right behind it
TREEHOUSE = 4580.0
CONE_PINE = 5390.0                  # a big pine right behind Digs' place at the bench, cones under it
CLEARING = 6700.0                   # the sunny clearing: its forever home
WORLD = 8200.0

SNOW, SNOW_SH, SNOW_BLUE = (238, 240, 236), (205, 214, 220), (214, 224, 234)
TRODDEN = (222, 214, 200)
TRUNK = (128, 96, 72)
WOOD, WOOD2 = (195, 148, 102), (176, 126, 86)
LAMP = (246, 212, 138)

# the light through the episode: [(t, preset)], set by the plan (default: all day)
LIGHT = [(0.0, "day")]
PRESETS = {      # sky top, mid, low; light multiplier, offset; sun (alpha, x, y as fractions of the frame)
    "day": ("#b7c8d6", "#e3e5e0", "#f2e4d4", (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), (0.85, 0.74, 0.2)),
    "dusk": ("#7c84a8", "#d5a6a6", "#efb08c", (0.95, 0.88, 0.9), (0.03, 0.0, 0.03), (0.9, 0.82, 0.52)),
    "night": ("#252f58", "#323d6c", "#495282", (0.76, 0.79, 0.93), (0.0, 0.01, 0.05), (0.0, 0.82, 0.7)),
    "morning": ("#a8c3dd", "#f3e2cb", "#fbd5ad", (1.03, 1.0, 0.95), (0.02, 0.01, 0.0), (0.95, 0.2, 0.36)),
    "evening": ("#5d6896", "#b98fa2", "#e4a487", (0.86, 0.82, 0.9), (0.02, 0.0, 0.05), (0.6, 0.8, 0.58)),
}


def _ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def light_at(t):
    """(preset a, preset b, u): the light at time t, between two keys (they ease into each other)."""
    keys = LIGHT
    if t <= keys[0][0] or len(keys) == 1:
        return keys[0][1], keys[0][1], 0.0
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return a, b, _ss((t - t0) / max(t1 - t0, 1e-6))
    return keys[-1][1], keys[-1][1], 0.0


def night(t):
    a, b, u = light_at(t)
    return (a == "night") * (1 - u) + (b == "night") * u


def _mixv(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def sky(pg, t):
    """The winter sky for the light at t; the sun (low, soft) by day, stars and the moon at night."""
    a, b, u = light_at(t)
    A, B = PRESETS[a], PRESETS[b]
    top, mid, low = (mix(A[i], B[i], u) for i in range(3))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.64)], [C(top), C(mid), C(low)], [0, 0.55, 1])
    pg.c.drawPaint(skia.Paint(Shader=sh))
    sa, sx, sy = _mixv(A[5], B[5], u)
    if sa > 0.02:
        r = 46.0
        pg.glow(W * sx, H * sy, r * 7, "#ffe2a8", 0.5 * sa)
        pg.flat(oval(W * sx, H * sy, r, r), "#fff2d2", sa)
    n = night(t)
    if n > 0.01:
        rs = np.random.default_rng(31)
        for _ in range(130):
            x, y = rs.uniform(0, W), rs.uniform(0, H * 0.5)
            pg.flat(oval(x, y, rs.uniform(1.0, 2.2), rs.uniform(1.0, 2.2)), "#fff6dc",
                    n * rs.uniform(0.35, 0.9) * (0.8 + 0.2 * math.sin(t * rs.uniform(0.5, 1.5) + x)))
        pg.flat(oval(W * 0.18, H * 0.13, 30, 30), "#f6efd8", n * 0.95)                # the moon
        pg.flat(oval(W * 0.18 + 11, H * 0.13 - 7, 26, 26), mix("#2c3560", top, 0.5), n * 0.95)
    pg.grain_opaque()


def light_mul(t):
    a, b, u = light_at(t)
    A, B = PRESETS[a], PRESETS[b]
    return np.array(_mixv(A[3], B[3], u), np.float32), np.array(_mixv(A[4], B[4], u), np.float32)


def apply_light(pg, t):
    """Tint what is on the page now by the light at t (lights drawn after it stay lit)."""
    mul, add = light_mul(t)
    if np.allclose(mul, 1.0) and not add.any():
        return
    import cv2
    img = pg.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    M = np.array([[mul[0], 0, 0, add[0] * 255], [0, mul[1], 0, add[1] * 255], [0, 0, mul[2], add[2] * 255]],
                 np.float32)
    img[..., :3] = cv2.transform(np.ascontiguousarray(img[..., :3]), M)
    pg.c.save()                                    # in screen space: a close shot's zoom must not apply twice
    pg.c.resetMatrix()
    pg.c.drawImage(skia.Image.fromarray(np.ascontiguousarray(img), colorType=skia.ColorType.kRGBA_8888_ColorType),
                   0, 0)
    pg.c.restore()


# ----------------------------------------------------------------------------------------------- layers (static)

def snowy_pine(p, x, y, h, col=None):
    """A pine with snow lying on its three tiers."""
    col = col or PAL["pine"]
    pine(p, x, y, h, col)
    w = h * 0.26
    for yy, ww in ((0.62, 0.42), (0.34, 0.72), (0.86, 0.22)):
        cy = y - h * yy
        p.flat(smooth([(x - w * ww, cy + h * 0.02), (x - w * ww * 0.4, cy - h * 0.05), (x, cy - h * 0.035),
                       (x + w * ww * 0.5, cy - h * 0.06), (x + w * ww, cy + h * 0.02), (x, cy + h * 0.03)]), SNOW, 0.95)
    p.flat(smooth([(x, y - h), (x + w * 0.2, y - h * 0.86), (x, y - h * 0.88), (x - w * 0.2, y - h * 0.86)]), SNOW)


def bare_tree(p, x, y, h, rs):
    """A leafless tree in winter, snow along the tops of its limbs."""
    p.shape(tube([(x, y), (x + rs.uniform(-8, 8), y - h * 0.6), (x + rs.uniform(-14, 14), y - h)], h * 0.035,
                 h * 0.012), TRUNK, 0.1, (-0.5, 0.0))
    for k in range(5):
        u = 0.4 + 0.12 * k
        sx = 1 if k % 2 else -1
        x0, y0 = x, y - h * u
        x1, y1 = x0 + sx * h * rs.uniform(0.14, 0.24), y0 - h * rs.uniform(0.12, 0.2)
        p.shape(tube([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 4), (x1, y1)], h * 0.014, h * 0.005), TRUNK, 0.0)
        p.stroke(skia.Path().moveTo(x0 + sx * 6, y0 - 4).quadTo((x0 + x1) / 2, (y0 + y1) / 2 - 2, x1, y1 - 3),
                 SNOW, 3.0)


def _hills(p, y, amp, seed, col, step=520.0, light_=0.04, dark=0.06):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H, col, light_, dark)


def _far(p):
    _hills(p, H * 0.55, H * 0.09, 11, (184, 196, 206), 640.0)


def _far2(p):
    _hills(p, H * 0.6, H * 0.05, 12, (200, 210, 216), 560.0)


def _far_trees(p):
    rs = np.random.default_rng(13)
    x = 20.0
    while x < p.strip:
        snowy_pine(p, x, H * 0.63, H * rs.uniform(0.06, 0.085), tone(PAL["pine"], 0.25))
        x += rs.uniform(70, 140)


def _mid(p):
    _hills(p, H * 0.67, H * 0.04, 14, (214, 222, 226), 480.0)
    rs = np.random.default_rng(15)
    x = 60.0
    while x < p.strip:
        if rs.random() < 0.6:
            snowy_pine(p, x, H * 0.675, H * rs.uniform(0.13, 0.2), tone(PAL["pine"], 0.1))
        else:
            bare_tree(p, x, H * 0.675, H * rs.uniform(0.16, 0.24), rs)
        x += rs.uniform(130, 260)


def _field(p):
    _hills(p, H * 0.72, H * 0.03, 16, (226, 231, 232), 600.0)
    rs = np.random.default_rng(17)
    x = 200.0
    while x < p.strip:
        if abs(x - CLEARING) > 700:
            bush(p, x, H * rs.uniform(0.7, 0.72), H * rs.uniform(0.03, 0.045), tone(PAL["olive"], -0.05))
            p.flat(oval(x, H * 0.7 - H * 0.03, H * 0.045, H * 0.012), SNOW, 0.9)
        x += rs.uniform(500, 1100)


def _ground(p):
    """The snowy meadow and the trodden path, the treehouse and its workbench, the cone pine, the clearing."""
    hill_band(p, [(x, H * 0.75 + 6 * math.sin(x / 700.0)) for x in np.arange(-100.0, p.strip + 400, 400.0)], H,
              SNOW, 0.02, 0.05)
    top = [(x, G - 26 + 4 * math.sin(x / 900.0)) for x in np.arange(-100.0, p.strip + 300, 300.0)]
    bot = [(x, G + 44 + 5 * math.sin(x / 1100.0 + 1)) for x in np.arange(p.strip + 300, -400.0, -300.0)]
    p.flat(smooth(top + bot), TRODDEN, 0.85)                                    # the path, trodden down
    p.flat(oval(CLEARING, BACK - 30, 620, 90), (246, 244, 234), 0.7, blur=40)  # the clearing: open, untrodden snow
    treehouse(p, TREEHOUSE, BACK + 8, 760)
    _snow_on_treehouse(p, TREEHOUSE, BACK + 8, 760)
    snowy_pine(p, CONE_PINE, BACK + 8, 520)
    for dx in (-150, 210):                                                     # the clearing's edge trees
        snowy_pine(p, CLEARING + dx * 3.6, BACK + 6, 440)
    rs = np.random.default_rng(19)
    for _ in range(int(p.strip / 55)):                                         # soft lumps in the snow, off the path
        x = rs.uniform(0, p.strip)
        y = G + rs.uniform(56, 120) if rs.random() < 0.5 else BACK - rs.uniform(0, 100)
        if abs(x - TREEHOUSE) < 260 and y < G:
            continue
        r = rs.uniform(10, 26)
        p.flat(oval(x, y, r * 1.8, r * 0.5), SNOW_SH, 0.5)
        p.flat(oval(x - r * 0.3, y - r * 0.15, r * 1.5, r * 0.4), SNOW, 0.9)
    for _ in range(int(p.strip / 160)):                                        # a few dry stems poking through
        x = rs.uniform(0, p.strip)
        y = BACK - rs.uniform(0, 80)
        if abs(x - TREEHOUSE) < 260 or abs(x - FIR0) < 120 or abs(x - CLEARING) < 300:
            continue
        for d in (-6, 0, 6):
            p.stroke(skia.Path().moveTo(x + d, y).quadTo(x + d * 2, y - 24, x + d * 3, y - 40), (150, 132, 96), 2.5)


def _snow_on_treehouse(p, x, y, h):
    """Snow lying on the treehouse crown, its roof and the porch rail."""
    s = h
    for dx, dy, r in ((-0.3, -0.7, 0.2), (0.3, -0.72, 0.21), (-0.1, -0.86, 0.22), (0.15, -0.88, 0.2),
                      (-0.42, -0.56, 0.13), (0.44, -0.58, 0.14)):
        cx, cy, rr = x + dx * s, y + dy * s - r * s * 0.6, r * s
        p.flat(smooth([(cx - rr * 0.8, cy + rr * 0.25), (cx - rr * 0.4, cy - rr * 0.18), (cx, cy - rr * 0.3),
                       (cx + rr * 0.45, cy - rr * 0.16), (cx + rr * 0.8, cy + rr * 0.25), (cx, cy + rr * 0.12)]),
               SNOW, 0.95)


def layers(world_w=WORLD):
    return [("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees), ("mid", 0.35, _mid),
            ("field", 0.55, _field), ("ground", 1.0, _ground)]


# ----------------------------------------------------------------------------------------------- live props

def workbench(pg, x, sh):
    """The Keepers' workbench (live: drawn behind the Keepers, in front of the treehouse)."""
    y = BACK + 10
    x0, x1 = x - 230 - sh, x + 230 - sh
    for lx in (x0 + 30, x1 - 30):
        pg.shape(rrect(lx - 11, y - 150, lx + 11, y, 4), tone(TRUNK, 0.05), 0.0)
    pg.shape(rrect(x0, y - 172, x1, y - 148, 6), WOOD2, 0.12)
    pg.flat(rrect(x0 + 4, y - 178, x1 - 4, y - 168, 4), SNOW, 0.9)            # a little snow on its back edge


def lantern(pg, x, y, lit, post=150.0, flicker=0.0, glow_only=False):
    """A little lantern on a wooden post; lit 0..1 (its flame). glow_only: just its light (drawn again over the dusk
    tint; the post itself stays behind whoever walks in front of it - FK0017 advisor r1)."""
    if glow_only:
        if lit > 0.01:
            f = 1.0 + 0.06 * flicker
            pg.glow(x, y - 18, 80 * f, "#f6d48a", 0.55 * lit)
            pg.flat(oval(x, y - 16, 4.5 * f, 8 * f), "#fff3cf", lit)
        return
    pg.shape(rrect(x - 5, y, x + 5, y + post, 3), tone(TRUNK, 0.05), 0.0)
    pg.shape(rrect(x - 15, y - 36, x + 15, y, 6), (92, 74, 62), 0.0)
    pg.flat(rrect(x - 11, y - 32, x + 11, y - 4, 4), mix((58, 58, 70), LAMP, lit))
    if lit > 0.01:
        f = 1.0 + 0.06 * flicker
        pg.glow(x, y - 18, 80 * f, "#f6d48a", 0.55 * lit)
        pg.flat(oval(x, y - 16, 4.5 * f, 8 * f), "#fff3cf", lit)
    pg.shape(smooth([(x - 20, y - 36), (x, y - 50), (x + 20, y - 36)]), (92, 74, 62), 0.0)


def clay_pot(pg, x, y, h, rim=None):
    """The clay pot (x, y = the middle of its foot; h its height)."""
    w = h * 0.62
    pg.shape(smooth([(x - w * 0.62, y - h * 0.92), (x + w * 0.62, y - h * 0.92), (x + w * 0.48, y), (x - w * 0.48, y)]),
             (192, 122, 82), 0.12)
    pg.shape(rrect(x - w * 0.7, y - h, x + w * 0.7, y - h * 0.82, 6), (204, 136, 94), 0.0)
