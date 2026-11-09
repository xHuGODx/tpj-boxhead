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
- A intenção visual é encontrar sprites do Boxhead e modificá-los; a pesquisa
  e a seleção de assets fazem parte do backlog.

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
- Se uma raridade ficar sem três opções, usar um fallback documentado e testado;
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
