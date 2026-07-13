"""Response schemas for analytics endpoints."""

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
