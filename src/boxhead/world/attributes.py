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


@dataclass
class Modifiers:
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


def derive_weapon(base: WeaponDef, mods: WeaponModifiers) -> WeaponDef:
    """Arma efetiva; `base` é partilhada e imutável, por isso devolve uma cópia."""
    return replace(
        base,
        damage=base.damage * mods.damage_multiplier,
        cooldown=base.cooldown / mods.fire_rate_multiplier,
        pellets=base.pellets + mods.extra_pellets,
    )
