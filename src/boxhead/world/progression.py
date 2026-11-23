"""XP, níveis e fila de escolhas de augment (níveis e recompensas de ronda).

O XP chega por eventos (`EnemyKilled`); cada nível ganho enfileira uma escolha, por isso
XP excedente que dê vários níveis gera várias escolhas, resolvidas uma de cada vez.
O bónus de ronda guarda a arma alvo sem alterar XP nem nível.
"""

from __future__ import annotations

from collections.abc import Callable
from collections import deque
from dataclasses import dataclass

from boxhead.core.events import EnemyKilled, EventQueue, LevelUp


@dataclass(frozen=True)
class LevelCurve:
    """XP necessário para subir do nível `n` para `n + 1` (propostas ajustáveis)."""

    base: int = 40
    growth: float = 1.3

    def xp_for_next(self, level: int) -> int:
        return max(1, round(self.base * self.growth ** (level - 1)))


DEFAULT_CURVE = LevelCurve()


@dataclass(frozen=True)
class AugmentChoice:
    level: int
    weapon: str | None = None
    round_number: int | None = None


class Progression:
    def __init__(
        self,
        curve: LevelCurve = DEFAULT_CURVE,
        xp_multiplier: Callable[[], float] = lambda: 1.0,
    ) -> None:
        self.curve = curve
        self._xp_multiplier = xp_multiplier
        self.level = 1
        self.total_xp = 0.0
        self.xp = 0.0  # XP acumulado dentro do nível atual
        self._choices: deque[AugmentChoice] = deque()
        self._events: EventQueue | None = None

    @property
    def pending_choices(self) -> int:
        return len(self._choices)

    @property
    def next_choice(self) -> AugmentChoice | None:
        return self._choices[0] if self._choices else None

    def reward_round(self, round_number: int, weapon: str) -> None:
        self._choices.append(AugmentChoice(self.level, weapon, round_number))

    @property
    def xp_needed(self) -> int:
        return self.curve.xp_for_next(self.level)

    @property
    def xp_ratio(self) -> float:
        return self.xp / self.xp_needed

    def add_xp(self, amount: float) -> int:
        """Soma XP (com o multiplicador atual); devolve quantos níveis foram ganhos."""
        if amount <= 0:
            return 0
        earned = amount * self._xp_multiplier()
        self.total_xp += earned
        self.xp += earned
        gained = 0
        while self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self._choices.append(AugmentChoice(self.level))
            gained += 1
            if self._events is not None:
                self._events.publish(LevelUp(self.level))
        return gained

    def consume_choice(self) -> None:
        if self.pending_choices <= 0:
            raise ValueError("no pending choices")
        self._choices.popleft()

    # --- subscrição a eventos (Observer), como `RunStats` -----------------------------

    def attach(self, events: EventQueue) -> None:
        if self._events is not None:
            return
        self._events = events
        events.subscribe(EnemyKilled, self._on_kill)

    def detach(self) -> None:
        if self._events is None:
            return
        self._events.unsubscribe(EnemyKilled, self._on_kill)
        self._events = None

    def _on_kill(self, event: EnemyKilled) -> None:
        self.add_xp(event.xp_reward)
