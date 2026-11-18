"""Storyboard stills for the getting-ready-for-winter episode (docs/engines/forest_keepers_winter_ready.md), seven
Keepers now that Sprout has joined. Composed in screen space from the real engine parts, like FK0008's layout:
the counter and the name card in screen space, the animals from winter_animals.py.

    python families/keepers/winter_ready_board.py <out_dir>
"""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import cv2
import numpy as np

from engine.canvas import Canvas
from engine.core import FORMATS
from families.keepers.animals import F
from families.keepers.bug_hunt import PAPER, WOOD
from families.keepers.factory_trip_board import mk, name_card, narrator
from families.keepers.seventh_keeper import sprout
from families.keepers.winter_animals import WINTER, draw_winter

W, H = 1920, 1080
TRUNK = np.array([86, 62, 46.0])
GOLD, ORANGE, RED = np.array([226, 170, 64.0]), np.array([214, 118, 48.0]), np.array([176, 70, 44.0])
SKIES = {   # top, middle, low sky colours, the far tree line, the forest floor, how much the autumn colours dim
    "sunset": ([46, 54, 96], [150, 104, 120], [246, 172, 110], [92, 70, 88], [92, 66, 46], 1.0),
    "late": ([36, 40, 84], [116, 84, 118], [214, 132, 104], [72, 56, 78], [80, 58, 42], 0.85),
    "dusk": ([20, 24, 56], [60, 52, 96], [128, 86, 110], [44, 40, 62], [56, 44, 36], 0.6),
    "night": ([10, 14, 32], [22, 30, 58], [36, 46, 74], [22, 30, 42], [36, 34, 30], 0.42),
}


def canvas():
    cv = Canvas(FORMATS["hd"], grain=0, vignette=0)
    cv.target = cv.img
    return cv


def backdrop(cv, G, mode, seed=3, trees=((60, 900), (1860, 980)), sun=(1020, 300)):
    top, mid, low, far, floor, dim = (np.array(v, np.float64) if isinstance(v, list) else v for v in SKIES[mode])
    for y in range(0, G + 1, 4):
        q = y / G
        col = top + (mid - top) * min(1, q / 0.6) if q < 0.6 else mid + (low - mid) * ((q - 0.6) / 0.4)
        cv.img[y:y + 4] = col.astype(np.uint8)
    rs = np.random.default_rng(seed)
    if mode in ("dusk", "night"):
        for _ in range(60 if mode == "night" else 25):
            cv.circle(rs.uniform(0, W), rs.uniform(0, G - 360), rs.uniform(1.0, 2.0), np.array([220, 226, 240]) * rs.uniform(0.4, 0.9))
    elif sun:
        cv.circle(sun[0], G - sun[1], 70, np.array([255, 214, 150.0]) * (1.0 if mode == "sunset" else 0.92))
    for x in np.arange(-60, W + 80, 70):
        hh = rs.uniform(220, 360)
        cv.circle(x, G - hh * 0.62, hh * 0.3, far)
        cv.polygon([(x - 8, G), (x + 8, G), (x + 6, G - hh * 0.5), (x - 6, G - hh * 0.5)], far)
    for tx, th in trees:
        cv.polygon([(tx - 46, G), (tx + 46, G), (tx + 30, G - th * 0.6), (tx - 30, G - th * 0.6)], TRUNK * dim)
        for q in range(9):
            a = q * 0.7
            cv.circle(tx + 170 * math.cos(a) * (q % 3) / 2, G - th * 0.72 + 120 * math.sin(a), 150 + 30 * (q % 2),
                      (GOLD, ORANGE, RED)[q % 3] * (0.78 + 0.05 * (q % 3)) * dim)
    cv.polygon([(0, G), (W, G), (W, H), (0, H)], floor)
    cv.polygon([(0, G - 8), (W, G - 8), (W, G + 6), (0, G + 6)], floor * 1.3)
    for j in range(140):
        lx, ly = rs.uniform(0, W), rs.uniform(G - 4, H)
        col = (GOLD, ORANGE, RED)[j % 3] * rs.uniform(0.7, 0.95) * dim
        cv.polygon(F(lx, ly, 14).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]), col)


def counter(cv, n):
    cv.polygon([(40, 36), (520, 36), (520, 104), (40, 104)], WOOD * 0.8)
    cv.polyline([(40, 36), (520, 36), (520, 104), (40, 104)], WOOD * 0.5, 4, closed=True)
    cv.text(f"READY FOR WINTER  {n} / 6", 280, 70, 30, PAPER)


def card(cv, kind, s=230, **pose):
    d = WINTER[kind]
    name_card(cv, lambda c, x, y: draw_winter(c, kind, x - 10, y - 2, s, 0.0, **pose), d["name"], d["line"])


def geese(cv, x0, y0, s=70, spread=1.0):
    for k, (gx, gy) in enumerate([(0, 30), (-70, 0), (-140, -30), (-70, 65), (-140, 100), (-210, 135)]):
        draw_winter(cv, "goose", x0 + gx * spread, y0 + gy * spread + 40, s, 0.0, fly=1.0, flap=(0.15 + 0.17 * k) % 1)


def save(cv, path):
    cv2.imwrite(path, cv.img[:, :, ::-1])
    print(path)


# ----- the stills -----

def hook(out):
    """The opening at sunset: the seven Keepers set out under the first geese, counter at 0, and the narrator names
    the one thing we only see at the very end (the first snowflakes, kept out of every shot before the goodnight)."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "sunset", seed=7, sun=(960, 260))
    geese(cv, 1420, 170, 60, 0.9)
    for kind, x in (("wheels", 170), ("tentacles", 390), ("teeth", 610), ("lantern", 800), ("springs", 980),
                    ("digger", 1170)):
        mk(kind, 0.5, x, G + 10 - (70 * 0.5 if kind == "lantern" else 0), smile=0.85, attend=0.0).draw(cv, 0.0)
    sprout(cv, 1370, G + 10, 0.55, 0.0, water=0.0, acorn=True)
    counter(cv, 0)
    cv.polygon([(760, 20), (1160, 20), (1160, 66), (760, 66)], np.array([12, 14, 20.0]))   # storyboard label only
    cv.text("Opening (storyboard note)", 960, 43, 26, np.array([226, 226, 214]))
    narrator(cv, ["The days are getting shorter, and the forest is getting ready for winter.",
                  "How will each of our neighbours get ready?",
                  "And at the very end, watch for the very first snowflakes."])
    save(cv, out)


def chipmunk(out):
    """Find 1 at sunset: Sprout has gathered a pile of acorns by the chipmunk's burrow; geese go over."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "sunset")
    geese(cv, 1150, 140)
    BX = 1260
    cv.polygon(F(BX, G + 2, 1).pts([(-120, 0), (-80, 40), (0, 56), (90, 40), (130, 0)]), np.array([104, 76, 52.0]))
    cv.polygon(F(BX, G + 4, 1).pts([(-46, 0), (-30, 30), (0, 38), (30, 30), (46, 0), (0, -6)]), np.array([34, 24, 20.0]))
    cv.line(BX - 200, G - 20, BX - 40, G + 30, TRUNK * 0.9, 18)
    AC, CAP = np.array([170, 116, 56.0]), np.array([112, 78, 44.0])
    for ax, ay in [(1000, G + 14), (1040, G + 18), (1020, G - 2), (1080, G + 22), (1060, G + 2), (970, G + 26)]:
        cv.circle(ax, ay, 15, AC)
        cv.polygon(F(ax, ay - 6, 15).pts([(-1.05, 0), (-0.8, 0.6), (0, 0.85), (0.8, 0.6), (1.05, 0)]), CAP)
    draw_winter(cv, "chipmunk", BX + 110, G + 26, 230, 0.0, face=-1, pouch=1.0)
    sprout(cv, 760, G + 10, 0.85, 0.3, water=0.0, acorn=True)
    counter(cv, 1)
    card(cv, "chipmunk", pouch=1.0)
    save(cv, out)


def beaver(out):
    """Find 2: Twigs trims a fallen branch with one blade out, Wheels hauls the cut branches in his little cart, the
    beaver tows one to its lodge in the pond."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "sunset", seed=7, trees=((60, 900),), sun=(760, 280))
    # the pond and the lodge on the right
    cv.polygon([(1240, G + 4), (W, G + 4), (W, G + 150), (1300, G + 120)], np.array([70, 86, 120.0]))
    cv.line(1300, G + 40, 1600, G + 40, np.array([200, 170, 150.0]) * 0.55, 3)
    cv.line(1420, G + 80, 1800, G + 80, np.array([200, 170, 150.0]) * 0.5, 3)
    lodge = [(1560, G + 30), (1600, G - 70), (1680, G - 120), (1770, G - 110), (1850, G - 40), (1880, G + 30)]
    cv.polygon(lodge, np.array([98, 72, 50.0]))
    for q in range(12):
        x0 = 1580 + (q * 47) % 290
        y0 = G + 10 - (q * 31) % 120
        cv.line(x0, y0, x0 + 70, y0 - 18 + (q % 3) * 12, np.array([70, 50, 36.0]), 7)
    draw_winter(cv, "beaver", 1430, G + 20, 210, 0.0, face=1, walk=1.0, gait=0.6, branch=1.0)
    # a fallen tree leaning on a stump, the side branch being trimmed
    t = mk("teeth", 0.7, 330, G + 10, hands=True, blades=1.0, blades_l=0.0, punch=1.0, smile=0.8, attend=0.0)
    tx, ty = t.blade_tip(1, 0.0)
    cv.polygon([(450, G), (510, G), (500, G - 70), (460, G - 70)], TRUNK * 0.9)
    cv.line(250, G - 10, 980, ty + 40, TRUNK * 1.05, 34)
    cv.line(tx + 10, ty + 36, tx - 40, ty - 60, TRUNK * 1.1, 10)
    for q in range(5):
        cv.circle(tx - 2 - q * 4, ty + 10 + q * 14, 2.5, np.array([214, 184, 140]))
    t.draw(cv, 0.0)
    # Wheels with a little cart of cut branches, the rope in his claw
    w = mk("wheels", 0.8, 1070, G + 10, smile=0.9)
    cx0, cx1, cy = 760, 940, G - 40
    cv.polygon([(cx0, cy - 40), (cx1, cy - 40), (cx1 - 10, cy + 10), (cx0 + 10, cy + 10)], np.array([140, 100, 64.0]))
    for q in range(4):
        cv.line(cx0 - 20 + q * 8, cy - 50 - q * 9, cx1 + 10 - q * 6, cy - 56 - q * 9, TRUNK * (1.1 + 0.04 * q), 9)
    for wx in (cx0 + 40, cx1 - 40):
        cv.circle(wx, G - 20, 22, np.array([60, 46, 36.0]))
        cv.circle(wx, G - 20, 7, np.array([150, 158, 172.0]))
    cv.line(cx1, cy - 20, w.x - 190 * w.k, w.y - 250 * w.k, np.array([200, 180, 140.0]), 3)
    w.draw(cv, 0.0)
    counter(cv, 2)
    card(cv, "beaver", 210)
    save(cv, out)


def groundhog(out):
    """Finds 3 and 4: Springs bounces up to watch the geese fly south; Digs tidies the groundhog's burrow door."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "late", seed=11, trees=((1860, 980),), sun=(420, 230))
    geese(cv, 1500, 150, 76, 1.1)
    s = mk("springs", 0.85, 480, G - 70, spring=-0.4, smile=1.0, attend=0.0)
    cv.polygon([(410, G + 6), (550, G + 6), (540, G - 2), (420, G - 2)], np.array([0, 0, 0.0]) + 40)    # shadow
    s.draw(cv, 0.0)
    BX = 1180
    cv.polygon(F(BX, G + 6, 1).pts([(-170, 0), (-110, 56), (0, 84), (110, 56), (180, 0)]), np.array([104, 84, 54.0]))
    cv.polygon(F(BX - 70, G + 6, 1).pts([(-52, 0), (-38, 42), (0, 56), (38, 42), (52, 0)]), np.array([30, 22, 18.0]))
    for q in range(5):                                         # the little pile of old leaves Digs swept out
        cv.polygon(F(BX - 330 + q * 18, G + 4 - (q % 2) * 6, 16).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]),
                   (GOLD, ORANGE, RED)[q % 3] * 0.8)
    d = mk("digger", 0.85, 900, G + 10, dig=0.7, smile=0.9)
    d.draw(cv, 0.0)
    draw_winter(cv, "groundhog", BX + 60, G - 30, 230, 0.0, face=-1, sit=1.0)
    counter(cv, 4)
    card(cv, "groundhog", 210)
    save(cv, out)


def bear(out):
    """Find 5 at dusk: Hans holds a low branch aside with a tentacle and the bear ambles into its den."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "dusk", seed=5, trees=((60, 900),))
    DX = 1690                                                  # the den: a hollow under a rocky bank and a root
    cv.polygon([(1080, G + 4), (1180, G - 180), (1380, G - 260), (1640, G - 250), (1860, G - 140), (W, G - 60), (W, G + 4)],
               np.array([72, 66, 70.0]))
    cv.polygon([(1180, G - 180), (1380, G - 260), (1640, G - 250), (1560, G - 230), (1360, G - 236)], np.array([92, 86, 88.0]))
    cv.polygon(F(DX, G + 4, 1).pts([(-140, 0), (-112, 110), (0, 160), (112, 110), (140, 0)]), np.array([20, 16, 20.0]))
    cv.line(DX - 200, G - 190, DX + 120, G - 170, TRUNK * 0.7, 16)
    h = mk("tentacles", 0.8, 560, G + 10, smile=0.9, attend=0.0)
    bx0, by0, bx1, by1 = 700, G - 520, 1260, G - 290            # the low branch, lifted up out of the way
    cv.line(90, by0 - 150, bx1, by1 - 30, TRUNK * 0.75, 14)                # from the big tree on the left
    for q in range(5):                                         # its last autumn leaves
        lx, ly = bx0 - 60 + q * 120, by0 - 10 + q * 44
        for j in range(3):
            cv.polygon(F(lx + j * 22, ly + 18 + (j % 2) * 14, 18).pts([(0, 0), (0.6, 0.35), (1.2, 0), (0.6, -0.35)]),
                       (GOLD, ORANGE, RED)[(q + j) % 3] * 0.6)
    h.work_tentacle(cv, 980, G - 370, 0.0, slot=1)
    h.draw(cv, 0.0)
    draw_winter(cv, "bear", 1300, G + 18, 280, 0.0, face=1, walk=1.0, gait=0.4)
    counter(cv, 5)
    card(cv, "bear", 150, walk=1.0, gait=0.4)
    save(cv, out)


def goodnight(out):
    """Find 6 at night, the first snowflakes: Glo's soft light on the feeder, the chickadee fluffed up into a ball."""
    cv = canvas()
    G = 730
    backdrop(cv, G, "night", seed=13, trees=((60, 900), (1860, 980)))
    FX = 1180                                                  # the feeder on its post
    cv.line(FX, G + 10, FX, G - 330, TRUNK * 0.7, 14)
    cv.polygon([(FX - 110, G - 330), (FX + 110, G - 330), (FX + 100, G - 310), (FX - 100, G - 310)], np.array([120, 86, 56.0]))
    cv.polygon([(FX - 130, G - 420), (FX, G - 470), (FX + 130, G - 420), (FX + 120, G - 410), (FX, G - 456), (FX - 120, G - 410)],
               np.array([100, 70, 46.0]))
    for q in (-1, 1):
        cv.line(FX + q * 96, G - 420, FX + q * 96, G - 330, np.array([100, 70, 46.0]), 7)
    for q in range(14):
        cv.circle(FX - 80 + (q * 37) % 160, G - 336 - (q % 3) * 4, 4, np.array([214, 190, 140.0]))
    g = mk("lantern", 0.8, 820, G - 120, smile=0.9, attend=0.0)
    lx, ly = g.x, g.y - 260 * g.k + 82 * g.k
    yy, xx = np.mgrid[0:H, 0:W]                                # the soft lamp light reaching the feeder
    fall = np.exp(-((xx - lx) ** 2 + (yy - ly) ** 2) / (2 * 260.0 ** 2))[..., None]
    cv.img[:] = np.clip(cv.img + fall * np.array([90, 62, 30.0]), 0, 255).astype(np.uint8)
    g.draw(cv, 0.0)
    draw_winter(cv, "chickadee", FX + 10, G - 330, 170, 0.0, face=-1, fluff=1.0)
    for name, x in (("wheels", 340),):
        mk(name, 0.7, x, G + 10, smile=0.8, alive=1.0).draw(cv, 0.0)
    sprout(cv, 560, G + 10, 0.6, 0.0, water=0.0, acorn=False)
    rs = np.random.default_rng(4)
    for _ in range(70):                                        # the first snowflakes
        sx_, sy_ = rs.uniform(0, W), rs.uniform(0, G + 200)
        cv.circle(sx_, sy_, rs.uniform(2.0, 4.5), np.array([236, 240, 250.0]) * rs.uniform(0.7, 1.0))
    counter(cv, 6)
    card(cv, "chickadee", 230, fluff=1.0)
    save(cv, out)


if __name__ == "__main__":
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    for name, f in (("1b_storyboard_hook", hook), ("2_storyboard_chipmunk", chipmunk), ("3_storyboard_beaver", beaver),
                    ("4_storyboard_groundhog_geese", groundhog), ("5_storyboard_bear", bear),
                    ("6_storyboard_goodnight", goodnight)):
        f(os.path.join(d, name + ".png"))
