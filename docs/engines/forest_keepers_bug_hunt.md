# Forest Keepers episode 10: Bug Hunt (`FK0007_bug_hunt`, ~6:38, 16:9)

Owner idea (2026-11-01, with the FK0006 approval): the Keepers turn over logs and rocks in the forest and find
different bugs. Each bug gets a **close-up**, and it should be **pretty real-world: it looks like the real bug**. A
Keeper **identifies** it, checking it against a book or a phone database, the **name shows on screen** with a
little about the bug (nothing too detailed, kid-friendly) and **what it does to help the forest**. Later episodes
can do the same with the **animals of the forest**.

Uses the new look (episode 9 on) and every standing rule in `forest_keepers.md` (no warping, slow on purpose, no
walking through walls, the music box, the end sign). Nothing scary: no stings or bites shown, nobody squashes or
keeps a bug; every log and rock goes gently back the way it was.

## Draft story (~6-7 min, 16:9)

1. **Hook (~0:30).** A calm forest morning, the name tags. Digs' shovel turns up a wiggly worm; the Keepers lean in,
   curious. Wheels rolls out the **Keeper Field Guide** (a big book with a leaf on the cover); Glo has an idea: find
   them all. The guide's first page shows six empty frames with a "?" each: the episode's checklist.
2. **Six finds, one per Keeper, each in its own way (~50 s each).** The Keeper lifts / opens the hiding place, the
   bug comes out, a big **magnifying glass** on a stand swings over (a slow zoom, no cut) and the bug fills the frame,
   moving like the real one. The finder pages through the guide, the picture matches, a tick, the name in big
   friendly letters and one or two short lines. The log or rock goes back gently.
3. **The guide is full (~0:30).** All six frames filled; the Keepers wave the bugs goodbye. End sign.

Possible finds (all common in North American woods, every fact checked before use):

| Keeper | Where | Bug | Line (draft) |
|---|---|---|---|
| Digs | digging soft soil | Earthworm | Digs tunnels that let air and rain into the soil, so roots can grow. |
| Hans | lifts a log with his tentacles | Pill bug (roly-poly) | Not an insect at all: it's related to shrimp and crabs! Rolls into a ball, eats dead leaves. |
| Twigs | peeks under loose bark (no sawing) | Millipede | Lots of legs, two pairs on most of its body parts. Turns rotting leaves and wood into soil. |
| Wheels | lifts a flat rock with his claws | Ground beetle | A night hunter that eats slugs and pests that chew on plants. |
| Springs | a hop onto a leafy plant | Ladybug | Eats aphids that hurt plants; its spots tell birds "I taste bad". |
| Glo | dusk, his light under the ferns | Firefly | Makes its own light to talk to other fireflies. |

Alternatives: a snail, a bess beetle (it squeaks), ants carrying seeds, a stag beetle.

## As built (`families/keepers/bug_hunt.py`, params `families/keepers/params/bug_hunt.yaml`)

One act (`hunt`), one night walk along a forest path, no cuts; then the end sign.
- **The bugs** (`families/keepers/bugs.py`, sheet `forest_keepers_bug_hunt/1_the_six_bugs.png`): seven-spot ladybug,
  common eastern firefly, a Carabus ground beetle, the common pill bug, the common earthworm, the American giant
  millipede; seen from above, checked against photos; beetles walk on a tripod gait, the millipede's legs move in
  waves, the worm squeezes and stretches, the pill bug rolls up, the firefly's lantern glows.
- **Hook**: the name tags, then Digs digs and an earthworm wiggles out; Glo has an idea; Wheels pushes the Keeper
  Field Guide over on its reading cart; Glo's light opens it on the checklist (six "?" frames); the card "BUG HUNT /
  Can the Keepers find six different bugs in the forest?".
- **Each find**: the walk (steady pan), the finder's way of looking (Digs digs; Hans rolls the log, seen end-on, off
  the pill bugs; Twigs peels loose bark on a stump; Wheels lifts a flat rock with his claw; Springs bounces up by a
  tall plant; Glo dims his lantern by the ferns), Glo floats his big lens over the bug while the camera closes in
  slowly (the lens shows the bug big, moving), Glo's light flare turns three pages to the match and ticks the box,
  the name card (bottom of the screen, ~9.5 s, quiet so it can be read), the bug goes home and the place is put back
  (the pill bugs walk into the shade under the log where it now lies). "BUGS FOUND n / 6" top left.
- **Finale**: fireflies rise all around, the checklist is full, "All six found! / Every one of them helps keep the
  forest healthy.", everyone cheers, the camera pulls back over the glowing forest.
- Music: the theme's `bughunt` variant (D major, 100 BPM, a new tiptoeing D part). A moth flutters round Glo's
  lantern. Checks: teleports, fast_moves, prop_jumps, act_cuts, cam_fast, wall_clips all 0; no folded notes.

Owner + Toby review of the first render (2026-11-01): redo it with three fixes; the rest is fine. (1) The count
and the name cards jittered the whole time: they are now drawn in fixed screen units (`HuntAct.screen`). (2) The log
rolled anticlockwise while Hans pulled it right: now clockwise. (3) The millipede's head was outside the lens: every
bug now fits in the lens head to tail (worm and millipede 205 long, slower walks, the beetle and the ladybug kept
inside too). Re-rendered into the same ID.

Owner approved the re-render 2026-11-01 as is, with two tiny flaws noted for next time (not to be fixed here): on
the last page turn the new bug appears on the left page before the page has landed, and the book's page text
shimmers a little while the camera moves (rules in `forest_keepers.md`).

First render 2026-11-01 (2.5 h): `renders/Forest Keepers/FK0007_bug_hunt.mp4`, 6:38, checks all 0, no folded notes;
in the publishing queue, awaiting owner review.

Promise -> payoff (for the HANDOFF entry): the title and cover promise the Keepers finding real forest bugs up close;
the hook sets the goal (find six) in the first half-minute, the first close-up is at ~0:40, the sixth bug is found by
~5:40 and the full checklist pays it off at ~6:05.

## Owner decisions (2026-11-01)

1. **The bugs are drawn in code, field-guide accurate**: real shape, colours, leg count and how it walks, checked
   side by side with reference photos. The close-up is big and detailed. Descriptions keep "all visuals and sound are
   generated with code".
2. **The Keeper Field Guide is a book** (no phone).
3. **Words on screen, no narrator** for this one: the name big, the line short, on screen long enough for a young
   reader. (A narrator gets tried in a couple of other episodes, probably the animal ones: `forest_keepers.md`.)

## Flat remake (ep 10, FK0022_bug_hunt_remake, 2026-11-06)

The owner had every old-look episode remade in the flat picture-book look (2026-11-06, "remake them all"). Bug Hunt keeps
the approved FK0007 story, timing, camera, sounds and name cards, and is drawn flat by `families/keepers/bug_flat.py`
(runner `experiments/keepers_flat/ep10.py`, params `bug_hunt_remake.yaml`), the way `tune_flat.py` draws the Tune-Up's
second half:
- **The bugs keep their field-guide drawing** (`bugs.py`), painted flat through `OldCanvas` (the old Canvas calls
  on a skia page), in the world, in Glo's lens, in the guide and on the name cards.
- **Natural walks** (owner, FK0016): arm swing, Twigs' knees forward, Hans' staggered ripple (`tune_flat.Walks`).
- **Nobody walks through anybody** (owner rule since FK0006; FK0007 had 10 passes through each other on the walks).
  `HuntFlatAct` keeps the queue's left-to-right order from one find to the next, so only the next finder has to get
  past the others, and he does it on the **back lane** (`bug_flat.lanes`): a second before the pass he steps a little
  up the path, drawn behind and smaller, and steps back a second after. Walk-through check (same lane): 0.
- **Wheels' cart**: the old push handle ran up across his face; the flat cart has a short push bar his right pincer
  holds, drawn behind him.
- No narrator (owner decision for this episode, 2026-11-01: words on screen); Twigs still has his wrist saws (hands come
  with ep 12, New Friend).
