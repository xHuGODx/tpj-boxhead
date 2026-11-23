"""Inimigos: definição imutável + estado de instância + FSM própria.

A FSM do inimigo é independente da `StateMachine` da aplicação, como pede o
`architecture.md`: não conhece eventos SDL nem superfícies. O inimigo normal ataca
corpo a corpo (Chase ⇄ Attack); o vermelho dispara à distância (Chase ⇄ RangedAttack).
Ambos são o mesmo `Enemy`, parametrizado por uma `EnemyDef` (Type Object).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol

from pygame import Vector2

from boxhead.world.projectile import Projectile

MUZZLE_GAP = 6


@dataclass(frozen=True)
class RangedAttack:
    """Parâmetros do ataque à distância; ausentes nos inimigos corpo a corpo."""

    damage: int
    projectile_speed: float
    projectile_range: float
    projectile_radius: float
    engage_range: float  # distância entre centros a que pára e prepara o disparo
    color: tuple[int, int, int] = (255, 110, 70)
    projectiles: int = 1  # por disparo
    ring: bool = False  # True: espalha os projéteis em círculo, em vez de apontar ao jogador


@dataclass(frozen=True)
class EnemyDef:
    """Type Object: valores partilhados por todos os inimigos deste tipo."""

    name: str
    max_health: float
    speed: float
    radius: float
    contact_damage: int
    attack_range: float  # folga entre os círculos para começar a atacar corpo a corpo
    windup: float  # preparação visível antes de o golpe/disparo
    recovery: float  # pausa depois do golpe/disparo
    xp_reward: int
    coin_reward: int
    sprite_prefix: str
    strike_leeway: float = 10.0  # o golpe ainda acerta se o jogador recuar um pouco
    ranged: RangedAttack | None = None
    # Animação visual → sufixo do ficheiro (`<prefix>_<sufixo>.png`).
    animations: tuple[tuple[str, str], ...] = (("walk", "walk"), ("attack", "attack"))
    is_boss: bool = False


BASIC = EnemyDef(
    name="Basic",
    max_health=50,
    speed=95,
    radius=22,
    contact_damage=10,
    attack_range=8,
    windup=0.35,
    recovery=0.6,
    xp_reward=10,
    coin_reward=1,
    sprite_prefix="enemies/enemy_basic",
)

RED = EnemyDef(
    name="Red",
    max_health=120,
    speed=75,
    radius=24,
    contact_damage=0,
    attack_range=0,
    windup=0.7,  # preparação longa e visível: dá tempo para desviar
    recovery=1.1,
    xp_reward=25,
    coin_reward=3,
    sprite_prefix="enemies/enemy_red",
    ranged=RangedAttack(
        damage=12,
        projectile_speed=380,
        projectile_range=700,
        projectile_radius=7,
        engage_range=420,
    ),
    animations=(("walk", "walk"), ("prepare", "prepare"), ("shoot", "shoot")),
)


BOSS = EnemyDef(
    name="Boss",
    max_health=900,
    speed=60,
    radius=56,
    contact_damage=0,
    attack_range=0,
    windup=1.0,  # preparação longa: o anel de aviso cresce até ao disparo
    recovery=1.5,  # janela de vulnerabilidade entre rajadas
    xp_reward=200,
    coin_reward=30,
    sprite_prefix="bosses/boss_01",
    ranged=RangedAttack(
        damage=15,
        projectile_speed=300,
        projectile_range=700,
        projectile_radius=9,
        engage_range=380,
        color=(190, 90, 255),
        projectiles=14,
        ring=True,
    ),
    animations=(("walk", "walk"), ("prepare", "prepare"), ("shoot", "attack")),
    is_boss=True,
)


class Target(Protocol):
    """O que o inimigo precisa de saber do alvo; evita depender de `Player`."""

    position: Vector2
    radius: float

    def take_damage(self, amount: float) -> None: ...


class EnemyState(ABC):
    name = "state"
    visual = "walk"  # animação a mostrar
    progress = 0.0  # 0..1 da preparação em curso (para telegrafar o ataque)

    def enter(self, enemy: Enemy) -> None:
        return None

    @abstractmethod
    def update(self, enemy: Enemy, dt: float, target: Target) -> EnemyState | None:
        """Devolve o próximo estado, ou None para continuar neste."""


class ChaseState(EnemyState):
    name = "chase"
    visual = "walk"

    def update(self, enemy: Enemy, dt: float, target: Target) -> EnemyState | None:
        offset = target.position - enemy.position
        distance = offset.length()
        if enemy.in_attack_range(target, distance):
            return enemy.start_attack()
        direction = offset / distance
        # Pequeno desvio fixo por inimigo: sem ele, um inimigo alinhado de frente com
        # o centro de um obstáculo fica preso para sempre (não há pathfinding ainda).
        if distance > 150:
            direction = direction.rotate(enemy.steer_degrees)
        enemy.position += direction * enemy.speed * dt
        enemy.orientation = direction
        return None


class AttackState(EnemyState):
    """Golpe corpo a corpo: preparação, golpe (uma vez), recuperação."""

    name = "attack"
    visual = "attack"

    def __init__(self) -> None:
        self._elapsed = 0.0
        self._struck = False

    def update(self, enemy: Enemy, dt: float, target: Target) -> EnemyState | None:
        offset = target.position - enemy.position
        distance = offset.length()
        if distance > 0:
            enemy.orientation = offset / distance
        self._elapsed += dt
        d = enemy.definition
        if not self._struck and self._elapsed >= d.windup:
            self._struck = True
            if distance <= enemy.reach(target) + d.strike_leeway:
                target.take_damage(d.contact_damage)
        if self._struck and self._elapsed >= d.windup + d.recovery:
            return ChaseState()
        return None


class RangedAttackState(EnemyState):
    """Disparo: fica parado a apontar (visível), dispara uma vez, recupera."""

    name = "attack"

    def __init__(self) -> None:
        self._elapsed = 0.0
        self._fired = False
        self._windup = 1.0

    @property
    def visual(self) -> str:  # type: ignore[override]
        return "shoot" if self._fired else "prepare"

    @property
    def progress(self) -> float:  # type: ignore[override]
        return 0.0 if self._fired else min(1.0, self._elapsed / self._windup)

    def enter(self, enemy: Enemy) -> None:
        self._windup = enemy.definition.windup

    def update(self, enemy: Enemy, dt: float, target: Target) -> EnemyState | None:
        d = enemy.definition
        ranged = d.ranged
        assert ranged is not None
        self._elapsed += dt
        if not self._fired:
            offset = target.position - enemy.position
            if offset.length_squared() > 0:
                enemy.orientation = offset.normalize()  # acompanha o jogador até disparar
            if self._elapsed >= d.windup:
                self._fired = True
                for direction in self._directions(enemy, ranged):
                    enemy.outbox.append(
                        Projectile(
                            position=enemy.position + direction * (enemy.radius + MUZZLE_GAP),
                            velocity=direction * ranged.projectile_speed,
                            damage=ranged.damage,
                            radius=ranged.projectile_radius,
                            range_left=ranged.projectile_range,
                            color=ranged.color,
                            hostile=True,
                            sprite_key=("projectiles/boss_projectile.png" if ranged.ring
                                        else "projectiles/enemy_fireball.png"),
                        )
                    )
        if self._fired and self._elapsed >= d.windup + d.recovery:
            return ChaseState()
        return None

    @staticmethod
    def _directions(enemy: Enemy, ranged: RangedAttack) -> list[Vector2]:
        if not ranged.ring:
            return [Vector2(enemy.orientation)]
        step = 360 / ranged.projectiles
        directions = [
            Vector2(1, 0).rotate(enemy.pattern_phase + i * step) for i in range(ranged.projectiles)
        ]
        enemy.pattern_phase += step / 2  # a rajada seguinte encaixa nos intervalos da anterior
        return directions


@dataclass(eq=False)
class Enemy:
    id: int
    definition: EnemyDef
    position: Vector2
    health: float
    speed: float
    steer_degrees: float = 0.0
    orientation: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    alive: bool = True
    pattern_phase: float = 0.0  # rotação (graus) da próxima rajada em anel
    # Projéteis acabados de disparar; o `World` recolhe-os (o inimigo não conhece o mundo).
    outbox: list[Projectile] = field(default_factory=list, init=False, repr=False)
    _state: EnemyState = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.max_health = self.health
        self._state = ChaseState()
        self._state.enter(self)

    @property
    def radius(self) -> float:
        return self.definition.radius

    @property
    def state_name(self) -> str:
        return self._state.name

    @property
    def visual(self) -> str:
        """Animação a mostrar: walk, attack, prepare ou shoot."""
        return self._state.visual

    @property
    def windup_progress(self) -> float:
        """0..1 enquanto prepara um ataque, 0 nos restantes estados."""
        return self._state.progress

    @property
    def is_boss(self) -> bool:
        return self.definition.is_boss

    def reach(self, target: Target) -> float:
        """Distância entre centros a partir da qual está encostado ao alvo."""
        return self.radius + target.radius + self.definition.attack_range

    def in_attack_range(self, target: Target, distance: float) -> bool:
        ranged = self.definition.ranged
        limit = ranged.engage_range if ranged else self.reach(target)
        return distance <= limit

    def start_attack(self) -> EnemyState:
        return RangedAttackState() if self.definition.ranged else AttackState()

    def update(self, dt: float, target: Target) -> None:
        if not self.alive:
            return
        next_state = self._state.update(self, dt, target)
        if next_state is not None:
            self._state = next_state
            self._state.enter(self)

    def take_damage(self, amount: float) -> bool:
        """Aplica dano; devolve True apenas na transição vivo → morto (uma só vez)."""
        if not self.alive:
            return False
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            return True
        return False
