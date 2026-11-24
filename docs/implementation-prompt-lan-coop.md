# Prompt de implementação — co-op LAN para dois jogadores

Estado: plano editável, ainda não implementado. Os valores abaixo são propostas iniciais.

## Como usar

Edita as tabelas e regras antes de implementar. Depois pede:
**“Implementa docs/implementation-prompt-lan-coop.md numa branch nova.”**

Este pedido deve produzir um modo completo e jogável, não apenas sockets ou um protótipo
de movimento. Conservar o single-player e os saves existentes. Não modificar o ZIP de
distribuição já gerado; criar um novo pacote co-op apenas depois de verificar o modo.
Não publicar, abrir portas do router ou instalar serviços externos automaticamente.

## Objetivo

Dois PCs Windows com a mesma versão do jogo, na mesma rede local, jogam a mesma partida.
Um jogador escolhe **Start Hosting**, o outro **Join Game**, introduz o IP local do host
e entra no lobby. Cada jogador escolhe uma arma comprada no seu próprio perfil e tem
build, vida, munições e câmara independentes. Os inimigos, mapa e rondas são partilhados.

Os nomes dos botões e o texto do jogo são em inglês. Documento e explicações em português.

## Decisões principais — editar aqui

| Tema | Decisão inicial |
| --- | --- |
| Jogadores | Exatamente 2: um host e um cliente. |
| Transporte | TCP IPv4 com framing, usando a biblioteca padrão de Python. |
| Endereço de escuta | Selecionar interface LAN; por defeito escutar em 0.0.0.0, mostrar os IPv4 locais úteis. Nunca mostrar 0.0.0.0 como endereço para entrar. |
| Porta | 47632, editável no lobby; não mudar silenciosamente se estiver ocupada. |
| Entrada na sessão | IP local e porta, por exemplo 192.168.1.42:47632. Botão para copiar endereço no host e colar no cliente. |
| Descoberta automática | Fora do primeiro âmbito. Entrada manual por IP é obrigatória e suficiente. |
| Simulação | Apenas o host; passo fixo 60 Hz, desacoplado do desenho. |
| Input do cliente | 30 Hz; enviar logo também quando muda movimento ou disparo, incluindo ao largar teclas. |
| Snapshots | 20 Hz, com tick e sequência de input processada; deltas entre estados completos. |
| Estado completo | Ao entrar e depois a cada 2 segundos; suficiente para corrigir o cliente sem reiniciar a partida. |
| Suavização | Interpolação visual de cerca de 100 ms. Previsão/reconciliação do movimento do jogador local. |
| Friendly fire | Desligado para balas, explosões e orbitais dos jogadores; barris continuam perigosos para ambos. |
| Colisão entre jogadores | Não se bloqueiam nem se empurram. |
| XP | Cada morte dá o XP base integral a ambos; cada um aplica o seu multiplicador de XP. |
| Moedas | Cada um recebe o valor integral da recompensa da equipa, guardado só no seu próprio perfil. |
| Munições | Uma caixa recolhida abastece a arma dos dois; só desaparece se abastecer pelo menos um. |
| Cartas | Ofertas individuais, sorteadas e validadas pelo host; escolha simultânea com pausa global. |
| Escape / build | Pede pausa global; só retomar quando ninguém tem pausa manual ou cartas pendentes. |
| Morte | Consumir Last Spark primeiro; sem cargas, espectador até à ronda seguinte. |
| Ronda seguinte | Reanimar os caídos com 50% da vida máxima, sem restaurar cargas nem encher munições. |
| Fim da partida | Os dois eliminados após resolver ressurreições do tick. |
| Desconexão | Terminar a sessão com resultado parcial e mensagem clara. Sem reconexão ou migração de host nesta versão. |
| Início tardio | Não permitir entrar numa run em curso; apenas no lobby. |
| Dificuldade | +50% vida e +50% orçamento normal de inimigos no co-op; limites de ativos e orçamento mantêm-se. Detalhes na secção de gameplay. |

Não usar sincronização por seed/lockstep: diferenças de input, tempo, ordem de colisões
e RNG não devem transformar o cliente numa segunda autoridade da simulação.
TCP é a escolha de simplicidade para esta primeira versão LAN, não uma promessa de
latência ideal em redes com perdas. Não acrescentar UDP ou bibliotecas de rede sem
evidência de que o transporte escolhido falha os critérios definidos abaixo.

## Fluxo de interface

### Menu

Manter Play Solo e Shop e acrescentar **Start Hosting** e **Join Game**.
Todos os menus continuam a suportar WASD, Espaço, setas e Enter; campos de IP precisam
de modo explícito de edição, para escrever letras/teclas não disparar ações do menu.

### Host

1. Start Hosting cria o listener e abre o lobby, sem bloquear o desenho.
2. Mostrar nome da sessão, endereços LAN, porta e estado “Waiting for player”.
3. Em PCs com várias interfaces, listar opções, identificando loopback separadamente;
   permitir escolher/copiar o endereço correto. Não depender de serviços na Internet para obter o IP.
4. Host escolhe mapa e a sua arma; cliente escolhe a sua arma. Mostrar os dois loadouts e Ready.
5. Alterar mapa/loadout remove o Ready necessário. Só o host vê **Start Match**, ativo com os dois prontos.
6. Ao iniciar, enviar estado inicial e esperar confirmação de carregamento do cliente
   antes de começar a contagem de 3 segundos.

### Cliente

1. Join Game mostra campo IP:porta, Connect e Back. Porta omitida usa 47632.
2. Mostrar “Connecting…” com Cancel. Timeout de ligação/handshake: 5 segundos cada.
3. Mensagens específicas: endereço inválido, ligação recusada, timeout, sessão cheia,
   partida em curso, versão incompatível, host saiu.
4. Após o handshake, entrar no lobby e escolher apenas armas compradas no perfil local.
5. Back/Cancel fecha a ligação e devolve ao menu; não deixar sockets ou threads pendurados.

## Arquitetura a adaptar no código atual

O jogo atual está centrado em `World.player`: isso afeta combate, câmara, navegação,
pickups, progressão, efeitos e HUD. Não implementar multiplayer apenas desenhando uma
segunda personagem. Fazer a separação de responsabilidades antes de ligar a rede.

| Componente | Alteração esperada |
| --- | --- |
| `app.py` e estados | Coordenar sessão/lobby; continuar a bombear a rede em todos os ecrãs, incluindo pausa, cartas e game over. |
| `world/world.py` | `players` por player_id, mundo autoritativo, regras comuns e identificação do jogador local apenas na apresentação. |
| `player.py` | IDs estáveis e estado vivo/eliminado; não ler diretamente perfis ou sockets. |
| Progression/inventory | Uma instância por jogador, com filas e ofertas independentes. |
| CombatEffects/behaviors | Uma instância por jogador; burns, ecos, orbitais e buffs não podem consultar implicitamente o jogador do host. |
| Projéteis e efeitos | IDs de entidade estáveis, dono e autoria completa para dano, XP e arma do golpe final. |
| Inimigos/navegação | Seleção de alvo por jogador; remover pressuposto de uma única posição a perseguir. |
| HUD/PlayingState | Desenhar todos os jogadores, mas seguir e mostrar os stats do jogador local. |
| Build panel/augments | Mostrar o inventário local; visualizar o colega e estado de pausa/Ready de cada um. |
| Perfil/loja | Cada processo continua a guardar apenas o perfil local. |
| Serialização | DTOs explícitos de dados primitivos, separados dos objetos de simulação e dos sprites. |

Estrutura sugerida, ajustável ao código real:

```text
src/boxhead/network/
  protocol.py       # envelopes, framing, schemas, versão
  transport.py      # sockets não bloqueantes, buffers, ligações
  session.py        # lobby, estados de sessão, heartbeat, mensagens
  replication.py    # snapshots, deltas e estado de apresentação do cliente
```

O host usa a mesma via de comandos de gameplay que o cliente, sem passar o input local
pelo socket. O cliente não executa IA, RNG de combate, dano, drops ou progressão real.
Pode prever movimento e efeitos visuais, mas não conceder recompensas ou confirmar acertos.
Manter `World.player` como compatibilidade temporária só se não esconder bugs de autoria.
O single-player deve usar a mesma lógica com um único jogador e sem listener/socket.

## Transporte e protocolo

- Usar sockets não bloqueantes com `selectors` e buffers de leitura/escrita. Nunca executar
  `accept`, `connect`, `recv` ou `sendall` bloqueantes no ciclo de desenho.
- Frames: comprimento de 4 bytes unsigned big-endian, seguido de JSON UTF-8.
- Um `recv` pode trazer parte de uma mensagem ou várias: acumular e extrair corretamente.
  Escritas também podem ser parciais; reter o resto do buffer.
- Ativar TCP_NODELAY para comandos pequenos. Não alterar opções do sistema globalmente.
- Limites iniciais: 1 MiB por mensagem, 8 KiB para comandos recebidos do cliente e
  4 MiB de dados de saída pendentes por ligação; tornar estes valores configuráveis.
- Se um snapshot completo exceder 1 MiB, dividir por chunks com snapshot_id,
  chunk_index/chunk_count; aplicar atomicamente quando estiver completo.
- Esses limites são de transporte/memória, não caps de stats, projéteis ou augments.
- Validar tipo, comprimento, enums, IDs e números finitos. Rejeitar NaN/Infinity,
  inputs fora de intervalo e mensagens que não são válidas no estado da sessão.
- Não usar pickle, eval, paths enviados pelo cliente, objetos Python arbitrários ou
  transmissão do ficheiro de perfil. Assets já existem nos dois executáveis.
- Mensagens têm protocol_version, type, sequence e payload; eventos de run incluem session_id/run_id.
- Handshake inclui versão do protocolo, versão de build e hash determinístico do
  catálogo/regras/assets relevantes. A versão 0.1.0 do pyproject, sozinha, não chega
  para identificar executáveis diferentes. Rejeitar incompatibilidade antes da run.
- O host atribui player_id; não confiar num ID escolhido pelo cliente para controlar outro jogador.

| Direção | Mensagens mínimas |
| --- | --- |
| Cliente → host | hello, lobby_loadout, ready, loaded, input_state, choose_augment, pause_request, pause_release, leave, ping/pong, result_ack |
| Host → cliente | welcome/reject, lobby_state, start_match, snapshot_full/delta, augment_offer, pause_state, match_result, session_closed, ping/pong |

Inputs contêm movimento normalizado, direção/estado de disparo, sequence e client_tick;
o host usa o seu relógio e valida velocidade/cadência/munição. Não aceitar posições finais,
damage, HP, moedas ou “matei este inimigo” como comandos válidos.
`choose_augment` refere offer_id e augment_id; o host verifica dono, escolha pendente,
oferta atual e elegibilidade antes de consumir. Mensagem repetida não aplica duas vezes.

### Backpressure e desconexões

- Antes de transmitir, substituir snapshots ainda não enviados por um estado mais recente
  apenas quando isso não quebrar a base dos deltas. Não remover bytes de um frame parcialmente enviado.
- Deltas referem base_snapshot_id; manter como base o estado realmente confirmado pelo cliente,
  ou enviar um completo. Cliente com base desconhecida pede ressincronização.
- Acrescentar snapshot_ack e request_full ao protocolo para essa confirmação/recuperação.
- Eventos visuais podem ser deduplicados pelo event_id e descartados se obsoletos;
  escolhas, drops existentes, mortes e resultados fazem parte do estado durável replicado.
- Se não conseguir escoar a ligação, mostrar problema de rede e terminar por timeout,
  sem deixar o mundo acumular memória indefinidamente nem impor um teto de projéteis ao jogador.
- Heartbeat a cada 1 segundo; mostrar aviso após 3 segundos sem mensagens e terminar
  após 10 segundos. Heartbeat usa tempo real monotónico, mesmo com a simulação pausada.
- No host, se não chegar input novo por 250 ms durante combate, limpar movimento/disparo
  daquele jogador. Não continuar a disparar ou andar com uma tecla que ficou presa.

## Estado replicado e apresentação

O cliente precisa de estado suficiente para desenhar a partida e todos os menus:

- Jogadores: IDs, posição, orientação, animação, HP, raio/tamanho, arma, munição,
  stats efetivos, augments/stacks, XP/nível, buffs temporários, cargas e estado eliminado.
- Inimigos: IDs/tipo, posição/orientação, HP/max HP, estado/animação, elite/prismatic/boss,
  alvo atual e progresso de preparação do ataque.
- Projéteis: IDs, posição, velocidade, sprite, crítico, dono e parâmetros visuais.
- Terreno: mapa/seed, chunks visíveis, barris destruídos e danificados. Cliente nunca
  decide recriar barris destruídos ao voltar a um chunk.
- Pickups: IDs, posição, TTL e estado de recolha.
- FX: evento/ID, tipo, posição, raio e instante/duração, sem reenviar e reiniciar animações a cada snapshot.
- Ronda/fase, spawns pendentes, kills, moedas da equipa e motivo/estado da pausa.
- Apenas as ofertas pendentes do destinatário precisam de lhe ser enviadas em detalhe.

Projetar o snapshot com dados dinâmicos necessários, não serializar o `World` inteiro.
O cliente carrega as definições partilhadas pelo ID do catálogo verificado no handshake.
IDs removidos desaparecem também do estado do cliente. Interpolação nunca altera o estado
autoritativo, inventários ou recompensas.

Prever só movimento local inicialmente, com as colisões conhecidas. Reconciliar pela última
sequência confirmada e reaplicar inputs não confirmados; suavizar correções pequenas e
aplicar imediatamente correções grandes/teletransportes. Não prever drops, mortes ou compras.
Interpolar inimigos, colega e projéteis com o mesmo relógio de snapshots; não avançar balas
através de paredes por extrapolação ilimitada. Mostrar ping e aviso de ligação instável.

## Gameplay com dois jogadores

### Jogadores, alvo e autoria

- Cada jogador escolhe arma própria e leva os stats permanentes do seu perfil. Enviar
  apenas níveis de melhorias e arma selecionada; host valida IDs/limites e recalcula stats.
  A propriedade das compras é confiada entre amigos nesta versão, não existe backend anti-cheat.
- Inimigos escolhem o jogador vivo mais próximo, revendo a escolha a cada 0,25 s;
  mudar só se o novo alvo estiver pelo menos 15% mais perto, exceto se o anterior morreu.
- Preparações de ataques guardam o target_id. Se morrer, cancelar/reavaliar a preparação;
  não transformar um golpe preparado num teletransporte do dano para o outro jogador.
- Projéteis hostis atingem o primeiro jogador vivo no caminho; o limite de 49% usa a vida
  máxima de quem é atingido. O boss continua letal, sujeito ao Last Spark desse jogador.
- Spawn de inimigos respeita distância de segurança dos dois jogadores vivos.
- Guardar owner_player_id, weapon_id e source_kind em dano direto, queimadura, eco,
  orbital, explosão e encadeamentos. Nunca atribuir kills do cliente à arma ativa do host.
- Ricochetes excluem IDs já atingidos e não escolhem jogadores como alvo.
- Rupture Rounds não causa friendly fire direto, mas pode detonar um barril, que atinge ambos.

### Builds, XP, moedas e munições

- Cada morte dá XP base a ambos; aplicar o multiplicador individual uma vez. Também
  acumular XP para o jogador eliminado, para não ficar permanentemente para trás.
- Aqui, XP base significa a recompensa final do inimigo, já com os bónus de elite/boss
  aplicáveis, antes do multiplicador pessoal de XP. Não perder esses bónus na divisão.
- Guardar dois inventários/Progression/CombatEffects. Não aplicar um augment a ambos.
- Boss/Prismatic concede uma escolha roxa a cada jogador, independentemente do golpe final.
- Fim de ronda concede a cada um uma escolha cinzenta para a sua arma fixa da run.
- Continuar a usar os pesos atuais no level-up; RNG e ofertas são geridos pelo host.
- Moedas de inimigos são a recompensa da equipa: cada perfil recebe o total integral,
  não metade. Não aplicar créditos por cada snapshot nem por cada mensagem de resultado repetida.
- Uma caixa abastece os dois arsenais, mesmo se o colega estiver longe/eliminado.
  Se ambos estiverem cheios, fica no chão. Duas recolhas no mesmo tick consomem só uma caixa.
- Loja permanente apenas fora da run; não permitir alterar os níveis a meio da sessão.

### Pausa e cartas

- Pedidos de pausa são estados por jogador, não um simples toggle. Abrir Escape marca
  pause_requested[player_id]; fechar liberta apenas o pedido desse jogador.
- A partida só avança se não houver pedidos manuais nem escolhas pendentes de ninguém.
- Escolhas pendentes abrem o menu individual; quem terminou vê a sua build e “Waiting
  for teammate”. Nenhum relógio de escolha obrigatório nesta primeira versão.
- Host continua a validar escolhas e a bombear rede com o mundo congelado. Não depender
  do `PlayingState.update()` para fazer polling da sessão.
- Não abrir uma carta de jogador eliminado como condição para ressuscitar: pode escolher
  enquanto espectador/pausado e reaparecer depois com a build atualizada.
- Limpar inputs ao pausar/retomar para evitar disparos acumulados e seleções acidentais.
- Escape durante escolha de carta abre o build panel e, ao fechar, volta à mesma oferta.
- Sempre mostrar quem está a pausar/escolher; não deixar o outro ver apenas um jogo congelado.

### Morte e espectador

- Resolver Last Spark de cada jogador no fim da fase de dano, como no solo. Não terminar
  a equipa antes de consumir as ressurreições disponíveis daquele tick.
- Sem cargas, jogador fica eliminado: não ataca, não se move, não é alvo nem bloqueia spawns.
  Mostra “Waiting for next round”, build própria e segue o colega com a câmara.
- Na ronda seguinte, reaparece perto do colega, com posição válida para o seu raio,
  50% HP, sem restaurar Last Spark ou munição. Se o mundo estiver pausado por escolhas,
  reanimar apenas na transição autoritativa de ronda, sem avançar combate.
- Se não houver posição válida no anel próximo por obstáculos/tamanho, procurar mais
  longe dentro da zona jogável; não deixar o jogador dentro de paredes ou fora do mapa.
- Os dois eliminados sem ressurreições encerram a run; ambos recebem resultado e acesso a Return to Lobby.

### Dificuldade co-op

- Multiplicar por 1,5 a vida final de inimigos básicos, vermelhos, elites, Prismatics e bosses.
  Preservar as fórmulas por ronda e multiplicadores entre bosses; aplicar o bónus uma vez.
- Barris têm a vida do básico normal correspondente já com este bónus; explosão dos
  barris continua a usar a regra atual e limite de dano por jogador.
- Orçamento normal = min(limite atual, round(orçamento solo × 1,5)). Aplicar depois as
  regras de escolta/boss/Prismatic, garantindo um único boss e um único Prismatic quando previsto.
- Manter o máximo de 50 inimigos simultâneos e o cap atual de orçamento. Não duplicar
  entidades só porque há duas câmaras.
- Não multiplicar dano/cadência inimiga adicionalmente nesta primeira versão.
- Todos estes multiplicadores são específicos de co-op; solo conserva o balanceamento atual.

## Mapas e câmaras

- Cada cliente tem câmara e HUD próprios. Mostrar barra/nome/color do colega e uma seta
  quando está fora do ecrã, distinguível das setas dos últimos inimigos.
- No mapa infinito, carregar no host a união dos chunks necessários aos dois jogadores;
  não usar só `world.player.position` para gerar ou descarregar terreno.
- Reposicionar inimigos distantes apenas se estiverem longe de todos os jogadores vivos,
  nunca remover inimigos que um dos dois ainda está a combater.
- Escolher chunks de interesse por cliente para replicação, mas manter IDs e autoridade
  globais. Não eliminar um inimigo globalmente porque ficou fora da câmara de um cliente.
- Não descartar projéteis, burns, ecos ou pickups por referência exclusiva à área do host.
- O mapa infinito faz parte do resultado final. Pode ser a última fase, mas não marcar
  o modo completo com a opção visível e quebrada.

## Persistência e encerramento

- Cada sessão tem session_id; cada run tem run_id. Uma segunda partida no mesmo lobby
  recebe um run_id novo. Retry de uma mensagem não cria uma run nova.
- Resultados têm result_id composto por run_id + recipient_player_id e valor absoluto
  de moedas. Reutilizar a persistência idempotente do perfil para creditar uma única vez.
- Em fim normal, o host envia match_result, cliente guarda e responde result_ack.
  Reenvios não duplicam saldo; não confiar em confirmação apenas visual.
- Em desconexão, o host finaliza o parcial autoritativo. O cliente finaliza uma única
  vez com o total de moedas do último estado confirmado, nunca inventando recompensas futuras.
  É aceitável perder as últimas moedas ainda não recebidas se o host desaparecer abruptamente.
- Guardar só o resultado do utilizador local. Não sobrescrever o save do cliente com o do host.
- Sair do lobby/run fecha os sockets. Falha de gravação mostra aviso e usa a fila de
  retry já existente; não creditar outra vez ao regressar ao menu.
- Sem reconexão a meio nem migração de host: deixar essas funcionalidades explícitas como futuras.

## LAN, diagnóstico e execução

- Explicar no lobby que os dois PCs precisam de se alcançar na rede local. Mesmo Wi-Fi
  não garante isso se for rede de convidados/isolamento de clientes.
- Mostrar instrução para permitir o jogo na rede privada na firewall do Windows quando
  aparecer o pedido. Não desligar a firewall nem criar exceções globais automaticamente.
- Não pedir port forwarding; não usar IP público, matchmaking, contas, cloud ou Dropbox como transporte.
- Para testes no mesmo PC: host em 127.0.0.1 e dois diretórios de perfil temporários
  independentes via BOXHEAD_HOME; escolher também portas diferentes para sessões simultâneas.
- Criar modo/log de diagnóstico opcional com estado da ligação, RTT, Hz de snapshots,
  bytes/s, tamanho das filas e motivo do último disconnect. Não pôr detalhes técnicos nos botões normais.

## Plano de implementação

1. Criar branch `feat/lan-coop`, preservando alterações locais existentes.
2. Refatorar estado por jogador e autoria; verificar solo com todos os augments atuais.
3. Implementar framing, transportes não bloqueantes, handshake e testes de mensagens parciais.
4. Criar Host/Join/lobby e duas personagens nas arenas limitadas.
5. Replicar combate completo, efeitos, inimigos, projéteis, barris e pickups.
6. Sincronizar rondas, escolhas, pausa, espectador, resultados e saves.
7. Adicionar mapa infinito com união de chunks e interesse por cliente.
8. Suavizar movimento, testar congestionamento/desconexões e preparar pacote Windows novo.

Cada fase pode ter commits próprios, mas completar o fluxo todo antes de declarar o modo pronto.
Não gerar um executável co-op que tente juntar-se ao ZIP antigo: versões diferentes são incompatíveis.

## Critérios de aceitação e testes

- Dois processos conseguem Host → Join por IP → Ready → Start Match sem comandos de terminal.
- Dois PCs na mesma LAN conseguem o mesmo fluxo com o executável, sem Python instalado.
- Cliente não bloqueia menus ao ligar a um IP inacessível; Cancel/Back funciona.
- Versões diferentes, terceiro jogador, porta ocupada e entrada tardia recebem mensagens claras.
- Movimento simultâneo, disparo e colisões são consistentes; inimigos perseguem os dois.
- XP, moedas e escolhas são atribuídos corretamente, sem duplicar kills ou recompensas.
- Testar boss + Prismatic na mesma ronda: cada jogador recebe as duas ofertas roxas.
- Testar todas as cartas novas com um jogador e com os dois: críticos/overflow,
  Split Chamber, Ember Rounds, Blast Bloom, Slipstream Feed, Last Spark, Siege Frame,
  Redline, Aftershot, Rupture Rounds, Ricochet, Chain Reaction e orbitais.
- Dano secundário conserva autoria e regras anti-recursão; ao escolher uma carta no
  cliente, os stats do host não mudam. Morte por burn do cliente credita a arma certa.
- Uma caixa recolhida no mesmo tick pelos dois não duplica recolhas nem bloqueia a partida.
- Pausa manual e escolhas simultâneas congelam só a simulação, não a rede/heartbeat.
- Last Spark evita a eliminação; sem cargas, espectador volta na ronda seguinte;
  ambos mortos encerram a run uma única vez.
- Desligar o cliente/host, fechar a janela, arrancar o cabo e perder Wi-Fi não deixam
  teclas presas, memória a crescer, ecrã congelado ou duplicação de moedas.
- Testar snapshots fragmentados/juntos, envios parciais, mensagens inválidas, delta sem
  base, evento repetido e perda do ACK do resultado.
- Testar mapa infinito com jogadores a afastarem-se e voltarem, barris destruídos e
  inimigos perto de um jogador mas longe do outro.
- Testar 50 inimigos e builds com muitos projéteis; medir filas, RTT e bytes/s.
  Meta de referência: 60 FPS de apresentação e input-to-visible local abaixo de 100 ms
  numa LAN saudável, no PC de desenvolvimento. Reportar medições, não prometer estes valores sem testar.
- Os testes de regressão atuais de solo continuam a passar; usar perfis temporários.
- No fim, documentar limitações reais e distinguir testes locais de testes efetivamente
  feitos em dois PCs. Se só houver um PC disponível, entregar a build, os testes de dois
  processos e um roteiro para a verificação LAN; não afirmar que dois PCs foram testados.

## Fora do âmbito inicial

Internet/NAT traversal, Steam, contas, matchmaking, servidor dedicado, reconexão,
migração de host, quatro jogadores, chat, voice chat e sincronização de perfis na cloud.
Não acrescentar estas dependências para resolver um jogo LAN de dois amigos.

## Referências técnicas

A arquitetura e os valores acima são decisões propostas para este projeto.
As fontes abaixo suportam os detalhes de transporte e configuração da firewall:

- [Python 3.12 — Socket Programming HOWTO: mensagens parciais e sockets não bloqueantes](https://docs.python.org/3.12/howto/sockets.html)
- [Python 3.12 — selectors](https://docs.python.org/3.12/library/selectors.html)
- [Microsoft — Windows Firewall e perfis privados/públicos](https://learn.microsoft.com/windows/security/operating-system-security/network-security/windows-firewall)
