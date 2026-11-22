"""Estado de partida: input → comandos, atualiza mundo e desenha."""

from __future__ import annotations

import math
from collections.abc import Callable

import pygame
from pygame import Vector2

from boxhead.core.catalog import Animation, catalog
from boxhead.core.commands import Move, Shoot, SwitchWeapon
from boxhead.core.events import EventQueue
from boxhead.core.state import State, StateMachine
from boxhead.world.augments import Rarity
from boxhead.world.camera import Camera
from boxhead.world.enemy import Enemy, EnemyDef
from boxhead.world.enemy_sprite import EnemyAnimator, EnemySprite
from boxhead.world.environment_sprite import EnvironmentSprite
from boxhead.world.player_sprite import PlayerSprite
from boxhead.world.rounds import Phase
from boxhead.world.world import World

SPRITE_RENDER_SIZE = (64, 64)
SHADOW_RENDER_SIZE = (64, 32)
SHADOW_OFFSET_Y = 26
SPRITE_PER_RADIUS = 2.9 

SHOOT_ANIMATION_SECONDS = 3 / 12
CAMERA_SPEED = 8.0

_CONTROL_KEYS = (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE)
_TEXT = (225, 230, 237)
_MUTED = (153, 163, 176)
_ACCENT = (255, 220, 120)
RARITY_COLORS = {
    Rarity.GRAY: (170, 176, 186),
    Rarity.GOLD: (235, 190, 70),
    Rarity.PRISMATIC: (190, 120, 255),
}


def round_label(director) -> str:
    """Texto do HUD durante uma ronda; assinala as rondas de boss."""
    base = f"RONDA {director.round_number}"
    return f"{base} · BOSS" if director.is_boss_round else base


class PlayingState(State):
    """A partida (`World`) pertence a esta instância e sobrevive a pausas.

    `enter()` corre também ao retomar da pausa, por isso não pode criar nem
    reiniciar nada que faça parte da partida; só prepara apresentação, input e
    subscrições (que `exit()` volta a retirar).
    """

    def __init__(
        self,
        machine: StateMachine,
        events: EventQueue,
        on_pause: Callable[[State], None],
        on_game_over: Callable[[World, float], None],
        viewport: tuple[int, int] = (1100, 700),
        world: World | None = None,
        on_level_up: Callable[[State], None] | None = None,
    ) -> None:
        self._machine = machine
        self._events = events
        self._on_pause = on_pause
        self._on_game_over = on_game_over
        self._on_level_up = on_level_up or (lambda state: None)

        self._world = world if world is not None else World(events=events)
        self._camera = Camera(viewport)
        self._camera.snap(self._world.player.position)
        self._elapsed = 0.0
        self._pressed: set[int] = set()
        self._shooting_timer = 0.0
        self._active_anim: Animation | None = None
        self._animators: dict[int, EnemyAnimator] = {}
        self._enemy_sprites: dict[str, EnemySprite] = {}
        self._show_debug = False
        self._presentation_ready = False
        self._scaled: dict[tuple[int, tuple[int, int]], pygame.Surface] = {}

    @property
    def world(self) -> World:
        return self._world

    # ------------------------------------------------------------------ ciclo de vida

    def enter(self) -> None:
        if not self._presentation_ready:
            self._load_presentation()
            self._presentation_ready = True
        self._world.start_listening()
      
        held = pygame.key.get_pressed()
        self._pressed = {key for key in _CONTROL_KEYS if held[key]}

    def exit(self) -> None:
        self._pressed.clear()
        self._world.stop_listening()

    def _load_presentation(self) -> None:
        self._player_sprite = PlayerSprite()
        self._env = EnvironmentSprite()
        self._active_anim = self._player_sprite.for_state(
            moving=False, shooting=False, orientation=self._world.player.orientation
        )

        icons = catalog().sheet("ui/ui_icons_main.png").animation().frames
        self._icon_heart, self._icon_coin, self._icon_gem = icons[0], icons[1], icons[2]
        self._font = pygame.font.Font(None, 28)
        self._font_big = pygame.font.Font(None, 44)

    def _enemy_sprite_for(self, definition: EnemyDef) -> EnemySprite:
        sprite = self._enemy_sprites.get(definition.name)
        if sprite is None:
            sprite = self._enemy_sprites[definition.name] = EnemySprite(definition)
        return sprite

    # ------------------------------------------------------------------ input / update

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._pressed.add(event.key)
            if event.key == pygame.K_ESCAPE:
                self._on_pause(self)
            elif event.key == pygame.K_F3:
                self._show_debug = not self._show_debug
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self._world.apply(SwitchWeapon(event.key - pygame.K_1), 0.0)
        elif event.type == pygame.KEYUP:
            self._pressed.discard(event.key)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self._pressed.clear()

    def update(self, dt: float) -> None:
        self._elapsed += dt
        direction = Vector2(
            (pygame.K_d in self._pressed) - (pygame.K_a in self._pressed),
            (pygame.K_s in self._pressed) - (pygame.K_w in self._pressed),
        )
        self._world.apply(Move(direction), dt)

        fired = False
        if pygame.K_SPACE in self._pressed:
            fired = self._world.player.can_fire  # ler ANTES: Shoot ativa o cooldown
            self._world.apply(Shoot(), dt)
            if fired:
                self._shooting_timer = SHOOT_ANIMATION_SECONDS
        self._shooting_timer = max(0.0, self._shooting_timer - dt)

        self._world.update(dt)
        self._events.dispatch()
        self._camera.follow(self._world.player.position, dt, CAMERA_SPEED)
        self._update_animations(dt, direction, fired)

        if not self._world.player.alive:
            self._on_game_over(self._world, self._elapsed)
        elif self._world.progression.pending_choices > 0:
            self._on_level_up(self)  

    def _update_animations(self, dt: float, direction: Vector2, fired: bool) -> None:
        shooting = self._shooting_timer > 0
        anim = self._player_sprite.for_state(
            moving=direction.length_squared() > 0,
            shooting=shooting,
            orientation=self._world.player.orientation,
        )
        if anim is not self._active_anim or (fired and shooting):
            anim.reset()  
            self._active_anim = anim
        self._active_anim.update(dt)

        alive_ids = set()
        for enemy in self._world.enemies:
            alive_ids.add(enemy.id)
            animator = self._animators.get(enemy.id)
            if animator is None:
                animator = self._animators[enemy.id] = self._enemy_sprite_for(
                    enemy.definition
                ).animator()
            animator.update(enemy, dt)
        for enemy_id in set(self._animators) - alive_ids:
            del self._animators[enemy_id]


    def draw(self, surface: pygame.Surface) -> None:
        """Só desenha: não altera mundo nem câmara."""
        m = self._world.map
        surface.fill((12, 14, 18))

        half = self._camera.viewport / 2
        top_left = self._camera.center - half
        bottom_right = self._camera.center + half

        size = m.tile_size
        start_x = int(top_left.x // size) * size
        start_y = int(top_left.y // size) * size
        end_x = int(bottom_right.x // size + 1) * size
        end_y = int(bottom_right.y // size + 1) * size
        for x in range(start_x, end_x, size):
            for y in range(start_y, end_y, size):
                tile = self._env.floor_at(x // size, y // size, m.floor_tiles)
                screen = self._camera.world_to_screen(Vector2(x, y))
                surface.blit(tile, (int(screen.x), int(screen.y)))

        for deco in m.decorations:
            if not self._in_view(deco.position, top_left, bottom_right, 64):
                continue
            sprite = self._env.decoration_for(deco.sprite_index)
            screen = self._camera.world_to_screen(deco.position)
            surface.blit(sprite, sprite.get_rect(center=(int(screen.x), int(screen.y))))

        self._draw_border_walls(surface, top_left, bottom_right)

        if self._show_debug:
            for spawn in m.spawn_points:
                pygame.draw.circle(
                    surface, (90, 60, 140), self._camera.world_to_screen(spawn), 6, 1
                )

        self._draw_entities(surface, top_left, bottom_right)
        self._draw_bodies_and_fx(surface)
        self._draw_projectiles(surface)
        if self._show_debug:
            self._draw_hitboxes(surface)
        self._draw_hud(surface)

    def _draw_entities(self, surface: pygame.Surface, top_left: Vector2, bottom_right: Vector2):
        """Obstáculos, inimigos e jogador ordenados por profundidade (y maior = mais à frente)."""
        world = self._world
        drawables: list[tuple[float, int, Callable[[], None]]] = []
        for obstacle in world.map.obstacles:
            if self._in_view(Vector2(obstacle.rect.center), top_left, bottom_right, 80):
                drawables.append(
                    (obstacle.rect.centery, 0, lambda o=obstacle: self._blit_obstacle(surface, o))
                )
        for enemy in world.enemies:
            if self._in_view(enemy.position, top_left, bottom_right, 64):
                drawables.append(
                    (enemy.position.y, 1, lambda e=enemy: self._draw_enemy(surface, e))
                )
        drawables.append((world.player.position.y, 2, lambda: self._draw_player(surface)))
        drawables.sort(key=lambda item: (item[0], item[1]))
        for _, _, draw in drawables:
            draw()

    def _scale(self, image: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
        key = (id(image), size)
        cached = self._scaled.get(key)
        if cached is None:
            cached = pygame.transform.smoothscale(image, size)
            self._scaled[key] = cached
        return cached

    def _blit_shadow(
        self, surface: pygame.Surface, screen_pos: Vector2, scale: float = 1.0
    ) -> None:
        size = (round(SHADOW_RENDER_SIZE[0] * scale), round(SHADOW_RENDER_SIZE[1] * scale))
        shadow = self._scale(self._player_sprite.shadow, size)
        offset = SHADOW_OFFSET_Y * scale
        surface.blit(shadow, shadow.get_rect(center=(screen_pos.x, screen_pos.y + offset)))

    def _draw_player(self, surface: pygame.Surface) -> None:
        screen_pos = self._camera.world_to_screen(self._world.player.position)
        self._blit_shadow(surface, screen_pos)
        frame = self._scale(self._active_anim.current, SPRITE_RENDER_SIZE)
        surface.blit(frame, frame.get_rect(center=screen_pos))

    def _draw_enemy(self, surface: pygame.Surface, enemy: Enemy) -> None:
        animator = self._animators.get(enemy.id)
        if animator is None: 
            return
        screen_pos = self._camera.world_to_screen(enemy.position)
        
        scale = enemy.radius * SPRITE_PER_RADIUS / SPRITE_RENDER_SIZE[0]
        self._blit_shadow(surface, screen_pos, scale)
        side = round(SPRITE_RENDER_SIZE[0] * scale)
        frame = self._scale(animator.current, (side, side))
        surface.blit(frame, frame.get_rect(center=screen_pos))
        if enemy.visual == "prepare":  
            self._draw_telegraph(surface, enemy, screen_pos)
        if enemy.health < enemy.max_health and not enemy.is_boss:  
            width, ratio = 40, max(0.0, enemy.health / enemy.max_health)
            bar = pygame.Rect(0, 0, width, 5)
            bar.midbottom = (int(screen_pos.x), int(screen_pos.y - enemy.radius - 16))
            pygame.draw.rect(surface, (50, 20, 20), bar)
            pygame.draw.rect(surface, (220, 70, 70), (bar.x, bar.y, int(width * ratio), bar.height))

    @staticmethod
    def _draw_telegraph(surface: pygame.Surface, enemy: Enemy, screen_pos: Vector2) -> None:
        ranged = enemy.definition.ranged
        color = ranged.color if ranged else (255, 120, 70)
        if ranged is not None and ranged.ring:
           
            radius = enemy.radius + 8 + enemy.windup_progress * 130
            pygame.draw.circle(surface, color, screen_pos, radius, 3)
            pygame.draw.circle(surface, (255, 255, 255), screen_pos, enemy.radius + 8, 1)
        else:  
            pygame.draw.line(surface, color, screen_pos, screen_pos + enemy.orientation * 70, 2)
            pygame.draw.circle(surface, color, screen_pos, enemy.radius + 6, 2)

    def _blit_obstacle(self, surface: pygame.Surface, obstacle) -> None:
      
        sprite = self._env.obstacle_for(obstacle.sprite_index)
        tl = self._camera.world_to_screen(Vector2(obstacle.rect.topleft))
        surface.blit(sprite, (int(tl.x), int(tl.y)))

    def _draw_bodies_and_fx(self, surface: pygame.Surface) -> None:
        for fx in self._world.fx:  
            radius = max(2, int(fx.radius * (0.4 + 0.6 * fx.progress)))
            layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = int(170 * (1 - fx.progress))
            pygame.draw.circle(layer, (255, 150, 60, alpha), (radius, radius), radius)
            pygame.draw.circle(
                layer, (255, 230, 150, min(255, alpha + 60)), (radius, radius), radius, 3
            )
            center = self._camera.world_to_screen(fx.position)
            surface.blit(layer, layer.get_rect(center=(int(center.x), int(center.y))))
        for body in self._world.bodies:  
            center = self._camera.world_to_screen(body.position)
            pygame.draw.circle(surface, (20, 40, 60), center, body.radius + 3)
            pygame.draw.circle(surface, body.color, center, body.radius)
            pygame.draw.circle(surface, (255, 255, 255), center, max(2, body.radius // 3))

    def _draw_projectiles(self, surface: pygame.Surface) -> None:
        for proj in self._world.projectiles:
            head = self._camera.world_to_screen(proj.position)
            if (
                proj.hostile
            ):  
                pygame.draw.circle(surface, (90, 20, 10), head, int(proj.radius) + 3)
                pygame.draw.circle(surface, proj.color, head, int(proj.radius) + 1)
                pygame.draw.circle(surface, (255, 235, 180), head, max(2, int(proj.radius) - 3))
                continue
            tail = head - proj.velocity.normalize() * 14  
            pygame.draw.line(surface, proj.color, tail, head, max(2, int(proj.radius)))
            pygame.draw.circle(surface, (255, 255, 255), head, max(2, int(proj.radius) - 1))

    def _draw_hitboxes(self, surface: pygame.Surface) -> None:
        world, cam = self._world, self._camera
        for obstacle in world.map.obstacles:
            tl = cam.world_to_screen(Vector2(obstacle.rect.topleft))
            rect = pygame.Rect(int(tl.x), int(tl.y), obstacle.rect.width, obstacle.rect.height)
            if obstacle.circular:
                pygame.draw.circle(surface, (80, 200, 120), rect.center, rect.width // 2, 1)
            else:
                pygame.draw.rect(surface, (80, 200, 120), rect, 1)
        p = world.player
        pygame.draw.circle(surface, (80, 160, 255), cam.world_to_screen(p.position), p.radius, 1)
        for enemy in world.enemies:
            pygame.draw.circle(
                surface, (255, 90, 90), cam.world_to_screen(enemy.position), enemy.radius, 1
            )

    def _icon(self, image: pygame.Surface) -> pygame.Surface:
        return self._scale(image, (36, 36))

    def _draw_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(surface, (24, 28, 36), rect, border_radius=4)
        if ratio > 0:
            fill = pygame.Rect(rect.x, rect.y, max(4, int(rect.width * ratio)), rect.height)
            pygame.draw.rect(surface, color, fill, border_radius=4)
        pygame.draw.rect(surface, (90, 100, 115), rect, 1, border_radius=4)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        world = self._world
        player, progression = world.player, world.progression
        bar_x = 16 + 36 + 10

        surface.blit(self._icon(self._icon_heart), (16, 14))
        health_bar = pygame.Rect(bar_x, 20, 190, 22)
        self._draw_bar(surface, health_bar, player.health / player.max_health, (220, 70, 70))
        hp_text = f"{math.ceil(player.health)}/{math.ceil(player.max_health)}"
        label = self._font.render(hp_text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=health_bar.center))

        surface.blit(self._icon(self._icon_gem), (16, 58))
        xp_bar = pygame.Rect(bar_x, 64, 190, 22)
        self._draw_bar(surface, xp_bar, progression.xp_ratio, (110, 190, 255))
        label = self._font.render(f"NV {progression.level}", True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=xp_bar.center))

        surface.blit(self._icon(self._icon_coin), (16, 102))
        coins = self._font.render(str(world.stats.coins), True, _TEXT)
        surface.blit(coins, (bar_x, 108))

        self._draw_owned_augments(surface)

        width = surface.get_width()
        director = world.director
        if director is not None:
            if director.phase is Phase.INTERMISSION:
                label = (
                    f"RONDA {director.round_number + 1} EM {max(0, director.intermission_left):.0f}"
                )
            else:
                label = round_label(director)
            text = self._font_big.render(label, True, _TEXT)
            surface.blit(text, text.get_rect(topright=(width - 16, 16)))
            remaining = world.alive_enemy_count + director.pending
            info = f"INIMIGOS {remaining}   MORTES {world.stats.kills}"
            line = self._font.render(info, True, _MUTED)
            surface.blit(line, line.get_rect(topright=(width - 16, 64)))

        self._draw_boss_bar(surface)

        player = world.player
        cursor_x = surface.get_width() // 2 - 170
        for slot, weapon in enumerate(player.weapons):
            active = slot == player.weapon_slot
            color = _ACCENT if active else _MUTED
            label = self._font.render(f"{slot + 1} {weapon.name}", True, color)
            surface.blit(label, (cursor_x, surface.get_height() - 36))
            if active:
                pygame.draw.line(
                    surface,
                    color,
                    (cursor_x, surface.get_height() - 12),
                    (cursor_x + label.get_width(), surface.get_height() - 12),
                    2,
                )
            cursor_x += label.get_width() + 36

    def _draw_boss_bar(self, surface: pygame.Surface) -> None:
        boss = next((e for e in self._world.enemies if e.is_boss and e.alive), None)
        if boss is None:
            return
        rect = pygame.Rect(0, 0, 460, 20)
        rect.midtop = (surface.get_width() // 2, 18)
        self._draw_bar(surface, rect, boss.health / boss.max_health, (190, 90, 255))
        label = self._font.render("BOSS", True, (255, 255, 255))
        surface.blit(label, label.get_rect(midtop=(rect.centerx, rect.bottom + 4)))

    def _draw_owned_augments(self, surface: pygame.Surface) -> None:
        owned = list(self._world.inventory.owned())[-8:] 
        y = surface.get_height() - 18 - 22 * len(owned)
        for augment, stacks in owned:
            suffix = f" x{stacks}" if stacks > 1 else ""
            text = self._font.render(f"{augment.name}{suffix}", True, RARITY_COLORS[augment.rarity])
            surface.blit(text, (16, y))
            y += 22

    @staticmethod
    def _in_view(point: Vector2, top_left: Vector2, bottom_right: Vector2, margin: int) -> bool:
        return (
            top_left.x - margin <= point.x <= bottom_right.x + margin
            and top_left.y - margin <= point.y <= bottom_right.y + margin
        )

    def _draw_border_walls(
        self, surface: pygame.Surface, top_left: Vector2, bottom_right: Vector2
    ) -> None:
        m = self._world.map
        tile = self._env.wall_for(0)  
        t = m.wall_thickness
        b = m.bounds

        def blit_at(x: int, y: int) -> None:
            if self._in_view(Vector2(x, y), top_left, bottom_right, t):
                s = self._camera.world_to_screen(Vector2(x, y))
                surface.blit(tile, (int(s.x), int(s.y)))

        for x in range(b.left, b.right, t):
            blit_at(x, b.top)
            blit_at(x, b.bottom - t)
        for y in range(b.top + t, b.bottom - t, t):
            blit_at(b.left, y)
            blit_at(b.right - t, y)
