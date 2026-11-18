"""Forest Keepers episode 6: the treetop marble run - the course, the marble physics and the drawing of both
(docs/engines/forest_keepers_marble_run.md).

The run hangs between two big old trees right of the village (TREE_A left, TREE_B right): five wide boards zigzag
down between the trunks (every board the same length and slope, resting on pegs in the trunks), a stop at every
turn, then a peg forest on the front of TREE_A, then the long last ramp left through the tunnel in the mound,
over the finish line and into the catch tray by the bunny's house.

The boards are wide: the six marbles race side by side, one lane each (lane 0 is nearest us). That is how real
marble races are run, and it lets a faster marble pass. Physics (pymunk, 480 Hz): each marble is a solid wooden
ball (moment 2/5 m r^2) that rolls on the wood with friction; the marbles differ a little, as real hand-made
wooden balls do (size, bounce, rolling resistance), and those differences decide the race. Lanes don't touch, so
each marble is simulated in its own space on the same course. The race is fully simulated before rendering.
"""
import math

import numpy as np
import pymunk

from families.foundry.keepers.common import GRAVITY, PLANK, ellipse, lerp, rect, seg, smoothstep
from families.foundry.products.monster import Xform
from families.foundry.style import IRON, lighten
from families.foundry.tree_monsters import BARK, LAMP, LEAF, TRUNK

G = 1000.0
TREE_A, TREE_B = 5100.0, 6700.0
N_BOARDS = 5
Y_TOP0 = G - 1600.0          # high end of the top board
LEVEL_GAP = 200.0
DROP = 90.0                  # every board falls 90 over its 1500: the same slope
BOARD_LEN = 1500.0
LEFT_X = (5205.0, 6705.0)    # boards the marbles roll left on (0, 2, 4)
RIGHT_X = (5110.0, 6610.0)   # boards they roll right on (1, 3)
STOP_A, STOP_B = 5135.0, 6680.0
BOARD_T = 18.0               # board thickness (we see its front edge)
SEG_R = 3.0                  # collision radius of the board surface
N_LANES = 6
LANE_DY = 13.5               # each lane further back sits this much higher on screen ...
LANE_SC = 0.03               # ... and this much smaller
LANE_DX = 7.0                # ... and a little to the right (we look at the run from a little to the left and above)
FACE = LANE_DY * N_LANES + 8.0   # depth of a board's top face as drawn (up on screen ...
FACE_DX = FACE * LANE_DX / LANE_DY   # ... and to the right)
BOX = (4960.0, 5280.0)       # the peg forest on the front of TREE_A (walls)
BOX_TOP = G - 690.0
PEG_R = 7.0
FIN0 = (5280.0, G - 320.0)   # the last ramp: from the floor of the peg box ...
FIN1 = (3950.0, G - 110.0)   # ... to the catch tray
TRAY = (3680.0, 3950.0)
TRAY_Y = G - 110.0
FINISH_X = 3995.0
MOUND = (4300.0, 4920.0, G - 440.0)      # the mound the tunnel goes through: x0, x1, top
GATE_X = 6648.0
START_X = 6672.0             # marbles wait here behind the gate
PULLEY = (5930.0, G - 1790.0)  # Hans' hoist pulley on the branch between the trees
R0 = 21.0                    # marble radius

# the six marbles, one per Keeper, in their colours
KINDS = ["wheels", "tentacles", "teeth", "springs", "lantern", "digger"]
MARBLE_COLS = {"wheels": (64, 120, 222), "tentacles": (232, 122, 44), "teeth": (150, 84, 214),
               "springs": (230, 184, 46), "lantern": (40, 190, 176), "digger": (210, 76, 60)}
NAMES = {"wheels": "Wheels", "tentacles": "Hans", "teeth": "Twigs", "springs": "Springs", "lantern": "Glo",
         "digger": "Digs"}
PLAIN = np.array([196, 164, 120], np.float64)     # Wheels' plain wooden ball from the start of the episode


# ====================================================================== course geometry

def board(k):
    """Board k (0 = top): ((x_left, y_left), (x_right, y_right)) of its top surface; dir -1 = marbles roll left."""
    hi = Y_TOP0 + LEVEL_GAP * k
    if k % 2 == 0:
        return (LEFT_X[0], hi + DROP), (LEFT_X[1], hi), -1
    return (RIGHT_X[0], hi), (RIGHT_X[1], hi + DROP), 1


def board_y(k, x):
    (x0, y0), (x1, y1), _ = board(k)
    return lerp(y0, y1, (x - x0) / (x1 - x0))


def board_ang(k):
    (x0, y0), (x1, y1), _ = board(k)
    return math.atan2(y1 - y0, x1 - x0)


def fin_y(x):
    """Surface of the last ramp (and the tray) at x."""
    if x <= FIN1[0]:
        return TRAY_Y
    return lerp(FIN1[1], FIN0[1], (x - FIN1[0]) / (FIN0[0] - FIN1[0]))


FIN_ANG = math.atan2(FIN0[1] - FIN1[1], FIN0[0] - FIN1[0])


def stops():
    """The stop at every turn: (x, y_top, y_bottom). A stop for board k's low end."""
    out = []
    for k in range(N_BOARDS - 1):
        (xl, yl), (xr, yr), d = board(k)
        if d < 0:
            out.append((STOP_A, yl - 80, yl + 30))
        else:
            out.append((STOP_B, yr - 80, yr + 30))
    return out


PEG_ROWS = [G - 630.0 + 60.0 * i for i in range(5)]
PEG_STEP = 66.0


def pegs():
    """The peg forest: evenly spaced rows, every other row offset by half a step (a triangular grid). Every gap
    (peg to peg, peg to wall) is wider than any marble, so none can wedge."""
    out = []
    x0 = BOX[0] + SEG_R + 52.0 + PEG_R
    for i, y in enumerate(PEG_ROWS):
        xs = [x0 + PEG_STEP * j for j in range(4)] if i % 2 == 0 else [x0 + PEG_STEP * (j + 0.5) for j in range(3)]
        out += [(x, y) for x in xs]
    return out


def deflectors():
    """Half pegs: on the offset rows a short slanted strip on each wall turns a marble running down the wall back
    into the pegs (as on a real peg board) -> [((x0, y0), (x1, y1))]."""
    out = []
    for i, y in enumerate(PEG_ROWS):
        if i % 2 == 1:
            out.append(((BOX[0] + SEG_R, y - 22), (BOX[0] + 30, y + 6)))
            out.append(((BOX[1] - SEG_R, y - 22), (BOX[1] - 30, y + 6)))
    return out


def box_walls():
    """(x, y_top, y_bottom) of the peg forest's two side walls; the left one stops short so marbles get out."""
    return [(BOX[0], BOX_TOP, G - 340.0), (BOX[1], BOX_TOP, fin_y(BOX[1]))]


def peg_spots():
    """Where Springs drives the trunk pegs: under each board end that rests on a trunk (x, y)."""
    out = []
    for k in range(N_BOARDS):
        (xl, yl), (xr, yr), d = board(k)
        out.append((xl + 40, yl + BOARD_T + 6))
        out.append((xr - 40, yr + BOARD_T + 6))
    return out


def course_checks():
    """Owner rule: things line up. Every board the same length and slope, pegs evenly spaced."""
    lens, slopes = [], []
    for k in range(N_BOARDS):
        (x0, y0), (x1, y1), _ = board(k)
        lens.append(x1 - x0)
        slopes.append(abs(y1 - y0) / (x1 - x0))
    ps = pegs()
    gaps = [ps[i + 1][0] - ps[i][0] for i in range(3)]
    return {"boards": N_BOARDS, "boards_even": max(lens) - min(lens) < 0.5,
            "slopes_even": max(slopes) - min(slopes) < 1e-6, "slope_deg": round(math.degrees(math.atan(slopes[0])), 2),
            "pegs": len(ps), "pegs_even": max(gaps) - min(gaps) < 0.5}


# ====================================================================== physics

class Trait:
    """How one hand-made wooden ball differs from the others (small, realistic)."""

    def __init__(self, r, bounce, roll):
        self.r, self.bounce, self.roll = r, bounce, roll


def traits(seed):
    rng = np.random.default_rng(seed)
    return [Trait(R0 * rng.uniform(0.96, 1.04), rng.uniform(0.25, 0.55), rng.uniform(0.02, 0.11))
            for _ in range(N_LANES)]


PHYS_HZ = 480
REC_HZ = 120


class Run:
    """One marble down the course in its own space (lanes don't touch). Recorded at REC_HZ:
    x, y, angle, speed, on (touching something); events: (t, kind, x, y, impulse)."""

    def __init__(self, trait, t_max=60.0, start=(START_X, None), boards=N_BOARDS, v0=(0.0, 0.0)):
        self.trait = tr = trait
        sp = pymunk.Space()
        sp.gravity = (0.0, GRAVITY)
        sp.iterations = 30
        st = sp.static_body
        shapes = []

        def segment(a, b, e, f=0.9, kind="wood"):
            s = pymunk.Segment(st, a, b, SEG_R)
            s.elasticity, s.friction = e, f
            s.kind = kind
            shapes.append(s)

        for k in range(boards):
            (x0, y0), (x1, y1), d = board(k)
            segment((x0, y0 + SEG_R), (x1, y1 + SEG_R), 0.5)
            hx, hy = (x1, y1) if d < 0 else (x0, y0)         # a lip at the high end
            segment((hx, hy + SEG_R), (hx, hy - 40), 0.4)
        for x, y0, y1 in stops():
            segment((x, y0), (x, y1), 0.45, kind="stop")
        for x, y0, y1 in box_walls():
            segment((x, y0), (x, y1), 0.45, kind="stop")
        for a, b_ in deflectors():
            segment(a, b_, 0.6, kind="peg")
        for x, y in pegs():
            c = pymunk.Circle(st, PEG_R, (x, y))
            c.elasticity, c.friction = 0.8, 0.6
            c.kind = "peg"
            shapes.append(c)
        segment((FIN0[0], FIN0[1] + SEG_R), (FIN1[0], FIN1[1] + SEG_R), 0.5)
        segment((FIN1[0], FIN1[1] + SEG_R), (TRAY[0], TRAY_Y + SEG_R), 0.4)
        segment((TRAY[0], TRAY_Y + SEG_R), (TRAY[0], TRAY_Y - 60), 0.15, kind="stop")
        sp.add(*shapes)

        b = pymunk.Body(1.0, 0.4 * tr.r * tr.r)
        sx = start[0]
        sy = start[1] if start[1] is not None else board_y(0, sx) - tr.r
        b.position = (sx, sy)
        b.velocity = v0
        b.velocity_func = self._roll
        c = pymunk.Circle(b, tr.r)
        c.elasticity, c.friction = tr.bounce, 0.9
        sp.add(b, c)
        self.body, self.space = b, sp
        self.events = []
        self.touch = 0
        self.t = 0.0
        h = sp.on_collision(None, None, begin=self._begin, separate=self._sep, post_solve=self._post)
        rec = []
        n_sub = PHYS_HZ // REC_HZ
        self.finish_t = None
        i = 0
        while self.t < t_max:
            for _ in range(n_sub):
                sp.step(1.0 / PHYS_HZ)
                self.t += 1.0 / PHYS_HZ
            p, v = b.position, b.velocity
            rec.append((p.x, p.y, b.angle, v.length, self.touch > 0))
            if self.finish_t is None and p.x < FINISH_X:
                self.finish_t = self.t
            i += 1
            if self.finish_t is not None and self.t > self.finish_t + 6.0 and v.length < 3.0:
                break
        self.rec = np.array([(r[0], r[1], r[2], r[3], 1.0 if r[4] else 0.0) for r in rec])
        self.dur = len(rec) / REC_HZ

    def _roll(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        if self.touch > 0:                      # rolling resistance while it rolls on the wood
            k = max(0.0, 1.0 - self.trait.roll * dt)
            body.velocity = body.velocity * k
            body.angular_velocity *= k
        v = body.velocity.length
        if v > 3000:
            body.velocity = body.velocity * (3000 / v)

    def _begin(self, arb, space, data):
        self.touch += 1
        return True

    def _sep(self, arb, space, data):
        self.touch = max(0, self.touch - 1)

    def _post(self, arb, space, data):
        if not arb.is_first_contact:
            return
        imp = arb.total_impulse.length
        if imp < 25:
            return
        other = [s for s in arb.shapes if s.body is not self.body][0]
        p = self.body.position
        self.events.append((self.t, getattr(other, "kind", "wood"), p.x, p.y, imp))

    def at(self, tau):
        """(x, y, angle, speed, on) tau seconds after the release (holds at the ends)."""
        f = tau * REC_HZ - 1.0
        if f <= 0:
            r = self.rec[0]
            return float(r[0]), float(r[1]), float(r[2]), 0.0, True
        i = int(f)
        if i >= len(self.rec) - 1:
            r = self.rec[-1]
            return float(r[0]), float(r[1]), float(r[2]), float(r[3]), True
        u = f - i
        a, b = self.rec[i], self.rec[i + 1]
        return (float(lerp(a[0], b[0], u)), float(lerp(a[1], b[1], u)), float(lerp(a[2], b[2], u)),
                float(lerp(a[3], b[3], u)), bool(a[4] > 0.5))

    def progress(self, tau):
        """How far along the course (for the standings): distance travelled down the zigzag."""
        x, y, _, _, _ = self.at(tau)
        return course_progress(x, y)


def course_progress(x, y):
    """A number that grows monotonically along the course (board by board), for the race order."""
    best = None
    for k in range(N_BOARDS):
        (x0, y0), (x1, y1), d = board(k)
        if y < min(y0, y1) - 60 or y > max(y0, y1) + 40 or not (x0 - 60 <= x <= x1 + 60):
            continue
        u = (x - x0) / (x1 - x0)
        along = (1 - u) if d < 0 else u
        val = k * 1.0 + max(0.0, min(1.0, along))
        best = val if best is None else max(best, val)
    if best is not None and y < BOX_TOP - 30:
        return best
    if y < G - 420 and BOX[0] - 10 <= x <= BOX[1] + 10:          # in the peg forest
        return N_BOARDS + seg(y, BOX_TOP - 30, G - 420) * 0.99
    if best is not None:
        return best
    return N_BOARDS + 1.0 + seg(-x, -FIN0[0], -TRAY[0]) * 1.5


class Race:
    """The six marbles, released together. finish order, lead changes, per-frame order."""

    def __init__(self, seed, t_max=70.0):
        self.seed = seed
        self.traits = traits(seed)
        self.runs = [Run(tr, t_max) for tr in self.traits]
        self.finish = [r.finish_t if r.finish_t is not None else 999.0 for r in self.runs]
        self.order = sorted(range(N_LANES), key=lambda i: self.finish[i])
        self.dur = max(r.dur for r in self.runs)
        # the leader as a viewer sees it: a marble takes the lead only when it is clearly ahead (half a marble
        # along the board), so two marbles side by side don't flicker it back and forth
        # (and stays ahead for half a second: at the turns, where they bunch up at the stop, the lead would flicker)
        self.leaders = []
        self.changes = 0
        last, cand, since = None, None, 0.0
        for f in range(int(min(self.finish) * 30) + 1):
            tau = f / 30.0
            prog = [r.progress(tau) for r in self.runs]
            best = max(range(N_LANES), key=lambda i: prog[i])
            if last is None:
                last = best
                self.leaders.append((0.0, best))
                continue
            if best != last and prog[best] > prog[last] + 0.015:
                if best != cand:
                    cand, since = best, tau
                if tau - since >= 0.5:
                    self.changes += 1
                    self.leaders.append((round(tau, 2), best))
                    last, cand = best, None
            else:
                cand = None
        if self.leaders[-1][1] != self.order[0]:       # photo finish: the winner takes it on the line
            self.leaders.append((round(min(self.finish), 2), self.order[0]))
            self.changes += 1
        self.spread = self.finish[self.order[-1]] - self.finish[self.order[0]]
        self.gap12 = self.finish[self.order[1]] - self.finish[self.order[0]]

    def standings(self, tau):
        """Lane indices in race order at tau (finished ones by finish time)."""
        def key(i):
            if self.finish[i] <= tau:
                return (0, self.finish[i])
            return (1, -self.runs[i].progress(tau))
        return sorted(range(N_LANES), key=key)

    def leader(self, tau):
        """The leader as shown (with the hysteresis above)."""
        ld = self.leaders[0][1]
        for t0, i in self.leaders:
            if t0 <= tau:
                ld = i
        return ld


# ====================================================================== drawing

WOOD = PLANK * 1.04
WOOD_FACE = lighten(PLANK, 1.16)
WOOD_EDGE = PLANK * 0.7
GROOVE = PLANK * 0.86
DOWEL = np.array([206, 176, 128], np.float64)
EARTH = np.array([70, 52, 38], np.float64)
MOSS = np.array([62, 96, 58], np.float64)
TUNNEL = np.array([16, 13, 12], np.float64)
STONE = np.array([96, 90, 84], np.float64)
ROPE = np.array([176, 150, 104], np.float64)
BIG_TREE_TOP = G - 1980.0
# a long branch from TREE_B over the run, Hans' hoist pulley hangs from it
BRANCH = ((TREE_B - 60.0, G - 1730.0), (5560.0, G - 1900.0))


def branch_y(x):
    (x0, y0), (x1, y1) = BRANCH
    return lerp(y0, y1, (x - x0) / (x1 - x0))


PULLEY = (5930.0, branch_y(5930.0) + 70.0)


def trunk_half(x, y):
    """Half width of a big trunk at height y (wide roots, tapering up)."""
    u = (G - y) / (G - BIG_TREE_TOP)
    return 125 - 45 * u + 60 * max(0.0, 1 - u * 9) ** 2


def draw_big_tree(c, s, x, seed, crown=True):
    """One of the two big old trees: a broad trunk with root flares and bark, a crown above the run."""
    rs = np.random.default_rng(seed)
    ys = np.linspace(G + 6, BIG_TREE_TOP, 24)
    left = [(x - trunk_half(x, y) + 6 * math.sin(y * 0.004 + seed), y) for y in ys]
    right = [(x + trunk_half(x, y) + 6 * math.sin(y * 0.005 + seed * 2), y) for y in ys]
    c.polygon(left + right[::-1], TRUNK)
    c.polygon([(x - 40, G + 6)] + right[:4] + [(x + 40, G + 6)], TRUNK * 1.06)
    for k in range(7):                                    # bark furrows
        bx = x + rs.uniform(-0.7, 0.7) * 90
        y0 = rs.uniform(G - 300, G - 100)
        c.polyline([(bx + 8 * math.sin(yy * 0.01 + k), yy) for yy in np.linspace(y0, y0 - rs.uniform(500, 1300), 14)],
                   BARK, 3 + k % 2)
    if not crown:
        return
    for k in range(13):
        cx = x + rs.uniform(-620, 620)
        cy = BIG_TREE_TOP - rs.uniform(-160, 260) + 0.00025 * (cx - x) ** 2
        c.circle(cx, cy, rs.uniform(190, 290), LEAF[k % 3] * 0.8)


def draw_trees(c, s, t):
    """Both big trees and the hoist branch, behind everything on the run."""
    for j, x in enumerate((TREE_A, TREE_B)):
        if s.visible(x - 900, x + 900):
            draw_big_tree(c, s, x, 61 + j)
    (x0, y0), (x1, y1) = BRANCH
    c.line(x0, y0, x1, y1, TRUNK, 34)
    c.line(lerp(x0, x1, 0.6), lerp(y0, y1, 0.6), x1 - 80, y1 - 90, TRUNK, 20)
    c.line(x0, y0 + 6, x1, y1 + 6, BARK, 3)


def draw_trunk_pegs(c, n):
    """The first n trunk pegs Springs has driven (bottom board first)."""
    spots = peg_order()
    for i in range(min(n, len(spots))):
        x, y = spots[i]
        c.line(x, y - 4, x, y + 4, DOWEL * 0.7, 16)
        c.circle(x, y, 8, DOWEL)
        c.circle(x - 2, y - 2, 3, lighten(DOWEL, 1.2))


def peg_order():
    """Trunk pegs in the order Springs drives them: bottom board first, its A end then its B end."""
    spots = peg_spots()
    order = []
    for k in reversed(range(N_BOARDS)):
        order += [spots[2 * k], spots[2 * k + 1]]
    return order


def back(x, y, d=FACE):
    """The point d further back (into the picture) from (x, y): up and a little to the right."""
    return x + d * LANE_DX / LANE_DY, y - d


def _face(c, a, b, depth, col, grooves=True):
    """Top face of a wide board between front surface points a, b (we look at it a little from above)."""
    (x0, y0), (x1, y1) = a, b
    b0, b1 = back(x0, y0, depth), back(x1, y1, depth)
    c.polygon([(x0, y0), (x1, y1), b1, b0], col)
    c.line(b0[0], b0[1], b1[0], b1[1], col * 0.8, 3)
    if grooves:
        for j in range(N_LANES):
            dx, dy, _ = lane_off(j)
            c.line(x0 + 4 + dx, y0 + dy - 3, x1 - 4 + dx, y1 + dy - 3, GROOVE, 2)


def _edge(c, a, b, col=WOOD, lip=6.0):
    """Front edge of a board below the surface line, and the lip along the front that the near lane rolls in."""
    (x0, y0), (x1, y1) = a, b
    c.polygon([(x0, y0), (x1, y1), (x1, y1 + BOARD_T), (x0, y0 + BOARD_T)], col)
    c.line(x0, y0 + BOARD_T, x1, y1 + BOARD_T, WOOD_EDGE, 3)
    c.polygon([(x0, y0 - lip), (x1, y1 - lip), (x1, y1 + 1), (x0, y0 + 1)], lighten(col, 1.1))
    for e in (x0, x1):                                   # end grain
        ye = y0 if e == x0 else y1
        c.line(e, ye - lip, e, ye + BOARD_T, WOOD_EDGE, 3)


def board_pts(k, dx=0.0, dy=0.0, ang=0.0):
    """Board k's surface end points, moved by (dx, dy) and turned by ang about its middle (for the hoist)."""
    (x0, y0), (x1, y1), _ = board(k)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = []
    for x, y in ((x0, y0), (x1, y1)):
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = x - cx, y - cy
        out.append((cx + px * ca - py * sa + dx, cy + px * sa + py * ca + dy))
    return out


def draw_board_back(c, k, dx=0.0, dy=0.0, ang=0.0):
    a, b = board_pts(k, dx, dy, ang)
    _face(c, a, b, FACE, WOOD_FACE)
    (x0, y0), (x1, y1), d = board(k)
    hx, hy = (b if d < 0 else a)                          # the lip at the high end
    c.polygon([(hx - 7, hy - 40), (hx + 7, hy - 40), back(hx + 7, hy - 40), back(hx - 7, hy - 40)], WOOD * 0.9)


def draw_board_front(c, k, dx=0.0, dy=0.0, ang=0.0):
    a, b = board_pts(k, dx, dy, ang)
    _edge(c, a, b)
    (x0, y0), (x1, y1), d = board(k)
    hx, hy = (b if d < 0 else a)
    rect(c, hx - 7, hy - 40, hx + 7, hy + 2, WOOD * 1.05)


def draw_stop(c, x, y0, y1, part="back"):
    """A stop at a turn: a short upright board across all the lanes."""
    if part == "back":
        c.polygon([(x - 8, y0), (x + 8, y0), back(x + 8, y0), back(x - 8, y0)], WOOD_FACE * 0.95)
        return
    rect(c, x - 8, y0, x + 8, y1, WOOD)
    c.line(x - 8, y0, x - 8, y1, WOOD_EDGE, 2)


def draw_pegbox_back(c, n_pegs=99, walls=1.0, dy=0.0):
    """The back panel of the peg forest, mounted on the front of TREE_A, and its pegs (dowel ends);
    dy: lower by this much (it is built standing on the ground, then lifted into place)."""
    if dy:
        c = Xform(c, 0.0, dy)
    floor_l, floor_r = fin_y(BOX[0]), fin_y(BOX[1])
    p0, p1 = back(BOX[0], BOX_TOP), back(BOX[1], floor_r)
    rect(c, p0[0], p0[1], p1[0], p1[1] + FACE * 0.5, PLANK * 0.62)
    for q in range(1, 5):
        xx = lerp(p0[0], p1[0], q / 5)
        c.line(xx, p0[1], xx, p1[1] + FACE * 0.5, PLANK * 0.52, 2)
    ps = pegs()
    for i, (x, y) in enumerate(ps[:n_pegs]):
        bx, by = back(x, y)
        c.line(x, y, bx, by, DOWEL * 0.66, PEG_R * 1.3)
        c.circle(bx, by, PEG_R, DOWEL * 0.8)
    if walls > 0:
        for (a, b) in deflectors():
            c.polygon([a, b, back(*b), back(*a)], WOOD_FACE * 0.9)


def draw_pegbox_front(c, n_pegs=99, walls=1.0, dy=0.0):
    if dy:
        c = Xform(c, 0.0, dy)
    ps = pegs()
    for i, (x, y) in enumerate(ps[:n_pegs]):           # the near ends of the dowels
        c.circle(x, y, PEG_R, DOWEL)
        c.circle(x - 1.5, y - 1.5, PEG_R * 0.4, lighten(DOWEL, 1.2))
    if walls <= 0:
        return
    for x, y0, y1 in box_walls():
        rect(c, x - 7, y0 - 6, x + 7, y1, WOOD)
        c.line(x + (7 if x < 5100 else -7), y0 - 6, x + (7 if x < 5100 else -7), y1, WOOD_EDGE, 2)
    for (a, b) in deflectors():
        c.line(a[0], a[1], b[0], b[1], WOOD, 8)


def draw_final_back(c, built=1.0, tray=True):
    """The last ramp from the peg forest to the tray (built: how much of it is down, from the top end) and the
    catch tray at its end."""
    if built > 0:
        x_end = lerp(FIN0[0], FIN1[0], built)
        _face(c, FIN0, (x_end, fin_y(x_end)), FACE, WOOD_FACE)
    if tray:
        _face(c, FIN1, (TRAY[0], TRAY_Y), FACE, WOOD_FACE, grooves=True)
        c.polygon([(TRAY[0] - 8, TRAY_Y - 60), (TRAY[0] + 8, TRAY_Y - 60), back(TRAY[0] + 8, TRAY_Y - 60),
                   back(TRAY[0] - 8, TRAY_Y - 60)], WOOD * 0.9)


def final_posts():
    return [4950.0, 4120.0]


def draw_final_front(c, built=1.0, tray=True):
    if built > 0:
        x_end = lerp(FIN0[0], FIN1[0], built)
        for px in final_posts():                          # legs to the ground
            if px >= x_end - 10:
                y = fin_y(px) + BOARD_T
                rect(c, px - 9, y, px + 9, G + 4, TRUNK * 0.95)
        _edge(c, FIN0, (x_end, fin_y(x_end)))
    if tray:
        _edge(c, FIN1, (TRAY[0], TRAY_Y), lip=10.0)
        rect(c, TRAY[0] - 8, TRAY_Y - 60, TRAY[0] + 8, TRAY_Y + BOARD_T, WOOD * 0.95)


def mound_y(x):
    """Top of the mound at x (ground outside it)."""
    x0, x1, top = MOUND
    if not (x0 < x < x1):
        return G
    u = (x - x0) / (x1 - x0)
    return G - (G - top) * math.sin(math.pi * u) ** 0.75


def tunnel_span():
    """x of the right (in) and left (out) portal: where the mound covers the track by a marble and more."""
    xs = np.linspace(MOUND[1] - 5, MOUND[0] + 5, 400)
    inside = [x for x in xs if mound_y(x) < fin_y(x) - 2 * R0 - 30]
    return max(inside), min(inside)


def draw_mound(c, s, part, dug=1.0):
    """The mound. part "back": the whole mound and, once dug, the dark tunnel behind the track;
    "cover": the mound in front of the track between the portals (hides the marbles in the tunnel) + portals."""
    x0, x1, top = MOUND
    xs = np.linspace(x0, x1, 48)
    pts = [(x, mound_y(x)) for x in xs]
    xin, xout = tunnel_span()
    if part == "back":
        c.polygon(pts + [(x1, G + 4), (x0, G + 4)], EARTH)
        c.polyline(pts, MOSS, 10)
        return
    if dug <= 0:
        return
    # the cover: the mound between the portals, in front of the track
    cov = [(x, mound_y(x)) for x in np.linspace(xout, xin, 40)]
    c.polygon(cov + [(xin, G + 4), (xout, G + 4)], EARTH)
    c.polyline(cov, MOSS, 10)
    rs = np.random.default_rng(5)
    for k in range(9):                                    # a few stones in the earth
        sx = rs.uniform(xout + 30, xin - 30)
        sy = rs.uniform(mound_y(sx) + 40, G - 20)
        c.polygon(ellipse(sx, sy, rs.uniform(14, 26), rs.uniform(9, 15), 12), EARTH * 1.25)
    # the two portals: a dark arch with a ring of stones; the right one is dug first
    for k, px in enumerate((xin, xout)):
        u = smoothstep(seg(dug, 0.0, 0.5)) if k == 0 else smoothstep(seg(dug, 0.5, 1.0))
        if u <= 0:
            continue
        py = fin_y(px)
        w, h = 64 * u, 96 * u
        c.polygon(ellipse(px, py + 4, w, h, 24, math.pi, 2 * math.pi) + [(px + w, py + BOARD_T), (px - w, py + BOARD_T)],
                  TUNNEL)
        for q in range(7):
            a = math.pi + math.pi * q / 6
            c.circle(px + math.cos(a) * (w + 9), py + 4 + math.sin(a) * (h + 9), 11 * u, STONE * (0.9 + 0.1 * (q % 2)))


def draw_tray_stand(c):
    """Legs under the catch tray."""
    for lx in (TRAY[0] + 30, TRAY[1] - 30):
        rect(c, lx - 8, TRAY_Y + BOARD_T, lx + 8, G + 4, TRUNK * 0.9)


def draw_finish(c, s, lit=1.0, t=0.0):
    """The finish arch over the track: two posts (near and far side), a cross bar with a chequered band, a lantern."""
    x = FINISH_X
    y = fin_y(x)
    top = y - FACE - 150
    fx, fy = back(x, y)
    c.line(fx, fy, fx, top - (y - fy) + FACE, TRUNK * 0.8, 10)            # far post (behind)
    rect(c, x - 7, top, x + 7, G + 4, TRUNK)                              # near post
    rect(c, x - 60, top - 26, x + 60, top, np.array([232, 226, 210]))
    for q in range(8):
        for r_ in range(2):
            if (q + r_) % 2 == 0:
                rect(c, x - 60 + q * 15, top - 26 + r_ * 13, x - 45 + q * 15, top - 13 + r_ * 13,
                     np.array([40, 36, 40]))
    lx, ly = x + 34, top - 70
    c.line(x + 30, top - 26, lx, ly, IRON, 3)
    c.polygon([(lx - 11, ly), (lx + 11, ly), (lx + 13, ly + 28), (lx - 13, ly + 28)],
              np.array([50, 50, 46]) + LAMP * 0.85 * lit)
    if lit > 0:
        s.glow_draw(lambda g: g.circle(lx, ly + 14, 60, LAMP * 0.6 * lit))


def draw_gate(c, open_=0.0):
    """The start gate at the top of the run: a bar across the lanes that lifts."""
    y = board_y(0, GATE_X)
    lift = 70 * smoothstep(open_)
    c.line(GATE_X, y - 60 - lift, GATE_X, y - 4 - lift, IRON * 1.4, 7)
    c.line(GATE_X, y - 60 - lift, *back(GATE_X, y - 60 - lift), IRON * 1.2, 5)
    c.line(GATE_X, y - 60 - lift, PLATFORM[0] + 20, PLATFORM[2] - 70, IRON, 3)     # the pull wire to the lever


PLATFORM = (6770.0, 6930.0, G - 1610.0)       # Springs' little start platform on TREE_B: x0, x1, y


def draw_platform(c):
    x0, x1, y = PLATFORM
    rect(c, x0, y, x1, y + 16, WOOD)
    c.line(x0 + 20, y + 16, TREE_B + 40, y + 120, TRUNK * 0.9, 9)
    lx = PLATFORM[0] + 20
    c.line(lx, y, lx, y - 70, IRON, 5)                    # the gate lever
    c.circle(lx, y - 70, 7, np.array([200, 70, 60]))


def turn_lights():
    """A little lantern on the trunk at every turn and at the top: (x, y)."""
    out = [(TREE_B + 30, Y_TOP0 - 160)]
    for k in range(N_BOARDS):
        (xl, yl), (xr, yr), d = board(k)
        out.append((TREE_A - 60, yl - 140) if d < 0 else (TREE_B + 60, yr - 140))
    return out


def spark_path():
    """The way Glo's spark runs up the run from the finish lantern: along the last ramp, then up the zigzag board by
    board (low end, high end), to the lantern at the top -> [(x, y)], and for each turn light the index of the
    point where it catches."""
    pts = [(FINISH_X, fin_y(FINISH_X) - 20), (FIN0[0], FIN0[1] - 20)]
    catch = {}
    for k in reversed(range(N_BOARDS)):
        (xl, yl), (xr, yr), d = board(k)
        low, high = ((xl, yl), (xr, yr)) if d < 0 else ((xr, yr), (xl, yl))
        pts.append((low[0], low[1] - 20))
        catch[k + 1] = len(pts) - 1                      # turn light k + 1 hangs by board k's low end
        pts.append((high[0], high[1] - 20))
    pts.append(turn_lights()[0])
    catch[0] = len(pts) - 1
    return pts, catch


def draw_turn_lights(c, s, lit, t):
    for i, (x, y) in enumerate(turn_lights()):
        u = lit[i] if i < len(lit) else 0.0
        sway = 0.06 * math.sin(t * 1.3 + i)
        c.line(x, y - 30, x + 30 * sway, y, IRON, 2)
        bx = x + 30 * sway
        c.polygon([(bx - 12, y), (bx + 12, y), (bx + 14, y + 30), (bx - 14, y + 30)],
                  np.array([50, 50, 46]) + LAMP * 0.85 * u)
        if u > 0:
            s.glow_draw(lambda g, bx=bx, y=y, u=u: g.circle(bx, y + 14, 70, LAMP * 0.55 * u))


def draw_pulley(c, rope_to=None):
    """Hans' hoist pulley hanging from the branch; rope_to = the two rope ends [(x, y), (x, y)]."""
    px, py = PULLEY
    by = branch_y(px)
    c.line(px, by, px, py, IRON, 4)
    c.circle(px, py, 22, IRON * 1.2)
    c.circle(px, py, 8, IRON * 0.7)
    if rope_to:
        for k, (x, y) in enumerate(rope_to):
            sx = px + (-22 if k == 0 else 22)
            c.line(sx, py, x, y, ROPE, 3)


def lane_off(j):
    """(dx, dy, scale) of lane j: further lanes higher on screen, a little to the right and a little smaller."""
    return LANE_DX * j, -LANE_DY * j, 1.0 - LANE_SC * j


def draw_marble(c, x, y, r, ang, col, s=None, glow=None, shade=1.0):
    """A painted wooden ball: base colour, a white band around it that turns with the real spin, a soft highlight.
    The band is a great circle seen at a slant, so it sweeps across as the ball rolls."""
    col = np.asarray(col, np.float64) * shade
    c.circle(x, y, r, col * 0.62)
    c.circle(x - r * 0.06, y - r * 0.06, r * 0.9, col)
    # the band: the near half of a great circle tilted towards us, turned by the roll angle (the ball spins about
    # the axis pointing at us as it rolls along the track)
    band = np.array([236, 230, 214], np.float64) * shade
    for i in range(24):
        a = 2 * math.pi * i / 24
        a2 = 2 * math.pi * (i + 1) / 24
        p0 = _band_pt(x, y, r, ang, a)
        p1 = _band_pt(x, y, r, ang, a2)
        if p0[2] >= 0 and p1[2] >= 0:
            c.line(p0[0], p0[1], p1[0], p1[1], band, max(1.5, r * 0.26))
    c.circle(x - r * 0.38, y - r * 0.4, r * 0.24, lighten(col, 1.5) * 0.9 + 18)
    c.circle(x - r * 0.42, y - r * 0.44, r * 0.1, np.array([250, 246, 236]) * shade)


def _band_pt(x, y, r, ang, a):
    """Point a (rad) of the band: a great circle in the x-z plane tilted 0.55 rad towards us, rolled by ang."""
    bx, by, bz = math.cos(a), 0.0, math.sin(a)
    tilt = 0.55
    by, bz = by * math.cos(tilt) - bz * math.sin(tilt), by * math.sin(tilt) + bz * math.cos(tilt)
    ca, sa = math.cos(ang), math.sin(ang)
    return x + (bx * ca - by * sa) * r * 0.92, y + (bx * sa + by * ca) * r * 0.92, bz
