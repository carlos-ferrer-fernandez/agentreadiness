"""
Assessments Router

Public endpoints for the free assessment flow (no auth required).
This is the main entry point for new users landing on the site.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from database import get_db
from models import Assessment
from config import get_settings
from pricing import calculate_report_price

router = APIRouter()
settings = get_settings()


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
    Crawls the site, scores it, and returns results.
    """
    from services.crawler.crawler import DocumentationCrawler
    from services.evaluator.scorer import FriendlinessScorer, QueryResult
    from urllib.parse import urlparse
    import logging

    logger = logging.getLogger(__name__)
    url = str(request.url)
    parsed = urlparse(url)
    site_name = parsed.netloc.replace("www.", "")

    try:
        # Crawl (limited to 30 pages for free assessment)
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

        # Generate synthetic query results from crawled content
        query_results = []
        for page in pages:
            content_length = len(page.content) if page.content else 0
            has_code = bool(page.code_blocks)
            has_headings = bool(page.heading_hierarchy and len(page.heading_hierarchy) >= 2)

            accuracy = min(1.0, 0.5 + (content_length / 5000) * 0.3 + (0.2 if has_code else 0))
            precision = min(1.0, 0.4 + (0.3 if has_headings else 0) + (content_length / 8000) * 0.3)
            latency = 800 + max(0, content_length // 10)
            citation = min(1.0, 0.7 + (0.2 if has_headings else 0) + (0.1 if page.links else 0))

            query_results.append(QueryResult(
                query=f"Query about: {page.title or page.url}",
                passed=accuracy > 0.6,
                confidence=accuracy,
                accuracy_score=accuracy,
                retrieval_precision=precision,
                latency_ms=min(latency, 5000),
                citation_accuracy=citation,
                code_valid=has_code,
            ))

        # Score
        scorer = FriendlinessScorer()
        score = scorer.calculate_score(query_results)

        # Generate top issues
        top_issues = _generate_top_issues(score)

        # Calculate dynamic price based on doc size
        report_price = calculate_report_price(len(pages))

        # Persist assessment
        assessment = Assessment(
            url=url,
            site_name=site_name,
            email=request.email,
            score=score.overall,
            grade=score.grade,
            components=score.components,
            query_count=score.query_count,
            pass_rate=score.pass_rate,
            avg_latency_ms=score.avg_latency_ms,
            page_count=len(pages),
            top_issues=top_issues,
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

    return AssessmentResponse(
        id=assessment.id,
        url=assessment.url,
        site_name=assessment.site_name,
        score=assessment.score,
        grade=assessment.grade,
        components=assessment.components,
        query_count=assessment.query_count,
        pass_rate=assessment.pass_rate,
        avg_latency_ms=assessment.avg_latency_ms,
        page_count=assessment.page_count,
        top_issues=assessment.top_issues,
        estimated_price_eur=assessment.estimated_price_eur,
        has_paid=assessment.has_paid,
        created_at=assessment.created_at.isoformat(),
    )


@router.post("/{assessment_id}/verify-promo")
async def verify_promo_code(
    assessment_id: str,
    request: PromoCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify a promo code and unlock the assessment. Code is validated server-side only."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Promo codes are stored server-side, not exposed to the client
    valid_promos = {"AGENT2025", "LAUNCH2025", "BETA2025"}
    if request.code.upper() not in valid_promos:
        raise HTTPException(status_code=400, detail="Invalid promo code")

    assessment.has_paid = True
    assessment.paid_plan = "promo"
    await db.flush()

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


def _generate_top_issues(score) -> list[dict]:
    """Generate top 3 issues based on component scores."""
    issues = []
    components = score.components

    if components.get("accuracy", 100) < 70:
        issues.append({
            "category": "content",
            "title": "Documentation lacks sufficient detail for accurate AI responses",
            "severity": "high",
        })
    if components.get("code_executability", 100) < 70:
        issues.append({
            "category": "code",
            "title": "Code examples are missing or contain errors",
            "severity": "high",
        })
    if components.get("context_utilization", 100) < 80:
        issues.append({
            "category": "structure",
            "title": "Documentation structure needs improvement for better AI context retrieval",
            "severity": "medium",
        })
    if components.get("citation_quality", 100) < 80:
        issues.append({
            "category": "metadata",
            "title": "Pages lack clear titles and descriptions for citation",
            "severity": "medium",
        })
    if components.get("latency", 100) < 80:
        issues.append({
            "category": "performance",
            "title": "Page content is too large, slowing agent response times",
            "severity": "low",
        })

    if not issues:
        issues.append({
            "category": "optimization",
            "title": "Minor optimizations available for a perfect score",
            "severity": "low",
        })

    return issues[:3]
