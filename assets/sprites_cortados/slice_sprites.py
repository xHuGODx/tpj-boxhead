"""
Corta todas as spritesheets do pack em PNGs individuais.

Uso:
    python slice_sprites.py [pasta_do_pack] [pasta_saida]
Por defeito:  pixel_art_pygame_pack_v2  ->  frames

Nomes gerados (a partir do manifest.json):
  com direções : player/player_walk_down_00.png, player_walk_left_01.png ...
  sem direções, 1 linha  : effects/explosion_small_00.png ...
  sem direções, grelha   : environment/walls_r0_c1.png ...
Também escreve frames/frames_index.json com a lista de ficheiros de cada folha.
"""
import json, sys
from pathlib import Path
from PIL import Image

pack = Path(sys.argv[1] if len(sys.argv) > 1 else "pixel_art_pygame_pack_v2")
out = Path(sys.argv[2] if len(sys.argv) > 2 else "frames")
manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))

index, total, empty = {}, 0, 0
for rel, meta in manifest.items():
    sheet = Image.open(pack / rel).convert("RGBA")
    fw, fh = meta["frame_size"]
    cols, rows = meta["columns"], meta["rows"]
    dirs = meta.get("direction_order")
    stem = Path(rel).stem
    dest = out / Path(rel).parent
    dest.mkdir(parents=True, exist_ok=True)
    files = []
    for r in range(rows):
        for c in range(cols):
            frame = sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
            if frame.getbbox() is None:
                empty += 1          # frame totalmente transparente (ex.: tiles com fundo nunca ficam vazios)
            if dirs:
                name = f"{stem}_{dirs[r]}_{c:02d}.png"
            elif rows == 1:
                name = f"{stem}_{c:02d}.png"
            else:
                name = f"{stem}_r{r}_c{c}.png"
            frame.save(dest / name)
            files.append(str((Path(rel).parent / name).as_posix()))
            total += 1
    index[rel] = {"frame_size": [fw, fh], "files": files,
                  **{k: meta[k] for k in ("fps", "loop") if k in meta}}

(out / "frames_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
print(f"{total} frames guardados em '{out}' ({len(index)} folhas, {empty} frames vazios)")
