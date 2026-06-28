# API esperada

Todos os endpoints ficam sob `/api/` e retornam JSON.

## Cápsulas

- `GET /api/capsules/`: lista cápsulas.
- `POST /api/capsules/`: cria cápsula.
- `GET /api/capsules/{id}/`: detalha cápsula.
- `PATCH /api/capsules/{id}/`: atualiza cápsula.
- `GET /api/capsules/{id}/timeline/`: linha do tempo de transições da cápsula, em
  ordem cronológica (ver `BR-007`).

Filtros esperados:

- `status`
- `rarity`

As listagens devem ser paginadas e aceitar ordenação configurável (ver `BR-008`).

## Reservas

- `POST /api/reservations/`: cria reserva.
- `POST /api/reservations/{id}/checkout/`: retira cápsula.
- `POST /api/reservations/{id}/return/`: devolve cápsula.

## Inspeções

- `POST /api/quality-checks/`: registra inspeção.

## Perfis

- `GET /api/profiles/`: lista perfis.
- `POST /api/profiles/`: cria perfil (apenas curador).

Os perfis governam as permissões descritas em `BR-004`.

## Trilha de auditoria

- `GET /api/status-changes/`: lista as transições de status registradas.

A trilha é somente leitura: transições são criadas pelo sistema quando o status de
uma cápsula muda (ver `BR-005`) e não podem ser editadas ou removidas pela API.

## Relatórios

- `GET /api/reports/occupancy/`: ocupação do acervo — contagem de cápsulas por
  status (ver `BR-008`).

## Eventos externos

- `POST /api/webhooks/external-museum/`: recebe eventos de museus parceiros.

Eventos externos devem ser idempotentes por `source + event_id`.
