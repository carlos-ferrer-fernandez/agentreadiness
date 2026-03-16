"""
Payments Router

Stripe integration for handling payments.
Uses settings for configuration instead of raw os.getenv.
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

PRICE_IDS = {
    "starter": settings.stripe_starter_price_id,
    "growth": settings.stripe_growth_price_id,
}


class CreateCheckoutRequest(BaseModel):
    plan: str  # 'starter' or 'growth'
    assessment_id: str
    success_url: str
    cancel_url: str


@router.post("/create-checkout")
async def create_checkout_session(request: CreateCheckoutRequest):
    """Create a Stripe checkout session."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    price_id = PRICE_IDS.get(request.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan. Must be 'starter' or 'growth'.")

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "assessment_id": request.assessment_id,
                "plan": request.plan,
            },
        )

        return {"session_id": checkout_session.id, "url": checkout_session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
async def verify_payment(session_id: str, db: AsyncSession = Depends(get_db)):
    """Verify a payment was successful and unlock the assessment."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            # Update the assessment in the database
            assessment_id = session.metadata.get("assessment_id")
            plan = session.metadata.get("plan")

            if assessment_id:
                result = await db.execute(
                    select(Assessment).where(Assessment.id == assessment_id)
                )
                assessment = result.scalar_one_or_none()
                if assessment:
                    assessment.has_paid = True
                    assessment.paid_plan = plan
                    assessment.stripe_session_id = session_id
                    await db.flush()

            return {
                "paid": True,
                "amount": session.amount_total,
                "currency": session.currency,
                "plan": plan,
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
        plan = session.get("metadata", {}).get("plan")

        if assessment_id:
            result = await db.execute(
                select(Assessment).where(Assessment.id == assessment_id)
            )
            assessment = result.scalar_one_or_none()
            if assessment:
                assessment.has_paid = True
                assessment.paid_plan = plan
                assessment.stripe_session_id = session.get("id")
                await db.flush()
                logger.info(f"Payment completed for assessment {assessment_id}, plan={plan}")

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        logger.warning(f"Payment failed: {payment_intent.get('id')}")

    return JSONResponse(content={"status": "success"})


@router.get("/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend."""
    return {
        "publishable_key": settings.stripe_publishable_key or None,
        "prices": {
            "starter": settings.stripe_starter_price_id,
            "growth": settings.stripe_growth_price_id,
        },
    }
