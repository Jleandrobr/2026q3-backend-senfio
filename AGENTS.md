# Museu de Cheiros Desaparecidos API

## Stack

- Python 3.12 gerenciado por `mise`.
- Django 5 + Django REST Framework.
- `uv` para dependências e execução.
- **PostgreSQL em qualquer situação** (dev, testes e CI), sempre via Docker — não há SQLite.
  - Dev: `docker-compose.yml`, serviço `db`, porta `54329`, com volume persistente.
  - Testes: `dev.docker-compose.yml`, serviço `test-db`, porta `54330`, efêmero (dados em `tmpfs`).
- Pytest, pytest-django e Ruff.

## Comandos canônicos

- `make bootstrap`: instala dependências, sobe o Postgres de dev, roda migrations e seed.
- `make doctor`: verifica ferramentas sem instalar nada.
- `make ci`: formata/corrige lint e roda testes (usa o Postgres de testes).
- `make ci-check`: checa formatação, lint e testes sem corrigir (usa o Postgres de testes).
- `make up`: sobe o Postgres de desenvolvimento (serviço `db`).
- `make down`: derruba o Postgres de desenvolvimento.
- `make logs`: mostra logs do Postgres de desenvolvimento.
- `make test-up` / `make test-down`: sobe / derruba o Postgres exclusivo de testes.
- `make clean_db`: recria o banco de dev do zero (derruba o volume Docker), migra e seed.
- `make test`: sobe o Postgres de testes, roda a suíte (pytest-django cria/migra o banco de teste) e derruba o serviço ao final.
- `make migrate`: aplica as migrations no Postgres de dev.
- `make seed`: popula dados de exemplo.
- `make run`: sobe o servidor de desenvolvimento do Django.
- `make shell`: abre o shell do Django.

## Objetivo do repo

Este é um repositório de desafio técnico. Ele representa um produto Django/DRF em
andamento: a documentação em `docs/` descreve o produto pretendido e a
implementação cobre parte dele. O backlog em `docs/TODO.md` é maior do que o
escopo de uma entrega.

Não tente transformar o projeto inteiro. A avaliação busca leitura crítica,
priorização, testes relevantes e implementação simples.

## Estrutura

O código Django vive sob `src/`; a documentação e a configuração de projeto ficam na raiz.

- `src/`: projeto Django (contém `manage.py`).
  - `src/config/`: configuração Django.
  - `src/scents/`: app principal com modelos, serializers e views.
  - `src/tests/`: testes existentes, que cobrem parte do comportamento.
- `docs/PRDs/`: descrição funcional do produto.
- `docs/BRs/`: regras de negócio esperadas.
- `docs/TODO.md`: backlog maior que o escopo de uma entrega.
- Raiz: `Makefile`, `pyproject.toml`, `mise.toml`, `docker-compose.yml`, `dev.docker-compose.yml`.

## Convenções

- Prefira mudanças pequenas e fáceis de revisar.
- Toda correção de regra de negócio deve vir acompanhada de teste.
- Evite abstrações genéricas para um domínio pequeno.
- Se usar IA, revise criticamente e assuma a decisão técnica.
