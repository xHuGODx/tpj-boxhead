"""Frames partilhados; escala/rotação cacheadas, sem carregar ficheiros no draw."""
import pygame
from boxhead.core.catalog import SpriteCatalog


class SpritePainter:
    def __init__(self, catalog: SpriteCatalog):
        self.catalog = catalog
        self._frames = {}
        self._cache = {}

    def prepare(self, keys):
        for key in keys:
            self._frames[key] = self.catalog.sheet(key).animation().frames

    def frame_count(self, key):
        return len(self._frames[key])

    def frame(self, key, index=0):
        return self._frames[key][index % len(self._frames[key])]

    def image(self, key, size, index=0, angle=0, flip_x=False):
        source = self.frame(key, index)
        cache_key = (key, index % len(self._frames[key]), size, round(angle / 5) * 5, flip_x)
        if cache_key not in self._cache:
            scaled = pygame.transform.scale(source, size)
            if flip_x:
                scaled = pygame.transform.flip(scaled, True, False)
            self._cache[cache_key] = pygame.transform.rotate(scaled, cache_key[-2])
        return self._cache[cache_key]

    def blit(self, surface, key, center, size, index=0, angle=0, flip_x=False):
        image = self.image(key, size, index, angle, flip_x)
        surface.blit(image, image.get_rect(center=center))
