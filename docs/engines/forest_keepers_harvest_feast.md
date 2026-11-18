# Forest Keepers episode 8: The Harvest Feast (`FK0005_harvest_feast`, ~7:40 since the second rework, 16:9)

Thanksgiving episode (owner request 2026-10-30; upload well before Nov 26). The water wheel from episode 4 now turns a
little acorn mill; the Keepers grind flour, build a long table and a clay oven, bake round loaves and acorn pies, and
share a harvest feast with the forest animals from episode 4. Calm and warm, no race. Also the first FK episode rendered
in a cloud session (render time logged below, as a test against the owner's PC: ~3000 s for the 3-minute FK0004).

## As built (2026-10-30)

**1. The acorn mill (0:00-0:38).** An autumn night at the water wheel (episode 4's stream, race and wheel, the
episode 2 bridge). Next to the wheel stands a small open-fronted MILL hut: the wheel's axle pulley drives a belt to a
pulley on the first of two round stone rollers (millstones seen face-on); their wooden gears mesh in the middle, so
they turn towards each other. A hopper above the nip, the flour sack below it.
- **Hook (0:00-0:08):** close on the oak's branch. A red squirrel runs along it and knocks an acorn loose; it falls
  (real gravity) into the basket on Wheels' head. Wheels rolls to the mill, Hans lifts the basket with two tentacles
  and tips it into the hopper, the acorns tumble in, drop one by one between the stones (`FEED` 0.42 s) and the
  flour runs into the sack with a soft puff. Glo: "?", then a pie bubble. Names float.
- **Every step twice more (0:08-0:31):** Springs bounces up two stubs on the trunk onto the branch and bounces it;
  four acorns drop into the basket at every bounce (the branch dips and swings back). Wheels carries each load to the
  mill, Hans tips it into the hopper. 38 acorns are milled; the sack fills only while flour runs (`sack_fill` counts
  milled acorns). The squirrel climbs up the trunk, Glo lights the branch.
- **The sack (0:31-0:38):** a pan from the wheel along the belt to the stones and the sack; Digs pats the flour down
  and holds the sack, Hans ties its neck with twine (tentacle round and round), Wheels lifts it onto his head and rolls
  off. (The act ends on a fade; in the clearing the sack stands by the bench.)

**2. The long table and the clay oven (0:38-1:26).** The clearing right of the treehouse village (episode 4's
birdhouses, hedgehog and bunny houses), two trees with a string of six unlit lanterns between them, an owl on a branch.
The table is two fallen logs lying side by side (the rails) with ten cross planks.
- Twigs trims the ten planks at a saw station: Wheels slides each rough board from the stack onto the sawhorses
  against a stop block, Twigs cuts its rough end off at the chalk line with his left wrist saw (offcut drops), Wheels
  lifts the plank onto the stack on his head. Every plank is the same length (`PLANK_L` 170, stats `planks_even`).
- Wheels carries the ten planks to the table, Hans takes them off his head one by one with two tentacles and lays them
  across the logs (the plank turns from lengthwise to across as he lays it), from the right end to the left, evenly
  spaced (110 px slots). Springs hops from plank to plank on the tabletop and bounces each one down.
- Glo lowers his spirit level onto the middle of the table: the bubble swings and settles in the middle, chime
  (`table_level`).
- Meanwhile Digs builds the clay oven: six trips to the clay pit, one coil of clay on his shovel each time, laid round
  the dome from left to right; Springs stomps the clay soft in the pit; Hans carries firewood from the pile to the oven
  and smooths each new coil with a tentacle. A seventh trip makes the chimney. Twigs saws two firewood logs in half on
  the chopping stump, Digs pushes the wood into the oven mouth on his shovel.

**3. Bake (1:26-2:14, no cut).** Glo floats to the oven and his light flares: sparkles drift down the beam onto the
wood, embers glow, then flames; smoke curls from the chimney. At the bench (a bread board on it):
- Hans scoops three tentacle-fuls of flour from the sack into the bowl, pours water from the jug, kneads (the dough
  squeezes), turns the dough out on the board.
- Twigs cuts the dough into six pieces with three passes of his wrist saw; Hans spreads them evenly (`board_even`) and
  shapes four round loaves; Springs hops onto the bench and bounces the two pie bases flat; Hans fills them with acorn
  mash from the pot; Twigs scores a cross on each loaf with his saw.
- Digs carries them two at a time on his shovel into the oven (two rows of three in the mouth, the back row smaller).
  They turn golden only in there, over ten seconds (`bake`), never off-screen.
- Hans carries the stack of plates and cups to the table and sets eight places and the hedgehog's plate on the ground at
  the left end (`settings_even`). Glo floats along the lantern string and lights the six lanterns one by one with his
  light flare, right to left (`lanterns_even`), each with a music-box note.
- Digs takes the bread out onto the board, Wheels lifts the board onto his head and rolls it to the table.

**4. The feast (2:14-2:58, no cut).** Hans lifts the six dishes off the board onto the middle of the table, evenly
spaced (`food_even`). The four birds hop out of their round holes onto their perches and fly to the table's back edge;
the two bunnies and the hedgehog come out of their doors (cut by the door edges with `feast_props.clip_inside`, never a
patch over them) and hop / trundle to the table. Everyone takes a piece onto their plate: Hans with a tentacle, Twigs
cuts his with his saw, Wheels with his pincers, Digs on his shovel, Springs with his hands, Glo hangs low over the table
and brings the hedgehog a piece. Then bites (each with a chew, a soft "mm" to the camera and crumbs), the bunnies
nibble the loaves, the birds peck crumbs, a clink of cups, fireflies. The camera pulls back slowly over the lit table,
the village and the forest.

**5. End sign** (every Forest Keepers video).

Seating, left to right behind the table: Glo, bunny, Hans, Twigs, Springs, bunny, Wheels, Digs; a bird between every
pair; the hedgehog at the left end.

## Owner review of the 5:41 re-render (2026-10-30): not approved

"Too many mistakes": still rushed at the start (the acorn fell and Glo had the idea while the name tags were still up);
1:50-2:00 the belt was crossed and didn't look like it ran on the wheel, the millstones were hidden behind the pulley
and a gear, flour came out while nothing seemed to turn, and Hans kept hold of the pulley while it turned; ~2:55-3:10
Hans' tentacle followed each piece of clay 2-3 s after it had moved into place; the planks being laid slid under the
front log and popped on top; Glo carried a spirit level for a minute for no reason; the bread "warped" to the table
and back into Digs' hands; the dip-to-black jumps between the oven and the table jerked the eye. "Slow on purpose,
like Mr. Rogers, to teach patience", never jump cuts. Every point was a bug in the cloud session's code:

- **Pulley and gears over the stones**: after they were fitted, `disc_state` never left 'held', so they were drawn in
  Hans' hand layer (over the stones), never turned, and Hans' tentacles stayed on the pulley. Now they reach a 'fit'
  state and are drawn behind the stones, turning.
- **The drive**: no crossed belt. A plain open belt runs from the wheel's axle pulley to a small leather pulley on a
  third gear left of the stones (on an arm from the front post). The wheel turns anticlockwise, the drive gear with it;
  it turns the first stone's gear clockwise and that one the second's anticlockwise: both stones still move down at
  the nip (`stones_turn_in`, `gears_mesh` checks all three). The stones moved 25 px right to make room. Build: Twigs
  slices three gear discs (the top one first), Springs holds each while Twigs notches it, Hans takes it and fits it;
  the pulley lies by the coiled belt from the start, the arm is a fifth offcut that rides on Wheels' head.
- **Opening**: the build act has 8 s of calm first (`FeastAct.LEAD`): a slow drift in on the group while the name tags
  show; the squirrel only starts when they are gone.
- **The oven**: four thick coils, each laid by Hans: his tentacle tip is the end of the coil as it goes round (taken off
  Digs' shovel, whose lump shrinks as he lays it), a second tentacle smooths just behind it; then the chimney.
- **Planks**: the plank being laid is drawn after the table (never under the front log); the last plank cut is on top
  of Wheels' stack and is laid first. 1.7 s per plank.
- **No level.** Glo just lights the way, then the lanterns and the fire.
- **No cuts anywhere** (the table, bake and feast acts had dip-to-black cuts): one wide shot of the saw and the oven,
  the oven close up, the camera follows Hans to the table; the lanterns (Glo) and the plates and cups (Hans, from a
  stack on a stump left of the table, each plate and cup carried over the table) are now done at the end of the table
  act, then everyone strolls to the oven with the camera. The bake act stays at the oven: everyone waits by the warm
  oven while the bread bakes, then follows Wheels and the bread to the table. The feast: Hans serves slower, then the
  camera drifts to the houses as the animals come out and back with them.
- **The bread**: every loaf and pie is wherever Digs' shovel blade is while he carries it, and slides off only where it
  is set down (it used to slide 200 px to the board in 0.25 s while Digs stood at the oven).
- Calmer clock: the village acts run 1.3x slower than written (was 1.2x). 7:40 in all.

New engine checks for every FK video (`families/keepers/scene.py`): `prop_jumps` (each act lists what it moves in
`props(t)`: food, plates, planks, discs, the board ...; a jump between two frames is a WARNING, like `teleports`),
`act_cuts` (any dip-to-black cut inside an act is a WARNING), camera pans now at most 250 screen px/s (was 300). This
cut: teleports 0, fast_moves 0, prop_jumps 0, act_cuts 0, cam_fast 0 (max pan 247 px/s, zoom 0.15/s).

## Rework (2026-10-30, after the owner's review) - 5:41, rendered locally (LOCAL_RENDERS job 8)

Acts: `build` (0:00-2:05), `mill` (2:05-2:41), `table` (2:41-3:38), `bake` (3:38-4:36), `feast` (4:36-5:29), end sign.
- **build** (`BuildMillAct`): the squirrel's acorn bonks Digs' hat and rolls onto the acorn heap, Glo's idea (bread).
  Digs digs six holes; Twigs cuts four posts (590 px) and two stone stands at the stop block, Wheels carries them;
  Hans stands each up into its hole, Springs tamps it; Glo's string line over the post tops (level). Hans rolls two
  round stones up from the brook bed, Digs taps the axle hole and six grooves into each, Hans lifts them onto their
  forked stands; Glo checks the gap with an acorn. Twigs cuts two beams and four roof boards, Hans fits the beams and
  the roof; the roof boards' offcuts become the hopper. Twigs slices three discs off a stump and notches 24 teeth into
  two of them while Springs holds them; Hans fits the pulley and the two gears (they mesh). Hans loops the belt from
  the wheel's axle to the stone pulley with one twist (`crossed_belt`): the stones spin up turning IN, both moving down
  at the nip (stat `stones_turn_in`, computed). A test acorn goes through: a puff of flour.
- **mill**: two basket loads (24 acorns) shaken off the branch by Springs, tipped into the hopper, milled into the
  sack; Hans ties it, Wheels carries it off.
- **table / bake / feast** as before but 1.2x slower (`VillageAct.STRETCH`), with the oven now stone and clay
  (`draw_oven`: hearth slabs, base stones, jambs and lintel round the mouth, clay coils smoothed by Hans into one grey
  dome, soot over the mouth once it burns; it used to draw 8 rings of which 6 were laid, a flat striped top).
- Camera: calm shots; long trips between the oven and the table are a soft dip to black inside the act (`act.cuts`,
  `Scene.cut_dim`) instead of a fast pan. New engine check for every FK video: `cam_max_pan` (screen px/s),
  `cam_max_zoom` (/s), `cam_fast` (moves over 300 px/s or 0.2 zoom/s, printed as a WARNING). This cut: 283 px/s,
  0.16/s, 0.
- Sim: teleports 0, fast_moves 0, cam_fast 0, 0 folded notes; all line-up stats true.

## Owner review of FK0005 (2026-10-30): not approved, rework into a 5-6 minute episode

- **We never see them build the mill; it is just there.** Keepers episodes start with a build. Episode 8 gets a full
  mill build first (posts, walls and roof, two dressed millstones, gears, hopper, belt), which makes it 5-6 minutes.
- **The millstones turn the wrong way**: the open belt turned the first stone the same way as the wheel, so at the nip
  the stones moved up, as if pushing the acorns out of the top. Both stones must turn in towards the nip (a crossed
  belt), pulling the acorns down between them.
- **The oven looks like it is made of wood** (flat brown coil bands with seam lines read as planks). An oven is stone and
  clay: a stone hearth and base, clay coils smoothed together into one round dome, stones round the mouth, soot.
- **Pans and zooms are too fast and make it feel shaky** (measured: the bake act panned at up to 1,035 screen px/s,
  8.8 s above 400; FK0004 stays at ~400 or below; plus a new framing every 2-3 s). Slow, few camera moves; the speed
  is to be checked in code like teleports.
- It felt rushed: every step was squeezed to fit ~3 minutes. (Not the cloud render: that only measured render speed.)

## Checks (stats in `video_log/FK0005_harvest_feast.json`)

`teleports` 0, `fast_moves` 0, 0 folded notes; `acorns_milled` 38, `planks_even`, `table_level`, `oven_rings` 6,
`board_even`, `settings_even`, `lanterns_even`, `food_even`, `animals_seated` 7; ~100 Keeper voices.
Springs can't jump 530 px onto the branch in one hop (the take-off would break the no-warp limit), so he bounces up two
stubs on the trunk; his bounces always start after a hop has landed.

## Rules that apply

Everything in `forest_keepers.md`: theme music all the way, end sign, Hans' tentacles, Twigs' wrist saws, Glo's
tendrils only from under his dome (lighting and fire by his light flare), things line up (stop block, slots, level),
real gravity (acorns, hops), nobody warps, the Keepers talk, small touches of life (the squirrel, the owl, fireflies,
the birds), nothing assembles itself (every coil, plank, plate and dish is put there by a Keeper on screen), no magic
changes (the flour comes out of the stones, the bread browns in the lit oven).

## Code

`harvest_feast.py` (acts `mill`, `table`, `bake`, `feast`; `Moves` for Springs' real-gravity hops; `VillageAct` draws the
clearing in depth order: Keepers behind things, the stations, the table, the bench, then everyone in front),
`feast_props.py` (oak, squirrel, owl, millstones, gears, hopper, sack, table logs and planks, clay oven, bread, pies,
plates, lantern string, `clip_inside`), params `harvest_feast.yaml`; chatter pictures "acorn", "pie", "bread" in
`chatter.py`.

## Cloud render (2026-10-30)

`python -m engine.render families/keepers/params/harvest_feast.yaml` took **2,332 s wall clock** (38:52; 2,300 s inside
the renderer, ~5.0-5.7 fps) for 190.0 s of 1080p60 (11,400 frames, 280 MB) on 4 vCPU Intel Xeon @ 2.8 GHz with 15 GiB RAM.
The renderer uses one core, so the extra cores don't help. The owner's PC: 3,000 s for the 192 s FK0004, so the cloud
machine was ~1.3x faster per video second. teleports 0, fast_moves 0, 0 folded notes. Audio: 4.3% of the energy at
1-3 kHz, 0.2% at 3-6 kHz, rms 0.163 (FK0004: 3.4%, 0.1%, 0.164).
