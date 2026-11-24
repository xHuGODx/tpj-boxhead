"""Estado das armas na partida: desbloqueios e reservas, sem input ou desenho."""
from boxhead.world.weapons import WeaponDef


class Arsenal:
    def __init__(self, weapons: tuple[WeaponDef, ...], owned_weapons: tuple[str, ...] = ("Pistol",)) -> None:
        self._weapons = {weapon.name: weapon for weapon in weapons}
        self._ammo = {weapon.name: weapon.starting_ammo for weapon in weapons
                      if weapon.name in owned_weapons}

    def is_unlocked(self, name: str) -> bool:
        return name in self._ammo

    def ammo(self, name: str) -> int:
        return self._ammo.get(name, 0)

    def consume(self, name: str) -> bool:
        if self.ammo(name) <= 0:
            return False
        self._ammo[name] -= 1
        return True

    def replenish(self) -> bool:
        """Uma caixa abastece cada arma desbloqueada; devolve se deu munições."""
        changed = False
        for name, current in self._ammo.items():
            weapon = self._weapons[name]
            amount = min(weapon.max_ammo, current + weapon.pickup_ammo)
            changed = changed or amount > current
            self._ammo[name] = amount
        return changed
