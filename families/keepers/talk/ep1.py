"""Episode 1, "How the Forest Keepers Began": the approved script, chapter by chapter, voiced (owner approved the
script as written 2026-11-17, "approve"; publish/OWNER_QUEUE.md).

The words come straight from docs/engines/forest_keepers_talk_ep1_script.md, so what is voiced is word for word what
he approved. The pauses come from its stage directions:
- a "Silence (music up)" direction is a real silence where the theme comes up: SILENCE s
- any other direction between two lines (someone hops, sniffs, looks up): ACTION s
- the gap between two lines with no direction: GAP s
- before a chapter's first line: OPEN s (chapter 1 opens on the theme over the wide shot: OPEN_FIRST s)
- after its last line: the closing direction (a cut: CLOSE s; the end hold of chapter 6: END s)

    .venv\\Scripts\\python.exe -m families.keepers.talk.ep1 [chapters...]     # voices them (cached), prints credits
"""
import os
import re
import sys

from engine.log import ROOT

SCRIPT = os.path.join(ROOT, "docs", "engines", "forest_keepers_talk_ep1_script.md")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "renders", "forest_keepers_talk", "ep1")
WHO = {"Narrator": "narrator", "Sprout": "sprout", "Springs": "springs", "Digs": "digs", "Glo": "glo"}
GAP, ACTION, SILENCE = 0.7, 2.2, 6.0
LONG_SILENCE = {4: 11.0}    # the sunset: the sky goes pink, then blue, the stars come out and Glo floats in
OPEN, OPEN_FIRST, CLOSE, END = 1.5, 5.0, 1.2, 9.0
SFX = {  # ElevenLabs sound effects (families.curiosity.sfx.generate, cached by prompt): name -> (prompt, seconds)
    "birdsong": ("gentle early spring morning birdsong in a quiet meadow, a few soft robins and wrens singing, calm and "
                 "far away, no wind, no music", 6.0),
    "croak": ("one loud happy frog croak from a pond a little way off, a single cheerful ribbit, no music", 2.0),
    "peepers": ("a distant chorus of spring peeper frogs on a calm spring night far away across a meadow, soft and "
                "muffled, no music", 10.0),
}


def chapters():
    """-> {n: (title, open seconds, [(who, text, pause after)])} from the approved script."""
    with open(SCRIPT, encoding="utf-8") as f:
        body = f.read().split("\n---\n")[1]
    out = {}
    for block in re.split(r"\n## ", "\n" + body)[1:]:
        head, _, rest = block.partition("\n")
        n, title = int(head.split(".")[0]), head.split(". ", 1)[1].split(" (")[0]
        paras = [" ".join(p.split()) for p in rest.strip().split("\n\n") if p.strip()]
        lines, pending = [], None
        for p in paras:
            m = re.match(r"\*\*(\w+):\*\* (.+)$", p)
            if m:
                lines.append([WHO[m.group(1)], m.group(2), GAP])
            elif p.startswith("*") and lines:
                lines[-1][2] = max(lines[-1][2], LONG_SILENCE.get(n, SILENCE) if p.startswith("*Silence")
                                   else ACTION)
        last = paras[-1]
        lines[-1][2] = END if "End sign" in last else CLOSE
        out[n] = (title, OPEN_FIRST if n == 1 else OPEN, [tuple(x) for x in lines])
    return out


def voice(which=None):
    from engine.elevenlabs import credits
    from families.keepers.talk import voices
    chs = chapters()
    which = which or sorted(chs)
    todo = sum(voices.characters(chs[n][2]) for n in which)
    before = credits()
    print(f"voicing chapters {which}: {todo:,} characters; credits used {before[0]:,} of {before[1]:,}")
    for n in which:
        title, lead, script = chs[n]
        cues = voices.voice_chapter(script, OUT, f"ep1_ch{n}", lead_in=lead)
        print(f"chapter {n} {title}: {len(cues)} lines, {cues[-1]['end'] + script[-1][2]:.1f} s")
    print(voices.credits_report(before))


if __name__ == "__main__":
    voice([int(a) for a in sys.argv[1:]] or None)
