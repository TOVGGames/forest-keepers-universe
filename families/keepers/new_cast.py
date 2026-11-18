"""Concept drawings for two new Forest Keepers characters (owner + Toby, 2026-11-14; docs/engines/forest_keepers_new_cast.md):

- Blossom, the new Keeper: pink cherry wood, feminine, a cherry flower on her head that shows how she feels
  (open = happy, half = curious, drooping = sad, a closed bud = sleepy or shy).
- Melody, the foreman of the night-shift factory: a rosewood music box with a crank, a lid that opens on a turning
  brass drum, and a conductor's baton. She runs the machines to her tune.

Concepts only, drawn with the same parts as the other Keepers (`monster.py` eyes, blush, smile, orb). Once the owner
and Toby approve a design, each becomes a `Monster` kind.

    blossom(cv, x, y, k, t, mood="happy", ...)      x, y = feet on the ground
    melody(cv, x, y, k, t, lid=0.0, crank=0.0, baton=0.0, play=0.0, ...)
"""
import math

import numpy as np

from families.foundry.products.monster import blob, blush, eye, orb, smile_mouth
from families.foundry.style import lighten
from families.keepers.seventh_keeper import _hand

PINK = np.array([236, 150, 178], np.float64)       # Blossom's cherry-wood body
HEM = np.array([222, 120, 156], np.float64)        # her bark-petal hem
BARK = np.array([132, 74, 82], np.float64)         # cherry bark: legs
PETAL = np.array([252, 214, 226], np.float64)      # the flower
PETAL_IN = np.array([242, 168, 196], np.float64)
GOLD = np.array([246, 204, 92], np.float64)
STEM = np.array([96, 150, 70], np.float64)
RIBBON = np.array([140, 196, 226], np.float64)

ROSE = np.array([186, 104, 112], np.float64)       # Melody's rosewood
INLAY = np.array([244, 226, 196], np.float64)
BRASS = np.array([214, 172, 82], np.float64)
DARK = np.array([92, 52, 58], np.float64)
BOW = np.array([248, 186, 206], np.float64)


def oval(cx, cy, rx, ry, rot=0.0, n=32):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        px, py = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + px * c - py * s, cy + px * s + py * c))
    return out


def rrect(cx, cy, w, h, r, rot=0.0, n=6):
    """Rounded rectangle centred on (cx, cy), turned by `rot` (rad) about its centre."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0.0), (-1, 1, 0.5 * math.pi), (-1, -1, math.pi), (1, -1, 1.5 * math.pi)):
        ox, oy = qx * (w / 2 - r), qy * (h / 2 - r)
        for i in range(n + 1):
            a = a0 + 0.5 * math.pi * i / n
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + px * c - py * s, cy + px * s + py * c) for px, py in pts]


class Turned:
    """Draws onto canvas `c` turned by `ang` (rad) about (cx, cy): every point, circle centre and arc angle."""

    def __init__(self, c, cx, cy, ang):
        self.__dict__.update(_c=c, _cx=cx, _cy=cy, _co=math.cos(ang), _si=math.sin(ang), _deg=math.degrees(ang))

    def _p(self, x, y):
        dx, dy = x - self._cx, y - self._cy
        return self._cx + dx * self._co - dy * self._si, self._cy + dx * self._si + dy * self._co

    def polygon(self, pts, col):
        self._c.polygon([self._p(*q) for q in pts], col)

    def polyline(self, pts, col, width=2.0, closed=False):
        self._c.polyline([self._p(*q) for q in pts], col, width, closed)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self._c.line(*self._p(x0, y0), *self._p(x1, y1), col, width)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        self._c.circle(*self._p(x, y), r, col, fill, width)

    def arc(self, x, y, r, a0, a1, col, width=2.0):
        self._c.arc(*self._p(x, y), r, a0 + self._deg, a1 + self._deg, col, width)

    def __getattr__(self, name):
        return getattr(self._c, name)

    def __setattr__(self, name, value):                    # e.g. Glow sets .glowing on the real canvas
        setattr(self._c, name, value)


def taper(c, pts, w0, col, w1=0.6):
    """A stroke along `pts` that narrows from width w0 to w1 (a lash, a liner's wing)."""
    n = len(pts)
    left, right = [], []
    for i, (px, py) in enumerate(pts):
        qx, qy = pts[min(i + 1, n - 1)]
        ox, oy = pts[max(i - 1, 0)]
        dx, dy = qx - ox, qy - oy
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    c.polygon(left + right[::-1], col)


def _rim(cx, cy, sx, R, deg):
    """A point on a circle round the eye: deg 0 = the outer corner, 90 = the top, negative = below."""
    a = math.radians(deg)
    return cx + sx * R * math.cos(a), cy - R * math.sin(a)


def lid_drop(cx, cy, er, x0, top):
    """How far down the upper eyelid has come at x = x0, measured from the top of the eye there (0 = eye open).
    Same lid as monster.eye(): its edge is yc + 0.12 r (1 - u^2), yc = y - r + 2 r min(top, 0.95)."""
    if top <= 0.01:
        return 0.0
    dx = min(abs(x0 - cx), 0.98 * er)
    rim_y = cy - math.sqrt(er * er - dx * dx)
    lid_y = cy - er + 2 * er * min(top, 0.95) + 0.12 * er * (1 - (dx / er) ** 2)
    return max(0.0, lid_y - rim_y)


def _lash(c, cx, cy, sx, R, deg, L, w, k, curl=0.0, col=None, drop=0.0):
    """One lash growing out from the rim at `deg`: outward, leaning to the outer corner, bending by `curl`;
    `drop` moves it down with a lowered eyelid."""
    col = DARK if col is None else col
    pts = []
    for i in range(7):
        u = i / 6
        d = deg - 14 - 26 * curl * u * u                    # leans out and curls round towards the outer side
        x0, y0 = _rim(cx, cy, sx, R, deg)
        y0 += drop
        a = math.radians(d)
        pts.append((x0 + sx * L * u * math.cos(a), y0 - L * u * math.sin(a) - curl * L * 0.35 * u * u))
    taper(c, pts, w * k, col, 0.8 * k)


LASHES = ["flick", "egyptian", "curl", "doll", "upper_lower"]


def lashes(c, cx, cy, er, sx, k, style, top=0.0):
    """Eyelash styles for Blossom (owner 2026-11-14: try a few). Everything grows OUT from just past the eye's rim
    (the flat eye is drawn r * 1.08 round), never over the eye itself."""
    R = er * 1.13
    if style == "flick":                                   # the owner's pick: three short lashes, top-outer corner
        R = er * 1.17                                      # owner round 4: half as far out as round 3's 1.21
        # owner round 4: the lashes go with the eyelid. As it lowers they ride down together (by the smallest lid
        # drop under them, so none ever dips below the lid's edge); as her eyes close they shrink away to nothing.
        fan = ((26, 13), (46, 14), (66, 11))
        drop = min(lid_drop(cx, cy, er, _rim(cx, cy, sx, R, d)[0], top) for d, _ in fan)
        f = min(1.0, max(0.0, (0.6 - top) / 0.25))         # full up to top 0.35, gone from 0.6 (sleepy, shut)
        if f <= 0.02:
            return
        for deg, L in fan:
            _lash(c, cx, cy, sx, R, deg, L * k * f, 4.6 * (0.4 + 0.6 * f), k, drop=drop)
    elif style == "egyptian":                              # a kohl liner round the top that sweeps into a wing
        pts = [_rim(cx, cy, sx, R - 1.5 * k, d) for d in range(172, 4, -8)]
        wing = [_rim(cx, cy, sx, R - 1.5 * k, 4)]
        ox, oy = wing[0]
        for i in range(1, 7):
            u = i / 6
            wing.append((ox + sx * 34 * k * u, oy - 20 * k * u * u - 2 * k * u))
        taper(c, pts + wing[1:], 3.2 * k, DARK, 5.5 * k)
        tail = [_rim(cx, cy, sx, R - 1.5 * k, d) for d in range(-62, 0, 8)]
        tail.append((tail[-1][0] + sx * 22 * k, tail[-1][1] - 3 * k))
        taper(c, tail, 1.6 * k, DARK, 3.6 * k)
    elif style == "curl":                                  # two big curly lashes, cartoon style
        for deg, L in ((40, 20), (64, 18)):
            _lash(c, cx, cy, sx, R, deg, L * k, 5.2, k, curl=1.0)
    elif style == "doll":                                  # a thin lash line round the top, five little lashes
        taper(c, [_rim(cx, cy, sx, R - 2 * k, d) for d in range(160, 8, -8)], 2.2 * k, DARK, 3.4 * k)
        for deg in (18, 36, 54, 72, 90):
            _lash(c, cx, cy, sx, R, deg, (10 - 0.04 * deg) * k, 3.6, k)
    elif style == "upper_lower":                           # two short ones on top, two tiny ones underneath
        for deg, L in ((30, 12), (54, 11)):
            _lash(c, cx, cy, sx, R, deg, L * k, 4.2, k)
        for deg in (-24, -46):
            a = math.radians(deg)
            x0, y0 = _rim(cx, cy, sx, R, deg)
            taper(c, [(x0, y0), (x0 + sx * 7 * k * math.cos(a - 0.3), y0 - 7 * k * math.sin(a - 0.3))], 3 * k, DARK,
                  0.8 * k)


def face(c, x, ey, my, ex, er, k, col, smile=0.7, look=(0.0, 0.1), top=0.0, cheek=0.0, talk=0.0, lash=None,
         frown=0.0):
    for sx in (-1, 1):
        eye(c, x + sx * ex, ey, er, look, 0.0, None, 1.0, col, top, 0.52, cheek)
        if lash:
            lashes(c, x + sx * ex, ey, er, sx, k, lash, top)
        blush(c, x + sx * (ex + er * 0.7), my - 12 * k, k, col, 1.0)
    if frown:                                              # a small downturned mouth
        c.arc(x, my + 16 * k, 20 * k, 228, 312, DARK, 5 * k)
    else:
        smile_mouth(c, x, my, 26 * k, smile, talk, col, k, depth=1.0, awake=1.0)


# ------------------------------------------------------------------ Blossom
MOODS = {   # bloom 0 bud .. 1 wide open, droop 0 up .. 1 hanging, the face to go with it
    "happy": dict(bloom=1.0, droop=0.0, smile=0.85, top=0.0, cheek=0.45, look=(0.0, 0.05), sparkle=1.0),
    "content": dict(bloom=1.0, droop=0.0, smile=0.7, top=0.0, cheek=0.0, look=(0.0, 0.08)),
    "curious": dict(bloom=0.55, droop=0.0, smile=0.35, top=0.0, cheek=0.0, look=(0.5, -0.25), tilt=0.12),
    "sad": dict(bloom=0.3, droop=1.0, smile=0.0, top=0.12, cheek=0.0, look=(-0.2, 0.6), frown=1.0),
    "sleepy": dict(bloom=0.0, droop=0.15, smile=0.2, top=0.62, cheek=0.0, look=(0.0, 0.3)),
}
SHINE = np.array([150, 196, 250], np.float64)          # her orb's blue light through the petals


def flower(c, x, y, k, bloom=1.0, droop=0.0, t=0.0, sparkle=0.0, glow=None, flash=0.0, job="keeper", wind=0.0):
    """Her cherry flower on a short stem whose root is at (x, y), with her orb as its centre (owner 2026-11-14).
    It opens from a bud and droops when she's sad; shut, the orb's blue light glows through the petals."""
    sway = 0.05 * math.sin(t * 1.4)
    bend = 2.7 * droop + sway - wind                        # the stem arcs over (sad); wind bends it back
    L = 50 * k
    pts, px, py = [(x, y)], x, y
    for i in range(1, 7):
        a = bend * i / 6
        px, py = px + math.sin(a) * L / 6 * (1 + 0.5 * droop), py - math.cos(a) * L / 6 * (1 + 0.5 * droop)
        pts.append((px, py))
    top = (px, py)
    c.polyline(pts, STEM, 8 * k)
    for sx in (-1, 1):                                     # two small leaves at the stem's foot
        a = -math.pi / 2 + sx * 1.15
        c.polygon(oval(x + math.cos(a) * 16 * k, y - 4 * k + math.sin(a) * 8 * k, 17 * k, 7 * k, a), STEM * 1.12)
    face_ang = bend                                        # the way the flower faces (0 = straight up)
    R = (44 + 24 * bloom) * k
    u = max(0.0, (bloom - 0.25) / 0.75)                    # how much of the centre shows
    shut = 1.0 - min(1.0, bloom / 0.45)                    # how much the light has to come through the petals
    orb_r = 15 * k * (0.7 + 0.3 * u)

    def centre():
        for j in range(10):                                # gold stamens round the orb
            a = j * math.pi / 5 + face_ang
            c.line(top[0], top[1], top[0] + math.cos(a) * 26 * k * u, top[1] + math.sin(a) * 26 * k * u, GOLD * 0.9,
                   2.6 * k)
            c.circle(top[0] + math.cos(a) * 26 * k * u, top[1] + math.sin(a) * 26 * k * u, 4 * k * u, GOLD)
        orb(c, top[0], top[1], orb_r, glow, 1.0, t, 1.0, flash, job)

    if bloom < 0.6:                                        # half shut: the orb sits down inside the petals
        centre()
    for i in range(5):
        # open: five petals round the centre; bud: all of them folded up together
        a_open = -math.pi / 2 + i * 2 * math.pi / 5
        a_bud = -math.pi / 2 + (i - 2) * 0.17
        a = a_bud + (a_open - a_bud) * bloom + face_ang
        pl = R * (0.62 + 0.38 * bloom) * (1.25 - 0.25 * bloom) * (1 + 0.35 * shut)
        pw = R * (0.30 + 0.22 * bloom) * (1 + 0.45 * shut)
        off = pl * (0.55 + 0.1 * bloom) - R * 0.25 * (1 - bloom)
        cx, cy = top[0] + math.cos(a) * off, top[1] + math.sin(a) * off
        col = PETAL * (0.9 + 0.1 * bloom) + PETAL_IN * (0.1 - 0.1 * bloom)
        col = col * (1 - 0.72 * shut) + SHINE * 0.72 * shut  # lit an even light blue from inside when shut
        c.polygon(oval(cx, cy, pl * 0.62, pw, a), col)
        tx, ty = cx + math.cos(a) * pl * 0.6, cy + math.sin(a) * pl * 0.6     # a cherry petal's little notch
        vein = PETAL_IN * (1 - shut) + col * 0.96 * shut       # shut, the veins go the same soft blue
        c.line(tx, ty, tx - math.cos(a) * 7 * k, ty - math.sin(a) * 7 * k, vein, 2.5 * k)
        c.line(cx - math.cos(a) * pl * 0.25, cy - math.sin(a) * pl * 0.25, cx + math.cos(a) * pl * 0.25,
               cy + math.sin(a) * pl * 0.25, vein * 0.98, 2 * k)
    if bloom >= 0.6:
        centre()
    if bloom <= 0.25:                                      # the bud's green cup
        c.polygon(oval(top[0] - math.sin(face_ang) * 6 * k, top[1] + math.cos(face_ang) * 6 * k, 20 * k, 12 * k,
                       face_ang), STEM * 1.05)
    if shut > 0 and glow is not None:                      # the soft blue glow through the shut petals
        pulse = 0.8 + 0.2 * math.sin(t * 1.6)
        glow.begin(c)
        c.polygon(oval(top[0] - math.sin(face_ang) * 24 * k, top[1] - math.cos(face_ang) * 24 * k, 40 * k, 58 * k,
                       face_ang), SHINE * 1.0 * shut * pulse)
        glow.end(c)
    if sparkle:                                            # happy: a few soft pollen sparkles
        for j, (dx, dy, r) in enumerate(((-84, -40, 5), (78, -62, 4), (92, 8, 3.5), (-56, -92, 3))):
            s_ = (0.6 + 0.4 * math.sin(t * 3 + j * 1.7)) * sparkle
            px, py = top[0] + dx * k, top[1] + dy * k
            c.line(px - r * 2 * k * s_, py, px + r * 2 * k * s_, py, GOLD, 2.2 * k)
            c.line(px, py - r * 2 * k * s_, px, py + r * 2 * k * s_, GOLD, 2.2 * k)


def star(c, x, y, r, col, k):
    """A little four-pointed glitter sparkle."""
    c.polygon([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28), (x, y + r),
               (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)], col)


def trail(c, hem, k, t, fly, dir=1):
    """What she sheds as she flies (owner 2026-11-14, round 3): glitter, a little when she flies, lots when she flies
    fast, plus a few tumbling petals when fast. No pollen. It comes off ALL ALONG her petal hem (`hem` = points on
    its bottom edge) and scatters, so it never reads as a single stream from one spot."""
    if fly <= 0:
        return
    fast = max(0.0, (fly - 0.5) / 0.5)
    n = int(4 + 46 * fly ** 1.5)                              # ~20 flying, ~50 flying fast
    white = np.array([255, 250, 236], np.float64)
    for i in range(n):
        h = (i * 0.38196601 + 0.13) % 1.0                         # where along the hem (spread, not in order)
        f = h * (len(hem) - 1)
        j = min(int(f), len(hem) - 2)
        ox = hem[j][0] + (hem[j + 1][0] - hem[j][0]) * (f - j)
        oy = hem[j][1] + (hem[j + 1][1] - hem[j][1]) * (f - j)
        ph = (t * (0.4 + 0.35 * fly) + i * 0.6180339) % 1.0       # each bit's age
        spread = math.sin(i * 2.71 + 1.3)                        # each one drifts its own way
        back = (10 + 190 * fly) * ph * k * (0.6 + 0.4 * abs(spread))
        fall = (14 + 46 * ph) * ph * k * (0.7 + 0.3 * math.cos(i * 1.9))
        px = ox - dir * back + spread * 22 * k * ph
        py = oy + fall + math.sin(i * 1.37 + 0.4) * 26 * k * ph   # and fans out up and down, a cloud, not a line
        fade = 1.0 - ph
        if fast > 0 and i % 4 == 3:                              # flying fast: a tiny cherry petal, tumbling
            c.polygon(oval(px, py, 8 * k * fast * (0.5 + 0.5 * fade), 4.5 * k * fast, t * 3 + i), PETAL * 0.96)
        else:                                                     # glitter
            col = (GOLD, white, PETAL_IN, lighten(SHINE, 1.05))[i % 4]
            tw = 0.75 + 0.25 * math.sin(t * 9 + i * 1.7)           # twinkle
            star(c, px, py, (3 + 3 * fly + 4 * fade) * k * tw, col, k)


def blossom(c, x, y, k, t=0.0, mood="happy", ribbon=True, wave=0.0, lash="flick", glow=None, fly=0.0, dir=1,
            flash=0.0, job="keeper"):
    """Blossom, round 2 (owner 2026-11-14): no legs, she floats over (x, y) and flies; her orb is the centre of
    her flower. `fly` 0 hovering .. 0.5 flying .. 1 flying fast (glitter, more of it and petals when fast), `dir` +1
    right. Lashes: "flick" (the owner's pick, round 3)."""
    m = MOODS[mood]
    gap = (36 + 8 * math.sin(t * 1.6) + 110 * fly) * k     # she floats, bobbing gently; higher when flying
    by = y - gap - 116 * k
    lean = 0.32 * fly * dir                                # leans into the way she flies
    tilt = m.get("tilt", 0.0)
    sh_x = math.sin(tilt)
    co, si = math.cos(lean), math.sin(lean)
    hem = []                                               # the bottom edge of her petal hem, turned with her
    for u in (-1.0, -0.5, 0.0, 0.5, 1.0):
        hx, hy = u * 66 * k, 108 * k + (1 - u * u) * 8 * k
        hem.append((x + hx * co - hy * si, by + hx * si + hy * co))
    if fly > 0.5:                                          # flying fast: a few soft swooshes behind her
        f = (fly - 0.5) / 0.5
        for j, dy in enumerate((-60, 10, 70)):
            y0 = by + dy * k
            x0 = x - dir * (110 + 20 * j) * k
            c.polyline([(x0 - dir * (i * 26 * k), y0 + 4 * k * math.sin(i * 0.9 + j)) for i in range(7)],
                       np.array([250, 244, 230]) * (0.97 + 0.03 * f), (5 - j) * k * f)
    trail(c, hem, k, t, fly, dir)
    real = c
    c = Turned(c, x, by, lean) if lean else c
    # arms: the left one waves (or rests); flying, both sweep back. The right one holds a ribbon spool
    sh = (x - 74 * k + sh_x * 10 * k, by + 8 * k)
    if wave:
        hd = (sh[0] - 40 * k, sh[1] - 56 * k * wave + 30 * k * (1 - wave))
        ang = -math.pi / 2 - 0.4
    else:
        hd = (sh[0] - 30 * k - 26 * k * fly * dir, sh[1] + 50 * k - 30 * k * fly)
        ang = math.pi / 2 + 0.3 + 0.8 * fly * dir
    c.line(*sh, *hd, PINK * 0.84, 13 * k)
    _hand(c, *hd, ang, k, PINK, grip=0.1)
    sh = (x + 74 * k + sh_x * 10 * k, by + 8 * k)
    hd = (sh[0] + 34 * k - 60 * k * fly * dir, sh[1] + 46 * k - 6 * k * fly)
    c.line(*sh, *hd, PINK * 0.84, 13 * k)
    if ribbon:                                             # her job: the finishing touches (a ribbon to tie a bow)
        pts = [(hd[0] + 8 * k + i * 7 * k, hd[1] + 10 * k + 14 * k * math.sin(i * 0.7 + t * 2) + i * 2.4 * k)
               for i in range(14)]
        c.polyline(pts, RIBBON, 7 * k)
        c.polygon(oval(hd[0] + 6 * k, hd[1] + 2 * k, 15 * k, 15 * k), RIBBON * 0.9)
        c.circle(hd[0] + 6 * k, hd[1] + 2 * k, 6 * k, lighten(RIBBON, 1.2))
    _hand(c, *hd, math.pi / 2 - 0.6 - 0.6 * fly * dir, k, PINK, grip=0.75 if ribbon else 0.1)
    # the body: a rounded cherry-wood drop over a hem of bark petals (no legs: the petals are her bottom)
    for i in range(7):
        u = (i - 3) / 3.0
        hx = x + u * 68 * k + sh_x * 8 * k
        hy = by + 76 * k + (1 - u * u) * 10 * k
        c.polygon(oval(hx, hy, 23 * k, 36 * k, u * 0.45 - 0.35 * fly * dir), HEM)
    blob(c, oval(x, by, 84 * k, 92 * k, tilt, 64), PINK)
    fx = x + sh_x * 40 * k
    face(c, fx, by - 14 * k, by + 34 * k, 34 * k, 25 * k, k, PINK, m["smile"], m["look"], m["top"], m["cheek"],
         lash=lash, frown=m.get("frown", 0.0))
    flower(c, x + sh_x * 92 * k, by - 88 * k, k, m["bloom"], m["droop"], t, m.get("sparkle", 0.0), glow, flash, job,
           wind=0.75 * fly * dir)
    del real


# ------------------------------------------------------------------ Melody
def note(c, x, y, k, col, beam=False):
    c.polygon(oval(x, y, 9 * k, 6.5 * k, -0.4), col)
    c.line(x + 7.5 * k, y - 2 * k, x + 7.5 * k, y - 34 * k, col, 3 * k)
    if beam:
        c.line(x + 7.5 * k, y - 34 * k, x + 31 * k, y - 40 * k, col, 6 * k)
        c.line(x + 31 * k, y - 40 * k, x + 31 * k, y - 8 * k, col, 3 * k)
        c.polygon(oval(x + 24 * k, y - 6 * k, 9 * k, 6.5 * k, -0.4), col)
    else:
        c.polyline([(x + 7.5 * k, y - 34 * k), (x + 18 * k, y - 24 * k), (x + 16 * k, y - 16 * k)], col, 3 * k)


def melody(c, x, y, k, t=0.0, lid=0.0, crank=0.0, baton=0.0, play=0.0, clipboard=True, glow=None, look=(0.0, 0.1),
           smile=0.75):
    """`lid` 0 shut .. 1 open on the turning drum, `crank` her crank's turn (rad), `baton` 0 down .. 1 raised to
    conduct, `play` 0..1 how many notes float up."""
    W, Hb = 210 * k, 172 * k
    bx, by = x, y - 70 * k - Hb / 2 + 2 * math.sin(t * 2.0) * k
    for sx in (-1, 1):                                     # two turned-wood legs with brass ball feet
        lx = x + sx * 56 * k
        c.line(lx, by + Hb / 2 - 6 * k, lx, y - 16 * k, ROSE * 0.72, 16 * k)
        c.polygon(oval(lx, by + Hb / 2 + 28 * k, 13 * k, 9 * k), ROSE * 0.8)          # the turned bead
        c.circle(lx, y - 12 * k, 13 * k, BRASS)
    # arms: the left holds a clipboard (the foreman's list), the right a baton
    sh = (bx - W / 2 + 4 * k, by + 10 * k)
    hd = (sh[0] - 34 * k, sh[1] + 50 * k)
    c.line(*sh, *hd, ROSE * 0.8, 12 * k)
    if clipboard:
        c.polygon(rrect(hd[0] - 6 * k, hd[1] - 26 * k, 54 * k, 70 * k, 5 * k, -0.15), np.array([176, 128, 84]))
        c.polygon(rrect(hd[0] - 6 * k, hd[1] - 22 * k, 44 * k, 56 * k, 3 * k, -0.15), INLAY * 1.02)
        for j in range(4):
            yy = hd[1] - 40 * k + j * 11 * k
            c.line(hd[0] - 22 * k + j * 1.6 * k, yy, hd[0] + 6 * k + j * 1.6 * k, yy - 4 * k, DARK * 1.3, 2.2 * k)
        c.polygon(rrect(hd[0] - 10 * k, hd[1] - 60 * k, 20 * k, 9 * k, 3 * k, -0.15), BRASS)
    _hand(c, *hd, math.pi / 2 + 0.5, k, ROSE, grip=0.7 if clipboard else 0.1)
    sh = (bx + W / 2 - 10 * k, by - 6 * k)
    up = baton
    hd = (sh[0] + 30 * k + 14 * k * up, sh[1] + 46 * k - 110 * k * up)
    c.line(*sh, *hd, ROSE * 0.8, 12 * k)
    ba = -0.35 - 0.9 * up + 0.15 * math.sin(t * 3) * up
    c.line(hd[0], hd[1], hd[0] + math.cos(ba) * 74 * k, hd[1] + math.sin(ba) * 74 * k, INLAY, 5 * k)
    c.circle(hd[0] + math.cos(ba) * 74 * k, hd[1] + math.sin(ba) * 74 * k, 4 * k, INLAY)
    _hand(c, *hd, ba, k, ROSE, grip=0.8)
    # the open lid (behind the box), tipped back on its hinge: we see its inside, a little oval mirror
    top = by - Hb / 2
    if lid > 0:
        h = 128 * k * lid
        c.polygon([(bx - W / 2 + 2 * k, top + 6 * k), (bx + W / 2 - 2 * k, top + 6 * k),
                   (bx + W / 2 - 12 * k, top - h), (bx - W / 2 + 12 * k, top - h)], ROSE * 0.82)
        c.polygon([(bx - W / 2 + 18 * k, top - 4 * k), (bx + W / 2 - 18 * k, top - 4 * k),
                   (bx + W / 2 - 26 * k, top - h + 14 * k), (bx - W / 2 + 26 * k, top - h + 14 * k)], INLAY * 0.95)
        c.polygon(oval(bx, top - h / 2 - 4 * k, 46 * k, h * 0.32), np.array([196, 214, 226]))
        c.line(bx - 18 * k, top - h / 2 - 20 * k * lid, bx + 4 * k, top - h / 2 + 2 * k, np.array([238, 244, 250]),
               4 * k)
    # the box: her body
    blob(c, rrect(bx, by, W, Hb, 26 * k), ROSE)
    c.polyline(rrect(bx, by + 6 * k, W - 24 * k, Hb - 34 * k, 18 * k), INLAY, 3 * k, closed=True)  # cream inlay line
    for j, (dx, dy) in enumerate(((-1, 1), (1, 1))):      # little carved flower inlays in the lower corners
        fx, fy = bx + dx * (W / 2 - 34 * k), by + Hb / 2 - 34 * k
        for i in range(5):
            a = i * 2 * math.pi / 5 - math.pi / 2
            c.polygon(oval(fx + math.cos(a) * 6 * k, fy + math.sin(a) * 6 * k, 6 * k, 4 * k, a), INLAY)
        c.circle(fx, fy, 3.5 * k, BRASS)
    if lid > 0:                                            # the drum turning in the open top
        c.polygon(rrect(bx, top + 2 * k, W - 30 * k, 22 * k, 8 * k), DARK)
        c.polygon(rrect(bx, top - 2 * k, W - 50 * k, 22 * k, 11 * k), BRASS * lid + DARK * (1 - lid))
        for i in range(11):
            px = bx - W / 2 + 36 * k + ((i * 13 + t * 40) % (W - 70 * k))
            c.circle(px, top - 2 * k + ((i * 7) % 3 - 1) * 5 * k, 2.2 * k, lighten(BRASS, 1.3))
    else:                                                  # shut: the lid sits on top, a bow on its corner
        c.polygon(rrect(bx, top - 6 * k, W + 10 * k, 26 * k, 11 * k), ROSE * 0.9)
        c.polygon(rrect(bx, top - 8 * k, W - 24 * k, 10 * k, 5 * k), INLAY * 0.9)
    bwx, bwy = bx - W / 2 + 26 * k, top - 14 * k           # her bow
    for sx in (-1, 1):
        c.polygon([(bwx, bwy), (bwx + sx * 28 * k, bwy - 16 * k), (bwx + sx * 30 * k, bwy + 14 * k)], BOW)
    c.circle(bwx, bwy, 8 * k, BOW * 0.88)
    c.circle(bx + W / 2 - 22 * k, top + 14 * k, 6 * k, BRASS)  # the keyhole plate
    c.circle(bx + W / 2 - 22 * k, top + 13 * k, 2 * k, DARK)
    face(c, bx, by - 22 * k, by + 22 * k, 40 * k, 25 * k, k, ROSE, smile, look, 0.0, 0.0)
    orb(c, bx, by + 64 * k, 12 * k, glow, 1.0, t)
    # the crank on her right side, low down: a brass shaft out of her side, an arm that turns, a wooden handle
    hx, hy = bx + W / 2 + 16 * k, by + 40 * k
    c.line(bx + W / 2 - 6 * k, hy, hx, hy, BRASS * 0.85, 11 * k)
    ex, ey = hx + 4 * k * math.cos(crank), hy + 36 * k * math.sin(crank)
    c.line(hx, hy, ex, ey, BRASS, 10 * k)
    c.circle(hx, hy, 10 * k, BRASS * 0.8)
    c.polygon(rrect(ex + 14 * k, ey, 32 * k, 17 * k, 8 * k), np.array([176, 128, 84]))
    c.circle(ex, ey, 6 * k, BRASS * 0.9)
    if play > 0:                                           # notes drifting up out of the open box
        for i in range(4):
            ph = (t * 0.35 + i * 0.25) % 1.0
            if ph > play + 0.05:
                continue
            nx = bx - 60 * k + i * 40 * k + 26 * k * math.sin(ph * 5 + i)
            ny = top - 40 * k - ph * 170 * k
            note(c, nx, ny, k * (0.9 + 0.2 * (i % 2)), DARK * (1.2 + 0.5 * ph), beam=i % 2 == 1)
