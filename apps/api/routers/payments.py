"""
Payments Router

Stripe integration for handling payments.
After successful payment, triggers the documentation optimization pipeline
to generate the customer's optimized docs (ZIP download).
"""

from fastapi import APIRouter, HTTPException, Request, Header, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import logging
from datetime import datetime, timezone

from database import get_db, async_session_factory
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
        raise HTTPException(status_code=400, detail="Already purchased")

    price_eur = assessment.estimated_price_eur
    amount_cents = price_eur * 100  # Stripe uses cents

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Optimized Documentation",
                        "description": (
                            f"AI-optimized documentation for {assessment.site_name} "
                            f"({assessment.page_count} pages) — ready to deploy"
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
                "page_count": str(assessment.page_count),
                "price_eur": str(price_eur),
            },
        )

        return {"session_id": checkout_session.id, "url": checkout_session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
async def verify_payment(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Verify a payment was successful and kick off documentation optimization."""
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
                    assessment.paid_plan = "optimized_docs"
                    assessment.stripe_session_id = session_id
                    assessment.optimization_status = "queued"
                    await db.flush()

                    # Trigger optimization in background
                    background_tasks.add_task(
                        _run_optimization_pipeline,
                        assessment_id,
                        assessment.url,
                    )

            return {
                "paid": True,
                "amount": session.amount_total,
                "currency": session.currency,
                "assessment_id": assessment_id,
                "optimization_status": "queued",
            }

        return {"paid": False, "status": session.payment_status}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
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
            if assessment and not assessment.has_paid:
                assessment.has_paid = True
                assessment.paid_plan = "optimized_docs"
                assessment.stripe_session_id = session.get("id")
                assessment.optimization_status = "queued"
                await db.flush()

                background_tasks.add_task(
                    _run_optimization_pipeline,
                    assessment_id,
                    assessment.url,
                )
                logger.info(f"Optimization queued for assessment {assessment_id}")

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


async def _run_optimization_pipeline(assessment_id: str, url: str):
    """
    Run the full documentation optimization pipeline in background.

    Uses its own DB session since this runs outside the request lifecycle.
    Applies all 20 agent-readiness rules to every page, generates a ZIP,
    and stores it at a persistent path (not /tmp).
    """
    import os
    from pathlib import Path
    from services.optimizer.document_optimizer import DocumentationOptimizer

    logger.info(f"Starting optimization for assessment {assessment_id}")

    # Validate OpenAI key before starting expensive work
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key or openai_key == "sk-your-openai-key":
        logger.error(f"Optimization aborted for {assessment_id}: OPENAI_API_KEY not configured")
        async with async_session_factory() as db:
            result = await db.execute(
                select(Assessment).where(Assessment.id == assessment_id)
            )
            assessment = result.scalar_one_or_none()
            if assessment:
                assessment.optimization_status = "failed"
                assessment.optimization_error = "Service configuration error. Please contact support."
                await db.commit()
        return

    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Assessment).where(Assessment.id == assessment_id)
            )
            assessment = result.scalar_one_or_none()
            if not assessment:
                logger.error(f"Assessment {assessment_id} not found")
                return

            assessment.optimization_status = "running"
            assessment.optimization_started_at = datetime.now(timezone.utc)
            await db.commit()

            # No config needed — optimizer always applies all 20 rules
            optimizer = DocumentationOptimizer()

            async def progress_callback(stage: str, progress: float):
                """Update DB with real-time progress so frontend can poll."""
                try:
                    async with async_session_factory() as progress_db:
                        r = await progress_db.execute(
                            select(Assessment).where(Assessment.id == assessment_id)
                        )
                        a = r.scalar_one_or_none()
                        if a:
                            a.optimization_progress = progress
                            a.optimization_stage = stage
                            await progress_db.commit()
                except Exception:
                    pass  # Progress updates are best-effort

            docs, metadata = await optimizer.optimize_documentation(
                url, progress_callback=progress_callback
            )
            zip_path = await optimizer.create_zip_package(docs, metadata)

            # Move ZIP to persistent storage directory (survives container restarts)
            persist_dir = Path("/opt/render/project/src/data/zips")
            if "RENDER" in os.environ:
                persist_dir.mkdir(parents=True, exist_ok=True)
            else:
                persist_dir = Path("./data/zips")
                persist_dir.mkdir(parents=True, exist_ok=True)

            import shutil
            persistent_path = str(persist_dir / f"{assessment_id}.zip")
            shutil.move(zip_path, persistent_path)

            # Update assessment with results
            result = await db.execute(
                select(Assessment).where(Assessment.id == assessment_id)
            )
            assessment = result.scalar_one_or_none()
            if assessment:
                assessment.optimization_status = "complete"
                assessment.optimization_progress = 1.0
                assessment.optimization_stage = "complete"
                assessment.optimization_zip_path = persistent_path
                assessment.optimization_metadata = metadata
                assessment.optimization_completed_at = datetime.now(timezone.utc)
                await db.commit()

            logger.info(f"Optimization complete for {assessment_id}: {len(docs)} pages optimized")

        except Exception as e:
            logger.error(f"Optimization failed for {assessment_id}: {e}", exc_info=True)
            try:
                result = await db.execute(
                    select(Assessment).where(Assessment.id == assessment_id)
                )
                assessment = result.scalar_one_or_none()
                if assessment:
                    assessment.optimization_status = "failed"
                    assessment.optimization_error = str(e)[:500]
                    await db.commit()
            except Exception:
                logger.error(f"Failed to update error status for {assessment_id}")
