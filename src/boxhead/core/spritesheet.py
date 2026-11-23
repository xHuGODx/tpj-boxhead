"""Recortes declarativos: grelha regular ou retângulos explícitos num atlas."""
from __future__ import annotations

import pygame


def cut_grid(image: pygame.Surface, frame_size: tuple[int, int], *, rows: int,
             columns: int, source_rects=None, anchor="center", frame_cleanup=None,
             tile_border=False) -> list[list[pygame.Surface]]:
    fw, fh = frame_size
    if fw <= 0 or fh <= 0 or rows <= 0 or columns <= 0:
        raise ValueError("invalid spritesheet dimensions")
    if source_rects is not None and len(source_rects) != rows*columns:
        raise ValueError("crop count does not match grid")
    if anchor not in ("center", "bottom"):
        raise ValueError("unknown anchor")
    cleanup = frame_cleanup or {}
    frames = []
    for index in range(rows*columns):
        row,col = divmod(index,columns)
        rect = pygame.Rect(source_rects[index] if source_rects is not None
                           else (col*fw,row*fh,fw,fh))
        if rect.width <= 0 or rect.height <= 0 or not image.get_rect().contains(rect):
            raise ValueError(f"crop {index} outside image: {rect}")
        source = image.subsurface(rect).copy()
        rule = cleanup.get(str(index), {})
        if rule:
            mask = pygame.mask.from_surface(source,0)
            parts = mask.connected_components()
            if rule.get("keep_largest"):
                parts = [max(parts,key=lambda part:part.count())] if parts else []
            else:
                parts = [part for part in parts if part.count() >= rule.get("min_area",1)]
            retained = pygame.mask.Mask(source.get_size())
            for part in parts:
                retained.draw(part,(0,0))
            # Não altera cores/alpha das partes mantidas; apenas elimina ilhas.
            for y in range(source.get_height()):
                for x in range(source.get_width()):
                    if not retained.get_at((x,y)):
                        source.set_at((x,y),(0,0,0,0))
        frame = pygame.Surface((fw,fh),pygame.SRCALPHA)
        if tile_border:
            pygame.draw.rect(frame,(25,20,36),frame.get_rect(),border_radius=7)
            pygame.draw.rect(frame,(185,180,197),frame.get_rect().inflate(-2,-2),2,border_radius=7)
        if source_rects is not None:
            available = (fw-24,fh-24) if tile_border else (fw-8,fh-8)
            if source.get_width() > available[0] or source.get_height() > available[1]:
                scale = min(available[0]/source.get_width(),available[1]/source.get_height())
                source = pygame.transform.scale(source,(max(1,round(source.get_width()*scale)),
                                                         max(1,round(source.get_height()*scale))))
            dest = source.get_rect()
            if anchor == "bottom":
                dest.midbottom = (fw//2,fh-4)
            else:
                dest.center = (fw//2,fh//2)
            frame.blit(source,dest)
        else:
            frame.blit(source,(0,0))
        frames.append(frame)
    return [frames[r*columns:(r+1)*columns] for r in range(rows)]
