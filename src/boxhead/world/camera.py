"""Câmara: conversão entre coordenadas do mundo e do ecrã."""

from __future__ import annotations

from pygame import Vector2


class Camera:
    def __init__(self, viewport: tuple[int, int]) -> None:
        self.viewport = Vector2(viewport)
        self.center = Vector2(0, 0)

    def follow(self, target: Vector2, smoothing: float = 0.15) -> None:
        self.center += (target - self.center) * smoothing

    def world_to_screen(self, point: Vector2) -> Vector2:
        return point - self.center + self.viewport / 2

    def screen_to_world(self, point: Vector2) -> Vector2:
        return point + self.center - self.viewport / 2