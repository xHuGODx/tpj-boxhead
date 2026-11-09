"""Ecrã inicial do scaffold. As funcionalidades estão no backlog."""

from collections.abc import Callable

import pygame

from boxhead.core.state import State


class MenuState(State):
    def __init__(self, on_quit: Callable[[], None]) -> None:
        self._on_quit = on_quit

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 100)
        self._body = pygame.font.Font(None, 30)
        self._small = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_quit()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        width, height = surface.get_size()
        lines = [
            (self._small, "TÓPICOS DE PROGRAMAÇÃO PARA JOGOS", (153, 163, 176), -120),
            (self._title, "BOXHEAD", (235, 77, 76), -50),
            (self._body, "Rondas infinitas. Augments. Evolução permanente.", (225, 230, 237), 35),
            (
                self._small,
                "Base do projeto pronta · Gameplay em desenvolvimento",
                (153, 163, 176),
                90,
            ),
            (self._small, "ESC para sair", (153, 163, 176), 160),
        ]
        for font, message, color, offset in lines:
            text = font.render(message, True, color)
            surface.blit(text, text.get_rect(center=(width // 2, height // 2 + offset)))
