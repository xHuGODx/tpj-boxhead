"""Carregamento de imagens com fallback para placeholders."""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)

_PACKAGED = Path(__file__).resolve().parent.parent / "data"
ASSETS_ROOT = _PACKAGED if _PACKAGED.exists() else Path(__file__).resolve().parents[3] / "assets"


def load_image(
    relative: str,
    *,
    size: tuple[int, int] | None = None,
    fallback_color: tuple[int, int, int] = (200, 200, 200),
    fallback_size: tuple[int, int] = (32, 32),
) -> pygame.Surface:
    path = ASSETS_ROOT / relative
    if not path.exists():
        path = ASSETS_ROOT / "sprites_cortados" / "pixel_art_pygame_pack_v2" / relative
    if path.exists():
        image = pygame.image.load(str(path)).convert_alpha()
        if size is not None and image.get_size() != size:
            image = pygame.transform.scale(image, size)
        return image
    logger.warning("missing asset, using placeholder: %s", relative)
    surface = pygame.Surface(size or fallback_size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fallback_color, surface.get_rect(), border_radius=4)
    return surface
