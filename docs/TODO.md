# Roadmap — funcionalidades ainda não implementadas

Esta página lista funcionalidades planejadas para o produto que **ainda não foram
construídas**. É um backlog de produto, maior do que o escopo de uma entrega.
Escolha alguns itens, priorize e justifique.

> Esta lista descreve o que falta **construir**. Ela não é um checklist de
> correções: parte do trabalho é decidir o que vale a pena fazer e em que ordem.
> Cada bloco aponta a regra de negócio (`BR-*`) que o especifica.

## Catálogo e reservas — ver `BR-006`

- Endpoint de devolução de cápsula (`POST /api/reservations/{id}/return/`), com
  tratamento de devolução com e sem dano.
- Expiração automática de reservas não retiradas até o prazo, liberando a cápsula
  de volta para o acervo.
- Aprovação manual para checkout de cápsulas raras ou únicas (ver `BR-002`).
- Filtros de listagem de cápsulas por `status` e `rarity`.

## Eventos externos — ver `BR-003`

- Reprocessamento seguro de eventos de museus parceiros.
- Suporte a novos tipos de evento além de `capsule.quarantined`.

## Perfis e permissões — ver `BR-004` e `BR-008`

- Autenticação que resolva a requisição para um perfil.
- Aplicar as permissões de BR-004 a todas as escritas (catálogo, inspeções,
  aposentadoria de cápsulas).
- Vincular a reserva e a inspeção ao perfil que as realizou.
- Endpoint para um curador promover ou rebaixar o perfil de outra pessoa.

## Trilha de auditoria — ver `BR-005` e `BR-007`

- Cobrir todas as transições de status de cápsula na trilha.
- Registrar quem provocou cada transição a partir do perfil autenticado.
- Expor a linha do tempo de uma cápsula (`GET /api/capsules/{id}/timeline/`).

## Qualidade e operação — ver `BR-008`

- Garantir atomicidade das transições que tocam mais de um registro.
- Notificar a curadoria quando uma cápsula entra em quarentena.
- Relatório de ocupação do acervo por status (`GET /api/reports/occupancy/`).
- Paginação e ordenação configuráveis nas listagens.
