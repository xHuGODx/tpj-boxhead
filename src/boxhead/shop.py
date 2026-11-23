"""Loja do menu: melhorias permanentes compradas com a moeda do perfil (#18).

Regras puras, sem pygame e sem estado global: `buy` altera o perfil e
`profile_modifiers` calcula, do zero, a base de uma partida nova a partir dele. Só as
compras feitas aqui mexem no perfil; obter um augment durante a partida nunca o faz.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from boxhead.profile import Profile, ProfileStore
from boxhead.world.attributes import Modifiers
from boxhead.world.augments import Effect, MaxHealth, MoveSpeed, XpGain


@dataclass(frozen=True)
class UpgradeDef:
    id: str
    name: str
    description: str  # efeito de cada nível
    effect: Effect  # aplicado uma vez por nível comprado
    max_level: int
    base_cost: int
    cost_growth: float

    def cost(self, level: int) -> int:
        """Custo de comprar o nível seguinte, tendo já `level` níveis."""
        return max(1, round(self.base_cost * self.cost_growth**level))


# Valores iniciais (propostas, ajustáveis com playtests); ver docs/game-design.md.
UPGRADES: tuple[UpgradeDef, ...] = (
    UpgradeDef("max_health", "Vida máxima", "+10 vida máxima por nível", MaxHealth(10), 5, 50, 1.5),
    UpgradeDef("speed", "Velocidade", "+4% velocidade por nível", MoveSpeed(0.04), 5, 60, 1.5),
    UpgradeDef("xp_gain", "Ganho de XP", "+5% XP por nível", XpGain(0.05), 5, 80, 1.6),
)
UPGRADES_BY_ID = {u.id: u for u in UPGRADES}


class PurchaseResult(Enum):
    BOUGHT = "bought"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    MAX_LEVEL = "max_level"
    UNKNOWN = "unknown"
    SAVE_FAILED = "save_failed"


def buy(
    profile: Profile, upgrade_id: str, upgrades: tuple[UpgradeDef, ...] = UPGRADES
) -> PurchaseResult:
    """Compra o nível seguinte; não altera nada se não for possível."""
    upgrade = next((u for u in upgrades if u.id == upgrade_id), None)
    if upgrade is None:
        return PurchaseResult.UNKNOWN
    level = profile.level(upgrade.id)
    if level >= upgrade.max_level:
        return PurchaseResult.MAX_LEVEL
    cost = upgrade.cost(level)
    if profile.balance < cost:
        return PurchaseResult.INSUFFICIENT_FUNDS
    profile.balance -= cost
    profile.upgrades[upgrade.id] = level + 1
    return PurchaseResult.BOUGHT


def profile_modifiers(profile: Profile, upgrades: tuple[UpgradeDef, ...] = UPGRADES) -> Modifiers:
    """Base de uma partida nova: calculada do zero a cada chamada, nunca acumulada.

    Os níveis guardados acima do máximo atual (p. ex. se o limite descer) contam só até ao máximo.
    """
    modifiers = Modifiers()
    for upgrade in upgrades:
        for _ in range(min(profile.level(upgrade.id), upgrade.max_level)):
            upgrade.effect.apply(modifiers)
    return modifiers


def purchase(profile: Profile, store: ProfileStore, upgrade_id: str,
             upgrades: tuple[UpgradeDef, ...] = UPGRADES) -> PurchaseResult:
    """Valida, guarda uma cópia e confirma. Uma falha mantém saldo e níveis."""
    from copy import deepcopy
    candidate = deepcopy(profile)
    result = buy(candidate, upgrade_id, upgrades)
    if result is PurchaseResult.BOUGHT:
        try:
            store.commit(profile, candidate)
        except OSError:
            return PurchaseResult.SAVE_FAILED
    return result
