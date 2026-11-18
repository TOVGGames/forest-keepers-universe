"""Storyboard stills for the factory-trip episode (docs/engines/forest_keepers_factory_trip.md): Twigs gets hands with
slide-out blades, and the machines build Sprout, the seventh Keeper. Composed in screen space from the real engine
parts (the Tune-Up hall's palette and machines, `Monster`, `seventh_keeper.sprout`, the chatter bubbles, the FK0008
name card); the real episode is built as acts after the owner OKs these.

    python families/keepers/factory_trip_board.py <out_dir>
"""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import cv2
import numpy as np

from engine.canvas import Canvas
from engine.core import FORMATS
from families.foundry.products.monster import CLAW, Monster, ellipse
from families.foundry.style import CABLE, FAR, FLOOR, IRON, MID, STEEL, lighten
from families.foundry.tree_monsters import HAZARD, INTERIOR, LAMP, SIGN_WARM, machine_block, rect
from families.keepers.bug_hunt import CARD, INK, PAPER, WOOD
from families.keepers.chatter import bubble
from families.keepers.seventh_keeper import CAP, IDEAS, seedling, sprout

W, H = 1920, 1080
BIN = np.array([64, 70, 66], np.float64)
PLANK = np.array([150, 112, 72], np.float64)
BARK = np.array([70, 52, 40], np.float64)
CANOPY = np.array([30, 52, 44], np.float64)
ACORN = np.array([176, 120, 58], np.float64)


def canvas():
    cv = Canvas(FORMATS["hd"], grain=0, vignette=0)
    cv.target = cv.img
    return cv


def mk(kind, K, x, y, **kw):
    m = Monster(kind, K)
    m.newlook = True
    m.x, m.y = x, y
    m.alive, m.orb_in, m.flash, m.job, m.pin = 1.0, 1.0, 0.0, "keeper", 0.0
    m.smile, m.cheek, m.attend = 0.75, 0.0, 0.6
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def caption(cv, n, text):
    """Storyboard caption (only on these stills, not in the episode); n=0 is the opening hook."""
    label = f"{n}/5" if n else "Opening"
    w = (len(text) + len(label) - 3) * 15.5 + 120
    rect(cv, 960 - w / 2, 14, 960 + w / 2, 66, np.array([12, 14, 20]))
    cv.text(f"{label}   {text}", 960, 40, 28, np.array([226, 226, 214]))


def narrator(cv, lines, who="Narrator (Johanna), spoken over the opening:"):
    """What the narrator says, written out on the storyboard only (in the episode it is spoken, with an .srt)."""
    h = 54 + 44 * len(lines)
    w = max(len(t) for t in lines) * 16.5 + 110
    rect(cv, 960 - w / 2, H - 30 - h, 960 + w / 2, H - 30, np.array([250, 244, 226]) * 0.94)
    cv.polyline([(960 - w / 2, H - 30 - h), (960 + w / 2, H - 30 - h), (960 + w / 2, H - 30), (960 - w / 2, H - 30)],
                np.array([120, 96, 70]), 3, closed=True)
    cv.text(who, 960, H - 30 - h + 28, 22, np.array([120, 96, 70]), weight="Medium")
    for i, t in enumerate(lines):
        cv.text(t, 960, H - 30 - h + 72 + 44 * i, 31, np.array([44, 36, 30]))


# ----- backdrops -----

def night_forest(cv, G, seed=2):
    rs = np.random.default_rng(seed)
    top, low = np.array([12, 18, 38.0]), np.array([34, 46, 74.0])
    for y in range(0, G + 1, 4):
        cv.img[y:y + 4] = (top + (low - top) * (y / G)).astype(np.uint8)
    for _ in range(90):
        cv.circle(rs.uniform(0, W), rs.uniform(0, G - 300), rs.uniform(1.0, 2.2), np.array([220, 226, 240]) * rs.uniform(0.5, 1))
    cv.circle(1640, 150, 54, np.array([238, 234, 210]))
    cv.circle(1622, 140, 54, top * 0.0 + np.array([20, 26, 48]))           # a crescent moon
    for x in np.arange(-40, W + 80, 90):                                    # far tree line
        hh = rs.uniform(260, 420)
        cv.circle(x, G - hh * 0.6, hh * 0.32, np.array([22, 34, 42]))
    rect(cv, 0, G, W, H, np.array([30, 40, 30]))
    cv.line(0, G, W, G, np.array([46, 60, 42]), 4)
    for _ in range(70):                                                     # grass tufts
        gx, gy = rs.uniform(0, W), rs.uniform(G + 10, H)
        for d in (-1, 0, 1):
            cv.line(gx, gy, gx + d * 6, gy - 12, np.array([44, 62, 40]), 2)


def big_tree(cv, x, G, h=760, branch=None):
    """A big tree trunk with a canopy; `branch` = (x0, y0, x1, y1) a low dead branch sticking out."""
    cv.polygon([(x - 60, G), (x + 60, G), (x + 40, G - h), (x - 40, G - h)], BARK)
    cv.line(x - 20, G - 20, x - 26, G - h + 40, BARK * 0.8, 6)
    for q in range(7):
        a = q * 0.9
        cv.circle(x + 150 * math.cos(a) * (q % 3) / 2, G - h - 30 + 90 * math.sin(a), 170 + 20 * (q % 2), CANOPY * (0.9 + 0.05 * (q % 3)))
    if branch:
        x0, y0, x1, y1 = branch
        cv.line(x0, y0, x1, y1, BARK * 1.15, 14)
        cv.line(x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.6, x0 + (x1 - x0) * 0.7 + 20, y0 + (y1 - y0) * 0.7 - 34,
                BARK * 1.15, 7)


def factory(cv, G, signs=(), lamps=(260, 960, 1660), rail=150, behind=None):
    """The night-shift factory hall of the Tune-Up: back wall, pillars, the lamp row, the floor, the line and its
    rollers, station crossbeams with their signs, the orb trolley rail."""
    rect(cv, 0, 0, W, G, INTERIOR)
    for gx in np.arange(40, W, 340):
        rect(cv, gx, 0, gx + 26, G, FAR)
    cv.line(0, G - 430, W, G - 430, FAR, 9)
    rect(cv, 0, 0, W, 34, MID)
    for lx in lamps:
        cv.line(lx, 34, lx, 70, CABLE, 3)
        cv.polygon([(lx - 42, 100), (lx + 42, 100), (lx + 22, 70), (lx - 22, 70)], STEEL)
        cv.circle(lx, 104, 12, IRON * 1.2 + LAMP * 0.6)
        cv.polygon([(lx - 42, 104), (lx + 42, 104), (lx + 300, G), (lx - 300, G)], INTERIOR * 1.18 + LAMP * 0.03)
    cv.line(0, rail, W, rail, CABLE, 10)
    rect(cv, 0, G, W, H, FLOOR)
    cv.line(0, G, W, G, lighten(FLOOR, 1.9), 2)
    PY = G - 40
    rect(cv, 0, PY + 14, W, G + 24, IRON)
    cv.line(0, PY + 14, W, PY + 14, lighten(IRON, 1.5), 2)
    for rx in np.arange(0, W, 48):
        cv.circle(rx, PY + 30, 8, STEEL)
    cv.line(0, G + 100, W, G + 100, lighten(FLOOR, 1.3), 2)
    if behind is not None:                                     # hangs from the rail, behind the station signs
        behind(cv)
    for sx, name in signs:
        beam = rail + 70
        for px in (sx - 220, sx + 220):
            rect(cv, px - 10, beam, px + 10, PY + 10, STEEL * 0.55)
        rect(cv, sx - 230, beam - 20, sx + 230, beam + 4, STEEL * 0.7)
        machine_block(cv, sx - 120, beam - 76, sx + 120, beam - 24, IRON)
        cv.text(name, sx - 12, beam - 50, 30, SIGN_WARM * 0.8)
        cv.circle(sx + 98, beam - 50, 8, HAZARD)
    return PY


def pallet(cv, x, PY, K):
    w = 120 * K / 0.55
    rect(cv, x - w, PY, x + w, PY + 14, HAZARD * 0.55)


def trolley(cv, x, rail, orbs=1):
    machine_block(cv, x - 120, rail - 20, x + 120, rail + 50, STEEL)
    for wx in (-80, 80):
        cv.circle(x + wx, rail, 12, IRON)
    cv.text("ORBS", x, rail + 14, 26, SIGN_WARM * 0.75)
    for q in range(orbs):
        cx = x - 60 + q * 40
        cv.line(cx, rail + 50, cx, rail + 92, CABLE, 3)
        cv.polygon(ellipse(cx, rail + 92, 17, 10, 16, 0, math.pi), IRON * 1.3)
        cv.circle(cx, rail + 86, 13, np.array([110, 190, 255]) * 0.8)
        cv.circle(cx - 4, rail + 82, 4, np.array([230, 244, 255]))


def gripper(cv, gx, gy, rail, open_=1.0):
    cv.line(gx, rail + 10, gx, gy - 26, CABLE, 3)
    rect(cv, gx - 12, gy - 34, gx + 12, gy - 22, STEEL * 1.2)
    for sd in (-1, 1):
        cv.line(gx + sd * 8, gy - 24, gx + sd * (14 + 8 * open_), gy - 6, STEEL * 1.4, 4)
        cv.line(gx + sd * (14 + 8 * open_), gy - 6, gx + sd * (8 + 6 * open_), gy + 8, STEEL * 1.4, 4)


def arm_of(m, sx, t=0.0):
    """Twigs' (shoulder, elbow, wrist) on side sx, the same maths as Monster._draw_teeth."""
    k, a = m.k, m.alive
    sway = a * 4 * math.sin(t * 1.1) * k
    cy = m.y - 350 * k + sway * 0.3
    return m._teeth_arm(sx, t, m.x + sway, cy)


def name_card(cv, kind_draw, title, lines):
    """The FK0008 name card in screen space."""
    Wc, Hc = 1240, 210
    x0, y0 = 960 - Wc // 2, 1080 - 30 - Hc
    rect(cv, x0, y0, x0 + Wc, y0 + Hc, WOOD * 0.75)
    rect(cv, x0 + 8, y0 + 8, x0 + Wc - 8, y0 + Hc - 8, CARD)
    kind_draw(cv, x0 + 130, y0 + Hc - 20)
    cx = (x0 + 250 + x0 + Wc - 40) // 2
    cv.text(title, cx, y0 + Hc // 2 - 52, 58, INK)
    for q, ln in enumerate(lines):
        cv.text(ln, cx, y0 + Hc // 2 + 14 + q * 42, 34, INK * 1.25)


def acorn(cv, x, y, r=13, ang=0.0):
    cv.circle(x, y, r, ACORN)
    ca, sa = math.cos(ang), math.sin(ang)
    cap = [(x + (px * ca - py * sa), y + (px * sa + py * ca)) for px, py in
           ellipse(0, -r * 0.45, r * 1.05, r * 0.62, 20, math.pi, 2 * math.pi)]
    cv.polygon(cap, CAP)


# ----- the opening hook and the five stills -----

def hook(out):
    """The opening: the six Keepers set off through the night forest towards the factory's lit door on the hill, and
    the narrator says what's coming and names the one thing we only see at the very end."""
    cv = canvas()
    G = 840
    night_forest(cv, G, seed=5)
    hill = [(1180 + 740 * q, G - 230 * math.sin(math.pi * min(1, q * 1.15)) ** 0.7) for q in np.linspace(0, 1, 30)]
    cv.polygon(hill + [(W, G)], np.array([26, 36, 32]))
    DX, DY = 1500, G - 226                                     # the factory on the hilltop, its door lit from inside
    WARM = np.array([236, 178, 96.0])
    yy, xx = np.mgrid[0:H, 0:W]
    fall = np.exp(-((xx - DX) ** 2 + (yy - (DY - 70)) ** 2) / (2 * 190.0 ** 2))[..., None]
    cv.img[:] = np.clip(cv.img + fall * np.array([54, 40, 20.0]), 0, 255).astype(np.uint8)
    rect(cv, DX + 60, DY - 250, DX + 96, DY - 150, IRON * 0.8)       # its chimney, a soft curl of steam
    for q in range(4):
        cv.circle(DX + 84 + q * 14, DY - 274 - q * 30, 14 + q * 5, np.array([96, 104, 124]) * (1 - q * 0.12))
    cv.polygon([(DX - 170, DY + 8), (DX + 170, DY + 8), (DX + 170, DY - 150), (DX + 90, DY - 200), (DX + 10, DY - 150),
                (DX - 70, DY - 200), (DX - 150, DY - 150), (DX - 170, DY - 150)], IRON)      # a saw-tooth factory roof
    cv.polygon([(DX - 44, DY + 8), (DX + 44, DY + 8), (DX + 44, DY - 70), (DX, DY - 96), (DX - 44, DY - 70)], WARM)
    for wx in (DX - 120, DX + 92):
        rect(cv, wx, DY - 110, wx + 34, DY - 70, WARM * 0.85)
    rect(cv, DX - 160, DY + 8, DX + 160, DY + 14, IRON * 0.7)
    for i in range(10):                                         # the warm light spilling down the path from the door
        q = i / 9
        cv.circle(DX - 30 - 300 * q, DY + 20 + 196 * q ** 1.3, 9 - 4 * q, WARM * (0.55 - 0.3 * q))
    for kind, x, kw in (("digger", 1080, {}), ("springs", 900, {}), ("lantern", 720, {}),
                        ("teeth", 545, {"saws": True}), ("tentacles", 340, {}), ("wheels", 150, {})):
        m = mk(kind, 0.5, x, G + 10 - (70 * 0.5 if kind == "lantern" else 0), smile=0.8, attend=0.0, **kw)
        m.draw(cv, 0.0)
    caption(cv, 0, "The Keepers set off for the factory; the narrator names what we only see at the end")
    narrator(cv, ["Tonight the Forest Keepers go back to the night-shift factory.",
                  "And at the very end, a brand-new Keeper plants its very first tree."])
    cv2.imwrite(out, cv.img[:, :, ::-1])


def still_1(out):
    """The village at night: Twigs has trimmed the dead branches, but his wrist saws can't pick up an acorn to plant."""
    cv = canvas()
    G = 880
    night_forest(cv, G)
    big_tree(cv, 140, G, 820)
    for q in range(4):                                         # the branches he trimmed, in a neat pile
        cv.line(980 - q * 10, G - 8 - q * 9, 1150 + q * 8, G - 16 - q * 9, BARK * (1.1 + 0.05 * q), 10)
    m = mk("teeth", 0.85, 760, G, saws=True, smile=-0.3, brow=-0.7, attend=0.0)
    sh, el, hd = arm_of(m, 1)
    acorn(cv, hd[0] + 40, G - 20, 20)
    acorn(cv, hd[0] + 170, G - 20, 20, 0.9)                       # one rolled away when the saw nudged it
    for q in range(3):
        cv.line(hd[0] + 104 + q * 4, G - 34 + q * 12, hd[0] + 140 + q * 4, G - 34 + q * 12, np.array([120, 134, 126]), 3)
    m.draw(cv, 0.0)
    bubble(cv, m.x + 220, m.y - 650 * m.k - 10, 52, "?", m.full, 1.0, (m.x + 120, m.y - 600 * m.k))
    w = mk("wheels", 0.85, 420, G, smile=0.5)
    w.draw(cv, 0.0)
    g = mk("lantern", 0.85, 1400, G - 70, smile=0.8)
    g.draw(cv, 0.0)
    bubble(cv, g.x + 140, g.y - 380 * g.k - 50, 58, "sparkle", g.full, 1.0, (g.x + 40, g.y - 360 * g.k))
    caption(cv, 1, "Twigs trims well, but his wrist saws can't pick up an acorn. Glo has an idea")
    cv2.imwrite(out, cv.img[:, :, ::-1])


def still_2(out):
    """The factory: Twigs asleep on the line (orb out, pale), his saws in the OLD bin, the FIT arm bringing his
    second new hand."""
    cv = canvas()
    G = 900
    PY = factory(cv, G, signs=[(560, "UNCLIP"), (1300, "FIT")])
    trolley(cv, 900, 150, orbs=1)
    # the OLD bin under UNCLIP, the two wrist saws peeking over its rim
    bx, by = 560, G - 60
    old = mk("teeth", 0.85, 0, 0, saws=True, alive=0.0)
    for q, sx in enumerate((-1, 1)):
        hd = (bx - 34 + q * 60, by - 8)
        old._wrist_saw(cv, hd, (hd[0] - 30 * sx, hd[1] + 40), sx)
    rect(cv, bx - 80, by, bx + 80, by + 90, BIN)
    cv.text("OLD", bx, by + 44, 24, SIGN_WARM * 0.5)
    pallet(cv, 1300, PY, 0.85)
    m = mk("teeth", 0.85, 1300, PY, hands=True, alive=0.0, orb_in=0.0, bare={1})
    m.draw(cv, 0.0)
    sh, el, hd = arm_of(m, 1)
    d = (70, -18)                                              # the new hand, just about to slide on
    piece_hd, piece_el = (hd[0] + d[0], hd[1] + d[1]), (el[0] + d[0], el[1] + d[1])
    m._twigs_hand(cv, piece_hd, piece_el, 1)
    ux, uy, nx, ny = m._blade_frame(piece_hd, piece_el, 1)
    mx = (piece_el[0] + piece_hd[0]) / 2 + nx * 13 * m.k + ux * 14 * m.k
    my = (piece_el[1] + piece_hd[1]) / 2 + ny * 13 * m.k + uy * 14 * m.k
    gripper(cv, mx, my + 6, 150, open_=0.0)
    g = mk("lantern", 0.85, 260, G - 40, smile=0.7)
    g.draw(cv, 0.0)
    caption(cv, 2, "At the factory: orb out, saws off into the OLD bin, the FIT arm brings the new hands")
    cv2.imwrite(out, cv.img[:, :, ::-1])


def still_3(out):
    """Sprout is built on the line, still pale and asleep; Twigs, awake with his new hands, plants the seedling in
    Sprout's cap."""
    cv = canvas()
    G = 900
    PY = factory(cv, G, signs=[(420, "FIT"), (1100, "PLANT")])
    trolley(cv, 1620, 150, orbs=1)
    FY = G + 60
    ks = 0.68
    pallet(cv, 1100, PY, 0.85)
    sprout(cv, 1100, PY, ks, 0.0, water=0.0, alive=0.0, orb_in=0.0, seed_on=False, acorn=False)
    h = mk("tentacles", 0.8, 260, FY, smile=0.8)
    h.draw(cv, 0.0)
    g = mk("lantern", 0.8, 620, FY - 70, smile=0.8)
    g.draw(cv, 0.0)
    t = mk("teeth", 0.95, 900, FY, hands=True, punch=1.0, grip=0.8, smile=0.9, brow=0.6, attend=0.0)
    sh, el, hd = arm_of(t, 1)
    ux, uy = hd[0] - el[0], hd[1] - el[1]
    L = math.hypot(ux, uy)
    hx, hy = hd[0] + ux / L * 12 * t.k, hd[1] + uy / L * 12 * t.k
    seedling(cv, hx + 4, hy + 18, ks)
    t.draw(cv, 0.0)
    w = mk("wheels", 0.8, 1520, FY, smile=0.9)
    w.draw(cv, 0.0)
    s = mk("springs", 0.8, 1780, FY, smile=0.9)
    s.draw(cv, 0.0)
    caption(cv, 3, "Sprout is built step by step, still asleep. Twigs's first job with hands: plant the seedling")
    cv2.imwrite(out, cv.img[:, :, ::-1])


def still_4(out):
    """The orb goes in: Sprout turns green and opens its eyes, the orb flashes the Forest Keeper badge, everyone
    cheers. The name card in screen space."""
    cv = canvas()
    G = 720
    PY = factory(cv, G, signs=[(1000, "ORB IN")], rail=150,
                 behind=lambda c: gripper(c, 1000, G - 40 - 290, 150, open_=1.0))   # back up after the orb went in
    trolley(cv, 1500, 150, orbs=0)
    FY = G + 60
    ks = 0.62
    pallet(cv, 1000, PY, 0.8)
    sprout(cv, 1000, PY, ks, 0.0, water=0.0, alive=1.0, orb_in=1.0, flash=0.85, acorn=False)
    for kind, x, kw in (("tentacles", 330, dict(smile=1.0)), ("lantern", 640, dict(smile=1.0)),
                        ("teeth", 790, dict(hands=True, punch=0.9, smile=1.0, brow=0.8)),
                        ("wheels", 1330, dict(punch=1.0, smile=1.0)), ("springs", 1560, dict(spring=0.4, smile=1.0)),
                        ("digger", 1755, dict(smile=1.0))):
        y = FY - 60 if kind == "lantern" else FY
        mk(kind, 0.72, x, y, **kw).draw(cv, 0.0)
    name_card(cv, lambda c, x, y: sprout(c, x, y, 0.5, 0.0, water=0.0, acorn=False),
              "Sprout", ["The seventh Forest Keeper, the gardener:", "plants a new tree for every branch Twigs trims."])
    caption(cv, 4, "The orb goes in: Sprout turns green, opens its eyes, and the orb flashes the Keeper badge")
    cv2.imwrite(out, cv.img[:, :, ::-1])


def still_5(out):
    """Back in the forest: Twigs slides a blade out and trims a dead branch, Sprout plants an acorn and waters it."""
    cv = canvas()
    G = 880
    night_forest(cv, G, seed=5)
    t = mk("teeth", 0.85, 470, G, hands=True, blades=1.0, blades_l=0.0, punch=1.0, smile=0.8, attend=0.0)
    tipx, tipy = t.blade_tip(1, 0.0)
    big_tree(cv, tipx + 230, G, 820, branch=(tipx + 200, tipy - 30, tipx - 10, tipy - 4))
    # the cut piece falling, a few sawdust flecks
    cv.line(tipx - 30, tipy + 60, tipx - 150, tipy + 120, BARK * 1.15, 12)
    for q in range(6):
        cv.circle(tipx + 6 - q * 5, tipy + 14 + q * 16, 2.5, np.array([214, 184, 140]))
    t.draw(cv, 0.0)
    ks = 0.72
    sx = 1180
    sprout(cv, sx, G, ks, 0.4, water=1.0, acorn=True)
    px = sx + 200 * ks + 60
    cv.polygon(ellipse(px, G + 2, 40, 9, 20), np.array([58, 44, 32]))           # the little planting hole, filled
    seedling(cv, px, G - 2, 0.32)
    w = mk("wheels", 0.85, 1640, G, smile=0.9)
    w.draw(cv, 0.0)
    for q, (fx, fy) in enumerate([(820, 520), (1020, 610), (1380, 470), (1500, 700), (300, 640)]):  # fireflies
        cv.circle(fx, fy, 5, np.array([230, 240, 150]) * 0.9)
        cv.circle(fx, fy, 11, np.array([60, 70, 50]))
        cv.circle(fx, fy, 4, np.array([250, 255, 190]))
    caption(cv, 5, "Home: Twigs slides a blade out to trim, Sprout plants a new tree and waters it")
    cv2.imwrite(out, cv.img[:, :, ::-1])


if __name__ == "__main__":
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    hook(os.path.join(d, "0_storyboard_hook.png"))
    print(os.path.join(d, "0_storyboard_hook.png"))
    for i, f in enumerate((still_1, still_2, still_3, still_4, still_5), 1):
        p = os.path.join(d, f"{i}_storyboard.png")
        f(p)
        print(p)
