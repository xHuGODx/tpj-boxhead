"""Definições imutáveis das armas (Type Object): dados, sem estado de instância.

Cooldowns pertencem ao `Player`; reservas/desbloqueios ao seu `Arsenal`. Aqui vivem
apenas valores partilhados, por isso todas as instâncias podem usar o mesmo objeto.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class WeaponDef:
    name: str
    damage: float  # por projétil
    cooldown: float  # segundos entre disparos
    pellets: int = 1
    spread_degrees: float = 0.0  # cone total; cada projétil sai num ângulo aleatório dentro dele
    projectile_speed: float = 900.0
    projectile_range: float = 700.0
    projectile_radius: float = 4.0
    color: tuple[int, int, int] = (255, 220, 120)
    unlock_round: int = 1
    starting_ammo: int = 60
    max_ammo: int = 180
    pickup_ammo: int = 18

    def __post_init__(self) -> None:
        values = (self.damage, self.cooldown, self.projectile_speed,
                  self.projectile_range, self.projectile_radius)
        if any(not isfinite(v) or v <= 0 for v in values):
            raise ValueError("weapon attributes must be positive and finite")
        if isinstance(self.pellets, bool) or not isinstance(self.pellets, int) or self.pellets < 1:
            raise ValueError("pellets must be a positive integer")
        if not isfinite(self.spread_degrees) or not 0 <= self.spread_degrees <= 360:
            raise ValueError("invalid spread")
        counts = (self.unlock_round, self.starting_ammo, self.max_ammo, self.pickup_ammo)
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in counts):
            raise ValueError("weapon unlock round and ammo counts must be positive integers")
        if self.starting_ammo > self.max_ammo:
            raise ValueError("starting ammo exceeds capacity")


PISTOL = WeaponDef(
    name="Pistol",
    damage=25,
    cooldown=0.35,
    projectile_speed=900,
    projectile_range=700,
)
SHOTGUN = WeaponDef(
    name="Shotgun",
    damage=12,
    cooldown=0.9,
    pellets=6,
    spread_degrees=24,
    projectile_speed=800,
    projectile_range=450,
    projectile_radius=3,
    color=(255, 170, 90),
    unlock_round=10,
    starting_ammo=24,
    max_ammo=72,
    pickup_ammo=8,
)
SMG = WeaponDef(
    name="SMG",
    damage=9,
    cooldown=0.09,
    spread_degrees=5,
    projectile_speed=950,
    projectile_range=650,
    projectile_radius=3,
    color=(140, 220, 255),
    unlock_round=5,
    starting_ammo=120,
    max_ammo=360,
    pickup_ammo=60,
)

# Ordem = teclas 1, 2, 3.
WEAPONS: tuple[WeaponDef, ...] = (PISTOL, SHOTGUN, SMG)
