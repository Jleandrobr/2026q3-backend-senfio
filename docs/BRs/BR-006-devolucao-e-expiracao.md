# BR-006 — Devolução de cápsulas e expiração de reservas

> Esta regra descreve comportamentos ainda **não construídos**. Ela é a
> especificação de dois itens do backlog (`docs/TODO.md`): o endpoint de
> devolução e a expiração automática de reservas. Complementa a BR-002.

## Regra

Uma reserva percorre um ciclo: é criada (`pending`), a cápsula é retirada
(`checked_out`) e, ao fim da sessão, a cápsula é **devolvida**. Quando a retirada
não acontece dentro do prazo, a reserva **expira** sozinha e a cápsula volta ao
acervo — sem depender de alguém tentar retirá-la.

### Devolução

A devolução encerra uma reserva `checked_out`:

- **Sem dano**: a reserva vai para `returned` e a cápsula volta para `available`.
- **Com dano**: a cápsula vai para `quarantine` e uma inspeção de qualidade
  (`QualityCheck`) é registrada para documentar o dano.

Só uma reserva em `checked_out` pode ser devolvida. Devolver uma reserva em
qualquer outro estado é um erro.

### Expiração automática

Se o prazo de retirada (`pickup_deadline`) passar e a cápsula não tiver sido
retirada, a reserva deve mudar para `expired` e a cápsula deve voltar para
`available`. Essa transição **não pode depender** de alguém chamar o checkout
depois do prazo: uma reserva vencida que ninguém tocou não pode ficar `pending`
para sempre, segurando a cápsula. Deve existir um processo (executável de forma
recorrente) que varre as reservas vencidas e as expira.

## Estados relevantes

- Reserva: `pending`, `checked_out`, `returned`, `expired`, `cancelled`.
- Cápsula: `available`, `reserved`, `checked_out`, `quarantine`, `retired`
  (ver BR-001).

## Critérios de aceite

- Dado uma reserva `checked_out`, quando for devolvida sem dano, então a reserva
  deve ir para `returned` e a cápsula para `available`.
- Dado uma reserva `checked_out`, quando for devolvida com dano, então a cápsula
  deve ir para `quarantine` e uma inspeção deve ser registrada.
- Dado uma reserva que não está `checked_out`, quando a devolução for solicitada,
  então a API deve rejeitar a operação.
- Dado uma reserva `pending` cujo prazo de retirada já passou, quando o processo
  de expiração rodar, então a reserva deve ir para `expired` e a cápsula para
  `available` — mesmo que ninguém chame o checkout.
- Dado uma reserva `pending` dentro do prazo, quando o processo de expiração
  rodar, então ela deve permanecer `pending`.
- Toda transição de status de cápsula provocada por devolução ou expiração deve
  ser registrada na trilha de auditoria (ver BR-005 e BR-007).
