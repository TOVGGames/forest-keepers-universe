"""The Treetop Marble Run (flat), beats 3c-5: the test run, the race, the cheer (docs/engines/
forest_keepers_marble_run_flat.md).

The tray Wheels carried over from the workshop (his plain ball at its right end, the six marbles queued behind it)
waits on the log bench right of TREE_B; a little crate with six grooves, one per lane (the start line in a box), waits
on a stump at the foot of TREE_B. Springs waits on the lowest stub of TREE_B.
- The test run: Wheels takes his plain ball from the tray, rolls over and drops it into the crate's front groove,
  rolls back. Springs hops down, takes the crate in both hands, bounces up the stubs to the starter's perch beside
  the top board's high end and tips the crate: the ball rolls out against the start gate. He lifts the gate with his
  left hand; the ball runs the whole course (pymunk) into the catch tray. Springs brings the crate back down. Wheels
  fetches his ball out of the catch tray.
- The race: Wheels lifts the tray, rolls over and tips it at the crate: the six marbles roll out of it one after
  another into the crate, one per groove. Springs carries it up and tips it: six marbles at the gate, each in its
  lane. 3, 2, 1, the gate: the race runs (every lane its own pymunk space on the same course; nothing steered), the
  whole course on screen, a standings strip.
- The cheer: the winner's Keeper hops for joy, everyone cheers; a rabbit hops over to the catch tray and noses the
  last marble.
"""
import math

import skia

from families.foundry.keepers.common import smoothstep

from . import marble_flat_course as MC
from . import storycheck as sc
from .marble_flat_build import SPRINGS_L, SPRINGS_SH, Hops
from .marble_flat_world import BACK, G, TREE_B, WOOD, WOOD2, WOOD3
from .storybook import oval, rrect, tone

K = 0.72
# the starter's perch: a stub on TREE_B right of the start, where Springs' left hand reaches the start and the gate
# (right of the start, clear of the six marbles waiting there: he lifts the gate by its cord)
PERCH = (MC.LEFT_X[1] + 72.0, MC.board_y(0, MC.START_X) - MC.R0 + SPRINGS_SH[1])
BENCH = (7180.0, 7780.0)            # the log bench right of TREE_B (the crate at its left end, then the tray)
BENCH_Y = BACK - 52.0
CRATE_AT = (BENCH[0] + 80.0, BENCH_Y)      # the crate on the bench (its middle, its floor)
CRATE_W = 150.0
BALL_SPOT = (BENCH[1] - 22.0, 0.0)  # where Wheels sets his ball down after the test run (the bench's end)
SH_RACK_Y = BACK - 24.0             # the tray's floor in the workshop (marble_flat_shop.RACK_Y0)
RACE_SEED = 1                        # picked from 80 seeds for a close race: all six within 0.64 s, 3 lead changes
FRONT_GROOVE = CRATE_AT[0] - CRATE_W / 2 + 30.0


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def _ease(p, q, u):
    u = smoothstep(min(max(u, 0.0), 1.0))
    return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u


class Race:
    def __init__(self, t0, b_stands, tray):
        """b_stands: Springs' feet on TREE_B's stubs, bottom to top; tray: the Tray (slots, pose)."""
        self.t0 = t0
        self.stands = b_stands
        self.tray = tray
        # --- the test run: Wheels' ball into the crate
        t = t0 + 1.0
        self.w_take = (t, t + 1.3)                                # his pincer takes it out of the tray's end slot
        self.w_go = (self.w_take[1], self.w_take[1] + 4.6)        # rolls over to the crate
        self.w_drop = (self.w_go[1], self.w_go[1] + 1.1)
        self.w_back = (self.w_drop[1] + 0.2, self.w_drop[1] + 4.8)
        self.cycles = [self._climb(self.w_back[1] - 1.5, test=True)]
        c = self.cycles[0]
        self.test = MC.Run(MC.Trait(MC.R0, 0.4, 0.06), t_max=40.0)
        self.test_go = c["gate"][1]
        self.test_end = self.test_go + self.test.finish_t + 2.0
        # Wheels fetches the plain ball out of the catch tray (Springs is up on the perch, then comes down)
        self.w_fetch_go = (max(self.test_end + 0.3, c["down"] + 0.3), None)
        self.w_fetch_go = (self.w_fetch_go[0], self.w_fetch_go[0] + 5.6)
        self.w_fetch = (self.w_fetch_go[1], self.w_fetch_go[1] + 1.6)
        self.w_fetch_back = (self.w_fetch[1] + 0.2, self.w_fetch[1] + 5.8)
        # --- the race: Wheels tips the tray on the bench toward the crate
        self.w_pass = (self.w_fetch_back[1] + 0.2, self.w_fetch_back[1] + 1.2)   # his ball onto the bench
        self.t_lift = (self.w_pass[1] + 1.0, self.w_pass[1] + 2.4)
        self.t_tip = (self.t_lift[1], self.t_lift[1] + 4.2)          # the six roll out into the crate
        self.t_set = (self.t_tip[1], self.t_tip[1] + 1.2)
        self.cycles.append(self._climb(self.t_set[1] - 0.6, test=False))
        c = self.cycles[1]
        self.count = [c["gate"][0] - 3.6, c["gate"][0] - 2.4, c["gate"][0] - 1.2]
        self.go = c["gate"][1]
        self.race = MC.Race(RACE_SEED)
        self.finish = [self.go + f for f in self.race.finish]
        self.first = min(self.finish)
        self.last = max(self.finish)
        self.winner = MC.KINDS[self.race.order[0]]
        self.cheer = (self.last + 0.8, self.last + 4.8)
        self.rabbit = (self.last + 2.0, self.last + 10.0)
        self.end = self.rabbit[1] + 1.0

    def _climb(self, t, test):
        """Springs: down from his stub to the crate, up TREE_B's stubs to the perch with it, tips it, the gate; then
        down to the stump with the (empty) crate and back up to his stub."""
        c = {"test": test}
        H = Hops()
        cur = self.stands[0]
        tt = H.hop(t, cur, (CRATE_AT[0], G), extra=20.0) + 0.2
        c["take"] = (tt, tt + 0.9)
        tt = c["take"][1] + 0.3
        cur = (CRATE_AT[0], G)
        for st in self.stands:
            tt = H.hop(tt, cur, st) + 0.25
            cur = st
        tt = H.hop(tt, cur, PERCH) + 0.4
        c["up"] = tt
        c["tip"] = (tt, tt + 1.3)                                 # tips the crate: they roll out to the gate
        c["hold"] = (c["tip"][1], c["tip"][1] + 0.6)              # holds it back up, empty
        c["gate"] = (c["hold"][1] + (5.2 if not test else 1.0), c["hold"][1] + (5.8 if not test else 1.6))
        H2 = Hops()
        tt = c["gate"][1] + (1.6 if test else 2.4)
        cur = PERCH
        for st in reversed(self.stands):
            tt = H2.hop(tt, cur, st) + 0.15
            cur = st
        tt = H2.hop(tt, cur, (CRATE_AT[0], G), extra=20.0) + 0.1
        c["put"] = (tt, tt + 0.8)                                 # the crate back on its stump
        tt = H2.hop(c["put"][1] + 0.2, (CRATE_AT[0], G), self.stands[0]) + 0.2
        c["down"] = tt
        c["hops"], c["hops_down"] = H, H2
        return c

    def springs_state(self, t):
        for c in self.cycles:
            for H in (c["hops"], c["hops_down"]):
                s = H.state(t)
                if s is not None:
                    return s
            if c["hops"].hops[-1][1] <= t < c["hops_down"].hops[0][0]:     # on the perch
                return PERCH[0], PERCH[1], 0.0
        if t >= self.cycles[0]["hops"].hops[0][0] - 0.3:
            return self.stands[0][0], self.stands[0][1], 0.0      # on his stub between the climbs and after
        return None

    def springs_hands(self, t, x, y):
        """{side: world xy}: holding the crate (both), the gate cord (left)."""
        for c in self.cycles:
            if c["take"][0] - 0.5 <= t < c["put"][1]:
                if c["hold"][1] <= t < c["gate"][1] + 0.8:        # the crate rests on the perch beside him
                    if c["gate"][0] - 0.6 <= t:
                        sx_, sy_ = x - SPRINGS_SH[0], y - SPRINGS_SH[1]          # his left shoulder
                        up = smoothstep(_seg(t, *c["gate"]))
                        return {-1: (sx_ - 24, sy_ + 22 - 46 * up)}             # the cord in his hand, pulled up
                    return None
                pose = self.crate_pose(t, x, y)
                if pose is None:
                    return None
                cx, cy, ang = pose
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                return {-1: (cx - ca * CRATE_W / 2 + 4, cy - 26 - sa * CRATE_W / 2),
                        1: (cx + ca * CRATE_W / 2 - 4, cy - 26 + sa * CRATE_W / 2)}
        return None

    def crate_pose(self, t, sx=None, sy=None):
        """(middle x, floor y, tilt deg): on its stump, in Springs' hands, tipped at the start, on the perch."""
        on_perch = (PERCH[0] + 96.0, PERCH[1])
        for c in self.cycles:
            if t < c["take"][0]:
                return CRATE_AT[0], CRATE_AT[1], 0.0
            if t >= c["put"][1]:
                continue
            if c["hold"][1] <= t < c["gate"][1] + 1.2:
                if t < c["hold"][1] + 0.6:
                    p = _ease(self._held(sx, sy), on_perch, _seg(t, c["hold"][1], c["hold"][1] + 0.6)) \
                        if sx is not None else on_perch
                    return p[0], p[1], 0.0
                return on_perch[0], on_perch[1], 0.0
            if sx is None:
                return None
            held = self._held(sx, sy)
            if t < c["take"][1]:
                p = _ease(CRATE_AT, held, _seg(t, *c["take"]))
                return p[0], p[1], 0.0
            if t < c["tip"][0]:
                return held[0], held[1], 0.0
            lip = (PERCH[0] - 30.0, MC.board_y(0, MC.LEFT_X[1]) - 2.0)   # its left end in over the board's end
            if t < c["tip"][1]:
                u = _seg(t, *c["tip"])
                p = _ease(held, lip, min(1.0, u * 2))
                return p[0], p[1], -26.0 * smoothstep(max(0.0, u * 2 - 1))
            if t < c["hold"][1]:
                p = _ease(lip, held, _seg(t, *c["hold"]))
                return p[0], p[1], -26.0 * (1 - smoothstep(_seg(t, *c["hold"])))
            if t < c["put"][0]:                                    # picked up again, carried down
                return held[0], held[1], 0.0
            p = _ease(held, CRATE_AT, _seg(t, *c["put"]))
            return p[0], p[1], 0.0
        return CRATE_AT[0], CRATE_AT[1], 0.0

    @staticmethod
    def _held(sx, sy):
        return sx, sy - 60.0                                      # low in front of him, between his hands

    # --- the marbles
    @staticmethod
    def t_release(c):
        """When the marbles leave the tipped crate (it is well tilted by then)."""
        return c["tip"][0] + 0.85 * (c["tip"][1] - c["tip"][0])

    def _roll_out(self, c, lane, t):
        """(x, y, spin) in lane-0 coords of a marble rolling out of the tipped crate down to the start gate."""
        t_r = self.t_release(c)
        cx, cy, ang = self.crate_pose(t_r, PERCH[0], PERCH[1])
        sx_, sy_ = self.crate_slot(lane, cx, cy)
        a = math.radians(ang)
        rx = cx + (sx_ - cx) * math.cos(a) - (sy_ - cy) * math.sin(a)
        ry = cy + (sx_ - cx) * math.sin(a) + (sy_ - cy) * math.cos(a)
        x0, y0 = rx - lane * MC.LANE_DX, ry + lane * MC.LANE_DY          # lane-0 coords (drawing adds the lane)
        u = smoothstep(_seg(t, t_r, t_r + 0.9))
        x = x0 + (MC.START_X - x0) * u
        y_board = MC.board_y(0, x) - MC.R0
        y = y0 + (y_board - y0) * min(1.0, u * 1.6)
        return x, y, (x0 - x) / MC.R0

    def _tilted_slot(self, lane, pose):
        cx, cy, ang = pose
        sx_, sy_ = self.crate_slot(lane, cx, cy)
        a = math.radians(ang)
        return (cx + (sx_ - cx) * math.cos(a) - (sy_ - cy) * math.sin(a),
                cy + (sx_ - cx) * math.sin(a) + (sy_ - cy) * math.cos(a))

    def crate_slot(self, lane, cx, cy):
        lx, ly, s = MC.lane_xy(cx - CRATE_W / 2 + 30, cy - MC.R0, lane)
        return lx, ly

    def marble(self, i, t):
        """(x, y, spin, state) of race marble i (lane i), None while it rides in the crate (drawn with it)."""
        c1 = self.cycles[1]
        a = self.t_tip[0] + 0.9 + 0.45 * (5 - i)                  # the leftmost goes first
        if t < a:
            x, y = self.tray.slot_xy(i, t)
            return x, y, 0.0, "in the tray"
        base = self.tray.shop.balls[i]["slot"]
        end = self.tray.shop.balls[5]["slot"] - 30.0              # rolled to the tray's left end
        roll = 0.3 + 0.07 * (base - end) / 54.0
        if t < a + roll:                                          # rolls down the tipped tray ...
            u = _seg(t, a, a + roll) ** 2
            x, y = self.tray._xf(base + (end - base) * u, self.tray.shop.balls[0]["c"][1] * 0 + SH_RACK_Y - MC.R0, t)
            return x, y, (base - end) * u / MC.R0 * -1, "rolls"
        if t < a + roll + 0.35:                                   # ... off its end and down into its groove
            u = _seg(t, a + roll, a + roll + 0.35)
            x0, y0 = self.tray._xf(end, SH_RACK_Y - MC.R0, a + roll)
            x1, y1 = self.crate_slot(i, *CRATE_AT[:2])
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u * u, -(base - end + (x0 - x1) * u) / MC.R0, "rolls"
        if t < self.t_release(c1):
            return None
        if t < self.go:
            return self._roll_out(c1, i, t) + ("at the gate",)
        x, y, ang, sp = self.race.runs[i].at(t - self.go)
        return x, y, ang, "races"

    def test_ball(self, t, wheels_hand):
        """(x, y, spin, state) of Wheels' plain ball in these beats (None: in the crate, drawn with it)."""
        c = self.cycles[0]
        if t < self.w_take[0] + 0.6:
            x, y = self.tray.plain_xy(t)
            return x, y, 0.0, "in the tray"
        if t < self.w_drop[0] + 0.6:
            hx, hy = wheels_hand(t)
            return hx, hy + MC.R0 - 2, 0.0, "in Wheels' pincer"
        if t < self.w_drop[1]:
            u = _seg(t, self.w_drop[0] + 0.6, self.w_drop[1])
            x0, y0 = wheels_hand(self.w_drop[0] + 0.6)
            x1, y1 = self.crate_slot(0, *CRATE_AT[:2])
            return x0, y0 + MC.R0 - 2 + (y1 - y0 - MC.R0 + 2) * u * u, 0.0, "falls"
        if t < self.t_release(c):
            return None
        if t < self.test_go:
            return self._roll_out(c, 0, t) + ("at the gate",)
        if t < self.w_fetch[0] + 0.7:
            x, y, ang, _ = self.test.at(t - self.test_go)
            return x, y, ang, "races"
        if t >= self.w_pass[1]:                                   # set down on the bench by the tray's end
            return BALL_SPOT[0], BENCH_Y - MC.R0, 0.0, "on the bench"
        hx, hy = wheels_hand(t, 1)
        return hx, hy + MC.R0 - 2, 0.0, "in Wheels' pincer"

    def gate_up(self, t):
        for c in reversed(self.cycles):
            if t >= c["gate"][0]:
                u = smoothstep(_seg(t, *c["gate"]))
                if c["test"] and t >= self.cycles[1]["up"] - 0.6:
                    return 0.0
                if c["test"] and t >= c["down"]:                   # set down again for the race (on his way back up)
                    return 1.0 - smoothstep(_seg(t, self.cycles[1]["up"] - 1.2, self.cycles[1]["up"] - 0.6))
                return u
        return 0.0

    def standings(self, t):
        if t < self.go:
            return None
        return self.race.standings(t - self.go)

    # --- Wheels
    def wheels_keys(self, home):
        """Wheels' path keys: to the crate and back (his ball), to the catch tray and back."""
        drop_x = FRONT_GROOVE - 72 * K - 30.0
        fetch_x = MC.TRAY[1] - 6 - MC.R0 - 100 * K - 40.0      # the ball 40 px out from his shoulder: a relaxed reach
        return [(self.w_go[0], home), (self.w_go[1], drop_x), (self.w_back[0], drop_x), (self.w_back[1], home),
                (self.w_fetch_go[0], home), (self.w_fetch_go[1], fetch_x), (self.w_fetch_back[0], fetch_x),
                (self.w_fetch_back[1], home)]

    def wheels_hands(self, t, x):
        """{side: world xy} of Wheels' pincers in these beats."""
        rest = (x + 124.4, G - 65.8)
        chest = (x + 112.0, G - 192.0)
        lchest = (x - 112.0, G - 192.0)
        meet = (x + 4, G - 190.0)
        a, b = self.w_take
        if a - 0.6 <= t < self.w_drop[1] + 0.6:
            slot = self.tray.plain_xy(t)
            slot = (slot[0], slot[1] - MC.R0 + 2)
            over = (FRONT_GROOVE, CRATE_AT[1] - 70.0)
            if t < a + 0.6:
                return {1: _ease(rest, slot, _seg(t, a - 0.6, a + 0.6))}
            if t < b:
                return {1: _ease(slot, chest, _seg(t, a + 0.6, b))}
            if t < self.w_drop[0]:
                return {1: chest}
            if t < self.w_drop[0] + 0.6:
                return {1: _ease(chest, over, _seg(t, self.w_drop[0], self.w_drop[0] + 0.6))}
            return {1: _ease(over, rest, _seg(t, self.w_drop[0] + 0.6, self.w_drop[1] + 0.6))}
        a, b = self.w_fetch
        if self.w_fetch_go[1] - 0.6 <= t < self.w_fetch_back[1]:
            tray = (MC.TRAY[1] - 6 - MC.R0, MC.TRAY_Y - 2 * MC.R0 + 2)
            if t < a:
                return {1: _ease(rest, tray, _seg(t, self.w_fetch_go[1] - 0.6, a))}
            if t < a + 0.7:
                return {1: tray}
            return {1: _ease(tray, chest, _seg(t, a + 0.7, b))}
        if t < self.w_fetch_back[1]:
            return None
        # he sets his ball down on the bench beside the tray's end (both pincers are free for the tray)
        p0, p1 = self.w_pass
        spot = (BALL_SPOT[0], BENCH_Y - 2 * MC.R0 + 2)
        if t < p1 + 0.6:
            if t < p0 + 0.6:
                return {1: _ease(chest, spot, _seg(t, p0, p0 + 0.6))}
            if t < p1:
                return {1: spot}
            return {1: _ease(spot, rest, _seg(t, p1, p1 + 0.6))}
        out = {}
        if self.t_lift[0] - 0.6 <= t < self.t_set[1] + 0.6:            # his right pincer lifts the tray's far end
            end = self.tray.end_xy(t)
            u = smoothstep(_seg(t, self.t_lift[0] - 0.6, self.t_lift[0])) * \
                (1 - smoothstep(_seg(t, self.t_set[1], self.t_set[1] + 0.6)))
            out[1] = _ease(rest, end, u)
        return out

    def tray_pose(self, t):
        """(dx, dy, tilt deg) of the tray on the bench: its right end lifted, so it tips toward the crate."""
        if t < self.t_lift[0] or t >= self.t_set[1]:
            return 0.0, 0.0, 0.0
        if t < self.t_lift[1]:
            return 0.0, 0.0, -9.0 * smoothstep(_seg(t, *self.t_lift))
        if t < self.t_tip[1]:
            return 0.0, 0.0, -9.0
        return 0.0, 0.0, -9.0 * (1 - smoothstep(_seg(t, self.t_tip[1], self.t_set[1])))

    # --- drawing
    def draw_bench(self, pg, t, sh):
        x0, x1 = BENCH[0] - sh, BENCH[1] - sh
        for lx in (x0 + 50, x1 - 50):
            pg.shape(rrect(lx - 22, BENCH_Y + 8, lx + 22, BACK + 8, 8), (128, 96, 72), 0.1)
        pg.shape(rrect(x0, BENCH_Y, x1, BENCH_Y + 18, 9), (150, 112, 82), 0.12)

    def draw_crate(self, pg, t, sh, springs):
        sx, sy = springs
        pose = self.crate_pose(t, sx, sy)
        if pose is None:
            return
        cx, cy, ang = pose
        c = pg.c
        c.save()
        c.rotate(ang, cx - sh, cy)
        for lane in range(MC.N_LANES - 1, -1, -1):
            col = self._in_crate(t, lane)
            if col is not None:
                lx, ly = self.crate_slot(lane, cx, cy)
                MC.draw_marble(pg, lx - sh, ly, MC.R0 * (1 - lane * MC.LANE_SC), col)
        pg.shape(rrect(cx - CRATE_W / 2 - sh, cy - 34, cx + CRATE_W / 2 - sh, cy + 6, 5), WOOD, 0.12)
        for gx in (cx - CRATE_W / 2 + 12, cx + CRATE_W / 2 - 12):
            pg.flat(rrect(gx - 3 - sh, cy - 30, gx + 3 - sh, cy + 2, 2), tone(WOOD, -0.14))
        c.restore()

    def _in_crate(self, t, lane):
        c0, c1 = self.cycles
        if lane == 0 and self.w_drop[1] <= t < self.t_release(c0):
            return MC.PLAIN
        if self.marble(lane, t) is None and t < self.t_release(c1):
            return MC.MARBLE_COLS[MC.KINDS[lane]]
        return None

    def draw_gate(self, pg, t, sh, springs_hand):
        """The start gate: a little flap across the lanes, lifted by a cord in Springs' left hand; the perch."""
        up = self.gate_up(t)
        x = MC.GATE_X - sh
        y = MC.board_y(0, MC.GATE_X)
        lift = up * 48.0
        red = (196, 82, 66)                                       # the start gate, painted red with a white stripe
        p = skia.Path().moveTo(x - 7, y - lift).lineTo(x + 7, y - lift).lineTo(x + 7 + MC.FACE_DX, y - lift - MC.FACE)
        p.lineTo(x + 7 + MC.FACE_DX, y - 52 - lift - MC.FACE).lineTo(x - 7, y - 52 - lift).close()
        pg.shape(p, red, 0.1)
        pg.stroke(skia.Path().moveTo(x - 7, y - 26 - lift).lineTo(x + 7 + MC.FACE_DX, y - 26 - lift - MC.FACE),
                  (246, 236, 222), 5.0)
        for gx in (x - 14, x + 14 + MC.FACE_DX):                  # its two little posts
            pg.shape(rrect(gx - 3, y - 70 - (MC.FACE if gx > x else 0), gx + 3, y - (MC.FACE if gx > x else 0), 2),
                     WOOD3, 0.0)
        if springs_hand is not None:
            pg.stroke(skia.Path().moveTo(x, y - 52 - lift).lineTo(springs_hand[0] - sh, springs_hand[1]),
                      (196, 160, 104), 2.5)
        pg.shape(rrect(PERCH[0] - 60 - sh, PERCH[1] - 2, PERCH[0] + 160 - sh, PERCH[1] + 14, 7), (138, 100, 76), 0.1)

    def draw_marbles(self, pg, t, sh, dowels, wheels_hand):
        """The race marbles and the test ball on the course, lane by lane from the back (each lane's dowel slices
        just behind its marble)."""
        for lane in range(MC.N_LANES - 1, -1, -1):
            dowels(lane)
            s = self.marble(lane, t)
            if s is not None and s[3] in ("races", "at the gate"):
                x, y, ang, st = s
                lx, ly, sc_ = MC.lane_xy(x - sh, y, lane)
                MC.draw_marble(pg, lx, ly, MC.R0 * sc_, MC.MARBLE_COLS[MC.KINDS[lane]], ang=ang)
            if lane == 0:
                b = self.test_ball(t, wheels_hand)
                if b is not None and b[3] in ("races", "at the gate"):
                    MC.draw_marble(pg, b[0] - sh, b[1], MC.R0, MC.PLAIN, ang=b[2])

    def draw_loose(self, pg, t, sh, wheels_hand):
        """Marbles off the course: in the tray, rolling into the crate, the plain ball in Wheels' pincer."""
        for i in range(6):
            s = self.marble(i, t)
            if s is not None and s[3] in ("in the tray", "rolls"):
                MC.draw_marble(pg, s[0] - sh, s[1], MC.R0, MC.MARBLE_COLS[MC.KINDS[i]])
        b = self.test_ball(t, wheels_hand)
        if b is not None and b[3] in ("in the tray", "in Wheels' pincer", "falls", "on the bench"):
            MC.draw_marble(pg, b[0] - sh, b[1], MC.R0, MC.PLAIN)

    # --- the checks
    def things(self, t, sh, springs, wheels_hand):
        out = {}
        sx, sy = springs(t)
        pose = self.crate_pose(t, sx, sy)
        for i in range(6):
            s = self.marble(i, t)
            name = f"marble {MC.KINDS[i]}"
            if s is None:
                if pose is not None:
                    lx, ly = self._tilted_slot(i, pose)
                    out[name] = sc.Thing(lx - sh, ly, MC.R0, held=("the crate", (lx - sh, ly)))
                continue
            x, y, ang, st = s
            if st == "races" or st == "at the gate":
                lx, ly, _ = MC.lane_xy(x, y, i)
                hidden = MC.TUNNEL_IN + 10 < x < MC.TUNNEL_OUT - 10 and st == "races"
                out[name] = sc.Thing(lx - sh, ly, MC.R0, moves="rolls", hidden=hidden)
            elif st == "rolls":
                out[name] = sc.Thing(x - sh, y, MC.R0, moves="rolls")
            else:
                out[name] = sc.Thing(x - sh, y, MC.R0, held=("the tray", (x - sh, y)))
        b = self.test_ball(t, wheels_hand)
        name = "Wheels' plain ball"
        if b is None:
            if pose is not None:
                lx, ly = self._tilted_slot(0, pose)
                out[name] = sc.Thing(lx - sh, ly, MC.R0, held=("the crate", (lx - sh, ly)))
        else:
            x, y, ang, st = b
            if st == "in Wheels' pincer":
                out[name] = sc.Thing(x - sh, y, MC.R0, held=("Wheels' pincer", (x - sh, y)))
            elif st in ("races", "at the gate"):
                hidden = MC.TUNNEL_IN + 10 < x < MC.TUNNEL_OUT - 10 and st == "races"
                out[name] = sc.Thing(x - sh, y, MC.R0, moves="rolls", hidden=hidden)
            elif st == "falls":
                out[name] = sc.Thing(x - sh, y, MC.R0, moves="falls")
            else:
                out[name] = sc.Thing(x - sh, y, MC.R0, held=("the tray", (x - sh, y)))
        return out


# ----------------------------------------------------------------------------------------------- the rabbit

RAB_FROM = 8000.0
RAB_Y = G + 26.0                     # just in front of the path line
RAB_S = 1.1


def rabbit_state(race, t):
    """(x, hop height, nose) of the rabbit hopping over to the catch tray after the race (None before)."""
    a, b = race.rabbit
    if t < a:
        return None
    last = race.race.order[-1]                                   # it noses the last marble home
    RAB_TO = MC.TRAY[1] - last * MC.LANE_STOP + 3 * last + 70.0
    n = max(6, int(round((RAB_FROM - RAB_TO) / 90.0)))
    hop_t = 0.5
    d = (RAB_FROM - RAB_TO) / n
    u = t - a
    if u < n * hop_t:
        i = int(u / hop_t)
        f = (u - i * hop_t) / hop_t
        x = RAB_FROM - d * (i + smoothstep(f))
        return x, 26.0 * math.sin(math.pi * f), 0.0
    nose = 0.5 + 0.5 * math.sin((u - n * hop_t) * 9.0)           # it sniffs the last marble
    return RAB_TO, 0.0, nose


def draw_rabbit(pg, race, t, sh):
    from .christmas_night import rabbit
    s = rabbit_state(race, t)
    if s is None:
        return
    x, hop, nose = s
    pg.shadow(x - sh, RAB_Y + 2, 40 * RAB_S, 8, 0.2)
    rabbit(pg, x - sh, RAB_Y, RAB_S, face=-1, hop=hop + 2.0 * nose)


def rabbit_thing(race, t, sh):
    s = rabbit_state(race, t)
    if s is None:
        return {}
    born = "hops in from the meadow" if t - race.rabbit[0] < 0.04 else None
    return {"a rabbit": sc.Thing(s[0] - sh, RAB_Y - 40 * RAB_S - s[1], 40 * RAB_S, moves="walks", born=born)}
