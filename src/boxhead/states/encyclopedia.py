"""Browsable, searchable field archive. Viewing never changes the profile."""
import pygame

from boxhead.core.state import State
from boxhead.presentation.build_panel import BuildPanel, TEXT, MUTED, GOLD
from boxhead.presentation.encyclopedia import CATEGORIES, entries

VISIBLE = 8


class EncyclopediaState(State):
    def __init__(self, profile, on_back):
        self.profile, self.on_back = profile, on_back
        self.category = 0
        self.cursor = 0
        self.query = ''
        self.editing = False
        self._size = (1100,700)

    def enter(self):
        self.archive = entries(self.profile)
        self.view = BuildPanel()
        self.view.painter.prepare(sorted({e.icon[0] for e in self.archive}))
        pygame.key.stop_text_input()

    def exit(self):
        pygame.key.stop_text_input()

    def filtered(self):
        needle = self.query.casefold().strip()
        return [e for e in self.archive if e.category == CATEGORIES[self.category]
                and (not needle or needle in f'{e.name} {e.tag} {e.description}'.casefold())]

    def move(self, amount):
        self.cursor = max(0,min(max(0,len(self.filtered())-1),self.cursor+amount))

    def set_category(self, index):
        self.category=index%len(CATEGORIES);self.cursor=0

    def _search(self, active):
        self.editing=active
        if active: pygame.key.start_text_input()
        else: pygame.key.stop_text_input()

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT and self.editing:
            self.query=(self.query+event.text)[:64];self.cursor=0
        elif event.type == pygame.KEYDOWN:
            key=event.key
            if self.editing:
                if key in (pygame.K_ESCAPE,pygame.K_RETURN,pygame.K_KP_ENTER):self._search(False)
                elif key==pygame.K_BACKSPACE:self.query=self.query[:-1];self.cursor=0
                return
            if key==pygame.K_ESCAPE:self.on_back()
            elif key==pygame.K_f:self._search(True)
            elif key==pygame.K_BACKSPACE:self.query='';self.cursor=0
            elif key in (pygame.K_a,pygame.K_LEFT):self.set_category(self.category-1)
            elif key in (pygame.K_d,pygame.K_RIGHT,pygame.K_TAB):self.set_category(self.category+1)
            elif key in (pygame.K_w,pygame.K_UP):self.move(-1)
            elif key in (pygame.K_s,pygame.K_DOWN):self.move(1)
        elif event.type==pygame.MOUSEWHEEL:
            self.move(-event.y)
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            scale=min(self._size[0]/1100,self._size[1]/700)
            x=(event.pos[0]-(self._size[0]-1100*scale)/2)/scale
            y=(event.pos[1]-(self._size[1]-700*scale)/2)/scale
            for i in range(len(CATEGORIES)):
                if pygame.Rect(32+i*164,96,154,34).collidepoint(x,y):self.set_category(i);self._search(False)
            if pygame.Rect(688,30,380,40).collidepoint(x,y):self._search(True)
            if pygame.Rect(48,226,308,VISIBLE*43).collidepoint(x,y):
                candidates=self.filtered()
                first=min(max(0,self.cursor-VISIBLE+1),max(0,len(candidates)-VISIBLE))
                self.cursor=min(max(0,len(candidates)-1),first+int((y-226)//43))

    def update(self, dt):
        pass

    def draw(self, surface):
        self._size=surface.get_size()
        v=self.view;c=v.canvas;c.fill((10,15,25))
        v.text('FIELD ARCHIVE',(32,25),48)
        v.text('ENCYCLOPEDIA / KNOW YOUR BUILD',(34,72),18,GOLD)
        search=pygame.Rect(688,30,380,40)
        pygame.draw.rect(c,(25,35,51),search,border_radius=8)
        pygame.draw.rect(c,GOLD if self.editing else (51,66,89),search,1,border_radius=8)
        shown=self.query+('|' if self.editing else '') if self.query or self.editing else 'F / click to search this category'
        # Render a clipped text window so a long query cannot overlap other panels.
        old=c.get_clip();c.set_clip(search.inflate(-20,-2))
        v.text(shown,(700,42),22,TEXT if self.query else MUTED);c.set_clip(old)
        for i,label in enumerate(CATEGORIES):
            rect=pygame.Rect(32+i*164,96,154,34)
            pygame.draw.rect(c,GOLD if i==self.category else (25,35,51),rect,border_radius=6)
            v.text(label,(rect.x+14,rect.y+9),22,(15,22,34) if i==self.category else MUTED)
        v.panel(pygame.Rect(32,148,340,464),'INDEX','W/S or mouse wheel to browse')
        # panel subtitle occupies the header; list starts below it.
        items=self.filtered();self.cursor=min(self.cursor,max(0,len(items)-1))
        first=min(max(0,self.cursor-VISIBLE+1),max(0,len(items)-VISIBLE))
        for row,e in enumerate(items[first:first+VISIBLE]):
            rect=pygame.Rect(48,226+row*43,308,39)
            pygame.draw.rect(c,(38,41,60) if first+row==self.cursor else (25,33,47),rect,border_radius=5)
            if first+row==self.cursor:pygame.draw.rect(c,e.color,rect,1,border_radius=5)
            v.painter.blit(c,e.icon[0],(68,rect.centery),(28,28),e.icon[1])
            # Long names shrink to fit the list column.
            name=e.name
            font=v.fonts[22] if v.fonts[22].size(name)[0]<248 else v.fonts[18]
            image=font.render(name,True,e.color);c.blit(image,(90,rect.y+10))
        v.panel(pygame.Rect(390,148,678,464),'REFERENCE',f'{len(items)} entries / actual game catalog')
        if items:
            e=items[self.cursor]
            v.text(e.name,(414,236),34,e.color)
            v.text(e.tag,(414,273),18,MUTED)
            v.painter.blit(c,e.icon[0],(1010,250),(72,72),e.icon[1])
            v.wrapped(e.description,pygame.Rect(414,306,620,116),TEXT)
            for i,(label,value) in enumerate(e.rows):
                top=432+i*18
                v.text(label,(414,top),18,MUTED)
                v.text(value,(1040,top),18,TEXT,True)
            v.text(f'{self.cursor+1} / {len(items)}',(354,584),18,MUTED,True)
        else:
            v.text('No matching entries',(414,256),34)
            v.wrapped('Try a different category or clear the search with Backspace.',pygame.Rect(414,312,580,100))
        v.text('A/D categories   /   W/S browse   /   F search   /   BACKSPACE clear   /   ESC menu',
               (32,648),22,MUTED)
        scale=min(surface.get_width()/1100,surface.get_height()/700)
        image=pygame.transform.smoothscale(c,(round(1100*scale),round(700*scale)))
        surface.fill((10,15,25));surface.blit(image,image.get_rect(center=surface.get_rect().center))
