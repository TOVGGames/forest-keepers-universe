"""Halloween decorations the Forest Keepers make in episode 3 (docs/engines/foundry_keepers_halloween.md).

Every decoration can be drawn at each step of its making, so the factory can show anonymous parts
long before anyone can tell what they are:
  pumpkin  - turned wood ball -> sanded -> painted orange with rib stripes + stem -> carved face -> candle lit
  bat      - cast iron crescent (wing blank) -> stamped scalloped wing; little oval body; assembled bat
  ghost    - white cloth disc lying flat -> draped over a small ball -> ghost with eyes
  lights   - glass bulbs (orange / purple) on a wire that sags between its hooks
Side view, y down. Sizes in scene units.
"""
import math

import numpy as np

from ..style import lighten, smoothstep

ORANGE = np.array([236, 118, 28], np.float64)
ORANGE_DARK = np.array([178, 74, 16], np.float64)
STEM = np.array([92, 104, 46], np.float64)
WOOD = np.array([176, 136, 92], np.float64)          # turned, sanded wood
WOOD_RAW = np.array([132, 98, 66], np.float64)       # rough block
CARVED = np.array([46, 20, 10], np.float64)          # inside of the shell, unlit
FLAME = np.array([255, 214, 120], np.float64)
CANDLE_LIGHT = np.array([255, 170, 60], np.float64)
IRON_BAT = np.array([40, 38, 46], np.float64)
IRON_EDGE = np.array([116, 108, 140], np.float64)      # a cool rim so dark bats read against dark leaves
BAT_EYE = np.array([255, 214, 90], np.float64)
CLOTH = np.array([226, 228, 236], np.float64)
CLOTH_SHADE = np.array([178, 182, 198], np.float64)
GHOST_EYE = np.array([24, 24, 34], np.float64)
BULB_COLORS = [np.array([255, 140, 40], np.float64), np.array([170, 90, 255], np.float64)]
WIRE = np.array([40, 44, 40], np.float64)


def _ell(cx, cy, rx, ry, n=40, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in np.linspace(a0, a1, n, endpoint=a1 - a0 < 2 * math.pi - 1e-6)]


def flicker(t, seed=0.0):
    """Candle flicker 0.75..1.0, smooth and never periodic-looking."""
    return 0.86 + 0.07 * math.sin(t * 9.1 + seed) + 0.05 * math.sin(t * 13.7 + seed * 2.3) + 0.02 * math.sin(t * 23 + seed)


# ----------------------------------------------------------------- pumpkin

def pumpkin(cv, x, y, r, paint=1.0, carve=0.0, lit=0.0, t=0.0, glow=None, seed=0.0, sanded=1.0, stem=None,
            face=0, ribs=None):
    """(x, y) = bottom of the pumpkin. paint 0 = bare turned wood ball, 1 = orange. ribs 0..1 carves the
    pumpkin lobes in (default: with the paint), stem 0..1 pushes the stem in.
    carve 0..1 cuts the face in (eyes, nose, then the smile); lit 0..1 a candle glows inside."""
    rb = paint if ribs is None else ribs
    rx, ry = r * (1.0 + 0.14 * rb), r * (1.0 - 0.1 * rb)
    cy = y - ry
    base = WOOD * (1 - paint) + ORANGE * paint
    if sanded < 1:
        base = WOOD_RAW * (1 - sanded) + base * sanded
    # lobes, back to front: the outer ones darker
    # lobes, back to front: the outer ones darker; together they fill the outline exactly
    lobes = [(-0.45, 0.55, 0.72), (0.45, 0.55, 0.72), (-0.22, 0.76, 0.86), (0.22, 0.76, 0.86), (0.0, 0.6, 1.0)]
    if rb < 0.02:
        lobes = [(0.0, 1.0, 1.0)]
    for ox, wf, shade in lobes:
        k = 1.0 - (1.0 - shade) * rb
        lx, lw = x + ox * rx * rb, rx * (wf * rb + (1 - rb))
        cv.polygon(_ell(lx, cy, lw, ry * (1 - 0.04 * abs(ox) * rb), 44), base * k)
        if rb > 0.02 and ox != 0.0:
            cv.polyline(_ell(lx, cy, lw, ry * (1 - 0.04 * abs(ox) * rb), 44, -1.2, 1.2) if ox < 0 else
                        _ell(lx, cy, lw, ry * (1 - 0.04 * abs(ox) * rb), 44, math.pi - 1.2, math.pi + 1.2),
                        ORANGE_DARK * 0.85 * rb + base * 0.6 * (1 - rb), 2)
    if paint < 0.5:
        # turned wood: lathe rings
        for f in (0.35, 0.65, 0.9):
            cv.arc(x, cy, r * f, 200, 340, base * 0.82, 2)
    cv.polyline(_ell(x, cy, rx, ry, 48), base * 0.5, 2.5, closed=True)
    # highlight
    cv.polyline(_ell(x - rx * 0.2, cy - ry * 0.25, rx * 0.55, ry * 0.5, 16, 3.6, 4.6), lighten(base, 1.25), 3)
    st = paint if stem is None else stem
    if st > 0.02:
        sh = r * 0.38 * st
        cv.polygon([(x - r * 0.09, cy - ry + 4), (x + r * 0.09, cy - ry + 4), (x + r * 0.13, cy - ry - sh),
                    (x + r * 0.22, cy - ry - sh - r * 0.08), (x + r * 0.02, cy - ry - sh + r * 0.02)], STEM)
        cv.line(x, cy - ry + 2, x + r * 0.1, cy - ry - sh, STEM * 0.7, 2)
    if carve > 0:
        _face(cv, x, cy, rx, ry, carve, lit, t, glow, seed, face)


def _face(cv, x, cy, rx, ry, carve, lit, t, glow, seed, face):
    fl = flicker(t, seed) if lit > 0 else 1.0
    inside = CARVED * (1 - lit) + np.minimum(255, CANDLE_LIGHT * 1.25) * fl * lit
    hole = lighten(inside, 1.0)
    shapes = []
    # eyes: triangles (or round, face 1), nose, then the smile
    ey = cy - ry * 0.22
    for sx in (-1, 1):
        ex = x + sx * rx * 0.36
        if face == 1:
            shapes.append(_ell(ex, ey, rx * 0.13, ry * 0.15, 16))
        else:
            shapes.append([(ex - rx * 0.15, ey + ry * 0.12), (ex + rx * 0.15, ey + ry * 0.12), (ex + sx * rx * 0.03, ey - ry * 0.2)])
    shapes.append([(x - rx * 0.07, cy + ry * 0.06), (x + rx * 0.07, cy + ry * 0.06), (x, cy - ry * 0.07)])
    # smile: a crescent with two square teeth
    sm_y = cy + ry * 0.32
    top, bot = [], []
    for i in range(15):
        u = i / 14
        sx = x + (u - 0.5) * 2 * rx * 0.58
        curve = 1 - (2 * u - 1) ** 2
        top.append((sx, sm_y - ry * 0.06 + ry * 0.04 * curve))
        bot.append((sx, sm_y - ry * 0.06 + ry * (0.04 + 0.26 * curve)))
    smile = top + bot[::-1]
    shapes.append(smile)
    n = len(shapes)
    for i, pts in enumerate(shapes):
        u = smoothstep((carve * n - i) / 1.0)
        if u <= 0:
            continue
        p = np.asarray(pts)
        c0 = p.mean(axis=0)
        p = c0 + (p - c0) * u
        cv.polygon(p, hole)
        cv.polyline(p, ORANGE_DARK * 0.6, 2, closed=True)
    if carve > 0.98:
        # two teeth in the smile
        for tx in (-0.18, 0.18):
            bx = x + tx * rx
            cv.polygon([(bx - rx * 0.06, sm_y - ry * 0.04), (bx + rx * 0.06, sm_y - ry * 0.04),
                        (bx + rx * 0.06, sm_y + ry * 0.06), (bx - rx * 0.06, sm_y + ry * 0.06)], ORANGE * 0.95)
    if lit > 0 and glow is not None:
        glow.begin(cv)
        for pts in shapes:
            cv.polygon(pts, CANDLE_LIGHT * 1.0 * lit * fl)
        cv.circle(x, cy, rx * 1.3, CANDLE_LIGHT * 0.26 * lit * fl)
        glow.end(cv)


def wood_block(cv, x, y, r, u=0.0, t=0.0):
    """A square wood block (y = its bottom) being turned round on the lathe: u 0 block .. 1 ball."""
    pts = []
    for a in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        c, s = math.cos(a), math.sin(a)
        sq = 1.0 / max(abs(c), abs(s))                  # unit square in polar form
        rr = r * (sq * 0.92 * (1 - u) + u)
        pts.append((x + c * rr, y - r + s * rr))
    col = WOOD_RAW * (1 - u) + WOOD * u
    cv.polygon(pts, col)
    cv.polyline(pts, col * 0.55, 2.5, closed=True)
    if u > 0.1:
        for f in (0.4, 0.75):
            cv.arc(x, y - r, r * f, 200, 340, col * 0.82, 2)


def candle(cv, x, y, s=1.0, lit=0.0, t=0.0, glow=None, seed=0.0):
    """Stubby white candle, (x, y) = bottom."""
    w, h = 14 * s, 30 * s
    cv.polygon([(x - w, y), (x + w, y), (x + w, y - h), (x - w, y - h)], np.array([236, 226, 200]))
    cv.polygon(_ell(x, y - h, w, w * 0.35, 20), np.array([250, 244, 226]))
    cv.line(x, y - h, x, y - h - 8 * s, np.array([40, 34, 30]), 2)
    if lit > 0:
        fl = flicker(t, seed)
        fh = 22 * s * fl * lit
        cv.polygon([(x - 6 * s, y - h - 8 * s), (x + 6 * s, y - h - 8 * s), (x + 1.5 * s, y - h - 8 * s - fh)], FLAME * lit)
        cv.circle(x, y - h - 10 * s, 5 * s * lit, FLAME)
        if glow is not None:
            glow.begin(cv)
            cv.circle(x, y - h - 14 * s, 26 * s, CANDLE_LIGHT * 0.6 * lit * fl)
            glow.end(cv)


# ----------------------------------------------------------------- bat

def wing_points(x, y, s, side, scallop=1.0, flap=0.0, heat=0.0):
    """One bat wing, root at (x, y), spreading to `side` (+1 right / -1 left). scallop 0 = a smooth
    crescent blank (as cast), 1 = three scallops pressed into the trailing edge. flap -1..1 lifts it."""
    tip = (x + side * 92 * s, y - (34 + 38 * flap) * s)
    lead = []
    for i in range(9):                                  # leading edge: a soft arc up to the tip
        u = i / 8
        lead.append((x + side * u * 92 * s, y - 6 * s - math.sin(u * math.pi * 0.62) * (30 + 34 * flap) * s * (0.4 + 0.6 * u)
                     - u * u * 6 * s))
    lead[-1] = tip
    trail = []
    for i in range(1, 31):                              # trailing edge back to the root: scallops
        u = 1 - i / 30
        bx = x + side * u * 92 * s
        by = y + 26 * s * math.sin(u * math.pi) * (1 - 0.3 * flap) - (34 + 38 * flap) * s * u ** 2 + 12 * s * u
        sc = abs(math.sin(u * math.pi * 3)) * 14 * s * scallop
        trail.append((bx, by - sc))
    return lead + trail


def bat(cv, x, y, s=1.0, flap=0.0, t=0.0, glow=None, wings=1.0, body=1.0, eyes=1.0, scallop=1.0, face=1):
    """Little bat, centre of the body at (x, y). `wings`/`body`/`eyes` 0..1 for assembly."""
    if wings > 0:
        for side in (-1, 1):
            off = (1 - wings) * 80 * s * side
            pts = wing_points(x + side * 12 * s + off, y, s, side, scallop, flap)
            cv.polygon(pts, IRON_BAT)
            cv.polyline(pts, IRON_EDGE, 2.5, closed=True)
            # finger bones
            for f in (0.35, 0.65):
                cv.line(x + side * 14 * s + off, y - 4 * s, x + side * (14 + 80 * f) * s + off,
                        y + 10 * s - 30 * s * f - 30 * s * flap * f, IRON_EDGE * 0.8, 2)
    if body > 0:
        bs = s * (0.6 + 0.4 * body)
        cv.polygon(_ell(x, y + 4 * bs, 20 * bs, 28 * bs, 28), IRON_BAT)
        cv.polygon(_ell(x, y - 26 * bs, 18 * bs, 16 * bs, 24), IRON_BAT)
        for sx in (-1, 1):                               # ears
            cv.polygon([(x + sx * 6 * bs, y - 36 * bs), (x + sx * 18 * bs, y - 34 * bs), (x + sx * 16 * bs, y - 56 * bs)],
                       IRON_BAT)
        cv.polyline(_ell(x, y + 4 * bs, 20 * bs, 28 * bs, 28), IRON_EDGE, 2, closed=True)
        cv.polyline(_ell(x, y - 26 * bs, 18 * bs, 16 * bs, 24, math.pi, 2 * math.pi), IRON_EDGE, 2)
    if eyes > 0 and body > 0:
        for sx in (-1, 1):
            cv.circle(x + sx * 7 * s, y - 28 * s, 4.5 * s * eyes, BAT_EYE)
            cv.circle(x + sx * 7 * s, y - 28 * s, 2 * s * eyes, np.array([30, 20, 10]))
        if face:
            cv.arc(x, y - 22 * s, 5 * s, 20, 160, IRON_EDGE * 1.4, 2)
        if glow is not None:
            glow.begin(cv)
            for sx in (-1, 1):
                cv.circle(x + sx * 7 * s, y - 28 * s, 8 * s * eyes, BAT_EYE * 0.35)
            glow.end(cv)


def wing_blank(cv, x, y, s, side, heat=0.0, scallop=0.0):
    """A cast wing lying on the bench (or in its mould): flat crescent, glowing while hot."""
    pts = wing_points(x - side * 46 * s, y, s, side, scallop, 0.0)
    col = IRON_BAT * (1 - heat) + np.array([255, 120, 30]) * heat
    cv.polygon(pts, col)
    cv.polyline(pts, IRON_EDGE * (1 - heat) + np.array([255, 200, 120]) * heat, 2, closed=True)
    return pts


def body_blank(cv, x, y, s, heat=0.0):
    col = IRON_BAT * (1 - heat) + np.array([255, 120, 30]) * heat
    cv.polygon(_ell(x, y, 20 * s, 28 * s, 24), col)
    cv.polyline(_ell(x, y, 20 * s, 28 * s, 24), IRON_EDGE * (1 - heat) + np.array([255, 200, 120]) * heat, 2,
                closed=True)


# ----------------------------------------------------------------- ghost

def ghost(cv, x, y, s=1.0, drape=1.0, eyes=1.0, t=0.0, seed=0.0, sway=0.0, ball=True):
    """Friendly ghost, top of the head at (x, y - 0). drape 0 = flat cloth disc lying on a ball, 1 = ghost."""
    hr = 34 * s                                         # head (the small turned ball under the cloth)
    hx, hy = x + sway * 10 * s, y + hr
    if drape < 0.999 and ball:
        cv.circle(hx, hy, hr, WOOD)
    L = (40 + 90 * drape) * s                           # how far the cloth hangs below the head
    W = (150 - 70 * drape) * s                          # flat disc is wide; draped it narrows
    pts = []
    n = 26
    for i in range(n + 1):                              # head dome
        a = math.pi + i * math.pi / n
        pts.append((hx + math.cos(a) * hr * 1.08, hy + math.sin(a) * hr * 1.08))
    # right side down, wavy hem, left side up
    rx = hx + W / 2 * (1 - drape) + hr * 1.25 * drape
    lx = hx - W / 2 * (1 - drape) - hr * 1.25 * drape
    bot = hy + L
    side_r = [(hx + hr * 1.08 + (rx - hx - hr * 1.08) * u, hy + (bot - hy) * u ** (1 - 0.4 * drape)) for u in np.linspace(0.1, 1, 6)]
    hem = []
    for i in range(1, 22):
        u = i / 22
        hx_ = rx + (lx - rx) * u
        wv = math.sin(u * math.pi * 4 + t * 2.2 + seed) * 9 * s * drape
        hem.append((hx_ + sway * 16 * s * drape, bot + wv))
    side_l = [(hx - hr * 1.08 + (lx - hx + hr * 1.08) * u, hy + (bot - hy) * u ** (1 - 0.4 * drape)) for u in np.linspace(1, 0.1, 6)]
    pts += side_r + hem + side_l
    cv.polygon(pts, CLOTH)
    # soft folds
    if drape > 0.3:
        for f in (-0.45, 0.0, 0.45):
            cv.line(hx + f * hr, hy + hr * 0.9, hx + f * hr * 1.4 + sway * 8 * s, bot - 12 * s, CLOTH_SHADE, 2)
    cv.polyline(pts, CLOTH_SHADE * 0.8, 2.5, closed=True)
    if eyes > 0:
        for sx in (-1, 1):
            cv.polygon(_ell(hx + sx * 13 * s, hy - 4 * s, 6.5 * s * eyes, 11 * s * eyes, 16), GHOST_EYE)
        cv.polygon(_ell(hx, hy + 16 * s, 6 * s * eyes, 7 * s * eyes, 14), GHOST_EYE)


def cloth_disc(cv, x, y, s=1.0):
    """Cut cloth circle lying flat on the table (seen from the side: a thin white ellipse)."""
    cv.polygon(_ell(x, y - 4 * s, 75 * s, 9 * s, 32), CLOTH)
    cv.polyline(_ell(x, y - 4 * s, 75 * s, 9 * s, 32), CLOTH_SHADE, 2, closed=True)


# ----------------------------------------------------------------- lights

def sag_curve(p0, p1, sag, n=24):
    """Hanging wire between two hooks: a parabola (a catenary at this shallow sag), `sag` below the chord."""
    (x0, y0), (x1, y1) = p0, p1
    return [(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + 4 * sag * u * (1 - u)) for u in np.linspace(0, 1, n)]


def bulb(cv, x, y, r, col, lit=0.0, glow=None, t=0.0, seed=0.0):
    """Glass bulb hanging from (x, y) on its little socket."""
    cv.polygon([(x - r * 0.4, y), (x + r * 0.4, y), (x + r * 0.4, y + r * 0.6), (x - r * 0.4, y + r * 0.6)], WIRE * 1.4)
    by = y + r * 0.6 + r
    tw = 0.92 + 0.08 * math.sin(t * 3 + seed)
    c = np.asarray(col) * (0.32 + 0.68 * lit * tw)
    cv.polygon(_ell(x, by, r * 0.8, r * 1.1, 20), c)
    cv.circle(x - r * 0.25, by - r * 0.4, r * 0.22, lighten(c, 1.5))
    if lit > 0 and glow is not None:
        glow.begin(cv)
        cv.circle(x, by, r * 2.6, np.asarray(col) * 0.5 * lit * tw)
        glow.end(cv)


def light_string(cv, hooks, n_bulbs, r, lit=0.0, glow=None, t=0.0, sag=0.12, bulbs_on=None):
    """Wire hung through `hooks` (list of points), with n_bulbs evenly spaced along its length.
    `lit` 0..1 overall, or per bulb via `bulbs_on` (list of 0..1). Returns the bulb positions."""
    path = []
    for a, b in zip(hooks, hooks[1:]):
        span = math.hypot(b[0] - a[0], b[1] - a[1])
        seg = sag_curve(a, b, span * sag, 20)
        path += seg if not path else seg[1:]
    p = np.asarray(path)
    cv.polyline(p, WIRE, 3)
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    pos = []
    for i in range(n_bulbs):
        s_ = (i + 0.5) / n_bulbs * d[-1]                 # equal arc-length spacing
        k = int(np.searchsorted(d, s_) - 1)
        k = max(0, min(len(p) - 2, k))
        u = (s_ - d[k]) / max(1e-6, d[k + 1] - d[k])
        bx, by = p[k] + (p[k + 1] - p[k]) * u
        on = lit if bulbs_on is None else bulbs_on[i]
        bulb(cv, bx, by, r, BULB_COLORS[i % 2], on, glow, t, i * 1.7)
        pos.append((bx, by))
    for hx, hy in hooks:
        cv.circle(hx, hy, 5, WIRE * 2)
    return pos
