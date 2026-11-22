"""Definições imutáveis das armas (Type Object): dados, sem estado de instância.

O estado de cada arma na partida (cooldown) pertence ao `Player`; aqui só vivem
os valores partilhados, por isso todas as instâncias podem apontar para o mesmo
objeto sem risco.
"""

from __future__ import annotations

from dataclasses import dataclass


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
)

# Ordem = teclas 1, 2, 3.
WEAPONS: tuple[WeaponDef, ...] = (PISTOL, SHOTGUN, SMG)
