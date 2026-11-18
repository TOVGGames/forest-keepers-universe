"""Storyboard stills for episode 14, "Sprout's Christmas Tree" (docs/engines/forest_keepers_christmas.md), in the flat
picture-book look (illustrate style 6 + flat.py), with the owner's notes from approving FK0016 (2026-11-05): every
Keeper makes an ornament, and a gentle conflict that builds to a climax and is resolved ("as long as it never gets too
tense"): on Christmas Eve a gust shakes the little fir, the star tumbles into the snow and the lanterns go out; the
Keepers find the star (Digs' hat lamp), shake the snow off, Springs bounces it back up and Glo relights the lanterns,
just as the winter animals come to see it.

    python families/keepers/christmas_flat_board.py <out_dir>
"""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import numpy as np  # noqa: E402
import skia  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from families.keepers import flat  # noqa: E402
from families.keepers import illustrate as il  # noqa: E402
from families.keepers.animals import deer, fox  # noqa: E402
from families.keepers.chatter import bubble  # noqa: E402
from families.keepers.storybook import mix, oval, rrect, smooth, tone, tube  # noqa: E402
from families.keepers.winter_animals import chickadee  # noqa: E402

W, H = 1920, 1080
G = 930                                   # the snowy ground line the Keepers stand on
K = 0.72                                  # the Keepers' scale (as in ep 13)
FONT = "engine/assets/fonts/Inter-Bold.otf"
SNOW, SNOW_SH, TRODDEN = "#eef0ec", "#c9d3da", "#ddd5c6"
FIR, FIR_D = "#4f7a5e", "#3f6550"
POT, SOIL = "#c07a52", "#6e5442"
RED, GOLD, WOOD, BERRY, RIBBON = "#c2554a", "#e2b54e", "#cf9f6a", "#b8423e", "#c98a80"
LAMP = "#f6d48a"


# ----------------------------------------------------------------------------------------------- scenery

def night_col(c, night):
    return mix(c, "#2c3656", 0.55 * night)


def sky(pg, night):
    """A winter sky: a pale morning (night 0) to a deep blue night with stars (night 1)."""
    top = mix("#c3d0d6", "#26324e", night)
    low = mix("#f2e6d8", "#5a6788", night)
    pg.grad(skia.Path().addRect(skia.Rect(0, 0, W, G)), top, low)
    if night > 0.5:
        rs = np.random.default_rng(7)
        for _ in range(70):
            x, y, r = rs.uniform(0, W), rs.uniform(10, G - 420), rs.uniform(1.2, 2.6)
            pg.flat(oval(x, y, r, r), "#f4efe2", rs.uniform(0.5, 0.95))


def snow_hills(pg, night, seed=3):
    rs = np.random.default_rng(seed)
    def col(c):                                                    # the snow is bluer at night
        return night_col(c, night)
    for y, amp, c in ((G - 300, 60, "#b8c4cc"), (G - 210, 50, "#cfd8dc"), (G - 120, 40, "#dfe5e4")):
        xs = np.linspace(-100, W + 100, 9)
        pts = [(x, y - amp * (0.5 + 0.5 * math.sin(x / 260 + rs.uniform(0, 6)))) for x in xs]
        flat.hill_band(pg, pts, G + 10, col(c))
        for x in rs.uniform(0, W, 7):                              # snowy pines along the band
            h = rs.uniform(110, 190) * (y / G)
            yb = y - amp * 0.3 + 30
            flat.pine(pg, x, yb, h, col("#6b8579"))
            w = h * 0.26
            cap = smooth([(x, yb - h), (x + w * 0.3, yb - h * 0.7), (x, yb - h * 0.76), (x - w * 0.3, yb - h * 0.7)])
            pg.flat(cap, col(SNOW))


def ground(pg, night, path=True):
    p = skia.Path().addRect(skia.Rect(0, G - 40, W, H))
    pg.grad(p, night_col(SNOW, night), night_col(SNOW_SH, night))
    if path:
        pg.flat(smooth([(-50, G + 10), (W * 0.5, G - 14), (W + 50, G + 6), (W + 50, G + 60), (W * 0.5, G + 44),
                        (-50, G + 64)]), night_col(TRODDEN, night), 0.9)


def falling_snow(pg, n=90, seed=11):
    rs = np.random.default_rng(seed)
    for _ in range(n):
        x, y, r = rs.uniform(0, W), rs.uniform(0, H), rs.uniform(2.0, 5.0)
        pg.flat(oval(x, y, r, r), "#fbfaf4", rs.uniform(0.6, 0.95))


def scene(pg, night=0.0, path=True, snow=False):
    pg.begin_grain()
    sky(pg, night)
    snow_hills(pg, night)
    ground(pg, night, path)
    pg.end_grain()
    if snow:
        falling_snow(pg)


# ----------------------------------------------------------------------------------------------- props

def star_path(x, y, r, inner=0.45, rot=-90.0):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else r * inner
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    p = skia.Path()
    p.addPoly(pts, True)
    return p


def fir(pg, x, yb, h, pot=True, soil_ball=False, orn=0, lights=0.0, star=True, snowy=0.0, lean=0.0, garland=False,
        berries=False, ribbons=False):
    """The little fir: three rounded tiers on a short trunk, in a clay pot (or lifted with its ball of soil)."""
    c = pg.c
    c.save()
    c.rotate(lean, x, yb)
    base = yb
    if pot:
        pw = h * 0.34
        pg.shape(smooth([(x - pw * 0.62, base - h * 0.26), (x + pw * 0.62, base - h * 0.26), (x + pw * 0.48, base),
                         (x - pw * 0.48, base)]), POT, 0.12)
        pg.shape(rrect(x - pw * 0.7, base - h * 0.3, x + pw * 0.7, base - h * 0.23, 6), tone(POT, 0.06), 0.0)
        base -= h * 0.28
    if soil_ball:
        pg.shape(oval(x, base - h * 0.07, h * 0.17, h * 0.12), SOIL, 0.12)
        base -= h * 0.1
    pg.shape(rrect(x - h * 0.035, base - h * 0.16, x + h * 0.035, base + 4, 4), "#7a5640", 0.0)
    top = base - h
    tiers = [(0.95, 0.42, 0.18), (0.68, 0.33, 0.44), (0.42, 0.22, 0.7)]
    for i, (yb_, w, yt) in enumerate(tiers):
        y0, y1 = base - h * (1 - yb_) - h * 0.12, base - h * yt - h * 0.3
        p = smooth([(x, y1 - h * 0.1), (x + h * w * 0.5, (y0 + y1) / 2), (x + h * w, y0), (x, y0 + h * 0.04),
                    (x - h * w, y0), (x - h * w * 0.5, (y0 + y1) / 2)])
        pg.shape(p, FIR if i % 2 == 0 else tone(FIR, 0.04), 0.14)
        if snowy:
            pg.flat(smooth([(x - h * w * 0.9, y0 - 2), (x - h * w * 0.4, y0 - h * 0.05 * snowy), (x, y0 - h * 0.02),
                            (x + h * w * 0.5, y0 - h * 0.06 * snowy), (x + h * w * 0.9, y0 - 2),
                            (x, y0 + h * 0.02)]), SNOW, 0.95)
    if garland:                                                     # Hans' braided garland, swagged round it
        for yy, ww in ((0.4, 0.26), (0.62, 0.36), (0.82, 0.44)):
            gy = top + h * yy
            pth = skia.Path()
            pth.moveTo(x - h * ww, gy)
            pth.quadTo(x, gy + h * 0.07, x + h * ww, gy - h * 0.02)
            pg.stroke(pth, "#b98d56", 5)
    rs = np.random.default_rng(5)
    spots = [(x + h * u, top + h * v) for u, v in ((-0.18, 0.5), (0.14, 0.42), (0.27, 0.74), (-0.3, 0.8), (0.0, 0.64),
                                                   (-0.08, 0.32), (0.34, 0.9), (-0.2, 0.95))]
    for i, (ox, oy) in enumerate(spots[:orn]):
        kind = i % 3
        if kind == 0:
            pg.shape(star_path(ox, oy, h * 0.045), WOOD, 0.1)
        elif kind == 1:
            pg.shape(oval(ox, oy, h * 0.032, h * 0.032), RED if i % 2 else GOLD, 0.12)
        else:                                                       # a carved acorn
            pg.shape(oval(ox, oy + h * 0.012, h * 0.026, h * 0.032), WOOD, 0.1)
            pg.shape(oval(ox, oy - h * 0.014, h * 0.03, h * 0.016), "#8a6450", 0.0)
    if berries:
        for i in range(14):
            u = i / 13
            bx, by = x + h * 0.36 * (u * 2 - 1) * (0.5 + 0.5 * u), top + h * (0.55 + 0.35 * u)
            pg.flat(oval(bx, by, 5, 5), BERRY)
    if ribbons:
        for ox, oy in ((x - h * 0.22, top + h * 0.58), (x + h * 0.2, top + h * 0.83)):
            pg.flat(smooth([(ox - 12, oy - 6), (ox, oy), (ox - 12, oy + 6)]), RIBBON)
            pg.flat(smooth([(ox + 12, oy - 6), (ox, oy), (ox + 12, oy + 6)]), RIBBON)
    if lights:
        for i in range(9):
            lx = x + h * (rs.uniform(-0.34, 0.34)) * (0.4 + 0.6 * i / 8)
            ly = top + h * (0.3 + 0.62 * i / 8)
            pg.glow(lx, ly, 30, LAMP, 0.45 * lights)
            pg.flat(oval(lx, ly, 6, 6), LAMP, lights)
    if star:
        sx, sy = x, top - h * 0.06
        if lights:
            pg.glow(sx, sy, 80, LAMP, 0.5 * lights)
        pg.shape(star_path(sx, sy, h * 0.085), GOLD, 0.12)
    c.restore()


def lantern(pg, x, y, lit, post=0):
    if post:
        pg.shape(rrect(x - 5, y, x + 5, y + post, 3), "#7a5640", 0.0)
    pg.shape(rrect(x - 14, y - 34, x + 14, y, 6), "#5d4a3e", 0.0)
    pg.flat(rrect(x - 10, y - 30, x + 10, y - 4, 4), LAMP if lit else "#3a3a44")
    if lit:
        pg.glow(x, y - 17, 70, LAMP, 0.55)


def workbench(pg, x0, x1, y):
    pg.shape(rrect(x0, y - 150, x1, y - 128, 6), "#b07e56", 0.12)
    for lx in (x0 + 30, x1 - 30):
        pg.shape(rrect(lx - 10, y - 130, lx + 10, y, 4), "#8a6450", 0.0)


def ornament_box(pg, x, y, open_=True):
    pg.shape(rrect(x - 90, y - 70, x + 90, y, 8), "#9c6e4c", 0.12)
    if open_:
        pg.shape(rrect(x - 92, y - 120, x + 92, y - 72, 8), "#b38360", 0.08)
        for i, c in enumerate((GOLD, RED, WOOD, RED, GOLD)):
            pg.flat(oval(x - 60 + i * 30, y - 70, 12, 12), c)


def rabbit(cv_pg, x, y, s, face=-1):
    """An eastern cottontail sitting: round grey-brown body, white tail puff, long ears, a big dark eye."""
    pg = cv_pg
    f = face
    body, light, dark = "#9a8672", "#b9a68f", "#3a2c24"
    pg.shape(oval(x - f * 10 * s, y - 34 * s, 46 * s, 36 * s), body, 0.12)
    pg.flat(oval(x - f * 50 * s, y - 34 * s, 13 * s, 13 * s), "#f4efe6")
    pg.shape(oval(x + f * 30 * s, y - 62 * s, 26 * s, 24 * s), body, 0.1)
    for dx in (-6, 8):
        pg.shape(oval(x + f * (22 + dx) * s, y - 104 * s, 8 * s, 28 * s, rot=-f * (10 + dx)), body, 0.08)
        pg.flat(oval(x + f * (22 + dx) * s, y - 102 * s, 4 * s, 20 * s, rot=-f * (10 + dx)), "#d4a8a0")
    pg.flat(oval(x + f * 38 * s, y - 66 * s, 6 * s, 7 * s), dark)
    pg.flat(oval(x + f * 40 * s, y - 68 * s, 2 * s, 2 * s), "#ffffff")
    pg.flat(oval(x + f * 52 * s, y - 56 * s, 3.5 * s, 3 * s), "#b07a70")
    pg.flat(oval(x + f * 10 * s, y - 4 * s, 22 * s, 7 * s), light)


def say(pg, x, y, pic, r=50):
    il.creature(pg, lambda cv: bubble(cv, x, y, r, pic, (214, 196, 176), tail=(x - 30, y + r * 1.6)), x, y)


def keeper(pg, kind, x, **a):
    return il.figure(pg, kind, x, G + a.pop("dy", 0), a.pop("k", K), 6, t=a.pop("t", 1.3), **a)


# ----------------------------------------------------------------------------------------------- the stills

def caption(rgb, n, text):
    im = Image.fromarray(rgb)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 30)
    label = "Opening" if n == 0 else f"{n}/6"
    s = f"{label}   {text}"
    w = d.textlength(s, font=f) + 60
    d.rounded_rectangle([960 - w / 2, 14, 960 + w / 2, 66], 12, fill=(28, 30, 38))
    d.text((960, 40), s, font=f, fill=(236, 232, 220), anchor="mm")
    return im


def hook(pg):
    scene(pg, 0.15)
    fir(pg, 960, G + 6, 200, pot=False, star=False, snowy=0.6)
    xs = {"digger": 560, "sprout": 720, "wheels": 400, "teeth": 1210, "tentacles": 1380, "springs": 1560,
          "lantern": 240}
    for kd, x in xs.items():
        keeper(pg, kd, x, attend=0.3)
    say(pg, 760, G - 330, "dots")
    return "A little fir is growing right on the path where everyone walks"


def potting(pg):
    scene(pg, 0.1)
    fir(pg, 900, G - 40, 200, pot=False, soil_ball=True, star=False, snowy=0.4)    # lifted, soil and all
    keeper(pg, "digger", 760, attend=0.2, arm_to={1: (850, G - 60)})
    keeper(pg, "sprout", 1120, can=True, attend=0.3)
    pg.shape(smooth([(1000, G - 70), (1090, G - 70), (1075, G), (1015, G)]), POT, 0.12)        # the pot, ready
    keeper(pg, "tentacles", 1450, attend=0.5)
    return "Digs lifts it out with its ball of soil, so nobody steps on it; Sprout has a pot ready"


def ornaments(pg):
    scene(pg, 0.35, path=False)
    lantern(pg, 960, G - 150, True, post=0)
    workbench(pg, 620, 1300, G)
    keeper(pg, "teeth", 720, attend=0.1, blades=1.0, arm_to={1: (830, G - 175)})
    pg.shape(star_path(840, G - 180, 26), WOOD, 0.1)
    for i in range(5):                                                       # curly shavings
        pg.flat(oval(800 + i * 14, G - 140 + (i % 2) * 6, 7, 3, rot=30 * i), "#e6c48e")
    keeper(pg, "wheels", 1180, attend=0.1, arm_to={-1: (1080, G - 172)})
    pg.shape(tube([(1075, G - 195), (1052, G - 168)], 5, 4), "#8a6450", 0.0)           # his brush
    pg.flat(oval(1050, G - 166, 6, 6), RED)
    for i, c in enumerate((RED, GOLD, RED)):
        pg.shape(oval(1000 + i * 40, G - 172, 14, 14), c, 0.12)
    keeper(pg, "tentacles", 330, attend=0.2)
    pth = skia.Path()
    pth.moveTo(200, G - 105)
    pth.quadTo(330, G - 40, 460, G - 95)
    pg.stroke(pth, "#b98d56", 9)
    for i in range(6):
        pg.flat(oval(225 + i * 44, G - 92 + 22 * math.sin(math.pi * i / 5), 9, 6, rot=40), "#7e9a5e")
    keeper(pg, "springs", 1520, attend=0.3)
    pth = skia.Path()
    pth.moveTo(1410, G - 130)
    pth.quadTo(1520, G - 60, 1640, G - 120)
    pg.stroke(pth, "#d8c8a8", 2)
    for i in range(11):
        u = i / 10
        bx = 1410 + 230 * u
        by = (1 - u) ** 2 * (G - 130) + 2 * u * (1 - u) * (G - 60) + u * u * (G - 120)
        pg.flat(oval(bx, by, 7, 7), BERRY)
    keeper(pg, "sprout", 1700, attend=0.3)
    return "Every Keeper makes something: Twigs carves, Wheels paints, Hans braids a garland, Springs threads berries"


def decorating(pg):
    scene(pg, 0.55, path=False)
    fir(pg, 960, G + 4, 300, orn=6, lights=0.0, star=False, garland=True, berries=True, ribbons=True)
    lantern(pg, 780, G - 140, False, post=140)
    lantern(pg, 1140, G - 140, True, post=140)
    pg.glow(1290, G - 200, 150, LAMP, 0.35)                                         # Glo's flare, from under his dome
    keeper(pg, "tentacles", 640, attend=0.2)
    pg.shape(oval(880, G - 150, 14, 14), RED, 0.12)                                 # the bauble he is hanging
    keeper(pg, "springs", 1240, dy=-200, spring=-0.4, attend=0.4)                  # bouncing up with the star
    pg.shape(star_path(1120, G - 400, 30), GOLD, 0.12)
    keeper(pg, "lantern", 1460, attend=0.3, lamp=1.8)
    keeper(pg, "sprout", 400, attend=0.4)
    return "Hans hangs them, Springs bounces up with the star, Glo's light flare lights the lanterns one by one"


def gust(pg):
    scene(pg, 0.95, path=False, snow=True)
    fir(pg, 960, G + 4, 300, orn=6, lights=0.0, star=False, garland=True, berries=True, ribbons=True, snowy=1.0,
        lean=-4.0)
    pg.shape(star_path(1250, G + 30, 26, rot=-60), GOLD, 0.12)                     # the star, in the snow
    for x in (780, 1140):
        lantern(pg, x, G - 140, False, post=140)
    keeper(pg, "springs", 1500, attend=0.6, smile=-0.6)
    keeper(pg, "sprout", 560, attend=0.6, smile=-0.5)
    keeper(pg, "digger", 1320, attend=0.2, lamp=1.8)                               # his hat lamp on, looking
    say(pg, 1560, G - 380, "dots")
    return "Christmas Eve: a gust shakes the fir, the star tumbles into the snow and the lanterns go out"


def christmas_eve(pg):
    scene(pg, 1.0, path=False, snow=True)
    fir(pg, 960, G + 4, 300, orn=6, lights=1.0, star=True, garland=True, berries=True, ribbons=True, snowy=0.5)
    for x in (780, 1140):
        lantern(pg, x, G - 140, True, post=140)
    for kd, x in (("sprout", 500), ("springs", 650), ("lantern", 1280), ("digger", 1430)):
        keeper(pg, kd, x, attend=0.5, smile=0.9)
    il.creature(pg, lambda cv: deer(cv, 1760, G + 30, 300, 0.0, face=-1, head_up=1.0), 1760, G + 30)
    il.creature(pg, lambda cv: fox(cv, 300, G + 30, 140, 0.0, face=1, sit=1.0), 300, G + 30)
    rabbit(pg, 1585, G + 30, 1.1, face=-1)
    il.creature(pg, lambda cv: chickadee(cv, 1140, G - 176, 70, 0.0, face=-1, fluff=1.0), 1140, G - 176)
    say(pg, 690, G - 330, "heart")
    return "The star goes back up, the lanterns glow again, and the winter animals come to see it"


def forever_home(pg):
    scene(pg, 0.0, path=False)
    pg.glow(1500, 260, 520, "#ffe2a0", 0.55)                                       # a bright winter morning sun
    pg.flat(oval(1500, 260, 70, 70), "#fbe3a6")
    pg.glow(1000, G - 100, 520, "#fff0c8", 0.25)                                   # the sunny clearing
    pg.flat(oval(1000, G + 8, 140, 18), SOIL, 0.6)
    fir(pg, 1000, G + 8, 240, pot=False, star=False)
    keeper(pg, "digger", 1220, attend=0.3)
    keeper(pg, "sprout", 820, can=True, water=1.0, attend=0.2)                    # its can pours onto the fir
    ornament_box(pg, 1540, G + 20)
    keeper(pg, "wheels", 1700, attend=0.4)
    return "After the holidays, the fir is planted in a sunny clearing; the ornaments go back in their box"


STILLS = [("0_flat_hook", hook), ("1_flat_potting", potting), ("2_flat_ornaments", ornaments),
          ("3_flat_decorating", decorating), ("4_flat_gust", gust), ("5_flat_christmas_eve", christmas_eve),
          ("6_flat_forever_home", forever_home)]


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    only = sys.argv[2:] or None
    for i, (name, fn) in enumerate(STILLS):
        if only and str(i) not in only:
            continue
        pg = flat.FlatPage(W, H, seed=3 + i)
        text = fn(pg)
        caption(pg.finish(), i, text).save(os.path.join(out, name + ".png"))
        print(name)
