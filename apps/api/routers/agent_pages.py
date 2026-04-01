"""
Agent Pages Router

Public endpoints for generating and viewing agent-ready documentation pages.
"""

import re
import random
import string
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from database import get_db
from models import AgentPage
from config import get_settings
from services.agent_page_generator import (
    generate_agent_page,
    render_generating_html,
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
stripe.api_key = settings.stripe_secret_key


# --- Request / Response models ---

class GenerateRequest(BaseModel):
    product_name: str
    docs_url: str
    email: str


class UnlockRequest(BaseModel):
    success_url: str
    cancel_url: str


class VerifyPaymentRequest(BaseModel):
    session_id: str


class PromoRequest(BaseModel):
    code: str


# --- Helpers ---

def _slugify(name: str) -> str:
    """Generate a URL-safe slug from a product name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "product"


def _random_suffix(length: int = 4) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


# --- Endpoints ---
# NOTE: /featured/list must be defined BEFORE /{slug} to avoid route conflicts.

@router.get("/featured/list")
async def featured_list(db: AsyncSession = Depends(get_db)):
    """Return list of featured / example agent pages."""
    result = await db.execute(
        select(AgentPage).where(
            or_(
                AgentPage.status == "full_ready",
                AgentPage.status == "draft_ready",
            )
        ).order_by(AgentPage.created_at)
    )
    pages = result.scalars().all()

    return [
        {
            "product_name": p.product_name,
            "slug": p.company_slug,
            "status": p.status,
            "payment_status": p.payment_status,
        }
        for p in pages
    ]


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create an agent page and start draft generation in the background."""
    slug = _slugify(request.product_name)

    # Check if slug exists
    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.email == request.email:
            # Same user, return existing
            return {"id": existing.id, "slug": existing.company_slug, "status": existing.status}
        else:
            # Different user, append suffix
            slug = f"{slug}-{_random_suffix()}"

    agent_page = AgentPage(
        product_name=request.product_name,
        company_slug=slug,
        docs_url=request.docs_url,
        email=request.email,
        status="submitted",
    )
    db.add(agent_page)
    await db.flush()
    await db.refresh(agent_page)

    page_id = agent_page.id

    background_tasks.add_task(generate_agent_page, page_id, "draft")

    return {"id": page_id, "slug": slug, "status": "submitted"}


@router.get("/{slug}")
async def get_agent_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Return agent page metadata."""
    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    return {
        "id": agent_page.id,
        "product_name": agent_page.product_name,
        "slug": agent_page.company_slug,
        "status": agent_page.status,
        "payment_status": agent_page.payment_status,
        "created_at": agent_page.created_at.isoformat() if agent_page.created_at else None,
    }


@router.get("/{slug}/view", response_class=HTMLResponse)
async def view_agent_page(slug: str, db: AsyncSession = Depends(get_db)):
    """Return the rendered HTML for the agent page."""
    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    # Still generating
    if agent_page.status in ("submitted", "crawling", "generating", "full_generating"):
        return HTMLResponse(
            content=render_generating_html(agent_page.product_name, slug),
            status_code=200,
        )

    # Determine which HTML to serve
    if agent_page.payment_status == "paid" and agent_page.full_html:
        html = agent_page.full_html
    elif agent_page.draft_html:
        html = agent_page.draft_html
    else:
        raise HTTPException(status_code=404, detail="No rendered page available")

    return HTMLResponse(content=html, status_code=200)


@router.get("/{slug}/status")
async def get_status(slug: str, db: AsyncSession = Depends(get_db)):
    """Return current status of an agent page."""
    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    return {
        "status": agent_page.status,
        "payment_status": agent_page.payment_status,
        "has_draft": agent_page.draft_html is not None,
        "has_full": agent_page.full_html is not None,
    }


@router.post("/{slug}/unlock")
async def unlock(
    slug: str,
    request: UnlockRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session to unlock the full agent page ($99)."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    if agent_page.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Already unlocked")

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Full Agent Page — {agent_page.product_name}",
                        "description": "Complete agent-ready documentation with all sections, workflows, and references.",
                    },
                    "unit_amount": 9900,  # $99
                },
                "quantity": 1,
            }],
            mode="payment",
            allow_promotion_codes=True,
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "agent_page_slug": slug,
                "agent_page_id": agent_page.id,
            },
        )

        return {"session_id": checkout_session.id, "url": checkout_session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


@router.post("/{slug}/verify-payment")
async def verify_payment(
    slug: str,
    request: VerifyPaymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Verify Stripe payment and trigger full generation if needed."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    try:
        session = stripe.checkout.Session.retrieve(request.session_id)

        if session.payment_status == "paid":
            agent_page.payment_status = "paid"
            await db.commit()

            # Trigger full generation if no full HTML yet
            if not agent_page.full_html:
                background_tasks.add_task(generate_agent_page, agent_page.id, "full")

            return {"paid": True, "status": agent_page.status}

        return {"paid": False, "status": session.payment_status}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying payment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{slug}/apply-promo")
async def apply_promo(
    slug: str,
    request: PromoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Apply a promo code. FREE100 bypasses payment entirely."""
    result = await db.execute(
        select(AgentPage).where(AgentPage.company_slug == slug)
    )
    agent_page = result.scalar_one_or_none()
    if not agent_page:
        raise HTTPException(status_code=404, detail="Agent page not found")

    code = request.code.upper().strip()

    if code != "FREE100":
        raise HTTPException(status_code=400, detail="Invalid promo code")

    # FREE100: bypass payment, mark paid, trigger full generation
    agent_page.payment_status = "paid"
    await db.commit()

    if not agent_page.full_html:
        background_tasks.add_task(generate_agent_page, agent_page.id, "full")

    return {"success": True, "free": True}
