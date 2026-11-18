# Forest Keepers ep 8: The River Raft Race, flat remake (of FK0004)

The remake of episode 7's FK0004 in the flat picture-book look, now episode 8 (session 3 of the remakes,
`forest_keepers_remake_briefs.md`). The story is the same: a leaf boat with a ladybird goes over a little falls,
Wheels has the idea, six log rafts with leaf sails are built on the bank, and the rafts race down the brook over two
little falls. Ducks come to see at the finish. Six Keepers only (no Sprout), with the new faces and the ep 14 walks.
It is narrated (the grandmother voice, `narrator.py`) and has its own music variant `raftrace`.

Code: `families/keepers/raft_flat.py` (plan, Keepers, drawing, soundtrack), `raft_flat_world.py` (brook, falls, race
physics, rafts, animals), `experiments/keepers_flat/ep8.py` (`--times`, `--stills`, `--check`, `--render`).

## Staging (why it looks the way it does)

- **The brook is behind the path.** The path runs at the bottom of the frame, then a strip of meadow, then the brook in
  six lanes (lane 0 nearest). The view is a little from the left as well: each lane further back is drawn 16 px to the
  right. Without that, a boom or the finish line lying across the water would read as a vertical post.
- **The path follows the brook down the valley.** The water steps down 64 px at each falls. Beside each falls the path
  eases down over about 1100 px, and the Keepers walk on it (the `Slope` gait wrapper puts every foot on the ground
  under it). Wheels leans with the slope.
- **The falls are smooth chutes of glassy water** (owner rule: rafts lie flat on the water, never nose-up). A raft
  rides down parallel to the water, nose down, and levels out below. It is never in the air and never pitches nose up
  (`raft_pose` clamps the pitch, and the storycheck counts `nose_up`). The water below each falls circles back (the
  hole) and can hold a raft for a moment until a surge flushes it out.
- **The raft line is an old wooden slide on the bank**: two poles on trestles, falling gently to the right, with a stop
  block, a notch on the near rail at the trimmed length, three spring pegs, and its foot running down into the pool.
  Each raft stops at three stations, and the Keepers stand on the path between them:
  - **Station 1:** Wheels rolls to the washed-up driftwood and lifts a bundle of four logs up over his head (left
    pincer, then both). He lays it against the stop block with his right. Twigs trims the four ragged ends at the notch
    with his left blade, far log first, and each offcut drops onto the meadow. Then he taps the peg down.
  - **Station 2:** Hans works with three tentacles at once: one holds the twine ball, one steadies the logs, one winds
    two lashings. Then he taps the peg.
  - **Station 3:** Glo lowers a leafy twig from his bunch into the deck and lets go. His light flares over the leaf and
    it takes its Keeper's colour. Digs taps the last peg, and the raft slides down the slide's foot into the pool.
  - Each raft glides out to its lane at the start boom: the first one built goes furthest back.
- **Layering:** everything on the slide (the pile, the bundle in Wheels' pincers, the rafts, the offcuts, Glo) is drawn
  behind the Keepers the whole way. A raft passing behind a Keeper is simply hidden, and nothing ever pops in front of
  or behind a hand.
- **Springs' leafy twigs:** he springs up, hangs from the maple's low branch by his right hand and bounces three times.
  The live branch bends with him, and six leafy twigs shake loose and flutter down into the open. Glo gathers them into
  a bunch either side of his lantern.
- **Digs** clears the mud out of the slide's foot with mole strokes (`MoleDig`/`Spoil`). Small heaps of soil land
  either side.
- **The course** is told on the walk down to the finish, one landmark at a time: riffle, falls, lily pool, rapids,
  falls, glide. Then comes a dip to black between the two acts, to the start.
- **The start:** Springs stands upstream of the rafts, never in front of them. He bounces for 3, 2, 1 and pulls the
  pin out of a post. The rope that held the boom's free end slips off, and the current swings the boom round to lie
  along the far bank, behind every lane.
- **The race** is simulated (`raft_flat_world.Race`, seed 146): current per stretch and lane, drag, breeze on the
  sail, gravity down the chutes, the holes. The result: 3 lead changes. Wheels' raft leads from 8.4 s and Twigs' raft
  takes it right at the line, by 0.18 s. All six finish within 1.5 s. The whole race stays on screen (the camera
  follows the pack's middle at a slow pan). Springs hops after the pack on the path, always behind the last raft. The
  winner, Twigs' raft, was built 4th, not first.
- **The finish:** the Keepers watch from beyond the end boom (never in front of the finish pool). Twigs cheers, and
  Springs bounds in from the start. Then a mother duck and three ducklings paddle out of the reeds. Goodnight, 4.5 s of
  quiet, the end sign.

## Raft owners (built order -> lane)

Wheels (lane 5), Hans (4), Digs (3), Twigs (2, the winner), Springs (1), Glo (0).

## Checks (`ep8.py --check`, all 0 before a render)

Storycheck (`thing_jumps`, `size_snaps`/`size_drift`, `pops`, `unheld_motion`, `paper_thin`, `crab_walk`, `water_snap`,
`limb_stretch`, `depth_order`, `scale_mismatch`, `no_reason`, `hidden_action`), plus `teleports`, `foot_slips`,
`reach_miss`, `walk_through` (no two Keepers on the path overlap), `nose_up`, `elbow_snap` (monster.py's two-bone elbow
flips if a hand comes too close to the shoulder) and `promise_line`. There are no walls or doors here
(`wall_clips` 0). In the race, `hidden_action` covers the pack, and a raft leaving the frame counts too.

## Rendered (2026-11-06)

`FK0019_raft_race`, 4:56 at 1080p60, filed in `renders/Forest Keepers/` (HANDOFF: "Forest Keepers episode 8 – The River
Raft Race", awaiting owner review).
- Storycheck, one pass over every frame after the render: 0 on all 21 counts. That includes the elbow jumps, on the
  engine's `hang_arm` fix f71f9382.
- Audio: -13.7 LUFS, 0 folded notes.
- Lessons for the next flat episode:
  - Wheels keeps his own arms all episode. Switching between `hang_arm` and `arm_to` mid-scene pops the elbow.
  - Walkers turn 0.8 s ahead.
  - Arm moves are arcs that straighten the arm where its elbow would turn over.
  - One BLAS thread per render worker: about 0.3 GB each instead of 1.5 GB.
