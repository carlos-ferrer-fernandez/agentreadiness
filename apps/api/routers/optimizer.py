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
    from config import get_settings
    results = {}

    # 0. Code version — helps confirm the right deploy is live
    results["code_version"] = "v2-httpx-browser-ua"
    results["max_crawl_pages"] = get_settings().max_crawl_pages

    # 1. Check OpenAI API key
    key = os.getenv("OPENAI_API_KEY", "")
    results["openai_key_set"] = bool(key) and key != "sk-your-openai-key"
    results["openai_key_prefix"] = key[:8] + "..." if len(key) > 8 else "(empty)"

    # 2. Check model config
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


@router.get("/test-single-page")
async def test_single_page_optimization():
    """End-to-end test: crawl 1 page of Stripe docs, optimize it, return results.

    This runs synchronously (not in background) so we get the full error
    if anything fails. Use this to debug pipeline failures.
    """
    import traceback
    import resource
    from services.optimizer.document_optimizer import DocumentationOptimizer

    test_url = "https://docs.stripe.com/payments"
    results = {"test_url": test_url, "steps": {}}

    try:
        # Step 1: Memory baseline
        mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB → MB on Linux
        results["steps"]["memory_baseline_mb"] = round(mem_mb, 1)

        # Step 2: Fetch a single page with httpx
        optimizer = DocumentationOptimizer()
        results["steps"]["httpx_ua"] = optimizer.BROWSER_UA[:30] + "..."

        page = await optimizer._fetch_page(test_url)
        if not page:
            results["steps"]["fetch"] = "FAILED — returned None"
            return results

        results["steps"]["fetch"] = {
            "status": "OK",
            "title": page.title,
            "content_length": len(page.content),
            "content_preview": page.content[:200] + "...",
            "links_found": len(page.links),
            "headings_found": len(page.headings),
        }

        # Step 3: Memory after fetch
        mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        results["steps"]["memory_after_fetch_mb"] = round(mem_mb, 1)

        # Step 4: Analyze page
        analysis = optimizer._analyze_page_deep(page)
        results["steps"]["analysis"] = {
            "word_count": analysis.word_count,
            "has_code_examples": analysis.has_code_examples,
            "issues_count": len(analysis.issues),
        }

        # Step 5: Optimize with GPT-4o (the actual OpenAI call)
        terminology_context = optimizer._build_terminology_context([page])
        optimized = await optimizer._optimize_page(page, analysis, terminology_context)
        results["steps"]["optimization"] = {
            "status": "OK",
            "improvements_count": len(optimized.improvements),
            "improvements": optimized.improvements[:5],
            "output_length": len(optimized.optimized_content),
            "output_preview": optimized.optimized_content[:300] + "...",
        }

        # Step 6: Memory after optimization
        mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        results["steps"]["memory_after_optimize_mb"] = round(mem_mb, 1)

        results["overall"] = "ALL STEPS PASSED"

    except Exception as e:
        results["overall"] = f"FAILED: {type(e).__name__}: {str(e)}"
        results["traceback"] = traceback.format_exc()

    finally:
        await optimizer._close_browser()

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
