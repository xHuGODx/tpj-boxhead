"""Mundo: arena, jogador, inimigos e projéteis; não conhece Surface.

Ordem de um tick (`update`), para a simulação ser previsível:
  1. cooldowns do jogador
  2. inimigos: FSM, movimento, separação, obstáculos
  3. projéteis: movimento varrido e acertos (publica `EnemyKilled`)
  4. remoção de mortos/expirados
  5. diretor de rondas (spawns, `RoundStarted`/`RoundEnded`)
Os eventos publicados são despachados pelo estado de partida depois do tick.
"""

from __future__ import annotations

import random

from pygame import Rect, Vector2

from boxhead.core.commands import Command, Shoot
from boxhead.core.events import EnemyKilled, EventQueue, make_counter
from boxhead.core.geometry import (
    SpatialGrid,
    circle_aabb,
    circle_circle,
    segment_aabb_hit,
    segment_circle_hit,
)
from boxhead.world.attributes import Modifiers
from boxhead.world.augments import (
    AUGMENTS,
    DEFAULT_OFFER,
    Augment,
    AugmentInventory,
    Offer,
    OfferConfig,
    draw_offer,
)
from boxhead.world.behaviors import BEHAVIOR_TYPES, Behavior
from boxhead.world.enemy import Enemy, EnemyDef
from boxhead.world.fx import Body, Fx
from boxhead.world.map import ARENA, MapDefinition, ObstacleDef
from boxhead.world.player import Player
from boxhead.world.progression import Progression
from boxhead.world.projectile import Projectile
from boxhead.world.rounds import DEFAULT_ROUNDS, RoundConfig, RoundDirector
from boxhead.world.stats import RunStats

MUZZLE_GAP = 6  # distância da boca da arma ao contorno do jogador
SPAWN_JITTER = 10  # evita inimigos criados no mesmo ponto ficarem empilhados
MAX_ENEMY_RADIUS_HINT = 64  # margem para a consulta da grelha


class World:
    # Resolver um obstáculo pode empurrar para outro; repete-se até estabilizar.
    COLLISION_PASSES = 4

    def __init__(
        self,
        map: MapDefinition = ARENA,
        player: Player | None = None,
        events: EventQueue | None = None,
        rng: random.Random | None = None,
        rounds: RoundConfig | None = DEFAULT_ROUNDS,
        base_modifiers: Modifiers | None = None,
    ) -> None:
        self.map = map
        self.player = player if player is not None else Player(position=Vector2(map.player_start))
        self.events = events if events is not None else EventQueue()
        self.rng = rng if rng is not None else random.Random()
        self.stats = RunStats()
        # `base_modifiers`: a base da partida (melhorias permanentes do perfil). Os augments
        # somam-se a ela e tudo é recalculado do zero, nunca por cima de valores já alterados.
        self.inventory = AugmentInventory(base_modifiers)
        self.player.set_modifiers(self.inventory.modifiers)
        self.progression = Progression(
            xp_multiplier=lambda: self.inventory.modifiers.xp_gain_multiplier
        )
        self.behaviors: dict[str, Behavior] = {}
        self.bodies: list[Body] = []  # corpos a desenhar (satélites, ...)
        self.fx: list[Fx] = []  # efeitos visuais de curta duração
        self._sync_behaviors()
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.director = RoundDirector(rounds) if rounds is not None else None
        self._next_enemy_id = make_counter()
        self._grid: SpatialGrid[Enemy] = SpatialGrid(128)

    @property
    def bounds(self) -> Rect:
        return self.map.bounds

    @property
    def alive_enemy_count(self) -> int:
        return sum(1 for e in self.enemies if e.alive)

    def start_listening(self) -> None:
        self.stats.attach(self.events)
        self.progression.attach(self.events)

    def stop_listening(self) -> None:
        self.stats.detach()
        self.progression.detach()

    # ------------------------------------------------------------------ augments

    def draw_offer(self, config: OfferConfig = DEFAULT_OFFER) -> Offer:
        """Oferta para a próxima escolha pendente; respeita o que já foi adquirido."""
        weapons = [w.name for w in self.player.weapons]
        return draw_offer(AUGMENTS, self.inventory, weapons, self.rng, config)

    def choose_augment(self, augment: Augment) -> None:
        """Adquire o augment, recalcula os atributos e consome uma escolha pendente.

        Valida tudo antes de alterar o estado: uma chamada inválida não deixa o mundo
        a meio (por exemplo, augment adicionado sem escolha consumida).
        """
        if self.progression.pending_choices <= 0:
            raise ValueError("não há escolhas pendentes")
        weapons = [w.name for w in self.player.weapons]
        self.inventory.add(augment, weapons)
        self.player.set_modifiers(self.inventory.modifiers)
        self._sync_behaviors()
        self.progression.consume_choice()

    def _sync_behaviors(self) -> None:
        """Cria/atualiza os comportamentos concedidos pelos modificadores atuais."""
        for kind, level in self.inventory.modifiers.behaviors.items():
            behavior = self.behaviors.get(kind)
            if behavior is None:
                self.behaviors[kind] = BEHAVIOR_TYPES[kind](level)
            else:
                behavior.set_level(level)  # mantém o estado (p. ex. o ângulo dos satélites)

    # ------------------------------------------------------------------ comandos

    def apply(self, command: Command, dt: float) -> None:
        # Ler can_fire ANTES: o jogador ativa o cooldown ao aplicar o comando.
        if isinstance(command, Shoot) and self.player.can_fire:
            self._fire_weapon()
        self.player.apply(command, dt)
        self._constrain(self.player.position, self.player.radius)

    def _fire_weapon(self) -> None:
        p = self.player
        weapon = p.weapon
        origin = p.position + p.orientation * (p.radius + MUZZLE_GAP)
        half_cone = weapon.spread_degrees / 2
        for _ in range(weapon.pellets):
            angle = self.rng.uniform(-half_cone, half_cone) if half_cone else 0.0
            direction = p.orientation.rotate(angle)
            projectile = Projectile(
                position=Vector2(origin),
                velocity=direction * weapon.projectile_speed,
                damage=weapon.damage,
                radius=weapon.projectile_radius,
                range_left=weapon.projectile_range,
                color=weapon.color,
            )
            for behavior in self.behaviors.values():
                behavior.on_fire(self, projectile)
            self.projectiles.append(projectile)

    # ------------------------------------------------------------------ inimigos

    def spawn_enemy(
        self,
        definition: EnemyDef,
        position: Vector2,
        *,
        health_multiplier: float = 1.0,
        speed_multiplier: float = 1.0,
    ) -> Enemy:
        jitter = Vector2(
            self.rng.uniform(-SPAWN_JITTER, SPAWN_JITTER),
            self.rng.uniform(-SPAWN_JITTER, SPAWN_JITTER),
        )
        enemy = Enemy(
            id=self._next_enemy_id(),
            definition=definition,
            position=Vector2(position) + jitter,
            health=definition.max_health * health_multiplier,
            speed=definition.speed * speed_multiplier,
            steer_degrees=self.rng.choice((-1, 1)) * self.rng.uniform(8, 20),
        )
        self.enemies.append(enemy)
        return enemy

    # ------------------------------------------------------------------ serviços de comportamentos

    def damage_enemy(self, enemy: Enemy, amount: float, chain_depth: int = 0) -> bool:
        """Único caminho de dano a inimigos: a morte publica o evento e chama os ganchos.

        `chain_depth` conta mortes encadeadas por efeitos (explosões), para as limitar.
        """
        if not enemy.take_damage(amount):
            return False
        d = enemy.definition
        self.events.publish(EnemyKilled(enemy.id, d.xp_reward, d.coin_reward, d.is_boss))
        for behavior in tuple(self.behaviors.values()):
            behavior.on_kill(self, enemy, chain_depth)
        return True

    def enemies_near(self, position: Vector2, radius: float) -> list[Enemy]:
        """Inimigos vivos cujo círculo toca o círculo (position, radius)."""
        reach = int(radius) + MAX_ENEMY_RADIUS_HINT
        probe = Rect(int(position.x) - reach, int(position.y) - reach, 2 * reach, 2 * reach)
        return [
            e
            for e in self._grid.query(probe)
            if e.alive and e.position.distance_to(position) <= radius + e.radius
        ]

    def line_of_sight(self, start: Vector2, end: Vector2) -> bool:
        """True se nenhum obstáculo está entre os dois pontos."""
        return all(
            self._segment_obstacle_hit(start, end, obstacle) is None
            for obstacle in self.map.obstacles
        )

    def add_fx(self, kind: str, position: Vector2, radius: float, duration: float) -> None:
        self.fx.append(Fx(kind, Vector2(position), radius, duration, duration))

    def rebuild_spatial_index(self) -> None:
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        self._grid.clear()
        for enemy in self.enemies:
            if enemy.alive:
                r = int(enemy.radius)
                x, y = int(enemy.position.x), int(enemy.position.y)
                self._grid.insert(enemy, Rect(x - r, y - r, 2 * r, 2 * r))

    def _update_enemy(self, enemy: Enemy, dt: float) -> None:
        enemy.update(dt, self.player)
        if enemy.outbox:  # disparos novos (inimigos à distância)
            self.projectiles.extend(enemy.outbox)
            enemy.outbox.clear()
        # Separação: cada um recua metade da sobreposição; o par resolve-se em conjunto.
        r = int(enemy.radius) + 4
        x, y = int(enemy.position.x), int(enemy.position.y)
        for other in self._grid.query(Rect(x - r, y - r, 2 * r, 2 * r)):
            if other is enemy or not other.alive:
                continue
            contact = circle_circle(enemy.position, enemy.radius, other.position, other.radius)
            if contact:
                enemy.position += contact.push_out * 0.5
        contact = circle_circle(
            enemy.position, enemy.radius, self.player.position, self.player.radius
        )
        if contact:
            enemy.position += contact.push_out  # o jogador não é empurrado por inimigos
        self._constrain(enemy.position, enemy.radius)

    # ------------------------------------------------------------------ projéteis

    def _advance_projectile(self, proj: Projectile, dt: float) -> None:
        start = Vector2(proj.position)
        step = proj.velocity * dt
        travel = step.length()
        if travel == 0:
            return
        if travel > proj.range_left:
            step *= proj.range_left / travel
            travel = proj.range_left
        end = start + step

        best_t, best_target = 2.0, None  # 2.0 = "ainda sem acerto"; None = obstáculo
        for obstacle in self.map.obstacles:
            t = self._segment_obstacle_hit(start, end, obstacle)
            if t is not None and t < best_t:
                best_t, best_target = t, None
        if proj.hostile:  # projétil de inimigo: só pode acertar no jogador
            player = self.player
            if player.alive:
                t = segment_circle_hit(start, end, player.position, player.radius + proj.radius)
                if t is not None and t < best_t:
                    best_t, best_target = t, player
        else:
            margin = MAX_ENEMY_RADIUS_HINT + int(proj.radius)
            area = Rect(
                int(min(start.x, end.x)) - margin,
                int(min(start.y, end.y)) - margin,
                int(abs(end.x - start.x)) + 2 * margin,
                int(abs(end.y - start.y)) + 2 * margin,
            )
            for enemy in self._grid.query(area):
                if not enemy.alive or enemy.id in proj.hit_ids:
                    continue
                t = segment_circle_hit(start, end, enemy.position, enemy.radius + proj.radius)
                if t is not None and t < best_t:
                    best_t, best_target = t, enemy

        if best_t <= 1.0:
            if isinstance(best_target, Enemy):
                hit_point = start + (end - start) * best_t
                proj.hit_ids.add(best_target.id)
                self.damage_enemy(best_target, proj.damage)
                continues = False  # um comportamento (Ricochet) pode manter o projétil em voo
                for behavior in tuple(self.behaviors.values()):
                    continues = behavior.on_hit(self, proj, best_target, hit_point) or continues
                if continues:
                    return
            elif best_target is self.player:
                self.player.take_damage(proj.damage)
            proj.alive = False  # sem comportamentos, uma bala acerta no máximo num alvo
            return

        proj.position = end
        proj.range_left -= travel
        if proj.range_left <= 0 or not self.map.playable_bounds.collidepoint(end):
            proj.alive = False

    @staticmethod
    def _segment_obstacle_hit(start: Vector2, end: Vector2, obstacle: ObstacleDef) -> float | None:
        if obstacle.circular:
            return segment_circle_hit(
                start, end, Vector2(obstacle.rect.center), obstacle.rect.width / 2
            )
        return segment_aabb_hit(start, end, obstacle.rect)

    # ------------------------------------------------------------------ tick

    def update(self, dt: float) -> None:
        self.player.update(dt)

        self._rebuild_grid()
        for enemy in self.enemies:
            self._update_enemy(enemy, dt)

        self._rebuild_grid()
        for proj in self.projectiles:
            if proj.alive:
                self._advance_projectile(proj, dt)

        for behavior in tuple(self.behaviors.values()):
            behavior.update(self, dt)
        for effect in self.fx:
            effect.ttl -= dt
        self.fx = [f for f in self.fx if f.ttl > 0]
        self.bodies = [body for b in self.behaviors.values() for body in b.bodies(self)]

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]

        if self.director is not None:
            self.director.update(dt, self)

    # ------------------------------------------------------------------ colisões com o mapa

    def _clamp_to_arena(self, position: Vector2, radius: float) -> None:
        area = self.map.playable_bounds
        position.x = max(area.left + radius, min(position.x, area.right - radius))
        position.y = max(area.top + radius, min(position.y, area.bottom - radius))

    @staticmethod
    def _obstacle_contact(position: Vector2, radius: float, obstacle: ObstacleDef):
        if obstacle.circular:
            return circle_circle(
                position, radius, Vector2(obstacle.rect.center), obstacle.rect.width / 2
            )
        return circle_aabb(position, radius, obstacle.rect)

    def _constrain(self, position: Vector2, radius: float) -> None:
        """Mantém um círculo dentro da arena e fora dos obstáculos (jogador e inimigos)."""
        self._clamp_to_arena(position, radius)
        for _ in range(self.COLLISION_PASSES):
            moved = False
            for obstacle in self.map.obstacles:
                contact = self._obstacle_contact(position, radius, obstacle)
                if contact:
                    position += contact.push_out
                    moved = True
            if not moved:
                break
        # Um empurrão de obstáculo não pode lançar o círculo para fora da arena.
        self._clamp_to_arena(position, radius)
