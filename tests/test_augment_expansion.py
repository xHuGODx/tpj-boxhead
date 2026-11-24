"""Regression checks for proc interactions, timing, progression and icon coverage."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import pygame
from pygame import Rect, Vector2

from boxhead.core.events import EventQueue, PlayerDied
from boxhead.presentation.icons import augment_icon, shop_icon
from boxhead.profile import Profile, ProfileStore
from boxhead.shop import UPGRADES, PurchaseResult, purchase, profile_modifiers
from boxhead.world.attributes import Modifiers
from boxhead.world.augments import AUGMENTS, AUGMENTS_BY_ID, Offer, Rarity
from boxhead.world.enemy import BASIC
from boxhead.world.map import ARENA, ObstacleDef
from boxhead.world.player import Player
from boxhead.world.projectile import Projectile
from boxhead.world.weapons import WEAPONS
from boxhead.world.world import World


def world(mods=None, weapon="Pistol", obstacles=()):
    definition = replace(ARENA, obstacles=obstacles, player_start=Vector2())
    slot = next(i for i, w in enumerate(WEAPONS) if w.name == weapon)
    return World(map=definition, player=Player(owned_weapons=(weapon,), weapon_slot=slot),
                 base_modifiers=mods, rounds=None, rng=random.Random(7))


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1100, 700))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_salvo_counts_ammo_and_parallel_offsets(self):
        for name, base in (("Pistol", 1), ("SMG", 1), ("Shotgun", 6)):
            for count in (1, 2, 3):
                w = world(Modifiers(projectile_count=count), name)
                before = w.player.ammo
                w.fire_held(0, True)
                self.assertEqual(len(w.projectiles), base*count)
                self.assertEqual(w.player.ammo, before-1)
                if name != "Shotgun":
                    self.assertEqual(len({tuple(p.position) for p in w.projectiles}), count)
                    self.assertTrue(all(p.velocity == w.projectiles[0].velocity for p in w.projectiles))

    def test_crit_overflow_and_echo_snapshot(self):
        w = world(Modifiers(crit_chance=1.1, crit_damage_bonus=.15, aftershot=2,
                            projectile_count=2))
        w.fire_held(0, True)
        self.assertTrue(all(p.critical for p in w.projectiles))
        self.assertAlmostEqual(w.projectiles[0].damage, 25*2.2)
        self.assertEqual(len(w.combat.echoes), 2)
        w.player.position = Vector2(100, 100)
        w.elapsed = .2; w.combat.update(w)
        echoes = [p for p in w.projectiles if not p.primary]
        self.assertEqual(len(echoes), 2)
        self.assertTrue(all(not p.critical and p.damage == 10 for p in echoes))
        self.assertTrue(all(p.position.y > 100 for p in echoes))
        self.assertEqual(len(w.combat.echoes), 1)

    def test_burn_damage_and_secondary_proc_exclusion(self):
        w = world(Modifiers(ember_rounds=1, slipstream_feed=1, redline=1))
        enemy = w.spawn_enemy(BASIC, Vector2(400, 0), health_multiplier=20, jitter=0)
        p = Projectile(Vector2(), Vector2(0, 1), 10, 2, 100, critical=True)
        w.combat.hit(w, p, enemy)
        self.assertEqual(w.combat.slip_hits, 1)
        self.assertEqual(w.combat.rhythm_hits, 1)
        w.combat.hit(w, replace(p, primary=False), enemy)
        self.assertEqual(w.combat.slip_hits, 1)
        for t in (1., 2., 3., 4.):
            w.elapsed=t; w.combat.update(w)
        self.assertAlmostEqual(enemy.health, 994)
        self.assertFalse(w.combat.burns)
        self.assertEqual(w.combat.rhythm_hits, 0)
        w.elapsed=5; w.combat.refresh(w)
        self.assertEqual(w.player.temporary_move, 0)

    def test_temporary_as_conversion_and_expiry(self):
        w = world(Modifiers(speed_multiplier=1.4, attack_speed_bonus=.5, slipstream_feed=1))
        self.assertAlmostEqual(w.player.attack_speed, 1.7)
        e = w.spawn_enemy(BASIC, Vector2(400, 0), jitter=0)
        p = Projectile(Vector2(), Vector2(1,0), 1, 1, 50)
        w.combat.hit(w,p,e)
        w.elapsed=4; w.combat.hit(w,p,e)
        w.elapsed=5; w.combat.refresh(w)
        self.assertEqual(w.combat.slip_hits,2)
        w.elapsed=9; w.combat.refresh(w)
        self.assertEqual(w.combat.slip_hits,0)

    def test_revival_once_per_frame_and_no_next_frame_immunity(self):
        w = world(Modifiers(last_spark=2))
        deaths=[]; w.events.subscribe(PlayerDied,deaths.append)
        for _ in range(3):
            w.player.take_damage(1000)
        w.update(.01)
        self.assertEqual(w.player.revivals_left,1)
        self.assertEqual(w.player.health,50)
        w.player.set_modifiers(w.inventory.modifiers)
        self.assertEqual(w.player.revivals_left,1)
        w.player.take_damage(1000); w.update(.01)
        self.assertEqual(w.player.revivals_left,0)
        w.player.take_damage(1000); w.update(.01); w.events.dispatch()
        self.assertEqual(len(deaths),1)

    def test_rate_above_frame_rate_and_no_idle_debt(self):
        counts=[]
        for fps in (30,120):
            w=world(Modifiers(attack_speed_bonus=99),"SMG")
            w.player.arsenal._ammo['SMG']=10000
            for _ in range(fps):
                w.fire_held(1/fps,True)
            counts.append(10000-w.player.ammo)
        self.assertLessEqual(abs(counts[0]-counts[1]),1)
        self.assertGreater(counts[0],1000)
        w.fire_held(100,False)
        w.projectiles.clear(); w.fire_held(0,True)
        self.assertEqual(len(w.projectiles),1)

    def test_cover_blocks_parallel_muzzle_offsets(self):
        wall=ObstacleDef(Rect(-40,24,80,80),0)
        w=world(Modifiers(projectile_count=3),obstacles=(wall,))
        w.fire_held(0,True)
        self.assertEqual(len(w.projectiles),0)

    def test_siege_growth_and_revalidation(self):
        w=world(Modifiers(max_health_bonus=25, attack_damage_bonus=20))
        a=AUGMENTS_BY_ID['siege_frame']
        w.progression.reward_prismatic('Boss')
        w._offer=Offer((a,),Rarity.PRISMATIC,Rarity.PRISMATIC)
        w.choose_augment(a)
        self.assertAlmostEqual(w.player.max_health,162.5)
        self.assertAlmostEqual(w.player.attack_damage,138)
        self.assertAlmostEqual(w.player.radius,25.2)
        # Fully obstructed map must reject growth without consuming the choice.
        w.map.obstacles=(ObstacleDef(Rect(-2048,-1536,4096,3072),0),)
        w.progression.reward_prismatic('Boss'); w._offer=Offer((a,),Rarity.PRISMATIC,Rarity.PRISMATIC)
        with self.assertRaises(ValueError): w.choose_augment(a)
        self.assertEqual(w.inventory.stacks(a.id),1)
        self.assertEqual(w.progression.pending_choices,1)

    def test_shop_persistence_and_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            s=ProfileStore(Path(folder)/'profile.json'); p=Profile(balance=100000)
            for key in ('split_chamber','crit_chance','crit_damage','blast_bloom'):
                u=next(u for u in UPGRADES if u.id==key)
                for _ in range(u.max_level):
                    self.assertIs(purchase(p,s,key),PurchaseResult.BOUGHT)
                self.assertIs(purchase(p,s,key),PurchaseResult.MAX_LEVEL)
            m=profile_modifiers(s.load().profile)
            self.assertEqual(m.projectile_count,2)
            self.assertAlmostEqual(m.crit_chance,.25)
            self.assertAlmostEqual(m.crit_damage_bonus,.5)
            self.assertAlmostEqual(m.blast_radius_bonus,.5)

    def test_every_icon_and_screen(self):
        from boxhead.states.playing import PlayingState
        from boxhead.states.shop import ShopState
        from boxhead.presentation.augment_cards import AugmentCards
        from boxhead.core.catalog import catalog
        screen=pygame.display.get_surface()
        w=world(); state=PlayingState(None,w.events,lambda s:None,lambda w:None,world=w)
        state.enter(); state.update(.01); state.draw(screen)
        cards=AugmentCards()
        for a in AUGMENTS:
            key,index=augment_icon(a.id)
            self.assertLess(index,len(catalog().sheet(key).animation().frames))
            cards.draw(screen,w,Offer((a,),a.rarity,a.rarity),0,False)
        shop=ShopState(Profile(),lambda:None,lambda key:PurchaseResult.BOUGHT)
        shop.enter()
        for i,u in enumerate(UPGRADES):
            key,index=shop_icon(u.id)
            self.assertLess(index,len(catalog().sheet(key).animation().frames))
            shop._cursor=i; shop.draw(screen)

    def test_actual_critical_ricochet_applies_burn_to_each_target(self):
        w=world(Modifiers(crit_chance=1,ember_rounds=1,slipstream_feed=1,redline=1))
        w.inventory.add(AUGMENTS_BY_ID['ricochet'],['Pistol'])
        w.player.set_modifiers(w.inventory.modifiers); w._sync_behaviors()
        first=w.spawn_enemy(BASIC,Vector2(0,100),health_multiplier=20,jitter=0)
        second=w.spawn_enemy(BASIC,Vector2(100,100),health_multiplier=20,jitter=0)
        w.rebuild_spatial_index(); w.fire_held(0,True)
        # Clear the zero-time first-step marker so we can advance this isolated shot.
        p=w.projectiles[0]; p.first_step=None
        w._advance_projectile(p,.15)
        self.assertTrue(p.alive)
        self.assertAlmostEqual(first.health,950)
        self.assertTrue(p.critical)
        w._advance_projectile(p,.2)
        self.assertAlmostEqual(second.health,960)
        self.assertEqual(len(w.combat.burns),2)
        self.assertEqual(w.combat.rhythm_hits,2)

    def test_blast_bloom_excludes_environment_and_empty_frames_bank_nothing(self):
        from boxhead.world.behaviors import ChainReaction
        w=world(Modifiers(blast_radius_bonus=.5))
        enemy=w.spawn_enemy(BASIC,Vector2(500,0),jitter=0)
        ChainReaction(1).on_kill(w,enemy,0)
        self.assertEqual(w.fx[-1].radius,120)
        barrel=ObstacleDef(Rect(900,900,80,80),2,True)
        w.map.obstacles=(barrel,)
        w.damage_barrel(barrel,w.barrel_max_health)
        self.assertEqual(w.fx[-1].radius,180)
        w.player.arsenal._ammo['Pistol']=0
        w.fire_held(100,True)
        w.player.arsenal.replenish(); w.projectiles.clear()
        w.fire_held(0,True)
        self.assertEqual(len(w.projectiles),1)

    def test_explosive_rounds_direct_splash_and_no_secondary_procs(self):
        w=world(Modifiers(rupture_rounds=1,aftershot=1,ember_rounds=1))
        first=w.spawn_enemy(BASIC,Vector2(0,100),health_multiplier=20,jitter=0)
        near=w.spawn_enemy(BASIC,Vector2(60,100),health_multiplier=20,jitter=0)
        far=w.spawn_enemy(BASIC,Vector2(400,100),health_multiplier=20,jitter=0)
        w.rebuild_spatial_index(); w.fire_held(0,True)
        p=w.projectiles[0]; p.first_step=None
        w._advance_projectile(p,.15)
        self.assertAlmostEqual(first.health,965) # 25 direct + 10 splash
        self.assertAlmostEqual(near.health,990)
        self.assertAlmostEqual(far.health,1000)
        self.assertEqual(len(w.combat.burns),1) # splash does not apply Ember
        self.assertEqual(sum(f.kind=='round_explosion' for f in w.fx),1)
        self.assertEqual(w.player.health,100) # bullet splash has no friendly fire
        w.elapsed=.2; w.combat.update(w)
        echo=next(p for p in w.projectiles if not p.primary)
        self.assertEqual(echo.blast_damage,0)
        before=len(w.fx); w.detonate_round(echo,Vector2(0,100))
        self.assertEqual(len(w.fx),before)

    def test_explosive_round_snapshot_scaling_and_barrels(self):
        barrel=ObstacleDef(Rect(120,60,80,80),2,True)
        w=world(Modifiers(rupture_rounds=2,attack_damage_bonus=100,blast_radius_bonus=.5),
                obstacles=(barrel,))
        w.fire_held(0,True); p=w.projectiles[0]
        self.assertEqual(p.blast_damage,40)
        self.assertEqual(p.blast_radius,150)
        w.player.set_modifiers(Modifiers())
        w.detonate_round(p,Vector2(100,100))
        self.assertEqual(w.barrel_health(barrel),10)
        self.assertEqual(w.fx[-1].kind,'round_explosion')
        self.assertEqual(w.fx[-1].radius,150)


if __name__ == '__main__':
    unittest.main()
