"""Response schemas for analytics endpoints."""

from typing import Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_sales: float
    total_orders: int
    average_order_value: float
    total_tax: float
    total_discount: float


class PlatformPerformance(BaseModel):
    platform: str
    orders: int
    sales: float


class BrandPerformance(BaseModel):
    brand: str
    orders: int
    sales: float


class DailySales(BaseModel):
    business_date: str
    sales: float
    orders: int


class FiltersResponse(BaseModel):
    platforms: list[str]
    brands: list[str]
    min_business_date: Optional[str]
    max_business_date: Optional[str]
