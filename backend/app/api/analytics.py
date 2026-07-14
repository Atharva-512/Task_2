# backend/app/api/analytics.py
"""Analytics API routes.

Read-only endpoints over the existing Task 1 gold layer, served via
DuckDB. All figures are computed on demand; nothing is hardcoded.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.connection import DatabaseConnectionError, QueryExecutionError
from app.schemas.analytics import (
    BrandPerformance,
    DailySales,
    FiltersResponse,
    PlatformPerformance,
    SummaryResponse,
)
from app.services import analytics as analytics_service

logger = logging.getLogger("restaurant_pos_api.api.analytics")

router = APIRouter(prefix="/api", tags=["analytics"])


def _validate_date(value: Optional[str], field_name: str) -> None:
    """Validate that a date string is in YYYY-MM-DD format.

    Raises:
        HTTPException: 400 if the value is present but not a valid date.
    """
    if value is None:
        return
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}: '{value}'. Expected format YYYY-MM-DD.",
        ) from exc


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    start_date: Optional[str] = Query(
        default=None, description="Filter start date (YYYY-MM-DD), inclusive."
    ),
    end_date: Optional[str] = Query(
        default=None, description="Filter end date (YYYY-MM-DD), inclusive."
    ),
    platform: Optional[str] = Query(default=None, description="Filter to a single platform."),
    brand: Optional[str] = Query(default=None, description="Filter to a single brand."),
) -> SummaryResponse:
    """Return aggregate sales summary metrics (gross figures)."""
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    try:
        data = analytics_service.get_summary(
            start_date=start_date, end_date=end_date, platform=platform, brand=brand
        )
        return SummaryResponse(**data)
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute summary: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to retrieve summary data.") from exc


@router.get("/platform-performance", response_model=list[PlatformPerformance])
async def get_platform_performance(
    platform: Optional[str] = Query(default=None, description="Filter to a single platform."),
    brand: Optional[str] = Query(default=None, description="Filter to a single brand."),
    start_date: Optional[str] = Query(
        default=None, description="Filter start date (YYYY-MM-DD), inclusive."
    ),
    end_date: Optional[str] = Query(
        default=None, description="Filter end date (YYYY-MM-DD), inclusive."
    ),
) -> list[PlatformPerformance]:
    """Return order counts and gross sales by platform, optionally filtered."""
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    try:
        data = analytics_service.get_platform_performance(
            platform=platform, brand=brand, start_date=start_date, end_date=end_date
        )
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute platform performance: %s", exc)
        raise HTTPException(
            status_code=500, detail="Unable to retrieve platform performance data."
        ) from exc

    if not data:
        raise HTTPException(status_code=404, detail="No platform performance records found.")

    return [PlatformPerformance(**row) for row in data]


@router.get("/brand-performance", response_model=list[BrandPerformance])
async def get_brand_performance(
    brand: Optional[str] = Query(default=None, description="Filter to a single brand."),
    platform: Optional[str] = Query(default=None, description="Filter to a single platform."),
    start_date: Optional[str] = Query(
        default=None, description="Filter start date (YYYY-MM-DD), inclusive."
    ),
    end_date: Optional[str] = Query(
        default=None, description="Filter end date (YYYY-MM-DD), inclusive."
    ),
) -> list[BrandPerformance]:
    """Return order counts and gross sales by brand, optionally filtered."""
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    try:
        data = analytics_service.get_brand_performance(
            brand=brand, platform=platform, start_date=start_date, end_date=end_date
        )
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute brand performance: %s", exc)
        raise HTTPException(
            status_code=500, detail="Unable to retrieve brand performance data."
        ) from exc

    if not data:
        raise HTTPException(status_code=404, detail="No brand performance records found.")

    return [BrandPerformance(**row) for row in data]


@router.get("/daily-sales", response_model=list[DailySales])
async def get_daily_sales(
    start_date: Optional[str] = Query(
        default=None, description="Filter start date (YYYY-MM-DD), inclusive."
    ),
    end_date: Optional[str] = Query(
        default=None, description="Filter end date (YYYY-MM-DD), inclusive."
    ),
    platform: Optional[str] = Query(default=None, description="Filter to a single platform."),
    brand: Optional[str] = Query(default=None, description="Filter to a single brand."),
) -> list[DailySales]:
    """Return daily sales and order counts, optionally filtered by date range, platform, and brand."""
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    try:
        data = analytics_service.get_daily_sales(
            start_date=start_date, end_date=end_date, platform=platform, brand=brand
        )
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute daily sales: %s", exc)
        raise HTTPException(
            status_code=500, detail="Unable to retrieve daily sales data."
        ) from exc

    if not data:
        raise HTTPException(status_code=404, detail="No daily sales records found.")

    return [DailySales(**row) for row in data]


@router.get("/filters", response_model=FiltersResponse)
async def get_filters() -> FiltersResponse:
    """Return available brands, platforms, and business date range from the warehouse."""
    try:
        data = analytics_service.get_filters()
        return FiltersResponse(**data)
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute filters: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to retrieve filter options.") from exc