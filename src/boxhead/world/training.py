"""Isolated combat sandbox; uses live combat rules without persistent rewards."""
from dataclasses import replace

from pygame import Rect, Vector2

from boxhead.world.arsenal import Arsenal
from boxhead.world.augments import AUGMENTS_BY_ID, AugmentInventory
from boxhead.world.combat import CombatEffects
from boxhead.world.enemy import BASIC, EnemyState
from boxhead.world.map import ARENA
from boxhead.world.player import Player
from boxhead.world.world import World


TRAINING_MAP = replace(
    ARENA, name="Dev Arena", bounds=Rect(-768, -576, 1536, 1152),
    obstacles=(), decorations=(), player_start=Vector2(0, 180),
)
DUMMY = replace(BASIC, name="Training Dummy", max_health=1000,
                speed=0, contact_damage=0, xp_reward=0, coin_reward=0)


class DummyIdle(EnemyState):
    name = "training"
    visual = "recover"

    def update(self, enemy, dt, target):
        return None


class TrainingArsenal(Arsenal):
    def ammo(self, name):
        return self._weapons[name].max_ammo if self.is_unlocked(name) else 0

    def consume(self, name):
        return self.is_unlocked(name)


class TrainingWorld(World):
    def __init__(self, *, viewport=(1100, 700)):
        player = Player(position=Vector2(TRAINING_MAP.player_start),
                        orientation=Vector2(0, -1),
                        owned_weapons=("Pistol", "SMG", "Shotgun"))
        super().__init__(map=TRAINING_MAP, player=player, rounds=None, viewport=viewport)
        self.player.arsenal = TrainingArsenal(player.weapons, player.owned_weapons)
        self.killable = False
        self.target_count = 1
        self.reset_meter()
        self.reset_targets()

    def reset_meter(self):
        self.total_damage = 0.0
        self.last_damage = 0.0
        self.highest_damage = 0.0
        self.first_damage_at = None
        self.target_kills = 0

    @property
    def dps(self):
        if self.first_damage_at is None:
            return 0.0
        return self.total_damage / max(.1, self.elapsed - self.first_damage_at)

    def reset_targets(self):
        self.enemies.clear()
        self.corpses.clear()
        self.projectiles.clear()
        self.fx.clear()
        self.ammo_drops.pickups.clear()
        self.bodies.clear()
        self.combat = CombatEffects()
        self.player.temporary_as = self.player.temporary_move = 0.0
        self.behaviors.clear()
        self._sync_behaviors()
        self._respawn_at = None
        for i in range(self.target_count):
            x = (i - (self.target_count - 1) / 2) * 74
            enemy = self.spawn_enemy(DUMMY, Vector2(x, 20), jitter=0)
            enemy.change_state(DummyIdle())
        self.rebuild_spatial_index()

    def reset_test(self):
        self.reset_meter()
        self.reset_targets()
        self.player._cooldowns = [0.0] * len(self.player.weapons)

    def set_stack(self, augment_id, count):
        """Rebuild from base when editing; old burns/echoes never leak into a test."""
        augment = AUGMENTS_BY_ID[augment_id]
        desired = {a.id: (a, n) for a, n in self.inventory.owned()}
        if count > 0:
            desired[augment_id] = (augment, count)
        else:
            desired.pop(augment_id, None)
        candidate = AugmentInventory()
        weapons = self.player.owned_weapons
        pending = list(desired.values())
        while pending:
            added = False
            for item in pending[:]:
                a, n = item
                if candidate.is_eligible(a, weapons):
                    for _ in range(n):
                        candidate.add(a, weapons)
                    pending.remove(item)
                    added = True
            if not added:
                raise ValueError("Incompatible augments or missing prerequisite.")
        self.inventory = candidate
        self.player.set_modifiers(candidate.modifiers)
        self.player.health = self.player.max_health
        self.reset_test()

    def clear_build(self):
        self.inventory = AugmentInventory()
        self.player.set_modifiers(self.inventory.modifiers)
        self.player.health = self.player.max_health
        self.player.revivals_used = 0
        self.reset_test()

    def select_weapon(self, slot):
        self.player.weapon_slot = slot % len(self.player.weapons)
        self.reset_test()

    def _update_enemy(self, enemy, dt):
        # Dummies stay fixed, never chase, attack or push each other around.
        pass

    def damage_enemy(self, enemy, amount, chain_depth=0, *, weapon_name=None):
        if not enemy.alive or amount <= 0:
            return False
        if self.first_damage_at is None:
            self.first_damage_at = self.elapsed
        self.total_damage += amount
        self.last_damage = amount
        self.highest_damage = max(self.highest_damage, amount)
        if not self.killable:
            return False
        killed = super().damage_enemy(enemy, amount, chain_depth, weapon_name=weapon_name)
        if killed:
            self.target_kills += 1
        return killed

    def update(self, dt):
        super().update(dt)
        # No XP, level-up choices, loot, or currency comes out of this sandbox.
        self.events.clear()
        self.ammo_drops.pickups.clear()
        self.player.health = self.player.max_health
        if not self.enemies:
            if self._respawn_at is None:
                self._respawn_at = self.elapsed + .75
            elif self.elapsed >= self._respawn_at:
                self.reset_targets()
