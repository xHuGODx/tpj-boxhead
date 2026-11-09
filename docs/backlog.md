# Backlog

As 24 issues estão publicadas no GitHub, sem responsáveis atribuídos e sem divisão por pessoa.
Cada issue contém objetivo, critérios de aceitação, arquitetura, validação e dependências.
As regras assinaladas como propostas no [design](game-design.md) podem ser ajustadas.

O setup inicial já está implementado; as issues descrevem o desenvolvimento a partir dessa base.
Prioridade alta identifica combate e identidade roguelike; prioridade normal identifica
progressão permanente, mapas adicionais e preparação da entrega. Todas fazem parte do plano.

Escolher tarefas com dependências concluídas. Os números organizam o backlog; não impõem
uma sequência estrita. Geometria, perfil e pesquisa de assets podem começar independentemente.

## Combate base

| Issue | Dependências |
| --- | --- |
| [#1 · Implementar fluxo de menu, partida, pausa e game over](https://github.com/xHuGODx/tpj-boxhead/issues/1) | — |
| [#2 · Implementar jogador com WASD, orientação persistente e comandos](https://github.com/xHuGODx/tpj-boxhead/issues/2) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1) |
| [#3 · Extrair geometria, deteção de colisões e contactos de projéteis](https://github.com/xHuGODx/tpj-boxhead/issues/3) | — |
| [#4 · Criar arena limitada, obstáculos e câmara em coordenadas do mundo](https://github.com/xHuGODx/tpj-boxhead/issues/4) | [#2](https://github.com/xHuGODx/tpj-boxhead/issues/2), [#3](https://github.com/xHuGODx/tpj-boxhead/issues/3) |
| [#5 · Introduzir eventos de domínio com Observer e Event Queue](https://github.com/xHuGODx/tpj-boxhead/issues/5) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1) |
| [#6 · Implementar pistola, shotgun e metralhadora](https://github.com/xHuGODx/tpj-boxhead/issues/6) | [#2](https://github.com/xHuGODx/tpj-boxhead/issues/2), [#3](https://github.com/xHuGODx/tpj-boxhead/issues/3), [#4](https://github.com/xHuGODx/tpj-boxhead/issues/4), [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5) |
| [#7 · Implementar inimigo normal com FSM e dano de contacto](https://github.com/xHuGODx/tpj-boxhead/issues/7) | [#2](https://github.com/xHuGODx/tpj-boxhead/issues/2), [#3](https://github.com/xHuGODx/tpj-boxhead/issues/3), [#4](https://github.com/xHuGODx/tpj-boxhead/issues/4), [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6) |
| [#8 · Implementar inimigo vermelho com ataque à distância](https://github.com/xHuGODx/tpj-boxhead/issues/8) | [#7](https://github.com/xHuGODx/tpj-boxhead/issues/7) |
| [#9 · Introduzir rondas infinitas, orçamento de spawns e dificuldade crescente](https://github.com/xHuGODx/tpj-boxhead/issues/9) | [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#7](https://github.com/xHuGODx/tpj-boxhead/issues/7), [#8](https://github.com/xHuGODx/tpj-boxhead/issues/8) |
| [#11 · Criar HUD, resumo de partida e contabilidade de recompensas](https://github.com/xHuGODx/tpj-boxhead/issues/11) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1), [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6), [#9](https://github.com/xHuGODx/tpj-boxhead/issues/9) |

## Identidade roguelike

| Issue | Dependências |
| --- | --- |
| [#10 · Adicionar boss periódico a cada 10 rondas](https://github.com/xHuGODx/tpj-boxhead/issues/10) | [#8](https://github.com/xHuGODx/tpj-boxhead/issues/8), [#9](https://github.com/xHuGODx/tpj-boxhead/issues/9) |
| [#12 · Implementar XP, níveis e fila de level-ups](https://github.com/xHuGODx/tpj-boxhead/issues/12) | [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#7](https://github.com/xHuGODx/tpj-boxhead/issues/7), [#11](https://github.com/xHuGODx/tpj-boxhead/issues/11) |
| [#13 · Definir catálogo de augments, raridades e sorteio de ofertas](https://github.com/xHuGODx/tpj-boxhead/issues/13) | [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6), [#12](https://github.com/xHuGODx/tpj-boxhead/issues/12) |
| [#14 · Implementar atributos derivados e augments cinzentos/dourados](https://github.com/xHuGODx/tpj-boxhead/issues/14) | [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6), [#13](https://github.com/xHuGODx/tpj-boxhead/issues/13) |
| [#15 · Implementar três augments prismáticos com mecânicas distintas](https://github.com/xHuGODx/tpj-boxhead/issues/15) | [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6), [#13](https://github.com/xHuGODx/tpj-boxhead/issues/13), [#14](https://github.com/xHuGODx/tpj-boxhead/issues/14) |
| [#16 · Criar seleção pausada de três augments por level-up](https://github.com/xHuGODx/tpj-boxhead/issues/16) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1), [#12](https://github.com/xHuGODx/tpj-boxhead/issues/12), [#13](https://github.com/xHuGODx/tpj-boxhead/issues/13), [#14](https://github.com/xHuGODx/tpj-boxhead/issues/14) |

## Perfil e mapas

| Issue | Dependências |
| --- | --- |
| [#17 · Persistir perfil local com saldo e melhorias permanentes](https://github.com/xHuGODx/tpj-boxhead/issues/17) | — |
| [#18 · Implementar loja do menu e aplicar melhorias permanentes](https://github.com/xHuGODx/tpj-boxhead/issues/18) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1), [#11](https://github.com/xHuGODx/tpj-boxhead/issues/11), [#14](https://github.com/xHuGODx/tpj-boxhead/issues/14), [#17](https://github.com/xHuGODx/tpj-boxhead/issues/17) |
| [#19 · Implementar mapa infinito com chunks e câmara móvel](https://github.com/xHuGODx/tpj-boxhead/issues/19) | [#3](https://github.com/xHuGODx/tpj-boxhead/issues/3), [#4](https://github.com/xHuGODx/tpj-boxhead/issues/4), [#7](https://github.com/xHuGODx/tpj-boxhead/issues/7), [#9](https://github.com/xHuGODx/tpj-boxhead/issues/9) |
| [#20 · Adicionar seleção de mapa e variantes de arenas limitadas](https://github.com/xHuGODx/tpj-boxhead/issues/20) | [#1](https://github.com/xHuGODx/tpj-boxhead/issues/1), [#4](https://github.com/xHuGODx/tpj-boxhead/issues/4), [#19](https://github.com/xHuGODx/tpj-boxhead/issues/19) |

## Apresentação e entrega

| Issue | Dependências |
| --- | --- |
| [#21 · Pesquisar sprites e integrar catálogo partilhado de assets](https://github.com/xHuGODx/tpj-boxhead/issues/21) | — |
| [#22 · Adicionar áudio e feedback visual de combate e escolhas](https://github.com/xHuGODx/tpj-boxhead/issues/22) | [#5](https://github.com/xHuGODx/tpj-boxhead/issues/5), [#6](https://github.com/xHuGODx/tpj-boxhead/issues/6), [#7](https://github.com/xHuGODx/tpj-boxhead/issues/7), [#9](https://github.com/xHuGODx/tpj-boxhead/issues/9) |
| [#23 · Validar jogo integrado, balancear progressão e medir desempenho](https://github.com/xHuGODx/tpj-boxhead/issues/23) | Issues #1–#22 (jogo integrado) |
| [#24 · Atualizar UML e justificar os padrões na versão final](https://github.com/xHuGODx/tpj-boxhead/issues/24) | [#23](https://github.com/xHuGODx/tpj-boxhead/issues/23) |
