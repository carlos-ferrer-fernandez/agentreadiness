"""
Agent Page Generator Service

Full pipeline: crawl docs -> generate structured JSON via OpenAI -> render HTML.
Produces agent-ready product documentation pages hosted at /agent-pages/{slug}.
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
from models import AgentPage
from services.crawler.crawler import DocumentationCrawler, Page

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# System prompt for OpenAI
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert technical writer creating agent-ready product documentation.
Your job is to transform raw product documentation into a structured, operational guide that teaches AI agents how to use a software product correctly.
You are not writing marketing copy. You are not summarizing loosely.
You are producing a high-signal, implementation-oriented guide.

Priorities:
1. Be accurate and grounded in the provided documentation
2. Prefer explicit instructions over vague descriptions
3. Highlight workflows, prerequisites, constraints, limitations, and failure modes
4. Make the output useful for both AI agents and humans reviewing agent documentation
5. Do not invent unsupported features or behaviors
6. If information is missing, say it is not clearly documented
7. Use concise, precise language
8. Preserve links/references to source documentation when possible

Return output in valid JSON only, matching the requested schema exactly.
Do not include markdown fences. Do not include commentary outside the JSON.
"""

JSON_SCHEMA_DESCRIPTION = """\
{
  "product_name": "string",
  "slug": "string",
  "mode": "draft or full",
  "summary": "1-2 sentence explanation",
  "overview": {
    "what_it_is": "string",
    "what_agents_can_do": ["string"],
    "best_for": ["string"]
  },
  "when_to_use": {
    "ideal_use_cases": ["string"],
    "non_ideal_use_cases": ["string"]
  },
  "getting_started": {
    "prerequisites": ["string"],
    "required_accounts_or_access": ["string"],
    "setup_steps": ["string"]
  },
  "authentication_access": {
    "auth_methods": ["string"],
    "permissions": ["string"],
    "important_auth_notes": ["string"]
  },
  "core_capabilities": [
    {"name": "string", "description": "string", "requirements": ["string"], "limitations": ["string"]}
  ],
  "recommended_workflows": [
    {"name": "string", "goal": "string", "steps": ["string"], "success_checks": ["string"], "failure_risks": ["string"]}
  ],
  "input_output_expectations": {
    "common_inputs": ["string"],
    "common_outputs": ["string"],
    "data_format_notes": ["string"]
  },
  "rules_constraints_caveats": ["string"],
  "examples": [
    {"title": "string", "scenario": "string", "example_instruction": "string", "expected_result": "string"}
  ],
  "troubleshooting": [
    {"issue": "string", "likely_causes": ["string"], "recommended_fix": ["string"]}
  ],
  "implementation_notes": {
    "what_should_appear_on_customer_agents_page": ["string"],
    "missing_info_or_doc_gaps": ["string"]
  },
  "canonical_references": [
    {"label": "string", "url": "string", "reason": "string"}
  ]
}
"""


# ---------------------------------------------------------------------------
# Stage 1: Crawl
# ---------------------------------------------------------------------------

async def crawl_docs(docs_url: str, mode: str = "draft") -> List[Page]:
    """Crawl documentation pages. Draft = max 5, full = max 20."""
    max_pages = 5 if mode == "draft" else 20

    async with DocumentationCrawler(
        start_url=docs_url,
        max_pages=max_pages,
        delay=0.2,
    ) as crawler:
        pages = await asyncio.wait_for(crawler.crawl(), timeout=120)

    return pages


# ---------------------------------------------------------------------------
# Stage 2: Generate structured JSON via OpenAI
# ---------------------------------------------------------------------------

async def generate_structured_json(
    pages: List[Page],
    product_name: str,
    slug: str,
    mode: str = "draft",
) -> dict:
    """Send crawled content to OpenAI and get structured JSON back."""
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    client_kwargs = {"api_key": api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url

    client = openai.AsyncOpenAI(**client_kwargs)

    # Build page content for the prompt
    page_texts = []
    for i, page in enumerate(pages, 1):
        title = page.title or "Untitled"
        content = (page.content or "")[:6000]  # Cap per page to fit context
        page_texts.append(f"--- Page {i}: {title} ({page.url}) ---\n{content}")

    combined_content = "\n\n".join(page_texts)

    mode_instruction = (
        "Produce a compelling but lighter version -- include overview, core capabilities, "
        "1-2 workflows, getting started. Keep other sections brief."
        if mode == "draft"
        else "Produce the most complete version -- detailed workflows, edge cases, "
        "constraints, references."
    )

    user_prompt = f"""\
Product name: {product_name}
Slug: {slug}
Mode: {mode}

{mode_instruction}

Below is the crawled documentation content from {len(pages)} pages:

{combined_content}

Return a single valid JSON object matching this schema exactly:
{JSON_SCHEMA_DESCRIPTION}
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=8000 if mode == "draft" else 16000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        content_json = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI JSON response: {e}\nRaw: {raw[:500]}")
        raise ValueError(f"OpenAI returned invalid JSON: {e}")

    return content_json


# ---------------------------------------------------------------------------
# Stage 3: Render HTML from JSON
# ---------------------------------------------------------------------------

def render_agent_page_html(
    content_json: dict,
    product_name: str,
    slug: str,
    mode: str = "draft",
) -> str:
    """Render a beautiful, self-contained HTML page from structured JSON."""
    is_draft = mode == "draft"
    badge_color = "#D97706" if is_draft else "#1A7A4C"
    badge_text = "Draft Preview" if is_draft else "Full Agent Page"

    summary = _esc(content_json.get("summary", ""))
    overview = content_json.get("overview", {})
    getting_started = content_json.get("getting_started", {})
    auth_access = content_json.get("authentication_access", {})
    capabilities = content_json.get("core_capabilities", [])
    workflows = content_json.get("recommended_workflows", [])
    when_to_use = content_json.get("when_to_use", {})
    io_expectations = content_json.get("input_output_expectations", {})
    rules = content_json.get("rules_constraints_caveats", [])
    examples = content_json.get("examples", [])
    troubleshooting = content_json.get("troubleshooting", [])
    impl_notes = content_json.get("implementation_notes", {})
    references = content_json.get("canonical_references", [])

    def _list_html(items: list, tag: str = "li") -> str:
        if not items:
            return "<p class='empty'>Not documented</p>"
        return "".join(f"<{tag}>{_esc(str(item))}</{tag}>" for item in items)

    def _section(title: str, content_html: str, locked: bool = False) -> str:
        lock_class = " locked" if locked else ""
        overlay = ""
        if locked:
            overlay = (
                '<div class="lock-overlay">'
                '<div class="lock-cta">'
                '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>'
                f'<p>Unlock Full Page &mdash; $99</p>'
                f'<a href="/agent-pages/{_esc(slug)}/unlock" class="unlock-btn">Unlock Now</a>'
                '</div></div>'
            )
        return (
            f'<section class="section{lock_class}">'
            f'<h2>{_esc(title)}</h2>'
            f'{content_html}'
            f'{overlay}'
            f'</section>'
        )

    # --- Build sections ---

    # Overview (always visible)
    overview_html = f"""
        <p class="summary">{summary}</p>
        <h3>What it is</h3>
        <p>{_esc(overview.get('what_it_is', ''))}</p>
        <h3>What agents can do</h3>
        <ul>{_list_html(overview.get('what_agents_can_do', []))}</ul>
        <h3>Best for</h3>
        <ul>{_list_html(overview.get('best_for', []))}</ul>
    """

    # Core Capabilities (always visible)
    caps_html = ""
    for cap in capabilities:
        caps_html += f"""
        <div class="capability-card">
            <h3>{_esc(cap.get('name', ''))}</h3>
            <p>{_esc(cap.get('description', ''))}</p>
            {'<div class="detail"><strong>Requirements:</strong><ul>' + _list_html(cap.get('requirements', [])) + '</ul></div>' if cap.get('requirements') else ''}
            {'<div class="detail"><strong>Limitations:</strong><ul>' + _list_html(cap.get('limitations', [])) + '</ul></div>' if cap.get('limitations') else ''}
        </div>
        """

    # Getting Started (always visible)
    gs_html = f"""
        <h3>Prerequisites</h3>
        <ul>{_list_html(getting_started.get('prerequisites', []))}</ul>
        <h3>Required Accounts / Access</h3>
        <ul>{_list_html(getting_started.get('required_accounts_or_access', []))}</ul>
        <h3>Setup Steps</h3>
        <ol>{_list_html(getting_started.get('setup_steps', []))}</ol>
    """

    # First workflow (always visible), rest locked in draft
    wf_html = ""
    for i, wf in enumerate(workflows):
        locked_wf = is_draft and i >= 1
        wf_content = f"""
        <div class="workflow-card{'locked' if locked_wf else ''}">
            <h3>{_esc(wf.get('name', ''))}</h3>
            <p class="goal"><strong>Goal:</strong> {_esc(wf.get('goal', ''))}</p>
            <h4>Steps</h4>
            <ol>{_list_html(wf.get('steps', []))}</ol>
            <div class="checks-risks">
                <div><h4>Success Checks</h4><ul>{_list_html(wf.get('success_checks', []))}</ul></div>
                <div><h4>Failure Risks</h4><ul>{_list_html(wf.get('failure_risks', []))}</ul></div>
            </div>
        </div>
        """
        wf_html += wf_content

    # Auth
    auth_html = f"""
        <h3>Auth Methods</h3>
        <ul>{_list_html(auth_access.get('auth_methods', []))}</ul>
        <h3>Permissions</h3>
        <ul>{_list_html(auth_access.get('permissions', []))}</ul>
        <h3>Important Notes</h3>
        <ul>{_list_html(auth_access.get('important_auth_notes', []))}</ul>
    """

    # When to Use
    wtu_html = f"""
        <h3>Ideal Use Cases</h3>
        <ul>{_list_html(when_to_use.get('ideal_use_cases', []))}</ul>
        <h3>Non-Ideal Use Cases</h3>
        <ul>{_list_html(when_to_use.get('non_ideal_use_cases', []))}</ul>
    """

    # I/O Expectations
    io_html = f"""
        <h3>Common Inputs</h3>
        <ul>{_list_html(io_expectations.get('common_inputs', []))}</ul>
        <h3>Common Outputs</h3>
        <ul>{_list_html(io_expectations.get('common_outputs', []))}</ul>
        <h3>Data Format Notes</h3>
        <ul>{_list_html(io_expectations.get('data_format_notes', []))}</ul>
    """

    # Rules & Constraints
    rules_html = f"<ul>{_list_html(rules)}</ul>" if rules else "<p class='empty'>None documented</p>"

    # Examples
    examples_html = ""
    for ex in examples:
        examples_html += f"""
        <div class="example-card">
            <h3>{_esc(ex.get('title', ''))}</h3>
            <p><strong>Scenario:</strong> {_esc(ex.get('scenario', ''))}</p>
            <p><strong>Instruction:</strong> {_esc(ex.get('example_instruction', ''))}</p>
            <p><strong>Expected Result:</strong> {_esc(ex.get('expected_result', ''))}</p>
        </div>
        """

    # Troubleshooting
    ts_html = ""
    for ts in troubleshooting:
        ts_html += f"""
        <div class="ts-card">
            <h3>{_esc(ts.get('issue', ''))}</h3>
            <h4>Likely Causes</h4>
            <ul>{_list_html(ts.get('likely_causes', []))}</ul>
            <h4>Recommended Fix</h4>
            <ul>{_list_html(ts.get('recommended_fix', []))}</ul>
        </div>
        """

    # Implementation Notes
    impl_html = f"""
        <h3>What Should Appear on Agent Page</h3>
        <ul>{_list_html(impl_notes.get('what_should_appear_on_customer_agents_page', []))}</ul>
        <h3>Missing Info / Doc Gaps</h3>
        <ul>{_list_html(impl_notes.get('missing_info_or_doc_gaps', []))}</ul>
    """

    # References
    refs_html = ""
    for ref in references:
        refs_html += (
            f'<div class="ref-card">'
            f'<a href="{_esc(ref.get("url", "#"))}" target="_blank" rel="noopener">{_esc(ref.get("label", ""))}</a>'
            f'<p>{_esc(ref.get("reason", ""))}</p>'
            f'</div>'
        )

    # --- Assemble full HTML ---
    sections_html = (
        _section("Overview", overview_html)
        + _section("Core Capabilities", caps_html)
        + _section("Getting Started", gs_html)
        + _section("Recommended Workflows", wf_html)
        + _section("Authentication & Access", auth_html, locked=is_draft)
        + _section("When to Use", wtu_html, locked=is_draft)
        + _section("Input / Output Expectations", io_html, locked=is_draft)
        + _section("Rules, Constraints & Caveats", rules_html, locked=is_draft)
        + _section("Examples", examples_html, locked=is_draft)
        + _section("Troubleshooting", ts_html, locked=is_draft)
        + _section("Implementation Notes", impl_html, locked=is_draft)
        + _section("Canonical References", refs_html, locked=is_draft)
    )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(product_name)} &mdash; Agent-Ready Documentation | GrounDocs</title>
<meta name="description" content="Agent-ready documentation for {_esc(product_name)}. Generated by GrounDocs.">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#FAFAF8;--surface:#FFFFFF;--border:#E8E5E0;
  --text:#1A1A1A;--text-secondary:#6B6B6B;
  --accent:#1A7A4C;--accent-light:#E8F5EE;
  --badge-color:{badge_color};
  --radius-sm:6px;--radius-md:12px;--radius-lg:20px;
}}
body{{
  font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.6;
  -webkit-font-smoothing:antialiased;
}}
.container{{max-width:820px;margin:0 auto;padding:2rem 1.5rem 4rem}}
header{{text-align:center;padding:3rem 0 2rem;border-bottom:1px solid var(--border);margin-bottom:2.5rem}}
header h1{{
  font-family:Georgia,'Times New Roman',serif;font-size:2.5rem;font-weight:400;
  color:var(--text);margin-bottom:0.5rem;letter-spacing:-0.02em;
}}
header .badge{{
  display:inline-block;padding:0.25rem 0.75rem;border-radius:100px;
  font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;
  color:#fff;background:var(--badge-color);margin-bottom:1rem;
}}
header .summary{{color:var(--text-secondary);font-size:1.05rem;max-width:600px;margin:0.75rem auto 0}}
.section{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:2rem 2.25rem;margin-bottom:1.5rem;position:relative;overflow:hidden;
}}
.section h2{{
  font-family:Georgia,'Times New Roman',serif;font-size:1.5rem;font-weight:400;
  color:var(--text);margin-bottom:1.25rem;letter-spacing:-0.01em;
  padding-bottom:0.75rem;border-bottom:1px solid var(--border);
}}
.section h3{{font-size:1rem;font-weight:600;color:var(--text);margin:1.25rem 0 0.5rem}}
.section h4{{font-size:0.875rem;font-weight:600;color:var(--text-secondary);margin:1rem 0 0.4rem}}
.section p{{color:var(--text-secondary);margin-bottom:0.5rem}}
.section ul,.section ol{{padding-left:1.5rem;color:var(--text-secondary);margin-bottom:0.75rem}}
.section li{{margin-bottom:0.35rem}}
.section li::marker{{color:var(--accent)}}
.empty{{color:#B0ADA8;font-style:italic}}
.capability-card,.workflow-card,.example-card,.ts-card,.ref-card{{
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);
  padding:1.25rem 1.5rem;margin-bottom:1rem;
}}
.capability-card h3,.workflow-card h3,.example-card h3,.ts-card h3{{margin-top:0;color:var(--accent)}}
.ref-card a{{color:var(--accent);font-weight:600;text-decoration:none}}
.ref-card a:hover{{text-decoration:underline}}
.detail{{margin-top:0.5rem}}
.checks-risks{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:0.75rem}}
.goal{{color:var(--text)!important;font-size:0.95rem}}
/* Lock overlay for draft sections */
.section.locked{{min-height:200px}}
.section.locked>*:not(h2):not(.lock-overlay){{filter:blur(4px);opacity:0.5;pointer-events:none;user-select:none}}
.lock-overlay{{
  position:absolute;top:0;left:0;right:0;bottom:0;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(250,250,248,0) 0%,rgba(250,250,248,0.85) 40%,rgba(250,250,248,0.97) 100%);
  z-index:10;
}}
.lock-cta{{
  text-align:center;padding:2rem;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:0 4px 24px rgba(0,0,0,0.06);
}}
.lock-cta svg{{color:var(--accent);margin-bottom:0.5rem}}
.lock-cta p{{font-weight:600;color:var(--text);margin-bottom:1rem;font-size:1.1rem}}
.unlock-btn{{
  display:inline-block;padding:0.75rem 2rem;background:var(--accent);color:#fff;
  border-radius:100px;font-weight:600;text-decoration:none;font-size:0.95rem;
  transition:background 0.2s;
}}
.unlock-btn:hover{{background:#15603B}}
footer{{
  text-align:center;padding:2.5rem 0 1rem;color:var(--text-secondary);font-size:0.85rem;
  border-top:1px solid var(--border);margin-top:1rem;
}}
footer a{{color:var(--accent);text-decoration:none;font-weight:600}}
footer a:hover{{text-decoration:underline}}
@media(max-width:640px){{
  .container{{padding:1rem 1rem 3rem}}
  header h1{{font-size:1.75rem}}
  .section{{padding:1.25rem 1rem}}
  .checks-risks{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="container">
  <header>
    <span class="badge">{badge_text}</span>
    <h1>{_esc(product_name)}</h1>
    <p class="summary">{summary}</p>
  </header>
  {sections_html}
  <footer>
    <p>Powered by <a href="https://groundocs.com" target="_blank">GrounDocs</a></p>
  </footer>
</div>
</body>
</html>
"""
    return html


def render_generating_html(product_name: str, slug: str) -> str:
    """Return a nice 'generating...' page with auto-refresh."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="5">
<title>{_esc(product_name)} &mdash; Generating... | GrounDocs</title>
<style>
body{{
  font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,sans-serif;
  background:#FAFAF8;color:#1A1A1A;display:flex;align-items:center;justify-content:center;
  min-height:100vh;margin:0;
}}
.card{{
  text-align:center;background:#fff;border:1px solid #E8E5E0;border-radius:20px;
  padding:3rem 2.5rem;max-width:480px;box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
h1{{font-family:Georgia,serif;font-weight:400;font-size:1.75rem;margin-bottom:1rem}}
p{{color:#6B6B6B;margin-bottom:1.5rem}}
.spinner{{
  width:40px;height:40px;border:3px solid #E8E5E0;border-top-color:#1A7A4C;
  border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 1.5rem;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<div class="card">
  <div class="spinner"></div>
  <h1>Generating your agent page</h1>
  <p>We&rsquo;re crawling <strong>{_esc(product_name)}</strong> docs and building your agent-ready page. This usually takes 30&ndash;60 seconds.</p>
  <p style="font-size:0.85rem;color:#B0ADA8">This page refreshes automatically.</p>
</div>
</body>
</html>
"""


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def generate_agent_page(agent_page_id: str, mode: str = "draft"):
    """Full pipeline: crawl -> generate JSON -> render HTML -> store in DB."""
    logger.info(f"=== AGENT PAGE PIPELINE STARTED for {agent_page_id} (mode={mode}) ===")

    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(AgentPage).where(AgentPage.id == agent_page_id)
            )
            agent_page = result.scalar_one_or_none()
            if not agent_page:
                logger.error(f"AgentPage {agent_page_id} not found")
                return

            # Stage 1: Crawl
            status_field = "crawling"
            agent_page.status = status_field
            agent_page.crawl_scope = mode
            await db.commit()

            pages = await crawl_docs(agent_page.docs_url, mode=mode)
            if not pages:
                raise ValueError(f"No pages crawled from {agent_page.docs_url}")

            agent_page.source_pages = [
                {"url": p.url, "title": p.title or "Untitled"}
                for p in pages
            ]
            await db.commit()

            # Stage 2: Generate JSON
            gen_status = "generating" if mode == "draft" else "full_generating"
            agent_page.status = gen_status
            await db.commit()

            content_json = await generate_structured_json(
                pages=pages,
                product_name=agent_page.product_name,
                slug=agent_page.company_slug,
                mode=mode,
            )

            # Stage 3: Render HTML
            html = render_agent_page_html(
                content_json=content_json,
                product_name=agent_page.product_name,
                slug=agent_page.company_slug,
                mode=mode,
            )

            # Store results
            if mode == "draft":
                agent_page.draft_content_json = content_json
                agent_page.draft_html = html
                agent_page.status = "draft_ready"
            else:
                agent_page.full_content_json = content_json
                agent_page.full_html = html
                agent_page.status = "full_ready"

            await db.commit()
            logger.info(f"=== AGENT PAGE PIPELINE COMPLETE for {agent_page_id} ===")

        except Exception as e:
            logger.error(f"=== AGENT PAGE PIPELINE FAILED for {agent_page_id}: {e} ===", exc_info=True)
            try:
                result = await db.execute(
                    select(AgentPage).where(AgentPage.id == agent_page_id)
                )
                agent_page = result.scalar_one_or_none()
                if agent_page:
                    agent_page.status = "failed"
                    agent_page.error_message = str(e)[:500]
                    await db.commit()
            except Exception:
                logger.error(f"Failed to update error status for {agent_page_id}")
