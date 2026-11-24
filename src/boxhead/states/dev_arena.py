"""Playable sandbox plus a paused, manually editable augment catalogue."""
import pygame
from pygame import Vector2

from boxhead.presentation.build_panel import BuildPanel, COLORS, GOLD, MUTED, TEXT
from boxhead.presentation.icons import augment_icon
from boxhead.states.playing import PlayingState
from boxhead.world.augments import AUGMENTS, Rarity
from boxhead.world.training import TrainingWorld

VISIBLE = 9
LIST = pygame.Rect(42, 180, 590, VISIBLE * 43)
SEARCH = pygame.Rect(688, 32, 380, 38)
BUTTONS = {
    'remove': pygame.Rect(674, 369, 172, 40),
    'add': pygame.Rect(858, 369, 172, 40),
    'weapon': pygame.Rect(674, 430, 356, 38),
    'targets': pygame.Rect(674, 480, 172, 38),
    'mode': pygame.Rect(858, 480, 172, 38),
    'clear': pygame.Rect(674, 530, 356, 38),
    'play': pygame.Rect(674, 610, 224, 42),
    'menu': pygame.Rect(910, 610, 120, 42),
}


class DevArenaState(PlayingState):
    def __init__(self, machine, on_pause, on_menu, viewport=(1100, 700)):
        world = TrainingWorld(viewport=viewport)
        super().__init__(machine, world.events, on_pause, lambda w: on_menu(),
                         viewport=viewport, world=world)
        self.on_menu = on_menu
        self.editor_open = True
        self.cursor = 0
        self.rarity = None
        self.query = ''
        self.searching = False
        self.message = ''
        self.view = None
        self._size = viewport

    def enter(self):
        super().enter()
        if self.view is None:
            self.view = BuildPanel()
        self._set_search(False)
        self._update_animations(0, Vector2(), False)

    def exit(self):
        self._set_search(False)
        super().exit()

    def filtered(self):
        return sorted((a for a in AUGMENTS
                       if (self.rarity is None or a.rarity is self.rarity)
                       and self.query.casefold() in f'{a.name} {a.weapon or ""} {a.description}'.casefold()),
                      key=lambda a: ({Rarity.PRISMATIC: 0, Rarity.GOLD: 1, Rarity.GRAY: 2}[a.rarity], a.name))

    def _set_search(self, active):
        self.searching = active
        if active:
            pygame.key.start_text_input()
        else:
            pygame.key.stop_text_input()

    def _toggle_editor(self):
        self.editor_open = not self.editor_open
        self._set_search(False)
        self._pressed.clear()
        self._shooting_timer = 0

    def _edit_stack(self, step):
        items = self.filtered()
        if not items:
            return
        a = items[min(self.cursor, len(items)-1)]
        count = max(0, self.world.inventory.stacks(a.id) + step)
        try:
            self.world.set_stack(a.id, count)
        except ValueError as error:
            self.message = str(error)
        else:
            self.message = f'{a.name}: x{count}'

    def _action(self, action):
        w = self.world
        self._set_search(False)
        if action in ('add', 'remove'):
            self._edit_stack(1 if action == 'add' else -1)
        elif action == 'weapon':
            w.select_weapon(w.player.weapon_slot + 1)
        elif action == 'targets':
            w.target_count = 3 if w.target_count == 1 else 1
            w.reset_test()
        elif action == 'mode':
            w.killable = not w.killable
            w.reset_test()
        elif action == 'clear':
            w.clear_build()
            self.message = 'Build cleared.'
        elif action == 'play':
            self._toggle_editor()
        elif action == 'menu':
            self.on_menu()

    def handle_event(self, event):
        if event.type == pygame.WINDOWFOCUSLOST:
            self._pressed.clear()
            if not self.editor_open:
                self._toggle_editor()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            if not getattr(event, 'repeat', False):
                self._toggle_editor()
            return
        if not self.editor_open:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_q, pygame.K_e):
                    if event.key in (pygame.K_q, pygame.K_e):
                        slot = self.world.player.weapon_slot + (-1 if event.key == pygame.K_q else 1)
                    else:
                        slot = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[event.key]
                    self.world.select_weapon(slot)
                    return
                if event.key == pygame.K_r:
                    self.world.reset_test()
                    return
                if event.key in (pygame.K_t, pygame.K_g):
                    self._action('mode' if event.key == pygame.K_t else 'targets')
                    return
            super().handle_event(event)
            return
        if event.type == pygame.TEXTINPUT and self.searching:
            self.query = (self.query + event.text)[:60]
            self.cursor = 0
        elif event.type == pygame.MOUSEWHEEL:
            self.cursor = max(0, min(max(0, len(self.filtered())-1), self.cursor-event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = (event.pos[0]*1100/self._size[0], event.pos[1]*700/self._size[1])
            self._set_search(SEARCH.collidepoint(pos))
            for i in range(4):
                if pygame.Rect(42+i*148, 119, 138, 34).collidepoint(pos):
                    self.rarity = (None, Rarity.GRAY, Rarity.GOLD, Rarity.PRISMATIC)[i]
                    self.cursor = 0
            if LIST.collidepoint(pos):
                first = max(0, self.cursor-VISIBLE+1)
                self.cursor = min(max(0, len(self.filtered())-1), first+int((pos[1]-LIST.y)//43))
            for action, rect in BUTTONS.items():
                if rect.collidepoint(pos):
                    self._action(action)
                    break
        elif event.type == pygame.KEYDOWN:
            if self.searching:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self._set_search(False)
                elif event.key == pygame.K_BACKSPACE:
                    self.query = self.query[:-1]
                    self.cursor = 0
                return
            if event.key == pygame.K_ESCAPE:
                self._toggle_editor()
            elif event.key in (pygame.K_f, pygame.K_SLASH):
                self._set_search(True)
            elif event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                step = -1 if event.key in (pygame.K_w, pygame.K_UP) else 1
                self.cursor = max(0, min(max(0, len(self.filtered())-1), self.cursor+step))
            elif event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_MINUS):
                self._edit_stack(-1)
            elif event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_RETURN, pygame.K_EQUALS):
                self._edit_stack(1)
            elif event.key in (pygame.K_q, pygame.K_e):
                self.world.select_weapon(self.world.player.weapon_slot + (-1 if event.key == pygame.K_q else 1))

    def update(self, dt):
        if self.editor_open:
            self._update_animations(0, Vector2(), False)
        else:
            super().update(dt)

    def _draw_enemy(self, surface, enemy):
        super()._draw_enemy(surface, enemy)
        if enemy.alive:
            point = self._camera.world_to_screen(enemy.position)
            pygame.draw.circle(surface, (246, 203, 104), point, round(enemy.radius+8), 1)
            title = self._elite_font.render('TRAINING DUMMY', True, GOLD)
            surface.blit(title, title.get_rect(midbottom=(point.x, point.y-52)))

    def draw(self, surface):
        self._size = surface.get_size()
        super().draw(surface)
        if self.editor_open:
            self._draw_editor(surface)
            return
        v = self.view
        v.canvas.fill((0, 0, 0, 0))
        pygame.draw.rect(v.canvas, (15, 22, 34, 240), (280, 15, 450, 77), border_radius=10)
        w = self.world
        v.text(f'DPS {w.dps:,.1f}    TOTAL {w.total_damage:,.0f}', (298, 26), 28, GOLD)
        v.text(f'Last {w.last_damage:,.1f}   Peak {w.highest_damage:,.1f}   Kills {w.target_kills}', (298, 61), 20)
        pygame.draw.rect(v.canvas, (15, 22, 34, 240), (180, 575, 740, 32), border_radius=7)
        v.text('TAB augments   1/2/3 weapons   R reset   T mortal/immortal   G targets', (198, 584), 20)
        v.text('DEV ARENA / INFINITE AMMO', (298, 100), 18, GOLD)
        surface.blit(pygame.transform.smoothscale(v.canvas, surface.get_size()), (0, 0))

    def _draw_editor(self, surface):
        v = self.view
        c = v.canvas
        c.fill((10, 15, 25, 250))
        v.text('DEV ARENA', (32, 25), 48)
        v.text('BUILD LAB / MANUAL AUGMENTS', (34, 72), 18, GOLD)
        pygame.draw.rect(c, (25, 35, 51), SEARCH, border_radius=8)
        pygame.draw.rect(c, GOLD if self.searching else (51, 66, 89), SEARCH, 1, border_radius=8)
        old = c.get_clip()
        c.set_clip(SEARCH.inflate(-16, -4))
        v.text(self.query + ('|' if self.searching else '') if self.query or self.searching else 'F / click to search',
               (700, 43), 22, TEXT if self.query else MUTED)
        c.set_clip(old)
        for i, (label, rarity) in enumerate(zip(('ALL', 'GRAY', 'GOLD', 'PRISMATIC'),
                                               (None, Rarity.GRAY, Rarity.GOLD, Rarity.PRISMATIC))):
            rect = pygame.Rect(42+i*148, 119, 138, 34)
            pygame.draw.rect(c, GOLD if rarity is self.rarity else (25, 35, 51), rect, border_radius=6)
            v.text(label, (rect.x+14, rect.y+9), 20, (15, 22, 34) if rarity is self.rarity else MUTED)
        items = self.filtered()
        self.cursor = max(0, min(self.cursor, max(0, len(items)-1)))
        first = max(0, self.cursor-VISIBLE+1)
        for row, augment in enumerate(items[first:first+VISIBLE]):
            rect = pygame.Rect(LIST.x, LIST.y+row*43, LIST.width, 39)
            selected = first+row == self.cursor
            color = COLORS[augment.rarity]
            pygame.draw.rect(c, (40, 46, 67) if selected else (20, 28, 42), rect, border_radius=6)
            if selected:
                pygame.draw.rect(c, color, rect, 1, border_radius=6)
            key, index = augment_icon(augment.id)
            v.painter.blit(c, key, (rect.x+22, rect.centery), (28, 28), index)
            v.text(augment.name, (rect.x+46, rect.y+10), 22, color)
            v.text(augment.weapon or 'PLAYER', (rect.right-62, rect.y+12), 18, MUTED, True)
            v.text(f'x{self.world.inventory.stacks(augment.id)}', (rect.right-12, rect.y+10), 22, TEXT, True)
        if not items:
            v.text('No augments match your search.', (60, 200), 22, MUTED)
        v.text(f'{len(items)} augments  /  scroll or W/S to browse', (44, 584), 20, MUTED)
        v.text('A/D or +/- remove/add  /  SPACE adds  /  Q/E weapon', (44, 616), 20)
        v.text('Base stats / no shop bonuses. Progress is not saved.', (44, 650), 20, GOLD)
        v.panel(pygame.Rect(656, 112, 392, 475), 'CONFIGURE', 'Simulation paused while editing')
        if items:
            a = items[self.cursor]
            v.text(a.name, (674, 198), 28, COLORS[a.rarity])
            v.wrapped(a.description, pygame.Rect(674, 238, 350, 72), TEXT)
            n = self.world.inventory.stacks(a.id)
            v.text(f'{a.rarity.value.upper()}  /  {a.weapon or "ALL WEAPONS"}  /  x{n}', (674, 325), 20, COLORS[a.rarity])
        labels = {'add': '+ ADD STACK', 'remove': '- REMOVE STACK',
                  'weapon': f'Weapon: {self.world.player.weapon.name}  /  Q/E',
                  'targets': f'Targets: {self.world.target_count}',
                  'mode': 'Mortal: 1000 HP' if self.world.killable else 'Immortal target',
                  'clear': 'CLEAR BUILD', 'play': 'TEST BUILD  /  TAB', 'menu': 'MENU'}
        for action, rect in BUTTONS.items():
            pygame.draw.rect(c, GOLD if action == 'play' else (34, 46, 65), rect, border_radius=7)
            image = v.fonts[20].render(labels[action], True, (15, 22, 34) if action == 'play' else TEXT)
            c.blit(image, image.get_rect(center=rect.center))
        v.wrapped(self.message, pygame.Rect(674, 578, 356, 28), GOLD)
        surface.blit(pygame.transform.smoothscale(c, surface.get_size()), (0, 0))
