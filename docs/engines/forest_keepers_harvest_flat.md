# Forest Keepers ep 9: The Harvest Feast, flat remake (of FK0005)

This remakes FK0005 in the flat picture-book look, as episode 9 (remake session 3, `forest_keepers_remake_briefs.md`).

The story is the old one (`forest_keepers_harvest_feast.md`):
- an acorn bonks Digs' hat and gives Glo the idea of bread;
- the Keepers build a mill at the old water wheel and grind the acorns into flour;
- home in the village they build a stone-and-clay oven and a long table;
- they bake bread and share it with the forest animals.

Like the other remakes, it has:
- only the six Keepers (no Sprout), with the new faces and the ep 14 walks;
- narration by the grandmother voice (`narrator.py`);
- its own music variant, `harvestfeast`.

The code:
- `families/keepers/harvest_flat.py`: the plan, the props, the Keepers, the drawing and the soundtrack;
- `harvest_flat_world.py`: the brook, the wheel, the mill parts, the oven, the table, the houses and the light;
- `experiments/keepers_flat/ep9.py`: `--times`, `--stills`, `--check` and `--render`.

## How things move

Every carried thing is a **Prop**: a list of moves (who holds it, where it goes, how it turns) written down once.
- Hans' working tentacles are computed from the props he holds, so a tentacle tip is always exactly on the thing it
  carries. This fixes the FK0005 note "the tentacle followed each piece of clay 2-3 s after it had moved".
- Glo's tendrils hold things from under his dome: the acorn, the basket, the bread peel. His light flare only lights
  the oven's fire and the lanterns (owner rules: Glo's light magic, no floating arm).

## The owner's FK0005 notes, and what this build does

- **Calm start.** The name tags show over a slow drift first. The squirrel's acorn falls only after that.
- **The full mill build is on screen** (it used to be "just there"):
  - Digs digs two post holes and pats the earth back round each post.
  - Hans stands the posts and lays the top beam and the low beam that holds the millstones.
  - Twigs trims two roof boards and two hopper boards at the rack's stop block, and Hans lays them.
  - Hans lifts two round stones out of the shallows (no `water_snap`), and Digs taps their eyes and six grooves.
  - Twigs makes the gears, as below.
- **The gears.** Each one starts as a square board. Hans turns it at Twigs' blade while Twigs cuts its four corners
  off, then eight teeth. This is all done at the blade's reach: his arm can't reach a thick log.
- **The stones turn IN.** The water pushes the wheel's bottom paddles downstream, so the wheel turns anticlockwise. A
  crossed belt (the X is visible, with stitches running along it) turns the left stone clockwise. The meshing gears
  behind the stones turn the right stone anticlockwise. Both move down at the nip.
- **Nothing hides the stones.** The gears are behind the stones, with only their teeth showing round the rims. The
  pulley is small, on the left stone's hub. Hans lets go of everything once it's fitted.
- **The wheel is held** by a rope pegged to a post. Springs jumps over Digs to the post and pulls the peg, and the
  wheel starts.
- **The first acorn** is the one from the hook. Glo has carried it all along, drops it in, and a puff of flour
  appears.
- **Milling.** Springs bounces on the oak's low branch and twelve acorns drop into the basket. Glo floats it to the
  hopper and tips it, and the acorns go through the stones one at a time. The sack fills with each acorn, and Hans
  ties it.
- **The oven is stone and clay**, never wood-looking:
  - Hans lays three base stones, a hearth slab, two jambs and a lintel round the door.
  - Digs digs clay and Springs bounces it soft.
  - Hans lays three clay coils. His tentacle tip is the end of each coil as it goes round, and the lump in it shrinks.
    A second tentacle smooths just behind.
  - He smooths the coils into one dome with finger marks, soot comes once it burns, and the fire shows in the door.
- **The table.**
  - Twigs trims all six planks at once at the stop block.
  - Hans lays them across the two fallen logs from above, one at a time. Nothing slides under the front log.
  - The table and the rack are in front of the path, so the Keepers stand behind the table.
- **The bread.**
  - Flour from the sack and water from the jug go onto a board on the rack. Hans kneads it, Twigs cuts it in four,
    and Hans rounds the loaves.
  - The loaves ride on the peel. They brown only while inside the oven, and they're on the peel or in a tentacle the
    whole way (they used to "warp" to the table).
- **No cuts inside an act, and slow pans.** There is one soft dip to black between the mill and the village.
- **The feast.**
  - The camera drifts to the animals' houses as the doors open and comes back with them.
  - The bunnies hop up onto the table, the hedgehog sits on a stump, and the birds fly down.
  - Hans breaks a loaf and hands round the pieces, under the lanterns and the fireflies.

## Owner note from the FK0019 approval (2026-11-06): no long walks

Walking stays in short bursts:
- The walk home along the brook is an act break: a few steps, a dip into the evening, and the last few steps into the
  village.
- Glo floats the loaded peel to the oven and back, so Hans never makes the long trip.
- Digs and Springs move to the table in two short bursts.

## Owner rule (2026-11-06): Hans has 8 tentacles, never more

- His six legs stand on the ground and two arms are free.
- A 3rd or 4th arm is a leg lifting off the ground. The outermost right legs go first (`hans_lifted`). The arm's tip
  starts at that leg's foot as it reaches out, and goes back down to a foot when it's done, so the leg visibly
  becomes the arm and back.
- `ep9.py --check` counts legs drawn plus arms drawn in every frame (`hans_tentacles`, must be 0 frames above 8). The
  main FK session's shared rule replaces it when it lands.

## Checks (`ep9.py --check`, all 0 before a render)

The act break is a cut: each act is checked on its own.

Storycheck:
- `thing_jumps`, `size_snaps`/`size_drift`, `pops` (every prop says what it was born from and where it went),
  `unheld_motion`, `paper_thin`, `crab_walk`, `water_snap`, `limb_stretch`, `depth_order`, `scale_mismatch`;
- plus `teleports`, `foot_slips`, `reach_miss`, `walk_through` (2D, so Springs' jumps over Digs count as clear),
  `elbow_snap`, `loose_hold` (a prop held by Hans with no tentacle on it) and `promise_line`.

There are no walls or doors here, so `wall_clips` is 0.

## Owner notes on FK0021 (2026-11-07, changes requested), and what changed

The owner's notes are quoted in `publish/OWNER_QUEUE.md`, Answered. Each one, and the fix:
- **The bonk was too small, and the acorn might have been floating.**
  - The camera comes in 1.5x on the squirrel, Digs and Glo. It's sharp, not a scaled-up bitmap: `zoom_figure.py`
    draws each Keeper at the zoomed size.
  - The squirrel is 1.7x and sits right over Digs, and the acorn is 1.45x. The acorn starts in the squirrel's paws
    (it's the same prop, never a drawn copy).
  - Four little strokes flick out round the hat.
  - Glo floats beside Digs instead of over his hat. The acorn hops off the hat into his tendrils, and two tendril
    tips curl round it while he carries it.
- **Digs' soil.** The holes are 280 px apart and his paw lets go 142 px out, so a full throw landed in the other
  hole. Between the holes the soil is now set down at the end of the stroke as one shared pile, clear of both holes
  (`SideSpoil`). The outer sides throw as before, and the camera comes in 1.3x on the digging.
- **The gears.**
  - The blade is at the blank's right rim, just clear of Twigs' body (his body used to cover the cut).
  - The blank starts as a diamond. Hans turns it anticlockwise so each corner, then each notch, comes to the blade
    in turn (`blank_turn`, checked by `blade_part`).
  - The drawing now has the same 8 notches as the cutting (it used to draw 12, so the notches appeared off the blade
    and round only part of the wheel). Each notch deepens while the blade goes through it.
  - The second gear is set half a tooth on, so the two mesh at the nip.
- **"Flour" said as "floor".** It's re-voiced as "Flower!" (the same sound) and confirmed with speech-to-text.
- **Glo in front of the mill, the acorns showing through him.**
  - Glo tips the basket, then floats off to the gap past Hans and sets it down on the grass. The acorns go through
    the stones only once he's clear.
  - The basket's acorns are drawn in front of Glo only while they're falling from the branch.
- **The dough.**
  - The board is where Twigs stands, so he makes all three cuts with his arm alone.
  - The cuts are at the quarters. The four slices are born exactly as cut, and Hans rolls each one round under his
    tentacle tip (`loaf_morph`).
  - The loaves are a quarter of the dough in size and rise a quarter bigger as they bake. They sit on the board side
    by side, and on the peel two by two.
- **The bread went in through the oven wall.**
  - The door is wider (92 px) and the stones are moved out to frame it.
  - The peel turns to point into the door. The blade and loaves go in through it and are drawn only inside the
    opening.
  - Glo holds the handle from the oven's lower right, clear of its front, and the camera comes in 1.4x.
- **The basket hid the lanterns.** The basket stayed at the mill. Glo hovers beside each lantern, his lamp level
  with it, and his light floats across to it.
- **The animals came out through the walls.**
  - The night pass redrew both houses over everything, walls and all. It now draws only the light in the doors and
    windows.
  - The doors are big enough for each animal. Each comes out of the dark, drawn only inside its doorway, then steps
    down in front of the wall.
  - Each animal has its own lane, so the bunnies pass the hedgehog in front of it.

The new cause-and-effect check (`causecheck.py`, in `ep9.py --check`) is 0 on all of this. Its self-test catches the
old mistakes it was tested on. See `forest_keepers_continuity.md`.

## Rendered (2026-11-07)

`renders/Forest Keepers/FK0021_harvest_feast.mp4`: 10:04, 1080p60, 254 MB. It took 6 workers at Below Normal and
3.5 h, plus a resume.
- The first run stopped at 6:00. A clay coil just begun had fewer than 2 points on its top line, and the seam stroke
  crashed. The strokes now need 2 points; no frame drawn before that changes.
- The 30 fps storycheck after the render is all 0 in both acts.
- Audio: -14.9 LUFS, peak -2.0 dBFS, 0 folded notes. 1-2.5 kHz is 4.9% of the energy and 2.5-5 kHz is 1.3%.
