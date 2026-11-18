"""Foundry look: night-factory colors, flat machine shapes, molten-metal colors, heat glow.

Machines are flat shapes with one darker shade for depth and a thin highlight edge.
Only hot or moving things glow: they are drawn a second time into a `HeatGlow` layer,
which is the only thing that gets bloom (Bright Lights blooms the whole frame).
"""
import cv2
import numpy as np

from engine.core import palette

STATIONS = ["furnace", "cooling", "stamping", "conveyor", "paint", "assembly"]
ACCENT = dict(zip(STATIONS, palette("foundry")))

BG = np.array([13, 16, 25], np.float64)          # night-factory navy/charcoal
FAR = np.array([18, 22, 33], np.float64)         # parallax silhouettes, low contrast
MID = np.array([23, 28, 41], np.float64)
STEEL = np.array([44, 50, 62], np.float64)       # machine bodies (matte)
IRON = np.array([36, 39, 47], np.float64)        # cast molds, heavy parts
FLOOR = np.array([20, 23, 32], np.float64)
CABLE = np.array([70, 74, 84], np.float64)

# molten metal cooling curve: steel -> dull red -> amber -> white-yellow
_MOLTEN = [(0.00, (74, 82, 94)), (0.18, (84, 56, 50)), (0.38, (160, 48, 22)),
           (0.60, (255, 138, 31)), (0.82, (255, 198, 96)), (1.00, (255, 246, 214))]


def molten(T):
    T = float(np.clip(T, 0, 1))
    for (t0, c0), (t1, c1) in zip(_MOLTEN, _MOLTEN[1:]):
        if T <= t1:
            u = (T - t0) / (t1 - t0)
            return np.array(c0) * (1 - u) + np.array(c1) * u
    return np.array(_MOLTEN[-1][1], np.float64)


def heat(T):
    """0..1 glow amount for metal at temperature T (nothing below dull red)."""
    return float(np.clip((T - 0.3) / 0.7, 0, 1)) ** 1.4


def lighten(c, k):
    return np.minimum(255, np.asarray(c) * k)


def block(cv, x0, y0, x1, y1, col, depth=0.18, edge=1.5):
    """Flat machine block: face, darker band along the bottom, thin highlight on top/left."""
    cv.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col)
    yb = y1 - (y1 - y0) * depth
    cv.polygon([(x0, yb), (x1, yb), (x1, y1), (x0, y1)], np.asarray(col) * 0.72)
    cv.line(x0, y0, x1, y0, lighten(col, edge), 2)
    cv.line(x0, y0, x0, y1, lighten(col, edge * 0.85), 1.5)


def shape(cv, pts, col, edge=1.5, outline=0.7):
    """Flat polygon with a dark outline and a highlight on its first edge."""
    cv.polygon(pts, col)
    cv.polyline(pts, np.asarray(col) * outline, 2, closed=True)
    cv.line(*pts[0], *pts[1], lighten(col, edge), 2)


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def smootherstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


def settle(u, overshoot=0.06):
    """Ease-out that overshoots slightly and settles back - for heavy mechanical stops."""
    u = min(1.0, max(0.0, u))
    return smootherstep(u) + overshoot * np.sin(np.pi * u) * u ** 2


class Shifted:
    """Canvas wrapper for the camera: moves everything up by `dy` scene units (vertical camera)
    and scales by `zoom` (< 1 = wider lens, more of the factory in frame), so stations draw in
    world y and camera-relative x. `w`/`h` report the visible size in scene units, so stations'
    off-screen culling keeps working. Everything else is forwarded to the real canvas."""

    def __init__(self, cv):
        self.__dict__["_cv"] = cv
        self.__dict__["dy"] = 0.0
        self.__dict__["zoom"] = 1.0
        self.__dict__["rot"] = None              # (angle, px, py): rotate drawing about a pivot

    def __getattr__(self, k):
        return getattr(self._cv, k)

    def __setattr__(self, k, v):
        if k in ("dy", "zoom", "rot"):
            self.__dict__[k] = v
        else:
            setattr(self._cv, k, v)

    @property
    def w(self):
        return self._cv.w / self.zoom

    @property
    def h(self):
        return self._cv.h / self.zoom

    def _r(self, p):
        if self.rot is None:
            return p
        a, px, py = self.rot
        c, s = np.cos(a), np.sin(a)
        x, y = p[:, 0] - px, p[:, 1] - py
        return np.stack([px + x * c - y * s, py + x * s + y * c], 1)

    def _pts(self, pts):
        p = self._r(np.array(pts, np.float64).reshape(-1, 2))
        p[:, 1] -= self.dy
        return p * self.zoom

    def _xy(self, x, y):
        if self.rot is None:
            return x, y
        q = self._r(np.array([[x, y]], np.float64))
        return q[0, 0], q[0, 1]

    def polygon(self, pts, col):
        self._cv.polygon(self._pts(pts), col)

    def polyline(self, pts, col, width=2.0, closed=False):
        self._cv.polyline(self._pts(pts), col, width * self.zoom, closed)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        z = self.zoom
        x0, y0 = self._xy(x0, y0)
        x1, y1 = self._xy(x1, y1)
        self._cv.line(x0 * z, (y0 - self.dy) * z, x1 * z, (y1 - self.dy) * z, col, width * z)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        z = self.zoom
        x, y = self._xy(x, y)
        self._cv.circle(x * z, (y - self.dy) * z, r * z, col, fill, width * z)

    def arc(self, x, y, r, a0, a1, col, width=2.0):
        z = self.zoom
        da = np.degrees(self.rot[0]) if self.rot is not None else 0.0
        x, y = self._xy(x, y)
        self._cv.arc(x * z, (y - self.dy) * z, r * z, a0 + da, a1 + da, col, width * z)

    def text(self, text, x, y, size, col, anchor="mm", weight="Bold"):
        z = self.zoom
        x, y = self._xy(x, y)
        self._cv.text(text, x * z, (y - self.dy) * z, size * z, col, anchor, weight)

    def shade_rect(self, x0, y0, x1, y1, k=0.3):
        z = self.zoom
        self._cv.shade_rect(x0 * z, (y0 - self.dy) * z, x1 * z, (y1 - self.dy) * z, k)


def chaikin(pts, n=3):
    """Round off a control polyline (corner cutting)."""
    p = np.asarray(pts, np.float64)
    for _ in range(n):
        q = p[:-1] * 0.75 + p[1:] * 0.25
        r = p[:-1] * 0.25 + p[1:] * 0.75
        p = np.concatenate([p[:1], np.stack([q, r], 1).reshape(-1, 2), p[-1:]])
    return p


class Haze:
    """Soft translucent puffs (steam): an alpha mask drawn at quarter resolution, blurred,
    and blended over the frame in one color."""

    def __init__(self, cv, color=(150, 160, 175)):
        self.q = 4
        self.mask = np.zeros((cv.H // self.q, cv.W // self.q), np.float32)
        self.color = np.array(color, np.float32)

    def puff(self, cv, x, y, r, a):
        z = getattr(cv, "zoom", 1.0)
        s = cv.s / self.q * z
        y -= getattr(cv, "dy", 0.0)
        cv2.circle(self.mask, (int(x * s), int(y * s)), max(1, int(r * s)), float(a), -1, cv2.LINE_AA)

    def apply(self, cv):
        if not self.mask.any():
            return
        m = cv2.GaussianBlur(self.mask, (0, 0), 3)
        m = cv2.resize(np.clip(m, 0, 0.8), (cv.W, cv.H), interpolation=cv2.INTER_LINEAR)[..., None]
        img = cv.img.astype(np.float32)
        cv.img[:] = (img + (self.color - img) * m).astype(np.uint8)
        self.mask[:] = 0


class HeatGlow:
    """Second draw target for hot things; bloomed and added onto the frame in `apply`."""

    def __init__(self, cv, strength=1.0, radius=1.0):
        self.layer = np.zeros_like(cv.img)
        self.strength, self.radius = strength, radius

    def clear(self):
        self.layer[:] = 0

    def begin(self, cv):
        cv.target = self.layer
        return cv

    def end(self, cv):
        cv.on_main()

    def apply(self, cv):
        W, H, q = cv.W, cv.H, 4
        small = cv2.resize(self.layer, (W // q, H // q), interpolation=cv2.INTER_AREA).astype(np.float32)
        r = self.radius * cv.s
        b1 = cv2.GaussianBlur(small, (0, 0), 2.5 * r)
        tiny = cv2.resize(small, (W // (q * 4), H // (q * 4)), interpolation=cv2.INTER_AREA)
        b2 = cv2.GaussianBlur(tiny, (0, 0), 3.0 * r)
        b2 = cv2.resize(b2, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_LINEAR)
        bloom = (b1 * 0.9 + b2 * 1.1) * self.strength
        bloom = cv2.resize(np.clip(bloom, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
        cv2.add(cv.img, bloom, dst=cv.img)
