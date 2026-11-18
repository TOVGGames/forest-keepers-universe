# Forest Keepers episode 5: First Snow (`FK####_first_snow`, ~5:30, 16:9)

Owner pick (2026-10-27), from the options after FK0001: in season for November, ends on a race (the format
already doing well), and snow piling up on everything is "oddly satisfying". FK0001's end sign asks viewers for
ideas; none were in yet (it wasn't uploaded), so this one is ours. Pick a comment idea for a later episode.

Owner note for this episode and every one after it: **the Keepers talk more**. Their little cute noises come more
often, and they are talking to the audience (see "The Keepers talk" below).

## Story

**1. First snow (~0:40).** Night at the treehouse, everything from episode 4 in place: four birdhouses on their
posts, the hedgehog and bunny houses, lanterns lit. The first flakes come down and settle; the roofs, posts,
branches and ground slowly go white. The birds peek out of their holes. The Keepers come out onto the platform
and turn to us: "ooh!" Springs catches flakes on his tongue, Hans holds a tentacle out to catch one. Wheels rolls
out into the snow, his wheels spin, snow sprays and he slides back: "uh-oh". Digs gives him a push, everyone
giggles. Twigs gets an idea: a speech bubble with a little picture of a sled in it.

**2. The sled workshop (~2:10).** An outdoor workbench by the woodpile at the foot of the hill, lanterns on posts.
Three sleds, one for each pair of Keepers, each painted in its riders' colours.
- CUT: Wheels pushes each plank against a stop block, Twigs saws it with his wrist saws at the pencil line (every
  slat the same length), Hans stacks the slats.
- BEND: Glo lights a little fire under the steam box; Hans takes the steamed runner strips out and bends two at a
  time around the curved form, his tentacles wrapping the wood, and clamps them.
- BUILD: the runners stand in the jig, the crossbars go on, the slats are laid evenly spaced on top (alignment
  check), Springs bounces each peg home.
- PAINT + ROPE: Glo paints each sled, Hans ties the pull rope.

**3. Up the hill (~0:50).** Digs packs three straight lanes down the hill with his shovels (snow spray), Glo
plants lanterns along the run, evenly spaced (string-line check). Everyone pulls the sleds up to the top. The
start line, the moon, the forest below. A countdown from everyone: three bubbles, 3, 2, 1.

**4. The race (~1:10).** Down they go, three sleds side by side in their lanes: real sled physics on the slope
(gravity, friction on snow, a little air over the bumps), snow spraying off the runners, lanterns whizzing past,
everyone going "weee!" to the camera. The birds fly alongside. A photo finish into the soft snowbank at the bottom:
a big puff of snow, everyone pops out with snow on their heads, giggling.

**5. Cozy (~0:25).** Back at the treehouse, snow still falling, the animals' lanterns glowing, the Keepers on the
platform. Slow pull-back.

**6. End sign** (as every Forest Keepers video), with snow falling on it.

## The Keepers talk (engine, every video from episode 5 on)

- More voices, about one every 4-6 seconds on average instead of ~20 in a whole episode: reactions to what is
  happening (wonder, a giggle, effort, a happy "yay", "uh-oh", a question, shivering "brr", "weee!").
- Each Keeper keeps its own voice (pitch) and gets its own vowel colour (Hans deep and round, Springs bright).
- When a Keeper talks it **looks at the audience** (eyes to the camera), does a little bounce, its mouth moves
  (Glo's lantern flickers brighter instead, she has no mouth), and a small speech bubble pops up with a picture,
  never words: ! ? a heart, a music note, a star, a snowflake, a sled, numbers for the countdown.
- Between the story beats the scene fills quiet stretches with asides: a Keeper on screen turns to us and reacts.
- All soft and warm (owner hears bright 1-5 kHz sound as harsh): low-passed voices, quiet.

## As built (2026-10-27)

Runtime 5:36 at 1920x1080/60: first snow 0:00-0:44, the sled workshop 0:44-3:16, up the hill 3:16-4:04, the race
4:04-4:57, cozy 4:57-5:24, end sign 5:24-5:34. Changes against the plan above:
- The idea is Twigs' (a bubble with a sled in it) after Wheels gets stuck and Digs pushes him free.
- Workshop: Digs carries planks 2 and 3 over from the pile; Twigs saws 15 slats at the stop block (three planks);
  Hans bends one pair of runners per trip (pulls the hot strips out of the steam box onto the bed, curls both
  noses at once, clamps, stacks the pair); for each sled he fetches all five slats at once, one per tentacle, and
  puts them on tail to nose while Springs hops along bouncing each one onto its pegs. Twigs trims each new rope with
  his saw. The sleds are built nose-right (the way they go up the hill) and race nose-left.
- Hill: Glo lights the first lantern and a spark runs up the run lighting all 27 (an ultra-wide shot of the lit
  line up the hill); the front sled sets off first so the three teams spread out on the way up.
- Race: three lanes side by side, further lanes higher and smaller (`sled.LANES`, `LANE_SCALE`). Physics in
  `sled.Ride` (g 2600, mu ~0.04, drag 1e-4 v^2, a sled leaves the snow when v^2 * curvature > g cos(slope)): ~34 s
  down a 4,450 px drop over 41,000 px, top speed ~1,350 px/s, three airs each (~60 px), finish 0.14 s and 0.16 s
  apart into the snowbank. The birds fly along for a stretch. After the bank everyone hops off and lines up.
- Checks in the stats: `teleports` 0, `fast_moves` 0 (`fast_ok` for the race: sleds are faster than walking),
  `sleds_even`, `lanterns_even`, `race_finish_s`, `race_airs`, `voices` (beats + asides). Audio: 0 folded
  notes, 5.6% of the energy at 1-3 kHz (FK0001: 6.9%), 0.2% at 3-6 kHz.
- Code: `first_snow.py` (act 1, shared SnowAct), `sled_shop.py` (act 2), `hill_race.py` (acts 3-5), `sled.py`
  (sled drawing, hill, physics), `snow.py` (snowfall, snow caps), `chatter.py` (talking), params `first_snow.yaml`.

## Owner notes on the render (approved 2026-10-27, FK0002 stays as is)
- Bad physics: the sleds looked like they were popping a wheelie, nose up the whole way down. A sled lies parallel
  to the hill. The cause was a sign error: `hill_ang` went into `draw_sled` negated, so on the 6 deg slope the sleds sat ~12 deg nose-up.
  Fixed after the render (`hill_race.py`); the sleds now lie flat and only tip while climbing a bump.
- Loved: the birds flying along over the sleds during the race. Keep adding small touches of life like that.

## Rules that apply
Everything in `forest_keepers.md`: theme music all the way, end sign, Hans' tentacles, Twigs' wrist saws,
things line up (stop block, string line, even slat spacing), real physics (sleds, jumps), **nobody warps**
(`teleports` and `fast_moves` must be 0 before the render), centred treehouse door.
