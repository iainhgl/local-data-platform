import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ElementaryStoryConfigTests(unittest.TestCase):
    def test_requirements_include_elementary_data(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text()

        self.assertIn("elementary-data", requirements)

    def test_profiles_include_elementary_target(self):
        profiles = (PROJECT_ROOT / "profiles.yml").read_text()

        self.assertIn("    elementary:", profiles)
        self.assertIn("      type: duckdb", profiles)
        self.assertIn(
            '      path: "{{ env_var(\'DBT_DUCKDB_PATH\', \'dev.duckdb\') }}"',
            profiles,
        )
        self.assertIn("      schema: elementary", profiles)
        self.assertIn("elementary:\n  target: elementary", profiles)

    def test_gitignore_includes_edr_target(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()

        self.assertIn("edr_target/", gitignore)

    def test_elementary_service_serves_report_directory(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        self.assertIn("  elementary:", compose)
        self.assertIn('- "./edr_target:/workspace/edr_target"', compose)
        self.assertIn("18030:8080", compose)
        self.assertIn("python:3.11-slim", compose)
        self.assertIn("python -m http.server 8080 --directory /workspace/edr_target", compose)

    def test_dbt_project_places_elementary_models_in_elementary_schema(self):
        dbt_project = (PROJECT_ROOT / "dbt_project.yml").read_text()

        self.assertIn("  elementary:\n    +schema: elementary", dbt_project)


if __name__ == "__main__":
    unittest.main()
