"""Loja: compra melhorias permanentes com a moeda do perfil (só se compra aqui)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from boxhead.core.state import State
from boxhead.profile import Profile
from boxhead.core.catalog import catalog
from boxhead.presentation.sprites import SpritePainter
from boxhead.presentation.icons import shop_icon
from boxhead.shop import UPGRADES, PurchaseResult, UpgradeDef

HINT = "WASD / arrows select · SPACE / ENTER buy · ESC back"
MESSAGES = {
    PurchaseResult.BOUGHT: "Purchased!",
    PurchaseResult.INSUFFICIENT_FUNDS: "Not enough coins.",
    PurchaseResult.MAX_LEVEL: "Already at maximum level.",
    PurchaseResult.UNKNOWN: "Unknown upgrade.",
    PurchaseResult.SAVE_FAILED: "Could not save. Purchase cancelled.",
}


def cost_label(upgrade: UpgradeDef, level: int) -> str:
    if upgrade.weapon and level > 0:
        return "OWNED"
    return "MAX" if level >= upgrade.max_level else f"{upgrade.cost(level)} coins"


def level_label(upgrade: UpgradeDef, level: int) -> str:
    if upgrade.weapon:
        return "Permanent unlock"
    return f"Level {level}/{upgrade.max_level}"


class ShopState(State):
    def __init__(
        self,
        profile: Profile,
        on_back: Callable[[], None],
        purchase: Callable[[str], PurchaseResult],
        upgrades: tuple[UpgradeDef, ...] = UPGRADES,
    ) -> None:
        self._profile = profile
        self._on_back = on_back
        self._purchase_upgrade = purchase
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
        self._painter = SpritePainter(catalog())
        self._painter.prepare(["shop/shop_upgrades.png", "augments/augment_icons.png", "weapons/weapon_icons.png"])

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        count = len(self._upgrades)
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._on_back()
        elif event.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
            self._cursor = (self._cursor - 1) % count
        elif event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
            self._cursor = (self._cursor + 1) % count
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._purchase(self._upgrades[self._cursor])

    def _purchase(self, upgrade: UpgradeDef) -> None:
        result = self._purchase_upgrade(upgrade.id)
        self._message_ok = result is PurchaseResult.BOUGHT
        self._message = MESSAGES[result]

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        width, height = surface.get_size()
        title = self._title.render("SHOP", True, (235, 77, 76))
        surface.blit(title, title.get_rect(midtop=(width // 2, 40)))
        coins = self._body.render(f"Coins: {self._profile.balance}", True, (255, 220, 120))
        surface.blit(coins, coins.get_rect(midtop=(width // 2, 120)))

        row_width, row_height = 640, 86
        left = (width - row_width) // 2
        visible_count = max(1, (height - 310) // (row_height + 14))
        first = min(max(0, self._cursor - visible_count + 1),
                    max(0, len(self._upgrades) - visible_count))
        for index in range(first, min(len(self._upgrades), first + visible_count)):
            upgrade = self._upgrades[index]
            level = self._profile.level(upgrade.id)
            rect = pygame.Rect(left, 190 + (index - first) * (row_height + 14), row_width, row_height)
            selected = index == self._cursor
            maxed = level >= upgrade.max_level
            pygame.draw.rect(surface, (28, 32, 42), rect, border_radius=10)
            border = (255, 220, 120) if selected else (70, 78, 92)
            pygame.draw.rect(surface, border, rect, 3 if selected else 1, border_radius=10)
            icon_key, icon = shop_icon(upgrade.id)
            self._painter.blit(surface, icon_key, (rect.x-32, rect.centery), (48,48), icon)
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
        position = self._small.render(f"{self._cursor + 1} / {len(self._upgrades)}", True, (153, 163, 176))
        surface.blit(position, position.get_rect(topright=(left + row_width, 160)))
