"""Forest Keepers illustration styles (owner, 2026-11-04, after the storybook look test: "they look too much like
baby versions of themselves... The eyes were better before, for sure... I would like to see 5 different illustrated
styles of the characters").

The Keepers keep their real anatomy: they are drawn by the same code as every episode so far
(families/foundry/products/monster.py: the old eyes, proportions, orbs, Glo's short tentacles, Digs' legs; Digs gets
mole claws, `mole_claws`). Only the way each shape is painted changes. StyleCanvas offers the drawing calls that code
uses (polygon, circle, line, polyline, arc) on a skia surface, and paints every shape in one of STYLES. Each Keeper is
drawn on its own transparent layer, so the whole figure can also get an outline, a drop shadow and a texture:

    from families.keepers import illustrate as il
    il.figure(pg, "digger", x, y_ground, k, style=3, mole_claws=True)      # pg: a storybook.Page
"""
import math

import numpy as np
import skia

from families.foundry.products.monster import Monster
from .storybook import C, _image, _noise, mix, tone

CREAM = (250, 242, 228)
STYLES = {
    1: dict(name="Gouache picture book", soften=0.55, outline=(2.6, "#6a4a3e", 0.55), shadow=0.22,
            note="soft painted shapes, light from the top left, a thin warm line round each figure"),
    2: dict(name="Ink and watercolour", soften=0.35, outline=(2.4, "#3e2c26", 0.95), shadow=0.18,
            note="see-through washes pooling at the edges, a sepia ink line"),
    3: dict(name="Cut paper", soften=0.5, outline=None, shadow=0.3,
            note="flat paper shapes with scissor-cut edges, layered with little shadows"),
    4: dict(name="Bold cartoon", soften=0.3, outline=(5.0, "#2e2639", 1.0), shadow=0.25,
            note="clean flat colour, one shade tone, a bold dark outline"),
    5: dict(name="Coloured pencil", soften=0.5, outline=None, shadow=0.2,
            note="hatched pencil strokes on toothy paper, sketchy lines"),
    # the owner's pick (2026-11-04): "1 and 2 are the closest, but the style should be flat, 2D vector-style
    # cartoon... no outlines; edges are defined by color alone, with soft shading in a slightly darker shade of each
    # color. A subtle grainy, paper-like texture runs over everything... warm and muted" (families/keepers/flat.py)
    6: dict(name="Flat picture book", soften=1.0, outline=None, shadow=0.16,
            note="flat shapes, no outlines, a soft darker shade of each colour, paper grain over everything"),
}


def _rgb(col):
    a = np.clip(np.asarray(col, np.float64)[:3], 0, 255)
    return tuple(int(round(v)) for v in a)


def soften(col, s):
    """Softer, warmer colour (the owner: "the colors... will need to be softened a bit"): a little less saturated,
    nudged toward the paper, the darkest darks lifted."""
    c = np.asarray(_rgb(col), np.float64)
    lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    c = c + (lum - c) * 0.18 * s
    c = c + (np.array(CREAM) - c) * 0.10 * s
    c = np.maximum(c, 34 + 20 * s)
    return tuple(int(v) for v in np.clip(c, 0, 255))


def mute(col, amount=0.4):
    """The flat look's warm, muted palette (dusty pink, slate blue, ochre, olive, orange): a softened colour, less
    saturated and a touch warmer. The scenery takes the full amount; the Keepers far less (KEEPER_MUTE)."""
    c = np.asarray(soften(col, min(1.0, 2.5 * amount)), np.float64)
    lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    c = c + (lum - c) * amount + np.array([7.0, 2.0, -8.0]) * amount / 0.4
    return tuple(int(v) for v in np.clip(c, 0, 255))


# owner, FK0013 sample (2026-11-04): "Hans... His colors are too muted. He just looks like brown. We can't have
# everything just being a shade of brown... He's orange." Each Keeper keeps its own colour, only a little softened.
KEEPER_MUTE = 0.12


def _lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def _hatch(n=256, period=4.5, seed=4, depth=0.3):
    """Pencil hatching: diagonal strokes of uneven pressure, 0.55..1 (multiplied over the colour)."""
    rs = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    ph = (x + y) / period + rs.random() * 6
    jitter = _noise(n, seed, octaves=3, base=4)
    line = np.clip((np.sin(2 * math.pi * (ph + 0.6 * jitter)) - 0.15) * 1.4, 0, 1)
    press = 0.5 + 0.5 * _noise(n, seed + 3, octaves=4, base=8)
    return 1.0 - depth * line * press


def _brush(n=512, seed=12):
    """Gouache brush marks: soft, slightly streaky strokes, 0.86..1 (multiplied over the colour)."""
    import cv2
    rs = np.random.default_rng(seed)
    a = rs.random((n, n))
    a = cv2.GaussianBlur(a, (0, 0), sigmaX=9, sigmaY=1.5)
    M = cv2.getRotationMatrix2D((n / 2, n / 2), 28, 1.0)
    a = cv2.warpAffine(a, M, (n, n), borderMode=cv2.BORDER_REFLECT)
    a = (a - a.min()) / (np.ptp(a) or 1)
    return 0.86 + 0.14 * a


def _tooth(n=512, seed=9, lo=0.78):
    rs = np.random.default_rng(seed)
    import cv2
    f = cv2.GaussianBlur(rs.random((n, n)), (0, 0), 0.8)
    f = (f - f.min()) / (np.ptp(f) or 1)
    fib = _noise(n, seed + 1, octaves=6, base=8)
    return lo + (1 - lo) * np.clip(0.55 * f + 0.45 * fib, 0, 1)


def _shader(gray, scale=1.0):
    return _image(np.ascontiguousarray(gray)).makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                   skia.SamplingOptions(skia.FilterMode.kLinear), skia.Matrix.Scale(scale, scale))


_SHADERS = {}


def shaders():
    if not _SHADERS:
        _SHADERS["hatch"] = _shader(_hatch())
        _SHADERS["hatch2"] = _shader(np.rot90(_hatch(seed=8)), 1.0)
        _SHADERS["tooth"] = _shader(_tooth())
        _SHADERS["paper"] = _shader(_tooth(seed=21, lo=0.86), 1.4)
        _SHADERS["wash"] = _shader(0.86 + 0.14 * _noise(512, 5, octaves=4, base=2), 2.5)
        _SHADERS["brush"] = _shader(_brush(), 1.0)
        _SHADERS["paperwhite"] = _shader(0.25 * (1 - _tooth(seed=33, lo=0.0)) ** 3, 1.0)
    return _SHADERS


def _wobble(path, amt, seed):
    """Scissor-cut edge: the outline nudged in and out a little, as if cut by hand."""
    out = skia.Path()
    it = skia.Path.Iter(path, True)
    rs = np.random.default_rng(seed)
    meas = skia.PathMeasure(path, True)
    L = meas.getLength()
    if L <= 0:
        return path
    n = max(8, int(L / 9))
    for i in range(n + 1):
        pos, tan = meas.getPosTan(L * i / n)
        d = amt * (rs.random() - 0.5) * 2
        x, y = pos.x() - tan.y() * d, pos.y() + tan.x() * d
        if i == 0:
            out.moveTo(x, y)
        else:
            out.lineTo(x, y)
    out.close()
    del it
    return out


class Glow:
    """Stands in for HeatGlow: what the Keepers draw between begin and end is light (Glo's lantern, Digs' lamp,
    the orbs), painted later as a soft screen-blended halo."""

    def begin(self, cv):
        cv.glowing = True
        return cv

    def end(self, cv):
        cv.glowing = False


class StyleCanvas:
    """The Canvas calls the Keepers draw with, painted in one illustration style on a transparent skia layer."""

    def __init__(self, W, H, style, seed=1):
        self.__dict__["surface"] = skia.Surface(W, H)
        self.c = self.surface.getCanvas()
        self.c.clear(skia.ColorTRANSPARENT)
        self.st = STYLES[style]
        self.style = style
        self.glowing = False
        self.glows = []
        self.n = seed * 1000
        self.W, self.H, self.s = W, H, 1.0
        self.flat_look = style == 6                              # monster.py's blob/grain/eye check this

    # --- the Canvas API
    def polygon(self, pts, col):
        p = np.asarray(pts, np.float64).reshape(-1, 2)
        if len(p) < 3:
            return
        path = skia.Path()
        path.moveTo(*p[0])
        for q in p[1:]:
            path.lineTo(*q)
        path.close()
        self._fill(path, col)

    def circle(self, x, y, r, col, fill=True, width=2.0):
        if r <= 0:
            return
        path = skia.Path().addOval(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r))
        if fill:
            self._fill(path, col)
        else:
            self._stroke(path, col, width)

    def ellipse(self, x, y, rx, ry, col, fill=True, width=2.0, a0=0, a1=360, angle=0):
        path = skia.Path().addOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry))
        if angle:
            path.transform(skia.Matrix.RotateDeg(angle, (x, y)))
        (self._fill if fill else lambda p, c: self._stroke(p, c, width))(path, col)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        self._stroke(skia.Path().moveTo(x0, y0).lineTo(x1, y1), col, width)

    def polyline(self, pts, col, width=2.0, closed=False):
        p = np.asarray(pts, np.float64).reshape(-1, 2)
        if len(p) < 2:
            return
        path = skia.Path()
        path.moveTo(*p[0])
        for q in p[1:]:
            path.lineTo(*q)
        if closed:
            path.close()
        self._stroke(path, col, width, closed)

    def arc(self, x, y, r, a0_deg, a1_deg, col, width=2.0):
        path = skia.Path()
        path.addArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), a0_deg, a1_deg - a0_deg)
        self._stroke(path, col, width)

    def text(self, *a, **kw):
        pass

    def on_main(self):
        self.glowing = False

    # --- painting
    def _grow(self, path, pad=0.0):
        b = path.getBounds()
        r = skia.Rect(b.left() - pad, b.top() - pad, b.right() + pad, b.bottom() + pad)
        self.bounds = r if getattr(self, "bounds", None) is None else skia.Rect(
            min(self.bounds.left(), r.left()), min(self.bounds.top(), r.top()),
            max(self.bounds.right(), r.right()), max(self.bounds.bottom(), r.bottom()))

    def _fill(self, path, col):
        self._grow(path, 2.0)
        st = self.st
        base = mute(col, getattr(self, "mute_amount", KEEPER_MUTE)) if self.flat_look else soften(col, st["soften"])
        if self.glowing:
            self.glows.append((path, _rgb(col)))
            return
        c = self.c
        b = path.getBounds()
        small = b.width() * b.height() < 24 * 24
        light = _lum(base) > 212
        self.n += 1
        S = self.style
        if S == 1:                                           # gouache: soft radial light, slightly soft edge
            R = max(b.width(), b.height()) * 0.8 + 1
            ctr = (b.centerX() - 0.2 * b.width(), b.centerY() - 0.28 * b.height())
            sh = skia.GradientShader.MakeRadial(ctr, R, [C(tone(base, 0.13)), C(base), C(tone(base, -0.14))],
                                                [0.0, 0.5, 1.0])
            c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh))
            if not small:
                c.save()
                c.clipPath(path, doAntiAlias=True)
                c.drawPaint(skia.Paint(Shader=shaders()["brush"], BlendMode=skia.BlendMode.kModulate))
                c.restore()
        elif S == 2:                                         # watercolour: a wash that pools darker at its edge
            wash = mix(base, CREAM, 0.14)
            if small or light:
                c.drawPath(path, skia.Paint(AntiAlias=True, Color=C(wash, 0.95)))
            else:
                q = skia.Path(path)                          # the wash runs a little past the ink, off-register
                q.offset(2.5, -2.0)
                bp = skia.Paint(AntiAlias=True, Color=C(wash, 0.5))
                bp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5))
                c.drawPath(q, bp)
                c.drawPath(path, skia.Paint(AntiAlias=True, Color=C(wash, 0.82)))
                c.save()
                c.clipPath(path, doAntiAlias=True)
                p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7.0,
                               Color=C(tone(wash, -0.35), 0.55))
                p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0))
                c.drawPath(path, p)
                c.drawPaint(skia.Paint(Shader=shaders()["wash"], BlendMode=skia.BlendMode.kModulate))
                c.restore()
        elif S == 3:                                         # cut paper: scissor edge, a small shadow under it
            pp = path if small or light else _wobble(path, 2.4 if b.width() * b.height() > 80 * 80 else 1.0, self.n)
            if not small:
                sp = skia.Paint(AntiAlias=True, Color=C("#3a2a26", 0.32))
                sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.6))
                q = skia.Path(pp)
                q.offset(2.5, 4.0)
                c.drawPath(q, sp)
            c.drawPath(pp, skia.Paint(AntiAlias=True, Color=C(base)))
            c.save()
            c.clipPath(pp, doAntiAlias=True)
            c.drawPaint(skia.Paint(Shader=shaders()["paper"], BlendMode=skia.BlendMode.kModulate))
            c.restore()
        elif S == 4:                                         # bold cartoon: flat colour and one shade tone
            c.drawPath(path, skia.Paint(AntiAlias=True, Color=C(base)))
            if not small and not light:
                q = skia.Path(path)
                q.offset(-0.13 * b.width(), -0.16 * b.height())
                shade = skia.Op(path, q, skia.PathOp.kDifference_PathOp)
                if shade is not None:
                    c.drawPath(shade, skia.Paint(AntiAlias=True, Color=C(tone(base, -0.16))))
        elif S == 6:                                         # flat picture book: flat colour, one soft shade
            c.drawPath(path, skia.Paint(AntiAlias=True, Color=C(base)))
            if not small and not light:
                from .flat import soft_shade
                soft_shade(c, path, base, 0.18)
        else:                                                # coloured pencil: hatched over a light layer
            c.drawPath(path, skia.Paint(AntiAlias=True, Color=C(base)))
            if not light:
                c.save()
                c.clipPath(path, doAntiAlias=True)
                c.drawPaint(skia.Paint(Shader=shaders()["hatch"], BlendMode=skia.BlendMode.kModulate))
                c.restore()
            if not small:
                for j in range(2):
                    pp = _wobble(path, 1.2, self.n * 7 + j)
                    c.drawPath(pp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.3,
                                              Color=C(tone(base, -0.38), 0.55)))

    def _stroke(self, path, col, width, closed=False):
        self._grow(path, width + 2.0)
        st = self.st
        base = mute(col, getattr(self, "mute_amount", KEEPER_MUTE)) if self.flat_look else soften(col, st["soften"])
        if self.glowing:
            return
        S = self.style
        if S == 6 and closed:                                # no outlines: edges are colour against colour
            return
        w = max(0.8, width)
        if S == 6 and w > 3:                                 # limbs: as thick as they looked with their outline
            w += 2.5
        colr = base
        if S == 2 and w < 6:                                 # thin lines are sepia ink (thick ones are limbs)
            colr = mix(base, (62, 44, 38), 0.8 if _lum(base) < 150 else 0.45)
            w = max(1.2, w * 0.8)
        if S == 4:
            w *= 1.25
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, Color=C(colr),
                       StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
        if S == 5 and w > 3:                                 # a pencil-drawn stroke: textured and a bit uneven
            self.c.drawPath(path, p)
            self.c.save()
            self.c.clipPath(self._stroked(path, w), doAntiAlias=True)
            self.c.drawPaint(skia.Paint(Shader=shaders()["hatch"], BlendMode=skia.BlendMode.kModulate))
            self.c.restore()
            return
        if S == 3 and w > 4:
            sp = skia.Paint(p)
            sp.setColor(C("#3a2a26", 0.2))
            sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.6))
            q = skia.Path(path)
            q.offset(1.2, 2.0)
            self.c.drawPath(q, sp)
        self.c.drawPath(path, p)

    def _stroked(self, path, w):
        p = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap)
        out = skia.Path()
        p.getFillPath(path, out)
        return out


def figure(pg, kind, x, y, k, style, t=1.3, eye_scale=1.15, extra=None, shadow=True, extra_behind=None, **attrs):
    """Draw one Keeper (monster.py anatomy) onto storybook Page pg in illustration style `style` (1-6). In the flat
    style (6) the eyes are drawn `eye_scale` times bigger (the owner's "oversized heads and eyes"). `extra(cv, m)`
    draws more on the Keeper's own layer after it (what Hans holds, his working tentacles), painted the same way."""
    st = STYLES[style]
    m = Monster(kind, k=k)
    m.x, m.y, m.newlook = x, y, True
    if kind == "teeth":
        m.hands, m.saws = True, False
    if kind == "sprout":
        m.acorn = False
    if kind == "tentacles" and style == 6:                                  # owner 2026-11-04: orange legs, peach
        from .flat_motion import HANS_COLOURS                               # suckers (wings: flat_motion.hans_mood)
        m.parts_col = dict(HANS_COLOURS, wings=(214, 100, 28))
    if kind == "digger":
        m.mole_claws = True
        m.hat_orb = style == 6                                              # flat look: his orb is in his hard hat
    for a, v in attrs.items():
        setattr(m, a, v)
    cv = StyleCanvas(pg.W, pg.H, style, seed=Monster.KINDS.index(kind) + 1)
    if style == 6:
        cv.eye_scale = eye_scale
    if extra_behind is not None:                                            # e.g. Hans' lifted legs at work: their
        extra_behind(cv, m)                                                 # roots go behind his head, like the legs
    m.draw(cv, t, Glow())
    if extra is not None:
        extra(cv, m)
    if style == 6 and hasattr(pg, "grain_on"):                              # paper grain fixed to the Keeper
        pg.grain_on(cv.surface.getCanvas(), x, y, getattr(cv, "bounds", None))
    fig = cv.surface.makeImageSnapshot()
    c = pg.c
    from .doorway import HALF_W
    hw = HALF_W.get(kind, 200.0) * k
    if shadow:
        pg.shadow(x, y + 4, hw * 0.75, 14 + 10 * k, st["shadow"])           # contact shadow on the ground
    if style == 3:                                                          # paper: the figure stands off the page
        c.drawImage(fig, 0, 0, paint=skia.Paint(ImageFilter=skia.ImageFilters.DropShadowOnly(
            7, 11, 6, 6, C("#3a2a26", 0.38))))
    if st["outline"]:
        w, col, a = st["outline"]
        f = skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(C(col, a), skia.BlendMode.kSrcIn),
                                          skia.ImageFilters.Dilate(w, w))
        c.drawImage(fig, 0, 0, paint=skia.Paint(ImageFilter=f))
    if style == 5:                                                          # the paper's tooth shows through
        tex = skia.Surface(pg.W, pg.H)
        tc = tex.getCanvas()
        tc.drawImage(fig, 0, 0)
        tc.drawPaint(skia.Paint(Shader=shaders()["tooth"], BlendMode=skia.BlendMode.kModulate))
        fig = tex.makeImageSnapshot()
    c.drawImage(fig, 0, 0)
    for path, col in cv.glows:                                              # the light it gives
        b = path.getBounds()
        r = max(b.width(), b.height()) * 0.5
        pg.glow(b.centerX(), b.centerY(), r * 2.2, col, 0.38)
        p = skia.Paint(AntiAlias=True, Color=C(col, 0.55), BlendMode=skia.BlendMode.kScreen)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.35 + 1))
        c.drawPath(path, p)
    return m


def creature(pg, draw, x, y, shadow=None, style=6, mute_amount=None):
    """Paint anything drawn with the Canvas calls (an animal from animals.py / winter_animals.py, a prop) onto Page pg
    in illustration style `style`, on its own layer: draw(cv) does the drawing; (x, y) anchors its paper grain (so the
    texture travels with it) and its contact shadow, `shadow` = that shadow's half-width or None."""
    cv = StyleCanvas(pg.W, pg.H, style, seed=int(abs(x)) % 97 + 1)
    if mute_amount is not None:
        cv.mute_amount = mute_amount
    draw(cv)
    if style == 6 and hasattr(pg, "grain_on"):
        pg.grain_on(cv.surface.getCanvas(), x, y, getattr(cv, "bounds", None))
    if shadow:
        pg.shadow(x, y + 2, shadow, max(6.0, shadow * 0.16), STYLES[style]["shadow"])
    pg.c.drawImage(cv.surface.makeImageSnapshot(), 0, 0)
    for path, col in cv.glows:
        b = path.getBounds()
        r = max(b.width(), b.height()) * 0.5
        pg.glow(b.centerX(), b.centerY(), r * 2.2, col, 0.38)
    return cv
