"""
Analyses Router

API endpoints for managing and retrieving analysis results.
Uses database persistence.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Analysis, AnalysisStatus, User, utcnow
from auth import get_current_user

router = APIRouter()


# --- Schemas ---

class AnalysisResponse(BaseModel):
    id: str
    site_id: str
    status: str
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreResponse(BaseModel):
    overall: int
    grade: str
    components: dict
    query_count: int
    pass_rate: float
    avg_latency_ms: int


class ProgressResponse(BaseModel):
    status: str
    progress: int
    current_stage: Optional[str] = None
    page_count: Optional[int] = None
    processed_pages: Optional[int] = None


STAGES = [
    "Discovering pages",
    "Analyzing structure",
    "Simulating queries",
    "Calculating score",
]


@router.get("", response_model=list[AnalysisResponse])
async def list_analyses(
    site_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List analysis runs with optional filtering and pagination."""
    query = select(Analysis).join(Analysis.site).where(
        Analysis.site.has(organization_id=user.organization_id)
    )

    if site_id:
        query = query.where(Analysis.site_id == site_id)
    if status:
        query = query.where(Analysis.status == status)

    query = query.order_by(Analysis.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific analysis run."""
    analysis = await _get_user_analysis(analysis_id, user, db)
    return analysis


@router.get("/{analysis_id}/progress", response_model=ProgressResponse)
async def get_analysis_progress(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the progress of an in-progress analysis."""
    analysis = await _get_user_analysis(analysis_id, user, db)

    current_stage = analysis.current_stage
    if not current_stage and analysis.status == AnalysisStatus.RUNNING.value:
        stage_index = min(analysis.progress // 25, len(STAGES) - 1)
        current_stage = STAGES[stage_index]

    return ProgressResponse(
        status=analysis.status,
        progress=analysis.progress,
        current_stage=current_stage if analysis.status == AnalysisStatus.RUNNING.value else None,
        page_count=analysis.page_count,
        processed_pages=analysis.processed_pages,
    )


@router.get("/{analysis_id}/score", response_model=ScoreResponse)
async def get_analysis_score(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the composite score for a completed analysis."""
    analysis = await _get_user_analysis(analysis_id, user, db)

    if analysis.overall_score is None:
        raise HTTPException(status_code=404, detail="Score not yet available")

    return ScoreResponse(
        overall=analysis.overall_score,
        grade=analysis.grade,
        components=analysis.components or {},
        query_count=analysis.query_count or 0,
        pass_rate=analysis.pass_rate or 0.0,
        avg_latency_ms=analysis.avg_latency_ms or 0,
    )


@router.post("/{analysis_id}/cancel")
async def cancel_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an in-progress analysis."""
    analysis = await _get_user_analysis(analysis_id, user, db)

    if analysis.status not in [AnalysisStatus.QUEUED.value, AnalysisStatus.RUNNING.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel analysis with status: {analysis.status}",
        )

    analysis.status = AnalysisStatus.CANCELLED.value
    await db.flush()

    return {"message": "Analysis cancelled successfully"}


@router.get("/{analysis_id}/compare")
async def compare_analysis(
    analysis_id: str,
    compare_to: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare analysis results with a previous analysis."""
    analysis = await _get_user_analysis(analysis_id, user, db)

    if analysis.overall_score is None:
        raise HTTPException(status_code=404, detail="Score not yet available")

    # Find previous analysis for comparison
    previous = None
    if compare_to:
        previous = await _get_user_analysis(compare_to, user, db)
    else:
        result = await db.execute(
            select(Analysis)
            .where(
                Analysis.site_id == analysis.site_id,
                Analysis.id != analysis_id,
                Analysis.status == AnalysisStatus.COMPLETED.value,
                Analysis.overall_score.is_not(None),
            )
            .order_by(Analysis.completed_at.desc())
            .limit(1)
        )
        previous = result.scalar_one_or_none()

    current_score = {
        "overall": analysis.overall_score,
        "components": analysis.components or {},
    }

    if previous and previous.overall_score is not None:
        previous_score = {
            "overall": previous.overall_score,
            "components": previous.components or {},
        }
        delta = {
            "overall": current_score["overall"] - previous_score["overall"],
            "components": {
                k: current_score["components"].get(k, 0) - previous_score["components"].get(k, 0)
                for k in current_score["components"]
            },
        }
        return {"current": current_score, "previous": previous_score, "delta": delta}

    return {"current": current_score, "previous": None, "delta": None}


async def _get_user_analysis(analysis_id: str, user: User, db: AsyncSession) -> Analysis:
    """Get an analysis, ensuring it belongs to the user's organization."""
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id).join(Analysis.site).where(
            Analysis.site.has(organization_id=user.organization_id)
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
