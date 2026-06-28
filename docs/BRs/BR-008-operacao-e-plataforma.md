# BR-008 — Operação e plataforma

> Esta regra descreve comportamentos ainda **não construídos**. Ela reúne as
> preocupações transversais que sustentam o produto: autenticação e aplicação
> consistente de permissões, integridade das transições e recursos de operação
> (relatórios, notificação, paginação). Complementa a BR-004.

## Regra

### Autenticação e resolução de perfil

As permissões da BR-004 pressupõem saber **quem** faz cada requisição. A API
precisa de um mecanismo de autenticação que resolva a requisição para um
`MuseumProfile` (curador, técnico ou visitante). Uma requisição sem perfil
identificado é tratada como **visitante** — o menor privilégio.

O mecanismo pode ser simples (não é preciso login com senha nem sessão de UI),
mas precisa ser explícito e consistente: a mesma requisição, autenticada da mesma
forma, sempre resolve para o mesmo perfil.

### Aplicação consistente das permissões

As permissões da BR-004 valem para **todas** as escritas, não para algumas. Hoje
a infraestrutura de perfis existe, mas não está aplicada de forma uniforme. Toda
escrita sensível — aposentar cápsula, registrar inspeção, gerenciar perfis,
aprovar checkout de rara/única — deve exigir o perfil correto e rejeitar com
`403` quem não o tiver. Não pode haver escrita sensível aberta a qualquer um.

Um curador pode ainda **promover ou rebaixar** o perfil de outra pessoa; essa
operação é, ela mesma, restrita ao curador.

### Integridade das transições

Uma transição de negócio costuma tocar mais de um registro ao mesmo tempo: a
reserva **e** a cápsula, ou a cápsula **e** a trilha de auditoria. Essas mudanças
formam uma unidade: ou todas acontecem, ou nenhuma. Uma falha no meio do caminho
não pode deixar o sistema num estado inconsistente — por exemplo, a reserva
marcada como `checked_out` mas a cápsula ainda `reserved`, ou o status mudado sem
o registro correspondente na trilha.

### Recursos de operação

Para operar o acervo no dia a dia, a API deve oferecer:

- **Relatório de ocupação**: uma visão da quantidade de cápsulas por status
  (quantas `available`, `reserved`, `quarantine`, etc.).
- **Notificação de quarentena**: quando uma cápsula entra em quarentena, a
  curadoria deve ser avisada (o canal pode ser simples — o essencial é que a
  entrada em quarentena dispare o aviso).
- **Paginação e ordenação**: as listagens devem ser paginadas e permitir
  ordenação configurável, para não devolver o acervo inteiro de uma vez.

## Estados relevantes

- Perfis: `curator`, `technician`, `visitor` (ver BR-004).
- Status de cápsula: os de BR-001.

## Critérios de aceite

- Dado uma requisição sem perfil identificado, quando tentar uma escrita
  sensível, então deve ser tratada como visitante e rejeitada com `403`.
- Dado um técnico, quando tentar aposentar uma cápsula, então deve receber `403`
  (aposentar é do curador).
- Dado um visitante, quando tentar registrar uma inspeção, então deve receber
  `403` (inspeção é do técnico).
- Dado um curador, quando promover ou rebaixar o perfil de outra pessoa, então a
  operação deve ter sucesso; para qualquer outro perfil, deve receber `403`.
- Dado uma transição que toca reserva e cápsula, quando uma etapa falhar, então
  nenhuma das mudanças deve persistir (a operação é atômica).
- Dado uma mudança de status, quando ela persistir, então o registro na trilha
  também persiste — nunca um sem o outro.
- Dado o acervo, quando o relatório de ocupação for consultado, então deve
  retornar a contagem de cápsulas por status.
- Dado uma cápsula que entra em quarentena, quando a transição ocorrer, então a
  curadoria deve ser notificada.
- Dado uma listagem, quando consultada, então deve ser paginada e aceitar
  ordenação configurável.
