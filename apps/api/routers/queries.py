"""
Queries Router

API endpoints for retrieving and analyzing query results.
Uses database persistence.
"""

from fastapi import APIRouter, HTTPException, Query as FastAPIQuery, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import QueryResult, Analysis, Site, User
from auth import get_current_user

router = APIRouter()


class QueryResponse(BaseModel):
    id: str
    query_text: str
    category: str
    difficulty: str
    passed: bool
    confidence: float
    generated_response: Optional[str] = None
    expected_answer: Optional[str] = None
    retrieved_chunks: Optional[list[dict]] = None

    model_config = {"from_attributes": True}


class QueryListResponse(BaseModel):
    id: str
    query_text: str
    category: str
    difficulty: str
    passed: bool
    confidence: float

    model_config = {"from_attributes": True}


@router.get("/analysis/{analysis_id}", response_model=list[QueryListResponse])
async def list_queries(
    analysis_id: str,
    category: Optional[str] = FastAPIQuery(None),
    difficulty: Optional[str] = FastAPIQuery(None),
    status: Optional[str] = FastAPIQuery(None),
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List query results for an analysis with filtering and pagination."""
    # Verify the user owns this analysis
    analysis_result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id)
        .join(Analysis.site)
        .where(Site.organization_id == user.organization_id)
    )
    if not analysis_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found")

    query = select(QueryResult).where(QueryResult.analysis_id == analysis_id)

    if category:
        query = query.where(QueryResult.category == category)
    if difficulty:
        query = query.where(QueryResult.difficulty == difficulty)
    if status == "pass":
        query = query.where(QueryResult.passed == True)
    elif status == "fail":
        query = query.where(QueryResult.passed == False)
    elif status == "borderline":
        query = query.where(QueryResult.confidence.between(0.4, 0.6))

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed results for a specific query."""
    result = await db.execute(
        select(QueryResult).where(QueryResult.id == query_id)
        .join(QueryResult.analysis)
        .join(Analysis.site)
        .where(Site.organization_id == user.organization_id)
    )
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=404, detail="Query not found")
    return qr


@router.post("/analysis/{analysis_id}/export")
async def export_queries(
    analysis_id: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export query results as JSON."""
    query = select(QueryResult).where(QueryResult.analysis_id == analysis_id)

    if category:
        query = query.where(QueryResult.category == category)
    if status == "pass":
        query = query.where(QueryResult.passed == True)
    elif status == "fail":
        query = query.where(QueryResult.passed == False)

    result = await db.execute(query)
    queries = result.scalars().all()

    return {
        "format": "json",
        "count": len(queries),
        "data": [
            {
                "id": q.id,
                "query_text": q.query_text,
                "category": q.category,
                "difficulty": q.difficulty,
                "passed": q.passed,
                "confidence": q.confidence,
            }
            for q in queries
        ],
    }
