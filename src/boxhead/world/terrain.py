"""Instâncias de mapas: arena fixa ou vizinhança de chunks determinísticos."""
from dataclasses import dataclass
from math import cos, sin, tau
from random import Random

from pygame import Rect, Vector2

from boxhead.world.map import DecorationDef, MapDefinition, ObstacleDef

CHUNK_SIZE = 768
CHUNK_RADIUS = 2


@dataclass(frozen=True)
class Chunk:
    obstacles: tuple[ObstacleDef, ...]
    decorations: tuple[DecorationDef, ...]


class Terrain:
    infinite = False

    def __init__(self, definition: MapDefinition):
        self.definition = definition

    def __getattr__(self, name):
        # Configuração imutável é partilhada; só o terreno infinito tem estado de carga.
        return getattr(self.definition, name)

    def update(self, center: Vector2) -> None:
        pass

    def spawn_candidates(self, center: Vector2, distance: float,
                         viewport=(1100, 700), margin: float = 100) -> tuple[Vector2, ...]:
        """Anel junto às margens da vista, independente de estar numa arena ou chunks."""
        half_width, half_height = viewport[0]/2+margin, viewport[1]/2+margin
        points = []
        for i in range(24):
            direction = Vector2(cos(i*tau/24), sin(i*tau/24))
            horizontal = half_width/abs(direction.x) if abs(direction.x) > 1e-8 else float('inf')
            vertical = half_height/abs(direction.y) if abs(direction.y) > 1e-8 else float('inf')
            radius = max(distance, min(horizontal, vertical))
            points.append(center+direction*radius)
        return tuple(points)


class InfiniteTerrain(Terrain):
    infinite = True

    def __init__(self, definition: MapDefinition, seed: int):
        super().__init__(definition)
        self.seed = seed
        self.chunks: dict[tuple[int, int], Chunk] = {}
        self._center_chunk = None
        self.update(Vector2(definition.player_start))

    def generate_chunk(self, cx: int, cy: int) -> Chunk:
        # Não usa hash() de Python nem o RNG do combate: regressar reproduz o terreno.
        mixed = (self.seed ^ (cx * 0x9E3779B185EBCA87) ^ (cy * 0xC2B2AE3D27D4EB4F)) & ((1 << 64)-1)
        rng = Random(mixed)
        obstacles, decorations = [], []
        slots = [(x, y) for x in (192, 384, 576) for y in (192, 384, 576)]
        rng.shuffle(slots)
        for x, y in slots[:rng.randint(1, 3)]:
            center = Vector2(cx*CHUNK_SIZE+x, cy*CHUNK_SIZE+y)
            if center.length() < 240:
                continue
            index = rng.randrange(6)
            obstacles.append(ObstacleDef(Rect(round(center.x)-40, round(center.y)-40, 80, 80), index, index == 1))
        for _ in range(2):
            point = Vector2(cx*CHUNK_SIZE+rng.randrange(96,672), cy*CHUNK_SIZE+rng.randrange(96,672))
            decorations.append(DecorationDef(point, rng.randrange(5)))
        return Chunk(tuple(obstacles), tuple(decorations))

    def update(self, center: Vector2) -> None:
        cell = (int(center.x // CHUNK_SIZE), int(center.y // CHUNK_SIZE))
        if cell == self._center_chunk:
            return
        self._center_chunk = cell
        keys = {(x,y) for x in range(cell[0]-CHUNK_RADIUS,cell[0]+CHUNK_RADIUS+1)
                for y in range(cell[1]-CHUNK_RADIUS,cell[1]+CHUNK_RADIUS+1)}
        self.chunks = {key: self.chunks[key] if key in self.chunks else self.generate_chunk(*key)
                       for key in sorted(keys)}
        self.obstacles = tuple(o for chunk in self.chunks.values() for o in chunk.obstacles)
        self.decorations = tuple(d for chunk in self.chunks.values() for d in chunk.decorations)
        side = (2*CHUNK_RADIUS+1)*CHUNK_SIZE
        self.bounds = Rect((cell[0]-CHUNK_RADIUS)*CHUNK_SIZE,
                           (cell[1]-CHUNK_RADIUS)*CHUNK_SIZE,side,side)
        self.playable_bounds = self.bounds



def create_terrain(definition: MapDefinition, seed: int) -> Terrain:
    return InfiniteTerrain(definition, seed) if definition.infinite else Terrain(definition)
