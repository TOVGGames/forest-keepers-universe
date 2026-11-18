"""Forest Keepers, The Treetop Marble Run, in the flat picture-book look: the world (docs/engines/
forest_keepers_marble_run_flat.md). A late-autumn walk to the right: the treehouse, the workshop under its awning, and
two big old trees with the marble run hung between them, the finish at the foot of the right one.

The camera can pull back (zoom < 1) for the wide shots of the run and the race. Everything is drawn in "working"
coordinates (world x minus the pan, world y), which are the frame at zoom 1; for a wide shot the frame is painted at
that same scale onto a bigger page (Page) and scaled down as a whole, so the paper grain, the Keepers and the scenery
all shrink together, the way a real camera pulling back would see them (grain stays fixed to what it is printed on).

    Cam(keys)                       pan x(t) and zoom z(t)
    Page(t, cam) ... .final()       the page for frame t (big when zoomed out) and the finished 1920x1080 frame
    Valley()                        the static layers, painted once, slid by the pan times their depth
"""
import math

import numpy as np
import skia

from .flat import PAL, FlatPage, bush, hill_band, leaf, lolly_tree, pine, poplar, treehouse, tuft
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
G = H * 0.93                        # the Keepers' path (their feet)
BACK = G - 40.0                     # the ground just behind the path: the trees' and the run's feet
TREEHOUSE = 1900.0
BENCH = 4100.0                      # the workbench (its middle), under the workshop awning
TREE_A, TREE_B = 5600.0, 7200.0     # the two big old trees the run hangs between (trunk middles)
RUN = (TREE_A + TREE_B) / 2
WORLD = 9200.0
ZMIN = 0.6                          # the widest the camera pulls back

TRUNK = (138, 100, 76)
TRUNK_D = (118, 84, 64)
WOOD, WOOD2, WOOD3 = (205, 158, 108), (186, 136, 92), (160, 116, 80)
LAMP = (246, 212, 138)

# working-coord range a page must hold at the widest zoom (pivot: the frame's middle, the path line)
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

    def shift(self, t):
        return self(t)[0] - W / 2


def to_frame(X, Y, z):
    """Working coords -> the finished frame's px at zoom z."""
    return W / 2 + (X - W / 2) * z, G + (Y - G) * z


class Page:
    """The page frame t is painted on: the normal 1920x1080 FlatPage at zoom 1, a bigger one (WB x HB, translated so
    working coords land right) when the camera is pulled back. Paint with .pg in working coords, then .final()."""

    _cache = {}

    def __init__(self, z, seed=3):
        self.z = z
        self.big = z < 0.999
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
        """(X0, X1, Y0, Y1) of working coords in the frame now."""
        z = self.z
        return W / 2 - W / (2 * z), W / 2 + W / (2 * z), G - G / z, G + (H - G) / z

    def final(self):
        """-> a FlatPage-sized (W x H) skia surface's canvas holder with the frame scaled down (or the page itself)."""
        pg = self.pg
        if not self.big:
            return pg
        z = self.z
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
    """Context: draw in the page's own px (no working-coords translation), e.g. a ready-made layer image."""
    class _R:
        def __enter__(self):
            pg.c.save()
            pg.c.resetMatrix()
            return pg

        def __exit__(self, *a):
            pg.c.restore()
    return _R()


# ----------------------------------------------------------------------------------------------- the light

# the light through the episode: [(t, preset)], set by the plan
LIGHT = [(0.0, "day")]
PRESETS = {      # sky top, mid, low; light multiplier, offset; sun (alpha, x, y as fractions of the frame)
    "day": ("#b9cbd2", "#efe6d6", "#f2d8c4", (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), (0.8, 0.76, 0.22)),
    "golden": ("#aebfd0", "#f2dcc0", "#f5c59a", (1.02, 0.98, 0.92), (0.025, 0.012, 0.0), (0.9, 0.8, 0.36)),
    "dusk": ("#7d84aa", "#d6a6a2", "#efae86", (0.93, 0.86, 0.88), (0.03, 0.0, 0.03), (0.75, 0.84, 0.55)),
}


def light_at(t):
    keys = LIGHT
    if t <= keys[0][0] or len(keys) == 1:
        return keys[0][1], keys[0][1], 0.0
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return a, b, _ss((t - t0) / max(t1 - t0, 1e-6))
    return keys[-1][1], keys[-1][1], 0.0


def _mixv(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def dusk(t):
    a, b, u = light_at(t)
    return (a == "dusk") * (1 - u) + (b == "dusk") * u


def sky(P, t):
    """The sky over the whole page (it stays put on screen: the far sky is very far away), the low autumn sun."""
    pg = P.pg
    a, b, u = light_at(t)
    A, B = PRESETS[a], PRESETS[b]
    top, mid, low = (mix(A[i], B[i], u) for i in range(3))
    x0, x1, y0, y1 = P.visible()
    with raw(pg):
        # the gradient runs over the frame as seen (so a pulled-back frame shows the same sky)
        ty0, ty1 = y0 + P.oy, y0 + P.oy + (y1 - y0) * 0.64
        sh = skia.GradientShader.MakeLinear([(0, ty0), (0, ty1)], [C(top), C(mid), C(low)], [0, 0.55, 1])
        pg.c.drawPaint(skia.Paint(Shader=sh))
        sa, sx, sy = _mixv(A[5], B[5], u)
        if sa > 0.02:
            fx = x0 + P.ox + (x1 - x0) * sx
            fy = y0 + P.oy + (y1 - y0) * sy
            r = 46.0 / P.z
            pg.glow(fx, fy, r * 7, "#ffe2a8", 0.45 * sa)
            pg.flat(oval(fx, fy, r, r), "#fff2d2", sa)
        pg.c.drawPaint(skia.Paint(Shader=pg.grain_shader(), BlendMode=skia.BlendMode.kSrcOver))


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
    with raw(pg):
        pg.c.drawImage(skia.Image.fromarray(np.ascontiguousarray(img), colorType=skia.ColorType.kRGBA_8888_ColorType),
                       0, 0)


# ----------------------------------------------------------------------------------------------- layers (static)

def _hills(p, y, amp, seed, col, step=520.0, light_=0.05, dark=0.06):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H + 400, col, light_, dark)


def _clouds(p):
    from .flat import cloud
    rs = np.random.default_rng(9)
    x = 100.0
    while x < p.strip:
        cloud(p, x, H * rs.uniform(0.06, 0.2), W * rs.uniform(0.1, 0.16))
        x += rs.uniform(500, 800)


def _far(p):
    _hills(p, H * 0.56, H * 0.09, 21, PAL["far"], 640.0)


def _far2(p):
    _hills(p, H * 0.61, H * 0.05, 22, PAL["far2"], 560.0)


def _far_trees(p):
    rs = np.random.default_rng(23)
    x = 20.0
    i = 0
    while x < p.strip:
        (pine if i % 3 else lolly_tree)(p, x, H * 0.635, H * rs.uniform(0.06, 0.08),
                                        tone(PAL["pine"] if i % 3 else PAL["olive"], 0.18))
        x += rs.uniform(70, 140)
        i += 1


def _mid(p):
    _hills(p, H * 0.67, H * 0.04, 24, PAL["mid"], 480.0)
    rs = np.random.default_rng(25)
    x = 60.0
    cols = [PAL["ochre"], PAL["orange"], PAL["pine"], PAL["pink"], PAL["olive"]]
    while x < p.strip:
        f = (poplar, lolly_tree, pine, lolly_tree, poplar)[int(rs.integers(0, 5))]
        f(p, x, H * 0.675, H * rs.uniform(0.13, 0.19), cols[int(rs.integers(0, 5))])
        x += rs.uniform(150, 280)


def _field(p):
    _hills(p, H * 0.75, H * 0.03, 26, PAL["field"], 600.0, 0.06, 0.04)
    rs = np.random.default_rng(27)
    x = 200.0
    while x < p.strip:
        bush(p, x, H * rs.uniform(0.74, 0.76), H * rs.uniform(0.03, 0.045), tone(PAL["olive"], -0.05))
        x += rs.uniform(600, 1200)


def big_tree(p, x, y, h, rs, lean=0.0):
    """One of the two big old trees the run hangs on: a broad trunk flaring into roots, a few branch stubs up its
    sides (Springs' steps), the crown high above (mostly out of the frame at zoom 1)."""
    top = y - h
    pts_l = [(x - 175, y + 4), (x - 128, y - 50), (x - 116, y - h * 0.3), (x - 106, y - h * 0.7), (x - 96, top)]
    pts_r = [(x + 96, top), (x + 106, y - h * 0.7), (x + 116, y - h * 0.3), (x + 130, y - 50), (x + 180, y + 4)]
    trunk = smooth(pts_l + pts_r)
    p.shape(trunk, TRUNK, 0.12, (-0.45, 0.0))
    for k in range(9):                                   # bark: a few soft long furrows
        bx = x + rs.uniform(-40, 40)
        by = y - rs.uniform(60, h * 0.9)
        p.flat(rrect(bx - 3, by - rs.uniform(40, 110), bx + 3, by, 3), TRUNK_D, 0.45)
    # the crown: big round autumn masses up top
    for dx, dy, r, col in ((-160, -60, 210, PAL["ochre"]), (150, -40, 200, PAL["orange"]), (0, -170, 230, PAL["orange"]),
                           (-260, 60, 150, tone(PAL["ochre"], -0.04)), (270, 80, 150, PAL["olive"]),
                           (60, 40, 190, tone(PAL["orange"], -0.05))):
        p.shape(oval(x + dx, top + dy, r, r * 0.92), col, 0.1)


def _ground(p):
    """The meadow, the path, the treehouse, the workshop's back wall and awning, the two big trees."""
    hill_band(p, [(x, H * 0.8 + 6 * math.sin(x / 700.0)) for x in np.arange(-100.0, p.strip + 400, 400.0)], H + 400,
              PAL["ground"], 0.06, 0.08)
    top = [(x, G - 26 + 4 * math.sin(x / 900.0)) for x in np.arange(-100.0, p.strip + 300, 300.0)]
    bot = [(x, G + 44 + 5 * math.sin(x / 1100.0 + 1)) for x in np.arange(p.strip + 300, -400.0, -300.0)]
    p.flat(smooth(top + bot), PAL["path"], 0.85)
    treehouse(p, TREEHOUSE, BACK + 8, 760)
    workshop_back(p, BENCH)
    rs = np.random.default_rng(31)
    for x in (TREE_A, TREE_B):
        big_tree(p, x, BACK + 6, 1500.0, rs)
    branch(p)
    rs = np.random.default_rng(33)
    for i in range(int(p.strip / 50)):                  # grass tufts and fallen leaves, off the path
        x = rs.uniform(0, p.strip)
        y = G + rs.uniform(50, 130) if rs.random() < 0.5 else BACK - rs.uniform(-4, 90)
        if abs(x - TREEHOUSE) < 300 and y < G:
            continue
        if TREE_A - 140 < x < TREE_B + 140 and y < G:  # the run's own ground stays clear (the mound, the tray)
            continue
        tuft(p, x, y, H * rs.uniform(0.014, 0.022), tone(PAL["ground"], -0.14))
        leaf(p, x + rs.uniform(-40, 40), y + rs.uniform(-6, 10), H * 0.007, rs.uniform(0, 180),
             (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])


# the pulley branch: from TREE_B up-left over the run; the pulley hangs under it at PULLEY
PULLEY = (RUN, BACK - 950.0)
PULLEY_R = 22.0


def branch(p):
    """The big branch from TREE_B over the run; the pulley hangs from it on a short strap (drawn live)."""
    x0, y0 = TREE_B - 60, BACK - 1040
    pts = [(x0, y0), (TREE_B - 450, y0 - 18), (PULLEY[0] + 60, PULLEY[1] - 62), (TREE_A + 330, BACK - 1080)]
    p.shape(tube(pts, 36, 16), TRUNK, 0.1, (0.0, -0.4))
    for dx, dy, r, col in ((-140, -70, 70, PAL["orange"]), (60, -90, 80, PAL["ochre"]), (-330, -40, 60, PAL["olive"])):
        p.shape(oval(PULLEY[0] + dx, PULLEY[1] - 60 + dy, r, r * 0.9), col, 0.1)      # a few leaves on it


def pulley(pg, sh, spin=0.0):
    """The pulley under the branch: a strap, the wheel (its spokes turn as the rope runs)."""
    x, y = PULLEY[0] - sh, PULLEY[1]
    pg.stroke(skia.Path().moveTo(x, y - 64).lineTo(x, y - 8), (150, 120, 90), 7.0)
    pg.shape(oval(x, y, PULLEY_R, PULLEY_R), (150, 140, 132), 0.12)
    pg.flat(oval(x, y, PULLEY_R - 6, PULLEY_R - 6), (120, 112, 106))
    for k in range(3):
        a = spin + k * math.pi / 3
        pg.stroke(skia.Path().moveTo(x - math.cos(a) * (PULLEY_R - 6), y - math.sin(a) * (PULLEY_R - 6))
                  .lineTo(x + math.cos(a) * (PULLEY_R - 6), y + math.sin(a) * (PULLEY_R - 6)), (96, 90, 86), 2.5)
    pg.flat(oval(x, y, 5, 5), (80, 74, 70))


def workshop_back(p, x):
    """The workshop: a plank back wall under a sloping roof on two posts (the bench and the machines stand in front)."""
    y = BACK + 6
    x0, x1 = x - 900, x + 1000
    n = 16
    p.shape(rrect(x0, y - 430, x1, y, 8), tone(WOOD2, -0.06), 0.06)
    for j in range(1, n):                               # vertical boards, every other a shade darker
        if j % 2:
            p.flat(skia.Path().addRect(skia.Rect(x0 + j * (x1 - x0) / n, y - 430, x0 + (j + 1) * (x1 - x0) / n, y)),
                   tone(WOOD2, -0.1), 0.7)
    for lx in (x0 + 10, (x0 + x1) / 2, x1 - 10):
        p.shape(rrect(lx - 14, y - 470, lx + 14, y, 5), TRUNK, 0.0)
    # a lean-to roof: a straight-edged slab sloping down toward us, its front edge in a darker band, shingle rows
    roof = skia.Path()
    roof.moveTo(x0 - 70, y - 452)
    roof.lineTo(x1 + 70, y - 452)
    roof.lineTo(x1 + 40, y - 520)
    roof.lineTo(x0 - 40, y - 520)
    roof.close()
    p.shape(roof, PAL["pink"], 0.1)
    for j in range(1, 3):
        yy = y - 520 + 68 * j / 3
        p.flat(skia.Path().addRect(skia.Rect(x0 - 60, yy - 3, x1 + 60, yy)), tone(PAL["pink"], -0.14), 0.6)
    p.flat(rrect(x0 - 74, y - 456, x1 + 74, y - 440, 5), tone(PAL["pink"], -0.18))
    # a pegboard of tools on the wall: a mallet, a saw, a coil of rope (decoration)
    p.shape(rrect(x - 380, y - 360, x - 200, y - 240, 6), tone(WOOD, -0.04), 0.0)
    p.stroke(skia.Path().moveTo(x - 340, y - 340).lineTo(x - 340, y - 270), (120, 90, 66), 6)
    p.shape(rrect(x - 362, y - 356, x - 318, y - 330, 4), (150, 110, 80), 0.0)
    p.flat(oval(x - 250, y - 300, 30, 30), PAL["rope"])
    p.flat(oval(x - 250, y - 300, 16, 16), tone(WOOD, -0.04))
    p.flat(oval(x + 300, y - 330, 40, 40), tone(WOOD2, -0.2))        # a round window
    p.flat(oval(x + 300, y - 330, 32, 32), "#f1d9a0")


def layers():
    return [("clouds", 0.03, _clouds), ("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees),
            ("mid", 0.35, _mid), ("field", 0.55, _field), ("ground", 1.0, _ground)]


class Valley:
    """Each layer painted once on a strip tall enough for the widest zoom (world y Y0 .. Y0 + HB) and wide enough for
    the whole pan, with its own grain; slid across by the pan times its depth."""

    def __init__(self, page_seed=3):
        self.layers = []
        span = WORLD - W                                # the pan's range (frame middle from W/2 to WORLD - W/2)
        for name, d, fn in layers():
            strip = int(WB + math.ceil(span * d)) + 4
            p = FlatPage(strip, HB, seed=page_seed)
            p._sc, p.strip = 1.0, strip
            p.c.clear(skia.ColorTRANSPARENT)
            p.begin_grain()
            p.c.save()
            p.c.translate(-X0, -Y0)                     # strip px = working coords at pan 0 + (-X0, -Y0)
            fn(p)
            p.c.restore()
            p.end_grain()
            self.layers.append((name, d, p.surface.makeImageSnapshot()))

    def draw(self, P, sh):
        """sh = world x at the working coords' 0 (cam x - W/2)."""
        pg = P.pg
        x0, x1, y0, y1 = P.visible()
        for name, d, img in self.layers:
            # strip px sx shows working X = sx + X0 - sh * d
            a = max(0.0, x0 - X0 + sh * d)
            b = min(float(img.width()), x1 - X0 + sh * d)
            if b <= a:
                continue
            src = skia.Rect(a, 0, b, img.height())
            dst = skia.Rect(a + X0 - sh * d, Y0, b + X0 - sh * d, Y0 + img.height())
            pg.c.drawImageRect(img, src, dst, skia.SamplingOptions(skia.FilterMode.kLinear), None,
                               skia.Canvas.kFast_SrcRectConstraint)


# ----------------------------------------------------------------------------------------------- live props

def lantern(pg, x, y, lit, post=150.0, flicker=0.0):
    """A little lantern on a wooden post; lit 0..1 (its flame)."""
    pg.shape(rrect(x - 5, y, x + 5, y + post, 3), tone(TRUNK, 0.05), 0.0)
    pg.shape(rrect(x - 15, y - 36, x + 15, y, 6), (92, 74, 62), 0.0)
    pg.flat(rrect(x - 11, y - 32, x + 11, y - 4, 4), mix((58, 58, 70), LAMP, lit))
    if lit > 0.01:
        f = 1.0 + 0.06 * flicker
        pg.glow(x, y - 18, 80 * f, "#f6d48a", 0.55 * lit)
        pg.flat(oval(x, y - 16, 4.5 * f, 8 * f), "#fff3cf", lit)
    pg.shape(smooth([(x - 20, y - 36), (x, y - 50), (x + 20, y - 36)]), (92, 74, 62), 0.0)
