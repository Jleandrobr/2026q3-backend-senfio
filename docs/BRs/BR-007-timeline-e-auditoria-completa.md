# BR-007 — Linha do tempo da cápsula e auditoria completa

> Esta regra descreve comportamentos ainda **não construídos**. Ela é a
> especificação de itens do backlog (`docs/TODO.md`): cobrir todas as transições
> na trilha, registrar quem provocou cada uma e expor a linha do tempo de uma
> cápsula. Aprofunda a BR-005.

## Regra

A trilha de auditoria (`StatusChange`, ver BR-005) precisa ser **completa** e
**consultável**. Completa: toda transição de status de cápsula deixa rastro, não
importa por qual caminho aconteceu. Consultável: é possível pedir à API a linha
do tempo de uma cápsula e reconstruir sua vida no acervo em ordem.

### Cobertura total

Toda mudança de status de cápsula gera um registro na trilha, incluindo as que
hoje passam sem rastro:

- reserva criada (`available -> reserved`);
- checkout (`reserved -> checked_out`);
- expiração de reserva (`reserved -> available`);
- devolução sem dano (`checked_out -> available`);
- quarentena por inspeção reprovada;
- quarentena por evento externo;
- aposentadoria (`-> retired`).

O ponto é **não** haver caminho de mudança de status que escape da trilha.

### Autoria da transição

Cada registro deve guardar **quem** provocou a transição, a partir do perfil
autenticado (ver BR-008), e não um texto solto. Uma transição sem autor
identificável é aceitável apenas quando o sistema a origina por conta própria
(por exemplo, a expiração automática), e nesse caso o autor deve deixar claro que
foi o sistema.

### Linha do tempo

A API deve expor a linha do tempo de uma cápsula:

- `GET /api/capsules/{id}/timeline/`: lista as transições da cápsula em ordem
  cronológica, permitindo reconstruir seu histórico.

## Estados relevantes

Os status de cápsula são os de BR-001. A trilha permanece **imutável** (BR-005):
esta regra amplia a cobertura e a consulta, não afrouxa a imutabilidade.

## Critérios de aceite

- Dado qualquer caminho que mude o status de uma cápsula, quando ele executar,
  então uma transição correspondente deve existir na trilha.
- Dado uma sequência de transições numa cápsula, quando a linha do tempo for
  consultada, então elas devem vir em ordem cronológica.
- Dado uma transição provocada por um perfil autenticado, quando registrada,
  então o autor deve identificar esse perfil.
- Dado uma transição originada pelo próprio sistema (ex.: expiração automática),
  quando registrada, então o autor deve indicar que foi o sistema.
- Dado uma cápsula sem transições, quando a linha do tempo for consultada, então
  a resposta deve ser uma lista vazia (e não um erro).
