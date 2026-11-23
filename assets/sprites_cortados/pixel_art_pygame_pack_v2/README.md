# Pixel Art Pack v2 — alta resolução — Pygame

Sprite pack baseado diretamente na imagem de referência fornecida pelo utilizador. Estilo: pixel art top-down, humano azul/castanho, zombie verde, inimigo vermelho, boss golem roxo/cinza com cristal vermelho; armas, efeitos e elementos do ambiente extraídos e retocados a partir da imagem de referência, com as cores e formas preservadas.

## Dimensões e convenções

- Personagens: 96 x 96 px por frame; boss: 192 x 192 px por frame.
- Personagens: as **linhas** representam `down`, `left`, `right`, `up`; **colunas** representam frames. Caminhar tem 4 frames/direção. O ficheiro de morte tem 1 linha.
- Armas independentes: 112 x 64 px; ícones HUD: 64 x 64 px; balas 32 x 32; efeitos 48–128 px.
- Tiles de chão: 64 x 64; paredes: 64 x 64; obstáculos: 80 x 80; augments: 80 x 80; cartas: 192 x 256.
- Todas as imagens são PNG RGBA, com frames de tamanho uniforme e metadados em `manifest.json`.
- Armas, personagens, projéteis, obstáculos e efeitos são transparentes; os **tiles, molduras de cartas, ícones com fundos e miniaturas** mantêm intencionalmente os seus fundos.

## Limitações honestas

- Os quatro `walk` dos três personagens e do boss foram redesenhados com mais detalhe; os `hurt`, `shoot`, `attack`, `prepare` e `death` são **adaptações programáticas desses frames** (flashes, deslocações e dissolvências) e não animações originais desenhadas manualmente frame a frame.
- Apesar da melhoria, isto não é uma extração perfeita da referência: os seus elementos já estavam fundidos sobre um fundo escuro e alguns recortes podem apresentar um halo subtil.
- O chão vem de miniaturas da referência e poderá precisar de ajustes para garantir repetição sem costuras.
- Os `muzzle_offsets.json` são apenas valores iniciais, confirmar visualmente no jogo.

## Exemplo básico de slicing

```python
import pygame
pygame.init()
sheet = pygame.image.load('assets/player/player_walk.png').convert_alpha()
FRAME_W = FRAME_H = 96
# linha 2 = right, frame 1 = segundo quadro
frame = sheet.subsurface((1*FRAME_W, 2*FRAME_H, FRAME_W, FRAME_H)).copy()
```

**Fonte**: conceito de pixel art fornecido pelo utilizador nesta conversa; sprites de movimento redesenhados para o presente pack; restantes assets isolados da referência. **Licença**: conteúdo produzido/transformado neste pedido para utilização no projeto do utilizador; não foram usados packs externos de terceiros neste ZIP.
