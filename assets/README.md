# Assets

O scaffold usa formas/texto do Pygame e a fonte predefinida incluída na biblioteca.
Os sprites próprios e os sons ainda não estão implementados.

## Sprites próprios

A arte do jogo será criada para o projeto (custom sprites), incluindo jogador,
inimigos normal e vermelho, boss, armas/projéteis e elementos dos mapas. A produção
e integração estão definidas na [issue #21](https://github.com/xHuGODx/tpj-boxhead/issues/21).

- Definir escala, paleta e convenções de orientação/animação consistentes.
- Guardar ficheiros-fonte editáveis e exports PNG com transparência.
- Documentar dimensões de cada frame, ordem das animações e ponto de origem.
- Manter hitboxes e regras de combate independentes do desenho dos sprites.
- Usar placeholders enquanto os sprites correspondentes estiverem em produção.

Registar cada sprite ou spritesheet acrescentado:

| Recurso | Autor | Ficheiro-fonte | Export | Dimensões/animações |
| --- | --- | --- | --- | --- |

## Outros recursos

Para sons, fontes e outros recursos, registar a respetiva origem:

| Ficheiro | Origem | Autor | Licença/permissão | Alterações |
| --- | --- | --- | --- | --- |

Spritesheets e sons serão carregados através de um catálogo partilhado, independente
dos atributos das entidades. Manter nomes e caminhos consistentes nos mapas.
