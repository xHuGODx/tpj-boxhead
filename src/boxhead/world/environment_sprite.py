"""Adaptador do ambiente (chão, paredes, obstáculos, decorações)."""

from __future__ import annotations

import pygame

from boxhead.core.catalog import SpriteSheet, catalog


class EnvironmentSprite:
    def __init__(self) -> None:
        cat = catalog()
        self.floor_sheet: SpriteSheet = cat.sheet("environment/floor_tiles.png")
        self.wall_sheet: SpriteSheet = cat.sheet("environment/walls.png")
        self.obstacle_sheet: SpriteSheet = cat.sheet("environment/obstacles.png")
        self.decoration_sheet: SpriteSheet = cat.sheet("environment/decorations.png")

        self.floors: list[pygame.Surface] = self.floor_sheet.animation().frames
        self.walls: list[pygame.Surface] = [
            frame for row in self.wall_sheet.frames for frame in row
        ]
        self.obstacles: list[pygame.Surface] = self.obstacle_sheet.animation().frames
        self.decorations: list[pygame.Surface] = self.decoration_sheet.animation().frames

    def floor_at(
        self, tile_x: int, tile_y: int, allowed: tuple[int, ...] | None = None
    ) -> pygame.Surface:
        """Escolhe um tile determinístico; restrito aos índices permitidos."""
        if not self.floors:
            return pygame.Surface((64, 64))
        if allowed:
            idx = allowed[(tile_x + tile_y) % len(allowed)]
        else:
            idx = (tile_x + tile_y) % len(self.floors)
        return self.floors[idx]

    def wall_for(self, index: int) -> pygame.Surface:
        return self.walls[index % len(self.walls)]

    def obstacle_for(self, index: int) -> pygame.Surface:
        return self.obstacles[index % len(self.obstacles)]

    def decoration_for(self, index: int) -> pygame.Surface:
        return self.decorations[index % len(self.decorations)]
