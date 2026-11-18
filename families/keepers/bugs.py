"""The bugs of the forest, drawn in code to field-guide accuracy (Bug Hunt, docs/engines/forest_keepers_bug_hunt.md).

Owner (2026-11-01): each bug gets a close-up and "should look like the real bug". So these are not cartoon bugs:
real shape and proportions, real colours and markings, the right number of legs and body parts, and the way the
real one moves (a beetle's tripod gait, a millipede's leg waves, a worm's squeeze-and-stretch, a pill bug rolling
up). Seen from above (dorsal), the way a field guide shows them. Each was checked side by side with photos.

    draw_bug(c, kind, x, y, L, heading, t, gait)   one bug, body length L (world units), heading in radians
    BUGS[kind]                                      name, line on screen, colours

Local frame: u runs along the body (+ = head end, the body spans about -0.5..0.5), v across it, both in units of L.
"""
import math

import numpy as np

from families.foundry.keepers.common import lerp, smoothstep
from families.foundry.products.monster import ellipse

BUGS = {
    "earthworm": dict(name="Earthworm", line=["Digs tunnels that let air and rain", "into the soil, so roots can grow."]),
    "pillbug": dict(name="Pill Bug (Roly-Poly)", line=["Not an insect: it's related to shrimp and crabs!",
                                                       "It eats dead leaves and rolls up into a ball."]),
    "millipede": dict(name="Millipede", line=["Lots of legs: two pairs on most of its body rings.",
                                              "It turns rotting leaves and wood into soil."]),
    "groundbeetle": dict(name="Ground Beetle", line=["A fast night hunter. It eats slugs and", "bugs that chew on plants."]),
    "ladybug": dict(name="Ladybug", line=["Eats the aphids that hurt plants.", "Its bright spots tell birds: I taste bad!"]),
    "firefly": dict(name="Firefly", line=["Makes its own light to talk", "to other fireflies."]),
}

BLACK = np.array([18, 17, 19], np.float64)


def _c(*v):
    return np.array(v, np.float64)


class Frame:
    """Maps the bug's local (u, v) (body lengths) to world points."""

    def __init__(self, x, y, L, heading):
        self.x, self.y, self.L = x, y, L
        self.ca, self.sa = math.cos(heading), math.sin(heading)

    def p(self, u, v):
        return (self.x + (u * self.ca - v * self.sa) * self.L, self.y + (u * self.sa + v * self.ca) * self.L)

    def pts(self, uv):
        return [self.p(u, v) for u, v in uv]

    def oval(self, u, v, ru, rv, n=40, a0=0.0, a1=2 * math.pi):
        return self.pts([(u + ru * math.cos(a), v + rv * math.sin(a))
                         for a in np.linspace(a0, a1, n, endpoint=a1 - a0 < 2 * math.pi - 1e-6)])


def _shade(c, f, u, v, ru, rv, col, gloss=0.6, rim=0.55):
    """A domed oval: base, darker rim, soft lighter top, a small glossy highlight towards the light (upper left)."""
    c.polygon(f.oval(u, v, ru, rv), col * rim)
    c.polygon(f.oval(u + ru * 0.03, v - rv * 0.04, ru * 0.9, rv * 0.86), col)
    c.polygon(f.oval(u + ru * 0.12, v - rv * 0.18, ru * 0.55, rv * 0.45), np.minimum(255, col * 1.18 + 8))
    if gloss > 0:
        c.polygon(f.oval(u + ru * 0.3, v - rv * 0.42, ru * 0.22, rv * 0.12), np.minimum(255, col * 0.4 + 150 * gloss))


def _leg(c, f, u0, v0, ang, l1, l2, bend, col, w, swing):
    """A jointed leg from the body side at (u0, v0): femur at `ang` (+ swing), tibia bent by `bend`, a little foot."""
    a = ang + swing
    k = (u0 + l1 * math.cos(a), v0 + l1 * math.sin(a))
    b = a + bend
    ft = (k[0] + l2 * math.cos(b), k[1] + l2 * math.sin(b))
    c.polyline(f.pts([(u0, v0), k]), col, w * f.L * 1.25)
    c.polyline(f.pts([k, ft]), col, w * f.L)
    c.circle(*f.p(*ft), w * f.L * 0.7, col)


def _six_legs(c, f, bases, angs, l1, l2, bend, col, w, gait, amp=0.32):
    """Three pairs on a tripod gait: front-left, middle-right and hind-left move together, then the other three."""
    for i, (u0, hv) in enumerate(bases):
        for s in (-1, 1):
            ph = gait * 2 * math.pi + (math.pi if (i % 2 == 0) == (s > 0) else 0.0)
            sw = amp * math.sin(ph)
            _leg(c, f, u0, s * hv, s * angs[i], l1[i], l2[i], s * bend[i], col, w, s * sw)


def _antenna(c, f, u0, v0, segs, ang, curve, col, w, wave, club=0.0):
    """Segmented antenna: `segs` lengths, curving by `curve` per segment, waving by `wave`."""
    pts, a, p = [(u0, v0)], ang + wave, (u0, v0)
    for i, sl in enumerate(segs):
        a += curve
        p = (p[0] + sl * math.cos(a), p[1] + sl * math.sin(a))
        pts.append(p)
    c.polyline(f.pts(pts), col, w * f.L)
    for q in pts[1:-1]:
        c.circle(*f.p(*q), w * f.L * 0.62, col)
    if club:
        c.polygon(f.oval(p[0], p[1], club * 1.4, club, 12), col)


# ----------------------------------------------------------------------------------------------- ladybug

def ladybug(c, f, t, gait, k=1.0):
    """Seven-spot ladybird (Coccinella septempunctata): red domed wing cases, 3 black spots on each plus one
    shared behind the black-and-white shield, black head with two pale spots, short black legs and antennae."""
    RED, LEG = _c(206, 34, 26), _c(22, 20, 20)
    _six_legs(c, f, [(0.18, 0.2), (0.04, 0.26), (-0.1, 0.26)], [-1.05, 1.5, 2.05], [0.12, 0.11, 0.13],
              [0.1, 0.1, 0.12], [-0.5, 0.35, 0.55], LEG, 0.02, gait, amp=0.2)
    _antenna(c, f, 0.47, -0.08, [0.06, 0.05, 0.04], -0.7, -0.15, LEG, 0.012, 0.15 * math.sin(t * 3.1), club=0.018)
    _antenna(c, f, 0.47, 0.08, [0.06, 0.05, 0.04], 0.7, 0.15, LEG, 0.012, -0.15 * math.sin(t * 2.7 + 1), club=0.018)
    c.polygon(f.oval(0.43, 0.0, 0.07, 0.14), BLACK)                               # head
    for s in (-1, 1):
        c.polygon(f.oval(0.46, s * 0.075, 0.022, 0.03, 12), _c(232, 226, 210))     # pale spots by the eyes
    c.polygon(f.pts([(0.27, -0.27), (0.29, -0.23), (0.41, -0.2), (0.44, 0.0), (0.41, 0.2), (0.29, 0.23),
                     (0.27, 0.27), (0.24, 0.0)]), BLACK)                          # pronotum
    for s in (-1, 1):                                                             # its white front corners
        c.polygon(f.pts([(0.3, s * 0.245), (0.37, s * 0.215), (0.41, s * 0.16), (0.37, s * 0.15),
                         (0.31, s * 0.19)]), _c(238, 234, 222))
    _shade(c, f, -0.08, 0.0, 0.37, 0.42, RED, gloss=0.9)                         # elytra dome
    c.polyline(f.pts([(0.29, 0.0), (-0.45, 0.0)]), BLACK * 1.5, 0.012 * f.L)       # the suture between the cases
    c.polygon(f.pts([(0.29, -0.06), (0.29, 0.06), (0.2, 0.0)]), BLACK)            # scutellum
    c.polygon(f.oval(0.215, 0.0, 0.06, 0.085, 24), BLACK)                         # the shared spot
    for s in (-1, 1):
        for u, v, r in ((0.13, 0.27, 0.05), (-0.05, 0.2, 0.072), (-0.26, 0.17, 0.055)):
            c.polygon(f.oval(u, s * v, r, r * 1.05, 24), BLACK)
    c.polygon(f.oval(0.13, -0.2, 0.08, 0.04, 16), _c(255, 236, 226) * 0.95)     # gloss
    c.polygon(f.oval(0.15, 0.22, 0.05, 0.025, 16), _c(255, 226, 216) * 0.75)


# ----------------------------------------------------------------------------------------------- firefly

def firefly(c, f, t, gait, glow=None, light=0.0, k=1.0, glow_r=0.42):
    """Common eastern firefly (Photinus pyralis): long soft body, the pale shield over the head with a black spot
    flanked by pink, dark wing cases with pale yellow edges, a yellow-green lantern at the tip of the abdomen."""
    DARK, EDGE, SHIELD, PINK = _c(46, 40, 34), _c(226, 204, 120), _c(232, 210, 140), _c(226, 120, 112)
    _six_legs(c, f, [(0.28, 0.07), (0.14, 0.09), (0.0, 0.09)], [-1.0, 1.45, 2.05], [0.13, 0.13, 0.15],
              [0.12, 0.13, 0.15], [-0.45, 0.3, 0.45], DARK * 0.8, 0.012, gait, amp=0.2)
    for s in (-1, 1):
        _antenna(c, f, 0.45, s * 0.05, [0.05] * 7, s * 0.55, s * 0.08, DARK * 0.9, 0.008,
                 s * 0.12 * math.sin(t * 2.4 + s))
    lx, ly = f.p(-0.47, 0.0)
    for j in range(3):                                                           # the lantern segments
        c.polygon(f.oval(-0.44 - j * 0.035, 0.0, 0.03, 0.12 - j * 0.025, 20), _c(230, 222, 150) * (1 - 0.06 * j))
    if light > 0:
        c.polygon(f.oval(-0.47, 0.0, 0.07, 0.1), np.minimum(255, _c(190, 240, 90) * (0.6 + 0.4 * light) + 50 * light))
        if glow is not None:
            glow.begin(c)
            c.circle(lx, ly, glow_r * f.L, _c(170, 255, 90) * 0.9 * light * min(1.0, 0.25 / glow_r))
            c.circle(lx, ly, glow_r * 0.43 * f.L, _c(220, 255, 150) * light * min(1.0, 0.3 / glow_r))
            glow.end(c)
    for s in (-1, 1):                                                            # wing cases, long and parallel
        pts = [(0.26, s * 0.005), (0.26, s * 0.17), (0.0, s * 0.19), (-0.3, s * 0.18), (-0.44, s * 0.11),
               (-0.47, s * 0.03), (-0.47, s * 0.005)]
        c.polygon(f.pts(pts), DARK)
        c.polyline(f.pts([(0.25, s * 0.165), (0.0, s * 0.185), (-0.3, s * 0.175), (-0.44, s * 0.105)]), EDGE,
                   0.026 * f.L)
        c.polyline(f.pts([(0.25, s * 0.008), (-0.46, s * 0.008)]), EDGE * 0.8, 0.006 * f.L)
        c.polyline(f.pts([(0.2, s * 0.09), (-0.4, s * 0.08)]), DARK * 1.35, 0.01 * f.L)
    c.polygon(f.oval(0.27, 0.0, 0.23, 0.2, 40, -math.pi / 2, math.pi / 2), SHIELD)  # pronotum, hides the head
    c.polygon(f.oval(0.29, 0.0, 0.17, 0.14, 32, -math.pi / 2, math.pi / 2), PINK)
    c.polygon(f.oval(0.33, 0.0, 0.07, 0.035, 20), BLACK)
    c.polygon(f.oval(0.4, -0.1, 0.04, 0.03, 12), np.minimum(255, SHIELD * 1.1))


# ----------------------------------------------------------------------------------------------- ground beetle

def groundbeetle(c, f, t, gait, k=1.0):
    """A ground beetle (Carabus nemoralis): glossy black with a violet-bronze sheen at the edges, grooved wing
    cases, a narrower pronotum, strong jaws, long legs and long thread-like antennae of 11 segments."""
    BODY, SHEEN, LEG = _c(28, 26, 32), _c(110, 80, 140), _c(26, 24, 26)
    _six_legs(c, f, [(0.22, 0.12), (0.1, 0.15), (-0.04, 0.15)], [-0.85, 1.55, 2.25], [0.22, 0.21, 0.26],
              [0.21, 0.24, 0.3], [-0.55, 0.35, 0.4], LEG, 0.019, gait, amp=0.34)
    for s in (-1, 1):
        _antenna(c, f, 0.43, s * 0.06, [0.045] * 11, s * 0.42, s * 0.04, LEG, 0.011,
                 s * 0.14 * math.sin(t * 3.3 + 2 * s))
    for s in (-1, 1):                                                            # mandibles
        c.polygon(f.pts([(0.44, s * 0.03), (0.52, s * 0.05), (0.55, s * 0.02), (0.5, s * 0.01)]), BODY * 1.2)
    c.polygon(f.oval(0.41, 0.0, 0.07, 0.085), BODY)                                # head
    for s in (-1, 1):
        c.circle(*f.p(0.42, s * 0.075), 0.02 * f.L, _c(60, 56, 54))              # eyes
    prn = [(0.24, 0.1), (0.25, 0.16), (0.3, 0.185), (0.35, 0.175), (0.375, 0.12), (0.37, 0.09)]
    c.polygon(f.pts([(u, -v) for u, v in prn] + [(u, v) for u, v in reversed(prn)]), BODY)   # pronotum
    for s in (-1, 1):
        c.polyline(f.pts([(u, s * v * 0.96) for u, v in prn[1:]]), SHEEN * 0.8, 0.006 * f.L)
    c.polyline(f.pts([(0.27, 0.0), (0.35, 0.0)]), BODY * 0.6, 0.006 * f.L)
    ely = [(0.22, 0.0), (0.22, 0.14), (0.15, 0.205), (-0.05, 0.225), (-0.28, 0.19), (-0.43, 0.1), (-0.48, 0.0)]
    for s in (-1, 1):
        pts = f.pts([(u, s * v) for u, v in ely])
        c.polygon(pts, BODY)
        c.polyline(f.pts([(u, s * v * 0.985) for u, v in ely[1:]]), SHEEN, 0.007 * f.L)
        for j in range(1, 8):                                                     # the grooves (striae)
            q = j / 8.0
            c.polyline(f.pts([(0.2, s * 0.14 * q), (0.1, s * 0.2 * q), (-0.08, s * 0.215 * q),
                              (-0.28, s * 0.18 * q), (-0.42, s * 0.09 * q)]), BODY * 0.5, 0.005 * f.L)
        c.polygon(f.oval(0.02, s * 0.1, 0.15, 0.022, 20), _c(78, 76, 92))         # gloss, soft
        c.polygon(f.oval(0.04, s * 0.1, 0.07, 0.01, 16), _c(140, 136, 156))
    c.polyline(f.pts([(0.22, 0.0), (-0.48, 0.0)]), BODY * 0.5, 0.008 * f.L)


# ----------------------------------------------------------------------------------------------- pill bug

def pillbug(c, f, t, gait, roll=0.0, k=1.0):
    """Common pill bug (Armadillidium vulgare): a slate-grey dome of 7 big plates, 5 small ones and a blunt tail
    plate, faint pale speckles, a small head with eyes and a pair of bent antennae, 7 pairs of short legs.
    roll 0..1: it curls up into a ball (it really does)."""
    GREY, PALE, LEG = _c(92, 96, 104), _c(186, 176, 140), _c(150, 140, 132)
    if roll > 0.0:
        r = lerp(0.5, 0.3, smoothstep(roll))
        ru, rv = lerp(0.5, r, roll), lerp(0.3, r, roll)
        _shade(c, f, 0.0, 0.0, ru, rv, GREY, gloss=0.45)
        for j in range(9):                                                        # the plates, curled
            a = lerp(-0.7, 0.7, j / 8)
            c.polyline(f.oval(ru * 0.9 * math.sin(a) * (1 - roll) + 0.0, 0.0, ru * 0.12 + roll * ru * 0.45, rv * 0.98,
                              24, -math.pi / 2, math.pi / 2), GREY * 0.62, 0.01 * f.L)
        if roll < 0.8:
            _pill_head(c, f, t, (1 - roll), GREY, LEG)
        return
    for i in range(7):                                                           # legs: a wave, just peeking out
        u0 = 0.28 - i * 0.085
        for s in (-1, 1):
            ph = gait * 2 * math.pi - i * 0.9 + (0 if s > 0 else math.pi)
            _leg(c, f, u0, s * 0.22, s * (1.5 + 0.08 * i), 0.05, 0.04, s * 0.5, LEG, 0.011, s * 0.3 * math.sin(ph))
    _pill_head(c, f, t, 1.0, GREY, LEG)
    _shade(c, f, -0.02, 0.0, 0.47, 0.29, GREY, gloss=0.35)
    rs = np.random.default_rng(7)
    for i in range(7):                                                           # 7 big plates
        u = 0.36 - i * 0.085
        w = 0.29 * math.sqrt(max(0.0, 1 - ((u + 0.02) / 0.47) ** 2))
        arc = [(u + 0.025 * (1 - ((q - 8) / 8) ** 2), (q - 8) / 8 * w * 0.98) for q in range(17)]
        c.polyline(f.pts(arc), GREY * 0.62, 0.008 * f.L)
        c.polyline(f.pts([(a - 0.007, b) for a, b in arc[1:-1]]), np.minimum(255, GREY * 1.25), 0.006 * f.L)
        for vv in (-0.55, -0.3, 0.3, 0.55):                                       # pale spots in rows
            if rs.uniform() < 0.8:
                c.polygon(f.oval(u - 0.035, vv * w, 0.012, 0.016, 10), PALE * 0.62 + GREY * 0.25)
    for i in range(5):                                                           # 5 small plates + the tail
        u = -0.24 - i * 0.045
        w = 0.29 * math.sqrt(max(0.0, 1 - ((u + 0.02) / 0.47) ** 2))
        c.polyline(f.pts([(u + 0.015 * (1 - ((q - 8) / 8) ** 2), (q - 8) / 8 * w * 0.97) for q in range(17)]),
                   GREY * 0.66, 0.006 * f.L)
    c.polygon(f.oval(0.08, -0.13, 0.22, 0.035, 24), np.minimum(255, GREY * 1.45))    # gloss


def _pill_head(c, f, t, a, GREY, LEG):
    if a <= 0:
        return
    for s in (-1, 1):                                                            # the antennae, elbowed
        _antenna(c, f, 0.47, s * 0.1, [0.05, 0.05, 0.06, 0.04, 0.035][:max(2, int(5 * a))], s * 0.35, s * 0.25,
                 LEG * 0.85, 0.016, s * 0.25 * math.sin(t * 4.0 + s))
    c.polygon(f.oval(0.44, 0.0, 0.07, 0.16), GREY * 0.82)
    for s in (-1, 1):
        c.polygon(f.oval(0.45, s * 0.125, 0.022, 0.03, 12), BLACK)


# ----------------------------------------------------------------------------------------------- long bodies

def body_path(f, n, t, wave, speed, amp, phase=0.0):
    """Points along a long body (head at u=0.5) that winds in a travelling wave."""
    pts = []
    for i in range(n + 1):
        u = 0.5 - i / n
        v = amp * math.sin(u * wave * 2 * math.pi + t * speed + phase) * (0.4 + 0.6 * (i / n))
        pts.append((u, v))
    return pts


def _tube(c, f, pts, width, col, rim=0.6):
    """A round tube along local points: dark rim, the body, a light stripe along the top."""
    n = len(pts)

    def side(sc, off=0.0):
        L, R = [], []
        for i, (u, v) in enumerate(pts):
            a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
            du, dv = b[0] - a[0], b[1] - a[1]
            d = math.hypot(du, dv) or 1.0
            nu, nv = -dv / d, du / d
            w = width(i / (n - 1)) * sc
            L.append((u + nu * (w + off), v + nv * (w + off)))
            R.append((u - nu * (w - off), v - nv * (w - off)))
        return f.pts(L + R[::-1])

    c.polygon(side(1.0), col * rim)
    c.polygon(side(0.82), col)
    c.polygon(side(0.35, 0.25 * width(0.4)), np.minimum(255, col * 1.25 + 10))
    return side


def earthworm(c, f, t, gait, k=1.0):
    """Common earthworm (Lumbricus terrestris): a long ringed tube, darker and redder at the front, the pale swollen
    saddle (clitellum) a third of the way back, a pointed head and a flattened tail; it moves by squeezing and
    stretching in waves, nearly straight."""
    COL, SADDLE = _c(184, 110, 104), _c(212, 140, 118)
    n = 60
    pts = []
    for i in range(n + 1):
        q = i / n
        sq = 0.012 * math.sin(q * 6 * math.pi - gait * 2 * math.pi)            # the squeeze wave
        u = 0.5 - q + sq
        v = 0.025 * math.sin(q * 2.2 * math.pi + t * 0.6)
        pts.append((u, v))

    def width(q):
        w = 0.03 * min(1.0, q / 0.08) ** 0.6 * (1.0 if q < 0.85 else 1 - (q - 0.85) / 0.2)
        w *= 1 + 0.25 * math.sin(q * 6 * math.pi - gait * 2 * math.pi)
        if 0.26 < q < 0.36:
            w *= 1.22
        return max(0.004, w)

    side = _tube(c, f, pts, width, COL)
    for i in range(2, n - 1):                                                    # the rings
        q = i / n
        u, v = pts[i]
        a, b = pts[i - 1], pts[i + 1]
        du, dv = b[0] - a[0], b[1] - a[1]
        d = math.hypot(du, dv) or 1.0
        nu, nv = -dv / d * width(q) * 0.85, du / d * width(q) * 0.85
        col = SADDLE * 0.86 if 0.26 < q < 0.36 else COL * (0.86 - 0.08 * (1 - q))
        c.polyline(f.pts([(u + nu, v + nv), (u - nu, v - nv)]), col, 0.0025 * f.L)
    i0, i1 = int(0.26 * n), int(0.36 * n)                                      # the saddle (clitellum)
    c.polyline(f.pts(pts[i0:i1 + 1]), SADDLE, width(0.31) * 1.55 * f.L)
    c.polyline(f.pts([(u, v - width(0.31) * 0.3) for u, v in pts[i0:i1 + 1]]), np.minimum(255, SADDLE * 1.15),
               width(0.31) * 0.5 * f.L)
    for i in range(0, int(0.25 * n)):                                            # the darker front
        u, v = pts[i]
        c.circle(*f.p(u, v - width(i / n) * 0.1), width(i / n) * 0.45 * f.L, COL * 0.86)
    c.polyline(f.pts([(u, v - width(0.5) * 0.4) for u, v in pts[3:-6]]), np.minimum(255, COL * 1.45), 0.005 * f.L)


def millipede(c, f, t, gait, k=1.0):
    """American giant millipede (Narceus americanus): a long dark round body of ~50 rings, each edged with a thin
    red-orange band, a rounded head with short antennae, and two pairs of fine legs on most rings moving in waves
    down the body."""
    COL, BAND, LEG = _c(52, 42, 40), _c(150, 66, 46), _c(160, 104, 80)
    n = 50
    pts = body_path(f, n, t, 0.9, 1.2, 0.03, phase=gait * 0.5)

    def width(q):
        return 0.032 * (0.75 + 0.25 * min(1.0, q / 0.06)) * (1.0 if q < 0.9 else 1 - (q - 0.9) / 0.15)

    for i in range(3, n - 1):                                                    # legs, 2 pairs a ring, in waves
        u, v = pts[i]
        a, b = pts[i - 1], pts[i + 1]
        du, dv = b[0] - a[0], b[1] - a[1]
        d = math.hypot(du, dv) or 1.0
        nu, nv = -dv / d, du / d
        for pair in (0, 1):
            ph = gait * 2 * math.pi * 2 - (i * 2 + pair) * 0.55
            sw = 0.008 * math.sin(ph)
            for s in (-1, 1):
                base = (u + s * nu * width(i / n) * 0.8 - du / d * 0.004 * pair,
                        v + s * nv * width(i / n) * 0.8 - dv / d * 0.004 * pair)
                tip = (base[0] + s * nu * 0.016 + du / d * sw, base[1] + s * nv * 0.016 + dv / d * sw)
                c.polyline(f.pts([base, tip]), LEG, 0.003 * f.L)
    _tube(c, f, pts, width, COL, rim=0.5)
    for i in range(2, n):                                                        # the rings and their red edges
        q = i / n
        u, v = pts[i]
        a, b = pts[i - 1], pts[min(n, i + 1)]
        du, dv = b[0] - a[0], b[1] - a[1]
        d = math.hypot(du, dv) or 1.0
        nu, nv = -dv / d * width(q) * 0.92, du / d * width(q) * 0.92
        c.polyline(f.pts([(u + nu, v + nv), (u + du / d * 0.003, v + dv / d * 0.003), (u - nu, v - nv)]), BAND,
                   0.0022 * f.L)
        c.polyline(f.pts([(u + nu * 0.9 - du / d * 0.004, v + nv * 0.9 - dv / d * 0.004),
                          (u - nu * 0.9 - du / d * 0.004, v - nv * 0.9 - dv / d * 0.004)]), COL * 0.62, 0.002 * f.L)
    hu, hv = pts[0]
    for s in (-1, 1):
        _antenna(c, f, hu + 0.01, hv + s * 0.018, [0.012] * 7, s * 0.6, s * 0.05, LEG * 0.8, 0.0035,
                 s * 0.2 * math.sin(t * 3 + s))
    c.polygon(f.oval(hu - 0.005, hv, 0.022, 0.03, 20), COL * 0.95)
    for s in (-1, 1):
        c.circle(*f.p(hu, hv + s * 0.02), 0.005 * f.L, BLACK)
    c.polyline(f.pts([(u, v - width(0.5) * 0.35) for u, v in pts[2:-4]]), np.minimum(255, COL * 1.9), 0.004 * f.L)


DRAW = {"ladybug": ladybug, "firefly": firefly, "groundbeetle": groundbeetle, "pillbug": pillbug,
        "earthworm": earthworm, "millipede": millipede}
# body lengths relative to each other (real sizes: worm ~15 cm, millipede ~10 cm, beetle ~2.5 cm, pill bug and
# firefly ~1.3 cm, ladybug ~7 mm); in the lens each is shown at its own magnification, the guide gives the real size
REAL_MM = {"earthworm": 150, "millipede": 100, "groundbeetle": 25, "pillbug": 13, "firefly": 13, "ladybug": 7}


def draw_bug(c, kind, x, y, L, heading=0.0, t=0.0, gait=0.0, **kw):
    DRAW[kind](c, Frame(x, y, L, heading), t, gait, **kw)
