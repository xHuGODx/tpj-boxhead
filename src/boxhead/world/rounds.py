"""Rondas infinitas: orçamento de spawns, intervalo entre rondas e dificuldade crescente.

As fases (Intermission → Spawning → Clearing) formam uma máquina própria, separada
dos estados da aplicação. Uma ronda só termina quando o orçamento se esgota *e* já
não há inimigos vivos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from pygame import Vector2

from boxhead.core.events import RoundEnded, RoundStarted
from boxhead.world.enemy import BASIC, BOSS, RED, EnemyDef

if TYPE_CHECKING:
    from boxhead.world.world import World


@dataclass(frozen=True)
class RoundConfig:
    """Curvas de dificuldade configuráveis; imutáveis e partilhadas."""

    first_intermission: float = 2.0
    intermission: float = 4.0
    base_enemies: int = 6
    enemy_growth: float = 1.25
    spawn_interval: float = 0.6
    max_alive: int = 25  # limita a carga; o resto do orçamento espera
    min_spawn_distance: float = 700.0
    health_per_round: float = 0.08
    speed_per_round: float = 0.03
    max_speed_multiplier: float = 1.5
    red_start_round: int = 3  # o vermelho só aparece a partir desta ronda
    red_chance_per_round: float = 0.08
    max_red_chance: float = 0.35
    boss_every: int = 10  # 0 desliga os bosses
    boss_escort_fraction: float = 0.5  # fração do orçamento normal que acompanha o boss
    boss_health_per_boss: float = 0.5  # +50% de vida por cada boss já derrotado/aparecido

    def enemy_budget(self, round_number: int) -> int:
        return max(1, round(self.base_enemies * self.enemy_growth ** (round_number - 1)))

    def health_multiplier(self, round_number: int) -> float:
        return 1.0 + self.health_per_round * (round_number - 1)

    def speed_multiplier(self, round_number: int) -> float:
        return min(self.max_speed_multiplier, 1.0 + self.speed_per_round * (round_number - 1))

    def is_boss_round(self, round_number: int) -> bool:
        return self.boss_every > 0 and round_number % self.boss_every == 0

    def boss_health_multiplier(self, round_number: int) -> float:
        boss_index = max(1, round_number // max(1, self.boss_every))
        return 1.0 + self.boss_health_per_boss * (boss_index - 1)

    def round_total(self, round_number: int) -> int:
        """Inimigos a criar na ronda: o orçamento normal, ou escoltas mais o boss."""
        budget = self.enemy_budget(round_number)
        if self.is_boss_round(round_number):
            return max(1, round(budget * self.boss_escort_fraction)) + 1
        return budget

    def red_chance(self, round_number: int) -> float:
        """Probabilidade de cada spawn ser vermelho (composição da ronda)."""
        if round_number < self.red_start_round:
            return 0.0
        rounds_in = round_number - self.red_start_round + 1
        return min(self.max_red_chance, self.red_chance_per_round * rounds_in)


DEFAULT_ROUNDS = RoundConfig()


class Phase(Enum):
    INTERMISSION = "intermission"
    SPAWNING = "spawning"
    CLEARING = "clearing"


class RoundDirector:
    def __init__(self, config: RoundConfig) -> None:
        self.config = config
        self.round_number = 0  # 0 = ainda nenhuma ronda começou
        self.phase = Phase.INTERMISSION
        self.intermission_left = config.first_intermission
        self.pending = 0  # inimigos do orçamento ainda por criar
        self.is_boss_round = False
        self._boss_pending = False
        self._spawn_cooldown = 0.0

    def update(self, dt: float, world: World) -> None:
        if self.phase is Phase.INTERMISSION:
            self.intermission_left -= dt
            if self.intermission_left <= 0:
                self._start_round(world)
        elif self.phase is Phase.SPAWNING:
            self._spawn_cooldown = max(0.0, self._spawn_cooldown - dt)
            if (
                self.pending > 0
                and self._spawn_cooldown == 0
                and world.alive_enemy_count < self.config.max_alive
            ):
                self._spawn_one(world)
            if self.pending == 0:
                self.phase = Phase.CLEARING
        elif self.phase is Phase.CLEARING and world.alive_enemy_count == 0:
            world.events.publish(RoundEnded(self.round_number))
            self.phase = Phase.INTERMISSION
            self.intermission_left = self.config.intermission

    def _start_round(self, world: World) -> None:
        self.round_number += 1
        self.pending = self.config.round_total(self.round_number)
        self.is_boss_round = self.config.is_boss_round(self.round_number)
        self._boss_pending = self.is_boss_round  # o boss é o primeiro a aparecer
        self.phase = Phase.SPAWNING
        self._spawn_cooldown = 0.0
        world.events.publish(RoundStarted(self.round_number))

    def _spawn_one(self, world: World) -> None:
        cfg, n = self.config, self.round_number
        if self._boss_pending:
            self._boss_pending = False
            world.spawn_enemy(
                BOSS,
                self._pick_spawn_point(world),
                health_multiplier=cfg.boss_health_multiplier(n),
            )
        else:
            world.spawn_enemy(
                self._pick_definition(world),
                self._pick_spawn_point(world),
                health_multiplier=cfg.health_multiplier(n),
                speed_multiplier=cfg.speed_multiplier(n),
            )
        self.pending -= 1
        self._spawn_cooldown = cfg.spawn_interval

    def _pick_definition(self, world: World) -> EnemyDef:
        chance = self.config.red_chance(self.round_number)
        # Só consome o RNG quando há escolha: rondas só com normais mantêm a sequência.
        if chance > 0 and world.rng.random() < chance:
            return RED
        return BASIC

    def _pick_spawn_point(self, world: World) -> Vector2:
        points = world.map.spawn_points
        player = world.player.position
        far = [p for p in points if p.distance_to(player) >= self.config.min_spawn_distance]
        if far:
            return world.rng.choice(far)
        return max(points, key=lambda p: p.distance_to(player))
