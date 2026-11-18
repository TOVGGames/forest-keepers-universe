# Forest Keepers engine (`FK`)

The six tree monsters - **Wheels, Hans, Twigs, Springs, Glo and Digs** - as their own series and engine.
Owner decision (2026-10-27): the Keepers series needed its own rules (lighthearted all-ages music, an end
card asking for ideas, the characters' tools), so from episode 4 it is an engine of its own with its own render
IDs (`FK####_<name>`) and its own line in the analytics (engine = ID prefix). Episodes 1-3 were made by the
Foundry engine and keep their FE IDs:

| Ep | ID | What happens |
|---|---|---|
| 1 | FE0009_monsters | The Monster Factory: trees in, monsters out |
| 2 | FE0012_monsters | Six Keepers are built, then replant the forest, bridge, treehouse |
| 3 | FE0014_halloween | Back to the factory for mystery parts: Halloween decorations for the treehouse (Toby's idea) |
| 4 | FK0001_animal_houses | Water wheel + forest workshop make homes for the forest animals (`forest_keepers_animal_houses.md`) |
| 5 | FK0002_first_snow | The first snow: three sleds built in a snowy workshop, a sled race down the hill (`forest_keepers_first_snow.md`) |
| 6 | FK0003_marble_run | Six wooden marbles made, a treetop marble run built between two big trees, a marble race (`forest_keepers_marble_run.md`) |
| 7 | FK0004_raft_race | Six log rafts with leaf sails built on the bank, raced down the brook over two little falls (`forest_keepers_raft_race.md`) |
| 8 | FK0005_harvest_feast | Thanksgiving: the water wheel turns an acorn mill, a long table and a clay oven are built, bread and acorn pies baked, a feast with the forest animals (`forest_keepers_harvest_feast.md`) |
| 9 | FK0006_tune_up | The Big Tune-Up: back to the factory, orbs out, Hans and Twigs get friendlier faces, everyone sanded and polished; the new look from here on (`forest_keepers_tune_up.md`) |

| 10 | FK0007_bug_hunt | Bug Hunt: six real forest bugs found under logs, rocks and bark, each in Glo's big lens and the Keeper Field Guide (`forest_keepers_bug_hunt.md`) |
| 11 | FK0008_night_animals | Who's Awake Tonight?: six night animals, the first narrated episode (grandmother narrator) (`forest_keepers_night_animals.md`) |

Owner ideas queued for later episodes (Toby's ideas still go first):
- **Animals of the forest** (owner, same day): the same idea with the forest animals, as later episodes.
- **Try a narrator in a couple of episodes**, probably the animal ones (owner, 2026-11-01, thinking of how Puffin Rock
  has a narrator): an elderly grandmother voice, a gentle female sage, who now and then gives hints of what the
  Keepers are up to. The Keepers keep their own cute noises. Through the narration pipeline (`engine/narration.py`,
  ElevenLabs); pick the voice by sending the owner a few short samples first; never the biology voice (Lindsay);
  narrated uploads: Altered content **No** (owner 2026-11-03, PRODUCTION.md), AI-voice credit line in the description. A/B against the caption-only episodes.

All of them are in the YouTube playlist **Monster Factory**.

## Standing rules (owner, every Keepers video)

- **Always "Forest Keepers", never "Forest Monsters"** (owner, 2026-11-02: "we really need that name recognition to
  kick in at Forest Keepers"). Every title, Short, description, thumbnail text and end card says "Forest Keepers"
  (e.g. "The Forest Keepers Build..."); descriptions open "Episode N of the Forest Keepers". "Monsters" alone is
  fine inside a sentence, never as the show's name.

- **Its own channel** (owner, 2026-11-01, via operations): the cartoons (Forest Keepers, the Tiny Tappers, future
  cartoons) move to a new YouTube channel; Dissociate State keeps the satisfying / sleep videos. Episodes 7-10 were
  set to Private there and get re-uploaded on the new channel in the same weekly order. All ages, **not made for
  kids** (comments stay on for the next-episode ideas): no "for kids" / "kids" wording in tags, and no end card or
  description calls Dissociate State the home channel.

- **Quality over speed**: things look good and realistic; take longer if needed (2026-10-26).
- **Not every Keeper in every episode** (owner, 2026-11-14, with Toby, for every episode not out yet): more Keepers
  are coming, so an episode shows only the Keepers its story needs. The others can stay back at the treehouse or the
  night-shift factory, or not appear at all. Approved and filed episodes stay as they are. The end sign shows the
  episode's own cast.
- **Two new characters in design** (owner, 2026-11-14). Neither is built until the owner and Toby approve a design.
  Design notes: `forest_keepers_new_cast.md`.
  - **Blossom**, the new Keeper: pink cherry wood, feminine. A flower on her head opens and closes with her
    feelings ("wears her heart on her sleeve", so everyone can see how she feels). Her job is decorating and the finishing touches.
  - **Melody**, the new foreman of the night-shift factory: a rosewood music box with a crank. She rebuilds the
    factory from hard steel and molten metal into a soft arts-and-crafts workshop in the storybook look. On every
    factory visit from then on, she's in charge: she set up the new things, changes things around and runs the
    machines. Owner: the steel and molten-metal feel belongs to the older bike/robot videos.
- **Better animation and realistic physics, from episode 14 on** (owner, approving FK0011 2026-11-03: "I don't care
  how much longer it takes. The quality needs to go up. The physics needs to be more realistic and we want everything
  super cute"):
  - **Hans walks on his legs** and is a little less floaty: his tentacle-legs carry him in steps planted on the ground,
    not a glide.
  - **Hans works with several tentacles at once** (two, three or four together) as his thing: holding, passing,
    steadying while another tentacle does the work.
  - **Digs digs like a real digger** (a dog or a mole): front paws scoop and throw the soil back between the legs in
    quick strokes, and the soil piles up behind; not just shaking his hands.
  - **Cutting and putting things together look physically right**: the tool really meets the material, chips and
    shavings fly from the contact point, pieces have weight, and parts are lined up, pushed in and seated.
  - Every scene still very cute.
- **No lazy animation: storycheck 0** (owner, turning down FK0012 2026-11-04: "this is the kind of lazy animation
  that I'm not going to accept"). Every storybook episode runs `families/keepers/storycheck.py` every frame and renders
  only with every count at 0:
  - nothing changes size, snaps or warps (one id per thing for its whole life, through every hand that holds it);
  - limbs keep their length (tentacles at most 2x, aim 1.6x);
  - every helping move has a visible reason (the obstacle really is in the way);
  - far things are painted behind near ones, and animals keep real size ratios (softened);
  - the action isn't hidden behind the Keepers;
  - (owner, FK0015 review 2026-11-05) nothing moves with nothing moving it: a prop is in a paw, a mouth or a hand
    the whole time it travels, or falls / rolls by itself (`unheld_motion`; "the grass just warps into his hands from
    nowhere");
  - a side-view animal never turns round by squashing thin in view (`paper_thin`; "when it turns around it is
    obviously paper thin"): it turns out of sight (the beaver ducks under the water), or quickly in mid-hop;
  - no crab walking (`crab_walk`);
  - an animal going into or out of water climbs out or slides in smoothly (`water_snap`: the `wet` share below the
    water line changes at most 1.5 per second; owner, FK0016 approval: the beaver "comes up halfway out of the water
    and then just warps clear onto the land");
  - the narrator never announces the payoff as "the promise" (`promise_line`, `storycheck.script_check` over every
    narration line; owner, SX0023 review 2026-11-05, `docs/PRODUCTION.md`: no "and now the thing we promised" or
    "here's what we waited for"; the payoff simply arrives, e.g. "And look... the very first snowflakes").
- **Walking: turn to walk, a real pace** (owner, FK0015 review 2026-11-05, every episode from ep 13 on: "they need to
  be able to turn laterally to walk... The walk is too slow as well as the weird crab walking"). A Keeper setting off
  turns its face round its head towards where it goes (`monster.Turned`, a three-quarter view, `flat_motion.heading`),
  its hips come in so its legs pass each other like a walk seen from the side (Twigs' bird knees swing round to point
  back), walks at an even pace (`flat_motion.walk_path`: ~100 px/s at K 0.72 between stops, ~80-85 on errands,
  speeding up and slowing over ~1 s), its body bobbing a little as its feet spread (`stance_drop`), and turns back to
  us as it stops. Talking to us on a walk it looks round at us, legs still walking. Errands overlap like a person's:
  the arm starts reaching as it arrives, it sets off again while the arm comes down.
- **Hans has 8 tentacles in total, never more (owner, 2026-11-06, for future builds; no redos):** "If his legs are 6, he can only use 2. If he wants to use a 3rd or a 4th, some of his leg ones need to pull up and get used. He can't just have 9, 10, 11 tentacles like that. 8 is the max." His arms come out of his legs: 6 legs down means 2 arms. A 3rd or 4th arm means a leg visibly lifts off the ground and becomes that arm, so fewer legs support him while it's up. Count his tentacles in every frame (legs plus arms = 8, never more). A storycheck rule `hans_tentacles` should fail on any frame above 8; the main FK session owns that rule.
- **Short walking bursts only (owner, approving FK0019 2026-11-06):** "The way twigs and digs walk is still just a little creepy... If they need to do a little walking, that's fine. But if they ever need to do more walking than that, you should change the angle or the crop or the zoom or something to where you're not just sitting there watching them walk... So little short bursts is okay... Think of some other way to edit it the production so that there's not long periods of walking". So keep each walk to a short burst, a few seconds. A longer journey gets a cut to a new angle, a crop or zoom, a cutaway to scenery or an animal, or the Keepers ride, hop, are carried or arrive. Never hold a long shot of Twigs or Digs walking. This loosens the older no-cuts pacing note for walking only. Nobody may still teleport: a cut has to keep everyone's place consistent.
- **Natural walks, from ep 14 on** (owner, approving FK0016 2026-11-05; "now that we have enough quantity to take some
  more time between productions, we really need to step up the quality"):
  - Digs' and Springs' walks are the models ("great").
  - Arms hang and swing naturally against the legs for every Keeper, never held out to the sides ("nobody walks with
    their arms out like they're pretending they're an airplane").
  - Twigs (the worst walker in FK0016): knees bend the way a walker's do and he never looks like he's walking
    backwards. If his bird-knee reads backwards, give him a forward-bending walk.
  - Hans keeps his colour-changing flaps ("great"), but walks with a natural, staggered six-leg gait, not a
    left-right march ("left, right, left, right... but with 6 feet instead of 2").
  - Built 2026-11-06, opt-in so older episodes stay as rendered:
    - `Monster.arm_swing` with `flat_motion.arm_swing(gait, t)` (walkers) and `roll_swing` (Wheels): arms hang at
      their own length and swing against the legs, settling as the Keeper stops.
    - `Monster.knee_fwd` (Twigs).
    - `flat_motion.WaveGait` (Hans): one tip at a time in a loose ripple, at least 4 down.
    - Test: `experiments/keepers_flat/walk14_test.py --check`; all rules at 0, no foot slips.
- **Story shape** (owner, same note): the educational episodes are "really good" and wholesome, and stories with a
  gentle conflict that builds to a climax and gets resolved are welcome too, "as long as it never gets too tense".
- **Emote bubbles** over a Keeper are big enough to read on a phone (radius 50 px at 1080p; owner: 30 was "too
  small").
- **Let the last shot breathe**: 3-5 s of quiet after the narrator's goodnight before the end sign (owner, FK0015).
  What went wrong in FK0012, item by item: `forest_keepers_fk0012_audit.md`.
- **Storybook style, from episode 14 on** (owner, 2026-11-03, after turning down a 3D look test; look test for his
  OK first, `docs/engines/forest_keepers_storybook/`; that test was NOT approved 2026-11-04: the characters looked like baby versions, the eyes were better before, Digs needs legs and mole claws, Glo his short tentacles, bigger orbs, a new treehouse; the backgrounds' textures were right. Next: he picks from 5 illustration styles of the Keepers' real anatomy, `docs/engines/forest_keepers_styles/`, drawn by `families/keepers/illustrate.py`); he picked 1-2 and spelled out a **flat picture-book look** 2026-11-04: flat 2D vector shapes, oversized heads and eyes, no outlines, one soft darker shade per colour, paper grain over everything, warm muted palette (dusty pink, slate blue, ochre, olive, orange), soft simple backgrounds with gentle gradients and rounded hills. Built as `illustrate.py` style 6 + `families/keepers/flat.py`; look test `docs/engines/forest_keepers_styles/flat/`: "looking a lot better", lash tick scrapped, 2026-11-04; next a 10 s animation sample, FK0013_flat_sample, `experiments/keepers_storybook/flat_sample.py`, motion in `families/keepers/flat_motion.py`: Hans' tripod gait on fixed-length planted tentacles, Digs' mole stroke, soil that flies from the paw onto growing heaps). His words: "Create illustrations using soft, rounded shapes and
  geometric forms to establish a simplified character anatomy. Design characters with large, expressive eyes and
  minimal facial details to maintain a friendly, approachable appearance. Utilize a rich, warm color palette that
  feels vibrant yet naturalistic, avoiding stark contrasts. For the background, build layered compositions with
  distinct textures to create depth and resemble a printed storybook illustration. Focus on maintaining clean, soft
  lines to enhance the overall calming and peaceful visual quality. Design the animation within a two dimensional
  planar space, utilizing layered background elements to create depth. Ensure all motion is rendered smoothly,
  focusing on gentle, fluid, and continuous transitions for characters and the environment to maintain a calming
  sense of movement." In practice:
  - **Characters**: soft rounded geometric shapes, simplified anatomy; big expressive eyes; minimal face (a small
    smile, soft blush; no teeth, no hard detail lines). Each Keeper keeps what makes it itself (colour, silhouette,
    Wheels' wheels, Hans' tentacles, Glo's dome and lantern, Twigs' antlers, Digs' hat and snout, Springs' springs,
    Sprout's cap and seedling).
  - **Colour**: rich, warm, naturalistic; no stark contrast (no black outlines or pure black/white; darks are deep
    warm hues, lights are cream).
  - **Lines**: clean and soft: outlines a darker shade of the fill, thin and smooth.
  - **Backgrounds**: layered planes (sky, far hills, far trees, mid trees, ground, foreground) each with its own
    printed texture (paper grain, painterly wash, stipple), so it reads like a printed picture book.
  - **2D planar**: depth from the layers (and gentle parallax), not 3D. Not 3D: the Blender test
    (`experiments/keepers3d/`) was not approved.
  - **Motion**: smooth, gentle, fluid and continuous (eased starts and stops, no snaps), for characters and scenery.
- **Lighthearted, all ages**: never the dark Foundry sound. The Forest Keepers theme (`families/keepers/music.py`)
  plays from the first second to the last on a music box (C4-E5, warm), with a soft bouncy bass and a warm pad
  (`synth.keepers_song_bed`) and faint crickets. Every SFX stays soft. Pitched notes in MIDI 36-96.
- **End card on every video**: the last ~8 s are a wooden sign hanging from a branch, "WHAT SHOULD THEY BUILD
  NEXT? / Comment your idea below! / We'll pick one for the next episode", with the episode's Keepers lined up under it (not necessarily all of them, owner 2026-11-14)
  and their names showing (`end_sign.py`). The engine appends it automatically (`end_sign: false` in a params file
  turns it off). Then pick a comment idea for the next episode.
- **Hans works with his own tentacles** and they look like his tentacles: `Monster.work_tentacle` /
  `reach_tentacle` (owner after FE0014: "however you did the tentacles is how we're going to do them from now on").
- **Glo's tendrils only come from under his dome**, where they hang (owner after FK0003: a long tendril floating out
  of the air above his head "has gotta go"). Short tendrils from there are fine for small jobs; for colouring or
  lighting things Glo uses his light: the lantern flares up and the thing changes with sparkles (`MarblesAct.magic`).
- **Twigs does the cutting.** Episodes 4-11: a little circular saw on each wrist (`Monster.saws`, `saw_center()`
  tells the scene where each blade is, `punch` / `punch_l` lift the right / left arm). **From the next factory-trip
  episode on: hands, with blades that slide out** (owner, 2026-11-03: "I want twigs to have hands and can also have
  retractable blades"). `Monster.hands = True` (instead of `saws`): three fingers and a thumb (`grip` 0 open .. 1
  holding), a steel sheath along the outside of each forearm, and a pruning blade that slides out of it past the hand
  with `blades` 0..1 (fine teeth, rounded end, bright silver); `blade_tip()` tells the scene where it is. Blades only
  come out for a cut and go back in after; the rest of the time he uses his hands. The change is made at the factory
  like the Tune-Up (orb out first, nothing changes while he's awake). Stills: `forest_keepers_seventh/2_twigs_new_hands.png`.
  **No teeth from then on** (owner, FK0009 review 2026-11-03: "he can keep the same mouth, but no teeth"): with
  `hands` his smile is drawn without teeth.
- **Sprout has two normal hands** (owner, FK0009 review 2026-11-03: no watering-can hand). To water it picks up a
  little watering can (`Monster.can`, it must be there to pick up: nothing appears in a hand), or Glo / Hans waters.
- **No monster goes back through the factory to be fixed**; fixes are made in the drawing code.
- **Things line up**: evenly spaced, square, level. Show a measuring beat (spirit level, string line) and check
  spacing in code (stats like `posts_even`, `houses_even_gaps`).
- **Nothing violent**, cute and calm. Animals are friends.
- **Nobody walks through a wall** (owner after FK0006, approved with it: "when they're walking into the night shift
  building, they still walk through the wall"; the FE0014 note "hidden only by the far jamb" was not enough and it
  came back). The wall a door is in stands behind the walkway: outside, a Keeper walks in front of it. At the door
  it walks straight in, away from the camera (smaller, its feet climbing the tunnel floor, darker) and fades into
  the dark, drawn only inside the opening, behind the frame; coming out is the same backwards
  (`families/keepers/doorway.py`, `Hill(..., walk_in=True)`). Doors are wide enough for Hans' tentacles
  (`DOOR_W` 460 at scale 0.55). Nothing solid is drawn in front of the walkway where a Keeper walks: an act lists
  whatever it does draw in front in `walls(t)` and the engine counts every Keeper overlapping one (`wall_clips`,
  WARNING; must be 0). Look at a still of every doorway (in and out) before rendering.
- **Nobody warps** (owner after FK0001: Hans kept jumping left and right, in one place in one frame and several feet
  over in the next with no movement between; "that kind of warping stuff shouldn't happen because it's not
  realistic"). Every
  Keeper on screen walks, rolls, hops or floats from one spot to the next. When a character's spot depends on which
  job is running, write its moves as one continuous path (e.g. `path()` keys from job to job), never a different
  fixed x per time window with a default spot in between. The engine checks every frame (`Scene._check_jumps` in
  `families/keepers/scene.py`): a velocity change of more than 1200 px/s in one frame (~20 px) is a jump, a ground
  move over 1600 px/s for a quarter second is zipping. Both print a WARNING and are logged as `teleports` /
  `fast_moves` in the stats. Run the scene through (sim / audio-only pass) before rendering and get both to 0.
  FK0001 shipped with 75 (the owner saw Hans's, at 5:39); it is not to be fixed, only not repeated.
- **Nothing else warps either** (owner after FK0005's re-render: the bread jumped to the table and back into Digs'
  hands, plates popped from under the table log). A carried thing is wherever its carrier's hand / head / shovel is,
  and is drawn over whatever it is set down on. Every act lists what it moves in `props(t)` ({name: (x, y)}); the
  engine gives them the same check (`prop_jumps`, WARNING). Get it to 0 too.
- **Slow on purpose, like Mr. Rogers** (owner after FK0005's re-render: "I could do random jump cuts every 3 seconds
  if I wanted to give them worse ADHD"): no cuts inside an act (a dip to black is a jump cut; `act_cuts` WARNING);
  slow pans that follow someone walking instead, at most 250 screen px/s (`cam_fast` WARNING); one thing at a time,
  told in order (if two jobs happen in two places, do them one after the other, not cutting between them); every
  step gets time; the act begins with a calm moment while the name tags show, before anything happens.
- **The working parts stay in view**: what turns, cuts or grinds is never hidden behind a part drawn in front of it
  (FK0005: the pulley and a gear covered the millstones). Keepers let go of a machine before it runs.
- **The right layer in motion, not just on arrival** (owner after FK0005, left as is): a part that ends up behind
  something is drawn behind it the whole way there (FK0005: the wooden gear discs were carried in front of the
  millstones and only went behind them when they landed). Pick the draw order by where a thing is going (its depth),
  not by whether it has landed; clip it by whatever it passes behind. Scrub every "part travels into place" moment
  before rendering.
- **On-screen text holds still** (owner + Toby after FK0007: the "BUGS FOUND" count and the name cards jittered
  the whole video). Captions, counters and cards are drawn straight onto the frame in screen units (the act's
  `screen(cv, t)`, called by the scene after the act), never in the world and mapped back through the camera; they
  fade, they don't move. Check: render consecutive frames with the grain off and compare the text area (0-1 change).
- **Text in the world holds still too** (owner after FK0007, approved with it): the field guide's page text still
  shimmered a little while the camera drifted. Text that sits in the scene (book pages, signs) is either read while
  the camera holds perfectly still, or drawn once and moved as a picture, never re-typeset every frame at a slightly
  different size.
- **What's in the book stays in the book** (owner after FK0008, approved with it: the flying squirrel's tail stuck out
  past the edge of its page; "your checks should have caught that"). Every picture on a page, in a checklist frame
  or on a name card is fitted to that box (`book.fit`), drawn clipped to it (`book.clipped`), and measured before any
  render (`book.check_art` over the act's `book_art()`: stat `page_spills`, WARNING; must be 0).
- **A page turn shows nothing new until the page lands** (owner after FK0007, approved with it): the next bug popped
  onto the left page before the turning page had come down. The new left page is printed on the back of the turning
  page and comes into view with it; the left side keeps the old page until the turn is finished.
- **Things roll the way they are pushed or pulled**: rolling right turns a log clockwise (FK0007 had it backwards).
- **A close-up shows the whole animal**, head to tail, the whole time it is on screen (FK0007: the millipede's head
  was outside the lens).
- **Everything a Keeper does is in step with what it moves**: a tentacle, hand or shovel is at the thing while it
  moves, not before or after (FK0005: Hans' tentacle followed the clay 2-3 s late).
- **The new look, from episode 9 on** (owner approved 2026-10-31, `forest_keepers_tune_up.md`): set
  `Monster.newlook = True` for every Keeper. No pinned badge; the orb flashes the episode's job badge now and then
  (`flash`, `job` = keeper / loaf / snow); Hans has no beard and smiles, Twigs has a softer eye, a brow and a
  rounded-tooth grin; without its orb a Keeper is pale grey and asleep. Many episodes can open with the orbs
  dropping in at the factory (owner).
- **The treehouse door is centred between the two round windows** (`House.door_x` in
  `families/foundry/keepers/halloween.py`), owner after FK0001. Episodes 2-4 had it at the right, half over the
  right-hand window.
- Physics is real: jumps are ballistic with the scene's g (`Jump`, `hops`), hanging things are damped pendulums.
- Names float over each Keeper at the start of the first act and on the end card.
- **The Keepers talk** (owner, 2026-10-27, from episode 5): their little cute noises come often, and they are
  talking to the audience. `families/keepers/chatter.py`: every voice turns the Keeper's eyes to the camera, gives a
  little bounce, moves its mouth (Glo's lantern flickers, Hans' beard wiggles) and pops a small speech bubble with a
  picture (never words). Acts ask for voices at their story beats with `act.chat(t, kind, mood)` (moods: ooh, yay,
  hm, q, mm, hehe, brr, uhoh, wee, huff, hey, aww, idea) and say which moods fit with `aside_moods(t)`; quiet
  stretches get asides automatically (`chatter: gap:` in the params). Episode 5 has ~130 voices in 5:34. Keep
  them soft (owner hears bright 1-5 kHz as harsh): voices are low-passed, the mix is checked per band.

## How the code is laid out

- `families/keepers/scene.py` - the engine's scene: the Foundry Keepers scene (`families/foundry/keepers/scene.py`)
  plus this engine's acts, the theme song, the end sign and Twigs' saws. `families/foundry/keepers/` keeps the
  shared pieces (acts base `KeeperAct`, the treehouse `House`, night sky, ground, animals, `Jump`, `path`, `hops`)
  and the six monsters live in `families/foundry/products/monster.py`.
- `families/keepers/<episode>.py` - one module per episode (its acts); `props.py` - things built and used.
- `families/keepers/params/<episode>.yaml` - `family: keepers`, `name:` = the episode (render ID suffix).
- An act can continue the previous one in the same world with no fade (`joins_prev = True`).

Render (owner's PC, ~1 h for 7 min at 1080p60):

    .venv\Scripts\python.exe -m engine.render families\keepers\params\<episode>.yaml

## Continuity advisor (required)

The owner turned down FK0021 The Harvest Feast (2026-11-07) for misses that every code check passed, and called it
"gross negligence". Since then Local Operations queues an FK review ask only when it comes with an advisor report
showing 0 must-fix. Every Forest Keepers episode needs all three steps below before its review ask. The full write-up
is `docs/engines/forest_keepers_continuity.md`.

1. **The cause-and-effect check, on the plan, before the render.** `families/keepers/causecheck.py` runs inside
   the episode's `--check`, next to storycheck, and every count must be 0:
   - `effect_off_tool`: a cut or mark isn't where the tool touches;
   - `dump_in_hole`: soil or offcuts dropped on another job's spot;
   - `action_hidden`: someone not doing the job covers what the viewer must see;
   - `see_through`: something drawn over a thing in front of it;
   - `form_snap` / `form_no_cause`: a shape changes all at once, or with nothing working on it;
   - `through_wall`: something is hidden by a wall instead of going through its opening;
   - `too_small`: a key moment is too small to see;
   - `shuffle_steps`: little steps where an arm would do.

   The episode declares each beat's action: what must be seen, where the tool touches, and who is doing it.
   `experiments/keepers_flat/ep9.py` (`cause_frame`) is the example, and `causecheck_selftest.py` shows the old
   FK0021 mistakes being caught.
2. **Fresh agents on the beat strips, before the render.** Draw strips of every beat straight from the plan with
   `experiments/keepers_flat/strips.py`. Give them to fresh general-purpose agents (no fork, no build context) with
   the owner's checklist (`families/keepers/advisor.py`, `CHECKLIST`). They draw any moment closer with
   `strips.py`.
3. **The advisor on the rendered file.** Run
   `.venv\Scripts\python.exe families\keepers\advisor.py prep "<video.mp4>" --id <ID> --script <lines.json>`.
   - It makes contact sheets every 0.5 s and 0.1 s strips round every sharp movement.
   - It runs speech-to-text on the LOCAL faster-whisper (in the shared .venv; never ElevenLabs Scribe) and compares
     it word by word with the script. A word heard wrong twice is must-fix.
   - It writes one prompt per ~75 s. Start one fresh agent per prompt, all in one message, then run
     `advisor.py report <ID>`. That writes `video_log/advisor/<ID>_rN.md`: each finding timestamped, must-fix or
     should-fix. It exits with 1 while anything is must-fix.

   `advisor.py stt <video or .wav> --script <lines.json>` checks the narration alone. Write the script with
   `advisor.write_script(plan.narration(), path)`.

   Fix every must-fix, re-render only the segments it touches, and run it again until it shows 0 must-fix. Put the
   report's path and counts in the HANDOFF entry and in the review ask.

Where a word is voiced wrong as written, respell it for the voice only and keep the written word everywhere else
(FK0021: `SPOKEN = {"Flour!": "Flower!"}` in `harvest_flat.py`).
