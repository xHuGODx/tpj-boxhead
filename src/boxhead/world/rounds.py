"""Rondas infinitas: orçamento de spawns, intervalo entre rondas e dificuldade crescente.

As fases (Intermission → Spawning → Clearing) formam uma máquina própria, separada
dos estados da aplicação. Uma ronda só termina quando o orçamento se esgota *e* já
não há inimigos vivos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil, isfinite, log
from typing import TYPE_CHECKING

from pygame import Vector2

from boxhead.core.events import RoundCompleted, RoundStarted
from boxhead.world.enemy import BASIC, BOSS, RED, EnemyDef

if TYPE_CHECKING:
    from boxhead.world.world import World


@dataclass(frozen=True)
class RoundConfig:
    """Curvas de dificuldade configuráveis; imutáveis e partilhadas."""

    first_intermission: float = 0.5
    intermission: float = 2.0
    base_enemies: int = 6
    max_budget: int = 300  # carga total por ronda; número de rondas não tem limite
    enemy_growth: float = 1.25
    spawn_interval: float = 0.45
    opening_spawn_interval: float = 0.25
    opening_rounds: int = 3
    max_alive: int = 50  # limita a carga; o resto do orçamento espera
    min_spawn_distance: float = 400.0
    health_per_round: float = 0.20
    health_exponential_start: int = 10
    health_growth: float = 1.20
    damage_per_round: float = 0.05
    normal_damage_cap: float = 0.49
    speed_per_round: float = 0.03
    max_speed_multiplier: float = 1.5
    timing_reduction_start: int = 10
    timing_reduction_per_round: float = 0.06
    min_timing_multiplier: float = 0.70
    red_start_round: int = 3  # o vermelho só aparece a partir desta ronda
    red_chance_per_round: float = 0.10
    max_red_chance: float = 0.50
    elite_start_round: int = 5
    elite_start_chance: float = 0.05
    elite_chance_per_round: float = 0.02
    max_elite_chance: float = 0.30
    elite_health_multiplier: float = 3.0
    elite_xp_multiplier: float = 1.5
    prismatic_every: int = 5
    prismatic_health_multiplier: float = 5.0
    boss_every: int = 10  # 0 desliga os bosses
    boss_escort_fraction: float = 0.5  # fração do orçamento normal que acompanha o boss
    boss_reward_per_boss: float = 0.25
    boss_health_growth: float = 10.0  # 1.º boss 1x, 2.º 10x, 3.º 100x, ...

    def __post_init__(self) -> None:
        counts = (
            self.base_enemies, self.max_budget, self.max_alive, self.red_start_round,
            self.opening_rounds, self.health_exponential_start, self.timing_reduction_start,
            self.elite_start_round,
        )
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in counts):
            raise ValueError("round counts must be positive integers")
        if self.max_budget < self.base_enemies or self.enemy_growth < 1:
            raise ValueError("invalid enemy scaling curve")
        values = (self.first_intermission, self.intermission, self.spawn_interval,
                  self.min_spawn_distance, self.opening_spawn_interval, self.enemy_growth, self.health_per_round,
                  self.health_growth, self.damage_per_round, self.normal_damage_cap,
                  self.speed_per_round, self.max_speed_multiplier, self.timing_reduction_per_round,
                  self.min_timing_multiplier, self.red_chance_per_round, self.max_red_chance,
                  self.elite_start_chance, self.elite_chance_per_round, self.max_elite_chance,
                  self.elite_health_multiplier, self.elite_xp_multiplier,
                  self.boss_escort_fraction, self.boss_health_growth,
                  self.boss_reward_per_boss)
        if any(not isfinite(v) or v < 0 for v in values) or self.spawn_interval == 0 or self.opening_spawn_interval == 0:
            raise ValueError("invalid round timing or multipliers")
        probabilities = (
            self.normal_damage_cap, self.max_red_chance, self.elite_start_chance,
            self.max_elite_chance, self.boss_escort_fraction,
        )
        if any(not 0 <= value <= 1 for value in probabilities):
            raise ValueError("probability/fraction outside 0..1")
        if self.health_growth < 1 or self.boss_health_growth < 1:
            raise ValueError("health growth must be at least one")
        if not 0 < self.min_timing_multiplier <= 1:
            raise ValueError("invalid minimum attack timing multiplier")
        if isinstance(self.boss_every, bool) or not isinstance(self.boss_every, int) or self.boss_every < 0:
            raise ValueError("invalid boss interval")
        if (isinstance(self.prismatic_every, bool) or not isinstance(self.prismatic_every, int)
                or self.prismatic_every < 1):
            raise ValueError("invalid prismatic interval")
        if not isfinite(self.prismatic_health_multiplier) or self.prismatic_health_multiplier < 1:
            raise ValueError("invalid prismatic health multiplier")

    def enemy_budget(self, round_number: int) -> int:
        if self.enemy_growth == 1:
            return self.base_enemies
        exponent_limit = ceil(log(self.max_budget / self.base_enemies) / log(self.enemy_growth))
        exponent = min(max(0, round_number - 1), exponent_limit)
        return min(self.max_budget, max(1, round(self.base_enemies * self.enemy_growth ** exponent)))

    def health_multiplier(self, round_number: int) -> float:
        linear_rounds = self.health_exponential_start - 1
        linear_multiplier = 1.0 + self.health_per_round * min(
            max(0, round_number - 1), linear_rounds
        )
        exponential_rounds = max(0, round_number - self.health_exponential_start)
        return linear_multiplier * self.health_growth ** exponential_rounds

    def damage_multiplier(self, round_number: int) -> float:
        return 1.0 + self.damage_per_round * max(0, round_number - 1)

    def speed_multiplier(self, round_number: int) -> float:
        return min(self.max_speed_multiplier, 1.0 + self.speed_per_round * (round_number - 1))

    def timing_multiplier(self, round_number: int) -> float:
        if round_number < self.timing_reduction_start:
            return 1.0
        rounds_in = round_number - self.timing_reduction_start + 1
        return max(self.min_timing_multiplier, 1.0 - self.timing_reduction_per_round * rounds_in)

    def is_boss_round(self, round_number: int) -> bool:
        return self.boss_every > 0 and round_number % self.boss_every == 0

    def boss_health_multiplier(self, round_number: int) -> float:
        boss_index = max(1, round_number // max(1, self.boss_every))
        return self.boss_health_growth ** (boss_index - 1)

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

    def elite_chance(self, round_number: int) -> float:
        if round_number < self.elite_start_round:
            return 0.0
        rounds_in = round_number - self.elite_start_round
        return min(
            self.max_elite_chance,
            self.elite_start_chance + self.elite_chance_per_round * rounds_in,
        )


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
        self._prismatic_pending = False
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
            world.events.publish(RoundCompleted(self.round_number, world.last_kill_weapon))
            self.phase = Phase.INTERMISSION
            self.intermission_left = self.config.intermission

    def _start_round(self, world: World) -> None:
        self.round_number += 1
        self.pending = self.config.round_total(self.round_number)
        self.is_boss_round = self.config.is_boss_round(self.round_number)
        self._boss_pending = self.is_boss_round  # o boss é o primeiro a aparecer
        self._prismatic_pending = self.round_number % self.config.prismatic_every == 0
        self.phase = Phase.SPAWNING
        self._spawn_cooldown = 0.0
        world.events.publish(RoundStarted(self.round_number))

    def _spawn_one(self, world: World) -> None:
        cfg, n = self.config, self.round_number
        is_boss = self._boss_pending
        is_prismatic = not is_boss and self._prismatic_pending
        definition = BOSS if is_boss else self._pick_definition(world)
        is_elite = not is_boss and not is_prismatic and world.rng.random() < cfg.elite_chance(n)
        position = self._pick_spawn_point(world, definition)
        self._spawn_cooldown = (cfg.opening_spawn_interval if n <= cfg.opening_rounds
                                else cfg.spawn_interval)
        if position is None:
            # Sem posição segura agora: mantém o orçamento e volta a tentar depois.
            return
        world.spawn_enemy(
            definition, position, jitter=0,
            health_multiplier=(cfg.boss_health_multiplier(n) if is_boss else
                               cfg.health_multiplier(n) *
                               (cfg.prismatic_health_multiplier if is_prismatic else
                                cfg.elite_health_multiplier if is_elite else 1.0)),
            speed_multiplier=(1.0 if is_boss else cfg.speed_multiplier(n)),
            damage_multiplier=(1.0 if is_boss else cfg.damage_multiplier(n)),
            reward_multiplier=(1+cfg.boss_reward_per_boss*(n//max(1,cfg.boss_every)-1)
                               if is_boss else 1.0),
            xp_reward_multiplier=(cfg.elite_xp_multiplier if is_elite else 1.0),
            timing_multiplier=cfg.timing_multiplier(n),
            damage_cap_fraction=(None if is_boss else cfg.normal_damage_cap),
            is_elite=is_elite,
            is_prismatic=is_prismatic,
            lethal_attacks=is_boss,
        )
        self._boss_pending = False
        if is_prismatic:
            self._prismatic_pending = False
        self.pending -= 1

    def _pick_definition(self, world: World) -> EnemyDef:
        chance = self.config.red_chance(self.round_number)
        if chance > 0 and world.rng.random() < chance:
            return RED
        return BASIC

    def _pick_spawn_point(self, world: World, definition: EnemyDef) -> Vector2 | None:
        opening = self.round_number <= self.config.opening_rounds
        margin = (64 if opening else 96)+definition.radius
        candidates = world.map.spawn_candidates(world.player.position,
                                                self.config.min_spawn_distance,
                                                world.viewport, margin)
        def valid(points):
            return [point for point in points
                    if point.distance_to(world.player.position) >= self.config.min_spawn_distance
                    and world.can_spawn_at(point, definition.radius)]
        nearby = valid(candidates)
        if not nearby:
            # Junto de limites/obstáculos pode ser necessário um ponto fixo da arena.
            nearby = valid(world.map.spawn_points)
        if not nearby:
            return None
        if opening:
            direct = [point for point in nearby if world.line_of_sight(point, world.player.position)]
            nearby = direct or nearby
        closest = min(point.distance_to(world.player.position) for point in nearby)
        band = 120 if opening else 220
        close = [point for point in nearby if point.distance_to(world.player.position) <= closest+band]
        return Vector2(world.rng.choice(close))
