"""Estado de partida: traduz input em comandos e atualiza o mundo."""

from __future__ import annotations

from collections.abc import Callable

import pygame
from pygame import Vector2

from boxhead.core.commands import Move, Shoot, SwitchWeapon
from boxhead.core.events import EventQueue
from boxhead.core.state import State, StateMachine
from boxhead.world.camera import Camera
from boxhead.world.world import World


class PlayingState(State):
    def __init__(self, machine: StateMachine, events: EventQueue,
                 on_pause: Callable[[State], None],
                 on_game_over: Callable[[World, float], None]) -> None:
        self._machine = machine
        self._events = events
        self._on_pause = on_pause
        self._on_game_over = on_game_over

    def enter(self) -> None:
        self._world = World()
        self._camera = Camera((1100, 700))
        self._elapsed = 0.0
        self._pressed: set[int] = set()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._pressed.add(event.key)
            if event.key == pygame.K_ESCAPE:
                self._on_pause(self)
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self._world.apply(SwitchWeapon(event.key - pygame.K_1), 0.0)
        elif event.type == pygame.KEYUP:
            self._pressed.discard(event.key)

    def update(self, dt: float) -> None:
        self._elapsed += dt
        direction = Vector2(
            (pygame.K_d in self._pressed) - (pygame.K_a in self._pressed),
            (pygame.K_s in self._pressed) - (pygame.K_w in self._pressed),
        )
        self._world.apply(Move(direction), dt)
        if pygame.K_SPACE in self._pressed:
            self._world.apply(Shoot(), dt)
        self._world.update(dt)
        self._events.dispatch()
        if self._world.player.health <= 0:
            self._on_game_over(self._world, self._elapsed)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 23, 29))
        self._camera.follow(self._world.player.position)
        center = self._camera.world_to_screen(self._world.player.position)
        pygame.draw.circle(surface, (235, 77, 76), center, self._world.player.radius)