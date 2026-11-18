# Foundry – Forest Keepers: Halloween (episode 3, ~8:30 16:9)

Owner + Toby brief (2026-10-26): the Keepers **go back to the factory** and forge, craft, cut and
sand lots of parts. **It must not be clear until around the middle that they are making Halloween
decorations.** Then they gather everything up, take it back to the forest and **decorate their
treehouse for Halloween**. Halloween is 2026-10-31, so this ships before then; the forest-workshop
idea (`forest_keepers_animal_houses.md`, built as episode 4) waits until after.

Owner rules that apply (2026-10-26):
- Quality and realism over speed: "this isn't going to go anywhere if we do low quality".
- **No monster goes back through the assembly line to be fixed.** They come back as workers.
- **Hans works with his own tentacles, and they look like tentacles** when he uses them: same
  colour, taper and suckers as his legs, curving and curling around what he holds
  (`Monster.reach_tentacle` in `products/monster.py`). Never a stick arm.
- Things line up: pumpkins, bulbs, bats and rungs are evenly spaced and square. The scene checks
  its own spacing and logs `alignment_ok` in the stats.
- Never scary-violent: cute Halloween (smiling jack-o'-lanterns, friendly ghosts, little bats).

## Structure

**1. Back to the factory (~0:35).** Open on the finished treehouse from episode 2 (lanterns lit,
moon). Names float over everyone. They climb down (Springs bounces, Glo floats), walk through the
night forest to the cliff door of the factory, the door rolls up, in they go.

**2. The night shift (~4:40).** The factory hall: seven work spots in a row, a big dark sign board
over the hall. Each Keeper runs a machine with its own body as the tool; the camera visits them in
order. Every product is shown only as anonymous parts until the reveal:
1. **FORGE** – Digs shovels coal into the furnace (the glow rises with every shovel); Hans tips
   the crucible with his tentacles and pours molten iron into a row of flat moulds; the castings
   cool from orange to black iron and Hans lifts them out: scalloped crescents and little ovals.
2. **LATHE** – Wheels clamps wood blocks in a lathe and turns them into smooth round balls
   (eight big, three small), shavings flying.
3. **PRESS** – Springs bounces on a foot press that stamps the iron crescents into crisp
   scalloped shapes (bat wings, but nobody can tell yet).
4. **CUT** – Twigs cuts white cloth into big circles with his sharp teeth, snip snip.
5. **GLASS** – Glo lights little glass bulbs one by one (a string of orange and purple) and
   eight candle stubs.
6. **SAND + PAINT** – Hans sands four balls at once, one in each tentacle; then the big balls go
   through the spray booth and come out orange with darker rib stripes and a green stem.
7. **ASSEMBLY (the reveal, ~3:50, the middle of the video)** – Twigs carves two triangle eyes
   and a smile into the first orange ball with his teeth, Glo drops a lit candle in: it's a
   **jack-o'-lantern**. The big board lights up **HAPPY HALLOWEEN**. Then the rest: all eight
   pumpkins carved and lit, Hans pins wings to the little ovals (**bats**, a test flap), the white
   cloth goes over the small balls and gets two eyes (**ghosts**), the bulbs are strung (**lights**).

**3. Haul (~0:35).** Everything goes into Wheels' wagon and the crates the others carry; out
through the cliff door and back through the forest to the treehouse.

**4. Decorate (~2:40).** Each Keeper with its own body as the tool again:
- Wheels and Digs set four jack-o'-lanterns along the ground in front of the tree, evenly spaced;
  Springs carries the other four up to the platform edge, two per real-gravity jump.
- Springs jumps up to hang the six bats from the branches; they swing (damped pendulums) and flap.
- Hans hangs the light string along the platform rail with several tentacles at once; it sags in
  a real catenary between its hooks.
- Glo floats the three ghosts up to the branch tips; they sway.
- Finale: Glo lights the jack-o'-lanterns one by one, then the lights string; the forest animals
  (bunnies, hedgehog) come to look; everyone gathers on the platform; slow pull-back with the moon.

## As built (2026-10-26)

Runtime ~6:35 at 1920x1080/60. The reveal (first jack-o'-lantern lit + HAPPY HALLOWEEN board) is at ~3:31,
54% in. Changes against the plan above, all for readability or physics:
- Ghost heads are four **frosted glass globes** Glo lights at the GLASS station (no small lathe balls), so the
  ghosts glow softly from inside.
- The paint booth makes **plain orange balls**; the pumpkin ribs, stems and faces only appear at the
  assembly table (Twigs carves the ribs, then the face), so nothing says "pumpkin" before ~3:20.
- The sign board shows nothing at all until it lights; letters light one by one at the reveal.
- Parts never appear on their own: Hans lifts each mould's castings into a tote and pushes it to the
  press; the lathe drops each ball onto a ramp that rolls it onto the belt; the belt drops the painted
  balls into Wheels' wagon; Twigs carries the cloth stack, Glo the bulb string and the globes, Springs the
  bin of stamped wings. At home: Digs drives in two forked stakes for the carrying pole; Wheels and Digs
  carry the jack-o'-lanterns from the wagon; Springs jumps the deck ones up and hangs the bats at the top
  of real-gravity jumps; Glo floats the ghosts to the branch tips; Hans climbs the ladder (tentacles on
  the rungs) and hooks the light string on under the deck.
- Hung things (bats, ghosts) swing as damped pendulums with the real g of the scene.
- Code: `keepers/halloween.py` (return, haul, decorate, the treehouse), `keepers/workshop.py` (the
  factory), `products/decor.py` (decorations), `Monster.work_tentacle` in `products/monster.py`.

## Owner feedback on FE0014_halloween (2026-10-27): approved, published as-is

- ✅ "Massive changes for the better." Published unchanged for Halloween.
- ✅ **The tentacles are the standard from now on.** Hans's working tentacles (`reach_tentacle` /
  `Monster.work_tentacle` in `products/monster.py`: Bézier spine with a wave, tapered, outline + light
  stripe + suckers, tip curling around what it holds) are how tentacles are done in every future video.
- For next time (not for FE0014):
  - **Entering the factory, they slide through the wall before the door.** Cause: `Hill.front()` in
    `keepers/halloween.py` draws the rock face *left* of the door (from `X - 40` to `d0`) over the monsters,
    so on the walk from their waiting spots (`wait_x`, just left of the cliff) to the opening they vanish
    behind solid rock, then reappear in the doorway. The rock left of the door belongs behind them
    (draw it in `back()`); only the rock right of the opening (`d1` onwards) and the lintel above it
    should cover them, so they disappear behind the right-hand jamb as they walk in. Check the same in
    `HaulAct` coming out.
  - **Twigs gets cutting tools on his hands**: small circular saw blades on his hands/wrists, since he
    does most of the cutting (instead of cutting with his teeth). Spinning blade, sparks/sawdust when cutting.

## Sound
Night forest bed (pad + crickets) for acts 1, 3, 4, crossfading to the industrial factory bed inside
(`keepers_bed` with `forest_spans`). New: a light Halloween tune for the decorating finale (A minor
music box, same instrument as before, MIDI 57-84). Pitched notes stay in MIDI 36-96.

## Files
- Scene acts: `families/foundry/keepers/halloween.py` (return, haul, decorate) + `keepers/workshop.py`,
  decorations in `families/foundry/products/decor.py`.
- Params: `families/foundry/params/keepers_halloween.yaml` (`name: halloween`, renders are
  `FE####_halloween`).
