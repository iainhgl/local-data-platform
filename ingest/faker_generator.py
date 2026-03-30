#!/usr/bin/env python3
"""
Faker synthetic data generator for local-data-platform.
Generates e-commerce entities: customers, products, orders, returns.

Usage:
    python ingest/faker_generator.py
    FAKER_ROWS=10000 python ingest/faker_generator.py
    FAKER_OUTPUT_DIR=data python ingest/faker_generator.py
"""
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
random.seed(42)  # Reproducible data for consistent test results (NFR16 idempotency)
Faker.seed(42)

ROWS = int(os.environ.get("FAKER_ROWS", "1000"))
OUTPUT_DIR = Path(os.environ.get("FAKER_OUTPUT_DIR", "data"))

CATEGORIES = ["Electronics", "Clothing", "Home", "Books", "Sports", "Toys"]
ORDER_STATUSES = ["pending", "shipped", "delivered", "cancelled", "returned"]
ORDER_STATUS_WEIGHTS = [10, 20, 50, 10, 10]
RETURN_REASONS = [
    "defective",
    "wrong_item",
    "not_as_described",
    "changed_mind",
    "damaged_in_transit",
]
ELIGIBLE_STATUSES = {"delivered", "returned"}


def _random_date(start_days_ago: int, end_days_ago: int = 0) -> str:
    """Return a random ISO8601 datetime string between start and end days ago."""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=random_seconds)).isoformat()


def generate_customers(n: int) -> list:
    customers = []
    for _ in range(n):
        customers.append(
            {
                "customer_id": str(uuid.uuid4()),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "address": fake.street_address(),
                "city": fake.city(),
                "country": fake.country_code(),
                "created_at": _random_date(730),
            }
        )
    return customers


def generate_products(n: int) -> list:
    products = []
    for _ in range(n):
        products.append(
            {
                "product_id": str(uuid.uuid4()),
                "product_name": fake.catch_phrase(),
                "category": random.choice(CATEGORIES),
                "unit_price": round(random.uniform(5.0, 500.0), 2),
                "sku": f"SKU-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))}",
                "created_at": _random_date(1095),
            }
        )
    return products


def generate_orders(n: int, customer_ids: list, products: list) -> list:
    orders = []
    for _ in range(n):
        product = random.choice(products)
        quantity = random.randint(1, 10)
        unit_price = product["unit_price"]
        order_date = _random_date(365)
        orders.append(
            {
                "order_id": str(uuid.uuid4()),
                "customer_id": random.choice(customer_ids),
                "product_id": product["product_id"],
                "order_date": order_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": round(quantity * unit_price, 2),
                "status": random.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0],
                "created_at": order_date,
            }
        )
    return orders


def generate_returns(orders: list, products: list) -> list:
    product_map = {p["product_id"]: p for p in products}
    eligible = [o for o in orders if o["status"] in ELIGIBLE_STATUSES]
    returns = []
    for order in eligible:
        return_date = _random_date(
            (datetime.now() - datetime.fromisoformat(order["order_date"])).days,
            0,
        )
        returns.append(
            {
                "return_id": str(uuid.uuid4()),
                "order_id": order["order_id"],
                "product_id": order["product_id"],
                "return_date": return_date,
                "reason": random.choice(RETURN_REASONS),
                "refund_amount": round(order["total_amount"] * random.uniform(0.5, 1.0), 2),
                "created_at": return_date,
            }
        )
    return returns


def write_json(data: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def main():
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        customers = generate_customers(ROWS)
        products = generate_products(ROWS)
        orders = generate_orders(ROWS, [c["customer_id"] for c in customers], products)
        returns = generate_returns(orders, products)

        for name, data in [
            ("customers", customers),
            ("products", products),
            ("orders", orders),
            ("returns", returns),
        ]:
            write_json(data, OUTPUT_DIR / f"{name}.json")
            print(f"✓ {name}: {len(data)} rows → {OUTPUT_DIR}/{name}.json")

    except Exception as e:
        print(json.dumps({"level": "ERROR", "script": "faker_generator", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
