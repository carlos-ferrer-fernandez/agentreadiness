"""
GrounDocs Platform - FastAPI Backend

Main entry point with proper lifespan management, database initialization,
and structured configuration.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from config import get_settings
from database import init_db, close_db, get_db
from models import AgentPage, DocPackage
from routers import sites, analyses, queries, recommendations, auth, payments, optimizer, assessments, contact, viewer
from routers import agent_pages
from routers import packages

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup, close on shutdown."""
    logger.info("Starting GrounDocs API...")
    await init_db()
    logger.info("Database initialized")

    # Seed example agent pages and packages
    from services.seed_examples import seed_example_pages
    from services.seed_packages import seed_example_packages
    from database import async_session_factory
    async with async_session_factory() as db:
        await seed_example_pages(db)
        await seed_example_packages(db)
        await db.commit()
    logger.info("Example agent pages and packages seeded")

    yield
    logger.info("Shutting down GrounDocs API...")
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
app.include_router(viewer.router, prefix="/api/v", tags=["Viewer"])
app.include_router(agent_pages.router, prefix="/api/agent-pages", tags=["Agent Pages"])
app.include_router(packages.router, prefix="/api/packages", tags=["Packages"])
app.include_router(contact.router)

# Auth
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Protected (auth required)
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["Analyses"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["Optimizer"])


@app.get("/agent-pages/{slug}", response_class=HTMLResponse)
async def serve_agent_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Serve agent pages as clean HTML at /agent-pages/{slug}."""
    from services.agent_page_generator import render_generating_html

    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    # Still generating
    if agent_page.status in ("submitted", "crawling", "generating", "full_generating"):
        return HTMLResponse(
            content=render_generating_html(agent_page.product_name, slug),
            status_code=200,
        )

    # Serve full HTML if paid and available, otherwise draft
    if agent_page.payment_status == "paid" and agent_page.full_html:
        return HTMLResponse(content=agent_page.full_html, status_code=200)
    elif agent_page.draft_html:
        return HTMLResponse(content=agent_page.draft_html, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Page not yet generated")


@app.get("/packages/{slug}/{page_slug}", response_class=HTMLResponse)
async def serve_package_page(slug: str, page_slug: str, db: AsyncSession = Depends(get_db)):
    """Serve package pages as clean HTML at /packages/{slug}/{page_slug}."""
    from services.package_renderer import render_generating_package_html

    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    if package.status in ("submitted", "crawling", "planning", "generating", "full_generating"):
        return HTMLResponse(
            content=render_generating_package_html(package.product_name, slug),
            status_code=200,
        )

    # Look up page HTML
    pages = {}
    if package.payment_status == "paid" and package.full_pages_json:
        pages = package.full_pages_json
    if not pages and package.preview_pages_json:
        pages = package.preview_pages_json

    page_data = pages.get(page_slug)
    if page_data and page_data.get("html"):
        return HTMLResponse(content=page_data["html"], status_code=200)

    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/packages/{slug}", response_class=HTMLResponse)
async def serve_package_overview(slug: str, db: AsyncSession = Depends(get_db)):
    """Redirect to the overview page of a package."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/packages/{slug}/overview", status_code=302)


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
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    # Show the actual error in non-production to aid debugging
    error_msg = f"{type(exc).__name__}: {str(exc)[:300]}"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_msg}"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
