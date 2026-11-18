"""Forest Keepers episode 11, Who's Awake Tonight?, in the flat picture-book look: the world (a remake of FK0008, the
approved story: docs/engines/forest_keepers_night_animals.md; staging: docs/engines/forest_keepers_night_flat.md; the
episode itself is night_flat.py).

A moonlit autumn night. We look along the Keepers' forest path from the side: behind it a strip of meadow, the wooded
slope and the far hills under the stars. The walk is six short stretches of the same path (owner, FK0019: no long
walks), one clearing per neighbour, each ZONE px wide; a soft dip into the dark takes them on to the next:

    0  the pond            a natural pond in the meadow, reeds and cattails, stones, lily pads (the raccoon)
    1  the old oak         its long low branch reaching out over the path (the barred owl)
    2  the old log         a round fallen log on the meadow (the opossum and her babies)
    3  two tall trees      side by side, their crowns high up (the flying squirrel glides from one to the other)
    4  the meadow          long grass, the trees thinning out (the red fox)
    5  the forest's edge   the last trees, then open meadow (the deer and her fawn)

Everything here is a pure function of its arguments (no state), so frames render in parallel.
"""
import math

import numpy as np
import skia

from . import harvest_flat_world as HW
from .flat import PAL, bush, hill_band, lolly_tree, pine, poplar, tuft
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H, K, GB = HW.W, HW.H, HW.K, HW.GB
PATH_TOP, FLOOR = HW.PATH_TOP, HW.FLOOR
ZONE = 2400.0
NZ = 6
WORLD = ZONE * NZ + 400.0


def zone_of(x):
    return int(min(NZ - 1, max(0, (x + W / 2) // ZONE)))


def Z(i, dx=0.0):
    return i * ZONE + dx


# the colours (painted in the autumn picture-book palette; the night is a soft multiply over it, as in ep 9's feast)
GRASS, GRASS_D, MEADOW = HW.GRASS, HW.GRASS_D, HW.MEADOW
TRUNK = (112, 84, 66)
TRUNK_D = (92, 68, 54)
BARK = (122, 92, 70)
LOG_END = (206, 168, 122)
LOG_RING = (176, 138, 98)
WATER = (86, 118, 140)
WATER_FAR = (104, 134, 152)
WATER_DEEP = (70, 98, 122)
MUD = (118, 96, 76)
STONE = HW.STONE
REED = (118, 136, 76)
CATTAIL = (124, 84, 56)
LILY = (98, 140, 88)
LILY_FLOWER = (238, 214, 220)
MOON = "#f3ead0"
LIGHT_MUL = (0.84, 0.84, 0.94)          # the night (ep 9's, the owner's "softer night")

# ----------------------------------------------------------------------------------------------- the places

POND = (Z(0, 1440.0), Z(0, 2010.0))     # the pond's ends (its near shore is just behind the path)
POND_NEAR, POND_FAR = 922.0, 842.0     # the water's near and far edges (screen y) at its middle
RACCOON_X = Z(0, 2080.0)               # the raccoon washes its food at the pond's right end (clear of the bush)
                                       # (advisor FK0023 r7: it stood on the water) on the bank past its tip
HIDE = {0: Z(0, 2290.0), 2: Z(2, 1905.0), 4: Z(4, 1850.0)}   # the bushes an animal slips away behind
OAK_X = Z(1, 1720.0)                   # the old oak; its low branch reaches out left over the meadow
OAK_BRANCH = [(OAK_X - 10, 520.0), (OAK_X - 140, 470.0), (OAK_X - 300, 446.0), (OAK_X - 440, 452.0)]
OWL_X = OAK_X - 300.0
OWL_Y = 446.0                          # the top of the branch under the owl's feet
LOG = (Z(2, 1270.0), Z(2, 1740.0))     # the old log's ends
LOG_R = 36.0
LOG_TOP = FLOOR - 2 * LOG_R + 4        # its top (the opossum walks along it)
TREE_A, TREE_B = Z(3, 1230.0), Z(3, 1690.0)   # the flying squirrel's two trees
TRUNK_HW = 30.0
CROWN_Y = 230.0                        # the crowns' middle (high up, into the top of the frame)
FOX_X = Z(4, 1520.0)
DEER_X = Z(5, 1430.0)


def branch_y(x):
    """The top of the oak's low branch at x (between its points)."""
    pts = OAK_BRANCH
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if min(x0, x1) <= x <= max(x0, x1):
            u = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * u
    return pts[-1][1]


# ----------------------------------------------------------------------------------------------- the sky

def sky(pg, t, sh):
    """The night sky: a deep blue gradient, stars that twinkle (fixed to the far sky) and the moon, fixed in each
    clearing (a slow drift with the camera, never a jump within a shot)."""
    top, mid, low = "#17213e", "#2b3a5e", "#3c4a6c"
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.62)], [C(top), C(mid), C(low)], [0, 0.55, 1])
    pg.c.drawPaint(skia.Paint(Shader=g))
    z = zone_of(sh)
    local = sh - Z(z)
    rs = np.random.default_rng(61 + z)
    for _ in range(170):
        x, y = rs.uniform(-200, W + 400), rs.uniform(10, H * 0.42)
        xx = x - local * 0.03
        tw = 0.65 + 0.35 * math.sin(t * rs.uniform(0.6, 1.6) + rs.uniform(0, 6.3))
        r = rs.uniform(1.2, 2.4)
        if -10 < xx < W + 10:
            pg.flat(oval(xx, y, r, r), "#f4ecd2", 0.8 * tw)
    mx, my = W * (0.7 if z % 2 else 0.3) - local * 0.03, H * 0.14
    pg.flat(oval(mx, my, 96, 96), MOON, 0.16, blur=32)
    pg.flat(oval(mx, my, 46, 46), MOON)
    pg.flat(oval(mx - 13, my - 9, 9, 9), tone(MOON, -0.06))
    pg.flat(oval(mx + 15, my + 12, 6, 6), tone(MOON, -0.05))
    pg.grain_opaque()


def apply_light(pg):
    col = skia.Color(*(int(round(255 * m)) for m in LIGHT_MUL))
    pg.c.drawPaint(skia.Paint(Color=col, BlendMode=skia.BlendMode.kMultiply))


# ----------------------------------------------------------------------------------------------- static layers

def _hills(p, y, amp, seed, col, step=520.0):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H, col, 0.05, 0.06)


def _far(p):
    _hills(p, H * 0.44, H * 0.08, 131, PAL["far"], 640.0)


def _far2(p):
    _hills(p, H * 0.49, H * 0.05, 132, PAL["far2"], 560.0)


def _far_trees(p):
    rs = np.random.default_rng(133)
    x = 30.0
    while x < p.strip:
        y = H * 0.52
        if rs.random() < 0.55:
            pine(p, x, y, H * rs.uniform(0.07, 0.095), tone(PAL["pine"], 0.16))
        else:
            lolly_tree(p, x, y, H * rs.uniform(0.065, 0.085), tone((PAL["ochre"], PAL["orange"], PAL["olive"])[
                int(rs.integers(3))], 0.1))
        x += rs.uniform(50, 110)


def _mid(p):
    """The wooded slope behind the meadow: dense in the forest, thinning out towards the forest's edge (zone 5)."""
    rs = np.random.default_rng(134)
    pts = [(x, H * 0.585 + rs.uniform(-12, 12)) for x in np.arange(-200.0, p.strip + 400, 380.0)]
    hill_band(p, pts, H, PAL["mid"], 0.05, 0.05)
    x = 40.0
    while x < p.strip:
        wx = x / 0.4                                                # this layer's px -> world x (its depth is 0.4)
        thin = min(1.0, max(0.0, (wx - Z(5, 600.0)) / 900.0))
        if rs.random() > 0.75 * thin:
            hh = H * rs.uniform(0.15, 0.23)
            col = (PAL["ochre"], PAL["orange"], PAL["pine"], PAL["olive"], PAL["pink"])[int(rs.integers(5))]
            (poplar, lolly_tree, pine)[int(rs.integers(3))](p, x, H * 0.6, hh, col)
        x += rs.uniform(90, 190)


def _trunk(p, x, y0, y1, hw, seed):
    """A tall trunk from the ground (y0) up to y1, a little lean and taper, a few bark lines."""
    rs = np.random.default_rng(seed)
    p.shape(tube([(x, y0 + 4), (x + 4, (y0 + y1) / 2), (x - 3, y1)], hw, hw * 0.75), TRUNK, 0.12, (-0.5, 0.0))
    for q in range(5):
        yy = y0 - 60 - q * (y0 - y1) / 6 + rs.uniform(-20, 20)
        p.stroke(skia.Path().moveTo(x - hw * 0.4, yy).quadTo(x, yy - 14, x + hw * 0.3, yy - 4), TRUNK_D, 3.0, 0.7)


def _oak(p):
    """The old oak: a thick trunk, its long low branch reaching out left (the owl's), a big round crown above."""
    x = OAK_X
    p.shape(tube([(x, FLOOR + 4), (x + 8, 700.0), (x - 6, 330.0)], 54, 36), TRUNK, 0.12, (-0.5, 0.0))
    p.shape(tube(OAK_BRANCH, 17, 9), TRUNK, 0.1, (0.0, -0.4))
    p.shape(tube([(x + 10, 420.0), (x + 160, 330.0), (x + 260, 300.0)], 15, 8), TRUNK, 0.1, (0.0, -0.4))
    for q in range(6):
        yy = FLOOR - 80 - q * 90
        p.stroke(skia.Path().moveTo(x - 30, yy).quadTo(x, yy - 16, x + 26, yy - 4), TRUNK_D, 3.5, 0.7)
    for dx, dy, r, col in ((-170, 210, 170, PAL["olive"]), (40, 150, 190, PAL["ochre"]), (220, 210, 150, PAL["orange"]),
                           (-40, 60, 150, tone(PAL["olive"], 0.05)), (130, 70, 130, tone(PAL["ochre"], -0.05))):
        p.shape(oval(x + dx, dy, r, r * 0.9), col, 0.1)


def _log(p):
    """The old log: round, lying along the meadow, bark on its side, its near cut end showing the rings."""
    a, b, r = LOG[0], LOG[1], LOG_R
    y = FLOOR - r + 2
    p.shape(rrect(a, y - r, b, y + r, r), BARK, 0.12, (0.0, -0.5))
    rs = np.random.default_rng(141)
    for q in range(9):                                              # bark furrows along it
        xq = a + 30 + q * (b - a - 60) / 8 + rs.uniform(-8, 8)
        yy = y + rs.uniform(-r * 0.5, r * 0.5)
        p.stroke(skia.Path().moveTo(xq, yy).lineTo(xq + 34, yy + rs.uniform(-3, 3)), tone(BARK, -0.14), 3.0, 0.8)
    p.flat(oval(b, y, r * 0.42, r), LOG_END)                         # the cut end (seen a little from the side)
    for q in (0.3, 0.55, 0.8):
        p.stroke(oval(b + 1, y, r * 0.42 * q, r * q), LOG_RING, 2.0)
    for q in range(4):                                              # moss and a little mushroom on top
        p.flat(oval(a + 60 + q * 110, y - r + 4, 22, 7), tone(GRASS, -0.1), 0.9)
    p.flat(oval(a + 210, y - r - 6, 9, 5), (214, 170, 140))
    p.flat(rrect(a + 208, y - r - 4, a + 212, y - r + 2, 1), (230, 214, 190))


def _trees_ab(p):
    for j, x in enumerate((TREE_A, TREE_B)):
        _trunk(p, x, FLOOR, CROWN_Y + 80, TRUNK_HW, 150 + j)


def _meadow(p):
    """The near ground: the meadow (from the foot of the wooded slope) down to the bottom of the frame, the path,
    tufts and pebbles; the oak, the log, the two trees' trunks; and grass that grows longer in the fox's meadow."""
    xs = np.arange(-100.0, p.strip + 60, 24.0)
    top = [(x, 660.0 + 10 * math.sin(x / 470.0)) for x in xs]
    p.grad(smooth(top + [(x, H + 10) for x in xs[::-1]]), MEADOW, tone(GRASS, -0.04))
    pa = [(x, PATH_TOP) for x in xs]
    pb = [(x, GB + 34) for x in xs[::-1]]
    p.flat(smooth(pa + pb), PAL["path"], 0.75)
    p.flat(smooth([(x, y + 10) for x, y in pa] + [(x, y - 12) for x, y in pb]), tone(PAL["path"], 0.06), 0.5)
    rs = np.random.default_rng(151)
    for i in range(int(p.strip / 26)):
        x = rs.uniform(0, p.strip)
        y = rs.uniform(700, H)
        if abs(y - GB) < 44 or (POND[0] - 80 < x < POND[1] + 80 and y < PATH_TOP):
            continue
        r = rs.random()
        if r < 0.5:
            tuft(p, x, y, rs.uniform(12, 20), tone(GRASS_D, -0.08))
        elif r < 0.85:
            from .flat import leaf
            leaf(p, x, y, 6.0, rs.uniform(0, 180), (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])
        else:
            p.flat(oval(x, y, 5, 3), tone(STONE, -0.05), 0.8)
    for j, x in enumerate(np.arange(80.0, p.strip, 330.0)):        # the forest along the meadow, between the places
        z = zone_of(x - W / 2)
        lx = x - Z(z)
        busy = {0: (1300, 2400), 1: (1100, 2100), 2: (1150, 2050), 3: (1050, 1900), 4: (1250, 2150), 5: (1100, 2400)}
        if busy[z][0] < lx < busy[z][1] or (z == 5 and lx > 900) or (z == 4 and 700 < lx < 2200):
            continue
        h = 620 + 120 * ((j * 7) % 3)
        xx = x + 40 * math.sin(j * 1.7)
        if j % 3 == 1:
            pine(p, xx, FLOOR - 4, h, tone(PAL["pine"], 0.02))
        else:
            lolly_tree(p, xx, FLOOR - 4, h, (PAL["olive"], PAL["ochre"], PAL["orange"])[j % 3])
    for k in range(70):                                            # the fox's meadow: long grass in clumps
        x = Z(4) + 700 + k * 22 + rs.uniform(-8, 8)
        y = FLOOR + rs.uniform(-30, 12)
        if abs(x - FOX_X) < 120 and y > FLOOR - 10:
            continue
        tuft(p, x, y, rs.uniform(26, 40), tone(GRASS_D, rs.uniform(-0.12, 0.0)))
    _oak(p)
    _log(p)
    _trees_ab(p)
    for x in (Z(5, 1000.0), Z(5, 1160.0)):                         # the last two trees at the forest's edge
        lolly_tree(p, x, FLOOR - 4, 760, PAL["olive"] if x < Z(5, 1100) else PAL["ochre"])


def _fg(p):
    """A few soft ferns and grasses along the bottom edge (nearer than the path)."""
    rs = np.random.default_rng(161)
    x = 80.0
    while x < p.strip:
        y = H + 6
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.32
            L = rs.uniform(60, 90)
            p.stroke(skia.Path().moveTo(x, y).quadTo(x + math.cos(a) * L * 0.5, y + math.sin(a) * L * 0.7,
                                                     x + math.cos(a) * L, y + math.sin(a) * L),
                     tone(GRASS_D, -0.16), 6.0)
        x += rs.uniform(260, 520)


def layers():
    return [("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees), ("mid", 0.4, _mid),
            ("meadow", 1.0, _meadow), ("fg", 1.12, _fg)]


# ----------------------------------------------------------------------------------------------- live: the pond

def pond_edge(u, k=1.0, dy=0.0):
    """A point on the pond's rim (u 0..2pi, seen low from the side: a wide wobbly oval)."""
    cx, rx = (POND[0] + POND[1]) / 2, (POND[1] - POND[0]) / 2
    cy, ry = (POND_NEAR + POND_FAR) / 2, (POND_NEAR - POND_FAR) / 2
    return (cx + rx * k * math.cos(u) * (1 + 0.05 * math.sin(3 * u + 1) + 0.03 * math.sin(7 * u)),
            cy + ry * k * math.sin(u) * (1 + 0.1 * math.sin(5 * u + 2)) + dy)


def draw_pond(pg, t, sh, ripple=None):
    """The pond: a muddy rim, the water (darker in the middle), moonlight glinting, lily pads with a flower, stones;
    ripples round the raccoon's paws (ripple = (x, y, amount))."""
    if not (POND[0] - 200 - sh < W and POND[1] + 200 - sh > 0):
        return
    us = np.linspace(0, 2 * math.pi, 72, endpoint=False)
    rim = smooth([(x - sh, y) for x, y in (pond_edge(u, 1.05, 3) for u in us)])
    pg.flat(rim, MUD)
    water = smooth([(x - sh, y) for x, y in (pond_edge(u) for u in us)])
    b = water.getBounds()
    pg.c.drawPath(water, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, b.top()), (0, b.bottom())], [C(WATER_FAR), C(WATER), C(WATER_DEEP)], [0.0, 0.5, 1.0])))
    pg.c.save()
    pg.c.clipPath(water, doAntiAlias=True)
    cx = (POND[0] + POND[1]) / 2
    for k in range(6):                                              # the moon's glints, drifting slowly
        yy = POND_FAR + 10 + k * 12
        for j in range(5):
            x0 = cx - 220 + j * 100 + 26 * math.sin(t * 0.35 + k * 1.3 + j)
            pg.stroke(skia.Path().moveTo(x0 - sh, yy).lineTo(x0 + 26 + 6 * math.sin(k + j) - sh, yy),
                      tone(WATER, 0.42), 2.2, 0.45 + 0.25 * math.sin(t * 0.8 + k + j * 2))
    if ripple is not None:                                          # (FK0023 r4: big = the clue Hans spots)
        rx, ry, a, big = ripple if len(ripple) > 3 else (*ripple, 0.5)
        for q in range(3):
            ph = (t * 0.55 + q / 3) % 1.0
            pg.stroke(oval(rx - sh, ry, 12 + (46 + 80 * big) * ph, 3 + (7 + 12 * big) * ph), tone(WATER, 0.5 + 0.2 * big),
                      2.0 + 1.2 * big, a * (1 - ph) * 0.9)
    pg.c.restore()
    for j, (lx, ly, r) in enumerate(((cx - 200, POND_FAR + 22, 24), (cx - 120, POND_FAR + 40, 20),
                                     (cx + 120, POND_FAR + 30, 22))):
        p = skia.Path()
        p.addOval(skia.Rect(lx - r - sh, ly - r * 0.32, lx + r - sh, ly + r * 0.32))
        cut = skia.Path().moveTo(lx - sh, ly).lineTo(lx + r * 1.2 - sh, ly - 4).lineTo(lx + r * 1.2 - sh, ly + 5)
        cut.close()
        p = skia.Op(p, cut, skia.PathOp.kDifference_PathOp)
        pg.flat(p, tone(LILY, 0.04 * j))
        if j == 0:
            pg.flat(oval(lx - 6 - sh, ly - 6, 7, 5), LILY_FLOWER)
            pg.flat(oval(lx - 6 - sh, ly - 7, 3, 2.4), (246, 220, 150))
    for sx, sy, r in ((POND[0] + 30, POND_NEAR - 6, 18), (POND[0] + 70, POND_NEAR + 2, 13),
                      (POND[1] - 120, POND_NEAR + 1, 15)):                       # stones on the near shore
        pg.shape(oval(sx - sh, sy, r * 1.3, r * 0.7), tone(STONE, -0.04), 0.14)


def draw_reeds(pg, t, sh):
    """Reeds and cattails at the pond's left end and behind its right end, swaying a little."""
    if not (POND[0] - 200 - sh < W and POND[1] + 260 - sh > 0):
        return
    rs = np.random.default_rng(171)
    for base0, n in ((POND[0] - 40, 16), (POND[1] - 70, 9)):
        for j in range(n):
            bx = base0 + j * 9 + rs.uniform(-3, 3)
            by = POND_NEAR - 4 + rs.uniform(-30, 4)
            h = 90 + 50 * rs.random()
            sw = 5 * math.sin(t * 0.8 + j * 0.7 + bx * 0.01)
            p = skia.Path().moveTo(bx - sh, by).quadTo(bx + sw * 0.4 - sh, by - h * 0.5, bx + sw - sh, by - h)
            pg.stroke(p, tone(REED, rs.uniform(-0.1, 0.06)), 3.2)
            if j % 3 == 0:
                pg.flat(rrect(bx + sw - 4.5 - sh, by - h + 6, bx + sw + 4.5 - sh, by - h + 32, 4.5), CATTAIL)


# ----------------------------------------------------------------------------------------------- live: the rest

def draw_hide_bush(pg, x, sh):
    """A round bush at the back of the path that an animal slips away behind (drawn over it)."""
    if -300 < x - sh < W + 300:
        bush(pg, x - sh, FLOOR + 22, 112, tone(PAL["olive"], -0.08))
        bush(pg, x + 70 - sh, FLOOR + 30, 78, tone(PAL["olive"], -0.02))


def draw_crowns(pg, sh):
    """The squirrel's two trees' crowns: in front of it when it climbs up into one."""
    for j, x in enumerate((TREE_A, TREE_B)):
        if -400 < x - sh < W + 400:
            for dx, dy, r, col in ((-120, 40, 150, PAL["olive"]), (90, 20, 160, PAL["ochre"]),
                                   (0, -60, 150, tone(PAL["olive"], 0.06)), (-40, 120, 110, tone(PAL["ochre"], -0.06))):
                pg.shape(oval(x + dx * (1 if j else -1) - sh, CROWN_Y + dy, r, r * 0.9), col, 0.1)


def fireflies(pg, t, sh, amount, x0, x1, n=40, y0=520.0, y1=900.0, seed=77):
    if amount <= 0:
        return
    rs = np.random.default_rng(seed)
    for _ in range(n):
        bx, by = rs.uniform(x0, x1), rs.uniform(y0, y1)
        ph, sp = rs.uniform(0, 6.3), rs.uniform(0.15, 0.4)
        x = bx + 60 * math.sin(t * sp + ph)
        y = by + 30 * math.sin(t * sp * 1.7 + ph * 2)
        a = (0.5 + 0.5 * math.sin(t * 1.3 + ph * 3)) * amount
        sx = x - sh
        if -20 < sx < W + 20:
            pg.flat(oval(sx, y, 9, 9), "#d8f08a", 0.18 * a, blur=5)
            pg.flat(oval(sx, y, 2.4, 2.4), "#eefcb0", 0.8 * a)
