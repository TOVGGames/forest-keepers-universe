"""Storyboard stills for "Sprout's Christmas Tree" (docs/engines/forest_keepers_christmas.md), episode 14: nobody cuts a
tree down. A little fir is growing right on the path where everyone walks; Digs lifts it, soil and all, into a pot,
and Sprout looks after it. Twigs carves wooden ornaments, Wheels paints them, Hans hangs them, Springs puts the star
on top, Glo lights the little lanterns with a flare of light. On Christmas Eve the winter animals come to see it, and
after the holidays the fir gets its forever home in a sunny clearing. Composed in screen space from the real engine
parts (`Monster` with all seven Keepers, the field-guide animals, the FK0008 name-card style).

    python families/keepers/christmas_board.py <out_dir>
"""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import cv2
import numpy as np

from families.foundry.keepers.common import bunny
from families.foundry.products.monster import ellipse, lighten
from families.keepers.animals import deer, fox
from families.keepers.factory_trip_board import canvas, mk, narrator
from families.keepers.winter_animals import chickadee

W, H = 1920, 1080
SNOW = np.array([226, 232, 244.0])
SNOW_SH = np.array([176, 188, 214.0])
FIR = np.array([46, 110, 70.0])
FIR_D = np.array([32, 82, 54.0])
TRUNK = np.array([96, 70, 50.0])
POT = np.array([176, 98, 62.0])
SOIL = np.array([82, 60, 44.0])
WOODC = np.array([206, 160, 104.0])
RED = np.array([196, 70, 60.0])
GOLD = np.array([232, 186, 70.0])
LAMP = np.array([255, 214, 140.0])


def caption(cv, n, text):
    """Storyboard caption (only on these stills, not in the episode)."""
    label = f"{n}/5" if n else "Opening"
    w = (len(text) + len(label) + 3) * 15.5 + 80
    cv.polygon([(960 - w / 2, 14), (960 + w / 2, 14), (960 + w / 2, 66), (960 - w / 2, 66)], np.array([12, 14, 20.0]))
    cv.text(f"{label}   {text}", 960, 40, 28, np.array([226, 226, 214]))


def snowy_night(cv, G, seed=4, dawn=0.0):
    """Night sky with stars (or a pale winter morning when dawn = 1), a far snowy tree line, snow on the ground."""
    rs = np.random.default_rng(seed)
    top = np.array([12, 18, 40.0]) * (1 - dawn) + np.array([150, 176, 214.0]) * dawn
    low = np.array([40, 54, 88.0]) * (1 - dawn) + np.array([232, 214, 200.0]) * dawn
    for y in range(0, G + 1, 4):
        cv.img[y:y + 4] = (top + (low - top) * (y / G)).astype(np.uint8)
    if dawn < 0.5:
        for _ in range(90):
            cv.circle(rs.uniform(0, W), rs.uniform(0, G - 320), rs.uniform(1.0, 2.2), np.array([220, 226, 240]) * rs.uniform(0.5, 1))
    far = np.array([30, 48, 60.0]) * (1 - dawn) + np.array([110, 136, 150.0]) * dawn
    for x in np.arange(-40, W + 80, 74):
        hh = rs.uniform(220, 360)
        cv.polygon([(x - hh * 0.22, G), (x, G - hh), (x + hh * 0.22, G)], far)
        cv.polygon([(x - hh * 0.08, G - hh * 0.72), (x, G - hh), (x + hh * 0.08, G - hh * 0.72)], SNOW * (0.55 + 0.4 * dawn))
    cv.polygon([(0, G), (W, G), (W, H), (0, H)], SNOW * (0.82 + 0.15 * dawn))
    pts = [(x, G - 8 - 6 * math.sin(x / 140.0 + seed)) for x in np.linspace(0, W, 40)]
    cv.polygon(pts + [(W, G + 10), (0, G + 10)], SNOW * (0.9 + 0.1 * dawn))
    for _ in range(30):
        x, y = rs.uniform(0, W), rs.uniform(G + 30, H)
        cv.polygon(ellipse(x, y, rs.uniform(30, 90), rs.uniform(4, 9), 18), SNOW_SH * (0.85 + 0.15 * dawn))


def falling_snow(cv, n=80, seed=9, G=None):
    rs = np.random.default_rng(seed)
    for _ in range(n):
        cv.circle(rs.uniform(0, W), rs.uniform(0, H if G is None else G + 150), rs.uniform(2.0, 4.0),
                  np.array([236, 240, 250.0]) * rs.uniform(0.7, 1.0))


def glow(cv, x, y, r, col, k=1.0):
    yy, xx = np.mgrid[0:H, 0:W]
    fall = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r))[..., None] * k
    cv.img[:] = np.clip(cv.img + fall * np.asarray(col, np.float64), 0, 255).astype(np.uint8)


def fir(cv, x, yb, h, pot=True, lights=0.0, orn=0, star=False, snow=0.0, soil_ball=False):
    """The little fir: tiers of branches on a short trunk, in a clay pot (or with its ball of soil, or in the ground at
    yb). lights 0..1 = the little lanterns lit; orn = how many ornaments are on; star = the wooden star on top."""
    base = yb
    if pot:
        ph = h * 0.26
        cv.polygon([(x - h * 0.2, base - ph), (x + h * 0.2, base - ph), (x + h * 0.15, base), (x - h * 0.15, base)], POT)
        cv.polygon([(x - h * 0.22, base - ph - h * 0.05), (x + h * 0.22, base - ph - h * 0.05), (x + h * 0.22, base - ph),
                    (x - h * 0.22, base - ph)], lighten(POT, 1.12))
        cv.polygon(ellipse(x, base - ph - h * 0.05, h * 0.2, h * 0.025, 20), SOIL)
        base = base - ph - h * 0.05
    elif soil_ball:
        cv.polygon(ellipse(x, base - h * 0.06, h * 0.16, h * 0.09, 24), SOIL)
        base = base - h * 0.12
    th = h - (yb - base)
    cv.polygon([(x - th * 0.04, base), (x + th * 0.04, base), (x + th * 0.03, base - th * 0.2), (x - th * 0.03, base - th * 0.2)],
               TRUNK)
    tiers = [(0.14, 0.34, 0.5), (0.36, 0.28, 0.4), (0.56, 0.21, 0.3), (0.74, 0.14, 0.2)]
    spots = []
    for i, (y0, hw, tall) in enumerate(tiers):
        yt = base - th * y0
        tip = base - th * min(1.0, y0 + tall)
        pts = [(x - th * hw, yt), (x, tip), (x + th * hw, yt)]
        cv.polygon(pts, FIR if i % 2 == 0 else FIR * 1.06)
        cv.polygon([(x - th * hw, yt), (x, yt - th * 0.05), (x + th * hw, yt), (x, yt + th * 0.02)], FIR_D)
        if snow > 0:
            cv.polygon([(x - th * hw * 0.5, (yt + tip) / 2 + th * 0.03), (x, tip + th * 0.02),
                        (x + th * hw * 0.5, (yt + tip) / 2 + th * 0.03)], SNOW * 0.95)
        for u in (-0.6, 0.0, 0.6):
            spots.append((x + u * th * hw * 0.8, yt - th * 0.05 - abs(u) * 0.0))
    top = base - th * 0.94
    cols = [RED, GOLD, WOODC]
    for j, (sx, sy) in enumerate(spots[:orn]):
        if j % 3 == 2:                                       # a carved acorn
            cv.circle(sx, sy, th * 0.028, WOODC)
            cv.polygon(ellipse(sx, sy - th * 0.014, th * 0.03, th * 0.016, 16, math.pi, 2 * math.pi), lighten(WOODC, 0.7))
        else:                                                # a painted wooden bauble
            cv.circle(sx, sy, th * 0.03, cols[j % 2])
            cv.circle(sx - th * 0.01, sy - th * 0.01, th * 0.009, lighten(cols[j % 2], 1.4))
    if lights > 0:
        for j in range(14):
            u = (j * 0.37) % 1.0
            v = 0.15 + 0.75 * ((j * 0.61) % 1.0)
            ly = base - th * v
            hw = th * 0.34 * (1 - v) + th * 0.04
            lx = x + (u - 0.5) * 2 * hw * 0.8
            cv.circle(lx, ly, th * 0.014, LAMP * (0.5 + 0.5 * lights))
            glow(cv, lx, ly, th * 0.03, LAMP * 0.35 * lights)
    if star:
        r = th * 0.07
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((x + math.cos(a) * rr, top + math.sin(a) * rr))
        cv.polygon(pts, WOODC * 1.08 if lights <= 0 else GOLD)
        if lights > 0:
            glow(cv, x, top, r * 1.6, LAMP * 0.4 * lights)
    return top


def save(cv, path):
    cv2.imwrite(path, cv.img[:, :, ::-1])
    print(path)


# ----- the stills -----

def hook(out):
    """The opening: the seven Keepers in the snowy village find a little fir growing right on the path."""
    cv = canvas()
    G = 800
    snowy_night(cv, G)
    falling_snow(cv, 50)
    fir(cv, 1040, G + 10, 190, pot=False, snow=0.6)
    for kind, x, kw in (("wheels", 230, {}), ("tentacles", 470, {}), ("teeth", 700, {"hands": True}),
                        ("sprout", 900, {}), ("digger", 1250, {}), ("springs", 1460, {}), ("lantern", 1650, {})):
        y = G + 14 - (40 if kind == "lantern" else 0)
        mk(kind, 0.55, x, y, smile=0.8, attend=0.0, **kw).draw(cv, 0.0)
    glow(cv, 1650, G - 150, 220, LAMP * 0.25)
    caption(cv, 0, "A little fir is growing right on the path; the narrator names what we only see at the end")
    narrator(cv, ["It's nearly Christmas, and there's a little fir growing right where everyone walks.",
                  "And at the very end, the little tree gets its forever home in the forest."])
    save(cv, out)


def potting(out):
    """Digs lifts the little fir out with its ball of soil; Sprout holds the clay pot ready and waters it."""
    cv = canvas()
    G = 760
    snowy_night(cv, G, seed=6)
    falling_snow(cv, 40, seed=3, G=G)
    cv.polygon(ellipse(960, G + 16, 70, 16, 24), SOIL * 0.6)                 # the little hole it came out of
    d = mk("digger", 0.85, 760, G + 14, dig=0.9, smile=0.9, attend=0.0)
    d.draw(cv, 0.0)
    fir(cv, 930, G - 34, 210, pot=False, soil_ball=True, snow=0.3)           # lifted on Digs' shovels
    s = mk("sprout", 0.85, 1350, G + 14, smile=0.9, attend=0.0, can=True, water=0.0)
    s.acorn = False
    cv.polygon([(1130, G - 50), (1210, G - 50), (1200, G + 14), (1140, G + 14)], POT)   # the empty pot, waiting
    cv.polygon(ellipse(1170, G - 50, 40, 8, 20), SOIL)
    s.draw(cv, 0.0)
    caption(cv, 1, "Digs lifts the little fir out, soil and all, so nobody steps on it; Sprout has a pot ready")
    save(cv, out)


def ornaments(out):
    """Twigs carves wooden stars and acorns with his blade; Wheels paints them red and gold."""
    cv = canvas()
    G = 760
    snowy_night(cv, G, seed=8)
    cv.polygon([(560, G - 150), (1360, G - 150), (1360, G - 128), (560, G - 128)], WOODC * 0.7)     # the workbench
    for lx in (600, 1320):
        cv.polygon([(lx - 12, G - 128), (lx + 12, G - 128), (lx + 12, G + 14), (lx - 12, G + 14)], WOODC * 0.55)
    glow(cv, 960, G - 420, 300, LAMP * 0.22)
    cv.line(960, 0, 960, G - 470, np.array([60, 60, 66.0]), 3)
    cv.polygon([(930, G - 470), (990, G - 470), (996, G - 420), (924, G - 420)], LAMP * 0.8)       # a lantern
    t = mk("teeth", 0.8, 760, G + 14, hands=True, blades=1.0, blades_l=0.0, punch=0.55, grip=0.9, smile=0.8,
           attend=0.0)
    t.draw(cv, 0.0)
    tx, ty = t.blade_tip(1, 0.0)
    star = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = 26 if i % 2 == 0 else 12
        star.append((tx + 18 + math.cos(a) * rr, ty + 10 + math.sin(a) * rr))
    cv.polygon(star, WOODC)
    for q in range(5):                                       # curly shavings
        cv.circle(tx - 6 + q * 9, ty + 34 + (q % 2) * 10, 4, lighten(WOODC, 1.15))
    for j, (bx, col) in enumerate(((1040, RED), (1100, GOLD), (1160, WOODC), (1220, RED))):
        if col is WOODC:
            cv.circle(bx, G - 168, 16, WOODC)
            cv.polygon(ellipse(bx, G - 176, 18, 10, 16, math.pi, 2 * math.pi), lighten(WOODC, 0.7))
        else:
            cv.circle(bx, G - 168, 18, col)
            cv.circle(bx - 5, G - 173, 5, lighten(col, 1.4))
    w = mk("wheels", 0.8, 1180, G + 14, smile=0.9, punch=0.6, attend=0.0)
    w.draw(cv, 0.0)
    cv.line(1235, G - 260, 1235, G - 200, WOODC, 6)                            # the brush in his claw
    cv.polygon([(1227, G - 204), (1243, G - 204), (1240, G - 186), (1230, G - 186)], RED)
    caption(cv, 2, "Twigs carves stars and acorns with his new blade; Wheels paints them red and gold")
    save(cv, out)


def decorating(out):
    """Hans hangs the ornaments, Springs bounces up with the wooden star, Glo lights the lanterns with a flare."""
    cv = canvas()
    G = 780
    snowy_night(cv, G, seed=10)
    falling_snow(cv, 40, seed=5, G=G)
    top = fir(cv, 960, G + 14, 470, pot=True, orn=9, lights=0.0, star=False, snow=0.2)
    h = mk("tentacles", 0.75, 600, G + 14, smile=0.9, attend=0.0)
    h.work_tentacle(cv, 860, G - 230, 0.0, slot=1)
    h.draw(cv, 0.0)
    cv.circle(862, G - 214, 13, GOLD)
    s = mk("springs", 0.75, 1210, G - 240, spring=-0.4, smile=1.0, attend=0.0)
    s.draw(cv, 0.0)
    star = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = 34 if i % 2 == 0 else 15
        star.append((1092 + math.cos(a) * rr, G - 382 + math.sin(a) * rr))     # held up in Springs' hand
    cv.polygon(star, WOODC * 1.08)
    g = mk("lantern", 0.75, 1520, G - 60, smile=0.9, attend=0.0)
    g.draw(cv, 0.0)
    glow(cv, 1520, G - 230, 90, LAMP * 0.55)                                  # the flare, from under his dome
    glow(cv, 1250, G - 160, 250, LAMP * 0.18)
    caption(cv, 3, "Hans hangs the ornaments, Springs bounces up with the star, Glo's flare lights the little lanterns")
    save(cv, out)


def christmas_eve(out):
    """Christmas Eve: the little fir glows in the snow; a deer, a fox, a rabbit and a chickadee come to see it."""
    cv = canvas()
    G = 760
    snowy_night(cv, G, seed=12)
    falling_snow(cv, 60, seed=7, G=G)
    fir(cv, 960, G + 14, 430, pot=True, orn=9, lights=1.0, star=True, snow=0.3)
    glow(cv, 960, G - 160, 330, LAMP * 0.3)
    deer(cv, 1420, G + 20, 300, 0.0, face=-1, head_up=1.0)
    fox(cv, 1240, G + 26, 150, 0.0, face=-1, sit=1.0)
    bunny(cv, 700, G + 14, 2.0, 0.0, 1)
    chickadee(cv, 870, G - 330, 150, 0.0, face=1, fluff=1.0)
    for kind, x in (("wheels", 180), ("sprout", 400), ("teeth", 560)):
        mk(kind, 0.55, x, G + 14, smile=0.9, attend=0.0, hands=(kind == "teeth")).draw(cv, 0.0)
    for kind, x in (("digger", 1650), ("lantern", 1830)):
        mk(kind, 0.55, x, G + 14 - (40 if kind == "lantern" else 0), smile=0.9, attend=0.0).draw(cv, 0.0)
    caption(cv, 4, "Christmas Eve: the little tree glows, and the winter animals come to see it")
    save(cv, out)


def forever_home(out):
    """After the holidays, a winter morning: the fir is planted in a sunny clearing; Sprout waters it."""
    cv = canvas()
    G = 760
    snowy_night(cv, G, seed=14, dawn=1.0)
    cv.circle(1500, 220, 70, np.array([255, 236, 190.0]))
    glow(cv, 1500, 220, 200, np.array([90, 70, 30.0]))
    cv.polygon(ellipse(960, G + 18, 110, 22, 28), SOIL * 1.1)                 # the fresh soil round it
    fir(cv, 960, G + 18, 300, pot=False, snow=0.0)
    d = mk("digger", 0.8, 660, G + 14, dig=0.3, smile=0.9, attend=0.0)
    d.draw(cv, 0.0)
    s = mk("sprout", 0.8, 820, G + 14, smile=1.0, attend=0.0, can=True, water=1.0)
    s.acorn = False
    s.draw(cv, 0.0)
    cv.polygon([(1230, G - 40), (1350, G - 40), (1350, G + 14), (1230, G + 14)], WOODC * 0.7)        # the ornament box
    for j, col in enumerate((RED, GOLD, RED)):
        cv.circle(1255 + j * 35, G - 44, 13, col)
    for kind, x in (("teeth", 1480), ("springs", 1680)):
        mk(kind, 0.7, x, G + 14, smile=0.9, attend=0.0, hands=(kind == "teeth")).draw(cv, 0.0)
    caption(cv, 5, "After the holidays: the little fir gets its forever home in a sunny clearing")
    save(cv, out)


if __name__ == "__main__":
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    for name, f in (("0_storyboard_hook", hook), ("1_storyboard_potting", potting), ("2_storyboard_ornaments", ornaments),
                    ("3_storyboard_decorating", decorating), ("4_storyboard_christmas_eve", christmas_eve),
                    ("5_storyboard_forever_home", forever_home)):
        f(os.path.join(d, name + ".png"))
