"""Forest Keepers, The Treetop Marble Run (flat look): the course between the two big trees, the marble physics, and
the drawing of both (docs/engines/forest_keepers_marble_run_flat.md).

Three wide boards zigzag down between the trunks (every board the same length and slope, each end resting on a peg
Springs taps into the trunk; a stop at every turn), then the peg forest on the front of TREE_A, then the long last
ramp right, through the tunnel in the mound, over the finish line into the catch tray at the foot of TREE_B.

The boards are wide: the six marbles race side by side, one lane each (lane 0 nearest us; a lane further back is drawn
a little higher, to the right and smaller - we look from a little above and to the left). That is how real marble
races are run, and it lets a faster marble pass. Physics (pymunk, 480 Hz): each marble is a solid wooden ball (moment
2/5 m r^2) that rolls on the wood with friction; the marbles differ a little, as hand-made wooden balls do (size,
bounce, rolling resistance), and those differences decide the race. Lanes don't touch, so each marble runs in its own
space on the same course. The race is fully simulated before rendering; nothing is steered.
"""
import math

import numpy as np
import pymunk
import skia

from families.foundry.keepers.common import GRAVITY

from .marble_flat_world import BACK, RUN, TREE_A, TREE_B, TRUNK, WOOD, WOOD2, WOOD3
from .storybook import mix, oval, rrect, smooth, tone

# ----------------------------------------------------------------------------------------------- the course

N_BOARDS = 3
LEVEL_GAP = 175.0
DROP = 60.0                         # every board falls 90 px over its length: the same slope
Y_HIGH0 = BACK - 820.0              # the top board's high end (the start)
BOARD_LEN = 1530.0
# every board hangs centred under the one pulley (they are hoisted from an eye at their middle): all span the same x;
# a slot near each board's low end lets the marbles drop through onto the board below (a lip at each end stops one
# that rolls past it), the way real marble-run boards turn
LEFT_X = RIGHT_X = (RUN - BOARD_LEN / 2, RUN + BOARD_LEN / 2)
HOLE = 72.0                         # the drop slot (a marble is 52 across)
HOLE_IN = 16.0                      # from the board's end
LIP_H = 40.0
BOARD_T = 18.0                      # board thickness (its front edge)
SEG_R = 3.0
N_LANES = 6
LANE_DY, LANE_DX, LANE_SC = 8.0, 6.0, 0.02
FACE = LANE_DY * N_LANES + 8.0      # a board's top face as drawn: up ...
FACE_DX = FACE * LANE_DX / LANE_DY  # ... and to the right
R0 = 26.0                           # marble radius
START_X = LEFT_X[1] - 52.0 - R0 - 2.0          # the marbles wait at the top board's high end ...
GATE_X = START_X - R0 - 5.0                   # ... behind the start gate
BOX = (TREE_A - 180.0, TREE_A + 200.0)      # the peg forest on the front of TREE_A (its walls)
BOX_TOP = BACK - 360.0
PEG_R = 7.0
PEG_ROWS = [BACK - 330.0, BACK - 270.0, BACK - 210.0]
PEG_STEP = 80.0
FIN0 = (BOX[0] + 10.0, BACK - 150.0)          # the last ramp: from the floor of the peg box ...
FIN1 = (TREE_B - 370.0, BACK - 35.0)          # ... to the catch tray (just past the tunnel and the line)
TRAY = (FIN1[0], TREE_B - 15.0)
TRAY_Y = FIN1[1]
FINISH_X = TREE_B - 410.0                     # the finish line, right after the tunnel
LANE_STOP = 58.0                              # each lane's end stop in the tray is this much further back:
                                              # the six marbles come to rest side by side, not on one spot
MOUND = (6070.0, 6730.0, BACK - 210.0)        # the mound the tunnel goes through: x0, x1, top
TUNNEL_IN, TUNNEL_OUT = MOUND[0] + 95.0, MOUND[1] - 95.0
PEG_SPOTS_DY = BOARD_T + 12.0


def board(k):
    """Board k (0 = top): ((x_left, y_left), (x_right, y_right), dir); dir -1 = the marbles roll left."""
    hi = Y_HIGH0 + LEVEL_GAP * k
    if k % 2 == 0:
        return (LEFT_X[0], hi + DROP), (LEFT_X[1], hi), -1
    return (RIGHT_X[0], hi), (RIGHT_X[1], hi + DROP), 1


def board_y(k, x):
    (x0, y0), (x1, y1), _ = board(k)
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def board_ang(k):
    (x0, y0), (x1, y1), _ = board(k)
    return math.atan2(y1 - y0, x1 - x0)


def board_mid(k):
    (x0, y0), (x1, y1), _ = board(k)
    return (x0 + x1) / 2, (y0 + y1) / 2


def fin_y(x):
    """The last ramp's surface (and the tray's) at x."""
    if x >= FIN1[0]:
        return TRAY_Y
    return FIN0[1] + (FIN1[1] - FIN0[1]) * (x - FIN0[0]) / (FIN1[0] - FIN0[0])


FIN_ANG = math.atan2(FIN1[1] - FIN0[1], FIN1[0] - FIN0[0])
FIN_LEN = math.hypot(FIN1[0] - FIN0[0], FIN1[1] - FIN0[1])


def hole(k):
    """Board k's drop slot (x0, x1), near its low end (the last board drops into the peg forest)."""
    (x0, _), (x1, _), d = board(k)
    return (x0 + HOLE_IN, x0 + HOLE_IN + HOLE) if d < 0 else (x1 - HOLE_IN - HOLE, x1 - HOLE_IN)


def board_segments(k):
    """Board k's top surface as physics segments: either side of its slot."""
    (x0, y0), (x1, y1), d = board(k)
    h0, h1 = hole(k)
    return [((x0, y0), (h0, board_y(k, h0))), ((h1, board_y(k, h1)), (x1, y1))]


def lips(k):
    """(x, y_top, y_bottom) of the lips at both ends of board k."""
    (x0, y0), (x1, y1), d = board(k)
    return [(x0 + 4, y0 - LIP_H, y0), (x1 - 4, y1 - LIP_H, y1)]


def stops():
    return []


def pegs():
    """The peg forest: rows of 4 and 3 dowels, the 3-rows offset half a step (a triangular grid). Every gap (peg to
    peg, peg to wall) is wider than any marble, so none can wedge."""
    out = []
    x0 = BOX[0] + 70.0
    for i, y in enumerate(PEG_ROWS):
        xs = [x0 + PEG_STEP * j for j in range(4)] if i % 2 == 0 else [x0 + PEG_STEP * (j + 0.5) for j in range(3)]
        out += [(x, y) for x in xs]
    return out


def deflectors():
    """Half pegs on the offset row: a short slanted strip on each wall turns a marble running down the wall back into
    the pegs (as on a real peg board) -> [((x0, y0), (x1, y1))]."""
    y = PEG_ROWS[1]
    return [((BOX[0] + SEG_R, y - 22), (BOX[0] + 32, y + 6)), ((BOX[1] - SEG_R, y - 22), (BOX[1] - 32, y + 6))]


def box_walls():
    """(x, y_top, y_bottom) of the peg forest's two side walls; the right one stops short so the marbles get out."""
    return [(BOX[0], BOX_TOP, fin_y(BOX[0])), (BOX[1], BOX_TOP, fin_y(BOX[1]) - 72.0)]


def peg_spots():
    """Where Springs taps the trunk pegs: under each board end, on the trunk (x, y), in the order he does them:
    TREE_A bottom to top, then TREE_B top to bottom (board k: its two ends)."""
    a, b = [], []
    for k in range(N_BOARDS):
        (xl, yl), (xr, yr), d = board(k)
        a.append((k, -1, (xl + 8.0, yl + PEG_SPOTS_DY)))
        b.append((k, 1, (xr - 8.0, yr + PEG_SPOTS_DY)))
    return list(reversed(a)) + b


def course_checks():
    """Owner rule: things line up. Every board the same length and slope, the pegs evenly spaced."""
    lens, slopes = [], []
    for k in range(N_BOARDS):
        (x0, y0), (x1, y1), _ = board(k)
        lens.append(x1 - x0)
        slopes.append(abs(y1 - y0) / (x1 - x0))
    ps = pegs()
    gaps = [ps[i + 1][0] - ps[i][0] for i in range(3)]
    return {"boards": N_BOARDS, "boards_even": max(lens) - min(lens) < 0.5,
            "slopes_even": max(slopes) - min(slopes) < 1e-6, "slope_deg": round(math.degrees(math.atan(slopes[0])), 2),
            "board_len": round(lens[0], 1), "pegs": len(ps), "pegs_even": max(gaps) - min(gaps) < 0.5,
            "peg_gap_px": round(PEG_STEP - 2 * PEG_R, 1), "marble_d_px": 2 * R0}


# ----------------------------------------------------------------------------------------------- physics

class Trait:
    """How one hand-made wooden ball differs from the others (small, realistic)."""

    def __init__(self, r, bounce, roll):
        self.r, self.bounce, self.roll = r, bounce, roll


def traits(seed):
    rng = np.random.default_rng(seed)
    return [Trait(R0 * rng.uniform(0.97, 1.03), rng.uniform(0.25, 0.55), rng.uniform(0.02, 0.11))
            for _ in range(N_LANES)]


PHYS_HZ = 480
REC_HZ = 120


class Run:
    """One marble down the whole course in its own space. Recorded at REC_HZ: x, y, angle, speed, touching;
    events (t, kind, x, y, impulse) for the sound."""

    def __init__(self, trait, t_max=60.0, lane=0):
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

        for k in range(N_BOARDS):
            for (ax, ay), (bx, by) in board_segments(k):
                segment((ax, ay + SEG_R), (bx, by + SEG_R), 0.5)
            for x, ya, yb in lips(k):
                segment((x, yb + SEG_R), (x, ya), 0.45, kind="stop")
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
        segment((FIN1[0], FIN1[1] + SEG_R), (TRAY[1], TRAY_Y + SEG_R), 0.4)
        stop = TRAY[1] - lane * LANE_STOP
        segment((stop, TRAY_Y + SEG_R), (stop, TRAY_Y - 60), 0.15, kind="stop")
        sp.add(*shapes)

        b = pymunk.Body(1.0, 0.4 * tr.r * tr.r)
        b.position = (START_X, board_y(0, START_X) - tr.r)
        b.velocity_func = self._roll
        c = pymunk.Circle(b, tr.r)
        c.elasticity, c.friction = tr.bounce, 0.9
        sp.add(b, c)
        self.body, self.space = b, sp
        self.events = []
        self.touch = 0
        self.t = 0.0
        sp.on_collision(None, None, begin=self._begin, separate=self._sep, post_solve=self._post)
        rec = []
        n_sub = PHYS_HZ // REC_HZ
        self.finish_t = None
        while self.t < t_max:
            for _ in range(n_sub):
                sp.step(1.0 / PHYS_HZ)
                self.t += 1.0 / PHYS_HZ
            p, v = b.position, b.velocity
            rec.append((p.x, p.y, b.angle, v.length, 1.0 if self.touch > 0 else 0.0))
            if self.finish_t is None and p.x > FINISH_X and p.y > BACK - 120:
                self.finish_t = self.t
            if self.finish_t is not None and self.t > self.finish_t + 6.0 and v.length < 3.0:
                break
        self.rec = np.array(rec)
        self.dur = len(rec) / REC_HZ

    def _roll(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        if self.touch > 0:                                        # rolling resistance on the wood
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
        """(x, y, angle, speed) tau seconds after the gate opens (holds at the ends)."""
        f = tau * REC_HZ - 1.0
        if f <= 0:
            r = self.rec[0]
            return float(r[0]), float(r[1]), float(r[2]), 0.0
        i = int(f)
        if i >= len(self.rec) - 1:
            r = self.rec[-1]
            return float(r[0]), float(r[1]), float(r[2]), float(r[3])
        u = f - i
        a, b = self.rec[i], self.rec[i + 1]
        return tuple(float(a[j] + (b[j] - a[j]) * u) for j in range(4))


def course_progress(x, y):
    """A number that grows along the course (board by board), for the race order."""
    for k in range(N_BOARDS):
        (x0, y0), (x1, y1), d = board(k)
        if min(y0, y1) - 90 <= y <= max(y0, y1) + 30 and x0 - 80 <= x <= x1 + 80:
            u = (x - x0) / (x1 - x0)
            return k + max(0.0, min(1.0, (1 - u) if d < 0 else u))
    if y < fin_y(min(max(x, FIN0[0]), FIN1[0])) - 50 and BOX[0] - 10 <= x <= BOX[1] + 10:
        return N_BOARDS + max(0.0, min(1.0, (y - BOX_TOP) / (PEG_ROWS[-1] + 30 - BOX_TOP))) * 0.99
    return N_BOARDS + 1.0 + max(0.0, min(1.0, (x - FIN0[0]) / (FINISH_X - FIN0[0]))) * 1.5


class Race:
    """The six marbles released together: finish times, order, lead changes as a viewer sees them."""

    def __init__(self, seed, t_max=70.0):
        self.seed = seed
        self.traits = traits(seed)
        self.runs = [Run(tr, t_max, lane=i) for i, tr in enumerate(self.traits)]
        self.finish = [r.finish_t if r.finish_t is not None else 999.0 for r in self.runs]
        self.order = sorted(range(N_LANES), key=lambda i: self.finish[i])
        self.dur = max(r.dur for r in self.runs)

    def standings(self, tau):
        """Lane indices in race order at tau (finished ones by their finish time)."""
        def key(i):
            if self.finish[i] <= tau:
                return (0, self.finish[i])
            x, y, _, _ = self.runs[i].at(tau)
            return (1, -course_progress(x, y))
        return sorted(range(N_LANES), key=key)

    def lead_changes(self, ahead=None, hold=0.5, hz=30):
        """Lead changes a viewer sees: a new leader that is ahead by `ahead` (default half a marble) for `hold` s."""
        ahead = R0 / BOARD_LEN if ahead is None else ahead
        lead, cand, n, t = None, None, 0, 0.0
        end = min(self.finish)
        while t < end:
            prog = [course_progress(*self.runs[i].at(t)[:2]) for i in range(N_LANES)]
            o = sorted(range(N_LANES), key=lambda i: -prog[i])
            top = o[0]
            if prog[top] - prog[o[1]] >= ahead and top != lead:
                if cand is None or cand[0] != top:
                    cand = (top, t)
                elif t - cand[1] >= hold:
                    n += lead is not None
                    lead, cand = top, None
            elif top == lead:
                cand = None
            t += 1.0 / hz
        return n

    def summary(self):
        f = sorted(x for x in self.finish if x < 999)
        return {"seed": self.seed, "finished": len(f), "spread_s": round(f[-1] - f[0], 2) if f else None,
                "first_two_s": round(f[1] - f[0], 2) if len(f) > 1 else None, "lead_changes": self.lead_changes(),
                "order": self.order, "times": [round(x, 2) for x in self.finish]}


# ----------------------------------------------------------------------------------------------- drawing

KINDS = ["wheels", "tentacles", "teeth", "springs", "lantern", "digger"]       # lane i = KINDS[i]'s marble
MARBLE_COLS = {"wheels": (86, 128, 196), "tentacles": (226, 128, 58), "teeth": (150, 104, 186),
               "springs": (226, 186, 74), "lantern": (62, 172, 160), "digger": (198, 88, 72)}
PLAIN = (206, 170, 124)               # bare wood (the cubes, the balls before Glo colours them, Wheels' old ball)
BAND = (246, 238, 220)


def lane_xy(x, y, lane):
    """Where a point of lane `lane` on a board is drawn (further lanes up, right, smaller)."""
    return x + lane * LANE_DX, y - lane * LANE_DY, 1.0 - lane * LANE_SC


def draw_marble(pg, x, y, r, col, ang=0.0, band=True, a=1.0):
    """A wooden marble at (x, y) radius r: flat colour, one soft shade, a cream band round it that turns with its
    real spin (ang, rad) so we see it roll."""
    pg.shape(oval(x, y, r, r), col, 0.12)
    if band:
        c = pg.c
        c.save()
        c.clipPath(oval(x, y, r * 0.98, r * 0.98), doAntiAlias=True)
        # the band: a stripe across the ball, at its spin angle (a great circle seen side on)
        ca, sa = math.cos(ang), math.sin(ang)
        p = skia.Path()
        w = r * 0.22
        p.moveTo(x - sa * w - ca * r * 1.2, y + ca * w - sa * r * 1.2)
        p.lineTo(x - sa * w + ca * r * 1.2, y + ca * w + sa * r * 1.2)
        p.lineTo(x + sa * w + ca * r * 1.2, y - ca * w + sa * r * 1.2)
        p.lineTo(x + sa * w - ca * r * 1.2, y - ca * w - sa * r * 1.2)
        p.close()
        pg.flat(p, mix(col, BAND, 0.75), 0.92 * a)
        c.restore()
    pg.flat(oval(x - r * 0.32, y - r * 0.36, r * 0.22, r * 0.16), mix(col, (255, 248, 236), 0.45), 0.55 * a)


def draw_board_shape(pg, x0, y0, x1, y1, t_=BOARD_T, face=FACE, face_dx=FACE_DX, col=WOOD):
    """A wide board seen a little from above: its top face (a slanted strip back and to the right) and its front
    edge. (x0, y0)-(x1, y1) = the front line of its top surface."""
    top = smooth([(x0, y0), (x1, y1), (x1 + face_dx, y1 - face), (x0 + face_dx, y0 - face)], closed=True)
    top = skia.Path().moveTo(x0, y0).lineTo(x1, y1).lineTo(x1 + face_dx, y1 - face).lineTo(x0 + face_dx, y0 - face)
    top.close()
    pg.flat(top, tone(col, 0.05))
    for j in range(1, 3):                                         # two faint grain lines along it
        u = j / 3
        pg.stroke(skia.Path().moveTo(x0 + face_dx * u, y0 - face * u).lineTo(x1 + face_dx * u, y1 - face * u),
                  tone(col, -0.06), 1.4)
    edge = skia.Path().moveTo(x0, y0).lineTo(x1, y1).lineTo(x1, y1 + t_).lineTo(x0, y0 + t_)
    edge.close()
    pg.flat(edge, tone(col, -0.12))
    # the end grain at each end (the right end shows its side)
    side = skia.Path().moveTo(x1, y1).lineTo(x1 + face_dx, y1 - face).lineTo(x1 + face_dx, y1 - face + t_)
    side.lineTo(x1, y1 + t_)
    side.close()
    pg.flat(side, tone(col, -0.2))


def draw_board_at(pg, k, cx, cy, ang, sh):
    """Board k drawn with its middle at (cx, cy) world, tilted ang (rad): while Hans hoists it, and in place."""
    L = BOARD_LEN
    ca, sa = math.cos(ang), math.sin(ang)
    x0, y0 = cx - ca * L / 2 - sh, cy - sa * L / 2
    x1, y1 = cx + ca * L / 2 - sh, cy + sa * L / 2
    draw_board_shape(pg, x0, y0, x1, y1)


def draw_peg_end(pg, x, y, a=1.0, out=1.0):
    """A trunk peg seen end on: a round dowel end poking out of the bark (out 0..1 how far it is in)."""
    if out <= 0.01:
        return
    r = 9.0
    pg.flat(oval(x + 2, y + 3, r * 1.1, r * 1.0), (70, 50, 40), 0.25 * a)
    pg.shape(oval(x, y, r, r), WOOD3, 0.15)
    pg.flat(oval(x - 1.5, y - 1.5, r * 0.55, r * 0.55), tone(WOOD, 0.08), 0.8)


def draw_stop(pg, x, y0, y1, sh):
    """The stop at a turn: an upright plank across all lanes (its front edge and a sliver of its top)."""
    pg.shape(rrect(x - 6 - sh, y0, x + 6 - sh, y1, 3), WOOD2, 0.1)
    pg.flat(skia.Path().moveTo(x - 6 - sh, y0).lineTo(x + 6 - sh, y0).lineTo(x + 6 + FACE_DX - sh, y0 - FACE)
            .lineTo(x - 6 + FACE_DX - sh, y0 - FACE).close(), tone(WOOD2, 0.06))


def draw_box_back(pg, sh, a=1.0):
    """The peg forest's back panel (behind every lane), its side walls."""
    x0, x1 = BOX[0] - sh, BOX[1] - sh
    yb = fin_y(BOX[1])
    p = skia.Path().moveTo(x0 + FACE_DX, BOX_TOP - FACE).lineTo(x1 + FACE_DX, BOX_TOP - FACE)
    p.lineTo(x1 + FACE_DX, yb - FACE).lineTo(x0 + FACE_DX, fin_y(BOX[0]) - FACE).close()
    pg.flat(p, tone(WOOD, -0.02), a)
    for i, y in enumerate(PEG_ROWS):                              # faint pencil lines where the rows were measured
        pg.stroke(skia.Path().moveTo(x0 + FACE_DX + 8, y - FACE).lineTo(x1 + FACE_DX - 8, y - FACE),
                  tone(WOOD, -0.12), 1.2)


def draw_box_walls(pg, sh, a=1.0):
    for x, y0, y1 in box_walls():
        xs = x - sh
        p = skia.Path().moveTo(xs - 5, y0).lineTo(xs + 5, y0).lineTo(xs + 5 + FACE_DX, y0 - FACE)
        p.lineTo(xs + 5 + FACE_DX, y1 - FACE).lineTo(xs + 5, y1).lineTo(xs - 5, y1).close()
        pg.flat(p, WOOD2, a)
    for (ax, ay), (bx, by) in deflectors():
        pg.stroke(skia.Path().moveTo(ax - sh, ay).lineTo(bx - sh, by), WOOD3, 7.0)


def draw_dowel(pg, x, y, lane_from, lane_to, sh, out=0.2):
    """The part of a peg-forest dowel from lane_from to lane_to (lanes are depth slices; it runs back and right).
    out: a loose dowel sticks out further toward us (1 loose .. 0.2 home)."""
    a = lane_xy(x - sh, y, lane_from - 0.5 - (1.2 * (out - 0.2) if lane_from <= 0 else 0.0))
    b = lane_xy(x - sh, y, lane_to + 0.5)
    p = skia.Path().moveTo(a[0], a[1]).lineTo(b[0], b[1])
    pg.stroke(p, WOOD3, 2 * PEG_R)
    if lane_from <= 0:                                            # its round front end
        pg.shape(oval(a[0], a[1], PEG_R, PEG_R), tone(WOOD, 0.02), 0.15)


SOIL = (128, 100, 72)
TUNNEL_DARK = (44, 32, 26)
HOLE_W, HOLE_H = 50.0, 74.0         # a tunnel mouth: half width, height above the ramp


def hole_path(j, h, sh):
    """Tunnel mouth j (0 in, 1 out), dug h 0..1 (it grows from a small scrape to the full arch): a round-topped
    arch standing on the ramp line."""
    xm = (TUNNEL_IN, TUNNEL_OUT)[j]
    y = fin_y(xm) + 10.0
    w, hh = HOLE_W * (0.35 + 0.65 * h), HOLE_H * (0.3 + 0.7 * h)
    p = skia.Path()
    p.moveTo(xm - w - sh, y)
    p.lineTo(xm - w - sh, y - hh + w)
    p.arcTo(skia.Rect(xm - w - sh, y - hh, xm + w - sh, y - hh + 2 * w), 180, 180, False)
    p.lineTo(xm + w - sh, y)
    p.close()
    return p


def mound_path(sh):
    x0, x1, top = MOUND
    m = smooth([(x0 - 40 - sh, BACK + 8), (x0 + 60 - sh, top + 60), ((x0 + x1) / 2 - sh, top),
                (x1 - 60 - sh, top + 60), (x1 + 40 - sh, BACK + 8)], closed=False)
    m.lineTo(x0 - 40 - sh, BACK + 8)
    m.close()
    return m


def draw_tunnel_inside(pg, sh, holes):
    """Inside each dug mouth: the dark, drawn before the ramp and the marbles (they are seen going in)."""
    for j, h in enumerate(holes):
        if h > 0.01:
            pg.flat(hole_path(j, h, sh), TUNNEL_DARK)


def draw_tunnel_shade(pg, sh, holes):
    """Over the ramp and the marbles inside each mouth: darker the further in (drawn just before the mound)."""
    for j, h in enumerate(holes):
        if h <= 0.01:
            continue
        p = hole_path(j, h, sh)
        b = p.getBounds()
        xa, xb = (b.left(), b.right()) if j == 0 else (b.right(), b.left())
        g = skia.GradientShader.MakeLinear([(xa, 0), (xb, 0)], [skia.Color4f(0.17, 0.12, 0.1, 0.25).toColor(),
                                                                 skia.Color4f(0.17, 0.12, 0.1, 0.97).toColor()])
        pg.c.drawPath(p, skia.Paint(AntiAlias=True, Shader=g))


def draw_mound(pg, sh, holes=(1.0, 1.0)):
    """The mound the last ramp goes through, with its tunnel mouths cut out (holes: how far each is dug, 0..1)."""
    x0, x1, top = MOUND
    m = mound_path(sh)
    for j, h in enumerate(holes):
        if h > 0.01:
            m = skia.Op(m, hole_path(j, h, sh), skia.PathOp.kDifference_PathOp)
    pg.shape(m, SOIL, 0.1)
    rs = np.random.default_rng(5)
    c = pg.c
    c.save()
    c.clipPath(m, doAntiAlias=True)
    for _ in range(16):                                           # pebbles on it
        x = rs.uniform(x0 + 40, x1 - 40)
        y = rs.uniform(top + 30, BACK - 6)
        pg.flat(oval(x - sh, y, rs.uniform(4, 9), rs.uniform(3, 6)), tone(SOIL, -0.12), 0.8)
    c.restore()
    for j, h in enumerate(holes):                                 # a rim of darker soil round each mouth
        if h > 0.01:
            pg.stroke(hole_path(j, h, sh), tone(SOIL, -0.18), 5.0)


def draw_tray(pg, sh, col=WOOD2):
    x0, x1 = TRAY[0] - sh - 10, TRAY[1] - sh + 8
    y = TRAY_Y
    pg.shape(rrect(x0, y, x1, y + 22, 5), col, 0.1)
    pg.flat(skia.Path().moveTo(x0, y).lineTo(x1, y).lineTo(x1 + FACE_DX, y - FACE).lineTo(x0 + FACE_DX, y - FACE)
            .close(), tone(col, 0.06))
    pg.shape(rrect(x1 - 4, y - 64, x1 + 8, y + 22, 3), tone(col, -0.05), 0.0)
    for i in range(1, N_LANES):                                   # each lane's own end stop, further back each time
        lx, ly, _ = lane_xy(TRAY[1] - i * LANE_STOP - sh, y, i)
        pg.flat(rrect(lx - 3, ly - 20, lx + 3, ly + 1, 2), tone(col, -0.22))


def draw_finish_line(pg, sh, a=1.0):
    """A chequered stripe painted across the last ramp's top face at FINISH_X."""
    x, y = FINISH_X - sh, fin_y(FINISH_X)
    n = N_LANES
    for i in range(n):
        for j in range(2):
            cx0 = x + i * LANE_DX + j * 7
            cy0 = y - i * LANE_DY
            p = skia.Path().moveTo(cx0, cy0).lineTo(cx0 + 7, cy0).lineTo(cx0 + 7 + LANE_DX, cy0 - LANE_DY)
            p.lineTo(cx0 + LANE_DX, cy0 - LANE_DY).close()
            pg.flat(p, (246, 240, 228) if (i + j) % 2 == 0 else (70, 56, 48), a)
