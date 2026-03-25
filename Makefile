.PHONY: help build up down restart logs migrate makemigrations superuser shell test lint flush collectstatic

COMPOSE = docker compose
BACKEND = $(COMPOSE) exec backend
MANAGE  = $(BACKEND) python manage.py

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Docker ──────────────────────────────────────────────────────

build: ## Build all Docker containers
	$(COMPOSE) build

up: ## Start all services in detached mode
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) down && $(COMPOSE) up -d

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

logs-backend: ## Tail backend logs
	$(COMPOSE) logs -f backend

logs-celery: ## Tail celery worker logs
	$(COMPOSE) logs -f celery_worker

logs-frontend: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

ps: ## List running containers
	$(COMPOSE) ps

# ─── Django ──────────────────────────────────────────────────────

migrate: ## Run Django migrations
	$(MANAGE) migrate --noinput

makemigrations: ## Create new Django migrations
	$(MANAGE) makemigrations

superuser: ## Create Django superuser
	$(MANAGE) createsuperuser

shell: ## Open Django shell (IPython)
	$(MANAGE) shell_plus

dbshell: ## Open database shell
	$(MANAGE) dbshell

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

flush: ## Flush database (destructive)
	$(MANAGE) flush --noinput

seed: ## Seed database with sample data
	$(MANAGE) loaddata fixtures/*.json

# ─── Testing ─────────────────────────────────────────────────────

test: ## Run backend tests
	$(BACKEND) pytest --cov=apps --cov-report=term-missing -v

test-app: ## Run tests for a specific app (usage: make test-app APP=accounts)
	$(BACKEND) pytest apps/$(APP) -v

# ─── Code Quality ────────────────────────────────────────────────

lint: ## Run linters (flake8, black check, isort check)
	$(BACKEND) flake8 .
	$(BACKEND) black --check .
	$(BACKEND) isort --check-only .

format: ## Auto-format code with black and isort
	$(BACKEND) black .
	$(BACKEND) isort .

# ─── Elasticsearch ───────────────────────────────────────────────

reindex: ## Rebuild Elasticsearch indices
	$(MANAGE) search_index --rebuild -f

# ─── Frontend ────────────────────────────────────────────────────

frontend-install: ## Install frontend dependencies
	$(COMPOSE) exec frontend npm install

frontend-build: ## Build frontend for production
	$(COMPOSE) exec frontend npm run build

frontend-lint: ## Lint frontend code
	$(COMPOSE) exec frontend npm run lint

# ─── Utilities ───────────────────────────────────────────────────

clean: ## Remove all containers, volumes, and images
	$(COMPOSE) down -v --rmi all --remove-orphans

prune: ## Remove dangling Docker resources
	docker system prune -f

env: ## Copy .env.example to .env
	cp .env.example .env
