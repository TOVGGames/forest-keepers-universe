"""The talking format's cast (owner 2026-11-17), from the production drawing code.

- No orbs on any Keeper ("Remove the orb, remove the orb from all of them"): Monster.orbless. Sprout has no tummy
  socket or rim, Glo no orb on her dome, Digs his plain hard hat with its little lamp, turning with his head.
- Sprout's mouth is a closed little smile at rest (SPROUT_SMILE): "Sprout never closes his mouth, which is weird".
- Springs is a sitting frog (legs A, face 2, the wide frog smile): frog_springs(). He is not a Monster: he is drawn
  whole here. His limbs are bones of a set length: arm 47 units, thigh and foot fixed shapes.
- Glo has no mouth; she talks with her lantern.
Ported from the Creative Director's prototype (experiments/forest_keepers_talk/cast.py), which the owner watched.
"""
import math

import numpy as np

from engine.core import hex_rgb
from families.foundry.products import monster as M
from families.keepers import illustrate as il

KINDS = {"sprout": "sprout", "glo": "lantern", "digs": "digger", "springs": "springs"}   # name -> drawing kind
SPROUT_SMILE = 0.1

COL = np.asarray(hex_rgb(M.COLORS["springs"]), np.float64)
BELLY = np.array([240, 214, 150.0])
DARK = np.array([92, 60, 40.0])                # mouth line: a deep warm brown, never black
BODY_UP = 100.0                                # the middle of his body above the ground, sitting (monster units)
ARM = 47.0


def figure(pg, who, x, y, k, **attrs):
    """One Keeper of the talking format at feet (x, y), size k. who: sprout, glo, digs (Springs: frog_springs)."""
    kind = KINDS.get(who, who)
    assert kind != "springs", "Springs is a frog now: frog_springs()"
    attrs["orbless"] = True
    if kind == "digger":
        attrs["hat_orb"] = False
    if kind == "sprout":
        attrs.setdefault("smile", SPROUT_SMILE)
        attrs.setdefault("acorn", False)
    return il.figure(pg, kind, x, y, k, 6, **attrs)


def _foot(cv, ax, ay, sx, k, ground):
    tips = [(ax + sx * 62 * k, ground - 6 * k), (ax + sx * 50 * k, ground - 24 * k), (ax + sx * 22 * k, ground - 4 * k)]
    cv.polygon([(ax, ay - 8 * k), tips[1], tips[0], tips[2], (ax - sx * 6 * k, ay + 6 * k)], COL * 0.6)
    for tx, ty in tips:
        cv.line(ax, ay, tx, ty, COL * 0.66, 13 * k)
        cv.circle(tx, ty, 8.5 * k, COL * 0.72)


def frog_springs(pg, x, ground, k, look=(0.0, 0.0), blink=0.0, talk=0.0, lift=0.0, squash=0.0, arms=(None, None),
                 shadow=True):
    """Springs, the sitting frog, at (x, ground). lift: how far his body is off the ground (a hop; the legs come with
    him), squash 0..1: crouched. arms: (left, right) angles in rad (0 = +x, y down), None = resting at his side.
    talk 0..1: how open his wide frog smile is; the tongue only shows when it is open wide enough to hold it."""
    by = ground - (BODY_UP - 14 * squash) * k - lift
    ry = 88 * (1 - 0.06 * squash) * k
    rx = 110 * (1 + 0.05 * squash) * k

    def draw(cv):
        cv.eye_scale = 1.15
        for sx in (-1, 1):                                       # legs: folded thighs, webbed feet out to the sides
            cv.ellipse(x + sx * 94 * k, by + 56 * k, 50 * k, 38 * k, COL * 0.74, angle=sx * 18)
            _foot(cv, x + sx * 104 * k, by + 86 * k, sx, k, by + 100 * k)
        for i, sx in enumerate((-1, 1)):                         # stubby arms, three fingers, a set length
            sh = (x + sx * 96 * k, by + 12 * k)
            ang = arms[i] if arms[i] is not None else math.atan2(18, sx * 44)
            hd = (sh[0] + math.cos(ang) * ARM * k, sh[1] + math.sin(ang) * ARM * k)
            cv.line(*sh, *hd, COL * 0.82, 16 * k)
            for f in (-1, 0, 1):
                fa = ang + f * 0.5
                cv.line(*hd, hd[0] + math.cos(fa) * 15 * k, hd[1] + math.sin(fa) * 15 * k, COL * 0.68, 6 * k)
        ex, ey, er, br = 46, 72, 30, 40
        for sx in (-1, 1):                                       # the bumps his eyes sit on
            cv.circle(x + sx * ex * k, by - ey * k, br * k, COL)
        cv.polygon(M.ellipse(x, by, rx, ry, 56), COL)            # head and body in one
        cv.polygon(M.ellipse(x, by + 44 * k, 62 * k, 36 * k, 40), BELLY)      # a pale frog tummy
        for sx in (-1, 1):
            M.eye(cv, x + sx * ex * k, by - (ey + 4) * k, er * k, look, blink, None, 1.0, COL, 0.0, 0.5)
            M.blush(cv, x + sx * 70 * k, by - 2 * k, k, COL, 1.0)
        pts = [(x + u * 66 * k, by - 6 * k + 15 * k * (1 - u * u)) for u in np.linspace(-1, 1, 21)]
        if talk > 0.04:                                          # the wide frog smile opens downward
            low = [(x + u * 56 * k, by - 6 * k + (15 + 30 * talk) * k * (1 - u * u)) for u in np.linspace(1, -1, 21)]
            cv.polygon(pts[2:-2] + low[2:-2], M.MOUTH)
            gap = 30 * talk * k                                  # the opening's height in the middle
            if talk > 0.3:                                       # owner on Proof B: never "stuck on the outside of his
                grow = min(1.0, (talk - 0.3) / 0.25)             # closed mouth": only once it fits, wholly inside
                cv.polygon(M.ellipse(x + 6 * k, by + 9 * k + gap * 0.66, 20 * k * grow, gap * 0.26 * grow, 20),
                           M.TONGUE)
        cv.polyline(pts, DARK, 5 * k)
        for q in (pts[0], pts[-1]):
            cv.circle(q[0], q[1] - 2 * k, 4.5 * k, DARK)

    il.creature(pg, draw, x, ground, shadow=(150 * k * max(0.45, 1 - lift / (260 * k))) if shadow else None, style=6,
                mute_amount=il.KEEPER_MUTE)


def sheet(path):
    """The cast as the format draws them (to check against the Creative Director's sheets), then Digs' hat turning
    and Springs talking."""
    from PIL import Image
    from families.keepers import flat
    pg = flat.FlatPage(1920, 1080)
    flat.autumn_hills(pg, house=None)
    figure(pg, "sprout", 300, 950, 1.0, t=1.3)
    figure(pg, "glo", 700, 930, 1.0, t=1.3)
    figure(pg, "digs", 1110, 950, 1.0, t=1.3)
    frog_springs(pg, 1560, 950, 0.9, look=(-0.3, 0.1))
    Image.fromarray(pg.finish()).save(path)
    pg = flat.FlatPage(1920, 1080)
    flat.autumn_hills(pg, house=None)
    for i, tr in enumerate((-1.0, -0.5, 0.0, 0.5, 1.0)):
        figure(pg, "digs", 230 + i * 365, 640, 0.8, t=1.3, turn=tr)
    for i, tk in enumerate((0.0, 0.2, 0.45, 0.9)):
        frog_springs(pg, 300 + i * 440, 1040, 0.6, talk=tk)
    Image.fromarray(pg.finish()).save(path.replace(".png", "_turn_talk.png"))
