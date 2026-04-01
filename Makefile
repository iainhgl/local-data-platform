.PHONY: help start stop run-pipeline open-docs install profiles init-duckdb

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

start: ## Start all services for the active COMPOSE_PROFILES
	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
	@echo "▶  Starting profile: $$(grep -E '^COMPOSE_PROFILES=' .env | cut -d= -f2)"
	@docker compose up -d
	@$(MAKE) init-duckdb

init-duckdb: ## Initialise the local DuckDB file with required schemas
	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
	@dbt run-operation ensure_quarantine_schema
	@echo "✔  Ensured DuckDB schema exists: quarantine"

stop: ## Stop all running services
	@docker compose down

run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test
	@echo "Pipeline implementation in Story 2"

open-docs: ## Open dbt docs and Elementary dashboard in browser
	@echo "Implementation in Story 2"

install: ## Install dbt packages (dbt deps)
	dbt deps

profiles: ## Show profiles and RAM requirements (simple/postgres: 8 GB; lakehouse/full: 16 GB)
	@echo ""
	@echo "Available profiles (set COMPOSE_PROFILES in .env):"
	@echo ""
	@echo "  simple    — DuckDB + Lightdash + Evidence + dbt docs + Elementary"
	@echo "              Minimum RAM: 8 GB"
	@echo ""
	@echo "  postgres  — simple profile + Postgres data warehouse"
	@echo "              Minimum RAM: 8 GB"
	@echo ""
	@echo "  lakehouse — postgres profile + MinIO + Trino (Iceberg)"
	@echo "              Minimum RAM: 16 GB"
	@echo ""
	@echo "  full      — lakehouse profile + Airflow + OpenMetadata + Prometheus"
	@echo "              + Grafana + Keycloak + Superset + MCP Server"
	@echo "              Minimum RAM: 16 GB"
	@echo ""
