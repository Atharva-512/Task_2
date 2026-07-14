"""FastAPI application entrypoint.

Phase 2 scope: app wiring, CORS, lifespan-managed DuckDB connection, and a
health check. No analytical endpoints or business logic live here yet.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, health
from app.core.config import get_settings
from app.db.connection import close_connection, get_connection

logger = logging.getLogger("restaurant_pos_api")
logging.basicConfig(level=logging.INFO)

settings = get_settings()

# Allowed frontend origins
ALLOWED_ORIGINS = [
    # Local development
    "http://localhost:5173",
    "http://127.0.0.1:5173",

    # Production frontend (Vercel)
    "https://task-2-six-sable.vercel.app",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    logger.info("Starting %s in '%s' mode", app.title, settings.app_env)

    settings.validate()
    logger.info("Configuration validated successfully.")

    get_connection()

    yield

    close_connection()
    logger.info("Shutting down %s", app.title)


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Restaurant POS API",
        description="Serving layer for the Restaurant POS analytics gold layer.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(analytics.router)

    return app


app = create_app()