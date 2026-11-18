"""Shared pieces for Forest Keepers acts: night sky, forest ground, wooden signs, particles, timing
helpers. Colours and the tree / log / saw drawings come from the episode 1 scene so both episodes
look the same."""
import math

import numpy as np

from ..products.monster import Xform, ellipse
from ..style import lighten, smoothstep, smootherstep, settle
from ..tree_monsters import (BG, BARK, EARTH, EARTH_DARK, GRASS, GREEN, LAMP, LEAF, LEAF_FAR, MOON, SAWDUST,
                             SKY_STAR, TRUNK, Particle, lerp, machine_block, rect, saw_blade, seg, tree)

__all__ = ["BG", "BARK", "EARTH", "EARTH_DARK", "GRASS", "GREEN", "LAMP", "LEAF", "LEAF_FAR", "MOON",
           "SAWDUST", "SKY_STAR", "TRUNK", "Particle", "lerp", "machine_block", "rect", "saw_blade", "seg",
           "tree", "Xform", "ellipse", "lighten", "smoothstep", "smootherstep", "settle", "Act", "Particles", "Jump",
           "GRAVITY",
           "Night", "wood_sign", "WATER", "WATER_DEEP", "PLANK", "SOIL", "SOIL_WET", "bunny", "hedgehog"]

WATER = np.array([40, 74, 110], np.float64)
WATER_DEEP = np.array([22, 40, 66], np.float64)
PLANK = np.array([150, 112, 72], np.float64)
SOIL = np.array([58, 42, 32], np.float64)
SOIL_WET = np.array([38, 28, 24], np.float64)
SIGN_WOOD = np.array([120, 86, 54], np.float64)
SIGN_TEXT = np.array([240, 226, 196], np.float64)


GRAVITY = 2600.0     # scene units / s^2, the same g the factory's falling logs use


class Jump:
    """Ballistic hop from (x0, y0) to (x1, y1) peaking `apex` above the higher end (y down).
    x moves at constant speed, y follows real gravity, so the flight time comes out of the heights."""

    def __init__(self, x0, y0, x1, y1, apex=90.0, g=GRAVITY):
        self.x0, self.y0, self.x1, self.y1, self.g = x0, y0, x1, y1, g
        top = min(y0, y1) - apex
        self.vy = math.sqrt(2 * g * (y0 - top))
        self.dur = self.vy / g + math.sqrt(2 * (y1 - top) / g)

    def at(self, tau):
        tau = min(max(tau, 0.0), self.dur)
        return lerp(self.x0, self.x1, tau / self.dur), self.y0 - self.vy * tau + 0.5 * self.g * tau * tau


class Act:
    """One part of the episode. Times passed to update/draw/target are local (0 = act start)."""
    name = "act"
    indoor = False                 # True: inside the factory (factory sound bed); False: the night forest

    def __init__(self, scene, P, t0):
        self.s = scene
        self.P = P
        self.t0 = t0
        self.dur = 10.0

    def target(self, t):
        """Camera (center x, center y, zoom)."""
        return 0.0, 0.0, 1.0

    def update(self, t, dt):
        pass

    def draw(self, c, t):
        pass

    # sound helpers in local time
    def hit(self, t, inst, note, vel, x, y):
        self.s.hit(self.t0 + t, inst, note, vel, x, y)

    def fx(self, t, name, dur, vel, x, y):
        self.s.fx(self.t0 + t, name, dur, vel, x, y)

    def crossed(self, at):
        return self.s.crossed(self.t0 + at)

    def say(self, t, kind, contour, x, y, vel=0.45):
        self.s.say(self.t0 + t, kind, contour, x, y, vel)


class Particles:
    def __init__(self, rng):
        self.rng = rng
        self.items = []

    def burst(self, x, y, n, col, speed, life, r, kind="dot", g=1400.0, up=0.0, glow=False, spread=math.pi,
              direction=-math.pi / 2):
        for _ in range(n):
            a = direction + self.rng.uniform(-spread, spread)
            sp = speed * self.rng.uniform(0.4, 1.0)
            self.items.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp - up,
                                       life * self.rng.uniform(0.6, 1.2), r * self.rng.uniform(0.6, 1.3),
                                       col, kind, g, glow))

    def leaves(self, x, y, n, spread=90):
        for _ in range(n):
            self.items.append(Particle(x + self.rng.uniform(-spread, spread), y + self.rng.uniform(-60, 60),
                                       self.rng.uniform(-220, 220), self.rng.uniform(-260, 40),
                                       self.rng.uniform(1.4, 2.6), self.rng.uniform(7, 13),
                                       LEAF[self.rng.integers(3)], "leaf", 260))

    def update(self, dt):
        alive = []
        for p in self.items:
            p.age += dt
            if p.age >= p.life:
                continue
            p.vy += p.g * dt
            if p.kind == "leaf":
                p.vx *= 1 - 1.5 * dt
                p.vy = min(p.vy, 120)
                p.x += math.sin(p.age * 5 + p.r) * 40 * dt
            elif p.kind == "firefly":
                p.vx += math.sin(p.age * 2.3 + p.r * 3) * 30 * dt
                p.vy += math.cos(p.age * 1.7 + p.r) * 20 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.items = alive

    def draw(self, c, glow_fn):
        for p in self.items:
            a = 1 - p.age / p.life
            if p.kind == "leaf":
                ang = p.age * 4 + p.r
                dx, dy = math.cos(ang) * p.r, math.sin(ang) * p.r * 0.5
                c.polygon([(p.x - dx, p.y - dy), (p.x + dy * 0.6, p.y - dx * 0.3), (p.x + dx, p.y + dy),
                           (p.x - dy * 0.6, p.y + dx * 0.3)], p.col * (0.4 + 0.6 * a))
            elif p.kind == "firefly":
                fl = 0.5 + 0.5 * math.sin(p.age * 6 + p.r * 5)
                f = min(1.0, p.age / 0.8) * min(1.0, (p.life - p.age) / 1.0) * fl
                c.circle(p.x, p.y, p.r * 0.5, p.col * (0.4 + 0.6 * f))
                glow_fn(lambda g, p=p, f=f: g.circle(p.x, p.y, p.r * 1.6, p.col * 0.7 * f))
            elif p.kind == "snow":                 # snow puffs shrink away instead of going grey
                c.circle(p.x, p.y, p.r * (0.3 + 0.7 * a), p.col)
            elif p.glow:
                glow_fn(lambda g, p=p, a=a: g.circle(p.x, p.y, p.r, p.col * a))
                c.circle(p.x, p.y, p.r * 0.7, p.col * a)
            else:
                c.circle(p.x, p.y, p.r, p.col * (0.3 + 0.7 * a))


class Night:
    """Outdoor night backdrop: stars + moon fixed-ish on screen, far tree line, ground slab."""

    def __init__(self, rng, ground, x0=-2000, x1=8000):
        self.ground = ground
        self.stars = [(rng.uniform(0, 4000), rng.uniform(0, 4000), rng.uniform(0.8, 2.2), rng.uniform(0.3, 1.0))
                      for _ in range(160)]
        self.far = [(rng.uniform(x0 - 3000, x1 + 3000), rng.uniform(0.6, 1.1)) for _ in range(int((x1 - x0 + 6000) / 120))]

    def draw(self, s, c, t, moon=True):
        cam_x, cam_y, w, h = s.cam_x, s.cam_y, s.w, s.h
        W, H = w + 200, h
        for sx, sy, r, b in self.stars:
            x = (sx - cam_x * 0.08) % W - 100 + cam_x
            y = (sy - cam_y * 0.08) % H + cam_y
            if y > self.ground - 200:
                continue
            tw = 0.75 + 0.25 * math.sin(t * 1.3 + sx)
            c.circle(x, y, r, SKY_STAR * b * tw * 0.6)
        if moon:
            mx, my = cam_x + w * 0.8, cam_y + h * 0.14
            if my < self.ground - 200:
                c.circle(mx, my, 62, MOON * 0.85)
                c.circle(mx - 16, my - 12, 14, MOON * 0.7)
                c.circle(mx + 20, my + 16, 9, MOON * 0.72)
                s.glow_draw(lambda g: g.circle(mx, my, 72, MOON * 0.28))
        G = self.ground
        vx0, vx1 = s.view()[:2]
        for fx_, sc in self.far:
            x = fx_ + cam_x * 0.4
            if x < vx0 - 300 or x > vx1 + 300:
                continue
            hh = 380 * sc
            c.polygon([(x - 14, G), (x + 14, G), (x + 10, G - hh * 0.5), (x - 10, G - hh * 0.5)], LEAF_FAR)
            c.circle(x, G - hh * 0.72, hh * 0.28, LEAF_FAR)
            c.circle(x - hh * 0.15, G - hh * 0.6, hh * 0.2, LEAF_FAR)
            c.circle(x + hh * 0.16, G - hh * 0.62, hh * 0.21, LEAF_FAR)

    def ground_slab(self, s, c, x0=None, x1=None):
        G = self.ground
        vx0, vx1 = s.view()[:2]
        L = vx0 - 300 if x0 is None else max(x0, vx0 - 300)
        R = vx1 + 300 if x1 is None else min(x1, vx1 + 300)
        if R <= L:
            return
        rect(c, L, G, R, G + 2500, EARTH)
        for y in np.arange(G + 60, G + 1200, 90):
            c.line(L, y + 10 * math.sin(y), R, y - 10 * math.sin(y * 0.7), EARTH_DARK, 3)
        rect(c, L, G - 6, R, G + 4, GRASS)


def wood_sign(c, x, ground, text, size=46, lit=0.0, glow_fn=None):
    """Wooden mission sign on two posts, carved text. `lit` 0..1: a little lamp on top."""
    tw = len(text) * size * 0.66 + 70
    top = ground - 260
    for px in (x - tw * 0.32, x + tw * 0.32):
        rect(c, px - 9, top + 60, px + 9, ground, TRUNK)
    pts = [(x - tw / 2, top), (x + tw / 2 - 18, top), (x + tw / 2 + 14, top + 45), (x + tw / 2 - 18, top + 90),
           (x - tw / 2, top + 90)]
    c.polygon(pts, SIGN_WOOD)
    c.polyline(pts, SIGN_WOOD * 0.6, 3, closed=True)
    for yy in (top + 30, top + 62):
        c.line(x - tw / 2 + 8, yy, x + tw / 2 - 30, yy, SIGN_WOOD * 0.85, 2)
    c.text(text, x - 8, top + 46, size, SIGN_TEXT)
    if lit > 0 and glow_fn is not None:
        c.circle(x - tw / 2 + 4, top - 8, 9, LAMP * (0.4 + 0.6 * lit))
        glow_fn(lambda g: g.circle(x - tw / 2 + 4, top - 8, 30, LAMP * 0.5 * lit))


def bunny(c, x, y, s=1.0, hop=0.0, face=1, col=None):
    """Little forest bunny, side view; (x, y) = feet. `hop` lifts it."""
    col = np.array([150, 138, 124]) if col is None else col
    y = y - hop
    c.polygon(ellipse(x, y - 22 * s, 30 * s, 20 * s, 24), col)
    c.circle(x + face * 24 * s, y - 38 * s, 15 * s, col)
    for e in (-1, 1):
        ex = x + face * (20 + e * 4) * s
        c.polygon(ellipse(ex, y - 66 * s, 5 * s, 18 * s, 14), col * 0.95)
        c.polygon(ellipse(ex, y - 64 * s, 2.5 * s, 12 * s, 10), np.array([200, 150, 150]))
    c.circle(x - face * 30 * s, y - 26 * s, 7 * s, np.array([220, 214, 204]))
    c.circle(x + face * 30 * s, y - 41 * s, 2.6 * s, np.array([20, 20, 24]))
    c.polygon(ellipse(x + face * 12 * s, y - 4 * s, 12 * s, 5 * s, 12), col * 0.85)


def hedgehog(c, x, y, s=1.0, face=1, t=0.0):
    body = np.array([90, 70, 54])
    spikes = []
    for i in range(13):
        a = math.pi + i * math.pi / 12
        r = (34 if i % 2 else 24) * s
        spikes.append((x - face * 4 * s + math.cos(a) * r * 1.2, y - 16 * s + math.sin(a) * r))
    c.polygon(spikes + [(x + face * 30 * s, y - 4 * s), (x - face * 34 * s, y - 4 * s)], body * 0.8)
    c.polygon(ellipse(x + face * 26 * s, y - 12 * s, 16 * s, 10 * s, 16), np.array([170, 140, 110]))
    c.circle(x + face * 40 * s, y - 13 * s, 3.5 * s, np.array([20, 20, 24]))
    c.circle(x + face * 28 * s, y - 17 * s, 2.5 * s, np.array([20, 20, 24]))
