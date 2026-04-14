import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Story214CronScheduleAndReadmeTests(unittest.TestCase):
    def test_scheduler_files_exist_with_expected_commands(self):
        dockerfile = PROJECT_ROOT / "docker/scheduler/Dockerfile"
        script = PROJECT_ROOT / "docker/scheduler/run_pipeline.sh"

        self.assertTrue(dockerfile.exists())
        self.assertTrue(script.exists())

        dockerfile_text = dockerfile.read_text()
        self.assertIn("FROM python:3.11-slim", dockerfile_text)
        self.assertIn("WORKDIR /workspace", dockerfile_text)
        self.assertIn("dbt-duckdb", dockerfile_text)
        self.assertIn('"dlt[filesystem]"', dockerfile_text)
        self.assertIn("requests", dockerfile_text)
        self.assertIn("COPY docker/scheduler/run_pipeline.sh /run_pipeline.sh", dockerfile_text)

        script_text = script.read_text()
        self.assertIn("#!/bin/sh", script_text)
        self.assertIn("set -e", script_text)
        self.assertIn("PYTHONPATH=/workspace python ingest/dlt_file_source.py", script_text)
        self.assertIn("PYTHONPATH=/workspace python ingest/dlt_api_source.py", script_text)
        self.assertIn("dbt run --profiles-dir /workspace", script_text)
        self.assertIn("dbt test --profiles-dir /workspace", script_text)
        self.assertIn("dbt docs generate --profiles-dir /workspace", script_text)

    def test_compose_and_env_include_cron_scheduler(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
        env_example = (PROJECT_ROOT / ".env.example").read_text()

        self.assertIn("  cron-scheduler:", compose)
        self.assertIn("dockerfile: docker/scheduler/Dockerfile", compose)
        self.assertIn('profiles: ["simple", "postgres", "lakehouse", "full"]', compose)
        self.assertIn("- ./:/workspace", compose)
        self.assertIn("- CRON_INTERVAL=${CRON_INTERVAL:-3600}", compose)
        self.assertIn("- DBT_DUCKDB_PATH=/workspace/dev.duckdb", compose)
        self.assertIn("Scheduler starting", compose)
        self.assertIn("/run_pipeline.sh", compose)
        self.assertIn('if [ \\"${CRON_INTERVAL:-3600}\\" = \\"0\\" ]', compose)

        self.assertIn("# Cron Scheduler (Story 2.14)", env_example)
        self.assertIn("CRON_INTERVAL=3600", env_example)

    def test_readme_includes_quick_start_profiles_wsl2_and_cloud_equivalence(self):
        readme = (PROJECT_ROOT / "README.md").read_text()

        self.assertIn("## Quick Start", readme)
        self.assertNotIn("<!-- Full quick-start instructions added in Story 2.14 -->", readme)
        self.assertIn("git clone https://github.com/iainhgl/local-data-platform.git", readme)
        self.assertIn("cp .env.example .env", readme)
        self.assertIn("make start", readme)
        self.assertIn("make run-pipeline", readme)
        self.assertIn("make open-docs", readme)
        self.assertIn("## Profiles", readme)
        self.assertIn("## Cloud Equivalence", readme)
        self.assertIn("## WSL2 (Windows)", readme)
        self.assertIn("[docs/profile-guide.md](docs/profile-guide.md)", readme)
        self.assertIn("[docs/cloud-equivalence.md](docs/cloud-equivalence.md)", readme)
        self.assertIn("[docs/wsl2.md](docs/wsl2.md)", readme)
        self.assertIn("| 2.14 | Cron schedule and README | done |", readme)

    def test_supporting_docs_cover_profiles_cloud_equivalence_and_wsl2(self):
        cloud_equivalence = (PROJECT_ROOT / "docs/cloud-equivalence.md")
        profile_guide = (PROJECT_ROOT / "docs/profile-guide.md")
        wsl2 = (PROJECT_ROOT / "docs/wsl2.md")

        self.assertTrue(cloud_equivalence.exists())
        self.assertTrue(profile_guide.exists())
        self.assertTrue(wsl2.exists())

        cloud_text = cloud_equivalence.read_text()
        self.assertIn("| DuckDB | BigQuery Serverless / Redshift Serverless |", cloud_text)
        self.assertIn("| OpenMetadata | Google Dataplex / Microsoft Purview |", cloud_text)
        self.assertIn("Cloud migration notes", cloud_text)

        profile_text = profile_guide.read_text()
        self.assertIn("## `simple`", profile_text)
        self.assertIn("## `postgres`", profile_text)
        self.assertIn("## `lakehouse`", profile_text)
        self.assertIn("## `full`", profile_text)
        self.assertIn("16 GB", profile_text)

        wsl2_text = wsl2.read_text()
        self.assertIn("Ubuntu 22.04+", wsl2_text)
        self.assertIn("Use WSL 2 based engine", wsl2_text)
        self.assertIn("/mnt/c/...", wsl2_text)
        self.assertIn("%USERPROFILE%\\.wslconfig", wsl2_text)


if __name__ == "__main__":
    unittest.main()
