"""Eventos de domínio: publicação e despacho em momentos distintos."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    """Evento de domínio; subclasses identificam o tipo."""


@dataclass(frozen=True)
class EnemyKilled(Event):
    enemy_id: int
    xp_reward: int
    coin_reward: int


@dataclass(frozen=True)
class RoundEnded(Event):
    round_number: int


Handler = Callable[[Event], None]


class EventQueue:
    """Publica e despacha eventos; nunca despacha durante a publicação.

    Eventos publicados durante o despacho ficam para o despacho seguinte,
    evitando recursão e efeitos em cadeia sem limite.
    """

    MAX_CHAIN = 32

    def __init__(self) -> None:
        self._pending: deque[Event] = deque()
        self._dispatch_count = 0
        self._subscribers: dict[type[Event], list[Handler]] = {}

    def subscribe(self, event_type: type[Event], handler: Handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: type[Event], handler: Handler) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Event) -> None:
        self._pending.append(event)

    def dispatch(self) -> None:
        """Processa os eventos pendentes por ordem de publicação."""
        while self._pending:
            if self._dispatch_count >= self.MAX_CHAIN:
                raise RuntimeError("cadeia de eventos excedeu o limite")
            event = self._pending.popleft()
            for handler in tuple(self._subscribers.get(type(event), ())):
                handler(event)
            self._dispatch_count += 1
        self._dispatch_count = 0

    def clear(self) -> None:
        self._pending.clear()

    def clear_subscribers(self) -> None:
        self._subscribers.clear()


def make_counter() -> Callable[[], int]:
    """Identificadores incrementais para entidades."""
    counter = 0

    def next_id() -> int:
        nonlocal counter
        counter += 1
        return counter

    return next_id