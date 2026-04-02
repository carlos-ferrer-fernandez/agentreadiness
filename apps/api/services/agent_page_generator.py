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

SYSTEM_PROMPT = """You are an expert technical writer designing agent operating guides for software products.

Your job is not to summarize documentation in a generic way.
Your job is to produce a practical operating manual that tells AI agents how to use a product safely and effectively.

The output must help answer:
- What can the agent do?
- What must the agent confirm before acting?
- What actions are too risky or ambiguous and should be escalated?
- What steps should the agent follow for common tasks?
- What should the agent verify before and after each action?
- What should the agent do when required information is missing?

Priorities:
1. Accuracy grounded in the provided documentation
2. Operational usefulness over broad explanation
3. Task-oriented guidance over feature summaries
4. Safety, approval boundaries, and escalation logic
5. Clear workflows with preconditions, steps, checks, and failure handling
6. Explicit acknowledgement when something is not clearly documented
7. Concise, high-signal language
8. No marketing fluff

Do not invent product capabilities, rules, thresholds, or policies that are not supported by the provided sources.
If a product-specific threshold or internal policy is not documented, describe the need for confirmation generically instead of making up a number.

Return valid JSON only, following the requested schema exactly.
Do not include markdown fences.
Do not include commentary outside the JSON."""

JSON_SCHEMA_DESCRIPTION = """\
{
  "meta": {
    "product_name": "string",
    "slug": "string",
    "mode": "draft | full",
    "docs_root_url": "string"
  },
  "hero": {
    "summary": "1-2 sentence product description",
    "agent_fit_summary": "what agents are well suited for with this product",
    "high_risk_notice": "brief warning about highest-risk actions",
    "primary_cta_label": "string"
  },
  "agent_scope": {
    "safe_without_approval": [
      {"action": "string", "reason": "string", "risk_level": "safe_read | safe_write"}
    ],
    "requires_confirmation": [
      {"action": "string", "reason": "string", "risk_level": "requires_confirmation", "confirmation_needed_for": ["string"]}
    ],
    "requires_escalation": [
      {"action": "string", "reason": "string", "risk_level": "requires_escalation", "escalate_when": ["string"]}
    ]
  },
  "suitability": {
    "best_for": ["string"],
    "less_suitable_for": ["string"],
    "not_clearly_supported": ["string"]
  },
  "setup_access": {
    "prerequisites": ["string"],
    "accounts_and_access": ["string"],
    "authentication": {
      "methods": ["string"],
      "required_secrets_or_tokens": ["string"],
      "permission_notes": ["string"],
      "environment_notes": ["string"]
    },
    "initial_setup_steps": ["string"]
  },
  "task_playbooks": [
    {
      "id": "string",
      "task_name": "string",
      "goal": "string",
      "when_to_use": ["string"],
      "when_not_to_use": ["string"],
      "risk_level": "safe_read | safe_write | requires_confirmation | requires_escalation | high_risk",
      "required_inputs": [{"name": "string", "description": "string", "required": true}],
      "optional_inputs": [{"name": "string", "description": "string"}],
      "pre_checks": ["string"],
      "steps": ["string"],
      "verification_checks": ["string"],
      "common_failure_modes": [{"issue": "string", "why_it_happens": ["string"], "safe_recovery": ["string"]}],
      "missing_information_behavior": ["string"],
      "confirmation_required_when": ["string"],
      "escalate_when": ["string"],
      "source_refs": [{"label": "string", "url": "string"}],
      "confidence": "high | medium | low"
    }
  ],
  "operating_rules": {
    "always_do": ["string"],
    "never_do": ["string"],
    "verify_before_write_actions": ["string"],
    "verify_after_write_actions": ["string"],
    "ambiguity_rules": ["string"],
    "environment_rules": ["string"],
    "retry_idempotency_rules": ["string"]
  },
  "decision_guide": [
    {
      "decision": "string",
      "choose_when": ["string"],
      "avoid_when": ["string"],
      "prefer_instead": ["string"],
      "escalate_when": ["string"]
    }
  ],
  "troubleshooting": [
    {
      "issue": "string",
      "signals": ["string"],
      "likely_causes": ["string"],
      "recommended_actions": ["string"],
      "do_not_do": ["string"],
      "escalate_when": ["string"],
      "source_refs": [{"label": "string", "url": "string"}]
    }
  ],
  "references_by_topic": [
    {
      "topic": "string",
      "references": [{"label": "string", "url": "string", "reason": "string"}]
    }
  ],
  "implementation_notes": {
    "customer_page_must_include": ["string"],
    "doc_gaps_or_unclear_areas": ["string"]
  }
}
"""


# ---------------------------------------------------------------------------
# Stage 1: Crawl
# ---------------------------------------------------------------------------

async def crawl_docs(docs_url: str, mode: str = "draft") -> List[Page]:
    """Crawl documentation pages. Draft = max 5, full = max 20."""
    max_pages = 5 if mode == "draft" else 20

    try:
        async with DocumentationCrawler(
            start_url=docs_url,
            max_pages=max_pages,
            delay=0.2,
        ) as crawler:
            pages = await asyncio.wait_for(crawler.crawl(), timeout=120)
    except asyncio.TimeoutError:
        raise ValueError(f"Crawl timed out after 120s for {docs_url}. The site may be slow or blocking requests.")
    except Exception as e:
        raise ValueError(f"Failed to crawl {docs_url}: {str(e)[:200]}")

    # Filter out pages with no meaningful content
    pages = [p for p in pages if p.content and len(p.content.strip()) > 50]

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
        "Produce a useful but lighter version. Include 2-3 key task playbooks, the most "
        "critical operating rules, and the most important action boundaries. Leave room "
        "for a deeper full version."
        if mode == "draft"
        else "Produce the most complete operational guide supported by the sources. Include "
        "all relevant task playbooks, comprehensive operating rules, detailed decision "
        "guides, and thorough troubleshooting."
    )

    user_prompt = f"""\
Product name: {product_name}
Slug: {slug}
Mode: {mode}

{mode_instruction}

Writing guidelines:
- Prefer "Agent should..." over descriptive prose
- Prefer "Use X when / Avoid X when / Escalate if..." framing
- For risky actions, explicitly describe confirmation or escalation needs
- For each task, include required inputs, pre-checks, steps, verification, failure modes, and escalation conditions
- If documentation is incomplete, say "not clearly documented"

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
        max_completion_tokens=8000 if mode == "draft" else 16000,
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
    """Render a premium agent operating guide HTML page from structured JSON."""
    import datetime

    is_draft = mode == "draft"
    badge_color = "#D97706" if is_draft else "#1A7A4C"
    badge_text = "Draft Preview" if is_draft else "Full Operating Guide"
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Extract top-level sections from the new schema
    meta = content_json.get("meta", {})
    hero = content_json.get("hero", {})
    agent_scope = content_json.get("agent_scope", {})
    suitability = content_json.get("suitability", {})
    setup_access = content_json.get("setup_access", {})
    task_playbooks = content_json.get("task_playbooks", [])
    operating_rules = content_json.get("operating_rules", {})
    decision_guide = content_json.get("decision_guide", [])
    troubleshooting = content_json.get("troubleshooting", [])
    references_by_topic = content_json.get("references_by_topic", [])
    impl_notes = content_json.get("implementation_notes", {})

    def _list_html(items: list) -> str:
        if not items:
            return '<p class="empty">Not documented</p>'
        return "<ul>" + "".join(f"<li>{_esc(str(item))}</li>" for item in items) + "</ul>"

    def _ol_html(items: list) -> str:
        if not items:
            return '<p class="empty">Not documented</p>'
        return "<ol>" + "".join(f"<li>{_esc(str(item))}</li>" for item in items) + "</ol>"

    def _risk_badge(level: str) -> str:
        colors = {
            "safe_read": ("#1A7A4C", "Safe Read"),
            "safe_write": ("#2563EB", "Safe Write"),
            "requires_confirmation": ("#D97706", "Requires Confirmation"),
            "requires_escalation": ("#DC2626", "Requires Escalation"),
            "high_risk": ("#991B1B", "High Risk"),
        }
        bg, label = colors.get(level, ("#71717A", level.replace("_", " ").title()))
        return f'<span class="risk-badge" style="background:{bg}">{_esc(label)}</span>'

    def _confidence_badge(level: str) -> str:
        colors = {"high": "#1A7A4C", "medium": "#D97706", "low": "#DC2626"}
        bg = colors.get(level, "#71717A")
        return f'<span class="confidence-badge" style="background:{bg}">{_esc(level.title())} Confidence</span>'

    def _callout(text: str, variant: str = "amber") -> str:
        if not text:
            return ""
        border = "#D97706" if variant == "amber" else "#DC2626"
        bg = "#FFFBEB" if variant == "amber" else "#FEF2F2"
        return f'<div class="callout" style="border-left:4px solid {border};background:{bg};padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin:0.75rem 0"><p style="margin:0;color:#18181B">{_esc(text)}</p></div>'

    def _callout_list(items: list, variant: str = "amber") -> str:
        if not items:
            return ""
        border = "#D97706" if variant == "amber" else "#DC2626"
        bg = "#FFFBEB" if variant == "amber" else "#FEF2F2"
        inner = "".join(f"<li>{_esc(str(i))}</li>" for i in items)
        return f'<div class="callout" style="border-left:4px solid {border};background:{bg};padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin:0.75rem 0"><ul style="margin:0;padding-left:1.25rem">{inner}</ul></div>'

    def _lock_overlay() -> str:
        return (
            '<div class="lock-overlay">'
            '<div class="lock-cta">'
            '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>'
            '<p>Unlock Full Operating Guide &mdash; $99</p>'
            f'<a href="/agent-pages/{_esc(slug)}/unlock" class="unlock-btn">Unlock Now</a>'
            '</div></div>'
        )

    def _section(title: str, body: str, locked: bool = False, section_id: str = "") -> str:
        id_attr = f' id="{_esc(section_id)}"' if section_id else ""
        cls = "section locked" if locked else "section"
        overlay = _lock_overlay() if locked else ""
        return f'<section class="{cls}"{id_attr}><h2>{_esc(title)}</h2>{body}{overlay}</section>'

    # ----- 1. Hero -----
    hero_html = f"""
    <header class="hero">
      <span class="mode-badge" style="background:{badge_color}">{badge_text}</span>
      <h1>{_esc(product_name)}</h1>
      <p class="hero-summary">{_esc(hero.get('summary', ''))}</p>
      <p class="hero-agent-fit">{_esc(hero.get('agent_fit_summary', ''))}</p>
      {_callout(hero.get('high_risk_notice', ''), 'amber')}
    </header>
    """

    # ----- 2. Agent Scope -----
    safe_items = agent_scope.get("safe_without_approval", [])
    confirm_items = agent_scope.get("requires_confirmation", [])
    escalate_items = agent_scope.get("requires_escalation", [])

    safe_cards = ""
    for item in safe_items:
        safe_cards += f'<li><strong>{_esc(item.get("action", ""))}</strong> <span class="scope-reason">{_esc(item.get("reason", ""))}</span></li>'

    confirm_cards = ""
    for item in confirm_items:
        cnf = item.get("confirmation_needed_for", [])
        cnf_html = "".join(f"<li>{_esc(c)}</li>" for c in cnf) if cnf else ""
        confirm_cards += f'<li><strong>{_esc(item.get("action", ""))}</strong> <span class="scope-reason">{_esc(item.get("reason", ""))}</span>'
        if cnf_html:
            confirm_cards += f'<ul class="scope-sub">{cnf_html}</ul>'
        confirm_cards += '</li>'

    escalate_cards = ""
    for item in escalate_items:
        esc = item.get("escalate_when", [])
        esc_html = "".join(f"<li>{_esc(e)}</li>" for e in esc) if esc else ""
        escalate_cards += f'<li><strong>{_esc(item.get("action", ""))}</strong> <span class="scope-reason">{_esc(item.get("reason", ""))}</span>'
        if esc_html:
            escalate_cards += f'<ul class="scope-sub">{esc_html}</ul>'
        escalate_cards += '</li>'

    scope_html = f"""
    <div class="scope-grid">
      <div class="scope-col scope-safe">
        <h3 class="scope-header" style="color:#1A7A4C;border-bottom:2px solid #1A7A4C">Safe Actions</h3>
        <ul class="scope-list">{safe_cards if safe_cards else '<li class="empty">None documented</li>'}</ul>
      </div>
      <div class="scope-col scope-confirm">
        <h3 class="scope-header" style="color:#D97706;border-bottom:2px solid #D97706">Requires Confirmation</h3>
        <ul class="scope-list">{confirm_cards if confirm_cards else '<li class="empty">None documented</li>'}</ul>
      </div>
      <div class="scope-col scope-escalate">
        <h3 class="scope-header" style="color:#DC2626;border-bottom:2px solid #DC2626">Requires Escalation</h3>
        <ul class="scope-list">{escalate_cards if escalate_cards else '<li class="empty">None documented</li>'}</ul>
      </div>
    </div>
    """

    # ----- 3. Suitability -----
    suit_html = f"""
    <div class="suit-grid">
      <div class="suit-card"><h3>Best For</h3>{_list_html(suitability.get('best_for', []))}</div>
      <div class="suit-card"><h3>Less Suitable For</h3>{_list_html(suitability.get('less_suitable_for', []))}</div>
      <div class="suit-card"><h3>Not Clearly Supported</h3>{_list_html(suitability.get('not_clearly_supported', []))}</div>
    </div>
    """

    # ----- 4. Setup & Access -----
    auth = setup_access.get("authentication", {})
    setup_html = f"""
    <h3>Prerequisites</h3>
    {_list_html(setup_access.get('prerequisites', []))}
    <h3>Accounts &amp; Access</h3>
    {_list_html(setup_access.get('accounts_and_access', []))}
    <h3>Authentication</h3>
    <div class="detail"><strong>Methods:</strong> {_list_html(auth.get('methods', []))}</div>
    <div class="detail"><strong>Required Secrets / Tokens:</strong> {_list_html(auth.get('required_secrets_or_tokens', []))}</div>
    <div class="detail"><strong>Permission Notes:</strong> {_list_html(auth.get('permission_notes', []))}</div>
    <div class="detail"><strong>Environment Notes:</strong> {_list_html(auth.get('environment_notes', []))}</div>
    <h3>Initial Setup Steps</h3>
    {_ol_html(setup_access.get('initial_setup_steps', []))}
    """

    # ----- 5. Task Playbooks -----
    playbooks_html = ""
    for idx, pb in enumerate(task_playbooks):
        # In draft mode, only show first 2 fully; rest locked
        locked_pb = is_draft and idx >= 2

        # Required inputs table
        req_inputs = pb.get("required_inputs", [])
        inputs_table = ""
        if req_inputs:
            rows = ""
            for inp in req_inputs:
                rows += f'<tr><td><code>{_esc(inp.get("name", ""))}</code></td><td>{_esc(inp.get("description", ""))}</td><td>{"Yes" if inp.get("required") else "No"}</td></tr>'
            inputs_table = f'<table class="inputs-table"><thead><tr><th>Input</th><th>Description</th><th>Required</th></tr></thead><tbody>{rows}</tbody></table>'

        opt_inputs = pb.get("optional_inputs", [])
        if opt_inputs:
            opt_rows = ""
            for inp in opt_inputs:
                opt_rows += f'<tr><td><code>{_esc(inp.get("name", ""))}</code></td><td>{_esc(inp.get("description", ""))}</td><td>No</td></tr>'
            inputs_table += f'<table class="inputs-table"><thead><tr><th>Optional Input</th><th>Description</th><th>Required</th></tr></thead><tbody>{opt_rows}</tbody></table>'

        # Failure modes
        failures = pb.get("common_failure_modes", [])
        failures_html = ""
        if failures:
            for fm in failures:
                why = "".join(f"<li>{_esc(w)}</li>" for w in fm.get("why_it_happens", []))
                rec = "".join(f"<li>{_esc(r)}</li>" for r in fm.get("safe_recovery", []))
                failures_html += f"""
                <div class="failure-mode">
                  <strong>{_esc(fm.get('issue', ''))}</strong>
                  {f'<div class="detail"><em>Why:</em><ul>{why}</ul></div>' if why else ''}
                  {f'<div class="detail"><em>Recovery:</em><ul>{rec}</ul></div>' if rec else ''}
                </div>
                """

        # Source refs
        refs = pb.get("source_refs", [])
        refs_html = ""
        if refs:
            refs_html = '<div class="pb-refs"><strong>Sources:</strong> '
            refs_html += ", ".join(f'<a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a>' for r in refs)
            refs_html += '</div>'

        pb_content = f"""
        <div class="playbook-card{' locked-inner' if locked_pb else ''}">
          <div class="pb-header">
            <h3>{_esc(pb.get('task_name', ''))}</h3>
            <div class="pb-badges">{_risk_badge(pb.get('risk_level', ''))}{_confidence_badge(pb.get('confidence', 'medium'))}</div>
          </div>
          <p class="pb-goal"><strong>Goal:</strong> {_esc(pb.get('goal', ''))}</p>
          <div class="pb-when">
            <div><h4>When to Use</h4>{_list_html(pb.get('when_to_use', []))}</div>
            <div><h4>When Not to Use</h4>{_list_html(pb.get('when_not_to_use', []))}</div>
          </div>
          {inputs_table}
          <h4>Pre-checks</h4>
          {_list_html(pb.get('pre_checks', []))}
          <h4>Steps</h4>
          {_ol_html(pb.get('steps', []))}
          <h4>Verification Checks</h4>
          <ul class="check-list">{"".join(f'<li>{_esc(c)}</li>' for c in pb.get('verification_checks', [])) if pb.get('verification_checks') else '<li class="empty">Not documented</li>'}</ul>
          {'<h4>Common Failure Modes</h4><div class="failures-group">' + failures_html + '</div>' if failures_html else ''}
          {_callout_list(pb.get('missing_information_behavior', []), 'amber') if pb.get('missing_information_behavior') else ''}
          {_callout_list(pb.get('confirmation_required_when', []), 'amber') if pb.get('confirmation_required_when') else ''}
          {_callout_list(pb.get('escalate_when', []), 'red') if pb.get('escalate_when') else ''}
          {refs_html}
        </div>
        """
        playbooks_html += pb_content

    # ----- 6. Operating Rules -----
    always_do = operating_rules.get("always_do", [])
    never_do = operating_rules.get("never_do", [])
    rules_html = f"""
    <div class="rules-grid">
      <div class="rules-col rules-always">
        <h3>Always Do</h3>
        {_list_html(always_do)}
      </div>
      <div class="rules-col rules-never">
        <h3>Never Do</h3>
        {_list_html(never_do)}
      </div>
    </div>
    <h3>Verify Before Write Actions</h3>
    {_list_html(operating_rules.get('verify_before_write_actions', []))}
    <h3>Verify After Write Actions</h3>
    {_list_html(operating_rules.get('verify_after_write_actions', []))}
    <h3>Ambiguity Rules</h3>
    {_list_html(operating_rules.get('ambiguity_rules', []))}
    <h3>Environment Rules</h3>
    {_list_html(operating_rules.get('environment_rules', []))}
    <h3>Retry &amp; Idempotency Rules</h3>
    {_list_html(operating_rules.get('retry_idempotency_rules', []))}
    """

    # ----- 7. Decision Guide -----
    dg_html = ""
    for dg in decision_guide:
        dg_html += f"""
        <div class="decision-card">
          <h3>{_esc(dg.get('decision', ''))}</h3>
          <div class="dg-grid">
            <div><h4>Choose When</h4>{_list_html(dg.get('choose_when', []))}</div>
            <div><h4>Avoid When</h4>{_list_html(dg.get('avoid_when', []))}</div>
            <div><h4>Prefer Instead</h4>{_list_html(dg.get('prefer_instead', []))}</div>
            <div><h4>Escalate When</h4>{_list_html(dg.get('escalate_when', []))}</div>
          </div>
        </div>
        """

    # ----- 8. Troubleshooting -----
    ts_html = ""
    for ts in troubleshooting:
        ts_refs = ts.get("source_refs", [])
        ts_refs_html = ""
        if ts_refs:
            ts_refs_html = '<div class="pb-refs"><strong>Sources:</strong> '
            ts_refs_html += ", ".join(f'<a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a>' for r in ts_refs)
            ts_refs_html += '</div>'

        ts_html += f"""
        <div class="ts-card">
          <h3>{_esc(ts.get('issue', ''))}</h3>
          <h4>Signals</h4>{_list_html(ts.get('signals', []))}
          <h4>Likely Causes</h4>{_list_html(ts.get('likely_causes', []))}
          <h4>Recommended Actions</h4>{_list_html(ts.get('recommended_actions', []))}
          <h4>Do Not Do</h4>{_list_html(ts.get('do_not_do', []))}
          {_callout_list(ts.get('escalate_when', []), 'red') if ts.get('escalate_when') else ''}
          {ts_refs_html}
        </div>
        """

    # ----- 9. References by Topic -----
    rbt_html = ""
    for topic_group in references_by_topic:
        refs = topic_group.get("references", [])
        links = ""
        for r in refs:
            links += f'<li><a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a> &mdash; <span class="ref-reason">{_esc(r.get("reason", ""))}</span></li>'
        rbt_html += f"""
        <div class="ref-topic">
          <h3>{_esc(topic_group.get('topic', ''))}</h3>
          <ul>{links if links else '<li class="empty">None</li>'}</ul>
        </div>
        """

    # ----- 10. Implementation Notes -----
    impl_html = f"""
    <h3>Customer Page Must Include</h3>
    {_list_html(impl_notes.get('customer_page_must_include', []))}
    <h3>Doc Gaps / Unclear Areas</h3>
    {_list_html(impl_notes.get('doc_gaps_or_unclear_areas', []))}
    """

    # ----- Assemble sections with draft gating -----
    sections = ""
    # Always visible: hero (rendered outside sections), agent_scope, setup_access, first 2 playbooks, operating_rules
    sections += _section("Agent Scope", scope_html, section_id="agent-scope")
    sections += _section("Suitability", suit_html, locked=is_draft, section_id="suitability")
    sections += _section("Setup &amp; Access", setup_html, section_id="setup-access")
    sections += _section("Task Playbooks", playbooks_html, section_id="task-playbooks")
    sections += _section("Operating Rules", rules_html, section_id="operating-rules")
    sections += _section("Decision Guide", dg_html, locked=is_draft, section_id="decision-guide")
    sections += _section("Troubleshooting", ts_html, locked=is_draft, section_id="troubleshooting")
    sections += _section("References by Topic", rbt_html, locked=is_draft, section_id="references")
    sections += _section("Implementation Notes", impl_html, locked=is_draft, section_id="impl-notes")

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(product_name)} &mdash; Agent Operating Guide | GrounDocs</title>
<meta name="description" content="Agent operating guide for {_esc(product_name)}. Generated by GrounDocs.">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#FAFAF8;--surface:#FFFFFF;--border:#E2E2DC;
  --text:#18181B;--muted:#71717A;
  --accent:#1A7A4C;--accent-light:#E8F5EE;
  --radius-sm:6px;--radius-md:12px;--radius-lg:20px;
}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.65;
  -webkit-font-smoothing:antialiased;
}}
.container{{max-width:900px;margin:0 auto;padding:2rem 1.5rem 4rem}}

/* Hero */
.hero{{text-align:center;padding:3rem 0 2.5rem;border-bottom:1px solid var(--border);margin-bottom:2rem}}
.hero h1{{
  font-family:Georgia,'Times New Roman',serif;font-size:2.75rem;font-weight:400;
  color:var(--text);margin-bottom:0.5rem;letter-spacing:-0.02em;
}}
.mode-badge{{
  display:inline-block;padding:0.25rem 0.85rem;border-radius:100px;
  font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
  color:#fff;margin-bottom:1rem;
}}
.hero-summary{{color:var(--muted);font-size:1.1rem;max-width:640px;margin:0.5rem auto}}
.hero-agent-fit{{color:var(--text);font-size:0.95rem;max-width:640px;margin:0.75rem auto 1rem;font-weight:500}}

/* Sections */
.section{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:2rem 2.25rem;margin-bottom:1.5rem;position:relative;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.03);
}}
.section h2{{
  font-family:Georgia,'Times New Roman',serif;font-size:1.45rem;font-weight:400;
  color:var(--text);margin-bottom:1.25rem;letter-spacing:-0.01em;
  padding-bottom:0.75rem;border-bottom:1px solid var(--border);
}}
.section h3{{font-size:0.95rem;font-weight:700;color:var(--text);margin:1.25rem 0 0.5rem}}
.section h4{{font-size:0.85rem;font-weight:700;color:var(--muted);margin:1rem 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em}}
.section p{{color:var(--muted);margin-bottom:0.5rem}}
.section ul,.section ol{{padding-left:1.5rem;color:var(--muted);margin-bottom:0.75rem}}
.section li{{margin-bottom:0.35rem}}
.section li::marker{{color:var(--accent)}}
.empty{{color:#B0ADA8;font-style:italic}}

/* Risk badges */
.risk-badge,.confidence-badge{{
  display:inline-block;padding:0.2rem 0.65rem;border-radius:100px;
  font-size:0.7rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.04em;
  margin-right:0.4rem;
}}

/* Scope grid */
.scope-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem}}
.scope-col{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:1.25rem}}
.scope-header{{font-size:0.9rem;font-weight:700;padding-bottom:0.5rem;margin:0 0 0.75rem!important}}
.scope-list{{list-style:none;padding:0!important}}
.scope-list>li{{padding:0.5rem 0;border-bottom:1px solid var(--border);font-size:0.9rem}}
.scope-list>li:last-child{{border-bottom:none}}
.scope-reason{{color:var(--muted);font-size:0.82rem;display:block;margin-top:0.15rem}}
.scope-sub{{margin-top:0.35rem;padding-left:1.25rem!important;font-size:0.82rem}}
.scope-sub li{{border:none!important;padding:0.15rem 0!important}}

/* Suitability grid */
.suit-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem}}
.suit-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:1.25rem}}
.suit-card h3{{margin-top:0!important;font-size:0.9rem}}

/* Playbook cards */
.playbook-card{{
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);
  padding:1.5rem;margin-bottom:1.25rem;
}}
.playbook-card.locked-inner{{filter:blur(4px);opacity:0.5;pointer-events:none;user-select:none}}
.pb-header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.75rem}}
.pb-header h3{{margin:0!important;color:var(--accent);font-size:1.05rem}}
.pb-badges{{display:flex;gap:0.3rem;flex-wrap:wrap}}
.pb-goal{{color:var(--text)!important;font-size:0.95rem;margin-bottom:0.75rem!important}}
.pb-when{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:0.5rem}}
.pb-refs{{margin-top:0.75rem;font-size:0.85rem;color:var(--muted)}}
.pb-refs a{{color:var(--accent);text-decoration:none;font-weight:600}}
.pb-refs a:hover{{text-decoration:underline}}

/* Inputs table */
.inputs-table{{width:100%;border-collapse:collapse;margin:0.75rem 0;font-size:0.88rem}}
.inputs-table th{{text-align:left;padding:0.5rem 0.75rem;background:var(--surface);border-bottom:2px solid var(--border);color:var(--text);font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.03em}}
.inputs-table td{{padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);color:var(--muted)}}
.inputs-table code{{background:var(--surface);padding:0.15rem 0.4rem;border-radius:4px;font-size:0.82rem;color:var(--text)}}

/* Failure modes */
.failures-group{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:1rem;margin:0.5rem 0}}
.failure-mode{{padding:0.5rem 0;border-bottom:1px solid var(--border)}}
.failure-mode:last-child{{border-bottom:none}}

/* Check list */
.check-list{{list-style:none!important;padding-left:0!important}}
.check-list li::before{{content:"\\2713 ";color:var(--accent);font-weight:700;margin-right:0.3rem}}

/* Rules */
.rules-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}}
.rules-col{{background:var(--bg);border-radius:var(--radius-md);padding:1.25rem}}
.rules-always{{border-left:4px solid #1A7A4C}}
.rules-never{{border-left:4px solid #DC2626}}
.rules-col h3{{margin-top:0!important}}

/* Decision guide */
.decision-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:1.25rem;margin-bottom:1rem}}
.decision-card h3{{margin-top:0!important;color:var(--accent)}}
.dg-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}

/* Troubleshooting */
.ts-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:1.25rem;margin-bottom:1rem}}
.ts-card h3{{margin-top:0!important;color:var(--text)}}

/* Reference topics */
.ref-topic{{margin-bottom:1rem}}
.ref-topic h3{{margin-top:0.5rem!important}}
.ref-topic a{{color:var(--accent);text-decoration:none;font-weight:600}}
.ref-topic a:hover{{text-decoration:underline}}
.ref-reason{{color:var(--muted);font-size:0.85rem}}

/* Callout */
.callout{{font-size:0.9rem}}
.callout ul{{margin:0}}

/* Detail helper */
.detail{{margin-top:0.5rem;margin-bottom:0.5rem}}

/* Lock overlay */
.section.locked{{min-height:220px}}
.section.locked>*:not(h2):not(.lock-overlay){{filter:blur(5px);opacity:0.4;pointer-events:none;user-select:none}}
.lock-overlay{{
  position:absolute;top:0;left:0;right:0;bottom:0;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(250,250,248,0) 0%,rgba(250,250,248,0.85) 35%,rgba(250,250,248,0.98) 100%);
  z-index:10;
}}
.lock-cta{{
  text-align:center;padding:2rem 2.5rem;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:0 8px 32px rgba(0,0,0,0.08);
}}
.lock-cta svg{{color:var(--accent);margin-bottom:0.5rem}}
.lock-cta p{{font-weight:700;color:var(--text);margin-bottom:1rem;font-size:1.1rem}}
.unlock-btn{{
  display:inline-block;padding:0.75rem 2.25rem;background:var(--accent);color:#fff;
  border-radius:100px;font-weight:700;text-decoration:none;font-size:0.95rem;
  transition:background 0.2s;box-shadow:0 2px 8px rgba(26,122,76,0.2);
}}
.unlock-btn:hover{{background:#15603B}}

/* Footer */
footer{{
  text-align:center;padding:2.5rem 0 1rem;color:var(--muted);font-size:0.82rem;
  border-top:1px solid var(--border);margin-top:1.5rem;
}}
footer a{{color:var(--accent);text-decoration:none;font-weight:600}}
footer a:hover{{text-decoration:underline}}

/* Responsive */
@media(max-width:768px){{
  .container{{padding:1rem 1rem 3rem}}
  .hero h1{{font-size:2rem}}
  .scope-grid,.suit-grid,.dg-grid,.pb-when,.rules-grid{{grid-template-columns:1fr}}
  .section{{padding:1.25rem 1rem}}
}}
</style>
</head>
<body>
<div class="container">
  {hero_html}
  {sections}
  <footer>
    <p>Generated by <a href="https://groundocs.com" target="_blank">GrounDocs</a> &mdash; Agent Operating Guide</p>
    <p style="margin-top:0.35rem;font-size:0.75rem;color:#B0ADA8">{timestamp}</p>
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
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:#FAFAF8;color:#18181B;display:flex;align-items:center;justify-content:center;
  min-height:100vh;margin:0;
}}
.card{{
  text-align:center;background:#fff;border:1px solid #E2E2DC;border-radius:20px;
  padding:3rem 2.5rem;max-width:480px;box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
h1{{font-family:Georgia,serif;font-weight:400;font-size:1.75rem;margin-bottom:1rem}}
p{{color:#71717A;margin-bottom:1.5rem}}
.spinner{{
  width:40px;height:40px;border:3px solid #E2E2DC;border-top-color:#1A7A4C;
  border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 1.5rem;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<div class="card">
  <div class="spinner"></div>
  <h1>Building your agent operating guide</h1>
  <p>We&rsquo;re crawling <strong>{_esc(product_name)}</strong> docs and building your agent operating guide. This usually takes 30&ndash;60 seconds.</p>
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
