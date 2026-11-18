"""Forest Keepers ep 12 (flat remake): the night-shift factory's line that builds Sprout (docs/engines/
forest_keepers_new_friend_flat.md, beat 2). Everything is a pure function of time (frames render in parallel).

The log *is* Sprout from the start: a Monster("sprout") with its build attributes (monster.py: log_top, turned,
spin, carved, socket, stained, attach + part_dxy, orb_in, alive), stood on the jig cart's peg. Each station's machine
does its step visibly:

    LOGS    the hoist trolley brings the round oak log in on its chain, lowers it onto the cart's peg, unhooks
    CUT     the big disc saw (its hub, hung from the gantry, always outside the log) runs in at the mark, a kerf
            grows across; the hoist comes back, hooks the offcut's eye bolt and lifts it away
    TURN    the cart's turntable spins the log, the cutter runs down it top to bottom (bark off, the acorn shape),
            curly shavings fly off and drop into the tray
    CARVE   the chisel cuts the cap's scales across, the drill cuts the orb socket, the brush stains the cap
    FIT     the gripper takes each part off the PARTS shelf and fits it: legs, left arm, right arm, the face
    PLANT   the arm holds out the seedling; Twigs takes it and plants it in the cap (newfriend_flat drives his hand)
    ORB     the trolley brings the seventh orb on its cable and lowers it into the socket; Sprout wakes up
"""
import math

import numpy as np
import skia

from families.foundry.products.monster import BARK_C, CAP, SPROUT_ORB_DY, Monster, seedling
from .newfriend_flat_world import DECK_Y, G, HALL, STATION
from .storybook import C, oval, rrect, smooth, tone

K = 0.72
CART_TOP = DECK_Y - 26.0            # the cart's plate (Sprout's feet line); the peg lifts the log 40 k above it
PEG = 40.0 * K
LT = 150.0                          # the log's extra length above the finished top (log_top, world units / k)
RAIL_Y = G - 800.0                  # the overhead rail (hoist and orb trolleys)
MOVE = 6.0                          # the cart's move from one station to the next, s (slow enough for the
                                    # camera's close shots, zoom 1.8-2, to follow it within its speed limit)
TRAY_X = STATION["turn"] + 250.0    # the shavings tray, right of TURN
SHELF = (STATION["fit"] - 480.0, DECK_Y - 330.0)     # the PARTS shelf's left end, its top (left of FIT): on the back
# wall, above Sprout's cap, so the cart rolls in underneath it (fresh agent, FK0024 round 9: at body height Sprout
# seemed to drive through the shelf, its leg and the parts on it)
SHELF_END = STATION["fit"] - 190.0                   # its right end: a gap before Sprout's body, where the legs and
#                                                      the left arm go down past it (fresh agent, FK0024 round 14: with
#                                                      no gap they went straight down through the board)
SHELF_AT = {"legs": -235.0, "arm": -330.0, "hand": -425.0}   # each part's grip spot (from FIT), all in view
CURL = (214, 184, 140)
STEEL = np.array([104, 117, 142], np.float64)
STEEL_D = np.array([80, 90, 110], np.float64)
SAWDUST = (226, 200, 160)


def _seg(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return min(max((t - a) / (b - a), 0.0), 1.0)


def ss(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease(t, a, b):
    return ss(_seg(t, a, b))


def lerp(a, b, u):
    return a + (b - a) * u


# ----------------------------------------------------------------------------------------------- Sprout's shape

def geom(x, y):
    """Sprout's build landmarks for a Sprout at (x, y) (feet; asleep, so no bob): body middle `by`, the log's top and
    bottom (finished top), the cap's middle `cy`, the seed hole, the socket."""
    k = K
    by = y - 150 * k
    cy = by - 74 * k
    return dict(by=by, top=by - 120 * k, bot=y - 40 * k, cy=cy, hole=(x, cy - 37 * k), socket=(x, by + SPROUT_ORB_DY * k),
                hw=100 * k)


def _profile_poly(x, y):
    m = Monster("sprout", k=K)
    m.x, m.y = x, y
    body, cap, cy = m._sprout_shape(x, y - 150 * K, K)
    return np.asarray(body, float), np.asarray(cap, float)


_PROF = {}


def half_width(yy, x=0.0, y=0.0):
    """The turned shape's half-width at height yy (for the cutter tip to ride on): body and cap outlines."""
    key = round(yy - y, 1)
    if key in _PROF:
        return _PROF[key]
    body, cap = _profile_poly(0.0, 0.0)
    best = 0.0
    for poly in (body, cap):
        for (x0, y0), (x1, y1) in zip(poly, np.roll(poly, -1, axis=0)):
            yq = yy - y
            if (y0 - yq) * (y1 - yq) <= 0 and y0 != y1:
                xx = x0 + (x1 - x0) * (yq - y0) / (y1 - y0)
                best = max(best, abs(xx))
    _PROF[key] = best
    return best


def cap_top(xx, x, y):
    """The cap's top edge height at x = xx (for the chisel and the brush to ride on)."""
    _, cap = _profile_poly(x, y)
    best = None
    for (x0, y0), (x1, y1) in zip(cap, np.roll(cap, -1, axis=0)):
        if (x0 - xx) * (x1 - xx) <= 0 and x0 != x1:
            yy = y0 + (y1 - y0) * (xx - x0) / (x1 - x0)
            best = yy if best is None else min(best, yy)
    return best if best is not None else geom(x, y)["cy"]


# ----------------------------------------------------------------------------------------------- the schedule

class Line:
    """The line's timetable from t0 (the hoist starts). Station work windows and the cart's moves."""

    ORDER = ("hoist", "cut", "turn", "carve", "fit", "plant")
    WORK = {"hoist": 12.0, "cut": 11.0, "turn": 11.5, "carve": 14.0, "fit": 24.0}

    def __init__(self, t0, plant_dur=13.0):
        self.t0 = t0
        t = t0
        self.at = {}                                   # station -> (arrive, leave)
        for name in self.ORDER:
            w = self.WORK.get(name, plant_dur)
            self.at[name] = (t, t + w)
            t += w + (MOVE if name != "plant" else 0.0)
        h0, h1 = self.at["hoist"]
        self.hoist = dict(come=(h0, h0 + 4.5), lower=(h0 + 4.8, h0 + 8.6), unhook=(h0 + 8.8, h0 + 9.8),
                          away=(h0 + 9.8, h0 + 12.6))
        c0_ = h0 + (self.at["cut"][0] - self.at["hoist"][0])
        self.hoist2 = dict(back=(c0_ + 6.8, c0_ + 9.0), drop=(c0_ + 9.1, c0_ + 9.9), lift=(c0_ + 10.1, c0_ + 11.5),
                           leave=(c0_ + 11.6, c0_ + 14.2))
        c0, _ = self.at["cut"]
        self.cut = dict(down=(c0 + 0.8, c0 + 2.2), saw=(c0 + 2.4, c0 + 6.4), up=(c0 + 6.6, c0 + 7.4),
                        push=(c0 + 7.6, c0 + 9.0), fall=(c0 + 9.0, c0 + 9.9), back=(c0 + 9.2, c0 + 10.6))
        u0, _ = self.at["turn"]
        self.turn = dict(spin=(u0 + 0.4, u0 + 11.0), cutter_in=(u0 + 0.8, u0 + 1.8), run=(u0 + 1.9, u0 + 9.4),
                         cutter_out=(u0 + 9.6, u0 + 10.6))
        a0, _ = self.at["carve"]
        self.carve = dict(chisel_in=(a0 + 0.6, a0 + 1.6), chisel=(a0 + 1.6, a0 + 5.6), chisel_out=(a0 + 5.7, a0 + 6.5),
                          sweep=(a0 + 1.6, a0 + 5.0), poke=(a0 + 5.0, a0 + 5.6), poke_hit=a0 + 5.42,
                          drill_in=(a0 + 5.6, a0 + 6.8), drill=(a0 + 6.8, a0 + 8.2), drill_out=(a0 + 8.2, a0 + 9.2),
                          brush_in=(a0 + 9.9, a0 + 10.7), brush=(a0 + 10.7, a0 + 13.0),
                          brush_out=(a0 + 13.0, a0 + 13.8))
        f0, _ = self.at["fit"]
        self.fit = []
        t = f0 + 0.6
        for part in ("legs", "arm", "hand"):
            bk = 1.8 if part == "legs" else 0.8           # (the legs' arm: in, up beside the body, across)
            d = dict(part=part, to_shelf=(t, t + 1.3), grip=(t + 1.3, t + 1.7), carry=(t + 1.7, t + 3.9),
                     press=(t + 3.9, t + 4.5), back=(t + 4.6, t + 4.6 + bk))
            self.fit.append(d)
            t += 4.8 + bk
        # the face is painted on, not carried: the fine brush comes down, paints across left to right, goes up
        self.paint = dict(brush_in=(t + 0.2, t + 1.2), paint=(t + 1.2, t + 4.4), brush_out=(t + 4.5, t + 5.3))
        p0, p1 = self.at["plant"]
        self.plant = dict(offer=(p0 + 0.4, p0 + 2.2),      # the PLANT arm holds the seedling out (Twigs then takes it)
                          up=(p0 + 6.0, p0 + 7.4))          # ...and goes back up once he has it
        self.end = p1

    # ----- the cart

    def cart_x(self, t):
        names = self.ORDER
        for i, name in enumerate(names):
            a, b = self.at[name]
            if t <= b or i == len(names) - 1:
                if i > 0 and t < a:
                    prev = names[i - 1]
                    u = ss(_seg(t, self.at[prev][1], a))
                    return lerp(STATION[prev], STATION[name], u)
                return STATION[name]
        return STATION[names[-1]]

    def cart_moving(self, t):
        for i, name in enumerate(self.ORDER[1:]):
            prev = self.ORDER[i]
            if self.at[prev][1] < t < self.at[name][0]:
                return True
        return False

    # ----- the hoist

    def hoist_x(self, t):
        h, h2 = self.hoist, self.hoist2
        x = STATION["hoist"]
        if t >= h2["back"][0]:                        # the second trip: back to CUT for the offcut, then away
            xc = STATION["cut"]
            if t < h2["leave"][0]:
                return lerp(x - 900.0, xc, ease(t, *h2["back"]))
            return lerp(xc, x - 900.0, ease(t, *h2["leave"]))
        if t < h["come"][1]:
            return lerp(x - 900.0, x, ease(t, *h["come"]))
        if t < h["away"][0]:
            return x
        return lerp(x, x - 900.0, ease(t, *h["away"]))

    def offcut_up(self, t):
        """How high the hoist has lifted the offcut off the log (px)."""
        h2 = self.hoist2
        return 260.0 * ease(t, *h2["lift"])          # (up to just under the CUT sign, never over its letters:
                                                      # fresh agent, FK0024 round 6)

    def log_hang(self, t):
        """How high the hanging log's feet line is above the cart plate (0 = on the peg)."""
        h = self.hoist
        return lerp(250.0, 0.0, ease(t, *h["lower"]))            # it comes in below the LOGS sign

    def hook_y(self, t):
        """The hook's height: on the eye bolt while it holds the log, then up out of the way."""
        h, h2 = self.hoist, self.hoist2
        y_rest = geom(0, CART_TOP)["top"] - LT * K - 18
        if t >= h2["back"][0]:                        # down onto the offcut's eye bolt, then up with it
            if t < h2["drop"][0]:
                return RAIL_Y + 120
            if t < h2["lift"][0]:
                return lerp(RAIL_Y + 120, y_rest, ease(t, *h2["drop"]))
            return y_rest - self.offcut_up(t)
        y_on = geom(0, CART_TOP - self.log_hang(t))["top"] - LT * K - 18
        if t < h["unhook"][0]:
            return y_on
        return lerp(y_rest, RAIL_Y + 120, ease(t, *h["unhook"]))

    # ----- Sprout

    def sprout(self, t):
        """(x, y, attrs) of the log / Sprout on the line at t (attrs for Monster: build state, asleep)."""
        x = self.cart_x(t)
        y = CART_TOP
        h = self.hoist
        if t < h["lower"][1]:
            x = self.hoist_x(t)
            y = CART_TOP - self.log_hang(t)
        c, u, a = self.cut, self.turn, self.carve
        cut_done = t >= c["saw"][1]
        a_ = dict(alive=0.0, orb_in=0.0, log_top=None if cut_done else LT, turned=0.0, spin=0.0, carved=0.0,
                  stained=0.0, socket=0.0, attach=dict(legs=0.0, arm=0.0, hand=0.0, face=0.0, seed=0.0),
                  part_dxy={}, smile=0.6)
        # TURN: the turntable spins (the bark ridges go round), the cutter runs down
        sp = u["spin"]
        if t > sp[0]:
            tt = min(t, sp[1])
            ramp = 1.2
            v = 9.0                                         # rad/s at speed
            d = tt - sp[0]
            spun = v * (max(0.0, d - ramp / 2) if d > ramp else d * d / (2 * ramp))
            if t > sp[1] - ramp:
                e = max(0.0, tt - (sp[1] - ramp))
                spun -= v * e * e / (2 * ramp)
            a_["spin"] = spun
        a_["turned"] = ease(t, *u["run"]) if t < u["run"][1] else 1.0
        if t >= u["run"][1]:
            a_["turned"] = 1.0
        # the scales go on across the pass; the seed hole (drawn once carved reaches 1) only as the chisel presses
        # it, in the middle of the cap (fresh agent, FK0024 beat review: the hole appeared with no tool on it)
        a_["carved"] = 1.0 if t >= a["poke_hit"] else (0.999 if t >= a["sweep"][1] else 0.0)
        a_["socket"] = _seg(t, *a["drill"])
        a_["stained"] = 1.0 if t >= a["brush"][1] else 0.0      # (drawn on under the brush: see reveal)
        # FIT: each part waits on the shelf (drawn by Sprout itself, shifted there), is carried over, pressed on
        for d in self.fit:
            p = d["part"]
            off = self.shelf_off(p, x, y)
            if t >= d["press"][1]:
                a_["attach"][p] = 1.0
                continue
            if t < d["carry"][0]:
                dxy = off
            elif p == "legs":
                dxy = legs_path(off, ease(t, *d["carry"]), geom(x, y)["hw"])
            elif p == "hand":
                dxy = over_path(off, ease(t, *d["carry"]))
            elif p == "arm":
                dxy = beside_path(off, ease(t, *d["carry"]))
            else:
                u_ = ease(t, *d["carry"])
                v_ = ease(t, *d["press"])
                lift = (-185.0 if p == "hand" else -70.0) * math.sin(math.pi * u_)
                dxy = (off[0] * (1 - u_), off[1] * (1 - u_) + lift + 0 * v_)
            a_["attach"][p] = 0.001
            a_["part_dxy"][p] = dxy
        a_["attach"]["face"] = 1.0 if t >= self.paint["paint"][1] else 0.0
        return x, y, a_

    def face_reveal(self, t):
        """0..1 how far across the brush has painted the face (the frame draws the painted part over the bare one)."""
        return _seg(t, *self.paint["paint"])

    def face_span(self, x, y):
        """The painted face's left and right x (world), and its top/bottom."""
        g = geom(x, y)
        return x - 70 * K, x + 70 * K, g["by"] - 50 * K, g["by"] + 54 * K

    def shelf_spot(self, part):
        """Where a part's grip point lies on the PARTS shelf (world)."""
        return STATION["fit"] + SHELF_AT[part], SHELF[1] - 20.0

    def shelf_off(self, part, x, y):
        """part_dxy that puts a part on the shelf: shelf spot minus its attached anchor."""
        m = Monster("sprout", k=K)
        m.x, m.y = x, y
        ax, ay = m.part_anchor(part)
        sx, sy = self.shelf_spot(part)
        return sx - ax, sy - ay

    def part_now(self, part, t):
        """Where the part's grip point is now (world), for the gripper."""
        x, y, a_ = self.sprout(t)
        m = Monster("sprout", k=K)
        m.x, m.y = x, y
        ax, ay = m.part_anchor(part)
        dx, dy = a_["part_dxy"].get(part, (0.0, 0.0))
        return ax + dx, ay + dy


# ----------------------------------------------------------------------------------------------- drawing helpers

def legs_path(off, u, hw):
    """The legs' part_dxy while the gripper carries them (u 0..1), kept in sight the whole way (owner, FK0021 review:
    nothing hidden): up off the shelf, down beside the body, clear of its left side, to the attach height, then slid
    in under it, so only their hip ends go behind the body, and only at the end."""
    side = -(hw + 46.0)
    if u < 0.15:                                       # up off the shelf
        v = ss(u / 0.15)
        return off[0], off[1] - 30.0 * v
    if u < 0.35:                                       # across, over the board, past its end
        return lerp(off[0], side, ss((u - 0.15) / 0.2)), off[1] - 30.0
    if u < 0.6:                                        # down beside the body, in the gap past the shelf's end
        return side, lerp(off[1] - 30.0, 0.0, ss((u - 0.35) / 0.25))
    v = ss((u - 0.6) / 0.4)                            # slid in under it
    return lerp(side, 0.0, v), 0.0


def beside_path(off, u, side=-60.0):
    """The left arm's part_dxy while carried (u 0..1): up off the shelf (high over the cart), down beside Sprout's
    left side to the shoulder's height, then in to the shoulder - never across the cap."""
    if u < 0.15:
        return off[0], off[1] - 24.0 * ss(u / 0.15)
    if u < 0.4:                                         # across over the board, past its end (round 14)
        return lerp(off[0], side, ss((u - 0.15) / 0.25)), off[1] - 24.0
    if u < 0.7:                                         # down in the gap past the shelf's end
        return side, lerp(off[1] - 24.0, 0.0, ss((u - 0.4) / 0.3))
    return lerp(side, 0.0, ss((u - 0.7) / 0.3)), 0.0


def over_path(off, u, high=-185.0):
    """The right arm's part_dxy while carried (u 0..1): up off the shelf, across high over Sprout's cap, then straight
    down outside the cap to the shoulder (fresh agent, FK0024 review: a straight carry clipped the cap's corner)."""
    top = min(off[1], high)
    if u < 0.2:                                         # up off the shelf
        return off[0], lerp(off[1], top, ss(u / 0.2))
    if u < 0.7:                                         # across, high over the cap
        return lerp(off[0], 0.0, ss((u - 0.2) / 0.5)), top
    return 0.0, lerp(top, 0.0, ss((u - 0.7) / 0.3))     # straight down outside the cap to the shoulder


def _poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def box(pg, x0, y0, x1, y1, col, r=3.0, shade=0.06):
    pg.shape(rrect(x0, y0, x1, y1, r), col, shade)


def rod(pg, x0, y0, x1, y1, col, w):
    pg.stroke(skia.Path().moveTo(x0, y0).lineTo(x1, y1), col, w)


def trolley(pg, x, col=HALL["steel"]):
    """A little trolley hanging on the overhead rail: two wheels on the rail, a body below."""
    for dx in (-22, 22):
        pg.flat(oval(x + dx, RAIL_Y - 4, 9, 9), tone(col, -0.2))
    box(pg, x - 40, RAIL_Y + 6, x + 40, RAIL_Y + 42, col, 5)
    pg.flat(oval(x, RAIL_Y + 24, 6, 6), HALL["hazard"])


def chain(pg, x, y0, y1):
    n = max(2, int((y1 - y0) / 14))
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        pg.stroke(oval(x, yy, 4, 7) if i % 2 else oval(x, yy, 2, 7), (130, 134, 142), 2.5)


def hook(pg, x, y):
    pg.stroke(skia.Path().moveTo(x, y - 16).lineTo(x, y + 2).arcTo(skia.Rect(x - 10, y - 4, x + 10, y + 16), 270, -220,
                                                                    False), (150, 154, 160), 5)


def eye_bolt(pg, x, y):
    pg.stroke(oval(x, y - 12, 9, 9), (150, 154, 160), 4)
    pg.flat(rrect(x - 3, y - 4, x + 3, y + 4, 1), (130, 134, 142))


def cart(pg, x, spin=0.0, turning=False):
    """The jig cart: a low steel cart on four small wheels, its plate, and the peg the log stands on (a turntable
    disc under the peg that spins at TURN: its marks go round)."""
    y = CART_TOP
    box(pg, x - 120, y, x + 120, y + 18, HALL["steel2"], 4)
    for dx in (-90, -30, 30, 90):
        pg.flat(oval(x + dx, DECK_Y - 4, 9, 9), (52, 56, 66))
        pg.flat(oval(x + dx, DECK_Y - 4, 3, 3), (110, 116, 128))
    pg.flat(oval(x, y, 58, 9), tone(HALL["steel"], 0.06))
    for q in range(4):
        a = spin + q * math.pi / 2
        u = math.cos(a)
        if math.sin(a) > -0.2:
            pg.flat(oval(x + 52 * u, y + 1, 4, 2.5), HALL["hazard"])
    pg.shape(rrect(x - 16, y - PEG, x + 16, y, 4), HALL["steel"], 0.05)


def offcut(pg, x, ytop, ang=0.0):
    """The log's top end once it's cut off: bark round it, its two cut faces, the eye bolt on top. (x, ytop): the
    middle of its top face. Rotated by ang about its middle as it tips."""
    k = K
    hgt = LT * k
    cx, cy = x, ytop + hgt / 2
    pg.c.save()
    pg.c.rotate(math.degrees(ang), cx, cy)
    pg.flat(rrect(x - 100 * k, ytop, x + 100 * k, ytop + hgt, 2), tuple(BARK_C))
    for q in range(9):                               # the bark ridges where the log's are (spin 0 at CUT)
        u = q / 9.0
        bx = x - 100 * k * math.cos(math.pi * u)
        if 0.06 < u < 0.94:
            rod(pg, bx, ytop + 4 * k, bx, ytop + hgt - 3 * k, tuple(BARK_C * (0.7 + 0.25 * math.sin(math.pi * u))),
                max(1.5, 5 * k))
    pg.flat(oval(x, ytop, 100 * k, 16 * k), (206, 168, 122))     # its top, plain as on the log (no new rings)
    eye_bolt(pg, x, ytop - 2)
    pg.c.restore()


def bin_(pg, x, label, front=True):
    """A low bin on the floor (OFFCUTS / the shavings tray): drawn in two passes, back then front, so what drops in
    goes behind its front wall."""
    from .christmas_flat import _font
    y = G + 2
    if not front:
        box(pg, x - 95, y - 54, x + 95, y, tone(HALL["bin"], -0.1), 4)
        return
    box(pg, x - 100, y - 42, x + 100, y + 4, HALL["bin2"], 4)
    f = _font(20, "Bold")
    tw = f.measureText(label)
    pg.c.drawString(label, x - tw / 2, y - 12, f, skia.Paint(AntiAlias=True, Color=C(HALL["sign"], 0.85)))


# ----------------------------------------------------------------------------------------------- the machines

def draw_hoist(pg, L, t, sh):
    h, h2 = L.hoist, L.hoist2
    trip1 = h["come"][0] - 0.1 <= t <= h["away"][1] + 0.2
    trip2 = h2["back"][0] - 0.1 <= t <= h2["leave"][1] + 0.2
    if not (trip1 or trip2):
        return
    x = L.hoist_x(t) - sh
    trolley(pg, x)
    hy = L.hook_y(t)
    chain(pg, x, RAIL_Y + 42, hy - 16)
    hook(pg, x, hy)


def draw_cut_back(pg, L, t, sh):
    """CUT: the saw's post on the right, its carriage and the disc (live), the ram on the left."""
    c = L.cut
    sx = STATION["cut"] - sh
    g = geom(0, CART_TOP)
    ycut = g["top"]
    # the saw's carriage on the gantry and its arbor down to the disc's hub (always beside the log, never over it)
    ds = disc_state(L, t, sh)
    hx, yc = ds if ds is not None else (sx + DISC_R + 100 * K + 24.0, G - 600)
    box(pg, sx - 200, G - 760, sx + 320, G - 742, HALL["frame"], 2)
    box(pg, hx - 26, G - 768, hx + 26, G - 734, HALL["steel2"], 4)
    rod(pg, hx, G - 734, hx, yc - 4, (150, 156, 168), 10)




def disc_state(L, t, sh):
    """(cx, yc) of the disc saw's middle (screen); parked up on its arbor (G-600, beside the log) before and after
    the cut, never gone (fresh agent, FK0024 round 4: it popped in and out of the bare rod). It comes down clear of the log's corner,
    cuts in, backs out the way it came along the cut, and only then rises (fresh agent, FK0024 beat review: it used
    to rise straight up through the uncut wood above the cut)."""
    c = L.cut
    sx = STATION["cut"] - sh
    if t < c["down"][0] or t > c["up"][1] + 0.3:
        return sx + DISC_R + 100 * K + 24.0, G - 600
    ycut = geom(0, CART_TOP)["top"]
    back = (c["up"][0], c["up"][0] + 0.45)
    if t < c["down"][1]:
        yc = lerp(G - 600, ycut, ease(t, *c["down"]))
    elif t < back[1]:
        yc = ycut
    else:
        yc = lerp(ycut, G - 600, ease(t, back[1], c["up"][1] + 0.3))
    run = ease(t, *c["saw"]) if t < c["up"][0] else 1.0 - ease(t, *back)
    # the hub runs from clear of the log to just outside its right side: the big blade reaches right across, the hub
    # (and its arbor up to the gantry) never goes into the wood (fresh agent, FK0024 review: the arm sank into it)
    return sx + lerp(DISC_R + 100 * K + 24.0, 100 * K + 22.0, run), yc


DISC_R = 168.0                      # the disc saw's radius: big enough to reach across the log from outside it
DISC_RY = 30.0                      # ...seen a little from above


def saw_disc(pg, L, t, sh, half=None):
    """The disc saw (seen a little from above: an ellipse). half "back": its far half (drawn before the log, so
    the log hides it where it's inside the cut), "front": the near half and the arm (after the log)."""
    if half is not None:
        ds = disc_state(L, t, sh)
        if ds is not None:
            yc = ds[1]
            sxl = STATION["cut"] - sh
            pg.c.save()
            if half == "back":
                pg.c.clipRect(skia.Rect(-4000, -4000, 9000, yc))
            else:                                    # the near half: hidden only inside the log's own round
                pg.c.clipRect(skia.Rect(-4000, yc, 9000, 9000))       # (the cut's ellipse, seen from the same
                rx = 100 * K                                          # angle as the disc); the rim that sweeps
                ry = DISC_RY * rx / DISC_R                            # round the log's front passes in front of it
                pg.c.clipRRect(skia.RRect.MakeOval(skia.Rect(sxl - rx, yc - ry, sxl + rx, yc + ry)),
                               skia.ClipOp.kDifference, True)
                # (fresh agent, FK0024 round 12: the whole near half vanished over the log's width, so the
                # blade looked like a knife sliding into the wood)
            saw_disc(pg, L, t, sh)
            pg.c.restore()
        return
    c = L.cut
    sx = STATION["cut"] - sh
    cx, yc = disc_state(L, t, sh)
    spin = t * 30.0
    on = 1.0 if c["down"][1] < t < c["up"][0] else 0.4
    pg.flat(oval(cx, yc, DISC_R, DISC_RY), (196, 202, 212))
    for q in range(30):                              # teeth round the rim, running round
        a = spin * on + q * 2 * math.pi / 30
        pg.flat(oval(cx + DISC_R * math.cos(a), yc + DISC_RY * math.sin(a), 4.5, 2.2), (150, 156, 168))
    pg.flat(oval(cx, yc, 26, 6), (120, 126, 138))
    # sawdust spraying out of the kerf, at the blade's edge: only once the teeth are in the wood (fresh agent, FK0024
    # round 5: chips flew while the edge was still 24 px short of the log)
    if c["saw"][0] < t < c["saw"][1] and cx - DISC_R <= sx + 100 * K:
        rs = np.random.default_rng(int(t * 30))
        for i in range(14):
            ph = rs.random()
            ex = max(sx - 100 * K, cx - DISC_R) + rs.uniform(-6, 6)
            pg.flat(oval(ex + ph * 60 * (1 if i % 2 else -1), yc + ph * ph * 160, 2.4, 2.4), SAWDUST, 0.9 * (1 - ph))


def kerf(pg, L, t, sh):
    """The saw's cut across the log, growing from the right as the disc goes through (on the log, under the disc)."""
    c = L.cut
    if not (c["saw"][0] < t < c["saw"][1]):
        return
    sx = STATION["cut"] - sh
    ycut = geom(0, CART_TOP)["top"]
    cx, _ = disc_state(L, t, sh)
    x1 = sx + 100 * K
    x0 = max(sx - 100 * K, min(x1, cx - DISC_R))       # as far across as the blade's edge has gone
    pg.flat(rrect(x0, ycut - 2.5, x1, ycut + 2.5, 1.5), (52, 38, 28))


def offcut_pose(L, t, sh):
    """(x, ytop, ang) of the offcut (its top face's middle), or None while it's still part of the log / once it's
    gone: it sits on the log until the hoist comes back, hooks its eye bolt, lifts it off and carries it away."""
    c, h2 = L.cut, L.hoist2
    if t < c["saw"][1]:
        return None                                   # (after the hoist has taken it off, it stays off-frame left)
    ytop = geom(0, CART_TOP)["top"] - LT * K - L.offcut_up(t)
    if t < h2["leave"][0]:
        return STATION["cut"] - sh, ytop, 0.0
    return L.hoist_x(t) - sh, ytop, 0.0


def draw_turn_back(pg, L, t, sh):
    """TURN: the cutter's slide on the right and its arm; the tip rides on the shape it cuts."""
    u = L.turn
    sx = STATION["turn"] - sh
    box(pg, sx + 160, G - 740, sx + 182, DECK_Y, HALL["frame"], 3)
    tip = turn_tip(L, t, sh)
    if tip is None:
        box(pg, sx + 146, G - 520, sx + 196, G - 470, HALL["steel2"], 5)
        return
    tx, ty, _ = tip
    box(pg, sx + 146, ty - 25, sx + 196, ty + 25, HALL["steel2"], 5)
    rod(pg, sx + 146, ty, tx + 10, ty, (150, 156, 168), 9)
    pg.shape(_poly([(tx + 14, ty - 9), (tx, ty), (tx + 14, ty + 9)]), (210, 214, 222), 0.0)


def turn_tip_front(pg, L, t, sh):
    """The lathe cutter's tip again, over Sprout, so it is seen right on the edge it cuts."""
    tip = turn_tip(L, t, sh)
    if tip is None:
        return
    tx, ty, _ = tip
    pg.shape(_poly([(tx + 14, ty - 9), (tx - 3, ty), (tx + 14, ty + 9)]), (210, 214, 222), 0.0)


def turn_tip(L, t, sh):
    """(x, y, cutting) of the turning cutter's tip, or None when parked."""
    u = L.turn
    if t < u["cutter_in"][0] or t > u["cutter_out"][1]:
        return None
    sx = STATION["turn"] - sh
    g = geom(0, CART_TOP)
    yr = g["top"] + (g["bot"] - g["top"]) * ease(t, *u["run"])
    surf = half_width(yr, 0.0, CART_TOP) if t >= u["run"][0] else 100 * K
    if t < u["run"][0]:
        yr = g["top"] + 2
        surf = 100 * K
    xin = sx + max(surf, 6.0)
    park = sx + 150.0
    if t < u["cutter_in"][1]:
        return lerp(park, xin, ease(t, *u["cutter_in"])), yr, False
    if t > u["cutter_out"][0]:
        return lerp(sx + 100 * K, park, ease(t, *u["cutter_out"])), g["bot"], False
    return xin, yr, u["run"][0] < t < u["run"][1]


def turn_clip(L, t, gx, y):
    """While the cutter runs down, the bark below it stays the log's full width (only what the tip has passed is
    gone: fresh agent, FK0024 round 10: trimming it in ahead of the tip made wood vanish where nothing touched it);
    the band just gets shorter, down to nothing as the tip reaches the point. The clip keeps the log's drawing to
    the band (its pale ring and ridges never hang below the log's foot or poke up past the tip: round 5's thin
    disc that vanished in one frame, round 10's stray line and dashes beside the acorn)."""
    u = L.turn
    if not (u["run"][0] < t < u["run"][1] + 0.05):
        return None
    g = geom(gx, y)
    f = ease(t, *u["run"])
    yr = g["top"] + (g["bot"] - g["top"]) * f
    w = g["hw"] + 2.0
    hb = half_width(yr - 10.0, 0.0, y) + 2.0          # just above the cut: only the turned shape, nothing at the sides
    p = skia.Path()
    p.addRect(skia.Rect(-4000, -4000, 9000, yr - 10.0))
    p.addRect(skia.Rect(gx - hb, yr - 10.5, gx + hb, yr + 0.5))
    if g["bot"] - yr > 0.5:
        p.addRect(skia.Rect(gx - w, yr - 1.5, gx + w, g["bot"] + 1.0))
    return p


def shavings(pg, L, t, sh):
    """Curly shavings peeling off at the cutter tip, flying right and dropping into the tray (and piling there)."""
    u = L.turn
    if t < u["run"][0]:
        return
    sx = STATION["turn"] - sh
    tray = TRAY_X - sh
    rs = np.random.default_rng(5)
    te = u["run"][0]
    pile = 0
    while te < min(t, u["run"][1]):
        tip = turn_tip(L, te, sh)
        vx, vy = rs.uniform(160, 260), rs.uniform(-120, -40)
        rot0, size = rs.uniform(0, 6.28), rs.uniform(5, 9)
        land_x = tray + rs.uniform(-60, 60)
        if tip is not None:
            x0, y0 = tip[0] + 6, tip[1]
            tau = t - te
            gpx = 1600.0
            y_land = G - 28 - (pile % 5) * 2           # inside the tray (its front wall hides them)
            fall = (-vy + math.sqrt(vy * vy + 2 * gpx * max(1.0, y_land - y0))) / gpx
            vx = (land_x - x0) / fall                  # each one is thrown just hard enough to drop in
            x = x0 + vx * tau
            y = y0 + vy * tau + 0.5 * gpx * tau * tau
            if x > land_x:
                x = land_x
            if y > y_land:
                y = y_land
                pile += 1
            a = rot0 + tau * 7.0 * (1 if y < y_land else 0)
            pg.stroke(skia.Path().addArc(skia.Rect(x - size, y - size, x + size, y + size),
                                         math.degrees(a), 250), CURL, 3.2)
        te += 0.11


def cap_rows(gx):
    """The chisel's / brush's path over the cap's front: three rows, left-right, right-left, left-right (screen)."""
    by = CART_TOP - 150 * K
    pts = []
    for i, yy in enumerate((by - 112 * K, by - 93 * K, by - 74 * K)):
        hw = max(10.0, half_width(yy, 0.0, CART_TOP) - 8.0)
        row = [(gx - hw, yy), (gx + hw, yy)]
        pts += row if i % 2 == 0 else row[::-1]
    return pts


def scale_rows(gx):
    """The chisel's path over the cap's scales: their three rows (monster.py draws them at cy+4k-row*14k, each a
    little arc hanging under that line), top row first, back and forth, the tip riding on the arcs themselves
    (fresh agent, FK0024 round 12: on cap_rows the tip ran 10-17 px above the scales it was cutting)."""
    by = CART_TOP - 150 * K
    cy = by - 74 * K
    pts = []
    for i, row in enumerate((2, 1, 0)):
        yy = cy + 4 * K - row * 14 * K + SCALE_SAG * K
        hw = min((4 - row) * 21 * K + 6 * K, max(10.0, half_width(yy, 0.0, CART_TOP) - 6.0))
        r_ = [(gx - hw, yy), (gx + hw, yy)]
        pts += r_ if i % 2 == 0 else r_[::-1]
    return pts


SCALE_SAG = 6.0                     # (the middle of a scale's arc, below its row line, in k)


def face_rows(gx):
    """The fine brush's path over the face: five rows across it, back and forth (screen)."""
    by = CART_TOP - 150 * K
    pts = []
    for i, dy in enumerate((-42, -21, 0, 21, 42)):
        yy = by + dy * K
        hw = min(58 * K, max(10.0, half_width(yy, 0.0, CART_TOP) - 10.0))
        row = [(gx - hw, yy), (gx + hw, yy)]
        pts += row if i % 2 == 0 else row[::-1]
    return pts


def face_strokes(gx):
    """The fine brush's strokes over the face, one feature at a time (fresh agent, FK0024 round 6: five rows across
    the whole face painted both eyes at once in flat bands): both eyes, the smile, then both cheeks (face_feats). [(paints, [points])] (screen); between features the brush is lifted and moves without painting.
    The features' spots follow Sprout's face in monster.py: eyes (x +-36k, by-14k) r 26k, cheeks (+-54k, by+24k),
    smile (x, by+36k)."""
    by = CART_TOP - 150 * K

    def eye(sx):
        cx, cy = gx + sx * 36 * K, by - 14 * K
        pts = []
        for i, dy in enumerate((-19, -7, 7, 19)):       # covers its whole lid disc (r 1.08 x 26k), no pop at the end
            hw = math.sqrt(max(0.0, 30 ** 2 - dy ** 2)) - 6
            row = [(cx - hw * K, cy + dy * K), (cx + hw * K, cy + dy * K)]
            pts += row if i % 2 == 0 else row[::-1]
        return pts

    def cheek(sx):
        cx, cy = gx + sx * 54 * K, by + 24 * K
        return [(cx - 10 * K, cy), (cx + 10 * K, cy)]

    smile = [(gx - 22 * K + 44 * K * q / 6, by + 36 * K + 5 * K * math.sin(math.pi * q / 6)) for q in range(7)]
    out, prev = [], None
    for f, b in zip(face_feats(eye, smile, cheek), FACE_FEAT_BRUSH):
        if out:
            a = out[-1][1][-1]
            if b != prev:                               # the turret turns to the next brush: lifted higher
                out.append((False, [a, (a[0], a[1] - BRUSH_SWAP_RISE), f[0]]))
            else:
                out.append((False, [a, f[0]]))
        out.append((True, f))
        prev = b
    return out


BRUSH_SWAP_RISE = 34.0              # (px the brush head lifts while its turret turns to the next brush)
FACE_FEAT_BRUSH = (0, 0, 1, 2, 2)   # which of the head's three brushes paints each feature: eyes, smile, cheeks


def face_feats(eye, smile, cheek):
    """The features in painting order: both eyes, the smile, both cheeks (both cheeks: fresh agent, FK0024 round
    10, the left one was never painted; one brush per colour on a turning head: round 16, one dark brush painted
    four colours)."""
    return [eye(-1), eye(1), smile[::-1], cheek(-1), cheek(1)]


def face_strokes_brush(gx):
    """The brush index (0 eye, 1 smile, 2 cheek) of each stroke in face_strokes; a lifted stroke between two
    features painted by different brushes is (a, b): the turret turns from a to b along it."""
    out, prev = [], None
    for b in FACE_FEAT_BRUSH:
        if prev is not None:
            out.append((prev, b))
        out.append((b, b))
        prev = b
    return out


def turret_pos(gx, u):
    """The paint head's turret position (0, 1, 2 = that brush pointing down; in between while it turns) a fraction
    u along the face strokes."""
    st, br = face_strokes(gx), face_strokes_brush(gx)
    lens = [sum(math.dist(a, b) for a, b in zip(p, p[1:])) for _, p in st]
    want = max(0.0, min(1.0, u)) * (sum(lens) or 1.0)
    for d, (a, b) in zip(lens, br):
        if want <= d:
            f = 0.0 if d == 0 else want / d
            return a + (b - a) * (f * f * (3 - 2 * f))
        want -= d
    return float(br[-1][1])


def stroke_pts(strokes):
    """[(a, b, paints)] segments of a stroke list, in order."""
    segs = []
    for paints, pts in strokes:
        segs += [(a, b, paints) for a, b in zip(pts, pts[1:])]
    return segs


def stroke_point(strokes, u):
    """(x, y, lifted 0..1) a fraction u along the strokes (by length); lifted rises while it travels between them."""
    segs = stroke_pts(strokes)
    want = max(0.0, min(1.0, u)) * (sum(math.dist(a, b) for a, b, _ in segs) or 1.0)
    for i, (a, b, paints) in enumerate(segs):
        d = math.dist(a, b)
        if want <= d or i == len(segs) - 1:
            f = 0.0 if d == 0 else min(1.0, want / d)
            return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (0.0 if paints else math.sin(math.pi * f))
        want -= d
    a = segs[-1][1]
    return a[0], a[1], 0.0


def stroke_clip(strokes, u, r):
    """The area the brush's tip has painted so far (a fraction u along the strokes): only the painting strokes."""
    segs = stroke_pts(strokes)
    want = max(0.0, min(1.0, u)) * (sum(math.dist(a, b) for a, b, _ in segs) or 1.0)
    path = skia.Path()
    done = 0.0
    for a, b, paints in segs:
        d = math.dist(a, b)
        if paints:
            n = max(1, int(d / 3.0))
            for i in range(n + 1):
                if done + d * i / n > want:
                    return path
                f = i / n
                path.addCircle(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, r)
        done += d
        if done > want:
            return path
    return path


def path_point(pts, u):
    """The point a fraction u along a polyline (by length)."""
    segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    want = max(0.0, min(1.0, u)) * (sum(segs) or 1.0)
    last = len(segs) - 1
    for i, ((a, b), d) in enumerate(zip(zip(pts, pts[1:]), segs)):
        if want <= d or i == last:                    # (by index: equal-length rows used to stop it on the first)
            f = 0.0 if d == 0 else min(1.0, want / d)
            return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        want -= d
    return pts[-1]


def path_clip(pts, u, r):
    """The area the tool's tip has covered so far (a fraction u along the path): circles of radius r every few px."""
    segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(segs) or 1.0
    want = max(0.0, min(1.0, u)) * total
    path = skia.Path()
    done = 0.0
    for (a, b), d in zip(zip(pts, pts[1:]), segs):
        n = max(1, int(d / 4.0))
        for i in range(n + 1):
            s_ = done + d * i / n
            if s_ > want:
                return path
            f = i / n
            path.addCircle(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, r)
        done += d
    return path


CHEEK_DAB = (214, 160, 150)        # the rose the fine brush puts on the cheeks (the awake blush takes over at the wake)


def cheek_starts(gx):
    """{side: fraction along the face strokes where the brush starts that cheek}."""
    segs = stroke_pts(face_strokes(gx))
    total = sum(math.dist(a, b) for a, b, _ in segs) or 1.0
    by = CART_TOP - 150 * K
    out, done = {}, 0.0
    for a, b, paints in segs:
        if paints and abs(a[1] - (by + 24 * K)) < 0.5 and abs(b[1] - a[1]) < 0.5:
            sx = 1 if a[0] > gx else -1
            out.setdefault(sx, done / total)
        done += math.dist(a, b)
    return out


def cheek_dabs(pg, gx, y, alive, u=None):
    """Sprout's two painted cheeks while it's still asleep: monster.py's blush is wood-coloured then, so only the
    shading made one of them show (fresh agent, FK0024 round 10: a one-cheeked face). Fades out as it wakes, where
    its own rosy blush comes up in the same places. u: how far the fine brush is along its strokes (while it paints,
    a cheek's dab only once the brush has got to that cheek: the eyes' strokes graze the cheeks' tops)."""
    by = geom(gx, y)["by"]
    st = cheek_starts(gx) if u is not None else {}
    for sx in (-1, 1):
        if u is not None and u < st.get(sx, 0.0):
            continue
        pg.flat(oval(gx + sx * 54 * K, by + 24 * K, 17 * K, 9 * K), CHEEK_DAB, 0.85 * (1.0 - alive))


SMILE_PAINT = (92, 64, 54)          # the fine brush's dark paint (the sleepy smile line)
BRUSH_TIPS = ((48, 46, 52), SMILE_PAINT, CHEEK_DAB)   # the paint head's brushes: eye lines, smile, cheeks


def smile_dab(pg, gx, y, alive):
    """Sprout's painted sleepy smile, along the brush's own smile stroke: monster.py's asleep mouth is a thin
    wood-toned line, so the painted face had no mouth and the empty socket below it read as an open "O" mouth
    (fresh agent, FK0024 round 12). Fades out as it wakes, where its own smile comes up in the same place."""
    if alive >= 1.0:
        return
    by = geom(gx, y)["by"]
    p = skia.Path()
    for q in range(13):
        xx = gx - 22 * K + 44 * K * q / 12
        yy = by + 36 * K + 5 * K * math.sin(math.pi * q / 12)
        (p.moveTo if q == 0 else p.lineTo)(xx, yy)
    pg.stroke(p, SMILE_PAINT, 3.4 * K, 0.9 * (1.0 - alive))


def reveal(L, t, gx):
    """(attribute, clip path) of the one change being made on Sprout now, or None: the scales under the chisel, the
    stain under the brush, the face under the fine brush (each drawn done inside the path its tip has covered)."""
    a = L.carve
    if a["sweep"][0] <= t < a["sweep"][1]:
        return "carved", path_clip(scale_rows(gx), _seg(t, *a["sweep"]), 8.5)   # (one row at a time)
    if a["brush"][0] <= t < a["brush"][1]:
        return "stained", path_clip(cap_rows(gx), _seg(t, *a["brush"]), 13.0)
    p = L.paint
    if p["paint"][0] <= t < p["paint"][1]:
        return "face", stroke_clip(face_strokes(gx), _seg(t, *p["paint"]), 9.0)
    return None


def chisel_x(L, t, gx):
    """The chisel's x (screen): across the cap left to right, then back to its middle for the seed hole."""
    return chisel_pt(L, t, gx)[0]


def chisel_pt(L, t, gx):
    """The chisel's tip (screen): along the cap's rows, then to the top of the cap's middle for the seed hole."""
    a = L.carve
    rows = scale_rows(gx)
    if t < a["sweep"][0]:
        return rows[0]
    if t < a["sweep"][1]:
        return path_point(rows, _seg(t, *a["sweep"]))
    u = ease(t, a["poke"][0], a["poke_hit"] - 0.1)
    end = rows[-1]
    return lerp(end[0], gx, u), lerp(end[1], cap_top(gx, gx, CART_TOP) + 2, u)


def draw_carve(pg, L, t, sh):
    """CARVE: the chisel on its arm from above, the drill from the right, the brush from above."""
    a = L.carve
    sx = STATION["carve"] - sh
    x, y, _ = L.sprout(t)
    gx = x - sh
    g = geom(gx, CART_TOP)
    box(pg, sx - 200, G - 760, sx + 200, G - 742, HALL["frame"], 2)
    # chisel: in from above at the left of the cap, across to the right, out
    if a["chisel_in"][0] < t < a["chisel_out"][1]:
        xc, top = chisel_pt(L, t, gx)
        up = 1.0 - ease(t, *a["chisel_in"]) if t < a["chisel_in"][1] else ease(t, *a["chisel_out"])
        tick = 3.0 * abs(math.sin(t * 14.0)) if a["sweep"][0] < t < a["sweep"][1] else 0.0
        press = 5.0 * math.sin(math.pi * _seg(t, a["poke_hit"] - 0.12, a["poke_hit"] + 0.14))
        ty = top - tick + press - up * 300                # the tip on the cap where it cuts (pressing in for the hole)
        rod(pg, xc, G - 742, xc, ty - 30, (150, 156, 168), 8)
        box(pg, xc - 9, ty - 34, xc + 9, ty - 8, HALL["steel2"], 3)
        pg.shape(_poly([(xc - 5, ty - 8), (xc + 5, ty - 8), (xc + 1, ty)]), (214, 218, 226), 0.0)
        if a["sweep"][0] < t < a["sweep"][1] or abs(t - a["poke_hit"]) < 0.2:
            rs = np.random.default_rng(int(t * 20))
            for i in range(5):
                ph = rs.random()
                pg.flat(oval(xc + (ph * 40 + 6) * (1 if i % 2 else -1), ty - 10 + ph * ph * 120, 2.2, 1.6), SAWDUST,
                        0.9 * (1 - ph))
    # brush: down onto the cap, across, up (a dab of stain on its bristles)
    if a["brush_in"][0] < t < a["brush_out"][1]:
        rows = cap_rows(gx)
        xb, top = rows[0] if t < a["brush"][0] else (path_point(rows, _seg(t, *a["brush"])) if t < a["brush"][1]
                                                      else rows[-1])
        up = 1.0 - ease(t, *a["brush_in"]) if t < a["brush_in"][1] else ease(t, *a["brush_out"])
        by_ = top + 2 - up * 300                          # the bristles on the cap where it stains
        rod(pg, xb, G - 742, xb, by_ - 40, (150, 156, 168), 8)
        box(pg, xb - 22, by_ - 44, xb + 22, by_ - 22, (150, 112, 74), 4)
        pg.flat(rrect(xb - 18, by_ - 24, xb + 18, by_ + 2, 3), tuple(CAP * 0.9))


def draw_drill(pg, L, t, sh):
    """CARVE's drill, drawn in front of Sprout: an arm from the right holds the drill pointing into the belly (seen
    end-on: its round head, the spinning flutes), pressed in right where the socket opens, chips flying out round it.
    (Fresh agent, FK0024 beat review: a drill lying across the front could not bore a hole facing us.)"""
    a = L.carve
    if not (a["drill_in"][0] < t < a["drill_out"][1]):
        return
    x, y, _ = L.sprout(t)
    sx = STATION["carve"] - sh
    g = geom(x - sh, CART_TOP)
    ox, oy = g["socket"]
    # it swings across held clear in front of the belly (drawn a touch bigger, nearer us), stops over the socket's
    # spot, then pushes straight in (shrinking to the belly's own size) before it bores, and pulls straight out
    # before it swings away (fresh agent, FK0024 round 15: a drill pointing into the belly slid across its face)
    i0, i1 = a["drill_in"]
    o0, o1 = a["drill_out"]
    im, om = i0 + 0.7 * (i1 - i0), o0 + 0.3 * (o1 - o0)
    if t < i1:
        reach, push = ease(t, i0, im), ease(t, im, i1)
    elif t < o0:
        reach, push = 1.0, 1.0
    else:
        reach, push = 1.0 - ease(t, om, o1), 1.0 - ease(t, o0, om)
    hx = lerp(sx + 190, ox, reach)
    z = lerp(1.3, 1.0, push)
    box(pg, sx + 176, oy - 22, sx + 214, oy + 22, HALL["steel2"], 5)
    rod(pg, sx + 176, oy, hx + 12 * z, oy, (150, 156, 168), 10 * z)
    on = a["drill"][0] < t < a["drill"][1]
    pg.flat(oval(hx, oy, 17.0 * z, 17.0 * z), (120, 126, 138))
    pg.flat(oval(hx, oy, 13.0 * z, 13.0 * z), (168, 174, 186))
    ph = t * 18.0 if on else 0.0
    for q in range(3):                                # the flutes, turning
        an = ph + q * 2.0944
        rod(pg, hx + 3 * z * math.cos(an), oy + 3 * z * math.sin(an), hx + 12 * z * math.cos(an + 0.6),
            oy + 12 * z * math.sin(an + 0.6), (90, 96, 108), 2.2 * z)
    pg.flat(oval(hx, oy, 3.0 * z, 3.0 * z), (70, 74, 84))
    if on:                                            # chips out round the head
        rs = np.random.default_rng(int(t * 24))
        for i in range(8):
            u = rs.random()
            an = rs.uniform(0, 6.283)
            r = 18 + u * 34
            pg.flat(oval(hx + r * math.cos(an), oy + r * math.sin(an) + u * u * 30, 2.2, 1.7), SAWDUST, 0.9 * (1 - u))


def legs_rod_x(L, t):
    """Where FIT's rod stays down (world) while the legs go in under Sprout: clear of its left side."""
    cx = L.cart_x(t)
    return cx - geom(cx, CART_TOP)["hw"] - 40.0


def fit_gripper(L, t, sh):
    """(x, y, closed) of the FIT gripper's jaws, or None when parked."""
    for d in L.fit:
        if d["to_shelf"][0] <= t <= d["back"][1]:
            p = d["part"]
            px, py = L.part_now(p, t)
            park = (STATION["fit"] + 60.0, G - 640.0)
            if t < d["to_shelf"][1]:
                u = ease(t, *d["to_shelf"])
                sx_, sy_ = L.shelf_spot(p)
                return lerp(park[0], sx_, u) - sh, lerp(park[1], sy_ - 26, u), False
            if t < d["press"][1]:
                return px - sh, py - 26, t >= d["grip"][1] - 0.2
            u = ease(t, *d["back"])
            m = Monster("sprout", k=K)
            m.x, m.y = L.cart_x(t), CART_TOP
            ax, ay = m.part_anchor(p)
            if p == "legs":                           # the arm slides back into its sleeve out from under the body,
                b0, b1 = d["back"]                    # the rod rises beside it, then across to park above it (fresh
                b_ = (b1 - b0) / 3                    # agent, FK0024 round 13: the arm's way back)
                lx = legs_rod_x(L, t)
                if t < b0 + b_:
                    return lerp(ax, lx, ease(t, b0, b0 + b_)) - sh, ay - 26, False
                if t < b0 + 2 * b_:
                    return lx - sh, lerp(ay - 26, park[1], ease(t, b0 + b_, b0 + 2 * b_)), False
                return lerp(lx, park[0], ease(t, b0 + 2 * b_, b1)) - sh, park[1], False
            return lerp(ax, park[0], u) - sh, lerp(ay - 26, park[1], u), False
    return None


def draw_fit(pg, L, t, sh):
    """FIT: the gantry over the station, the carriage and the gripper's rod down to its jaws; the PARTS shelf."""
    from .christmas_flat import _font
    sx = STATION["fit"] - sh
    for bx in (SHELF[0] + 20.0, SHELF_END - 40.0):     # two wall brackets under it (all of it above the cap)
        rod(pg, bx - sh, SHELF[1] + 26, bx - sh, SHELF[1] + 64, HALL["frame"], 7)
        rod(pg, bx - sh, SHELF[1] + 64, bx + 34 - sh, SHELF[1] + 26, HALL["frame"], 5)
    box(pg, SHELF[0] - sh - 20, SHELF[1], SHELF_END - sh, SHELF[1] + 26, HALL["frame"], 3)
    f = _font(20, "Bold")
    pg.c.drawString("PARTS", SHELF[0] - sh + 70, SHELF[1] + 21, f, skia.Paint(AntiAlias=True, Color=C(HALL["sign"], 0.9)))
    box(pg, sx - 260, G - 760, sx + 220, G - 742, HALL["frame"], 2)
    gp = fit_gripper(L, t, sh)
    if gp is None:
        gx, gy, closed = sx + 60, G - 640, False
    else:
        gx, gy, closed = gp
    d = L.fit[0]
    rx = gx                                           # where the rod comes down: over the jaws, except while the legs
    if d["grip"][0] <= t <= d["back"][1]:             # go in under Sprout - then it stays down beside its left side and
        if t < d["back"][1] - (d["back"][1] - d["back"][0]) / 3:     # the jaws slide out on a telescoping arm in
            rx = min(gx, legs_rod_x(L, t) - sh)       # under the body at hip height (fresh agent, FK0024 round 8: the
        #                                               rod came down onto its cap; round 13: the arm grew out of the
        #                                               rod with no sleeve, and the rod jumped back over the jaws)
    box(pg, rx - 30, G - 766, rx + 30, G - 736, HALL["steel2"], 4)
    rod(pg, rx, G - 736, rx, gy - 16, (150, 156, 168), 8)
    if not fit_jaws_front(L, t):
        _fit_jaws(pg, L, t, rx, gx, gy, closed)


def fit_jaws_front(L, t):
    """While the legs are carried down and slid in under Sprout, the jaws, their arm and the legs' crossbar are drawn
    in front of the cart's peg (behind Sprout's body), the same depth as the legs they hold (fresh agent, FK0024
    round 15: the legs slid across in front of the peg while the jaws holding them were behind it)."""
    d = L.fit[0]
    return d["grip"][0] <= t <= d["back"][0] + (d["back"][1] - d["back"][0]) / 3


def draw_fit_front(pg, L, t, sh):
    """The FIT jaws' front layer (see fit_jaws_front), drawn after the cart, before Sprout."""
    if not fit_jaws_front(L, t):
        return
    gx, gy, closed = fit_gripper(L, t, sh)
    rx = min(gx, legs_rod_x(L, t) - sh)
    _fit_jaws(pg, L, t, rx, gx, gy, closed)


def _fit_jaws(pg, L, t, rx, gx, gy, closed):
    """The gripper's foot: the inner arm out of the sleeve, the sleeve, the jaws, and the legs' crossbar."""
    d = L.fit[0]
    if gx - rx > 1.0:                                 # the inner arm, out of the sleeve on the rod's foot
        rod(pg, rx, gy - 16, gx, gy - 16, (150, 156, 168), 7)
    box(pg, rx - 14, gy - 25, rx + 28, gy - 7, HALL["steel2"], 3)          # the sleeve (always on the rod's foot)
    box(pg, gx - 16, gy - 22, gx + 16, gy - 8, HALL["steel"], 3)
    o = 6 if closed else 16
    for s in (-1, 1):
        rod(pg, gx + s * o, gy - 10, gx + s * (o - 2), gy + 14, (196, 200, 210), 5)
    # the legs: a crossbar under the jaws clamps both leg tops
    if d["to_shelf"][0] <= t <= d["back"][1]:
        by_ = gy + 16
        box(pg, gx - 36 * K - 14, by_ - 4, gx + 36 * K + 14, by_ + 4, HALL["steel"], 2)
        for s in (-1, 1):
            pg.stroke(skia.Path().addCircle(gx + s * 38 * K, by_ + 6, 9), (196, 200, 210), 3)


def plant_arm_tip(L, t, sh):
    """Where the PLANT arm holds the seedling (its cup's top): it comes down from the gantry to just over Sprout's
    cap, between Sprout and Twigs, in clear view (fresh agent, FK0024 beat review: it used to come down behind Twigs'
    head), and goes back up after he takes it."""
    sx = STATION["plant"] - sh
    p = L.plant
    yy = lerp(G - 600.0, G - 329.0, ease(t, *p["offer"]))
    if t > p["up"][0]:
        yy = lerp(G - 329.0, G - 600.0, ease(t, *p["up"]))
    return sx + 55.0, yy


def draw_plant(pg, L, t, sh, holding=True):
    """PLANT: the arm's carriage on the gantry, its rod down to a little cup; while holding, the seedling in it."""
    tx, ty = plant_arm_tip(L, t, sh)
    box(pg, tx - 8, G - 766, tx + 28, G - 736, HALL["steel2"], 4)
    rod(pg, tx + 10, G - 736, tx + 10, ty - 6, (150, 156, 168), 6)
    box(pg, tx - 12, ty - 8, tx + 32, ty + 6, HALL["steel"], 3)
    if holding:
        seedling_at(pg, tx + 10, ty - 10, t)


def seedling_at(pg, x, y, t, ang=0.0):
    """The seedling (as monster.seedling draws it), its root ball at (x, y)."""
    from . import illustrate as il
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=17)
    cv.c.translate(pg.ox, pg.oy)
    seedling(cv, x, y, K, 0.0, ang)                   # no sway: the same as Sprout draws it asleep
    from .newfriend_flat_world import raw
    with raw(pg):
        pg.c.drawImage(cv.surface.makeImageSnapshot(), 0, 0)


ORB_ARM = 150.0                     # the orb arm's rod comes down this far right of Sprout, clear of its face and
                                    # outside its right hand (fresh agent, FK0024 round 6: at 120 the orb grazed it)


RAM_LEN = ORB_ARM - 10.0                   # the push ram's cylinder (right of the rod: as long as the piston's stroke)


def orb_xy(L, t, sh, t_orb):
    """(x, y) of the seventh orb in the trolley arm's cup (screen; t_orb: (come, lower, in)), also after it is in.
    It travels tucked against the rod, beside Sprout, and only crosses to the socket at the socket's own height
    (owner, FK0021 review: nothing in front of the action), never down over Sprout's cap and face."""
    come, lower, in_t = t_orb
    x_s = L.cart_x(t) - sh
    ox, oy = geom(x_s, CART_TOP)["socket"]
    beside = ox + ORB_ARM - 12.0
    down = (lower[0], lower[1] - 0.6)                  # the rod comes down beside Sprout
    push = (lower[1] - 0.5, in_t)                      # the arm reaches out and pushes the orb into the socket
    if t < come[1]:
        return lerp(x_s + 1100.0, beside, ease(t, *come)), RAIL_Y + 150
    if t < push[0]:
        return beside, lerp(RAIL_Y + 150, oy, ease(t, *down))
    return lerp(beside, ox, ease(t, *push)), oy


def orb_carried(L, t, sh, t_orb):
    """(x, y) of the seventh orb while the trolley carries it, or None once it's in."""
    if t >= t_orb[2]:
        return None
    return orb_xy(L, t, sh, t_orb)


def draw_orb_trolley(pg, L, t, sh, t_orb):
    """The orb trolley: it runs in on the rail, lowers a rod beside Sprout (not over its face), and the rod's short
    arm holds the orb in a little cup level with the socket; it pushes it in, lets go, and goes back up."""
    come, lower, in_t = t_orb
    if t < come[0] - 0.1 or t > in_t + 4.0:
        return
    x_s = L.cart_x(t) - sh
    ox, oy = geom(x_s, CART_TOP)["socket"]
    ax, yb = orb_xy(L, t, sh, t_orb)
    if t >= in_t:
        yb = lerp(oy, RAIL_Y + 150, ease(t, in_t + 1.1, in_t + 3.8))
    rx = ax + 12.0 if t < come[1] else ox + ORB_ARM          # running in: the trolley brings the orb along
    # once the orb is in, the arm first draws back into its rod (clear of Sprout's face), then the rod goes up
    pull = ease(t, in_t + 0.2, in_t + 1.0) if t >= in_t else 0.0
    tip = lerp(ax + 12, rx - 8, pull)
    trolley(pg, rx)
    rod(pg, rx, RAIL_Y + 42, rx, yb + 6, (150, 156, 168), 6)
    # the push ram: its cylinder on the far side of the rod, its piston sliding out through the rod's elbow block
    # (fresh agent, FK0024 round 12: an arm grew out of the bare rod's end with no joint or slide)
    box(pg, rx + 6, yb - 2, rx + 6 + RAM_LEN, yb + 14, HALL["steel2"], 4)
    pg.flat(rrect(rx + 10 + RAM_LEN - 18, yb + 1, rx + 2 + RAM_LEN, yb + 11, 2), (120, 126, 138))
    rod(pg, rx, yb + 6, tip, yb + 6, (196, 202, 212), 5)                     # the piston, level with the orb
    box(pg, rx - 9, yb - 4, rx + 9, yb + 16, HALL["steel2"], 3)              # the elbow block on the rod
    if pull < 0.9:
        cx_ = tip - 12
        pg.stroke(skia.Path().addArc(skia.Rect(cx_ - 13, yb - 6, cx_ + 13, yb + 16), 10, 160), (150, 156, 168), 3)
    if t < in_t:                                        # the orb, glowing softly (like the Keepers' own)
        pg.flat(oval(ax, yb, 24.0, 24.0), (150, 205, 250), 0.22)
        pg.flat(oval(ax, yb, 16.0, 16.0), (150, 205, 250), 0.35)
        pg.flat(oval(ax, yb, 10.1, 10.1), (96, 170, 230))
        pg.flat(oval(ax - 3, yb - 3, 3.2, 3.2), (225, 242, 255))


def face_brush(pg, L, t, sh):
    """The fine brush that paints Sprout's face on (a thin rod from the gantry, a pointed brush, a dab of dark paint):
    it zigzags a little as it paints across."""
    p = L.paint
    if not (p["brush_in"][0] < t < p["brush_out"][1]):
        return
    x, y, _ = L.sprout(t)
    st = face_strokes(x - sh)
    bx, by, lift = (*st[0][1][0], 0.0) if t < p["paint"][0] else (
        stroke_point(st, _seg(t, *p["paint"])) if t < p["paint"][1] else (*st[-1][1][-1], 0.0))
    by -= 14 * lift                                   # lifted off the wood while it moves to the next feature
    up = 1.0 - ease(t, *p["brush_in"]) if t < p["brush_in"][1] else ease(t, *p["brush_out"])
    by -= up * 320
    pos = turret_pos(x - sh, _seg(t, *p["paint"]))
    # a small paint head with three fine brushes, one per paint (fresh agent, FK0024 round 16: one dark brush
    # painted grey eyes, a brown smile and pink cheeks): the turret turns the next brush down between features,
    # while the head is lifted off the wood. The down brush's point is the paint spot (bx - 4: round 5).
    hx, hy = bx + 22, by - 34
    rod(pg, bx + 40, G - 742, bx + 40, hy, (150, 156, 168), 6)
    rod(pg, bx + 40, hy, hx, hy, (150, 156, 168), 6)
    down = math.atan2(by - hy, (bx - 4) - hx)
    reach = math.hypot(by - hy, (bx - 4) - hx)
    for i, col in enumerate(BRUSH_TIPS):
        th = down + (i - pos) * 2 * math.pi / 3
        ux, uy = math.cos(th), math.sin(th)
        nx, ny = -uy, ux
        rod(pg, hx, hy, hx + ux * reach * 0.55, hy + uy * reach * 0.55, (196, 170, 120), 4)   # wooden handle
        b0 = (hx + ux * reach * 0.55, hy + uy * reach * 0.55)
        tip = (hx + ux * reach, hy + uy * reach)
        pg.shape(_poly([(b0[0] + nx * 4, b0[1] + ny * 4), tip, (b0[0] - nx * 4, b0[1] - ny * 4)]), col, 0.0)
    pg.shape(_poly([(hx + 7 * math.cos(a_ * math.pi / 3), hy + 7 * math.sin(a_ * math.pi / 3)) for a_ in range(6)]),
             (120, 126, 138), 0.0)                    # the turret's hub
