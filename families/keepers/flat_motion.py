"""Forest Keepers motion for the flat picture-book look (owner, 2026-11-03/04: Hans "walks on his legs" and is less
floaty, using 2-4 tentacles at once is his thing; Digs digs the way a mole really does; no lazy animation: nothing
slides, stretches, snaps or warps - families/keepers/storycheck.py).

Pure functions of time (no drawing), so the renderer and the checks see exactly the same motion.

    g = TripodGait(x0, v, ground, k)        # Hans: g.body_x(t), g.feet(t) -> six planted (x, y) for monster.feet
    d = MoleDig(k)                          # Digs: d.angles(t) -> {-1: rad, 1: rad} for monster.paw_ang
    s = Spoil(d, x, rim_y, k, t1, ...)      # the soil Digs throws out: s.pieces(t, dt), s.heap(side, t)
"""
import math

from families.foundry.keepers.common import smoothstep

HANS_LEG = 275.0              # a leg tentacle's length (monster.py units)

# Hans in the flat look (owner, 2026-11-04): "orange body and orange legs, peach suckers, and then for his... wings,
# they should be orange, but they could change color from yellow to peach to coral, and they should flap around a bit
# with his mood. Like maybe... coral and flapping when he's excited, and maybe yellow and still and like erect when
# he's surprised". His wings are a feeling he shows, like a blush: they change over about half a second, never at once.
HANS_COLOURS = {"legs": (224, 112, 30), "suckers": (250, 198, 152)}
HANS_MOODS = {
    #            wing colour        flap  speed  up    face
    "calm":      ((214, 100, 28),   0.10, 1.6,   0.0,  dict(smile=0.5)),
    "happy":     ((242, 172, 128),  0.20, 2.6,   0.1,  dict(smile=0.8, cheek=0.2)),
    "excited":   ((236, 106, 92),   0.55, 9.0,   0.15, dict(smile=1.0, cheek=0.35)),
    "surprised": ((246, 202, 66),   0.0,  0.0,   0.85, dict(smile=-1.0, attend=1.0)),
}


def hans_mood(mood, to=None, u=0.0):
    """Monster attributes for Hans in `mood`, or part way (u 0..1, eased) from `mood` to `to`."""
    def one(name):
        col, amp, spd, up, face = HANS_MOODS[name]
        return col, amp, spd, up, face
    c0, a0, s0, u0, f0 = one(mood)
    if to is None:
        u = 0.0
        c1, a1, s1, u1, f1 = c0, a0, s0, u0, f0
    else:
        c1, a1, s1, u1, f1 = one(to)
    e = smoothstep(min(max(u, 0.0), 1.0))
    lerp = lambda p, q: p + (q - p) * e                            # noqa: E731
    face = {k: lerp(f0.get(k, 0.0), f1.get(k, 0.0)) for k in set(f0) | set(f1)}
    return dict(parts_col=dict(HANS_COLOURS, wings=tuple(lerp(p, q) for p, q in zip(c0, c1))),
                wing_amp=lerp(a0, a1), wing_speed=lerp(s0, s1), wing_up=lerp(u0, u1), **face)


def smooth_path(keys):
    """A walk along x through keyframes [(t, x), ...]: it eases out of each key and into the next (it stops at
    every key), and holds before the first and after the last. -> x(t)."""
    keys = sorted(keys)

    def x(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
            if t <= t1:
                return x0 + (x1 - x0) * smoothstep((t - t0) / max(t1 - t0, 1e-9))
        return keys[-1][1]
    return x


def walk_path(keys, ease=0.6):
    """A walk along x through keyframes [(t, x), ...] the way people walk (owner 2026-11-05: smoother, more human,
    not too slow): from each stop it speeds up over `ease` s (less on a short move), keeps an even pace, and slows
    into the next stop over the same; it holds before the first key and after the last. -> x(t)."""
    keys = sorted(keys)

    def ramp(u):                                                   # distance under a smoothstep speed-up, 0..0.5
        return u ** 3 - 0.5 * u ** 4

    def x(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
            if t <= t1:
                D = max(t1 - t0, 1e-9)
                e = min(ease, D / 2)
                v = (x1 - x0) / (D - e)                            # the even pace
                s_ = t - t0
                if s_ < e:
                    return x0 + v * e * ramp(s_ / e)
                if s_ <= D - e:
                    return x0 + v * (0.5 * e + s_ - e)
                return x1 - v * e * ramp((D - s_) / e)
        return keys[-1][1]
    return x


TURN_V = 30.0                 # px/s: walking this fast (or faster) it has turned all the way round to walk


def heading(path, ahead=0.3):
    """-> turn(t), -1..1: a walker turns to face where it goes as it sets off, walks turned, and turns back to us
    as it stops (it starts turning `ahead` s before it moves, the way we look where we are going first)."""
    def turn(t):
        v = (path(t + ahead) - path(t - ahead)) / (2 * ahead)
        u = min(abs(v) / TURN_V, 1.0)
        return math.copysign(smoothstep(u), v) if u > 1e-6 else 0.0
    return turn


class Gait:
    """A walk on planted feet: each foot stays at one spot on the ground until it lifts, arcs forward and sets down
    ahead (no foot ever slides). A step is only taken when the body has moved: standing still, every foot stays
    down. `path(t)` -> the body's x; `homes` each foot's x from the body's when it sets down; `phases` when each
    foot steps (0..1 of the cycle); `dys` each foot's y from `ground` (+ = nearer the camera)."""

    def __init__(self, path, ground, k, homes, phases, dys=None, period=1.0, duty=0.6, lift=18.0, still=0.6,
                 spread=None):
        self.path, self.ground, self.k = path, ground, k
        self.spread = spread or (lambda t: 1.0)                   # homes x this (the feet come in as it turns)
        self.home, self.phase = list(homes), list(phases)
        self.dy = list(dys) if dys is not None else [0.0] * len(self.home)
        self.T, self.duty, self.lift, self.still = period, duty, lift * k, still

    def body_x(self, t):
        return self.path(t)

    def bob(self, t):
        return 0.0

    def _plant(self, i, n):
        td = (n - self.phase[i]) * self.T                         # when step n sets down
        tm = td + self.duty * self.T / 2
        return self.body_x(tm) + self.home[i] * self.spread(tm)

    def foot(self, i, t):
        """(x, y, planted, step) of foot i at time t."""
        c = t / self.T + self.phase[i]
        n = math.floor(c)
        f = c - n
        y0 = self.ground + self.dy[i]
        a, b = self._plant(i, n), self._plant(i, n + 1)
        if f < self.duty or abs(b - a) < self.still:             # down (or standing still: no step to take)
            return a if f < self.duty else (a if abs(b - a) < self.still else b), y0, True, n
        s = (f - self.duty) / (1 - self.duty)
        return a + (b - a) * smoothstep(s), y0 - self.lift * math.sin(math.pi * s), False, n

    def feet(self, t):
        return [self.foot(i, t)[:2] for i in range(len(self.home))]

    def touchdowns(self, t0, t1):
        """(t, foot) of every foot setting down after a real step in [t0, t1) (a soft step sound)."""
        out = []
        for i in range(len(self.home)):
            n = math.ceil(t0 / self.T + self.phase[i])
            while True:
                td = (n - self.phase[i]) * self.T
                if td >= t1:
                    break
                if td >= t0 and abs(self._plant(i, n) - self._plant(i, n - 1)) >= self.still:
                    out.append((td, i))
                n += 1
        return sorted(out)


class TripodGait(Gait):
    """Hans walks on his six leg tentacles in two alternating sets of three (0, 2, 4 and 1, 3, 5), like a calm
    six-legged walker: at least three tips are always down, and his head barely bobs. `path` is the body's x(t), or
    give x0 and a steady speed v (px/s)."""

    def __init__(self, x0, v, ground, k, period=1.0, duty=0.6, lift=22.0, out=(80.0, 60.0, 40.0), path=None,
                 spread=None):
        # each tip sets down a little outside its root (roots: monster.leg_root, (i - 2.5) / 2.5 * 80 units)
        homes = [((i - 2.5) / 2.5 * 80.0 + (1 if i > 2 else -1) * out[min(i, 5 - i)]) * k for i in range(6)]
        phases = [0.0 if i % 2 == 0 else 0.5 for i in range(6)]
        dys = [(5.0 if i % 2 else -5.0) * k for i in range(6)]
        super().__init__(path or (lambda t: x0 + v * t), ground, k, homes, phases, dys, period, duty, lift,
                         spread=spread)
        self.x0, self.v = x0, v

    def bob(self, t):
        """A small dip as each set takes his weight (px, down is positive) - only while he walks."""
        moving = abs(self.path(t + 0.05) - self.path(t - 0.05)) > 0.05
        return 2.5 * self.k * (0.5 - 0.5 * math.cos(4 * math.pi * t / self.T)) if moving else 0.0


class WaveGait(Gait):
    """Hans from ep 14 on (owner, FK0016: his tripod walk was "too much like a march. It's left, right, left, right...
    but with 6 feet instead of 2"): his six leg tentacles step one at a time, never two side by side together, in a
    loose ripple (phases spread round the cycle, not in order along him), each lifting a little differently. At least
    four tips are always down (duty 0.75, no two swings closer than 0.15 of a cycle), and his head eases down a touch
    as each tip lifts, so he glides rather than bobs in time."""

    PHASES = (0.0, 0.55, 0.3, 0.85, 0.15, 0.7)
    LIFTS = (1.0, 0.8, 1.15, 0.9, 1.05, 0.85)

    def __init__(self, ground, k, path, period=1.1, duty=0.75, lift=20.0, out=(80.0, 60.0, 40.0), spread=None):
        homes = [((i - 2.5) / 2.5 * 80.0 + (1 if i > 2 else -1) * out[min(i, 5 - i)]) * k for i in range(6)]
        dys = [(5.0 if i % 2 else -5.0) * k for i in range(6)]
        super().__init__(path, ground, k, homes, self.PHASES, dys, period, duty, lift, spread=spread)

    def foot(self, i, t):
        x, y, down, n = super().foot(i, t)
        if not down:                                             # this tip's own lift
            y = self.ground + self.dy[i] - (self.ground + self.dy[i] - y) * self.LIFTS[i]
        return x, y, down, n

    def bob(self, t):
        d = 0.0
        for i in range(6):
            c = t / self.T + self.phase[i]
            f = c - math.floor(c)
            n = math.floor(c)
            if f >= self.duty and abs(self._plant(i, n + 1) - self._plant(i, n)) >= self.still:
                d += math.sin(math.pi * (f - self.duty) / (1 - self.duty))
        return 1.6 * self.k * d


def arm_swing(gait, t, stride=None):
    """-> -1..1 how far a walker's right arm is swung forward at time t: the arms swing against the legs (the right
    arm forward as the left foot is ahead), as far as the feet are apart, so they settle to 0 when it stands still.
    Hand it to Monster.arm_swing (it is measured in the way it walks: Monster.swing_dir turns it onto the screen)."""
    (lx, _), (rx, _) = gait.feet(t)[:2]
    v = (gait.body_x(t + 0.05) - gait.body_x(t - 0.05)) / 0.1
    s = 1.0 if v >= 0 else -1.0
    d = (lx - rx) - (gait.home[0] - gait.home[1]) * gait.spread(t)     # how far the left foot is ahead of the right
    stride = stride or max(abs(v) * gait.T, 40.0 * gait.k)
    return max(-1.0, min(1.0, d * s / stride))


def roll_swing(path, t, wheel_r, amp=0.5):
    """-> arm swing for Wheels rolling: a gentle easy swing with his wheels' turn, 0 when he stops."""
    v = (path(t + 0.05) - path(t - 0.05)) / 0.1
    u = min(abs(v) / 60.0, 1.0)
    return amp * u * math.sin(path(t) / (wheel_r * 2.0))


def biped(kind, path, ground, k, spread=None):
    """Two-footed walks for Twigs (long stilt legs, slow steps), Digs (stubby legs, quick little steps) and Sprout
    (short legs): the feet take turns; lift and stride stay small enough that each leg keeps its length."""
    hip = {"teeth": 40.0, "digger": 62.0, "sprout": 38.0}[kind]
    # short legs can only lift their feet a little (a stub that lifted more would have to shrink) and take quick
    # little steps so the foot never reaches far ahead of the hip
    period, lift, dy = {"teeth": (0.8, 22.0, 3.0), "digger": (0.42, 5.0, 1.5), "sprout": (0.42, 5.0, 1.5)}[kind]
    toe = {"teeth": 10.0, "digger": 0.0, "sprout": 4.0}[kind]
    return Gait(path, ground, k, [-(hip + toe) * k, (hip + toe) * k], [0.0, 0.5], [-dy * k, dy * k],
                period, 0.6, lift, spread=spread)


def stance_drop(gait, hips, leg, t):
    """How far (px) a knee-less walker's body sinks at time t so each planted leg keeps its length `leg` (px):
    lowest when its feet are furthest apart, back up as one leg passes under it - the natural bob of a walk.
    hips(t) -> the two hip x's."""
    d = 0.0
    for i, hx in enumerate(hips(t)):
        fx, fy, down, _ = gait.foot(i, t)
        if down:
            dx = min(abs(fx - hx), leg * 0.95)
            d = max(d, leg - math.sqrt(leg * leg - dx * dx))
    return d


class Hopper:
    """Springs gets about by hopping on his coil springs: his feet stay down while he squashes and pushes off, the
    hop carries him forward, and he lands where the next hop starts (no sliding). -> x(t), feet-y(t), squash(t)."""

    def __init__(self, path, ground, k, period=0.95, duty=0.45, height=42.0):
        self.g = Gait(path, ground, k, [0.0], [0.0], None, period, duty, height)
        self.k = k

    def state(self, t):
        x, y, down, n = self.g.foot(0, t)
        f = (t / self.g.T) % 1.0
        sq = 0.0
        if down and abs(self.g._plant(0, n + 1) - self.g._plant(0, n)) >= self.g.still:
            d = self.g.duty                                        # squash into the push-off, spring up
            sq = 0.55 * math.sin(math.pi * min(f / d, 1.0)) if f < d else 0.0
        return x, y, sq


class MoleDig:
    """Digs digs like a mole: a mole's broad front paws face outwards and push the soil sideways, one paw after the
    other. Each stroke: reach down and in to the bottom of the hole, scoop, sweep the paw out and up to the side
    (the power stroke), flick the soil off at the end, and swing back. The arm keeps one length the whole time; only
    its angle at the shoulder changes."""

    # (stroke fraction, angle for the right arm in rad, screen y down: 0 = straight out to the side, pi/2 = down)
    KEYS = [(0.0, -0.35), (0.3, 1.95), (0.45, 2.12), (0.82, 0.12), (1.0, -0.35)]
    FLICK = 0.82

    def __init__(self, k, period=1.15, t_start=0.0):
        self.k, self.P, self.t0 = k, period, t_start
        self.offset = {1: 0.0, -1: 0.5}                            # the paws take turns

    def frac(self, sx, t):
        c = (t - self.t0) / self.P + self.offset[sx]
        return c - math.floor(c), math.floor(c)

    def angle(self, sx, t):
        f, _ = self.frac(sx, t)
        for (f0, a0), (f1, a1) in zip(self.KEYS, self.KEYS[1:]):
            if f0 <= f <= f1:
                u = smoothstep((f - f0) / (f1 - f0))
                a = a0 + (a1 - a0) * u
                break
        return a if sx > 0 else math.pi - a

    def angles(self, t):
        return {s: self.angle(s, t) for s in (-1, 1)}

    def flicks(self, sx, t0, t1, at=None):
        """Times in [t0, t1) when paw sx reaches stroke fraction `at` (default FLICK, the end of the power stroke)."""
        at = self.FLICK if at is None else at
        out = []
        n = math.ceil((t0 - self.t0) / self.P + self.offset[sx] - at)
        while True:
            t = self.t0 + (n - self.offset[sx] + at) * self.P
            if t >= t1:
                break
            if t >= t0:
                out.append(t)
            n += 1
        return out

    def scrapes(self, sx, t0, t1):
        """Times the power stroke starts (a soft scrape)."""
        return self.flicks(sx, t0, t1, 0.45)


G = 1500.0                    # px/s^2, gravity for the soil
SCOOP = 0.45                  # MoleDig stroke fraction: the paw has a load of soil from here...
RELEASE = 0.705               # ...and lets it go here, sweeping out and up, so it flies on with the paw's own speed


class Spoil:
    """The soil Digs throws out: each stroke the paw scoops one clod and two crumbs at the bottom of the hole,
    carries them out on the power stroke and lets go as it sweeps up; they fly on with the paw's own velocity (a
    little spread) and land on the heap on that side, which grows by what lands on it (smoothly, over a quarter
    second). All in the ground layer's own coordinates (the scene adds the camera)."""

    def __init__(self, dig, x, rim_y, k, t1, shoulder, arm, bob, heap_h0=22.0):
        self.dig, self.x, self.rim, self.k = dig, x, rim_y, k
        self.shoulder, self.arm, self.bob = shoulder, arm, bob     # shoulder (dx, dy) from (x, rim); arm length
        self.h0 = heap_h0 * k / 0.72
        self.flights = []                    # (id, side, t_scoop, t_release, x0, y0, vx, vy, size, offset)
        for sx in (-1, 1):
            for j, tr in enumerate(dig.flicks(sx, -2.0, t1, RELEASE)):
                ts = tr - (RELEASE - SCOOP) * dig.P
                (px, py), (vx, vy) = self.paw(sx, tr), self.paw_v(sx, tr)
                for q, (fv, size, off) in enumerate(((1.0, 7.0, 0.0), (0.9, 3.6, -5.0), (1.08, 3.0, 5.0))):
                    self.flights.append((f"soil {'LR'[sx > 0]}{j}.{q}", sx, ts, tr, px, py, vx * fv, vy * fv,
                                         size * k / 0.72, off * k / 0.72))
        self.landed = [(f, f[3] + self._fall(f)) for f in self.flights]
        self.cx = {}
        for sx in (-1, 1):
            xs = [self._fly(f, tl)[0] for f, tl in self.landed if f[1] == sx and f[0].endswith(".0")]
            self.cx[sx] = sum(xs) / len(xs)

    def paw(self, sx, t):
        a = self.dig.angle(sx, t)
        return (self.x + sx * self.shoulder[0] + math.cos(a) * self.arm,
                self.rim + self.shoulder[1] + self.bob(t) + math.sin(a) * self.arm)

    def paw_v(self, sx, t, h=1e-3):
        a, b = self.paw(sx, t - h), self.paw(sx, t + h)
        return (b[0] - a[0]) / (2 * h), (b[1] - a[1]) / (2 * h)

    def _fly(self, f, t):
        u = t - f[3]
        return f[4] + f[6] * u, f[5] + f[7] * u + 0.5 * G * u * u

    def _fall(self, f):
        top = self.rim - self.h0 * 0.8                             # about the heap's top
        a, b, c = 0.5 * G, f[7], f[5] - top
        return (-b + math.sqrt(max(b * b - 4 * a * c, 0.0))) / (2 * a)

    def heap(self, sx, t):
        """(centre x, height) of the heap on side sx at time t."""
        h = self.h0
        for f, tl in self.landed:
            if f[1] == sx and tl < t:
                h += (1.1 if f[0].endswith(".0") else 0.3) * self.k / 0.72 * smoothstep(min(1.0, (t - tl) / 0.25))
        return self.cx[sx], h

    def pieces(self, t, dt):
        """Soil Digs is carrying or that is in the air at time t: [(id, x, y, size, carried, lands this frame)]."""
        out = []
        for f, tl in self.landed:
            if f[2] <= t < tl:
                if t < f[3]:                                       # in the paw, a little in front of the palm
                    x, y = self.paw(f[1], t)
                    x += f[9]
                    y -= 4 * self.k
                    out.append((f[0], x, y, f[8], True, False))
                else:
                    x, y = self._fly(f, t)
                    out.append((f[0], x, y, f[8], False, tl - t <= dt + 1e-9))
        return out
