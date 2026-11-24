# TPJ · Boxhead

A survival shooter for the Game Programming Topics course, inspired by Boxhead,
with endless rounds, periodic bosses, run-specific augments and a permanent
upgrade shop inspired by Vampire Survivors.

The project uses custom sprites with a consistent style for the player, enemies,
weapons and environments. All in-game text is in English.

The academic focus is OOP, clear responsibilities, low coupling and software
design patterns applied to concrete problems.

## Current state

Two bounded arenas and an infinite map are playable, with an animated player,
three weapons, two enemy types, a boss, rounds, XP, augments and permanent upgrades.
The menu, pause, map and augment selection, and game-over screens are connected.
Run results are immutable and rewards are saved once per run. Sprites are bundled
with the installable package. Enemies use local navigation and explicit
attack/recovery/death states. Audio and final gameplay balancing are still pending.

## Run

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/xHuGODx/tpj-boxhead.git
cd tpj-boxhead
uv sync --locked
uv run boxhead
```

Alternatively, use `uv run python -m boxhead`. From the main menu, **Esc** or the
window close button exits the application.

Without uv, inside a Python 3.12 virtual environment:

```bash
python -m pip install -e .
python -m boxhead
```

`uv.lock` pins the development environment. Installing with pip uses the declared
dependencies without necessarily reproducing that lock.

## Controls

Menus support WASD navigation and Space to confirm, alongside arrows and Enter.
On map selection, A/D selects the map and W/S selects the run weapon (Q/E also works).
Pause and game-over screens also have selectable actions. Augment selection requires
releasing Space after shooting before confirming a card.

- **WASD**: move and face a direction.
- **Space**: fire in the direction the player faces; aiming does not use the mouse.
- **1 / 2 / 3**: choose a card on the augment screen.
- **Esc**: pause/resume; **M** from pause abandons the run and returns to the menu.
- **W/S or arrows**, then **Enter**: navigate menus and the shop.
- **A/D or arrows**, then **Enter**: choose a map. Retry keeps the selected map.
- **F3**: display hitboxes.
- **F11** or **Alt+Enter**: toggle fullscreen from any screen.

Fullscreen can also be toggled in the main menu or enabled at startup with
`uv run boxhead --fullscreen`. The preference is saved in the profile. The logical
canvas keeps its aspect ratio and play area; some monitors may show black bars.
Mouse coordinates are mapped back to the canvas for augment selection.

## Weapons, ammo and round rewards

The pistol is free. Buy SMG and Shotgun permanently in the shop to unlock more
loadout options. On map selection, use Q/E to choose ONE weapon for the whole run.
Only that weapon receives ammo and weapon augments; there is no switching in combat.

| Weapon | Shop price | Starting ammo | Capacity | Ammo per crate |
| --- | --- | --- | --- | --- |
| Pistol | Free | 60 | 180 | 18 |
| SMG | 250 | 120 | 360 | 60 |
| Shotgun | 400 | 24 | 72 | 8 |

The character starts with 100 AD and 1.00x attack speed, both shown in the HUD.
Weapon damage scales with AD/100; attack speed multiplies each weapon's firing
rate. Shop levels add +5 AD or +0.05 attack speed, up to five levels each. Gold
augments add +20 AD or +0.15 attack speed and stack without limits. Gray augments
continue to specialize individual weapons. Removed weapon-specific shop upgrades
are refunded once on startup.

A successful trigger pull consumes one bullet or shell; shotgun pellets share a
single shell. There are no magazines or reload controls. Each killed enemy has a
35% chance to drop an ammo crate at its position. Walk over it to replenish all
unlocked weapons, up to their capacities. Crates remain on the ground if every
reserve is full, expire after 60 seconds of gameplay, and pause with the game.

Completing a round pauses the game for one additional augment choice: three gray
augments for the weapon that killed the final enemy. This reward is separate from
XP level-ups; simultaneous rewards are queued and resolved one at a time. Bullets
and ricochets retain their firing weapon after switching, and chain explosions
inherit their triggering weapon. Independent orbital kills credit the active weapon.
All run augments stack without limits. Damage, fire rate, pellet count, range and
movement speed have no upper stat caps. Permanent shop upgrades retain their
individual level limits. Ammo and round rewards reset with each new run; weapon
ownership persists.

## Development

The augment expansion adds Split Chamber, Precision/Dead Center, Ember Rounds,
Blast Bloom, Slipstream Feed, Last Spark, Siege Frame, Redline and Aftershot.
The HUD shows projectile count, critical stats, explosion radius, revival charges
and temporary hit stacks. Run augments have unlimited stacks; new shop entries
retain the limits and prices in `docs/implementation-prompt-augments.md`.
Icon assignments and intentional symbol reuse are documented in `docs/icon-map.md`.

Focused regression checks can be run with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The course prioritizes code organization and design patterns. This project uses
manual checks plus focused combat regression tests, without mandatory linting or CI/CD. Open
the game and exercise the affected feature when checking a change.

```text
src/boxhead/
├── app.py            # Composition and navigation
├── core/             # FSM, commands, events, geometry and sprite catalog
├── world/            # Runs, combat, rounds, progression and results
├── presentation/     # HUD and shared sprite drawing
├── states/           # Input and screens
├── profile.py        # JSON persistence and atomic commits
└── shop.py           # Purchases and permanent upgrades
assets/               # Manifest, spritesheets and crops
```

Course documentation and source comments remain in Portuguese:

- [Game rules and tunable proposals](docs/game-design.md)
- [Architecture and course slides](docs/architecture.md)
- [Backlog and implementation order](docs/backlog.md)
- [Contribution guide](CONTRIBUTING.md)
- [GitHub issues](https://github.com/xHuGODx/tpj-boxhead/issues)
- [Assets, integration and retouching provenance](assets/README.md)

Tools: [Pygame](https://pypi.org/project/pygame/) and
[uv projects](https://docs.astral.sh/uv/guides/projects/).
