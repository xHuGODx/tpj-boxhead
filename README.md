# TPJ · Boxhead

Survival shooter para Tópicos de Programação para Jogos: inspirado em Boxhead,
com rondas infinitas, bosses periódicos, augments de partida e uma loja de
melhorias permanentes inspirada em Vampire Survivors.

A direção visual usa sprites próprios (custom sprites), criados para o projeto,
com identidade visual consistente entre jogador, inimigos, armas e cenários.

O objetivo académico é demonstrar OOP, responsabilidades claras, baixo acoplamento
e padrões de desenho aplicados a problemas concretos.

## Estado atual

Setup inicial: pacote Python instalável, janela com ecrã inicial, Game Loop
e State/StateMachine.
O combate, os mapas e a progressão estão planeados nas issues; ainda não são jogáveis.

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
├── __main__.py       # CLI e arranque
├── app.py            # Composição, eventos SDL e Game Loop
├── config.py         # Configuração imutável da janela
├── core/state.py     # Contrato State e gestor do ciclo de vida
└── states/menu.py    # Ecrã inicial
docs/                # Design, arquitetura e backlog
.github/             # Templates de issues e PRs
```

Os módulos de gameplay serão criados quando as respetivas issues forem implementadas.

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
