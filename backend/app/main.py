"""
FastAPI main application entry point.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.
    """
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    # TODO: Initialize database connection pool
    # TODO: Initialize ChromaDB
    # TODO: Load embedding model

    yield

    # Cleanup on shutdown
    logger.info(f"Shutting down {settings.app_name}")
    # TODO: Close database connections
    # TODO: Close ChromaDB connections


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Personal Knowledge Assistant API with RAG capabilities",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint - health check.
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
    }


# Include API routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.api_v1_prefix)
