"""Jogador: posição, orientação persistente, vida e armas com cooldown próprio.

Os valores efetivos (velocidade, vida máxima, armas) são derivados da base e dos
`Modifiers` atuais; a base nunca é alterada.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Vector2

from boxhead.core.commands import Command, Move, Shoot, SwitchWeapon
from boxhead.world.attributes import Modifiers, derive_weapon
from boxhead.world.weapons import WEAPONS, WeaponDef

SPEED = 220.0
RADIUS = 24
MAX_HEALTH = 100


@dataclass
class Player:
    position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    orientation: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    health: float = MAX_HEALTH
    weapon_slot: int = 0
    weapons: tuple[WeaponDef, ...] = WEAPONS  # definições base, partilhadas e imutáveis
    modifiers: Modifiers = field(default_factory=Modifiers)
    _cooldowns: list[float] = field(init=False, repr=False)
    _effective_weapons: tuple[WeaponDef, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Um cooldown por arma: trocar de arma não permite contornar a cadência.
        self._cooldowns = [0.0] * len(self.weapons)
        self._effective_weapons = self._derive_weapons()
        self.health = min(self.health, self.max_health)

    def _derive_weapons(self) -> tuple[WeaponDef, ...]:
        return tuple(derive_weapon(w, self.modifiers.for_weapon(w.name)) for w in self.weapons)

    def set_modifiers(self, modifiers: Modifiers) -> None:
        """Aplica novos modificadores (sempre calculados a partir da base da partida).

        Subir a vida máxima cura o mesmo valor; descer nunca deixa a vida acima do máximo.
        """
        old_max = self.max_health
        self.modifiers = modifiers
        self._effective_weapons = self._derive_weapons()
        self.health = min(self.max_health, self.health + max(0.0, self.max_health - old_max))

    @property
    def radius(self) -> float:
        return RADIUS

    @property
    def max_health(self) -> float:
        return MAX_HEALTH + self.modifiers.max_health_bonus

    @property
    def speed(self) -> float:
        return SPEED * self.modifiers.speed_multiplier

    @property
    def weapon(self) -> WeaponDef:
        """Arma ativa, já com os modificadores aplicados."""
        return self._effective_weapons[self.weapon_slot]

    @property
    def can_fire(self) -> bool:
        return self._cooldowns[self.weapon_slot] <= 0.0

    @property
    def alive(self) -> bool:
        return self.health > 0

    def take_damage(self, amount: float) -> None:
        self.health = max(0.0, self.health - amount)

    def apply(self, command: Command, dt: float) -> None:
        if isinstance(command, Move) and command.direction.length_squared() > 0:
            direction = command.direction.normalize()
            self.position += direction * self.speed * dt
            self.orientation = direction
        elif isinstance(command, Shoot) and self.can_fire:
            self._cooldowns[self.weapon_slot] = self.weapon.cooldown
        elif isinstance(command, SwitchWeapon) and 0 <= command.slot < len(self.weapons):
            self.weapon_slot = command.slot

    def update(self, dt: float) -> None:
        self._cooldowns = [max(0.0, c - dt) for c in self._cooldowns]
        regen = self.modifiers.regen_per_second
        if regen > 0 and self.alive:
            self.health = min(self.max_health, self.health + regen * dt)
