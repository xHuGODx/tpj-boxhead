"""Mundo: limites, obstáculos e jogador; não conhece Surface."""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Rect, Vector2

from boxhead.core.commands import Command
from boxhead.core.geometry import circle_aabb
from boxhead.world.player import Player


@dataclass
class World:
    bounds: Rect = field(default_factory=lambda: Rect(-600, -400, 1200, 800))
    obstacles: list[Rect] = field(default_factory=list)
    player: Player = field(default_factory=Player)

    def apply(self, command: Command, dt: float) -> None:
        self.player.apply(command, dt)
        self._clamp_player()

    def update(self, dt: float) -> None:
        self.player.update(dt)

    def _clamp_player(self) -> None:
        p = self.player
        p.position.x = max(self.bounds.left + p.radius,
                           min(p.position.x, self.bounds.right - p.radius))
        p.position.y = max(self.bounds.top + p.radius,
                           min(p.position.y, self.bounds.bottom - p.radius))
        for obstacle in self.obstacles:
            contact = circle_aabb(p.position, p.radius, obstacle)
            if contact:
                p.position += contact.normal * contact.penetration