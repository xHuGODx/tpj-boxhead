"""Composição da aplicação e Game Loop; sem regras de gameplay."""

import pygame

from boxhead.config import AppConfig
from boxhead.core.state import StateMachine
from boxhead.states.menu import MenuState


class App:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run(self, *, max_frames: int | None = None) -> None:
        if max_frames is not None and max_frames <= 0:
            raise ValueError("max_frames tem de ser positivo")
        machine = None
        try:
            pygame.display.init()
            pygame.font.init()
            screen = pygame.display.set_mode(self.config.window_size)
            pygame.display.set_caption(self.config.title)
            clock = pygame.time.Clock()
            machine = StateMachine(MenuState(self.stop))
            self._running = True
            frames = 0

            while self._running and (max_frames is None or frames < max_frames):
                dt = min(clock.tick(self.config.fps) / 1000, self.config.max_frame_seconds)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.stop()
                    else:
                        machine.handle_event(event)
                    if not self._running:
                        break
                if not self._running:
                    break
                machine.update(dt)
                machine.draw(screen)
                pygame.display.flip()
                frames += 1
        finally:
            self._running = False
            try:
                if machine is not None:
                    machine.close()
            finally:
                pygame.quit()
