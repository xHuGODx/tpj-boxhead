# RAGE enemy sprites

Generated with the built-in `image_gen` tool, using the project's Basic enemy
sprites as visual references. Original sprites remain unchanged.

## Files

- `enemy_rage_walk.png`: four walking poses per direction, 4 × 4 sheet.
- `enemy_rage_attack.png`: four melee attack poses per direction, 4 × 4 sheet.
- `enemy_rage_death.png`: four death poses, one horizontal row.
- The idle animation reuses the first walking pose of each direction through
  `assets/manifest.json`; there is no separate idle PNG.

Directional row order: down, left, right, up. All PNGs retain transparent alpha.
The manifest defines individual source rectangles, bottom alignment, uniform
scaling and removal of isolated detached components. This keeps feet anchored
and prevents neighboring frames from leaking into the animation.

## Generation prompt set — production brief summary

Common constraints: pixel-art sprite sheet for a Pygame game. Match the existing
green Basic zombie: green skin, red eyes, brown clothing, proportions and view.
Create its RAGE variant with compact orange/yellow flames attached to its head
and shoulders. Keep the face and silhouette readable at gameplay size. Genuine
transparent background, empty gutters, full padding, no text, labels, watermarks,
grid lines or scenery. Keep the feet aligned and each pose wholly within its cell.

Walking sheet: four frames for each of down, left, right and up, in four rows.
Small alternating steps and consistent body size, with lively but compact flames.
The refinement requested clean transparency, additional padding and no stray
detached particles around the sprites.

Attack sheet: match the selected flaming walking character exactly. Four melee
attack poses in each directional row: anticipation, reach, strike, return. Preserve
clothes, palette, scale and direction order. Do not introduce weapons or scenery.

Death sheet: match the selected flaming character in a four-frame horizontal
sequence: upright, falling, collapsed, final body on the ground with fading flames.
Keep the floor baseline fixed, preserve the body identity, and leave generous
transparent gutters between every frame.

Selected built-in output identifiers:

- Walk: `exec-4c663177-5d56-4c2b-9241-b168b33c9c0b.png`
- Attack: `exec-b41bd95d-628c-46b7-a8a1-1fe4d2287e89.png`
- Death: `exec-ebeb750e-4910-4fe5-ad88-a6c2edfacccc.png`

The selected outputs are copied here and used by the game directly. No API/CLI
fallback was used.
