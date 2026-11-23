# Assets

Os sprites estão integrados através de `assets/manifest.json`. O catálogo partilha
os frames; cada entidade mantém o seu estado de animação. Fontes usam o recurso
predefinido incluído no Pygame e são criadas ao entrar no ecrã.

## Origem e fontes editáveis

Os oito PNGs iniciais foram fornecidos na branch do colega. Os restantes recursos
foram fornecidos pelo utilizador em `sprites_cortados.zip`, preservado extraído em
`assets/sprites_cortados/`. Autoria original não identificada individualmente.
As informações de produção e limitações fornecidas com o pack estão em
[sprites_cortados/pixel_art_pygame_pack_v2/README.md](sprites_cortados/pixel_art_pygame_pack_v2/README.md).
Essas informações são as declarações do pack fornecido, sem verificação independente.

Os PNGs completos são as fontes raster editáveis disponíveis; os recortes separados
estão em `sprites_cortados/frames/`, acompanhados do índice. Não foram fornecidos
ficheiros de camadas. Os scripts de slicing/demo são material auxiliar, não fazem
parte do arranque do jogo.

## Convenções de integração

- Procurar primeiro o caminho direto em `assets/`; depois o mesmo caminho dentro
  de `sprites_cortados/pixel_art_pygame_pack_v2/`. Um PNG ausente usa placeholder.
- As quatro linhas direcionais são down, left, right, up. O movimento admite oito
  direções; diagonais usam a representação cardinal mais próxima.
- Cada frame é centrado na posição da entidade; dimensões, FPS, ordem e loop estão
  no manifest. Escala/rotação não alteram raios ou hitboxes.
- O catálogo e os adaptadores preparam recursos antes do desenho. Frames e versões
  escaladas são partilhados/cacheados; não se lêem ficheiros por entidade/frame.
- Todos os recursos são incluídos no wheel em `boxhead/data`, permitindo executar
  de outra diretoria e instalar o pacote fora do checkout.
- O pack contém animações derivadas programaticamente e possíveis halos/costuras,
  descritos no README original. Sons ainda não estão implementados.

## Inventário dos exports

Origem comum: recursos fornecidos pela equipa/utilizador. As folhas completas são
fontes e exports PNG; recortes individuais preservados no bundle. O ponto de origem
usado é o centro do frame. Todas as entradas abaixo constam do manifest.

| Recurso | Frame (px) | Grelha (linhas × colunas) | FPS |
| --- | --- | --- | --- |
| `player/player_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `player/player_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `player/player_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `player/player_death.png` | 96 × 96 | 1 × 6 | 9 |
| `player/player_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `player/player_shoot.png` | 96 × 96 | 4 × 3 | 12 |
| `enemies/enemy_basic_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `enemies/enemy_basic_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `enemies/enemy_basic_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `enemies/enemy_basic_death.png` | 96 × 96 | 1 × 4 | 9 |
| `enemies/enemy_basic_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `enemies/enemy_basic_attack.png` | 96 × 96 | 4 × 3 | 10 |
| `enemies/enemy_red_walk.png` | 96 × 96 | 4 × 4 | 9 |
| `enemies/enemy_red_idle.png` | 96 × 96 | 4 × 1 | 3 |
| `enemies/enemy_red_hurt.png` | 96 × 96 | 4 × 2 | 8 |
| `enemies/enemy_red_death.png` | 96 × 96 | 1 × 4 | 9 |
| `enemies/enemy_red_shadow.png` | 96 × 96 | 1 × 1 | 8 |
| `enemies/enemy_red_prepare.png` | 96 × 96 | 4 × 3 | 8 |
| `enemies/enemy_red_shoot.png` | 96 × 96 | 4 × 3 | 12 |
| `bosses/boss_01_walk.png` | 192 × 192 | 4 × 4 | 9 |
| `bosses/boss_01_idle.png` | 192 × 192 | 4 × 1 | 3 |
| `bosses/boss_01_hurt.png` | 192 × 192 | 4 × 2 | 8 |
| `bosses/boss_01_death.png` | 192 × 192 | 1 × 8 | 9 |
| `bosses/boss_01_shadow.png` | 192 × 192 | 1 × 1 | 8 |
| `bosses/boss_01_prepare.png` | 192 × 192 | 4 × 3 | 7 |
| `bosses/boss_01_attack.png` | 192 × 192 | 4 × 4 | 10 |
| `weapons/pistol.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/shotgun.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/smg.png` | 112 × 64 | 1 × 1 | 8 |
| `weapons/weapon_icons.png` | 64 × 64 | 1 × 3 | 8 |
| `projectiles/player_bullet.png` | 32 × 32 | 1 × 1 | 8 |
| `projectiles/player_pellet.png` | 32 × 32 | 1 × 1 | 8 |
| `projectiles/enemy_fireball.png` | 64 × 64 | 1 × 4 | 10 |
| `projectiles/boss_projectile.png` | 64 × 64 | 1 × 4 | 10 |
| `projectiles/orbital_satellite.png` | 80 × 80 | 1 × 4 | 10 |
| `effects/muzzle_flash.png` | 48 × 48 | 1 × 3 | 12 |
| `effects/impact_enemy.png` | 48 × 48 | 1 × 4 | 12 |
| `effects/impact_wall.png` | 48 × 48 | 1 × 4 | 12 |
| `effects/explosion_small.png` | 80 × 80 | 1 × 4 | 12 |
| `effects/explosion_large.png` | 128 × 128 | 1 × 6 | 12 |
| `effects/chain_explosion.png` | 128 × 128 | 1 × 6 | 12 |
| `effects/charge_effect.png` | 80 × 80 | 1 × 4 | 12 |
| `effects/spawn_effect.png` | 128 × 128 | 1 × 4 | 12 |
| `environment/floor_tiles.png` | 64 × 64 | 1 × 4 | 8 |
| `environment/walls.png` | 64 × 64 | 4 × 4 | 8 |
| `environment/obstacles.png` | 80 × 80 | 1 × 6 | 8 |
| `environment/decorations.png` | 64 × 64 | 1 × 5 | 8 |
| `ui/ui_icons_main.png` | 64 × 64 | 1 × 3 | 8 |
| `ui/healthbar.png` | 384 × 96 | 1 × 1 | 8 |
| `ui/xpbar.png` | 384 × 80 | 1 × 1 | 8 |
| `augments/augment_icons.png` | 80 × 80 | 2 × 6 | 8 |
| `shop/shop_upgrades.png` | 96 × 96 | 1 × 3 | 8 |
| `cards/card_frames.png` | 192 × 256 | 1 × 3 | 8 |
| `maps/map_01_thumb.png` | 256 × 256 | 1 × 1 | 8 |
| `maps/map_02_thumb.png` | 256 × 256 | 1 × 1 | 8 |
| `maps/map_03_thumb.png` | 256 × 256 | 1 × 1 | 8 |


## Revisão de recortes

Todas as 56 folhas (326 frames) correspondem às dimensões declaradas. O problema
não era o tamanho da grelha: alguns elementos estavam desalinhados dentro do atlas.
O manifest suporta agora `source_rects`, `anchor`, `frame_cleanup` e `tile_border`.
Os recortes explícitos são colocados em frames do mesmo tamanho lógico, sem alterar
os PNGs de origem. As âncoras centram o conteúdo ou alinham-no pelo chão.

- Obstáculos: removidos fragmentos entre caixas/rochas/colunas. Ordem real registada
  como caixa, caixa, barril, rocha, rocha grande, coluna. Corrigidos os índices dos
  mapas e a identificação do barril circular nas arenas e nos chunks.
- Decorações: preservados os grupos completos de pedras, relva, sangue, grelha e
  ossos; excluída a linha residual da margem direita. A grelha antes atravessava
  duas células e aparecia partida.
- Augments: regiões dos símbolos explicitadas e centradas em molduras uniformes.
  `labels` associa IDs aos símbolos de dano, alcance, XP, vida, etc., independentemente
  da ordem do catálogo. A apresentação deixou de tentar adivinhar os recortes.
- Limpeza limitada a ilhas desconectadas confirmadas no boss/SMG/projéteis e a
  fragmentos brancos nas explosões/spawns. Partículas legítimas dos outros efeitos
  mantêm-se; os critérios são definidos por folha/frame, sem filtro global de cores.
- Sombra: o adaptador usa o conteúdo alfa da imagem e coloca-o junto dos pés, sem
  duplicar a margem transparente com o deslocamento no renderer.

Limitações encontradas nos originais: há halos amarelos/magentas junto de alguns
personagens e zonas residuais de fundo junto do boss, da SMG e da coluna. Elementos
já fundidos com o desenho não são corrigíveis apenas mudando retângulos de corte;
precisam de retoque da arte ou de fontes com transparência mais limpa. A limpeza
por componentes preserva o desenho principal e não reconstrói partes da ilustração.
