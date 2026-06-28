# BR-004 — Perfis e permissões

## Regra

Cada pessoa que opera a API tem um perfil que define o que pode fazer. Há três
perfis:

- **Curador**: responsável pelo acervo. Pode catalogar lotes e cápsulas, aposentar
  cápsulas e aprovar a saída de cápsulas raras ou únicas.
- **Técnico**: responsável pela conservação. Pode registrar inspeções de qualidade
  e mover cápsulas para quarentena.
- **Visitante**: público do museu. Pode consultar o acervo e criar reservas para
  sessões guiadas.

Leituras (`GET`) são liberadas para qualquer perfil. As escritas seguem o perfil.

## Estados relevantes

O perfil mora em `MuseumProfile`, associado a um usuário. Um usuário sem perfil é
tratado como visitante.

## Critérios de aceite

- Aposentar uma cápsula (mudar status para `retired`) só é permitido ao curador.
- Aprovar o checkout de uma cápsula rara ou única só é permitido ao curador.
- Registrar uma inspeção de qualidade só é permitido ao técnico.
- Criar uma reserva é permitido a qualquer perfil, inclusive visitante.
- Gerenciar perfis de outras pessoas só é permitido ao curador.
- Uma escrita feita por um perfil sem permissão deve ser rejeitada com `403`.
