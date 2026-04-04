"""
Package Generator Service

Two-phase pipeline:
1. Crawl docs + infer information architecture (page map)
2. Generate per-page content via OpenAI, render HTML

Produces a multi-page AI-ready documentation package.
"""

import asyncio
import json
import logging
import os
from typing import List, Optional

import openai
from sqlalchemy import select

from config import get_settings
from database import async_session_factory
from models import DocPackage
from services.crawler.crawler import DocumentationCrawler, Page
from services.agent_page_generator import (
    generate_structured_json as generate_agents_json,
    render_agent_page_html,
    SYSTEM_PROMPT as AGENTS_SYSTEM_PROMPT,
    crawl_docs,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Page type definitions
# ---------------------------------------------------------------------------

PREVIEW_PAGE_TYPES = {"overview", "agents", "getting-started"}

PAGE_TYPE_CONFIG = {
    "overview": {
        "title_default": "Overview",
        "tier": "preview",
        "prompt": (
            "Create a product overview page for AI agents and developers.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- tagline: one sentence describing what this product does\n"
            "- what_it_does: 3-5 bullet points, each under 12 words\n"
            "- key_concepts: list of {term, definition} — core domain terms agents need\n"
            "- capabilities: list of {name, description} — what the product can do\n"
            "- integrations: list of known integrations/platforms\n"
            "- when_to_use: 3-5 scenarios where this product is the right choice\n"
            "- when_not_to_use: 2-3 scenarios where it's the wrong choice\n"
            "- links: list of {label, url} — key entry points into the docs\n\n"
            "Be factual. Never invent features or integrations not in the source docs."
        ),
    },
    "agents": {
        "title_default": "Agent Operating Guide",
        "tier": "preview",
        "prompt": None,  # Uses existing agent page generator
    },
    "getting-started": {
        "title_default": "Getting Started",
        "tier": "preview",
        "prompt": (
            "Create a getting-started guide for AI agents and developers.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- prerequisites: list of requirements before starting\n"
            "- install_steps: list of {step_number, instruction, code_snippet?} — minimal setup\n"
            "- first_api_call: {description, code_snippet, expected_response} — simplest working example\n"
            "- auth_setup: {method, steps} — how to authenticate\n"
            "- common_next_steps: list of {action, description} — what to do after setup\n"
            "- gotchas: list of common mistakes during setup\n\n"
            "Focus on the fastest path to a working integration. Skip advanced config."
        ),
    },
    "authentication": {
        "title_default": "Authentication",
        "tier": "full",
        "prompt": (
            "Create an authentication reference page.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- auth_methods: list of {method, description, when_to_use}\n"
            "- token_management: {how_to_get, how_to_refresh, expiration, storage_recommendations}\n"
            "- scopes_and_permissions: list of {scope, description, required_for}\n"
            "- security_rules: list of rules agents must follow\n"
            "- common_errors: list of {error, cause, fix}\n\n"
            "Only document auth methods that exist in the source docs."
        ),
    },
    "core-concepts": {
        "title_default": "Core Concepts",
        "tier": "full",
        "prompt": (
            "Create a core concepts reference page.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- domain_model: list of {entity, description, relationships}\n"
            "- key_abstractions: list of {name, what_it_is, why_it_matters}\n"
            "- data_flow: description of how data moves through the system\n"
            "- terminology: list of {term, definition} — product-specific terms\n"
            "- mental_model: 2-3 sentences describing how to think about this product\n\n"
            "Be precise. Use the product's own terminology."
        ),
    },
    "rules": {
        "title_default": "Rules & Constraints",
        "tier": "full",
        "prompt": (
            "Create a rules and constraints reference page.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- rate_limits: list of {endpoint_or_resource, limit, window, what_happens_when_exceeded}\n"
            "- quotas: list of {resource, limit, how_to_check}\n"
            "- size_limits: list of {what, max_size}\n"
            "- naming_rules: list of constraints on names/identifiers\n"
            "- ordering_rules: list of operations that must happen in specific order\n"
            "- edge_cases: list of {scenario, behavior, recommendation}\n\n"
            "Only include limits/rules actually documented. Say 'not documented' for unknowns."
        ),
    },
    "troubleshooting": {
        "title_default": "Troubleshooting",
        "tier": "full",
        "prompt": (
            "Create a troubleshooting guide.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- common_errors: list of {error_code_or_message, likely_cause, fix, escalate_if}\n"
            "- diagnostic_steps: list of {symptom, check_first, then_check}\n"
            "- health_checks: list of {what_to_check, how, healthy_response}\n"
            "- known_issues: list of {issue, workaround, status}\n\n"
            "Focus on errors agents are likely to encounter programmatically."
        ),
    },
    "faq": {
        "title_default": "FAQ",
        "tier": "full",
        "prompt": (
            "Create a FAQ page based on the documentation.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- questions: list of {question, answer, category}\n\n"
            "Categories: setup, usage, billing, limits, security, integration\n"
            "Answers should be 1-3 sentences. Focus on questions agents would ask.\n"
            "Only include questions answerable from the source docs."
        ),
    },
    "resources": {
        "title_default": "Resources",
        "tier": "full",
        "prompt": (
            "Create a resources reference page.\n\n"
            "Include:\n"
            "- product_name: string\n"
            "- sdks: list of {language, package_name, install_command, url}\n"
            "- api_references: list of {name, url, description}\n"
            "- changelogs: {url, latest_version?}\n"
            "- community: list of {platform, url}\n"
            "- status_page: {url} if available\n"
            "- support: {how_to_contact, response_time?}\n\n"
            "Only include resources that are actually linked in the docs."
        ),
    },
}


# ---------------------------------------------------------------------------
# OpenAI client helper
# ---------------------------------------------------------------------------

def _get_openai_client() -> openai.AsyncOpenAI:
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    kwargs = {"api_key": api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return openai.AsyncOpenAI(**kwargs)


# ---------------------------------------------------------------------------
# Phase 1: Crawl + Plan page map
# ---------------------------------------------------------------------------

PAGE_MAP_SYSTEM_PROMPT = """You are an information architect for AI-ready documentation.

Given crawled documentation content, decide which pages should be in the documentation package.

Rules:
1. Always include: overview, agents, getting-started (these are the free preview)
2. Only include other page types if the docs have enough content to fill them meaningfully
3. For workflow pages: identify 2-5 distinct task workflows from the docs
4. Each workflow should be a specific end-to-end task (e.g., "Send a transactional email", "Process a payment")
5. Never invent page types not in the allowed list
6. Workflow slugs must be: workflow-{short-kebab-name}

Return valid JSON only. No markdown fences."""


async def plan_page_map(pages: List[Page], product_name: str) -> list:
    """Analyze crawled content and decide which pages to generate."""
    client = _get_openai_client()

    page_summaries = []
    for i, page in enumerate(pages[:20], 1):
        title = page.title or "Untitled"
        content = (page.content or "")[:2000]
        page_summaries.append(f"--- Page {i}: {title} ---\n{content}")

    combined = "\n\n".join(page_summaries)

    user_prompt = f"""\
Product: {product_name}
Crawled {len(pages)} documentation pages.

Content summary:
{combined}

Allowed page types: overview, agents, getting-started, authentication, core-concepts, rules, troubleshooting, faq, resources, workflow-*

Return a JSON array of page entries. Each entry:
{{"page_type": "string", "title": "Human-readable title", "slug": "url-slug", "tier": "preview|full"}}

The first 3 must be overview, agents, getting-started (tier: preview).
All others are tier: full.
Workflow pages use page_type "workflow" and slug "workflow-{{task-name}}".
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": PAGE_MAP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_completion_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        page_map = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse page map JSON: {e}\nRaw: {raw[:500]}")
        # Fallback to default preview pages
        page_map = [
            {"page_type": "overview", "title": "Overview", "slug": "overview", "tier": "preview"},
            {"page_type": "agents", "title": "Agent Operating Guide", "slug": "agents", "tier": "preview"},
            {"page_type": "getting-started", "title": "Getting Started", "slug": "getting-started", "tier": "preview"},
        ]

    # Ensure preview pages are always present
    existing_types = {p["page_type"] for p in page_map if p["page_type"] != "workflow"}
    for pt in ["overview", "agents", "getting-started"]:
        if pt not in existing_types:
            cfg = PAGE_TYPE_CONFIG[pt]
            page_map.insert(0, {
                "page_type": pt,
                "title": cfg["title_default"],
                "slug": pt,
                "tier": "preview",
            })

    return page_map


# ---------------------------------------------------------------------------
# Phase 2: Generate per-page content
# ---------------------------------------------------------------------------

PER_PAGE_SYSTEM_PROMPT = """You are an expert technical writer creating AI-ready documentation pages.

Rules:
1. Only include information present in the source documentation
2. Never invent endpoints, parameters, limits, or features
3. If information is missing, say "not documented" or omit the field
4. Be concise: bullets under 12 words when possible
5. Use the product's own terminology consistently

Return valid JSON only. No markdown fences. No commentary."""


async def generate_page_content(
    pages: List[Page],
    product_name: str,
    page_type: str,
    page_title: str,
) -> dict:
    """Generate structured JSON content for a single page type."""

    # Special case: agents page uses the existing generator
    if page_type == "agents":
        return await generate_agents_json(
            pages=pages,
            product_name=product_name,
            slug="agents",
            mode="full",
        )

    config = PAGE_TYPE_CONFIG.get(page_type)
    if not config:
        # Workflow page — use a generic workflow prompt
        config = {
            "prompt": (
                f"Create a step-by-step workflow guide for: {page_title}\n\n"
                "Include:\n"
                "- product_name: string\n"
                "- workflow_name: string\n"
                "- goal: one sentence describing the end result\n"
                "- prerequisites: list of requirements\n"
                "- steps: list of {step_number, action, details, code_snippet?, gotcha?}\n"
                "- verify: how to confirm the workflow succeeded\n"
                "- common_variations: list of {variation, how_it_differs}\n"
                "- error_handling: list of {error, fix}\n"
                "- related_workflows: list of workflow names\n\n"
                "Focus on the behavioral steps, not raw API reference."
            ),
        }

    client = _get_openai_client()

    page_texts = []
    for i, page in enumerate(pages[:15], 1):
        title = page.title or "Untitled"
        content = (page.content or "")[:5000]
        page_texts.append(f"--- Page {i}: {title} ({page.url}) ---\n{content}")

    combined = "\n\n".join(page_texts)

    user_prompt = f"""\
Product: {product_name}
Page type: {page_type}
Page title: {page_title}

{config["prompt"]}

Source documentation ({len(pages)} pages):
{combined}

Return a single valid JSON object.
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": PER_PAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_completion_tokens=6000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        content = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse page content JSON for {page_type}: {e}")
        raise ValueError(f"OpenAI returned invalid JSON for {page_type}: {e}")

    return content


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def generate_package(package_id: str, tier: str = "preview"):
    """
    Full pipeline: crawl -> plan page map -> generate per-page content -> render HTML -> store.

    tier="preview": generate only the 3 free preview pages
    tier="full": generate all pages in the page map
    """
    logger.info(f"=== PACKAGE PIPELINE STARTED for {package_id} (tier={tier}) ===")

    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(DocPackage).where(DocPackage.id == package_id)
            )
            package = result.scalar_one_or_none()
            if not package:
                logger.error(f"DocPackage {package_id} not found")
                return

            # --- Stage 1: Crawl ---
            package.status = "crawling"
            await db.commit()

            max_pages = 5 if tier == "preview" else 20
            crawled_pages = await crawl_docs(package.docs_url, mode="draft" if tier == "preview" else "full")
            if not crawled_pages:
                raise ValueError(f"No pages crawled from {package.docs_url}")

            package.source_pages = [
                {"url": p.url, "title": p.title or "Untitled"}
                for p in crawled_pages
            ]
            await db.commit()

            # --- Stage 2: Plan page map ---
            package.status = "planning"
            await db.commit()

            if not package.page_map_json:
                page_map = await plan_page_map(crawled_pages, package.product_name)
                package.page_map_json = page_map
                await db.commit()
            else:
                page_map = package.page_map_json

            # --- Stage 3: Generate per-page content ---
            package.status = "generating" if tier == "preview" else "full_generating"
            await db.commit()

            # Import renderer here to avoid circular imports
            from services.package_renderer import render_package_page

            pages_to_generate = []
            for entry in page_map:
                if tier == "preview" and entry.get("tier") != "preview":
                    continue
                pages_to_generate.append(entry)

            generated_pages = {}
            for entry in pages_to_generate:
                page_type = entry["page_type"]
                page_title = entry["title"]
                page_slug = entry["slug"]

                logger.info(f"Generating page: {page_slug} ({page_type})")

                try:
                    content_json = await generate_page_content(
                        pages=crawled_pages,
                        product_name=package.product_name,
                        page_type=page_type,
                        page_title=page_title,
                    )

                    html = render_package_page(
                        content_json=content_json,
                        page_type=page_type,
                        page_title=page_title,
                        product_name=package.product_name,
                        package_slug=package.slug,
                        page_map=page_map,
                        current_page_slug=page_slug,
                        is_paid=package.payment_status == "paid",
                    )

                    generated_pages[page_slug] = {
                        "title": page_title,
                        "page_type": page_type,
                        "html": html,
                        "content_json": content_json,
                    }
                except Exception as e:
                    logger.error(f"Failed to generate page {page_slug}: {e}")
                    generated_pages[page_slug] = {
                        "title": page_title,
                        "page_type": page_type,
                        "html": None,
                        "content_json": None,
                        "error": str(e)[:200],
                    }

            # Store results
            if tier == "preview":
                package.preview_pages_json = generated_pages
                package.status = "preview_ready"
            else:
                # Merge with existing preview pages
                all_pages = dict(package.preview_pages_json or {})
                all_pages.update(generated_pages)
                package.full_pages_json = all_pages
                package.status = "full_ready"

            await db.commit()
            logger.info(f"=== PACKAGE PIPELINE COMPLETE for {package_id} ({len(generated_pages)} pages) ===")

        except Exception as e:
            logger.error(f"=== PACKAGE PIPELINE FAILED for {package_id}: {e} ===", exc_info=True)
            try:
                result = await db.execute(
                    select(DocPackage).where(DocPackage.id == package_id)
                )
                package = result.scalar_one_or_none()
                if package:
                    package.status = "failed"
                    package.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                logger.error(f"Failed to update error status for {package_id}")
