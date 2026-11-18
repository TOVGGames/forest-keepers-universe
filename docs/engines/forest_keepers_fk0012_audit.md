# FK0012 "Getting Ready for Winter": frame-by-frame audit (2026-11-04)

The owner turned FK0012 down on 2026-11-04 (Don's Asks, main ca8f6e4): "this is the kind of lazy animation that I'm
not going to accept." It will be remade in the storybook style (`families/keepers/storybook.py`) once he OKs the look
test. Don's Asks told him he doesn't need to rewatch it, so this is the full list, from the frames of
`renders/Forest Keepers/FK0012_winter_ready.mp4` and the code that drew them (`families/keepers/winter_ready.py`).
Times are video times.

Every item marked **check** is caught automatically by `families/keepers/storycheck.py`. Running FK0012's own
geometry through it (`python experiments/keepers_storybook/fk0012_check.py`) flags all of them. A storybook episode
renders only with every storycheck count at 0, and the remake fixes each item as listed.

## 1. Things changing size, snapping or warping into place

| # | When | What happened | Remake | |
|---|------|---------------|--------|---|
| 1 | 0:26, 0:36, 0:45 | When Sprout picks an acorn off the stump, it shrinks to 0.6x in its hand. The acorn that vanishes from the stump is not the one under its hand: it is 22-66 px away, so an acorn jumps into the hand. | One acorn, one size, from the stump to the pile. The hand closes on the acorn it touches. | **check** (size, jump) |
| 2 | 0:31, 0:41, 0:50 | Right before the drop, the acorn grows back to 1.65x (2.7x the area). This is the owner's "3 times bigger in his hand". | Same as 1. | **check** (size) |
| 3 | 0:41, 0:50 | The acorn falls, lands, and then jumps 20 px or 17 px to its spot on the pile. This is the owner's "warp into place". | It lands where it falls, then rolls and settles against the others in the pile. | **check** (jump) |
| 4 | 1:00, 1:02, 1:04 | The chipmunk "eats" from the pile from 60 px away: each acorn just vanishes 90-110 px from its mouth. The seed it holds in its paws never changes, and it was already holding it when it came up out of the burrow. | It reaches the pile, takes each acorn in its paws and tucks it into a cheek. Its paws are empty to begin with. | **check** (pop) |
| 5 | 1:00, 1:02, 1:04 | Its cheek pouches jump bigger in one frame, three times. | The pouches fill smoothly as each acorn goes in. | **check** (size snap) |
| 6 | 2:10 | The beaver dives with its leafy branch, then a different bare stick pops up in the mud beside the lodge. | It pushes the same branch into the mud, in view, and the branch's end stays showing. | **check** (pop) |
| 7 | 2:50-2:54 | As Digs sweeps, the old leaves vanish from the groundhog's door one by one. New leaves pop up 130 px away in a heap, while a few loose leaf particles fly. | Every leaf is carried or flicked along its own path to where it lands. | **check** (pop) |
| 8 | 4:15-4:20 | The bear shrinks by 25% as it walks into its den. | It keeps its size and goes into the dark of the den. | **check** (size drift) |
| 9 | 4:59 | The chickadee's seed jumps 90 px from the feeder tray to its bill. About 1.7 s later it vanishes. | It takes the seed it lands next to, and eats it (pecks, swallows) or flies off with it. | **check** (jump, pop) |
| 10 | whole video | The setting sun grows and shrinks with every camera zoom (from 60 to 119 px). Something that far away keeps one size on screen. | The sun and sky have a fixed size on screen. Far layers move and zoom less than near ones (parallax). | **check** (size drift) |

## 2. Limbs stretching or shrinking

| # | When | What happened | Remake | |
|---|------|---------------|--------|---|
| 11 | 4:04-4:23 | Hans' lifting tentacle reaches 3.6x his tentacle length in a straight line, and more along its curve. This is the owner's "6x stretch". | Hans walks close first. His tentacles stay within 1.6x (the owner allows up to about 2x). Two or three of them work together. | **check** (stretch) |
| 12 | 1:41-1:48 | Twigs' arm shrinks while he lifts it to saw: the upper arm drops to 0.5x and the forearm to 0.7x. Even his idle sway changes his arm length by about 15%. | Stick arms keep their length (elbow IK, as in the storybook kit). | **check** (stretch) |

## 3. Actions with no visible reason

| # | When | What happened | Remake | |
|---|------|---------------|--------|---|
| 13 | 4:05-4:23 | Hans lifts a branch "out of the bear's way", but the branch hangs above the den and above the bear the whole time. This is the owner's "a branch that wasn't in the way". | The branch really hangs across the den's mouth, low enough to be in the bear's path, until it is lifted. If nothing is in the way, Hans does something else. | **check** (no_reason) |
| 14 | 1:41-1:58 | Twigs cuts a dead, leafy branch off a fallen tree for the beaver. Beavers store fresh green branches (willow, aspen) to eat the bark under the ice; a dead branch isn't food. | A fresh green branch, from a willow growing at the pond. | by eye (fact-check before the remake) |
| 15 | 2:49-2:54 | Digs sweeps the old leaves out of the groundhog's door. Before hibernating, groundhogs line their sleeping chamber with dry grass and leaves, and close off the burrow from inside. Taking the bedding out works against it. | Digs brings dry grass or leaves to the door, and the groundhog pulls them in. | by eye (fact-check before the remake) |

## 4. Depth and perspective

| # | When | What happened | Remake | |
|---|------|---------------|--------|---|
| 16 | 3:01, 3:09 | The tiny, far-away geese fly in front of two big near trees. This is the owner's point. | Each layer has a depth. Far geese are painted behind the near trees (they pass behind the crowns), or they fly well above them. | **check** (depth_order) |
| 17 | whole video | Animal sizes are off. The black bear is drawn about as tall as the chipmunk sitting up (0.9x; even with storybook softening it should be about 2.6x). The groundhog and beaver are about the chipmunk's size, and the chickadee is 0.7x the bear. | Real size ratios, softened for the storybook (ratio^0.6): bear > groundhog ~ beaver > chipmunk > chickadee. | **check** (scale_mismatch) |
| 18 | whole video | The far forest and the fence slide and zoom exactly like the path, so the background reads as flat paint glued to the ground. | Layered background with parallax (the storybook kit's `shift`). | by eye |
| 19 | 0:00-2:40 | The falling "leaves" are dark round dots, all one size, drawn on top of everything, including over the chipmunk's face. | Leaf shapes, sized by their layer, with near leaves rare and soft. | by eye |

## 5. The action hidden (owner rule "show the action")

| # | When | What happened | Remake | |
|---|------|---------------|--------|---|
| 20 | 1:56-1:58 | The beaver taking its branch is about half hidden behind Wheels' cart and Twigs' legs. | Whoever helps stands to the side. The animal does its thing in the open. | **check** (hidden_action) |
| 21 | 4:09-4:15 | The bear walks to its den behind Springs and Digs, about a third hidden. Then Hans' tentacle crosses in front of it at the den mouth. | Same as 20. | **check** (hidden_action) |
| 22 | 2:56-3:27 | The groundhog at its door is partly behind Digs' paw. | Same as 20. | by eye |

## What the new checks are

`storycheck.Check.frame(...)` is called every frame by the storybook episode. Each rule is one kind of mistake above:

- **thing_jumps / size_snaps / size_drift / pops**: every loose thing keeps one id, position and size for its whole
  life. A thing appears only from a visible cause (`born`). It disappears only right where it visibly goes
  (`gone`, checked to within 2 of its sizes). A thing that really grows says why, and still has to grow smoothly.
- **limb_stretch**: rigid limbs keep 0.85-1.15 of their rest length. Tentacles reach at most 2x (we aim for 1.6x).
- **depth_order**: things are painted far to near. A farther thing painted over a nearer one where they overlap is
  an error.
- **scale_mismatch**: two animals at one depth keep their real size ratio, softened to ratio^0.6, within 0.6-1.7.
- **no_reason**: a helping move names its obstacle and the path of whoever it helps. The two must overlap.
- **hidden_action**: nearer things may cover at most 35% of the action the camera is showing.

The by-eye items (14, 15, 18, 19, 22) go on the remake's storyboard and self-review checklist, with the animal
facts checked against sources first.
