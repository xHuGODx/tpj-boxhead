"""Catálogo de spritesheets/animações, orientado pelo manifest.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from boxhead.core.assets import ASSETS_ROOT, load_image
from boxhead.core.spritesheet import cut_grid


@dataclass
class Animation:
    frames: list[pygame.Surface]
    fps: float = 8.0
    loop: bool = True

    def __post_init__(self) -> None:
        self._time = 0.0
        self._index = 0
        self._done = False

    def update(self, dt: float) -> None:
        if self._done or len(self.frames) <= 1:
            return
        self._time += dt
        step = 1.0 / self.fps
        while self._time >= step:
            self._time -= step
            nxt = self._index + 1
            if nxt >= len(self.frames):
                if self.loop:
                    self._index = 0
                else:
                    self._index = len(self.frames) - 1
                    self._done = True
                    return
            else:
                self._index = nxt

    @property
    def current(self) -> pygame.Surface:
        return self.frames[self._index]

    @property
    def finished(self) -> bool:
        return self._done

    def reset(self) -> None:
        self._time = 0.0
        self._index = 0
        self._done = False


@dataclass
class SpriteSheet:
    rows: int
    columns: int
    fps: float
    loop: bool
    direction_order: list[str] | None
    frames: list[list[pygame.Surface]] = field(default_factory=list)

    def animation(self, direction: str | None = None) -> Animation:
        if direction and self.direction_order and direction in self.direction_order:
            idx = self.direction_order.index(direction)
            row = self.frames[idx]
            return Animation(list(row), self.fps, self.loop)
        flat = [frame for row in self.frames for frame in row]
        return Animation(flat, self.fps, self.loop)


class SpriteCatalog:
    """Carrega e cacheia spritesheets a partir do manifest.json."""

    def __init__(self, manifest_path: Path | None = None) -> None:
        self._manifest_path = manifest_path or (ASSETS_ROOT / "manifest.json")
        self._entries: dict[str, dict] = {}
        self._sheets: dict[str, SpriteSheet] = {}
        if self._manifest_path.exists():
            with self._manifest_path.open(encoding="utf-8") as f:
                self._entries = json.load(f)

    def has(self, key: str) -> bool:
        return key in self._entries

    def indices(self, key: str) -> dict[str, int]:
        return dict(self._entries[key].get("labels", {}))

    def preload(self) -> None:
        """Carrega o manifest uma vez, depois de o SDL estar pronto."""
        for key in self._entries:
            self.sheet(key)

    def sheet(self, key: str) -> SpriteSheet:
        if key in self._sheets:
            return self._sheets[key]
        entry = self._entries.get(key)
        if entry is None:
            raise KeyError(f"chave ausente do manifest: {key}")
        frame_size = tuple(entry["frame_size"])
        image = load_image(
            key,
            fallback_color=self._fallback_color(key),
            fallback_size=(
                frame_size[0] * entry.get("columns", 1),
                frame_size[1] * entry.get("rows", 1),
            ),
        )
        grid = cut_grid(
            image,
            frame_size,
            rows=entry.get("rows", 1),
            columns=entry.get("columns", 1),
            source_rects=entry.get("source_rects"),
            anchor=entry.get("anchor", "center"),
            frame_cleanup=entry.get("frame_cleanup"),
            tile_border=entry.get("tile_border", False),
        )
        sheet = SpriteSheet(
            rows=entry.get("rows", 1),
            columns=entry.get("columns", 1),
            fps=entry.get("fps", 8.0),
            loop=entry.get("loop", True),
            direction_order=entry.get("direction_order"),
            frames=grid,
        )
        self._sheets[key] = sheet
        return sheet

    @staticmethod
    def _fallback_color(key: str) -> tuple[int, int, int]:
        if key.startswith("player"):
            return (235, 77, 76)
        if key.startswith("enemies/enemy_red"):
            return (215, 70, 70)
        if key.startswith("enemies"):
            return (180, 90, 200)
        if key.startswith("bosses"):
            return (200, 60, 60)
        if key.startswith("environment"):
            return (60, 70, 50)
        if key.startswith("ui"):
            return (90, 110, 140)
        return (120, 120, 120)


_catalog: SpriteCatalog | None = None


def catalog() -> SpriteCatalog:
    global _catalog
    if _catalog is None:
        _catalog = SpriteCatalog()
    return _catalog


def reset_catalog() -> None:
    global _catalog
    _catalog = None
