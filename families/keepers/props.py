"""Things the Forest Keepers build and use in episode 4 (docs/engines/forest_keepers_animal_houses.md): the animal
houses, birds, the water wheel and its frame, the sluice gate, the forest workshop (shed, line shaft, belts, drill
press, nail press, paint stand, roller line) and small tools (spirit level). Side view, y down, world units.
"""
import math

import numpy as np

from families.foundry.keepers.common import PLANK, ellipse, lerp, lighten, rect, smoothstep
from families.foundry.style import IRON, STEEL
from families.foundry.tree_monsters import LAMP, SAWDUST, TRUNK

WOOD = PLANK
WOOD_DARK = PLANK * 0.62
INSIDE = np.array([30, 22, 20], np.float64)
ROPE = np.array([150, 128, 92], np.float64)
LEATHER = np.array([96, 62, 40], np.float64)
GLASS = np.array([60, 66, 62], np.float64)
WATER = np.array([46, 84, 124], np.float64)
WATER_LIGHT = np.array([120, 170, 214], np.float64)
FOAM = np.array([200, 222, 236], np.float64)


# ====================================================================== houses

class HouseSpec:
    """One house design. Sizes in world units; hole_y = height of the door/hole centre above the floor (0..1 of
    the body height); arch = door standing on the floor (rounded top) instead of a round hole."""

    def __init__(self, kind, w, h, roof, hole_r, hole_y, color, perch=False, arch=False, window=False):
        self.kind, self.w, self.h, self.roof = kind, w, h, roof
        self.hole_r, self.hole_y, self.arch, self.perch, self.window = hole_r, hole_y, arch, perch, window
        self.color = np.array(color, np.float64)

    @property
    def top(self):
        return self.h + self.roof


SPECS = [HouseSpec("bird", 86, 96, 50, 15, 0.62, (104, 160, 214), perch=True),
         HouseSpec("bird", 86, 96, 50, 15, 0.62, (226, 186, 92), perch=True),
         HouseSpec("bird", 86, 96, 50, 15, 0.62, (118, 186, 128), perch=True),
         HouseSpec("bird", 86, 96, 50, 15, 0.62, (222, 140, 152), perch=True),
         HouseSpec("hedgehog", 176, 92, 56, 30, 0.0, (198, 120, 84), arch=True),
         HouseSpec("bunny", 204, 132, 72, 38, 0.0, (168, 146, 214), arch=True, window=True)]

# where each panel comes from while it is being put on (unit direction, scaled by `reach`)
PANELS = {"back": (0.0, -1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0), "front": (0.0, -1.0),
          "roofL": (-0.7, -1.0), "roofR": (0.7, -1.0)}


def hole_center(spec, x, yb):
    if spec.arch:
        return x - spec.w * 0.12, yb - spec.hole_r * 1.1
    return x, yb - spec.h * spec.hole_y


def lamp_point(spec, x, yb):
    """Where the little lantern hangs: right of the door, under the eave."""
    return x + spec.w * 0.5 - 16, yb - spec.h * 0.86


def draw_house(c, s, spec, x, yb, t, parts=None, paint=1.0, lamp=0.0, inside=0.0, reach=110.0, hole=1.0,
               shade=1.0, src=None, hanger=True):
    """A house standing on (x, yb). parts: panel -> 0..1 while being put together (None = finished);
    paint 0..1 sweeps the colour on from the roof down; lamp 0..1 lights the little lantern; inside 0..1 a
    warm glow through the door (someone lives there and the lights are on); hole 0..1 the door is drilled."""
    w, h = spec.w, spec.h
    x0, x1, top = x - w / 2, x + w / 2, yb - h

    def u(name):
        return 1.0 if parts is None else parts.get(name, 0.0)

    def off(name):
        if src is not None:                     # comes up out of the kit at `src`
            e = (1 - u(name)) ** 2
            bx, by = PANEL_BASE[name](spec, x, yb)
            return (src[0] - bx) * e, (src[1] - by) * e
        e = (1 - u(name)) ** 2 * reach
        d = PANELS[name]
        return d[0] * e, d[1] * e

    sweep = top - spec.roof + (h + spec.roof) * paint           # painted above this line

    def col_at(y):
        return (spec.color * 0.92 if y < sweep else WOOD) * shade

    hx, hy = hole_center(spec, x, yb)
    if u("back") > 0:
        dx, dy = off("back")
        rect(c, x0 + dx, top + dy, x1 + dx, yb + dy, WOOD_DARK * 1.1 * shade)
    for side, sx in (("left", -1), ("right", 1)):
        if u(side) > 0:
            dx, dy = off(side)
            ex = (x0 if sx < 0 else x1 - 9) + dx
            rect(c, ex, top + dy, ex + 9, yb + dy, WOOD * 0.82 * shade)
    if u("front") > 0:
        dx, dy = off("front")
        rect(c, x0 + dx, top + dy, x1 + dx, yb + dy, WOOD * shade)
        if paint > 0:
            rect(c, x0 + dx, top + dy, x1 + dx, min(yb, sweep) + dy, spec.color * 0.92 * shade)
        for k in range(1, 3):                                   # board joints
            yy = top + k * h / 3 + dy
            c.line(x0 + dx + 3, yy, x1 + dx - 3, yy, col_at(yy) * 0.8, 2)
        c.polyline([(x0 + dx, top + dy), (x1 + dx, top + dy), (x1 + dx, yb + dy), (x0 + dx, yb + dy)],
                   WOOD_DARK * 0.8 * shade, 2, closed=True)
        if hole > 0:
            r = spec.hole_r * min(1.0, hole)
            glow = LAMP * 0.75 * inside
            if spec.arch:
                pts = ellipse(hx + dx, hy + dy, r, r * 1.1, 24, math.pi, 2 * math.pi) + \
                      [(hx + dx + r, yb + dy), (hx + dx - r, yb + dy)]
                c.polygon(pts, INSIDE + glow)
                c.polyline(pts, col_at(hy) * 0.62, 3, closed=True)
            else:
                c.circle(hx + dx, hy + dy, r, INSIDE + glow)
                c.circle(hx + dx, hy + dy, r, col_at(hy) * 0.62, False, 3)
            if inside > 0.02:
                s.glow_draw(lambda g: g.circle(hx + dx, hy + dy, r * 2.0, LAMP * 0.4 * inside))
        if spec.perch and u("front") >= 1:
            c.line(hx - 2, hy + spec.hole_r + 14, hx + 22, hy + spec.hole_r + 14, WOOD_DARK, 5)
        if spec.window and u("front") >= 1:
            wx, wy, wr = x + w * 0.24, top + h * 0.38, 18
            c.circle(wx, wy, wr, INSIDE + LAMP * 0.8 * inside)
            c.circle(wx, wy, wr, col_at(wy) * 0.6, False, 4)
            c.line(wx - wr, wy, wx + wr, wy, col_at(wy) * 0.6, 3)
            c.line(wx, wy - wr, wx, wy + wr, col_at(wy) * 0.6, 3)
            if inside > 0.02:
                s.glow_draw(lambda g: g.circle(wx, wy, 34, LAMP * 0.4 * inside))
    ridge = (x, top - spec.roof)
    for name, sx in (("roofL", -1), ("roofR", 1)):
        if u(name) <= 0:
            continue
        dx, dy = off(name)
        eave = (x + sx * (w / 2 + 16), top + 10)
        th = 13
        pts = [(ridge[0] + dx, ridge[1] + dy), (eave[0] + dx, eave[1] + dy), (eave[0] + dx, eave[1] + th + dy),
               (ridge[0] + dx, ridge[1] + th + dy)]
        rc = (spec.color * 0.62 if paint > 0.05 else WOOD * 0.8) * shade
        rc = lerp(WOOD * 0.8 * shade, rc, smoothstep(min(1.0, paint * 4)))
        c.polygon(pts, rc)
        c.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], lighten(rc, 1.3), 2)
    if parts is None or (u("roofL") >= 1 and u("roofR") >= 1):
        # gable fill between the roof boards and the body
        c.polygon([(x0 + 2, top + 1), (x1 - 2, top + 1), (ridge[0], ridge[1] + 13)], col_at(top - 4) * 0.94)
    if lamp > 0 or (hanger and parts is None and paint >= 1):
        lx, ly = lamp_point(spec, x, yb)
        c.line(lx, ly - 12, lx, ly, IRON * 1.4, 2)
        c.polygon([(lx - 7, ly), (lx + 7, ly), (lx + 8, ly + 16), (lx - 8, ly + 16)],
                  np.array([50, 50, 46]) + LAMP * 0.85 * lamp)
        if lamp > 0:
            s.glow_draw(lambda g: g.circle(lx, ly + 8, 30, LAMP * 0.55 * lamp))


PANEL_BASE = {"back": lambda sp, x, yb: (x, yb - sp.h * 0.5),
              "left": lambda sp, x, yb: (x - sp.w / 2 + 4, yb - sp.h * 0.5),
              "right": lambda sp, x, yb: (x + sp.w / 2 - 4, yb - sp.h * 0.5),
              "front": lambda sp, x, yb: (x, yb - sp.h * 0.5),
              "roofL": lambda sp, x, yb: (x - sp.w * 0.3, yb - sp.h - sp.roof * 0.45),
              "roofR": lambda sp, x, yb: (x + sp.w * 0.3, yb - sp.h - sp.roof * 0.45)}
GRIP = {"back": (0.0, -0.3), "left": (0.0, -0.2), "right": (0.0, -0.2), "front": (0.3, -0.25), "roofL": (0.0, 0.0),
        "roofR": (0.0, 0.0)}


def panel_grip(spec, x, yb, name, u, reach=110.0, src=None):
    """World point a tentacle holds panel `name` by while it moves in."""
    bx, by = PANEL_BASE[name](spec, x, yb)
    gx, gy = bx + GRIP[name][0] * spec.w, by + GRIP[name][1] * spec.h
    e = (1 - u) ** 2
    if src is not None:
        return gx + (src[0] - bx) * e, gy + (src[1] - by) * e
    d = PANELS[name]
    return gx + d[0] * e * reach, gy + d[1] * e * reach


def draw_kit(c, spec, x, yb, n=6):
    """The cut panels of one house, stacked flat in a tray (seen edge-on)."""
    for k in range(n):
        wk = spec.w * (1.0 if k % 3 else 0.8)
        rect(c, x - wk / 2, yb - 9 * (k + 1), x + wk / 2, yb - 9 * k - 1, WOOD * (0.9 + 0.08 * (k % 2)))


# ====================================================================== animals

ROBIN = (np.array([118, 92, 70]), np.array([226, 120, 70]))
BLUE_TIT = (np.array([80, 120, 170]), np.array([226, 206, 96]))


def bird(c, x, y, s=1.0, face=1, flap=0.0, cols=ROBIN, t=0.0):
    """Little round songbird, side view; (x, y) = feet. flap -1..1 = wings up/down while flying; 0 = folded."""
    body, breast = cols
    by = y - 15 * s
    c.polygon([(x - face * 14 * s, by - 2 * s), (x - face * 30 * s, by - 10 * s), (x - face * 30 * s, by + 2 * s)],
              body * 0.8)                                                                 # tail
    c.polygon(ellipse(x, by, 17 * s, 13 * s, 24), body)
    c.polygon(ellipse(x + face * 5 * s, by + 3 * s, 10 * s, 9 * s, 18), breast)
    c.circle(x + face * 12 * s, by - 10 * s, 9 * s, body)                               # head
    c.circle(x + face * 15 * s, by - 7 * s, 5 * s, breast)
    c.circle(x + face * 15 * s, by - 13 * s, 2.2 * s, np.array([16, 16, 20]))
    c.polygon([(x + face * 20 * s, by - 11 * s), (x + face * 27 * s, by - 9 * s), (x + face * 20 * s, by - 7 * s)],
              np.array([220, 170, 70]))
    if flap == 0.0:
        c.polygon(ellipse(x - face * 3 * s, by - 2 * s, 11 * s, 7 * s, 16), body * 0.78)
    else:
        tip = (x - face * 6 * s, by - 2 * s - 24 * s * flap)
        c.polygon([(x - face * 8 * s, by - 4 * s), (x + face * 6 * s, by - 4 * s), tip], body * 0.78)
    if flap == 0.0:
        for f in (-3, 3):
            c.line(x + f * s, by + 11 * s, x + f * s + face * 2 * s, y, np.array([180, 130, 70]), 1.5 * s)


# ====================================================================== water wheel

def water_wheel(c, x, y, R, rot, paddles, plen=58.0, n=8, shade=1.0):
    """Undershot wheel seen face-on, turning about (x, y). paddles: set of slot indices fitted (slot k sits at
    angle rot + k * 2pi/n; angle 0 = +x, y down, so -pi/2 is the top)."""
    for k in range(n):                                        # spokes
        a = rot + (k + 0.5) * 2 * math.pi / n
        c.line(x, y, x + math.cos(a) * (R - 8), y + math.sin(a) * (R - 8), WOOD * 0.72 * shade, 13)
        c.line(x, y, x + math.cos(a) * (R - 8), y + math.sin(a) * (R - 8), WOOD * 0.92 * shade, 4)
    c.circle(x, y, R, WOOD * 0.7 * shade, False, 22)          # rim
    c.circle(x, y, R + 9, WOOD_DARK * shade, False, 3)
    c.circle(x, y, R - 11, WOOD * 0.95 * shade, False, 3)
    for k in range(n):                                        # slots / paddles
        a = rot + k * 2 * math.pi / n
        ca, sa = math.cos(a), math.sin(a)
        if k in paddles:
            r0, r1, hw = R - 12, R + plen, 15
            pts = [(x + ca * r0 - sa * hw, y + sa * r0 + ca * hw), (x + ca * r1 - sa * hw, y + sa * r1 + ca * hw),
                   (x + ca * r1 + sa * hw, y + sa * r1 - ca * hw), (x + ca * r0 + sa * hw, y + sa * r0 - ca * hw)]
            c.polygon(pts, WOOD * 1.05 * shade)
            c.polyline(pts, WOOD_DARK * shade, 2, closed=True)
        else:
            c.circle(x + ca * R, y + sa * R, 7, INSIDE)
    c.circle(x, y, 36, IRON * 1.3)
    c.circle(x, y, 36, IRON * 0.8, False, 3)
    c.circle(x, y, 24, LEATHER)                               # belt pulley on the axle
    for k in range(3):
        a = rot * 1.0 + k * 2 * math.pi / 3
        c.line(x, y, x + math.cos(a) * 20, y + math.sin(a) * 20, LEATHER * 0.6, 3)
    c.circle(x, y, 7, STEEL * 1.4)


def paddle_tip(x, y, R, rot, k, n=8, plen=58.0):
    a = rot + k * 2 * math.pi / n
    return x + math.cos(a) * (R + plen * 0.5), y + math.sin(a) * (R + plen * 0.5)


def aframe(c, x, yc, G, legs=(1.0, 1.0), bearing=1.0, spread=230.0, reach=200.0):
    """Front A-frame holding the axle: two legs from the ground up to the bearing block at (x, yc). legs = 0..1
    each (0 = not there yet, coming in from above-outside), bearing 0..1 the block bolted on."""
    for k, sx in enumerate((-1, 1)):
        u = legs[k]
        if u <= 0:
            continue
        e = (1 - u) ** 2 * reach
        fx, fy = x + sx * spread + sx * e, G + 6 - e
        tx, ty = x + sx * 20 + sx * e, yc + 14 - e
        c.line(fx, fy, tx, ty, TRUNK * 1.05, 24)
        c.line(fx, fy, tx, ty, TRUNK * 1.3, 4)
    if legs[0] >= 1 and legs[1] >= 1:
        yb = lerp(yc, G, 0.55)
        c.line(x - spread * 0.45, yb, x + spread * 0.45, yb, TRUNK * 0.95, 16)
    if bearing > 0:
        e = (1 - bearing) ** 2 * 120
        rect(c, x - 34, yc - 18 - e, x + 34, yc + 22 - e, IRON * 1.2)
        for bx in (-22, 22):
            c.circle(x + bx, yc + 2 - e, 5, STEEL * 1.5)


def sluice(c, x, G, depth, lift, frame=1.0):
    """Sluice gate across the head of the race: two posts and a board that slides up by `lift` (0..1)."""
    if frame > 0:
        for sx in (-1, 1):
            rect(c, x + sx * 36 - 8, G - 150, x + sx * 36 + 8, G + depth, TRUNK)
        rect(c, x - 52, G - 162, x + 52, G - 146, TRUNK * 0.9)
    yb = G + depth - lift * (depth + 70)
    rect(c, x - 28, yb - depth - 30, x + 28, yb, WOOD * 0.95)
    c.line(x - 28, yb - depth * 0.5 - 15, x + 28, yb - depth * 0.5 - 15, WOOD_DARK, 2)
    c.line(x, yb - depth - 30, x, G - 150, IRON * 1.3, 4)             # the lifting rod
    c.circle(x, G - 150 - 10, 9, IRON * 1.5)


# ====================================================================== workshop

def shed_back(c, x0, x1, G, roof_y):
    """Open-sided forest workshop: back wall of rough planks and a packed earth floor."""
    rect(c, x0, roof_y, x1, G, np.array([44, 34, 30]))
    for x in np.arange(x0, x1, 46):
        c.line(x, roof_y, x, G, np.array([36, 28, 25]), 2)
    rect(c, x0 - 30, G - 4, x1 + 30, G + 4, np.array([58, 44, 34]))


def shed_front(c, s, x0, x1, G, roof_y, posts, lamps, t):
    """Posts, roof with an overhanging eave and warm lanterns hanging under it."""
    for px in posts:
        rect(c, px - 16, roof_y, px + 16, G, TRUNK)
        c.line(px - 6, roof_y, px - 4, G, TRUNK * 0.8, 3)
    c.polygon([(x0 - 120, roof_y), (x1 + 120, roof_y), (x1 + 60, roof_y - 120), (x0 - 60, roof_y - 120)],
              np.array([86, 56, 44]))
    for x in np.arange(x0 - 100, x1 + 100, 60):
        c.line(x, roof_y, x + 40 * ((x - (x0 + x1) / 2) / (x1 - x0)), roof_y - 118, np.array([70, 46, 36]), 3)
    rect(c, x0 - 120, roof_y - 6, x1 + 120, roof_y + 14, TRUNK * 0.9)
    for k, lx in enumerate(lamps):
        ly = roof_y + 60
        sw = 0.05 * math.sin(t * 1.3 + k)
        lxx = lx + 50 * sw
        c.line(lx, roof_y + 14, lxx, ly, np.array([60, 52, 40]), 2)
        c.polygon([(lxx - 15, ly), (lxx + 15, ly), (lxx + 18, ly + 34), (lxx - 18, ly + 34)],
                  np.array([50, 50, 46]) + LAMP * 0.85)
        s.glow_draw(lambda g, lxx=lxx, ly=ly: g.circle(lxx, ly + 18, 44, LAMP * 0.6))
        s.glow_draw(lambda g, lxx=lxx, ly=ly: g.polygon([(lxx - 20, ly + 30), (lxx + 20, ly + 30), (lxx + 260, G),
                                                         (lxx - 260, G)], LAMP * 0.035))


def pulley(c, x, y, r, rot, col=LEATHER):
    c.circle(x, y, r, col * 0.9)
    c.circle(x, y, r, col * 0.55, False, 3)
    for k in range(4):
        a = rot + k * math.pi / 2
        c.line(x, y, x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, col * 0.55, 3)
    c.circle(x, y, r * 0.22, STEEL * 1.3)


def belt(c, p0, r0, p1, r1, phase, col=LEATHER):
    """Open belt between two pulleys (centres p0, p1); `phase` (world units of belt travelled) moves the marks."""
    (x0, y0), (x1, y1) = p0, p1
    d = math.hypot(x1 - x0, y1 - y0) + 1e-9
    nx, ny = -(y1 - y0) / d, (x1 - x0) / d
    for sgn, dirn in ((1, 1), (-1, -1)):
        a = (x0 + nx * r0 * sgn, y0 + ny * r0 * sgn)
        b = (x1 + nx * r1 * sgn, y1 + ny * r1 * sgn)
        c.line(a[0], a[1], b[0], b[1], col, 7)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for m in np.arange((phase * dirn) % 90, L, 90):
            u = m / L
            px, py = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            c.line(px, py, px + (b[0] - a[0]) / L * 12, py + (b[1] - a[1]) / L * 12, col * 0.55, 7)


def line_shaft(c, x0, x1, y, rot, brackets):
    c.line(x0, y, x1, y, STEEL * 0.9, 12)
    c.line(x0, y - 3, x1, y - 3, STEEL * 1.3, 2)
    for bx in brackets:
        rect(c, bx - 10, y - 70, bx + 10, y - 4, IRON * 1.2)
        c.circle(bx, y, 13, IRON * 1.4)
    for x in np.arange(x0 + 40, x1, 160):                      # a painted stripe shows it turning
        ph = (rot * 13 + x * 0.0) % (2 * math.pi)
        if math.sin(ph) > 0:
            c.line(x, y - 4, x, y + 4, np.array([200, 160, 60]), 4)


def level(c, x, y, L, bubble=0.0, ok=0.0):
    """Spirit level lying on something: bar, centre vial with the bubble (bubble -1..1 off centre)."""
    rect(c, x - L / 2, y - 18, x + L / 2, y, np.array([214, 168, 52]))
    c.polyline([(x - L / 2, y - 18), (x + L / 2, y - 18), (x + L / 2, y), (x - L / 2, y)],
               np.array([140, 106, 30]), 2, closed=True)
    rect(c, x - 26, y - 14, x + 26, y - 4, np.array([150, 220, 120]) * (0.7 + 0.3 * ok))
    c.line(x - 8, y - 14, x - 8, y - 4, np.array([40, 60, 30]), 1.5)
    c.line(x + 8, y - 14, x + 8, y - 4, np.array([40, 60, 30]), 1.5)
    c.circle(x + bubble * 16, y - 9, 4.5, np.array([236, 250, 220]))


def bench(c, x0, x1, y, G, col=TRUNK):
    rect(c, x0, y, x1, y + 20, col * 1.1)
    c.line(x0, y, x1, y, lighten(col, 1.3), 3)
    for lx in (x0 + 24, x1 - 24):
        rect(c, lx - 9, y + 20, lx + 9, G, col * 0.8)


def tray(c, x, y, w=150.0):
    """Shallow wooden tray on the roller line; y = its bottom."""
    rect(c, x - w / 2, y - 14, x + w / 2, y, WOOD * 0.72)
    rect(c, x - w / 2, y - 26, x - w / 2 + 8, y, WOOD * 0.6)
    rect(c, x + w / 2 - 8, y - 26, x + w / 2, y, WOOD * 0.6)


def rollers(c, x0, x1, y, G, rot):
    rect(c, x0, y + 10, x1, y + 22, IRON * 1.0)
    for x in np.arange(x0 + 20, x1 - 10, 40):
        c.circle(x, y + 5, 8, STEEL * 0.9)
        a = rot + x * 0.05
        c.line(x, y + 5, x + math.cos(a) * 7, y + 5 + math.sin(a) * 7, STEEL * 0.5, 2)
    for lx in np.arange(x0 + 30, x1, 420):
        rect(c, lx - 8, y + 22, lx + 8, G, IRON * 0.8)


def drill_press(c, x, top_y, table_y, G, feed, rot, bit_r):
    """Belt-driven drill press: column, head with the drive pulley, quill + hole saw going down by feed (0..1)
    onto the table at table_y; lever on the right pulled down by the same feed."""
    rect(c, x + 60, top_y, x + 80, G, IRON * 1.1)                    # column
    rect(c, x - 40, table_y, x + 110, table_y + 16, IRON * 1.25)       # table
    rect(c, x + 30, G - 24, x + 120, G, IRON)
    rect(c, x - 50, top_y, x + 100, top_y + 70, IRON * 1.3)           # head
    c.polyline([(x - 50, top_y), (x + 100, top_y), (x + 100, top_y + 70), (x - 50, top_y + 70)], IRON * 0.8, 2,
               closed=True)
    pulley(c, x + 30, top_y - 20, 26, rot)
    q = top_y + 70 + feed * (table_y - top_y - 70 - 20)
    rect(c, x - 8, top_y + 70, x + 8, q - 26, STEEL * 1.2)            # quill
    rect(c, x - bit_r, q - 26, x + bit_r, q, STEEL * 1.5)             # hole saw
    for k in range(int(bit_r / 4)):
        tx = x - bit_r + k * 8 + (rot * 6) % 8
        if tx < x + bit_r - 2:
            c.line(tx, q, tx + 3, q + 5, STEEL * 1.7, 2)
    ang = 0.5 + feed * 0.9                                            # lever
    c.line(x + 100, top_y + 40, x + 100 + math.cos(ang) * 120, top_y + 40 + math.sin(ang) * 120, STEEL, 8)
    c.circle(x + 100 + math.cos(ang) * 120, top_y + 40 + math.sin(ang) * 120, 11, np.array([40, 36, 36]))
    return x + 100 + math.cos(ang) * 120, top_y + 40 + math.sin(ang) * 120


def nail_press(c, x, top_y, G, press, w=280.0, stroke=70.0):
    """Two-post press with a top step to bounce on; the plate with four nail drivers comes down by `press`
    (0..1 of its stroke, set per house so the drivers just reach the top of the box). Returns the step's y."""
    for sx in (-1, 1):
        rect(c, x + sx * w / 2 - 12, top_y, x + sx * w / 2 + 12, G, IRON * 1.1)
    py = top_y + 30 + press * stroke
    rect(c, x - w / 2 + 12, py, x + w / 2 - 12, py + 22, IRON * 1.35)
    for k in range(4):
        nx = x - w * 0.36 + k * w * 0.24
        rect(c, nx - 5, py + 22, nx + 5, py + 44, STEEL * 1.5)
    rect(c, x - 20, top_y - 40 + press * stroke, x + 20, py, STEEL)         # ram
    rect(c, x - 70, top_y - 56 + press * stroke, x + 70, top_y - 40 + press * stroke, np.array([200, 160, 60]))
    c.line(x - w / 2 - 20, top_y, x + w / 2 + 20, top_y, IRON * 1.2, 10)
    return top_y - 56 + press * stroke


def sawdust_pile(c, x, y, amount):
    if amount <= 0:
        return
    r = 20 + 40 * amount
    c.polygon(ellipse(x, y, r * 1.6, r * 0.5, 24, math.pi, 2 * math.pi), SAWDUST * 0.75)


def drill_over(c, x, head_y, stop_y, feed, rot, bit_r, post_x):
    """Overhead drill on a post behind the roller line: the head hangs at head_y, the hole saw goes down by
    `feed` (0..1) to stop_y; worked by a foot pedal (see pedal())."""
    rect(c, post_x - 12, head_y - 40, post_x + 12, stop_y + 140, IRON * 1.0)
    rect(c, x - 10, head_y - 8, post_x, head_y + 8, IRON * 1.15)                 # arm
    rect(c, x - 46, head_y - 30, x + 46, head_y + 40, IRON * 1.35)              # head
    c.polyline([(x - 46, head_y - 30), (x + 46, head_y - 30), (x + 46, head_y + 40), (x - 46, head_y + 40)],
               IRON * 0.8, 2, closed=True)
    pulley(c, x, head_y - 30, 22, rot)
    q = lerp(head_y + 40 + 50, stop_y, feed)                                     # bottom of the hole saw
    rect(c, x - 7, head_y + 40, x + 7, q - 22, STEEL * 1.2)
    rect(c, x - bit_r, q - 22, x + bit_r, q, STEEL * 1.5)
    for k in range(int(bit_r / 4)):
        tx = x - bit_r + k * 8 + (rot * 6) % 8
        if tx < x + bit_r - 2:
            c.line(tx, q, tx + 3, q + 5, STEEL * 1.7, 2)


def pedal(c, x, G, press):
    """Foot pedal on the floor (the rod goes up the drill post)."""
    rect(c, x - 30, G - 14, x + 30, G, IRON)
    ang = -0.35 + 0.3 * press
    c.line(x - 20, G - 12, x - 20 + math.cos(ang) * 90, G - 12 + math.sin(ang) * 90, STEEL * 1.1, 10)


def hanging_sign(c, x, y, text, size=34):
    w = len(text) * size * 0.68 + 40
    for sx in (-1, 1):
        c.line(x + sx * w * 0.35, y - 70, x + sx * w * 0.35, y, ROPE * 0.8, 3)
    rect(c, x - w / 2, y, x + w / 2, y + size * 1.5, np.array([120, 86, 54]))
    c.polyline([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y + size * 1.5), (x - w / 2, y + size * 1.5)],
               np.array([70, 50, 32]), 3, closed=True)
    c.text(text, x, y + size * 0.78, size, np.array([240, 226, 196]))


def flat_wagon(c, x0, x1, G, wheel_rot=0.0):
    """Long low flat wagon with a pull handle on the left; bed top at G - 70."""
    rect(c, x0, G - 70, x1, G - 46, WOOD * 0.85)
    c.line(x0, G - 70, x1, G - 70, WOOD * 1.1, 3)
    for wx in np.linspace(x0 + 70, x1 - 70, 4):
        c.circle(wx, G - 24, 24, np.array([30, 30, 34]))
        c.circle(wx, G - 24, 9, STEEL * 1.8)
        c.line(wx, G - 24, wx + math.cos(wheel_rot) * 18, G - 24 + math.sin(wheel_rot) * 18, STEEL * 1.2, 3)
    c.line(x0, G - 58, x0 - 120, G - 110, IRON * 1.3, 6)
    c.circle(x0 - 120, G - 110, 9, IRON * 1.6)
