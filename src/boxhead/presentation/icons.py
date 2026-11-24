"""Explicit semantic icon assignments, shared by cards, HUD and shop.

Atlas: 0 heavy bullet, 1 boot, 2 three rounds, 3 heart, 4 XP,
5 bouncing arrows, 6 blast, 7 satellite, 8 fast bullet, 9 two rounds,
10 crosshair, 11 medical cross. Reuse is intentional: only 12 symbols exist.
"""
AUGMENT_ATLAS = "augments/augment_icons.png"
ICONS = {
    "pistol_damage": 0, "shotgun_damage": 0, "smg_damage": 0,
    "pistol_rate": 8, "shotgun_rate": 8, "smg_rate": 8,
    "shotgun_pellets": 2, "pistol_range": 10, "smg_range": 10,
    "attack_damage": 0, "attack_speed": 8, "vitality": 3,
    "swift": 1, "regeneration": 11, "quick_learner": 4,
    "juggernaut": 3, "sprinter": 1, "ricochet": 5,
    "chain_reaction": 6, "orbitals": 7, "crit_chance": 10,
    "crit_damage": 0, "split_chamber": 2, "ember_rounds": 6,
    "blast_bloom": 6, "slipstream_feed": 1, "last_spark": 11,
    "siege_frame": 3, "redline": 8, "aftershot": 9,
}


def augment_icon(key):
    return AUGMENT_ATLAS, ICONS[key]


def shop_icon(key):
    dedicated = {"max_health": ("shop/shop_upgrades.png", 0),
                 "speed": ("shop/shop_upgrades.png", 1),
                 "xp_gain": ("shop/shop_upgrades.png", 2),
                 "weapon_smg": ("weapons/weapon_icons.png", 2),
                 "weapon_shotgun": ("weapons/weapon_icons.png", 1)}
    return dedicated[key] if key in dedicated else augment_icon(key)
