"""Mapas: dados puros (limites, obstáculos, spawns, cores). Sem desenho."""

from __future__ import annotations

from dataclasses import dataclass, replace

from pygame import Rect, Vector2

OBSTACLE_SIZE = 80  # igual ao frame_size do manifest


@dataclass(frozen=True)
class ObstacleDef:
    """Um obstáculo: hitbox + índice do frame em environment/obstacles.png."""

    rect: Rect
    sprite_index: int
    circular: bool = False


@dataclass(frozen=True)
class DecorationDef:
    """Decoração: posição no mundo + índice em environment/decorations.png."""

    position: Vector2
    sprite_index: int


@dataclass(frozen=True)
class MapDefinition:
    name: str
    bounds: Rect
    obstacles: tuple[ObstacleDef, ...]
    decorations: tuple[DecorationDef, ...]
    spawn_points: tuple[Vector2, ...]
    floor_tiles: tuple[int, ...]
    tile_size: int
    border_color: tuple[int, int, int]
    wall_thickness: int
    player_start: Vector2
    infinite: bool = False
    description: str = "Arena limitada com obstáculos e rondas infinitas."
    thumbnail: str = "maps/map_01_thumb.png"

    @property
    def playable_bounds(self) -> Rect:
        """Área onde o jogador pode estar: os limites menos a espessura das paredes."""
        inset = -2 * self.wall_thickness
        return self.bounds.inflate(inset, inset)


def _obstacle(cx: int, cy: int, sprite_index: int, *, circular: bool = False) -> ObstacleDef:
    """Obstáculo de 80×80 centrado em (cx, cy)."""
    half = OBSTACLE_SIZE // 2
    return ObstacleDef(
        rect=Rect(cx - half, cy - half, OBSTACLE_SIZE, OBSTACLE_SIZE),
        sprite_index=sprite_index,
        circular=circular,
    )


# Índices de environment/obstacles.png (80×80, 6 frames):
#   0 = crate, 1 = barril, 2 = rocha grande,
#   3 = rocha, 4 = rocha pequena, 5 = coluna
_OBSTACLES: tuple[ObstacleDef, ...] = (
    # centro da arena — coluna
    _obstacle(0, 0, 5),
    # noroeste — rochas e crate
    _obstacle(-600, -400, 2),
    _obstacle(-500, -400, 0),
    _obstacle(-600, -300, 3),
    # sudeste — crates
    _obstacle(400, 400, 0),
    _obstacle(500, 500, 1, circular=True),
    # norte — rochas
    _obstacle(-200, -800, 2),
    _obstacle(200, -800, 3),
    # sul — barril
    _obstacle(0, 700, 1, circular=True),
    # leste — rochas
    _obstacle(800, 0, 4),
    _obstacle(900, 100, 4),
    # oeste — barril
    _obstacle(-900, 0, 1, circular=True),
)

_DECORATIONS: tuple[DecorationDef, ...] = (
    DecorationDef(Vector2(-350, -450), 0),
    DecorationDef(Vector2(700, -200), 1),
    DecorationDef(Vector2(-800, 600), 2),
    DecorationDef(Vector2(900, 900), 3),
    DecorationDef(Vector2(-300, 1200), 4),
    DecorationDef(Vector2(400, -1100), 1),
    DecorationDef(Vector2(-1100, -900), 0),
    DecorationDef(Vector2(1300, -1200), 2),
)


ARENA: MapDefinition = MapDefinition(
    name="Arena",
    bounds=Rect(-2048, -1536, 4096, 3072),  # múltiplos de 64: paredes sem sobras
    obstacles=_OBSTACLES,
    decorations=_DECORATIONS,
    spawn_points=(
        Vector2(-1800, -1300),
        Vector2(1800, -1300),
        Vector2(-1800, 1300),
        Vector2(1800, 1300),
        Vector2(0, -1200),
        Vector2(0, 1200),
        Vector2(-1200, 0),
        Vector2(1200, 0),
    ),
    floor_tiles=(0, 1),
    tile_size=64,
    border_color=(120, 132, 150),
    wall_thickness=64,
    player_start=Vector2(0, 150),  # fora da coluna central (0, 0)
)


RUINS = replace(
    ARENA, name="Ruínas", floor_tiles=(2,3),
    obstacles=tuple(_obstacle(x,y,(i%6)) for i,(x,y) in enumerate(
        [(-720,-600),(-240,-600),(240,-600),(720,-600),
         (-720,0),(-240,0),(240,0),(720,0),
         (-720,600),(-240,600),(240,600),(720,600)])),
    description="Arena limitada com colunas e corredores largos.",
    thumbnail="maps/map_02_thumb.png",
)
INFINITE = replace(
    ARENA, name="Terras infinitas", infinite=True, obstacles=(), decorations=(),
    spawn_points=(), wall_thickness=0, player_start=Vector2(), floor_tiles=(0,1),
    description="Exploração sem fronteiras; terreno por chunks e rondas infinitas.",
    thumbnail="maps/map_03_thumb.png",
)
MAPS: dict[str, MapDefinition] = {"arena": ARENA, "ruins": RUINS, "infinite": INFINITE}
