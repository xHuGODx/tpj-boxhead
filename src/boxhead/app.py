"""Composição da aplicação e Game Loop; sem regras de gameplay."""

import logging
import random

import pygame

from boxhead.config import AppConfig
from boxhead.core.catalog import catalog
from boxhead.core.events import EventQueue
from boxhead.core.state import State, StateMachine
from boxhead.profile import LoadStatus, Profile, ProfileStore, default_profile_path
from boxhead.shop import profile_modifiers, purchase
from boxhead.states.augment_select import AugmentSelectState
from boxhead.states.game_over import GameOverState
from boxhead.states.menu import MenuState
from boxhead.states.paused import PausedState
from boxhead.states.playing import PlayingState
from boxhead.states.shop import ShopState
from boxhead.world.result import RunReason, RunResult
from boxhead.world.world import World

logger = logging.getLogger(__name__)


_WARN_STATUSES = (LoadStatus.RECOVERED, LoadStatus.INCOMPATIBLE)


class App:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self._running = False
        self._events = EventQueue()
        self._machine: StateMachine | None = None
        # Perfil local (#17): saldo e melhorias permanentes, partilhados por todas as partidas.
        self.profile_store = ProfileStore(self.config.profile_path or default_profile_path())
        loaded = self.profile_store.load()
        self.profile: Profile = loaded.profile
        self._profile_notice = loaded.detail if loaded.status in _WARN_STATUSES else None
        self._pending_results: dict[str, RunResult] = {}
        self._active_world: World | None = None  # partida em curso, ainda por creditar

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------ perfil

    def _retry_rewards(self) -> None:
        for run_id, result in list(self._pending_results.items()):
            try:
                self.profile_store.credit_run(self.profile, run_id, result.coins)
            except OSError as error:
                logger.warning("Recompensa %s pendente: %s", run_id, error)
                self._profile_notice = "Recompensa por guardar; nova tentativa no menu."
                return
            del self._pending_results[run_id]
        self._profile_notice = None

    def _finish_run(self, world: World | None = None, reason: RunReason = "quit") -> RunResult | None:
        world = world if world is not None else self._active_world
        if world is None:
            return None
        # Recompensas já publicadas são contabilizadas antes do snapshot.
        self._events.dispatch()
        result = world.finish(reason)
        self._events.dispatch()
        world.stop_listening()
        self._pending_results[result.run_id] = result
        self._retry_rewards()
        world.stats.credited = result.run_id in self.profile.credited_runs
        if world is self._active_world:
            self._active_world = None
        return result

    def _abandon_run(self) -> None:
        self._finish_run(reason="abandoned")
        self._to_menu()

    # ------------------------------------------------------------------ navegação

    def _make_menu(self) -> MenuState:
        return MenuState(
            self._start,
            self.stop,
            on_shop=self._to_shop,
            balance=self.profile.balance,
            notice=self._profile_notice,
        )

    def _to_menu(self) -> None:
        self._retry_rewards()
        assert self._machine is not None
        self._machine.change(self._make_menu())

    def _to_shop(self) -> None:
        assert self._machine is not None
        self._machine.change(
            ShopState(
                self.profile,
                self._to_menu,
                lambda upgrade_id: purchase(self.profile, self.profile_store, upgrade_id),
            )
        )

    def _start(self) -> None:
        self._retry_rewards()
        self._events.clear()
        self._events.clear_subscribers()
        assert self._machine is not None
        world = World(
            events=self._events,
            rng=random.Random(self.config.seed),
            base_modifiers=profile_modifiers(self.profile),
        )
        self._active_world = world
        playing = PlayingState(
            self._machine,
            self._events,
            on_pause=self._pause,
            on_game_over=self._game_over,
            viewport=self.config.window_size,
            world=world,
            on_level_up=self._level_up,
        )
        self._machine.change(playing)

    def _pause(self, state: State) -> None:
        assert self._machine is not None
        self._machine.change(PausedState(state, self._resume, self._abandon_run))

    def _resume(self, target: State) -> None:
        assert self._machine is not None
        self._machine.change(target)

    def _level_up(self, playing: PlayingState) -> None:
        self._next_selection_or_resume(playing)

    def _next_selection_or_resume(self, playing: PlayingState) -> None:
        """Abre a próxima escolha pendente (uma por nível) ou retoma a partida.

        Se não houver nenhum augment elegível, a escolha é dispensada: nunca se
        apresenta uma escolha impossível nem se bloqueia a partida.
        """
        assert self._machine is not None
        world = playing.world
        while world.progression.pending_choices > 0:
            offer = world.draw_offer()
            if offer.choices:
                self._machine.change(
                    AugmentSelectState(
                        playing,
                        world,
                        offer,
                        on_choose=lambda augment: self._augment_chosen(playing, augment),
                    )
                )
                return
            world.progression.consume_choice()
        if self._machine.current is not playing:
            self._machine.change(playing)

    def _augment_chosen(self, playing: PlayingState, augment) -> None:
        playing.world.choose_augment(augment)
        self._next_selection_or_resume(playing)

    def _game_over(self, world: World) -> None:
        assert self._machine is not None
        result = self._finish_run(world, "death")
        self._machine.change(
            GameOverState(
                result,
                on_retry=self._start,
                on_menu=self._to_menu,
                balance=self.profile.balance,
                notice=self._profile_notice,
            )
        )

    def run(self, *, max_frames: int | None = None) -> None:
        if max_frames is not None and max_frames <= 0:
            raise ValueError("max_frames tem de ser positivo")
        machine = None
        try:
            pygame.display.init()
            pygame.font.init()
            screen = pygame.display.set_mode(self.config.window_size)
            pygame.display.set_caption(self.config.title)
            catalog().preload()
            clock = pygame.time.Clock()
            machine = StateMachine(self._make_menu())
            self._machine = machine
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
                self._finish_run()
                self._retry_rewards()
                if machine is not None:
                    machine.close()
                self._events.clear()
                self._events.clear_subscribers()
            finally:
                pygame.quit()
