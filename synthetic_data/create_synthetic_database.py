"""
create_synthetic_database.py

Generates a synthetic DuckDB warehouse that is schema-identical to the
production Restaurant POS gold layer (9 base tables + 16 analytical views),
populated entirely with fake data. Intended for public deployment of the
Task 2 serving layer, where real business figures and real business names
(brands, restaurant locations, menu items) must never be exposed.

Design notes
------------
- Table names, column names, and column types match production exactly.
- View SQL is copied verbatim from the production warehouse (`duckdb_views()`),
  so query code in the backend does not need to change between the real
  warehouse and this synthetic one -- only DATABASE_PATH changes.
- All dimension values (brand, restaurant, category, item names) are
  procedurally generated placeholders -- never the real business names.
- All fact-table measures are drawn from distributions that are
  directionally realistic (order totals, discounts, prep times, etc.) but
  are not derived from copying any real row's values.
- Data generation is fully vectorized with NumPy/pandas and loaded into
  DuckDB via bulk `INSERT INTO ... SELECT * FROM df` (no row-by-row
  inserts), which keeps runtime to roughly 5 seconds end to end.

Usage
-----
    python create_synthetic_database.py [output_path]

Default output path: ./data/warehouse.duckdb
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

SEED = 42
OUTPUT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/warehouse.duckdb")

NUM_DAYS = 70
NUM_BRANDS = 2
NUM_RESTAURANTS = 6
NUM_CATEGORIES = 74
NUM_ITEMS = 843

NUM_ORDERS = 141_431
NUM_ORDER_ITEMS = 451_976
NUM_KITCHEN_TICKETS = 107_027

DATE_RANGE_END = pd.Timestamp("2026-07-09")

rng = np.random.default_rng(SEED)


# --------------------------------------------------------------------------
# Dimension generation
# --------------------------------------------------------------------------

def build_dim_date() -> pd.DataFrame:
    dates = pd.date_range(end=DATE_RANGE_END, periods=NUM_DAYS, freq="D")
    df = pd.DataFrame(
        {
            "date_key": np.arange(1, len(dates) + 1, dtype=np.int64),
            "business_date": dates.date,
            "weekday": dates.day_name(),
            "month": dates.month.astype(np.int64),
            "month_name": dates.month_name(),
            "quarter": dates.quarter.astype(np.int64),
            "year": dates.year.astype(np.int64),
        }
    )
    return df


def build_dim_brand() -> pd.DataFrame:
    names = [f"Brand {chr(65 + i)}" for i in range(NUM_BRANDS)]
    return pd.DataFrame(
        {"brand_key": np.arange(1, NUM_BRANDS + 1, dtype=np.int64), "brand": names}
    )


def build_dim_platform() -> pd.DataFrame:
    # Generic channel/platform categories -- not proprietary business data.
    names = ["Delivery", "Dine In", "Pick Up", "Aggregator A", "Aggregator A (Partner)", "Aggregator B"]
    return pd.DataFrame(
        {"platform_key": np.arange(1, len(names) + 1, dtype=np.int64), "platform": names}
    )


def build_dim_restaurant() -> pd.DataFrame:
    names = [f"Location {i + 1}" for i in range(NUM_RESTAURANTS)]
    return pd.DataFrame(
        {
            "restaurant_key": np.arange(1, NUM_RESTAURANTS + 1, dtype=np.int64),
            "restaurant_name": names,
        }
    )


def build_dim_category() -> pd.DataFrame:
    pool = [
        "Starters", "Main Course", "Breads", "Rice & Biryani", "Curries",
        "Beverages", "Desserts", "Snacks", "Combos", "Thali", "Salads",
        "Soups", "Add-Ons", "Sides", "Wraps", "Sandwiches", "Chaat",
        "Pizza", "Pasta", "Grill",
    ]
    names = []
    i = 0
    while len(names) < NUM_CATEGORIES:
        base = pool[i % len(pool)]
        suffix = i // len(pool)
        names.append(base if suffix == 0 else f"{base} {suffix + 1}")
        i += 1
    return pd.DataFrame(
        {
            "category_key": np.arange(1, NUM_CATEGORIES + 1, dtype=np.int64),
            "category_name": names,
        }
    )


def build_dim_item(dim_category: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    names = [f"Item {i + 1:04d}" for i in range(NUM_ITEMS)]
    df = pd.DataFrame(
        {"item_key": np.arange(1, NUM_ITEMS + 1, dtype=np.int64), "item_name": names}
    )
    # Fixed item -> category assignment, used later for fact_order_items
    # so item/category pairs stay consistent across all fact rows.
    item_category_keys = rng.choice(dim_category["category_key"].to_numpy(), size=NUM_ITEMS)
    return df, item_category_keys


# --------------------------------------------------------------------------
# Fact table generation
# --------------------------------------------------------------------------

ORDER_TYPES = ["Delivery(Parcel)", "Dine In", "Pick Up"]
DAYPARTS = ["Breakfast", "Lunch", "Snacks", "Dinner", "Late Night"]
CANCEL_REASONS = [
    "Order rejected due to 'Customer cancellation'",
    "Order rejected due to 'Kitchen is full'",
    "Order rejected due to 'Item out of stock'",
    "Order rejected due to 'Delivery partner cancelled'",
]
SERVER_NAMES = [
    "Autoaccept", "Server A", "Server B", "Server C", "Server D",
    "Server E", "Server F", "Server G", "Server H",
]
ITEM_STATUSES = ["Success", "Cancelled"]


def build_fact_orders(dim_date: pd.DataFrame, dim_restaurant: pd.DataFrame,
                       dim_brand: pd.DataFrame, dim_platform: pd.DataFrame) -> pd.DataFrame:
    n = NUM_ORDERS

    date_keys = rng.choice(dim_date["date_key"].to_numpy(), size=n)
    restaurant_keys = rng.choice(dim_restaurant["restaurant_key"].to_numpy(), size=n)
    brand_keys = rng.choice(dim_brand["brand_key"].to_numpy(), size=n).astype(np.float64)
    platform_keys = rng.choice(dim_platform["platform_key"].to_numpy(), size=n)

    invoice_no = np.array([f"INV{100000 + i}" for i in range(n)])
    kot_no = np.array([f"KOT{100000 + i}" for i in range(n)])

    daypart = rng.choice(DAYPARTS, size=n, p=[0.12, 0.28, 0.15, 0.30, 0.15])
    order_type = rng.choice(ORDER_TYPES, size=n, p=[0.55, 0.25, 0.20])

    status = rng.choice(["Success", "Cancelled"], size=n, p=[0.92, 0.08])
    order_cancel_reason = np.where(
        status == "Cancelled",
        rng.choice(CANCEL_REASONS, size=n),
        None,
    )

    # Gross amount: log-normal, floored/capped to a realistic order-value range.
    my_amount = np.round(np.clip(rng.lognormal(mean=6.0, sigma=0.6, size=n), 50, 19000), 2)
    total_tax = np.round(my_amount * rng.uniform(0.02, 0.06, size=n), 2)
    discount = np.round(
        np.where(
            rng.random(n) < 0.35,
            my_amount * rng.uniform(0.02, 0.25, size=n),
            0.0,
        ),
        2,
    )
    delivery_charge = np.round(
        np.where(order_type == "Delivery(Parcel)", rng.uniform(0, 80, size=n), 0.0), 2
    )
    container_charge = np.round(
        np.where(order_type == "Delivery(Parcel)", rng.uniform(0, 40, size=n), 0.0), 2
    )
    service_charge = np.zeros(n, dtype=np.int64)
    additional_charge = np.zeros(n, dtype=np.int64)
    deduction_charge = np.zeros(n, dtype=np.int64)
    waived_off = np.round(np.where(rng.random(n) < 0.05, rng.uniform(0, 50, size=n), 0.0), 2)
    round_off = np.round(rng.uniform(-0.5, 0.5, size=n), 2)

    total = np.round(
        my_amount - discount + total_tax + delivery_charge + container_charge
        - waived_off + round_off,
        2,
    )
    # Cancelled orders contribute zero net sales, mirroring real POS behaviour.
    total = np.where(status == "Cancelled", 0.0, total)

    return pd.DataFrame(
        {
            "date_key": date_keys,
            "restaurant_key": restaurant_keys,
            "brand_key": brand_keys,
            "platform_key": platform_keys,
            "invoice_no": invoice_no,
            "kot_no": kot_no,
            "daypart": daypart,
            "order_type": order_type,
            "status": status,
            "order_cancel_reason": order_cancel_reason,
            "my_amount": my_amount,
            "total_tax": total_tax,
            "discount": discount,
            "delivery_charge": delivery_charge,
            "container_charge": container_charge,
            "service_charge": service_charge,
            "additional_charge": additional_charge,
            "deduction_charge": deduction_charge,
            "waived_off": waived_off,
            "round_off": round_off,
            "total": total,
        }
    )


def build_fact_order_items(fact_orders: pd.DataFrame, dim_item: pd.DataFrame,
                            item_category_keys: np.ndarray) -> pd.DataFrame:
    n_orders = len(fact_orders)
    avg_items_per_order = NUM_ORDER_ITEMS / n_orders
    # Poisson-distributed line-item counts per order, floored at 1.
    lines_per_order = rng.poisson(lam=avg_items_per_order, size=n_orders)
    lines_per_order = np.clip(lines_per_order, 1, None)

    order_idx = np.repeat(np.arange(n_orders), lines_per_order)
    n = len(order_idx)

    item_keys = rng.integers(1, NUM_ITEMS + 1, size=n)
    category_keys = item_category_keys[item_keys - 1]

    item_quantity = rng.integers(1, 4, size=n).astype(np.float64)
    item_price = np.round(np.clip(rng.lognormal(mean=4.5, sigma=0.5, size=n), 20, 2000), 2)
    item_total = np.round(item_quantity * item_price, 2)

    orders = fact_orders.iloc[order_idx]

    df = pd.DataFrame(
        {
            "date_key": orders["date_key"].to_numpy().astype(np.float64),
            "restaurant_key": orders["restaurant_key"].to_numpy().astype(np.float64),
            "brand_key": orders["brand_key"].to_numpy(),
            "platform_key": orders["platform_key"].to_numpy().astype(np.float64),
            "category_key": category_keys,
            "item_key": item_keys,
            "invoice_no": orders["invoice_no"].to_numpy(),
            "item_quantity": item_quantity,
            "item_price": item_price,
            "item_total": item_total,
        }
    )
    return df


def build_fact_kitchen(dim_date: pd.DataFrame, dim_item: pd.DataFrame) -> pd.DataFrame:
    n = NUM_KITCHEN_TICKETS

    date_keys = rng.choice(dim_date["date_key"].to_numpy(), size=n)
    item_keys = rng.integers(1, NUM_ITEMS + 1, size=n).astype(np.float64)
    kot_id = np.arange(1, n + 1, dtype=np.int64)
    order_type = rng.choice(ORDER_TYPES, size=n, p=[0.55, 0.25, 0.20])
    server_name = rng.choice(SERVER_NAMES, size=n)
    item_status = rng.choice(ITEM_STATUSES, size=n, p=[0.94, 0.06])
    qty = rng.integers(1, 4, size=n).astype(np.float64)
    price = np.round(np.clip(rng.lognormal(mean=4.5, sigma=0.5, size=n), 20, 2000), 2)
    prep_time = np.round(np.clip(rng.gamma(shape=3.0, scale=3.5, size=n), 0.5, 1580), 2)

    return pd.DataFrame(
        {
            "date_key": date_keys,
            "item_key": item_keys,
            "kot_id": kot_id,
            "order_type": order_type,
            "server_name": server_name,
            "item_status": item_status,
            "qty": qty,
            "price": price,
            "preparation_time_taken_mins": prep_time,
        }
    )


# --------------------------------------------------------------------------
# View definitions (copied verbatim from production `duckdb_views()`)
# --------------------------------------------------------------------------

VIEW_DEFINITIONS: dict[str, str] = {
    "vw_aov_analysis": """
        CREATE VIEW vw_aov_analysis AS
        WITH monthly_orders AS (
            SELECT d."year" AS "year", d."month" AS "month", d.month_name AS month_name,
                   count(DISTINCT f.invoice_no) AS orders, sum(f.total) AS sales
            FROM fact_orders AS f
            INNER JOIN dim_date AS d ON (f.date_key = d.date_key)
            GROUP BY d."year", d."month", d.month_name
        )
        SELECT "year", "month", month_name, orders, sales,
               round((sales / nullif(orders, 0)), 2) AS average_order_value
        FROM monthly_orders
        ORDER BY "year", "month"
    """,
    "vw_brand_performance": """
        CREATE VIEW vw_brand_performance AS
        SELECT b.brand AS brand, count(DISTINCT f.invoice_no) AS orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total_tax) AS tax, sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value,
               round(avg(f.discount), 2) AS average_discount
        FROM fact_orders AS f
        INNER JOIN dim_brand AS b ON (f.brand_key = b.brand_key)
        GROUP BY b.brand
        ORDER BY net_sales DESC
    """,
    "vw_brand_sales": """
        CREATE VIEW vw_brand_sales AS
        SELECT b.brand AS brand, count(DISTINCT f.invoice_no) AS total_orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value
        FROM fact_orders AS f
        INNER JOIN dim_brand AS b ON (f.brand_key = b.brand_key)
        GROUP BY b.brand
        ORDER BY gross_sales DESC
    """,
    "vw_category_performance": """
        CREATE VIEW vw_category_performance AS
        SELECT c.category_name AS category, sum(f.item_quantity) AS items_sold,
               sum((f.item_price * f.item_quantity)) AS gross_sales,
               sum(f.item_total) AS net_sales,
               round((sum(f.item_total) / nullif(sum(f.item_quantity), 0)), 2) AS average_item_price
        FROM fact_order_items AS f
        INNER JOIN dim_category AS c ON (f.category_key = c.category_key)
        GROUP BY c.category_name
        ORDER BY net_sales DESC
    """,
    "vw_category_sales": """
        CREATE VIEW vw_category_sales AS
        SELECT c.category_name AS category_name, sum(f.item_quantity) AS quantity_sold,
               sum(f.item_total) AS revenue,
               round((sum(f.item_total) / nullif(sum(f.item_quantity), 0)), 2) AS average_item_price
        FROM fact_order_items AS f
        INNER JOIN dim_category AS c ON (f.category_key = c.category_key)
        GROUP BY c.category_name
        ORDER BY revenue DESC
    """,
    "vw_charge_analysis": """
        CREATE VIEW vw_charge_analysis AS
        SELECT d.business_date AS business_date, sum(f.delivery_charge) AS delivery_charge,
               sum(f.container_charge) AS container_charge, sum(f.service_charge) AS service_charge,
               sum(f.additional_charge) AS additional_charge, sum(f.deduction_charge) AS deduction_charge,
               sum(f.total) AS total_sales
        FROM fact_orders AS f
        INNER JOIN dim_date AS d ON (f.date_key = d.date_key)
        GROUP BY d.business_date
        ORDER BY d.business_date
    """,
    "vw_daily_sales": """
        CREATE VIEW vw_daily_sales AS
        SELECT d.business_date AS business_date, d.weekday AS weekday, d."month" AS "month",
               d.month_name AS month_name, d."year" AS "year", r.restaurant_name AS restaurant_name,
               count(DISTINCT f.invoice_no) AS orders, sum(f.my_amount) AS gross_sales,
               sum(f.discount) AS discount, sum(f.delivery_charge) AS delivery_charge,
               sum(f.container_charge) AS container_charge, sum(f.total_tax) AS tax,
               sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value
        FROM fact_orders AS f
        INNER JOIN dim_date AS d ON (f.date_key = d.date_key)
        INNER JOIN dim_restaurant AS r ON (f.restaurant_key = r.restaurant_key)
        GROUP BY d.business_date, d.weekday, d."month", d.month_name, d."year", r.restaurant_name
        ORDER BY d.business_date, r.restaurant_name
    """,
    "vw_daypart_sales": """
        CREATE VIEW vw_daypart_sales AS
        SELECT COALESCE(f.daypart, 'Unknown') AS daypart, count(DISTINCT f.invoice_no) AS orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total_tax) AS tax, sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value,
               round(avg(f.discount), 2) AS average_discount
        FROM fact_orders AS f
        GROUP BY COALESCE(f.daypart, 'Unknown')
        ORDER BY net_sales DESC
    """,
    "vw_discount_analysis": """
        CREATE VIEW vw_discount_analysis AS
        SELECT d.business_date AS business_date, sum(f.my_amount) AS gross_sales,
               sum(f.discount) AS discount,
               round(((sum(f.discount) / nullif(sum(f.my_amount), 0)) * 100), 2) AS discount_percentage
        FROM fact_orders AS f
        INNER JOIN dim_date AS d ON (f.date_key = d.date_key)
        GROUP BY d.business_date
        ORDER BY d.business_date
    """,
    "vw_item_performance": """
        CREATE VIEW vw_item_performance AS
        SELECT i.item_name AS item, c.category_name AS category, sum(f.item_quantity) AS quantity,
               sum((f.item_price * f.item_quantity)) AS gross_sales,
               round(avg(f.item_price), 2) AS average_item_price
        FROM fact_order_items AS f
        INNER JOIN dim_item AS i ON (f.item_key = i.item_key)
        INNER JOIN dim_category AS c ON (f.category_key = c.category_key)
        GROUP BY i.item_name, c.category_name
        ORDER BY gross_sales DESC
    """,
    "vw_item_sales": """
        CREATE VIEW vw_item_sales AS
        SELECT i.item_name AS item_name, sum(f.item_quantity) AS quantity_sold,
               sum(f.item_total) AS revenue,
               round((sum(f.item_total) / nullif(sum(f.item_quantity), 0)), 2) AS average_price,
               count(DISTINCT f.invoice_no) AS number_of_orders
        FROM fact_order_items AS f
        INNER JOIN dim_item AS i ON (f.item_key = i.item_key)
        GROUP BY i.item_name
        ORDER BY revenue DESC
    """,
    "vw_kitchen_performance": """
        CREATE VIEW vw_kitchen_performance AS
        SELECT f.order_type AS order_type, f.server_name AS server_name, f.item_status AS item_status,
               count(DISTINCT f.kot_id) AS kitchen_tickets,
               round(avg(f.preparation_time_taken_mins), 2) AS average_preparation_time,
               min(f.preparation_time_taken_mins) AS minimum_preparation_time,
               max(f.preparation_time_taken_mins) AS maximum_preparation_time,
               CASE
                   WHEN (avg(f.preparation_time_taken_mins) < 10) THEN 'Excellent'
                   WHEN (avg(f.preparation_time_taken_mins) < 15) THEN 'Good'
                   ELSE 'Needs Attention'
               END AS performance_status
        FROM fact_kitchen AS f
        GROUP BY f.order_type, f.server_name, f.item_status
        ORDER BY average_preparation_time DESC
    """,
    "vw_order_status_analysis": """
        CREATE VIEW vw_order_status_analysis AS
        SELECT f.status AS status,
               CASE
                   WHEN (f.status = 'Success') THEN 'Not Cancelled'
                   WHEN (f.order_cancel_reason IS NULL) THEN 'Unknown'
                   ELSE f.order_cancel_reason
               END AS order_cancel_reason,
               count(DISTINCT f.invoice_no) AS orders, sum(f.my_amount) AS gross_sales,
               sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value,
               round(((100.0 * count(DISTINCT f.invoice_no)) / sum(count(DISTINCT f.invoice_no)) OVER ()), 2) AS order_percentage
        FROM fact_orders AS f
        GROUP BY f.status,
                 CASE
                     WHEN (f.status = 'Success') THEN 'Not Cancelled'
                     WHEN (f.order_cancel_reason IS NULL) THEN 'Unknown'
                     ELSE f.order_cancel_reason
                 END
        ORDER BY orders DESC
    """,
    "vw_order_type_performance": """
        CREATE VIEW vw_order_type_performance AS
        SELECT f.order_type AS order_type, count(DISTINCT f.invoice_no) AS orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total_tax) AS tax, sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value,
               round(avg(f.discount), 2) AS average_discount
        FROM fact_orders AS f
        GROUP BY f.order_type
        ORDER BY net_sales DESC
    """,
    "vw_platform_performance": """
        CREATE VIEW vw_platform_performance AS
        SELECT p.platform AS platform, count(DISTINCT f.invoice_no) AS orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total_tax) AS tax, sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value,
               round(avg(f.discount), 2) AS average_discount
        FROM fact_orders AS f
        INNER JOIN dim_platform AS p ON (f.platform_key = p.platform_key)
        GROUP BY p.platform
        ORDER BY net_sales DESC
    """,
    "vw_platform_sales": """
        CREATE VIEW vw_platform_sales AS
        SELECT p.platform AS platform, count(DISTINCT f.invoice_no) AS total_orders,
               sum(f.my_amount) AS gross_sales, sum(f.discount) AS discount,
               sum(f.total_tax) AS tax, sum(f.total) AS net_sales,
               round((sum(f.total) / nullif(count(DISTINCT f.invoice_no), 0)), 2) AS average_order_value
        FROM fact_orders AS f
        INNER JOIN dim_platform AS p ON (f.platform_key = p.platform_key)
        GROUP BY p.platform
        ORDER BY gross_sales DESC
    """,
}

# View creation order matters only in that all referenced tables must exist
# first; views do not depend on each other, so any order is safe.
VIEW_ORDER = [
    "vw_platform_sales", "vw_platform_performance", "vw_order_type_performance",
    "vw_order_status_analysis", "vw_kitchen_performance", "vw_item_sales",
    "vw_item_performance", "vw_discount_analysis", "vw_daypart_sales",
    "vw_daily_sales", "vw_charge_analysis", "vw_category_sales",
    "vw_category_performance", "vw_brand_sales", "vw_brand_performance",
    "vw_aov_analysis",
]


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    start = time.perf_counter()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    print("Generating dimension data...")
    dim_date = build_dim_date()
    dim_brand = build_dim_brand()
    dim_platform = build_dim_platform()
    dim_restaurant = build_dim_restaurant()
    dim_category = build_dim_category()
    dim_item, item_category_keys = build_dim_item(dim_category)

    print("Generating fact_orders...")
    fact_orders = build_fact_orders(dim_date, dim_restaurant, dim_brand, dim_platform)

    print("Generating fact_order_items...")
    fact_order_items = build_fact_order_items(fact_orders, dim_item, item_category_keys)

    print("Generating fact_kitchen...")
    fact_kitchen = build_fact_kitchen(dim_date, dim_item)

    print(f"Connecting to {OUTPUT_PATH} ...")
    con = duckdb.connect(str(OUTPUT_PATH))

    print("Bulk-loading tables...")
    tables = {
        "dim_brand": dim_brand,
        "dim_category": dim_category,
        "dim_date": dim_date,
        "dim_item": dim_item,
        "dim_platform": dim_platform,
        "dim_restaurant": dim_restaurant,
        "fact_kitchen": fact_kitchen,
        "fact_order_items": fact_order_items,
        "fact_orders": fact_orders,
    }
    for table_name, df in tables.items():
        con.register("df_tmp", df)
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_tmp")
        con.unregister("df_tmp")

    print("Creating views...")
    for view_name in VIEW_ORDER:
        con.execute(VIEW_DEFINITIONS[view_name])

    print("Verifying schema parity (16 views, 9 base tables)...")
    counts = con.execute(
        """
        SELECT table_type, COUNT(*) AS cnt
        FROM information_schema.tables
        GROUP BY table_type
        """
    ).fetchdf()
    print(counts.to_string(index=False))

    con.close()

    elapsed = time.perf_counter() - start
    print(f"Done. Synthetic warehouse written to {OUTPUT_PATH} in {elapsed:.2f}s.")


if __name__ == "__main__":
    main()
