"""The Treetop Marble Run (flat), beat 1: the ball (docs/engines/forest_keepers_marble_run_flat.md).

At the treehouse Springs dribbles a little wooden ball (his right hand pats it down, it bounces back up to it). One
bounce lands on a root and kicks off to the right: it bounces away, each bounce lower (restitution), then rolls and
slows on the path (rolling resistance). Wheels rolls after it and scoops it up in his right pincer as it comes to rest
by him. Glo, watching it roll, has an idea (a bubble with a little marble run). Every position is a pure function of
time, so the renderer and the checks see the same motion.
"""
import math

from families.foundry.keepers.common import smoothstep

from . import storycheck as sc
from .marble_flat_world import G
from .storybook import oval

K = 0.72
BALL_R = 26.0                       # the same size as the marbles (it becomes the test ball)
GROUND = G + 2.0                    # the ball rolls just in front of the Keepers' feet line
GBALL = 2600.0                      # px/s^2 (the scene's g)
SPRINGS_L = 47.0 * K                # Springs' arm (shoulder to hand)
WOOD_BALL = (206, 170, 124)


def _seg(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


class Ball:
    """Springs at x SX dribbles from t_start; the ball gets away at t_away; Wheels (from WX) catches it."""

    def __init__(self, t_start, n_bounces, SX, WX):
        self.SX, self.WX = SX, WX
        self.hand = (SX + 100 * K, G - (170 * K) + 10 * K + SPRINGS_L)     # his right hand at the top of a dribble
        self.top = self.hand[1] + BALL_R                                    # the ball's centre there
        self.low = GROUND - BALL_R                                          # ... and on the ground
        H = self.low - self.top
        self.vp = 260.0                                                     # the pat sends it down at this speed
        self.t_dn = (-self.vp + math.sqrt(self.vp ** 2 + 2 * GBALL * H)) / GBALL
        self.v_up = math.sqrt(2 * GBALL * H)
        self.t_up = self.v_up / GBALL
        self.T = self.t_dn + self.t_up
        self.t0 = t_start
        self.pick = t_start - 0.8                                           # he picks it up off the porch step
        self.away = t_start + n_bounces * self.T                            # this pat's bounce goes wrong
        self.bx = self.hand[0]
        # the bad bounce: it lands on a root and kicks off right, low; then bounces lower each time and rolls
        hits = []
        t, x, vx, vy = self.away + self.t_dn, self.bx, 0.0, 0.0
        vx, vy = 700.0, -0.55 * self.v_up
        arcs = []
        for _ in range(4):
            dur = 2 * -vy / GBALL
            arcs.append((t, x, vx, vy, dur))
            hits.append(t + dur)
            x += vx * dur
            t += dur
            vy *= 0.45
            vx *= 0.88
        self.arcs = arcs
        self.hits = [self.away + self.t_dn] + hits
        self.roll0 = (t, x, vx)
        self.decel = 80.0
        self.roll_t = vx / self.decel
        self.rest_x = x + vx * vx / (2 * self.decel)
        self.rest_t = t + self.roll_t
        # Wheels: sets off as it gets away, slows into place with his right pincer just past it
        self.catch_x = self.rest_x - 100.0                                 # his middle: his right pincer reaches it
        self.w_go = self.away + 0.5
        self.w_at = self.rest_t + 0.4
        self.grab = (self.w_at, self.w_at + 0.7)                            # pincer down to it, closes on it
        self.lift = (self.grab[1], self.grab[1] + 0.9)                      # up to his chest
        self.end = self.lift[1] + 0.3

    # --- the ball
    def _dribble(self, t):
        u = (t - self.t0) % self.T
        if u < self.t_dn:
            return self.top + self.vp * u + 0.5 * GBALL * u * u
        u -= self.t_dn
        return self.low - self.v_up * u + 0.5 * GBALL * u * u

    def pos(self, t, wheels_hand=None):
        """(x, y, held_by) of the ball's centre at t (world)."""
        if t < self.t0:                                                     # in Springs' hand / on the step
            return self.bx, self.top, "Springs' right hand"
        if t < self.away + self.t_dn:
            return self.bx, self._dribble(t), ("Springs' right hand" if self._dribble(t) < self.top + 4 else None)
        for t0, x0, vx, vy, dur in self.arcs:
            if t < t0 + dur:
                u = t - t0
                return x0 + vx * u, self.low + vy * u + 0.5 * GBALL * u * u, None
        tr, xr, vr = self.roll0
        if t < self.rest_t:
            u = t - tr
            return xr + vr * u - 0.5 * self.decel * u * u, self.low, None
        if t < self.grab[1] or wheels_hand is None:
            return self.rest_x, self.low, None
        hx, hy = wheels_hand(t)
        return hx, hy + BALL_R - 2, "Wheels' right pincer"

    def spin(self, t):
        """Its turn (rad): it rolls the way it goes."""
        x = self.pos(t)[0]
        return (x - self.bx) / BALL_R

    def springs_hand(self, t):
        """Springs' right hand target (world) while he dribbles (None: his own swing)."""
        if t < self.pick - 0.6 or t > self.away + self.t_dn + 0.8:
            return None
        if t < self.t0:
            return self.hand
        if t < self.away + self.t_dn:
            y = self._dribble(t) - BALL_R
            return self.hand[0], min(max(y, self.hand[1] - 6), self.hand[1] + 16)
        u = _seg(t, self.away + self.t_dn, self.away + self.t_dn + 0.8)
        return self.hand[0], self.hand[1] - 4 * math.sin(math.pi * u)

    def wheels_keys(self):
        return [(self.w_go, self.WX), (self.w_at, self.catch_x)]

    def wheels_hand(self, t, x):
        """Wheels' right pincer (world) during the catch, then holding the ball at his chest."""
        if t < self.grab[0] - 0.5:
            return None
        ball = (self.rest_x, self.low - BALL_R + 2)        # the pincer takes it from the top
        chest = (x + 112.0, G - 192.0)
        if t < self.grab[1]:
            u = smoothstep(_seg(t, self.grab[0] - 0.5, self.grab[0] + 0.2))
            rest = (x + 124.4, G - 65.8)
            return rest[0] + (ball[0] - rest[0]) * u, rest[1] + (ball[1] - rest[1]) * u
        if t < self.lift[1]:
            u = smoothstep(_seg(t, *self.lift))
            return ball[0] + (chest[0] - ball[0]) * u, ball[1] + (chest[1] - ball[1]) * u
        return chest

    def things(self, t, sh, wheels_hand):
        x, y, held = self.pos(t, wheels_hand)
        h = None
        if held == "Springs' right hand":
            h = (held, (self.hand[0] - sh, y - BALL_R))
        elif held is not None:
            hx, hy = wheels_hand(t)
            h = (held, (hx - sh, hy))
        moving = "rolls" if self.away <= t < self.rest_t + 0.2 else ("falls" if self.t0 <= t < self.away + 0.3
                                                                     else None)
        return {"Springs' wooden ball": sc.Thing(x - sh, y, BALL_R, held=h if moving is None else None, moves=moving)}

    def draw(self, pg, t, sh, wheels_hand):
        from .marble_flat_course import draw_marble
        x, y, _ = self.pos(t, wheels_hand)
        if y > self.low - 30:                                               # its shadow on the path
            pg.flat(oval(x - sh, GROUND + 2, BALL_R * 0.9, 4), (60, 50, 40), 0.18)
        draw_marble(pg, x - sh, y, BALL_R, WOOD_BALL, ang=self.spin(t), band=True)

    def springs_squash(self, t):
        """Springs bobs on his springs with each pat."""
        if not (self.t0 <= t < self.away + self.t_dn):
            return 0.0
        u = ((t - self.t0) % self.T) / self.T
        return 0.12 * math.sin(2 * math.pi * u) ** 2

    def draw_at(self, pg, x, y, spin):
        """The ball at screen (x, y): its shadow on the path while it is down there."""
        from .marble_flat_course import draw_marble
        if y > self.low - 30:
            pg.flat(oval(x, GROUND + 2, BALL_R * 0.9, 4), (60, 50, 40), 0.18)
        draw_marble(pg, x, y, BALL_R, WOOD_BALL, ang=spin, band=True)
