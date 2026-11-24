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
from collections import deque
from dataclasses import replace
from uuid import uuid4
from boxhead.world.result import RunReason, RunResult

from pygame import Rect, Vector2

from boxhead.core.commands import Command, Shoot
from boxhead.core.events import (
    EnemyKilled, EventQueue, PlayerDied, RoundCompleted, RoundStarted, RunFinished, make_counter,
)
from boxhead.core.geometry import (
    SpatialGrid,
    circle_aabb,
    circle_circle,
    swept_circle_aabb_hit,
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
    draw_weapon_offer,
    draw_prismatic_offer,
)
from boxhead.world.behaviors import BEHAVIOR_TYPES, Behavior
from boxhead.world.enemy import BASIC, Enemy, EnemyDef
from boxhead.world.fx import Body, Fx
from boxhead.world.map import ARENA, MapDefinition, ObstacleDef
from boxhead.world.player import Player, SPEED
from boxhead.world.loot import AmmoDropConfig, AmmoDrops
from boxhead.world.progression import Progression
from boxhead.world.projectile import Projectile
from boxhead.world.rounds import DEFAULT_ROUNDS, RoundConfig, RoundDirector
from boxhead.world.stats import RunStats
from boxhead.world.terrain import create_terrain
from boxhead.world.navigation import Navigator
from boxhead.world.enemy import ChaseState
from boxhead.world.combat import (
    CombatEffects, PARALLEL_SPACING, ROUND_BLAST_RADIUS,
    ROUND_BLAST_RADIUS_PER_STACK, ROUND_BLAST_AD_RATIO,
)

MUZZLE_GAP = 6  # distância da boca da arma ao contorno do jogador
SPAWN_JITTER = 10  # evita inimigos criados no mesmo ponto ficarem empilhados
MAX_ENEMY_RADIUS_HINT = 64  # margem para a consulta da grelha
BARREL_BLAST_RADIUS = 180.0


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
        viewport: tuple[int, int] = (1100, 700),
        ammo_drops: AmmoDropConfig = AmmoDropConfig(),
    ) -> None:
        self.viewport = viewport
        self.rng = rng if rng is not None else random.Random()
        self.map = create_terrain(map, self.rng.getrandbits(64))
        self.navigator = Navigator(self.map)
        self._barrel_damage: dict[tuple[int, int, int], float] = {}
        self.combat = CombatEffects()
        self.player = player if player is not None else Player(position=Vector2(map.player_start))
        self.events = events if events is not None else EventQueue()
        self.stats = RunStats()
        self.run_id = uuid4().hex
        self.elapsed = 0.0
        self.result: RunResult | None = None
        self._death_published = False
        self._listening = False
        self.last_kill_weapon: str | None = None
        self.ammo_notice_left = 0.0
        self.ammo_drops = AmmoDrops(ammo_drops)
        # `base_modifiers`: a base da partida (melhorias permanentes do perfil). Os augments
        # somam-se a ela e tudo é recalculado do zero, nunca por cima de valores já alterados.
        self.inventory = AugmentInventory(base_modifiers)
        self._offer: Offer | None = None
        self.player.set_modifiers(self.inventory.modifiers)
        self.progression = Progression(
            xp_multiplier=lambda: self.inventory.modifiers.xp_gain_multiplier
        )
        self.behaviors: dict[str, Behavior] = {}
        self.bodies: list[Body] = []  # corpos a desenhar (satélites, ...)
        self.fx: list[Fx] = []  # efeitos visuais de curta duração
        self._sync_behaviors()
        self.enemies: list[Enemy] = []
        self.corpses: list[Enemy] = []
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
        if self._listening:
            return
        self.stats.attach(self.events)
        self.progression.attach(self.events)
        self.events.subscribe(RoundStarted, self._on_round_started)
        self.events.subscribe(RoundCompleted, self._on_round_completed)
        self._listening = True

    def stop_listening(self) -> None:
        if not self._listening:
            return
        self.stats.detach()
        self.progression.detach()
        self.events.unsubscribe(RoundStarted, self._on_round_started)
        self.events.unsubscribe(RoundCompleted, self._on_round_completed)
        self._listening = False

    def _on_round_started(self, event: RoundStarted) -> None:
        self.last_kill_weapon = None

    def _on_round_completed(self, event: RoundCompleted) -> None:
        weapon = event.weapon_name or self.player.weapon.name
        if self.player.arsenal.is_unlocked(weapon):
            self.progression.reward_round(event.round_number, weapon)

    # ------------------------------------------------------------------ augments

    def draw_offer(self, config: OfferConfig = DEFAULT_OFFER) -> Offer:
        """Oferta para a próxima escolha pendente; respeita o que já foi adquirido."""
        if self._offer is None:
            weapons = [w.name for w in self.player.available_weapons]
            choice = self.progression.next_choice
            available = tuple(a for a in AUGMENTS
                              if not (a.id == "redline" and self.player.modifiers.crit_chance <= 0)
                              and not (a.id == "siege_frame" and self.growth_position() is None))
            if choice is not None and choice.prismatic_source is not None:
                self._offer = draw_prismatic_offer(available, self.inventory, weapons, self.rng)
            elif choice is not None and choice.weapon is not None:
                self._offer = draw_weapon_offer(available, self.inventory, weapons, choice.weapon, self.rng)
            else:
                self._offer = draw_offer(available, self.inventory, weapons, self.rng, config)
        return self._offer

    def clear_offer(self) -> None:
        self._offer = None

    def choose_augment(self, augment: Augment) -> None:
        """Adquire o augment, recalcula os atributos e consome uma escolha pendente.

        Valida tudo antes de alterar o estado: uma chamada inválida não deixa o mundo
        a meio (por exemplo, augment adicionado sem escolha consumida).
        """
        if self.progression.pending_choices <= 0:
            raise ValueError("no pending choices")
        if self._offer is None or augment not in self._offer.choices:
            raise ValueError("augment does not belong to the current offer")
        weapons = [w.name for w in self.player.available_weapons]
        choice = self.progression.next_choice
        is_bonus = choice is not None and (
            choice.weapon is not None or choice.prismatic_source is not None
        )
        position = self.growth_position() if augment.id == "siege_frame" else None
        if augment.id == "siege_frame" and position is None:
            raise ValueError("no reachable space for Siege Frame")
        self.inventory.add(augment, weapons, ignore_stack_limit=is_bonus)
        self.player.set_modifiers(self.inventory.modifiers)
        if position is not None:
            self.player.position = position
        self._sync_behaviors()
        self.progression.consume_choice()
        self._offer = None

    def _sync_behaviors(self) -> None:
        """Cria/atualiza os comportamentos concedidos pelos modificadores atuais."""
        for kind, level in self.inventory.modifiers.behaviors.items():
            behavior = self.behaviors.get(kind)
            if behavior is None:
                self.behaviors[kind] = BEHAVIOR_TYPES[kind](level)
            else:
                behavior.set_level(level)  # mantém o estado (p. ex. o ângulo dos satélites)

    # ------------------------------------------------------------------ comandos

    def apply(self, command: Command, dt: float) -> bool:
        if self.result is not None or not self.player.alive:
            return False
        if isinstance(command, Shoot):
            weapon = self.player.try_fire()
            if weapon is None:
                return False
            self._fire_weapon(weapon)
            return True
        self.player.apply(command, dt)
        self._constrain(self.player.position, self.player.radius)
        return True

    def fire_held(self, dt: float, held: bool) -> bool:
        """Consume only elapsed firing time; idle/empty frames never bank shots."""
        p = self.player
        slot = p.weapon_slot
        if not held or not p.alive or self.result is not None:
            p._cooldowns[slot] = max(0.0, p._cooldowns[slot] - dt)
            return False
        remaining, fired = dt, False
        while p.ammo > 0 and p._cooldowns[slot] <= remaining:
            offset = p._cooldowns[slot]
            remaining -= offset
            p._cooldowns[slot] = 0
            weapon = p.try_fire()
            if weapon is None:
                break
            self._fire_weapon(weapon, self.elapsed + dt - remaining, remaining)
            fired = True
        p._cooldowns[slot] = max(0.0, p._cooldowns[slot] - remaining)
        return fired

    def emit_projectile(self, projectile) -> None:
        """Test muzzle offsets too, so parallel shots cannot spawn through cover."""
        start, end = self.player.position, projectile.position
        hits = [(t, o) for o in self.map.obstacles
                if (t := self._segment_obstacle_hit(start, end, o, projectile.radius)) is not None]
        if hits:
            t, obstacle = min(hits, key=lambda item: item[0])
            if obstacle.is_barrel:
                self.damage_barrel(obstacle, projectile.damage, weapon_name=projectile.weapon_name)
            self.detonate_round(projectile, start + (end-start)*t)
            return
        self.projectiles.append(projectile)

    def _fire_weapon(self, weapon, fired_at=None, travel_dt=None) -> None:
        p = self.player
        origin = p.position + p.orientation * (p.radius + MUZZLE_GAP)
        half_cone = weapon.spread_degrees / 2
        count = weapon.pellets * p.modifiers.projectile_count
        templates = []
        parallel_angle = self.rng.uniform(-half_cone, half_cone) if half_cone else 0.0
        for index in range(count):
            angle = (self.rng.uniform(-half_cone, half_cone)
                     if weapon.name == "Shotgun" else parallel_angle)
            direction = p.orientation.rotate(angle)
            offset = (p.orientation.rotate(90) * ((index - (count-1)/2) * PARALLEL_SPACING)
                      if weapon.name != "Shotgun" else Vector2())
            projectile = Projectile(
                position=Vector2(origin + offset),
                velocity=direction * weapon.projectile_speed,
                damage=weapon.damage,
                radius=weapon.projectile_radius,
                range_left=weapon.projectile_range,
                color=weapon.color,
                sprite_key=("projectiles/player_pellet.png" if weapon.name == "Shotgun"
                            else "projectiles/player_bullet.png"),
                weapon_name=weapon.name,
                blast_damage=ROUND_BLAST_AD_RATIO * p.attack_damage * p.modifiers.rupture_rounds,
                blast_radius=((ROUND_BLAST_RADIUS + ROUND_BLAST_RADIUS_PER_STACK *
                               (p.modifiers.rupture_rounds-1)) * (1+p.modifiers.blast_radius_bonus)
                              if p.modifiers.rupture_rounds else 0.0),
            )
            for behavior in self.behaviors.values():
                behavior.on_fire(self, projectile)
            templates.append(replace(projectile, position=projectile.position - p.position, hit_ids=set()))
            if self.rng.random() < min(1, p.modifiers.crit_chance):
                projectile.critical = True
                projectile.damage *= p.crit_multiplier
                projectile.color = (255, 240, 120)
            self.emit_projectile(projectile)
            projectile.first_step = travel_dt
        self.combat.queue_echoes(self, templates, self.elapsed if fired_at is None else fired_at)

    def growth_position(self):
        """Reachable positions with the old radius; growth needs a clear new circle."""
        old = self.player.radius
        new = 24 * (1 + .05 * (self.player.modifiers.siege_stacks + 1))
        area = self.map.playable_bounds
        if new * 2 > min(area.width, area.height):
            return None
        def fits(point, radius):
            return (area.left + radius <= point.x <= area.right - radius
                    and area.top + radius <= point.y <= area.bottom - radius
                    and all(self._obstacle_contact(point, radius, o) is None for o in self.map.obstacles))
        start = self.player.position
        if fits(start, new):
            return Vector2(start)
        queue = deque([(Vector2(start), (0, 0))]); seen = {(0, 0)}
        while queue:
            point, cell = queue.popleft()
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                key = cell[0]+dx, cell[1]+dy
                if key in seen:
                    continue
                seen.add(key)
                nxt = start + Vector2(key)*16
                if not fits(nxt, old):
                    continue
                if any(self._segment_obstacle_hit(point, nxt, o, old) is not None for o in self.map.obstacles):
                    continue
                if fits(nxt, new):
                    return nxt
                queue.append((nxt, key))
        return None

    # ------------------------------------------------------------------ inimigos

    def spawn_enemy(
        self,
        definition: EnemyDef,
        position: Vector2,
        *,
        health_multiplier: float = 1.0,
        speed_multiplier: float = 1.0,
        jitter: float = SPAWN_JITTER,
        damage_multiplier: float = 1.0,
        reward_multiplier: float = 1.0,
        xp_reward_multiplier: float = 1.0,
        timing_multiplier: float = 1.0,
        damage_cap_fraction: float | None = None,
        is_elite: bool = False,
        is_prismatic: bool = False,
        lethal_attacks: bool = False,
    ) -> Enemy:
        offset = Vector2(
            self.rng.uniform(-jitter, jitter),
            self.rng.uniform(-jitter, jitter),
        )
        enemy = Enemy(
            id=self._next_enemy_id(),
            definition=definition,
            damage_multiplier=damage_multiplier,
            reward_multiplier=reward_multiplier,
            xp_reward_multiplier=xp_reward_multiplier,
            timing_multiplier=timing_multiplier,
            damage_cap_fraction=damage_cap_fraction,
            is_elite=is_elite,
            is_prismatic=is_prismatic,
            lethal_attacks=lethal_attacks,
            position=Vector2(position) + offset,
            health=definition.max_health * health_multiplier,
            speed=definition.speed * speed_multiplier,
            steer_degrees=self.rng.choice((-1, 1)) * self.rng.uniform(8, 20),
        )
        self.enemies.append(enemy)
        return enemy

    def can_spawn_at(self, position: Vector2, radius: float) -> bool:
        area = self.map.playable_bounds
        if not (area.left + radius <= position.x <= area.right - radius
                and area.top + radius <= position.y <= area.bottom - radius):
            return False
        if any(self._obstacle_contact(position, radius, o) is not None for o in self.map.obstacles):
            return False
        return not any(e.alive and circle_circle(position, radius, e.position, e.radius)
                       for e in self.enemies)

    # ------------------------------------------------------------------ serviços de comportamentos

    def damage_enemy(self, enemy: Enemy, amount: float, chain_depth: int = 0, *,
                     weapon_name: str | None = None) -> bool:
        """Único caminho de dano a inimigos: a morte publica o evento e chama os ganchos.

        `chain_depth` conta mortes encadeadas por efeitos (explosões), para as limitar.
        """
        if not enemy.take_damage(amount):
            return False
        weapon_name = weapon_name or self.player.weapon.name
        self.last_kill_weapon = weapon_name
        d = enemy.definition
        if enemy.is_boss:
            for projectile in self.projectiles:
                if projectile.owner_id == enemy.id:
                    projectile.alive = False
        self.corpses.append(enemy)
        self.events.publish(EnemyKilled(enemy.id, round(d.xp_reward*enemy.reward_multiplier
                                                        * enemy.xp_reward_multiplier),
                                        round(d.coin_reward*enemy.reward_multiplier), d.is_boss,
                                        weapon_name, enemy.is_prismatic))
        self.ammo_drops.drop(enemy.position, self.rng)
        for behavior in tuple(self.behaviors.values()):
            behavior.on_kill(self, enemy, chain_depth, weapon_name)
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
        if not enemy.alive:
            return
        enemy.steering = self.navigator.direction(enemy.id, enemy.position, self.player.position, enemy.radius)
        enemy.can_see = self.line_of_sight(enemy.position, self.player.position)
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

    def detonate_round(self, projectile, point) -> None:
        """Primary impacts splash enemies/barrels; splash never creates another bullet proc."""
        if not projectile.primary or projectile.hostile or projectile.blast_damage <= 0:
            return
        radius = projectile.blast_radius
        self.add_fx("round_explosion", point, radius, .4)
        for enemy in tuple(self.enemies):
            if enemy.alive and enemy.position.distance_to(point) <= radius + enemy.radius:
                self.damage_enemy(enemy, projectile.blast_damage, weapon_name=projectile.weapon_name)
        for obstacle in tuple(self.map.obstacles):
            if obstacle.is_barrel and Vector2(obstacle.rect.center).distance_to(point) <= radius + obstacle.rect.width/2:
                self.damage_barrel(obstacle, projectile.blast_damage, weapon_name=projectile.weapon_name)

    @property
    def barrel_max_health(self) -> float:
        multiplier = (self.director.config.health_multiplier(max(1, self.director.round_number))
                      if self.director is not None else 1.0)
        return BASIC.max_health * multiplier

    def barrel_health(self, obstacle: ObstacleDef) -> float:
        if obstacle.key in self.map._destroyed_obstacles:
            return 0.0
        return max(0.0, self.barrel_max_health - self._barrel_damage.get(obstacle.key, 0.0))

    def damage_barrel(self, obstacle: ObstacleDef, amount: float, *,
                      weapon_name: str | None = None) -> None:
        """Destroy barrels once; process chained blasts iteratively."""
        pending = [(obstacle, amount)]
        while pending:
            barrel, damage = pending.pop()
            if not barrel.is_barrel or barrel.key in self.map._destroyed_obstacles:
                continue
            self._barrel_damage[barrel.key] = self._barrel_damage.get(barrel.key, 0.0) + damage
            if self.barrel_health(barrel) > 0:
                continue
            self.map.destroy_obstacle(barrel)
            self._barrel_damage.pop(barrel.key, None)
            self.navigator.clear()
            center = Vector2(barrel.rect.center)
            blast_damage = self.barrel_max_health * 2
            self.add_fx("barrel_explosion", center, BARREL_BLAST_RADIUS, 0.5)
            for enemy in tuple(self.enemies):
                if enemy.alive and enemy.position.distance_to(center) <= BARREL_BLAST_RADIUS + enemy.radius:
                    self.damage_enemy(enemy, blast_damage, weapon_name=weapon_name)
            if self.player.alive and self.player.position.distance_to(center) <= BARREL_BLAST_RADIUS + self.player.radius:
                self.player.take_damage(min(blast_damage, self.player.max_health * 0.49))
            for other in self.map.obstacles:
                if other.is_barrel and Vector2(other.rect.center).distance_to(center) <= BARREL_BLAST_RADIUS + other.rect.width / 2:
                    pending.append((other, blast_damage))

    def _advance_projectile(self, proj: Projectile, dt: float) -> None:
        if proj.first_step is not None:
            dt = min(dt, proj.first_step)
            proj.first_step = None
        start = Vector2(proj.position)
        step = proj.velocity * dt
        travel = step.length()
        if travel == 0:
            return
        if travel > proj.range_left:
            step *= proj.range_left / travel
            travel = proj.range_left
        end = start + step

        best_t, best_target = 2.0, None  # 2.0 = ainda sem acerto
        for obstacle in self.map.obstacles:
            t = self._segment_obstacle_hit(start, end, obstacle, proj.radius)
            if t is not None and t < best_t:
                best_t, best_target = t, obstacle
        if proj.hostile:
            if proj.empowers_basic:
                margin = MAX_ENEMY_RADIUS_HINT + int(proj.radius)
                area = Rect(int(min(start.x,end.x))-margin, int(min(start.y,end.y))-margin,
                            int(abs(end.x-start.x))+2*margin, int(abs(end.y-start.y))+2*margin)
                for enemy in self._grid.query(area):
                    if not enemy.alive or enemy.is_empowered or enemy.definition is not BASIC:
                        continue
                    t = segment_circle_hit(start,end,enemy.position,enemy.radius+proj.radius)
                    if t is not None and t < best_t:
                        best_t,best_target = t,enemy
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
                if proj.hostile:
                    best_target.empower(SPEED)
                    proj.alive = False
                    return
                hit_point = start + (end - start) * best_t
                proj.hit_ids.add(best_target.id)
                self.combat.hit(self, proj, best_target)
                if proj.critical:
                    self.add_fx("critical", best_target.position, best_target.radius, .15)
                self.damage_enemy(best_target, proj.damage, weapon_name=proj.weapon_name)
                self.detonate_round(proj, hit_point)
                continues = False  # um comportamento (Ricochet) pode manter o projétil em voo
                for behavior in tuple(self.behaviors.values()):
                    continues = behavior.on_hit(self, proj, best_target, hit_point) or continues
                if continues:
                    return
            elif isinstance(best_target, ObstacleDef):
                if best_target.is_barrel:
                    self.damage_barrel(best_target, proj.damage, weapon_name=proj.weapon_name)
                self.detonate_round(proj, start + (end-start)*best_t)
            elif best_target is self.player:
                damage = self.player.max_health if proj.lethal else proj.damage
                if proj.damage_cap_fraction is not None and not proj.lethal:
                    damage = min(damage, self.player.max_health * proj.damage_cap_fraction)
                self.player.take_damage(damage)
            proj.alive = False  # sem comportamentos, uma bala acerta no máximo num alvo
            return

        proj.position = end
        proj.range_left -= travel
        if proj.range_left <= 0 or not self.map.playable_bounds.collidepoint(end):
            proj.alive = False

    @staticmethod
    def _segment_obstacle_hit(start: Vector2, end: Vector2, obstacle: ObstacleDef, radius: float = 0) -> float | None:
        if obstacle.circular:
            return segment_circle_hit(
                start, end, Vector2(obstacle.rect.center), obstacle.rect.width / 2 + radius
            )
        return swept_circle_aabb_hit(start, end, radius, obstacle.rect)

    # ------------------------------------------------------------------ tick

    def update(self, dt: float) -> None:
        if self.result is not None:
            return
        self._refresh_terrain()
        self.navigator.begin_frame()
        self.elapsed += dt
        self.combat.refresh(self)
        self.player.update(dt)
        self.ammo_notice_left = max(0.0, self.ammo_notice_left - dt)

        self._rebuild_grid()
        for enemy in self.enemies:
            self._update_enemy(enemy, dt)

        self._rebuild_grid()
        for proj in self.projectiles:
            if proj.alive:
                self._advance_projectile(proj, dt)

        for behavior in tuple(self.behaviors.values()):
            behavior.update(self, dt)
        self.combat.update(self)
        if not self.player.alive:
            self.combat.echoes.clear()
            if self.player.revivals_left:
                self.player.revivals_used += 1
                self.player.health = self.player.max_health * .5
        for effect in self.fx:
            effect.ttl -= dt
        self.fx = [f for f in self.fx if f.ttl > 0]
        self.bodies = [body for b in self.behaviors.values() for body in b.bodies(self)]

        self.enemies = [e for e in self.enemies if e.alive]
        for corpse in self.corpses:
            corpse.death_age += dt
        self.corpses = [e for e in self.corpses if e.death_age < 1.0]
        self.navigator.retain({e.id for e in self.enemies})
        self.projectiles = [p for p in self.projectiles if p.alive]
        if self.player.alive and self.ammo_drops.update(
            dt, self.player.position, self.player.radius, self.player.arsenal
        ):
            self.ammo_notice_left = 1.5

        if self.director is not None and self.player.alive:
            self.director.update(dt, self)
        if not self.player.alive and not self._death_published:
            self._death_published = True
            self.events.publish(PlayerDied(self.run_id))

    def _refresh_terrain(self) -> None:
        old_chunk = getattr(self.map, "_center_chunk", None)
        self.map.update(self.player.position)
        if not self.map.infinite:
            return
        if old_chunk != self.map._center_chunk:
            self.navigator.clear()
        for enemy in self.enemies:
            if enemy.alive and enemy.position.distance_to(self.player.position) > 1450:
                candidates = self.map.spawn_candidates(self.player.position, 900, self.viewport, 100+enemy.radius)
                point = next((p for p in candidates if self.can_spawn_at(p, enemy.radius)), None)
                if point is not None:
                    enemy.position = Vector2(point)
                    enemy.outbox.clear()
                    enemy.change_state(ChaseState())
        area = self.map.playable_bounds
        self.projectiles = [p for p in self.projectiles if area.collidepoint(p.position)]
        self.corpses = [e for e in self.corpses if area.collidepoint(e.position)]
        self.fx = [f for f in self.fx if area.collidepoint(f.position)]
        self.ammo_drops.pickups = [p for p in self.ammo_drops.pickups if area.collidepoint(p.position)]

    # ------------------------------------------------------------------ colisões com o mapa

    def _clamp_to_arena(self, position: Vector2, radius: float) -> None:
        if self.map.infinite:
            return
        area = self.map.playable_bounds
        position.x = max(area.left + radius, min(position.x, area.right - radius))
        position.y = max(area.top + radius, min(position.y, area.bottom - radius))

    @staticmethod
    def _obstacle_contact(position: Vector2, radius: float, obstacle: ObstacleDef):
        if obstacle.circular:
            return circle_circle(
                position, radius, Vector2(obstacle.rect.center), obstacle.rect.width / 2 + radius
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


    def finish(self, reason: RunReason) -> RunResult:
        """Congela um único resultado; chamadas repetidas devolvem o mesmo objeto."""
        if self.result is None:
            self.result = RunResult(self.run_id, reason, self.stats.round,
                                    self.stats.kills, self.progression.level,
                                    self.progression.total_xp, self.stats.coins, self.elapsed, self.map.name)
            self.events.publish(RunFinished(self.result))
        return self.result
