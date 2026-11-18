"""Things made and used in Forest Keepers episode 8, The Harvest Feast (docs/engines/forest_keepers_harvest_feast.md):
the oak and its acorns, the little roller mill by the water wheel (hopper, two round millstones with meshing gears,
the flour sack), the feast table (two fallen logs, ten cross planks), the clay oven, bread, acorn pies, plates and cups,
the lantern string, a squirrel and an owl. Drawing only; the acts decide where and when."""
import math

import cv2
import numpy as np

from families.foundry.keepers.common import PLANK, Xform, ellipse, lerp, rect, smoothstep
from families.foundry.style import IRON, STEEL
from families.foundry.tree_monsters import BARK, LAMP, LEAF, TRUNK

ACORN = np.array([152, 104, 56], np.float64)
ACORN_CAP = np.array([104, 78, 50], np.float64)
FLOUR = np.array([226, 216, 196], np.float64)
DOUGH = np.array([222, 200, 160], np.float64)
CRUST = np.array([170, 104, 52], np.float64)          # fully baked
PIE_FILL = np.array([120, 72, 42], np.float64)
CLAY = np.array([150, 92, 64], np.float64)
CLAY_WET = np.array([112, 70, 52], np.float64)
STONE = np.array([118, 112, 104], np.float64)
BASKET = np.array([168, 128, 76], np.float64)
SACK = np.array([176, 150, 110], np.float64)
PLATE = np.array([196, 178, 146], np.float64)          # wooden plates, a light wood
CUP = np.array([132, 92, 60], np.float64)
LOG = np.array([96, 70, 50], np.float64)
LOG_END = np.array([170, 132, 92], np.float64)
SQUIRREL = np.array([168, 90, 46], np.float64)
OWL = np.array([120, 96, 72], np.float64)
WATER_BLUE = np.array([110, 160, 214], np.float64)
SOOT = np.array([40, 30, 28], np.float64)


def clip_inside(c, pts, draw):
    """draw(), but keep it only inside the polygon pts (world units): everything it painted outside is put back.
    (Something coming out of a doorway is cut by the door edges, not covered by a patch.)"""
    img = c.target
    before = img.copy()
    draw()
    m = np.zeros(img.shape[:2], np.uint8)
    c.target = m
    try:
        c.polygon(pts, (255, 255, 255))
    finally:
        c.target = img
    out = m == 0
    img[out] = before[out]


# ====================================================================== acorns, basket, oak

def acorn(c, x, y, r=9.5, ang=0.0):
    """An acorn: (x, y) its middle; ang tilts it."""
    cv = Xform(c, 0, 0, ang, 1.0, x, y) if ang else c
    cv.polygon(ellipse(x, y + r * 0.15, r * 0.78, r * 1.0, 16), ACORN)
    cv.polygon(ellipse(x - r * 0.25, y + r * 0.1, r * 0.22, r * 0.5, 10), ACORN * 1.22)
    cv.polygon(ellipse(x, y - r * 0.55, r * 0.9, r * 0.5, 16, math.pi, 2 * math.pi), ACORN_CAP)
    cv.line(x - r * 0.88, y - r * 0.55, x + r * 0.88, y - r * 0.55, ACORN_CAP * 0.8, max(1.5, r * 0.25))
    cv.line(x, y - r * 1.0, x + r * 0.2, y - r * 1.4, ACORN_CAP * 0.8, max(1.2, r * 0.18))


def heap_spots(n, w, r=8.0):
    """Spots for n acorns heaped in a container w wide (bottom row first), relative to the bottom middle."""
    out, row, k = [], 0, 0
    per = max(1, int(w / (2 * r * 0.9)))
    while k < n:
        m = per - (row % 2)
        for i in range(m):
            if k >= n:
                break
            out.append(((i - (m - 1) / 2) * 2 * r * 0.9, -r - row * r * 1.5))
            k += 1
        row += 1
    return out


def basket(c, x, y, n, ang=0.0, w=118.0, h=44.0):
    """Woven basket: (x, y) = bottom middle; n acorns in it; ang tips it (about its middle)."""
    cy = y - h / 2
    cv = Xform(c, 0, 0, ang, 1.0, x, cy) if ang else c
    for (dx, dy) in heap_spots(n, w - 20):
        acorn(cv, x + dx, y - 4 + dy * 0.9, 8.0)
    body = [(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 - 10, y), (x - w / 2 + 10, y)]
    cv.polygon(body, BASKET)
    for k in range(1, 4):
        yy = y - h + k * h / 4
        cv.line(x - w / 2 + 3 * k, yy, x + w / 2 - 3 * k, yy, BASKET * 0.72, 2)
    for k in range(7):
        xx = x - w / 2 + 8 + k * (w - 16) / 6
        cv.line(xx, y - h, xx + (k - 3) * -1.2, y, BASKET * 0.8, 2)
    cv.line(x - w / 2 - 3, y - h, x + w / 2 + 3, y - h, BASKET * 0.66, 5)


def basket_mouth(x, y, ang, w=118.0, h=44.0):
    """World point at the low lip of a tipped basket (where the acorns pour out)."""
    cy = y - h / 2
    lx, ly = -w / 2 if ang < 0 else w / 2, -h / 2
    ca, sa = math.cos(ang), math.sin(ang)
    return x + lx * ca - ly * sa, cy + lx * sa + ly * ca


class Oak:
    """The big oak by the mill. The branch reaches left over the path; acorns hang under it in clusters. dip(x) is
    how far the branch bends down at x (Springs bouncing on it)."""

    def __init__(self, x, G):
        self.x, self.G = x, G
        self.b0 = (x - 30.0, G - 560.0)            # where the branch leaves the trunk
        self.b1 = (x - 420.0, G - 470.0)           # its tip
        self.stubs = [(x - 82.0, G - 180.0), (x - 74.0, G - 360.0)]   # two short stubs: Springs' steps up the trunk

    def branch_y(self, x, dip=0.0, at=None):
        """Top of the branch at x (bends most near the load point `at`, not at all at the trunk)."""
        (x0, y0), (x1, y1) = self.b0, self.b1
        u = min(1.0, max(0.0, (x0 - x) / (x0 - x1)))
        y = lerp(y0, y1, u) - 14 * (1 - u)
        return y + dip * min(1.0, u * 1.6)

    def draw_back(self, c, s, t):
        x, G = self.x, self.G
        rs = np.random.default_rng(88)
        for k in range(12):
            cx = x + rs.uniform(-520, 380)
            cy = G - 900 - rs.uniform(-80, 220) - 160 * math.cos((cx - x) / 1300 * math.pi)
            c.circle(cx, cy, rs.uniform(170, 250), LEAF[k % 3] * 0.8)
        c.polygon([(x - 80, G), (x + 80, G), (x + 58, G - 920), (x - 58, G - 920)], TRUNK)
        for k in (-1, 1):
            c.polygon([(x + k * 70, G), (x + k * 170, G + 4), (x + k * 60, G - 70)], TRUNK * 0.9)
        c.line(x - 20, G, x - 14, G - 860, BARK, 5)
        c.line(x + 30, G - 80, x + 24, G - 760, BARK, 3)
        for (sx, sy) in self.stubs:
            c.polygon([(x - 40, sy - 6), (sx - 34, sy - 4), (sx - 36, sy + 12), (x - 40, sy + 22)], TRUNK * 1.05)
            c.polygon(ellipse(sx - 35, sy + 4, 5, 8, 10), np.array([150, 116, 80]))

    def draw_branch(self, c, t, dip=0.0, hanging=()):
        """The acorn branch; `hanging`: (x, r) of acorns still on it."""
        xs = np.linspace(self.b1[0], self.b0[0], 18)
        top = [(xx, self.branch_y(xx, dip)) for xx in xs]
        thick = [lerp(10.0, 30.0, (xx - self.b1[0]) / (self.b0[0] - self.b1[0])) for xx in xs]
        bot = [(xx, yy + th) for (xx, yy), th in zip(top, thick)]
        c.polygon(top + bot[::-1], TRUNK * 1.02)
        c.polyline(top, BARK * 1.1, 3)
        for k, xx in enumerate((self.b1[0] + 40, self.b1[0] + 150, self.b1[0] + 260)):
            yy = self.branch_y(xx, dip)
            c.line(xx, yy, xx - 40, yy - 70 - 10 * k, TRUNK, 7)
            for q in range(3):
                c.polygon(ellipse(xx - 40 + (q - 1) * 22, yy - 80 - 10 * k + abs(q - 1) * 10, 20, 11, 10, q * 0.6),
                          LEAF[q] * 1.15)
        for (ax, r) in hanging:
            yy = self.branch_y(ax, dip) + lerp(10.0, 30.0, (ax - self.b1[0]) / (self.b0[0] - self.b1[0]))
            c.line(ax, yy - 4, ax, yy + 6, ACORN_CAP * 0.8, 2)
            acorn(c, ax, yy + 6 + r, r)


def squirrel(c, x, y, face=1, t=0.0, run=0.0, s=1.0, nibble=0.0):
    """A red squirrel, side view: (x, y) = its feet. run 0..1 = bounding gait, nibble 0..1 = sitting up eating."""
    ph = t * 14
    bound = run * abs(math.sin(ph)) * 8 * s
    y = y - bound
    sit = nibble
    tail = [(x - face * 14 * s, y - 10 * s), (x - face * 40 * s, y - 30 * s), (x - face * 46 * s, y - 62 * s),
            (x - face * 30 * s, y - 74 * s), (x - face * 22 * s, y - 52 * s), (x - face * 18 * s, y - 24 * s)]
    c.polygon(tail, SQUIRREL * 0.95)
    c.polygon(ellipse(x - face * 32 * s, y - 52 * s, 9 * s, 16 * s, 12), SQUIRREL * 1.15)
    by = y - (14 + 10 * sit) * s
    c.polygon(ellipse(x, by, (18 - 5 * sit) * s, (11 + 6 * sit) * s, 18, 0.0, 2 * math.pi), SQUIRREL)
    c.polygon(ellipse(x + face * 5 * s, by + 3 * s, 8 * s, 7 * s, 12), np.array([230, 206, 170]))
    hx, hy = x + face * (17 - 6 * sit) * s, by - (8 + 6 * sit) * s
    c.circle(hx, hy, 9 * s, SQUIRREL)
    c.polygon([(hx - face * 2 * s, hy - 7 * s), (hx - face * 7 * s, hy - 17 * s), (hx + face * 2 * s, hy - 9 * s)],
              SQUIRREL * 0.9)
    c.circle(hx + face * 4 * s, hy - 2 * s, 2.2 * s, np.array([16, 14, 16]))
    c.circle(hx + face * 9 * s, hy + 1 * s, 1.8 * s, np.array([60, 30, 30]))
    for k in (-1, 1):
        lift = run * max(0.0, math.sin(ph + k)) * 5 * s
        c.line(x + k * 8 * s, by + 6 * s, x + k * 9 * s, y - lift, SQUIRREL * 0.8, 3.5 * s)
    if nibble > 0.3:
        acorn(c, hx + face * 8 * s, hy + 9 * s, 5.5 * s)


def owl(c, s, x, y, t, k=1.0):
    """A tawny owl on a branch: (x, y) = its feet. Blinks slowly, turns its head now and then."""
    turn = math.sin(t * 0.35) * 0.5
    body = OWL
    c.polygon(ellipse(x, y - 40 * k, 30 * k, 42 * k, 24), body)
    c.polygon(ellipse(x, y - 32 * k, 20 * k, 28 * k, 20), np.array([196, 170, 130]))
    for i in range(3):
        for j in range(2):
            c.line(x - 8 * k + j * 14 * k, y - 46 * k + i * 12 * k, x - 4 * k + j * 14 * k, y - 42 * k + i * 12 * k,
                   OWL * 0.7, 2 * k)
    hx = x + turn * 8 * k
    c.circle(hx, y - 88 * k, 26 * k, body)
    c.polygon([(hx - 22 * k, y - 104 * k), (hx - 14 * k, y - 122 * k), (hx - 8 * k, y - 106 * k)], body * 0.9)
    c.polygon([(hx + 22 * k, y - 104 * k), (hx + 14 * k, y - 122 * k), (hx + 8 * k, y - 106 * k)], body * 0.9)
    bl = 1.0 if (t % 5.0) < 0.22 else 0.0
    for sx in (-1, 1):
        ex = hx + sx * 11 * k
        c.circle(ex, y - 90 * k, 9 * k, np.array([214, 196, 160]))
        if bl:
            c.line(ex - 8 * k, y - 90 * k, ex + 8 * k, y - 90 * k, OWL * 0.6, 2.5 * k)
        else:
            c.circle(ex + turn * 2 * k, y - 90 * k, 5 * k, np.array([24, 18, 14]))
            c.circle(ex + turn * 2 * k - 1.5 * k, y - 92 * k, 1.6 * k, np.array([240, 236, 220]))
    c.polygon([(hx - 4 * k, y - 82 * k), (hx + 4 * k, y - 82 * k), (hx, y - 72 * k)], np.array([210, 170, 80]))
    for sx in (-1, 1):
        c.line(x + sx * 8 * k, y - 4 * k, x + sx * 10 * k, y, np.array([200, 170, 90]), 3 * k)


# ====================================================================== the mill

def gear(c, x, y, r, rot, teeth=22, col=None):
    """A wooden spur gear with pegs round the rim (seen face-on)."""
    col = PLANK * 0.8 if col is None else col
    c.circle(x, y, r, col)
    c.circle(x, y, r, col * 0.6, False, 3)
    for k in range(teeth):
        a = rot + k * 2 * math.pi / teeth
        ca, sa = math.cos(a), math.sin(a)
        c.line(x + ca * (r - 2), y + sa * (r - 2), x + ca * (r + 7), y + sa * (r + 7), col * 1.12, 6)
    for k in range(4):
        a = rot + k * math.pi / 2 + math.pi / 4
        c.line(x, y, x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, col * 0.62, 5)


def millstone(c, x, y, r, rot):
    """A round millstone roller, face-on: grooves turn with it."""
    c.circle(x, y, r, STONE)
    c.circle(x, y, r, STONE * 0.65, False, 4)
    rs = np.random.default_rng(int(x) % 97)
    for k in range(9):                         # speckles
        a = rot + rs.uniform(0, 2 * math.pi)
        d = rs.uniform(0.25, 0.85) * r
        c.circle(x + math.cos(a) * d, y + math.sin(a) * d, rs.uniform(2, 4), STONE * rs.uniform(0.75, 1.2))
    for k in range(6):                         # dressing grooves
        a = rot + k * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        c.line(x + ca * r * 0.32, y + sa * r * 0.32, x + ca * r * 0.92, y + sa * r * 0.92, STONE * 0.72, 3)
    c.circle(x, y, r * 0.18, IRON * 1.2)
    c.circle(x, y, r * 0.07, STEEL * 1.4)


def hopper(c, x, top, throat, w_top, w_throat, fill_n, t, ac_r=8.0):
    """Wooden hopper over the stones: acorns heaped inside up to fill_n."""
    pts = [(x - w_top / 2, top), (x + w_top / 2, top), (x + w_throat / 2, throat), (x - w_throat / 2, throat)]
    c.polygon(pts, PLANK * 0.5)                # the inside (back) of the hopper, dark
    if fill_n > 0:
        h = throat - top
        level = min(1.0, 0.08 + fill_n / 34.0)
        ly = throat - h * level
        wl = lerp(w_throat, w_top, level) - 14
        rs = np.random.default_rng(5)
        n = min(int(fill_n), 40)
        for k in range(n):                     # acorns piled in it, the top ones on the surface
            u = (k + 0.5) / max(1, n)
            yy = lerp(throat - 8, ly + 6, u ** 0.8)
            ww = lerp(w_throat, wl, (throat - yy) / h)
            xx = x + rs.uniform(-0.5, 0.5) * max(4.0, ww - 2 * ac_r)
            acorn(c, xx, yy, ac_r, rs.uniform(-0.6, 0.6))
    # front boards (just the rim and the edges: it is open at the front so you see in, the cut edge is clean)
    c.line(x - w_top / 2, top, x - w_throat / 2, throat, PLANK * 0.9, 9)
    c.line(x + w_top / 2, top, x + w_throat / 2, throat, PLANK * 0.9, 9)
    c.line(x - w_top / 2 - 6, top, x + w_top / 2 + 6, top, PLANK, 8)
    c.line(x - w_throat / 2 - 4, throat, x + w_throat / 2 + 4, throat, PLANK * 0.8, 6)


def sack(c, x, G, fill, tied=0.0, lift=None):
    """Flour sack standing at x (or lifted: lift = (x, y_bottom)). fill 0..1 how full; tied 0..1 the neck tied."""
    if lift is not None:
        x, G = lift
    h = 76 + 70 * fill
    w = 92 + 26 * fill
    top = G - h
    neck = lerp(w * 0.5, 22, tied)
    body = [(x - w / 2 + 6, G), (x + w / 2 - 6, G), (x + w / 2, G - h * 0.35), (x + w / 2 - 6, G - h * 0.75),
            (x + neck / 2 + 6, top + 12 * tied), (x - neck / 2 - 6, top + 12 * tied), (x - w / 2 + 6, G - h * 0.75),
            (x - w / 2, G - h * 0.35)]
    c.polygon(body, SACK)
    c.polyline(body, SACK * 0.68, 2.5, closed=True)
    c.line(x - w / 2 + 14, G - h * 0.5, x + w / 2 - 14, G - h * 0.5 - 3, SACK * 0.82, 2)
    if tied < 0.5:                             # open: the flour shows inside the mouth
        c.polygon(ellipse(x, top + 2, neck / 2 + 6, 7, 18), SACK * 0.55)
        if fill > 0.02:
            c.polygon(ellipse(x, top + 3, neck / 2 + 2, 5, 18), FLOUR * (0.85 + 0.15 * fill))
    else:
        c.polygon([(x - 18, top + 12), (x + 18, top + 12), (x + 26, top - 14), (x - 26, top - 14)], SACK * 0.95)
        c.line(x - 16, top + 12, x + 16, top + 12, np.array([150, 128, 92]), 4)
    c.text("FLOUR", x, G - h * 0.42, 18 + 4 * fill, SACK * 0.55)


def flour_stream(c, s, x, y0, y1, rate, t):
    """Flour falling from the stones to the sack, rate 0..1."""
    if rate <= 0.02 or y1 <= y0:
        return
    w = 3 + 9 * rate
    for k in range(3):
        xs = x + (k - 1) * w * 0.35
        pts = [(xs + 2.0 * math.sin(yy * 0.06 + t * 9 + k), yy) for yy in np.linspace(y0, y1, 12)]
        c.polyline(pts, FLOUR * (0.75 + 0.1 * k), max(1.5, w * 0.5))
    for k in range(int(4 + 8 * rate)):
        u = (t * 2.4 + k * 0.137) % 1.0
        yy = lerp(y0, y1, u)
        c.circle(x + 6 * math.sin(k * 2.1 + t * 3), yy, 2.0, FLOUR * 0.95)


def crossed_belt(c, p0, r0, p1, r1, phase, col=None):
    """A crossed belt (one twist) between two pulleys: it turns the second pulley the other way round (the stones
    have to turn in towards the nip, the wheel turns the other way). `phase` = belt travelled, moves the marks."""
    col = np.array([96, 62, 40], np.float64) if col is None else col
    (x0, y0), (x1, y1) = p0, p1
    d = math.hypot(x1 - x0, y1 - y0) + 1e-9
    nx, ny = -(y1 - y0) / d, (x1 - x0) / d
    for sgn in (1, -1):
        a = (x0 + nx * r0 * sgn, y0 + ny * r0 * sgn)
        b = (x1 - nx * r1 * sgn, y1 - ny * r1 * sgn)
        c.line(a[0], a[1], b[0], b[1], col * (1.0 if sgn > 0 else 0.85), 7)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for m in np.arange((phase * sgn) % 90, L, 90):
            u = m / L
            px_, py_ = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            c.line(px_, py_, px_ + (b[0] - a[0]) / L * 12, py_ + (b[1] - a[1]) / L * 12, col * 0.55, 7)


def post(c, x, y, L, ang=0.0, w=26.0, shade=1.0, fork=False):
    """A sawn post standing on (x, y) (its foot), leaning `ang` from upright (positive: top to the right)."""
    sa, ca = math.sin(ang), math.cos(ang)
    tx, ty = x + sa * L, y - ca * L
    nx, ny = ca * w / 2, sa * w / 2
    col = TRUNK * 1.12 * shade
    c.polygon([(x - nx, y - ny), (x + nx, y + ny), (tx + nx, ty + ny), (tx - nx, ty - ny)], col)
    c.line(x - nx * 0.3, y - ny * 0.3, tx - nx * 0.3, ty - ny * 0.3, BARK * 1.2 * shade, 3)
    c.line(tx - nx, ty - ny, tx + nx, ty + ny, np.array([190, 150, 104]) * shade, 3)     # the sawn top
    if fork:                                     # a fork at the top for an axle
        for sg in (-1, 1):
            c.line(tx + sg * nx * 0.6, ty + sg * ny * 0.6, tx + sg * nx * 1.3 + sa * 26, ty + sg * ny * 1.3 - ca * 26,
                   col, 9)


def post_hole(c, x, y, dug=1.0, filled=0.0):
    """A post hole: dug 0..1 (the heap of soil beside it grows), filled 0..1 tamped back round the post."""
    if dug <= 0:
        return
    c.polygon(ellipse(x, y + 4, 24 * dug, 8 * dug, 14), np.array([22, 16, 14]) if filled < 0.5 else np.array([52, 40, 32]))
    heap = (1 - filled) * dug
    if heap > 0.02:
        c.polygon(ellipse(x + 44, y + 2, 26 * heap + 4, 16 * heap + 2, 14, math.pi, 2 * math.pi), np.array([70, 54, 42]))


def beam(c, x0, x1, y, h=24.0, shade=1.0):
    c.polygon([(x0, y - h), (x1, y - h), (x1, y), (x0, y)], TRUNK * 1.05 * shade)
    c.line(x0, y - h * 0.4, x1, y - h * 0.4, BARK * 1.15 * shade, 3)
    for xx in (x0, x1):
        c.line(xx, y - h, xx, y, np.array([190, 150, 104]) * shade, 3)


def shed_roof(c, x0, x1, eave, ridge, boards):
    """The mill shed's roof: rafters, then `boards` roof boards (2 per side, left side first)."""
    xm = (x0 + x1) / 2
    for sg in (-1, 1):
        e = (x0 - 70 if sg < 0 else x1 + 70, eave + 14)
        c.line(xm, ridge + 10, e[0], e[1], TRUNK * 0.9, 12)
    for k in range(int(boards)):
        side, j = divmod(k, 2)
        sg = -1 if side == 0 else 1
        e = (x0 - 70 if sg < 0 else x1 + 70, eave + 14)
        a0, a1 = j / 2, (j + 1) / 2
        p0 = (lerp(xm, e[0], a0), lerp(ridge, e[1], a0))
        p1 = (lerp(xm, e[0], a1), lerp(ridge, e[1], a1))
        col = np.array([92, 60, 44]) * (1.0 - 0.06 * j)
        c.polygon([p0, p1, (p1[0], p1[1] + 26), (p0[0], p0[1] + 26)], col)
        c.line(p0[0], p0[1], p1[0], p1[1], np.array([128, 86, 60]), 3)


def string_line(c, s, x0, y0, x1, y1, ok=0.0, a=1.0):
    """Glo's glowing string line between two points; it turns green when they are level."""
    col = lerp(LAMP, np.array([150, 230, 130]), ok) * a
    c.line(x0, y0, x1, y1, col * 0.9, 3)
    s.glow_draw(lambda g: g.line(x0, y0, x1, y1, col * 0.5, 8))


def millstone_dressed(c, x, y, r, rot, hole=1.0, grooves=6, alpha=1.0):
    """A round millstone face-on, being dressed: hole 0..1 the axle hole tapped through, grooves 0..6 cut."""
    c.circle(x, y, r, STONE)
    c.circle(x, y, r, STONE * 0.65, False, 4)
    rs = np.random.default_rng(int(x) % 97)
    for k in range(9):
        a = rot + rs.uniform(0, 2 * math.pi)
        d = rs.uniform(0.25, 0.85) * r
        c.circle(x + math.cos(a) * d, y + math.sin(a) * d, rs.uniform(2, 4), STONE * rs.uniform(0.75, 1.2))
    for k in range(int(grooves)):
        a = rot + k * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        c.line(x + ca * r * 0.32, y + sa * r * 0.32, x + ca * r * 0.92, y + sa * r * 0.92, STONE * 0.72, 3)
    if hole > 0:
        c.circle(x, y, r * 0.18 * min(1.0, hole), np.array([40, 38, 36]) if hole < 1 else IRON * 1.2)
        if hole >= 1:
            c.circle(x, y, r * 0.07, STEEL * 1.4)


def gear_cut(c, x, y, r, rot, teeth, n_cut, col=None):
    """A wooden gear wheel being made: a round slice of log with n_cut of its `teeth` notched so far."""
    col = PLANK * 0.8 if col is None else col
    c.circle(x, y, r + 7, col * 0.95)
    c.circle(x, y, r + 7, col * 0.6, False, 3)
    for k in range(teeth):                       # each notch cut leaves a tooth either side of it
        if k < n_cut:
            a = rot + (k + 0.5) * 2 * math.pi / teeth
            c.line(x + math.cos(a) * (r - 1), y + math.sin(a) * (r - 1), x + math.cos(a) * (r + 9),
                   y + math.sin(a) * (r + 9), np.array([14, 16, 24]), 6)
    for q in range(3):                            # growth rings of the log slice
        c.circle(x, y, r * (0.3 + 0.22 * q), col * 0.78, False, 2)
    c.circle(x, y, r * 0.12, col * 0.5)


def hopper_build(c, x, top, throat, w_top, w_throat, boards):
    """The hopper put together board by board (0..4): left side, right side, the front rim, the throat."""
    if boards >= 1:
        c.line(x - w_top / 2, top, x - w_throat / 2, throat, PLANK * 0.9, 9)
    if boards >= 2:
        c.line(x + w_top / 2, top, x + w_throat / 2, throat, PLANK * 0.9, 9)
    if boards >= 3:
        c.line(x - w_top / 2 - 6, top, x + w_top / 2 + 6, top, PLANK, 8)
    if boards >= 4:
        c.line(x - w_throat / 2 - 4, throat, x + w_throat / 2 + 4, throat, PLANK * 0.8, 6)


def acorn_pile(c, x, y, n=40, w=150.0):
    rs = np.random.default_rng(3)
    for k in range(n):
        u = k / max(1, n - 1)
        hy = (1 - (2 * rs.uniform() - 1) ** 2)
        acorn(c, x + rs.uniform(-1, 1) * w * (1 - 0.6 * u), y - 6 - 34 * u * hy, 9.0, rs.uniform(-1.2, 1.2))


# ====================================================================== the feast table

def log_rail(c, x0, x1, y, r):
    """A fallen log lying along the table: (x0..x1) its length, y its top."""
    rect(c, x0, y, x1, y + 2 * r, LOG)
    c.line(x0, y + r * 0.5, x1, y + r * 0.5, LOG * 1.15, 3)
    c.line(x0, y + r * 1.4, x1, y + r * 1.4, LOG * 0.8, 3)
    for xx in (x0, x1):
        c.polygon(ellipse(xx, y + r, r * 0.45, r, 16), LOG_END)
        c.polygon(ellipse(xx, y + r, r * 0.25, r * 0.55, 12), LOG_END * 0.85)


def plank_laid(c, x0, x1, yb, yf, shade=1.0, press=0.0):
    """A cross plank lying on the two logs, seen from above at an angle: x0..x1 its width, from the back log (yb)
    to the front one (yf); 9 px thick."""
    yb, yf = yb + press, yf + press
    col = PLANK * shade
    c.polygon([(x0, yb), (x1, yb), (x1 + 6, yf), (x0 + 6, yf)], col)
    c.polygon([(x0 + 6, yf), (x1 + 6, yf), (x1 + 6, yf + 9), (x0 + 6, yf + 9)], col * 0.7)
    c.line(x0 + 10, lerp(yb, yf, 0.35), x1 - 6, lerp(yb, yf, 0.4), col * 0.85, 2)
    c.line(x1, yb, x1 + 6, yf, col * 0.62, 2)


def plank_side(c, x, y, L, ang=0.0, ragged=0.0, shade=1.0):
    """A plank seen along its length (on the sawhorses, on Wheels' head): (x, y) = bottom middle; ragged px of rough
    end past the cut line on its right."""
    cv = Xform(c, 0, 0, ang, 1.0, x, y - 5) if ang else c
    x0, x1 = x - L / 2, x + L / 2 + ragged
    cv.polygon([(x0, y - 11), (x1, y - 11), (x1, y), (x0, y)], PLANK * shade)
    cv.line(x0, y - 7, x1, y - 7, PLANK * 0.82 * shade, 2)
    if ragged > 1:
        cv.polygon([(x1, y - 11), (x1 + 5, y - 7), (x1 - 2, y - 4), (x1 + 4, y)], PLANK * 0.78 * shade)
    else:
        cv.line(x1, y - 11, x1, y, np.array([214, 184, 140]) * shade, 3)
    cv.line(x0, y - 11, x0, y, np.array([214, 184, 140]) * shade, 3)


def plank_between(c, x, y, u, L, W, yb, yf, ragged=0.0):
    """A plank turning from 'along' (u=0: seen as L long, 11 thick, bottom middle at (x, y)) to 'laid across' (u=1:
    W wide, from yb to yf) - Hans swings it round as he lays it."""
    if u <= 0.0:
        plank_side(c, x, y, L, ragged=ragged)
        return
    if u >= 1.0:
        plank_laid(c, x - W / 2, x + W / 2, yb, yf)
        return
    a = [(x - L / 2, y - 11), (x + L / 2 + ragged, y - 11), (x + L / 2 + ragged, y), (x - L / 2, y)]
    b = [(x - W / 2, yb), (x + W / 2, yb), (x + W / 2 + 6, yf), (x - W / 2 + 6, yf)]
    e = smoothstep(u)
    pts = [(lerp(p[0], q[0], e), lerp(p[1], q[1], e)) for p, q in zip(a, b)]
    c.polygon(pts, PLANK)
    c.polyline(pts, PLANK * 0.7, 2, closed=True)


def sawhorse(c, x, top, G):
    c.line(x - 34, G, x - 8, top, TRUNK * 1.1, 9)
    c.line(x + 34, G, x + 8, top, TRUNK * 1.1, 9)
    c.line(x - 22, lerp(G, top, 0.4), x + 22, lerp(G, top, 0.4), TRUNK, 6)
    rect(c, x - 30, top - 4, x + 30, top + 6, TRUNK * 1.25)


# ====================================================================== the clay oven

def oven_profile(cx, G, R, H, u):
    """Point on the dome outline at u (0 left foot .. 1 right foot)."""
    a = math.pi * (1 - u)
    return cx + math.cos(a) * R, G - math.sin(a) * H


CLAY_DRY = np.array([148, 124, 104], np.float64)    # grey-ochre clay (cooler than the wood, so it never reads as boards)
CLAY_FRESH = np.array([112, 90, 76], np.float64)   # a coil just laid, still wet
OVEN_STONE = np.array([112, 110, 106], np.float64)

OVEN_STONES = 11                                    # 3 hearth slabs, 5 base stones, 2 mouth stones, the lintel


def oven_stone_spots(cx, G, R, H):
    """Where each oven stone goes, in the order Digs lays them: (x, y, rx, ry, kind)."""
    mw, mh = R * 0.72, H * 0.52
    out = [(cx - R * 0.66 + R * 0.66 * k, G + 2, R * 0.36, 9, "slab") for k in range(3)]          # the hearth
    for k, u in enumerate((0.02, 0.17, 0.5, 0.83, 0.98)):                                        # the base ring
        if k == 2:
            out.append((cx + R * 0.25, G - 20, 26, 20, "stone"))   # (the middle one sits behind, beside the mouth)
        else:
            out.append((cx - R + 2 * R * u, G - 20, 28, 20, "stone"))
    out.append((cx - mw / 2 - 16, G - mh * 0.45, 18, mh * 0.45, "jamb"))                         # the mouth
    out.append((cx + mw / 2 + 16, G - mh * 0.45, 18, mh * 0.45, "jamb"))
    out.append((cx, G - mh - 14, mw / 2 + 30, 13, "lintel"))
    return out


def draw_oven(c, s, cx, G, R, H, rings, ring_u, chimney, wood, fire, t, items=None, n=6, stones=OVEN_STONES,
              smoothed=99, soot=0.0):
    """The oven Digs builds, stone and clay (owner after FK0005's first cut: an oven can't be wood): a hearth of flat
    stones, a ring of stones at the foot, stone jambs and a lintel round the mouth, then `n` coils of clay laid on top
    (`rings` done, the next one ring_u laid round from the left), each one smoothed into the dome by Hans (coils below
    `smoothed` have no seam left), then the chimney. The mouth shows the wood, the fire and what is baking."""
    if stones <= 0 and rings <= 0 and ring_u <= 0:
        return
    hh = H / n
    mw, mh = R * 0.72, H * 0.52
    spots = oven_stone_spots(cx, G, R, H)

    def half(h):                                  # half-width of the dome at height h
        return R * math.sqrt(max(0.0, 1 - (h / H) ** 2))

    def stone(sp, k):
        x, y, rx, ry, kind = sp
        col = OVEN_STONE * (0.92 + 0.06 * ((k * 7) % 3))
        if kind == "slab":
            c.polygon([(x - rx, y - ry), (x + rx - 4, y - ry - 1), (x + rx, y + ry), (x - rx + 3, y + ry)], col)
            c.line(x - rx, y - ry, x + rx - 4, y - ry - 1, col * 1.18, 2)
        elif kind == "lintel":
            c.polygon([(x - rx, y - ry), (x + rx, y - ry - 2), (x + rx - 6, y + ry), (x - rx + 5, y + ry)], col)
            c.line(x - rx, y - ry, x + rx, y - ry - 2, col * 1.18, 2)
        else:
            c.polygon(ellipse(x, y, rx, ry, 18), col)
            c.polygon(ellipse(x - rx * 0.25, y - ry * 0.35, rx * 0.45, ry * 0.3, 12), col * 1.15)
    for k in range(min(stones, 8)):               # hearth and base, under the clay
        stone(spots[k], k)
    for k in range(n):
        u = 1.0 if k < rings else (ring_u if k == rings else 0.0)
        if u <= 0:
            continue
        h0, h1 = k * hh, (k + 1) * hh
        hs = np.linspace(h0, h1, 6)
        left = [(cx - half(h), G - h) for h in hs]
        right = [(cx - half(h) + 2 * half(h) * u, G - h) for h in hs[::-1]]
        fresh = 1.0 - min(1.0, max(0.0, (rings - k) * 0.5)) if k >= smoothed else 0.0
        col = lerp(CLAY_DRY, CLAY_FRESH, 0.35 * fresh + (0.6 if k == rings else 0.0))
        c.polygon(left + right, col)
        if k >= smoothed or k == rings:           # a coil not smoothed yet: its rounded ridge still shows
            c.polyline([(cx - half(h0 + hh * 0.85) + 2 * half(h0 + hh * 0.85) * f, G - h0 - hh * 0.85 - 2 * math.sin(f * 40))
                        for f in np.linspace(0, u, 24)], col * 1.12, 3)
            c.polyline([(cx - half(h0) + 2 * half(h0) * f, G - h0) for f in np.linspace(0, u, 24)], col * 0.82, 2)
    done = min(rings, smoothed)
    if done > 0:                                  # the smoothed dome: soft shading and a few specks, no seams
        htop = min(H, done * hh)
        rs = np.random.default_rng(7)
        for q in range(26):
            hq = rs.uniform(4, htop - 4)
            xq = cx + rs.uniform(-0.9, 0.9) * half(hq)
            c.circle(xq, G - hq, rs.uniform(1.5, 3.2), CLAY_DRY * rs.choice([0.85, 1.1]))
        hl = [(cx - half(h) * 0.55, G - h) for h in np.linspace(htop * 0.35, htop * 0.85, 8)]
        c.polyline(hl, CLAY_DRY * 1.16, 5)
    if rings >= 3:                                # the mouth
        top = G - mh
        arch = [(cx - mw / 2, G - 6)] + [(cx + math.cos(a) * mw / 2, top + mh * 0.5 - math.sin(a) * mh * 0.5)
                                        for a in np.linspace(math.pi, 0, 20)] + [(cx + mw / 2, G - 6)]
        inside = SOOT + LAMP * 0.25 * fire
        c.polygon(arch, inside)
        if wood > 0:
            for q in range(int(round(wood * 4))):
                lx = cx - mw * 0.28 + (q % 2) * mw * 0.18
                ly = G - 12 - (q // 2) * 12
                c.line(lx, ly, lx + mw * 0.4, ly - 4, np.array([90, 62, 44]) * (1 - 0.6 * fire), 10)
        if fire > 0:
            for q in range(5):
                fx = cx - mw * 0.25 + q * mw * 0.12
                fh = mh * (0.35 + 0.18 * math.sin(t * 7 + q * 1.9)) * fire
                c.polygon([(fx - 12, G - 18), (fx + 12, G - 18), (fx + 3 * math.sin(t * 5 + q), G - 18 - fh)],
                          lerp(np.array([220, 110, 40]), np.array([255, 200, 90]), 0.5 + 0.5 * math.sin(t * 6 + q)))
            s.glow_draw(lambda g: g.circle(cx, G - mh * 0.45, mw * 0.55, LAMP * 0.16 * fire))
        if items is not None:
            clip_inside(c, arch, lambda: items(c))
        if soot > 0:                              # smoke has blackened the clay over the mouth
            c.polygon(ellipse(cx, top - 22, mw * 0.5 * (0.6 + 0.4 * soot), 26 * soot + 4, 20), lerp(CLAY_DRY, SOOT, 0.55 * soot))
    for k in range(8, min(stones, OVEN_STONES)):  # jambs and lintel frame the mouth
        stone(spots[k], k)
    if chimney > 0:
        h = 70 * chimney
        x0 = cx + R * 0.32
        ytop = G - H * 0.86
        c.polygon([(x0 - 16, ytop + 10), (x0 + 16, ytop + 10), (x0 + 14, ytop - h), (x0 - 14, ytop - h)], CLAY_DRY * 0.94)
        c.line(x0 - 18, ytop - h, x0 + 18, ytop - h, CLAY_DRY * 0.8, 6)


def chimney_top(cx, G, R, H):
    return cx + R * 0.32, G - H * 0.86 - 70


# ====================================================================== food, plates, cups

def bake_col(bake):
    return lerp(DOUGH, CRUST, smoothstep(min(1.0, max(0.0, bake))))


def loaf(c, x, y, bake=0.0, eaten=0.0, scored=0.0, r=30.0):
    """A round loaf: (x, y) = its bottom middle. eaten 0..1 = how much is gone (bites taken from the right)."""
    if eaten >= 0.99:
        return
    col = bake_col(bake)
    pts = ellipse(x, y - r * 0.55, r, r * 0.62, 30, math.pi, 2 * math.pi) + [(x + r, y), (x - r, y)]
    if eaten > 0:
        cut = x + r - 2 * r * eaten
        pts = [(min(px, cut + 6 * math.sin(py * 0.3)), py) for px, py in pts]
    c.polygon(pts, col)
    c.polygon([(px, py) for px, py in ellipse(x - r * 0.3, y - r * 0.85, r * 0.35, r * 0.15, 12)
               if eaten <= 0 or px < x + r - 2 * r * eaten], col * 1.12)
    if scored > 0:
        sc = col * 0.7
        k = smoothstep(scored)
        c.line(x - r * 0.35 * k, y - r * 0.95, x + r * 0.35 * k, y - r * 0.85, sc, 3)
        if scored > 0.5:
            c.line(x, y - r * 1.12, x + r * 0.05, y - r * 0.7 * k, sc, 3)
    if eaten > 0:
        cut = x + r - 2 * r * eaten
        c.line(cut, y - 2, cut + 3, y - r * 1.0, np.array([236, 220, 186]), 3)


def pie(c, x, y, bake=0.0, eaten=0.0, filled=1.0, r=36.0):
    """An acorn pie in its crust: (x, y) = bottom middle."""
    if eaten >= 0.99:
        return
    col = bake_col(bake)
    lim = x + r - 2 * r * eaten
    base = [(x - r, y - 14), (x + r, y - 14), (x + r - 6, y), (x - r + 6, y)]
    base = [(min(px, lim), py) for px, py in base]
    c.polygon(base, col * 0.9)
    top = ellipse(x, y - 14, r, 9, 24)
    c.polygon([(min(px, lim), py) for px, py in top], col)
    if filled > 0:
        fill = ellipse(x, y - 15, r - 7, 6, 24)
        c.polygon([(min(px, lim - 4), py) for px, py in fill], lerp(DOUGH, PIE_FILL, filled) * (1 - 0.2 * bake))
        for q in range(5):
            ax = x - r * 0.5 + q * r * 0.25
            if ax < lim - 6 and filled > 0.6:
                c.circle(ax, y - 16 + (q % 2) * 2, 3, ACORN * (1.1 - 0.25 * bake))


def piece(c, x, y, kind, bake, eaten=0.0):
    """A served piece on a plate: a wedge of loaf or of pie."""
    if eaten >= 0.99:
        return
    w = 26 * (1 - eaten)
    col = bake_col(bake)
    if kind == "loaf":
        c.polygon([(x - 13, y), (x - 13 + w, y), (x - 13 + w, y - 18), (x - 13, y - 22)], col)
        c.line(x - 13 + w, y - 1, x - 13 + w, y - 17, np.array([236, 220, 186]), 3)
    else:
        c.polygon([(x - 13, y), (x - 13 + w, y), (x - 13 + w * 0.9, y - 10), (x - 13, y - 12)], col)
        c.line(x - 12, y - 11, x - 13 + w * 0.9, y - 9, PIE_FILL, 3)


def plate(c, x, y):
    c.polygon(ellipse(x, y, 30, 8, 20), PLATE * 0.8)
    c.polygon(ellipse(x, y - 1, 24, 5.5, 20), PLATE)


def cup(c, x, y):
    c.polygon([(x - 8, y - 22), (x + 8, y - 22), (x + 6, y), (x - 6, y)], CUP)
    c.polygon(ellipse(x, y - 22, 8, 3, 12), CUP * 0.6)
    c.arc(x + 9, y - 12, 6, -90, 90, CUP * 0.9, 3)


def bowl(c, x, y, flour=0.0, water=0.0, dough=0.0, squeeze=0.0):
    """Mixing bowl on the bench: (x, y) its bottom middle."""
    if dough > 0:
        c.polygon(ellipse(x + squeeze * 6, y - 34 - 10 * dough, 40 - 6 * squeeze, 14 + 10 * dough * (1 - squeeze * 0.4),
                          24), lerp(FLOUR, DOUGH, dough))
    elif flour > 0:
        c.polygon(ellipse(x, y - 36, 40, 6 + 10 * flour, 24, math.pi, 2 * math.pi), FLOUR)
        if water > 0:
            c.polygon(ellipse(x + 4, y - 37, 16 * water, 4 * water, 16), WATER_BLUE * 0.8)
    c.polygon([(x - 52, y - 36), (x + 52, y - 36), (x + 34, y), (x - 34, y)], np.array([156, 112, 76]))
    c.line(x - 54, y - 36, x + 54, y - 36, np.array([120, 84, 56]), 5)


def jug(c, x, y, ang=0.0, water=1.0):
    cv = Xform(c, 0, 0, ang, 1.0, x, y - 30) if ang else c
    cv.polygon([(x - 18, y - 50), (x + 14, y - 50), (x + 22, y - 20), (x + 16, y), (x - 16, y), (x - 22, y - 20)],
               np.array([170, 120, 90]))
    cv.polygon([(x + 14, y - 50), (x + 26, y - 56), (x + 18, y - 44)], np.array([170, 120, 90]))
    cv.arc(x - 24, y - 30, 12, 90, 270, np.array([140, 98, 72]), 4)


def stump_board(c, x0, x1, y):
    """A wide wooden board the hot bread goes on."""
    c.polygon([(x0, y - 8), (x1, y - 8), (x1 + 4, y), (x0 - 4, y)], PLANK * 1.05)
    c.line(x0, y - 4, x1, y - 4, PLANK * 0.8, 2)


# ====================================================================== lantern string

def lantern_string(c, s, t, x0, x1, y_end, sag, lamps, lit):
    """A rope between two trees with lanterns hanging from it; lamps: x of each, lit: 0..1 each."""
    def rope_y(x):
        u = (x - x0) / (x1 - x0)
        return y_end + sag * 4 * u * (1 - u)
    pts = [(x, rope_y(x)) for x in np.linspace(x0, x1, 40)]
    c.polyline(pts, np.array([70, 58, 44]), 3)
    for k, lx in enumerate(lamps):
        ly = rope_y(lx)
        sway = 0.06 * math.sin(t * 1.2 + k * 1.3)
        lc = Xform(c, ang=sway, px=lx, py=ly)
        lc.line(lx, ly, lx, ly + 22, np.array([70, 58, 44]), 2)
        a = lit[k]
        lc.polygon([(lx - 15, ly + 22), (lx + 15, ly + 22), (lx + 19, ly + 60), (lx - 19, ly + 60)],
                   np.array([46, 46, 42]) + LAMP * 0.85 * a)
        lc.polyline([(lx - 15, ly + 22), (lx + 15, ly + 22), (lx + 19, ly + 60), (lx - 19, ly + 60)],
                    np.array([60, 52, 40]), 3, closed=True)
        lc.line(lx - 18, ly + 22, lx + 18, ly + 22, np.array([60, 52, 40]), 5)
        if a > 0:
            s.glow_draw(lambda g, lx=lx, ly=ly, a=a: g.circle(lx, ly + 41, 46, LAMP * 0.6 * a))
    return rope_y
