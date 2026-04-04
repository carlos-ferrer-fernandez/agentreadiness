"""
Packages Router

Public endpoints for generating and viewing AI-ready documentation packages.
"""

import io
import json
import re
import random
import string
import logging
import zipfile
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from database import get_db
from models import DocPackage
from config import get_settings
from services.package_generator import generate_package
from services.package_renderer import render_generating_package_html

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
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "product"


def _random_suffix(length: int = 4) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


# --- Endpoints ---
# NOTE: /examples must be defined BEFORE /{slug} to avoid route conflicts.

@router.get("/examples")
async def examples_list(db: AsyncSession = Depends(get_db)):
    """Return list of seed example packages."""
    result = await db.execute(
        select(DocPackage).where(
            or_(
                DocPackage.status == "preview_ready",
                DocPackage.status == "full_ready",
            )
        ).order_by(DocPackage.created_at)
    )
    packages = result.scalars().all()

    return [
        {
            "product_name": p.product_name,
            "slug": p.slug,
            "status": p.status,
            "payment_status": p.payment_status,
            "page_count": len(p.page_map_json) if p.page_map_json else 0,
            "page_map": p.page_map_json,
        }
        for p in packages
    ]


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a package and start preview generation in the background."""
    slug = _slugify(request.product_name)

    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.email == request.email:
            if existing.status in ("failed", "submitted", "crawling", "planning", "generating"):
                existing.status = "submitted"
                existing.error_message = None
                existing.docs_url = request.docs_url
                await db.commit()
                background_tasks.add_task(generate_package, existing.id, "preview")
                return {"id": existing.id, "slug": existing.slug, "status": "submitted"}
            return {"id": existing.id, "slug": existing.slug, "status": existing.status}
        else:
            slug = f"{slug}-{_random_suffix()}"

    package = DocPackage(
        product_name=request.product_name,
        slug=slug,
        docs_url=request.docs_url,
        email=request.email,
        status="submitted",
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)

    package_id = package.id
    background_tasks.add_task(generate_package, package_id, "preview")

    return {"id": package_id, "slug": slug, "status": "submitted"}


@router.get("/{slug}")
async def get_package(slug: str, db: AsyncSession = Depends(get_db)):
    """Return package metadata + page map."""
    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return {
        "id": package.id,
        "product_name": package.product_name,
        "slug": package.slug,
        "status": package.status,
        "payment_status": package.payment_status,
        "page_map": package.page_map_json,
        "created_at": package.created_at.isoformat() if package.created_at else None,
    }


@router.get("/{slug}/status")
async def get_status(slug: str, db: AsyncSession = Depends(get_db)):
    """Return current status of a package."""
    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return {
        "status": package.status,
        "payment_status": package.payment_status,
        "page_map": package.page_map_json,
        "has_preview": package.preview_pages_json is not None,
        "has_full": package.full_pages_json is not None,
        "error_message": package.error_message,
    }


@router.get("/{slug}/{page_slug}", response_class=HTMLResponse)
async def view_page(slug: str, page_slug: str, db: AsyncSession = Depends(get_db)):
    """Return the rendered HTML for a specific page in the package."""
    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Still generating
    if package.status in ("submitted", "crawling", "planning", "generating", "full_generating"):
        return HTMLResponse(
            content=render_generating_package_html(package.product_name, slug),
            status_code=200,
        )

    # Look up page HTML from the appropriate store
    pages = {}
    if package.payment_status == "paid" and package.full_pages_json:
        pages = package.full_pages_json
    if not pages and package.preview_pages_json:
        pages = package.preview_pages_json

    page_data = pages.get(page_slug)
    if not page_data or not page_data.get("html"):
        # Check if it's a locked full page
        if package.page_map_json:
            entry = next((p for p in package.page_map_json if p["slug"] == page_slug), None)
            if entry and entry.get("tier") == "full" and package.payment_status != "paid":
                # Render a locked page
                from services.package_renderer import render_package_page
                html = render_package_page(
                    content_json={},
                    page_type=entry.get("page_type", ""),
                    page_title=entry["title"],
                    product_name=package.product_name,
                    package_slug=package.slug,
                    page_map=package.page_map_json,
                    current_page_slug=page_slug,
                    is_paid=False,
                )
                return HTMLResponse(content=html, status_code=200)
        raise HTTPException(status_code=404, detail="Page not found")

    return HTMLResponse(content=page_data["html"], status_code=200)


@router.post("/{slug}/unlock")
async def unlock(
    slug: str,
    request: UnlockRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session to unlock the full package ($99)."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment system not configured")

    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    if package.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Already unlocked")

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Full Documentation Package — {package.product_name}",
                        "description": "Complete AI-ready documentation package with all pages + ZIP download.",
                    },
                    "unit_amount": 9900,
                },
                "quantity": 1,
            }],
            mode="payment",
            allow_promotion_codes=True,
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "package_slug": slug,
                "package_id": package.id,
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
    """Verify Stripe payment and trigger full generation."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    try:
        session = stripe.checkout.Session.retrieve(request.session_id)

        if session.payment_status == "paid":
            package.payment_status = "paid"
            await db.commit()

            if not package.full_pages_json:
                background_tasks.add_task(generate_package, package.id, "full")

            return {"paid": True, "status": package.status}

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
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    code = request.code.upper().strip()
    if code != "FREE100":
        raise HTTPException(status_code=400, detail="Invalid promo code")

    package.payment_status = "paid"
    await db.commit()

    if not package.full_pages_json:
        background_tasks.add_task(generate_package, package.id, "full")

    return {"success": True, "free": True}


@router.get("/{slug}/download")
async def download_package(slug: str, db: AsyncSession = Depends(get_db)):
    """Download the full package as a ZIP file."""
    result = await db.execute(
        select(DocPackage).where(DocPackage.slug == slug)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    if package.payment_status != "paid":
        raise HTTPException(status_code=403, detail="Package not unlocked. Payment required.")

    pages = package.full_pages_json or package.preview_pages_json
    if not pages:
        raise HTTPException(status_code=404, detail="No pages generated yet")

    # Build ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # README
        readme = f"# {package.product_name} — AI-Ready Documentation\n\n"
        readme += f"Generated by GrounDocs (https://groundocs.com)\n\n"
        readme += "## Pages\n\n"
        if package.page_map_json:
            for entry in package.page_map_json:
                readme += f"- **{entry['title']}** (`{entry['slug']}`)\n"
        zf.writestr("README.md", readme)

        # HTML and content files per page
        for page_slug, page_data in pages.items():
            if not isinstance(page_data, dict):
                continue
            title = page_data.get("title", page_slug)
            html = page_data.get("html", "")
            content_json = page_data.get("content_json", {})

            if html:
                zf.writestr(f"html/{page_slug}.html", html)
            if content_json:
                zf.writestr(f"json/{page_slug}.json", json.dumps(content_json, indent=2))

        # Metadata
        metadata = {
            "product_name": package.product_name,
            "slug": package.slug,
            "page_map": package.page_map_json,
            "generated_by": "GrounDocs",
        }
        zf.writestr("_metadata.json", json.dumps(metadata, indent=2))

        # llms.txt
        llms_txt = f"# {package.product_name}\n\n"
        llms_txt += f"> AI-ready documentation package\n\n"
        if package.page_map_json:
            for entry in package.page_map_json:
                llms_txt += f"- [{entry['title']}](html/{entry['slug']}.html)\n"
        zf.writestr("llms.txt", llms_txt)

    buf.seek(0)
    filename = f"{package.slug}-ai-docs.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
