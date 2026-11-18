"""The Treetop Marble Run (flat), beat 3a: building the run between the two big trees (docs/engines/
forest_keepers_marble_run_flat.md).

What is there when the Keepers arrive (nothing appears later): the three boards stacked on two sawhorses between the
trees, the rope over the pulley with its hook, six pegs set loosely in the trunks under where the board ends will rest,
the peg-forest panel on two blocks left of TREE_A with its eleven dowels set loosely in it.

- Springs bounces up the branch stubs on TREE_A (real ballistic hops) and taps each loose peg home with his palm,
  hops down, taps the peg-forest dowels home (hopping to reach each one), hops over to TREE_B (passing the others in
  front of them) and does the same there.
- Then one board at a time, top board first (a rising board never passes one already in place): Hans lets the hook
  down, Twigs clips it onto the board's eye, Hans hauls the rope hand over hand with two tentacles (the board rises
  only while a tentacle pulls), lifts it just above its pegs and lets it down: its high end lands on its peg first and
  it tips onto the other. A short tug frees the hook. Glo floats up and sets his little slope level on it: the bubble
  sits in the middle (every board the same gentle slope).
"""
import math

import skia

from families.foundry.keepers.common import smoothstep

from . import marble_flat_course as MC
from . import storycheck as sc
from .marble_flat_world import BACK, G, PULLEY, PULLEY_R, RUN, TREE_A, TREE_B, TRUNK, TRUNK_D, WOOD, WOOD2, WOOD3
from families.foundry.products.monster import TWIGS_FORE, TWIGS_UPPER

from .storybook import mix, oval, rrect, tone

K = 0.72
GJ = 2600.0                          # px/s^2 for Springs' hops
SPRINGS_SH = (100 * K, 170 * K - 10 * K)    # his shoulder from his feet: (out, up)
SPRINGS_L = 47.0 * K
SAW_TOP = BACK - 112.0              # the stack's sawhorses
HANS_HAUL = RUN + 240.0              # where Hans stands to haul
TWIGS_HOOK = RUN - 130.0             # where Twigs stands to clip the hook on
ROPE_X = PULLEY[0] + PULLEY_R       # the hauling side of the rope
GRIP_HI, GRIP_LO = G - 360.0, G - 215.0
GLO_TIPS = 92.0                     # Glo's tendril tips are this far above his y


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def _lin(p, q, u):
    u = min(max(u, 0.0), 1.0)
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


def _ease(p, q, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


# ----------------------------------------------------------------------------------------------- Springs' hops

class Hops:
    """A list of ballistic hops [(t0, (x0, y0), (x1, y1))] (feet positions); between them he stands. state(t) ->
    (x, y, squash) or None when he is not on this schedule."""

    def __init__(self):
        self.hops = []                                            # (t_off, t_land, p0, p1, vy0)
        self.span = None

    def hop(self, t0, p0, p1, extra=36.0):
        apex = min(p0[1], p1[1]) - extra
        up, dn = p0[1] - apex, p1[1] - apex
        t_up, t_dn = math.sqrt(2 * up / GJ), math.sqrt(2 * dn / GJ)
        self.hops.append((t0, t0 + t_up + t_dn, p0, p1, -math.sqrt(2 * GJ * up)))
        self.apex_t = t0 + t_up
        return t0 + t_up + t_dn

    def state(self, t):
        hs = self.hops
        if not hs or t < hs[0][0] - 0.3 or t > hs[-1][1] + 0.3:
            return None
        for i, (a, b, p0, p1, vy) in enumerate(hs):
            if t < a:
                prev = hs[i - 1][3] if i else p0
                sq = 0.45 * math.sin(math.pi * _seg(t, a - 0.25, a))                 # crouch, push off
                land = 0.0 if not i else 0.35 * math.sin(math.pi * _seg(t, hs[i - 1][1], hs[i - 1][1] + 0.22))
                return prev[0], prev[1], max(sq, land)
            if t < b:
                u = t - a
                x = p0[0] + (p1[0] - p0[0]) * u / (b - a)
                return x, p0[1] + vy * u + 0.5 * GJ * u * u, -0.25 * math.sin(math.pi * u / (b - a))
        last = hs[-1]
        return last[3][0], last[3][1], 0.35 * math.sin(math.pi * _seg(t, last[1], last[1] + 0.22))


# ----------------------------------------------------------------------------------------------- the beat

class Build:
    def __init__(self, t0, springs_x):
        self.t0 = t0
        spots = MC.peg_spots()                                    # A bottom to top, then B top to bottom
        self.spots = spots
        self.a_spots, self.b_spots = spots[:3], spots[3:]
        H = self.hops_a = Hops()
        self.taps = []                                            # (name, spot xy, t0, t1, side, stand xy)
        t = t0 + 1.5
        ground = (springs_x, G)
        cur = ground
        # TREE_A: he faces the trunk with his right hand (stands left of each peg)
        for k, side, (px, py) in self.a_spots:
            stand = self.stand_for((px, py), 1)
            t = H.hop(t, cur, stand) + 0.3
            self.taps.append((f"peg A{k}", (px, py), t, t + 1.6, 1, stand))
            t += 1.9
            cur = stand
        for k, side, (px, py) in reversed(self.a_spots[:-1]):     # down again stub by stub
            stand = self.stand_for((px, py), 1)
            t = H.hop(t, cur, stand) + 0.15
            cur = stand
        t = H.hop(t, cur, (springs_x, G)) + 0.4
        # the peg forest: eleven dowels set loosely in the panel on its blocks, tapped home on hops
        self.panel_dx, self.panel_dy = PANEL_DX, PANEL_DY
        cur = (springs_x, G)
        dowels = sorted(MC.pegs(), key=lambda p: (-p[1], p[0]))   # bottom row first, left to right
        self.dowel_taps = []
        for j, (x, y) in enumerate(dowels):
            dx, dy = x + PANEL_DX, y + PANEL_DY
            sx_, sy_ = dx - 18 - SPRINGS_SH[0], dy + 22 + SPRINGS_SH[1]   # feet where his hand meets it at the top
            p1 = (sx_, G)
            t_land = H.hop(t, cur, p1, extra=max(12.0, G - sy_))   # the top of the hop puts his hand on it
            self.dowel_taps.append((j, (dx, dy), H.apex_t, (x, y)))
            t = t_land + 0.25
            cur = p1
        self.dowels_end = t
        self.springs_ground_a = cur
        # over to TREE_B (on the ground: the Plan walks him there), then up its stubs with his left hand
        self.b_go = t + 1.2                                       # a breath; his first step starts after the hops
        self.b_at = self.b_go + abs(B_GROUND - cur[0]) / 170.0 + 1.0
        Hb = self.hops_b = Hops()
        t = self.b_at + 1.6                                       # (his walk over has settled by then)
        cur = (B_GROUND, G)
        order = list(reversed(self.b_spots))                      # bottom stub first, going up
        for k, side, (px, py) in order:
            stand = self.stand_for((px, py), -1)
            t = Hb.hop(t, cur, stand) + 0.3
            self.taps.append((f"peg B{k}", (px, py), t, t + 1.6, -1, stand))
            t += 1.9
            cur = stand
        for k, side, (px, py) in list(reversed(order))[1:]:
            stand = self.stand_for((px, py), -1)
            t = Hb.hop(t, cur, stand) + 0.15
            cur = stand
        t = Hb.hop(t, cur, (B_GROUND, G)) + 0.4
        self.pegs_end = t
        # the boards: top first
        self.boards = []
        t = self.pegs_end + 1.0
        hook_y = self.stack_eye(0) - 90.0                          # the hook waits a little above the stack
        self.hook_keys = [(t0, hook_y)]
        self.haul = []                                            # (t0, t1) of each hand-over-hand stroke
        self.feeds = []
        for k in range(MC.N_BOARDS):
            b = {}
            eye0 = self.stack_eye(k)
            fd = abs(eye0 - hook_y)
            b["feed"] = (t, t + max(0.8, fd / 320.0))
            self.feeds.append(b["feed"])
            self.hook_keys.append((b["feed"][1], eye0 - 24))
            b["clip"] = (b["feed"][1], b["feed"][1] + 1.4)        # Twigs guides the hook onto the eye
            self.hook_keys.append((b["clip"][1], eye0))
            eye1 = self.placed_eye(k) - 50.0                      # lifted just above its pegs (its high end clear)
            rise = eye0 - eye1
            n = max(2, int(math.ceil(rise / 150.0)))
            ts = b["clip"][1] + 0.3
            self.hook_keys.append((ts, eye0))                      # it waits on the eye until the first pull
            strokes = [(ts + i * 0.95, ts + (i + 1) * 0.95) for i in range(n)]
            self.haul += strokes
            b["rise"] = (strokes[0][0], strokes[-1][1])
            b["n"] = n
            for i, (a_, c_) in enumerate(strokes):
                self.hook_keys.append((c_, eye0 - rise * (i + 1) / n))
            b["settle"] = (b["rise"][1] + 0.2, b["rise"][1] + 1.6)
            self.hook_keys.append((b["settle"][1], self.placed_eye(k)))
            b["free"] = (b["settle"][1] + 0.2, b["settle"][1] + 1.1)
            hook_y = self.placed_eye(k) - 36.0
            self.hook_keys.append((b["free"][1], hook_y))
            b["eye0"], b["eye1"] = eye0, eye1
            lx = RUN + 330.0
            b["level"] = (b["free"][1] + 0.2, b["free"][1] + 3.6)     # Glo: up, set it down, the bubble, away
            b["level_x"] = lx
            self.boards.append(b)
            t = b["level"][1] + 0.3
        self.end = t

    # --- Springs
    @staticmethod
    def stand_for(spot, side):
        """Where Springs' feet are so his hand on `side` presses the peg at spot."""
        px, py = spot
        sx = px - side * 24.0
        sy = py + 24.0
        return sx - side * SPRINGS_SH[0], sy + SPRINGS_SH[1]

    def springs_state(self, t):
        for H in (self.hops_a, self.hops_b):
            s = H.state(t)
            if s is not None:
                return s
        return None

    def springs_hand(self, t):
        """{side: world xy} while he taps a peg or a dowel."""
        for name, (px, py), a, b, side, stand in self.taps:
            if a - 0.35 <= t < b + 0.35:
                sh = (stand[0] + side * SPRINGS_SH[0], stand[1] - SPRINGS_SH[1])
                rest = (sh[0] + side * 6, sh[1] + SPRINGS_L)
                if t < a:
                    return {side: _ease(rest, (px, py), _seg(t, a - 0.35, a))}
                if t < b:
                    u = (t - a) / (b - a)
                    back = 12.0 * (0.5 - 0.5 * math.cos(u * 3 * 2 * math.pi))  # three taps (in at 0.25, 0.58, 0.92)
                    return {side: (px - side * back * 0.4, py + back * 0.3)}
                return {side: _ease((px, py), rest, _seg(t, b, b + 0.35))}
        for j, (dx, dy), at, _ in self.dowel_taps:
            if at - 0.3 <= t < at + 0.3:
                return {1: (dx, dy)}
        return None

    def peg_out(self, name, t):
        """How far a loose peg still sticks out (1 loose .. 0.2 home)."""
        for nm, spot, a, b, side, stand in self.taps:
            if nm == name:
                n = sum(1 for q in range(3) if t >= a + (b - a) * (q + 0.25) / 3)    # each tap drives it in
                return 1.0 - 0.8 * n / 3
        return 1.0

    def dowel_out(self, j, t):
        for jj, _, at, _ in self.dowel_taps:
            if jj == j:
                return 1.0 if t < at else 0.2
        return 1.0

    # --- the hoist
    @staticmethod
    def stack_surface(k):
        return SAW_TOP - MC.BOARD_T * (MC.N_BOARDS - k)

    def stack_eye(self, k):
        return self.stack_surface(k) - 10.0

    @staticmethod
    def placed_eye(k):
        return MC.board_mid(k)[1] - 10.0

    def hook_y(self, t):
        keys = self.hook_keys
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, y0), (t1, y1) in zip(keys, keys[1:]):
            if t <= t1:
                # while hauling the hook moves only during a stroke; elsewhere it eases
                u = _seg(t, t0, t1)
                return y0 + (y1 - y0) * smoothstep(u)
        return keys[-1][1]

    def hook_x(self, t):
        x = RUN
        for b in self.boards:
            if b["free"][0] <= t < b["free"][1]:                   # the tug that frees it: out and back
                x += 10 * math.sin(math.pi * _seg(t, *b["free"]))
        return x

    def board_pose(self, k, t):
        """(middle x, surface y at the middle, angle rad, state) of board k."""
        b = self.boards[k]
        if t < b["rise"][0]:
            return RUN, self.stack_surface(k), 0.0, "stack"
        if t < b["settle"][0]:
            return RUN, self.hook_y(t) + 10.0, 0.0, "lifted"
        (x0, y0), (x1, y1), d = MC.board(k)
        ang = MC.board_ang(k)
        if t < b["settle"][1]:
            u = _seg(t, *b["settle"])
            y_hi = min(y0, y1)                                    # the high end comes down onto its peg ...
            lvl0 = b["eye1"] + 10.0
            if u < 0.5:
                return RUN, lvl0 + (y_hi - lvl0) * smoothstep(u / 0.5), 0.0, "settling"
            a = ang * smoothstep((u - 0.5) / 0.5)                  # ... then it tips onto the other
            hx = x1 if d < 0 else x0
            half = MC.BOARD_LEN / 2
            sgn = -1 if d < 0 else 1                               # from the high end to the middle
            cx = hx + sgn * half * math.cos(a)
            cy = y_hi + sgn * half * math.sin(a)
            return cx, cy, a, "settling"
        mx, my = MC.board_mid(k)
        return mx, my, ang, "placed"

    def rope_spin(self, t):
        return (self.hook_y(t) - self.hook_keys[0][1]) / PULLEY_R

    def hans_targets(self, t, x):
        """Hand over hand: two tentacles on the rope's hauling side, the pulling one moving down with the rope."""
        if not (self.boards[0]["feed"][0] - 0.8 <= t <= self.boards[-1]["free"][1] + 0.8):
            return []
        on = smoothstep(_seg(t, self.boards[0]["feed"][0] - 0.8, self.boards[0]["feed"][0])) * \
            (1 - smoothstep(_seg(t, self.boards[-1]["free"][1], self.boards[-1]["free"][1] + 0.8)))
        a_y, b_y, ga, gb = G - 300.0, G - 240.0, 0.7, 0.7          # holding loosely (the rope slides through)
        for i, (s0, s1) in enumerate(self.haul):
            if s0 - 0.05 <= t < s1:
                u = smoothstep(_seg(t, s0, s1))
                pull = GRIP_HI + (GRIP_LO - GRIP_HI) * u           # this one pulls down with the rope
                back = GRIP_LO + (GRIP_HI - GRIP_LO) * u           # the other reaches up for a new grip
                if i % 2 == 0:
                    a_y, b_y, ga, gb = pull, back, 1.0, 0.25
                else:
                    a_y, b_y, ga, gb = back, pull, 0.25, 1.0
                break
        dx_b = 8.0
        return [(-1, (ROPE_X + 2, a_y), on * ga + (1 - on) * 0.001), (-2, (ROPE_X - 2 + dx_b * 0, b_y),
                                                                       on * gb + (1 - on) * 0.001)]

    def twigs_hands(self, t, x):
        """Twigs' right hand takes the hook down onto each board's eye."""
        for b in self.boards:
            a, c = b["clip"]
            if a - 0.9 <= t < c + 0.9:
                # monster.py's elbow changes sides where the hand passes ~68 deg below his shoulder; it only ever
                # does so here with the arm held straight (the elbow then barely moves): from hanging, the arm
                # straightens, swings out straight past that line, then bends in to the hook; back the same way
                shx, shy = x + 82 * K, G - 340 * K
                L = (TWIGS_UPPER + TWIGS_FORE) * K * 1.012                # a hair past his reach: fully straight
                p1 = (shx + L * math.cos(math.radians(73)), shy + L * math.sin(math.radians(73)))
                p2 = (shx + L * math.cos(math.radians(62)), shy + L * math.sin(math.radians(62)))
                eye = (RUN - 4, b["eye0"] - 6)
                hook = (RUN - 4, self.hook_y(min(max(t, a), c)) - 6)
                if t < a:
                    rest = hang_hand(x, a - 0.9)
                    if t < a - 0.6:
                        return {1: _ease(rest, p1, _seg(t, a - 0.9, a - 0.6))}
                    if t < a - 0.35:
                        return {1: _lin(p1, p2, _seg(t, a - 0.6, a - 0.35))}
                    return {1: _ease(p2, (RUN - 4, self.hook_y(a) - 6), _seg(t, a - 0.35, a))}
                if t < c:
                    return {1: hook}
                rest = hang_hand(x, c + 0.9)
                if t < c + 0.35:
                    return {1: _ease(eye, p2, _seg(t, c, c + 0.35))}
                if t < c + 0.6:
                    return {1: _lin(p2, p1, _seg(t, c + 0.35, c + 0.6))}
                return {1: _ease(p1, rest, _seg(t, c + 0.6, c + 0.9))}
        return None

    # --- Glo's level
    def glo_level(self, t):
        """(x, lift above his usual height, level xy or None, bubble ok 0..1) while Glo checks a board."""
        for k, b in enumerate(self.boards):
            a, c = b["level"]
            if a - 1.4 <= t < c + 1.4:
                lx = b["level_x"]
                sy = MC.board_y(k, lx) - 6.0                        # the level sits on the top face
                return k, lx, sy, smoothstep(_seg(t, a + 1.0, a + 1.6)) * (1 - smoothstep(_seg(t, c - 0.6, c)))
        return None

    # --- drawing
    def draw_trees_bits(self, pg, t, sh):
        """On the trunks: the branch stubs Springs hops on, the pegs (loose, then tapped home)."""
        for k, side, (px, py) in self.spots:
            stand = self.stand_for((px, py), 1 if side < 0 else -1)
            sx, sy = stand[0] - sh, stand[1]
            stub = (164, 122, 90)                                # a sawn-off branch stub sticking out toward us
            pg.shape(rrect(sx - 36, sy - 1, sx + 36, sy + 15, 7), stub, 0.14)
            pg.flat(oval(sx + 31, sy + 7, 6, 7.5), (196, 156, 112))
            pg.flat(oval(sx + 31, sy + 7, 3, 3.5), tone(stub, -0.2))
            nm = f"peg {'A' if side < 0 else 'B'}{k}"
            draw_peg(pg, px - sh, py, self.peg_out(nm, t))

    def draw_stack(self, pg, t, sh):
        for lx in (RUN - 420, RUN + 420):                          # the stack's sawhorses
            pg.shape(rrect(lx - 70 - sh, SAW_TOP, lx + 70 - sh, SAW_TOP + 12, 4), WOOD2, 0.1)
            for dx in (-50, 50):
                pg.shape(rrect(lx + dx - 7 - sh, SAW_TOP + 8, lx + dx + 7 - sh, BACK + 8, 3), WOOD3, 0.0)

    def draw_boards(self, pg, t, sh, placed=True):
        """The boards: placed ones (placed=True) or the stack / hoisted one (placed=False)."""
        for k in range(MC.N_BOARDS):
            cx, cy, ang, st = self.board_pose(k, t)
            if (st == "placed") != placed:
                continue
            draw_board(pg, k, cx - sh, cy, ang)
            ex, ey = cx - sh, cy - 10.0                            # the eye on its front edge, at the middle
            if st != "placed" or True:
                pg.stroke(skia.Path().addOval(skia.Rect(ex - 7, ey - 7, ex + 7, ey + 7)), (110, 104, 100), 3.0)

    def draw_rope(self, pg, t, sh, hans_grip):
        """Pulley, rope down to the hook, the hauling side down to Hans' tentacles, the slack in a coil."""
        from .marble_flat_world import pulley
        pulley(pg, sh, self.rope_spin(t))
        px, py = PULLEY[0] - sh, PULLEY[1]
        hx, hy = self.hook_x(t) - sh, self.hook_y(t)
        rope = (196, 160, 104)
        pg.stroke(skia.Path().moveTo(px - PULLEY_R + 2, py).lineTo(hx, hy - 14), rope, 4.0)
        pg.stroke(skia.Path().moveTo(hx, hy - 14).quadTo(hx + 9, hy - 2, hx + 2, hy + 6), (120, 114, 110), 4.0)
        gx, gy = hans_grip
        pg.stroke(skia.Path().moveTo(px + PULLEY_R - 2, py).lineTo(gx - sh, gy), rope, 4.0)
        cx, cy = HANS_HAUL - 110 - sh, G + 8                       # the hauled rope coils on the ground
        p = skia.Path().moveTo(gx - sh, gy).cubicTo(gx - sh + 10, gy + 120, cx + 40, cy - 40, cx, cy)
        pg.stroke(p, rope, 4.0)
        pg.stroke(skia.Path().addOval(skia.Rect(cx - 36, cy - 8, cx + 36, cy + 8)), tone(rope, -0.1), 4.0)

    def draw_level(self, pg, t, sh, glo):
        s = self.glo_level(t)
        if s is None:
            return
        k, lx, sy, ok = s
        b = self.boards[k]
        a, c = b["level"]
        gx, gy = glo
        held = (gx - sh, gy - GLO_TIPS)                           # under his tendrils' tips
        on = (lx - sh, sy - 6)
        u_dn = smoothstep(_seg(t, a, a + 0.9))
        u_up = smoothstep(_seg(t, c - 0.5, c + 0.4))
        x, y = _ease(held, on, u_dn) if u_up <= 0 else _ease(on, held, u_up)
        ang = math.degrees(MC.board_ang(k)) * (u_dn * (1 - u_up))
        c_ = pg.c
        c_.save()
        c_.rotate(ang, x, y)
        pg.shape(rrect(x - 46, y - 9, x + 46, y + 7, 4), (110, 150, 170), 0.1)
        pg.flat(rrect(x - 16, y - 6, x + 16, y + 3, 4), (214, 236, 200))
        bx = x + (1 - ok) * 9
        pg.flat(oval(bx, y - 1.5, 5, 3.4), (250, 252, 240))
        pg.stroke(skia.Path().moveTo(x - 6, y - 7).lineTo(x - 6, y + 4), (90, 110, 90), 1.2)
        pg.stroke(skia.Path().moveTo(x + 6, y - 7).lineTo(x + 6, y + 4), (90, 110, 90), 1.2)
        c_.restore()
        if ok > 0.6:
            pg.glow(x, y - 10, 36, "#fff2c0", 0.4 * ok)

    def draw_panel(self, pg, t, sh, pose=None):
        """The peg forest's panel with its walls and dowels; pose = (dx, dy) offset from its place on TREE_A (on its
        blocks left of the tree until Hans lifts it)."""
        dx, dy = pose if pose is not None else (PANEL_DX, PANEL_DY)
        c = pg.c
        c.save()
        c.translate(dx, dy)
        MC.draw_box_back(pg, sh)
        for L in range(MC.N_LANES - 1, -1, -1):
            pass
        for j, (x, y) in enumerate(sorted(MC.pegs(), key=lambda p: (-p[1], p[0]))):
            MC.draw_dowel(pg, x, y, 0, MC.N_LANES - 1, sh, out=self.dowel_out(j, t))
        MC.draw_box_walls(pg, sh)
        c.restore()
        if pose is None or (dx, dy) == (PANEL_DX, PANEL_DY):
            for bx in (MC.BOX[0] + PANEL_DX + 40, MC.BOX[1] + PANEL_DX - 40):     # its blocks
                pg.shape(rrect(bx - 26 - sh, MC.fin_y(MC.BOX[0]) + PANEL_DY + 2, bx + 26 - sh, BACK + 8, 4), WOOD3,
                         0.1)

    # --- the checks
    def things(self, t, sh, twigs_hand, hans_tip):
        out = {}
        for k in range(MC.N_BOARDS):
            cx, cy, ang, st = self.board_pose(k, t)
            held = None
            if st in ("lifted", "settling"):
                held = ("the hook on the rope", (self.hook_x(t) - sh, self.hook_y(t)))
            out[f"board {k}"] = sc.Thing(cx - sh, cy, MC.BOARD_LEN / 2, held=(held[0], (cx - sh, cy)) if held
                                         else None)
        hx, hy = self.hook_x(t), self.hook_y(t)
        out["the hook"] = sc.Thing(hx - sh, hy, 12.0, held=("the rope Hans hauls", (hx - sh, hy)))
        return out


# the peg-forest panel waits on two blocks left of TREE_A, this far from its place
PANEL_DX = -470.0
PANEL_DY = (BACK - 60.0) - MC.fin_y(MC.BOX[0])      # its bottom on the blocks, 60 above the ground
B_GROUND = TREE_B - 200.0                           # Springs' spot under the boards, left of TREE_B


def draw_peg(pg, x, y, out=0.2):
    """A peg in the trunk seen end on, sticking out toward us by `out` (loose 1 .. home 0.2): a short round dowel."""
    r = 9.0
    L = 22.0 * out
    pg.flat(oval(x + 2, y + 3, r * 1.1, r), (70, 50, 40), 0.25)
    pg.stroke(skia.Path().moveTo(x, y).lineTo(x + L * 0.45, y + L * 0.6), WOOD3, 2 * r)
    pg.shape(oval(x + L * 0.45, y + L * 0.6, r, r), tone(WOOD, 0.02), 0.15)


def draw_board(pg, k, cx, cy, ang):
    """Board k with its middle (front line of its top face) at (cx, cy), tilted ang: the board, its drop slot near
    its low end, a lip at each end."""
    L = MC.BOARD_LEN
    ca, sa = math.cos(ang), math.sin(ang)
    x0, y0 = cx - ca * L / 2, cy - sa * L / 2
    x1, y1 = cx + ca * L / 2, cy + sa * L / 2
    MC.draw_board_shape(pg, x0, y0, x1, y1)
    (bx0, _), (bx1, _), d = MC.board(k)
    h0, h1 = MC.hole(k)
    u0, u1 = (h0 - bx0) / L, (h1 - bx0) / L                       # the slot along the board
    p0 = (x0 + (x1 - x0) * u0, y0 + (y1 - y0) * u0)
    p1 = (x0 + (x1 - x0) * u1, y0 + (y1 - y0) * u1)
    slot = skia.Path().moveTo(*p0).lineTo(*p1).lineTo(p1[0] + MC.FACE_DX, p1[1] - MC.FACE)
    slot.lineTo(p0[0] + MC.FACE_DX, p0[1] - MC.FACE).close()
    pg.flat(slot, (70, 52, 40))
    for (ex, ey) in ((x0, y0), (x1, y1)):                          # the lips
        lp = skia.Path().moveTo(ex - 4, ey).lineTo(ex + 4, ey).lineTo(ex + 4 + MC.FACE_DX, ey - MC.FACE)
        lp.lineTo(ex + 4 + MC.FACE_DX, ey - MC.FACE - MC.LIP_H).lineTo(ex - 4, ey - MC.LIP_H).close()
        pg.flat(lp, WOOD2)


def hang_hand(x, t):
    """Where Twigs' right hand hangs (world xy) when he stands at x, his arms at rest (as monster.py draws it)."""
    from families.foundry.products.monster import ORB, Monster
    from . import illustrate as il

    class _N:
        flat_look, eye_scale, glowing, iris_col = True, 1.15, False, ORB

        def __getattr__(self, k):
            return lambda *a, **kw: None
    m = Monster("teeth", k=K)
    m.x, m.y, m.newlook = x, G, True
    m.hands, m.saws, m.knee_fwd, m.clamp_reach, m.arm_swing, m.attend = True, False, True, True, 0.0, 0.25
    m.draw(_N(), t, il.Glow())
    return m.arm_len[1][2]
