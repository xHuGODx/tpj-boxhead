"""Adaptador entre o jogador (domínio) e o catálogo de sprites."""

from __future__ import annotations

import pygame

from boxhead.core.catalog import Animation, catalog


def direction_name(orientation: pygame.Vector2) -> str:
    """Orientação contínua → uma das 4 direções das spritesheets."""
    if orientation.length_squared() == 0:
        return "down"
    if abs(orientation.x) > abs(orientation.y):
        return "right" if orientation.x > 0 else "left"
    return "down" if orientation.y > 0 else "up"


class PlayerSprite:
    def __init__(self) -> None:
        cat = catalog()
        self._walk_sheet = cat.sheet("player/player_walk.png")
        self._idle_sheet = cat.sheet("player/player_idle.png")
        self._shoot_sheet = cat.sheet("player/player_shoot.png")
        self._shadow_sheet = cat.sheet("player/player_shadow.png")

        self._walk = {d: self._walk_sheet.animation(d) for d in ("down", "left", "right", "up")}
        self._idle = {d: self._idle_sheet.animation(d) for d in ("down", "left", "right", "up")}
        self._shoot = {d: self._shoot_sheet.animation(d) for d in ("down", "left", "right", "up")}
        shadow = self._shadow_sheet.animation().current
        self._shadow = shadow.subsurface(shadow.get_bounding_rect()).copy()

    @staticmethod
    def direction(orientation: pygame.Vector2) -> str:
        return direction_name(orientation)

    def for_state(self, *, moving: bool, shooting: bool, orientation: pygame.Vector2) -> Animation:
        d = self.direction(orientation)
        if shooting:
            return self._shoot[d]
        if moving:
            return self._walk[d]
        return self._idle[d]

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow
