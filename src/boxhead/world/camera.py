"""Câmara: conversão entre coordenadas do mundo e do ecrã."""

from __future__ import annotations

import math

from pygame import Vector2


class Camera:
    def __init__(self, viewport: tuple[int, int]) -> None:
        self.viewport = Vector2(viewport)
        self.center = Vector2(0, 0)

    def snap(self, target: Vector2) -> None:
        """Centra imediatamente, sem suavização (início de partida)."""
        self.center = Vector2(target)

    def follow(self, target: Vector2, dt: float, speed: float = 8.0) -> None:
        """Aproxima-se do alvo; o resultado não depende do frame rate."""
        factor = 1.0 - math.exp(-speed * dt)
        self.center += (target - self.center) * factor

    def world_to_screen(self, point: Vector2) -> Vector2:
        return point - self.center + self.viewport / 2

    def screen_to_world(self, point: Vector2) -> Vector2:
        return point + self.center - self.viewport / 2
