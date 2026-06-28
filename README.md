# Museu de Cheiros Desaparecidos API

![Museu de Cheiros Desaparecidos](docs/assets/img/logo.png)

O **Museu de Cheiros Desaparecidos** é uma API fictícia para catalogar, preservar e emprestar cápsulas de cheiro de experiências que quase não existem mais: chuva em rua de paralelepípedo, cinema de bairro, biblioteca antiga, feira depois da chuva.

Este repositório é um **desafio técnico para Pessoa Desenvolvedora Python/Django Pleno**. Ele simula um projeto real em andamento: a documentação em `docs/` descreve o produto pretendido, a implementação cobre **parte** dele, e o que falta não vem sinalizado no código.

## Sua missão

Você acaba de entrar num time que mantém esta API. A documentação em `docs/` é a fonte de verdade do produto; o código é o que foi entregue até agora. **Nem tudo o que a documentação promete está implementado, e nem tudo o que está implementado cumpre a documentação.** Seu trabalho é:

1. **Entender o domínio** lendo o PRD e as regras de negócio (`BR-*`) em `docs/`.
2. **Confrontar documentação e código** — encontrar onde eles divergem. As divergências **não estão marcadas** no código (não há `# TODO`, não há comentário apontando o que falta): identificá-las faz parte da avaliação.
3. **Relatar o que encontrou** — um resumo do delta entre o pretendido e o real.
4. **Escolher alguns itens e trabalhá-los** — corrigir uma regra quebrada, completar um comportamento faltante ou construir algo novo a partir do backlog. Justifique por que escolheu esses e não outros.

Há também um backlog em `docs/TODO.md` com funcionalidades ainda **não construídas**: parte da sua missão pode ser tirar um item dali do papel, guiando-se pela regra de negócio correspondente.

**Não tente resolver tudo.** O escopo foi desenhado deliberadamente maior do que cabe numa entrega — priorizar é parte do desafio. Queremos avaliar como você:

- entende o domínio;
- lê criticamente a documentação e a confronta com o código;
- prioriza o que tem mais risco ou valor;
- escreve testes relevantes antes ou junto da mudança;
- implementa com simplicidade, sem inflar o escopo;
- explica decisões, trade-offs e o que deixou de fora — e por quê.

Não há resposta única esperada. Uma entrega pequena, bem justificada e testada vale mais do que muitas mudanças superficiais. O uso de IA é permitido; o que avaliamos é como você valida, revisa e responde pelo resultado.

## Como rodar

O banco é **PostgreSQL em qualquer situação** (dev, testes e CI) — não há SQLite.
O Postgres sobe via Docker, então **Docker é pré-requisito**. Você não precisa
instalar Postgres na máquina: o `make` cuida de subir os containers.

```bash
mise trust
make bootstrap
make ci-check
make run
```

O `mise trust` só é necessário na primeira execução, caso o `mise` peça confirmação para confiar no `mise.toml` do repositório.

- `make bootstrap` sobe o Postgres de desenvolvimento (`docker-compose.yml`, porta
  `54329`), roda migrations e seed.
- `make ci-check` roda os testes contra um Postgres **exclusivo de testes**
  (`dev.docker-compose.yml`, porta `54330`), efêmero: sobe, migra, testa e derruba
  sozinho a cada execução.

Endpoints principais ficam sob `/api/`.

## Estrutura

O código Django fica em `src/` (com o `manage.py`); a documentação e a configuração de projeto ficam na raiz.

- `src/config/`: configuração Django.
- `src/scents/`: app principal (modelos, serializers, views, permissões, seed).
- `src/tests/`: testes existentes.
- `docs/`: PRD, regras de negócio (`BR-*`), contrato de API, roadmap e enredo.

## Comandos úteis

- `make doctor`: verifica ferramentas básicas.
- `make bootstrap`: instala dependências, sobe o Postgres de dev, roda migrations e seed.
- `make up` / `make down`: sobe / derruba o Postgres de desenvolvimento.
- `make test`: sobe o Postgres de testes, roda a suíte e derruba o serviço ao final.
- `make ci`: formata, corrige lint e roda os testes (usa o Postgres de testes).
- `make ci-check`: checa formatação, lint e testes sem corrigir (usa o Postgres de testes).
- `make clean_db`: recria o banco de dev do zero, incluindo o volume Docker, e roda o seed.
- `make seed`: popula dados de exemplo.
- `make logs`: acompanha os logs do Postgres de desenvolvimento.

## Documentação

- `docs/HISTORIA.md`: enredo do museu — de onde veio, o que guarda, como cuida e sua missão (contexto de domínio).
- `docs/PRDs/PRD-001-catalogo-e-reservas.md`: produto e fluxos esperados.
- `docs/BRs/BR-001-disponibilidade-de-capsulas.md`: disponibilidade e quarentena.
- `docs/BRs/BR-002-reservas-e-retiradas.md`: reservas, retirada e devolução.
- `docs/BRs/BR-003-eventos-externos.md`: webhooks e idempotência.
- `docs/BRs/BR-004-perfis-e-permissoes.md`: perfis de operação e permissões.
- `docs/BRs/BR-005-trilha-de-auditoria.md`: trilha de auditoria das transições de status.
- `docs/BRs/BR-006-devolucao-e-expiracao.md`: devolução de cápsulas e expiração automática de reservas.
- `docs/BRs/BR-007-timeline-e-auditoria-completa.md`: linha do tempo da cápsula e cobertura total da trilha.
- `docs/BRs/BR-008-operacao-e-plataforma.md`: autenticação, permissões consistentes, integridade transacional e relatórios.
- `docs/API.md`: contrato esperado da API.
- `docs/TODO.md`: funcionalidades ainda não implementadas (roadmap).

> As BRs de 006 a 008 descrevem comportamentos ainda **não construídos** (ver
> `docs/TODO.md`). Elas são a especificação para quem quiser tirar um item do
> backlog do papel — a regra existe, o código ainda não.

## Entrega esperada

Inclua na sua entrega:

- resumo do que encontrou;
- TODOs escolhidos e por quê;
- mudanças implementadas;
- testes adicionados ou ajustados;
- o que ficou de fora e por quê.
