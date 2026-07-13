"""FastAPI application entrypoint.

Phase 1 scope: app wiring, CORS, lifespan events, and a health check only.
No database connection and no analytical endpoints live here yet.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import get_settings

logger = logging.getLogger("restaurant_pos_api")
logging.basicConfig(level=logging.INFO)

settings = get_settings()

# Local Vite dev server defaults. Adjust/extend via ALLOWED_ORIGINS in a
# later phase if additional environments (e.g. deployed frontend URL) need
# to be added.
LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    logger.info("Starting %s in '%s' mode", app.title, settings.app_env)
    yield
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
        allow_origins=LOCAL_DEV_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)

    return app


app = create_app()
