# Desenvolvimento

Código e identificadores em inglês; documentação, issues e explicações em português.
Usamos Python 3.12, Pygame e uv, como nos exercícios locais da cadeira.

## Fluxo

1. Escolher uma issue cujas dependências estejam concluídas.
2. Criar uma branch curta, por exemplo `feat/12-player-movement`.
3. Implementar um comportamento completo e verificável.
4. Experimentar a funcionalidade no jogo.
5. Abrir PR com a issue e uma descrição curta da alteração.

Não há atribuições de issues ou divisão por pessoa. As prioridades e dependências
servem para orientar a sequência de implementação.

## Organização do código

- Manter input, atualização e desenho separados.
- Usar composição para combinar comportamentos; herança quando houver um contrato comum real.
- Separar geometria e regras do mundo das superfícies, fontes e sons.
- Passar dependências explicitamente pelo construtor; evitar estado global mutável.
- Explicar cada padrão com o problema que resolve, em vez de acrescentar classes só pelo nome.
- Dados de configuração partilhados devem ser imutáveis; estado de cada entidade pertence à instância.
- Uma alteração de gameplay deve atualizar a documentação quando mudar regras públicas.

## Verificação manual

Para esta cadeira introdutória, o projeto dispensa testes automatizados, lint
obrigatório e CI/CD. Confirmar as alterações jogando os cenários relevantes,
sem exigir suites de testes ou relatórios formais.

## Assets

Os sprites são próprios, criados para o projeto. Guardar os ficheiros-fonte editáveis
e os exports, com autor, dimensões e organização das animações em `assets/README.md`.
Seguir a escala, paleta e convenções definidas na issue #21. Placeholders podem ser
usados durante o desenvolvimento até existir a arte correspondente.

Para outros recursos, como sons e fontes, registar origem, autor, licença/permissão
e alterações em `assets/README.md`.
