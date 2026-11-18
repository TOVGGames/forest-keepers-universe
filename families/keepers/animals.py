"""The animals of the forest at night, drawn in code to field-guide accuracy (docs/engines/forest_keepers_night_animals.md).

Like the bugs (bugs.py): real shape and proportions, real colours and markings, and the way the real animal moves.
Seen from the side (the owl from the front, as it perches), facing right; face=-1 mirrors.

    draw_animal(c, kind, x, ground_y, s, t, face=1, **pose)   s = the animal's height scale in world units

Markings that make each one itself: the raccoon's black mask and ringed tail and its clever hands; the barred owl's
dark eyes, round head with no ear tufts, barred collar and streaked belly; the Virginia opossum's white face, pink
nose, black ears and legs, bare tail and the babies riding on her back; the southern flying squirrel's big dark eyes
and the furry skin between its legs it glides on; the red fox's black stockings, black-backed ears and white tail tip;
the white-tailed deer's white throat patch, eye ring and nose band and the white under its tail, and the fawn's spots.
"""
import math

import numpy as np

from families.foundry.keepers.common import lerp, smoothstep
from families.foundry.products.monster import Xform, ellipse

ANIMALS = {
    "raccoon": dict(name="Raccoon", line=["Its front paws are so sensitive, it can", "feel what it's holding without looking."]),
    "owl": dict(name="Barred Owl", line=["It calls \"who cooks for you?\" and its soft", "feathers let it fly almost silently."]),
    "opossum": dict(name="Opossum", line=["North America's only marsupial: the babies", "grow in a pouch, then ride on mom's back."]),
    "squirrel": dict(name="Flying Squirrel", line=["It doesn't really fly: it glides on a", "furry skin stretched between its legs."]),
    "fox": dict(name="Red Fox", line=["Its big ears can hear a mouse squeak", "under the leaves from far away."]),
    "deer": dict(name="White-tailed Deer", line=["It lifts its white tail like a flag", "to tell the others: watch out!"]),
}


def _c(*v):
    return np.array(v, np.float64)


def spline(pts, n=6, closed=True):
    """Catmull-Rom through the points: smooth, organic outlines from a few control points."""
    p = [np.asarray(q, np.float64) for q in pts]
    m = len(p)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1 = p[(i - 1) % m] if closed or i > 0 else p[0], p[i]
        p2 = p[(i + 1) % m]
        p3 = p[(i + 2) % m] if closed or i + 2 < m else p[-1]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            q = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)
            out.append((float(q[0]), float(q[1])))
    if not closed:
        out.append(tuple(p[-1]))
    return out


class F:
    """Local frame: (u, v) in units of s, u forward (towards the face), v up; origin on the ground under the body."""

    def __init__(self, x, y, s, face=1, kx=1.0):
        self.x, self.y, self.s, self.face, self.kx = x, y, s, face, kx

    def p(self, u, v):
        return self.x + self.face * u * self.s * self.kx, self.y - v * self.s

    def zoom(self, u0, v0, k):
        """A frame drawing everything k times bigger about local point (u0, v0) (same coordinates)."""
        X, Y = self.p(u0, v0)
        return F(X - self.face * u0 * self.s * k * self.kx, Y + v0 * self.s * k, self.s * k, self.face, self.kx)

    def pts(self, uv):
        return [self.p(u, v) for u, v in uv]

    def blob(self, c, uv, col, n=6):
        c.polygon(self.pts(spline(uv, n)), col)

    def oval(self, c, u, v, ru, rv, col, n=28):
        c.polygon(self.pts([(u + ru * math.cos(a), v + rv * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, False)]),
                  col)

    def line(self, c, uv, col, w):
        c.polyline(self.pts(uv), col, w * self.s)

    def limb(self, c, a, b, d, w0, w1, col):
        """A tapered leg through hip a, knee b, foot d (local units)."""
        for (p0, p1, ww0, ww1) in ((a, b, w0, (w0 + w1) / 2), (b, d, (w0 + w1) / 2, w1)):
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            c.polygon(self.pts([(p0[0] + nx * ww0, p0[1] + ny * ww0), (p1[0] + nx * ww1, p1[1] + ny * ww1),
                                (p1[0] - nx * ww1, p1[1] - ny * ww1), (p0[0] - nx * ww0, p0[1] - ny * ww0)]), col)
            c.circle(*self.p(*p1), ww1 * self.s, col)


def walk_leg(hip, up, down, ph, stride, lift):
    """A leg on a walk cycle: (hip, knee, foot) in local units; ph 0..1 (stance first half, swing second)."""
    if ph < 0.5:
        fx = hip[0] + stride * (0.5 - 2 * ph)
        fy = 0.0
    else:
        q = (ph - 0.5) * 2
        fx = hip[0] + stride * (-0.5 + q)
        fy = lift * math.sin(math.pi * q)
    foot = (fx, fy)
    kx = (hip[0] + fx) / 2 + up
    ky = (hip[1] + fy) / 2 + down
    return hip, (kx, ky), foot


def speckle(c, f, region, n, col, seed, r=0.008):
    """Grizzled fur: small lighter flecks scattered over a (u0, u1, v0, v1) box, kept inside by the caller's shape."""
    rs = np.random.default_rng(seed)
    u0, u1, v0, v1 = region
    for _ in range(n):
        f.oval(c, rs.uniform(u0, u1), rs.uniform(v0, v1), r * rs.uniform(0.7, 1.3), r * 0.7, col, 6)


def hull(pts):
    """Convex hull (monotone chain) of 2-D points."""
    P = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(P) < 3:
        return P

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def cute_eye(c, f, u, v, r, look=(0.0, 0.0), blink=0.0, iris=_c(36, 26, 22)):
    """A big shiny animal eye: dark, with a large and a small highlight (what makes a face read as cute)."""
    if blink > 0.85:
        f.line(c, [(u - r, v), (u, v - r * 0.35), (u + r, v)], iris, r * 0.45)
        return
    f.oval(c, u, v, r, r * (1 - blink), iris, 22)
    f.oval(c, u + r * 0.32 + look[0] * r * 0.1, v + r * 0.32 + look[1] * r * 0.1, r * 0.34, r * 0.34 * (1 - blink),
           _c(250, 250, 246), 14)
    f.oval(c, u - r * 0.3, v - r * 0.3, r * 0.14, r * 0.14 * (1 - blink), _c(220, 220, 214), 10)


class Head:
    """A round head that can turn: yaw 0 = profile facing forward (u), pi/2 = looking straight at the camera.
    Features sit on the sphere (azimuth b from the face direction, elevation e) and slide round as it turns, the far
    ones hide behind - so a head turn is a smooth turn, never a swap."""

    def __init__(self, f, cu, cv, R, yaw):
        self.f, self.cu, self.cv, self.R, self.yaw = f, cu, cv, R, yaw

    def at(self, b, e, r=1.0):
        a = self.yaw + b
        x, y, z = math.cos(a) * math.cos(e), math.sin(e), math.sin(a) * math.cos(e)
        return (self.cu + self.R * r * x, self.cv + self.R * r * y), z

    def spot(self, c, b, e, ru, rv, col, r=1.0, n=18):
        """A patch on the head (foreshortened as it turns away)."""
        (u, v), z = self.at(b, e, r)
        if z < -0.05:
            return
        k = max(0.15, math.sin(self.yaw + b) * 0.6 + 0.4)
        self.f.oval(c, u, v, ru * k, rv, col, n)


# ----------------------------------------------------------------------------------------------- raccoon

def raccoon_wash(t, wash):
    """The washing paws (advisor FK0023 r8: a 4 px rub, it read as standing frozen with the food on the ground): the two
    front paws roll the food between them, one forward as the other goes back, and dip it in the water and lift it,
    -> (far paw's rub, near paw's rub, paw height), in body units."""
    rub = 0.075 * wash
    up = 0.5 + 0.5 * math.cos(2 * math.pi * t / 1.7)
    return rub * math.sin(t * 5.0 + math.pi), rub * math.sin(t * 5.0), 0.05 + (0.11 * up + 0.01) * wash


def raccoon(c, x, y, s, t, face=1, wash=0.0, walk=0.0, gait=0.0, look=0.0, blink=0.0):
    """Raccoon, storybook-cute but true: a chubby grey body with a lighter belly and darker back, short dark legs and
    hand-like paws, a fluffy tail with black rings, a big round head with the classic black bandit mask over both
    eyes, white brows above it and a white muzzle below with a black nose, round ears with white rims.
    look 0..1 turns the head to look straight at the camera (the whole mask shows); wash 0..1 rubs food at the water."""
    f = F(x, y, s, face)
    GREY, DARK, LIGHT, WHITE, BLACK = _c(140, 134, 128), _c(96, 90, 86), _c(188, 182, 174), _c(238, 236, 230), _c(30, 28, 28)
    cr = 0.08 * wash
    tl = spline([(-0.42, 0.52 - cr), (-0.7, 0.55 - cr), (-0.92, 0.45 - cr + 0.03 * math.sin(t * 1.3)),
                 (-1.02, 0.3 - cr + 0.05 * math.sin(t * 1.3))], 8, closed=False)
    for i, (u, v) in enumerate(tl):
        q = i / (len(tl) - 1)
        r = 0.13 * (1 - 0.25 * q)
        f.oval(c, u, v, r, r, BLACK * 1.4 if int(q * 5.99) % 2 == 1 else GREY * 1.12, 18)
    ph = gait % 1.0
    for row, far in (([((-0.28, 0.3 - cr), 0.5), ((0.2, 0.3 - cr), 0.0)], True),
                     ([((-0.32, 0.28 - cr), 0.0), ((0.24, 0.28 - cr), 0.5)], False)):
        if not far:
            f.blob(c, [(-0.5, 0.42 - cr), (-0.42, 0.66 - cr), (-0.16, 0.76 - cr), (0.14, 0.7 - cr * 1.5),
                       (0.32, 0.56 - cr * 2), (0.32, 0.32 - cr * 1.4), (0.04, 0.22 - cr), (-0.34, 0.22 - cr)], GREY)
            f.blob(c, [(-0.4, 0.62 - cr), (-0.16, 0.73 - cr), (0.1, 0.66 - cr * 1.5), (-0.1, 0.6 - cr),
                       (-0.32, 0.58 - cr)], DARK)                                       # darker back
            f.blob(c, [(-0.3, 0.26 - cr), (0.0, 0.24 - cr), (0.26, 0.32 - cr), (0.08, 0.36 - cr), (-0.22, 0.34 - cr)],
                   LIGHT)                                                                # lighter belly
        for hip, off in row:
            front = hip[0] > 0
            if walk > 0:
                a, b, d = walk_leg(hip, 0.03, 0.03, (ph + off + (0.25 if far else 0)) % 1, 0.22, 0.06)
            elif front and wash > 0:
                rf, rn, pv = raccoon_wash(t, wash)
                a, b, d = hip, (hip[0] + 0.12, 0.14 + 0.5 * (pv - 0.05)), (hip[0] + 0.26 + (rf if far else rn), pv)
            else:
                a, b, d = hip, (hip[0] + 0.02, 0.14), (hip[0] + 0.03, 0.0)
            f.limb(c, a, b, d, 0.085, 0.06, DARK * (0.65 if far else 0.8))
            f.oval(c, d[0] + 0.03, d[1] + 0.03, 0.06, 0.035, BLACK * 1.5, 14)
    yaw = look * math.pi / 2
    hd = Head(f, 0.42, 0.62 - cr * 2.2, 0.21, yaw)
    for sgn in (-1, 1):                                                           # the far ear behind the head
        (eu, ev), z = hd.at(sgn * 1.0, 0.95)
        if z < 0:
            f.oval(c, eu, ev + 0.02, 0.075, 0.085, DARK, 16)
    f.oval(c, hd.cu, hd.cv, hd.R * 1.05, hd.R * 1.0, DARK * 0.9, 36)                # a soft rim: the head reads
    f.oval(c, hd.cu, hd.cv, hd.R, hd.R * 0.95, GREY * 1.12, 36)
    for sgn in (-1, 1):                                                           # cheeks: white ruffs
        hd.spot(c, sgn * 0.85, -0.45, 0.1, 0.075, WHITE, 1.0)
    for sgn in (-1, 1):                                                           # the near ears, white rims
        (eu, ev), z = hd.at(sgn * 1.0, 0.95)
        if z >= 0:
            f.oval(c, eu, ev + 0.02, 0.078, 0.088, WHITE, 16)
            f.oval(c, eu, ev + 0.01, 0.05, 0.06, DARK, 14)
    # the bandit mask: a black band through both eyes and over the bridge of the nose
    band = []
    for b in np.linspace(-0.9, 0.9, 19):
        (mu, mv), z = hd.at(b, 0.12 - 0.05 * abs(b), 1.0)
        if z > -0.02:
            band.append((mu, mv))
    if len(band) > 1:
        f.line(c, band, BLACK, 0.11)
    for sgn in (-1, 1):
        hd.spot(c, sgn * 0.55, 0.1, 0.085, 0.07, BLACK, 1.0)
        (bu, bv), z = hd.at(sgn * 0.55, 0.42, 1.0)                                 # white brow above the mask
        if z > 0:
            f.line(c, [(bu - 0.04, bv - 0.005), (bu + 0.04, bv + 0.01)], WHITE, 0.035)
    # the muzzle: a pale cone towards the face direction, black nose at the tip
    ring = [hd.at(0.48 * math.cos(q), -0.28 + 0.36 * math.sin(q), 0.98)[0] for q in np.linspace(0, 2 * math.pi, 18)]
    tip_r = 1.32
    a = yaw
    tip = (hd.cu + hd.R * tip_r * math.cos(a) * math.cos(-0.22), hd.cv + hd.R * tip_r * math.sin(-0.22))
    f.blob(c, hull(ring + [tip]), WHITE, 3)
    f.oval(c, tip[0] - 0.012 * math.cos(a), tip[1] + 0.01, 0.038, 0.03, BLACK, 14)
    for sgn in (-1, 1):                                                           # the eyes in the mask
        (eu, ev), z = hd.at(sgn * 0.55, 0.1, 1.0)
        if z > 0.05:
            cute_eye(c, f, eu, ev, 0.045 * (0.6 + 0.4 * z), blink=blink)


# ----------------------------------------------------------------------------------------------- barred owl

def owl(c, x, y, s, t, face=1, head=0.0, call=0.0, blink=0.0, wings=0.0, flap=0.0):
    """Barred owl perched, seen from the front: round head, no ear tufts, big dark brown eyes, small yellow bill,
    pale grey-buff facial disc with fine concentric rings and a thin dark rim, brown-and-white barred collar, brown
    streaks down the pale belly, folded brown wings spotted white. head -1..1 turns the head; call puffs the throat.
    wings 0..1 opens its broad wings out from behind the folded ones (1: flying, feet tucked); flap -1..1 beats them
    (slow, soft wingbeats)."""
    f = F(x, y, s, 1)
    BROWN, PALE, DARK, BILL, DISC = _c(126, 98, 70), _c(226, 216, 198), _c(74, 54, 40), _c(234, 206, 96), _c(206, 194, 176)
    if wings > 0.0:                                                               # the open wings, behind the body
        for sx in (-1, 1):
            span = 0.12 + 0.93 * wings
            lift = 0.16 * flap * wings
            r0, tip = 0.16, 0.16 + span
            top = [(sx * r0, 0.74), (sx * (r0 + 0.45 * span), 0.8 + 0.5 * lift + 0.04 * wings),
                   (sx * (r0 + 0.85 * span), 0.74 + lift), (sx * tip, 0.66 + lift)]
            trail = []
            for k in range(5):                                                    # the soft, scalloped trailing edge
                u = 1.0 - k / 4.0
                trail.append((sx * (r0 + span * (0.95 * u + 0.03)), 0.58 + lift * u - 0.12 * wings * math.sin(math.pi * u * 0.9)))
            pts = top + trail + [(sx * (r0 + 0.02), 0.34)]
            f.blob(c, pts, BROWN * 0.92, 6)
            for k in range(4):                                                    # pale bars across the flight feathers
                u = 0.3 + 0.17 * k
                for j in range(3):
                    vv = 0.7 + lift * u - 0.05 * j - 0.04 * wings * j
                    f.oval(c, sx * (r0 + span * u), vv, 0.02 * (0.4 + 0.6 * wings), 0.011, PALE * 0.88, 8)
    f.blob(c, [(-0.1, 0.14), (0.1, 0.14), (0.09, -0.08), (-0.09, -0.08)], BROWN * 0.85, 4)          # tail
    f.blob(c, [(-0.2, 0.74), (0.0, 0.8), (0.2, 0.74), (0.26, 0.46), (0.18, 0.12), (0.0, 0.05), (-0.18, 0.12),
               (-0.26, 0.46)], PALE)
    for k in range(6):                                                            # the barred collar: arcs
        v = 0.74 - k * 0.032
        f.line(c, [(-0.2 + k * 0.01, v - 0.02), (0.0, v + 0.004), (0.2 - k * 0.01, v - 0.02)], BROWN * 0.95, 0.016)
    rs = np.random.default_rng(9)
    for su in np.linspace(-0.16, 0.16, 7):                                        # belly streaks, broken
        v = 0.52
        while v > 0.16:
            L = rs.uniform(0.04, 0.08)
            f.line(c, [(su + rs.uniform(-0.005, 0.005), v), (su * 0.96, v - L)], BROWN * rs.uniform(0.85, 1.05), 0.016)
            v -= L + rs.uniform(0.015, 0.03)
    f.oval(c, 0.0, 0.76 + 0.03 * call, 0.1 * (1 + 0.3 * call), 0.05 * (1 + call), PALE * 1.02, 20)
    for sx in (-1, 1):                                                            # folded wings over the sides
        wing = [(sx * 0.18, 0.76), (sx * 0.29, 0.6), (sx * 0.29, 0.3), (sx * 0.2, 0.06), (sx * 0.15, 0.2),
                (sx * 0.16, 0.6)]
        f.blob(c, wing, BROWN * 0.95, 6)
        for k in range(7):
            v = 0.68 - k * 0.085
            for j in range(2):
                f.oval(c, sx * (0.2 + 0.04 * j), v - 0.01 * j, 0.016, 0.01, PALE * 0.92, 8)
    tuck = 0.07 * min(1.0, wings * 1.5)                                            # (tucked up as it flies)
    for sx in (-0.06, 0.06):                                                      # feathered feet, talons
        f.oval(c, sx, 0.07 + tuck, 0.04, 0.035, PALE * 0.95, 12)
        for k in (-1, 0, 1):
            f.line(c, [(sx + k * 0.02, 0.05 + tuck), (sx + k * 0.03, -0.01 + tuck * 1.4)], DARK, 0.012)
    hu, hv = 0.0, 0.98
    f.oval(c, hu, hv, 0.25, 0.22, BROWN, 40)
    for k in range(6):
        v = hv + 0.2 - k * 0.02
        w = math.sqrt(max(0.0, 0.22 ** 2 - (v - hv) ** 2)) * 1.1
        f.line(c, [(hu - w * 0.8, v), (hu + w * 0.8, v)], PALE * 0.82, 0.01)
    trn = 1.0 - 0.3 * abs(head)
    d = 0.11 * head
    f.oval(c, hu + d, hv - 0.02, 0.2 * trn, 0.18, DARK * 0.9, 40)                 # the thin dark rim
    f.oval(c, hu + d, hv - 0.02, 0.188 * trn, 0.17, DISC, 40)                     # facial disc
    for sx in (-1, 1):
        cx = hu + d + sx * 0.085 * trn
        for r in (0.13, 0.1, 0.07):
            c.polyline(f.pts([(cx + r * 0.75 * trn * math.cos(a), hv - 0.02 + r * 0.85 * math.sin(a))
                              for a in np.linspace(0, 2 * math.pi, 24)]), DISC * 0.86, 0.006 * s)
    f.blob(c, [(hu + d - 0.02, hv + 0.08), (hu + d + 0.02, hv + 0.08), (hu + d + 0.012, hv - 0.04),
               (hu + d - 0.012, hv - 0.04)], PALE, 3)                             # pale feathers between the eyes
    for sx in (-1, 1):
        ex = hu + d + sx * 0.085 * trn
        f.oval(c, ex, hv + 0.0, 0.048, 0.048 * (1 - max(0.0, blink)), _c(40, 26, 20), 22)
        if blink < 0.6:
            f.oval(c, ex + 0.014, hv + 0.016, 0.012, 0.012, _c(220, 214, 200), 10)
    f.blob(c, [(hu + d - 0.022, hv - 0.045), (hu + d + 0.022, hv - 0.045), (hu + d, hv - 0.11)], BILL, 3)


# ----------------------------------------------------------------------------------------------- opossum

def opossum(c, x, y, s, t, face=1, walk=0.0, gait=0.0, babies=3, sniff=0.0, blink=0.0):
    """Virginia opossum, storybook-cute but true: a soft grey coat, a white face with a pointed (not too long) pink-
    nosed snout, big dark shiny eyes, round black ears with pale tips, short dark legs with pale hand-like feet, a
    long bare tail (dark at the base), and her babies riding on her back."""
    f = F(x, y, s, face)
    GREY, LIGHT, WHITE, BLACK, PINK = _c(176, 172, 166), _c(206, 202, 196), _c(240, 238, 232), _c(40, 36, 36), _c(236, 174, 176)
    tp = spline([(-0.48, 0.28), (-0.75, 0.24), (-0.98, 0.14 + 0.03 * math.sin(t)), (-1.12, 0.1)], 7, False)
    for i in range(len(tp) - 1):
        q = i / (len(tp) - 1)
        f.line(c, [tp[i], tp[i + 1]], lerp(BLACK * 1.5, PINK * 0.92, min(1.0, q * 3.0)), 0.05 * (1 - 0.6 * q))
    ph = gait % 1.0
    for row, far in (([((-0.28, 0.26), 0.5), ((0.2, 0.25), 0.0)], True),
                     ([((-0.32, 0.24), 0.0), ((0.24, 0.23), 0.5)], False)):
        if not far:
            f.blob(c, [(-0.5, 0.3), (-0.4, 0.52), (-0.12, 0.6), (0.16, 0.54), (0.32, 0.42), (0.3, 0.24),
                       (0.0, 0.17), (-0.38, 0.18)], GREY)
            f.blob(c, [(-0.36, 0.5), (-0.12, 0.58), (0.12, 0.52), (-0.1, 0.48)], LIGHT)   # soft long guard hairs
        for hip, off in row:
            if walk > 0:
                a, b, d = walk_leg(hip, 0.03, 0.025, (ph + off + (0.25 if far else 0)) % 1, 0.2, 0.06)
            else:
                a, b, d = hip, (hip[0] + 0.02, 0.12), (hip[0] + 0.03, 0.0)
            f.limb(c, a, b, d, 0.062, 0.04, BLACK * (0.75 if far else 1.0))
            f.oval(c, d[0] + 0.035, d[1] + 0.02, 0.055, 0.03, PINK * 0.95, 14)
    hx, hy = 0.34, 0.42 + 0.015 * sniff
    f.oval(c, hx + 0.02, hy + 0.15, 0.065, 0.075, BLACK, 18)                       # round black ear
    f.oval(c, hx + 0.02, hy + 0.2, 0.035, 0.025, WHITE * 0.95, 12)
    f.oval(c, hx + 0.06, hy + 0.02, 0.15, 0.13, WHITE, 30)                          # round white head
    f.blob(c, [(hx + 0.12, hy + 0.08), (hx + 0.24, hy + 0.04), (hx + 0.34, hy - 0.04), (hx + 0.34, hy - 0.08),
               (hx + 0.2, hy - 0.08), (hx + 0.1, hy - 0.06)], WHITE)                 # the snout
    f.oval(c, hx + 0.345, hy - 0.06, 0.032, 0.028, PINK, 14)
    cute_eye(c, f, hx + 0.12, hy + 0.04, 0.035, blink=blink)
    f.line(c, [(hx + 0.22, hy - 0.07), (hx + 0.28, hy - 0.075)], PINK * 0.7, 0.008)   # a little smile
    for k in (-1, 0, 1):
        f.line(c, [(hx + 0.29, hy - 0.05), (hx + 0.41, hy - 0.03 + k * 0.025)], WHITE * 0.85, 0.005)
    for q in range(babies):                                                       # the babies on her back
        bu = -0.3 + q * 0.18 + 0.012 * math.sin(t * 1.7 + q * 2)
        bv = 0.55 - 0.1 * abs(bu + 0.1) ** 1.4
        bf = F(*f.p(bu, bv), s * 0.3, face)
        bf.line(c, [(-0.42, 0.12), (-0.66, 0.2), (-0.8, 0.06)], PINK * 0.85, 0.05)
        bf.blob(c, [(-0.45, 0.12), (-0.22, 0.34), (0.16, 0.34), (0.36, 0.16), (0.06, -0.02), (-0.36, 0.0)], GREY)
        bf.oval(c, 0.28, 0.38, 0.1, 0.12, BLACK, 14)
        bf.oval(c, 0.38, 0.2, 0.2, 0.17, WHITE, 22)
        bf.blob(c, [(0.48, 0.24), (0.66, 0.16), (0.68, 0.1), (0.5, 0.1)], WHITE, 3)
        bf.oval(c, 0.68, 0.12, 0.05, 0.045, PINK, 10)
        cute_eye(c, bf, 0.44, 0.22, 0.055)
        bf.limb(c, (0.1, 0.05), (0.13, -0.05), (0.18, -0.1), 0.06, 0.045, BLACK)    # holding on to her fur


def opossum_back(c, x, y, s, t, babies=3):
    """The opossum seen from behind: the in-between pose as she turns round (FK0023 r5: a one-frame mirror flip;
    squashing the side view makes a stick). Round grey back with her babies on top, the back of her white head and
    both black ears over it, short dark legs with pink feet, her long bare tail hanging and curling to one side."""
    f = F(x, y, s, 1)
    GREY, LIGHT, WHITE, BLACK, PINK = _c(176, 172, 166), _c(206, 202, 196), _c(240, 238, 232), _c(40, 36, 36), _c(236, 174, 176)
    for k in (-1, 1):                                                         # front legs, behind
        f.limb(c, (k * 0.07, 0.22), (k * 0.075, 0.1), (k * 0.08, 0.0), 0.05, 0.035, BLACK * 0.75)
        f.oval(c, k * 0.08, 0.015, 0.045, 0.025, PINK * 0.8, 12)
    for k in (-1, 1):                                                         # ears, then the top of her head
        f.oval(c, k * 0.085, 0.585, 0.045, 0.05, BLACK * 1.3, 14)              # just showing over her shoulders
    f.oval(c, 0.0, 0.52, 0.1, 0.07, WHITE * 0.88, 22)
    f.oval(c, 0.0, 0.34, 0.3, 0.2, GREY, 34)                                  # her round back
    f.oval(c, 0.0, 0.44, 0.2, 0.08, LIGHT, 24)                                # soft long guard hairs
    for k in (-1, 1):                                                         # hind legs
        f.limb(c, (k * 0.17, 0.22), (k * 0.18, 0.1), (k * 0.19, 0.0), 0.065, 0.042, BLACK)
        f.oval(c, k * 0.2, 0.018, 0.055, 0.03, PINK * 0.95, 14)
    tp = spline([(0.0, 0.16), (0.06, 0.08), (0.18, 0.03 + 0.01 * math.sin(t)), (0.36, 0.035)], 7, False)
    for i in range(len(tp) - 1):                                              # the bare tail, dark at the base
        q = i / (len(tp) - 1)
        f.line(c, [tp[i], tp[i + 1]], lerp(BLACK * 1.5, PINK * 0.92, min(1.0, q * 3.0)), 0.05 * (1 - 0.6 * q))
    for q in range(babies):                                                   # the babies on her back, from behind
        bu = (q - (babies - 1) / 2) * 0.15
        bv = 0.53 - 0.05 * abs(bu) / 0.15
        f.oval(c, bu, bv, 0.08, 0.066, GREY * 0.8, 18)
        f.oval(c, bu, bv, 0.07, 0.056, GREY * 1.06, 18)
        for e in (-1, 1):
            f.oval(c, bu + e * 0.035, bv + 0.055, 0.02, 0.024, BLACK * 1.3, 10)


# ----------------------------------------------------------------------------------------------- flying squirrel

def squirrel(c, x, y, s, t, face=1, glide=0.0, ang=0.0, climb=0.0, cling=1.0):
    """Southern flying squirrel. glide 1: gliding, legs out, the furry skin between them spread like a little sail,
    flat tail behind. Otherwise clinging to a tree trunk (the trunk on its `face` side): belly and all four feet
    against the bark, head up, big dark eyes, flat tail hanging below; climb = how far it has climbed (the feet take
    turns as it goes up)."""
    BROWN, BELLY, DARK = _c(156, 134, 110), _c(236, 228, 214), _c(70, 58, 50)
    if glide > 0.5:
        g = F(x, y, s, face)
        cg = Xform(c, 0, 0, ang * face, 1.0, x, y)
        sail = [(0.32, 0.14), (0.4, 0.2), (0.3, 0.02), (0.25, -0.16), (-0.3, -0.18), (-0.38, -0.2), (-0.3, 0.0),
                (-0.32, 0.18), (-0.4, 0.22), (0.0, 0.16)]
        cg.polygon(g.pts(spline(sail, 5)), BROWN)
        cg.polyline(g.pts(spline(sail, 5)), DARK * 1.3, 0.012 * s, closed=True)
        cg.polygon(g.pts(spline([(-0.35, 0.02), (-0.6, 0.06), (-0.85, 0.02), (-0.6, -0.04)], 5)), BROWN * 0.95)
        cg.polygon(g.pts(spline([(0.2, 0.06), (0.4, 0.1), (0.5, 0.0), (0.4, -0.1), (0.2, -0.06)], 5)), BROWN * 1.06)
        cg.polygon(g.pts([(0.4 + 0.045 * math.cos(a), 0.03 + 0.045 * math.sin(a)) for a in np.linspace(0, 6.28, 14)]),
                   DARK * 0.45)
        cg.polygon(g.pts([(0.415 + 0.015 * math.cos(a), 0.045 + 0.015 * math.sin(a)) for a in np.linspace(0, 6.28, 8)]),
                   _c(240, 240, 236))
        return
    f = F(x, y, s, face)
    ph = climb * 2.5
    step = math.sin(2 * math.pi * ph)
    f.blob(c, [(0.0, 0.18), (-0.12, -0.05), (-0.16, -0.32), (-0.08, -0.42), (0.02, -0.2), (0.06, 0.1)],
           BROWN * 0.93)                                                          # flat tail hanging down
    f.limb(c, (0.02, 0.18), (0.1, 0.1 + 0.03 * step), (0.17, 0.12 + 0.05 * step), 0.05, 0.03, BROWN * 0.85)   # hind
    f.blob(c, [(-0.02, 0.12), (-0.08, 0.32), (-0.04, 0.55), (0.08, 0.62), (0.15, 0.48), (0.16, 0.2), (0.1, 0.08)],
           BROWN)                                                                 # body, belly to the bark
    f.blob(c, [(0.1, 0.12), (0.15, 0.24), (0.15, 0.46), (0.11, 0.5), (0.08, 0.3)], BELLY, 4)
    f.limb(c, (0.08, 0.5), (0.13, 0.56 - 0.03 * step), (0.17, 0.6 - 0.05 * step), 0.045, 0.028, BROWN * 0.95)  # front
    f.oval(c, 0.06, 0.7, 0.12, 0.11, BROWN * 1.05, 26)                              # round head, looking about
    f.oval(c, -0.01, 0.8, 0.04, 0.055, BROWN * 0.9, 12)                             # ear
    f.oval(c, 0.14, 0.66, 0.03, 0.025, BELLY, 10)                                   # pale cheek
    cute_eye(c, f, 0.1, 0.72, 0.045)


# ----------------------------------------------------------------------------------------------- red fox

def fox(c, x, y, s, t, face=1, sit=1.0, ears=0.0, walk=0.0, gait=0.0, tail=0.0, blink=0.0, alive=0.0):
    """Red fox, storybook-cute but true: orange-red coat, white chin, chest and tail tip, black 'stockings',
    big black-backed pointed ears, a narrow muzzle, amber eyes, a big bushy tail. sit 1: sitting very still, tail
    round the feet; ears -1..1 turn as it listens; walk: an easy trot. alive 0..1 (FK0023 r5: the sitting fox read as
    a cut-out): its tail tip curls with tail, it breathes, its ears turn further."""
    f = F(x, y, s, face)
    RED, LIGHTRED, WHITE, BLACK, DARKRED = _c(210, 106, 44), _c(226, 138, 72), _c(242, 236, 226), _c(32, 26, 24), _c(168, 76, 32)
    if sit > 0.5:
        tw = 0.1 * tail * alive                                                  # the tail tip curls and uncurls
        f.blob(c, [(-0.3, 0.05), (-0.7, 0.1 + 0.5 * tw), (-0.86 - 0.3 * tw, 0.22 + tw), (-0.6, 0.2 + 0.6 * tw),
                   (-0.1, 0.12)], RED * 0.95)
        f.oval(c, -0.84 - 0.3 * tw, 0.19 + tw, 0.08, 0.06, WHITE, 16)
        f.blob(c, [(-0.38, 0.05), (-0.42, 0.35), (-0.22, 0.62), (0.08, 0.86), (0.2, 0.7), (0.16, 0.3), (0.12, 0.05)],
               RED)
        f.blob(c, [(0.04, 0.82), (0.18, 0.72), (0.18, 0.42), (0.08, 0.5)], WHITE)
        f.blob(c, [(-0.4, 0.05), (-0.42, 0.28), (-0.25, 0.32), (-0.12, 0.12), (-0.15, 0.04)], DARKRED)
        for du in (0.05, 0.13):
            k = 1.0 if du > 0.1 else 0.8
            f.limb(c, (du, 0.46), (du + 0.01, 0.3), (du + 0.015, 0.2), 0.05, 0.04, RED * 0.9 * k)
            f.limb(c, (du + 0.015, 0.24), (du + 0.02, 0.12), (du + 0.025, 0.02), 0.038, 0.03, BLACK * k)
            f.oval(c, du + 0.04, 0.02, 0.045, 0.022, BLACK * k, 10)
        hx, hy = 0.18, 0.98 + 0.012 * alive * math.sin(t * 1.6)                # breathing
        f = f.zoom(hx + 0.05, hy - 0.05, 1.3)
    else:
        ph = gait % 1.0
        for hip, off in (((-0.32, 0.42), 0.5), ((0.24, 0.44), 0.0)):             # far legs
            a, b, d = walk_leg(hip, 0.04, 0.03, (ph + off + 0.25) % 1, 0.26, 0.08)
            f.limb(c, a, b, d, 0.05, 0.028, BLACK * 0.75)
        tw = 0.05 * math.sin(t * 2.2) + 0.05 * tail
        f.blob(c, [(-0.38, 0.58), (-0.62, 0.62 + tw), (-0.86, 0.56 + tw * 1.5), (-0.98, 0.46 + tw * 2),
                   (-0.84, 0.42 + tw), (-0.6, 0.44), (-0.4, 0.5)], RED * 0.96)        # big bushy tail
        f.oval(c, -0.95, 0.47 + tw * 2, 0.07, 0.055, WHITE, 16)
        f.blob(c, [(-0.42, 0.5), (-0.36, 0.64), (-0.05, 0.66), (0.24, 0.64), (0.4, 0.58), (0.42, 0.44), (0.24, 0.4),
                   (-0.1, 0.42), (-0.36, 0.42)], RED)                                # slim body
        f.blob(c, [(0.28, 0.44), (0.42, 0.46), (0.46, 0.62), (0.36, 0.56)], WHITE)    # chest
        for hip, off in (((-0.36, 0.42), 0.0), ((0.28, 0.44), 0.5)):             # near legs, black stockings
            a, b, d = walk_leg(hip, 0.04, 0.03, (ph + off) % 1, 0.26, 0.08)
            f.limb(c, (a[0], a[1] + 0.06), a, b, 0.075, 0.05, RED if a[0] < 0 else LIGHTRED)   # the thigh / upper leg
            f.limb(c, a, b, d, 0.04, 0.03, BLACK)                                             # black stocking
            f.oval(c, d[0] + 0.03, d[1] + 0.015, 0.045, 0.022, BLACK, 10)
        f.blob(c, [(0.3, 0.56), (0.4, 0.66), (0.52, 0.78), (0.6, 0.72), (0.48, 0.56)], RED)      # neck
        hx, hy = 0.54, 0.76
        f = f.zoom(hx, hy, 1.35)
    f.blob(c, [(hx - 0.1, hy - 0.02), (hx - 0.05, hy + 0.08), (hx + 0.08, hy + 0.08), (hx + 0.28, hy - 0.04),
               (hx + 0.28, hy - 0.07), (hx + 0.1, hy - 0.11), (hx - 0.06, hy - 0.12)], RED)
    f.blob(c, [(hx + 0.0, hy - 0.06), (hx + 0.26, hy - 0.06), (hx + 0.1, hy - 0.12)], WHITE)
    for k, du in enumerate((-0.04, 0.03)):
        tilt = (0.09 + 0.09 * alive) * ears * (1 if k else -1)                 # (advisor FK0023 r3: 0.04 read as frozen)
        f.blob(c, [(hx + du - 0.045, hy + 0.05), (hx + du + tilt, hy + 0.25), (hx + du + 0.05, hy + 0.05)],
               BLACK if k == 0 else RED * 0.92, 3)
        if k:
            f.blob(c, [(hx + du - 0.02, hy + 0.06), (hx + du + tilt * 0.8, hy + 0.2), (hx + du + 0.025, hy + 0.06)],
                   WHITE * 0.9, 3)
    cute_eye(c, f, hx + 0.1, hy + 0.0, 0.026, blink=blink, iris=_c(120, 80, 30))
    f.oval(c, hx + 0.28, hy - 0.055, 0.025, 0.02, BLACK, 10)


# ----------------------------------------------------------------------------------------------- white-tailed deer

def deer(c, x, y, s, t, face=1, fawn=False, walk=0.0, gait=0.0, flag=0.0, head_up=1.0, ears=0.0):
    """White-tailed deer (a doe; fawn=True her spotted fawn): slender, reddish-brown back fading to a white belly,
    deep chest, long neck, big ears, white eye ring, white band behind the black nose, white throat patch; legs
    with the hind leg's backward hock; a brown tail that flags up to show the white underneath."""
    f = F(x, y, s, face, kx=0.84)
    COAT = _c(152, 108, 70) if not fawn else _c(180, 110, 62)
    WHITE, DARK, HOOF = _c(240, 234, 224), _c(66, 48, 36), _c(38, 30, 26)
    ph = gait % 1.0

    def hind(hip, p, col):
        if walk > 0:
            sw = 0.16 * math.sin(2 * math.pi * p)
            lift = 0.06 * max(0.0, math.sin(2 * math.pi * p))
        else:
            sw, lift = 0.0, 0.0
        st = (hip[0] + 0.06 + sw * 0.5, 0.36 + lift)
        hk = (hip[0] - 0.06 + sw * 0.8, 0.2 + lift)
        hf = (hip[0] - 0.02 + sw, 0.0 + lift * 0.7)
        f.blob(c, [(hip[0] - 0.1, hip[1] + 0.06), (hip[0] + 0.1, hip[1] + 0.04), (st[0] + 0.04, st[1]),
                   (st[0] - 0.05, st[1] - 0.02)], col, 4)                            # thigh
        f.limb(c, st, hk, hf, 0.05, 0.026, col)
        f.oval(c, hf[0] + 0.015, hf[1] + 0.012, 0.025, 0.016, HOOF, 10)

    def front(sh, p, col):
        if walk > 0:
            sw = 0.16 * math.sin(2 * math.pi * p)
            lift = 0.07 * max(0.0, math.sin(2 * math.pi * p))
        else:
            sw, lift = 0.0, 0.0
        kn = (sh[0] + 0.01 + sw * 0.6, 0.22 + lift)
        hf = (sh[0] + 0.02 + sw, 0.0 + lift * 0.6)
        f.limb(c, (sh[0] + 0.02, sh[1] + 0.06), (sh[0], sh[1] - 0.06), hf, 0.07, 0.026, col)
        f.limb(c, (sh[0], sh[1] - 0.06), kn, hf, 0.05, 0.026, col)
        f.oval(c, hf[0] + 0.015, hf[1] + 0.012, 0.025, 0.016, HOOF, 10)

    hind((-0.33, 0.54), ph + 0.5, COAT * 0.72)
    front((0.28, 0.48), ph, COAT * 0.72)
    tail_up = 0.18 * flag
    f.blob(c, [(-0.46, 0.66), (-0.54, 0.66 + tail_up), (-0.58, 0.56 + tail_up * 1.3), (-0.5, 0.56)],
           WHITE if flag > 0.4 else COAT * 0.85, 4)
    body = [(-0.48, 0.58), (-0.44, 0.68), (-0.1, 0.66), (0.22, 0.7), (0.36, 0.72), (0.44, 0.6), (0.38, 0.4),
            (0.16, 0.36), (-0.2, 0.38), (-0.42, 0.44)]
    f.blob(c, body, COAT)
    f.blob(c, [(-0.36, 0.42), (-0.1, 0.38), (0.16, 0.37), (0.34, 0.42), (0.1, 0.45), (-0.2, 0.46)], WHITE * 0.96)
    hind((-0.36, 0.52), ph, COAT * 0.95)
    front((0.32, 0.46), ph + 0.5, COAT * 0.95)
    if fawn:
        rs = np.random.default_rng(11)
        for k in range(22):
            f.oval(c, rs.uniform(-0.4, 0.3), rs.uniform(0.52, 0.66), 0.018, 0.014, WHITE, 8)
    hu, hv = 0.52 + 0.06 * head_up, 0.62 + 0.36 * head_up
    f.blob(c, [(0.3, 0.7), (0.4, 0.74), (hu - 0.02, hv + 0.02), (hu + 0.06, hv - 0.04), (0.5, 0.56), (0.42, 0.52)],
           COAT)                                                                   # neck
    f.oval(c, (0.46 + hu) / 2 + 0.04, (0.6 + hv) / 2 - 0.0, 0.04, 0.05, WHITE, 14)   # throat patch
    for k, du in enumerate((-0.03, 0.03)):                                        # big ears
        tilt = 0.04 * ears * (1 if k else -1)
        f.blob(c, [(hu + du - 0.02, hv + 0.05), (hu + du - 0.12 + tilt, hv + 0.15), (hu + du - 0.07 + tilt, hv + 0.18),
                   (hu + du + 0.03, hv + 0.07)], COAT * (0.8 if k == 0 else 1.02), 4)
        if k:
            f.blob(c, [(hu + du - 0.02, hv + 0.06), (hu + du - 0.1 + tilt, hv + 0.15), (hu + du + 0.01, hv + 0.08)],
                   WHITE * 0.85, 3)
    f.blob(c, [(hu - 0.06, hv + 0.02), (hu + 0.0, hv + 0.08), (hu + 0.1, hv + 0.06), (hu + 0.24, hv - 0.04),
               (hu + 0.25, hv - 0.08), (hu + 0.14, hv - 0.09), (hu + 0.0, hv - 0.06)], COAT * 1.05)
    f.oval(c, hu + 0.08, hv + 0.028, 0.034, 0.03, WHITE, 14)                       # eye ring
    cute_eye(c, f, hu + 0.08, hv + 0.028, 0.025)
    f.blob(c, [(hu + 0.16, hv - 0.02), (hu + 0.2, hv - 0.01), (hu + 0.21, hv - 0.08), (hu + 0.16, hv - 0.08)],
           WHITE, 3)                                                              # band behind the nose
    f.oval(c, hu + 0.235, hv - 0.065, 0.022, 0.02, HOOF, 10)


def deer_back(c, x, y, s, t, flag=0.0):
    """The doe seen from behind: the in-between pose as she turns round (FK0017 r2: squashing the side view to turn
    it made a stick puppet with joint balls). Rump with its white patch and tail, hind legs, neck, back of the head,
    both big ears."""
    f = F(x, y, s, 1, kx=0.84)
    COAT, WHITE, HOOF = _c(152, 108, 70), _c(240, 234, 224), _c(38, 30, 26)
    for k in (-1, 1):                                                         # front legs, behind
        f.blob(c, [(k * 0.05, 0.46), (k * 0.1, 0.46), (k * 0.09, 0.02), (k * 0.055, 0.02)], COAT * 0.6, 4)
    f.blob(c, [(-0.06, 0.62), (-0.055, 0.9), (0.055, 0.9), (0.06, 0.62)], COAT * 0.92, 4)      # neck
    for k in (-1, 1):                                                         # big ears, their backs to us
        f.blob(c, [(k * 0.02, 0.97), (k * 0.17, 1.06), (k * 0.15, 1.11), (k * 0.0, 1.01)], COAT * 0.9, 4)
    f.oval(c, 0.0, 0.94, 0.075, 0.07, COAT * 1.03, 24)                        # the back of her head
    for k in (-1, 1):                                                         # hind legs
        f.blob(c, [(k * 0.2, 0.6), (k * 0.02, 0.58), (k * 0.06, 0.36), (k * 0.15, 0.34)], COAT * 0.95, 4)
        f.blob(c, [(k * 0.07, 0.38), (k * 0.14, 0.38), (k * 0.12, 0.02), (k * 0.08, 0.02)], COAT * 0.88, 4)
        f.oval(c, k * 0.1, 0.014, 0.03, 0.016, HOOF, 10)
    f.oval(c, 0.0, 0.57, 0.2, 0.15, COAT, 30)                                 # rump
    f.oval(c, 0.0, 0.55, 0.1, 0.1, WHITE * 0.96, 24)                          # the white patch round the tail
    tail_up = 0.12 * flag
    f.blob(c, [(-0.035, 0.67), (0.035, 0.67), (0.03, 0.53 + tail_up), (-0.03, 0.53 + tail_up)],
           WHITE if flag > 0.4 else COAT * 0.85, 4)


def fox_back(c, x, y, s, t, tail=0.0):
    """The fox seen from behind, standing: the in-between pose as it turns round (FK0017 r2). Black-backed ears,
    black stockings, the big bushy tail hanging with its white tip."""
    f = F(x, y, s, 1)
    RED, WHITE, BLACK = _c(210, 106, 44), _c(242, 236, 226), _c(32, 26, 24)
    for k in (-1, 1):                                                         # front legs, behind
        f.blob(c, [(k * 0.04, 0.44), (k * 0.09, 0.44), (k * 0.08, 0.02), (k * 0.05, 0.02)], BLACK * 0.8, 4)
    f.blob(c, [(-0.08, 0.6), (-0.07, 0.76), (0.07, 0.76), (0.08, 0.6)], RED * 0.95, 4)        # neck
    for k in (-1, 1):                                                         # big pointed ears, black backs
        f.blob(c, [(k * 0.04, 0.84), (k * 0.15, 1.04), (k * 0.16, 0.82)], BLACK, 3)
    f.oval(c, 0.0, 0.8, 0.13, 0.1, RED, 26)                                   # the back of its head
    for k in (-1, 1):                                                         # hind legs: red thighs, black stockings
        f.blob(c, [(k * 0.17, 0.56), (k * 0.03, 0.54), (k * 0.07, 0.3), (k * 0.15, 0.3)], RED * 0.96, 4)
        f.blob(c, [(k * 0.08, 0.32), (k * 0.14, 0.32), (k * 0.13, 0.02), (k * 0.09, 0.02)], BLACK, 4)
        f.oval(c, k * 0.11, 0.015, 0.04, 0.02, BLACK, 10)
    f.oval(c, 0.0, 0.53, 0.18, 0.13, RED, 30)                                 # haunches
    sw = 0.03 * math.sin(t * 2.2) + 0.03 * tail
    f.blob(c, [(-0.06, 0.56), (-0.13 + sw, 0.4), (-0.11 + sw, 0.18), (0.0 + sw, 0.09), (0.09 + sw, 0.18),
               (0.09 + sw, 0.4), (0.06, 0.56)], RED * 0.93)                   # the bushy tail, hanging
    f.oval(c, sw * 0.9, 0.12, 0.065, 0.05, WHITE, 16)


DRAW = {"raccoon": raccoon, "owl": owl, "opossum": opossum, "squirrel": squirrel, "fox": fox, "deer": deer}


def draw_animal(c, kind, x, y, s, t=0.0, face=1, **kw):
    DRAW[kind](c, x, y, s, t, face=face, **kw)
