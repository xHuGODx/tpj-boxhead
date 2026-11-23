"""Jogador: posição, orientação persistente, vida e armas com cooldown próprio.

Os valores efetivos (velocidade, vida máxima, armas) são derivados da base e dos
`Modifiers` atuais; a base nunca é alterada.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Vector2

from boxhead.core.commands import Command, Move, SwitchWeapon
from boxhead.world.attributes import Modifiers, derive_weapon
from boxhead.world.weapons import WEAPONS, WeaponDef
from boxhead.world.arsenal import Arsenal

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
    arsenal: Arsenal = field(init=False)

    def __post_init__(self) -> None:
        # Um cooldown por arma: trocar de arma não permite contornar a cadência.
        self._cooldowns = [0.0] * len(self.weapons)
        self._effective_weapons = self._derive_weapons()
        self.arsenal = Arsenal(self.weapons)
        if not self.arsenal.is_unlocked(self.weapons[self.weapon_slot].name):
            self.weapon_slot = next(i for i, w in enumerate(self.weapons)
                                    if self.arsenal.is_unlocked(w.name))
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
        return SPEED * max(0.1, min(3.0, self.modifiers.speed_multiplier))

    @property
    def weapon(self) -> WeaponDef:
        """Arma ativa, já com os modificadores aplicados."""
        return self._effective_weapons[self.weapon_slot]

    @property
    def can_fire(self) -> bool:
        return self._cooldowns[self.weapon_slot] <= 0.0 and self.ammo > 0

    @property
    def ammo(self) -> int:
        return self.arsenal.ammo(self.weapon.name)

    @property
    def available_weapons(self) -> tuple[WeaponDef, ...]:
        return tuple(w for w in self.weapons if self.arsenal.is_unlocked(w.name))

    @property
    def cooldown_ratio(self) -> float:
        return min(1.0, self._cooldowns[self.weapon_slot] / self.weapon.cooldown)

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
        elif (isinstance(command, SwitchWeapon) and 0 <= command.slot < len(self.weapons)
              and self.arsenal.is_unlocked(self.weapons[command.slot].name)):
            self.weapon_slot = command.slot

    def try_fire(self) -> WeaponDef | None:
        if not self.alive or not self.can_fire:
            return None
        weapon = self.weapon
        if not self.arsenal.consume(weapon.name):
            return None
        self._cooldowns[self.weapon_slot] = weapon.cooldown
        return weapon

    def update(self, dt: float) -> None:
        self._cooldowns = [max(0.0, c - dt) for c in self._cooldowns]
        regen = self.modifiers.regen_per_second
        if regen > 0 and self.alive:
            self.health = min(self.max_health, self.health + regen * dt)
