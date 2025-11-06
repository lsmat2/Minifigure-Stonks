.PHONY: help up down logs rebuild db-shell redis-shell clean test format lint

# Detect which Docker Compose command to use (new: "docker compose", old: "docker-compose")
DOCKER_COMPOSE := $(shell docker compose version > /dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up:  ## Start all Docker services
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. Access:"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis: localhost:6379"

down:  ## Stop all Docker services
	$(DOCKER_COMPOSE) down

logs:  ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

rebuild:  ## Rebuild and restart services
	$(DOCKER_COMPOSE) up -d --build

db-shell:  ## Open PostgreSQL shell
	docker exec -it minifig_db psql -U minifig_user -d minifigure_stonks

redis-shell:  ## Open Redis CLI
	docker exec -it minifig_redis redis-cli

clean:  ## Stop services and remove volumes (WARNING: deletes all data)
	$(DOCKER_COMPOSE) down -v
	@echo "All data removed!"

test:  ## Run tests (once backend is created)
	cd backend && pytest

format:  ## Format code with black
	cd backend && black .

lint:  ## Lint code with ruff
	cd backend && ruff check .
