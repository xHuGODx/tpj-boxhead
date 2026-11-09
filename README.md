# TPJ · Boxhead

Survival shooter para Tópicos de Programação para Jogos: inspirado em Boxhead,
com rondas infinitas, bosses periódicos, augments de partida e uma loja de
melhorias permanentes inspirada em Vampire Survivors.

O objetivo académico é demonstrar OOP, responsabilidades claras, baixo acoplamento
e padrões de desenho aplicados a problemas concretos.

## Estado atual

Setup inicial: pacote Python instalável, janela com ecrã inicial, Game Loop,
State/StateMachine, testes, lint, formatação e CI em Linux e Windows.
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

O `uv.lock` fixa o ambiente usado em desenvolvimento e CI. A alternativa com pip
instala as dependências declaradas, sem reproduzir necessariamente esse lock.

## Verificações

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
uv run --locked boxhead --headless --frames 10
```

O último comando abre e fecha a aplicação com o driver SDL dummy, sem precisar
de ecrã. Para aplicar a formatação: `uv run ruff format .`.

## Organização

```text
src/boxhead/
├── __main__.py       # CLI e arranque
├── app.py            # Composição, eventos SDL e Game Loop
├── config.py         # Configuração imutável da janela
├── core/state.py     # Contrato State e gestor do ciclo de vida
└── states/menu.py    # Ecrã inicial
tests/               # Contratos da FSM e encerramento da aplicação
docs/                # Design, arquitetura e backlog
.github/             # CI e templates
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
