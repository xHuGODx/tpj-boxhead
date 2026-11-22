"""Augments: dados (catálogo) + efeitos plugáveis + sorteio de ofertas.

Um augment é só dados e um `Effect`; acrescentar comportamentos novos (os prismáticos
de #15) é acrescentar uma classe `Effect` e uma entrada no catálogo, sem tocar no
jogador nem nas armas e sem cadeias de `if augment_id == ...`.
"""

from __future__ import annotations

import copy
import random
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from boxhead.world.attributes import Modifiers
from boxhead.world.behaviors import BEHAVIOR_TYPES


class Rarity(Enum):
    GRAY = "gray"  # atributos de uma arma
    GOLD = "gold"  # atributos mais fortes da personagem
    PRISMATIC = "prismatic"  # mecânicas distintas (#15)


class Effect(Protocol):
    """Altera `Modifiers` uma vez por acumulação do augment."""

    def apply(self, modifiers: Modifiers) -> None: ...


# --- efeitos -----------------------------------------------------------------------


@dataclass(frozen=True)
class WeaponDamage:
    weapon: str
    amount: float  # fração: 0,20 = +20 %

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.weapon(self.weapon).damage_multiplier += self.amount


@dataclass(frozen=True)
class WeaponFireRate:
    weapon: str
    amount: float

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.weapon(self.weapon).fire_rate_multiplier += self.amount


@dataclass(frozen=True)
class WeaponPellets:
    weapon: str
    count: int

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.weapon(self.weapon).extra_pellets += self.count


@dataclass(frozen=True)
class MaxHealth:
    amount: float

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.max_health_bonus += self.amount


@dataclass(frozen=True)
class MoveSpeed:
    amount: float

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.speed_multiplier += self.amount


@dataclass(frozen=True)
class Regeneration:
    per_second: float

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.regen_per_second += self.per_second


@dataclass(frozen=True)
class XpGain:
    amount: float

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.xp_gain_multiplier += self.amount


@dataclass(frozen=True)
class GrantBehavior:
    """Concede (ou melhora) um comportamento plugável; ver `behaviors.BEHAVIOR_TYPES`."""

    kind: str

    def __post_init__(self) -> None:
        if self.kind not in BEHAVIOR_TYPES:  # falha ao definir, não a meio de uma partida
            raise ValueError(f"comportamento desconhecido: {self.kind!r}")

    def apply(self, modifiers: Modifiers) -> None:
        modifiers.behaviors[self.kind] = modifiers.behaviors.get(self.kind, 0) + 1


# --- definições --------------------------------------------------------------------


@dataclass(frozen=True)
class Augment:
    id: str
    name: str
    description: str
    rarity: Rarity
    effect: Effect
    max_stacks: int = 1
    weapon: str | None = None  # só é oferecido se a arma estiver disponível
    requires: tuple[str, ...] = ()  # ids que o jogador já tem de possuir
    incompatible_with: tuple[str, ...] = ()  # ids que impedem a oferta


def _gray(id: str, weapon: str, name: str, description: str, effect: Effect, max_stacks: int, **kw):
    return Augment(
        id, f"{weapon}: {name}", description, Rarity.GRAY, effect, max_stacks, weapon, **kw
    )


def _gold(id: str, name: str, description: str, effect: Effect, max_stacks: int, **kw):
    return Augment(id, name, description, Rarity.GOLD, effect, max_stacks, **kw)


AUGMENTS: tuple[Augment, ...] = (
    # Cinzentos: atributos de uma arma.
    _gray("pistol_damage", "Pistol", "Heavy Rounds", "+20% dano", WeaponDamage("Pistol", 0.20), 5),
    _gray(
        "pistol_rate", "Pistol", "Hair Trigger", "+15% cadência", WeaponFireRate("Pistol", 0.15), 5
    ),
    _gray(
        "shotgun_pellets", "Shotgun", "Extra Pellet", "+1 projétil", WeaponPellets("Shotgun", 1), 4
    ),
    _gray("shotgun_damage", "Shotgun", "Slug Load", "+15% dano", WeaponDamage("Shotgun", 0.15), 5),
    _gray(
        "shotgun_rate",
        "Shotgun",
        "Pump Action",
        "+15% cadência (requer Slug Load)",
        WeaponFireRate("Shotgun", 0.15),
        4,
        requires=("shotgun_damage",),
    ),
    _gray("smg_rate", "SMG", "Overclock", "+12% cadência", WeaponFireRate("SMG", 0.12), 5),
    _gray("smg_damage", "SMG", "Hot Loads", "+15% dano", WeaponDamage("SMG", 0.15), 5),
    # Dourados: atributos mais fortes da personagem.
    _gold("vitality", "Vitality", "+25 vida máxima", MaxHealth(25), 4),
    _gold("swift", "Swift", "+12% velocidade", MoveSpeed(0.12), 4),
    _gold("regeneration", "Regeneration", "+1,5 vida/s", Regeneration(1.5), 3),
    _gold("quick_learner", "Quick Learner", "+15% XP", XpGain(0.15), 4),
    _gold(
        "juggernaut",
        "Juggernaut",
        "+60 vida máxima (exclusivo com Sprinter)",
        MaxHealth(60),
        1,
        incompatible_with=("sprinter",),
    ),
    _gold(
        "sprinter",
        "Sprinter",
        "+25% velocidade (exclusivo com Juggernaut)",
        MoveSpeed(0.25),
        1,
        incompatible_with=("juggernaut",),
    ),
    # Prismáticos: mecânicas distintas, concedidas como comportamentos plugáveis.
    Augment(
        "ricochet",
        "Ricochet",
        "As balas saltam para o inimigo mais próximo (+1 salto por acumulação)",
        Rarity.PRISMATIC,
        GrantBehavior("ricochet"),
        3,
    ),
    Augment(
        "chain_reaction",
        "Chain Reaction",
        "Os inimigos explodem ao morrer e ferem os vizinhos (mais raio e dano por acumulação)",
        Rarity.PRISMATIC,
        GrantBehavior("chain_reaction"),
        3,
    ),
    Augment(
        "orbitals",
        "Orbital Satellites",
        "Satélites orbitam o jogador e ferem quem tocam (+1 satélite por acumulação)",
        Rarity.PRISMATIC,
        GrantBehavior("orbitals"),
        3,
    ),
)

AUGMENTS_BY_ID: dict[str, Augment] = {a.id: a for a in AUGMENTS}


# --- inventário da partida ---------------------------------------------------------


class AugmentInventory:
    """Augments adquiridos nesta partida e os `Modifiers` que resultam deles.

    Os modificadores são sempre recalculados a partir de `base` (a base da partida,
    onde a loja vai aplicar as melhorias permanentes), por isso adquirir um augment
    nunca volta a aplicar efeitos já aplicados.
    """

    def __init__(self, base: Modifiers | None = None) -> None:
        self._base = base if base is not None else Modifiers()
        # Guarda os próprios `Augment` (não só ids): funciona com augments fora do catálogo
        # global, como os prismáticos de #15 ou os definidos em testes.
        self._owned: dict[str, tuple[Augment, int]] = {}
        self._modifiers = self._compute()

    @property
    def modifiers(self) -> Modifiers:
        return self._modifiers

    def stacks(self, augment_id: str) -> int:
        entry = self._owned.get(augment_id)
        return entry[1] if entry else 0

    def owned(self) -> Iterator[tuple[Augment, int]]:
        """Por ordem de aquisição."""
        yield from self._owned.values()

    def is_eligible(self, augment: Augment, available_weapons: Iterable[str]) -> bool:
        if self.stacks(augment.id) >= augment.max_stacks:
            return False
        if augment.weapon is not None and augment.weapon not in set(available_weapons):
            return False
        if any(self.stacks(required) == 0 for required in augment.requires):
            return False
        return not any(self.stacks(other) > 0 for other in augment.incompatible_with)

    def add(self, augment: Augment, available_weapons: Iterable[str]) -> None:
        if not self.is_eligible(augment, available_weapons):
            raise ValueError(f"augment não elegível: {augment.id}")
        self._owned[augment.id] = (augment, self.stacks(augment.id) + 1)
        self._modifiers = self._compute()

    def _compute(self) -> Modifiers:
        modifiers = copy.deepcopy(self._base)
        for augment, stacks in self.owned():
            for _ in range(stacks):
                augment.effect.apply(modifiers)
        return modifiers


# --- oferta ------------------------------------------------------------------------


@dataclass(frozen=True)
class OfferConfig:
    """Probabilidades iniciais (propostas, ajustáveis com playtests): 60/30/10."""

    weights: tuple[tuple[Rarity, float], ...] = (
        (Rarity.GRAY, 60),
        (Rarity.GOLD, 30),
        (Rarity.PRISMATIC, 10),
    )
    size: int = 3
    # Se a raridade sorteada não tiver opções suficientes, tenta estas por ordem.
    fallback: tuple[tuple[Rarity, tuple[Rarity, ...]], ...] = (
        (Rarity.GRAY, (Rarity.GOLD, Rarity.PRISMATIC)),
        (Rarity.GOLD, (Rarity.GRAY, Rarity.PRISMATIC)),
        (Rarity.PRISMATIC, (Rarity.GOLD, Rarity.GRAY)),
    )


DEFAULT_OFFER = OfferConfig()


@dataclass(frozen=True)
class Offer:
    choices: tuple[Augment, ...]
    rolled: Rarity  # raridade sorteada
    used: Rarity | None  # raridade realmente usada; None = oferta mista (fallback final)


def draw_offer(
    catalog: Sequence[Augment],
    inventory: AugmentInventory,
    available_weapons: Iterable[str],
    rng: random.Random,
    config: OfferConfig = DEFAULT_OFFER,
) -> Offer:
    """Sorteia uma raridade e apresenta `size` augments distintos dessa raridade.

    Fallback, por ordem:
      1. a raridade sorteada, se tiver `size` opções elegíveis;
      2. a primeira raridade da sua cadeia de fallback com `size` opções;
      3. oferta mista: as opções elegíveis disponíveis, a começar pela raridade sorteada
         e seguindo a cadeia, até `size`;
      4. sem nenhuma opção elegível: oferta vazia (quem chama dispensa a escolha).
    Nunca devolve uma escolha impossível, nem repetidos.
    """
    weapons = tuple(available_weapons)
    by_rarity: dict[Rarity, list[Augment]] = {r: [] for r in Rarity}
    for augment in catalog:
        if inventory.is_eligible(augment, weapons):
            by_rarity[augment.rarity].append(augment)

    rarities = [r for r, _ in config.weights]
    rolled = rng.choices(rarities, weights=[w for _, w in config.weights])[0]
    order = [rolled, *dict(config.fallback).get(rolled, ())]

    for rarity in order:
        pool = by_rarity[rarity]
        if len(pool) >= config.size:
            return Offer(tuple(rng.sample(pool, config.size)), rolled, rarity)

    choices: list[Augment] = []
    for rarity in order:
        pool = list(by_rarity[rarity])
        rng.shuffle(pool)
        choices.extend(pool[: config.size - len(choices)])
        if len(choices) == config.size:
            break
    return Offer(tuple(choices), rolled, None)


__all__ = [
    "AUGMENTS",
    "AUGMENTS_BY_ID",
    "DEFAULT_OFFER",
    "Augment",
    "AugmentInventory",
    "Effect",
    "Offer",
    "OfferConfig",
    "Rarity",
    "draw_offer",
]
