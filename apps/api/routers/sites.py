"""
Sites Router

API endpoints for managing documentation sites.
Uses database persistence and real authentication.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Site, SiteStatus, Analysis, AnalysisStatus, User, utcnow
from auth import get_current_user
from services.analysis_pipeline import run_analysis_pipeline

router = APIRouter()


# --- Schemas ---

class SiteCreate(BaseModel):
    url: HttpUrl
    name: str
    sitemap_url: Optional[HttpUrl] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None


class SiteResponse(BaseModel):
    id: str
    url: str
    name: str
    status: str
    organization_id: str
    page_count: Optional[int] = None
    last_crawled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VerificationRequest(BaseModel):
    method: str  # "meta_tag" or "dns_txt"
    token: str


# --- Endpoints ---

@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(
    site: SiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new documentation site."""
    new_site = Site(
        url=str(site.url),
        name=site.name,
        organization_id=user.organization_id,
        sitemap_url=str(site.sitemap_url) if site.sitemap_url else None,
    )
    db.add(new_site)
    await db.flush()
    await db.refresh(new_site)
    return new_site


@router.get("", response_model=list[SiteResponse])
async def list_sites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documentation sites for the user's organization."""
    result = await db.execute(
        select(Site)
        .where(Site.organization_id == user.organization_id)
        .order_by(Site.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific documentation site."""
    return await _get_user_site(site_id, user, db)


@router.patch("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    update: SiteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a documentation site."""
    site = await _get_user_site(site_id, user, db)
    if update.name is not None:
        site.name = update.name
    site.updated_at = utcnow()
    await db.flush()
    await db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a documentation site and all associated data."""
    site = await _get_user_site(site_id, user, db)
    await db.delete(site)


@router.post("/{site_id}/verify")
async def verify_site(
    site_id: str,
    request: VerificationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify site ownership using meta tag or DNS TXT record."""
    site = await _get_user_site(site_id, user, db)

    if request.token != site.verification_token:
        raise HTTPException(status_code=400, detail="Verification token mismatch")

    site.status = SiteStatus.VERIFIED.value
    site.updated_at = utcnow()
    await db.flush()
    await db.refresh(site)

    return {
        "verified": True,
        "message": "Site verified successfully",
        "site": SiteResponse.model_validate(site),
    }


@router.post("/{site_id}/analyze")
async def analyze_site(
    site_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full analysis of the documentation site."""
    site = await _get_user_site(site_id, user, db)

    if site.status not in [SiteStatus.VERIFIED.value, SiteStatus.READY.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot analyze site with status: {site.status}. Verify the site first.",
        )

    analysis = Analysis(site_id=site.id, status=AnalysisStatus.QUEUED.value)
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    background_tasks.add_task(run_analysis_pipeline, analysis.id, site.url)

    return {
        "analysis_id": analysis.id,
        "status": "QUEUED",
        "message": "Analysis queued successfully",
    }


@router.get("/{site_id}/verification-token")
async def get_verification_token(
    site_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the verification token for a site."""
    site = await _get_user_site(site_id, user, db)
    return {
        "token": site.verification_token,
        "meta_tag": f'<meta name="agentreadiness-verification" content="{site.verification_token}">',
        "dns_txt": f"agentreadiness-verification={site.verification_token}",
    }


async def _get_user_site(site_id: str, user: User, db: AsyncSession) -> Site:
    """Get a site, ensuring it belongs to the user's organization."""
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.organization_id == user.organization_id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site
