#!/usr/bin/env python3
"""
dlt file source pipeline for local-data-platform.
Reads Faker-generated JSON files from data/ and loads to bronze schema in DuckDB.

Usage:
    python ingest/dlt_file_source.py
    DBT_DUCKDB_PATH=dev.duckdb FAKER_OUTPUT_DIR=data python ingest/dlt_file_source.py
"""
import json
import os
import sys
from pathlib import Path

import dlt
import duckdb

DATA_DIR = Path(os.environ.get("FAKER_OUTPUT_DIR", "data"))
DUCKDB_PATH = os.environ.get("DBT_DUCKDB_PATH", "dev.duckdb")
COMPOSE_PROFILES = os.environ.get("COMPOSE_PROFILES", "simple")

ENTITIES = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "returns": "return_id",
}


def make_resource(entity: str, primary_key: str) -> dlt.resource:
    @dlt.resource(name=entity, primary_key=primary_key, write_disposition="merge")
    def _resource():
        path = DATA_DIR / f"{entity}.json"
        with open(path) as f:
            yield json.load(f)

    _resource.__name__ = entity
    return _resource


@dlt.source
def faker_file_source():
    for entity, pk in ENTITIES.items():
        yield make_resource(entity, pk)


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
    return dlt.destinations.duckdb(DUCKDB_PATH)


def _verify_counts():
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
                for entity in ENTITIES:
                    cur.execute(f"SELECT COUNT(*) FROM bronze.{entity}")
                    count = cur.fetchone()[0]
                    print(f"✓ {entity}: {count} rows")
        finally:
            conn.close()
        return

    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    try:
        for entity in ENTITIES:
            count = conn.execute(f"SELECT COUNT(*) FROM bronze.{entity}").fetchone()[0]
            print(f"✓ {entity}: {count} rows")
    finally:
        conn.close()


def main():
    try:
        pipeline = dlt.pipeline(
            pipeline_name="faker_file",
            destination=_get_destination(),
            dataset_name="bronze",
        )
        load_info = pipeline.run(faker_file_source())
        load_info.raise_on_failed_jobs()
        _verify_counts()
    except Exception as e:
        print(json.dumps({"level": "ERROR", "pipeline": "faker_file", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
