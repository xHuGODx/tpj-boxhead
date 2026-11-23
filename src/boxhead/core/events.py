"""Eventos de domínio: publicação e despacho em momentos distintos."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boxhead.world.result import RunResult


@dataclass(frozen=True)
class Event:
    """Evento de domínio; subclasses identificam o tipo."""


@dataclass(frozen=True)
class EnemyKilled(Event):
    enemy_id: int
    xp_reward: int
    coin_reward: int
    is_boss: bool = False
    weapon_name: str | None = None


@dataclass(frozen=True)
class LevelUp(Event):
    level: int  


@dataclass(frozen=True)
class RoundStarted(Event):
    round_number: int


@dataclass(frozen=True)
class RoundCompleted(Event):
    round_number: int
    weapon_name: str | None = None


# Nome antigo mantido para consumidores existentes; é o mesmo tipo de evento.
RoundEnded = RoundCompleted


@dataclass(frozen=True)
class PlayerDied(Event):
    run_id: str


@dataclass(frozen=True)
class RunFinished(Event):
    result: "RunResult"


Handler = Callable[[Event], None]


class EventQueue:
    """Publica e despacha eventos; nunca despacha durante a publicação.

    Eventos publicados durante o despacho ficam para a *geração* seguinte,
    evitando recursão. O limite aplica-se à profundidade da cadeia (quantas
    gerações seguidas), não ao número de eventos: muitas mortes no mesmo frame
    são uma só geração e não são um problema.
    """

    MAX_CHAIN = 32

    def __init__(self) -> None:
        self._pending: deque[Event] = deque()
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
        """Processa os eventos pendentes, geração a geração, por ordem de publicação."""
        generation = 0
        while self._pending:
            if generation >= self.MAX_CHAIN:
                self._pending.clear()
                raise RuntimeError("event chain exceeded its limit")
            for _ in range(len(self._pending)):
                event = self._pending.popleft()
                for handler in tuple(self._subscribers.get(type(event), ())):
                    handler(event)
            generation += 1

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
