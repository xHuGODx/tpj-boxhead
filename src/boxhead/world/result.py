"""Resultado imutável de uma partida, independente da interface e do perfil."""

from dataclasses import dataclass
from typing import Literal

RunReason = Literal["death", "abandoned", "quit"]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    reason: RunReason
    round: int
    kills: int
    level: int
    xp: float
    coins: int
    elapsed: float
