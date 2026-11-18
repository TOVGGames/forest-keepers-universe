"""The places of the talking format's first episode, in the flat look, in early spring (ep 1 script, 2026-11-17).

The places: the old oak at the forest's edge (morning and night), the pond, the molehill meadow, and the meadow at
sunset. One camera height for all of them, so one distance rule (scale_at): a Keeper's size comes from where its feet
are. Everything here is scenery, painted once per shot. Nothing in front of the Keepers: roots, reeds and molehills sit
behind and around where they stand (the reviewer's note: whatever is behind stays behind for the whole shot).

Spring, not autumn: fresh greens, blossom on a few trees, last year's leaves only as damp brown litter under the oak.
"""
import math

import numpy as np
import skia

from families.keepers import flat
from families.keepers.storybook import C, oval, smooth, tone, tube

W, H = 1920, 1080
HORIZON = 790.0

SPRING = dict(sky_top="#bcd3dc", sky_mid="#eaf0e4", sky_low="#f3e6d2", far="#a9b9c4", far2="#9fb3a4",
              mid="#9fb27a", field="#a9c07a", ground="#93ad62", path="#d9c79a", pine="#5d7f6c", leafy="#7fa65a",
              fresh="#9cc46a", blossom="#e9b8c4", bark="#7d5c48", litter="#9a7a5a", mud="#8a7258",
              water="#8fb0c0", water2="#b7cfd6", reed="#6f8a56", lily="#7fa060", soil="#7a5a44")
LIGHT = {  # sky gradient (top, middle, low) and a wash over the land: (colour, alpha)
    "morning": (("#bcd3dc", "#eaf0e4", "#f6e4cf"), None),
    "day": (("#b5cfe0", "#e4eee8", "#eef0dc"), None),
    "sunset": (("#5f5d8f", "#c07f8c", "#f2b07a"), ("#e8946a", 0.18)),
    "night": (("#141c36", "#25335a", "#3d4c6e"), ("#1c2a52", 0.72)),
}


def scale_at(y):
    """A Keeper's size from where its feet are on the ground: the one distance rule, every place (as in the proofs)."""
    return 1.1 * (y - HORIZON) / 250.0


def _sky(pg, light, seed, sun=True):
    top, mid, low = LIGHT[light][0]
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.7)], [C(top), C(mid), C(low)], [0, 0.6, 1])
    pg.c.drawPaint(skia.Paint(Shader=g))
    rs = np.random.default_rng(seed)
    if light == "night":
        for _ in range(140):                                      # stars, more of them higher up
            x, y = rs.uniform(0, W), H * rs.uniform(0, 0.55) ** 1.4
            pg.flat(oval(x, y, 1.6 + 1.6 * rs.random(), 1.6 + 1.6 * rs.random()), "#f4ecd2", 0.5 + 0.5 * rs.random())
    elif light == "sunset":
        if sun:
            pg.flat(oval(W * 0.3, H * 0.5, 70, 70), "#fbd79a", 0.95, blur=6)        # the sun, low behind the hills
    else:
        for cx, cy, w in ((0.16, 0.13, 0.16), (0.5, 0.08, 0.11), (0.86, 0.15, 0.14)):
            flat.cloud(pg, W * cx, H * cy, W * w)
    pg.grain_opaque()


FAR_HILL = [(-100, H * 0.58), (W * 0.15, H * 0.5), (W * 0.4, H * 0.56), (W * 0.62, H * 0.51), (W * 0.85, H * 0.56),
            (W + 100, H * 0.5)]


def setting_sun(pg, view, u):
    """The sunset's sun going down behind the far hill (u 0 -> 1), drawn over the scenery but clipped to the sky
    above the hill, so it really goes behind it (the backdrop is then painted with sun=False)."""
    p = smooth(FAR_HILL, closed=False)
    p.lineTo(FAR_HILL[-1][0], H + 400)
    p.lineTo(FAR_HILL[0][0], H + 400)
    p.close()
    c = pg.c
    c.save()
    if view:
        Z = view["zoom"]
        c.translate(view["sx"] - view["cx"] * Z, view["sy"] - view["cy"] * Z)
        c.scale(Z, Z)
    c.clipPath(p, skia.ClipOp.kDifference, True)
    pg.flat(oval(W * 0.3, H * 0.5 + 160 * u, 70, 70), "#fbd79a", 0.95 * (1 - 0.35 * u), blur=6)
    c.restore()


def _hills(pg, P):
    flat.hill_band(pg, FAR_HILL, H, P["far"])
    flat.hill_band(pg, [(-100, H * 0.62), (W * 0.25, H * 0.585), (W * 0.5, H * 0.63), (W * 0.75, H * 0.59),
                        (W + 100, H * 0.62)], H, P["far2"])


def _forest_wall(pg, P, rs, x0=-60, x1=W + 60):
    """The edge of the forest: a dense band of trees across the back of the meadow."""
    flat.hill_band(pg, [(-100, H * 0.66), (W * 0.3, H * 0.645), (W * 0.6, H * 0.665), (W + 100, H * 0.65)], H,
                   P["mid"])
    x = x0
    while x < x1:
        h = H * rs.uniform(0.2, 0.3)
        f = (flat.pine, flat.lolly_tree, flat.poplar)[int(rs.integers(0, 3))]
        col = (P["pine"], P["leafy"], P["fresh"], P["blossom"])[int(rs.integers(0, 4))] if f is not flat.pine else P["pine"]
        f(pg, x, H * 0.7 + rs.uniform(-6, 6), h, tone(col, rs.uniform(-0.06, 0.04)), P["bark"])
        x += rs.uniform(48, 80)


def _meadow(pg, P, rs, top=HORIZON - 10, litter=False):
    flat.hill_band(pg, [(-100, top + 6), (W * 0.3, top - 8), (W * 0.65, top + 2), (W + 100, top - 6)], H,
                   P["ground"], 0.06, 0.08)
    for _ in range(60):                                           # short grass: tufts low down, below their feet
        x, y = rs.uniform(0, W), rs.uniform(top + 20, H)
        flat.tuft(pg, x, y, 6 + 14 * scale_at(y), tone(P["ground"], -0.14))
    for _ in range(26):                                           # a few spring flowers
        x, y = rs.uniform(0, W), rs.uniform(top + 30, H)
        pg.flat(oval(x, y - 4, 4 + 4 * scale_at(y), 4 + 4 * scale_at(y)), ("#f4efe2", "#f2d27a", "#e9b8c4")[_ % 3])
    if litter:
        for _ in range(110):                                      # last year's leaves, damp and flat
            x, y = rs.uniform(0, W * 0.75), rs.uniform(top + 10, H)
            flat.leaf(pg, x, y, 5 + 7 * scale_at(y), rs.uniform(0, 180), tone(P["litter"], rs.uniform(-0.1, 0.08)))


def old_oak(pg, P, x, y, h, rs):
    """The old oak: a thick, short, gnarled trunk on wide roots, a huge round spring crown of several lobes, a
    squirrel's hole in the trunk and a bird's nest in a fork. Its roots spread on the ground behind the Keepers."""
    c = pg.c                                                     # the trunk ends at the ground, under its roots
    c.save()
    c.clipRect(skia.Rect(x - h, y - h * 1.5, x + h, y + h * 0.015))
    pg.shape(tube([(x, y + 4), (x + h * 0.02, y - h * 0.42), (x - h * 0.03, y - h * 0.6)], h * 0.15, h * 0.1),
             P["bark"], 0.12, (-0.5, 0.0))
    c.restore()
    for dx, dy in ((-0.34, 0.02), (0.36, 0.03), (-0.18, 0.045), (0.2, 0.05)):          # roots, along the ground
        pg.shape(tube([(x + dx * h * 0.12, y - h * 0.03), (x + dx * h * 0.6, y + dy * h * 0.6), (x + dx * h, y + dy * h)],
                      h * 0.06, h * 0.012), tone(P["bark"], -0.04), 0.08)
    pg.shape(tube([(x - h * 0.02, y - h * 0.5), (x - h * 0.22, y - h * 0.72)], h * 0.06, h * 0.035), P["bark"], 0.1)
    pg.shape(tube([(x + h * 0.01, y - h * 0.48), (x + h * 0.24, y - h * 0.7)], h * 0.06, h * 0.035), P["bark"], 0.1)
    pg.flat(oval(x + h * 0.02, y - h * 0.3, h * 0.035, h * 0.05), "#3a2a22")          # the squirrel's hole
    for dx, dy, r, col in ((-0.3, -0.78, 0.26, P["leafy"]), (0.3, -0.8, 0.27, P["leafy"]),
                           (0.0, -0.98, 0.3, P["fresh"]), (-0.12, -0.72, 0.22, P["fresh"]),
                           (0.16, -0.74, 0.22, tone(P["leafy"], 0.05))):
        pg.shape(oval(x + dx * h, y + dy * h, r * h, r * h * 0.92), col, 0.12)
    nx, ny = x + h * 0.27, y - h * 0.6                                                 # the nest, under the crown's edge
    pg.shape(tube([(x + h * 0.12, y - h * 0.62), (nx + h * 0.06, ny + h * 0.005)], h * 0.018, h * 0.012), P["bark"], 0.08)
    pg.shape(smooth([(nx - h * 0.058, ny - h * 0.014), (nx - h * 0.045, ny + h * 0.028), (nx, ny + h * 0.036),
                     (nx + h * 0.045, ny + h * 0.028), (nx + h * 0.058, ny - h * 0.014)]), "#8a6a4a", 0.12)   # a bowl of twigs
    pg.flat(oval(nx, ny - h * 0.013, h * 0.058, h * 0.013), "#6e5238")                   # its rim
    tw = skia.Paint(Color=C("#5e4630"), StrokeWidth=max(1.5, h * 0.0045), AntiAlias=True,
                    StrokeCap=skia.Paint.kRound_Cap)
    for i in range(14):                                           # twigs woven round it, poking out at the rim
        u = -1 + 2 * i / 13
        a = rs.uniform(-0.5, 0.5)
        px, py = nx + u * h * 0.05, ny - h * 0.012 + (1 - u * u) * h * rs.uniform(0.0, 0.03)
        L = h * rs.uniform(0.02, 0.035)
        c.drawLine(px - math.cos(a) * L, py - math.sin(a) * L, px + math.cos(a) * L, py + math.sin(a) * L, tw)
    return dict(hole=(x + h * 0.02, y - h * 0.3, h * 0.035, h * 0.05), nest=(nx, ny), oak=(x, y, h))


def oak_life(pg, marks, S, Z, sleepy=1.0):
    """Who lives in the old oak, asleep at night (ep 1 chapter 5: "A nest, with birds asleep in it. And a squirrel,
    curled up in a hole in the trunk. And little moths on the bark."). S maps world to screen, Z the zoom."""
    x, y, h = marks["oak"]
    nx, ny = marks["nest"]
    ink = skia.Paint(Color=C("#3a2a22"), AntiAlias=True, Style=skia.Paint.kStroke_Style,
                     StrokeCap=skia.Paint.kRound_Cap)
    for dx, f in ((-0.024, 1), (0.02, -1)):                       # two robins, heads tucked, eyes shut
        X, Y = S(nx + dx * h, ny - h * 0.02)
        r = h * 0.02 * Z
        pg.flat(oval(X, Y, r * 1.2, r * 0.95), "#7d6656")                                   # brown back
        pg.flat(oval(X + f * r * 0.35, Y + r * 0.25, r * 0.75, r * 0.55), "#e08850")       # orange breast
        pg.flat(oval(X + f * r * 0.75, Y - r * 0.55, r * 0.55, r * 0.5), "#7d6656")       # the head, tucked down
        pg.flat(smooth([(X + f * r * 1.2, Y - r * 0.6), (X + f * r * 1.55, Y - r * 0.45),
                        (X + f * r * 1.2, Y - r * 0.35)]), "#e0b050")                       # beak
        ink.setStrokeWidth(max(1.2, r * 0.12))
        path = skia.Path()
        path.moveTo(X + f * r * 0.6, Y - r * 0.62)
        path.quadTo(X + f * r * 0.78, Y - r * 0.5, X + f * r * 0.95, Y - r * 0.62)          # closed eye
        pg.c.drawPath(path, ink)
    hx, hy, hrx, hry = marks["hole"]                                # the squirrel, curled up asleep in its hole
    X, Y = S(hx, hy + hry * 0.2)
    rx, ry = hrx * Z, hry * Z
    pg.flat(oval(X - rx * 0.15, Y + ry * 0.05, rx * 0.8, ry * 0.6), "#b0663c")                # its body
    for ex in (-0.55, -0.15):                                       # two ears
        pg.flat(smooth([(X + rx * (ex - 0.14), Y - ry * 0.4), (X + rx * ex, Y - ry * 0.85),
                        (X + rx * (ex + 0.14), Y - ry * 0.4)]), "#a05a34")
    pg.flat(oval(X - rx * 0.35, Y - ry * 0.25, rx * 0.42, ry * 0.36), "#b8703f")              # the head
    pg.flat(oval(X + rx * 0.4, Y - ry * 0.05, rx * 0.5, ry * 0.65), "#d08a52")                # the bushy tail, curled
    pg.flat(oval(X + rx * 0.45, Y - ry * 0.25, rx * 0.28, ry * 0.32), "#e4a876")              # over it, pale tip
    ink.setStrokeWidth(max(1.2, 0.09 * rx))
    path = skia.Path()
    path.moveTo(X - rx * 0.55, Y - ry * 0.28)
    path.quadTo(X - rx * 0.45, Y - ry * 0.18, X - rx * 0.33, Y - ry * 0.28)                    # closed eye
    pg.c.drawPath(path, ink)
    for mx, my, ang in ((-0.065, -0.15, -25), (0.075, -0.33, 18), (-0.01, -0.53, -8)):   # moths resting on the bark
        X, Y = S(x + mx * h, y + my * h)
        r = h * 0.009 * Z
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

        def R(u, v):
            return X + u * ca - v * sa, Y + u * sa + v * ca
        pg.flat(smooth([R(0, -r * 1.4), R(-r * 1.5, r * 1.1), R(0, r * 0.7), R(r * 1.5, r * 1.1)]), "#b9a585")  # wings
        pg.flat(smooth([R(-r * 0.9, r * 0.5), R(0, r * 0.2), R(r * 0.9, r * 0.5), R(0, r * 0.45)]), "#8a7458")    # band
        ink.setStrokeWidth(max(1.0, r * 0.12))
        for sx in (-1, 1):                                         # antennae
            pg.c.drawLine(*R(0, -r * 1.3), *R(sx * r * 0.7, -r * 2.2), ink)


def pond(pg, P, rs):
    cx, cy = W * 0.5, HORIZON + 40
    pg.flat(oval(cx, cy, W * 0.42, 70), P["mud"])                                    # the muddy edge
    pg.flat(oval(cx, cy - 4, W * 0.4, 60), P["water"])
    for dx, dy, w in ((-0.2, -14, 0.12), (0.15, 6, 0.09), (0.05, -24, 0.07)):
        pg.flat(oval(cx + dx * W, cy + dy, w * W, 6), P["water2"], 0.7)
    for dx, dy in ((-0.28, 8), (-0.1, 18), (0.22, -4), (0.3, 16)):                     # lily pads
        pg.flat(oval(cx + dx * W, cy + dy, 34, 10), P["lily"])
    for x in list(np.linspace(W * 0.08, W * 0.22, 7)) + list(np.linspace(W * 0.8, W * 0.93, 6)):   # reeds, back edge
        hh = rs.uniform(60, 110)
        pg.flat(oval(x, cy - 40 - hh * 0.5, 3.5, hh * 0.5), P["reed"])
        pg.flat(oval(x, cy - 40 - hh, 5, 12), "#8a6450")


def molehills(pg, P, rs):
    for x, y in ((260, 880), (560, 850), (1500, 870), (1760, 905), (420, 1040), (1680, 835)):  # none behind a Keeper
        s = 0.5 + scale_at(y)
        pg.shape(smooth([(x - 60 * s, y), (x - 30 * s, y - 34 * s), (x + 20 * s, y - 38 * s), (x + 62 * s, y)]),
                 P["soil"], 0.12)


PLACES = {  # name: (what to draw, default light)
    "oak": ("oak", "morning"), "pond": ("pond", "morning"), "molehills": ("molehills", "day"),
    "sunset": ("sunset", "sunset"),
}
OAK = (380.0, 830.0, 640.0)          # the old oak: trunk base x, ground y, height (left side: it stays off to the side)


def backdrop(place, light=None, seed=7, view=None, sun=True, page=(W, H)):
    """The scenery of a place in a light, painted once: -> (skia image, landmarks). The light's wash goes over the
    whole frame afterwards (light_over). view: a closer framing (zoom about cx, cy to sx, sy on screen), painted at
    that size so it stays sharp (the same scenery, the same seed, so nothing moves across the cut). page: the size of the
    picture (the world stays 1920x1080; an upright Short is a 1080x1920 page with a view into it)."""
    P = SPRING
    light = light or PLACES[place][1]
    PW, PH = page
    pg = flat.FlatPage(PW, PH)
    if view:
        Z = view["zoom"]
        assert view["sx"] - view["cx"] * Z <= 0 and (W - view["cx"]) * Z + view["sx"] >= PW, view
        assert view["sy"] - view["cy"] * Z <= 0 and (H - view["cy"]) * Z + view["sy"] >= PH, view
        pg.c.translate(view["sx"] - view["cx"] * Z, view["sy"] - view["cy"] * Z)
        pg.c.scale(Z, Z)
    _sky(pg, light, seed, sun)
    rs = np.random.default_rng(seed)
    pg.begin_grain()
    _hills(pg, P)
    if place in ("oak", "molehills"):
        _forest_wall(pg, P, rs)
    else:
        _forest_wall(pg, P, rs, x0=W * 0.55 if place == "sunset" else -60)
    _meadow(pg, P, rs, litter=place == "oak")
    extra = {}
    if place == "oak":
        extra = old_oak(pg, P, *OAK, rs)
    elif place == "pond":
        pond(pg, P, rs)
    elif place == "molehills":
        molehills(pg, P, rs)
    pg.end_grain()
    return pg.surface.makeImageSnapshot(), extra


def light_over(pg, light, part=1.0):
    """The light of the hour as a multiply wash. Night is dark for everyone, but the Keepers stay readable: the
    scenery gets the wash first (part 0.6), then the whole frame, Keepers included, gets the rest (part 0.45)."""
    wash = LIGHT[light][1]
    if wash:
        pg.c.drawPaint(skia.Paint(Color=C(wash[0], wash[1] * part), BlendMode=skia.BlendMode.kMultiply))
