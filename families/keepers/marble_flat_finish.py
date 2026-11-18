"""The Treetop Marble Run (flat), beat 3b: the tunnel, the peg forest goes up, the finish lantern (docs/engines/
forest_keepers_marble_run_flat.md).

The last ramp stands on its legs in two halves from the start, the left half ending at the mound's left face, the
right half starting at its right face.
- Digs digs the tunnel: his right paw scoops into the mound face at the ramp's height again and again and flicks each
  load back over to the path behind him, where it lands on a heap that grows; the mouth grows with every stroke and
  near the end the far side breaks open (a few clods tumble out).
- Hans lifts the peg-forest panel off its blocks with four tentacles at once and carries it over to TREE_A, slowly up
  onto the ramp's end, and lets go.
- Glo floats to the finish lantern; his lantern flares, a mote of light drifts over and it lights.
"""
import math

import numpy as np
import skia

from families.foundry.keepers.common import smoothstep

from . import marble_flat_course as MC
from . import storycheck as sc
from .marble_flat_build import PANEL_DX, PANEL_DY
from .marble_flat_world import BACK, G, TREE_A, TREE_B, WOOD2, WOOD3
from .storybook import oval, rrect, tone

K = 0.72
DIGS_ARM = 95.0 * K
DIGS_SH = 118.0 * K
GS = 1500.0                          # px/s^2 for the soil
DIG_X = MC.TUNNEL_IN - 58.0 - DIGS_SH - 0.55 * DIGS_ARM
HEAP_X = DIG_X - 150.0
LANTERN_X = MC.FINISH_X + 40.0       # the finish lantern, on a post behind the ramp
LANTERN_Y = BACK - 210.0


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def digs_shoulder(x, y, sx, t):
    by = y - 150 * K + 2 * K * math.sin(t * 2.6)
    return x + sx * DIGS_SH, by + 4 * K


class Finish:
    def __init__(self, t0, hans_from):
        self.t0 = t0
        # the tunnel: ten strokes of Digs' right paw
        self.dig = (t0 + 0.5, t0 + 0.5 + 10 * 1.05)
        self.strokes = [(self.dig[0] + i * 1.05, self.dig[0] + (i + 1) * 1.05) for i in range(10)]
        self.through = (self.strokes[7][0], self.strokes[9][1])     # the far side breaks open
        rs = np.random.default_rng(17)
        self.clods = []                                           # (id, t_scoop, t_release, size, vx, vy)
        for i, (a, b) in enumerate(self.strokes):
            for q in range(2):
                self.clods.append((f"soil {i}.{q}", a + 0.32 * (b - a), a + 0.78 * (b - a),
                                   rs.uniform(5.0, 8.0) if q == 0 else rs.uniform(3.0, 4.5),
                                   rs.uniform(-250, -200), rs.uniform(-300, -240)))   # the paw's flick
        # the heap is where the soil really lands (a clod's flight from the paw, Digs standing at DIG_X)
        lands = [self._land_x(c) for c in self.clods if c[0].endswith(".0")]
        self.heap_x = sum(lands) / len(lands)
        self.out_clods = [(f"clod out {q}", self.through[0] + 0.5 + 0.35 * q, rs.uniform(4.5, 7.0)) for q in range(3)]
        self.dig_end = self.dig[1] + 0.6
        # the peg forest goes up onto TREE_A (Hans walks over first: the plan times his walk)
        self.hans_from = hans_from
        self.panel_at = self.dig_end + 1.5 + abs(hans_from - self.panel_stand()) / 95.0 + 1.0
        self.grip = (self.panel_at + 0.2, self.panel_at + 1.4)
        self.lift = (self.grip[1], self.grip[1] + 1.2)
        self.carry = (self.lift[1], self.lift[1] + 4.4)           # over to its place, slowly
        self.seat = (self.carry[1], self.carry[1] + 1.4)
        self.let_go = (self.seat[1], self.seat[1] + 1.0)
        self.panel_end = self.let_go[1]
        # the finish lantern
        self.lamp = (self.panel_end + 7.5, self.panel_end + 9.5)
        self.end = self.lamp[1] + 1.0

    # --- Digs
    @staticmethod
    def mouth():
        return MC.TUNNEL_IN - 40.0, MC.fin_y(MC.TUNNEL_IN) - 30.0

    def paw_angle(self, t, x, y):
        """Digs' right arm angle (rad) while he digs, or None."""
        if not (self.dig[0] - 0.6 <= t < self.dig[1] + 0.6):
            return None
        sx_, sy_ = digs_shoulder(x, y, 1, t)
        mx, my = self.mouth()
        a_in = math.atan2(my - sy_, mx - sx_)
        a_back = math.radians(150.0)                              # swept down and back past his side
        rest = math.radians(72.0)
        if t < self.dig[0]:
            return rest + (a_in - rest) * smoothstep(_seg(t, self.dig[0] - 0.6, self.dig[0]))
        if t >= self.dig[1]:
            return a_in + (rest - a_in) * smoothstep(_seg(t, self.dig[1], self.dig[1] + 0.6))
        for a, b in self.strokes:
            if a <= t < b:
                u = (t - a) / (b - a)
                if u < 0.32:                                      # into the face
                    return a_in
                if u < 0.78:                                      # the scoop: down and back (the power stroke)
                    return a_in + (a_back - a_in) * smoothstep((u - 0.32) / 0.46)
                return a_back + (a_in - a_back) * smoothstep((u - 0.78) / 0.22)
        return a_in

    def hole(self, t):
        """(left mouth, right mouth) dug 0..1."""
        n = sum(smoothstep(_seg(t, a + 0.32 * (b - a), a + 0.78 * (b - a))) for a, b in self.strokes)
        return min(1.0, n / 8.0), smoothstep(_seg(t, *self.through))

    def _paw(self, t, dx, dy):
        ang = self.paw_angle(t, dx, dy)
        sx_, sy_ = digs_shoulder(dx, dy, 1, t)
        return sx_ + math.cos(ang) * DIGS_ARM, sy_ + math.sin(ang) * DIGS_ARM

    def clod(self, c, t, digs):
        """(x, y, state) of a scooped clod: in the paw, flying, on the heap (None before / after)."""
        name, ts, tr, r, vx, vy = c
        if t < ts:
            return None
        dx, dy = digs(t)
        if t < tr:
            px, py = self._paw(t, dx, dy)
            return px, py - r * 0.5, "in Digs' paw"
        x0, y0 = self._paw(tr, *digs(tr))
        y0 -= r * 0.5
        u = t - tr
        land = G + 10.0
        tl = (-vy + math.sqrt(vy * vy + 2 * GS * (land - y0))) / GS
        if u < tl:
            return x0 + vx * u, y0 + vy * u + 0.5 * GS * u * u, "flies"
        return None

    def _land_x(self, c):
        name, ts, tr, r, vx, vy = c
        x0, y0 = self._paw(tr, DIG_X, G)
        y0 -= r * 0.5
        tl = (-vy + math.sqrt(vy * vy + 2 * GS * (G + 10.0 - y0))) / GS
        return x0 + vx * tl

    def landed(self, t, digs):
        """Clods on the heap by t (they make it grow) -> count."""
        n = 0
        for c in self.clods:
            name, ts, tr, r, vx, vy = c
            if t > tr + 0.6:
                n += 1
        return n

    def heap_h(self, t):
        n = sum(1 for c in self.clods if t > c[2] + 0.55)
        return 6.0 + 2.2 * n

    def out_clod(self, c, t):
        name, t0, r = c
        if t < t0:
            return None
        x0, y0 = MC.TUNNEL_OUT + 20.0, MC.fin_y(MC.TUNNEL_OUT) - 20.0
        u = t - t0
        # it tumbles out of the mouth and rolls down the mound's slope to the foot
        # it tumbles out of the mouth and down the mound's slope to its foot, where it stops
        t_land = 0.32 + (BACK + 6 - (y0 + 0.5 * GS * 0.32 ** 2)) / 160.0
        uu = min(u, t_land)
        x = x0 + 120 * uu
        y = y0 + 0.5 * GS * min(uu, 0.32) ** 2 + 160 * max(0.0, uu - 0.32)
        return x, y, ("falls" if u < t_land else "rests")

    # --- Hans and the panel
    @staticmethod
    def panel_stand():
        return MC.BOX[1] + PANEL_DX + 130.0                       # Hans' middle just right of the panel

    def panel_pose(self, t):
        """(dx, dy) of the panel from its place on TREE_A."""
        home = (PANEL_DX, PANEL_DY)
        up = (PANEL_DX, PANEL_DY - 70.0)
        over = (0.0, -40.0)
        if t < self.lift[0]:
            return home
        if t < self.lift[1]:
            u = smoothstep(_seg(t, *self.lift))
            return home[0], home[1] + (up[1] - home[1]) * u
        if t < self.carry[1]:
            u = smoothstep(_seg(t, *self.carry))
            return up[0] + (over[0] - up[0]) * u, up[1] + (over[1] - up[1]) * u
        if t < self.seat[1]:
            u = smoothstep(_seg(t, *self.seat))
            return 0.0, over[1] * (1 - u)
        return 0.0, 0.0

    def hans_carry_x(self, t):
        """Hans' middle while he carries the panel (he walks with it, to its right)."""
        dx, _ = self.panel_pose(t)
        return MC.BOX[1] + dx + 130.0

    def hans_targets(self, t, x):
        """Four tentacles on the panel: two under its floor, two on its right wall (his thing: several at once)."""
        a, b = self.grip[0] - 0.4, self.let_go[1]
        if not (a <= t < b + 0.8):
            return []
        on = smoothstep(_seg(t, a, self.grip[1])) * (1 - smoothstep(_seg(t, self.let_go[0], b + 0.8)))
        dx, dy = self.panel_pose(t)
        x0, x1 = MC.BOX[0] + dx, MC.BOX[1] + dx
        yb0, yb1 = MC.fin_y(MC.BOX[0]) + dy, MC.fin_y(MC.BOX[1]) + dy
        yt = MC.BOX_TOP + dy
        return [(-2, (x0 + 200, MC.fin_y(MC.BOX[0] + 200) + dy - 2), on),
                (-1, (x0 + 300, MC.fin_y(MC.BOX[0] + 300) + dy - 2), on),
                (1, (x1 + 4, yt + 60), on), (2, (x1 + 4, yb1 - 40), on)]

    # --- the lantern
    def lamp_lit(self, t):
        a, b = self.lamp
        return smoothstep(_seg(t, a + 0.6 * (b - a), b))

    # --- drawing
    def draw_ramp(self, pg, t, sh):
        """The last ramp's two halves on their legs (in front of the mound's ends), the finish line, the tray."""
        mid0, mid1 = MC.TUNNEL_IN + 30.0, MC.TUNNEL_OUT - 30.0
        for xa, xb in ((MC.FIN0[0], mid0), (mid1, MC.FIN1[0])):
            MC.draw_board_shape(pg, xa - sh, MC.fin_y(xa), xb - sh, MC.fin_y(xb))
            for lx in (xa + 60, xb - 60):
                if MC.MOUND[0] - 40 < lx < MC.MOUND[1] + 40:
                    continue
                pg.shape(rrect(lx - 7 - sh, MC.fin_y(lx) + MC.BOARD_T - 2, lx + 7 - sh, BACK + 8, 3), WOOD3, 0.0)
        MC.draw_tray(pg, sh)
        MC.draw_finish_line(pg, sh)

    def draw_heap(self, pg, t, sh):
        h = self.heap_h(t)
        if t < self.dig[0]:
            return
        x, y = self.heap_x - sh, G + 14.0                         # a little dome of loose soil on the path
        w = 34 + h * 1.5
        p = skia.Path().moveTo(x - w, y)
        p.cubicTo(x - w * 0.55, y - h * 1.15, x + w * 0.55, y - h * 1.15, x + w, y).close()
        pg.shape(p, (146, 112, 80), 0.14)
        pg.flat(oval(x - w * 0.2, y - h * 0.55, w * 0.3, h * 0.18), (164, 128, 92), 0.7)

    def draw_soil(self, pg, t, sh, digs):
        for c in self.clods:
            s = self.clod(c, t, digs)
            if s is not None:
                pg.flat(oval(s[0] - sh, s[1], c[3], c[3] * 0.8), (112, 86, 62))
        for c in self.out_clods:
            s = self.out_clod(c, t)
            if s is not None:
                pg.flat(oval(s[0] - sh, s[1] - c[2] * 0.6, c[2], c[2] * 0.8), (112, 86, 62))

    def draw_lantern(self, pg, t, sh, lit_only=False):
        from .marble_flat_world import lantern
        lit = self.lamp_lit(t)
        if lit_only:
            if lit > 0.01:
                lantern(pg, LANTERN_X - sh, LANTERN_Y, lit, post=BACK - LANTERN_Y + 6, flicker=math.sin(t * 6))
            return
        lantern(pg, LANTERN_X - sh, LANTERN_Y, lit, post=BACK - LANTERN_Y + 6, flicker=math.sin(t * 6))

    def draw_flare(self, pg, t, sh, glo):
        a, b = self.lamp
        if not (a <= t < b + 0.4):
            return
        gx, gy = glo
        u = smoothstep(_seg(t, a, b))
        tx, ty = LANTERN_X, LANTERN_Y - 18
        x = gx + (tx - gx) * u
        y0 = gy - 178 * K
        y = y0 + (ty - y0) * u - 60 * math.sin(math.pi * u)
        fade = 1 - smoothstep(_seg(t, b, b + 0.4))
        pg.glow(x - sh, y, 60, "#ffe7a8", 0.7 * fade)
        pg.flat(oval(x - sh, y, 7, 7), "#fff4d0", fade)

    # --- the checks
    def things(self, t, sh, digs):
        out = {}
        for c in self.clods:
            s = self.clod(c, t, digs)
            if s is None:
                continue
            x, y, st = s
            name = c[0]
            born = "scooped out of the mound by Digs' paw" if t - c[1] < 0.04 else None
            nxt = self.clod(c, t + 1 / 30, digs)
            gone = ("onto the heap", (x - sh, y)) if nxt is None and abs(x - self.heap_x) < 40 + self.heap_h(t) * 1.6                 else (("onto the heap", (self.heap_x - sh, G + 6)) if nxt is None else None)
            if st == "in Digs' paw":
                px, py = self._paw(t, *digs(t))
                out[name] = sc.Thing(x - sh, y, c[3], held=("Digs' right paw", (px - sh, py)), born=born)
            else:
                out[name] = sc.Thing(x - sh, y, c[3], moves="falls", gone=gone)
        for c in self.out_clods:
            s = self.out_clod(c, t)
            if s is not None:
                born = "pushed out of the far mouth" if t - c[1] < 0.04 else None
                out[c[0]] = sc.Thing(s[0] - sh, s[1], c[2], born=born, moves="falls" if s[2] == "falls" else None)
        dx, dy = self.panel_pose(t)
        held = self.grip[1] <= t < self.let_go[0]
        cx, cy = (MC.BOX[0] + MC.BOX[1]) / 2 + dx, (MC.BOX_TOP + MC.fin_y(MC.BOX[1])) / 2 + dy
        out["the peg forest"] = sc.Thing(cx - sh, cy, 190.0, held=("Hans' tentacles", (cx - sh, cy)) if held
                                         else None)
        return out
