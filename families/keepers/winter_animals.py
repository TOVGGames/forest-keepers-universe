"""The animals getting ready for winter (episode 12, docs/engines/forest_keepers_winter_ready.md), drawn in code
in the same storybook-cute but true style as animals.py: soft round shapes, big shiny eyes, true markings and
poses, no speckles.

    draw_winter(c, kind, x, ground_y, s, t, face=1, **pose)   s = the animal's height scale in world units

Markings that make each one itself: the eastern chipmunk's black-and-white back stripes, striped face and the
cheek pouches it stuffs full; the beaver's flat scaly tail, orange front teeth and webbed hind feet; the Canada
goose's black head and neck with the white chinstrap; the groundhog's chunky brown body, dark feet and short bushy
tail; the black bear's black coat, tan muzzle and round ears; the black-capped chickadee's black cap and bib,
white cheeks and buff sides.
"""
import math

from families.keepers.animals import F, _c, cute_eye, spline, walk_leg

WINTER = {
    "chipmunk": dict(name="Eastern Chipmunk", line=["It carries seeds home in its stretchy", "cheek pouches and stores them underground."]),
    "beaver": dict(name="Beaver", line=["It pushes branches into the mud by", "its lodge, to eat under the ice all winter."]),
    "goose": dict(name="Canada Goose", line=["Many geese fly south in a V: each bird", "rides the air lifted by the one ahead."]),
    "groundhog": dict(name="Groundhog", line=["It hibernates all winter in its burrow,", "its heart beating only a few times a minute."]),
    "bear": dict(name="Black Bear", line=["It eats and eats all autumn, then", "sleeps the winter away in a cosy den."]),
    "chickadee": dict(name="Chickadee", line=["It stays all winter: it fluffs its feathers", "into a warm coat and remembers where it hid seeds."]),
}


# ----------------------------------------------------------------------------------------------- chipmunk

def chipmunk(c, x, y, s, t, face=1, pouch=0.0, nibble=0.0, blink=0.0, tail=0.0, seed=True, lean=0.0):
    """Eastern chipmunk sitting up, holding a seed in its front paws: rusty rump, grey-brown shoulders, a black-
    white-black stripe down its side and a dark stripe down the middle of its back, a striped face (white above and
    below the eye, dark through it), a pale belly, a furry tail held up behind. pouch 0..1 fills the cheeks."""
    f = F(x, y, s, face)
    RUST, GREYB, CREAM, WHITE, BLACK = _c(190, 116, 62), _c(160, 128, 100), _c(240, 226, 204), _c(246, 242, 232), _c(46, 34, 28)
    tw = 0.04 * math.sin(t * 1.6) + 0.06 * tail
    f.blob(c, [(-0.14, 0.06), (-0.3, 0.08), (-0.4, 0.24 + tw), (-0.38, 0.46 + tw), (-0.32, 0.46 + tw),
               (-0.3, 0.28 + tw * 0.5), (-0.16, 0.16)], GREYB * 0.78)             # furry tail, held up behind
    f.blob(c, [(-0.16, 0.09), (-0.28, 0.11), (-0.36, 0.26 + tw), (-0.35, 0.4 + tw), (-0.32, 0.27 + tw * 0.5),
               (-0.17, 0.16)], RUST * 0.86)
    body = [(-0.2, 0.04), (-0.24, 0.2), (-0.2, 0.38), (-0.1, 0.5), (0.04, 0.54), (0.14, 0.46), (0.18, 0.26),
            (0.14, 0.04)]
    f.blob(c, body, RUST)
    f.blob(c, [(-0.16, 0.36), (-0.08, 0.48), (0.04, 0.53), (0.13, 0.46), (0.06, 0.36)], GREYB)   # grey-brown shoulders
    f.blob(c, [(0.08, 0.08), (0.16, 0.2), (0.15, 0.4), (0.08, 0.44), (0.04, 0.24)], CREAM, 4)       # pale belly
    for k, (col, w) in enumerate(((BLACK, 0.028), (WHITE, 0.026), (BLACK, 0.024))):          # side stripes
        d = k * 0.035
        f.line(c, spline([(-0.17 + d, 0.12), (-0.19 + d, 0.26), (-0.14 + d * 0.8, 0.4), (-0.06 + d * 0.5, 0.48)], 5,
                         False), col, w)
    f.line(c, spline([(-0.22, 0.12), (-0.235, 0.24), (-0.2, 0.36)], 4, False), BLACK, 0.02)  # back stripe
    f.oval(c, -0.04, 0.12, 0.12, 0.1, RUST * 0.94, 24)                            # haunch
    f.oval(c, 0.06, 0.025, 0.08, 0.025, RUST * 0.8, 14)                           # hind foot
    hx, hy = 0.06, 0.66 + 0.01 * math.sin(nibble * 9.0)
    f.oval(c, hx - 0.05, hy + 0.12, 0.045, 0.05, RUST * 0.85, 14)                 # round ear
    f.oval(c, hx - 0.05, hy + 0.12, 0.025, 0.03, CREAM * 0.9, 10)
    f.oval(c, hx, hy, 0.15, 0.135, GREYB * 1.04, 30)                              # round head
    f.blob(c, [(hx + 0.06, hy + 0.04), (hx + 0.2, hy - 0.0), (hx + 0.22, hy - 0.05), (hx + 0.12, hy - 0.08),
               (hx + 0.04, hy - 0.06)], GREYB * 1.04)                              # short snout
    pr = 0.05 + 0.06 * pouch                                                      # cheek pouch, stuffed full
    f.oval(c, hx + 0.03, hy - 0.06, pr, pr * 0.85, GREYB * 1.1, 20)
    f.oval(c, hx + 0.04, hy - 0.07 - 0.01 * pouch, pr * 0.8, pr * 0.65, CREAM, 18)
    f.line(c, [(hx - 0.07, hy + 0.05), (hx + 0.03, hy + 0.04), (hx + 0.14, hy + 0.0)], BLACK * 1.6, 0.014)  # dark stripe
    f.line(c, [(hx - 0.06, hy + 0.095), (hx + 0.04, hy + 0.09), (hx + 0.12, hy + 0.055)], WHITE, 0.016)   # white above
    f.line(c, [(hx - 0.03, hy + 0.0), (hx + 0.12, hy - 0.03)], WHITE, 0.014)     # white below
    f.oval(c, hx + 0.215, hy - 0.04, 0.022, 0.018, BLACK, 10)                     # nose
    cute_eye(c, f, hx + 0.06, hy + 0.035, 0.04, blink=blink)
    nu, nv = 0.17, 0.42 + 0.02 * nibble                                           # the seed in its paws
    if seed:                                                                      # (seed=False: paws empty, or
        f.oval(c, nu + 0.03, nv + 0.03, 0.04, 0.05, _c(150, 100, 52), 14)         # holding what the scene draws
        f.oval(c, nu + 0.03, nv + 0.07, 0.042, 0.018, _c(110, 74, 40), 12)        # at chipmunk_paws)
    for dv in (0.0, 0.04):
        f.limb(c, (0.08, 0.4 + dv * 0.5), (0.13, 0.36 + dv), (nu + 0.01, nv + dv), 0.026, 0.018, GREYB * 0.9)


def beaver_mouth(x, y, s, face=1, kx=1.0):
    """Where the beaver's front teeth grip (world)."""
    return F(x, y, s, face, kx).p(0.555, 0.25)


BEAVER_STRIDE = 0.14            # walk_leg stride (local units): one gait cycle moves it 2 strides


def chickadee_bill(x, y, s, face=1, fluff=0.0, hop=0.0):
    """The tip of the chickadee's bill (world): where it holds a seed."""
    k = 1.0 + 0.22 * fluff
    by = 0.38 + 0.06 * abs(math.sin(hop * math.pi))
    return F(x, y, s, face).p(0.08 + 0.2, by + 0.2 * k - 0.005)


def chipmunk_paws(x, y, s, face=1, nibble=0.0):
    """Where the chipmunk's front paws hold a seed (world), for a scene that draws what it holds."""
    return F(x, y, s, face).p(0.2, 0.45 + 0.02 * nibble)


def chipmunk_cheek(x, y, s, face=1):
    """The cheek pouch (world): where a seed goes in."""
    return F(x, y, s, face).p(0.09, 0.6)


# ----------------------------------------------------------------------------------------------- beaver

def beaver(c, x, y, s, t, face=1, walk=0.0, gait=0.0, branch=1.0, blink=0.0, kx=1.0):
    """North American beaver on land: a big round brown body, small round ears, a blunt head, big orange front
    teeth, short front legs with clever hands, big webbed hind feet, and the flat black scaly paddle of a tail.
    branch 1: carrying a leafy branch crosswise in its teeth. kx: squashed across while it turns round (-1..1)."""
    f = F(x, y, s, face, kx)
    BROWN, LIGHT, DARK, TAIL, ORANGE = _c(132, 86, 52), _c(160, 112, 72), _c(92, 58, 36), _c(58, 52, 50), _c(236, 150, 60)
    ph = gait % 1.0
    tail = [(-0.4, 0.14), (-0.6, 0.12), (-0.86, 0.1), (-0.96, 0.06), (-0.9, 0.0), (-0.6, 0.02), (-0.4, 0.06)]
    f.blob(c, tail, TAIL)                                                         # flat paddle tail
    for k in range(3):                                                            # a few soft scale lines
        u = -0.62 - k * 0.1
        f.line(c, [(u, 0.1), (u - 0.03, 0.02)], TAIL * 1.35, 0.008)
    f.line(c, [(-0.45, 0.07), (-0.92, 0.05)], TAIL * 1.35, 0.008)

    def leg(hip, off, far):
        if walk > 0:
            a, b, d = walk_leg(hip, 0.02, 0.02, (ph + off + (0.25 if far else 0)) % 1, 0.14, 0.05)
        else:
            a, b, d = hip, (hip[0] + 0.02, 0.1), (hip[0] + 0.03, 0.0)
        return a, b, (d[0], d[1] + 0.04)
    for hip, off in (((-0.22, 0.2), 0.5), ((0.2, 0.22), 0.0)):
        a, b, d = leg(hip, off, True)
        f.limb(c, a, b, d, 0.07, 0.045, DARK * 0.8)
    f.blob(c, [(-0.46, 0.14), (-0.44, 0.38), (-0.22, 0.56), (0.08, 0.58), (0.3, 0.46), (0.36, 0.26), (0.22, 0.1),
               (-0.2, 0.08)], BROWN)                                              # big round body
    f.blob(c, [(-0.3, 0.46), (-0.12, 0.56), (0.1, 0.56), (-0.04, 0.5)], LIGHT * 0.95, 4)         # sheen on the back
    for hip, off in (((-0.24, 0.18), 0.0), ((0.22, 0.2), 0.5)):
        a, b, d = leg(hip, off, False)
        hindleg = hip[0] < 0
        f.limb(c, a, b, d, 0.09 if hindleg else 0.06, 0.045, DARK)
        if hindleg:                                                               # big webbed hind foot
            f.blob(c, [(d[0] - 0.06, d[1] - 0.03), (d[0] + 0.12, d[1] - 0.04), (d[0] + 0.14, d[1] - 0.0),
                       (d[0] - 0.02, d[1] + 0.01)], TAIL * 1.2, 3)
        else:
            f.oval(c, d[0] + 0.03, d[1] - 0.015, 0.045, 0.022, TAIL * 1.2, 10)
    hx, hy = 0.4, 0.36
    f.oval(c, hx - 0.08, hy + 0.13, 0.04, 0.04, DARK, 12)                         # small round ear
    f.oval(c, hx, hy, 0.15, 0.14, BROWN * 1.05, 30)                               # round head
    f.blob(c, [(hx + 0.04, hy + 0.06), (hx + 0.18, hy + 0.02), (hx + 0.21, hy - 0.06), (hx + 0.12, hy - 0.1),
               (hx + 0.02, hy - 0.08)], LIGHT)                                    # blunt muzzle
    f.oval(c, hx + 0.2, hy - 0.0, 0.032, 0.026, _c(40, 30, 26), 12)               # nose
    if branch > 0:                                                                # leafy branch in its teeth
        BR = _c(110, 82, 56)
        f.line(c, [(hx + 0.04, hy - 0.13), (hx + 0.16, hy - 0.1), (hx + 0.5, hy - 0.02)], BR, 0.022)
        f.line(c, [(hx + 0.34, hy - 0.06), (hx + 0.44, hy + 0.06)], BR, 0.013)
        for k, (u, v, a) in enumerate(((hx + 0.49, hy - 0.02, 0.2), (hx + 0.44, hy + 0.06, 1.1),
                                       (hx + 0.3, hy - 0.07, -1.2), (hx + 0.4, hy - 0.05, -0.5))):
            col = _c(226, 176, 64) if k % 2 == 0 else _c(206, 132, 52)
            ca, sa = math.cos(a), math.sin(a)
            f.blob(c, [(u, v), (u + 0.06 * ca - 0.025 * sa, v + 0.06 * sa + 0.025 * ca), (u + 0.1 * ca, v + 0.1 * sa),
                       (u + 0.06 * ca + 0.025 * sa, v + 0.06 * sa - 0.025 * ca)], col, 3)
    f.blob(c, [(hx + 0.13, hy - 0.08), (hx + 0.18, hy - 0.08), (hx + 0.175, hy - 0.15), (hx + 0.135, hy - 0.15)],
           ORANGE, 2)                                                             # the orange front teeth
    f.line(c, [(hx + 0.155, hy - 0.08), (hx + 0.155, hy - 0.15)], ORANGE * 0.7, 0.006)
    cute_eye(c, f, hx + 0.06, hy + 0.05, 0.04, blink=blink)


# ----------------------------------------------------------------------------------------------- Canada goose

def goose(c, x, y, s, t, face=1, fly=0.0, flap=0.0, walk=0.0, gait=0.0, honk=0.0, blink=0.0):
    """Canada goose: black head and long black neck, a white chinstrap from cheek to cheek, a brown-grey back with
    pale feather edges, a pale breast, white under the tail, a black tail and bill, black legs and webbed feet.
    fly 1: flying, neck stretched out, wings beating (flap 0..1 = one wingbeat)."""
    f = F(x, y, s, face)
    BACK, EDGE, BREAST, WHITE, BLACK = _c(128, 108, 88), _c(176, 160, 140), _c(214, 204, 190), _c(244, 242, 236), _c(30, 28, 28)
    if fly > 0.5:
        w = math.sin(flap * 2 * math.pi)                                          # +1 wings up, -1 down
        f.blob(c, [(-0.16, 0.52), (-0.1, 0.52 + 0.3 * w), (-0.2, 0.54 + 0.48 * w), (-0.32, 0.52 + 0.36 * w),
                   (-0.3, 0.52)], BACK * 0.78, 5)                                 # far wing
        f.blob(c, [(-0.42, 0.52), (-0.24, 0.6), (0.18, 0.6), (0.34, 0.54), (0.2, 0.44), (-0.2, 0.44)], BACK)
        f.blob(c, [(0.0, 0.46), (0.22, 0.46), (0.34, 0.53), (0.12, 0.5)], BREAST, 3)
        f.blob(c, [(-0.42, 0.52), (-0.5, 0.54), (-0.48, 0.48), (-0.36, 0.48)], BLACK, 3)        # tail
        f.oval(c, -0.36, 0.48, 0.06, 0.03, WHITE, 12)
        f.line(c, [(0.3, 0.55), (0.5, 0.57), (0.64, 0.58)], BLACK, 0.045)                       # neck stretched
        f.oval(c, 0.68, 0.585, 0.06, 0.045, BLACK, 16)
        f.blob(c, [(0.72, 0.6), (0.82, 0.585), (0.72, 0.56)], BLACK, 2)
        f.oval(c, 0.665, 0.57, 0.035, 0.022, WHITE, 12)                                         # chinstrap
        f.blob(c, [(0.1, 0.54), (0.06, 0.54 + 0.32 * w), (-0.06, 0.56 + 0.5 * w), (-0.2, 0.55 + 0.38 * w),
                   (-0.16, 0.54)], BACK * 1.06, 5)                                # near wing
        f.line(c, [(0.04, 0.54 + 0.34 * w), (-0.06, 0.56 + 0.5 * w), (-0.18, 0.55 + 0.4 * w)], BLACK * 1.8, 0.022)
        return
    ph = gait % 1.0
    if walk > 0:
        legs = [walk_leg((0.0, 0.32), 0.02, 0.0, (ph + 0.5) % 1, 0.16, 0.05), walk_leg((0.04, 0.32), 0.02, 0.0, ph, 0.16, 0.05)]
    else:
        legs = [((0.0, 0.32), (-0.01, 0.16), (0.0, 0.0)), ((0.06, 0.32), (0.05, 0.16), (0.07, 0.0))]
    for k, (a, b, d) in enumerate(legs):
        col = BLACK * (0.85 if k == 0 else 1.0)
        f.limb(c, a, b, (d[0], d[1] + 0.012), 0.018, 0.012, col)
        f.blob(c, [(d[0] - 0.03, d[1] + 0.012), (d[0] + 0.07, d[1] + 0.004), (d[0] + 0.07, d[1] + 0.026)], col, 2)
    f.blob(c, [(-0.44, 0.54), (-0.36, 0.6), (-0.1, 0.62), (0.16, 0.6), (0.28, 0.5), (0.24, 0.36), (0.0, 0.3),
               (-0.3, 0.36)], BACK)                                               # body
    f.blob(c, [(0.04, 0.34), (0.22, 0.38), (0.28, 0.5), (0.2, 0.56), (0.08, 0.44)], BREAST)       # pale breast
    f.blob(c, [(-0.3, 0.36), (-0.42, 0.42), (-0.4, 0.48), (-0.24, 0.42)], WHITE, 3)              # white under tail
    f.blob(c, [(-0.38, 0.5), (-0.5, 0.54), (-0.46, 0.6), (-0.34, 0.58)], BLACK, 3)              # black tail
    for k in range(2):                                                            # folded wing, pale feather edges
        v = 0.54 - k * 0.07
        f.line(c, spline([(-0.32 + k * 0.04, v), (-0.12, v + 0.02), (0.08 - k * 0.03, v - 0.01)], 4, False), EDGE, 0.014)
    bob = 0.02 * honk
    f.line(c, spline([(0.2, 0.56), (0.3, 0.72), (0.31, 0.9), (0.34, 1.02 + bob)], 5, False), BLACK, 0.075)   # long neck
    hx, hy = 0.37, 1.04 + bob
    f.oval(c, hx, hy, 0.085, 0.07, BLACK, 20)
    f.blob(c, [(hx + 0.06, hy + 0.025), (hx + 0.15, hy - 0.005 + 0.01 * honk), (hx + 0.145, hy - 0.03),
               (hx + 0.06, hy - 0.03)], BLACK * 1.3, 3)                           # bill
    f.blob(c, [(hx - 0.04, hy - 0.0), (hx + 0.03, hy + 0.0), (hx + 0.05, hy - 0.05), (hx - 0.0, hy - 0.07),
               (hx - 0.05, hy - 0.04)], WHITE, 3)                                 # the white chinstrap
    cute_eye(c, f, hx + 0.025, hy + 0.025, 0.022, blink=blink, iris=_c(14, 12, 12))


# ----------------------------------------------------------------------------------------------- groundhog

def groundhog(c, x, y, s, t, face=1, sit=1.0, sleep=0.0, breathe=0.0, blink=0.0):
    """Groundhog (woodchuck): a chunky brown body, paler brown front, dark brown-black feet, a short bushy dark
    tail, small round ears, a blunt round head with a pale muzzle. sit 1: standing up on its hind legs to look
    around; sleep 1: curled up in a round ball, nose tucked to its tummy, eyes shut, breathing slowly."""
    f = F(x, y, s, face)
    BROWN, PALE, DARK, MUZ = _c(140, 100, 66), _c(184, 146, 104), _c(64, 44, 32), _c(214, 190, 160)
    if sleep > 0.5:
        b = 1.0 + 0.025 * math.sin(breathe * 2 * math.pi)
        f.blob(c, [(-0.44, 0.06), (-0.5, 0.18), (-0.42, 0.3), (-0.32, 0.26), (-0.34, 0.12)], DARK * 1.3)  # tail round
        f.oval(c, 0.0, 0.26 * b, 0.44, 0.27 * b, BROWN, 40)                       # the round ball
        f.oval(c, -0.06, 0.34 * b, 0.3, 0.14 * b, PALE * 0.92, 30)                # soft sheen on the back
        f.oval(c, 0.26, 0.16, 0.16, 0.14, BROWN * 1.04, 26)                       # head tucked in
        f.oval(c, 0.2, 0.28, 0.035, 0.03, DARK, 10)                               # ear
        f.oval(c, 0.32, 0.08, 0.08, 0.06, MUZ, 18)                                # muzzle towards the tummy
        f.oval(c, 0.36, 0.05, 0.022, 0.018, DARK * 0.8, 10)
        cute_eye(c, f, 0.28, 0.18, 0.03, blink=1.0)                               # eyes shut
        f.oval(c, 0.14, 0.04, 0.07, 0.03, DARK, 12)                               # paws tucked
        return
    f.blob(c, [(-0.16, 0.04), (-0.32, 0.04), (-0.38, 0.12), (-0.24, 0.12)], DARK * 1.2, 4)      # short bushy tail
    body = [(-0.22, 0.04), (-0.28, 0.24), (-0.22, 0.46), (-0.08, 0.6), (0.06, 0.62), (0.16, 0.5), (0.2, 0.26),
            (0.16, 0.04)]
    f.blob(c, body, BROWN)                                                        # chunky, standing up
    f.blob(c, [(0.04, 0.1), (0.15, 0.22), (0.15, 0.46), (0.06, 0.52), (0.0, 0.3)], PALE, 4)      # paler front
    f.oval(c, -0.06, 0.12, 0.14, 0.12, BROWN * 0.95, 26)                          # haunch
    f.oval(c, 0.06, 0.028, 0.09, 0.028, DARK, 14)                                 # dark hind foot
    f.limb(c, (0.08, 0.46), (0.16, 0.42), (0.18, 0.36), 0.04, 0.03, DARK)         # front paws held at the chest
    hx, hy = 0.06, 0.74
    f.oval(c, hx - 0.07, hy + 0.1, 0.04, 0.035, DARK * 1.2, 12)                   # small round ear
    f.oval(c, hx, hy, 0.15, 0.13, BROWN * 1.04, 30)                               # blunt round head
    f.oval(c, hx - 0.03, hy + 0.06, 0.1, 0.055, BROWN * 0.86, 24)                 # a little darker on top
    f.oval(c, hx + 0.12, hy - 0.04, 0.08, 0.065, MUZ, 20)                         # pale muzzle
    f.oval(c, hx + 0.19, hy - 0.02, 0.025, 0.02, DARK * 0.7, 10)                  # nose
    f.blob(c, [(hx + 0.15, hy - 0.09), (hx + 0.18, hy - 0.09), (hx + 0.175, hy - 0.125), (hx + 0.155, hy - 0.125)],
           _c(244, 240, 226), 2)                                                  # little front teeth
    cute_eye(c, f, hx + 0.06, hy + 0.025, 0.036, blink=blink)


# ----------------------------------------------------------------------------------------------- black bear

def bear(c, x, y, s, t, face=1, walk=0.0, gait=0.0, sleep=0.0, breathe=0.0, blink=0.0):
    """American black bear: a black coat, a tan muzzle, round ears, a straight face (no dished face, no shoulder
    hump), short tail, thick tapering legs with round paws. walk: a slow rolling amble; sleep 1: curled up in its
    den."""
    f = F(x, y, s, face)
    BLACK, SHEEN, TAN, NOSE = _c(40, 36, 38), _c(62, 58, 62), _c(178, 138, 96), _c(22, 20, 20)
    if sleep > 0.5:
        b = 1.0 + 0.02 * math.sin(breathe * 2 * math.pi)
        f.oval(c, -0.04, 0.3 * b, 0.56, 0.3 * b, BLACK, 44)                       # curled body
        f.oval(c, -0.1, 0.42 * b, 0.36, 0.13 * b, SHEEN, 34)
        f.oval(c, 0.34, 0.18, 0.2, 0.17, BLACK * 1.08, 30)                        # head resting on the paws
        for du in (-0.08, 0.06):
            f.oval(c, 0.3 + du, 0.34, 0.055, 0.055, BLACK * 1.15, 14)             # round ears
            f.oval(c, 0.3 + du, 0.34, 0.03, 0.03, SHEEN * 0.9, 10)
        f.oval(c, 0.48, 0.12, 0.1, 0.075, TAN, 20)                                # tan muzzle
        f.oval(c, 0.55, 0.13, 0.03, 0.024, NOSE, 10)
        cute_eye(c, f, 0.38, 0.2, 0.034, blink=1.0)
        f.blob(c, [(0.1, 0.02), (0.44, 0.02), (0.46, 0.07), (0.12, 0.08)], BLACK * 1.15, 3)      # paws under the chin
        return
    ph = gait % 1.0

    def leg(hip, p):
        if walk > 0:
            return walk_leg(hip, 0.02, 0.02, p % 1, 0.18, 0.05)
        return hip, (hip[0] + 0.01, 0.16), (hip[0] + 0.02, 0.0)
    for hip, off in (((-0.32, 0.34), 0.75), ((0.24, 0.34), 0.25)):               # far legs
        a, b, d = leg(hip, ph + off)
        f.limb(c, a, b, (d[0], d[1] + 0.05), 0.11, 0.06, BLACK * 0.72)
        f.oval(c, d[0] + 0.03, d[1] + 0.04, 0.075, 0.042, BLACK * 0.72, 14)
    f.oval(c, -0.52, 0.56, 0.05, 0.04, BLACK, 12)                                 # short tail
    f.blob(c, [(-0.54, 0.38), (-0.5, 0.6), (-0.26, 0.72), (0.06, 0.72), (0.3, 0.66), (0.42, 0.5), (0.36, 0.28),
               (0.0, 0.22), (-0.38, 0.24)], BLACK)                                # big round body
    f.blob(c, [(-0.36, 0.64), (-0.14, 0.7), (0.12, 0.7), (-0.06, 0.64)], SHEEN, 4)
    for hip, off in (((-0.36, 0.34), 0.0), ((0.28, 0.34), 0.5)):                 # near legs: thick, tapering
        a, b, d = leg(hip, ph + off)
        f.limb(c, a, b, (d[0], d[1] + 0.05), 0.12, 0.065, BLACK * 1.06)
        f.oval(c, d[0] + 0.035, d[1] + 0.04, 0.08, 0.045, BLACK * 1.06, 16)       # round paw
    hx, hy = 0.5, 0.6
    f.oval(c, hx - 0.06, hy + 0.15, 0.06, 0.06, BLACK * 1.1, 16)                  # round ear
    f.oval(c, hx - 0.06, hy + 0.15, 0.032, 0.032, SHEEN * 0.9, 12)
    f.oval(c, hx, hy, 0.18, 0.16, BLACK * 1.08, 34)                               # round head
    f.blob(c, [(hx + 0.06, hy + 0.04), (hx + 0.24, hy + 0.0), (hx + 0.27, hy - 0.06), (hx + 0.2, hy - 0.11),
               (hx + 0.06, hy - 0.1)], TAN)                                       # straight tan muzzle
    f.oval(c, hx + 0.26, hy - 0.03, 0.04, 0.032, NOSE, 14)
    f.line(c, [(hx + 0.16, hy - 0.09), (hx + 0.22, hy - 0.085)], NOSE * 2, 0.008)  # a little smile
    cute_eye(c, f, hx + 0.06, hy + 0.05, 0.036, blink=blink)


# ----------------------------------------------------------------------------------------------- chickadee

def chickadee(c, x, y, s, t, face=1, fluff=0.0, hop=0.0, sing=0.0, blink=0.0, seed=0.0, fly=0.0, flap=0.0):
    """Black-capped chickadee perched: a round little bird with a black cap (over the eye) and a black bib, white
    cheeks, a grey back and wings with white feather edges, buff sides, a pale belly, a grey tail, a tiny black bill.
    fluff 0..1 puffs it into a round ball against the cold; seed 1 holds a seed in its bill."""
    f = F(x, y, s, face)
    GREY, EDGE, BUFF, WHITE, BLACK = _c(128, 132, 136), _c(220, 222, 220), _c(226, 196, 156), _c(244, 242, 236), _c(28, 28, 30)
    k = 1.0 + 0.22 * fluff
    by = 0.38 + 0.06 * abs(math.sin(hop * math.pi))
    f.blob(c, [(-0.16, by - 0.02), (-0.42, by - 0.12), (-0.44, by - 0.07), (-0.18, by + 0.06)], GREY * 0.9, 3)   # tail
    for du in (0.0, 0.04):                                                        # little dark legs and toes
        f.line(c, [(du, by - 0.2 * k), (du + 0.01, 0.03)], BLACK * 1.5, 0.012)
        f.line(c, [(du - 0.04, 0.02), (du + 0.06, 0.02)], BLACK * 1.5, 0.01)
    f.oval(c, -0.02, by, 0.22 * k, 0.21 * k, BUFF, 36)                             # round body: buff sides
    f.oval(c, 0.04, by - 0.03 * k, 0.16 * k, 0.17 * k, WHITE, 30)                  # pale belly
    if fly > 0.5:                                                                 # flying: both wings out,
        w = math.sin(flap * 2 * math.pi)                                          # beating (flap 0..1 = one beat)
        for side, sh in ((1, 1.0), (-1, 0.82)):
            tip = (-0.12 + 0.05 * side, by + 0.42 * w * side + 0.1)
            f.blob(c, [(-0.1, by + 0.06), (tip[0] - 0.18, tip[1] + 0.04), (tip[0], tip[1]), (0.06, by + 0.08)],
                   GREY * sh, 3)
    else:
        f.blob(c, [(-0.22 * k, by + 0.08), (-0.1, by + 0.16 * k), (0.06, by + 0.1), (0.0, by - 0.06),
                   (-0.24 * k, by - 0.06)], GREY)                                 # folded grey wing
        for j in range(3):
            f.line(c, [(-0.2 * k + j * 0.04, by + 0.06 - j * 0.04), (0.0, by + 0.04 - j * 0.04)], EDGE, 0.012)
    hx, hy = 0.08, by + 0.2 * k
    f.oval(c, hx, hy, 0.14, 0.13, WHITE, 30)                                      # head: white cheek
    f.blob(c, [(hx - 0.14, hy + 0.0), (hx - 0.1, hy + 0.12), (hx + 0.04, hy + 0.14), (hx + 0.14, hy + 0.04),
               (hx + 0.13, hy - 0.03), (hx + 0.02, hy - 0.025), (hx - 0.08, hy - 0.0)], BLACK)   # black cap, over the eye
    f.blob(c, [(hx + 0.04, hy - 0.07), (hx + 0.13, hy - 0.05), (hx + 0.1, hy - 0.14), (hx + 0.05, hy - 0.15)],
           BLACK, 4)                                                              # the black bib under the bill
    f.blob(c, [(hx + 0.12, hy + 0.02), (hx + 0.2, hy - 0.0 + 0.02 * sing), (hx + 0.12, hy - 0.03)], BLACK, 2)   # bill
    if seed > 0:
        f.oval(c, hx + 0.2, hy - 0.005, 0.025, 0.014, _c(90, 70, 50), 10)
    cute_eye(c, f, hx + 0.07, hy + 0.01, 0.032, blink=blink, iris=_c(12, 12, 14))


DRAW = {"chipmunk": chipmunk, "beaver": beaver, "goose": goose, "groundhog": groundhog, "bear": bear,
        "chickadee": chickadee}


def draw_winter(c, kind, x, y, s, t=0.0, face=1, **kw):
    DRAW[kind](c, x, y, s, t, face=face, **kw)


_PER_S = {}


def per_s(kind, **kw):
    """Drawn height (top of head or ears to the ground) per unit of s, measured once by drawing it at s = 100: so a
    scene can size every animal by its real height (FK0012 audit item 17)."""
    key = (kind, tuple(sorted(kw.items())))
    if key not in _PER_S:
        import numpy as np
        from families.keepers.illustrate import StyleCanvas
        cv = StyleCanvas(800, 800, 6)
        draw_winter(cv, kind, 400.0, 700.0, 100.0, t=1.0, **kw)
        a = cv.surface.makeImageSnapshot().toarray()[..., 3]
        rows = np.where(a.max(axis=1) > 20)[0]
        _PER_S[key] = (700.0 - rows.min()) / 100.0 if rows.size else 1.0
    return _PER_S[key]
