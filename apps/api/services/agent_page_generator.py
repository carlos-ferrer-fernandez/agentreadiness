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

SYSTEM_PROMPT = """You are an expert technical writer creating agent operating guides.

Your job: produce a concise, scannable operating page that tells AI agents what they can do, what requires approval, and when to stop.

The page is NOT a documentation summary. It is a behavioral rulebook for agents.

Key principles:
1. Lead with boundaries: what's safe, what needs confirmation, what's forbidden
2. Task playbooks: behavioral steps, not API reference
3. Stop conditions: prominent, specific, non-negotiable
4. Every bullet under 10 words when possible
5. No marketing, no filler, no repeated explanations
6. Never invent thresholds, timeouts, retry counts, or policies not in the source docs
7. If uncertain, say "check docs" or "not clearly documented"

Playbook format for each task:
- Ask for: required inputs
- Check: preconditions to verify
- Do: 3-5 behavioral steps (not code)
- Verify: how to confirm success
- Confirm before: when to pause for human approval
- Escalate if: when to hand off entirely

Stop conditions format:
- stop_and_ask: situations where agent must pause and ask the human
- stop_and_escalate: situations where agent must hand off to a human entirely

Output rules:
- Bullets under 10 words preferred
- Hero summary: 1 sentence max
- No section should repeat content from another section
- Playbooks: 3-5 Do steps max
- Operating rules: under 8 words each
- Never list items should be absolute prohibitions, not cautionary advice

Return valid JSON only. No markdown fences. No commentary."""

JSON_SCHEMA_DESCRIPTION = """\
{
  "meta": {
    "product_name": "string",
    "slug": "string",
    "mode": "draft | full",
    "docs_root_url": "string"
  },
  "hero": {
    "summary": "One sentence: what this product does",
    "high_risk_notice": "One sentence: the biggest risk agents should know"
  },
  "agent_scope": {
    "safe_without_approval": [
      {"action": "short action name", "risk_level": "safe_read | safe_write"}
    ],
    "requires_confirmation": [
      {"action": "short action name", "risk_level": "requires_confirmation", "confirm_what": ["string"]}
    ],
    "requires_escalation": [
      {"action": "short action name", "risk_level": "requires_escalation"}
    ],
    "never_do": ["short absolute prohibition"]
  },
  "stop_conditions": {
    "stop_and_ask": ["specific situation requiring human input"],
    "stop_and_escalate": ["specific situation requiring full handoff"]
  },
  "task_playbooks": [
    {
      "task_name": "string",
      "goal": "one sentence",
      "risk_level": "safe_read | safe_write | requires_confirmation | requires_escalation",
      "ask_for": ["required input"],
      "check": ["precondition"],
      "do": ["behavioral step"],
      "verify": ["success check"],
      "confirm_before": ["when to pause"],
      "escalate_if": ["when to hand off"],
      "refs": [{"label": "string", "url": "string"}]
    }
  ],
  "operating_rules": {
    "always": ["short rule"],
    "never": ["short prohibition"],
    "environment": ["env-specific rule"]
  },
  "setup": {
    "prerequisites": ["string"],
    "auth_methods": ["string"],
    "required_secrets": ["string"],
    "env_notes": ["string"]
  },
  "decision_guide": [
    {
      "decision": "string",
      "use_when": ["string"],
      "avoid_when": ["string"],
      "escalate_if": ["string"]
    }
  ],
  "troubleshooting": [
    {
      "issue": "string",
      "likely_cause": "string",
      "fix": "string",
      "escalate_if": "string"
    }
  ],
  "references": [
    {"label": "string", "url": "string", "topic": "string"}
  ]
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
        "critical stop conditions, and the top action boundaries."
        if mode == "draft"
        else "Produce the complete operational guide. Include all relevant task playbooks, "
        "comprehensive stop conditions, and thorough operating rules."
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
    """HTML-escape user-provided text, avoiding double-escaping."""
    import html as _html_mod
    normalized = _html_mod.unescape(str(text))
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
    badge_text = "DRAFT" if is_draft else "FULL GUIDE"
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # -- Extract sections (support both old and new schema) --
    hero = content_json.get("hero", {})
    agent_scope = content_json.get("agent_scope", {})
    stop_conditions = content_json.get("stop_conditions", {})
    task_playbooks = content_json.get("task_playbooks", [])
    operating_rules = content_json.get("operating_rules", {})
    setup = content_json.get("setup", content_json.get("setup_access", {}))
    decision_guide = content_json.get("decision_guide", [])
    troubleshooting = content_json.get("troubleshooting", [])
    references = content_json.get("references", content_json.get("references_by_topic", []))

    # -- Helpers --
    def _risk_badge(level: str) -> str:
        cfg = {
            "safe_read": ("#DCFCE7", "#166534", "SAFE"),
            "safe_write": ("#DBEAFE", "#1E40AF", "SAFE WRITE"),
            "requires_confirmation": ("#FEF3C7", "#92400E", "CONFIRM"),
            "requires_escalation": ("#FEE2E2", "#991B1B", "ESCALATE"),
            "high_risk": ("#991B1B", "#FFFFFF", "HIGH RISK"),
        }
        bg, fg, label = cfg.get(level, ("#F4F4F5", "#71717A", level.replace("_", " ").title()))
        return f'<span class="badge" style="background:{bg};color:{fg}">{label}</span>'

    def _lock_overlay() -> str:
        return (
            '<div class="lock-overlay">'
            '<div class="lock-cta">'
            '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>'
            '<p>Unlock Full Operating Guide &mdash; $99</p>'
            f'<a href="/agent-pages/{_esc(slug)}" class="unlock-btn">Unlock Now</a>'
            '</div></div>'
        )

    def _scope_list(items: list, key: str = "action") -> str:
        if not items:
            return '<li class="empty">None documented</li>'
        out = ""
        for item in items[:5]:
            text = item.get(key, str(item)) if isinstance(item, dict) else str(item)
            out += f"<li>{_esc(text)}</li>"
        return out

    # ===== 1. HERO (compact) =====
    high_risk = hero.get("high_risk_notice", "")
    high_risk_html = ""
    if high_risk:
        high_risk_html = f'<div class="hero-risk">{_esc(high_risk)}</div>'

    hero_html = f"""
    <header class="hero">
      <div class="hero-top">
        <h1>{_esc(product_name)}</h1>
        <span class="badge badge-mode" style="background:{badge_color};color:#fff">{badge_text}</span>
      </div>
      <p class="hero-sub">{_esc(hero.get("summary", ""))}</p>
      {high_risk_html}
    </header>"""

    # ===== 2. QUICK SCOPE (4 cards) =====
    safe_items = agent_scope.get("safe_without_approval", [])
    confirm_items = agent_scope.get("requires_confirmation", [])
    escalate_items = agent_scope.get("requires_escalation", [])
    never_items = agent_scope.get("never_do", operating_rules.get("never_do", operating_rules.get("never", [])))

    # Handle both dict list and string list for never_items
    never_html_items = ""
    if never_items:
        for item in never_items[:5]:
            text = item.get("action", str(item)) if isinstance(item, dict) else str(item)
            never_html_items += f"<li>{_esc(text)}</li>"
    else:
        never_html_items = '<li class="empty">None documented</li>'

    scope_html = f"""
    <section class="scope-section">
      <div class="scope-grid">
        <div class="scope-card scope-green">
          <div class="scope-icon">&#10003;</div>
          <h3>Agents can do</h3>
          <ul>{_scope_list(safe_items)}</ul>
        </div>
        <div class="scope-card scope-amber">
          <div class="scope-icon">&#9888;</div>
          <h3>Confirm first</h3>
          <ul>{_scope_list(confirm_items)}</ul>
        </div>
        <div class="scope-card scope-red">
          <div class="scope-icon">&#9757;</div>
          <h3>Escalate to human</h3>
          <ul>{_scope_list(escalate_items)}</ul>
        </div>
        <div class="scope-card scope-black">
          <div class="scope-icon">&#10005;</div>
          <h3>Never do</h3>
          <ul>{never_html_items}</ul>
        </div>
      </div>
    </section>"""

    # ===== 3. STOP CONDITIONS (prominent, right after scope) =====
    # Gather from both new schema (stop_conditions) and old schema (operating_rules.ambiguity_rules + playbook escalate_when)
    ask_conditions = list(stop_conditions.get("stop_and_ask", []))
    esc_conditions = list(stop_conditions.get("stop_and_escalate", []))

    # Fallback: pull from old schema if stop_conditions is empty
    if not ask_conditions:
        ask_conditions = list(operating_rules.get("ambiguity_rules", []))
        for pb in task_playbooks:
            for c in pb.get("confirmation_required_when", pb.get("confirm_before", [])):
                if c not in ask_conditions:
                    ask_conditions.append(c)
    if not esc_conditions:
        for pb in task_playbooks:
            for e in pb.get("escalate_when", pb.get("escalate_if", [])):
                if e not in esc_conditions:
                    esc_conditions.append(e)

    ask_bullets = "".join(f"<li>{_esc(str(c))}</li>" for c in ask_conditions[:8])
    esc_bullets = "".join(f"<li>{_esc(str(c))}</li>" for c in esc_conditions[:8])

    stop_html = f"""
    <section class="stop-section">
      <div class="stop-grid">
        <div class="stop-card stop-ask">
          <h3>&#9888; Stop and ask if&hellip;</h3>
          <ul>{ask_bullets if ask_bullets else '<li class="empty">None documented</li>'}</ul>
        </div>
        <div class="stop-card stop-escalate">
          <h3>&#128721; Stop and escalate if&hellip;</h3>
          <ul>{esc_bullets if esc_bullets else '<li class="empty">None documented</li>'}</ul>
        </div>
      </div>
    </section>"""

    # ===== 4. TOP TASKS (compact clickable cards) =====
    task_cards = ""
    for idx, pb in enumerate(task_playbooks):
        task_name = pb.get("task_name", "")
        goal = pb.get("goal", "")
        risk = pb.get("risk_level", "")
        task_cards += (
            f'<a href="#playbook-{idx}" class="task-card">'
            f'<div class="task-card-top">'
            f'<span class="task-name">{_esc(task_name)}</span>'
            f'{_risk_badge(risk)}'
            f'</div>'
            f'<p>{_esc(goal)}</p>'
            f'</a>'
        )

    tasks_html = f"""
    <section class="card" id="tasks">
      <h2>Top Agent Tasks</h2>
      <div class="tasks-grid">{task_cards}</div>
    </section>"""

    # ===== 5. TASK PLAYBOOKS (behavioral, compact) =====
    playbooks_parts = []
    for idx, pb in enumerate(task_playbooks):
        locked_pb = is_draft and idx >= 2
        locked_cls = " pb-locked" if locked_pb else ""

        # Support both old and new schema field names
        ask_for = pb.get("ask_for", [])
        if not ask_for:
            ask_for = [inp.get("name", "") for inp in pb.get("required_inputs", [])]
        check = pb.get("check", pb.get("pre_checks", []))
        do_steps = pb.get("do", pb.get("steps", []))
        verify = pb.get("verify", pb.get("verification_checks", []))
        confirm_before = pb.get("confirm_before", pb.get("confirmation_required_when", []))
        escalate_if = pb.get("escalate_if", pb.get("escalate_when", []))
        refs = pb.get("refs", pb.get("source_refs", []))

        def _mini_list(items, max_n=4, ordered=False):
            if not items:
                return '<span class="empty">-</span>'
            tag = "ol" if ordered else "ul"
            inner = "".join(f"<li>{_esc(str(i))}</li>" for i in items[:max_n])
            return f"<{tag}>{inner}</{tag}>"

        refs_html = ""
        if refs:
            links = " &middot; ".join(
                f'<a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a>'
                for r in refs
            )
            refs_html = f'<div class="pb-refs">{links}</div>'

        pb_html = f"""
        <div class="pb-card{locked_cls}" id="playbook-{idx}">
          <div class="pb-header">
            <h3>{_esc(pb.get("task_name", ""))}</h3>
            {_risk_badge(pb.get("risk_level", ""))}
          </div>
          <p class="pb-goal">{_esc(pb.get("goal", ""))}</p>
          <div class="pb-grid">
            <div class="pb-col">
              <h4>Ask for</h4>
              {_mini_list(ask_for)}
            </div>
            <div class="pb-col">
              <h4>Check</h4>
              {_mini_list(check)}
            </div>
            <div class="pb-col pb-col-wide">
              <h4>Do</h4>
              {_mini_list(do_steps, max_n=5, ordered=True)}
            </div>
          </div>
          <div class="pb-grid pb-grid-bottom">
            <div class="pb-col">
              <h4>&#10003; Verify</h4>
              {_mini_list(verify)}
            </div>
            <div class="pb-col">
              <h4>&#9888; Confirm before</h4>
              {_mini_list(confirm_before)}
            </div>
            <div class="pb-col">
              <h4>&#128721; Escalate if</h4>
              {_mini_list(escalate_if)}
            </div>
          </div>
          {refs_html}
        </div>"""
        playbooks_parts.append(pb_html)

    playbooks_body = "".join(playbooks_parts)
    playbooks_section = f"""
    <section class="card" id="playbooks">
      <h2>Task Playbooks</h2>
      {playbooks_body}
      {_lock_overlay() if is_draft and len(task_playbooks) > 2 else ""}
    </section>"""

    # ===== 6. OPERATING RULES (Always / Never, compact) =====
    always_rules = operating_rules.get("always", operating_rules.get("always_do", []))
    never_rules = operating_rules.get("never", operating_rules.get("never_do", []))
    env_rules = operating_rules.get("environment", operating_rules.get("environment_rules", []))

    always_items = "".join(f"<li>{_esc(str(r))}</li>" for r in always_rules)
    never_items_html = "".join(f"<li>{_esc(str(r))}</li>" for r in never_rules)
    env_items = "".join(f"<li>{_esc(str(r))}</li>" for r in env_rules)

    rules_html = f"""
    <section class="card" id="rules">
      <h2>Operating Rules</h2>
      <div class="rules-grid">
        <div class="rules-col rules-always">
          <h3>&#10003; Always</h3>
          <ul>{always_items if always_items else '<li class="empty">-</li>'}</ul>
        </div>
        <div class="rules-col rules-never">
          <h3>&#10005; Never</h3>
          <ul>{never_items_html if never_items_html else '<li class="empty">-</li>'}</ul>
        </div>
      </div>
      {"<details class='detail-section'><summary>Environment rules</summary><ul>" + env_items + "</ul></details>" if env_items else ""}
    </section>"""

    # ===== 7. SETUP (collapsible) =====
    # Support both old and new schema
    auth = setup.get("authentication", {})
    auth_methods = setup.get("auth_methods", auth.get("methods", []))
    required_secrets = setup.get("required_secrets", auth.get("required_secrets_or_tokens", []))
    prerequisites = setup.get("prerequisites", [])
    env_notes = setup.get("env_notes", auth.get("environment_notes", []))

    auth_pills = "".join(
        f'<span class="badge" style="background:#DBEAFE;color:#1E40AF">{_esc(m)}</span>'
        for m in auth_methods
    ) if auth_methods else ''

    prereq_items = "".join(f"<li>{_esc(str(p))}</li>" for p in prerequisites)
    secret_items = "".join(f"<li><code>{_esc(str(s))}</code></li>" for s in required_secrets)
    env_note_items = "".join(f"<li>{_esc(str(n))}</li>" for n in env_notes)

    setup_html = f"""
    <section class="card" id="setup">
      <details class="detail-section" open>
        <summary><h2>Setup &amp; Access</h2></summary>
        <div class="setup-content">
          {"<div class='auth-pills'>" + auth_pills + "</div>" if auth_pills else ""}
          {"<h4>Prerequisites</h4><ul>" + prereq_items + "</ul>" if prereq_items else ""}
          {"<h4>Required Secrets</h4><ul class='code-list'>" + secret_items + "</ul>" if secret_items else ""}
          {"<h4>Environment Notes</h4><ul>" + env_note_items + "</ul>" if env_note_items else ""}
        </div>
      </details>
    </section>"""

    # ===== 8. DECISION GUIDE (collapsible, full only) =====
    dg_cards = ""
    for dg in decision_guide:
        use_when = dg.get("use_when", dg.get("choose_when", []))
        avoid_when = dg.get("avoid_when", [])
        esc_w = dg.get("escalate_if", dg.get("escalate_when", []))
        use_items = "".join(f"<li>{_esc(str(c))}</li>" for c in use_when[:3])
        avoid_items = "".join(f"<li>{_esc(str(c))}</li>" for c in avoid_when[:3])
        esc_items = "".join(f"<li>{_esc(str(c))}</li>" for c in esc_w[:3])
        dg_cards += f"""
        <div class="dg-card">
          <h4>{_esc(dg.get("decision", ""))}</h4>
          <div class="dg-grid">
            <div><strong>Use when</strong><ul>{use_items if use_items else '<li class="empty">-</li>'}</ul></div>
            <div><strong>Avoid when</strong><ul>{avoid_items if avoid_items else '<li class="empty">-</li>'}</ul></div>
            <div><strong>Escalate if</strong><ul>{esc_items if esc_items else '<li class="empty">-</li>'}</ul></div>
          </div>
        </div>"""

    dg_section = ""
    if decision_guide:
        dg_section = f"""
    <section class="card{' section-locked' if is_draft else ''}" id="decisions">
      <details class="detail-section">
        <summary><h2>Decision Guide</h2></summary>
        {dg_cards}
      </details>
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== 9. TROUBLESHOOTING (collapsible, full only) =====
    ts_rows = ""
    for ts in troubleshooting:
        issue = ts.get("issue", "")
        cause = ts.get("likely_cause", "")
        # Fallback for old schema with list of causes
        if not cause and isinstance(ts.get("likely_causes"), list):
            cause = ts["likely_causes"][0] if ts["likely_causes"] else ""
        fix = ts.get("fix", "")
        if not fix and isinstance(ts.get("recommended_actions"), list):
            fix = ts["recommended_actions"][0] if ts["recommended_actions"] else ""
        esc = ts.get("escalate_if", "")
        if not esc and isinstance(ts.get("escalate_when"), list):
            esc = ts["escalate_when"][0] if ts["escalate_when"] else ""

        ts_rows += f"""
        <tr>
          <td><strong>{_esc(issue)}</strong></td>
          <td>{_esc(cause)}</td>
          <td>{_esc(fix)}</td>
          <td>{_esc(esc)}</td>
        </tr>"""

    ts_section = ""
    if troubleshooting:
        ts_section = f"""
    <section class="card{' section-locked' if is_draft else ''}" id="troubleshooting">
      <details class="detail-section">
        <summary><h2>Troubleshooting</h2></summary>
        <table class="ts-table">
          <thead><tr><th>Issue</th><th>Likely Cause</th><th>Fix</th><th>Escalate if</th></tr></thead>
          <tbody>{ts_rows}</tbody>
        </table>
      </details>
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== 10. REFERENCES (collapsible) =====
    ref_items = ""
    # Support both flat list and grouped list
    if references:
        if isinstance(references[0], dict) and "references" in references[0]:
            # Old schema: grouped by topic
            for tg in references:
                topic = _esc(tg.get("topic", ""))
                for r in tg.get("references", []):
                    ref_items += f'<li><a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a> <span class="ref-topic">{topic}</span></li>'
        else:
            # New schema: flat list
            for r in references:
                topic = _esc(r.get("topic", ""))
                ref_items += f'<li><a href="{_esc(r.get("url", "#"))}" target="_blank" rel="noopener">{_esc(r.get("label", ""))}</a> <span class="ref-topic">{topic}</span></li>'

    ref_section = ""
    if ref_items:
        ref_section = f"""
    <section class="card{' section-locked' if is_draft else ''}" id="references">
      <details class="detail-section">
        <summary><h2>References</h2></summary>
        <ul class="ref-list">{ref_items}</ul>
      </details>
      {_lock_overlay() if is_draft else ""}
    </section>"""

    # ===== CSS =====
    css = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#FAFAF8;--surface:#FFFFFF;--border:#E5E5E0;
  --text:#1A1A1A;--muted:#6B6B6B;--light:#9B9B9B;
  --accent:#1A7A4C;--accent-bg:#E8F5EE;
  --green:#166534;--green-bg:#F0FDF4;--green-border:#BBF7D0;
  --amber:#92400E;--amber-bg:#FFFBEB;--amber-border:#FDE68A;
  --red:#991B1B;--red-bg:#FEF2F2;--red-border:#FECACA;
  --radius:10px;
}
body{
  font-family:'Plus Jakarta Sans',system-ui,-apple-system,sans-serif;
  font-size:14px;background:var(--bg);color:var(--text);line-height:1.55;
  -webkit-font-smoothing:antialiased;
}
.container{max-width:920px;margin:0 auto;padding:1.5rem 1.5rem 3rem}

/* Hero — compact */
.hero{padding:1.5rem 0 1.25rem;border-bottom:1px solid var(--border);margin-bottom:1.25rem}
.hero-top{display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap}
.hero h1{
  font-family:'Instrument Serif',Georgia,serif;font-size:2.25rem;font-weight:400;
  color:var(--text);letter-spacing:-0.02em;margin:0;line-height:1.1;
}
.hero-sub{color:var(--muted);font-size:0.95rem;margin:0.35rem 0 0;max-width:600px}
.hero-risk{
  display:inline-block;background:var(--amber-bg);color:var(--amber);
  padding:0.3rem 0.85rem;border-radius:100px;font-size:0.78rem;font-weight:600;
  margin-top:0.6rem;border:1px solid var(--amber-border);
}

/* Badge */
.badge{
  display:inline-block;padding:0.15rem 0.55rem;border-radius:100px;
  font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
  white-space:nowrap;vertical-align:middle;
}
.badge-mode{font-size:0.6rem;letter-spacing:0.08em;padding:0.2rem 0.6rem}

/* Scope cards — the most important visual */
.scope-section{margin-bottom:1.25rem}
.scope-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem}
.scope-card{
  background:var(--surface);border-radius:var(--radius);
  padding:0.85rem 1rem;border:1px solid var(--border);position:relative;
}
.scope-icon{
  font-size:1.1rem;margin-bottom:0.25rem;
}
.scope-card h3{
  font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;
  margin:0 0 0.4rem;
}
.scope-card ul{list-style:none;padding:0;margin:0}
.scope-card li{
  font-size:0.8rem;color:var(--text);padding:0.15rem 0;
  border-bottom:1px solid rgba(0,0,0,0.04);line-height:1.35;
}
.scope-card li:last-child{border-bottom:none}
.scope-green{border-top:3px solid #1A7A4C}
.scope-green h3{color:var(--green)}
.scope-green .scope-icon{color:var(--green)}
.scope-amber{border-top:3px solid #D97706}
.scope-amber h3{color:var(--amber)}
.scope-amber .scope-icon{color:var(--amber)}
.scope-red{border-top:3px solid #DC2626}
.scope-red h3{color:var(--red)}
.scope-red .scope-icon{color:var(--red)}
.scope-black{border-top:3px solid #1A1A1A}
.scope-black h3{color:#1A1A1A}
.scope-black .scope-icon{color:#1A1A1A}

/* Stop conditions — prominent */
.stop-section{margin-bottom:1.25rem}
.stop-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.6rem}
.stop-card{border-radius:var(--radius);padding:1rem 1.15rem}
.stop-card h3{
  font-size:0.78rem;font-weight:700;margin:0 0 0.5rem;
}
.stop-card ul{list-style:none;padding:0;margin:0}
.stop-card li{
  font-size:0.82rem;padding:0.2rem 0;
  padding-left:1rem;position:relative;line-height:1.4;
}
.stop-card li::before{
  content:'';position:absolute;left:0;top:0.55rem;
  width:5px;height:5px;border-radius:50%;
}
.stop-ask{background:var(--amber-bg);border:1px solid var(--amber-border)}
.stop-ask h3{color:var(--amber)}
.stop-ask li::before{background:var(--amber)}
.stop-escalate{background:var(--red-bg);border:1px solid var(--red-border)}
.stop-escalate h3{color:var(--red)}
.stop-escalate li::before{background:var(--red)}

/* Card (section container) */
.card{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.25rem 1.5rem;margin-bottom:1rem;position:relative;overflow:hidden;
  box-shadow:0 1px 2px rgba(0,0,0,0.02);
}
.card h2{
  font-family:'Instrument Serif',Georgia,serif;font-size:1.2rem;font-weight:400;
  color:var(--text);margin:0 0 0.85rem;padding-bottom:0.5rem;
  border-bottom:1px solid var(--border);
}

/* Tasks grid */
.tasks-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem}
.task-card{
  display:block;text-decoration:none;color:inherit;
  background:var(--bg);border:1px solid var(--border);border-radius:8px;
  padding:0.65rem 0.85rem;transition:border-color 0.15s;
}
.task-card:hover{border-color:var(--accent)}
.task-card-top{display:flex;align-items:center;gap:0.4rem;margin-bottom:0.15rem}
.task-name{font-weight:700;font-size:0.82rem}
.task-card p{font-size:0.75rem;color:var(--muted);margin:0;line-height:1.35}

/* Playbook cards */
.pb-card{
  background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);
  padding:1rem 1.15rem;margin-bottom:0.75rem;
}
.pb-card.pb-locked{filter:blur(4px);opacity:0.4;pointer-events:none;user-select:none}
.pb-header{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.3rem}
.pb-header h3{margin:0;color:var(--accent);font-size:0.95rem}
.pb-goal{font-size:0.82rem;color:var(--muted);margin:0 0 0.65rem;font-weight:500}
.pb-grid{display:grid;grid-template-columns:1fr 1fr 1.5fr;gap:0.5rem;margin-bottom:0.4rem}
.pb-grid-bottom{margin-top:0.2rem;border-top:1px solid rgba(0,0,0,0.04);padding-top:0.5rem}
.pb-col h4{
  font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;
  color:var(--light);margin:0 0 0.25rem;
}
.pb-col ul,.pb-col ol{padding-left:1rem;margin:0;font-size:0.78rem;color:var(--text)}
.pb-col li{margin-bottom:0.1rem;line-height:1.35}
.pb-col-wide{grid-column:span 1}
.pb-refs{
  margin-top:0.5rem;padding-top:0.4rem;border-top:1px solid rgba(0,0,0,0.04);
  font-size:0.75rem;
}
.pb-refs a{color:var(--accent);text-decoration:none;font-weight:600}
.pb-refs a:hover{text-decoration:underline}

/* Rules */
.rules-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.6rem}
.rules-col{background:var(--bg);border-radius:8px;padding:0.85rem 1rem}
.rules-always{border-left:3px solid var(--green)}
.rules-never{border-left:3px solid var(--red)}
.rules-col h3{font-size:0.78rem;font-weight:700;margin:0 0 0.35rem}
.rules-col ul{list-style:none;padding:0;margin:0;font-size:0.8rem}
.rules-col li{padding:0.15rem 0;line-height:1.35}

/* Collapsible details */
.detail-section{border:none}
.detail-section summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:0.5rem}
.detail-section summary::-webkit-details-marker{display:none}
.detail-section summary::before{
  content:'\\25B6';font-size:0.6rem;color:var(--light);
  transition:transform 0.15s;display:inline-block;
}
.detail-section[open] summary::before{transform:rotate(90deg)}
.detail-section summary h2{border-bottom:none;margin:0;padding:0}
.detail-section > *:not(summary){margin-top:0.75rem}

/* Setup */
.setup-content h4{
  font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;
  color:var(--light);margin:0.75rem 0 0.25rem;
}
.setup-content ul{padding-left:1.1rem;font-size:0.82rem;margin:0 0 0.25rem}
.setup-content li{margin-bottom:0.15rem;line-height:1.35}
.code-list li{font-family:'JetBrains Mono',monospace;font-size:0.78rem}
.auth-pills{display:flex;gap:0.35rem;flex-wrap:wrap;margin-bottom:0.5rem}

/* Decision guide */
.dg-card{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem}
.dg-card h4{margin:0 0 0.4rem;font-size:0.88rem;color:var(--accent)}
.dg-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem}
.dg-grid strong{font-size:0.65rem;text-transform:uppercase;letter-spacing:0.04em;color:var(--light)}
.dg-grid ul{padding-left:1rem;font-size:0.78rem;margin:0.15rem 0 0}

/* Troubleshooting table */
.ts-table{width:100%;border-collapse:collapse;font-size:0.8rem}
.ts-table th{
  text-align:left;font-size:0.65rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.04em;color:var(--light);padding:0.4rem 0.6rem;
  border-bottom:2px solid var(--border);
}
.ts-table td{padding:0.5rem 0.6rem;border-bottom:1px solid var(--border);color:var(--text);vertical-align:top}

/* References */
.ref-list{list-style:none;padding:0;margin:0;columns:2;column-gap:1.5rem}
.ref-list li{padding:0.25rem 0;font-size:0.82rem;break-inside:avoid}
.ref-list a{color:var(--accent);text-decoration:none;font-weight:600}
.ref-list a:hover{text-decoration:underline}
.ref-topic{font-size:0.7rem;color:var(--light);margin-left:0.25rem}

/* Lock overlay */
.section-locked{min-height:180px}
.section-locked>*:not(.lock-overlay){filter:blur(5px);opacity:0.3;pointer-events:none;user-select:none}
.lock-overlay{
  position:absolute;top:0;left:0;right:0;bottom:0;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg,rgba(250,250,248,0) 0%,rgba(250,250,248,0.9) 40%,rgba(250,250,248,0.98) 100%);
  z-index:10;
}
.lock-cta{
  text-align:center;padding:1.25rem 1.75rem;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius);
  box-shadow:0 8px 32px rgba(0,0,0,0.08);
}
.lock-cta svg{color:var(--accent);margin-bottom:0.4rem}
.lock-cta p{font-weight:700;color:var(--text);margin-bottom:0.6rem;font-size:0.95rem}
.unlock-btn{
  display:inline-block;padding:0.5rem 1.75rem;background:var(--accent);color:#fff;
  border-radius:100px;font-weight:700;text-decoration:none;font-size:0.85rem;
  transition:background 0.15s;box-shadow:0 2px 8px rgba(26,122,76,0.15);
}
.unlock-btn:hover{background:#15603B}

.empty{color:#C0BDB8;font-style:italic;font-size:0.78rem}

/* Footer */
footer{
  text-align:center;padding:1.5rem 0 0.75rem;color:var(--light);font-size:0.75rem;
  border-top:1px solid var(--border);margin-top:1rem;
}
footer a{color:var(--accent);text-decoration:none;font-weight:600}
footer a:hover{text-decoration:underline}

/* Responsive */
@media(max-width:768px){
  .container{padding:1rem 1rem 2.5rem}
  .hero h1{font-size:1.75rem}
  .scope-grid{grid-template-columns:1fr 1fr}
  .tasks-grid,.pb-grid,.pb-grid-bottom,.dg-grid,.stop-grid,.rules-grid{grid-template-columns:1fr}
  .card{padding:1rem 0.85rem}
  .ref-list{columns:1}
}
@media(max-width:480px){
  .scope-grid{grid-template-columns:1fr}
}
"""

    # ===== ASSEMBLE =====
    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(product_name)} &mdash; Agent Operating Guide | GrounDocs</title>
<meta name="description" content="Agent operating guide for {_esc(product_name)}. Generated by GrounDocs.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div class="container">
  {hero_html}
  {scope_html}
  {stop_html}
  {tasks_html}
  {playbooks_section}
  {rules_html}
  {setup_html}
  {dg_section}
  {ts_section}
  {ref_section}
  <footer>
    <p>Generated by <a href="https://groundocs.com" target="_blank">GrounDocs</a></p>
    <p style="margin-top:0.2rem;font-size:0.68rem;color:#C0BDB8">{timestamp}</p>
  </footer>
</div>
</body>
</html>
"""
    return html


def render_generating_html(product_name: str, slug: str) -> str:
    """Return a generating page with auto-refresh."""
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
  font-family:'Plus Jakarta Sans',system-ui,sans-serif;
  background:#FAFAF8;color:#1A1A1A;display:flex;align-items:center;justify-content:center;
  min-height:100vh;margin:0;
}}
.card{{
  text-align:center;background:#fff;border:1px solid #E5E5E0;border-radius:10px;
  padding:2.5rem 2rem;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,0.04);
}}
h1{{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:1.5rem;margin-bottom:0.5rem}}
p{{color:#6B6B6B;margin-bottom:0.75rem;font-size:0.9rem}}
.spinner{{
  width:32px;height:32px;border:3px solid #E5E5E0;border-top-color:#1A7A4C;
  border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 1rem;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.hint{{font-size:0.75rem;color:#C0BDB8}}
</style>
</head>
<body>
<div class="card">
  <div class="spinner"></div>
  <h1>Building your agent guide</h1>
  <p>Crawling <strong>{_esc(product_name)}</strong> docs and generating the operating guide.</p>
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
