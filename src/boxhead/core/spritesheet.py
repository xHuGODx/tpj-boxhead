"""Corte de spritesheets em grelha."""

from __future__ import annotations

import pygame


def cut_grid(
    image: pygame.Surface,
    frame_size: tuple[int, int],
    *,
    rows: int,
    columns: int,
) -> list[list[pygame.Surface]]:
    fw, fh = frame_size
    return [
        [image.subsurface(pygame.Rect(col * fw, row * fh, fw, fh)).copy() for col in range(columns)]
        for row in range(rows)
    ]
