"""Frame canvas: anti-aliased neon drawing in scene units + glow/bloom post.

All coordinates are scene units (short side = 1080). Colors are RGB 0-255.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .core import hot

SHIFT = 4                 # cv2 sub-pixel bits
SUB = 1 << SHIFT
AA = cv2.LINE_AA
FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")
# system fonts with symbol glyphs (zodiac signs U+2648-2653), first one found is used
SYMBOL_FONTS = ["C:/Windows/Fonts/seguisym.ttf",                          # Windows: Segoe UI Symbol
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Linux (fonts-dejavu)
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Apple Symbols.ttf"]
EMOJI_FONTS = ["C:/Windows/Fonts/seguiemj.ttf",                           # Windows: Segoe UI Emoji (colour)
               "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
               "/System/Library/Fonts/Apple Color Emoji.ttc"]


def _c(col):
    c = np.clip(np.asarray(col, dtype=np.float64), 0, 255)
    return (float(c[0]), float(c[1]), float(c[2]))


class Canvas:
    def __init__(self, fmt, glow=1.0, glow_radius=1.0, trail_decay=0.0, grain=1.0,
                 background=(0, 0, 0), vignette=0.35):
        self.fmt = fmt
        self.W, self.H = fmt.width, fmt.height
        self.s = fmt.scale
        self.w, self.h = fmt.units
        self.glow = glow
        self.glow_radius = glow_radius
        self.grain = grain
        self.img = np.zeros((self.H, self.W, 3), np.uint8)
        # persistent afterglow layer (motion trails); 0 disables
        self.trail_decay = trail_decay
        self.trail = np.zeros_like(self.img) if trail_decay > 0 else None
        self._bg = self._make_background(background, vignette)
        rs = np.random.default_rng(1234)
        self._grain = [rs.normal(0, 1, (self.H // 2, self.W // 2, 1)).astype(np.float32) for _ in range(4)]
        self._fonts = {}
        self.target = self.img

    # ----- frame lifecycle -----

    def _make_background(self, bg, vignette):
        y, x = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        r = np.hypot((x - self.W / 2) / (self.W / 2), (y - self.H / 2) / (self.H / 2)) / np.sqrt(2)
        k = 1 - vignette * r ** 2
        base = np.array(bg, np.float32)[None, None, :] * k[..., None]
        return np.clip(base, 0, 255).astype(np.uint8)

    def begin(self):
        np.copyto(self.img, self._bg)
        if self.trail is not None:
            # multiply then subtract a little so faint trails reach true black
            cv2.addWeighted(self.trail, self.trail_decay, self.trail, 0, -1.0, dst=self.trail)
        self.target = self.img

    def on_trail(self):
        """Subsequent draw calls go to the persistent trail layer."""
        self.target = self.trail
        return self

    def on_main(self):
        self.target = self.img
        return self

    def finish(self, frame_index=0, flash=0.0):
        """Composite trails, apply bloom + grain, return the uint8 RGB frame."""
        img = self.img
        if self.trail is not None:
            img = cv2.add(img, self.trail)
        if self.glow > 0:
            img = self._bloom(img)
        if flash > 0:
            img = cv2.addWeighted(img, 1.0, np.full_like(img, 255), flash, 0)
        if self.grain > 0:
            g = self._grain[frame_index % 4]
            g = cv2.resize(g, (self.W, self.H), interpolation=cv2.INTER_NEAREST)[..., None]
            img = np.clip(img.astype(np.float32) + g * self.grain, 0, 255).astype(np.uint8)
        return img

    def _bloom(self, img):
        # two-octave bloom computed at low resolution, then one full-res add
        q = 4
        small = cv2.resize(img, (self.W // q, self.H // q), interpolation=cv2.INTER_AREA).astype(np.float32)
        r = self.glow_radius * self.s
        b1 = cv2.GaussianBlur(small, (0, 0), 3.0 * r)
        tiny = cv2.resize(small, (self.W // (q * 4), self.H // (q * 4)), interpolation=cv2.INTER_AREA)
        b2 = cv2.GaussianBlur(tiny, (0, 0), 3.5 * r)
        b2 = cv2.resize(b2, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_LINEAR)
        bloom = (b1 * 0.9 + b2 * 0.8) * self.glow
        bloom = cv2.resize(np.clip(bloom, 0, 255).astype(np.uint8), (self.W, self.H),
                           interpolation=cv2.INTER_LINEAR)
        return cv2.add(img, bloom)

    # ----- primitives (scene units) -----

    def P(self, x, y):
        return (int(round(x * self.s * SUB)), int(round(y * self.s * SUB)))

    def _t(self, width):
        return max(1, int(round(width * self.s)))

    def circle(self, x, y, r, col, fill=True, width=2.0):
        cv2.circle(self.target, self.P(x, y), max(1, int(round(r * self.s * SUB))), _c(col),
                   -1 if fill else self._t(width), AA, SHIFT)

    def line(self, x0, y0, x1, y1, col, width=2.0):
        cv2.line(self.target, self.P(x0, y0), self.P(x1, y1), _c(col), self._t(width), AA, SHIFT)

    def polyline(self, pts, col, width=2.0, closed=False):
        p = np.round(np.asarray(pts, np.float64) * self.s * SUB).astype(np.int32)
        cv2.polylines(self.target, [p], closed, _c(col), self._t(width), AA, SHIFT)

    def polygon(self, pts, col):
        p = np.round(np.asarray(pts, np.float64) * self.s * SUB).astype(np.int32)
        cv2.fillPoly(self.target, [p], _c(col), AA, SHIFT)

    def arc(self, x, y, r, a0_deg, a1_deg, col, width=2.0):
        """Arc from a0 to a1 degrees (clockwise on screen, 0 = +x)."""
        rr = int(round(r * self.s * SUB))
        cv2.ellipse(self.target, self.P(x, y), (rr, rr), 0, a0_deg, a1_deg, _c(col),
                    self._t(width), AA, SHIFT)

    # ----- neon helpers: colored halo stroke + hot core -----

    def neon_line(self, x0, y0, x1, y1, col, width=4.0):
        self.line(x0, y0, x1, y1, np.asarray(col) * 0.55, width * 2.2)
        self.line(x0, y0, x1, y1, hot(col, 0.45), width)

    def neon_polyline(self, pts, col, width=4.0, closed=False):
        self.polyline(pts, np.asarray(col) * 0.55, width * 2.2, closed)
        self.polyline(pts, hot(col, 0.45), width, closed)

    def neon_arc(self, x, y, r, a0, a1, col, width=4.0):
        self.arc(x, y, r, a0, a1, np.asarray(col) * 0.55, width * 2.2)
        self.arc(x, y, r, a0, a1, hot(col, 0.45), width)

    def neon_circle(self, x, y, r, col, core=0.6):
        self.circle(x, y, r * 1.0, col)
        self.circle(x, y, r * core, hot(col, 0.55))

    # ----- text -----

    def font(self, size, weight="Bold"):
        key = (int(size * self.s), weight)
        if key not in self._fonts:
            path = os.path.join(FONT_DIR, f"Inter-{weight}.otf")
            self._fonts[key] = ImageFont.truetype(path, key[0])
        return self._fonts[key]

    def text_layer(self, items):
        """Render text items to an RGBA-ish (rgb, alpha) pair once; blit with blit_text.

        items: list of (text, x, y, size, rgb, anchor, weight)
        """
        im = Image.new("RGB", (self.W, self.H))
        d = ImageDraw.Draw(im)
        for text, x, y, size, col, anchor, weight in items:
            d.text((x * self.s, y * self.s), text, font=self.font(size, weight),
                   fill=tuple(int(v) for v in np.clip(col, 0, 255)), anchor=anchor)
        return np.asarray(im)

    def symbol_font(self, size, kind="symbol"):
        """A font with glyphs Inter lacks: zodiac signs etc. (kind "symbol") or colour emoji
        (kind "emoji"); first system font found."""
        key = (int(size * self.s), kind)
        if key not in self._fonts:
            paths = EMOJI_FONTS if kind == "emoji" else SYMBOL_FONTS
            path = next((p for p in paths if os.path.exists(p)), None)
            if path is None:
                raise RuntimeError(f"no {kind} font found (looked for {paths})")
            self._fonts[key] = ImageFont.truetype(path, key[0])
        return self._fonts[key]

    def text(self, text, x, y, size, col, anchor="mm", weight="Bold", stroke=0, stroke_col=(0, 0, 0),
             symbol=False):
        """Draw text directly (PIL on a crop of the target). Fine for a few labels/frame.

        stroke: outline width in units (keeps small labels legible over busy scenes);
        symbol: use symbol_font() instead of Inter; "emoji" draws a colour emoji (col is ignored).
        """
        emoji = symbol == "emoji"
        f = self.symbol_font(size, "emoji" if emoji else "symbol") if symbol else self.font(size, weight)
        sw = int(round(stroke * self.s))
        l, t, r, b = f.getbbox(text, anchor=anchor, stroke_width=sw)
        px, py = int(x * self.s), int(y * self.s)
        x0, y0 = max(0, px + l - 2), max(0, py + t - 2)
        x1, y1 = min(self.W, px + r + 2), min(self.H, py + b + 2)
        if x1 <= x0 or y1 <= y0:
            return
        crop = Image.fromarray(self.target[y0:y1, x0:x1])
        ImageDraw.Draw(crop).text((px - x0, py - y0), text, font=f,
                                  fill=tuple(int(v) for v in np.clip(col, 0, 255)), anchor=anchor,
                                  stroke_width=sw, stroke_fill=tuple(int(v) for v in np.clip(stroke_col, 0, 255)),
                                  embedded_color=emoji)
        self.target[y0:y1, x0:x1] = np.asarray(crop)

    def shade_rect(self, x0, y0, x1, y1, k=0.3):
        """Darken a rectangle (backing panel for text over busy scenes)."""
        a, b = max(0, int(y0 * self.s)), min(self.H, int(y1 * self.s))
        c, d = max(0, int(x0 * self.s)), min(self.W, int(x1 * self.s))
        if b > a and d > c:
            self.target[a:b, c:d] = (self.target[a:b, c:d] * k).astype(np.uint8)

    def blit_add(self, layer, alpha=1.0):
        if alpha >= 0.999:
            cv2.add(self.target, layer, dst=self.target)
        elif alpha > 0:
            cv2.addWeighted(self.target, 1.0, layer, alpha, 0, dst=self.target)


class SoftCanvas(Canvas):
    """Light, matte mode for the Sandglass engine (docs/engines/sandglass.md).

    Normal "over" compositing, no bloom, a light grain, a soft cream background with an optional
    tabletop, and helpers for blurred multiply shadows, soft highlights and translucent strokes.
    A subclass so Bright Lights / Foundry (plain Canvas) render exactly as before.
    """

    def __init__(self, fmt, background=(250, 245, 237), vignette=0.07, grain=1.3,
                 table_y=None, table=(238, 228, 213), table_soft=8.0, light=0.03, zoom=1.0):
        self._table = (table_y, table, table_soft, light)
        super().__init__(fmt, glow=0.0, trail_decay=0.0, grain=grain, background=background,
                         vignette=vignette)
        if zoom != 1.0:
            # a closer camera: every unit is `zoom` x more pixels, the frame fewer units across
            self.s *= zoom
            self.w, self.h = self.w / zoom, self.h / zoom
            self._bg = self._make_background(background, vignette)
        # grain as precomputed +/- uint8 layers: two saturating adds per frame instead of a float pass
        self._grain_pm = []
        for g in self._grain:
            g = cv2.resize(g, (self.W, self.H), interpolation=cv2.INTER_NEAREST)
            g = np.round(g * grain).astype(np.int16)
            self._grain_pm.append((np.clip(g, 0, 255).astype(np.uint8)[..., None].repeat(3, 2),
                                   np.clip(-g, 0, 255).astype(np.uint8)[..., None].repeat(3, 2)))

    def finish(self, frame_index=0, flash=0.0):
        img = self.img
        if flash > 0:
            img = cv2.addWeighted(img, 1.0, np.full_like(img, 255), flash, 0)
        if self.grain > 0:
            pos, neg = self._grain_pm[frame_index % 4]
            img = cv2.subtract(cv2.add(img, pos), neg)
        return img

    def capture_overlay(self, box, draw):
        """Record `draw(cv)` inside box (x0, y0, x1, y1 units) as a reusable overlay.

        Every SoftCanvas operation is an affine blend per pixel (strokes, translucency, soft light,
        multiply shadows), so drawing once over black and once over white gives A, B with
        result = frame * A + B. Replaying that is far cheaper than redrawing many soft strokes.
        Returns (A, B, px, py); apply with overlay(layer, dx, dy) (integer pixel shift).
        """
        s = self.s
        x0, y0 = max(0, int(box[0] * s)), max(0, int(box[1] * s))
        x1, y1 = min(self.W, int(np.ceil(box[2] * s))), min(self.H, int(np.ceil(box[3] * s)))
        reg = self.img[y0:y1, x0:x1]
        saved, target = reg.copy(), self.target
        self.target = self.img
        reg[:] = 0
        draw(self)
        b = reg.astype(np.float32)
        reg[:] = 255
        draw(self)
        a = (reg.astype(np.float32) - b) / 255.0
        reg[:] = saved
        self.target = target
        return a, b, x0, y0

    def overlay(self, layer, dx=0, dy=0):
        a, b, px, py = layer
        h, w = b.shape[:2]
        px, py = px + dx, py + dy
        x0, y0, x1, y1 = max(0, px), max(0, py), min(self.W, px + w), min(self.H, py + h)
        if x1 <= x0 or y1 <= y0:
            return
        sa = a[y0 - py:y1 - py, x0 - px:x1 - px]
        sb = b[y0 - py:y1 - py, x0 - px:x1 - px]
        dst = self.target[y0:y1, x0:x1]
        dst[:] = np.clip(dst * sa + sb + 0.5, 0, 255).astype(np.uint8)

    def bake_background(self):
        """Keep what has been drawn so far (static set dressing, shadows) as every later frame's start."""
        self._bg = self.img.copy()

    def _make_background(self, bg, vignette):
        y, x = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        img = np.empty((self.H, self.W, 3), np.float32)
        img[:] = np.asarray(bg, np.float32)
        table_y, table, soft, light = self._table
        if table_y is not None:
            ty = table_y * self.s
            u = np.clip((y - ty) / (soft * self.s) + 0.5, 0, 1)[..., None]
            depth = np.clip((y - ty) / max(1.0, self.H - ty), 0, 1)[..., None]
            top = np.asarray(table, np.float32) * (1 - 0.05 * depth)     # a touch darker toward us
            img = img * (1 - u) + top * u
        # gentle light from the top-left, then a very soft vignette
        img *= (1 + light * (1 - 2 * (0.6 * x / self.W + 0.4 * y / self.H)))[..., None]
        r = np.hypot((x - self.W / 2) / (self.W / 2), (y - self.H / 2) / (self.H / 2)) / np.sqrt(2)
        img *= (1 - vignette * r ** 2)[..., None]
        return np.clip(img, 0, 255).astype(np.uint8)

    # ----- extra primitives -----

    def ellipse(self, x, y, rx, ry, col, fill=True, width=2.0, a0=0, a1=360, angle=0):
        axes = (max(1, int(round(rx * self.s * SUB))), max(1, int(round(ry * self.s * SUB))))
        cv2.ellipse(self.target, self.P(x, y), axes, angle, a0, a1, _c(col),
                    -1 if fill else self._t(width), AA, SHIFT)

    class _Translucent:
        def __init__(self, cv, alpha, box):
            self.cv, self.alpha = cv, alpha
            if box is None:
                self.sl = (slice(None), slice(None))
            else:
                s, (x0, y0, x1, y1) = cv.s, box
                self.sl = (slice(max(0, int(y0 * s) - 2), max(0, int(np.ceil(y1 * s)) + 2)),
                           slice(max(0, int(x0 * s) - 2), max(0, int(np.ceil(x1 * s)) + 2)))

        def __enter__(self):
            self.base = self.cv.target[self.sl].copy()
            return self.cv

        def __exit__(self, *exc):
            t = self.cv.target[self.sl]
            cv2.addWeighted(t, self.alpha, self.base, 1 - self.alpha, 0, dst=t)

    def translucent(self, alpha, box=None):
        """`with cv.translucent(0.3, box): cv.line(...)` - whatever is drawn inside is blended at alpha.
        box = (x0, y0, x1, y1) in units bounds the drawing (much faster than the whole frame)."""
        return self._Translucent(self, alpha, box)

    def composite(self, px, py, rgb, alpha):
        """Alpha-composite an (h, w, 3) float/uint8 patch at pixel (px, py) with (h, w) alpha 0..1."""
        h, w = alpha.shape
        x0, y0 = max(0, px), max(0, py)
        x1, y1 = min(self.W, px + w), min(self.H, py + h)
        if x1 <= x0 or y1 <= y0:
            return
        a = alpha[y0 - py:y1 - py, x0 - px:x1 - px, None]
        src = rgb[y0 - py:y1 - py, x0 - px:x1 - px]
        dst = self.target[y0:y1, x0:x1].astype(np.float32)
        self.target[y0:y1, x0:x1] = np.clip(dst + (src - dst) * a, 0, 255).astype(np.uint8)

    # ----- soft light & shadow (blurred masks) -----

    def _soft_mask(self, shapes, blur):
        """Rasterise shapes into a blurred 0..1 mask. Returns (mask, x0, y0) in full-res pixels.

        shapes: ("ellipse", x, y, rx, ry) | ("poly", pts) | ("line", x0, y0, x1, y1, width), units.
        """
        sig = max(0.5, blur * self.s)
        q = int(np.clip(sig // 1.5, 1, 4))         # work at lower res when the blur hides it
        pts = []
        for sh in shapes:
            if sh[0] == "ellipse":
                _, x, y, rx, ry = sh
                pts += [(x - rx, y - ry), (x + rx, y + ry)]
            elif sh[0] == "poly":
                pts += [tuple(p) for p in sh[1]]
            else:
                _, ax, ay, bx, by, wd = sh
                pts += [(min(ax, bx) - wd, min(ay, by) - wd), (max(ax, bx) + wd, max(ay, by) + wd)]
        p = np.asarray(pts, np.float64) * self.s
        pad = 3 * sig + 2 * q
        x0 = int(max(0, np.floor(p[:, 0].min() - pad)) // q * q)
        y0 = int(max(0, np.floor(p[:, 1].min() - pad)) // q * q)
        x1 = int(min(self.W, np.ceil(p[:, 0].max() + pad)))
        y1 = int(min(self.H, np.ceil(p[:, 1].max() + pad)))
        if x1 <= x0 or y1 <= y0:
            return None, 0, 0
        mw, mh = -(-(x1 - x0) // q), -(-(y1 - y0) // q)
        m = np.zeros((mh, mw), np.float32)
        k = self.s / q * SUB

        def P(x, y):
            return (int(round((x * self.s - x0) / q * SUB)), int(round((y * self.s - y0) / q * SUB)))

        for sh in shapes:
            if sh[0] == "ellipse":
                _, x, y, rx, ry = sh
                cv2.ellipse(m, P(x, y), (max(1, int(rx * k)), max(1, int(ry * k))), 0, 0, 360, 1.0, -1, AA, SHIFT)
            elif sh[0] == "poly":
                pp = np.array([P(*pt) for pt in sh[1]], np.int32)
                cv2.fillPoly(m, [pp], 1.0, AA, SHIFT)
            else:
                _, ax, ay, bx, by, wd = sh
                cv2.line(m, P(ax, ay), P(bx, by), 1.0, max(1, int(round(wd * self.s / q))), AA, SHIFT)
        m = cv2.GaussianBlur(m, (0, 0), sig / q)
        if q > 1:
            m = cv2.resize(m, (mw * q, mh * q), interpolation=cv2.INTER_LINEAR)
        return np.clip(m[:y1 - y0, :x1 - x0], 0, 1), x0, y0

    def soft_shadow(self, shapes, strength=0.3, blur=16.0, tint=(120, 98, 84)):
        """Blurred multiply shadow (warm, never pure black) - drawn under the objects that cast it."""
        m, x0, y0 = self._soft_mask(shapes, blur)
        if m is None:
            return
        h, w = m.shape
        mul = 1 - (strength * m)[..., None] * (1 - np.asarray(tint, np.float32) / 255)
        reg = self.target[y0:y0 + h, x0:x0 + w]
        reg[:] = np.clip(reg * mul, 0, 255).astype(np.uint8)

    def soft_light(self, shapes, strength=0.5, blur=3.0, color=(255, 255, 255)):
        """Paint `color` through a soft-edged mask (highlights, glass glints, haze)."""
        m, x0, y0 = self._soft_mask(shapes, blur)
        if m is None:
            return
        h, w = m.shape
        self.composite(x0, y0, np.broadcast_to(np.asarray(color, np.float32), (h, w, 3)), m * strength)


class SkyCanvas(Canvas):
    """Near-black HDR mode for the Deep Sky engine (docs/engines/deep_sky.md).

    Scenes draw linear light into a float32 buffer `hdr` (0 = black, ~1 = bright, stars far above):
    gaussian star splats, alpha-composited patches (planets hide what is behind them) and a uint8
    `lines` layer for anti-aliased cv2 strokes, merged with flush_lines(). finish() adds a soft
    lens bloom, tone-maps (1 - e^-x, then a gamma-2 curve so the dark end keeps its levels) and
    quantises through a fixed fine dither pattern: dark gradients don't band, and since the pattern
    never changes the encoder spends no bits on it over hours of video.
    A subclass so the other engines (plain Canvas / SoftCanvas) render exactly as before.
    """

    def __init__(self, fmt, glow=1.0, exposure=1.0, dither=0.8):
        super().__init__(fmt, glow=0.0, trail_decay=0.0, grain=0.0, background=(0, 0, 0), vignette=0.0)
        self.bloom, self.exposure = glow, exposure
        self.hdr = np.zeros((self.H, self.W, 3), np.float32)
        self.lines = np.zeros((self.H, self.W, 3), np.uint8)
        self.lines_gain = 0.02           # a 255 line pixel adds this much linear light
        self.overlay = []                # set_overlay(): text composited after tone mapping
        self._sky = None                 # per-frame starting image (set_background); None = the scene paints
                                         # every pixel of hdr itself (e.g. warping its sky straight into it)
        # high-passed white noise ~ blue noise: fine, even, nothing a viewer reads as grain
        rs = np.random.default_rng(4321)
        n = rs.random((self.H, self.W, 3)).astype(np.float32) + rs.random((self.H, self.W, 3)).astype(np.float32)
        n -= cv2.GaussianBlur(n, (0, 0), 1.2)
        self._dither = (n / (np.std(n) + 1e-9) * 0.5 * dither + 0.5).astype(np.float32)   # +0.5: rounding
        self.target = self.lines

    def set_background(self, img):
        self._sky = np.ascontiguousarray(img, np.float32)

    def begin(self):
        if self._sky is not None:
            np.copyto(self.hdr, self._sky)
        self.lines[:] = 0
        self.target = self.lines

    def flush_lines(self):
        """Add what was drawn on the line layer so far, so later patches can cover it."""
        cv2.addWeighted(self.hdr, 1.0, self.lines, self.lines_gain / 255.0, 0.0, dst=self.hdr, dtype=cv2.CV_32F)
        self.lines[:] = 0

    def splat(self, x, y, flux, sigma=0.75, radius=2):
        """Gaussian points at unit positions x, y (arrays), flux (n, 3) linear light each. Weights are
        normalised per point, so a star keeps its brightness at any sub-pixel position (no shimmer)."""
        px, py = np.asarray(x, np.float64) * self.s, np.asarray(y, np.float64) * self.s
        flux = np.asarray(flux, np.float32).reshape(len(px), 3)
        sig = np.broadcast_to(np.asarray(sigma, np.float64), px.shape)
        ok = (px > -radius) & (px < self.W + radius) & (py > -radius) & (py < self.H + radius)
        px, py, flux, sig = px[ok], py[ok], flux[ok], sig[ok]
        if not len(px):
            return
        o = np.arange(-radius, radius + 1)
        ix = np.floor(px)[:, None] + o[None, :]
        iy = np.floor(py)[:, None] + o[None, :]
        wx = np.exp(-0.5 * ((ix + 0.5 - px[:, None]) / sig[:, None]) ** 2)
        wy = np.exp(-0.5 * ((iy + 0.5 - py[:, None]) / sig[:, None]) ** 2)
        w = wy[:, :, None] * wx[:, None, :]
        w /= w.sum(axis=(1, 2), keepdims=True)
        X = np.broadcast_to(ix[:, None, :], w.shape).astype(np.int64)
        Y = np.broadcast_to(iy[:, :, None], w.shape).astype(np.int64)
        inside = (X >= 0) & (X < self.W) & (Y >= 0) & (Y < self.H)
        X, Y, wf = X[inside], Y[inside], w[inside]
        k = np.broadcast_to(np.arange(len(px))[:, None, None], w.shape)[inside]
        if not len(X):
            return
        # accumulate in the splats' bounding box only
        x0, y0 = X.min(), Y.min()
        bw, bh = X.max() - x0 + 1, Y.max() - y0 + 1
        idx = (Y - y0) * bw + (X - x0)
        box = self.hdr[y0:y0 + bh, x0:x0 + bw]
        for c in range(3):
            box[..., c] += np.bincount(idx, wf * flux[k, c], minlength=bw * bh).reshape(bh, bw)

    def points(self, x, y, flux, sigma=0.65):
        """Many small stars at once: bilinear deposit (keeps each star's total light at any sub-pixel
        position) into a scratch layer, one gaussian blur, add. Much faster than splat() for thousands."""
        if not hasattr(self, "_pts"):
            self._pts = np.zeros_like(self.hdr)
        acc = self._pts
        acc[:] = 0
        px, py = np.asarray(x) * self.s - 0.5, np.asarray(y) * self.s - 0.5
        flux = np.asarray(flux, np.float32).reshape(len(px), 3)
        ok = (px >= 0) & (px < self.W - 1) & (py >= 0) & (py < self.H - 1)
        px, py, flux = px[ok], py[ok], flux[ok]
        ix, iy = np.floor(px).astype(np.int64), np.floor(py).astype(np.int64)
        fx, fy = (px - ix).astype(np.float32)[:, None], (py - iy).astype(np.float32)[:, None]
        for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            np.add.at(acc, (iy + dy, ix + dx), flux * wt)
        cv2.GaussianBlur(acc, (0, 0), sigma * self.s, dst=acc)
        self.hdr += acc

    def over(self, px, py, rgb, alpha):
        """Composite an (h, w, 3) linear patch with (h, w) coverage at pixel (px, py) over the frame."""
        h, w = alpha.shape
        x0, y0, x1, y1 = max(0, px), max(0, py), min(self.W, px + w), min(self.H, py + h)
        if x1 <= x0 or y1 <= y0:
            return
        a = alpha[y0 - py:y1 - py, x0 - px:x1 - px, None]
        dst = self.hdr[y0:y1, x0:x1]
        dst += (rgb[y0 - py:y1 - py, x0 - px:x1 - px] - dst) * a

    def add(self, px, py, rgb):
        """Add an (h, w, 3) linear patch at pixel (px, py) (glows, halos)."""
        h, w = rgb.shape[:2]
        x0, y0, x1, y1 = max(0, px), max(0, py), min(self.W, px + w), min(self.H, py + h)
        if x1 > x0 and y1 > y0:
            self.hdr[y0:y1, x0:x1] += rgb[y0 - py:y1 - py, x0 - px:x1 - px]

    def finish(self, frame_index=0, flash=0.0):
        self.flush_lines()
        img = self.hdr
        if self.bloom > 0:
            # lens bloom from the bright parts: a tight and a wide octave at low resolution
            q = 4
            small = cv2.resize(img, (self.W // q, self.H // q), interpolation=cv2.INTER_AREA)
            hi = np.maximum(small - 0.15, 0)
            r = self.s / q
            b1 = cv2.GaussianBlur(hi, (0, 0), 6.0 * r)
            tiny = cv2.resize(hi, (self.W // (q * 4), self.H // (q * 4)), interpolation=cv2.INTER_AREA)
            b2 = cv2.resize(cv2.GaussianBlur(tiny, (0, 0), 30.0 * r / 4), (small.shape[1], small.shape[0]),
                            interpolation=cv2.INTER_LINEAR)
            bloom = (b1 * 0.10 + b2 * 0.05) * self.bloom
            img += cv2.resize(bloom, (self.W, self.H), interpolation=cv2.INTER_LINEAR)     # hdr is redrawn next frame
        # tone map + gamma 2: sqrt(1 - e^-x), with cv2's vectorised maths on a one-channel view (cv2 would
        # apply a plain scalar to the first channel only of a 3-channel image)
        x = img.reshape(self.H, -1)
        np.multiply(x, np.float32(-self.exposure), out=x)
        np.clip(x, -60.0, 0.0, out=x)
        y = cv2.sqrt(cv2.subtract(1.0, cv2.exp(x)))
        out = cv2.scaleAdd(y, 255.0, self._dither.reshape(self.H, -1))
        np.clip(out, 0, 255, out=out)
        out = out.astype(np.uint8).reshape(self.H, self.W, 3)
        for rgb, a, y0, y1, x0, x1 in self.overlay:     # fixed text (Shorts: hook, footer), after tone mapping
            box = out[y0:y1, x0:x1].astype(np.float32)
            out[y0:y1, x0:x1] = (box + (rgb - box) * a).astype(np.uint8)
        return out

    def set_overlay(self, items):
        """Text drawn on top of every frame after tone mapping, so it stays crisp and exactly its colour.
        items: (text, x, y, size, rgb, weight), centred at x, y (units)."""
        self.overlay = []
        for text, x, y, size, rgb, weight in items:
            f = self.font(size, weight)
            l, t, r, b = f.getbbox(text, anchor="mm")
            px, py = int(x * self.s), int(y * self.s)
            x0, y0 = max(0, px + l - 2), max(0, py + t - 2)
            x1, y1 = min(self.W, px + r + 2), min(self.H, py + b + 2)
            cov = Image.new("L", (x1 - x0, y1 - y0))
            ImageDraw.Draw(cov).text((px - x0, py - y0), text, font=f, fill=255, anchor="mm")
            a = np.asarray(cov, np.float32)[..., None] / 255.0
            self.overlay.append((np.float32(rgb), a, y0, y1, x0, x1))
