"""Fim de partida: resumo e opções de repetir ou menu."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.world.result import RunResult

HINT = "WASD select · SPACE confirm · R retry · M/ESC menu"


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
        self._cursor = 0
        self._down_keys: set[int] = set()

    def enter(self) -> None:
        held = pygame.key.get_pressed()
        self._down_keys = {key for key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) if held[key]}
        self._title = pygame.font.Font(None, 80)
        self._body = pygame.font.Font(None, 32)
        self._small = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYUP:
            self._down_keys.discard(event.key)
            return
        if event.type == pygame.KEYDOWN:
            if getattr(event, "repeat", False) or event.key in self._down_keys:
                return
            self._down_keys.add(event.key)
            if event.key == pygame.K_r:
                self._on_retry()
            elif event.key in (pygame.K_ESCAPE, pygame.K_m):
                self._on_menu()
            elif event.key in (pygame.K_w, pygame.K_a, pygame.K_UP, pygame.K_LEFT,
                               pygame.K_s, pygame.K_d, pygame.K_DOWN, pygame.K_RIGHT):
                self._cursor = 1 - self._cursor
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                (self._on_retry if self._cursor == 0 else self._on_menu)()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        w, h = surface.get_size()
        title = self._title.render("GAME OVER", True, (235, 77, 76))
        surface.blit(title, title.get_rect(center=(w // 2, h // 2 - 110)))
        stats = self._result
        lines = [
            f"Map: {stats.map_name}",
            f"Round: {stats.round}",
            f"Level: {stats.level}",
            f"Kills: {stats.kills}",
            f"Time: {stats.elapsed:.1f}s",
            f"Coins: {stats.coins}"
            + (f" (balance: {self._balance})" if self._balance is not None else ""),
            ("> " if self._cursor == 0 else "") + "Retry",
            ("> " if self._cursor == 1 else "") + "Main menu",
        ]
        if self._notice:
            lines.insert(-2, self._notice)
        for i, line in enumerate(lines):
            color = (255, 220, 120) if line.startswith("> ") else (225, 230, 237)
            text = self._body.render(line, True, color)
            surface.blit(text, text.get_rect(center=(w // 2, h // 2 - 30 + i * 38)))
        hint = self._small.render(HINT, True, (153, 163, 176))
        surface.blit(hint, hint.get_rect(midbottom=(w // 2, h - 16)))
