"""Forest Keepers ep 1 (talk format), "How the Forest Keepers Began": the long video's thumbnail options (owner rule:
4-6 really different ones, each its own moment and hook, 2-5 words readable on a phone) and their contact sheet with
the exact upload title. Frames come from ep1_film.Episode.frame, the same frames as the video, in the episode's flat
picture-book look (cream label, warm ink, as the earlier Forest Keepers covers).

    .venv\\Scripts\\python.exe -m families.keepers.talk.ep1_thumbs <ID> [title]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from engine import thumbnail
from engine.log import ROOT
from families.keepers.talk import ep1_film as E

F = os.path.join(ROOT, "engine", "assets", "fonts", "Inter-Bold.otf")
INK, PAPER = (92, 64, 54), (250, 242, 228)


def options(ep):
    """option: (episode time, crop (x0, y0, x1, y1) of the 1920x1080 frame, headline, label at top/bottom)."""
    ch1, ch2, ch4, ch5 = ep.ch[0], ep.ch[1], ep.ch[3], ep.ch[4]
    T = ep.T
    return {
        # Sprout just awake in the close-up, leaves up, looking at us: "But what am I?" (ch 1)
        "A": (T[0] + ch1.c(5)["start"] + 4.2, (105, 146, 1605, 990), "WHAT AM I?", "top"),
        # all four under the old oak at night, Glo's lantern lit (ch 5, the closer framing)
        "B": (T[4] + ch5.c(4)["start"] + 1.0, (0, 0, 1920, 1080), "HOW IT ALL BEGAN", "top"),
        # Sprout meets Springs at the pond (ch 2: "you've got a little sprout on your head!")
        "C": (T[1] + ch2.c(7)["start"] + 2.0, (0, 140, 1680, 1085), "A NEW FRIEND", "top"),
        # the stars are out and Glo has floated in, lantern glowing: "Hello, everyone." (ch 4)
        "D": (T[3] + ch4.c(7)["start"] + 1.0, (0, 0, 1920, 1080), "WHO IS GLOWING?", "top"),
        # the oak at night: the sleeping birds in the nest, the squirrel in its hole, the moths (ch 5 insert)
        "E": (T[4] + ch5.c(3)["start"] + 1.0, (0, 0, 1920, 1080), "WHO LIVES IN THE OAK?", "top"),
    }


def label(img, text, where):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    size = 96
    f = ImageFont.truetype(F, size)
    while d.textlength(text, font=f) > W - 120:
        size -= 4
        f = ImageFont.truetype(F, size)
    tw = d.textlength(text, font=f)
    x0, y0 = (W - tw) / 2 - 34, 30 if where == "top" else H - size - 90
    box = (x0, y0, x0 + tw + 68, y0 + size + 50)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0] + 6, box[1] + 10, box[2] + 6, box[3] + 10), 30, fill=(50, 34, 28, 90))
    img.paste(Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(10))).convert("RGB"))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 30, fill=PAPER)
    d.text((x0 + 34, y0 + 18), text, font=f, fill=INK)
    return img


def main(vid, title=None, out=os.path.join(ROOT, "thumbnails")):
    ep = E.Episode()
    paths = []
    for k, (t, crop, text, where) in options(ep).items():
        frame = Image.fromarray(ep.frame(t))
        x0, y0, x1, y1 = crop
        h = (x1 - x0) * 9 / 16                                     # keep 16:9 inside the frame
        y0 = max(0, min(y0, 1080 - h))
        img = frame.crop((x0, int(y0), x1, int(y0 + h))).resize((1280, 720), Image.LANCZOS)
        if t > ep.T[3] + ep.ch[3].dusk1:                           # night: a touch brighter so it reads on a phone
            img = ImageEnhance.Brightness(img).enhance(1.3)
        img = label(img, text, where)
        p = os.path.join(out, f"{vid}_{k}.png")
        img.save(p)
        paths.append(p)
        m, s = divmod(t, 60)
        print(f"wrote {p}  frame {int(m)}:{s:04.1f}  {text}")
    thumbnail.sheet(paths, os.path.join(out, f"{vid}_options.png"), title=title)
    print("wrote sheet")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
