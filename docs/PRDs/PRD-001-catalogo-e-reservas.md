# PRD-001 — Catálogo e reservas de cápsulas de cheiro

## Contexto

O Museu de Cheiros Desaparecidos preserva cápsulas olfativas de experiências
culturais em desaparecimento. Visitantes podem reservar cápsulas para sessões
guiadas, desde que elas estejam disponíveis, válidas e fora de quarentena. A
operação é conduzida por uma equipe com perfis distintos — curadoria, técnica e
visitação — e toda mudança no acervo precisa deixar rastro.

## Objetivos

- Catalogar cápsulas e lotes de preservação.
- Permitir reservas para sessões.
- Controlar retirada e devolução.
- Registrar inspeções de qualidade.
- Governar quem pode fazer o quê por perfil.
- Manter uma trilha de auditoria das transições de status.
- Integrar eventos de museus parceiros.

## Escopo

- CRUD de lotes e cápsulas.
- Reservas, checkout e devolução.
- Inspeções de qualidade.
- Perfis e permissões de operação.
- Trilha de auditoria de status.
- Webhook de eventos externos.

## Regras de negócio relacionadas

- `BR-001` — disponibilidade de cápsulas.
- `BR-002` — reservas, retirada e devolução.
- `BR-003` — eventos externos e idempotência.
- `BR-004` — perfis e permissões.
- `BR-005` — trilha de auditoria.
- `BR-006` — devolução de cápsulas e expiração de reservas (a construir).
- `BR-007` — linha do tempo da cápsula e auditoria completa (a construir).
- `BR-008` — operação e plataforma: autenticação, permissões consistentes,
  integridade transacional e relatórios (a construir).

## Fora de escopo por enquanto

- Login com senha e sessão de UI (a BR-008 pede apenas um mecanismo simples que
  resolva a requisição para um perfil).
- Pagamento ou cobrança.
- Frontend.
- Integração real com museus externos.
