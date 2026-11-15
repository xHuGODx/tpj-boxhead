"""Fim de partida: resumo e opções de repetir ou menu."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.world.world import World


class GameOverState(State):
    def __init__(self, world: World, elapsed: float,
                 on_retry: Callable[[], None], on_menu: Callable[[], None]) -> None:
        self._world = world
        self._elapsed = elapsed
        self._on_retry = on_retry
        self._on_menu = on_menu

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 80)
        self._body = pygame.font.Font(None, 32)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._on_retry()
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                self._on_menu()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        w, h = surface.get_size()
        title = self._title.render("GAME OVER", True, (235, 77, 76))
        surface.blit(title, title.get_rect(center=(w // 2, h // 2 - 60)))
        lines = [
            f"Tempo: {self._elapsed:.1f}s",
            f"Vida: {self._world.player.health}",
            "R — repetir · M/ESC — menu",
        ]
        for i, line in enumerate(lines):
            text = self._body.render(line, True, (225, 230, 237))
            surface.blit(text, text.get_rect(center=(w // 2, h // 2 + 20 + i * 40)))