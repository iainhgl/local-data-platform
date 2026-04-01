{% macro ensure_quarantine_schema() %}
    {% if target.type == 'duckdb' %}
        {% do run_query('create schema if not exists quarantine') %}
    {% else %}
        {{ log("ensure_quarantine_schema: skipped (target type is " ~ target.type ~ ", not duckdb)", info=True) }}
    {% endif %}
{% endmacro %}
