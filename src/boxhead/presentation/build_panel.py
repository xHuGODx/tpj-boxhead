"""Read-only pause build panel, drawn on a fixed canvas for consistent scaling."""
import pygame

from boxhead.core.catalog import catalog
from boxhead.presentation.icons import augment_icon
from boxhead.presentation.sprites import SpritePainter
from boxhead.world.augments import Rarity

SIZE = (1100, 700)
TEXT = (233, 237, 245)
MUTED = (137, 153, 176)
GOLD = (246, 203, 104)
COLORS = {Rarity.GRAY: (167, 183, 200), Rarity.GOLD: GOLD,
          Rarity.PRISMATIC: (192, 143, 255)}
VISIBLE = 5


class BuildPanel:
    def __init__(self):
        self.canvas = pygame.Surface(SIZE, pygame.SRCALPHA)
        self.fonts = {size: pygame.font.Font(None, size) for size in (18, 20, 22, 24, 28, 34, 48)}
        self.painter = SpritePainter(catalog())
        self.painter.prepare(['augments/augment_icons.png', 'weapons/weapon_icons.png'])

    @staticmethod
    def owned(world):
        return sorted(world.inventory.owned(), key=lambda item:
                      ({Rarity.PRISMATIC: 0, Rarity.GOLD: 1, Rarity.GRAY: 2}[item[0].rarity], item[0].name))

    def text(self, value, position, size=22, color=TEXT, right=False):
        img = self.fonts[size].render(str(value), True, color)
        rect = img.get_rect(topright=position) if right else img.get_rect(topleft=position)
        self.canvas.blit(img, rect)

    def wrapped(self, text, rect, color=MUTED):
        words, line, y = text.split(), '', rect.y
        for word in words:
            candidate = f'{line} {word}'.strip()
            if self.fonts[20].size(candidate)[0] > rect.width and line:
                if y + 20 > rect.bottom:
                    return
                self.text(line, (rect.x,y), 20, color)
                line, y = word, y+20
            else:
                line = candidate
        if y + 20 <= rect.bottom:
            self.text(line, (rect.x,y), 20, color)

    def panel(self, rect, label, subtitle):
        pygame.draw.rect(self.canvas, (20, 28, 42), rect, border_radius=14)
        pygame.draw.rect(self.canvas, (51, 66, 89), rect, 1, border_radius=14)
        pygame.draw.line(self.canvas, GOLD, (rect.x+18,rect.y+24), (rect.x+18,rect.y+42), 3)
        self.text(label, (rect.x+30,rect.y+20), 28)
        self.text(subtitle, (rect.x+18,rect.y+54), 18, MUTED)

    def rows(self, x, y, width, rows):
        for i, (label,value) in enumerate(rows):
            top = y+i*28
            if i%2 == 0:
                pygame.draw.rect(self.canvas,(25,35,51),(x-6,top-3,width+12,26),border_radius=4)
            self.text(label,(x,top),20,MUTED)
            self.text(value,(x+width,top),22,TEXT,True)

    def draw(self, surface, world, index, action):
        self.canvas.fill((10, 15, 25, 246))
        for y in range(100):
            pygame.draw.line(self.canvas, (20+y//8, 23+y//12, 42+y//6), (0,y),(1100,y))
        self.text('RUN DOSSIER', (32,24), 48)
        self.text('PAUSED / YOUR BUILD', (34,72), 18, GOLD)
        p, m, weapon = world.player, world.player.modifiers, world.player.weapon
        round_number = world.director.round_number if world.director else world.stats.round
        self.text(f'ROUND {round_number:02}   /   LV {world.progression.level:02}',(1068,28),28,GOLD,True)
        self.text(f'{world.map.name}  /  {world.elapsed/60:.0f}m {world.elapsed%60:02.0f}s  /  {world.stats.kills} kills',
                  (1068,65),20,MUTED,True)
        self.panel(pygame.Rect(32,112,250,492),'SURVIVOR','Effective stats / live bonuses included')
        self.text(f'{p.health:,.0f} / {p.max_health:,.0f} HP',(50,192),28,(125,223,173))
        pygame.draw.rect(self.canvas,(38,53,62),(50,226,214,6),border_radius=3)
        pygame.draw.rect(self.canvas,(100,210,160),(50,226,round(214*max(0,p.health/p.max_health)),6),border_radius=3)
        self.rows(50,252,214,[
            ('Attack damage',f'{p.attack_damage:,.1f}'), ('Attack speed',f'{p.attack_speed:.2f}x'),
            ('Critical chance',f'{m.crit_chance:.0%}'), ('Critical damage',f'{p.crit_multiplier:.2f}x'),
            ('Movement',f'{p.speed:,.0f}/s'), ('Regeneration',f'{m.regen_per_second:.1f}/s'),
            ('XP gain',f'{m.xp_gain_multiplier:.2f}x'), ('Body size',f'{p.size_multiplier:.2f}x'),
            ('Blast radius',f'{1+m.blast_radius_bonus:.2f}x'), ('Revival charges',p.revivals_left),
        ])
        self.text(f'SLIP {world.combat.slip_hits}    REDLINE {world.combat.rhythm_hits}',(50,570),18,GOLD)
        self.panel(pygame.Rect(298,112,250,492),'LOADOUT',weapon.name.upper())
        self.painter.blit(self.canvas,'weapons/weapon_icons.png',(423,217),(86,86),p.weapon_slot)
        projectiles = weapon.pellets*m.projectile_count
        expected = weapon.damage*projectiles/weapon.cooldown * (1+min(1,m.crit_chance)*(p.crit_multiplier-1))
        self.rows(316,278,214,[
            ('Damage / bullet',f'{weapon.damage:,.1f}'), ('Shots / second',f'{1/weapon.cooldown:,.2f}'),
            ('Bullets / salvo',projectiles), ('Projectile count',f'{m.projectile_count}x'),
            ('Range',f'{weapon.projectile_range:,.0f}'), ('Bullet speed',f'{weapon.projectile_speed:,.0f}/s'),
            ('Ammo',f'{p.ammo} / {weapon.max_ammo}'), ('Direct DPS*',f'{expected:,.0f}'),
        ])
        self.wrapped('*All bullets hit; includes crit average. Excludes burns, echoes and splash.',pygame.Rect(316,518,214,65))
        self.panel(pygame.Rect(564,112,504,492),'AUGMENT ARCHIVE','Rarity sorted / every selected augment and stack')
        owned = self.owned(world)
        index = max(0,min(index,len(owned)-1))
        first = min(max(0,index-VISIBLE+1),max(0,len(owned)-VISIBLE))
        if not owned:
            self.text('A blank slate.',(588,234),34)
            self.wrapped('Your chosen augments will appear here. Permanent shop stats are already included on the left.',
                         pygame.Rect(588,284,440,100))
        for row,(augment,stacks) in enumerate(owned[first:first+VISIBLE]):
            selected = first+row==index
            rect=pygame.Rect(580,194+row*56,470,50)
            color=COLORS[augment.rarity]
            pygame.draw.rect(self.canvas,(37,39,58) if selected else (25,33,47),rect,border_radius=7)
            if selected: pygame.draw.rect(self.canvas,color,rect,1,border_radius=7)
            key,icon=augment_icon(augment.id)
            self.painter.blit(self.canvas,key,(606,rect.centery),(34,34),icon)
            self.text(augment.name,(634,rect.y+7),22,color)
            self.text(augment.rarity.value.upper(),(634,rect.y+29),18,MUTED)
            self.text(f'x{stacks}',(1035,rect.y+13),24,color,True)
        if owned:
            a,stacks=owned[index]
            self.text(f'{index+1:02} / {len(owned):02}  /  {sum(n for _,n in owned)} total stacks',
                      (1048,170),18,MUTED,True)
            pygame.draw.line(self.canvas,(51,66,89),(584,488),(1048,488))
            self.text(a.name,(584,504),24,COLORS[a.rarity])
            self.wrapped(a.description,pygame.Rect(584,536,462,62),TEXT)
            if len(owned)>VISIBLE:
                height=280*VISIBLE/len(owned)
                y=194+(280-height)*first/(len(owned)-VISIBLE)
                pygame.draw.rect(self.canvas,GOLD,(1057,round(y),3,round(height)),border_radius=1)
        for i,label in enumerate(('RESUME','MAIN MENU')):
            rect=pygame.Rect(32+i*185,626,173,40)
            pygame.draw.rect(self.canvas,GOLD if action==i else (29,39,55),rect,border_radius=7)
            image=self.fonts[24].render(label,True,(16,22,34) if action==i else MUTED)
            self.canvas.blit(image,image.get_rect(center=rect.center))
        self.text('W/S archive  /  A/D action  /  SPACE confirm  /  ESC resume', (1068,640),20,MUTED,True)
        scale=min(surface.get_width()/1100,surface.get_height()/700)
        size=(round(1100*scale),round(700*scale))
        image=pygame.transform.smoothscale(self.canvas,size)
        surface.blit(image,image.get_rect(center=surface.get_rect().center))
