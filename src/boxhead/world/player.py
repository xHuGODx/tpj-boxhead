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
BASE_ATTACK_DAMAGE = 100.0
BASE_ATTACK_SPEED = 1.0


@dataclass
class Player:
    position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    orientation: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    health: float = MAX_HEALTH
    weapon_slot: int = 0
    weapons: tuple[WeaponDef, ...] = WEAPONS  # definições base, partilhadas e imutáveis
    modifiers: Modifiers = field(default_factory=Modifiers)
    owned_weapons: tuple[str, ...] = ("Pistol",)
    temporary_move: float = 0.0
    temporary_as: float = 0.0
    revivals_used: int = 0
    _cooldowns: list[float] = field(init=False, repr=False)
    _effective_weapons: tuple[WeaponDef, ...] = field(init=False, repr=False)
    arsenal: Arsenal = field(init=False)

    def __post_init__(self) -> None:
        # Um cooldown por arma: trocar de arma não permite contornar a cadência.
        self._cooldowns = [0.0] * len(self.weapons)
        self._effective_weapons = self._derive_weapons()
        if self.weapons[self.weapon_slot].name not in self.owned_weapons:
            self.weapon_slot = next(i for i, w in enumerate(self.weapons)
                                    if w.name in self.owned_weapons)
        selected = self.weapons[self.weapon_slot].name
        self.arsenal = Arsenal(self.weapons, (selected,))
        self.health = min(self.health, self.max_health)

    def _derive_weapons(self) -> tuple[WeaponDef, ...]:
        return tuple(derive_weapon(w, self.modifiers.for_weapon(w.name),
                                   self.attack_damage, self.attack_speed) for w in self.weapons)

    @property
    def attack_damage(self) -> float:
        return (BASE_ATTACK_DAMAGE + self.modifiers.attack_damage_bonus) * (1 + .15 * self.modifiers.siege_stacks)

    @property
    def attack_speed(self) -> float:
        movement = self.modifiers.speed_multiplier - 1 + self.temporary_move
        conversion = .5 * movement if self.modifiers.slipstream_feed else 0
        return BASE_ATTACK_SPEED + self.modifiers.attack_speed_bonus + self.temporary_as + conversion

    @property
    def size_multiplier(self) -> float:
        return 1 + .05 * self.modifiers.siege_stacks

    @property
    def crit_multiplier(self) -> float:
        return 2 + self.modifiers.crit_damage_bonus + .5 * max(0, self.modifiers.crit_chance - 1)

    @property
    def revivals_left(self) -> int:
        return max(0, self.modifiers.last_spark - self.revivals_used)

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
        return RADIUS * self.size_multiplier

    @property
    def max_health(self) -> float:
        return (MAX_HEALTH + self.modifiers.max_health_bonus) * (1 + .30 * self.modifiers.siege_stacks)

    @property
    def speed(self) -> float:
        return SPEED * max(0.1, self.modifiers.speed_multiplier + self.temporary_move)

    @property
    def weapon(self) -> WeaponDef:
        """Arma ativa, já com os modificadores aplicados."""
        return derive_weapon(self.weapons[self.weapon_slot],
                             self.modifiers.for_weapon(self.weapons[self.weapon_slot].name),
                             self.attack_damage, self.attack_speed)

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
        if self.alive:
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
        self._cooldowns[self.weapon_slot] += weapon.cooldown
        return weapon

    def update(self, dt: float) -> None:
        regen = self.modifiers.regen_per_second
        if regen > 0 and self.alive:
            self.health = min(self.max_health, self.health + regen * dt)
