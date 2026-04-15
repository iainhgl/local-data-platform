import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Story32RbacPiiMaskingTests(unittest.TestCase):
    def test_postgres_masking_sql_exists_with_required_logging_and_masking_blocks(self):
        masking_sql = (PROJECT_ROOT / "docker/init/postgres_masking.sql").read_text()

        self.assertIn("CREATE TABLE IF NOT EXISTS public.pii_access_log", masking_sql)
        self.assertIn("GRANT INSERT, SELECT ON public.pii_access_log TO pii_analyst_role;", masking_sql)
        self.assertIn("GRANT USAGE, SELECT ON SEQUENCE public.pii_access_log_id_seq TO pii_analyst_role;", masking_sql)
        self.assertIn("ALTER SYSTEM SET log_statement = 'all';", masking_sql)
        self.assertIn("SELECT pg_reload_conf();", masking_sql)

        for table_name in (
            "silver.faker_customers",
            "gold.dim_customers",
            "gold.orders_mart",
            "quarantine.faker_customers_failed",
        ):
            self.assertIn(f"REVOKE SELECT ON {table_name} FROM analyst_role;", masking_sql)

        for view_name in (
            "silver.faker_customers_masked",
            "gold.dim_customers_masked",
            "gold.orders_mart_masked",
            "quarantine.faker_customers_failed_masked",
        ):
            self.assertIn(f"CREATE OR REPLACE VIEW {view_name} AS", masking_sql)
            self.assertIn(f"GRANT SELECT ON {view_name} TO analyst_role;", masking_sql)

    def test_masking_sql_redacts_expected_pii_columns(self):
        masking_sql = (PROJECT_ROOT / "docker/init/postgres_masking.sql").read_text()

        expected_redactions = (
            "AS first_name",
            "AS last_name",
            "AS email",
            "AS phone",
            "AS address",
        )

        for redaction in expected_redactions:
            self.assertIn(f"'***REDACTED***'::varchar {redaction}", masking_sql)

    def test_all_four_pii_tables_are_covered_and_no_pii_table_is_left_unmasked(self):
        masking_sql = (PROJECT_ROOT / "docker/init/postgres_masking.sql").read_text()

        pii_tables = {
            "silver.faker_customers": "silver.faker_customers_masked",
            "gold.dim_customers": "gold.dim_customers_masked",
            "gold.orders_mart": "gold.orders_mart_masked",
            "quarantine.faker_customers_failed": "quarantine.faker_customers_failed_masked",
        }

        for table_name, view_name in pii_tables.items():
            self.assertIn(f"REVOKE SELECT ON {table_name} FROM analyst_role;", masking_sql)
            self.assertIn(f"CREATE OR REPLACE VIEW {view_name} AS", masking_sql)

        self.assertEqual(masking_sql.count("REVOKE SELECT ON "), 4)
        self.assertEqual(masking_sql.count("CREATE OR REPLACE VIEW "), 4)

    def test_docker_compose_mounts_both_postgres_sql_scripts(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        self.assertIn(
            "- ./docker/init/postgres_init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro",
            compose,
        )
        self.assertIn(
            "- ./docker/init/postgres_masking.sql:/scripts/postgres_masking.sql:ro",
            compose,
        )

    def test_makefile_runs_postgres_masking_and_exposes_log_target(self):
        makefile = (PROJECT_ROOT / "Makefile").read_text()

        self.assertIn("pg-show-pii-log", makefile)
        self.assertIn('if [ "$$COMPOSE_PROFILES" = "postgres" ]; then \\', makefile)
        self.assertIn("-f /scripts/postgres_masking.sql; \\", makefile)
        self.assertIn("SELECT logged_at, role_name, schema_name, table_name FROM public.pii_access_log", makefile)

    def test_story_3_1_engineer_role_full_access_remains_unchanged(self):
        init_sql = (PROJECT_ROOT / "docker/init/postgres_init.sql").read_text()

        for schema in ("bronze", "silver", "gold", "quarantine"):
            self.assertIn(f"GRANT USAGE, CREATE ON SCHEMA {schema} TO engineer_role;", init_sql)
            self.assertIn(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT ALL ON TABLES TO engineer_role;", init_sql)


if __name__ == "__main__":
    unittest.main()
