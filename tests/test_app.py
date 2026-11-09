"""Fechar a aplicação deve funcionar também em CI sem ecrã."""

import pygame
import pytest

from boxhead.app import App
from boxhead.config import AppConfig


@pytest.mark.parametrize(
    "event",
    [pygame.event.Event(pygame.QUIT), pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
)
def test_quit_and_escape_stop_before_another_update(monkeypatch, event):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(pygame.event, "get", lambda: [event])

    def unexpected_update(self, dt):
        pytest.fail("não pode haver update depois de sair")

    monkeypatch.setattr("boxhead.states.menu.MenuState.update", unexpected_update)
    App(AppConfig(window_size=(640, 480))).run(max_frames=2)
    assert not pygame.display.get_init()
    assert not pygame.font.get_init()


def test_sdl_is_released_when_a_state_fails(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setattr(pygame.event, "get", lambda: [])

    def fail(self, dt):
        raise RuntimeError("erro simulado")

    monkeypatch.setattr("boxhead.states.menu.MenuState.update", fail)
    with pytest.raises(RuntimeError, match="erro simulado"):
        App().run(max_frames=1)
    assert not pygame.display.get_init()
    assert not pygame.font.get_init()
