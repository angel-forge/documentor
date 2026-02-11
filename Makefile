.PHONY: up down migrate reset-db lint format test test-int test-all

## ---- Docker ----

up: ## Start database container
	docker compose up -d

down: ## Stop database container
	docker compose down

## ---- Database ----

migrate: ## Run Alembic migrations
	uv run alembic upgrade head

reset-db: down ## Reset database (destroy volume, recreate, migrate)
	docker compose down -v
	docker compose up -d
	@echo "Waiting for database to be ready..."
	@until docker compose exec db pg_isready -U documentor -q; do sleep 1; done
	uv run alembic upgrade head

## ---- Quality ----

lint: ## Run linter
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

## ---- Tests ----

test: ## Run unit tests
	uv run pytest tests/unit/ -v

test-int: ## Run integration tests (needs Docker)
	uv run pytest tests/integration/ -v

test-all: ## Run all tests with coverage
	uv run pytest --cov=src/documentor -v

## ---- Help ----

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
