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
from boxhead.world.augments import (
    Effect, MaxHealth, MoveSpeed, XpGain, Regeneration, AttackDamage, AttackSpeed,
    StatBonus,
)


@dataclass(frozen=True)
class UpgradeDef:
    id: str
    name: str
    description: str  # efeito de cada nível
    effect: Effect | None  # None: compra de arma permanente
    max_level: int
    base_cost: int
    cost_growth: float
    weapon: str | None = None

    def cost(self, level: int) -> int:
        """Custo de comprar o nível seguinte, tendo já `level` níveis."""
        return max(1, round(self.base_cost * self.cost_growth**level))


# Valores iniciais (propostas, ajustáveis com playtests); ver docs/game-design.md.
UPGRADES: tuple[UpgradeDef, ...] = (
    UpgradeDef("split_chamber", "Split Chamber", "+1 projectile count for every salvo", StatBonus("projectile_count", 1), 1, 2500, 1),
    UpgradeDef("crit_chance", "Precision", "+5 percentage points of critical chance", StatBonus("crit_chance", .05), 5, 150, 1.6),
    UpgradeDef("crit_damage", "Dead Center", "+0.10 critical damage multiplier", StatBonus("crit_damage_bonus", .10), 5, 150, 1.6),
    UpgradeDef("blast_bloom", "Blast Bloom", "+10% explosion radius (not barrels)", StatBonus("blast_radius_bonus", .10), 5, 100, 1.5),
    UpgradeDef("max_health", "Max Health", "+10 max health per level", MaxHealth(10), 5, 50, 1.5),
    UpgradeDef("speed", "Movement Speed", "+4% movement speed per level", MoveSpeed(0.04), 5, 60, 1.5),
    UpgradeDef("xp_gain", "XP Gain", "+5% XP per level", XpGain(0.05), 5, 80, 1.6),
    UpgradeDef("regeneration", "Regeneration", "+0.25 health/s per level", Regeneration(0.25), 4, 100, 1.6),
    UpgradeDef("attack_damage", "Attack Damage", "+5 AD for all weapons per level", AttackDamage(5), 5, 70, 1.5),
    UpgradeDef("attack_speed", "Attack Speed", "+5% base attack speed per level", AttackSpeed(0.05), 5, 80, 1.5),
    UpgradeDef("weapon_smg", "Unlock SMG", "Permanent weapon - available from round 1", None, 1, 250, 1, "SMG"),
    UpgradeDef("weapon_shotgun", "Unlock Shotgun", "Permanent weapon - available from round 1", None, 1, 400, 1, "Shotgun"),
)
UPGRADES_BY_ID = {u.id: u for u in UPGRADES}


def owned_weapons(profile: Profile) -> tuple[str, ...]:
    return ("Pistol",) + tuple(u.weapon for u in UPGRADES
                              if u.weapon is not None and profile.level(u.id) > 0)


def refund_legacy_weapon_upgrades(profile: Profile) -> bool:
    """One-time refund of removed upgrades, using their original price curves."""
    changed = False
    for key, base, growth in (("pistol_damage", 70, 1.5), ("smg_damage", 90, 1.5),
                              ("shotgun_damage", 90, 1.5), ("shotgun_pellets", 150, 1.8)):
        if key in profile.upgrades:
            levels = profile.upgrades.pop(key)
            profile.credit(sum(max(1, round(base * growth**n)) for n in range(levels)))
            changed = True
    return changed


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

    Os níveis guardados acima do máximo atual contam só até ao máximo.
    """
    modifiers = Modifiers()
    for upgrade in upgrades:
        if upgrade.effect is None:
            continue
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
