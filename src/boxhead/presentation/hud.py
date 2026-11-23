"""HUD: lê o mundo; nunca altera a partida."""
import math
import pygame
from boxhead.core.catalog import catalog
from boxhead.world.augments import Rarity
from boxhead.world.rounds import Phase
_TEXT = (225,230,237)
_MUTED = (153,163,176)
_ACCENT = (255,220,120)
RARITY_COLORS = {Rarity.GRAY:(170,176,186), Rarity.GOLD:(235,190,70), Rarity.PRISMATIC:(190,120,255)}

def round_label(director):
    return f"ROUND {director.round_number}" + (" · BOSS" if director.is_boss_round else "")

class HUD:
    def __init__(self):
        icons = catalog().sheet("ui/ui_icons_main.png").animation().frames
        self._icon_heart, self._icon_coin, self._icon_gem = icons[:3]
        self._font = pygame.font.Font(None, 28)
        self._font_big = pygame.font.Font(None, 44)
        self._weapon_icons = catalog().sheet("weapons/weapon_icons.png").animation().frames
        self._scaled = {}

    def _scale(self, image, size):
        key = (id(image), size)
        if key not in self._scaled:
            self._scaled[key] = pygame.transform.scale(image, size)
        return self._scaled[key]

    def _icon(self, image: pygame.Surface) -> pygame.Surface:
        return self._scale(image, (36, 36))

    def _draw_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(surface, (24, 28, 36), rect, border_radius=4)
        if ratio > 0:
            fill = pygame.Rect(rect.x, rect.y, max(4, int(rect.width * ratio)), rect.height)
            pygame.draw.rect(surface, color, fill, border_radius=4)
        pygame.draw.rect(surface, (90, 100, 115), rect, 1, border_radius=4)

    def draw(self, surface: pygame.Surface, world) -> None:
        self._world = world
        player, progression = world.player, world.progression
        bar_x = 16 + 36 + 10

        surface.blit(self._icon(self._icon_heart), (16, 14))
        health_bar = pygame.Rect(bar_x, 20, 190, 22)
        self._draw_bar(surface, health_bar, player.health / player.max_health, (220, 70, 70))
        hp_text = f"{math.ceil(player.health)}/{math.ceil(player.max_health)}"
        label = self._font.render(hp_text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=health_bar.center))

        surface.blit(self._icon(self._icon_gem), (16, 58))
        xp_bar = pygame.Rect(bar_x, 64, 190, 22)
        self._draw_bar(surface, xp_bar, progression.xp_ratio, (110, 190, 255))
        label = self._font.render(f"LV {progression.level}", True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=xp_bar.center))

        surface.blit(self._icon(self._icon_coin), (16, 102))
        coins = self._font.render(str(world.stats.coins), True, _TEXT)
        surface.blit(coins, (bar_x, 108))

        self._draw_owned_augments(surface)

        width = surface.get_width()
        director = world.director
        if director is not None:
            if director.phase is Phase.INTERMISSION:
                label = (
                    f"ROUND {director.round_number + 1} IN {max(0, director.intermission_left):.0f}"
                )
            else:
                label = round_label(director)
            text = self._font_big.render(label, True, _TEXT)
            surface.blit(text, text.get_rect(topright=(width - 16, 16)))
            remaining = world.alive_enemy_count + director.pending
            info = f"ENEMIES {remaining}   KILLS {world.stats.kills}"
            line = self._font.render(info, True, _MUTED)
            surface.blit(line, line.get_rect(topright=(width - 16, 64)))

        timer = self._font.render(f"{world.map.name} · {world.elapsed:.1f}s", True, _TEXT)
        surface.blit(timer, timer.get_rect(topright=(width - 16, 96)))
        cooldown = pygame.Rect(width // 2 - 100, surface.get_height() - 56, 200, 7)
        self._draw_bar(surface, cooldown, 1 - player.cooldown_ratio, (255, 220, 120))
        self._draw_boss_bar(surface)

        player = world.player
        cursor_x = surface.get_width() // 2 - 250
        for slot, weapon in enumerate(player.weapons):
            active = slot == player.weapon_slot
            color = _ACCENT if active else _MUTED
            label = self._font.render(f"{slot + 1} {weapon.name}", True, color)
            surface.blit(self._scale(self._weapon_icons[slot], (28,28)), (cursor_x-30, surface.get_height()-40))
            surface.blit(label, (cursor_x, surface.get_height() - 36))
            if active:
                pygame.draw.line(
                    surface,
                    color,
                    (cursor_x, surface.get_height() - 12),
                    (cursor_x + label.get_width(), surface.get_height() - 12),
                    2,
                )
            cursor_x += label.get_width() + 72

    def _draw_boss_bar(self, surface: pygame.Surface) -> None:
        boss = next((e for e in self._world.enemies if e.is_boss and e.alive), None)
        if boss is None:
            return
        rect = pygame.Rect(0, 0, 460, 20)
        rect.midtop = (surface.get_width() // 2, 18)
        self._draw_bar(surface, rect, boss.health / boss.max_health, (190, 90, 255))
        label = self._font.render("BOSS", True, (255, 255, 255))
        surface.blit(label, label.get_rect(midtop=(rect.centerx, rect.bottom + 4)))

    def _draw_owned_augments(self, surface: pygame.Surface) -> None:
        owned = list(self._world.inventory.owned())[-8:]
        y = surface.get_height() - 18 - 22 * len(owned)
        for augment, stacks in owned:
            suffix = f" x{stacks}" if stacks > 1 else ""
            text = self._font.render(f"{augment.name}{suffix}", True, RARITY_COLORS[augment.rarity])
            surface.blit(text, (16, y))
            y += 22
