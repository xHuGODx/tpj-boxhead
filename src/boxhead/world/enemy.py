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
    animations: tuple[tuple[str, str], ...] = (("walk", "walk"), ("attack", "attack"), ("recover", "idle"), ("death", "death"))
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
    animations=(("walk", "walk"), ("prepare", "prepare"), ("shoot", "shoot"), ("recover", "idle"), ("death", "death")),
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
    animations=(("walk", "walk"), ("prepare", "prepare"), ("shoot", "attack"), ("recover", "idle"), ("death", "death")),
    is_boss=True,
)


class Target(Protocol):
    """O que o inimigo precisa de saber do alvo; evita depender de `Player`."""

    position: Vector2
    radius: float
    max_health: float

    def change_state(self, state: EnemyState) -> None:
        self._state.exit(self)
        self._state = state
        self._state.enter(self)

    def take_damage(self, amount: float) -> None: ...


class EnemyState(ABC):
    name = "state"
    visual = "walk"
    progress = 0.0

    def enter(self, enemy: Enemy) -> None:
        pass

    def exit(self, enemy: Enemy) -> None:
        pass

    @abstractmethod
    def update(self, enemy: Enemy, dt: float, target: Target) -> EnemyState | None:
        """Devolve a transição, sem conhecer mundo, SDL ou sprites."""


class ChaseState(EnemyState):
    name = "chase"

    def update(self, enemy, dt, target):
        offset = target.position-enemy.position
        if enemy.in_attack_range(target, offset.length()):
            return enemy.start_attack()
        direction = enemy.steering
        if direction is None:
            direction = offset.normalize() if offset.length_squared() else Vector2()
        enemy.position += direction*enemy.speed*dt
        if direction.length_squared():
            enemy.orientation = Vector2(direction)
        return None


class RecoveryState(EnemyState):
    name = "recovery"
    visual = "recover"

    def enter(self, enemy):
        self.elapsed = 0.0

    def update(self, enemy, dt, target):
        self.elapsed += dt
        return ChaseState() if self.elapsed >= enemy.recovery else None


class AttackState(EnemyState):
    name = "attack"
    visual = "attack"

    def enter(self, enemy):
        self.elapsed = 0.0

    def update(self, enemy, dt, target):
        offset = target.position-enemy.position
        if offset.length_squared():
            enemy.orientation = offset.normalize()
        self.elapsed += dt
        if self.elapsed >= enemy.windup:
            if enemy.can_see and offset.length() <= enemy.reach(target)+enemy.definition.strike_leeway:
                damage = enemy.definition.contact_damage * enemy.damage_multiplier
                if enemy.lethal_attacks:
                    damage = target.max_health
                elif enemy.damage_cap_fraction is not None:
                    damage = min(damage, target.max_health * enemy.damage_cap_fraction)
                target.take_damage(damage)
            return RecoveryState()
        return None


class PrepareRangedState(EnemyState):
    name = "prepare"
    visual = "prepare"

    def enter(self, enemy):
        self.elapsed = 0.0
        self.windup = enemy.windup

    @property
    def progress(self):
        return min(1.0,self.elapsed/self.windup)

    def update(self, enemy, dt, target):
        if not enemy.can_see:
            return ChaseState()
        offset=target.position-enemy.position
        if offset.length_squared():
            enemy.orientation=offset.normalize()
        self.elapsed+=dt
        return RangedAttackState() if self.elapsed >= self.windup else None


class RangedAttackState(EnemyState):
    name = "shoot"
    visual = "shoot"

    def enter(self, enemy):
        self.elapsed=0.0
        attack=enemy.definition.ranged
        if attack is None or not enemy.alive:
            return
        if attack.ring:
            step=360/attack.projectiles
            directions=[Vector2(1,0).rotate(enemy.pattern_phase+i*step) for i in range(attack.projectiles)]
            enemy.pattern_phase+=step/2
        else:
            directions=[Vector2(enemy.orientation)]
        for direction in directions:
            enemy.outbox.append(Projectile(
                position=enemy.position+direction*(enemy.radius+MUZZLE_GAP),
                velocity=direction*attack.projectile_speed,
                damage=attack.damage*enemy.damage_multiplier,
                radius=attack.projectile_radius, range_left=attack.projectile_range,
                color=attack.color, hostile=True, owner_id=enemy.id,
                sprite_key=("projectiles/boss_projectile.png" if attack.ring
                            else "projectiles/enemy_fireball.png"),
                damage_cap_fraction=enemy.damage_cap_fraction,
                lethal=enemy.lethal_attacks,
            ))

    def update(self, enemy, dt, target):
        self.elapsed+=dt
        return RecoveryState() if self.elapsed >= 0.15 else None


class DeadState(EnemyState):
    name = "dead"
    visual = "death"

    def enter(self, enemy):
        enemy.outbox.clear()

    def update(self, enemy, dt, target):
        return None


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
    damage_multiplier: float = 1.0
    reward_multiplier: float = 1.0
    xp_reward_multiplier: float = 1.0
    timing_multiplier: float = 1.0
    damage_cap_fraction: float | None = None
    is_elite: bool = False
    is_prismatic: bool = False
    lethal_attacks: bool = False
    death_age: float = 0.0
    steering: Vector2 | None = field(default=None, repr=False)
    can_see: bool = True
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

    @property
    def windup(self) -> float:
        return self.definition.windup * self.timing_multiplier

    @property
    def recovery(self) -> float:
        return self.definition.recovery * self.timing_multiplier

    def reach(self, target: Target) -> float:
        """Distância entre centros a partir da qual está encostado ao alvo."""
        return self.radius + target.radius + self.definition.attack_range

    def in_attack_range(self, target: Target, distance: float) -> bool:
        ranged = self.definition.ranged
        limit = ranged.engage_range if ranged else self.reach(target)
        return self.can_see and distance <= limit

    def start_attack(self) -> EnemyState:
        return PrepareRangedState() if self.definition.ranged else AttackState()

    def update(self, dt: float, target: Target) -> None:
        if not self.alive:
            return
        next_state = self._state.update(self, dt, target)
        if next_state is not None:
            self.change_state(next_state)

    def change_state(self, state: EnemyState) -> None:
        self._state.exit(self)
        self._state = state
        self._state.enter(self)

    def take_damage(self, amount: float) -> bool:
        """Aplica dano; devolve True apenas na transição vivo → morto (uma só vez)."""
        if not self.alive:
            return False
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            self.change_state(DeadState())
            return True
        return False
