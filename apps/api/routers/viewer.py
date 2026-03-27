"""
Public Viewer Router

Serves hosted optimization results at shareable URLs.
All endpoints are public (no auth) — source docs were already public.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Assessment

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/public")
async def list_public_optimizations(db: AsyncSession = Depends(get_db)):
    """List showcase-worthy optimizations for the gallery page."""
    result = await db.execute(
        select(Assessment)
        .where(and_(
            Assessment.has_paid == True,
            Assessment.optimization_status == "complete",
        ))
        .order_by(Assessment.created_at.desc())
        .limit(24)
    )
    assessments = result.scalars().all()

    return [
        {
            "id": a.id,
            "site_name": a.site_name,
            "url": a.url,
            "score": a.score,
            "grade": a.grade,
            "page_count": len(a.optimization_docs) if a.optimization_docs else 0,
            "created_at": a.created_at.isoformat(),
        }
        for a in assessments
    ]


@router.get("/{assessment_id}")
async def get_viewer_index(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Return optimization metadata and page list for the viewer."""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    if not assessment.has_paid or assessment.optimization_status != "complete":
        raise HTTPException(status_code=403, detail="Optimization not available")

    docs = assessment.optimization_docs or []
    if isinstance(docs, str):
        docs = json.loads(docs)

    pages = [
        {
            "file_name": d["file_name"],
            "title": d["title"],
            "original_url": d["original_url"],
            "improvements": d.get("improvements", []),
        }
        for d in docs
    ]

    return {
        "id": assessment.id,
        "site_name": assessment.site_name,
        "url": assessment.url,
        "score": assessment.score,
        "grade": assessment.grade,
        "pages": pages,
        "created_at": assessment.created_at.isoformat(),
    }


@router.get("/{assessment_id}/{file_name}")
async def get_optimized_page(
    assessment_id: str,
    file_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a single optimized page's content."""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Not found")
    if not assessment.has_paid or assessment.optimization_status != "complete":
        raise HTTPException(status_code=403, detail="Optimization not available")

    docs = assessment.optimization_docs or []
    if isinstance(docs, str):
        docs = json.loads(docs)

    page = next((d for d in docs if d["file_name"] == file_name), None)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "title": page["title"],
        "original_url": page["original_url"],
        "optimized_content": page["optimized_content"],
        "improvements": page.get("improvements", []),
        "site_name": assessment.site_name,
        "assessment_id": assessment_id,
    }
