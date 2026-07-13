"""Response schemas for the health check endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shape of the /health endpoint response."""

    status: str
    service: str
