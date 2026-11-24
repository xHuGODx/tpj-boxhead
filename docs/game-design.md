# Design do jogo

## Decisões confirmadas

- Jogo em Python/Pygame, para um jogador.
- Movimento com WASD; Espaço dispara na orientação da personagem.
- Mapas limitados e um modo de mapa infinito.
- Rondas infinitas com dificuldade crescente e bosses periódicos, inicialmente a cada 10 rondas.
- Três armas: pistola grátis; SMG e shotgun compradas permanentemente na loja,
  selecionáveis desde a ronda 1. Q/E na escolha de mapa seleciona a única arma da partida.
- Munições finitas por arma e 35% de probabilidade de cada inimigo largar uma caixa de munições.
- Cada ronda concluída concede uma escolha adicional de augment para a arma do golpe final.
- Dois inimigos iniciais: normal e vermelho inspirado no original.
- XP e níveis durante a partida; cada level-up pausa o jogo e apresenta três augments.
- Cinzento: atributos de uma arma. Dourado: atributos mais fortes da personagem.
- Prismático: uma mecânica nova com impacto visível na forma de jogar.
- Augments só duram a partida. Uma loja no menu compra melhorias permanentes,
  ao estilo Vampire Survivors, com progresso guardado localmente.
- A direção visual usa sprites próprios (custom sprites), criados para o projeto:
  jogador, inimigos, boss, armas/projéteis e elementos dos mapas.
- A criação dos sprites e a integração num catálogo partilhado fazem parte do
  backlog. Placeholders permitem desenvolver o gameplay enquanto a arte é criada.

## Propostas de implementação

As regras seguintes permitem avançar, mas são ajustáveis durante implementação e playtest.

| Tema | Proposta inicial |
| --- | --- |
| Orientação | Oito direções; diagonais normalizadas; ao parar mantém a última orientação; começa virado para baixo. |
| Disparo | Segurar Espaço repete disparos respeitando cooldown e munições; cada disparo consome uma bala/cartucho, independentemente dos pellets. |
| Escolha de arma | Q/E antes da partida escolhe uma arma; não é possível trocar em combate. Teclas 1/2/3 escolhem cartas nos menus de augments. |
| Disponibilidade de armas | Pistola grátis, SMG por 250 moedas e shotgun por 400. As compras desbloqueiam opções de arma para levar desde a ronda 1. |
| Munições | Reserva inicial/máxima/por caixa: pistola 60/180/18, SMG 120/360/60, shotgun 24/72/8. Sem carregadores/recarga. |
| Drops | Cada morte tem 35% de chance de largar uma caixa na posição do inimigo; recolha por contacto abastece todas as armas desbloqueadas. |
| Rondas | Orçamento finito de inimigos por ronda; termina quando não há spawns pendentes nem inimigos vivos. |
| Entre rondas | Escolha adicional de três augments cinzentos da arma do golpe final, seguida de intervalo curto; menus e escolhas pausam a simulação. |
| Dificuldade | Quantidade, composição e atributos crescem por curvas configuráveis; limites de ativos controlam carga sem terminar as rondas. |
| Vermelho | Mais resistente, com ataque à distância e preparação visível; confirmar o comportamento pretendido ao implementar. |
| Boss | Um boss inicial com fases de perseguição, preparação, ataque e recuperação, nas rondas 10, 20, 30… |
| XP | Recompensa automática por morte de inimigo; pickups físicos podem ser acrescentados depois. |
| Moeda permanente | Ganha em mortes/rondas, separada do XP; creditada uma vez no fim da partida. |
| Loja | Vida, movimento, XP, regeneração, AD e attack speed com limites; compras únicas de SMG/shotgun. |
| Mapas | Começar por uma arena limitada aberta; depois variantes com obstáculos e mapa infinito por chunks. |
| Fim de partida | Morte mostra ronda, nível, tempo, mortes e moeda; permite repetir ou regressar ao menu. |

## Raridade e escolha de augments

Proposta: sortear **uma raridade por oferta** e apresentar três escolhas dessa
raridade. Evita que a escolha óbvia seja sempre a carta de maior raridade.
Probabilidades iniciais: 60% cinzento, 30% dourado, 10% prismático; ficam em dados
e serão afinadas com playtests. Os valores e a política de sorteio não são requisitos fechados.

- As três escolhas são distintas e elegíveis para o estado atual da partida.
- Augments de arma identificam a arma afetada e só aparecem para armas disponíveis.
- Limites de acumulação, pré-requisitos e incompatibilidades pertencem às definições.
- Se uma raridade ficar sem três opções, usar um fallback documentado;
  nunca apresentar uma escolha impossível nem bloquear a partida.
- XP excedente pode gerar vários level-ups: enfileirar uma escolha por nível.
- Nenhum movimento, tiro, spawn, cooldown ou temporizador de combate avança durante a seleção.
- As escolhas seguintes respeitam os augments acabados de adquirir.

Exemplos propostos de cinzentos: dano da pistola, pellets da shotgun e cadência da
metralhadora. Dourados: vida máxima, velocidade de movimento e regeneração.
Magnitudes devem respeitar as unidades de cada atributo; a cor não torna percentagens
de atributos diferentes diretamente comparáveis.

Primeiros prismáticos propostos:

1. **Ricochete:** projéteis saltam para novos alvos, com alcance e saltos limitados.
2. **Reação em cadeia:** mortes causam explosões; cadeias têm limites para evitar recursão infinita.
3. **Satélites orbitais:** objetos orbitam o jogador e causam dano com cooldown por alvo.

O motor de efeitos deve permitir acrescentar novos comportamentos sem transformar
o jogador ou a arma num conjunto crescente de `if augment_id == ...`.

## Partida e perfil

| Partida: reinicia sempre | Perfil: persiste |
| --- | --- |
| XP, nível e augments | Saldo de moeda |
| Ronda e entidades | Níveis comprados na loja |
| Vida, cooldowns, munições e desbloqueios | Versão do formato de save |
| Efeitos temporários | Preferências, quando existirem |

Criar uma partida aplica as melhorias do perfil a uma nova base. Nunca voltar a
aplicar multiplicadores sobre atributos já modificados de uma partida anterior.
Só as compras feitas no menu afetam o perfil; obter um augment não é uma compra permanente.

## Etapas

1. **Combate base:** menu, personagem, uma arena, três armas, dois inimigos e rondas.
2. **Identidade roguelike:** XP, raridades, efeitos, seleção pausada e boss.
3. **Progressão e mapas:** perfil, loja, infinito e variantes limitadas.
4. **Entrega:** assets, áudio, balanceamento, desempenho e documentação final.

Os passos são orientação, sem prazos ou divisão por pessoa. O backlog regista as
dependências reais; algumas tarefas podem avançar independentemente.


## Regras implementadas de armas, rondas e augments

A expansão definida em `implementation-prompt-augments.md` está implementada nos
itens marcados como sim. São dez cartas novas: três douradas (Precision, Dead Center,
Blast Bloom) e sete roxas (Split Chamber, Ember Rounds, Slipstream Feed, Last Spark,
Siege Frame, Redline e Aftershot).
As regras numéricas e de interação do prompt são a referência desta expansão.
Os itens marcados como não continuam por implementar.

- Disparo contínuo usa o tempo decorrido e pode criar vários tiros por frame,
  respeitando munição e cooldown. Cada bala só avança pelo tempo restante do seu
  primeiro frame. Não há crédito de tiros por estar parado, sem munição ou em pausa.
- Críticos são sorteados por bala principal, capturados ao disparar e conservados
  nos ricochetes. A chance acima de 100% converte o excedente em dano crítico.
- Queimaduras preservam duração e autoria; ecos não gastam munição, não critam e
  não disparam efeitos primários nem outros ecos. Barris não ativam efeitos de acerto.
- Last Spark resolve a morte no fim da fase de dano, consumindo no máximo uma carga
  por frame, sem imunidade no seguinte. Siege Frame verifica geometria antes da compra.
- Os ícones explícitos e os casos de reutilização estão em `icon-map.md`.

- Disparo: `Player.try_fire()` verifica vida, cooldown e reserva em `Arsenal`, consumindo
  uma munição apenas por disparo aceite. O mundo cria os
  projéteis apenas quando aceita o comando; a animação usa esse resultado. Cada arma
  conserva o seu cooldown. Input e simulação usam passos variáveis, e o disparo
  contínuo calcula os tiros devidos dentro de cada frame pelo tempo decorrido.
- Nove cinzentos, três por arma: pistola (dano, cadência, alcance), shotgun (pellets,
  dano, cadência), SMG (cadência, dano, alcance). Há onze dourados e dez prismáticos.
- Stats globais: AD base 100 e attack speed base 1,00. Dano final da arma = dano
  base × AD/100 × modificador específico; cadência final = cadência base × attack
  speed × modificador específico. A loja oferece +5 AD/+0,05 AS por nível (máximo
  cinco); cartas douradas concedem +20 AD/+0,15 AS sem limite. Melhorias por arma
  foram removidas da loja e o custo original é devolvido uma vez ao carregar o perfil.
- Modificadores numéricos são aditivos em relação à base: dois +20% dão 1,40×.
  Augments acumulam sem limite em todas as ofertas. Dano, cadência, alcance,
  pellets e velocidade de movimento não têm teto de atributos. Aumentar vida
  máxima cura o incremento. Pré-requisitos e incompatibilidades mantêm-se.
- A base permanente é copiada ao criar a partida. Recalcular atributos começa
  sempre nessa base, sem reaplicar multiplicadores anteriores.
- Uma oferta sorteada pertence ao mundo e mantém-se até ser consumida. Cada
  aquisição limpa a oferta, consome uma escolha pendente e recalcula elegibilidade.
- A fila `AugmentChoice` distingue level-ups de recompensas de ronda, guardando nível,
  número de ronda e arma alvo. A morte final pode gerar ambas sem perder nenhuma.
  Armas bloqueadas não aparecem nas escolhas de level-up. Bónus de ronda só oferecem
  os cinzentos da arma alvo; todos os augments continuam disponíveis para acumular
  nas rondas infinitas.
- Projéteis guardam a arma de origem. Ricochetes e explosões encadeadas preservam
  essa autoria, mesmo com troca de arma. Mortes por satélites independentes usam a
  arma ativa. `RoundCompleted` transporta a arma do último inimigo morto.
- Caixas de munições vivem até 60 segundos de simulação (máximo de 100 ativas),
  piscam nos últimos 5 segundos e desaparecem ao sair da área simulada no infinito.
  Uma caixa não é consumida se todas as reservas estiverem cheias. Pausa/seleção
  preservam reservas, caixas e tempos; repetir a partida reinicia tudo.
- Pesos, IDs, alvos, referências e ciclos de pré-requisitos são validados. As
  incompatibilidades são respeitadas nos dois sentidos. Fallback pode apresentar
  menos de três cartas se não houver suficientes; um pool vazio dispensa o nível.
- Cartas aceitam uma confirmação por oferta. Teclas/botão mantidos e repetição de
  teclado não confirmam automaticamente a próxima. Esc abre pausa; continuar
  preserva a mesma oferta, e abandonar descarta as escolhas dessa partida.
- As rondas não têm limite numérico. O orçamento cresce até 300 inimigos por ronda
  (configurável), com máximo de 50 ativos. A vida cresce 20 pontos percentuais por
  ronda até à 10 e, depois, multiplica por 1,20 em cada ronda. O dano normal cresce
  5 pontos percentuais por ronda, mas cada acerto fica limitado a 49% da vida máxima
  do jogador. Bosses e escoltas seguem a configuração de cada décima ronda.
- Spawns usam posições fora da distância de segurança, dentro dos limites e livres
  de obstáculos e inimigos; se nenhuma estiver disponível, o orçamento espera.
  Layouts novos precisam de pontos de spawn suficientes para essa distância.
- Na arena limitada não se removem inimigos por distância: todos continuam vivos
  na contagem até serem mortos, mesmo fora do ecrã. Não há despawn com recompensa
  ou conclusão artificial de ronda. No infinito, inimigos distantes são
  reposicionados vivos, preservando ID, vida e a contagem da ronda.


## Mapas e inimigos implementados

- Barris (obstáculo de índice 2) recebem dano de projéteis e têm a vida de um
  inimigo básico da ronda atual. Dano já recebido é preservado entre rondas.
  Ao chegar a zero desaparecem da colisão/navegação e explodem com animação laranja,
  raio de 180 unidades e dano igual a duas vezes essa vida. A explosão atinge inimigos,
  jogador (máximo de 49% da vida máxima por explosão) e outros barris. Barris não dão
  recompensas próprias; mortes de inimigos causadas pela explosão seguem as regras
  normais. A destruição persiste na partida, mesmo ao descarregar chunks no infinito.

- O menu oferece Arena, Ruínas e Terras infinitas, com miniaturas. As duas arenas
  têm layouts abertos distintos, limites e zonas de spawn alcançáveis. O mesmo
  World gere combate, rondas, XP e augments em todos os mapas.
- Repetir cria um mundo novo no mapa selecionado. Voltar ao menu permite escolher
  outro mapa. O resumo identifica o mapa da partida.
- Terras infinitas usa chunks de 768 unidades, com vizinhança 5×5 (25 chunks).
  A geração deriva da seed e coordenada, incluindo negativas; descarregar/regressar
  reproduz os mesmos obstáculos e decorações, sem histórico crescente de chunks.
- A câmara acompanha o jogador sem fronteiras. Spawns usam um anel junto às margens da vista, fora da zona
  segura de 400 unidades e dentro da vizinhança simulada.
- Um inimigo a mais de 1450 unidades é reposicionado para uma posição válida no
  anel: preserva ID, vida, escala e contagens. O ataque em preparação é cancelado
  ao recolocar, para não disparar imediatamente junto da área visível. Não há XP,
  moeda nem evento de morte nessa operação. Projéteis/efeitos fora da vizinhança
  são descartados; cadáveres duram até um segundo e não contam como vivos.
- Navegação usa linha direta quando livre e A* local em grelha de 96 unidades
  quando existe obstáculo. Segmentos consideram o raio para não cortar cantos.
  As rotas/geometria têm cache e até três novos planos por frame. Não há formação
  tática ou perseguição global através de chunks descarregados.
- Normal: perseguição → preparação/golpe → recuperação; vermelho e boss:
  perseguição → preparação → disparo → recuperação. Morte é um estado terminal,
  cancela disparos pendentes e mantém apenas a animação, sem dano/colisão.
  Matar o boss também desativa os projéteis que ele já tinha disparado.
- O vermelho só prepara/dispara com linha de visão. O boss alterna a rotação
  das rajadas em anel; ataques e projéteis ficam parados em pausa/seleção.
- A presença de vermelhos começa em 10% na ronda 3, cresce 10 pontos percentuais
  por ronda e fica limitada a 50% desde a ronda 7.
- Desde a ronda 5, inimigos normais ou vermelhos podem ser elites. A probabilidade
  começa em 5%, cresce 2 pontos percentuais por ronda até 30%, e elites têm 3x vida,
  1,5x XP e uma etiqueta visual.
- Nas rondas 5, 10, 15… um spawn normal é substituído por um Prismatic, normal ou
  vermelho, com 5x a vida da ronda e etiqueta roxa. Não acumula o modificador elite.
  A sua morte e a morte de cada boss concedem, separadamente, uma escolha garantida
  entre augments prismáticos. A escolha pausa a partida e permite ultrapassar os
  stacks sem limite; XP e o bónus de fim de ronda continuam independentes.
- Windup e recovery mantêm os valores base até à ronda 9; desde a ronda 10 diminuem
  6% por ronda até ao mínimo de 70%.
- Bosses nas rondas 10, 20, 30… acompanham metade do orçamento normal. A vida é
  multiplicada por 10 entre bosses (1x, 10x, 100x…) e qualquer projétil do boss é
  letal. As recompensas mantêm +25% por boss adicional. A ronda só termina depois
  de acabar o orçamento e morrerem todos os inimigos, incluindo as escoltas.


### Ritmo de chegada dos inimigos

A primeira ronda começa após 0,5 s e o intervalo entre rondas é de 2 s. Nas três
primeiras rondas os spawns têm intervalo de 0,25 s; depois passam para 0,45 s.
Todos os mapas procuram posições junto das margens da vista lógica, com folga
para o raio do inimigo e distância mínima de 400 unidades. No início, dão
preferência aos pontos mais próximos com linha de visão, evitando uma longa
viagem por trás de obstáculos. Validam sempre limites, obstáculos e ocupação;
pontos fixos da arena são apenas fallback quando o anel não tem posições livres.
