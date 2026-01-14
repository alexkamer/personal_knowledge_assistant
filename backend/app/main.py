"""
FastAPI main application entry point.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import (
    KnowledgeAssistantException,
    general_exception_handler,
    http_exception_handler,
    knowledge_assistant_exception_handler,
)
from app.core.rate_limit import RateLimitMiddleware

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

    Startup sequence:
    1. Reset circuit breakers
    2. Initialize and validate database connection
    3. Initialize and validate ChromaDB
    4. Preload embedding model
    5. Validate Ollama connectivity
    6. Start research scheduler
    """
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")

    try:
        # 1. Reset circuit breakers from previous runs
        from app.core.retry import (
            embedding_circuit_breaker,
            ollama_circuit_breaker,
            vector_db_circuit_breaker,
        )

        embedding_circuit_breaker.reset()
        ollama_circuit_breaker.reset()
        vector_db_circuit_breaker.reset()
        logger.info("Circuit breakers reset")

        # 2. Initialize and test database connection
        from app.core.database import init_db, get_async_session

        await init_db()
        logger.info("Database connection pool initialized and verified")

        # 3. Initialize and validate ChromaDB
        from app.core.vector_db import get_chroma_client, get_or_create_collection

        chroma_client = get_chroma_client()
        collection = get_or_create_collection()
        collection_count = collection.count()
        logger.info(
            f"ChromaDB initialized successfully. Collection '{collection.name}' has {collection_count} chunks"
        )

        # 4. Preload embedding model (warm start to avoid first-request latency)
        from app.services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()
        embedding_dim = embedding_service.get_embedding_dimension()
        logger.info(
            f"Embedding model '{settings.embedding_model}' preloaded successfully (dimension: {embedding_dim})"
        )

        # 5. Validate Ollama connectivity (optional - log warning if unavailable)
        try:
            from app.services.llm_service import get_llm_service

            llm_service = get_llm_service()
            # Test connection with lightweight model check
            available_models = await llm_service.list_models()
            if settings.ollama_primary_model in available_models:
                logger.info(
                    f"Ollama connected successfully. Primary model '{settings.ollama_primary_model}' available"
                )
            else:
                logger.warning(
                    f"Ollama connected but primary model '{settings.ollama_primary_model}' not found. "
                    f"Available models: {available_models}"
                )
        except Exception as e:
            logger.warning(
                f"Ollama not available at startup (non-fatal): {e}. "
                f"LLM endpoints will be unavailable until Ollama is started."
            )

        # 6. Start Research Scheduler
        from app.services.research_scheduler_service import get_research_scheduler

        scheduler = get_research_scheduler()
        await scheduler.start()
        logger.info("Research Autopilot scheduler started")

        logger.info(f"{settings.app_name} startup complete ✓")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise RuntimeError(f"Application startup failed: {e}") from e

    yield

    # Cleanup on shutdown
    logger.info(f"Shutting down {settings.app_name}")

    try:
        # Shutdown Research Scheduler
        await scheduler.shutdown()
        logger.info("Research Autopilot scheduler shutdown")

        # Close database connections
        from app.core.database import close_db

        await close_db()
        logger.info("Database connections closed")

        # Close ChromaDB
        from app.core.vector_db import close_chroma

        close_chroma()
        logger.info("ChromaDB closed")

        logger.info(f"{settings.app_name} shutdown complete ✓")

    except Exception as e:
        logger.error(f"Shutdown error (non-fatal): {e}", exc_info=True)


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

# Add rate limiting middleware (60 requests per minute default)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=100,
)

# Register exception handlers
app.add_exception_handler(KnowledgeAssistantException, knowledge_assistant_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


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
async def health_check() -> dict:
    """
    Comprehensive health check endpoint.

    Verifies connectivity to:
    - PostgreSQL database
    - ChromaDB vector database
    - Embedding service
    - Ollama LLM service (optional)

    Returns 200 if all critical services (DB, ChromaDB, embeddings) are available.
    Returns 503 if any critical service is down.
    """
    from app.core.database import get_async_session
    from app.core.vector_db import get_chroma_client
    from app.services.embedding_service import get_embedding_service
    from app.services.llm_service import get_llm_service

    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "checks": {},
    }

    all_healthy = True

    # 1. Check database
    try:
        async with get_async_session() as session:
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1"))
            result.scalar()
            health_status["checks"]["database"] = {
                "status": "up",
                "url": str(settings.database_url).split("@")[0] + "@***",  # Hide credentials
            }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["database"] = {
            "status": "down",
            "error": str(e),
        }

    # 2. Check ChromaDB
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        health_status["checks"]["chromadb"] = {
            "status": "up",
            "collections": len(collections),
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["chromadb"] = {
            "status": "down",
            "error": str(e),
        }

    # 3. Check embedding service
    try:
        embedding_service = get_embedding_service()
        dimension = embedding_service.get_embedding_dimension()
        health_status["checks"]["embeddings"] = {
            "status": "up",
            "model": settings.embedding_model,
            "dimension": dimension,
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["embeddings"] = {
            "status": "down",
            "error": str(e),
        }

    # 4. Check Ollama (optional - not critical)
    try:
        llm_service = get_llm_service()
        models = await llm_service.list_models()
        health_status["checks"]["ollama"] = {
            "status": "up",
            "models": len(models),
            "primary_model_available": settings.ollama_primary_model in models,
        }
    except Exception as e:
        # Ollama is optional, so don't mark overall health as down
        health_status["checks"]["ollama"] = {
            "status": "down",
            "error": str(e),
            "note": "Ollama is optional - LLM endpoints will be unavailable",
        }

    # Set overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"
        from fastapi import status as http_status
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content=health_status,
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return health_status


# Include API routers
from app.api.v1.api import api_router

app.include_router(api_router, prefix=settings.api_v1_prefix)
