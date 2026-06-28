# BR-003 — Eventos externos e idempotência

## Regra

Museus parceiros podem enviar eventos sobre cápsulas compartilhadas. O webhook deve ser idempotente por `source + event_id`.

## Critérios de aceite

- Dado um evento novo, quando recebido, então ele deve ser registrado e processado.
- Dado um evento repetido com mesmo `source + event_id`, quando recebido novamente, então a API deve retornar sucesso sem duplicar o evento.
- Dado um evento `capsule.quarantined`, quando recebido, então a cápsula referenciada deve ir para quarentena.
- Eventos com payload inválido devem retornar erro claro.
