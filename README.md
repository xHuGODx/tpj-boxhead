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

- **WASD**: move and face a direction.
- **Space**: fire in the direction the player faces; aiming does not use the mouse.
- **1 / 2 / 3**: switch weapons; on the augment screen, choose a card.
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

Each run starts with the pistol. Other weapons unlock automatically at the start
of their round and arrive with their own ammo supply. Their keys stay fixed.

| Weapon | Key | Unlock round | Starting ammo | Capacity | Ammo per crate |
| --- | --- | --- | --- | --- | --- |
| Pistol | 1 | 1 | 60 | 180 | 18 |
| SMG | 3 | 5 | 120 | 360 | 60 |
| Shotgun | 2 | 10 | 24 | 72 | 8 |

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
Round bonuses can exceed normal augment stack limits, while derived stat caps
still apply. All ammo, unlocks and round rewards reset with each new run.

## Development

The course prioritizes code organization and design patterns. This project uses
simple manual checks, without automated tests, mandatory linting or CI/CD. Open
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
