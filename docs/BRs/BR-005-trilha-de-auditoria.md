# BR-005 — Trilha de auditoria de cápsulas

## Regra

A vida de uma cápsula no acervo precisa ser reconstruível. Toda vez que o status
de uma cápsula muda, o museu registra a transição numa trilha de auditoria
(`StatusChange`): de qual status para qual status, quem provocou a mudança e por
quê.

A trilha é **histórica e imutável**: registros são criados quando a transição
acontece e nunca são editados ou removidos. Corrigir um engano significa registrar
uma nova transição, não apagar a anterior.

## Estados relevantes

Os status de cápsula são os de BR-001: `available`, `reserved`, `checked_out`,
`quarantine`, `retired`.

## Critérios de aceite

- Ao criar uma reserva, a transição `available -> reserved` deve ser registrada.
- Ao retirar uma cápsula (checkout), a transição `reserved -> checked_out` deve
  ser registrada.
- Ao mover uma cápsula para quarentena — por inspeção reprovada ou por evento
  externo — a transição para `quarantine` deve ser registrada.
- Ao aposentar uma cápsula, a transição para `retired` deve ser registrada.
- Nenhum registro da trilha pode ser alterado ou apagado depois de criado.
- A trilha de uma cápsula deve permitir reconstruir a ordem das transições.
