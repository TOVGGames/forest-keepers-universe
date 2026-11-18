# Forest Keepers episode 6: The Treetop Marble Run (`FK0003_marble_run`, 5:38, 16:9)

Owner pick (2026-10-27), from the options after FK0002: no holiday episode yet (no Thanksgiving, no Christmas).
Marble races are the channel's best-performing format (Bright Lights); this brings them into the Keepers series as
a "how it's made" build with a race finale. Every Keeper gets a marble in its own colour, so viewers have one to
cheer for (like the "pick yours" races).

Late autumn night: the first snow from episode 5 has melted, leaves are falling. Everything from episodes 4-5 is
in place: the treehouse (door centred), the four birdhouses on their posts, the hedgehog and bunny houses.

## Story

**1. The ball (~0:35).** At the treehouse. Springs bounces a little wooden ball on the platform; it rolls off the
edge, bounces down onto the ground (real bounces, each one lower), and rolls away past the birdhouses. Wheels races
after it and catches it. Everyone giggles. Glo watches the ball roll and has an idea: a bubble with a little marble
run in it (a zigzag track with a ball).

**2. The marbles (~0:55).** A workshop by two big old trees, right of the village.
- Twigs saws six cubes off a square beam at a stop block (every cube the same size).
- Hans drops the cubes into a tumbler barrel with sand; Wheels drives the rollers that turn it (his wheels spin,
  the barrel turns, clatter, sawdust puffs out).
- Hans opens the barrel: six round wooden balls roll out into a tray and line up.
- Glo paints each one in a Keeper's colour (Wheels blue, Hans orange, Twigs purple, Springs gold, Glo teal, Digs
  red) with a white band so you can see them roll. They go into a little rack.

**3. The run (~2:10).** Building the run between the two big trees.
- Twigs saws the track boards to length at the stop block (every ramp the same length), Digs carries them over.
- Springs bounces pegs into the two trunks, hopping up from peg to peg as he goes (real jumps); Glo checks each
  pair with the slope level (every ramp the same slope).
- Hans hoists each board up on a rope over a pulley on a branch, hand over hand with his tentacles, and lowers it
  onto its pegs. Six zigzag ramps, top to bottom.
- Springs' special part: a springy bumper at one turn, and a peg forest (a board full of evenly spaced pegs the
  marbles rattle down through).
- Digs digs a tunnel through the mound at the bottom; the last long ramp runs through it to the finish line by the
  animals' houses, into a catch tray. Glo lights the finish lantern.
- Test run: Wheels lets his plain ball from the opening go at the top. It runs the whole course into the tray
  (the first wide look at the whole run). Everyone cheers.

**4. The race (~0:55).** Springs jumps up the tree to the start gate (real jumps, branch to branch). Everyone else
stands at the finish. Countdown bubbles 3, 2, 1, Springs pulls the gate: six marbles roll out. Real physics
(pymunk): they roll down the zigzag, bunch up at the turns, bounce off the springy bumper, rattle through the peg
forest (the order shuffles), down the last ramp, into the tunnel (who comes out first?) and over the line. A little
standings strip shows the order with each marble's colour. The birds watch from the branches and hop off the rail
when the marbles come. The marbles roll into the tray in finishing order.

**5. Cheer (~0:20).** The winner's Keeper does a happy dance, everyone cheers; the six marbles sit in the tray in
order; the bunny noses the last one. Slow pull back to the whole lit run in the trees.

**6. End sign** (every Forest Keepers video).

## As built (2026-10-27)

Runtime 5:38 at 1920x1080/60 (FK0003_marble_run): the ball 0:00-0:35, the marbles 0:35-1:44, building the run 1:44-4:10 (test run from
3:32), the race 4:10-5:02, cheer 5:02-5:26, end sign 5:26-5:36. Changes against the plan above:
- The ball: Springs dribbles it on the platform; it gets away (real bounces, restitution 0.45, then it rolls and
  slows) and stops at the hedgehog's door; the hedgehog comes out and noses it back, Wheels flicks it up onto his head
  and keeps it there. Springs comes down the ladder rung by rung. Glo's idea bubble shows a little marble run.
- The marbles: six cubes at the stop block, Hans tips them into the tumbler barrel, Springs bounces the hatch shut
  from the top (via a crate: every hop real), Wheels drives the rollers from a pair of drive rollers, the balls roll
  out down a chute into the tray (5/7 g sin rolling); Glo's lantern flares up over each one for about a second, sparkles
  drift down to it and it takes its colour while Hans turns it. Wheels' plain ball sits in the first cup.
  (Owner after the first cut: Glo first painted with a long tendril that came out of the air above his head - "that's
  gotta go"; re-rendered into the same ID with the light magic, `MarblesAct.magic`.)
- The run (`marbles.py`): two big trees 1600 apart, five boards 1500 long, all at 3.43 deg, wide enough for six lanes
  (lane 0 nearest us; further lanes drawn higher, a little right and smaller - we look from a little above). Springs
  climbs branch stubs up each trunk and hops out to every peg spot (top board first); Glo checks each board with a
  string line and a level; Twigs trims every board at the line (the stop block sets the length); Hans hoists them on
  a rope over a pulley on a branch, top board first so a rising board never passes one already in place; Glo fits a
  stop at each turn. The peg forest (18 pegs, every gap wider than a marble, slanted half pegs at the walls) is pegged
  by Springs while it stands on the ground, then Hans lifts it onto TREE_A. Digs digs the tunnel through the mound;
  Hans lays the last ramp. Glo lights the finish lantern and a spark runs up the whole run lighting each turn (wide
  shot). The test run is Wheels' plain ball, released by Glo at the gate.
- The race: pymunk at 480 Hz, each marble in its own lane (its own space, the same course): solid wooden balls (moment
  2/5 m r^2), friction 0.9, and small hand-made differences (size +-4%, bounce 0.25-0.55, rolling resistance) that
  decide the race. `race_seed: 29` was picked from 40 seeds: 4 lead changes as a viewer sees them (a marble has to be
  half a marble ahead for half a second), the lead decided on the last ramp, all six within 0.81 s; Glo wins by 0.12 s
  over Twigs. A standings strip at the top left; the camera follows the leader and the middle of the pack at zoom 1.45.
  The watchers stand in front of the last ramp right of the finish arch; Springs pulls the gate lever at the top.
- Living touches: the hedgehog noses the ball back, the bunny hops over to sniff the marbles in the tray, leaves fall.
  Not built from the plan: the birds on the rail (the birds had their moment in FK0002), Digs carrying the boards
  (they wait stacked on the sawhorses under the run).
- Checks in the stats: `teleports` 0, `fast_moves` 0, `cubes_even`, `boards_even`, `slopes_even`, `pegs_even`,
  `string_line_checks`, `test_run_s`, `race_*`, `voices` (94 beats + 28 asides). Audio: 0 folded notes, 5.5% of the
  energy at 1-3 kHz, 0.1% at 3-6 kHz, the same level as FK0002.
- Code: `marbles.py` (course, physics, drawing), `marble_run.py` (acts ball, marbles, run, marble_race, cheer), params
  `marble_run.yaml`.

## Rules that apply
Everything in `forest_keepers.md`: theme music all the way, end sign, Hans' tentacles, Twigs' wrist saws, things
line up (stop block, slope level, even peg spacing: stats `ramps_even`, `slopes_even`, `pegs_even`), real physics
(marbles in pymunk, ballistic jumps), **nobody warps** (`teleports` and `fast_moves` 0 before the render), the
Keepers talk (chatter, picture bubbles), centred treehouse door. From FK0002's review: anything on a slope sits
parallel to it (the boards lie along their slope, the marbles roll on the track, and their painted band turns
with the real spin), and add small touches of life (the birds on the rail, the bunny at the tray).
