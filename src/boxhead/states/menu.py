"""Ecrã inicial: jogar, abrir a loja ou sair."""

from collections.abc import Callable

import pygame

from boxhead.core.state import State

HINT = "WASD / arrows navigate · SPACE / ENTER select · F11 fullscreen · ESC quit"


class MenuState(State):
    def __init__(
        self,
        on_start: Callable[[], None],
        on_quit: Callable[[], None],
        on_shop: Callable[[], None] | None = None,
        balance: int | None = None,
        notice: str | None = None,
        on_fullscreen: Callable[[], None] | None = None,
        fullscreen: Callable[[], bool] | None = None,
    ) -> None:
        self._on_quit = on_quit
        self._balance = balance
        self._notice = notice
        self._items: list[tuple[str | Callable[[], str], Callable[[], None]]] = [("Play", on_start)]
        if on_shop is not None:
            self._items.append(("Shop", on_shop))
        if on_fullscreen is not None:
            is_fullscreen = fullscreen or (lambda: False)
            self._items.append((lambda: "Fullscreen: " + ("On" if is_fullscreen() else "Off"), on_fullscreen))
        self._items.append(("Quit", on_quit))
        self._cursor = 0

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def labels(self) -> list[str]:
        return [label() if callable(label) else label for label, _ in self._items]

    def enter(self) -> None:
        self._title = pygame.font.Font(None, 100)
        self._body = pygame.font.Font(None, 38)
        self._small = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._on_quit()
        elif event.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
            self._cursor = (self._cursor - 1) % len(self._items)
        elif event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
            self._cursor = (self._cursor + 1) % len(self._items)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._items[self._cursor][1]()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        width, height = surface.get_size()
        center_x = width // 2
        subtitle = self._small.render("GAME PROGRAMMING TOPICS", True, (153, 163, 176))
        surface.blit(subtitle, subtitle.get_rect(center=(center_x, height // 2 - 160)))
        title = self._title.render("BOXHEAD", True, (235, 77, 76))
        surface.blit(title, title.get_rect(center=(center_x, height // 2 - 80)))
        for index, label in enumerate(self.labels):
            selected = index == self._cursor
            color = (255, 220, 120) if selected else (225, 230, 237)
            text = self._body.render(f"> {label}" if selected else label, True, color)
            surface.blit(text, text.get_rect(center=(center_x, height // 2 + 20 + index * 48)))
        hint = self._small.render(HINT, True, (153, 163, 176))
        surface.blit(hint, hint.get_rect(center=(center_x, height - 40)))
        if self._balance is not None:
            coins = self._body.render(f"Coins: {self._balance}", True, (255, 220, 120))
            surface.blit(coins, coins.get_rect(topright=(width - 24, 20)))
        if self._notice:
            warning = self._small.render(self._notice, True, (240, 150, 100))
            surface.blit(warning, warning.get_rect(center=(center_x, height - 80)))
