.PHONY: up down restart logs reset psql redis-cli qdrant-ui install fmt lint typecheck test ci test-db-create test-db-migrate test-db-setup

up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

restart: down up

logs:
	docker compose -f docker/docker-compose.yml logs -f

reset:
	docker compose -f docker/docker-compose.yml down -v
	docker compose -f docker/docker-compose.yml up -d

psql:
	docker exec -it sc-postgres psql -U shopping -d shopping

redis-cli:
	docker exec -it sc-redis redis-cli

qdrant-ui:
	@echo "Open http://localhost:6333/dashboard"

install:
	uv sync

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest -v

ci: lint typecheck test

# al final del Makefile
test-db-create:
	docker exec -it sc-postgres psql -U shopping -c "CREATE DATABASE shopping_test;" || echo "already exists"

test-db-migrate:
	POSTGRES_DSN="postgresql+asyncpg://shopping:shopping@localhost:5432/shopping_test" \
	  uv run alembic upgrade head

test-db-setup: test-db-create test-db-migrate
