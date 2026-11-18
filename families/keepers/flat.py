"""Forest Keepers flat picture-book look (owner, 2026-11-04, after the 5-style mood board): "the style should be flat,
2D vector-style cartoon. It uses simple geometric shapes, with oversized heads and eyes. There are no outlines; edges
are defined by color alone, with soft shading in a slightly darker shade of each color. A subtle grainy, paper-like
texture runs over everything, which gives it a hand-printed or gouache-on-paper feel. The palette is warm and muted
(such as dusty pink, slate blue, ochre, olive green, orange), and the backgrounds are softly painted and simplified,
with gentle gradients and rounded hills."

Every shape here is one flat colour plus at most one soft shade a little darker (`soft_shade`), never a line round it.
The Keepers are drawn with illustrate.figure(..., style=6); the scenery with the functions below:

    pg = FlatPage(W, H)
    autumn_hills(pg)                       # sky, soft clouds, rounded hill bands, simple trees, the treehouse
    il.figure(pg, "digger", x, ground_y, k, style=6)
    rgb = pg.finish()                      # (each layer and Keeper already carries its own paper grain)
"""
import math

import numpy as np
import skia

from .storybook import C, Page, _image, mix, oval, rrect, smooth, tone, tube

PAL = dict(sky_top="#c3d0d3", sky_mid="#efe6d6", sky_low="#f0d6c6", cloud="#faf4ea",
           far="#a6b2bd", far2="#9aa69f", mid="#a3a46c", field="#cfac62", ground="#99a05a", path="#d9bf8a",
           pine="#5d7a6c", orange="#d98a45", ochre="#cfa24c", olive="#8e9a50", pink="#c98a80", slate="#6f8399",
           bark="#8a6450", wood="#c39466", wood2="#b07e56", lit="#f4c66c", door="#8c5c44", rope="#c7a46a")


def soft_shade(c, path, base, k=0.11, off=(-0.17, -0.21), soft=0.035):
    """The one shade a flat shape gets: the part away from the light (top left), a slightly darker tone of its own
    colour, with a soft edge, kept inside the shape."""
    b = path.getBounds()
    q = skia.Path(path)
    q.offset(off[0] * b.width(), off[1] * b.height())
    shade = skia.Op(path, q, skia.PathOp.kDifference_PathOp)
    if shade is None:
        return
    p = skia.Paint(AntiAlias=True, Color=C(tone(base, -k)))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, soft * max(b.width(), b.height()) + 0.8))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.drawPath(shade, p)
    c.restore()


class FlatPage(Page):
    """A storybook Page for the flat look: a fine paper grain on every layer and every Keeper, fixed to what it is
    painted on (owner, FK0013 sample, 2026-11-04: the texture "can't be moving every time the camera pans" - so it is
    never laid over the finished frame, where things would slide under it). Paint a layer between begin_grain() and
    end_grain(dx, dy), with (dx, dy) how far that layer has moved on screen; a Keeper's own layer gets grain_on()."""

    GRAIN = 0.12                                                   # strongest speck's opacity

    def __init__(self, W, H, seed=3):
        super().__init__(W, H, seed)
        import cv2
        rs = np.random.default_rng(seed + 40)
        n = 512

        def blur(a, sg):                                           # wrapped, so the tile has no seams
            m = int(4 * sg) + 2
            b = cv2.GaussianBlur(np.pad(a, m, mode="wrap"), (0, 0), sg)[m:-m, m:-m]
            return (b - b.min()) / (np.ptp(b) or 1)
        fine = blur(rs.random((n, n)), 0.6)
        blot = blur(rs.random((n, n)), 6)
        g = np.clip(0.5 + 0.55 * (fine - 0.5) + 0.35 * (blot - 0.5), 0, 1)
        # light specks where the paper is light, dark ones where it is dark, painted only onto what is already there
        a = np.clip(np.abs(2 * g - 1) * self.GRAIN, 0, 1)
        v = np.where(g > 0.5, 255.0, 0.0)
        rgba = np.dstack([v, v, v, a * 255]).astype(np.uint8)
        self._speck = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                           alphaType=skia.AlphaType.kUnpremul_AlphaType)
        self._sc = max(1.0, W / 1920)

    def grain_shader(self, dx=0.0, dy=0.0):
        m = skia.Matrix.Translate(dx, dy)
        m.preScale(self._sc, self._sc)
        return self._speck.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                      skia.SamplingOptions(skia.FilterMode.kLinear), m)

    def grain_on(self, canvas, dx=0.0, dy=0.0, bounds=None):
        """Grain onto what `canvas` already holds (only there: SrcATop), fixed to an object that is (dx, dy) along.
        bounds (skia.Rect): only there (a Keeper's own box: much faster than the whole frame)."""
        if bounds is not None:
            canvas.save()
            canvas.clipRect(bounds)
        canvas.drawPaint(skia.Paint(Shader=self.grain_shader(dx, dy), BlendMode=skia.BlendMode.kSrcATop))
        if bounds is not None:
            canvas.restore()

    def grain_opaque(self):
        """Grain over an opaque area that stays put (the sky): a ready-made frame of it, laid on top (fast)."""
        if getattr(self, "_full", None) is None:
            s = skia.Surface(self.W, self.H)
            s.getCanvas().clear(skia.ColorTRANSPARENT)
            s.getCanvas().drawPaint(skia.Paint(Shader=self.grain_shader()))
            self._full = s.makeImageSnapshot().makeRasterImage()
        self.c.drawImage(self._full, 0, 0)

    def begin_grain(self, rect=None):
        """rect (x0, y0, x1, y1): only that much of the page (a small thing: much faster)."""
        self.c.saveLayer(skia.Rect(*rect) if rect else None)

    def end_grain(self, dx=0.0, dy=0.0):
        self.grain_on(self.c, dx, dy)
        self.c.restore()

    def shape(self, path, col, shade=0.11, off=(-0.17, -0.21)):
        self.flat(path, col)
        if shade:
            soft_shade(self.c, path, col, shade, off)

    def grad(self, path, top, bottom):
        """A flat area with a gentle top-to-bottom gradient (hills, sky)."""
        b = path.getBounds()
        sh = skia.GradientShader.MakeLinear([(0, b.top()), (0, b.bottom())], [C(top), C(bottom)])
        self.c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh))

    def finish(self):
        img = self.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        return np.ascontiguousarray(img[..., :3])


# ----------------------------------------------------------------------------------------------- scenery

def cloud(pg, x, y, w):
    """A simple soft cloud: three or four round puffs on a flat bottom."""
    p = skia.Path()
    for dx, dy, r in ((-0.3, 0.05, 0.22), (-0.05, -0.08, 0.3), (0.25, 0.0, 0.24), (0.42, 0.08, 0.15)):
        p.addOval(skia.Rect(x + (dx - r) * w, y + (dy - r) * w, x + (dx + r) * w, y + (dy + r) * w))
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x - 0.45 * w, y - 0.02 * w, x + 0.55 * w, y + 0.2 * w),
                                     0.1 * w, 0.1 * w))
    p = skia.Op(p, skia.Path().addRect(skia.Rect(x - w, y - w, x + w, y + 0.2 * w)), skia.PathOp.kIntersect_PathOp)
    pg.flat(p, PAL["cloud"], 0.92, blur=0.006 * w + 0.5)
    q = skia.Op(p, skia.Path().addRect(skia.Rect(x - w, y + 0.08 * w, x + w, y + w)), skia.PathOp.kIntersect_PathOp)
    pg.flat(q, tone(PAL["cloud"], -0.05), 0.8, blur=0.02 * w)


def hill_band(pg, pts, bottom, col, light=0.05, dark=0.06):
    """A rounded hill band, a touch lighter along its top than at its foot."""
    p = smooth(pts, closed=False)
    p.lineTo(pts[-1][0], bottom)
    p.lineTo(pts[0][0], bottom)
    p.close()
    pg.grad(p, tone(col, light), tone(col, -dark))
    return p


def lolly_tree(pg, x, y, h, col, trunk=None):
    """A round-crowned tree: a short tapered trunk and one round crown with its soft shade."""
    trunk = trunk or PAL["bark"]
    pg.shape(tube([(x, y), (x + h * 0.01, y - h * 0.55)], h * 0.05, h * 0.03), trunk, 0.1, (-0.5, 0.0))
    r = h * 0.3
    pg.shape(oval(x, y - h * 0.68, r, r * 1.05), col, 0.12)


def poplar(pg, x, y, h, col, trunk=None):
    trunk = trunk or PAL["bark"]
    pg.shape(rrect(x - h * 0.025, y - h * 0.3, x + h * 0.025, y, h * 0.02), trunk, 0.0)
    pg.shape(smooth([(x, y - h), (x + h * 0.15, y - h * 0.6), (x + h * 0.12, y - h * 0.3), (x, y - h * 0.22),
                     (x - h * 0.12, y - h * 0.3), (x - h * 0.15, y - h * 0.6)]), col, 0.12)


def pine(pg, x, y, h, col, trunk=None):
    """A simple rounded-triangle pine."""
    trunk = trunk or PAL["bark"]
    pg.shape(rrect(x - h * 0.03, y - h * 0.18, x + h * 0.03, y, h * 0.02), trunk, 0.0)
    w = h * 0.26
    pg.shape(smooth([(x, y - h), (x + w * 0.45, y - h * 0.55), (x + w, y - h * 0.16), (x, y - h * 0.12),
                     (x - w, y - h * 0.16), (x - w * 0.45, y - h * 0.55)]), col, 0.12)


def bush(pg, x, y, r, col):
    p = skia.Path()
    for dx, dy, rr in ((-0.55, 0.1, 0.6), (0.0, -0.15, 0.8), (0.6, 0.1, 0.62)):
        p.addOval(skia.Rect(x + (dx - rr) * r, y + (dy - rr) * r, x + (dx + rr) * r, y + (dy + rr) * r))
    p = skia.Op(p, skia.Path().addRect(skia.Rect(x - 3 * r, y - 3 * r, x + 3 * r, y + 0.3 * r)),
                skia.PathOp.kIntersect_PathOp)
    pg.shape(p, col, 0.12)


def tuft(pg, x, y, s, col):
    p = skia.Path()
    for dx, hh, lean in ((-0.35, 0.7, -0.25), (0.0, 1.0, 0.05), (0.32, 0.75, 0.3)):
        p.moveTo(x + (dx - 0.12) * s, y)
        p.quadTo(x + (dx + lean * 0.5) * s, y - hh * 0.6 * s, x + (dx + lean) * s, y - hh * s)
        p.quadTo(x + (dx + 0.05) * s, y - hh * 0.5 * s, x + (dx + 0.12) * s, y)
        p.close()
    pg.flat(p, col)


def leaf(pg, x, y, s, ang, col):
    p = smooth([(x - s, y), (x, y - 0.45 * s), (x + s, y), (x, y + 0.45 * s)])
    p.transform(skia.Matrix.RotateDeg(ang, (x, y)))
    pg.flat(p, col)


def treehouse(pg, x, y, h):
    """The Keepers' treehouse in the flat look: an old oak with a round autumn crown, a plank cabin on a porch in its
    fork, a round lit window, a rounded door, a dusty-pink roof with a chimney, a rope ladder and a lantern.
    (x, y) is the foot of the trunk, h the height to the top of the crown."""
    s = h
    P = PAL
    bark = P["bark"]
    # two limbs up into the crown (behind it)
    for pts, w0, w1 in (([(x - 0.04 * s, y - 0.46 * s), (x - 0.16 * s, y - 0.6 * s), (x - 0.27 * s, y - 0.68 * s)],
                         0.045, 0.022),
                        ([(x + 0.04 * s, y - 0.46 * s), (x + 0.17 * s, y - 0.62 * s), (x + 0.3 * s, y - 0.7 * s)],
                         0.045, 0.022)):
        pg.shape(tube(pts, w0 * s, w1 * s), bark, 0.1, (0.0, -0.4))
    # the crown behind everything: overlapping round masses, a few autumn colours
    for dx, dy, r, col in ((-0.3, -0.7, 0.2, P["ochre"]), (0.3, -0.72, 0.21, P["orange"]),
                           (-0.1, -0.86, 0.22, P["orange"]), (0.15, -0.88, 0.2, P["ochre"]),
                           (0.0, -0.66, 0.24, tone(P["orange"], -0.04)), (-0.42, -0.56, 0.13, P["olive"]),
                           (0.44, -0.58, 0.14, tone(P["ochre"], -0.05))):
        pg.shape(oval(x + dx * s, y + dy * s, r * s, r * s * 0.95), col, 0.1)
    # the trunk, flaring into roots
    trunk = smooth([(x - 0.15 * s, y + 0.01 * s), (x - 0.08 * s, y - 0.06 * s), (x - 0.065 * s, y - 0.3 * s),
                    (x - 0.075 * s, y - 0.5 * s), (x + 0.075 * s, y - 0.5 * s), (x + 0.07 * s, y - 0.3 * s),
                    (x + 0.09 * s, y - 0.06 * s), (x + 0.17 * s, y + 0.01 * s)])
    pg.shape(trunk, bark, 0.12, (-0.45, 0.0))
    # the porch: a deck on two beams from the trunk, a railing in front of the cabin's feet
    dy = y - 0.42 * s
    for sx in (-1, 1):
        pg.shape(tube([(x + sx * 0.05 * s, y - 0.3 * s), (x + sx * 0.27 * s, dy + 0.02 * s)], 0.014 * s,
                      0.012 * s), tone(bark, -0.05), 0.0)
    cab0, cab1, ctop = x - 0.2 * s, x + 0.17 * s, dy - 0.25 * s
    pg.shape(rrect(cab0, ctop, cab1, dy, 0.012 * s), P["wood"], 0.0)
    for j in range(5):                                            # planks: every other board a shade darker
        if j % 2:
            yy = ctop + (dy - ctop) * j / 5
            pg.flat(skia.Path().addRect(skia.Rect(cab0, yy, cab1, yy + (dy - ctop) / 5)), tone(P["wood"], -0.06))
    pg.flat(skia.Path().addRect(skia.Rect(cab1 - 0.06 * s, ctop, cab1, dy)), tone(P["wood"], -0.1), 0.6)
    wx, wy, wr = x - 0.1 * s, ctop + 0.11 * s, 0.045 * s                  # round lit window, a cross in it
    pg.glow(wx, wy, wr * 3.2, P["lit"], 0.35)
    pg.flat(oval(wx, wy, wr * 1.25, wr * 1.25), tone(P["wood"], -0.18))
    pg.flat(oval(wx, wy, wr, wr), P["lit"])
    pg.flat(oval(wx + wr * 0.25, wy + wr * 0.25, wr * 0.7, wr * 0.7), tone(P["lit"], -0.08), blur=wr * 0.2)
    pg.flat(skia.Path().addRect(skia.Rect(wx - wr, wy - wr * 0.07, wx + wr, wy + wr * 0.07)), tone(P["wood"], -0.2))
    pg.flat(skia.Path().addRect(skia.Rect(wx - wr * 0.07, wy - wr, wx + wr * 0.07, wy + wr)), tone(P["wood"], -0.2))
    door = skia.Path()
    d0, d1, dt = x + 0.03 * s, x + 0.11 * s, ctop + 0.07 * s
    door.addRRect(skia.RRect.MakeRectXY(skia.Rect(d0, dt, d1, dy + 0.02 * s), 0.04 * s, 0.04 * s))
    door = skia.Op(door, skia.Path().addRect(skia.Rect(d0 - 1, dt - 1, d1 + 1, dy)), skia.PathOp.kIntersect_PathOp)
    pg.shape(door, P["door"], 0.1)
    pg.flat(oval(d1 - 0.018 * s, (dt + dy) / 2 + 0.01 * s, 0.007 * s, 0.007 * s), P["ochre"])
    # the roof: a steep rounded triangle, its right half in shade, a chimney with soft smoke
    r0, r1, apex = cab0 - 0.06 * s, cab1 + 0.06 * s, ctop - 0.2 * s
    mid = (cab0 + cab1) / 2
    ch = rrect(mid + 0.08 * s, apex + 0.04 * s, mid + 0.13 * s, ctop - 0.08 * s, 0.006 * s)
    pg.shape(ch, tone(P["pink"], -0.18), 0.0)
    for j, (px, py, pr) in enumerate(((0.108, 0.015, 0.018), (0.125, -0.035, 0.025), (0.15, -0.095, 0.032))):
        pg.flat(oval(mid + px * s, apex + py * s, pr * s, pr * s * 0.85), "#f4ede4", 0.75 - 0.18 * j)
    roof = skia.Path()                                            # a triangle with softly rounded corners
    corners = [(mid, apex), (r1, ctop + 0.03 * s), (r0, ctop + 0.03 * s)]
    rr = 0.02 * s
    for i, q in enumerate(corners):
        a, b = np.asarray(corners[i - 1], float), np.asarray(corners[(i + 1) % 3], float)
        q = np.asarray(q, float)
        u0 = q + (a - q) / np.linalg.norm(a - q) * rr
        u1 = q + (b - q) / np.linalg.norm(b - q) * rr
        (roof.moveTo if i == 0 else roof.lineTo)(*u0)
        roof.quadTo(*q, *u1)
    roof.close()
    pg.flat(roof, P["pink"])
    c = pg.c
    c.save()
    c.clipPath(roof, doAntiAlias=True)
    pg.flat(skia.Path().addRect(skia.Rect(mid, apex - 1, r1 + 5, ctop + 0.05 * s)), tone(P["pink"], -0.1))
    for j in range(1, 4):                                         # rows of shingles: a darker band under each row
        yy = apex + (ctop + 0.03 * s - apex) * j / 4
        pg.flat(skia.Path().addRect(skia.Rect(r0, yy - 0.008 * s, r1, yy)), tone(P["pink"], -0.16), 0.55)
    c.restore()
    # deck and railing in front of the cabin's feet
    pg.shape(rrect(x - 0.3 * s, dy, x + 0.3 * s, dy + 0.035 * s, 0.01 * s), P["wood2"], 0.12, (0.0, -0.5))
    for j in range(7):
        px = x - 0.28 * s + j * 0.56 * s / 6
        pg.flat(rrect(px - 0.006 * s, dy - 0.07 * s, px + 0.006 * s, dy + 0.005 * s, 0.004 * s), tone(P["wood2"], -0.1))
    pg.flat(rrect(x - 0.3 * s, dy - 0.075 * s, x + 0.3 * s, dy - 0.06 * s, 0.006 * s), P["wood2"])
    # the lantern on the corner post, and the rope ladder down to the roots
    lx, ly = x - 0.28 * s, dy - 0.1 * s
    pg.glow(lx, ly, 0.08 * s, P["lit"], 0.45)
    pg.flat(rrect(lx - 0.014 * s, ly - 0.022 * s, lx + 0.014 * s, ly + 0.02 * s, 0.008 * s), P["lit"])
    pg.flat(rrect(lx - 0.017 * s, ly - 0.03 * s, lx + 0.017 * s, ly - 0.02 * s, 0.004 * s), tone(P["slate"], -0.1))
    rx0, rx1 = x + 0.2 * s, x + 0.25 * s
    for xx in (rx0, rx1):
        pg.stroke(skia.Path().moveTo(xx, dy + 0.03 * s).lineTo(xx + 0.005 * s, y - 0.005 * s), P["rope"],
                  0.006 * s)
    for j in range(1, 8):
        yy = dy + 0.03 * s + (y - dy - 0.04 * s) * j / 8
        pg.flat(rrect(rx0 - 0.004 * s, yy - 0.005 * s, rx1 + 0.008 * s, yy + 0.005 * s, 0.004 * s),
                tone(P["rope"], -0.12))


DEPTH = dict(clouds=0.03, far=0.08, far2=0.14, far_trees=0.2, mid=0.35, field=0.55, ground=1.0)


X1 = 1.6                      # layers reach past the frame, for panning


def _sky(pg, seed, house):
    W, H, P = pg.W, pg.H, PAL
    sky = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.62)], [C(P["sky_top"]), C(P["sky_mid"]),
                                                                   C(P["sky_low"])], [0, 0.6, 1])
    pg.c.drawPaint(skia.Paint(Shader=sky))


def _clouds(pg, seed, house):
    W, H = pg.W, pg.H
    for cx, cy, w in ((0.14, 0.14, 0.17), (0.45, 0.09, 0.12), (0.64, 0.2, 0.15), (0.9, 0.11, 0.13),
                      (1.2, 0.16, 0.14)):
        cloud(pg, W * cx, H * cy, W * w)


def _far(pg, seed, house):
    W, H = pg.W, pg.H
    hill_band(pg, [(-0.1 * W, H * 0.58), (W * 0.12, H * 0.47), (W * 0.34, H * 0.55), (W * 0.55, H * 0.5),
                   (W * 0.78, H * 0.56), (W * 0.95, H * 0.48), (W * 1.2, H * 0.55), (W * X1, H * 0.5)], H,
              PAL["far"])


def _far2(pg, seed, house):
    W, H = pg.W, pg.H
    hill_band(pg, [(-0.1 * W, H * 0.6), (W * 0.22, H * 0.56), (W * 0.46, H * 0.615), (W * 0.68, H * 0.57),
                   (W * 0.9, H * 0.61), (W * 1.15, H * 0.575), (W * X1, H * 0.6)], H, PAL["far2"])


def _far_trees(pg, seed, house):
    W, H, P = pg.W, pg.H, PAL
    rs = np.random.default_rng(seed)
    for i in range(20):                                            # a far line of little trees
        x = W * (0.02 + i / 15.5) + rs.uniform(-20, 20)
        (pine if i % 3 else lolly_tree)(pg, x, H * 0.635, H * rs.uniform(0.06, 0.08),
                                        tone(P["pine"] if i % 3 else P["olive"], 0.18))


def _mid(pg, seed, house):
    W, H, P = pg.W, pg.H, PAL
    hill_band(pg, [(-0.1 * W, H * 0.66), (W * 0.2, H * 0.62), (W * 0.45, H * 0.665), (W * 0.7, H * 0.63),
                   (W * 1.1, H * 0.66), (W * 1.35, H * 0.63), (W * X1, H * 0.655)], H, P["mid"])
    for x, hh, f, col in ((0.06, 0.2, poplar, P["ochre"]), (0.12, 0.15, lolly_tree, P["orange"]),
                          (0.3, 0.17, pine, P["pine"]), (0.35, 0.13, lolly_tree, P["pink"]),
                          (0.5, 0.19, poplar, P["olive"]), (0.53, 0.14, lolly_tree, P["ochre"]),
                          (0.62, 0.16, pine, P["pine"]), (1.08, 0.15, lolly_tree, P["orange"]),
                          (1.14, 0.18, poplar, P["ochre"]), (1.25, 0.16, pine, P["pine"])):
        f(pg, W * x, H * 0.665, H * hh, col)


def _field(pg, seed, house):
    W, H, P = pg.W, pg.H, PAL
    hill_band(pg, [(-0.1 * W, H * 0.77), (W * 0.25, H * 0.73), (W * 0.55, H * 0.745), (W * 0.8, H * 0.735),
                   (W * 1.1, H * 0.76), (W * 1.35, H * 0.74), (W * X1, H * 0.755)], H, P["field"], 0.06, 0.04)
    if house:
        treehouse(pg, W * house[0], H * house[1], H * house[2])
    bush(pg, W * 0.66, H * 0.75, H * 0.035, P["olive"])
    bush(pg, W * 0.97, H * 0.76, H * 0.04, tone(P["olive"], -0.05))
    bush(pg, W * 1.2, H * 0.755, H * 0.035, P["olive"])


def _ground(pg, seed, house):
    W, H, P = pg.W, pg.H, PAL
    hill_band(pg, [(-0.1 * W, H * 0.83), (W * 0.3, H * 0.8), (W * 0.65, H * 0.815), (W * 1.1, H * 0.795),
                   (W * X1, H * 0.81)], H, P["ground"], 0.06, 0.08)
    path = smooth([(W * 0.42, H * 1.02), (W * 0.5, H * 0.9), (W * 0.62, H * 0.83), (W * 0.74, H * 0.8),
                   (W * 0.79, H * 0.805), (W * 0.7, H * 0.85), (W * 0.62, H * 0.93), (W * 0.6, H * 1.02)])
    pg.flat(path, P["path"], 0.9)
    rs = np.random.default_rng(seed)
    rs.uniform(size=40)                                            # (the far trees' draws: the same tufts as before)
    for i in range(48):                                            # grass tufts and a few fallen leaves
        x, y = rs.uniform(0, W * 1.5), H * rs.uniform(0.82, 1.0)
        tuft(pg, x, y, H * rs.uniform(0.014, 0.022), tone(P["ground"], -0.14))
    for i in range(64):
        x, y = rs.uniform(0, W * 1.5), H * rs.uniform(0.81, 1.0)
        leaf(pg, x, y, H * 0.007, rs.uniform(0, 180), (P["orange"], P["ochre"], P["pink"])[i % 3])


LAYERS = [("sky", _sky), ("clouds", _clouds), ("far", _far), ("far2", _far2), ("far_trees", _far_trees),
          ("mid", _mid), ("field", _field), ("ground", _ground)]


def draw_layer(pg, name, shift=0.0, seed=5, house=(0.8, 0.74, 0.5)):
    """One layer of the valley, moved by the camera's pan times its DEPTH, carrying its own grain."""
    fn = dict(LAYERS)[name]
    if name == "sky":                                              # the sky stays put
        fn(pg, seed, house)
        pg.grain_on(pg.c)
        return
    c = pg.c
    c.save()
    c.translate(-shift * DEPTH[name], 0)
    pg.begin_grain()
    fn(pg, seed, house)
    pg.end_grain()
    c.restore()


def autumn_hills(pg, seed=5, house=(0.8, 0.74, 0.5), shift=0.0):
    """The Keepers' valley in late autumn: a pale sky with soft clouds, slate-blue far hills, olive and ochre rounded
    hills with simple trees, the treehouse on the near hill, and the olive meadow the Keepers stand on.
    house: the treehouse (x/W, ground y/H, height/H), or None. shift: the camera's pan in px (each layer moves by its
    own DEPTH, so far hills slide slowly and the meadow under the Keepers moves with them). For an animation, Valley
    paints each layer once and slides it."""
    for name, _ in LAYERS:
        draw_layer(pg, name, shift, seed, house)


class Valley:
    """autumn_hills for a panning shot: each layer painted once (with its grain) on a strip wide enough for the whole
    pan, then slid across each frame by the pan times its depth - the same picture, many times faster.
    layers: an episode's own [(name, depth, fn(page))] instead of the valley's (fn draws across page.strip px; depth
    0 stays put); the sky can be left out and painted live (it changes with the light)."""

    def __init__(self, W, H, pan, seed=5, house=(0.8, 0.74, 0.5), page_seed=3, layers=None):
        self.layers = []
        todo = layers or [(name, 0.0 if name == "sky" else DEPTH[name],
                           lambda p, name=name: draw_layer(p, name, 0.0, seed, house)) for name, _ in LAYERS]
        for name, d, fn in todo:
            strip = W + int(math.ceil(pan * d)) + 4
            p = FlatPage(strip, H, seed=page_seed)
            p.W, p._sc, p.strip = W, max(1.0, W / 1920), strip      # lay out for the frame, not the strip
            p.c.clear(skia.ColorTRANSPARENT)
            if layers:
                p.begin_grain()
                fn(p)
                p.end_grain()
            else:
                fn(p)
            self.layers.append((name, d, p.surface.makeImageSnapshot()))

    def draw(self, pg, shift, paint=None, only=None):
        """paint: e.g. a colour filter for the light (dusk, night); only: the names of the layers to draw."""
        for name, d, img in self.layers:
            if only is None or name in only:                       # only the part of the strip in the frame
                x0 = max(0.0, shift * d)
                w = min(float(pg.W), img.width() - x0)
                src = skia.Rect(x0, 0, x0 + w, img.height())
                dst = skia.Rect(x0 - shift * d, 0, x0 - shift * d + w, img.height())
                pg.c.drawImageRect(img, src, dst, skia.SamplingOptions(skia.FilterMode.kLinear), paint,
                                   skia.Canvas.kFast_SrcRectConstraint)
