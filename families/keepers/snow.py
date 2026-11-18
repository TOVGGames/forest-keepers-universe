"""Snow for the Forest Keepers (episode 5, First Snow): falling flakes in parallax layers, and snow that settles
and piles up on everything (ground, roofs, posts, branches, leaves) as `depth` grows.

Snow lies only on surfaces that face up, thicker on flat tops than on slopes, with soft rounded ends that hang a
little over the edges. Moonlit snow is a cool blue-white, the side away from the moon a bit darker.
"""
import math

import numpy as np

from families.foundry.keepers.common import LEAF, LEAF_FAR, MOON, SKY_STAR, Night, ellipse, lerp, rect, smoothstep
from families.foundry.tree_monsters import BARK, EARTH, TRUNK

SNOW = np.array([206, 214, 232], np.float64)
SNOW_SHADE = np.array([156, 168, 198], np.float64)
SNOW_DEEP = np.array([176, 188, 214], np.float64)
FLAKE = np.array([226, 232, 244], np.float64)
FIELD = np.array([104, 112, 138], np.float64)      # snow on the ground in front, away from the lamps


class Snowfall:
    """Flakes in four depth layers. Layer 3 is the near one (big, soft, fast) and is drawn over the Keepers."""
    LAYERS = ((0.35, 1.3, 70.0, 0.35), (0.65, 2.2, 95.0, 0.55), (1.0, 3.4, 125.0, 0.8), (1.5, 6.5, 170.0, 0.9))

    def __init__(self, seed, n=600):
        rng = np.random.default_rng(seed + 1717)
        self.n = n
        self.fx = rng.uniform(0, 1, n)
        self.fy = rng.uniform(0, 1, n)
        self.layer = rng.choice(4, n, p=[0.3, 0.3, 0.28, 0.12])
        self.ph = rng.uniform(0, 2 * math.pi, n)
        self.sp = rng.uniform(0.75, 1.25, n)
        self.rank = rng.permutation(n) / n          # flakes with rank < amount are falling

    def draw(self, c, s, t, amount, wind=24.0, near=False):
        """amount 0..1 how hard it snows. near=False draws layers 0-2 (behind / among), True only layer 3."""
        if amount <= 0.001:
            return
        x0, x1, y0, y1 = s.view()
        W, H = x1 - x0, y1 - y0
        z = s.zoom
        for i in range(self.n):
            L = int(self.layer[i])
            if (L == 3) != near or self.rank[i] >= amount:
                continue
            par, r, fall, bright = self.LAYERS[L]
            # screen fractions: drift with the wind, fall, sway; the camera moves the layers at their own rate
            u = (self.fx[i] + (wind * t * par - s.cam_x * (par - 1.0) * 0.6) / 1920.0
                 + 0.012 * math.sin(t * 0.9 * self.sp[i] + self.ph[i])) % 1.0
            v = (self.fy[i] + fall * self.sp[i] * t / 1080.0 - s.cam_y * (par - 1.0) * 0.3 / 1080.0) % 1.0
            x, y = x0 - 0.02 * W + u * 1.04 * W, y0 - 0.02 * H + v * 1.04 * H
            rr = r / z
            col = FLAKE * bright
            if L == 3:
                c.circle(x, y, rr * 1.5, col * 0.45)
            c.circle(x, y, rr, col)


def _bumps(x, depth):
    return depth * (0.12 * math.sin(x * 0.031) + 0.08 * math.sin(x * 0.083 + 1.3))


def cap_line(c, pts, depth, col=SNOW, overhang=0.6):
    """Snow lying on a top edge (pts left to right, y down). Thinner where the edge is steep."""
    if depth < 0.6 or len(pts) < 2:
        return
    top, bot = [], []
    n = len(pts)
    # extend the ends a little: the snow overhangs and droops
    (ax, ay), (bx, by) = pts[0], pts[1]
    (cx_, cy_), (dx_, dy_) = pts[-2], pts[-1]
    ext = depth * overhang
    la = math.hypot(bx - ax, by - ay) or 1.0
    lb = math.hypot(dx_ - cx_, dy_ - cy_) or 1.0
    e0 = (ax - (bx - ax) / la * ext, ay - (by - ay) / la * ext + ext * 0.5)
    e1 = (dx_ + (dx_ - cx_) / lb * ext, dy_ + (dy_ - cy_) / lb * ext + ext * 0.5)
    full = [e0] + list(pts) + [e1]
    m = len(full)
    for i, (x, y) in enumerate(full):
        j0, j1 = max(0, i - 1), min(m - 1, i + 1)
        sx, sy = full[j1][0] - full[j0][0], full[j1][1] - full[j0][1]
        slope = abs(sy) / (math.hypot(sx, sy) or 1.0)
        hold = max(0.0, 1 - slope * 0.9) ** 1.2          # flat tops hold the most, steep ones less
        end = min(1.0, i / 1.5, (m - 1 - i) / 1.5)        # rounded ends
        d = depth * hold * (0.35 + 0.65 * smoothstep(end)) + _bumps(x, depth) * hold
        top.append((x, y - max(0.0, d)))
        bot.append((x, y + min(depth * 0.25, 3.0)))
    c.polygon(top + bot[::-1], col)
    # a soft shaded underside line where the snow meets the surface
    c.polyline(bot[1:-1], col * 0.82, max(1.0, depth * 0.12))


def cap_flat(c, x0, x1, y, depth, col=SNOW):
    """Snow on a flat top from x0 to x1."""
    n = max(3, int((x1 - x0) / 24))
    cap_line(c, [(lerp(x0, x1, i / (n - 1)), y) for i in range(n)], depth, col)


def cap_circle(c, cx, cy, r, depth, col=SNOW, a0=-2.55, a1=-0.59):
    """Snow on the top of a round thing (leaves, bushes): an arc band, thickest at the top."""
    if depth < 0.6:
        return
    n = 20
    outer, inner = [], []
    for i in range(n + 1):
        a = lerp(a0, a1, i / n)
        w = math.sin(math.pi * i / n) ** 0.7
        ro = r + depth * w * (1.0 + 0.15 * math.sin(a * 7 + cx * 0.01))
        ri = r - depth * 0.35 * w - 1
        outer.append((cx + math.cos(a) * ro, cy + math.sin(a) * ro))
        inner.append((cx + math.cos(a) * ri, cy + math.sin(a) * ri))
    c.polygon(outer + inner[::-1], col)


def ground(c, s, G, depth, x0=None, x1=None, col=SNOW):
    """Snow over the flat ground (after the ground slab): a white layer with a soft, slightly lumpy top."""
    if depth < 0.6:
        return
    vx0, vx1 = s.view()[:2]
    L = vx0 - 300 if x0 is None else max(x0, vx0 - 300)
    R = vx1 + 300 if x1 is None else min(x1, vx1 + 300)
    if R <= L:
        return
    xs = np.linspace(L, R, max(8, int((R - L) / 40)))
    # the snowy field in front of the scene (the ground slab, seen from above) goes white as the snow builds up
    k = min(1.0, depth / 14.0)
    rect(c, L, G, R, G + 40000, EARTH * (1 - k) + FIELD * k)
    for i, y in enumerate(np.arange(G + 70, G + 1200, 110)):
        c.line(L, y + 8 * math.sin(y), R, y - 8 * math.sin(y * 0.7), (EARTH * 0.8 * (1 - k) + FIELD * 0.9 * k), 3)
    top = [(x, G - depth - _bumps(x, depth) * 1.5) for x in xs]
    c.polygon(top + [(R, G + 6 + depth * 0.4), (L, G + 6 + depth * 0.4)], col)
    c.polyline([(x, G + 6 + depth * 0.4) for x in xs], SNOW_SHADE * 0.85, 2)


def front_lip(c, s, G, depth, x0=None, x1=None):
    """The front edge of the snow layer, drawn over feet so the Keepers stand in the snow, not on it."""
    if depth < 2:
        return
    vx0, vx1 = s.view()[:2]
    L = vx0 - 300 if x0 is None else max(x0, vx0 - 300)
    R = vx1 + 300 if x1 is None else min(x1, vx1 + 300)
    if R <= L:
        return
    xs = np.linspace(L, R, max(8, int((R - L) / 40)))
    h = depth * 0.55
    top = [(x, G - h - _bumps(x + 400, depth)) for x in xs]
    c.polygon(top + [(R, G + 8), (L, G + 8)], SNOW * 0.97)


def snowy_tree(c, x, base_y, h, seed, depth):
    """families.foundry.tree_monsters.tree (same shapes, same seed) with snow on the leaves."""
    rs = np.random.default_rng(seed)
    tw = 50
    top = base_y - h * 0.58
    c.polygon([(x - tw / 2, base_y), (x + tw / 2, base_y), (x + tw * 0.36, top), (x - tw * 0.36, top)], TRUNK)
    c.line(x - tw * 0.1, base_y, x - tw * 0.05, top + 20, BARK, 4)
    c.line(x + tw * 0.25, base_y - 30, x + tw * 0.18, top + 60, BARK, 3)
    cy = base_y - h * 0.74
    blobs = []
    for i in range(7):
        a = rs.uniform(0, 2 * math.pi)
        d = rs.uniform(0, h * 0.13)
        r = rs.uniform(0.17, 0.24) * h
        blobs.append((x + math.cos(a) * d * 1.3, cy + math.sin(a) * d - (i == 0) * h * 0.1, r, LEAF[i % 3]))
    for bx, by, r, col in blobs:
        c.circle(bx, by, r, col)
    c.circle(x - h * 0.06, cy - h * 0.08, h * 0.12, LEAF[1] * 1.12)
    for bx, by, r, col in sorted(blobs, key=lambda b: b[1]):
        cap_circle(c, bx, by, r, depth * 0.9 * (1.0 if by < cy else 0.6))


class SnowNight(Night):
    """Night backdrop for a snowy forest: the far tree line wears snow too."""

    def __init__(self, rng, ground, x0=-2000, x1=8000):
        super().__init__(rng, ground, x0, x1)
        self.depth = 0.0

    def draw(self, s, c, t, moon=True):
        cam_x, cam_y, w, h = s.cam_x, s.cam_y, s.w, s.h
        W, H = w + 200, h
        # sky in screen terms (the stars and the moon stay the same size however far the camera pulls back)
        vx0, vx1, vy0, vy1 = s.view()
        z = s.zoom
        for sx, sy, r, b in self.stars:
            x = vx0 + ((sx - cam_x * 0.08) % W - 100) / w * (vx1 - vx0)
            y = vy0 + ((sy - cam_y * 0.08) % H) / h * (vy1 - vy0)
            if y > self.ground - 200:
                continue
            tw = 0.75 + 0.25 * math.sin(t * 1.3 + sx)
            c.circle(x, y, r / z, SKY_STAR * b * tw * 0.45)      # fewer, fainter stars: there are clouds
        if moon:
            mx, my = vx0 + 0.8 * (vx1 - vx0), vy0 + 0.14 * (vy1 - vy0)
            if my < self.ground - 200:
                c.circle(mx, my, 62 / z, MOON * 0.85)
                c.circle(mx - 16 / z, my - 12 / z, 14 / z, MOON * 0.7)
                c.circle(mx + 20 / z, my + 16 / z, 9 / z, MOON * 0.72)
                s.glow_draw(lambda g: g.circle(mx, my, 90 / z, MOON * 0.3))
        G = self.ground
        vx0, vx1 = s.view()[:2]
        d = self.depth
        for fx_, sc in self.far:
            x = fx_ + cam_x * 0.4
            if x < vx0 - 300 or x > vx1 + 300:
                continue
            hh = 380 * sc
            c.polygon([(x - 14, G), (x + 14, G), (x + 10, G - hh * 0.5), (x - 10, G - hh * 0.5)], LEAF_FAR)
            c.circle(x, G - hh * 0.72, hh * 0.28, LEAF_FAR)
            c.circle(x - hh * 0.15, G - hh * 0.6, hh * 0.2, LEAF_FAR)
            c.circle(x + hh * 0.16, G - hh * 0.62, hh * 0.21, LEAF_FAR)
            if d > 0.6:
                cap_circle(c, x, G - hh * 0.72, hh * 0.28, d * 0.45, SNOW_SHADE * 0.62)
                cap_circle(c, x - hh * 0.15, G - hh * 0.6, hh * 0.2, d * 0.3, SNOW_SHADE * 0.58)
                cap_circle(c, x + hh * 0.16, G - hh * 0.62, hh * 0.21, d * 0.3, SNOW_SHADE * 0.58)
        if d > 0.6:     # the far forest floor is white too
            rect(c, vx0 - 300, G - 4, vx1 + 300, G + 2, SNOW_SHADE * 0.7)


def treehouse_caps(c, H, depth, leaves=True):
    """Snow on the treehouse (families.foundry.keepers.halloween.House): its leaves (call right after
    House.draw_tree), or with leaves=False the roof, platform, rail and branches (after House.draw_house)."""
    G, tx = H.G, H.tx
    if leaves:
        rs = np.random.default_rng(42)
        circ = []
        for k in range(16):
            cx = tx + rs.uniform(-750, 750)
            cy = G - 1150 - rs.uniform(-120, 260) - 200 * math.cos((cx - tx) / 1500 * math.pi)
            circ.append((cx, cy, rs.uniform(170, 260)))
        for cx, cy, r in sorted(circ, key=lambda q: q[1]):
            cap_circle(c, cx, cy, r, depth * 1.1)
        for (bx, by), (ex, ey) in H.branches:      # the branch tips that poke out of the leaves
            cap_line(c, [(lerp(bx, ex, 0.55), lerp(by, ey, 0.55) - 13), (ex, ey - 13)], depth * 0.6, overhang=0.3)
        return
    py = H.py
    cap_flat(c, H.p0, H.p1, py, depth)                                # the platform
    ridge = ((H.h0 + H.h1) / 2, H.wall_top - 190)
    for sgn in (-1, 1):
        eave = (H.h0 - 70 if sgn < 0 else H.h1 + 70, H.wall_top + 10)
        pts = [eave, ridge] if sgn < 0 else [ridge, eave]
        cap_line(c, [(lerp(pts[0][0], pts[1][0], i / 8), lerp(pts[0][1], pts[1][1], i / 8)) for i in range(9)],
                 depth * 1.25)
    for k in range(H.n_rungs):                                        # a little on every rung
        yk = H.rung_y(k)
        cap_flat(c, H.ladder_x - 36, H.ladder_x + 36, yk - 3, depth * 0.35)


def house_caps(c, spec, x, yb, depth, post=None):
    """Snow on one of the episode 4 houses (families/keepers/props.py), and on its post top if post = post top y."""
    w, h = spec.w, spec.h
    top = yb - h
    ridge = (x, top - spec.roof)
    for sx in (-1, 1):
        eave = (x + sx * (w / 2 + 16), top + 10)
        pts = [eave, ridge] if sx < 0 else [ridge, eave]
        cap_line(c, [(lerp(pts[0][0], pts[1][0], i / 6), lerp(pts[0][1], pts[1][1], i / 6)) for i in range(7)],
                 depth * 0.9)
