import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Story33SchemaContractsTests(unittest.TestCase):
    def test_gold_models_keep_contract_enforcement_enabled(self):
        for schema_path, model_names in (
            ("models/gold/facts/schema.yml", ("fct_orders",)),
            ("models/gold/dimensions/schema.yml", ("dim_customers", "dim_products")),
            ("models/gold/marts/schema.yml", ("orders_mart",)),
        ):
            schema = yaml.safe_load((PROJECT_ROOT / schema_path).read_text())
            models = {model["name"]: model for model in schema["models"]}

            for model_name in model_names:
                self.assertTrue(models[model_name]["config"]["contract"]["enforced"])

    def test_all_gold_model_columns_declare_data_types(self):
        for schema_path in (
            "models/gold/facts/schema.yml",
            "models/gold/dimensions/schema.yml",
            "models/gold/marts/schema.yml",
        ):
            schema = yaml.safe_load((PROJECT_ROOT / schema_path).read_text())

            for model in schema["models"]:
                for column in model["columns"]:
                    self.assertIn("data_type", column, f"{model['name']}.{column['name']} is missing data_type")

    def test_primary_key_columns_declare_not_null_and_primary_key_constraints(self):
        expected_constraints = {
            ("models/gold/facts/schema.yml", "fct_orders", "order_id"): {"not_null", "primary_key"},
            ("models/gold/dimensions/schema.yml", "dim_customers", "customer_id"): {"not_null", "primary_key"},
            ("models/gold/dimensions/schema.yml", "dim_products", "product_id"): {"not_null", "primary_key"},
            ("models/gold/marts/schema.yml", "orders_mart", "order_id"): {"not_null", "primary_key"},
        }

        for schema_path, model_name, column_name in expected_constraints:
            schema = yaml.safe_load((PROJECT_ROOT / schema_path).read_text())
            model = next(model for model in schema["models"] if model["name"] == model_name)
            column = next(column for column in model["columns"] if column["name"] == column_name)
            constraint_types = {constraint["type"] for constraint in column["constraints"]}

            self.assertEqual(constraint_types, expected_constraints[(schema_path, model_name, column_name)])

    def test_makefile_declares_contract_verification_target(self):
        makefile = (PROJECT_ROOT / "Makefile").read_text()

        self.assertIn(".PHONY: help start stop run-pipeline pg-show-pii-log dbt-verify-contracts", makefile)
        self.assertIn("dbt-verify-contracts: ## Compile Gold models to verify schema contract syntax (no DB required)", makefile)
        self.assertIn("\tdbt compile --select tag:gold", makefile)


if __name__ == "__main__":
    unittest.main()
