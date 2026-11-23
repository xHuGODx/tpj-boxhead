# TPJ · Boxhead

Survival shooter para Tópicos de Programação para Jogos: inspirado em Boxhead,
com rondas infinitas, bosses periódicos, augments de partida e uma loja de
melhorias permanentes inspirada em Vampire Survivors.

A direção visual usa sprites próprios (custom sprites), criados para o projeto,
com identidade visual consistente entre jogador, inimigos, armas e cenários.

O objetivo académico é demonstrar OOP, responsabilidades claras, baixo acoplamento
e padrões de desenho aplicados a problemas concretos.

## Estado atual

Há duas arenas limitadas e um mapa infinito com jogador animado, três armas, dois inimigos, boss,
rondas, XP, augments e loja permanente. Menu, pausa, seleção e game over estão
ligados; o resultado da partida é imutável e as recompensas são gravadas uma vez.
Os sprites fornecidos estão integrados e incluídos no pacote instalável.
O menu permite escolher o mapa. Inimigos usam navegação local e estados explícitos
de ataque/recuperação/morte. Áudio e playtest final continuam pendentes.

## Executar

Requisitos: Python 3.12 e [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/xHuGODx/tpj-boxhead.git
cd tpj-boxhead
uv sync --locked
uv run boxhead
```

Também existe o ponto de entrada `uv run python -m boxhead`. No ecrã inicial,
**Esc** ou fechar a janela termina a aplicação.

Sem uv, dentro de um ambiente virtual Python 3.12:

```bash
python -m pip install -e .
python -m boxhead
```

O `uv.lock` fixa o ambiente usado em desenvolvimento. A alternativa com pip
instala as dependências declaradas, sem reproduzir necessariamente esse lock.

## Desenvolvimento

O foco da cadeira é a organização do código e a aplicação de padrões de desenho.
Este projeto usa verificações manuais simples, sem testes automatizados, lint
obrigatório ou CI/CD. Para conferir uma alteração, abrir o jogo e experimentar
a funcionalidade correspondente.

## Organização

```text
src/boxhead/
├── app.py            # Composição e navegação
├── core/             # FSM, comandos, eventos, geometria e catálogo
├── world/            # Partida, combate, rondas, progressão e resultado
├── presentation/     # HUD e desenho de sprites adicionais
├── states/           # Input e ecrãs
├── profile.py        # JSON e confirmação atómica de alterações
└── shop.py           # Compras e melhorias permanentes
assets/               # Manifest, spritesheets e recortes
```

Na seleção de mapa: A/D ou setas e Enter. Repetir conserva o mapa escolhido.
Controlos: WASD move, Espaço dispara, 1/2/3 troca de arma, Esc pausa,
M abandona a partir da pausa, F3 mostra hitboxes. Menu/loja usam W/S e Enter.

## Design e desenvolvimento

- [Regras do jogo e propostas ainda ajustáveis](docs/game-design.md)
- [Arquitetura e relação com os slides](docs/architecture.md)
- [Backlog e ordem de implementação](docs/backlog.md)
- [Como contribuir](CONTRIBUTING.md)
- [Issues no GitHub](https://github.com/xHuGODx/tpj-boxhead/issues)

Controlos planeados: **WASD** para mover e orientar; **Espaço** para disparar na
direção em que a personagem está virada. O rato não controla a mira.

Referências de ferramentas: [Pygame](https://pypi.org/project/pygame/) e
[projetos com uv](https://docs.astral.sh/uv/guides/projects/).
