"""What is drawn "in the book" stays in the book (owner, FK0008 review, 2026-11-01: the flying squirrel's tail stuck
out past the edge of its page - "your checks should have caught that").

Every picture an act draws on a page, in a checklist frame or on a name card is
  1. measured once, before anything renders: `check_art(items)` draws each one into a `Bounds` recorder (no pixels)
     and reports any that reach past the edge they belong in (scene stat `page_spills`, a WARNING; must be 0), and
  2. drawn clipped to that edge (`clipped`), so even a pose that changes can never show outside it.
"""
import math

import numpy as np

from .doorway import fade_clip


class Bounds:
    """A stand-in canvas that draws nothing and remembers how far the drawing reaches (strokes included)."""

    def __init__(self):
        self.box = [math.inf, math.inf, -math.inf, -math.inf]
        self.s = 1.0

    def _add(self, pts, pad=0.0):
        for x, y in pts:
            b = self.box
            b[0], b[1] = min(b[0], x - pad), min(b[1], y - pad)
            b[2], b[3] = max(b[2], x + pad), max(b[3], y + pad)

    def polygon(self, pts, col):
        self._add(np.asarray(pts, np.float64).reshape(-1, 2))

    def polyline(self, pts, col, width=2.0, closed=False):
        self._add(np.asarray(pts, np.float64).reshape(-1, 2), width / 2)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self._add([(x0, y0), (x1, y1)], width / 2)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        self._add([(x, y)], r + (0 if fill else width / 2))

    def arc(self, x, y, r, a0, a1, col, width=2.0):
        self._add([(x, y)], r + width / 2)

    def text(self, *a, **k):
        pass


def art_box(draw):
    rec = Bounds()
    draw(rec)
    return rec.box


def spill(box, rect):
    """How far (units) the drawing reaches past rect = (x0, y0, x1, y1); 0 if it fits."""
    return max(0.0, rect[0] - box[0], rect[1] - box[1], box[2] - rect[2], box[3] - rect[3])


def check_art(items, tol=0.5):
    """items: [(name, draw(canvas), rect)] -> [(name, how far over)] for every one that doesn't fit."""
    out = []
    for name, draw, rect in items:
        over = spill(art_box(draw), rect)
        if over > tol:
            out.append((name, round(over, 1)))
    return out


def fit(draw_at, rect, margin=6.0, s0=100.0, grow=False, valign="bottom"):
    """Place a picture inside rect: draw_at(canvas, x, y, s) draws it at (x, y) with size s; it is measured once at
    s0 and scaled (never up, unless grow) and moved so it sits centred inside rect with `margin`, standing on the
    bottom (valign 'bottom') or in the middle. -> (x, y, s) to draw it with."""
    bx0, by0, bx1, by1 = art_box(lambda c: draw_at(c, 0.0, 0.0, s0))
    w, h = bx1 - bx0, by1 - by0
    rw, rh = rect[2] - rect[0] - 2 * margin, rect[3] - rect[1] - 2 * margin
    k = min(rw / w, rh / h)
    if not grow:
        k = min(k, 1.0)
    x = (rect[0] + rect[2]) / 2 - k * (bx0 + bx1) / 2
    y = (rect[3] - margin - k * by1) if valign == "bottom" else ((rect[1] + rect[3]) / 2 - k * (by0 + by1) / 2)
    return x, y, s0 * k


def clipped(c, glow, rect, draw):
    """Draw draw(c) showing only inside rect (the page, the frame, the card's picture box)."""
    x0, y0, x1, y1 = rect
    fade_clip(c, glow, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lambda: draw(c), 1.0, 1.0)
