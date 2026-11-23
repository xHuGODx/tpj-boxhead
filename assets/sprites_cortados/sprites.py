"""
Carregador de sprites para Pygame (corta as spritesheets em memória, usando o manifest.json).

    from sprites import SpriteBank
    bank = SpriteBank("pixel_art_pygame_pack_v2")          # depois de pygame.display.set_mode()
    walk = bank.animation("player/player_walk.png", "down")  # Animation
    frames = bank.frames("effects/explosion_small.png")      # lista de Surfaces
    tile = bank.cell("environment/walls.png", row=0, col=1)  # um único quadro da grelha
"""
import json
from pathlib import Path
import pygame


class Animation:
    def __init__(self, frames, fps=10, loop=True):
        self.frames, self.fps, self.loop = frames, fps, loop
        self.t = 0.0
        self.done = False

    def reset(self):
        self.t, self.done = 0.0, False

    def update(self, dt):
        """dt em segundos."""
        self.t += dt * self.fps
        if not self.loop and self.t >= len(self.frames):
            self.t, self.done = len(self.frames) - 1, True

    @property
    def image(self):
        n = len(self.frames)
        return self.frames[int(self.t) % n if self.loop else min(int(self.t), n - 1)]


class SpriteBank:
    def __init__(self, pack_dir):
        self.root = Path(pack_dir)
        self.manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self._sheets, self._grids = {}, {}

    def grid(self, rel):
        """Devolve grid[row][col] -> Surface (com cache)."""
        if rel not in self._grids:
            meta = self.manifest[rel]
            fw, fh = meta["frame_size"]
            sheet = pygame.image.load(str(self.root / rel)).convert_alpha()
            self._grids[rel] = [
                [sheet.subsurface((c * fw, r * fh, fw, fh)).copy() for c in range(meta["columns"])]
                for r in range(meta["rows"])
            ]
        return self._grids[rel]

    def cell(self, rel, row=0, col=0):
        return self.grid(rel)[row][col]

    def frames(self, rel, direction=None):
        """Lista de frames. Para folhas com direções passar 'down'/'left'/'right'/'up'."""
        meta = self.manifest[rel]
        g = self.grid(rel)
        if meta.get("direction_order"):
            if direction is None:
                raise ValueError(f"{rel} tem direções: {meta['direction_order']}")
            return g[meta["direction_order"].index(direction)]
        return [f for row in g for f in row]

    def animation(self, rel, direction=None, fps=None, loop=None):
        meta = self.manifest[rel]
        return Animation(self.frames(rel, direction),
                         fps if fps is not None else meta.get("fps", 10),
                         loop if loop is not None else meta.get("loop", True))

    def directional(self, rel, **kw):
        """Dict {'down': Animation, 'left': ..., ...}"""
        return {d: self.animation(rel, d, **kw) for d in self.manifest[rel]["direction_order"]}
