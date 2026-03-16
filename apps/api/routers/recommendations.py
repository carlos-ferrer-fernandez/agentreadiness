"""
Recommendations Router

API endpoints for managing improvement recommendations.
Uses database persistence.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Recommendation, RecommendationStatus, Site, User, utcnow
from auth import get_current_user

router = APIRouter()


class RecommendationResponse(BaseModel):
    id: str
    site_id: str
    priority: int
    impact: str
    effort: str
    category: str
    title: str
    description: str
    affected_pages: list[dict]
    before_example: Optional[str] = None
    after_example: Optional[str] = None
    estimated_score_improvement: Optional[float] = None
    implementation_status: str

    model_config = {"from_attributes": True}


class RecommendationUpdate(BaseModel):
    implementation_status: Optional[str] = None


@router.get("/site/{site_id}", response_model=list[RecommendationResponse])
async def list_recommendations(
    site_id: str,
    category: Optional[str] = None,
    impact: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recommendations for a site with filtering."""
    # Verify the user owns this site
    site_result = await db.execute(
        select(Site).where(Site.id == site_id, Site.organization_id == user.organization_id)
    )
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Site not found")

    query = select(Recommendation).where(Recommendation.site_id == site_id)
    if category:
        query = query.where(Recommendation.category == category)
    if impact:
        query = query.where(Recommendation.impact == impact)
    if status:
        query = query.where(Recommendation.implementation_status == status)
    query = query.order_by(Recommendation.priority)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific recommendation."""
    rec = await _get_user_recommendation(recommendation_id, user, db)
    return rec


@router.patch("/{recommendation_id}")
async def update_recommendation(
    recommendation_id: str,
    update: RecommendationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a recommendation (e.g., mark as implemented)."""
    rec = await _get_user_recommendation(recommendation_id, user, db)

    if update.implementation_status:
        valid_statuses = [s.value for s in RecommendationStatus]
        if update.implementation_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )
        rec.implementation_status = update.implementation_status
        rec.updated_at = utcnow()
        await db.flush()

    return {"message": "Recommendation updated successfully"}


@router.post("/{recommendation_id}/create-ticket")
async def create_ticket(
    recommendation_id: str,
    integration: str = "github",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a ticket in external system (GitHub, Jira, etc.)."""
    rec = await _get_user_recommendation(recommendation_id, user, db)

    # TODO: Implement actual GitHub/Jira ticket creation via API
    import uuid
    ticket_id = f"{integration.upper()}-{uuid.uuid4().hex[:8]}"

    return {
        "ticket_id": ticket_id,
        "integration": integration,
        "url": f"https://github.com/org/repo/issues/{ticket_id}",
        "title": rec.title,
        "description": rec.description,
    }


async def _get_user_recommendation(
    recommendation_id: str, user: User, db: AsyncSession
) -> Recommendation:
    """Get a recommendation, ensuring it belongs to the user's organization."""
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.id == recommendation_id)
        .join(Recommendation.site)
        .where(Site.organization_id == user.organization_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec
