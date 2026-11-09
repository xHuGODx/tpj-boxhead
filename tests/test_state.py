"""Contrato da FSM: ciclo de vida e encaminhamento para o estado ativo."""

import pygame

from boxhead.core.state import State, StateMachine


class RecordingState(State):
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def enter(self):
        self.calls.append((self.name, "enter"))

    def exit(self):
        self.calls.append((self.name, "exit"))

    def handle_event(self, event):
        self.calls.append((self.name, "event", event))

    def update(self, dt):
        self.calls.append((self.name, "update", dt))

    def draw(self, surface):
        self.calls.append((self.name, "draw", surface))


def test_transition_exits_before_entering_and_keeps_same_state_untouched():
    calls = []
    menu = RecordingState("menu", calls)
    game = RecordingState("game", calls)
    machine = StateMachine(menu)
    machine.change(menu)
    machine.change(game)
    assert calls == [("menu", "enter"), ("menu", "exit"), ("game", "enter")]
    assert machine.current is game


def test_only_current_state_receives_events_updates_and_rendering():
    calls = []
    machine = StateMachine(RecordingState("old", calls))
    machine.change(RecordingState("active", calls))
    calls.clear()
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    surface = pygame.Surface((10, 10))
    machine.handle_event(event)
    machine.update(0.02)
    machine.draw(surface)
    machine.close()
    assert calls == [
        ("active", "event", event),
        ("active", "update", 0.02),
        ("active", "draw", surface),
        ("active", "exit"),
    ]
