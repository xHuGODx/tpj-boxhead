import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from dataclasses import replace
import pygame
from pygame import Rect,Vector2

from boxhead.core.events import EnemyKilled
from boxhead.world.enemy import BASIC,RED,BOSS,RAGE_BASIC,RangedAttackState
from boxhead.world.map import ARENA,ObstacleDef
from boxhead.world.player import SPEED
from boxhead.world.projectile import Projectile
from boxhead.world.world import World


def world(obstacles=()):
    return World(map=replace(ARENA,obstacles=obstacles,player_start=Vector2()),rounds=None)


def red_shot(start=(50,0)):
    return Projectile(Vector2(start),Vector2(1000,0),12,7,2000,hostile=True,empowers_basic=True)


class RageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1100,700))

    @classmethod
    def tearDownClass(cls):pygame.quit()

    def test_stats_preserve_wounds_and_apply_once(self):
        w=world();e=w.spawn_enemy(BASIC,Vector2(400,0),jitter=0,health_multiplier=3,
                                 damage_multiplier=1.5,timing_multiplier=.7)
        e.health=90
        self.assertTrue(e.empower(SPEED))
        self.assertIs(e.definition,RAGE_BASIC)
        self.assertEqual((e.health,e.max_health),(180,300))
        self.assertAlmostEqual(e.speed,95*1.3)
        self.assertEqual(e.damage_multiplier,3)
        self.assertAlmostEqual(e.windup,.35*.7*.5)
        self.assertAlmostEqual(e.recovery,.6*.7*.5)
        self.assertFalse(e.empower(SPEED))
        self.assertEqual((e.health,e.max_health),(180,300))
        capped=w.spawn_enemy(BASIC,Vector2(600,0),jitter=0,speed_multiplier=3)
        capped.empower(SPEED);self.assertEqual(capped.speed,SPEED)

    def test_red_boss_and_existing_rage_are_pierced(self):
        w=world()
        red=w.spawn_enemy(RED,Vector2(200,0),jitter=0)
        boss=w.spawn_enemy(BOSS,Vector2(320,0),jitter=0)
        rage=w.spawn_enemy(BASIC,Vector2(440,0),jitter=0);rage.empower(SPEED)
        target=w.spawn_enemy(BASIC,Vector2(600,0),jitter=0)
        w.rebuild_spatial_index();p=red_shot();w._advance_projectile(p,.8)
        self.assertFalse(p.alive);self.assertTrue(target.is_empowered)
        self.assertEqual(target.health,100)
        self.assertEqual(red.health,120);self.assertEqual(boss.health,900)
        self.assertFalse(red.is_empowered);self.assertFalse(boss.is_empowered)
        p=red_shot();w._advance_projectile(p,.8)
        self.assertTrue(p.alive);self.assertEqual(target.health,100)

    def test_elite_and_prismatic_rewards_stack_with_rage(self):
        for elite,prismatic,mult,xp in ((True,False,3,1.5),(False,True,5,1)):
            w=world();events=[];w.events.subscribe(EnemyKilled,events.append)
            e=w.spawn_enemy(BASIC,Vector2(400,0),jitter=0,health_multiplier=mult,
                            xp_reward_multiplier=xp,is_elite=elite,is_prismatic=prismatic)
            e.empower(SPEED)
            self.assertEqual(e.max_health,50*mult*2)
            self.assertEqual((e.is_elite,e.is_prismatic),(elite,prismatic))
            w.damage_enemy(e,e.health);w.events.dispatch()
            self.assertEqual(len(events),1)
            self.assertEqual(events[0].xp_reward,round(10*xp*2))
            self.assertEqual(events[0].coin_reward,2)
            self.assertEqual(events[0].is_prismatic,prismatic)

    def test_nearest_collision_walls_and_player_still_block(self):
        w=world((ObstacleDef(Rect(140,-50,50,100),0),))
        e=w.spawn_enemy(BASIC,Vector2(400,0),jitter=0)
        w.rebuild_spatial_index();p=red_shot();w._advance_projectile(p,.8)
        self.assertFalse(p.alive);self.assertFalse(e.is_empowered)
        w=world();w.player.position=Vector2(150,0)
        e=w.spawn_enemy(BASIC,Vector2(400,0),jitter=0)
        w.rebuild_spatial_index();p=red_shot();w._advance_projectile(p,.8)
        self.assertFalse(p.alive);self.assertEqual(w.player.health,88)
        self.assertFalse(e.is_empowered)

    def test_projectile_origin_not_color_controls_empower(self):
        w=world()
        for definition,expected in ((RED,True),(BOSS,False)):
            enemy=w.spawn_enemy(definition,Vector2(500,500),jitter=0)
            RangedAttackState().enter(enemy)
            self.assertTrue(enemy.outbox)
            self.assertTrue(all(p.empowers_basic is expected for p in enemy.outbox))
        target=w.spawn_enemy(BASIC,Vector2(400,0),jitter=0)
        w.rebuild_spatial_index()
        p=red_shot();p.empowers_basic=False;w._advance_projectile(p,.8)
        self.assertFalse(target.is_empowered);self.assertTrue(p.alive)

    def test_sprite_swap_and_combined_tags_render(self):
        from boxhead.states.playing import PlayingState
        w=world();e=w.spawn_enemy(BASIC,w.player.position+Vector2(120,0),jitter=0,is_elite=True)
        state=PlayingState(None,w.events,lambda s:None,lambda w:None,world=w)
        state.enter();state.update(.01)
        old=state._animators[e.id]
        e.empower(SPEED);state._update_animations(.01,Vector2(),False)
        self.assertIsNot(state._animators[e.id],old)
        self.assertEqual(state._animator_types[e.id],'Rage Basic')
        state.draw(pygame.display.get_surface())
        w.damage_enemy(e,e.health);state._update_animations(.01,Vector2(),False)
        state.draw(pygame.display.get_surface())


if __name__=='__main__':unittest.main()
