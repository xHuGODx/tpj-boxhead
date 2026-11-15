"""Jogador: posição, orientação persistente e cooldown de disparo."""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Vector2

from boxhead.core.commands import Command, Move, Shoot, SwitchWeapon

SPEED = 220.0
FIRE_COOLDOWN = 0.25
RADIUS = 14


@dataclass
class Player:
    position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    orientation: Vector2 = field(default_factory=lambda: Vector2(0, 1))
    health: int = 100
    weapon_slot: int = 0
    _cooldown: float = 0.0

    @property
    def radius(self) -> float:
        return RADIUS

    @property
    def can_fire(self) -> bool:
        return self._cooldown <= 0.0

    def apply(self, command: Command, dt: float) -> None:
        if isinstance(command, Move) and command.direction.length_squared() > 0:
            direction = command.direction.normalize()
            self.position += direction * SPEED * dt
            self.orientation = direction
        elif isinstance(command, Shoot) and self.can_fire:
            self._cooldown = FIRE_COOLDOWN
        elif isinstance(command, SwitchWeapon) and 0 <= command.slot <= 2:
            self.weapon_slot = command.slot

    def update(self, dt: float) -> None:
        if self._cooldown > 0:
            self._cooldown = max(0.0, self._cooldown - dt)