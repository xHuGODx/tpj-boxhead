"""Pausa: preserva a partida e não avança o relógio."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State

HINT = "ESC — resume · M — menu"


class PausedState(State):
    """Mostra a partida congelada por baixo. ESC retoma; M abandona para o menu."""

    def __init__(
        self,
        resume_target: State,
        on_resume: Callable[[State], None],
        on_menu: Callable[[], None],
    ) -> None:
        self._resume_target = resume_target
        self._on_resume = on_resume
        self._on_menu = on_menu
        self._overlay: pygame.Surface | None = None

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 64)
        self._body = pygame.font.Font(None, 30)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._on_resume(self._resume_target)
        elif event.key == pygame.K_m:
            self._on_menu()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        self._resume_target.draw(surface)  
        size = surface.get_size()
        if self._overlay is None or self._overlay.get_size() != size:
            self._overlay = pygame.Surface(size, pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 150))
        surface.blit(self._overlay, (0, 0))
        center = surface.get_rect().center
        title = self._title.render("PAUSED", True, (235, 77, 76))
        surface.blit(title, title.get_rect(center=center))
        hint = self._body.render(HINT, True, (225, 230, 237))
        surface.blit(hint, hint.get_rect(center=(center[0], center[1] + 56)))
