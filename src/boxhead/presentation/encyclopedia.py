"""Read-only reference entries, sourced from the same catalogs as gameplay."""
from dataclasses import dataclass

from boxhead.presentation.icons import augment_icon, shop_icon
from boxhead.world.augments import AUGMENTS, DEFAULT_OFFER, Rarity
from boxhead.world.enemy import BASIC, RED, BOSS
from boxhead.world.weapons import WEAPONS
from boxhead.world.rounds import DEFAULT_ROUNDS
from boxhead.shop import UPGRADES

CATEGORIES = ('Augments', 'Weapons', 'Enemies', 'Shop', 'Field Guide')
NOTES = {
    'split_chamber': 'Multiplies the full salvo, including shotgun pellets. Still consumes one ammo per original shot. Pistol and SMG copies fly in parallel.',
    'rupture_rounds': 'Primary impacts explode on enemies or cover. Blast Bloom increases the radius. Splash can detonate barrels but cannot crit or trigger on-hit effects. Aftershot echoes do not explode.',
    'ember_rounds': 'Each primary hit adds an independent three-second burn. Damage scales with AD and stacks, not enemy health or critical damage. Echoes do not apply burns.',
    'slipstream_feed': 'Each primary hit gives movement for five seconds and refreshes the whole chain. Half of bonus movement becomes additional attack speed. No hits for five seconds clears the chain.',
    'redline': 'Requires some critical chance to appear. Critical primary hits build attack speed; each refreshes the four-second chain. Echoes do not activate it.',
    'last_spark': 'Each acquired stack grants one revival charge. Returns at half maximum health, with no timed invulnerability. Charges are consumed permanently for this run.',
    'siege_frame': 'Scales total health and AD after flat bonuses. Sprite and hitbox grow together. Bigger size can close narrow routes; only offered when reachable space permits growth.',
    'aftershot': 'Each stack adds an echo at another 0.2-second interval. Echoes copy the original salvo at 40% normal damage, cost no ammo and cannot crit or trigger primary hit effects.',
    'blast_bloom': 'Increases player explosion radius, including Chain Reaction and Rupture Rounds. Does not change barrel or enemy explosions, or explosion damage.',
    'crit_chance': 'Each main bullet rolls independently. Above 100%, hits are guaranteed critical and half of the excess chance becomes bonus critical damage.',
    'crit_damage': 'Adds to the critical multiplier: a +0.15 upgrade changes 2.00x into 2.15x. Burns, splash, orbitals and echoes cannot crit.',
    'ricochet': 'Primary ricochets keep their critical result and can activate primary hit effects on each new enemy. A bullet never hits the same enemy twice.',
    'chain_reaction': 'Kills create explosions that can kill more enemies. Blast Bloom scales the radius. Chain depth is limited to prevent recursive explosions.',
    'orbitals': 'Satellites orbit your character and damage nearby enemies. They do not use ammunition or trigger bullet on-hit effects.',
}


@dataclass(frozen=True)
class Entry:
    key: str
    name: str
    category: str
    tag: str
    description: str
    icon: tuple[str, int]
    rows: tuple[tuple[str, str], ...] = ()
    color: tuple[int, int, int] = (246, 203, 104)


def entries(profile):
    result = []
    colors = {Rarity.GRAY:(167,183,200), Rarity.GOLD:(246,203,104), Rarity.PRISMATIC:(192,143,255)}
    for a in AUGMENTS:
        rows = [('Target', a.weapon or 'All weapons / character'), ('Stack limit','Unlimited'),
                ('Acquired from','Level-up offers' if a.rarity is not Rarity.GRAY else 'Level-ups / round reward')]
        if a.rarity is Rarity.PRISMATIC:
            rows.append(('Guaranteed offers','Boss / Prismatic enemy kills'))
        if a.requires: rows.append(('Requires',', '.join(a.requires)))
        if a.incompatible_with: rows.append(('Excludes',', '.join(a.incompatible_with)))
        result.append(Entry(a.id,a.name,'Augments',a.rarity.value.upper(),
                            a.description.rstrip('. ')+'. '+NOTES.get(a.id,''),augment_icon(a.id),tuple(rows),colors[a.rarity]))
    for i,w in enumerate(WEAPONS):
        unlock = next((u for u in UPGRADES if u.weapon==w.name),None)
        owned = unlock is None or profile.level(unlock.id)>0
        result.append(Entry(w.name,w.name,'Weapons','BASE WEAPON',
                            'Choose one owned weapon before a run. AD and attack speed apply globally; gray augments specialize your chosen weapon.',
                            ('weapons/weapon_icons.png',i),(
                                ('Damage / bullet',f'{w.damage:g}'),('Shots / second',f'{1/w.cooldown:.2f}'),
                                ('Pellets / salvo',str(w.pellets)),('Range',f'{w.projectile_range:g}'),
                                ('Bullet speed',f'{w.projectile_speed:g}/s'),('Starting ammo',str(w.starting_ammo)),
                                ('Capacity / crate',f'{w.max_ammo} / +{w.pickup_ammo}'),
                                ('Unlock','Free' if unlock is None else f'{unlock.base_cost} coins'),
                                ('Your profile','Owned' if owned else 'Not purchased'))))
    cfg=DEFAULT_ROUNDS
    for e in (BASIC,RED,BOSS):
        attack = 'LETHAL' if e.is_boss else str(e.ranged.damage if e.ranged else e.contact_damage)
        description = ('A melee pursuer. Health, speed and damage scale with the round.' if e is BASIC else
                       'A ranged enemy that prepares before firing. Needs line of sight. Appears from round 3.' if e is RED else
                       f'Appears every {cfg.boss_every} rounds with escorts. First boss uses base HP; each following boss has {cfg.boss_health_growth:g}x the previous health. Hits are lethal; Last Spark can save you.')
        result.append(Entry(e.name,e.name,'Enemies','BOSS' if e.is_boss else 'BASE STATS',description,
                            (f'{e.sprite_prefix}_walk.png',0),(
                                ('Base health',f'{e.max_health:g}'),('Base speed',f'{e.speed:g}/s'),
                                ('Hit damage',attack),('Windup',f'{e.windup:g}s'),('Recovery',f'{e.recovery:g}s'),
                                ('Base XP / coins',f'{e.xp_reward} / {e.coin_reward}'))))
    result.extend((
        Entry('elite','Elite','Enemies','ENEMY VARIANT','Basic or Red with extra health. Golden ELITE label. Not a separate attack type.',
              ('augments/augment_icons.png',3),(('Starts at round',str(cfg.elite_start_round)),
              ('Health',f'{cfg.elite_health_multiplier:g}x round health'),('XP',f'{cfg.elite_xp_multiplier:g}x'),
              ('Initial chance',f'{cfg.elite_start_chance:.0%}'),('Growth / cap',f'+{cfg.elite_chance_per_round:.0%} per round / {cfg.max_elite_chance:.0%}'))),
        Entry('prismatic_enemy','Prismatic','Enemies','ENEMY VARIANT','One Basic or Red variant replaces a normal spawn every five rounds. Does not also become Elite. Its death guarantees a purple augment offer.',
              ('augments/augment_icons.png',7),(('Every',f'{cfg.prismatic_every} rounds'),('Health',f'{cfg.prismatic_health_multiplier:g}x round health')),
              (192,143,255)),
    ))
    for u in UPGRADES:
        level=profile.level(u.id)
        result.append(Entry(u.id,u.name,'Shop','PERMANENT',u.description+'. Purchases persist between runs; visit the Shop to buy.',shop_icon(u.id),(
            ('Your level',f'{level} / {u.max_level}'),('Base price',f'{u.base_cost} coins'),
            ('Price growth',f'{u.cost_growth:g}x per level'),('Next price','MAX / OWNED' if level>=u.max_level else f'{u.cost(level)} coins'),
            ('Type','Weapon unlock' if u.weapon else 'Starting stat upgrade'))))
    result.extend((
        Entry('rounds','Round Scaling','Field Guide','SURVIVAL RULES',
              'Clear all spawned enemies to finish a round. The final off-screen enemies receive direction pointers. Health grows linearly through round 10, then exponentially.',
              ('augments/augment_icons.png',0),(
                  ('First wave / growth',f'{cfg.base_enemies} / {cfg.enemy_growth:g}x'),
                  ('Wave cap / active cap',f'{cfg.max_budget} / {cfg.max_alive}'),
                  ('HP rounds 1-10',f'+{cfg.health_per_round:.0%} base per round'),
                  ('HP after round 10',f'{cfg.health_growth:g}x per round'),
                  ('Normal damage cap',f'{cfg.normal_damage_cap:.0%} of player max HP'))),
        Entry('rewards','Augment Offers','Field Guide','BUILD YOUR RUN',
              'One rarity is rolled for the whole level-up offer, then you choose ONE card. End-of-round gray rewards target your run weapon. Bosses and Prismatic enemies guarantee purple offers. Eligibility and fallback can change the offered rarity.',
              ('augments/augment_icons.png',4),tuple((r.value.title(),f'{weight/sum(w for _,w in DEFAULT_OFFER.weights):.0%}') for r,weight in DEFAULT_OFFER.weights)),
        Entry('barrels','Explosive Barrels','Field Guide','ENVIRONMENT',
              'Barrels have the health of a Basic enemy in the current round. Destroying one causes an orange explosion that damages enemies, players and nearby barrels. Rupture Rounds may trigger them. Destruction persists within the run.',
              ('environment/obstacles.png',2),(('Blast radius','180'),('Blast damage','2x current Basic health'),('Player damage cap','49% max HP per explosion'))),
    ))
    order = {'PRISMATIC':0,'GOLD':1,'GRAY':2}
    return tuple(sorted(result,key=lambda e:(CATEGORIES.index(e.category),order.get(e.tag,3),e.name.casefold())))
