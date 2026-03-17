"""
Payments Router

Stripe integration for handling payments.
Dynamic pricing model: price scales with documentation size (3x API cost, min €49).
Uses Stripe's price_data for dynamic amounts — no pre-created Price objects needed.
"""

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import logging

from database import get_db
from models import Assessment
from config import get_settings
from auth import get_optional_user

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


class CreateCheckoutRequest(BaseModel):
    assessment_id: str
    success_url: str
    cancel_url: str


@router.post("/create-checkout")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe checkout session with dynamic pricing.
    The price is determined by the assessment's page_count (stored at scan time).
    """
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    # Look up the assessment to get the calculated price
    result = await db.execute(
        select(Assessment).where(Assessment.id == request.assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.has_paid:
        raise HTTPException(status_code=400, detail="Report already purchased")

    price_eur = assessment.estimated_price_eur
    amount_cents = price_eur * 100  # Stripe uses cents

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Agent-Readiness Report",
                        "description": (
                            f"Complete playbook for {assessment.site_name} "
                            f"({assessment.page_count} pages analysed)"
                        ),
                    },
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "assessment_id": request.assessment_id,
                "plan": "report",
                "page_count": str(assessment.page_count),
                "price_eur": str(price_eur),
            },
        )

        return {"session_id": checkout_session.id, "url": checkout_session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
async def verify_payment(session_id: str, db: AsyncSession = Depends(get_db)):
    """Verify a payment was successful and unlock the report."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            assessment_id = session.metadata.get("assessment_id")

            if assessment_id:
                result = await db.execute(
                    select(Assessment).where(Assessment.id == assessment_id)
                )
                assessment = result.scalar_one_or_none()
                if assessment:
                    assessment.has_paid = True
                    assessment.paid_plan = "report"
                    assessment.stripe_session_id = session_id
                    await db.flush()

            return {
                "paid": True,
                "amount": session.amount_total,
                "currency": session.currency,
                "plan": "report",
                "assessment_id": assessment_id,
            }

        return {"paid": False, "status": session.payment_status}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhooks."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        assessment_id = session.get("metadata", {}).get("assessment_id")

        if assessment_id:
            result = await db.execute(
                select(Assessment).where(Assessment.id == assessment_id)
            )
            assessment = result.scalar_one_or_none()
            if assessment:
                assessment.has_paid = True
                assessment.paid_plan = "report"
                assessment.stripe_session_id = session.get("id")
                await db.flush()
                logger.info(f"Report unlocked for assessment {assessment_id}")

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        logger.warning(f"Payment failed: {payment_intent.get('id')}")

    return JSONResponse(content={"status": "success"})


@router.get("/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend."""
    return {
        "publishable_key": settings.stripe_publishable_key or None,
    }
