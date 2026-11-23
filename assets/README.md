# Assets

Sprites are integrated through `assets/manifest.json`. The catalog shares image
frames; each entity owns its animation state. Fonts use Pygame's bundled default
resource and are prepared when entering a screen.

## Sources and editable files

The first eight PNGs came from the teammate's branch. The remaining resources were
provided by the user in `sprites_cortados.zip`, kept extracted under
`assets/sprites_cortados/`. Individual original authors were not identified.
Production notes and known limitations supplied with the pack are preserved in
[the original pack README](sprites_cortados/pixel_art_pygame_pack_v2/README.md).
Those notes are the supplier's statements and have not been independently verified.

Full PNG sheets are the available raster sources; individual crops are kept in
`sprites_cortados/frames/` alongside their index. Layered source files were not
provided. The bundled slicing/demo scripts are supporting material and are not
part of game startup. Original files remain unchanged by the retouching pass.

## Integration conventions

- Look up the manifest's optional `source` path, or use the entry's key as the path.
  Paths are resolved under `assets/`, then under
  `sprites_cortados/pixel_art_pygame_pack_v2/`. Missing images use placeholders.
- Directional rows are down, left, right, up. Diagonal movement uses the nearest
  cardinal direction's animation.
- Each frame is centered on the entity. Logical frame sizes, grid, FPS and loop
  behavior are declared in the manifest. Visual scaling does not change hitboxes.
- The catalog and adapters prepare resources before drawing. Frames and transformed
  images are shared/cached; rendering never reads files per entity or per frame.
- All resources are included in the wheel under `boxhead/data`, so the installed
  game can run outside the checkout.
- The supplied pack includes synthesized animations and possible halos/seams.
  Audio is not implemented yet.

## Export inventory

Unless specified in the retouching section below, resources were supplied by the
team/user. Full sheets are the available PNG sources/exports; individual crops
remain in the original bundle. The frame center is the rendering origin.
All entries below are in the manifest.

| Asset | Frame (px) | Grid (rows × columns) | FPS |
| --- | --- | --- | --- |
| `player/player_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `player/player_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `player/player_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `player/player_death.png` | 96 × 96 | 1 × 6 | 9 |
| `player/player_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `player/player_shoot.png` | 96 × 96 | 4 × 3 | 12 |
| `enemies/enemy_basic_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `enemies/enemy_basic_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `enemies/enemy_basic_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `enemies/enemy_basic_death.png` | 96 × 96 | 1 × 4 | 9 |
| `enemies/enemy_basic_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `enemies/enemy_basic_attack.png` | 96 × 96 | 4 × 3 | 10 |
| `enemies/enemy_red_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `enemies/enemy_red_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `enemies/enemy_red_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `enemies/enemy_red_death.png` | 96 × 96 | 1 × 4 | 9 |
| `enemies/enemy_red_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `enemies/enemy_red_prepare.png` | 96 × 96 | 4 × 3 | 8 |
| `enemies/enemy_red_shoot.png` | 96 × 96 | 4 × 3 | 12 |
| `bosses/boss_01_walk.png` | 192 × 192 | 4 × 4 | 9 |
| `bosses/boss_01_idle.png` | 192 × 192 | 4 × 1 | 3 |
| `bosses/boss_01_hurt.png` | 192 × 192 | 4 × 2 | 8 |
| `bosses/boss_01_death.png` | 192 × 192 | 1 × 8 | 9 |
| `bosses/boss_01_shadow.png` | 192 × 192 | 1 × 1 | 8 |
| `bosses/boss_01_prepare.png` | 192 × 192 | 4 × 3 | 7 |
| `bosses/boss_01_attack.png` | 192 × 192 | 4 × 4 | 10 |
| `weapons/pistol.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/shotgun.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/smg.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/weapon_icons.png` | 64 × 64 | 1 × 3 | 8 |
| `projectiles/player_bullet.png` | 32 × 32 | 1 × 1 | 8 |
| `projectiles/player_pellet.png` | 32 × 32 | 1 × 1 | 8 |
| `projectiles/enemy_fireball.png` | 64 × 64 | 1 × 4 | 10 |
| `projectiles/boss_projectile.png` | 64 × 64 | 1 × 4 | 10 |
| `projectiles/orbital_satellite.png` | 80 × 80 | 1 × 4 | 10 |
| `effects/muzzle_flash.png` | 48 × 48 | 1 × 3 | 12 |
| `effects/impact_enemy.png` | 48 × 48 | 1 × 4 | 12 |
| `effects/impact_wall.png` | 48 × 48 | 1 × 4 | 12 |
| `effects/explosion_small.png` | 80 × 80 | 1 × 4 | 12 |
| `effects/explosion_large.png` | 128 × 128 | 1 × 6 | 12 |
| `effects/chain_explosion.png` | 128 × 128 | 1 × 6 | 12 |
| `effects/charge_effect.png` | 80 × 80 | 1 × 4 | 12 |
| `effects/spawn_effect.png` | 128 × 128 | 1 × 4 | 12 |
| `environment/floor_tiles.png` | 64 × 64 | 1 × 4 | 8 |
| `environment/walls.png` | 64 × 64 | 4 × 4 | 8 |
| `environment/obstacles.png` | 80 × 80 | 1 × 6 | 8 |
| `environment/decorations.png` | 64 × 64 | 1 × 5 | 8 |
| `ui/ui_icons_main.png` | 64 × 64 | 1 × 3 | 8 |
| `ui/healthbar.png` | 384 × 96 | 1 × 1 | 8 |
| `ui/xpbar.png` | 384 × 80 | 1 × 1 | 8 |
| `augments/augment_icons.png` | 80 × 80 | 2 × 6 | 8 |
| `shop/shop_upgrades.png` | 96 × 96 | 1 × 3 | 8 |
| `cards/card_frames.png` | 192 × 256 | 1 × 3 | 8 |
| `maps/map_01_thumb.png` | 256 × 256 | 1 × 1 | 8 |
| `maps/map_02_thumb.png` | 256 × 256 | 1 × 1 | 8 |
| `maps/map_03_thumb.png` | 256 × 256 | 1 × 1 | 8 |

## Atlas crop review

All 56 sheets (326 frames) match the declared logical dimensions. Some atlas
objects were misaligned within their cells. The manifest supports `source_rects`,
`anchor`, `frame_cleanup`, `tile_border`, `labels`, and an optional `source` path.
Explicit crops keep logical frame sizes; anchors center content or align its base.

- Obstacles use complete crate, crate, barrel, rock, large rock, and column frames.
  Map/chunk obstacle indices and the circular barrel index match that order.
- Decorations keep complete stones, grass, blood, grate, and bones groups, excluding
  the stray right-edge line. The grate previously crossed two grid cells.
- Augment symbols are centered in uniform borders. `labels` maps augment IDs to
  damage, range, XP, health, and other symbols without presentation-side guessing.
- Connected-component cleanup removes confirmed detached fragments from selected
  projectiles and explosion/spawn frames. There is no global color-removal filter
  that could erase legitimate particles.
- The player shadow uses its alpha content bounds and is positioned near the feet.

## Retouched sprites

Eight replacement sheets are stored in `retouched/` and selected through `source`:

- `retouched/weapons/smg.png`: isolated weapon without the purple rectangular matte.
- `retouched/environment/obstacles.png`: the five existing corrected obstacle crops
  plus an isolated replacement column without the neighboring vertical line.
- `retouched/bosses/boss_01_{walk,idle,hurt,prepare,attack,death}.png`: six boss
  animation sheets with cleaner silhouettes and reduced background contamination.

Retouching used the built-in `image_gen` tool through the **imagegen** skill.
[provenance.json](retouched/provenance.json) records the source assets, final paths,
and full prompt set. Generated results were cropped, resized with nearest-neighbor
sampling, and packed into the existing logical grids using Pygame. Their colors
and alpha channels were preserved. Existing frame counts, directional order, FPS,
and animation loops remain compatible with the gameplay code. No regeneration
happens at startup.

These are raster retouches rather than recovery of layered source art: a few fine
colored fringes and soft edge pixels remain, especially around some boss frames
and the column. The largest rectangular mattes and detached fragments are removed
or substantially reduced. The original pack remains available for comparison.
