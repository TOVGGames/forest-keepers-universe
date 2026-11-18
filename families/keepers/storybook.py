"""Soft 2D storybook drawing kit for the Forest Keepers, from episode 14 on (owner 2026-11-03;
docs/engines/forest_keepers.md, "Storybook style").

Soft rounded shapes with a gentle light-to-shade gradient and a printed-paper grain, outlines a darker shade of the
fill (never black), big expressive eyes, minimal faces, a rich warm palette, and layered textured backgrounds.
Everything is drawn with skia (anti-aliased vector paths), in pixels:

    pg = Page(W, H)
    winter_clearing(pg)                       # a layered storybook background
    KEEPERS["Hans"](pg, x, ground_y, k, t=0, **pose)    # k = pixels per Keeper unit (~ a small Keeper's height)
    rgb = pg.finish()                         # paper grain + soft warm vignette -> HxWx3 uint8
"""
import math

import numpy as np
import skia

WARM_DARK = (64, 44, 40)
CREAM = (255, 247, 233)


# ----------------------------------------------------------------------------------------------- colour

def rgb(c):
    if isinstance(c, str):
        h = c.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


def mix(a, b, u):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def tone(c, k):
    """k > 0 lightens towards cream, k < 0 darkens towards a warm brown (never grey or black)."""
    return mix(c, CREAM, k) if k > 0 else mix(c, WARM_DARK, -k)


def C(c, a=1.0):
    c = rgb(c)
    return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, a).toColor()


# ----------------------------------------------------------------------------------------------- paths

def smooth(pts, closed=True):
    """A smooth path through the points (Catmull-Rom as cubic Beziers)."""
    P = [np.asarray(p, np.float64) for p in pts]
    n = len(P)
    path = skia.Path()
    path.moveTo(*P[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        path.cubicTo(*c1, *c2, *p2)
    if closed:
        path.close()
    return path


def oval(cx, cy, rx, ry, rot=0.0):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    if rot:
        p.transform(skia.Matrix.RotateDeg(rot, (cx, cy)))
    return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r))
    return p


def _dense(pts, n=10):
    P = [np.asarray(p, np.float64) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2 = P[max(i - 1, 0)], P[i], P[i + 1]
        p3 = P[min(i + 2, len(P) - 1)]
        for k in range(n):
            u = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-1])
    return out


def tube(pts, w0, w1):
    """A soft tapered limb through the points (half-width w0 at the start to w1 at the end), round ends."""
    Q = _dense(pts)
    m = len(Q)
    L, R = [], []
    for i, q in enumerate(Q):
        d = Q[min(i + 1, m - 1)] - Q[max(i - 1, 0)]
        d = d / (np.linalg.norm(d) or 1.0)
        nrm = np.array([-d[1], d[0]])
        w = w0 + (w1 - w0) * i / (m - 1)
        L.append(q + nrm * w)
        R.append(q - nrm * w)
    poly = list(L)
    d_end = Q[-1] - Q[-2]
    a_end = math.atan2(d_end[1], d_end[0])
    for j in range(1, 12):                                    # round end cap
        a = a_end + math.pi / 2 - math.pi * j / 12
        poly.append(Q[-1] + w1 * np.array([math.cos(a), math.sin(a)]))
    poly += R[::-1]
    d0 = Q[1] - Q[0]
    a0 = math.atan2(d0[1], d0[0]) + math.pi
    for j in range(1, 12):                                    # round start cap
        a = a0 + math.pi / 2 - math.pi * j / 12
        poly.append(Q[0] + w0 * np.array([math.cos(a), math.sin(a)]))
    path = skia.Path()
    path.moveTo(*poly[0])
    for p in poly[1:]:
        path.lineTo(*p)
    path.close()
    return path


# ----------------------------------------------------------------------------------------------- the page

def _noise(n, seed, octaves=5, base=4):
    rs = np.random.default_rng(seed)
    acc = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    import cv2
    for o in range(octaves):
        g = base * 2 ** o
        r = rs.random((g, g))
        r = np.pad(r, 1, mode="wrap")
        up = cv2.resize(r, (n + 2 * n // g, n + 2 * n // g), interpolation=cv2.INTER_CUBIC)
        s = n // g
        acc += amp * up[s:s + n, s:s + n]
        tot += amp
        amp *= 0.55
    acc = acc / tot
    return (acc - acc.min()) / (np.ptp(acc) or 1.0)


def _image(gray):
    g = np.clip(gray * 255, 0, 255).astype(np.uint8)
    rgba = np.dstack([g, g, g, np.full_like(g, 255)])
    return skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType)


class Page:
    """One frame: a skia surface plus the textures every shape shares."""

    def __init__(self, W, H, seed=3):
        self.W, self.H = W, H
        self.surface = skia.Surface(W, H)
        self.c = self.surface.getCanvas()
        rs = np.random.default_rng(seed)
        fine = 0.5 + (rs.random((512, 512)) - 0.5) * 0.55          # paper tooth
        import cv2
        fine = cv2.GaussianBlur(fine, (0, 0), 0.7)
        fiber = _noise(512, seed + 1, octaves=6, base=8)
        self.grain = _image(np.clip(0.5 * fine + 0.5 * fiber, 0, 1)).makeShader(
            skia.TileMode.kRepeat, skia.TileMode.kRepeat)
        self.wash = _image(_noise(512, seed + 2, octaves=4, base=2)).makeShader(
            skia.TileMode.kMirror, skia.TileMode.kMirror, skia.SamplingOptions(skia.FilterMode.kLinear),
            skia.Matrix.Scale(3.2, 3.2))

    # --- painting primitives
    def fill(self, path, base, shade=0.17, tex=0.16, line=0.34, lw=2.6, alpha=1.0, light=(-0.35, -0.55)):
        """Fill a shape: a soft radial light-to-shade gradient, printed texture, and a soft line a darker shade."""
        c = self.c
        b = path.getBounds()
        cx, cy = b.centerX(), b.centerY()
        R = max(b.width(), b.height()) * 0.78 + 1
        ctr = (cx + light[0] * b.width() * 0.5, cy + light[1] * b.height() * 0.5)
        sh = skia.GradientShader.MakeRadial(ctr, R, [C(tone(base, shade), alpha), C(base, alpha),
                                                     C(tone(base, -shade * 0.9), alpha)], [0.0, 0.5, 1.0])
        c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh))
        if tex:
            c.save()
            c.clipPath(path, doAntiAlias=True)
            c.drawPaint(skia.Paint(Shader=self.grain, BlendMode=skia.BlendMode.kOverlay, Alphaf=tex * alpha))
            c.restore()
        if line:
            c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=lw,
                                        StrokeJoin=skia.Paint.kRound_Join, Color=C(tone(base, -line), 0.9 * alpha)))

    def flat(self, path, col, alpha=1.0, blur=0.0, blend=None):
        p = skia.Paint(AntiAlias=True, Color=C(col, alpha))
        if blur:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        if blend:
            p.setBlendMode(blend)
        self.c.drawPath(path, p)

    def stroke(self, path, col, w, alpha=1.0, blur=0.0):
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, Color=C(col, alpha),
                       StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
        if blur:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        self.c.drawPath(path, p)

    def glow(self, x, y, r, col, a=0.6):
        sh = skia.GradientShader.MakeRadial((x, y), r, [C(col, a), C(col, a * 0.35), C(col, 0.0)], [0, 0.35, 1])
        self.c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=skia.BlendMode.kScreen))

    def shadow(self, x, y, rx, ry, a=0.22):
        self.flat(oval(x, y, rx, ry), tone("#5a4a5a", -0.2), a, blur=ry * 0.6)

    def textured(self, path, col, wash=0.22, tex=0.18, alpha=1.0):
        """A flat background plane with a painterly wash and paper tooth (no outline)."""
        c = self.c
        self.flat(path, col, alpha)
        c.save()
        c.clipPath(path, doAntiAlias=True)
        c.drawPaint(skia.Paint(Shader=self.wash, BlendMode=skia.BlendMode.kSoftLight, Alphaf=wash * alpha))
        c.drawPaint(skia.Paint(Shader=self.grain, BlendMode=skia.BlendMode.kOverlay, Alphaf=tex * alpha))
        c.restore()

    def finish(self):
        c = self.c
        c.drawPaint(skia.Paint(Shader=self.grain, BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
        W, H = self.W, self.H
        sh = skia.GradientShader.MakeRadial((W / 2, H * 0.45), max(W, H) * 0.75,
                                            [C("#ffffff", 0.0), C("#ffffff", 0.0), C(tone("#7a5a4a", -0.1), 0.22)],
                                            [0, 0.62, 1])
        c.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kMultiply))
        img = self.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        return np.ascontiguousarray(img[..., :3])


# ----------------------------------------------------------------------------------------------- faces

def eye(pg, x, y, r, look=(0.0, 0.0), blink=0.0, iris="#3f5f8f"):
    """A big expressive eye: cream white, a large deep iris, a dark pupil and two soft catchlights."""
    if blink > 0.85:
        p = skia.Path()
        p.moveTo(x - r * 0.8, y)
        p.quadTo(x, y + r * 0.45, x + r * 0.8, y)
        pg.stroke(p, tone(iris, -0.5), r * 0.16)
        return
    ry = r * (1 - 0.9 * blink)
    pg.fill(oval(x, y, r * 0.86, ry), "#fffaf0", shade=0.0, tex=0.04, line=0.0)
    pg.stroke(oval(x, y, r * 0.86, ry), tone("#c8b4a8", -0.2), max(1.6, r * 0.07), 0.8)
    pg.c.save()
    pg.c.clipPath(oval(x, y, r * 0.86, ry), doAntiAlias=True)
    ix, iy = x + look[0] * r * 0.28, y + r * 0.12 + look[1] * r * 0.2
    pg.fill(oval(ix, iy, r * 0.6, r * 0.64), iris, shade=0.22, tex=0.05, line=0.0)
    pg.flat(oval(ix, iy + r * 0.03, r * 0.36, r * 0.38), tone(iris, -0.72))
    pg.flat(oval(ix - r * 0.22, iy - r * 0.26, r * 0.2, r * 0.2), "#fffaf0", 0.95)
    pg.flat(oval(ix + r * 0.2, iy + r * 0.2, r * 0.09, r * 0.09), "#fffaf0", 0.85)
    pg.c.restore()


def smile(pg, x, y, w, curve, col, lw):
    p = skia.Path()
    p.moveTo(x - w, y)
    p.quadTo(x, y + curve * 2, x + w, y)
    pg.stroke(p, col, lw, 0.95)


def open_mouth(pg, x, y, w, h, col="#8a3a3e"):
    p = skia.Path()
    p.moveTo(x - w, y)
    p.quadTo(x, y + h * 0.25, x + w, y)
    p.quadTo(x + w * 0.85, y + h * 1.1, x, y + h * 1.15)
    p.quadTo(x - w * 0.85, y + h * 1.1, x - w, y)
    p.close()
    pg.flat(p, col)
    pg.c.save()
    pg.c.clipPath(p, doAntiAlias=True)
    pg.flat(oval(x, y + h * 1.05, w * 0.55, h * 0.45), "#ef8f96")
    pg.c.restore()
    pg.stroke(p, tone(col, -0.3), max(1.5, w * 0.06), 0.8)


def blush(pg, x, y, r):
    pg.flat(oval(x, y, r, r * 0.62), "#f39a95", 0.42, blur=r * 0.35)


def orb(pg, x, y, r):
    pg.glow(x, y, r * 3.2, "#9fe9f5", 0.35)
    pg.fill(oval(x, y, r, r), "#c8f4fb", shade=0.15, tex=0.0, line=0.35, lw=max(1.4, r * 0.18))


# ----------------------------------------------------------------------------------------------- the Keepers

def _ik(hip, foot, L1, L2, bend=1.0):
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    D = min(math.hypot(dx, dy), L1 + L2 - 1e-3)
    a = (L1 * L1 - L2 * L2 + D * D) / (2 * D)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    return hx + ux * a - uy * h * bend, hy + uy * a + ux * h * bend


def _step(ph, stride, lift, duty=0.55):
    """Foot offset (dx, dy up) on a walk cycle: planted and sliding back, then lifted forward (eased)."""
    ph %= 1.0
    if ph < duty:
        return stride * (0.5 - ph / duty), 0.0
    u = (ph - duty) / (1 - duty)
    e = 0.5 - 0.5 * math.cos(math.pi * u)
    return stride * (-0.5 + e), lift * math.sin(math.pi * u)


def wheels(pg, x, y, k, t=0.0, face=0.0, carry=None):
    body, grey = "#5d8fd8", "#bdb5ab"
    pg.shadow(x, y, 0.85 * k, 0.11 * k)
    for sx in (-1, 1):
        wx, wy, r = x + sx * 0.44 * k, y - 0.26 * k, 0.26 * k
        pg.fill(oval(wx, wy, r, r), "#5a4b52", shade=0.12, line=0.25)
        pg.fill(oval(wx, wy, r * 0.48, r * 0.48), "#d8d0c6", shade=0.12, line=0.2, lw=2)
        for j in range(3):
            a = t * 2.5 + j * 2 * math.pi / 3
            pg.flat(oval(wx + math.cos(a) * r * 0.3, wy + math.sin(a) * r * 0.3, r * 0.07, r * 0.07), "#9a8f86")
    pg.fill(rrect(x - 0.46 * k, y - 0.38 * k, x + 0.46 * k, y - 0.25 * k, 0.06 * k), grey, line=0.3)
    pg.fill(rrect(x - 0.08 * k, y - 0.55 * k, x + 0.08 * k, y - 0.34 * k, 0.04 * k), grey, line=0.3)
    cy = y - 1.0 * k

    def arms(sxs):
        for sx in sxs:                                           # arms with soft grabbers
            if carry is None:
                hx, hy, el = x + sx * 0.98 * k, cy - 0.3 * k, (x + sx * 0.78 * k, cy - 0.05 * k)
            else:                                                # hugging the thing in front, one grabber each side
                hx, hy, el = x + sx * 0.42 * k, cy + 0.45 * k, (x + sx * 0.72 * k, cy + 0.3 * k)
            pg.fill(tube([(x + sx * 0.45 * k, cy + 0.05 * k), el, (hx, hy)], 0.06 * k, 0.05 * k), grey, line=0.3)
            for f in (-1, 1):
                d = sx if carry is None else -sx
                pg.fill(tube([(hx, hy), (hx + d * 0.1 * k, hy + f * 0.1 * k), (hx + d * 0.17 * k, hy + f * 0.05 * k)],
                             0.035 * k, 0.025 * k), grey, line=0.3, lw=2)
    if carry is None:
        arms((-1, 1))
    pg.fill(oval(x, cy, 0.56 * k, 0.54 * k), body)
    fx = face * 0.12 * k
    for dx, dy in ((-0.25, -0.28), (0.0, -0.36), (0.25, -0.28)):
        eye(pg, x + dx * k + fx, cy + dy * k, 0.14 * k, look=(face, 0.1))
    for sx in (-1, 1):
        blush(pg, x + sx * 0.35 * k + fx, cy + 0.02 * k, 0.09 * k)
    smile(pg, x + fx, cy + 0.0 * k, 0.13 * k, 0.05 * k, tone(body, -0.6), 0.035 * k)
    orb(pg, x + fx * 0.5, cy + 0.3 * k, 0.065 * k)
    if carry is not None:
        carry(pg, x, cy + 0.48 * k, k)
        arms((-1, 1))


def hans(pg, x, y, k, t=0.0, face=0.0, walk=None, hold=None):
    """Hans: a round orange octopus with little flap fins and eight curly tentacles. walk: a phase 0..1 (he walks
    on his tentacles, feet planted); hold: (x, y, draw) a thing he holds up over his head with three tentacles at
    once (they reach up from behind him and curl over it), standing on the other five."""
    org, dots = "#e98a3f", "#f8cf9c"
    bob = 0.0 if walk is None else 0.035 * k * math.cos(4 * math.pi * walk)
    cy = y - 1.05 * k + bob
    pg.shadow(x, y, 1.0 * k, 0.12 * k)
    feet = [-0.95, -0.66, -0.36, -0.12, 0.12, 0.36, 0.66, 0.95]
    holders = (2, 4, 5) if hold else ()

    def leg(i, back):
        f = feet[i]
        sgn = 1 if f > 0 else -1
        bx = x + f * 0.42 * k
        by = cy + 0.38 * k
        if i in holders:
            return
        else:
            dx, lift = (0.0, 0.0) if walk is None else _step(walk + (0.5 if i % 2 else 0.0), 0.26 * k, 0.14 * k)
            fxp = x + f * k + dx
            fy = y - 0.05 * k - lift
            pts = [(bx, by), (bx + (fxp - bx) * 0.55, (by + fy) / 2 + 0.06 * k), (fxp, fy),
                   (fxp + sgn * 0.16 * k, fy - 0.03 * k), (fxp + sgn * 0.22 * k, fy - 0.15 * k),
                   (fxp + sgn * 0.14 * k, fy - 0.22 * k)]
        col = tone(org, -0.12) if back else org
        pg.fill(tube(pts, 0.12 * k, 0.03 * k), col, line=0.32)
        if not back:
            Q = _dense(pts[:3], 6)
            for q in Q[4:-1:3]:
                pg.flat(oval(q[0], q[1] + 0.05 * k, 0.025 * k, 0.025 * k), dots, 0.9)

    for i in (1, 6, 3, 4):
        leg(i, True)
    if hold:
        hx, hy, item = hold
        tips = []
        for j, (sx, sy) in enumerate(((-0.5, 0.05), (0.08, -0.3), (0.5, 0.05))):
            u = j - 1
            a = (x + sx * k, cy + sy * k)
            e = (hx + u * 0.5 * k, hy + 0.02 * k)
            mid = (a[0] + u * 0.42 * k, (a[1] + e[1]) / 2)
            pg.fill(tube([a, mid, e], 0.1 * k, 0.05 * k), tone(org, -0.06), line=0.32)
            tips.append(e)
        item(pg, hx, hy, k)
        for e in tips:                                           # the tips curl over the top of it
            pg.fill(tube([(e[0] - 0.05 * k, e[1] + 0.02 * k), (e[0], e[1] - 0.1 * k), (e[0] + 0.07 * k, e[1] - 0.07 * k),
                          (e[0] + 0.08 * k, e[1] + 0.0 * k)], 0.05 * k, 0.028 * k), org, line=0.32)
    for s in (-1, 1):                                            # flap fins
        pg.fill(smooth([(x + s * 0.45 * k, cy - 0.25 * k), (x + s * 0.82 * k, cy - 0.58 * k),
                        (x + s * 0.92 * k, cy - 0.36 * k), (x + s * 0.6 * k, cy - 0.05 * k)]), tone(org, -0.05))
    pg.fill(oval(x, cy, 0.64 * k, 0.58 * k), org)
    for i in (0, 7, 2, 5):
        leg(i, False)
    fx = face * 0.13 * k
    for s in (-1, 1):
        eye(pg, x + s * 0.21 * k + fx, cy - 0.06 * k, 0.17 * k, look=(face, 0.1))
        blush(pg, x + s * 0.42 * k + fx, cy + 0.16 * k, 0.1 * k)
    smile(pg, x + fx, cy + 0.2 * k, 0.14 * k, 0.05 * k, tone(org, -0.6), 0.035 * k)
    orb(pg, x + fx * 0.5, cy - 0.45 * k, 0.065 * k)


def sprout(pg, x, y, k, t=0.0, face=0.0, walk=None, water=None):
    grn, cap, root, leaf = "#6cbd4e", "#a06c42", "#4f9940", "#86d15c"
    bob = 0.0 if walk is None else 0.025 * k * abs(math.sin(2 * math.pi * walk))
    cy = y - 0.6 * k - bob
    pg.shadow(x, y, 0.5 * k, 0.08 * k)
    for s in (-1, 1):                                            # little root legs
        dx, lift = (0.0, 0.0) if walk is None else _step(walk + (0.5 if s > 0 else 0), 0.18 * k, 0.07 * k)
        fx_, fy_ = x + s * 0.15 * k + dx, y - 0.03 * k - lift
        pg.fill(tube([(x + s * 0.13 * k, cy + 0.3 * k), (fx_, fy_)], 0.055 * k, 0.05 * k), root, line=0.3)
        pg.fill(oval(fx_ + 0.03 * k, fy_, 0.09 * k, 0.045 * k), root, line=0.3, lw=2)
    sw = 0.0 if walk is None else 0.06 * k * math.sin(2 * math.pi * walk)
    for s in (-1, 1):                                            # two little hands
        if water and s > 0:
            hx, hy = x + 0.5 * k, cy - 0.02 * k
        else:
            hx, hy = x + s * 0.48 * k + s * sw, cy + 0.12 * k
        pg.fill(tube([(x + s * 0.36 * k, cy - 0.02 * k), (hx, hy)], 0.045 * k, 0.04 * k), grn, line=0.3)
        pg.fill(oval(hx, hy, 0.065 * k, 0.065 * k), grn, line=0.3, lw=2)
    pg.fill(smooth([(x, cy - 0.5 * k), (x + 0.4 * k, cy - 0.3 * k), (x + 0.42 * k, cy + 0.12 * k),
                    (x + 0.18 * k, cy + 0.42 * k), (x, cy + 0.47 * k), (x - 0.18 * k, cy + 0.42 * k),
                    (x - 0.42 * k, cy + 0.12 * k), (x - 0.4 * k, cy - 0.3 * k)]), grn)
    capp = smooth([(x - 0.5 * k, cy - 0.3 * k), (x - 0.42 * k, cy - 0.55 * k), (x, cy - 0.68 * k),
                   (x + 0.42 * k, cy - 0.55 * k), (x + 0.5 * k, cy - 0.3 * k), (x, cy - 0.24 * k)])
    pg.fill(capp, cap)
    pg.c.save()
    pg.c.clipPath(capp, doAntiAlias=True)
    for j in range(-6, 7):                                       # the cap's soft scale pattern
        p = skia.Path()
        p.moveTo(x + j * 0.12 * k - 0.3 * k, cy - 0.75 * k)
        p.lineTo(x + j * 0.12 * k + 0.3 * k, cy - 0.15 * k)
        pg.stroke(p, tone(cap, -0.3), 0.018 * k, 0.45)
        p = skia.Path()
        p.moveTo(x + j * 0.12 * k + 0.3 * k, cy - 0.75 * k)
        p.lineTo(x + j * 0.12 * k - 0.3 * k, cy - 0.15 * k)
        pg.stroke(p, tone(cap, -0.3), 0.018 * k, 0.45)
    pg.c.restore()
    pg.fill(tube([(x, cy - 0.64 * k), (x + 0.02 * k, cy - 0.82 * k), (x, cy - 0.95 * k)], 0.022 * k, 0.018 * k),
            leaf, line=0.3, lw=2)
    for s in (-1, 1):
        lx, ly = x + s * 0.12 * k, cy - 0.98 * k
        pg.fill(smooth([(x, cy - 0.95 * k), (lx, ly - 0.07 * k), (x + s * 0.24 * k, ly), (lx, ly + 0.05 * k)]), leaf,
                line=0.3, lw=2)
    fx = face * 0.1 * k
    for s in (-1, 1):
        eye(pg, x + s * 0.17 * k + fx, cy - 0.05 * k, 0.13 * k, look=(face, 0.15))
        blush(pg, x + s * 0.3 * k + fx, cy + 0.13 * k, 0.07 * k)
    smile(pg, x + fx, cy + 0.16 * k, 0.09 * k, 0.04 * k, tone(grn, -0.6), 0.03 * k)
    orb(pg, x + fx * 0.5, cy + 0.32 * k, 0.05 * k)
    if water:
        _can(pg, x + 0.5 * k, cy - 0.02 * k, k, water, t)


def _can(pg, hx, hy, k, tip, t):
    """Sprout's little watering can, held by its top handle; tip 0..1 pours a soft shower."""
    c = pg.c
    c.save()
    c.rotate(28 * tip, hx, hy)
    tin = "#a9bcc0"
    pg.fill(rrect(hx - 0.16 * k, hy + 0.06 * k, hx + 0.18 * k, hy + 0.36 * k, 0.06 * k), tin, line=0.3)
    pg.fill(tube([(hx + 0.15 * k, hy + 0.26 * k), (hx + 0.42 * k, hy + 0.08 * k)], 0.035 * k, 0.025 * k), tin,
            line=0.3, lw=2)
    pg.fill(oval(hx + 0.45 * k, hy + 0.06 * k, 0.05 * k, 0.06 * k, 30), tone(tin, -0.1), line=0.3, lw=2)
    p = skia.Path()
    p.moveTo(hx - 0.12 * k, hy + 0.07 * k)
    p.quadTo(hx, hy - 0.12 * k, hx + 0.14 * k, hy + 0.07 * k)
    pg.stroke(p, tone(tin, -0.4), 0.03 * k)
    pt = c.getTotalMatrix().mapXY(hx + 0.48 * k, hy + 0.08 * k)
    rx, ry = pt.x(), pt.y()
    c.restore()
    if tip > 0.5:
        for i in range(10):
            ph = (t * 0.8 + i * 0.37) % 1.0
            dx = rx + 0.02 * k + (i % 3) * 0.035 * k + ph * 0.06 * k
            dy = ry + ph * ph * 0.55 * k
            pg.flat(oval(dx, dy, 0.012 * k, 0.02 * k), "#9fd0e6", 0.85 * (1 - ph * 0.5))


def twigs(pg, x, y, k, t=0.0, face=0.0, walk=None):
    pur, ant = "#8f63c9", "#a87a52"
    bob = 0.0 if walk is None else 0.04 * k * math.cos(4 * math.pi * walk)
    cy = y - 1.95 * k + bob
    pg.shadow(x, y, 0.55 * k, 0.09 * k)

    def legs(back):
        for s in (-1, 1):
            if (s < 0) != back:
                continue
            dx, lift = (0.0, 0.0) if walk is None else _step(walk + (0.5 if s > 0 else 0.0), 0.36 * k, 0.14 * k)
            hip = (x + s * 0.13 * k, cy + 0.5 * k)
            foot = (x + s * 0.16 * k + dx, y - 0.05 * k - lift)
            knee = _ik(hip, foot, 0.72 * k, 0.72 * k, bend=-1 if walk is not None else 0.0) if walk is not None else \
                ((hip[0] + foot[0]) / 2 + s * 0.03 * k, (hip[1] + foot[1]) / 2)
            col = tone(pur, -0.12) if back else pur
            pg.fill(tube([hip, knee, foot], 0.07 * k, 0.06 * k), col, line=0.3)
            pg.fill(oval(foot[0] + 0.05 * k, foot[1], 0.12 * k, 0.055 * k), col, line=0.3, lw=2)

    def arm(s, back):
        sw = 0.0 if walk is None else -0.12 * k * math.sin(2 * math.pi * walk) * s
        sh = (x + s * 0.32 * k, cy + 0.05 * k)
        hd = (x + s * 0.5 * k + sw, cy + 0.72 * k)
        el = _ik(sh, hd, 0.4 * k, 0.4 * k, bend=-s)
        col = tone(pur, -0.12) if back else pur
        pg.fill(tube([sh, el, hd], 0.05 * k, 0.045 * k), col, line=0.3)
        pg.fill(oval(hd[0], hd[1], 0.075 * k, 0.075 * k), col, line=0.3, lw=2)

    legs(True)
    arm(-1, True)
    for s in (-1, 1):                                            # antlers
        b0 = (x + s * 0.12 * k, cy - 0.5 * k)
        b1 = (x + s * 0.2 * k, cy - 0.85 * k)
        b2 = (x + s * 0.36 * k, cy - 1.15 * k)
        pg.fill(tube([b0, b1, b2], 0.05 * k, 0.025 * k), ant, line=0.3, lw=2)
        pg.fill(tube([(b1[0] + s * 0.05 * k, b1[1] - 0.12 * k), (x + s * 0.48 * k, cy - 0.98 * k)], 0.03 * k, 0.02 * k),
                ant, line=0.3, lw=2)
        pg.fill(tube([(b1[0], b1[1] - 0.05 * k), (x + s * 0.1 * k, cy - 1.18 * k)], 0.028 * k, 0.018 * k), ant,
                line=0.3, lw=2)
    pg.fill(oval(x, cy, 0.4 * k, 0.6 * k), pur)
    legs(False)
    arm(1, False)
    fx = face * 0.12 * k
    eye(pg, x + fx, cy - 0.18 * k, 0.24 * k, look=(face, 0.1))
    for s in (-1, 1):
        blush(pg, x + s * 0.25 * k + fx, cy + 0.08 * k, 0.08 * k)
    smile(pg, x + fx, cy + 0.12 * k, 0.12 * k, 0.045 * k, tone(pur, -0.6), 0.035 * k)
    orb(pg, x + fx * 0.5, cy + 0.36 * k, 0.06 * k)


def springs(pg, x, y, k, t=0.0, face=0.0, bounce=0.0):
    """Springs: a round yellow fellow on two coil springs; bounce -1..1 squashes (-) or stretches (+) the springs."""
    yel, coil = "#f0bf3c", "#cfc9c0"
    lift = max(0.0, bounce) * 0.35 * k
    top = y - (0.55 + 0.12 * min(0.0, bounce)) * k - lift
    pg.shadow(x, y, 0.55 * k * (1 - 0.3 * max(0.0, bounce)), 0.08 * k)
    for s in (-1, 1):
        fx_, fy_ = x + s * 0.2 * k, y - 0.06 * k - lift
        n = 6
        for j in range(n):
            yy = top + (fy_ - top) * (j + 0.5) / n
            pg.stroke(oval(fx_, yy, 0.1 * k, 0.035 * k), tone(coil, -0.35), 0.03 * k)
            pg.stroke(oval(fx_, yy, 0.1 * k, 0.035 * k), coil, 0.018 * k)
        pg.fill(oval(fx_ + 0.02 * k, fy_, 0.14 * k, 0.06 * k), yel, line=0.3, lw=2)
    cy = top - 0.42 * k
    for s in (-1, 1):
        hx, hy = x + s * 0.72 * k, cy - 0.3 * k
        pg.fill(tube([(x + s * 0.44 * k, cy), (hx, hy)], 0.045 * k, 0.04 * k), yel, line=0.3)
        pg.fill(oval(hx, hy, 0.07 * k, 0.07 * k), yel, line=0.3, lw=2)
    pg.fill(oval(x, cy, 0.52 * k, 0.48 * k), yel)
    fx = face * 0.1 * k
    for s in (-1, 1):
        eye(pg, x + s * 0.2 * k + fx, cy - 0.22 * k, 0.17 * k, look=(face, 0.1))
        blush(pg, x + s * 0.38 * k + fx, cy + 0.04 * k, 0.08 * k)
    open_mouth(pg, x + fx, cy + 0.05 * k, 0.17 * k, 0.13 * k)
    orb(pg, x + fx * 0.5, cy + 0.33 * k, 0.055 * k)


def glo(pg, x, y, k, t=0.0, face=0.0, flare=0.0):
    """Glo: a floating teal jellyfish dome with soft tendrils, holding a little lantern; flare 0..1 = his light."""
    teal = "#46bfb2"
    bob = 0.05 * k * math.sin(t * 1.4)
    cy = y - 1.5 * k + bob
    pg.shadow(x, y, 0.45 * k, 0.06 * k, a=0.14)
    lx, ly = x, cy + 0.62 * k
    pg.glow(lx, ly, (0.9 + 0.6 * flare) * k, "#ffd88a", 0.45 + 0.3 * flare)
    if flare:
        pg.flat(oval(lx, ly, 0.75 * k, 0.75 * k), "#ffe2a0", 0.22 * flare, blur=0.25 * k)
        for i in range(8):
            a = i * math.pi / 4 + 0.3
            sparkle(pg, lx + math.cos(a) * 0.55 * k, ly + math.sin(a) * 0.55 * k, (0.05 + 0.02 * (i % 2)) * k, flare)
    for i in range(9):                                           # tendrils, gently swaying
        u = -1 + 2 * i / 8
        bx = x + u * 0.36 * k
        pts = [(bx + 0.03 * k * math.sin(t * 1.2 + i + j * 0.9) + u * 0.04 * k * j, cy + 0.12 * k + j * 0.17 * k)
               for j in range(6)]
        pg.fill(tube(pts, 0.035 * k, 0.012 * k), tone(teal, -0.05 if i % 2 else 0.0), line=0.28, lw=1.8)
    for s in (-1, 1):
        pg.fill(tube([(x + s * 0.12 * k, cy + 0.15 * k), (lx + s * 0.07 * k, ly - 0.12 * k)], 0.03 * k, 0.026 * k),
                teal, line=0.28, lw=2)
    pg.fill(rrect(lx - 0.11 * k, ly - 0.14 * k, lx + 0.11 * k, ly + 0.14 * k, 0.04 * k), "#ffd98c", shade=0.3,
            line=0.35)
    pg.fill(rrect(lx - 0.14 * k, ly - 0.18 * k, lx + 0.14 * k, ly - 0.12 * k, 0.025 * k), "#7a5a48", line=0.3, lw=2)
    pg.fill(rrect(lx - 0.13 * k, ly + 0.12 * k, lx + 0.13 * k, ly + 0.17 * k, 0.025 * k), "#7a5a48", line=0.3, lw=2)
    dome = smooth([(x - 0.56 * k, cy + 0.12 * k), (x - 0.52 * k, cy - 0.25 * k), (x - 0.28 * k, cy - 0.5 * k),
                   (x, cy - 0.56 * k), (x + 0.28 * k, cy - 0.5 * k), (x + 0.52 * k, cy - 0.25 * k),
                   (x + 0.56 * k, cy + 0.12 * k), (x + 0.3 * k, cy + 0.18 * k), (x, cy + 0.14 * k),
                   (x - 0.3 * k, cy + 0.18 * k)])
    pg.fill(dome, teal)
    for j in range(5):                                           # soft scallops on the rim
        sx = x + (-0.4 + 0.2 * j) * k
        pg.flat(oval(sx, cy + 0.12 * k, 0.07 * k, 0.04 * k), tone(teal, 0.25), 0.55)
    fx = face * 0.1 * k
    for s in (-1, 1):
        eye(pg, x + s * 0.18 * k + fx, cy - 0.12 * k, 0.13 * k, look=(face, 0.1))
        blush(pg, x + s * 0.34 * k + fx, cy + 0.03 * k, 0.07 * k)
    smile(pg, x + fx, cy + 0.04 * k, 0.09 * k, 0.04 * k, tone(teal, -0.6), 0.03 * k)
    orb(pg, x + fx * 0.5, cy - 0.5 * k, 0.055 * k)


def digs(pg, x, y, k, t=0.0, face=0.0, dig=None):
    """Digs: round and red, a yellow hard hat with a little lamp, a soft pink snout and spade paws.
    dig: a phase 0..1 digging like a dog: leaning in, front paws scooping, soil flung back behind him."""
    red, hat, steel = "#d85a4c", "#f1c34a", "#c6bdb2"
    pg.shadow(x, y, 0.65 * k, 0.09 * k)
    c = pg.c
    if dig is not None:
        _soil(pg, x, y, k, dig)
        c.save()
        c.rotate(-24, x, y)
    cy = y - 0.68 * k
    for s in (-1, 1):                                            # little feet with cream claws
        fx_ = x + s * 0.22 * k
        pg.fill(oval(fx_, y - 0.05 * k, 0.13 * k, 0.06 * k), red, line=0.3, lw=2)
        for j in (-1, 0, 1):
            pg.flat(oval(fx_ + j * 0.05 * k + 0.04 * k, y - 0.02 * k, 0.018 * k, 0.012 * k), "#f6eee2")
    def paws():
        for s in (-1, 1):                                        # spade paws
            if dig is None:
                sh, (hx, hy) = (x + s * 0.4 * k, cy + 0.1 * k), (x + s * 0.72 * k, cy + 0.2 * k)
            else:                                                # from under his tummy, scooping at the hole in turn
                sh = (x - 0.22 * k + s * 0.1 * k, cy + 0.34 * k)
                a = 2 * math.pi * (dig + (0.5 if s > 0 else 0))
                wx = x - 0.78 * k + 0.16 * k * math.cos(a) + s * 0.06 * k
                wy = y - 0.1 * k - 0.07 * k * max(0.0, math.sin(a))
                inv = skia.Matrix()
                c.getTotalMatrix().invert(inv)
                q = inv.mapXY(wx, wy)
                hx, hy = q.x(), q.y()
            pg.fill(tube([sh, (hx, hy)], 0.07 * k, 0.06 * k), red, line=0.3)
            pg.fill(smooth([(hx - 0.1 * k, hy - 0.02 * k), (hx, hy - 0.1 * k), (hx + 0.1 * k, hy - 0.02 * k),
                            (hx + 0.06 * k, hy + 0.1 * k), (hx - 0.06 * k, hy + 0.1 * k)]), steel, line=0.3, lw=2)
    paws()
    pg.fill(oval(x, cy, 0.56 * k, 0.52 * k), red)
    pg.fill(smooth([(x - 0.46 * k, cy - 0.3 * k), (x - 0.38 * k, cy - 0.62 * k), (x, cy - 0.76 * k),
                    (x + 0.38 * k, cy - 0.62 * k), (x + 0.46 * k, cy - 0.3 * k)]), hat)
    pg.fill(rrect(x - 0.56 * k, cy - 0.36 * k, x + 0.56 * k, cy - 0.26 * k, 0.05 * k), tone(hat, -0.05))
    pg.glow(x, cy - 0.56 * k, 0.3 * k, "#fff3c4", 0.5)
    pg.fill(oval(x, cy - 0.56 * k, 0.08 * k, 0.08 * k), "#fff6d2", shade=0.1, line=0.3, lw=2)
    fx = face * 0.11 * k
    for s in (-1, 1):
        eye(pg, x + s * 0.2 * k + fx, cy - 0.1 * k, 0.13 * k, look=(face, 0.1))
        blush(pg, x + s * 0.38 * k + fx, cy + 0.1 * k, 0.08 * k)
    pg.fill(oval(x + fx, cy + 0.08 * k, 0.13 * k, 0.09 * k), "#f3a3a6", shade=0.12, line=0.3, lw=2)
    for s in (-1, 1):
        pg.flat(oval(x + fx + s * 0.04 * k, cy + 0.08 * k, 0.018 * k, 0.026 * k), tone("#f3a3a6", -0.45), 0.8)
    smile(pg, x + fx, cy + 0.24 * k, 0.1 * k, 0.035 * k, tone(red, -0.6), 0.03 * k)
    orb(pg, x + fx * 0.5, cy + 0.38 * k, 0.05 * k)
    if dig is not None:
        c.restore()


def _soil(pg, x, y, k, ph):
    """The hole in front of Digs, a mound behind him, and clods flung back between his legs in soft arcs."""
    soil = "#8a6244"
    pg.fill(oval(x - 0.75 * k, y + 0.02 * k, 0.32 * k, 0.07 * k), tone(soil, -0.35), line=0.0, tex=0.2)
    pg.fill(smooth([(x + 0.45 * k, y), (x + 0.7 * k, y - 0.22 * k), (x + 1.0 * k, y - 0.26 * k),
                    (x + 1.25 * k, y - 0.08 * k), (x + 1.3 * k, y)]), soil, line=0.25)
    for i in range(7):
        u = (ph * 2 + i / 7) % 1.0
        sx = x - 0.6 * k + u * 1.75 * k
        sy = y - 0.15 * k - math.sin(math.pi * u) * 0.75 * k
        r = (0.05 + 0.02 * (i % 3)) * k
        pg.fill(oval(sx, sy, r, r * 0.8, i * 40), soil, line=0.25, lw=1.6, tex=0.2)


def stipple(pg, b, col, r, n, seed, a=0.35):
    """Small soft dots scattered over a box: the printed, hand-made texture on foliage."""
    rs = np.random.default_rng(abs(seed) + 11)
    for _ in range(n):
        rr = r * rs.uniform(0.6, 1.3)
        pg.flat(oval(rs.uniform(b.left(), b.right()), rs.uniform(b.top(), b.bottom()), rr, rr), col, a)


def sparkle(pg, x, y, r, a=1.0):
    """A soft four-point twinkle."""
    p = skia.Path()
    p.moveTo(x, y - r)
    p.quadTo(x, y, x + r, y)
    p.quadTo(x, y, x, y + r)
    p.quadTo(x, y, x - r, y)
    p.quadTo(x, y, x, y - r)
    p.close()
    pg.flat(p, "#f4c55c", 0.95 * a)
    pg.flat(oval(x, y, r * 0.25, r * 0.25), "#fff6dc", a)


def seedling(pg, x, y, k, grow=1.0):
    """A little seedling in a soft mound of soil."""
    pg.fill(smooth([(x - 0.3 * k, y), (x - 0.12 * k, y - 0.1 * k), (x + 0.12 * k, y - 0.1 * k), (x + 0.3 * k, y)]),
            "#8a6244", line=0.25, tex=0.2)
    h = 0.35 * k * grow
    pg.fill(tube([(x, y - 0.08 * k), (x + 0.02 * k, y - 0.08 * k - h * 0.6), (x, y - 0.08 * k - h)], 0.022 * k,
                 0.016 * k), "#6cbd4e", line=0.3, lw=2)
    for s in (-1, 1):
        ly = y - 0.08 * k - h
        pg.fill(smooth([(x, ly), (x + s * 0.1 * k, ly - 0.07 * k), (x + s * 0.2 * k, ly), (x + s * 0.1 * k, ly + 0.04 * k)]),
                "#86d15c", line=0.3, lw=2)


KEEPERS = {"Wheels": wheels, "Hans": hans, "Sprout": sprout, "Twigs": twigs, "Springs": springs, "Glo": glo,
           "Digs": digs}


# ----------------------------------------------------------------------------------------------- backgrounds

def _hills(W, y0, amp, seed, n=7):
    rs = np.random.default_rng(seed)
    xs = np.linspace(-0.1 * W, 1.1 * W, n)
    ys = y0 - amp * (0.5 + 0.5 * rs.random(n))
    return list(zip(xs, ys))


def _band(pg, pts, bottom, col, wash=0.22, tex=0.18, cap=None):
    p = smooth(pts, closed=False)
    p.lineTo(pts[-1][0], bottom)
    p.lineTo(pts[0][0], bottom)
    p.close()
    pg.textured(p, col, wash, tex)
    if cap:                                                      # a soft lighter rim along the top (snow, light)
        pg.stroke(smooth(pts, closed=False), cap, 10, 0.55, blur=3)


def fir(pg, x, y, h, col, snow="#fbf3e6", trunk="#7a5640", tex=0.2, line=0.25):
    """A rounded storybook fir: soft stacked tiers, a snowy cap on each, a short warm trunk."""
    w = h * 0.42
    pg.fill(rrect(x - h * 0.04, y - h * 0.16, x + h * 0.04, y, h * 0.02), trunk, line=line, lw=2)
    for j in range(3):
        top = y - h * (1.0 - 0.27 * j)
        bot = y - h * (0.55 - 0.18 * j) + h * 0.04
        ww = w * (0.55 + 0.25 * j)
        tier = smooth([(x, top), (x + ww * 0.55, (top + bot) / 2), (x + ww, bot), (x, bot + h * 0.05),
                       (x - ww, bot), (x - ww * 0.55, (top + bot) / 2)])
        pg.fill(tier, tone(col, 0.04 * j), shade=0.12, tex=tex, line=line, lw=2.2)
        pg.c.save()
        pg.c.clipPath(tier, doAntiAlias=True)
        stipple(pg, tier.getBounds(), tone(col, -0.25), h * 0.012, int(18 + h * 0.15), int(x + j * 7))
        pg.flat(oval(x - ww * 0.15, top + (bot - top) * 0.3, ww * 0.6, (bot - top) * 0.35, -15), snow, 0.85)
        pg.c.restore()


def round_tree(pg, x, y, h, col, trunk="#7a5640", snow=None, line=0.25):
    pg.fill(tube([(x, y), (x + h * 0.02, y - h * 0.5)], h * 0.055, h * 0.04), trunk, line=line, lw=2)
    for dx, dy, r in ((0, -0.72, 0.3), (-0.2, -0.58, 0.22), (0.21, -0.6, 0.23)):
        pg.fill(oval(x + dx * h, y + dy * h, r * h, r * h * 0.92), col, shade=0.14, line=line, lw=2.2)
        pg.c.save()
        pg.c.clipPath(oval(x + dx * h, y + dy * h, r * h, r * h * 0.92), doAntiAlias=True)
        stipple(pg, oval(x + dx * h, y + dy * h, r * h, r * h).getBounds(), tone(col, -0.25), h * 0.012, 60, int(x + dx * 99))
        pg.c.restore()
        if snow:
            pg.c.save()
            pg.c.clipPath(oval(x + dx * h, y + dy * h, r * h, r * h * 0.92), doAntiAlias=True)
            pg.flat(oval(x + dx * h - r * h * 0.2, y + dy * h - r * h * 0.75, r * h * 0.8, r * h * 0.4), snow, 0.85)
            pg.c.restore()


def _branch(pg, pts, w0, w1, bark, snow):
    """A bare oak limb (tapered), dusted with snow along its top."""
    pg.fill(tube(pts, w0, w1), bark, shade=0.1, tex=0.22, line=0.3, lw=2)
    top = [(px, py - w * 0.42) for (px, py), w in zip(pts, np.linspace(w0, w1, len(pts)))]
    pg.stroke(smooth(top, closed=False), snow, max(2.0, w1 * 0.55), 0.9)


def _limb(pg, x, y, ang, L, w, depth, rs, bark, snow):
    """A gnarled oak limb: a slightly crooked tapered piece that forks into smaller ones, the ends thin twigs; snow
    along the top of the thicker parts."""
    pts, a = [(x, y)], ang
    for i in range(3):
        a += rs.uniform(-0.22, 0.22)
        x, y = x + math.cos(a) * L / 3, y + math.sin(a) * L / 3
        pts.append((x, y))
    w1 = w * 0.55
    if w > 4:
        _branch(pg, pts, w, w1, bark, snow)
    else:
        pg.stroke(smooth(pts, closed=False), bark, max(1.5, w), 0.95)
    if depth > 0:
        for da in (-rs.uniform(0.35, 0.6), rs.uniform(0.3, 0.55)):
            _limb(pg, x, y, a + da - 0.12, L * rs.uniform(0.55, 0.72), w1, depth - 1, rs, bark, snow)


def treehouse(pg, x, y, h):
    """The Keepers' treehouse (owner 2026-11-04: "I definitely don't like the look of their treehouse"): a plank
    cabin with a steep shingled roof in the fork of a big old oak, bare and snowy for winter; a porch with a railing,
    a round window and a square one lit warm, a little chimney, a rope ladder and a lantern."""
    bark, bark_d, snow = "#7f5c46", "#6a4a38", "#fbf3e6"
    plank, roof, trim, win = "#c79260", "#9c5a46", "#8a5a3c", "#ffd58a"
    c = pg.c
    # the oak: a wide trunk with roots, splitting into a fork that holds the cabin
    pg.fill(smooth([(x - 0.3 * h, y + 0.01 * h), (x - 0.15 * h, y - 0.04 * h), (x - 0.1 * h, y - 0.3 * h),
                    (x - 0.13 * h, y - 0.52 * h), (x - 0.26 * h, y - 0.68 * h), (x - 0.18 * h, y - 0.7 * h),
                    (x - 0.02 * h, y - 0.58 * h), (x + 0.1 * h, y - 0.62 * h), (x + 0.24 * h, y - 0.72 * h),
                    (x + 0.3 * h, y - 0.68 * h), (x + 0.13 * h, y - 0.5 * h), (x + 0.1 * h, y - 0.28 * h),
                    (x + 0.16 * h, y - 0.04 * h), (x + 0.32 * h, y + 0.01 * h)]), bark, shade=0.1, tex=0.24)
    for dx in (-0.06, 0.0, 0.05):                                # bark furrows
        pg.stroke(smooth([(x + dx * h, y - 0.02 * h), (x + (dx + 0.01) * h, y - 0.2 * h),
                          (x + (dx - 0.01) * h, y - 0.42 * h)], closed=False), bark_d, 0.008 * h, 0.55)
    rs = np.random.default_rng(int(x) + 3)
    for bx, by_, ang, L, w in ((x - 0.2 * h, y - 0.66 * h, -168, 0.5, 0.05), (x - 0.16 * h, y - 0.7 * h, -128, 0.42, 0.04),
                               (x + 0.22 * h, y - 0.68 * h, -14, 0.52, 0.05), (x + 0.18 * h, y - 0.72 * h, -58, 0.44, 0.04)):
        _limb(pg, bx, by_, math.radians(ang), L * h, w * h, 3, rs, bark, snow)
    # the porch: a deck on two beams, its railing
    dy = y - 0.68 * h
    pg.fill(rrect(x - 0.36 * h, dy - 0.012 * h, x + 0.36 * h, dy + 0.03 * h, 0.006 * h), tone(plank, -0.2),
            tex=0.22)
    pg.stroke(skia.Path().moveTo(x - 0.36 * h, dy - 0.016 * h).lineTo(x + 0.36 * h, dy - 0.016 * h), snow,
              0.014 * h, 0.95)
    for bx in (-0.28, 0.28):
        pg.stroke(skia.Path().moveTo(x + bx * h, dy + 0.03 * h).lineTo(x + bx * 0.45 * h, dy + 0.16 * h),
                  tone(plank, -0.3), 0.016 * h)
    # the cabin: horizontal planks, a steep roof with an overhang
    x0, x1, top = x - 0.22 * h, x + 0.22 * h, dy - 0.27 * h
    body = rrect(x0, top, x1, dy - 0.012 * h, 0.01 * h)
    pg.fill(body, plank, shade=0.08, tex=0.24, line=0.32)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    for j in range(1, 7):
        yy = top + j * (dy - top) / 7
        pg.stroke(skia.Path().moveTo(x0, yy).lineTo(x1, yy), tone(plank, -0.22), 0.004 * h, 0.7)
    c.restore()
    for wx, wy, rnd in ((x - 0.1 * h, top + 0.11 * h, True), (x + 0.11 * h, top + 0.12 * h, False)):
        pg.glow(wx, wy, 0.11 * h, win, 0.45)
        r = 0.045 * h
        wp = oval(wx, wy, r, r) if rnd else rrect(wx - r, wy - r, wx + r, wy + r, 0.006 * h)
        pg.fill(wp, win, shade=0.18, tex=0.1, line=0.0)
        pg.stroke(wp, trim, 0.012 * h)
        pg.stroke(skia.Path().moveTo(wx - r, wy).lineTo(wx + r, wy), trim, 0.007 * h)
        pg.stroke(skia.Path().moveTo(wx, wy - r).lineTo(wx, wy + r), trim, 0.007 * h)
    door = rrect(x - 0.035 * h, dy - 0.12 * h, x + 0.035 * h, dy - 0.012 * h, 0.03 * h)
    pg.fill(door, tone(plank, -0.32), shade=0.08, line=0.3)
    pg.fill(oval(x + 0.02 * h, dy - 0.065 * h, 0.006 * h, 0.006 * h), "#e0b860", line=0.0, tex=0)
    pg.fill(rrect(x + 0.1 * h, top - 0.15 * h, x + 0.15 * h, top - 0.02 * h, 0.005 * h), "#a8806a", tex=0.2)
    for j in range(4):                                           # chimney smoke
        pg.flat(oval(x + 0.13 * h + j * 0.03 * h, top - 0.2 * h - j * 0.07 * h, (0.025 + 0.012 * j) * h,
                     (0.02 + 0.01 * j) * h), "#f4eee8", 0.55 - 0.1 * j, blur=6)
    rp = [(x0 - 0.06 * h, top + 0.015 * h), (x, top - 0.2 * h), (x1 + 0.06 * h, top + 0.015 * h)]
    pg.fill(skia.Path().moveTo(*rp[0]).lineTo(*rp[1]).lineTo(*rp[2]).close(), roof, shade=0.1, tex=0.24,
            line=0.32)
    c.save()
    c.clipPath(skia.Path().moveTo(*rp[0]).lineTo(*rp[1]).lineTo(*rp[2]).close(), doAntiAlias=True)
    for j in range(1, 6):                                        # shingle rows
        yy = top - 0.2 * h + j * 0.04 * h
        for i in range(-9, 10):
            xx = x + (i + 0.5 * (j % 2)) * 0.045 * h
            pg.stroke(smooth([(xx - 0.022 * h, yy), (xx, yy + 0.012 * h), (xx + 0.022 * h, yy)], closed=False),
                      tone(roof, -0.25), 0.004 * h, 0.75)
    pg.flat(skia.Path().moveTo(x0 - 0.04 * h, top - 0.0 * h).lineTo(x, top - 0.19 * h)
            .lineTo(x1 + 0.04 * h, top).lineTo(x + 0.1 * h, top - 0.08 * h).lineTo(x - 0.06 * h, top - 0.11 * h)
            .close(), snow, 0.92)
    c.restore()
    for px_ in [x - 0.34 * h + i * 0.057 * h for i in range(13)]:   # the railing
        if abs(px_ - x) < 0.24 * h:
            continue
        pg.stroke(skia.Path().moveTo(px_, dy - 0.012 * h).lineTo(px_, dy - 0.08 * h), tone(plank, -0.25),
                  0.007 * h)
    for side in (-1, 1):
        pg.stroke(skia.Path().moveTo(x + side * 0.24 * h, dy - 0.08 * h).lineTo(x + side * 0.36 * h, dy - 0.08 * h),
                  tone(plank, -0.18), 0.012 * h)
        pg.stroke(skia.Path().moveTo(x + side * 0.24 * h, dy - 0.087 * h)
                  .lineTo(x + side * 0.36 * h, dy - 0.087 * h), snow, 0.008 * h, 0.9)
    # a lantern on the porch post, a rope ladder down to the snow
    lx, ly = x - 0.3 * h, dy - 0.12 * h
    pg.stroke(skia.Path().moveTo(lx, dy - 0.012 * h).lineTo(lx, ly), tone(plank, -0.3), 0.01 * h)
    pg.glow(lx, ly + 0.025 * h, 0.08 * h, win, 0.5)
    pg.fill(rrect(lx - 0.016 * h, ly, lx + 0.016 * h, ly + 0.045 * h, 0.006 * h), win, line=0.4, lw=1.5, tex=0)
    for rx in (x + 0.24 * h, x + 0.3 * h):
        pg.stroke(smooth([(rx, dy + 0.02 * h), (rx + 0.004 * h, y - 0.34 * h), (rx, y - 0.02 * h)], closed=False),
                  "#b89a72", 0.006 * h)
    for j in range(8):
        yy = dy + 0.06 * h + j * (y - dy - 0.08 * h) / 8
        pg.stroke(skia.Path().moveTo(x + 0.24 * h, yy).lineTo(x + 0.3 * h, yy + 0.004 * h), tone(plank, -0.15),
                  0.01 * h)
    pg.flat(oval(x, y + 0.01 * h, 0.36 * h, 0.03 * h), snow, 0.95)          # snow drifted round the roots


def winter_clearing(pg, shift=0.0, seed=7):
    """A layered storybook winter clearing by day: warm sky, far hills, far forest, mid firs and the treehouse,
    the snowy ground, berry bushes in front. shift: camera pan in px (each layer moves by its own depth)."""
    W, H = pg.W, pg.H
    c = pg.c
    sky = skia.GradientShader.MakeLinear([(0, 0), (0, H * 0.7)], [C("#b4cfdb"), C("#e5e2d6"), C("#f6d8b4")],
                                         [0, 0.55, 1])
    c.drawPaint(skia.Paint(Shader=sky))
    c.drawPaint(skia.Paint(Shader=pg.wash, BlendMode=skia.BlendMode.kSoftLight, Alphaf=0.25))
    pg.glow(W * 0.74 - shift * 0.05, H * 0.3, H * 0.45, "#fff0c8", 0.55)
    pg.flat(oval(W * 0.74 - shift * 0.05, H * 0.3, H * 0.06, H * 0.06), "#fff6dc", 0.95)
    rs = np.random.default_rng(seed)
    for _ in range(5):                                           # soft clouds
        cx, cyy = rs.uniform(0, W) - shift * 0.05, rs.uniform(H * 0.08, H * 0.3)
        for j in range(4):
            pg.flat(oval(cx + j * 60 - 90, cyy + (j % 2) * 10, 90, 34), "#fffaf0", 0.5, blur=14)

    def layer(depth):
        c.save()
        c.translate(-shift * depth, 0)
    layer(0.12)
    _band(pg, _hills(W * 1.3, H * 0.6, H * 0.12, seed), H, "#c8bcc8", cap="#f6ece2")
    c.restore()
    layer(0.22)
    _band(pg, _hills(W * 1.3, H * 0.66, H * 0.08, seed + 1, 9), H, "#b2a6bb", cap="#f6ece2")
    for i in range(34):                                          # far forest line
        x = i * W * 1.3 / 34 + rs.uniform(-10, 10)
        fir(pg, x, H * 0.69 + rs.uniform(-6, 6), H * rs.uniform(0.09, 0.13), "#86a092", snow="#f3eee6",
            trunk="#8a7a78", tex=0.12, line=0.12)
    c.restore()
    layer(0.45)
    _band(pg, [(-200, H * 0.72), (W * 0.3, H * 0.705), (W * 0.7, H * 0.715), (W * 1.5, H * 0.7)], H, "#efe4da")
    for x, hh in ((W * 0.05, 0.34), (W * 0.16, 0.27), (W * 0.36, 0.3), (W * 0.5, 0.24), (W * 0.9, 0.33),
                  (W * 1.02, 0.28), (W * 1.15, 0.31)):
        fir(pg, x, H * 0.73, H * hh, "#4f806c")
    round_tree(pg, W * 0.27, H * 0.73, H * 0.3, "#6b8f60", snow="#fbf3e6")
    treehouse(pg, W * 0.67, H * 0.74, H * 0.42)
    c.restore()
    layer(0.7)                                                   # the snowy ground with soft blue shadows
    g = [(-300, H * 0.75), (W * 0.25, H * 0.74), (W * 0.6, H * 0.76), (W * 1.6, H * 0.745)]
    _band(pg, g, H, "#f6ece0", wash=0.3, tex=0.2)
    for j in range(4):
        y0 = H * (0.8 + 0.05 * j)
        pts = [(-300, y0), (W * 0.3, y0 - 8), (W * 0.65, y0 + 6), (W * 1.6, y0 - 4)]
        pg.stroke(smooth(pts, closed=False), "#d3cbe0", 18, 0.35, blur=8)
    path = smooth([(W * 0.0, H * 0.99), (W * 0.3, H * 0.86), (W * 0.55, H * 0.8), (W * 0.72, H * 0.76),
                   (W * 0.76, H * 0.765), (W * 0.62, H * 0.83), (W * 0.4, H * 0.92), (W * 0.15, H * 1.05)])
    pg.textured(path, "#ead8c2", 0.25, 0.22)                     # a trodden path to the treehouse
    c.restore()


def foreground(pg, shift=0.0):
    """Berry bushes, snowy stones and grass tufts along the bottom edge (in front of the Keepers)."""
    W, H = pg.W, pg.H
    c = pg.c
    c.save()
    c.translate(-shift * 1.15, 0)
    for x, r in ((W * 0.03, 0.12), (W * 0.12, 0.08), (W * 0.93, 0.13), (W * 1.04, 0.1)):
        for dx, dy, rr in ((0, 0, 1.0), (-0.7, 0.25, 0.75), (0.7, 0.2, 0.8)):
            p = oval(x + dx * r * H, H + dy * r * H - r * H * 0.25, rr * r * H, rr * r * H * 0.8)
            pg.fill(p, "#3f6a52", shade=0.13, line=0.25)
        rs = np.random.default_rng(int(x))
        for _ in range(9):
            bx, by = x + rs.uniform(-1.2, 1.2) * r * H, H - r * H * rs.uniform(0.1, 0.8)
            pg.fill(oval(bx, by, r * H * 0.07, r * H * 0.07), "#d4473f", shade=0.25, line=0.3, lw=1.5)
        pg.flat(oval(x - r * H * 0.2, H - r * H * 0.95, r * H * 0.7, r * H * 0.2), "#fbf3e6", 0.9)
    for x in (W * 0.22, W * 0.8):
        pg.fill(oval(x, H * 0.985, H * 0.05, H * 0.03), "#a89c94", line=0.3)
        pg.flat(oval(x - H * 0.01, H * 0.965, H * 0.04, H * 0.013), "#fbf3e6", 0.9)
    c.restore()
