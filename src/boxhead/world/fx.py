"""Dados de apresentação produzidos pela simulação: efeitos curtos e corpos em órbita.

São só dados (sem Surfaces): o estado de partida desenha-os e o domínio não sabe como.
"""

from __future__ import annotations

from dataclasses import dataclass

from pygame import Vector2


@dataclass
class Fx:
    """Efeito visual de curta duração (por exemplo, uma explosão)."""

    kind: str
    position: Vector2
    radius: float
    ttl: float  # tempo restante
    duration: float  # duração total, para calcular o progresso

    @property
    def progress(self) -> float:
        return 1.0 - max(0.0, self.ttl) / self.duration


@dataclass(frozen=True)
class Body:
    """Corpo persistente que aparece no mundo (por exemplo, um satélite orbital)."""

    position: Vector2
    radius: float
    color: tuple[int, int, int]
