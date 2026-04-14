#!/usr/bin/env python3
"""
dlt API source pipeline for local-data-platform.
Reads from JSONPlaceholder REST API and loads to bronze schema in DuckDB.

Usage:
    python ingest/dlt_api_source.py
    API_BASE_URL=https://jsonplaceholder.typicode.com DBT_DUCKDB_PATH=dev.duckdb python ingest/dlt_api_source.py
"""
import json
import os
import sys

import dlt
import duckdb
import requests

DEFAULT_API_BASE_URL = "https://jsonplaceholder.typicode.com"
DEFAULT_DUCKDB_PATH = "dev.duckdb"
COMPOSE_PROFILES = os.environ.get("COMPOSE_PROFILES", "simple")
TABLES = ["posts", "users"]


def get_api_base_url() -> str:
    return os.environ.get("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def get_duckdb_path() -> str:
    return os.environ.get("DBT_DUCKDB_PATH", DEFAULT_DUCKDB_PATH)


def _get_destination():
    if COMPOSE_PROFILES == "postgres":
        conn = (
            f"postgresql://{os.environ.get('POSTGRES_USER', 'dbt')}:"
            f"{os.environ.get('POSTGRES_PASSWORD', '')}@"
            f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
            f"{os.environ.get('POSTGRES_PORT', '18040')}/"
            f"{os.environ.get('POSTGRES_DB', 'local_data_platform')}"
        )
        return dlt.destinations.postgres(conn)
    return dlt.destinations.duckdb(get_duckdb_path())


def fetch_json(api_base_url: str, endpoint: str):
    response = requests.get(f"{api_base_url}/{endpoint}", timeout=30)
    response.raise_for_status()
    return response.json()


@dlt.source
def jsonplaceholder_source(api_base_url: str):
    @dlt.resource(name="posts", primary_key="id", write_disposition="merge")
    def posts():
        yield fetch_json(api_base_url, "posts")

    @dlt.resource(name="users", primary_key="id", write_disposition="merge")
    def users():
        yield fetch_json(api_base_url, "users")

    yield posts()
    yield users()


def _verify_counts(duckdb_path: str):
    if COMPOSE_PROFILES == "postgres":
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "18040")),
            user=os.environ.get("POSTGRES_USER", "dbt"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            dbname=os.environ.get("POSTGRES_DB", "local_data_platform"),
        )
        try:
            with conn.cursor() as cur:
                for table in TABLES:
                    cur.execute(f"SELECT COUNT(*) FROM bronze.{table}")
                    count = cur.fetchone()[0]
                    print(f"✓ {table}: {count} rows")
        finally:
            conn.close()
        return

    conn = duckdb.connect(duckdb_path, read_only=True)
    try:
        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM bronze.{table}").fetchone()[0]
            print(f"✓ {table}: {count} rows")
    finally:
        conn.close()


def main():
    try:
        api_base_url = get_api_base_url()
        duckdb_path = get_duckdb_path()
        pipeline = dlt.pipeline(
            pipeline_name="jsonplaceholder",
            destination=_get_destination(),
            dataset_name="bronze",
        )
        load_info = pipeline.run(jsonplaceholder_source(api_base_url))
        load_info.raise_on_failed_jobs()
        _verify_counts(duckdb_path)
    except Exception as exc:
        print(json.dumps({"level": "ERROR", "pipeline": "jsonplaceholder", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
