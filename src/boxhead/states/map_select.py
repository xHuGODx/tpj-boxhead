"""Escolha de definição de mapa; cada confirmação cria uma partida independente."""
from collections.abc import Callable

import pygame

from boxhead.core.catalog import catalog
from boxhead.core.state import State
from boxhead.presentation.sprites import SpritePainter
from boxhead.world.map import MAPS


class MapSelectState(State):
    def __init__(self, on_select: Callable[[str], None], on_back: Callable[[], None], selected: str):
        self._on_select = on_select
        self._on_back = on_back
        self._keys = tuple(MAPS)
        self._cursor = self._keys.index(selected)

    def enter(self):
        self._title = pygame.font.Font(None, 54)
        self._body = pygame.font.Font(None, 32)
        self._small = pygame.font.Font(None, 24)
        self._painter = SpritePainter(catalog())
        self._painter.prepare([m.thumbnail for m in MAPS.values()])

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self._on_back()
        elif event.key in (pygame.K_LEFT,pygame.K_a):
            self._cursor = (self._cursor-1)%len(self._keys)
        elif event.key in (pygame.K_RIGHT,pygame.K_d):
            self._cursor = (self._cursor+1)%len(self._keys)
        elif event.key in (pygame.K_RETURN,pygame.K_SPACE):
            self._on_select(self._keys[self._cursor])

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((19,23,29))
        width,height = surface.get_size()
        title=self._title.render("ESCOLHER MAPA",True,(235,77,76))
        surface.blit(title,title.get_rect(center=(width//2,100)))
        for index,key in enumerate(self._keys):
            definition=MAPS[key]
            rect=pygame.Rect(width//2-463+index*318,height//2-120,290,320)
            pygame.draw.rect(surface,(28,32,42),rect,border_radius=10)
            color=(255,220,120) if index==self._cursor else (90,100,115)
            pygame.draw.rect(surface,color,rect,3,border_radius=10)
            self._painter.blit(surface,definition.thumbnail,(rect.centerx,rect.y+100),(260,170))
            text=self._body.render(definition.name,True,(235,235,240))
            surface.blit(text,text.get_rect(center=(rect.centerx,rect.y+210)))
            mode="Chunks · sem fronteiras" if definition.infinite else "Arena limitada"
            text=self._small.render(mode,True,color)
            surface.blit(text,text.get_rect(center=(rect.centerx,rect.y+260)))
        hint=self._small.render("A/D ou setas · Enter joga · Esc volta",True,(170,180,190))
        surface.blit(hint,hint.get_rect(center=(width//2,height-70)))
