"""Pausa: preserva a partida e não avança o relógio."""

from __future__ import annotations

import pygame

from boxhead.core.state import State


class PausedState(State):
    def __init__(self, resume_target: State, on_quit: callable) -> None:
        self._resume_target = resume_target
        self._on_quit = on_quit

    def enter(self) -> None:
        self._font = pygame.font.Font(None, 64)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_quit(self._resume_target)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        text = self._font.render("PAUSA", True, (235, 77, 76))
        surface.blit(text, text.get_rect(center=surface.get_rect().center))