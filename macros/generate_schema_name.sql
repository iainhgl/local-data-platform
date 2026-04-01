{#
  Intentional override of dbt's default generate_schema_name behaviour.
  dbt default concatenates: <target.schema>_<custom_schema_name> (e.g. dev_gold).
  This project uses raw custom schema names (e.g. gold, silver, quarantine)
  so that schema paths are consistent regardless of dbt target — intentional
  for a single-environment local development platform.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none or custom_schema_name | trim == '' -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
