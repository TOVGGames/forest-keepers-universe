"""Episode 1, "How the Forest Keepers Began": the six chapters as film (script approved by the owner as written,
2026-11-17; docs/engines/forest_keepers_talk_ep1_script.md). Every stage direction in the script is here as a move,
a look or a light; the voices are ep1.py's (cached, so this costs no credits).

    PY = .venv\\Scripts\\python.exe
    PY -m families.keepers.talk.ep1_film --check                 # talkcheck + overlaps, every frame
    PY -m families.keepers.talk.ep1_film --still 1:30 3:75 ...    # chapter:second stills (scratch dir)
    PY -m families.keepers.talk.ep1_film --sheet                  # one still every few seconds, as contact sheets
    PY -m families.keepers.talk.ep1_film --render                 # the episode (Idle priority by day)
"""
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia

from engine.log import ROOT
from families.keepers.storybook import C, rrect
from families.keepers import harvest_flat_world as HW
from families.keepers.talk import anim, places
from families.keepers.talk.anim import FPS, H, W, Chapter, card, glow, sun_pool, text
from families.keepers.talk.ep1 import OUT as VOICES
from families.keepers.talk.mix import SR, ease

TITLE = "How the Forest Keepers Began"
NAME = "keepers_began"
SHARED = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # this repo's root
FINAL_DIR = os.path.join(SHARED, "renders", "Forest Keepers")


# closer framings (a cut, with nobody moving, keeps everyone where they are): zoom about (cx, cy) to (sx, sy)
MED1 = dict(zoom=1.4, cx=900.0, cy=800.0, sx=960.0, sy=700.0)         # the acorn under the oak
CLOSE1 = dict(zoom=2.0, cx=1120.0, cy=800.0, sx=960.0, sy=580.0)       # Sprout, waking (the oak's root out of shot)
MED2 = anim.view(1.7, 1070, 990, 1000)                                 # Sprout and Springs at the pond
MED3 = anim.view(1.55, 1100, 990, 1010)                                 # the three by the molehills
CLOSE3 = anim.view(2.4, 600, 992, 1000)                                # Sprout: "So... I'm a tree?"
MED4 = anim.view(1.55, 1060, 976, 1005)                                # the three at sunset
MED4G = anim.view(1.22, 895, 990, 985)                                  # the four, once Glo is there
OAK5 = dict(zoom=2.4, cx=430.0, cy=450.0, sx=960.0, sy=540.0)          # the oak: nest, squirrel's hole, moths
CLOSE6 = dict(zoom=1.35, cx=1150.0, cy=760.0, sx=960.0, sy=723.0)      # the four at the foot of the oak (hole out)
GLO5 = anim.view(2.6, 478, 955, 1000)                                  # Glo by the oak: "That's my secret."
TIGHT6 = anim.view(1.5, 1206, 965, 1000)                              # closer on the four: who looks after what


# ===================================================================================================== chapter 1
class Ch1(Chapter):
    """Under the Old Oak, early spring morning: the acorn wakes as the sun reaches it."""
    place, light, title, lead = "oak", "morning", "Under the Old Oak", 5.0
    SPROUT = (1040.0, 990.0)

    def plan(self):
        c = self.c
        s = self.add("sprout", *self.SPROUT)
        self.sun0, self.sun1 = c(1)["end"] + 0.2, c(1)["end"] + 3.4
        s.sleep.v0, s.fold.v0 = 1.0, 0.9
        s.sleep.to(self.sun1 - 0.2, 0.0, 0.5)
        self.shots += [(c(0)["start"] + 4.0, MED1),                        # nearer the sleeping acorn
                       (self.sun1 - 0.6, CLOSE1)]                          # in close as its eyes open
        s.fold.to(self.sun1 + 0.4, -0.1, 2.0)
        s.look(c(2)["start"] - 0.3, c(2)["end"], (-0.6, -0.1))
        s.look(c(3)["start"] - 0.2, c(3)["end"], (0.6, -0.1))
        s.look(c(3)["end"], c(4)["start"] - 0.2, (0.35, -0.6))           # listening to the birds
        s.look(c(4)["start"] - 0.2, c(4)["end"], (0.1, 0.6))               # the wet leaves at its feet
        s.look(c(4)["end"], c(5)["start"] + 3.6, (0.0, -0.85))             # "leaves on my head"
        s.look(c(5)["start"] + 3.6, c(5)["end"] + 0.6, (0.0, 0.0))         # "what am I?" to us
        s.look(c(5)["end"] + 0.6, 1e9, (0.85, 0.15))                       # the croak, off to the right
        s.walk(c(6)["end"] + 0.5, 2080.0)
        self.until = self.gone("sprout", c(6)["end"] + 0.5)               # cut once it has walked out of the shot
        self.loops.append((self.sun0, self.until, "birdsong", 0.12))
        self.sfx += [(c(3)["end"] - 0.1, "birdsong", 0.4), (c(5)["end"] + 0.35, "croak", 0.8)]

    def scenery_over(self, pg, t, S, Z):                                    # the sunlight comes across the leaves,
        u = ease(t, self.sun0, self.sun1)                                   # on the ground, under the acorn
        if u > 0.001:
            x = 260 + (self.SPROUT[0] - 260) * u
            sun_pool(pg, *S(x, 1000), 460 * Z, 80 * Z, 0.5 * u)
        for t0, y0, sc in ((0.8, 250.0, 1.0), (1.5, 300.0, 0.85)):          # two birds fly over the quiet meadow
            u = (t - t0) / 9.0
            if 0.0 < u < 1.0:
                X, Y = S(2000 - 2100 * u, y0 - 60 * math.sin(math.pi * u) + 6 * math.sin(t * 9))
                HW.bird(pg, X, Y, -1, t, HW.BIRD_COLS[0], flap=0.5 + 0.5 * math.sin(t * 16 + t0), s=sc * Z)

    def light_extra(self, pg, t, S, Z):
        u = ease(t, self.sun0, self.sun1)
        if u < 0.999:                                                      # before the sun: the cool of early morning
            pg.c.drawPaint(skia.Paint(Color=C("#b6bed4", 0.32 * (1 - u)), BlendMode=skia.BlendMode.kMultiply))
        if u > 0.001:                                                      # and a little warmth on the acorn itself
            glow(pg, *S(self.SPROUT[0], 900), 160 * Z, 0.12 * ease(t, self.sun1 - 0.6, self.sun1 + 0.6))

    def overlay(self, pg, t):
        a = ease(t, 0.5, 1.3) * (1 - ease(t, 3.9, 4.7))
        if a > 0.01:
            pg.flat(rrect(W / 2 - 520, 150, W / 2 + 520, 290, 30), (40, 28, 24), 0.16 * a, blur=12)
            pg.flat(rrect(W / 2 - 512, 140, W / 2 + 512, 280, 30), anim.PAPER, 0.9 * a)
            text(pg, TITLE, W / 2, 232, 64, a=a)


# ===================================================================================================== chapter 2
class Ch2(Chapter):
    """The Pond: Springs wakes; Sprout gets its name; a hop and a bounce; off they go."""
    place, light, title = "pond", "morning", "The Pond"
    extra = {9: 1.3}

    def plan(self):
        c = self.c
        f = self.add("springs", 1210.0, 995.0)
        s = self.add("sprout", -90.0, 985.0)
        s.walk(0.3, 720.0)
        s.look(0.0, 5.6, (0.7, 0.0))
        self.shots.append((c(1)["start"] + 0.4, MED2))
        f.sleep.v0 = 1.0
        f.yawn.to(1.6, 0.85, 0.8).to(3.1, 0.0, 0.8)
        f.sleep.to(3.6, 0.0, 0.4)
        f.look(3.6, c(1)["start"] + 3.0, (0.1, -0.8))                    # "Good morning, sun! ... sky!"
        f.point.to(c(7)["start"] + 0.2, 1.0, 0.5).to(c(7)["start"] + 2.6, 0.0, 0.6)
        s.look(c(7)["start"] + 1.0, c(7)["start"] + 3.0, (0.05, -0.85))  # up at its own leaves
        self.cards += [(c(8)["start"] + 0.4, c(8)["start"] + 4.2, "sprout", "Sprout"),
                       (c(9)["start"] + 0.2, c(9)["start"] + 3.7, "springs", "Springs")]
        f.hop(c(9)["end"] + 0.25, 1420.0)                                  # "Watch!"
        s.bounce(c(9)["end"] + 1.5, 2)                                     # its feet hardly leave the ground
        s.look(c(9)["end"] + 0.2, c(9)["end"] + 1.4, "springs")
        s.look(c(9)["end"] + 1.4, c(9)["end"] + 2.5, (0.0, 0.5))
        f.hop(c(14)["start"] + 1.0, 2140.0, n=3)                           # Springs went first, of course
        s.walk(c(14)["end"] + 0.3, 2060.0)
        s.look(c(14)["end"] + 0.3, 1e9, (0.8, 0.0))
        self.until = self.gone("sprout", c(14)["end"] + 0.3)
        self.loops.append((0.0, self.until, "birdsong", 0.1))


# ===================================================================================================== chapter 3
class Ch3(Chapter):
    """The Molehills: Digs (who can't see well in daylight) smells the oak on Sprout. "So... I'm a tree?" """
    place, light, title = "molehills", "day", "The Molehills"
    extra = {4: 1.2}

    def plan(self):
        c = self.c
        d = self.add("digs", 1450.0, 985.0)
        f = self.add("springs", -150.0, 930.0)
        s = self.add("sprout", -200.0, 992.0)
        d.squint = 0.4                                                     # too bright up here
        f.hop(0.2, 1110.0, n=5)
        s.walk(1.6, 700.0)
        s.look(0.0, 6.8, (0.7, 0.0))
        self.cards.append((c(1)["start"] + 0.3, c(1)["start"] + 3.8, "digs", "Digs"))
        self.shots.append((c(2)["start"] - 0.3, MED3))
        s.walk(c(4)["end"] + 0.2, 820.0)                                   # "Come a little closer."
        sn0 = c(4)["end"] + 1.4
        d.look(sn0, c(5)["start"] - 0.1, lambda t: (-0.15, -0.55 + 0.1 * math.sin(t * 38)))   # sniff, sniff
        s.look(c(6)["start"] - 0.2, c(6)["start"] + 1.4, (-0.75, -0.5))  # the big one, back that way
        s.look(c(10)["start"] - 0.2, c(10)["start"] + 1.0, (0.05, 0.6))   # "So... I'm a tree?"
        self.shots += [(c(10)["start"] - 0.3, CLOSE3), (c(11)["end"] + 0.35, MED3)]
        f.hop(c(12)["start"] + 0.1, 1110.0)                                # "A tree with feet!"
        s.look(c(12)["end"] + 0.3, c(13)["start"] + 0.6, (-0.75, -0.65))  # up and away, toward the old oak
        s.fold.to(c(12)["end"] + 0.8, 0.5, 1.6)
        d.look(c(14)["end"] + 0.1, 1e9, "springs")                         # Digs and Springs look at each other
        f.look(c(14)["end"] + 0.3, 1e9, "digs")
        self.tail = 3.9
        self.loops.append((0.0, 1e9, "birdsong", 0.07))


# ===================================================================================================== chapter 4
class Ch4(Chapter):
    """The Meadow at Sunset: Springs promises ("Frog's honor"); the sun goes down; Glo floats in."""
    place, light, title = "sunset", "sunset", "The Meadow at Sunset"
    sky_sun = False
    GLO = (330.0, 1040.0)

    def plan(self):
        c = self.c
        g = self.add("glo", -280.0, 1000.0)
        self.add("springs", 700.0, 975.0)
        s = self.add("sprout", 1030.0, 978.0)
        self.add("digs", 1420.0, 975.0)
        s.fold.v0 = 0.5
        s.look(0.0, c(0)["end"], (0.1, 0.55))
        self.dusk0, self.dusk1 = c(6)["end"] + 0.6, c(6)["end"] + 8.6
        self.shots += [(c(1)["start"] - 0.25, MED4), (c(6)["end"] + 0.3, None), (c(8)["start"] - 0.25, MED4G)]
        g.float_to(c(6)["end"] + 5.0, c(7)["start"] - 0.6, *self.GLO)
        for who in ("springs", "sprout", "digs"):
            self.actors[who].look(c(6)["end"] + 5.4, c(7)["start"] - 0.1, "glo")
        g.look(c(6)["end"] + 5.0, c(7)["start"], "sprout")
        self.cards.append((c(9)["start"] + 0.3, c(9)["start"] + 3.8, "glo", "Glo"))
        self.tail = 1.6

    def lights(self, t):
        u = ease(t, self.dusk0, self.dusk1)
        return [("sunset", 1 - u), ("night", u)]

    def scenery_over(self, pg, t, S, Z):                                    # the sun goes down behind the far hill
        u = ease(t, self.dusk0 - 1.0, self.dusk1 - 2.0)
        if u < 0.999:
            places.setting_sun(pg, self.shot(t), u)

    def light_extra(self, pg, t, S, Z):
        u = ease(t, self.dusk0, self.dusk1)
        s = self.actors["glo"].pos(t)
        k = places.scale_at(s["y"])
        X, Y = S(s["x"], s["y"] - 190 * k)
        glow(pg, X, Y, 110 * k * Z, 0.12 + 0.3 * u)


# ===================================================================================================== chapter 5
NEST, HOLE, MOTHS, CROWN = ("pt", 553, 446), ("pt", 393, 638), ("pt", 350, 715), ("pt", 470, 330)


class Ch5(Chapter):
    """Night under the Old Oak: the peepers; who lives in the oak; "a squirrel planted me?" """
    place, light, title = "oak", "night", "Night under the Old Oak"
    extra = {13: 2.0}
    POS = {"glo": (720.0, 955.0), "springs": (980.0, 965.0), "sprout": (1262.0, 965.0), "digs": (1610.0, 965.0)}

    def plan(self):
        c = self.c
        a = {w: self.add(w, *p) for w, p in self.POS.items()}
        s = a["sprout"]
        s.fold.v0 = 0.5
        a["springs"].look(c(0)["start"] - 0.2, c(0)["end"], (0.85, -0.35))   # the peepers, far off
        self.lamp0 = c(1)["end"] + 0.5
        self.shots += [(c(2)["end"] + 0.2, OAK5), (c(3)["end"] + 0.2, CLOSE6), (c(7)["start"] - 0.2, None),
                       (c(8)["start"] - 0.2, CLOSE6), (c(15)["start"] - 0.3, GLO5)]
        a["glo"].lamp.to(self.lamp0, 1.6, 2.2)
        for w in a:                                                            # all look up into the oak
            a[w].look(c(1)["end"] + 1.2, c(2)["end"] if w != "sprout" else c(3)["start"], CROWN)
            a[w].look(c(7)["start"] + 0.3, c(7)["end"], CROWN)
        n = c(3)["start"]
        s.look(n - 0.1, n + 2.6, NEST).look(n + 2.6, n + 5.3, HOLE).look(n + 5.3, c(3)["end"] + 0.3, MOTHS)
        a["digs"].look(c(4)["start"] - 0.2, c(4)["end"], (0.1, 0.7))
        a["springs"].look(c(5)["start"] - 0.2, c(5)["end"], (0.85, 0.05))
        a["glo"].look(c(6)["start"] - 0.2, c(6)["end"], CROWN)
        a["springs"].hop(c(13)["start"] + 0.2, 980.0)                          # "Lucky us!"
        s.look(c(13)["end"] + 0.3, c(14)["start"] + 0.6, CROWN)                # a long look up at the big tree
        s.fold.to(c(13)["end"] + 0.9, -0.1, 1.8)
        self.loops.append((0.0, 1e9, "peepers", 0.22))
        self.tail = 1.6

    def scenery_over(self, pg, t, S, Z):
        places.oak_life(pg, self.marks, S, Z)

    def light_extra(self, pg, t, S, Z):
        g = self.actors["glo"]
        s = g.pos(t)
        k = places.scale_at(s["y"])
        X, Y = S(s["x"], s["y"] - 190 * k)
        lamp = g.lamp(t)
        glow(pg, X, Y, 110 * k * Z, 0.36)
        glow(pg, *S(470, 520), 320 * Z, 0.42 * (lamp - 1.0))                   # on the branches above
        glow(pg, *S(400, 680), 190 * Z, 0.14 + 0.25 * (lamp - 1.0))             # on the trunk
        if self.shot(t) is OAK5 or getattr(self, "oak_light", False):                                             # the close look: lit enough to read
            for (px, py), r in (((553, 446), 70), ((393, 638), 60), ((400, 560), 120)):
                glow(pg, *S(px, py), r * Z, 0.22)


# ===================================================================================================== chapter 6
class Ch6(Chapter):
    """The Forest Keepers: what each will look after; the name; sleep; the wide shot under the oak; the end sign."""
    place, light, close, title = "oak", "night", TIGHT6, "The Forest Keepers"
    POS = Ch5.POS

    def plan(self):
        c = self.c
        a = {w: self.add(w, *p) for w, p in self.POS.items()}
        self.wide = c(12)["start"] - 0.4
        self.shots += [(c(5)["start"] - 0.3, CLOSE6),                      # "Then we're keepers."
                       (self.wide, None)]                                  # small under the big tree and the stars
        a["digs"].sleep.to(c(11)["start"] + 1.2, 1.0, 1.2)                  # a little nap
        a["springs"].sleep.to(c(11)["end"] + 0.3, 1.0, 1.4)
        a["sprout"].fold.v0 = -0.1
        a["sprout"].fold.to(c(11)["end"] + 1.0, 0.85, 3.0)                   # its leaves fold down, slowly
        a["sprout"].sleep.to(c(11)["end"] + 2.4, 1.0, 1.6)
        a["glo"].look(c(11)["end"] + 0.6, 1e9, "sprout")
        a["glo"].lamp.v0 = 1.0
        a["glo"].lamp.to(self.wide, 0.8, 4.0)
        a["springs"].hop(c(6)["start"] + 0.1, 980.0)                          # "Forest Keepers!"
        self.sign0 = c(12)["end"] + 0.8
        self.tail = 9.6
        self.loops.append((0.0, 1e9, "peepers", 0.22))

    def scenery_over(self, pg, t, S, Z):
        places.oak_life(pg, self.marks, S, Z)

    def light_extra(self, pg, t, S, Z):
        g = self.actors["glo"]
        s = g.pos(t)
        k = places.scale_at(s["y"])
        X, Y = S(s["x"], s["y"] - 190 * k)
        glow(pg, X, Y, 110 * k * Z, 0.36 * g.lamp(t))
        glow(pg, *S(400, 680), 170 * Z, 0.1)

    def overlay(self, pg, t):
        a = ease(t, self.sign0, self.sign0 + 0.9)
        if a <= 0.01:
            return
        bw, bh = 1040, 230
        x0, y0 = (W - bw) / 2, 110
        pg.flat(rrect(x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10, 26), (40, 28, 24), 0.25 * a, blur=10)
        pg.flat(rrect(x0, y0, x0 + bw, y0 + bh, 26), (150, 108, 72), a)
        pg.flat(rrect(x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14, 18), (176, 132, 90), a)
        text(pg, "WHAT SHOULD THE KEEPERS DO NEXT?", W / 2, y0 + 110, 46, col=anim.PAPER, a=a)
        text(pg, "Tell us your idea in the comments", W / 2, y0 + 172, 36, col=(250, 232, 200), a=a,
             weight="Medium")


CHAPTERS = [Ch1, Ch2, Ch3, Ch4, Ch5, Ch6]


# ===================================================================================================== the episode
class Episode:
    DIP = 0.7                       # a soft dip through cream at every change of chapter

    def __init__(self):
        self.ch, self.T, t = [], [], 0.0
        for i, cls in enumerate(CHAPTERS, 1):
            ch = cls(i, VOICES, f"ep1_ch{i}")
            self.ch.append(ch)
            self.T.append(t)
            t += ch.dur
        self.end = t

    def at(self, t):
        for i in range(len(self.ch) - 1, -1, -1):
            if t >= self.T[i]:
                return i, t - self.T[i]
        return 0, t

    def frame(self, t):
        i, u = self.at(t)
        pg = self.ch[i].frame(u)
        d = min([abs(t - T) for T in self.T[1:]] + [9.0])
        dip = max(0.0, 1 - d / self.DIP)
        fade = min(ease(t, 0.0, 0.8), 1 - ease(t, self.end - 1.4, self.end), 1 - dip * dip * (3 - 2 * dip))
        if fade < 0.999:
            pg.c.drawPaint(skia.Paint(Color=skia.Color(250, 244, 234, int(255 * (1 - fade)))))
        return pg.finish()

    def cues(self):
        out = []
        for T, ch in zip(self.T, self.ch):
            out += [dict(c, start=c["start"] + T, end=c["end"] + T, chapter=ch.n) for c in ch.cues]
        return out

    # ------------------------------------------------------------------------------------------------- sound
    def audio(self, path):
        from families.curiosity.sfx import generate, load
        from families.keepers.talk import mix as MX
        from scipy.io import wavfile
        from scipy.signal import butter, sosfilt
        from families.keepers.talk.ep1 import SFX
        n = int((self.end + 0.5) * SR)
        v = np.zeros(n, np.float32)
        for T, ch in zip(self.T, self.ch):
            i = int(T * SR)
            m = min(len(ch.voices), n - i)
            v[i:i + m] += ch.voices[:m]
        fx = np.zeros(n, np.float32)
        lib = {}
        for name, (prompt, sec) in SFX.items():
            a = load(generate(prompt, sec))
            a = sosfilt(butter(2, [250, 6500], btype="band", fs=SR, output="sos"), a).astype(np.float32)
            fr = np.array([np.sqrt(np.mean(a[j:j + 882] ** 2)) for j in range(0, len(a) - 882, 882)])
            act = fr[fr > 0.25 * fr.max()]
            lib[name] = a / (np.sqrt(np.mean(act ** 2)) + 1e-9) * 0.085
        for T, ch in zip(self.T, self.ch):
            for t0, name, g in ch.sfx:
                a = lib[name] * g
                i = int((T + t0) * SR)
                fx[i:i + len(a)] += a[:max(0, n - i)]
            for t0, t1, name, g in ch.loops:
                t1 = min(t1, ch.dur)
                a = lib[name]
                i0, i1 = int((T + t0) * SR), int((T + t1) * SR)
                seg = np.tile(a, (i1 - i0) // len(a) + 2)[:i1 - i0] * g
                ramp = np.minimum(1, np.minimum(np.arange(len(seg)), np.arange(len(seg))[::-1]) / (1.2 * SR))
                fx[i0:i1] += seg * ramp
        cues = self.cues()
        theme_path = os.path.join(VOICES, "ep1_theme.wav")
        _, chords, folded = MX.theme(self.end, theme_path)
        music = _stereo(theme_path, n)
        voice = np.stack([v + fx, v + fx], 1)
        out, mask = MX.mix(voice, music, cues)
        wavfile.write(path, SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
        return mask, folded


def _stereo(path, n):
    from families.keepers.talk.voices import ffmpeg
    raw = subprocess.run([ffmpeg(), "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2)
    if len(a) < n:
        a = np.vstack([a, np.zeros((n - len(a), 2), np.float32)])
    return a[:n].copy()


# ===================================================================================================== checks
def check(ep, mask=None):
    from families.keepers.talk import check as TC
    total = 0
    for T, ch in zip(ep.T, ep.ch):
        frames = [(i / FPS, ch.state(i / FPS)) for i in range(int(ch.dur * FPS))]
        env = ch.mouths.env

        def said(who, t, ch=ch, env=env):
            return any(c["who"] == who and c["start"] <= t <= c["end"] for c in ch.cues) and \
                env[min(int(t * FPS), len(env) - 1)] > 0.25
        print(f"--- chapter {ch.n} {ch.title} ({ch.dur:.1f} s)")
        total += TC.run(frames, ch.cues, ch.cuts, places.scale_at, FPS, said=said)
        ov = [f"{t:.2f}s {p}" for t, st in frames[::3] for p in anim.overlap(st)]
        print(f"overlaps: {len(ov)}")
        for p in ov[:8]:
            print("   ", p)
        total += len(ov)
        ec = anim.edge_crops(ch)
        print(f"edge crops: {len(ec)}")
        for p in ec[:8]:
            print("   ", p)
        total += len(ec)
    if mask is not None:
        from families.keepers.talk.check import music
        mp = music(mask, ep.cues(), SR)
        print(f"music: {len(mp)}")
        total += len(mp)
    print(f"EPISODE CHECK TOTAL {total}")
    return total


# ===================================================================================================== render
_EP = None


def _init(idle):
    if idle:
        _idle()


def _work(i):
    global _EP
    if _EP is None:
        _EP = Episode()
    return _EP.frame(i / FPS).tobytes()


def _idle(pid=None):
    """Idle 7 AM - 9 PM, Below Normal overnight (owner rule), through the Windows API (no psutil in the venv)."""
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = k.OpenProcess.restype = ctypes.c_void_p
        k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        k.CloseHandle.argtypes = [ctypes.c_void_p]
        cls = 0x40 if 7 <= time.localtime().tm_hour < 21 else 0x4000     # IDLE / BELOW_NORMAL_PRIORITY_CLASS
        h = k.OpenProcess(0x0200 | 0x0400, False, pid) if pid else k.GetCurrentProcess()
        if not k.SetPriorityClass(h, cls):
            raise OSError(ctypes.GetLastError())
        if pid:
            k.CloseHandle(h)
    except Exception as e:                                           # never fail a render over priority
        print("priority not set:", e)


def render(workers=8):
    import multiprocessing as mp
    from engine import log
    from families.keepers.talk.voices import ffmpeg
    _idle()
    ep = Episode()
    vid = log.next_id("keepers", NAME)
    os.makedirs(FINAL_DIR, exist_ok=True)
    wav = os.path.join(VOICES, f"{vid}_mix.wav")
    mask, folded = ep.audio(wav)
    assert check(ep, mask) == 0, "talkcheck must be 0 before rendering"
    out = os.path.join(FINAL_DIR, f"{vid}.mp4")
    n = int(round(ep.end * FPS))
    p = subprocess.Popen([ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{ep.end:.3f}",
                          "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    _idle(p.pid)
    _idle()
    t0 = time.time()
    with mp.Pool(workers, initializer=_init, initargs=(True,)) as pool:
        for i, buf in enumerate(pool.imap(_work, range(n), chunksize=8)):
            p.stdin.write(buf)
            if i % 300 == 0:
                print(f"frame {i}/{n}  {time.time() - t0:.0f} s", flush=True)
    p.stdin.close()
    p.wait()
    log.write(dict(id=vid, family="keepers", status="rendered", file=out, title=TITLE,
                   params=dict(format="talk", episode=1, script="docs/engines/forest_keepers_talk_ep1_script.md",
                               chapters=[(c.n, c.title, round(c.dur, 2)) for c in ep.ch], fps=FPS, size=[W, H]),
                   seed=0, stats=dict(duration=round(ep.end, 2), audio_folded_notes=len(folded),
                                      summary=f"FK talk ep 1, {ep.end / 60:.1f} min")))
    print("WROTE", out, f"{ep.end:.1f} s in {time.time() - t0:.0f} s")
    return out


def stills(specs, out_dir):
    from PIL import Image
    ep = Episode()
    os.makedirs(out_dir, exist_ok=True)
    for sp in specs:
        n, s = sp.split(":")
        n, s = int(n), float(s)
        t = ep.T[n - 1] + s
        Image.fromarray(ep.frame(t)).save(os.path.join(out_dir, f"ch{n}_{s:05.1f}.png"))
    print("chapters:", ", ".join(f"{c.n} {c.dur:.1f}s" for c in ep.ch), f"total {ep.end:.1f}s")


def sheet(out_dir, every=4.0, per=12):
    from PIL import Image
    ep = Episode()
    os.makedirs(out_dir, exist_ok=True)
    for ch, T in zip(ep.ch, ep.T):
        ts = list(np.arange(0.4, ch.dur - 0.3, every))
        for b in range(0, len(ts), per):
            tiles = []
            for t in ts[b:b + per]:
                im = Image.fromarray(ep.frame(T + t)).resize((640, 360))
                tiles.append((t, im))
            sh = Image.new("RGB", (1920, 360 * ((len(tiles) + 2) // 3)), "white")
            from PIL import ImageDraw
            for j, (t, im) in enumerate(tiles):
                sh.paste(im, ((j % 3) * 640, (j // 3) * 360))
                ImageDraw.Draw(sh).text(((j % 3) * 640 + 8, (j // 3) * 360 + 6), f"ch{ch.n} {t:.1f}s", fill="black")
            sh.save(os.path.join(out_dir, f"sheet_ch{ch.n}_{b // per}.png"))
    print("chapters:", ", ".join(f"{c.n} {c.dur:.1f}s" for c in ep.ch), f"total {ep.end:.1f}s")


if __name__ == "__main__":
    scratch = os.environ.get("FK_SCRATCH", os.path.join(SHARED, "renders", "forest_keepers_talk", "ep1", "stills"))
    if "--check" in sys.argv:
        e = Episode()
        sys.exit(1 if check(e) else 0)
    if "--still" in sys.argv:
        stills(sys.argv[sys.argv.index("--still") + 1:], scratch)
    if "--sheet" in sys.argv:
        sheet(scratch)
    if "--render" in sys.argv:
        render()
