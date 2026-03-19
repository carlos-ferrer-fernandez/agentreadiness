"""
AgentReadiness Platform - FastAPI Backend

Main entry point with proper lifespan management, database initialization,
and structured configuration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import get_settings
from database import init_db, close_db
from routers import sites, analyses, queries, recommendations, auth, payments, optimizer, assessments

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup, close on shutdown."""
    logger.info("Starting AgentReadiness API...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down AgentReadiness API...")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="API for measuring and optimizing documentation for AI agent consumption",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS - configurable via settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
# Public (no auth required)
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])

# Auth
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Protected (auth required)
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["Analyses"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["Optimizer"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "services": {
            "api": "up",
            "database": "up",
            "stripe": "configured" if settings.stripe_secret_key else "not configured",
            "openai": "configured" if settings.openai_api_key else "not configured",
        },
    }


@app.get("/api")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
