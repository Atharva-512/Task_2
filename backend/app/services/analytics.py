# backend/app/services/analytics.py
"""Analytics service layer.

Executes parameterized, read-only SQL against the existing Task 1 gold
layer (views if present, fact tables otherwise). Column names are never
guessed: they are resolved against the warehouse's actual metadata
(DESCRIBE) at query time, from a list of accepted synonyms, and an error
is raised if no matching column exists.

The warehouse is a normalized star schema: fact_orders holds only
foreign keys (date_key, brand_key, platform_key), while the actual
filterable values (business_date, brand, platform) live on the
corresponding dimension tables (dim_date, dim_brand, dim_platform).
Whenever a filter is applied, the fact-table fallback path joins to
these dimensions to resolve and filter on the real values.
"""

import logging
from typing import Optional

import pandas as pd

from app.db.connection import execute_query, QueryExecutionError

logger = logging.getLogger("restaurant_pos_api.services.analytics")

_VIEW_SUMMARY = "vw_sales_summary"
_VIEW_PLATFORM_PERFORMANCE = "vw_platform_performance"
_VIEW_BRAND_PERFORMANCE = "vw_brand_performance"
_VIEW_DAILY_SALES = "vw_daily_sales"

_FACT_ORDERS = "fact_orders"
_DIM_DATE = "dim_date"
_DIM_BRAND = "dim_brand"
_DIM_PLATFORM = "dim_platform"

_column_cache: dict[str, list[str]] = {}


def _relation_exists(name: str) -> bool:
    """Check whether a view or table exists in the warehouse catalog."""
    query = """
        SELECT COUNT(*) AS cnt
        FROM information_schema.tables
        WHERE table_name = ?
    """
    df = execute_query(query, (name,))
    return bool(df.iloc[0]["cnt"]) if not df.empty else False


def _get_columns(relation: str) -> list[str]:
    """Return the actual column names of a table/view via warehouse metadata."""
    if relation in _column_cache:
        return _column_cache[relation]

    df = execute_query(f"DESCRIBE {relation}")
    columns = df["column_name"].tolist() if "column_name" in df.columns else df.iloc[:, 0].tolist()
    _column_cache[relation] = columns
    return columns


def _resolve_column(relation: str, candidates: list[str]) -> str:
    """Return the first candidate column name that actually exists on relation.

    Raises:
        QueryExecutionError: If none of the candidates exist on the relation.
    """
    available = _get_columns(relation)
    for candidate in candidates:
        if candidate in available:
            return candidate

    raise QueryExecutionError(
        f"None of the expected columns {candidates} exist on '{relation}'. "
        f"Actual columns: {available}"
    )


def _has_any_filter(
    start_date: Optional[str],
    end_date: Optional[str],
    platform: Optional[str],
    brand: Optional[str],
) -> bool:
    """Return True if at least one filter value is present.

    Treats both None and empty/whitespace-only strings as "no filter", so
    a frontend that sends "" instead of omitting the param is still safe.
    """
    return any(bool(value) for value in (start_date, end_date, platform, brand))


def _build_fact_where(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    brand: Optional[str] = None,
) -> tuple[str, str, list, str, str, str, str]:
    """Build a parameterized JOIN + WHERE clause against fact_orders for the given filters.

    fact_orders only stores foreign keys (date_key, brand_key, platform_key),
    so the actual filterable/groupable values (business_date, brand, platform)
    must be resolved via dim_date, dim_brand, and dim_platform respectively.
    This helper always joins fact_orders to all three dimensions (aliased
    f, d, b, p) so callers can SELECT/GROUP BY the real dimension columns
    regardless of which filters were supplied, and adds WHERE clauses
    (using only ? placeholders, never string-interpolated values) only for
    whichever of start_date, end_date, platform, and brand are non-empty.

    Returns:
        A tuple of (join_clause, where_clause, params, date_col, platform_col,
        brand_col, order_id_col). date_col/platform_col/brand_col/order_id_col
        are fully qualified (aliased) column references usable directly in
        SELECT/GROUP BY/ORDER BY.
    """
    order_id_col = _resolve_column(
        _FACT_ORDERS, ["invoice_no", "order_id", "order_no", "order_number"]
    )
    fact_date_key = _resolve_column(_FACT_ORDERS, ["date_key"])
    fact_brand_key = _resolve_column(_FACT_ORDERS, ["brand_key"])
    fact_platform_key = _resolve_column(_FACT_ORDERS, ["platform_key"])

    dim_date_key = _resolve_column(_DIM_DATE, ["date_key"])
    dim_date_business_date = _resolve_column(_DIM_DATE, ["business_date"])

    dim_brand_key = _resolve_column(_DIM_BRAND, ["brand_key"])
    dim_brand_name = _resolve_column(_DIM_BRAND, ["brand"])

    dim_platform_key = _resolve_column(_DIM_PLATFORM, ["platform_key"])
    dim_platform_name = _resolve_column(_DIM_PLATFORM, ["platform"])

    join_clause = f"""
        FROM {_FACT_ORDERS} AS f
        INNER JOIN {_DIM_DATE} AS d ON f.{fact_date_key} = d.{dim_date_key}
        INNER JOIN {_DIM_BRAND} AS b ON f.{fact_brand_key} = b.{dim_brand_key}
        INNER JOIN {_DIM_PLATFORM} AS p ON f.{fact_platform_key} = p.{dim_platform_key}
    """

    date_col = f"d.{dim_date_business_date}"
    brand_col = f"b.{dim_brand_name}"
    platform_col = f"p.{dim_platform_name}"
    order_id_col = f"f.{order_id_col}"

    filters: list[str] = []
    params: list = []

    if start_date:
        filters.append(f"{date_col} >= ?")
        params.append(start_date)
    if end_date:
        filters.append(f"{date_col} <= ?")
        params.append(end_date)
    if platform:
        filters.append(f"{platform_col} = ?")
        params.append(platform)
    if brand:
        filters.append(f"{brand_col} = ?")
        params.append(brand)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    return join_clause, where_clause, params, date_col, platform_col, brand_col, order_id_col


def _summary_from_fact(
    start_date: Optional[str],
    end_date: Optional[str],
    platform: Optional[str],
    brand: Optional[str],
) -> dict:
    """Compute summary metrics directly from fact_orders (joined to dims) with optional filters."""
    sales_col = _resolve_column(
        _FACT_ORDERS,
        ["total", "my_amount", "gross_sales", "gross_revenue", "total_sales", "sales_amount", "amount"],
    )
    tax_col = _resolve_column(_FACT_ORDERS, ["total_tax", "tax_amount", "tax", "gst_amount"])
    discount_col = _resolve_column(_FACT_ORDERS, ["discount", "discount_amount"])

    join_clause, where_clause, params, _date_col, _platform_col, _brand_col, order_id_col = _build_fact_where(
        start_date=start_date, end_date=end_date, platform=platform, brand=brand
    )

    sql = f"""
        SELECT
            COALESCE(SUM(f.{sales_col}), 0) AS total_sales,
            COUNT(DISTINCT {order_id_col}) AS total_orders,
            CASE
                WHEN COUNT(DISTINCT {order_id_col}) = 0 THEN 0
                ELSE COALESCE(SUM(f.{sales_col}), 0) / COUNT(DISTINCT {order_id_col})
            END AS average_order_value,
            COALESCE(SUM(f.{tax_col}), 0) AS total_tax,
            COALESCE(SUM(f.{discount_col}), 0) AS total_discount
        {join_clause}
        {where_clause}
    """
    df = execute_query(sql, tuple(params) if params else None)

    if df.empty:
        return {
            "total_sales": 0.0,
            "total_orders": 0,
            "average_order_value": 0.0,
            "total_tax": 0.0,
            "total_discount": 0.0,
        }

    row = df.iloc[0]
    return {
        "total_sales": float(row["total_sales"]),
        "total_orders": int(row["total_orders"]),
        "average_order_value": float(row["average_order_value"]),
        "total_tax": float(row["total_tax"]),
        "total_discount": float(row["total_discount"]),
    }


def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    brand: Optional[str] = None,
) -> dict:
    """Return aggregate sales summary metrics (gross figures), optionally filtered."""
    if not _has_any_filter(start_date, end_date, platform, brand) and _relation_exists(_VIEW_SUMMARY):
        sql = f"SELECT * FROM {_VIEW_SUMMARY}"
        df = execute_query(sql)
        row = df.iloc[0] if not df.empty else None
        if row is None:
            return {
                "total_sales": 0.0,
                "total_orders": 0,
                "average_order_value": 0.0,
                "total_tax": 0.0,
                "total_discount": 0.0,
            }
        sales_col = _resolve_column(_VIEW_SUMMARY, ["total_sales", "gross_sales", "sales"])
        orders_col = _resolve_column(_VIEW_SUMMARY, ["total_orders", "orders"])
        aov_col = _resolve_column(
            _VIEW_SUMMARY, ["average_order_value", "avg_order_value", "aov"]
        )
        tax_col = _resolve_column(_VIEW_SUMMARY, ["total_tax", "tax"])
        discount_col = _resolve_column(
            _VIEW_SUMMARY, ["total_discount", "discount", "average_discount"]
        )
        return {
            "total_sales": float(row[sales_col]),
            "total_orders": int(row[orders_col]),
            "average_order_value": float(row[aov_col]),
            "total_tax": float(row[tax_col]),
            "total_discount": float(row[discount_col]),
        }

    return _summary_from_fact(start_date=start_date, end_date=end_date, platform=platform, brand=brand)


def get_platform_performance(
    platform: Optional[str] = None,
    brand: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Return order counts and gross sales by platform, optionally filtered."""
    if not _has_any_filter(start_date, end_date, platform, brand) and _relation_exists(
        _VIEW_PLATFORM_PERFORMANCE
    ):
        platform_col = _resolve_column(_VIEW_PLATFORM_PERFORMANCE, ["platform"])
        orders_col = _resolve_column(_VIEW_PLATFORM_PERFORMANCE, ["orders"])
        sales_col = _resolve_column(
            _VIEW_PLATFORM_PERFORMANCE, ["gross_sales", "net_sales", "sales"]
        )

        sql = f"""
            SELECT
                {platform_col} AS platform,
                {orders_col} AS orders,
                {sales_col} AS sales
            FROM {_VIEW_PLATFORM_PERFORMANCE}
            ORDER BY {sales_col} DESC
        """
        df = execute_query(sql)
        return df.to_dict(orient="records")

    sales_col = _resolve_column(
        _FACT_ORDERS, ["total", "my_amount", "gross_sales", "gross_revenue", "total_sales", "sales_amount"]
    )

    join_clause, where_clause, params, _date_col, platform_col, _brand_col, order_id_col = _build_fact_where(
        start_date=start_date, end_date=end_date, platform=platform, brand=brand
    )

    sql = f"""
        SELECT
            {platform_col} AS platform,
            COUNT(DISTINCT {order_id_col}) AS orders,
            COALESCE(SUM(f.{sales_col}), 0) AS sales
        {join_clause}
        {where_clause}
        GROUP BY {platform_col}
        ORDER BY sales DESC
    """
    df = execute_query(sql, tuple(params) if params else None)
    return df.to_dict(orient="records")


def get_brand_performance(
    brand: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Return order counts and gross sales by brand, optionally filtered."""
    if not _has_any_filter(start_date, end_date, platform, brand) and _relation_exists(
        _VIEW_BRAND_PERFORMANCE
    ):
        brand_col = _resolve_column(_VIEW_BRAND_PERFORMANCE, ["brand"])
        orders_col = _resolve_column(_VIEW_BRAND_PERFORMANCE, ["orders"])
        sales_col = _resolve_column(
            _VIEW_BRAND_PERFORMANCE, ["gross_sales", "net_sales", "sales"]
        )

        sql = f"""
            SELECT
                {brand_col} AS brand,
                {orders_col} AS orders,
                {sales_col} AS sales
            FROM {_VIEW_BRAND_PERFORMANCE}
            ORDER BY {sales_col} DESC
        """
        df = execute_query(sql)
        return df.to_dict(orient="records")

    sales_col = _resolve_column(
        _FACT_ORDERS, ["total", "my_amount", "gross_sales", "gross_revenue", "total_sales", "sales_amount"]
    )

    join_clause, where_clause, params, _date_col, _platform_col, brand_col, order_id_col = _build_fact_where(
        start_date=start_date, end_date=end_date, platform=platform, brand=brand
    )

    sql = f"""
        SELECT
            {brand_col} AS brand,
            COUNT(DISTINCT {order_id_col}) AS orders,
            COALESCE(SUM(f.{sales_col}), 0) AS sales
        {join_clause}
        {where_clause}
        GROUP BY {brand_col}
        ORDER BY sales DESC
    """
    df = execute_query(sql, tuple(params) if params else None)
    return df.to_dict(orient="records")


def get_daily_sales(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Optional[str] = None,
    brand: Optional[str] = None,
) -> list[dict]:
    """Return daily sales and order counts, optionally filtered by date range, platform, and brand."""
    if not _has_any_filter(start_date, end_date, platform, brand) and _relation_exists(
        _VIEW_DAILY_SALES
    ):
        date_col = _resolve_column(_VIEW_DAILY_SALES, ["business_date"])
        sales_col = _resolve_column(
            _VIEW_DAILY_SALES,
            ["gross_sales", "net_sales", "sales"]
        )
        orders_col = _resolve_column(_VIEW_DAILY_SALES, ["orders"])

        sql = f"""
            SELECT {date_col}, {sales_col}, {orders_col}
            FROM {_VIEW_DAILY_SALES}
            ORDER BY {date_col}
        """
        df = execute_query(sql)
        date_col_out = date_col
        sales_col_out = sales_col
        orders_col_out = orders_col
    else:
        sales_col = _resolve_column(
            _FACT_ORDERS, ["total", "my_amount", "gross_sales", "gross_revenue", "total_sales", "sales_amount"]
        )

        join_clause, where_clause, params, date_col, _platform_col, _brand_col, order_id_col = _build_fact_where(
            start_date=start_date, end_date=end_date, platform=platform, brand=brand
        )

        sql = f"""
            SELECT
                {date_col} AS business_date,
                COALESCE(SUM(f.{sales_col}), 0) AS sales,
                COUNT(DISTINCT {order_id_col}) AS orders
            {join_clause}
            {where_clause}
            GROUP BY {date_col}
            ORDER BY {date_col}
        """
        df = execute_query(sql, tuple(params) if params else None)
        date_col_out = "business_date"
        sales_col_out = "sales"
        orders_col_out = "orders"

    if df.empty:
        return []

    if date_col_out != "business_date":
        df = df.rename(columns={date_col_out: "business_date"})
    if sales_col_out != "sales":
        df = df.rename(columns={sales_col_out: "sales"})
    if orders_col_out != "orders":
        df = df.rename(columns={orders_col_out: "orders"})

    if pd.api.types.is_datetime64_any_dtype(df["business_date"]):
        df["business_date"] = df["business_date"].dt.strftime("%Y-%m-%d")
    else:
        df["business_date"] = df["business_date"].astype(str)

    return df.to_dict(orient="records")


def get_filters() -> dict:
    """Return available brands, platforms and business date range."""

    platforms_df = execute_query("""
        SELECT DISTINCT platform
        FROM dim_platform
        WHERE platform IS NOT NULL
        ORDER BY platform
    """)

    brands_df = execute_query("""
        SELECT DISTINCT brand
        FROM dim_brand
        WHERE brand IS NOT NULL
        ORDER BY brand
    """)

    dates_df = execute_query("""
        SELECT
            MIN(business_date) AS min_business_date,
            MAX(business_date) AS max_business_date
        FROM dim_date
    """)

    min_date = None
    max_date = None

    if not dates_df.empty:
        if pd.notna(dates_df.iloc[0]["min_business_date"]):
            min_date = str(dates_df.iloc[0]["min_business_date"])[:10]

        if pd.notna(dates_df.iloc[0]["max_business_date"]):
            max_date = str(dates_df.iloc[0]["max_business_date"])[:10]

    return {
        "platforms": platforms_df["platform"].tolist() if not platforms_df.empty else [],
        "brands": brands_df["brand"].tolist() if not brands_df.empty else [],
        "min_business_date": min_date,
        "max_business_date": max_date,
    }