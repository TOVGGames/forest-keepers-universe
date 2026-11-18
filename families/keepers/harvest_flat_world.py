"""Forest Keepers episode 9, The Harvest Feast, in the flat picture-book look: the world (a remake of FK0005; staging:
docs/engines/forest_keepers_harvest_flat.md; the episode itself is harvest_flat.py).

We look along the Keepers' path from the side. Behind the path a strip of meadow, then (on the left) the brook with
the old water wheel, and the autumn hills. Left to right:

    the old oak (the squirrel, the acorns)      x ~ 250
    the water wheel in the brook                 x ~ 820, its brake post on the bank
    the mill (built in the episode)              x 1180-1460: two posts, beams, a roof, two millstones turning in
    the saw rack + the wood pile                 x 1690-1890 (Twigs trims at the notch)
    ... the path along the brook, which bends away behind the bushes ...
    the oven (built: stones and clay)            x ~ 3600
    the long table (built: planks on two logs)   x 4000-4900, in FRONT of the path (the Keepers stand behind it)
    the animals' houses                           x 5200-5900 (birdhouses on posts, the hedgehog's, the bunnies')

The day goes from a golden afternoon (the mill) through sunset (the walk) and dusk (the oven, the table) to night
(the feast, lanterns and fireflies). World x is the ground layer's own px; everything here is a pure function of its
arguments (no state), so frames render in parallel.
"""
import math

import numpy as np
import skia

from .flat import PAL, bush, cloud, hill_band, lolly_tree, pine, poplar, treehouse, tuft
from .storybook import C, mix, oval, rrect, smooth, tone, tube

W, H = 1920, 1080
K = 0.72
GB = 960.0                         # the Keepers' feet on the path
PATH_TOP = 930.0
FLOOR = 905.0                      # the meadow line things behind the path stand on (the mill, the oven, houses)
COLS = {"wheels": (64, 112, 196), "tentacles": (224, 112, 30), "teeth": (138, 76, 196), "springs": (214, 166, 40),
        "lantern": (40, 170, 158), "digger": (200, 74, 54)}
WORLD = 7600.0


def _ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ground(x):
    return GB


# ----------------------------------------------------------------------------------------------- the brook

BROOK_END = 2900.0                 # the brook bends away behind the bushes here
FAR0, NEAR0 = 646.0, 726.0


def far_edge(x):
    return FAR0 + 26.0 * _ss((x - 2300.0) / (BROOK_END - 2300.0))


def near_edge(x):
    return NEAR0 - 54.0 * _ss((x - 2300.0) / (BROOK_END - 2300.0))


def water_y(x):
    """The middle of the water (where the wheel's paddles dip, where the millstones lie in the shallows)."""
    return (far_edge(x) + near_edge(x)) / 2


WATER_C = (112, 146, 164)
WATER_FAR = (138, 168, 178)
WATER_DEEP = (96, 128, 148)
FOAM = (232, 238, 234)
STONE = (150, 140, 128)
STONE_D = (118, 110, 102)
MILLSTONE = (168, 160, 150)
MILLSTONE_D = (138, 130, 122)
WOOD = (176, 132, 90)
WOOD_D = (146, 106, 72)
WOOD_END = (222, 186, 138)
WOOD_RING = (180, 138, 96)
POLE = (150, 112, 80)
ROOF = (160, 104, 82)
GRASS = (152, 160, 92)
GRASS_D = (128, 138, 78)
MEADOW = (170, 172, 104)
GRAVEL = (196, 178, 140)
EARTH = (150, 116, 86)
CLAY = (176, 132, 104)
CLAY_SOFT = (164, 116, 92)
TRUNK = (128, 96, 72)
ACORN = (170, 116, 62)
ACORN_CAP = (120, 92, 60)
FLOUR = (246, 236, 214)
SACK = (214, 190, 150)
TWINE = (150, 74, 50)               # r13: a red-brown cord (the old twine was the sack's own colour: unseen)
BREAD = (214, 160, 92)
BREAD_DOUGH = (236, 216, 180)
LAMP = "#ffd890"


# ----------------------------------------------------------------------------------------------- sky + light

LIGHT = [(0.0, "gold")]
PRESETS = {      # sky top, mid, low; light multiplier; sun (alpha, x, y as fractions of the frame); stars
    "gold": ("#a9b6c8", "#f0d8bc", "#f4bf96", (1.02, 0.97, 0.9), (0.85, 0.82, 0.3), 0.0),
    "sunset": ("#8f94b4", "#e6b2a0", "#f2a878", (0.97, 0.88, 0.84), (0.9, 0.9, 0.52), 0.0),
    "dusk": ("#4e5a86", "#a28aa4", "#d9a08a", (0.84, 0.8, 0.88), (0.0, 0.9, 0.7), 0.35),
    "night": ("#17213e", "#2b3a5e", "#3c4a6c", (0.5, 0.54, 0.74), (0.0, 0.9, 0.7), 1.0),   # r29 (round 29 part 3: close shots read as day)
}


def light_at(t):
    keys = LIGHT
    if t <= keys[0][0] or len(keys) == 1:
        return keys[0][1], keys[0][1], 0.0
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return a, b, _ss((t - t0) / max(t1 - t0, 1e-6))
    return keys[-1][1], keys[-1][1], 0.0


def darkness(t):
    """0 in daylight .. 1 at night (lamps, windows and fireflies show up with it)."""
    a, b, u = light_at(t)
    return PRESETS[a][5] + (PRESETS[b][5] - PRESETS[a][5]) * u


def sky(pg, t, sh):
    a, b, u = light_at(t)
    A, B = PRESETS[a], PRESETS[b]
    top, mid, low = (mix(A[i], B[i], u) for i in range(3))
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.62)], [C(top), C(mid), C(low)], [0, 0.55, 1])
    pg.c.drawPaint(skia.Paint(Shader=g))
    sa, sx, sy = (p + (q - p) * u for p, q in zip(A[4], B[4]))
    if sa > 0.02:
        r = 44.0
        pg.glow(W * sx, H * sy, r * 7, "#ffe2a8", 0.45 * sa)
        pg.flat(oval(W * sx, H * sy, r, r), "#fff2d2", sa)
    st = darkness(t)
    if st > 0.02:                                                  # stars and the moon, fixed to the far sky
        rs = np.random.default_rng(61)
        for _ in range(160):
            x, y = rs.uniform(-200, W + 600), rs.uniform(10, H * 0.42)
            xx = (x - sh * 0.04) % (W + 400) - 200
            tw = 0.65 + 0.35 * math.sin(t * rs.uniform(0.6, 1.6) + rs.uniform(0, 6.3))
            r = rs.uniform(1.2, 2.4)
            pg.flat(oval(xx, y, r, r), "#f4ecd2", 0.8 * tw * st)
        mx, my = W * 0.22 - sh * 0.04 % 400, H * 0.16
        pg.flat(oval(mx, my, 90, 90), "#f3ead0", 0.18 * st, blur=30)
        pg.flat(oval(mx, my, 44, 44), "#f3ead0", st)
        pg.flat(oval(mx - 12, my - 8, 9, 9), tone("#f3ead0", -0.06), st)
    pg.grain_opaque()


def light_mul(t):
    a, b, u = light_at(t)
    return np.array([p + (q - p) * u for p, q in zip(PRESETS[a][3], PRESETS[b][3])], np.float32)


def apply_light(pg, t):
    mul = light_mul(t)
    if np.allclose(mul, 1.0):
        return
    col = skia.Color(*(int(round(255 * min(1.0, float(m)))) for m in mul))
    pg.c.drawPaint(skia.Paint(Color=col, BlendMode=skia.BlendMode.kMultiply))
    if mul.max() > 1.0:                                            # a warm afternoon: a touch brighter in red
        pass


# ----------------------------------------------------------------------------------------------- static layers

def _hills(p, y, amp, seed, col, step=520.0, light_=0.05, dark=0.06):
    rs = np.random.default_rng(seed)
    xs = np.arange(-200.0, p.strip + step, step)
    pts = [(x + rs.uniform(-80, 80), y - amp * rs.uniform(0.2, 1.0)) for x in xs]
    return hill_band(p, pts, H, col, light_, dark)


def _clouds(p):
    rs = np.random.default_rng(21)
    x = 120.0
    while x < p.strip:
        cloud(p, x, H * rs.uniform(0.08, 0.2), W * rs.uniform(0.1, 0.16))
        x += rs.uniform(420, 760)


def _far(p):
    _hills(p, H * 0.42, H * 0.08, 31, PAL["far"], 640.0)


def _far2(p):
    _hills(p, H * 0.47, H * 0.05, 32, PAL["far2"], 560.0)


def _far_trees(p):
    rs = np.random.default_rng(33)
    x = 30.0
    while x < p.strip:
        y = H * 0.5
        if rs.random() < 0.5:
            pine(p, x, y, H * rs.uniform(0.06, 0.085), tone(PAL["pine"], 0.2))
        else:
            lolly_tree(p, x, y, H * rs.uniform(0.06, 0.08), tone((PAL["ochre"], PAL["orange"], PAL["olive"])[
                int(rs.integers(3))], 0.15))
        x += rs.uniform(60, 130)


def _mid(p):
    """The wooded slope behind the brook and the village."""
    rs = np.random.default_rng(34)
    pts = [(x, H * 0.55 + rs.uniform(-12, 12)) for x in np.arange(-200.0, p.strip + 400, 380.0)]
    hill_band(p, pts, H, PAL["mid"], 0.05, 0.05)
    x = 40.0
    while x < p.strip:
        y = H * 0.565
        kind = rs.integers(3)
        hh = H * rs.uniform(0.13, 0.2)
        col = (PAL["ochre"], PAL["orange"], PAL["pine"], PAL["olive"], PAL["pink"])[int(rs.integers(5))]
        (poplar, lolly_tree, pine)[int(kind)](p, x, y, hh, col)
        x += rs.uniform(110, 230)


def _far_bank(p):
    """The bank across the brook (left) and the grass behind the village (right), up to the wood."""
    xw = np.arange(-300.0, p.strip + 60, 30.0)
    top = [(x, far_edge(x) - 48 - 10 * math.sin(x / 530.0)) for x in xw]
    edge = [(x, far_edge(x) + 2) for x in xw[::-1]]
    p.grad(smooth(top + edge), tone(MEADOW, 0.04), tone(GRASS_D, -0.02))
    rs = np.random.default_rng(41)
    for x in np.arange(-200.0, min(p.strip, BROOK_END), 34.0):    # stones along the far water's edge
        xx = x + rs.uniform(-8, 8)
        r = rs.uniform(10, 18)
        p.shape(oval(xx, far_edge(xx) - 3, r, r * 0.5), tone(STONE, rs.uniform(-0.08, 0.06)), 0.12)
    for x in (120.0, 1900.0, 2700.0, 3300.0, 6100.0, 6900.0):     # a few trees on the far side
        y = far_edge(x) - 40
        if x in (1900.0, 3300.0):
            pine(p, x, y, 300, tone(PAL["pine"], 0.04))
        else:
            lolly_tree(p, x, y, 330, (PAL["orange"], PAL["ochre"])[int(x) % 2])


OAK_X = 240.0                      # the old oak (the squirrel's; Springs shakes the acorns off its low branch)
OAK_Y = 905.0
OAK_BRANCH = [(OAK_X + 12, OAK_Y - 330), (OAK_X + 150, OAK_Y - 372), (OAK_X + 330, OAK_Y - 392)]


def _oak(p):
    x, y = OAK_X, OAK_Y
    p.shape(tube([(x, y), (x + 6, y - 260), (x - 6, y - 470)], 40, 24), TRUNK, 0.12, (-0.5, 0.0))
    p.shape(tube(OAK_BRANCH[:2], 15, 9), TRUNK, 0.1, (0.0, -0.4))
    for dx, dy, r, col in ((-120, -540, 140, PAL["olive"]), (40, -590, 150, PAL["ochre"]),
                           (-40, -680, 120, tone(PAL["olive"], 0.06)), (130, -520, 100, tone(PAL["ochre"], -0.04)),
                           (-200, -450, 90, PAL["orange"])):
        p.shape(oval(x + dx, y + dy, r, r * 0.92), col, 0.1)
    rs = np.random.default_rng(5)
    for _ in range(14):                                         # acorns in the crown
        ax, ay = x + rs.uniform(-200, 180), y + rs.uniform(-700, -460)
        draw_acorn(p, ax, ay, 0.8, rs.uniform(-20, 20))


# where things stand on the meadow
WX, WY, WR = 820.0, 520.0, 170.0   # the water wheel's axle and radius (the paddles dip into the brook)
WHEEL_PULLEY_R = 40.0
BRAKE_X = 1035.0                   # the brake post on the bank: a peg in its top holds the rope round the wheel
BRAKE_TOP = 840.0                  # r13: lower (800 was past Springs' reach: the peg jumped to his hand)
PL, PR = 1140.0, 1555.0            # r46 (round 45 part 1 must-fix "gear 1's left teeth run into post 1": 1180 -> 1140, its
                                   # tooth tips now clear the post by ~10 px) the mill's two posts (their holes; r31: right one 1555, was 1460, round 30 part 1
                                   # must-fix "the post runs across gear 2's face": both gears now clear of the posts)
POST_TOP = 500.0
BEAM_Y = 488.0                     # the top beam (its top), the roof sits on it
AXLE_BEAM_Y = 734.0                # the low beam behind the stones (their axles rest in it)
STONES = [(1250.0, 745.0), (1390.0, 745.0)]
STONE_R = 68.0                     # r16 (part 1 must-fix "they don't touch: they can't grind"): the two rollers all but touch at the nip
GEAR_R = 88.0                      # r33: 88 (teeth showing past the stones). Was: GEAR_R = 80.0                      # (r28: 86 -> 80, see BLANK) the gear blanks' half side (r27 part 2 must-fix "the gears hide behind the stones": 70 -> 86,
                                   # bigger than the stones, their teeth seen all round them); their axles 140 apart, they mesh deep
PULLEY_R = 26.0
NIP_X = 1320.0
HOPPER = [((1238.0, 502.0), (1310.0, 668.0)), ((1402.0, 502.0), (1330.0, 668.0))]   # pegged to the beam at
                                    # their top ends (r2 review: the old V floated under the beam)
SACK_X = 1320.0
ROOF_L = ((1107.5, 500.0), (1347.5, 392.0))   # r46: 20 px left with the left post (its middle again at (PL + PR) / 2)
#    # (r31: over the wider frame, on the top beam's ends: its middle at
ROOF_R = ((1347.5, 392.0), (1587.5, 500.0))   # (PL + PR) / 2, 480 long; was 1090-1320-1550)
STOP_X = 1711.0                    # the saw rack: pieces lie against the stop block... (r33, round 32 part 2
                                   # must-fix "Twigs saws air": 1711, was 1690 - a hopper board against it ended 3 px short of
                                   # the notch; now it runs 18 px past it, so the blade cuts wood and the offcut is that end)
NOTCH_X = 1892.0                   # ...and Twigs trims them at the notch
RACK_Y = 852.0                     # the rack's top
PILE = (1700.0, 1880.0)            # the wood pile behind the rack
IN_BROOK = [(1160.0, 708.0), (1045.0, 674.0)]   # r34 (round 33 must-fixes: a lumpy slab, cut square by the brook's
                                                 # front band, and a long stretch into the water for the far one): apart, in the
                                                 # (the far one at x 1045 as before: further left Hans' stand for it ran into Digs)
                                                 # near half of the shallows, water lapping their rims. r31: left of the left post, the near one first (with the right post
                                                 # at 1555 there's no room out right before Twigs) (r23: the far one first (r24: 50 further out, so they show
                                                 # above the gears while they're named)   # the two round stones lying in the shallows
BASKET_HOME = (560.0, 902.0)       # the acorn basket under the oak

# the village
OVEN_X = 3580.0
OVEN_W = 180.0
OVEN_H = 210.0
CLAY_X = 3180.0                    # Digs digs the clay here
TABLE = (3980.0, 4700.0)           # the long table, in front of the path (the Keepers stand behind it)
TABLE_FRONT = 958.0                # its top's front edge; its back edge is 70 px up (the oblique view)
PLANK_W = (TABLE[1] - TABLE[0]) / 6
FRACK = (4700.0, 4942.0)           # the saw rack by the table's end, also in front of the path
HEDGE_X, BUNNY_X = 2700.0, 2880.0  # the animals' houses, left of the oven
HEDGE_HOUSE = (150.0, 120.0, 70.0, 38.0)   # width, height, roof, door radius: the hedgehog fits in its doorway
BUNNY_HOUSE = (190.0, 150.0, 80.0, 40.0)   # ...and a bunny, ears and all (owner, FK0021: they came out through the
                                           # walls, half in the house and half out)


def house_door(x, sh, door_r, y=FLOOR):
    """The door opening of a cottage at x (screen units)."""
    X = x - sh
    return rrect(X - door_r, y - door_r * 2.1, X + door_r, y, door_r)
BIRD_POSTS = [3300.0, 3380.0, 5400.0, 5500.0]
BIRD_POST_TOP = 560.0
TREEHOUSE_X = 5900.0
LANTERNS = [(3960.0, 640.0), (4320.0, 600.0), (4660.0, 640.0)]  # on poles behind the table: (x, lamp y)


def _meadow(p):
    """The near ground: from the water's near edge (or the far grass) down to the bottom of the frame, the path."""
    xs = np.arange(-100.0, p.strip + 60, 24.0)
    edge = [(x, near_edge(x) - 1) for x in xs]
    bottom = [(x, H + 10) for x in xs[::-1]]
    p.grad(smooth(edge + bottom), MEADOW, tone(GRASS, -0.04))
    rs = np.random.default_rng(51)
    xb = np.arange(-100.0, BROOK_END - 100, 24.0)
    p.flat(smooth([(x, near_edge(x) - 1) for x in xb] + [(x, near_edge(x) + 14) for x in xb[::-1]]),
           tone(GRAVEL, -0.12), 0.9)
    for x in np.arange(0.0, BROOK_END - 150, 28.0):              # wet stones along the water's edge
        xx = x + rs.uniform(-6, 6)
        r = rs.uniform(9, 15)
        p.shape(oval(xx, near_edge(xx) + 4, r, r * 0.45), tone(STONE, rs.uniform(-0.12, 0.02)), 0.12)
    for bx, r in ((2780.0, 120.0), (2920.0, 150.0), (3060.0, 110.0)):   # the bushes the brook bends away behind
        bush(p, bx, near_edge(bx) + 30, r, tone(PAL["olive"], -0.06))
    top = [(x, PATH_TOP) for x in xs]
    bot = [(x, GB + 34) for x in xs[::-1]]
    p.flat(smooth(top + bot), PAL["path"], 0.75)
    p.flat(smooth([(x, y + 10) for x, y in top] + [(x, y - 12) for x, y in bot]), tone(PAL["path"], 0.06), 0.5)
    for i in range(int(p.strip / 30)):                          # tufts, leaves, pebbles (not where things get built)
        x = rs.uniform(0, p.strip)
        y = rs.uniform(near_edge(x) + 22, H)
        if abs(y - GB) < 44 or (1080 < x < 1960 and y < PATH_TOP) or (3400 < x < 3800 and y < PATH_TOP) or \
                (TABLE[0] - 60 < x < FRACK[1] + 40 and y > GB):
            continue
        r = rs.random()
        if r < 0.45:
            tuft(p, x, y, rs.uniform(12, 20), tone(GRASS_D, -0.08))
        elif r < 0.85:
            from .flat import leaf
            leaf(p, x, y, 6.0, rs.uniform(0, 180), (PAL["orange"], PAL["ochre"], PAL["pink"])[i % 3])
        else:
            p.flat(oval(x, y, 5, 3), tone(STONE, -0.05), 0.8)
    _oak(p)
    treehouse(p, TREEHOUSE_X, FLOOR - 10, 1000)
    for x in BIRD_POSTS:                                         # the birds' posts (their houses are drawn live)
        p.shape(rrect(x - 11, BIRD_POST_TOP, x + 11, FLOOR + 6, 4), TRUNK, 0.08)
    for x in (TABLE[0] - 10, (TABLE[0] + TABLE[1]) / 2, TABLE[1] + 10):   # the lantern poles behind the table
        pass


def _fg(p):
    """A few soft ferns and grasses along the bottom edge (nearer than the path); none in front of the table."""
    rs = np.random.default_rng(61)
    x = 80.0
    while x < p.strip:
        if not (TABLE[0] - 200 < x < FRACK[1] + 200):
            y = H + 6
            for k in range(5):
                a = -math.pi / 2 + (k - 2) * 0.32
                L = rs.uniform(60, 90)
                p.stroke(skia.Path().moveTo(x, y).quadTo(x + math.cos(a) * L * 0.5, y + math.sin(a) * L * 0.7,
                                                         x + math.cos(a) * L, y + math.sin(a) * L),
                         tone(GRASS_D, -0.16), 6.0)
        x += rs.uniform(260, 520)


def layers():
    return [("clouds", 0.03, _clouds), ("far", 0.08, _far), ("far2", 0.14, _far2), ("far_trees", 0.2, _far_trees),
            ("mid", 0.4, _mid), ("far_bank", 1.0, _far_bank), ("meadow", 1.0, _meadow), ("fg", 1.12, _fg)]


# ----------------------------------------------------------------------------------------------- the brook, live

def draw_water(pg, t, sh, flow=110.0):
    x0, x1 = sh - 200, min(sh + W + 60, BROOK_END + 40)
    if x1 <= x0:
        return
    xw = np.arange(x0, x1 + 16, 16.0)
    band = smooth([(x - sh, far_edge(x) - 2) for x in xw] + [(x - sh, near_edge(x) + 4) for x in xw[::-1]])
    b = band.getBounds()
    pg.c.drawPath(band, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, b.top()), (0, b.bottom())], [C(WATER_FAR), C(WATER_C), C(WATER_DEEP)], [0.0, 0.6, 1.0])))
    pg.c.save()
    pg.c.clipPath(band, doAntiAlias=True)
    for row in range(4):                                         # streaks drifting downstream, each in its own cell
        spacing = 130.0 + 23 * row
        for k in range(int(math.floor(x0 / spacing)), int(x1 / spacing) + 1):
            base = k * spacing
            ph = (flow * t * 0.9 / spacing + 0.37 * k + 0.29 * row) % 1.0
            x = base + ph * spacing
            a = math.sin(math.pi * ph)
            if a < 0.05:
                continue
            fy = far_edge(x) + (row + 0.6) / 4.3 * (near_edge(x) - far_edge(x))
            y = fy + 1.5 * math.sin(x * 0.03 + t * 3)
            ln = 18 + 5 * row
            pg.stroke(skia.Path().moveTo(x - sh, y).lineTo(x - sh + ln, y), tone(WATER_C, 0.32), 2.2, 0.7 * a)
    pg.c.restore()


def draw_brook_front(pg, t, sh):
    """The near half of the water again, over the wheel's lower paddles (they dip into it), with a ripple line."""
    x0, x1 = max(sh - 50, WX - WR - 60), min(sh + W + 50, WX + WR + 60)
    if x1 <= x0:
        return
    xw = np.arange(x0, x1 + 8, 8.0)
    surf = [(x - sh, water_y(x) - 6 + 1.5 * math.sin(x * 0.05 + t * 2.5)) for x in xw]
    band = smooth(surf + [(x - sh, near_edge(x) + 4) for x in xw[::-1]])
    pg.flat(band, mix(WATER_C, WATER_DEEP, 0.4), 0.96)
    p = skia.Path()
    for i, (x, y) in enumerate(surf):
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    pg.stroke(p, tone(WATER_C, 0.3), 2.0, 0.6)


# ----------------------------------------------------------------------------------------------- small things

def draw_acorn(pg, x, y, s=1.0, ang=0.0, a=1.0):
    p = oval(x, y + 3 * s, 7 * s, 9 * s, ang)
    pg.shape(p, ACORN, 0.12) if a >= 1 else pg.flat(p, ACORN, a)
    cap = rrect(x - 8 * s, y - 7 * s, x + 8 * s, y + 1 * s, 4 * s)
    if ang:
        cap.transform(skia.Matrix.RotateDeg(ang, (x, y + 3 * s)))
    pg.flat(cap, ACORN_CAP, a)


def draw_basket(pg, x, y, tilt=0.0, acorns=0, sh=0.0, seed=0):
    """A round woven basket; (x, y) the middle of its bottom. tilt (deg) tips it (pouring)."""
    c = pg.c
    c.save()
    c.rotate(tilt, x - sh, y - 26)
    X = x - sh
    rs = np.random.default_rng(seed)
    for i in range(acorns):                                      # the acorns heaped in it (behind its front)
        ax = X + (i % 5 - 2) * 11 + rs.uniform(-2, 2)
        ay = y - 44 - (i // 5) * 9 + rs.uniform(-2, 2)
        draw_acorn(pg, ax, ay, 0.85, rs.uniform(-30, 30))
    body = smooth([(X - 42, y - 46), (X + 42, y - 46), (X + 32, y), (X - 32, y)])
    pg.shape(body, (196, 150, 96), 0.12)
    for q in range(3):
        yy = y - 40 + q * 13
        pg.stroke(skia.Path().moveTo(X - 40 + q * 3, yy).lineTo(X + 40 - q * 3, yy), (160, 116, 70), 2.0, 0.8)
    pg.flat(rrect(X - 46, y - 52, X + 46, y - 42, 5), (176, 130, 80))
    c.restore()


def draw_pole(pg, x0, y0, x1, y1, sh, w=13.0, col=POLE):
    """A straight pole (a post, a beam) from (x0, y0) to (x1, y1), its cut ends lighter."""
    path = tube([(x0 - sh, y0), (x1 - sh, y1)], w, w)
    pg.shape(path, col, 0.1, (0.0, -0.4))
    pg.stroke(path, tone(col, -0.35), 1.6, 0.85)                  # an edge, so which pole is in front reads


def board_path(cx, cy, L, ang, th=12.0):
    p = rrect(cx - L / 2, cy - th / 2, cx + L / 2, cy + th / 2, 3)
    if ang:
        p.transform(skia.Matrix.RotateDeg(ang, (cx, cy)))
    return p


def draw_board(pg, cx, cy, L, ang, sh, th=12.0, col=WOOD, peg=0):
    """A sawn board seen edge-on: (cx, cy) its middle. peg -1/+1: a wooden peg through it 8 px in from that end."""
    pg.shape(board_path(cx - sh, cy, L, ang, th), col, 0.1)
    a = math.radians(ang)
    if peg:
        px, py = cx - sh + peg * (L / 2 - 8.0) * math.cos(a), cy + peg * (L / 2 - 8.0) * math.sin(a)
        pg.flat(oval(px, py, 4.6, 4.6), tone(WOOD, -0.45))
        pg.flat(oval(px - 0.8, py - 0.8, 2.6, 2.6), WOOD_END)
    for s_ in (-1, 1):                                            # the sawn ends, a lighter line
        ex, ey = cx - sh + s_ * L / 2 * math.cos(a), cy + s_ * L / 2 * math.sin(a)
        pg.stroke(skia.Path().moveTo(ex - th / 2 * math.sin(-a), ey - th / 2 * math.cos(a))
                  .lineTo(ex + th / 2 * math.sin(-a), ey + th / 2 * math.cos(a)), WOOD_END, 2.0, 0.8)


def draw_log(pg, x0, x1, y, sh, r=16.0, col=WOOD, end_r=True):
    """A log lying along x (y its middle), its right end cut (rings)."""
    pg.shape(rrect(x0 - sh, y - r, x1 - sh, y + r, r * 0.6), col, 0.1)
    if end_r:
        pg.flat(oval(x1 - sh - 2, y, r * 0.45, r * 0.98), WOOD_END)
        pg.stroke(skia.Path().addOval(skia.Rect(x1 - sh - 2 - r * 0.22, y - r * 0.5, x1 - sh - 2 + r * 0.22,
                                                y + r * 0.5)), WOOD_RING, 1.4, 0.8)


def groove_line(X, y, a0, g, r=STONE_R):
    """Groove g's two ends (the eye's edge, near the rim) on a millstone at (X, y) turned a0 (rad): cut clockwise
    round the stone (r33: it is turned clockwise between grooves, so each is cut at the same spot under Digs' claw;
    r8 was anticlockwise), each slanting a little (r3)."""
    a = a0 - g * math.pi / 3
    return ((X + math.cos(a) * 14.0, y + math.sin(a) * 14.0),
            (X + math.cos(a + 0.25) * (r - 8.0), y + math.sin(a + 0.25) * (r - 8.0)))


def draw_stone(pg, x, y, ang, sh, grooves=6, hole=1.0, wet=0.0, r=STONE_R):
    """A round millstone seen face on: (x, y) its middle, turned by ang (deg). Dressed: `grooves` of its six grooves
    cut (each a little furrow from the eye outwards), hole 0..1 the eye cut through."""
    X = x - sh
    pg.shape(oval(X, y, r, r), MILLSTONE, 0.12)
    pg.stroke(skia.Path().addOval(skia.Rect(X - r + 4, y - r + 4, X + r - 4, y + r - 4)), MILLSTONE_D, 2.0, 0.5)
    a0 = math.radians(ang)
    for pa, pr, ps in ((0.6, 0.62, 5.0), (2.3, 0.45, 3.8), (3.4, 0.78, 4.4), (4.6, 0.3, 3.2), (5.5, 0.7, 4.2)):
        pg.flat(oval(X + math.cos(a0 + pa) * r * pr, y + math.sin(a0 + pa) * r * pr, ps, ps * 0.85), MILLSTONE_D, 0.85)
        # (r14: a few pits in the stone, so it can be seen turning; r26 part 1 must-fix "the speckles stay put while
        # the grooves swing round": bigger, plus two pale flecks, all turning with it)
    for pa, pr, ps in ((1.4, 0.58, 4.0), (4.0, 0.66, 3.4)):
        pg.flat(oval(X + math.cos(a0 + pa) * r * pr, y + math.sin(a0 + pa) * r * pr, ps * 1.3, ps), (226, 220, 210), 0.7)
    for g in range(6):
        u = min(max(grooves - g, 0.0), 1.0)
        if u <= 0:
            continue
        (x0, y0), (x1, y1) = groove_line(X, y, a0, g, r)          # r26: it grows along its own line (it swung
        pg.stroke(skia.Path().moveTo(x0, y0).lineTo(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u), MILLSTONE_D, 4.0, 0.9)
    if hole > 0:
        pg.flat(oval(X, y, 11 * hole, 11 * hole), (86, 78, 72))
    if wet > 0:
        pg.flat(oval(X, y, r, r), (90, 110, 130), 0.25 * wet)


def gear_path(X, y, ang, r, teeth, cut=None, face=1.0):
    """A wooden gear (cogs on its rim): cut = how many of its `teeth` gaps have been notched so far."""
    n = teeth
    cut = n if cut is None else cut
    p = skia.Path()
    steps = n * 8
    a0 = math.radians(ang)
    pts = []
    for i in range(steps):
        a = a0 + 2 * math.pi * i / steps
        q = (i % 8)
        k = i // 8
        notched = k < cut
        rr = r + (8.0 if (q < 4 or not notched) else 0.0)
        pts.append((X + math.cos(a) * rr * face, y + math.sin(a) * rr))
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def draw_gear(pg, x, y, ang, sh, r=GEAR_R, teeth=16, cut=None, face=1.0, col=WOOD):
    X = x - sh
    if face < 0.12:                                               # edge on: a thin slice
        pg.shape(rrect(X - 9, y - r - 6, X + 9, y + r + 6, 4), col, 0.1)
        return
    pg.shape(gear_path(X, y, ang, r - 4, teeth, cut, face), col, 0.12)
    pg.flat(oval(X, y, (r - 14) * face, r - 14), WOOD_END, 0.9)
    for q in range(3):
        rr = (r - 22 - 10 * q)
        if rr > 4:
            pg.stroke(skia.Path().addOval(skia.Rect(X - rr * face, y - rr, X + rr * face, y + rr)), WOOD_RING, 1.4,
                      0.7)
    pg.flat(oval(X, y, 8 * face, 8), (96, 70, 50))


def draw_pulley(pg, x, y, ang, sh, r=PULLEY_R, col=WOOD_D):
    X = x - sh
    pg.shape(oval(X, y, r, r), col, 0.1)
    pg.flat(oval(X, y, r - 6, r - 6), tone(col, 0.12))
    a = math.radians(ang)
    for q in range(3):                                            # three spokes, so you see it turn
        b = a + q * 2 * math.pi / 3
        pg.stroke(skia.Path().moveTo(X, y).lineTo(X + math.cos(b) * (r - 6), y + math.sin(b) * (r - 6)), col, 3.0)
    pg.flat(oval(X, y, 5, 5), (86, 64, 46))


def tangents_crossed(c0, r0, c1, r1):
    """The two inner (crossed) tangent lines between circles c0 (radius r0) and c1 (r1): [(p0, p1), (p0', p1')]."""
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    d = math.hypot(dx, dy)
    base = math.atan2(dy, dx)
    a = math.acos(min(1.0, (r0 + r1) / d))
    out = []
    for s in (1, -1):
        th = base + s * a
        p0 = (c0[0] + r0 * math.cos(th), c0[1] + r0 * math.sin(th))
        p1 = (c1[0] - r1 * math.cos(th), c1[1] - r1 * math.sin(th))
        out.append((p0, p1))
    return out


def draw_belt(pg, sh, run=0.0, c0=(WX, WY), r0=WHEEL_PULLEY_R, c1=STONES[0], r1=PULLEY_R + 2, part=1.0, end=None):
    """The crossed leather belt from the wheel's pulley to the mill's (an X between them), stitches moving along it
    by `run` px. part < 1 / end: while Hans is fitting it, only the stretch from the wheel pulley to `end`."""
    col, st = (122, 84, 58), (200, 168, 120)
    if end is not None:                                           # its free end in Hans' tentacle
        (a0, _), _ = tangents_crossed(c0, r0, c1, r1)
        pg.stroke(skia.Path().addOval(skia.Rect(c0[0] - r0 - sh, c0[1] - r0, c0[0] + r0 - sh, c0[1] + r0)), col, 5.0)
        mx, my = (a0[0] + end[0]) / 2, max(a0[1], end[1]) + 18
        pg.stroke(skia.Path().moveTo(a0[0] - sh, a0[1]).quadTo(mx - sh, my, end[0] - sh, end[1]), col, 5.0)
        return
    (a0, a1), (b0, b1) = tangents_crossed(c0, r0, c1, r1)
    for (p, q) in ((a0, a1), (b0, b1)):
        pg.stroke(skia.Path().moveTo(p[0] - sh, p[1]).lineTo(q[0] - sh, q[1]), col, 5.0)
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        n = int(L // 34)
        for i in range(n):                                       # stitches, moving along with the belt
            u = ((i * 34 + run) % L) / L
            x, y = p[0] + (q[0] - p[0]) * u - sh, p[1] + (q[1] - p[1]) * u
            pg.flat(oval(x, y, 2.2, 2.2), st, 0.9)
    for c, r in ((c0, r0), (c1, r1)):
        pg.stroke(skia.Path().addOval(skia.Rect(c[0] - r - sh, c[1] - r, c[0] + r - sh, c[1] + r)), col, 5.0)


def draw_sack(pg, x, y, fill, tied, sh, lean=0.0, cord_to=None, neck_only=False, slump=0.0):
    """A cloth sack standing on the floor at (x, y): fill 0 (flat, open) .. 1 (round and full); tied 0..1:
    0-0.3 the mouth gathered shut into a neck, 0.3-0.75 three turns of cord wound round it, 0.75-1 a bow.
    cord_to: (world) where the loose end of the cord is held while it is wound (r13: "no string, no tying").
    neck_only: just the gathered neck, the cord and the bow (drawn again over Hans' tentacles reaching behind it).
    slump 0..1 (r16, part 3 must-fix "the soft sack turns into a rigid, flared, bucket-like cone" as it's tipped): how
    far it's tipped over on its right side: the cloth sags, that side bulging, the other caving in, and the open mouth
    puckers small, a soft crumpled lip, not a wide rim."""
    X = x - sh
    w = 34 + 18 * fill
    h = 40 + 44 * fill
    g = min(1.0, tied / 0.3)
    wnd = min(max((tied - 0.3) / 0.45, 0.0), 1.0)
    b = min(max((tied - 0.75) / 0.25, 0.0), 1.0)
    mouth = 26 - 14 * g
    sl = min(max(slump, 0.0), 1.0)
    mouth = mouth + (min(mouth, 13.0) - mouth) * sl               # (the lip puckers as the cloth hangs)
    if sl > 0.0:                                                   # tipped on its right side: soft, sagging cloth
        # (a rounded pillow of a body, its flat foot gone round, the width kept till a short gathered neck; the
        # side underneath, its right, sags out, the top side sinks in)
        def mix_(p, q_):
            return (p[0] + (q_[0] - p[0]) * sl, p[1] + (q_[1] - p[1]) * sl)
        stand = [(X - mouth + lean, y - h - 8), (X - w * 0.98, y - h * 0.62), (X - w, y - h * 0.5),
                 (X - w * 0.92, y), (X, y), (X + w * 0.92, y), (X + w, y - h * 0.5), (X + w * 0.98, y - h * 0.62),
                 (X + mouth + lean, y - h - 8)]
        soft = [(X - mouth + lean, y - h - 6), (X - w * 0.62, y - h * 0.78), (X - w * 0.86, y - h * 0.42),
                (X - w * 0.74, y - 3), (X + 4, y + 7), (X + w * 0.98, y - 6), (X + w * 1.1, y - h * 0.46),
                (X + w * 0.8, y - h * 0.8), (X + mouth + lean, y - h - 10)]
        pts = [mix_(p, q_) for p, q_ in zip(stand, soft)]
    else:
        pts = [(X - mouth + lean, y - h - 8), (X - w, y - h * 0.5), (X - w * 0.92, y), (X + w * 0.92, y),
               (X + w, y - h * 0.5), (X + mouth + lean, y - h - 8)]
    if not neck_only:
        pg.shape(smooth(pts), SACK, 0.12)
        if sl > 0.05:                                              # creases gathering into the neck
            for d in (-1, 1):
                pg.stroke(skia.Path().moveTo(X + d * mouth * 0.7 + lean, y - h - 4).quadTo(
                    X + d * (mouth + 10), y - h * 0.86, X + d * w * 0.55, y - h * 0.68), tone(SACK, -0.14), 1.6 * sl)
    if not neck_only and g < 1.0:                                  # the drawstring round the mouth's rim
        pg.stroke(skia.Path().moveTo(X - mouth + lean, y - h - 5).quadTo(X + lean, y - h - 5 + 4 * sl,
                                                                        X + mouth + lean, y - h - 5), TWINE, 2.4)
    if g < 1.0 and not neck_only:                                  # the open mouth (narrowing as it is gathered)
        pg.flat(oval(X + lean, y - h - 8, mouth, 6 * (1 - g) * (1 - 0.5 * sl)), tone(SACK, -0.25))
        if fill > 0.05:
            pg.flat(oval(X + lean, y - h - 6, mouth * 0.8, 4 * (1 - g) * (1 - 0.5 * sl)), FLOUR, 0.9)
    if not neck_only and cord_to is None and wnd == 0.0:           # r13: its drawstring's tail, hanging by the mouth
        e = (X + mouth + lean - 2, y - h - 8)                      # (r32: by the gathered neck too, once he's
        pg.stroke(skia.Path().moveTo(*e).quadTo(e[0] + 12, e[1] + 8, e[0] + 8, e[1] + 26), TWINE, 3.0)   # closed it)
    if g > 0:                                                      # the gathered neck and its ruffled top
        top = y - h - 14 - 16 * g
        pg.flat(smooth([(X - 13 + lean, y - h - 12), (X - 9 + lean, top + 4), (X - 4 + lean, top),
                        (X + 1 + lean, top + 3), (X + 6 + lean, top - 1), (X + 11 + lean, top + 4),
                        (X + 13 + lean, y - h - 12)]), SACK)
        for d in (-5, 1, 7):                                       # its folds
            pg.stroke(skia.Path().moveTo(X + d + lean, top + 6).lineTo(X + d * 0.6 + lean, y - h - 10),
                      tone(SACK, -0.18), 1.6)
    end = None
    for k in range(3):                                             # three turns of cord, wound on one at a time
        uk = min(max(wnd * 3 - k, 0.0), 1.0)
        if uk > 0:
            yk = y - h - 15 + 4 * k
            pg.stroke(skia.Path().moveTo(X - 13 + lean, yk).lineTo(X - 13 + 26 * uk + lean, yk + 1), TWINE, 3.4)
            end = (X - 13 + 26 * uk + lean, yk + 1)
    if cord_to is not None and 0.0 < tied < 0.999:                 # the loose end, held in his tentacle
        e = end or (X - 13 + lean, y - h - 15)
        hx, hy = cord_to[0] - sh, cord_to[1]
        pg.stroke(skia.Path().moveTo(*e).quadTo((e[0] + hx) / 2, max(e[1], hy) + 10, hx, hy), TWINE, 3.0)
    if b > 0:                                                      # pulled tight into a bow
        for d in (-1, 1):
            pg.stroke(skia.Path().addOval(skia.Rect(X + lean + d * 10 * b - 7 * b, y - h - 19, X + lean + d * 10 * b
                                                    + 7 * b, y - h - 9)), TWINE, 2.8)
        for d in (-1, 1):                                          # and its two tails
            pg.stroke(skia.Path().moveTo(X + lean, y - h - 12).lineTo(X + lean + d * 7 * b, y - h - 12 + 12 * b),
                      TWINE, 2.6)


def squirrel(pg, x, y, face, t, sit=1.0, sh=0.0, nibble=0.0):
    """A red squirrel sitting on a branch at (x, y) (its feet), facing `face`, its big tail curled up behind."""
    X = x - sh
    f = face
    body = (190, 98, 56)
    pg.shape(smooth([(X - 22 * f, y - 4), (X - 38 * f, y - 40), (X - 30 * f, y - 76), (X - 10 * f, y - 82),
                     (X - 6 * f, y - 50), (X - 4 * f, y - 10)]), tone(body, 0.08), 0.12)     # the tail
    pg.shape(oval(X, y - 16, 15, 17), body, 0.1)
    pg.flat(oval(X + 4 * f, y - 14, 7, 11), (238, 214, 180))
    hx, hy = X + 9 * f, y - 36 + 1.5 * math.sin(t * 3)
    pg.shape(oval(hx, hy, 11, 10), body, 0.1)
    pg.flat(smooth([(hx - 4 * f, hy - 8), (hx - 2 * f, hy - 20), (hx + 3 * f, hy - 8)]), body)
    pg.flat(oval(hx + 5 * f, hy - 2, 2.4, 2.8), "#2a201c")
    pg.flat(oval(hx + 11 * f, hy + 2, 2.0, 1.6), "#4a2e22")
    if nibble > 0:
        draw_acorn(pg, hx + 12 * f, hy + 10, 0.7)


def bird(pg, x, y, face, t, col, flap=None, sh=0.0, s=1.0):
    """A small round bird (robin, blue tit, ...) at (x, y) (its feet), wings flapping when flap is not None."""
    X = x - sh
    f = face
    pg.shape(oval(X, y - 12 * s, 14 * s, 11 * s), col[0], 0.1)
    pg.flat(oval(X + 4 * f * s, y - 9 * s, 7 * s, 6 * s), col[1])
    pg.flat(oval(X + 11 * f * s, y - 20 * s, 7.5 * s, 7 * s), col[0])
    pg.flat(oval(X + 13 * f * s, y - 21 * s, 1.6 * s, 1.6 * s), "#1a1414")
    pg.flat(smooth([(X + 17 * f * s, y - 21 * s), (X + 23 * f * s, y - 19 * s), (X + 17 * f * s, y - 17 * s)]),
            "#e0b050")
    pg.flat(smooth([(X - 12 * f * s, y - 14 * s), (X - 24 * f * s, y - 18 * s), (X - 22 * f * s, y - 10 * s)]),
            tone(col[0], -0.15))
    if flap is not None:
        wy = y - 12 * s - (14 * flap - 4) * s
        pg.flat(smooth([(X - 6 * f * s, y - 12 * s), (X + 6 * f * s, y - 12 * s), (X - 2 * f * s, wy)]),
                tone(col[0], -0.12))
    else:
        pg.flat(oval(X - 2 * f * s, y - 12 * s, 8 * s, 5 * s, 10 * f), tone(col[0], -0.12))


BIRD_COLS = [((200, 110, 74), (236, 156, 110)), ((96, 140, 196), (238, 210, 110)), ((206, 176, 72), (240, 226, 160)),
             ((150, 112, 82), (214, 186, 150))]
HOUSE_COLS = [(104, 160, 214), (214, 150, 104), (150, 190, 120), (200, 120, 150)]


def birdhouse(pg, x, y, j, sh, glow=0.0, glow_only=False, door_r=11.0):
    """A birdhouse on its post at (x, y) (its floor): its own colour, a little roof, a round door. glow_only: just
    its lit door (the night pass; the birds flying out stay in front of it)."""
    X = x - sh
    col = HOUSE_COLS[j]
    if glow_only:
        if glow > 0:
            pg.flat(oval(X, y - 40, door_r, door_r), LAMP, 0.7 * glow)
        return
    pg.shape(rrect(X - 34, y - 70, X + 34, y, 3), col, 0.1)
    pg.shape(smooth([(X - 44, y - 66), (X, y - 104), (X + 44, y - 66)]), tone(col, -0.25), 0.05)
    pg.flat(oval(X, y - 40, door_r, door_r), "#2a2230")
    if glow > 0:
        pg.flat(oval(X, y - 40, door_r, door_r), LAMP, 0.7 * glow)
    pg.flat(rrect(X - 14, y + 2, X + 14, y + 8, 2), tone(col, -0.2))


def cottage(pg, x, y, w, h, roof, col, sh, door_r=20.0, window=False, glow=0.0, door_open=0.0, glow_only=False):
    """A little animal house (the hedgehog's, the bunnies') on the meadow at (x, y): walls in its own colour, a roof,
    a rounded door (lit inside at night), a round window. glow_only: just the light in the door and the window (the
    pass over the night's darkening; it never paints the walls again over whoever is in front of them)."""
    X = x - sh
    door = rrect(X - door_r, y - door_r * 2.1, X + door_r, y, door_r)
    if glow_only:
        if glow > 0:
            pg.flat(door, LAMP, 0.85 * glow)
            pg.flat(oval(X, y - door_r, door_r * 2.6, door_r * 2.2), LAMP, 0.16 * glow, blur=16)
            if window:
                pg.flat(oval(X + w * 0.3, y - h * 0.62, 13, 13), LAMP, 0.9)
        return
    pg.shape(rrect(X - w / 2, y - h, X + w / 2, y, 4), col, 0.1)
    pg.shape(smooth([(X - w / 2 - 14, y - h + 4), (X, y - h - roof), (X + w / 2 + 14, y - h + 4)]), tone(col, -0.22),
             0.06)
    pg.flat(door, (70, 52, 46))
    if glow > 0:
        pg.flat(door, LAMP, 0.85 * glow)
        pg.flat(oval(X, y - door_r, door_r * 2.6, door_r * 2.2), LAMP, 0.16 * glow, blur=16)
    if door_open < 1:                                              # the door itself, swinging open
        dw = door_r * 2 * (1 - door_open)
        pg.shape(rrect(X - door_r, y - door_r * 2.1, X - door_r + dw, y, min(door_r, dw / 2)), tone(col, -0.35), 0.0)
    if window:
        wx, wy = X + w * 0.3, y - h * 0.62
        pg.flat(oval(wx, wy, 13, 13), LAMP if glow > 0 else (70, 52, 46), 0.9 if glow > 0 else 1.0)


def lantern(pg, x, y, lit, t, sh):
    """A paper lantern hanging at (x, y); lit 0..1 by Glo's light."""
    X = x - sh
    pg.stroke(skia.Path().moveTo(X, y - 40).lineTo(X, y - 20), (90, 70, 56), 2.0)
    col = mix((214, 196, 170), (255, 214, 140), lit)
    pg.shape(oval(X, y, 18, 22), col, 0.1)
    for q in (-8, 0, 8):
        pg.stroke(skia.Path().moveTo(X + q, y - 20).quadTo(X + q * 1.4, y, X + q, y + 20), tone(col, -0.12), 1.2, 0.7)
    pg.flat(rrect(X - 9, y - 24, X + 9, y - 19, 2), (90, 70, 56))
    if lit > 0:
        fl = 1.0 + 0.05 * math.sin(t * 9 + x)
        pg.glow(X, y, 90 * fl, "#ffd68a", 0.32 * lit)


def fireflies(pg, t, sh, amount, x0=3300.0, x1=6400.0, n=46):
    if amount <= 0:
        return
    rs = np.random.default_rng(77)
    for _ in range(n):
        bx, by = rs.uniform(x0, x1), rs.uniform(420, 880)
        ph, sp = rs.uniform(0, 6.3), rs.uniform(0.15, 0.4)
        x = bx + 60 * math.sin(t * sp + ph)
        y = by + 30 * math.sin(t * sp * 1.7 + ph * 2)
        a = (0.5 + 0.5 * math.sin(t * 1.3 + ph * 3)) * amount
        sx = x - sh
        if -20 < sx < W + 20:
            pg.flat(oval(sx, y, 9, 9), "#d8f08a", 0.18 * a, blur=5)
            pg.flat(oval(sx, y, 2.4, 2.4), "#eefcb0", 0.8 * a)
