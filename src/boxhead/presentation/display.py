"""Modo de janela independente do mundo; canvas lógico e input proporcionais."""
import pygame


class Display:
    def __init__(self, logical_size: tuple[int, int], fullscreen: bool = False):
        self.logical_size = logical_size
        self.fullscreen = fullscreen
        self.screen: pygame.Surface | None = None
        self.canvas: pygame.Surface | None = None
        self._scaled: pygame.Surface | None = None

    def open(self) -> None:
        size = (0, 0) if self.fullscreen else self.logical_size
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode(size, flags)
        if self.canvas is None:
            self.canvas = pygame.Surface(self.logical_size).convert()
        self._scaled = None

    def toggle(self) -> None:
        self.fullscreen = not self.fullscreen
        try:
            self.open()
        except pygame.error:
            self.fullscreen = not self.fullscreen
            self.open()
            raise

    @property
    def viewport(self) -> pygame.Rect:
        assert self.screen is not None
        width, height = self.screen.get_size()
        scale = min(width/self.logical_size[0], height/self.logical_size[1])
        rect = pygame.Rect(0, 0, round(self.logical_size[0]*scale), round(self.logical_size[1]*scale))
        rect.center = (width//2, height//2)
        return rect

    def map_event(self, event: pygame.event.Event) -> pygame.event.Event | None:
        """Coordenadas físicas → canvas; barras laterais não recebem cliques."""
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return event
        rect = self.viewport
        if not rect.collidepoint(event.pos):
            # Libertar o botão continua a ser importante mesmo fora do canvas.
            if event.type != pygame.MOUSEBUTTONUP:
                return None
        data = event.dict.copy()
        data['pos'] = ((event.pos[0]-rect.x)*self.logical_size[0]/rect.width,
                       (event.pos[1]-rect.y)*self.logical_size[1]/rect.height)
        if 'rel' in data:
            data['rel'] = (data['rel'][0]*self.logical_size[0]/rect.width,
                           data['rel'][1]*self.logical_size[1]/rect.height)
        return pygame.event.Event(event.type, data)

    def present(self) -> None:
        assert self.screen is not None and self.canvas is not None
        rect = self.viewport
        self.screen.fill((0, 0, 0))
        if rect.size == self.logical_size:
            self.screen.blit(self.canvas, rect)
        else:
            if self._scaled is None or self._scaled.get_size() != rect.size:
                self._scaled = pygame.Surface(rect.size).convert()
            pygame.transform.smoothscale(self.canvas, rect.size, self._scaled)
            self.screen.blit(self._scaled, rect)
        pygame.display.flip()
