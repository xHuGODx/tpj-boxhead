"""Atributos derivados: base + modificadores, sempre recalculados do zero.

`Modifiers` descreve *quanto* os augments (e, mais tarde, a loja) alteram a base. Nunca
se escreve no jogador nem nas armas partilhadas: o valor efetivo é derivado a partir
da base imutável, por isso reaplicar não acumula efeitos já aplicados.

Unidades: multiplicadores somam-se em fração (+0,20 = +20 %), vida e pellets somam-se
em valor absoluto, regeneração é vida por segundo.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from boxhead.world.weapons import WeaponDef


@dataclass
class WeaponModifiers:
    damage_multiplier: float = 1.0
    fire_rate_multiplier: float = 1.0
    extra_pellets: int = 0
    range_multiplier: float = 1.0


@dataclass
class Modifiers:
    projectile_count: int = 1
    crit_chance: float = 0.0
    crit_damage_bonus: float = 0.0
    blast_radius_bonus: float = 0.0
    ember_rounds: int = 0
    slipstream_feed: int = 0
    last_spark: int = 0
    siege_stacks: int = 0
    redline: int = 0
    aftershot: int = 0
    attack_damage_bonus: float = 0.0
    attack_speed_bonus: float = 0.0
    max_health_bonus: float = 0.0
    speed_multiplier: float = 1.0
    regen_per_second: float = 0.0
    xp_gain_multiplier: float = 1.0
    weapons: dict[str, WeaponModifiers] = field(default_factory=dict)
    # Tipo de comportamento → nível (acumulações); ver `behaviors.BEHAVIOR_TYPES`.
    behaviors: dict[str, int] = field(default_factory=dict)

    def weapon(self, name: str) -> WeaponModifiers:
        """Modificadores de uma arma, criados se ainda não existirem (para os efeitos)."""
        return self.weapons.setdefault(name, WeaponModifiers())

    def for_weapon(self, name: str) -> WeaponModifiers:
        """Só leitura: não cria entradas."""
        return self.weapons.get(name) or WeaponModifiers()


def derive_weapon(base: WeaponDef, mods: WeaponModifiers,
                  attack_damage: float = 100.0, attack_speed: float = 1.0) -> WeaponDef:
    """Arma efetiva; `base` é partilhada e imutável, por isso devolve uma cópia."""
    return replace(
        base,
        damage=base.damage * max(0.1, mods.damage_multiplier) * max(0.1, attack_damage / 100),
        cooldown=base.cooldown / (max(0.1, mods.fire_rate_multiplier) * max(0.1, attack_speed)),
        pellets=max(1, base.pellets + mods.extra_pellets),
        projectile_range=base.projectile_range * max(0.1, mods.range_multiplier),
    )
