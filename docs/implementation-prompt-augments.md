# Prompt de implementação — novos stats, itens e augments

Estado: âmbito marcado como `sim` implementado na branch `feat/augment-expansion`.
As linhas marcadas como `não` continuam apenas propostas. Este documento conserva as regras de referência, editáveis para ajustes futuros.
Os valores acrescentados nesta revisão são estimativas para playtest; continuam todos editáveis.

## Como usar e editar

1. Altera as tabelas e as fichas abaixo com as regras que quiseres.
2. Na coluna `Implementar`, usa `sim` ou `não`. Isto indica intenção, não trabalho concluído.
3. Ajusta os números e regras que quiseres. Os valores sugeridos são nossos, não os valores dos jogos de referência.
4. Depois pede: **“Implementa o que está marcado como sim em docs/implementation-prompt-augments.md.”**

## Instruções para o agente que implementar

Lê este documento completo e inspeciona o código atual antes de alterar o jogo.
Implementa apenas as funcionalidades marcadas como `sim`, incluindo as dependências necessárias.
As decisões editadas neste documento prevalecem sobre as sugestões anteriores da conversa.
Não implementes os itens marcados como `não` nem transformes este catálogo inteiro em âmbito obrigatório.

O documento já contém decisões suficientes para implementar o âmbito selecionado. Resolve detalhes técnicos de acordo com estas regras; só pede esclarecimentos se uma edição posterior introduzir uma contradição material.
Não substituas valores definidos por outros valores de balanceamento sem explicar a alteração.
Mantém os números de gameplay configuráveis, sem espalhar constantes pelo código.
No final, explica o que implementaste, como verificaste e quais as decisões ainda pendentes.

## Objetivo e regras a preservar

Queremos builds muito OP, com sinergias visíveis, enquanto os inimigos acabam por ultrapassar o jogador.

- O jogador escolhe uma única arma para levar para a partida; comprar armas desbloqueia opções de escolha.
- AD e AS são globais. As cartas cinzentas especializam a arma escolhida.
- Augments da partida acumulam sem limite de stacks. A loja tem limites por melhoria.
- Não reintroduzir tetos artificiais de AD, AS, projéteis ou outros stats do jogador.
- Preservar as curvas, limites e recompensas atuais dos inimigos, bosses, elites e Prismatics.
- Manter o sorteio normal em 60% cinzento / 30% dourado / 10% roxo com Luck zero.
- Bosses e inimigos Prismatic continuam a dar escolhas roxas garantidas.
- Uma escolha dá um augment, não todas as cartas apresentadas.
- Preservar saves, moedas, armas compradas e melhorias existentes.
- Código e texto dentro do jogo em inglês; documentação e explicações em português.
- Não usar sprites ou outros assets extraídos dos jogos de referência.
- Usar os nomes próprios abaixo nas cartas, loja e descrições. Os nomes originais aparecem apenas nas notas de inspiração e nas fontes; não são nomes a implementar.

## Âmbito selecionado

Esta é a primeira leva sugerida. Editar `Implementar` para mudar o âmbito.

| Implementar | Funcionalidade | Onde aparece | Prioridade |
| --- | --- | --- | --- |
| sim | Split Chamber / Projectile Count | Roxa + loja limitada | 1 |
| sim | Sistema de críticos | Stats + douradas + loja limitada | 1 |
| sim | Ember Rounds | Roxa | 2 |
| sim | Blast Bloom / Blast Radius | Dourada + loja limitada | 2 |
| sim | Slipstream Feed | Roxa | 3 |
| sim | Last Spark | Roxa | 3 |
| não | Velocity Kit / Projectile Speed | Dourada + loja limitada | Depois |
| não | Fortune Chip / Luck | Dourada + loja limitada | Depois |
| não | Bounty Seal / Greed | Dourada + loja limitada | Depois |
| não | Salvage Magnet / Pickup Radius | Loja; carta opcional | Depois |
| não | Impact Plating | Dourada + loja limitada | Depois |
| sim | Siege Frame | Roxa | 3 |
| sim | Redline | Roxa | 3 |
| sim | Aftershot | Roxa | 3 |
| não | Missões evolutivas | Cartas com objetivos | Depois |

### Nomes e identificadores para implementação

| Nome apresentado | ID sugerido |
| --- | --- |
| Split Chamber | `split_chamber` |
| Ember Rounds | `ember_rounds` |
| Blast Bloom | `blast_bloom` |
| Slipstream Feed | `slipstream_feed` |
| Last Spark | `last_spark` |
| Siege Frame | `siege_frame` |
| Redline | `redline` |
| Aftershot | `aftershot` |
| Velocity Kit | `velocity_kit` |
| Fortune Chip | `fortune_chip` |
| Bounty Seal | `bounty_seal` |
| Salvage Magnet | `salvage_magnet` |
| Impact Plating | `impact_plating` |

Os nomes dos stats, como Projectile Count, AD, AS e Crit Chance, mantêm-se descritivos.
Esta revisão muda apenas nomes, não efeitos, raridades, valores ou âmbito selecionado.

## Decisões transversais

| Regra | Proposta / decisão editável |
| --- | --- |
| Consumo de munição | Uma munição por disparo original, independentemente do número de projéteis. |
| Split Chamber na shotgun | Duplica a salva completa, não acrescenta apenas um pellet. |
| Distribuição de projéteis | Pistola e SMG: tiros simultâneos e paralelos, com origens desfasadas lateralmente 10 unidades, centradas na direção de disparo. Shotgun: manter a abertura angular atual, distribuindo os pellets extra dentro da mesma abertura. |
| Efeitos ao acertar | Contam por projétil principal e por inimigo atingido, a 100% de eficácia, incluindo pellets. Barris não ativam estes efeitos. |
| Dano secundário | Não gera novas cópias de si próprio nem ativa automaticamente todos os efeitos ao acertar. |
| Críticos de efeitos secundários | Só os projéteis principais das armas podem critar, incluindo os criados por Split Chamber. Os tiros secundários de Aftershot não podem critar. Queimaduras, explosões e orbitais também não. |
| Stacks temporários | Sem teto de quantidade; duração e perda definidas nas fichas de Slipstream Feed e Redline. Pausar congela os temporizadores. |
| Informação ao jogador | Mostrar stats relevantes e descrições com números, duração e condições de ativação. |

### Tipos de dano e interações

| Fonte | Pode critar | Aplica Ember Rounds | Dá stacks de Slipstream Feed | Dá stacks de Redline | Ativa Aftershot |
| --- | --- | --- | --- | --- | --- |
| Projétil principal / pellet / cópia de Split Chamber | Sim | Sim | Sim | Se for crítico | Uma ativação por disparo original, não por acerto |
| Ricochete de um projétil principal | Conserva o crítico original | Sim, em cada novo inimigo | Sim | Se o projétil for crítico | Não |
| Projétil secundário de Aftershot | Não | Não | Não | Não | Não |
| Queimadura, explosão ou orbital | Não | Não | Não | Não | Não |

Ricochetes de tiros secundários conservam a classificação secundária e não passam a ativar estes efeitos.
Chain Reaction continua a poder ser ativada por mortes causadas por estas fontes, com a proteção de encadeamento existente.
Uma bala nunca repete um acerto no mesmo inimigo apenas por ricochetear. Contar dano efetivamente causado, não colisões com inimigos já mortos.

## 1. Split Chamber

Inspiração: Duplicator / Amount de Vampire Survivors.

- Novo stat global: `Projectile Count`.
- Base: **1**.
- Carta roxa: **+1 por stack**, sem teto na partida.
- Loja: **+1**, máximo **1 nível**.
- Preço da loja: **2.500 moedas**, compra única. É uma melhoria permanente muito forte; o preço inicial é mais de seis vezes o da shotgun.
- Aplicação: projéteis das armas; não duplicar automaticamente orbitais, explosões ou queimaduras.
- Cada cópia conserva o dano normal do projétil e a autoria da arma.
- Pistola/SMG: manter a mesma direção e desfasar as origens perpendicularmente 10 unidades entre vizinhos; com duas balas, os offsets são -5 e +5. Com três, -10, 0 e +10.
- Shotgun: manter o spread atual da arma. Aumentar a quantidade dentro desse cone, sem multiplicar também o ângulo.
- Testar o caminho entre a arma e cada origem desfasada: cópias não podem nascer através de paredes/barris. Uma cópia bloqueada acerta no obstáculo; não atravessa nem reduz o custo de munição.

```text
Projéteis por disparo = (pellets base da arma + pellets extra da arma) × Projectile Count
```

| Arma | Count 1 | Count 2 | Count 3 |
| --- | --- | --- | --- |
| Pistola | 1 bala | 2 balas | 3 balas |
| SMG | 1 bala | 2 balas | 3 balas |
| Shotgun sem upgrades | 6 pellets | 12 pellets | 18 pellets |

Exemplo adicional: shotgun com 8 pellets e Count 3 dispara 24 projéteis por munição.

## 2. Sistema de críticos

Stats globais novos: `Crit Chance` e `Crit Damage`.

| Parâmetro | Valor editável |
| --- | --- |
| Chance base | 0%. |
| Multiplicador de dano crítico base | 2,00× o dano normal. |
| Carta dourada de chance | +15 pontos percentuais por stack, sem teto de stacks. |
| Carta dourada de dano crítico | +0,15 ao multiplicador por stack: 2,00× → 2,15×. Não multiplica o valor anterior por 1,15. |
| Loja: Crit Chance | +5 pontos percentuais por nível, máximo 5 níveis; custo inicial 150 moedas, crescimento ×1,6 por nível. |
| Loja: Crit Damage | +0,10 ao multiplicador por nível, máximo 5 níveis; custo inicial 150 moedas, crescimento ×1,6 por nível. |
| Chance acima de 100% | Conservar a chance bruta. Acima de 100%, todos os tiros principais critam e cada ponto percentual excedente acrescenta 0,005 ao multiplicador. Exemplo: 110% dá crítico garantido e +0,05 ao multiplicador. |
| Sorteio | Independente por projétil principal, uma vez ao criar a bala. Cada pellet pode critar ou não; o resultado acompanha o projétil nos ricochetes. |

**O que significa “sorteio por projétil ou por salva”?** Com 30% de chance, sortear por salva faria o disparo inteiro da shotgun ser crítico ou normal. Sortear por projétil dá a cada pellet a sua própria tentativa de 30%: numa salva podes ter uma mistura de pellets normais e críticos. Escolhemos a segunda opção, coerente com os efeitos por projétil.

```text
C = chance bruta em fração; 110% = 1,10
Chance efetiva = min(C, 1)
Multiplicador crítico = 2 + bónus de dano crítico + 0,5 × max(0, C - 1)
Dano crítico = dano normal efetivo da arma × multiplicador crítico
```

Os stats atuais são capturados na criação do projétil; melhorias posteriores não alteram balas já em voo.
A chance bruta continua sem teto de progressão; apenas a probabilidade de um evento fica matematicamente limitada a 100%.
Exemplo: 110% de chance e uma carta de dano crítico dão 2,00 + 0,15 + 0,05 = **2,20×**.

Os críticos devem abrir uma alternativa a investir apenas em AD/AS. Dar feedback visual legível.
Não criar Redline ou outras cartas dependentes de críticos antes deste sistema funcionar.

## 3. Ember Rounds

Inspiração: ataques que aplicam queimaduras acumuláveis em ARAM: Mayhem.

- Raridade: roxa.
- Acertar com uma bala aplica queimadura ao inimigo.
- Várias aplicações acumulam; ideal para a SMG e Split Chamber.
- Cada acerto principal aplica uma queimadura independente de **3 segundos**.
- Cada aplicação causa **0,02 × AD × stacks da carta** de dano por segundo. Com AD 100 e uma carta: 2 HP/s, 6 HP no total; com duas cartas: 4 HP/s por aplicação.
- Usar AD, sem percentagem da vida inimiga e sem multiplicar pelos upgrades de dano específicos da arma ou pelo crítico do acerto.
- Capturar AD, número de stacks e autoria quando a aplicação nasce; novas aplicações não renovam a duração das anteriores.
- Acumular aplicações sem teto. Processar o dano com o tempo real de simulação, sem depender do FPS, e sem guardar uma entidade pesada por aplicação se puderem ser agrupadas sem alterar expirações/autoria.
- Regra para pellets e disparos secundários: seguir a decisão transversal de efeitos ao acertar.
- A queimadura não aplica mais queimaduras a si própria. Preservar a autoria da arma em mortes por dano ao longo do tempo.

## 4. Blast Bloom / Blast Radius

Inspiração: aumento de área de Vampire Survivors.

- Stat global: `Blast Radius`, base 1,00.
- Carta dourada: **+20% de raio por stack**, aditivo relativamente ao raio base.
- Deve afetar Chain Reaction e outros efeitos explosivos do jogador.
- Barris mantêm o raio próprio de 180 unidades, independentemente de quem os detona. Este stat não altera explosões ambientais nem inimigas.
- Loja: **+10% de raio por nível**, máximo **5 níveis**, custo inicial **100 moedas**, crescimento **×1,5 por nível**.
- Fórmula: raio base do efeito × (1 + bónus da loja + 0,20 × stacks da carta). Não aumentar o dano nem o alcance de procura do ricochete.
- Alterar tanto o raio visual como a área real de dano.
- Não confundir +20% de raio com +20% de área; a área cresce com o quadrado do raio.

## 5. Slipstream Feed

Inspiração: acertos concedem movimento e movimento contribui para AS em Mayhem.

- Raridade: roxa.
- Acertar dá stacks temporários de velocidade de movimento.
- Parte da velocidade de movimento extra converte-se em AS.
- Cada acerto principal dá **+0,5% da velocidade de movimento base por stack da carta**, durante **5 segundos**.
- Cada novo acerto renova a duração de todos os stacks deste efeito. Após 5 segundos sem acertar, perdem-se todos; não existe limite de quantidade.
- Converter **50% do bónus de movimento em fração** em AS adicional. Incluir bónus de movimento da loja, cartas e Slipstream Feed; excluir a base.
- Exemplo: +40% de movimento total acrescenta +0,20 ao stat AS. Com AS 1,50 antes da conversão, fica AS 1,70.
- Stacks adicionais da carta aumentam o movimento ganho por acerto; a taxa de conversão mantém-se em 50%, evitando multiplicar o mesmo benefício duas vezes.
- Calcular a conversão a partir da velocidade antes da própria conversão. Não derivar AS diretamente do número de unidades por segundo.
- Evitar um ciclo de cálculo infinito: a conversão movimento → AS não pode voltar a gerar movimento sem um novo acerto.
- Mostrar stacks/bónus ativos. Funciona como build de mobilidade e disparo contínuo.

## 6. Last Spark

Inspiração: ressurreições do Tirajisú de Vampire Survivors.

- Raridade: roxa.
- Cada stack concede **1 carga de ressurreição** durante a partida.
- Ressuscita com **50% da vida máxima**.
- Invulnerabilidade após ressuscitar: 0.
- Deve funcionar contra o ataque letal de bosses.
- Uma morte consome só uma carga, mesmo se vários projéteis acertarem no mesmo frame.
- Resolver a ressurreição no fim da fase de dano do frame: a vida provisoriamente a zero já não recebe outros acertos nesse frame; consumir uma carga e restaurar a vida antes de publicar a morte definitiva.
- Isto não cria segundos de invulnerabilidade: no frame seguinte o jogador já pode morrer de novo, incluindo com outro projétil do boss. Não consumir nem eliminar projéteis que não chegaram a acertar.
- Só terminar a partida/publicar a morte definitiva quando não restarem cargas.
- Pausar, recalcular stats ou retomar a partida não pode restaurar cargas consumidas.
- Mostrar cargas restantes; não confundir stacks adquiridos com cargas ainda disponíveis.


## 7. Siege Frame, Redline e Aftershot

| Carta | Efeito | Stacking e parâmetros |
| --- | --- | --- |
| Siege Frame | +30% de vida máxima e +15% de AD total por stack; personagem e hitbox maiores. | Multiplicadores 1 + 0,30 × N para vida e 1 + 0,15 × N para AD; tamanho linear cresce +5% da base por stack. Sem teto e sem multiplicar por 1,30/1,15 repetidamente. |
| Redline | Cada acerto crítico principal dá +0,02 AS por stack da carta, durante 4 s. | Acumulação sem teto. Cada novo crítico renova todos os stacks; perdem-se todos após 4 s sem crítico. |
| Aftershot | Cada disparo original gera uma salva secundária após 0,20 s, com 40% do dano normal. | Cada stack acrescenta uma salva; atrasos 0,20 s, 0,40 s, 0,60 s… Todas com 40% do dano normal e sem gastar munições. |

### Siege Frame: fórmulas e espaço no mapa

- Aplicar o multiplicador de vida depois dos bónus fixos da loja/Vitality/Juggernaut; aplicar o de AD depois dos bónus fixos globais.
- Aumentar a vida máxima cura apenas a diferença, tal como a regra atual do jogador.
- O sprite, sombra, posição da arma e hitbox devem corresponder ao tamanho real.
- Usar o raio atual em colisões, posicionamento e deteção de acertos, sem constantes escondidas do raio inicial.
- Crescer pode fechar corredores: esse é o custo da carta. Não encolher automaticamente o jogador para caber.
- Antes de mostrar Siege Frame numa oferta, verificar se existe espaço válido na área carregada para o tamanho seguinte. Se não existir, a carta fica temporariamente inelegível por geometria, não por limite de stacks.
- Ao adquirir, usar a posição válida mais próxima, com procura determinística limitada à área carregada. A procura é uma verificação geométrica, não um teletransporte através de paredes: só aceitar posições alcançáveis a partir da posição atual com o raio anterior.
- Revalidar a posição antes de consumir a escolha; falhar esta validação não cobra a carta nem altera os stats.

### Redline: acesso e ativação

- Oferecer apenas com chance crítica bruta superior a zero. Ao adquirir chance, a carta torna-se elegível.
- Cada pellet crítico conta; um ricochete crítico também conta ao atingir outro inimigo. Tiros de Aftershot não contam.
- Calcular o bónus temporário a partir de um contador próprio, sem alterar permanentemente os modificadores do inventário.

### Aftershot: captura do disparo

- Guardar o dano **normal antes do crítico**, os parâmetros da arma, número de projéteis, origens relativas e direções do disparo original.
- No momento do eco, emitir a salva a partir da posição atual do jogador, com as direções guardadas. Revalidar paredes e origens, tal como nos tiros principais.
- Split Chamber já está incluído na salva capturada: não o aplicar outra vez ao emitir o eco.
- Os ecos têm 40% do dano normal guardado, mesmo se a bala original tiver sido crítica. Não sortear críticos para ecos.
- Podem ricochetear se o jogador tinha Ricochet ao disparar, mas não aplicam Ember Rounds, Slipstream Feed ou Redline.
- Os ecos não geram novos ecos. Morrendo o jogador, cancelar os ecos pendentes; pausar apenas congela os atrasos.
- Não atribuir custos ou cooldowns novos a estes disparos.

Split Chamber aumenta os projéteis simultâneos; Aftershot repete a salva mais tarde.
Disparos secundários devem guardar a autoria original e não voltar a ativar a sua própria repetição.


## 8. Dependências técnicas e verificação

- Rever o limite atual de um disparo por frame antes de expandir muito AS. A cadência deve conseguir cumprir vários disparos num frame quando necessário, respeitando munições e o tempo decorrido.
- Não acumular disparos pendentes por estar parado, sem disparar, pausado ou a escolher cartas.
- Separar dano direto, queimaduras, explosões e ataques secundários; definir explicitamente quais os efeitos que cada um pode ativar.
- Preservar AD/AS globais, modificadores específicos, autoria do dano, XP, moedas e recompensas garantidas.
- Testar combinações com Split Chamber, shotgun, ricochetes e Chain Reaction; evitar duplicações recursivas e recompensas repetidas.
- Confirmar que stats e cargas não se multiplicam ao recalcular modificadores ou retomar uma pausa.
- Verificar os exemplos numéricos deste documento: shotgun 6/12/18 projéteis; crítico 110% com uma carta de dano = 2,20×; Ember Rounds com AD 100 = 6 de dano total por aplicação com uma carta.
- Confirmar que Last Spark consome no máximo uma carga por frame, mas não protege contra um acerto no frame seguinte.
- Confirmar que Siege Frame não deixa o jogador sobreposto a obstáculos e que ofertas impossíveis por geometria não bloqueiam a seleção.
- Verificar compras limitadas, persistência, novos perfis e carregamento de saves antigos sem editar o perfil real só para testar.
- Reutilizar as animações de explosão existentes. Não exigir gerar sprites novos para implementar regras.
- Atualizar descrições das cartas, loja, HUD e documentação para corresponderem ao comportamento real.

## Combinações que queremos tornar possíveis

- SMG + Split Chamber + Ember Rounds: muitas balas a acumular queimaduras.
- Shotgun + críticos + área de explosão: disparos fortes que limpam grupos.
- Pistola + ricochetes + Slipstream Feed: precisão e mobilidade com tiros a saltar entre alvos.

## Fontes da pesquisa

Estas fontes explicam a inspiração; as regras de implementação são as editadas acima.

- [Vampire Survivors — Duplicator](https://vampire.survivors.wiki/w/Duplicator)
- [Vampire Survivors — Passive items](https://vampire.survivors.wiki/w/Passive_items)
- [Vampire Survivors — Tirajisú](https://vampire.survivors.wiki/w/Tirajis%C3%BA)
- [ARAM: Mayhem — Augments](https://wiki.leagueoflegends.com/en-us/ARAM%3A_Mayhem/Augments)
- [Riot — Patch 26.12: Ability e Quest Augments](https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-12-notes/)
