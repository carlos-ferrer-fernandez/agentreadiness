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

Additional output quality rules:
- Keep all text concise. Prefer 5-8 word bullets over full sentences.
- For task playbooks, use this order: Ask for -> Check -> Do -> Verify -> Confirm before -> Escalate if -> References
- Do not center playbooks around raw API endpoints or SDK syntax in the main narrative.
- Focus on behavioral guidance: what to do, what to check, when to stop.
- Do not include exact time windows, thresholds, expiration periods, retry counts, or irreversible-behavior claims unless they appear verbatim in the source documentation.
- If uncertain about a specific number or policy, say "not clearly documented" or phrase it generally.
- Avoid repeating the product overview in multiple sections.
- The hero summary should be 1-2 sentences maximum.
- agent_fit_summary should be a short bullet list, not a paragraph.
- high_risk_notice should be one sentence.
- Each task_playbook should have 3-6 steps maximum, not 8-10.
- operating_rules bullets should be under 12 words each.

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

def _esc(text: str) -> str:
    """HTML-escape user-provided text for safe insertion into HTML.

    Avoids double-escaping: if text already contains &amp; etc., we don't
    re-escape the ampersand.
    """
    import html as _html_mod
    # First, unescape any existing HTML entities to normalize
    normalized = _html_mod.unescape(str(text))
    # Then escape once cleanly
    return (
        normalized.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_agent_page_html(
    content_json: dict,
    product_name: str,
    slug: str,
    mode: str = "draft",
) -> str:
    """Render a premium, scannable agent operating guide HTML page."""
    import datetime

    is_draft = mode == "draft"
    badge_color = "#D97706" if is_draft else "#1A7A4C"
    badge_text = "Draft Preview" if is_draft else "Full Operating Guide"
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # -- Extract sections --
    hero = content_json.get("hero", {})
    agent_scope = content_json.get("agent_scope", {})
    setup_access = content_json.get("setup_access", {})
    task_playbooks = content_json.get("task_playbooks", [])
    operating_rules = content_json.get("operating_rules", {})
    decision_guide = content_json.get("decision_guide", [])
    troubleshooting = content_json.get("troubleshooting", [])
    references_by_topic = content_json.get("references_by_topic", [])

    # -- Helpers --
    def _bullets(items: list, max_items: int = 0) -> str:
        if not items:
            return '<p class="empty">Not documented</p>'
        subset = items[:max_items] if max_items else items
        return "<ul>" + "".join(f"<li>{_esc(str(i))}</li>" for i in subset) + "</ul>"

    def _risk_badge(level: str) -> str:
        cfg = {
            "safe_read": ("#DCFCE7", "#166534", "Safe Read"),
            "safe_write": ("#DBEAFE", "#1E40AF", "Safe Write"),
            "requires_confirmation": ("#FEF3C7", "#92400E", "Confirm"),
            "requires_escalation": ("#FEE2E2", "#991B1B", "Escalate"),
            "high_risk": ("#991B1B", "#FFFFFF", "High Risk"),
        }
        bg, fg, label = cfg.get(level, ("#F4F4F5", "#71717A", level.replace("_", " ").title()))
        return f'<span class="badge" style="background:{bg};color:{fg}">{label}</span>'

    def _confidence_badge(level: str) -> str:
        cfg = {"high": ("#DCFCE7", "#166534"), "medium": ("#FEF3C7", "#92400E"), "low": ("#FEE2E2", "#991B1B")}
        bg, fg = cfg.get(level, ("#F4F4F5", "#71717A"))
        return f'<span class="badge" style="background:{bg};color:{fg}">{level.title()}</span>'

    def _lock_overlay() -> str:
        return (
            '<div class="lock-overlay">'
            '<div class="lock-cta">'
            '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>'
            '<p>Unlock Full Operating Guide &mdash; $99</p>'
            f'<a href="/agent-pages/{_esc(slug)}/unlock" class="unlock-btn">Unlock Now</a>'
            '</div></div>'
        )

    # ===== 1. HERO =====
    high_risk = hero.get("high_risk_notice", "")
    high_risk_html = ""
    if high_risk:
        high_risk_html = f'<div class="high-risk-banner">{_esc(high_risk)}</div>'

    hero_html = f"""
    <header class="hero">
      <h1>{_esc(product_name)}</h1>
      <p class="hero-summary">{_esc(hero.get("summary", ""))}</p>
      <div class="hero-badges">
        <span class="badge badge-mode" style="background:{badge_color};color:#fff">{badge_text}</span>
        <span class="badge" style="background:#F4F4F5;color:#71717A">Agent Operating Guide</span>
      </div>
      {high_risk_html}
    </header>"""

    # ===== 2. QUICK SCOPE CARDS =====
    safe_items = agent_scope.get("safe_without_approval", [])
    confirm_items = agent_scope.get("requires_confirmation", [])
    escalate_items = agent_scope.get("requires_escalation", [])
    never_items = operating_rules.get("never_do", [])

    def _scope_bullets(items: list, key: str = "action", max_n: int = 5) -> str:
        if not items:
            return '<p class="empty">None documented</p>'
        out = "<ul>"
        for item in items[:max_n]:
            text = item.get(key, str(item)) if isinstance(item, dict) else str(item)
            out += f"<li>{_esc(text)}</li>"
        out += "</ul>"
        return out

    scope_html = f"""
    <section class="section" id="quick-scope">
      <h2>What Can Agents Do?</h2>
      <div class="scope-grid">
        <div class="scope-card scope-green">
          <h3>Agents can help with</h3>
          {_scope_bullets(safe_items)}
        </div>
        <div class="scope-card scope-amber">
          <h3>Requires confirmation</h3>
          {_scope_bullets(confirm_items)}
        </div>
        <div class="scope-card scope-red">
          <h3>Requires escalation</h3>
          {_scope_bullets(escalate_items)}
        </div>
        <div class="scope-card scope-darkred">
          <h3>Never do</h3>
          {_scope_bullets(never_items, max_n=5)}
        </div>
      </div>
    </section>"""

    # ===== 3. TOP AGENT TASKS (compact summary) =====
    task_summary_items = ""
    for idx, pb in enumerate(task_playbooks):
        task_summary_items += (
            f'<a href="#playbook-{idx}" class="task-summary-card">'
            f'<div class="task-summary-header">'
            f'<span class="task-summary-name">{_esc(pb.get("task_name", ""))}</span>'
            f'{_risk_badge(pb.get("risk_level", ""))}'
            f'</div>'
            f'<p>{_esc(pb.get("goal", ""))}</p>'
            f'</a>'
        )
    tasks_summary_html = f"""
    <section class="section" id="common-tasks">
      <h2>Common Agent Tasks</h2>
      <div class="tasks-summary-grid">{task_summary_items}</div>
    </section>"""

    # ===== 4. SETUP & ACCESS =====
    auth = setup_access.get("authentication", {})
    auth_methods = auth.get("methods", [])
    auth_pills = "".join(
        f'<span class="badge" style="background:#DBEAFE;color:#1E40AF">{_esc(m)}</span>'
        for m in auth_methods
    ) if auth_methods else '<span class="empty">Not documented</span>'

    env_notes = auth.get("environment_notes", [])
    env_html = ""
    if env_notes:
        env_html = '<div class="env-callout">' + "".join(f"<p>{_esc(str(n))}</p>" for n in env_notes) + "</div>"

    setup_html = f"""
    <section class="section" id="setup-access">
      <h2>Setup &amp; Access</h2>
      <h3>Prerequisites</h3>
      {_bullets(setup_access.get("prerequisites", []))}
      <h3>Authentication</h3>
      <div class="auth-pills">{auth_pills}</div>
      {env_html}
    </section>"""

    # ===== 5. TASK PLAYBOOKS (detailed) =====
    playbooks_html_parts = []
    for idx, pb in enumerate(task_playbooks):
        locked_pb = is_draft and idx >= 2
        locked_cls = " locked-inner" if locked_pb else ""

        # Ask for / Check / Do grid
        req_inputs = pb.get("required_inputs", [])
        ask_items = "".join(f"<li>{_esc(inp.get('name', ''))}</li>" for inp in req_inputs)
        pre_checks = pb.get("pre_checks", [])
        check_items = "".join(f"<li>{_esc(str(c))}</li>" for c in pre_checks[:4])
        steps = pb.get("steps", [])
        step_items = "".join(f"<li>{_esc(str(s))}</li>" for s in steps[:6])

        # Verify / Confirm before / Escalate if grid
        verify = pb.get("verification_checks", [])
        verify_items = "".join(f'<li class="check-item">{_esc(str(v))}</li>' for v in verify[:4])
        confirm_when = pb.get("confirmation_required_when", [])
        confirm_items_html = "".join(f'<li class="warn-item">{_esc(str(c))}</li>' for c in confirm_when[:4])
        escalate_when = pb.get("escalate_when", [])
        escalate_items_html = "".join(f'<li class="danger-item">{_esc(str(e))}</li>' for e in escalate_when[:4])

        # Common failures (compact)
        failures = pb.get("common_failure_modes", [])
        failures_html = ""
        if failures:
            rows = ""
            for fm in failures[:3]:
                issue = _esc(fm.get("issue", ""))
                recovery = fm.get("safe_recovery", [])
                rec_text = _esc(recovery[0]) if recovery else "See docs"
                rows += f"<tr><td><strong>{issue}</strong></td><td>{rec_text}</td></tr>"
            failures_html = f'<div class="pb-sub"><h4>Common Failures</h4><table class="compact-table"><tbody>{rows}</tbody></table></div>'

        # References
        refs = pb.get("source_refs", [])
        refs_html = ""
        if refs:
            links = ", ".join(
                f'<a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a>'
                for r in refs
            )
            refs_html = f'<div class="pb-sub"><h4>References</h4><p>{links}</p></div>'

        pb_html = f"""
        <div class="playbook-card{locked_cls}" id="playbook-{idx}">
          <div class="pb-header">
            <h3>{_esc(pb.get("task_name", ""))}</h3>
            <div class="pb-badges">{_risk_badge(pb.get("risk_level", ""))}{_confidence_badge(pb.get("confidence", "medium"))}</div>
          </div>
          <p class="pb-goal">{_esc(pb.get("goal", ""))}</p>
          <div class="pb-grid-3">
            <div><h4>Ask for</h4><ul>{ask_items if ask_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Check</h4><ul>{check_items if check_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Do</h4><ol>{step_items if step_items else '<li class="empty">-</li>'}</ol></div>
          </div>
          <div class="pb-grid-3">
            <div><h4>Verify</h4><ul>{verify_items if verify_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Confirm before</h4><ul>{confirm_items_html if confirm_items_html else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Escalate if</h4><ul>{escalate_items_html if escalate_items_html else '<li class="empty">-</li>'}</ul></div>
          </div>
          {failures_html}
          {refs_html}
        </div>"""
        playbooks_html_parts.append(pb_html)

    playbooks_body = "".join(playbooks_html_parts)
    playbooks_section = f"""
    <section class="section" id="task-playbooks">
      <h2>Task Playbooks</h2>
      {playbooks_body}
      {_lock_overlay() if is_draft and len(task_playbooks) > 2 else ""}
    </section>"""

    # ===== 6. STOP CONDITIONS (prominent) =====
    # Collect all "stop and ask" conditions
    ask_conditions = list(operating_rules.get("ambiguity_rules", []))
    for pb in task_playbooks:
        ask_conditions.extend(pb.get("confirmation_required_when", []))
    # Collect all "stop and escalate" conditions
    esc_conditions = []
    for pb in task_playbooks:
        esc_conditions.extend(pb.get("escalate_when", []))

    ask_bullets = "".join(f"<li>{_esc(str(c))}</li>" for c in ask_conditions[:8])
    esc_bullets = "".join(f"<li>{_esc(str(c))}</li>" for c in esc_conditions[:8])

    stop_html = f"""
    <section class="section" id="stop-conditions">
      <h2>Stop Conditions</h2>
      <div class="stop-grid">
        <div class="stop-card stop-ask">
          <h3>Stop and ask if...</h3>
          <ul>{ask_bullets if ask_bullets else '<li class="empty">None documented</li>'}</ul>
        </div>
        <div class="stop-card stop-escalate">
          <h3>Stop and escalate if...</h3>
          <ul>{esc_bullets if esc_bullets else '<li class="empty">None documented</li>'}</ul>
        </div>
      </div>
    </section>"""

    # ===== 7. OPERATING RULES (compact) =====
    always_items = "".join(f"<li>{_esc(str(r))}</li>" for r in operating_rules.get("always_do", []))
    never_items_html = "".join(f"<li>{_esc(str(r))}</li>" for r in operating_rules.get("never_do", []))
    env_rules = operating_rules.get("environment_rules", [])
    retry_rules = operating_rules.get("retry_idempotency_rules", [])
    extra_rules = env_rules + retry_rules
    extra_html = ""
    if extra_rules:
        extra_html = '<h3>Environment &amp; Retry Rules</h3><ul>' + "".join(f"<li>{_esc(str(r))}</li>" for r in extra_rules) + "</ul>"

    rules_html = f"""
    <section class="section" id="operating-rules">
      <h2>Operating Rules</h2>
      <div class="rules-grid">
        <div class="rules-col rules-always"><h3>Always</h3><ul>{always_items if always_items else '<li class="empty">-</li>'}</ul></div>
        <div class="rules-col rules-never"><h3>Never</h3><ul>{never_items_html if never_items_html else '<li class="empty">-</li>'}</ul></div>
      </div>
      {extra_html}
    </section>"""

    # ===== 8. DECISION GUIDE =====
    dg_cards = ""
    for dg in decision_guide:
        choose = "".join(f"<li>{_esc(str(c))}</li>" for c in dg.get("choose_when", [])[:3])
        avoid = "".join(f"<li>{_esc(str(c))}</li>" for c in dg.get("avoid_when", [])[:3])
        esc_w = "".join(f"<li>{_esc(str(c))}</li>" for c in dg.get("escalate_when", [])[:3])
        dg_cards += f"""
        <div class="decision-card">
          <h3>{_esc(dg.get("decision", ""))}</h3>
          <div class="dg-grid">
            <div><h4>Use when</h4><ul>{choose if choose else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Avoid when</h4><ul>{avoid if avoid else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Escalate if</h4><ul>{esc_w if esc_w else '<li class="empty">-</li>'}</ul></div>
          </div>
        </div>"""

    dg_section = f"""
    <section class="section{'  locked' if is_draft else ''}" id="decision-guide">
      <h2>Decision Guide</h2>
      {dg_cards if dg_cards else '<p class="empty">Not documented</p>'}
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== 9. TROUBLESHOOTING =====
    ts_cards = ""
    for ts in troubleshooting:
        cause_items = "".join(f"<li>{_esc(str(c))}</li>" for c in ts.get("likely_causes", [])[:3])
        action_items = "".join(f"<li>{_esc(str(a))}</li>" for a in ts.get("recommended_actions", [])[:3])
        dont_items = "".join(f"<li>{_esc(str(d))}</li>" for d in ts.get("do_not_do", [])[:2])
        esc_items_ts = "".join(f"<li>{_esc(str(e))}</li>" for e in ts.get("escalate_when", [])[:2])
        ts_cards += f"""
        <div class="ts-card">
          <h3>{_esc(ts.get("issue", ""))}</h3>
          <div class="ts-grid">
            <div><h4>Likely cause</h4><ul>{cause_items if cause_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Fix</h4><ul>{action_items if action_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Don't do</h4><ul>{dont_items if dont_items else '<li class="empty">-</li>'}</ul></div>
            <div><h4>Escalate if</h4><ul>{esc_items_ts if esc_items_ts else '<li class="empty">-</li>'}</ul></div>
          </div>
        </div>"""

    ts_section = f"""
    <section class="section{' locked' if is_draft else ''}" id="troubleshooting">
      <h2>Troubleshooting</h2>
      {ts_cards if ts_cards else '<p class="empty">Not documented</p>'}
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== 10. REFERENCES =====
    ref_links = ""
    for tg in references_by_topic:
        topic = _esc(tg.get("topic", ""))
        links = "".join(
            f'<li><a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a> &mdash; {_esc(r.get("reason", ""))}</li>'
            for r in tg.get("references", [])
        )
        if links:
            ref_links += f"<h3>{topic}</h3><ul>{links}</ul>"

    ref_section = f"""
    <section class="section{' locked' if is_draft else ''}" id="references">
      <h2>References</h2>
      {ref_links if ref_links else '<p class="empty">Not documented</p>'}
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== ASSEMBLE =====
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
  --radius:12px;
}}
body{{
  font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:15px;background:var(--bg);color:var(--text);line-height:1.6;
  -webkit-font-smoothing:antialiased;
}}
.container{{max-width:960px;margin:0 auto;padding:2rem 1.5rem 4rem}}

/* Hero */
.hero{{text-align:center;padding:2.5rem 0 2rem;border-bottom:1px solid var(--border);margin-bottom:1.5rem}}
.hero h1{{
  font-family:Georgia,'Times New Roman',serif;font-size:2.75rem;font-weight:400;
  color:var(--text);margin-bottom:0.4rem;letter-spacing:-0.02em;
}}
.hero-summary{{color:var(--muted);font-size:1.05rem;max-width:600px;margin:0 auto 0.75rem}}
.hero-badges{{display:flex;gap:0.5rem;justify-content:center;flex-wrap:wrap;margin-bottom:0.75rem}}
.high-risk-banner{{
  display:inline-block;background:#FEF3C7;color:#92400E;padding:0.4rem 1rem;
  border-radius:100px;font-size:0.85rem;font-weight:600;margin-top:0.25rem;
}}

/* Badge (universal pill) */
.badge{{
  display:inline-block;padding:0.15rem 0.6rem;border-radius:100px;
  font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;
  white-space:nowrap;vertical-align:middle;
}}
.badge-mode{{font-size:0.65rem;letter-spacing:0.06em}}

/* Sections */
.section{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.75rem 2rem;margin-bottom:1.25rem;position:relative;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.03);
}}
.section h2{{
  font-family:Georgia,'Times New Roman',serif;font-size:1.35rem;font-weight:400;
  color:var(--text);margin-bottom:1rem;padding-bottom:0.6rem;border-bottom:1px solid var(--border);
}}
.section h3{{font-size:0.88rem;font-weight:700;color:var(--text);margin:1rem 0 0.4rem}}
.section h4{{font-size:0.75rem;font-weight:700;color:var(--muted);margin:0.75rem 0 0.3rem;text-transform:uppercase;letter-spacing:0.04em}}
.section p{{color:var(--muted);margin-bottom:0.4rem;font-size:0.9rem}}
.section ul,.section ol{{padding-left:1.25rem;color:var(--muted);margin-bottom:0.5rem;font-size:0.88rem}}
.section li{{margin-bottom:0.25rem}}
.section li::marker{{color:var(--accent)}}
.empty{{color:#B0ADA8;font-style:italic;font-size:0.85rem}}

/* Quick Scope Cards */
.scope-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem}}
.scope-card{{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1rem 1.1rem;
}}
.scope-card h3{{font-size:0.8rem;font-weight:700;margin:0 0 0.5rem!important;text-transform:uppercase;letter-spacing:0.03em}}
.scope-card ul{{padding-left:1rem;margin:0;font-size:0.82rem}}
.scope-card li{{margin-bottom:0.2rem}}
.scope-green{{border-left:3px solid #1A7A4C}}
.scope-green h3{{color:#166534}}
.scope-amber{{border-left:3px solid #D97706}}
.scope-amber h3{{color:#92400E}}
.scope-red{{border-left:3px solid #DC2626}}
.scope-red h3{{color:#991B1B}}
.scope-darkred{{border-left:3px solid #7F1D1D}}
.scope-darkred h3{{color:#7F1D1D}}

/* Task summary grid */
.tasks-summary-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:0.75rem}}
.task-summary-card{{
  display:block;text-decoration:none;color:inherit;
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);
  padding:0.85rem 1rem;transition:border-color 0.15s;
}}
.task-summary-card:hover{{border-color:var(--accent)}}
.task-summary-header{{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem}}
.task-summary-name{{font-weight:700;font-size:0.9rem;color:var(--text)}}
.task-summary-card p{{font-size:0.82rem;color:var(--muted);margin:0}}

/* Auth pills */
.auth-pills{{display:flex;gap:0.4rem;flex-wrap:wrap;margin:0.5rem 0}}
.env-callout{{
  background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
  padding:0.6rem 0.85rem;margin-top:0.5rem;font-size:0.85rem;color:#166534;
}}

/* Playbook cards */
.playbook-card{{
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.25rem 1.5rem;margin-bottom:1rem;
}}
.playbook-card.locked-inner{{filter:blur(4px);opacity:0.5;pointer-events:none;user-select:none}}
.pb-header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem}}
.pb-header h3{{margin:0!important;color:var(--accent);font-size:1rem}}
.pb-badges{{display:flex;gap:0.3rem;flex-wrap:wrap}}
.pb-goal{{font-size:0.9rem;color:var(--text)!important;margin-bottom:0.75rem!important;font-weight:500}}
.pb-grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;margin-bottom:0.5rem}}
.pb-grid-3 ul,.pb-grid-3 ol{{font-size:0.82rem;padding-left:1.1rem;margin:0}}
.pb-grid-3 h4{{margin-top:0}}
.pb-sub{{margin-top:0.5rem}}
.compact-table{{width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:0.25rem}}
.compact-table td{{padding:0.3rem 0.5rem;border-bottom:1px solid var(--border);color:var(--muted)}}
.check-item::marker{{content:"\\2713  ";color:var(--accent)}}
.warn-item::marker{{content:"\\26A0  ";color:#D97706}}
.danger-item::marker{{content:"\\1F534  "}}

/* Stop conditions */
.stop-grid{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem}}
.stop-card{{border-radius:var(--radius);padding:1.25rem 1.5rem}}
.stop-card h3{{margin:0 0 0.5rem!important;font-size:0.9rem}}
.stop-card ul{{font-size:0.85rem;padding-left:1.25rem;margin:0}}
.stop-card li{{margin-bottom:0.2rem}}
.stop-ask{{background:#FFFBEB;border:1px solid #FDE68A}}
.stop-ask h3{{color:#92400E}}
.stop-escalate{{background:#FEF2F2;border:1px solid #FECACA}}
.stop-escalate h3{{color:#991B1B}}

/* Rules */
.rules-grid{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:0.75rem}}
.rules-col{{background:var(--bg);border-radius:var(--radius);padding:1rem 1.25rem}}
.rules-always{{border-left:3px solid #1A7A4C}}
.rules-never{{border-left:3px solid #DC2626}}
.rules-col h3{{margin-top:0!important;font-size:0.85rem}}
.rules-col ul{{font-size:0.85rem}}

/* Decision guide */
.decision-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;margin-bottom:0.75rem}}
.decision-card h3{{margin-top:0!important;color:var(--accent);font-size:0.95rem}}
.dg-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem}}
.dg-grid ul{{font-size:0.82rem}}

/* Troubleshooting */
.ts-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;margin-bottom:0.75rem}}
.ts-card h3{{margin-top:0!important;font-size:0.95rem}}
.ts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:0.5rem}}
.ts-grid ul{{font-size:0.82rem}}

/* References */
#references h3{{font-size:0.85rem;margin-top:0.75rem!important}}
#references ul{{font-size:0.85rem}}
#references a{{color:var(--accent);text-decoration:none;font-weight:600}}
#references a:hover{{text-decoration:underline}}

/* Lock overlay */
.section.locked{{min-height:200px}}
.section.locked>*:not(h2):not(.lock-overlay){{filter:blur(5px);opacity:0.4;pointer-events:none;user-select:none}}
.lock-overlay{{
  position:absolute;top:0;left:0;right:0;bottom:0;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(250,250,248,0) 0%,rgba(250,250,248,0.85) 35%,rgba(250,250,248,0.98) 100%);
  z-index:10;
}}
.lock-cta{{
  text-align:center;padding:1.5rem 2rem;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius);box-shadow:0 8px 32px rgba(0,0,0,0.08);
}}
.lock-cta svg{{color:var(--accent);margin-bottom:0.5rem}}
.lock-cta p{{font-weight:700;color:var(--text);margin-bottom:0.75rem;font-size:1rem}}
.unlock-btn{{
  display:inline-block;padding:0.6rem 2rem;background:var(--accent);color:#fff;
  border-radius:100px;font-weight:700;text-decoration:none;font-size:0.9rem;
  transition:background 0.2s;box-shadow:0 2px 8px rgba(26,122,76,0.2);
}}
.unlock-btn:hover{{background:#15603B}}

/* Footer */
footer{{
  text-align:center;padding:2rem 0 1rem;color:var(--muted);font-size:0.8rem;
  border-top:1px solid var(--border);margin-top:1.25rem;
}}
footer a{{color:var(--accent);text-decoration:none;font-weight:600}}
footer a:hover{{text-decoration:underline}}

/* Responsive */
@media(max-width:768px){{
  .container{{padding:1rem 1rem 3rem}}
  .hero h1{{font-size:2rem}}
  .scope-grid{{grid-template-columns:1fr 1fr}}
  .tasks-summary-grid,.pb-grid-3,.dg-grid,.stop-grid,.rules-grid,.ts-grid{{grid-template-columns:1fr}}
  .section{{padding:1.25rem 1rem}}
}}
@media(max-width:480px){{
  .scope-grid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="container">
  {hero_html}
  {scope_html}
  {tasks_summary_html}
  {setup_html}
  {playbooks_section}
  {stop_html}
  {rules_html}
  {dg_section}
  {ts_section}
  {ref_section}
  <footer>
    <p>Generated by <a href="https://groundocs.com" target="_blank">GrounDocs</a> &mdash; Agent Operating Guide</p>
    <p style="margin-top:0.25rem;font-size:0.72rem;color:#B0ADA8">{timestamp}</p>
  </footer>
</div>
</body>
</html>
"""
    return html


def render_generating_html(product_name: str, slug: str) -> str:
    """Return a generating page with auto-refresh, matching the new design."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="5">
<title>{_esc(product_name)} &mdash; Generating... | GrounDocs</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{
  font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:#FAFAF8;color:#18181B;display:flex;align-items:center;justify-content:center;
  min-height:100vh;margin:0;
}}
.card{{
  text-align:center;background:#fff;border:1px solid #E2E2DC;border-radius:12px;
  padding:2.5rem 2rem;max-width:440px;box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
h1{{font-family:Georgia,serif;font-weight:400;font-size:1.6rem;margin-bottom:0.75rem}}
p{{color:#71717A;margin-bottom:1rem;font-size:0.95rem}}
.spinner{{
  width:36px;height:36px;border:3px solid #E2E2DC;border-top-color:#1A7A4C;
  border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 1.25rem;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.hint{{font-size:0.8rem;color:#B0ADA8}}
</style>
</head>
<body>
<div class="card">
  <div class="spinner"></div>
  <h1>Building your agent guide</h1>
  <p>Crawling <strong>{_esc(product_name)}</strong> docs and generating your agent operating guide. This usually takes 30-60 seconds.</p>
  <p class="hint">This page refreshes automatically.</p>
</div>
</body>
</html>
"""


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
