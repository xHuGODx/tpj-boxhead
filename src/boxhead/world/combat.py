"""Run-only hit effects and delayed salvos; no rendering or profile writes."""
from dataclasses import dataclass, field, replace
from pygame import Vector2

from boxhead.world.projectile import Projectile

BURN_SECONDS = 3.0
BURN_AD_RATIO = .02
SLIP_SECONDS = 5.0
SLIP_MOVE_PER_HIT = .005
REDLINE_SECONDS = 4.0
REDLINE_AS_PER_HIT = .02
ECHO_DELAY = .20
ECHO_DAMAGE = .40
PARALLEL_SPACING = 10.0
ROUND_BLAST_RADIUS = 90.0
ROUND_BLAST_RADIUS_PER_STACK = 10.0
ROUND_BLAST_AD_RATIO = .10


@dataclass
class Burn:
    enemy: object
    dps: float
    expiry: float
    last_tick: float
    weapon: str | None


@dataclass
class CombatEffects:
    burns: dict = field(default_factory=dict)
    echoes: list = field(default_factory=list)
    slip_bonus: float = 0.0
    slip_until: float = 0.0
    rhythm_bonus: float = 0.0
    rhythm_until: float = 0.0
    slip_hits: int = 0
    rhythm_hits: int = 0

    def refresh(self, world):
        now = world.elapsed
        if now >= self.slip_until:
            self.slip_bonus = 0; self.slip_hits = 0
        if now >= self.rhythm_until:
            self.rhythm_bonus = 0; self.rhythm_hits = 0
        world.player.temporary_move = self.slip_bonus
        world.player.temporary_as = self.rhythm_bonus

    def hit(self, world, projectile, enemy):
        if not projectile.primary or not enemy.alive:
            return
        mods, now = world.player.modifiers, world.elapsed
        if mods.ember_rounds:
            dps = BURN_AD_RATIO * world.player.attack_damage * mods.ember_rounds
            key = (enemy.id, now, dps, projectile.weapon_name)
            if key in self.burns:
                self.burns[key].dps += dps
            else:
                self.burns[key] = Burn(enemy, dps, now + BURN_SECONDS, now, projectile.weapon_name)
        if mods.slipstream_feed:
            self.slip_bonus += SLIP_MOVE_PER_HIT * mods.slipstream_feed
            self.slip_hits += 1
            self.slip_until = now + SLIP_SECONDS
        if mods.redline and projectile.critical:
            self.rhythm_bonus += REDLINE_AS_PER_HIT * mods.redline
            self.rhythm_hits += 1
            self.rhythm_until = now + REDLINE_SECONDS
        self.refresh(world)

    def queue_echoes(self, world, templates, fired_at):
        for n in range(world.player.modifiers.aftershot):
            copies = tuple(replace(p, position=Vector2(p.position), velocity=Vector2(p.velocity),
                                   damage=p.damage * ECHO_DAMAGE, primary=False, critical=False,
                                   blast_damage=0.0, blast_radius=0.0,
                                   hit_ids=set()) for p in templates)
            self.echoes.append((fired_at + ECHO_DELAY * (n + 1), copies))

    def update(self, world):
        for key, burn in tuple(self.burns.items()):
            end = min(world.elapsed, burn.expiry)
            if burn.enemy.alive and end > burn.last_tick:
                world.damage_enemy(burn.enemy, burn.dps * (end - burn.last_tick), weapon_name=burn.weapon)
            burn.last_tick = end
            if not burn.enemy.alive or world.elapsed >= burn.expiry:
                del self.burns[key]
        if not world.player.alive:
            self.echoes.clear()
        pending = []
        for at, templates in self.echoes:
            if not world.player.alive:
                pending.clear()
                break
            if at <= world.elapsed:
                for template in templates:
                    if not world.player.alive:
                        break
                    world.emit_projectile(replace(template, position=world.player.position + template.position,
                                                  hit_ids=set()))
            else:
                pending.append((at, templates))
        self.echoes = pending
        self.refresh(world)
