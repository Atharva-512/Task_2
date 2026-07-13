"""Analytics API routes.

Read-only endpoints over the existing Task 1 gold layer, served via
DuckDB. All figures are computed on demand; nothing is hardcoded.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.connection import DatabaseConnectionError, QueryExecutionError
from app.schemas.analytics import (
    BrandPerformance,
    DailySales,
    PlatformPerformance,
    SummaryResponse,
)
from app.services import analytics as analytics_service

logger = logging.getLogger("restaurant_pos_api.api.analytics")

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/summary", response_model=SummaryResponse)
async def get_summary() -> SummaryResponse:
    """Return aggregate sales summary metrics (gross figures)."""
    try:
        data = analytics_service.get_summary()
        return SummaryResponse(**data)
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute summary: %s", exc)
        raise HTTPException(status_code=503, detail="Unable to retrieve summary data.") from exc


@router.get("/platform-performance", response_model=list[PlatformPerformance])
async def get_platform_performance() -> list[PlatformPerformance]:
    """Return order counts and gross sales broken down by platform."""
    try:
        data = analytics_service.get_platform_performance()
        return [PlatformPerformance(**row) for row in data]
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute platform performance: %s", exc)
        raise HTTPException(
            status_code=503, detail="Unable to retrieve platform performance data."
        ) from exc


@router.get("/brand-performance", response_model=list[BrandPerformance])
async def get_brand_performance() -> list[BrandPerformance]:
    """Return order counts and gross sales broken down by brand."""
    try:
        data = analytics_service.get_brand_performance()
        return [BrandPerformance(**row) for row in data]
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute brand performance: %s", exc)
        raise HTTPException(
            status_code=503, detail="Unable to retrieve brand performance data."
        ) from exc


@router.get("/daily-sales", response_model=list[DailySales])
async def get_daily_sales(
    start_date: Optional[str] = Query(
        default=None, description="Filter start date (YYYY-MM-DD), inclusive."
    ),
    end_date: Optional[str] = Query(
        default=None, description="Filter end date (YYYY-MM-DD), inclusive."
    ),
) -> list[DailySales]:
    """Return daily sales and order counts, optionally filtered by date range."""
    try:
        data = analytics_service.get_daily_sales(start_date=start_date, end_date=end_date)
        return [DailySales(**row) for row in data]
    except (DatabaseConnectionError, QueryExecutionError) as exc:
        logger.error("Failed to compute daily sales: %s", exc)
        raise HTTPException(
            status_code=503, detail="Unable to retrieve daily sales data."
        ) from exc
