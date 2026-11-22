"""Adaptador entre inimigos (domínio) e o catálogo de sprites.

Flyweight: os frames (Surfaces) vêm do catálogo e são partilhados por todos os
inimigos do mesmo tipo; cada inimigo só tem o seu `EnemyAnimator` (índice/tempo).
Enquanto a arte não existir, o catálogo devolve placeholders.
"""

from __future__ import annotations

import pygame

from boxhead.core.catalog import Animation, SpriteSheet, catalog
from boxhead.world.enemy import Enemy, EnemyDef
from boxhead.world.player_sprite import direction_name

_DIRECTIONS = ("down", "left", "right", "up")


class EnemyAnimator:
    """Estado de animação de um inimigo; os frames são partilhados (Flyweight)."""

    def __init__(self, sheets: dict[str, SpriteSheet]) -> None:
        self._animations = {
            visual: {d: sheet.animation(d) for d in _DIRECTIONS} for visual, sheet in sheets.items()
        }
        self._active: Animation = self._animations["walk"]["down"]

    def update(self, enemy: Enemy, dt: float) -> None:
        by_direction = self._animations.get(enemy.visual) or self._animations["walk"]
        anim = by_direction[direction_name(enemy.orientation)]
        if anim is not self._active:
            anim.reset()
            self._active = anim
        self._active.update(dt)

    @property
    def current(self) -> pygame.Surface:
        return self._active.current


class EnemySprite:
    """Carrega as spritesheets de um tipo de inimigo, segundo `EnemyDef.animations`."""

    def __init__(self, definition: EnemyDef) -> None:
        cat = catalog()
        self._sheets = {
            visual: cat.sheet(f"{definition.sprite_prefix}_{suffix}.png")
            for visual, suffix in definition.animations
        }

    def animator(self) -> EnemyAnimator:
        return EnemyAnimator(self._sheets)
