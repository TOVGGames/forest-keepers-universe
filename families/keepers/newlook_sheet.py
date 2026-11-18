"""New-look sheets for the Forest Keepers (episode 9, docs/engines/forest_keepers_tune_up.md), for the owner and
Toby to approve before the episode is built.

    python -m families.keepers.newlook_sheet <out_dir>

Writes 1_before_after.jpg, 2_hans.jpg, 3_twigs.jpg, 4_all_six.jpg, 5_asleep_and_orbs.jpg.
"""
import os
import sys

import cv2
import numpy as np

from engine.canvas import Canvas
from engine.core import FORMATS
from families.foundry.products.monster import ORB, STEEL, PUPIL, Monster, badge, orb
from families.foundry.style import BG, FLOOR, HeatGlow

T = 1.3          # idle time (eyes open, no blink)
INK = (214, 208, 196)
DIM = (150, 146, 138)


def page(title, floor=None):
    cv = Canvas(FORMATS["hd"], glow=0.0, grain=1.0, background=BG, vignette=0.4)
    cv.begin()
    glow = HeatGlow(cv, 1.0, 1.1)
    if floor:
        for y in floor:
            cv.polygon([(0, y), (cv.w, y), (cv.w, y + 26), (0, y + 26)], FLOOR)
    cv.text(title, cv.w / 2, 52, 40, INK)
    return cv, glow


def save(cv, glow, path):
    glow.apply(cv)
    cv2.imwrite(path, cv2.cvtColor(cv.finish(0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    return path


def keeper(kind, x, y, k, new=True, **kw):
    m = Monster(kind, k=k)
    m.x, m.y = x, y
    m.newlook = new
    if kind == "teeth":
        m.saws = True
    if not new:
        m.badge = 1.0
    for a, v in kw.items():
        setattr(m, a, v)
    return m


def before_after(path):
    cv, glow = page("HANS AND TWIGS: BEFORE  ->  AFTER", floor=[990])
    w = cv.w
    for i, (kind, new, label) in enumerate([("tentacles", False, "Hans before"), ("tentacles", True, "Hans after"),
                                            ("teeth", False, "Twigs before"), ("teeth", True, "Twigs after")]):
        x = (225, 685, 1200, 1680)[i]
        m = keeper(kind, x, 990, 0.82 if kind == "tentacles" else 1.08, new)
        m.draw(cv, T, glow)
        cv.text(label, x, 1045, 30, INK if new else DIM)
    cv.line(w / 2, 110, w / 2, 1060, (60, 64, 76), 3)
    return save(cv, glow, path)


EXPR = [("smiling", {}), ("laughing", {"smile": 1.0, "talk": 0.75, "cheek": 0.38, "brow": 0.6}),
        ("ooh!", {"smile": -0.8, "brow": 1.0, "attend": 1.0}), ("sleepy", {"smile": 0.3, "lid_top": 0.55,
                                                                        "brow": -0.3})]


def expressions(path, kind, name, k):
    cv, glow = page(f"{name.upper()}: NEW FACE, A FEW EXPRESSIONS", floor=[1000])
    for i, (label, kw) in enumerate(EXPR):
        x = cv.w * (i + 0.5) / 4
        keeper(kind, x, 1000, k, True, **kw).draw(cv, T, glow)
        cv.text(label, x, 1052, 30, INK)
    return save(cv, glow, path)


def all_six(path):
    cv, glow = page("ALL SIX, NEW LOOK: NO PINNED BADGE (GLO'S AND DIGS' ORBS ARE FLASHING)",
                    floor=[960])
    for i, kind in enumerate(Monster.KINDS):
        x = cv.w * (i + 0.5) / 6
        m = keeper(kind, x, 960, 0.72, True, flash=1.0 if kind in ("lantern", "digger") else 0.0)
        m.draw(cv, T, glow)
        m.draw_name(cv, 1.0)
    return save(cv, glow, path)


def asleep_and_orbs(path):
    cv, glow = page("ORB OUT: PALE AND ASLEEP   |   ORB IN: THE BADGE FLASH", floor=[560])
    for i, kind in enumerate(Monster.KINDS):
        x = cv.w * (i + 0.5) / 6
        keeper(kind, x, 560, 0.5, True, alive=0.0, orb_in=0.0).draw(cv, T, glow)
    cv.text("orbs out: grey wood, eyes shut, still; the empty sockets wait for the orbs", cv.w / 2, 615, 26, DIM)
    # the flash, step by step, then the three badges
    steps = [0.0, 0.35, 0.7, 1.0]
    for i, f in enumerate(steps):
        x, y = 200 + i * 230, 820
        orb(cv, x, y, 62, None, 1.0, T, 1.0, f, "keeper")
        cv.text(f"{'orb' if f == 0 else 'flash' if f == 1 else ''}", x, 950, 26, DIM)
    cv.text("the flash: about a second when the orb goes in, then now and then while they work", 530, 1010, 24, DIM)
    for i, job in enumerate(("keeper", "loaf", "snow")):
        x, y = 1260 + i * 220, 820
        orb(cv, x, y, 62, None, 1.0, T, 1.0, 1.0, job)
        cv.text({"keeper": "Forest Keeper", "loaf": "baking", "snow": "winter jobs"}[job], x, 950, 26, INK)
    cv.text("one badge per job", 1480, 1010, 24, DIM)
    return save(cv, glow, path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "docs/engines/forest_keepers_newlook"
    os.makedirs(out, exist_ok=True)
    print(before_after(os.path.join(out, "1_before_after.jpg")))
    print(expressions(os.path.join(out, "2_hans.jpg"), "tentacles", "Hans", 0.82))
    print(expressions(os.path.join(out, "3_twigs.jpg"), "teeth", "Twigs", 1.08))
    print(all_six(os.path.join(out, "4_all_six.jpg")))
    print(asleep_and_orbs(os.path.join(out, "5_asleep_and_orbs.jpg")))
