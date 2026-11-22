"""Loja: compra melhorias permanentes com a moeda do perfil (só se compra aqui)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.profile import Profile
from boxhead.shop import UPGRADES, PurchaseResult, UpgradeDef, buy

HINT = "W/S ou setas para escolher · ENTER compra · ESC volta"
MESSAGES = {
    PurchaseResult.BOUGHT: "Comprado!",
    PurchaseResult.INSUFFICIENT_FUNDS: "Moeda insuficiente.",
    PurchaseResult.MAX_LEVEL: "Já está no nível máximo.",
    PurchaseResult.UNKNOWN: "Melhoria desconhecida.",
}
SAVE_FAILED = "Comprado, mas não foi possível guardar o perfil."


def cost_label(upgrade: UpgradeDef, level: int) -> str:
    return "MÁX" if level >= upgrade.max_level else f"{upgrade.cost(level)} moeda"


def level_label(upgrade: UpgradeDef, level: int) -> str:
    return f"Nível {level}/{upgrade.max_level}"


class ShopState(State):
    def __init__(
        self,
        profile: Profile,
        on_back: Callable[[], None],
        save: Callable[[], bool],
        upgrades: tuple[UpgradeDef, ...] = UPGRADES,
    ) -> None:
        self._profile = profile
        self._on_back = on_back
        self._save = save  # devolve False se não conseguiu guardar
        self._upgrades = upgrades
        self._cursor = 0
        self._message = ""
        self._message_ok = True

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def message(self) -> str:
        return self._message

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 72)
        self._body = pygame.font.Font(None, 34)
        self._small = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        count = len(self._upgrades)
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._on_back()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % count
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % count
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._purchase(self._upgrades[self._cursor])

    def _purchase(self, upgrade: UpgradeDef) -> None:
        result = buy(self._profile, upgrade.id, self._upgrades)
        self._message_ok = result is PurchaseResult.BOUGHT
        self._message = MESSAGES[result]
        if result is PurchaseResult.BOUGHT and not self._save():
            self._message, self._message_ok = SAVE_FAILED, False

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        width, height = surface.get_size()
        title = self._title.render("LOJA", True, (235, 77, 76))
        surface.blit(title, title.get_rect(midtop=(width // 2, 40)))
        coins = self._body.render(f"Moeda: {self._profile.balance}", True, (255, 220, 120))
        surface.blit(coins, coins.get_rect(midtop=(width // 2, 120)))

        row_width, row_height = 640, 86
        left = (width - row_width) // 2
        for index, upgrade in enumerate(self._upgrades):
            level = self._profile.level(upgrade.id)
            rect = pygame.Rect(left, 190 + index * (row_height + 14), row_width, row_height)
            selected = index == self._cursor
            maxed = level >= upgrade.max_level
            pygame.draw.rect(surface, (28, 32, 42), rect, border_radius=10)
            border = (255, 220, 120) if selected else (70, 78, 92)
            pygame.draw.rect(surface, border, rect, 3 if selected else 1, border_radius=10)
            name = self._body.render(upgrade.name, True, (255, 255, 255))
            surface.blit(name, (rect.x + 18, rect.y + 12))
            desc = self._small.render(upgrade.description, True, (180, 188, 200))
            surface.blit(desc, (rect.x + 18, rect.y + 50))
            lvl = self._small.render(level_label(upgrade, level), True, (153, 163, 176))
            surface.blit(lvl, lvl.get_rect(topright=(rect.right - 18, rect.y + 14)))
            price_color = (120, 200, 140) if maxed else (255, 220, 120)
            affordable = maxed or self._profile.balance >= upgrade.cost(level)
            if not affordable:
                price_color = (200, 110, 100)
            price = self._body.render(cost_label(upgrade, level), True, price_color)
            surface.blit(price, price.get_rect(bottomright=(rect.right - 18, rect.bottom - 10)))

        if self._message:
            color = (120, 200, 140) if self._message_ok else (240, 150, 100)
            text = self._body.render(self._message, True, color)
            surface.blit(text, text.get_rect(center=(width // 2, height - 90)))
        hint = self._small.render(HINT, True, (153, 163, 176))
        surface.blit(hint, hint.get_rect(center=(width // 2, height - 40)))
