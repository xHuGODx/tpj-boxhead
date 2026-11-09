"""Configuração imutável da aplicação; sem estado global de partida."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    title: str = "Boxhead | TPJ"
    window_size: tuple[int, int] = (1100, 700)
    fps: int = 60
    max_frame_seconds: float = 0.1
