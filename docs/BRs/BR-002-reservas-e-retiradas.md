# BR-002 — Reservas, retirada e devolução

## Regra

Reservas controlam o uso de cápsulas em sessões guiadas.

## Critérios de aceite

- Ao criar uma reserva válida, a cápsula deve mudar para `reserved`.
- Uma reserva só pode ser retirada enquanto estiver `pending`.
- Se o prazo de retirada expirar, a reserva deve mudar para `expired` e a cápsula deve voltar para `available`.
- Cápsulas raras ou únicas exigem aprovação manual antes do checkout (a aprovação é do curador — ver BR-004). **
- Ao devolver uma cápsula sem dano, a reserva deve mudar para `returned` e a cápsula para `available`.
- Ao devolver uma cápsula com dano, a cápsula deve ir para `quarantine` e uma inspeção deve ser registrada.
