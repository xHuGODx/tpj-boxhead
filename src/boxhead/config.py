"""Configuração imutável da aplicação; sem estado global de partida."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    title: str = "Boxhead | TPJ"
    window_size: tuple[int, int] = (1100, 700)
    fps: int = 60
    max_frame_seconds: float = 0.1
    seed: int | None = None  # None = aleatório; um valor fixo torna a partida reproduzível
    profile_path: Path | None = None  # None = ~/.boxhead/profile.json (ou $BOXHEAD_HOME)
    fullscreen: bool | None = None  # None usa a preferência guardada
