import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import tempfile
import unittest
from pathlib import Path

import pygame
from pygame import Vector2

from boxhead.world.training import TrainingWorld


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1100, 700))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_immortal_dummy_measures_real_bullets_and_burns(self):
        w = TrainingWorld()
        w.set_stack('ember_rounds', 1)
        target = w.enemies[0]
        position = Vector2(target.position)
        for _ in range(180):
            w.fire_held(1/60, True)
            w.update(1/60)
        self.assertTrue(target.alive)
        self.assertEqual(target.health, target.max_health)
        self.assertEqual(target.position, position)
        self.assertGreater(w.total_damage, 100)
        self.assertGreater(w.dps, 0)
        self.assertTrue(w.combat.burns)
        self.assertEqual(w.stats.coins, 0)
        self.assertEqual(w.progression.pending_choices, 0)

    def test_editing_recomputes_stats_and_clears_old_effects(self):
        w = TrainingWorld()
        w.set_stack('attack_damage', 3)
        w.set_stack('split_chamber', 2)
        w.set_stack('orbitals', 1)
        self.assertEqual(w.player.attack_damage, 160)
        self.assertEqual(w.player.modifiers.projectile_count, 3)
        self.assertIn('orbitals', w.behaviors)
        w.fire_held(.1, True)
        self.assertTrue(w.projectiles)
        w.set_stack('orbitals', 0)
        self.assertNotIn('orbitals', w.behaviors)
        self.assertFalse(w.projectiles)
        w.set_stack('attack_damage', 1)
        self.assertEqual(w.player.attack_damage, 120)
        w.clear_build()
        self.assertEqual(list(w.inventory.owned()), [])
        self.assertEqual(w.player.attack_damage, 100)
        self.assertEqual(w.player.modifiers.projectile_count, 1)
        self.assertFalse(w.behaviors)

    def test_incompatible_edit_is_atomic(self):
        w = TrainingWorld()
        w.set_stack('sprinter', 1)
        before = w.inventory
        with self.assertRaises(ValueError):
            w.set_stack('juggernaut', 1)
        self.assertIs(w.inventory, before)
        self.assertEqual(w.inventory.stacks('sprinter'), 1)
        self.assertEqual(w.inventory.stacks('juggernaut'), 0)

    def test_all_weapons_have_infinite_ammo_and_keep_build(self):
        w = TrainingWorld()
        w.set_stack('attack_damage', 2)
        for slot in range(3):
            w.select_weapon(slot)
            self.assertEqual(w.player.weapon_slot, slot)
            for _ in range(500):
                w.player._cooldowns[slot] = 0
                self.assertIsNotNone(w.player.try_fire())
            self.assertEqual(w.player.ammo, w.player.weapon.max_ammo)
            self.assertEqual(w.player.attack_damage, 140)

    def test_mortal_targets_support_kill_effects_respawn_and_no_rewards(self):
        w = TrainingWorld()
        w.start_listening()
        w.killable = True
        w.target_count = 3
        w.set_stack('chain_reaction', 50)
        w.damage_enemy(w.enemies[0], 1000)
        self.assertEqual(w.target_kills, 3)
        self.assertTrue(w.fx)
        for _ in range(60):
            w.update(1/60)
            w.events.dispatch()
        self.assertEqual(w.alive_enemy_count, 3)
        self.assertEqual(w.stats.coins, 0)
        self.assertEqual(w.progression.total_xp, 0)
        self.assertEqual(w.progression.pending_choices, 0)
        self.assertFalse(w.ammo_drops.pickups)
        self.assertIsNone(w.director)
        w.stop_listening()

    def test_editor_controls_pause_simulation_and_render(self):
        from boxhead.states.dev_arena import DevArenaState
        state = DevArenaState(None, lambda s: None, lambda: None)
        state.enter()
        state.query = 'Split Chamber'
        state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(state.world.inventory.stacks('split_chamber'), 1)
        state.update(2)
        self.assertEqual(state.world.elapsed, 0)
        surface = pygame.Surface((1100, 700))
        state.draw(surface)
        state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
        self.assertFalse(state.editor_open)
        state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        state.update(.1)
        self.assertGreater(state.world.elapsed, 0)
        state.draw(surface)
        state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
        self.assertFalse(state._pressed)
        state.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
        self.assertEqual(state.world.inventory.stacks('split_chamber'), 0)
        state.exit()

    def test_menu_entry_and_training_never_credit_profile(self):
        from boxhead.app import App
        from boxhead.config import AppConfig
        from boxhead.core.state import StateMachine
        from boxhead.states.dev_arena import DevArenaState
        with tempfile.TemporaryDirectory() as folder:
            app = App(AppConfig(profile_path=Path(folder)/'profile.json'))
            app.profile.balance = 123
            app._machine = StateMachine(app._make_menu())
            self.assertIn('Dev Arena', app._machine.current.labels)
            app._to_dev_arena()
            state = app._machine.current
            self.assertIsInstance(state, DevArenaState)
            self.assertIsNot(state.world.events, app._events)
            self.assertIsNone(app._active_world)
            state.world.stats.coins = 99999
            app._pause_training(state)
            app._resume(state)
            self.assertIs(app._machine.current, state)
            app._to_menu()
            app._finish_run()
            self.assertEqual(app.profile.balance, 123)
            self.assertFalse(list(Path(folder).glob('*.json')))
            app._machine.close()


if __name__ == '__main__':
    unittest.main()
