"""Episode 1 staging: one key frame per chapter, where everyone stands, before anything is voiced (no credits).

Each chapter's layout puts the Keepers' feet on the ground with their size from scale_at, keeps a gap between any
two of them (no overlaps, so no front/behind choices), keeps the old oak off to one side (Sprout looks toward it out
of the shot, never turns its back to us), and keeps the action near the middle third where a vertical Short's crop
can hold it. talkcheck runs on every layout: size and overlap.

    .venv\\Scripts\\python.exe -m families.keepers.talk.staging <out dir>
"""
import os
import sys

import skia

from families.keepers import flat
from families.keepers.doorway import HALF_W
from families.keepers.talk import cast, check, places

HALF = {"sprout": HALF_W["sprout"] * 0.8, "digs": HALF_W["digger"], "springs": HALF_W["springs"],
        "glo": HALF_W["lantern"]}       # Sprout's arms hang at its sides here (HALF_W counts them held out)

# chapter: (place, light, {who: (x, feet y, look)}, close-up zoom or None, title)
CHAPTERS = {
    1: ("oak", "morning", {"sprout": (1040, 990, (0.6, -0.3))}, None, "1 Under the Old Oak"),
    2: ("pond", "morning", {"sprout": (720, 985, (0.8, 0.0)), "springs": (1210, 995, (-0.8, 0.0))}, None,
        "2 The Pond"),
    3: ("molehills", "day", {"springs": (470, 990, (0.8, 0.0)), "sprout": (900, 992, (0.8, 0.0)),
                             "digs": (1390, 985, (-0.8, 0.0))}, None, "3 The Molehills"),
    4: ("sunset", "sunset", {"springs": (420, 975, (0.8, 0.0)), "sprout": (800, 978, (0.8, 0.0)),
                             "digs": (1180, 975, (-0.8, 0.0)), "glo": (1620, 1035, (-0.8, 0.0))}, None,
        "4 The Meadow at Sunset"),
    5: ("oak", "night", {"springs": (560, 1000, (-0.3, -0.7)), "sprout": (900, 990, (-0.5, -0.8)),
                         "digs": (1290, 985, (-0.6, -0.6)), "glo": (1660, 960, (-0.8, -0.4))}, None,
        "5 Night under the Old Oak"),
    6: ("oak", "night", {"springs": (560, 1000, (0.6, 0.0)), "sprout": (900, 990, (0.0, 0.0)),
                         "digs": (1290, 985, (-0.6, 0.0)), "glo": (1660, 960, (-0.8, 0.0))},
        dict(zoom=1.3, cx=1110.0, cy=760.0, sx=960.0, sy=680.0), "6 The Forest Keepers (close)"),
}


def overlap(state):
    """Pairs of Keepers whose widths overlap on screen (each one's half width at its size), with no gap between."""
    out, items = [], sorted(state.items(), key=lambda q: q[1]["x"])
    for (a, sa), (b, sb) in zip(items, items[1:]):
        gap = (sb["x"] - HALF[b] * sb["k"]) - (sa["x"] + HALF[a] * sa["k"])
        if gap < 0:
            out.append(f"{a} and {b} overlap by {-gap:.0f} px")
    return out


def frame(ch, path=None):
    place, light, who, close, title = CHAPTERS[ch]
    bg, marks = places.backdrop(place, light)
    Z = close["zoom"] if close else 1.0
    S = (lambda x, y: ((x - close["cx"]) * Z + close["sx"], (y - close["cy"]) * Z + close["sy"])) if close else \
        (lambda x, y: (x, y))
    pg = flat.FlatPage(places.W, places.H)
    if close:                                         # the zoomed scenery must still cover the whole frame
        assert close["sx"] - close["cx"] * Z <= 0 and (places.W - close["cx"]) * Z + close["sx"] >= places.W
        assert close["sy"] - close["cy"] * Z <= 0 and (places.H - close["cy"]) * Z + close["sy"] >= places.H
        c = pg.c
        c.save()
        c.translate(close["sx"] - close["cx"] * Z, close["sy"] - close["cy"] * Z)
        c.scale(Z, Z)
        c.drawImage(bg, 0, 0, skia.SamplingOptions(skia.CubicResampler.Mitchell()))
        c.restore()
    else:
        pg.c.drawImage(bg, 0, 0)
    places.light_over(pg, light, 0.6)                 # the scenery's share of the light
    state = {}
    for name, (x, y, look) in sorted(who.items(), key=lambda q: q[1][1]):          # far to near
        k = places.scale_at(y)
        state[name] = dict(x=x, y=y, k=k, lift=0.0, talk=0.0, holding=None)
        X, Y = S(x, y)
        if name == "springs":
            cast.frog_springs(pg, X, Y, k * Z, look=look)
        elif name == "glo":
            cast.figure(pg, "glo", X, Y, k * Z, t=0.0, shadow=False, lamp=1.0, _look=lambda _t, l=look: l)
        else:
            cast.figure(pg, name, X, Y, k * Z, t=0.0, _look=lambda _t, l=look: l, _blink=lambda _t: 0.0)
    places.light_over(pg, light, 0.45)                # everyone's share
    if light in ("night", "sunset") and "glo" in who:                               # Glo's lantern light, small and warm
        x, y, _ = who["glo"]
        k = places.scale_at(y)
        X, Y = S(x, y - 190 * k)
        p = skia.Paint(Color=skia.Color(255, 214, 140, 80), BlendMode=skia.BlendMode.kScreen, AntiAlias=True)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40 * Z * k))
        pg.c.drawCircle(X, Y, 95 * Z * k, p)
    if path:
        from PIL import Image
        Image.fromarray(pg.finish()).save(path)
    return state


def main(out):
    os.makedirs(out, exist_ok=True)
    total = 0
    for ch in CHAPTERS:
        st = frame(ch, os.path.join(out, f"ep1_ch{ch}.png"))
        probs = overlap(st) + check.size([(0.0, st)], places.scale_at)
        total += len(probs)
        print(f"chapter {ch}: {', '.join(f'{w} k={s['k']:.2f}' for w, s in st.items())}  problems: {probs or 0}")
    from PIL import Image
    tiles = [Image.open(os.path.join(out, f"ep1_ch{ch}.png")).resize((960, 540)) for ch in CHAPTERS]
    sheet = Image.new("RGB", (1920, 1620))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 2) * 960, (i // 2) * 540))
    sheet.save(os.path.join(out, "ep1_staging.png"))
    print(f"staging check TOTAL {total}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "renders/forest_keepers_talk/ep1_staging")
