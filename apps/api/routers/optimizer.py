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
    """Get pricing estimate based on documentation size.

    Price = max(49, estimated_api_cost × 3), rounded to end in 9.
    """
    from services.crawler.crawler import DocumentationCrawler

    try:
        async with DocumentationCrawler(start_url=request.url, max_pages=5, delay=0.3) as crawler:
            urls = await crawler._discover_urls()
            estimated_pages = len(urls)
    except Exception:
        estimated_pages = 25  # Fallback estimate

    # Calculate dynamic price: base + per_page, × 3 margin, min €49
    base_cost = float(os.getenv("PRICING_BASE_COST_USD", "5.0"))
    per_page_cost = float(os.getenv("PRICING_PER_PAGE_COST_USD", "0.40"))
    multiplier = float(os.getenv("PRICING_MARGIN_MULTIPLIER", "3.0"))
    min_price = float(os.getenv("PRICING_MIN_EUR", "49"))
    max_price = float(os.getenv("PRICING_MAX_EUR", "499"))

    estimated_cost = base_cost + (per_page_cost * estimated_pages)
    raw_price = estimated_cost * multiplier

    # Round to a "nice" price ending in 9
    price = max(min_price, min(max_price, _round_to_nice_price(raw_price)))

    return PricingResponse(
        estimated_pages=estimated_pages,
        price_eur=price,
    )


def _round_to_nice_price(raw: float) -> float:
    """Round to a nice price ending in 9 (e.g., 89, 149, 199, 299)."""
    if raw <= 89:
        return 89
    if raw <= 149:
        return 149
    if raw <= 199:
        return 199
    if raw <= 299:
        return 299
    if raw <= 399:
        return 399
    return 499


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
