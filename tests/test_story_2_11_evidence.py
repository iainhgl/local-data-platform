import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Story211EvidenceTests(unittest.TestCase):
    def test_evidence_project_files_and_content(self):
        package_json = PROJECT_ROOT / "evidence/package.json"
        plugins_file = PROJECT_ROOT / "evidence/evidence.plugins.yaml"
        connection_file = PROJECT_ROOT / "evidence/sources/local_duckdb/connection.yaml"
        index_page = PROJECT_ROOT / "evidence/pages/index.md"
        orders_summary = PROJECT_ROOT / "evidence/pages/gold/orders-summary.md"

        self.assertTrue(package_json.exists())
        self.assertTrue(plugins_file.exists())
        self.assertTrue(connection_file.exists())
        self.assertTrue(index_page.exists())
        self.assertTrue(orders_summary.exists())

        self.assertIn('"name"', package_json.read_text())

        plugins_text = plugins_file.read_text()
        self.assertIn("components:", plugins_text)
        self.assertIn('"@evidence-dev/core-components": {}', plugins_text)
        self.assertIn("plugins:", plugins_text)
        self.assertIn('"@evidence-dev/duckdb": {}', plugins_text)

        connection_text = connection_file.read_text()
        self.assertIn("name: local_duckdb", connection_text)
        self.assertIn("type: duckdb", connection_text)
        self.assertIn("filename: ../../../dev.duckdb", connection_text)

        index_text = index_page.read_text()
        self.assertIn("Local Data Platform - Pipeline Reports", index_text)
        self.assertIn("# Pipeline Reports", index_text)
        self.assertIn("[Orders Summary](/gold/orders-summary)", index_text)

        orders_text = orders_summary.read_text()
        self.assertIn("title: Gold Layer - Orders Summary", orders_text)
        self.assertIn("Source: `gold.orders_mart`", orders_text)
        self.assertIn("from orders_mart", orders_text)
        self.assertIn("<BigValue data={orders_overview}", orders_text)
        self.assertIn("<DataTable data={orders_by_category} />", orders_text)

    def test_evidence_docker_service_and_gitignore(self):
        docker_compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
        gitignore = (PROJECT_ROOT / ".gitignore").read_text()

        self.assertIn("evidence:", docker_compose)
        self.assertIn("image: node:20-slim", docker_compose)
        self.assertIn("platform: linux/arm64", docker_compose)
        self.assertIn('- ./:/evidence-workspace', docker_compose)
        self.assertIn("working_dir: /evidence-workspace", docker_compose)
        self.assertIn(
            "Evidence build not found, run: make build-evidence",
            docker_compose,
        )
        self.assertIn("npx serve -s evidence/.evidence/template/build -l 3000", docker_compose)

        self.assertIn("evidence/node_modules/", gitignore)
        self.assertIn("evidence/.evidence/", gitignore)
        self.assertIn("evidence/.env", gitignore)


if __name__ == "__main__":
    unittest.main()
