"""Fim de partida: resumo e opções de repetir ou menu."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.world.result import RunResult

HINT = "R — repetir · M/ESC — menu"


class GameOverState(State):
    def __init__(
        self,
        result: RunResult,
        on_retry: Callable[[], None],
        on_menu: Callable[[], None],
        balance: int | None = None,
        notice: str | None = None,
    ) -> None:
        self._notice = notice
        self._balance = balance
        self._result = result
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
        surface.blit(title, title.get_rect(center=(w // 2, h // 2 - 110)))
        stats = self._result
        lines = [
            f"Ronda: {stats.round}",
            f"Nível: {stats.level}",
            f"Mortes: {stats.kills}",
            f"Tempo: {stats.elapsed:.1f}s",
            f"Moeda: {stats.coins}"
            + (f" (saldo: {self._balance})" if self._balance is not None else ""),
            HINT,
        ]
        if self._notice:
            lines.insert(-1, self._notice)
        for i, line in enumerate(lines):
            color = (153, 163, 176) if i == len(lines) - 1 else (225, 230, 237)
            text = self._body.render(line, True, color)
            surface.blit(text, text.get_rect(center=(w // 2, h // 2 - 30 + i * 38)))
