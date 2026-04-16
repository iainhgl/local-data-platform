import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _phony_targets(makefile_text: str) -> list[str]:
    for line in makefile_text.splitlines():
        if line.startswith(".PHONY:"):
            return line.split(":", 1)[1].strip().split()
    raise AssertionError(".PHONY line not found in Makefile")


class Story34LightdashTests(unittest.TestCase):
    def test_lightdash_config_exists_and_targets_workspace_postgres_profile(self):
        config_path = PROJECT_ROOT / "lightdash.config.yaml"

        self.assertTrue(config_path.exists(), "lightdash.config.yaml should exist at the repo root")

        config = yaml.safe_load(config_path.read_text())
        self.assertEqual(config["version"], "1.0")

        project = next((project for project in config["projects"] if project["name"] == "local_data_platform"), None)
        self.assertIsNotNone(project)
        self.assertEqual(project["type"], "dbt")

        dbt_config = project["dbt"]
        self.assertEqual(dbt_config["type"], "local")
        self.assertEqual(dbt_config["project_dir"], "/workspace")
        self.assertEqual(dbt_config["profiles_dir"], "/workspace")
        self.assertEqual(dbt_config["profile"], "local_data_platform")
        self.assertEqual(dbt_config["target"], "postgres")

    def test_docker_compose_lightdash_service_mounts_workspace_and_sets_postgres_overrides(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        self.assertIn("- ./:/workspace", compose)
        self.assertIn("POSTGRES_HOST=postgres", compose)
        self.assertIn("POSTGRES_PORT=5432", compose)
        self.assertIn("POSTGRES_USER=${POSTGRES_USER}", compose)
        self.assertIn("POSTGRES_PASSWORD=${POSTGRES_PASSWORD}", compose)
        self.assertIn("POSTGRES_DB=${POSTGRES_DB}", compose)
        self.assertIn("PGHOST=lightdash-db", compose)
        self.assertIn(
            "Warehouse connection requires postgres service; Lightdash is only fully functional on postgres/full profiles.",
            compose,
        )

    def test_makefile_declares_lightdash_ping_target_and_phony_membership(self):
        makefile = (PROJECT_ROOT / "Makefile").read_text()
        phony_targets = _phony_targets(makefile)

        self.assertIn("lightdash-ping", phony_targets)
        self.assertIn("lightdash-ping: ## Check Lightdash is responding (postgres profile required)", makefile)
        self.assertIn("curl -sf http://localhost:18000/api/v1/health", makefile)


if __name__ == "__main__":
    unittest.main()
