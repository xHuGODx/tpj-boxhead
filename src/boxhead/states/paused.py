"""Pausa: preserva a partida e não avança o relógio."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.presentation.build_panel import BuildPanel

HINT = "WASD select · SPACE / ENTER confirm · ESC resume · M menu"


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
        self._cursor = 0
        self._down_keys: set[int] = set()
        self._world = getattr(resume_target, 'world', getattr(resume_target, '_world', None))
        self._build_panel = None
        self._augment_index = 0

    def enter(self) -> None:
        held = pygame.key.get_pressed()
        self._down_keys = {key for key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) if held[key]}
        self._title = pygame.font.Font(None, 64)
        self._body = pygame.font.Font(None, 30)
        self._small = pygame.font.Font(None, 24)
        if self._world is not None and self._build_panel is None:
            self._build_panel = BuildPanel()

    def _scroll_augments(self, step):
        count = len(self._build_panel.owned(self._world)) if self._build_panel else 0
        self._augment_index = max(0,min(max(0,count-1), self._augment_index+step))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_augments(-event.y)
            return
        if event.type == pygame.KEYUP:
            self._down_keys.discard(event.key)
            return
        if event.type != pygame.KEYDOWN:
            return
        if getattr(event, "repeat", False) or event.key in self._down_keys:
            return
        self._down_keys.add(event.key)
        if event.key == pygame.K_ESCAPE:
            self._on_resume(self._resume_target)
        elif event.key == pygame.K_m:
            self._on_menu()
        elif self._build_panel and event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
            self._scroll_augments(-1 if event.key in (pygame.K_w,pygame.K_UP) else 1)
        elif event.key in (pygame.K_w, pygame.K_a, pygame.K_UP, pygame.K_LEFT,
                           pygame.K_s, pygame.K_d, pygame.K_DOWN, pygame.K_RIGHT):
            self._cursor = 1 - self._cursor
        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            if self._cursor == 0:
                self._on_resume(self._resume_target)
            else:
                self._on_menu()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        self._resume_target.draw(surface)  
        if self._build_panel is not None:
            self._build_panel.draw(surface,self._world,self._augment_index,self._cursor)
            return
        size = surface.get_size()
        if self._overlay is None or self._overlay.get_size() != size:
            self._overlay = pygame.Surface(size, pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 150))
        surface.blit(self._overlay, (0, 0))
        center = surface.get_rect().center
        title = self._title.render("PAUSED", True, (235, 77, 76))
        surface.blit(title, title.get_rect(center=(center[0], center[1] - 80)))
        for index, label in enumerate(("Resume", "Main menu")):
            selected = index == self._cursor
            text = self._body.render(("> " if selected else "") + label, True,
                                     (255, 220, 120) if selected else (225, 230, 237))
            surface.blit(text, text.get_rect(center=(center[0], center[1] + index * 42)))
        hint = self._small.render(HINT, True, (225, 230, 237))
        surface.blit(hint, hint.get_rect(center=(center[0], center[1] + 106)))
