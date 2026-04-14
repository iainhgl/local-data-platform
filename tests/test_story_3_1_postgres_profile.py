import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Story31PostgresProfileTests(unittest.TestCase):
    def test_postgres_init_sql_exists_with_required_schemas_roles_and_grants(self):
        init_sql = (PROJECT_ROOT / "docker/init/postgres_init.sql").read_text()

        for schema in ("bronze", "silver", "gold", "quarantine"):
            self.assertIn(f"CREATE SCHEMA IF NOT EXISTS {schema};", init_sql)

        for role in ("engineer_role", "analyst_role", "pii_analyst_role"):
            self.assertIn(role, init_sql)

        self.assertIn("GRANT USAGE, CREATE ON SCHEMA bronze TO engineer_role;", init_sql)
        self.assertIn("ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO analyst_role;", init_sql)
        self.assertIn(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA quarantine GRANT SELECT ON TABLES TO pii_analyst_role;",
            init_sql,
        )

    def test_docker_compose_postgres_service_mounts_init_script(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        self.assertIn('profiles: ["postgres", "full"]', compose)
        self.assertIn('- "${POSTGRES_PORT:-18040}:5432"', compose)
        self.assertIn(
            "- ./docker/init/postgres_init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro",
            compose,
        )

    def test_profiles_postgres_target_uses_env_vars(self):
        profiles = (PROJECT_ROOT / "profiles.yml").read_text()

        self.assertIn("      type: postgres", profiles)
        self.assertIn('      host: "{{ env_var(\'POSTGRES_HOST\', \'localhost\') }}"', profiles)
        self.assertIn('      port: "{{ env_var(\'POSTGRES_PORT\', \'18040\') | int }}"', profiles)

    def test_dlt_file_source_supports_postgres_destination(self):
        source = (PROJECT_ROOT / "ingest/dlt_file_source.py").read_text()

        self.assertIn('COMPOSE_PROFILES = os.environ.get("COMPOSE_PROFILES", "simple")', source)
        self.assertIn("dlt.destinations.postgres", source)
        self.assertIn("import psycopg2", source)

    def test_dlt_api_source_supports_postgres_destination(self):
        source = (PROJECT_ROOT / "ingest/dlt_api_source.py").read_text()

        self.assertIn('COMPOSE_PROFILES = os.environ.get("COMPOSE_PROFILES", "simple")', source)
        self.assertIn("dlt.destinations.postgres", source)
        self.assertIn("import psycopg2", source)

    def test_requirements_include_postgres_driver(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text()

        self.assertIn("psycopg2-binary", requirements)

    def test_makefile_run_pipeline_is_profile_aware(self):
        makefile = (PROJECT_ROOT / "Makefile").read_text()

        self.assertIn("set -a; . ./.env; set +a;", makefile)
        self.assertIn('if [ "$$COMPOSE_PROFILES" = "simple" ]; then \\', makefile)
        self.assertIn("Elementary (edr) and Evidence skipped for profile", makefile)


if __name__ == "__main__":
    unittest.main()
