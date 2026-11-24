# Revisão de cortes e centragem

Correções feitas no manifest e no recortador; os PNGs originais não foram alterados.

- Explosões grandes: três estágios completos recuperados; removidos fragmentos laterais
  e o fumo final cuja própria arte já estava truncada. Duração dos efeitos de gameplay mantida.
- Explosões pequenas: quatro formas completas, sem metades de outros sprites.
- Muzzle flash e impactos: retângulos por forma, em vez de grelha que atravessava os desenhos.
- Charge effect: removidos os restos de texto no topo e ilhas desligadas do efeito.
- Cartas: retângulos explícitos para as três molduras; removida a linha residual à direita.
- Personagens e boss: recorte da transparência e alinhamento pelo centro horizontal/pés,
  com margem comum por família. Animações de morte mantêm o posicionamento original
  para preservar o desaparecimento em vez de recentrar cada fragmento.
- Armas: transparência aparada e conteúdo centrado, sem esticar cada frame.
- Barras de referência: healthbar deixa de incluir a barra de XP que vinha no mesmo PNG;
  xpbar deixa de carregar o bloco vazio por baixo.
- Piso e paredes: preservados; os buracos nas variantes danificadas das paredes já fazem
  parte da imagem e não são causados pelo recorte. Reconstruí-los exigiria redesenhar a arte.

`uniform_scale` conserva as proporções relativas entre estágios de um efeito;
`trim`, `padding` e `anchor` controlam a transparência e o ponto de alinhamento.
Os cortes existentes sem estas opções continuam com o comportamento anterior.

Para voltar a gerar as folhas de inspeção visual:

```powershell
.\.venv\Scripts\python.exe scripts\audit-sprites.py
```

Os resultados ficam em `build/sprite-audit/`, fora do controlo de versões.
O ZIP Windows existente não foi reconstruído nesta revisão.
