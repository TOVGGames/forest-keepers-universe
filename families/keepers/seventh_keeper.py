"""Three ideas for a seventh Forest Keeper (owner 2026-11-03: "Maybe make a 7th keeper, what ideas does the instance
have"). Concept drawings only, in the new look and with the same helpers as the six (`monster.py`: carved body blob,
tree-ring grain, eyes, blush, smile, orb in a steel socket). Once the owner and Toby pick one, it moves into
`Monster` as a seventh kind with its parts, so the factory can build it piece by piece.

    draw_seventh(cv, kind, x, y, k, t, glow=None, **pose)     x, y = feet on the ground (Whirly floats above it)
"""
import math

import numpy as np

from engine.core import hex_rgb
from families.foundry.products.monster import (CLAW, LEAF, MOUTH, PALE, STEEL, WOOD, blob, blush, ellipse, eye, grain,
                                               orb, smile_mouth)
from families.foundry.style import lighten

IDEAS = {
    "sprout": dict(name="Sprout", color="#4c9f48", what="the gardener",
                   lines=["A little acorn Keeper, a seedling on top.",
                          "Plants a new tree for every branch",
                          "Twigs trims, and waters it."]),
    "whirly": dict(name="Whirly", color="#e2689a", what="the treetop helper",
                   lines=["Maple-seed wings on its head turn slowly,",
                          "so it floats gently up into the trees:",
                          "checks nests, frees stuck kites."]),
    "chime": dict(name="Chime", color="#e8dcc0", what="the music box",
                  lines=["A wind-up key, bluebell ears, and a lid",
                         "that opens on its turning tune.",
                         "Plays the theme song and lullabies."]),
}
BRASS = np.array([206, 164, 74], np.float64)
CAP = np.array([128, 92, 56], np.float64)
WATER = np.array([150, 200, 240], np.float64)
BELL = np.array([120, 136, 226], np.float64)


def _col(kind):
    return hex_rgb(IDEAS[kind]["color"]).astype(np.float64)


def _face(c, x, ey, my, ex, er, k, col, t, smile=0.7, look=(0.0, 0.12), glow=None, alive=1.0):
    for sx in (-1, 1):
        eye(c, x + sx * ex, ey, er, look, 1.0 if alive < 0.5 else 0.0, glow, alive, col, 0.0, 0.52, 0.0)
        blush(c, x + sx * (ex + er * 0.7), my - 12 * k, k, col, alive)
    smile_mouth(c, x, my, 30 * k, smile, 0.0, col, k, depth=1.0, awake=alive)


def _hand(c, hx, hy, ang, k, col, grip=0.0):
    """Little three-fingered wooden hand pointing along `ang`."""
    for f in (-1, 0, 1):
        a = ang + f * 0.36 * (1 - 0.5 * grip)
        L = (17 - 3 * abs(f)) * k * (1 - 0.4 * grip)
        c.line(hx, hy, hx + math.cos(a) * L, hy + math.sin(a) * L, col * 0.8, 7 * k)
        c.circle(hx + math.cos(a) * L, hy + math.sin(a) * L, 4 * k, col * 0.86)
    c.circle(hx, hy, 10 * k, col * 0.84)


# ----- Sprout: the gardener (acorn body, seedling on top, watering-can arm) -----

def seedling(c, x, y, k, t=0.0, ang=0.0):
    """Sprout's seedling: a little stem with two leaves, its root end at (x, y), leaning by `ang` (rad)."""
    sway = 0.08 * math.sin(t * 1.3) + ang
    ca, sa = math.cos(sway), math.sin(sway)
    q = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    top = q(6 * k, -56 * k)
    c.polyline([q(0, 0), q(2 * k, -26 * k), top], np.array([96, 150, 70]), 6 * k)
    for sx in (-1, 1):
        a = -math.pi / 2 + sx * 1.0 + sway
        lf = [(top[0], top[1]), (top[0] + math.cos(a - 0.35) * 26 * k, top[1] + math.sin(a - 0.35) * 26 * k),
              (top[0] + math.cos(a) * 46 * k, top[1] + math.sin(a) * 46 * k),
              (top[0] + math.cos(a + 0.35) * 26 * k, top[1] + math.sin(a + 0.35) * 26 * k)]
        c.polygon(lf, LEAF * 1.08)
        c.line(top[0], top[1], top[0] + math.cos(a) * 40 * k, top[1] + math.sin(a) * 40 * k, LEAF * 0.7, 2 * k)


def sprout(c, x, y, k, t, glow=None, water=1.0, walk=0.0, gait=0.0, alive=1.0, orb_in=1.0, flash=0.0,
           seed_on=True, acorn=True):
    """`alive` 0 = asleep and pale grey (orb out, as on the factory line), `seed_on` False = no seedling in the cap
    yet (a little hole where it goes)."""
    col = PALE * (1 - alive) + _col("sprout") * alive
    bob = 2 * math.sin(t * 2.0) * k
    by = y - 150 * k + bob
    for sx in (-1, 1):                                      # two short legs, root toes
        lift = walk * 14 * k * max(0.0, math.sin(gait + (sx > 0) * math.pi))
        lx = x + sx * 38 * k
        c.line(lx, by + 70 * k, lx + sx * 4 * k, y - 10 * k - lift, col * 0.74, 20 * k)
        for toe in (-1, 0, 1):
            c.line(lx + sx * 4 * k, y - 10 * k - lift, lx + sx * 4 * k + toe * 17 * k, y - 2 * k - lift,
                   col * 0.6, 7 * k)
    # left arm: a little hand holding an acorn
    sh = (x - 78 * k, by + 4 * k)
    hd = (sh[0] - 46 * k, sh[1] + 34 * k)
    c.line(*sh, *hd, col * 0.8, 14 * k)
    if acorn:
        c.circle(hd[0] - 6 * k, hd[1] - 12 * k, 11 * k, np.array([176, 120, 58]))
        c.polygon(ellipse(hd[0] - 6 * k, hd[1] - 18 * k, 12 * k, 7 * k, 20, math.pi, 2 * math.pi), CAP)
    _hand(c, *hd, -math.pi / 2 - 0.5, k, col, grip=0.7 if acorn else 0.2)
    # right arm: the watering-can spout, a sprinkler rose at the end
    sh = (x + 80 * k, by - 4 * k)
    el = (sh[0] + 52 * k, sh[1] + 10 * k)
    rose = (el[0] + 66 * k, el[1] + 26 * k)
    c.line(*sh, *el, col * 0.8, 16 * k)
    sp = [(el[0], el[1] - 12 * k), (rose[0], rose[1] - 6 * k), (rose[0], rose[1] + 6 * k), (el[0], el[1] + 12 * k)]
    c.polygon(sp, CLAW * 0.95)                              # a tin watering-can spout
    c.polyline(sp, CLAW * 0.6, 2, closed=True)
    c.line(el[0] + 4 * k, el[1] - 7 * k, rose[0], rose[1] - 3 * k, lighten(CLAW, 1.3), 2.5 * k)
    c.circle(*el, 13 * k, CLAW * 0.8)
    rx_, ry_ = rose[0] + 8 * k, rose[1] + 2 * k              # the rose: a round sprinkler head with holes
    c.polygon(ellipse(rx_, ry_, 11 * k, 20 * k, 24), CLAW * 0.95)
    c.polyline(ellipse(rx_, ry_, 11 * k, 20 * k, 24), CLAW * 0.6, 2, closed=True)
    c.polygon(ellipse(rx_ + 3 * k, ry_, 6 * k, 15 * k, 20), lighten(CLAW, 1.2))
    for hy_ in (-8, 0, 8):
        c.circle(rx_ + 4 * k, ry_ + hy_ * k, 1.8 * k, CLAW * 0.5)
    if water > 0:                                          # a soft shower of drops falling from the rose
        for i in range(9):
            ph = (t * 0.9 + i * 0.37) % 1.0
            dx = rose[0] + 16 * k + (i % 3) * 9 * k + ph * 26 * k
            dy = rose[1] + (i % 3 - 1) * 9 * k + ph * ph * 120 * k
            c.polygon(ellipse(dx, dy, 2.6 * k, 4.2 * k, 12), WATER * (0.6 + 0.4 * (1 - ph)) * water + col * 0)
    # body: an acorn nut, a little point at the bottom
    pts = ellipse(x, by, 88 * k, 96 * k, 60)
    pts = [(px, py + max(0.0, py - by - 70 * k) * 0.55) for px, py in pts]
    blob(c, pts, col)
    grain(c, x, by + 54 * k, 54 * k, 24 * k, col)
    # the acorn cap with its scales, and the seedling growing out of the top
    cy = by - 74 * k
    cap = ellipse(x, cy + 6 * k, 98 * k, 46 * k, 40, math.pi, 2 * math.pi) + [(x + 96 * k, cy + 14 * k), (x - 96 * k, cy + 14 * k)]
    c.polygon(cap, CAP)
    for row in range(3):
        for j in range(-4 + row, 5 - row):
            sx_, sy_ = x + j * 21 * k, cy + 4 * k - row * 14 * k
            c.arc(sx_, sy_, 10 * k, 20, 160, CAP * 0.72, 2.5 * k)
    c.polyline(cap, CAP * 0.6, 2.5, closed=True)
    if seed_on:
        seedling(c, x, cy - 36 * k, k, t)
    else:                                                  # the little hole in the cap where it gets planted
        c.polygon(ellipse(x, cy - 37 * k, 9 * k, 4 * k, 16), CAP * 0.45)
    _face(c, x, by - 14 * k, by + 36 * k, 36 * k, 26 * k, k, col, t, glow=glow, alive=alive)
    orb(c, x, by + 72 * k, 14 * k, glow, alive, t, orb_in, flash)


# ----- Whirly: the treetop helper (maple-seed rotor, floats) -----

def whirly(c, x, y, k, t, glow=None, spin=0.35, lift=1.0):
    col = _col("whirly")
    by = y - (190 + 70 * lift) * k + 6 * math.sin(t * 1.2) * k
    c.polygon(ellipse(x, y - 4 * k, 70 * k * (1 - 0.25 * lift), 12 * k, 30), np.array([0, 0, 0]) * 0 + col * 0.18)   # shadow
    # two dangling legs with round feet
    for sx in (-1, 1):
        sw = 0.12 * math.sin(t * 1.5 + sx)
        top = (x + sx * 34 * k, by + 70 * k)
        ft = (top[0] + sx * 8 * k + sw * 30 * k, top[1] + 84 * k)
        c.line(*top, *ft, col * 0.74, 15 * k)
        c.polygon(ellipse(ft[0] + sx * 6 * k, ft[1] + 6 * k, 18 * k, 10 * k, 20), col * 0.62)
    # arms: one waves, one holds a little kite string
    for sx in (-1, 1):
        sh = (x + sx * 82 * k, by + 6 * k)
        wave = 0.5 + 0.2 * math.sin(t * 2.0) if sx < 0 else -0.1
        hd = (sh[0] + sx * 46 * k, sh[1] - wave * 60 * k + 20 * k)
        c.line(*sh, *hd, col * 0.8, 13 * k)
        _hand(c, *hd, math.atan2(hd[1] - sh[1], hd[0] - sh[0]), k, col)
    # body: round seed pod
    blob(c, ellipse(x, by, 90 * k, 84 * k, 56), col)
    grain(c, x, by + 46 * k, 54 * k, 22 * k, col)
    # mast + hub + two maple-seed wings turning (seen from the side: the far one behind, foreshortened)
    hub = (x, by - 104 * k)
    c.line(x, by - 76 * k, *hub, CLAW * 0.8, 9 * k)
    PAPER = np.array([214, 168, 120], np.float64) * 0.7 + col * 0.3
    blades = sorted(((spin * 2 * math.pi + i * math.pi) % (2 * math.pi) for i in (0, 1)),
                    key=lambda a: -math.sin(a))                # the far blade first
    for a in blades:
        L, d = 190 * k * math.cos(a), math.sin(a)
        far = d < 0
        tipx, tipy = hub[0] + L, hub[1] - 10 * k + d * 8 * k
        w = 32 * k
        wing = [(hub[0], hub[1] - 6 * k), (hub[0] + L * 0.35, hub[1] - w * 0.9), (hub[0] + L * 0.8, hub[1] - w * 1.05),
                (tipx, tipy - w * 0.55), (tipx + 6 * k * np.sign(L), tipy), (hub[0] + L * 0.7, hub[1] + 2 * k),
                (hub[0], hub[1] + 6 * k)]
        shade = 0.82 if far else 1.0
        c.polygon(wing, PAPER * shade)
        for v in (0.3, 0.5, 0.7):                          # fine veins fanning out from the seed
            c.line(hub[0] + L * 0.06, hub[1], hub[0] + L * (v + 0.18), hub[1] - w * (0.25 + v * 0.9),
                   PAPER * 0.72 * shade, 1.8 * k)
        c.polyline(wing, PAPER * 0.6 * shade, 2, closed=True)
        c.polygon(ellipse(hub[0] + L * 0.08, hub[1] - 2 * k, abs(L) * 0.09 + 6 * k, 12 * k, 20), CAP * shade)  # the seed
    c.circle(*hub, 9 * k, CLAW)
    c.circle(*hub, 4 * k, lighten(STEEL, 1.5))
    _face(c, x, by - 18 * k, by + 30 * k, 38 * k, 27 * k, k, col, t, glow=glow, look=(0.0, -0.1))
    orb(c, x, by + 62 * k, 14 * k, glow, 1.0, t)


# ----- Chime: the music box (wind-up key, bluebell ears, a window onto the turning tune) -----

def _rrect(cx, cy, w, h, r, n=8):
    pts = []
    for qx, qy, a0 in ((cx + w / 2 - r, cy - h / 2 + r, -math.pi / 2), (cx + w / 2 - r, cy + h / 2 - r, 0.0),
                       (cx - w / 2 + r, cy + h / 2 - r, math.pi / 2), (cx - w / 2 + r, cy - h / 2 + r, math.pi)):
        pts += [(qx + r * math.cos(a0 + u * math.pi / 2), qy + r * math.sin(a0 + u * math.pi / 2))
                for u in np.linspace(0, 1, n)]
    return pts


def chime(c, x, y, k, t, glow=None, play=1.0, key=0.3):
    col = _col("chime")
    bob = 2 * math.sin(t * 1.8) * k
    by = y - 150 * k + bob
    W, H = 210 * k, 176 * k
    for sx in (-1, 1):                                      # short legs on round music-box feet
        lx = x + sx * 60 * k
        c.line(lx, by + H / 2 - 10 * k, lx, y - 22 * k, col * 0.72, 18 * k)
        c.circle(lx, y - 16 * k, 17 * k, BRASS)
        c.circle(lx - 5 * k, y - 21 * k, 5 * k, lighten(BRASS, 1.35))
    # the wind-up key out of its right side, turning (its wings foreshortened by the turn)
    kx, ky = x + W / 2, by + 4 * k
    c.line(kx - 4 * k, ky, kx + 34 * k, ky, BRASS * 0.8, 9 * k)
    sp = abs(math.cos(key * 2 * math.pi)) * 0.8 + 0.2
    for sy in (-1, 1):
        wing = ellipse(kx + 44 * k, ky + sy * 22 * k * sp, 14 * k, 22 * k * sp, 24)
        c.polygon(wing, BRASS)
        c.polyline(wing, BRASS * 0.6, 2, closed=True)
    c.circle(kx + 44 * k, ky, 8 * k, BRASS * 0.85)
    # arms: little hands, one turning nothing in particular, both relaxed
    for sx in (-1, 1):
        if sx > 0:
            sh = (x + W / 2 - 8 * k, by + 46 * k)
        else:
            sh = (x - W / 2 + 8 * k, by + 20 * k)
        hd = (sh[0] + sx * 34 * k, sh[1] + 40 * k)
        c.line(*sh, *hd, col * 0.78, 13 * k)
        _hand(c, *hd, math.atan2(hd[1] - sh[1], hd[0] - sh[0]), k, col)
    # bluebell ears on stems from the sides, the bells hanging and swaying
    for sx in (-1, 1):
        sw = 0.15 * math.sin(t * 1.4 + sx)
        st = (x + sx * (W / 2 - 4 * k), by - 52 * k)
        tip = (st[0] + sx * 44 * k, st[1] - 40 * k)
        c.polyline([st, (st[0] + sx * 30 * k, st[1] - 10 * k), tip], np.array([96, 150, 70]), 5 * k)
        bx, byy = tip[0] + sx * 8 * k + sw * 20 * k, tip[1] + 30 * k
        bell = [(bx - 16 * k, byy + 16 * k), (bx - 12 * k, byy - 10 * k), (bx, byy - 18 * k), (bx + 12 * k, byy - 10 * k),
                (bx + 16 * k, byy + 16 * k), (bx + 8 * k, byy + 12 * k), (bx, byy + 18 * k), (bx - 8 * k, byy + 12 * k)]
        c.line(*tip, bx, byy - 16 * k, np.array([96, 150, 70]), 3 * k)
        c.polygon(bell, BELL)
        c.polyline(bell, BELL * 0.62, 2, closed=True)
        c.circle(bx, byy + 18 * k, 3.5 * k, lighten(BRASS, 1.2))
    # the lid, hinged at the back and propped open behind the box, a little mirror inside
    top = by - H / 2
    lo = 1.0 if play > 0 else 0.0
    lid = [(x - W / 2 + 10 * k, top + 6 * k), (x + W / 2 - 10 * k, top + 6 * k),
           (x + W / 2 - 22 * k, top - 70 * k * lo), (x - W / 2 + 22 * k, top - 70 * k * lo)]
    c.polygon(lid, col * 0.8)
    c.polyline(lid, BRASS * 0.85, 4 * k, closed=True)
    if lo:
        c.polygon([(x - 50 * k, top - 14 * k), (x + 50 * k, top - 14 * k), (x + 46 * k, top - 56 * k),
                   (x - 46 * k, top - 56 * k)], np.array([150, 170, 186]))
        c.line(x - 30 * k, top - 22 * k, x - 10 * k, top - 48 * k, np.array([210, 222, 232]), 3 * k)
    # the box body, gold corner trims
    blob(c, _rrect(x, by, W, H, 34 * k), col, shade=0.8)
    for sx in (-1, 1):
        c.circle(x + sx * (W / 2 - 22 * k), by + H / 2 - 22 * k, 7 * k, BRASS * 0.9)
    # the open top: the brass drum turning, its pins plucking the steel comb
    c.polygon([(x - 78 * k, top + 6 * k), (x + 78 * k, top + 6 * k), (x + 74 * k, top + 34 * k),
               (x - 74 * k, top + 34 * k)], np.array([52, 40, 34]))
    c.polygon([(x - 70 * k, top + 10 * k), (x + 30 * k, top + 10 * k), (x + 30 * k, top + 24 * k),
               (x - 70 * k, top + 24 * k)], BRASS * 0.95)
    ph = t * 1.4 * play
    for i in range(10):                                     # pins on the turning drum
        u = (i * 0.37 + ph) % 1.0
        c.circle(x - 66 * k + i * 10.5 * k, top + 11 * k + u * 12 * k, 2.2 * k, lighten(BRASS, 1.5))
    for i in range(7):                                      # comb teeth, longer to one side
        px = x + 38 * k + i * 6 * k
        c.line(px, top + 10 * k, px, top + (31 - i * 2) * k, lighten(STEEL, 1.4), 3 * k)
    c.line(x - W / 2 + 6 * k, top + 36 * k, x + W / 2 - 6 * k, top + 36 * k, BRASS, 5 * k)
    _face(c, x, by - 6 * k, by + 34 * k, 42 * k, 26 * k, k, col, t, smile=0.6, glow=glow)
    orb(c, x, by + 66 * k, 13 * k, glow, 1.0, t)
    if play > 0:                                           # soft notes drifting up from the lid
        for i in range(3):
            ph2 = (t * 0.35 + i / 3) % 1.0
            nx = x + 90 * k + i * 26 * k + 22 * k * math.sin(ph2 * 5 + i)
            ny = by - H / 2 - 20 * k - ph2 * 160 * k
            a = play * (1 - ph2) * 0.95
            nc = BRASS * a + np.array([60, 74, 64]) * (1 - a)
            c.polygon(ellipse(nx, ny, 9 * k, 7 * k, 16), nc)
            c.line(nx + 8 * k, ny, nx + 8 * k, ny - 30 * k, nc, 3 * k)
            c.line(nx + 8 * k, ny - 30 * k, nx + 20 * k, ny - 22 * k, nc, 3 * k)


DRAW = {"sprout": sprout, "whirly": whirly, "chime": chime}


def draw_seventh(cv, kind, x, y, k=1.0, t=0.0, glow=None, **pose):
    DRAW[kind](cv, x, y, k, t, glow, **pose)
