"""Projétil: estado de uma bala em voo; a deteção de acertos é feita pelo `World`."""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Vector2


@dataclass(eq=False)
class Projectile:
    position: Vector2
    velocity: Vector2
    damage: float
    radius: float
    range_left: float
    color: tuple[int, int, int] = (255, 220, 120)
    sprite_key: str = "projectiles/player_bullet.png"
    owner_id: int | None = None
    hostile: bool = False  # True: disparado por inimigos; só acerta no jogador
    damage_cap_fraction: float | None = None  # limite relativo à vida máxima do jogador
    lethal: bool = False  # ataques de boss ignoram o limite e matam ao acertar
    alive: bool = True
    bounces_left: int = 0  # saltos que ainda pode dar (augment Ricochet)
    hit_ids: set[int] = field(default_factory=set)  # alvos já acertados: não repete o mesmo
    weapon_name: str | None = None  # arma de origem; trocar de arma não muda a autoria
    primary: bool = True
    critical: bool = False
    first_step: float | None = None
    blast_damage: float = 0.0
    blast_radius: float = 0.0
