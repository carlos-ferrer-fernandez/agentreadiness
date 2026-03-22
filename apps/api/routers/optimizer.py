"""
Optimizer Router

API endpoints for documentation optimization service.
No configuration needed — we apply ALL 20 agent-readiness rules to every page.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import logging

from services.optimizer.document_optimizer import DocumentationOptimizer

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for optimization jobs (transient, not worth DB persistence)
_optimization_jobs: dict[str, dict] = {}


class OptimizationRequest(BaseModel):
    url: str
    email: Optional[str] = None


class PricingRequest(BaseModel):
    url: str


class PricingResponse(BaseModel):
    estimated_pages: int
    price_eur: float


@router.post("/pricing", response_model=PricingResponse)
async def get_pricing(request: PricingRequest):
    """Get pricing estimate. Flat $199 (€172) for everyone.

    No tiers, no per-page pricing. One-time payment.
    """
    from services.crawler.crawler import DocumentationCrawler

    try:
        async with DocumentationCrawler(start_url=request.url, max_pages=5, delay=0.3) as crawler:
            urls = await crawler._discover_urls()
            estimated_pages = len(urls)
    except Exception:
        estimated_pages = 25  # Fallback estimate

    return PricingResponse(
        estimated_pages=estimated_pages,
        price_eur=172,  # Flat €172 ($199 USD)
    )


@router.post("/start")
async def start_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
):
    """Start a documentation optimization job.

    Applies all 20 agent-readiness rules automatically.
    No configuration needed — we always optimize maximally.
    """
    job_id = f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    _optimization_jobs[job_id] = {
        "id": job_id,
        "url": request.url,
        "status": "queued",
        "progress": 0,
        "stage": "queued",
        "email": request.email,
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_optimization, job_id, request.url)

    return {"job_id": job_id, "status": "queued", "message": "Optimization started — applying 20 agent-readiness rules"}


@router.get("/status/{job_id}")
async def get_optimization_status(job_id: str):
    """Get the status of an optimization job."""
    if job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _optimization_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "stage": job.get("stage", "unknown"),
        "error": job.get("error"),
        "created_at": job["created_at"],
    }


@router.get("/download/{job_id}")
async def download_optimized_docs(job_id: str):
    """Download the optimized documentation as a ZIP file."""
    if job_id not in _optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _optimization_jobs[job_id]

    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail="Optimization not complete")

    zip_path = job.get("result")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"agent-optimized-docs-{job_id}.zip",
    )


@router.get("/diagnostics")
async def optimizer_diagnostics():
    """Check optimizer dependencies: Playwright, OpenAI key, model."""
    import os
    results = {}

    # 1. Check OpenAI API key
    key = os.getenv("OPENAI_API_KEY", "")
    results["openai_key_set"] = bool(key) and key != "sk-your-openai-key"
    results["openai_key_prefix"] = key[:8] + "..." if len(key) > 8 else "(empty)"

    # 2. Check model config
    from config import get_settings
    settings = get_settings()
    results["openai_model"] = settings.openai_model
    results["openai_base_url"] = settings.openai_base_url or "(direct OpenAI)"

    # 3. Check Playwright
    try:
        from playwright.async_api import async_playwright
        results["playwright_installed"] = True
        # Try to launch browser
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            results["playwright_browser_works"] = True
            await browser.close()
            await pw.stop()
        except Exception as e:
            results["playwright_browser_works"] = False
            results["playwright_browser_error"] = str(e)
    except ImportError:
        results["playwright_installed"] = False

    # 4. Quick OpenAI test
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key, timeout=10.0)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        results["openai_api_works"] = True
        results["openai_response"] = response.choices[0].message.content
    except Exception as e:
        results["openai_api_works"] = False
        results["openai_api_error"] = str(e)

    # 5. Check Stripe
    results["stripe_key_set"] = bool(settings.stripe_secret_key)

    return results


async def _run_optimization(job_id: str, url: str):
    """Run the optimization in background."""
    job = _optimization_jobs[job_id]
    job["status"] = "running"

    def progress_callback(stage: str, progress: float):
        job["progress"] = progress
        job["stage"] = stage

    try:
        optimizer = DocumentationOptimizer()
        docs, metadata = await optimizer.optimize_documentation(url, progress_callback=progress_callback)
        zip_path = await optimizer.create_zip_package(docs, metadata)

        job["status"] = "complete"
        job["progress"] = 1.0
        job["result"] = zip_path
        job["metadata"] = metadata

    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {e}", exc_info=True)
        job["status"] = "failed"
        job["error"] = str(e)
