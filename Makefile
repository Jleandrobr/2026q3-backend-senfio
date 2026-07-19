.PHONY: bootstrap doctor ci ci-check up down logs run-docker clean_db test test-up test-down migrate seed run shell

PYTHON := uv run python
# O projeto Django vive em src/ (config, scents, tests e manage.py).
MANAGE := $(PYTHON) src/manage.py

# Postgres é o banco padrão em qualquer situação (dev, testes e CI).
# O serviço de dev fica em docker-compose.yml (porta 54329, com volume);
# o serviço de testes fica em dev.docker-compose.yml (porta 54330, efêmero via tmpfs).
TEST_COMPOSE := docker compose -f dev.docker-compose.yml
TEST_DB_URL := postgres://museum:museum@localhost:54330/museum_test

bootstrap:
	mise install
	uv sync --all-groups
	$(MAKE) up
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) doctor

doctor:
	@command -v mise >/dev/null || (echo "mise não encontrado" && exit 1)
	@command -v uv >/dev/null || (echo "uv não encontrado" && exit 1)
	@command -v docker >/dev/null || (echo "docker não encontrado" && exit 1)
	@command -v make >/dev/null || (echo "make não encontrado" && exit 1)
	@echo "Ambiente básico OK. Rode 'make bootstrap' se as dependências ainda não foram instaladas."

ci:
	uv run ruff format .
	uv run ruff check --fix .
	$(MAKE) test

ci-check:
	uv run ruff format --check .
	uv run ruff check .
	$(MAKE) test

up:
	docker compose up -d --wait db

down:
	docker compose down

logs:
	docker compose logs -f

# Sobe/derruba o Postgres exclusivo de testes (efêmero: os dados vivem em tmpfs).
test-up:
	$(TEST_COMPOSE) up -d --wait test-db

test-down:
	$(TEST_COMPOSE) down

# Sobe o banco de testes, roda a suíte (o pytest-django cria e migra o banco de
# teste automaticamente) e derruba o serviço ao final, com ou sem falha.
test: test-up
	@DATABASE_URL=$(TEST_DB_URL) uv run pytest --create-db; \
	status=$$?; \
	$(MAKE) test-down; \
	exit $$status

# Recria o banco de dev do zero, incluindo o volume Docker.
clean_db:
	docker compose down -v
	$(MAKE) up
	$(MAKE) migrate
	$(MAKE) seed

migrate:
	$(MANAGE) migrate

seed:
	$(MANAGE) seed

run:
	$(MANAGE) runserver

# Caminho alternativo ao `make run`: sobe a API dentro do Docker (serviço
# `web`, com live-reload via bind mount de src/) em vez de rodar via `uv run`
# local. `make down` derruba tudo.
run-docker:
	docker compose up -d --build web

shell:
	$(MANAGE) shell
