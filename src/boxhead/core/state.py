"""State: o gestor controla o ciclo de vida do estado ativo."""

from abc import ABC, abstractmethod

import pygame


class State(ABC):
    def enter(self) -> None:
        """Preparar o estado ao entrar."""
        return None

    def exit(self) -> None:
        """Libertar subscrições ou recursos ao sair."""
        return None

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Interpretar um evento de interface."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Atualizar usando segundos, sem desenhar."""

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Desenhar sem alterar a simulação."""


class StateMachine:
    def __init__(self, initial: State) -> None:
        self._current = initial
        self._current.enter()

    @property
    def current(self) -> State:
        return self._current

    def change(self, target: State) -> None:
        if target is self._current:
            return
        self._current.exit()
        self._current = target
        self._current.enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        self._current.handle_event(event)

    def update(self, dt: float) -> None:
        self._current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._current.draw(surface)

    def close(self) -> None:
        self._current.exit()
