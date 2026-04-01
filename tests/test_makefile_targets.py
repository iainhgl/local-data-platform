import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE_PATH = PROJECT_ROOT / "Makefile"


def _target_block(target_name: str) -> str:
    lines = MAKEFILE_PATH.read_text().splitlines()
    collecting = False
    block = []
    for line in lines:
        if not collecting and line.startswith(f"{target_name}:"):
            collecting = True
        elif collecting and line and not line.startswith("\t"):
            break

        if collecting:
            block.append(line)

    if not block:
        raise AssertionError(f"Target {target_name} not found in Makefile")

    return "\n".join(block)


class MakefileTargetsTests(unittest.TestCase):
    def test_run_pipeline_target_executes_required_steps(self):
        block = _target_block("run-pipeline")

        self.assertIn(
            '@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)',
            block,
        )
        self.assertNotIn("faker_generator.py", block)
        self.assertIn('@echo "▶  Running ingestion (file source)..."', block)
        self.assertIn("@PYTHONPATH=. python ingest/dlt_file_source.py", block)
        self.assertIn('@echo "▶  Running ingestion (API source)..."', block)
        self.assertIn("@PYTHONPATH=. python ingest/dlt_api_source.py", block)
        self.assertIn('@echo "▶  Running dbt run..."', block)
        self.assertIn("@dbt run", block)
        self.assertIn('@echo "▶  Running dbt test..."', block)
        self.assertIn("@dbt test", block)
        self.assertIn(
            '@echo "✔  Pipeline complete — run make open-docs to view dashboards"',
            block,
        )

    def test_open_docs_target_lists_all_dashboards_and_urls(self):
        block = _target_block("open-docs")

        self.assertIn(
            "open-docs: ## Open dashboards: Lightdash (18000) Evidence (18010) dbt docs (18020) Elementary (18030)",
            block,
        )
        self.assertIn('@echo "▶  Opening dashboards..."', block)
        self.assertIn("open http://localhost:18000", block)
        self.assertIn("xdg-open http://localhost:18000", block)
        self.assertIn('echo "ℹ  Lightdash:   http://localhost:18000"', block)
        self.assertIn("open http://localhost:18010", block)
        self.assertIn("xdg-open http://localhost:18010", block)
        self.assertIn('echo "ℹ  Evidence:    http://localhost:18010"', block)
        self.assertIn("open http://localhost:18020", block)
        self.assertIn("xdg-open http://localhost:18020", block)
        self.assertIn('echo "ℹ  dbt docs:    http://localhost:18020"', block)
        self.assertIn("open http://localhost:18030", block)
        self.assertIn("xdg-open http://localhost:18030", block)
        self.assertIn('echo "ℹ  Elementary:  http://localhost:18030"', block)
        self.assertIn('@echo "✔  Dashboards opened"', block)

    def test_make_help_includes_updated_target_descriptions(self):
        result = subprocess.run(
            ["make", "help"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("run-pipeline", result.stdout)
        self.assertIn("Run full pipeline: ingestion", result.stdout)
        self.assertIn("open-docs", result.stdout)
        self.assertIn("Open dashboards: Lightdash (18000)", result.stdout)


if __name__ == "__main__":
    unittest.main()
