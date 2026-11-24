"""Comportamentos plugáveis do jogador (base dos augments prismáticos).

O `World` não conhece nenhum augment: chama estes ganchos em momentos fixos (disparo,
acerto, morte, tick). Um augment prismático concede um *tipo* de comportamento através
dos `Modifiers`; acrescentar um novo é escrever uma classe `Behavior` e registá-la em
`BEHAVIOR_TYPES`, sem `if augment_id == ...` no jogador, nas armas ou no mundo.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame import Vector2

from boxhead.world.fx import Body

if TYPE_CHECKING:
    from boxhead.world.enemy import Enemy
    from boxhead.world.projectile import Projectile
    from boxhead.world.world import World


class Behavior:
    """Base com ganchos vazios; `level` é o número de acumulações do augment."""

    kind = "behavior"

    def __init__(self, level: int) -> None:
        self.level = level

    def set_level(self, level: int) -> None:
        self.level = level

    def on_fire(self, world: World, projectile: Projectile) -> None:
        """Um projétil do jogador acabou de ser criado."""

    def on_hit(self, world: World, projectile: Projectile, enemy: Enemy, point: Vector2) -> bool:
        """Um projétil do jogador acertou. Devolve True se o projétil continua em voo."""
        return False

    def on_kill(self, world: World, enemy: Enemy, depth: int,
                weapon_name: str | None = None) -> None:
        """Um inimigo morreu; `depth` conta as mortes encadeadas por efeitos."""

    def update(self, world: World, dt: float) -> None:
        """Avança o comportamento um tick (a simulação parada não chama isto)."""

    def bodies(self, world: World) -> list[Body]:
        """Corpos a desenhar neste momento."""
        return []


class Ricochet(Behavior):
    """Os projéteis saltam para o inimigo mais próximo, com saltos e alcance limitados."""

    kind = "ricochet"
    SEARCH_RADIUS = 320.0  # distância máxima de um salto
    DAMAGE_KEEP = 0.8  # cada salto mantém 80% do dano

    @property
    def bounces(self) -> int:
        return self.level + 1  # 2, 3 ou 4 saltos

    def on_fire(self, world: World, projectile: Projectile) -> None:
        projectile.bounces_left = self.bounces

    def on_hit(self, world: World, projectile: Projectile, enemy: Enemy, point: Vector2) -> bool:
        if projectile.bounces_left <= 0:
            return False
        candidates = [
            e
            for e in world.enemies_near(point, self.SEARCH_RADIUS)
            if e.id not in projectile.hit_ids and world.line_of_sight(point, e.position)
        ]
        if not candidates:
            return False
        target = min(candidates, key=lambda e: e.position.distance_to(point))
        speed = projectile.velocity.length()
        projectile.position = Vector2(point)
        projectile.velocity = (target.position - point).normalize() * speed
        projectile.damage *= self.DAMAGE_KEEP
        projectile.bounces_left -= 1
        projectile.range_left = self.SEARCH_RADIUS + 80  # cada salto tem o seu alcance curto
        return True


class ChainReaction(Behavior):
    """Os inimigos explodem ao morrer; as explosões podem matar e encadear, até um limite."""

    kind = "chain_reaction"
    MAX_DEPTH = 3  # profundidade máxima da cadeia: sem recursão infinita

    @property
    def radius(self) -> float:
        return 80.0 + 20.0 * (self.level - 1)

    @property
    def damage(self) -> float:
        return 35.0 + 20.0 * (self.level - 1)

    def on_kill(self, world: World, enemy: Enemy, depth: int,
                weapon_name: str | None = None) -> None:
        if depth >= self.MAX_DEPTH:
            return
        radius = self.radius * (1 + world.player.modifiers.blast_radius_bonus)
        world.add_fx("explosion", enemy.position, radius, 0.35)
        for target in world.enemies_near(enemy.position, radius):
            if target is not enemy:
                world.damage_enemy(target, self.damage, chain_depth=depth + 1,
                                   weapon_name=weapon_name)


class Orbitals(Behavior):
    """Satélites orbitam o jogador e ferem o que tocam, com cooldown por alvo."""

    kind = "orbitals"
    ORBIT_RADIUS = 95.0
    ANGULAR_SPEED = 3.2  # rad/s
    BODY_RADIUS = 12.0
    DAMAGE = 14.0
    HIT_COOLDOWN = 0.5  # por inimigo, partilhado entre satélites
    COLOR = (130, 220, 255)

    def __init__(self, level: int) -> None:
        super().__init__(level)
        self.angle = 0.0
        self._cooldowns: dict[int, float] = {}

    @property
    def count(self) -> int:
        return self.level + 1  # 2, 3 ou 4 satélites

    def positions(self, center: Vector2) -> list[Vector2]:
        step = 2 * math.pi / self.count
        return [
            center + Vector2(self.ORBIT_RADIUS, 0).rotate_rad(self.angle + i * step)
            for i in range(self.count)
        ]

    def update(self, world: World, dt: float) -> None:
        self.angle = (self.angle + self.ANGULAR_SPEED * dt) % (2 * math.pi)
        self._cooldowns = {k: v - dt for k, v in self._cooldowns.items() if v - dt > 0}
        for position in self.positions(world.player.position):
            for enemy in world.enemies_near(position, self.BODY_RADIUS):
                if enemy.id not in self._cooldowns:
                    self._cooldowns[enemy.id] = self.HIT_COOLDOWN
                    world.damage_enemy(enemy, self.DAMAGE)

    def bodies(self, world: World) -> list[Body]:
        return [
            Body(p, self.BODY_RADIUS, self.COLOR) for p in self.positions(world.player.position)
        ]


BEHAVIOR_TYPES: dict[str, type[Behavior]] = {
    Ricochet.kind: Ricochet,
    ChainReaction.kind: ChainReaction,
    Orbitals.kind: Orbitals,
}
