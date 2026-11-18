"""Sleds and the sledding hill for Forest Keepers episode 5 (First Snow).

A sled (side view, nose to the LEFT: the run goes downhill to the left): two bent wooden runners with a curled
nose, five slats across them (we see their ends, evenly spaced), the paint, a pull rope on the nose.

The hill rises to the right of the sled workshop: a short run-out, a long even slope with three bumps, a steeper
start and a flat top with the start line. Three packed lanes run down it side by side (lane 0 nearest us).
Sled physics is real: gravity along the slope, sliding friction on snow, air drag, and a sled leaves the snow
when a bump curves away faster than gravity can hold it (then it flies ballistically and lands).
"""
import math

import numpy as np

from families.foundry.keepers.common import GRAVITY, PLANK, ellipse, lerp, rect, smoothstep
from families.foundry.products.monster import Xform
from families.foundry.style import IRON, lighten
from families.foundry.tree_monsters import BARK, LAMP, TRUNK

from .snow import FIELD, SNOW, SNOW_DEEP, SNOW_SHADE

G = 1000.0
L = 480.0                    # sled length
RUN_H = 28.0                 # runner strip height
DECK_Y = 84.0                # slat tops above the snow
N_SLATS = 5
SLAT_W = 66.0
SLAT_T = 20.0                # slat thickness
ROPE = np.array([176, 150, 104], np.float64)
CURL_R = 44.0


def slat_x(i):
    """Centre of slat i along the sled (local, nose at -L/2), evenly spaced."""
    a, b = -L / 2 + 92, L / 2 - 52
    return lerp(a, b, i / (N_SLATS - 1))


def runner_pts(b, n=40, length=None):
    """Runner strip centreline, local coords (x along the sled, y up = negative), b 0..1 how far the nose is bent.
    The strip keeps its length: straight it sticks out past the nose, bent it curls up and back."""
    S = (length or L) + math.pi * CURL_R * 1.15
    flat = L - 0.0
    pts = []
    for i in range(n + 1):
        s = S * i / n                      # from the tail (x = +L/2) towards the nose
        if s <= flat:
            pts.append((L / 2 - s, -RUN_H / 2))
        else:
            r = s - flat
            phi = b * r / CURL_R               # bent angle so far
            if b < 1e-3:
                pts.append((L / 2 - s, -RUN_H / 2))
            else:
                R = CURL_R / b                 # partly bent: a gentler curve with the same strip length
                pts.append((-L / 2 - R * math.sin(phi), -RUN_H / 2 - R * (1 - math.cos(phi))))
    return pts


def draw_runner(c, x, y, ang, b, col, far=False, w=RUN_H, nose=-1, sc=1.0):
    """One runner strip with its nose bent b, (x, y) = the sled's centre on the snow."""
    xf = Xform(c, 0, 0, ang, sc, x, y, fx=-nose)
    pts = [(x + px, y + py) for px, py in runner_pts(b)]
    shade = 0.72 if far else 1.0
    xf.polyline(pts, col * 0.62 * shade, w + 4)
    xf.polyline(pts, col * shade, w)
    xf.polyline(pts, lighten(col * shade, 1.18), max(2.0, w * 0.18))


def draw_sled(c, x, y, ang, color, runners=(1.0, 1.0), slats=N_SLATS, paint=1.0, rope=1.0, shade=1.0, snow=0.0,
              t=0.0, nose=-1, clamp=0.0, sc=1.0):
    """Sled resting on the snow at (x, y) (centre of the runners' bottom), rotated by ang on screen (rad,
    clockwise; on a hill: hill_ang, so the runners lie flat on the snow). nose -1 = nose to the left (the race), +1 = to the right (the workshop).
    runners: bend of the (near, far) runner, or None if that runner isn't there yet. slats: how many are on
    (fractional = the last one is coming down). paint 0..1 sweeps the colour on from the nose. sc scales the
    whole sled about (x, y) (a sled in a further lane is smaller)."""
    color = np.asarray(color, np.float64)
    wood = PLANK * shade

    def col_at(lx):
        u = (lx + L / 2) / L
        return lerp(wood, color * shade, smoothstep((paint * 1.2 - u) * 6 + 0.5)) if paint > 0 else wood

    xf = Xform(c, 0, 0, ang, sc, x, y, fx=-nose)
    rc = col_at(-L / 2) * 0.85 if paint > 0.9 else wood * 0.85
    if runners[1] is not None:                      # the far runner peeks out above the near one
        draw_runner(c, x - 10 * nose * sc, y - 8 * sc, ang, runners[1], rc, far=True, nose=nose, sc=sc)
    # slats: across the sled, so we see their ends, sitting on the runners. slats = a count (fractional: the
    # last one is coming down) or the set of slat indices that are on
    placed = sorted(slats) if isinstance(slats, (set, list, tuple)) else range(int(math.ceil(slats)))
    for i in placed:
        drop = 0.0 if not isinstance(slats, (int, float)) or i < int(slats) else (1 - (slats - int(slats))) * 70
        sx = x + slat_x(i)
        top = y - DECK_Y - drop
        cc = col_at(slat_x(i))
        xf.polygon([(sx - SLAT_W / 2, top), (sx + SLAT_W / 2, top), (sx + SLAT_W / 2, top + SLAT_T),
                    (sx - SLAT_W / 2, top + SLAT_T)], cc)
        xf.line(sx - SLAT_W / 2, top + 1, sx + SLAT_W / 2, top + 1, lighten(cc, 1.25), 2)
        xf.line(sx - SLAT_W / 2 + 4, top + SLAT_T, sx + SLAT_W / 2 - 4, top + SLAT_T, cc * 0.6, 2)
    if runners[0] is not None:
        draw_runner(c, x, y, ang, runners[0], rc, nose=nose, sc=sc)
        # knees: short posts between the runner and the slats
        for i in (0, 2, 4):
            if i in placed:
                kx = x + slat_x(i)
                xf.line(kx, y - RUN_H, kx, y - DECK_Y + SLAT_T, rc * 0.8, 12)
    if rope > 0 and runners[0] is not None and runners[0] > 0.9:
        nx, ny = x - L / 2 - CURL_R * 0.6, y - RUN_H - CURL_R * 1.1
        ln = 150 * rope
        pts = [(nx, ny)] + [(nx - 0.75 * ln * u, ny + 26 * u + 22 * math.sin(math.pi * u)) for u in (0.25, 0.5, 0.75, 1.0)]
        xf.polyline(pts, ROPE * shade, 4)
    if clamp > 0:                                   # the C-clamp that holds the bend while it sets
        cx_, cy_ = x - L / 2 + 30, y - RUN_H - 10
        xf.polyline([(cx_ - 14, cy_ + 22), (cx_ - 14, cy_ - 30), (cx_ + 18, cy_ - 30), (cx_ + 18, cy_ - 8)],
                    IRON * 1.5 * clamp, 6)
    if snow > 0.5:                                  # a little snow caught on the deck
        for i in placed:
            sx = x + slat_x(i)
            xf.polygon(ellipse(sx, y - DECK_Y, SLAT_W * 0.45, snow * 0.5, 12, math.pi, 2 * math.pi), SNOW)


def deck_point(x, y, ang, lx, nose=-1, sc=1.0):
    """World point on top of the deck at local x = lx (where a rider stands); ang and sc as in draw_sled."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = lx * -nose * sc, -DECK_Y * sc
    return x + px * ca - py * sa, y + px * sa + py * ca


# ====================================================================== the hill

HILL_X0 = 9600.0             # foot of the hill (it rises to the right of the sled workshop)
TOP_X = 50000.0              # top of the slope (the start line is on the flat top beyond)
START_X = 50350.0
TOP_END = 51800.0
BANK_X = 9440.0              # the soft snowbank at the bottom that stops the sleds
LANES = (0.0, -110.0, -220.0)  # lane offsets: lane 0 nearest us; further lanes sit higher on screen ...
LANE_SCALE = (1.0, 0.86, 0.74)   # ... and look smaller
BUMPS = ((35500.0, 64.0, 150.0), (24500.0, 58.0, 150.0), (16000.0, 52.0, 150.0))
LANTERN_EVERY = 1500.0


def _slope_deg(x):
    if x < HILL_X0:
        return 0.0
    if x < HILL_X0 + 2000:
        return 6.2 * smoothstep((x - HILL_X0) / 2000)
    if x < TOP_X - 2400:
        return 6.2
    if x < TOP_X:
        return lerp(6.2, 10.5, smoothstep((x - (TOP_X - 2400)) / 1400))
    if x < TOP_X + 500:
        return 10.5 * (1 - smoothstep((x - TOP_X) / 500))
    return 0.0


_XS = np.arange(0.0, TOP_END + 3000, 5.0)
_SL = np.tan(np.radians(np.array([_slope_deg(x) for x in _XS])))
_YS = G - np.concatenate([[0.0], np.cumsum((_SL[1:] + _SL[:-1]) / 2 * 5.0)])
for _bx, _bh, _bw in BUMPS:
    _YS -= _bh * np.exp(-((_XS - _bx) / _bw) ** 2)


def hill_y(x):
    """Snow surface of lane 0 at x."""
    return float(np.interp(x, _XS, _YS))


def hill_ang(x):
    """Surface angle at x (rad, screen rotation, + = clockwise; the hill rises to the right, so it is negative).
    Pass it straight to draw_sled: the sled then lies parallel to the snow (never nose-up, owner 2026-10-27)."""
    return math.atan((hill_y(x + 6) - hill_y(x - 6)) / 12.0) if x > 0 else 0.0


def lantern_xs():
    return list(np.arange(HILL_X0 + 900, TOP_X + 1, LANTERN_EVERY))


def draw_hill(c, s, t, lit=None, groove=1.0, packed=None):
    """The hill under the view: the snowy slope with its three lanes (packed up to `packed` x if given),
    its far edge, and the lantern posts on the far side (lit: x -> 0..1)."""
    x0, x1 = s.view()[:2]
    if x1 < HILL_X0 - 400:
        return
    a = max(x0 - 200, LANES_X0)
    b = x1 + 200
    if b <= a:
        return
    xs = np.linspace(a, b, max(20, int((b - a) / max(30.0, 3.0 / s.zoom))))
    far = [(x, hill_y(x) + (LANES[2] - 30) * lane_w(x)) for x in xs]
    near = [(x, hill_y(x) + 16) for x in xs]
    deep = G + 40000.0
    c.polygon(far + near[::-1], SNOW)
    c.polyline(far, lighten(SNOW, 1.06), 3)
    c.polygon(near + [(b, deep), (a, deep)], FIELD)            # the near side of the hill, like the snowy field
    for k, off in enumerate((140.0, 330.0, 600.0, 980.0)):     # soft drifts on it, following the slope
        c.polyline([(x, y + off + 14 * math.sin(x * 0.004 + k)) for x, y in near], FIELD * (1.07 - 0.015 * k), 4)
    c.polyline(near, SNOW_SHADE * 0.95, 3)
    # the three lanes: packed grooves (slightly blue, smooth) where Digs has packed them
    for li, dy in enumerate(LANES):
        pts = [(x, hill_y(x) + dy) for x in xs if (packed is None or x <= packed) and lane_w(x) > 0.98]
        if len(pts) > 1:
            c.polyline(pts, SNOW_DEEP * (0.92 + 0.03 * li), 22 * groove)
            c.polyline([(x, y + 9) for x, y in pts], SNOW_SHADE * 0.95, 3 * groove)
    for lx in lantern_xs():
        if x0 - 200 < lx < x1 + 200:
            lantern_post(c, s, lx, hill_y(lx) + LANES[2] - 34, 1.0 if lit is None else lit(lx), t)


LANES_X0 = HILL_X0 - 2400.0  # the packed lanes start on the flat, by the parked sleds


def lane_w(x):
    """0..1 how far the lane band has opened out (it starts on the flat ground left of the hill)."""
    return smoothstep((x - LANES_X0) / 700.0)


def lantern_post(c, s, x, y, lit, t, h=230.0):
    """A lantern on a post stuck in the snow at (x, y)."""
    c.line(x, y, x, y - h, TRUNK * 0.9, 10)
    c.line(x, y - h + 4, x + 34, y - h + 4, TRUNK * 0.9, 6)
    lx, ly = x + 30, y - h + 18 + 3 * math.sin(t * 1.5 + x)
    c.line(lx, ly - 14, lx, ly - 6, IRON * 1.4, 2)
    c.polygon([(lx - 12, ly - 6), (lx + 12, ly - 6), (lx + 14, ly + 20), (lx - 14, ly + 20)],
              np.array([50, 50, 46]) + LAMP * 0.85 * lit)
    c.polygon(ellipse(lx, ly - 7, 14, 4, 12, math.pi, 2 * math.pi), SNOW)
    if lit > 0:
        r = max(46.0, 26.0 / s.zoom)                # seen from far away a lantern is still a warm dot
        if s.zoom < 0.3:
            c.circle(lx, ly + 6, 4.0 / s.zoom, LAMP * lit)
        s.glow_draw(lambda g: g.circle(lx, ly + 8, r, LAMP * (0.5 if s.zoom >= 0.3 else 0.8) * lit))
        s.glow_draw(lambda g: g.polygon(ellipse(lx, y + 4, 120, 22, 20), LAMP * 0.08 * lit))


def snowbank(c, x=BANK_X, y=G, w=260.0, h=120.0, dent=0.0):
    """The soft snowbank at the bottom of the run (dent 0..1 where the sleds plowed in)."""
    pts = ellipse(x - w * 0.4, y, w, h, 40, math.pi, 2 * math.pi)
    c.polygon(pts, SNOW)
    c.polygon(ellipse(x - w * 0.55, y - h * 0.15, w * 0.6, h * 0.55, 30, math.pi, 2 * math.pi), lighten(SNOW, 1.04))
    if dent > 0:
        c.polygon(ellipse(x - w * 0.05, y - h * 0.45, 60 * dent, 30 * dent, 20), SNOW_SHADE)


# ====================================================================== sled physics

class Ride:
    """One sled's run down the hill, worked out in advance with real physics (so it plays back the same in
    every frame and every render). Positions are lane 0 coordinates; the lane offset is added when drawing."""

    def __init__(self, x0, v0, mu, kd, t_push, bank=BANK_X, dt=1 / 600.0, t_max=80.0):
        self.t_push = t_push
        g = GRAVITY
        x, y = x0, hill_y(x0)
        vx, vy = -v0, 0.0
        air = False
        out = []
        t = 0.0
        while t < t_max:
            gy = hill_y(x)
            if not air:
                th = math.atan2(hill_y(x - 3) - hill_y(x + 3), 6)       # >0: the surface goes down to the left
                # speed along the surface (to the left = positive)
                v = math.hypot(vx, vy) * (1 if vx <= 0 else -1)
                a = g * math.sin(th) - (mu * g * math.cos(th) + kd * v * v) * (1 if v > 0 else -1 if v < 0 else 0)
                if x < bank + 60:                                   # plowing into the soft bank
                    a -= (1800.0 + v * v / 400.0) * (1 if v > 0 else 0)
                v_new = v + a * dt
                if v > 0 and v_new < 0 or (v <= 0 and v_new <= 0 and x < bank + 200):
                    v_new = 0.0
                v = v_new
                vx, vy = -v * math.cos(th), v * math.sin(th)
                nx, ny = x + vx * dt, y + vy * dt
                # over a crest the ground curves away; if gravity can't bend our path that fast, we fly
                if v * v * _curv(x) > g * math.cos(th):
                    air = True
                    x, y = nx, ny
                else:
                    x, y = nx, hill_y(nx)
            else:
                vy += g * dt
                x += vx * dt
                y += vy * dt
                if y >= hill_y(x):                                   # landing: keep the speed along the surface
                    th = math.atan2(hill_y(x - 3) - hill_y(x + 3), 6)
                    tx_, ty_ = -math.cos(th), math.sin(th)
                    v = vx * tx_ + vy * ty_
                    vx, vy = v * tx_, v * ty_
                    y = hill_y(x)
                    air = False
                    out.append((t, x, y, air, True))
                    t += dt
                    continue
            out.append((t, x, y, air, False))
            t += dt
            if x < bank + 200 and abs(vx) < 1.0 and not air:
                break
        arr = np.array([(o[0], o[1], o[2], 1.0 if o[3] else 0.0) for o in out])
        k = max(1, int(round((1 / 120.0) / dt)))
        self.ts, self.xs, self.ys, self.air = arr[::k, 0], arr[::k, 1], arr[::k, 2], arr[::k, 3]
        self.landings = [o[0] for o in out if o[4]]
        self.takeoffs = [out[i][0] for i in range(1, len(out)) if out[i][3] and not out[i - 1][3]]
        self.dur = float(self.ts[-1])
        # pitch: follows the surface on the snow, eases towards the flight path in the air
        ang = []
        a_prev = hill_ang(self.xs[0])
        for i in range(len(self.ts)):
            if self.air[i] > 0.5 and 0 < i < len(self.ts) - 1:
                target = math.atan2(self.ys[i + 1] - self.ys[i - 1], self.xs[i - 1] - self.xs[i + 1])
            else:
                target = hill_ang(self.xs[i])
            a_prev += (target - a_prev) * 0.07          # the sled settles over ~0.1 s
            ang.append(a_prev)
        self.angs = np.array(ang)
        self.bank_t = next((float(tt) for tt, xx in zip(self.ts, self.xs) if xx < bank + 60), self.dur)

    def at(self, tau):
        """(x, y, ang, airborne, speed) tau seconds after the push."""
        if tau <= 0:
            return float(self.xs[0]), float(self.ys[0]), float(self.angs[0]), False, 0.0
        tau = min(tau, self.dur)
        x = float(np.interp(tau, self.ts, self.xs))
        y = float(np.interp(tau, self.ts, self.ys))
        a = float(np.interp(tau, self.ts, self.angs))
        i = min(len(self.ts) - 1, int(tau * 120))
        j = max(0, i - 1)
        sp = math.hypot(self.xs[i] - self.xs[j], self.ys[i] - self.ys[j]) * 120 if i > j else 0.0
        return x, y, a, self.air[i] > 0.5, sp


def _curv(x):
    """Curvature of the surface at x, > 0 over a crest (y is down, so a crest is a local minimum of y)."""
    h = 8.0
    return (hill_y(x + h) + hill_y(x - h) - 2 * hill_y(x)) / (h * h)
