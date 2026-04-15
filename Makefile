.PHONY: help start stop run-pipeline pg-show-pii-log dbt-verify-contracts lightdash-ping build-evidence open-docs install profiles init-duckdb

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

run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test → dbt docs generate (edr + Evidence: simple profile only)
	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
	@set -a; . ./.env; set +a; \
	echo "▶  Running pipeline for profile: $$COMPOSE_PROFILES"; \
	echo "▶  Running ingestion (file source)..." && \
	PYTHONPATH=. python ingest/dlt_file_source.py && \
	echo "▶  Running ingestion (API source)..." && \
	PYTHONPATH=. python ingest/dlt_api_source.py && \
	echo "▶  Running dbt run..." && \
	dbt run && \
	if [ "$$COMPOSE_PROFILES" = "postgres" ]; then \
		echo "▶  Applying PII masking views (postgres profile)..."; \
		docker compose exec -T postgres psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" \
			-f /scripts/postgres_masking.sql; \
	fi && \
	echo "▶  Running dbt test..." && \
	dbt test && \
	echo "▶  Generating dbt docs..." && \
	dbt docs generate && \
	if [ "$$COMPOSE_PROFILES" = "simple" ]; then \
		echo "▶  Generating Elementary report..."; \
		mkdir -p edr_target; \
		DBT_DUCKDB_PATH="$$(pwd)/dev.duckdb" edr report --profiles-dir . --profile-target elementary && \
		$(MAKE) build-evidence; \
	else \
		echo "ℹ  Elementary (edr) and Evidence skipped for profile: $$COMPOSE_PROFILES (DuckDB-only components)"; \
	fi && \
	echo "✔  Pipeline complete — run make open-docs to view dashboards"

pg-show-pii-log: ## Show recent PII access log entries (postgres profile only)
	@test -f .env || (echo "❌  .env not found" && exit 1)
	@set -a; . ./.env; set +a; \
	if [ "$$COMPOSE_PROFILES" != "postgres" ]; then \
		echo "⚠  pg-show-pii-log requires COMPOSE_PROFILES=postgres (current: $$COMPOSE_PROFILES)" && exit 1; \
	fi; \
	docker compose exec -T postgres psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" \
	    -c "SELECT logged_at, role_name, schema_name, table_name FROM public.pii_access_log ORDER BY logged_at DESC LIMIT 20;"

dbt-verify-contracts: ## Compile Gold models to verify schema contract syntax (no DB required)
	dbt compile --select tag:gold

lightdash-ping: ## Check Lightdash is responding (postgres profile required)
	@curl -sf http://localhost:18000/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('status')=='ok' else 1)" && echo "✓ Lightdash healthy at http://localhost:18000" || echo "✗ Lightdash not responding — is the postgres profile running?"

build-evidence: ## Build Evidence analytical reports (runs on host — DuckDB WASM build requires macOS)
	@echo "▶  Building Evidence reports (host build)..."
	@cd evidence && npm install && npm run sources && npm run build
	@echo "✔  Evidence reports built — run 'docker compose up' to serve at http://localhost:18010"

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
