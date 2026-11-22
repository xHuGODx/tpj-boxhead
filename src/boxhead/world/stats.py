"""Contabilidade da partida, alimentada por eventos de domínio (Observer).

Subscreve ao entrar e deixa de subscrever ao sair, por isso repetir partidas
não duplica recompensas.
"""

from __future__ import annotations

from dataclasses import dataclass

from boxhead.core.events import EnemyKilled, EventQueue, RoundEnded, RoundStarted

ROUND_COIN_BONUS = 2  # moeda por número de ronda concluída (ronda 5 → 10)


@dataclass
class RunStats:
    kills: int = 0
    xp: int = 0
    coins: int = 0
    round: int = 0
    bosses: int = 0
    rounds_completed: int = 0
    credited: bool = False  # a moeda já foi creditada ao perfil (acontece uma só vez)

    def __post_init__(self) -> None:
        self._events: EventQueue | None = None

    def attach(self, events: EventQueue) -> None:
        if self._events is not None:
            return
        self._events = events
        events.subscribe(EnemyKilled, self._on_kill)
        events.subscribe(RoundStarted, self._on_round_started)
        events.subscribe(RoundEnded, self._on_round_ended)

    def detach(self) -> None:
        if self._events is None:
            return
        self._events.unsubscribe(EnemyKilled, self._on_kill)
        self._events.unsubscribe(RoundStarted, self._on_round_started)
        self._events.unsubscribe(RoundEnded, self._on_round_ended)
        self._events = None

    def _on_kill(self, event: EnemyKilled) -> None:
        self.kills += 1
        self.xp += event.xp_reward
        self.coins += event.coin_reward
        self.bosses += event.is_boss

    def _on_round_started(self, event: RoundStarted) -> None:
        self.round = event.round_number

    def _on_round_ended(self, event: RoundEnded) -> None:
        self.rounds_completed += 1
        self.coins += ROUND_COIN_BONUS * event.round_number
