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

run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test → edr report
	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
	@echo "▶  Running ingestion (file source)..."
	@PYTHONPATH=. python ingest/dlt_file_source.py
	@echo "▶  Running ingestion (API source)..."
	@PYTHONPATH=. python ingest/dlt_api_source.py
	@echo "▶  Running dbt run..."
	@dbt run
	@echo "▶  Running dbt test..."
	@dbt test
	@echo "▶  Generating Elementary report..."
	@edr report --profiles-dir . --profile local_data_platform --target elementary
	@echo "✔  Pipeline complete — run make open-docs to view dashboards"

open-docs: ## Open dashboards: Lightdash (18000) Evidence (18010) dbt docs (18020) Elementary (18030)
	@echo "▶  Opening dashboards..."
	@open http://localhost:18000 2>/dev/null || xdg-open http://localhost:18000 2>/dev/null || echo "ℹ  Lightdash:   http://localhost:18000"
	@open http://localhost:18010 2>/dev/null || xdg-open http://localhost:18010 2>/dev/null || echo "ℹ  Evidence:    http://localhost:18010"
	@open http://localhost:18020 2>/dev/null || xdg-open http://localhost:18020 2>/dev/null || echo "ℹ  dbt docs:    http://localhost:18020"
	@open http://localhost:18030 2>/dev/null || xdg-open http://localhost:18030 2>/dev/null || echo "ℹ  Elementary:  http://localhost:18030"
	@echo "✔  Dashboards opened"

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
