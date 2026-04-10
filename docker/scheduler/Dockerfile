FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir \
    dbt-duckdb \
    "dlt[filesystem]" \
    faker \
    pandas \
    requests

COPY docker/scheduler/run_pipeline.sh /run_pipeline.sh

RUN chmod +x /run_pipeline.sh
