"""Stills for the owner: 1) three ideas for a 7th Forest Keeper, 2) Twigs' new hands with slide-out blades."""
import math
import os
import sys

sys.path.insert(0, os.getcwd())
import cv2
import numpy as np

from engine.canvas import Canvas
from engine.core import FORMATS
from families.foundry.products.monster import Monster
from families.keepers.seventh_keeper import IDEAS, draw_seventh

out1, out2 = sys.argv[1], sys.argv[2]
BG, GROUND, LAB, SUB = (44, 58, 52), (34, 44, 38), (232, 230, 216), (196, 204, 184)


def sheet():
    cv = Canvas(FORMATS["hd"], grain=0, vignette=0)
    cv.img[:] = BG
    cv.target = cv.img
    return cv


# ---- 1. the 7th Keeper ideas ----
cv = sheet()
G = 720
cv.polygon([(0, G), (1920, G), (1920, 1080), (0, 1080)], np.array(GROUND))
cv.text("A 7TH FOREST KEEPER?  THREE IDEAS", 960, 52, 46, LAB)
for i, kind in enumerate(("sprout", "whirly", "chime")):
    cx = 330 + i * 630
    d = IDEAS[kind]
    col = np.array([int(d["color"][j:j + 2], 16) for j in (1, 3, 5)], np.float64)
    cv.text(d["name"], cx, 122, 52, np.minimum(255, col * 0.7 + 90))
    cv.text(d["what"], cx, 170, 30, SUB)
    for q, ln in enumerate(d["lines"]):
        cv.text(ln, cx, G + 70 + q * 44, 27, SUB)
    if i:
        cv.line(cx - 315, 110, cx - 315, 1040, (60, 76, 68), 3)
K = 1.25
# a seedling for Sprout to water
sx0 = 250
draw_seventh(cv, "sprout", sx0, G, K, 0.6, water=1.0)
px = sx0 + 290
cv.polyline([(px, G), (px + 2, G - 40), (px - 1, G - 70)], np.array([96, 150, 70]), 5)
for a in (-0.9, 0.9, -0.3):
    cv.polygon([(px - 1, G - 70 + abs(a) * 30), (px + math.sin(a) * 30, G - 84 + abs(a) * 30 - 10),
                (px + math.sin(a) * 44, G - 74 + abs(a) * 30), (px + math.sin(a) * 18, G - 64 + abs(a) * 30)],
               np.array([82, 172, 92]))
cv.polygon([(px - 30, G + 4), (px + 30, G + 4), (px + 22, G - 6), (px - 22, G - 6)], np.array([70, 52, 38]))
draw_seventh(cv, "whirly", 960, G, K, 0.4, spin=0.06, lift=1.0)
draw_seventh(cv, "chime", 1570, G, K, 0.5, play=1.0, key=0.1)
cv.text("Toby can rename or change any of them", 960, 1048, 26, (150, 164, 150))
cv2.imwrite(out1, cv.img[:, :, ::-1])
print(out1)

# ---- 2. Twigs' new hands ----
cv = sheet()
G = 980
cv.polygon([(0, G), (1920, G), (1920, 1080), (0, 1080)], np.array(GROUND))
cv.text("TWIGS' NEW HANDS, WITH BLADES THAT SLIDE OUT", 960, 52, 44, LAB)
labels = [("Now: wrist saws", "(episodes 4-11)"), ("New: hands, blades in", "picks things up, waves, holds"),
          ("Blades out", "slide out past the hand to trim")]
for i, (a, b) in enumerate(labels):
    cx = 330 + i * 630
    cv.text(a, cx, 120, 40, LAB)
    cv.text(b, cx, 164, 28, SUB)
    if i:
        cv.line(cx - 315, 100, cx - 315, 1040, (60, 76, 68), 3)
for i in range(3):
    m = Monster("teeth", 1.12)
    m.newlook = True
    m.x, m.y = 330 + i * 630, G
    m.alive, m.orb_in, m.flash, m.job, m.pin = 1.0, 1.0, 0.0, "keeper", 0.0
    m.smile, m.cheek, m.attend = 0.8, 0.0, 1.0
    if i == 0:
        m.saws = True
    else:
        m.hands = True
        m.blades = 0.0 if i == 1 else 1.0
        m.punch = 0.55 if i == 2 else 0.25
        m.punch_l = 0.0 if i == 2 else 0.25
        m.grip = 0.0
    m.draw(cv, 0.0, None)
cv2.imwrite(out2, cv.img[:, :, ::-1])
print(out2)
