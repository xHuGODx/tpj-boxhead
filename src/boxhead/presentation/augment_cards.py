"""Apresentação das cartas: layout proporcional, tipografia e seleção.

Usa um canvas lógico para manter desenho e áreas de clique alinhados em qualquer
resolução. Apenas lê a oferta e a progressão; confirmar escolhas pertence ao estado.
"""
import pygame

from boxhead.core.catalog import catalog
from boxhead.presentation.sprites import SpritePainter
from boxhead.presentation.icons import augment_icon
from boxhead.world.augments import Rarity

SIZE = (1536, 1024)
CARD_SIZE = (420, 560)
GAP = 36
COLORS = {
    Rarity.GRAY: (190, 194, 210),
    Rarity.GOLD: (255, 207, 40),
    Rarity.PRISMATIC: (205, 145, 255),
}
LABELS = {Rarity.GRAY: "GRAY", Rarity.GOLD: "GOLD", Rarity.PRISMATIC: "PRISMATIC"}


def wrap(font, text, width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    return [*lines, current] if current else lines


class AugmentCards:
    def __init__(self):
        self._canvas = pygame.Surface(SIZE, pygame.SRCALPHA)
        self._fonts = {}
        self._painter = SpritePainter(catalog())
        self._painter.prepare(["cards/card_frames.png", "augments/augment_icons.png"])

    @staticmethod
    def _transform(size):
        height = 815 if size[0]/size[1] > 1.75 else SIZE[1]
        scale = min(size[0]/SIZE[0], size[1]/height)
        return scale, ((size[0]-SIZE[0]*scale)/2, (size[1]-height*scale)/2), height

    @staticmethod
    def _logical_rects(count, compact=False):
        total = count*CARD_SIZE[0] + (count-1)*GAP
        left = (SIZE[0]-total)//2
        return [pygame.Rect(left+i*(CARD_SIZE[0]+GAP),170 if compact else 250,*CARD_SIZE) for i in range(count)]

    def rects(self, size, count):
        scale, (x,y), height = self._transform(size)
        return [pygame.Rect(round(x+r.x*scale), round(y+r.y*scale),
                            round(r.width*scale), round(r.height*scale))
                for r in self._logical_rects(count, height == 815)]

    def _font(self, size, bold=False):
        key = (size,bold)
        if key not in self._fonts:
            font = pygame.font.Font(None,size)
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    def _text(self, text, center, size, color=(240,233,226), bold=False):
        image = self._font(size,bold).render(text,True,color)
        self._canvas.blit(image,image.get_rect(center=center))

    def _paragraph(self, text, rect, size, bold=False, color=(242,235,229)):
        # Reduz o tamanho apenas quando necessário: descrições longas ficam dentro
        # do painel, sem sobrepor o alvo, o nome ou o limite de acumulação.
        for font_size in range(size,17,-1):
            font = self._font(font_size,bold)
            lines = wrap(font,text,rect.width)
            line_height = font.get_linesize()
            if (len(lines)*line_height <= rect.height
                    and all(font.size(line)[0] <= rect.width for line in lines)):
                break
        y = rect.centery-(len(lines)-1)*line_height/2
        for line in lines:
            self._text(line,(rect.centerx,round(y)),font_size,color,bold)
            y += line_height

    def _diamond(self, center, color, radius=8):
        x,y = center
        pygame.draw.polygon(self._canvas,color,[(x,y-radius),(x+radius,y),(x,y+radius),(x-radius,y)])
        pygame.draw.polygon(self._canvas,(255,239,177),[(x,y-radius),(x+radius,y),(x,y+radius),(x-radius,y)],1)

    def _divider(self, rect, y, color):
        pygame.draw.line(self._canvas,(*color,100),(rect.x+65,y),(rect.centerx-16,y),2)
        pygame.draw.line(self._canvas,(*color,100),(rect.centerx+16,y),(rect.right-65,y),2)
        self._diamond((rect.centerx,y),color,6)

    def _header(self, world, offer, compact):
        center=SIZE[0]//2
        choice = world.progression.next_choice
        round_reward = choice is not None and choice.weapon is not None
        points=[(center-264,42),(center+264,42),(center+264,62),(center+290,90),
                (center+264,118),(center+264,136),(center-264,136),(center-264,118),
                (center-290,90),(center-264,62)]
        if compact:
            points=[(x,round(y*.75-10)) for x,y in points]
        pygame.draw.polygon(self._canvas,(43,22,61),points)
        pygame.draw.polygon(self._canvas,(236,169,38),points,5)
        title = (f"ROUND {choice.round_number}" if round_reward
                 else f"LEVEL {choice.level if choice else world.progression.level}")
        if choice and choice.prismatic_source:
            title = "PRISMATIC REWARD"
        self._text(title,(center,58 if compact else 88),64 if compact else 76,bold=True)
        self._diamond((center-185,58 if compact else 88),(255,202,45),11)
        self._diamond((center+185,58 if compact else 88),(255,202,45),11)
        subtitle = f"{choice.weapon} round reward" if round_reward else "Choose an augment"
        if choice and choice.prismatic_source:
            subtitle = f"{choice.prismatic_source} reward"
        self._text(subtitle,(center,131 if compact else 181),44,bold=True)
        pygame.draw.line(self._canvas,(175,113,38),(center-310,131 if compact else 181),(center-215,131 if compact else 181),3)
        pygame.draw.line(self._canvas,(175,113,38),(center+215,131 if compact else 181),(center+310,131 if compact else 181),3)
        queued=world.progression.pending_choices-1
        if queued > 0:
            noun = "choice" if queued == 1 else "choices"
            self._text(f"{queued} more {noun} after this",(center,155 if compact else 218),27,(184,178,194))

    def _card(self, world, augment, rect, index, selected):
        color=COLORS[augment.rarity]
        if selected:
            # Contornos translúcidos dão destaque sem alterar a textura do pack.
            for spread in range(22,0,-2):
                outer=rect.inflate(spread*2,spread*2)
                pygame.draw.rect(self._canvas,(*color, max(5,50-spread*2)),outer,4,border_radius=20)
        rarity_index={Rarity.GRAY:0,Rarity.GOLD:1,Rarity.PRISMATIC:2}[augment.rarity]
        self._painter.blit(self._canvas,"cards/card_frames.png",rect.center,rect.size,rarity_index)
        if selected:
            pygame.draw.rect(self._canvas,color,rect,3,border_radius=18)
        # Badge separado da raridade, como na referência.
        x,y=rect.x+38,rect.y+24
        badge=[(x,y),(x+54,y),(x+62,y+12),(x+62,y+65),(x+27,y+84),(x-8,y+65),(x-8,y+12)]
        pygame.draw.polygon(self._canvas,(42,30,37),badge)
        pygame.draw.polygon(self._canvas,color,badge,3)
        self._text(str(index+1),(x+27,y+38),52,(255,224,154),True)
        label=self._font(32,True).render(LABELS[augment.rarity],True,color)
        self._canvas.blit(label,label.get_rect(topright=(rect.right-38,rect.y+39)))
        icon_key, icon_index = augment_icon(augment.id)
        self._painter.blit(self._canvas,icon_key,
                           (rect.centerx,rect.y+138),(112,112),icon_index)
        self._paragraph(augment.name,pygame.Rect(rect.x+40,rect.y+205,rect.width-80,68),44,True)
        prefix="Weapon:" if augment.weapon else "Target:"
        target=augment.weapon or "player"
        target_font=self._font(32)
        prefix_image=self._font(32,True).render(prefix,True,color)
        target_image=target_font.render(target,True,(210,202,203))
        width=prefix_image.get_width()+10+target_image.get_width()
        left=rect.centerx-width//2
        self._canvas.blit(prefix_image,(left,rect.y+280))
        self._canvas.blit(target_image,(left+prefix_image.get_width()+10,rect.y+280))
        self._divider(rect,rect.y+318,color)
        effect=pygame.Rect(rect.x+46,rect.y+328,rect.width-92,92)
        pygame.draw.rect(self._canvas,(35,24,43),effect,border_radius=14)
        pygame.draw.rect(self._canvas,(77,49,65),effect,1,border_radius=14)
        self._paragraph(augment.description,effect.inflate(-24,-14),42,True)
        self._divider(rect,rect.y+434,color)
        have=world.inventory.stacks(augment.id)
        choice = world.progression.next_choice
        limit = "unlimited"
        self._paragraph(f"Stacks: {have} -> {have+1} ({limit})",
                        pygame.Rect(rect.x+40,rect.y+452,rect.width-80,38),30,color=(200,190,189))

    def draw(self, surface, world, offer, cursor, locked):
        scale,(x,y),height=self._transform(surface.get_size())
        if self._canvas.get_height() != height:
            self._canvas=pygame.Surface((SIZE[0],height),pygame.SRCALPHA)
        compact=height == 815
        self._canvas.fill((0,0,0,0))
        self._header(world,offer,compact)
        for index,(augment,rect) in enumerate(zip(offer.choices,self._logical_rects(len(offer.choices),compact),strict=True)):
            self._card(world,augment,rect,index,index==cursor)
        self._text("WASD navigate · SPACE choose · 1/2/3 or click · ESC pause",
                   (SIZE[0]//2,785 if compact else 900),32,
                   (155,150,160) if locked else (207,196,190))
        scaled=pygame.transform.smoothscale(self._canvas,(round(SIZE[0]*scale),round(height*scale)))
        surface.blit(scaled,(round(x),round(y)))
