"""
Assessments Router

Public endpoints for the free assessment flow (no auth required).
Evaluates documentation against the 20 agent-readiness rules derived
from a multi-agent benchmark (Claude, GPT, Kimi, Grok, Deepseek, etc.).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os
import logging

from database import get_db
from models import Assessment
from config import get_settings
from pricing import calculate_report_price

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


class AssessmentRequest(BaseModel):
    url: HttpUrl
    email: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: str
    url: str
    site_name: str
    score: int
    grade: str
    components: dict
    rule_results: list[dict]  # Per-rule breakdown (20 rules)
    query_count: int
    pass_rate: float
    avg_latency_ms: int
    page_count: int
    top_issues: list[dict]
    estimated_price_eur: int
    has_paid: bool
    optimization_status: Optional[str] = None
    optimization_progress: float = 0.0
    optimization_stage: Optional[str] = None
    optimization_metadata: Optional[dict] = None
    created_at: str

    model_config = {"from_attributes": True}


class PromoCodeRequest(BaseModel):
    assessment_id: str
    code: str


@router.post("/analyze", response_model=AssessmentResponse)
async def run_assessment(
    request: AssessmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Run a free public assessment on a documentation URL.

    Crawls the site and evaluates it against the 20 agent-readiness rules
    derived from benchmarking 8 major AI agents. Returns per-rule scores,
    component scores, and an overall grade.
    """
    from services.crawler.crawler import DocumentationCrawler
    from services.evaluator.rule_analyzer import AgentReadinessAnalyzer
    from urllib.parse import urlparse

    url = str(request.url)
    parsed = urlparse(url)
    site_name = parsed.netloc.replace("www.", "")

    try:
        # Step 1: Crawl (limited to 30 pages for free assessment)
        async with DocumentationCrawler(
            start_url=url,
            max_pages=30,
            delay=0.5,
        ) as crawler:
            pages = await crawler.crawl()

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Could not crawl the provided URL. Please check the URL and try again.",
            )

        # Step 2: Analyze against 20 agent-readiness rules
        analyzer = AgentReadinessAnalyzer()
        analysis = analyzer.analyze(pages)

        # Step 3: Calculate dynamic price based on doc size
        report_price = calculate_report_price(len(pages))

        # Step 4: Compute query-equivalent stats (for backward compat)
        rules_passing = sum(1 for r in analysis.rule_results if r.status == 'pass')
        pass_rate = rules_passing / len(analysis.rule_results) if analysis.rule_results else 0.0

        # Step 5: Persist assessment
        assessment = Assessment(
            url=url,
            site_name=site_name,
            email=request.email,
            score=analysis.overall_score,
            grade=analysis.grade,
            components=analysis.components,
            rule_results=[r.to_dict() for r in analysis.rule_results],
            query_count=len(analysis.rule_results),  # 20 rules evaluated
            pass_rate=pass_rate,
            avg_latency_ms=0,  # Not applicable for rule-based analysis
            page_count=len(pages),
            top_issues=analysis.top_issues,
            estimated_price_eur=report_price,
        )
        db.add(assessment)
        await db.flush()
        await db.refresh(assessment)

        return _build_response(assessment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment failed for {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Assessment failed. Please try again.")


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a previously completed assessment."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return _build_response(assessment)


@router.post("/{assessment_id}/verify-promo")
async def verify_promo_code(
    assessment_id: str,
    request: PromoCodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Verify a promo code, unlock the assessment, and trigger optimization."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    valid_promos = {"AGENT2025", "LAUNCH2025", "BETA2025"}
    if request.code.upper() not in valid_promos:
        raise HTTPException(status_code=400, detail="Invalid promo code")

    assessment.has_paid = True
    assessment.paid_plan = "promo"
    assessment.optimization_status = "queued"
    await db.flush()

    # Trigger optimization in background (same pipeline as paid flow)
    from routers.payments import _run_optimization_pipeline
    background_tasks.add_task(
        _run_optimization_pipeline,
        assessment_id,
        assessment.url,
    )

    return {"success": True, "message": "Promo code applied! Your optimized docs are being generated."}


@router.get("/{assessment_id}/optimization-status")
async def get_optimization_status(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Poll optimization progress."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.has_paid:
        raise HTTPException(status_code=403, detail="Payment required")

    return {
        "status": assessment.optimization_status or "pending",
        "progress": assessment.optimization_progress,
        "stage": assessment.optimization_stage,
        "metadata": assessment.optimization_metadata,
        "error": assessment.optimization_error,
    }


@router.get("/{assessment_id}/download")
async def download_optimized_docs(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Download the optimized documentation ZIP."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if not assessment.has_paid:
        raise HTTPException(status_code=403, detail="Payment required")

    if assessment.optimization_status != "complete":
        raise HTTPException(status_code=400, detail="Optimization not yet complete")

    zip_path = assessment.optimization_zip_path
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Optimized docs file not found")

    filename = f"{assessment.site_name}-optimized-docs.zip"
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=filename,
    )


def _build_response(assessment: Assessment) -> AssessmentResponse:
    """Build a consistent AssessmentResponse from an Assessment model."""
    return AssessmentResponse(
        id=assessment.id,
        url=assessment.url,
        site_name=assessment.site_name,
        score=assessment.score,
        grade=assessment.grade,
        components=assessment.components,
        rule_results=assessment.rule_results or [],
        query_count=assessment.query_count,
        pass_rate=assessment.pass_rate,
        avg_latency_ms=assessment.avg_latency_ms,
        page_count=assessment.page_count,
        top_issues=assessment.top_issues,
        estimated_price_eur=assessment.estimated_price_eur,
        has_paid=assessment.has_paid,
        optimization_status=assessment.optimization_status,
        optimization_progress=assessment.optimization_progress,
        optimization_stage=assessment.optimization_stage,
        optimization_metadata=assessment.optimization_metadata,
        created_at=assessment.created_at.isoformat(),
    )
