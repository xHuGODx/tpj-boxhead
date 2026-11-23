# Design do jogo

## Decisões confirmadas

- Jogo em Python/Pygame, para um jogador.
- Movimento com WASD; Espaço dispara na orientação da personagem.
- Mapas limitados e um modo de mapa infinito.
- Rondas infinitas com dificuldade crescente e bosses periódicos, inicialmente a cada 10 rondas.
- Três armas iniciais: pistola, shotgun e metralhadora.
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
| Disparo | Segurar Espaço repete disparos respeitando o cooldown; munições ilimitadas na primeira versão. |
| Troca de arma | Teclas 1/2/3, com cooldown por arma para impedir contornar a cadência. |
| Disponibilidade de armas | As três armas disponíveis na partida inicial; desbloqueios ficam para expansão. |
| Rondas | Orçamento finito de inimigos por ronda; termina quando não há spawns pendentes nem inimigos vivos. |
| Entre rondas | Intervalo curto configurável; o relógio da partida também pausa em menus e escolhas. |
| Dificuldade | Quantidade, composição e atributos crescem por curvas configuráveis; limites de ativos controlam carga sem terminar as rondas. |
| Vermelho | Mais resistente, com ataque à distância e preparação visível; confirmar o comportamento pretendido ao implementar. |
| Boss | Um boss inicial com fases de perseguição, preparação, ataque e recuperação, nas rondas 10, 20, 30… |
| XP | Recompensa automática por morte de inimigo; pickups físicos podem ser acrescentados depois. |
| Moeda permanente | Ganha em mortes/rondas, separada do XP; creditada uma vez no fim da partida. |
| Loja | Níveis de vida máxima, velocidade e ganho de XP, com custos crescentes e limites configuráveis. |
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
| Vida atual e cooldowns | Versão do formato de save |
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

- Disparo: `Player.try_fire()` é a única autoridade do cooldown. O mundo cria os
  projéteis apenas quando aceita o comando; a animação usa esse resultado. Cada arma
  conserva o seu cooldown ao trocar. Input e simulação usam passos variáveis, pelo
  que o instante do disparo fica quantizado ao frame (no máximo um tiro por frame).
- Nove cinzentos, três por arma: pistola (dano, cadência, alcance), shotgun (pellets,
  dano, cadência), SMG (cadência, dano, alcance). Há seis dourados e três prismáticos.
- Modificadores numéricos são aditivos em relação à base: dois +20% dão 1,40×.
  Limites derivados: dano 0,1–5×; alcance 0,1–3×; velocidade de movimento 0,1–3×;
  pellets 1–32 e intervalo mínimo entre tiros 0,05 s. Vida/regen/XP respeitam os
  limites de acumulação do catálogo. Aumentar vida máxima cura o incremento.
- A base permanente é copiada ao criar a partida. Recalcular atributos começa
  sempre nessa base, sem reaplicar multiplicadores anteriores.
- Uma oferta sorteada pertence ao mundo e mantém-se até ser consumida. Cada
  aquisição limpa a oferta, consome um nível pendente e recalcula elegibilidade.
- Pesos, IDs, alvos, referências e ciclos de pré-requisitos são validados. As
  incompatibilidades são respeitadas nos dois sentidos. Fallback pode apresentar
  menos de três cartas se não houver suficientes; um pool vazio dispensa o nível.
- Cartas aceitam uma confirmação por oferta. Teclas/botão mantidos e repetição de
  teclado não confirmam automaticamente a próxima. Esc abre pausa; continuar
  preserva a mesma oferta, e abandonar descarta as escolhas dessa partida.
- As rondas não têm limite numérico. O orçamento cresce até 300 inimigos por ronda
  (configurável), com máximo de 25 ativos. Vida e composição continuam a escalar.
  Bosses e escoltas seguem a configuração de cada décima ronda.
- Spawns usam posições fora da distância de segurança, dentro dos limites e livres
  de obstáculos e inimigos; se nenhuma estiver disponível, o orçamento espera.
  Layouts novos precisam de pontos de spawn suficientes para essa distância.
- Na arena limitada não se removem inimigos por distância: todos continuam vivos
  na contagem até serem mortos, mesmo fora do ecrã. Não há despawn com recompensa
  ou conclusão artificial de ronda. No infinito, inimigos distantes são
  reposicionados vivos, preservando ID, vida e a contagem da ronda.


## Mapas e inimigos implementados

- O menu oferece Arena, Ruínas e Terras infinitas, com miniaturas. As duas arenas
  têm layouts abertos distintos, limites e zonas de spawn alcançáveis. O mesmo
  World gere combate, rondas, XP e augments em todos os mapas.
- Repetir cria um mundo novo no mapa selecionado. Voltar ao menu permite escolher
  outro mapa. O resumo identifica o mapa da partida.
- Terras infinitas usa chunks de 768 unidades, com vizinhança 5×5 (25 chunks).
  A geração deriva da seed e coordenada, incluindo negativas; descarregar/regressar
  reproduz os mesmos obstáculos e decorações, sem histórico crescente de chunks.
- A câmara acompanha o jogador sem fronteiras. Spawns usam um anel de pelo menos
  1000 unidades, fora da zona segura e dentro da vizinhança simulada.
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
- Bosses nas rondas 10, 20, 30… acompanham metade do orçamento normal. Por boss
  adicional: +50% vida, +15% dano e +25% recompensas. A ronda só termina depois
  de acabar o orçamento e morrerem todos os inimigos, incluindo as escoltas.
