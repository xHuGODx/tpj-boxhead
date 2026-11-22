"""Escolha de augment ao subir de nível: o mundo fica parado por baixo.

Este estado só desenha a partida congelada (nada avança aqui: nem movimento, tiros,
spawns, cooldowns ou relógio) e devolve a escolha ao `App`, que aplica o augment e
abre a escolha seguinte, se houver mais níveis na fila, ou retoma a partida.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.world.augments import Augment, Offer, Rarity
from boxhead.world.world import World

CARD_SIZE = (290, 320)
CARD_GAP = 28
LOCKOUT_SECONDS = 0.4  
RARITY_LABEL = {
    Rarity.GRAY: "CINZENTO",
    Rarity.GOLD: "DOURADO",
    Rarity.PRISMATIC: "PRISMÁTICO",
}
RARITY_COLOR = {
    Rarity.GRAY: (170, 176, 186),
    Rarity.GOLD: (235, 190, 70),
    Rarity.PRISMATIC: (190, 120, 255),
}
_NUMBER_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)
HINT = "1/2/3 ou clique para escolher · setas e Enter também funcionam"


def stacks_label(have: int, max_stacks: int) -> str:
    return f"Acumulação: {have} -> {have + 1} (máx. {max_stacks})"


def wrap_text(font: pygame.font.Font, text: str, width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] <= width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class AugmentSelectState(State):
    def __init__(
        self,
        resume_target: State,
        world: World,
        offer: Offer,
        on_choose: Callable[[Augment], None],
    ) -> None:
        self._resume_target = resume_target
        self._world = world
        self._offer = offer
        self._on_choose = on_choose
        self._cursor = 0
        self._lockout = LOCKOUT_SECONDS
        self._overlay: pygame.Surface | None = None

    @property
    def offer(self) -> Offer:
        return self._offer

    @property
    def locked(self) -> bool:
        return self._lockout > 0

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 56)
        self._name = pygame.font.Font(None, 32)
        self._body = pygame.font.Font(None, 26)
        self._small = pygame.font.Font(None, 22)

    # ------------------------------------------------------------------ layout / input

    def _card_rects(self, surface_size: tuple[int, int]) -> list[pygame.Rect]:
        count = len(self._offer.choices)
        width, height = CARD_SIZE
        total = count * width + (count - 1) * CARD_GAP
        left = (surface_size[0] - total) // 2
        top = (surface_size[1] - height) // 2 + 30
        return [
            pygame.Rect(left + i * (width + CARD_GAP), top, width, height) for i in range(count)
        ]

    def _choose(self, index: int) -> None:
        if self.locked or not 0 <= index < len(self._offer.choices):
            return
        self._on_choose(self._offer.choices[index])

    def handle_event(self, event: pygame.event.Event) -> None:
        count = len(self._offer.choices)
        if event.type == pygame.KEYDOWN:
            if event.key in _NUMBER_KEYS[:count]:
                self._choose(_NUMBER_KEYS.index(event.key))
            elif event.key == pygame.K_LEFT:
                self._cursor = (self._cursor - 1) % count
            elif event.key == pygame.K_RIGHT:
                self._cursor = (self._cursor + 1) % count
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):  
                self._choose(self._cursor)
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            size = pygame.display.get_surface().get_size()
            for index, rect in enumerate(self._card_rects(size)):
                if rect.collidepoint(event.pos):
                    self._cursor = index
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._choose(index)
                    break

    def update(self, dt: float) -> None:
        self._lockout = max(
            0.0, self._lockout - dt
        )  


    def draw(self, surface: pygame.Surface) -> None:
        self._resume_target.draw(surface)
        size = surface.get_size()
        if self._overlay is None or self._overlay.get_size() != size:
            self._overlay = pygame.Surface(size, pygame.SRCALPHA)
            self._overlay.fill((0, 0, 0, 170))
        surface.blit(self._overlay, (0, 0))

        progression = self._world.progression
        title = self._title.render(f"NÍVEL {progression.level}", True, (255, 255, 255))
        rects = self._card_rects(size)
        top = rects[0].top
        surface.blit(title, title.get_rect(midbottom=(size[0] // 2, top - 40)))
        queued = progression.pending_choices - 1
        subtitle = "Escolhe um augment" + (
            f"  ·  +{queued} escolha(s) em fila" if queued > 0 else ""
        )
        sub = self._body.render(subtitle, True, (200, 206, 216))
        surface.blit(sub, sub.get_rect(midbottom=(size[0] // 2, top - 12)))

        for index, (augment, rect) in enumerate(zip(self._offer.choices, rects, strict=True)):
            self._draw_card(surface, augment, rect, index)

        text = self._small.render(HINT, True, (153, 163, 176))
        surface.blit(text, text.get_rect(midtop=(size[0] // 2, rects[0].bottom + 18)))

    def _draw_card(self, surface: pygame.Surface, augment: Augment, rect: pygame.Rect, index: int):
        color = RARITY_COLOR[augment.rarity]
        selected = index == self._cursor
        dim = self.locked
        pygame.draw.rect(surface, (28, 32, 42), rect, border_radius=10)
        border = color if not dim else tuple(c // 2 for c in color)
        pygame.draw.rect(surface, border, rect, 4 if selected else 2, border_radius=10)

        key = self._title.render(str(index + 1), True, color)
        surface.blit(key, (rect.x + 16, rect.y + 12))
        tag = self._small.render(RARITY_LABEL[augment.rarity], True, color)
        surface.blit(tag, tag.get_rect(topright=(rect.right - 16, rect.y + 20)))

        y = rect.y + 80
        for line in wrap_text(self._name, augment.name, rect.width - 32):
            surface.blit(self._name.render(line, True, (255, 255, 255)), (rect.x + 16, y))
            y += 32
        y += 8
        for line in wrap_text(self._body, augment.description, rect.width - 32):
            surface.blit(self._body.render(line, True, (205, 211, 221)), (rect.x + 16, y))
            y += 26

        have = self._world.inventory.stacks(augment.id)
        text = self._small.render(stacks_label(have, augment.max_stacks), True, (153, 163, 176))
        surface.blit(text, (rect.x + 16, rect.bottom - 32))
