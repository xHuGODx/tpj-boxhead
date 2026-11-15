"""Comandos: intenções traduzidas do input SDL antes de chegar ao mundo."""

from __future__ import annotations

from dataclasses import dataclass

from pygame import Vector2


@dataclass(frozen=True)
class Command:
    """Intenção abstrata; não conhece teclas SDL nem entidades concretas."""


@dataclass(frozen=True)
class Move(Command):
    direction: Vector2  


@dataclass(frozen=True)
class Shoot(Command):
    pass


@dataclass(frozen=True)
class SwitchWeapon(Command):
    slot: int  # 0..2