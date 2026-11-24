# Mapeamento de ícones

Revisto visualmente a partir dos sprites locais. A implementação partilhada está em
`src/boxhead/presentation/icons.py`; cartas, HUD e loja usam identificadores explícitos,
sem fallback silencioso para o primeiro ícone. As labels do manifest acompanham o mapa.

Existem apenas 12 símbolos no atlas dos augments: alguns efeitos partilham um símbolo
por afinidade. A raridade é indicada pela carta, não pelo ícone. Não foram criados assets.

| Atlas de augments: índice | Símbolo observado | Augments / melhorias |
| --- | --- | --- |
| 0 | Bala pesada dourada | Dano das armas, AD, Dead Center (dano crítico) |
| 1 | Bota azul | Swift, Sprinter, Slipstream Feed |
| 2 | Três munições | Extra Pellet, Split Chamber |
| 3 | Coração | Vitality, Juggernaut, Siege Frame |
| 4 | XP | Quick Learner |
| 5 | Setas a ricochetear | Ricochet |
| 6 | Explosão laranja | Chain Reaction, Blast Bloom, Ember Rounds, Rupture Rounds |
| 7 | Satélite roxo | Orbital Satellites |
| 8 | Bala inclinada, variante rápida | Cadência das armas, AS, Redline |
| 9 | Duas munições | Aftershot |
| 10 | Mira vermelha | Alcance das armas, Precision (chance crítica) |
| 11 | Cruz médica verde | Regeneration, Last Spark |

## Loja

- Vida, movimento e XP usam os três ícones próprios de `shop/shop_upgrades.png`
  (coração, bota e XP, todos com seta de melhoria).
- As compras de shotgun/SMG usam as imagens das respetivas armas em
  `weapons/weapon_icons.png`: índice 1 shotgun e índice 2 SMG.
- AD, AS, regeneração e os novos itens usam o mesmo símbolo das cartas correspondentes.
- Retirado o fallback que mostrava um coração em quase todos os itens novos.

## Limitações do atlas

Não existe um símbolo específico para chama, crítico forte ou ressurreição.
Ember Rounds usa a explosão laranja por representar dano de fogo; Dead Center usa a bala
pesada e Last Spark a cruz médica. Podemos desenhar ícones próprios futuramente;
até lá, as associações são explícitas e consistentes, mas alguns símbolos repetem-se.
