"""Going in and out through a door the way a real door works.

Owner (FK0006 review, 2026-11-01): "When they're walking into the night shift building, they still walk through the
wall." The old way drew the rock (or the hall's end wall) IN FRONT of the Keepers, so on the way to the door they
slid into solid rock beside it, and inside they slid sideways behind the rock.

The rule now (docs/engines/forest_keepers.md, "Doors"): the wall a door is in stands BEHIND the walkway. Outside, a
Keeper walks in front of the wall like in front of any house. At the door it walks straight in, away from the camera:
smaller, its feet climbing the tunnel floor, darker, and it fades into the dark. While it is in there it is drawn
only inside the opening and behind the door frame (hidden by clipping, never by a patch). Coming out is the same
backwards. Nothing solid is ever drawn in front of a walking Keeper: acts declare their front-layer walls in
`walls(t)` and the scene counts any Keeper overlapping one (stat `wall_clips`, must be 0).

The opening must be wide enough for the widest Keeper to stand in it before it starts to recede (Hans' tentacles
are ~380 wide at monster_scale 0.55): DOOR_W.
"""
import math

import numpy as np

from families.foundry.keepers.common import lerp, seg, smoothstep
from families.foundry.products.monster import Xform

DOOR_W = 460.0          # opening width (Hans' tentacles ~380 at scale 0.55, plus a margin each side)
DEPTH_T = 2.8           # seconds from the doorstep into the dark (or out of it)

# half-widths of the drawn Keepers at k = 1 (measured from Monster.draw, new look)
HALF_W = {"wheels": 265.0, "tentacles": 348.0, "teeth": 170.0, "springs": 166.0, "lantern": 150.0, "digger": 250.0,
          "sprout": 230.0}


def half_width(m):
    return HALF_W.get(m.kind, 300.0) * m.k


def depth_in(t, t0, dur=DEPTH_T):
    """0 at the doorstep at t0 -> 1 in the dark: sets off gently, then walks at a steady pace."""
    u = seg(t, t0, t0 + dur)
    r = 0.25                                            # the first quarter speeds up from standing
    if u < r:
        return u * u / (2 * r) / (1 - r / 2)
    return (u - r / 2) / (1 - r / 2)


def depth_out(t, t0, dur=DEPTH_T):
    """1 in the dark at t0 -> 0 on the doorstep: steady pace, slows down into the first step outside."""
    return depth_in(t0 + dur - (t - t0), t0, dur) if t < t0 + dur else 0.0


class Doorway:
    """An opening (d0..d1, from floor - h up to the floor) in a wall behind the walkway."""

    def __init__(self, d0, d1, floor, h, rise=70.0, far=0.42, dark=0.7):
        self.d0, self.d1, self.floor, self.h = d0, d1, floor, h
        self.xc = (d0 + d1) / 2
        self.rise, self.far, self.dark = rise, far, dark

    def opening(self):
        """Clip polygon: the opening down to just under the floor line (feet stand on it)."""
        return [(self.d0, self.floor - self.h), (self.d1, self.floor - self.h), (self.d1, self.floor + 40),
                (self.d0, self.floor + 40)]

    def fits(self, m, x=None):
        x = self.xc if x is None else x
        hw = half_width(m)
        return self.d0 + 6 <= x - hw and x + hw <= self.d1 - 6

    def pose(self, u):
        """-> (scale, feet lift, shade, visibility) at depth u."""
        sc = 1.0 - self.far * u
        return sc, self.rise * u, 1.0 - self.dark * u, 1.0 - smoothstep(seg(u, 0.5, 1.0))

    def walking(self, act, m, t, dt, u, y, dy=0.0):
        """place() for a Keeper in the doorway: standing at the door's middle, walking (gait, wheels) into depth."""
        act.place(m, self.xc, t, dt, y=y, dy=dy, walk=1.0 if 0.0 < u < 1.0 else 0.0)
        if 0.0 < u < 1.0:
            if m.kind == "wheels":
                m.wheel_rot += dt * 3.0
            elif m.kind != "lantern":
                d, a = act.poses[m.kind]
                act.poses[m.kind] = (d - abs(math.sin(m.gait * 0.5)) * 8, a)

    def draw_inside(self, act, c, t, depth):
        """Draw every Keeper with depth u > 0 ({kind: u}), deepest first, inside the opening only."""
        s = act.s
        if not s.visible(self.d0 - 100, self.d1 + 100):
            return
        for kind, u in sorted(depth.items(), key=lambda e: -e[1]):
            m = act.m(kind)
            if m is None or u <= 0.0 or u >= 1.0 or kind not in act.poses:
                continue
            sc, lift, shade, vis = self.pose(u)
            dy, ang = act.poses[kind]
            fy = m.y

            def draw(c=c, m=m, sc=sc, lift=lift, dy=dy, fy=fy):
                mc = Xform(c, 0, dy - lift, 0.0, sc, m.x, fy)
                m.draw(mc, t, s.glow)

            fade_clip(c, s.glow, self.opening(), draw, shade, vis)


def fade_clip(c, glow, pts, draw, shade=1.0, vis=1.0):
    """draw(), then keep it only inside polygon pts (world units), darkened by `shade` and faded to `vis` over what
    was there before. The glow layer gets the same clip and fade (eyes and lamps must not shine through the wall)."""
    img = c.target
    before = img.copy()
    gl = glow.layer if glow is not None else None
    gbefore = gl.copy() if gl is not None else None
    draw()
    mask = np.zeros(img.shape[:2], np.uint8)
    c.target = mask
    try:
        c.polygon(pts, (255, 255, 255))
    finally:
        c.target = img
    a = mask[..., None].astype(np.float32) / 255.0
    b = before.astype(np.float32)
    img[:] = np.clip(b + (img.astype(np.float32) * shade - b) * a * vis + 0.5, 0, 255).astype(np.uint8)
    if gl is not None:
        gb = gbefore.astype(np.float32)
        gl[:] = np.clip(gb + (gl.astype(np.float32) * shade - gb) * a * vis + 0.5, 0, 255).astype(np.uint8)
