"""A Keeper drawn sharp under a camera zoom (FK remake session 3, 2026-11-07).

illustrate.figure paints each Keeper on its own full-frame layer and then lays that layer onto the page. Under a
zoomed page canvas the layer would be scaled up as a bitmap, so the Keeper would go soft. This wrapper gives the layer
the page's own matrix before the Keeper is drawn, so it is drawn as vectors at the zoomed size, and lays it on with no
matrix. At zoom 1 it is exactly illustrate.figure.

It is written only for the flat look (style 6, which has no outline and no paper drop shadow).
"""
import skia

from . import illustrate as il
from .doorway import HALF_W


def zoomed(pg):
    return not pg.c.getTotalMatrix().isIdentity()


def figure(pg, kind, x, y, k, t=1.3, eye_scale=1.15, extra=None, shadow=True, **attrs):
    if not zoomed(pg):
        return il.figure(pg, kind, x, y, k, 6, t=t, eye_scale=eye_scale, extra=extra, shadow=shadow, **attrs)
    M = pg.c.getTotalMatrix()
    st = il.STYLES[6]
    m = il.Monster(kind, k=k)
    m.x, m.y, m.newlook = x, y, True
    if kind == "teeth":
        m.hands, m.saws = True, False
    if kind == "sprout":
        m.acorn = False
    if kind == "tentacles":
        from .flat_motion import HANS_COLOURS
        m.parts_col = dict(HANS_COLOURS, wings=(214, 100, 28))
    if kind == "digger":
        m.mole_claws = True
        m.hat_orb = True
    for a, v in attrs.items():
        setattr(m, a, v)
    cv = il.StyleCanvas(pg.W, pg.H, 6, seed=il.Monster.KINDS.index(kind) + 1)
    cv.eye_scale = eye_scale
    cv.c.setMatrix(M)                                    # drawn at the zoomed size, as vectors
    m.draw(cv, t, il.Glow())
    if extra is not None:
        extra(cv, m)
    if hasattr(pg, "grain_on"):
        pg.grain_on(cv.surface.getCanvas(), x, y, getattr(cv, "bounds", None))
    fig = cv.surface.makeImageSnapshot()
    c = pg.c
    hw = HALF_W.get(kind, 200.0) * k
    if shadow:
        pg.shadow(x, y + 4, hw * 0.75, 14 + 10 * k, st["shadow"])
    c.save()
    c.resetMatrix()                                      # the layer is already in frame pixels
    c.drawImage(fig, 0, 0)
    c.restore()
    for path, col in cv.glows:                           # the light it gives (paths in the page's own units)
        b = path.getBounds()
        r = max(b.width(), b.height()) * 0.5
        pg.glow(b.centerX(), b.centerY(), r * 2.2, col, 0.38)
        p = skia.Paint(AntiAlias=True, Color=il.C(col, 0.55), BlendMode=skia.BlendMode.kScreen)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.35 + 1))
        c.drawPath(path, p)
    return m
