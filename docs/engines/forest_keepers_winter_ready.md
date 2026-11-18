# Forest Keepers episode 13 (proposed): Getting Ready for Winter (`FK####_winter_ready`, ~7 min, 16:9, narrated)

**FK0012 NOT approved (owner, 2026-11-04): remake in the storybook style with softer colours, after his OK on the look test; every mistake found frame by frame and its fix: `forest_keepers_fk0012_audit.md`; the remake renders only with storycheck 0.** Earlier: **Status: storyboard APPROVED by the owner 2026-11-03 ("Yes, I approve"); animals fact-checked (below); built and rendered as `FK0010_winter_ready`, awaiting the owner's review** (2026-11-03 via Don's Asks: "Episode 12 seems fine"). It comes right
after the factory-trip episode (`forest_keepers_factory_trip.md`), so Sprout is the seventh Keeper here. The edible
Christmas tree follow-up is out (owner: "They're going to eat a Christmas tree. Seems weird"); a new idea went to him
instead: Sprout grows a little fir in a pot, they decorate it with carved ornaments, then plant it in the forest.
Nothing rendered yet.

Same format as Night Animals (FK0008), which the owner liked: the storybook narrator Johanna (slow, sparse), the
Keeper Field Guide, a name card with one short line per animal, a counter, every rule in `forest_keepers.md` (cute
animals first, on-screen text in screen space, everything in the book fitted and clipped to its page with
`page_spills` 0, no walking through walls, music at the normal level ducked only under the narrator, AI-voice line on
upload). The twist: it starts at sunset (warm autumn colours, geese going over) and turns to night by the end, and
each Keeper gives one animal a gentle hand (seven Keepers, so Wheels and Twigs help the beaver together). Nobody
touches or chases the animals.

## The hook

"The days are getting shorter, and the forest is getting ready for winter. How will each of our neighbours get ready?
And at the very end, watch for the very first snowflakes." (Owner's long-form rule: say what's coming early and name
one thing we only see at the end.) No snow in any shot before the goodnight. Counter: READY FOR WINTER n / 6.

## Six animals (`families/keepers/winter_animals.py`, sheet `forest_keepers_winter_ready/1_the_six_animals.png`)

| Keeper | Animal | What we see | Card line (draft, checked before use) |
|---|---|---|---|
| Sprout (gathers acorns into a pile with its little hand) | Eastern chipmunk | sits up, stuffs its cheek pouches, pops down its burrow | It carries seeds home in its stretchy cheek pouches and stores them underground. |
| Twigs (one blade out, trims a fallen branch) and Wheels (hauls the branches over) | Beaver | carries a leafy branch to its lodge and pushes it into the mud | It pushes branches into the mud by its lodge, to eat under the ice all winter. |
| Springs (bounces up to look) | Canada geese | a V of geese flies over, honking | Many geese fly south in a V: each bird rides the air lifted by the one ahead. |
| Digs (tidies the burrow door) | Groundhog | stands up to look round, then curls up asleep | It hibernates all winter in its burrow, its heart beating only a few times a minute. |
| Hans (holds a branch aside) | Black bear | ambles to its den and settles in | It eats and eats all autumn, then sleeps the winter away in a cosy den. |
| Glo (soft light on a feeder) | Black-capped chickadee | fluffs up into a little ball, takes a seed | It stays all winter: it fluffs its feathers into a warm coat and remembers where it hid seeds. |

Ending: night falls, the first snowflakes, "Six neighbours, all ready for winter. Goodnight, forest." End sign "WHAT
SHOULD THEY DO NEXT?", seven Keepers under it.

## Storyboard stills

1. `forest_keepers_winter_ready/1_the_six_animals.png`: the six animals, with their poses (chipmunk with empty and full
   pouches, goose standing and flying, groundhog and bear awake and asleep, chickadee normal and fluffed up).
1b. `forest_keepers_winter_ready/1b_storyboard_hook.png`: the opening at sunset: the seven Keepers set out under the
   first geese, counter at 0 / 6, the narrator's hook written out (storyboard only; spoken in the episode).
2. `forest_keepers_winter_ready/2_storyboard_chipmunk.png`: find 1 at sunset: Sprout has gathered acorns by the
   chipmunk's burrow, geese go over, counter and name card in screen space.
3. `3_storyboard_beaver.png`: Twigs trims a fallen branch with one blade out, Wheels hauls; the beaver tows a branch
   to its lodge.
4. `4_storyboard_groundhog_geese.png`: Digs tidies the groundhog's burrow door while Springs bounces up to watch the
   geese go south.
5. `5_storyboard_bear.png`: dusk turning to night: Hans holds a branch aside and the bear ambles into its den.
6. `6_storyboard_goodnight.png`: night, the first snowflakes: Glo's soft light on the feeder, the chickadee fluffed
   up, "READY FOR WINTER 6 / 6".
Made by `families/keepers/winter_ready_board.py`.

## Fact check (owner 2026-11-03: "I assume that you fact-checked that all those are animals that actually overwinter")

Every animal really does what the episode shows; two card lines were tightened.

- **Eastern chipmunk:** stores nuts and seeds in food chambers of its burrow and spends the winter in torpor, waking
  every few days to weeks to eat from that store (Maine IFW; Biodome Montreal, citing McGill studies). Narration must not
  say it sleeps straight through. Card line OK.
- **Beaver:** stays all winter; in autumn it pushes cut branches into the mud near the lodge and eats them under the
  ice, reached through the water (Vermont Center for Ecostudies; Northern Woodlands; DuPage Forest Preserve). Card OK.
- **Groundhog:** a true hibernator; its heart drops from about 80 to 4-5 beats a minute (Live Science; Daily Herald;
  Missouri Conservation). Card now says "hibernates" instead of "sleeps" (it wakes now and then, as hibernators do).
- **Canada goose:** northern breeding populations migrate south, but many resident flocks now stay all year (Northern
  Woodlands "Canada Geese: Migrant or Resident"); the V saves energy because each bird rides the lift off the wingtip
  of the one ahead (Birds & Blooms; Press Herald). Card now says "Many geese fly south" and "the air lifted".
- **Black bear:** eats almost nonstop in autumn (hyperphagia), then dens for the winter in a hollow log, under roots
  or in a rock crevice, its heart rate and breathing slowing (NPS "Bears in Winter"; North American Bear Center). OK.
- **Black-capped chickadee:** a year-round resident that fluffs its dense feathers, caches seeds in many places and
  remembers them, and drops its body temperature on cold nights (Cornell Lab K-12; Nature Conservancy of Canada;
  Natural Resources Council of Maine). OK.

Sources: maine.gov/ifw/fish-wildlife/wildlife/species-information/mammals/eastern-chipmunk.html,
espacepourlavie.ca/blogue/en/chipmunk-original-rodent, vtecostudies.org/blog/outdoor-radio-winter-world-of-beavers,
northernwoodlands.org/outside_story/article/beavers-winter, dupageforest.org/blog/beavers-prepare-for-winter,
livescience.com/64672-groundhog-day-hibernation.html, northernwoodlands.org/outside_story/article/canada-geese-migrant-resident,
birdsandblooms.com/birding/birding-basics/why-geese-fly-v-formation/, nps.gov/articles/bears-winter.htm,
bear.org/5-stages-of-activity-and-hibernation/, birds.cornell.edu/k12/how-do-song-birds-survive-winter/,
natureconservancy.ca/en/blog/archive/winter-chickadees.html, nrcm.org/nature-of-maine-blog/caching-up-for-winter/.

## As built (`families/keepers/winter_ready.py`, act `winter`, params `families/keepers/params/winter_ready.yaml`)

One narrated walk, sunset to night, no cuts, run 1.2x slower than written (slow on purpose). The animals stay in the
layer behind the path (burrows, the pond and lodge, the den, the feeder); the Keepers walk the path in one fixed
order (Sprout in front ... Glo at the back), so nobody passes anyone: at each place the ones ahead walk on past it and
the helper stops beside it. Wheels pushes his little cart the whole way. Music variant `winterready` (D, 90 bpm,
quiet bars for the narrator). Times in the render (about 5:47 with the end sign):

- 0:01 the hook (narrator), name tags; 0:15 the counter READY FOR WINTER 0 / 6.
- 0:20 Sprout carries three acorns, one at a time, from the old stump to a pile by the chipmunk's burrow; 0:55 the
  chipmunk comes up, stuffs its cheek pouches with them and goes back down: 1 / 6 at 1:09, its card.
- 1:36 Twigs slides out his left blade and trims the dead end off the fallen tree; it drops into Wheels' cart. The
  beaver swims over, lifts it out, goes back under (it turns round under water), swims to its lodge and dives; the
  branch end sticks up out of the water by the lodge: 2 / 6 at 2:11.
- 2:44 Digs sweeps the old leaves out of the groundhog's door; the groundhog comes up and looks round; 2:59-3:15 a V
  of six geese goes over honking while Springs bounces up to watch: 3 / 6 at 3:14; the groundhog goes down to
  sleep: 4 / 6 at 3:29.
- 3:59 dusk: Hans lifts the low branch out of the way with a tentacle, the bear ambles along and into its den, and
  he lets the branch down again: 5 / 6 at 4:20.
- 4:49 night: Glo's light on the feeder; the chickadee hops down from its twig, takes a seed and fluffs up: 6 / 6 at
  5:02. 5:13 the very first snowflakes (none before); 5:17 the finale ("...Goodnight, forest."); 5:35 the end sign
  ("WHAT SHOULD THEY DO NEXT?", the narrator's sign-off).

Checks (whole video): teleports 0, fast moves 0, prop jumps 0, act cuts 0, camera too fast 0 (max pan 222 px/s,
max zoom 0.13/s), wall clips 0, no two Keepers overlapping at any time (own check).

## Remake: episode 13 in the flat picture-book look (started 2026-11-04)

The owner approved the flat look on FK0014 ("Yes, start ep 13"). The remake keeps the approved storyboard above: the same six
animals, sunset to night, the counter, the narrator's lines, the first snowflakes, and the end sign. It is rebuilt on the flat kit:
- `families/keepers/illustrate.py` style 6 and `families/keepers/flat.py` (layers cached by `Valley`, grain fixed to each thing);
- `families/keepers/flat_motion.py` (Hans' tripod gait, Digs' mole stroke, Hans' mood wings).

Every frame goes through `storycheck`, and every count must be 0, with planted feet never sliding. Each of the 22 mistakes in
`forest_keepers_fk0012_audit.md` is fixed as follows:

| Beat | What changes (audit item) |
|---|---|
| Chipmunk | Sprout carries one acorn at a time, always the same size, from the stump to the pile. Each acorn lands, rolls and settles against the others (1-3). The chipmunk comes out with empty paws, walks to the pile, takes each acorn in its paws and tucks it into a cheek. Its pouches fill smoothly, one acorn at a time (4-5). |
| Beaver | Twigs trims a **fresh green willow branch** from a willow at the pond's edge (14). Wheels carts it to the water's edge. The beaver takes that same branch in its teeth, swims it to the lodge and pushes it into the mud, in view, with its end left showing (6). Twigs and Wheels stand to the side, so the beaver is in the open (20). |
| Groundhog + geese | Digs brings an armful of **dry grass** to the groundhog's door, and the groundhog pulls it inside, one bundle at a time (15, 7). Then it goes in and pushes a plug of soil into the doorway behind it (fact: it walls off its chamber). The geese fly high above the treetops, behind every near tree, never in front of one (16). Springs watches from beside the door, not in front of it (22). |
| Bear | Dusk. A low branch really hangs across the den's mouth, in the bear's path (13). Hans walks right up to it and lifts it with two tentacles at once, each within 1.6x its length (11). The bear walks in at its own size and fades into the den's darkness (8). Nobody stands between the camera and the bear (21). |
| Chickadee | Night. The chickadee lands next to a seed on the feeder, takes it and eats it (pecks, swallows), then fluffs up into a warm ball (9). Glo's soft light comes from under his dome. |
| Everywhere | Animals are drawn at their real size ratios, softened to ratio^0.6: bear > groundhog ≈ beaver > chipmunk > chickadee (17). Layers have depth and parallax (18). The sun and sky keep one size on screen (10). Falling leaves are leaf shapes, sized by their layer and rare near the camera (19). Every Keeper walks with planted feet, and its limbs keep their length (12). Wheels' wheels turn exactly as far as he rolls. |

Status: building. The six animals redrawn in the flat look come first (a sheet for the owner), then the world and the walk,
then each beat with its checks, then the full render, a frame-by-frame self-review, thumbnails (with the fresh-agent
expectation test), the HANDOFF entry and the OWNER_QUEUE ask listing what was found and fixed.

Fact checks added 2026-11-04:
- **Beavers:** they push fresh, cut branches (willow and aspen preferred) into the mud near the lodge. The cold mud keeps
  them fresh, and they eat the bark under the ice. Sources: dupageforest.org/blog/beavers-prepare-for-winter,
  nps.gov/gaar/naturescience/beaver-natures-engineer.htm, whistlernaturalists.ca/single-post/a-winter-under-water.
- **Groundhogs:** the hibernation chamber is lined with dead leaves and dry grass, which they gather before winter. They
  then wall off the chamber's entrance with soil. Sources: loudounwildlife.org/2005/01/groundhogs/,
  psu.edu/news/story/do-groundhogs-hibernate-what-know-about-groundhogs-groundhog-day,
  outdoor.wildlifeillinois.org/articles/groundhogs-illinoiss-largest-squirrel/.

### Remake layout and timeline (`families/keepers/winter_flat.py`)

One walk to the right along a path through the valley (world x, ground-layer px). The animals' places sit just behind
the path. The Keepers walk in a fixed order: Sprout in front, then Twigs, Wheels, Digs, Springs, Hans, and Glo at the back,
and nobody passes anyone. At each place the helper stands on the side the animal doesn't use; those ahead walk on past
its route and those behind wait short of it, so nobody stands between the camera and the animal (audit 20-22).

| ~Time | Place (x) | Helper(s) and staging |
|---|---|---|
| 0:00 | meadow, sunset | the seven walk in. The hook: "...And at the very end, watch for the very first snowflakes." Counter 0 / 6. |
| 0:14 | stump 2600, pile 2760, burrow 2850 | Sprout carries three acorns from the stump to the pile, one at a time. The chipmunk comes up, fills its pouches at the pile and goes down. |
| 1:15 | willow 4300, cart 4500, pond 4450-5600, lodge 5300 | Twigs trims a green willow branch into Wheels' cart. The beaver climbs out, takes it and swims it to the lodge. Those ahead wait past 5700. |
| 2:20 | door 7000, dry grass 7350 | Digs brings dry grass in two armfuls, and the groundhog pulls each into its door. The geese pass high above the trees, and Springs watches from 6800. The groundhog goes in and plugs its door. |
| 3:35 | den 9300, low branch from a tree at 9500 | Dusk. The bear comes from the left along the bank. Hans, on the den's far side, lifts the low branch with two tentacles, and the bear goes in. |
| 4:45 | feeder 11000 | Night. Glo lights the feeder from its left. The chickadee lands, eats a seed and fluffs up. |
| 5:40 | feeder | The first snowflakes, the goodnight line, then the end sign, "WHAT SHOULD THEY DO NEXT?". |

The narration is the 15 approved FK0012 lines, all already voiced (cached, 92.6 s in all). The music box is the `winterready` variant.

### Owner's FK0015 review (2026-11-05, via Don's Asks): not approved, seven fixes

Kept as they are: the art style ("perfect"), the sunset, the geese ("greatly improved"). The seven fixes, in the order
he gave them, and what changed:

- **Emote bubbles were too small.** Their radius is now 50 px, up from 30, and they sit higher.
- **Sprout's three acorn trips looked robotic.** He now turns to walk and walks at a brisk pace (85 px/s) with a little bob.
  His arm starts reaching as he arrives, he sets off again while it comes down, and he holds it out as he reaches the pile.
  On the way back his empty arm hangs at his side.
- **Everyone crab-walked sideways, and too slowly.** Each Keeper now turns to face where it is going, then turns back to us
  as it stops. The face turns round the head in a three-quarter view (`monster.Turned`). The hips come in so the legs pass
  each other, and Twigs' knees swing round to point back. The pace is 100 px/s between stops, up from 58 px/s.
  - The walks pick up speed and slow down over about 1 s (`flat_motion.walk_path`), instead of over the whole walk.
  - The episode is now about 5:56.
  - At the start the group stands while the hook is told, then sets off.
- **The beaver went paper thin when it turned.** It now ducks fully under the water, turns round out of sight, and comes up
  facing the lodge. The branch in its teeth stays floating at the surface.
- **Digs' grass warped into his hands.** The grass is now two bunches of eight tufts, a little apart from the groundhog's
  door (`GRASS` 5790).
  - He stands beside a bunch, takes hold of it low down in his left paw, and pulls it up.
  - He carries it held out at his side and sets it down by the door, then steps back.
  - The groundhog leans right out, bites the bunch, and pulls it down its burrow.
  - The grass is always in a paw or a mouth, or lying still, and is always drawn behind Digs.
  - The Keepers ahead of him stand further right (Wheels 6200, Twigs 6430, Sprout 6660) to leave him room.
- **The meadow's tufts and leaves continued into the bear's den.** None are drawn on the rocky bank or in the den's mouth
  any more (`rock_bank_outline`).
- **There was no pause after "Goodnight, forest".** There are now 4 s of quiet before the end sign (`HOLD_END`).

New storycheck rules catch these mistakes in every episode: `unheld_motion`, `paper_thin` and `crab_walk`. They are listed
in `forest_keepers.md` (standing rules).

### FK0016 status (2026-11-05): the fixed version, awaiting the owner's review

Rendered 6:01 at 1080p60 (`renders/Forest Keepers/FK0016_winter_ready.mp4`, 187 MB). Storycheck is 0 over all 10,821 frames
(30 fps) on all 13 rules, including the three new ones. Audio is -14.0 LUFS, LRA 5.2, true peak -1.4 dBFS, with no folded notes.

The frame-by-frame review (2 s contact sheets plus close-ups of each fix) found nothing to change:
- the turned walks at the start and on the way to the ground scene;
- Sprout's trips;
- the beaver's turn, hidden under the water;
- Digs' two grass trips (he grips at the bunch, carries it, and the groundhog bites and pulls it in);
- the den floor, which is clean;
- the bigger bubbles;
- about 5 s of quiet between "Goodnight, forest" and the end sign.

Thumbnails A (bear, 4:30) and B (beaver, 2:03) are the same moments and words as FK0015's, re-shot. HANDOFF: "Forest Keepers episode 13 ... FK0016".

### Remake status (2026-11-05): rendered as FK0015_winter_ready, awaiting the owner's review (superseded: see above)

Rendered 7:08 at 1080p60 (`renders/Forest Keepers/FK0015_winter_ready.mp4`) in one-minute segments, so a render can resume.
Storycheck is 0 over all 12,860 frames (30 fps); audio is -14.1 LUFS, LRA 4.6, with no folded notes. The frame-by-frame review
(2 s contact sheets plus close-ups) found one problem. In Digs' dry-grass armful, the eight upright tufts sat right under his
nose and read as a mouthful of fangs (owner: no teeth). Now he carries it low at his tummy as one soft bunch with the tips
poking up. It bunches as he sweeps it together and loosens as he sets it down. Minutes 3-5 were re-rendered and spliced in at
the segment keyframes; the audio is unchanged. Thumbnails A (bear) and B (beaver) passed the fresh-agent expectation test;
the chipmunk, snow and grass options were dropped. HANDOFF: "Forest Keepers episode 13 ... FK0015".

### Remake build status (2026-11-04)

Done and checked by eye:
- the six animals in the flat look (`docs/engines/forest_keepers_winter_ready_flat/1_the_six_animals.png`);
- planted-foot walking for all seven Keepers (`experiments/keepers_flat/walk_test.py`: foot_slips, wheel_slip and limb_stretch all 0);
- the world, sunset to night (`families/keepers/winter_flat_world.py`);
- the episode core and the opening walk (`families/keepers/winter_flat.py`, CLI `experiments/keepers_flat/ep13.py`);
- the chipmunk beat. Sprout picks three acorns off a young oak's low twig by the old stump, a change from the storyboard's
  stump: at true sizes the chipmunk is taller than the stump, and Sprout's arms can't reach the stump top or the ground. The
  narration's "by the old stump" stays true. He carries them one at a time; they drop, land and roll into a pile. The
  chipmunk comes up empty-pawed, takes each in its paws, tucks it into a cheek (the pouch fills smoothly) and goes back down.

The animals are drawn bigger than real next to the Keepers (owner: fill the frame) but keep their real ratios between
themselves: the chipmunk is about 2/3 of Digs.

Next:
- the beaver, then the groundhog and geese, the bear, the chickadee, the snowflakes and the end sign;
- the counter, name cards and name tags;
- the Keepers' chatter, music, narration mix and SFX;
- full-episode storycheck;
- a parallel render (about 1.5 s per frame on six workers, roughly 90 min);
- a frame-by-frame self-review, thumbnails with the expectation test, the HANDOFF entry, and the OWNER_QUEUE ask listing every
  audit fix.
