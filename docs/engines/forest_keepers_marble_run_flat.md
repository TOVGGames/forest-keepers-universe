# Forest Keepers: The Treetop Marble Run, flat remake (session 2 of `forest_keepers_remake_briefs.md`)

The same story as FK0003 (`forest_keepers_marble_run.md`, owner-approved 2026-10-28), redone in the flat picture-book
look with only the original six Keepers (no Sprout), narrated by the Keepers' grandmother narrator, music box
throughout (its own variant, `marblerun`), and every owner rule since: natural walks (arm swing, Twigs `knee_fwd`,
Hans `WaveGait`), no warping, grain fixed to objects, storycheck at 0.

Code (new files only; shared modules untouched):
- `families/keepers/marble_flat_world.py`: the world (layers, light), the camera (pan + slow zoom), the page.
- `families/keepers/marble_flat_course.py`: the run between the trees, the pymunk race, drawing the run and marbles.
- `families/keepers/marble_flat.py` (+ `marble_flat_*.py` beats): the plan, the Keepers, the frame, the sound.
- `experiments/keepers_flat/ep7.py`: `--times`, `--stills`, `--check`, `--render`.

## Why the camera pulls back (a choice of this remake)

The flat engine pans in 2D at one scale; at that scale (K 0.72, Hans 440 px) the whole run and six watchers can't
share one 1920 frame. For the test run and the race the camera eases back to zoom 0.66 over ~8 s (slow: no screen
point moves faster than ~60 px/s), so the **whole race stays on screen** with no cuts and no camera chasing the
leader (sports realism). A pulled-back frame is painted at full scale on a bigger page and scaled down as a whole, so
the paper grain shrinks with the things it's printed on (grain stays fixed to objects).

## World (world x; ground `G`, the trees' and the run's feet `BACK`)

| x | what |
|---|---|
| 1900 | the treehouse (start: the ball) |
| 3950 | the workshop under its awning: the cube beam on the bench with a stop block, the tumbler barrel on rollers, Wheels' drive rollers, the chute and the tray |
| 5600 / 7200 | the two big old trees (TREE_A / TREE_B); the run hangs between them |

The run: three wide boards zigzag down (top board's high end at the gate by TREE_B, `BACK - 820`), each 1530 long and
2.25 deg, ends resting on pegs in the trunks, a stop at each turn (fixed to the next board's high end). Then the peg
forest on the front of TREE_A (11 dowels, every gap 66 px for a 52 px marble), then the last ramp right through the
tunnel in the mound, over the finish line into the catch tray at the foot of TREE_B. Six lanes side by side (lane 0
nearest). The marbles: one per Keeper in its colour with a cream band that turns with the real spin.

## Story beats

1. **The ball** (treehouse): Springs dribbles a little wooden ball; one bounce hits a root, it bounces away (each
   bounce lower) and rolls off along the path; Wheels rolls after it and scoops it up. Glo watches it roll: idea
   bubble (a little marble run). Hook names the end-only payoff: six marbles racing down from the treetops, who comes
   out of the tunnel first.
2. **The marbles** (workshop): Twigs slides the beam to the stop block and saws six equal cubes with his blade (they
   drop into the basket); Hans tips them into the tumbler and shuts the hatch; Wheels rolls onto the drive rollers and
   his wheels turn the barrel (clatter, sawdust puffs); Hans opens it: six round balls roll down the chute into the
   tray; Glo's lantern flares over each one and it takes a Keeper's colour (sparkles: a visible cause).
3. **The run** (the trees): Springs hops up branch stubs on each trunk with a little bucket of pegs and taps one in
   under every board end; Hans hoists each board on the rope over the pulley, hand over hand with his tentacles (top
   board first), it settles onto its pegs high end first; Glo checks each with a little level; Springs pegs the peg
   forest's dowels; Digs digs the tunnel through the mound from both sides (mole strokes, soil heaps); Hans slides the
   last ramp through it and carries the peg forest onto TREE_A with several tentacles at once; Glo lights the finish
   lantern. Test run: Wheels' plain ball goes first (wide shot).
4. **The race**: Springs takes the six marbles up to the gate; 3-2-1; he pulls the gate; six marbles race (real
   physics, whole course on screen, standings strip). Birds on a branch flutter up as the marbles pass.
5. **Cheer**: the winner's Keeper does a happy hop, the marbles rest in the tray in finishing order, a rabbit hops
   over and noses the last one; the narrator's goodnight; 4.5 s of quiet; the end sign.

## As built (2026-11-06/07)

Changes against the plan above, each for a physical reason:
- **One pulley, every board centred under it.** The boards are hoisted from an eye at their middle, so all three span
  the same x; a marble drops through a **slot** near each board's low end onto the board below (a lip at each end
  stops one that overshoots), the way real marble-run boards turn. Board hoists rise level, and on the way down the
  high end lands on its peg first and the board tips onto the other.
- **Pegs are set loosely in the trunks from the start** and Springs taps each one home (three taps, it sinks in with
  each). His arms are very short, so he can't carry a bucket and place pegs; tapping home is what he can really do.
  The peg-forest dowels are the same: set loosely in the panel, tapped home on hops.
- **The last ramp stands in two halves on legs** from the start, ending at the mound's faces; Digs digs the tunnel
  between them from the left (his right paw scoops, the soil flies back onto a heap on the path) until the far side
  breaks open. Hans lifts the peg forest onto TREE_A with four tentacles.
- **The marbles travel in the workshop's rack-tray**, which Wheels lifts off its legs and carries to the log bench by
  TREE_B. His plain ball from the opening sits in the tray's end slot.
- **The start**: a six-groove crate (the start line in a box). Springs carries it up TREE_B's stubs in both hands to a
  starter's perch and tips it at the gate (his left hand then lifts the gate by its cord). Test run: Wheels drops his
  plain ball into the crate. Race: Wheels lifts the tray's far end and the six marbles roll along it into the crate.
- **Front lane**: where a Keeper has to pass another (Springs going from TREE_A to TREE_B, Hans going to the peg
  forest) it steps a little nearer us and back, painted in front: nobody walks through anybody.
- **The finish** is right after the tunnel ("who comes out of the tunnel first?"); each lane has its own end stop in
  the catch tray, so the six marbles rest side by side.
- **Race seed** picked from a search of seeds for a close race (all six within about half a second, several lead
  changes), nothing steered: the physics runs in full and decides it.
- **Arms (Twigs, Wheels)**: monster.py's two-bone reach puts the elbow "down and out" and changes the elbow's side
  where the hand's direction from the shoulder crosses one line (~68 deg below horizontal for Twigs, ~63 for Wheels),
  and its hanging-arm code bends the elbow the other way; a reach that starts from a hanging arm, or swings past that
  line with the arm bent, snapped the elbow 40-110 px in one frame (not caught by storycheck: found with a
  frame-to-frame elbow test). This episode handles it in its own file (shared code untouched): both arms always aim
  through the reach (`rest_arms`, a resting hand aimed like the hanging one), and near the line the hand is eased out
  to a straight arm (`unflip`), so the side change happens with the elbow on the arm's line; Twigs' sawing poses keep
  clear of the line. A few quick hand-to-hand passes (Wheels passing his ball) still swing the elbow fast over 2-3
  frames. Worth a shared fix in `two_bone` (keep the previous side unless the arm is nearly straight) by the main FK
  session.
- **Short walking bursts only** (owner, approving FK0019 2026-11-06; checked here before the review, Local Operations):
  no Twigs or Digs walk is on screen longer than ~4 s (longest 3.7 s). On the two long trips (treehouse -> workshop,
  workshop -> the trees) the camera rides ahead with Wheels (rolling, with the tray the second time), Hans and Glo;
  Springs, Twigs and Digs set off once it has left them (`LAG`, all three so nobody passes anybody) and are seen only
  walking the last steps into the workshop / bench frame, then the camera pans back to the work. Digs walks into a frame
  held on the mound and out while the camera looks at the tunnel's far side; Twigs walks out of the lantern shot.
- **Hans has 8 tentacles, never more** (owner 2026-11-06): six legs down and two working tentacles everywhere, except
  the peg forest (four at once): there his two left legs (nearest the panel) lift off the ground and become the 3rd and
  4th arms, blended smoothly from leg to reaching arm (`hans_pre`, drawn behind his body like his legs; the Monster's own
  legs are hidden for that beat only), and he stands and carries on the other four. storycheck `hans_tentacles` 0.
- **Checks** (`experiments/keepers_flat/ep7.py --check`): storycheck every frame at 30 fps plus foot slips, hands
  that fall short (`reach_miss`), Keepers overlapping while moving (`walk_through`, front lane excepted), the camera's
  screen speed (`cam_fast`, 250 px/s), `promise_line`. Real collisions from the physics (bounces, pats, marbles off
  pegs, cubes landing in the basket) are passed to the jump rule as impacts and counted separately.
