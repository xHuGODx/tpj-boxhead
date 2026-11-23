"""Caixas de munições: sorteio, duração e recolha, separados do combate/desenho."""
from dataclasses import dataclass
from math import isfinite
import random

from pygame import Vector2

from boxhead.core.geometry import circle_circle
from boxhead.world.arsenal import Arsenal


@dataclass(frozen=True)
class AmmoDropConfig:
    chance: float = 0.35
    lifetime: float = 60.0
    max_pickups: int = 100
    radius: float = 16.0

    def __post_init__(self) -> None:
        if not isfinite(self.chance) or not 0 <= self.chance <= 1:
            raise ValueError("ammo drop chance must be between 0 and 1")
        if any(not isfinite(v) or v <= 0 for v in (self.lifetime, self.radius)):
            raise ValueError("pickup lifetime and radius must be positive")
        if isinstance(self.max_pickups, bool) or not isinstance(self.max_pickups, int) or self.max_pickups < 1:
            raise ValueError("pickup limit must be a positive integer")


@dataclass
class AmmoPickup:
    position: Vector2
    ttl: float


class AmmoDrops:
    def __init__(self, config: AmmoDropConfig = AmmoDropConfig()) -> None:
        self.config = config
        self.pickups: list[AmmoPickup] = []

    def drop(self, position: Vector2, rng: random.Random) -> None:
        if rng.random() < self.config.chance:
            if len(self.pickups) >= self.config.max_pickups:
                self.pickups.pop(0)
            self.pickups.append(AmmoPickup(Vector2(position), self.config.lifetime))

    def update(self, dt: float, position: Vector2, radius: float, arsenal: Arsenal) -> bool:
        collected = False
        remaining = []
        for pickup in self.pickups:
            pickup.ttl -= dt
            if pickup.ttl <= 0:
                continue
            contact = circle_circle(position, radius, pickup.position, self.config.radius)
            if contact and arsenal.replenish():
                collected = True
            else:
                remaining.append(pickup)
        self.pickups = remaining
        return collected
