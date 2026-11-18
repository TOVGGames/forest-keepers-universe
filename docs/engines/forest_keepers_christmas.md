# Forest Keepers episode 14: Sprout's Christmas Tree (`FK####_christmas_tree`, 6-10 min, 16:9, narrated)

**Status (2026-11-06): the flat-look storyboard (below, "Flat-look storyboard") is with the owner for his OK, via
Local Operations.** It is the story he approved on 2026-11-03, redrawn in the approved flat picture-book look (FK0016),
with his notes from approving FK0016. The planned render is `FK0017_christmas_tree`, to post around Nov 23-25.

## Flat-look storyboard (2026-11-06)

Stills: `forest_keepers_christmas_flat/` (made by `families/keepers/christmas_flat_board.py`).

What changed from the approved 2026-11-03 storyboard:
- **Every Keeper makes something** (his 11-03 note). Twigs carves stars and acorns, Wheels paints, Hans braids a
  garland, Springs threads berries, Sprout ties ribbons, and Digs brings pine cones.
- **A gentle conflict with a climax** (his FK0016 note: "it's okay, too, to have stories... where there's some conflict
  that needs resolution and comes to a climax... As long as it never gets too tense"):
  - On Christmas Eve a gust shakes the little fir. The star tumbles into the snow, and the lanterns go out.
  - Digs' hat lamp searches the snow and finds the star. Hans shakes the snow off the branches with his tentacles.
  - Springs' first bounce falls short. The second puts the star back on top: that's the climax.
  - Glo's flare relights the lanterns one by one, just as the winter animals come to see.
  - Nobody is upset for long, and the music stays the music box throughout.
- **His FK0016 walk notes, from this episode on:**
  - arms swing naturally, never held out to the sides;
  - Twigs never looks like he's walking backwards;
  - Hans walks with a staggered six-leg gait, not a march;
  - Digs' and Springs' walks are the model.
  - There's no water in this story; `water_snap` stays in storycheck anyway.

Beats (about 7:30):
0. **Hook** (0:00-0:15): the snowy path; the Keepers find the little fir growing in the middle of it.
1. **Potting** (~1:00): Digs lifts it out with its ball of soil, and Sprout has a pot ready. They set it in, and
   Sprout waters it.
2. **Ornaments** (~1:30): at the workbench under a lantern, every Keeper makes something (the list above).
3. **Decorating** (~1:15): Hans hangs the ornaments, the garland and berries go round, and Springs puts the star on.
   Glo's flare comes from under his dome and lights the lanterns one by one.
4. **The gust** (~1:15, Christmas Eve, falling snow): the star falls and the lanterns go out. They search, shake the
   snow off, and Springs tries twice.
5. **Christmas Eve** (~1:15): the lit tree. A deer, a red fox, a cottontail and a chickadee come to see. All of them
   are out in winter; nothing hibernating or migrating.
6. **Forever home** (~1:00): a bright winter morning after the holidays. Digs digs a hole in a sunny clearing, the fir
   goes in, Sprout waters it, and the ornaments go back in their box. Goodnight, then 3-5 s of quiet, then the end sign.

Draft narration (Johanna, slow and sparse; passes storycheck `promise_line`):
- "It's nearly Christmas in the forest. And look... a little fir is growing right in the middle of the path. At the
  very end, it gets a forever home of its own."
- "Digs lifts it out gently, roots and soil and all, so nobody steps on it."
- "Every Keeper is making something for the little tree."
- "Hans hangs them, one by one. And Springs has the star."
- "Christmas Eve. Oh... a gust of wind. The star has tumbled into the snow, and the lanterns have gone out."
- "Digs has the very lamp for looking in the snow."
- "Up goes the star again. And the lanterns glow."
- "Someone has come to see. A deer, a fox, a rabbit, and a little chickadee."
- "After the holidays, on a bright winter morning, the little fir gets its forever home, in a sunny clearing.
  Goodnight, forest."

**Promise -> payoff:** the title and cover promise the Keepers' own Christmas tree. The hook sets up the ending: the
fir's forever home. The tree is decorated by about 4:00. The gust and the star going back up are the climax, around
5:00. The planting in the clearing is the last scene before the end sign.

## Re-stage for the continuity advisor (FK0017 v2, 2026-11-07)

Round 1 of the continuity advisor (`video_log/advisor/FK0017_r1.md`) found 56 must-fix. Local Operations
(2026-11-07): "do the full FK0017 re-stage... Keep the approved story beats, the gust and the visitors, and break the
long walks with short cuts and act breaks". The narration keeps its cached takes (ElevenLabs credits are short), so
the picture is fitted to the lines, never the other way round.

How it's built:
1. **Time warp, for the long walks** (the 14-31 s walks, and every walk-through on the way). The world keeps its one
   continuous timeline. The video shows it through `warp(t_video) -> t_world`: a walk longer than ~4 s shows its
   first ~3 s, then an act break (a ~1.2 s dip to dark, the world time jumping ahead while it's dark), then its last
   ~3 s. Narration and sound events are moved by the same map. The check runs on world time per shown stretch, so
   an act break isn't a teleport.
2. **Depth: one rule for the props.** The fir, the pot, the garland, the lantern posts, the basket and the bench
   stand BACK of the lane. A Keeper in the lane is drawn in front of all of them, the garland included; a Keeper
   never stands in front of the fir while working on it (they work from its side).
3. **Hans:** working tentacles come from lifted legs (`legs_up`), never from his face; nothing fades in; no
   tentacle longer than a leg; the braid is a braid (the sprigs are used up as it grows).
4. **No magic:** paint only where a brush touches; the carving cut by the saw at the point it touches, with chips;
   no prop changes shape; every ornament carried is the one that's hung (no extra acorns or cones).
5. **Show the action:** close shots for the bench work, the star going on (Springs beside the fir, not in front),
   the gust (sway, snow streaks, a slower fall), the planting (a real hole and a soil heap, the watering into the
   pot), and the potting-out in clear view.
6. **The animals turn** (head first, then the body over ~0.8 s), never mirror in a frame.
7. **"Sprout has a pot ready, back home":** after the lift, the act break takes them home, where Sprout is waiting
   with the pot, so the line is true.

## Build staging (FK0017, 2026-11-06; storyboard approved by the owner 2026-11-06, "Yes")

Code: `families/keepers/christmas_flat.py` (beats), `christmas_flat_world.py` (world, light) and
`experiments/keepers_flat/ep14.py` (stills, check, render).

**Space rules:**
- The Keepers walk in one lane (feet on G) and never pass each other in it.
- The fir, the pot, the bench, the lanterns and the props stand just behind that lane (BACK), so a Keeper can stand
  in front of the fir or walk past in front of it, painted nearer.
- Glo floats behind everyone.
- Line order, front to back (right to left on the way out): Springs, Digs, Sprout, Twigs, Wheels, Hans, Glo. It is
  the same at the bench, right to left.

**Places (world x):**
- FIR0 2300: the fir on the path.
- SPOT 3300: the pot, ready by the lanterns.
- BENCH 3700-4600: bench work, with the treehouse behind it.
- CONE_PINE: behind Digs' bench place, so he picks cones at its foot without walking past anyone.
- CLEARING: 6000+.

**Beats:**
0. **Hook:** they walk in from the left. Springs walks past in front of the fir. Digs stops just past it, so it is at
   his left paw.
1. **Potting:**
   - Digs digs round its foot with his left paw (soil flies), then lifts it out by its ball of soil.
   - They walk right to SPOT, the fir carried at Digs' left paw (Sprout keeps clear behind it).
   - Digs lowers it into the waiting pot. Sprout steps up and waters it.
2. **Bench** (left to right): Hans braids the garland (several tentacles); Wheels paints the stars Twigs carves;
   Twigs carves stars and acorns (shavings fall); Sprout ties ribbon bows; Digs picks cones off the snow at the cone
   pine's foot; Springs threads berries. Glo's flare lights the bench lantern.
3. **Decorating:**
   - They file past the fir right to left, each stopping in front of it to hang their own pieces, then moving on
     left: Hans (garland), Wheels (painted stars), Twigs (acorns), Sprout (bows), Springs (berries, then the star in
     one bounce), Digs (cones) last. Digs ends nearest the fir, on its left.
   - Glo lights the two lanterns. Dusk.
4. **Gust** (night, snow):
   - The fir sways, and the star tumbles off to the right into the snow.
   - The lantern flames shrink out, with a wisp.
   - Digs walks in front of the fir to its right, his hat lamp sweeping, finds the star at his right paw, digs it out
     and lifts it.
   - Springs hops up in front of the fir and takes it from Digs' paw. His first bounce falls short, the second puts
     it on top.
   - Glo relights the lanterns.
5. **Christmas Eve:** the snow eases. Deer, rabbit and fox come in from the right, and a chickadee lands on a lantern
   post.
6. **Forever home:**
   - Morning comes. Springs (bouncing) and Digs take the ornaments off into the box.
   - Digs carries the pot to the clearing and sets it down at his left. He digs a hole at his right, heaping the soil
     just left of it, lifts the fir out of the pot by its soil ball and walks right until it is over the hole.
   - He lowers it in and pushes the soil back. Sprout waters it.
   - Evening falls. "Goodnight, forest", 3-5 s of quiet, then the end sign.

**Changes while building** (2026-11-06; the reasons are the owner's standing rules):
- **Decorating from the fir's left side:** each Keeper walks past in front of the fir and works from its left,
  reaching over with the right hand. Standing in front of it hid it completely ("show the action").
- **The morning:**
  - After the visit they walk home to the treehouse for the night, and the fir glows on alone in the snow until
    morning.
  - They come back out with Hans first. He takes every piece off with his tentacles into the basket at the fir's
    foot ("the ornaments go back in their box").
  - He carries the potted fir to the clearing, sets the pot down, lifts the fir out by its soil ball and lowers it
    into the hole Digs dug. Digs pats the soil round it and Sprout waters it.
  - In a single lane, no one else could reach both the top ornaments and the box.
- **The bench:** the bench is a counter in front of Twigs and Wheels, so the carving and painting show. The bench
  work runs in two halves, with a slow pan between them.
- **Sprout's bows:** Sprout ties them as ornaments of their own, and Digs drops his cones into his own basket. No
  paw passes across a face.
- **Sprout's can:** Sprout keeps the watering can the whole episode. It lifts the can to pour, so the water goes in
  over the pot's rim.

## Earlier status (2026-11-03): storyboard APPROVED by the owner, with notes; waiting on the storybook look test
before it is built. The 3D look test was NOT approved (2026-11-03): the Keepers move to a soft 2D storybook style instead (see
"Storybook style" in `forest_keepers.md`); its look test goes to the owner first.
Owner, verbatim: "No, I like the storyboard. Perhaps the other [Forest] keepers can make some other ornaments as well.
It's okay if it's a little bit longer episode. I remember we're targeting for 6 to 10 minutes. One of the other things
is that they're out in the daytime, which I think is okay ... I'm wondering though if we need to start moving towards a
little bit more of a 3D look for this ... We want their walking to look more real. We want their building to look more
real. We want everything to look more real and so like when Wheels needs to turn to the side he would become thin or
invisible. We want more realistic stuff like head turning kind of like we did with the raccoon ... The first raccoon
was 2D and ugly. The second raccoon was 3D and very cute. I think the whole Forest keepers animation style is going to
need to move more towards that". What that changes:
- **More Keepers make ornaments**, not only Twigs (carving) and Wheels (painting): e.g. Hans braids little garlands
  with several tentacles at once, Springs threads berries, Digs brings pine cones, Sprout ties ribbons. 6-10 minutes.
- **Daytime is fine** (the beats already have the snowy village by day and a bright winter morning).
- ~~A 3D look~~ (3D look test `experiments/keepers3d/` NOT approved): **the soft 2D storybook style** instead
  (`forest_keepers.md`, "Storybook style"). The animation-quality rule there (Hans' legs and tentacles, Digs digging,
  real cutting and assembly) applies too.

Earlier: idea OK'd by the owner 2026-11-03 ("Yes", via Don's Asks).
It replaces the edible Christmas tree (owner: "They're going to eat a Christmas tree. Seems weird"). Order: Sprout's
episode (12, `forest_keepers_factory_trip.md`), Getting Ready for Winter (13, `forest_keepers_winter_ready.md`), then this.
Sprout is "it" (owner 2026-11-03). Sprout has two normal hands and carries a little watering can; Twigs has no teeth
since the factory (owner, FK0009 review 2026-11-03); the stills show both.

Nobody cuts a tree down. A little fir is growing right on the path where everyone walks; the Keepers lift it into a pot
so it's safe, it becomes their Christmas tree, and after the holidays they plant it in a sunny clearing.

**Promise -> payoff:** the title and cover promise the Keepers' own Christmas tree (cover: the little fir lit up in the
snow with the Keepers and the animals). The opening narration names the ending ("And at the very end, the little tree
gets its forever home in the forest"); the tree is decorated and lit by the middle, the animals' visit is the Christmas
Eve scene, and the planting in the clearing is the last scene before the end sign.

Every Keepers rule applies (`forest_keepers.md`): music box all the way (its own variant, a little Christmassy),
the Keepers' noises, Johanna slow and sparse (music ducked only under her), on-screen text in screen space, nothing
changes without a visible cause (every ornament carved, painted and hung by someone; the lanterns lit by Glo's flare
from under his dome), nobody walks through anyone, AI-voice line on upload, end sign with seven Keepers.

## Beats

0. **The hook** (~15 s): the snowy village. Narrator: "It's nearly Christmas, and there's a little fir growing right
   where everyone walks. And at the very end, the little tree gets its forever home in the forest."
1. **Potting** (~1 min): Digs lifts the fir out with its ball of soil (so nobody steps on it); Sprout has a clay pot
   ready, they set it in and Sprout waters it.
2. **Ornaments** (~1.5 min): at a workbench under a lantern, Twigs carves wooden stars and acorns with his new blade
   (curly shavings; his hands hold the wood), Wheels paints them red and gold.
3. **Decorating** (~1.5 min): Hans hangs the ornaments with his tentacles, Springs bounces up with the star for the
   top, Glo's flare lights the little lanterns one by one.
4. **Christmas Eve** (~1.5 min): the lit tree in the falling snow; winter animals that really are out and about in
   winter come to look: a white-tailed deer, a red fox, a cottontail rabbit, a chickadee (no hibernators, no
   migrants). Narrator, softly, once.
5. **Forever home** (~1 min): after the holidays, a bright winter morning: Digs digs a hole in a sunny clearing, the
   fir goes in, Sprout waters it, the ornaments go back in their box for next year. Narrator's goodnight. End sign.

## Storyboard stills (`forest_keepers_christmas/`, made by `families/keepers/christmas_board.py`)

0. `0_storyboard_hook.png`: the seven Keepers find the little fir on the path; the narrator's hook written out.
1. `1_storyboard_potting.png`: Digs lifts the fir with its soil, Sprout waits with the pot.
2. `2_storyboard_ornaments.png`: Twigs carves a star with his blade, Wheels paints the baubles.
3. `3_storyboard_decorating.png`: Hans hangs ornaments, Springs bounces up with the star, Glo's flare.
4. `4_storyboard_christmas_eve.png`: the lit tree, the deer, fox, rabbit and chickadee, the Keepers watching.
5. `5_storyboard_forever_home.png`: the fir planted in a sunny clearing, Sprout watering, the ornament box.
