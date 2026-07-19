# BR-001 — Disponibilidade de cápsulas

## Regra

Uma cápsula só pode ser reservada quando estiver:

- dentro da validade;
- com status `available`;
- fora de quarentena;
- sem reserva ativa.

Uma cápsula tem **no máximo uma reserva ativa** por vez. Uma reserva é
considerada ativa enquanto estiver `pending` ou `checked_out`. Essa unicidade
precisa valer **mesmo sob concorrência**: dois pedidos de reserva para a mesma
cápsula chegando ao mesmo tempo não podem, os dois, ter sucesso.

## Estados relevantes

- `available`: pode ser reservada.
- `reserved`: há uma reserva pendente.
- `checked_out`: está em sessão.
- `quarantine`: bloqueada por inspeção ou evento externo.
- `retired`: removida do acervo ativo.

## Critérios de aceite

- Dado uma cápsula vencida, quando uma reserva for criada, então a API deve rejeitar a reserva.
- Dado uma cápsula em quarentena, quando uma reserva for criada, então a API deve rejeitar a reserva.
- Dado uma cápsula com reserva ativa, quando outra reserva for criada, então a API deve rejeitar a nova reserva.
- Dado duas requisições de reserva concorrentes para a mesma cápsula disponível, quando ambas forem processadas, então no máximo uma deve ter sucesso e a outra deve ser rejeitada. **
- Dado uma inspeção reprovada, quando ela for registrada, então a cápsula deve ir para quarentena. **
