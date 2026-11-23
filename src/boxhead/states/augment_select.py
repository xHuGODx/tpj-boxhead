"""Escolha de augment ao subir de nível: o mundo fica parado por baixo.

Este estado só desenha a partida congelada (nada avança aqui: nem movimento, tiros,
spawns, cooldowns ou relógio) e devolve a escolha ao `App`, que aplica o augment e
abre a escolha seguinte, se houver mais níveis na fila, ou retoma a partida.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.presentation.augment_cards import AugmentCards
from boxhead.world.augments import Augment, Offer
from boxhead.world.world import World

LOCKOUT_SECONDS = 0.4
_NUMBER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)


class AugmentSelectState(State):
    def __init__(
        self,
        resume_target: State,
        world: World,
        offer: Offer,
        on_choose: Callable[[Augment], None],
        on_pause: Callable[[State], None] | None = None,
    ) -> None:
        self._resume_target = resume_target
        self._world = world
        self._offer = offer
        self._on_choose = on_choose
        self._on_pause = on_pause
        self._chosen = False
        self._down_keys: set[int] = set()
        self._mouse_held = False
        if not 1 <= len(offer.choices) <= 3:
            raise ValueError("oferta sem escolhas ou com demasiadas opções")
        self._cursor = 0
        self._surface_size = (1100, 700)
        self._lockout = LOCKOUT_SECONDS
        self._overlay: pygame.Surface | None = None
        self._cards: AugmentCards | None = None

    @property
    def offer(self) -> Offer:
        return self._offer

    @property
    def locked(self) -> bool:
        return self._lockout > 0

    def enter(self) -> None:
        held = pygame.key.get_pressed()
        self._down_keys = {key for key in (*_NUMBER_KEYS, pygame.K_RETURN, pygame.K_KP_ENTER) if held[key]}
        self._mouse_held = pygame.mouse.get_pressed()[0]
        self._lockout = LOCKOUT_SECONDS
        if self._cards is None:
            self._cards = AugmentCards()

    def _card_rects(self, surface_size: tuple[int, int]) -> list[pygame.Rect]:
        assert self._cards is not None
        return self._cards.rects(surface_size, len(self._offer.choices))

    def _choose(self, index: int) -> None:
        if self._chosen or self.locked or not 0 <= index < len(self._offer.choices):
            return
        self._chosen = True
        self._on_choose(self._offer.choices[index])

    def handle_event(self, event: pygame.event.Event) -> None:
        count = len(self._offer.choices)
        if event.type == pygame.KEYUP:
            self._down_keys.discard(event.key)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._mouse_held = False
        elif event.type == pygame.KEYDOWN:
            if getattr(event, "repeat", False) or event.key in self._down_keys:
                return
            self._down_keys.add(event.key)
            if event.key == pygame.K_ESCAPE and self._on_pause is not None:
                self._on_pause(self)
            elif event.key in _NUMBER_KEYS[:count]:
                self._choose(_NUMBER_KEYS.index(event.key))
            elif event.key == pygame.K_LEFT:
                self._cursor = (self._cursor - 1) % count
            elif event.key == pygame.K_RIGHT:
                self._cursor = (self._cursor + 1) % count
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):  
                self._choose(self._cursor)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            size = self._surface_size
            for index, rect in enumerate(self._card_rects(size)):
                if rect.collidepoint(event.pos):
                    self._cursor = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if not self._mouse_held:
                            self._mouse_held = True
                            self._choose(index)
                    break

    def update(self, dt: float) -> None:
        self._lockout = max(
            0.0, self._lockout - dt
        )  


    def draw(self, surface: pygame.Surface) -> None:
        self._resume_target.draw(surface)
        size = surface.get_size()
        self._surface_size = size
        if self._overlay is None or self._overlay.get_size() != size:
            self._overlay = pygame.Surface(size, pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 170))
        surface.blit(self._overlay, (0, 0))

        assert self._cards is not None
        self._cards.draw(surface, self._world, self._offer, self._cursor, self.locked)
